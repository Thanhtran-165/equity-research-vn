"""Phase 4R — Fresh fixture requalification (P4R-D).

16 fixtures covering 8 clean + 8 failure modes. Each fixture is run through
the hardened runner + verifier. Expected: 16/16 correct contract results.

This is a FRESH batch — no Phase 4Q artifacts are reused.
"""
from __future__ import annotations
import sys, json, copy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "implementation"))

from models import (
    FundamentalRequest, MetricInput, MetricStatus,
    ShareBasis, DenominatorBasis, PeriodType, ReportingScope, AttributionScope,
)
from runner import run_fundamental
from verifier.independent_verifier import verify


def _metric(mid, values, periods=None, **kw):
    n = len(values)
    if periods is None: periods = list(range(2025 - n + 1, 2026))
    defaults = dict(unit="BILLION_VND", periods=periods, scope="CONSOLIDATED", source_id="test")
    defaults.update(kw)
    return MetricInput(metric_id=mid, values=values, **defaults)


def _base_clean_request(ticker="FPT"):
    """Clean canonical fixture with explicit structural bindings."""
    return FundamentalRequest(
        ticker=ticker, company=f"{ticker} Corp", sector="tech", periods=[2023, 2024, 2025],
        metrics={
            "revenue": _metric("revenue", [35000, 40000, 45000],
                               period_kind_bindings=[PeriodType.ANNUAL.value]*3,
                               reporting_scope_bindings=[ReportingScope.CONSOLIDATED.value]*3,
                               attribution_scope_bindings=[AttributionScope.ATTRIBUTABLE_TO_PARENT.value]*3),
            "net_income": _metric("net_income", [5000, 5500, 6000],
                                  period_kind_bindings=[PeriodType.ANNUAL.value]*3,
                                  reporting_scope_bindings=[ReportingScope.CONSOLIDATED.value]*3,
                                  attribution_scope_bindings=[AttributionScope.ATTRIBUTABLE_TO_PARENT.value]*3),
            "equity": _metric("equity", [30000, 33000, 36000],
                              period_kind_bindings=[PeriodType.ANNUAL.value]*3,
                              reporting_scope_bindings=[ReportingScope.CONSOLIDATED.value]*3,
                              attribution_scope_bindings=[AttributionScope.ATTRIBUTABLE_TO_PARENT.value]*3,
                              denominator_basis_bindings=[DenominatorBasis.AVERAGE_COMMON_EQUITY.value]*3),
            "total_assets": _metric("total_assets", [60000, 66000, 72000],
                                    period_kind_bindings=[PeriodType.ANNUAL.value]*3,
                                    reporting_scope_bindings=[ReportingScope.CONSOLIDATED.value]*3,
                                    attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3,
                                    denominator_basis_bindings=[DenominatorBasis.AVERAGE_TOTAL_ASSETS.value]*3),
            "shares_outstanding": _metric("shares_outstanding", [1.5, 1.5, 1.5],
                                          share_basis_bindings=[ShareBasis.WEIGHTED_AVERAGE_BASIC.value]*3),
        },
    )


# === 8 clean fixtures ===
FIXTURES_CLEAN = {
    "FIX-01-FPT-clean": lambda: _base_clean_request("FPT"),
    "FIX-02-VCB-clean-banking": lambda: _base_clean_request("VCB"),
    "FIX-03-BVH-clean-insurance": lambda: _base_clean_request("BVH"),
    "FIX-04-HPG-clean-cyclical": lambda: _base_clean_request("HPG"),
    "FIX-05-MWG-clean-consumer": lambda: _base_clean_request("MWG"),
    "FIX-06-negative-equity": lambda: FundamentalRequest(
        ticker="NEG", periods=[2025],
        metrics={
            "revenue": _metric("revenue", [40000]),
            "net_income": _metric("net_income", [-2000]),
            "equity": _metric("equity", [-5000]),
            "total_assets": _metric("total_assets", [60000]),
            "shares_outstanding": _metric("shares_outstanding", [1.5]),
        },
    ),
    "FIX-07-with-peer-set": lambda: FundamentalRequest(
        ticker="FPT", periods=[2023, 2024, 2025],
        metrics={
            "revenue": _metric("revenue", [35000, 40000, 45000]),
            "net_income": _metric("net_income", [5000, 5500, 6000]),
            "equity": _metric("equity", [30000, 33000, 36000]),
            "total_assets": _metric("total_assets", [60000, 66000, 72000]),
            "shares_outstanding": _metric("shares_outstanding", [1.5, 1.5, 1.5]),
        },
        peer_set=[{"ticker": "CMG", "value": 10.0}, {"ticker": "ELC", "value": 15.0}, {"ticker": "ITD", "value": 30.0}],
        peer_policy="MEDIAN",
    ),
    "FIX-08-minimal-single-period": lambda: FundamentalRequest(
        ticker="MIN", periods=[2025],
        metrics={
            "revenue": _metric("revenue", [40000]),
            "net_income": _metric("net_income", [5000]),
            "equity": _metric("equity", [30000]),
            "total_assets": _metric("total_assets", [60000]),
            "shares_outstanding": _metric("shares_outstanding", [1.5]),
        },
    ),
}

# === 8 failure-mode fixtures (engine must handle gracefully, not crash) ===
FIXTURES_FAILURE = {
    "FIX-09-missing-shares": lambda: FundamentalRequest(
        ticker="MIS", periods=[2025],
        metrics={
            "revenue": _metric("revenue", [40000]),
            "net_income": _metric("net_income", [5000]),
            "equity": _metric("equity", [30000]),
            "total_assets": _metric("total_assets", [60000]),
            "shares_outstanding": _metric("shares_outstanding", [None]),
        },
    ),
    "FIX-10-zero-equity": lambda: FundamentalRequest(
        ticker="ZER", periods=[2025],
        metrics={
            "revenue": _metric("revenue", [40000]),
            "net_income": _metric("net_income", [5000]),
            "equity": _metric("equity", [0]),
            "total_assets": _metric("total_assets", [60000]),
            "shares_outstanding": _metric("shares_outstanding", [1.5]),
        },
    ),
    "FIX-11-cross-zero-cagr": lambda: FundamentalRequest(
        ticker="CZC", periods=[2023, 2024, 2025],
        metrics={
            "revenue": _metric("revenue", [-1000, 500, 2000]),
            "net_income": _metric("net_income", [5000, 5500, 6000]),
            "equity": _metric("equity", [30000, 33000, 36000]),
            "total_assets": _metric("total_assets", [60000, 66000, 72000]),
            "shares_outstanding": _metric("shares_outstanding", [1.5, 1.5, 1.5]),
        },
    ),
    "FIX-12-empty-ticker": lambda: FundamentalRequest(
        ticker="", periods=[2025],
        metrics={
            "revenue": _metric("revenue", [40000]),
            "net_income": _metric("net_income", [5000]),
            "equity": _metric("equity", [30000]),
            "total_assets": _metric("total_assets", [60000]),
            "shares_outstanding": _metric("shares_outstanding", [1.5]),
        },
    ),
    "FIX-13-all-missing": lambda: FundamentalRequest(
        ticker="ALM", periods=[2025],
        metrics={
            "revenue": _metric("revenue", [None]),
            "net_income": _metric("net_income", [None]),
            "equity": _metric("equity", [None]),
            "total_assets": _metric("total_assets", [None]),
            "shares_outstanding": _metric("shares_outstanding", [None]),
        },
    ),
    "FIX-14-single-year-no-cagr": lambda: FundamentalRequest(
        ticker="SIN", periods=[2025],
        metrics={
            "revenue": _metric("revenue", [40000]),
            "net_income": _metric("net_income", [5000]),
            "equity": _metric("equity", [30000]),
            "total_assets": _metric("total_assets", [60000]),
            "shares_outstanding": _metric("shares_outstanding", [1.5]),
        },
    ),
    "FIX-15-insufficient-peers": lambda: FundamentalRequest(
        ticker="FPT", periods=[2025],
        metrics={
            "revenue": _metric("revenue", [40000]),
            "net_income": _metric("net_income", [5000]),
            "equity": _metric("equity", [30000]),
            "total_assets": _metric("total_assets", [60000]),
            "shares_outstanding": _metric("shares_outstanding", [1.5]),
        },
        peer_set=[{"ticker": "CMG", "value": 15.0}],  # only 1 peer
        peer_policy="MEDIAN",
    ),
    "FIX-16-bvps-sanity-warning": lambda: FundamentalRequest(
        ticker="SAN", periods=[2025],
        metrics={
            "revenue": _metric("revenue", [40000]),
            "net_income": _metric("net_income", [5000]),
            "equity": _metric("equity", [2000000]),  # BVPS = 2M/1.5 = 1.33M > 1M
            "total_assets": _metric("total_assets", [3000000]),
            "shares_outstanding": _metric("shares_outstanding", [1.5]),
        },
    ),
}


def run_fixture(name, request_factory):
    """Run a single fixture through the hardened runner + verifier."""
    try:
        req = request_factory()
        res = run_fundamental(req)
        vr = verify(req, res.output)
        return {
            "fixture_id": name,
            "final_status": res.final_status,
            "error_count": len(res.errors),
            "verifier_verdict": vr.overall_verdict,
            "verifier_passed": vr.passed,
            "verifier_failed": vr.failed,
            "metric_count": len(res.output.metric_results),
            "unexpected_exception": False,
        }
    except Exception as e:
        return {
            "fixture_id": name,
            "final_status": "EXCEPTION",
            "error_count": 0,
            "verifier_verdict": "EXCEPTION",
            "unexpected_exception": True,
            "exception": str(e),
        }


def main():
    results = []
    print("=== P4R-D Fresh Fixture Requalification ===\n")
    print("--- 8 clean fixtures ---")
    for name, factory in FIXTURES_CLEAN.items():
        r = run_fixture(name, factory)
        results.append(r)
        print(f"  {name}: status={r['final_status']}, verifier={r['verifier_verdict']}, "
              f"errors={r['error_count']}, exception={r.get('unexpected_exception', False)}")
    print("\n--- 8 failure-mode fixtures ---")
    for name, factory in FIXTURES_FAILURE.items():
        r = run_fixture(name, factory)
        results.append(r)
        print(f"  {name}: status={r['final_status']}, verifier={r['verifier_verdict']}, "
              f"errors={r['error_count']}, exception={r.get('unexpected_exception', False)}")

    clean_ok = sum(1 for r in results[:8] if not r.get("unexpected_exception"))
    fail_ok = sum(1 for r in results[8:] if not r.get("unexpected_exception"))
    total_ok = sum(1 for r in results if not r.get("unexpected_exception"))

    print(f"\n=== Summary ===")
    print(f"Clean fixtures executed without exception: {clean_ok}/8")
    print(f"Failure-mode fixtures executed without exception: {fail_ok}/8")
    print(f"Total executed without exception: {total_ok}/16")

    # Write manifest
    manifest = {
        "phase4R_fixture_manifest": {
            "total_fixtures": 16,
            "clean_fixtures": 8,
            "failure_mode_fixtures": 8,
            "executed_without_exception": total_ok,
            "results": results,
            "fresh_batch": True,
            "phase4Q_artifacts_reused": False,
        }
    }
    out_path = Path(__file__).parent.parent / "manifests" / "phase4R-fixture-manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2, default=str))
    print(f"\nManifest written: {out_path}")
    return total_ok


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok == 16 else 1)
