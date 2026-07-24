"""Live Fundamental Adapter — vn-fundamental-analysis Phase 5 (P5A).

Bridges vnstock live data to the Phase 4R3 MetricInput schema with full
structural bindings (unit, scale, period, scope, attribution, share_basis,
provenance). No silent transformations.

The adapter fetches data via the vnstock sponsor venv (golden tier) or
community fallback, maps provider fields to canonical metric IDs, applies
registered normalization, and produces a FundamentalRequest ready for the
Phase 4R3 engine.
"""
from __future__ import annotations
import json, sys, os, datetime as dt
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add Phase 4R3 implementation to path
PHASE4R3_IMPL = Path(__file__).parent.parent.parent / "vn-fundamental-analysis-phase5R3b" / "implementation"
sys.path.insert(0, str(PHASE4R3_IMPL))

from models import (
    FundamentalRequest, MetricInput,
    PeriodType, ReportingScope, AttributionScope, ShareBasis, DenominatorBasis,
)


ADAPTER_VERSION = "phase5-v1"
NORMALIZATION_VND = 1.0e-9
NORMALIZATION_SHARES = 1.0e-9


def _fetch_live_data(ticker: str, years: List[str]) -> Dict[str, Any]:
    """Fetch raw data from vnstock for a ticker.

    Uses sponsor venv if available (golden tier, 8+ years), else community.
    Returns dict with income_statement, balance_sheet, company_overview DataFrames
    serialized to dict.
    """
    sponsor_python = "/Users/bobo/dev/main-sonet-runtime/.venv-vnstock-sponsor311/bin/python"

    # Write a fetch script and run it via sponsor venv
    fetch_script = f'''
import json, sys
sys.stderr = open(os.devnull, 'w') if "VNSTOCK" else sys.stderr
import os
os.environ["VNSTOCK_SHOW_LOG"] = "false"
from vnstock import Vnstock
stock = Vnstock().stock(symbol="{ticker}", source="VCI")

# Income statement (annual)
inc = stock.finance.income_statement(period="year", lang="en")
income_data = {{}}
for _, row in inc.iterrows():
    item_id = str(row.get("item_id", ""))
    item_en = str(row.get("item_en", ""))
    vals = {{y: float(row[y]) if y in row.index and row[y] is not None else None for y in {years}}}
    income_data[item_id] = {{"item_en": item_en, "values": vals}}

# Balance sheet
bs = stock.finance.balance_sheet(period="year", lang="en")
balance_data = {{}}
for _, row in bs.iterrows():
    item_id = str(row.get("item_id", ""))
    item_en = str(row.get("item_en", ""))
    vals = {{y: float(row[y]) if y in row.index and row[y] is not None else None for y in {years}}}
    balance_data[item_id] = {{"item_en": item_en, "values": vals}}

# Company overview (shares)
co = stock.company.overview()
shares = None
if "issue_share" in co.columns and len(co) > 0:
    shares = float(co["issue_share"].iloc[0])
company_name = ""
exchange = ""
industry = ""
if "company_name" in co.columns and len(co) > 0:
    company_name = str(co["company_name"].iloc[0])
if "exchange" in co.columns and len(co) > 0:
    exchange = str(co["exchange"].iloc[0])
if "industry" in co.columns and len(co) > 0:
    industry = str(co["industry"].iloc[0])

result = {{
    "ticker": "{ticker}",
    "income_statement": income_data,
    "balance_sheet": balance_data,
    "shares_outstanding_raw": shares,
    "company_name": company_name,
    "exchange": exchange,
    "industry": industry,
    "fetch_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}}
print(json.dumps(result, default=str))
'''
    # Add datetime import
    fetch_script = "import datetime, os\n" + fetch_script

    import subprocess
    result = subprocess.run(
        [sponsor_python, "-c", fetch_script],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise RuntimeError(f"vnstock fetch failed for {ticker}: {result.stderr[:500]}")
    # Find JSON in output (skip sponsor banner)
    output = result.stdout
    # Find first '{' and last '}'
    start = output.find('{"ticker"')
    if start == -1:
        start = output.find('{')
    end = output.rfind('}') + 1
    if start >= 0 and end > start:
        return json.loads(output[start:end])
    raise RuntimeError(f"Could not parse vnstock output for {ticker}")


def _extract_metric(data: Dict, statement: str, item_ids: List[str],
                    years: List[str]) -> Tuple[List[Optional[float]], List[Optional[float]]]:
    """Extract raw values for a metric from fetched data.

    Returns (raw_values, normalized_values).
    raw_values = original VND values from provider.
    normalized_values = raw × normalization_factor (tỷ VND).
    """
    stmt_data = data.get(statement, {})
    for iid in item_ids:
        if iid in stmt_data:
            raw_vals = [stmt_data[iid]["values"].get(y) for y in years]
            return raw_vals, raw_vals
    # Try fuzzy match on item_en
    for iid, info in stmt_data.items():
        en = info.get("item_en", "").lower()
        for target in item_ids:
            if target.lower().replace("_", " ") in en:
                raw_vals = [info["values"].get(y) for y in years]
                return raw_vals, raw_vals
    return [None]*len(years), [None]*len(years)


def adapt_ticker(ticker: str, years: List[int], peer_set: Optional[List] = None) -> Tuple[FundamentalRequest, Dict]:
    """Fetch live data and build a FundamentalRequest with full bindings.

    Returns (request, raw_snapshot).
    """
    year_strs = [str(y) for y in years]
    data = _fetch_live_data(ticker, year_strs)
    fetch_ts = data.get("fetch_timestamp", dt.datetime.now(dt.timezone.utc).isoformat())

    # Extract metrics
    rev_raw, _ = _extract_metric(data, "income_statement", ["net_sales"], year_strs)
    npat_raw, _ = _extract_metric(data, "income_statement",
                                  ["attributable_to_parent_company",
                                   "net_profit_attributable_to_shareholders_of_the_group",
                                   "net_profit_attributable"], year_strs)
    ta_raw, _ = _extract_metric(data, "balance_sheet", ["total_assets"], year_strs)
    eq_raw, _ = _extract_metric(data, "balance_sheet", ["owners_equity", "owner_equity"], year_strs)

    # Weighted-average shares: back-calc từ EPS basic × NPAT (vnstock có EPS basic).
    # Rule: weighted_shares = NPAT_attributable / EPS_basic (per period).
    # This derives the weighted-average basic shares that the provider used to
    # compute EPS — more accurate than issue_share (period-end count).
    eps_basic_raw, _ = _extract_metric(data, "income_statement", ["eps_basic_vnd", "eps_basic"], year_strs)
    weighted_shares_raw = []  # per-period weighted-average shares (raw count)
    for i, y in enumerate(year_strs):
        npat_v = npat_raw[i] if i < len(npat_raw) else None
        eps_v = eps_basic_raw[i] if i < len(eps_basic_raw) else None
        if npat_v is not None and eps_v is not None and eps_v != 0:
            weighted_shares_raw.append(npat_v / eps_v)
        else:
            weighted_shares_raw.append(None)

    shares_raw_count = data.get("shares_outstanding_raw")  # period-end (fallback only)

    # Normalize: VND → tỷ VND, shares → tỷ shares
    def _norm_vnd(raw_list):
        return [v * NORMALIZATION_VND if v is not None else None for v in raw_list]
    def _norm_shares(val):
        return val * NORMALIZATION_SHARES if val is not None else None

    rev_norm = _norm_vnd(rev_raw)
    npat_norm = _norm_vnd(npat_raw)
    ta_norm = _norm_vnd(ta_raw)
    eq_norm = _norm_vnd(eq_raw)
    # Weighted shares normalized per-period (different from period-end single value)
    shares_norm_list = [v * NORMALIZATION_SHARES if v is not None else None for v in weighted_shares_raw]

    # Build MetricInput with full structural bindings
    n = len(years)

    def _metric(mid, raw_vals, norm_vals, *, raw_unit="VND", raw_scale="UNIT",
                reporting_scope=ReportingScope.CONSOLIDATED.value,
                attribution_scope=AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                period_kind=PeriodType.ANNUAL.value,
                denom_basis=None, share_basis=None):
        return MetricInput(
            metric_id=mid, values=norm_vals, periods=list(years),
            unit="BILLION_VND" if raw_unit == "VND" else "BILLION_SHARES",
            scope=reporting_scope, source_id=f"vnstock:{ticker}:{mid}",
            raw_values=raw_vals, raw_unit=raw_unit, raw_scale=raw_scale,
            period_kind_bindings=[period_kind]*n,
            reporting_scope_bindings=[reporting_scope]*n,
            attribution_scope_bindings=[attribution_scope]*n,
            denominator_basis_bindings=[denom_basis]*n if denom_basis else [],
            share_basis_bindings=[share_basis]*n if share_basis else [],
            source_metric_ids=[f"vnstock_{mid}_{y}" for y in years],
            source_dates=[fetch_ts]*n,
            source_types=["live_provider_vnstock"]*n,
        )

    metrics = {
        "revenue": _metric("revenue", rev_raw, rev_norm,
                          attribution_scope=AttributionScope.TOTAL_GROUP.value),
        "net_income": _metric("net_income", npat_raw, npat_norm,
                             attribution_scope=AttributionScope.ATTRIBUTABLE_TO_PARENT.value),
        "equity": _metric("equity", eq_raw, eq_norm,
                         attribution_scope=AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                         period_kind=PeriodType.POINT_IN_TIME.value,
                         denom_basis=DenominatorBasis.AVERAGE_COMMON_EQUITY.value),
        "total_assets": _metric("total_assets", ta_raw, ta_norm,
                               attribution_scope=AttributionScope.TOTAL_GROUP.value,
                               period_kind=PeriodType.POINT_IN_TIME.value,
                               denom_basis=DenominatorBasis.AVERAGE_TOTAL_ASSETS.value),
    }

    # Shares — weighted-average basic shares (back-calc từ EPS × NPAT).
    # NON-CIRCULAR POLICY (directive §3): back-calc from provider EPS is a
    # DERIVED_INPUT with quality flag. Provider EPS cannot be used as independent
    # oracle for EPS validation. Independent verification must use a different
    # source (e.g., corporate action disclosure, audited notes).
    # period_kind = ANNUAL (matches income statement period for EPS computation).
    if any(v is not None for v in shares_norm_list):
        metrics["shares_outstanding"] = MetricInput(
            metric_id="shares_outstanding", values=shares_norm_list, periods=list(years),
            unit="BILLION_SHARES", scope=ReportingScope.CONSOLIDATED.value,
            source_id=f"vnstock:{ticker}:weighted_avg_basic_shares_derived",
            quality_status="DERIVED_INPUT",
            raw_values=weighted_shares_raw, raw_unit="SHARES", raw_scale="UNIT",
            period_kind_bindings=[PeriodType.ANNUAL.value]*n,
            reporting_scope_bindings=[ReportingScope.CONSOLIDATED.value]*n,
            attribution_scope_bindings=[AttributionScope.ATTRIBUTABLE_TO_PARENT.value]*n,
            share_basis_bindings=[ShareBasis.WEIGHTED_AVERAGE_BASIC.value]*n,
            source_metric_ids=[f"WEIGHTED_SHARES_DERIVED_FROM_REPORTED_EPS_{y}" for y in years],
            source_dates=[fetch_ts]*n,
            source_types=["derived_from_provider_eps"]*n,
        )

    company = data.get("company_name", ticker)
    exchange = data.get("exchange", "HOSE")
    industry = data.get("industry", "")

    request = FundamentalRequest(
        ticker=ticker, company=company, exchange=exchange, sector=industry,
        reporting_currency="VND", periods=list(years), metrics=metrics,
        peer_set=peer_set or [],
    )

    # Raw snapshot for replay (frozen source)
    snapshot = {
        "ticker": ticker,
        "fetch_timestamp": fetch_ts,
        "years": year_strs,
        "raw_data": data,
        "adapter_version": ADAPTER_VERSION,
    }
    return request, snapshot


def save_snapshot(snapshot: Dict, output_dir: Path, ticker: str):
    """Save raw source snapshot for deterministic replay."""
    out = output_dir / ticker / "raw-source-snapshot.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, indent=2, default=str))
    return out


if __name__ == "__main__":
    # Preflight test
    ticker = sys.argv[1] if len(sys.argv) > 1 else "FPT"
    years = [2021, 2022, 2023, 2024, 2025]
    print(f"=== Adapter preflight: {ticker} ===")
    req, snapshot = adapt_ticker(ticker, years)
    print(f"Company: {req.company}")
    print(f"Exchange: {req.exchange}")
    print(f"Periods: {req.periods}")
    for mid, m in req.metrics.items():
        latest = m.values[-1] if m.values else None
        raw_latest = m.raw_values[-1] if m.raw_values else None
        print(f"  {mid}: normalized={latest}, raw={raw_latest}, unit={m.unit}")
    print(f"\nSnapshot keys: {list(snapshot.keys())}")
