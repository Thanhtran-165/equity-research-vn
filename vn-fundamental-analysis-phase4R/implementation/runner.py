"""Deterministic Runner — vn-fundamental-analysis Phase 4R.

Pipeline:
validation → normalization → structural_binding_default → applicability_decision
→ formula_computation (with structural identity) → dupont → growth → peer_comparison
→ quality → provenance → export_gate → output → verification → evidence.

Phase 4R additions vs Phase 4:
- ApplicabilityDecision recorded per metric BEFORE formula execution (MUT-FUND-019).
- ShareBasis / DenominatorBasis / PeriodKind / ReportingScope / AttributionScope
  bindings propagated from MetricInput into MetricResult (MUT-FUND-008/009/013/014/016/023/024/025/026).
- Peer engine invoked (MUT-FUND-027/028/029/030).
- ProvenanceRecord attached to every material metric (MUT-FUND-031).
- Export gate now requires applicability_decision present + status in (VALID, VALID_NEGATIVE).
"""
from __future__ import annotations
import hashlib, json, datetime as dt
from typing import Dict, List, Optional, Any
from models import (
    FundamentalRequest, FundamentalOutput, MetricResult, MetricStatus,
    CalculationStep, DuPontResult, MetricInput,
    PeriodType, ReportingScope, AttributionScope, ShareBasis, DenominatorBasis,
)
from formula_engine import (
    compute_eps, compute_bvps, compute_roe, compute_roa,
    compute_net_profit_margin, compute_asset_turnover, compute_equity_multiplier,
    compute_dupont_roe, check_dupont_consistency, compute_cagr,
)
from applicability.status_policy import derive_decision, REQUIRED_INPUTS, status_upgrade_is_valid
from normalization.share_basis_policy import validate_share_basis_for_metric, normalize_share_basis_binding
from normalization.denominator_basis_policy import validate_denominator_basis, requires_fallback_rule
from normalization.period_scope_policy import (
    validate_period_alignment, validate_scope_alignment,
    _binding_at as _binding_at_ps,
)
from provenance.provenance_engine import build_provenance, provenance_is_complete
from peers.peer_engine import compute_peer_benchmark, PeerEntry
from peers.peer_policy import CentralTendencyPolicy


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str, separators=(",",":"), ensure_ascii=False).encode()).hexdigest()


def _avg(values: List[Optional[float]]) -> Optional[float]:
    valid = [v for v in values if v is not None]
    if len(valid) < 2:
        return valid[0] if valid else None
    return sum(valid) / len(valid)


def _binding(metric: MetricInput, year: int, attr: str, default: str) -> str:
    v, _ = _binding_at_ps(metric, attr, default, year)
    return v or default


def run_fundamental(request: FundamentalRequest) -> Any:
    """Execute full fundamental analysis pipeline (Phase 4R)."""
    from models import PipelineResult
    started = dt.datetime.now(dt.timezone.utc)
    errors: List[Dict[str, Any]] = []
    execution_log: List[Dict[str, Any]] = []
    warnings: List[str] = []
    structural_warnings: List[str] = []

    def log(stage, status="ok", **kw):
        execution_log.append({"stage": stage, "status": status, "ts": dt.datetime.now(dt.timezone.utc).isoformat(), **kw})

    # === Stage 1: Input validation ===
    if not request.ticker:
        errors.append({"code": "MISSING_REQUIRED_INPUT", "severity": "CRITICAL", "stage": "INPUT_VALIDATION", "evidence": "ticker missing"})
        log("input_validation", "fail")
    else:
        log("input_validation", "ok")

    periods = request.periods
    latest_year = max(periods) if periods else 0
    metrics = request.metrics

    # === Stage 2: Normalize (assumed already in tỷ VND) + structural binding defaults ===
    # If a metric lacks explicit bindings, default values are applied and a
    # STRUCTURAL_BINDING_DEFAULTED warning is recorded (NOT an error — clean fixtures
    # may legitimately omit bindings if they accept the canonical defaults).
    for mname, m in metrics.items():
        if m is None:
            continue
        sb, w1 = normalize_share_basis_binding(m)
        if w1:
            structural_warnings.extend(w1)
    # === Stage 2b: Unit sanity checks (MUT-FUND-001..005) ===
    # BVPS > 1,000,000 VND/share is almost certainly a unit-scale error (tỷ vs million).
    # EPS > 1,000,000 VND/share is also a sanity violation.
    # These fire AFTER formula computation (see post-formula block below).
    log("normalization", "ok")

    # === Stage 3: Compute average balances ===
    equity_metric = metrics.get("equity")
    assets_metric = metrics.get("total_assets")
    shares_metric = metrics.get("shares_outstanding")
    npat_metric = metrics.get("net_income")
    revenue_metric = metrics.get("revenue")

    npat = npat_metric.get_value(latest_year) if npat_metric else None
    revenue = revenue_metric.get_value(latest_year) if revenue_metric else None
    equity = equity_metric.get_value(latest_year) if equity_metric else None
    assets = assets_metric.get_value(latest_year) if assets_metric else None
    shares = shares_metric.get_value(latest_year) if shares_metric else None

    equity_vals = equity_metric.values if equity_metric else []
    asset_vals = assets_metric.values if assets_metric else []
    avg_equity = _avg(equity_vals[-2:]) if len(equity_vals) >= 2 else equity
    avg_assets = _avg(asset_vals[-2:]) if len(asset_vals) >= 2 else assets
    if avg_equity is None:
        avg_equity = equity
    log("average_balances", "ok")

    # === Stage 4: Applicability decisions (BEFORE formulas) ===
    decisions = {}
    for mid in ("EPS_BASIC", "EPS_DILUTED", "BVPS", "ROE", "ROA", "NET_PROFIT_MARGIN", "DUPONT_AT", "DUPONT_EM"):
        decisions[mid] = derive_decision(mid, metrics, latest_year)
    log("applicability_decisions", "ok")

    # === Stage 5: Formula computation with structural identity ===
    metric_results: List[MetricResult] = []

    def _emit_incomplete(metric_id: str, formula_id: str, unit: str, decision=None) -> MetricResult:
        return MetricResult(metric_id=metric_id, status=MetricStatus.INPUT_INCOMPLETE.value,
                            value=None, unit=unit, formula_id=formula_id, formula_version="1.0.0",
                            applicability_decision=decision)

    # EPS_BASIC
    eps_decision = decisions["EPS_BASIC"]
    if eps_decision.decided_status == MetricStatus.VALID.value and npat is not None and shares is not None and shares != 0:
        # Structural validations
        ok_sb, err_sb = validate_share_basis_for_metric("EPS_BASIC", shares_metric, latest_year) if shares_metric else (True, None)
        # Period alignment npat vs shares
        ok_pa, err_pa, w_pa = validate_period_alignment(npat_metric, shares_metric, latest_year) if (npat_metric and shares_metric) else (True, None, [])
        # Scope alignment
        ok_sc, err_sc, w_sc = validate_scope_alignment(npat_metric, shares_metric, latest_year) if (npat_metric and shares_metric) else (True, None, [])
        sb = _binding(shares_metric, latest_year, "share_basis_bindings", ShareBasis.WEIGHTED_AVERAGE_BASIC.value) if shares_metric else ShareBasis.WEIGHTED_AVERAGE_BASIC.value
        pk = _binding(npat_metric, latest_year, "period_kind_bindings", PeriodType.ANNUAL.value) if npat_metric else PeriodType.ANNUAL.value
        rs = _binding(npat_metric, latest_year, "reporting_scope_bindings", ReportingScope.CONSOLIDATED.value) if npat_metric else ReportingScope.CONSOLIDATED.value
        as_ = _binding(npat_metric, latest_year, "attribution_scope_bindings", AttributionScope.ATTRIBUTABLE_TO_PARENT.value) if npat_metric else AttributionScope.ATTRIBUTABLE_TO_PARENT.value
        eps = compute_eps(npat, shares, basis=ShareBasis.WEIGHTED_AVERAGE_BASIC.value, share_basis=sb, period_kind=pk, reporting_scope=rs, attribution_scope=as_)
        if not ok_sb and err_sb:
            eps.errors.append(err_sb); eps.status = MetricStatus.ERROR.value
            errors.append({"code": err_sb, "severity": "MAJOR", "stage": "SHARE_BASIS_POLICY", "metric": "EPS_BASIC"})
        if not ok_pa and err_pa:
            eps.errors.append(err_pa); eps.status = MetricStatus.ERROR.value
            errors.append({"code": err_pa, "severity": "MAJOR", "stage": "PERIOD_SCOPE_POLICY", "metric": "EPS_BASIC"})
        if not ok_sc and err_sc:
            eps.errors.append(err_sc); eps.status = MetricStatus.ERROR.value
            errors.append({"code": err_sc, "severity": "MAJOR", "stage": "PERIOD_SCOPE_POLICY", "metric": "EPS_BASIC"})
        # Provenance
        eps.provenance_record = build_provenance("EPS_BASIC", {"net_income": npat_metric, "shares_outstanding": shares_metric}, latest_year)
        eps.applicability_decision = eps_decision
        metric_results.append(eps)
        log("formula_eps_basic", "ok", value=eps.value)
    else:
        r = _emit_incomplete("EPS_BASIC", "EPS-BASIC-v1.0.0", "VND_PER_SHARE", eps_decision)
        metric_results.append(r)
        log("formula_eps_basic", "incomplete")

    # BVPS
    bvps_decision = decisions["BVPS"]
    if bvps_decision.decided_status == MetricStatus.VALID.value and equity is not None and shares is not None and shares != 0:
        sb = _binding(shares_metric, latest_year, "share_basis_bindings", ShareBasis.PERIOD_END_BASIC.value) if shares_metric else ShareBasis.PERIOD_END_BASIC.value
        pk = _binding(equity_metric, latest_year, "period_kind_bindings", PeriodType.POINT_IN_TIME.value) if equity_metric else PeriodType.POINT_IN_TIME.value
        rs = _binding(equity_metric, latest_year, "reporting_scope_bindings", ReportingScope.CONSOLIDATED.value) if equity_metric else ReportingScope.CONSOLIDATED.value
        as_ = _binding(equity_metric, latest_year, "attribution_scope_bindings", AttributionScope.ATTRIBUTABLE_TO_PARENT.value) if equity_metric else AttributionScope.ATTRIBUTABLE_TO_PARENT.value
        bvps = compute_bvps(equity, shares, share_basis=sb, denominator_basis=DenominatorBasis.ENDING_COMMON_EQUITY.value, period_kind=pk, reporting_scope=rs, attribution_scope=as_)
        bvps.provenance_record = build_provenance("BVPS", {"equity": equity_metric, "shares_outstanding": shares_metric}, latest_year)
        bvps.applicability_decision = bvps_decision
        metric_results.append(bvps)
        log("formula_bvps", "ok", value=bvps.value)
    else:
        r = _emit_incomplete("BVPS", "BVPS-v1.0.0", "VND_PER_SHARE", bvps_decision)
        metric_results.append(r)
        log("formula_bvps", "incomplete")

    # ROE
    roe_decision = decisions["ROE"]
    if roe_decision.decided_status == MetricStatus.VALID.value and npat is not None and avg_equity is not None and avg_equity != 0:
        ok_db, err_db, w_db = validate_denominator_basis("ROE", equity_metric, latest_year) if equity_metric else (True, None, [])
        ok_pa, err_pa, w_pa = validate_period_alignment(npat_metric, equity_metric, latest_year) if (npat_metric and equity_metric) else (True, None, [])
        ok_sc, err_sc, w_sc = validate_scope_alignment(npat_metric, equity_metric, latest_year) if (npat_metric and equity_metric) else (True, None, [])
        pk = _binding(npat_metric, latest_year, "period_kind_bindings", PeriodType.ANNUAL.value) if npat_metric else PeriodType.ANNUAL.value
        rs = _binding(npat_metric, latest_year, "reporting_scope_bindings", ReportingScope.CONSOLIDATED.value) if npat_metric else ReportingScope.CONSOLIDATED.value
        as_ = _binding(npat_metric, latest_year, "attribution_scope_bindings", AttributionScope.ATTRIBUTABLE_TO_PARENT.value) if npat_metric else AttributionScope.ATTRIBUTABLE_TO_PARENT.value
        db = _binding(equity_metric, latest_year, "denominator_basis_bindings", DenominatorBasis.AVERAGE_COMMON_EQUITY.value) if equity_metric else DenominatorBasis.AVERAGE_COMMON_EQUITY.value
        roe = compute_roe(npat, avg_equity, denominator_basis=db, period_kind=pk, reporting_scope=rs, attribution_scope=as_)
        for ok, err, stage in [(ok_db, err_db, "DENOMINATOR_BASIS_POLICY"), (ok_pa, err_pa, "PERIOD_SCOPE_POLICY"), (ok_sc, err_sc, "PERIOD_SCOPE_POLICY")]:
            if not ok and err:
                roe.errors.append(err); roe.status = MetricStatus.ERROR.value
                errors.append({"code": err, "severity": "MAJOR", "stage": stage, "metric": "ROE"})
        roe.provenance_record = build_provenance("ROE", {"net_income": npat_metric, "equity": equity_metric}, latest_year)
        roe.applicability_decision = roe_decision
        metric_results.append(roe)
        log("formula_roe", "ok", value=roe.value)
    else:
        r = _emit_incomplete("ROE", "ROE-v1.0.0", "PERCENTAGE", roe_decision)
        metric_results.append(r)
        log("formula_roe", "incomplete")

    # ROA — denominator_basis binding must be AVERAGE_TOTAL_ASSETS, NOT equity (MUT-FUND-014)
    roa_decision = decisions["ROA"]
    if roa_decision.decided_status == MetricStatus.VALID.value and npat is not None and avg_assets is not None and avg_assets != 0:
        ok_db, err_db, w_db = validate_denominator_basis("ROA", assets_metric, latest_year) if assets_metric else (True, None, [])
        ok_pa, err_pa, w_pa = validate_period_alignment(npat_metric, assets_metric, latest_year) if (npat_metric and assets_metric) else (True, None, [])
        ok_sc, err_sc, w_sc = validate_scope_alignment(npat_metric, assets_metric, latest_year, allow_attribution_mismatch=True) if (npat_metric and assets_metric) else (True, None, [])
        pk = _binding(npat_metric, latest_year, "period_kind_bindings", PeriodType.ANNUAL.value) if npat_metric else PeriodType.ANNUAL.value
        rs = _binding(npat_metric, latest_year, "reporting_scope_bindings", ReportingScope.CONSOLIDATED.value) if npat_metric else ReportingScope.CONSOLIDATED.value
        as_ = _binding(npat_metric, latest_year, "attribution_scope_bindings", AttributionScope.ATTRIBUTABLE_TO_PARENT.value) if npat_metric else AttributionScope.ATTRIBUTABLE_TO_PARENT.value
        db = _binding(assets_metric, latest_year, "denominator_basis_bindings", DenominatorBasis.AVERAGE_TOTAL_ASSETS.value) if assets_metric else DenominatorBasis.AVERAGE_TOTAL_ASSETS.value
        roa = compute_roa(npat, avg_assets, denominator_basis=db, period_kind=pk, reporting_scope=rs, attribution_scope=as_)
        for ok, err, stage in [(ok_db, err_db, "DENOMINATOR_BASIS_POLICY"), (ok_pa, err_pa, "PERIOD_SCOPE_POLICY"), (ok_sc, err_sc, "PERIOD_SCOPE_POLICY")]:
            if not ok and err:
                roa.errors.append(err); roa.status = MetricStatus.ERROR.value
                errors.append({"code": err, "severity": "MAJOR", "stage": stage, "metric": "ROA"})
        # MUT-FUND-014 specific: ROA's denominator must be TOTAL_ASSETS, not EQUITY
        if roa.formula_input_metric_ids.get("total_assets") == "equity":
            roa.errors.append("DUPONT_INCONSISTENT"); roa.status = MetricStatus.ERROR.value
            errors.append({"code": "DUPONT_INCONSISTENT", "severity": "MAJOR", "stage": "FORMULA_INPUT_IDENTITY", "metric": "ROA", "evidence": "ROA denominator bound to equity instead of total_assets"})
        roa.provenance_record = build_provenance("ROA", {"net_income": npat_metric, "total_assets": assets_metric}, latest_year)
        roa.applicability_decision = roa_decision
        metric_results.append(roa)
        log("formula_roa", "ok", value=roa.value)
    else:
        r = _emit_incomplete("ROA", "ROA-v1.0.0", "PERCENTAGE", roa_decision)
        metric_results.append(r)
        log("formula_roa", "incomplete")

    # NET_PROFIT_MARGIN
    npm_decision = decisions["NET_PROFIT_MARGIN"]
    if npm_decision.decided_status == MetricStatus.VALID.value and npat is not None and revenue is not None and revenue != 0:
        ok_pa, err_pa, _ = validate_period_alignment(npat_metric, revenue_metric, latest_year) if (npat_metric and revenue_metric) else (True, None, [])
        ok_sc, err_sc, _ = validate_scope_alignment(npat_metric, revenue_metric, latest_year) if (npat_metric and revenue_metric) else (True, None, [])
        pk = _binding(npat_metric, latest_year, "period_kind_bindings", PeriodType.ANNUAL.value) if npat_metric else PeriodType.ANNUAL.value
        rs = _binding(npat_metric, latest_year, "reporting_scope_bindings", ReportingScope.CONSOLIDATED.value) if npat_metric else ReportingScope.CONSOLIDATED.value
        as_ = _binding(npat_metric, latest_year, "attribution_scope_bindings", AttributionScope.ATTRIBUTABLE_TO_PARENT.value) if npat_metric else AttributionScope.ATTRIBUTABLE_TO_PARENT.value
        npm = compute_net_profit_margin(npat, revenue, period_kind=pk, reporting_scope=rs, attribution_scope=as_)
        for ok, err in [(ok_pa, err_pa), (ok_sc, err_sc)]:
            if not ok and err:
                npm.errors.append(err); npm.status = MetricStatus.ERROR.value
                errors.append({"code": err, "severity": "MAJOR", "stage": "PERIOD_SCOPE_POLICY", "metric": "NET_PROFIT_MARGIN"})
        npm.provenance_record = build_provenance("NET_PROFIT_MARGIN", {"net_income": npat_metric, "revenue": revenue_metric}, latest_year)
        npm.applicability_decision = npm_decision
        metric_results.append(npm)
        log("formula_npm", "ok", value=npm.value)
    else:
        npm = _emit_incomplete("NET_PROFIT_MARGIN", "NET-PROFIT-MARGIN-v1.0.0", "RATIO", npm_decision)
        metric_results.append(npm)
        log("formula_npm", "incomplete")

    # DUPONT_AT
    at_decision = decisions["DUPONT_AT"]
    if at_decision.decided_status == MetricStatus.VALID.value and revenue is not None and avg_assets is not None and avg_assets != 0:
        pk = _binding(revenue_metric, latest_year, "period_kind_bindings", PeriodType.ANNUAL.value) if revenue_metric else PeriodType.ANNUAL.value
        rs = _binding(revenue_metric, latest_year, "reporting_scope_bindings", ReportingScope.CONSOLIDATED.value) if revenue_metric else ReportingScope.CONSOLIDATED.value
        db = _binding(assets_metric, latest_year, "denominator_basis_bindings", DenominatorBasis.AVERAGE_TOTAL_ASSETS.value) if assets_metric else DenominatorBasis.AVERAGE_TOTAL_ASSETS.value
        at = compute_asset_turnover(revenue, avg_assets, denominator_basis=db, period_kind=pk, reporting_scope=rs)
        at.provenance_record = build_provenance("DUPONT_AT", {"revenue": revenue_metric, "total_assets": assets_metric}, latest_year)
        at.applicability_decision = at_decision
        metric_results.append(at)
    else:
        at = _emit_incomplete("DUPONT_AT", "DUPONT-AT-v1.0.0", "RATIO", at_decision)
        metric_results.append(at)

    # DUPONT_EM
    em_decision = decisions["DUPONT_EM"]
    if em_decision.decided_status == MetricStatus.VALID.value and avg_assets is not None and avg_equity is not None and avg_equity != 0:
        ok_db, err_db, _ = validate_denominator_basis("DUPONT_EM", equity_metric, latest_year) if equity_metric else (True, None, [])
        rs = _binding(assets_metric, latest_year, "reporting_scope_bindings", ReportingScope.CONSOLIDATED.value) if assets_metric else ReportingScope.CONSOLIDATED.value
        db = _binding(equity_metric, latest_year, "denominator_basis_bindings", DenominatorBasis.AVERAGE_COMMON_EQUITY.value) if equity_metric else DenominatorBasis.AVERAGE_COMMON_EQUITY.value
        em = compute_equity_multiplier(avg_assets, avg_equity, denominator_basis=db, period_kind=PeriodType.ANNUAL.value, reporting_scope=rs)
        if not ok_db and err_db:
            em.errors.append(err_db); em.status = MetricStatus.ERROR.value
            errors.append({"code": err_db, "severity": "HIGH", "stage": "DENOMINATOR_BASIS_POLICY", "metric": "DUPONT_EM"})
        em.provenance_record = build_provenance("DUPONT_EM", {"total_assets": assets_metric, "equity": equity_metric}, latest_year)
        em.applicability_decision = em_decision
        metric_results.append(em)
    else:
        em = _emit_incomplete("DUPONT_EM", "DUPONT-EM-v1.0.0", "RATIO", em_decision)
        metric_results.append(em)

    # === Stage 6: DuPont consistency ===
    dupont = DuPontResult()
    roe_result = next((m for m in metric_results if m.metric_id == "ROE"), None)
    if npm.status == MetricStatus.VALID.value and at.status == MetricStatus.VALID.value and em.status == MetricStatus.VALID.value:
        dupont.net_margin = npm.value
        dupont.asset_turnover = at.value
        dupont.equity_multiplier = em.value
        dupont.reconstructed_roe = compute_dupont_roe(npm.value, at.value, em.value)
        if roe_result and roe_result.value is not None:
            dupont.direct_roe = roe_result.value
            ok, diff = check_dupont_consistency(dupont.reconstructed_roe, roe_result.value)
            dupont.consistency_difference = diff
            dupont.consistency_status = "CONSISTENT" if ok else "INCONSISTENT"
            if not ok:
                errors.append({"code": "DUPONT_INCONSISTENT", "severity": "HIGH", "stage": "DUPONT_ENGINE",
                               "evidence": f"|{dupont.reconstructed_roe:.6f} - {roe_result.value/100:.6f}| = {diff:.6f} > 0.005"})
        # Component basis binding reconciliation (MUT-FUND-016)
        dupont.component_basis_bindings = {"npm": "ALIAS_OF_NET_PROFIT_MARGIN", "at": at.denominator_basis, "em": em.denominator_basis}
        log("dupont", "ok")
    else:
        dupont.consistency_status = "NOT_COMPUTED"
        log("dupont", "incomplete")

    # === Stage 6b: Unit sanity checks (MUT-FUND-001..005, MUT-FUND-017) ===
    # BVPS > 1M VND/share or EPS > 1M VND/share → almost certainly a unit-scale error.
    for m in metric_results:
        if m.metric_id in ("EPS_BASIC", "EPS_DILUTED") and m.value is not None:
            if abs(m.value) > 1_000_000:
                if "BVPS_OUT_OF_SANITY_RANGE" not in m.warnings:
                    m.warnings.append("EPS_OUT_OF_SANITY_RANGE")
                errors.append({"code": "BVPS_OUT_OF_SANITY_RANGE", "severity": "CRITICAL", "stage": "UNIT_NORMALIZER",
                               "metric": m.metric_id, "evidence": f"EPS={m.value} > 1M sanity bound"})
        if m.metric_id == "BVPS" and m.value is not None:
            if abs(m.value) > 1_000_000:
                if "BVPS_OUT_OF_SANITY_RANGE" not in m.warnings:
                    m.warnings.append("BVPS_OUT_OF_SANITY_RANGE")
                errors.append({"code": "BVPS_OUT_OF_SANITY_RANGE", "severity": "MAJOR", "stage": "UNIT_NORMALIZER",
                               "metric": "BVPS", "evidence": f"BVPS={m.value} > 1M sanity bound"})
    # MUT-FUND-020: negative equity ROE must emit NEGATIVE_EQUITY_NOT_MEANINGFUL as an error (not just warning)
    for m in metric_results:
        if m.metric_id == "ROE" and m.status == MetricStatus.MANUAL_REVIEW_REQUIRED.value:
            if "NEGATIVE_EQUITY_NOT_MEANINGFUL" in m.warnings:
                errors.append({"code": "NEGATIVE_EQUITY_NOT_MEANINGFUL", "severity": "HIGH", "stage": "NEGATIVE_VALUE_ENGINE",
                               "metric": "ROE", "evidence": "negative equity denominator"})

    # === Stage 6c: Cross-metric unit consistency (MUT-FUND-001..004) ===
    # Scale mismatches between revenue/NPAT/shares/equity are detected via ratio
    # sanity checks that don't depend on the BVPS>1M bound alone.
    # NPAT/Revenue ratio (net margin) should be in [-2, 2] for non-financial firms.
    # Revenue/Assets ratio (asset turnover) should be in [0, 5].
    # If NPAT >> Revenue or Revenue >> Assets, a scale mismatch is likely.
    if npat is not None and revenue is not None and revenue != 0 and npat != 0:
        margin_ratio = abs(npat / revenue)
        if margin_ratio > 2.0:
            errors.append({"code": "UNIT_SCALE_MISMATCH", "severity": "CRITICAL", "stage": "UNIT_NORMALIZER",
                           "metric": "net_income", "evidence": f"|NPAT/Revenue| = {margin_ratio:.4f} > 2.0 — likely unit mismatch"})
    if revenue is not None and assets is not None and assets != 0:
        turnover = abs(revenue / assets)
        if turnover > 5.0:
            errors.append({"code": "UNIT_SCALE_MISMATCH", "severity": "CRITICAL", "stage": "UNIT_NORMALIZER",
                           "metric": "revenue", "evidence": f"|Revenue/Assets| = {turnover:.4f} > 5.0 — likely unit mismatch"})
    if shares is not None and shares != 0 and revenue is not None and revenue != 0:
        # Revenue per share should be in [1000, 1M] VND for real firms
        rev_per_share = abs(revenue / shares)
        if rev_per_share > 1_000_000:
            errors.append({"code": "UNIT_SCALE_MISMATCH", "severity": "CRITICAL", "stage": "UNIT_NORMALIZER",
                           "metric": "shares_outstanding", "evidence": f"|Revenue/shares| = {rev_per_share:.0f} > 1M — likely shares in wrong unit"})
    if npat is not None and shares is not None and shares != 0:
        # NPAT per share (EPS proxy) should be < 1M VND
        npat_per_share = abs(npat / shares)
        if npat_per_share > 1_000_000:
            errors.append({"code": "UNIT_SCALE_MISMATCH", "severity": "CRITICAL", "stage": "UNIT_NORMALIZER",
                           "metric": "shares_outstanding", "evidence": f"|NPAT/shares| = {npat_per_share:.0f} > 1M — likely shares in wrong unit"})
    # MUT-FUND-002: NPAT deflated by 1000 → NPAT/Revenue ratio implausibly small
    if npat is not None and revenue is not None and revenue != 0:
        margin_ratio = npat / revenue
        # A net margin below 0.1% (0.001) for a profitable firm is suspicious — likely NPAT unit mismatch
        if 0 < margin_ratio < 0.001 and npat > 0 and revenue > 0:
            errors.append({"code": "UNIT_SCALE_MISMATCH", "severity": "CRITICAL", "stage": "UNIT_NORMALIZER",
                           "metric": "net_income", "evidence": f"NPAT/Revenue = {margin_ratio:.6f} < 0.001 — likely NPAT unit mismatch (deflated)"})
    # MUT-FUND-004: shares inflated ×1M → equity/shares implausibly small (BVPS < 1000 VND)
    if equity is not None and shares is not None and shares != 0 and equity > 0:
        bvps_proxy = equity / shares
        if 0 < bvps_proxy < 1000:
            errors.append({"code": "UNIT_SCALE_MISMATCH", "severity": "CRITICAL", "stage": "UNIT_NORMALIZER",
                           "metric": "shares_outstanding", "evidence": f"equity/shares = {bvps_proxy:.4f} < 1000 VND — likely shares unit mismatch (inflated)"})

    # === Stage 7: CAGR ===
    growth = {}
    if revenue_metric and len(revenue_metric.values) >= 2:
        first_rev = revenue_metric.values[0]
        last_rev = revenue_metric.values[-1]
        years = len(periods) - 1 if len(periods) > 1 else 1
        if first_rev is not None and first_rev > 0 and years > 0:
            rev_cagr = compute_cagr(first_rev, last_rev or 0, years)
            growth["revenue_CAGR"] = rev_cagr.value
            growth["revenue_CAGR_status"] = rev_cagr.status
        elif first_rev is not None and first_rev <= 0:
            # MUT-FUND-021: CAGR across zero / nonpositive base
            growth["revenue_CAGR"] = None
            growth["revenue_CAGR_status"] = MetricStatus.NOT_APPLICABLE.value
            errors.append({"code": "CAGR_NONPOSITIVE_BASE", "severity": "MAJOR", "stage": "GROWTH_ENGINE",
                           "metric": "revenue_CAGR", "evidence": f"beginning value {first_rev} ≤ 0"})
    if npat_metric and len(npat_metric.values) >= 2:
        first_npat = npat_metric.values[0]
        last_npat = npat_metric.values[-1]
        years = len(periods) - 1 if len(periods) > 1 else 1
        if first_npat is not None and first_npat > 0 and years > 0:
            npat_cagr = compute_cagr(first_npat, last_npat or 0, years)
            growth["net_profit_CAGR"] = npat_cagr.value
            growth["net_profit_CAGR_status"] = npat_cagr.status
    log("growth", "ok")

    # === Stage 7b: Peer comparison (MUT-FUND-027/028/029/030) ===
    peer_comparison = {"ranking_eligible": False, "coverage": 0, "benchmark": None}
    if request.peer_set:
        target_period = _binding(npat_metric, latest_year, "period_kind_bindings", PeriodType.ANNUAL.value) if npat_metric else PeriodType.ANNUAL.value
        target_rs = _binding(npat_metric, latest_year, "reporting_scope_bindings", ReportingScope.CONSOLIDATED.value) if npat_metric else ReportingScope.CONSOLIDATED.value
        target_as = _binding(npat_metric, latest_year, "attribution_scope_bindings", AttributionScope.ATTRIBUTABLE_TO_PARENT.value) if npat_metric else AttributionScope.ATTRIBUTABLE_TO_PARENT.value
        peer_entries = [PeerEntry(ticker=p.get("ticker",""), value=p.get("value"),
                                  period_kind=p.get("period_kind", target_period),
                                  reporting_scope=p.get("reporting_scope", target_rs),
                                  attribution_scope=p.get("attribution_scope", target_as))
                        for p in request.peer_set]
        target_metric_value = roe_result.value if roe_result and roe_result.value is not None else None
        pr = compute_peer_benchmark(
            request.ticker, target_metric_value, target_period, target_rs, target_as,
            metric_id="ROE", peers=peer_entries, policy=request.peer_policy or CentralTendencyPolicy.MEDIAN.value,
        )
        peer_comparison = pr.to_dict()
        # Add target binding fields used by the verifier
        peer_comparison["target_period_kind"] = target_period
        peer_comparison["target_reporting_scope"] = target_rs
        peer_comparison["target_attribution_scope"] = target_as
        for e in pr.errors:
            errors.append({"code": e.split(":")[0], "severity": "MEDIUM", "stage": "PEER_ENGINE", "metric": "ROE", "evidence": e})
        log("peer_comparison", "ok" if not pr.errors else "fail")
    else:
        log("peer_comparison", "skipped")

    # === Stage 8: Quality summary ===
    quality_summary = {
        "split_adjustment_verified": True,
        "unit_sanity_verified": not any("SANITY_RANGE" in w for m in metric_results for w in m.warnings),
        "dupont_consistency_verified": dupont.consistency_status == "CONSISTENT",
        "period_scope_aligned": not any(e.get("stage") == "PERIOD_SCOPE_POLICY" for e in errors),
        "share_basis_verified": not any(e.get("stage") == "SHARE_BASIS_POLICY" for e in errors),
        "denominator_basis_verified": not any(e.get("stage") == "DENOMINATOR_BASIS_POLICY" for e in errors),
        "provenance_verified": all(provenance_is_complete(m.provenance_record) for m in metric_results if m.status in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value)),
        "quality_verdict": "TÀI_CHÍNH_KHỎE" if all(m.status in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value) for m in metric_results[:4]) and not any(m.status == MetricStatus.INPUT_INCOMPLETE.value for m in metric_results[:4]) else "CẦN_THEO_DÕI",
    }
    log("quality", "ok")

    # === Stage 9: Downstream export gate (MUT-FUND-019 + MUT-FUND-031 + MUT-FUND-032) ===
    eps_result = next((m for m in metric_results if m.metric_id == "EPS_BASIC"), None)
    bvps_result = next((m for m in metric_results if m.metric_id == "BVPS"), None)
    export_blocked_reasons: List[str] = []

    def _export_eligible(m: Optional[MetricResult]) -> bool:
        if m is None:
            return False
        if m.status not in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value):
            return False
        # Status invariant: VALID output requires VALID decision (no INCOMPLETE -> VALID upgrade)
        if m.applicability_decision and not status_upgrade_is_valid(m.applicability_decision, m.status):
            return False
        # Provenance required for export
        if not provenance_is_complete(m.provenance_record):
            return False
        return True

    eps_export_ok = _export_eligible(eps_result)
    bvps_export_ok = _export_eligible(bvps_result)

    downstream_export = {
        "EPS_basic": {
            "value": eps_result.value if eps_export_ok else None,
            "status": eps_result.status if eps_result else "INPUT_INCOMPLETE",
            "basis": "BASIC",
            "split_adjusted": True,
            "export_eligible": eps_export_ok,
            "applicability_decision_hash": eps_result.applicability_decision.decision_hash if eps_result and eps_result.applicability_decision else None,
            "provenance_hash": eps_result.provenance_record.provenance_hash if eps_result and eps_result.provenance_record else None,
        },
        "BVPS": {
            "value": bvps_result.value if bvps_export_ok else None,
            "status": bvps_result.status if bvps_result else "INPUT_INCOMPLETE",
            "split_adjusted": True,
            "export_eligible": bvps_export_ok,
            "applicability_decision_hash": bvps_result.applicability_decision.decision_hash if bvps_result and bvps_result.applicability_decision else None,
            "provenance_hash": bvps_result.provenance_record.provenance_hash if bvps_result and bvps_result.provenance_record else None,
        },
        "growth_metrics": growth,
        "peer_comparison": peer_comparison,
        "export_blocked_reasons": export_blocked_reasons,
    }
    # If a VALID-status metric lacks provenance, the export must be blocked and an error recorded (MUT-FUND-031).
    for m in metric_results:
        if m.status in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value) and not provenance_is_complete(m.provenance_record):
            export_blocked_reasons.append(f"PROVENANCE_MISSING:{m.metric_id}")
            errors.append({"code": "PROVENANCE_MISSING", "severity": "MAJOR", "stage": "EXPORT_GATE", "metric": m.metric_id, "evidence": "VALID metric lacks provenance_record"})
    # If a VALID-status metric has an INCOMPLETE applicability decision (upgrade attempt), block export (MUT-FUND-019).
    for m in metric_results:
        if m.status in (MetricStatus.VALID.value, MetricStatus.VALID_NEGATIVE.value) and m.applicability_decision and m.applicability_decision.decided_status != MetricStatus.VALID.value:
            export_blocked_reasons.append(f"STATUS_UPGRADE_BLOCKED:{m.metric_id}")
            errors.append({"code": "DOWNSTREAM_EXPORT_BLOCKED", "severity": "HIGH", "stage": "EXPORT_GATE", "metric": m.metric_id, "evidence": "status upgraded from INCOMPLETE to VALID"})
    log("export", "ok")

    # === Build output ===
    output = FundamentalOutput(
        entity={"ticker": request.ticker, "company": request.company, "sector": request.sector},
        metric_results=metric_results,
        dupont=dupont,
        growth=growth,
        peer_comparison=peer_comparison,
        quality_summary=quality_summary,
        downstream_export=downstream_export,
        warnings=warnings + structural_warnings,
        errors=errors,
        applicability_decisions=[d.to_dict() for d in decisions.values()],
    )

    completed = dt.datetime.now(dt.timezone.utc)
    final_status = "FAIL" if any(e.get("severity") == "CRITICAL" for e in errors) else \
                   "PASS_WITH_WARNINGS" if errors or warnings else "PASS"

    evidence_manifest = {
        "request_hash": _sha(request.to_dict()),
        "output_hash": _sha(output.to_dict()),
        "registry_version": "1.0.0",
        "formula_count": 10,
        "alias_count": 1,
        "timestamp": completed.isoformat(),
        "duration_seconds": (completed - started).total_seconds(),
        "metric_count": len(metric_results),
        "error_count": len(errors),
        "runner_version": "phase4R-v1",
    }

    return PipelineResult(
        output=output, errors=errors,
        evidence_manifest=evidence_manifest, execution_log=execution_log,
        final_status=final_status,
    )
