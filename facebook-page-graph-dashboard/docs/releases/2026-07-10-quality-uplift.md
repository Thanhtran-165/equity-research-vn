# Release: Quality Uplift P0/P1/P2 — 2026-07-10

## Summary

Dashboard raised from "functional" to "operationally reliable for weekly/monthly use". No new features added — all changes are data integrity fixes, UX polish, and verification infrastructure.

## P0 fixes (data integrity)

| Fix | Impact | Root cause |
|---|---|---|
| Data-reminders idempotency | No more duplicate M01-M04 items on repeated API calls | Monthly query used `periodStart startsWith monthKey` which matched YTD range incorrectly |
| Video monthly uniqueVideos | Monthly "Videos" column now shows distinct video count, not raw daily rows | `aggregateMonthly` computed `uniqueVideos` from empty Set fallback |
| Metric-source contract (ER) | 0 non-true-reach posts have ER; `isTrueReachSource()` helper shared across all layers | `facebook_video_metric` posts had ER set during sync; ER formula included clicks |
| Health check PASS/WARN/FAIL | Health script now returns non-zero exit on FAIL-level invariants | Old script always printed "OK" |

## P1 polish (UX)

| Change | Before | After |
|---|---|---|
| Posts page | Full message body dumped in table row, hard to scan | Compact triage table: 150-char preview, source badges, ER status, full content in drawer |
| Source filter | Only "Reach thật (insights)" | Added "📊 MBS CSV (true reach)" + "🎥 Video views" + "👥 Public engagement" |
| Visual contrast | text-dim #8b8ba7 (too dim) | text-dim #a8a8c8 (more readable) |
| ER display | Always shown if non-null | Green for true-reach, amber + `*` for non-true-reach, `—` for null |

## P2 polish (operational reliability)

| Change | Details |
|---|---|
| Video asset linking | Script `scripts/link-video-assets.ts` matches by title + ±1 day window. 16/235 auto-linked (conf≥0.9). 4 candidates for review. 219 unlinked (expected — Meta uses separate ID namespaces for Post export vs Video export). |
| Anomaly UX | Video with avg watch >600s/view now shows amber row background + `⚠ anomaly` badge + "likely Meta data issue" subtext in lifetime table. Not removed, only flagged. |
| Report polish | `lib/reporting/pageReport.ts` uses `isTrueReachSource()` — ER/CTR only computed from true-reach sources in monthly reports. |
| QA manifest | `output/p2-qa-2026-07-10/qa-manifest.md` — all 5 routes verified HTTP 200, no console errors, data correctness confirmed. |

## Known warnings (intentional, not bugs)

1. **219 video assets unlinked** — Meta uses completely different ID systems for Post export vs Video asset export. No permalink or ID overlap exists. Linking requires Graph API enrichment (future).
2. **1 watch-time anomaly** — Video `1573073453955923` has 59 views but 931K seconds watch time (15,787 sec/view). This is Meta's internal data aggregation error. Flagged, not removed.

## Files changed in this release

| File | Change |
|---|---|
| `app/api/data-reminders/current/route.ts` | Idempotency fix + auto-complete logic + YTD exact match |
| `app/api/video-dashboard/route.ts` | Monthly uniqueVideos computed from distinct videoAssetId |
| `app/api/reports/monthly/route.ts` | Added metricSource to query |
| `app/posts/page.tsx` | Full redesign: compact triage table + source filter |
| `app/video-dashboard/page.tsx` | Anomaly badge in lifetime table |
| `app/globals.css` | Contrast improvement |
| `lib/metricSource.ts` | Added `isTrueReachSource()` helper |
| `lib/videoAggregations.ts` | Fixed aggregateMonthly uniqueVideos |
| `lib/reporting/pageReport.ts` | Uses isTrueReachSource for ER/CTR |
| `scripts/report-dashboard-health.ts` | PASS/WARN/FAIL with exit codes |
| `scripts/link-video-assets.ts` | New: video-to-post linking script |
| `scripts/generate-monthly-report.ts` | Added metricSource to query |
| `lib/__tests__/reporting.test.ts` | Updated with metricSource |
| `lib/__tests__/metricSource.test.ts` | Added isTrueReachSource tests |

## DB backup

- **Path**: `backups/chimcut_dashboard_p2_quality_uplift_20260710.db` (15 MB, local only)
- **Previous backup**: `backups/chimcut_dashboard_after_video_dashboard_20260709.db`

## Verification

| Command | Result |
|---|---|
| `npm run typecheck` | ✅ Pass |
| `npm test` | ✅ 243/243 pass |
| `npm run lint` | ✅ No errors |
| `npm run build` | ✅ Pass |
| `npm run dashboard:health` | ✅ PASS (with 2 intentional warnings) |
