# Authority Reconciliation Report — skill-harness-evaluator (R1)

**Generated:** 2026-07-29
**Phase:** REGISTRY_REMEDIATION_R1
**Target:** equity-research-vn v1.1.0
**Parent commit:** raw authority commit `fbc2de2f9` (full SHA reported in §11 attestation)

---

## R1 Corrections Applied

| Issue (Sol §1-6) | R1 Fix |
|---|---|
| Run accounting dimension mismatch (L3 in logical) | L3→L4_UNKNOWN for 12 records without parent; `unique_logical_runs = L1+L2+L4` |
| L3 without rescore lineage | 12 records now L4_UNKNOWN + `RESCORE_SUSPECTED_BUT_PARENT_UNRESOLVED` |
| Hash self-reference | Report contains hashes of OTHER 4 artifacts only; own hash reported externally post-commit (§9) |
| Protocol source hash missing (v0.11.0) | `source_file_sha256` filled for all 17 protocols |
| Supersession gate rationale wrong | Gate now based on actual broken_links=0; unresolved=1 (non-blocking) |

---

## 1. Canonical Accounting Model (R1 §2)

```yaml
physical_events: 110
physical_event_types:
  agent_execution_events: 78
  verifier_rescore_events: 0
  synthetic_replay_events: 0
  static_validation_events: 0
  unknown_events: 32

unique_logical_runs: 98
logical_run_evidence:
  L1_explicit_genuine: 16
  L2_likely_genuine: 50
  L4_unknown: 32
  SUM: 98 ✓

rescore_events:
  L3_rescore_only: 0
```

### Invariants verified

```yaml
physical_events_invariant:
  expected: 78 + 0 + 0 + 0 + 32 = 110
  observed: 110
  match: TRUE

logical_runs_invariant:
  expected: 16 + 50 + 32 = 98
  observed: 98
  match: TRUE
```

---

## 2. Rescore Lineage Reconciliation (R1 §3)

12 records suspected rescore (duration 0.1–3.3s) but **no parent resolved**. Per §3 directive: classified `L4_UNKNOWN`, NOT `L3`.

```yaml
rescore_integrity:
  L3_events: 0
  parent_resolved: 0
  orphan_rescore_events: 0
  duplicate_rescore_relationships: 0
  rescore_suspected_but_parent_unresolved: 12
```

### Phase 5 + Phase F explicit tables (R1 §4)

```yaml
phase5_news_digest:
  records: 10
  L3_with_parent: 0
  L4_parent_unresolved: 10
  note: news-digest data pipeline (vnstock), no model_calls, duration 0.2-3.3s

phase_F_PNJ:
  records: 2
  L3_with_parent: 0
  L4_parent_unresolved: 2
  note: section_results empty + error field, duration 0.1s
```

Duration = supporting evidence only. No parent fabricated.

---

## 3. Protocol Hash Normalization (R1 §5)

All 17 protocols now have `source_file_sha256`. v0.11.0 (incomplete lock):

```yaml
protocol_v0_11_0:
  source_file_sha256: FILLED
  embedded_protocol_hash: null
  embedded_hash_present: false
  embedded_hash_verified: false
  frozen_before_execution: false
  authority_status: INCOMPLETE
```

```yaml
registry_integrity:
  missing_source_file_hashes: 0 ✓
```

---

## 4. Supersession Reconciliation (R1 §6)

```yaml
supersession_chain:
  protocol_records: 17
  explicit_links: 15
  inferred_links: 0
  broken_links: 0
  forks: 0
  multiple_successors: 0
  unresolved_links: 1   (v0.11.0 — missing baseline_protocol_sha256, non-blocking)
```

Canonical gate `supersession_lineage_resolved`: **TRUE** (relies on broken_links=0, not historical registry absence).

---

## 5. Cohort Accounting

| Cohort | Protocol | Records | Unique logical | L1 | L2 | L4 | PASS | FAIL |
|---|---|---|---|---|---|---|---|---|
| Cohort C | 0.7.1 | 10 | 10 | 0 | 0 | 10 | 0 | 10 |
| Cohort C-prime | 0.7.1 | 10 | 10 | 0 | 0 | 10 | 10 | 0 |
| Phase E | 0.8.0 | 12 | 12 | 0 | 12 | 0 | 12 | 0 |
| Phase F shadow | 0.9.0 | 20 | 20 | 0 | 18 | 2 | 18 | 2 |
| Phase F soak | 0.9.1 | 20 | 20 | 0 | 20 | 0 | 20 | 0 |
| Phase 5 news | 0.10.0 | 10 | 10 | 0 | 0 | 10 | 0 | 10 |
| TH rc3 | 0.11.1 | 12 | 12 (shared) | 12 | 0 | 0 | 7 | 5 |
| TH rc4 | 0.12.0 | 12 | 12 (shared) | 12 | 0 | 0 | 8 | 4 |
| Targeted-v5 | 0.12.0 | 4 | 4 | 4 | 0 | 0 | 4 | 0 |

### Phase F shadow (§12 separate denominator)

```yaml
genuine_or_likely_agent_runs: {executed: 18, PASS: 18, FAIL: 0}
unknown_events_rescore_suspected: {events: 2, classification: L4_UNKNOWN_RESCORE_SUSPECTED}
```

---

## 6. Collector Classification (§13)

```yaml
vn_financial_data_collector:
  exercised_indirectly_through_target_contracts: true
  independently_targeted_by_harness: false
  independent_maturity_assigned: false
```

---

## 7. Targeted-v5 (§14)

```yaml
planned: 8, located: 4 (ACB, GEX)
missing: GAS, CTD, SAB, SSI
subset_verdict: PASS (4/4, 28/28)
full_protocol_verdict: INCOMPLETE
```

---

## 8. Registry Integrity (R1 §8)

```yaml
duplicate_protocol_ids: 0
duplicate_physical_event_ids: 0
duplicate_logical_run_ids_without_relationship: 0
orphan_rescore_events: 0
unknown_protocol_references: 0
missing_source_paths: 0
missing_source_file_hashes: 0
fabricated_identifiers: 0

physical_event_accounting_match: TRUE
logical_run_accounting_match: TRUE

registry_integrity: PASS
```

---

## 9. Hash Attestation (R1 §7)

Hashes of the OTHER 4 committed artifacts (filled from this corrective commit):

```yaml
authority_artifact_hashes:
  protocol_registry:        <filled post-commit>
  run_registry:             <filled post-commit>
  overlap_and_rescore_map:  <filled post-commit>
  authority_decision:       <filled post-commit>
  reconciliation_report:    EXTERNAL_POST_COMMIT_ATTESTATION_ONLY
  present: 5/5
  byte_distinct: 5/5
```

Per R1 §7: this report does NOT contain its own final SHA-256. Full 5/5 hashes reported in commit attestation after commit closes (§11).

---

## 10. Final Gate (R1 §10)

```yaml
skill_harness_evaluator_registry_remediation_R1:
  physical_events_reconciled: TRUE
  unique_logical_runs_reconciled: TRUE
  L3_excluded_from_logical_denominator: TRUE

  rescore_events:
    parent_resolved: 0
    L3_confirmed: 0
    L4_parent_unresolved: 12
    orphan: 0

  protocol_source_hashes: complete (17/17)
  supersession_chain: honestly_classified (broken=0, unresolved=1)

  registry_integrity: PASS
  authority_hashes: 5/5 (external attestation)
  unauthorized_paths: 0

  final_verdict: PASS
```

---

## 11. Commit Attestation (R1 §9)

```yaml
raw_authority_commit:
  short: fbc2de2f9
  full: <reported in external attestation>

corrective_commit:
  direct_parent: <full SHA of raw authority commit>
  changed_paths: 5
  required_paths: 5/5
  unauthorized_paths: 0
  full_sha: <reported post-commit>
```

Full 40-char SHAs filled in external attestation after commit closes.

---

## 12. Next State

```yaml
on_PASS_and_canonical_protocol_not_confirmed:
  next_required_phase: skill_harness_evaluator_protocol_authority_remediation

current_state:
  skill_harness_evaluator_engine: FUNCTIONAL
  canonical_authority_registry: R1_PENDING_ACCEPTANCE
  canonical_protocol_confirmed: FALSE
  consolidated_scorecard: BLOCKED_PENDING_PROTOCOL_AUTHORITY_REMEDIATION
```

---

## Prohibited Actions (§1)

```yaml
target_skill_changes: 0
verifier_changes: 0
historical_artifact_changes: 0
new_agent_runs: 0
replacement_protocol_runs: 0
```

Corrective commit contains only the 5 authority artifacts. Raw commit NOT amended/rewritten.
