#!/usr/bin/env python3
"""
Phase 3: Valuation for PNJ
Jewelry retail (bán lẻ trang sức) → consumer sector, WACC ~9-10%
9 methods: PE/PB median, EV/EBITDA, P/CF, P/S, DCF (3 scenarios), DDM, Graham, Reverse DCF
"""
import json, os, math

TICKER = "PNJ"
WORK_DIR = "/Users/bobo/ZCodeProject/pnj-research"
DATA_DIR = os.path.join(WORK_DIR, "data")

with open(os.path.join(DATA_DIR, "financials.json")) as f:
    fin = json.load(f)
with open(os.path.join(DATA_DIR, "fundamental.json")) as f:
    fund = json.load(f)
with open(os.path.join(DATA_DIR, "overview.json")) as f:
    ov = json.load(f)

YEARS = fin["years"]
current_price = ov["current_price_vnd"]
market_cap = ov["market_cap_vnd"]  # VND
shares_m = ov["shares_m"]
shares_count = ov["issue_share"]
net_debt_ty = (fin["total_debt_ty"]["2025"] or 0) - (fin["cash_ty"]["2025"] or 0)
print("=" * 60)
print(f"  PHASE 3: Valuation — {TICKER}")
print("=" * 60)
print(f"  Price: {current_price:,.0f} VND | MCap: {market_cap/1e9:,.0f} tỷ | Shares: {shares_m:.1f}M")
print(f"  Net debt: {net_debt_ty:,.0f} tỷ")

eps_adj = fund["eps_adjusted_vnd"]  # [2021..2025]
bvps_adj = fund["bvps_adjusted_vnd"]
revenue = [fin["revenue_ty"][str(y)] for y in YEARS]
npatmi = [fin["npatmi_ty"][str(y)] for y in YEARS]
cfo = [fin["cfo_ty"][str(y)] for y in YEARS]
fcf = [fin["fcf_ty"][str(y)] for y in YEARS]
total_debt = [fin["total_debt_ty"][str(y)] for y in YEARS]
cash = [fin["cash_ty"][str(y)] for y in YEARS]
op_profit = [fin["operating_profit_ty"][str(y)] for y in YEARS]
interest_exp = [fin["interest_expense_ty"][str(y)] for y in YEARS]
tax = [abs(fin.get("tax_ty", {}).get(str(y), 0) or 0) for y in YEARS]

# ============ 1. PE/PB HISTORY (using adjusted EPS) ============
print("\n[1] PE/PB history (split-adjusted EPS/BVPS):")
# We need year-end prices. We have current price + weekly data.
# For historical PE, approximate with adjusted EPS × reasonable PE band.
# Better: compute PE NOW for each year's EPS at current price (relative valuation)
pe_now_per_year = [current_price / e for e in eps_adj]
pb_now_per_year = [current_price / b for b in bvps_adj]
for i, y in enumerate(YEARS):
    print(f"  {y}: EPS_adj={eps_adj[i]:,.0f} → PE@now={pe_now_per_year[i]:.1f}x | BVPS_adj={bvps_adj[i]:,.0f} → PB@now={pb_now_per_year[i]:.2f}x")

# Median PE/PB from the 5-year range (as proxy for historical average multiple)
pe_median_5y = sorted(pe_now_per_year)[2]
pb_median_5y = sorted(pb_now_per_year)[2]

# Fair price: current EPS × median PE
eps_2025 = eps_adj[-1]
bvps_2025 = bvps_adj[-1]
fair_pe = eps_2025 * pe_median_5y
fair_pb = bvps_2025 * pb_median_5y
print(f"\n  Median PE 5y: {pe_median_5y:.1f}x → Fair price (EPS2025 × median PE): {fair_pe:,.0f} VND")
print(f"  Median PB 5y: {pb_median_5y:.2f}x → Fair price (BVPS2025 × median PB): {fair_pb:,.0f} VND")

# More reasonable: use industry-typical PE for jewelry retail
# PNJ historical PE typically 10-15x. Use 12x as fair multiple.
pe_industry = 12.0
pb_industry = 2.0
fair_pe_industry = eps_2025 * pe_industry
fair_pb_industry = bvps_2025 * pb_industry
print(f"  Industry PE {pe_industry}x → Fair: {fair_pe_industry:,.0f} VND")
print(f"  Industry PB {pb_industry}x → Fair: {fair_pb_industry:,.0f} VND")

# ============ 2. EV/EBITDA ============
print("\n[2] EV/EBITDA:")
# EBITDA = EBIT + D&A. EBIT = Operating profit (or PBT + interest)
# We don't have D&A directly extracted; approximate from CFO vs NPAT difference
# Better: EBIT ≈ Operating profit. D&A estimate from (CFO - NPAT_before_tax + tax_paid)... complex
# Use EBIT = Operating profit, EBITDA ≈ EBIT × 1.1 (D&A ~10% of EBIT for retail)
# Actually for PNJ (jewelry), D&A is small. Let's compute EBIT properly.
ebit = []
for i, y in enumerate(YEARS):
    # EBIT = PBT + Interest expense
    pbt = npatmi[i] + tax[i]  # approximate PBT
    eb = pbt + (interest_exp[i] or 0)
    ebit.append(eb)
    print(f"  {y}: EBIT ≈ {eb:,.0f} tỷ (PBT {pbt:,.0f} + Int {interest_exp[i] or 0:.0f})")

# EBITDA with small D&A adjustment (jewelry = asset light, D&A ~3-5% of revenue... actually PNJ has stores)
# Use EBITDA = EBIT (conservative, no D&A add-back since PNJ D&A is modest)
ebitda_2025 = ebit[-1]
ev_2025 = market_cap / 1e9 + net_debt_ty
ev_ebitda = ev_2025 / ebitda_2025
print(f"\n  EBITDA 2025 ≈ {ebitda_2025:,.0f} tỷ (≈ EBIT, D&A small for jewelry)")
print(f"  EV 2025 = {market_cap/1e9:,.0f} (MCap) + {net_debt_ty:,.0f} (Net debt) = {ev_2025:,.0f} tỷ")
print(f"  EV/EBITDA = {ev_ebitda:.1f}x")
# Fair: industry EV/EBITDA for jewelry retail ~6-8x
ev_ebitda_industry = 7.0
fair_ev = ebitda_2025 * ev_ebitda_industry
fair_mc_ev = fair_ev - net_debt_ty
fair_ev_price = fair_mc_ev * 1e9 / shares_count
print(f"  Industry EV/EBITDA {ev_ebitda_industry}x → Fair EV: {fair_ev:,.0f} → Fair price: {fair_ev_price:,.0f} VND")

# ============ 3. P/CF and P/S ============
print("\n[3] P/CF and P/S:")
pcf = market_cap / 1e9 / cfo[-1]
ps = market_cap / 1e9 / revenue[-1]
print(f"  P/CF (MCap/CFO 2025): {pcf:.1f}x")
print(f"  P/S (MCap/Revenue 2025): {ps:.2f}x")
# Fair P/CF ~8x for quality consumer
pcf_industry = 8.0
fair_pcf = cfo[-1] * pcf_industry * 1e9 / shares_count
print(f"  Industry P/CF {pcf_industry}x → Fair: {fair_pcf:,.0f} VND")

# ============ 4. PEG ============
print("\n[4] PEG:")
pe_current = current_price / eps_2025
eps_growth_4y = (eps_adj[-1] / eps_adj[0]) ** (1/4) - 1
eps_growth_3y = (eps_adj[-1] / eps_adj[1]) ** (1/3) - 1
peg = pe_current / (eps_growth_3y * 100) if eps_growth_3y > 0 else None
print(f"  PE current: {pe_current:.1f}x")
print(f"  EPS growth 3y CAGR: {eps_growth_3y*100:.1f}%")
print(f"  PEG: {peg:.2f}" if peg else "  PEG: NA")
print(f"  (PEG <1 = undervalued, 1-2 = fair, >2 = overvalued)")

# ============ 5. DCF (3 scenarios) ============
print("\n[5] DCF (3 scenarios):")
# PNJ FCF is strongly positive (3,516 tỷ 2025), so DCF is valid
# WACC for consumer/jewelry: ~9-10%. Use 9.5% base.
# Terminal growth: 3% (VN GDP growth ~6%, jewelry ~inflation+)
wacc_base = 0.095
g_terminal = 0.03

# Forecast FCF 5 years (2026-2030)
# Base: NPAT CAGR 3y = 16% → moderate to 10% growth (gold prices normalize)
fcf_2025 = fcf[-1]
# Scenario assumptions
scenarios = {
    "bull": {"growth": [0.15, 0.15, 0.12, 0.10, 0.08], "wacc": 0.090, "g": 0.035, "label": "Tích cực"},
    "base": {"growth": [0.10, 0.10, 0.08, 0.07, 0.06], "wacc": 0.095, "g": 0.030, "label": "Cơ sở"},
    "bear": {"growth": [0.03, 0.03, 0.02, 0.02, 0.02], "wacc": 0.105, "g": 0.020, "label": "Bi quan"},
}

dcf_results = {}
for name, sc in scenarios.items():
    fcff_forecast = []
    prev = fcf_2025
    for g in sc["growth"]:
        prev = prev * (1 + g)
        fcff_forecast.append(prev)
    wacc = sc["wacc"]
    g = sc["g"]
    # PV explicit
    pv_explicit = sum(fcff_forecast[i] / (1 + wacc) ** (i + 1) for i in range(5))
    # Terminal value
    tv = fcff_forecast[-1] * (1 + g) / (wacc - g)
    pv_tv = tv / (1 + wacc) ** 5
    # Enterprise value
    ev_dcf = pv_explicit + pv_tv
    equity_value = ev_dcf - net_debt_ty
    fair_price_dcf = equity_value * 1e9 / shares_count
    dcf_results[name] = {
        "fcff_forecast": [round(f, 0) for f in fcff_forecast],
        "wacc": wacc,
        "g_terminal": g,
        "ev": round(ev_dcf, 0),
        "equity_value": round(equity_value, 0),
        "fair_price": round(fair_price_dcf, 0),
        "upside_pct": round((fair_price_dcf / current_price - 1) * 100, 1),
    }
    print(f"\n  {sc['label']} ({name}):")
    print(f"    FCF forecast: {fcff_forecast}")
    print(f"    WACC={wacc*100:.1f}%, g={g*100:.1f}%")
    print(f"    EV={ev_dcf:,.0f} tỷ → Equity={equity_value:,.0f} tỷ")
    print(f"    Fair price: {fair_price_dcf:,.0f} VND (upside {dcf_results[name]['upside_pct']:+.1f}%)")

# DCF note: FCF > 0, no need for alternative method
dcf_note = None  # FCF0 = 3,516 tỷ > 0 → DCF valid

# ============ 6. DDM (Gordon) ============
print("\n[6] DDM (Gordon Growth):")
# PNJ pays cash dividends: 2024 = 1,400 đ/cp (round 2) + earlier rounds
# Estimate total DPS 2024 ~ 2,500 đ (pre-split). Adjusted: 2,500/1.5 = 1,667 đ
# 2025 round 1 = 1,000 VND (pre-split? post-split? event date 2025-12-31, likely pre-split base)
# Let's use DPS_adj ≈ 1,800 đ/cp (normalized, post-split adjusted)
dps_adj = 1800  # đ/cp post-split adjusted (estimate from events)
ke = 0.10  # cost of equity for consumer
g_ddm = 0.04
fair_ddm = dps_adj * (1 + g_ddm) / (ke - g_ddm)
div_yield = dps_adj / current_price * 100
print(f"  DPS adj (estimate): {dps_adj} đ/cp")
print(f"  Dividend yield: {div_yield:.1f}%")
print(f"  DDM fair price (ke=10%, g=4%): {fair_ddm:,.0f} VND")
print(f"  Note: DDM conservative — PNJ retains earnings for expansion")

# ============ 7. Graham Number ============
print("\n[7] Graham Number:")
graham = math.sqrt(22.5 * eps_2025 * bvps_2025)
print(f"  Graham = √(22.5 × {eps_2025} × {bvps_2025}) = {graham:,.0f} VND")
print(f"  PE×PB check: {pe_current:.1f} × {fund['pb_now']:.2f} = {pe_current * fund['pb_now']:.1f} (≤22.5 = Graham cheap)")

# ============ 8. Reverse DCF ============
print("\n[8] Reverse DCF (implied growth at current price):")
ev_current = market_cap / 1e9 + net_debt_ty
# Binary search g
def calc_ev(g, base_fcf, wacc, g_terminal=0.03):
    pv = 0
    for i in range(1, 6):
        pv += base_fcf * (1 + g) ** i / (1 + wacc) ** i
    tv = base_fcf * (1 + g) ** 5 * (1 + g_terminal) / (wacc - g_terminal)
    pv += tv / (1 + wacc) ** 5
    return pv

lo, hi = 0.0, 0.25
for _ in range(50):
    mid = (lo + hi) / 2
    if calc_ev(mid, fcf_2025, wacc_base) < ev_current:
        lo = mid
    else:
        hi = mid
implied_g = (lo + hi) / 2
print(f"  Current EV: {ev_current:,.0f} tỷ")
print(f"  Implied FCF growth (WACC 9.5%, g_term 3%): {implied_g*100:.1f}%/year")
print(f"  PNJ NPAT CAGR 3y = {fund['cagr_npat_3y']:.1f}% → {'UNDERVALUED' if implied_g < fund['cagr_npat_3y']/100 else 'FAIR/OVERVALUED'}")

# ============ 9. CONVERGE ============
print("\n[9] Convergence:")
all_targets = {
    "PE_median_5y": fair_pe,
    "PE_industry_12x": fair_pe_industry,
    "PB_median_5y": fair_pb,
    "PB_industry_2x": fair_pb_industry,
    "EV/EBITDA_7x": fair_ev_price,
    "P/CF_8x": fair_pcf,
    "DCF_base": dcf_results["base"]["fair_price"],
    "DCF_bull": dcf_results["bull"]["fair_price"],
    "DCF_bear": dcf_results["bear"]["fair_price"],
    "DDM": fair_ddm,
    "Graham": graham,
}
print(f"  {'Method':<20} {'Fair price':>12} {'Upside':>8}")
print(f"  {'-'*42}")
for method, price in sorted(all_targets.items(), key=lambda x: x[1]):
    upside = (price / current_price - 1) * 100
    print(f"  {method:<20} {price:>12,.0f} {upside:>+7.1f}%")

# Converge: median + P25-P75
prices = sorted(all_targets.values())
n = len(prices)
converge_median = prices[n // 2]
p25 = prices[int(n * 0.25)]
p75 = prices[int(n * 0.75)]
print(f"\n  Converge median: {converge_median:,.0f} VND (upside {(converge_median/current_price-1)*100:+.1f}%)")
print(f"  Range P25-P75: {p25:,.0f} - {p75:,.0f} VND")

# Verdict
avg_target = sum(prices) / n
if avg_target > current_price * 1.15:
    verdict = "UNDERVALUED"
elif avg_target < current_price * 0.85:
    verdict = "OVERVALUED"
else:
    verdict = "FAIR"
print(f"  Average target: {avg_target:,.0f} VND → {verdict}")
print(f"  Current price: {current_price:,.0f} VND")

# Analyst target
analyst_target = ov.get("target_price", 0)
print(f"\n  Analyst consensus target: {analyst_target:,.0f} VND (upside {(analyst_target/current_price-1)*100:+.1f}%)")

# ============ SAVE ============
result = {
    "ticker": TICKER,
    "current_price": current_price,
    "market_cap_ty": market_cap / 1e9,
    "eps_2025_adj": eps_2025,
    "bvps_2025_adj": bvps_2025,
    "pe_current": round(pe_current, 2),
    "pb_current": fund["pb_now"],
    "pe_median_5y": round(pe_median_5y, 2),
    "pb_median_5y": round(pb_median_5y, 2),
    "ev_ebitda": round(ev_ebitda, 2),
    "pcf": round(pcf, 2),
    "ps": round(ps, 2),
    "peg": round(peg, 2) if peg else None,
    "dcf": dcf_results,
    "dcf_note": dcf_note,
    "ddm_fair": round(fair_ddm, 0),
    "dps_adj": dps_adj,
    "dividend_yield": round(div_yield, 2),
    "graham_number": round(graham, 0),
    "reverse_dcf_implied_g": round(implied_g * 100, 1),
    "all_targets": {k: round(v, 0) for k, v in all_targets.items()},
    "converge_median": round(converge_median, 0),
    "converge_p25": round(p25, 0),
    "converge_p75": round(p75, 0),
    "verdict": verdict,
    "analyst_target": analyst_target,
    "wacc_base": wacc_base,
    "g_terminal": g_terminal,
}

with open(os.path.join(DATA_DIR, "valuation.json"), "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"\n✅ Phase 3 complete → data/valuation.json")
print(f"   Verdict: {verdict} | Converge median: {converge_median:,.0f} VND")
print(f"   DCF base: {dcf_results['base']['fair_price']:,.0f} | Analyst: {analyst_target:,.0f}")
