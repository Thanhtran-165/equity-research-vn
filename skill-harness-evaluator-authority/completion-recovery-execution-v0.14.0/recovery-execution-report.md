# Recovery Execution Report — v0.14.0

**Generated:** 2026-07-30
**Phase:** COMPLETION_RECOVERY_EXECUTION v0.14.0
**Protocol:** 0.14.0 (frozen, accepted)
**Parent commit:** `3721ee52c25589ca28ba3e12feddc7dde4089e6d`

---

## 1. Execution Summary

```yaml
planned_runs: 1
launcher_attempts: 1
genuine_agent_executions: 1
completed_with_verdict: 1
PASS: 1, FAIL: 0, ERROR: 0, INTERRUPTED: 0
requirements_expected: 28
requirements_accounted: 28
```

---

## 2. TV14-CTD-01 Result

```yaml
run_id: TV14-CTD-01
ticker: CTD
role: CROSS_TICKER_REQUALIFICATION
execution_type: genuine_agent
final_verdict: PASS
phases_completed: 9/9
duration_seconds: 594
exit_code: 0
terminating_signal: NONE

launcher_attempt_id: TV14-CTD-01-LAUNCH-01
logical_run_id: TV14-CTD-01
physical_event_id: PEV-TV14-CTD-01-001

output_sha256: 416ca68afdc1b503afbb5ed427ded62b64fb35f5150ed106375e2c2e77209b66
run_result_sha256: 04cf8804ef1843bc13d660917f0d19c4e465bd12aeb966eba018099f17d78d20
```

---

## 3. Launcher Safety Compliance (§5)

```yaml
shell_pipeline_used: false
pipe_to_head: false
pipe_to_tail: false
stdout_redirected: true (to agent-invocation.log)
stderr_redirected: true (to agent-invocation.err)
unique_attempt_directory: true
existing_directory_reused: false
rm_rf_performed: false
process_exit_code: 0
terminating_signal: NONE
stderr_content: empty (0 lines)
```

---

## 4. Pre-execution Gate (§3)

```yaml
target_skill_hash: MATCH
evaluator_hash: MATCH
verifier_hash: MATCH
protocol_hash: MATCH
evidence_adoption_hash: MATCH
model_backend: zai/GLM-5.2 configured
launcher_paths_match: true
placeholders: 0
verdict: PASS
```

---

## 5. Authoritative Completion (§10)

```yaml
adopted_v0_12: 4/4 valid
adopted_unaffected_v0_13: 3/3 valid
fresh_v0_14: 1/1 completed PASS
excluded_v0_13_CTD: preserved, non-authoritative

total_expected_obligations: 8
authoritative_completed: 8
incomplete: 0
absent: 0

authoritative_run_set:
  - TV5-ACB-01 (adopted v0.12)
  - TV5-ACB-02 (adopted v0.12)
  - TV5-GEX-01 (adopted v0.12)
  - TV5-GEX-02 (adopted v0.12)
  - TV13-GAS-01 (adopted v0.13)
  - TV14-CTD-01 (fresh v0.14) ← COMPLETED PASS
  - TV13-SAB-01 (adopted v0.13)
  - TV13-SSI-01 (adopted v0.13)
```

TV13-CTD-01 NOT in authoritative set.

---

## 6. Critical Requirements Closure

```yaml
REQ-013: PASS 8/8 (4 v0.12 + 3 v0.13 + TV14-CTD-01)
REQ-023: PASS 8/8 (directly tested, incl TV14-CTD-01 fresh execution)
REQ-025: PASS 8/8 (4 v0.12 + 3 v0.13 + TV14-CTD-01)
```

---

## 7. Completion Gate (§8)

```yaml
TV14_CTD_completion_gate:
  launcher_attempts: 1/1
  genuine_agent_executions: 1/1
  explicit_execution_type: genuine_agent
  invocation_completed: true
  output_present: true
  output_sha256_present: true
  verifier_completed: true
  verifier_sha256_present: true
  final_verdict_present: true (PASS)
  requirements_total: 28
  requirements_accounted: 28/28
  REQ_013_direct_result: present
  REQ_023_direct_result: present
  REQ_025_direct_result: present
  missing_evidence: 0
```

---

## 8. Final Gate (§14)

```yaml
skill_harness_evaluator_completion_recovery_execution_v0_14:
  authority:
    protocol_frozen: true
    freeze_accepted: true
  pre_execution_gate: PASS
  planned_runs: 1
  launcher_attempts: {authorized: 1, observed: 1}
  genuine_agent_executions: {authorized: 1, observed: 1}
  TV14_CTD:
    completed_with_verdict: 1
    requirements_accounted: 28/28
    missing_evidence: 0
  authoritative_completion: {expected: 8, completed: 8}
  artifact_hashes: 5/5
  unauthorized_paths: 0
  final_verdict: PASS
```

---

## 9. Decision (§11)

```yaml
final_recovery_protocol_verdict: PASS
consolidated_scorecard_authorized: true
rationale: >
  TV14-CTD-01 completed PASS (1/1 launcher, 1/1 genuine agent, 28/28 reqs).
  Authoritative completion 8/8. Evidence complete.
```

---

## Prohibited Actions (§3)

```yaml
new_agent_runs_beyond_TV14: 0
model_calls_outside_runner: 0
verifier_runs_outside_runner: 0
target_skill_changes: 0
evaluator_changes: 0
verifier_changes: 0
v0_13_artifact_changes: 0
v0_14_freeze_artifact_changes: 0
historical_attempt_deletion: 0
retroactive_CTD_authorization: 0
additional_tickers: 0
replacement_run_ids: 0
shell_pipeline: 0
```
