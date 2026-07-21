"""Phase 5R regression tests — source adapter scale correctness.

Per Directive Phase 5R §5: prove that
  raw VND value + Scale.UNIT → NOT multiplied by 1M
  raw value truly in million VND + Scale.MILLION → multiplied by 1M correctly.

Plus VVE-REQ-071 positive (bridge balances) + negative (bridge doesn't balance) tests.
"""
import sys, os
import pytest

SKILL = "/Users/bobo/.zcode/skills/vn-valuation-engine"
WORK = "/Users/bobo/ZCodeProject/vn-valuation-engine-phase5"
sys.path.insert(0, os.path.join(SKILL, "implementation"))
sys.path.insert(0, os.path.join(WORK, "source-adapter"))

from models.canonical_models import (
    ValuationMetric, MetricStatus, Unit, Scale, Currency,
    PeriodType, Scope, SourceType,
)
from engines.unit_currency_engine import normalize_metric
from models.canonical_models import MethodResult, CalculationStep, ValuationOutput
from verifier.independent_verifier import verify


# === Scale regression tests (Directive 5R §5) ===

def _make_metric(value, scale):
    return ValuationMetric(
        metric_id="test_ebitda", value=value, status=MetricStatus.VALID,
        unit=Unit.VND, scale=scale, currency=Currency.VND,
        period="FY2025", period_type=PeriodType.YEAR, scope=Scope.CONSOLIDATED,
        source_id="test", source_date="2025-12-31", source_type=SourceType.SPONSOR,
    )


def test_raw_vnd_with_scale_unit_NOT_multiplied():
    """Critical regression: raw VND value (4.96e12) + Scale.UNIT must NOT be multiplied.
    
    Pre-fix bug: adapter set Scale.MILLION for raw VND → engine multiplied × 1M → 4.96e18.
    Post-fix: adapter uses Scale.UNIT for raw VND → engine leaves value unchanged.
    """
    raw_vnd_value = 4.96e12  # FPT EBITDA in raw VND
    metric = _make_metric(raw_vnd_value, Scale.UNIT)
    normalized = normalize_metric(metric)
    
    # Value should remain 4.96e12 (NOT multiplied by 1M)
    assert normalized.normalized_value == pytest.approx(raw_vnd_value, rel=1e-9), \
        f"Scale.UNIT for raw VND must NOT multiply. Got {normalized.normalized_value}, expected {raw_vnd_value}"
    assert normalized.normalized_value < 1e15, f"Value {normalized.normalized_value} suggests scale multiplication occurred"


def test_million_vnd_with_scale_million_multiplied_correctly():
    """Complementary: a value truly expressed in million VND + Scale.MILLION must be multiplied × 1M.
    
    Example: BVPS expressed as '8.619' meaning 8.619 million VND (= 8,619,000 VND).
    """
    value_in_millions = 8.619  # 8.619 million VND
    metric = _make_metric(value_in_millions, Scale.MILLION)
    normalized = normalize_metric(metric)
    
    # Should be multiplied by 1M
    assert normalized.normalized_value == pytest.approx(8.619e6, rel=1e-6), \
        f"Scale.MILLION must multiply by 1M. Got {normalized.normalized_value}, expected ~8.619e6"


def test_thousand_vnd_with_scale_thousand_multiplied_correctly():
    """Value in thousand VND + Scale.THOUSAND must be multiplied × 1K."""
    value_in_thousands = 8619.0  # 8619 thousand VND = 8.619M VND
    metric = _make_metric(value_in_thousands, Scale.THOUSAND)
    normalized = normalize_metric(metric)
    
    assert normalized.normalized_value == pytest.approx(8.619e6, rel=1e-6), \
        f"Scale.THOUSAND must multiply by 1K. Got {normalized.normalized_value}, expected ~8.619e6"


def test_billion_vnd_with_scale_billion_multiplied_correctly():
    """Value in billion VND + Scale.BILLION must be multiplied × 1B."""
    value_in_billions = 4.96  # 4.96 billion VND = 4.96e9 VND
    metric = _make_metric(value_in_billions, Scale.BILLION)
    normalized = normalize_metric(metric)
    
    assert normalized.normalized_value == pytest.approx(4.96e9, rel=1e-6), \
        f"Scale.BILLION must multiply by 1B. Got {normalized.normalized_value}, expected ~4.96e9"


def test_adapter_default_scale_is_UNIT():
    """Smoke test: import adapter, check that _metric default scale is Scale.UNIT (not MILLION)."""
    import inspect
    import vnstock_adapter
    src = inspect.getsource(vnstock_adapter._metric)
    assert "Scale.UNIT" in src, f"Adapter _metric default scale must be Scale.UNIT. Source contains:\n{src[:300]}"
    assert "Scale.MILLION" not in src.split("defaults = dict(")[1].split(")")[0], \
        "Adapter _metric default scale must NOT contain Scale.MILLION"


# === VVE-REQ-071 positive/negative tests (Directive 5R §5) ===

def _make_method_result(method_id, bridge_balanced, items):
    return MethodResult(
        method_id=method_id, status="VALID", formula_id="EV_EBITDA-v1.0.0",
        calculation_trace=[CalculationStep(step=1, expression="test", result=1.0)],
        implied_enterprise_value=items[0]["value"],
        equity_bridge_items=items,
        bridge_balanced=bridge_balanced,
        implied_equity_value=items[-1]["value"],
        shares_outstanding=1e6,
        implied_price=items[-1]["value"] / 1e6,
    )


def _make_output_with_method(method):
    return ValuationOutput(
        schema_version="1.0.0-phase2",
        request={"ticker":"TEST"},
        entity={"canonical_ticker":"TEST"},
        valuation_date="2026-07-21",
        method_results=[method],
    )


def test_VVE_REQ_071_positive_balanced_bridge_PASS():
    """Bridge that balances → VVE-REQ-071 PASS."""
    items = [
        {"item_id":"EV", "value":1e10, "sign":"+"},
        {"item_id":"NET_DEBT", "value":2e9, "sign":"-"},
        {"item_id":"MINORITY_INTEREST", "value":1e9, "sign":"-"},
        {"item_id":"EQUITY_VALUE", "value":7e9, "sign":"="},  # 10 - 2 - 1 = 7
    ]
    method = _make_method_result("EV_EBITDA", True, items)
    output = _make_output_with_method(method)
    result = verify(output)
    
    # Find VVE-REQ-071 in results
    req_071 = next((r for r in result.requirement_results if r.requirement_id == "VVE-REQ-071"), None)
    assert req_071 is not None, "VVE-REQ-071 must be present"
    assert req_071.verdict == "PASS", f"Balanced bridge must PASS VVE-REQ-071. Got {req_071.verdict}"


def test_VVE_REQ_071_negative_unbalanced_bridge_FAIL():
    """Bridge that doesn't balance → VVE-REQ-071 FAIL with EQUITY_BRIDGE_INVALID."""
    items = [
        {"item_id":"EV", "value":1e10, "sign":"+"},
        {"item_id":"NET_DEBT", "value":2e9, "sign":"-"},
        {"item_id":"EQUITY_VALUE", "value":5e9, "sign":"="},  # 10 - 2 = 8, NOT 5 → unbalanced
    ]
    method = _make_method_result("EV_EBITDA", False, items)
    output = _make_output_with_method(method)
    result = verify(output)
    
    req_071 = next((r for r in result.requirement_results if r.requirement_id == "VVE-REQ-071"), None)
    assert req_071 is not None
    assert req_071.verdict == "FAIL", f"Unbalanced bridge must FAIL VVE-REQ-071. Got {req_071.verdict}"
    assert req_071.failure_code == "EQUITY_BRIDGE_INVALID", \
        f"Failure code must be EQUITY_BRIDGE_INVALID. Got {req_071.failure_code}"


# === Adapter defect regression: pre-fix adapter would fail post-fix tests ===

def test_prefixed_adapter_would_fail_scale_UNIT_test():
    """Meta-test: load pre-fix adapter source, confirm it would FAIL the Scale.UNIT test.
    
    This proves the regression test would have caught the original defect.
    """
    import inspect
    prefixed_path = "/Users/bobo/ZCodeProject/vn-valuation-engine-phase5/halt-baseline-v1-scale-defect/source-adapter-reconstructed/vnstock_adapter_prefixed.py"
    if not os.path.exists(prefixed_path):
        pytest.skip("Pre-fix adapter not available")
    
    src = open(prefixed_path).read()
    # The pre-fix adapter has Scale.MILLION as default
    defaults_section = src.split("defaults = dict(")[1].split(")")[0]
    assert "Scale.MILLION" in defaults_section, "Pre-fix adapter must have Scale.MILLION as default"
    assert "Scale.UNIT" not in defaults_section, "Pre-fix adapter must NOT have Scale.UNIT as default"
