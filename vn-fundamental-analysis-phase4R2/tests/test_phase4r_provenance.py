"""Phase 4R provenance tests (MUT-FUND-031).

10 tests covering ProvenanceRecord completeness, hash binding, staleness detection,
runner-side attachment, and verifier-side detection.
"""
import sys, pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "implementation"))

from models import FundamentalRequest, MetricInput, MetricStatus, ProvenanceRecord
from provenance.provenance_engine import build_provenance, provenance_is_complete, provenance_hash_matches
from runner import run_fundamental


def _metric(mid, values, periods=None, **kw):
    n = len(values)
    if periods is None: periods = list(range(2025-n+1, 2026))
    defaults = dict(unit="BILLION_VND", periods=periods, scope="CONSOLIDATED", source_id="t")
    defaults.update(kw)
    return MetricInput(metric_id=mid, values=values, **defaults)


def test_p4r_prov_001_provenance_removed_from_eps_detected():
    """P4R-TEST-PROV-001: VALID EPS without provenance → export blocked + error."""
    # Build a clean request first
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
    eps = next(m for m in res.output.metric_results if m.metric_id == "EPS_BASIC")
    # Clean case: provenance present
    assert eps.provenance_record is not None
    assert provenance_is_complete(eps.provenance_record) is True

    # Now mutate: strip provenance from EPS but keep VALID status
    eps.provenance_record = None
    # Re-verify
    from verifier.independent_verifier import verify
    vr = verify(req, res.output)
    # Verifier should flag PROVENANCE_MISSING
    assert vr.overall_verdict == "FAIL"
    assert any("PROVENANCE_MISSING" in str(m) for m in vr.mismatches)


def test_p4r_prov_build_provenance_complete_record():
    metrics = {
        "net_income": _metric("net_income", [5000], source_metric_ids=["ni_2025"]),
        "shares_outstanding": _metric("shares_outstanding", [1.5], source_metric_ids=["sh_2025"]),
    }
    rec = build_provenance("EPS_BASIC", metrics, 2025, formula_input_ids=["net_income", "shares_outstanding"])
    assert rec.source_id != ""
    assert rec.collector_metric_id == "ni_2025"
    assert rec.raw_evidence_hash != ""
    assert rec.provenance_hash != ""
    assert provenance_is_complete(rec) is True


def test_p4r_prov_provenance_hash_matches_stable():
    metrics = {
        "net_income": _metric("net_income", [5000]),
        "shares_outstanding": _metric("shares_outstanding", [1.5]),
    }
    rec1 = build_provenance("EPS_BASIC", metrics, 2025)
    rec2 = build_provenance("EPS_BASIC", metrics, 2025)
    assert rec1.provenance_hash == rec2.provenance_hash
    assert provenance_hash_matches(rec1, rec2.provenance_hash) is True


def test_p4r_prov_provenance_hash_changes_on_input_change():
    m1 = {"net_income": _metric("net_income", [5000]), "shares_outstanding": _metric("shares_outstanding", [1.5])}
    m2 = {"net_income": _metric("net_income", [6000]), "shares_outstanding": _metric("shares_outstanding", [1.5])}
    rec1 = build_provenance("EPS_BASIC", m1, 2025)
    rec2 = build_provenance("EPS_BASIC", m2, 2025)
    assert rec1.provenance_hash != rec2.provenance_hash


def test_p4r_prov_stale_hash_detected():
    metrics = {"net_income": _metric("net_income", [5000]), "shares_outstanding": _metric("shares_outstanding", [1.5])}
    rec = build_provenance("EPS_BASIC", metrics, 2025)
    # Stale hash -> mismatch
    assert provenance_hash_matches(rec, "stale_hash_value") is False


def test_p4r_prov_incomplete_record_detected():
    empty = ProvenanceRecord()
    assert provenance_is_complete(empty) is False


def test_p4r_prov_runner_attaches_provenance_to_all_valid_metrics():
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
    for m in res.output.metric_results:
        if m.status in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value):
            assert m.provenance_record is not None, f"{m.metric_id} missing provenance"
            assert provenance_is_complete(m.provenance_record)


def test_p4r_prov_export_carries_provenance_hash():
    req = FundamentalRequest(
        ticker="FPT", periods=[2025],
        metrics={
            "revenue": _metric("revenue", [40000]),
            "net_income": _metric("net_income", [5000]),
            "equity": _metric("equity", [30000]),
            "total_assets": _metric("total_assets", [60000]),
            "shares_outstanding": _metric("shares_outstanding", [1.5]),
        },
    )
    res = run_fundamental(req)
    eps_export = res.output.downstream_export["EPS_basic"]
    assert eps_export["provenance_hash"] is not None
    assert eps_export["export_eligible"] is True


def test_p4r_prov_collector_metric_id_from_source_metric_ids_binding():
    metrics = {
        "net_income": _metric("net_income", [5000], source_metric_ids=["collector_ni_2025"]),
    }
    rec = build_provenance("ROE", metrics, 2025)
    assert rec.collector_metric_id == "collector_ni_2025"


def test_p4r_prov_provenance_carries_formula_input_ids():
    metrics = {
        "net_income": _metric("net_income", [5000]),
        "shares_outstanding": _metric("shares_outstanding", [1.5]),
    }
    rec = build_provenance("EPS_BASIC", metrics, 2025, formula_input_ids=["net_income", "shares_outstanding"])
    assert "net_income" in rec.formula_input_ids
    assert "shares_outstanding" in rec.formula_input_ids
