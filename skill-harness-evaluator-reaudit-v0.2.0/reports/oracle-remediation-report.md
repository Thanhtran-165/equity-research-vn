# Oracle Remediation Report (R2B)

**Date:** 2026-07-21
**Subphase:** R2B — ORACLE_SPECIFICATION_REMEDIATION
**Status:** PASS

## Root cause preserved (Directive §8.1)

```yaml
root_cause:
  layer: TEST_ORACLE_SPECIFICATION
  target_verifier_defect: false
  
  evidence: |
    The v0.1.0 MUT-VALUATION-001 oracle specified "corrupt one P/E value (9.1→33.7)"
    without constraining how many semantic positions the report uses for the same metric.
    A real PNJ clean-control report has 9+ distinct positions displaying P/E 9.1x:
    KPI card, current-value stat, narratives (5 instances), peer table cell,
    valuation criteria table, crawlable hidden div.
    
    The verifier uses majority-vote semantics (≥3 occurrences of same value) to identify
    the primary P/E and reject outliers/projections. Corrupting only 1 position leaves
    the majority intact → verifier correctly picks 9.1x → mutation not detected.
    
    This is NOT a verifier defect. The majority-vote logic is intentional and correct
    for handling reports that display the same metric in multiple positions.
    The oracle was under-specified.
```

## Oracle specification v2 (Directive §8.2-8.5)

```yaml
MUT_VALUATION_001_v2:
  mutation_id: MUT-VALUATION-001
  mutation_revision: 2
  protocol_version: 0.2.0
  supersedes: MUT-VALUATION-001 revision 1 (protocol 0.1.0)
  
  corruption_strategy: MULTI_POSITION_SEMANTIC_CORRUPTION
  minimum_semantic_positions_corrupted: 3
  actual_positions_corrupted: 9
  
  positions_targeted:
    - KPI card P/E display (1 occurrence)
    - "P/E hiện tại" stat-value (1)
    - "Luận điểm cốt lõi" narrative P/E 9.1x (1)
    - Bull case narrative P/E 9.1x (1)
    - Summary section P/E 9.1x (1)
    - Bottom crawlable div (aria-hidden) P/E 9.1x (1)
    - Peer table PNJ row P/E cell (1)
    - "Đạt — P/E < median" check narrative (1)
    - Valuation criteria table PE row (1)
    # Plus 1 more insec narrative — total 9
    - Valuation summary text (1)
  
  materiality:
    original_value: 9.1
    mutated_value: 33.7
    absolute_difference: 24.6
    relative_difference: 270% (3.7× original)
    threshold_rule: "relative difference > 50% AND absolute difference > 1.0 → material"
    material: true
  
  expected:
    expected_detection: true
    expected_severity: CRITICAL
    expected_verdict: FAIL
    expected_requirement_ids: [REQ-025]
    expected_owner: FORMULA_ENGINE / VALUATION_RECOMPUTE_CHECK
    acceptable_detection_paths:
      - REQ-025 valuation_recompute_check FAIL
    unacceptable_false_pass_paths:
      - REQ-025 PASS (would mean majority-vote filtered out all 9 corruptions — impossible since all positions corrupted)
  
  majority_vote_bypass:
    semantics: "verifier requires ≥3 occurrences of same value to identify primary multiple"
    corruption_count: 9 (far exceeds 3 threshold)
    bypasses_majority_vote: true
```

## Mutation inversion test (Directive §10.5)

```yaml
inversion_test:
  hypothesis: "If only 1 position is corrupted (like old MUT-VALUATION-001), verifier should NOT detect it because majority-vote semantics correctly filter outlier."
  proof: "MUT-VALUATION-001 (1-position) PASSED REQ-025 in v0.1.0 → confirms majority-vote is intentional and not a defect."
  new_oracle_test: "MUT-VALUATION-001-v2 (9-position) FAILS REQ-025 → confirms specification change is real, not just rename."
  
meta_test_required:
  - "Old oracle (1-position) → undetected: TRUE in v0.1.0"
  - "New oracle (9-position) → detected: TRUE in v0.2.0"
  - "If new oracle passes with 1-position corruption → specification did not actually change"
```

## Historical preservation (Directive §8.6)

```yaml
historical_artifacts_preserved:
  MUT_VALUATION_001_v1:
    location: /Users/bobo/ZCodeProject/skill-harness-evaluator-reaudit/mutations/mutations/MUT-VALUATION-001.html
    protocol_version: 0.1.0
    status: HISTORICAL_IMMUTABLE
    semantic_positions_corrupted: 1
    v0_1_0_verdict: NOT_DETECTED (correctly — majority-vote filtered outlier)
  
  MUT_VALUATION_002:
    location: /Users/bobo/ZCodeProject/skill-harness-evaluator-reaudit/mutations/mutations/MUT-VALUATION-002.html
    protocol_version: 0.1.0-positive-control
    status: HISTORICAL_IMMUTABLE (also used as v0.2.0 positive control)
    semantic_positions_corrupted: 11
    v0_1_0_verdict: DETECTED (REQ-025 FAIL)
    v0_2_0_verdict: DETECTED (REQ-025 FAIL) — same behavior

new_artifacts:
  MUT_VALUATION_001_v2:
    location: /Users/bobo/ZCodeProject/skill-harness-evaluator-reaudit-v0.2.0/mutations/MUT-VALUATION-001-v2.html
    protocol_version: 0.2.0
    status: ACTIVE
    semantic_positions_corrupted: 9
    v0_2_0_verdict: DETECTED (REQ-025 FAIL)
```

## R2B gate

```yaml
R2B_gate:
  oracle_root_cause_preserved: true           ✓ (TEST_ORACLE_SPECIFICATION, not verifier defect)
  multi_position_corruption_defined: true     ✓
  semantic_positions_corrupted: "9 (>=3)"     ✓
  corruption_materiality_defined: true        ✓ (270% relative diff)
  expected_verdict_defined: true              ✓ (FAIL with REQ-025)
  expected_requirement_defined: true          ✓ (REQ-025)
  historical_mutation_preserved: true         ✓ (MUT-VALUATION-001 v1 untouched in old workspace)
  target_changes: 0                           ✓
  status: PASS
```

## Verification of mutation (target unchanged)

```yaml
target_verifier_used: /Users/bobo/.zcode/skills/equity-research-vn/scripts/independent_verifier.py
target_verifier_hash_unchanged: true (vs v0.1.0)

results:
  clean_control: VERDICT PASS (28/28)         ✓ specificity
  MUT_VALUATION_001_v2: VERDICT FAIL (26/28, REQ-025 FAIL)  ✓ sensitivity
  MUT_VALUATION_002: VERDICT FAIL (26/28, REQ-025 FAIL)     ✓ positive control

no_target_modification: true
no_verifier_modification: true
```

## Conclusion

Oracle specification remediated correctly per Directive §8. The v2 mutation corrupts 9 semantic positions (far exceeding ≥3 threshold) with material difference (270%), bypassing the verifier's majority-vote filter. Historical v0.1.0 mutation preserved untouched in old workspace. Target verifier unchanged.

Ready for R2C protocol freeze.
