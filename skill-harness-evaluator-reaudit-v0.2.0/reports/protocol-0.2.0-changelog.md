# Protocol v0.2.0 Changelog

**Date:** 2026-07-21
**Supersedes:** v0.1.0
**Backward pooling:** NOT ALLOWED

## Changes (Directive §9.2)

### Strengthened (in v0.2.0)

```yaml
changes:
  - id: STRENGTHENED_MUT_VALUATION_001_ORACLE
    description: |
      v0.1.0 MUT-VALUATION-001 oracle specified "corrupt one P/E value" without 
      constraining semantic positions. Real PNJ report has 9+ positions for same P/E.
      Verifier correctly uses majority-vote (≥3 same value) to identify primary multiple.
      Single-position corruption correctly filtered as outlier → undetected.
      v0.2.0 oracle requires multi-position semantic corruption.
  
  - id: ADDED_MULTI_POSITION_SEMANTIC_CORRUPTION_REQUIREMENT
    description: |
      New oracle contract field: corruption_strategy = MULTI_POSITION_SEMANTIC_CORRUPTION
      with minimum_semantic_positions_corrupted >= 3.
      Actual v2 mutation corrupts 9 positions.
  
  - id: ADDED_ORACLE_MATERIALITY_RULE
    description: |
      New oracle contract field: materiality with original_value, mutated_value,
      relative_difference_pct, threshold_rule.
      Rule: relative_difference > 50% AND absolute > 1.0.
      v2 mutation: 9.1 → 33.7 = 270% relative diff (material).
  
  - id: CLARIFIED_MAJORITY_VOTE_SEMANTICS
    description: |
      v0.2.0 explicitly notes majority_vote_bypass=true for the new oracle.
      This is documentation only — verifier behavior unchanged.
  
  - id: PRESERVED_TARGET_AND_VERIFIER
    description: |
      No changes to target skill (equity-research-vn 1.1.0).
      No changes to target verifier (independent_verifier.py).
      No changes to target requirements.yaml.
      Only the oracle specification (evaluator-side) changed.
```

### Unchanged (explicit per Directive §9.2)

```yaml
unchanged:
  - target (equity-research-vn 1.1.0 — 505 files byte-for-byte)
  - target verifier (independent_verifier.py byte-for-byte)
  - target requirements (requirements.yaml byte-for-byte)
  - hard-gate definitions (17 gates, same conditions)
  - scorecard denominator (10 runs, 5 mutations + clean control)
  - maturity rubric (EXPERIMENTAL/FUNCTIONAL/ROBUST/STABLE/PRODUCTION_READY thresholds)
  - weights (PRS 0.25/0.35/0.40, SDS subweights, HRS subweights, SCS subweights)
  - mutation oracles except MUT-VALUATION-001 (4 of 5 unchanged)
  - na_policy (excluded_from_denominator)
```

## Why a new protocol version (Directive §9.1)

Per protocol immutability principle (HG-PROTOCOL-IMMUTABLE), once a protocol is frozen 
its weights/thresholds/oracles cannot change mid-audit. Changing the MUT-VALUATION-001 oracle 
contract — even though it's an evaluator-side specification fix, not a target change — 
requires a new protocol version. v0.1.0 results are preserved as historical evidence; 
v0.2.0 produces its own independent results.

## Hash continuity

```yaml
v0_1_0:
  protocol_sha256: 72ce36017ab1aafd4a8fbeef1bf7af2bc7888653df4ec2818df576be4d7b9c23
  preserved_at: /Users/bobo/ZCodeProject/skill-harness-evaluator-reaudit/reports/evaluation-protocol.lock.yaml

v0_2_0:
  protocol_sha256: ee83380d2d9f95c28946f0c1987c7f8bc375e940e60f0a015725255718a5f4e8
  frozen_at: /Users/bobo/ZCodeProject/skill-harness-evaluator-reaudit-v0.2.0/evaluation-protocol.lock.yaml

backward_pooling_allowed: false
```
