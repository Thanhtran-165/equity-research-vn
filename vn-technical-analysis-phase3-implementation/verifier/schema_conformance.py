"""Verification domain: SCHEMA_CONFORMANCE.

Owns 23 canonical VCs (per vta-VC-to-verifier-mapping.yaml
verifier_module_coverage = INPUT_PRE_FLIGHT (14) + OUTPUT_SCHEMA (11) -
overlaps + MODE_SEP schema):

  INPUT_PRE_FLIGHT (excluding price-basis recompute owned by formula domain
  and excluding VC-FAB-VAL-1 owned by provenance domain):
    VC-EMPTY-SERIES-1, VC-INHIST-1, VC-DUP-TS-1, VC-UNSORTED-1,
    VC-MISS-INT-1, VC-ZERO-PX-1, VC-ZERO-VOL-1, VC-CORP-ACT-1,
    VC-BENCH-MISALIGN-1, VC-PARTIAL-WEEK-1, VC-PRICE-BASIS-3,
    VC-NAN-PROP-1

  OUTPUT_SCHEMA / MODE_SEPARATION:
    VC-ACTIVE-VALID-1, VC-ACTIVE-VALID-2, VC-ACTIVE-VALID-3,
    VC-PROFILE-VALID-1, VC-PROFILE-VALID-2, VC-PROFILE-VALID-3,
    VC-SCHEMA-DRIFT-1, VC-MODE-SEP-1, VC-MODE-SEP-2, VC-MODE-SEP-3,
    VC-MODE-CONTAM-1

Independence: schema/mode checks reason over the JSON shape of the output
packet and the frozen input fixture only. No production schema validator is
imported; the verifier implements the additionalProperties:false /
required-key / type checks independently from the contract descriptions.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .common import CheckOutcome, CODE_NONE, STATUS_FAIL, STATUS_PASS

DOMAIN_NAME = "schema_conformance"

OWNED_VC_IDS = (
    # INPUT_PRE_FLIGHT
    "VC-EMPTY-SERIES-1",
    "VC-INHIST-1",
    "VC-DUP-TS-1",
    "VC-UNSORTED-1",
    "VC-MISS-INT-1",
    "VC-ZERO-PX-1",
    "VC-ZERO-VOL-1",
    "VC-CORP-ACT-1",
    "VC-BENCH-MISALIGN-1",
    "VC-PARTIAL-WEEK-1",
    "VC-PRICE-BASIS-3",
    "VC-NAN-PROP-1",
    # OUTPUT_SCHEMA
    "VC-ACTIVE-VALID-1",
    "VC-ACTIVE-VALID-2",
    "VC-ACTIVE-VALID-3",
    "VC-PROFILE-VALID-1",
    "VC-PROFILE-VALID-2",
    "VC-PROFILE-VALID-3",
    "VC-SCHEMA-DRIFT-1",
    # MODE_SEPARATION
    "VC-MODE-SEP-1",
    "VC-MODE-SEP-2",
    "VC-MODE-SEP-3",
    "VC-MODE-CONTAM-1",
)

# Mode-detection heuristics. The packet declares its mode explicitly when
# possible; otherwise the verifier infers from the presence of mode-specific
# keys (tech_score => ACTIVE, profile_blocks => PROFILE).
_ACTIVE_KEYS = {"tech_score", "binary_signals_6", "six_binary_signals"}
_PROFILE_KEYS = {"profile_blocks", "blocks", "setups", "archetype"}
_ACTIVE_INDICATORS = {"MA", "RSI", "MACD", "BB", "Beta", "CMF"}
_PROFILE_BLOCK_COUNT = 17
_ACTIVE_INDICATOR_COUNT = 6
_WEEKLY_BASELINE = 52
_DAILY_BASELINE = 60


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
# Shared helpers
# ===========================================================================


def _load_fixture(ctx) -> Dict[str, Any]:
    if not ctx.fixture_id:
        return {}
    fixture = ctx.load_fixture(ctx.fixture_id)
    return fixture if isinstance(fixture, dict) else {"_root": fixture}


def _detect_mode(packet: Dict[str, Any]) -> str:
    mode = packet.get("mode")
    if isinstance(mode, str):
        return mode.upper()
    if any(k in packet for k in _ACTIVE_KEYS):
        return "ACTIVE"
    if any(k in packet for k in _PROFILE_KEYS):
        return "PROFILE"
    # Default to ACTIVE when 6-indicator block present.
    indicators = packet.get("indicators")
    if isinstance(indicators, dict) and _ACTIVE_INDICATORS & set(indicators.keys()):
        return "ACTIVE"
    return "UNKNOWN"



def _error_code_str(packet: Dict[str, Any]) -> Optional[str]:
    """Extract error_code as string, handling ErrorEnvelope objects."""
    ec = packet.get("error_code")
    if ec is None:
        return None
    if isinstance(ec, str):
        return ec
    if isinstance(ec, dict):
        return ec.get("error_code") or ec.get("code")
    # ErrorEnvelope-like object
    if hasattr(ec, "error_code"):
        return str(ec.error_code)
    return str(ec)

def _ohlcv_rows(fixture: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Production fixtures store the OHLCV series under
    # ``frozen_production_input.complete_OHLCV_records``. The flat harness
    # fixtures (self-test) expose it at top level as ``ohlcv``/``rows``/``bars``.
    rows = (
        fixture.get("ohlcv")
        or fixture.get("rows")
        or fixture.get("bars")
        or _nested(fixture, ("frozen_production_input", "complete_OHLCV_records"))
    )
    if isinstance(rows, list):
        return [r for r in rows if isinstance(r, dict)]
    return []


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


def _fixture_field(fixture: Dict[str, Any], *names: str) -> Any:
    """Look up a scalar field that may live at the top of the fixture or nested
    under ``frozen_production_input``. Returns the first non-None hit, else None."""
    for name in names:
        if name in fixture and fixture[name] is not None:
            return fixture[name]
    return _nested(fixture, ("frozen_production_input", names[0])) if names else None


def _dates(rows: Sequence[Dict[str, Any]]) -> List[str]:
    out = []
    for r in rows:
        d = r.get("date") or r.get("trade_date") or r.get("timestamp")
        if d is not None:
            out.append(str(d))
    return out


def _is_nan(value: Any) -> bool:
    if isinstance(value, float):
        return math.isnan(value)
    if isinstance(value, str):
        return value.strip().lower() in ("nan", "none", "null")
    return False


def _walk_numeric(node: Any, prefix: str = "") -> Iterable[Tuple[str, Any]]:
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _walk_numeric(value, f"{prefix}.{key}" if prefix else key)
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            yield from _walk_numeric(value, f"{prefix}[{idx}]")
    else:
        if isinstance(node, (int, float)):
            yield prefix, node


def _foreign_keys(packet: Dict[str, Any], allowed: Iterable[str]) -> List[str]:
    allowed_set = set(allowed)
    return sorted(k for k in packet.keys() if k not in allowed_set)


# Allowed top-level keys per mode (independent reimplementation from contract
# descriptions; production schemas are not imported). These mirror the shared
# canonical packet field contract (R3 directive) plus the per-mode legacy /
# envelope keys. The canonical shared set is duplicated here (frozen data, not
# imported from production) so the verifier stays inside its independence
# boundary while agreeing with production on the schema surface.
_CANONICAL_SHARED_KEYS = {
    "schema_version",
    "mode",
    "instrument_id",
    "evaluation_timestamp",
    "price_basis",
    "adjustment_state",
    "weekly_history",
    "daily_history",
    "indicators",
    "profile_blocks",
    "bullish_setups",
    "bearish_setups",
    "archetype",
    "tech_score",
    "setup_coverage_status",
    "setup_coverage_denominator",
    "analysis_status",
    "primary_failure_code",
    "diagnostic_failure_codes",
    "provenance",
    "computation_chain_id",
    "computation_chain",
    "error_code",
}

# Envelope / legacy / context keys present alongside the body after the
# verifier's packet normalizer flattens the production OutputPacket envelope.
_ENVELOPE_KEYS = {
    "as_of_date", "symbol", "ticker",
    "validation", "warnings", "errors", "boundary_check", "is_valid",
    "language_check", "benchmark", "status", "fixture_id", "target_VC_ids",
    "lookahead_safe", "causal",
    "blocks", "setups", "setup_coverage",
    "conflict_behavior", "bull_bear_conflict_resolution",
    "six_binary_signals",
}

_ACTIVE_ALLOWED_TOP = _CANONICAL_SHARED_KEYS | _ENVELOPE_KEYS | {
    "binary_signals_6",
}
_PROFILE_ALLOWED_TOP = _CANONICAL_SHARED_KEYS | _ENVELOPE_KEYS


# ===========================================================================
# INPUT_PRE_FLIGHT handlers
# ===========================================================================


def _vc_empty_series_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-EMPTY-SERIES-1: empty OHLCV input must produce an error envelope
    with error_code=INSUFFICIENT_HISTORY (FM-EMPTY-SERIES). The error envelope
    suppresses all other codes (pre-flight short-circuit)."""
    rows = _ohlcv_rows(fixture)
    is_empty_case = len(rows) == 0 or bool(fixture.get("empty_input"))
    error_code = _error_code_str(packet)
    has_partial_output = _has_computation_output(packet)
    if is_empty_case:
        if error_code == "INSUFFICIENT_HISTORY" and not has_partial_output:
            return CheckOutcome.pass_clean(
                empty_series_correctly_rejected=True,
                error_code=error_code,
            )
        return CheckOutcome.fail(
            "INSUFFICIENT_HISTORY",
            ["EMPTY_SERIES_DETECTED"],
            reason=(
                "empty input did not produce the contracted INSUFFICIENT_HISTORY "
                "error envelope (or produced partial output)"
            ),
            observed_error_code=error_code,
            partial_output_present=has_partial_output,
        )
    # Non-empty input: this VC is silent (no INSUFFICIENT_HISTORY from emptiness).
    return CheckOutcome.pass_clean(empty_input=False)


def _has_computation_output(packet: Dict[str, Any]) -> bool:
    for key in ("indicators", "profile_blocks", "blocks", "tech_score"):
        if packet.get(key) not in (None, {}, []):
            return True
    return False


def _vc_inhist_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-INHIST-1: ACTIVE 51w -> INSUFFICIENT_HISTORY; PROFILE 59d ->
    INSUFFICIENT_HISTORY. Boundaries: 52w / 60d exact pass."""
    rows = _ohlcv_rows(fixture)
    mode = _detect_mode(packet) or str(fixture.get("mode", "")).upper() or "ACTIVE"
    error_code = _error_code_str(packet)
    if not rows:
        return CheckOutcome.error(
            "no OHLCV rows in fixture; cannot evaluate history baseline"
        )
    count = len(rows)
    if mode.startswith("ACTIVE"):
        baseline = _WEEKLY_BASELINE
        below = count < baseline
    else:
        baseline = _DAILY_BASELINE
        below = count < baseline
    if below:
        if error_code == "INSUFFICIENT_HISTORY":
            return CheckOutcome.pass_clean(
                insufficient_history_correctly_rejected=True,
                error_code=error_code,
                mode=mode,
                provided_sessions=count,
                required_sessions=baseline,
            )
        return CheckOutcome.fail(
            "INSUFFICIENT_HISTORY",
            [
                "ACTIVE_51W_BELOW_52_BASELINE"
                if mode.startswith("ACTIVE")
                else "PROFILE_59D_BELOW_60_BASELINE"
            ],
            reason=(
                f"{mode} input below {baseline}-session baseline was not rejected "
                "with INSUFFICIENT_HISTORY"
            ),
            mode=mode,
            provided_sessions=count,
            required_sessions=baseline,
            observed_error_code=error_code,
        )
    return CheckOutcome.pass_clean(
        mode=mode,
        provided_sessions=count,
        required_sessions=baseline,
        below_baseline=False,
    )


def _vc_dup_ts_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-DUP-TS-1: duplicate timestamps must be deduped (last-value-wins)
    with a warning in provenance; analysis_status=VALID_WITH_WARNINGS."""
    rows = _ohlcv_rows(fixture)
    dates_seq = _dates(rows)
    if not dates_seq:
        return CheckOutcome.error("no dated rows in fixture")
    has_dupes = len(dates_seq) != len(set(dates_seq))
    status = packet.get("analysis_status")
    warnings = _provenance_warnings(packet)
    dedup_warned = any("dedup" in str(w).lower() for w in warnings)
    if has_dupes:
        if status == "VALID_WITH_WARNINGS" and dedup_warned:
            return CheckOutcome.fail(
                "DUPLICATE_TIMESTAMP_DEDUPED",
                ["DUPLICATE_TIMESTAMP_DEDUPED"],
                reason="duplicate timestamps deduped with warning",
                duplicate_count=len(dates_seq) - len(set(dates_seq)),
            )
        return CheckOutcome.fail(
            "DUPLICATE_TIMESTAMP_DEDUPED",
            ["DUPLICATE_TIMESTAMP_DEDUPED"],
            reason=(
                "duplicate timestamps present but engine did not emit "
                "VALID_WITH_WARNINGS + dedup warning"
            ),
            duplicate_count=len(dates_seq) - len(set(dates_seq)),
            observed_status=status,
            dedup_warned=dedup_warned,
        )
    return CheckOutcome.pass_clean(duplicates_present=False)


def _vc_unsorted_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-UNSORTED-1: unsorted input must be sorted ascending with a warning."""
    rows = _ohlcv_rows(fixture)
    dates_seq = _dates(rows)
    if not dates_seq:
        return CheckOutcome.error("no dated rows in fixture")
    is_sorted = all(dates_seq[i] <= dates_seq[i + 1] for i in range(len(dates_seq) - 1))
    status = packet.get("analysis_status")
    warnings = _provenance_warnings(packet)
    sort_warned = any("sort" in str(w).lower() for w in warnings)
    if not is_sorted:
        if status == "VALID_WITH_WARNINGS" and sort_warned:
            return CheckOutcome.fail(
                "UNSORTED_TIMESTAMP_SORTED",
                ["UNSORTED_TIMESTAMP_SORTED"],
                reason="unsorted input sorted with warning",
            )
        return CheckOutcome.fail(
            "UNSORTED_TIMESTAMP_SORTED",
            ["UNSORTED_TIMESTAMP_SORTED"],
            reason=(
                "unsorted input not handled with VALID_WITH_WARNINGS + sort warning"
            ),
            observed_status=status,
            sort_warned=sort_warned,
        )
    return CheckOutcome.pass_clean(unsorted_input=False)


def _vc_miss_int_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-MISS-INT-1: 10% gaps -> warning, output still valid. Triggering
    condition (registry): actual_trading_days / expected_trading_days < 0.95."""
    rows = _ohlcv_rows(fixture)
    if not rows:
        return CheckOutcome.error("no OHLCV rows in fixture")
    dates_seq = _dates(rows)
    if not dates_seq:
        return CheckOutcome.error("no dated rows in fixture")
    expected = _fixture_field(fixture, "expected_trading_days", "expected_sessions")
    actual = len(dates_seq)
    if expected is None:
        # No declared expected-trading-days baseline. Without a frozen
        # expectation the gap-ratio obligation cannot be evaluated; PASS silent
        # rather than inferring a calendar baseline that misclassifies weekly
        # data as gapped daily data.
        return CheckOutcome.pass_clean(
            actual_days=actual, expected_declared=False,
        )
    try:
        expected_int = int(expected)
    except (TypeError, ValueError):
        return CheckOutcome.error("expected_trading_days is not an integer")
    ratio = actual / expected_int if expected_int else 1.0
    status = packet.get("analysis_status")
    warnings = _provenance_warnings(packet)
    gap_warned = any("gap" in str(w).lower() or "missing" in str(w).lower() for w in warnings)
    if ratio < 0.95:
        if status == "VALID_WITH_WARNINGS" and gap_warned:
            # Engine correctly warned about the missing-interval gap.
            return CheckOutcome.pass_clean(
                actual_days=actual, expected_days=expected_int, ratio=ratio,
                gap_warned=True,
            )
        return CheckOutcome.fail(
            "MISSING_INTERVAL",
            ["MISSING_INTERVAL_WARNING"],
            reason=(
                "gap ratio below 0.95 did not produce VALID_WITH_WARNINGS + "
                "missing-interval warning"
            ),
            actual_days=actual,
            expected_days=expected_int,
            ratio=ratio,
            observed_status=status,
            gap_warned=gap_warned,
        )
    return CheckOutcome.pass_clean(
        actual_days=actual, expected_days=expected_int, ratio=ratio
    )


def _vc_zero_px_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-ZERO-PX-1: any OHLC == 0 -> fail-closed with ZERO_PRICE_DETECTED."""
    rows = _ohlcv_rows(fixture)
    zero_fields = []
    for r in rows:
        for field in ("open", "high", "low", "close"):
            v = r.get(field)
            if _is_finite(v) and float(v) == 0.0:
                zero_fields.append((r.get("date"), field))
    error_code = _error_code_str(packet)
    has_partial = _has_computation_output(packet)
    if zero_fields:
        if error_code == "ZERO_PRICE_DETECTED" and not has_partial:
            return CheckOutcome.pass_clean(
                zero_price_correctly_rejected=True,
                error_code=error_code,
                zero_count=len(zero_fields),
            )
        return CheckOutcome.fail(
            "ZERO_PRICE_DETECTED",
            ["ZERO_PRICE_DETECTED"],
            reason=(
                "zero price in OHLC did not produce ZERO_PRICE_DETECTED error "
                "envelope with no partial output"
            ),
            zero_count=len(zero_fields),
            observed_error_code=error_code,
            partial_output_present=has_partial,
        )
    return CheckOutcome.pass_clean(zero_price_present=False)


def _vc_zero_vol_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-ZERO-VOL-1: zero-volume session accepted, value=0, no warning
    (legitimate suspended session). Canonical emission is the DIAGNOSTIC
    ZERO_VOLUME_ACCEPTED which is 'Never PRIMARY' by design; the verifier
    reports PASS (clean) when the engine does NOT raise it as an error."""
    rows = _ohlcv_rows(fixture)
    zero_vol_dates = [
        r.get("date") for r in rows if _is_finite(r.get("volume")) and float(r.get("volume")) == 0.0
    ]
    if not zero_vol_dates:
        return CheckOutcome.pass_clean(zero_volume_present=False)
    error_code = _error_code_str(packet)
    has_partial = _has_computation_output(packet)
    # If engine produced a clean output (no error) the obligation is met; the
    # DIAGNOSTIC is design-as-primary but surfaces as analysis_status context,
    # never as an error.
    if error_code is None and has_partial:
        return CheckOutcome.pass_clean(
            zero_volume_present=True,
            zero_volume_dates=zero_vol_dates,
            diagnostic="ZERO_VOLUME_ACCEPTED (design-as-primary DIAGNOSTIC)",
        )
    if error_code is not None:
        return CheckOutcome.fail(
            "ZERO_VOLUME_ACCEPTED",
            [],
            reason=(
                "zero-volume session was rejected with an error code; contract "
                "requires acceptance as legitimate suspended session"
            ),
            observed_error_code=error_code,
            zero_volume_dates=zero_vol_dates,
        )
    return CheckOutcome.pass_clean(
        zero_volume_present=True, zero_volume_dates=zero_vol_dates
    )


def _vc_corp_act_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-CORP-ACT-1: adjustment_status=UNKNOWN -> fail-closed with
    UNKNOWN_ADJUSTMENT_STATUS."""
    rows = _ohlcv_rows(fixture)
    unknown_dates = [
        r.get("date")
        for r in rows
        if str(r.get("adjustment_status", "")).upper() == "UNKNOWN"
    ]
    error_code = _error_code_str(packet)
    has_partial = _has_computation_output(packet)
    if unknown_dates:
        if error_code == "UNKNOWN_ADJUSTMENT_STATUS" and not has_partial:
            return CheckOutcome.fail(
                "UNKNOWN_ADJUSTMENT_STATUS",
                ["CONFLICTING_ADJUSTMENT_STATUS"],
                reason="UNKNOWN adjustment_status correctly rejected",
                unknown_count=len(unknown_dates),
            )
        return CheckOutcome.fail(
            "UNKNOWN_ADJUSTMENT_STATUS",
            ["CONFLICTING_ADJUSTMENT_STATUS"],
            reason=(
                "UNKNOWN adjustment_status did not produce UNKNOWN_ADJUSTMENT_STATUS "
                "error envelope with no partial output"
            ),
            unknown_count=len(unknown_dates),
            observed_error_code=error_code,
            partial_output_present=has_partial,
        )
    return CheckOutcome.pass_clean(unknown_adjustment_present=False)


def _vc_bench_misalign_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-BENCH-MISALIGN-1: misaligned dates -> inner-join + warning;
    None benchmark -> BENCHMARK_UNAVAILABLE error."""
    benchmark_declared = (
        "benchmark" in fixture
        or "benchmark_series" in fixture
        or _fixture_field(fixture, "benchmark_none") is True
    )
    benchmark = _fixture_field(fixture, "benchmark", "benchmark_series")
    # Only treat as a benchmark-none TEST CASE when the fixture explicitly
    # declares a null/absent benchmark (a benchmark key set to null, or the
    # benchmark_none flag). A fixture that simply does not mention benchmark
    # is not a benchmark case at all and the VC is silent.
    benchmark_none = benchmark_declared and (
        benchmark is None or _fixture_field(fixture, "benchmark_none") is True
    )
    error_code = _error_code_str(packet)
    status = packet.get("analysis_status")
    warnings = _provenance_warnings(packet)
    bench_warned = any(
        "benchmark" in str(w).lower() or "misalign" in str(w).lower()
        for w in warnings
    )
    overlap = _fixture_field(fixture, "overlap_ratio")
    if benchmark_none:
        if error_code == "BENCHMARK_UNAVAILABLE":
            return CheckOutcome.fail(
                "BENCHMARK_UNAVAILABLE",
                ["BENCHMARK_UNAVAILABLE"],
                reason="None benchmark correctly produced BENCHMARK_UNAVAILABLE",
            )
        return CheckOutcome.fail(
            "BENCHMARK_UNAVAILABLE",
            ["BENCHMARK_UNAVAILABLE"],
            reason="None benchmark did not produce BENCHMARK_UNAVAILABLE error",
            observed_error_code=error_code,
        )
    # Misalignment path: benchmark present but overlap < 0.95.
    misaligned = (
        (overlap is not None and float(overlap) < 0.95)
        or fixture.get("benchmark_misaligned") is True
    )
    if misaligned:
        if status == "VALID_WITH_WARNINGS" and bench_warned:
            return CheckOutcome.fail(
                "BENCHMARK_MISALIGNED",
                ["BENCHMARK_UNAVAILABLE"],
                reason="benchmark misalignment correctly warned",
                overlap_ratio=overlap,
            )
        return CheckOutcome.fail(
            "BENCHMARK_MISALIGNED",
            ["BENCHMARK_UNAVAILABLE"],
            reason=(
                "benchmark misalignment did not produce VALID_WITH_WARNINGS + "
                "benchmark warning"
            ),
            overlap_ratio=overlap,
            observed_status=status,
            bench_warned=bench_warned,
        )
    return CheckOutcome.pass_clean(
        benchmark_none=False, misaligned=False, overlap_ratio=overlap
    )


def _vc_partial_week_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-PARTIAL-WEEK-1: latest weekly bar < 5 trading days -> dropped,
    warning logged. ACTIVE-only."""
    fixture_mode = _fixture_field(fixture, "mode")
    if not str(fixture_mode or "").upper().startswith("ACTIVE") and (
        _detect_mode(packet) != "ACTIVE"
    ):
        # Not an ACTIVE case; VC is silent.
        return CheckOutcome.pass_clean(active_mode=False)
    partial = _fixture_field(fixture, "partial_week", "latest_week_trading_days")
    has_partial_flag = _fixture_field(fixture, "has_partial_week")
    is_partial = (
        partial is not None
        and _is_finite(partial)
        and float(partial) < 5
    ) or has_partial_flag is True
    status = packet.get("analysis_status")
    warnings = _provenance_warnings(packet)
    partial_warned = any("partial" in str(w).lower() for w in warnings)
    if is_partial:
        if status == "VALID_WITH_WARNINGS" and partial_warned:
            return CheckOutcome.fail(
                "PARTIAL_WEEK_DROPPED",
                ["PARTIAL_WEEK_DROPPED"],
                reason="partial week correctly dropped with warning",
            )
        return CheckOutcome.fail(
            "PARTIAL_WEEK_DROPPED",
            ["PARTIAL_WEEK_DROPPED"],
            reason=(
                "partial week not handled with VALID_WITH_WARNINGS + partial warning"
            ),
            observed_status=status,
            partial_warned=partial_warned,
        )
    return CheckOutcome.pass_clean(partial_week_present=False)


def _vc_price_basis_3(ctx, packet, fixture) -> CheckOutcome:
    """VC-PRICE-BASIS-3: fail-closed on UNKNOWN adjustment status. Companion
    to VC-CORP-ACT-1 but verifies the price-basis-selection fail-closed path."""
    rows = _ohlcv_rows(fixture)
    unknown = any(
        str(r.get("adjustment_status", "")).upper() == "UNKNOWN" for r in rows
    )
    error_code = _error_code_str(packet)
    if unknown:
        if error_code == "UNKNOWN_ADJUSTMENT_STATUS":
            return CheckOutcome.fail(
                "UNKNOWN_ADJUSTMENT_STATUS",
                ["CONFLICTING_ADJUSTMENT_STATUS"],
                reason="UNKNOWN adjustment correctly fail-closed on price-basis path",
            )
        return CheckOutcome.fail(
            "UNKNOWN_ADJUSTMENT_STATUS",
            ["CONFLICTING_ADJUSTMENT_STATUS"],
            reason="UNKNOWN adjustment did not fail-closed on price-basis path",
            observed_error_code=error_code,
        )
    return CheckOutcome.pass_clean(unknown_adjustment_present=False)


def _vc_nan_prop_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-NAN-PROP-1: NaN in a required output field -> NAN_PROPAGATION
    error; no NaN reaches output. POST_COMPUTE check."""
    leaked: List[str] = []
    skip_paths = {"provenance", "warnings", "errors"}
    for path, value in _walk_numeric(packet):
        # Skip provenance/warning envelopes (NaN may be recorded there as
        # diagnostic context, not as a required output value).
        top = path.split(".", 1)[0].split("[", 1)[0]
        if top in skip_paths:
            continue
        if isinstance(value, float) and math.isnan(value):
            leaked.append(path)
    if leaked:
        return CheckOutcome.fail(
            "NAN_PROPAGATION",
            ["NAN_IN_REQUIRED_FIELD"],
            reason="NaN reached a required output field",
            leaked_fields=leaked[:20],
            leaked_count=len(leaked),
        )
    return CheckOutcome.pass_clean(leaked_count=0)


# ===========================================================================
# OUTPUT_SCHEMA / MODE_SEPARATION handlers
# ===========================================================================


def _vc_active_valid_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-ACTIVE-VALID-1: ACTIVE output satisfies the ACTIVE schema. The
    verifier checks the contractually-required top-level keys and types."""
    if _detect_mode(packet) not in ("ACTIVE", "UNKNOWN"):
        return CheckOutcome.pass_clean(non_active_packet=True)
    missing = _missing_active_required_keys(packet)
    foreign = _foreign_keys(packet, _ACTIVE_ALLOWED_TOP)
    if missing:
        return CheckOutcome.fail(
            "SCHEMA_VALIDATION_FAILED",
            ["JSONSCHEMA_REJECTION"],
            reason="ACTIVE output missing required keys",
            missing=missing,
        )
    if foreign:
        return CheckOutcome.fail(
            "SCHEMA_VALIDATION_FAILED",
            ["JSONSCHEMA_REJECTION"],
            reason="ACTIVE output contains foreign top-level keys",
            foreign=foreign,
        )
    return CheckOutcome.pass_clean(mode="ACTIVE")


def _missing_active_required_keys(packet: Dict[str, Any]) -> List[str]:
    required = ("mode", "as_of_date", "indicators")
    return [k for k in required if k not in packet]


def _vc_active_valid_2(ctx, packet, fixture) -> CheckOutcome:
    """VC-ACTIVE-VALID-2: weekly history >= 52 baseline (output-side recheck
    of VC-INHIST-1 for ACTIVE). ACTIVE-only: silent on non-ACTIVE packets
    (PROFILE has no weekly bars by design)."""
    if _detect_mode(packet) != "ACTIVE":
        return CheckOutcome.pass_clean(non_active_packet=True)
    history = packet.get("weekly_history")
    if _is_finite(history):
        if int(float(history)) < _WEEKLY_BASELINE:
            return CheckOutcome.fail(
                "INSUFFICIENT_HISTORY",
                ["WEEKLY_BELOW_52_BASELINE"],
                reason="weekly_history below 52 baseline",
                weekly_history=int(float(history)),
                baseline=_WEEKLY_BASELINE,
            )
        return CheckOutcome.pass_clean(
            weekly_history=int(float(history)), baseline=_WEEKLY_BASELINE
        )
    # If weekly_history absent but error_code present, that's a valid fail-closed.
    if packet.get("error_code") == "INSUFFICIENT_HISTORY":
        return CheckOutcome.fail(
            "INSUFFICIENT_HISTORY",
            ["WEEKLY_BELOW_52_BASELINE"],
            reason="weekly_history absent and engine fail-closed with INSUFFICIENT_HISTORY",
        )
    return CheckOutcome.fail(
        "INSUFFICIENT_HISTORY",
        ["WEEKLY_BELOW_52_BASELINE"],
        reason="weekly_history field absent without INSUFFICIENT_HISTORY error",
    )


def _vc_active_valid_3(ctx, packet, fixture) -> CheckOutcome:
    """VC-ACTIVE-VALID-3: 6 indicators all present or fail-closed with
    error_code. ACTIVE-only: silent on non-ACTIVE packets (PROFILE has no
    ACTIVE indicators by design)."""
    if _detect_mode(packet) != "ACTIVE":
        return CheckOutcome.pass_clean(non_active_packet=True)
    indicators = packet.get("indicators")
    if isinstance(indicators, dict):
        present = sorted(set(_ACTIVE_INDICATORS) & set(indicators.keys()))
        missing = sorted(set(_ACTIVE_INDICATORS) - set(indicators.keys()))
    elif isinstance(indicators, list):
        present_ids = {
            (n.get("id") or n.get("name") or n.get("indicator"))
            for n in indicators
            if isinstance(n, dict)
        }
        present = sorted(set(_ACTIVE_INDICATORS) & present_ids)
        missing = sorted(set(_ACTIVE_INDICATORS) - present_ids)
    else:
        present, missing = [], list(_ACTIVE_INDICATORS)
    if missing and not packet.get("error_code"):
        return CheckOutcome.fail(
            "INDICATOR_MISSING",
            ["PARTIAL_INDICATOR_OUTPUT"],
            reason="fewer than 6 mandatory ACTIVE indicators without error_code",
            present=present,
            missing=missing,
        )
    if missing and packet.get("error_code"):
        return CheckOutcome.fail(
            "INDICATOR_MISSING",
            ["PARTIAL_INDICATOR_OUTPUT"],
            reason="indicators missing but engine fail-closed with error_code",
            present=present,
            missing=missing,
            error_code=packet.get("error_code"),
        )
    return CheckOutcome.pass_clean(present=present, count=len(present))


def _vc_profile_valid_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-PROFILE-VALID-1: PROFILE output satisfies the PROFILE schema."""
    if _detect_mode(packet) not in ("PROFILE", "UNKNOWN"):
        return CheckOutcome.pass_clean(non_profile_packet=True)
    missing = _missing_profile_required_keys(packet)
    foreign = _foreign_keys(packet, _PROFILE_ALLOWED_TOP)
    if missing:
        return CheckOutcome.fail(
            "SCHEMA_VALIDATION_FAILED",
            ["JSONSCHEMA_REJECTION"],
            reason="PROFILE output missing required keys",
            missing=missing,
        )
    if foreign:
        return CheckOutcome.fail(
            "SCHEMA_VALIDATION_FAILED",
            ["JSONSCHEMA_REJECTION"],
            reason="PROFILE output contains foreign top-level keys",
            foreign=foreign,
        )
    return CheckOutcome.pass_clean(mode="PROFILE")


def _missing_profile_required_keys(packet: Dict[str, Any]) -> List[str]:
    required = ("mode", "as_of_date")
    return [k for k in required if k not in packet]


def _vc_profile_valid_2(ctx, packet, fixture) -> CheckOutcome:
    """VC-PROFILE-VALID-2: daily history >= 60 sessions (output-side recheck
    of VC-INHIST-1 for PROFILE). PROFILE-only: silent on non-PROFILE packets."""
    if _detect_mode(packet) != "PROFILE":
        return CheckOutcome.pass_clean(non_profile_packet=True)
    history = packet.get("daily_history")
    if _is_finite(history):
        if int(float(history)) < _DAILY_BASELINE:
            return CheckOutcome.fail(
                "INSUFFICIENT_HISTORY",
                ["DAILY_BELOW_60_BASELINE"],
                reason="daily_history below 60 baseline",
                daily_history=int(float(history)),
                baseline=_DAILY_BASELINE,
            )
        return CheckOutcome.pass_clean(
            daily_history=int(float(history)), baseline=_DAILY_BASELINE
        )
    if packet.get("error_code") == "INSUFFICIENT_HISTORY":
        return CheckOutcome.fail(
            "INSUFFICIENT_HISTORY",
            ["DAILY_BELOW_60_BASELINE"],
            reason="daily_history absent and engine fail-closed",
        )
    return CheckOutcome.fail(
        "INSUFFICIENT_HISTORY",
        ["DAILY_BELOW_60_BASELINE"],
        reason="daily_history absent without INSUFFICIENT_HISTORY error",
    )


def _vc_profile_valid_3(ctx, packet, fixture) -> CheckOutcome:
    """VC-PROFILE-VALID-3: 17 blocks all present or marked optional-skipped
    (FORMULA_NOT_APPLICABLE rationale). The verifier counts blocks present
    OR optional-skipped; missing == count < 17 without skip marker.

    PROFILE-only: silent on non-PROFILE packets (ACTIVE has no profile
    blocks by design). Accepts BOTH the list-of-blocks shape (each block a
    dict carrying id / value / present) and the production dict shape
    (block_id -> payload), as well as the optional-skipped marker keys
    ``_skipped:<bid>`` the output_assembler emits for FORMULA_NOT_APPLICABLE
    blocks."""
    if _detect_mode(packet) != "PROFILE":
        return CheckOutcome.pass_clean(non_profile_packet=True)
    raw = packet.get("profile_blocks") or packet.get("blocks")
    present = 0
    skipped_with_marker = 0
    missing_examples: List[str] = []
    if isinstance(raw, dict):
        # Production shape: {block_id: payload, "_skipped:<bid>": {rationale}}.
        seen_block_ids = set()
        for key, value in raw.items():
            if isinstance(key, str) and key.startswith("_skipped:"):
                bid = key.split(":", 1)[1]
                rationale = ""
                if isinstance(value, dict):
                    rationale = str(value.get("rationale") or value.get("skip_reason") or "")
                if "formula_not_applicable" in rationale.lower():
                    skipped_with_marker += 1
                    seen_block_ids.add(bid)
                else:
                    missing_examples.append(bid)
                continue
            # A real block payload (dict or scalar). Non-empty content counts
            # as present; null/empty counts as missing.
            if value is None or value == {} or value == []:
                missing_examples.append(str(key))
            else:
                present += 1
    elif isinstance(raw, list):
        for block in raw:
            if not isinstance(block, dict):
                continue
            block_id = block.get("id") or block.get("block_id") or block.get("name")
            if block.get("optional_skipped") is True or block.get("skipped") is True:
                rationale = (
                    block.get("skip_reason")
                    or block.get("rationale")
                    or block.get("applicability_reason")
                    or ""
                )
                if "formula_not_applicable" in str(rationale).lower() or block.get(
                    "applicability"
                ) in ("CONDITIONAL", "NOT_APPLICABLE"):
                    skipped_with_marker += 1
                else:
                    missing_examples.append(str(block_id))
            elif block.get("value") is not None or block.get("present") is True or block.get(
                "computed"
            ) is True:
                present += 1
            else:
                missing_examples.append(str(block_id))
    covered = present + skipped_with_marker
    if covered < _PROFILE_BLOCK_COUNT:
        return CheckOutcome.fail(
            "BLOCK_MISSING",
            ["BLOCK_ABSENT_WITHOUT_SKIP_MARKER"],
            reason=f"only {covered} of {_PROFILE_BLOCK_COUNT} PROFILE blocks accounted for",
            present=present,
            optional_skipped=skipped_with_marker,
            covered=covered,
            expected=_PROFILE_BLOCK_COUNT,
            missing_examples=missing_examples[:10],
        )
    return CheckOutcome.pass_clean(
        present=present,
        optional_skipped=skipped_with_marker,
        covered=covered,
        expected=_PROFILE_BLOCK_COUNT,
    )


def _vc_schema_drift_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-SCHEMA-DRIFT-1: injected foreign key -> schema rejection. The
    verifier independently detects top-level foreign keys (the contract's
    additionalProperties:false semantics)."""
    mode = _detect_mode(packet)
    if mode == "PROFILE":
        allowed = _PROFILE_ALLOWED_TOP
    else:
        allowed = _ACTIVE_ALLOWED_TOP
    foreign = _foreign_keys(packet, allowed)
    if foreign:
        # Engine should have rejected; if it didn't, schema drift is present
        # AND undetected. The verifier reports the drift regardless.
        rejected = packet.get("error_code") == "SCHEMA_VALIDATION_FAILED"
        return CheckOutcome.fail(
            "SCHEMA_VALIDATION_FAILED",
            ["ADDITIONAL_PROPERTIES_REJECTED"],
            reason="foreign top-level keys present (additionalProperties:false)",
            foreign=foreign,
            engine_rejected=rejected,
        )
    return CheckOutcome.pass_clean(foreign_keys=[])


def _vc_mode_sep_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-MODE-SEP-1: ACTIVE output MUST NOT contain profile_blocks.

    Per the canonical packet contract the shared fields (archetype,
    setup_coverage_status, profile_blocks, setup listings) are always EMITTED
    in both modes but carry null/empty values in the mode that does not own
    them. Contamination is reported only when the PROFILE-only field carries
    NON-EMPTY content (real profile_blocks in ACTIVE)."""
    if _detect_mode(packet) != "ACTIVE":
        return CheckOutcome.pass_clean(non_active_packet=True)
    profile_only = ("profile_blocks", "blocks")
    present = [k for k in profile_only if packet.get(k) not in (None, "", [], {})]
    if present:
        return CheckOutcome.fail(
            "MODE_CONTAMINATION",
            ["PROFILE_BLOCKS_IN_ACTIVE"],
            reason="ACTIVE output contains profile-only keys",
            present=present,
        )
    return CheckOutcome.pass_clean()


def _vc_mode_sep_2(ctx, packet, fixture) -> CheckOutcome:
    """VC-MODE-SEP-2: PROFILE output MUST NOT contain tech_score /
    6_binary_signals.

    Per the canonical packet contract the shared fields (including tech_score)
    are always EMITTED in both modes but carry null/empty values in the mode
    that does not own them. Contamination is reported only when the ACTIVE-only
    field carries NON-EMPTY content (a real tech_score in PROFILE)."""
    if _detect_mode(packet) != "PROFILE":
        return CheckOutcome.pass_clean(non_profile_packet=True)
    forbidden = ("tech_score", "binary_signals_6", "six_binary_signals")
    present = [k for k in forbidden if packet.get(k) not in (None, "", [], {})]
    if present:
        return CheckOutcome.fail(
            "MODE_CONTAMINATION",
            ["TECH_SCORE_IN_PROFILE"],
            reason="PROFILE output contains ACTIVE-only keys",
            present=present,
        )
    return CheckOutcome.pass_clean()


def _vc_mode_sep_3(ctx, packet, fixture) -> CheckOutcome:
    """VC-MODE-SEP-3: schema validation rejects foreign keys
    (additionalProperties:false). Companion to VC-SCHEMA-DRIFT-1 but focused
    on the schema-level enforcement assertion."""
    mode = _detect_mode(packet)
    allowed = _PROFILE_ALLOWED_TOP if mode == "PROFILE" else _ACTIVE_ALLOWED_TOP
    foreign = _foreign_keys(packet, allowed)
    if foreign and packet.get("error_code") != "SCHEMA_VALIDATION_FAILED":
        return CheckOutcome.fail(
            "SCHEMA_VALIDATION_FAILED",
            ["ADDITIONAL_PROPERTIES_ALLOWED"],
            reason="foreign keys present but engine did not reject with SCHEMA_VALIDATION_FAILED",
            foreign=foreign,
        )
    return CheckOutcome.pass_clean(
        foreign_keys=foreign,
        engine_rejected=packet.get("error_code") == "SCHEMA_VALIDATION_FAILED",
    )


def _vc_mode_contam_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-MODE-CONTAM-1: ACTIVE output with profile_blocks -> rejection.
    Negative-fixture companion to VC-MODE-SEP-1. Per the canonical packet
    contract the shared profile_blocks field is always emitted but empty in
    ACTIVE; contamination is reported only when it carries real content."""
    if _detect_mode(packet) != "ACTIVE":
        return CheckOutcome.pass_clean(non_active_packet=True)
    profile_only = ("profile_blocks", "blocks")
    contamination = [k for k in profile_only if packet.get(k) not in (None, "", [], {})]
    if contamination:
        rejected = packet.get("error_code") == "MODE_CONTAMINATION" or packet.get(
            "error_code"
        ) == "SCHEMA_VALIDATION_FAILED"
        return CheckOutcome.fail(
            "MODE_CONTAMINATION",
            ["CROSS_MODE_FIELD_INJECTED"],
            reason="ACTIVE output contaminated with profile-mode fields",
            contamination=contamination,
            engine_rejected=rejected,
        )
    return CheckOutcome.pass_clean()


# ===========================================================================
# Utility
# ===========================================================================


def _is_finite(value: Any) -> bool:
    if value is None:
        return False
    try:
        f = float(value)
    except (TypeError, ValueError):
        return False
    return not (math.isnan(f) or math.isinf(f))


def _provenance_warnings(packet: Dict[str, Any]) -> List[Any]:
    prov = packet.get("provenance")
    if isinstance(prov, dict):
        warnings = prov.get("warnings")
        if isinstance(warnings, list):
            return warnings
    warnings = packet.get("warnings")
    if isinstance(warnings, list):
        return warnings
    return []


_HANDLERS = {
    "VC-EMPTY-SERIES-1": _vc_empty_series_1,
    "VC-INHIST-1": _vc_inhist_1,
    "VC-DUP-TS-1": _vc_dup_ts_1,
    "VC-UNSORTED-1": _vc_unsorted_1,
    "VC-MISS-INT-1": _vc_miss_int_1,
    "VC-ZERO-PX-1": _vc_zero_px_1,
    "VC-ZERO-VOL-1": _vc_zero_vol_1,
    "VC-CORP-ACT-1": _vc_corp_act_1,
    "VC-BENCH-MISALIGN-1": _vc_bench_misalign_1,
    "VC-PARTIAL-WEEK-1": _vc_partial_week_1,
    "VC-PRICE-BASIS-3": _vc_price_basis_3,
    "VC-NAN-PROP-1": _vc_nan_prop_1,
    "VC-ACTIVE-VALID-1": _vc_active_valid_1,
    "VC-ACTIVE-VALID-2": _vc_active_valid_2,
    "VC-ACTIVE-VALID-3": _vc_active_valid_3,
    "VC-PROFILE-VALID-1": _vc_profile_valid_1,
    "VC-PROFILE-VALID-2": _vc_profile_valid_2,
    "VC-PROFILE-VALID-3": _vc_profile_valid_3,
    "VC-SCHEMA-DRIFT-1": _vc_schema_drift_1,
    "VC-MODE-SEP-1": _vc_mode_sep_1,
    "VC-MODE-SEP-2": _vc_mode_sep_2,
    "VC-MODE-SEP-3": _vc_mode_sep_3,
    "VC-MODE-CONTAM-1": _vc_mode_contam_1,
}
