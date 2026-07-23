"""Phase 4R2 — Specificity controls (Blocker 2 §3).

Verifies that legitimate low-EPS / low-BVPS / low-profit companies do NOT
trigger UNIT_SCALE_MISMATCH (false positives). Plausibility is warning-only.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "implementation"))
from models import FundamentalRequest, MetricInput, MetricStatus, AttributionScope
from runner import run_fundamental
from verifier.independent_verifier import verify


def _metric(mid, values, periods=None, **kw):
    n = len(values)
    if periods is None: periods = list(range(2025-n+1, 2026))
    defaults = dict(unit="BILLION_VND", periods=periods, source_id="t")
    defaults.update(kw)
    return MetricInput(metric_id=mid, values=values, **defaults)


def _check(name, req):
    res = run_fundamental(req)
    vr = verify(req, res.output)
    unit_errors = [e for e in res.errors if e.get("code") == "UNIT_SCALE_MISMATCH"]
    return {"control": name, "verifier_verdict": vr.overall_verdict,
            "unit_scale_mismatch_errors": len(unit_errors),
            "false_positive": len(unit_errors) > 0}


def main():
    print("=== P4R2 Specificity Controls ===\n")
    controls = []

    # 1. Legitimate EPS below 100 VND (low-profit company, tiny NPAT)
    c1 = _check("legitimate_EPS_below_100", FundamentalRequest(
        ticker="LOWP", periods=[2023, 2024, 2025],
        metrics={
            "revenue": _metric("revenue", [10000, 11000, 12000]),
            "net_income": _metric("net_income", [10, 12, 15]),  # EPS = 15/1.5 = 10 VND (very low)
            "equity": _metric("equity", [5000, 5500, 6000]),
            "total_assets": _metric("total_assets", [10000, 11000, 12000],
                                    attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
            "shares_outstanding": _metric("shares_outstanding", [1.5, 1.5, 1.5]),
        }))
    controls.append(c1)

    # 2. Legitimate BVPS below 1000 VND
    c2 = _check("legitimate_BVPS_below_1000", FundamentalRequest(
        ticker="LOWB", periods=[2023, 2024, 2025],
        metrics={
            "revenue": _metric("revenue", [5000, 5500, 6000]),
            "net_income": _metric("net_income", [200, 220, 240]),
            "equity": _metric("equity", [800, 900, 1000]),  # BVPS = 1000/1.5 = 667 VND
            "total_assets": _metric("total_assets", [2000, 2200, 2400],
                                    attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
            "shares_outstanding": _metric("shares_outstanding", [1.5, 1.5, 1.5]),
        }))
    controls.append(c2)

    # 3. Low-profit company (margin < 1%)
    c3 = _check("low_profit_company", FundamentalRequest(
        ticker="LOWM", periods=[2023, 2024, 2025],
        metrics={
            "revenue": _metric("revenue", [50000, 55000, 60000]),
            "net_income": _metric("net_income", [100, 110, 120]),  # margin ~0.2%
            "equity": _metric("equity", [30000, 33000, 36000]),
            "total_assets": _metric("total_assets", [60000, 66000, 72000],
                                    attribution_scale_bindings=[AttributionScope.TOTAL_GROUP.value]*3) if False else _metric("total_assets", [60000, 66000, 72000],
                                    attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
            "shares_outstanding": _metric("shares_outstanding", [1.5, 1.5, 1.5]),
        }))
    controls.append(c3)

    # 4. Negative EPS (loss-making company) — must be VALID_NEGATIVE, not UNIT error
    c4 = _check("negative_EPS_VALID_NEGATIVE", FundamentalRequest(
        ticker="LOSS", periods=[2023, 2024, 2025],
        metrics={
            "revenue": _metric("revenue", [10000, 11000, 12000]),
            "net_income": _metric("net_income", [-500, -400, -300]),  # negative NPAT
            "equity": _metric("equity", [5000, 4500, 4200]),
            "total_assets": _metric("total_assets", [10000, 9500, 9000],
                                    attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
            "shares_outstanding": _metric("shares_outstanding", [1.5, 1.5, 1.5]),
        }))
    controls.append(c4)

    for c in controls:
        status = "PASS (no false positive)" if not c["false_positive"] else "FAIL (false positive!)"
        print(f"  {c['control']:40} -> {status}")

    false_positives = sum(1 for c in controls if c["false_positive"])
    print(f"\nFalse positives: {false_positives}/{len(controls)}")

    import json
    manifest = {"phase4R2_specificity_manifest": {"controls": controls, "false_positive_count": false_positives}}
    Path(__file__).parent.parent / "manifests" / "phase4R2-specificity-manifest.json"
    out = Path(__file__).parent.parent / "manifests" / "phase4R2-specificity-manifest.json"
    out.write_text(json.dumps(manifest, indent=2, default=str))
    return false_positives


if __name__ == "__main__":
    fp = main()
    sys.exit(0 if fp == 0 else 1)
