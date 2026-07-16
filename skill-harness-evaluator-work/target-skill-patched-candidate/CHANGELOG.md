# CHANGELOG — target-skill-patched-candidate (verification-layer patches)

**NOT the original skill.** This is a separate candidate copy of `equity-research-vn`'s verification layer (`scripts/independent_verifier.py` + `requirements.yaml`) with the 4 P0 fixes from the audit. Original at `~/.zcode/skills/equity-research-vn` is untouched.

## P0 fixes (audit 2026-07-12)

### P0-1: REQ-028 false-positive (specificity)
- **Before:** `verify_chart_runtime_check` treated EVERY chart-like JS reference as a required canvas. Conditional refs (`if ($(id))`) and fallback refs (`$(primary) || $(fallback)`) flagged as missing → clean deployed PNJ report wrongly FAILed.
- **After:** classify refs into `unconditional_required` vs conditional/fallback. Only missing *unconditional* canvases count. A few absent canvases → advisory WARN, not deploy-blocking FAIL. Critical FAIL only for: duplicate IDs, no DATA, no Chart.js, canvas-after-body, or >30% required canvases missing.
- **Evidence:** audit mutation-results.json#clean_control (REQ-028 fail on clean).

### P0-2: REQ-009 missed mutation (sensitivity)
- **Before:** `min_canonical_match: 15/22` was so lenient that removing 1 canonical section still PASSed (MUT-SECTION-001). Count-based proxy, not identity.
- **After:** tightened to `20/22` AND added `required_signal_sections: [sec-hero, sec-exec, sec-valuation]` — each must be individually present (not just counted). `verify_section_map` now requires both.
- **Evidence:** MUT-SECTION-001 (REQ-009 PASS after sec-bs removed).

### P0-3: REQ-025 missed mutation (sensitivity)
- **Before:** `verify_valuation_recompute` used `re.search` (first-match only). A corrupted multiple in a non-anchored position was invisible if a valid multiple matched the regex first (MUT-VALUATION-001).
- **After:** `re.findall` for ALL P/E and P/B occurrences; verify EACH against the computed value. Any divergent occurrence = FAIL.
- **Evidence:** MUT-VALUATION-001 (REQ-025 PASS after P/E corrupted).

### P0-4: REQ-021 evidence provenance + state binding
- **Before:** REQ-021 was computed but NEVER written as an evidence file → mutation harness saw "MISSING" (MUT-DEPLOY-001). Worse, deploy status could theoretically be confirmed by evidence not bound to the current requirement state.
- **After:** write `evidence/REQ-021.json` with provenance block: `{source_run_id, source_artifact, source_artifact_sha256, evidence_generated_after_validation, unresolved_required_failures, all_requirements_pass, requirement_state_at_eval}`. Reject-by-design evidence from a different run/snapshot/pre-validation.
- **Evidence:** MUT-DEPLOY-001 (REQ-021 MISSING).

## Exit criteria (must verify before promoting to original)
```yaml
clean_control_false_positive_count: 0
missed_critical_mutations: 0
correct_detection_rate: 1.0
wrong_reason_failure_rate: 0.0
```
Note: 5/5 detection proves the verifier passes THIS suite, not absolute correctness.
