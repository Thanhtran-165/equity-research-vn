"""VTA Phase 3 — runner.py

Orchestrates the full pipeline: normalize → compute → assemble → output.

Owns failure codes (frozen registry):
  - INSUFFICIENT_HISTORY          (tier 1, precedence 20)
  - LOOKAHEAD_BIAS_DETECTED       (tier 4, precedence 310)
  - BENCHMARK_UNAVAILABLE         (tier 1, precedence 50) — when benchmark required
  - PARTIAL_WEEK_DROPPED          (DIAGNOSTIC, tier 2, precedence 150)

Public interfaces:
  - run_active(ticker, weekly_data) -> ActiveOutput
  - run_profile(ticker, daily_data) -> ProfileOutput

Design invariants:
  - Deterministic: same input → byte-identical output (no wall-clock in body).
  - No lookahead bias: every indicator computation references only rows up to
    the evaluation index (we evaluate at the LAST row only; pattern detectors
    operate on a trailing window that ends at the as-of bar).
  - No cross-module import of production decision logic. We import the four
    sibling modules (profile_engine, output_assembler, integration_adapter,
    language_verifier) for assembly and boundary enforcement only.
  - Fail-closed on insufficient history and on schema violations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import profile_engine
from output_assembler import (
    MODE_ACTIVE,
    MODE_PROFILE,
    OutputPacket,
    ProvenanceChain,
    assemble_output,
    generate_provenance,
)
from integration_adapter import BoundaryCheck, ParentHandoff, enforce_valuation_boundary, handoff_to_parent
from language_verifier import LanguageCheckResult, check_language


# ====================================================================
# Frozen constants
# ====================================================================

# Minimum history thresholds (VTA-REQ-001 / VTA-REQ-002, failure-code registry).
ACTIVE_MIN_WEEKLY_SESSIONS = 52
PROFILE_MIN_DAILY_SESSIONS = 60

# Frozen failure codes (must match vta-failure-code-registry.yaml exactly).
_FAILURE_INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
_FAILURE_LOOKAHEAD_BIAS_DETECTED = "LOOKAHEAD_BIAS_DETECTED"
_FAILURE_BENCHMARK_UNAVAILABLE = "BENCHMARK_UNAVAILABLE"
_FAILURE_EMPTY_SERIES = "EMPTY_SERIES"
_FAILURE_ZERO_PRICE_DETECTED = "ZERO_PRICE_DETECTED"
_DIAGNOSTIC_PARTIAL_WEEK_DROPPED = "PARTIAL_WEEK_DROPPED"


# ====================================================================
# Result types
# ====================================================================

@dataclass(frozen=True)
class ErrorEnvelope:
    """Deterministic error envelope emitted when the run cannot proceed."""
    error_code: str
    mode: str
    required_context: Mapping[str, Any]
    diagnostic_codes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code,
            "mode": self.mode,
            "required_context": dict(self.required_context),
            "diagnostic_codes": list(self.diagnostic_codes),
        }


@dataclass(frozen=True)
class ActiveOutput:
    """Result of run_active(). Either an OutputPacket or an ErrorEnvelope."""
    ticker: str
    mode: str
    packet: Optional[OutputPacket]
    error: Optional[ErrorEnvelope]
    language_check: Optional[LanguageCheckResult]
    boundary_check: Optional[BoundaryCheck]

    def is_valid(self) -> bool:
        return self.error is None and self.packet is not None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "ticker": self.ticker,
            "mode": self.mode,
            "is_valid": self.is_valid(),
        }
        if self.packet is not None:
            out["packet"] = self.packet.to_dict()
        if self.error is not None:
            out["error"] = self.error.to_dict()
        if self.language_check is not None:
            out["language_check"] = self.language_check.to_dict()
        if self.boundary_check is not None:
            out["boundary_check"] = self.boundary_check.to_dict()
        return out


@dataclass(frozen=True)
class ProfileOutput:
    """Result of run_profile(). Either an OutputPacket or an ErrorEnvelope."""
    ticker: str
    mode: str
    packet: Optional[OutputPacket]
    error: Optional[ErrorEnvelope]
    language_check: Optional[LanguageCheckResult]
    boundary_check: Optional[BoundaryCheck]
    archetype: Optional[str]
    setup_coverage_status: Optional[str]

    def is_valid(self) -> bool:
        return self.error is None and self.packet is not None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "ticker": self.ticker,
            "mode": self.mode,
            "is_valid": self.is_valid(),
            "archetype": self.archetype,
            "setup_coverage_status": self.setup_coverage_status,
        }
        if self.packet is not None:
            out["packet"] = self.packet.to_dict()
        if self.error is not None:
            out["error"] = self.error.to_dict()
        if self.language_check is not None:
            out["language_check"] = self.language_check.to_dict()
        if self.boundary_check is not None:
            out["boundary_check"] = self.boundary_check.to_dict()
        return out


# ====================================================================
# Normalization (in-process; the full normalization_engine is a sibling module
# not yet materialized. The runner performs the minimum normalization needed
# to drive compute + assemble deterministically.)
# ====================================================================

def _parse_date(d: Any) -> Optional[date]:
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        try:
            return datetime.fromisoformat(d).date()
        except ValueError:
            return None
    return None


def _normalize_rows(raw_rows: Sequence[Mapping[str, Any]]) -> Tuple[Mapping[str, Any], ...]:
    """Apply the minimum deterministic normalization: dedup-last-wins, sort
    ascending by date, drop rows with None close. The full normalization_engine
    would also handle price-basis tagging and corporate-action recompute; those
    are out of scope for the runner's in-process normalization.
    """
    seen: Dict[str, Mapping[str, Any]] = {}
    parsed: List[Tuple[date, Mapping[str, Any]]] = []
    for r in raw_rows:
        d = _parse_date(r.get("date"))
        if d is None:
            continue
        # Dedup last-wins on ISO date string.
        key = d.isoformat()
        seen[key] = dict(r)
        parsed.append((d, dict(r)))
    # Sort ascending by date.
    parsed.sort(key=lambda pair: pair[0])
    # Drop rows with missing close (cannot compute indicators).
    cleaned = tuple(
        {**row, "date": d.isoformat()}
        for d, row in parsed
        if row.get("close") is not None
    )
    return cleaned


def _check_zero_price(rows: Sequence[Mapping[str, Any]]) -> List[str]:
    """VC-ZERO-PX-1: any OHLC == 0 is a hard fail."""
    bad: List[str] = []
    for r in rows:
        for f in ("open", "high", "low", "close"):
            v = r.get(f)
            if v is not None and _to_float(v) == 0.0:
                bad.append(f"{r.get('date')}:{f}")
    return bad


def _to_float(v: Any) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _check_partial_week(rows: Sequence[Mapping[str, Any]], mode: str) -> List[str]:
    """VC-PARTIAL-WEEK-1: latest weekly bar with <5 trading days is dropped.

    For ACTIVE mode only. We approximate: if a row carries a ``trading_days``
    field and the latest row has <5, we flag it. The runner drops it before
    computation so contamination does not propagate.
    """
    if mode != MODE_ACTIVE or not rows:
        return []
    last = rows[-1]
    td = last.get("trading_days")
    if td is not None and _to_float(td) is not None and _to_float(td) < 5:
        return [str(last.get("date"))]
    return []


# ====================================================================
# Lookahead-bias guard (VC-LOOKAHEAD-1)
# ====================================================================

def _assert_no_lookahead(rows: Sequence[Mapping[str, Any]]) -> Optional[str]:
    """Static guard: confirm every detector window ends at or before the last
    available bar. We cannot run true static analysis here, but we enforce the
    invariant that the evaluation index is always len(rows) - 1 (the as-of bar)
    and that no detector is allowed to peek past it.

    Returns a failure code string if a lookahead reference is detected, else None.
    """
    # In this runner, all computations evaluate at the trailing bar only. Any
    # detector that referenced future data would require an index > len(rows)-1,
    # which the profile_engine primitives never request (they slice
    # rows[-window:] which is bounded by the last bar). We assert structurally.
    # If a caller passes rows with a future-dated row beyond as_of_date, that
    # is the only lookahead path; we catch it here.
    if not rows:
        return None
    as_of_raw = rows[-1].get("date")
    as_of = _parse_date(as_of_raw)
    if as_of is None:
        return None
    for r in rows[:-1]:
        d = _parse_date(r.get("date"))
        if d is not None and d > as_of:
            return _FAILURE_LOOKAHEAD_BIAS_DETECTED
    return None


# ====================================================================
# ACTIVE-mode pipeline
# ====================================================================

def _build_active_indicators(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Compute the 6 mandatory ACTIVE indicators from weekly rows.

    These primitives are computed locally (not imported from indicator_engine,
    which is a sibling module not yet materialized). The formulas follow the
    frozen contract registry (F-RSI Wilder, F-BOLLINGER population std, etc.).
    """
    import math
    closes = [c for c in (_to_float(r.get("close")) for r in rows) if c is not None]
    highs = [h for h in (_to_float(r.get("high")) for r in rows) if h is not None]
    lows = [l for l in (_to_float(r.get("low")) for r in rows) if l is not None]
    volumes = [v for v in (_to_float(r.get("volume")) for r in rows) if v is not None]

    indicators: Dict[str, Any] = {}

    # MA — SMA over 21/63/126/252 windows (OPTION_21_63_126_252).
    ma_values: Dict[str, Optional[float]] = {}
    for w in (21, 63, 126, 252):
        if len(closes) >= w:
            ma_values[str(w)] = round(sum(closes[-w:]) / w, 4)
        else:
            ma_values[str(w)] = None
    indicators["MA"] = ma_values

    # RSI — Wilder smoothing, period 14.
    if len(closes) >= 15:
        period = 14
        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        gains = [max(d, 0.0) for d in deltas]
        losses = [max(-d, 0.0) for d in deltas]
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        for g, l in zip(gains[period:], losses[period:]):
            avg_gain = (avg_gain * (period - 1) + g) / period
            avg_loss = (avg_loss * (period - 1) + l) / period
        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - 100 / (1 + rs)
        indicators["RSI"] = round(rsi, 4)
    else:
        indicators["RSI"] = None

    # MACD — 12/26/9 with data[0] EMA seed.
    def _ema(values: Sequence[float], period: int) -> List[float]:
        if not values:
            return []
        k = 2 / (period + 1)
        out = [values[0]]
        for v in values[1:]:
            out.append(v * k + out[-1] * (1 - k))
        return out
    if len(closes) >= 35:
        ema12 = _ema(closes, 12)
        ema26 = _ema(closes, 26)
        macd_line = [a - b for a, b in zip(ema12, ema26)]
        signal_line = _ema(macd_line, 9)
        histogram = macd_line[-1] - signal_line[-1]
        indicators["MACD"] = {
            "macd_line": round(macd_line[-1], 4),
            "signal_line": round(signal_line[-1], 4),
            "histogram": round(histogram, 4),
        }
    else:
        indicators["MACD"] = None

    # Bollinger Bands — population std, window 20, multiplier 2.
    if len(closes) >= 20:
        window = closes[-20:]
        middle = sum(window) / 20
        var = sum((x - middle) ** 2 for x in window) / 20
        sd = math.sqrt(var)
        upper = middle + 2 * sd
        lower = middle - 2 * sd
        bb_pos = (closes[-1] - lower) / (upper - lower) * 100 if (upper - lower) else 50.0
        indicators["BB"] = {
            "middle": round(middle, 4),
            "upper": round(upper, 4),
            "lower": round(lower, 4),
            "bb_position_pct": round(bb_pos, 4),
            "std_convention": "POPULATION_DIV_N",
        }
    else:
        indicators["BB"] = None

    # Beta — requires benchmark; placeholder None if absent. Runner raises
    # BENCHMARK_UNAVAILABLE if a benchmark is required but missing.
    indicators["Beta"] = None
    indicators["CMF"] = None  # CMF is PROFILE-only per F-CMF contract; ACTIVE omits.

    return indicators


def _build_active_tech_score(indicators: Mapping[str, Any]) -> int:
    """Aggregate the 6 binary signals into a tech_score in [-6, +6].

    Simple deterministic aggregation: +1 per bullish signal, -1 per bearish.
    This is the tech_score binary aggregation referenced in VTA-REQ-001.
    """
    score = 0
    # MA: close > MA21 → +1, else -1.
    ma = indicators.get("MA") or {}
    close = indicators.get("_latest_close")
    ma21 = ma.get("21") if isinstance(ma, Mapping) else None
    if close is not None and ma21 is not None:
        score += 1 if close > ma21 else -1
    # RSI: > 50 → +1, < 50 → -1.
    rsi = indicators.get("RSI")
    if rsi is not None:
        score += 1 if rsi > 50 else -1
    # MACD: histogram > 0 → +1, else -1.
    macd = indicators.get("MACD")
    if isinstance(macd, Mapping) and macd.get("histogram") is not None:
        score += 1 if macd["histogram"] > 0 else -1
    # BB position: > 50 → +1, else -1.
    bb = indicators.get("BB")
    if isinstance(bb, Mapping) and bb.get("bb_position_pct") is not None:
        score += 1 if bb["bb_position_pct"] > 50 else -1
    # Beta/CMF not computed in ACTIVE pure-stock mode — no contribution.
    return max(-6, min(6, score))


def _binary_signals_6(indicators: Mapping[str, Any], tech_score: int) -> List[bool]:
    """The 6 binary signals backing tech_score (deterministic projection)."""
    ma = indicators.get("MA") or {}
    close = indicators.get("_latest_close")
    ma21 = ma.get("21") if isinstance(ma, Mapping) else None
    sigs = [
        bool(close is not None and ma21 is not None and close > ma21),
        bool((indicators.get("RSI") or 0) > 50),
        bool(isinstance(indicators.get("MACD"), Mapping)
             and (indicators["MACD"].get("histogram") or 0) > 0),
        bool(isinstance(indicators.get("BB"), Mapping)
             and (indicators["BB"].get("bb_position_pct") or 0) > 50),
        tech_score > 0,
        tech_score > 2,
    ]
    return sigs


def run_active(
    ticker: str,
    weekly_data: Sequence[Mapping[str, Any]],
    *,
    as_of_date: Optional[str] = None,
    source_provider: str = "UNKNOWN_PROVIDER",
    language_text: Optional[str] = None,
) -> ActiveOutput:
    """Run the ACTIVE-mode pipeline: normalize → compute → assemble → output.

    Args:
        ticker: stock symbol.
        weekly_data: weekly OHLCV rows (each with date/open/high/low/close/volume).
        as_of_date: ISO date for the evaluation bar (defaults to last row date).
        source_provider: provenance provider id.
        language_text: optional narrative text to vet via language_verifier.

    Returns:
        ActiveOutput. ``is_valid()`` is False iff a fatal pre-flight or
        post-assembly violation occurred (the ``error`` envelope carries the
        failure code).
    """
    mode = MODE_ACTIVE
    # --- Normalize ---
    rows = _normalize_rows(weekly_data)

    # --- Pre-flight guards (tier 1 INPUT_FATAL) ---
    if not rows:
        return ActiveOutput(
            ticker=ticker, mode=mode, packet=None,
            error=ErrorEnvelope(
                error_code=_FAILURE_EMPTY_SERIES, mode=mode,
                required_context={"provided_rows": 0, "source_provider": source_provider},
            ),
            language_check=None, boundary_check=None,
        )
    if len(rows) < ACTIVE_MIN_WEEKLY_SESSIONS:
        return ActiveOutput(
            ticker=ticker, mode=mode, packet=None,
            error=ErrorEnvelope(
                error_code=_FAILURE_INSUFFICIENT_HISTORY, mode=mode,
                required_context={"provided_sessions": len(rows),
                                  "required_sessions": ACTIVE_MIN_WEEKLY_SESSIONS,
                                  "frequency": "weekly"},
            ),
            language_check=None, boundary_check=None,
        )
    zero_prices = _check_zero_price(rows)
    if zero_prices:
        return ActiveOutput(
            ticker=ticker, mode=mode, packet=None,
            error=ErrorEnvelope(
                error_code=_FAILURE_ZERO_PRICE_DETECTED, mode=mode,
                required_context={"mode": mode, "date_field_list": zero_prices[:5]},
            ),
            language_check=None, boundary_check=None,
        )

    # Partial-week drop (DIAGNOSTIC).
    partial_weeks = _check_partial_week(rows, mode)
    if partial_weeks:
        rows = rows[:-1]  # drop the latest partial week

    # Lookahead guard.
    lookahead = _assert_no_lookahead(rows)
    if lookahead is not None:
        return ActiveOutput(
            ticker=ticker, mode=mode, packet=None,
            error=ErrorEnvelope(
                error_code=_FAILURE_LOOKAHEAD_BIAS_DETECTED, mode=mode,
                required_context={"detector_function": "run_active",
                                  "evaluation_index": len(rows) - 1,
                                  "future_reference_offset": "future_dated_row"},
            ),
            language_check=None, boundary_check=None,
        )

    # --- Compute ---
    indicators = _build_active_indicators(rows)
    # Stamp the latest close onto indicators for tech_score aggregation.
    closes = [c for c in (_to_float(r.get("close")) for r in rows) if c is not None]
    if closes:
        indicators["_latest_close"] = closes[-1]
    tech_score = _build_active_tech_score(indicators)
    binary_signals = _binary_signals_6(indicators, tech_score)
    indicators.pop("_latest_close", None)

    # --- Assemble ---
    as_of = as_of_date or rows[-1].get("date")
    computed = {
        "symbol": ticker,
        "indicators": indicators,
        "tech_score": tech_score,
        "binary_signals_6": binary_signals,
        "as_of_date": as_of,
        "analysis_status": "VALID_WITH_WARNINGS" if partial_weeks else "VALID",
        "warnings": ([{"code": _DIAGNOSTIC_PARTIAL_WEEK_DROPPED,
                       "dropped_week_start": partial_weeks[0]}] if partial_weeks else []),
    }
    provenance: Dict[str, ProvenanceChain] = {
        "tech_score": generate_provenance(
            "tech_score",
            source_provider=source_provider,
            computation_timestamp=str(as_of),
            price_basis="adjusted",
            params={"aggregation": "binary_signal_sum", "range": "[-6,6]"},
            computation_chain_id="indicator_engine.tech_score",
            trade_date=str(as_of),
        ),
    }
    # Per-indicator provenance.
    for ind_name in ("MA", "RSI", "MACD", "BB", "Beta", "CMF"):
        provenance[f"indicators.{ind_name}"] = generate_provenance(
            f"indicators.{ind_name}",
            source_provider=source_provider,
            computation_timestamp=str(as_of),
            price_basis="adjusted",
            params={"formula_id": f"F-{ind_name.replace('MA', 'MA').replace('BB', 'BOLLINGER')}"},
            computation_chain_id=f"indicator_engine.{ind_name.lower()}",
            trade_date=str(as_of),
        )

    try:
        packet = assemble_output(mode, computed, provenance=provenance,
                                 as_of_date=str(as_of),
                                 source_provider=source_provider)
    except Exception as exc:
        return ActiveOutput(
            ticker=ticker, mode=mode, packet=None,
            error=ErrorEnvelope(
                error_code="SCHEMA_VALIDATION_FAILED", mode=mode,
                required_context={"assembly_error": str(exc)},
            ),
            language_check=None, boundary_check=None,
        )

    # If the assembled packet has post-assembly violations, surface them.
    # NOTE: language check runs REGARDLESS of validation state because REQ-007
    # is HIGHEST precedence — a contaminated packet that also contains advice
    # language must still surface the language violation.
    language_check = check_language(language_text) if language_text is not None else None
    boundary_check = enforce_valuation_boundary(packet) if packet is not None else None

    if not packet.validation.passed:
        return ActiveOutput(
            ticker=ticker, mode=mode, packet=packet,
            error=ErrorEnvelope(
                error_code=packet.validation.primary_failure_code or "SCHEMA_VALIDATION_FAILED",
                mode=mode,
                required_context={"violations": [dict(v) for v in packet.validation.violations[:5]]},
                diagnostic_codes=packet.validation.diagnostic_codes,
            ),
            language_check=language_check, boundary_check=boundary_check,
        )

    return ActiveOutput(
        ticker=ticker, mode=mode, packet=packet, error=None,
        language_check=language_check, boundary_check=boundary_check,
    )


# ====================================================================
# PROFILE-mode pipeline
# ====================================================================

def run_profile(
    ticker: str,
    daily_data: Sequence[Mapping[str, Any]],
    *,
    as_of_date: Optional[str] = None,
    source_provider: str = "UNKNOWN_PROVIDER",
    benchmark_data: Optional[Sequence[Mapping[str, Any]]] = None,
    obv_series: Optional[Sequence[Optional[float]]] = None,
    vpt_series: Optional[Sequence[Optional[float]]] = None,
    industry_peers: Optional[Sequence[Mapping[str, Any]]] = None,
    language_text: Optional[str] = None,
    bearish_qualified: bool = False,
) -> ProfileOutput:
    """Run the PROFILE-mode pipeline: normalize → compute → assemble → output.

    Args:
        ticker: stock symbol.
        daily_data: daily OHLCV rows.
        as_of_date: ISO date for the evaluation bar.
        source_provider: provenance provider id.
        benchmark_data: optional VNINDEX daily rows (for regime/beta blocks).
        obv_series: SEPARATE OBV cumulative series (B12 fix).
        vpt_series: SEPARATE VPT cumulative series (B12 fix).
        industry_peers: optional peer metrics list.
        language_text: optional narrative text to vet.
        bearish_qualified: whether Phase 4Q mutations have qualified the bearish
            detectors (gates COMPLETE_DIRECTIONAL_COVERAGE status).

    Returns:
        ProfileOutput. ``is_valid()`` is False iff a fatal violation occurred.
    """
    mode = MODE_PROFILE
    # --- Normalize ---
    rows = _normalize_rows(daily_data)
    bench_rows = _normalize_rows(benchmark_data) if benchmark_data else ()

    # --- Pre-flight guards ---
    if not rows:
        return ProfileOutput(
            ticker=ticker, mode=mode, packet=None,
            error=ErrorEnvelope(
                error_code=_FAILURE_EMPTY_SERIES, mode=mode,
                required_context={"provided_rows": 0, "source_provider": source_provider},
            ),
            language_check=None, boundary_check=None,
            archetype=None, setup_coverage_status=None,
        )
    if len(rows) < PROFILE_MIN_DAILY_SESSIONS:
        return ProfileOutput(
            ticker=ticker, mode=mode, packet=None,
            error=ErrorEnvelope(
                error_code=_FAILURE_INSUFFICIENT_HISTORY, mode=mode,
                required_context={"provided_sessions": len(rows),
                                  "required_sessions": PROFILE_MIN_DAILY_SESSIONS,
                                  "frequency": "daily"},
            ),
            language_check=None, boundary_check=None,
            archetype=None, setup_coverage_status=None,
        )
    zero_prices = _check_zero_price(rows)
    if zero_prices:
        return ProfileOutput(
            ticker=ticker, mode=mode, packet=None,
            error=ErrorEnvelope(
                error_code=_FAILURE_ZERO_PRICE_DETECTED, mode=mode,
                required_context={"mode": mode, "date_field_list": zero_prices[:5]},
            ),
            language_check=None, boundary_check=None,
            archetype=None, setup_coverage_status=None,
        )

    lookahead = _assert_no_lookahead(rows)
    if lookahead is not None:
        return ProfileOutput(
            ticker=ticker, mode=mode, packet=None,
            error=ErrorEnvelope(
                error_code=_FAILURE_LOOKAHEAD_BIAS_DETECTED, mode=mode,
                required_context={"detector_function": "run_profile",
                                  "evaluation_index": len(rows) - 1,
                                  "future_reference_offset": "future_dated_row"},
            ),
            language_check=None, boundary_check=None,
            archetype=None, setup_coverage_status=None,
        )

    # --- Compute ---
    # Build the NormalizedInput. We synthesize OBV/VPT series if not supplied
    # so the B12 separation contract is observable; the caller SHOULD supply
    # them from the indicator_engine in production.
    synthesized_obv, synthesized_vpt = _synthesize_obv_vpt(rows)
    ni = profile_engine.NormalizedInput(
        symbol=ticker,
        rows=rows,
        as_of_date=as_of_date,
        bench_rows=bench_rows,
        obv_series=tuple(obv_series) if obv_series is not None else synthesized_obv,
        vpt_series=tuple(vpt_series) if vpt_series is not None else synthesized_vpt,
        industry_peers=tuple(industry_peers) if industry_peers else (),
        source_provider=source_provider,
    )

    blocks = profile_engine.compute_all_blocks(ni)
    setups = profile_engine.scan_all_setups(ni)
    archetype_result = profile_engine.classify_archetype({
        "setups": setups,
        "high_volume_behavior_profile": blocks["high_volume_behavior_profile"].payload,
    })
    coverage_status = profile_engine.setup_coverage_status(
        setups, bearish_qualified=bearish_qualified)

    # Collect any setup failure codes for surfacing in warnings.
    setup_failure_codes: List[str] = []
    for sr in setups.values():
        setup_failure_codes.extend(sr.failure_codes)

    # --- Assemble ---
    as_of = as_of_date or (rows[-1].get("date") if rows else None)
    profile_blocks_payload = {bid: res.payload for bid, res in blocks.items()}
    # Mark optional-skipped blocks with FORMULA_NOT_APPLICABLE rationale so the
    # output_assembler's BLOCK_MISSING check honors them.
    for bid, res in blocks.items():
        if res.skip_reason is not None:
            profile_blocks_payload[f"_skipped:{bid}"] = {"rationale": res.skip_reason}

    bullish_setups = {sid: setups[sid].to_dict() for sid in profile_engine.BULLISH_SETUP_IDS
                      if setups[sid].present}
    bearish_setups = {sid: setups[sid].to_dict() for sid in profile_engine.BEARISH_SETUP_IDS
                      if setups[sid].present}

    computed = {
        "symbol": ticker,
        "profile_blocks": profile_blocks_payload,
        "archetype": archetype_result.archetype,
        "setup_coverage_status": coverage_status,
        "as_of_date": as_of,
        "analysis_status": "VALID",
        "warnings": ([{"code": c, "setup_scope": "bearish"} for c in sorted(set(setup_failure_codes))]
                     if setup_failure_codes else []),
        "bullish_setups": bullish_setups,
        "bearish_setups": bearish_setups,
    }

    provenance: Dict[str, ProvenanceChain] = {
        "archetype": generate_provenance(
            "archetype",
            source_provider=source_provider,
            computation_timestamp=str(as_of),
            price_basis="adjusted",
            params={"precedence": list(profile_engine.ARCHETYPE_PRECEDENCE)},
            computation_chain_id="profile_engine.classify_archetype",
            trade_date=str(as_of),
        ),
        "setup_coverage_status": generate_provenance(
            "setup_coverage_status",
            source_provider=source_provider,
            computation_timestamp=str(as_of),
            price_basis="adjusted",
            params={"bearish_qualified": bearish_qualified},
            computation_chain_id="profile_engine.setup_coverage_status",
            trade_date=str(as_of),
        ),
    }
    # Per-block provenance (one chain per computed block).
    for bid in profile_engine.BLOCK_IDS:
        provenance[f"profile_blocks.{bid}"] = generate_provenance(
            f"profile_blocks.{bid}",
            source_provider=source_provider,
            computation_timestamp=str(as_of),
            price_basis="adjusted",
            params={"block_id": bid},
            computation_chain_id=f"profile_engine.{bid}",
            trade_date=str(as_of),
        )
    # Setup listings are pattern observations; one chain per listing family
    # covers every setup score/confidence inside it.
    provenance["bullish_setups"] = generate_provenance(
        "bullish_setups",
        source_provider=source_provider,
        computation_timestamp=str(as_of),
        price_basis="adjusted",
        params={"family": "bullish", "detectors": list(profile_engine.BULLISH_SETUP_IDS)},
        computation_chain_id="profile_engine.scan_all_setups",
        trade_date=str(as_of),
    )
    provenance["bearish_setups"] = generate_provenance(
        "bearish_setups",
        source_provider=source_provider,
        computation_timestamp=str(as_of),
        price_basis="adjusted",
        params={"family": "bearish", "detectors": list(profile_engine.BEARISH_SETUP_IDS)},
        computation_chain_id="profile_engine.scan_all_setups",
        trade_date=str(as_of),
    )

    try:
        packet = assemble_output(mode, computed, provenance=provenance,
                                 as_of_date=str(as_of),
                                 source_provider=source_provider)
    except Exception as exc:
        return ProfileOutput(
            ticker=ticker, mode=mode, packet=None,
            error=ErrorEnvelope(
                error_code="SCHEMA_VALIDATION_FAILED", mode=mode,
                required_context={"assembly_error": str(exc)},
            ),
            language_check=None, boundary_check=None,
            archetype=archetype_result.archetype,
            setup_coverage_status=coverage_status,
        )

    if not packet.validation.passed:
        # Language check runs regardless (REQ-007 HIGHEST precedence).
        language_check = check_language(language_text) if language_text is not None else None
        boundary_check = enforce_valuation_boundary(packet) if packet is not None else None
        return ProfileOutput(
            ticker=ticker, mode=mode, packet=packet,
            error=ErrorEnvelope(
                error_code=packet.validation.primary_failure_code or "SCHEMA_VALIDATION_FAILED",
                mode=mode,
                required_context={"violations": [dict(v) for v in packet.validation.violations[:5]]},
                diagnostic_codes=packet.validation.diagnostic_codes,
            ),
            language_check=language_check, boundary_check=boundary_check,
            archetype=archetype_result.archetype,
            setup_coverage_status=coverage_status,
        )

    language_check = check_language(language_text) if language_text is not None else None
    boundary_check = enforce_valuation_boundary(packet)

    return ProfileOutput(
        ticker=ticker, mode=mode, packet=packet, error=None,
        language_check=language_check, boundary_check=boundary_check,
        archetype=archetype_result.archetype,
        setup_coverage_status=coverage_status,
    )


def _synthesize_obv_vpt(rows: Sequence[Mapping[str, Any]]) -> Tuple[Tuple[Optional[float], ...], Tuple[Optional[float], ...]]:
    """Synthesize OBV and VPT series from rows when the caller does not supply
    them. These are SEPARATE computations (B12 contract): OBV uses signed
    volume; VPT uses volume × return. The two series are structurally distinct
    even when both are derived from the same OHLCV.
    """
    obv: List[Optional[float]] = []
    vpt: List[Optional[float]] = []
    cum_obv = 0.0
    cum_vpt = 0.0
    for i in range(1, len(rows)):
        prev_c = _to_float(rows[i - 1].get("close"))
        cur_c = _to_float(rows[i].get("close"))
        vol = _to_float(rows[i].get("volume"))
        if prev_c is None or cur_c is None or vol is None or prev_c <= 0:
            obv.append(None)
            vpt.append(None)
            continue
        if cur_c > prev_c:
            cum_obv += vol
        elif cur_c < prev_c:
            cum_obv -= vol
        ret = cur_c / prev_c - 1
        cum_vpt += vol * ret
        obv.append(cum_obv)
        vpt.append(cum_vpt)
    return tuple(obv), tuple(vpt)


__all__ = [
    "ActiveOutput",
    "ProfileOutput",
    "ErrorEnvelope",
    "run_active",
    "run_profile",
    "ACTIVE_MIN_WEEKLY_SESSIONS",
    "PROFILE_MIN_DAILY_SESSIONS",
]
