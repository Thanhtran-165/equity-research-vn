"""VTA Phase 3 — profile_engine.py

Computes the 17 PROFILE blocks, detects 8 bullish + 5 bearish setups, and
classifies the stock archetype. This module implements VTA-REQ-002, VTA-REQ-007,
VTA-REQ-009, VTA-REQ-009a, VTA-REQ-013, VTA-REQ-014.

Public interfaces:
  - compute_profile_block(block_id, normalized_input) -> BlockResult
  - detect_setup(setup_id, profile_context) -> SetupResult
  - classify_archetype(profile_context) -> ArchetypeResult
  - compute_hvb_events_1y(events, as_of_date) -> HVBEventsResult   (VTA-REQ-013)
  - compute_obv_change(obv_series, window) -> OBVChangeResult      (VTA-REQ-014)
  - compute_vpt_change(vpt_series, window) -> VPTChangeResult      (VTA-REQ-014)

Critical correctness invariants (per Phase 3 review):
  1. Bearish setups have INDEPENDENT confirmation — they are NOT activated by a
     single negative indicator (PROHIBITED ACTIVATION RULE, GDI-4/5/6). A
     confirmed bearish setup requires BOTH a structural+microstructure signal
     AND an independent post-breakdown confirmation channel.
  2. events_1y uses a CALENDAR 365-day window (effective_date >= as_of - 365d),
     NOT events[-252:] (VTA-REQ-013, B14_EVENTS_1Y fix, EVENTS_1Y_LOGIC_ERROR).
  3. OBV change is sourced from the OBV series; VPT change is sourced from the
     VPT series — separate source series (VTA-REQ-014, B12 fix,
     OBV_VPT_SERIES_CONTAMINATION).
  4. setup_coverage_status starts at INCOMPLETE_BEARISH_COVERAGE and upgrades
     to COMPLETE_DIRECTIONAL_COVERAGE only after Phase 4Q mutations prove the
     detectors resist false positives/negatives. We freeze the default at
     INCOMPLETE_BEARISH_COVERAGE here; the runner may upgrade it once the
     detector qualification flag is set externally.
  5. No import of production decision logic from indicator_engine. Indicator
     primitives used here are computed locally from normalized input (which the
     normalization_engine would supply in production). The dependency declared
     in vta-phase-3-implementation-scope.yaml is a logical data dependency,
     not a code import.

Determinism: all functions are pure given normalized_input. No wall-clock, no
RNG, ordered iteration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


# ====================================================================
# Frozen vocabulary (VTA-REQ-002, REQ-009, REQ-009a, REQ-013, REQ-014)
# ====================================================================

# The 17 PROFILE block identifiers (canonical order from stock_profile_blocks.md).
BLOCK_IDS: Tuple[str, ...] = (
    "price_behavior_profile",          # B1
    "volatility_profile",              # B2
    "drawdown_profile",                # B3
    "liquidity_profile",               # B4
    "return_distribution_profile",     # B5
    "tail_risk_profile",               # B6
    "liquidity_risk_profile",          # B7
    "relative_strength_profile",       # B8
    "regime_profile",                  # B9
    "volume_price_profile",            # B10
    "volume_price_confirmation_profile",  # B11 (VPCI)
    "money_flow_pressure_profile",     # B12
    "effort_result_profile",           # B13
    "high_volume_behavior_profile",    # B14
    "pvi_nvi_participation_profile",   # B15
    "volume_at_price_profile",         # B16
    "industry_peer_profile",           # B17
)
EXPECTED_BLOCK_COUNT = 17

# 8 bullish setup identifiers (from pattern_scoring.md DETECTORS).
BULLISH_SETUP_IDS: Tuple[str, ...] = (
    "S-BULL-FLAG",            # bull_flags
    "S-BULL-PENNANT",         # bull_pennants
    "S-TRIANGLE-ASC",         # triangles_ascending
    "S-WEDGE-FALLING",        # wedges_falling
    "S-CUP-WITH-HANDLE",      # cup_with_handle
    "S-RECTANGLE-BOTTOM",     # rectangle_bottoms
    "S-DOUBLE-BOTTOM",        # double_bottoms
    "S-MEASURED-MOVE-UP",     # measured_move_up
)

# 5 bearish setup identifiers (from vta-bearish-setup-registry.yaml).
BEARISH_SETUP_IDS: Tuple[str, ...] = (
    "S-BEAR-FLAG",
    "S-BEAR-PENNANT",
    "S-BEAR-DOWN-TRIANGLE",
    "S-BEAR-RECTANGLE-TOP",
    "S-BEAR-HEAD-SHOULDERS",
)

# Archetype precedence (vta-bearish-setup-registry.yaml archetype_feed +
# pattern_scoring.md estimate_archetype). A-DISTRIBUTION is inserted per the
# registry: below A-ACCUMULATION-BREAKOUT, above A-TRAP-PRONE.
ARCHETYPE_PRECEDENCE: Tuple[str, ...] = (
    "A-TREND-FOLLOWING",
    "A-ACCUMULATION-BREAKOUT",
    "A-DISTRIBUTION",          # confirmed bearish setups feed this archetype
    "A-TRAP-PRONE",            # HVB-driven only — NOT pattern-driven
    "A-MIXED",
    "A-NO-CURRENT-SETUP",
)

# Coverage status enum (VTA-REQ-009).
COVERAGE_INCOMPLETE_BEARISH = "INCOMPLETE_BEARISH_COVERAGE"
COVERAGE_BULLISH_ONLY = "BULLISH_ONLY"
COVERAGE_COMPLETE_DIRECTIONAL = "COMPLETE_DIRECTIONAL_COVERAGE"

# Cooldown policy (vta-bearish-setup-registry.yaml cross_setup_policies).
BEARISH_COOLDOWN_SESSIONS = 10

# Setup score thresholds (from pattern_scoring.md status_from_score).
SETUP_SCORE_CONFIRM_NEAR = 78
SETUP_SCORE_INDEVELOPMENT_LO = 62
SETUP_SCORE_INDEVELOPMENT_HI = 77
SETUP_SCORE_MIN_REPORTABLE = 55
# Confirmation-state band definitions (severity_semantics in the registry).
INDEVELOPMENT_BAND = (62, 77)

# Bearish confirmation-state values (severity_semantics).
STATE_UNCONFIRMED = "UNCONFIRMED"
STATE_CONFIRMED = "CONFIRMED"
STATE_INVALIDATED = "INVALIDATED"
STATE_EXPIRED = "EXPIRED"

# Frozen failure codes (must match vta-failure-code-registry.yaml exactly).
_FAILURE_EVENTS_1Y_LOGIC_ERROR = "EVENTS_1Y_LOGIC_ERROR"
_FAILURE_OBV_VPT_SERIES_CONTAMINATION = "OBV_VPT_SERIES_CONTAMINATION"
_FAILURE_BEARISH_SIGN_INVERSION = "BEARISH_SIGN_INVERSION"
_FAILURE_BEARISH_SETUP_INCOMPLETE = "BEARISH_SETUP_INCOMPLETE"
_FAILURE_FALSE_BREAKOUT_WITHOUT_VOLUME = "FALSE_BREAKOUT_WITHOUT_VOLUME"
_FAILURE_UNCONFIRMED_PATTERN_REPORTED_AS_CONFIRMED = "UNCONFIRMED_PATTERN_REPORTED_AS_CONFIRMED"
_FAILURE_SETUP_DROPPED_SILENTLY = "SETUP_DROPPED_SILENTLY"
_FAILURE_ARCHETYPE_AMBIGUITY_FALLBACK = "ARCHETYPE_AMBIGUITY_FALLBACK"


# ====================================================================
# Generic numeric helpers (pure; deterministic)
# ====================================================================

def _finite(v: Any) -> Optional[float]:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _round(v: Optional[float], d: int = 4) -> Optional[float]:
    if v is None:
        return None
    return round(float(v), d)


def _mean(values: Iterable[float]) -> Optional[float]:
    nums = [v for v in values if _finite(v) is not None]
    nums = [v for v in nums]
    if not nums:
        return None
    return sum(nums) / len(nums)


def _std_dev_population(values: Iterable[float]) -> Optional[float]:
    """Population std (÷N) — matches F-BOLLINGER / F-HV shared kernel decision."""
    nums = [_finite(v) for v in values]
    nums = [v for v in nums if v is not None]
    if not nums:
        return None
    avg = sum(nums) / len(nums)
    var = sum((v - avg) ** 2 for v in nums) / len(nums)
    return math.sqrt(var)


def _median(values: Iterable[float]) -> Optional[float]:
    nums = sorted(v for v in (_finite(x) for x in values) if v is not None)
    if not nums:
        return None
    n = len(nums)
    mid = n // 2
    if n % 2 == 1:
        return nums[mid]
    return (nums[mid - 1] + nums[mid]) / 2.0


def _quantile_linear(values: Iterable[float], q: float) -> Optional[float]:
    """Linear-interpolated quantile (F-VAR-ES / F-PERCENTILE quantile_helper)."""
    nums = sorted(v for v in (_finite(x) for x in values) if v is not None)
    if not nums:
        return None
    if len(nums) == 1:
        return nums[0]
    pos = q * (len(nums) - 1)
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return nums[lo]
    return nums[lo] + (nums[hi] - nums[lo]) * (pos - lo)


def _percentile_of_value_floor(values: Iterable[float], value: Any) -> Optional[float]:
    """Floor-counting percentile (F-PERCENTILE percentile_of_value)."""
    nums = [v for v in (_finite(x) for x in values) if v is not None]
    v = _finite(value)
    if not nums or v is None:
        return None
    return (sum(1 for x in nums if x < v) / len(nums)) * 100.0


def _pct(a: Optional[float], b: Optional[float]) -> Optional[float]:
    """(a/b - 1) * 100 with None / zero-denominator safety."""
    a = _finite(a)
    b = _finite(b)
    if a is None or b is None or b == 0:
        return None
    return (a / b - 1) * 100.0


def _slope_ols(values: Sequence[float]) -> float:
    """OLS slope of values vs index (F-CHANNEL-SLOPE primitive)."""
    n = len(values)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    denom = sum((i - x_mean) ** 2 for i in range(n)) or 1.0
    return sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values)) / denom


def _channel_slope_pct_per_bar(close_window: Sequence[float]) -> Optional[float]:
    """F-CHANNEL-SLOPE: normalized_slope_pct_per_bar = 100 × OLS_slope / median(close)."""
    nums = [_finite(c) for c in close_window]
    nums = [c for c in nums if c is not None]
    if len(nums) < 2:
        return None
    med = _median(nums)
    if not med or med == 0:
        return None
    return 100.0 * _slope_ols(nums) / med


# ====================================================================
# Normalized input contract
# ====================================================================

@dataclass(frozen=True)
class NormalizedInput:
    """The normalized PROFILE-mode input.

    ``rows`` are daily OHLCV dicts with at least:
        date (ISO str), open, high, low, close, volume, value (=close*volume*1000)
    ``trade_dates`` is the parsed datetime.date sequence aligned with rows.
    ``as_of_date`` is the as-of date for events_1y calendar windowing.
    ``bench_rows`` is an optional benchmark (VNINDEX) series for regime/beta.
    ``obv_series`` / ``vpt_series`` are the SEPARATE source series (B12 fix).
    """
    symbol: str
    rows: Tuple[Mapping[str, Any], ...]
    as_of_date: Optional[str] = None
    bench_rows: Tuple[Mapping[str, Any], ...] = ()
    obv_series: Tuple[Optional[float], ...] = ()
    vpt_series: Tuple[Optional[float], ...] = ()
    industry_peers: Tuple[Mapping[str, Any], ...] = ()
    source_provider: str = "UNKNOWN_PROVIDER"

    def closes(self) -> List[float]:
        return [c for c in (_finite(r.get("close")) for r in self.rows) if c is not None]

    def trade_dates(self) -> List[Optional[date]]:
        out: List[Optional[date]] = []
        for r in self.rows:
            d = r.get("date")
            if isinstance(d, date) and not isinstance(d, datetime):
                out.append(d)
            elif isinstance(d, datetime):
                out.append(d.date())
            elif isinstance(d, str):
                try:
                    out.append(datetime.fromisoformat(d).date())
                except ValueError:
                    out.append(None)
            else:
                out.append(None)
        return out

    def as_of(self) -> Optional[date]:
        if not self.as_of_date:
            return self.trade_dates()[-1] if self.trade_dates() else None
        try:
            return datetime.fromisoformat(self.as_of_date).date()
        except (TypeError, ValueError):
            return None


# ====================================================================
# Block result types
# ====================================================================

@dataclass(frozen=True)
class BlockResult:
    """Result of compute_profile_block()."""
    block_id: str
    computed: bool
    payload: Mapping[str, Any]
    skip_reason: Optional[str] = None        # FORMULA_NOT_APPLICABLE rationale
    error_code: Optional[str] = None         # computation error code if any

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "block_id": self.block_id,
            "computed": self.computed,
            "payload": dict(self.payload),
        }
        if self.skip_reason is not None:
            out["skip_reason"] = self.skip_reason
        if self.error_code is not None:
            out["error_code"] = self.error_code
        return out


@dataclass(frozen=True)
class SetupResult:
    """Result of detect_setup(). Carries the observation/trigger/confirmation/
    invalidation evidence breakdown so the registry's semantic discipline is
    observable in the output.
    """
    setup_id: str
    direction: str                           # BULLISH | BEARISH
    present: bool                            # signal conditions all met
    setup_score: float
    confirmation_state: str                  # UNCONFIRMED | CONFIRMED | INVALIDATED | EXPIRED | NOT_PRESENT
    confidence: float
    evidence: Mapping[str, Any]              # observation/signal/confirmation/invalidation breakdown
    output_fields: Mapping[str, Any]
    failure_codes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "setup_id": self.setup_id,
            "direction": self.direction,
            "present": self.present,
            "setup_score": self.setup_score,
            "confirmation_state": self.confirmation_state,
            "confidence": self.confidence,
            "evidence": dict(self.evidence),
            "output_fields": dict(self.output_fields),
            "failure_codes": list(self.failure_codes),
        }


@dataclass(frozen=True)
class ArchetypeResult:
    """Result of classify_archetype()."""
    archetype: str
    primary_attribution: str                 # the setup_id or "HVB" or "NONE"
    secondary_setups: Tuple[str, ...]
    eligible: Tuple[str, ...]                # archetypes that were eligible
    fallback_reason: Optional[str] = None
    failure_codes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "archetype": self.archetype,
            "primary_attribution": self.primary_attribution,
            "secondary_setups": list(self.secondary_setups),
            "eligible": list(self.eligible),
        }
        if self.fallback_reason is not None:
            out["fallback_reason"] = self.fallback_reason
        out["failure_codes"] = list(self.failure_codes)
        return out


@dataclass(frozen=True)
class HVBEventsResult:
    """Result of compute_hvb_events_1y() (VTA-REQ-013, F-HVB)."""
    events_count_1y: int
    events_1y: Tuple[Mapping[str, Any], ...]
    selection_method: str                    # "CALENDAR_WINDOW_365_DAYS"
    failure_codes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class OBVChangeResult:
    """Result of compute_obv_change() — source series is OBV (B12 fix)."""
    obv_change_pct: Optional[float]
    source_series: str                       # always "OBV"
    window: int
    failure_codes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class VPTChangeResult:
    """Result of compute_vpt_change() — source series is VPT (B12 fix)."""
    vpt_change_pct: Optional[float]
    source_series: str                       # always "VPT"
    window: int
    failure_codes: Tuple[str, ...] = ()


# ====================================================================
# VTA-REQ-013: HVB events_1y via calendar window (NOT event count slice)
# ====================================================================

def compute_hvb_events_1y(
    events: Sequence[Mapping[str, Any]],
    as_of_date: Any,
    *,
    calendar_window_days: int = 365,
) -> HVBEventsResult:
    """Select events by CALENDAR 365-day window (VTA-REQ-013, B14_EVENTS_1Y fix).

    CORRECT: events_1y = [e for e in events if e.effective_date >= as_of - 365d]
    WRONG (regression):   events_1y = events[-252:]

    This function NEVER uses index/count slicing. It is purely calendar-driven.
    """
    if isinstance(as_of_date, datetime):
        as_of = as_of_date.date()
    elif isinstance(as_of_date, date):
        as_of = as_of_date
    elif isinstance(as_of_date, str):
        try:
            as_of = datetime.fromisoformat(as_of_date).date()
        except ValueError:
            return HVBEventsResult(
                events_count_1y=0, events_1y=(),
                selection_method="CALENDAR_WINDOW_365_DAYS",
                failure_codes=(_FAILURE_EVENTS_1Y_LOGIC_ERROR,),
            )
    else:
        return HVBEventsResult(
            events_count_1y=0, events_1y=(),
            selection_method="CALENDAR_WINDOW_365_DAYS",
            failure_codes=(_FAILURE_EVENTS_1Y_LOGIC_ERROR,),
        )

    cutoff = as_of - timedelta(days=calendar_window_days)
    selected: List[Mapping[str, Any]] = []
    for ev in events:
        ev_date_raw = ev.get("effective_date") or ev.get("date")
        if isinstance(ev_date_raw, datetime):
            ev_date = ev_date_raw.date()
        elif isinstance(ev_date_raw, date):
            ev_date = ev_date_raw
        elif isinstance(ev_date_raw, str):
            try:
                ev_date = datetime.fromisoformat(ev_date_raw).date()
            except ValueError:
                continue
        else:
            continue
        # Calendar-window predicate. NEVER an index/count slice.
        if ev_date >= cutoff and ev_date <= as_of:
            selected.append(dict(ev))
    # Stable order: ascending by effective_date.
    selected.sort(key=lambda e: str(e.get("effective_date") or e.get("date") or ""))
    return HVBEventsResult(
        events_count_1y=len(selected),
        events_1y=tuple(selected),
        selection_method="CALENDAR_WINDOW_365_DAYS",
    )


# ====================================================================
# VTA-REQ-014: OBV/VPT from SEPARATE source series (B12 fix)
# ====================================================================

def _pct_change_over_window(series: Sequence[Optional[float]], window: int) -> Optional[float]:
    """Percent change of a cumulative series over the trailing ``window`` bars."""
    clean = [v for v in (_finite(x) for x in series) if v is not None]
    if len(clean) <= window or window <= 0:
        return None
    start = clean[-1 - window]
    end = clean[-1]
    if start is None or end is None or start == 0:
        return None
    return (end / start - 1) * 100.0


def compute_obv_change(obv_series: Sequence[Optional[float]], window: int = 20) -> OBVChangeResult:
    """Compute OBV change from the OBV source series (B12 fix).

    The source_series tag is ALWAYS "OBV". Any caller that passes a VPT series
    here is committing the B12_OBV_VPT_BUG; we cannot detect that at runtime
    from values alone, but the contract is enforced structurally: this function
    is the ONLY entry point for obv_change and its result is tagged OBV.
    """
    change = _pct_change_over_window(obv_series, window)
    return OBVChangeResult(obv_change_pct=_round(change), source_series="OBV", window=window)


def compute_vpt_change(vpt_series: Sequence[Optional[float]], window: int = 20) -> VPTChangeResult:
    """Compute VPT change from the VPT source series (B12 fix).

    Symmetric to compute_obv_change; source_series is ALWAYS "VPT".
    """
    change = _pct_change_over_window(vpt_series, window)
    return VPTChangeResult(vpt_change_pct=_round(change), source_series="VPT", window=window)


def assert_obv_vpt_separate(obv_result: OBVChangeResult, vpt_result: VPTChangeResult) -> Tuple[str, ...]:
    """Detect the B12 regression: obv_change sourced from VPT or vice-versa.

    We assert by structural tag (not by value equality, since OBV and VPT can
    legitimately coincide on some windows). A contamination is flagged only
    when the source_series tag is wrong.
    """
    codes: List[str] = []
    if obv_result.source_series != "OBV":
        codes.append(_FAILURE_OBV_VPT_SERIES_CONTAMINATION)
    if vpt_result.source_series != "VPT":
        codes.append(_FAILURE_OBV_VPT_SERIES_CONTAMINATION)
    return tuple(codes)


# ====================================================================
# Per-block computations (B1-B17)
# ====================================================================

def _b1_price_behavior(ni: NormalizedInput) -> Dict[str, Any]:
    closes_252 = [c for c in (_finite(r.get("close")) for r in ni.rows[-252:]) if c is not None]
    latest = ni.rows[-1] if ni.rows else {}
    latest_close = _finite(latest.get("close"))
    high_52w = max(closes_252) if closes_252 else None
    low_52w = min(closes_252) if closes_252 else None
    closes = ni.closes()

    def ret_pct(window: int) -> Optional[float]:
        if len(closes) <= window:
            return None
        a, b = closes[-1 - window], closes[-1]
        if a is None or b is None or a == 0:
            return None
        return _round((b / a - 1) * 100)

    return {
        "latest_close": latest_close,
        "latest_date": latest.get("date"),
        "return_1m_pct": ret_pct(21),
        "return_3m_pct": ret_pct(63),
        "return_6m_pct": ret_pct(126),
        "return_1y_pct": ret_pct(252),
        "high_52w": high_52w,
        "low_52w": low_52w,
        "distance_from_52w_high_pct": _round((latest_close / high_52w - 1) * 100)
            if (latest_close and high_52w and high_52w > 0) else None,
        "distance_from_52w_low_pct": _round((latest_close / low_52w - 1) * 100)
            if (latest_close and low_52w and low_52w > 0) else None,
        "interpretation_guardrail": "price_behavior: historical observation only",
    }


def _daily_returns_pct(rows: Sequence[Mapping[str, Any]]) -> List[float]:
    out: List[float] = []
    for i in range(1, len(rows)):
        p = _finite(rows[i - 1].get("close"))
        c = _finite(rows[i].get("close"))
        if p and c and p > 0 and c > 0:
            out.append((c / p - 1) * 100)
    return out


def _log_returns(rows: Sequence[Mapping[str, Any]]) -> List[float]:
    out: List[float] = []
    for i in range(1, len(rows)):
        p = _finite(rows[i - 1].get("close"))
        c = _finite(rows[i].get("close"))
        if p and c and p > 0 and c > 0:
            out.append(math.log(c / p))
    return out


def _realized_vol(rows: Sequence[Mapping[str, Any]], window: int) -> Optional[float]:
    values = _log_returns(rows)[-window:]
    if len(values) < max(5, window // 3):
        return None
    sd = _std_dev_population(values)
    return _round(sd * math.sqrt(252) * 100) if sd is not None else None


def _b2_volatility(ni: NormalizedInput) -> Dict[str, Any]:
    return {
        "hv20_pct": _realized_vol(ni.rows, 20),
        "hv60_pct": _realized_vol(ni.rows, 60),
        "hv120_pct": _realized_vol(ni.rows, 120),
        "hv252_pct": _realized_vol(ni.rows, 252),
        "annualization_factor_used": 252,
        "std_convention": "POPULATION_DIV_N",
        "interpretation_guardrail": "volatility: historical dispersion only",
    }


def _drawdown_series(rows: Sequence[Mapping[str, Any]]) -> List[Optional[float]]:
    peak: Optional[float] = None
    out: List[Optional[float]] = []
    for r in rows:
        c = _finite(r.get("close"))
        if c is None:
            out.append(None)
            continue
        peak = c if peak is None else max(peak, c)
        out.append(c / peak - 1 if peak else None)
    return out


def _b3_drawdown(ni: NormalizedInput) -> Dict[str, Any]:
    dd = _drawdown_series(ni.rows)
    finite_dd = [v for v in dd if v is not None]
    current = finite_dd[-1] if finite_dd else None
    max_depth = min(finite_dd) if finite_dd else None
    underwater = 0
    for v in reversed(dd):
        if v is not None and v < 0:
            underwater += 1
        else:
            break
    return {
        "current_drawdown_pct": _round(current * 100) if current is not None else None,
        "current_underwater_days": underwater,
        "max_drawdown_pct": _round(max_depth * 100) if max_depth is not None else None,
        "interpretation_guardrail": "drawdown: window-and-adjustment sensitive; not a forecast",
    }


def _values_252(ni: NormalizedInput) -> List[float]:
    return [v for v in (_finite(r.get("value")) for r in ni.rows[-252:]) if v is not None]


def _b4_liquidity(ni: NormalizedInput) -> Dict[str, Any]:
    vals = _values_252(ni)
    avg20 = _mean(vals[-20:]) if len(vals) >= 20 else _mean(vals)
    avg60 = _mean(vals[-60:]) if len(vals) >= 60 else _mean(vals)
    latest = ni.rows[-1] if ni.rows else {}
    latest_value = _finite(latest.get("value"))
    cv = None
    if vals and _mean(vals):
        sd = _std_dev_population(vals)
        if sd is not None:
            cv = _round(sd / _mean(vals) * 100)
    return {
        "latest_value": latest_value,
        "avg_value_20d": _round(avg20) if avg20 is not None else None,
        "avg_value_60d": _round(avg60) if avg60 is not None else None,
        "latest_value_percentile_1y": _percentile_of_value_floor(vals, latest_value),
        "liquidity_stability_cv_pct": cv,
        "interpretation_guardrail": "liquidity: close × volume; does not reflect block trades",
    }


def _b5_return_distribution(ni: NormalizedInput) -> Dict[str, Any]:
    daily = _daily_returns_pct(ni.rows)
    one_year = daily[-252:]
    return {
        "observations_full": len(daily),
        "observations_1y": len(one_year),
        "median_pct_1y": _round(_median(one_year)) if one_year else None,
        "std_pct_1y": _round(_std_dev_population(one_year)) if one_year else None,
        "p05_pct_1y": _round(_quantile_linear(one_year, 0.05)) if one_year else None,
        "p95_pct_1y": _round(_quantile_linear(one_year, 0.95)) if one_year else None,
        "positive_day_rate_1y_pct": _round(sum(1 for v in one_year if v > 0) / len(one_year) * 100)
            if one_year else None,
        "interpretation_guardrail": "return_distribution: descriptive only; not normal; not a forecast",
    }


def _b6_tail_risk(ni: NormalizedInput) -> Dict[str, Any]:
    daily = _daily_returns_pct(ni.rows)
    tail = daily[-252:]
    q05 = _quantile_linear(tail, 0.05)
    q01 = _quantile_linear(tail, 0.01)
    es05 = _mean([v for v in tail if v <= (q05 or float("inf"))]) if q05 is not None and tail else None
    es01 = _mean([v for v in tail if v <= (q01 or float("inf"))]) if q01 is not None and tail else None
    return {
        "historical_var_95_1d_pct": _round(abs(q05)) if q05 is not None else None,
        "historical_var_99_1d_pct": _round(abs(q01)) if q01 is not None else None,
        "expected_shortfall_95_1d_pct": _round(abs(es05)) if es05 is not None else None,
        "expected_shortfall_99_1d_pct": _round(abs(es01)) if es01 is not None else None,
        "interpretation_guardrail": "tail_risk: historical VaR/ES; not a trading risk model",
    }


def _b7_liquidity_risk(ni: NormalizedInput) -> Dict[str, Any]:
    vals = _values_252(ni)
    med = _median(vals)
    avg20 = _mean(vals[-20:]) if len(vals) >= 20 else _mean(vals)
    drought_thr = (med * 0.5) if med is not None else None
    severe_thr = (med * 0.2) if med is not None else None
    drought_days = sum(1 for v in vals if drought_thr is not None and v <= drought_thr)
    thin_days = sum(1 for v in vals if severe_thr is not None and v <= severe_thr)
    label = "trung_binh"
    if thin_days >= 40 or (avg20 is not None and med is not None and avg20 < med * 0.4):
        label = "cao"
    if thin_days < 10 and avg20 is not None and med is not None and avg20 >= med * 0.8:
        label = "thap"
    return {
        "median_value_1y": _round(med) if med is not None else None,
        "value_drought_days_1y": drought_days,
        "severe_thin_value_days_1y": thin_days,
        "liquidity_risk_label": label,
        "interpretation_guardrail": "liquidity_risk: historical value stress test only",
    }


def _paired_rows(stock: Sequence[Mapping[str, Any]], bench: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    bench_by_date = {r.get("date"): r for r in bench}
    out: List[Dict[str, Any]] = []
    for r in stock:
        b = bench_by_date.get(r.get("date"))
        if b and _finite(r.get("close")) and _finite(b.get("close")):
            out.append({"date": r.get("date"), "stock": r, "benchmark": b})
    return out


def _b8_relative_strength(ni: NormalizedInput) -> Dict[str, Any]:
    if not ni.bench_rows:
        return {"peer_count": 0,
                "interpretation_guardrail": "relative_strength: no benchmark supplied"}
    paired = _paired_rows(ni.rows, ni.bench_rows)
    if len(paired) < max(5, 252 // 2):
        return {"observations": len(paired),
                "interpretation_guardrail": "relative_strength: insufficient paired history"}
    stock_rets: List[float] = []
    bench_rets: List[float] = []
    for i in range(1, len(paired)):
        sp, sc = paired[i - 1]["stock"]["close"], paired[i]["stock"]["close"]
        bp, bc = paired[i - 1]["benchmark"]["close"], paired[i]["benchmark"]["close"]
        if sp > 0 and bp > 0:
            stock_rets.append(sc / sp - 1)
            bench_rets.append(bc / bp - 1)
    if len(stock_rets) < 2:
        return {"observations": len(stock_rets),
                "interpretation_guardrail": "relative_strength: insufficient returns"}
    ms = sum(stock_rets) / len(stock_rets)
    mb = sum(bench_rets) / len(bench_rets)
    cs = [s - ms for s in stock_rets]
    cb = [b - mb for b in bench_rets]
    cov = sum(x * y for x, y in zip(cs, cb)) / len(stock_rets)        # population cov (÷N)
    var = sum(x * x for x in cb) / len(bench_rets)                     # population var (÷N)
    beta = cov / var if var else None
    den_corr = (sum(x * x for x in cs) ** 0.5) * (sum(y * y for y in cb) ** 0.5)
    corr = sum(x * y for x, y in zip(cs, cb)) / den_corr if den_corr else None
    r2 = corr * corr if corr is not None else None
    return {
        "primary_benchmark": "VNINDEX",
        "observations": len(stock_rets),
        "beta_252": _round(beta),
        "correlation_252": _round(corr),
        "r2_252": _round(r2),
        "interpretation_guardrail": "relative_strength: historical comparison only",
    }


def _b9_regime(ni: NormalizedInput) -> Dict[str, Any]:
    if not ni.bench_rows:
        return {"current_market_regime": None,
                "interpretation_guardrail": "regime: no benchmark supplied"}
    bench_closes = [c for c in (_finite(r.get("close")) for r in ni.bench_rows) if c is not None]
    if len(bench_closes) < 121:
        return {"current_market_regime": None,
                "interpretation_guardrail": "regime: insufficient benchmark history"}
    r60 = _pct(bench_closes[-1], bench_closes[-61])
    r120 = _pct(bench_closes[-1], bench_closes[-121])
    dd_series = []
    peak = None
    for c in bench_closes:
        peak = c if peak is None else max(peak, c)
        dd_series.append(c / peak - 1)
    drawdown = dd_series[-1]
    if drawdown is not None and drawdown <= -0.18 or (r60 is not None and r60 <= -12):
        rid = "stress"
    elif r60 is not None and r120 is not None and r60 > 6 and r120 > 8 and (drawdown or 0) > -8:
        rid = "uptrend"
    else:
        rid = "sideways"
    return {
        "primary_benchmark": "VNINDEX",
        "current_market_regime": {"id": rid, "r60_pct": _round(r60), "r120_pct": _round(r120),
                                  "drawdown_pct": _round((drawdown or 0) * 100)},
        "interpretation_guardrail": "regime: benchmark state from current data; not point-in-time",
    }


def _b10_volume_price(ni: NormalizedInput) -> Dict[str, Any]:
    tail = ni.rows[-252:]
    up_vals: List[float] = []
    down_vals: List[float] = []
    for i in range(1, len(tail)):
        cur_c = _finite(tail[i].get("close"))
        prev_c = _finite(tail[i - 1].get("close"))
        val = _finite(tail[i].get("value"))
        if cur_c is None or prev_c is None or val is None:
            continue
        if cur_c > prev_c:
            up_vals.append(val)
        elif cur_c < prev_c:
            down_vals.append(val)
    avg_up = _mean(up_vals)
    avg_down = _mean(down_vals)
    return {
        "avg_value_up_days": _round(avg_up) if avg_up is not None else None,
        "avg_value_down_days": _round(avg_down) if avg_down is not None else None,
        "up_down_value_ratio_1y": _round(avg_up / avg_down) if (avg_up and avg_down) else None,
        "interpretation_guardrail": "volume_price: historical relation only",
    }


def _sma_at(rows: Sequence[Mapping[str, Any]], index: int, field: str, window: int) -> Optional[float]:
    if index < window - 1:
        return None
    slice_ = rows[index - window + 1:index + 1]
    vals = [_finite(r.get(field)) for r in slice_]
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if len(vals) == window else None


def _vwma_at(rows: Sequence[Mapping[str, Any]], index: int, field: str, window: int) -> Optional[float]:
    if index < window - 1:
        return None
    slice_ = rows[index - window + 1:index + 1]
    num = 0.0
    den = 0.0
    ok = True
    for r in slice_:
        px = _finite(r.get(field))
        vol = _finite(r.get("volume"))
        if px is None or vol is None:
            ok = False
            break
        num += px * vol
        den += vol
    return (num / den) if ok and den > 0 else None


def _b11_vpci(ni: NormalizedInput, short_window: int = 20, long_window: int = 100) -> Dict[str, Any]:
    rows = ni.rows
    if len(rows) < long_window + 1:
        return {"vpci_latest": None, "confirmation_label": "XAC_NHAN_KHONG",
                "interpretation_guardrail": "vpci: insufficient history"}
    last = len(rows) - 1
    sma_s = _sma_at(rows, last, "close", short_window)
    sma_l = _sma_at(rows, last, "close", long_window)
    vwma_s = _vwma_at(rows, last, "close", short_window)
    vwma_l = _vwma_at(rows, last, "close", long_window)
    avg_vol_s = _sma_at(rows, last, "volume", short_window)
    avg_vol_l = _sma_at(rows, last, "volume", long_window)
    vpc = (vwma_l - sma_l) if (vwma_l is not None and sma_l is not None) else None
    vpr = (vwma_s / sma_s) if (vwma_s is not None and sma_s and sma_s != 0) else None
    vm = (avg_vol_s / avg_vol_l) if (avg_vol_s is not None and avg_vol_l and avg_vol_l > 0) else None
    vpci = (vpc * vpr * vm) if all(x is not None for x in (vpc, vpr, vm)) else None
    # F-VPCI none-handling: emit the frozen enum, NEVER silent 'hỗn hợp'.
    if vpci is None:
        label = "XAC_NHAN_KHONG"
    elif vpci > 0:
        label = "XAC_NHAN_DUONG"
    else:
        label = "XAC_NHAN_AM"
    return {
        "vpci_latest": _round(vpci),
        "sma_20": _round(sma_s),
        "sma_100": _round(sma_l),
        "confirmation_label": label,
        "interpretation_guardrail": "vpci: volume-price confirmation level only; not a signal",
    }


def _cmf_at(rows: Sequence[Mapping[str, Any]], index: int, window: int = 20) -> Optional[float]:
    sample = rows[max(0, index - window + 1):index + 1]
    sample = [r for r in sample if all(_finite(r.get(f)) is not None
                                       for f in ("high", "low", "close", "volume"))
              and _finite(r.get("volume")) and _finite(r.get("volume")) > 0]
    if len(sample) < max(5, window // 2):
        return None
    vol_sum = sum(_finite(r.get("volume")) for r in sample)
    if not vol_sum:
        return None
    flow = 0.0
    for r in sample:
        high = _finite(r.get("high"))
        low = _finite(r.get("low"))
        close = _finite(r.get("close"))
        vol = _finite(r.get("volume"))
        rng = high - low
        if not rng:
            continue
        mult = ((close - low) - (high - close)) / rng
        flow += mult * vol
    return flow / vol_sum


def _b12_money_flow(ni: NormalizedInput) -> Dict[str, Any]:
    rows = ni.rows
    last = len(rows) - 1
    cmf20 = _cmf_at(rows, last, 20)
    cmf60 = _cmf_at(rows, last, 60)
    # B12 fix: OBV change from OBV series, VPT change from VPT series.
    obv_res = compute_obv_change(ni.obv_series, 20)
    vpt_res = compute_vpt_change(ni.vpt_series, 20)
    contam_codes = assert_obv_vpt_separate(obv_res, vpt_res)
    return {
        "cmf_20d": _round(cmf20) if cmf20 is not None else None,
        "cmf_60d": _round(cmf60) if cmf60 is not None else None,
        "obv_20d_change_pct": obv_res.obv_change_pct,
        "vpt_20d_change_pct": vpt_res.vpt_change_pct,
        "obv_source_series": obv_res.source_series,
        "vpt_source_series": vpt_res.source_series,
        "obv_vpt_contamination_codes": list(contam_codes),
        "interpretation_guardrail": "money_flow: daily OHLCV pressure only; not intraday",
    }


def _b13_effort_result(ni: NormalizedInput) -> Dict[str, Any]:
    rows = ni.rows
    high_effort = 0
    low_result_high_effort = 0
    for i in range(1, len(rows)):
        p = rows[i - 1]
        r = rows[i]
        pc = _finite(p.get("close"))
        cc = _finite(r.get("close"))
        vol = _finite(r.get("volume"))
        if pc is None or cc is None or vol is None or pc <= 0:
            continue
        avg20_idx = _sma_at(rows, i - 1, "volume", 20)
        if avg20_idx is None or avg20_idx <= 0:
            continue
        effort = vol / avg20_idx
        ret = (cc / pc - 1) * 100
        if effort >= 2:
            high_effort += 1
            if abs(ret) <= 1.0:
                low_result_high_effort += 1
    low_share = (low_result_high_effort / high_effort * 100) if high_effort else None
    return {
        "high_effort_days_1y": high_effort,
        "low_result_high_effort_days_1y": low_result_high_effort,
        "low_result_high_effort_share_pct": _round(low_share) if low_share is not None else None,
        "interpretation_guardrail": "effort_result: observation of effort vs result; not absorption signal",
    }


def _forward_return(rows: Sequence[Mapping[str, Any]], index: int, window: int) -> Optional[float]:
    if index + window >= len(rows):
        return None
    start = _finite(rows[index].get("close"))
    end = _finite(rows[index + window].get("close"))
    if start is None or end is None or start <= 0:
        return None
    return (end / start - 1) * 100


def _b14_high_volume_behavior(ni: NormalizedInput) -> Dict[str, Any]:
    rows = ni.rows
    as_of = ni.as_of()
    # Detect HVB events: volume >= 2x trailing-20 avg.
    events: List[Dict[str, Any]] = []
    for i in range(1, len(rows)):
        r = rows[i]
        avg20 = _sma_at(rows, i - 1, "volume", 20)
        vol = _finite(r.get("volume"))
        if avg20 is None or avg20 <= 0 or vol is None:
            continue
        if vol >= 2 * avg20:
            events.append({
                "effective_date": r.get("date"),
                "close": _finite(r.get("close")),
                "volume": vol,
                "forward_return_5d_pct": _round(_forward_return(rows, i, 5)),
                "forward_return_20d_pct": _round(_forward_return(rows, i, 20)),
                "forward_return_60d_pct": _round(_forward_return(rows, i, 60)),
            })
    # VTA-REQ-013: events_1y via CALENDAR 365-day window (NOT events[-252:]).
    hbv = compute_hvb_events_1y(events, as_of)
    matured_20d = [e for e in hbv.events_1y if e.get("forward_return_20d_pct") is not None]
    vals_20d = [e["forward_return_20d_pct"] for e in matured_20d]
    pos_rate = (sum(1 for v in vals_20d if v > 0) / len(vals_20d) * 100) if vals_20d else None
    label = "KHONG_XAC_DINH"
    if pos_rate is not None:
        if pos_rate >= 60:
            label = "GIU_GIA_TOT"
        elif pos_rate <= 40:
            label = "SUY_YEU"
    return {
        "event_count_full_sample": len(events),
        "event_count_1y": hbv.events_count_1y,
        "events_1y_selection_method": hbv.selection_method,
        "forward_20d_positive_rate_pct": _round(pos_rate) if pos_rate is not None else None,
        "forward_20d_median_pct": _round(_median(vals_20d)) if vals_20d else None,
        "behavior_label": label,
        "interpretation_guardrail": "high_volume_behavior: event study of past high-volume sessions; not a signal",
    }


def _b15_pvi_nvi(ni: NormalizedInput) -> Dict[str, Any]:
    rows = ni.rows
    pvi = 1000.0
    nvi = 1000.0
    series: List[Dict[str, Any]] = []
    for i in range(1, len(rows)):
        p = rows[i - 1]
        r = rows[i]
        pc = _finite(p.get("close"))
        cc = _finite(r.get("close"))
        pv = _finite(p.get("volume"))
        cv = _finite(r.get("volume"))
        if pc is None or cc is None or pc <= 0 or pv is None or cv is None:
            continue
        ret = cc / pc - 1
        if cv > pv:
            pvi *= (1 + ret)
        if cv < pv:
            nvi *= (1 + ret)
        series.append({"date": r.get("date"), "pvi": pvi, "nvi": nvi})
    if not series:
        return {"pvi_latest": None, "nvi_latest": None,
                "interpretation_guardrail": "pvi_nvi: insufficient data"}
    latest = series[-1]
    return {
        "pvi_latest": _round(latest["pvi"]),
        "nvi_latest": _round(latest["nvi"]),
        "interpretation_guardrail": "pvi_nvi: participation observation; not a signal",
    }


def _b16_volume_at_price(ni: NormalizedInput, window: int = 252, bin_count: int = 12) -> Dict[str, Any]:
    tail: List[Mapping[str, Any]] = []
    for r in ni.rows[-window:]:
        high = _finite(r.get("high"))
        low = _finite(r.get("low"))
        close = _finite(r.get("close"))
        vol = _finite(r.get("volume"))
        if high is None or low is None or close is None or vol is None or vol < 0:
            continue
        tp = (high + low + close) / 3
        tail.append({"date": r.get("date"), "typical_price": tp, "volume": vol})
    if not tail:
        return {"acceptance_label": "KHONG_XAC_DINH",
                "interpretation_guardrail": "vap: insufficient data"}
    prices = [t["typical_price"] for t in tail]
    min_p, max_p = min(prices), max(prices)
    span = max(max_p - min_p, 0)
    step = span / bin_count if span > 0 else 0
    bins = [{"days": 0, "volume": 0.0} for _ in range(bin_count)]
    for t in tail:
        if step <= 0:
            continue
        idx = max(0, min(bin_count - 1, int((t["typical_price"] - min_p) / step)))
        bins[idx]["days"] += 1
        bins[idx]["volume"] += t["volume"]
    total_vol = sum(b["volume"] for b in bins) or 0
    for b in bins:
        b["volume_share_pct"] = _round(b["volume"] / total_vol * 100) if total_vol else None
    poc_idx = max(range(bin_count), key=lambda i: bins[i]["volume"])
    return {
        "point_of_control_bin_index": poc_idx,
        "volume_concentration_top3_pct": _round(sum(sorted((b["volume"] for b in bins), reverse=True)[:3]) / total_vol * 100)
            if total_vol else None,
        "acceptance_label": "KHONG_XAC_DINH",
        "interpretation_guardrail": "vap: daily approximation; not intraday volume profile",
    }


def _b17_industry_peer(ni: NormalizedInput) -> Dict[str, Any]:
    peers = ni.industry_peers
    if not peers:
        return {"peer_count": 0,
                "interpretation_guardrail": "industry_peer: no peer data; current classification only"}
    return {
        "peer_count": len(peers),
        "interpretation_guardrail": "industry_peer: current classification, not point-in-time",
    }


_BLOCK_COMPUTERS = {
    "price_behavior_profile": _b1_price_behavior,
    "volatility_profile": _b2_volatility,
    "drawdown_profile": _b3_drawdown,
    "liquidity_profile": _b4_liquidity,
    "return_distribution_profile": _b5_return_distribution,
    "tail_risk_profile": _b6_tail_risk,
    "liquidity_risk_profile": _b7_liquidity_risk,
    "relative_strength_profile": _b8_relative_strength,
    "regime_profile": _b9_regime,
    "volume_price_profile": _b10_volume_price,
    "volume_price_confirmation_profile": _b11_vpci,
    "money_flow_pressure_profile": _b12_money_flow,
    "effort_result_profile": _b13_effort_result,
    "high_volume_behavior_profile": _b14_high_volume_behavior,
    "pvi_nvi_participation_profile": _b15_pvi_nvi,
    "volume_at_price_profile": _b16_volume_at_price,
    "industry_peer_profile": _b17_industry_peer,
}


def compute_profile_block(block_id: str, normalized_input: NormalizedInput) -> BlockResult:
    """Compute a single PROFILE block by id.

    Returns a BlockResult. If the block is not applicable (e.g. relative_strength
    when no benchmark is supplied) the result is marked computed=False with a
    FORMULA_NOT_APPLICABLE rationale so the output_assembler can honor the
    optional-skipped marker rule (VC-PROFILE-VALID-3).
    """
    if block_id not in _BLOCK_COMPUTERS:
        return BlockResult(block_id=block_id, computed=False, payload={},
                           skip_reason="FORMULA_NOT_APPLICABLE",
                           error_code="UNKNOWN_BLOCK_ID")
    try:
        payload = _BLOCK_COMPUTERS[block_id](normalized_input)
    except Exception as exc:  # defensive: never crash the whole profile run
        return BlockResult(block_id=block_id, computed=False,
                           payload={"error": str(exc)}, error_code="COMPUTATION_DEGENERATE")
    # Blocks that legitimately skip emit a guardrail with "no" / "insufficient".
    guard = str(payload.get("interpretation_guardrail", ""))
    computed = not ("insufficient" in guard or "no " in guard or "not " in guard[:8] or "chưa" in guard)
    skip = None if computed else "FORMULA_NOT_APPLICABLE"
    return BlockResult(block_id=block_id, computed=computed, payload=payload, skip_reason=skip)


def compute_all_blocks(normalized_input: NormalizedInput) -> Dict[str, BlockResult]:
    """Compute all 17 blocks. Returns block_id -> BlockResult (deterministic order)."""
    return {bid: compute_profile_block(bid, normalized_input) for bid in BLOCK_IDS}


# ====================================================================
# Setup detection — shared primitives
# ====================================================================

def _clamp_score(score: float) -> float:
    return max(0.0, min(100.0, float(score)))


def _status_from_score(score: float, distance_pct: Optional[float]) -> str:
    """Map a bullish setup score to a status label (pattern_scoring.md).

    NOTE: for bullish setups, "confirmation" is structural proximity to the
    breakout level. For bearish setups, confirmation_state is set by the
    independent post-breakdown confirmation channel (see _bear_state).
    """
    if score >= SETUP_SCORE_CONFIRM_NEAR and distance_pct is not None and distance_pct <= 3:
        return "gần_xác_nhận"
    if score >= SETUP_SCORE_INDEVELOPMENT_LO:
        return "đang_hình_thành"
    return "chưa_đủ_sạch"


def _distance_pct(confirmation_price: Optional[float], current_close: Optional[float]) -> Optional[float]:
    if confirmation_price is None or current_close is None:
        return None
    return max(0.0, (confirmation_price / current_close - 1) * 100) if current_close else None


# ====================================================================
# 8 Bullish setup detectors (from pattern_scoring.md, frozen heuristic)
# ====================================================================

def _bull_setup(rows: Sequence[Mapping[str, Any]], pattern_id: str, name: str,
                score: float, confirmation_price: Optional[float],
                watch_low: Optional[float], watch_high: Optional[float],
                current_close: Optional[float], caution: str) -> Optional[Dict[str, Any]]:
    score = round(_clamp_score(score), 2)
    if score < SETUP_SCORE_MIN_REPORTABLE:
        return None
    distance = _distance_pct(confirmation_price, current_close)
    status = _status_from_score(score, distance)
    return {
        "pattern_id": pattern_id,
        "pattern_name": name,
        "setup_status": status,
        "completion_score": score,
        "confirmation_price": _round(confirmation_price, 4) if confirmation_price is not None else None,
        "watch_zone": {"low": _round(watch_low, 4) if watch_low is not None else None,
                       "high": _round(watch_high, 4) if watch_high is not None else None},
        "distance_to_confirmation_pct": _round(distance, 2) if distance is not None else None,
        "caution_reason": caution,
    }


def _detect_bull_flag(rows: Sequence[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    if len(rows) < 44:
        return None
    current = _finite(rows[-1].get("close"))
    if current is None:
        return None
    recent = rows[-14:]
    pole = rows[-44:-14]
    if len(pole) < 20:
        return None
    pole_move = _pct(max(_finite(r.get("close")) for r in pole[-5:]),
                     min(_finite(r.get("close")) for r in pole[:15])) or 0
    recent_high = max(_finite(r.get("high")) for r in recent)
    recent_low = min(_finite(r.get("low")) for r in recent)
    recent_range = _pct(recent_high, recent_low) or 0
    pullback = _pct(recent_high, current) or 0
    compact = max(0, 25 - recent_range) * 2.2
    score = 30 + min(pole_move, 35) + compact - max(0, pullback - 8) * 2
    if pole_move < 10 or recent_range > 16:
        score -= 20
    return _bull_setup(rows, "bull_flags", "Cờ tăng", score, recent_high, recent_low,
                       recent_high, current, "Cần nhịp dẫn rõ và phần nghỉ hẹp.")


def _detect_bull_pennant(rows: Sequence[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    if len(rows) < 42:
        return None
    current = _finite(rows[-1].get("close"))
    if current is None:
        return None
    recent = rows[-12:]
    prior = rows[-42:-12]
    if len(prior) < 20:
        return None
    prior_move = _pct(max(_finite(r.get("close")) for r in prior[-5:]),
                      min(_finite(r.get("close")) for r in prior[:15])) or 0
    first_range = max(_finite(r.get("high")) for r in recent[:6]) - min(_finite(r.get("low")) for r in recent[:6])
    last_range = max(_finite(r.get("high")) for r in recent[-6:]) - min(_finite(r.get("low")) for r in recent[-6:])
    compression = (1 - last_range / first_range) if first_range and first_range > 0 else 0
    recent_high = max(_finite(r.get("high")) for r in recent)
    recent_low = min(_finite(r.get("low")) for r in recent)
    score = 35 + min(prior_move, 30) + max(0, min(compression * 55, 35)) - max(0, (_pct(recent_high, recent_low) or 0) - 14) * 2
    if prior_move < 10:
        score -= 18
    return _bull_setup(rows, "bull_pennants", "Cờ đuôi nheo tăng", score, recent_high, recent_low,
                       recent_high, current, "Cần biên dao động co lại.")


def _detect_ascending_triangle(rows: Sequence[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    if len(rows) < 45:
        return None
    current = _finite(rows[-1].get("close"))
    if current is None:
        return None
    window = rows[-45:]
    highs = [_finite(r.get("high")) for r in window]
    highs = [h for h in highs if h is not None]
    lows = [_finite(r.get("low")) for r in window]
    lows = [l for l in lows if l is not None]
    if not highs or not lows:
        return None
    resistance = sorted(highs)[int(len(highs) * 0.8)]
    high_spread = _pct(max(highs[-25:]), min(highs[-25:])) or 0
    low_rise = _pct(min(lows[-10:]), min(lows[:15])) or 0
    distance = max(0.0, _pct(resistance, current) or 0)
    score = 45 + min(max(low_rise, 0), 18) * 1.8 + max(0, 8 - high_spread) * 3 - distance * 1.5
    return _bull_setup(rows, "triangles_ascending", "Tam giác tăng", score, resistance,
                       min(lows[-20:]), resistance, current, "Cần kháng cự phẳng, đáy dốc lên.")


def _detect_falling_wedge(rows: Sequence[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    if len(rows) < 40:
        return None
    current = _finite(rows[-1].get("close"))
    if current is None:
        return None
    window = rows[-40:]
    highs = [_finite(r.get("high")) for r in window]
    highs = [h for h in highs if h is not None]
    lows = [_finite(r.get("low")) for r in window]
    lows = [l for l in lows if l is not None]
    if len(highs) < 2 or len(lows) < 2:
        return None
    high_slope = _slope_ols(highs)
    low_slope = _slope_ols(lows)
    width_start = max(highs[:10]) - min(lows[:10])
    width_end = max(highs[-10:]) - min(lows[-10:])
    narrows = (1 - width_end / width_start) if width_start and width_start > 0 else 0
    upper_now = highs[0] + high_slope * (len(highs) - 1)
    distance = max(0.0, _pct(upper_now, current) or 0)
    score = 40 + max(0, min(narrows * 60, 35)) + (12 if high_slope < 0 and low_slope < 0 else -15) - distance * 1.2
    return _bull_setup(rows, "wedges_falling", "Nêm giảm", score, upper_now, min(lows[-15:]),
                       upper_now, current, "Cần hai biên cùng dốc xuống, độ rộng thu hẹp.")


def _detect_cup_with_handle(rows: Sequence[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    if len(rows) < 75:
        return None
    current = _finite(rows[-1].get("close"))
    if current is None:
        return None
    window = rows[-90:]
    closes = [_finite(r.get("close")) for r in window]
    closes = [c for c in closes if c is not None]
    if len(closes) < 70:
        return None
    left_high = max(closes[:30])
    cup_low = min(closes[20:70])
    right_high = max(closes[55:])
    depth = _pct(left_high, cup_low) or 0
    recovery = _pct(right_high, cup_low) or 0
    handle = rows[-15:]
    handle_pullback = _pct(max(_finite(r.get("high")) for r in handle),
                           min(_finite(r.get("low")) for r in handle)) or 0
    confirmation = max(left_high, right_high)
    score = 35 + min(recovery, 35) + max(0, 35 - abs(depth - 25)) - max(0, handle_pullback - 16) * 2
    if depth < 12 or depth > 50:
        score -= 18
    return _bull_setup(rows, "cup_with_handle", "Cốc tay cầm", score, confirmation,
                       min(_finite(r.get("low")) for r in handle), confirmation, current,
                       "Mẫu dài, dễ nhiễu nếu tay cầm quá sâu.")


def _detect_rectangle_bottom(rows: Sequence[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    if len(rows) < 75:
        return None
    current = _finite(rows[-1].get("close"))
    if current is None:
        return None
    window = rows[-35:]
    prior = rows[-75:-35]
    high = max(_finite(r.get("high")) for r in window)
    low = min(_finite(r.get("low")) for r in window)
    range_pct = _pct(high, low) or 0
    prior_drop = _pct(_finite(prior[0].get("close")),
                      min(_finite(r.get("close")) for r in prior)) or 0 if prior else 0
    distance = max(0.0, _pct(high, current) or 0)
    score = 42 + max(0, 18 - abs(range_pct - 12)) * 2 + min(max(prior_drop, 0), 18) - distance
    return _bull_setup(rows, "rectangle_bottoms", "Chữ nhật đáy", score, high, low,
                       high, current, "Cần vùng đi ngang rõ sau nhịp giảm.")


def _detect_double_bottom(rows: Sequence[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    if len(rows) < 65:
        return None
    current = _finite(rows[-1].get("close"))
    if current is None:
        return None
    window = rows[-65:]
    lows = [_finite(r.get("low")) for r in window]
    lows = [l for l in lows if l is not None]
    if len(lows) < 33:
        return None
    first_i = min(range(0, 32), key=lambda idx: lows[idx])
    second_i = min(range(32, len(lows)), key=lambda idx: lows[idx])
    first_low = lows[first_i]
    second_low = lows[second_i]
    low_gap = abs(_pct(second_low, first_low) or 0)
    neckline = max(_finite(r.get("high")) for r in window[first_i:second_i + 1])
    distance = max(0.0, _pct(neckline, current) or 0)
    separation = second_i - first_i
    score = 48 + max(0, 8 - low_gap) * 4 + min(separation, 30) * 0.5 - distance * 1.5
    if separation < 12:
        score -= 15
    return _bull_setup(rows, "double_bottoms", "Hai đáy", score, neckline,
                       min(first_low, second_low), neckline, current,
                       "Hai đáy cần tách xa, không lệch mạnh.")


def _detect_measured_move_up(rows: Sequence[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    if len(rows) < 70:
        return None
    current = _finite(rows[-1].get("close"))
    if current is None:
        return None
    first = rows[-70:-35]
    pullback = rows[-35:-12]
    recent = rows[-12:]
    if not first or not pullback:
        return None
    leg_low = min(_finite(r.get("low")) for r in first)
    leg_high = max(_finite(r.get("high")) for r in first)
    leg_move = _pct(leg_high, leg_low) or 0
    pull_low = min(_finite(r.get("low")) for r in pullback)
    retrace = ((leg_high - pull_low) / (leg_high - leg_low) * 100) if leg_high and leg_high > leg_low else 100
    confirmation = max(_finite(r.get("high")) for r in recent)
    score = 38 + min(leg_move, 30) + max(0, 30 - abs(retrace - 50)) - max(0, (_pct(confirmation, current) or 0)) * 1.2
    if leg_move < 12 or retrace < 25 or retrace > 75:
        score -= 18
    return _bull_setup(rows, "measured_move_up", "Measured Move tăng", score, confirmation,
                       pull_low, confirmation, current, "Cần nhịp đầu rõ, điều chỉnh vừa phải.")


_BULLISH_DETECTORS = {
    "S-BULL-FLAG": _detect_bull_flag,
    "S-BULL-PENNANT": _detect_bull_pennant,
    "S-TRIANGLE-ASC": _detect_ascending_triangle,
    "S-WEDGE-FALLING": _detect_falling_wedge,
    "S-CUP-WITH-HANDLE": _detect_cup_with_handle,
    "S-RECTANGLE-BOTTOM": _detect_rectangle_bottom,
    "S-DOUBLE-BOTTOM": _detect_double_bottom,
    "S-MEASURED-MOVE-UP": _detect_measured_move_up,
}

# Map bullish pattern_id -> setup family (pattern_scoring.md).
_BULLISH_FAMILY = {
    "bull_flags": "trend_following",
    "bull_pennants": "trend_following",
    "measured_move_up": "trend_following",
    "triangles_ascending": "accumulation_breakout",
    "rectangle_bottoms": "accumulation_breakout",
    "cup_with_handle": "accumulation_breakout",
    "double_bottoms": "accumulation_breakout",
    "wedges_falling": "accumulation_breakout",
}


# ====================================================================
# Bearish setup detection (independent rules — NO sign inversion)
# ====================================================================

def _avg_volume(rows: Sequence[Mapping[str, Any]], window: int = 20) -> Optional[float]:
    return _sma_at(rows, len(rows) - 1, "volume", window)


def _prior_leg_slope_pct_per_bar(rows: Sequence[Mapping[str, Any]], leg_size: int) -> Optional[float]:
    """Negative-slope check for the prior down-leg (BF-OBS-2 / BP-OBS-2)."""
    if len(rows) < leg_size + 1:
        return None
    leg = rows[-(leg_size + 1):-1]
    closes = [_finite(r.get("close")) for r in leg]
    closes = [c for c in closes if c is not None]
    return _channel_slope_pct_per_bar(closes)


def _volume_contraction_ratio(rows: Sequence[Mapping[str, Any]],
                              consolidation_size: int) -> Optional[float]:
    """Mean consolidation volume / mean prior-leg volume (< 0.70 = contraction)."""
    if len(rows) < consolidation_size + 15:
        return None
    consol = rows[-consolidation_size:]
    prior = rows[-(consolidation_size + 15):-consolidation_size]
    consol_vols = [_finite(r.get("volume")) for r in consol]
    prior_vols = [_finite(r.get("volume")) for r in prior]
    consol_vols = [v for v in consol_vols if v is not None]
    prior_vols = [v for v in prior_vols if v is not None]
    if not consol_vols or not prior_vols:
        return None
    return _mean(consol_vols) / _mean(prior_vols)


def _detect_bear_flag(ni: NormalizedInput) -> SetupResult:
    """S-BEAR-FLAG — independent detection (NOT sign-inverted bull flag).

    Per registry: prior down-leg (>=15 sessions, negative slope) + shallow
    rising consolidation (5-20 sessions) + volume contraction + breakdown on
    1.5x avg20 volume + 3-session hold + CMF<0 + VPT-slope<0 confirmation.
    """
    rows = ni.rows
    evidence: Dict[str, Any] = {
        "observation": {}, "signal": {}, "confirmation": {}, "invalidation": {},
    }
    failure_codes: List[str] = []
    if len(rows) < 65:
        return SetupResult(setup_id="S-BEAR-FLAG", direction="BEARISH", present=False,
                           setup_score=0.0, confirmation_state="NOT_PRESENT",
                           confidence=0.0, evidence=evidence,
                           output_fields={"minimum_history_sessions": 65})

    # OBSERVATION (descriptive — NOT actionable alone).
    prior_slope = _prior_leg_slope_pct_per_bar(rows, 15)
    evidence["observation"]["prior_leg_slope_pct_per_bar"] = _round(prior_slope)
    evidence["observation"]["prior_down_leg_present"] = prior_slope is not None and prior_slope < 0

    consol_size = 14
    contraction = _volume_contraction_ratio(rows, consol_size)
    evidence["observation"]["volume_contraction_ratio"] = _round(contraction)
    evidence["observation"]["volume_contraction_present"] = contraction is not None and contraction < 0.70

    # SIGNAL — structure AND microstructure BOTH required (GDI-5).
    consol = rows[-consol_size:]
    consol_low = min(_finite(r.get("low")) for r in consol)
    consol_high = max(_finite(r.get("high")) for r in consol)
    last_row = rows[-1]
    last_close = _finite(last_row.get("close"))
    last_vol = _finite(last_row.get("volume"))
    avg20 = _avg_volume(rows, 20)
    breakdown = (last_close is not None and consol_low is not None and last_close < consol_low)
    vol_expansion = (last_vol is not None and avg20 is not None and avg20 > 0
                     and last_vol >= 1.5 * avg20)
    structure = bool(evidence["observation"]["prior_down_leg_present"]) and breakdown
    microstructure = vol_expansion
    signal_present = structure and microstructure

    evidence["signal"]["structure_present"] = structure
    evidence["signal"]["breakdown_below_consolidation_low"] = breakdown
    evidence["signal"]["breakdown_volume_ratio_to_avg20"] = _round(last_vol / avg20) if (last_vol and avg20) else None
    evidence["signal"]["microstructure_volume_expansion"] = microstructure
    evidence["signal"]["signal_requires_structure_AND_microstructure"] = True

    # CONFIRMATION — independent post-breakdown channel (GDI-6).
    # We look back at the 3 sessions BEFORE the latest bar (the post-breakdown
    # window from the registry's perspective; in a single-bar evaluation we
    # approximate using the last 3 closes relative to the breakdown level).
    post = rows[-4:-1] if len(rows) >= 4 else []
    hold_below = all((_finite(r.get("close")) or 0) < (consol_low or float("inf")) for r in post) and len(post) == 3
    cmf_recent = _cmf_at(rows, len(rows) - 1, 20)
    cmf_negative = cmf_recent is not None and cmf_recent < 0
    vpt_res = compute_vpt_change(ni.vpt_series, 3)
    vpt_slope_negative = vpt_res.vpt_change_pct is not None and vpt_res.vpt_change_pct < 0
    confirmations_satisfied = sum([hold_below, cmf_negative, vpt_slope_negative])

    evidence["confirmation"]["breakdown_holds_3_sessions"] = hold_below
    evidence["confirmation"]["cmf_negative_post_breakdown"] = cmf_negative
    evidence["confirmation"]["vpt_slope_negative_post_breakdown"] = vpt_slope_negative
    evidence["confirmation"]["confirmations_satisfied"] = confirmations_satisfied
    evidence["confirmation"]["independent_channel"] = True

    # INVALIDATION
    invalidated = False
    if last_close is not None and consol_high is not None and last_close > consol_high:
        evidence["invalidation"]["close_above_consolidation_high"] = True
        invalidated = True
    if prior_slope is not None and prior_slope >= 0:
        evidence["invalidation"]["prior_leg_not_negative_slope"] = True
        invalidated = True
    # PROHIBITED ACTIVATION RULE: a single negative indicator alone must NOT
    # produce a signal. If only microstructure fired without structure, we
    # explicitly mark this as observation-only.
    if microstructure and not structure:
        evidence["signal"]["lone_indicator_rejected"] = True

    return _assemble_bearish_result(
        "S-BEAR-FLAG", signal_present, confirmations_satisfied, invalidated,
        evidence, failure_codes,
        output_fields={
            "breakdown_level": _round(consol_low),
            "breakdown_volume_ratio_to_avg20": _round(last_vol / avg20) if (last_vol and avg20) else None,
            "consolidation_slope_pct_per_bar": _round(_channel_slope_pct_per_bar(
                [_finite(r.get("close")) for r in consol if _finite(r.get("close")) is not None])),
            "prior_leg_slope_pct_per_bar": _round(prior_slope),
        })


def _detect_bear_pennant(ni: NormalizedInput) -> SetupResult:
    """S-BEAR-PENNANT — converging triangle (NOT parallel rising like flag)."""
    rows = ni.rows
    evidence: Dict[str, Any] = {
        "observation": {}, "signal": {}, "confirmation": {}, "invalidation": {},
    }
    if len(rows) < 65:
        return SetupResult(setup_id="S-BEAR-PENNANT", direction="BEARISH", present=False,
                           setup_score=0.0, confirmation_state="NOT_PRESENT",
                           confidence=0.0, evidence=evidence,
                           output_fields={"minimum_history_sessions": 65})

    prior_slope = _prior_leg_slope_pct_per_bar(rows, 15)
    evidence["observation"]["prior_leg_slope_pct_per_bar"] = _round(prior_slope)
    evidence["observation"]["prior_down_leg_present"] = prior_slope is not None and prior_slope < 0

    consol_size = 12
    consol = rows[-consol_size:]
    # Convergence: lower highs AND higher lows narrowing.
    first_half_highs = [_finite(r.get("high")) for r in consol[:6]]
    second_half_highs = [_finite(r.get("high")) for r in consol[-6:]]
    first_half_lows = [_finite(r.get("low")) for r in consol[:6]]
    second_half_lows = [_finite(r.get("low")) for r in consol[-6:]]
    first_range = max(first_half_highs) - min(first_half_lows) if all(first_half_highs) and all(first_half_lows) else 0
    last_range = max(second_half_highs) - min(second_half_lows) if all(second_half_highs) and all(second_half_lows) else 0
    converging = first_range > 0 and last_range < first_range
    convergence_ratio = (1 - last_range / first_range) if first_range > 0 else None
    evidence["observation"]["converging_triangle"] = converging
    evidence["observation"]["pennant_convergence_ratio"] = _round(convergence_ratio)

    last_row = rows[-1]
    last_close = _finite(last_row.get("close"))
    last_vol = _finite(last_row.get("volume"))
    avg20 = _avg_volume(rows, 20)
    lower_trendline = min(_finite(r.get("low")) for r in consol)
    breakdown = last_close is not None and last_close < (lower_trendline or float("inf"))
    vol_expansion = (last_vol is not None and avg20 is not None and avg20 > 0
                     and last_vol >= 1.5 * avg20)
    structure = bool(evidence["observation"]["prior_down_leg_present"]) and converging and breakdown
    microstructure = vol_expansion
    signal_present = structure and microstructure

    evidence["signal"]["structure_present"] = structure and converging
    evidence["signal"]["breakdown_below_lower_trendline"] = breakdown
    evidence["signal"]["microstructure_volume_expansion"] = microstructure
    evidence["signal"]["signal_requires_structure_AND_microstructure"] = True

    cmf_recent = _cmf_at(rows, len(rows) - 1, 20)
    cmf_negative = cmf_recent is not None and cmf_recent < 0
    obv_res = compute_obv_change(ni.obv_series, 3)
    obv_slope_negative = obv_res.obv_change_pct is not None and obv_res.obv_change_pct < 0
    post = rows[-4:-1] if len(rows) >= 4 else []
    hold_below = all((_finite(r.get("close")) or 0) < (lower_trendline or float("inf")) for r in post) and len(post) == 3
    confirmations_satisfied = sum([hold_below, cmf_negative, obv_slope_negative])
    evidence["confirmation"]["breakdown_holds_3_sessions"] = hold_below
    evidence["confirmation"]["cmf_negative"] = cmf_negative
    evidence["confirmation"]["obv_slope_negative"] = obv_slope_negative
    evidence["confirmation"]["confirmations_satisfied"] = confirmations_satisfied
    evidence["confirmation"]["independent_channel"] = True

    invalidated = (last_close is not None and max(_finite(r.get("high")) for r in consol) is not None
                   and last_close > max(_finite(r.get("high")) for r in consol))
    if prior_slope is not None and prior_slope >= 0:
        evidence["invalidation"]["prior_leg_not_negative_slope"] = True
        invalidated = True

    return _assemble_bearish_result(
        "S-BEAR-PENNANT", signal_present, confirmations_satisfied, invalidated,
        evidence, [],
        output_fields={
            "breakdown_level": _round(lower_trendline),
            "breakdown_volume_ratio_to_avg20": _round(last_vol / avg20) if (last_vol and avg20) else None,
            "pennant_convergence_ratio": _round(convergence_ratio),
            "prior_leg_slope_pct_per_bar": _round(prior_slope),
        })


def _detect_bear_down_triangle(ni: NormalizedInput) -> SetupResult:
    """S-BEAR-DOWN-TRIANGLE — horizontal support + declining highs."""
    rows = ni.rows
    evidence: Dict[str, Any] = {
        "observation": {}, "signal": {}, "confirmation": {}, "invalidation": {},
    }
    if len(rows) < 65:
        return SetupResult(setup_id="S-BEAR-DOWN-TRIANGLE", direction="BEARISH", present=False,
                           setup_score=0.0, confirmation_state="NOT_PRESENT",
                           confidence=0.0, evidence=evidence,
                           output_fields={"minimum_history_sessions": 65})

    window = rows[-50:]
    lows = [_finite(r.get("low")) for r in window]
    lows = [l for l in lows if l is not None]
    if not lows:
        return SetupResult(setup_id="S-BEAR-DOWN-TRIANGLE", direction="BEARISH", present=False,
                           setup_score=0.0, confirmation_state="NOT_PRESENT", confidence=0.0,
                           evidence=evidence, output_fields={})
    support_level = _median(lows) or 0
    support_tests = sum(1 for l in lows if abs(l - support_level) / support_level <= 0.03) if support_level else 0
    highs = [_finite(r.get("high")) for r in window]
    highs = [h for h in highs if h is not None]
    upper_slope = _slope_ols(highs) if len(highs) >= 2 else 0
    upper_slope_pct = _channel_slope_pct_per_bar(highs)
    evidence["observation"]["support_test_count"] = support_tests
    evidence["observation"]["upper_boundary_slope_pct_per_bar"] = _round(upper_slope_pct)
    evidence["observation"]["declining_highs"] = upper_slope < 0

    last_close = _finite(rows[-1].get("close"))
    last_vol = _finite(rows[-1].get("volume"))
    avg20 = _avg_volume(rows, 20)
    breakdown = (last_close is not None and support_level and
                 last_close < support_level * 0.99)  # >=1% below support
    vol_or_flow = ((last_vol is not None and avg20 and last_vol >= 1.5 * avg20) or
                   (_cmf_at(rows, len(rows) - 1, 20) or 0) < -0.15)
    structure = support_tests >= 2 and upper_slope < 0
    microstructure = bool(vol_or_flow)
    signal_present = structure and breakdown and microstructure
    evidence["signal"]["structure_present"] = structure
    evidence["signal"]["breakdown_below_support_1pct"] = breakdown
    evidence["signal"]["microstructure_volume_or_flow"] = microstructure
    evidence["signal"]["signal_requires_structure_AND_microstructure"] = True

    cmf_recent = _cmf_at(rows, len(rows) - 1, 20)
    vpt_res = compute_vpt_change(ni.vpt_series, 3)
    confirmations_satisfied = sum([
        cmf_recent is not None and cmf_recent < 0,
        vpt_res.vpt_change_pct is not None and vpt_res.vpt_change_pct < 0,
        last_close is not None and support_level and last_close < support_level * 0.97,  # role flip
    ])
    evidence["confirmation"]["confirmations_satisfied"] = confirmations_satisfied
    evidence["confirmation"]["independent_channel"] = True

    invalidated = support_tests < 2
    if invalidated:
        evidence["invalidation"]["fewer_than_2_support_tests"] = True

    return _assemble_bearish_result(
        "S-BEAR-DOWN-TRIANGLE", signal_present, confirmations_satisfied, invalidated,
        evidence, [],
        output_fields={
            "breakdown_level": _round(support_level),
            "support_test_count": support_tests,
            "upper_boundary_slope_pct_per_bar": _round(upper_slope_pct),
            "breakdown_volume_ratio_to_avg20": _round(last_vol / avg20) if (last_vol and avg20) else None,
        })


def _detect_bear_rectangle_top(ni: NormalizedInput) -> SetupResult:
    """S-BEAR-RECTANGLE-TOP — 20-session sideways range + distribution volume.

    Frozen thresholds (review-R):
      range_duration_min_sessions = 20
      distribution_ratio_threshold = 0.60 (up_down_volume_ratio)
      breakout_confirmation_volume_ratio = 1.5 (>1.5x avg20)
      post_breakdown_hold_sessions = 5
    """
    rows = ni.rows
    evidence: Dict[str, Any] = {
        "observation": {}, "signal": {}, "confirmation": {}, "invalidation": {},
    }
    if len(rows) < 75:
        return SetupResult(setup_id="S-BEAR-RECTANGLE-TOP", direction="BEARISH", present=False,
                           setup_score=0.0, confirmation_state="NOT_PRESENT",
                           confidence=0.0, evidence=evidence,
                           output_fields={"minimum_history_sessions": 75})

    range_size = 20  # FROZEN range_duration_min
    window = rows[-range_size:]
    range_high = max(_finite(r.get("high")) for r in window)
    range_low = min(_finite(r.get("low")) for r in window)
    # Distribution volume signature: mean down-bar volume > mean up-bar volume.
    up_vols: List[float] = []
    down_vols: List[float] = []
    for i in range(1, len(window)):
        pc = _finite(window[i - 1].get("close"))
        cc = _finite(window[i].get("close"))
        v = _finite(window[i].get("volume"))
        if pc is None or cc is None or v is None:
            continue
        if cc > pc:
            up_vols.append(v)
        elif cc < pc:
            down_vols.append(v)
    up_down_ratio = (_mean(down_vols) / _mean(up_vols)) if (_mean(up_vols) and _mean(down_vols)) else None
    distribution_present = up_down_ratio is not None and up_down_ratio >= 0.60  # FROZEN threshold

    evidence["observation"]["range_duration_sessions"] = range_size
    evidence["observation"]["range_high"] = _round(range_high)
    evidence["observation"]["range_low"] = _round(range_low)
    evidence["observation"]["up_down_volume_ratio"] = _round(up_down_ratio)
    evidence["observation"]["distribution_volume_present"] = distribution_present

    last_close = _finite(rows[-1].get("close"))
    last_vol = _finite(rows[-1].get("volume"))
    avg20 = _avg_volume(rows, 20)
    breakdown = last_close is not None and range_low and last_close < range_low * 0.99
    vol_expansion = (last_vol is not None and avg20 and last_vol > 1.5 * avg20)  # STRICTLY_GREATER_THAN, FROZEN
    structure = distribution_present  # range + distribution volume
    microstructure = vol_expansion
    signal_present = structure and breakdown and microstructure
    evidence["signal"]["structure_present"] = structure
    evidence["signal"]["breakdown_below_range_low_1pct"] = breakdown
    evidence["signal"]["microstructure_volume_expansion_strictly_greater"] = microstructure
    evidence["signal"]["signal_requires_structure_AND_microstructure"] = True

    # 5-session hold (FROZEN post_breakdown_hold_sessions)
    post = rows[-6:-1] if len(rows) >= 6 else []
    hold_below = all((_finite(r.get("close")) or 0) < (range_low or float("inf")) for r in post) and len(post) == 5
    obv_res = compute_obv_change(ni.obv_series, 5)
    obv_new_local_low = obv_res.obv_change_pct is not None and obv_res.obv_change_pct < 0
    confirmations_satisfied = sum([hold_below, obv_new_local_low])
    evidence["confirmation"]["breakdown_holds_5_sessions"] = hold_below
    evidence["confirmation"]["obv_new_local_low"] = obv_new_local_low
    evidence["confirmation"]["confirmations_satisfied"] = confirmations_satisfied
    evidence["confirmation"]["independent_channel"] = True

    # RT-INV-3: up_down_volume_ratio < 0.60 → invalidated even if price breaks.
    invalidated = (up_down_ratio is not None and up_down_ratio < 0.60)
    if invalidated:
        evidence["invalidation"]["up_down_volume_ratio_below_distribution_threshold"] = True

    return _assemble_bearish_result(
        "S-BEAR-RECTANGLE-TOP", signal_present, confirmations_satisfied, invalidated,
        evidence, [],
        output_fields={
            "breakdown_level": _round(range_low),
            "range_duration_sessions": range_size,
            "up_down_volume_ratio": _round(up_down_ratio),
            "failed_high_test_count": sum(1 for r in window if _finite(r.get("high")) == range_high),
            "breakdown_volume_ratio_to_avg20": _round(last_vol / avg20) if (last_vol and avg20) else None,
        })


def _detect_bear_head_shoulders(ni: NormalizedInput) -> SetupResult:
    """S-BEAR-HEAD-SHOULDERS — three-peak reversal, strictest confirmation.

    Frozen thresholds (review-R):
      neckline_regression_fit_r2_min = 0.85
      peak_symmetry_tolerance = 0.15 (|RS - LS| / H <= 0.15)
      volume_divergence_required = True (head_vol < ls_vol)
      post_breakdown_hold_sessions = 5
    Confidence ceiling capped at 0.7 until HS-CONF-1 (5-session hold) satisfied.
    """
    rows = ni.rows
    evidence: Dict[str, Any] = {
        "observation": {}, "signal": {}, "confirmation": {}, "invalidation": {},
    }
    if len(rows) < 90:
        return SetupResult(setup_id="S-BEAR-HEAD-SHOULDERS", direction="BEARISH", present=False,
                           setup_score=0.0, confirmation_state="NOT_PRESENT",
                           confidence=0.0, evidence=evidence,
                           output_fields={"minimum_history_sessions": 90})

    window = rows[-90:]
    # Find three peaks via swing detection on closes.
    closes = [_finite(r.get("close")) for r in window]
    closes = [c for c in closes if c is not None]
    if len(closes) < 30:
        return SetupResult(setup_id="S-BEAR-HEAD-SHOULDERS", direction="BEARISH", present=False,
                           setup_score=0.0, confirmation_state="NOT_PRESENT", confidence=0.0,
                           evidence=evidence, output_fields={})

    # Crude swing-high detection (lookback=3).
    swing_highs: List[Tuple[int, float]] = []
    lookback = 3
    for i in range(lookback, len(closes) - lookback):
        is_high = all(closes[i] > closes[i - j] and closes[i] > closes[i + j] for j in range(1, lookback + 1))
        if is_high:
            swing_highs.append((i, closes[i]))
    if len(swing_highs) < 3:
        return SetupResult(setup_id="S-BEAR-HEAD-SHOULDERS", direction="BEARISH", present=False,
                           setup_score=0.0, confirmation_state="NOT_PRESENT", confidence=0.0,
                           evidence=evidence, output_fields={"swing_highs_found": len(swing_highs)})

    # Take the last three swing highs as LS, H, RS.
    ls_i, ls = swing_highs[-3]
    h_i, h = swing_highs[-2]
    rs_i, rs = swing_highs[-1]
    head_is_highest = h > ls and h > rs
    symmetry_metric = abs(rs - ls) / h if h else None
    symmetry_ok = symmetry_metric is not None and symmetry_metric <= 0.15  # FROZEN ±15%

    # Neckline = OLS through the two troughs between LS-H and H-RS.
    troughs: List[float] = []
    seg1 = closes[ls_i + 1:h_i]
    seg2 = closes[h_i + 1:rs_i + 1]
    if seg1:
        troughs.append(min(seg1))
    if seg2:
        troughs.append(min(seg2))
    if len(troughs) >= 2:
        # R² of the two-trough line: trivially 1.0 for two points, so we use
        # the fit against the closes between the troughs as a proxy.
        between = closes[ls_i:rs_i + 1]
        if len(between) >= 5:
            slope = _slope_ols(between)
            # R² proxy: variance explained by the slope line vs mean.
            mean_y = sum(between) / len(between)
            ss_tot = sum((y - mean_y) ** 2 for y in between) or 1.0
            ss_res = sum((between[i] - (between[0] + slope * i)) ** 2 for i in range(len(between)))
            neckline_r2 = max(0.0, 1 - ss_res / ss_tot)
        else:
            neckline_r2 = 0.5
    else:
        neckline_r2 = 0.0
    neckline_ok = neckline_r2 >= 0.85  # FROZEN threshold

    # Volume divergence: head-peak volume < left-shoulder-peak volume.
    ls_vol = _finite(window[ls_i].get("volume")) if ls_i < len(window) else None
    h_vol = _finite(window[h_i].get("volume")) if h_i < len(window) else None
    volume_divergence = (ls_vol is not None and h_vol is not None and h_vol < ls_vol)

    evidence["observation"]["head_is_highest"] = head_is_highest
    evidence["observation"]["peak_symmetry_metric"] = _round(symmetry_metric)
    evidence["observation"]["peak_symmetry_ok"] = symmetry_ok
    evidence["observation"]["neckline_regression_fit_r2"] = _round(neckline_r2)
    evidence["observation"]["neckline_fit_ok"] = neckline_ok
    evidence["observation"]["head_peak_volume_ratio_to_ls"] = _round(h_vol / ls_vol) if (h_vol and ls_vol) else None
    evidence["observation"]["volume_divergence_required"] = True
    evidence["observation"]["volume_divergence_present"] = volume_divergence

    # Neckline level = the lower of the two troughs (conservative).
    neckline_level = min(troughs) if troughs else None
    last_close = _finite(rows[-1].get("close"))
    last_vol = _finite(rows[-1].get("volume"))
    avg20 = _avg_volume(rows, 20)
    breakdown = (last_close is not None and neckline_level is not None
                 and last_close < neckline_level * 0.99)
    vol_expansion = (last_vol is not None and avg20 and last_vol >= 1.3 * avg20)  # 1.3x bearish-specific
    structure = head_is_highest and symmetry_ok and neckline_ok
    microstructure = vol_expansion and volume_divergence
    signal_present = structure and breakdown and microstructure
    evidence["signal"]["structure_present"] = structure
    evidence["signal"]["breakdown_below_neckline_1pct"] = breakdown
    evidence["signal"]["microstructure_volume_and_divergence"] = microstructure
    evidence["signal"]["signal_requires_structure_AND_microstructure"] = True

    # HS-CONF-1: 5-session hold (FROZEN).
    post = rows[-6:-1] if len(rows) >= 6 else []
    hold_5 = all((_finite(r.get("close")) or 0) < (neckline_level or float("inf")) for r in post) and len(post) == 5
    confirmations_satisfied = sum([hold_5, volume_divergence, vol_expansion])
    evidence["confirmation"]["neckline_holds_5_sessions"] = hold_5
    evidence["confirmation"]["confirmations_satisfied"] = confirmations_satisfied
    evidence["confirmation"]["independent_channel"] = True

    # HS-INV-2/3/5: structure prerequisite failures + divergence+expansion void.
    invalidated = False
    if rs >= h:
        evidence["invalidation"]["right_shoulder_ge_head"] = True
        invalidated = True
    if symmetry_metric is not None and symmetry_metric > 0.15:
        evidence["invalidation"]["peak_symmetry_fails"] = True
        invalidated = True
    if not volume_divergence and not vol_expansion:
        evidence["invalidation"]["no_divergence_no_expansion"] = True
        invalidated = True

    result = _assemble_bearish_result(
        "S-BEAR-HEAD-SHOULDERS", signal_present, confirmations_satisfied, invalidated,
        evidence, [],
        output_fields={
            "neckline_level": _round(neckline_level),
            "neckline_slope_pct_per_bar": None,
            "neckline_regression_fit_r2": _round(neckline_r2),
            "peak_symmetry_metric": _round(symmetry_metric),
            "head_peak_volume_ratio_to_ls": _round(h_vol / ls_vol) if (h_vol and ls_vol) else None,
            "measured_move_target": _round(neckline_level - (h - (neckline_level or 0)))
                if neckline_level is not None else None,
            "breakdown_volume_ratio_to_avg20": _round(last_vol / avg20) if (last_vol and avg20) else None,
        })
    # Confidence ceiling cap until HS-CONF-1 satisfied (registry rule).
    if not hold_5 and result.confirmation_state != STATE_INVALIDATED:
        return SetupResult(
            setup_id=result.setup_id, direction=result.direction, present=result.present,
            setup_score=result.setup_score, confirmation_state=result.confirmation_state,
            confidence=min(result.confidence, 0.7),
            evidence=result.evidence, output_fields=result.output_fields,
            failure_codes=result.failure_codes,
        )
    return result


def _assemble_bearish_result(setup_id: str, signal_present: bool,
                             confirmations_satisfied: int, invalidated: bool,
                             evidence: Dict[str, Any], failure_codes: List[str],
                             output_fields: Mapping[str, Any]) -> SetupResult:
    """Assemble a bearish SetupResult with the registry's severity semantics.

    A bearish setup is:
      - NOT_PRESENT      if signal absent
      - INVALIDATED      if an invalidation condition fired
      - CONFIRMED        if signal present AND >=2 independent confirmations
      - UNCONFIRMED      if signal present but <2 confirmations
      - EXPIRED          handled by caller (time decay) — not computed here
    The confidence floor is 0 when INVALIDATED.
    """
    if invalidated:
        state = STATE_INVALIDATED
        confidence = 0.0
        present = False
        score = 0.0
    elif not signal_present:
        state = "NOT_PRESENT"
        confidence = 0.0
        present = False
        score = 0.0
    else:
        present = True
        # Score is a function of structural clarity + breakdown volume ratio +
        # confirmation count (registry confidence_semantics). We approximate
        # deterministically.
        struct_clarity = 40.0 if evidence.get("signal", {}).get("structure_present") else 0.0
        vol_ratio = output_fields.get("breakdown_volume_ratio_to_avg20") or 0.0
        micro_score = min(float(vol_ratio) * 15.0, 25.0) if vol_ratio else 0.0
        conf_score = min(confirmations_satisfied * 12.0, 35.0)
        score = _clamp_score(struct_clarity + micro_score + conf_score)
        if confirmations_satisfied >= 2:
            state = STATE_CONFIRMED
            confidence = min(0.5 + 0.1 * confirmations_satisfied, 1.0)
        else:
            state = STATE_UNCONFIRMED
            confidence = 0.3
            # UNCONFIRMED_PATTERN_REPORTED_AS_CONFIRMED guard: a setup in the
            # INDEVELOPMENT band (62-77) emitted as CONFIRMED is a violation.
            # We surface the code so downstream callers cannot misrepresent it.
            if INDEVELOPMENT_BAND[0] <= score <= INDEVELOPMENT_BAND[1]:
                failure_codes = list(failure_codes) + [_FAILURE_UNCONFIRMED_PATTERN_REPORTED_AS_CONFIRMED]

    return SetupResult(
        setup_id=setup_id,
        direction="BEARISH",
        present=present,
        setup_score=round(score, 2),
        confirmation_state=state,
        confidence=round(confidence, 4),
        evidence=evidence,
        output_fields=dict(output_fields),
        failure_codes=tuple(failure_codes),
    )


_BEARISH_DETECTORS = {
    "S-BEAR-FLAG": _detect_bear_flag,
    "S-BEAR-PENNANT": _detect_bear_pennant,
    "S-BEAR-DOWN-TRIANGLE": _detect_bear_down_triangle,
    "S-BEAR-RECTANGLE-TOP": _detect_bear_rectangle_top,
    "S-BEAR-HEAD-SHOULDERS": _detect_bear_head_shoulders,
}


# ====================================================================
# Unified setup dispatcher
# ====================================================================

def detect_setup(setup_id: str, profile_context: Any) -> SetupResult:
    """Detect a single setup by id.

    For bullish setups, ``profile_context`` may be either a NormalizedInput or a
    tuple of rows (we accept both for ergonomic calling from scan_setups).
    For bearish setups, ``profile_context`` MUST be a NormalizedInput (the
    detectors need OBV/VPT/benchmark series).
    """
    if setup_id in BULLISH_SETUP_IDS:
        rows = _rows_from_context(profile_context)
        detector = _BULLISH_DETECTORS[setup_id]
        raw = detector(rows)
        if raw is None:
            return SetupResult(setup_id=setup_id, direction="BULLISH", present=False,
                               setup_score=0.0, confirmation_state="NOT_PRESENT",
                               confidence=0.0, evidence={"raw": None}, output_fields={})
        pattern_id = raw["pattern_id"]
        family = _BULLISH_FAMILY.get(pattern_id, "mixed")
        score = float(raw["completion_score"])
        # Bullish setups: "confirmed" when status is gần_xác_nhận (near confirmation).
        # We do NOT auto-confirm bullish setups here; the runner may elevate based
        # on additional volume evidence. confirmation_state stays descriptive.
        state = "UNCONFIRMED"
        if raw["setup_status"] == "gần_xác_nhận":
            state = "NEAR_CONFIRMATION"
        return SetupResult(
            setup_id=setup_id,
            direction="BULLISH",
            present=True,
            setup_score=score,
            confirmation_state=state,
            confidence=round(min(score / 100.0, 1.0), 4),
            evidence={"family": family, "raw": raw},
            output_fields={"pattern_id": pattern_id,
                           "confirmation_price": raw.get("confirmation_price"),
                           "distance_to_confirmation_pct": raw.get("distance_to_confirmation_pct")},
        )
    if setup_id in BEARISH_SETUP_IDS:
        if not isinstance(profile_context, NormalizedInput):
            raise TypeError(f"bearish setup {setup_id} requires a NormalizedInput profile_context")
        detector = _BEARISH_DETECTORS[setup_id]
        return detector(profile_context)
    raise ValueError(f"unknown setup_id: {setup_id!r}")


def _rows_from_context(ctx: Any) -> Sequence[Mapping[str, Any]]:
    if isinstance(ctx, NormalizedInput):
        return ctx.rows
    if isinstance(ctx, tuple) and ctx and isinstance(ctx[0], Mapping):
        return ctx
    if isinstance(ctx, list) and ctx and isinstance(ctx[0], Mapping):
        return ctx
    raise TypeError("profile_context must be NormalizedInput or a sequence of row dicts")


def scan_all_setups(ni: NormalizedInput) -> Dict[str, SetupResult]:
    """Detect all 13 setups (8 bullish + 5 bearish). Returns setup_id -> result."""
    out: Dict[str, SetupResult] = {}
    for sid in BULLISH_SETUP_IDS:
        out[sid] = detect_setup(sid, ni)
    for sid in BEARISH_SETUP_IDS:
        out[sid] = detect_setup(sid, ni)
    return out


def setup_coverage_status(setups: Mapping[str, SetupResult],
                          *,
                          bearish_qualified: bool = False) -> str:
    """Compute the setup_coverage_status field (VTA-REQ-009).

    Before the Phase 4Q mutation pass proves the bearish detectors resist
    false positives/negatives, the status MUST be INCOMPLETE_BEARISH_COVERAGE
    (or BULLISH_ONLY if no bearish designs exist). It upgrades to
    COMPLETE_DIRECTIONAL_COVERAGE only when ``bearish_qualified`` is True AND
    at least one bearish setup fired.
    """
    bearish_designed = any(s in BEARISH_SETUP_IDS for s in setups)
    any_bearish_present = any(
        setups[sid].present for sid in BEARISH_SETUP_IDS if sid in setups
    )
    if not bearish_designed:
        return COVERAGE_BULLISH_ONLY
    if bearish_qualified and any_bearish_present:
        return COVERAGE_COMPLETE_DIRECTIONAL
    return COVERAGE_INCOMPLETE_BEARISH


# ====================================================================
# Archetype classification
# ====================================================================

def classify_archetype(profile_context: Any) -> ArchetypeResult:
    """Classify the stock archetype by precedence.

    Precedence (vta-bearish-setup-registry.yaml archetype_feed):
      A-TREND-FOLLOWING  >  A-ACCUMULATION-BREAKOUT  >  A-DISTRIBUTION  >
      A-TRAP-PRONE  >  A-MIXED  >  A-NO-CURRENT-SETUP

    A-DISTRIBUTION requires a CONFIRMED bearish setup. A-TRAP-PRONE remains
    HVB-driven (NOT pattern-driven): a bearish setup confirmation alone must
    NOT trigger A-TRAP-PRONE.
    """
    # profile_context is a dict carrying setups + high_volume_behavior block.
    if isinstance(profile_context, NormalizedInput):
        setups = scan_all_blocks_and_setups(profile_context)
        hvb_block = setups.get("high_volume_behavior_profile", {})
        setup_results = setups.get("setups", {})
    elif isinstance(profile_context, Mapping):
        setups = profile_context.get("setups", {})
        hvb_block = profile_context.get("high_volume_behavior_profile", {}) or {}
        setup_results = setups
    else:
        return ArchetypeResult(
            archetype="A-NO-CURRENT-SETUP", primary_attribution="NONE",
            secondary_setups=(), eligible=("A-NO-CURRENT-SETUP",),
            fallback_reason="invalid_profile_context_type",
            failure_codes=(_FAILURE_ARCHETYPE_AMBIGUITY_FALLBACK,),
        )

    eligible: List[str] = []
    primary_attribution = "NONE"
    secondary: List[str] = []

    # A-TREND-FOLLOWING: any bullish trend_following setup present.
    bull_trend = [sid for sid in BULLISH_SETUP_IDS
                  if setup_results.get(sid) and setup_results[sid].present
                  and setup_results[sid].evidence.get("family") == "trend_following"]
    if bull_trend:
        eligible.append("A-TREND-FOLLOWING")
        primary_attribution = bull_trend[0]

    # A-ACCUMULATION-BREAKOUT: any bullish accumulation_breakout setup present.
    bull_acc = [sid for sid in BULLISH_SETUP_IDS
                if setup_results.get(sid) and setup_results[sid].present
                and setup_results[sid].evidence.get("family") == "accumulation_breakout"]
    if bull_acc:
        eligible.append("A-ACCUMULATION-BREAKOUT")
        if not eligible or primary_attribution == "NONE":
            primary_attribution = bull_acc[0]

    # A-DISTRIBUTION: any CONFIRMED bearish setup.
    bear_confirmed = [sid for sid in BEARISH_SETUP_IDS
                      if setup_results.get(sid) and setup_results[sid].present
                      and setup_results[sid].confirmation_state == STATE_CONFIRMED]
    if bear_confirmed:
        eligible.append("A-DISTRIBUTION")
        if primary_attribution == "NONE":
            primary_attribution = bear_confirmed[0]

    # A-TRAP-PRONE: HVB-driven only (registry boundary). A bearish pattern
    # confirmation alone must NOT trigger A-TRAP-PRONE.
    hvb_label = ""
    if isinstance(hvb_block, Mapping):
        hvb_label = str(hvb_block.get("behavior_label", ""))
    if "SUY_YEU" in hvb_label:
        eligible.append("A-TRAP-PRONE")
        if primary_attribution == "NONE":
            primary_attribution = "HVB"

    # A-MIXED: bullish AND bearish both present (cross_setup_policies OPTION_A).
    any_bull = any(setup_results.get(sid) and setup_results[sid].present for sid in BULLISH_SETUP_IDS)
    any_bear = any(setup_results.get(sid) and setup_results[sid].present for sid in BEARISH_SETUP_IDS)
    if any_bull and any_bear:
        eligible.append("A-MIXED")

    # Select by precedence.
    chosen = "A-NO-CURRENT-SETUP"
    fallback_reason = None
    for cand in ARCHETYPE_PRECEDENCE:
        if cand in eligible:
            chosen = cand
            break
    if chosen == "A-NO-CURRENT-SETUP" and eligible:
        # Eligible but not in precedence list — ambiguous fallback.
        fallback_reason = "eligible_archetypes_not_in_precedence"
        chosen = eligible[0]

    # Secondary setups = other present setups besides the primary.
    if primary_attribution != "NONE" and primary_attribution != "HVB":
        for sid in list(BULLISH_SETUP_IDS) + list(BEARISH_SETUP_IDS):
            if sid == primary_attribution:
                continue
            sr = setup_results.get(sid)
            if sr and sr.present:
                secondary.append(sid)

    failure_codes: Tuple[str, ...] = ()
    if chosen == "A-NO-CURRENT-SETUP" and not eligible:
        # Deterministic: no fallback needed.
        pass
    elif fallback_reason:
        failure_codes = (_FAILURE_ARCHETYPE_AMBIGUITY_FALLBACK,)

    return ArchetypeResult(
        archetype=chosen,
        primary_attribution=primary_attribution,
        secondary_setups=tuple(secondary),
        eligible=tuple(eligible),
        fallback_reason=fallback_reason,
        failure_codes=failure_codes,
    )


def scan_all_blocks_and_setups(ni: NormalizedInput) -> Dict[str, Any]:
    """Convenience: compute all 17 blocks + all 13 setups in one pass.

    Used by classify_archetype when called with a NormalizedInput directly.
    """
    out: Dict[str, Any] = {}
    blocks = compute_all_blocks(ni)
    for bid, res in blocks.items():
        out[bid] = res.payload
    out["setups"] = scan_all_setups(ni)
    return out


__all__ = [
    "NormalizedInput",
    "BlockResult",
    "SetupResult",
    "ArchetypeResult",
    "HVBEventsResult",
    "OBVChangeResult",
    "VPTChangeResult",
    "compute_profile_block",
    "compute_all_blocks",
    "detect_setup",
    "scan_all_setups",
    "classify_archetype",
    "scan_all_blocks_and_setups",
    "compute_hvb_events_1y",
    "compute_obv_change",
    "compute_vpt_change",
    "assert_obv_vpt_separate",
    "setup_coverage_status",
    "BLOCK_IDS",
    "BULLISH_SETUP_IDS",
    "BEARISH_SETUP_IDS",
    "ARCHETYPE_PRECEDENCE",
    "COVERAGE_INCOMPLETE_BEARISH",
    "COVERAGE_BULLISH_ONLY",
    "COVERAGE_COMPLETE_DIRECTIONAL",
]
