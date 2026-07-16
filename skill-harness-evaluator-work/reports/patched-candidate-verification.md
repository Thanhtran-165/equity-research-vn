# Patched-Candidate Verification Report

**Candidate:** `target-skill-patched-candidate/` (separate copy of `equity-research-vn` verification layer)  
**Original:** `~/.zcode/skills/equity-research-vn` — **UNTOUCHED** (HG-004/HG-005 PASS)  
**Date:** 2026-07-12

Following the approved sequence: *fix validator → validate validator → (only then) run agent*. This report covers "fix validator" + "validate validator" only. No agent stability test run yet (correct order).

## P0 exit criteria — ALL MET

| Criterion | Required | Original verifier | Patched candidate | Status |
|---|---|---|---|---|
| clean_control_false_positive_count | 0 | 1 | **0** | ✅ |
| missed_critical_mutations | 0 | 2 (refined oracles) | **0** | ✅ |
| correct_detection_rate | 1.0 | 0.6 | **1.0** | ✅ |
| wrong_reason_failure_rate | 0.0 | 0.4 | **0.0** | ✅ |
| specificity_rate | 1.0 | 0.0 | **1.0** | ✅ |

Evidence: `mutation-results-patched.json` vs `mutation-results-orig-refined.json`.

## What the 4 patches do

1. **P0-1 REQ-028 (false-positive fix):** `verify_chart_runtime_check` now distinguishes unconditional canvas refs from conditional (`if ($(id))`) and fallback (`$(a) || $(b)`) refs. Only missing *unconditional* canvases count, and a minority absent → advisory WARN (not deploy-blocking FAIL). Critical FAIL reserved for: duplicate IDs, no DATA, no Chart.js, canvas-after-body, >30% required missing.
2. **P0-2 REQ-009 (sensitivity fix):** `min_canonical_match` 15→20, plus `required_signal_sections: [sec-hero, sec-exec, sec-valuation]` each individually mandatory (not just counted).
3. **P0-3 REQ-025 (sensitivity fix):** `verify_valuation_recompute` now checks every P/E occurrence in a *primary valuation context* (val-card / current-price), not first-match regex. Peer/historical/projected multiples remain advisory.
4. **P0-4 REQ-021 (provenance + state-binding fix):** writes `evidence/REQ-021.json` with `{source_run_id, source_artifact, source_artifact_sha256, evidence_generated_after_validation, unresolved_required_failures, all_requirements_pass, requirement_state_at_eval}`. Deploy evidence is now bound to the current run + current artifact + post-validation timestamp.

## Oracle refinements (made the mutations honest, not the verifier weaker)

Two mutations were initially weak oracles that the verifier *correctly* passed — fixed the oracles, not the verifier:
- **MUT-SECTION-001:** retargeted from `sec-bs` (non-signal) to `sec-exec` (a required_signal_section) — now tests the real each-signal-section property.
- **MUT-VALUATION-001:** the corruption regex couldn't cross HTML tags, so it hit an unrelated `Nx` and left the real `P/E ... 9.1x` values intact. Now handles tags-between-label-and-value and corrupts every primary P/E.

This is itself a finding: **mutation oracles must be validated against the artifact's actual structure** — a mutation that "applied=True" but didn't touch the targeted business value produces a false sense of verifier correctness.

## Honest limits of this result

- 5/5 detection proves the patched verifier passes THIS suite — **not absolute correctness** (your note).
- P1 (expand mutation families: capex, evidence-provenance, runtime, source-claim, partial-abstention, stale-state, cross-run contamination) still pending.
- After P1 expansion, re-verify. Only then proceed to P2 (genuine agent stability tests).

## Files
- `target-skill-patched-candidate/scripts/independent_verifier.py` (4 patches, sha256 `d6acebd1…` → recompiled)
- `target-skill-patched-candidate/requirements.yaml` (REQ-009 threshold + signal sections)
- `target-skill-patched-candidate/CHANGELOG.md` (before/after per patch)
- `patched-skill-dir/` (run-ready copy with SKILL_DIR redirected)
- `mutation-results-patched.json`, `mutation-results-orig-refined.json` (before/after evidence)

## Recommendation
The patched candidate is a defensible P0 fix and meets the exit criteria. **Promotion to the original skill is the owner's decision** — the auditor recommends: (1) review the patches, (2) run P1 mutation expansion against the patched verifier, (3) only then merge + proceed to agent stability tests.
