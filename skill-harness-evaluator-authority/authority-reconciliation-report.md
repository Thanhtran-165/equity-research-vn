# Authority Reconciliation Report — skill-harness-evaluator

**Generated:** 2026-07-29
**Phase:** CANONICAL_AUTHORITY_REGISTRY_PHASE (owner directive §1)
**Target:** equity-research-vn v1.1.0
**Scope:** Hợp nhất evidence đã tồn tại. KHÔNG chạy thêm agent, KHÔNG sửa target, KHÔNG thay đổi kết quả lịch sử.

---

## 1. Protocol Registry Summary

| Metric | Value |
|---|---|
| Total protocols located | **17** (v0.1.0 → v0.12.0) |
| Hash verified | **16/17** ✓ |
| Incomplete lock | **1** (v0.11.0 — no hash, no frozen flag) |
| SUPERSEDED | 15 |
| CANDIDATE_CANONICAL | 1 (v0.12.0) |
| CANONICAL confirmed | **0** |

### Canonical protocol gate (§5) — v0.12.0 check

```yaml
lock_file_present: TRUE
full_sha256_verified: TRUE
frozen_before_execution: TRUE
supersession_lineage_resolved: FALSE   ← no prior registry existed
required_execution_manifest_present: TRUE
planned_vs_observed_runs_reconciled: FALSE   ← targeted-v5 4/8
canonical_scorecard_or_decision_present: FALSE   ← blocked
```

**Result: NOT_CONFIRMED.** v0.12.0 is latest located but NOT canonical. Per §15, honest NOT_CONFIRMED is acceptable.

---

## 2. Run Reconciliation

```yaml
raw_artifact_mentions: 110
physical_events: 110
unique_logical_runs: 98

L1_unique_runs (explicit genuine):  16
L2_unique_runs (likely genuine):    50
L3_events (rescore only):           12
L4_unresolved:                      20

duplicate_physical_events_removed:  12   (all rc3/rc4 pairs)
rescore_events:                     12
unidentified_records:                0
unresolved_cross_scheme_overlap:     POSSIBLE (24 unenumerable records)
```

### rc3/rc4 deduplication (§7)

12 logical runs (TH-BVH-01...TH-POW-02) each appear in both `targeted-hotfix-v1.0.1-rc3` and `targeted-hotfix-v1.0.1-rc4`. These are **same 12 agent outputs evaluated by 2 verifier versions**. Deduplicated to 12 unique logical runs (not 24).

```yaml
rc3_rc4_case:
  logical_runs: 12
  physical_verifier_events: 24
  agent_executions: 12
  rescoring_events: 12
```

---

## 3. Exact Genuine Total — UNRESOLVED

```yaml
status: UNRESOLVED
confirmed_L1_minimum: 16
confirmed_L1_plus_L2_upper_observation: 66   ← NOT "confirmed genuine total"
reason: 24 records (Cohort C + C-prime) lack deduplicable run_id; cross-scheme overlap possible
```

**12 labeled genuine + 50 likely genuine** does NOT mean 62 confirmed genuine executions.

---

## 4. Cohort Accounting (§11)

| Cohort | Protocol | Records | Unique logical | L1 | L2 | L3 | L4 | PASS | FAIL |
|---|---|---|---|---|---|---|---|---|---|
| Cohort C | 0.7.1 | 10 | 10 (unenum) | 0 | 0 | 0 | 10 | 0 | 10 |
| Cohort C-prime | 0.7.1 | 10 | 10 (unenum) | 0 | 0 | 0 | 10 | 10 | 0 |
| Phase E | 0.8.0 | 12 | 12 | 0 | 12 | 0 | 0 | 12 | 0 |
| Phase F shadow | 0.9.0 | 20 | 20 | 0 | 18 | 2 | 0 | 18 | 2 |
| Phase F soak | 0.9.1 | 20 | 20 | 0 | 20 | 0 | 0 | 20 | 0 |
| Phase 5 news | 0.10.0 | 10 | 10 | 0 | 0 | 10 | 0 | 0 | 10 |
| TH rc3 | 0.11.1 | 12 | 12 (shared) | 12 | 0 | 0 | 0 | 7 | 5 |
| TH rc4 | 0.12.0 | 12 | 12 (shared) | 12 | 0 | 0 | 0 | 8 | 4 |
| Targeted-v5 | 0.12.0 | 4 | 4 | 4 | 0 | 0 | 0 | 4 | 0 |

### Phase F special accounting (§12)

```yaml
phase_F_shadow:
  genuine_or_likely_agent_runs: {executed: 18, PASS: 18, FAIL: 0}
  verifier_or_rescore_events:   {events: 2, PASS: 0, FAIL: 2}   ← 2 PNJ rescore
  note: 'Do NOT combine into one genuine pass rate'

phase_F_soak:
  genuine_or_likely_agent_runs: {executed: 20, PASS: 20, FAIL: 0}
  verifier_or_rescore_events:   {events: 0}
```

---

## 5. Collector Classification (§13)

```yaml
vn_financial_data_collector:
  exercised_indirectly_through_target_contracts: true
  contracts_exercised: [fundamental-input-contract, provenance-contract, metric-ownership]
  independently_targeted_by_harness: false
  independent_maturity_assigned: false
  note: 'Implicit coverage must not become independent PASS verdict'
```

---

## 6. Targeted-v5 Reconciliation (§14)

```yaml
planned_runs: 8
located_runs: 4
located_tickers: [ACB, GEX]
missing_or_unlocated_tickers: [GAS, CTD, SAB, SSI]
subset_verdict: PASS (4/4, 28/28 requirements)
full_protocol_completion: UNCONFIRMED
full_protocol_verdict: INCOMPLETE
```

---

## 7. Registry Integrity (§16)

```yaml
duplicate_protocol_ids: 0
duplicate_physical_event_ids: 0
duplicate_logical_run_ids_without_relationship: 0   (12 rc3/rc4 have explicit relationship)
orphan_rescore_events: 12   (rescore parents not located — L3 records)
unknown_protocol_references: 0
missing_source_paths: 0
missing_hashes: 1   (v0.11.0 INCOMPLETE lock)
fabricated_identifiers: 0
```

Every registry record traces to at least one source artifact.

---

## 8. Decision Gate (§18)

```yaml
protocol_records: 17
run_records: 110 physical / 98 unique logical
source_paths_verified: TRUE
registry_integrity: PASS (1 known gap: v0.11.0 incomplete, documented)

protocol_authority:
  canonical_confirmed: FALSE

run_inventory:
  raw_mentions: 110
  physical_events: 110
  unique_logical_runs: 98
  L1: 16
  L2: 50
  L3: 12
  L4: 20

targeted_v5:
  located: 4/8
  subset: PASS
  full_protocol: INCOMPLETE

historical_results_preserved: true
backward_pooling: 0
target_skill_modified: 0

final_verdict: PASS
```

**PASS** means registries accurately represent available evidence. It does NOT require canonical protocol to exist.

---

## 9. Hash Manifest (§17)

SHA-256 of all 5 authority artifacts:

```yaml
authority_artifact_hashes:
  protocol_registry:           08c3786323b28653a71e496e262aa78565b0d020db53fbc1f79553693f9bf56d
  run_registry:                407843f8babce8214764486869c9799d858ef8ccc1f354ec097f05cd8f1b93ac
  overlap_and_rescore_map:     63d47f6cc7665f987639a0e19c6f396ff08bd3b4101acffd345df29f4992bbd9
  authority_decision:          379eeff3f7c1e50e29e779140dc717cd81a46d22565948d0ab1424236a66fca3
  reconciliation_report:       93e672cb0daba498d72523367863935e7f22fc4afb63b26be7e934239d0b0204   ← this file
  present: 5/5
  byte_distinct: 5/5
```

Note: per §17, commit's own hash is NOT placed inside artifacts.

---

## 10. Next State (§19)

```yaml
current_state:
  skill_harness_evaluator_engine: FUNCTIONAL
  canonical_authority_registry: COMPLETED_THIS_PHASE
  canonical_protocol_confirmed: FALSE
  consolidated_scorecard: BLOCKED_PENDING_PROTOCOL_AUTHORITY_REMEDIATION
  evaluator_certified_production_readiness: UNCONFIRMED

on_PASS_and_canonical_protocol_NOT_confirmed:
  next_required_phase: skill_harness_evaluator_protocol_authority_remediation
```

---

## 11. Prohibited Actions Compliance (§3)

```yaml
target_skill_changes: 0
verifier_changes: 0
historical_artifact_changes: 0
protocol_lock_changes: 0
result_reinterpretation_without_evidence: 0
backward_pooling: 0
synthetic_missing_runs: 0
invented_run_ids: 0
```

All 8 prohibited actions = 0. Phase compliant.
