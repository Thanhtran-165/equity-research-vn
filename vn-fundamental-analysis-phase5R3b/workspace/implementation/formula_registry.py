"""Formula input identity registry — generic, mutation-agnostic (Phase 4R3).

Registers the canonical numerator/denominator metric_id for each formula.
The verifier independently checks that a MetricResult's formula_input_metric_ids
match the registered canonical inputs. No mutation IDs, no markers.

This catches MUT-015 (operating_income substituted for net_income in NPM)
via generic FORMULA_INPUT_DEFINITION_MISMATCH — the runner emits the actual
numerator metric_id it used, the verifier compares against this registry.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple


# Canonical formula input definitions.
# formula_id -> {numerator_metric_id, denominator_metric_id}
CANONICAL_FORMULA_INPUTS: Dict[str, Dict[str, str]] = {
    "EPS-BASIC-v1.0.0":     {"numerator": "net_income", "denominator": "shares_outstanding"},
    "EPS-DILUTED-v1.0.0":   {"numerator": "net_income", "denominator": "shares_outstanding"},
    "BVPS-v1.0.0":          {"numerator": "equity", "denominator": "shares_outstanding"},
    "ROE-v1.0.0":           {"numerator": "net_income", "denominator": "equity"},
    "ROA-v1.0.0":           {"numerator": "net_income", "denominator": "total_assets"},
    "NET-PROFIT-MARGIN-v1.0.0": {"numerator": "net_income", "denominator": "revenue"},
    "DUPONT-AT-v1.0.0":     {"numerator": "revenue", "denominator": "total_assets"},
    "DUPONT-EM-v1.0.0":     {"numerator": "total_assets", "denominator": "equity"},
}


def get_canonical_inputs(formula_id: str) -> Optional[Dict[str, str]]:
    """Return the registered canonical numerator/denominator for a formula_id."""
    return CANONICAL_FORMULA_INPUTS.get(formula_id)


def check_formula_input_identity(formula_id: str,
                                  observed_numerator_metric_id: Optional[str],
                                  observed_denominator_metric_id: Optional[str]) -> Tuple[bool, Optional[str], Optional[str]]:
    """Check that observed formula inputs match the registered canonical inputs.

    Returns (ok, error_code, expected_field).
    - FORMULA_INPUT_DEFINITION_MISMATCH if numerator or denominator metric_id
      differs from the registered canonical input.
    """
    canonical = get_canonical_inputs(formula_id)
    if canonical is None:
        return True, None, None  # unregistered formula — no check
    if observed_numerator_metric_id is not None and observed_numerator_metric_id != canonical["numerator"]:
        return False, "FORMULA_INPUT_DEFINITION_MISMATCH", f"numerator: expected {canonical['numerator']}, got {observed_numerator_metric_id}"
    if observed_denominator_metric_id is not None and observed_denominator_metric_id != canonical["denominator"]:
        return False, "FORMULA_INPUT_DEFINITION_MISMATCH", f"denominator: expected {canonical['denominator']}, got {observed_denominator_metric_id}"
    return True, None, None


def list_registered_formulas() -> List[str]:
    return list(CANONICAL_FORMULA_INPUTS.keys())
