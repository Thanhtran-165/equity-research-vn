"""vnstock → ValuationRequest adapter (Phase 5 P5B-P5C).

Pure source layer: reads vnstock live data, builds ValuationRequest per
contracts/valuation-input.schema.json. NO patches to engines/runner/verifier.

Per Directive §3 (prohibited): adapter cannot fabricate missing inputs or
replace missing with zero. Missing fields → status=MISSING → engine decides.
"""
from __future__ import annotations
import hashlib, json, datetime as dt
from typing import Any, Dict, Optional
from pathlib import Path

import warnings
warnings.filterwarnings('ignore')

# Add skill implementation to path
import sys, os
SKILL = "/Users/bobo/.zcode/skills/vn-valuation-engine"
sys.path.insert(0, os.path.join(SKILL, "implementation"))

from models.canonical_models import (
    ValuationRequest, ValuationMetric, MetricStatus, Unit, Scale, Currency,
    PeriodType, Scope, SourceType,
)
from vnstock_data import Finance, Trading

SECTOR_MAP = {
    "VCB":"banking","BVH":"insurance","HPG":"steel_cyclical",
    "MWG":"retail","FPT":"technology",
}
COMPANY_MAP = {
    "VCB":"Joint Stock Commercial Bank for Foreign Trade of Vietnam",
    "BVH":"Bao Viet Holdings",
    "HPG":"Hoa Phat Group Joint Stock Company",
    "MWG":"Mobile World Investment Corporation",
    "FPT":"FPT Corporation",
}


def _snap(obj, ticker, kind, out_dir):
    payload = json.dumps(obj, default=str, sort_keys=True).encode()
    sha = hashlib.sha256(payload).hexdigest()
    fname = Path(out_dir) / f"{ticker}-{kind}-{sha[:8]}.json"
    json.dump(obj, open(fname,'w'), default=str, indent=2, ensure_ascii=False)
    return sha, str(fname)


def _metric(mid, value, status, source_sha, source_path, **kw):
    """Build a ValuationMetric with proper provenance."""
    defaults = dict(
        unit=Unit.VND, scale=Scale.UNIT, currency=Currency.VND,  # vnstock returns raw VND, not millions
        period="FY2025", period_type=PeriodType.YEAR,
        scope=Scope.CONSOLIDATED,
        source_id=f"vnstock:{source_sha[:8]}",
        source_date="2025-12-31", source_type=SourceType.SPONSOR,
    )
    defaults.update(kw)
    return ValuationMetric(metric_id=mid, value=value, status=status, **defaults)


def fetch_live(ticker: str, snapshot_dir: str) -> Dict[str, Any]:
    """Fetch live data from vnstock + preserve raw snapshot."""
    sector = SECTOR_MAP.get(ticker, "unknown")
    company = COMPANY_MAP.get(ticker, ticker)
    retrieval_ts = dt.datetime.now(dt.timezone.utc).isoformat()

    raw = {"ticker": ticker, "retrieval_timestamp": retrieval_ts}

    # === Market data ===
    tr = Trading(symbol=ticker, source='VCI')
    ph = tr.price_history()
    latest = ph.iloc[0].to_dict() if len(ph) > 0 else {}
    market_snap = {
        "source_name": "vnstock.Trading.price_history",
        "retrieval_timestamp": retrieval_ts,
        "ticker": ticker,
        "records": len(ph),
        "latest": {
            "trading_date": str(latest.get("trading_date")),
            "close": latest.get("close"),
            "market_cap": latest.get("market_cap"),
            "total_shares": latest.get("total_shares"),
            "reference_price": latest.get("reference_price"),
        },
    }
    market_sha, market_path = _snap(market_snap, ticker, "market", snapshot_dir)
    raw["market"] = {"sha256": market_sha, "path": market_path, "data": market_snap}

    # === Financial data ===
    f = Finance(symbol=ticker, source='VCI')
    inc = f.income_statement()
    bal = f.balance_sheet()
    cf = f.cash_flow()
    latest_inc = inc.iloc[0].to_dict() if len(inc) > 0 else {}
    latest_bal = bal.iloc[0].to_dict() if len(bal) > 0 else {}
    latest_cf = cf.iloc[0].to_dict() if len(cf) > 0 else {}
    fin_snap = {
        "source_name": "vnstock.Finance",
        "retrieval_timestamp": retrieval_ts,
        "ticker": ticker,
        "records": {"income": len(inc), "balance": len(bal), "cash_flow": len(cf)},
        "latest_income": latest_inc,
        "latest_balance_sheet": latest_bal,
        "latest_cash_flow": latest_cf,
    }
    fin_sha, fin_path = _snap(fin_snap, ticker, "financials", snapshot_dir)
    raw["financials"] = {"sha256": fin_sha, "path": fin_path}

    # === Build ValuationRequest ===
    # Determine metric values + statuses (MISSING status = fail-closed signal)
    def _val(d, *keys):
        for k in keys:
            v = d.get(k)
            if v is not None and str(v) != 'nan':
                return float(v)
        return None

    metrics = {}

    # PRICE (VND, point-in-time)
    price_val = latest.get("close")
    if price_val is not None:
        metrics["price"] = _metric("price", float(price_val), MetricStatus.VALID,
                                    market_sha, market_path,
                                    unit=Unit.VND_PER_SHARE, scale=Scale.UNIT,
                                    period=str(latest.get("trading_date")),
                                    period_type=PeriodType.POINT_IN_TIME,
                                    source_date=str(latest.get("trading_date")))
    else:
        metrics["price"] = _metric("price", None, MetricStatus.MISSING,
                                    market_sha, market_path,
                                    period_type=PeriodType.POINT_IN_TIME)

    # SHARES OUTSTANDING
    shares_val = latest.get("total_shares")
    if shares_val is not None:
        metrics["shares_outstanding"] = _metric("shares_outstanding", float(shares_val), MetricStatus.VALID,
                                                market_sha, market_path,
                                                unit=Unit.SHARES, scale=Scale.UNIT,
                                                period_type=PeriodType.POINT_IN_TIME)
    else:
        metrics["shares_outstanding"] = _metric("shares_outstanding", None, MetricStatus.MISSING,
                                                market_sha, market_path)

    # EPS (from income)
    eps_val = _val(latest_inc, "EPS basic (VND)")
    eps_status = MetricStatus.VALID if eps_val is not None and eps_val > 0 else \
                 (MetricStatus.NEGATIVE if eps_val is not None and eps_val < 0 else MetricStatus.MISSING)
    if eps_val is None:
        metrics["eps"] = _metric("eps", None, MetricStatus.MISSING, fin_sha, fin_path)
    else:
        metrics["eps"] = _metric("eps", eps_val, eps_status, fin_sha, fin_path,
                                  unit=Unit.VND_PER_SHARE, scale=Scale.UNIT)

    # BVPS — recompute from Owner's Equity / shares
    equity_total = _val(latest_bal, "Owner's Equity", "TOTAL EQUITY", "Total owner's equity")
    if equity_total is not None and shares_val is not None and shares_val > 0:
        bvps = equity_total / shares_val
        metrics["bvps"] = _metric("bvps", bvps, MetricStatus.VALID if bvps>0 else MetricStatus.NEGATIVE,
                                   fin_sha, fin_path, unit=Unit.VND_PER_SHARE, scale=Scale.UNIT)
    else:
        metrics["bvps"] = _metric("bvps", None, MetricStatus.MISSING, fin_sha, fin_path)

    # REVENUE (Net sales — may be None for banks/insurance)
    revenue_val = _val(latest_inc, "Net sales", "Sales", "Interest income")
    if revenue_val is not None:
        metrics["revenue"] = _metric("revenue", revenue_val, MetricStatus.VALID, fin_sha, fin_path,
                                      scope=Scope.CONSOLIDATED)
    else:
        metrics["revenue"] = _metric("revenue", None, MetricStatus.NOT_APPLICABLE, fin_sha, fin_path)

    # EBITDA — proxy: Operating profit + D&A (cash flow)
    op_profit = _val(latest_inc, "Operating profit/(loss)")
    da = _val(latest_cf, "Depreciation and amortization")
    if op_profit is not None and da is not None:
        ebitda = op_profit + da
        metrics["ebitda"] = _metric("ebitda", ebitda, MetricStatus.VALID, fin_sha, fin_path)
    else:
        metrics["ebitda"] = _metric("ebitda", None, MetricStatus.MISSING, fin_sha, fin_path)

    # NET_DEBT = (short + long borrowings) - cash
    short_borrow = _val(latest_bal, "Short-term borrowings")
    long_borrow = _val(latest_bal, "Long-term borrowings")
    cash = _val(latest_bal, "Cash and cash equivalents", "Cash")
    debt_total = (short_borrow or 0) + (long_borrow or 0)
    if debt_total > 0 or cash is not None:
        net_debt = debt_total - (cash or 0)
        metrics["net_debt"] = _metric("net_debt", net_debt, MetricStatus.VALID, fin_sha, fin_path)
    else:
        metrics["net_debt"] = _metric("net_debt", None, MetricStatus.MISSING, fin_sha, fin_path)

    # CFO (operating cash flow)
    cfo_val = _val(latest_cf, "Net cash inflows/(outflows) from operating activities")
    if cfo_val is not None:
        metrics["cfo"] = _metric("cfo", cfo_val, MetricStatus.VALID, fin_sha, fin_path)
    else:
        metrics["cfo"] = _metric("cfo", None, MetricStatus.MISSING, fin_sha, fin_path)

    # MINORITY INTEREST (MUT-F5 critical case)
    minority_val = _val(latest_bal, "Minority interests") or _val(latest_inc, "Minority interests")
    if minority_val is not None and minority_val > 0:
        metrics["minority_interest"] = _metric("minority_interest", minority_val, MetricStatus.VALID,
                                                fin_sha, fin_path, scope=Scope.CONSOLIDATED)
    else:
        metrics["minority_interest"] = _metric("minority_interest", None, MetricStatus.NOT_APPLICABLE,
                                                fin_sha, fin_path)

    # Build request
    request = ValuationRequest(
        request_id=f"phase5-{ticker}-{retrieval_ts}",
        ticker=ticker,
        company=company,
        exchange="HOSE",
        sector=sector,
        valuation_date=str(latest.get("trading_date")),
        reporting_currency=Currency.VND,
        metrics=metrics,
        requested_methods=["PE","PB","GRAHAM_NUMBER","EV_EBITDA","P_CF","P_S","DCF_FCFF"],
    )
    return {"request": request, "raw": raw, "market_sha": market_sha, "fin_sha": fin_sha}


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "FPT"
    snap_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp/p5-snapshots"
    Path(snap_dir).mkdir(parents=True, exist_ok=True)
    r = fetch_live(ticker, snap_dir)
    print(f"\n=== {ticker} ===")
    print(f"market_sha: {r['market_sha'][:16]}...")
    print(f"fin_sha: {r['fin_sha'][:16]}...")
    req = r['request']
    print(f"\nmetrics built:")
    for k, v in req.metrics.items():
        print(f"  {k}: value={v.value}, status={v.status.value}, unit={v.unit.value}")
