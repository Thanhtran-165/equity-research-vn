# GLM Quality Uplift Prompt

Bạn là senior full-stack/product engineer. Làm việc trong repo:

`/Users/bobo/ZCodeProject/facebook-page-graph-dashboard`

Mục tiêu: nâng trần chất lượng dashboard Facebook Page Graph Dashboard từ "đã chạy được" lên "đủ tin cậy để vận hành weekly/monthly cho Chim Cút". Không thêm feature mới trước khi sửa xong các lỗi dữ liệu và UX dưới đây.

## Context bắt buộc

- App: Next.js 14 + Prisma + SQLite.
- Runtime local: `http://localhost:3123`.
- DB chính: `prisma/dev.db`.
- Dữ liệu hiện tại: Chim Cút, khoảng 44.880 followers, 631 posts trong DB, dashboard API lấy 500 latest posts.
- Verified commands hiện tại đều pass: `npm run typecheck`, `npm test` với 237 tests, `npm run lint`, `npm run build`.
- Manual Meta export workflow là ràng buộc sản phẩm: không scrape Meta, không browser automation trên Meta thật, chỉ manual export + watched folder + CSV/XLSX import.

## P0 fixes

1. Fix `GET /api/data-reminders/current` idempotency.
   - Bug hiện tại: monthly run query tìm `periodStart startsWith current month`, nhưng monthly YTD run có `periodStart=2026-01-01`, nên mỗi lần mở trang/call endpoint lại catch unique rồi tạo thêm M01-M04 duplicate.
   - Evidence: `DataReminderItem` runId=3 có M01-M04 lặp 6 lần.
   - Sửa route để:
     - tìm monthly run bằng exact generated YTD range hoặc stable monthly key, không dùng `periodStart startsWith monthKey`;
     - chỉ create items khi `monthlyRun.items.length === 0`;
     - dùng transaction/upsert hoặc createMany skipDuplicates nếu thêm unique constraint;
     - không để GET làm tăng số row sau khi gọi lặp.
   - Thêm test idempotency cho repeated calls hoặc extract pure helper để test.
   - Cleanup DB duplicate an toàn: giữ một item tốt nhất mỗi `(runId, code)` theo ưu tiên `applied_ok > pending`, rồi xoá bản sao.

2. Fix video monthly "Videos" semantics.
   - Bug hiện tại: `lib/videoAggregations.ts` line aggregateMonthly tính `uniqueVideos` từ `new Set(arr.flatMap((d) => [])).size || sum(activeVideos)`, nên cột `Videos` đang là raw video-day rows, không phải unique videos.
   - Evidence DB:
     - 2026-01 raw rows 1860, unique videos 60, days 31; UI đang hiển thị Videos=1860.
     - 2026-06 raw rows 6240, unique videos 208, days 30; UI đang hiển thị Videos=6240.
   - Sửa bằng cách giữ `videoAssetId` trong daily aggregate hoặc aggregate monthly trực tiếp từ raw daily rows.
   - Add tests covering repeated video per day/month.
   - Rename columns nếu cần: `Rows` = days aggregated, `Video-days` = raw rows, `Videos` = distinct videoAssetId.

3. Clean metric-source contract across DB/API/UI.
   - Rule sản phẩm: ER chỉ hợp lệ với true reach (`facebook_graph_api_insights` hoặc `meta_business_suite_csv`).
   - Current DB has 20 `facebook_video_metric` posts with non-null `engagementRate`; Posts page displays ER whenever non-null.
   - Fix:
     - create shared helper `isTrueReachSource(source)` and reuse in dashboard, posts, reports, imports, health.
     - backfill DB: set `engagementRate=null` and `score=null` where source is not true reach.
     - show ER only for true reach rows; otherwise show `—` with clear reason.
     - add `meta_business_suite_csv` badge/filter as true reach source. Current Posts filter only says `Reach thật (insights)`, but real data is mostly CSV.

4. Make health check fail on dirty invariants.
   - `scripts/report-dashboard-health.ts` currently prints `Health: OK` even with:
     - all video assets unlinked,
     - one watch-time anomaly,
     - ER count greater than reach count,
     - duplicate reminder items.
   - Convert into PASS/WARN/FAIL:
     - FAIL: duplicate reminder items, non-true-reach rows with ER, build/runtime unavailable.
     - WARN: video assets unlinked if expected, watch-time anomalies, stale import.
   - Return non-zero exit code for FAIL.

## P1 product/UX polish

5. Redesign Posts page for triage, not raw text reading.
   - Current table dumps long post bodies and becomes slow to scan.
   - Use compact row: date, source, type, topic, first 120-180 chars, metric trio, comments/shares, ER status.
   - Move full body into drawer only.
   - Add source filter for `meta_business_suite_csv`; group true reach sources together.

6. Improve visual hierarchy and contrast.
   - The current UI is dominated by dark purple glass cards and dim text. Keep brand feel but make operational dashboards easier to scan.
   - Reduce nested card feel, improve text contrast, and reserve neon gradients for primary actions/status, not every surface.
   - Preserve existing layout and component style where useful; do not rebuild from scratch.

7. Add browser QA.
   - After fixes, run app on `localhost:3123`.
   - Capture screenshots for `/dashboard`, `/posts`, `/imports`, `/video-dashboard`, `/data-reminders`.
   - Verify loaded state, no blank charts, no duplicate monthly items, correct CSV true-reach badges/filter, and correct monthly video counts.
   - Add one real mobile viewport check using Playwright/Chromium if available; the previous in-app viewport override did not change screenshot size.

## Required verification

Run and report:

```bash
npm run typecheck
npm test
npm run lint
npm run build
npm run dashboard:health
```

Also run DB/API checks:

```bash
sqlite3 -header -column prisma/dev.db "SELECT runId, code, COUNT(*) AS c FROM DataReminderItem GROUP BY runId, code HAVING c > 1;"
sqlite3 -header -column prisma/dev.db "SELECT metricSource, COUNT(*) posts, SUM(CASE WHEN engagementRate IS NOT NULL THEN 1 ELSE 0 END) with_er FROM Post GROUP BY metricSource;"
sqlite3 -header -column prisma/dev.db "SELECT substr(date,1,7) month, COUNT(*) raw_rows, COUNT(DISTINCT videoAssetId) unique_videos, COUNT(DISTINCT date) days FROM VideoDailyMetric GROUP BY month ORDER BY month;"
node -e 'fetch("http://localhost:3123/api/video-dashboard").then(r=>r.json()).then(j=>console.log(JSON.stringify(j.data.monthly,null,2)))'
```

Acceptance criteria:

- Repeated calls to `/api/data-reminders/current` do not change row counts.
- Monthly `Videos` equals distinct `videoAssetId`, not raw daily rows.
- No non-true-reach post has non-null ER/score.
- Posts page clearly treats `meta_business_suite_csv` as true reach.
- Health script does not print OK when fail-level invariants are broken.
- Browser screenshots prove loaded, usable screens.
