# Failure Taxonomy — equity-research-vn audit

4-bucket → 9-sub (spec §IX preserved verbatim). Each observed failure mapped to its root cause.

## Observed failures (from real audit, P4)

| Finding | Bucket | Sub-cause | Evidence |
|---|---|---|---|
| REQ-028 false-positive on clean deployed PNJ report | Enforcement | validator_error | mutation-results.json#clean_control (verdict FAIL, REQ-028 fail) |
| MUT-SECTION-001 missed (REQ-009 PASS after section removed) | Enforcement | validator_error | mutation-results.json#MUT-SECTION-001 (wrong_reason) |
| MUT-VALUATION-001 missed (REQ-025 PASS after P/E corrupted) | Enforcement | validator_error | mutation-results.json#MUT-VALUATION-001 (wrong_reason) |
| MUT-DEPLOY-001 missed (REQ-021 evidence MISSING) | Enforcement | validator_error | mutation-results.json#MUT-DEPLOY-001 (MISSING) |
| CTD orphan report (no sibling data/) → REQ-022..026 structurally unverifiable | Infrastructure | fixture_error | baseline-test-results.json#CTD |
| REQ-028 logic reflects a real residual artifact defect (chartBSDt2 duplicate) on PNJ | Infrastructure | fixture_error | evidence/REQ-028.json (bare_canvas/duplicate detection) |

## Bucket summary

### Specification (human_specification_error, skill_design_error)
None observed. Design is strong (SDS=92): thin orchestrator, 28 machine-readable REQs, per-phase verification, deploy gate. The `min_canonical_match: 15/22` threshold is borderline-spec but not a defect per se.

### Execution (model_adherence_error, context_error)
**Not assessable.** No genuine agent runs were observed (stream B was `deterministic_workflow` — run_phase.py orchestrates but executes no model inference). Claiming model-adherence findings here would be fabrication.

### Enforcement (harness_enforcement_error, validator_error) — THE dominant bucket
The verification layer has real blind spots:
1. **REQ-028 over-triggers** (false positive on clean artifact) — the chart_runtime_check logic flags `chartBSDt2` as a duplicate on a report that actually renders. Either the check is too strict or the artifact genuinely has a duplicate canvas the skill shipped anyway.
2. **REQ-009 under-triggers** (missed removed section) — `min_canonical_match: 15/22` is so lenient that removing one canonical section still passes. A defect this layer was designed to catch slips through.
3. **REQ-025 under-triggers** (missed corrupted multiple) — `valuation_recompute_check` only inspects specific P/E and P/B regex patterns; corrupting a multiple in a position the regex doesn't cover defeats it.
4. **REQ-021 evidence MISSING** — the all_requirements_pass gate is synthesized separately and its evidence file isn't written the same way as other REQs, so the mutation harness can't confirm detection.

### Infrastructure (tool_error, fixture_error, environment_error)
- CTD report shipped without its `data/` dir → 5 REQs unverifiable. Fixable by co-locating data.
- REQ-028 may reflect a genuine artifact defect rather than a verifier bug (needs the specificity test to disambiguate — which it did: the clean control FAILS, so it IS a false positive for deploy-gating purposes).

## Key distinction (the audit's central value)
The failures here are **not** "the agent is lazy" (we have no agent evidence). They are **verifier blind spots** — exactly the class of defect the mutation/specificity testing was built to surface, and which a naive "the verifier passes 93%, ship it" assessment would have hidden.
