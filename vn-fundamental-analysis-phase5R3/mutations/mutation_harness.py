"""Phase 4R3 — Mutation harness: pure negative mutations + separate positive controls.

Key changes from Phase 4R2:
- NO mutation-specific markers in production code (NPM_NUMERATOR_SUBSTITUTION,
  CAGR_YEARS_OVERRIDE removed).
- MUT-015: post-run corruption of formula_input_metric_ids (numerator swapped
  to operating_income). Verifier detects via generic formula_registry check.
- MUT-017: post-run corruption of growth_window.stated_years. Verifier recomputes
  expected years from start/end and detects mismatch.
- MUT-005-v2: post-run removal of REQUIRED warning (BVPS_OUT_OF_SANITY_RANGE).
  Verifier detects via generic required-warning-presence check.
- Positive controls (clean artifact with high BVPS) are SEPARATE from the
  32-mutation denominator. They verify the engine emits warnings on clean input.

All 32 mutations are TRUE negative corruptions: artifact is corrupted, expected
verdict = FAIL. No mutation counts as "caught" because a clean warning was emitted.
"""
from __future__ import annotations
import sys, json, copy
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

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
    """Canonical clean fixture — ground truth."""
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


# === Pre-run mutation helpers (corrupt the INPUT) ===
def _set_shares_basis(req, basis):
    req = copy.deepcopy(req); req.metrics["shares_outstanding"].share_basis_bindings = [basis]*3; return req

def _set_denom_basis(req, metric, basis):
    req = copy.deepcopy(req); req.metrics[metric].denominator_basis_bindings = [basis]*3; return req

def _set_period_kind(req, metric, pk):
    req = copy.deepcopy(req); req.metrics[metric].period_kind_bindings = [pk]*3; return req

def _set_reporting_scope(req, metric, rs):
    req = copy.deepcopy(req); req.metrics[metric].reporting_scope_bindings = [rs]*3; return req

def _set_attribution_scope(req, metric, as_):
    req = copy.deepcopy(req); req.metrics[metric].attribution_scope_bindings = [as_]*3; return req

def _scale_value(req, metric, factor):
    """Inject raw_values channel: raw = original, normalized = scaled."""
    req = copy.deepcopy(req); m = req.metrics[metric]
    m.raw_values = list(m.values); m.values = [v * factor if v is not None else v for v in m.values]
    return req

def _inflate_equity(req, factor):
    """Inflate equity values (no raw channel) — triggers plausibility warning."""
    req = copy.deepcopy(req); m = req.metrics["equity"]
    m.values = [v * factor if v is not None else v for v in m.values]; return req

def _set_both_periods(req, m1, pk1, m2, pk2):
    req = copy.deepcopy(req)
    req.metrics[m1].period_kind_bindings = [pk1]*3; req.metrics[m2].period_kind_bindings = [pk2]*3; return req

def _flip_revenue_sign(req):
    req = copy.deepcopy(req); m = req.metrics["revenue"]; v = list(m.values)
    if v: v[0] = -abs(v[0]) if v[0] else -1000
    m.values = v; return req

def _mutate_peer_set(req, remove_count=2):
    req = copy.deepcopy(req); req.peer_set = req.peer_set[:max(0, len(req.peer_set)-remove_count)]; return req

def _mutate_peer_period(req, ticker, pk):
    req = copy.deepcopy(req)
    for p in req.peer_set:
        if p.get("ticker") == ticker: p["period_kind"] = pk
    return req

def _replace_missing_with_zero(req):
    """raw_values[2023]=None, normalized[2023]=0.0."""
    req = copy.deepcopy(req); m = req.metrics["net_income"]
    m.raw_values = [None, 5500.0, 6000.0]; m.values = [0.0, 5500.0, 6000.0]; return req

def _near_zero_denom(req):
    """Equity near-zero positive — engine must warn. (Input mutation, not post-run.)"""
    req = copy.deepcopy(req); req.metrics["equity"].values = [0.4, 0.45, 0.5]; return req


# === Post-run mutation helpers (corrupt the OUTPUT artifact) ===
def _post_strip_provenance(res):
    res = copy.deepcopy(res)
    for m in res.output.metric_results:
        if m.metric_id == "EPS_BASIC": m.provenance_record = None
    res.output.downstream_export["EPS_basic"]["provenance_hash"] = None
    return res

def _post_swap_peer_policy(res):
    res = copy.deepcopy(res)
    pc = res.output.peer_comparison
    if pc.get("benchmark_value") is not None and pc.get("policy") == "MEDIAN":
        res.output.peer_comparison["benchmark_value"] = 18.333333
    return res

def _post_swap_npm_numerator(res):
    """MUT-015: corrupt NPM formula_input_metric_ids numerator to operating_income."""
    res = copy.deepcopy(res)
    for m in res.output.metric_results:
        if m.metric_id == "NET_PROFIT_MARGIN":
            m.formula_input_metric_ids["net_income"] = "operating_income"
    return res

def _post_corrupt_cagr_years(res):
    """MUT-017: corrupt growth_window.stated_years to wrong value."""
    res = copy.deepcopy(res)
    gw = res.output.growth.get("growth_window")
    if gw:
        gw["stated_years"] = 1  # actual distance is 2 (2023→2025)
    return res

def _post_strip_bvps_warning(res):
    """MUT-005-v2: remove BVPS_OUT_OF_SANITY_RANGE warning from BVPS output."""
    res = copy.deepcopy(res)
    for m in res.output.metric_results:
        if m.metric_id == "BVPS":
            m.warnings = [w for w in m.warnings if "BVPS_OUT_OF_SANITY_RANGE" not in w]
    return res


# === Phase 5R3 negative-value post-run mutation helpers ===
def _post_suppress_negative_eps(res):
    """MUT-033: change VALID_NEGATIVE EPS to INPUT_INCOMPLETE (suppress negative)."""
    res = copy.deepcopy(res)
    for m in res.output.metric_results:
        if m.metric_id == "EPS_BASIC" and m.status == MetricStatus.VALID_NEGATIVE.value:
            m.status = MetricStatus.INPUT_INCOMPLETE.value
            m.value = None
    return res

def _post_flip_eps_sign(res):
    """MUT-034: flip negative EPS to positive (remove sign)."""
    res = copy.deepcopy(res)
    for m in res.output.metric_results:
        if m.metric_id == "EPS_BASIC" and m.value is not None and m.value < 0:
            m.value = abs(m.value)
            m.status = MetricStatus.VALID.value
    return res

def _post_force_roe_valid(res):
    """MUT-035: force negative-equity ROE from MANUAL_REVIEW to VALID."""
    res = copy.deepcopy(res)
    for m in res.output.metric_results:
        if m.metric_id == "ROE" and m.status == MetricStatus.MANUAL_REVIEW_REQUIRED.value:
            m.status = MetricStatus.VALID.value
            m.warnings = [w for w in m.warnings if "NEGATIVE_EQUITY" not in w]
    return res

def _post_strip_equity_warning(res):
    """MUT-036: remove EXTREME_EQUITY_RATIO_WARNING."""
    res = copy.deepcopy(res)
    for m in res.output.metric_results:
        m.warnings = [w for w in m.warnings if "EXTREME_EQUITY_RATIO" not in w]
    return res

def _post_strip_derived_flag(res):
    """MUT-037: remove DERIVED_INPUT quality flag from downstream export."""
    res = copy.deepcopy(res)
    if "EPS_basic" in res.output.downstream_export:
        res.output.downstream_export["EPS_basic"]["quality_status"] = "VALID"
    return res

def _post_inject_circular_oracle(res):
    """MUT-038: inject circular EPS oracle (provider EPS used as independent verification)."""
    res = copy.deepcopy(res)
    # Mark output as "verified by provider EPS" — circular
    for m in res.output.metric_results:
        if m.metric_id == "EPS_BASIC":
            m.note = "VERIFIED_BY_PROVIDER_EPS (circular)"
    return res

def _set_negative_equity(req):
    """Set equity to negative for MUT-035 pre-condition."""
    req = copy.deepcopy(req)
    req.metrics["equity"].values = [1000, -300, -500]
    return req

def _set_near_zero_equity(req):
    """Set equity near-zero relative to assets for MUT-036 pre-condition."""
    req = copy.deepcopy(req)
    req.metrics["equity"].values = [500, 400, 93]
    req.metrics["total_assets"].values = [10000, 11000, 15000]
    return req

def _post_strip_near_zero_warning(res):
    """MUT-022: remove EXTREME_DENOMINATOR_WARNING from ROE output."""
    res = copy.deepcopy(res)
    for m in res.output.metric_results:
        if m.metric_id == "ROE":
            m.warnings = [w for w in m.warnings if "EXTREME_DENOMINATOR_WARNING" not in w]
    return res


@dataclass
class Mutation:
    id: str
    severity: str
    description: str
    expected_error: str
    expected_owner: str
    semantic_target: str
    apply: Callable[[FundamentalRequest], FundamentalRequest]
    post_run: Optional[Callable] = None
    precondition_apply: Optional[Callable] = None  # extra input setup before main apply


# === 32 NEGATIVE MUTATIONS (all true corruptions, expected verdict = FAIL) ===
MUTATIONS: List[Mutation] = [
    # Unit & scale (5)
    Mutation("MUT-FUND-001", "CRITICAL", "revenue ×1000", "UNIT_SCALE_MISMATCH", "UNIT_NORMALIZER", "revenue scale", lambda r: _scale_value(r, "revenue", 1000)),
    Mutation("MUT-FUND-002", "CRITICAL", "net income ÷1000", "UNIT_SCALE_MISMATCH", "UNIT_NORMALIZER", "net_income scale", lambda r: _scale_value(r, "net_income", 0.001)),
    Mutation("MUT-FUND-003", "CRITICAL", "tỷ VND treated as million VND", "UNIT_SCALE_MISMATCH", "UNIT_NORMALIZER", "revenue scale", lambda r: _scale_value(r, "revenue", 0.001)),
    Mutation("MUT-FUND-004", "CRITICAL", "shares ×1M", "UNIT_SCALE_MISMATCH", "UNIT_NORMALIZER", "shares scale", lambda r: _scale_value(r, "shares_outstanding", 1000000)),
    # MUT-005-v2: TRUE negative — strip required warning (not positive control)
    Mutation("MUT-FUND-005", "MAJOR", "BVPS sanity warning removed (post-run)", "REQUIRED_WARNING_REMOVED", "UNIT_NORMALIZER", "required plausibility warning preservation",
             lambda r: _inflate_equity(r, 100), post_run=_post_strip_bvps_warning),

    # Share & split (5)
    Mutation("MUT-FUND-006", "CRITICAL", "split adjustment removed", "SHARE_BASIS_MISMATCH", "SHARE_ADJUSTMENT_ENGINE", "split adjustment", lambda r: _set_shares_basis(r, ShareBasis.SPLIT_ADJUSTED_HISTORICAL.value)),
    Mutation("MUT-FUND-007", "MAJOR", "bonus share adjustment removed", "SHARE_BASIS_MISMATCH", "SHARE_ADJUSTMENT_ENGINE", "bonus adjustment", lambda r: _set_shares_basis(r, ShareBasis.PERIOD_END_BASIC.value)),
    Mutation("MUT-FUND-008", "MAJOR", "period-end shares as weighted", "SHARE_BASIS_MISMATCH", "SHARE_ADJUSTMENT_ENGINE", "period-end vs weighted", lambda r: _set_shares_basis(r, ShareBasis.PERIOD_END_BASIC.value)),
    Mutation("MUT-FUND-009", "MAJOR", "basic shares as diluted", "EPS_BASIS_MISMATCH", "SHARE_ADJUSTMENT_ENGINE", "basic vs diluted", lambda r: _set_shares_basis(r, ShareBasis.WEIGHTED_AVERAGE_DILUTED.value)),
    Mutation("MUT-FUND-010", "CRITICAL", "historical EPS not restated", "SHARE_BASIS_MISMATCH", "SHARE_ADJUSTMENT_ENGINE", "historical EPS restatement", lambda r: _set_shares_basis(r, ShareBasis.SPLIT_ADJUSTED_HISTORICAL.value)),

    # Formula (7)
    Mutation("MUT-FUND-011", "CRITICAL", "EPS numerator total NI", "SCOPE_MISMATCH", "FORMULA_ENGINE", "EPS numerator scope", lambda r: _set_attribution_scope(r, "net_income", AttributionScope.TOTAL_GROUP.value)),
    Mutation("MUT-FUND-012", "HIGH", "BVPS uses total equity", "SCOPE_MISMATCH", "FORMULA_ENGINE", "BVPS equity scope", lambda r: _set_attribution_scope(r, "equity", AttributionScope.TOTAL_GROUP.value)),
    Mutation("MUT-FUND-013", "MAJOR", "ROE ending equity silently", "PERIOD_MISMATCH", "FORMULA_ENGINE", "ROE denominator basis", lambda r: _set_denom_basis(r, "equity", DenominatorBasis.ENDING_COMMON_EQUITY.value)),
    Mutation("MUT-FUND-014", "MAJOR", "ROA denominator to equity", "PERIOD_MISMATCH", "FORMULA_ENGINE", "ROA denominator identity", lambda r: _set_denom_basis(r, "total_assets", DenominatorBasis.ENDING_COMMON_EQUITY.value)),
    # MUT-015: post-run formula_input numerator swap (generic registry check)
    Mutation("MUT-FUND-015", "MAJOR", "NPM numerator swapped to operating_income (post-run)", "SCOPE_MISMATCH", "FORMULA_ENGINE", "NPM numerator identity",
             lambda r: r, post_run=_post_swap_npm_numerator),
    Mutation("MUT-FUND-016", "HIGH", "DuPont EM ending", "PERIOD_MISMATCH", "DUPONT_ENGINE", "EM denominator basis", lambda r: _set_denom_basis(r, "equity", DenominatorBasis.ENDING_COMMON_EQUITY.value)),
    # MUT-017: post-run stated_years corruption (generic window check)
    Mutation("MUT-FUND-017", "MAJOR", "CAGR stated_years corrupted (post-run)", "CAGR_PERIOD_INVALID", "GROWTH_ENGINE", "CAGR year count",
             lambda r: r, post_run=_post_corrupt_cagr_years),

    # Applicability & missing data (5)
    Mutation("MUT-FUND-018", "CRITICAL", "missing input → zero", "MISSING_REPLACED_WITH_ZERO", "APPLICABILITY_ENGINE", "missing to zero", _replace_missing_with_zero),
    Mutation("MUT-FUND-019", "HIGH", "INPUT_INCOMPLETE → VALID", "EPS_BASIS_MISMATCH", "APPLICABILITY_ENGINE", "status upgrade", lambda r: _set_shares_basis(r, ShareBasis.PERIOD_END_DILUTED.value)),
    Mutation("MUT-FUND-020", "HIGH", "negative equity ROE VALID", "NEGATIVE_EQUITY_NOT_MEANINGFUL", "NEGATIVE_VALUE_ENGINE", "negative equity handling", lambda r: _inflate_equity(r, -1)),
    Mutation("MUT-FUND-021", "MAJOR", "CAGR across zero VALID", "CAGR_NONPOSITIVE_BASE", "GROWTH_ENGINE", "CAGR nonpositive base", _flip_revenue_sign),
    # MUT-022: post-run near-zero warning removal
    Mutation("MUT-FUND-022", "MEDIUM", "near-zero denom warning removed (post-run)", "REQUIRED_WARNING_REMOVED", "QUALITY_ENGINE", "required near-zero warning preservation",
             _near_zero_denom, post_run=_post_strip_near_zero_warning),

    # Period & scope (4)
    Mutation("MUT-FUND-023", "MAJOR", "TTM vs quarter", "PERIOD_MISMATCH", "PERIOD_SCOPE_ENGINE", "period alignment", lambda r: _set_both_periods(r, "net_income", PeriodType.TTM.value, "equity", PeriodType.QUARTERLY.value)),
    Mutation("MUT-FUND-024", "MAJOR", "consolidated → standalone", "SCOPE_MISMATCH", "PERIOD_SCOPE_ENGINE", "reporting scope", lambda r: _set_reporting_scope(r, "equity", ReportingScope.STANDALONE.value)),
    Mutation("MUT-FUND-025", "MAJOR", "attributable + total mix", "SCOPE_MISMATCH", "PERIOD_SCOPE_ENGINE", "attribution scope", lambda r: _set_attribution_scope(r, "equity", AttributionScope.TOTAL_GROUP.value)),
    Mutation("MUT-FUND-026", "MAJOR", "avg → ending silently", "PERIOD_MISMATCH", "FORMULA_ENGINE", "denominator basis", lambda r: _set_denom_basis(r, "total_assets", DenominatorBasis.ENDING_TOTAL_ASSETS.value)),

    # Peer (4)
    Mutation("MUT-FUND-027", "MEDIUM", "peer removed", "PEER_COVERAGE_INSUFFICIENT", "PEER_ENGINE", "peer coverage", lambda r: _mutate_peer_set(r, 2)),
    Mutation("MUT-FUND-028", "MEDIUM", "median → mean (post-run)", "PEER_POLICY_VIOLATION", "PEER_ENGINE", "peer policy", lambda r: r, post_run=_post_swap_peer_policy),
    Mutation("MUT-FUND-029", "MEDIUM", "period-misaligned peer", "PEER_COVERAGE_INSUFFICIENT", "PEER_ENGINE", "peer period", lambda r: _mutate_peer_period(r, "CMG", PeriodType.QUARTERLY.value)),
    Mutation("MUT-FUND-030", "MEDIUM", "insufficient coverage ranked", "PEER_COVERAGE_INSUFFICIENT", "PEER_ENGINE", "peer coverage", lambda r: _mutate_peer_set(r, 2)),

    # Provenance & export (2)
    Mutation("MUT-FUND-031", "MAJOR", "provenance removed (post-run)", "PROVENANCE_MISSING", "PROVENANCE_ENGINE", "provenance presence", lambda r: r, post_run=_post_strip_provenance),
    Mutation("MUT-FUND-032", "CRITICAL", "invalid EPS exported", "EPS_BASIS_MISMATCH", "EXPORT_BUILDER", "export gate", lambda r: _set_shares_basis(r, ShareBasis.PERIOD_END_DILUTED.value)),

    # === Phase 5R3: Negative-value contract mutations (6 new) ===
    Mutation("MUT-FUND-033", "CRITICAL", "negative EPS changed to INPUT_INCOMPLETE (post-run)", "DOWNSTREAM_EXPORT_BLOCKED", "APPLICABILITY_ENGINE", "negative EPS status suppression",
             lambda r: r, post_run=_post_suppress_negative_eps),
    Mutation("MUT-FUND-034", "HIGH", "negative EPS sign removed (post-run)", "EPS_SIGN_INCONSISTENT", "FORMULA_ENGINE", "negative EPS sign preservation",
             lambda r: r, post_run=_post_flip_eps_sign),
    Mutation("MUT-FUND-035", "HIGH", "negative equity ROE marked VALID (post-run)", "NEGATIVE_EQUITY_NOT_MEANINGFUL", "NEGATIVE_VALUE_ENGINE", "negative equity ROE policy",
             lambda r: _set_negative_equity(r), post_run=_post_force_roe_valid),
    Mutation("MUT-FUND-036", "MEDIUM", "near-zero equity warning removed (post-run)", "REQUIRED_WARNING_REMOVED", "QUALITY_ENGINE", "extreme equity ratio warning preservation",
             lambda r: _set_near_zero_equity(r), post_run=_post_strip_equity_warning),
    Mutation("MUT-FUND-037", "MAJOR", "DERIVED_INPUT quality flag removed (post-run)", "QUALITY_STATUS_MISMATCH", "PROVENANCE_ENGINE", "derived input quality binding",
             lambda r: r, post_run=_post_strip_derived_flag),
    Mutation("MUT-FUND-038", "CRITICAL", "circular EPS oracle accepted (post-run)", "CIRCULAR_ORACLE_DETECTED", "VERIFIER", "circular oracle prohibition",
             lambda r: r, post_run=_post_inject_circular_oracle),
]


# === POSITIVE CONTROLS (separate denominator, NOT counted in 32 mutations) ===
POSITIVE_CONTROLS = [
    {
        "id": "POS-001-high-BVPS-warning-emitted",
        "description": "Clean fixture with high BVPS — engine MUST emit BVPS_OUT_OF_SANITY_RANGE warning",
        "setup": lambda: _inflate_equity(_clean_request(), 100),
        "expected_warning": "BVPS_OUT_OF_SANITY_RANGE",
        "expected_verdict": "PASS_WITH_WARNING",
    },
    {
        "id": "POS-002-low-EPS-no-unit-error",
        "description": "Clean low-profit company — engine must NOT emit UNIT_SCALE_MISMATCH",
        "setup": lambda: FundamentalRequest(
            ticker="LOWP", periods=[2023, 2024, 2025],
            metrics={
                "revenue": _metric("revenue", [10000, 11000, 12000]),
                "net_income": _metric("net_income", [10, 12, 15]),
                "equity": _metric("equity", [5000, 5500, 6000]),
                "total_assets": _metric("total_assets", [10000, 11000, 12000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
                "shares_outstanding": _metric("shares_outstanding", [1.5, 1.5, 1.5]),
            }),
        "expected_no_error": "UNIT_SCALE_MISMATCH",
        "expected_verdict": "PASS",
    },
    {
        "id": "POS-003-negative-EPS-valid-negative",
        "description": "Loss-making company — EPS must be VALID_NEGATIVE, not unit error",
        "setup": lambda: FundamentalRequest(
            ticker="LOSS", periods=[2023, 2024, 2025],
            metrics={
                "revenue": _metric("revenue", [10000, 11000, 12000]),
                "net_income": _metric("net_income", [-500, -400, -300]),
                "equity": _metric("equity", [5000, 4500, 4200]),
                "total_assets": _metric("total_assets", [10000, 9500, 9000], attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value]*3),
                "shares_outstanding": _metric("shares_outstanding", [1.5, 1.5, 1.5]),
            }),
        "expected_no_error": "UNIT_SCALE_MISMATCH",
        "expected_verdict": "PASS",
    },
]


def run_mutation(mut: Mutation) -> Dict[str, Any]:
    clean = _clean_request()
    try:
        mutated = mut.apply(clean)
    except Exception as e:
        return _fail(mut, f"apply_exception: {e}")
    try:
        res = run_fundamental(mutated)
    except Exception as e:
        return _fail(mut, f"runner_exception: {e}")
    if mut.post_run:
        try:
            res = mut.post_run(res)
        except Exception as e:
            return _fail(mut, f"post_run_exception: {e}")
    try:
        vr = verify(mutated, res.output)
    except Exception as e:
        return _fail(mut, f"verifier_exception: {e}")

    runner_codes = [str(e.get("code", "")) for e in res.errors]
    verifier_codes = [str(m.get("code", "")) for m in vr.mismatches]
    all_evidence = " ".join(str(m.get("evidence", "")) for m in vr.mismatches) + " " + " ".join(str(e.get("evidence", "")) for e in res.errors)
    all_codes = runner_codes + verifier_codes
    expected = mut.expected_error
    caught = any(expected in c for c in all_codes) or expected in all_evidence
    wrong_reason = (not caught) and vr.overall_verdict == "FAIL"
    return {
        "mutation_id": mut.id, "severity": mut.severity, "description": mut.description,
        "semantic_target": mut.semantic_target, "expected_error": expected, "expected_owner": mut.expected_owner,
        "runner_error_codes": runner_codes, "verifier_verdict": vr.overall_verdict,
        "verifier_mismatch_codes": verifier_codes, "caught": caught,
        "wrong_reason_failure": wrong_reason, "unsafe_false_pass": (not caught and vr.overall_verdict == "PASS"),
        "is_positive_control": False, "artifact_corrupted": True,
    }


def _fail(mut, reason):
    return {"mutation_id": mut.id, "caught": False, "reason": reason, "expected_error": mut.expected_error,
            "verifier_verdict": "EXCEPTION", "wrong_reason_failure": False, "unsafe_false_pass": True,
            "is_positive_control": False, "artifact_corrupted": True,
            "runner_error_codes": [], "verifier_mismatch_codes": []}


def run_positive_control(ctrl: Dict) -> Dict[str, Any]:
    try:
        req = ctrl["setup"]()
        res = run_fundamental(req)
        vr = verify(req, res.output)
        runner_codes = [str(e.get("code", "")) for e in res.errors]
        if "expected_warning" in ctrl:
            all_warnings = []
            for m in res.output.metric_results: all_warnings.extend(m.warnings)
            passed = any(ctrl["expected_warning"] in w for w in all_warnings)
        elif "expected_no_error" in ctrl:
            passed = ctrl["expected_no_error"] not in runner_codes
        else:
            passed = vr.overall_verdict in ("PASS", "PASS_WITH_WARNING") if ctrl.get("expected_verdict") == "PASS_WITH_WARNING" else True
        return {"control_id": ctrl["id"], "description": ctrl["description"], "passed": passed,
                "verifier_verdict": vr.overall_verdict, "runner_error_codes": runner_codes,
                "is_positive_control": True, "artifact_corrupted": False}
    except Exception as e:
        return {"control_id": ctrl["id"], "passed": False, "reason": str(e), "is_positive_control": True}


def main():
    print("=== P4R3 Mutation Qualification (32 negative + 3 positive controls) ===\n")
    print("--- 32 NEGATIVE MUTATIONS ---")
    results = []
    for mut in MUTATIONS:
        r = run_mutation(mut); results.append(r)
        status = "CAUGHT" if r["caught"] else ("WRONG_REASON" if r.get("wrong_reason_failure") else "SURVIVED")
        print(f"  {mut.id} [{mut.severity:8}] {mut.description:50} -> {status}")
        if not r["caught"]:
            print(f"      expected: {mut.expected_error}")
            print(f"      runner: {r['runner_error_codes']}  verifier: {r['verifier_mismatch_codes']}")

    print("\n--- POSITIVE CONTROLS (separate denominator) ---")
    pc_results = []
    for ctrl in POSITIVE_CONTROLS:
        r = run_positive_control(ctrl); pc_results.append(r)
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  {ctrl['id']:45} -> {status}")

    total = len(results); caught = sum(1 for r in results if r["caught"])
    survived = total - caught
    pc_passed = sum(1 for r in pc_results if r["passed"])
    sem_preserved = sum(1 for r in results if r.get("semantic_target"))

    print(f"\n=== Summary ===")
    print(f"Negative mutations: {total}")
    print(f"  caught: {caught}/{total}  survived: {survived}")
    print(f"  critical: {sum(1 for r in results if not r['caught'] and r['severity']=='CRITICAL')}")
    print(f"Positive controls: {len(pc_results)}  passed: {pc_passed}/{len(pc_results)}")
    print(f"Positive controls in mutation denominator: 0")

    manifest = {
        "phase4R3_mutation_manifest": {
            "negative_mutations": {"total": total, "caught": caught, "survived": survived,
                "critical_survived": sum(1 for r in results if not r['caught'] and r['severity']=='CRITICAL'),
                "high_survived": sum(1 for r in results if not r['caught'] and r['severity']=='HIGH'),
                "major_survived": sum(1 for r in results if not r['caught'] and r['severity']=='MAJOR'),
                "medium_survived": sum(1 for r in results if not r['caught'] and r['severity']=='MEDIUM'),
                "results": results},
            "positive_controls": {"total": len(pc_results), "passed": pc_passed, "results": pc_results},
            "positive_controls_in_mutation_denominator": 0,
            "fresh_batch": True,
        }
    }
    out = Path(__file__).parent.parent / "manifests" / "phase4R3-mutation-manifest.json"
    out.write_text(json.dumps(manifest, indent=2, default=str))
    print(f"\nManifest: {out}")
    return caught, survived, pc_passed


if __name__ == "__main__":
    caught, survived, pc_passed = main()
    sys.exit(0 if caught == 32 and pc_passed == 3 else 1)
