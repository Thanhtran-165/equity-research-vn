#!/usr/bin/env python3
"""
Exploratory analysis — tìm patterns thật trong data để inform outline.

Phân tích 4 mối quan hệ cốt lõi:
1. Bond yields vs SBV rate decisions (event study)
2. Bond yields vs USD/VND (correlation + lead/lag)
3. Bond yields vs CPI (correlation)
4. Bond yields vs interbank proxy (correlation)
"""
import pandas as pd
import numpy as np

m = pd.read_csv("data/processed/master_monthly.csv")
m["date"] = pd.to_datetime(m["date"])
m = m.sort_values("date").reset_index(drop=True)

print("=" * 70)
print("EXPLORATORY ANALYSIS — vn-bond-transmission")
print("=" * 70)
print(f"\nMaster monthly: {len(m)} rows | {m.date.min().date()} → {m.date.max().date()}")

# Focus window: 2014-2026 (có bond yields)
w = m[m.date >= "2014-01"].copy()
print(f"Analysis window (2014+): {len(w)} months")

# ========================================
print("\n" + "=" * 70)
print("MỐI QUAN HỆ 1: BOND YIELDS ↔ SBV RATE DECISIONS")
print("=" * 70)

# SBV refinancing changes
sbv = pd.read_csv("data/raw/sbv_decisions/sbv_policy_rate_timeline.csv")
ref_changes = sbv[(sbv.rate_type == "refinancing") & (sbv.effective_date >= "2014-01-01")].copy()
ref_changes["date"] = pd.to_datetime(ref_changes["effective_date"])
print(f"\nSBV refinancing changes 2014-2026: {len(ref_changes)}")

# Bond yield trước/sau mỗi SBV decision
print("\n--- Bond 10Y yield quanh mỗi SBV decision (before/after 3 months) ---")
prev_rate = 6.0  # refinancing rate đầu tiên trong window
for _, ev in ref_changes.iterrows():
    ev_date = ev["date"]
    before = w[(w.date < ev_date) & (w.date >= ev_date - pd.Timedelta(days=90))]
    after = w[(w.date > ev_date) & (w.date <= ev_date + pd.Timedelta(days=90))]
    b_y = before["10y_par_yield"].mean()
    a_y = after["10y_par_yield"].mean()
    delta = a_y - b_y if not np.isnan(b_y) and not np.isnan(a_y) else np.nan
    direction = "HIKING" if ev["rate_pct"] > prev_rate else ("CUT" if ev["rate_pct"] < prev_rate else "HOLD")
    print(f"  {ev_date.strftime('%Y-%m-%d')}: SBV→{ev['rate_pct']}% [{direction}] ({ev['decision_number'][:18]}) | "
          f"10Y before={b_y:.2f}% after={a_y:.2f}% Δ={delta:+.2f}")
    prev_rate = ev["rate_pct"]

# ========================================
print("\n" + "=" * 70)
print("MỐI QUAN HỆ 2: BOND YIELDS ↔ USD/VND")
print("=" * 70)

# Correlation bond vs FX
sub = w[["10y_par_yield", "5y_par_yield", "2y_par_yield", "usd_vnd_central", "usd_vnd_market"]].dropna()
print(f"\nObservations: {len(sub)}")
print(f"\nPearson correlation (monthly, same period):")
corr = sub.corr()
print(corr.round(3))

# Lead/lag: does bond lead FX or vice versa?
print("\n--- Lead/lag analysis (cross-correlation) ---")
for lag in [-3, -2, -1, 0, 1, 2, 3]:
    bond = w["10y_par_yield"]
    fx = w["usd_vnd_central"]
    if lag >= 0:
        c = bond.corr(fx.shift(-lag))
    else:
        c = bond.corr(fx.shift(-lag))
    label = f"bond t vs FX t{lag:+d}" if lag != 0 else "bond t vs FX t  "
    print(f"  {label}: {c:.3f}")

# ========================================
print("\n" + "=" * 70)
print("MỐI QUAN HỆ 3: BOND YIELDS ↔ CPI")
print("=" * 70)

cpi_sub = w[["10y_par_yield", "5y_par_yield", "cpi_yoy_pct", "cpi_mom_pct"]].dropna()
print(f"\nObservations: {len(cpi_sub)}")
print(f"\nPearson correlation:")
print(cpi_sub.corr().round(3))

# Does bond yield lead CPI? (Fisher hypothesis)
print("\n--- Bond yield vs CPI YoY (lag analysis) ---")
for lag in [-6, -3, 0, 3, 6, 12]:
    bond = w["10y_par_yield"]
    cpi = w["cpi_yoy_pct"]
    if lag >= 0:
        c = bond.corr(cpi.shift(-lag))
    else:
        c = bond.corr(cpi.shift(-lag))
    print(f"  bond t vs CPI t{lag:+d}: {c:.3f}")

# ========================================
print("\n" + "=" * 70)
print("MỐI QUAN HỆ 4: BOND YIELDS ↔ INTERBANK PROXY")
print("=" * 70)

# IMF Lending rate (proxy) vs bond yield
interbank_sub = w[["10y_par_yield", "lending_rate", "deposit_rate"]].dropna()
print(f"\nObservations: {len(interbank_sub)}")
print(f"\nPearson correlation:")
print(interbank_sub.corr().round(3))

print("\n--- Note: lending/deposit rate là BANK-TO-CUSTOMER, KHÔNG phải interbank ---")
print("--- Đây là PROXY, chỉ cho thấy trend direction, không claim causal về interbank ---")

# ========================================
print("\n" + "=" * 70)
print("BONUS: US 10Y vs VN 10Y (transmission quốc tế)")
print("=" * 70)

us_vn = w[["10y_par_yield", "us_10y_yield", "us_2y_yield", "dxy_trade_weighted"]].dropna()
print(f"\nObservations: {len(us_vn)}")
print(f"\nPearson correlation:")
print(us_vn.corr().round(3))

# Yield spread VN-US
us_vn["vn_us_spread"] = us_vn["10y_par_yield"] - us_vn["us_10y_yield"]
print(f"\nVN-US 10Y spread: mean={us_vn.vn_us_spread.mean():.2f}% | min={us_vn.vn_us_spread.min():.2f}% | max={us_vn.vn_us_spread.max():.2f}%")
print(f"  2020: {us_vn[us_vn.index.isin(w[w.date.str[:4]=='2020'].index) if False else us_vn.index[-60:-48]].vn_us_spread.mean():.2f}%")
print(f"  2022: {us_vn.vn_us_spread.iloc[-48:-36].mean():.2f}%")
print(f"  2024: {us_vn.vn_us_spread.iloc[-24:-12].mean():.2f}%")
print(f"  2026: {us_vn.vn_us_spread.iloc[-7:].mean():.2f}%")

# ========================================
print("\n" + "=" * 70)
print("KEY FINDINGS SUMMARY")
print("=" * 70)
print("""
Từ exploratory analysis, các patterns nổi bật:
1. [Điền sau khi chạy]
2. 
3. 
""")
