# Hướng dẫn Import CSV từ Meta Business Suite (cho người dùng)

Tài liệu hướng dẫn người dùng Việt Nam xuất dữ liệu từ Meta Business Suite và nhập vào dashboard.

---

## 1. Vì sao cần import CSV?

Dashboard của bạn cần chỉ số **Reach thật** và **Impressions thật** để:
- Hiển thị **Engagement Rate** chính xác.
- Xếp hạng **Top posts** đúng.
- Tạo **báo cáo tuần/tháng** đáng tin cậy.

Facebook Graph API (qua quyền `read_insights`) đang bị chặn ở **Business Verification**. Trong khi chờ App Review, bạn có thể **tự xuất file CSV/XLSX** từ Meta Business Suite — đây là dữ liệu chính thức do Meta cung cấp, được dashboard coi là nguồn insight thật.

---

## 2. Cách xuất dữ liệu từ Meta Business Suite (step-by-step)

### Bước 1: Mở Meta Business Suite
- Truy cập: <https://business.facebook.com/latest/>
- Chọn Page của bạn (vd: "Chim Cút").

### Bước 2: Vào Insights → Content
- Menu trái → **Insights** → **Content**.
- Đây là nơi liệt kê các bài viết với metric theo từng post.

### Bước 3: Chọn khoảng thời gian
- Bấm chọn khoảng thời gian ở góc phải (7 ngày / 28 ngày / 90 ngày).

### Bước 4: Bấm Export
- Tìm biểu tượng **Export** (thường là icon mũi tên xuống hoặc biểu tượng tải về).
- Chọn:
  - **Loại file**: CSV (khuyến nghị) hoặc XLSX.
  - **Loại dữ liệu**: Content (cho post-level) hoặc Overview (cho Page-level).
- Bấm **Export** → Meta tạo file → tự tải về máy (thường vào thư mục `~/Downloads`).

### Bước 5: Đặt tên file (khuyến nghị)
Để dễ quản lý, đặt tên theo mẫu:
```
meta-insights-<page-slug>-<loại>-<YYYY-MM-DD>.csv

Ví dụ:
meta-insights-chimcut-content-2026-07-07.csv       ← post performance
meta-insights-chimcut-overview-2026-07-07.csv      ← page overview
meta-insights-chimcut-reels-2026-07-07.csv         ← video/reels
```

---

## 3. Cách import vào dashboard

### Cách A — Upload qua UI /imports

1. Mở dashboard → **/imports** (menu trái).
2. Kéo thả file CSV/XLSX vào ô upload (hoặc bấm để chọn file).
3. Dashboard tự **parse** + **detect columns**.
4. Xem **preview 20 dòng đầu**.
5. Nếu cần, **sửa column mapping** (chọn cột tương ứng cho từng field).
6. Bấm **Confirm mapping**.
7. Bấm **Apply** (match với post trong DB + apply insights).
8. Xem kết quả: bao nhiêu row matched, bao nhiêu unmatched.
9. Xem **Import history** ở dưới.

### Cách B — Watched folder (semi-automation)

Nếu muốn dashboard **tự phát hiện** file bạn vừa tải về:

```bash
# Mở terminal, chạy:
cd /Users/bobo/ZCodeProject/facebook-page-graph-dashboard
META_EXPORTS_WATCH_DIR=~/Downloads \
META_EXPORTS_AUTO_IMPORT=true \
npx tsx scripts/watch-meta-exports.ts
```

Khi bạn tải file từ Meta Business Suite về `~/Downloads`, script sẽ:
1. Phát hiện file match pattern (`*.csv`, có "insights"/"facebook"/"meta" trong tên).
2. Đợi file ổn định (5s).
3. Copy vào `imports/incoming/`.
4. Tự upload qua API.

> ⚠️ Script KHÔNG mở browser, KHÔNG login Meta, KHÔNG tải file thay bạn. Chỉ xử lý file bạn đã tự tải.

---

## 4. Checklist xuất định kỳ (tuần/tháng)

### Hàng tuần (thứ 2 hàng tuần)
```
☐ Mở Meta Business Suite → Insights → Content
☐ Chọn "Last 7 days"
☐ Export CSV → meta-insights-<page>-content-YYYY-MM-DD.csv
☐ Upload vào /imports
☐ Review unmatched rows (nếu có)
```

### Hàng tháng (ngày 1 hàng tháng)
```
☐ Mở Meta Business Suite → Insights → Overview
☐ Chọn "Last 28 days"
☐ Export CSV → meta-insights-<page>-overview-YYYY-MM-DD.csv
☐ Upload vào /imports (cho PageSnapshot)
```

---

## 5. Xử lý vấn đề thường gặp

### "KHÔNG match được post nào"
Nguyên nhân có thể:
- **File không có cột Post ID hoặc Permalink** → dashboard không biết match với post nào.
- **Cột Post ID khác format** với DB (vd: file có "111", DB có "100_111").
- **Cột Permalink URL khác domain** với DB (vd: file có `fb.me/...`, DB có `facebook.com/...`).

**Cách xử lý:**
- Bấm **Export unmatched** trong /imports để xem rows nào không match.
- Kiểm tra manual: copy permalink từ file → tìm trong /posts của dashboard.
- Nếu cần, mở CSV trong Excel/Google Sheets, sửa cột Post ID cho khớp format DB.

### "Matched nhưng metric sai"
- Kiểm tra lại **column mapping** (bước 5 ở phần upload).
- Có thể cột "Reach" đã bị map sang cột khác (vd: "Impressions").

### "File format không hỗ trợ"
- Dashboard chỉ nhận `.csv`, `.xlsx`, `.xls`.
- Nếu Meta xuất ra `.tsv` (tab-separated), đổi đuôi file thành `.csv` rồi mở Excel save lại thành CSV.

### "Số trong file có dấu phẩy (1,234)"
- Dashboard tự detect comma/dot separator → không cần sửa.
- Nếu vẫn sai, mở file trong Excel → File → Save As → chọn format "CSV UTF-8".

---

## 6. Cảnh báo quan trọng

- ⚠️ **Không realtime**: dữ liệu CSV chỉ cập nhật khi bạn tự export.
- ⚠️ **Cần export định kỳ** (hàng tuần/tháng) để dashboard có data mới.
- ⚠️ **Format có thể thay đổi**: Meta có thể đổi tên cột theo version UI → dashboard auto-detect, nhưng có thể cần sửa manual.
- ⚠️ **Không scrape Meta**: đừng cố tự động tải file bằng script bypass login.
- ⚠️ **Một số export có thể không có post_id**: phải match qua permalink/created_time → độ chính xác giảm.
