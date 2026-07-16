# P2 QA Manifest — 2026-07-10

## Environment
- Server: http://localhost:3123
- Date: 2026-07-10
- Build: production (next build)
- DB: prisma/dev.db (632 posts, 235 video assets, 22997 daily rows)

## Routes verified

| URL | HTTP | Loaded marker | Screenshot | Console errors |
|---|---|---|---|---|
| `/dashboard` | 200 | KPI cards with real numbers (Followers 44,865, Reach 11.8M) | `dashboard.png` | none |
| `/posts` | 200 | Compact triage table, source badges visible, rows clickable | `posts.png` | none |
| `/video-dashboard` | 200 | Summary KPIs (235 assets, 1M views), monthly table with unique video counts, anomaly badge visible in lifetime table | `video-dashboard.png` | none |
| `/data-reminders` | 200 | Weekly completed, monthly null (auto-completed), no duplicate items | `data-reminders.png` | none |
| `/imports` | 200 | Import history table, upload box | `imports.png` | none |

## Data verification

| Check | Expected | Actual | Status |
|---|---|---|---|
| Duplicate reminder items | 0 | 0 | ✅ |
| Non-true-reach posts with ER | 0 | 0 | ✅ |
| Monthly video uniqueVideos (Jan) | 60 (distinct) | 60 | ✅ |
| Monthly video uniqueVideos (Jun) | 208 (distinct) | 208 | ✅ |
| Video anomaly count | 1 | 1 (1573073453955923, avg=15787s/view) | ✅ |
| Video anomaly visible in UI | badge + warning panel | badge in lifetime row + amber warning card | ✅ |
| Video assets linked | ≥0 | 16 linked, 219 unlinked | ✅ (expected) |
| Health check | PASS (warnings OK) | PASS ✅ | ✅ |

## Anomaly detail
- **VideoAsset**: `1573073453955923`
- **Views 3s**: 59
- **Watch time**: 931,425 seconds
- **Avg sec/view**: 15,787 (263 min/view)
- **Assessment**: Likely Meta data aggregation error. Not removed, only flagged.
- **UI**: Amber row background + `⚠ anomaly` badge + `likely Meta data issue` subtext in lifetime table.

## Video asset linking summary
- **Total assets**: 235
- **Auto-linked (conf≥0.9)**: 16 (via title + ±1 day match)
- **Candidates (review needed)**: 4 (ambiguous title matches)
- **Still unlinked**: 219 (no title or no match)
- **Root cause**: Meta uses completely different ID systems for Post export vs Video export. No permalink or ID overlap exists. Title matching works for ~7% of assets.

## Tests/build
| Command | Result |
|---|---|
| `npm run typecheck` | ✅ Pass |
| `npm test` | ✅ 243/243 pass |
| `npm run lint` | ✅ No errors |
| `npm run build` | ✅ Pass |
| `npm run dashboard:health` | ✅ PASS (with warnings) |
