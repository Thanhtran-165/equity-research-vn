"""Incremental update: fetch recent data and rebuild the master dataset.

Typical cron usage (daily):
    python -m src.update            # refresh last 89 days, then rebuild master

This is a thin orchestrator: crawl the trailing window, then merge. The merge
step is idempotent — dedup keeps everything consistent regardless of overlaps.
"""
from __future__ import annotations

from datetime import date, timedelta

from .config import DEFAULT_GOLD_PRICE_ID, MAX_WINDOW_DAYS
from .crawl import crawl_range
from .merge import build_master, save_master


def update(
    gold_price_id: int = DEFAULT_GOLD_PRICE_ID,
    headless: bool = True,
    days: int = MAX_WINDOW_DAYS,
) -> dict:
    """Fetch the last `days` days (default 89) and rebuild the master dataset."""
    end = date.today()
    start = end - timedelta(days=days - 1)

    print(f"== Crawling trailing window {start} → {end} ==")
    summary = crawl_range(
        start, end,
        gold_price_id=gold_price_id,
        headless=headless,
        skip_existing=False,  # always overwrite the trailing window
    )

    print("\n== Rebuilding master dataset ==")
    df = build_master()
    info = save_master(df)
    info["crawl"] = summary
    print(f"Master: {info['rows']:,} rows, {info['unique_days']:,} days, "
          f"{info['date_min']} → {info['date_max']}")
    return info


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Incremental SJC update.")
    ap.add_argument("--gold-price-id", type=int, default=DEFAULT_GOLD_PRICE_ID)
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--days", type=int, default=MAX_WINDOW_DAYS)
    args = ap.parse_args()
    update(
        gold_price_id=args.gold_price_id,
        headless=not args.headed,
        days=args.days,
    )


if __name__ == "__main__":
    main()
