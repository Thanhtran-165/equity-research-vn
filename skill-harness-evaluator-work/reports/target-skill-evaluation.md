# Skill Evaluation — equity-research-vn

**Evaluator**: skill-harness-evaluator v0.1.0  
**Date**: 2026-07-12T13:12:28.241981  
**Protocol sha256**: `67a869e781259444…`  
**Observed runs**: 10 | Projected: 0

## Scores (every score carries evidence_coverage_pct + confidence)

| Score | Value | Coverage | Confidence | Note |
|---|---|---|---|---|
| Skill Design (SDS) | 92.0 | 100% | HIGH | static analysis |
| Skill Correctness (SCS) | 66.45 | 80% | MEDIUM | 50% native + 50% mutation (independent) |
| Harness Reliability (HRS) | 88.33 | 33.3% | LOW | Preliminary — not for maturity |
| Production Readiness (PRS) | 81.5895 | 33.3% | LOW | vetoed by hard gates if critical FAIL |

## Validator sensitivity (N2) & specificity (N3)

- **correct_detection_rate** (PRIMARY): 0.4
- **missed_critical_defects**: 3
- **specificity_rate** (clean control): 0.0
- **false_positive_count**: 1

## Hard gates

**Status: FAIL** | critical violations: ['HG-VALIDATOR-FALSE-POSITIVE', 'HG-VALIDATOR-MISSED-CRITICAL']

## Maturity (tiered, observed-only)

| Tier | Level | Max allowed | Constrained by |
|---|---|---|---|
| evaluator_engine | None | ROBUST | ['dogfood not yet run'] |
| target_verification_layer | FUNCTIONAL | ROBUST | ['mutation correct_detection<1.0', 'false_positive>0'] |
| target_orchestration | EXPERIMENTAL | FUNCTIONAL | ['1 observed phase run'] |
| target_agent_execution | EXPERIMENTAL | FUNCTIONAL | ['insufficient genuine agent runs'] |
| **overall_target_skill** | **EXPERIMENTAL** | **FUNCTIONAL** | ['insufficient genuine agent runs', 'overall capped at FUNCTIONAL per evidence'] |

## Final status: **FAIL**
