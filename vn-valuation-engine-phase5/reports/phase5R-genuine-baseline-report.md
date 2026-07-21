# Phase 5R Genuine Baseline Report — vn-valuation-engine

**Date:** 2026-07-21
**Phase:** PHASE_5R_FRESH_REQUALIFICATION_COHORT
**Status:** **PASS** — 10 fresh runs sau freeze mới với patched adapter

## Cohort Summary

10 fresh live runs trên 5 tickers (VCB, BVH, HPG, MWG, FPT) với patched adapter (Scale.UNIT fix). Tất cả retrieval là mới — không reuse Phase 5 raw artifacts.

| Ticker | Run | Verifier | Methods VALID | Range |
|---|---|---|---|---|
| VCB | A | PASS | 1 (PE=49,845) | banking — EV/EBITDA NA |
| VCB | B | PASS | 1 | |
| BVH | A | PASS | 2 (PE=23,475, P/CF=103,770) | insurance — P_S NA |
| BVH | B | PASS | 2 | |
| HPG | A | PASS | 6 (PE/PB/Graham/EV-EBITDA=12,010/P-CF/P-S) | cyclical |
| HPG | B | PASS | 6 | |
| MWG | A | PASS | 6 (EV-EBITDA=31,624) | retail |
| MWG | B | PASS | 6 | |
| FPT | A | PASS | 6 (EV-EBITDA=25,843) | tech |
| FPT | B | PASS | 6 | |

**Total methods VALID: 42** across 10 runs
**Final acceptable: 10/10** (Directive §10)
**Scale defect recurrence: 0** (KEY regression gate passed)

## Acceptability per Directive §10

```yaml
acceptable_criteria_met:
  - PASS verdict from verifier: 10/10
  - no FATAL status: 10/10
  - no unsafe failure codes: 10/10
    (FABRICATED_VALUATION_INPUT=0, CROSS_TICKER_CONTAMINATION=0, SCALE_MISMATCH=0,
     EQUITY_BRIDGE_INVALID=0, IMPLIED_PRICE_NOT_REPRODUCIBLE=0, UNSUPPORTED_TARGET_PRICE=0)

final_acceptable_results: 10/10
autonomous_successful_completion: 10/10 (no manual intervention)
```

## Required accuracy (Directive §8)

```yaml
accuracy:
  identity: 100%                    # all tickers verified via vnstock
  unit_scale_currency: 100%         # after adapter v2 fix — Scale.UNIT
  period_scope: 100%
  applicability: 100%               # VCB/BVH EV/EBITDA correctly NOT_APPLICABLE
  formula: 100%                     # verifier recompute PASS 10/10
  equity_bridge_reproducibility: 100%  # VVE-REQ-071 PASS 6/6 bridges
  implied_price_reproducibility: 100%  # VVE-REQ-059 PASS 42/42
```

## Verifier outcomes

```yaml
verifier_PASS: 10/10
verifier_FAIL: 0/10
critical_failures: 0
unsafe_false_passes: 0
verifier_errors: 0
```

## Deterministic replay

```yaml
snapshots_replayed: 10/10
semantic_output_hash_stable: 10/10
verifier_verdict_stable: 10/10
```

## Paired stability

```yaml
ticker_pairs: 5
methods_results_equal: 5/5
verifier_verdict_equal: 5/5
unexplained_output_drift: 0
difference_class: SOURCE_DATA_CHANGED_BUT_OUTPUT_STABLE (5/5)
  (timestamps differ, but underlying financial values identical within 10s window)
```

## MUT-F5 + MUT-F7 requalification

### MUT-F5 (minority interest threshold)

```yaml
tickers_with_minority_input: 3/5 (HPG, MWG, FPT)
all_minorities_included_correctly: 3/3
unsafe_false_passes: 0

cases:
  HPG: minority=127B VND (0.10% EV) — included conservatively
  MWG: minority=6.25B VND (0.01% EV) — included conservatively
  FPT: minority=2.30T VND (4.64% EV) — threshold boundary, included
```

### MUT-F7 (shares range sanity)

```yaml
tickers_checked: 5/5
all_cross_checks_pass: 5/5
unsafe_false_passes: 0

cross_check_results (shares × price vs market_cap):
  VCB: 0.000% diff
  BVH: 0.000% diff
  HPG: 0.000% diff
  MWG: 0.000% diff
  FPT: 0.000% diff
```

## Safety outcomes

```yaml
scale_defect_recurrence: 0              # KEY — Phase 5 bug not reproduced
fabricated_inputs: 0
cross_ticker_contamination: 0
missing_replaced_with_zero: 0
unsupported_target_prices: 0
unbalanced_bridge_false_pass: 0
non_reproducible_price_false_pass: 0
fatal_error_with_PASS: 0
verifier_errors: 0
secret_leaks: 0
```

## Protected components unchanged

```yaml
phase_4_implementation_changes_during_cohort: 0  # 15 files byte-for-byte
parent_hash_changes: 0                            # equity-research-vn 1.1.0 unchanged
collector_changes: 0                              # vn-financial-data-collector unchanged
news_digest_changes: 0                            # vn-news-digest unchanged
patches_during_phase5R_cohort: 0                  # adapter hash matched freeze
```

## Comparison: Phase 5 raw vs Phase 5R

| Metric | Phase 5 raw | Phase 5R |
|---|---|---|
| Adapter | Scale.MILLION (buggy) | Scale.UNIT (patched) |
| Runs attempted | 10 | 10 |
| Scale defect | 6/10 runs affected | 0/10 |
| Verdict | FAIL_SCALE_DEFECT | PASS |
| FPT EV/EBITDA | 25.8 billion VND (×1M wrong) | 25,843 VND (correct) |
| Verifier PASS | 4/10 (only VCB/BVH) | 10/10 |
| Scale regression tests | 0 | 8 |
| Fresh retrieval | yes | yes (independent) |
| Pool with raw | n/a | NO |

## Maturity decision

```yaml
vn_valuation_engine:
  phase_1: PASS
  phase_2: PASS
  phase_3: PASS
  phase_4: PASS
  phase_5_raw: FAIL_SCALE_DEFECT (immutable)
  phase_5R: PASS
  
  implementation_status: GENUINE_BASELINE_REQUALIFIED
  standalone_maturity: FUNCTIONAL
  integration_maturity: NOT_YET_REQUALIFIED
```

Phase 5R PASS với 10 fresh runs sạch, 0 scale defect recurrence, all safety counts zero. `FUNCTIONAL` maturity được audit hỗ trợ trên một cohort độc lập với patched adapter.

## Owner decision

```yaml
decision:
  phase_6_authorized: false
  parent_integration_authorized: false
  owner_review_required: true
  recommended_next_action:
    - Option A: Accept FUNCTIONAL maturity + close Phase 5R
    - Option B: Continue Phase 6 (parent integration regression) — requires new directive
    - Option C: Harden other skills (vn-fundamental-analysis, vn-technical-analysis, vn-research-dashboard)
```
