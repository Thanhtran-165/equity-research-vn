# Phase 5R MUT-F5 + MUT-F7 Requalification Report

**Date:** 2026-07-21
**Status:** PASS (both gaps requalified on fresh data)

## MUT-F5: Minority Interest Threshold (rule_BR3)

**Verdict: PASS** — 3 tickers with non-zero minority interest, all correctly included in equity bridge.

| Ticker | Minority input | Bridge includes | % of EV | >5% threshold | Correct behavior |
|---|---|---|---|---|---|
| VCB | None (banking N/A) | n/a | n/a | n/a | ✓ |
| BVH | None (insurance N/A) | n/a | n/a | n/a | ✓ |
| HPG | 127B VND | ✓ | 0.10% | no | ✓ (conservative include) |
| MWG | 6.25B VND | ✓ | 0.01% | no | ✓ (conservative include) |
| FPT | **2.30T VND** | ✓ | **4.64%** | no (just under) | ✓ (threshold boundary, conservative include) |

```yaml
exercised: true
tickers_with_minority: 3/5
all_correctly_included: 3/3
unsafe_false_passes: 0
unsafe_omissions: 0
```

FPT at 4.64% EV is the **threshold boundary case** per rule_BR3.3 "Below 5% optional but flag". Engine conservatively includes — safe behavior.

## MUT-F7: Shares Range Sanity

**Verdict: PASS** — 5/5 tickers cross-check shares × price = market_cap exactly.

| Ticker | Shares | Price | Computed MCap | Raw MCap | Diff % | In range 10M-100B |
|---|---|---|---|---|---|---|
| VCB | 8,355,675,094 | 56,700 | 473,766,777,829,800 | 473,766,777,829,800 | 0.000% | ✓ |
| BVH | 742,322,764 | 58,100 | 43,128,952,588,400 | 43,128,952,588,400 | 0.000% | ✓ |
| HPG | 8,442,964,520 | 20,600 | 173,925,069,112,000 | 173,925,069,112,000 | 0.000% | ✓ |
| MWG | 1,475,765,646 | 75,200 | 110,977,576,579,200 | 110,977,576,579,200 | 0.000% | ✓ |
| FPT | 1,714,326,422 | 67,100 | 115,031,302,916,200 | 115,031,302,916,200 | 0.000% | ✓ |

```yaml
tickers_checked: 5/5
all_cross_checks_pass: 5/5
all_range_checks_pass: 5/5
unsafe_false_passes: 0
```

Cross-check exact match (0.000% diff) — vnstock `Trading.price_history` provides consistent `total_shares`, `close`, `market_cap`.

## Both gaps from Phase 4 → closed

```yaml
phase_4_carried_gaps:
  MUT_F5:
    status_then: DOCUMENTED_NON_BLOCKING_GAP (no live evidence)
    status_now: EXERCISED + PASS (3 tickers with minority, all correctly included)
  MUT_F7:
    status_then: DOCUMENTED_NON_BLOCKING_GAP (no live evidence)
    status_now: EXERCISED + PASS (5/5 cross-check exact match)
```

Both gaps originally documented in Phase 4E have been properly requalified on fresh live data in Phase 5R.
