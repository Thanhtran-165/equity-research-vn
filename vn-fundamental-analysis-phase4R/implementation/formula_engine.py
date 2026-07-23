"""Formula Engine — vn-fundamental-analysis Phase 4R.

10 canonical formulas (DUPONT_NPM is alias of NET_PROFIT_MARGIN, not recomputed).

Phase 4R adds structural identity to every MetricResult:
- share_basis, period_kind, reporting_scope, attribution_scope, denominator_basis
- formula_input_metric_ids: role -> source metric_id (formula input identity, MUT-FUND-014)
- applicability_decision + provenance_record slots (filled by runner)

The numeric computation is unchanged from Phase 4 — only identity metadata is added.
"""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
from models import (
    MetricResult, MetricStatus, CalculationStep, MetricInput,
    PeriodType, ReportingScope, AttributionScope, ShareBasis, DenominatorBasis,
)


def _round(value: float, decimals: int = 2) -> float:
    """Deterministic rounding."""
    if value is None:
        return None
    return float(Decimal(str(value)).quantize(Decimal(f"0.{'0'*decimals if decimals > 0 else ''}"), rounding=ROUND_HALF_UP))


def compute_eps(npat: float, shares: float, basis: str = ShareBasis.WEIGHTED_AVERAGE_BASIC.value,
                share_basis: str = ShareBasis.WEIGHTED_AVERAGE_BASIC.value,
                period_kind: str = PeriodType.ANNUAL.value,
                reporting_scope: str = ReportingScope.CONSOLIDATED.value,
                attribution_scope: str = AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                npat_metric_id: str = "net_income", shares_metric_id: str = "shares_outstanding") -> MetricResult:
    """EPS = NPAT_attributable / weighted_average_shares.

    `basis` selects EPS_BASIC vs EPS_DILUTED metric_id and formula_id.
    `share_basis` is the identity of the shares input (must be BASIC family for EPS_BASIC).
    """
    eps_kind = "BASIC" if "BASIC" in basis.upper() else "DILUTED"
    metric_id = f"EPS_{eps_kind}"
    formula_id = f"EPS-{eps_kind}-v1.0.0"
    if shares == 0:
        return MetricResult(metric_id=metric_id, status=MetricStatus.ERROR.value,
                            value=None, unit="VND_PER_SHARE", formula_id=formula_id, formula_version="1.0.0",
                            errors=["DIVISION_BY_ZERO"], share_basis=share_basis, period_kind=period_kind,
                            reporting_scope=reporting_scope, attribution_scope=attribution_scope,
                            formula_input_metric_ids={"net_income": npat_metric_id, "shares": shares_metric_id})
    eps_value = npat / shares  # tỷ VND / tỷ shares = VND per share
    status = MetricStatus.VALID_NEGATIVE if eps_value < 0 else MetricStatus.VALID
    return MetricResult(
        metric_id=metric_id, status=status.value, value=_round(eps_value),
        unit="VND_PER_SHARE", formula_id=formula_id, formula_version="1.0.0",
        normalized_inputs={"net_income": npat, "shares": shares, "basis": basis},
        calculation_trace=[
            CalculationStep(1, f"NPAT_attributable = {npat} tỷ VND", ["net_income"], npat),
            CalculationStep(2, f"{share_basis} shares = {shares} tỷ", ["shares_outstanding"], shares),
            CalculationStep(3, f"EPS = NPAT / shares = {npat}/{shares} = {_round(eps_value)}", ["net_income", "shares_outstanding"], _round(eps_value)),
        ],
        period=period_kind, scope=reporting_scope, basis=eps_kind,
        share_basis=share_basis, period_kind=period_kind,
        reporting_scope=reporting_scope, attribution_scope=attribution_scope,
        formula_input_metric_ids={"net_income": npat_metric_id, "shares": shares_metric_id},
    )


def compute_bvps(equity: float, shares: float,
                 share_basis: str = ShareBasis.PERIOD_END_BASIC.value,
                 denominator_basis: str = DenominatorBasis.ENDING_COMMON_EQUITY.value,
                 period_kind: str = PeriodType.POINT_IN_TIME.value,
                 reporting_scope: str = ReportingScope.CONSOLIDATED.value,
                 attribution_scope: str = AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                 equity_metric_id: str = "equity", shares_metric_id: str = "shares_outstanding") -> MetricResult:
    """BVPS = common_equity / period_end_shares."""
    if shares == 0:
        return MetricResult(metric_id="BVPS", status=MetricStatus.ERROR.value,
                            value=None, unit="VND_PER_SHARE", formula_id="BVPS-v1.0.0", formula_version="1.0.0",
                            errors=["DIVISION_BY_ZERO"], share_basis=share_basis, denominator_basis=denominator_basis,
                            period_kind=period_kind, reporting_scope=reporting_scope, attribution_scope=attribution_scope,
                            formula_input_metric_ids={"equity": equity_metric_id, "shares": shares_metric_id})
    bvps = equity / shares
    status = MetricStatus.VALID_NEGATIVE if bvps < 0 else MetricStatus.VALID
    warnings = []
    if bvps > 1_000_000:
        warnings.append("BVPS_OUT_OF_SANITY_RANGE")
    return MetricResult(
        metric_id="BVPS", status=status.value, value=_round(bvps),
        unit="VND_PER_SHARE", formula_id="BVPS-v1.0.0", formula_version="1.0.0",
        normalized_inputs={"equity": equity, "shares": shares},
        calculation_trace=[
            CalculationStep(1, f"common_equity = {equity} tỷ VND ({denominator_basis})", ["equity"], equity),
            CalculationStep(2, f"{share_basis} shares = {shares} tỷ", ["shares_outstanding"], shares),
            CalculationStep(3, f"BVPS = equity / shares = {_round(bvps)}", ["equity", "shares_outstanding"], _round(bvps)),
        ],
        period=period_kind, scope=reporting_scope,
        share_basis=share_basis, denominator_basis=denominator_basis,
        period_kind=period_kind, reporting_scope=reporting_scope, attribution_scope=attribution_scope,
        formula_input_metric_ids={"equity": equity_metric_id, "shares": shares_metric_id},
        warnings=warnings,
    )


def compute_roe(npat: float, avg_equity: float,
                denominator_basis: str = DenominatorBasis.AVERAGE_COMMON_EQUITY.value,
                period_kind: str = PeriodType.ANNUAL.value,
                reporting_scope: str = ReportingScope.CONSOLIDATED.value,
                attribution_scope: str = AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                npat_metric_id: str = "net_income", equity_metric_id: str = "equity") -> MetricResult:
    """ROE = NPAT / average_equity × 100."""
    if avg_equity == 0:
        return MetricResult(metric_id="ROE", status=MetricStatus.ERROR.value,
                            value=None, unit="PERCENTAGE", formula_id="ROE-v1.0.0", formula_version="1.0.0",
                            errors=["DIVISION_BY_ZERO"], denominator_basis=denominator_basis,
                            period_kind=period_kind, reporting_scope=reporting_scope, attribution_scope=attribution_scope,
                            formula_input_metric_ids={"net_income": npat_metric_id, "equity": equity_metric_id})
    if avg_equity < 0:
        v = npat / avg_equity * 100
        return MetricResult(metric_id="ROE", status=MetricStatus.MANUAL_REVIEW_REQUIRED.value,
                            value=_round(v), unit="PERCENTAGE", formula_id="ROE-v1.0.0", formula_version="1.0.0",
                            warnings=["NEGATIVE_EQUITY_NOT_MEANINGFUL"],
                            normalized_inputs={"npat": npat, "avg_equity": avg_equity},
                            calculation_trace=[
                                CalculationStep(1, f"NPAT = {npat}", ["net_income"], npat),
                                CalculationStep(2, f"avg_equity = {avg_equity} (NEGATIVE)", ["equity"], avg_equity),
                                CalculationStep(3, f"ROE = {npat}/{avg_equity}×100 = {_round(v)}", ["net_income", "equity"], _round(v)),
                            ],
                            denominator_basis=denominator_basis, period_kind=period_kind,
                            reporting_scope=reporting_scope, attribution_scope=attribution_scope,
                            formula_input_metric_ids={"net_income": npat_metric_id, "equity": equity_metric_id})
    roe = npat / avg_equity * 100
    return MetricResult(
        metric_id="ROE", status=MetricStatus.VALID.value, value=_round(roe),
        unit="PERCENTAGE", formula_id="ROE-v1.0.0", formula_version="1.0.0",
        normalized_inputs={"npat": npat, "avg_equity": avg_equity},
        calculation_trace=[
            CalculationStep(1, f"NPAT = {npat}", ["net_income"], npat),
            CalculationStep(2, f"avg_equity = {avg_equity} ({denominator_basis})", ["equity"], avg_equity),
            CalculationStep(3, f"ROE = {npat}/{avg_equity}×100 = {_round(roe)}", ["net_income", "equity"], _round(roe)),
        ],
        denominator_basis=denominator_basis, period_kind=period_kind,
        reporting_scope=reporting_scope, attribution_scope=attribution_scope,
        formula_input_metric_ids={"net_income": npat_metric_id, "equity": equity_metric_id},
    )


def compute_roa(npat: float, avg_assets: float,
                denominator_basis: str = DenominatorBasis.AVERAGE_TOTAL_ASSETS.value,
                period_kind: str = PeriodType.ANNUAL.value,
                reporting_scope: str = ReportingScope.CONSOLIDATED.value,
                attribution_scope: str = AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                npat_metric_id: str = "net_income", assets_metric_id: str = "total_assets") -> MetricResult:
    """ROA = NPAT / average_total_assets × 100."""
    if avg_assets == 0:
        return MetricResult(metric_id="ROA", status=MetricStatus.ERROR.value,
                            value=None, unit="PERCENTAGE", formula_id="ROA-v1.0.0", formula_version="1.0.0",
                            errors=["DIVISION_BY_ZERO"], denominator_basis=denominator_basis,
                            period_kind=period_kind, reporting_scope=reporting_scope, attribution_scope=attribution_scope,
                            formula_input_metric_ids={"net_income": npat_metric_id, "total_assets": assets_metric_id})
    roa = npat / avg_assets * 100
    return MetricResult(
        metric_id="ROA", status=MetricStatus.VALID.value, value=_round(roa),
        unit="PERCENTAGE", formula_id="ROA-v1.0.0", formula_version="1.0.0",
        normalized_inputs={"npat": npat, "avg_assets": avg_assets},
        calculation_trace=[
            CalculationStep(1, f"NPAT = {npat}", ["net_income"], npat),
            CalculationStep(2, f"avg_total_assets = {avg_assets} ({denominator_basis})", ["total_assets"], avg_assets),
            CalculationStep(3, f"ROA = {npat}/{avg_assets}×100 = {_round(roa)}", ["net_income", "total_assets"], _round(roa)),
        ],
        denominator_basis=denominator_basis, period_kind=period_kind,
        reporting_scope=reporting_scope, attribution_scope=attribution_scope,
        formula_input_metric_ids={"net_income": npat_metric_id, "total_assets": assets_metric_id},
    )


def compute_net_profit_margin(npat: float, revenue: float,
                              period_kind: str = PeriodType.ANNUAL.value,
                              reporting_scope: str = ReportingScope.CONSOLIDATED.value,
                              attribution_scope: str = AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                              npat_metric_id: str = "net_income", revenue_metric_id: str = "revenue") -> MetricResult:
    """NPM = NPAT / Revenue."""
    if revenue == 0:
        return MetricResult(metric_id="NET_PROFIT_MARGIN", status=MetricStatus.ERROR.value,
                            value=None, unit="RATIO", formula_id="NET-PROFIT-MARGIN-v1.0.0", formula_version="1.0.0",
                            errors=["DIVISION_BY_ZERO"], period_kind=period_kind,
                            reporting_scope=reporting_scope, attribution_scope=attribution_scope,
                            formula_input_metric_ids={"net_income": npat_metric_id, "revenue": revenue_metric_id})
    npm = npat / revenue
    return MetricResult(
        metric_id="NET_PROFIT_MARGIN", status=MetricStatus.VALID.value, value=_round(npm, 6),
        unit="RATIO", formula_id="NET-PROFIT-MARGIN-v1.0.0", formula_version="1.0.0",
        normalized_inputs={"npat": npat, "revenue": revenue},
        calculation_trace=[
            CalculationStep(1, f"NPAT = {npat}", ["net_income"], npat),
            CalculationStep(2, f"revenue = {revenue}", ["revenue"], revenue),
            CalculationStep(3, f"NPM = {npat}/{revenue} = {_round(npm, 6)}", ["net_income", "revenue"], _round(npm, 6)),
        ],
        period_kind=period_kind, reporting_scope=reporting_scope, attribution_scope=attribution_scope,
        formula_input_metric_ids={"net_income": npat_metric_id, "revenue": revenue_metric_id},
        note="display_value = NPM × 100 = percentage; DUPONT-NPM is alias",
    )


def compute_asset_turnover(revenue: float, avg_assets: float,
                           denominator_basis: str = DenominatorBasis.AVERAGE_TOTAL_ASSETS.value,
                           period_kind: str = PeriodType.ANNUAL.value,
                           reporting_scope: str = ReportingScope.CONSOLIDATED.value,
                           attribution_scope: str = AttributionScope.TOTAL_GROUP.value,
                           revenue_metric_id: str = "revenue", assets_metric_id: str = "total_assets") -> MetricResult:
    """AT = Revenue / average_total_assets."""
    if avg_assets == 0:
        return MetricResult(metric_id="DUPONT_AT", status=MetricStatus.ERROR.value,
                            value=None, unit="RATIO", formula_id="DUPONT-AT-v1.0.0", formula_version="1.0.0",
                            errors=["DIVISION_BY_ZERO"], denominator_basis=denominator_basis,
                            period_kind=period_kind, reporting_scope=reporting_scope, attribution_scope=attribution_scope,
                            formula_input_metric_ids={"revenue": revenue_metric_id, "total_assets": assets_metric_id})
    at = revenue / avg_assets
    return MetricResult(
        metric_id="DUPONT_AT", status=MetricStatus.VALID.value, value=_round(at, 6),
        unit="RATIO", formula_id="DUPONT-AT-v1.0.0", formula_version="1.0.0",
        normalized_inputs={"revenue": revenue, "avg_assets": avg_assets},
        calculation_trace=[
            CalculationStep(1, f"revenue = {revenue}", ["revenue"], revenue),
            CalculationStep(2, f"avg_total_assets = {avg_assets} ({denominator_basis})", ["total_assets"], avg_assets),
            CalculationStep(3, f"AT = {revenue}/{avg_assets} = {_round(at, 6)}", ["revenue", "total_assets"], _round(at, 6)),
        ],
        denominator_basis=denominator_basis, period_kind=period_kind,
        reporting_scope=reporting_scope, attribution_scope=attribution_scope,
        formula_input_metric_ids={"revenue": revenue_metric_id, "total_assets": assets_metric_id},
    )


def compute_equity_multiplier(avg_assets: float, avg_equity: float,
                              denominator_basis: str = DenominatorBasis.AVERAGE_COMMON_EQUITY.value,
                              period_kind: str = PeriodType.ANNUAL.value,
                              reporting_scope: str = ReportingScope.CONSOLIDATED.value,
                              attribution_scope: str = AttributionScope.TOTAL_GROUP.value,
                              assets_metric_id: str = "total_assets", equity_metric_id: str = "equity") -> MetricResult:
    """EM = average_total_assets / average_common_equity."""
    if avg_equity == 0:
        return MetricResult(metric_id="DUPONT_EM", status=MetricStatus.ERROR.value,
                            value=None, unit="RATIO", formula_id="DUPONT-EM-v1.0.0", formula_version="1.0.0",
                            errors=["DIVISION_BY_ZERO"], denominator_basis=denominator_basis,
                            period_kind=period_kind, reporting_scope=reporting_scope, attribution_scope=attribution_scope,
                            formula_input_metric_ids={"total_assets": assets_metric_id, "equity": equity_metric_id})
    em = avg_assets / avg_equity
    return MetricResult(
        metric_id="DUPONT_EM", status=MetricStatus.VALID.value, value=_round(em, 6),
        unit="RATIO", formula_id="DUPONT-EM-v1.0.0", formula_version="1.0.0",
        normalized_inputs={"avg_assets": avg_assets, "avg_equity": avg_equity},
        calculation_trace=[
            CalculationStep(1, f"avg_total_assets = {avg_assets}", ["total_assets"], avg_assets),
            CalculationStep(2, f"avg_common_equity = {avg_equity} ({denominator_basis})", ["equity"], avg_equity),
            CalculationStep(3, f"EM = {avg_assets}/{avg_equity} = {_round(em, 6)}", ["total_assets", "equity"], _round(em, 6)),
        ],
        denominator_basis=denominator_basis, period_kind=period_kind,
        reporting_scope=reporting_scope, attribution_scope=attribution_scope,
        formula_input_metric_ids={"total_assets": assets_metric_id, "equity": equity_metric_id},
    )


def compute_dupont_roe(npm: float, at: float, em: float) -> float:
    """DuPont ROE = NPM × AT × EM. Returns ratio (not percentage)."""
    return npm * at * em


def check_dupont_consistency(reconstructed_roe: float, direct_roe_pct: float, tolerance: float = 0.005) -> Tuple[bool, float]:
    """Check |reconstructed_ROE - direct_ROE/100| < tolerance."""
    direct_roe_ratio = direct_roe_pct / 100
    diff = abs(reconstructed_roe - direct_roe_ratio)
    return diff < tolerance, diff


def compute_cagr(beginning: float, ending: float, years: int,
                 period_kind: str = PeriodType.ANNUAL.value,
                 reporting_scope: str = ReportingScope.CONSOLIDATED.value) -> MetricResult:
    """CAGR = (ending/beginning)^(1/years) - 1. Fail-closed on non-positive base."""
    formula_id = "CAGR-v1.0.0"
    if beginning <= 0:
        return MetricResult(metric_id="CAGR", status=MetricStatus.NOT_APPLICABLE.value,
                            value=None, unit="RATIO", formula_id=formula_id, formula_version="1.0.0",
                            warnings=["CAGR_NONPOSITIVE_BASE: beginning value ≤ 0"],
                            period_kind=period_kind, reporting_scope=reporting_scope)
    if years <= 0:
        return MetricResult(metric_id="CAGR", status=MetricStatus.NOT_APPLICABLE.value,
                            value=None, unit="RATIO", formula_id=formula_id, formula_version="1.0.0",
                            warnings=["CAGR_PERIOD_INVALID: years ≤ 0"],
                            period_kind=period_kind, reporting_scope=reporting_scope)
    ratio = ending / beginning
    if ratio <= 0:
        return MetricResult(metric_id="CAGR", status=MetricStatus.NOT_APPLICABLE.value,
                            value=None, unit="RATIO", formula_id=formula_id, formula_version="1.0.0",
                            warnings=["CAGR_SIGN_CROSSING: ending/beginning ≤ 0"],
                            period_kind=period_kind, reporting_scope=reporting_scope)
    cagr = ratio ** (1.0 / years) - 1
    return MetricResult(
        metric_id="CAGR", status=MetricStatus.VALID.value, value=_round(cagr, 6),
        unit="RATIO", formula_id=formula_id, formula_version="1.0.0",
        normalized_inputs={"beginning": beginning, "ending": ending, "years": years},
        calculation_trace=[
            CalculationStep(1, f"beginning = {beginning}", ["first_year"], beginning),
            CalculationStep(2, f"ending = {ending}", ["last_year"], ending),
            CalculationStep(3, f"ratio = {ending}/{beginning} = {_round(ratio, 6)}", ["first_year", "last_year"], _round(ratio, 6)),
            CalculationStep(4, f"CAGR = {ratio:.6f}^(1/{years}) - 1 = {_round(cagr, 6)}", ["ratio", "years"], _round(cagr, 6)),
        ],
        period_kind=period_kind, reporting_scope=reporting_scope,
    )
