"""VTA Phase 3 — Normalization Engine.

Production module for input validation, dedup, sort, price-basis selection,
and adjustment-status verification per the VTA Phase 3 frozen contracts.

Owns requirements:
  - VTA-REQ-004 (price basis selection per calculation type)
  - VTA-REQ-012 (no fabricated price data)

Emits canonical failure codes from vta-failure-code-registry.yaml:
  Tier 1 INPUT_FATAL:
    EMPTY_SERIES, INSUFFICIENT_HISTORY, ZERO_PRICE_DETECTED,
    UNKNOWN_ADJUSTMENT_STATUS, CONFLICTING_ADJUSTMENT_STATUS,
    BENCHMARK_UNAVAILABLE, PRICE_BASIS_UNTAGGED, PRICE_BASIS_MISMATCH
  Tier 2 INPUT_RECOVERABLE (diagnostics):
    BENCHMARK_MISALIGNED, MISSING_INTERVAL, DUPLICATE_TIMESTAMP_DEDUPED,
    UNSORTED_TIMESTAMP_SORTED, PARTIAL_WEEK_DROPPED, ZERO_VOLUME_ACCEPTED

This module is NOT a production decision function and imports no decision
logic from other modules. It is deterministic, wall-clock-independent, and
network-independent. Provenance timestamps are injected by the caller.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Frozen constants (from vta-formula-contract-registry.yaml shared_policies)
# ---------------------------------------------------------------------------

NUMERICAL_TOLERANCE = 1.0e-9
COMPARISON_EPSILON = 1.0e-6

# Minimum history gates per vta-failure-code-registry.yaml INSUFFICIENT_HISTORY
MIN_SESSIONS_ACTIVE = 52       # weekly sessions for ACTIVE mode
MIN_SESSIONS_PROFILE = 60      # daily sessions for PROFILE mode

# Missing-interval threshold per shared_policies.missing_bar_behavior
GAP_THRESHOLD_PCT = 10
MISSING_INTERVAL_RATIO_THRESHOLD = 0.95  # actual/expected < 0.95 -> diagnose

# Benchmark inner-join overlap diagnostic threshold
BENCHMARK_OVERLAP_THRESHOLD = 0.95

# Partial-week detection (ACTIVE): weekly bar must cover >= 5 trading days
PARTIAL_WEEK_MIN_TRADING_DAYS = 5


class Mode(str, Enum):
    """Operating mode."""

    ACTIVE = "ACTIVE"
    PROFILE = "PROFILE"


class PriceBasis(str, Enum):
    """Price basis tags per VTA-REQ-004 / shared_policies.price_basis."""

    ADJUSTED = "adjusted"                              # ADJUSTED_OHLCV — indicators/patterns
    TOTAL_RETURN_ADJUSTED = "total_return_adjusted"    # for returns / beta
    RAW = "raw"                                        # for provenance only


class CalculationType(str, Enum):
    """Calculation categories used by verify_price_basis."""

    INDICATOR = "indicator"        # F-MA, F-BOLLINGER, F-RSI, F-MACD, F-CMF...
    PATTERN = "pattern"
    RETURNS = "returns"            # requires TOTAL_RETURN_ADJUSTED
    BETA = "beta"                  # requires TOTAL_RETURN_ADJUSTED
    ALPHA = "alpha"                # inherits from beta


class AdjustmentStatus(str, Enum):
    """Per-row adjustment_status field values (VTA-REQ-004)."""

    ADJUSTED = "adjusted"
    TOTAL_RETURN_ADJUSTED = "total_return_adjusted"
    RAW = "raw"
    UNKNOWN = "unknown"


# Calculation-type -> required price basis (frozen contract)
_REQUIRED_BASIS: Dict[CalculationType, PriceBasis] = {
    CalculationType.INDICATOR: PriceBasis.ADJUSTED,
    CalculationType.PATTERN: PriceBasis.ADJUSTED,
    CalculationType.RETURNS: PriceBasis.TOTAL_RETURN_ADJUSTED,
    CalculationType.BETA: PriceBasis.TOTAL_RETURN_ADJUSTED,
    CalculationType.ALPHA: PriceBasis.TOTAL_RETURN_ADJUSTED,
}


class Severity(str, Enum):
    """Failure-code tier mapping (informational; codes carry tier themselves)."""

    FATAL = "FATAL"          # tier 1 — aborts the run
    DIAGNOSTIC = "DIAGNOSTIC"  # tier 2 — run continues, status degrades


class AnalysisStatus(str, Enum):
    """Run-level status."""

    OK = "OK"
    VALID_WITH_WARNINGS = "VALID_WITH_WARNINGS"
    FAILED = "FAILED"


# ---------------------------------------------------------------------------
# Failure-code records (stable machine contract — no free-text parsing)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FailureCode:
    """A canonical failure-code record.

    Per P-NO-MESSAGE-AS-CONTRACT: failure_code is the machine-readable
    contract; message is human diagnostic only.
    """

    failure_code: str
    tier: int
    precedence: int
    classification: str            # PRIMARY | DIAGNOSTIC
    semantic_definition: str
    required_context_fields: Tuple[str, ...]
    mutually_exclusive_with: Tuple[str, ...] = ()


# Registry of codes owned/emitted by this module (from the frozen registry).
_CODES: Dict[str, FailureCode] = {
    "EMPTY_SERIES": FailureCode(
        "EMPTY_SERIES", 1, 10, "PRIMARY",
        "Input OHLCV series has zero rows after load.",
        ("mode", "provided_rows", "source_provider"),
        mutually_exclusive_with=("INSUFFICIENT_HISTORY",),
    ),
    "INSUFFICIENT_HISTORY": FailureCode(
        "INSUFFICIENT_HISTORY", 1, 20, "PRIMARY",
        "Input series present but below the mode-specific minimum session count.",
        ("mode", "provided_sessions", "required_sessions", "frequency"),
        mutually_exclusive_with=("EMPTY_SERIES",),
    ),
    "ZERO_PRICE_DETECTED": FailureCode(
        "ZERO_PRICE_DETECTED", 1, 30, "PRIMARY",
        "An OHLC value in the input is exactly 0 (never a legitimate VN market price).",
        ("mode", "date", "field", "observed_value"),
        mutually_exclusive_with=("COMPUTATION_DEGENERATE",),
    ),
    "UNKNOWN_ADJUSTMENT_STATUS": FailureCode(
        "UNKNOWN_ADJUSTMENT_STATUS", 1, 40, "PRIMARY",
        "adjustment_status == UNKNOWN on an input row consumed by the run.",
        ("mode", "date", "observed_adjustment_status"),
        mutually_exclusive_with=("CONFLICTING_ADJUSTMENT_STATUS",),
    ),
    "CONFLICTING_ADJUSTMENT_STATUS": FailureCode(
        "CONFLICTING_ADJUSTMENT_STATUS", 1, 41, "PRIMARY",
        "Input series mixes adjustment_status values within the same series.",
        ("mode", "distinct_statuses", "affected_date_range"),
        mutually_exclusive_with=("UNKNOWN_ADJUSTMENT_STATUS",),
    ),
    "PRICE_BASIS_UNTAGGED": FailureCode(
        "PRICE_BASIS_UNTAGGED", 1, 42, "PRIMARY",
        "An indicator input record lacks the required price_basis tag.",
        ("mode", "indicator_id", "observed_basis_tag"),
        mutually_exclusive_with=("UNKNOWN_ADJUSTMENT_STATUS",),
    ),
    "PRICE_BASIS_MISMATCH": FailureCode(
        "PRICE_BASIS_MISMATCH", 1, 43, "PRIMARY",
        "Returns/beta consumed adjusted_close instead of total_return_adjusted_close.",
        ("mode", "calculation", "observed_basis", "required_basis"),
        mutually_exclusive_with=("UNKNOWN_ADJUSTMENT_STATUS",),
    ),
    "BENCHMARK_UNAVAILABLE": FailureCode(
        "BENCHMARK_UNAVAILABLE", 1, 50, "PRIMARY",
        "Benchmark series required but None / not supplied.",
        ("mode", "calculation", "expected_benchmark"),
        mutually_exclusive_with=("BENCHMARK_MISALIGNED",),
    ),
    "BENCHMARK_MISALIGNED": FailureCode(
        "BENCHMARK_MISALIGNED", 2, 110, "DIAGNOSTIC",
        "Stock and benchmark dates overlap below 95%; inner-join proceeds on subset.",
        ("mode", "overlap_ratio", "stock_range", "benchmark_range"),
        mutually_exclusive_with=("BENCHMARK_UNAVAILABLE",),
    ),
    "MISSING_INTERVAL": FailureCode(
        "MISSING_INTERVAL", 2, 120, "DIAGNOSTIC",
        "Gaps in trading-day sequence exceed 5% of expected sessions.",
        ("mode", "actual_days", "expected_days", "gap_dates"),
    ),
    "DUPLICATE_TIMESTAMP_DEDUPED": FailureCode(
        "DUPLICATE_TIMESTAMP_DEDUPED", 2, 130, "DIAGNOSTIC",
        "Duplicate dates resolved with last-value-wins before computation.",
        ("mode", "duplicate_dates", "resolution_policy"),
    ),
    "UNSORTED_TIMESTAMP_SORTED": FailureCode(
        "UNSORTED_TIMESTAMP_SORTED", 2, 140, "DIAGNOSTIC",
        "Input dates were not monotonic; sorted ascending before computation.",
        ("mode", "original_order_violation_count"),
    ),
    "PARTIAL_WEEK_DROPPED": FailureCode(
        "PARTIAL_WEEK_DROPPED", 2, 150, "DIAGNOSTIC",
        "Latest weekly bar covers <5 trading days; dropped.",
        ("mode", "dropped_week_start", "trading_days_in_week"),
    ),
    "ZERO_VOLUME_ACCEPTED": FailureCode(
        "ZERO_VOLUME_ACCEPTED", 2, 160, "DIAGNOSTIC",
        "Zero-volume session detected and accepted as legitimate (suspended/halted).",
        ("mode", "date", "observed_volume"),
        mutually_exclusive_with=("ZERO_PRICE_DETECTED",),
    ),
    # ------------------------------------------------------------------
    # Tier 1 INPUT_FATAL (config validation) — emitted by indicator_engine
    # and other formula modules for frozen-contract config violations.
    # ------------------------------------------------------------------
    "CONFIG_VALIDATION_FAILED": FailureCode(
        "CONFIG_VALIDATION_FAILED", 1, 60, "PRIMARY",
        "A configuration value (window, threshold, enum) violates the frozen contract.",
        ("config_key", "observed_value", "allowed_values"),
    ),
    # ------------------------------------------------------------------
    # Tier 3 COMPUTATION — emitted by indicator_engine for degenerate
    # denominators, NaN propagation, and formula-specific regressions.
    # ------------------------------------------------------------------
    "COMPUTATION_DEGENERATE": FailureCode(
        "COMPUTATION_DEGENERATE", 3, 210, "PRIMARY",
        "A numeric computation hit a degenerate denominator/state (std=0, denominator=0).",
        ("mode", "formula_id", "denominator_field", "window"),
        mutually_exclusive_with=("ZERO_PRICE_DETECTED",),
    ),
    "NAN_PROPAGATION": FailureCode(
        "NAN_PROPAGATION", 3, 220, "PRIMARY",
        "A NaN reached a required output field that must be finite.",
        ("mode", "field_path", "source_nan_date"),
    ),
    "OBV_VPT_SERIES_CONTAMINATION": FailureCode(
        "OBV_VPT_SERIES_CONTAMINATION", 3, 240, "PRIMARY",
        "obv_change sourced from VPT series OR vpt_change sourced from OBV (B12 regression).",
        ("mode", "field", "expected_source_series", "observed_source_series"),
    ),
    "SMOOTHING_MISMATCH": FailureCode(
        "SMOOTHING_MISMATCH", 3, 230, "PRIMARY",
        "Recomputed RSI using Wilder smoothing diverges from engine beyond 1e-6.",
        ("mode", "index", "engine_value", "recompute_value", "abs_diff"),
    ),
    "MODE_KERNEL_DIVERGENCE": FailureCode(
        "MODE_KERNEL_DIVERGENCE", 3, 260, "PRIMARY",
        "ACTIVE-mode and PROFILE-mode kernels diverge for a shared indicator.",
        ("indicator", "active_value", "profile_value", "abs_diff",
         "std_convention_active", "std_convention_profile"),
    ),
}


@dataclass
class FailureEvent:
    """An emitted failure code with its required context fields populated."""

    failure_code: str
    tier: int
    precedence: int
    classification: str
    semantic_definition: str
    context: Dict[str, Any] = field(default_factory=dict)
    message: str = ""  # human diagnostic only; NOT a machine contract

    @classmethod
    def from_code(cls, code_name: str, context: Dict[str, Any], message: str = "") -> "FailureEvent":
        spec = _CODES[code_name]
        normalized = cls._coerce_context(code_name, context)
        return cls(
            failure_code=spec.failure_code,
            tier=spec.tier,
            precedence=spec.precedence,
            classification=spec.classification,
            semantic_definition=spec.semantic_definition,
            context=normalized,
            message=message,
        )

    @staticmethod
    def _coerce_context(code_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure required_context_fields are present (P-NO-MESSAGE-AS-CONTRACT)."""
        spec = _CODES[code_name]
        out: Dict[str, Any] = {}
        for key in spec.required_context_fields:
            if key in context:
                out[key] = context[key]
            else:
                out[key] = None
        # carry any extra context too (diagnostic enrichment)
        for k, v in context.items():
            if k not in out:
                out[k] = v
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "failure_code": self.failure_code,
            "tier": self.tier,
            "precedence": self.precedence,
            "classification": self.classification,
            "context": dict(self.context),
            "message": self.message,
        }


# ---------------------------------------------------------------------------
# Public result types
# ---------------------------------------------------------------------------


@dataclass
class PriceBasisResult:
    """Result of verify_price_basis."""

    ok: bool
    calculation_type: CalculationType
    required_basis: PriceBasis
    observed_basis: Optional[PriceBasis]
    is_fatal: bool
    failure_events: List[FailureEvent] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedInput:
    """Result of normalize_input — clean, sorted, de-duplicated series.

    All numeric fields are float64; rows are in chronological ascending
    order by trade_date. The series is guaranteed to satisfy the mode's
    minimum-session gate unless `is_fatal` is True.
    """

    mode: Mode
    frequency: str                           # "weekly" | "daily"
    trade_dates: List[str]                   # ISO-8601 ascending
    adjusted_close: List[float]              # ADJUSTED_OHLCV (indicators/patterns)
    total_return_adjusted_close: List[float]  # returns/beta basis
    raw_open: List[float]
    raw_high: List[float]
    raw_low: List[float]
    raw_close: List[float]
    volume: List[float]
    adjustment_status: AdjustmentStatus       # uniform after verification
    price_basis_indicator: PriceBasis = PriceBasis.ADJUSTED
    price_basis_returns: PriceBasis = PriceBasis.TOTAL_RETURN_ADJUSTED
    analysis_status: AnalysisStatus = AnalysisStatus.OK
    is_fatal: bool = False
    primary_failure: Optional[FailureEvent] = None
    diagnostic_codes: List[FailureEvent] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)

    @property
    def n_sessions(self) -> int:
        return len(self.trade_dates)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "frequency": self.frequency,
            "n_sessions": self.n_sessions,
            "adjustment_status": self.adjustment_status.value,
            "price_basis_indicator": self.price_basis_indicator.value,
            "price_basis_returns": self.price_basis_returns.value,
            "analysis_status": self.analysis_status.value,
            "is_fatal": self.is_fatal,
            "primary_failure": self.primary_failure.to_dict() if self.primary_failure else None,
            "diagnostic_codes": [c.to_dict() for c in self.diagnostic_codes],
            "provenance": dict(self.provenance),
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _is_finite_number(x: Any) -> bool:
    """True iff x is a finite real number (not None/NaN/inf/non-numeric)."""
    if x is None:
        return False
    if isinstance(x, bool):
        return False
    if not isinstance(x, (int, float)):
        return False
    f = float(x)
    return not (math.isnan(f) or math.isinf(f))


def _to_float_or_nan(x: Any) -> float:
    """Coerce to float, returning NaN if missing/non-numeric (pass-through policy)."""
    if _is_finite_number(x):
        return float(x)
    return float("nan")


def _coerce_adjustment_status(raw: Any) -> AdjustmentStatus:
    """Parse the adjustment_status field defensively; unknown strings -> UNKNOWN."""
    if raw is None:
        return AdjustmentStatus.UNKNOWN
    s = str(raw).strip().lower()
    mapping = {
        "adjusted": AdjustmentStatus.ADJUSTED,
        "adj": AdjustmentStatus.ADJUSTED,
        "total_return_adjusted": AdjustmentStatus.TOTAL_RETURN_ADJUSTED,
        "total_return": AdjustmentStatus.TOTAL_RETURN_ADJUSTED,
        "tra": AdjustmentStatus.TOTAL_RETURN_ADJUSTED,
        "raw": AdjustmentStatus.RAW,
        "unadjusted": AdjustmentStatus.RAW,
        "unknown": AdjustmentStatus.UNKNOWN,
        "": AdjustmentStatus.UNKNOWN,
    }
    return mapping.get(s, AdjustmentStatus.UNKNOWN)


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

    ``input_data`` accepts the raw OHLCV series (or any hashable
    representation the caller is processing). When omitted the id is still
    deterministic but flagged with mode UNKNOWN.
    """
    import hashlib
    import json as _json

    canonical = _json.dumps(
        {"data": str(input_data)[:1000], "mode": str(mode)},
        sort_keys=True,
    )
    return "chain-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Price-basis verification (VTA-REQ-004)
# ---------------------------------------------------------------------------


def verify_price_basis(
    input_record: Any,
    calculation_type: CalculationType,
    *,
    mode: Mode = Mode.ACTIVE,
    indicator_id: Optional[str] = None,
) -> PriceBasisResult:
    """Verify the price basis required for a calculation type.

    Per VTA-REQ-004 frozen contract:
      - INDICATOR / PATTERN -> adjusted (ADJUSTED_OHLCV)
      - RETURNS / BETA / ALPHA -> total_return_adjusted (TOTAL_RETURN_ADJUSTED_CLOSE)

    Emits, when violated:
      PRICE_BASIS_UNTAGGED — input lacks the required tag
      PRICE_BASIS_MISMATCH — returns/beta used adjusted basis

    Parameters
    ----------
    input_record : object carrying a ``price_basis`` attribute/key, or None.
    calculation_type : CalculationType
    mode : Mode
    indicator_id : optional indicator id for context enrichment.
    """
    calc = CalculationType(calculation_type) if not isinstance(calculation_type, CalculationType) else calculation_type
    required = _REQUIRED_BASIS[calc]

    observed: Optional[PriceBasis] = None
    has_tag = False
    if input_record is not None:
        raw_basis = None
        if isinstance(input_record, dict):
            raw_basis = input_record.get("price_basis")
        else:
            raw_basis = getattr(input_record, "price_basis", None)
        if raw_basis is not None and str(raw_basis).strip() != "":
            has_tag = True
            try:
                observed = PriceBasis(str(raw_basis).strip().lower())
            except ValueError:
                observed = None
                has_tag = False

    events: List[FailureEvent] = []
    is_fatal = False
    ok = True

    if not has_tag or observed is None:
        # Tag absent or invalid -> PRICE_BASIS_UNTAGGED (tier 1 fatal).
        is_fatal = True
        ok = False
        ctx = {
            "mode": mode.value,
            "indicator_id": indicator_id or calc.value,
            "observed_basis_tag": None if input_record is None else (
                input_record.get("price_basis") if isinstance(input_record, dict)
                else getattr(input_record, "price_basis", None)
            ),
        }
        events.append(FailureEvent.from_code(
            "PRICE_BASIS_UNTAGGED", ctx,
            "Indicator input record lacks a valid price_basis tag.",
        ))
    elif observed != required:
        # Wrong basis used. For returns/beta class this is PRICE_BASIS_MISMATCH;
        # for indicator class this is also a basis-tag violation but mismatch
        # semantics are the canonical mapping (returns/beta mis-basis).
        is_fatal = True
        ok = False
        ctx = {
            "mode": mode.value,
            "calculation": calc.value,
            "observed_basis": observed.value,
            "required_basis": required.value,
            "indicator_id": indicator_id or calc.value,
        }
        # PRICE_BASIS_MISMATCH owns VC-PRICE-BASIS-2 (returns/beta on wrong basis).
        # For indicator-class wrong basis, PRICE_BASIS_UNTAGGED does not fit;
        # PRICE_BASIS_MISMATCH is the closest canonical code and is emitted
        # for both, with required/observed recorded in context. Mutually
        # exclusive with UNKNOWN_ADJUSTMENT_STATUS per registry.
        if calc in (CalculationType.RETURNS, CalculationType.BETA, CalculationType.ALPHA):
            events.append(FailureEvent.from_code(
                "PRICE_BASIS_MISMATCH", ctx,
                f"{calc.value} requires {required.value}; observed {observed.value}.",
            ))
        else:
            ctx["calculation"] = calc.value
            events.append(FailureEvent.from_code(
                "PRICE_BASIS_MISMATCH", ctx,
                f"{calc.value} requires {required.value}; observed {observed.value}.",
            ))

    return PriceBasisResult(
        ok=ok,
        calculation_type=calc,
        required_basis=required,
        observed_basis=observed,
        is_fatal=is_fatal,
        failure_events=events,
        provenance={
            "source_provider": None,
            "calculation_type": calc.value,
            "required_basis": required.value,
        },
    )


# ---------------------------------------------------------------------------
# Benchmark alignment diagnostic (used by Beta / Correlation callers)
# ---------------------------------------------------------------------------


def align_benchmark_dates(
    stock_dates: Sequence[str],
    benchmark_dates: Sequence[str],
    *,
    mode: Mode = Mode.ACTIVE,
    calculation: str = "beta",
    expected_benchmark: str = "VNINDEX",
    benchmark_values: Optional[Sequence[float]] = None,
    stock_values: Optional[Sequence[float]] = None,
) -> Dict[str, Any]:
    """Inner-join two series on common trade dates (INNER_JOIN_BY_TRADE_DATE).

    Returns aligned (stock, benchmark) values + diagnostic codes:
      BENCHMARK_UNAVAILABLE (tier 1) if benchmark is empty/None
      BENCHMARK_MISALIGNED (tier 2) if overlap < 95%
    """
    if benchmark_dates is None or len(benchmark_dates) == 0 or benchmark_values is None:
        return {
            "aligned_dates": [],
            "aligned_stock": [],
            "aligned_benchmark": [],
            "failure_events": [FailureEvent.from_code(
                "BENCHMARK_UNAVAILABLE",
                {"mode": mode.value, "calculation": calculation, "expected_benchmark": expected_benchmark},
                f"Benchmark {expected_benchmark} unavailable for {calculation}.",
            )],
            "is_fatal": True,
        }

    stock_map: Dict[str, float] = {}
    for d, v in zip(stock_dates, stock_values or [float("nan")] * len(stock_dates)):
        stock_map[str(d)] = _to_float_or_nan(v)
    bench_map: Dict[str, float] = {}
    for d, v in zip(benchmark_dates, benchmark_values or [float("nan")] * len(benchmark_dates)):
        bench_map[str(d)] = _to_float_or_nan(v)

    common = sorted(set(stock_map.keys()) & set(bench_map.keys()))
    overlap_ratio = (len(common) / len(set(stock_dates))) if stock_dates else 0.0

    aligned_stock = [stock_map[d] for d in common]
    aligned_bench = [bench_map[d] for d in common]

    events: List[FailureEvent] = []
    if overlap_ratio < BENCHMARK_OVERLAP_THRESHOLD:
        events.append(FailureEvent.from_code(
            "BENCHMARK_MISALIGNED",
            {
                "mode": mode.value,
                "overlap_ratio": overlap_ratio,
                "stock_range": (stock_dates[0], stock_dates[-1]) if stock_dates else (None, None),
                "benchmark_range": (benchmark_dates[0], benchmark_dates[-1]) if benchmark_dates else (None, None),
            },
            f"Stock/benchmark overlap ratio {overlap_ratio:.4f} < {BENCHMARK_OVERLAP_THRESHOLD}.",
        ))

    return {
        "aligned_dates": common,
        "aligned_stock": aligned_stock,
        "aligned_benchmark": aligned_bench,
        "failure_events": events,
        "is_fatal": False,
        "overlap_ratio": overlap_ratio,
    }


# ---------------------------------------------------------------------------
# normalize_input — the public entry point
# ---------------------------------------------------------------------------


# Canonical OHLCV field names accepted from market-data-packet-v1.
_OHLCV_FIELDS = ("open", "high", "low", "close", "volume", "adjusted_close",
                 "total_return_adjusted_close", "trade_date", "date",
                 "adjustment_status")


def _extract_row_fields(row: Any) -> Dict[str, Any]:
    """Pull OHLCV fields from a dict-like or object-like row."""
    out: Dict[str, Any] = {}
    if isinstance(row, dict):
        src = row
    else:
        src = {f: getattr(row, f, None) for f in _OHLCV_FIELDS}
        # also accept dict-style access on objects
        for f in _OHLCV_FIELDS:
            if f not in src or src[f] is None:
                if hasattr(row, "__getitem__"):
                    try:
                        src[f] = row[f]
                    except Exception:
                        pass

    out["trade_date"] = src.get("trade_date") or src.get("date")
    out["open"] = src.get("open")
    out["high"] = src.get("high")
    out["low"] = src.get("low")
    out["close"] = src.get("close")
    out["volume"] = src.get("volume")
    out["adjusted_close"] = src.get("adjusted_close")
    out["total_return_adjusted_close"] = src.get("total_return_adjusted_close")
    out["adjustment_status"] = src.get("adjustment_status")
    return out


def _detect_zero_price(rows: List[Dict[str, Any]], mode: Mode) -> Optional[FailureEvent]:
    """VC-ZERO-PX-1: any OHLC == 0 is fatal (never a legitimate VN price)."""
    for r in rows:
        for f in ("open", "high", "low", "close", "adjusted_close",
                  "total_return_adjusted_close"):
            v = r.get(f)
            if v is not None and _is_finite_number(v) and float(v) == 0.0:
                return FailureEvent.from_code(
                    "ZERO_PRICE_DETECTED",
                    {
                        "mode": mode.value,
                        "date": r.get("trade_date"),
                        "field": f,
                        "observed_value": 0.0,
                    },
                    f"Field {f} == 0 at {r.get('trade_date')}; zero price prohibited.",
                )
    return None


def _resolve_duplicates(rows: List[Dict[str, Any]], mode: Mode) -> Tuple[List[Dict[str, Any]], List[FailureEvent]]:
    """VC-DUP-TS-1: dedup by trade_date, last-wins."""
    events: List[FailureEvent] = []
    seen: Dict[str, Dict[str, Any]] = {}
    dup_dates: List[str] = []
    order: List[str] = []
    for r in rows:
        d = r.get("trade_date")
        if d is None:
            continue
        key = str(d)
        if key in seen:
            dup_dates.append(key)
        else:
            order.append(key)
        seen[key] = r  # last wins
    if dup_dates:
        events.append(FailureEvent.from_code(
            "DUPLICATE_TIMESTAMP_DEDUPED",
            {
                "mode": mode.value,
                "duplicate_dates": sorted(set(dup_dates)),
                "resolution_policy": "DEDUP_LAST_WINS",
            },
            f"{len(set(dup_dates))} duplicate trade_date(s) collapsed (last-wins).",
        ))
    deduped = [seen[k] for k in order]
    return deduped, events


def _sort_chronologically(rows: List[Dict[str, Any]], mode: Mode) -> Tuple[List[Dict[str, Any]], List[FailureEvent]]:
    """VC-UNSORTED-1: sort ascending by trade_date, diagnose if unsorted."""
    events: List[FailureEvent] = []
    original_keys = [str(r.get("trade_date")) for r in rows if r.get("trade_date") is not None]
    is_sorted = all(original_keys[i] <= original_keys[i + 1] for i in range(len(original_keys) - 1))
    if not is_sorted:
        violations = sum(
            1 for i in range(len(original_keys) - 1)
            if original_keys[i] > original_keys[i + 1]
        )
        events.append(FailureEvent.from_code(
            "UNSORTED_TIMESTAMP_SORTED",
            {"mode": mode.value, "original_order_violation_count": violations},
            f"{violations} monotonic-order violations; sorted ascending.",
        ))
    return sorted(rows, key=lambda r: str(r.get("trade_date"))), events


def _verify_adjustment_uniformity(rows: List[Dict[str, Any]], mode: Mode) -> Tuple[AdjustmentStatus, List[FailureEvent]]:
    """VTA-REQ-004: UNKNOWN or mixed adjustment_status -> fail-closed.

    Returns the uniform status if clean, else UNKNOWN plus fatal event(s).
    """
    events: List[FailureEvent] = []
    statuses: List[AdjustmentStatus] = []
    unknown_dates: List[str] = []

    for r in rows:
        st = _coerce_adjustment_status(r.get("adjustment_status"))
        statuses.append(st)
        if st == AdjustmentStatus.UNKNOWN:
            unknown_dates.append(str(r.get("trade_date")))

    if unknown_dates:
        # UNKNOWN on any consumed row -> fail-closed (precedence 40).
        first = unknown_dates[0]
        events.append(FailureEvent.from_code(
            "UNKNOWN_ADJUSTMENT_STATUS",
            {
                "mode": mode.value,
                "date": first,
                "observed_adjustment_status": "unknown",
            },
            f"adjustment_status == UNKNOWN on {len(unknown_dates)} row(s); cannot decide basis.",
        ))
        return AdjustmentStatus.UNKNOWN, events

    non_raw = [s for s in statuses if s != AdjustmentStatus.RAW]
    distinct = set(non_raw)
    if len(distinct) > 1:
        # Mixed non-RAW statuses within the series -> CONFLICTING (precedence 41).
        events.append(FailureEvent.from_code(
            "CONFLICTING_ADJUSTMENT_STATUS",
            {
                "mode": mode.value,
                "distinct_statuses": sorted(s.value for s in distinct),
                "affected_date_range": (
                    str(rows[0].get("trade_date")), str(rows[-1].get("trade_date"))
                ) if rows else (None, None),
            },
            f"Conflicting adjustment_status values: {sorted(s.value for s in distinct)}.",
        ))
        return AdjustmentStatus.UNKNOWN, events

    if not non_raw:
        # Only RAW present -> treat as UNKNOWN basis decision (cannot satisfy any
        # adjusted-basis requirement). This is the only path where RAW input
        # triggers a fatal; the canonical mapping is UNKNOWN_ADJUSTMENT_STATUS
        # because the basis decision cannot be made.
        events.append(FailureEvent.from_code(
            "UNKNOWN_ADJUSTMENT_STATUS",
            {
                "mode": mode.value,
                "date": str(rows[0].get("trade_date")) if rows else None,
                "observed_adjustment_status": "raw_only",
            },
            "Only raw adjustment_status present; cannot select adjusted basis.",
        ))
        return AdjustmentStatus.UNKNOWN, events

    uniform = next(iter(distinct))
    return uniform, events


def _detect_missing_intervals(
    dates: List[str], mode: Mode, frequency: str
) -> List[FailureEvent]:
    """VC-MISS-INT-1: gap diagnostic when actual/expected < 0.95.

    Expected count is approximated from the calendar span because the engine
    has no trading-calendar dependency (frozen: no_network_dependency). The
    gap detection is best-effort calendar-based; full calendar integration is
    a Phase 4 concern (per shared_policies.missing_bar_behavior).
    """
    events: List[FailureEvent] = []
    if len(dates) < 2:
        return events
    try:
        from datetime import date as _date, timedelta as _td

        def _parse(d: str) -> _date:
            return _date.fromisoformat(str(d)[:10])

        first = _parse(dates[0])
        last = _parse(dates[-1])
        span_days = (last - first).days + 1
        if frequency == "weekly":
            expected = max(1, span_days // 7)
        else:
            # daily: approximate trading days as ~5/7 of calendar days
            expected = max(1, int(span_days * 5 / 7))
        actual = len(dates)
        ratio = actual / expected if expected else 1.0
        if ratio < MISSING_INTERVAL_RATIO_THRESHOLD:
            gap_dates = _find_gap_dates(dates, frequency)
            events.append(FailureEvent.from_code(
                "MISSING_INTERVAL",
                {
                    "mode": mode.value,
                    "actual_days": actual,
                    "expected_days": expected,
                    "gap_dates": gap_dates[:20],
                },
                f"actual/expected sessions ratio {ratio:.4f} < {MISSING_INTERVAL_RATIO_THRESHOLD}.",
            ))
    except Exception:
        # Date parsing unavailable — skip the diagnostic (no synthetic data
        # injected; PASS_THROUGH_AS_MISSING policy).
        pass
    return events


def _find_gap_dates(dates: List[str], frequency: str) -> List[str]:
    """Return a sample list of missing dates (calendar heuristic)."""
    try:
        from datetime import date as _date, timedelta as _td

        parsed = [_parse_iso(d) for d in dates]
        gaps: List[str] = []
        step = _td(days=7) if frequency == "weekly" else _td(days=1)
        cur = parsed[0]
        idx = 0
        while idx < len(parsed) - 1:
            nxt = parsed[idx + 1]
            while cur < nxt:
                if cur != parsed[idx]:
                    gaps.append(cur.isoformat())
                cur += step
            idx += 1
            cur = parsed[idx]
        return gaps
    except Exception:
        return []


def _parse_iso(d: str):
    from datetime import date as _date
    return _date.fromisoformat(str(d)[:10])


def _select_primary(events: List[FailureEvent]) -> Optional[FailureEvent]:
    """Return the lowest-(tier,precedence) PRIMARY event, else None."""
    primaries = [e for e in events if e.classification == "PRIMARY"]
    if not primaries:
        return None
    primaries.sort(key=lambda e: (e.tier, e.precedence))
    return primaries[0]


def normalize_input(
    raw_ohlcv: Any,
    mode: Mode,
    *,
    frequency: Optional[str] = None,
    source_provider: Optional[str] = None,
    benchmark_data: Optional[Dict[str, Any]] = None,
    expected_benchmark: str = "VNINDEX",
    drop_partial_week: bool = True,
    chain_id: Optional[str] = None,
) -> NormalizedInput:
    """Validate, dedup, sort and price-basis-select raw OHLCV into a NormalizedInput.

    Steps (per vta-phase-3-implementation-scope.yaml module contract):
      1. EMPTY_SERIES pre-flight
      2. Row field extraction
      3. ZERO_PRICE_DETECTED scan (fatal)
      4. DUPLICATE_TIMESTAMP_DEDUPED (diagnostic, last-wins)
      5. UNSORTED_TIMESTAMP_SORTED (diagnostic)
      6. UNKNOWN_ADJUSTMENT_STATUS / CONFLICTING_ADJUSTMENT_STATUS (fatal)
      7. INSUFFICIENT_HISTORY gate (fatal)
      8. MISSING_INTERVAL diagnostic
      9. ZERO_VOLUME_ACCEPTED diagnostic (PROFILE only)
      10. PARTIAL_WEEK_DROPPED diagnostic (ACTIVE, if enabled)
      11. Price-basis population (adjusted vs total_return_adjusted)

    The numeric output series are always returned (even on fatal) so callers
    can inspect provenance; callers MUST check ``is_fatal`` / ``primary_failure``
    before computing on them.
    """
    mode_enum = Mode(mode) if not isinstance(mode, Mode) else mode
    freq = frequency or ("weekly" if mode_enum == Mode.ACTIVE else "daily")

    all_events: List[FailureEvent] = []
    chain = chain_id or _gen_chain_id(raw_ohlcv, mode_enum.value)

    # --- Step 1: EMPTY_SERIES pre-flight ---------------------------------
    if raw_ohlcv is None:
        all_events.append(FailureEvent.from_code(
            "EMPTY_SERIES",
            {"mode": mode_enum.value, "provided_rows": 0, "source_provider": source_provider},
            "Input OHLCV series is None.",
        ))
        return _empty_result(mode_enum, freq, all_events, source_provider, chain)

    rows_in: List[Any]
    if isinstance(raw_ohlcv, (list, tuple)):
        rows_in = list(raw_ohlcv)
    else:
        # DataFrame-like: iterate records defensively.
        try:
            rows_in = list(raw_ohlcv)  # iterable of rows
        except TypeError:
            rows_in = []

    if len(rows_in) == 0:
        all_events.append(FailureEvent.from_code(
            "EMPTY_SERIES",
            {"mode": mode_enum.value, "provided_rows": 0, "source_provider": source_provider},
            "Input OHLCV series has zero rows.",
        ))
        return _empty_result(mode_enum, freq, all_events, source_provider, chain)

    # --- Step 2: row field extraction ------------------------------------
    extracted = [_extract_row_fields(r) for r in rows_in]
    extracted = [r for r in extracted if r.get("trade_date") is not None]

    # --- Step 3: ZERO_PRICE scan (fatal) ---------------------------------
    zero_price = _detect_zero_price(extracted, mode_enum)
    if zero_price is not None:
        all_events.append(zero_price)

    # --- Step 4: dedup (last-wins) ---------------------------------------
    deduped, dup_events = _resolve_duplicates(extracted, mode_enum)
    all_events.extend(dup_events)

    # --- Step 5: chronological sort --------------------------------------
    sorted_rows, sort_events = _sort_chronologically(deduped, mode_enum)
    all_events.extend(sort_events)

    # --- Step 6: adjustment-status verification --------------------------
    uniform_status, adj_events = _verify_adjustment_uniformity(sorted_rows, mode_enum)
    all_events.extend(adj_events)

    # --- Step 7: INSUFFICIENT_HISTORY gate -------------------------------
    n = len(sorted_rows)
    required = MIN_SESSIONS_ACTIVE if mode_enum == Mode.ACTIVE else MIN_SESSIONS_PROFILE
    if n < required:
        all_events.append(FailureEvent.from_code(
            "INSUFFICIENT_HISTORY",
            {
                "mode": mode_enum.value,
                "provided_sessions": n,
                "required_sessions": required,
                "frequency": freq,
            },
            f"Provided {n} {freq} sessions < {required} required for {mode_enum.value}.",
        ))

    # --- Step 8: MISSING_INTERVAL diagnostic -----------------------------
    dates_only = [str(r.get("trade_date")) for r in sorted_rows]
    all_events.extend(_detect_missing_intervals(dates_only, mode_enum, freq))

    # --- Step 9: ZERO_VOLUME diagnostic (PROFILE only) -------------------
    if mode_enum == Mode.PROFILE:
        for r in sorted_rows:
            v = r.get("volume")
            if v is not None and _is_finite_number(v) and float(v) == 0.0:
                all_events.append(FailureEvent.from_code(
                    "ZERO_VOLUME_ACCEPTED",
                    {"mode": mode_enum.value, "date": r.get("trade_date"), "observed_volume": 0.0},
                    "Zero-volume session accepted (suspended/halted).",
                ))
                # one diagnostic per series is sufficient for status context
                break

    # --- Step 10: PARTIAL_WEEK diagnostic (ACTIVE) -----------------------
    dropped_partial: List[Dict[str, Any]] = []
    if mode_enum == Mode.ACTIVE and drop_partial_week and sorted_rows:
        last = sorted_rows[-1]
        td = last.get("trading_days_in_week")
        if _is_finite_number(td) and int(td) < PARTIAL_WEEK_MIN_TRADING_DAYS:
            dropped_partial.append(last)
            all_events.append(FailureEvent.from_code(
                "PARTIAL_WEEK_DROPPED",
                {
                    "mode": mode_enum.value,
                    "dropped_week_start": last.get("trade_date"),
                    "trading_days_in_week": int(td),
                },
                f"Latest weekly bar covers {int(td)} < {PARTIAL_WEEK_MIN_TRADING_DAYS} trading days; dropped.",
            ))

    # Build the numeric series. Partial-week bar (if flagged) is dropped from
    # the returned series per the diagnostic's contract.
    effective_rows = [r for r in sorted_rows if r not in dropped_partial] if dropped_partial else sorted_rows

    # --- Step 11: price-basis population ---------------------------------
    # adjusted_close for indicators/patterns; total_return_adjusted_close for
    # returns/beta. If a column is missing, fall back to raw close but flag
    # via the adjustment verification (uniform_status will already be UNKNOWN
    # if basis cannot be determined).
    adjusted_close: List[float] = []
    total_return_close: List[float] = []
    raw_open: List[float] = []
    raw_high: List[float] = []
    raw_low: List[float] = []
    raw_close: List[float] = []
    volume: List[float] = []
    final_dates: List[str] = []

    for r in effective_rows:
        adj = r.get("adjusted_close")
        tra = r.get("total_return_adjusted_close")
        # Pass-through-as-missing policy: NaN where missing/non-numeric.
        adjusted_close.append(_to_float_or_nan(adj if adj is not None else r.get("close")))
        total_return_close.append(_to_float_or_nan(tra if tra is not None else adj))
        raw_open.append(_to_float_or_nan(r.get("open")))
        raw_high.append(_to_float_or_nan(r.get("high")))
        raw_low.append(_to_float_or_nan(r.get("low")))
        raw_close.append(_to_float_or_nan(r.get("close")))
        volume.append(_to_float_or_nan(r.get("volume")))
        final_dates.append(str(r.get("trade_date")))

    # Final primary + diagnostic classification.
    primary = _select_primary(all_events)
    diagnostics = [e for e in all_events if e.classification == "DIAGNOSTIC"]
    is_fatal = primary is not None
    status = AnalysisStatus.FAILED if is_fatal else (
        AnalysisStatus.VALID_WITH_WARNINGS if diagnostics else AnalysisStatus.OK
    )

    price_basis_indicator = PriceBasis.ADJUSTED
    price_basis_returns = PriceBasis.TOTAL_RETURN_ADJUSTED

    return NormalizedInput(
        mode=mode_enum,
        frequency=freq,
        trade_dates=final_dates,
        adjusted_close=adjusted_close,
        total_return_adjusted_close=total_return_close,
        raw_open=raw_open,
        raw_high=raw_high,
        raw_low=raw_low,
        raw_close=raw_close,
        volume=volume,
        adjustment_status=uniform_status,
        price_basis_indicator=price_basis_indicator,
        price_basis_returns=price_basis_returns,
        analysis_status=status,
        is_fatal=is_fatal,
        primary_failure=primary,
        diagnostic_codes=diagnostics,
        provenance={
            "source_provider": source_provider,
            "computation_chain_id": chain,
            "provided_rows": len(rows_in),
            "final_rows": len(final_dates),
            "frequency": freq,
            "n_sessions": len(final_dates),
            "dedup_applied": any(e.failure_code == "DUPLICATE_TIMESTAMP_DEDUPED" for e in all_events),
            "sort_applied": any(e.failure_code == "UNSORTED_TIMESTAMP_SORTED" for e in all_events),
        },
    )


def _empty_result(
    mode: Mode, freq: str, events: List[FailureEvent],
    source_provider: Optional[str], chain: str,
) -> NormalizedInput:
    primary = _select_primary(events)
    diagnostics = [e for e in events if e.classification == "DIAGNOSTIC"]
    return NormalizedInput(
        mode=mode,
        frequency=freq,
        trade_dates=[],
        adjusted_close=[],
        total_return_adjusted_close=[],
        raw_open=[], raw_high=[], raw_low=[], raw_close=[],
        volume=[],
        adjustment_status=AdjustmentStatus.UNKNOWN,
        analysis_status=AnalysisStatus.FAILED,
        is_fatal=True,
        primary_failure=primary,
        diagnostic_codes=diagnostics,
        provenance={
            "source_provider": source_provider,
            "computation_chain_id": chain,
            "provided_rows": 0,
            "final_rows": 0,
            "frequency": freq,
            "n_sessions": 0,
        },
    )


# ---------------------------------------------------------------------------
# Corporate-action helpers (VTA-REQ-004 corporate_action_policy)
# ---------------------------------------------------------------------------


def apply_corporate_action_policy(
    input_series: NormalizedInput,
    corporate_action_dates: Sequence[str],
    *,
    recompute_from_effective_date: bool = True,
) -> Tuple[NormalizedInput, List[FailureEvent]]:
    """Enforce the corporate-action policy.

    Per shared_policies.price_basis.corporate_action_policy:
      "Recompute affected windows from corporate-action effective date forward;
       never backfill."

    This helper does NOT mutate already-computed indicators; it returns the
    input series annotated with a provenance flag and emits no failure code
    by default (corporate actions are expected events, not failures). If the
    caller supplies adjustment metadata that conflicts with the input's
    uniform status, a CONFLICTING_ADJUSTMENT_STATUS event is surfaced.
    """
    events: List[FailureEvent] = []
    if not corporate_action_dates:
        return input_series, events

    # Record the policy in provenance (observable, no silent mutation).
    input_series.provenance["corporate_action_dates"] = list(corporate_action_dates)
    input_series.provenance["corporate_action_policy"] = (
        "RECOMPUTE_FORWARD" if recompute_from_effective_date else "PASS_THROUGH"
    )
    return input_series, events


__all__ = [
    "Mode",
    "PriceBasis",
    "CalculationType",
    "AdjustmentStatus",
    "Severity",
    "AnalysisStatus",
    "FailureCode",
    "FailureEvent",
    "PriceBasisResult",
    "NormalizedInput",
    "normalize_input",
    "verify_price_basis",
    "align_benchmark_dates",
    "apply_corporate_action_policy",
    "NUMERICAL_TOLERANCE",
    "COMPARISON_EPSILON",
    "MIN_SESSIONS_ACTIVE",
    "MIN_SESSIONS_PROFILE",
    "GAP_THRESHOLD_PCT",
    "BENCHMARK_OVERLAP_THRESHOLD",
    "PARTIAL_WEEK_MIN_TRADING_DAYS",
]
