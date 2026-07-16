#!/usr/bin/env python3
"""CTD Bước 2+3: Fundamental analysis + valuation. Tự tính từ BCTC (ratios stale)."""
import pandas as pd
import numpy as np
import json

DATA = '/Users/bobo/ZCodeProject/ctd_data'
inc = pd.read_csv(f'{DATA}/income_statement.csv')
bal = pd.read_csv(f'{DATA}/balance_sheet.csv')
cf = pd.read_csv(f'{DATA}/cash_flow.csv')
ov = json.load(open(f'{DATA}/overview.json'))

# Column map: 2026-Q1, 2025-Q4, 2025-Q3, 2025-Q2, 2025-Q1, 2024-Q4, 2024-Q3, 2024-Q2
# Strategy: build full-year 2024 and 2025 from Q4 (annual snapshot, cumulative).
# vnstock income_statement is CUMULATIVE within year, so Q4 col = full year.
cols = list(inc.columns)
print("Income cols:", cols[3:])

def get_row(df, item_contains, prefer_col=None):
    mask = df['item'].astype(str).str.contains(item_contains, case=False, na=False, regex=False)
    if not mask.any(): return None
    row = df[mask].iloc[0]
    return row

def yr(df, item, col):
    r = get_row(df, item)
    if r is None: return None
    v = r[col]
    try: return float(v)
    except: return None

# ===== FULL YEAR 2024 + 2025 (Q4 col = cumulative annual) =====
items_inc = {
    'revenue': 'Doanh thu thuần',
    'gross_profit': 'Lợi nhuận gộp',
    'interest_expense': 'Chi phí lãi vay',
    'operating_profit': 'Lãi/(lỗ) từ hoạt động kinh doanh',
    'pretax_profit': 'Lãi/(lỗ) trước thuế',
    'net_profit': 'Lợi nhuận của Cổ đông của Công ty mẹ',
    'eps_vnd': 'Lãi cơ bản trên cổ phiếu (VND)',
}
fy = {}
for yr_col, label in [('2024-Q4','FY2024'), ('2025-Q4','FY2025')]:
    fy[label] = {}
    for k, item in items_inc.items():
        fy[label][k] = yr(inc, item, yr_col)

# Balance sheet (point-in-time, so Q4 = year-end snapshot)
items_bal = {
    'total_assets': 'TỔNG CỘNG TÀI SẢN',
    'current_assets': 'TÀI SẢN NGẮN HẠN',
    'equity': 'VỐN CHỦ SỞ HỮU',
    'total_liabilities': 'NỢ PHẢI TRẢ',
}
for yr_col, label in [('2024-Q4','FY2024'), ('2025-Q4','FY2025')]:
    for k, item in items_bal.items():
        fy[label][k] = yr(bal, item, yr_col)

# Cash flow — try multiple item name variants
def yr_cf(item, col):
    r = get_row(cf, item)
    if r is None: return None
    try: return float(r[col])
    except: return None

for col, label in [('2024-Q4','FY2024'),('2025-Q4','FY2025')]:
    cfo = None
    for item in ['Lưu chuyển tiền tệ ròng từ các hoạt động sản xuất kinh doanh',
                 'Lưu chuyển tiền thuần từ hoạt động kinh doanh','Lợi nhuận HĐKD']:
        cfo = yr_cf(item, col)
        if cfo: break
    fy[label]['cfo'] = cfo
fy['FY2024']['capex'] = yr(cf, 'Tiền chi ra để mua sắm, xây dựng TSCĐ', '2024-Q4')
fy['FY2025']['capex'] = yr(cf, 'Tiền chi ra để mua sắm, xây dựng TSCĐ', '2025-Q4')

print("\n=== FY2024 vs FY2025 ===")
for k in ['revenue','gross_profit','operating_profit','net_profit','eps_vnd','equity','total_assets','cfo']:
    v24, v25 = fy['FY2024'].get(k), fy['FY2025'].get(k)
    if v24 and v25:
        chg = (v25/v24 - 1)*100 if v24 else None
        print(f"  {k}: {v24:,.0f} → {v25:,.0f} ({chg:+.1f}%)")
    else:
        print(f"  {k}: {v24} → {v25}")

# ===== RATIOS (tự tính) =====
price = float(ov['current_price'])  # 71700
shares = float(ov['issue_share'])   # from overview
mcap = float(ov['market_cap'])
print(f"\nPrice={price:,.0f}, Shares={shares:,.0f}, Mcap={mcap/1e12:.2f}T")

ratios_calc = {}
for label in ['FY2024','FY2025']:
    d = fy[label]
    eq = d.get('equity'); ni = d.get('net_profit'); rev = d.get('revenue')
    ta = d.get('total_assets'); gp = d.get('gross_profit')
    # EPS: dùng BCTC trực tiếp (weighted-average shares), KHÔNG tự tính (sai lệch weighted)
    eps_bctc = d.get('eps_vnd')
    ratios_calc[label] = {
        'EPS': eps_bctc,
        'BVPS': eq / shares if eq and shares else None,  # equity(đồng) / shares(units)
        'ROE': ni / eq * 100 if ni and eq else None,
        'ROA': ni / ta * 100 if ni and ta else None,
        'ROS': ni / rev * 100 if ni and rev else None,
        'gross_margin': gp / rev * 100 if gp and rev else None,
    }
    # P/E P/B based on current price
    eps = ratios_calc[label]['EPS']; bvps = ratios_calc[label]['BVPS']
    ratios_calc[label]['PE'] = price / eps if eps else None
    ratios_calc[label]['PB'] = price / bvps if bvps else None

print("\n=== Ratios tự tính ===")
for label in ['FY2024','FY2025']:
    print(f"  {label}:")
    for k,v in ratios_calc[label].items():
        print(f"    {k}: {v:.2f}" if v else f"    {k}: None")

# ===== DuPONT =====
print("\n=== DuPont FY2025 ===")
d = fy['FY2025']
ni, eq, rev, ta = d.get('net_profit'), d.get('equity'), d.get('revenue'), d.get('total_assets')
liab = d.get('total_liabilities')
if all([ni,eq,rev,ta]):
    npm = ni/rev; ta_turn = rev/ta; eq_mult = ta/eq
    roe_dupont = npm * ta_turn * eq_mult * 100
    print(f"  NPM (biên LN): {npm*100:.2f}%")
    print(f"  TÀI SẢN vòng quay: {ta_turn:.2f}x")
    print(f"  Đòn bẩy (TA/EQ): {eq_mult:.2f}x")
    print(f"  ROE DuPont: {roe_dupont:.2f}% (verify vs direct {ni/eq*100:.2f}%)")

# ===== VALUATION =====
print("\n=== VALUATION (9 PP hội tụ) ===")
eps25 = ratios_calc['FY2025']['EPS']; eps24 = ratios_calc['FY2024']['EPS']
bvps25 = ratios_calc['FY2025']['BVPS']; bvps24 = ratios_calc['FY2024']['BVPS']
cfo25 = fy['FY2025'].get('cfo'); rev25 = fy['FY2025'].get('revenue')
val = {}
# PE median (2 năm vì chỉ có data 2 năm)
val['PE_FY2025'] = price/eps25 if eps25 else None
val['PB_FY2025'] = price/bvps25 if bvps25 else None
val['PCF'] = (mcap / cfo25) if cfo25 else None  # cả 2 cùng đơn vị đồng
val['PS'] = mcap / rev25 if rev25 else None
# Graham: V = sqrt(22.5 * EPS * BVPS)
val['Graham'] = (22.5 * eps25 * bvps25)**0.5 if eps25 and bvps25 else None
print(f"  PE (FY25): {val['PE_FY2025']:.2f}x")
print(f"  PB (FY25): {val['PB_FY2025']:.2f}x")
print(f"  P/CF: {val['PCF']:.2f}x (mcap/CFO)" if val.get('PCF') else "  P/CF: None (CFO missing)")
print(f"  P/S: {val['PS']:.2f}x" if val.get('PS') else "  P/S: None")
print(f"  Graham (sqrt(22.5*EPS*BVPS)): {val['Graham']:,.0f} VND" if val.get('Graham') else "  Graham: None")

# DCF simplified (3 scenarios) — use FY25 net profit as FCF proxy, perpetuity
g_scen = {'bearish': 0.0, 'base': 0.05, 'bullish': 0.10}
disc = 0.12  # WACC proxy cho VN (xem wacc_estimates.md)
fcf0 = ni  # proxy FCF = NI (xấu nhưng thiếu data chi tiết)
for scn, g in g_scen.items():
    if g < disc:
        dcf_val = fcf0 * (1+g) / (disc - g)
        val[f'DCF_{scn}'] = dcf_val
        val[f'DCF_per_share_{scn}'] = dcf_val / shares
        print(f"  DCF {scn} (g={g:.0%}, WACC={disc:.0%}): firm {dcf_val/1e9:,.0f}B → {val[f'DCF_per_share_{scn}']:,.0f} VND/sh")

# Save
out = {
    'ticker': 'CTD',
    'price': price,
    'shares': shares,
    'market_cap': mcap,
    'financials': fy,
    'ratios': ratios_calc,
    'valuation': val,
    'data_caveat': 'BCTC community edition: chỉ 8 kỳ (2024-Q2 → 2026-Q1). Full-year chỉ có FY2024+FY2025. Ratios vnstock stale (2018). Tự tính.',
}
with open(f'{DATA}/fundamental_valuation.json','w') as f:
    json.dump(out, f, ensure_ascii=False, indent=2, default=str)
print(f"\nSaved {DATA}/fundamental_valuation.json")
