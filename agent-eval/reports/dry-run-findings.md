# Dry-Run Findings — First Genuine-Agent Evidence (GLM-5.2, unscored)

**Run**: `dryrun-zai` | **scored**: false (instrumentation dry run per spec §IV) | **execution_type**: `genuine_agent` ✅ | **model**: GLM-5.2 via api.z.ai/api/anthropic | **duration**: 420s (7 min)

## What the dry run validated (instrumentation — PASS)
- ✅ GLM-5.2 invoked genuinely for all 9 phases (real inference, not fabricated)
- ✅ Fresh isolated workspace, source-pack copied, task-state initialized
- ✅ Phase events + per-phase latency captured (phase6 dashboard 119s, phase4b profile 102s — slowest)
- ✅ Artifact produced + verifier invoked + run-result logged
- ✅ Runner honesty contract held (refused NO_MODEL_BOUND before bridge; now genuine)

## What the dry run REVEALED (agent behavior — this is the real signal)
The agent (GLM-5.2) ran all phases but the **phase-6 output was narration, not the structured HTML dashboard**. Artifact begins `# Phase 6: Dashboard Build - CTD...` — the model *described* building the dashboard rather than emitting the 22-canonical-section `CTD_Complete_Report.html`. Consequently:

**Verifier verdict: FAIL | 42.9% recall (12 pass / 16 fail / 1 skip)**

### Passed (12) — model handled these well
REQ-001 (sponsor import), REQ-002 (≥20 periods), REQ-004 (real price data), REQ-007 (neutral tech-profile lang), REQ-008 (news sentiment), REQ-010 (no empty tokens), REQ-011 (canvas height-wrapper), REQ-013 (content depth), REQ-016 (valuation sanity), REQ-017 (honest limitation flag), REQ-019 (JS syntax), REQ-027 (external-claim flag)

### Failed (16) — concentration tells the story
- **REQ-009** (canonical sections missing 22/22 — agent didn't emit the template structure)
- **REQ-012** (charts <10, sections <20, refs <10)
- **REQ-014** (3 insight sections all 0 chars)
- **REQ-018** (0 numbered references)
- **REQ-020** (div imbalance 39 open / 38 close — it's prose, not structured HTML)
- **REQ-022/023/024/025/026** (data-accuracy — artifact has no DATA JS object to verify against)
- **REQ-005/006** (technical modes — not structured)
- **REQ-028** (chart render-readiness — no real charts)
- **REQ-021** (deploy gate FAIL, correctly blocked)

## Root-cause attribution (4-bucket, not "lazy model")
| Bucket | Sub-cause | Evidence |
|---|---|---|
| **Execution** | model_adherence_error | GLM narrated phase-6 instead of emitting the dashboard HTML the phase prompt asks for. The model treated the phase prompt as a task to describe, not a template to fill. |
| Specification | skill_design_error (contributing) | phase6-dashboard.md may not unambiguously demand raw-HTML emission; the prompt may read as "explain how to build" → invites narration. |
| Enforcement | — | verifier correctly FAILed (0.1.1 working as designed; caught the non-artifact) |
| Infrastructure | — | none (bridge worked; latency high but functional) |

**This is NOT "lazy model."** It's a real adherence/prompt-design interaction: the model produced *plausible prose about* the dashboard, not the dashboard. The harness caught it (verifier FAIL). Exactly the kind of finding the agent-eval was designed to surface.

## Instrumentation gap found + fixed
The runner's verifier step had a 120s timeout; on this 28KB narration artifact the verifier exceeded it during the pipeline (returned None). **Fixed: timeout 120s → 300s.** Verified: re-running the verifier in isolation returns verdict FAIL / 42.9% recall correctly. The dry run's recorded `None` was an instrumentation artifact, not the agent's real result.

## What this dry run does NOT establish (honest)
- It is ONE run, unscored. Not a cohort. Cannot compute run-consistency or HRS from it.
- The FAIL is on agent execution (adherence), NOT on the verifier — verifier 0.1.1 worked.
- Does not lift maturity above EXPERIMENTAL (needs ≥5 genuine scored runs).
- Per spec §IV: dry run must NOT be used to change rubric based on content quality. The rubric is unchanged.

## Implication for Cohort A/B (when run)
If phase-6 narration-instead-of-HTML is systematic across runs, Cohort A will show ~40-50% recall uniformly → that's a real model-adherence finding (the skill works structurally; GLM doesn't emit the artifact format). Either phase6-dashboard.md needs to demand raw HTML more forcefully (skill patch — separate cycle, not during cohort), OR this is genuine model behavior to report.

## Runner hash (updated after timeout fix)
- `agent_runner.py`: (recompute after edit)
- verifier timeout: 120s → 300s (only change)
