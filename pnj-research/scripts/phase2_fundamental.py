#!/usr/bin/env python3
"""
Phase 2: Fundamental Analysis — compute from raw financials (NOT trusting ratio())
- EPS, BVPS per year (split-adjusted)
- ROE, ROA, ROS, gross margin, net margin
- DuPont 3-component decomposition
- CAGR: revenue + NPAT (full period + recovery)
- Debt metrics: D/E, Net Debt/Equity, interest coverage
"""
import json, os

TICKER = "PNJ"
WORK_DIR = "/Users/bobo/ZCodeProject/pnj-research"
DATA_DIR = os.path.join(WORK_DIR, "data")

with open(os.path.join(DATA_DIR, "financials.json")) as f:
    fin = json.load(f)

YEARS = fin["years"]
SPLIT_MULT = fin.get("split_mult", 1.5)

def arr(key, y=YEARS):
    return [fin[key][str(yy)] for yy in y]

revenue = arr("revenue_ty")
gross_profit = arr("gross_profit_ty")
npatmi = arr("npatmi_ty")
eps_orig = arr("eps_vnd")
eps_adj = arr("eps_adjusted_vnd")
bvps_adj = arr("bvps_adjusted_vnd")
total_assets = arr("total_assets_ty")
equity = arr("equity_ty")
liabilities = arr("liabilities_ty")
inventory = arr("inventory_ty")
cash = arr("cash_ty")
st_debt = arr("st_debt_ty")
lt_debt = arr("lt_debt_ty")
total_debt = arr("total_debt_ty")
cfo = arr("cfo_ty")
capex = arr("capex_ty")
fcf = arr("fcf_ty")
op_profit = arr("operating_profit_ty")
interest_exp = arr("interest_expense_ty")
selling_exp = arr("selling_expense_ty")
ga_exp = arr("ga_expense_ty")

print("=" * 60)
print(f"  PHASE 2: Fundamental Analysis — {TICKER}")
print("=" * 60)

# ============ MARGINS ============
print("\n[1] Margins:")
gross_margin = []
net_margin = []
operating_margin = []
for i, y in enumerate(YEARS):
    gm = gross_profit[i] / revenue[i] * 100 if gross_profit[i] and revenue[i] else None
    nm = npatmi[i] / revenue[i] * 100 if npatmi[i] and revenue[i] else None
    om = op_profit[i] / revenue[i] * 100 if op_profit[i] and revenue[i] else None
    gross_margin.append(round(gm, 2) if gm else None)
    net_margin.append(round(nm, 2) if nm else None)
    operating_margin.append(round(om, 2) if om else None)
    print(f"  {y}: Gross={gm:.1f}% | OpMargin={om:.1f}% | NetMargin={nm:.1f}%")

# ============ ROE, ROA, ROS ============
print("\n[2] Returns:")
roe = []
roa = []
roic = []
for i, y in enumerate(YEARS):
    r = npatmi[i] / equity[i] * 100 if npatmi[i] and equity[i] else None
    a = npatmi[i] / total_assets[i] * 100 if npatmi[i] and total_assets[i] else None
    roe.append(round(r, 2) if r else None)
    roa.append(round(a, 2) if a else None)
    print(f"  {y}: ROE={r:.2f}% | ROA={a:.2f}%")

# ============ DUPONT 3-COMPONENT ============
print("\n[3] DuPont Decomposition (ROE = NPM × Asset Turnover × Equity Multiplier):")
dupont = []
for i, y in enumerate(YEARS):
    npm = npatmi[i] / revenue[i] if npatmi[i] and revenue[i] else None
    at = revenue[i] / total_assets[i] if revenue[i] and total_assets[i] else None
    em = total_assets[i] / equity[i] if total_assets[i] and equity[i] else None
    roe_check = npm * at * em if all(v is not None for v in [npm, at, em]) else None
    dup = {"year": y, "npm": round(npm * 100, 2) if npm else None,
           "asset_turnover": round(at, 3) if at else None,
           "equity_multiplier": round(em, 3) if em else None,
           "roe_check": round(roe_check * 100, 2) if roe_check else None}
    dupont.append(dup)
    print(f"  {y}: NPM={npm*100:.2f}% × AT={at:.3f} × EM={em:.3f} = ROE {roe_check*100:.2f}%")

# ============ CAGR ============
print("\n[4] CAGR:")
# 4-year CAGR (2021-2025)
n_years = 4
rev_cagr_4y = (revenue[-1] / revenue[0]) ** (1 / n_years) - 1
npat_cagr_4y = (npatmi[-1] / npatmi[0]) ** (1 / n_years) - 1
print(f"  Revenue CAGR (2021-2025, 4y): {rev_cagr_4y*100:.1f}%")
print(f"  NPATMI CAGR (2021-2025, 4y): {npat_cagr_4y*100:.1f}%")

# 3-year CAGR (2022-2025) — more normalized (skip COVID-recovery 2021)
rev_cagr_3y = (revenue[-1] / revenue[1]) ** (1 / 3) - 1
npat_cagr_3y = (npatmi[-1] / npatmi[1]) ** (1 / 3) - 1
print(f"  Revenue CAGR (2022-2025, 3y): {rev_cagr_3y*100:.1f}%")
print(f"  NPATMI CAGR (2022-2025, 3y): {npat_cagr_3y*100:.1f}%")

# ============ DEBT & COVERAGE ============
print("\n[5] Debt & Coverage:")
de_ratio = []
net_de_ratio = []
interest_cov = []
for i, y in enumerate(YEARS):
    de = total_debt[i] / equity[i] if total_debt[i] and equity[i] else None
    net_debt = total_debt[i] - (cash[i] or 0)
    nde = net_debt / equity[i] if equity[i] else None
    ic = op_profit[i] / interest_exp[i] if op_profit[i] and interest_exp[i] and interest_exp[i] > 0 else None
    de_ratio.append(round(de, 3) if de else None)
    net_de_ratio.append(round(nde, 3) if nde else None)
    interest_cov.append(round(ic, 1) if ic else None)
    print(f"  {y}: D/E={de:.2f} | NetD/E={nde:.2f} | IntCov={ic:.1f}x" if all(v for v in [de,nde,ic]) else f"  {y}: partial")

# ============ EFFICIENCY ============
print("\n[6] Efficiency:")
inv_turn = []
asset_turn = []
for i, y in enumerate(YEARS):
    it = revenue[i] / inventory[i] if revenue[i] and inventory[i] else None
    at = revenue[i] / total_assets[i] if revenue[i] and total_assets[i] else None
    inv_turn.append(round(it, 2) if it else None)
    asset_turn.append(round(at, 3) if at else None)
    print(f"  {y}: InvTurn={it:.2f}x | AssetTurn={at:.3f}x" if it and at else f"  {y}: partial")

# ============ CASH FLOW QUALITY ============
print("\n[7] Cash flow quality (CFO/NPAT — accrual quality):")
cfo_npat = []
for i, y in enumerate(YEARS):
    cn = cfo[i] / npatmi[i] if cfo[i] and npatmi[i] else None
    cfo_npat.append(round(cn, 2) if cn else None)
    print(f"  {y}: CFO/NPAT={cn:.2f}x (>1 = good cash quality)" if cn else f"  {y}: NA")

# ============ FCF per share (adjusted) ============
print("\n[8] FCF per share (split-adjusted):")
fcf_per_share = []
shares_adj = fin.get("shares_adjusted_m", {})
for i, y in enumerate(YEARS):
    sa = shares_adj.get(str(y))
    if sa and fcf[i]:
        fps = fcf[i] * 1e9 / (sa * 1e6)  # tỷ → đồng / shares
        fcf_per_share.append(round(fps, 0))
        print(f"  {y}: FCF={fcf[i]:,.0f} tỷ / {sa:.0f}M shares = {fps:,.0f} đ/share")
    else:
        fcf_per_share.append(None)

# ============ DIVIDEND YIELD (from events) ============
print("\n[9] Dividend info from events:")
with open(os.path.join(DATA_DIR, "events.json")) as f:
    events = json.load(f)
div_events = [e for e in events if "cổ tức" in e["title"].lower() and "tiền" in e["title"].lower()]
for e in div_events[:5]:
    print(f"  {e['date']} | {e['title']} | ratio={e.get('exercise_ratio')} | value={e.get('value_per_share')}")

# ============ SAVE ============
result = {
    "ticker": TICKER,
    "years": YEARS,
    "eps_orig_vnd": eps_orig,
    "eps_adjusted_vnd": eps_adj,
    "bvps_adjusted_vnd": bvps_adj,
    "gross_margin": gross_margin,
    "operating_margin": operating_margin,
    "net_margin": net_margin,
    "roe": roe,
    "roa": roa,
    "dupont": dupont,
    "cagr_revenue_4y": round(rev_cagr_4y * 100, 1),
    "cagr_npat_4y": round(npat_cagr_4y * 100, 1),
    "cagr_revenue_3y": round(rev_cagr_3y * 100, 1),
    "cagr_npat_3y": round(npat_cagr_3y * 100, 1),
    "de_ratio": de_ratio,
    "net_de_ratio": net_de_ratio,
    "interest_coverage": interest_cov,
    "inventory_turnover": inv_turn,
    "asset_turnover": asset_turn,
    "cfo_npat_ratio": cfo_npat,
    "fcf_per_share_adj_vnd": fcf_per_share,
    "current_price_vnd": fin["current_price_vnd"],
    "pe_now": round(fin["current_price_vnd"] / eps_adj[-1], 2),
    "pb_now": round(fin["current_price_vnd"] / bvps_adj[-1], 2),
}

with open(os.path.join(DATA_DIR, "fundamental.json"), "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"\n✅ Phase 2 complete → data/fundamental.json")
print(f"   Avg ROE 5y: {sum(v for v in roe if v)/len([v for v in roe if v]):.1f}%")
print(f"   Avg Net Margin 5y: {sum(v for v in net_margin if v)/len([v for v in net_margin if v]):.1f}%")
print(f"   NPAT CAGR 4y: {npat_cagr_4y*100:.1f}% | 3y: {npat_cagr_3y*100:.1f}%")
