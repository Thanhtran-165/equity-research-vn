# Operator Checklist — Chim Cút Dashboard

Hướng dẫn vận hành hàng tuần/tháng cho dashboard Facebook Page Graph Dashboard.

## Weekly routine (mỗi Thứ Hai)

### 1. Tải dữ liệu từ Meta Business Suite

Mở: https://business.facebook.com/latest/
Path: Thông tin chi tiết → Nội dung → Xuất dữ liệu

Files cần tải (theo thứ tự ưu tiên):

| # | Code | Content level | Data view | Filter | Preset | Filename |
|---|---|---|---|---|---|---|
| 1 | W01 | Video | Hằng ngày | Hoạt động | Hiệu quả | `chimcut_fb_video_daily_activity_performance_YYYY-MM-DD_YYYY-MM-DD.csv` |
| 2 | W02 | Bài viết | Trọn đời | Ngày tạo | Hiệu quả | `chimcut_fb_posts_lifetime_created_performance_YYYY-MM-DD_YYYY-MM-DD.csv` |
| 3 | W03 | Bài viết | Trọn đời | Ngày tạo | Đã đăng | `chimcut_fb_posts_lifetime_created_published_YYYY-MM-DD_YYYY-MM-DD.csv` |
| 4 | W04 | Video | Trọn đời | Ngày tạo | Hiệu quả | `chimcut_fb_video_lifetime_created_performance_YYYY-MM-DD_YYYY-MM-DD.csv` |

**Date range**: Tuần trước (Thứ Hai → Chủ Nhật)

### 2. Đưa file vào imports

Copy file đã tải vào:
```
imports/incoming/
```

Hoặc mở `http://localhost:3123/imports` → kéo thả file.

### 3. Import + Apply

1. Mở `/imports`
2. Upload file → xem preview → confirm mapping
3. Apply (cho Posts files) hoặc Apply Video (cho Video files)
4. Kiểm tra: matched count, warnings

### 4. Kiểm tra sức khỏe

```bash
npm run dashboard:health
```

Kết quả mong đợi:
- `PASS ✅` = tốt
- `WARN ⚠️` = cần để ý nhưng không nghiêm trọng
- `FAIL ❌` = cần sửa ngay, exit code non-zero

### 5. Tạo báo cáo tháng (nếu đầu tháng)

```bash
npm run report:monthly -- --month=2026-07
```

Output: `reports/2026-07-chimcut-monthly-report.md`

## Monthly routine (đầu tháng)

Vào Thứ Hai đầu tháng, ngoài weekly files, tải thêm YTD refresh:

| # | Code | Content level | Data view | Preset | Filename |
|---|---|---|---|---|---|
| 1 | M01 | Bài viết | Trọn đời | Hiệu quả | `chimcut_fb_posts_lifetime_created_performance_ytd_YYYY-MM-DD.csv` |
| 2 | M02 | Bài viết | Trọn đời | Đã đăng | `chimcut_fb_posts_lifetime_created_published_ytd_YYYY-MM-DD.csv` |
| 3 | M03 | Video | Trọn đời | Hiệu quả | `chimcut_fb_video_lifetime_created_performance_ytd_YYYY-MM-DD.csv` |

Date range: 01/01 → Chủ Nhật cuối cùng trước ngày nhắc.

## Commands reference

```bash
# Health check
npm run dashboard:health

# Link video assets to posts (title + date matching)
npx tsx scripts/link-video-assets.ts

# Generate monthly report
npm run report:monthly -- --month=2026-07

# Generate export checklist
npm run export:checklist -- --month 2026-07

# Start/stop server
./scripts/agent-start.sh
./scripts/agent-stop.sh

# Watch Downloads folder (optional semi-automation)
npm run watch-exports
```

## How to interpret PASS/WARN/FAIL

| Level | Meaning | Action |
|---|---|---|
| ✅ PASS | Invariant OK | None |
| ⚠️ WARN | Known issue, not blocking | Monitor; resolve if convenient |
| ❌ FAIL | Data corruption or broken invariant | Fix immediately |

### Expected WARN items (do NOT fix)

- **219 video assets unlinked** — Meta uses different ID systems for Post vs Video export. Expected.
- **1 watch-time anomaly** — Meta data error. Flagged, not removed.

### FAIL items (MUST fix)

- Duplicate reminder items → run cleanup SQL
- Non-true-reach posts with ER → run backfill SQL
- Build/runtime unavailable → restart server

## What NOT to do

- ❌ **Không scrape Meta Business Suite** — không browser automation trên Meta thật
- ❌ **Không tự động tải file** — user tự tải thủ công
- ❌ **Không xóa raw data** trừ khi có backup + migration rõ ràng
- ❌ **Không map "Lượt hiển thị quảng cáo" vào organic impressions**
- ❌ **Không gọi video views là reach**
- ❌ **Không tính ER với clicks** — ER = (reactions + comments + shares) / reach only
- ❌ **Không commit token/DB lên git**

## Rollback procedure

Nếu dashboard bị hỏng sau update:

```bash
# 1. Stop server
./scripts/agent-stop.sh

# 2. Restore DB from backup
cp backups/chimcut_dashboard_p2_quality_uplift_20260710.db prisma/dev.db

# 3. Restart server
./scripts/agent-start.sh

# 4. Verify
npm run dashboard:health
```

Backups available:
- `backups/chimcut_dashboard_p2_quality_uplift_20260710.db` — after P2 quality uplift
- `backups/chimcut_dashboard_after_video_dashboard_20260709.db` — after video dashboard v1
