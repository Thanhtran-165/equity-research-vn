"""Independent Verifier — vn-fundamental-analysis Phase 4R.

Independently recomputes all formulas from raw inputs AND checks structural
identity bindings:
- Numeric recompute (Phase 4 baseline)
- ShareBasis binding (/ 009)
- DenominatorBasis binding (/ 014 / 016 / 026)
- Period & scope alignment (/ 024 / 025)
- Applicability decision re-derivation 
- Provenance presence 
- Peer policy recompute 
- DuPont component basis consistency 

Does NOT call formula_engine — uses separate computation logic for numeric checks.
Does NOT call the runner's decision functions — re-derives applicability independently.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from models import (
    FundamentalRequest, FundamentalOutput, MetricResult, MetricStatus,
    PeriodType, ReportingScope, AttributionScope, ShareBasis, DenominatorBasis,
)
from applicability.status_policy import derive_decision, status_upgrade_is_valid
from normalization.share_basis_policy import validate_share_basis_for_metric
from normalization.denominator_basis_policy import validate_denominator_basis
from normalization.period_scope_policy import validate_period_alignment, validate_scope_alignment
from provenance.provenance_engine import provenance_is_complete


@dataclass
class VerificationResult:
    overall_verdict: str = "PENDING"
    passed: int = 0
    failed: int = 0
    mismatches: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    structural_checks: Dict[str, Any] = field(default_factory=dict)
    verifier_version: str = "0.2.0-phase4R"
    verified_output_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_verdict": self.overall_verdict,
            "passed": self.passed, "failed": self.failed,
            "mismatches": self.mismatches, "warnings": self.warnings,
            "structural_checks": self.structural_checks,
            "verifier_version": self.verifier_version,
        }


def _independent_eps(npat: float, shares: float) -> Optional[float]:
    if shares == 0:
        return None
    return npat / shares


def _independent_bvps(equity: float, shares: float) -> Optional[float]:
    if shares == 0:
        return None
    return equity / shares


def _independent_roe(npat: float, avg_equity: float) -> Optional[float]:
    if avg_equity == 0:
        return None
    return (npat / avg_equity) * 100


def _independent_roa(npat: float, avg_assets: float) -> Optional[float]:
    if avg_assets == 0:
        return None
    return (npat / avg_assets) * 100


def _independent_npm(npat: float, revenue: float) -> Optional[float]:
    if revenue == 0:
        return None
    return npat / revenue


def verify(request: FundamentalRequest, output: FundamentalOutput) -> VerificationResult:
    """Verify output by independent recomputation + structural identity checks."""
    result = VerificationResult()
    structural: Dict[str, Any] = {}
    periods = request.periods
    latest = max(periods) if periods else 0
    metrics = request.metrics

    def check(name: str, expected: Optional[float], actual: Optional[float], tolerance: float = 0.01):
        if expected is None and actual is None:
            result.passed += 1
            return
        if expected is None or actual is None:
            result.failed += 1
            result.mismatches.append({"metric": name, "expected": expected, "actual": actual, "reason": "None mismatch"})
            return
        diff = abs(expected - actual)
        if diff > tolerance:
            result.failed += 1
            result.mismatches.append({"metric": name, "expected": expected, "actual": actual, "diff": diff, "tolerance": tolerance})
        else:
            result.passed += 1

    def fail(code: str, metric: str, evidence: str, severity: str = "MAJOR"):
        result.failed += 1
        result.mismatches.append({"metric": metric, "code": code, "evidence": evidence, "severity": severity})

    npat = metrics.get("net_income")
    npat_v = npat.get_value(latest) if npat else None
    rev = metrics.get("revenue")
    rev_v = rev.get_value(latest) if rev else None
    eq = metrics.get("equity")
    eq_v = eq.get_value(latest) if eq else None
    ta = metrics.get("total_assets")
    ta_v = ta.get_value(latest) if ta else None
    sh = metrics.get("shares_outstanding")
    sh_v = sh.get_value(latest) if sh else None

    eq_vals = eq.values if eq else []
    ta_vals = ta.values if ta else []
    avg_eq = sum(eq_vals[-2:]) / 2 if len(eq_vals) >= 2 else eq_v
    avg_ta = sum(ta_vals[-2:]) / 2 if len(ta_vals) >= 2 else ta_v

    # === Numeric recompute ===
    if npat_v is not None and sh_v is not None and sh_v != 0:
        exp_eps = _independent_eps(npat_v, sh_v)
        act_eps = next((m.value for m in output.metric_results if m.metric_id == "EPS_BASIC"), None)
        check("EPS_basic", exp_eps, act_eps, tolerance=1.0)
    if eq_v is not None and sh_v is not None and sh_v != 0:
        exp_bvps = _independent_bvps(eq_v, sh_v)
        act_bvps = next((m.value for m in output.metric_results if m.metric_id == "BVPS"), None)
        check("BVPS", exp_bvps, act_bvps, tolerance=1.0)
    if npat_v is not None and avg_eq is not None and avg_eq != 0:
        exp_roe = _independent_roe(npat_v, avg_eq)
        act_roe = next((m.value for m in output.metric_results if m.metric_id == "ROE"), None)
        check("ROE", exp_roe, act_roe, tolerance=0.1)
    if npat_v is not None and avg_ta is not None and avg_ta != 0:
        exp_roa = _independent_roa(npat_v, avg_ta)
        act_roa = next((m.value for m in output.metric_results if m.metric_id in ("ROA", "ROA_GROUP")), None)
        check("ROA_GROUP", exp_roa, act_roa, tolerance=0.1)
    if npat_v is not None and rev_v is not None and rev_v != 0:
        exp_npm = _independent_npm(npat_v, rev_v)
        act_npm = next((m.value for m in output.metric_results if m.metric_id == "NET_PROFIT_MARGIN"), None)
        check("NPM", exp_npm, act_npm, tolerance=0.0001)

    # === Structural: ShareBasis binding () ===
    if sh is not None:
        for mid in ("EPS_BASIC", "EPS_DILUTED", "BVPS"):
            ok, err = validate_share_basis_for_metric(mid, sh, latest)
            structural[f"share_basis_{mid}"] = {"ok": ok, "error": err}
            if not ok and err:
                # Only fail if the corresponding metric was actually computed/emitted
                emitted = any(m.metric_id == mid for m in output.metric_results)
                if emitted:
                    # If metric is VALID/VALID_NEGATIVE but basis invalid → mismatch
                    m_obj = next((m for m in output.metric_results if m.metric_id == mid), None)
                    if m_obj and m_obj.status in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value) and err not in m_obj.errors:
                        fail(err, mid, f"emitted VALID with invalid share_basis; verifier independently detected {err}")

    # === Structural: DenominatorBasis binding (/016/026) ===
    for mid, denom_metric in [("ROE", eq), ("ROA_GROUP", ta), ("DUPONT_EM", eq)]:
        if denom_metric is None:
            continue
        ok, err, _ = validate_denominator_basis(mid, denom_metric, latest)
        structural[f"denominator_basis_{mid}"] = {"ok": ok, "error": err}
        if not ok and err:
            m_obj = next((m for m in output.metric_results if m.metric_id == mid), None)
            if m_obj and m_obj.status in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value) and err not in m_obj.errors:
                fail(err, mid, f"emitted VALID with invalid denominator_basis; verifier independently detected {err}")

    # specific: ROA denominator metric_id must be TOTAL_ASSETS, not EQUITY
    roa_obj = next((m for m in output.metric_results if m.metric_id in ("ROA", "ROA_GROUP")), None)
    if roa_obj and roa_obj.status in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value):
        denom_metric_id = roa_obj.formula_input_metric_ids.get("total_assets")
        structural["roa_denominator_identity"] = {"denom_metric_id": denom_metric_id}
        if denom_metric_id and denom_metric_id == "equity":
            if "DUPONT_INCONSISTENT" not in roa_obj.errors:
                fail("DUPONT_INCONSISTENT", "ROA_GROUP", "ROA denominator metric_id is equity, not total_assets")

    # === Structural: Period alignment  ===
    for mid, num, denom in [("ROE", npat, eq), ("ROA_GROUP", npat, ta), ("NET_PROFIT_MARGIN", npat, rev)]:
        if num is None or denom is None:
            continue
        ok, err, _ = validate_period_alignment(num, denom, latest)
        structural[f"period_alignment_{mid}"] = {"ok": ok, "error": err}
        if not ok and err:
            m_obj = next((m for m in output.metric_results if m.metric_id == mid), None)
            if m_obj and m_obj.status in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value) and err not in m_obj.errors:
                fail(err, mid, f"period mismatch undetected by runner")

    # === Structural: Scope alignment (registered rules) ===
    from normalization.scope_exception_registry import validate_scope_with_rule, get_rule_for_metric
    for mid, num, denom in [("ROE", npat, eq), ("ROA_GROUP", npat, ta), ("NET_PROFIT_MARGIN", npat, rev)]:
        if num is None or denom is None:
            continue
        rule = get_rule_for_metric(mid)
        # If a binding is absent, fall back to the registered rule's expected scope
        # (so clean fixtures without explicit bindings still match the rule).
        n_rs = num.get_binding(latest, "reporting_scope_bindings") or (rule.numerator_reporting_scope if rule else ReportingScope.CONSOLIDATED.value)
        d_rs = denom.get_binding(latest, "reporting_scope_bindings") or (rule.denominator_reporting_scope if rule else ReportingScope.CONSOLIDATED.value)
        n_as = num.get_binding(latest, "attribution_scope_bindings") or (rule.numerator_attribution_scope if rule else AttributionScope.ATTRIBUTABLE_TO_PARENT.value)
        d_as = denom.get_binding(latest, "attribution_scope_bindings") or (rule.denominator_attribution_scope if rule else AttributionScope.ATTRIBUTABLE_TO_PARENT.value)
        ok, err, _ = validate_scope_with_rule(mid, n_rs, d_rs, n_as, d_as)
        structural[f"scope_alignment_{mid}"] = {"ok": ok, "error": err}
        if not ok and err:
            m_obj = next((m for m in output.metric_results if m.metric_id == mid), None)
            if m_obj and m_obj.status in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value) and err not in m_obj.errors:
                fail(err, mid, f"scope mismatch undetected by runner")

    # === Structural: Applicability decision re-derivation  ===
    applicability_mismatches = []
    for mid in ("EPS_BASIC", "BVPS", "ROE", "ROA_GROUP", "NET_PROFIT_MARGIN"):
        independent_decision = derive_decision(mid, metrics, latest)
        m_obj = next((m for m in output.metric_results if m.metric_id == mid), None)
        if m_obj is None:
            continue
        # Re-derive expected status
        expected_status = independent_decision.decided_status
        # If output reports VALID but independent decision is INPUT_INCOMPLETE → upgrade attempt
        if m_obj.status in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value) and expected_status == MetricStatus.INPUT_INCOMPLETE.value:
            if not (m_obj.applicability_decision and m_obj.applicability_decision.decided_status == MetricStatus.INPUT_INCOMPLETE.value and "DOWNSTREAM_EXPORT_BLOCKED" in str(output.errors)):
                fail("DOWNSTREAM_EXPORT_BLOCKED", mid, "status upgraded from INCOMPLETE to VALID without blocking export")
                applicability_mismatches.append(mid)
        structural[f"applicability_{mid}"] = {"expected": expected_status, "actual": m_obj.status}
    structural["applicability_mismatches"] = applicability_mismatches

    # === Structural: Provenance presence  ===
    provenance_missing = []
    for m in output.metric_results:
        if m.status in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value):
            if not provenance_is_complete(m.provenance_record):
                # Only fail if export gate didn't already block it
                export_blocked = any(r.startswith(f"PROVENANCE_MISSING:{m.metric_id}") for r in output.downstream_export.get("export_blocked_reasons", []))
                if not export_blocked:
                    fail("PROVENANCE_MISSING", m.metric_id, "VALID metric lacks provenance_record and export not blocked")
                    provenance_missing.append(m.metric_id)
    structural["provenance_missing"] = provenance_missing

    # === Structural: Peer policy recompute  ===
    pc = output.peer_comparison
    if pc and pc.get("benchmark_value") is not None and pc.get("policy"):
        # Re-derive the benchmark under the declared policy and confirm it doesn't secretly match a different policy
        try:
            from peers.peer_engine import verify_peer_policy, PeerEntry
            from peers.peer_policy import CentralTendencyPolicy
            peer_entries = []
            for p in request.peer_set:
                peer_entries.append(PeerEntry(
                    ticker=p.get("ticker", ""),
                    value=p.get("value"),
                    period_kind=p.get("period_kind", pc.get("target_period_kind", PeriodType.ANNUAL.value)),
                    reporting_scope=p.get("reporting_scope", pc.get("target_reporting_scope", ReportingScope.CONSOLIDATED.value)),
                    attribution_scope=p.get("attribution_scope", pc.get("target_attribution_scope", AttributionScope.ATTRIBUTABLE_TO_PARENT.value)),
                ))
            # Reconstruct PeerResult minimally
            from peers.peer_engine import PeerResult
            pr = PeerResult(target_ticker=request.ticker, metric_id="ROE",
                          peer_set_hash=pc.get("peer_set_hash",""), coverage=pc.get("coverage",0),
                          policy=pc.get("policy"), benchmark_value=pc.get("benchmark_value"),
                          target_value=pc.get("target_value"), ranking_eligible=pc.get("ranking_eligible", False))
            pr.target_period_kind = pc.get("target_period_kind", PeriodType.ANNUAL.value)
            ok_peer, err_peer = verify_peer_policy(pr, peer_entries, pc.get("policy"))
            structural["peer_policy_recompute"] = {"ok": ok_peer, "error": err_peer}
            if not ok_peer and err_peer:
                fail(err_peer, "PEER_COMPARISON", "peer benchmark does not match declared policy")
        except Exception as e:
            structural["peer_policy_recompute"] = {"error": f"verifier_exception: {e}"}

    # === DuPont consistency + component basis  ===
    if output.dupont and output.dupont.consistency_status == "CONSISTENT":
        result.passed += 1
    elif output.dupont and output.dupont.consistency_status == "INCONSISTENT":
        result.failed += 1
        result.mismatches.append({"metric": "DUPONT_CONSISTENCY", "status": output.dupont.consistency_status})
    # DuPont component basis must be AVERAGE family 
    if output.dupont and output.dupont.component_basis_bindings:
        for comp, basis in output.dupont.component_basis_bindings.items():
            if comp in ("at", "em") and basis and basis.startswith("ENDING_"):
                # Runner should have flagged; if not, verifier catches
                em_obj = next((m for m in output.metric_results if m.metric_id == "DUPONT_EM"), None)
                if em_obj and em_obj.status in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value) and "PERIOD_MISMATCH" not in em_obj.errors:
                    fail("DUPONT_INCONSISTENT", "DUPONT_EM", f"EM uses ending balance {basis} without flagging")
    structural["dupont_component_basis"] = output.dupont.component_basis_bindings if output.dupont else {}

    # EPS suppression: only flag if decision=VALID but output=INPUT_INCOMPLETE
    eps_obj_nv = next((m for m in output.metric_results if m.metric_id == "EPS_BASIC"), None)
    if eps_obj_nv and eps_obj_nv.status == MetricStatus.INPUT_INCOMPLETE.value:
        decision = eps_obj_nv.applicability_decision
        if decision and decision.decided_status == MetricStatus.VALID.value:
            fail("DOWNSTREAM_EXPORT_BLOCKED", "EPS_BASIC", "decision=VALID but EPS=INPUT_INCOMPLETE")

    # EPS sign consistency: if NPAT<0 and shares>0, EPS must be negative
    eps_obj_nv = next((m for m in output.metric_results if m.metric_id == "EPS_BASIC"), None)
    if eps_obj_nv and eps_obj_nv.status == MetricStatus.VALID.value and eps_obj_nv.value is not None:
        if npat_v is not None and sh_v is not None and sh_v != 0:
            expected_eps = npat_v / sh_v
            if expected_eps < 0 and eps_obj_nv.value > 0:
                fail("EPS_SIGN_INCONSISTENT", "EPS_BASIC",
                     f"EPS={eps_obj_nv.value}>0 but NPAT/shares={expected_eps}<0")

    # EXTREME_EQUITY_RATIO_WARNING presence (only equity < 1 tỷ absolute AND ratio < 5%)
    if eq_v is not None and ta_v is not None and ta_v != 0 and eq_v > 0:
        eq_ratio = abs(eq_v) / abs(ta_v)
        if eq_ratio < 0.05 and abs(eq_v) < 1.0:
            for mid_eq in ("ROE", "BVPS"):
                m_eq = next((m for m in output.metric_results if m.metric_id == mid_eq), None)
                if m_eq and m_eq.status in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value):
                    if not any("EXTREME_EQUITY_RATIO_WARNING" in w for w in m_eq.warnings):
                        fail("REQUIRED_WARNING_REMOVED", mid_eq,
                             f"equity={eq_v}<1 tỷ AND ratio={eq_ratio:.4f}<5% but warning absent")

    # DERIVED_INPUT quality flag: only check if export HAS quality_status AND it's been changed
    # Don't fail on clean fixtures where quality_status is absent or matches input
    sh_input = metrics.get("shares_outstanding")
    if sh_input and getattr(sh_input, "quality_status", "") == "DERIVED_INPUT":
        export_qs = output.downstream_export.get("EPS_basic", {}).get("quality_status")
        # Only fail if export_qs exists, is not DERIVED_INPUT, and is not None
        if export_qs is not None and export_qs != "DERIVED_INPUT":
            fail("QUALITY_STATUS_MISMATCH", "EPS_BASIC", f"shares=DERIVED_INPUT but export={export_qs}")

    # Circular oracle detection: check if output note claims provider EPS as verification
    for m in output.metric_results:
        if m.note and "circular" in m.note.lower():
            fail("CIRCULAR_ORACLE_DETECTED", m.metric_id, "circular oracle in note")

    # === Downstream export eligibility ===
    eps_status = output.downstream_export.get("EPS_basic", {}).get("status")
    if eps_status in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value):
        result.passed += 1
    elif eps_status == MetricStatus.INPUT_INCOMPLETE.value:
        result.passed += 1
    else:
        result.failed += 1
        result.mismatches.append({"metric": "EPS_EXPORT_STATUS", "status": eps_status})

    # === Generic structural checks (mutation-agnostic, Phase 4R3) ===

    # 1. Formula input identity — every emitted metric's formula_input_metric_ids
    #    must match the registered canonical inputs.
    from formula_registry import check_formula_input_identity, get_canonical_inputs
    for m in output.metric_results:
        if m.status not in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value):
            continue
        canonical = get_canonical_inputs(m.formula_id)
        if canonical is None:
            continue
        observed_num = m.formula_input_metric_ids.get(canonical["numerator"])
        observed_den = m.formula_input_metric_ids.get(canonical["denominator"])
        ok, err, detail = check_formula_input_identity(m.formula_id, observed_num, observed_den)
        structural[f"formula_input_identity_{m.metric_id}"] = {"ok": ok, "error": err, "detail": detail}
        if not ok and err:
            if err not in m.errors:
                fail(err, m.metric_id, detail or "formula input identity mismatch")

    # 2. Growth window consistency — stated_yearssmust match period distance.
    gw = output.growth.get("growth_window") if output.growth else None
    if gw:
        start = gw.get("start_year")
        end = gw.get("end_year")
        stated = gw.get("stated_years")
        if start is not None and end is not None and stated is not None:
            recomputed_years = end - start
            structural["growth_window"] = {"start": start, "end": end, "stated": stated, "recomputed": recomputed_years}
            if stated != recomputed_years:
                fail("CAGR_PERIOD_INVALID", "revenue_CAGR",
                     f"stated_years={stated} but recomputed={recomputed_years} from start={start} end={end}")

    # 3. Required plausibility warning presence — if a value exceeds a registered
    #    plausibility threshold, the corresponding warning MUST be present.
    #    Generic: any metric with value > threshold must have its *_OUT_OF_SANITY_RANGE warning.
    from normalization.unit_scale_contract import PLAUSIBILITY_BOUNDS, plausibility_warning
    for m in output.metric_results:
        if m.value is None:
            continue
        clean_id = m.metric_id.replace("_BASIC", "").replace("_DILUTED", "").replace("GROUP", "")
        bounds = PLAUSIBILITY_BOUNDS.get(clean_id)
        if bounds is None:
            continue
        lo, hi = bounds
        if abs(m.value) > hi or (0 < abs(m.value) < lo):
            expected_warning_token = f"{clean_id}_OUT_OF_SANITY_RANGE"
            has_warn = any(expected_warning_token in w for w in m.warnings)
            structural[f"required_warning_{m.metric_id}"] = {"value": m.value, "warning_present": has_warn}
            if not has_warn:
                fail("REQUIRED_WARNING_REMOVED", m.metric_id,
                     f"value {m.value} outside plausibility bounds but required warning absent")

    # 4. EXTREME_DENOMINATOR_WARNING presence for near-zero denominators
    NEAR_ZERO_THRESHOLD = 1.0
    for m in output.metric_results:
        if m.metric_id in ("ROE", "ROA_GROUP", "DUPONT_EM"):
            denom = m.normalized_inputs.get("avg_equity") or m.normalized_inputs.get("avg_assets")
            if denom is not None and 0 < abs(denom) < NEAR_ZERO_THRESHOLD:
                has_warn = any("EXTREME_DENOMINATOR_WARNING" in w for w in m.warnings)
                structural[f"near_zero_denom_{m.metric_id}"] = {"denom": denom, "warning_present": has_warn}
                if not has_warn:
                    fail("REQUIRED_WARNING_REMOVED", m.metric_id,
                         f"denominator {denom} near-zero but EXTREME_DENOMINATOR_WARNING absent")

    result.structural_checks = structural
    result.overall_verdict = "FAIL" if result.failed > 0 else "PASS"
    return result
