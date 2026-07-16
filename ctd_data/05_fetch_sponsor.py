#!/usr/bin/env python3
"""CTD sponsor data fetch — dùng vnstock_data (golden tier) qua sponsor venv.
Fetch đầy đủ 5 năm BCTC + ratios + events + price. KHÔNG dùng community 8 kỳ."""
import sys, json, os
os.environ['VNSTOCK_NO_BANNER'] = '1'
import warnings; warnings.filterwarnings('ignore')

from vnstock_data import Finance, Company, Quote
import pandas as pd

TICKER = 'CTD'
OUT = '/Users/bobo/ZCodeProject/ctd_data'
os.makedirs(OUT, exist_ok=True)
# Clear old community data to avoid confusion
for f in os.listdir(OUT):
    if f.startswith('income_statement') or f.startswith('balance_sheet') or f.startswith('cash_flow') or f.startswith('ratios_sponsor'):
        os.remove(f'{OUT}/{f}')

def log(m): sys.stderr.write(m+"\n"); sys.stderr.flush()
def save_df(df, name): df.to_csv(f'{OUT}/{name}.csv', index=False); log(f"  saved {name}.csv ({df.shape})")
def save_json(obj, name):
    with open(f'{OUT}/{name}.json','w',encoding='utf-8') as f: json.dump(obj,f,ensure_ascii=False,indent=2,default=str)
    log(f"  saved {name}.json")

log(f"=== CTD SPONSOR FETCH (golden tier) ===")

# Finance — sponsor format: English HOA columns, report_period year/quarter
f = Finance(symbol=TICKER, source='VCI')
inc = f.income_statement(); save_df(inc, 'income_statement_sponsor')
bal = f.balance_sheet(); save_df(bal, 'balance_sheet_sponsor')
cf = f.cash_flow(); save_df(cf, 'cash_flow_sponsor')
try:
    ratios = f.ratio(); save_df(ratios, 'ratios_sponsor')
except Exception as e:
    log(f"  ratios ERR: {repr(e)[:150]}")

# Extract yearly data (report_period = 'year')
log("\n=== Extract yearly full-year data ===")
inc_yr = inc[inc['report_period']=='year'] if 'report_period' in inc.columns else inc
bal_yr = bal[bal['report_period']=='year'] if 'report_period' in bal.columns else bal
cf_yr = cf[cf['report_period']=='year'] if 'report_period' in cf.columns else cf
log(f"  income yearly rows: {len(inc_yr)}")
log(f"  balance yearly rows: {len(bal_yr)}")
log(f"  cashflow yearly rows: {len(cf_yr)}")

# Show available years
if 'ticker' in inc_yr.columns:
    yr_cols = [c for c in inc_yr.columns if c not in ['report_period','ticker']]
    log(f"  income columns (first 8): {yr_cols[:8]}")
    # Find year identifier — sponsor uses index as period
    log(f"  income index sample: {list(inc_yr.index[:6])}")

# Company + Quote — dùng community python3 (sponsor Company API bị KeyError).
# Price/news không phụ thuộc sponsor tier → community OK.
log("\n=== Company/Quote: dùng community (đã fetch ở 01_collect.py) ===")
log("  (overview.json, events.csv, news.csv, price_*.csv đã có từ 01_collect.py)")

log("\n=== DONE ===")
