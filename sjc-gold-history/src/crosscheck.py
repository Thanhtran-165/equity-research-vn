"""Cross-check SJC master data against an independent source (giavang.org).

giavang.org publishes per-day SJC history as static HTML pages:
    https://giavang.org/trong-nuoc/sjc/lich-su/YYYY-MM-DD.html
Each page contains a table with (branch, type, buy x1000đ/lượng, sell x1000đ/lượng,
timestamp). Data coverage: 2009-07-22 → 2025-04-21 (stale after that).

This module samples N days from our master dataset, fetches the corresponding
giavang.org page, and reports the max abs difference in buy/sell prices.
A difference of 0 means the two sources agree.

Usage:
    python -m src.crosscheck                    # sample 20 random days
    python -m src.crosscheck --n 50 --seed 1
"""
from __future__ import annotations

import argparse
import random
import re
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from .config import DEFAULT_GOLD_PRICE_ID
from .merge import PROCESSED_DIR, VN_TZ


GIAVANG_URL = "https://giavang.org/trong-nuoc/sjc/lich-su/{d}.html"
# giavang.org prices are in x1000đ/lượng (e.g. "74.000" = 74,000,000 VND/lượng).
# Multiplier to VND: 1000.
GIAVANG_FACTOR = 1000

# Only cross-check the canonical SJC 1L price in HCM (gold_price_id 1).
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


def _fetch_giavang_day(d: date) -> dict | None:
    """Return {'buy_vnd': int, 'sell_vnd': int} from a giavang.org day page.

    Looks for the closing-price table row for "Vàng SJC 1L..." in Hồ Chí Minh.
    Returns None if the page has no data (stale future dates, weekends, etc.).
    """
    url = GIAVANG_URL.format(d=d.isoformat())
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
    except requests.RequestException:
        return None
    if r.status_code != 200 or "x1000đ/lượng" not in r.text:
        return None

    html = r.text
    # Find the first <tbody> after "Đơn vị". The closing-price table lists
    # HCM SJC 1L first. Pull buy/sell (x1000đ/lượng, '.' = thousands sep).
    i = html.find("Đơn vị")
    seg = html[i : i + 4000] if i >= 0 else html
    # Row pattern: <tr><th...>Hồ Chí Minh</th><td>Vàng SJC 1L...</td>
    #              <td...>74.000</td><td...>77.000</td><td...>HH:MM:SS ...</td>
    m = re.search(
        r"Hồ Chí Minh</th>\s*<td[^>]*>Vàng SJC 1L[^<]*</td>"
        r'\s*<td[^>]*>([0-9.]+)</td>\s*<td[^>]*>([0-9.]+)</td>',
        seg,
    )
    if not m:
        return None
    buy = int(m.group(1).replace(".", "")) * GIAVANG_FACTOR
    sell = int(m.group(2).replace(".", "")) * GIAVANG_FACTOR
    return {"buy_vnd": buy, "sell_vnd": sell}


def crosscheck(master_path: Path, n: int = 20, seed: int = 0) -> pd.DataFrame:
    """Sample n days, compare master's last price of the day to giavang.org."""
    # Prefer parquet (typed timestamps); fall back to CSV with mixed parsing.
    if master_path.suffix == ".parquet":
        df = pd.read_parquet(master_path)
        df["ts"] = pd.to_datetime(df["timestamp"])
    else:
        df = pd.read_csv(master_path)
        df["ts"] = pd.to_datetime(df["timestamp"], format="mixed", utc=True)
    # Canonical ID + only dates within giavang.org's coverage (<= 2025-04-21).
    df = df[(df["gold_price_id"] == DEFAULT_GOLD_PRICE_ID)]
    if df["ts"].dt.tz is None:
        df["ts"] = df["ts"].dt.tz_localize(VN_TZ)
    else:
        df["ts"] = df["ts"].dt.tz_convert(VN_TZ)
    df["d"] = df["ts"].dt.date

    cutoff = date(2025, 4, 21)
    days = sorted({d for d in df["d"] if d <= cutoff})
    if not days:
        print("No days within giavang.org coverage to compare.")
        return pd.DataFrame()

    rng = random.Random(seed)
    sample = rng.sample(days, min(n, len(days)))

    rows = []
    for idx, d in enumerate(sample, 1):
        day_df = df[df["d"] == d].sort_values("ts")
        if day_df.empty:
            continue
        last = day_df.iloc[-1]  # closing (last update) of the day
        gv = _fetch_giavang_day(d)
        if gv is None:
            rows.append({
                "date": d, "master_buy": int(last.buy_vnd),
                "master_sell": int(last.sell_vnd),
                "gv_buy": None, "gv_sell": None,
                "diff_buy": None, "diff_sell": None, "status": "no_gv_data",
            })
        else:
            rows.append({
                "date": d,
                "master_buy": int(last.buy_vnd), "master_sell": int(last.sell_vnd),
                "gv_buy": gv["buy_vnd"], "gv_sell": gv["sell_vnd"],
                "diff_buy": int(last.buy_vnd) - gv["buy_vnd"],
                "diff_sell": int(last.sell_vnd) - gv["sell_vnd"],
                "status": "ok",
            })
        time.sleep(0.3)  # be polite to giavang.org
        if idx % 5 == 0:
            print(f"  ...{idx}/{len(sample)} checked")

    res = pd.DataFrame(rows)
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description="Cross-check master vs giavang.org.")
    ap.add_argument("--master", default=str(PROCESSED_DIR / "sjc_master.parquet"),
                    help="path to sjc_master.parquet (or .csv)")
    ap.add_argument("--n", type=int, default=20, help="sample size")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    master_path = Path(args.master)
    if not master_path.exists():
        raise SystemExit(f"Master not found: {master_path}. Run `python -m src.merge` first.")

    print(f"Cross-checking {args.n} random days against giavang.org ...")
    res = crosscheck(master_path, n=args.n, seed=args.seed)
    if res.empty:
        return

    ok = res[res["status"] == "ok"]
    print(f"\nResults: {len(ok)} comparable, {len(res) - len(ok)} had no giavang.org data.")
    if len(ok):
        print(f"  max |Δbuy| : {ok['diff_buy'].abs().max():,.0f} VND")
        print(f"  max |Δsell|: {ok['diff_sell'].abs().max():,.0f} VND")
        exact = ((ok["diff_buy"] == 0) & (ok["diff_sell"] == 0)).sum()
        print(f"  exact matches (both Δ=0): {exact}/{len(ok)}")
        worst = ok.reindex(ok["diff_sell"].abs().sort_values(ascending=False).index)
        print("\n  Largest discrepancies:")
        print(worst[["date", "master_buy", "gv_buy", "diff_buy",
                     "master_sell", "gv_sell", "diff_sell"]].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
