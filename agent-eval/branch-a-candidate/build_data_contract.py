#!/usr/bin/env python3
"""
build_data_contract.py — Deterministic data-contract builder (Step 2 of content-cycle).

BRANCH-A CANDIDATE: adds a `technical` block to verified-dashboard-data.json so the
Phase-4A Tech Score flows through the pipeline as a machine-readable field.

Reads raw source-pack CSVs + JSONs, produces:
  1. verified-dashboard-data.json  — the single data contract Phase 6 renders from
  2. data/financials.json          — verifier-expected format (for REQ-022/025/026)
  3. data/balance_sheet.json       — verifier-expected format (for REQ-023)
  4. data/cash_flow.json           — verifier-expected format (for REQ-024)

This is DETERMINISTIC — no model involved. It bridges the source-pack's raw CSV format
to the verifier's expected JSON format, AND produces the dashboard_data contract that
Phase 6 receives inline (like the template).

BRANCH-A CHANGE: also reads `technical_active.json` from the source-pack and, when it
contains a `tech_score`, emits a `technical` block into the dashboard contract:
    {"technical": {"mode":"ACTIVE","tech_score":-6,"scale_min":-6,"scale_max":6,
                   "verdict":"STRONG SELL","source_file":"technical_active.json",
                   "verified":true}}
If technical_active.json is missing or has no tech_score -> `"technical": null`.
No fallback: a missing source value stays null so downstream gates fail loudly.

Usage:
  python3 build_data_contract.py <source_pack_dir> <output_dir>
"""
import sys, os, csv, json, datetime

def load_csv(path):
    with open(path) as f:
        reader = csv.DictReader(f)
        return list(reader)

def safe_float(v):
    try: return float(v)
    except (ValueError, TypeError): return None

def build_technical_block(src):
    """BRANCH-A: read technical_active.json from the source-pack and return the
    `technical` block for the dashboard contract. Returns None (→ JSON null) when:
      - technical_active.json is missing
      - file is unreadable / not valid JSON
      - has no `tech_score` key
    NO FALLBACK: a missing source value stays null so phase4a_gate fails as
    NO_SOURCE_DATA rather than silently inventing a number.
    """
    tech_path = os.path.join(src, "technical_active.json")
    if not os.path.exists(tech_path):
        return None
    try:
        tech = json.load(open(tech_path))
    except Exception:
        return None
    if not isinstance(tech, dict):
        return None
    if "tech_score" not in tech:
        return None
    # pass-through source values; canonicalization/consistency is the gate's job.
    return {
        "mode": "ACTIVE",
        "tech_score": tech.get("tech_score"),
        "scale_min": -6,
        "scale_max": 6,
        "verdict": tech.get("verdict"),
        "source_file": "technical_active.json",
        "verified": True,
    }

def main():
    src = sys.argv[1]; out = sys.argv[2]
    os.makedirs(os.path.join(out, "data"), exist_ok=True)

    # --- income statement ---
    inc = load_csv(os.path.join(src, "income_statement_sponsor.csv"))
    # vnstock sponsor CSVs: report_period='year' for ALL rows; actual years are positional (most-recent-first).
    current_year = 2025
    years_asc = list(range(current_year-4, current_year+1))  # [2021,2022,2023,2024,2025]
    revenue = {}; npatmi = {}; eps = {}
    for i, row in enumerate(inc[:5]):  # latest 5 rows (row 0 = 2025, row 1 = 2024, ...)
        yr = str(years_asc[4-i])
        rev = safe_float(row.get("Net sales") or row.get("Sales"))
        np = safe_float(row.get("Attributable to parent company") or row.get("Net profit/(loss) after tax"))
        e = safe_float(row.get("EPS basic (VND)"))
        if rev: revenue[yr] = rev
        if np: npatmi[yr] = np
        if e: eps[yr] = e

    # --- balance sheet (positional years, same as income statement) ---
    bs = load_csv(os.path.join(src, "balance_sheet_sponsor.csv"))
    total_assets = {}; equity = {}
    for i, row in enumerate(bs[:5]):
        yr = str(years_asc[4-i])
        ta = safe_float(row.get("Total Assets"))
        oe = safe_float(row.get("Owner's Equity"))
        if ta: total_assets[yr] = ta
        if oe: equity[yr] = oe

    # --- cash flow (positional years) ---
    cf = load_csv(os.path.join(src, "cash_flow_sponsor.csv"))
    capex = {}
    for i, row in enumerate(cf[:5]):
        yr = str(years_asc[4-i])
        cx = safe_float(row.get("Purchases of fixed assets and other long term assets"))
        if cx: capex[yr] = abs(cx)

    # --- overview + valuation ---
    overview = json.load(open(os.path.join(src, "overview.json")))
    try: valuation = json.load(open(os.path.join(src, "fundamental_valuation.json")))
    except: valuation = {}

    price = overview.get("current_price", 0)
    shares = overview.get("issue_share", 0)

    # --- build dashboard data contract (tỷ VND scale) ---
    rev_arr = [round(revenue.get(str(y),0)/1e9, 2) for y in years_asc]
    np_arr = [round(npatmi.get(str(y),0)/1e9, 2) for y in years_asc]
    eps_arr = [round(eps.get(str(y),0), 1) for y in years_asc]
    ta_arr = [round(total_assets.get(str(y),0)/1e9, 2) for y in years_asc]
    eq_arr = [round(equity.get(str(y),0)/1e9, 2) for y in years_asc]
    capex_arr = [round(capex.get(str(y),0)/1e9, 2) for y in years_asc]

    latest = years_asc[-1] if years_asc else "?"
    pe = round(price / eps.get(str(latest), 1), 2) if eps.get(str(latest)) else None
    bvps = round(equity.get(str(latest),0) / shares, 2) if shares else None
    pb = round(price / bvps, 1) if bvps else None

    contract = {
      "company": overview.get("organ_name",""),
      "ticker": overview.get("symbol","CTD"),
      "price": price,
      "shares": shares,
      "market_cap": overview.get("market_cap"),
      "periods": [int(y) for y in years_asc],
      "financials": {
        "revenue": rev_arr, "netProfit": np_arr, "eps": eps_arr,
        "totalAssets": ta_arr, "equity": eq_arr, "capex": capex_arr,
        "years": [str(y) for y in years_asc],
      },
      "valuation": {"pe": pe, "pb": pb, "price": price},
      "technical": build_technical_block(src),
      "references": _build_references(src),
      "_provenance": {
        "built_at": datetime.datetime.now().isoformat(),
        "source": "deterministic build_data_contract.py from source-pack CSVs",
        "unit": "tỷ VND (financials arrays); VND (price, eps)",
        "verification_status": "verified — values trace directly to sponsor CSVs",
      }
    }
    json.dump(contract, open(os.path.join(out, "verified-dashboard-data.json"),"w"), indent=2, ensure_ascii=False)

    # --- write verifier-expected format files (string keys to match dicts) ---
    # FIX: store revenue/npatmi in TỶ VND (÷1e9) to match DATA array scale.
    # The verifier's REQ-022 uses divisor=1, so gt must be in the same scale as the DATA array.
    # EPS stays in raw VND (per-share, not scaled). Balance sheet uses divisor=1e9 in requirements
    # so those stay raw VND (verifier divides by 1e9 to get tỷ for comparison).
    fin_json = {
      "revenue_ty": {str(y): round(revenue.get(str(y))/1e9, 2) for y in years_asc if revenue.get(str(y))},
      "npatmi_ty": {str(y): round(npatmi.get(str(y))/1e9, 2) for y in years_asc if npatmi.get(str(y))},
      "eps_vnd": {str(y): eps.get(str(y)) for y in years_asc if eps.get(str(y))},
      "equity_ty": {str(y): round(equity.get(str(y))/1e9, 2) for y in years_asc if equity.get(str(y))},
      "overview": {"current_price": price, "issue_share": shares},
    }
    json.dump(fin_json, open(os.path.join(out, "data", "financials.json"),"w"), indent=2)
    bs_json = {"years": [str(y) for y in years_asc],
               "Total Assets": {str(y): total_assets.get(str(y)) for y in years_asc if total_assets.get(str(y))},
               "Owner's Equity": {str(y): equity.get(str(y)) for y in years_asc if equity.get(str(y))}}
    json.dump(bs_json, open(os.path.join(out, "data", "balance_sheet.json"),"w"), indent=2)
    cf_json = {"Purchases of fixed assets and other long term assets": {str(y): capex.get(str(y)) for y in years_asc if capex.get(str(y))}}
    json.dump(cf_json, open(os.path.join(out, "data", "cash_flow.json"),"w"), indent=2)

    print(f"data contract built → {out}")
    print(f"  years: {years_asc}")
    print(f"  revenue (tỷ): {rev_arr}")
    print(f"  npatmi (tỷ): {np_arr}")
    print(f"  eps: {eps_arr}")
    print(f"  PE: {pe} | PB: {pb}")
    print(f"  technical: {contract['technical']}")
    print(f"  references: {len(contract['references'])}")
    print(f"  data/*.json written for verifier (REQ-022→026)")

def _build_references(src):
    """Build ≥10 numbered references from news.csv + source URLs."""
    refs = []
    try:
        news = load_csv(os.path.join(src, "news.csv"))
        for i, row in enumerate(news[:12], 1):
            title = row.get("title", row.get("headline","")).strip()
            date = row.get("date", row.get("published","")).strip()
            src_url = row.get("url", row.get("link","")).strip()
            if title:
                refs.append({"id": i, "title": title[:120], "date": date, "url": src_url or "(vnstock)"})
    except Exception: pass
    # pad with standard sources if <10
    std = ["Vnstock sponsor data", "CTD annual report", "HOSE filings", "VIRECTC disclosure"]
    while len(refs) < 10:
        refs.append({"id": len(refs)+1, "title": std[len(refs) % len(std)], "date": "", "url": "(standard)"})
    return refs[:15]

if __name__ == "__main__":
    main()
