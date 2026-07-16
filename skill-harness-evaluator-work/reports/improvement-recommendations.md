# Improvement Recommendations — equity-research-vn

Split by 6 change-categories (spec §X.6). Priority P0 (blocker) / P1 (should-fix) / P2 (nice). Original skill NOT modified.

## P0 — blocking (would change maturity tier)

### validator_changes
- **P0-1: Fix REQ-028 false positive.** The clean deployed PNJ report FAILs REQ-028 (chart_runtime_check) yet renders. Either (a) the check's duplicate-canvas detection is over-broad, or (b) the artifact genuinely ships a duplicate `chartBSDt2` canvas. Either way, a report that passes human review and deploys should not be gated FAIL. *Action:* investigate `verify_chart_runtime_check`; tighten the duplicate heuristic; re-run the specificity gate.
- **P0-2: Tighten REQ-009 `min_canonical_match` from 15/22.** Mutation MUT-SECTION-001 removed a canonical section and REQ-009 still PASSed. The threshold is too lenient for a "critical" requirement. *Action:* raise to ≥20/22 or require the specific high-signal sections (sec-hero, sec-exec, sec-valuation) to be individually mandatory.

### harness_changes
- **P0-3: REQ-021 evidence-provenance binding (most severe).** MUT-DEPLOY-001 showed REQ-021 (all_requirements_pass) is handled out-of-band and its evidence file isn't written like other REQs (mutation harness saw "MISSING"). This is a **provenance + state-binding** defect, not just a parity issue: if deploy status can be confirmed by evidence not bound to the *current* requirement state, then `current FAIL + stale/cross-run PASS evidence → deploy wrongly allowed` becomes possible.
  *Action:* bind REQ-021 evidence to the current run/snapshot:
  ```yaml
  deployment_gate:
    source_run_id: current_run_id
    source_snapshot_hash: current_snapshot_hash
    unresolved_required_failures: 0
    all_requirements_pass: true
    evidence_generated_after_validation: true
  ```
  Reject evidence that: comes from a different run; a different snapshot hash; was generated before the final validation pass; or carries no requirement-state hash. Write `evidence/REQ-021.json` with this provenance block, same schema as other REQs.

## P1 — should-fix

### validator_changes
- **P1-1: Broaden REQ-025 valuation_recompute_check coverage.** MUT-VALUATION-001 corrupted a P/E value in a position the regex didn't anchor on, and REQ-025 PASSed. *Action:* extract ALL P/E and P/B occurrences (not just first-match) and verify each; or parse a structured valuation card rather than regex over free text.

### tooling_changes
- **P1-2: Co-locate `data/` with every shipped report.** CTD_Complete_Report.html shipped orphaned, making REQ-022..026 unverifiable (5 critical REQs). *Action:* phase7-deploy.md should require the `data/` dir alongside the HTML before the artifact is considered "complete".

### observability_changes
- **P1-3: Populate `_summary.json#details`.** The verifier leaves the `details` array empty, forcing consumers to read per-REQ files. *Action:* populate details with per-REQ {id,status,method} so a single file gives the full picture.

## P2 — nice-to-have

### skill_text_changes
- **P2-1: Document the verifier's known blind spots** in SKILL.md (or a VERIFIER_LIMITATIONS.md) so users know REQ-009/025 have coverage gaps. Honest abstention over silent weakness.

### fixture_changes
- **P2-2: Add a regression fixture set** to the skill itself (golden PASS report + known-bad mutations) so future edits to the verifier are checked against the same oracles this audit used.

### harness_changes
- **P2-3: Make `run_phase.py` emit a structured run-result** (steps_observed, requirements_passed/failed) instead of free-text stdout, so the evaluator can score orchestration deterministically.

## What should move from prompt → code
- REQ-009 canonical-section requirement and REQ-025 multiple recomputation are already in code (good). The remaining prose-heavy areas (phase prompts' "KHÔNG được" lists) could be promoted to machine-checkable prohibited_actions — already partially done in `requirements.yaml`.

## What should stay with the model
- Fundamental analysis narrative, insight generation, news categorization — genuinely open-ended; keep as model decisions. The evaluator must not penalize a research skill for non-determinism in domains that are inherently non-deterministic.
