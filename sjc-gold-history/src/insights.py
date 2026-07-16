"""3 special insights for the longform article.

1. Spread between gold types over time (SJC 1L vs ring 99.99 vs jewelry 99% vs 75%)
2. What drives premium elasticity (correlation vs USDVND, QT vol, bid-ask spread)
3. SJC vs VN-Index (return, correlation, drawdown comparison)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .analytics import OUT_DIR, sjc_daily
from .merge import PROCESSED_DIR, build_master
from .spread import LUONG_TO_TROY_OZ

OUT_DIR.mkdir(parents=True, exist_ok=True)


def insight1_gold_types_spread():
    """Compare 4 gold types (SJC 1L, ring 99.99, jewelry 99%, 75%) over time."""
    master = build_master()
    ids = {1: "SJC 1L (miếng)", 49: "Nhẫn SJC 99,99%", 97: "Nữ trang 99%", 113: "Nữ trang 75%"}
    daily = {}
    for gid, label in ids.items():
        d = sjc_daily(master, gid)
        if len(d):
            daily[label] = d.set_index("date")["close_sell"]

    df = pd.DataFrame(daily).dropna(how="all").sort_index()
    # Normalize to SJC 1L = 100 to see relative spreads
    base = df["SJC 1L (miếng)"]
    rel = df.div(base, axis=0).mul(100)

    # Yearly stats: each type as % of SJC 1L
    rel["year"] = rel.index.year
    yearly = rel.groupby("year").mean().round(1).reset_index()

    # Discount of each type vs SJC 1L (negative = cheaper than SJC 1L)
    print("=== Insight 1: Gold types as % of SJC 1L price (yearly avg) ===")
    print(yearly.to_string(index=False))

    yearly.to_csv(OUT_DIR / "insight1_gold_types_yearly.csv", index=False)
    return yearly, df


def insight2_premium_drivers():
    """Correlate premium changes with potential drivers."""
    spread = pd.read_parquet(PROCESSED_DIR / "sjc_spread.parquet")
    spread["date"] = pd.to_datetime(spread["date"])
    fx = pd.read_parquet(PROCESSED_DIR / "fx_gold.parquet")
    fx["date"] = pd.to_datetime(fx["date"])
    master = build_master()
    d1 = sjc_daily(master, 1)[["date", "spread_pct"]].rename(
        columns={"spread_pct": "bidask_pct"})
    d1["date"] = pd.to_datetime(d1["date"])

    m = spread.merge(fx, on="date", suffixes=("", "_fx")).merge(d1, on="date")
    m = m.dropna(subset=["premium_pct", "usd_vnd", "gold_usd_oz", "bidask_pct"])
    m["premium_chg"] = m["premium_pct"].diff()
    m["usdvnd_chg"] = m["usd_vnd"].pct_change()
    m["goldvol_20d"] = m["gold_usd_oz"].pct_change().rolling(20).std() * np.sqrt(252) * 100
    m = m.dropna()

    corrs = {}
    for driver, col in [("USD/VND thay đổi (daily %)", "usdvnd_chg"),
                        ("Volatility vàng QT (20d ann.)", "goldvol_20d"),
                        ("Bid-ask spread SJC (%)", "bidask_pct")]:
        c = m[col].corr(m["premium_pct"])
        c_chg = m[col].corr(m["premium_chg"])
        corrs[driver] = {"corr_with_level": round(float(c), 3),
                         "corr_with_change": round(float(c_chg), 3)}

    print("\n=== Insight 2: Premium correlation with drivers ===")
    for k, v in corrs.items():
        print(f"  {k}: level r={v['corr_with_level']}, change r={v['corr_with_change']}")

    return corrs, m


def insight3_sjc_vs_vnindex():
    """Compare SJC vs VN-Index: return, correlation, drawdown."""
    vni = pd.read_parquet(PROCESSED_DIR / "vnindex.parquet")
    vni["time"] = pd.to_datetime(vni["time"])
    vni = vni.rename(columns={"time": "date", "close": "vnindex"}).sort_values("date")
    vni = vni[["date", "vnindex"]].dropna()

    spread = pd.read_parquet(PROCESSED_DIR / "sjc_spread.parquet")
    spread["date"] = pd.to_datetime(spread["date"])
    sjc = spread[["date", "sell_vnd"]].rename(columns={"sell_vnd": "sjc"})
    sjc["sjc_m"] = sjc["sjc"] / 1e6

    m = pd.merge(sjc, vni, on="date", how="inner").sort_values("date")
    m["sjc_ret"] = m["sjc"].pct_change()
    m["vni_ret"] = m["vnindex"].pct_change()

    # Total return
    sjc_ret = (m["sjc"].iloc[-1] / m["sjc"].iloc[0] - 1) * 100
    vni_ret = (m["vnindex"].iloc[-1] / m["vnindex"].iloc[0] - 1) * 100

    # Correlation of daily returns
    corr = m["sjc_ret"].corr(m["vni_ret"])

    # Max drawdown each
    def max_dd(s):
        cum = (1 + s.fillna(0)).cumprod()
        return float((cum / cum.cummax() - 1).min() * 100)
    sjc_dd = max_dd(m["sjc_ret"])
    vni_dd = max_dd(m["vni_ret"])

    # Annual returns comparison
    m["year"] = m["date"].dt.year
    yr = m.groupby("year").agg(sjc=("sjc", "last"), vni=("vnindex", "last"))
    yr_ret = yr.pct_change() * 100

    print("\n=== Insight 3: SJC vs VN-Index ===")
    print(f"  SJC total return: {sjc_ret:.1f}%  vs  VN-Index: {vni_ret:.1f}%")
    print(f"  Correlation (daily returns): {corr:.3f}")
    print(f"  SJC max drawdown: {sjc_dd:.1f}%  vs  VN-Index: {vni_dd:.1f}%")
    print("\n  Annual returns:")
    print(yr_ret.round(1).to_string())

    yr_ret.round(1).reset_index().to_csv(OUT_DIR / "insight3_sjc_vnindex_yearly.csv", index=False)
    return {"sjc_return": round(sjc_ret, 1), "vni_return": round(vni_ret, 1),
            "correlation": round(float(corr), 3),
            "sjc_dd": round(sjc_dd, 1), "vni_dd": round(vni_dd, 1),
            "rows": len(m), "range": f"{m.date.min().date()} → {m.date.max().date()}",
            "yearly_returns": yr_ret.round(1).reset_index().to_dict("records")}


def main():
    summary = {}
    y1, _ = insight1_gold_types_spread()
    summary["insight1"] = y1.to_dict("records")
    corrs, _ = insight2_premium_drivers()
    summary["insight2"] = corrs
    summary["insight3"] = insight3_sjc_vs_vnindex()
    (OUT_DIR / "insights_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    print(f"\n✅ Saved to {OUT_DIR}/insights_summary.json")


if __name__ == "__main__":
    main()
