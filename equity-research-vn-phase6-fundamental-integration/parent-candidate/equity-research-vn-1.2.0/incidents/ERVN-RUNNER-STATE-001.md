# Defect ERVN-RUNNER-STATE-001 — Runner Harness State Safety

| Field | Value |
|---|---|
| Defect ID | ERVN-RUNNER-STATE-001 |
| Severity | CRITICAL |
| Status | OPEN — RC3 |
| Component | `agent_runner.py` |
| Root cause layer | RUNNER_HARNESS |
| Discovered | 2026-07-19 (RC2 TH-BVH-01, TH-MWG-02 NO_RESULT) |
| Owner directive | 2026-07-19 §2 Patch A |
| Target candidate | equity-research-vn-1.0.1-rc3 |

## 1. Defect

In `agent_runner.py` line 469 (RC2):
```python
if not adm_result["admitted"]:
    # FAIL CLOSED
    ...
    model_result["output"] = ""
else:
    # ARTIFACT INTEGRITY GATE
    import artifact_integrity_gate as AIG
    aig_result = AIG.check_artifact_integrity(model_result["output"])
phase6_integrity = {"passed": aig_result["passed"]}  # ← LINE 469 OUTSIDE IF/ELSE
```

Line 469 is **outside** the `if admitted / else not admitted` block. When admission FAILs (aig_result never bound), line 469 raises `UnboundLocalError: cannot access local variable 'aig_result'`.

This is a pre-existing structural bug, but RC2's stronger admission gate (audit-split + chart-wrap checks) rejects more artifacts → bug surfaces more often.

## 2. Required fix (per owner §2 Patch A)

Not just "move one line". Must ensure every execution branch initializes or doesn't access these variables:
- `aig_result`
- artifact path
- verification result
- retry result
- final verdict

Pattern:
```text
artifact không admitted
→ không tham chiếu kết quả verifier chưa tồn tại
→ ghi structured failure
→ thực hiện bounded retry nếu đủ điều kiện
→ nếu retry thất bại, trả FAIL có cấu trúc
```

## 3. Expected outcome

```yaml
admission_failure:
  execution_type: ADMISSION_REJECTED
  final_status: FAIL
  no_result: false
  traceback: none
```

`NO_RESULT` due to code error is **forbidden** after RC3.

## 4. Regression requirements (owner §4)

```yaml
runner_tests:
  admitted_artifact: PASS
  rejected_artifact: STRUCTURED_FAIL
  retry_success: PASS
  retry_failure: STRUCTURED_FAIL
  aig_result_unbound: impossible
  no_result_due_to_runner_exception: 0
```

## 5. Linked evidence

- `cohort-c/targeted-hotfix-v1.0.1-rc2/TH-BVH-01/.phase6-rejected-raw.txt` (artifact that triggered)
- `cohort-c/targeted-hotfix-v1.0.1-rc2/TH-MWG-02/.phase6-rejected-raw.txt`
- stderr in summary.json for both runs
