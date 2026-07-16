"""Compute the SJC vs international gold spread / premium.

The headline question: how much more (or less) does SJC gold cost in Vietnam
compared to the equivalent amount of world gold, expressed in VND per lượng?

Conversion:
  - 1 lượng (SJC) = 37.5 g  (tael, thường lượng vàng SJC = 1.20567 troy oz)
  - 1 troy oz     = 31.1034768 g
  - So 1 lượng    = 37.5 / 31.1034768 = 1.20565 troy oz

  world_vnd_per_luong = gold_usd_oz × usd_vnd × (37.5 / 31.1034768)

  spread_vnd   = sjc_sell_vnd − world_vnd_per_luong
  premium_pct  = spread_vnd / world_vnd_per_luong × 100

SJC daily close = last price update of each trading day (from sjc_master).

Usage:
    python -m src.spread              # build spread dataset + yearly stats
    python -m src.spread --plot       # also render chart PNG
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .merge import PROCESSED_DIR, VN_TZ

# 1 SJC lượng = 37.5 g = 1.20565 troy oz (37.5 / 31.1034768).
LUONG_GRAMS = 37.5
TROY_OZ_GRAMS = 31.1034768
LUONG_TO_TROY_OZ = LUONG_GRAMS / TROY_OZ_GRAMS  # ≈ 1.20565

CHART_OUT = PROCESSED_DIR / "sjc_vs_world_premium.png"


def load_sjc_daily(master_path: Path) -> pd.DataFrame:
    """Collapse intraday SJC master to one row per day (closing price)."""
    df = pd.read_parquet(master_path)
    # Canonical SJC 1L in HCM.
    df = df[df["gold_price_id"] == 1].copy()
    df["ts"] = pd.to_datetime(df["timestamp"])
    if df["ts"].dt.tz is None:
        df["ts"] = df["ts"].dt.tz_localize(VN_TZ)
    else:
        df["ts"] = df["ts"].dt.tz_convert(VN_TZ)
    df["date"] = df["ts"].dt.date
    # Closing = last update of the day.
    daily = (df.sort_values("ts")
             .groupby("date", as_index=False)
             .last()[["date", "buy_vnd", "sell_vnd", "ts"]])
    daily = daily.rename(columns={"ts": "sjc_close_time"})
    daily["date"] = pd.to_datetime(daily["date"])
    return daily


def build_spread(master_path: Path, fx_path: Path) -> pd.DataFrame:
    """Join SJC daily close with world gold (VND/lượng) and compute spread."""
    sjc = load_sjc_daily(master_path)
    fx = pd.read_parquet(fx_path)
    fx["date"] = pd.to_datetime(fx["date"])

    df = pd.merge(sjc, fx, on="date", how="inner")
    df = df.dropna(subset=["sell_vnd", "gold_usd_oz", "usd_vnd"])

    # World gold price in VND per lượng.
    df["world_vnd_per_luong"] = (df["gold_usd_oz"]
                                 * df["usd_vnd"]
                                 * LUONG_TO_TROY_OZ)
    # Spread & premium (use SJC SELL price as the retail reference).
    df["spread_vnd"] = df["sell_vnd"] - df["world_vnd_per_luong"]
    df["premium_pct"] = df["spread_vnd"] / df["world_vnd_per_luong"] * 100

    df = df.sort_values("date").reset_index(drop=True)
    cols = ["date", "sell_vnd", "buy_vnd", "gold_usd_oz", "usd_vnd",
            "world_vnd_per_luong", "spread_vnd", "premium_pct",
            "sjc_close_time"]
    return df[cols]


def yearly_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Premium statistics by calendar year."""
    d = df.copy()
    d["year"] = d["date"].dt.year
    g = d.groupby("year").agg(
        days=("premium_pct", "size"),
        prem_mean_pct=("premium_pct", "mean"),
        prem_min_pct=("premium_pct", "min"),
        prem_max_pct=("premium_pct", "max"),
        prem_med_pct=("premium_pct", "median"),
        sjc_mean_m=("sell_vnd", lambda s: s.mean() / 1e6),
        world_mean_m=("world_vnd_per_luong", lambda s: s.mean() / 1e6),
        spread_mean_m=("spread_vnd", lambda s: s.mean() / 1e6),
    ).round({"prem_mean_pct": 2, "prem_min_pct": 2, "prem_max_pct": 2,
             "prem_med_pct": 2, "sjc_mean_m": 1, "world_mean_m": 1,
             "spread_mean_m": 1})
    return g.reset_index()


def render_chart(df: pd.DataFrame, out: Path = CHART_OUT) -> Path:
    """Plot SJC vs world-gold (VND/lượng) + premium %. Needs matplotlib."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8), sharex=True,
                                   gridspec_kw={"height_ratios": [2, 1]})
    ax1.plot(df["date"], df["sell_vnd"] / 1e6, label="SJC bán (triệu/lượng)", lw=1.0)
    ax1.plot(df["date"], df["world_vnd_per_luong"] / 1e6,
             label="Vàng QT quy đổi (triệu/lượng)", lw=1.0, alpha=0.85)
    ax1.set_ylabel("Giá (triệu VND / lượng)")
    ax1.set_title("SJC vs Vàng thế giới (quy đổi VND/lượng) — 2009→nay")
    ax1.legend(loc="upper left")
    ax1.grid(alpha=0.3)

    ax2.fill_between(df["date"], df["premium_pct"], 0,
                     where=df["premium_pct"] >= 0, color="red", alpha=0.4,
                     label="Premium (+)")
    ax2.fill_between(df["date"], df["premium_pct"], 0,
                     where=df["premium_pct"] < 0, color="green", alpha=0.4,
                     label="Discount (−)")
    ax2.axhline(0, color="black", lw=0.6)
    ax2.set_ylabel("Premium SJC vs QT (%)")
    ax2.set_xlabel("Năm")
    ax2.legend(loc="upper left")
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(out, dpi=110)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="SJC vs world gold spread/premium.")
    ap.add_argument("--master", default=str(PROCESSED_DIR / "sjc_master.parquet"))
    ap.add_argument("--fx", default=str(PROCESSED_DIR / "fx_gold.parquet"))
    ap.add_argument("--plot", action="store_true", help="render chart PNG")
    args = ap.parse_args()

    df = build_spread(Path(args.master), Path(args.fx))
    out_parquet = PROCESSED_DIR / "sjc_spread.parquet"
    out_csv = PROCESSED_DIR / "sjc_spread.csv"
    df.to_parquet(out_parquet, index=False)
    df.to_csv(out_csv, index=False)

    print(f"Spread dataset: {len(df)} rows, "
          f"{df['date'].min().date()} → {df['date'].max().date()}")
    print(f"  Parquet: {out_parquet}")
    print(f"  CSV:     {out_csv}")

    stats = yearly_stats(df)
    print("\n=== Premium SJC vs vàng QT, theo năm ===")
    print(stats.to_string(index=False))
    print(f"\nConversion factor: 1 lượng = {LUONG_TO_TROY_OZ:.5f} troy oz "
          f"(37.5 g / 31.1035 g)")

    if args.plot:
        p = render_chart(df)
        print(f"\nChart: {p}")

    print("\n=== Recent 5 days ===")
    print(df.tail(5)[["date", "sell_vnd", "world_vnd_per_luong",
                      "spread_vnd", "premium_pct"]].to_string(index=False))


if __name__ == "__main__":
    main()
