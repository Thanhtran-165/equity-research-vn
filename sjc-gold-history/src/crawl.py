"""Crawl SJC gold price history from sjc.com.vn.

sjc.com.vn sits behind Cloudflare, which fingerprints TLS (JA3/JA4) to
distinguish real browsers from automation libraries. Plain `requests`/
`httpx` use OpenSSL's fingerprint and get a 403. We use `curl_cffi`, which
impersonates Chrome's exact TLS handshake, so Cloudflare treats us as a
genuine browser.

The API rejects windows >= 90 days ("Chỉ được xem Giá trong khoảng dưới 90
ngày"). We chunk [start, end] into 89-day windows and call per window.

Usage (CLI):
    python -m src.crawl backfill                  # 22/07/2009 → today
    python -m src.crawl backfill --start 2020-01-01 --end 2026-07-08
    python -m src.crawl update                    # incremental, last 89 days
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from curl_cffi import requests as cffi_requests

from .config import (
    DEFAULT_GOLD_PRICE_ID,
    EARLIEST_DATE,
    MAX_WINDOW_DAYS,
    PRICE_SERVICE_URL,
    SJC_URL,
)

# Where raw JSON chunks are written (one file per window).
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


# --------------------------------------------------------------------------- #
# Window helpers
# --------------------------------------------------------------------------- #
def date_range_windows(
    start: date, end: date, window_days: int = MAX_WINDOW_DAYS
) -> list[tuple[date, date]]:
    """Split [start, end] into consecutive inclusive windows of <= window_days.

    Each window is <= MAX_WINDOW_DAYS so the API never rejects it.
    """
    windows: list[tuple[date, date]] = []
    cur = start
    while cur <= end:
        nxt = min(cur + timedelta(days=window_days - 1), end)
        windows.append((cur, nxt))
        cur = nxt + timedelta(days=1)
    return windows


def to_dmy(d: date) -> str:
    """API expects DD/MM/YYYY."""
    return d.strftime("%d/%m/%Y")


def to_iso(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def parse_iso(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


# --------------------------------------------------------------------------- #
# HTTP session (Cloudflare-aware via curl_cffi)
# --------------------------------------------------------------------------- #
class SjcCrawler:
    """A curl_cffi session impersonating Chrome. Stateful (cookies persist).

    Cloudflare's JS challenge is solved implicitly: the TLS fingerprint +
    cookie jar from impersonating Chrome is enough — no browser needed.
    """

    def __init__(self, impersonate: str = "chrome"):
        self.session = cffi_requests.Session(impersonate=impersonate)
        self._warmed = False

    def start(self) -> "SjcCrawler":
        """Load the chart page once to seed CF cookies."""
        r = self.session.get(SJC_URL, timeout=30)
        if r.status_code != 200 or "select-province" not in r.text:
            raise RuntimeError(
                f"Warm-up failed: status={r.status_code}, "
                f"isCF={'Just a moment' in r.text}"
            )
        self._warmed = True
        return self

    def fetch_window(
        self,
        gold_price_id: int,
        frm: date,
        to: date,
        max_retries: int = 4,
    ) -> list[dict]:
        """Fetch one <=89-day window with retry on transient errors.

        Returns the raw `data` array of points. Each point:
        {Id, TypeName, BranchName, Buy, BuyValue, Sell, SellValue,
         BuyDiffer, BuyDifferValue, SellDiffer, SellDifferValue,
         GroupDate: "/Date(<epoch_ms>)/"}
        """
        if not self._warmed:
            self.start()

        last_err: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                r = self.session.post(
                    PRICE_SERVICE_URL,
                    data={
                        "method": "GetGoldPriceHistory",
                        "goldPriceId": str(gold_price_id),
                        "fromDate": to_dmy(frm),
                        "toDate": to_dmy(to),
                    },
                    headers={
                        "X-Requested-With": "XMLHttpRequest",
                        "Content-Type": "application/x-www-form-urlencoded; "
                                        "charset=UTF-8",
                        "Referer": SJC_URL,
                        "Origin": "https://sjc.com.vn",
                    },
                    timeout=30,
                )
            except Exception as e:  # noqa: BLE001
                last_err = e
                time.sleep(2 * attempt)
                continue

            # Cloudflare re-challenged: re-seed cookies and retry.
            if r.status_code == 403 or "Just a moment" in r.text:
                print(f"      (CF challenge attempt {attempt}/{max_retries}; "
                      f"re-warming)")
                self._warmed = False
                time.sleep(3 * attempt)
                try:
                    self.start()
                except Exception as e:  # noqa: BLE001
                    last_err = e
                continue

            if r.status_code != 200:
                last_err = RuntimeError(f"HTTP {r.status_code}")
                if attempt < max_retries:
                    time.sleep(2 * attempt)
                    continue
                raise RuntimeError(
                    f"API error {frm}→{to}: {last_err}"
                )

            body = r.json()
            if not body.get("success", False):
                msg = body.get("message", "")
                # "Invalid chart or period" / range-limit: treat as empty.
                if "90 ngày" in msg or "Invalid" in msg:
                    return []
                raise RuntimeError(f"API success=false for {frm}→{to}: {msg}")
            return body.get("data") or []

        raise RuntimeError(
            f"API error {frm}→{to}: exhausted {max_retries} retries. "
            f"Last: {last_err}"
        )

    def close(self) -> None:
        self.session.close()


# --------------------------------------------------------------------------- #
# Disk I/O for raw chunks
# --------------------------------------------------------------------------- #
def raw_path(gold_price_id: int, frm: date, to: date) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    return RAW_DIR / f"sjc_id{gold_price_id}_{to_iso(frm)}_{to_iso(to)}.json"


def save_raw(gold_price_id: int, frm: date, to: date, points: list[dict]) -> Path:
    p = raw_path(gold_price_id, frm, to)
    payload = {
        "gold_price_id": gold_price_id,
        "from": to_iso(frm),
        "to": to_iso(to),
        "fetched_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "count": len(points),
        "data": points,
    }
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return p


def existing_windows(gold_price_id: int) -> set[tuple[date, date]]:
    """Windows already on disk (for skip/resume support)."""
    out = set()
    if not RAW_DIR.exists():
        return out
    prefix = f"sjc_id{gold_price_id}_"
    for f in RAW_DIR.glob(f"{prefix}*.json"):
        stem = f.stem  # sjc_id1_2020-01-01_2020-03-30
        try:
            _, _, s, e = stem.split("_")
            out.add((parse_iso(s), parse_iso(e)))
        except ValueError:
            continue
    return out


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def crawl_range(
    start: date,
    end: date,
    gold_price_id: int = DEFAULT_GOLD_PRICE_ID,
    skip_existing: bool = True,
    sleep_between: float = 0.8,
) -> dict:
    """Crawl [start, end] in 89-day windows, writing raw JSON per window."""
    windows = date_range_windows(start, end)
    summary = {
        "gold_price_id": gold_price_id,
        "start": to_iso(start),
        "end": to_iso(end),
        "windows_total": len(windows),
        "windows_skipped": 0,
        "windows_fetched": 0,
        "points_total": 0,
        "windows_empty": 0,
        "errors": [],
    }

    done = existing_windows(gold_price_id) if skip_existing else set()
    crawler = SjcCrawler().start()
    try:
        for i, (frm, to) in enumerate(windows, 1):
            if (frm, to) in done:
                summary["windows_skipped"] += 1
                continue
            try:
                pts = crawler.fetch_window(gold_price_id, frm, to)
                save_raw(gold_price_id, frm, to, pts)
                summary["windows_fetched"] += 1
                summary["points_total"] += len(pts)
                if not pts:
                    summary["windows_empty"] += 1
                tag = "ok" if pts else "EMPTY"
                print(
                    f"  [{i}/{len(windows)}] {to_iso(frm)} → {to_iso(to)}: "
                    f"{len(pts)} pts [{tag}]"
                )
            except Exception as e:  # noqa: BLE001
                summary["errors"].append(f"{to_iso(frm)}→{to_iso(to)}: {e}")
                print(f"  [{i}/{len(windows)}] {to_iso(frm)} → {to_iso(to)}: "
                      f"ERROR {e}")
            time.sleep(sleep_between)
    finally:
        crawler.close()

    print(
        f"\nDone: {summary['windows_fetched']} fetched, "
        f"{summary['windows_skipped']} skipped, "
        f"{summary['windows_empty']} empty, "
        f"{summary['points_total']} points total."
    )
    if summary["errors"]:
        print(f"  ⚠ {len(summary['errors'])} errors.")
    return summary


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description="Crawl SJC gold price history.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_back = sub.add_parser("backfill", help="Crawl a date range (default: full).")
    p_back.add_argument("--start", default=EARLIEST_DATE, help="YYYY-MM-DD")
    p_back.add_argument("--end", default=None, help="YYYY-MM-DD (default: today)")
    p_back.add_argument("--gold-price-id", type=int, default=DEFAULT_GOLD_PRICE_ID)
    p_back.add_argument("--no-skip", action="store_true", help="re-fetch existing")

    p_up = sub.add_parser("update", help="Incremental: last 89 days to today.")
    p_up.add_argument("--gold-price-id", type=int, default=DEFAULT_GOLD_PRICE_ID)

    args = ap.parse_args()

    if args.cmd == "backfill":
        start = parse_iso(args.start)
        end = parse_iso(args.end) if args.end else date.today()
        crawl_range(
            start, end,
            gold_price_id=args.gold_price_id,
            skip_existing=not args.no_skip,
        )
    elif args.cmd == "update":
        end = date.today()
        start = end - timedelta(days=MAX_WINDOW_DAYS - 1)
        crawl_range(
            start, end,
            gold_price_id=args.gold_price_id,
            skip_existing=False,  # update always overwrites the trailing window
        )


if __name__ == "__main__":
    main()
