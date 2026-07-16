# Export Matrix — Chim Cút

> Export checklist cho Page "Chim Cút" từ Meta Business Suite.
> Website: https://business.facebook.com/latest/
> UI Path: Insights → Content → Export data

## Naming convention

```
chimcut_fb_<content_level>_<data_view>_<filter>_<preset>_<period>.csv
```

---

## ⚠️ Meta limitations đã xác minh

### 1. Activity filter chỉ gồm video

> "Bộ lọc hoạt động chỉ bao gồm bài viết có video."

Posts / Daily / Activity chỉ trả video posts. Không phải dữ liệu toàn bộ bài viết.

### 2. Page / Daily / Performance chưa tìm thấy trong Content export

> Khi chọn **Cấp độ nội dung = Trang / Page**, preset **"Hiệu quả / Performance" bị disable** với ghi chú:
> "chỉ áp dụng cho bài viết và video".

Vì vậy **G01 (Page / Daily / Performance) = desired, chưa verified**. Chưa tìm thấy export surface nào trong Content Export trả Page-level daily performance metrics (reach, impressions, engagement theo ngày cho toàn Page).

**Nếu sau này tìm thấy Page performance ở Insights → Results hoặc Overview**, sẽ promote G01 lên P0 verified.

### 3. Page / Daily / Audience = verified nhưng audience-only

Page / Daily / Audience có thể tải được, nhưng chỉ chứa demographic data (độ tuổi, giới tính, quốc gia). **Không thay thế cho Page performance** — không có reach/impressions/engagement.

---

## Priority logic (verified vs desired)

### Verified — tìm thấy và tải được từ Content Export

| ID | Priority | Content | Data view | Filter | Preset | Scope | Use case |
|---|---|---|---|---|---|---|---|
| **P01** | **P0** | Posts | Lifetime | Created | Performance | Tất cả bài | **Ranking toàn bộ bài viết** (video + photo + text + link) |
| **P02** | **P0** | Posts | Lifetime | Created | Published | Tất cả bài | **Master list bài viết** |
| **V01** | **P0** | Video | Lifetime | Created | Performance | Chỉ video | **Top video/reels ranking** |
| V02 | P1 | Video | Daily | Activity | Performance | Chỉ video | Operational video daily trend |
| V03 | P2 | Video | Lifetime | Created | Retention | Chỉ video | Video retention analysis |
| G02 | P2 | Page | Daily | — | Audience | Toàn Page | Audience demographics (không phải performance) |

### Desired — chưa tìm thấy trong Content Export

| ID | Priority | Content | Data view | Filter | Preset | Status | Notes |
|---|---|---|---|---|---|---|---|
| G01 | — | Page | Daily | — | Performance | **❌ Not yet found** | Page-level preset "Hiệu quả" bị disable khi content level = Trang. Nếu tìm thấy ở Insights → Results/Overview, sẽ promote lên P0. |

---

## P0 — Verified (bắt buộc hàng tháng)

### P01: Posts / Lifetime / Created / Performance

| Field | Value |
|---|---|
| Content level | Bài viết / Posts |
| Data view | Trọn đời / Lifetime |
| Filter | Ngày tạo / Created date |
| Preset | Hiệu quả / Performance |
| Filename (monthly) | `chimcut_fb_posts_lifetime_created_performance_YYYY_MM.csv` |
| Use case | **Ranking toàn bộ bài viết** — top content, milestone. Bao gồm tất cả loại bài. |

### P02: Posts / Lifetime / Created / Published

| Field | Value |
|---|---|
| Content level | Bài viết / Posts |
| Data view | Trọn đời / Lifetime |
| Filter | Ngày tạo / Created date |
| Preset | Đã đăng / Published |
| Filename (monthly) | `chimcut_fb_posts_lifetime_created_published_YYYY_MM.csv` |
| Use case | **Master list bài viết** — danh sách đầy đủ tất cả bài đã đăng. |

### V01: Video / Lifetime / Created / Performance

| Field | Value |
|---|---|
| Content level | Video |
| Data view | Trọn đời / Lifetime |
| Filter | Ngày tạo / Created date |
| Preset | Hiệu quả / Performance |
| Filename (monthly) | `chimcut_fb_video_lifetime_created_performance_YYYY_MM.csv` |
| Use case | **Top video/reels ranking** — milestone video. |

---

## P1 — Operational video (hàng tháng)

### V02: Video / Daily / Activity / Performance

| Field | Value |
|---|---|
| Content level | Video |
| Data view | Hằng ngày / Daily |
| Filter | Hoạt động / Activity |
| Preset | Hiệu quả / Performance |
| Filename (monthly) | `chimcut_fb_video_daily_activity_performance_YYYY_MM.csv` |
| Use case | Operational video daily trend. ⚠️ Chỉ gồm video posts. |

---

## P2 — Optional / Specialized

### V03: Video / Lifetime / Created / Retention (if available)

| Field | Value |
|---|---|
| Content level | Video |
| Data view | Trọn đời / Lifetime |
| Filter | Ngày tạo / Created date |
| Preset | Tỷ lệ giữ chân / Retention |
| Filename | `chimcut_fb_video_lifetime_created_retention_YYYY_QX.csv` |
| Notes | Chỉ tải nếu preset Tỷ lệ giữ chân có sẵn |

### G02: Page / Daily / Audience (verified, audience-only)

| Field | Value |
|---|---|
| Content level | Trang / Page |
| Data view | Hằng ngày / Daily |
| Filter | — |
| Preset | Đối tượng / Audience |
| Filename | `chimcut_fb_page_daily_audience_YYYY_MM.csv` |
| Use case | Audience demographics (độ tuổi, giới tính, quốc gia). **KHÔNG thay thế cho Page performance.** |
| ⚠️ | Không có reach/impressions/engagement. Chỉ demographic data. |

---

## ❌ Desired — chưa verified

### G01: Page / Daily / Performance

| Field | Value |
|---|---|
| Status | **❌ Not yet found in Content Export** |
| Issue | Page / preset "Hiệu quả" bị disable → "chỉ áp dụng cho bài viết và video" |
| If found | Promote lên P0 — sẽ là operational health toàn Page |
| Search locations | Insights → Results, Insights → Overview, Meta Business Suite home dashboard export |

---

## Summary table

| ID | Priority | Verified? | Content | Data view | Preset | Use case |
|---|---|---|---|---|---|---|
| **P01** | **P0** | ✅ | Posts | Lifetime | Performance | Ranking toàn bộ bài |
| **P02** | **P0** | ✅ | Posts | Lifetime | Published | Master list bài |
| **V01** | **P0** | ✅ | Video | Lifetime | Performance | Top video ranking |
| V02 | P1 | ✅ | Video | Daily/Activity | Performance | Video daily trend |
| V03 | P2 | ✅ | Video | Lifetime | Retention | Video retention |
| G02 | P2 | ✅ | Page | Daily | Audience | Audience demo only |
| ~~G01~~ | — | ❌ | Page | Daily | Performance | **Not yet found** |

## Notes

- P01, P02, V01 là **bắt buộc mỗi tháng** — verified downloadable.
- V02 tải **mỗi tháng** — operational video.
- V03, G02 **tùy chọn** — chỉ khi preset có sẵn.
- G01 **chưa verified** — cần tìm export surface khác (không phải Content Export).
- Thu nhập/Earnings bỏ qua nếu Page chưa monetization.
