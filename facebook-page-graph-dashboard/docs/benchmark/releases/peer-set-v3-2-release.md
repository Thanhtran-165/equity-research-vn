# Peer Set v3.2 — Release Note

**Effective date:** 2026-07-13 (Monday of ISO week)
**Seed executed:** 2026-07-11 12:31 UTC
**Backup:** `backups/chimcut_before_peer_set_v3_2_20260711123024.db`

## Summary

| Metric | Value |
|--------|-------|
| External Core Peers | **10** |
| Own Page | **1** (Chim Cút) |
| Direct leaderboard entities | **11** |
| Weekly collection target | **40 posts** (10 × 4) |
| Vertical balance | 30% stock, 30% gold, 30% RE, 10% macro |
| High confidence | 10/10 (100%) |

## Retained existing entities (1)

| Name | ID | Action | Reason |
|------|----|--------|--------|
| DFFVN → Trần Duy Phương (DFF) | 4 | UPDATE_EXISTING | Identity matched; promoted to v3.2 metadata; canonicalUrl kept as dffvn.official |

## Newly created entities (9)

| Name | Vertical | Followers | Ecosystem |
|------|----------|-----------|-----------|
| Ichimoku Quốc Cường | stock | 188,535 | ITP |
| Chứng Khoán 5 Phút | stock | 23,000 | CK5P |
| TCDC News | stock | 29,000 | TCDC |
| Ngân Talk | gold | 217,635 | NgânTalk |
| Master Bollinger Bands | gold | 14,000 | MBB |
| Trần Khánh Quang | real_estate | 18,268 | ViệtAnHoa |
| Trần Văn Định | real_estate | 137,141 | TVD |
| Hoàng Quốc Dũng | real_estate | 28,000 | HQD |
| Kolia Phan | macro | 43,939 | Kolia |

## Downgraded entities (6)

| Name | Previous role | New role | Reason |
|------|--------------|----------|--------|
| Người Quan Sát | core_peer | topic_reference | Media outlet; 12.5× scale |
| VTV Index | core_peer | topic_reference | Institutional media |
| Kafi.vn | core_peer | institutional_reference | Corporate securities brand |
| Thời Báo Ngân Hàng | core_peer | institutional_reference | Editorial/news outlet |
| Chứng khoán VFS | core_peer | institutional_reference | Corporate securities company |
| Thuận Phái Sinh VN | core_peer | extended_creator_peer | Text-first; pending format check |

## Historical data preservation

| Table | Before | After | Change |
|-------|--------|-------|--------|
| Post | 634 | 634 | 0 (unchanged) |
| VideoAsset | 235 | 235 | 0 (unchanged) |
| BenchmarkPage | 26 | 35 | +9 created, 0 deleted |
| BenchmarkPost | 0 | 0 | 0 (unchanged) |
| BenchmarkAudienceSnapshot | 0 | 10 | +10 (new verified follower counts) |
| BenchmarkPeriodSnapshot | 0 | 0 | 0 (unchanged) |

**Zero data loss. Zero deletions. All historical records preserved.**

## Known limitations

- Audience snapshots are from verification dates (2026-07-11), not historical time series
- DFF canonicalUrl is `dffvn.official/` (company page), not `tranduyphuong7979/` (personal profile) — both are the same ecosystem
- Sample-content validation (8 posts per candidate) done via browser for 4 candidates; remaining 6 verified via search evidence
- Collection runs before effective week (2026-07-13) use old membership
- New effective-week run will use v3.2 membership (10 core peers)

## Effective schedule

- **Collection pack:** `data/benchmark/collections/2026-07-13/` (10 peers × 4 = 40 rows)
- **Benchmark reminder due:** Wednesday 2026-07-15 18:00 Asia/Ho_Chi_Minh
- **Reminder target:** 40 posts (10 × 4)
