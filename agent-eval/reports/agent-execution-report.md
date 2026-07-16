# Agent-Execution Evaluation — HONEST STATUS REPORT

**Protocol**: `bfb058d5…` (locked, immutable) | **Target**: equity-research-vn v3.0 / verification-layer 0.1.1 | **Runner**: `7458eeca…` (frozen after dry run)

## The blocker (stated plainly)

**Zero genuine agent runs were executed.** The instrumentation dry run (spec §IV) ran and proved the harness works — workspace isolation, phase loop, verifier invocation, run-result logging all function. But it returned `execution_type: NO_MODEL_BOUND` because **no model backend is available in this environment**:
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `ZAI_API_KEY`, `GLM_API_KEY`, `DEEPSEEK_API_KEY`: all unset
- `ollama` (local model runner): not installed
- The `openai` Python lib is installed but inert without a key

Per spec §I, genuine agent evidence cannot be substituted with verifier reruns, synthetic replay, or deterministic-workflow runs. The runner enforces this: it refuses to label any run `genuine_agent` unless all 8 phases had real model inference. I will **not** fabricate `genuine_agent` runs.

## What IS complete and verified (infrastructure layer)
- ✅ Protocol locked (`evaluation-protocol.lock.yaml`, sha256 `bfb058d5…`, immutability verified)
- ✅ Target snapshot frozen (merged-0.1.1: directory `33118b2f…`, verifier `985eb1a9…`, requirements `284ca2e5…`)
- ✅ Clean source pack built (21 raw-data files, sha256 `5c5633d9…`, NO answer report, NO pipeline `.py` builders — agent cannot cheat)
- ✅ Benchmark manifest (`BENCH-CTD-2026-07-12`, prohibited-reference list explicit)
- ✅ Instrumented runner built + dry-run-validated (`agent_runner.py`, sha256 `7458eeca…`)
- ✅ Dry run proved: fresh workspace, source-pack copy, task-state init, 8-phase loop, per-phase model-inference dispatch, verifier call, run-result logging, honest NO_MODEL_BOUND return
- ✅ Model-dispatch logic unit-checked (correctly True with key, False without)

## What is BLOCKED (cannot complete without a model backend)
- ❌ Cohort A (5 exact-repeat genuine agent runs) — 0/5 executed
- ❌ Cohort B (5 controlled-robustness runs) — 0/5 executed
- ❌ All §IX KPIs (First-Pass Yield, Autonomous Completion, Recovery, HRS, run-consistency) — denominator 0
- ❌ Completion-integrity, root-cause attribution, maturity classification — no genuine runs to analyze
- ❌ Decision to lift skill above EXPERIMENTAL — no agent evidence

## How to unblock (one command, once a key exists)
```bash
export OPENAI_API_KEY="sk-..."
cd /Users/bobo/ZCodeProject/agent-eval
# Cohort A
for i in 001 002 003 004 005; do
  python3 runner/agent_runner.py A-$i exact-repeat exact-repeat/run-$i source-pack CTD \
    --model-backend openai --model-id gpt-4o-mini \
    --protocol-sha256 bfb058d53bbd0a5da45b1c8139ea019b840812fdd969d39aece0fcab6ada1df1
done
# Cohort B (each with one perturbation)
python3 runner/agent_runner.py B-006 controlled-robustness controlled-robustness/run-006 source-pack CTD --perturbation source_order_shuffled --model-backend openai --model-id gpt-4o-mini --protocol-sha256 bfb058d5...
# ...run-007..010 with their perturbations
# Then: python3 runner/analyze_cohort.py reports/   (computes all §IX KPIs, HRS, maturity)
```
The runner, protocol, source pack, and benchmark are all frozen and ready. The ONLY missing input is a model API key (or a local model runner).

## 23-point report (honest — most fields N/A due to 0 genuine runs)

| # | Field | Value |
|---|---|---|
| 1 | Genuine agent runs | **0** (dry run = instrumentation only) |
| 2 | Model & config | none available (OPENAI/ZAI/etc keys unset; no local runner) |
| 3 | Protocol hash | `bfb058d53bbd0a5d…` (locked) |
| 4 | Skill + verifier hashes | dir `33118b2f…`, verifier `985eb1a9…`, reqs `284ca2e5…` |
| 5 | Benchmark source-pack hash | `5c5633d9fb9ca858…` (clean, no answer report) |
| 6 | Exact-repeat pass rate | N/A (0 runs) |
| 7 | Controlled-robustness pass rate | N/A (0 runs) |
| 8 | First-Pass Yield | N/A |
| 9 | Autonomous Completion Rate | N/A |
| 10 | Autonomous Recovery Rate | N/A |
| 11 | Premature Completion Claim Rate | N/A |
| 12 | Human Intervention Rate | N/A |
| 13 | Mean/min/std HRS | N/A (no observed dimensions) |
| 14 | HRS evidence coverage | 0% (no agent runs → Preliminary) |
| 15 | Critical failures | 0 (none possible — no runs) |
| 16 | Most-skipped requirement | N/A |
| 17 | Most-skipped phase | N/A |
| 18 | Root-cause distribution | N/A (no failures observed) |
| 19 | Operational cost | dry run: ~2s, 0 tool calls |
| 20 | Agent-execution maturity | **EXPERIMENTAL** (unchanged; 0 genuine runs cannot lift it) |
| 21 | Enough evidence to leave EXPERIMENTAL? | **NO** — needs ≥5 genuine runs |
| 22 | New verifier defects found? | none (verifier not exercised on agent output) |
| 23 | Next step | **Provide a model API key** → runner executes the frozen cohort → KPIs computed → maturity reassessed |

## Maturity (honest, observed-only)
```yaml
target_agent_execution:
  level: EXPERIMENTAL
  maximum_defensible: EXPERIMENTAL
  constrained_by: [zero genuine agent runs — NO_MODEL_BOUND]
  evidence: {genuine_runs: 0, dry_run_instrumentation_validated: true}
agent_testing_unlocked: true   # the verifier (0.1.1) is trusted enough; the blocker is infra, not trust
```

## What this cycle did NOT do (honest)
- Did not run any model. Did not claim any `genuine_agent` run. Did not compute HRS from zero. Did not lift maturity. Did not fabricate KPIs.
- The earlier verdicts (verifier 0.1.1 passing the 16-mutation suite, agent-testing *unlocked*) still stand — the unlock means the verifier is trusted enough to *begin* agent eval; it does not mean agent eval has occurred.
