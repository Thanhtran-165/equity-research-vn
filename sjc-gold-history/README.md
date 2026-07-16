# SJC Gold Price History Collector

Thu thập **lịch sử giá vàng SJC** từ nguồn chính chủ `sjc.com.vn`, tạo chuỗi dữ liệu
**liên tục từ 22/07/2009 đến hiện tại** với độ phân giải **theo giờ/intraday**.

## Kết quả thực tế

Dataset đã build thành công (verified):

| Metric | Giá trị |
|---|---|
| **Số dòng** | 27.921 (mỗi dòng = 1 lần update giá) |
| **Số ngày** | 4.345 ngày giao dịch |
| **Phạm vi** | 22/07/2009 → 08/07/2026 (~17 năm) |
| **Cross-check vs giavang.org** | 19/30 khớp exact, 11/30 lệch ≤0.4% (chốt giờ khác) |
| **Anomalies** | 1 điểm lỗi nguồn (đã filter) |

## Tại sao dự án này tồn tại

`sjc.com.vn` là nguồn chính thức của Công ty Vàng Bạc Đá Quý Sài Gòn — nguồn
đáng tin cậy nhất cho giá vàng SJC. Trang có API ẩn (`PriceService.ashx`) trả về
lịch sử giá, nhưng có 2 trở ngại:

1. **Cloudflare protection (TLS fingerprinting)**: `requests`/`httpx` dùng OpenSSL
   → CF nhận diện qua JA3/JA4 fingerprint → 403. Giải pháp: dùng `curl_cffi`,
   impersonate **chính xác TLS handshake của Chrome** → CF coi là browser thật.
2. **Giới hạn 90 ngày/lần gọi**: API trả lỗi *"Chỉ được xem Giá trong khoảng dưới
   90 ngày"* → chia thành các window 89 ngày.

## Cài đặt

```bash
pip install curl_cffi pandas pyarrow requests
```

Không cần Playwright/Chromium — `curl_cffi` giải CF ở tầng TLS, gọn và nhanh hơn
nhiều so với headless browser.

## Sử dụng

### 1. Backfill toàn bộ (lần đầu)

```bash
cd sjc-gold-history
python -m src.crawl backfill          # 22/07/2009 → hôm nay
```

Tự bỏ qua các window đã crawl (resume được). ~70 window × 89 ngày, mất ~3 phút.
Backfill thực tế: **25.885 points, 0 errors**.

### 2. Cập nhật định kỳ (hàng ngày/tuần)

```bash
python -m src.update                  # kéo 89 ngày gần nhất, rebuild master
```

### 3. Build master dataset

```bash
python -m src.merge                   # raw JSON → sjc_master.parquet + .csv
```

### 4. Cross-check với giavang.org (tùy chọn)

```bash
python -m src.crosscheck --n 30       # sample 30 ngày, so sánh giá đóng cửa
```

So sánh với nguồn độc lập [giavang.org](https://giavang.org/trong-nuoc/sjc/lich-su/)
(coverage 2009→21/04/2025) để phát hiện anomaly.

## Output

```
data/
├── raw/                     # JSON chunks, 1 file / window 89 ngày
│   └── sjc_id1_2024-01-15_2024-04-13.json
└── processed/
    ├── sjc_master.parquet   # canonical, typed (đề nghị dùng cái này)
    └── sjc_master.csv       # human-readable
```

### Schema

| Cột | Kiểu | Mô tả |
|---|---|---|
| `timestamp` | datetime (Asia/Ho_Chi_Minh) | Thời điểm SJC set giá |
| `date` | date | Ngày lịch (UTC+7) |
| `gold_price_id` | int | ID nguồn (1 = SJC 1L HCM) |
| `branch` | str | Chi nhánh (Hồ Chí Minh, Miền Bắc, ...) |
| `gold_type` | str | Loại vàng (Vàng SJC 1L..., Nhẫn SJC, Nữ trang...) |
| `buy_vnd` | int64 | Giá mua, VND/lượng |
| `sell_vnd` | int64 | Giá bán, VND/lượng |
| `buy_million` | float | Giá mua, triệu/lượng |
| `sell_million` | float | Giá bán, triệu/lượng |

Mỗi dòng = **một lần update giá** của SJC trong ngày (4–10+ lần/ngày).
Filter vệ sinh: bỏ các giá trị < 5M VND/lượng (feed errors).

### Lấy các loại vàng / chi nhánh khác

ID mặc định = 1 (HCM, SJC 1L). Các ID khác (Nhẫn SJC, Nữ trang 99%, các chi nhánh
Miền Bắc/Trung/Tây...) xem trong `src/config.py:GOLD_PRICE_IDS`.

```bash
python -m src.crawl backfill --gold-price-id 49   # Nhẫn SJC 99,99% HCM
python -m src.merge                                # merge tất cả ID
```

## Cron / Tự động hóa

```cron
# Mỗi ngày lúc 19:00 (sau giờ giao dịch), update + rebuild
0 19 * * 1-6  cd /path/to/sjc-gold-history && python -m src.update >> logs/update.log 2>&1
```

Chỉ chạy T2–T7 (thị trường vàng đóng cửa CN).

## Kiến trúc

```
src/
├── config.py       # Hằng số: gold_price_id map, giới hạn 89 ngày, endpoints
├── crawl.py        # curl_cffi crawler, chia window 89 ngày, retry CF
├── merge.py        # Parse raw JSON → tidy DataFrame → parquet/csv
├── update.py       # Wrapper: crawl trailing window + rebuild master
└── crosscheck.py   # Cross-check với giavang.org
```

## Câu hỏi thường gặp

**Tại sao không dùng `requests`/`httpx`?** sjc.com.vn sau Cloudflare dùng TLS
fingerprinting (JA3/JA4) để phân biệt browser. `requests` có fingerprint OpenSSL
→ 403. `curl_cffi` impersonate Chrome → pass.

**Tại sao không dùng Playwright?** Đã thử: Cloudflare có rule riêng, chặn API
endpoint (`/GoldPrice/Services/PriceService.ashx`) ngay cả khi document request
pass — clearance cho trang HTML không áp dụng cho API. `curl_cffi` đơn giản hơn
và reliable hơn.

**Tại sao window 89 ngày?** API chặn >= 90 ngày. 89 là an toàn nhất (chính xác
90 cũng bị chặn).

**Dữ liệu cũ đến bao xa?** sjc.com.vn có từ **22/07/2009**. Trước đó không có.

**Rate limit?** `curl_cffi` impersonate tốt nên hiếm khi bị CF re-challenge.
Nếu có, crawler tự re-warm (load lại trang để lấy cookie mới) rồi retry với
backoff.
