"""Fetch XAUUSD (gold) and USDVND daily history.

Sources:
  - Yahoo Finance chart API (via curl_cffi to pass anti-bot):
      * GC=F  — COMEX gold futures (proxy for spot XAUUSD). Covers 2009→today.
      * USDVND=X — USD/VND spot. Covers ~2009→mid-2025 (Yahoo stalled).
  - fawazahmed0 currency-api (via jsdelivr CDN): backup for USDVND recent
    (2024→today), used to fill Yahoo's trailing gap.

Output: data/processed/fx_gold.parquet + .csv with columns
  date, gold_usd_oz (GC=F close), usd_vnd

Anomalies (Yahoo feed glitches, e.g. USDVND=21.x) are filtered with a
plausibility band.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
from curl_cffi import requests as cffi

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Plausibility bands (VND per USD, USD per troy ounce). Yahoo's USDVND feed
# occasionally glitches to ~21 (off by ~1000x) — drop those.
USDVND_MIN = 15_000
USDVND_MAX = 30_000
USDCNY_MIN = 6.0
USDCNY_MAX = 8.5
GOLD_MIN = 800     # gold never below ~$800/oz in our 2009+ era
GOLD_MAX = 6_000


# --------------------------------------------------------------------------- #
# Yahoo Finance chart API
# --------------------------------------------------------------------------- #
def _yahoo_chart(symbol: str, start: date, end: date) -> pd.DataFrame:
    """Pull daily OHLC for one Yahoo symbol between start..end (inclusive)."""
    p1 = int(datetime(start.year, start.month, start.day, tzinfo=timezone.utc).timestamp())
    p2 = int(datetime(end.year, end.month, end.day, tzinfo=timezone.utc).timestamp())
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        f"?period1={p1}&period2={p2}&interval=1d"
    )
    r = cffi.get(url, impersonate="chrome", timeout=30,
                 headers={"User-Agent": "Mozilla/5.0"})
    if r.status_code != 200:
        raise RuntimeError(f"Yahoo {symbol}: HTTP {r.status_code}")
    j = r.json()
    res = (j.get("chart") or {}).get("result")
    if not res:
        raise RuntimeError(f"Yahoo {symbol}: no result (delisted?)")
    res = res[0]
    ts = res.get("timestamp", [])
    quote = res.get("indicators", {}).get("quote", [{}])[0]
    rows = []
    for i, t in enumerate(ts):
        close = quote.get("close", [None])[i] if i < len(quote.get("close", [])) else None
        if close is None:
            continue
        rows.append({
            "date": datetime.fromtimestamp(t, tz=timezone.utc).date(),
            "close": float(close),
        })
    return pd.DataFrame(rows)


def fetch_gold(start: date, end: date) -> pd.DataFrame:
    """Gold futures (GC=F) daily close, USD/troy oz. Filter implausible."""
    df = _yahoo_chart("GC=F", start, end)
    df = df[(df["close"] >= GOLD_MIN) & (df["close"] <= GOLD_MAX)]
    df = df.rename(columns={"close": "gold_usd_oz"})
    return df.drop_duplicates("date").sort_values("date").reset_index(drop=True)


def fetch_usdcny(start: date, end: date) -> pd.DataFrame:
    """USD/CNY daily from Yahoo. Filter implausible values."""
    df = _yahoo_chart("CNY=X", start, end)
    df = df[(df["close"] >= USDCNY_MIN) & (df["close"] <= USDCNY_MAX)]
    df = df.rename(columns={"close": "usd_cny"})
    return df.drop_duplicates("date").sort_values("date").reset_index(drop=True)


def fetch_usdvnd_yahoo(start: date, end: date) -> pd.DataFrame:
    """USDVND daily from Yahoo. Filter the ~21.x feed glitches."""
    df = _yahoo_chart("USDVND=X", start, end)
    df = df[(df["close"] >= USDVND_MIN) & (df["close"] <= USDVND_MAX)]
    df = df.rename(columns={"close": "usd_vnd"})
    return df.drop_duplicates("date").sort_values("date").reset_index(drop=True)


# --------------------------------------------------------------------------- #
# fawazahmed0 backup (for recent USDVND)
# --------------------------------------------------------------------------- #
def fetch_usdvnd_fawaz(start: date, end: date) -> pd.DataFrame:
    """USDVND from fawazahmed0 currency-api (jsdelivr CDN). Per-date fetch.

    Coverage starts ~late 2024. Used to backfill Yahoo's trailing gap.
    """
    rows = []
    cur = start
    # Be polite — small sleep every batch.
    n = 0
    while cur <= end:
        url = (f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@"
               f"{cur.isoformat()}/v1/currencies/usd.json")
        try:
            r = cffi.get(url, impersonate="chrome", timeout=15)
            if r.status_code == 200:
                j = r.json()
                vnd = (j.get("usd") or {}).get("vnd")
                d = j.get("date")
                if vnd and d:
                    dd = datetime.strptime(d, "%Y-%m-%d").date()
                    if USDVND_MIN <= vnd <= USDVND_MAX:
                        rows.append({"date": dd, "usd_vnd": float(vnd)})
        except Exception:  # noqa: BLE001
            pass
        n += 1
        if n % 20 == 0:
            time.sleep(0.5)
        cur += timedelta_days(1)
    return pd.DataFrame(rows).drop_duplicates("date").sort_values("date").reset_index(drop=True)


def timedelta_days(n: int):
    from datetime import timedelta
    return timedelta(days=n)


# --------------------------------------------------------------------------- #
# Merge USDVND sources
# --------------------------------------------------------------------------- #
def fetch_usdvnd(start: date, end: date) -> pd.DataFrame:
    """Combine Yahoo (long history) + fawaz (recent gap-fill)."""
    y = fetch_usdvnd_yahoo(start, end)
    # If Yahoo's last date is well before `end`, fill the gap with fawaz.
    y_end = y["date"].max() if len(y) else start
    if y_end < end:
        gap_start = y_end + timedelta_days(1)
        print(f"  filling USDVND gap {gap_start} → {end} via fawazahmed0 ...")
        f = fetch_usdvnd_fawaz(gap_start, end)
        if len(f):
            print(f"    fawaz rows: {len(f)} ({f['date'].min()} → {f['date'].max()})")
        y = pd.concat([y, f], ignore_index=True)
    return y.drop_duplicates("date", keep="last").sort_values("date").reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def build_fx_gold(start: date, end: date, out_dir: Path = PROCESSED_DIR) -> dict:
    print(f"Fetching gold (GC=F) {start} → {end} ...")
    gold = fetch_gold(start, end)
    print(f"  gold rows: {len(gold)} ({gold['date'].min()} → {gold['date'].max()})")

    print(f"Fetching USDVND {start} → {end} ...")
    vnd = fetch_usdvnd(start, end)
    print(f"  usdvnd rows: {len(vnd)} ({vnd['date'].min()} → {vnd['date'].max()})")

    print(f"Fetching USD/CNY {start} → {end} ...")
    cny = fetch_usdcny(start, end)
    print(f"  usdcny rows: {len(cny)} ({cny['date'].min()} → {cny['date'].max()})")

    df = pd.merge(gold, vnd, on="date", how="outer")
    df = pd.merge(df, cny, on="date", how="outer").sort_values("date").reset_index(drop=True)

    out_dir.mkdir(parents=True, exist_ok=True)
    pq = out_dir / "fx_gold.parquet"
    csv = out_dir / "fx_gold.csv"
    df.to_parquet(pq, index=False)
    df.to_csv(csv, index=False)
    return {
        "parquet": str(pq), "csv": str(csv), "rows": len(df),
        "gold_rows": int(df["gold_usd_oz"].notna().sum()),
        "vnd_rows": int(df["usd_vnd"].notna().sum()),
        "cny_rows": int(df["usd_cny"].notna().sum()),
        "both_rows": int((df["gold_usd_oz"].notna() & df["usd_vnd"].notna()).sum()),
        "range": f"{df['date'].min()} → {df['date'].max()}",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch GC=F + USDVND daily history.")
    ap.add_argument("--start", default="2009-07-22")
    ap.add_argument("--end", default=None, help="default: today")
    args = ap.parse_args()
    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    end = datetime.strptime(args.end, "%Y-%m-%d").date() if args.end else date.today()
    info = build_fx_gold(start, end)
    print(f"\nfx_gold dataset: {info['rows']} rows, {info['range']}")
    print(f"  with gold: {info['gold_rows']}, with usdvnd: {info['vnd_rows']}, "
          f"with usdcny: {info.get('cny_rows','?')}, with both gold+vnd: {info['both_rows']}")
    print(f"  Parquet: {info['parquet']}")
    print(f"  CSV:     {info['csv']}")


if __name__ == "__main__":
    main()
