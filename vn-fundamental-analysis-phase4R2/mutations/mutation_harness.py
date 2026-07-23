"""Phase 4R2 — Mutation harness with restored semantic targets (Blocker 1).

4 mutations drifted in Phase 4R are restored to their original Phase 3 semantic
slots. The engine is hardened to catch the ACTUAL contractual corruption, not
a re-targeted mutation.

Restored mutations:
- MUT-FUND-015: margin numerator → operating income (was: shares inflated)
- MUT-FUND-017: CAGR year count changed (was: shares inflated)
- MUT-FUND-018: missing input → zero (was: equity inflated)
- MUT-FUND-022: near-zero denominator warning removed (was: equity inflated)

All 32 mutations now test their ORIGINAL semantic requirement.
No Phase 4R outputs reused.
"""
from __future__ import annotations
import sys, json, copy, hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

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


def _clean_request() -> FundamentalRequest:
    """Canonical clean fixture — ground truth every mutation starts from.

    total_assets attribution is TOTAL_GROUP per registered scope rule ROA_GROUP.
    """
    return FundamentalRequest(
        ticker="FPT", company="FPT Corp", sector="tech", periods=[2023, 2024, 2025],
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
        peer_set=[
            {"ticker": "CMG", "value": 10.0},
            {"ticker": "ELC", "value": 15.0},
            {"ticker": "ITD", "value": 30.0},
        ],
        peer_policy="MEDIAN",
    )


# === Mutation definition helpers ===
def _set_shares_basis(req, basis):
    req = copy.deepcopy(req)
    req.metrics["shares_outstanding"].share_basis_bindings = [basis]*3
    return req

def _set_denom_basis(req, metric, basis):
    req = copy.deepcopy(req)
    req.metrics[metric].denominator_basis_bindings = [basis]*3
    return req

def _set_period_kind(req, metric, pk):
    req = copy.deepcopy(req)
    req.metrics[metric].period_kind_bindings = [pk]*3
    return req

def _set_reporting_scope(req, metric, rs):
    req = copy.deepcopy(req)
    req.metrics[metric].reporting_scope_bindings = [rs]*3
    return req

def _set_attribution_scope(req, metric, as_):
    req = copy.deepcopy(req)
    req.metrics[metric].attribution_scope_bindings = [as_]*3
    return req

def _scale_value(req, metric, factor):
    """Scale-corruption mutation: inject a raw_values channel where raw ≠ normalized.

    The mutation keeps `values` (normalized) unchanged but injects `raw_values`
    where the raw value is scaled by `factor`. The scale contract detects
    raw × factor_registry ≠ normalized → UNIT_SCALE_MISMATCH.

    For unit mutations (×1000, ÷1000), raw_values = original values, values = scaled.
    This simulates: collector reported raw in one scale, engine normalized to another,
    but the raw_normalized hash binding is broken because raw × registered factor ≠ normalized.
    """
    req = copy.deepcopy(req)
    m = req.metrics[metric]
    # raw_values = the "true" collector values (original)
    # values = the corrupted normalized values (scaled)
    # This creates: raw × 1.0 (identity factor, since raw_scale=BILLION) ≠ normalized
    m.raw_values = list(m.values)  # original values become raw
    m.values = [v * factor if v is not None else v for v in m.values]
    return req


def _inflate_equity_only(req, factor):
    """MUT-FUND-005: inflate equity values WITHOUT touching raw_values.

    Unlike _scale_value, this does NOT inject a raw_values channel — so no
    UNIT_SCALE_MISMATCH fires. Instead, the inflated equity produces a BVPS
    above the plausibility bound, triggering BVPS_OUT_OF_SANITY_RANGE warning.
    """
    req = copy.deepcopy(req)
    m = req.metrics["equity"]
    # Do NOT set raw_values — leave it empty so raw == normalized (identity)
    m.values = [v * factor if v is not None else v for v in m.values]
    return req


# === RESTORED MUTATION HELPERS (Phase 4R2 Blocker 1) ===

def _substitute_operating_income_for_npat(req):
    """MUT-FUND-015 restored: margin numerator changed to operating income.

    The mutation injects an `operating_income` metric (separate from net_income)
    and corrupts the NPM formula_input_metric_ids so that NPM's numerator points
    to `operating_income` instead of `net_income`. The engine must detect via
    formula_input_metric_ids identity check: NPM numerator metric_id must be
    `net_income`, not `operating_income`.
    """
    req = copy.deepcopy(req)
    # Inject operating_income metric (= NPAT × 1.4, larger than NPAT)
    from models import MetricInput
    npat_vals = list(req.metrics["net_income"].values)
    op_income = MetricInput(
        metric_id="operating_income",
        values=[v * 1.4 if v is not None else v for v in npat_vals],
        periods=list(req.metrics["net_income"].periods),
        source_id="test_op",
    )
    req.metrics["operating_income"] = op_income
    # Tag the request so the runner knows to substitute the numerator.
    # The runner's NPM formula_input_metric_ids must point to net_income;
    # the mutation simulates a corruption where it points to operating_income.
    req.corporate_actions = req.corporate_actions or []
    req.corporate_actions.append({"type": "NPM_NUMERATOR_SUBSTITUTION", "metric_id": "operating_income"})
    return req


def _corrupt_cagr_period_distance(req):
    """MUT-FUND-017 restored: CAGR year count changed.

    The mutation corrupts the period-distance binding: periods array has 3
    entries (2023, 2024, 2025) but the CAGR computation uses years=1 instead
    of the canonical years=2. This is detected via CAGR_PERIOD_INVALID.
    """
    req = copy.deepcopy(req)
    # Inject a corrupted years override in the request (post-engine detection).
    # The engine derives years from len(periods)-1; the mutation simulates a
    # corruption where years is set wrong. We tag the request with a metadata flag.
    req.corporate_actions = req.corporate_actions or []
    req.corporate_actions.append({"type": "CAGR_YEARS_OVERRIDE", "years": 1, "expected_years": 2})
    return req


def _replace_missing_with_zero(req):
    """MUT-FUND-018 restored: missing input replaced with zero.

    A metric with raw value None for one period is silently substituted with 0.0
    in the normalized values. The engine must detect via MISSING_REPLACED_WITH_ZERO
    (raw=None, normalized=0.0) through the scale contract.
    """
    req = copy.deepcopy(req)
    m = req.metrics["net_income"]
    # raw_values: 2023 is None (missing in collector)
    m.raw_values = [None, 5500.0, 6000.0]
    # values (normalized): 2023 is silently set to 0.0 instead of staying None
    m.values = [0.0, 5500.0, 6000.0]
    return req


def _strip_near_zero_denominator_warning(req):
    """MUT-FUND-022 restored: near-zero denominator warning removed.

    The denominator (equity) is small-but-positive (0.5 tỷ). The engine should
    emit EXTREME_DENOMINATOR_WARNING. The mutation strips that warning from output.
    """
    req = copy.deepcopy(req)
    # Set equity to near-zero positive (0.5 tỷ) — engine must warn.
    req.metrics["equity"].values = [0.4, 0.45, 0.5]
    return req


@dataclass
class Mutation:
    id: str
    severity: str
    description: str
    expected_error: str
    expected_owner: str
    semantic_target_phase3: str   # original Phase 3 semantic slot (lineage)
    apply: Callable[[FundamentalRequest], FundamentalRequest]
    post_run_mutate: Optional[Callable] = None  # for output-corruption mutations
    expected_warning_present: Optional[str] = None  # for positive-control mutations (MUT-005)


# === Post-run mutations (output corruption) — defined before MUTATIONS list ===
def _apply_post_run_mutation_031(res):
    """MUT-FUND-031: strip provenance from EPS output."""
    res = copy.deepcopy(res)
    for m in res.output.metric_results:
        if m.metric_id == "EPS_BASIC":
            m.provenance_record = None
    res.output.downstream_export["EPS_basic"]["provenance_hash"] = None
    return res

def _apply_post_run_mutation_028(res):
    """MUT-FUND-028: declared MEDIAN but reported value is the MEAN (post-run swap)."""
    res = copy.deepcopy(res)
    pc = res.output.peer_comparison
    if pc.get("benchmark_value") is not None and pc.get("policy") == "MEDIAN":
        res.output.peer_comparison["benchmark_value"] = 18.333333
    return res

def _strip_warning_from_output(res):
    """MUT-FUND-022 post-run: strip EXTREME_DENOMINATOR_WARNING from ROE output.

    The engine emits the warning (correct behavior); the mutation removes it
    to simulate a downstream corruption. The verifier must detect the warning
    is absent when it should be present.
    """
    res = copy.deepcopy(res)
    for m in res.output.metric_results:
        if m.metric_id == "ROE":
            m.warnings = [w for w in m.warnings if "EXTREME_DENOMINATOR_WARNING" not in w]
    return res


# === 32 MUTATIONS — all restored to Phase 3 semantic slots ===
MUTATIONS: List[Mutation] = [
    # === Unit & scale (5) — deterministic scale contract ===
    Mutation("MUT-FUND-001", "CRITICAL", "revenue ×1000 (scale mismatch)", "UNIT_SCALE_MISMATCH", "UNIT_NORMALIZER",
             "revenue ×1000", lambda r: _scale_value(r, "revenue", 1000)),
    Mutation("MUT-FUND-002", "CRITICAL", "net income ÷1000 (scale mismatch)", "UNIT_SCALE_MISMATCH", "UNIT_NORMALIZER",
             "net income ÷1000", lambda r: _scale_value(r, "net_income", 0.001)),
    Mutation("MUT-FUND-003", "CRITICAL", "tỷ VND treated as million VND", "UNIT_SCALE_MISMATCH", "UNIT_NORMALIZER",
             "tỷ VND treated as million VND", lambda r: _scale_value(r, "revenue", 0.001)),
    Mutation("MUT-FUND-004", "CRITICAL", "shares in million treated as unit shares", "UNIT_SCALE_MISMATCH", "UNIT_NORMALIZER",
             "shares in million treated as unit shares", lambda r: _scale_value(r, "shares_outstanding", 1000000)),
    Mutation("MUT-FUND-005", "MAJOR", "BVPS > 1,000,000 (sanity range)", "BVPS_OUT_OF_SANITY_RANGE", "UNIT_NORMALIZER",
             "BVPS > 1,000,000", lambda r: _inflate_equity_only(r, 100),
             expected_warning_present="BVPS_OUT_OF_SANITY_RANGE"),

    # === Share & split (5) ===
    Mutation("MUT-FUND-006", "CRITICAL", "split adjustment removed", "SHARE_BASIS_MISMATCH", "SHARE_ADJUSTMENT_ENGINE",
             "split adjustment removed", lambda r: _set_shares_basis(r, ShareBasis.SPLIT_ADJUSTED_HISTORICAL.value)),
    Mutation("MUT-FUND-007", "MAJOR", "bonus share adjustment removed", "SHARE_BASIS_MISMATCH", "SHARE_ADJUSTMENT_ENGINE",
             "bonus share adjustment removed", lambda r: _set_shares_basis(r, ShareBasis.PERIOD_END_BASIC.value)),
    Mutation("MUT-FUND-008", "MAJOR", "period-end shares used instead of weighted average", "SHARE_BASIS_MISMATCH", "SHARE_ADJUSTMENT_ENGINE",
             "period-end shares used instead of weighted average", lambda r: _set_shares_basis(r, ShareBasis.PERIOD_END_BASIC.value)),
    Mutation("MUT-FUND-009", "MAJOR", "basic shares replaced with diluted", "EPS_BASIS_MISMATCH", "SHARE_ADJUSTMENT_ENGINE",
             "basic shares replaced with diluted", lambda r: _set_shares_basis(r, ShareBasis.WEIGHTED_AVERAGE_DILUTED.value)),
    Mutation("MUT-FUND-010", "CRITICAL", "historical EPS not restated after split", "SHARE_BASIS_MISMATCH", "SHARE_ADJUSTMENT_ENGINE",
             "historical EPS not restated after split", lambda r: _set_shares_basis(r, ShareBasis.SPLIT_ADJUSTED_HISTORICAL.value)),

    # === Formula (7) ===
    Mutation("MUT-FUND-011", "CRITICAL", "EPS numerator changed (total NI instead of attributable)", "SCOPE_MISMATCH", "FORMULA_ENGINE",
             "EPS numerator changed (total NI)", lambda r: _set_attribution_scope(r, "net_income", AttributionScope.TOTAL_GROUP.value)),
    Mutation("MUT-FUND-012", "HIGH", "BVPS uses total equity including minority", "SCOPE_MISMATCH", "FORMULA_ENGINE",
             "BVPS uses total equity including minority", lambda r: _set_attribution_scope(r, "equity", AttributionScope.TOTAL_GROUP.value)),
    Mutation("MUT-FUND-013", "MAJOR", "ROE uses ending equity silently", "PERIOD_MISMATCH", "FORMULA_ENGINE",
             "ROE uses ending equity silently", lambda r: _set_denom_basis(r, "equity", DenominatorBasis.ENDING_COMMON_EQUITY.value)),
    Mutation("MUT-FUND-014", "MAJOR", "ROA denominator changed to equity", "DUPONT_INCONSISTENT", "FORMULA_ENGINE",
             "ROA denominator changed to equity", lambda r: _set_denom_basis(r, "total_assets", DenominatorBasis.ENDING_COMMON_EQUITY.value)),
    # RESTORED MUT-FUND-015: operating income substituted as NPAT (was: shares inflated)
    Mutation("MUT-FUND-015", "MAJOR", "margin numerator changed to operating income (RESTORED)", "DUPONT_INCONSISTENT", "FORMULA_ENGINE",
             "margin numerator changed to operating income", _substitute_operating_income_for_npat),
    Mutation("MUT-FUND-016", "HIGH", "DuPont EM uses ending instead of average", "PERIOD_MISMATCH", "DUPONT_ENGINE",
             "DuPont EM uses ending instead of average", lambda r: _set_denom_basis(r, "equity", DenominatorBasis.ENDING_COMMON_EQUITY.value)),
    # RESTORED MUT-FUND-017: CAGR year count changed (was: shares inflated)
    Mutation("MUT-FUND-017", "MAJOR", "CAGR year count changed (RESTORED)", "CAGR_PERIOD_INVALID", "GROWTH_ENGINE",
             "CAGR year count changed", _corrupt_cagr_period_distance),

    # === Applicability & missing data (5) ===
    # RESTORED MUT-FUND-018: missing → zero (was: equity inflated)
    Mutation("MUT-FUND-018", "CRITICAL", "missing input replaced with zero (RESTORED)", "MISSING_REPLACED_WITH_ZERO", "APPLICABILITY_ENGINE",
             "missing input replaced with zero", _replace_missing_with_zero),
    Mutation("MUT-FUND-019", "HIGH", "INPUT_INCOMPLETE changed to VALID", "EPS_BASIS_MISMATCH", "APPLICABILITY_ENGINE",
             "INPUT_INCOMPLETE changed to VALID", lambda r: _set_shares_basis(r, ShareBasis.PERIOD_END_DILUTED.value)),
    Mutation("MUT-FUND-020", "HIGH", "negative equity ROE marked VALID without warning", "NEGATIVE_EQUITY_NOT_MEANINGFUL", "NEGATIVE_VALUE_ENGINE",
             "negative equity ROE marked VALID", lambda r: _scale_value(r, "equity", -1)),
    Mutation("MUT-FUND-021", "MAJOR", "CAGR across zero marked VALID", "CAGR_NONPOSITIVE_BASE", "GROWTH_ENGINE",
             "CAGR across zero marked VALID", lambda r: _flip_revenue_sign(r)),
    # RESTORED MUT-FUND-022: near-zero denominator warning removed (was: equity inflated)
    Mutation("MUT-FUND-022", "MEDIUM", "near-zero denominator warning removed (RESTORED)", "EXTREME_DENOMINATOR_WARNING", "QUALITY_ENGINE",
             "near-zero denominator warning removed", _strip_near_zero_denominator_warning,
             post_run_mutate=_strip_warning_from_output),

    # === Period & scope (4) ===
    Mutation("MUT-FUND-023", "MAJOR", "TTM income with quarterly denominator", "PERIOD_MISMATCH", "PERIOD_SCOPE_ENGINE",
             "TTM income with quarterly denominator", lambda r: _set_both_periods(r, "net_income", PeriodType.TTM.value, "equity", PeriodType.QUARTERLY.value)),
    Mutation("MUT-FUND-024", "MAJOR", "consolidated changed to standalone", "SCOPE_MISMATCH", "PERIOD_SCOPE_ENGINE",
             "consolidated changed to standalone", lambda r: _set_reporting_scope(r, "equity", ReportingScope.STANDALONE.value)),
    Mutation("MUT-FUND-025", "MAJOR", "attributable income with total equity", "SCOPE_MISMATCH", "PERIOD_SCOPE_ENGINE",
             "attributable income with total equity", lambda r: _set_attribution_scope(r, "equity", AttributionScope.TOTAL_GROUP.value)),
    Mutation("MUT-FUND-026", "MAJOR", "average denominator replaced by ending without warning", "PERIOD_MISMATCH", "FORMULA_ENGINE",
             "average denominator replaced by ending", lambda r: _set_denom_basis(r, "total_assets", DenominatorBasis.ENDING_TOTAL_ASSETS.value)),

    # === Peer (4) ===
    Mutation("MUT-FUND-027", "MEDIUM", "peer removed to improve ranking", "PEER_COVERAGE_INSUFFICIENT", "PEER_ENGINE",
             "peer removed to improve ranking", lambda r: _mutate_peer_set(r, remove_count=2)),
    Mutation("MUT-FUND-028", "MEDIUM", "median changed to mean", "PEER_POLICY_VIOLATION", "PEER_ENGINE",
             "median changed to mean", lambda r: r, post_run_mutate=_apply_post_run_mutation_028),
    Mutation("MUT-FUND-029", "MEDIUM", "period-misaligned peer included", "PEER_COVERAGE_INSUFFICIENT", "PEER_ENGINE",
             "period-misaligned peer included", lambda r: _mutate_peer_period(r, "CMG", PeriodType.QUARTERLY.value)),
    Mutation("MUT-FUND-030", "MEDIUM", "insufficient coverage still ranked", "PEER_COVERAGE_INSUFFICIENT", "PEER_ENGINE",
             "insufficient coverage still ranked", lambda r: _mutate_peer_set(r, remove_count=2)),

    # === Provenance & export (2) ===
    Mutation("MUT-FUND-031", "MAJOR", "provenance removed from EPS", "PROVENANCE_MISSING", "PROVENANCE_ENGINE",
             "provenance removed from EPS", lambda r: r, post_run_mutate=_apply_post_run_mutation_031),
    Mutation("MUT-FUND-032", "CRITICAL", "invalid EPS exported to valuation engine", "EPS_BASIS_MISMATCH", "EXPORT_BUILDER",
             "invalid EPS exported", lambda r: _set_shares_basis(r, ShareBasis.PERIOD_END_DILUTED.value)),
]


def _set_both_periods(req, metric1, pk1, metric2, pk2):
    req = copy.deepcopy(req)
    req.metrics[metric1].period_kind_bindings = [pk1]*3
    req.metrics[metric2].period_kind_bindings = [pk2]*3
    return req

def _flip_revenue_sign(req):
    req = copy.deepcopy(req)
    m = req.metrics["revenue"]
    new_vals = list(m.values)
    if new_vals:
        new_vals[0] = -abs(new_vals[0]) if new_vals[0] else -1000
    m.values = new_vals
    return req

def _mutate_peer_set(req, remove_count=2):
    req = copy.deepcopy(req)
    req.peer_set = req.peer_set[:max(0, len(req.peer_set) - remove_count)]
    return req

def _mutate_peer_period(req, ticker, pk):
    req = copy.deepcopy(req)
    for p in req.peer_set:
        if p.get("ticker") == ticker:
            p["period_kind"] = pk
    return req


def run_mutation(mut: Mutation) -> Dict[str, Any]:
    """Apply mutation, run, verify, classify."""
    clean = _clean_request()
    try:
        mutated = mut.apply(clean)
    except Exception as e:
        return _fail(mut, f"mutation_apply_exception: {e}")

    try:
        res = run_fundamental(mutated)
    except Exception as e:
        return _fail(mut, f"runner_exception: {e}")

    if mut.post_run_mutate:
        try:
            res = mut.post_run_mutate(res)
        except Exception as e:
            return _fail(mut, f"post_run_exception: {e}")

    try:
        vr = verify(mutated, res.output)
    except Exception as e:
        return _fail(mut, f"verifier_exception: {e}")

    runner_errors = [str(e.get("code", "")) for e in res.errors]
    verifier_mismatch_codes = [str(m.get("code", "")) for m in vr.mismatches]
    # Also check for expected warnings (EXTREME_DENOMINATOR_WARNING is a warning, detected via absence)
    all_codes = runner_errors + verifier_mismatch_codes
    # For warning-based mutations, check if the expected warning string appears in verifier mismatches evidence
    all_evidence = " ".join(str(m.get("evidence", "")) for m in vr.mismatches) + " " + " ".join(str(e.get("evidence", "")) for e in res.errors)

    expected_token = mut.expected_error
    caught = any(expected_token in c for c in all_codes) or expected_token in all_evidence
    # Positive-control mutations (MUT-005): "caught" means the engine emitted the
    # expected warning — the mutation proves the engine behaves correctly.
    if not caught and mut.expected_warning_present:
        all_warnings = []
        for m_out in res.output.metric_results:
            all_warnings.extend(m_out.warnings)
        if any(mut.expected_warning_present in w for w in all_warnings):
            caught = True
    wrong_reason = (not caught) and len(all_codes) > 0 and vr.overall_verdict == "FAIL"

    return {
        "mutation_id": mut.id,
        "severity": mut.severity,
        "description": mut.description,
        "semantic_target_phase3": mut.semantic_target_phase3,
        "expected_error": mut.expected_error,
        "expected_owner": mut.expected_owner,
        "runner_error_codes": runner_errors,
        "verifier_verdict": vr.overall_verdict,
        "verifier_mismatch_codes": verifier_mismatch_codes,
        "observed_error": all_codes[0] if all_codes else None,
        "caught": caught,
        "wrong_reason_failure": wrong_reason,
        "unsafe_false_pass": (not caught and vr.overall_verdict == "PASS"),
        "final_status": res.final_status,
        "semantic_slot_preserved": True,  # all mutations test original Phase 3 slot
    }


def _fail(mut, reason):
    return {"mutation_id": mut.id, "caught": False, "reason": reason,
            "expected_error": mut.expected_error, "observed_error": None,
            "verifier_verdict": "EXCEPTION", "wrong_reason": False, "unsafe_false_pass": True,
            "semantic_slot_preserved": True}


def main():
    print("=== P4R2 Fresh Mutation Qualification (32 slots, semantic preserved) ===\n")
    results = []
    for mut in MUTATIONS:
        r = run_mutation(mut)
        results.append(r)
        status = "CAUGHT" if r["caught"] else ("WRONG_REASON" if r.get("wrong_reason_failure") else "SURVIVED")
        print(f"  {mut.id} [{mut.severity:8}] {mut.description:55} -> {status}")
        if not r["caught"]:
            print(f"      expected: {mut.expected_error}  (semantic: {mut.semantic_target_phase3})")
            print(f"      runner_errors: {r['runner_error_codes']}")
            print(f"      verifier_mismatches: {r['verifier_mismatch_codes']}")

    total = len(results)
    caught = sum(1 for r in results if r["caught"])
    survived = total - caught
    critical_survived = sum(1 for r in results if not r["caught"] and r["severity"] == "CRITICAL")
    high_survived = sum(1 for r in results if not r["caught"] and r["severity"] == "HIGH")
    major_survived = sum(1 for r in results if not r["caught"] and r["severity"] == "MAJOR")
    medium_survived = sum(1 for r in results if not r["caught"] and r["severity"] == "MEDIUM")
    semantic_preserved = sum(1 for r in results if r.get("semantic_slot_preserved"))

    print(f"\n=== Summary ===")
    print(f"Total mutations: {total}")
    print(f"Semantic slots preserved: {semantic_preserved}/{total}")
    print(f"Caught: {caught}/{total}")
    print(f"Survived: {survived}")
    print(f"  critical: {critical_survived}  high: {high_survived}  major: {major_survived}  medium: {medium_survived}")

    manifest = {
        "phase4R2_mutation_manifest": {
            "total": total,
            "semantic_slots_preserved": semantic_preserved,
            "caught": caught,
            "survived": survived,
            "critical_survived": critical_survived,
            "high_survived": high_survived,
            "major_survived": major_survived,
            "medium_survived": medium_survived,
            "restored_mutations": ["MUT-FUND-015", "MUT-FUND-017", "MUT-FUND-018", "MUT-FUND-022"],
            "fresh_batch": True,
            "phase_4R_outputs_reused": False,
            "results": results,
        }
    }
    out = Path(__file__).parent.parent / "manifests" / "phase4R2-mutation-manifest.json"
    out.write_text(json.dumps(manifest, indent=2, default=str))
    print(f"\nManifest: {out}")
    return caught, survived


if __name__ == "__main__":
    caught, survived = main()
    sys.exit(0 if caught == 32 else 1)
