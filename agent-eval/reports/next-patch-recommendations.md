# Next-Patch Recommendations (agent-eval cycle)

## P0 — unblock agent evidence (infrastructure, not skill)
- **Provide a model backend.** Set `OPENAI_API_KEY` (or `ZAI_API_KEY`/`GLM_API_KEY`/`ANTHROPIC_API_KEY`) OR install a local runner (`ollama`). The frozen runner (`7458eeca…`) will then execute the 10-run cohort as-is. No skill/verifier/protocol change needed — all are frozen and ready.
- Once a key exists: run Cohort A (5 exact-repeat) → Cohort B (5 controlled-robustness) → `analyze_cohort.py` computes all §IX KPIs/HRS/maturity.

## P1 — runner hardening (after first genuine runs surface gaps)
- **`analyze_cohort.py`** — the aggregator that reads all run-result.json files and computes the §IX KPIs with bootstrap CI + exact binomial interval. Not yet written (writes only when there are runs to aggregate).
- **Per-phase evidence capture**: the runner currently writes the phase-6 HTML; phases 0–5 outputs need explicit capture (task-state.json updates are the existing channel). Verify each phase writes its slice.
- **Perturbation fixtures for Cohort B**: run-007 (one_noncritical_source_unavailable) and run-008 (tool_returns_empty_once_then_recovers) need hand-built fixtures so they're hard-mode, not impossible-mode. Pre-build these before Cohort B.

## P2 — verifier watch-items (carried from 0.1.1 release; still open)
- PATH B heuristic: add fallback-path mutations (adjacent years / same-window collisions).
- Additive-oracle consumer-path assertion (`validator_input_contains_mutation`).
- Stale task-state, cross-run contamination, partial-abstention mutation families.

## Verifier defects found THIS cycle
None — the verifier was not exercised on genuine agent output (0 runs). This question (#22 in the spec) genuinely cannot be answered until runs occur.

## Anti-deflation check
Do not interpret "0 runs" as "skill failed." The skill and verifier are unchanged and still pass the 16-mutation suite at 0.1.1. The blocker is purely that no model backend is available in THIS environment. The honest reading: **agent-execution maturity is EXPERIMENTAL *for lack of evidence*, not for evidence of failure.**
