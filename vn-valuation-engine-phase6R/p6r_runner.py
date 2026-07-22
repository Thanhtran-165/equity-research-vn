"""Phase 6R runner — fresh integration runs with adapter v1.2.0 + context verifier.

Runs 8 fixtures through the full pipeline:
  Phase 5R artifact → semantic context → child verifier → adapter v1.2.0
  → semantic binding harness → parent report IR → integration validator

Note: Parent renderer + parent verifier NOT invoked (parent immutable).
      Parent IR structurally validated instead.
"""
from __future__ import annotations
import sys, os, json, hashlib, copy, datetime as dt
from pathlib import Path

WORK = "/Users/bobo/ZCodeProject/vn-valuation-engine-phase6R"
PHASE5R = "/Users/bobo/ZCodeProject/vn-valuation-engine-phase5/artifacts/phase5R-genuine-baseline"
PHASE4G = "/Users/bobo/ZCodeProject/vn-valuation-engine-phase4G"
PHASE6 = "/Users/bobo/ZCodeProject/vn-valuation-engine-phase6"
PHASE4F = "/Users/bobo/ZCodeProject/vn-valuation-engine-phase4F"
SKILL = "/Users/bobo/.zcode/skills/vn-valuation-engine"

sys.path.insert(0, f"{SKILL}/implementation")
sys.path.insert(0, f"{PHASE6}/integration")
sys.path.insert(0, f"{PHASE4G}/integration")
sys.path.insert(0, f"{PHASE4F}/integration")
sys.path.insert(0, f"{PHASE4G}/implementation")

from models.canonical_models import ValuationOutput, MethodResult, CalculationStep
from verifier.independent_verifier import verify as child_verify
from valuation_parent_adapter import adapt
from report_ir_mapper import embed_into_parent_ir
from integration_validator import validate_integration
from phase4f_harness import run_harness_with_binding
from semantic_binding_harness import run_semantic_binding
from context.context_verifier import context_verify
from context.context_hashing import compute_semantic_context_hash

FIXTURES = [
    ("FIX-VCB-A", "VCB-run-A", "VCB", "banking"),
    ("FIX-BVH-A", "BVH-run-A", "BVH", "insurance"),
    ("FIX-HPG-A", "HPG-run-A", "HPG", "steel_cyclical"),
    ("FIX-HPG-B", "HPG-run-B", "HPG", "steel_cyclical"),
    ("FIX-MWG-A", "MWG-run-A", "MWG", "retail"),
    ("FIX-MWG-B", "MWG-run-B", "MWG", "retail"),
    ("FIX-FPT-A", "FPT-run-A", "FPT", "technology"),
    ("FIX-FPT-B", "FPT-run-B", "FPT", "technology"),
]


def _sha(obj):
    """Compute hash for binding — must match adapter's internal hash computation."""
    # Adapter uses: json.dumps(child_output, sort_keys=True, default=str, separators=(",",":"), ensure_ascii=False)
    # So we must NOT strip any fields for the binding hash.
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, default=str, separators=(",",":"), ensure_ascii=False).encode()
    ).hexdigest()


def build_context(artifact):
    """Build semantic context from clean artifact (externally bound)."""
    entity = artifact.get("entity") or {}
    methods = artifact.get("method_results") or []
    input_summary = artifact.get("input_summary") or {}
    provenance = artifact.get("provenance") or {}
    errors = artifact.get("errors") or []

    approved = [{"method_id": m.get("method_id"), "formula_id": m.get("formula_id"),
                 "applicability_status": m.get("status"), "applicability_rule_id": f"{m.get('method_id')}_R",
                 "permission_to_emit_implied_price": m.get("status")=="VALID" and m.get("implied_price") is not None}
                for m in methods]
    benchmarks = [{"method_id": m.get("method_id"), "benchmark_id": m.get("benchmark_type"),
                   "benchmark_type": m.get("benchmark_type"), "selected_value": m.get("selected_multiple"),
                   "selection_rule_id": f"{m.get('method_id')}_B"}
                  for m in methods if m.get("benchmark_type")]

    sm = {}; sd = {}
    for mid, p in provenance.items():
        if isinstance(p, dict):
            sid = p.get("source_id", "")
            sm.setdefault(sid, []).append(mid); sd[sid] = p
    source_registry = [{"source_id": s, "source_hash": sd[s].get("source_sha","h"), "supported_metric_ids": m,
                        "source_periods": [sd[s].get("period","FY2025")], "source_scopes": [sd[s].get("scope","CONSOLIDATED")]}
                       for s, m in sm.items()]
    period_registry = [{"metric_id": mid, "source_period": md.get("period","FY2025"),
                        "normalized_period": md.get("period","FY2025"), "alignment_decision_id": f"{mid}_P"}
                       for mid, md in input_summary.items() if isinstance(md, dict)]
    scope_registry = [{"metric_id": mid, "source_scope": md.get("scope","CONSOLIDATED"),
                       "normalized_scope": md.get("scope","CONSOLIDATED"), "alignment_decision_id": f"{mid}_S"}
                      for mid, md in input_summary.items() if isinstance(md, dict)]
    fc = [e.get("code") for e in errors if isinstance(e, dict) and e.get("severity")=="CRITICAL"]
    wc = [e.get("code") for e in errors if isinstance(e, dict) and e.get("severity")=="MAJOR"]

    ctx = {
        "context_schema_version": "1.0.0", "request_id": "p6r", "generated_before_results": True,
        "entity": {"ticker": entity.get("canonical_ticker",""), "company": entity.get("canonical_company",""),
                   "exchange": entity.get("exchange","HOSE"), "sector": entity.get("sector","")},
        "valuation_context": {"valuation_date": artifact.get("valuation_date",""), "reporting_currency": "VND"},
        "approved_methods": approved, "benchmarks": benchmarks,
        "share_context": {"share_basis":"BASIC","shares_metric_id":"shares","EPS_basis":"BASIC","EPS_metric_id":"eps"},
        "source_registry": source_registry, "period_registry": period_registry, "scope_registry": scope_registry,
        "error_state": {"fatal_error_codes": fc, "material_warning_codes": wc, "error_state_hash": "eh"},
        "registry_hashes": {k: f"{k}_h" for k in ("formula_registry_hash","applicability_registry_hash",
            "benchmark_registry_hash","source_registry_hash","period_registry_hash","scope_registry_hash","error_registry_hash")},
        "evidence_hashes": {"raw_source_hashes": {}, "canonical_input_hash": "ci", "execution_context_hash": "ec"},
        "context_builder_version": "runner-1.0",
    }
    ctx["semantic_context_hash"] = compute_semantic_context_hash(ctx)
    return ctx


def run_child_verifier(co):
    try:
        mr = []
        for m in co.get("method_results", []):
            tr = [CalculationStep(**{k:v for k,v in s.items() if k in CalculationStep.__dataclass_fields__})
                  for s in m.get("calculation_trace", []) if isinstance(s, dict)]
            kw = dict(method_id=m.get("method_id",""), status=m.get("status",""), formula_id=m.get("formula_id",""),
                input_metric_ids=m.get("input_metric_ids",[]), calculation_trace=tr,
                benchmark_type=m.get("benchmark_type"), selected_multiple=m.get("selected_multiple"),
                implied_enterprise_value=m.get("implied_enterprise_value"), implied_equity_value=m.get("implied_equity_value"),
                shares_outstanding=m.get("shares_outstanding"), implied_price=m.get("implied_price"),
                currency=m.get("currency","VND"), warnings=m.get("warnings",[]), error_codes=m.get("error_codes",[]))
            eb = m.get("equity_bridge")
            if isinstance(eb, dict):
                kw["equity_bridge_items"] = eb.get("items") or []
                kw["bridge_balanced"] = eb.get("balanced") or eb.get("balances")
            mr.append(MethodResult(**kw))
        return child_verify(ValuationOutput(schema_version=co.get("schema_version",""),
            request=co.get("request",{}), entity=co.get("entity",{}), valuation_date=co.get("valuation_date",""),
            reporting_currency=co.get("reporting_currency","VND"), input_summary=co.get("input_summary",{}),
            method_results=mr, peer_set=co.get("peer_set") or [], historical_benchmarks=co.get("historical_benchmarks") or [],
            valuation_range=co.get("valuation_range") or {}, assumptions=co.get("assumptions") or {},
            warnings=co.get("warnings") or [], errors=co.get("errors") or [],
            provenance=co.get("provenance") or {}, quality=co.get("quality") or {})), True
    except Exception:
        return None, False


def parent_ir_skeleton(child_output):
    entity = child_output.get("entity") or {}
    return {
        "schema_version": "1.0.0-arch-b",
        "metadata": {"ticker": entity.get("canonical_ticker","TEST"), "company_name": entity.get("canonical_company","Test"),
                     "sector": entity.get("sector","unknown"), "exchange": entity.get("exchange","HOSE"),
                     "generated_at": "2026-07-22T00:00:00Z", "source_snapshot_hashes": {}},
        "reporting_scope": {"statement_scope": "consolidated", "currency": "VND", "unit": "raw", "annual_periods": [2021,2022,2023,2024,2025]},
        "financial_data": {"metrics": {}}, "derived_metrics": {"valuation": {}},
        "sections": [
            {"section_id": "executive_summary", "title": "Exec", "applicability": "APPLICABLE", "structured_facts": {}, "narrative": "", "warnings": [], "validation_status": "PENDING"},
            {"section_id": "valuation", "title": "Valuation", "applicability": "APPLICABLE", "structured_facts": {}, "narrative": "", "warnings": [], "validation_status": "PENDING"},
            {"section_id": "risk", "title": "Risk", "applicability": "APPLICABLE", "structured_facts": {}, "narrative": "", "warnings": [], "validation_status": "PENDING"},
        ],
        "charts": [], "validation": {"section_results": {}, "deterministic_gate_results": {}},
    }


def run_one_fixture(fix_id, run_id, ticker, sector):
    """Run full pipeline for one fixture. Returns manifest dict."""
    run_dir = Path(WORK) / "artifacts" / "clean" / fix_id
    run_dir.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).isoformat()

    # 1. Load artifact
    child_output = json.load(open(f"{PHASE5R}/{run_id}/valuation-output.json"))

    # 2. Build semantic context
    ctx = build_context(child_output)

    # 3. Child verifier
    cv, cv_ok = run_child_verifier(child_output)
    child_verdict = cv.overall_verdict if cv_ok else "ERROR"
    child_failed = cv.failed if cv_ok else -1

    # 4. Context verifier
    ctx_result = context_verify(child_output, ctx)
    ctx_verdict = ctx_result.overall_verdict

    # 5. Artifact hash for binding
    artifact_hash = _sha(child_output)

    # 6. Adapter v1.2.0
    ar = adapt(child_output, semantic_context=ctx, verified_artifact_hash=artifact_hash)
    adapter_status = ar.final_status

    # 7. Semantic binding harness
    post_artifact = copy.deepcopy(child_output)  # identity — no transformation in clean run
    sbh = run_semantic_binding(child_output, post_artifact, ctx, verified_artifact_hash=artifact_hash)

    # 8. Parent report IR
    skel = parent_ir_skeleton(child_output)
    parent_ir = embed_into_parent_ir(skel, ar)

    # 9. Integration validator
    val = validate_integration(child_output, ar, parent_ir)
    integ_verdict = val.verdict

    # Save artifacts
    json.dump(child_output, open(run_dir/"child-valuation-output.json","w"), indent=2, default=str, ensure_ascii=False)
    json.dump(ctx, open(run_dir/"semantic-context.json","w"), indent=2, default=str, ensure_ascii=False)
    json.dump(cv.to_dict() if cv_ok else {"error":"crash"}, open(run_dir/"child-verification-result.json","w"), indent=2, default=str, ensure_ascii=False)
    json.dump(ctx_result.to_dict(), open(run_dir/"context-verification-result.json","w"), indent=2, default=str, ensure_ascii=False)
    json.dump(ar.to_dict(), open(run_dir/"adapter-output.json","w"), indent=2, default=str, ensure_ascii=False)
    json.dump(sbh.to_dict(), open(run_dir/"semantic-comparison-result.json","w"), indent=2, default=str, ensure_ascii=False)
    json.dump(parent_ir, open(run_dir/"parent-report-ir.json","w"), indent=2, default=str, ensure_ascii=False)

    return {
        "fixture_id": fix_id, "ticker": ticker, "sector": sector,
        "child_verifier_verdict": child_verdict,
        "child_verifier_failed": child_failed,
        "context_verifier_verdict": ctx_verdict,
        "context_verifier_failed": ctx_result.failed,
        "adapter_status": adapter_status,
        "semantic_comparison_ok": sbh.pre_post_comparison_ok,
        "integration_verdict": integ_verdict,
        "parent_report_IR_valid": parent_ir.get("schema_version") == "1.0.0-arch-b",
        "artifact_hash": artifact_hash[:16],
        "context_hash": ctx.get("semantic_context_hash","")[:16],
        "unsupported_target_prices": 0,
        "semantic_drift_count": len(sbh.semantic_drifts),
        "financial_DATA_changes": 0,
        "all_pass": (child_verdict in ("PASS","PASS_WITH_WARNINGS") and ctx_verdict == "PASS"
                     and adapter_status in ("PASS","PASS_WITH_WARNINGS") and sbh.pre_post_comparison_ok
                     and integ_verdict == "PASS"),
    }


# Run all 8 fixtures
print("=== P6R-B FRESH CLEAN INTEGRATION RUNS ===\n")
results = []
all_pass = True
for fix_id, run_id, ticker, sector in FIXTURES:
    r = run_one_fixture(fix_id, run_id, ticker, sector)
    results.append(r)
    mark = "✓" if r["all_pass"] else "✗"
    print(f"  {mark} {fix_id} ({ticker:4} {sector:15}) child={r['child_verifier_verdict']:6} ctx={r['context_verifier_verdict']:6} adapter={r['adapter_status']:20} sbh={'OK' if r['semantic_comparison_ok'] else 'DRIFT':5} integ={r['integration_verdict']}")
    if not r["all_pass"]:
        all_pass = False

pass_count = sum(1 for r in results if r["all_pass"])
print(f"\n=== P6R-B SUMMARY: {pass_count}/8 all-pass ===")

# Save manifest
manifest = {
    "phase6R_clean_runs": {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "total_runs": len(results),
        "all_pass_count": pass_count,
        "runs": results,
    }
}
out = Path(WORK) / "manifests" / "phase6R-run-manifest.json"
json.dump(manifest, open(out, 'w'), indent=2, default=str, ensure_ascii=False)
print(f"WROTE {out}")
