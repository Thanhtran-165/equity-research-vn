# Meta Business Suite Export — Research

> Mục tiêu: hiểu luồng export CSV/XLSX chính thức từ Meta Business Suite để dùng làm nguồn "true insight data, manually imported" thay thế cho `read_insights` Graph API (đang bị chặn ở Business Verification).

---

## 1. Luồng export thủ công hiện tại (chính thức)

Đây là luồng **chính thức do Meta cung cấp**, người dùng tự thao tác, không vi phạm ToS:

1. Mở **Meta Business Suite**: <https://business.facebook.com/latest/>
2. Chọn Page (vd: "Chim Cút").
3. Vào menu trái → **Insights** → **Overview** hoặc **Content**.
4. Chọn khoảng thời gian (7 ngày / 28 ngày / 90 ngày).
5. Bấm nút **Export** (góc phải, icon mũi tên xuống hoặc biểu tượng export).
6. Chọn:
   - **Loại dữ liệu**: Overview / Content / Audience.
   - **Format**: CSV hoặc XLSX (tùy UI version).
   - **Date range**.
7. Bấm **Export** → Meta tạo file → tự download về máy.

> ⚠️ UI Meta Business Suite có thể thay đổi theo thời gian và theo ngôn ngữ (English / Tiếng Việt). Một số tài khoản có thể không thấy nút Export hoặc chỉ thấy CSV.

---

## 2. Các loại export cần test

Yêu cầu người dùng cung cấp **ít nhất 3 file mẫu** để ta xác định format thật:

| # | Loại export | Vị trí trong Meta Business Suite | Mục đích |
|---|---|---|---|
| 1 | **Page overview insights** | Insights → Overview → Export | Reach/impressions tổng Page theo ngày |
| 2 | **Content / Post performance** | Insights → Content → Export | **Quan trọng nhất** — post-level reach/impressions/clicks |
| 3 | **Reels / Video insights** | Insights → Content → filter Video/Reels → Export | Video views, watch time, 3s views |

Cũng nên thử export theo 3 khoảng thời gian để check format có thay đổi không:
- **7 ngày**
- **28 ngày**
- **90 ngày**

---

## 3. Format dự kiến + mapping linh hoạt (EN/VI)

Meta Business Suite export thường có cấu trúc:

### Row structure
- **Page overview**: 1 row/ngày với các cột `Date, Reach, Impressions, Engagements, ...`
- **Content / Post performance**: 1 row/post với cột `Post ID, Permalink, Post message, Reach, Impressions, Reactions, Comments, Shares, ...`
- **Reels/Video**: thêm `Video views, 3-second views, 1-minute views, Watch time`

### Column aliases (linh hoạt EN + VI)

| Field chuẩn | Aliases EN | Aliases VI |
|---|---|---|
| `postId` | `Post ID`, `Content ID`, `Facebook Post ID`, `ID` | `ID bài viết`, `ID nội dung`, `Mã bài viết` |
| `permalinkUrl` | `Permalink`, `Permalink URL`, `Post URL`, `Link`, `Content URL` | `Liên kết`, `URL bài viết`, `Đường dẫn`, `Permalink` |
| `createdTime` | `Created time`, `Published date`, `Date published`, `Post date` | `Ngày đăng`, `Thời gian đăng`, `Ngày tạo` |
| `messageSnippet` | `Post message`, `Content`, `Caption`, `Title`, `Description` | `Nội dung`, `Tiêu đề`, `Chú thích`, `Mô tả` |
| `reach` | `Reach`, `Post reach`, `Facebook reach`, `Accounts reached`, `People reached` | `Lượt tiếp cận`, `Số người tiếp cận`, `Người tiếp cận`, `Tiếp cận` |
| `impressions` | `Impressions`, `Post impressions`, `Views`, `Total impressions` | `Lượt hiển thị`, `Số lượt hiển thị`, `Hiển thị` |
| `clicks` | `Clicks`, `Post clicks`, `Link clicks`, `Other clicks` | `Lượt nhấp`, `Số lượt nhấp`, `Nhấp`, `Click` |
| `engagedUsers` | `Engaged users`, `Post engaged users`, `Engagements`, `People engaged` | `Người tương tác`, `Lượt tương tác`, `Tương tác` |
| `reactions` | `Reactions`, `Likes and reactions`, `Likes` | `Cảm xúc`, `Lượt thích`, `Thích`, `Reactions` |
| `comments` | `Comments`, `Comment count` | `Bình luận`, `Số bình luận` |
| `shares` | `Shares`, `Share count` | `Chia sẻ`, `Số lượt chia sẻ` |
| `videoViews` | `Video views`, `3-second video views`, `Views` | `Lượt xem video`, `Lượt xem`, `Views` |
| `watchTime` | `Watch time`, `Average watch time` | `Thời gian xem`, `Thời lượng xem` |

---

## 4. Rủi ro format

| Rủi ro | Mô tả | Cách xử lý |
|---|---|---|
| **Tên cột đổi theo ngôn ngữ UI** | English → "Reach", Tiếng Việt → "Lượt tiếp cận" | `columnDetection.ts` với alias map |
| **Excel có header nhiều dòng** | Dòng 1-2 có thể là tiêu đề báo cáo, dòng 3 mới là header | Tự detect header row (scan 5 dòng đầu tìm row có >50% field alias) |
| **CSV encoding UTF-8 BOM** | File có prefix `\uFEFF` | Strip BOM trong `parseCsv.ts` |
| **Delimiter comma vs semicolon** | Region settings ảnh hưởng | Auto-detect: đếm `,` vs `;` trong dòng header |
| **Date format khác nhau** | `MM/DD/YYYY`, `DD/MM/YYYY`, `YYYY-MM-DD`, ISO | `normalizeRows.ts` thử nhiều format |
| **Gom theo ngày thay vì theo post** | Overview export là row/ngày, không phải row/post | Chỉ dùng cho PageSnapshot, không áp cho Post |
| **Không có post_id** | Một số export chỉ có permalink | Fallback matching qua permalink + created_time |
| **Number with thousand separator** | `1,234` (EN) vs `1.234` (VI) | Strip separator + parseInt |

---

## 5. Kết luận research

### File phù hợp nhất cho post-level insights
→ **Content / Post performance export** (file #2 ở mục 2). Mỗi row = 1 post với đầy đủ post_id, permalink, reach, impressions, comments, shares.

### File chỉ phù hợp cho Page-level overview
→ **Page overview insights** (file #1). Mỗi row = 1 ngày, dùng để update `PageSnapshot`.

### Cột tối thiểu để import post-level tốt

| Bắt buộc | Tốt nếu có |
|---|---|
| `permalink_url` hoặc `post_id` | `reach` |
| `created_time` hoặc `published_date` | `impressions` |
| — | `reactions`, `comments`, `shares` |

### Nếu thiếu post_id/permalink
- Phải đưa vào **review thủ công** trong UI `/imports`.
- Hiển thị ở danh sách "unmatched rows" để user tự map.

### Workflow đề xuất

```
1. User vào Meta Business Suite → Insights → Content → Export (CSV/XLSX)
2. Mở dashboard → /imports → upload file
3. App detect columns → preview 20 dòng
4. User confirm mapping
5. App match với post hiện có (qua post_id/permalink)
6. Apply metrics (reach, impressions, clicks, engagedUsers)
7. metricSource = meta_business_suite_csv
8. Dashboard tự switch sang Insights Mode
9. Unmatched rows → hiển thị để user review
```

---

## 6. Sample naming convention (đề xuất)

Để dễ phân biệt file:
```
meta-insights-<page-slug>-<export-type>-<YYYY-MM-DD>.csv

Ví dụ:
meta-insights-chimcut-content-2026-07-07.csv       ← post performance
meta-insights-chimcut-overview-2026-07-07.csv      ← page overview
meta-insights-chimcut-reels-2026-07-07.csv         ← video/reels
```
