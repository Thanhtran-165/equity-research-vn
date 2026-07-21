# RC2 Closure Record — equity-research-vn-1.0.1-rc2
**Date:** 2026-07-19
**Status:** CLOSED — 7/12 PASS, FAIL per owner §9 gate
**Immutable:** artifacts + summary preserved unchanged

## Cohort run

```yaml
targeted_hotfix_v1_0_1_rc2:
  completed_runs: 12/12
  pass: 7
  fail: 3
  no_result: 2
  verdict: FAIL
  artifacts_preserved: true
  patches_during_cohort: 0
  candidate_hash: 04f3005f1cd90609ef79862a7aea183c9d33871c8c99215271a6895bc966b0bf
  start: 2026-07-19T10:30
  end:   2026-07-19T12:43
```

## Per-run verdict

| Run | Ticker | Status | Pass/Fail | Failed REQs | PI |
|---|---|---|---|---|---|
| TH-FPT-01 | FPT | FAIL | 16/29 | 13 (REQ-003/005/006/008/009/012/014/015/018/025...) | pass |
| TH-FPT-02 | FPT | PASS | 29/29 | — | pass |
| TH-BVH-01 | BVH | NO_RESULT | — | crash (aig_result UnboundLocalError) | — |
| TH-BVH-02 | BVH | FAIL | 27/29 | REQ-026 "revenue: not found in JS DATA", REQ-021 | pass |
| TH-MSN-01 | MSN | PASS | 29/29 | — | pass |
| TH-MSN-02 | MSN | FAIL | 16/29 | 13 (same pattern as FPT-01) | pass |
| TH-POW-01 | POW | PASS | 29/29 | — | pass |
| TH-POW-02 | POW | PASS | 29/29 | — | pass (was FAIL in RC1 → RC2 fixed) |
| TH-HPG-01 | HPG | PASS | 29/29 | — | pass |
| TH-HPG-02 | HPG | PASS | 29/29 | — | pass |
| TH-MWG-01 | MWG | PASS | 29/29 | — | pass |
| TH-MWG-02 | MWG | NO_RESULT | — | crash (aig_result UnboundLocalError) | — |

## Positive signal acknowledged

```yaml
period_hotfix:
  executed_runs: 10/10
  period_integrity_pass: 10/10
  detected_inversions: 0
  architecture_status: VALIDATED_TWICE (rc1+rc2)
```

The period resolver + period-integrity architecture works. But not sufficient for parent release.

## RC2 positive deltas vs RC1

- TH-POW-02 PASS (RC1 was FAIL) → artifact admission chart-wrap fix worked
- TH-MWG-02 REQ-027 fixed in RC2 (RC1 was FAIL) → claim-qualifier parser worked
- Admission gate now actively rejects bad artifacts (was permissive in RC1)

## Three defect classes discovered

### Defect ERVN-RUNNER-STATE-001 (CRITICAL)
**Component:** `agent_runner.py`
**Root cause:** Line 469 `phase6_integrity = {"passed": aig_result["passed"]}` lies outside the `if admitted/else not admitted` block. When admission FAILs (RC2 admission gate now rejects more), `aig_result` is never bound. → `UnboundLocalError` → NO_RESULT.
**Runs affected:** TH-BVH-01, TH-MWG-02

### Defect ERVN-DOWNSTREAM-NA-001 (MAJOR)
**Component:** `agent_runner.py` + `independent_verifier.py` REQ-026
**Root cause:** RC2 contract change (`revenue=null+NOT_APPLICABLE`) not propagated to JS DATA in artifact. REQ-026 (Chart DATA JS) searches for revenue array in HTML → not found → FAIL. Owner warned about this in §"Điều kiện đối với thay đổi contract bảo hiểm".
**Runs affected:** TH-BVH-02

### Defect ERVN-ARTIFACT-QUALITY-001/002 (MAJOR, kept open from RC1)
**Component:** `artifact_admission_gate.py` + `bounded_retry`
**Root cause:** Admission gate runs structural checks but does not verify full artifact completeness (13-failure pattern shows agent produced skeleton artifact missing required sections, charts, content depth).
**Runs affected:** TH-FPT-01, TH-MSN-02

## Owner verdict (2026-07-19 §1)

```yaml
rc2:
  verdict: FAIL
  immutable: true
  artifacts_preserved: true

rc3:
  status: AUTHORIZED_WITH_MODIFIED_SCOPE
  required_fixes: 3 (not 2 — FPT-01/MSN-02 NOT dismissed as variance)
```

## Path forward (per owner §2-§7)

```text
RC2 CLOSED with 7/12 FAIL
→ Open 3 defect tickets (RUNNER-STATE-001, DOWNSTREAM-NA-001, ARTIFACT-QUALITY-001/002 kept)
→ Build RC3 with 3 patches (A: runner state safety, B: NOT_APPLICABLE downstream, C: artifact completeness)
→ RC3 regression (4 sections per owner §4)
→ Hash-lock RC3 (rc1/rc2 hashes historical only)
→ Re-run targeted cohort: 12 fresh runs, gate 12/12 required
→ RC3 rollback drill
→ If PASS: open Shadow Step 5
→ If FAIL: close RC3, evaluate RC4 or descope release
```

## Hash state (historical only)

- RC1 aggregate: `4a5071fc087e37c8fcfd1d482037b98a2c59ce226386e7435517cc1e722a53fd`
- RC2 aggregate: `04f3005f1cd90609ef79862a7aea183c9d33871c8c99215271a6895bc966b0bf`
- RC3 aggregate: TBD (will be hash-locked after build)

## Linked artifacts (immutable)

- `cohort-c/targeted-hotfix-v1.0.1-rc2/TH-*/run-result.json` × 10
- `cohort-c/targeted-hotfix-v1.0.1-rc2/TH-BVH-01/.phase6-rejected-raw.txt` × 1
- `cohort-c/targeted-hotfix-v1.0.1-rc2/TH-MWG-02/.phase6-rejected-raw.txt` × 1
- `cohort-c/targeted-hotfix-v1.0.1-rc2/run.log`
- `cohort-c/targeted-hotfix-v1.0.1-rc2/summary.json`
- `incidents/v1.0.1-rc2/ERVN-PERIOD-001-v1.0.1-rc2-hash-lock.json`
- `incidents/v1.0.1-rc2/ERVN-PERIOD-001-rc2-rollback-drill-summary.json`
