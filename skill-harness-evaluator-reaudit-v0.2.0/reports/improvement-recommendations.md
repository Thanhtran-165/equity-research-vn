# Improvement Recommendations (v0.2.0)

**Date:** 2026-07-21

## P0-1 status: CLOSED

The v0.1.0 P0-1 recommendation (update MUT-VALUATION-001 oracle contract) has been **fully addressed** in v0.2.0:

```yaml
P0_1_status: CLOSED
resolution: |
  v0.2.0 oracle contract requires MULTI_POSITION_SEMANTIC_CORRUPTION (≥3 positions).
  Actual v2 mutation corrupts 9 semantic positions with 270% material difference.
  Majority-vote bypass: true.
  All 6 mutations now caught (was 4/5 in v0.1.0).
verification: target_verification_layer upgraded FUNCTIONAL → ROBUST.
```

## Remaining P1/P2 items (unchanged from v0.1.0)

These are owner-actionable but outside P0-1 scope:

### P1 — should-fix

- **P1-1 harness**: Add explicit `source_run_id`/`source_snapshot_hash` to REQ-021 evidence file (residual from v0.1.0).
- **P1-2 tooling**: Co-locate `data/` with shipped reports (CTD orphan artifact).
- **P1-3 validator**: Populate `_summary.json#details` array.

### P2 — nice-to-have

- **P2-1 skill_text**: Document verifier's majority-vote valuation semantics in SKILL.md (now formalized in v0.2.0 protocol).
- **P2-2 fixture**: Add regression fixture set to skill itself.
- **P2-3 observability**: Structured run-result from `run_phase.py`.

## NEW recommendations from v0.2.0 re-audit

### Promote agent-run cohort (P0 for PRODUCTION_READY)

```yaml
recommendation: |
  To promote overall_target_skill from FUNCTIONAL to STABLE+ (and eventually PRODUCTION_READY),
  the target needs N>=5 genuine agent runs (not deterministic_workflow).
  
  This is a Phase 8 long-run generalization effort, outside P0-1 scope.
  
  Until then, target SKILL.md self-claim of PRODUCTION_READY is NOT supported.
```

### Update SKILL.md self-claim (P1)

```yaml
recommendation: |
  Target SKILL.md currently claims maturity: PRODUCTION_READY (VERSION file).
  v0.2.0 audit supports FUNCTIONAL (overall), ROBUST (verification layer only).
  Owner should update SKILL.md to claim FUNCTIONAL until agent evidence exists.
```

## Phase 6 unblock

```yaml
vn_valuation_engine_phase_6:
  status: UNBLOCKED_BY_V0_2_0_REAUDIT
  reason: |
    Phase 5R closed with vn-valuation-engine standalone_maturity FUNCTIONAL.
    v0.2.0 re-audit confirms equity-research-vn verification layer ROBUST at valuation boundary.
    Parent integration regression can proceed with clean valuation verifier.
  awaiting: Owner directive to open Phase 6.
```
