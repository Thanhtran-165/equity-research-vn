#!/usr/bin/env python3
"""
Fetch SBV central reference exchange rate (tỷ giá trung tâm USD/VND) 2015→nay.

Source: SBV Liferay Headless API (discovered via bieu-do-ty-gia-trung-tam chart script)
Endpoint: GET /o/headless-delivery/v1.0/content-structures/137473/structured-contents
  ?pageSize=100&sort=datePublished:desc
  &filter=datePublished ge {fromISO} and datePublished le {toISO}

Note: API requires Liferay session auth token — must call via Liferay.Util.fetch
      in a browser context (Playwright). Direct curl returns 244 bytes (WAF block).

Output: data/raw/sbv_fx/sbv_central_fx_daily.csv
  columns: date, usd_vnd_central, so_van_ban, ngay_ban_hanh
"""
import csv, os, time
from playwright.sync_api import sync_playwright

OUT_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "sbv_fx", "sbv_central_fx_daily.csv")
OUT_CSV = os.path.abspath(OUT_CSV)

PAGE_URL = "https://sbv.gov.vn/bieu-do-ty-gia-trung-tam"
API_TEMPLATE = (
    "/o/headless-delivery/v1.0/content-structures/137473/structured-contents"
    "?pageSize=100&page={page}&sort=datePublished:desc"
    "&filter=datePublished ge {from_enc} and datePublished le {to_enc}"
)
FROM_ISO = "2015-01-01T00:00:00Z"
TO_ISO = "2026-12-31T23:59:59Z"

def main():
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    all_rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = p.chromium.new_page() if False else browser.new_page()
        page.goto(PAGE_URL, timeout=30000, wait_until="networkidle")
        page.wait_for_timeout(2000)

        from urllib.parse import quote
        from_enc = quote(FROM_ISO)
        to_enc = quote(TO_ISO)

        # Page 1 để biết totalCount
        print(f"Fetching page 1...", flush=True)
        result = page.evaluate("""async (args) => {
            const url = args.url;
            try {
                const r = await Liferay.Util.fetch(url, {method: "GET"});
                const data = await r.json();
                return {
                    status: r.status,
                    totalCount: data.totalCount,
                    lastPage: data.lastPage,
                    items: (data.items || []).map(it => {
                        const cf = {};
                        (it.contentFields || []).forEach(f => {
                            cf[f.name] = f.contentFieldValue?.data || "";
                        });
                        return {
                            ngay_bat_dau: cf.NgayBatDau || it.datePublished,
                            ngay_ban_hanh: cf.NgayBanHanh,
                            ty_gia_so: cf.TyGiaSo,
                            so_van_ban: cf.SoVanBan,
                            date_published: it.datePublished
                        };
                    })
                };
            } catch(e) {
                return {error: e.message};
            }
        }""", {"url": API_TEMPLATE.format(page=1, from_enc=from_enc, to_enc=to_enc)})

        if "error" in result:
            print(f"❌ API error: {result['error']}", flush=True)
            browser.close()
            return

        total = result["totalCount"]
        last_page = result["lastPage"]
        print(f"totalCount: {total} | lastPage: {last_page}", flush=True)
        all_rows.extend(result["items"])
        print(f"  page 1: {len(result['items'])} items (cumulative {len(all_rows)})", flush=True)

        # Paginate
        for pg in range(2, last_page + 1):
            if pg % 5 == 0:
                print(f"  page {pg}/{last_page} (cumulative {len(all_rows)})", flush=True)
            time.sleep(0.3)  # polite
            r = page.evaluate("""async (args) => {
                const url = args.url;
                try {
                    const r = await Liferay.Util.fetch(url, {method: "GET"});
                    const data = await r.json();
                    return (data.items || []).map(it => {
                        const cf = {};
                        (it.contentFields || []).forEach(f => {
                            cf[f.name] = f.contentFieldValue?.data || "";
                        });
                        return {
                            ngay_bat_dau: cf.NgayBatDau || it.datePublished,
                            ngay_ban_hanh: cf.NgayBanHanh,
                            ty_gia_so: cf.TyGiaSo,
                            so_van_ban: cf.SoVanBan,
                            date_published: it.datePublished
                        };
                    });
                } catch(e) {
                    return {error: e.message};
                }
            }""", {"url": API_TEMPLATE.format(page=pg, from_enc=from_enc, to_enc=to_enc)})

            if isinstance(r, dict) and "error" in r:
                print(f"  ⚠️ page {pg} error: {r['error']}, retry once", flush=True)
                time.sleep(2)
                continue
            all_rows.extend(r)

        browser.close()

    # Write CSV
    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "usd_vnd_central", "so_van_ban", "ngay_ban_hanh", "date_published"])
        writer.writeheader()
        for row in all_rows:
            # Parse date from ISO string → YYYY-MM-DD
            raw_date = row.get("ngay_bat_dau") or row.get("date_published") or ""
            try:
                # ISO format 2026-07-08T17:00:00Z → 2026-07-08
                date_str = raw_date[:10] if len(raw_date) >= 10 else raw_date
            except Exception:
                date_str = raw_date
            writer.writerow({
                "date": date_str,
                "usd_vnd_central": row.get("ty_gia_so"),
                "so_van_ban": row.get("so_van_ban"),
                "ngay_ban_hanh": (row.get("ngay_ban_hanh") or "")[:10],
                "date_published": row.get("date_published"),
            })

    print(f"\n✅ Saved {len(all_rows)} rows -> {OUT_CSV}", flush=True)

    # Verify
    import pandas as pd
    df = pd.read_csv(OUT_CSV)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    print(f"Date range: {df.date.min().date()} → {df.date.max().date()}", flush=True)
    print(f"USD/VND range: {df.usd_vnd_central.min()} → {df.usd_vnd_central.max()}", flush=True)

if __name__ == "__main__":
    main()
