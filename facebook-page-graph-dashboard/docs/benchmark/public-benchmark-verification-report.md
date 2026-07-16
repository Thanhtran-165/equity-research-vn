# Public Benchmark Verification & Curation Report

## 1. Top 30 Verification Results

| Status | Count |
|---|---|
| Verified with URL | 24 |
| URL uncertain (needs manual) | 4 |
| Duplicate identified | 1 (#17 theanh98 = #86 duplicate) |
| Group (not Page) | 3 (#1, #2, #3 → groups, not leaderboard-eligible) |

### Correction to data source note

Meta Business Suite exports are only available for pages the user manages (Chim Cút). For competitor pages, data collection uses **public metrics observation + manual entry + manually prepared CSV** only. Future Graph API Advanced Access may enable automated collection.

## 2. Invalid / Duplicate / Inactive Candidates

| Candidate | Problem | Evidence | Recommended action |
|---|---|---|---|
| #17 Phạm Thế Anh (theanh98) | Duplicate of #86 | Same URL facebook.com/theanh98/ | Merge — keep one entry |
| #10 Bò và Gấu (Bears & Bulls) | No URL found | Web search returned name only but no FB page | Exclude from Top 30 → moved to watchlist |
| #1-6 (stock groups) | Object type = Group, not Page | URL contains /groups/ | Move to Group Reference, not Core Peer |
| #13 Stockbiz | URL uncertain | Entity confirmed but FB URL not found | Needs manual review |
| #25-26 TS. Cấn Văn Lực, TS. Lê Xuân Nghĩa | Profile, not Page + URL uncertain | Experts confirmed via web search but no clean FB URL | Creator Reference, low confidence |

## 3. Object Type Breakdown

| Type | Count | Treatment |
|---|---|---|
| facebook_page | 19 | Eligible for Core Peer / leaderboard |
| facebook_group | 3 | Group Reference only — not in direct leaderboard |
| facebook_profile | 4 | Creator Reference — separate from Page leaderboard |
| unknown | 4 | Needs manual verification |

## 4. Public Metric Availability

| Metric | Visible on most pages? | Notes |
|---|---|---|
| Reactions | ✅ Yes | Public on all verified pages |
| Comments | ✅ Yes | Public on all verified pages |
| Shares | ⚠️ Partial | Often hidden in newer UI; visible on some |
| Video views | ⚠️ Partial | Only on video posts; varies by page |
| Follower count | ⚠️ Partial | Many show "likes" not "followers"; some unknown |

### Data Collection Feasibility Distribution

| Score | Count | Meaning |
|---|---|---|
| 5 (easy) | 5 | All metrics visible, active posting |
| 4 (mostly visible) | 16 | Most metrics visible, minor gaps |
| 3 (partial) | 5 | Missing some metrics (e.g., shares hidden) |
| 2 (unstable) | 4 | Profile pages with uncertain data, URL gaps |
| 1 (unusable) | 0 | — |

## 5. Peer Set v2

**File**: `data/benchmark/public-benchmark-peer-set-v2.csv` — 25 entries

## 6. Core Peers (8 Facebook Pages)

| Name | Scale | Fit v2 | Why core peer |
|---|---|---|---|
| **Người Quan Sát** | Medium (563K) | 4.45 | Closest analytical peer, same "observer" positioning |
| **VTV Index** | Small | 4.30 | Same video reels format + VN-Index/macro topics |
| **Phạm Thế Anh** | Micro | 4.30 | Individual creator doing stock analysis video |
| **DFFVN** | Micro | 3.80 | Multi-asset (stocks/macro/gold) video analysis |
| **Kafi.vn** | Small | 3.75 | Multi-commodity daily (gold/oil/inflation) |
| **Thời Báo Ngân Hàng** | Small | 3.75 | Banking/rates/FX/gold sector outlet |
| **VFS (Nhất Việt)** | Micro | 3.60 | Multi-asset page (stocks/FX/gold) |
| **Thuận Phái Sinh VN** | Micro | 3.50 | Niche stock critique, text-focused |

**Scale balance**: 4 micro, 3 small, 1 medium — good spread for Chim Cút (44K = micro/small boundary).

## 7. Topic and Format References (12 sources)

| Role | Count | Examples |
|---|---|---|
| Topic reference | 8 | CafeF (1.5M), CafeBiz (1.97M), VnEconomy, Vietstock, VnExpress, 24H Money, Kinh Tế Sài Gòn, Batdongsan.com.vn |
| Format reference | 1 | Forbes Vietnam (premium longform) |
| Creator reference | 1 | TS. Nguyễn Trí Hiếu (banking expert profile) |
| Group reference | 2 | Diễn đàn Giá Vàng, Cộng đồng đầu tư gold/oil |

## 8. Weekly Collection Workload

| Set | Sources | Posts/source | Frequency | Estimated weekly rows |
|---|---|---|---|---|
| Core peers | 8 | 4 avg | Weekly | **32** |
| Topic references | 8 | 2 avg | Monthly (~2/week) | **4** |
| Total active weekly | 16 | — | — | **~36 rows/week** |

✅ **Within 50-70 posts/week budget.** Comfortable for manual collection.

## 9. Candidates Still Needing Manual Review

| Candidate | Issue | Action needed |
|---|---|---|
| Master Anh Đức | No FB URL | Search Facebook manually for profile |
| TS. Cấn Văn Lực | No FB URL | Check if he has a personal profile or page |
| TS. Lê Xuần Nghĩa | No FB URL | Same — may not have active FB presence |
| Stockbiz | URL uncertain | Verify facebook.com/stockbiz or similar |
| F247 | Verified but text-only | Consider for watchlist, not core |

## 10. Recommendation

✅ **Ready to code Public Benchmark module** with Peer Set v2 (8 core peers + 12 references).

**Collection workflow for user:**
1. Each Monday: manually observe 8 core peer pages
2. Record 3-5 top posts per page (reactions, comments, shares, permalink)
3. Enter into CSV using existing CompetitorMetricSnapshot import
4. Dashboard computes benchmark score from public engagement metrics

**NOT ready for:**
- Automated scraping (compliance risk)
- Meta Business Suite export of competitor pages (impossible — only for owned pages)
- Cross-platform benchmark (TikTok/YouTube — no data sources identified)
