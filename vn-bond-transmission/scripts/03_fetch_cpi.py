#!/usr/bin/env python3
"""
Fetch CPI monthly from NSO (Tổng cục Thống kê) — server-rendered articles.

Source: nso.gov.vn CPI archive (27 pages, 262 articles 2019-11 → 2026-07)
Method: requests (server-rendered HTML) + regex parse CPI YoY/MoM

Output: data/raw/cpi/nso_cpi_monthly.csv
  columns: date, cpi_yoy_pct, cpi_mom_pct, url
"""
import requests, re, json, time, os, urllib3
import pandas as pd
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LINKS_FILE = "data/raw/cpi/nso_cpi_links.json"
OUT_CSV = "data/raw/cpi/nso_cpi_monthly.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", "Accept-Language": "vi-VN,vi;q=0.9"}

YOY_PATTERN = re.compile(
    # "CPI tháng X/YYYY ... tăng/giảm Y.YY% so với tháng X năm YYYY-1"
    r'(?:CPI|chỉ số giá tiêu dùng)[^%.]{0,10}?tháng\s*(\d{1,2})\s*[/\-]\s*(\d{4})[^%]{0,100}?(tăng|giảm)\s*(\d+[,.]?\d*)\s*%\s*so\s*với\s*tháng\s*\d+\s*năm\s*\d{4}',
    re.IGNORECASE
)
YOY_FALLBACK = re.compile(
    # "tăng/giảm Y.YY% so với cùng kỳ" —宽松, sẽ range-check sau
    r'(?:CPI|chỉ số giá tiêu dùng)[^%.]{0,400}?(tăng|giảm)\s*(\d+[,.]?\d*)\s*%\s*so\s*với\s*cùng\s*kỳ',
    re.IGNORECASE
)
# Pattern 3: "tăng X% so với cùng kỳ năm trước" gần "bình quân" hoặc footnote
YOY_FOOTNOTE = re.compile(
    r'(?:bình quân|tốc độ tăng)[^%.]{0,100}?CPI[^%.]{0,100}?(?:tăng|giảm)\s*(\d+[,.]?\d*)\s*%',
    re.IGNORECASE
)
MOM_PATTERN = re.compile(
    r'tháng\s*(\d{1,2})\s*[/\-]\s*(\d{4})[^%]{0,80}?(tăng|giảm)\s*(\d+[,.]?\d*)\s*%\s*so\s*với\s*tháng\s*trước',
    re.IGNORECASE
)

# Range check: CPI YoY VN lịch sử -5% đến 25%. Ngoài range = parse sai (vàng/xăng)
CPI_YOY_MAX = 25.0
CPI_YOY_MIN = -5.0

def parse_one(item):
    url_month, url = item
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        if r.status_code != 200:
            return None
        # Parse text
        soup = BeautifulSoup(r.text, "lxml")
        text = soup.get_text(separator=" ", strip=True)

        # Primary YoY: "CPI tháng X/YYYY ... tăng/giảm Y% so với tháng X năm YYYY-1"
        yoy_matches = YOY_PATTERN.findall(text)
        # Fallback YoY: "CPI ... tăng/giảm Y% so với cùng kỳ"
        if not yoy_matches:
            yoy_fallback = YOY_FALLBACK.findall(text)
        else:
            yoy_fallback = []
        mom_matches = MOM_PATTERN.findall(text)

        cpi_yoy = cpi_mom = cpi_month = cpi_year = None

        # YoY primary (has month/year) — với range check
        for m, y, d, v in yoy_matches[:1]:
            val = float(v.replace(",", ".")) * (-1 if d == "giảm" else 1)
            if CPI_YOY_MIN <= val <= CPI_YOY_MAX:  # range check
                cpi_yoy = val
                cpi_month, cpi_year = int(m), int(y)
        # YoY fallback (no month/year — infer from URL) — thử nhiều match, lấy cái hợp lệ
        if cpi_yoy is None and yoy_fallback:
            for d, v in yoy_fallback[:5]:  # thử 5 match đầu
                val = float(v.replace(",", ".")) * (-1 if d == "giảm" else 1)
                if CPI_YOY_MIN <= val <= CPI_YOY_MAX:
                    cpi_yoy = val
                    break
        # YoY footnote pattern (bình quân/tốc độ tăng)
        if cpi_yoy is None:
            fn_matches = YOY_FOOTNOTE.findall(text)
            for v in fn_matches[:3]:
                val = float(v.replace(",", "."))
                if CPI_YOY_MIN <= val <= CPI_YOY_MAX:
                    cpi_yoy = val
                    break
        # Infer month/year from url_month if still None
        if cpi_month is None and "-" in url_month:
            parts = url_month.split("-")
            if len(parts) == 2:
                cpi_year, cpi_month = int(parts[0]), int(parts[1])
        # MoM
        for m, y, d, v in mom_matches[:1]:
            cpi_mom = float(v.replace(",", ".")) * (-1 if d == "giảm" else 1)
            if cpi_month is None:
                cpi_month, cpi_year = int(m), int(y)

        if cpi_yoy is not None or cpi_mom is not None:
            return {
                "url_month": url_month,
                "url": url,
                "date": f"{cpi_year}-{cpi_month:02d}" if cpi_year and cpi_month else url_month,
                "cpi_yoy_pct": cpi_yoy,
                "cpi_mom_pct": cpi_mom,
            }
    except Exception:
        return None
    return None

def main():
    with open(LINKS_FILE) as f:
        links = json.load(f)
    print(f"Total links: {len(links)}")

    # Load existing (checkpoint)
    existing = {}
    if os.path.exists(OUT_CSV):
        df_ex = pd.read_csv(OUT_CSV)
        for _, row in df_ex.iterrows():
            existing[row["url"]] = row.to_dict()
        print(f"Already parsed: {len(existing)}")

    results = list(existing.values())
    todo = [(um, u) for um, u in links if u not in existing]
    print(f"To fetch: {len(todo)}")

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(parse_one, item): item for item in todo}
        done = 0
        for fut in as_completed(futures):
            done += 1
            r = fut.result()
            if r:
                results.append(r)
            if done % 30 == 0:
                print(f"  {done}/{len(todo)} (cumulative {len(results)})", flush=True)
                # Checkpoint save
                pd.DataFrame(results).to_csv(OUT_CSV, index=False)
            time.sleep(0.05)

    # Dedupe by date
    df = pd.DataFrame(results)
    if len(df) == 0 or "date" not in df.columns:
        print(f"\n⚠️ No results parsed. Check SSL/network.")
        return
    df = df.sort_values("date").drop_duplicates("date", keep="first").reset_index(drop=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"\n✅ Saved {len(df)} months -> {OUT_CSV}")
    print(f"Range: {df.date.min()} → {df.date.max()}")
    print(f"YoY valid: {df.cpi_yoy_pct.notna().sum()}/{len(df)}")
    print(f"MoM valid: {df.cpi_mom_pct.notna().sum()}/{len(df)}")

if __name__ == "__main__":
    main()
