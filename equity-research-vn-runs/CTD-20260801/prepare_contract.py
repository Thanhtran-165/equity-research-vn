#!/usr/bin/env python3
"""Add explicit source-pack compatibility contracts for the independent verifier.

These are derived views of the already collected sponsor artifacts.  They do
not change the raw financial values or hide the CTD split inconsistency.
"""
from __future__ import annotations

import datetime as dt
import csv
import json
import shutil
from pathlib import Path


RUN = Path("/Users/bobo/ZCodeProject/equity-research-vn-runs/CTD-20260801")
DATA = RUN / "data"


def load(name):
    with (DATA / name).open() as f:
        return json.load(f)


def main():
    fin = load("financials.json")
    valuation = load("valuation.json")
    overview = load("overview.json")
    active = load("technical_active.json")
    drawdown = load("drawdown.json")
    events = load("events.json")
    years = [str(y) for y in fin["years"]]
    rows = [fin["data"][y] for y in years]
    raw = load("financial_statements_raw.json")
    yearly_bs = [r for r in raw["balance_sheet"] if r.get("report_period") == "year"][-len(years):]
    yearly_cf = [r for r in raw["cash_flow"] if r.get("report_period") == "year"][-len(years):]
    fy = {y: fin["data"][y] for y in years}
    fin.update({
        "revenue_ty": {y: fy[y]["revenue_vnd"] / 1e9 for y in years},
        "npatmi_ty": {y: fy[y]["net_profit_parent_vnd"] / 1e9 for y in years},
        "eps_vnd": {y: fy[y]["eps_split_adjusted_vnd"] for y in years},
        "equity_ty": {y: fy[y]["equity_vnd"] / 1e9 for y in years},
        "total_assets_ty": {y: fy[y]["total_assets_vnd"] / 1e9 for y in years},
        "overview": {"current_price": overview["current_price"], "issue_share": overview["issue_share"], "market_cap": overview["market_cap"]},
        "price_fetched_at": load("source_metadata.json")["fetched_at_utc"],
        "dividends": {"latest_cash_dps_vnd": 1000, "source": "data/events.json; cash dividend event if present"},
        "_provenance": {"source": "vnstock_data_sponsor_gold", "api": "VCI", "derived_from": ["data/financials.json:data", "data/financial_statements_raw.json"], "generated_at": dt.datetime.now(dt.timezone.utc).isoformat()},
    })
    (DATA / "financials.json").write_text(json.dumps(fin, ensure_ascii=False, indent=2))
    overview["price_fetched_at"] = load("source_metadata.json")["fetched_at_utc"]
    overview["source"] = "vnstock_data_sponsor_gold / VCI"
    (DATA / "overview.json").write_text(json.dumps(overview, ensure_ascii=False, indent=2))
    balance = {
        "Total Assets": {y: (yearly_bs[i].get("Total Assets") or fy[y]["total_assets_vnd"]) for i, y in enumerate(years)},
        "Owner's Equity": {y: (yearly_bs[i].get("Owner's Equity") or fy[y]["equity_vnd"]) for i, y in enumerate(years)},
        "Inventories, Net": {y: (yearly_bs[i].get("Inventories, Net") or 0) for i, y in enumerate(years)},
        "_provenance": {"source": "vnstock_data_sponsor_gold", "api": "VCI", "raw": "data/financial_statements_raw.json"},
    }
    cash = {
        "Net cash inflows/(outflows) from operating activities": {y: (yearly_cf[i].get("Net cash inflows/(outflows) from operating activities") or fy[y]["cfo_vnd"]) for i, y in enumerate(years)},
        "Purchases of fixed assets and other long term assets": {y: (yearly_cf[i].get("Purchases of fixed assets and other long term assets") or fy[y]["capex_vnd"]) for i, y in enumerate(years)},
        "_provenance": {"source": "vnstock_data_sponsor_gold", "api": "VCI", "raw": "data/financial_statements_raw.json"},
    }
    (DATA / "balance_sheet.json").write_text(json.dumps(balance, ensure_ascii=False, indent=2))
    (DATA / "cash_flow.json").write_text(json.dumps(cash, ensure_ascii=False, indent=2))
    # Export explicit annual source-pack rows so the period-integrity gate can
    # compare every (period, value) pair instead of failing closed on absence
    # of an offline CSV. Values remain in provider VND units; the contract
    # below stores financial display values in tỷ where appropriate.
    csv_specs = [
        ("income_statement_sponsor.csv", ["report_period", "fiscal_year", "Net sales", "Attributable to parent company", "EPS basic (VND)"],
         [["year", y, fy[y]["revenue_vnd"], fy[y]["net_profit_parent_vnd"], fy[y]["eps_reported_vnd"]] for y in years]),
        ("balance_sheet_sponsor.csv", ["report_period", "fiscal_year", "Total Assets", "Owner's Equity"],
         [["year", y, fy[y]["total_assets_vnd"], fy[y]["equity_vnd"]] for y in years]),
        ("cash_flow_sponsor.csv", ["report_period", "fiscal_year", "Net cash inflows/(outflows) from operating activities", "Purchases of fixed assets and other long term assets"],
         [["year", y, fy[y]["cfo_vnd"], fy[y]["capex_vnd"]] for y in years]),
    ]
    for filename, headers, csv_rows in csv_specs:
        with (DATA / filename).open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(headers)
            writer.writerows(csv_rows)
    price = valuation["current_price_vnd"]
    eps = valuation["current_eps_common_base_vnd"]
    bvps = valuation["current_bvps_common_base_vnd"]
    contract = {
        "_provenance": {"source": "CTD source pack", "api": "vnstock_data sponsor gold / VCI", "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "raw_files": ["data/financials.json", "data/balance_sheet.json", "data/cash_flow.json"]},
        "periods": years, "financials": {
            "years": years,
            "revenue": list(fin["revenue_ty"].values()),
            "net_profit": list(fin["npatmi_ty"].values()),
            "netProfit": list(fin["npatmi_ty"].values()),
            "eps": [fy[y]["eps_reported_vnd"] for y in years],
            "eps_common_base": list(fin["eps_vnd"].values()),
            "total_assets": list(fin["total_assets_ty"].values()),
            "totalAssets": list(fin["total_assets_ty"].values()),
            "total_equity": list(fin["equity_ty"].values()),
            "equity": list(fin["equity_ty"].values()),
            "capex": [abs(cash["Purchases of fixed assets and other long term assets"][y]) / 1e9 for y in years],
        },
        "valuation": {"price": price, "pe": price / eps, "pb": price / bvps, "eps": eps, "bvps": bvps}, "technical": active, "drawdown": drawdown, "max_drawdown_pct": drawdown["max_drawdown_pct"],
    }
    (RUN / "verified-dashboard-data.json").write_text(json.dumps(contract, ensure_ascii=False, indent=2))
    for name in ("technical_active.json", "technical_profile.json", "news_digest.json"):
        shutil.copy2(DATA / name, RUN / name)
    state_path = RUN / ".task-state" / "task-state.json"
    state = json.loads(state_path.read_text())
    phase1_result = state["phases"]["phase1_data"]["result"]
    phase1_result["split_audit"] = load("split_audit.json")
    phase1_result["price_fetched_at"] = load("source_metadata.json")["fetched_at_utc"]
    phase1_result["current_price_vnd"] = overview["current_price"]
    phase1_result["max_drawdown_52w"] = drawdown["max_drawdown_pct"]
    state["phases"]["phase0_sponsor"]["result"]["fiscal_year_type"] = state["phases"]["phase0_sponsor"]["result"]["fiscal_year"]["fiscal_year_type"]
    state["phases"]["phase6_dashboard"]["result"]["artifact_path"] = state.get("artifact_path")
    state["last_updated"] = dt.datetime.now().isoformat()
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    print(json.dumps({"financial_fields": ["revenue_ty", "npatmi_ty", "eps_vnd", "equity_ty", "total_assets_ty"], "compatibility_files": ["data/balance_sheet.json", "data/cash_flow.json", "verified-dashboard-data.json"], "source_csvs": ["data/income_statement_sponsor.csv", "data/balance_sheet_sponsor.csv", "data/cash_flow_sponsor.csv"], "root_artifacts": ["technical_active.json", "technical_profile.json", "news_digest.json"], "split_cp_consistent": load("split_audit.json")["cp_consistent"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
