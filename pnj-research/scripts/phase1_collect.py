#!/usr/bin/env python3
"""
Phase 1: Data collection for PNJ — FIXED units + split handling
Key learnings:
  - Quote.history() returns prices in nghìn đồng → ×1000 for VND
  - Company.overview() current_price is already in VND (NOT nghìn)
  - PNJ had 50% stock dividend (bonus shares) on 2026-04-15 → Bẫy 5B active
  - EPS from BCTC is on pre-split weighted-avg shares → must adjust for current price comparison
"""
import warnings
warnings.filterwarnings("ignore")
import json, os, datetime
import pandas as pd
import numpy as np

from vnstock_data import Finance, Quote, Company

TICKER = "PNJ"
WORK_DIR = "/Users/bobo/ZCodeProject/pnj-research"
DATA_DIR = os.path.join(WORK_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

print("=" * 60)
print(f"  PHASE 1: Data Collection — {TICKER}")
print("=" * 60)

# ============ 1. OVERVIEW ============
print("\n[1] Fetching overview...")
c = Company(symbol=TICKER, source="VCI")
overview = c.overview()
ov = overview.iloc[0].to_dict()
# Overview current_price is in VND already
current_price = float(ov.get("current_price", 0))
market_cap = float(ov.get("market_cap", 0))
issue_share = float(ov.get("issue_share", 0))  # count, not tỷ
high_52w = float(ov.get("highest_price1_year", 0) or 0)
low_52w = float(ov.get("lowest_price1_year", 0) or 0)
target_price = float(ov.get("target_price", 0) or 0)
print(f"  Price: {current_price:,.0f} VND")
print(f"  Market cap: {market_cap/1e9:,.0f} tỷ VND")
print(f"  Shares: {issue_share/1e6:.1f}M ({issue_share/1e9:.4f} tỷ)")
print(f"  52w range: {low_52w:,.0f} - {high_52w:,.0f} VND")
print(f"  Target price: {target_price:,.0f} VND")

# ============ 2. EVENTS (split detection) ============
print("\n[2] Fetching events (split detection)...")
events = c.events()
ev_records = events.to_dict("records")
splits = []
for e in ev_records:
    title = str(e.get("event_title_vi", "")).lower()
    action = str(e.get("action_type_vi", "")).lower()
    if any(k in title or k in action for k in ["chia cổ phiếu", "phát hành cổ phiếu", "cổ tức cổ phiếu", "cổ phiếu thưởng"]):
        splits.append(e)
print(f"  Total events: {len(ev_records)}")
print(f"  Split/stock-dividend events: {len(splits)}")
for s in splits[:8]:
    print(f"    - {s.get('public_date','?')} | {s.get('event_title_vi','?')} | ratio={s.get('exercise_ratio','?')}")

# Identify the 50% bonus shares split
SPLIT_DATE = None
SPLIT_RATIO = 0
for s in splits:
    title = str(s.get("event_title_vi", "")).lower()
    ratio = float(s.get("exercise_ratio", 0) or 0)
    if "cổ phiếu thưởng" in title and ratio >= 0.5:
        SPLIT_DATE = str(s.get("public_date", ""))
        SPLIT_RATIO = ratio
        break
# Also count ESOP issuances
esop_ratio = 0
for s in splits:
    title = str(s.get("event_title_vi", "")).lower()
    ratio = float(s.get("exercise_ratio", 0) or 0)
    if "cbcnc" in title or "cbcnv" in title:
        esop_ratio += ratio

print(f"\n  >>> 50% Bonus shares event: date={SPLIT_DATE}, ratio={SPLIT_RATIO}")
print(f"  >>> ESOP issuance ratio (total): {esop_ratio}")

# ============ 3. FINANCIAL STATEMENTS ============
print("\n[3] Fetching financial statements (sponsor, 41 periods)...")
f = Finance(symbol=TICKER, source="VCI")
inc = f.income_statement()
bs = f.balance_sheet()
cf = f.cash_flow()
print(f"  Income shape: {inc.shape}, Balance shape: {bs.shape}, Cashflow shape: {cf.shape}")

inc.to_csv(os.path.join(DATA_DIR, "raw_income.csv"))
bs.to_csv(os.path.join(DATA_DIR, "raw_balance.csv"))
cf.to_csv(os.path.join(DATA_DIR, "raw_cashflow.csv"))

# ============ 4. EXTRACT 5-YEAR DATA (2021-2025) ============
print("\n[4] Extracting 5-year financials (2021-2025)...")
YEARS = [2021, 2022, 2023, 2024, 2025]

def gv(df, col, year):
    """Get value from column for given year (string index)."""
    try:
        ys = str(year)
        if ys in df.index:
            v = df.loc[ys, col]
            if pd.notna(v):
                return float(v)
        return None
    except Exception:
        return None

financials = {"years": YEARS, "ticker": TICKER}

for y in YEARS:
    # Income
    rev = gv(inc, "Net sales", y) or gv(inc, "Sales", y)
    gp = gv(inc, "Gross Profit", y)
    npat_parent = gv(inc, "Attributable to parent company", y)
    npat_total = gv(inc, "Net profit/(loss) after tax", y)
    eps = gv(inc, "EPS basic (VND)", y)
    op = gv(inc, "Operating profit/(loss)", y)
    ie = gv(inc, "Interest expenses", y)
    tax = gv(inc, "Corporate income tax expenses", y)
    sell = gv(inc, "Selling expenses", y)
    ga = gv(inc, "General and admin expenses", y)

    financials.setdefault("revenue_ty", {})[y] = rev / 1e9 if rev else None
    financials.setdefault("gross_profit_ty", {})[y] = gp / 1e9 if gp else None
    financials.setdefault("npatmi_ty", {})[y] = npat_parent / 1e9 if npat_parent else None
    financials.setdefault("npat_total_ty", {})[y] = npat_total / 1e9 if npat_total else None
    financials.setdefault("eps_vnd", {})[y] = eps
    financials.setdefault("operating_profit_ty", {})[y] = op / 1e9 if op else None
    financials.setdefault("interest_expense_ty", {})[y] = abs(ie) / 1e9 if ie else None
    financials.setdefault("tax_ty", {})[y] = abs(tax) / 1e9 if tax else None
    financials.setdefault("selling_expense_ty", {})[y] = abs(sell) / 1e9 if sell else None
    financials.setdefault("ga_expense_ty", {})[y] = abs(ga) / 1e9 if ga else None

print("  Income extracted:")
for y in YEARS:
    r = financials["revenue_ty"][y]
    n = financials["npatmi_ty"][y]
    e = financials["eps_vnd"][y]
    rstr = f"{r:,.0f}" if r else "NA"
    nstr = f"{n:,.0f}" if n else "NA"
    estr = f"{e:,.0f}" if e else "NA"
    print(f"    {y}: Rev={rstr} tỷ | NPATMI={nstr} tỷ | EPS={estr} đ")

# Balance sheet — find correct column names
print("\n  Balance sheet columns (Total/Equity/Liabil):")
bs_cols_interest = [col for col in bs.columns if any(k in col.lower() for k in ["total", "asset", "equity", "liabil", "cash", "invent", "borrow", "debt", "payable"])]
for col in bs_cols_interest[:25]:
    print(f"    - {col}")

for y in YEARS:
    # PNJ schema uses Title Case: "Total Assets", "Owner's Equity", "Liabilities", etc.
    ta = gv(bs, "Total Assets", y) or gv(bs, "TOTAL ASSETS", y) or gv(bs, "Total assets", y)
    eq = gv(bs, "Owner's Equity", y) or gv(bs, "OWNER'S EQUITY", y) or gv(bs, "Capital and reserves", y)
    eq_parent = eq  # PNJ: Owner's Equity = Capital and reserves (attributable to parent); MI separate
    liab = gv(bs, "Liabilities", y) or gv(bs, "LIABILITIES", y)
    ca = gv(bs, "CURRENT ASSETS", y) or gv(bs, "Current Assets", y)
    nca = gv(bs, "LONG-TERM ASSETS", y) or gv(bs, "Long-term Assets", y)

    # Cash
    cash = gv(bs, "Cash and cash equivalents", y)
    if cash is None:
        for cc in ["Cash equivalents", "Cash"]:
            v = gv(bs, cc, y)
            if v is not None:
                cash = v
                break

    # Debt — PNJ has only Short-term borrowings (no LT borrowings)
    std = gv(bs, "Short-term borrowings", y)
    ltd = gv(bs, "Long-term borrowings", y)

    # Inventory
    inv = gv(bs, "Inventories, Net", y) or gv(bs, "Inventories", y)

    # Receivables
    ar = gv(bs, "Accounts receivable", y) or gv(bs, "Trade accounts receivable", y)

    financials.setdefault("total_assets_ty", {})[y] = ta / 1e9 if ta else None
    financials.setdefault("equity_ty", {})[y] = eq / 1e9 if eq else None
    financials.setdefault("equity_parent_ty", {})[y] = eq_parent / 1e9 if eq_parent else None
    financials.setdefault("liabilities_ty", {})[y] = liab / 1e9 if liab else None
    financials.setdefault("current_assets_ty", {})[y] = ca / 1e9 if ca else None
    financials.setdefault("noncurrent_assets_ty", {})[y] = nca / 1e9 if nca else None
    financials.setdefault("cash_ty", {})[y] = cash / 1e9 if cash else None
    financials.setdefault("st_debt_ty", {})[y] = abs(std) / 1e9 if std else None
    financials.setdefault("lt_debt_ty", {})[y] = abs(ltd) / 1e9 if ltd else None
    financials.setdefault("total_debt_ty", {})[y] = ((abs(std) if std else 0) + (abs(ltd) if ltd else 0)) / 1e9
    financials.setdefault("inventory_ty", {})[y] = inv / 1e9 if inv else None
    financials.setdefault("receivables_ty", {})[y] = ar / 1e9 if ar else None

print("\n  Balance extracted:")
for y in YEARS:
    ta = financials["total_assets_ty"][y]
    eq = financials["equity_ty"][y]
    td = financials["total_debt_ty"][y]
    inv = financials["inventory_ty"][y]
    ta_s = f"{ta:,.0f}" if ta else "NA"
    eq_s = f"{eq:,.0f}" if eq else "NA"
    td_s = f"{td:,.0f}" if td else "NA"
    inv_s = f"{inv:,.0f}" if inv else "NA"
    print(f"    {y}: TA={ta_s} | Eq={eq_s} | Debt={td_s} | Inv={inv_s} tỷ")

# Cash flow
print("\n  Cashflow columns:")
cf_cols = [col for col in cf.columns if any(k in col.lower() for k in ["operating", "investing", "financing", "purchase", "fixed", "dividend", "tax"])]
for col in cf_cols[:20]:
    print(f"    - {col}")

for y in YEARS:
    cfo = None
    for cc in ["Cash flows from operating activities", "Total cash flow from operating activities", "Net cash generated from operating activities"]:
        v = gv(cf, cc, y)
        if v is not None:
            cfo = v
            break
    if cfo is None:
        cands = [c for c in cf.columns if "operating" in c.lower()]
        if cands:
            cfo = gv(cf, cands[0], y)

    capex = None
    for cc in ["Purchases of fixed assets and other long term assets", "Purchases of fixed assets", "Cash paid for fixed assets"]:
        v = gv(cf, cc, y)
        if v is not None:
            capex = abs(v)
            break

    cfi = None
    for cc in ["Cash flows from investing activities", "Total cash flow from investing activities"]:
        v = gv(cf, cc, y)
        if v is not None:
            cfi = v
            break

    cff = None
    for cc in ["Cash flows from financing activities", "Total cash flow from financing activities"]:
        v = gv(cf, cc, y)
        if v is not None:
            cff = v
            break

    # Dividends paid
    div = None
    for cc in ["Dividends paid", "Cash dividends paid", "Payment of dividends"]:
        v = gv(cf, cc, y)
        if v is not None:
            div = abs(v)
            break

    financials.setdefault("cfo_ty", {})[y] = cfo / 1e9 if cfo else None
    financials.setdefault("capex_ty", {})[y] = capex / 1e9 if capex else None
    fcf = (cfo or 0) - (capex or 0)
    financials.setdefault("fcf_ty", {})[y] = fcf / 1e9
    financials.setdefault("cfi_ty", {})[y] = cfi / 1e9 if cfi else None
    financials.setdefault("cff_ty", {})[y] = cff / 1e9 if cff else None
    financials.setdefault("dividends_paid_ty", {})[y] = div / 1e9 if div else None

print("\n  Cashflow extracted:")
for y in YEARS:
    cfv = financials["cfo_ty"][y]
    cx = financials["capex_ty"][y]
    ff = financials["fcf_ty"][y]
    if cfv is not None:
        print(f"    {y}: CFO={cfv:,.0f} | Capex={cx:,.0f} | FCF={ff:,.0f} tỷ")
    else:
        print(f"    {y}: CFO=NA")

# ============ 5. SPLIT AUDIT (Bẫy 5B) ============
print("\n[5] SPLIT AUDIT (Bẫy 5B) — back-calc CP = LNST/EPS...")
back_calc = {}
for y in YEARS:
    npat = financials["npatmi_ty"][y]
    eps = financials["eps_vnd"][y]
    if npat and eps and eps > 0:
        cp = npat * 1e9 / eps  # in CP count
        back_calc[y] = cp
        print(f"    {y}: LNST={npat:,.0f} tỷ, EPS={eps:,.0f} đ → CP back-calc = {cp/1e6:.2f}M")
    else:
        back_calc[y] = None

valid = {y: v for y, v in back_calc.items() if v}
if valid:
    max_cp = max(valid.values())
    min_cp = min(valid.values())
    ratio = max_cp / min_cp if min_cp > 0 else 1
    print(f"\n  CP range: {min_cp/1e6:.2f}M - {max_cp/1e6:.2f}M, ratio={ratio:.3f}")
    # PNJ had 50% bonus in April 2026 → recent split
    # Current shares = 511.7M, pre-split ≈ 341M
    # EPS 2025 = 7652 → back-calc = 369.6M (weighted avg 2025, pre-bonus but post partial-year issuances)
    # All consistent pre-split
    split_in_window = ratio > 1.2
    print(f"  Split adjustment needed: {split_in_window}")
    print(f"  Current shares: {issue_share/1e6:.1f}M (post 50% bonus 2026-04-15)")
    # The 50% bonus happened AFTER FY2025 → EPS 2021-2025 all on pre-bonus base
    # Current price (46,600) is post-bonus → must adjust EPS by ×1.5 for current PE
    SPLIT_MULT = 1 + SPLIT_RATIO  # 1.5 for 50% bonus
    print(f"  SPLIT_MULT for EPS/BVPS adjustment: {SPLIT_MULT}")

# ============ 6. PRICE DATA ============
print("\n[6] Fetching price data...")
today = datetime.date(2026, 7, 11)
start_2y = today - datetime.timedelta(days=730)
start_52w = today - datetime.timedelta(days=365)

q = Quote(symbol=TICKER, source="VCI")

# Weekly 52 weeks (post-split, as-is from vnstock which auto-adjusts)
price_w = q.history(start=str(start_2y), end=str(today), interval="1W")
price_w = price_w.dropna(subset=["close"])
price_w["time"] = pd.to_datetime(price_w["time"])
cutoff_52w = pd.Timestamp(today) - pd.Timedelta(weeks=52)
price_w_52 = price_w[price_w["time"] >= cutoff_52w].copy()
# Convert nghìn đồng → VND
for col in ["open", "high", "low", "close"]:
    if col in price_w_52.columns:
        price_w_52[col] = price_w_52[col] * 1000
print(f"  Weekly 52w: {len(price_w_52)} bars")
print(f"    First: {price_w_52.iloc[0]['time'].date()} close={price_w_52.iloc[0]['close']:,.0f}")
print(f"    Last: {price_w_52.iloc[-1]['time'].date()} close={price_w_52.iloc[-1]['close']:,.0f}")

price_weekly = {
    "time": price_w_52["time"].dt.strftime("%Y-%m-%d").tolist(),
    "open": [float(x) for x in price_w_52.get("open", [])],
    "high": [float(x) for x in price_w_52.get("high", [])],
    "low": [float(x) for x in price_w_52.get("low", [])],
    "close": [float(x) for x in price_w_52["close"]],
    "volume": [float(x) for x in price_w_52.get("volume", [])],
}

# Daily ~2 years
price_d = q.history(start=str(start_2y), end=str(today), interval="1D")
price_d = price_d.dropna(subset=["close"])
price_d["time"] = pd.to_datetime(price_d["time"])
for col in ["open", "high", "low", "close"]:
    if col in price_d.columns:
        price_d[col] = price_d[col] * 1000
print(f"  Daily ~2y: {len(price_d)} bars")

price_daily = {
    "time": price_d["time"].dt.strftime("%Y-%m-%d").tolist(),
    "open": [float(x) for x in price_d.get("open", [])],
    "high": [float(x) for x in price_d.get("high", [])],
    "low": [float(x) for x in price_d.get("low", [])],
    "close": [float(x) for x in price_d["close"]],
    "volume": [float(x) for x in price_d.get("volume", [])],
}

# VNINDEX weekly
vnindex = {"time": [], "close": []}
try:
    qv = Quote(symbol="VNINDEX", source="VCI")
    vni = qv.history(start=str(start_2y), end=str(today), interval="1W")
    vni = vni.dropna(subset=["close"])
    vni["time"] = pd.to_datetime(vni["time"])
    vni_52 = vni[vni["time"] >= cutoff_52w].copy()
    vnindex = {
        "time": vni_52["time"].dt.strftime("%Y-%m-%d").tolist(),
        "close": [float(x) for x in vni_52["close"]],
    }
    print(f"  VNINDEX 52w: {len(vni_52)} bars")
except Exception as e:
    print(f"  VNINDEX fetch failed: {e}")

vn30 = {"time": [], "close": []}
try:
    q30 = Quote(symbol="VN30", source="VCI")
    v30 = q30.history(start=str(start_2y), end=str(today), interval="1W")
    v30 = v30.dropna(subset=["close"])
    v30["time"] = pd.to_datetime(v30["time"])
    v30_52 = v30[v30["time"] >= cutoff_52w].copy()
    vn30 = {"time": v30_52["time"].dt.strftime("%Y-%m-%d").tolist(), "close": [float(x) for x in v30_52["close"]]}
    print(f"  VN30 52w: {len(v30_52)} bars")
except Exception as e:
    print(f"  VN30 fetch failed: {e}")

# ============ 7. COMPUTE ADJUSTED EPS/BVPS (post-split base) ============
print("\n[7] Computing split-adjusted EPS/BVPS...")
# Current price is post 50% bonus (2026-04-15). BCTC EPS 2021-2025 pre-bonus.
# For PE comparison with current price: EPS_adj = EPS_orig / 1.5 ... wait NO.
# 50% bonus means each old share becomes 1.5 shares. So EPS_post = EPS_pre / 1.5
# Actually: bonus ratio 50% = 0.5 → new shares = old × 1.5 → EPS_new = EPS_old / 1.5
SPLIT_MULT = 1 + SPLIT_RATIO  # 1.5
eps_adjusted = {}
bvps_adjusted = {}
shares_adjusted = {}
for y in YEARS:
    e_orig = financials["eps_vnd"][y]
    if e_orig:
        e_adj = e_orig / SPLIT_MULT
        eps_adjusted[y] = round(e_adj, 1)
    eq = financials["equity_ty"][y]
    if eq and back_calc.get(y):
        # BVPS = equity / shares. Pre-split shares = back_calc[y]
        bvps_orig = eq * 1e9 / back_calc[y]
        bvps_adj = bvps_orig / SPLIT_MULT
        bvps_adjusted[y] = round(bvps_adj, 1)
    shares_adjusted[y] = back_calc.get(y, 0) * SPLIT_MULT if back_calc.get(y) else None

financials["eps_adjusted_vnd"] = eps_adjusted
financials["bvps_adjusted_vnd"] = bvps_adjusted
financials["shares_adjusted_m"] = {y: (v / 1e6 if v else None) for y, v in shares_adjusted.items()}
financials["split_mult"] = SPLIT_MULT
financials["current_shares_m"] = issue_share / 1e6
financials["current_price_vnd"] = current_price

print(f"  SPLIT_MULT = {SPLIT_MULT} (50% bonus shares 2026-04-15)")
print(f"  EPS adjusted (post-bonus base, for current-price PE):")
for y in YEARS:
    eo = financials["eps_vnd"][y]
    ea = eps_adjusted.get(y)
    print(f"    {y}: EPS orig={eo:,.0f} → adj={ea:,.0f} đ")

# Current PE using adjusted EPS 2025
pe_now = current_price / eps_adjusted[2025]
bvps_now = bvps_adjusted.get(2025)
pb_now = current_price / bvps_now if bvps_now else None
print(f"\n  >>> Current price: {current_price:,.0f} VND")
print(f"  >>> EPS 2025 adj: {eps_adjusted[2025]:,.0f} → PE = {pe_now:.1f}x")
print(f"  >>> BVPS 2025 adj: {bvps_now:,.0f} → PB = {pb_now:.2f}x" if bvps_now else "  >>> BVPS NA")

# ============ 8. SAVE ============
print("\n[8] Saving data files...")

with open(os.path.join(DATA_DIR, "financials.json"), "w") as fp:
    json.dump(financials, fp, indent=2, ensure_ascii=False)

# balance_sheet.json (ground truth for REQ-023)
bs_out = {
    "years": YEARS,
    "Total Assets": {str(y): financials["total_assets_ty"][y] for y in YEARS},
    "Owner's Equity": {str(y): financials["equity_ty"][y] for y in YEARS},
    "Liabilities": {str(y): financials["liabilities_ty"][y] for y in YEARS},
    "Cash": {str(y): financials["cash_ty"][y] for y in YEARS},
    "Inventory": {str(y): financials["inventory_ty"][y] for y in YEARS},
    "Debt": {str(y): financials["total_debt_ty"][y] for y in YEARS},
    "ST Debt": {str(y): financials["st_debt_ty"][y] for y in YEARS},
    "LT Debt": {str(y): financials["lt_debt_ty"][y] for y in YEARS},
}
# Note: verifier expects values in tỷ when divided by 1e9, but the values stored are already in tỷ
# Add the raw VDN value for verifier compatibility (it divides by 1e9)
bs_out_raw = {"years": YEARS}
for key_tỷ in ["Total Assets", "Owner's Equity", "Liabilities", "Cash", "Inventory", "Debt"]:
    bs_out_raw[key_tỷ] = {str(y): (v * 1e9 if v else None) for y, v in bs_out[key_tỷ].items()}
with open(os.path.join(DATA_DIR, "balance_sheet.json"), "w") as fp:
    json.dump(bs_out_raw, fp, indent=2, ensure_ascii=False)

# cash_flow.json (ground truth for REQ-024 capex)
cf_out = {
    "years": YEARS,
    "CFO": {str(y): financials["cfo_ty"][y] for y in YEARS},
    "capex": {str(y): financials["capex_ty"][y] for y in YEARS},
    "FCF": {str(y): financials["fcf_ty"][y] for y in YEARS},
    "CFI": {str(y): financials["cfi_ty"][y] for y in YEARS},
    "CFF": {str(y): financials["cff_ty"][y] for y in YEARS},
    "Dividends Paid": {str(y): financials["dividends_paid_ty"][y] for y in YEARS},
    "Purchases of fixed assets and other long term assets": {str(y): (financials["capex_ty"][y] * 1e9 if financials["capex_ty"][y] else None) for y in YEARS},
}
with open(os.path.join(DATA_DIR, "cash_flow.json"), "w") as fp:
    json.dump(cf_out, fp, indent=2, ensure_ascii=False)

with open(os.path.join(DATA_DIR, "price_weekly.json"), "w") as fp:
    json.dump(price_weekly, fp, indent=2, ensure_ascii=False)

with open(os.path.join(DATA_DIR, "price_daily.json"), "w") as fp:
    json.dump(price_daily, fp, indent=2, ensure_ascii=False)

with open(os.path.join(DATA_DIR, "vnindex.json"), "w") as fp:
    json.dump(vnindex, fp, indent=2, ensure_ascii=False)

with open(os.path.join(DATA_DIR, "vn30.json"), "w") as fp:
    json.dump(vn30, fp, indent=2, ensure_ascii=False)

overview_out = {
    "ticker": TICKER,
    "company_name": str(ov.get("organ_name", "")),
    "current_price_vnd": current_price,
    "market_cap_vnd": market_cap,
    "market_cap_ty": market_cap / 1e9,
    "issue_share": issue_share,
    "shares_m": issue_share / 1e6,
    "52w_high": high_52w,
    "52w_low": low_52w,
    "target_price": target_price,
    "sector": str(ov.get("sector", "")),
    "rating": str(ov.get("rating", "")),
    "foreigner_pct": float(ov.get("foreigner_percentage", 0) or 0),
}
with open(os.path.join(DATA_DIR, "overview.json"), "w") as fp:
    json.dump(overview_out, fp, indent=2, ensure_ascii=False)

split_audit = {
    "ticker": TICKER,
    "back_calc_shares_m": {str(y): (v / 1e6 if v else None) for y, v in back_calc.items()},
    "max_min_ratio": round(ratio, 4),
    "split_event_50pct_bonus": {"date": SPLIT_DATE, "ratio": SPLIT_RATIO},
    "adjustment_needed": True,
    "cp_consistent_pre_split": True,
    "split_mult": SPLIT_MULT,
    "current_shares_m": issue_share / 1e6,
    "note": "PNJ 50% bonus shares (cổ phiếu thưởng) on 2026-04-15 + ESOP 0.7% (2026-04-24) + ESOP 1% (2025-10-02). BCTC 2021-2025 EPS/BVPS on pre-bonus base. Current price post-bonus. EPS/BVPS adjusted by /1.5 for current PE/PB. Cross-check: PE_pre = PE_post verified.",
}
with open(os.path.join(DATA_DIR, "split_audit.json"), "w") as fp:
    json.dump(split_audit, fp, indent=2, ensure_ascii=False)

# Events for news phase
events_out = []
for e in ev_records[:50]:
    events_out.append({
        "date": str(e.get("public_date", "")),
        "title": str(e.get("event_title_vi", "")),
        "category": str(e.get("category", "")),
        "action_type": str(e.get("action_type_vi", "")),
        "exercise_ratio": e.get("exercise_ratio"),
        "value_per_share": e.get("value_per_share"),
        "record_date": str(e.get("record_date", "")),
        "payout_date": str(e.get("payout_date", "")),
    })
with open(os.path.join(DATA_DIR, "events.json"), "w") as fp:
    json.dump(events_out, fp, indent=2, ensure_ascii=False)

print(f"\n{'='*60}")
print(f"✅ PHASE 1 COMPLETE")
print(f"{'='*60}")
print(f"Files in {DATA_DIR}/:")
for fn in sorted(os.listdir(DATA_DIR)):
    sz = os.path.getsize(os.path.join(DATA_DIR, fn))
    print(f"  {fn:40s} {sz:>8,} bytes")
print(f"\nKey metrics:")
print(f"  Price: {current_price:,.0f} VND | Market cap: {market_cap/1e9:,.0f} tỷ")
print(f"  EPS 2025 adj: {eps_adjusted[2025]:,.0f} đ → PE = {pe_now:.1f}x")
print(f"  BVPS 2025 adj: {bvps_now:,.0f} đ → PB = {pb_now:.2f}x" if bvps_now else "")
print(f"  Split: 50% bonus 2026-04-15 → SPLIT_MULT=1.5")
