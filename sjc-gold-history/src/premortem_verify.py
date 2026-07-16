"""Premortem verification — measure all P0/P1 blind spots in one pass.

B.1: USDVND Yahoo→fawaz gap (step shift at 11/07/2025?)
B.2: drawdown intraday vs daily close (flash-crash deeper?)
B.3: cross-check sign bias (11 days off — same direction?)
B.4: rolling correlation SJC vs VN-Index (soften 'independent')
B.5: lag cross-correlation premium vs USDVND change (causal?)
A.2: spec check (can't auto-verify, just note)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .analytics import sjc_daily
from .merge import PROCESSED_DIR, build_master

OUT = PROCESSED_DIR / "analytics"


def b1_usdvnd_gap():
    """Measure step shift at Yahoo→fawaz boundary (~11/07/2025)."""
    fx = pd.read_parquet(PROCESSED_DIR / "fx_gold.parquet")
    fx["date"] = pd.to_datetime(fx["date"])
    vnd = fx.dropna(subset=["usd_vnd"]).sort_values("date").set_index("date")["usd_vnd"]
    # Boundary ~ 2025-07-11. Window 30d before / 30d after.
    b = pd.Timestamp("2025-07-11")
    before = vnd.loc[b - pd.Timedelta(days=30):b - pd.Timedelta(days=1)]
    after = vnd.loc[b:b + pd.Timedelta(days=30)]
    # Overlap check: any dates with both sources? Re-fetch both to compare.
    from curl_cffi import requests as cf
    overlap_days = []
    for d in pd.date_range("2025-06-15", "2025-07-25"):
        # fawaz
        try:
            r = cf.get(f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{d.date().isoformat()}/v1/currencies/usd.json",
                       impersonate="chrome", timeout=10)
            fv = r.json().get("usd", {}).get("vnd") if r.status_code == 200 else None
        except Exception:
            fv = None
        yv = vnd.get(d, None)
        if fv and yv:
            overlap_days.append({"date": d.date(), "yahoo": float(yv), "fawaz": float(fv),
                                 "diff_pct": (fv - float(yv)) / float(yv) * 100})
    df = pd.DataFrame(overlap_days)
    print("=== B.1: USDVND Yahoo↔fawaz overlap ===")
    if len(df):
        print(f"  overlap days: {len(df)}")
        print(f"  diff mean: {df.diff_pct.mean():.3f}%  std: {df.diff_pct.std():.3f}%")
        print(f"  diff range: {df.diff_pct.min():.3f}% to {df.diff_pct.max():.3f}%")
        print(f"  systematic bias? mean abs > 0.1% = {'YES' if abs(df.diff_pct.mean())>0.1 else 'no'}")
        print(df.head(5).to_string(index=False))
    else:
        print("  no overlap days found (Yahoo already stopped before fawaz window)")
    return df


def b2_drawdown_intraday():
    """Drawdown on raw intraday SJC vs daily close."""
    master = build_master()
    sjc = master[master["gold_price_id"] == 1].copy()
    sjc["ts"] = pd.to_datetime(sjc["timestamp"])
    sjc = sjc.sort_values("ts").dropna(subset=["sell_vnd"])

    # Intraday drawdown — use sell_vnd series directly
    cum_i = sjc["sell_vnd"]
    runmax_i = cum_i.cummax()
    dd_i = (cum_i / runmax_i - 1) * 100
    intraday_maxdd = dd_i.min()

    # Daily close drawdown
    d1 = sjc_daily(master, 1).sort_values("date")
    cum_d = d1["close_sell"]
    dd_d = (cum_d / cum_d.cummax() - 1) * 100
    daily_maxdd = dd_d.min()

    print("\n=== B.2: drawdown intraday vs daily ===")
    print(f"  daily close max DD:    {daily_maxdd:.1f}%")
    print(f"  intraday max DD:       {intraday_maxdd:.1f}%")
    print(f"  difference:            {abs(intraday_maxdd) - abs(daily_maxdd):.1f}pp")
    print(f"  flash-crash deeper?    {'YES — underestimating risk' if abs(intraday_maxdd) > abs(daily_maxdd)+1 else 'no (>1pp threshold)'}")

    # When did intraday max DD happen?
    idx = dd_i.idxmin()
    print(f"  intraday max DD on:    {sjc.loc[idx, 'ts']}")
    return {"daily": round(float(daily_maxdd), 1), "intraday": round(float(intraday_maxdd), 1),
            "diff_pp": round(float(abs(intraday_maxdd) - abs(daily_maxdd)), 1)}


def b3_crosscheck_sign_bias():
    """Check direction of 11 'off' days in cross-check."""
    # Re-run crosscheck but capture sign
    import requests
    from .spread import build_spread
    spread = build_spread(PROCESSED_DIR / "sjc_master.parquet", PROCESSED_DIR / "fx_gold.parquet")
    spread["date"] = pd.to_datetime(spread["date"])
    spread["d"] = spread["date"].dt.date

    # Sample 30 days seed 42, same as crosscheck
    import random
    from datetime import date as ddate
    cutoff = ddate(2025, 4, 21)
    days = sorted({d for d in spread["d"] if d <= cutoff})
    rng = random.Random(42)
    sample = rng.sample(days, min(30, len(days)))

    GV_URL = "https://giavang.org/trong-nuoc/sjc/lich-su/{d}.html"
    diffs = []
    for d in sample:
        day_df = spread[spread["d"] == d].sort_values("date")
        if day_df.empty:
            continue
        master_sell = int(day_df.iloc[-1]["sell_vnd"])
        try:
            import re
            r = requests.get(GV_URL.format(d=d.isoformat()), headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            if r.status_code != 200 or "x1000đ/lượng" not in r.text:
                continue
            i = r.text.find("Đơn vị")
            seg = r.text[i:i + 4000]
            m = re.search(r'Hồ Chí Minh</th>\s*<td[^>]*>Vàng SJC 1L[^<]*</td>\s*<td[^>]*>([0-9.]+)</td>\s*<td[^>]*>([0-9.]+)</td>', seg)
            if not m:
                continue
            gv_sell = int(m.group(2).replace(".", "")) * 1000
            diffs.append({"date": d, "master": master_sell, "giavang": gv_sell,
                          "diff": master_sell - gv_sell})
        except Exception:
            continue

    df = pd.DataFrame(diffs)
    off = df[df["diff"] != 0]
    print("\n=== B.3: cross-check sign bias ===")
    print(f"  total compared: {len(df)}, exact: {(df['diff']==0).sum()}, off: {len(off)}")
    if len(off):
        pos = (off["diff"] > 0).sum()
        neg = (off["diff"] < 0).sum()
        print(f"  off days — master HIGHER than giavang: {pos}, LOWER: {neg}")
        print(f"  systematic bias? {'YES — all same direction' if min(pos,neg)==0 else 'no — mixed direction'}")
        print(f"  mean diff: {off['diff'].mean():,.0f} VND")
    return df


def b4_rolling_corr():
    """Rolling 252-day correlation SJC vs VN-Index."""
    vni = pd.read_parquet(PROCESSED_DIR / "vnindex.parquet")
    vni["date"] = pd.to_datetime(vni["time"])
    vni = vni.rename(columns={"close": "vnindex"})[["date", "vnindex"]].dropna()

    spread = pd.read_parquet(PROCESSED_DIR / "sjc_spread.parquet")
    spread["date"] = pd.to_datetime(spread["date"])
    sjc = spread[["date", "sell_vnd"]].rename(columns={"sell_vnd": "sjc"})

    m = sjc.merge(vni, on="date").sort_values("date")
    m["sjc_ret"] = m["sjc"].pct_change()
    m["vni_ret"] = m["vnindex"].pct_change()
    rolling = m["sjc_ret"].rolling(252).corr(m["vni_ret"]).dropna()

    print("\n=== B.4: rolling 252d corr SJC vs VN-Index ===")
    print(f"  point estimate (full): {m['sjc_ret'].corr(m['vni_ret']):.3f}")
    print(f"  rolling mean: {rolling.mean():.3f}, std: {rolling.std():.3f}")
    print(f"  rolling range: {rolling.min():.3f} to {rolling.max():.3f}")
    print(f"  ever > 0.3? {'YES' if rolling.max()>0.3 else 'no'}")
    print(f"  soften 'independent'? {'YES — rolling varies' if rolling.max()-rolling.min()>0.2 else 'no — stable'}")
    return {"full_corr": round(float(m['sjc_ret'].corr(m['vni_ret'])), 3),
            "rolling_mean": round(float(rolling.mean()), 3),
            "rolling_min": round(float(rolling.min()), 3),
            "rolling_max": round(float(rolling.max()), 3)}


def b5_lag_causal():
    """Cross-correlation premium vs USDVND change at different lags."""
    m = pd.read_parquet(PROCESSED_DIR / "sjc_spread.parquet")
    m["date"] = pd.to_datetime(m["date"])
    m = m.dropna(subset=["premium_pct", "usd_vnd"])
    m["premium_chg"] = m["premium_pct"].diff()
    m["usdvnd_chg"] = m["usd_vnd"].pct_change()
    m = m.dropna()

    print("\n=== B.5: lag cross-correlation (premium Δ vs USDVND Δ) ===")
    corrs = {}
    for lag in range(-5, 6):
        if lag >= 0:
            c = m["usdvnd_chg"].corr(m["premium_chg"].shift(-lag))
        else:
            c = m["usdvnd_chg"].shift(-lag).corr(m["premium_chg"])
        corrs[lag] = round(float(c), 3) if not np.isnan(c) else None
        label = f"USDVND t, premium t{'+' if lag>0 else ''}{lag}" if lag != 0 else "same day (lag 0)"
        print(f"  lag {lag:+d} ({label}): r = {corrs[lag]}")

    peak_lag = max(corrs, key=lambda k: abs(corrs[k] or 0))
    print(f"\n  peak |r| at lag {peak_lag} (r={corrs[peak_lag]})")
    print(f"  causal direction USDVND→premium? {'YES' if peak_lag>0 else 'NO — reverse or simultaneous' if peak_lag<0 else 'simultaneous (lag 0)'}")
    return corrs


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = {}
    try:
        results["b1"] = b1_usdvnd_gap().to_dict("records")
    except Exception as e:
        results["b1_error"] = str(e)
    results["b2"] = b2_drawdown_intraday()
    try:
        results["b3"] = b3_crosscheck_sign_bias().to_dict("records")
    except Exception as e:
        results["b3_error"] = str(e)
    results["b4"] = b4_rolling_corr()
    results["b5"] = b5_lag_causal()
    (OUT / "premortem_verify.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str))
    print(f"\n✅ Saved {OUT / 'premortem_verify.json'}")


if __name__ == "__main__":
    main()
