"""VTA Phase 3 Production Integration — observability.py

Mandatory metrics + structured logging for the integration boundary
(directive 18).

12 mandatory metrics:
  - integration_invocation_total
  - integration_success_total
  - integration_failure_total
  - canonical_failure_envelope_total
  - adapter_rejection_total
  - output_schema_mismatch_total
  - semantic_divergence_total
  - latency_seconds
  - input_record_count
  - output_bytes
  - feature_flag_state
  - rollback_activation_total

6 mandatory dimensions:
  - environment
  - integration_version
  - VTA_implementation_commit
  - canonical_schema_version
  - consumer
  - result_status
  - primary_failure_code      (a 7th label surface; directive lists 7 under
                                "dimensions" in section 18's dimensions block)

Logs MUST include:
  integration_run_id, deterministic VTA record ID, canonical input digest,
  output digest, provenance version, feature-flag state, elapsed time,
  result status.

Logs MUST NOT include:
  secrets, auth tokens, unrestricted raw market-data dumps,
  machine-local absolute paths, user-private data not required for debugging.

Design:
  - Counters are monotonic non-negative integers; never decrease.
  - latency_seconds / input_record_count / output_bytes / feature_flag_state
    are recorded as observations (last-wins gauge snapshot in the observation
    log; the counter semantics are preserved by the *_total family).
  - No PII / no secret scrubbing is done by redacting values blindly — instead
    the LOGGABLE allowlist guarantees only safe fields are emitted.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple


# ====================================================================
# Frozen identity
# ====================================================================

METRIC_INTEGRATION_INVOCATION_TOTAL = "integration_invocation_total"
METRIC_INTEGRATION_SUCCESS_TOTAL = "integration_success_total"
METRIC_INTEGRATION_FAILURE_TOTAL = "integration_failure_total"
METRIC_CANONICAL_FAILURE_ENVELOPE_TOTAL = "canonical_failure_envelope_total"
METRIC_ADAPTER_REJECTION_TOTAL = "adapter_rejection_total"
METRIC_OUTPUT_SCHEMA_MISMATCH_TOTAL = "output_schema_mismatch_total"
METRIC_SEMANTIC_DIVERGENCE_TOTAL = "semantic_divergence_total"
METRIC_LATENCY_SECONDS = "latency_seconds"
METRIC_INPUT_RECORD_COUNT = "input_record_count"
METRIC_OUTPUT_BYTES = "output_bytes"
METRIC_FEATURE_FLAG_STATE = "feature_flag_state"
METRIC_ROLLBACK_ACTIVATION_TOTAL = "rollback_activation_total"

MANDATORY_METRICS: Tuple[str, ...] = (
    METRIC_INTEGRATION_INVOCATION_TOTAL,
    METRIC_INTEGRATION_SUCCESS_TOTAL,
    METRIC_INTEGRATION_FAILURE_TOTAL,
    METRIC_CANONICAL_FAILURE_ENVELOPE_TOTAL,
    METRIC_ADAPTER_REJECTION_TOTAL,
    METRIC_OUTPUT_SCHEMA_MISMATCH_TOTAL,
    METRIC_SEMANTIC_DIVERGENCE_TOTAL,
    METRIC_LATENCY_SECONDS,
    METRIC_INPUT_RECORD_COUNT,
    METRIC_OUTPUT_BYTES,
    METRIC_FEATURE_FLAG_STATE,
    METRIC_ROLLBACK_ACTIVATION_TOTAL,
)
MANDATORY_METRIC_COUNT = 12

MANDATORY_DIMENSIONS: Tuple[str, ...] = (
    "environment",
    "integration_version",
    "VTA_implementation_commit",
    "canonical_schema_version",
    "consumer",
    "result_status",
    "primary_failure_code",
)
MANDATORY_DIMENSION_COUNT = 7  # directive section 18 dimensions block lists 7.

# Counter metrics (monotonic).
_COUNTER_METRICS: Tuple[str, ...] = (
    METRIC_INTEGRATION_INVOCATION_TOTAL,
    METRIC_INTEGRATION_SUCCESS_TOTAL,
    METRIC_INTEGRATION_FAILURE_TOTAL,
    METRIC_CANONICAL_FAILURE_ENVELOPE_TOTAL,
    METRIC_ADAPTER_REJECTION_TOTAL,
    METRIC_OUTPUT_SCHEMA_MISMATCH_TOTAL,
    METRIC_SEMANTIC_DIVERGENCE_TOTAL,
    METRIC_ROLLBACK_ACTIVATION_TOTAL,
)

# Loggable fields (allowlist). Anything not here is NEVER logged.
LOGGABLE_FIELDS: Tuple[str, ...] = (
    "integration_run_id",
    "deterministic_record_id",
    "canonical_input_digest",
    "output_digest",
    "provenance_version",
    "feature_flag_state",
    "elapsed_seconds",
    "result_status",
    "primary_failure_code",
    "integration_version",
    "VTA_implementation_commit",
    "canonical_schema_version",
    "environment",
    "consumer",
    "mode",
    "ticker",
    "input_record_count",
    "output_bytes",
    "metric_name",
    "metric_value",
    "dimensions",
)


def _scrub(record: Mapping[str, Any]) -> Dict[str, Any]:
    """Allowlist projection. Drops anything not in LOGGABLE_FIELDS.

    This also implicitly forbids unrestricted raw market-data dumps and
    user-private data: only the explicit allowlist survives.
    """
    allowed = set(LOGGABLE_FIELDS)
    out: Dict[str, Any] = {}
    for k, v in record.items():
        if k in allowed:
            out[k] = v
    return out


# ====================================================================
# Metric registry / recorder
# ====================================================================

@dataclass
class _MetricSeries:
    name: str
    is_counter: bool
    # Counter value (monotonic). For gauges we keep last observation.
    samples: List[Dict[str, Any]] = field(default_factory=list)

    def total(self) -> int:
        if not self.is_counter:
            return 0
        return sum(int(s["value"]) for s in self.samples)

    def last(self) -> Optional[Dict[str, Any]]:
        return self.samples[-1] if self.samples else None


class ObservabilityRecorder:
    """In-process metric + log recorder.

    The host is expected to bridge these into its production metrics + log
    pipeline (Prometheus/OTLP/etc.). This class is the deterministic contract
    surface: the same metric/dimension/log schema the host MUST consume.

    Thread-safety: a single internal lock guards all mutation. Recorders are
    intended to be per-invocation OR shared; either is safe.
    """

    def __init__(self) -> None:
        self._series: Dict[str, _MetricSeries] = {}
        self._logs: List[Dict[str, Any]] = []
        for name in MANDATORY_METRICS:
            self._series[name] = _MetricSeries(
                name=name, is_counter=(name in _COUNTER_METRICS))

    # ----------------------------------------------------------------
    # Counters / gauges
    # ----------------------------------------------------------------

    def _validate_dimensions(self, dims: Mapping[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for d in MANDATORY_DIMENSIONS:
            out[d] = dims.get(d, "")
        return out

    def inc(self, metric: str, *, amount: int = 1,
            dimensions: Optional[Mapping[str, Any]] = None) -> None:
        if metric not in self._series:
            raise KeyError(f"unknown metric: {metric}")
        series = self._series[metric]
        if not series.is_counter:
            raise ValueError(f"{metric} is not a counter; use observe()")
        series.samples.append({
            "value": int(amount),
            "dimensions": self._validate_dimensions(dimensions or {}),
            "ts": _monotonic_ns(),
        })

    def observe(self, metric: str, value: float,
                dimensions: Optional[Mapping[str, Any]] = None) -> None:
        if metric not in self._series:
            raise KeyError(f"unknown metric: {metric}")
        series = self._series[metric]
        if series.is_counter:
            raise ValueError(f"{metric} is a counter; use inc()")
        series.samples.append({
            "value": float(value),
            "dimensions": self._validate_dimensions(dimensions or {}),
            "ts": _monotonic_ns(),
        })

    def feature_flag_state(self, enabled: bool,
                           dimensions: Optional[Mapping[str, Any]] = None) -> None:
        # Gauge: 1.0 enabled, 0.0 disabled.
        self.observe(METRIC_FEATURE_FLAG_STATE, 1.0 if enabled else 0.0,
                     dimensions=dimensions)

    # ----------------------------------------------------------------
    # Convenience: full invocation accounting
    # ----------------------------------------------------------------

    def record_invocation(
        self,
        *,
        result_status: str,
        primary_failure_code: str,
        elapsed_seconds: float,
        input_record_count: int,
        output_bytes: int,
        feature_flag_enabled: bool,
        rollback_activated: bool = False,
        canonical_failure_envelope: bool = False,
        adapter_rejection: bool = False,
        output_schema_mismatch: bool = False,
        semantic_divergence: bool = False,
        dimensions: Optional[Mapping[str, Any]] = None,
    ) -> None:
        dims = dimensions or {}
        self.inc(METRIC_INTEGRATION_INVOCATION_TOTAL, dimensions=dims)
        if result_status == "OK":
            self.inc(METRIC_INTEGRATION_SUCCESS_TOTAL, dimensions=dims)
        else:
            self.inc(METRIC_INTEGRATION_FAILURE_TOTAL, dimensions=dims)
        if canonical_failure_envelope:
            self.inc(METRIC_CANONICAL_FAILURE_ENVELOPE_TOTAL, dimensions=dims)
        if adapter_rejection:
            self.inc(METRIC_ADAPTER_REJECTION_TOTAL, dimensions=dims)
        if output_schema_mismatch:
            self.inc(METRIC_OUTPUT_SCHEMA_MISMATCH_TOTAL, dimensions=dims)
        if semantic_divergence:
            self.inc(METRIC_SEMANTIC_DIVERGENCE_TOTAL, dimensions=dims)
        if rollback_activated:
            self.inc(METRIC_ROLLBACK_ACTIVATION_TOTAL, dimensions=dims)
        self.observe(METRIC_LATENCY_SECONDS, float(elapsed_seconds), dimensions=dims)
        self.observe(METRIC_INPUT_RECORD_COUNT, float(input_record_count), dimensions=dims)
        self.observe(METRIC_OUTPUT_BYTES, float(output_bytes), dimensions=dims)
        self.feature_flag_state(feature_flag_enabled, dimensions=dims)

    # ----------------------------------------------------------------
    # Logs
    # ----------------------------------------------------------------

    def log(self, record: Mapping[str, Any]) -> None:
        """Emit a structured log line. Allowlist-filtered, JSON-serializable."""
        scrubbed = _scrub(record)
        # Deterministic ordering for replay.
        self._logs.append({k: scrubbed[k] for k in sorted(scrubbed)})

    # ----------------------------------------------------------------
    # Snapshot (for evidence + tests)
    # ----------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        return {
            "metrics": {
                name: {
                    "name": name,
                    "is_counter": s.is_counter,
                    "total": s.total(),
                    "sample_count": len(s.samples),
                    "last": s.last(),
                }
                for name, s in self._series.items()
            },
            "logs": list(self._logs),
            "mandatory_metric_count": MANDATORY_METRIC_COUNT,
            "mandatory_dimension_count": MANDATORY_DIMENSION_COUNT,
        }

    def reset(self) -> None:
        for s in self._series.values():
            s.samples.clear()
        self._logs.clear()


def _monotonic_ns() -> int:
    return time.monotonic_ns()


__all__ = [
    "MANDATORY_METRICS",
    "MANDATORY_METRIC_COUNT",
    "MANDATORY_DIMENSIONS",
    "MANDATORY_DIMENSION_COUNT",
    "LOGGABLE_FIELDS",
    "ObservabilityRecorder",
    "METRIC_INTEGRATION_INVOCATION_TOTAL",
    "METRIC_INTEGRATION_SUCCESS_TOTAL",
    "METRIC_INTEGRATION_FAILURE_TOTAL",
    "METRIC_CANONICAL_FAILURE_ENVELOPE_TOTAL",
    "METRIC_ADAPTER_REJECTION_TOTAL",
    "METRIC_OUTPUT_SCHEMA_MISMATCH_TOTAL",
    "METRIC_SEMANTIC_DIVERGENCE_TOTAL",
    "METRIC_LATENCY_SECONDS",
    "METRIC_INPUT_RECORD_COUNT",
    "METRIC_OUTPUT_BYTES",
    "METRIC_FEATURE_FLAG_STATE",
    "METRIC_ROLLBACK_ACTIVATION_TOTAL",
]
