#!/usr/bin/env python3
"""
Fetch HNX Government Bond Yield Curve — daily backfill 2014→nay.

Endpoint: POST https://hnx.vn/ModuleReportBonds/Bond_YieldCurve/SearchAndNextPageYieldCurveData
Body: pDate=DD/MM/YYYY, pPageSize=50, pPageIndex=1
Output: data/raw/hnx_yield/hnx_yield_curve_daily.csv

Features:
- Checkpoint/resume: append-only, skip dates already in CSV
- Parallel requests (4 workers) for speed
- Skip holidays (response size < 1000 bytes = no data)
- SSL verify=False (HNX cert issue on macOS Python)
- Sleep 0.5s between requests per worker (polite)
- Retry 3x on failure
"""
import requests, urllib3, time, sys, os, csv, threading, queue
from datetime import date, timedelta, datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "https://hnx.vn/ModuleReportBonds/Bond_YieldCurve/SearchAndNextPageYieldCurveData"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://hnx.vn/",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "text/html, application/json, */*; q=0.01",
    "Accept-Language": "vi-VN,vi;q=0.9",
}
OUT_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "hnx_yield", "hnx_yield_curve_daily.csv")
OUT_CSV = os.path.abspath(OUT_CSV)

# Tenors HNX provides (map Vietnamese label → standard key)
TENOR_MAP = {
    "3 tháng": "3m", "6 tháng": "6m", "9 tháng": "9m",
    "1 năm": "1y", "2 năm": "2y", "3 năm": "3y",
    "5 năm": "5y", "7 năm": "7y", "10 năm": "10y", "15 năm": "15y",
}

def fetch_one(date_obj):
    """Fetch yield curve for a single date. Returns dict or None."""
    date_str = date_obj.strftime("%d/%m/%Y")
    for attempt in range(3):
        try:
            r = requests.post(URL, data={"pDate": date_str, "pPageSize": 50, "pPageIndex": 1},
                              headers=HEADERS, timeout=20, verify=False)
            if r.status_code == 200 and len(r.text) > 1000:
                return parse_html(date_obj, r.text)
            elif r.status_code == 200:
                return None  # holiday / no data (small response)
            time.sleep(1)
        except Exception:
            time.sleep(2)
    return "ERROR"

def parse_html(date_obj, html):
    """Parse HNX yield table HTML → dict of tenor: par_yield."""
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")
    if not tables:
        return None
    rows = tables[0].find_all("tr")
    if len(rows) < 2:
        return None
    result = {"date": date_obj.isoformat(), "tenors": {}}
    for row in rows[1:]:
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cells) >= 4 and cells[0] in TENOR_MAP:
            tenor = TENOR_MAP[cells[0]]
            # Par yield (col index 2) = benchmark; fallback spot_annual (col 3)
            par = cells[2].replace(",", ".") if cells[2] else None
            spot = cells[3].replace(",", ".") if cells[3] else None
            result["tenors"][tenor] = float(par) if par else (float(spot) if spot else None)
    return result if result["tenors"] else None

def load_done_dates():
    """Load dates already in CSV (for resume)."""
    done = set()
    if os.path.exists(OUT_CSV):
        with open(OUT_CSV, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("date"):
                    done.add(row["date"])
    return done

def append_rows(results):
    """Append results to CSV (thread-safe)."""
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    fieldnames = ["date"] + [f"{t}_par_yield" for t in TENOR_MAP.values()]
    file_exists = os.path.exists(OUT_CSV) and os.path.getsize(OUT_CSV) > 0
    with open(OUT_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for r in results:
            if r and r != "ERROR":
                row = {"date": r["date"]}
                for tenor_key in TENOR_MAP.values():
                    row[f"{tenor_key}_par_yield"] = r["tenors"].get(tenor_key)
                writer.writerow(row)

def main():
    start_date = date(2014, 1, 2)
    end_date = date.today()
    # Generate business days (skip Sat/Sun)
    all_dates = []
    d = start_date
    while d <= end_date:
        if d.weekday() < 5:  # Mon-Fri
            all_dates.append(d)
        d += timedelta(days=1)

    done = load_done_dates()
    todo = [d for d in all_dates if d.isoformat() not in done]
    print(f"Total dates: {len(all_dates)} | Already done: {len(done)} | To fetch: {len(todo)}", flush=True)
    if not todo:
        print("Nothing to do.", flush=True)
        return

    batch_size = 50  # append every 50 to be safe
    fetched = 0
    no_data = 0
    errors = 0
    buffer = []
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {}
        for i, d in enumerate(todo):
            futures[pool.submit(fetch_one, d)] = d
            # Stagger initial submission to avoid burst
            if (i + 1) % 4 == 0:
                time.sleep(0.15)

        for fut in as_completed(futures):
            d = futures[fut]
            try:
                result = fut.result()
            except Exception:
                result = "ERROR"
            fetched += 1
            if result == "ERROR":
                errors += 1
            elif result is None:
                no_data += 1
            else:
                buffer.append(result)

            # Append batch
            if len(buffer) >= batch_size:
                append_rows(buffer)
                buffer = []

            # Progress
            if fetched % 100 == 0:
                elapsed = time.time() - t0
                rate = fetched / elapsed if elapsed > 0 else 0
                remaining = (len(todo) - fetched) / rate if rate > 0 else 0
                print(f"  {fetched}/{len(todo)} ({rate:.1f}/s, ~{remaining/60:.1f}m left) "
                      f"| no_data:{no_data} err:{errors}", flush=True)

    # Final flush
    if buffer:
        append_rows(buffer)

    elapsed = time.time() - t0
    print(f"\n✅ Done in {elapsed/60:.1f}m", flush=True)
    print(f"   Fetched: {fetched} | With data: {fetched-no_data-errors} | No data (holiday): {no_data} | Errors: {errors}", flush=True)
    print(f"   Output: {OUT_CSV}", flush=True)

    # Verify
    if os.path.exists(OUT_CSV):
        import pandas as pd
        df = pd.read_csv(OUT_CSV)
        print(f"\n   CSV: {len(df)} rows | {df.date.min()} → {df.date.max()}")

if __name__ == "__main__":
    main()
