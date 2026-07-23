"""Phase 4R structural validation tests — applicability & export gate (MUT-FUND-019).

8 tests covering status invariant, export gate, applicability decision hash.
"""
import sys, pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "implementation"))

from models import FundamentalRequest, MetricInput, MetricStatus
from applicability.status_policy import derive_decision, status_upgrade_is_valid, REQUIRED_INPUTS
from runner import run_fundamental


def _metric(mid, values, periods=None, **kw):
    n = len(values)
    if periods is None: periods = list(range(2025-n+1, 2026))
    defaults = dict(unit="BILLION_VND", periods=periods, scope="CONSOLIDATED", source_id="t")
    defaults.update(kw)
    return MetricInput(metric_id=mid, values=values, **defaults)


def test_p4r_struct_006_status_incomplete_upgraded_to_valid_blocked():
    """P4R-TEST-STRUCT-006: INPUT_INCOMPLETE cannot be upgraded to VALID."""
    # shares missing -> EPS decision should be INPUT_INCOMPLETE
    req = FundamentalRequest(
        ticker="FPT", periods=[2025],
        metrics={
            "net_income": _metric("net_income", [5000]),
            "equity": _metric("equity", [30000]),
            "total_assets": _metric("total_assets", [60000]),
            "revenue": _metric("revenue", [40000]),
            "shares_outstanding": _metric("shares_outstanding", [None]),  # missing
        },
    )
    res = run_fundamental(req)
    eps = next(m for m in res.output.metric_results if m.metric_id == "EPS_BASIC")
    assert eps.status == MetricStatus.INPUT_INCOMPLETE.value
    assert eps.applicability_decision.decided_status == MetricStatus.INPUT_INCOMPLETE.value
    # Export gate must block it
    assert res.output.downstream_export["EPS_basic"]["export_eligible"] is False


def test_p4r_struct_applicability_decision_hash_stable():
    """Same inputs → same decision hash (reproducibility)."""
    metrics = {
        "net_income": _metric("net_income", [5000]),
        "shares_outstanding": _metric("shares_outstanding", [1.5]),
    }
    d1 = derive_decision("EPS_BASIC", metrics, 2025)
    d2 = derive_decision("EPS_BASIC", metrics, 2025)
    assert d1.decision_hash == d2.decision_hash


def test_p4r_struct_applicability_decision_hash_changes_on_input_change():
    """Different input values → different decision hash."""
    m1 = {"net_income": _metric("net_income", [5000]), "shares_outstanding": _metric("shares_outstanding", [1.5])}
    m2 = {"net_income": _metric("net_income", [6000]), "shares_outstanding": _metric("shares_outstanding", [1.5])}
    d1 = derive_decision("EPS_BASIC", m1, 2025)
    d2 = derive_decision("EPS_BASIC", m2, 2025)
    assert d1.decision_hash != d2.decision_hash


def test_p4r_struct_status_upgrade_is_valid_returns_false_for_incomplete_to_valid():
    """status_upgrade_is_valid detects an illegal upgrade."""
    from applicability.status_policy import ApplicabilityDecision
    decision = ApplicabilityDecision(metric_id="EPS_BASIC", decided_status=MetricStatus.INPUT_INCOMPLETE.value)
    assert status_upgrade_is_valid(decision, MetricStatus.VALID.value) is False


def test_p4r_struct_status_upgrade_is_valid_returns_true_for_complete_to_valid():
    """status_upgrade_is_valid allows VALID when decision is VALID."""
    from applicability.status_policy import ApplicabilityDecision
    decision = ApplicabilityDecision(metric_id="EPS_BASIC", decided_status=MetricStatus.VALID.value)
    assert status_upgrade_is_valid(decision, MetricStatus.VALID.value) is True


def test_p4r_struct_export_gate_blocks_invalid_status():
    """A metric that cannot be computed (zero denominator) is not export-eligible."""
    req = FundamentalRequest(
        ticker="FPT", periods=[2025],
        metrics={
            "net_income": _metric("net_income", [5000]),
            "equity": _metric("equity", [0]),  # zero equity -> ROE cannot compute
            "total_assets": _metric("total_assets", [60000]),
            "revenue": _metric("revenue", [40000]),
            "shares_outstanding": _metric("shares_outstanding", [1.5]),
        },
    )
    res = run_fundamental(req)
    roe = next((m for m in res.output.metric_results if m.metric_id == "ROE"), None)
    assert roe is not None
    # ROE is either ERROR (div by zero) or INPUT_INCOMPLETE (avg=0 short-circuit) —
    # either way it must NOT be VALID/VALID_NEGATIVE.
    assert roe.status not in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value)


def test_p4r_struct_required_inputs_map_complete():
    """All per-share / ratio metrics have required_inputs defined."""
    for mid in ("EPS_BASIC", "EPS_DILUTED", "BVPS", "ROE", "ROA", "NET_PROFIT_MARGIN", "DUPONT_AT", "DUPONT_EM"):
        assert mid in REQUIRED_INPUTS
        assert len(REQUIRED_INPUTS[mid]) >= 2


def test_p4r_struct_applicability_decision_recorded_for_all_material_metrics():
    """Runner records an applicability_decision for every material metric."""
    req = FundamentalRequest(
        ticker="FPT", periods=[2023, 2024, 2025],
        metrics={
            "revenue": _metric("revenue", [35000, 40000, 45000]),
            "net_income": _metric("net_income", [5000, 5500, 6000]),
            "equity": _metric("equity", [30000, 33000, 36000]),
            "total_assets": _metric("total_assets", [60000, 66000, 72000]),
            "shares_outstanding": _metric("shares_outstanding", [1.5, 1.5, 1.5]),
        },
    )
    res = run_fundamental(req)
    assert len(res.output.applicability_decisions) >= 8
    for d in res.output.applicability_decisions:
        assert "metric_id" in d
        assert "decision_hash" in d
