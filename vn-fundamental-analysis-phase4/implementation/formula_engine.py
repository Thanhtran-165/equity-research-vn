"""Formula Engine — vn-fundamental-analysis Phase 4.

10 canonical formulas (DUPONT_NPM is alias of NET_PROFIT_MARGIN, not recomputed).
"""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
from models import (
    MetricResult, MetricStatus, CalculationStep, MetricInput,
    PeriodType, Scope, ShareBasis,
)


def _round(value: float, decimals: int = 2) -> float:
    """Deterministic rounding."""
    if value is None:
        return None
    return float(Decimal(str(value)).quantize(Decimal(f"0.{'0'*decimals if decimals > 0 else ''}"), rounding=ROUND_HALF_UP))


def _check_inputs(metrics: Dict[str, MetricInput], required: List[str], year: int) -> Tuple[bool, Dict[str, float]]:
    """Check if required inputs are available for a given year. Returns (ok, values)."""
    values = {}
    for req in required:
        m = metrics.get(req)
        if m is None:
            return False, {}
        v = m.get_value(year)
        if v is None:
            return False, {}
        values[req] = float(v)
    return True, values


def compute_eps(npat: float, shares: float, basis: str = "BASIC") -> MetricResult:
    """EPS = NPAT_attributable / weighted_average_shares."""
    formula_id = f"EPS-{basis}-v1.0.0"
    if shares == 0:
        return MetricResult(metric_id=f"EPS_{basis}", status=MetricStatus.ERROR.value,
                            value=None, unit="VND_PER_SHARE", formula_id=formula_id, formula_version="1.0.0",
                            errors=["DIVISION_BY_ZERO"])

    eps = _round(npat / shares * 1e9 / 1e9)  # tỷ/tỷ = đơn vị cơ bản
    # Actually: NPAT in tỷ VND, shares in tỷ shares → NPAT/shares = đồng/cp directly
    eps_value = npat / shares  # tỷ VND / tỷ shares = VND per share (no ×1000)

    status = MetricStatus.VALID_NEGATIVE if eps_value < 0 else MetricStatus.VALID

    return MetricResult(
        metric_id=f"EPS_{basis}", status=status.value, value=_round(eps_value),
        unit="VND_PER_SHARE", formula_id=formula_id, formula_version="1.0.0",
        normalized_inputs={"net_income": npat, "shares": shares, "basis": basis},
        calculation_trace=[
            CalculationStep(1, f"NPAT_attributable = {npat} tỷ VND", ["net_income"], npat),
            CalculationStep(2, f"weighted_avg_{basis}_shares = {shares} tỷ", ["shares_outstanding"], shares),
            CalculationStep(3, f"EPS = NPAT / shares = {npat}/{shares} = {_round(eps_value)}", ["net_income", "shares_outstanding"], _round(eps_value)),
        ],
        period="ANNUAL", scope="ATTRIBUTABLE_TO_PARENT", basis=basis,
    )


def compute_bvps(equity: float, shares: float) -> MetricResult:
    """BVPS = common_equity / period_end_shares."""
    if shares == 0:
        return MetricResult(metric_id="BVPS", status=MetricStatus.ERROR.value,
                            value=None, unit="VND_PER_SHARE", formula_id="BVPS-v1.0.0", formula_version="1.0.0",
                            errors=["DIVISION_BY_ZERO"])

    bvps = equity / shares  # tỷ VND / tỷ shares = VND per share
    status = MetricStatus.VALID_NEGATIVE if bvps < 0 else MetricStatus.VALID

    warnings = []
    if bvps > 1_000_000:
        warnings.append("BVPS_OUT_OF_SANITY_RANGE")

    return MetricResult(
        metric_id="BVPS", status=status.value, value=_round(bvps),
        unit="VND_PER_SHARE", formula_id="BVPS-v1.0.0", formula_version="1.0.0",
        normalized_inputs={"equity": equity, "shares": shares},
        calculation_trace=[
            CalculationStep(1, f"common_equity = {equity} tỷ VND", ["equity"], equity),
            CalculationStep(2, f"period_end_shares = {shares} tỷ", ["shares_outstanding"], shares),
            CalculationStep(3, f"BVPS = equity / shares = {_round(bvps)}", ["equity", "shares_outstanding"], _round(bvps)),
        ],
        period="POINT_IN_TIME", scope="ATTRIBUTABLE_TO_PARENT", warnings=warnings,
    )


def compute_roe(npat: float, avg_equity: float) -> MetricResult:
    """ROE = NPAT / average_equity × 100."""
    if avg_equity == 0:
        return MetricResult(metric_id="ROE", status=MetricStatus.ERROR.value,
                            value=None, unit="PERCENTAGE", formula_id="ROE-v1.0.0", formula_version="1.0.0",
                            errors=["DIVISION_BY_ZERO"])
    if avg_equity < 0:
        return MetricResult(metric_id="ROE", status=MetricStatus.MANUAL_REVIEW_REQUIRED.value,
                            value=_round(npat / avg_equity * 100), unit="PERCENTAGE",
                            formula_id="ROE-v1.0.0", formula_version="1.0.0",
                            warnings=["NEGATIVE_EQUITY_NOT_MEANINGFUL"],
                            normalized_inputs={"npat": npat, "avg_equity": avg_equity},
                            calculation_trace=[
                                CalculationStep(1, f"NPAT = {npat}", ["net_income"], npat),
                                CalculationStep(2, f"avg_equity = {avg_equity} (NEGATIVE)", ["equity"], avg_equity),
                                CalculationStep(3, f"ROE = {npat}/{avg_equity}×100 = {_round(npat/avg_equity*100)}", ["net_income","equity"], _round(npat/avg_equity*100)),
                            ])
    roe = npat / avg_equity * 100
    return MetricResult(
        metric_id="ROE", status=MetricStatus.VALID.value, value=_round(roe),
        unit="PERCENTAGE", formula_id="ROE-v1.0.0", formula_version="1.0.0",
        normalized_inputs={"npat": npat, "avg_equity": avg_equity},
        calculation_trace=[
            CalculationStep(1, f"NPAT = {npat}", ["net_income"], npat),
            CalculationStep(2, f"avg_equity = {avg_equity}", ["equity"], avg_equity),
            CalculationStep(3, f"ROE = {npat}/{avg_equity}×100 = {_round(roe)}", ["net_income","equity"], _round(roe)),
        ],
    )


def compute_roa(npat: float, avg_assets: float) -> MetricResult:
    """ROA = NPAT / average_total_assets × 100."""
    if avg_assets == 0:
        return MetricResult(metric_id="ROA", status=MetricStatus.ERROR.value,
                            value=None, unit="PERCENTAGE", formula_id="ROA-v1.0.0", formula_version="1.0.0",
                            errors=["DIVISION_BY_ZERO"])
    roa = npat / avg_assets * 100
    return MetricResult(
        metric_id="ROA", status=MetricStatus.VALID.value, value=_round(roa),
        unit="PERCENTAGE", formula_id="ROA-v1.0.0", formula_version="1.0.0",
        normalized_inputs={"npat": npat, "avg_assets": avg_assets},
        calculation_trace=[
            CalculationStep(1, f"NPAT = {npat}", ["net_income"], npat),
            CalculationStep(2, f"avg_total_assets = {avg_assets}", ["total_assets"], avg_assets),
            CalculationStep(3, f"ROA = {npat}/{avg_assets}×100 = {_round(roa)}", ["net_income","total_assets"], _round(roa)),
        ],
    )


def compute_net_profit_margin(npat: float, revenue: float) -> MetricResult:
    """NPM = NPAT / Revenue (ratio form — display ×100 for percentage)."""
    if revenue == 0:
        return MetricResult(metric_id="NET_PROFIT_MARGIN", status=MetricStatus.ERROR.value,
                            value=None, unit="RATIO", formula_id="NET-PROFIT-MARGIN-v1.0.0", formula_version="1.0.0",
                            errors=["DIVISION_BY_ZERO"])
    npm = npat / revenue
    return MetricResult(
        metric_id="NET_PROFIT_MARGIN", status=MetricStatus.VALID.value, value=_round(npm, 6),
        unit="RATIO", formula_id="NET-PROFIT-MARGIN-v1.0.0", formula_version="1.0.0",
        normalized_inputs={"npat": npat, "revenue": revenue},
        calculation_trace=[
            CalculationStep(1, f"NPAT = {npat}", ["net_income"], npat),
            CalculationStep(2, f"revenue = {revenue}", ["revenue"], revenue),
            CalculationStep(3, f"NPM = {npat}/{revenue} = {_round(npm, 6)}", ["net_income","revenue"], _round(npm, 6)),
        ],
        note="display_value = NPM × 100 = percentage",  # positional ok since note is after provenance
    )


def compute_asset_turnover(revenue: float, avg_assets: float) -> MetricResult:
    """AT = Revenue / average_total_assets."""
    if avg_assets == 0:
        return MetricResult(metric_id="DUPONT_AT", status=MetricStatus.ERROR.value,
                            value=None, unit="RATIO", formula_id="DUPONT-AT-v1.0.0", formula_version="1.0.0",
                            errors=["DIVISION_BY_ZERO"])
    at = revenue / avg_assets
    return MetricResult(
        metric_id="DUPONT_AT", status=MetricStatus.VALID.value, value=_round(at, 6),
        unit="RATIO", formula_id="DUPONT-AT-v1.0.0", formula_version="1.0.0",
        normalized_inputs={"revenue": revenue, "avg_assets": avg_assets},
        calculation_trace=[
            CalculationStep(1, f"revenue = {revenue}", ["revenue"], revenue),
            CalculationStep(2, f"avg_total_assets = {avg_assets}", ["total_assets"], avg_assets),
            CalculationStep(3, f"AT = {revenue}/{avg_assets} = {_round(at, 6)}", ["revenue","total_assets"], _round(at, 6)),
        ],
    )


def compute_equity_multiplier(avg_assets: float, avg_equity: float) -> MetricResult:
    """EM = average_total_assets / average_common_equity."""
    if avg_equity == 0:
        return MetricResult(metric_id="DUPONT_EM", status=MetricStatus.ERROR.value,
                            value=None, unit="RATIO", formula_id="DUPONT-EM-v1.0.0", formula_version="1.0.0",
                            errors=["DIVISION_BY_ZERO"])
    em = avg_assets / avg_equity
    return MetricResult(
        metric_id="DUPONT_EM", status=MetricStatus.VALID.value, value=_round(em, 6),
        unit="RATIO", formula_id="DUPONT-EM-v1.0.0", formula_version="1.0.0",
        normalized_inputs={"avg_assets": avg_assets, "avg_equity": avg_equity},
        calculation_trace=[
            CalculationStep(1, f"avg_total_assets = {avg_assets}", ["total_assets"], avg_assets),
            CalculationStep(2, f"avg_common_equity = {avg_equity}", ["equity"], avg_equity),
            CalculationStep(3, f"EM = {avg_assets}/{avg_equity} = {_round(em, 6)}", ["total_assets","equity"], _round(em, 6)),
        ],
    )


def compute_dupont_roe(npm: float, at: float, em: float) -> float:
    """DuPont ROE = NPM × AT × EM. Returns ratio (not percentage)."""
    return npm * at * em


def check_dupont_consistency(reconstructed_roe: float, direct_roe_pct: float, tolerance: float = 0.005) -> Tuple[bool, float]:
    """Check |reconstructed_ROE - direct_ROE/100| < tolerance."""
    direct_roe_ratio = direct_roe_pct / 100
    diff = abs(reconstructed_roe - direct_roe_ratio)
    return diff < tolerance, diff


def compute_cagr(beginning: float, ending: float, years: int) -> MetricResult:
    """CAGR = (ending/beginning)^(1/years) - 1. Fail-closed on non-positive base."""
    formula_id = "CAGR-v1.0.0"
    if beginning <= 0:
        return MetricResult(metric_id="CAGR", status=MetricStatus.NOT_APPLICABLE.value,
                            value=None, unit="RATIO", formula_id=formula_id, formula_version="1.0.0",
                            warnings=["CAGR_NONPOSITIVE_BASE: beginning value ≤ 0"])
    if years <= 0:
        return MetricResult(metric_id="CAGR", status=MetricStatus.NOT_APPLICABLE.value,
                            value=None, unit="RATIO", formula_id=formula_id, formula_version="1.0.0",
                            warnings=["CAGR_PERIOD_INVALID: years ≤ 0"])

    ratio = ending / beginning
    if ratio <= 0:
        return MetricResult(metric_id="CAGR", status=MetricStatus.NOT_APPLICABLE.value,
                            value=None, unit="RATIO", formula_id=formula_id, formula_version="1.0.0",
                            warnings=["CAGR_SIGN_CROSSING: ending/beginning ≤ 0"])

    cagr = ratio ** (1.0 / years) - 1
    return MetricResult(
        metric_id="CAGR", status=MetricStatus.VALID.value, value=_round(cagr, 6),
        unit="RATIO", formula_id=formula_id, formula_version="1.0.0",
        normalized_inputs={"beginning": beginning, "ending": ending, "years": years},
        calculation_trace=[
            CalculationStep(1, f"beginning = {beginning}", ["first_year"], beginning),
            CalculationStep(2, f"ending = {ending}", ["last_year"], ending),
            CalculationStep(3, f"ratio = {ending}/{beginning} = {_round(ratio, 6)}", ["first_year","last_year"], _round(ratio, 6)),
            CalculationStep(4, f"CAGR = {ratio:.6f}^(1/{years}) - 1 = {_round(cagr, 6)}", ["ratio","years"], _round(cagr, 6)),
        ],
    )
