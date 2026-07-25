# RC3 Closure Record — equity-research-vn-1.0.1-rc3
**Date:** 2026-07-19
**Status:** CLOSED — 7/12 PASS, FAIL per owner §9 gate
**Immutable:** artifacts preserved

## Cohort run

```yaml
targeted_hotfix_v1_0_1_rc3:
  completed_runs: 12/12
  pass: 7
  fail_or_rejected: 5
  no_result: 0
  period_inversion_defects: 0
  verdict: FAIL
  artifacts_preserved: true
  patches_during_cohort: 0
  concurrency: 4 (parallel)
  total_wall_clock: ~40 min
```

## Per-run verdict

| Run | Ticker | Status | Pass/Fail | Failed REQs | PI |
|---|---|---|---|---|---|
| TH-FPT-01 | FPT | PASS | 28/28 | — | pass |
| TH-FPT-02 | FPT | PASS | 28/28 | — | pass |
| TH-BVH-01 | BVH | FAIL | 26/28 | REQ-026, REQ-021 | pass |
| TH-BVH-02 | BVH | FAIL | 26/28 | REQ-026, REQ-021 | pass |
| TH-MSN-01 | MSN | PASS | 28/28 | — | pass |
| TH-MSN-02 | MSN | FAIL | 26/28 | REQ-019 (JS syntax), REQ-021 | pass |
| TH-POW-01 | POW | FAIL | 14/28 | 14 REQs (skeleton artifact) | pass |
| TH-POW-02 | POW | PASS | 28/28 | — | pass |
| TH-HPG-01 | HPG | PASS | 28/28 | — | pass |
| TH-HPG-02 | HPG | PASS | 28/28 | — | pass |
| TH-MWG-01 | MWG | PASS | 28/28 | — | pass |
| TH-MWG-02 | MWG | FAIL | rejected | admission_rejected (audit_split false positive) | — |

## RC3 improvements acknowledged (per owner §1)

- `aig_result` structural crash eliminated (ERVN-RUNNER-STATE-001 fixed)
- NO_RESULT reduced from 2 (RC2) to 0 (RC3)
- Period-integrity still detects 0 inversions
- Fail-closed chain working as designed
- Parallel execution cut wall-clock from ~2h to ~40min

## Four RC3 defects (per owner §2)

### ERVN-NA-ENFORCEMENT-002 (BVH-01/02)
- **REQ-026** still fails: "revenue: not found in JS DATA"
- Contract has revenue=null+NOT_APPLICABLE, but encoding not propagated to final artifact
- Needs 7-step trace to find where NOT_APPLICABLE metadata is lost

### ERVN-JS-VALIDITY-001 (MSN-02)
- **REQ-019** fails: `node --check` returns exit 1
- Agent produced JS with syntax error
- Needs `node --check` in pre-admission, not just final verification

### ERVN-CONTENT-DEPTH-001 (POW-01)
- 14 REQs fail: skeleton artifact (16KB) passed admission gate
- File size >20KB threshold is not reliable proxy for completeness
- Needs semantic per-section content depth check

### ERVN-ADMISSION-FALSE-POSITIVE-001 (MWG-02)
- Admission rejected 106KB artifact (22 sections, 12 charts) because audit-split keyword not found
- REQ-003 check is too keyword-dependent
- Needs applicability logic: if no corporate action/split evidence, audit-split is NOT_APPLICABLE

## Owner verdict (2026-07-19 §1)

```yaml
rc3:
  verdict: FAIL
  immutable: true
  improvements_acknowledged: [runner_safety, no_result_zero, parallel_execution]

rc4:
  investigation: AUTHORIZED
  build: CONDITIONAL_ON_ROOT_CAUSE_AND_FIXTURE
  scope: 4 specific defect classes (no other changes)
  stop_rule: if RC4 also fails, evaluate architecture change (deterministic section builder)
```
