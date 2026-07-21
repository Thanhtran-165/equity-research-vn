# Improvement Recommendations — equity-research-vn 1.1.0 (re-audit 2026-07-21)

Split by 6 change-categories (spec §X.6). Priority P0/P1/P2. **Original skill NOT modified** — these are owner-actionable only.

## Comparison vs prior audit (2026-07-12)

```yaml
metric                       prior   re-audit   delta
specificity_rate             0.0     1.0        ✅ FIXED (REQ-028 false positive gone)
correct_detection_rate       0.4     0.8        ✅ +0.4 (REQ-009/REQ-021 caught)
missed_critical_defects      3       1          ✅ -2 (only REQ-025 oracle remains)
clean_control_first_pass     0.0     1.0        ✅ FIXED
overall_status               FAIL    FAIL       ⚠ same — different reason
```

The target has materially improved. Prior audit's 2 P0 critical blind spots (REQ-028 FP, REQ-009 threshold lỏng) are RESOLVED. The remaining FAIL is a **test oracle specification gap**, not a verifier defect.

## P0 — blocking (would change maturity tier)

### oracle_changes (NEW category for re-audit)

- **P0-1: Update MUT-VALUATION-001 oracle contract.** The original contract specified "corrupt one P/E value" without semantic-position scope. A real PNJ report has 11 P/E 9.1x positions; corrupting only 1 (KPI card) is correctly filtered by the verifier's majority-vote logic. **Action:** Either (a) update the oracle to corrupt ≥3 positions or all occurrences, or (b) document in SKILL.md that the verifier's majority-vote semantics are part of the correctness contract and adjust oracle expectations. The stricter MUT-VALUATION-002 (corrupt all 11 positions) was caught correctly — proving the verifier is sound. Until the oracle is updated, this re-audit cannot reach ROBUST on `target_verification_layer`.

## P1 — should-fix

### harness_changes

- **P1-1: Add `source_run_id` + `source_snapshot_hash` to REQ-021 evidence file.** (Residual from prior P0-3.) Although re-audit confirms the current implicit binding (per-run .task-state) catches deploy-block correctly, explicit provenance fields would harden against cross-run evidence contamination in future multi-ticker concurrent runs. *Action:* write `evidence/REQ-021.json` with `{source_run_id, source_snapshot_hash, unresolved_required_failures, all_requirements_pass, generated_after_validation}`.

### tooling_changes

- **P1-2: Co-locate `data/` with every shipped report.** (Residual from prior P1-2.) The CTD_Complete_Report.html ships orphaned (no `data/`), making REQ-022..026 unverifiable (5 critical REQs). Phase7-deploy.md should require `data/` dir alongside HTML before artifact considered complete.

### validator_changes

- **P1-3: Populate `_summary.json#details` array.** (Residual from prior P1-3.) Currently `details` is empty, forcing consumers to read per-REQ files. *Action:* populate with per-REQ {id,status,method} so a single file gives the full picture.

## P2 — nice-to-have

### skill_text_changes

- **P2-1: Document verifier's majority-vote semantics for valuation multiples in SKILL.md (or VERIFIER_LIMITATIONS.md).** A report with multiple distinct P/E values for the same metric is treated as AMBIGUOUS unless a primary semantic marker (data-metric, TTM, val-card) identifies one. Honest abstention over silent weakness.

### fixture_changes

- **P2-2: Add a regression fixture set** to the skill itself (golden PASS report + known-bad mutations including the all-positions variant) so future verifier edits are checked.

### observability_changes

- **P2-3: Emit structured run-result from `run_phase.py`.** Currently free-text stdout; structured {steps_observed, requirements_passed/failed, duration_ms, model_inference_detected} would let the evaluator score orchestration deterministically (currently relies on stdout classification).

## What should move from prompt → code
- Already largely done in 1.1.0 (HYBRID_DETERMINISTIC_SHELL). Remaining prose areas (phase prompt "KHÔNG được" lists) could be promoted to machine-checkable prohibited_actions.

## What should stay with the model
- Fundamental analysis narrative, insight generation, news categorization — genuinely open-ended. Evaluator must not penalize research skills for non-determinism in inherently non-deterministic domains.

## Maturity impact if owner applies P0-1

```yaml
if_P0_1_applied:
  correct_detection_rate: 1.0   # (after oracle update or MUT-VALUATION-002 substitution)
  missed_critical_defects: 0
  specificity_rate: 1.0
  HG-VALIDATOR-MISSED-CRITICAL: PASS
  HG-011: PASS
  target_verification_layer: ROBUST-eligible (still needs N=10 with new oracle)
  overall_target_skill: still capped at FUNCTIONAL until genuine agent runs measured
```
