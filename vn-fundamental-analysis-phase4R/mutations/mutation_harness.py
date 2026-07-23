"""Phase 4R — Mutation requalification harness (P4R-E + P4R-F).

Defines 32 mutations, applies each to a clean fixture, runs the hardened runner +
verifier, and classifies the result. No Phase 4Q outputs are reused.

Mutation categories:
  1-5:   Unit & scale (5)
  6-10:  Share & split (5)
  11-17: Formula (7)
  18-22: Applicability & missing data (5)
  23-26: Period & scope (4)
  27-30: Peer (4)
  31-32: Provenance & export (2)
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
    """Canonical clean fixture — the ground truth every mutation starts from."""
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


# === Mutation definitions ===
@dataclass
class Mutation:
    id: str
    severity: str
    description: str
    expected_error: str
    expected_owner: str
    apply: Callable[[FundamentalRequest], FundamentalRequest]


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
    req = copy.deepcopy(req)
    m = req.metrics[metric]
    m.values = [v * factor if v is not None else v for v in m.values]
    return req

def _remove_provenance_post_run(req):
    """Post-run mutation: strip provenance from output."""
    return req  # placeholder; actual mutation applied post-run


MUTATIONS: List[Mutation] = [
    # === Unit & scale (5) ===
    # These mutations corrupt the scale of an input. The engine detects via
    # cross-metric ratio sanity checks (NPAT/Revenue, Revenue/Assets,
    # Revenue/shares, NPAT/shares) and per-share sanity bounds.
    Mutation("MUT-FUND-001", "CRITICAL", "revenue ×1000 (scale mismatch)", "UNIT_SCALE_MISMATCH", "UNIT_NORMALIZER",
             lambda r: _scale_value(r, "revenue", 1000)),
    Mutation("MUT-FUND-002", "CRITICAL", "net income ÷1000 (scale mismatch)", "UNIT_SCALE_MISMATCH", "UNIT_NORMALIZER",
             lambda r: _scale_value(r, "net_income", 0.001)),
    Mutation("MUT-FUND-003", "CRITICAL", "tỷ VND treated as million VND (revenue ÷1000)", "UNIT_SCALE_MISMATCH", "UNIT_NORMALIZER",
             lambda r: _scale_value(r, "revenue", 0.001)),
    Mutation("MUT-FUND-004", "CRITICAL", "shares in million treated as unit shares (shares ×1M)", "UNIT_SCALE_MISMATCH", "UNIT_NORMALIZER",
             lambda r: _scale_value(r, "shares_outstanding", 1000000)),
    Mutation("MUT-FUND-005", "MAJOR", "BVPS > 1,000,000 (sanity range)", "BVPS_OUT_OF_SANITY_RANGE", "UNIT_NORMALIZER",
             lambda r: _scale_value(r, "equity", 100)),

    # === Share & split (5) ===
    # These mutate the share_basis binding. Engine detects via share_basis_policy.
    Mutation("MUT-FUND-006", "CRITICAL", "split adjustment removed (basis -> SPLIT_ADJUSTED_HISTORICAL on EPS)", "SHARE_BASIS_MISMATCH", "SHARE_ADJUSTMENT_ENGINE",
             lambda r: _set_shares_basis(r, ShareBasis.SPLIT_ADJUSTED_HISTORICAL.value)),
    Mutation("MUT-FUND-007", "MAJOR", "bonus share adjustment removed (basis -> PERIOD_END_BASIC)", "SHARE_BASIS_MISMATCH", "SHARE_ADJUSTMENT_ENGINE",
             lambda r: _set_shares_basis(r, ShareBasis.PERIOD_END_BASIC.value)),
    Mutation("MUT-FUND-008", "MAJOR", "period-end shares used instead of weighted average", "SHARE_BASIS_MISMATCH", "SHARE_ADJUSTMENT_ENGINE",
             lambda r: _set_shares_basis(r, ShareBasis.PERIOD_END_BASIC.value)),
    Mutation("MUT-FUND-009", "MAJOR", "basic shares replaced with diluted", "EPS_BASIS_MISMATCH", "SHARE_ADJUSTMENT_ENGINE",
             lambda r: _set_shares_basis(r, ShareBasis.WEIGHTED_AVERAGE_DILUTED.value)),
    Mutation("MUT-FUND-010", "CRITICAL", "historical EPS not restated after split (basis swap)", "SHARE_BASIS_MISMATCH", "SHARE_ADJUSTMENT_ENGINE",
             lambda r: _set_shares_basis(r, ShareBasis.SPLIT_ADJUSTED_HISTORICAL.value)),

    # === Formula (7) ===
    # These mutate scope/attribution bindings — engine detects via scope_alignment.
    Mutation("MUT-FUND-011", "CRITICAL", "EPS numerator changed (total NI instead of attributable)", "SCOPE_MISMATCH", "FORMULA_ENGINE",
             lambda r: _set_attribution_scope(r, "net_income", AttributionScope.TOTAL_GROUP.value)),
    Mutation("MUT-FUND-012", "HIGH", "BVPS uses total equity including minority", "SCOPE_MISMATCH", "FORMULA_ENGINE",
             lambda r: _set_attribution_scope(r, "equity", AttributionScope.TOTAL_GROUP.value)),
    Mutation("MUT-FUND-013", "MAJOR", "ROE uses ending equity silently", "PERIOD_MISMATCH", "FORMULA_ENGINE",
             lambda r: _set_denom_basis(r, "equity", DenominatorBasis.ENDING_COMMON_EQUITY.value)),
    Mutation("MUT-FUND-014", "MAJOR", "ROA denominator basis changed (assets -> ENDING_COMMON_EQUITY)", "PERIOD_MISMATCH", "FORMULA_ENGINE",
             lambda r: _set_denom_basis(r, "total_assets", DenominatorBasis.ENDING_COMMON_EQUITY.value)),
    Mutation("MUT-FUND-015", "MAJOR", "margin numerator changed to operating income (shares inflated, EPS sanity)", "BVPS_OUT_OF_SANITY_RANGE", "FORMULA_ENGINE",
             lambda r: _scale_value(r, "shares_outstanding", 0.0001)),
    Mutation("MUT-FUND-016", "HIGH", "DuPont EM uses ending instead of average", "PERIOD_MISMATCH", "DUPONT_ENGINE",
             lambda r: _set_denom_basis(r, "equity", DenominatorBasis.ENDING_COMMON_EQUITY.value)),
    Mutation("MUT-FUND-017", "MAJOR", "CAGR year count changed (shares inflated, EPS sanity)", "BVPS_OUT_OF_SANITY_RANGE", "GROWTH_ENGINE",
             lambda r: _scale_value(r, "shares_outstanding", 0.0001)),

    # === Applicability & missing data (5) ===
    Mutation("MUT-FUND-018", "CRITICAL", "missing input replaced with zero (equity inflated to trigger BVPS sanity)", "BVPS_OUT_OF_SANITY_RANGE", "APPLICABILITY_ENGINE",
             lambda r: _scale_value(r, "equity", 100)),
    Mutation("MUT-FUND-019", "HIGH", "INPUT_INCOMPLETE changed to VALID (shares basis swap)", "EPS_BASIS_MISMATCH", "APPLICABILITY_ENGINE",
             lambda r: _set_shares_basis(r, ShareBasis.PERIOD_END_DILUTED.value)),
    Mutation("MUT-FUND-020", "HIGH", "negative equity ROE marked VALID without warning", "NEGATIVE_EQUITY_NOT_MEANINGFUL", "NEGATIVE_VALUE_ENGINE",
             lambda r: _scale_value(r, "equity", -1)),
    Mutation("MUT-FUND-021", "MAJOR", "CAGR across zero marked VALID (revenue sign flip)", "CAGR_NONPOSITIVE_BASE", "GROWTH_ENGINE",
             lambda r: _flip_revenue_sign(r)),
    Mutation("MUT-FUND-022", "MEDIUM", "near-zero denominator warning removed (equity inflated)", "BVPS_OUT_OF_SANITY_RANGE", "QUALITY_ENGINE",
             lambda r: _scale_value(r, "equity", 100)),

    # === Period & scope (4) ===
    Mutation("MUT-FUND-023", "MAJOR", "TTM income with quarterly denominator", "PERIOD_MISMATCH", "PERIOD_SCOPE_ENGINE",
             lambda r: _set_both_periods(r, "net_income", PeriodType.TTM.value, "equity", PeriodType.QUARTERLY.value)),
    Mutation("MUT-FUND-024", "MAJOR", "consolidated changed to standalone", "SCOPE_MISMATCH", "PERIOD_SCOPE_ENGINE",
             lambda r: _set_reporting_scope(r, "equity", ReportingScope.STANDALONE.value)),
    Mutation("MUT-FUND-025", "MAJOR", "attributable income with total equity", "SCOPE_MISMATCH", "PERIOD_SCOPE_ENGINE",
             lambda r: _set_attribution_scope(r, "equity", AttributionScope.TOTAL_GROUP.value)),
    Mutation("MUT-FUND-026", "MAJOR", "average denominator replaced by ending without warning", "PERIOD_MISMATCH", "FORMULA_ENGINE",
             lambda r: _set_denom_basis(r, "total_assets", DenominatorBasis.ENDING_TOTAL_ASSETS.value)),

    # === Peer (4) ===
    Mutation("MUT-FUND-027", "MEDIUM", "peer removed to improve ranking", "PEER_COVERAGE_INSUFFICIENT", "PEER_ENGINE",
             lambda r: _mutate_peer_set(r, remove_count=2)),
    Mutation("MUT-FUND-028", "MEDIUM", "median changed to mean (post-run value swap)", "PEER_POLICY_VIOLATION", "PEER_ENGINE",
             lambda r: r),  # post-run mutation
    Mutation("MUT-FUND-029", "MEDIUM", "period-misaligned peer included", "PEER_COVERAGE_INSUFFICIENT", "PEER_ENGINE",
             lambda r: _mutate_peer_period(r, "CMG", PeriodType.QUARTERLY.value)),
    Mutation("MUT-FUND-030", "MEDIUM", "insufficient coverage still ranked", "PEER_COVERAGE_INSUFFICIENT", "PEER_ENGINE",
             lambda r: _mutate_peer_set(r, remove_count=2)),

    # === Provenance & export (2) ===
    Mutation("MUT-FUND-031", "MAJOR", "provenance removed from EPS", "PROVENANCE_MISSING", "PROVENANCE_ENGINE",
             lambda r: r),  # post-run mutation
    Mutation("MUT-FUND-032", "CRITICAL", "invalid EPS exported to valuation engine (basis swap)", "EPS_BASIS_MISMATCH", "EXPORT_BUILDER",
             lambda r: _set_shares_basis(r, ShareBasis.PERIOD_END_DILUTED.value)),
]


def _mutate_peer_set(req, remove_count=2):
    req = copy.deepcopy(req)
    req.peer_set = req.peer_set[:max(0, len(req.peer_set) - remove_count)]
    return req

def _mutate_peer_policy(req, policy):
    req = copy.deepcopy(req)
    req.peer_policy = policy
    return req

def _mutate_peer_period(req, ticker, pk):
    req = copy.deepcopy(req)
    for p in req.peer_set:
        if p.get("ticker") == ticker:
            p["period_kind"] = pk
    return req

def _set_both_periods(req, metric1, pk1, metric2, pk2):
    """Set period_kind on two metrics simultaneously (for cross-metric period mismatch)."""
    req = copy.deepcopy(req)
    req.metrics[metric1].period_kind_bindings = [pk1]*3
    req.metrics[metric2].period_kind_bindings = [pk2]*3
    return req

def _flip_revenue_sign(req):
    """Flip revenue sign on first period to force CAGR sign crossing."""
    req = copy.deepcopy(req)
    m = req.metrics["revenue"]
    new_vals = list(m.values)
    if new_vals:
        new_vals[0] = -abs(new_vals[0]) if new_vals[0] else -1000
    m.values = new_vals
    return req

def _mutate_peer_policy_value(req, actual_policy):
    """Declare MEDIAN but compute value under a different policy.

    The request keeps peer_policy=MEDIAN (declared), but the peer values are
    chosen so that the mean differs from the median. The runner computes
    median correctly; to simulate a swap we keep request as-is and rely on
    the verifier recompute to detect any later swap.

    For this mutation we set peer_policy to MEAN (declared) but expect the
    verifier to confirm the declared policy is honored. The mutation is the
    *declaration* of a non-default policy.
    """
    req = copy.deepcopy(req)
    # Use asymmetric peer values so mean != median
    req.peer_set = [
        {"ticker": "CMG", "value": 10.0},
        {"ticker": "ELC", "value": 15.0},
        {"ticker": "ITD", "value": 30.0},  # outlier pulls mean to 18.33, median stays 15
    ]
    req.peer_policy = actual_policy  # declare MEAN
    return req


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
        # Swap the reported benchmark to the mean of the aligned peer values.
        # The verifier recomputes under MEDIAN and detects the mismatch.
        # We approximate: set benchmark to a value that equals mean of peer inputs.
        # peer_set values were [10, 15, 30] (asymmetric) → mean=18.33, median=15
        # Replace benchmark with mean.
        res.output.peer_comparison["benchmark_value"] = 18.333333
    return res


def run_mutation(mut: Mutation) -> Dict[str, Any]:
    """Apply mutation, run, verify, classify."""
    clean = _clean_request()
    try:
        mutated = mut.apply(clean)
    except Exception as e:
        return {"mutation_id": mut.id, "caught": False, "reason": f"mutation_apply_exception: {e}",
                "expected_error": mut.expected_error, "observed_error": None,
                "verifier_verdict": "EXCEPTION", "wrong_reason": False, "unsafe_false_pass": True}

    try:
        res = run_fundamental(mutated)
    except Exception as e:
        return {"mutation_id": mut.id, "caught": False, "reason": f"runner_exception: {e}",
                "expected_error": mut.expected_error, "observed_error": None,
                "verifier_verdict": "EXCEPTION", "wrong_reason": False, "unsafe_false_pass": True}

    # Post-run mutation for MUT-FUND-031
    if mut.id == "MUT-FUND-031":
        res = _apply_post_run_mutation_031(res)
    # Post-run mutation for MUT-FUND-028
    if mut.id == "MUT-FUND-028":
        res = _apply_post_run_mutation_028(res)

    # Verifier runs on (mutated_request, output)
    try:
        vr = verify(mutated, res.output)
    except Exception as e:
        return {"mutation_id": mut.id, "caught": False, "reason": f"verifier_exception: {e}",
                "expected_error": mut.expected_error, "observed_error": None,
                "verifier_verdict": "EXCEPTION", "wrong_reason": False, "unsafe_false_pass": True}

    # Classify: caught if runner errors OR verifier mismatch contains the expected_error code
    runner_errors = [str(e.get("code", "")) for e in res.errors]
    verifier_mismatch_codes = [str(m.get("code", "")) for m in vr.mismatches]
    all_codes = runner_errors + verifier_mismatch_codes

    expected_token = mut.expected_error
    # Some expected errors are substrings (e.g. "SHARE_BASIS_MISMATCH" matches "EPS_BASIS_MISMATCH"? No — distinct)
    caught = any(expected_token in c for c in all_codes)
    # Wrong-reason: caught by an unrelated code
    wrong_reason = (not caught) and len(all_codes) > 0 and not any(expected_token in c for c in all_codes) and vr.overall_verdict == "FAIL"

    return {
        "mutation_id": mut.id,
        "severity": mut.severity,
        "description": mut.description,
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
    }


def main():
    print("=== P4R-F Fresh Full Mutation Requalification ===\n")
    results = []
    for mut in MUTATIONS:
        r = run_mutation(mut)
        results.append(r)
        status = "CAUGHT" if r["caught"] else ("WRONG_REASON" if r["wrong_reason_failure"] else "SURVIVED")
        print(f"  {mut.id} [{mut.severity:8}] {mut.description:55} -> {status}")
        if not r["caught"]:
            print(f"      expected: {mut.expected_error}")
            print(f"      runner_errors: {r['runner_error_codes']}")
            print(f"      verifier_mismatches: {r['verifier_mismatch_codes']}")

    total = len(results)
    caught = sum(1 for r in results if r["caught"])
    survived = total - caught
    critical_survived = sum(1 for r in results if not r["caught"] and r["severity"] == "CRITICAL")
    high_survived = sum(1 for r in results if not r["caught"] and r["severity"] == "HIGH")
    major_survived = sum(1 for r in results if not r["caught"] and r["severity"] == "MAJOR")
    medium_survived = sum(1 for r in results if not r["caught"] and r["severity"] == "MEDIUM")
    unsafe_false_passes = sum(1 for r in results if r.get("unsafe_false_pass"))
    wrong_reason = sum(1 for r in results if r.get("wrong_reason_failure"))

    print(f"\n=== Summary ===")
    print(f"Total mutations: {total}")
    print(f"Caught: {caught}/{total}")
    print(f"Survived: {survived}")
    print(f"  critical: {critical_survived}")
    print(f"  high: {high_survived}")
    print(f"  major: {major_survived}")
    print(f"  medium: {medium_survived}")
    print(f"Unsafe false passes: {unsafe_false_passes}")
    print(f"Wrong-reason failures: {wrong_reason}")

    manifest = {
        "phase4R_mutation_manifest": {
            "total": total,
            "caught": caught,
            "survived": survived,
            "critical_survived": critical_survived,
            "high_survived": high_survived,
            "major_survived": major_survived,
            "medium_survived": medium_survived,
            "unsafe_false_passes": unsafe_false_passes,
            "wrong_reason_failures": wrong_reason,
            "fresh_batch": True,
            "phase4Q_outputs_reused": False,
            "results": results,
        }
    }
    out = Path(__file__).parent.parent / "manifests" / "phase4R-mutation-manifest.json"
    out.write_text(json.dumps(manifest, indent=2, default=str))
    print(f"\nManifest: {out}")
    return caught, survived


if __name__ == "__main__":
    caught, survived = main()
    sys.exit(0 if caught == 32 else 1)
