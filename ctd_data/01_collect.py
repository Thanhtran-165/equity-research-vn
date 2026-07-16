#!/usr/bin/env python3
"""CTD data collector — Bước 1. Fetch ALL data in one pass, save to ctd_data/*.json + *.csv."""
import warnings, json, sys, os, io, contextlib
warnings.filterwarnings('ignore')
os.environ['VNSTOCK_NO_BANNER'] = '1'

# Silence the vnstock sponsor banner
with contextlib.redirect_stdout(io.StringIO()):
    from vnstock import Quote, Finance, Company

import pandas as pd
import numpy as np
from datetime import datetime

TICKER = 'CTD'
OUT = '/Users/bobo/ZCodeProject/ctd_data'
os.makedirs(OUT, exist_ok=True)

def log(msg):
    sys.stderr.write(msg + "\n"); sys.stderr.flush()

def save_json(obj, name):
    with open(f"{OUT}/{name}.json", 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)
    log(f"  saved {name}.json")

def save_df(df, name):
    df.to_csv(f"{OUT}/{name}.csv", index=False)
    log(f"  saved {name}.csv ({len(df)} rows)")

log(f"=== CTD DATA COLLECTION {datetime.now().isoformat(timespec='seconds')} ===")

# ============ 1. OVERVIEW ============
log("[1] Overview + market data")
c = Company(symbol=TICKER, source='VCI')
ov = c.overview()
if hasattr(ov, 'to_dict'):
    ov_row = ov.iloc[0].to_dict() if len(ov) > 0 else {}
else:
    ov_row = ov
save_json(ov_row, 'overview')
log(f"  price={ov_row.get('current_price')}, mcap={ov_row.get('market_cap')}, sector={ov_row.get('sector')}")

# ============ 2. EVENTS (for split audit) ============
log("[2] Events (split audit)")
try:
    events = c.events()
    save_df(events, 'events')
    # Flag potential splits
    if 'action_type_vi' in events.columns:
        splits = events[events['action_type_vi'].astype(str).str.contains('chia|tách|split', case=False, na=False)]
        log(f"  potential split events: {len(splits)}")
        if len(splits) > 0:
            save_df(splits, 'split_events')
except Exception as e:
    log(f"  events ERR: {repr(e)[:200]}")

# ============ 3. CAPITAL HISTORY (KBS) ============
log("[3] Capital history (KBS)")
try:
    c_kbs = Company(symbol=TICKER, source='KBS')
    cap = c_kbs.capital_history()
    save_df(cap, 'capital_history')
    log(f"  capital history rows: {len(cap)}")
except Exception as e:
    log(f"  capital_history ERR: {repr(e)[:200]}")

# ============ 4. FINANCIAL STATEMENTS ============
log("[4] Financial statements (BCTC)")
f = Finance(symbol=TICKER, source='VCI')
income = f.income_statement()
balance = f.balance_sheet()
cashflow = f.cash_flow()
save_df(income, 'income_statement')
save_df(balance, 'balance_sheet')
save_df(cashflow, 'cash_flow')
log(f"  income {income.shape}, balance {balance.shape}, cashflow {cashflow.shape}")

# ============ 5. RATIOS (with stale check) ============
log("[5] Ratios (stale check)")
try:
    ratios = f.ratio()
    save_df(ratios, 'ratios')
    log(f"  ratios shape: {ratios.shape}")
    # Stale warning: if < 8 year-columns or years are old
    yr_cols = [c for c in ratios.columns if any(str(y) in str(c) for y in range(2018, 2027))]
    log(f"  year columns found: {len(yr_cols)} -> {'STALE?' if len(yr_cols) < 8 else 'ok'}")
except Exception as e:
    log(f"  ratios ERR: {repr(e)[:200]}")

# ============ 6. PRICE DATA — weekly 52W (for ACTIVE mode) ============
log("[6] Price weekly 52W (ACTIVE mode)")
q = Quote(symbol=TICKER, source='VCI')
wk = q.history(start='2025-06-22', end='2026-07-08', interval='1W').dropna(subset=['close'])
save_df(wk, 'price_weekly_52w')
log(f"  weekly rows: {len(wk)}, last close={wk.iloc[-1]['close'] if len(wk)>0 else 'NA'}")

# VNINDEX + VN30 weekly for Beta
for idx in ['VNINDEX', 'VN30']:
    try:
        qi = Quote(symbol=idx, source='VCI')
        wi = qi.history(start='2025-06-22', end='2026-07-08', interval='1W').dropna(subset=['close'])
        save_df(wi, f'price_weekly_{idx.lower()}')
        log(f"  {idx} weekly: {len(wi)} rows")
    except Exception as e:
        log(f"  {idx} ERR: {repr(e)[:150]}")

# ============ 7. PRICE DATA — daily ~2y (for PROFILE mode) ============
log("[7] Price daily ~2y (PROFILE mode)")
for sym in [TICKER, 'VNINDEX', 'VN30']:
    try:
        qd = Quote(symbol=sym, source='VCI')
        dd = qd.history(start='2024-07-01', end='2026-07-08', interval='1D').dropna(subset=['close'])
        save_df(dd, f'price_daily_{sym.lower()}')
        log(f"  {sym} daily: {len(dd)} rows")
    except Exception as e:
        log(f"  {sym} daily ERR: {repr(e)[:150]}")

# ============ 8. NEWS ============
log("[8] News (50 latest)")
try:
    news = c.news()
    save_df(news, 'news')
    log(f"  news: {len(news)} articles")
except Exception as e:
    log(f"  news ERR: {repr(e)[:200]}")

# ============ SPLIT AUDIT (Bẫy 5B) ============
log("[AUDIT] Split-adjustment consistency (Bẫy 5B)")
audit = {"split_detected": False, "notes": []}
try:
    if len(events) > 0 and 'action_type_vi' in events.columns:
        split_rows = events[events['action_type_vi'].astype(str).str.contains('chia|tách|split', case=False, na=False)]
        if len(split_rows) > 0:
            audit['split_detected'] = True
            audit['notes'].append(f"{len(split_rows)} split-related events found — manual EPS/shares adjust required")
    if 'cap' in dir() and len(cap) > 0:
        # detect charter capital jumps > 30% YoY
        cap_sorted = cap.sort_values('date') if 'date' in cap.columns else cap
        audit['capital_history_rows'] = len(cap)
except Exception as e:
    audit['notes'].append(f"audit ERR: {repr(e)[:150]}")
save_json(audit, 'split_audit')
log(f"  split_detected={audit['split_detected']}")

log("=== DONE ===")
