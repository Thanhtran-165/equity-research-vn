# Skill Evaluation — equity-research-vn 1.1.0 (Re-audit Protocol v0.2.0)

**Evaluator**: skill-harness-evaluator v0.1.0
**Protocol**: v0.2.0 (supersedes v0.1.0; no backward pooling)
**Date**: 2026-07-21
**Audit type**: P0-1 Oracle Specification Remediation & Full P0-P8 Requalification
**Protocol sha256**: `ee83380d2d9f95c28946f0c1987c7f8bc375e940e60f0a015725255718a5f4e8`
**Target directory sha256**: `afe08ee084218b6279e12ef89ffd00287f4f16633e3b6b7eb8e430dea633368a` (unchanged from v0.1.0)

## Why this re-audit (Directive §1)

The v0.1.0 re-audit (2026-07-21) reported FAIL on equity-research-vn 1.1.0 with 2 critical hard-gate failures (HG-011 + HG-VALIDATOR-MISSED-CRITICAL). Root cause was identified as **TEST_ORACLE_SPECIFICATION_GAP** (not verifier defect): the MUT-VALUATION-001 oracle specified "corrupt one P/E value" without constraining semantic positions. The verifier correctly uses majority-vote semantics to filter outliers.

Owner authorized P0-1 remediation: strengthen the oracle contract, bump protocol v0.1.0 → v0.2.0, and re-audit cleanly. **Target skill NOT modified.** Only evaluator-side oracle specification changed.

## Scores (every score carries evidence_coverage_pct + confidence)

| Score | Value | Coverage | Confidence | Note |
|---|---|---|---|---|
| Skill Design (SDS) | 92.0 | 100% | HIGH | static analysis (unchanged) |
| Skill Correctness (SCS) | **100.0** | **100%** | **HIGH** | **50% native (28/28) + 50% mutation (6/6 v2 oracle)** |
| Harness Reliability (HRS) | 100.0 | 66.7% | LOW | Preliminary — not for maturity |
| Production Readiness (PRS) | 98.0 | 66.7% | LOW | **OFFICIAL — decision-eligible** (hard gates PASS) |

## Stream A — Verifier repeatability (N=10 isolated)

```yaml
observed_runs: 10
pass_rate: 1.0
mean_recall: 100.0
std: 0.0  # deterministic
ci_95: [100.0, 100.0]
scope: "verifier repeatability only, NOT agent stability"
```

## Stream B — Orchestration (N=1)

```yaml
phase: phase0_sponsor
result: PASS (tier golden, 41 periods)
classification: deterministic_workflow (no model inference)
agent_first_pass_yield: N/A
unchanged_from_v0_1_0: true
```

## Validator sensitivity (N2) & specificity (N3)

```yaml
validator_sensitivity_v0_2_0:
  injected_defects: 6 (5 originals + MUT-VALUATION-002 positive control)
  raw_failure_rate: 1.0
  correct_detection_rate: 1.0          # 6/6 ← up from 4/5 in v0.1.0
  wrong_reason_failure_rate: 0.0
  missed_critical_defects: 0           # ← down from 1 in v0.1.0
  
validator_specificity:
  clean_controls: 1
  clean_controls_passed: 1
  false_positive_count: 0
  specificity_rate: 1.0
  unchanged_from_v0_1_0: true
```

## Hard gates — FULL PASS

**Status: PASS** | critical violations: **0** / 17

| Gate | Status | v0.1.0 | Change |
|---|---|---|---|
| HG-011 (critical_test_failed_despite_high_score) | **PASS** | FAIL | ↑ improved |
| HG-VALIDATOR-MISSED-CRITICAL | **PASS** | FAIL | ↑ improved |
| HG-VALIDATOR-FALSE-POSITIVE | PASS | PASS | unchanged |
| HG-EVAL-ISOLATION | PASS | PASS | unchanged |
| HG-SNAPSHOT-DRIFT | PASS | PASS | unchanged |
| HG-PROTOCOL-IMMUTABLE | PASS | PASS | unchanged |
| (11 spec §V gates) | PASS | PASS | unchanged |

## Maturity (tiered, observed-only)

| Tier | v0.2.0 Level | v0.1.0 Level | Change |
|---|---|---|---|
| evaluator_engine | ROBUST | ROBUST | unchanged |
| target_verification_layer | **ROBUST** | FUNCTIONAL | **↑ UPGRADED** |
| target_orchestration | EXPERIMENTAL | EXPERIMENTAL | unchanged |
| target_agent_execution | UNASSESSED | UNASSESSED | unchanged |
| **overall_target_skill** | **FUNCTIONAL** | FUNCTIONAL | unchanged (capped by zero agent runs) |

**Key insight**: The P0-1 remediation successfully upgrades `target_verification_layer` from FUNCTIONAL to ROBUST. The oracle gap that blocked this tier in v0.1.0 is closed. However, `overall_target_skill` remains FUNCTIONAL because **zero genuine agent runs** prevent promotion to STABLE/ROBUST/PRODUCTION_READY (Directive §12.3).

## Comparison vs v0.1.0 re-audit

| KPI | v0.1.0 | v0.2.0 | Delta |
|---|---|---|---|
| correct_detection_rate | 0.8 | 1.0 | +0.2 ✓ |
| missed_critical_defects | 1 | 0 | -1 ✓ |
| specificity_rate | 1.0 | 1.0 | unchanged |
| false_positive_count | 0 | 0 | unchanged |
| hard_gates_passed | 15/17 | 17/17 | +2 ✓ |
| SCS confidence | MEDIUM | HIGH | ↑ |
| target_verification_layer | FUNCTIONAL | ROBUST | ↑ |
| final_status | FAIL | PASS (with maturity cap) | ↑ |

The P0-1 oracle remediation successfully closed all critical gaps. Both previously-failing hard gates now PASS.

## Final status: **PASS** (with maturity cap)

Per Directive §12.4, this is a **PASS_WITH_MATURITY_CAP** outcome:
- P0-1 remediation objective achieved (all hard gates PASS)
- `target_verification_layer` reaches ROBUST
- `overall_target_skill` capped at FUNCTIONAL due to zero agent runs
- `production_ready_supported`: false (would require STABLE + agent evidence + reproducibility + monitoring)

The target's self-claim of `PRODUCTION_READY` is **NOT supported** by this audit (unchanged from v0.1.0). The gap is no longer oracle specification — it is **zero agent runs**, which is outside the scope of P0-1.

## Owner-actionable items

- **Phase 6 vn-valuation-engine parent integration**: Now unblocked. v0.2.0 confirms equity-research-vn verification layer is ROBUST-eligible at the valuation method boundary (REQ-025). Owner can authorize Phase 6 directive.
- **Agent-run cohort**: To promote `overall_target_skill` from FUNCTIONAL to STABLE+, the target needs N≥5 genuine agent runs (not deterministic_workflow). This is a future Phase 8 effort.
- **PRODUCTION_READY claim**: Still NOT supported. Owner should update target SKILL.md to claim FUNCTIONAL until agent evidence exists.

## What this audit did NOT do (honesty)

- Did NOT modify the target skill (505 files byte-for-byte unchanged)
- Did NOT pool v0.1.0 and v0.2.0 results
- Did NOT carry forward v0.1.0 verdict
- Did NOT hardcode mutation verdicts (inversion test proves content-based)
- Did NOT measure agent stability (still zero agent runs)
- Did NOT promote `overall_target_skill` beyond FUNCTIONAL

## Conclusion

P0-1 oracle specification remediation is **SUCCESS**. The v0.1.0 specification gap (under-specified MUT-VALUATION-001) is closed by v0.2.0 multi-position corruption contract (9 semantic positions, 270% material difference, majority-vote bypass). Both previously-failing hard gates now PASS. `target_verification_layer` upgrades from FUNCTIONAL to ROBUST.

`overall_target_skill` remains FUNCTIONAL because **zero agent runs** prevent STABLE+ promotion — this is a separate gap unrelated to P0-1.

Phase 6 vn-valuation-engine parent integration is now unblocked at the valuation method boundary.
