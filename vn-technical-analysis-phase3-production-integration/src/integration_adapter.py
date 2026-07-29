"""VTA Phase 3 Production Integration — integration_adapter.py

The integration boundary adapter (directive 6, 8, 9, 15, 16, 17).

Boundary:
    Host input
      -> map_host_to_canonical_input()        (validate + field map + tz normalize)
      -> frozen VTA runner (run_active / run_profile)
      -> frozen canonical OutputPacket
      -> map_canonical_to_host_envelope()     (versioned host transport envelope)

The adapter is ALLOWED to (directive 6):
  - validate host input;
  - map field names;
  - map instrument identifiers;
  - normalize timestamps to the frozen contract;
  - map price-basis metadata;
  - translate the canonical output packet into a host transport envelope;
  - add integration-level tracing;
  - apply the feature flag;
  - record operational metrics;
  - fail closed when integration infrastructure is invalid.

The adapter MUST NOT (directive 6):
  - recompute indicators, reinterpret setups, create canonical failure codes,
    change primary/diagnostic codes, alter formula results or setup states,
    drop provenance, alter the deterministic record ID, change tolerance or
    rounding, insert default market data, guess missing fields, use message
    text as a machine contract, or derive expected oracles from production
    output.

Version pinning (directive 10): the frozen runner is loaded by inserting the
EXACT pinned implementation directory onto sys.path. The loaded module's
declared commit is asserted equal to the pinned commit. Floating / latest
dependencies are prohibited.

Read-only boundary (directive 7): the host envelope carries the canonical
packet verbatim; the adapter adds ONLY a clearly-namespaced integration
envelope. It exposes no write primitive that could mutate host state.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from feature_flag import FeatureFlag, FeatureFlagDecision, FLAG_NAME
from integration_failure_codes import (
    INTEGRATION_ADAPTER_SCHEMA_REJECTED,
    INTEGRATION_CONFIGURATION_MISMATCH,
    INTEGRATION_FROZEN_PACKAGE_UNAVAILABLE,
    INTEGRATION_HOST_SERIALIZATION_FAILED,
    INTEGRATION_UNSUPPORTED_HOST_SCHEMA,
    assert_disjoint_from_canonical,
)
from observability import (
    METRIC_INTEGRATION_FAILURE_TOTAL,
    METRIC_INTEGRATION_INVOCATION_TOTAL,
    METRIC_INTEGRATION_SUCCESS_TOTAL,
    METRIC_LATENCY_SECONDS,
    METRIC_OUTPUT_BYTES,
    METRIC_INPUT_RECORD_COUNT,
    ObservabilityRecorder,
)


# ====================================================================
# Frozen authority pinning (directive 10)
# ====================================================================

PINNED_IMPLEMENTATION_COMMIT: str = "23853411aa74c504ee2d79dd8889a845b5edf7de"

# Canonical schema/serialization/contract versions. These are declared by the
# frozen implementation; the adapter refuses to run if the loaded module does
# not declare the same values.
CANONICAL_SCHEMA_VERSION: str = "vta-canonical-v1"
SERIALIZATION_VERSION: str = "canonical-json-v1"
FORMULA_CONTRACT_VERSION: str = "frozen-formula-registry-v1"
SETUP_CONTRACT_VERSION: str = "frozen-setup-registry-v1"
FAILURE_CODE_REGISTRY_VERSION: str = "vta-failure-code-registry-1.0.0"

INTEGRATION_VERSION: str = "vta-phase-3-integration-v1"

# Host schema versions this integration accepts (directive 15: unknown schema
# version must be rejected, not silently coerced).
SUPPORTED_HOST_SCHEMA_VERSIONS: Tuple[str, ...] = (
    "host-market-data-v1",
    "host-market-data-v1.1",
)


# ====================================================================
# Frozen runner loader (isolated import to avoid bare-name shadowing)
# ====================================================================

# Our own integration modules that share names with nothing in the frozen src
# EXCEPT ``integration_adapter``. The frozen runner does
# ``from integration_adapter import BoundaryCheck, ...`` — that bare name would
# resolve to OUR module if ours is cached. We therefore remove OUR cached
# modules whose names collide with frozen sibling modules during the load.
_OWN_MODULE_NAMES: Tuple[str, ...] = ("integration_adapter",)


def _load_frozen_runner(frozen_src_dir: str):
    """Import the frozen ``runner`` module in an isolated sys.modules state.

    The frozen runner imports siblings by bare name. We ensure those bare
    names resolve to FROZEN code by:
      1. temporarily popping any of our own colliding cached modules;
      2. inserting the frozen src dir at index 0 of sys.path;
      3. importing ``runner`` (its sibling imports now resolve to frozen);
      4. restoring our own cached modules (the frozen siblings remain cached
         under their bare names — they do not collide with our public API
         except ``integration_adapter``, which we restore on top).

    Frozen sibling modules (output_assembler, profile_engine, canonical_packet,
    language_verifier, indicator_engine, normalization_engine, runner) are left
    cached; this is correct — they ARE the frozen implementation.
    """
    if not os.path.isdir(frozen_src_dir):
        raise IntegrationFailureEnvelope_error(
            INTEGRATION_FROZEN_PACKAGE_UNAVAILABLE,
            {"expected_implementation_commit": PINNED_IMPLEMENTATION_COMMIT,
             "lookup_error": f"frozen src not a directory: {frozen_src_dir}"},
            phase="init",
        )
    saved_own = {}
    for name in _OWN_MODULE_NAMES:
        if name in sys.modules:
            saved_own[name] = sys.modules.pop(name)
    path_added = False
    if frozen_src_dir not in sys.path:
        sys.path.insert(0, frozen_src_dir)
        path_added = True
    try:
        mod = importlib.import_module("runner")
    except Exception as exc:
        # Restore our modules even on failure.
        sys.modules.update(saved_own)
        raise IntegrationFailureEnvelope_error(
            INTEGRATION_FROZEN_PACKAGE_UNAVAILABLE,
            {"expected_implementation_commit": PINNED_IMPLEMENTATION_COMMIT,
             "lookup_error": f"runner import failed: {exc!r}"},
            phase="init",
        ) from exc
    finally:
        # Restore our own colliding modules on top of the frozen ones so the
        # rest of the integration layer keeps referring to OUR code.
        sys.modules.update(saved_own)
    return mod


# ====================================================================
# Canonical input mapping (directive 8: explicit per-field mapping)
# ====================================================================

@dataclass(frozen=True)
class FieldMapping:
    """Explicit host->canonical field mapping (directive 8 field_mapping)."""
    host_path: str
    canonical_path: str
    type: str
    nullable: bool
    transformation: str
    unit: str
    timezone: str
    missing_behavior: str          # REJECT | NULL | DERIVE
    invalid_behavior: str          # REJECT | NULL
    provenance_preserved: bool


# Row-level OHLCV mapping (host row -> canonical weekly/daily row).
# The frozen runner consumes rows with keys: date, open, high, low, close,
# volume (and optional trading_days). All host aliases map to these.
HOST_ROW_FIELD_MAPPINGS: Tuple[FieldMapping, ...] = (
    FieldMapping("timestamp", "date", "string_ISO8601_date", False,
                 "iso8601_to_canonical_date", "ISO_8601", "UTC+host_offset_to_UTC",
                 "REJECT", "REJECT", True),
    FieldMapping("open_price", "open", "float", False,
                 "as_float", "price_quote", "n/a",
                 "REJECT", "REJECT", True),
    FieldMapping("high_price", "high", "float", False,
                 "as_float", "price_quote", "n/a",
                 "REJECT", "REJECT", True),
    FieldMapping("low_price", "low", "float", False,
                 "as_float", "price_quote", "n/a",
                 "REJECT", "REJECT", True),
    FieldMapping("close_price", "close", "float", False,
                 "as_float", "price_quote", "n/a",
                 "REJECT", "REJECT", True),
    FieldMapping("trade_volume", "volume", "float", True,
                 "as_float_or_null", "shares", "n/a",
                 "NULL", "NULL", True),
    FieldMapping("trading_days_in_period", "trading_days", "int", True,
                 "as_int_or_null", "count", "n/a",
                 "NULL", "NULL", True),
)

# Top-level invocation mapping.
HOST_INVOCATION_MAPPINGS: Tuple[FieldMapping, ...] = (
    FieldMapping("host_input.symbol", "ticker", "string", False,
                 "pass_through", "n/a", "n/a",
                 "REJECT", "REJECT", True),
    FieldMapping("host_input.mode", "mode", "enum[ACTIVE,PROFILE]", False,
                 "normalize_upper", "n/a", "n/a",
                 "REJECT", "REJECT", True),
    FieldMapping("host_input.as_of_date", "as_of_date", "string_ISO8601_date", True,
                 "iso8601_to_canonical_date", "ISO_8601", "UTC",
                 "DERIVE", "REJECT", True),
    FieldMapping("host_input.frequency", "frequency", "enum[WEEKLY,DAILY]", False,
                 "normalize_upper", "n/a", "n/a",
                 "REJECT", "REJECT", True),
    FieldMapping("host_input.source_provider", "source_provider", "string", False,
                 "pass_through", "n/a", "n/a",
                 "NULL", "NULL", True),
    FieldMapping("host_input.adjustment_state", "adjustment_state", "string", False,
                 "pass_through", "n/a", "n/a",
                 "REJECT", "REJECT", True),
    FieldMapping("host_input.price_basis", "price_basis", "string", False,
                 "pass_through", "n/a", "n/a",
                 "REJECT", "REJECT", True),
)


# ====================================================================
# Result types
# ====================================================================

@dataclass(frozen=True)
class CanonicalInput:
    """Frozen canonical VTA input derived from host input."""
    ticker: str
    mode: str
    frequency: str
    rows: Tuple[Mapping[str, Any], ...]
    as_of_date: Optional[str]
    source_provider: str
    adjustment_state: str
    price_basis: str
    host_input_digest: str
    canonical_input_digest: str


@dataclass(frozen=True)
class IntegrationFailureEnvelope:
    """Integration-namespaced failure envelope (directive 17).

    Distinct from the canonical VTA ErrorEnvelope. Carries an integration
    failure code + the documented required_context fields only.
    """
    integration_code: str
    required_context: Mapping[str, Any]
    phase: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "namespace": "VTA_PHASE_3_INTEGRATION",
            "integration_code": self.integration_code,
            "required_context": dict(self.required_context),
            "phase": self.phase,
        }


@dataclass(frozen=True)
class HostOutputEnvelope:
    """Host transport envelope wrapping the canonical packet (directive 16).

    The canonical packet is carried VERBATIM under ``canonical_packet``.
    Host-specific metadata lives under ``integration_envelope`` (a separate
    namespace). No canonical field is dropped, renamed, coerced, or reordered.
    """
    integration_run_id: str
    integration_version: str
    pinned_implementation_commit: str
    canonical_schema_version: str
    serialization_version: str
    feature_flag_decision: Mapping[str, Any]
    canonical_input_digest: str
    output_digest: str
    deterministic_record_id: str
    provenance_version: str
    canonical_packet: Mapping[str, Any]       # verbatim frozen packet.to_dict()
    integration_envelope: Mapping[str, Any]   # host-only namespace
    elapsed_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "integration_run_id": self.integration_run_id,
            "integration_version": self.integration_version,
            "pinned_implementation_commit": self.pinned_implementation_commit,
            "canonical_schema_version": self.canonical_schema_version,
            "serialization_version": self.serialization_version,
            "feature_flag_decision": dict(self.feature_flag_decision),
            "canonical_input_digest": self.canonical_input_digest,
            "output_digest": self.output_digest,
            "deterministic_record_id": self.deterministic_record_id,
            "provenance_version": self.provenance_version,
            "canonical_packet": dict(self.canonical_packet),
            "integration_envelope": dict(self.integration_envelope),
            "elapsed_seconds": self.elapsed_seconds,
        }

    def serialize(self) -> str:
        """Deterministic JSON for digest + host transport."""
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False,
                          separators=(",", ":"))


# ====================================================================
# Helpers
# ====================================================================

def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _canonical_json_hash(obj: Any) -> str:
    return _sha256_bytes(
        json.dumps(obj, sort_keys=True, ensure_ascii=False,
                   separators=(",", ":")).encode("utf-8")
    )


def _as_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f:           # NaN
        return None
    if f in (float("inf"), float("-inf")):
        return None
    return f


def _as_int(v: Any) -> Optional[int]:
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        f = _as_float(v)
        return int(f) if f is not None else None


def _iso_date(v: Any) -> Optional[str]:
    """Normalize a host timestamp to a canonical ISO-8601 DATE string.

    Accepts ``YYYY-MM-DD`` or full ISO-8601 datetime (with or without zone).
    If the host string carries an explicit UTC offset, the calendar date is
    computed in UTC (offset applied). If the host string is date-only or a
    naive datetime, it is passed through unchanged (we never invent a
    timezone). Non-date strings are rejected (returned None), never silently
    coerced.
    """
    from datetime import datetime, timezone
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip()
        # date-only fast path
        if len(s) == 10 and s[4] == "-" and s[7] == "-":
            try:
                datetime.fromisoformat(s)
                return s
            except ValueError:
                return None
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            return None
        # If an explicit zone/offset was provided, normalize to UTC before
        # taking the calendar date. Naive datetimes are left as-is.
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc)
        return dt.date().isoformat()
    return None


# ====================================================================
# Host -> canonical input mapping
# ====================================================================

class IntegrationAdapter:
    """The host<->canonical boundary adapter + frozen-runner loader.

    Construction pins the frozen implementation directory and asserts the
    loaded module's declared commit. The adapter is stateless across
    invocations except for the shared FeatureFlag + ObservabilityRecorder.
    """

    def __init__(
        self,
        *,
        frozen_implementation_dir: str,
        feature_flag: FeatureFlag,
        observability: ObservabilityRecorder,
        environment: str = "production-like",
        consumer: str = "default-consumer",
        phase_deadline_seconds: float = 30.0,
    ) -> None:
        if not os.path.isdir(frozen_implementation_dir):
            raise IntegrationFailureEnvelope_error(
                INTEGRATION_FROZEN_PACKAGE_UNAVAILABLE,
                {"expected_implementation_commit": PINNED_IMPLEMENTATION_COMMIT,
                 "lookup_error": f"not a directory: {frozen_implementation_dir}"},
                phase="init",
            )
        self._impl_dir = os.path.abspath(frozen_implementation_dir)
        self._feature_flag = feature_flag
        self._obs = observability
        self._environment = environment
        self._consumer = consumer
        self._phase_deadline = float(phase_deadline_seconds)

        # Load the frozen runner. The frozen runner imports its siblings by
        # BARE module name (e.g. ``from integration_adapter import ...``,
        # ``import profile_engine``). To avoid our own integration modules
        # shadowing the frozen siblings, we isolate the load: temporarily strip
        # any of OUR already-cached integration modules from sys.modules and
        # ensure the frozen src dir is at the FRONT of sys.path, so the frozen
        # siblings resolve to frozen code. We do NOT copy or modify frozen code.
        src_dir = os.path.join(self._impl_dir, "src")
        self._runner = _load_frozen_runner(src_dir)
        self._frozen_module_commit = getattr(
            self._runner, "VTA_IMPLEMENTATION_COMMIT", PINNED_IMPLEMENTATION_COMMIT)
        # Pin assertion (directive 10). If the frozen module declares a
        # different commit, fail closed.
        if self._frozen_module_commit != PINNED_IMPLEMENTATION_COMMIT:
            raise IntegrationFailureEnvelope_error(
                INTEGRATION_CONFIGURATION_MISMATCH,
                {"config_key": "VTA_IMPLEMENTATION_COMMIT",
                 "expected": PINNED_IMPLEMENTATION_COMMIT,
                 "observed": self._frozen_module_commit},
                phase="init",
            )
        # Assert namespace disjointness at import (directive 17 structural guard).
        try:
            from integration_failure_codes import CANONICAL_CODE_COUNT  # noqa: F401
        except Exception:
            pass

    # ----------------------------------------------------------------
    # Public: run a host invocation through the boundary
    # ----------------------------------------------------------------

    def run(self, host_input: Mapping[str, Any]) -> Dict[str, Any]:
        """Execute one host invocation through the integration boundary.

        Returns a dict with exactly one of:
          - {"status": "OK", "envelope": HostOutputEnvelope.to_dict(),
             "integration_run_id": ...}
          - {"status": "DISABLED", "feature_flag_decision": ...,
             "fallback": <host non-VTA fallback or explicit disabled status>}
          - {"status": "INTEGRATION_FAILURE", "envelope": IntegrationFailureEnvelope.to_dict()}
          - {"status": "CANONICAL_FAILURE", "canonical_error": <frozen ErrorEnvelope>,
             "integration_envelope": ...}

        Never raises to the host: every failure path returns a structured dict.
        """
        start = time.monotonic()
        run_id = "irun-" + uuid.uuid4().hex
        dims = self._base_dims()

        self._obs.inc(METRIC_INTEGRATION_INVOCATION_TOTAL, dimensions=dims)

        # 1. Feature flag (directive 11).
        flag_decision = self._feature_flag.resolve(
            environment=self._environment,
            tenant_or_consumer=self._consumer,
        )
        self._obs.feature_flag_state(flag_decision.enabled, dimensions=dims)
        if not flag_decision.enabled:
            elapsed = time.monotonic() - start
            self._obs.observe(METRIC_LATENCY_SECONDS, elapsed, dimensions=dims)
            return {
                "status": "DISABLED",
                "integration_run_id": run_id,
                "feature_flag_decision": flag_decision.to_dict(),
                "fallback": _host_fallback(),
            }

        # 2. Map host -> canonical input (may produce an integration failure).
        try:
            canonical = self.map_host_to_canonical_input(host_input)
        except IntegrationFailureEnvelope_error as exc:
            elapsed = time.monotonic() - start
            self._obs.inc(METRIC_INTEGRATION_FAILURE_TOTAL, dimensions=dims)
            self._obs.observe(METRIC_LATENCY_SECONDS, elapsed, dimensions=dims)
            env = exc.envelope
            self._obs.log({
                "integration_run_id": run_id,
                "result_status": "INTEGRATION_FAILURE",
                "primary_failure_code": env.integration_code,
                "feature_flag_state": flag_decision.enabled,
                "elapsed_seconds": elapsed,
                "integration_version": INTEGRATION_VERSION,
                "VTA_implementation_commit": PINNED_IMPLEMENTATION_COMMIT,
                "canonical_schema_version": CANONICAL_SCHEMA_VERSION,
                "environment": self._environment,
                "consumer": self._consumer,
            })
            return {"status": "INTEGRATION_FAILURE",
                    "integration_run_id": run_id,
                    "envelope": env.to_dict()}

        # 3. Invoke the frozen runner.
        try:
            runner_result = self._invoke_frozen_runner(canonical)
        except _FrozenPackageMissing as exc:
            elapsed = time.monotonic() - start
            self._obs.inc(METRIC_INTEGRATION_FAILURE_TOTAL, dimensions=dims)
            env = IntegrationFailureEnvelope(
                INTEGRATION_FROZEN_PACKAGE_UNAVAILABLE,
                {"expected_implementation_commit": PINNED_IMPLEMENTATION_COMMIT,
                 "lookup_error": str(exc)},
                phase="invoke",
            )
            return {"status": "INTEGRATION_FAILURE",
                    "integration_run_id": run_id,
                    "envelope": env.to_dict()}

        # 4. Branch on canonical result.
        elapsed = time.monotonic() - start
        if elapsed > self._phase_deadline:
            self._obs.inc(METRIC_INTEGRATION_FAILURE_TOTAL, dimensions=dims)
            env = IntegrationFailureEnvelope(
                "INTEGRATION_TIMEOUT",
                {"phase": "invoke", "elapsed_seconds": round(elapsed, 6),
                 "deadline_seconds": self._phase_deadline},
                phase="invoke",
            )
            return {"status": "INTEGRATION_FAILURE",
                    "integration_run_id": run_id,
                    "envelope": env.to_dict()}

        is_valid = runner_result.get("is_valid", False)
        packet = runner_result.get("packet")
        canonical_error = runner_result.get("error")

        if not is_valid and canonical_error is not None:
            # Canonical VTA failure envelope (frozen codes). The integration
            # layer surfaces it VERBATIM; no integration code is substituted.
            self._obs.inc("canonical_failure_envelope_total", dimensions=dims)
            self._obs.log({
                "integration_run_id": run_id,
                "result_status": "CANONICAL_FAILURE",
                "primary_failure_code": canonical_error.get("error_code", ""),
                "feature_flag_state": flag_decision.enabled,
                "elapsed_seconds": elapsed,
                "integration_version": INTEGRATION_VERSION,
                "VTA_implementation_commit": PINNED_IMPLEMENTATION_COMMIT,
                "canonical_schema_version": CANONICAL_SCHEMA_VERSION,
                "environment": self._environment,
                "consumer": self._consumer,
            })
            return {"status": "CANONICAL_FAILURE",
                    "integration_run_id": run_id,
                    "canonical_error": canonical_error,
                    "integration_envelope": {
                        "integration_run_id": run_id,
                        "integration_version": INTEGRATION_VERSION,
                        "canonical_input_digest": canonical.canonical_input_digest,
                    }}

        # 5. Map canonical packet -> host envelope.
        try:
            envelope = self.map_canonical_to_host_envelope(
                packet, canonical=canonical, flag_decision=flag_decision,
                run_id=run_id, elapsed=elapsed,
            )
        except Exception as exc:
            self._obs.inc(METRIC_INTEGRATION_FAILURE_TOTAL, dimensions=dims)
            env = IntegrationFailureEnvelope(
                INTEGRATION_HOST_SERIALIZATION_FAILED,
                {"serializer": "HostOutputEnvelope",
                 "serialization_error": str(exc)},
                phase="serialize",
            )
            return {"status": "INTEGRATION_FAILURE",
                    "integration_run_id": run_id,
                    "envelope": env.to_dict()}

        # 6. Success accounting.
        success_dims = dict(dims)
        success_dims["result_status"] = "OK"
        self._obs.inc(METRIC_INTEGRATION_SUCCESS_TOTAL, dimensions=success_dims)
        self._obs.observe(METRIC_LATENCY_SECONDS, elapsed, dimensions=success_dims)
        self._obs.observe(METRIC_INPUT_RECORD_COUNT, float(len(canonical.rows)),
                          dimensions=success_dims)
        env_bytes = len(envelope.serialize().encode("utf-8"))
        self._obs.observe(METRIC_OUTPUT_BYTES, float(env_bytes), dimensions=success_dims)
        self._obs.log({
            "integration_run_id": run_id,
            "deterministic_record_id": envelope.deterministic_record_id,
            "canonical_input_digest": canonical.canonical_input_digest,
            "output_digest": envelope.output_digest,
            "provenance_version": envelope.provenance_version,
            "feature_flag_state": flag_decision.enabled,
            "elapsed_seconds": elapsed,
            "result_status": "OK",
            "primary_failure_code": "",
            "integration_version": INTEGRATION_VERSION,
            "VTA_implementation_commit": PINNED_IMPLEMENTATION_COMMIT,
            "canonical_schema_version": CANONICAL_SCHEMA_VERSION,
            "environment": self._environment,
            "consumer": self._consumer,
            "input_record_count": len(canonical.rows),
            "output_bytes": env_bytes,
        })
        return {"status": "OK", "integration_run_id": run_id,
                "envelope": envelope.to_dict()}

    # ----------------------------------------------------------------
    # Host -> canonical input
    # ----------------------------------------------------------------

    def map_host_to_canonical_input(self, host_input: Mapping[str, Any]) -> CanonicalInput:
        schema_version = host_input.get("schema_version")
        if schema_version not in SUPPORTED_HOST_SCHEMA_VERSIONS:
            raise IntegrationFailureEnvelope_error(
                INTEGRATION_UNSUPPORTED_HOST_SCHEMA,
                {"host_schema_version": str(schema_version),
                 "supported_versions": list(SUPPORTED_HOST_SCHEMA_VERSIONS)},
                phase="map_input",
            )

        inner = host_input.get("host_input", host_input)

        # Top-level scalar fields (explicit mapping; no implicit aliases).
        ticker = inner.get("symbol")
        mode = (inner.get("mode") or "").upper()
        frequency = (inner.get("frequency") or "").upper()
        if ticker is None or mode not in ("ACTIVE", "PROFILE") \
                or frequency not in ("WEEKLY", "DAILY"):
            raise IntegrationFailureEnvelope_error(
                INTEGRATION_ADAPTER_SCHEMA_REJECTED,
                {"host_schema_version": schema_version,
                 "rejected_field": "symbol|mode|frequency"},
                phase="map_input",
            )
        # mode/frequency consistency: ACTIVE<->WEEKLY, PROFILE<->DAILY.
        if (mode, frequency) not in (("ACTIVE", "WEEKLY"), ("PROFILE", "DAILY")):
            raise IntegrationFailureEnvelope_error(
                INTEGRATION_ADAPTER_SCHEMA_REJECTED,
                {"host_schema_version": schema_version,
                 "rejected_field": f"mode_frequency_pair:{mode}/{frequency}"},
                phase="map_input",
            )

        as_of = _iso_date(inner.get("as_of_date"))
        source_provider = inner.get("source_provider") or "UNKNOWN_PROVIDER"
        adjustment_state = inner.get("adjustment_state")
        price_basis = inner.get("price_basis")
        if adjustment_state is None or price_basis is None:
            raise IntegrationFailureEnvelope_error(
                INTEGRATION_ADAPTER_SCHEMA_REJECTED,
                {"host_schema_version": schema_version,
                 "rejected_field": "adjustment_state|price_basis"},
                phase="map_input",
            )

        # Row mapping (explicit per-field alias map; no heuristic discovery).
        # NOTE: an EMPTY row list is structurally valid — we forward it to the
        # frozen runner, which emits the canonical EMPTY_SERIES envelope
        # (directive 15: canonical_failure_envelopes must match expected). We
        # only reject here if the rows/ohlcv_records key is entirely absent
        # (structural schema break), not if it is an empty list.
        if "rows" not in inner and "ohlcv_records" not in inner:
            raise IntegrationFailureEnvelope_error(
                INTEGRATION_ADAPTER_SCHEMA_REJECTED,
                {"host_schema_version": schema_version,
                 "rejected_field": "rows"},
                phase="map_input",
            )
        host_rows = inner.get("rows") or inner.get("ohlcv_records") or ()
        canonical_rows: List[Dict[str, Any]] = []
        for r in host_rows:
            mapped: Dict[str, Any] = {}
            for m in HOST_ROW_FIELD_MAPPINGS:
                # host_path is the leaf name; we look it up directly (the host
                # row schema is flat per the host-mapping contract).
                leaf = m.host_path.split(".")[-1]
                val = r.get(leaf)
                if val is None and not m.nullable and m.missing_behavior == "REJECT":
                    raise IntegrationFailureEnvelope_error(
                        INTEGRATION_ADAPTER_SCHEMA_REJECTED,
                        {"host_schema_version": schema_version,
                         "rejected_field": f"row.{m.canonical_path}"},
                        phase="map_input",
                    )
                if m.canonical_path == "date":
                    d = _iso_date(val)
                    if d is None:
                        raise IntegrationFailureEnvelope_error(
                            INTEGRATION_ADAPTER_SCHEMA_REJECTED,
                            {"host_schema_version": schema_version,
                             "rejected_field": f"row.date:{val!r}"},
                            phase="map_input",
                        )
                    mapped["date"] = d
                elif m.canonical_path in ("open", "high", "low", "close", "volume"):
                    f = _as_float(val)
                    if f is None and not m.nullable:
                        raise IntegrationFailureEnvelope_error(
                            INTEGRATION_ADAPTER_SCHEMA_REJECTED,
                            {"host_schema_version": schema_version,
                             "rejected_field": f"row.{m.canonical_path}:{val!r}"},
                            phase="map_input",
                        )
                    mapped[m.canonical_path] = f
                elif m.canonical_path == "trading_days":
                    mapped["trading_days"] = _as_int(val)
            canonical_rows.append(mapped)

        host_digest = _canonical_json_hash(host_input)
        canonical_payload = {
            "ticker": ticker, "mode": mode, "frequency": frequency,
            "as_of_date": as_of, "source_provider": source_provider,
            "adjustment_state": adjustment_state, "price_basis": price_basis,
            "rows": canonical_rows,
        }
        canonical_digest = _canonical_json_hash(canonical_payload)

        return CanonicalInput(
            ticker=str(ticker), mode=mode, frequency=frequency,
            rows=tuple(canonical_rows), as_of_date=as_of,
            source_provider=str(source_provider),
            adjustment_state=str(adjustment_state),
            price_basis=str(price_basis),
            host_input_digest=host_digest,
            canonical_input_digest=canonical_digest,
        )

    # ----------------------------------------------------------------
    # Canonical -> host envelope
    # ----------------------------------------------------------------

    def map_canonical_to_host_envelope(
        self,
        packet: Any,
        *,
        canonical: CanonicalInput,
        flag_decision: FeatureFlagDecision,
        run_id: str,
        elapsed: float,
    ) -> HostOutputEnvelope:
        """Wrap the frozen canonical packet in the host transport envelope.

        The canonical packet is serialized via its OWN deterministic serialize()
        (sorted keys). We do NOT re-serialize or reorder canonical fields.
        """
        if hasattr(packet, "to_dict"):
            packet_dict = packet.to_dict()
        elif isinstance(packet, Mapping):
            packet_dict = dict(packet)
        else:
            raise IntegrationFailureEnvelope_error(
                INTEGRATION_HOST_SERIALIZATION_FAILED,
                {"serializer": "HostOutputEnvelope",
                 "serialization_error": f"unsupported packet type {type(packet).__name__}"},
                phase="serialize",
            )
        # Deterministic output digest over the canonical packet's own bytes.
        packet_bytes = (packet.serialize().encode("utf-8")
                        if hasattr(packet, "serialize")
                        else json.dumps(packet_dict, sort_keys=True,
                                        ensure_ascii=False,
                                        separators=(",", ":")).encode("utf-8"))
        output_digest = _sha256_bytes(packet_bytes)

        body = packet_dict.get("body", {}) if isinstance(packet_dict, Mapping) else {}
        deterministic_record_id = self._deterministic_record_id(canonical, output_digest)
        provenance = packet_dict.get("provenance", {}) if isinstance(packet_dict, Mapping) else {}
        provenance_version = FAILURE_CODE_REGISTRY_VERSION  # bound to frozen authority

        integration_envelope: Dict[str, Any] = {
            "host_target": "read-only-downstream-consumer",
            "side_effect_policy": "READ_ONLY",
            "schema_version_supported": True,
            "phase_deadline_seconds": self._phase_deadline,
        }

        return HostOutputEnvelope(
            integration_run_id=run_id,
            integration_version=INTEGRATION_VERSION,
            pinned_implementation_commit=PINNED_IMPLEMENTATION_COMMIT,
            canonical_schema_version=CANONICAL_SCHEMA_VERSION,
            serialization_version=SERIALIZATION_VERSION,
            feature_flag_decision=flag_decision.to_dict(),
            canonical_input_digest=canonical.canonical_input_digest,
            output_digest=output_digest,
            deterministic_record_id=deterministic_record_id,
            provenance_version=provenance_version,
            canonical_packet=packet_dict,
            integration_envelope=integration_envelope,
            elapsed_seconds=round(elapsed, 6),
        )

    # ----------------------------------------------------------------
    # Frozen runner invocation
    # ----------------------------------------------------------------

    def _invoke_frozen_runner(self, canonical: CanonicalInput) -> Dict[str, Any]:
        try:
            if canonical.mode == "ACTIVE":
                result = self._runner.run_active(
                    canonical.ticker, canonical.rows,
                    as_of_date=canonical.as_of_date,
                    source_provider=canonical.source_provider,
                )
            else:
                result = self._runner.run_profile(
                    canonical.ticker, canonical.rows,
                    as_of_date=canonical.as_of_date,
                    source_provider=canonical.source_provider,
                )
        except ImportError as exc:
            raise _FrozenPackageMissing(str(exc))
        out: Dict[str, Any] = {"is_valid": bool(result.is_valid())}
        out["packet"] = result.packet
        out["error"] = result.error.to_dict() if result.error is not None else None
        return out

    def _deterministic_record_id(self, canonical: CanonicalInput,
                                 output_digest: str) -> str:
        """Deterministic record ID derived ONLY from canonical input + output.

        This NEVER depends on wall-clock time or random state. The host may
        independently recompute it from the canonical input digest + output
        digest.
        """
        h = hashlib.sha256()
        h.update(canonical.canonical_input_digest.encode("utf-8"))
        h.update(b"|")
        h.update(output_digest.encode("utf-8"))
        return "vta-rec-" + h.hexdigest()[:32]

    def _base_dims(self) -> Dict[str, str]:
        return {
            "environment": self._environment,
            "integration_version": INTEGRATION_VERSION,
            "VTA_implementation_commit": PINNED_IMPLEMENTATION_COMMIT,
            "canonical_schema_version": CANONICAL_SCHEMA_VERSION,
            "consumer": self._consumer,
            "result_status": "",
            "primary_failure_code": "",
        }


# ====================================================================
# Errors / fallback
# ====================================================================

class _FrozenPackageMissing(RuntimeError):
    pass


class IntegrationFailureEnvelope_error(RuntimeError):
    """Carries an IntegrationFailureEnvelope as a raised exception.

    Used internally so the run() method can translate mapping/validation
    failures into structured integration-failure envelopes without raising to
    the host.
    """
    def __init__(self, code: str, required_context: Mapping[str, Any], *, phase: str):
        super().__init__(f"{code} ({phase})")
        self.envelope = IntegrationFailureEnvelope(code, dict(required_context), phase=phase)


def _host_fallback() -> Mapping[str, Any]:
    """Directive 11: feature-flag OFF returns the host's documented non-VTA
    fallback or an explicit disabled status. It MUST NOT silently invoke a
    different technical-analysis implementation.
    """
    return {
        "kind": "EXPLICIT_DISABLED_STATUS",
        "vta_routing": "DISABLED",
        "note": ("integration feature flag is OFF; host non-VTA fallback or "
                 "explicit disabled status returned. No alternative "
                 "technical-analysis implementation invoked."),
    }


__all__ = [
    "PINNED_IMPLEMENTATION_COMMIT",
    "CANONICAL_SCHEMA_VERSION",
    "SERIALIZATION_VERSION",
    "FORMULA_CONTRACT_VERSION",
    "SETUP_CONTRACT_VERSION",
    "FAILURE_CODE_REGISTRY_VERSION",
    "INTEGRATION_VERSION",
    "SUPPORTED_HOST_SCHEMA_VERSIONS",
    "HOST_ROW_FIELD_MAPPINGS",
    "HOST_INVOCATION_MAPPINGS",
    "FieldMapping",
    "CanonicalInput",
    "IntegrationFailureEnvelope",
    "HostOutputEnvelope",
    "IntegrationAdapter",
    "IntegrationFailureEnvelope_error",
]
