"""Collector → Fundamental adapter — Phase 6 integration.

Reads collector_output.json (from vn-financial-data-collector) and builds a
FundamentalRequest with full structural bindings. Does NOT call vnstock.

In INTEGRATED_COLLECTOR_BOUND mode, all financial inputs come from the
frozen collector packet — no direct provider calls.
"""
from __future__ import annotations
import json, hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "vn-fundamental-analysis-phase5R3b" / "workspace" / "implementation"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import (
    FundamentalRequest, MetricInput, MetricStatus,
    PeriodType, ReportingScope, AttributionScope, ShareBasis, DenominatorBasis,
)
from context.research_context import ResearchContext


def _hash_obj(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def adapt_collector_to_fundamental(collector_output: Dict[str, Any],
                                    context: ResearchContext) -> Tuple[FundamentalRequest, Dict[str, Any]]:
    """Build FundamentalRequest from collector output packet.

    Args:
        collector_output: Parsed collector_output.json dict
        context: ResearchContext with ticker, period, scope bindings

    Returns:
        (FundamentalRequest, adapter_evidence) tuple
    """
    ticker = collector_output.get("ticker", context.ticker)
    periods_raw = collector_output.get("reporting_scope", {}).get("annual_periods", [])
    periods = [int(p) for p in periods_raw if p]
    if not periods:
        periods = [context.fiscal_period] if context.fiscal_period else [2025]

    n = len(periods)
    metrics_dict = collector_output.get("metrics", {})

    def _extract_values(canonical_field: str) -> List[Optional[float]]:
        """Extract per-period values from collector metrics, filtered by status."""
        m = metrics_dict.get(canonical_field, {})
        vbp = m.get("values_by_period", {})
        status = m.get("status", "VALID")
        result = []
        for p in periods:
            v = vbp.get(str(p))
            if v is not None and status in ("VALID", "SUSPECT_ZERO_OR_MISSING"):
                result.append(float(v))
            else:
                result.append(None)
        return result

    def _get_field_status(canonical_field: str) -> str:
        m = metrics_dict.get(canonical_field, {})
        return m.get("status", "VALID")

    # Extract raw values
    revenue_raw = _extract_values("revenue")
    npat_raw = _extract_values("net_profit")
    ta_raw = _extract_values("total_assets")
    eq_raw = _extract_values("total_equity")
    eps_raw = _extract_values("eps_basic")
    shares_raw = _extract_values("shares_outstanding")

    # Normalize: VND_raw → tỷ VND, shares → tỷ shares
    def _norm_vnd(raw_list):
        return [v * 1e-9 if v is not None else None for v in raw_list]
    def _norm_shares(raw_list):
        return [v * 1e-9 if v is not None else None for v in raw_list]

    revenue_norm = _norm_vnd(revenue_raw)
    npat_norm = _norm_vnd(npat_raw)
    ta_norm = _norm_vnd(ta_raw)
    eq_norm = _norm_vnd(eq_raw)

    # Weighted shares: back-calc from EPS × NPAT (DERIVED_INPUT, non-circular)
    weighted_raw = []
    for i in range(n):
        npat_v = npat_raw[i] if i < len(npat_raw) else None
        eps_v = eps_raw[i] if i < len(eps_raw) else None
        if npat_v is not None and eps_v is not None and eps_v != 0:
            weighted_raw.append(npat_v / eps_v)
        else:
            weighted_raw.append(None)
    shares_norm = _norm_shares(weighted_raw)

    # Provenance from collector
    provenance = collector_output.get("provenance", {})
    sources = provenance.get("sources_used", [])
    source_id = sources[0].get("source_id", "collector") if sources else "collector"
    source_date = sources[0].get("accessed_at", "") if sources else ""

    # Build MetricInput with full structural bindings
    def _metric(mid, raw_vals, norm_vals, *, unit="BILLION_VND",
                rs=ReportingScope.CONSOLIDATED.value,
                as_=AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                pk=PeriodType.ANNUAL.value, db=None, sb=None, qs="VALID"):
        return MetricInput(
            metric_id=mid, values=norm_vals, periods=list(periods),
            unit=unit, scope=rs, source_id=f"collector:{ticker}:{mid}",
            quality_status=qs,
            raw_values=raw_vals,
            raw_unit="VND" if unit != "BILLION_SHARES" else "SHARES",
            raw_scale="UNIT",
            period_kind_bindings=[pk]*n,
            reporting_scope_bindings=[rs]*n,
            attribution_scope_bindings=[as_]*n,
            denominator_basis_bindings=[db]*n if db else [],
            share_basis_bindings=[sb]*n if sb else [],
            source_metric_ids=[f"collector_{mid}_{p}" for p in periods],
            source_dates=[source_date]*n,
            source_types=["collector_packet"]*n,
        )

    metrics = {
        "revenue": _metric("revenue", revenue_raw, revenue_norm,
                          as_=AttributionScope.TOTAL_GROUP.value),
        "net_income": _metric("net_income", npat_raw, npat_norm),
        "equity": _metric("equity", eq_raw, eq_norm,
                         pk=PeriodType.POINT_IN_TIME.value,
                         db=DenominatorBasis.AVERAGE_COMMON_EQUITY.value),
        "total_assets": _metric("total_assets", ta_raw, ta_norm,
                               as_=AttributionScope.TOTAL_GROUP.value,
                               pk=PeriodType.POINT_IN_TIME.value,
                               db=DenominatorBasis.AVERAGE_TOTAL_ASSETS.value),
    }

    # Shares — DERIVED_INPUT (back-calc from EPS)
    if any(v is not None for v in shares_norm):
        metrics["shares_outstanding"] = _metric(
            "shares_outstanding", weighted_raw, shares_norm,
            unit="BILLION_SHARES",
            pk=PeriodType.ANNUAL.value,
            sb=ShareBasis.WEIGHTED_AVERAGE_BASIC.value,
            qs="DERIVED_INPUT",
        )

    request = FundamentalRequest(
        ticker=ticker,
        company=collector_output.get("identity", {}).get("company_name", ""),
        exchange=collector_output.get("identity", {}).get("exchange", "HOSE"),
        sector=collector_output.get("identity", {}).get("sector", ""),
        reporting_currency="VND",
        periods=list(periods),
        metrics=metrics,
    )

    collector_hash = _hash_obj(collector_output)
    evidence = {
        "adapter": "collector_to_fundamental",
        "collector_output_hash": collector_hash,
        "context_hash": context.context_hash,
        "field_mapping": {k: v.get("fundamental_metric_id") for k, v in COLLECTOR_MAP.items()},
        "missing_to_zero_count": 0,
        "status_filtered": {k: _get_field_status(k) for k in COLLECTOR_MAP},
    }

    return request, evidence


# Import mapping from integration_version
from integration_version import COLLECTOR_TO_FUNDAMENTAL_MAP as COLLECTOR_MAP
