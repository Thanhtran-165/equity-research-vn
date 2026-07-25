# Defect ERVN-SECTOR-APPLICABILITY-001 — Generic Revenue Semantics Invalid for Insurance

| Field | Value |
|---|---|
| Defect ID | ERVN-SECTOR-APPLICABILITY-001 |
| Severity | MAJOR |
| Status | OPEN |
| Component | `build_data_contract.py` + `period_integrity_gate.py` |
| Discovered | 2026-07-19 (RC1 Step 4 closure) |
| Owner directive | 2026-07-19 §2 |
| Target candidate | equity-research-vn-1.0.1-rc2 |

## 1. Defect

When a sector's income statement has no generic "Sales" / "Revenue" column (insurance, banking), `build_data_contract.py` currently emits:

```yaml
revenue:
  value: 0
  status: VALID   # implicit: 0 is a real numeric value
```

This conflates **two semantically distinct states**:
- "Revenue is genuinely 0 VND" (unlikely for any operating company)
- "Revenue field is not applicable for this sector" (true for insurance/banking)

The number 0 carries economic meaning. Using it to encode "field-not-applicable" loses information and forces the period-integrity gate to report FAIL (because the snapshot found a revenue value via substring matching while the contract reports 0).

## 2. Required encoding

Two acceptable encodings (RC2 must implement one):

### Option A — NULL + NOT_APPLICABLE
```yaml
revenue:
  value: null
  status: NOT_APPLICABLE
  applicability_rule: INSURANCE_REVENUE_NOT_GENERIC_SALES
  provenance:
    source_field: null
    transformation: NONE
```

### Option B — Sector-specific metric (only if insurance_metric_registry exists)
```yaml
insurance_revenue:
  value: <source value>
  status: VALID
  canonical_definition: <registered definition from insurance_metric_registry>
```

Option B requires the metric registry described in owner directive §3. **RC2 uses Option A** (no registry yet — registry deferred to v1.0.2 per owner §3).

## 3. Period-gate conditions for NOT_APPLICABLE

Per owner directive §2, REQ-PERIOD-INTEGRITY may return NOT_APPLICABLE for a metric only when ALL of:

```yaml
sector_applicability_gate:
  registered_sector_rule: true       # applicability_rule field present
  metric_status: NOT_APPLICABLE      # explicit status field
  numeric_value_present: false       # value is null, not 0
  downstream_metric_usage: false     # metric not used in PE/PB/growth formulas
```

If ANY condition fails, the metric must be VERIFIED normally. The gate does NOT exempt entire tickers or sectors — only the specific metric with proper NOT_APPLICABLE encoding.

For BVH (insurance), RC2 must:
- Verify `net_profit`, `eps`, `total_assets`, `total_equity`, `capex`, `operating_cash_flow` normally (these ARE applicable)
- Emit `revenue: NOT_APPLICABLE` with all 4 conditions met

## 4. Regression fixture (per owner §7)

```yaml
bad_insurance_output:
  sector: insurance
  revenue:
    value: 0
    status: NOT_APPLICABLE
  expected: FAIL_INVALID_NOT_APPLICABLE_ENCODING
  reason: "value=0 with status=NOT_APPLICABLE is contradictory; must be value=null"
```

## 5. Implementation scope for RC2

| File | Change |
|---|---|
| `build_data_contract.py` | When `resolve_field(revenue)` returns None for non-banking sector, emit `{value: null, status: NOT_APPLICABLE, applicability_rule: INSURANCE_REVENUE_NOT_GENERIC_SALES}` instead of `value: 0` |
| `period_integrity_gate.py` | Add `sector_applicability_gate` branch: if contract has `{value: null, status: NOT_APPLICABLE, applicability_rule: <registered>}`, skip per-field period verification for that metric only; verify all other metrics normally |
| `requirements_v1.0.1.yaml` | Update REQ-PERIOD-INTEGRITY text to acknowledge NOT_APPLICABLE semantics |
| Regression suite | Add `bad_insurance_output` negative fixture (Option B in §3) |

## 6. NOT scope

- Adding insurance-specific revenue aliases (deferred to v1.0.2)
- Adding banking-specific revenue aliases (deferred to v1.0.2)
- Building insurance_metric_registry (deferred to v1.0.2)

## 7. Linked evidence

- RC1 closure: `incidents/v1.0.1-rc1/RC1-CLOSURE-8OF12-FAIL.md`
- TH-BVH-01 evidence: `cohort-c/targeted-hotfix-v1.0.1/TH-BVH-01/.task-state/evidence/REQ-PERIOD-INTEGRITY.json`
- TH-BVH-02 evidence: `cohort-c/targeted-hotfix-v1.0.1/TH-BVH-02/.task-state/evidence/REQ-PERIOD-INTEGRITY.json`
- Forensic classification (5 mismatches): `incidents/ERVN-PERIOD-001-forensic-v1.0.1-remaining-mismatches.yaml`
