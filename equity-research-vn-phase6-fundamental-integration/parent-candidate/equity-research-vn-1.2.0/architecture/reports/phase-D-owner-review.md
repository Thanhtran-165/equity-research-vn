# Phase D — Integrated Synthetic Validation Report
**Date:** 2026-07-20
**Status:** Phase D PASS

## Gate Results

```yaml
phase_D_gate:
  total_cases_completed: 39
  clean_controls_pass: 6/6 ✓
  corrupted_cases_fail_correctly: 12/12 ✓ (renderer renders, post-render layer detects)
  section_isolation_cases: 6/6 ✓ (failures isolated, DATA preserved)
  section_retry_cases: 5/5 ✓ (DATA hash always preserved)
  applicability_consistency: 6/6 ✓
  reproducibility: 3/3 ✓ (semantic IR hash stable)
  BVH_NOT_APPLICABLE: 7/7 checks ✓
  critical_mutations_survived: 0 ✓
  sanitizer_bypass: 0 ✓
  contradictory_verdicts: 0 ✓
  cross_ticker_contamination: 0 ✓
  deterministic_reproducibility: PASS ✓
```

## Case Breakdown

| Category | Cases | Pass | Description |
|----------|-------|------|-------------|
| clean_e2e | 6 | 6 | All 6 tickers produce valid deterministic HTML |
| corrupted | 12 | 12 | Renderer renders corrupted IR; post-render gates detect |
| section_isolation | 6 | 6 | 1 section fails → others preserved, DATA unchanged |
| section_retry | 5 | 5 | Retry preserves DATA hash in all cases |
| applicability | 6 | 6 | All layers use same decision_hash |
| reproducibility | 3 | 3 | Same input → same output (semantic hash stable) |
| BVH control | 1 | 1 | 7 NOT_APPLICABLE checks all PASS |

## Key Findings

1. **Deterministic shell is secure**: no narrative injection can modify DATA, charts, or HTML structure
2. **Section isolation works**: one section failure doesn't cascade to others
3. **DATA is immutable**: section generation/retry never changes financial data hash
4. **Reproducibility confirmed**: same source → same deterministic output
5. **BVH NOT_APPLICABLE end-to-end**: revenue=null, status, rule, chart absent, zero not displayed

## Decision

```yaml
decision:
  phase_D: PASS
  phase_E_recommendation: AUTHORIZE (12 genuine section-generation runs)
  phase_E_execution: NOT_STARTED
  owner_review_required: true
```
