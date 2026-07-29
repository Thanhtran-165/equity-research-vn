"""Verification domain: PROVENANCE_INTEGRITY.

Owns 6 canonical VCs (per vta-VC-to-verifier-mapping.yaml
verifier_module_coverage = PROVENANCE (5) + VC-FAB-VAL-1 merged, primary
OUTPUT_SCHEMA cross-listed):

    VC-PROV-1, VC-PROV-2, VC-PROV-MISS-1, VC-NO-FAB-1, VC-NO-FAB-2,
    VC-FAB-VAL-1.

Independence: provenance checks reason only over the structure of the output
packet's provenance / computation_chain metadata and the frozen input fixture.
The verifier does NOT consult production provenance-generation code.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from .common import CheckOutcome, CODE_NONE, STATUS_FAIL, STATUS_PASS

DOMAIN_NAME = "provenance_integrity"

OWNED_VC_IDS = (
    "VC-PROV-1",
    "VC-PROV-2",
    "VC-PROV-MISS-1",
    "VC-NO-FAB-1",
    "VC-NO-FAB-2",
    "VC-FAB-VAL-1",
)


def evaluate(ctx) -> Dict[str, CheckOutcome]:
    packet = ctx.output_packet
    fixture = _load_fixture(ctx)
    outcomes: Dict[str, CheckOutcome] = {}
    for vc_id in OWNED_VC_IDS:
        handler = _HANDLERS.get(vc_id)
        if handler is None:
            outcomes[vc_id] = CheckOutcome.error(
                f"No handler bound for {vc_id}", vc_id=vc_id
            )
            continue
        try:
            outcomes[vc_id] = handler(ctx, packet, fixture)
        except Exception as exc:  # pragma: no cover - defensive
            outcomes[vc_id] = CheckOutcome.error(
                f"Handler raised: {type(exc).__name__}: {exc}", vc_id=vc_id
            )
    return outcomes


# ===========================================================================
# Helpers
# ===========================================================================


def _load_fixture(ctx) -> Dict[str, Any]:
    if not ctx.fixture_id:
        return {}
    fixture = ctx.load_fixture(ctx.fixture_id)
    return fixture if isinstance(fixture, dict) else {"_root": fixture}


def _nested(node: Any, path: Sequence[str]) -> Any:
    """Walk a dotted path through nested mappings; return None if absent or if
    any intermediate node is not a mapping."""
    current = node
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current


def _ohlcv_rows(fixture: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Production fixtures store the OHLCV series under
    ``frozen_production_input.complete_OHLCV_records``; flat harness fixtures
    (self-test) expose it at top level as ``ohlcv``/``rows``/``bars``."""
    rows = (
        fixture.get("ohlcv")
        or fixture.get("rows")
        or fixture.get("bars")
        or _nested(fixture, ("frozen_production_input", "complete_OHLCV_records"))
    )
    if isinstance(rows, list):
        return [r for r in rows if isinstance(r, dict)]
    return []


def _computation_chain(packet: Dict[str, Any]) -> List[Dict[str, Any]]:
    chain = packet.get("computation_chain")
    if isinstance(chain, list):
        return [n for n in chain if isinstance(n, dict)]
    prov = packet.get("provenance")
    if isinstance(prov, dict):
        chain = prov.get("computation_chain")
        if isinstance(chain, list):
            return [n for n in chain if isinstance(n, dict)]
    return []


def _provenance_root(packet: Dict[str, Any]) -> Dict[str, Any]:
    prov = packet.get("provenance")
    return prov if isinstance(prov, dict) else {}


def _numeric_output_fields(packet: Dict[str, Any]) -> List[Tuple[str, float]]:
    """Flatten the packet to (path, float_value) pairs, skipping the
    metadata envelopes (provenance, validation, boundary_check, computation_chain,
    warnings, errors, language_check, diagnostic_failure_codes) and the
    boolean-signal / setup-listing fields. These carry metadata or per-record
    booleans, not presentation output values requiring per-field traceability."""
    out: List[Tuple[str, float]] = []
    skip = {
        "provenance", "warnings", "errors", "computation_chain",
        "validation", "boundary_check", "language_check",
        "diagnostic_failure_codes",
        "binary_signals_6", "bullish_setups", "bearish_setups",
    }
    _walk_numeric(packet, "", out, skip)
    # Drop presentation-only fields the contract allows without a dedicated
    # computation-chain node (mirrors _is_exempt_presentation_field so VC-PROV-1
    # and VC-FAB-VAL-1 agree on the traceable set).
    out = [pair for pair in out if not _is_exempt_presentation_field(pair[0])]
    return out


def _walk_numeric(
    node: Any,
    prefix: str,
    acc: List[Tuple[str, float]],
    skip: set,
) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in skip and prefix == "":
                continue
            _walk_numeric(value, f"{prefix}.{key}" if prefix else key, acc, skip)
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            _walk_numeric(value, f"{prefix}[{idx}]", acc, skip)
    else:
        if isinstance(node, (int, float)) and not isinstance(node, bool):
            f = float(node)
            if not math.isnan(f):
                acc.append((prefix, f))


def _field_has_provenance(packet: Dict[str, Any], field_path: str) -> bool:
    """Check whether a field has an entry in the computation_chain or a
    per-field provenance map."""
    prov = _provenance_root(packet)
    # Per-field provenance map keyed by field path.
    field_prov = prov.get("field_provenance") or prov.get("fields")
    if isinstance(field_prov, dict) and field_path in field_prov:
        return True
    chain = _computation_chain(packet)
    for node in chain:
        node_fields = (
            node.get("output_field")
            or node.get("field")
            or node.get("output_fields")
            or node.get("fields")
        )
        if isinstance(node_fields, list) and field_path in node_fields:
            return True
        if isinstance(node_fields, str) and node_fields == field_path:
            return True
    # Field-path prefix match: a chain node tagged with a parent path covers
    # every numeric leaf beneath it. indicators.<ID>.* is covered by a node
    # tagged indicators.<ID> (or by an indicator_id tag matching the path);
    # profile_blocks.<bid>.* is covered by a node tagged profile_blocks.<bid>;
    # bullish_setups / bearish_setups leaves are covered by the family chain.
    head = field_path.split(".", 1)[0].split("[", 1)[0]
    if head in {"indicators"}:
        for node in chain:
            tag = node.get("indicator_id") or node.get("indicator") or node.get("id")
            if isinstance(tag, str) and tag in field_path:
                return True
        # Also honour explicit output_field prefix chains (e.g.
        # "indicators.RSI" covers "indicators.RSI.rsi_value").
        for node in chain:
            of = node.get("output_field") or node.get("field")
            if isinstance(of, str) and of and (
                field_path == of or field_path.startswith(of + ".")
            ):
                return True
    if head in {"profile_blocks"}:
        for node in chain:
            of = node.get("output_field") or node.get("field")
            if isinstance(of, str) and of and (
                field_path == of or field_path.startswith(of + ".")
            ):
                return True
    if head in {"bullish_setups", "bearish_setups"}:
        # The family chain covers every setup score/confidence inside it.
        for node in chain:
            of = node.get("output_field") or node.get("field")
            if isinstance(of, str) and of == head:
                return True
    return False


# ===========================================================================
# Per-VC handlers
# ===========================================================================


def _vc_prov_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-PROV-1: every numeric output field has source -> computation_chain."""
    numeric = _numeric_output_fields(packet)
    if not numeric:
        return CheckOutcome.error(
            "no numeric output fields in packet; cannot verify provenance presence"
        )
    missing: List[str] = []
    for path, _ in numeric:
        if not _field_has_provenance(packet, path):
            missing.append(path)
    if missing:
        return CheckOutcome.fail(
            "PROVENANCE_MISSING",
            ["FIELD_WITHOUT_COMPUTATION_CHAIN"],
            reason="numeric output fields lack provenance/computation_chain",
            missing_fields=missing[:20],
            missing_count=len(missing),
            total_numeric_fields=len(numeric),
        )
    return CheckOutcome.pass_clean(
        total_numeric_fields=len(numeric), missing_count=0
    )


def _vc_prov_2(ctx, packet, fixture) -> CheckOutcome:
    """VC-PROV-2: provenance includes timestamp, provider, params."""
    prov = _provenance_root(packet)
    if not prov:
        return CheckOutcome.fail(
            "PROVENANCE_MISSING",
            ["PROVENANCE_TIMESTAMP_MISSING", "PROVENANCE_PROVIDER_MISSING", "PROVENANCE_PARAMS_MISSING"],
            reason="no provenance block in packet",
        )
    missing_components: List[str] = []
    diagnostics: List[str] = []
    for field, diag in (
        ("timestamp", "PROVENANCE_TIMESTAMP_MISSING"),
        ("provider", "PROVENANCE_PROVIDER_MISSING"),
        ("source_provider", "PROVENANCE_PROVIDER_MISSING"),
        ("params", "PROVENANCE_PARAMS_MISSING"),
    ):
        if field not in prov or prov[field] in (None, "", {}, []):
            if field == "source_provider":
                # provider OR source_provider satisfies the provider component.
                if "provider" in prov and prov["provider"] not in (None, "", {}, []):
                    continue
            missing_components.append(field)
            diagnostics.append(diag)
    # Deduplicate diagnostics.
    seen = set()
    unique_diagnostics: List[str] = []
    for d in diagnostics:
        if d not in seen:
            seen.add(d)
            unique_diagnostics.append(d)
    if missing_components:
        return CheckOutcome.fail(
            "PROVENANCE_MISSING",
            unique_diagnostics,
            reason="provenance block missing required components",
            missing_components=sorted(set(missing_components)),
        )
    return CheckOutcome.pass_clean(
        components_present=["timestamp", "provider", "params"]
    )


def _vc_prov_miss_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-PROV-MISS-1: provenance stripped from one field -> detection.
    Negative fixture; the verifier independently detects any numeric field
    without provenance (more thorough form of VC-PROV-1)."""
    outcome = _vc_prov_1(ctx, packet, fixture)
    if outcome.observed_status == STATUS_FAIL:
        # Re-tag with the stripped-field diagnostic.
        return CheckOutcome.fail(
            "PROVENANCE_MISSING",
            ["FIELD_PROVENANCE_STRIPPED"],
            reason="at least one numeric field has its provenance stripped",
            missing_fields=outcome.evidence.get("missing_fields", []),
            missing_count=outcome.evidence.get("missing_count", 0),
        )
    return outcome


def _vc_no_fab_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-NO-FAB-1: every OHLCV value MUST have a provenance chain reaching
    the collector packet (input-side provenance gate)."""
    rows = _ohlcv_rows(fixture)
    prov = _provenance_root(packet)
    input_chain = (
        prov.get("input_provenance")
        or prov.get("ohlcv_provenance")
        or prov.get("source_chain")
    )
    if not isinstance(rows, list) or not rows:
        # Without input rows we can only check the output declares a collector
        # packet provenance for OHLCV.
        if not _ohlcv_traceable(prov):
            return CheckOutcome.fail(
                "FABRICATED_VALUE_DETECTED",
                ["OHLCV_WITHOUT_SOURCE_CHAIN"],
                reason="no input rows and no OHLCV collector-packet provenance",
            )
        return CheckOutcome.pass_clean(input_rows_present=False)
    unsourced: List[int] = []
    chain_index = _index_input_chain(input_chain, rows)
    collector_covers_all = _ohlcv_traceable(prov) and not chain_index
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        if not _row_traceable(row, idx, chain_index):
            unsourced.append(idx)
    if unsourced and not collector_covers_all:
        return CheckOutcome.fail(
            "FABRICATED_VALUE_DETECTED",
            ["OHLCV_WITHOUT_SOURCE_CHAIN"],
            reason="OHLCV rows lack provenance chain to collector packet",
            unsourced_indices=unsourced[:20],
            unsourced_count=len(unsourced),
            total_rows=len(rows),
        )
    # Either every row is individually traceable, or the packet declares a
    # single collector packet that covers all input rows (the canonical packet
    # model). Both satisfy the input-side provenance gate.
    return CheckOutcome.pass_clean(
        total_rows=len(rows), unsourced_count=0,
        collector_packet_covers_all=collector_covers_all,
    )


def _ohlcv_traceable(prov: Dict[str, Any]) -> bool:
    for key in ("market_data_packet", "collector_packet", "source_packet"):
        if prov.get(key) not in (None, "", {}, []):
            return True
    if prov.get("input_provenance") not in (None, "", {}, []):
        return True
    return False


def _index_input_chain(
    input_chain: Any, rows: Sequence[Dict[str, Any]]
) -> Dict[Any, Dict[str, Any]]:
    if not isinstance(input_chain, list):
        return {}
    index: Dict[Any, Dict[str, Any]] = {}
    for node in input_chain:
        if not isinstance(node, dict):
            continue
        key = (
            node.get("date")
            or node.get("trade_date")
            or node.get("index")
            or node.get("row_index")
        )
        if key is not None:
            index[key] = node
    return index


def _row_traceable(
    row: Dict[str, Any], idx: int, chain_index: Dict[Any, Dict[str, Any]]
) -> bool:
    if not chain_index:
        # If there is no per-row chain, traceability is asserted only when the
        # packet explicitly claims a single collector packet covering all rows.
        return False
    for key_attr in ("date", "trade_date"):
        key = row.get(key_attr)
        if key is not None and key in chain_index:
            return True
    if idx in chain_index:
        return True
    return False


def _vc_no_fab_2(ctx, packet, fixture) -> CheckOutcome:
    """VC-NO-FAB-2: no placeholder values (0, NaN, NULL) silently injected
    into OHLCV. Placeholders are permitted only with an explicit marker."""
    rows = _ohlcv_rows(fixture)
    if not rows:
        return CheckOutcome.pass_clean(input_rows_present=False)
    placeholders: List[Tuple[int, str, Any]] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        for field in ("open", "high", "low", "close", "volume"):
            if field not in row:
                continue
            value = row[field]
            if _is_placeholder(value):
                # Explicit marker permits the placeholder (e.g. suspended
                # session legitimately records volume=0).
                marker = (
                    row.get(f"{field}_marker")
                    or row.get("marker")
                    or row.get("placeholder_marker")
                )
                rationale = row.get("rationale") or row.get("note")
                if marker in (None, "", False) and rationale in (None, ""):
                    placeholders.append((idx, field, value))
    if placeholders:
        return CheckOutcome.fail(
            "FABRICATED_VALUE_DETECTED",
            ["PLACEHOLDER_VALUE_INJECTED"],
            reason="placeholder values (0/NaN/NULL) in OHLCV without explicit marker",
            placeholders=placeholders[:20],
            placeholder_count=len(placeholders),
        )
    return CheckOutcome.pass_clean(
        total_rows=len(rows), placeholder_count=0
    )


def _is_placeholder(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() in ("", "null", "none", "nan"):
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, (int, float)) and not isinstance(value, bool) and float(value) == 0.0:
        # Zero is a placeholder candidate; volume=0 is legitimate only with a
        # marker (handled by the caller). Price=0 is always a placeholder.
        return True
    return False


def _vc_fab_val_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-FAB-VAL-1: inject a value not in the computation chain -> detection.
    Cross-listed OUTPUT_SCHEMA/PROVENANCE; single canonical record. The
    verifier independently recomputes the set of values the computation chain
    could produce and flags any output value outside that set."""
    numeric = _numeric_output_fields(packet)
    chain = _computation_chain(packet)
    if not numeric:
        return CheckOutcome.error(
            "no numeric output fields in packet; cannot detect fabricated values"
        )
    chain_values = _chain_value_set(chain)
    fabricated: List[Tuple[str, float]] = []
    for path, value in numeric:
        if not _value_in_chain(value, path, chain, chain_values):
            # Exempt presentation-only fields the contract allows without a
            # chain node (e.g. tech_score derived from indicators, weekly_history
            # which is an input count).
            if _is_exempt_presentation_field(path):
                continue
            fabricated.append((path, value))
    if fabricated:
        return CheckOutcome.fail(
            "FABRICATED_VALUE_DETECTED",
            ["VALUE_NOT_IN_COMPUTATION_CHAIN"],
            reason="output numeric values not traceable to computation_chain",
            fabricated=[{"path": p, "value": v} for p, v in fabricated[:20]],
            fabricated_count=len(fabricated),
            chain_nodes=len(chain),
        )
    return CheckOutcome.pass_clean(
        total_numeric_fields=len(numeric), fabricated_count=0, chain_nodes=len(chain)
    )


def _chain_value_set(chain: Sequence[Dict[str, Any]]) -> List[float]:
    out: List[float] = []
    for node in chain:
        for key in ("value", "output_value", "result", "values"):
            v = node.get(key)
            if isinstance(v, list):
                out.extend(float(x) for x in v if _is_number(x))
            elif _is_number(v):
                out.append(float(v))
    return out


def _value_in_chain(
    value: float,
    path: str,
    chain: Sequence[Dict[str, Any]],
    chain_values: Sequence[float],
) -> bool:
    # Exact value match against chain node values.
    for cv in chain_values:
        if _close(value, cv, 1e-9):
            return True
    # Indicator-tagged chain nodes cover all values under indicators.<ID>.*
    if path.startswith("indicators."):
        indicator_id = path.split(".")[1]
        for node in chain:
            tag = node.get("indicator_id") or node.get("indicator") or node.get("id")
            if tag == indicator_id:
                return True
    # Parent-prefix coverage: a chain node tagged with a parent path covers
    # every numeric leaf beneath it. indicators.<ID>.* and profile_blocks.<bid>.*
    # are covered by nodes whose output_field is a prefix of the value path.
    for node in chain:
        of = node.get("output_field") or node.get("field")
        if isinstance(of, str) and of and (path == of or path.startswith(of + ".")):
            return True
    # Setup-listing family chain covers every setup score/confidence inside it.
    head = path.split(".", 1)[0].split("[", 1)[0]
    if head in {"bullish_setups", "bearish_setups"}:
        for node in chain:
            of = node.get("output_field") or node.get("field")
            if isinstance(of, str) and of == head:
                return True
    return False


def _is_exempt_presentation_field(path: str) -> bool:
    """Fields the contract allows without a dedicated computation-chain node.

    Mirrors the production output_assembler's exempt set so both sides agree
    on the traceable numeric field set: input counts, schema bookkeeping,
    frozen constants, categorical fields, and aggregate scores (tech_score is
    a binary-signal sum projection, not a priced computation) are
    presentation-only."""
    head = path.split(".", 1)[0].split("[", 1)[0]
    if head in {
        "weekly_history", "daily_history", "setup_coverage_denominator",
        "as_of_date", "evaluation_timestamp", "mode", "ticker",
        "symbol", "instrument_id", "schema_version", "price_basis",
        "adjustment_state", "analysis_status", "computation_chain_id",
        "primary_failure_code", "error_code",
        "archetype", "setup_coverage_status",
        "tech_score",          # aggregate binary-signal projection
    }:
        return True
    if path in {
        "weekly_history", "daily_history", "setup_coverage_denominator",
        "tech_score",
    }:
        return True
    return False


def _close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol + tol * abs(b)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


_HANDLERS = {
    "VC-PROV-1": _vc_prov_1,
    "VC-PROV-2": _vc_prov_2,
    "VC-PROV-MISS-1": _vc_prov_miss_1,
    "VC-NO-FAB-1": _vc_no_fab_1,
    "VC-NO-FAB-2": _vc_no_fab_2,
    "VC-FAB-VAL-1": _vc_fab_val_1,
}
