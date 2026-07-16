"""Deep analytics for the longform report.

Computes all the derived datasets the longform article needs, in one pass:
  1. Premium SJC vs QT (already in spread.py — re-run for consistency)
  2. Lag correlation QT→SJC (how many days SJC lags world gold moves)
  3. Bid-ask spread over time (SJC stress barometer)
  4. Volatility & drawdown by year
  5. Vàng nhẫn vs vàng miếng spread
  6. Premium SJC vs Shanghai gold proxy (GC=F × USDCNY, 3-tier cascade)

Outputs JSON summary + per-analysis CSVs in data/processed/analytics/.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .merge import PROCESSED_DIR, VN_TZ, build_master
from .spread import LUONG_TO_TROY_OZ

OUT_DIR = PROCESSED_DIR / "analytics"


def sjc_daily(df: pd.DataFrame, gold_price_id: int) -> pd.DataFrame:
    """Collapse intraday to daily OHLC-ish (open=first, close=last, high/low)."""
    d = df[df["gold_price_id"] == gold_price_id].copy()
    d["ts"] = pd.to_datetime(d["timestamp"])
    if d["ts"].dt.tz is None:
        d["ts"] = d["ts"].dt.tz_localize(VN_TZ)
    else:
        d["ts"] = d["ts"].dt.tz_convert(VN_TZ)
    d["date"] = d["ts"].dt.date
    g = d.groupby("date").agg(
        open_buy=("buy_vnd", "first"), close_buy=("buy_vnd", "last"),
        high_buy=("buy_vnd", "max"), low_buy=("buy_vnd", "min"),
        open_sell=("sell_vnd", "first"), close_sell=("sell_vnd", "last"),
        high_sell=("sell_vnd", "max"), low_sell=("sell_vnd", "min"),
    ).reset_index()
    g["date"] = pd.to_datetime(g["date"])
    g["mid_close"] = (g["close_buy"] + g["close_sell"]) / 2
    g["spread_vnd"] = g["close_sell"] - g["close_buy"]
    g["spread_pct"] = g["spread_vnd"] / g["close_sell"] * 100
    return g.sort_values("date").reset_index(drop=True)


def lag_correlation(sjc: pd.DataFrame, fx: pd.DataFrame) -> dict:
    """Cross-correlation: daily returns of QT gold vs SJC, for lags 0..10 days.

    A peak at lag=k means SJC reacts to QT moves k days later.
    """
    m = pd.merge(
        sjc[["date", "close_sell"]].rename(columns={"close_sell": "sjc"}),
        fx[["date", "gold_usd_oz", "world_vnd_per_luong"]].dropna(),
        on="date", how="inner",
    )
    m["sjc_ret"] = m["sjc"].pct_change()
    m["qt_ret"] = m["world_vnd_per_luong"].pct_change()
    m = m.dropna()
    corrs = {}
    for lag in range(0, 11):
        if lag == 0:
            c = m["qt_ret"].corr(m["sjc_ret"])
        else:
            c = m["qt_ret"].corr(m["sjc_ret"].shift(-lag))
        corrs[lag] = round(float(c), 4) if not np.isnan(c) else None
    peak_lag = max(corrs, key=lambda k: corrs[k] or -1)
    # Also: what fraction of QT up-days does SJC follow within 1 day?
    m["qt_up"] = m["qt_ret"] > 0
    m["sjc_up_next"] = m["sjc_ret"].shift(-1) > 0
    follow = (m["qt_up"] & m["sjc_up_next"]).sum() / m["qt_up"].sum()
    return {
        "corrs_by_lag_days": corrs,
        "peak_lag_days": int(peak_lag),
        "peak_corr": corrs[peak_lag],
        "follow_rate_1day": round(float(follow), 4) if not np.isnan(follow) else None,
    }


def yearly_vol_drawdown(sjc: pd.DataFrame) -> pd.DataFrame:
    """Annualized volatility & max drawdown per year."""
    d = sjc.copy()
    d["year"] = d["date"].dt.year
    d["ret"] = d["close_sell"].pct_change()
    rows = []
    for y, g in d.groupby("year"):
        rets = g["ret"].dropna()
        vol = rets.std() * np.sqrt(252) if len(rets) > 5 else None
        # Max drawdown within the year
        cum = (1 + g["ret"].fillna(0)).cumprod()
        running_max = cum.cummax()
        dd = (cum / running_max - 1)
        rows.append({
            "year": int(y),
            "vol_annualized_pct": round(float(vol * 100), 1) if vol else None,
            "max_drawdown_pct": round(float(dd.min() * 100), 1),
            "start_sell_m": round(float(g["close_sell"].iloc[0] / 1e6), 1),
            "end_sell_m": round(float(g["close_sell"].iloc[-1] / 1e6), 1),
            "annual_return_pct": round(
                float((g["close_sell"].iloc[-1] / g["close_sell"].iloc[0] - 1) * 100), 1
            ),
        })
    return pd.DataFrame(rows)


def ring_vs_bar(daily1: pd.DataFrame, daily49: pd.DataFrame) -> pd.DataFrame:
    """Spread between vàng miếng (id=1) and vàng nhẫn (id=49)."""
    m = pd.merge(
        daily1[["date", "close_sell"]].rename(columns={"close_sell": "bar_sell"}),
        daily49[["date", "close_sell"]].rename(columns={"close_sell": "ring_sell"}),
        on="date", how="inner",
    )
    m = m.dropna()
    m["diff_vnd"] = m["bar_sell"] - m["ring_sell"]
    m["diff_pct"] = m["diff_vnd"] / m["ring_sell"] * 100
    return m


def shanghai_cascade(fx: pd.DataFrame) -> dict:
    """Premium SJC vs Shanghai gold proxy = GC=F × USDCNY × (37.5/31.1).

    Shanghai gold typically trades ~1-2% premium to London/COMEX (import quotas).
    So world_gold_cny ≈ gold_usd × usd_cny, and SJC premium vs that.
    """
    m = fx.dropna(subset=["gold_usd_oz", "usd_cny", "usd_vnd"])
    m = m.copy()
    m["world_cny_per_oz"] = m["gold_usd_oz"] * m["usd_cny"]
    m["world_cny_per_luong"] = m["world_cny_per_oz"] * LUONG_TO_TROY_OZ
    # Convert world gold (CNY) to VND via cross rate usd_vnd/usd_cny = vnd_per_cny
    m["vnd_per_cny"] = m["usd_vnd"] / m["usd_cny"]
    m["world_via_cny_per_luong"] = m["world_cny_per_luong"] * m["vnd_per_cny"]
    return {
        "rows": len(m),
        "range": f"{m['date'].min().date()} → {m['date'].max().date()}" if len(m) else "-",
        "vnd_per_cny_mean": round(float(m["vnd_per_cny"].mean()), 1) if len(m) else None,
        "vnd_per_cny_min": round(float(m["vnd_per_cny"].min()), 1) if len(m) else None,
        "vnd_per_cny_max": round(float(m["vnd_per_cny"].max()), 1) if len(m) else None,
        "note": "CNY is a managed float; SJC premium computed via GC=F×USDCNY path",
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    master = build_master()
    fx = pd.read_parquet(PROCESSED_DIR / "fx_gold.parquet")
    fx["date"] = pd.to_datetime(fx["date"])

    # World gold in VND/lượng (for lag + premium)
    fx["world_vnd_per_luong"] = fx["gold_usd_oz"] * fx["usd_vnd"] * LUONG_TO_TROY_OZ

    d1 = sjc_daily(master, 1)
    d49 = sjc_daily(master, 49)

    summary = {}

    # 1. Lag correlation
    print("Computing lag correlation QT→SJC ...")
    lc = lag_correlation(d1, fx)
    summary["lag_correlation"] = lc
    print(f"  peak lag: {lc['peak_lag_days']} days (r={lc['peak_corr']}), "
          f"follow-rate 1d: {lc['follow_rate_1day']}")

    # 2. Bid-ask spread over time
    print("Computing bid-ask spread ...")
    spread = d1[["date", "spread_vnd", "spread_pct", "close_sell"]].copy()
    spread["year"] = spread["date"].dt.year
    spread_stats = spread.groupby("year").agg(
        mean_spread_pct=("spread_pct", "mean"),
        max_spread_pct=("spread_pct", "max"),
        mean_spread_m=("spread_vnd", lambda s: s.mean() / 1e6),
    ).round(2).reset_index()
    spread_stats.to_csv(OUT_DIR / "bidask_spread_yearly.csv", index=False)
    summary["bidask_spread_yearly"] = spread_stats.to_dict("records")

    # 3. Volatility & drawdown
    print("Computing volatility & drawdown ...")
    vd = yearly_vol_drawdown(d1)
    vd.to_csv(OUT_DIR / "vol_drawdown_yearly.csv", index=False)
    summary["vol_drawdown_yearly"] = vd.to_dict("records")

    # 4. Ring vs bar
    print("Computing ring vs bar spread ...")
    rvb = ring_vs_bar(d1, d49)
    rvb["year"] = rvb["date"].dt.year
    rvb_stats = rvb.groupby("year").agg(
        mean_diff_pct=("diff_pct", "mean"),
        min_diff_pct=("diff_pct", "min"),
        max_diff_pct=("diff_pct", "max"),
        n=("diff_pct", "size"),
    ).round(2).reset_index()
    rvb_stats.to_csv(OUT_DIR / "ring_vs_bar_yearly.csv", index=False)
    summary["ring_vs_bar_yearly"] = rvb_stats.to_dict("records")
    rvb.to_csv(OUT_DIR / "ring_vs_bar_daily.csv", index=False)

    # 5. Shanghai cascade
    print("Computing Shanghai cascade ...")
    sc = shanghai_cascade(fx)
    summary["shanghai_cascade"] = sc
    print(f"  VND/CNY mean: {sc['vnd_per_cny_mean']} ({sc['range']})")

    (OUT_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str)
    )
    print(f"\nAll analytics saved to {OUT_DIR}/")
    print(f"  summary.json, bidask_spread_yearly.csv, vol_drawdown_yearly.csv,")
    print(f"  ring_vs_bar_yearly.csv, ring_vs_bar_daily.csv")


if __name__ == "__main__":
    main()
