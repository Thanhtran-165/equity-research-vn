# Defect ERVN-ARTIFACT-QUALITY-001 — Missing Audit Split + Bare Canvas (POW-02)

| Field | Value |
|---|---|
| Defect ID | ERVN-ARTIFACT-QUALITY-001 |
| Severity | MAJOR |
| Status | OPEN — RC3 (kept open per owner 2026-07-19 §2 Patch C) |
| Component | `agent_runner.py` + `artifact_admission_gate.py` + `bounded_retry` |
| Layer | `SKILL_MODEL_AND_RUNNER_HARNESS` |
| Discovered | 2026-07-19 (RC1 TH-POW-02; RC2 TH-FPT-01, TH-MSN-02 same pattern) |
| Owner directive | 2026-07-19 §2 Patch C + §3 (NO carve-out for agent variance) |
| Target candidate | equity-research-vn-1.0.1-rc3 |

## 1. Failure symptoms (TH-POW-02)

```yaml
ticker: POW
run_id: TH-POW-02
verdict: FAIL
failed_REQs:
  - REQ-003:  # Audit split (Bẫy 5B) trước khi tính EPS/PE/PB
      evidence: {"found": false}
  - REQ-011:  # Canvas elements phải có height-wrapper
      evidence: {"bare_canvas_count": 1, "bare_canvas_ids": ["chartThesisRPO"], "total_canvas": 12}
  - REQ-021:  # All requirements pass (blocker; auto-fail when others fail)
```

## 2. Owner-instructed investigation order (§4)

1. **Raw model output missing content vs runner dropping it?**
   - Inspect `.phase6-attempt-1.txt` and intermediate phase artifacts in `TH-POW-02/`
   - Determine if the model never produced audit split / proper canvas OR if a runner step stripped it
2. **Did artifact_admission_gate run?**
   - Check phase events in run-result.json for admission gate invocation
3. **Why was bare canvas accepted?**
   - Artifact admission should reject bare canvas before final verifier sees it
4. **Why did pipeline continue despite missing audit split?**
   - REQ-003 fail should have triggered bounded_retry or admission rejection
5. **(N/A for POW-02)** External claims flagging — applies to MWG-02
6. **Was bounded_retry triggered correctly?**
   - Check `agent_content_recovery_count` and any retry phase events

## 3. Required admission preflight (per owner §5)

Add deterministic admission checks BEFORE final verification:

```yaml
artifact_admission:
  required_audit_split_present: true
  bare_canvas_count: 0
  unflagged_external_claims: 0
```

If admission FAIL → bounded regeneration per §5:

```yaml
bounded_retry:
  maximum_attempts: 1
  trigger:
    - REQUIRED_SECTION_MISSING
    - BARE_CANVAS_DETECTED
    - UNFLAGGED_EXTERNAL_CLAIM
  full_artifact_replacement: prohibited_unless_integrity_preserved
  raw_attempts_preserved: true
```

Retry must NOT:
- Modify deterministic financial data
- Change source / ticker
- Delete valid artifact sections
- Loop until PASS

## 4. Investigation log

```
[X] Q1: Raw model output inspection
    Finding: Model did NOT produce audit split section (0 occurrences of "audit split"
    / "bẫy 5B" in .phase6-attempt-1.txt). POW-01 (passed) had 9 occurrences.
    Finding: Model produced bare canvas HTML: <canvas id="chartThesisRPO" style="...">
    without .chart-wrap wrapper. POW-01 used proper <div class="chart-wrap"> wrapper.
    Verdict: MODEL_VARIANCE — runner did not drop content; model produced different
    template on run-2.

[X] Q2: artifact_admission_gate invocation trace
    Finding: agent_content_recovery_count=1 in run-result.json → gate DID run.
    But existing admission gate checks structure (sections, divs, etc.), not the
    specific audit-split section presence. So it admitted an artifact that was
    structurally complete but content-incomplete.

[X] Q3: Bare canvas acceptance path
    Finding: Existing artifact_admission_gate does not check for .chart-wrap.
    REQ-011 (canvas_check) catches this only at final verifier step — too late.

[X] Q4: REQ-003-fail-but-pipeline-continued path
    Finding: REQ-003 is not in the bounded_retry trigger list. Only REQ-005/REQ-007
    currently trigger phase6 retry. REQ-003 fail proceeds to final verifier, which
    then fails REQ-021.

[X] Q5: bounded_retry trigger evaluation
    Finding: bounded_retry was triggered ONCE (agent_content_recovery_count=1) for
    some other REQ during the run, but the retry did not produce audit split or
    fix the bare canvas. Retry content not preserved for inspection.
```

## 4a. Confirmed root causes

| Question | Root cause |
|---|---|
| Q1 (model vs runner) | MODEL — agent produced different output on run-2 |
| Q2 (admission gate) | GATE GAP — admission gate checks structure not audit-split presence |
| Q3 (bare canvas) | GATE GAP — admission gate doesn't check `.chart-wrap` |
| Q4 (pipeline continue) | PIPELINE GAP — REQ-003 not in bounded_retry trigger list |
| Q5 (retry triggered) | YES, once — but for different REQ; did not fix REQ-003/REQ-011 issues |

## 4b. Required RC2 changes

1. Extend `artifact_admission_gate.py` to require audit-split section presence
2. Extend `artifact_admission_gate.py` to check `.chart-wrap` on every canvas
3. Add REQ-003 (`REQUIRED_SECTION_MISSING`) and REQ-011 (`BARE_CANVAS_DETECTED`) to bounded_retry trigger list
4. Preserve raw retry attempts as evidence (raw_attempts_preserved: true)

## 5. Linked evidence

- `cohort-c/targeted-hotfix-v1.0.1/TH-POW-02/run-result.json`
- `cohort-c/targeted-hotfix-v1.0.1/TH-POW-02/.task-state/evidence/REQ-003.json`
- `cohort-c/targeted-hotfix-v1.0.1/TH-POW-02/.task-state/evidence/REQ-011.json`
- `cohort-c/targeted-hotfix-v1.0.1/TH-POW-02/.phase6-attempt-*.txt` (intermediate model output)
