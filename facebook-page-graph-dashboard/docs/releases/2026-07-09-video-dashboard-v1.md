# Release: Video Dashboard v1 — 2026-07-09

## Summary

Dashboard video/reels cho Page Chim Cút dựa trên dữ liệu Meta Business Suite CSV.

## Data snapshot

| Metric | Value |
|---|---|
| Posts imported (CSV) | **544** |
| Total post reach (summed) | **11.826.390** |
| Posts from Graph API sync | 84 (facebook_video_metric) |
| Video assets (total) | **235** |
| Lifetime videos (V01) | **145** |
| Daily-only videos (V02 only) | **90** |
| VideoDailyMetric rows | **22.997** |
| Date range (daily) | 2026-01-01 → 2026-07-08 |

## Data source

- **Source**: Meta Business Suite CSV export (manual, user-driven)
- **metricSource**: `meta_business_suite_csv`
- **Files applied**: 2 Posts Lifetime (P01 + P01-variant) + 1 Video Lifetime (V01) + 7 Video Daily monthly (V02 Jan–Jul)
- **Files skipped**: G02 Page Daily (engagement-only, no reach/impressions)

## Metric definitions

| Metric | Formula |
|---|---|
| Social engagement rate (ER) | (reactions + comments + shares) / reach — **excludes clicks** |
| Click-through rate (CTR) | clicks / reach |
| Total activity | reactions + comments + shares + clicks |
| avgWatchTimePerView | watchTimeSeconds / videoViews3s |
| Summed reach | Σ reach across videos/days — **NOT unique Page reach** |

## Known limitations

1. **VideoAsset not linked to Post** — Meta uses different ID systems for posts vs video assets. Linking requires Graph API enrichment (future).
2. **No Graph API enrichment** — permalinks not fetched for VideoAsset.
3. **G02 Page Daily skipped** — only has engagement/negative feedback, no reach/impressions.
4. **1 watch-time anomaly flagged** — video `1573073453955923` has 15.787 sec/view (likely Meta data error). Not removed, only flagged.
5. **Summed reach ≠ unique reach** — dashboard labels use "Summed reach" to clarify.
6. **Video titles mostly "(untitled)"** — Meta V01/V02 export doesn't include full captions for most videos.

## Schema changes since last release

| Model | Added |
|---|---|
| Post | `externalPostId` field (unique, nullable) — stores raw Facebook post ID |
| VideoAsset | new — video asset registry |
| VideoLifetimeMetric | new — V01 lifetime metrics |
| VideoDailyMetric | new — V02 daily time-series (unique: videoAssetId + date + source) |

## Bug fixes applied

| Bug | Impact | Fix |
|---|---|---|
| `parseNumber` ×1000 | Watch time values 1000× too large | Fixed heuristic: dot = thousand separator only if integer part ≤ 3 digits |
| `parseDate` timezone shift | Jan 1 → Dec 31 (UTC-7 offset) | Return YYYY-MM-DD directly, no `toISOString()` |
| `calculateEngagementRate` | ER included clicks | Changed to `(reactions + comments + shares) / reach` only |
| Paid impressions mapped as organic | "Lượt hiển thị quảng cáo" → impressions | Added `isPaidHeader()` filter |
| Shares/clicks/watchTime not detected | Missing VI aliases | Added "lượt chia sẻ", "tổng lượt click", "số giây xem" aliases |
| Video files applied to Post model | V02 created fake Post IDs | Added `isPostsFile` guard — video files skip Post apply |

## Database backup

- **Path**: `backups/chimcut_dashboard_after_video_dashboard_20260709.db` (local only, not committed)
- **Size**: ~15 MB
- **Contains**: 628 Posts + 235 VideoAssets + 145 LifetimeMetrics + 22.997 DailyMetrics

## Tests

- 196/196 pass
- Coverage: parseNumber, parseDate, columnDetection, matchPosts, applyImportedInsights, exportPlan, fileCleanup, videoAggregations, metricSource, dashboardMode, metrics
