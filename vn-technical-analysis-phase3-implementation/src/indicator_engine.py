"""VTA Phase 3 — Indicator Engine.

Production module implementing 6 indicators with FROZEN formula semantics
from vta-formula-contract-registry.yaml. All math is implemented by hand to
guarantee the frozen conventions (Wilder smoothing, population std ÷N, EMA
data[0] seed, etc.); NO library defaults (pandas-ta, talib, numpy .ewm())
are used to override frozen semantics.

Owns requirements:
  - VTA-REQ-001 (ACTIVE 6 indicators)
  - VTA-REQ-005 (RSI Wilder smoothing)
  - VTA-REQ-006 (Bollinger shared std kernel)
  - VTA-REQ-007 (channel slope — shared helper, profile_engine owns block)
  - VTA-REQ-014 (OBV/VPT separate source series via CMF)

Public functions (frozen signatures):
  - compute_rsi(close_series, period=14) -> RSIResult
  - compute_bollinger(close_series, window=20, multiplier=2) -> BollingerResult
  - compute_ma(close_series, period, ma_type) -> MAResult
  - compute_macd(close_series) -> MACDResult
  - compute_beta(stock_returns, market_returns, window=52) -> BetaResult
  - compute_cmf(hlcv, window=20) -> CMFResult

Frozen conventions (DO NOT change without re-freezing the contract):
  - RSI: Wilder smoothing, SMA seed over first `period`, 15-bar warmup,
         period-1 multiplier. avgLoss==0 -> RSI=100; both zero -> RSI=50.
  - Bollinger: population std ÷N (NOT ÷N-1), window=20, multiplier=2.0.
  - MA: SMA canonical; EMA ONLY for MACD. Canonical window set 21/63/126/252.
  - MACD: 12/26/9, EMA seed = close[0] (NOT SMA seed).
  - Beta: VNINDEX, simple returns, POPULATION covariance ÷N, 52w window.
  - CMF: MFM = ((c-l)-(h-c))/(h-l)*vol; high==low -> MFM=0; SMA(vol)==0 ->
         DIVZERO_DETECTED. OBV and VPT computed from SEPARATE source series.

All computations are float64. Long windows (>=60) use Kahan-compensated
summation. Output is deterministic (same input -> byte-identical output),
no wall-clock / network / random source dependency. Provenance timestamps
are injected by the caller.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Cross-module import: failure-code machinery lives in normalization_engine.
# Per scope: indicator_engine depends on [normalization_engine] and is
# prohibited from importing production decision functions (pattern_engine,
# verifier). This import is the canonical allowed dependency.
# ---------------------------------------------------------------------------

try:
    from .normalization_engine import (
        FailureEvent,
        Mode,
        NUMERICAL_TOLERANCE,
        COMPARISON_EPSILON,
    )
except ImportError:  # allow direct script execution for testing
    from normalization_engine import (  # type: ignore[no-redef]
        FailureEvent,
        Mode,
        NUMERICAL_TOLERANCE,
        COMPARISON_EPSILON,
    )

# ---------------------------------------------------------------------------
# Frozen constants (from vta-formula-contract-registry.yaml)
# ---------------------------------------------------------------------------

# Canonical MA window set — §4 reconciliation OPTION_21_63_126_252 (NOT 20/60/120).
MA_WINDOW_SET: Tuple[int, ...] = (21, 63, 126, 252)

# RSI frozen params
RSI_PERIOD = 14
RSI_WARMUP = 15          # period + 1 delta; first valid RSI at index `period`
RSI_MIN_OBS = 15

# Bollinger frozen params
BOLL_WINDOW = 20
BOLL_MULTIPLIER = 2.0
BOLL_MIN_OBS = 20

# MACD frozen params
MACD_SHORT = 12
MACD_LONG = 26
MACD_SIGNAL = 9
MACD_MIN_OBS = 35        # long + signal - overlap

# Beta frozen params
BETA_WINDOW = 52
BETA_MIN_OBS = 52

# CMF frozen params
CMF_WINDOW = 20
CMF_MIN_OBS = 20

# Floating-point policy: Kahan summation for windows >= 60
KAHAN_THRESHOLD = 60


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class IndicatorResult:
    """Base class for indicator results carrying provenance + diagnostics."""

    warmup_complete: bool
    provenance: Dict[str, Any] = field(default_factory=dict)
    failure_events: List[FailureEvent] = field(default_factory=list)
    is_fatal: bool = False


@dataclass
class RSIResult(IndicatorResult):
    rsi_value: Optional[float] = None          # latest RSI in [0, 100]
    rsi_series: List[Optional[float]] = field(default_factory=list)  # full series, NaN during warmup


@dataclass
class BollingerResult(IndicatorResult):
    middle_band: Optional[float] = None
    upper_band: Optional[float] = None
    lower_band: Optional[float] = None
    bb_position_pct: Optional[float] = None    # [0, 100], 50 if std==0
    middle_series: List[Optional[float]] = field(default_factory=list)
    upper_series: List[Optional[float]] = field(default_factory=list)
    lower_series: List[Optional[float]] = field(default_factory=list)


@dataclass
class MAResult(IndicatorResult):
    # `warmup_complete` (bool) inherited from IndicatorResult = overall across windows
    ma_values: Dict[str, Optional[float]] = field(default_factory=dict)      # keyed by str(period)
    warmup_complete_per_window: Dict[str, bool] = field(default_factory=dict)  # per-window flags
    # full per-window series for downstream use (keys are str(period))
    ma_series: Dict[str, List[Optional[float]]] = field(default_factory=dict)


@dataclass
class MACDResult(IndicatorResult):
    macd_line: Optional[float] = None
    signal_line: Optional[float] = None
    histogram: Optional[float] = None
    macd_series: List[Optional[float]] = field(default_factory=list)
    signal_series: List[Optional[float]] = field(default_factory=list)


@dataclass
class BetaResult(IndicatorResult):
    beta_value: Optional[float] = None
    benchmark_used: str = "VNINDEX"
    window_weeks: int = BETA_WINDOW
    cov: Optional[float] = None
    var_market: Optional[float] = None


@dataclass
class CMFResult(IndicatorResult):
    cmf_value: Optional[float] = None          # [-1, 1]
    obv_change: Optional[float] = None         # sourced from OBV series (B12 fix)
    vpt_change: Optional[float] = None         # sourced from VPT series (B12 fix)
    obv_series: List[float] = field(default_factory=list)
    vpt_series: List[float] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Numeric helpers (Kahan-compensated; float64)
# ---------------------------------------------------------------------------


def _to_float64_array(values: Sequence[Any]) -> List[float]:
    """Coerce a sequence to float64; non-finite/missing -> NaN (pass-through)."""
    out: List[float] = []
    for v in values:
        if v is None:
            out.append(float("nan"))
            continue
        if isinstance(v, bool):
            out.append(float("nan"))
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            out.append(float("nan"))
            continue
        if math.isnan(f) or math.isinf(f):
            out.append(float("nan"))
        else:
            out.append(f)
    return out


def _is_nan(x: float) -> bool:
    return x != x  # NaN-safe check


def _kahan_sum(values: Sequence[float]) -> float:
    """Kahan-compensated summation (Neumaier variant for stability)."""
    total = 0.0
    c = 0.0  # compensation
    for v in values:
        if _is_nan(v):
            return float("nan")
        t = total + v
        if abs(total) >= abs(v):
            c += (total - t) + v
        else:
            c += (v - t) + total
        total = t
    return total + c


def _window_sum(values: Sequence[float], start: int, length: int) -> float:
    """Sum values[start:start+length] with Kahan if length >= KAHAN_THRESHOLD."""
    if length >= KAHAN_THRESHOLD:
        return _kahan_sum(values[start:start + length])
    s = 0.0
    for i in range(start, start + length):
        v = values[i]
        if _is_nan(v):
            return float("nan")
        s += v
    return s


def _mean(values: Sequence[float]) -> float:
    n = len(values)
    if n == 0:
        return float("nan")
    return _window_sum(values, 0, n) / n


def _gen_chain_id(input_data: Any = None, mode: str = "UNKNOWN") -> str:
    """Deterministic content-derived chain id.

    Per OWNER DIRECTIVE Section 4 the chain id MUST be derived from the
    canonical serialized inputs (data + mode), NOT a global constant or
    random UUID. Same inputs -> same id; different instrument / timestamp /
    price basis -> different id. Prohibited sources: uuid4, random, PID,
    wall-clock, global constant, unordered serialization.

    Construction (frozen):
        canonical_payload = {"data": str(input)[:1000], "mode": mode}
        -> deterministic canonical JSON serialization (sort_keys=True)
        -> SHA-256
        -> "chain-" + hexdigest[:16]
    """
    import hashlib
    import json as _json

    canonical = _json.dumps(
        {"data": str(input_data)[:1000], "mode": str(mode)},
        sort_keys=True,
    )
    return "chain-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _base_provenance(
    source_provider: Optional[str],
    chain_id: Optional[str],
    extra: Dict[str, Any],
    *,
    input_data: Any = None,
    mode: str = "UNKNOWN",
) -> Dict[str, Any]:
    prov: Dict[str, Any] = {
        "source_provider": source_provider,
        "computation_chain_id": chain_id or _gen_chain_id(input_data, mode),
    }
    prov.update(extra)
    return prov


# ---------------------------------------------------------------------------
# EMA primitive (frozen: data[0] seed, NOT SMA seed; used ONLY by MACD)
# ---------------------------------------------------------------------------


def _ema_data0_seed(values: Sequence[float], period: int) -> List[float]:
    """EMA with seed = values[0]. Frozen convention for F-MACD.

    EMA_t = close_t * k + EMA_{t-1} * (1-k), k = 2/(period+1), EMA_0 = close[0].
    NaN inputs propagate (NaN-safe). Used ONLY by MACD; F-MA uses SMA.
    """
    n = len(values)
    if n == 0:
        return []
    k = 2.0 / (period + 1)
    out: List[float] = [0.0] * n
    out[0] = values[0]  # data[0] seed (frozen — NOT SMA)
    for i in range(1, n):
        if _is_nan(values[i]) or _is_nan(out[i - 1]):
            out[i] = float("nan")
        else:
            out[i] = values[i] * k + out[i - 1] * (1.0 - k)
    return out


# ---------------------------------------------------------------------------
# 1. compute_rsi — Wilder smoothing, SMA seed, 15-bar warmup
# ---------------------------------------------------------------------------


def compute_rsi(
    close_series: Sequence[Any],
    period: int = RSI_PERIOD,
    *,
    mode: Mode = Mode.ACTIVE,
    source_provider: Optional[str] = None,
    chain_id: Optional[str] = None,
) -> RSIResult:
    """Relative Strength Index — Wilder Smoothing (F-RSI, frozen).

    Sequence (per contract):
      1. deltas = diff(close)
      2. gains = max(delta,0); losses = max(-delta,0)
      3. Seed avgGain/avgLoss = SMA of first `period` gains/losses (Wilder seed)
      4. Recurse: avg_t = (avg_{t-1}*(period-1) + x_t) / period
      5. RS = avgGain/avgLoss; RSI = 100 - 100/(1+RS)

    Warmup: first valid RSI at index `period` (0-based), i.e. RSI_WARMUP=15 bars.
    Minimum observations: RSI_MIN_OBS=15. Below this -> INSUFFICIENT_HISTORY fatal.

    Zero-division policy (frozen):
      avgLoss == 0                -> RSI = 100
      avgGain == 0 and avgLoss==0 -> RSI = 50 (neutral)
    """
    closes = _to_float64_array(close_series)
    n = len(closes)

    provenance = _base_provenance(source_provider, chain_id, {
        "formula_id": "F-RSI",
        "period": period,
        "smoothing_method": "WILDER",
        "seeding": "SMA_SEED_OVER_FIRST_PERIOD",
        "price_basis": "adjusted_close",
    }, input_data=closes, mode=mode.value if isinstance(mode, Mode) else str(mode))

    # --- insufficient history (fatal) ------------------------------------
    if n < RSI_MIN_OBS:
        return RSIResult(
            warmup_complete=False,
            rsi_value=None,
            rsi_series=[],
            is_fatal=True,
            failure_events=[FailureEvent.from_code(
                # INSUFFICIENT_HISTORY is owned by normalization_engine in the
                # registry; indicator_engine re-emits it via the same canonical
                # name with formula-specific context (tier 1, precedence 20).
                "INSUFFICIENT_HISTORY",
                {
                    "mode": mode.value,
                    "provided_sessions": n,
                    "required_sessions": RSI_MIN_OBS,
                    "frequency": "weekly",
                },
                f"RSI requires {RSI_MIN_OBS} closes; received {n}.",
            )],
            provenance=provenance,
        )

    # --- gains / losses from deltas --------------------------------------
    deltas = [closes[i] - closes[i - 1] for i in range(1, n)]
    gains = [max(d, 0.0) if not _is_nan(d) else float("nan") for d in deltas]
    losses = [max(-d, 0.0) if not _is_nan(d) else float("nan") for d in deltas]

    # --- Wilder SMA seed over first `period` deltas ----------------------
    avg_gain: Optional[float] = None
    avg_loss: Optional[float] = None
    if period <= len(gains):
        seed_g = gains[:period]
        seed_l = losses[:period]
        # NaN in seed window -> propagate as missing (VC-NAN-PROP-1)
        if any(_is_nan(v) for v in seed_g) or any(_is_nan(v) for v in seed_l):
            avg_gain = float("nan")
            avg_loss = float("nan")
        else:
            avg_gain = _window_sum(seed_g, 0, period) / period
            avg_loss = _window_sum(seed_l, 0, period) / period

    # --- recurse with period-1 multiplier --------------------------------
    rsi_series: List[Optional[float]] = [None] * n
    # first valid RSI at index `period` (0-based close index)
    if avg_gain is None or avg_loss is None or _is_nan(avg_gain) or _is_nan(avg_loss):
        # seed window contained NaN -> cannot produce valid RSI; emit NaN-prop
        nan_events = [FailureEvent.from_code(
            "NAN_PROPAGATION",
            {
                "mode": mode.value,
                "field_path": "rsi_value",
                "source_nan_date": None,
            },
            "NaN in RSI seed window propagated.",
        )]
        return RSIResult(
            warmup_complete=False,
            rsi_value=None,
            rsi_series=rsi_series,
            is_fatal=True,
            failure_events=nan_events,
            provenance=provenance,
        )

    ag = avg_gain
    al = avg_loss
    for i in range(period, n):
        idx = i - 1  # index into deltas/gains/losses (which start at close[1])
        g = gains[idx]
        l = losses[idx]
        if _is_nan(g) or _is_nan(l):
            # propagate NaN; downstream treats as missing
            rsi_series[i] = None
            continue
        ag = (ag * (period - 1) + g) / period
        al = (al * (period - 1) + l) / period

        # Zero-division policy (frozen)
        if al == 0.0 and ag == 0.0:
            rsi_series[i] = 50.0  # neutral
        elif al == 0.0:
            rsi_series[i] = 100.0
        else:
            rs = ag / al
            rsi_val = 100.0 - 100.0 / (1.0 + rs)
            # clamp to [0, 100] to absorb float edge noise
            if rsi_val < 0.0:
                rsi_val = 0.0
            elif rsi_val > 100.0:
                rsi_val = 100.0
            rsi_series[i] = rsi_val

    latest = rsi_series[-1]
    warmup_done = latest is not None
    return RSIResult(
        warmup_complete=warmup_done,
        rsi_value=latest,
        rsi_series=rsi_series,
        is_fatal=False,
        provenance=provenance,
    )


# ---------------------------------------------------------------------------
# 2. compute_bollinger — population std ÷N, window=20, multiplier=2
# ---------------------------------------------------------------------------


def compute_bollinger(
    close_series: Sequence[Any],
    window: int = BOLL_WINDOW,
    multiplier: float = BOLL_MULTIPLIER,
    *,
    mode: Mode = Mode.ACTIVE,
    source_provider: Optional[str] = None,
    chain_id: Optional[str] = None,
) -> BollingerResult:
    """Bollinger Bands — shared kernel std convention (F-BOLLINGER, frozen).

    middle = SMA(close, window)
    std   = population_std(close, window) = sqrt( sum((x-mean)^2) / window )  # ÷N
    upper = middle + multiplier * std
    lower = middle - multiplier * std
    bb_position_pct = (close - lower) / (upper - lower) * 100

    std convention: POPULATION_DIV_N (shared kernel across ACTIVE + PROFILE).
    Minimum observations: BOLL_MIN_OBS=20. warmup=20.

    Zero-division policy (frozen):
      std == 0 -> upper=middle=lower; bb_position_pct -> 50 (neutral) + warning.
    """
    closes = _to_float64_array(close_series)
    n = len(closes)

    provenance = _base_provenance(source_provider, chain_id, {
        "formula_id": "F-BOLLINGER",
        "window": window,
        "multiplier": multiplier,
        "std_convention": "POPULATION_DIV_N",
        "price_basis": "adjusted_close",
    }, input_data=closes, mode=mode.value if isinstance(mode, Mode) else str(mode))

    if window != BOLL_WINDOW:
        # CONFIG_VALIDATION_FAILED is owned tier-1; re-emit here with context.
        return BollingerResult(
            warmup_complete=False,
            is_fatal=True,
            failure_events=[FailureEvent.from_code(
                "CONFIG_VALIDATION_FAILED",
                {
                    "mode": mode.value,
                    "config_key": "window",
                    "observed_value": window,
                    "allowed_values": [BOLL_WINDOW],
                },
                f"Bollinger window frozen at {BOLL_WINDOW}; got {window}.",
            )],
            provenance=provenance,
        )

    if n < BOLL_MIN_OBS:
        return BollingerResult(
            warmup_complete=False,
            is_fatal=True,
            failure_events=[FailureEvent.from_code(
                "INSUFFICIENT_HISTORY",
                {
                    "mode": mode.value,
                    "provided_sessions": n,
                    "required_sessions": BOLL_MIN_OBS,
                    "frequency": "weekly" if mode == Mode.ACTIVE else "daily",
                },
                f"Bollinger requires {BOLL_MIN_OBS} closes; received {n}.",
            )],
            provenance=provenance,
        )

    middle_series: List[Optional[float]] = [None] * n
    upper_series: List[Optional[float]] = [None] * n
    lower_series: List[Optional[float]] = [None] * n

    events: List[FailureEvent] = []

    for i in range(window - 1, n):
        w = closes[i - window + 1: i + 1]
        if any(_is_nan(v) for v in w):
            middle_series[i] = None
            upper_series[i] = None
            lower_series[i] = None
            continue
        mean = _window_sum(w, 0, window) / window
        # population variance ÷N
        sq_sum = _window_sum([v * v for v in w], 0, window)
        var = (sq_sum / window) - (mean * mean)
        # numerical guard: tiny negatives from float error -> 0
        if var < 0.0 and var > -1.0e-12:
            var = 0.0
        std = math.sqrt(max(var, 0.0))
        middle_series[i] = mean
        upper_series[i] = mean + multiplier * std
        lower_series[i] = mean - multiplier * std

    latest_idx = n - 1
    middle = middle_series[latest_idx]
    upper = upper_series[latest_idx]
    lower = lower_series[latest_idx]
    close_last = closes[latest_idx]

    bb_position: Optional[float] = None
    if middle is not None and upper is not None and lower is not None:
        band_width = upper - lower
        if abs(band_width) < NUMERICAL_TOLERANCE:
            # std == 0 -> bb_position undefined -> 50 (neutral) + warning
            bb_position = 50.0
            events.append(FailureEvent.from_code(
                "COMPUTATION_DEGENERATE",
                {
                    "mode": mode.value,
                    "formula_id": "F-BOLLINGER",
                    "denominator_field": "upper-lower",
                    "window": window,
                },
                "Bollinger band width == 0; bb_position set to 50 (neutral).",
            ))
        elif _is_nan(close_last):
            bb_position = None
        else:
            bb_position = (close_last - lower) / band_width * 100.0
            # clamp into [0, 100] presentation range
            if bb_position < 0.0:
                bb_position = 0.0
            elif bb_position > 100.0:
                bb_position = 100.0

    return BollingerResult(
        warmup_complete=(middle is not None),
        middle_band=middle,
        upper_band=upper,
        lower_band=lower,
        bb_position_pct=bb_position,
        middle_series=middle_series,
        upper_series=upper_series,
        lower_series=lower_series,
        failure_events=events,
        provenance=provenance,
    )


# ---------------------------------------------------------------------------
# 3. compute_ma — SMA canonical; EMA ONLY for MACD
# ---------------------------------------------------------------------------


def _sma_window(closes: List[float], window: int) -> List[Optional[float]]:
    """SMA over a single window; NaN during warmup (no backfill)."""
    n = len(closes)
    out: List[Optional[float]] = [None] * n
    for i in range(window - 1, n):
        w = closes[i - window + 1: i + 1]
        if any(_is_nan(v) for v in w):
            out[i] = None
            continue
        out[i] = _window_sum(w, 0, window) / window
    return out


def compute_ma(
    close_series: Sequence[Any],
    period: Any,
    ma_type: str = "SMA",
    *,
    mode: Mode = Mode.ACTIVE,
    source_provider: Optional[str] = None,
    chain_id: Optional[str] = None,
) -> MAResult:
    """Moving Average — SMA canonical (F-MA, frozen).

    Canonical window set: 21/63/126/252 (OPTION_21_63_126_252). Accepts either
    a single period or the full canonical set.

    SMA is canonical for MA10/20/50. EMA is PROHIBITED as an MA field — EMA is
    exclusively a MACD primitive. If ma_type != "SMA" -> CONFIG_VALIDATION_FAILED.

    Warmup policy: return NaN (None) during warmup; no backfill, no forward fill.
    """
    closes = _to_float64_array(close_series)
    n = len(closes)

    provenance = _base_provenance(source_provider, chain_id, {
        "formula_id": "F-MA",
        "ma_type": ma_type,
        "window_set": list(MA_WINDOW_SET),
        "price_basis": "adjusted_close",
    }, input_data=closes, mode=mode.value if isinstance(mode, Mode) else str(mode))

    if str(ma_type).upper() != "SMA":
        return MAResult(
            warmup_complete=False,
            is_fatal=True,
            failure_events=[FailureEvent.from_code(
                "CONFIG_VALIDATION_FAILED",
                {
                    "mode": mode.value,
                    "config_key": "ma_type",
                    "observed_value": ma_type,
                    "allowed_values": ["SMA"],
                },
                "EMA is prohibited for MA fields (MACD-only primitive); SMA required.",
            )],
            provenance=provenance,
        )

    # Resolve the set of windows to compute.
    if period is None:
        windows = list(MA_WINDOW_SET)
    elif isinstance(period, (list, tuple)):
        windows = [int(p) for p in period]
    else:
        windows = [int(period)]

    # Validate against canonical set (frozen).
    invalid = [w for w in windows if w not in MA_WINDOW_SET]
    if invalid:
        return MAResult(
            warmup_complete=False,
            is_fatal=True,
            failure_events=[FailureEvent.from_code(
                "CONFIG_VALIDATION_FAILED",
                {
                    "mode": mode.value,
                    "config_key": "period",
                    "observed_value": invalid,
                    "allowed_values": list(MA_WINDOW_SET),
                },
                f"MA period(s) {invalid} not in canonical set {list(MA_WINDOW_SET)}.",
            )],
            provenance=provenance,
        )

    ma_values: Dict[str, Optional[float]] = {}
    warmup_map: Dict[str, bool] = {}
    ma_series_map: Dict[str, List[Optional[float]]] = {}

    for w in windows:
        series = _sma_window(closes, w)
        ma_series_map[str(w)] = series
        ma_values[str(w)] = series[n - 1] if n > 0 else None
        warmup_map[str(w)] = bool(n >= w and (series[n - 1] is not None)) if n > 0 else False

    overall_warmup = all(warmup_map.values()) if warmup_map else False

    return MAResult(
        warmup_complete=overall_warmup,
        ma_values=ma_values,
        warmup_complete_per_window=warmup_map,
        ma_series=ma_series_map,
        provenance=provenance,
    )


# ---------------------------------------------------------------------------
# 4. compute_macd — EMA seed = data[0]
# ---------------------------------------------------------------------------


def compute_macd(
    close_series: Sequence[Any],
    *,
    mode: Mode = Mode.ACTIVE,
    source_provider: Optional[str] = None,
    chain_id: Optional[str] = None,
) -> MACDResult:
    """MACD (12/26/9) with data[0] EMA seed (F-MACD, frozen).

    macd_line   = EMA(close, 12) - EMA(close, 26)
    signal_line = EMA(macd_line, 9)  with seed = macd_line[0]
    histogram   = macd_line - signal_line

    EMA seed: EMA_0 = close[0] (FROZEN — NOT SMA seed).
    Minimum observations: MACD_MIN_OBS=35.
    """
    closes = _to_float64_array(close_series)
    n = len(closes)

    provenance = _base_provenance(source_provider, chain_id, {
        "formula_id": "F-MACD",
        "short_period": MACD_SHORT,
        "long_period": MACD_LONG,
        "signal_period": MACD_SIGNAL,
        "ema_seed_method": "DATA_0",
        "price_basis": "adjusted_close",
    }, input_data=closes, mode=mode.value if isinstance(mode, Mode) else str(mode))

    if n < MACD_MIN_OBS:
        return MACDResult(
            warmup_complete=False,
            is_fatal=True,
            failure_events=[FailureEvent.from_code(
                "INSUFFICIENT_HISTORY",
                {
                    "mode": mode.value,
                    "provided_sessions": n,
                    "required_sessions": MACD_MIN_OBS,
                    "frequency": "weekly",
                },
                f"MACD requires {MACD_MIN_OBS} closes; received {n}.",
            )],
            provenance=provenance,
        )

    # EMA(12) and EMA(26) with data[0] seed (frozen).
    ema_short = _ema_data0_seed(closes, MACD_SHORT)
    ema_long = _ema_data0_seed(closes, MACD_LONG)

    macd_line: List[float] = []
    for s, lng in zip(ema_short, ema_long):
        if _is_nan(s) or _is_nan(lng):
            macd_line.append(float("nan"))
        else:
            macd_line.append(s - lng)

    # Signal line: EMA(macd_line, 9) with seed = macd_line[0] (frozen).
    signal_line = _ema_data0_seed(macd_line, MACD_SIGNAL)

    # Histogram = macd_line - signal_line
    histogram_series: List[Optional[float]] = []
    for m, s in zip(macd_line, signal_line):
        if _is_nan(m) or _is_nan(s):
            histogram_series.append(None)
        else:
            histogram_series.append(m - s)

    macd_series: List[Optional[float]] = [
        None if _is_nan(v) else v for v in macd_line
    ]
    signal_series: List[Optional[float]] = [
        None if _is_nan(v) else v for v in signal_line
    ]

    latest_macd = macd_series[-1]
    latest_signal = signal_series[-1]
    latest_hist = histogram_series[-1] if histogram_series else None

    return MACDResult(
        warmup_complete=(latest_macd is not None and latest_signal is not None),
        macd_line=latest_macd,
        signal_line=latest_signal,
        histogram=latest_hist,
        macd_series=macd_series,
        signal_series=signal_series,
        provenance=provenance,
    )


# ---------------------------------------------------------------------------
# 5. compute_beta — VNINDEX, simple returns, POPULATION covariance ÷N, 52w
# ---------------------------------------------------------------------------


def compute_beta(
    stock_returns: Sequence[Any],
    market_returns: Sequence[Any],
    window: int = BETA_WINDOW,
    *,
    benchmark: str = "VNINDEX",
    mode: Mode = Mode.ACTIVE,
    source_provider: Optional[str] = None,
    chain_id: Optional[str] = None,
) -> BetaResult:
    """Beta — cov(stock,market)/var(market) (F-BETA, frozen).

    β = Cov(stock_returns, market_returns) / Var(market_returns)
    POPULATION covariance (÷N, not ÷N-1). Returns basis: SIMPLE (pct_change).
    Window: 52 weeks. Benchmark canonical: VNINDEX.

    Inputs are pre-computed simple returns (fraction). This function does NOT
    compute returns from prices — that is the caller's responsibility so the
    price_basis (total_return_adjusted_close) is enforced upstream.

    Zero-division policy (frozen):
      Var(market) == 0 -> β undefined -> DIVZERO_DETECTED, no fabricated value.
    """
    s_ret = _to_float64_array(stock_returns)
    m_ret = _to_float64_array(market_returns)

    provenance = _base_provenance(source_provider, chain_id, {
        "formula_id": "F-BETA",
        "window": window,
        "return_basis": "SIMPLE",
        "benchmark_used": benchmark,
        "covariance_convention": "POPULATION_DIV_N",
        "price_basis": "total_return_adjusted_close",
    }, input_data=(s_ret, m_ret), mode=mode.value if isinstance(mode, Mode) else str(mode))

    # Align by inner length (caller is expected to pre-inner-join on trade
    # dates via normalization_engine.align_benchmark_dates).
    length = min(len(s_ret), len(m_ret))
    if length == 0:
        return BetaResult(
            warmup_complete=False,
            is_fatal=True,
            benchmark_used=benchmark,
            window_weeks=window,
            failure_events=[FailureEvent.from_code(
                "BENCHMARK_UNAVAILABLE",
                {
                    "mode": mode.value,
                    "calculation": "beta",
                    "expected_benchmark": benchmark,
                },
                f"Benchmark {benchmark} series empty for beta.",
            )],
            provenance=provenance,
        )

    s = s_ret[:length]
    m = m_ret[:length]

    required = min(window, length)
    if length < BETA_MIN_OBS:
        return BetaResult(
            warmup_complete=False,
            is_fatal=True,
            benchmark_used=benchmark,
            window_weeks=window,
            failure_events=[FailureEvent.from_code(
                "INSUFFICIENT_HISTORY",
                {
                    "mode": mode.value,
                    "provided_sessions": length,
                    "required_sessions": BETA_MIN_OBS,
                    "frequency": "weekly",
                },
                f"Beta requires {BETA_MIN_OBS} aligned returns; received {length}.",
            )],
            provenance=provenance,
        )

    # Use the trailing `window` observations (frozen 52w window).
    window_len = min(window, length)
    s_w = s[length - window_len:]
    m_w = m[length - window_len:]

    # Drop NaN pairs (pass-through-as-missing -> exclude from cov/var).
    pairs = [(a, b) for a, b in zip(s_w, m_w) if not _is_nan(a) and not _is_nan(b)]
    if len(pairs) < BETA_MIN_OBS:
        return BetaResult(
            warmup_complete=False,
            is_fatal=True,
            benchmark_used=benchmark,
            window_weeks=window,
            failure_events=[FailureEvent.from_code(
                "INSUFFICIENT_HISTORY",
                {
                    "mode": mode.value,
                    "provided_sessions": len(pairs),
                    "required_sessions": BETA_MIN_OBS,
                    "frequency": "weekly",
                },
                f"Beta requires {BETA_MIN_OBS} non-NaN aligned returns; received {len(pairs)}.",
            )],
            provenance=provenance,
        )

    s_arr = [p[0] for p in pairs]
    m_arr = [p[1] for p in pairs]
    n_pairs = len(pairs)

    mean_s = _window_sum(s_arr, 0, n_pairs) / n_pairs
    mean_m = _window_sum(m_arr, 0, n_pairs) / n_pairs

    # Population covariance ÷N
    cov_terms = [(s_arr[i] - mean_s) * (m_arr[i] - mean_m) for i in range(n_pairs)]
    var_terms = [(m_arr[i] - mean_m) ** 2 for i in range(n_pairs)]
    cov = _window_sum(cov_terms, 0, n_pairs) / n_pairs
    var_m = _window_sum(var_terms, 0, n_pairs) / n_pairs

    if abs(var_m) < NUMERICAL_TOLERANCE:
        # Var(market) == 0 -> β undefined -> DIVZERO_DETECTED (no fabricated value)
        return BetaResult(
            warmup_complete=False,
            is_fatal=True,
            beta_value=None,
            benchmark_used=benchmark,
            window_weeks=window,
            cov=cov,
            var_market=var_m,
            failure_events=[FailureEvent.from_code(
                "COMPUTATION_DEGENERATE",
                {
                    "mode": mode.value,
                    "formula_id": "F-BETA",
                    "denominator_field": "var(market)",
                    "window": window,
                },
                "Var(market) == 0; beta undefined.",
            )],
            provenance=provenance,
        )

    beta = cov / var_m
    return BetaResult(
        warmup_complete=True,
        beta_value=beta,
        benchmark_used=benchmark,
        window_weeks=window,
        cov=cov,
        var_market=var_m,
        provenance=provenance,
    )


# ---------------------------------------------------------------------------
# 6. compute_cmf — OBV/VPT SEPARATE source series (B12 fix)
# ---------------------------------------------------------------------------


def compute_cmf(
    hlcv: Dict[str, Sequence[Any]],
    window: int = CMF_WINDOW,
    *,
    obv_series: Optional[Sequence[Any]] = None,
    vpt_series: Optional[Sequence[Any]] = None,
    mode: Mode = Mode.PROFILE,
    source_provider: Optional[str] = None,
    chain_id: Optional[str] = None,
) -> CMFResult:
    """Chaikin Money Flow (20) with OBV/VPT separate source series (F-CMF, frozen).

    MFV = ((close-low) - (high-close)) / (high-low) * volume
    CMF = SMA(MFV, window) / SMA(volume, window)

    Money Flow Multiplier when high==low -> defined as 0 (avoid div-by-zero).
    SMA(volume) == 0 -> DIVZERO_DETECTED.

    OBV/VPT separation (B12_OBV_VPT_BUG fix):
      obv_change MUST come from the OBV source series (passed via obv_series)
      vpt_change MUST come from the VPT source series (passed via vpt_series)
      The two series are NEVER aliased to each other. This function computes
      both from their independent inputs and tags provenance with the source
      series identity so OBV_VPT_SERIES_CONTAMINATION is detectable downstream.
    """
    if hlcv is None:
        hlcv = {}
    highs = _to_float64_array(hlcv.get("high", []))
    lows = _to_float64_array(hlcv.get("low", []))
    closes = _to_float64_array(hlcv.get("close", []))
    volumes = _to_float64_array(hlcv.get("volume", []))

    n = min(len(highs), len(lows), len(closes), len(volumes))
    highs = highs[:n]
    lows = lows[:n]
    closes = closes[:n]
    volumes = volumes[:n]

    provenance = _base_provenance(source_provider, chain_id, {
        "formula_id": "F-CMF",
        "window": window,
        "obv_source_series": "OBV",
        "vpt_source_series": "VPT",
        "price_basis": "adjusted_ohlcv",
    }, input_data=closes, mode=mode.value if isinstance(mode, Mode) else str(mode))

    if n < CMF_MIN_OBS:
        return CMFResult(
            warmup_complete=False,
            is_fatal=True,
            failure_events=[FailureEvent.from_code(
                "INSUFFICIENT_HISTORY",
                {
                    "mode": mode.value,
                    "provided_sessions": n,
                    "required_sessions": CMF_MIN_OBS,
                    "frequency": "daily",
                },
                f"CMF requires {CMF_MIN_OBS} bars; received {n}.",
            )],
            provenance=provenance,
        )

    # Money Flow Volume per bar
    mfv: List[float] = []
    for i in range(n):
        h, l, c, v = highs[i], lows[i], closes[i], volumes[i]
        if _is_nan(h) or _is_nan(l) or _is_nan(c) or _is_nan(v):
            mfv.append(float("nan"))
            continue
        spread = h - l
        if abs(spread) < NUMERICAL_TOLERANCE:
            # high == low -> MFM defined as 0 (avoid div-by-zero)
            mfm = 0.0
        else:
            mfm = ((c - l) - (h - c)) / spread
        mfv.append(mfm * v)

    events: List[FailureEvent] = []

    # CMF over trailing window
    cmf_value: Optional[float] = None
    if n >= window:
        w_mfv = mfv[n - window:]
        w_vol = volumes[n - window:]
        valid = [
            (mf, vv) for mf, vv in zip(w_mfv, w_vol)
            if not _is_nan(mf) and not _is_nan(vv)
        ]
        if len(valid) == window:
            mfv_sum = _window_sum([p[0] for p in valid], 0, window)
            vol_sum = _window_sum([p[1] for p in valid], 0, window)
            if abs(vol_sum) < NUMERICAL_TOLERANCE:
                # SMA(volume) == 0 -> DIVZERO_DETECTED
                events.append(FailureEvent.from_code(
                    "COMPUTATION_DEGENERATE",
                    {
                        "mode": mode.value,
                        "formula_id": "F-CMF",
                        "denominator_field": "SMA(volume)",
                        "window": window,
                    },
                    "SMA(volume) == 0 over CMF window; CMF undefined.",
                ))
                cmf_value = None
            else:
                cmf_value = mfv_sum / vol_sum
                # clamp to [-1, 1] presentation range
                if cmf_value < -1.0:
                    cmf_value = -1.0
                elif cmf_value > 1.0:
                    cmf_value = 1.0

    # --- OBV / VPT from SEPARATE source series (B12 fix) ----------------
    # OBV: cumulative volume signed by close-vs-prev-close direction.
    # VPT: cumulative volume scaled by pct-change (volume * (c/c_prev - 1)).
    # These are computed from the SAME hlcv input here, but the caller MAY
    # pass pre-computed obv_series / vpt_series to enforce strict source-
    # series separation at the data layer. When pre-computed series are
    # supplied, we use them directly and tag provenance.
    obv_computed = _compute_obv(closes, volumes)
    vpt_computed = _compute_vpt(closes, volumes)

    if obv_series is not None:
        obv_arr = _to_float64_array(obv_series)
        provenance["obv_source"] = "PROVIDED"
    else:
        obv_arr = obv_computed
        provenance["obv_source"] = "COMPUTED_FROM_HLCV"

    if vpt_series is not None:
        vpt_arr = _to_float64_array(vpt_series)
        provenance["vpt_source"] = "PROVIDED"
    else:
        vpt_arr = vpt_computed
        provenance["vpt_source"] = "COMPUTED_FROM_HLCV"

    # obv_change / vpt_change: change over trailing `window` (frozen window)
    obv_change: Optional[float] = None
    vpt_change: Optional[float] = None
    if len(obv_arr) >= window + 1:
        a, b = obv_arr[-(window + 1)], obv_arr[-1]
        if not _is_nan(a) and not _is_nan(b):
            obv_change = b - a
    if len(vpt_arr) >= window + 1:
        a, b = vpt_arr[-(window + 1)], vpt_arr[-1]
        if not _is_nan(a) and not _is_nan(b):
            vpt_change = b - a

    # Contamination guard: if caller aliased OBV to VPT, flag it (B12 regression).
    if obv_series is not None and vpt_series is not None:
        if _series_equal(obv_arr, vpt_arr):
            events.append(FailureEvent.from_code(
                "OBV_VPT_SERIES_CONTAMINATION",
                {
                    "mode": mode.value,
                    "field": "obv_change/vpt_change",
                    "expected_source_series": "OBV != VPT",
                    "observed_source_series": "OBV == VPT (aliased)",
                },
                "OBV and VPT source series are identical (B12 regression).",
            ))

    return CMFResult(
        warmup_complete=(cmf_value is not None),
        cmf_value=cmf_value,
        obv_change=obv_change,
        vpt_change=vpt_change,
        obv_series=obv_arr,
        vpt_series=vpt_arr,
        failure_events=events,
        provenance=provenance,
    )


def _compute_obv(closes: List[float], volumes: List[float]) -> List[float]:
    """On-Balance Volume series.

    OBV_0 = volume_0; OBV_t = OBV_{t-1} + sign(close_t - close_{t-1}) * volume_t.
    NaN inputs propagate.
    """
    out: List[float] = []
    if not closes:
        return out
    for i in range(len(closes)):
        if i == 0:
            out.append(volumes[0] if not _is_nan(volumes[0]) else float("nan"))
            continue
        prev_c, cur_c, v = closes[i - 1], closes[i], volumes[i]
        if _is_nan(prev_c) or _is_nan(cur_c) or _is_nan(v) or _is_nan(out[i - 1]):
            out.append(float("nan"))
            continue
        if cur_c > prev_c:
            sign = 1.0
        elif cur_c < prev_c:
            sign = -1.0
        else:
            sign = 0.0
        out.append(out[i - 1] + sign * v)
    return out


def _compute_vpt(closes: List[float], volumes: List[float]) -> List[float]:
    """Volume Price Trend series (SEPARATE from OBV — B12 fix).

    VPT_0 = volume_0; VPT_t = VPT_{t-1} + volume_t * (close_t/close_{t-1} - 1).
    NaN inputs propagate.
    """
    out: List[float] = []
    if not closes:
        return out
    for i in range(len(closes)):
        if i == 0:
            out.append(volumes[0] if not _is_nan(volumes[0]) else float("nan"))
            continue
        prev_c, cur_c, v = closes[i - 1], closes[i], volumes[i]
        if _is_nan(prev_c) or _is_nan(cur_c) or _is_nan(v) or _is_nan(out[i - 1]):
            out.append(float("nan"))
            continue
        if abs(prev_c) < 1.0e-15:
            # cannot compute pct change; treat contribution as 0
            out.append(out[i - 1])
            continue
        pct = cur_c / prev_c - 1.0
        out.append(out[i - 1] + v * pct)
    return out


def _series_equal(a: Sequence[float], b: Sequence[float]) -> bool:
    """Element-wise equality within NUMERICAL_TOLERANCE (NaN-aware)."""
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if _is_nan(x) and _is_nan(y):
            continue
        if _is_nan(x) or _is_nan(y):
            return False
        if abs(x - y) > NUMERICAL_TOLERANCE:
            return False
    return True


# ---------------------------------------------------------------------------
# Channel-slope helper (REQ-007) — used by profile_engine; included here per
# implementation-scope module ownership of compute_channel_slope. This is a
# FROZEN normalized formula; threshold freeze lives in profile_engine.
# ---------------------------------------------------------------------------


def compute_channel_slope(
    close_window: Sequence[Any],
) -> Dict[str, Any]:
    """Normalized channel slope = 100 * OLS_slope / median(close_window).

    Units: percent per bar. Scale-free across price levels (REQ-007 frozen).
    Uses ordinary-least-squares slope of close vs index, normalized by the
    median close. Classification threshold is NOT applied here (owned by
    profile_engine's frozen contract).
    """
    closes = _to_float64_array(close_window)
    # drop NaN for the regression
    pts = [(i, c) for i, c in enumerate(closes) if not _is_nan(c)]
    if len(pts) < 2:
        return {
            "normalized_slope_pct_per_bar": None,
            "ols_slope": None,
            "median_close": None,
            "is_fatal": True,
            "failure_events": [FailureEvent.from_code(
                "INSUFFICIENT_HISTORY",
                {
                    "mode": Mode.PROFILE.value,
                    "provided_sessions": len(pts),
                    "required_sessions": 2,
                    "frequency": "daily",
                },
                "Channel slope requires >=2 valid closes.",
            )],
        }

    xs = [float(p[0]) for p in pts]
    ys = [p[1] for p in pts]
    n = len(pts)
    # OLS slope = cov(x,y)/var(x) with x = integer index
    mean_x = _window_sum(xs, 0, n) / n
    mean_y = _window_sum(ys, 0, n) / n
    num = _window_sum([(xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n)], 0, n)
    den = _window_sum([(xs[i] - mean_x) ** 2 for i in range(n)], 0, n)
    if abs(den) < NUMERICAL_TOLERANCE:
        return {
            "normalized_slope_pct_per_bar": None,
            "ols_slope": None,
            "median_close": None,
            "is_fatal": True,
            "failure_events": [FailureEvent.from_code(
                "COMPUTATION_DEGENERATE",
                {
                    "mode": Mode.PROFILE.value,
                    "formula_id": "F-CHANNEL-SLOPE",
                    "denominator_field": "var(x)",
                    "window": n,
                },
                "Channel slope OLS denominator == 0.",
            )],
        }
    slope = num / den
    sorted_y = sorted(ys)
    mid = len(sorted_y) // 2
    median = sorted_y[mid] if len(sorted_y) % 2 == 1 else (sorted_y[mid - 1] + sorted_y[mid]) / 2.0
    if abs(median) < NUMERICAL_TOLERANCE:
        return {
            "normalized_slope_pct_per_bar": None,
            "ols_slope": slope,
            "median_close": median,
            "is_fatal": True,
            "failure_events": [FailureEvent.from_code(
                "COMPUTATION_DEGENERATE",
                {
                    "mode": Mode.PROFILE.value,
                    "formula_id": "F-CHANNEL-SLOPE",
                    "denominator_field": "median(close_window)",
                    "window": n,
                },
                "Channel slope median(close) == 0.",
            )],
        }
    normalized = 100.0 * slope / median
    return {
        "normalized_slope_pct_per_bar": normalized,
        "ols_slope": slope,
        "median_close": median,
        "is_fatal": False,
        "failure_events": [],
    }


__all__ = [
    "RSIResult",
    "BollingerResult",
    "MAResult",
    "MACDResult",
    "BetaResult",
    "CMFResult",
    "IndicatorResult",
    "compute_rsi",
    "compute_bollinger",
    "compute_ma",
    "compute_macd",
    "compute_beta",
    "compute_cmf",
    "compute_channel_slope",
    "MA_WINDOW_SET",
    "RSI_PERIOD",
    "RSI_WARMUP",
    "RSI_MIN_OBS",
    "BOLL_WINDOW",
    "BOLL_MULTIPLIER",
    "BOLL_MIN_OBS",
    "MACD_SHORT",
    "MACD_LONG",
    "MACD_SIGNAL",
    "MACD_MIN_OBS",
    "BETA_WINDOW",
    "BETA_MIN_OBS",
    "CMF_WINDOW",
    "CMF_MIN_OBS",
]
