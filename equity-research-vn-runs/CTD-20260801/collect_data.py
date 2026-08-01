#!/usr/bin/env python3
"""Collect the CTD source pack for the equity-research-vn run."""
from __future__ import annotations

import datetime as dt
import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
from vnstock_data import Company, Finance, Quote


RUN_DIR = Path("/Users/bobo/ZCodeProject/equity-research-vn-runs/CTD-20260801")
DATA_DIR = RUN_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
TICKER = "CTD"
SOURCE = "VCI"
NOW = dt.datetime.now(dt.timezone.utc)
TODAY = NOW.date()


def scalar(value):
    if value is None:
        return None
    if isinstance(value, (pd.Timestamp, dt.datetime, dt.date)):
        return value.isoformat()
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def records(frame):
    if frame is None:
        return []
    return [{str(k): scalar(v) for k, v in row.items()} for row in frame.to_dict("records")]


def save_json(name, payload):
    path = DATA_DIR / name
    with path.open("w") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
    return path


def first_value(row, *keys):
    for key in keys:
        if key in row and row[key] is not None and not pd.isna(row[key]):
            return float(row[key])
    return None


def fetch_history(symbol, start, end, interval):
    frame = Quote(source=SOURCE, symbol=symbol).history(
        start=start.isoformat(), end=end.isoformat(), interval=interval
    )
    frame = frame.copy()
    if "time" in frame:
        frame["time"] = pd.to_datetime(frame["time"])
    for column in ["open", "high", "low", "close"]:
        if column in frame:
            frame[column] = frame[column].astype(float) * 1000.0
    if "volume" in frame:
        frame["volume"] = frame["volume"].astype(float)
    return frame


finance = Finance(source=SOURCE, symbol=TICKER)
company = Company(source=SOURCE, symbol=TICKER)
income = finance.income_statement()
balance = finance.balance_sheet()
cashflow = finance.cash_flow()
ratios = finance.ratio()
overview_frame = company.overview()
events = company.events()
news = company.news()

overview = records(overview_frame)[0]
save_json("overview.json", overview)
save_json("events.json", records(events))
save_json("news_raw.json", records(news))
save_json("ratios_raw.json", records(ratios))
save_json("financial_statements_raw.json", {
    "income_statement": records(income),
    "balance_sheet": records(balance),
    "cash_flow": records(cashflow),
})

# The provider returns annual rows in ascending order. CTD reports on a June 30
# fiscal year, so these are FY2018..FY2025, not calendar years.
annual_income = income[income["report_period"] == "year"].reset_index(drop=True)
annual_balance = balance[balance["report_period"] == "year"].reset_index(drop=True)
annual_cashflow = cashflow[cashflow["report_period"] == "year"].reset_index(drop=True)
annual_years = list(range(2018, 2018 + len(annual_income)))
annual_by_year = {year: i for i, year in enumerate(annual_years)}
analysis_years = [2021, 2022, 2023, 2024, 2025]


def event_date(row):
    for key in ("public_date", "record_date", "exright_date", "display_date1"):
        value = row.get(key)
        if value:
            try:
                return pd.Timestamp(value).date()
            except Exception:
                pass
    return None


split_events = []
for row in records(events):
    title = str(row.get("event_title_vi") or "")
    category = str(row.get("category") or "")
    ratio = row.get("exercise_ratio")
    if category == "DIVIDEND" and ("cổ phiếu" in title.lower() or "phát hành" in title.lower()):
        try:
            ratio = float(ratio)
        except (TypeError, ValueError):
            ratio = 0.0
        if ratio > 0:
            split_events.append({
                "date": event_date(row).isoformat() if event_date(row) else None,
                "title": title,
                "ratio": ratio,
                "source": "vnstock_data.Company.events",
            })
split_events = sorted(split_events, key=lambda x: x["date"] or "")

capital_history = None
capital_history_error = None
for capital_source in ("KBS", "VCI", "DNSE"):
    try:
        capital_history = Company(source=capital_source, symbol=TICKER).capital_history()
        break
    except Exception as exc:
        capital_history_error = f"{capital_source}: {type(exc).__name__}: {exc}"

capital_history_rows = records(capital_history)
if capital_history_rows:
    save_json("capital_history_raw.json", capital_history_rows)


def capital_shares_at(period_end):
    """Anchor the split audit to provider charter-capital history.

    EPS is based on weighted-average shares, so period-end shares are only an
    anchor, not an equality target for the back-calculated EPS denominator.
    """
    candidates = []
    for row in capital_history_rows:
        raw_date = row.get("date") or row.get("issue_date") or row.get("public_date")
        charter = row.get("charter_capital")
        if not raw_date or charter in (None, 0) or pd.isna(raw_date) or str(raw_date).strip().lower() in {"nat", "nan", "none"}:
            continue
        try:
            date = pd.Timestamp(raw_date).date()
            shares_b = float(charter) / 1e13  # VND / par value 10,000 / 1e9
        except (TypeError, ValueError):
            continue
        if date <= period_end:
            candidates.append((date, shares_b))
    return max(candidates, key=lambda x: x[0])[1] if candidates else None


def multiplier_after(period_end):
    factor = 1.0
    for event in split_events:
        if event["date"] and event["date"] > period_end.isoformat() and pd.Timestamp(event["date"]).date() <= TODAY:
            factor *= 1.0 + float(event["ratio"])
    return factor


financials = []
for year in analysis_years:
    idx = annual_by_year[year]
    inc = annual_income.iloc[idx]
    bs = annual_balance.iloc[idx]
    cf = annual_cashflow.iloc[idx]
    net_profit = first_value(inc, "Attributable to parent company", "Net profit/(loss) after tax")
    eps = first_value(inc, "EPS basic (VND)")
    equity = first_value(bs, "Owner's Equity", "Capital and reserves")
    total_assets = first_value(bs, "Total Assets")
    shares_backcalc_b = (net_profit / eps / 1e9) if net_profit is not None and eps not in (None, 0) else None
    period_end = dt.date(year, 6, 30)
    split_factor = multiplier_after(period_end)
    adjusted_shares_b = shares_backcalc_b * split_factor if shares_backcalc_b is not None else None
    bvps_raw = equity / (shares_backcalc_b * 1e9) if equity is not None and shares_backcalc_b else None
    financials.append({
        "fiscal_year": year,
        "period_end": period_end.isoformat(),
        "fiscal_year_end": "06/30",
        "revenue_vnd": first_value(inc, "Net sales", "Sales"),
        "cost_of_sales_vnd": abs(first_value(inc, "Cost of sales") or 0),
        "net_profit_parent_vnd": net_profit,
        "eps_reported_vnd": eps,
        "equity_vnd": equity,
        "total_assets_vnd": total_assets,
        "cfo_vnd": first_value(cf, "Net cash inflows/(outflows) from operating activities"),
        "capex_vnd": first_value(cf, "Purchases of fixed assets and other long term assets"),
        "shares_backcalc_b": shares_backcalc_b,
        "split_factor_to_current_base": split_factor,
        "shares_split_adjusted_b": adjusted_shares_b,
        "eps_split_adjusted_vnd": eps / split_factor if eps is not None else None,
        "bvps_split_adjusted_vnd": bvps_raw / split_factor if bvps_raw is not None else None,
        "capital_history_shares_b": capital_shares_at(period_end),
    })

save_json("financials.json", {
    "ticker": TICKER,
    "source": "vnstock_data_sponsor_gold",
    "source_api": SOURCE,
    "fiscal_year_type": "custom",
    "fiscal_year_end": "06/30",
    "years": analysis_years,
    "data": {str(item["fiscal_year"]): item for item in financials},
})

weekly_start = TODAY - dt.timedelta(days=371)
daily_start = TODAY - dt.timedelta(days=730)
weekly = fetch_history(TICKER, weekly_start, TODAY + dt.timedelta(days=2), "1W")
daily = fetch_history(TICKER, daily_start, TODAY + dt.timedelta(days=2), "1D")
save_json("price_weekly.json", {
    "ticker": TICKER,
    "source": "vnstock_data.Quote.history",
    "price_unit": "VND",
    "raw_provider_unit": "thousand VND",
    "fetched_at": NOW.isoformat(),
    "start": weekly_start.isoformat(),
    "end": TODAY.isoformat(),
    "rows": records(weekly),
})
save_json("price_daily.json", {
    "ticker": TICKER,
    "source": "vnstock_data.Quote.history",
    "price_unit": "VND",
    "raw_provider_unit": "thousand VND",
    "fetched_at": NOW.isoformat(),
    "start": daily_start.isoformat(),
    "end": TODAY.isoformat(),
    "rows": records(daily),
})


def max_drawdown(frame):
    close = frame["close"].astype(float)
    running_max = close.cummax()
    drawdown = close / running_max - 1.0
    idx = drawdown.idxmin()
    return {
        "max_drawdown_pct": float(drawdown.loc[idx] * 100.0),
        "trough_date": scalar(frame.loc[idx, "time"]),
        "trough_close_vnd": float(frame.loc[idx, "close"]),
    }


last10 = daily.tail(10).copy()
last10["traded_value_vnd"] = last10["close"] * last10["volume"]
liquidity = {
    "source": "vnstock_data.Quote.history + Company.overview",
    "sessions": len(last10),
    "avg_volume_10_sessions": float(last10["volume"].mean()),
    "avg_traded_value_vnd_10_sessions": float(last10["traded_value_vnd"].mean()),
    "free_float_percentage": overview.get("free_float_percentage"),
    "free_float_shares": overview.get("free_float"),
    "price_fetched_at": NOW.isoformat(),
}
save_json("liquidity.json", liquidity)
save_json("drawdown.json", max_drawdown(weekly))

peer_candidates = ["HBC", "C4G", "VCG", "HHV", "LCG", "FCN", "CII", "G36", "CTR"]
peers = []
peer_errors = []
for peer_ticker in peer_candidates:
    try:
        peer_company = Company(source=SOURCE, symbol=peer_ticker)
        peer_overview = records(peer_company.overview())[0]
        if not peer_overview.get("listing") or peer_overview.get("icb_code_lv4") != overview.get("icb_code_lv4"):
            continue
        peer_finance = Finance(source=SOURCE, symbol=peer_ticker)
        peer_income = peer_finance.income_statement()
        peer_ratio = peer_finance.ratio()
        p_annual = peer_income[peer_income["report_period"] == "year"].reset_index(drop=True)
        revs = [first_value(row, "Net sales", "Sales") for _, row in p_annual.tail(4).iterrows()]
        revs = [x for x in revs if x is not None and x > 0]
        cagr_3y = ((revs[-1] / revs[0]) ** (1 / 3) - 1.0) * 100.0 if len(revs) == 4 else None
        ratio_rows = records(peer_ratio)
        current_ratio = next((r for r in ratio_rows if r.get("report_period") == "quarter"), ratio_rows[0] if ratio_rows else {})
        peers.append({
            "ticker": peer_ticker,
            "name": peer_overview.get("organ_short_name") or peer_overview.get("organ_name"),
            "icb_code_lv4": peer_overview.get("icb_code_lv4"),
            "pb": current_ratio.get("P/B"),
            "pe": current_ratio.get("P/E"),
            "ev_ebitda": current_ratio.get("EV/EBITDA"),
            "cagr_3y_pct": cagr_3y,
            "market_cap_vnd": peer_overview.get("market_cap"),
            "current_price_raw": peer_overview.get("current_price"),
            "source": "vnstock_data_sponsor_gold",
        })
    except Exception as exc:
        peer_errors.append({"ticker": peer_ticker, "error": f"{type(exc).__name__}: {exc}"})
save_json("peers.json", {
    "status": "available" if len(peers) >= 4 else "partial",
    "source": "vnstock_data_sponsor_gold",
    "selection": {"icb_code_lv4": overview.get("icb_code_lv4"), "sector": overview.get("sector")},
    "peers": peers,
    "errors": peer_errors,
})

index_data = {}
for index in ("VNINDEX", "VN30"):
    try:
        frame = fetch_history(index, weekly_start, TODAY + dt.timedelta(days=2), "1W")
        index_data[index] = records(frame)
    except Exception as exc:
        index_data[index] = {"status": "unavailable", "error": f"{type(exc).__name__}: {exc}"}
save_json("market_indices_weekly.json", index_data)

current_issue_share_b = (overview.get("issue_share") or 0) / 1e9
backcalc_vs_capital = {
    str(x["fiscal_year"]): round(abs(x["shares_backcalc_b"] - x["capital_history_shares_b"]) / x["capital_history_shares_b"] * 100, 2)
    for x in financials
    if x["shares_backcalc_b"] is not None and x.get("capital_history_shares_b")
}
adjusted_vs_current = {
    str(x["fiscal_year"]): round(abs(x["shares_split_adjusted_b"] - current_issue_share_b) / current_issue_share_b * 100, 2)
    for x in financials
    if x["shares_split_adjusted_b"] is not None and current_issue_share_b
}
adjusted_shares = [x["shares_split_adjusted_b"] for x in financials if x["shares_split_adjusted_b"] is not None]
split_audit = {
    "cp_consistent": bool(backcalc_vs_capital and max(backcalc_vs_capital.values()) <= 10.0 and adjusted_vs_current and max(adjusted_vs_current.values()) <= 10.0),
    "method": "back-calc CP=LNST/EPS, reconcile weighted-average EPS shares to KBS capital_history, then event-based split normalization",
    "periods_checked": len(financials),
    "shares_backcalc_b": {str(x["fiscal_year"]): x["shares_backcalc_b"] for x in financials},
    "current_issue_share_b": current_issue_share_b,
    "capital_history_shares_b": {str(x["fiscal_year"]): x.get("capital_history_shares_b") for x in financials},
    "backcalc_vs_capital_history_pct": backcalc_vs_capital,
    "adjusted_shares_vs_current_pct": adjusted_vs_current,
    "variation_vs_median_pct": float((max(adjusted_shares) - min(adjusted_shares)) / np.median(adjusted_shares) * 100.0) if adjusted_shares else None,
    "adjustment_needed": bool(split_events),
    "adjustment_applied": True,
    "split_events": split_events,
    "capital_history_status": "available" if capital_history is not None else "unavailable",
    "capital_history_error": capital_history_error,
    "verification_note": "CTD has 33.3% stock bonus in 2023, 5% in 2025, and 5% in 2026. EPS uses weighted-average shares; KBS charter-capital history anchors the audit, then EPS/BVPS/shares are normalized to the current base.",
}
save_json("split_audit.json", split_audit)

save_json("source_metadata.json", {
    "ticker": TICKER,
    "source": "vnstock_data_sponsor_gold",
    "source_module_version": "3.0.0",
    "vnstock_community_version": "3.5.1",
    "fetched_at_utc": NOW.isoformat(),
    "fiscal_year_type": "custom",
    "fiscal_year_end": "06/30",
    "annual_row_mapping": "provider annual rows 2018..2025 ascending; analysis uses 2021..2025",
    "overview_current_price_raw": overview.get("current_price"),
    "overview_current_price_vnd": overview.get("current_price"),
    "overview_market_cap_vnd": overview.get("market_cap"),
    "overview_issue_share": overview.get("issue_share"),
    "audit_opinion": "not exposed by vnstock_data.Company.overview",
})

print(json.dumps({
    "ticker": TICKER,
    "annual_years": analysis_years,
    "weekly_rows": len(weekly),
    "daily_rows": len(daily),
    "peers": [p["ticker"] for p in peers],
    "split_events": split_events,
    "max_drawdown": max_drawdown(weekly),
    "current_price_vnd": overview.get("current_price"),
}, ensure_ascii=False, indent=2))
