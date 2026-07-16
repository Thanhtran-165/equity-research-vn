#!/usr/bin/env python3
"""
Build master_monthly.csv + master_daily_2014_2026.csv + COVERAGE.md.

Merges all raw data sources into aligned master datasets with provenance + confidence flags.
"""
import pandas as pd, numpy as np, os
from datetime import datetime

BASE = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(BASE, "data", "raw")
OUT = os.path.join(BASE, "data", "processed")
os.makedirs(OUT, exist_ok=True)

def load_csv(path, **kw):
    if os.path.exists(path):
        return pd.read_csv(path, **kw)
    print(f"  ⚠️ NOT FOUND: {path}")
    return None

print("=" * 70)
print("BUILDING MASTER DATASETS")
print("=" * 70)

# ========================================
# 1. HNX YIELD (biến A — daily 2014-2026)
# ========================================
print("\n[1] HNX Yield Curve (biến A)...")
hnx = load_csv(f"{RAW}/hnx_yield/hnx_yield_curve_daily.csv")
if hnx is not None:
    hnx["date"] = pd.to_datetime(hnx["date"], errors="coerce")
    hnx = hnx.dropna(subset=["date"]).sort_values("date")
    print(f"  {len(hnx)} rows | {hnx.date.min().date()} → {hnx.date.max().date()}")
    # Key tenors
    for col in ["2y_par_yield", "5y_par_yield", "10y_par_yield"]:
        if col in hnx.columns:
            valid = hnx[col].notna().sum()
            print(f"    {col}: {valid}/{len(hnx)} valid")

# ========================================
# 2. SBV CENTRAL FX (biến C central — daily 2015-2026)
# ========================================
print("\n[2] SBV Central FX (biến C central)...")
sbv_fx = load_csv(f"{RAW}/sbv_fx/sbv_central_fx_daily.csv")
if sbv_fx is not None:
    sbv_fx["date"] = pd.to_datetime(sbv_fx["date"], errors="coerce")
    sbv_fx = sbv_fx.dropna(subset=["date"]).sort_values("date")
    sbv_fx["usd_vnd_central"] = pd.to_numeric(sbv_fx["usd_vnd_central"], errors="coerce")
    print(f"  {len(sbv_fx)} rows | {sbv_fx.date.min().date()} → {sbv_fx.date.max().date()}")
    print(f"  USD/VND range: {sbv_fx.usd_vnd_central.min():.0f} → {sbv_fx.usd_vnd_central.max():.0f}")

# ========================================
# 3. USD/VND MARKET (biến C market — daily 2009-2026, từ sjc)
# ========================================
print("\n[3] USD/VND Market Rate (biến C market)...")
mkt_fx = load_csv(f"{RAW}/workspace_reuse/usd_vnd_market_daily_2009_2026.csv")
if mkt_fx is not None:
    mkt_fx["date"] = pd.to_datetime(mkt_fx["date"], errors="coerce")
    mkt_fx = mkt_fx.dropna(subset=["date"]).sort_values("date")
    print(f"  {len(mkt_fx)} rows | {mkt_fx.date.min().date()} → {mkt_fx.date.max().date()}")

# ========================================
# 4. IMF LENDING/DEPOSIT (biến B proxy — monthly 1992-2023)
# ========================================
print("\n[4] IMF Lending/Deposit Rate (biến B proxy)...")
imf = load_csv(f"{RAW}/imf_rates/imf_lending_deposit_monthly.csv")
if imf is not None:
    imf["date"] = pd.to_datetime(imf["period"], errors="coerce")
    imf = imf.dropna(subset=["date"]).sort_values("date")
    # Pivot: series → columns
    imf_pivot = imf.pivot_table(index="date", columns="series", values="value", aggfunc="first").reset_index()
    print(f"  {len(imf_pivot)} months | {imf_pivot.date.min().date()} → {imf_pivot.date.max().date()}")

# ========================================
# 5. FRED (biến D CPI + context US rates/DXY — daily/monthly)
# ========================================
# ========================================
# 5. FRED (biến D CPI + context US rates/DXY — daily/monthly)
# ========================================
print("\n[5] FRED (CPI VN + US rates + DXY)...")
fred = load_csv(f"{RAW}/fred_global/fred_data.csv")
if fred is not None:
    fred["date"] = pd.to_datetime(fred["date"], errors="coerce")
    fred["value"] = pd.to_numeric(fred["value"], errors="coerce")
    fred = fred.dropna(subset=["date", "value"])
    # Pivot từng series riêng rồi merge (tránh pivot_table bug với NaT/duplicate)
    parts = []
    for s in fred.series.unique():
        sub = fred[fred.series == s][["date","value"]].rename(columns={"value": s}).drop_duplicates("date")
        parts.append(sub)
    fred_pivot = parts[0]
    for p in parts[1:]:
        fred_pivot = fred_pivot.merge(p, on="date", how="outer")
    fred_pivot = fred_pivot.sort_values("date").reset_index(drop=True)
    print(f"  {len(fred_pivot)} rows | {fred_pivot.date.min().date()} → {fred_pivot.date.max().date()}")
    for col in fred_pivot.columns:
        if col != "date":
            valid = fred_pivot[col].notna().sum()
            print(f"    {col}: {valid} valid")

# ========================================
# 5b. NSO CPI MONTHLY (biến D — monthly YoY/MoM 2019-2026)
# ========================================
print("\n[5b] NSO CPI monthly (biến D monthly)...")
nso_cpi = load_csv(f"{RAW}/cpi/nso_cpi_monthly.csv")
if nso_cpi is not None:
    nso_cpi["date"] = pd.to_datetime(nso_cpi["date"], errors="coerce")
    nso_cpi = nso_cpi.dropna(subset=["date"]).sort_values("date")
    print(f"  {len(nso_cpi)} months | {nso_cpi.date.min().date()} → {nso_cpi.date.max().date()}")
    print(f"    YoY valid: {nso_cpi.cpi_yoy_pct.notna().sum()} | MoM valid: {nso_cpi.cpi_mom_pct.notna().sum()}")

# ========================================
# 6. WORLD BANK (context annual)
# ========================================
print("\n[6] World Bank macro (annual context)...")
wb = load_csv(f"{RAW}/worldbank_macro/wb_vn_annual.csv")
if wb is not None:
    wb_pivot = wb.pivot_table(index="year", columns="indicator", values="value", aggfunc="first").reset_index()
    print(f"  {len(wb_pivot)} years | {int(wb_pivot.year.min())} → {int(wb_pivot.year.max())}")

# ========================================
# 7. VBMA INTERBANK (biến B gần đây — weekly 2026)
# ========================================
print("\n[7] VBMA Interbank (weekly gần đây)...")
vbma = load_csv(f"{RAW}/vbma_archive/vbma_interbank_weekly.csv")
if vbma is not None:
    # Parse week_to → date
    vbma["date"] = pd.to_datetime(vbma["week_to"], format="%d%m%Y", errors="coerce")
    vbma = vbma.dropna(subset=["date"]).sort_values("date")
    print(f"  {len(vbma)} weeks | {vbma.date.min().date()} → {vbma.date.max().date()}")

# ========================================
# 8. SBV POLICY RATE (biến E — event timeline)
# ========================================
print("\n[8] SBV Policy Rate timeline (biến E)...")
sbv_pol = load_csv(f"{RAW}/sbv_decisions/sbv_policy_rate_timeline.csv")
if sbv_pol is not None:
    # Handle both old (date) and new (effective_date) schema
    date_col = "effective_date" if "effective_date" in sbv_pol.columns else "date"
    sbv_pol["date"] = pd.to_datetime(sbv_pol[date_col], errors="coerce")
    sbv_pol = sbv_pol.dropna(subset=["date"]).sort_values("date")
    print(f"  {len(sbv_pol)} events | {sbv_pol.date.min().date()} → {sbv_pol.date.max().date()}")

# ========================================
# BUILD master_daily_2014_2026.csv (overlap đủ biến)
# ========================================
print("\n" + "=" * 70)
print("BUILDING master_daily_2014_2026.csv")
print("=" * 70)

daily = pd.DataFrame()
if hnx is not None:
    daily = hnx[["date"] + [c for c in ["2y_par_yield","5y_par_yield","10y_par_yield"] if c in hnx.columns]].copy()
    # Add provenance
    for c in ["2y_par_yield","5y_par_yield","10y_par_yield"]:
        if c in daily.columns:
            daily[f"{c}_src"] = "HNX"
            daily[f"{c}_conf"] = "high"

if sbv_fx is not None:
    daily = daily.merge(sbv_fx[["date","usd_vnd_central"]], on="date", how="outer")
    daily["usd_vnd_central_src"] = "SBV"
    daily["usd_vnd_central_conf"] = "high"

if mkt_fx is not None:
    # Only usd_vnd_filled
    sub = mkt_fx[["date"]].copy()
    sub["usd_vnd_market"] = mkt_fx["usd_vnd_filled"] if "usd_vnd_filled" in mkt_fx.columns else mkt_fx["usd_vnd"]
    daily = daily.merge(sub, on="date", how="outer")
    daily["usd_vnd_market_src"] = "sjc-gold-history (VCB/Market)"
    daily["usd_vnd_market_conf"] = "high"

if fred_pivot is not None:
    fred_sub = fred_pivot[["date"] + [c for c in ["us_10y_yield","us_2y_yield","dxy_trade_weighted"] if c in fred_pivot.columns]].copy()
    daily = daily.merge(fred_sub, on="date", how="outer")

# Filter 2014-2026
daily = daily[(daily["date"] >= "2014-01-01") & (daily["date"] <= "2026-12-31")]
daily = daily.sort_values("date").reset_index(drop=True)

daily_path = f"{OUT}/master_daily_2014_2026.csv"
daily.to_csv(daily_path, index=False)
print(f"✅ Saved {len(daily)} rows -> {daily_path}")
print(f"   Date range: {daily.date.min().date()} → {daily.date.max().date()}")
print(f"   Columns: {list(daily.columns)}")

# ========================================
# BUILD master_monthly.csv
# ========================================
print("\n" + "=" * 70)
print("BUILDING master_monthly.csv")
print("=" * 70)

def to_monthly(df, date_col="date", agg="mean"):
    """Resample daily → monthly."""
    d = df.copy()
    d["month"] = d[date_col].dt.to_period("M")
    numeric_cols = d.select_dtypes(include=[np.number]).columns.tolist()
    if agg == "mean":
        m = d.groupby("month")[numeric_cols].mean().reset_index()
    elif agg == "last":
        m = d.groupby("month")[numeric_cols].last().reset_index()
    m["month"] = m["month"].astype(str)
    return m

monthly = pd.DataFrame()

# Bond yields → monthly mean (EOM cho yield)
if hnx is not None:
    hnx_m = to_monthly(hnx[["date"] + [c for c in ["2y_par_yield","5y_par_yield","10y_par_yield"] if c in hnx.columns]], agg="mean")
    hnx_m = hnx_m.rename(columns={"month":"date"})
    monthly = hnx_m if monthly.empty else monthly.merge(hnx_m, on="date", how="outer")

# SBV FX → monthly mean
if sbv_fx is not None:
    fx_m = to_monthly(sbv_fx[["date","usd_vnd_central"]])
    fx_m = fx_m.rename(columns={"month":"date"})
    monthly = monthly.merge(fx_m, on="date", how="outer") if not monthly.empty else fx_m

# Market FX → monthly mean
if mkt_fx is not None:
    sub = mkt_fx[["date"]].copy()
    sub["usd_vnd_market"] = mkt_fx["usd_vnd_filled"] if "usd_vnd_filled" in mkt_fx.columns else mkt_fx["usd_vnd"]
    mkt_m = to_monthly(sub)
    mkt_m = mkt_m.rename(columns={"month":"date"})
    monthly = monthly.merge(mkt_m, on="date", how="outer") if not monthly.empty else mkt_m

# IMF rates → đã monthly
if imf_pivot is not None:
    imf_m = imf_pivot.copy()
    imf_m["date"] = imf_m["date"].dt.to_period("M").astype(str)
    monthly = monthly.merge(imf_m, on="date", how="outer") if not monthly.empty else imf_m

# FRED US rates → monthly mean; CPI VN index → monthly (đã monthly)
if fred_pivot is not None:
    for col in ["us_10y_yield","us_2y_yield","dxy_trade_weighted"]:
        if col in fred_pivot.columns:
            sub = fred_pivot[["date", col]].dropna()
            if len(sub) > 0:
                m = to_monthly(sub)
                m = m.rename(columns={"month":"date"})
                monthly = monthly.merge(m, on="date", how="outer") if not monthly.empty else m
    # CPI VN index (annual, forward-fill)
    if "cpi_vn_index" in fred_pivot.columns:
        cpi = fred_pivot[["date","cpi_vn_index"]].dropna()
        cpi["date"] = cpi["date"].dt.to_period("M").astype(str)
        cpi = cpi.rename(columns={"date":"year_month"})
        # Map to year
        cpi["year"] = cpi["year_month"].str[:4].astype(int)
        monthly["year"] = monthly["date"].str[:4].astype(int) if "date" in monthly.columns else None
        if "year" in monthly.columns:
            monthly = monthly.merge(cpi[["year","cpi_vn_index"]], on="year", how="left")
            monthly = monthly.drop(columns=["year"])

# NSO CPI monthly YoY/MoM
if nso_cpi is not None:
    nso_m = nso_cpi[["date","cpi_yoy_pct","cpi_mom_pct"]].copy()
    nso_m["date"] = nso_m["date"].dt.to_period("M").astype(str)
    nso_m = nso_m.rename(columns={"cpi_yoy_pct":"cpi_yoy_pct","cpi_mom_pct":"cpi_mom_pct"})
    monthly = monthly.merge(nso_m, on="date", how="outer") if not monthly.empty else nso_m

# SBV policy rate → forward-fill theo month
if sbv_pol is not None:
    # Refinancing + discount
    for rt in ["refinancing", "discount"]:
        sub = sbv_pol[sbv_pol["rate_type"] == rt][["date","rate_pct"]].copy()
        sub = sub.rename(columns={"rate_pct": f"sbv_{rt}_pct"})
        sub["month"] = sub["date"].dt.to_period("M")
        # Forward fill: mỗi month lấy rate mới nhất ≤ month đó
        all_months = pd.period_range(sub["month"].min(), pd.Period.now("M"), freq="M")
        sub_full = pd.DataFrame({"month": all_months})
        sub_full = sub_full.merge(sub.groupby("month")[f"sbv_{rt}_pct"].last().reset_index(), on="month", how="left")
        sub_full[f"sbv_{rt}_pct"] = sub_full[f"sbv_{rt}_pct"].ffill()
        sub_full["date"] = sub_full["month"].astype(str)
        monthly = monthly.merge(sub_full[["date", f"sbv_{rt}_pct"]], on="date", how="outer") if not monthly.empty else sub_full[["date", f"sbv_{rt}_pct"]]

monthly["date"] = monthly["date"].astype(str)
monthly = monthly.sort_values("date").reset_index(drop=True)
# Filter 1992+ (có IMF proxy)
monthly = monthly[monthly["date"] >= "1992-01"].reset_index(drop=True)

monthly_path = f"{OUT}/master_monthly.csv"
monthly.to_csv(monthly_path, index=False)
print(f"✅ Saved {len(monthly)} rows -> {monthly_path}")
print(f"   Date range: {monthly.date.min()} → {monthly.date.max()}")
print(f"   Columns: {list(monthly.columns)}")

# ========================================
# COVERAGE REPORT
# ========================================
print("\n" + "=" * 70)
print("COVERAGE ANALYSIS")
print("=" * 70)

def coverage_report(df, date_col, name):
    if df is None or date_col not in df.columns:
        return f"  {name}: ❌ MISSING"
    d = pd.to_datetime(df[date_col], errors="coerce").dropna()
    if len(d) == 0:
        return f"  {name}: ❌ NO VALID DATES"
    return f"  {name}: {len(df)} rows | {d.min().date()} → {d.max().date()}"

print("\n=== DAILY DATA ===")
print(coverage_report(hnx, "date", "A. Bond yields (HNX)"))
print(coverage_report(sbv_fx, "date", "C. USD/VND central (SBV)"))
print(coverage_report(mkt_fx, "date", "C. USD/VND market (sjc)"))
print(coverage_report(fred_pivot, "date", "Context: US rates + DXY"))

print("\n=== MONTHLY DATA ===")
print(coverage_report(imf_pivot, "date", "B. Interbank PROXY (IMF Lending/Deposit)"))
print(coverage_report(monthly, "date", "Master monthly"))

print("\n=== WEEKLY DATA ===")
print(coverage_report(vbma, "date", "B. Interbank real (VBMA, gần đây)"))

print("\n=== EVENT DATA ===")
print(coverage_report(sbv_pol, "date", "E. SBV policy rate decisions"))

print("\n=== ANNUAL CONTEXT ===")
print(coverage_report(wb_pivot, "year", "World Bank macro"))

print("\n✅ DONE — Master datasets built.")
