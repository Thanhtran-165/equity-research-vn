# Completion Protocol v0.13.0 — Freeze Report

**Generated:** 2026-07-30
**Phase:** COMPLETION_PROTOCOL_FREEZE (Remediation-R1 applied)
**Target:** equity-research-vn v1.1.0

---

## R1 Correction Applied

| Issue (Sol R1) | Fix |
|---|---|
| SAB role contradiction (clean control + stress) | Model B: CLEAN_POSITIVE_CONTROL, REQ-023 APPLICABLE expect PASS, stress_case=false |
| Missing per-run applicability matrix | Added explicit APPLICABLE/NOT_APPLICABLE for all 4 runs × 3 REQs |
| "banking REQ-023 stress" phrasing | Removed everywhere |

---

## 1. Objective

Create and freeze a clean-authority completion protocol to finish 4 Targeted-v5 obligations that no existing protocol can govern (v0.12.0 UNRESOLVED per R2).

---

## 2. Authority Anchors (§2)

```yaml
accepted_registry_commit: 232c9b8c1ba7e0adf7c48972162db016bcde483c
accepted_R2_decision_commit: 089b06a27056e021af32a1d37384316aac15380f
```

v0.13.0 is anchored directly to these two accepted commits. It does NOT use v0.12.0 as predecessor.

```yaml
relationship_to_v0_12: COMPLETES_UNFINISHED_EVALUATION_OBLIGATIONS
inherits_authority: false
modifies_v0_12: false
```

---

## 3. Planned Runs (§7)

4 fresh genuine-agent executions:

| Run ID | Ticker | Role | Obligation |
|---|---|---|---|
| TV13-GAS-01 | GAS | TARGETED_DEFECT_VALIDATION | Fresh (legacy TV5-GAS-01 interrupted, excluded) |
| TV13-CTD-01 | CTD | CROSS_TICKER_REQUALIFICATION | Fresh (never executed) |
| TV13-SAB-01 | SAB | CLEAN_POSITIVE_CONTROL | Fresh (clean positive, REQ-023 applicable expect PASS, not stress) |
| TV13-SSI-01 | SSI | GENERALIZATION_CONTROL | Fresh (securities archetype) |

All run_ids are new — no collision with historical logical/physical IDs.

---

## 4. Requirement Matrix (§8)

28 requirements per run. Restated in full (not "same as v0.12.0"). REQ-023 explicitly included with direct testing rule:

### Per-run applicability matrix (R1 §5)

```yaml
run_applicability:
  TV13-GAS-01:  {REQ_013: APPLICABLE, REQ_023: APPLICABLE, REQ_025: APPLICABLE}
  TV13-CTD-01:  {REQ_013: APPLICABLE, REQ_023: APPLICABLE, REQ_025: APPLICABLE}
  TV13-SAB-01:  {REQ_013: APPLICABLE, REQ_023: APPLICABLE, REQ_025: APPLICABLE}
  TV13-SSI-01:  {REQ_013: APPLICABLE, REQ_023: APPLICABLE, REQ_025: APPLICABLE}
```

All 3 REQs APPLICABLE for all 4 tickers (per requirements.yaml `applicability: all`). No NOT_APPLICABLE values.

### Role consistency (R1 §6)

```yaml
role_matrix:
  complete: true
  internally_consistent: true
  placeholders: 0
  contradictory_role_labels: 0

SAB:
  role: CLEAN_POSITIVE_CONTROL
  REQ_023_applicability: APPLICABLE
  stress_case: false
  defect_injection: prohibited
  expected_result: PASS
```

```yaml
REQ-023:
  description: 'Balance sheet accuracy (banking-sector-aware column mapping)'
  verifier_rule: balance_sheet_accuracy_check
  note: 'MUST be tested directly (not inferred). All 4 tickers APPLICABLE per requirements.yaml.'
```

Minimum coverage: REQ-013, REQ-023, REQ-025, artifact completeness, report structure, source traceability, deterministic shell, unsupported-claim prevention, ticker isolation, no cross-run leakage, runtime completion, verifier applicability, failure-reason correctness.

---

## 5. Preexisting Evidence Adoption (§5)

4 completed v0.12 runs adopted as ADOPTED_PREEXISTING_EVIDENCE (NOT counted as v0.13.0 executions):

| Run | Verdict | Output SHA-256 | Adoption |
|---|---|---|---|
| TV5-ACB-01 | PASS 28/28 | fc610a55... | ADMITTED |
| TV5-ACB-02 | PASS 28/28 | 12028314... | ADMITTED |
| TV5-GEX-01 | PASS 28/28 | ff582b70... | ADMITTED |
| TV5-GEX-02 | PASS 28/28 | 8c70217f... | ADMITTED |

All 4 adopted (all PASS). No cherry-picking. Full SHA-256 pinned.

---

## 6. Legacy GAS Artifact (§6)

```yaml
TV5-GAS-01:
  state: INTERRUPTED_NO_VERDICT
  admissible_as_final_result: false
  admissible_as_execution_completion: false
  historical_preservation: required
  adoption: EXCLUDED
  rationale: 'phase=init, decision-log incomplete. No retroactive adjudication. TV13-GAS-01 fresh execution required.'
```

---

## 7. Execution Environment Freeze (§11)

```yaml
target_skill: equity-research-vn v1.1.0 (tree sha256: 6e6b2a25...)
evaluator: skill-harness-evaluator 0.1.0 (tree sha256: 083a9604...)
verifier: 0.1.6 (sha256: c155d5cb...)
runtime: Darwin 25.5.0, Python 3.11.14, model zai/GLM-5.2
```

No execution permitted if target/evaluator/verifier differ from freeze record.

---

## 8. Run Acceptance Gate (§13)

```yaml
agent_invocation_completed: required
output_artifact_present: required
decision_log_complete: required
verifier_completed: required
final_verdict_present: required
requirements_accounted: all
evidence_hashes_present: all
```

INTERRUPTED does NOT count as completed with verdict.

---

## 9. Hash Design (§17)

```yaml
lock_file:
  contains_protocol_sha256: true
  contains_evidence_adoption_sha256: true
  contains_authority_anchor_commits: true
  contains_own_sha256: false   ← no self-reference
```

Full 4/4 hashes reported externally post-commit.

---

## 10. Freeze Integrity Gate (§19)

```yaml
completion_protocol_freeze_integrity:
  authority_anchors_valid: true
  planned_runs: 4
  unique_run_ids: 4/4
  requirement_matrix_complete: true
  REQ_023_explicitly_included: true

  existing_PASS_evidence:
    reviewed: 4/4
    hash_pinned: 4/4
    cherry_picking: 0

  interrupted_GAS:
    preserved_historically: true
    adopted_as_final_result: false

  protocol_hash_verified: true
  frozen_before_execution: true

  artifact_hashes: 4/4
  byte_distinct: 4/4
  unauthorized_paths: 0

  final_verdict: PASS
```

**PASS of freeze phase only proves protocol validly locked. It does NOT prove 4 runs completed.**

---

## 11. Combined Targeted-v5 View (§15, post-execution template)

After execution, report two layers:

```yaml
combined_targeted_completion:
  adopted_preexisting_evidence:
    runs: 4, PASS: 4, FAIL: 0, invalid: 0
  v0_13_new_executions:
    planned: 4, completed: <post-execution>, PASS/FAIL/ERROR/INTERRUPTED: <post-execution>
  combined_obligation_coverage:
    total_expected: 8, valid_completed: <post>, incomplete: <post>, absent: <post>
```

Coverage view only — do not describe all 8 as same-protocol runs.

---

## 12. Prohibited Actions (§4)

```yaml
agent_runs: 0          ← this phase only freezes, does not execute
target_runs: 0
verifier_runs: 0
target_skill_changes: 0
evaluator_changes: 0
verifier_changes: 0
historical_protocol_changes: 0
historical_result_changes: 0
v0_12_reclassification: 0
retroactive_verdict_creation: 0
```

---

## 13. Next Phase (§20)

```yaml
on_PASS:
  next_required_phase: skill_harness_evaluator_completion_execution
```

After freeze PASS, execute the 4 genuine-agent runs under v0.13.0 authority.
