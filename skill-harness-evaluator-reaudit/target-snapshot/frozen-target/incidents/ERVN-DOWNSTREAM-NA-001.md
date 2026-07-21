# Defect ERVN-DOWNSTREAM-NA-001 — NOT_APPLICABLE Downstream Semantics

| Field | Value |
|---|---|
| Defect ID | ERVN-DOWNSTREAM-NA-001 |
| Severity | MAJOR |
| Status | OPEN — RC3 |
| Component | `agent_runner.py` (DATA enforcer) + `independent_verifier.py` REQ-026 |
| Root cause layer | RUNNER_HARNESS_AND_VERIFIER |
| Discovered | 2026-07-19 (RC2 TH-BVH-02 REQ-026 fail) |
| Owner directive | 2026-07-19 §2 Patch B |
| Target candidate | equity-research-vn-1.0.1-rc3 |

## 1. Defect

RC2 contract change (`revenue=null + status=NOT_APPLICABLE + applicability_rule`) was applied at the `verified-dashboard-data.json` level but **not propagated downstream** to the JS DATA block in the rendered HTML artifact. When REQ-026 (Chart DATA JS) verifies the artifact's DATA object, it searches for `revenue` array → not found → FAIL.

Evidence from TH-BVH-02:
```json
{
  "checked_arrays": ["revenue", "netProfit", "eps"],
  "mismatches": ["revenue: not found in JS DATA"]
}
```

Owner warned about this exact scenario in RC2 review §"Điều kiện đối với thay đổi contract bảo hiểm": *"chart không vẽ điểm 0 giả"*.

## 2. Required fix (per owner §2 Patch B)

NOT just "skip REQ-026 when revenue missing". Must propagate the full NOT_APPLICABLE semantics into the artifact.

### Artifact must encode:
```yaml
revenue:
  value: null
  status: NOT_APPLICABLE
  applicability_rule: INSURANCE_REVENUE_NOT_GENERIC_SALES
```

### JS DATA or equivalent metadata must hold:
```javascript
revenue: null,
revenueStatus: "NOT_APPLICABLE",
revenueApplicabilityRule: "INSURANCE_REVENUE_NOT_GENERIC_SALES"
```

## 3. REQ-026 carve-out (5 conditions all required)

REQ-026 returns NOT_APPLICABLE only when ALL of:
```yaml
contract_value_is_null: true
contract_status: NOT_APPLICABLE
registered_applicability_rule_present: true
artifact_encodes_same_status: true
revenue_dependent_chart_absent: true
revenue_dependent_calculations_absent_or_NA: true
```

If revenue is missing from DATA without status:
```
FAIL_REQUIRED_FIELD_OR_STATUS_MISSING
```

This ensures carve-out cannot hide genuine data omission.

## 4. Implementation scope (RC3)

| File | Change |
|---|---|
| `data_contract_enforcer.py` | When contract has `field_applicability.revenue.status=NOT_APPLICABLE`, inject `revenue: null, revenueStatus: "NOT_APPLICABLE", revenueApplicabilityRule: <rule>` into DATA block (instead of skipping revenue entirely) |
| `independent_verifier.py` REQ-026 | Add 5-condition carve-out for NOT_APPLICABLE encoding |
| Agent phase6 prompt (skill content) | Out of scope — agent must learn from injected DATA shape |

## 5. Regression requirements (owner §4)

```yaml
na_tests:
  null_plus_registered_rule: NOT_APPLICABLE
  zero_plus_not_applicable: FAIL
  missing_field_without_status: FAIL
  revenue_chart_absent_when_NA: PASS
  revenue_chart_with_zero_when_NA: FAIL
  inverted_non_NA_BVH_metric: FAIL
```

## 6. NOT scope

- Agent narrative adaptation to NOT_APPLICABLE (e.g., not saying "doanh thu = 0")
- Insurance-specific revenue aliases (deferred to v1.0.2)

## 7. Linked evidence

- `cohort-c/targeted-hotfix-v1.0.1-rc2/TH-BVH-02/.task-state/evidence/REQ-026.json`
- `incidents/ERVN-SECTOR-APPLICABILITY-001.md` (parent defect — this is the downstream fix)
