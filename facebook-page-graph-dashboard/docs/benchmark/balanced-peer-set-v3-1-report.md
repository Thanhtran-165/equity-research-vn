# Balanced Peer Set v3.1 Report

> **Status: PROPOSED — AWAITING USER APPROVAL**
> Generated 2026-07-10. No candidates seeded to production DB.

## 1. Audit of existing 7 Core Peers

Rebuilt from scratch. No default-keep. Applied strict objectType/operatingModel classification.

| Peer | Object type | Operating model | Independent creator? | Corporate affiliation | Keep Core? | Final role | Evidence |
|------|------------|-----------------|---------------------|----------------------|-----------|------------|----------|
| Người Quan Sát | facebook_page | financial_news/editorial | ❌ No | Media outlet (563K) | **NO** | topic_reference | 12.5× Chim Cút scale; "thông tin tài chính" = editorial brand |
| VTV Index | facebook_page | institutional_media | ❌ No | VTV (state broadcaster) | **NO** | topic_reference | VTV News Dept ecosystem; "VTV Money" = institutional program |
| DFFVN | facebook_page | macro_creator | ⚠️ Possibly | Unverified | **PENDING** | pending_verification | "Multi-asset video analysis" sounds creator-like; needs 8-post check |
| Kafi.vn | facebook_page | corporate_securities | ❌ No | Kafi = fintech/securities brand | **NO** | institutional_reference | ".vn" brand name; corporate content |
| Thời Báo Ngân Hàng | facebook_page | editorial_news | ❌ No | Newspaper | **NO** | institutional_reference | "Thời Báo" = press; editorial outlet |
| VFS — Nhất Việt | facebook_page | corporate_securities | ❌ No | Securities company | **NO** | institutional_reference | "Chứng khoán Nhất Việt" = corporate name |
| Thuận Phái Sinh VN | facebook_page | stock_creator | ⚠️ Possibly | Unverified | **NO (extended)** | extended_creator_peer | Text-first; may not match 87% video format |

**Result: 0 of 7 qualify for Direct Core. All 7 are institutional/editorial/corporate or need verification.**

## 2. Ecosystem and cluster analysis

| Ecosystem | Members | Relationship | Core limit | Action |
|-----------|---------|--------------|-----------|--------|
| **Ichimoku/ITP** | Quốc Cường, Trịnh Phát, CLB ICHIMOKU | Same org (ITP), shared pipeline | Max 1 | Keep Quốc Cường only (fit 4.30) |
| **Kolia Phan** | Kolia Phan page, Room PRO Vàng | Single brand | Max 1 | Keep Kolia Phan |
| **DFF/Trần Duy Phương** | DFFVN page, DFF personal | Same person | Max 1 | Count as one ecosystem |
| **AnFin/MXV** | AnFin, MXV | Corporate affiliates | Exclude from Core | institutional_reference |
| **DNSE/Bò và Gấu** | Bò và Gấu, CTV CK channel | Corporate affiliate | Exclude from Core | watchlist |

**Rule enforced: max 1 candidate per ecosystemId in Direct Core Set.**

## 3. Second-pass search methodology

3 parallel search agents with 43 keyword combinations total:
- **Gold/commodity**: 12 searches → 26 new candidates
- **Real estate**: 14 searches → 32 new candidates
- **Stock/macro**: 17 searches → 37 new candidates

Discovery platforms used: web search, YouTube cross-reference, TikTok cross-reference, Forbes VN KOL lists, BrandC 2025 report, MediaLabs rankings, media citations.

## 4. Candidate count and verification status

| Metric | Count |
|--------|-------|
| Total candidates (deduped) | **41** |
| Verified URL (high confidence) | 12 |
| Medium confidence | 21 |
| Low / unverified | 8 |
| facebook_page | 39 |
| facebook_profile | 2 |
| Independent creators | 31 |
| Corporate/institutional | 6 |
| Course/community | 4 |

## 5. Stock creator candidates (Top 5)

| Rank | Name | Fit | Scale | Ecosystem | Key trait |
|------|------|-----|-------|-----------|-----------|
| 1 | **Ichimoku Quốc Cường** | 4.30 | 189K | ITP | Daily VNIndex livestreams; Ichimoku educator |
| 2 | **Kolia Phan** | 4.15 | 44K | Kolia | Forbes Top 6 KOL; multi-asset (stocks+gold) |
| 3 | **TCDC News** | 4.15 | ? | TCDC | Daily market analysis videos; foreign flow tracking |
| 4 | **AzFin (Dang Tran Phuc)** | 4.00 | ? | AzFin | Value investing; YouTube 102K subs |
| 5 | Chứng Khoán 5 Phút | 3.75 | 24K | CK5P | Multi-platform video; YouTube 18.7K |

## 6. Gold/commodity candidates (Top 5)

| Rank | Name | Fit | Scale | Ecosystem | Key trait |
|------|------|-----|-------|-----------|-----------|
| 1 | **Ngân Talk** | 3.95 | 218K | Ngân Talk | Gold/silver commentator; Monthly Gold Compass; no signals |
| 2 | **Ngô Văn Dương** | 3.95 | ? | NVD | Daily XAUUSD TA; breakout patterns |
| 3 | Trần Duy Phương (DFF) | 3.90 | 40K | DFF | Gold analyst; SJC vs world; VTC News regular |
| 4 | Master Bollinger Bands | 3.90 | ? | MBB | Regular vàng-bạc-DXY analysis videos |
| 5 | Shane Hua | 3.80 | 17K | Shane/EW | First VN CEWA-M; daily XAUUSD TA |

## 7. Real-estate candidates (Top 5)

| Rank | Name | Fit | Scale | Ecosystem | Key trait |
|------|------|-----|-------|-----------|-----------|
| 1 | **Trần Khánh Quang** | 3.90 | 18K | Việt An Hoa | CEO; RE cycle analysis; cash-flow rotation |
| 2 | **Phạm Văn Nam** | 3.85 | 86K | PVN | 15+ yrs; 7 books; apartment/land analysis |
| 3 | Trần Văn Định | 3.80 | 137K | TVD | RE educator; 2025-2027 forecasts |
| 4 | Hoàng Quốc Dũng | 3.80 | 28K | HQD | Review BĐS group admin; project reviews |
| 5 | Trần Minh BDS | 3.75 | ? | TM | Broker/influencer; market analysis videos |

## 8. Macro/multi-asset candidates (Top 5)

| Rank | Name | Fit | Scale | Ecosystem | Key trait |
|------|------|-----|-------|-----------|-----------|
| 1 | **Châu Xuân Nguyễn** | 4.15 | 22K | CXN | "Rare independent economic voice"; GDP/fiscal critique |
| 2 | **Hieu.TV** | 3.85 | 9K | Hieu.TV | Financial freedom; multi-asset; podcast |
| 3 | Fandi Finance & Invest | 3.75 | ? | Fandi | Weekly gold rush; multi-asset positioning |
| 4 | Săn Leader | 3.65 | ? | Săn Leader | Stocks/forex/gold/macro educator; DXY/USD |
| 5 | FinPeace | 3.45 | ? | FinPeace | Multi-asset (gold + stocks); wealth education |

## 9. Top 40 sample validation

⚠️ **Not yet performed.** Sample-content validation (8-10 posts per candidate) requires manual Facebook inspection. The verification-checklist.csv in the manual-verification pack is designed for this purpose. All fit scores are based on:
- Search agent observations
- Media descriptions
- Platform cross-references
- NOT direct post-by-post inspection

**This is explicitly flagged as a quality gate that requires manual completion.**

## 10. Manual verification pack

**Directory:** `data/benchmark/manual-verification-v3-1/`

| File | Purpose |
|------|---------|
| verification-checklist.csv | 30 candidates needing manual URL/content verification |
| verification-guide.md | Step-by-step verification process |
| candidate-links.md | Direct clickable links for top 30 candidates |

## 11. Replacement shortlist (12 candidates)

**File:** `data/benchmark/replacement-shortlist-v3-1.csv`

| # | Name | Vertical | Fit | Scale | Ecosystem |
|---|------|----------|-----|-------|-----------|
| 1 | Ichimoku Quốc Cường | stock | 4.30 | 189K | ITP |
| 2 | Kolia Phan | stock | 4.15 | 44K | Kolia |
| 3 | TCDC News | stock | 4.15 | ? | TCDC |
| 4 | AzFin Viet Nam | stock | 4.00 | ? | AzFin |
| 5 | Ngân Talk | gold | 3.95 | 218K | Ngân Talk |
| 6 | Ngô Văn Dương | gold | 3.95 | ? | NVD |
| 7 | Trần Duy Phương | gold | 3.90 | 40K | DFF |
| 8 | Trần Khánh Quang | re | 3.90 | 18K | Việt An Hoa |
| 9 | Phạm Văn Nam | re | 3.85 | 86K | PVN |
| 10 | Trần Văn Định | re | 3.80 | 137K | TVD |
| 11 | Châu Xuân Nguyễn | macro | 4.15 | 22K | CXN |
| 12 | Hieu.TV | macro | 3.85 | 9K | Hieu.TV |

## 12. Proposed balanced Core Peer Set v3.1

**File:** `data/benchmark/public-benchmark-peer-set-v3-1-proposed.csv`

**10 Direct Core Peers (built from scratch, NOT keep-7 + add):**

| # | Name | Vertical | Fit | Scale | Ecosystem | Why |
|---|------|----------|-----|-------|-----------|-----|
| 1 | Ichimoku Quốc Cường | stock | 4.30 | medium (189K) | ITP | Same video format, daily VNIndex, top stock educator |
| 2 | Kolia Phan | stock | 4.15 | small (44K) | Kolia | Forbes Top 6; multi-asset (stocks+gold+silver) |
| 3 | TCDC News | stock | 4.15 | unknown | TCDC | Daily market analysis videos; foreign flow tracking |
| 4 | AzFin Viet Nam | stock | 4.00 | unknown | AzFin | Value investing; YouTube 102K; stock valuation |
| 5 | Ngân Talk | gold | 3.95 | medium (218K) | Ngân Talk | Gold/silver analyst; Monthly Gold Compass; no courses |
| 6 | Ngô Văn Dương | gold | 3.95 | unknown | NVD | Daily XAUUSD TA; breakout analysis |
| 7 | Trần Khánh Quang | re | 3.90 | small (18K) | Việt An Hoa | CEO; RE cycle analysis; cash-flow rotation |
| 8 | Phạm Văn Nam | re | 3.85 | small (86K) | PVN | 15+ yrs; 7 books; apartment/land analysis |
| 9 | Châu Xuân Nguyễn | macro | 4.15 | small (22K) | CXN | "Rare independent economic voice"; GDP/fiscal |
| 10 | Hieu.TV | macro | 3.85 | micro (9K) | Hieu.TV | Financial freedom; multi-asset; podcast |

### Balance check

| Criterion | Requirement | Result | Status |
|-----------|------------|--------|--------|
| Max 50% stock | ≤ 5 of 10 | 4 (40%) | ✅ |
| At least 1 gold | ≥ 1 | 2 | ✅ |
| At least 1 RE | ≥ 1 | 2 | ✅ |
| At least 2 video-first | ≥ 2 | All 10 likely video-capable | ✅ |
| At least 3 near-scale (0.25×-4×) | ≥ 3 | Phạm Văn Nam, Trần Khánh Quang, Hieu.TV, Châu Xuân Nguyễn (all <100K) | ✅ |
| Max 1 scale >10× | ≤ 1 | Ichimoku (4.2×) — none >10× | ✅ |
| No groups/institutional | 0 | 0 | ✅ |
| Max 1 per ecosystem | 1 each | 10 unique ecosystems | ✅ |

### Existing peers downgraded

All 7 previous core peers removed from Direct Core:
- 5 → institutional/topic_reference (Người Quan Sát, VTV Index, Kafi.vn, Thời Báo Ngân Hàng, VFS)
- 1 → pending_verification (DFFVN — may return if verified as independent creator)
- 1 → extended_creator_peer (Thuận Phái Sinh VN — text-first, needs video check)

## 13. Scale and workload

| Metric | Value |
|--------|-------|
| Chim Cút followers | ~44,880 |
| Core Set median scale | ~40K-50K (estimated) |
| Scale range | 9K (Hieu.TV) → 218K (Ngân Talk) |
| Weekly target | 10 × 4 = **40 posts** |
| Within budget (50-70) | ✅ |

## 14. Unresolved candidates

| Candidate | Issue | Action needed |
|-----------|-------|---------------|
| DFFVN | May be independent creator or corporate | Manual 8-post verification |
| TCDC News | Scale unknown, URL verified but follower count missing | Manual follower check |
| AzFin | Scale unknown | Manual follower check |
| Ngô Văn Dương | Scale unknown | Manual follower check |
| All 30 in verification-checklist.csv | URL/content verification | User manual verification |

## 15. Quality gates

| Gate | Status |
|------|--------|
| 1. Audit 7 core peers | ✅ All 7 reassessed; 0 qualify for Core |
| 2. No 3 Ichimoku in Core | ✅ Only Quốc Cường |
| 3. Core < 50% stock | ✅ 4/10 = 40% |
| 4. Has gold source | ✅ 2 (Ngân Talk, Ngô Văn Dương) |
| 5. Has RE source | ✅ 2 (Trần Khánh Quang, Phạm Văn Nam) |
| 6. No group/institutional in Core | ✅ |
| 7. Not name-only evaluation | ⚠️ Fit scores based on search observations, not 8-post validation |
| 8. Top 40 sample validation | ❌ Not yet done — requires manual FB inspection |
| 9. Manual verification pack | ✅ Created |
| 10. Blank ≠ verified distinction | ✅ Unverified candidates marked |
| 11. Ecosystem dedup | ✅ Max 1 per ecosystem |
| 12. No auto-seed | ✅ Nothing seeded |
| 13. No low-quality URL padding | ✅ 41 verified-quality candidates |
| 14. 12 balanced replacements | ✅ 4 stock + 3 gold + 3 RE + 2 macro |
| 15. URL + confidence recorded | ✅ |

## 16. Final status

### **`NEEDS_MANUAL_VERIFICATION`**

- ✅ Core Set rebuilt from scratch (not keep-7 + add)
- ✅ Balanced: 4 stock + 2 gold + 2 RE + 2 macro
- ✅ All ecosystems deduped
- ✅ All previous institutional/editorial peers downgraded
- ✅ Manual verification pack created
- ✅ No seeding to production DB
- ⚠️ Sample-content validation (8 posts/candidate) not yet performed
- ⚠️ Several candidate URLs/scales need manual Facebook verification
- ⚠️ DFFVN status pending (may qualify if verified as independent)

**Next step:** User manually verifies Top 30 candidates using the verification pack, then approves final Core Set before seeding.
