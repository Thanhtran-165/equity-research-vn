"""Denominator basis policy — Phase 4R structural validation (MUT-FUND-013 / 016 / 026).

Ensures balance-sheet denominators are bound to DenominatorBasis and that the
average-vs-ending distinction is explicit. Ending-balance fallback is only
legal with a registered rule_id + warning + quality downgrade + calculation trace.
"""
from __future__ import annotations
from typing import List, Optional, Tuple
from models import MetricInput, DenominatorBasis


# Per-ratio metric -> denominator basis that the input MUST carry.
RATIO_DENOMINATOR_REQUIREMENTS = {
    # metric_id : (denominator_role, required_basis_prefix, fallback_allowed_with_warning)
    "ROE":        ("equity",      "AVERAGE_COMMON_EQUITY",  True),
    "ROA":        ("total_assets","AVERAGE_TOTAL_ASSETS",   True),
    "DUPONT_EM":  ("equity",      "AVERAGE_COMMON_EQUITY",  True),  # EM denominator is equity
    "DUPONT_AT":  ("total_assets","AVERAGE_TOTAL_ASSETS",   True),  # AT denominator is assets
}


def normalize_denominator_basis_binding(metric: MetricInput, default: str) -> Tuple[List[str], List[str]]:
    """Pad denominator_basis_bindings to len(values) with `default`; warn on each pad."""
    n = len(metric.values)
    bindings = list(metric.denominator_basis_bindings)
    warnings: List[str] = []
    while len(bindings) < n:
        bindings.append(default)
        warnings.append(f"STRUCTURAL_BINDING_DEFAULTED: denominator_basis defaulted to {default} (slot {len(bindings)-1})")
    return bindings[:n], warnings


def validate_denominator_basis(metric_id: str, denominator_metric: MetricInput, year: int,
                               fallback_rule_attached: bool = False) -> Tuple[bool, Optional[str], List[str]]:
    """Check denominator metric carries the required basis for the ratio.

    Returns (ok, error_code, warnings).
    - If basis is AVERAGE_* (matches required): ok.
    - If basis is ENDING_* (fallback) AND fallback_rule_attached=True: ok with warning.
    - If basis is ENDING_* AND fallback_rule_attached=False: PERIOD_MISMATCH
      (silent ending substitution without registered fallback rule).
    - Otherwise: PERIOD_MISMATCH.
    """
    req = RATIO_DENOMINATOR_REQUIREMENTS.get(metric_id)
    if req is None:
        return True, None, []
    _, required_prefix, fallback_allowed = req
    if year not in denominator_metric.periods:
        return False, "PERIOD_OUT_OF_RANGE", []
    idx = denominator_metric.periods.index(year)
    bindings, pad_warnings = normalize_denominator_basis_binding(denominator_metric, default=required_prefix)
    if idx >= len(bindings):
        return False, "PERIOD_MISMATCH", pad_warnings
    bound = bindings[idx]
    warnings = list(pad_warnings)
    if bound == required_prefix:
        return True, None, warnings
    # Ending-balance fallback path — only ok if caller attached fallback rule
    if fallback_allowed and bound.startswith("ENDING_") and bound.replace("ENDING_", "AVERAGE_") == required_prefix:
        if fallback_rule_attached:
            warnings.append(f"DENOMINATOR_ENDING_BALANCE_FALLBACK: {metric_id} using {bound} instead of {required_prefix} (rule attached)")
            return True, None, warnings
        else:
            warnings.append(f"DENOMINATOR_ENDING_BALANCE_FALLBACK_WITHOUT_RULE: {metric_id} using {bound} without fallback_rule_id")
            return False, "PERIOD_MISMATCH", warnings
    return False, "PERIOD_MISMATCH", warnings


def requires_fallback_rule(metric_id: str, denominator_metric: MetricInput, year: int) -> bool:
    """True if the bound basis is ENDING_* (fallback path) — caller must attach rule_id + quality downgrade."""
    ok, _, warnings = validate_denominator_basis(metric_id, denominator_metric, year)
    if not ok:
        return False
    return any("ENDING_BALANCE_FALLBACK" in w for w in warnings)
