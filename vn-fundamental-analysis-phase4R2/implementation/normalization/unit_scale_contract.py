"""Unit-scale contract — Phase 4R2 deterministic scale validation (Blocker 2).

Replaces Phase 4R's plausibility heuristics (EPS < 100, BVPS < 1000) with a
deterministic contract: every normalized value must equal raw_value ×
registered_normalization_factor. Mismatches are hard errors (UNIT_SCALE_MISMATCH).

A ScaleContract binds: raw_value, raw_unit, raw_scale, normalized_value,
normalization_factor, expected_unit, expected_scale, source_metric_id.

Plausibility checks (EPS/BVPS sanity bounds) are demoted to structured warnings
only — they CANNOT cause UNIT_SCALE_MISMATCH.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from models import MetricInput


# Registered normalization factors per raw_scale → expected_scale.
# Collector delivers values in "tỷ VND" (BILLION_VND) and "tỷ shares" (BILLION_SHARES).
# Engine canonical scale is BILLION_VND for money, BILLION_SHARES for counts.
NORMALIZATION_REGISTRY = {
    ("VND", "UNIT"): ("BILLION_VND", 1e-9),         # raw VND unit → tỷ VND
    ("VND", "MILLION"): ("BILLION_VND", 1e-3),       # raw million VND → tỷ VND
    ("VND", "BILLION"): ("BILLION_VND", 1.0),        # raw tỷ VND → tỷ VND (identity)
    ("SHARES", "UNIT"): ("BILLION_SHARES", 1e-9),    # raw unit shares → tỷ shares
    ("SHARES", "MILLION"): ("BILLION_SHARES", 1e-3), # raw million shares → tỷ shares
    ("SHARES", "BILLION"): ("BILLION_SHARES", 1.0),  # raw tỷ shares → tỷ shares (identity)
}

# Default normalization for collector metrics (assumed already canonical if not specified).
DEFAULT_SCALE = {
    "revenue": ("VND", "BILLION"),
    "net_income": ("VND", "BILLION"),
    "equity": ("VND", "BILLION"),
    "total_assets": ("VND", "BILLION"),
    "shares_outstanding": ("SHARES", "BILLION"),
}


@dataclass
class ScaleContract:
    """Per-value scale binding for deterministic unit validation."""
    metric_id: str
    period: int
    raw_value: Optional[float]
    raw_unit: str
    raw_scale: str
    normalization_factor: float
    expected_unit: str
    expected_scale: str
    normalized_value: Optional[float]
    source_metric_id: str = ""
    currency: str = "VND"
    raw_normalized_hash: str = ""

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items()}


def build_scale_contract(metric_id: str, period: int, raw_value: Optional[float],
                         normalized_value: Optional[float],
                         raw_unit: str = "", raw_scale: str = "",
                         source_metric_id: str = "") -> ScaleContract:
    """Build a scale contract for one value of one metric."""
    default_unit, default_scale = DEFAULT_SCALE.get(metric_id, ("VND", "BILLION"))
    ru = raw_unit or default_unit
    rs = raw_scale or default_scale
    key = (ru, rs)
    expected_scale, factor = NORMALIZATION_REGISTRY.get(key, (rs, 1.0))
    return ScaleContract(
        metric_id=metric_id, period=period,
        raw_value=raw_value, raw_unit=ru, raw_scale=rs,
        normalization_factor=factor,
        expected_unit=ru, expected_scale=expected_scale,
        normalized_value=normalized_value,
        source_metric_id=source_metric_id or metric_id,
    )


def validate_scale_contract(contract: ScaleContract) -> Tuple[bool, Optional[str]]:
    """Deterministic check: normalized_value must equal raw_value × normalization_factor.

    Returns (ok, error_code).
    - MISSING_REPLACED_WITH_ZERO if raw is None but normalized is 0.0 (hard error, MUT-FUND-018).
    - UNIT_SCALE_MISMATCH if normalized ≠ raw × factor (beyond tolerance).
    - None values (both None): ok (missing handled by applicability).
    """
    # MUT-FUND-018: raw None but normalized 0.0 = silent missing→zero substitution
    if contract.raw_value is None and contract.normalized_value is not None:
        if contract.normalized_value == 0.0:
            return False, "MISSING_REPLACED_WITH_ZERO"
        return False, "MISSING_INPUT_HAS_VALUE"  # raw missing but normalized non-zero
    if contract.raw_value is None and contract.normalized_value is None:
        return True, None  # missing handled elsewhere
    if contract.normalized_value is None:
        return True, None  # raw present, normalized absent (engine chose INPUT_INCOMPLETE)
    expected_normalized = contract.raw_value * contract.normalization_factor
    # Tolerance for float rounding
    if abs(expected_normalized - contract.normalized_value) > 1e-9 * max(1.0, abs(expected_normalized)):
        return False, "UNIT_SCALE_MISMATCH"
    return True, None


def validate_metric_scale_contracts(metric: MetricInput, periods: List[int]) -> List[Tuple[int, bool, Optional[str], ScaleContract]]:
    """Validate scale contracts for all periods of a metric.

    Returns list of (period, ok, error_code, contract).
    raw_value comes from metric.raw_values (or falls back to values if raw_values empty).
    normalized_value is metric.values (the canonical tỷ-scale value the engine uses).
    """
    results = []
    for p in periods:
        # Read raw (pre-normalization) — falls back to values if raw_values empty (identity)
        raw = metric.get_raw_value(p)
        normalized = metric.get_value(p)
        # Determine the raw_unit/raw_scale: prefer metric-level, else default by metric_id
        ru = metric.raw_unit or DEFAULT_SCALE.get(metric.metric_id, ("VND", "BILLION"))[0]
        rs = metric.raw_scale or DEFAULT_SCALE.get(metric.metric_id, ("VND", "BILLION"))[1]
        contract = build_scale_contract(metric.metric_id, p, raw, normalized,
                                         raw_unit=ru, raw_scale=rs,
                                         source_metric_id=metric.get_binding(p, "source_metric_ids") or metric.metric_id)
        ok, err = validate_scale_contract(contract)
        results.append((p, ok, err, contract))
    return results


# === Plausibility checks (WARNING only, never hard-fail) ===

PLAUSIBILITY_BOUNDS = {
    "EPS": (100, 1_000_000),       # VND/share — below 100 or above 1M = unusual
    "BVPS": (1000, 1_000_000),     # VND/share
}


def plausibility_warning(metric_id: str, value: Optional[float]) -> Optional[str]:
    """Return a warning string if value is outside plausibility bounds, else None.

    This is a WARNING, not an error. It cannot cause UNIT_SCALE_MISMATCH.
    """
    if value is None:
        return None
    bounds = PLAUSIBILITY_BOUNDS.get(metric_id)
    if bounds is None:
        return None
    lo, hi = bounds
    if abs(value) > hi:
        return f"{metric_id}_OUT_OF_SANITY_RANGE_HIGH: |{value}| > {hi}"
    if 0 < abs(value) < lo:
        return f"{metric_id}_OUT_OF_SANITY_RANGE_LOW: |{value}| < {lo} (possible but unusual)"
    return None
