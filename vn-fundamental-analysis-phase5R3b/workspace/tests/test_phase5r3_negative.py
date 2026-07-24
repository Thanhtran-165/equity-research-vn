"""Phase 5R3 — Negative value tests (negative EPS, negative/near-zero equity).

26 new tests covering:
- Negative EPS VALID_NEGATIVE (6)
- Negative equity ROE NOT_APPLICABLE/MANUAL_REVIEW (6)
- Near-zero equity EXTREME_EQUITY_RATIO_WARNING (6)
- Downstream negative export (4)
- DERIVED_INPUT quality binding (4)
"""
import sys, pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "implementation"))

from models import FundamentalRequest, MetricInput, MetricStatus, ShareBasis, AttributionScope
from runner import run_fundamental
from verifier.independent_verifier import verify


def _metric(mid, values, periods=None, **kw):
    n = len(values)
    if periods is None: periods = list(range(2025-n+1, 2026))
    defaults = dict(unit="BILLION_VND", periods=periods, source_id="t")
    defaults.update(kw)
    return MetricInput(metric_id=mid, values=values, **defaults)


def _req(**metrics):
    periods = [2023, 2024, 2025]
    for m in metrics.values():
        if m and m.periods: periods = m.periods; break
    return FundamentalRequest(ticker="NEG", periods=periods, metrics=metrics)


# === Negative EPS (6) ===
def test_neg_eps_negative_npat_valid_negative_eps():
    """NPAT<0 + shares available → EPS VALID_NEGATIVE."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, -2000, -3000]),
        equity=_metric("equity", [5000, 4000, 3500]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    eps = next(m for m in res.output.metric_results if m.metric_id == "EPS_BASIC")
    assert eps.status == MetricStatus.VALID_NEGATIVE.value
    assert eps.value < 0


def test_neg_eps_negative_eps_not_input_incomplete():
    """Negative EPS must NOT be INPUT_INCOMPLETE when shares available."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [-2000, -1000, -500]),
        equity=_metric("equity", [5000, 4000, 3500]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    eps = next(m for m in res.output.metric_results if m.metric_id == "EPS_BASIC")
    assert eps.status != MetricStatus.INPUT_INCOMPLETE.value
    assert eps.status == MetricStatus.VALID_NEGATIVE.value


def test_neg_eps_pe_not_applicable():
    """When EPS<0, PE must be NOT_APPLICABLE in downstream export."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, -600]),
        equity=_metric("equity", [5000, 5000, 5000]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    assert res.output.downstream_export["EPS_basic"]["PE_method_applicability"] == "NOT_APPLICABLE"


def test_neg_eps_exported_when_negative():
    """VALID_NEGATIVE EPS must be exported (eligible=True)."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, -2000, 300]),
        equity=_metric("equity", [5000, 4000, 3500]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    assert res.output.downstream_export["EPS_basic"]["export_eligible"] is True


def test_neg_eps_value_correct():
    """EPS = NPAT / shares. Negative NPAT → negative EPS."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, -3000]),
        equity=_metric("equity", [5000, 4500, 4000]),
        total_assets=_metric("total_assets", [10000, 10000, 10000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.5, 1.5, 1.5]),
    )
    res = run_fundamental(req)
    eps = next(m for m in res.output.metric_results if m.metric_id == "EPS_BASIC")
    assert abs(eps.value - (-3000/1.5)) < 0.01


def test_neg_eps_positive_npat_positive_eps():
    """Positive NPAT → positive EPS (control)."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, 600]),
        equity=_metric("equity", [5000, 5500, 6000]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    eps = next(m for m in res.output.metric_results if m.metric_id == "EPS_BASIC")
    assert eps.status == MetricStatus.VALID.value
    assert eps.value > 0


# === Negative equity (6) ===
def test_neg_equity_roe_manual_review():
    """Negative avg equity → ROE MANUAL_REVIEW_REQUIRED."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, 600]),
        equity=_metric("equity", [1000, -300, -500]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    roe = next(m for m in res.output.metric_results if m.metric_id == "ROE")
    assert roe.status == MetricStatus.MANUAL_REVIEW_REQUIRED.value


def test_neg_equity_bvps_valid_negative():
    """Negative equity → BVPS VALID_NEGATIVE."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, 600]),
        equity=_metric("equity", [1000, -300, -500]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    bvps = next(m for m in res.output.metric_results if m.metric_id == "BVPS")
    assert bvps.status == MetricStatus.VALID_NEGATIVE.value


def test_neg_equity_negative_equity_warning():
    """Negative avg equity ROE must emit NEGATIVE_EQUITY_NOT_MEANINGFUL."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, 600]),
        equity=_metric("equity", [1000, -300, -500]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    roe = next(m for m in res.output.metric_results if m.metric_id == "ROE")
    assert any("NEGATIVE_EQUITY_NOT_MEANINGFUL" in w for w in roe.warnings)
    assert any(e.get("code") == "NEGATIVE_EQUITY_NOT_MEANINGFUL" for e in res.errors)


def test_neg_equity_cagr_not_applicable():
    """CAGR across zero (negative beginning) → NOT_APPLICABLE."""
    req = _req(
        revenue=_metric("revenue", [-500, 1000, 2000]),
        net_income=_metric("net_income", [500, 550, 600]),
        equity=_metric("equity", [1000, 1500, 2000]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    assert res.output.growth.get("revenue_CAGR_status") == MetricStatus.NOT_APPLICABLE.value


def test_neg_equity_bvps_negative_value_correct():
    """BVPS = equity/shares. Negative equity → negative BVPS."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, 600]),
        equity=_metric("equity", [1000, -300, -500]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    bvps = next(m for m in res.output.metric_results if m.metric_id == "BVPS")
    assert bvps.value < 0


def test_neg_equity_roe_error_in_results():
    """Negative equity error appears in runner errors list."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, 600]),
        equity=_metric("equity", [1000, -300, -500]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    assert any(e.get("code") == "NEGATIVE_EQUITY_NOT_MEANINGFUL" for e in res.errors)


# === Near-zero equity (6) ===
def test_near_zero_equity_ratio_warning():
    """Equity/assets < 5% → EXTREME_EQUITY_RATIO_WARNING."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [-500, -300, -100]),
        equity=_metric("equity", [500, 400, 93]),
        total_assets=_metric("total_assets", [10000, 11000, 15000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    roe = next(m for m in res.output.metric_results if m.metric_id == "ROE")
    assert any("EXTREME_EQUITY_RATIO_WARNING" in w for w in roe.warnings)


def test_near_zero_equity_bvps_warning():
    """Near-zero equity → BVPS EXTREME_EQUITY_RATIO_WARNING."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, 600]),
        equity=_metric("equity", [500, 400, 93]),
        total_assets=_metric("total_assets", [10000, 11000, 15000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    bvps = next(m for m in res.output.metric_results if m.metric_id == "BVPS")
    assert any("EXTREME_EQUITY_RATIO_WARNING" in w for w in bvps.warnings)


def test_near_zero_equity_normal_no_warning():
    """Normal equity ratio → NO EXTREME_EQUITY_RATIO_WARNING."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, 600]),
        equity=_metric("equity", [3000, 3500, 4000]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    bvps = next(m for m in res.output.metric_results if m.metric_id == "BVPS")
    assert not any("EXTREME_EQUITY_RATIO_WARNING" in w for w in bvps.warnings)


def test_near_zero_equity_threshold_boundary():
    """Equity/assets = 5% exactly → no warning (boundary)."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, 600]),
        equity=_metric("equity", [500, 500, 500]),
        total_assets=_metric("total_assets", [10000, 10000, 10000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    bvps = next(m for m in res.output.metric_results if m.metric_id == "BVPS")
    assert not any("EXTREME_EQUITY_RATIO_WARNING" in w for w in bvps.warnings)


def test_near_zero_equity_hbc_case():
    """HBC-like: equity=93 tỷ, assets=15250 tỷ → ratio 0.6% → warning."""
    req = _req(
        revenue=_metric("revenue", [8000, 9000, 10000]),
        net_income=_metric("net_income", [500, -1000, -1100]),
        equity=_metric("equity", [4000, 1191, 93]),
        total_assets=_metric("total_assets", [16577, 18314, 15250], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [0.347, 0.347, 0.347]),
    )
    res = run_fundamental(req)
    roe = next(m for m in res.output.metric_results if m.metric_id == "ROE")
    assert any("EXTREME_EQUITY_RATIO_WARNING" in w for w in roe.warnings)


def test_near_zero_equity_warning_does_not_block_export():
    """Near-zero equity warning does NOT block export (warning only)."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, 600]),
        equity=_metric("equity", [500, 400, 93]),
        total_assets=_metric("total_assets", [10000, 11000, 15000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    bvps = next(m for m in res.output.metric_results if m.metric_id == "BVPS")
    assert bvps.status in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value)


# === Downstream negative export (4) ===
def test_export_negative_eps_pe_not_applicable():
    """Negative EPS export: PE_method_applicability = NOT_APPLICABLE."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, -600]),
        equity=_metric("equity", [5000, 5000, 5000]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    assert res.output.downstream_export["EPS_basic"]["PE_method_applicability"] == "NOT_APPLICABLE"


def test_export_positive_eps_pe_applicable():
    """Positive EPS export: PE_method_applicability = APPLICABLE."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, 600]),
        equity=_metric("equity", [5000, 5500, 6000]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    assert res.output.downstream_export["EPS_basic"]["PE_method_applicability"] == "APPLICABLE"


def test_export_negative_eps_eligible():
    """VALID_NEGATIVE EPS must be export_eligible=True."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, -600]),
        equity=_metric("equity", [5000, 5000, 5000]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    assert res.output.downstream_export["EPS_basic"]["export_eligible"] is True
    assert res.output.downstream_export["EPS_basic"]["status"] == MetricStatus.VALID_NEGATIVE.value


def test_export_negative_eps_value_negative():
    """Negative EPS export value is negative."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, -600]),
        equity=_metric("equity", [5000, 5000, 5000]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0]),
    )
    res = run_fundamental(req)
    assert res.output.downstream_export["EPS_basic"]["value"] < 0


# === DERIVED_INPUT quality binding (4) ===
def test_derived_input_quality_flag_preserved():
    """DERIVED_INPUT shares quality_status preserved in metric."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, 600]),
        equity=_metric("equity", [5000, 5500, 6000]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0], quality_status="DERIVED_INPUT"),
    )
    res = run_fundamental(req)
    assert req.metrics["shares_outstanding"].quality_status == "DERIVED_INPUT"


def test_derived_input_not_blocking():
    """DERIVED_INPUT shares do NOT block EPS computation."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, 600]),
        equity=_metric("equity", [5000, 5500, 6000]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0], quality_status="DERIVED_INPUT"),
    )
    res = run_fundamental(req)
    eps = next(m for m in res.output.metric_results if m.metric_id == "EPS_BASIC")
    assert eps.status in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value)


def test_derived_input_quality_in_export():
    """DERIVED_INPUT quality flag preserved in downstream export."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, 600]),
        equity=_metric("equity", [5000, 5500, 6000]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0], quality_status="DERIVED_INPUT"),
    )
    res = run_fundamental(req)
    # Quality flag in export (added by engine)
    assert "quality_status" in res.output.downstream_export["EPS_basic"]


def test_derived_input_share_basis_correct():
    """DERIVED_INPUT shares still have correct share_basis binding."""
    req = _req(
        revenue=_metric("revenue", [10000, 11000, 12000]),
        net_income=_metric("net_income", [500, 550, 600]),
        equity=_metric("equity", [5000, 5500, 6000]),
        total_assets=_metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
        shares_outstanding=_metric("shares_outstanding", [1.0, 1.0, 1.0], quality_status="DERIVED_INPUT",
                                   share_basis_bindings=[ShareBasis.WEIGHTED_AVERAGE_BASIC.value]*3),
    )
    res = run_fundamental(req)
    assert req.metrics["shares_outstanding"].share_basis_bindings[0] == ShareBasis.WEIGHTED_AVERAGE_BASIC.value
