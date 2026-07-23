"""Independent Verifier — vn-fundamental-analysis Phase 4.

Independently recomputes all formulas from raw inputs.
Does NOT call formula_engine — uses separate computation logic.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from models import FundamentalRequest, FundamentalOutput, MetricResult, MetricStatus


@dataclass
class VerificationResult:
    overall_verdict: str = "PENDING"
    passed: int = 0
    failed: int = 0
    mismatches: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    verifier_version: str = "0.1.0-phase4"
    verified_output_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_verdict": self.overall_verdict,
            "passed": self.passed, "failed": self.failed,
            "mismatches": self.mismatches, "warnings": self.warnings,
            "verifier_version": self.verifier_version,
        }


def _independent_eps(npat: float, shares: float) -> Optional[float]:
    """Independent EPS recompute."""
    if shares == 0:
        return None
    return npat / shares


def _independent_bvps(equity: float, shares: float) -> Optional[float]:
    if shares == 0:
        return None
    return equity / shares


def _independent_roe(npat: float, avg_equity: float) -> Optional[float]:
    if avg_equity == 0:
        return None
    return (npat / avg_equity) * 100


def _independent_roa(npat: float, avg_assets: float) -> Optional[float]:
    if avg_assets == 0:
        return None
    return (npat / avg_assets) * 100


def _independent_npm(npat: float, revenue: float) -> Optional[float]:
    if revenue == 0:
        return None
    return npat / revenue


def verify(request: FundamentalRequest, output: FundamentalOutput) -> VerificationResult:
    """Verify output by independent recomputation."""
    result = VerificationResult()
    periods = request.periods
    latest = max(periods) if periods else 0
    metrics = request.metrics

    def check(name: str, expected: Optional[float], actual: Optional[float], tolerance: float = 0.01):
        result.passed += 0  # count will be adjusted
        if expected is None and actual is None:
            result.passed += 1
            return
        if expected is None or actual is None:
            result.failed += 1
            result.mismatches.append({"metric": name, "expected": expected, "actual": actual, "reason": "None mismatch"})
            return
        diff = abs(expected - actual)
        if diff > tolerance:
            result.failed += 1
            result.mismatches.append({"metric": name, "expected": expected, "actual": actual, "diff": diff, "tolerance": tolerance})
        else:
            result.passed += 1

    # Get raw inputs
    npat = metrics.get("net_income", None)
    npat_v = npat.get_value(latest) if npat else None
    rev = metrics.get("revenue", None)
    rev_v = rev.get_value(latest) if rev else None
    eq = metrics.get("equity", None)
    eq_v = eq.get_value(latest) if eq else None
    ta = metrics.get("total_assets", None)
    ta_v = ta.get_value(latest) if ta else None
    sh = metrics.get("shares_outstanding", None)
    sh_v = sh.get_value(latest) if sh else None

    # Compute average balances independently
    eq_vals = eq.values if eq else []
    ta_vals = ta.values if ta else []
    avg_eq = sum(eq_vals[-2:]) / 2 if len(eq_vals) >= 2 else eq_v
    avg_ta = sum(ta_vals[-2:]) / 2 if len(ta_vals) >= 2 else ta_v

    # Recompute and compare
    if npat_v is not None and sh_v is not None and sh_v != 0:
        exp_eps = _independent_eps(npat_v, sh_v)
        act_eps = next((m.value for m in output.metric_results if m.metric_id == "EPS_BASIC"), None)
        check("EPS_basic", exp_eps, act_eps, tolerance=1.0)  # 1 VND tolerance for rounding

    if eq_v is not None and sh_v is not None and sh_v != 0:
        exp_bvps = _independent_bvps(eq_v, sh_v)
        act_bvps = next((m.value for m in output.metric_results if m.metric_id == "BVPS"), None)
        check("BVPS", exp_bvps, act_bvps, tolerance=1.0)

    if npat_v is not None and avg_eq is not None and avg_eq != 0:
        exp_roe = _independent_roe(npat_v, avg_eq)
        act_roe = next((m.value for m in output.metric_results if m.metric_id == "ROE"), None)
        check("ROE", exp_roe, act_roe, tolerance=0.1)

    if npat_v is not None and avg_ta is not None and avg_ta != 0:
        exp_roa = _independent_roa(npat_v, avg_ta)
        act_roa = next((m.value for m in output.metric_results if m.metric_id == "ROA"), None)
        check("ROA", exp_roa, act_roa, tolerance=0.1)

    if npat_v is not None and rev_v is not None and rev_v != 0:
        exp_npm = _independent_npm(npat_v, rev_v)
        act_npm = next((m.value for m in output.metric_results if m.metric_id == "NET_PROFIT_MARGIN"), None)
        check("NPM", exp_npm, act_npm, tolerance=0.0001)

    # DuPont consistency check
    if output.dupont and output.dupont.consistency_status == "CONSISTENT":
        result.passed += 1
    elif output.dupont and output.dupont.consistency_status == "INCONSISTENT":
        result.failed += 1
        result.mismatches.append({"metric": "DUPONT_CONSISTENCY", "status": output.dupont.consistency_status})

    # Downstream export eligibility
    eps_status = output.downstream_export.get("EPS_basic", {}).get("status")
    if eps_status in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value):
        result.passed += 1
    elif eps_status == MetricStatus.INPUT_INCOMPLETE.value:
        result.passed += 1  # Correctly blocked
    else:
        result.failed += 1
        result.mismatches.append({"metric": "EPS_EXPORT_STATUS", "status": eps_status})

    # Verdict
    if result.failed > 0:
        result.overall_verdict = "FAIL"
    else:
        result.overall_verdict = "PASS"

    return result
