# RC1 Closure Record — equity-research-vn-1.0.1-rc1
**Date:** 2026-07-19
**Status:** CLOSED — 8/12 PASS, FAIL per owner §8.1 gate
**Immutable:** artifacts + summary preserved unchanged

## Cohort run

```yaml
targeted_hotfix_v1_0_1_rc1:
  runs: 12
  pass: 8
  fail: 4
  result: FAILED
  artifacts_immutable: true
  start: 2026-07-18T17:34
  end:   2026-07-18T19:42
  total_wall_clock_minutes: ~128
```

## Per-run verdict

| Run | Ticker | Status | Pass/Fail | Failed REQs | Wall (s) |
|---|---|---|---|---|---|
| TH-FPT-01 | FPT | PASS | 29/29 | — | 706 |
| TH-FPT-02 | FPT | PASS | 29/29 | — | 514 |
| TH-BVH-01 | BVH | FAIL | 27/29 | REQ-PERIOD-INTEGRITY, REQ-021 | 668 |
| TH-BVH-02 | BVH | FAIL | 27/29 | REQ-PERIOD-INTEGRITY, REQ-021 | 666 |
| TH-MSN-01 | MSN | PASS | 29/29 | — | 527 |
| TH-MSN-02 | MSN | PASS | 29/29 | — | 644 |
| TH-POW-01 | POW | PASS | 29/29 | — | 674 |
| TH-POW-02 | POW | FAIL | 26/29 | REQ-003, REQ-011, REQ-021 | 734 |
| TH-HPG-01 | HPG | PASS | 29/29 | — | 739 |
| TH-HPG-02 | HPG | PASS | 29/29 | — | 553 |
| TH-MWG-01 | MWG | PASS | 29/29 | — | 635 |
| TH-MWG-02 | MWG | FAIL | 27/29 | REQ-027, REQ-021 | 553 |

## Failure root causes (owner-classified)

### Layer 1 — Sector-applicability defect (2 runs: TH-BVH-01/02)
- **Defect ID:** `ERVN-SECTOR-APPLICABILITY-001`
- **Component:** `data_contract + period_integrity_gate`
- **Severity:** MAJOR
- **Issue:** `GENERIC_REVENUE_SEMANTICS_INVALID_FOR_INSURANCE`
- **Description:** Builder resolves no "Sales" column for insurance; emits `revenue: 0` (numeric value with semantics of "valid zero"). Correct contract must emit `revenue: null + status: NOT_APPLICABLE + applicability_rule`. Gate then lacks sector-applicability branch and treats `0` as a value mismatch.
- **NOT period-inversion** — same root cause as the 5 forensic mismatches owner already classified EXPECTED_TRANSFORMATION.

### Layer 2 — Artifact admission gap (2 runs: TH-POW-02, TH-MWG-02)
- **Defect IDs (pending):** `ERVN-ARTIFACT-QUALITY-001`, `ERVN-ARTIFACT-QUALITY-002`
- **Component:** `artifact_admission + bounded_retry`
- **Layer:** `SKILL_MODEL_OR_ARTIFACT_ADMISSION`
- **POW-02 specifics:** REQ-003 (audit split missing, `found: false`), REQ-011 (1 bare canvas `chartThesisRPO` of 12)
- **MWG-02 specifics:** REQ-027 (4 unflagged external claims about "điểm bán")
- **Pending investigation per owner §4:**
  1. Raw model output missing content vs runner dropping it?
  2. Did artifact_admission_gate run?
  3. Why was bare canvas accepted?
  4. Why did pipeline continue despite missing audit split?
  5. Why were external claims not flagged?
  6. Was existing bounded_retry triggered correctly?

## Reporting-bug acknowledgment

The runner summary reported `REQ-PERIOD-INTEGRITY executed: 0/12`. Per-file evidence proves gate ran 12/12. This is a code bug in the summary reporter (lookup `val.get("by_id")` doesn't exist).

```yaml
raw_summary:
  period_integrity_executed: 0/12
  status: REPORTING_BUG

corrected_summary:
  period_integrity_executed: 12/12
  period_integrity_pass: 10/12 (8 non-insurance + 2 insurance-sector-NA via FAIL)
  period_integrity_inversion_defects: 0/12
  artifact_hashes_unchanged: true
  model_runs_reused: true
```

Corrected summary is appended; RC1 raw summary + 12 run-result.json files preserved unchanged.

## Owner verdict (per directive 2026-07-19)

```yaml
step_4_rc1:
  completed: 12/12
  final_pass: 8/12
  verdict: FAIL
  fail_closed_chain: WORKING_AS_DESIGNED

step_5:
  status: BLOCKED
```

## Hash-lock (RC1 baseline, retained for audit)

```yaml
rc1_hash_lock:
  aggregate_sha256: 4a5071fc087e37c8fcfd1d482037b98a2c59ce226386e7435517cc1e722a53fd
  components_locked: 11
  valid_for: rc1_only
  lock_manifest: incidents/v1.0.1-candidate/ERVN-PERIOD-001-v1.0.1-candidate-hash-lock.json
```

## Path forward (per owner directive §6-§11)

```text
RC1 CLOSED with 8/12 FAIL
→ Open defect ERVN-SECTOR-APPLICABILITY-001 + 2 ARTIFACT-QUALITY defects
→ Investigate POW-02/MWG-02 root cause (6 owner questions)
→ Design RC2: null+NOT_APPLICABLE contract semantics, sector-applicability gate,
   artifact_admission preflight, bounded_retry, summary fix
→ Build RC2 (RC1 untouched), hash-lock RC2 separately
→ RC2 regression (11 sub-suites + bad_insurance_output negative fixture)
→ Re-run Step 4 with RC2: 12 fresh runs, no reuse, no selective retry
→ RC2 rollback drill on final LKG
→ If RC2 Step 4 PASS: launch Step 5 shadow requal
```

## Linked artifacts (immutable)

- `cohort-c/targeted-hotfix-v1.0.1/TH-*/run-result.json` × 12
- `cohort-c/targeted-hotfix-v1.0.1/TH-*/.task-state/evidence/REQ-*.json` × all
- `cohort-c/targeted-hotfix-v1.0.1/run.log`
- `cohort-c/targeted-hotfix-v1.0.1/manifest.json`
- `cohort-c/targeted-hotfix-v1.0.1/summary.json` (raw, with reporting bug)
