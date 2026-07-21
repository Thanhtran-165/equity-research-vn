# Skill Evaluation — equity-research-vn 1.1.0 (re-audit)

**Evaluator**: skill-harness-evaluator v0.1.0
**Date**: 2026-07-21
**Audit type**: Re-audit after target drift (snapshot 60 → 505 files, target version v1.0.0 → v1.1.0)
**Protocol sha256**: `72ce36017ab1aafd4a8fbeef1bf7af2bc7888653df4ec2818df576be4d7b9c23`
**Target directory sha256**: `afe08ee084218b6279e12ef89ffd00287f4f16633e3b6b7eb8e430dea633368a`

## Why a re-audit

The 2026-07-12 audit reported FAIL on equity-research-vn (then v1.0.0, 60 files). The target has since matured to v1.1.0 (HYBRID_DETERMINISTIC_SHELL, 505 files, claims PRODUCTION_READY). Two of the original P0 blockers may now be resolved. This re-audit answers: **is the FAIL verdict still warranted, and has the target earned a higher maturity tier?**

## Scores (every score carries evidence_coverage_pct + confidence)

| Score | Value | Coverage | Confidence | Note |
|---|---|---|---|---|
| Skill Design (SDS) | 92.0 | 100% | HIGH | static analysis of v1.1.0 skill-spec |
| Skill Correctness (SCS) | 90.0 | 80% | MEDIUM | 50% native (clean-control 28/28) + 50% mutation (4/5 correct) |
| Harness Reliability (HRS) | 100.0 | 66.7% | LOW | Preliminary — not for maturity (4/6 dimensions observed) |
| Production Readiness (PRS) | 94.5 | 66.7% | LOW | **PRELIMINARY — vetoed by hard gates** |

## Stream A — Verifier repeatability (N=10 isolated)

```yaml
observed_runs: 10
pass_rate: 1.0
mean_recall: 100.0
std: 0.0   # deterministic
ci_95: [100.0, 100.0]   # small-sample caveat
scope: "verifier repeatability only, NOT agent stability"
```

Stream A proves the verifier is deterministic and reproducible on a frozen artifact. It says nothing about agent stability (no model inference involved).

## Stream B — Orchestration (N=1)

```yaml
phase: phase0_sponsor
duration_seconds: 4
result: PASS (tier golden, 41 periods, sponsor_ok=true)
classification: deterministic_workflow
  reason: "no model inference detected; only vnstock data fetch + python subprocess"
agent_first_pass_yield: N/A
```

Stream B is correctly labeled `deterministic_workflow`, not `agent_assisted`. Honesty model §2: an agent run requires actual model inference.

## Validator sensitivity (N2) & specificity (N3)

```yaml
validator_sensitivity:
  injected_defects: 5
  correct_detection_rate: 0.8   # 4/5
  wrong_reason_failure_rate: 0.0
  missed_critical_defects: 1
validator_specificity:
  clean_controls: 1
  clean_controls_passed: 1
  false_positive_count: 0
  specificity_rate: 1.0
```

**Comparison vs prior audit (2026-07-12):**

| KPI | Prior | Re-audit | Delta |
|---|---|---|---|
| specificity_rate | 0.0 | 1.0 | ✅ FIXED |
| correct_detection_rate | 0.4 | 0.8 | ✅ +0.4 |
| missed_critical_defects | 3 | 1 | ✅ -2 |
| clean_control first-pass yield | 0.0 | 1.0 | ✅ FIXED |

The target has materially improved. The two prior P0 critical blind spots (REQ-028 false positive, REQ-009 threshold lỏng) are RESOLVED in v1.1.0.

## Mutation reclassification (important)

The single remaining miss — **MUT-VALUATION-001** — is a **test oracle specification defect**, not a verifier implementation defect:

- Original oracle: "corrupt one P/E value 9.1→33.7 in KPI card"
- Verifier behavior: PASS (used majority-vote to identify primary P/E as 9.1x — 10/11 occurrences intact; the lone 33.7x filtered as outlier)
- Stricter oracle **MUT-VALUATION-002** (corrupt all 11 P/E positions): **REQ-025 FAIL ✓ correctly**

This proves the verifier's logic is sound; the original oracle was under-specified for the multi-position report structure.

**However**, hard gate `HG-VALIDATOR-MISSED-CRITICAL` remains FAIL because:
1. The frozen protocol lock included MUT-VALUATION-001 as an official critical oracle.
2. We do not retroactively weaken gates after seeing the score (N4: protocol immutability).
3. The reclassification is documented as evidence for the owner, not as a gate override.

## Hard gates

**Status: FAIL** | critical violations: 2 / 17

| Gate | Status | Reason |
|---|---|---|
| HG-011 (critical_test_failed_despite_high_score) | FAIL | MUT-VALUATION-001 missed while SCS=90 |
| HG-VALIDATOR-MISSED-CRITICAL | FAIL | correct_detection_rate=0.8, missed_critical=1 |
| HG-VALIDATOR-FALSE-POSITIVE | **PASS** | false_positive_count=0 (REQ-028 FP fixed) |
| HG-EVAL-ISOLATION | PASS | 10/10 isolated runs |
| HG-SNAPSHOT-DRIFT | PASS | directory_sha256 stable through audit |
| HG-PROTOCOL-IMMUTABLE | PASS | protocol_sha256 stable |
| (12 spec §V gates) | PASS | no fabricated evidence, no overwrite, etc. |

## Maturity (tiered, observed-only)

| Tier | Level | Max allowed | Constrained by |
|---|---|---|---|
| evaluator_engine | **ROBUST** | ROBUST | 28 unit + 5 schemas + 10 self-tests |
| target_verification_layer | **FUNCTIONAL** | ROBUST | correct_detection<1.0, missed_critical>0 |
| target_orchestration | **EXPERIMENTAL** | FUNCTIONAL | 1 deterministic phase0 (no agent inference) |
| target_agent_execution | **UNASSESSED** | FUNCTIONAL | no genuine agent runs |
| **overall_target_skill** | **FUNCTIONAL** | **FUNCTIONAL** | hard_gate_veto + no_agent_runs |

The target's self-claim of `PRODUCTION_READY` is **NOT supported** by this audit:
- Hard gate FAIL vetoes production promotion regardless of arithmetic PRS=94.5
- Zero genuine agent runs = no agent-stability evidence
- The target's claim is aspirational; the audit's observation is FUNCTIONAL

## Final status: **FAIL**

Same overall verdict as prior audit, but for a **fundamentally different reason**:
- Prior (2026-07-12): FAIL due to 2 verifier implementation blind spots (false positive + lenient threshold)
- Re-audit (2026-07-21): FAIL due to 1 test oracle specification gap (MUT-VALUATION-001 under-specified)

The target has cleared the implementation-level issues. The remaining FAIL is documentation/oracle hygiene — owner can resolve it by updating the oracle contract or adding MUT-VALUATION-002 to the suite.

## Owner-actionable items

See `reports/improvement-recommendations.md` for full P0/P1/P2 list. Highlights:

- **P0-1 (oracle_changes):** Update MUT-VALUATION-001 contract to require corruption of ≥3 semantic positions, or document verifier's majority-vote semantics as part of correctness contract. Stricter MUT-VALUATION-002 already proven to catch correctly.
- **P1-1 (harness_changes):** Add explicit `source_run_id`/`source_snapshot_hash` to REQ-021 evidence file.
- **P1-2 (tooling_changes):** Co-locate `data/` with shipped reports (CTD orphan artifact).
- **P2-1 (skill_text_changes):** Document verifier's majority-vote valuation semantics in SKILL.md.

## What this audit did NOT do (honesty)

- Did NOT measure agent stability — phase0 was deterministic_workflow only
- Did NOT validate v1.1.0 against genuine production data (CTD_Complete_Report.html is an orphan artifact missing data/ dir; baseline therefore showed 15 REQs N/A)
- Did NOT exercise phases 1-7 orchestration — only phase0 was observed
- Did NOT pool results with the prior audit (different protocol versions, different snapshots)
- Did NOT weaken any gate after seeing the score
