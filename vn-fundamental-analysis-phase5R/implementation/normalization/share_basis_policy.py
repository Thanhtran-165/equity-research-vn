"""Share basis policy — Phase 4R structural validation (/ 009).

Ensures each per-share metric's shares input is explicitly bound to a ShareBasis
and that the bound basis is consistent with the declared EPS basis.
"""
from __future__ import annotations
from typing import List, Optional, Tuple
from models import MetricInput, ShareBasis


# Per-share metric -> required shares basis family.
# EPS requires WEIGHTED_AVERAGE_* shares (period-end is NOT acceptable silently).
# BVPS uses period-end shares (any *BASIC/*DILUTED PERIOD_END allowed, weighted ok).
PER_SHARE_REQUIREMENTS = {
    "EPS_BASIC":   {"allowed": {ShareBasis.WEIGHTED_AVERAGE_BASIC.value}, "must_contain": "BASIC"},
    "EPS_DILUTED": {"allowed": {ShareBasis.WEIGHTED_AVERAGE_DILUTED.value}, "must_contain": "DILUTED"},
    "BVPS":        {"allowed": {ShareBasis.PERIOD_END_BASIC.value, ShareBasis.PERIOD_END_DILUTED.value, ShareBasis.WEIGHTED_AVERAGE_BASIC.value, ShareBasis.WEIGHTED_AVERAGE_DILUTED.value}, "must_contain": None},
}


def normalize_share_basis_binding(metric: MetricInput, default: str = ShareBasis.WEIGHTED_AVERAGE_BASIC.value) -> Tuple[List[str], List[str]]:
    """Return (resolved_bindings, warnings).

    If metric.share_basis_bindings is shorter than values, pad with `default`
    and emit STRUCTURAL_BINDING_DEFAULTED for each padded slot.
    """
    n = len(metric.values)
    bindings = list(metric.share_basis_bindings)
    warnings: List[str] = []
    while len(bindings) < n:
        bindings.append(default)
        warnings.append(f"STRUCTURAL_BINDING_DEFAULTED: share_basis defaulted to {default} (slot {len(bindings)-1})")
    return bindings[:n], warnings


def validate_share_basis_for_metric(metric_id: str, shares_metric: MetricInput, year: int) -> Tuple[bool, Optional[str]]:
    """Check that the shares metric's bound basis at `year` is allowed for `metric_id`.

    Returns (ok, error_code).
    """
    req = PER_SHARE_REQUIREMENTS.get(metric_id)
    if req is None:
        return True, None
    bindings, _ = normalize_share_basis_binding(shares_metric)
    if year not in shares_metric.periods:
        return False, "PERIOD_OUT_OF_RANGE"
    idx = shares_metric.periods.index(year)
    if idx >= len(bindings):
        return False, "SHARE_BASIS_MISMATCH"
    bound = bindings[idx]
    if bound not in req["allowed"]:
        # Distinguish EPS_BASIS_MISMATCH (basic vs diluted swap) from generic SHARE_BASIS_MISMATCH.
        if req["must_contain"] and req["must_contain"] not in bound:
            return False, "EPS_BASIS_MISMATCH"
        return False, "SHARE_BASIS_MISMATCH"
    return True, None
