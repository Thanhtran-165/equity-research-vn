"""Backtest the ★5 framework (premortem vòng 2 B.1 + B.2).

B.1: Do the 4 premium zones (<8 / 8-15 / 15-25 / >25%) actually have
     different forward drawdown profiles? If not, the thresholds are arbitrary.
B.2: Is the (premium, spread) 4x4 matrix populated, or are zones empty?

Also compute the natural percentile-based thresholds as an alternative
(P25/P50/P75) to compare with the hand-picked 8/15/25%.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .analytics import OUT_DIR, sjc_daily
from .merge import PROCESSED_DIR, build_master


def load_premium_spread_daily():
    """Daily SJC close with premium_pct and bidask spread_pct on same date."""
    master = build_master()
    d1 = sjc_daily(master, 1)
    d1["date"] = pd.to_datetime(d1["date"])
    spread = pd.read_parquet(PROCESSED_DIR / "sjc_spread.parquet")
    spread["date"] = pd.to_datetime(spread["date"])
    m = d1[["date", "close_sell", "spread_pct"]].merge(
        spread[["date", "premium_pct", "sell_vnd"]], on="date"
    )
    # keep sjc close from d1 (intraday-collapsed) for drawdown calc
    m = m.rename(columns={"close_sell": "sjc_close"})
    return m.sort_values("date").reset_index(drop=True)


def forward_drawdown(series: pd.Series, start_idx: int, horizon_days: int) -> float:
    """Max drawdown over the next `horizon_days` days from start_idx (%)."""
    end = min(start_idx + horizon_days, len(series))
    window = series.iloc[start_idx:end]
    if len(window) < 2:
        return 0.0
    cum = window
    runmax = cum.cummax()
    dd = (cum / runmax - 1) * 100
    return float(dd.min())


def backtest_premium_zones(m: pd.DataFrame, horizon: int = 252):
    """B.1: forward 12-month drawdown by premium zone."""
    zones = [
        ("Bình thường (<8%)", lambda p: p < 8),
        ("Căng (8-15%)", lambda p: (p >= 8) & (p < 15)),
        ("Rất căng (15-25%)", lambda p: (p >= 15) & (p < 25)),
        ("Hoảng loạn (>25%)", lambda p: p >= 25),
    ]
    results = []
    for name, fn in zones:
        mask = fn(m["premium_pct"]).fillna(False)
        idxs = m.index[mask].tolist()
        # only compute forward DD where we have `horizon` days ahead
        valid = [i for i in idxs if i + horizon <= len(m)]
        if not valid:
            results.append({"zone": name, "n_days": int(mask.sum()),
                            "n_with_horizon": 0, "fwd_dd_med": None,
                            "fwd_dd_p10": None, "fwd_dd_mean": None})
            continue
        dds = [forward_drawdown(m["sjc_close"], i, horizon) for i in valid]
        results.append({
            "zone": name,
            "n_days": int(mask.sum()),
            "n_with_horizon": len(valid),
            "fwd_dd_med": round(float(np.median(dds)), 1),
            "fwd_dd_p10": round(float(np.percentile(dds, 10)), 1),  # worst-decile
            "fwd_dd_mean": round(float(np.mean(dds)), 1),
        })
    return results


def natural_percentile_thresholds(m: pd.DataFrame):
    """Alternative to hand-picked: P25/P50/P75 of premium distribution."""
    p = m["premium_pct"].dropna()
    return {
        "P25": round(float(p.quantile(0.25)), 1),
        "P50": round(float(p.quantile(0.50)), 1),
        "P75": round(float(p.quantile(0.75)), 1),
        "P90": round(float(p.quantile(0.90)), 1),
        "mean": round(float(p.mean()), 1),
        "n": int(len(p)),
    }


def scatter_premium_spread(m: pd.DataFrame):
    """B.2: how many days fall in each cell of (premium zone × spread zone)?"""
    pzones = [("p<8", lambda p: p < 8), ("p8-15", lambda p: (p >= 8) & (p < 15)),
              ("p15-25", lambda p: (p >= 15) & (p < 25)), ("p>25", lambda p: p >= 25)]
    szones = [("s<1", lambda s: s < 1), ("s1-2", lambda s: (s >= 1) & (s < 2)),
              ("s2-3", lambda s: (s >= 3) & (s < 3)), ("s>3", lambda s: s >= 3)]
    # fix: spread zones should be <1 / 1-2 / 2-3 / >3
    szones = [("s<1%", lambda s: s < 1), ("s1-2%", lambda s: (s >= 1) & (s < 2)),
              ("s2-3%", lambda s: (s >= 2) & (s < 3)), ("s>3%", lambda s: s >= 3)]

    matrix = {}
    total_check = 0
    for pname, pf in pzones:
        row = {}
        for sname, sf in szones:
            mask = pf(m["premium_pct"]).fillna(False) & sf(m["spread_pct"]).fillna(False)
            n = int(mask.sum())
            row[sname] = n
            total_check += n
        matrix[pname] = row

    # % days in each cell
    n_total = len(m.dropna(subset=["premium_pct", "spread_pct"]))
    pct_matrix = {p: {s: round(v / n_total * 100, 1) for s, v in row.items()}
                  for p, row in matrix.items()}
    return {"counts": matrix, "pct": pct_matrix, "n_total": n_total,
            "check_sum": total_check}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m = load_premium_spread_daily()
    print(f"Loaded {len(m)} days, {m.date.min().date()} → {m.date.max().date()}")

    print("\n=== B.1: forward 12-month drawdown by premium zone ===")
    bt = backtest_premium_zones(m, horizon=252)
    for r in bt:
        print(f"  {r['zone']:25s}: n={r['n_days']:4d} (horizon:{r['n_with_horizon']:4d})  "
              f"fwd_dd med={r['fwd_dd_med']}%  P10(worst decile)={r['fwd_dd_p10']}%")

    print("\n=== Natural percentile thresholds (alternative) ===")
    pct = natural_percentile_thresholds(m)
    print(f"  P25={pct['P25']}  P50(med)={pct['P50']}  P75={pct['P75']}  P90={pct['P90']}  mean={pct['mean']}")

    print("\n=== B.2: (premium × spread) matrix — % days in each cell ===")
    sc = scatter_premium_spread(m)
    print(pd.DataFrame(sc["pct"]).to_string())
    print(f"\n  total days: {sc['n_total']}")

    summary = {"b1_backtest": bt, "percentile_thresholds": pct,
               "b2_scatter_matrix_pct": sc["pct"], "b2_total": sc["n_total"]}
    (OUT_DIR / "framework_backtest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n✅ Saved {OUT_DIR / 'framework_backtest.json'}")


if __name__ == "__main__":
    main()
