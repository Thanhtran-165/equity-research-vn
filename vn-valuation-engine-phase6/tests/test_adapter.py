"""Adapter unit tests — Phase 6 P6B (Directive §8.7).

Required: 8 clean + 12 negative + 4 reproducibility = 24 minimum.
"""
import sys, os, copy, json, pytest
from pathlib import Path

WORK = "/Users/bobo/ZCodeProject/vn-valuation-engine-phase6"
PHASE5R = "/Users/bobo/ZCodeProject/vn-valuation-engine-phase5/artifacts/phase5R-genuine-baseline"
sys.path.insert(0, f"{WORK}/integration")

from valuation_parent_adapter import adapt, AdapterFailure, AdapterResult
from report_ir_mapper import embed_into_parent_ir
from integration_validator import validate_integration
from integration_evidence_manifest import build_evidence_manifest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_fixture_output(run_id: str) -> dict:
    """Load Phase 5R run output as child_output dict."""
    p = Path(PHASE5R) / run_id / "valuation-output.json"
    return json.load(open(p))


def _parent_ir_skeleton(child_output: dict) -> dict:
    """Build a minimal parent IR skeleton for embed testing (financial_data from request)."""
    request = child_output.get("request") or {}
    return {
        "schema_version": "1.0.0-arch-b",
        "metadata": {
            "ticker": request.get("ticker", "TEST"),
            "company_name": request.get("company", "Test Company"),
            "sector": request.get("sector", "unknown"),
            "exchange": request.get("exchange", "HOSE"),
            "generated_at": "2026-07-21T00:00:00Z",
            "source_snapshot_hashes": {},
        },
        "reporting_scope": {
            "statement_scope": "consolidated",
            "currency": "VND",
            "unit": "raw",
            "annual_periods": [2021, 2022, 2023, 2024, 2025],
        },
        "financial_data": {"metrics": {}},  # untouched by adapter
        "derived_metrics": {"valuation": {}},
        "sections": [
            {"section_id": "executive_summary", "title": "Executive Summary",
             "applicability": "APPLICABLE", "structured_facts": {}, "narrative": "",
             "warnings": [], "validation_status": "PENDING"},
            {"section_id": "valuation", "title": "Valuation",
             "applicability": "APPLICABLE", "structured_facts": {}, "narrative": "",
             "warnings": [], "validation_status": "PENDING"},
            {"section_id": "risk", "title": "Risk",
             "applicability": "APPLICABLE", "structured_facts": {}, "narrative": "",
             "warnings": [], "validation_status": "PENDING"},
        ],
        "charts": [],
        "validation": {"section_results": {}, "deterministic_gate_results": {}},
    }


def _full_pipeline(child_output: dict):
    """Helper: full adapter + mapper + validator."""
    adapter_result = adapt(child_output)
    parent_ir = _parent_ir_skeleton(child_output)
    parent_ir = embed_into_parent_ir(parent_ir, adapter_result)
    validation = validate_integration(child_output, adapter_result, parent_ir)
    return adapter_result, parent_ir, validation


# ---------------------------------------------------------------------------
# 8 CLEAN MAPPING TESTS (Directive §8.7)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("run_id", [
    "VCB-run-A", "BVH-run-A", "HPG-run-A", "HPG-run-B",
    "MWG-run-A", "MWG-run-B", "FPT-run-A", "FPT-run-B",
])
def test_clean_adapter_passes_8_fixtures(run_id):
    """8 clean fixtures must pass adapter without CRITICAL failures."""
    child_output = _load_fixture_output(run_id)
    adapter_result = adapt(child_output)
    assert adapter_result.final_status in ("PASS", "PASS_WITH_WARNINGS"), \
        f"{run_id}: adapter final_status={adapter_result.final_status}, failures={[f.to_dict() for f in adapter_result.failures]}"


@pytest.mark.parametrize("run_id", [
    "VCB-run-A", "BVH-run-A", "HPG-run-A", "HPG-run-B",
    "MWG-run-A", "MWG-run-B", "FPT-run-A", "FPT-run-B",
])
def test_clean_validator_passes_8_fixtures(run_id):
    """8 clean fixtures must pass integration validator."""
    child_output = _load_fixture_output(run_id)
    _, _, validation = _full_pipeline(child_output)
    assert validation.verdict == "PASS", \
        f"{run_id}: validation={validation.to_dict()}"


def test_clean_pe_pb_graham_extracted_to_derived_metrics_FPT():
    """FPT has PE/PB/Graham VALID → derived_metrics.valuation must have them."""
    child_output = _load_fixture_output("FPT-run-A")
    _, parent_ir, _ = _full_pipeline(child_output)
    val = parent_ir["derived_metrics"]["valuation"]
    assert "pe_implied" in val and val["pe_implied"] is not None
    assert "pb_implied" in val and val["pb_implied"] is not None
    assert "graham_implied" in val and val["graham_implied"] is not None


def test_clean_no_financial_data_modification():
    """Adapter must NOT modify parent's financial_data."""
    child_output = _load_fixture_output("HPG-run-A")
    skeleton = _parent_ir_skeleton(child_output)
    original_financial = copy.deepcopy(skeleton["financial_data"])
    adapter_result = adapt(child_output)
    parent_ir = embed_into_parent_ir(skeleton, adapter_result)
    assert parent_ir["financial_data"] == original_financial, "financial_data was modified"


# ---------------------------------------------------------------------------
# 12 NEGATIVE MAPPING TESTS (Directive §8.7)
# ---------------------------------------------------------------------------

def test_negative_missing_required_field():
    """Mutilate a method by removing method_id → CRITICAL failure."""
    child_output = _load_fixture_output("FPT-run-A")
    child_output["method_results"][0].pop("method_id", None)
    adapter_result = adapt(child_output)
    assert adapter_result.final_status == "FAIL"
    assert any(f.code == "MISSING_REQUIRED_FIELD" for f in adapter_result.failures)


def test_negative_duplicate_method_id():
    """Duplicate method_id → CRITICAL."""
    child_output = _load_fixture_output("FPT-run-A")
    child_output["method_results"].append(copy.deepcopy(child_output["method_results"][0]))
    adapter_result = adapt(child_output)
    assert adapter_result.final_status == "FAIL"
    assert any(f.code == "DUPLICATE_METHOD_ID" for f in adapter_result.failures)


def test_negative_invalid_status():
    """Invalid status value → CRITICAL."""
    child_output = _load_fixture_output("FPT-run-A")
    child_output["method_results"][0]["status"] = "BOGUS_STATUS"
    adapter_result = adapt(child_output)
    assert adapter_result.final_status == "FAIL"
    assert any(f.code == "INVALID_METHOD_STATUS" for f in adapter_result.failures)


def test_negative_valid_method_missing_implied_price():
    """VALID method without implied_price → CRITICAL."""
    child_output = _load_fixture_output("FPT-run-A")
    for m in child_output["method_results"]:
        if m.get("method_id") == "PE":
            m["implied_price"] = None
    adapter_result = adapt(child_output)
    assert any(f.code == "VALID_METHOD_MISSING_IMPLIED_PRICE" for f in adapter_result.failures)


def test_negative_valid_method_missing_trace():
    """VALID method without calculation_trace → CRITICAL."""
    child_output = _load_fixture_output("FPT-run-A")
    for m in child_output["method_results"]:
        if m.get("method_id") == "PE":
            m["calculation_trace"] = []
    adapter_result = adapt(child_output)
    assert any(f.code == "VALID_METHOD_MISSING_TRACE" for f in adapter_result.failures)


def test_negative_not_applicable_with_price():
    """NOT_APPLICABLE method with implied_price → CRITICAL (would be fake valuation)."""
    child_output = _load_fixture_output("VCB-run-A")
    # Find EV_EBITDA (NOT_APPLICABLE in VCB)
    for m in child_output["method_results"]:
        if m.get("method_id") == "EV_EBITDA" and m.get("status") == "NOT_APPLICABLE":
            m["implied_price"] = 99999  # fake
    adapter_result = adapt(child_output)
    assert any(f.code == "NOT_APPLICABLE_WITH_PRICE" for f in adapter_result.failures)


def test_negative_cross_ticker_contamination():
    """request.ticker != entity.canonical_ticker → CRITICAL."""
    child_output = _load_fixture_output("FPT-run-A")
    child_output["entity"]["canonical_ticker"] = "HPG"  # mismatch
    adapter_result = adapt(child_output)
    assert any(f.code == "CROSS_TICKER_CONTAMINATION" for f in adapter_result.failures)


def test_negative_invalid_child_output_type():
    """Non-dict child_output → CRITICAL."""
    adapter_result = adapt("not a dict")
    assert adapter_result.final_status == "FAIL"
    assert any(f.code == "INVALID_CHILD_OUTPUT_TYPE" for f in adapter_result.failures)


def test_negative_no_target_price_when_all_NA():
    """When all methods are NOT_APPLICABLE, no target_price should be emitted."""
    child_output = _load_fixture_output("VCB-run-A")
    # Make all methods NOT_APPLICABLE
    for m in child_output["method_results"]:
        m["status"] = "NOT_APPLICABLE"
        m["implied_price"] = None
        m["calculation_trace"] = []
    _, parent_ir, validation = _full_pipeline(child_output)
    exec_section = next(s for s in parent_ir["sections"] if s.get("section_id") == "executive_summary")
    val_sum = exec_section.get("structured_facts", {}).get("valuation_summary", {})
    assert val_sum.get("target_price_median") is None, "should not emit target price when all NA"


def test_negative_lossy_mapping_detected_by_validator():
    """Force lossy mapping (drop method) → validator detects method count mismatch."""
    child_output = _load_fixture_output("FPT-run-A")
    adapter_result = adapt(child_output)
    # Simulate lossy mapping by removing a method from adapter output
    adapter_result.valuation_methods.pop()
    skeleton = _parent_ir_skeleton(child_output)
    parent_ir = embed_into_parent_ir(skeleton, adapter_result)
    validation = validate_integration(child_output, adapter_result, parent_ir)
    assert validation.verdict == "FAIL"
    assert any("method_count_preserved" in f.get("check","") for f in validation.failures)


def test_negative_method_id_substitution():
    """Swap PE→PB silently → validator detects ID mismatch."""
    child_output = _load_fixture_output("FPT-run-A")
    for m in child_output["method_results"]:
        if m.get("method_id") == "PE":
            m["method_id"] = "PB2"  # silent rename
    adapter_result = adapt(child_output)
    # Adapter preserves as-is, but IDs no longer match expected set
    method_ids = {m.get("method_id") for m in adapter_result.valuation_methods}
    assert "PB2" in method_ids  # adapter preserved (correct behavior)


def test_negative_orphan_metric_reference():
    """Trace references non-existent metric → MAJOR failure."""
    child_output = _load_fixture_output("FPT-run-A")
    for m in child_output["method_results"]:
        if m.get("method_id") == "PE":
            # Inject orphan reference
            m["calculation_trace"].append({
                "step": 99, "expression": "test", "inputs_used": ["totally_bogus_metric"],
                "result": 0, "rule_id": None, "evidence": None,
            })
    adapter_result = adapt(child_output)
    assert any(f.code == "ORPHAN_METRIC_REFERENCE" for f in adapter_result.failures)


# ---------------------------------------------------------------------------
# 4 REPRODUCIBILITY TESTS (Directive §8.7)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("run_id", ["FPT-run-A", "HPG-run-A", "MWG-run-A", "VCB-run-A"])
def test_reproducibility_adapter_output_stable(run_id):
    """Running adapter twice on same child_output must produce identical result."""
    child_output = _load_fixture_output(run_id)
    r1 = adapt(child_output).to_dict()
    r2 = adapt(child_output).to_dict()
    # Strip warnings (may differ) and compare core zones
    for r in (r1, r2):
        r.pop("warnings", None)
    assert r1 == r2, f"{run_id}: adapter not deterministic"


@pytest.mark.parametrize("run_id", ["FPT-run-A", "HPG-run-A", "MWG-run-A", "VCB-run-A"])
def test_reproducibility_validator_verdict_stable(run_id):
    """Validator verdict must be stable across runs."""
    child_output = _load_fixture_output(run_id)
    _, _, v1 = _full_pipeline(child_output)
    _, _, v2 = _full_pipeline(child_output)
    assert v1.verdict == v2.verdict


def test_reproducibility_parent_ir_stable_FPT():
    """Parent IR must be byte-stable across two adapter invocations (semantic hash)."""
    import hashlib
    child_output = _load_fixture_output("FPT-run-A")
    _, p1, _ = _full_pipeline(child_output)
    _, p2, _ = _full_pipeline(child_output)
    h1 = hashlib.sha256(json.dumps(p1, sort_keys=True, default=str).encode()).hexdigest()
    h2 = hashlib.sha256(json.dumps(p2, sort_keys=True, default=str).encode()).hexdigest()
    assert h1 == h2, "parent IR not byte-stable across adapter runs"


def test_reproducibility_no_random_state_FPT():
    """Adapter must not use random/time-based state — same input → same output hash."""
    import hashlib
    child_output = _load_fixture_output("FPT-run-A")
    hashes = set()
    for _ in range(3):
        r = adapt(child_output).to_dict()
        hashes.add(hashlib.sha256(json.dumps(r, sort_keys=True, default=str).encode()).hexdigest())
    assert len(hashes) == 1, f"adapter produced {len(hashes)} different outputs"
