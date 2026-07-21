"""Phase 4F regression tests for VVE-REQ-077..081 + harness binding.

Directive Phase 4F §10: bridge ≥8, applicability ≥8, shares ≥8, registry ≥8.
"""
import sys, os, json, copy, pytest
sys.path.insert(0, "/Users/bobo/.zcode/skills/vn-valuation-engine/implementation")
sys.path.insert(0, "/Users/bobo/ZCodeProject/vn-valuation-engine-phase4F/integration")

from models.canonical_models import ValuationOutput, MethodResult, CalculationStep
from verifier.independent_verifier import verify, _recompute_bridge, _check_applicability_consistency, _check_shares_range, _check_registry_consistency
from phase4f_harness import run_harness_with_binding


# Helpers
def _m(**kw):
    defaults = dict(method_id="TEST", status="VALID", formula_id="PE-v1.0.0",
                    input_metric_ids=["eps"], calculation_trace=[CalculationStep(step=1, expression="x", inputs_used=["eps"], result=100)],
                    implied_price=100, shares_outstanding=1e9, currency="VND", warnings=[], error_codes=[])
    defaults.update(kw)
    return MethodResult(**defaults)

def _output(methods, **kw):
    defaults = dict(schema_version="1.0.0", entity={"canonical_ticker":"FPT"},
                    input_summary={"price":{"value":100},"eps":{"value":10}},
                    method_results=methods, errors=[], quality={})
    defaults.update(kw)
    return ValuationOutput(**defaults)


# === Bridge recompute (VVE-REQ-077) — 8 tests ===

def test_bridge_balanced_pass():
    items = [{"item_id":"EV","value":100,"sign":"+"},{"item_id":"NET_DEBT","value":20,"sign":"-"},
             {"item_id":"EQUITY_VALUE","value":80,"sign":"="}]
    ok, _ = _recompute_bridge(_m(method_id="EV_EBITDA", equity_bridge_items=items, bridge_balanced=True))
    assert ok

def test_bridge_net_debt_sign_reversed_fail():
    items = [{"item_id":"EV","value":100,"sign":"+"},{"item_id":"NET_DEBT","value":-20,"sign":"-"},  # negative!
             {"item_id":"EQUITY_VALUE","value":80,"sign":"="}]
    ok, _ = _recompute_bridge(_m(method_id="EV_EBITDA", equity_bridge_items=items, bridge_balanced=True))
    assert not ok

def test_bridge_minority_removed_fail():
    items = [{"item_id":"EV","value":100,"sign":"+"},{"item_id":"NET_DEBT","value":20,"sign":"-"},
             {"item_id":"EQUITY_VALUE","value":80,"sign":"="}]  # no MINORITY_INTEREST
    # If original had minority, removing it changes sum
    items_with_minority = [{"item_id":"EV","value":100,"sign":"+"},{"item_id":"NET_DEBT","value":20,"sign":"-"},
                           {"item_id":"MINORITY_INTEREST","value":10,"sign":"-"},
                           {"item_id":"EQUITY_VALUE","value":70,"sign":"="}]
    ok_removed, _ = _recompute_bridge(_m(method_id="EV_EBITDA", equity_bridge_items=items, bridge_balanced=True))
    # The "removed" bridge should still balance because EQUITY_VALUE was updated to match
    # But if EQUITY_VALUE stays 70 (original) while items removed, it won't balance
    items_removed_but_eq_stale = [{"item_id":"EV","value":100,"sign":"+"},{"item_id":"NET_DEBT","value":20,"sign":"-"},
                                  {"item_id":"EQUITY_VALUE","value":70,"sign":"="}]  # eq=70 but computed=80
    ok_stale, _ = _recompute_bridge(_m(method_id="EV_EBITDA", equity_bridge_items=items_removed_but_eq_stale, bridge_balanced=True))
    assert not ok_stale

def test_bridge_cash_double_counted_fail():
    items = [{"item_id":"EV","value":100,"sign":"+"},{"item_id":"NET_DEBT","value":20,"sign":"-"},
             {"item_id":"CASH","value":50,"sign":"+"},{"item_id":"CASH","value":50,"sign":"+"},  # double!
             {"item_id":"EQUITY_VALUE","value":80,"sign":"="}]
    ok, _ = _recompute_bridge(_m(method_id="EV_EBITDA", equity_bridge_items=items, bridge_balanced=True))
    assert not ok

def test_bridge_no_equity_value_fail():
    items = [{"item_id":"EV","value":100,"sign":"+"},{"item_id":"NET_DEBT","value":20,"sign":"-"}]
    ok, _ = _recompute_bridge(_m(method_id="EV_EBITDA", equity_bridge_items=items, bridge_balanced=True))
    assert not ok

def test_bridge_empty_passes_silently():
    # Non-EV method has no bridge
    ok, evidence = _recompute_bridge(_m(method_id="PE"))
    assert ok and evidence == ""

def test_bridge_tolerance_accepts_small_diff():
    items = [{"item_id":"EV","value":100,"sign":"+"},{"item_id":"NET_DEBT","value":20,"sign":"-"},
             {"item_id":"EQUITY_VALUE","value":80.5,"sign":"="}]  # 0.5 diff
    ok, _ = _recompute_bridge(_m(method_id="EV_EBITDA", equity_bridge_items=items, bridge_balanced=True))
    assert ok

def test_bridge_full_verify_catches_sign_reversal():
    items = [{"item_id":"EV","value":1000,"sign":"+"},{"item_id":"NET_DEBT","value":-200,"sign":"-"},
             {"item_id":"EQUITY_VALUE","value":800,"sign":"="}]
    m = _m(method_id="EV_EBITDA", equity_bridge_items=items, bridge_balanced=True)
    out = _output([m])
    result = verify(out)
    # Should have at least one FAIL for bridge
    bridge_results = [r for r in result.requirement_results if r.requirement_id == "VVE-REQ-077"]
    assert any(r.verdict == "FAIL" for r in bridge_results)


# === Applicability consistency (VVE-REQ-078) — 8 tests ===

def test_applic_VALID_with_trace_passes():
    ok, _ = _check_applicability_consistency(_m(status="VALID"), _output([_m()]))
    assert ok

def test_applic_NA_with_price_fails():
    m = _m(status="NOT_APPLICABLE", implied_price=999)
    ok, _ = _check_applicability_consistency(m, _output([m]))
    assert not ok

def test_applic_INCOMPLETE_with_price_fails():
    m = _m(status="INPUT_INCOMPLETE", implied_price=999)
    ok, _ = _check_applicability_consistency(m, _output([m]))
    assert not ok

def test_applic_NA_without_price_passes():
    m = _m(status="NOT_APPLICABLE", implied_price=None, calculation_trace=[])
    ok, _ = _check_applicability_consistency(m, _output([m]))
    assert ok

def test_applic_VALID_with_critical_error_fails():
    m = _m(status="VALID", method_id="EV_EBITDA")
    out = _output([m], errors=[{"method_id":"EV_EBITDA","severity":"CRITICAL","code":"TEST"}])
    ok, _ = _check_applicability_consistency(m, out)
    assert not ok

def test_applic_VALID_without_trace_fails():
    m = _m(status="VALID", calculation_trace=[])
    ok, _ = _check_applicability_consistency(m, _output([m]))
    assert not ok

def test_applic_PE_VALID_with_negative_EPS_fails():
    m = _m(method_id="PE", status="VALID", input_metric_ids=["eps"])
    out = _output([m], input_summary={"eps":{"value":-10,"status":"VALID"}})
    ok, _ = _check_applicability_consistency(m, out)
    assert not ok

def test_applic_PE_VALID_with_NA_EPS_fails():
    m = _m(method_id="PE", status="VALID", input_metric_ids=["eps"])
    out = _output([m], input_summary={"eps":{"value":None,"status":"NOT_APPLICABLE"}})
    ok, _ = _check_applicability_consistency(m, out)
    assert not ok


# === Shares range sanity (VVE-REQ-079) — 8 tests ===

def test_shares_in_range_passes():
    m = _m(shares_outstanding=1e9, implied_price=100)
    out = _output([m], input_summary={"price":{"value":100}})
    ok, _ = _check_shares_range(m, out)
    assert ok

def test_shares_too_low_fails():
    m = _m(shares_outstanding=1000)
    out = _output([m])
    ok, _ = _check_shares_range(m, out)
    assert not ok

def test_shares_too_high_fails():
    m = _m(shares_outstanding=1e15)
    out = _output([m])
    ok, _ = _check_shares_range(m, out)
    assert not ok

def test_shares_x1000_caught():
    m = _m(shares_outstanding=1e12)  # 1B × 1000 = 1T — out of range
    out = _output([m])
    ok, _ = _check_shares_range(m, out)
    assert not ok

def test_shares_none_passes_silently():
    m = _m(shares_outstanding=None)
    out = _output([m])
    ok, _ = _check_shares_range(m, out)
    assert ok

def test_shares_with_price_market_cap_in_range():
    m = _m(shares_outstanding=1e9, implied_price=50000)
    out = _output([m], input_summary={"price":{"value":50000}})
    ok, _ = _check_shares_range(m, out)
    assert ok

def test_shares_with_price_market_cap_too_low():
    m = _m(shares_outstanding=1e7, implied_price=10)  # mcap = 1e8 = 100M < 100B
    out = _output([m], input_summary={"price":{"value":10}})
    ok, _ = _check_shares_range(m, out)
    assert not ok

def test_shares_full_verify_catches_x1000():
    m = _m(method_id="PE", shares_outstanding=1e12, implied_price=100)
    out = _output([m], input_summary={"price":{"value":100}})
    result = verify(out)
    shares_results = [r for r in result.requirement_results if r.requirement_id == "VVE-REQ-079"]
    assert any(r.verdict == "FAIL" for r in shares_results)


# === Registry consistency (VVE-REQ-080) — 8 tests ===

REGISTERED = {"PE","PB","EV_EBITDA","P_CF","P_S","PEG","DCF_FCFF","REVERSE_DCF","DDM","GRAHAM_NUMBER"}
FORMULAS = {"PE":"PE-v1.0.0","PB":"PB-v1.0.0","EV_EBITDA":"EV_EBITDA-v1.0.0","P_CF":"P_CF-v1.0.0",
            "P_S":"P_S-v1.0.0","PEG":"PEG-v1.0.0","DCF_FCFF":"DCF_FCFF-v1.0.0",
            "REVERSE_DCF":"REVERSE_DCF-v1.0.0","DDM":"DDM-v1.0.0","GRAHAM_NUMBER":"GRAHAM_NUMBER-v1.0.0"}

def test_reg_known_method_correct_formula_passes():
    ok, _ = _check_registry_consistency(_m(method_id="PE", formula_id="PE-v1.0.0"), REGISTERED, FORMULAS)
    assert ok

def test_reg_unknown_method_fails():
    ok, _ = _check_registry_consistency(_m(method_id="BOGUS"), REGISTERED, FORMULAS)
    assert not ok

def test_reg_wrong_formula_fails():
    ok, _ = _check_registry_consistency(_m(method_id="PE", formula_id="PE-v9.9.9"), REGISTERED, FORMULAS)
    assert not ok

def test_reg_EV_EBITDA_correct_passes():
    ok, _ = _check_registry_consistency(_m(method_id="EV_EBITDA", formula_id="EV_EBITDA-v1.0.0"), REGISTERED, FORMULAS)
    assert ok

def test_reg_GRAHAM_correct_passes():
    ok, _ = _check_registry_consistency(_m(method_id="GRAHAM_NUMBER", formula_id="GRAHAM_NUMBER-v1.0.0"), REGISTERED, FORMULAS)
    assert ok

def test_reg_DCF_FCFF_correct_passes():
    ok, _ = _check_registry_consistency(_m(method_id="DCF_FCFF", formula_id="DCF_FCFF-v1.0.0"), REGISTERED, FORMULAS)
    assert ok

def test_reg_selected_multiple_mismatch_fails():
    m = _m(method_id="PE", status="VALID", selected_multiple=15.0,
           calculation_trace=[CalculationStep(step=1, expression="EPS", inputs_used=["eps"], result=10),
                              CalculationStep(step=2, expression="selected_multiple", inputs_used=["bench"], result=20.0),
                              CalculationStep(step=3, expression="price", inputs_used=["eps","bench"], result=200)])
    ok, _ = _check_registry_consistency(m, REGISTERED, FORMULAS)
    assert not ok

def test_reg_full_verify_catches_formula_change():
    m = _m(method_id="PE", formula_id="PE-v9.9.9")
    out = _output([m])
    result = verify(out)
    reg_results = [r for r in result.requirement_results if r.requirement_id == "VVE-REQ-080"]
    assert any(r.verdict == "FAIL" for r in reg_results)


# === Harness binding (F4F-D) — 4 tests ===

def test_harness_clean_passes():
    original = {"method_results":[{"method_id":"PE"},{"method_id":"PB"}], "entity":{"canonical_ticker":"FPT"}}
    adapter_out = {"valuation_methods":[{"method_id":"PE"},{"method_id":"PB"}]}
    h = run_harness_with_binding(original, adapter_out)
    assert h.pre_post_comparison_ok

def test_harness_drop_method_detected():
    original = {"method_results":[{"method_id":"PE"},{"method_id":"PB"}], "entity":{"canonical_ticker":"FPT"}}
    adapter_out = {"valuation_methods":[{"method_id":"PE"}]}  # PB dropped
    h = run_harness_with_binding(original, adapter_out)
    assert not h.pre_post_comparison_ok

def test_harness_add_method_detected():
    original = {"method_results":[{"method_id":"PE"}], "entity":{"canonical_ticker":"FPT"}}
    adapter_out = {"valuation_methods":[{"method_id":"PE"},{"method_id":"FAKE"}]}
    h = run_harness_with_binding(original, adapter_out)
    assert not h.pre_post_comparison_ok

def test_harness_stale_verifier_detected():
    original = {"method_results":[], "entity":{"canonical_ticker":"FPT"}}
    h = run_harness_with_binding(original, {}, child_verifier_artifact_hash="stale_hash")
    assert h.stale_verifier_detected
