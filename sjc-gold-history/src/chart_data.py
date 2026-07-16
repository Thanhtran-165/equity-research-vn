"""Export pre-computed chart datasets as JSON for the longform article.

Each output is a Chart.js-ready config fragment (labels + datasets) so the
article's inline JS stays clean. Saved to data/processed/analytics/chart_data.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .analytics import OUT_DIR, sjc_daily, ring_vs_bar
from .merge import PROCESSED_DIR, build_master
from .spread import LUONG_TO_TROY_OZ, build_spread


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    master = build_master()
    fx = pd.read_parquet(PROCESSED_DIR / "fx_gold.parquet")
    fx["date"] = pd.to_datetime(fx["date"])

    spread = build_spread(PROCESSED_DIR / "sjc_master.parquet",
                          PROCESSED_DIR / "fx_gold.parquet")
    spread["date"] = pd.to_datetime(spread["date"])

    d1 = sjc_daily(master, 1)
    d49 = sjc_daily(master, 49)

    charts = {}

    # C1: SJC price 17 years (monthly avg for readability)
    d1m = d1.set_index("date")["close_sell"].resample("MS").mean().dropna()
    charts["c1_sjc_full"] = {
        "labels": [d.strftime("%m/%Y") for d in d1m.index],
        "datasets": [{"label": "SJC bán (triệu/lượng)",
                      "data": [round(v / 1e6, 2) for v in d1m.values]}],
    }

    # C2: Premium % by year (mean/min/max)
    sy = spread.copy()
    sy["year"] = sy["date"].dt.year
    g = sy.groupby("year").agg(mean=("premium_pct", "mean"),
                               mn=("premium_pct", "min"),
                               mx=("premium_pct", "max")).round(2)
    charts["c2_premium_yearly"] = {
        "labels": [int(y) for y in g.index],
        "datasets": [
            {"label": "Premium TB (%)", "data": g["mean"].round(2).tolist(),
             "type": "bar"},
            {"label": "Min (%)", "data": g["mn"].tolist(), "type": "line"},
            {"label": "Max (%)", "data": g["mx"].tolist(), "type": "line"},
        ],
    }

    # C3: SJC vs world gold (VND/lượng), quarterly avg
    q = spread.set_index("date")[["sell_vnd", "world_vnd_per_luong"]].resample("QS").mean().dropna()
    charts["c3_sjc_vs_world"] = {
        "labels": [d.strftime("%m/%Y") for d in q.index],
        "datasets": [
            {"label": "SJC bán (triệu/lượng)",
             "data": [round(v / 1e6, 1) for v in q["sell_vnd"]]},
            {"label": "Vàng QT quy đổi (triệu/lượng)",
             "data": [round(v / 1e6, 1) for v in q["world_vnd_per_luong"]]},
        ],
    }

    # C4: Premium distribution histogram (all 17y)
    import numpy as np
    prem = spread["premium_pct"].dropna()
    counts, edges = np.histogram(prem, bins=40)
    charts["c4_premium_hist"] = {
        "labels": [round((edges[i] + edges[i + 1]) / 2, 1) for i in range(len(counts))],
        "datasets": [{"label": "Số ngày", "data": [int(c) for c in counts]}],
    }

    # C5: Bid-ask spread yearly
    sp_y = pd.read_csv(OUT_DIR / "bidask_spread_yearly.csv")
    charts["c5_bidask_yearly"] = {
        "labels": sp_y["year"].tolist(),
        "datasets": [
            {"label": "Spread TB (%)", "data": sp_y["mean_spread_pct"].tolist(),
             "type": "bar"},
            {"label": "Spread max (%)", "data": sp_y["max_spread_pct"].tolist(),
             "type": "line"},
        ],
    }

    # C6: Volatility & drawdown yearly
    vd = pd.read_csv(OUT_DIR / "vol_drawdown_yearly.csv")
    charts["c6_vol_drawdown"] = {
        "labels": vd["year"].tolist(),
        "datasets": [
            {"label": "Volatility năm (%)", "data": vd["vol_annualized_pct"].tolist(),
             "type": "bar"},
            {"label": "Max drawdown (%)", "data": vd["max_drawdown_pct"].tolist(),
             "type": "line"},
        ],
    }

    # C7: Ring vs bar yearly
    rvb = pd.read_csv(OUT_DIR / "ring_vs_bar_yearly.csv")
    charts["c7_ring_vs_bar"] = {
        "labels": rvb["year"].tolist(),
        "datasets": [
            {"label": "Bar đắt hơn ring TB (%)", "data": rvb["mean_diff_pct"].tolist(),
             "type": "bar"},
            {"label": "Max (%)", "data": rvb["max_diff_pct"].tolist(), "type": "line"},
            {"label": "Min (%)", "data": rvb["min_diff_pct"].tolist(), "type": "line"},
        ],
    }

    # C8: Lag correlation
    summary = json.loads((OUT_DIR / "summary.json").read_text())
    lc = summary["lag_correlation"]["corrs_by_lag_days"]
    charts["c8_lag_corr"] = {
        "labels": [f"{k}d" for k in lc],
        "datasets": [{"label": "Correlation r",
                      "data": [lc[k] for k in lc], "type": "bar"}],
    }

    # C9: SJC vs world zoom 2020-2026 (monthly)
    z = spread[spread["date"] >= "2020-01-01"].set_index("date")[
        ["sell_vnd", "world_vnd_per_luong"]
    ].resample("MS").mean().dropna()
    charts["c9_zoom_2020"] = {
        "labels": [d.strftime("%m/%Y") for d in z.index],
        "datasets": [
            {"label": "SJC bán (triệu/lượng)",
             "data": [round(v / 1e6, 1) for v in z["sell_vnd"]]},
            {"label": "Vàng QT quy đổi (triệu/lượng)",
             "data": [round(v / 1e6, 1) for v in z["world_vnd_per_luong"]]},
        ],
    }

    # C10: Annual return SJC vs world (both VND/lượng equivalent)
    sa = spread.copy()
    sa["year"] = sa["date"].dt.year
    yr = sa.groupby("year").agg(
        sjc=("sell_vnd", "last"), world=("world_vnd_per_luong", "last"))
    yr_ret = yr.pct_change() * 100
    charts["c10_annual_return"] = {
        "labels": [int(y) for y in yr_ret.index],
        "datasets": [
            {"label": "SJC (%)", "data": yr_ret["sjc"].round(1).tolist(),
             "type": "bar"},
            {"label": "Vàng QT (%)", "data": yr_ret["world"].round(1).tolist(),
             "type": "line"},
        ],
    }

    (OUT_DIR / "chart_data.json").write_text(
        json.dumps(charts, ensure_ascii=False, indent=2, default=str)
    )
    print(f"Exported {len(charts)} chart datasets to {OUT_DIR / 'chart_data.json'}")
    for k, v in charts.items():
        print(f"  {k}: {len(v['labels'])} pts")


if __name__ == "__main__":
    main()
