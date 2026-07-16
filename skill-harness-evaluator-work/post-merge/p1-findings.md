# P1 Mutation Expansion — Findings (merged skill, verification-layer 0.1.0)

P1 = one mutation per important validator NOT covered by P0. Ran 9 mutations on the **merged** skill (fresh, post-merge). Results below are observed.

## Summary
```yaml
clean_control: PASS (specificity 1.0 — no false positive)
valid_oracles: 7
invalid_oracles: 2  (MUT-DATA-BS-001, MUT-CHARTDUP-001 — oracle refinements pending)
correct_detection_rate_validity_aware: 5/7 = 0.714
missed_critical_defects: 2   ← NEW blind spots found
```

## NEW blind spots found (P1 value)

### P1-1: REQ-022 data_accuracy_check — number matching too lenient (MISSED)
- **Mutation MUT-DATA-REV-001**: corrupted a revenue figure (`34,976 → 104,928`). REQ-022 still PASSed.
- **Root cause**: `verify_data_accuracy` scans the ENTIRE report text for *any* number within tolerance of the ground-truth value. With many revenue figures present (per-year table), an UN-corrupted year's value still matches → the corrupted year goes undetected.
- **Severity**: critical (anti-fabrication gate defeated by partial corruption).
- **Recommended fix**: match numbers by *position/context* (e.g., value adjacent to its year label), not global any-match. Reject if the ground-truth value for a specific year is absent in its expected context.

### P1-2: REQ-027 external_claim_flag_check — pattern coverage gap (MISSED)
- **Mutation MUT-EXTCLAIM-001**: injected `WCM LN 15.2 tỷ — MCH DT 8.4 tỷ — 240 điểm bán`. REQ-027 still PASSed.
- **Root cause**: the flag-check looks for the *flag* word (`ước tính|estimate|external|marketing`) but the mutation includes "internal estimate" / no Vietnamese flag word → the claim goes unflagged. Either the patterns are too narrow or the check passes when no claim is detected.
- **Severity**: high (unflagged external claim = silent speculation).
- **Recommended fix**: invert the logic — when a WCM/MCH/store-count claim is present, REQUIRE an adjacent flag; absence of flag on a matching claim = FAIL.

## Validators that PASSED their P1 mutation (regression-safe)
REQ-026 (chart_data), REQ-011 (canvas_check), REQ-013 (content_depth), REQ-020 (div_balance), REQ-012 (count) — all correctly detected.

## INVALID_ORACLE (oracle refinement needed, not verifier defects)
- **MUT-DATA-BS-001** (Total Assets): locator didn't find the label in this report's language → INVALID. Oracle needs a report-specific label or a value-anchor approach.
- **MUT-CHARTDUP-001** (duplicate canvas): the duplicate-detection branch fired (correct=True) but the locator reports None (no pre-existing duplicate) → flagged INVALID by the provenance rule. The verifier actually *did* detect it; the oracle's "before" state was None because there was no duplicate to begin with. This is an oracle-semantics edge: for additive mutations, `target_value_before=None` is expected and should still be VALID if `target_value_after` is non-None. **Recommended evaluator fix**: relax oracle validity for additive-oracle mutations (before=None & after!=None → VALID).

## Status
- P0 suite (5 mutations): **all PASS** on merged skill (post-merge gates met, merge committed).
- P1 suite (9 mutations): **found 2 new critical/high blind spots** (REQ-022, REQ-027) + 2 oracle-refinement items.
- **Agent stability testing remains BLOCKED** — P1 surfaced new verifier defects that must be patched (next P0 cycle) before agent tests are meaningful.

## Recommended next cycle (owner's call)
1. Patch REQ-022 (context-anchored number matching) + REQ-027 (inverted flag logic) in a new patched candidate.
2. Fix the 2 INVALID_ORACLE items (label-anchored Total-Assets; additive-oracle validity relaxation in the evaluator).
3. Re-run P0+P1 combined; only proceed to agent stability when combined correct_detection_rate == 1.0.
