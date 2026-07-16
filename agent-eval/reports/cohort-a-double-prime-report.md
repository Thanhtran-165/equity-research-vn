# Cohort A″ — Two-Layer Report (protocol v0.3.0, verifier 0.1.2)

## Layer 1: Raw cohort result (honest, unchanged)

```yaml
protocol: v0.3.0 (41ec0d6d)
verifier: 0.1.2 (merged)
genuine_runs_completed: 2/5 (run-003 timed out at phase6 — API ReadTimeout)
runs:
  A-001: genuine_agent, FAIL, recall 92.9%, HTML, 1714s
  A-002: genuine_agent, FAIL, recall 89.3%, HTML, 1439s
  A-003: PARTIAL_AGENT, verdict None (API timeout at phase6, no artifact)
cohort_status: INCOMPLETE (3/5 ran, 2 genuine, stopped early on infra failure)
narration: 0/2 genuine runs (0%)
HTML: 2/2 genuine runs (100%)
phase6_recovery: 2/2 (both recovered from truncation → HTML on attempt 2)
```

### Why incomplete (honest)
Run-003 hit a `ReadTimeout` during phase6 inference (the streaming connection to api.z.ai timed out after 1606s). This is an **infrastructure failure** (API/network), not an agent-skill failure. The orchestrator correctly stopped (stop condition: non-genuine execution type). Runs 4-5 did not execute.

### REQ-level (2 genuine runs)

| REQ | Run A-001 | Run A-002 | Pattern |
|---|---|---|---|
| REQ-005 (tech ACTIVE score) | FAIL (has_tech_score: false) | FAIL (has_tech_score: false) | **systematic** — agent doesn't emit the Tech Score format |
| REQ-007 (non-advice lang) | PASS | FAIL (output: 1, max: 0 — advisory word in tech-profile) | **variable** — run-002 has 1 non-advice word |
| REQ-021 (deploy gate) | FAIL | FAIL | **by design** (blocks while REQ-005 fails) |
| All other 25 REQs | PASS | PASS | ✅ |

### Key observations
- **REQ-004 false-positive did NOT recur** in genuine runs (it was dry-run-specific — the "oracle" word appeared in the dry run's content but not in these 2 runs' content). So the REQ-004 P2 fix may not be needed — the false positive is content-dependent, not systematic.
- **REQ-005 is the new systematic FAIL**: the agent fills sec-tech but doesn't emit the Tech Score format (`-?[0-9]\s*/\s*6` or `STRONG SELL/BUY/SELL/NEUTRAL`). The section has content (285-624 chars) but lacks the specific score pattern.
- **REQ-007 is variable**: run-002 has one advisory word in the tech-profile section (likely "bullish"/"bearish" slipping through).
- **Phase6 recovery works perfectly**: both genuine runs recovered from OUTPUT_TRUNCATED → HTML on attempt 2.

## Layer 2: Known-verifier-issue diagnosis

```yaml
known_verifier_issues:
  REQ-004:
    type: false_positive
    trigger: Vietnamese semantic use of "oracle" (meaning "chủ đầu tư then chốt")
    dependent_requirement: [REQ-021]
    affected_runs_in_this_cohort: 0/2  # did NOT recur
    status: NOT_BLOCKING_THIS_COHORT (but still a latent risk for other tickers)
  REQ-005:
    type: real_agent_gap (not verifier issue)
    description: agent fills tech section but doesn't emit Tech Score numeric format
    blocking: true (causes REQ-021 cascade)
```

## Three-layer comparison (A → A′ → A″)

| KPI | Cohort A | Cohort A′ | Cohort A″ (2 genuine) |
|---|---:|---:|---:|
| HTML output rate | 0% | 100% | 100% |
| Narration rate | 100% | 0% | 0% |
| Mean recall | 39.3% | 66.4% | **91.1%** |
| REQs passing | 11/28 | 19/28 | **~26/28** |
| Phase6 first-attempt success | N/A | 40% | 0% (both truncated → recovered) |
| Phase6 recovery rate | N/A | 60% | **100%** (2/2) |
| Data-accuracy (REQ-022-026) | 0% | 0% | **100%** (all PASS) |
| REQ-025 pass rate | 0% | 0% | **100%** |
| Final pass rate | 0% | 0% | 0% (REQ-005 blocks) |
| Autonomous successful completion | 0% | 0% | 0% |
| Critical failures | 0 | 0 | 0 |

## Root-cause attribution for remaining FAIL

| Bucket | Finding |
|---|---|
| Execution | REQ-005: agent doesn't emit Tech Score format (`-?[0-9]/6` + Verdict). The tech section has content but lacks the specific score pattern. **This is a content-completeness gap, not an output-type or data-accuracy issue.** |
| Specification | REQ-005's format requirement may need to be more explicit in the phase4a prompt (demand the exact Tech Score pattern). |
| Enforcement | REQ-021 correctly blocking deploy while REQ-005 fails. Working as designed. |
| Infrastructure | run-003 API timeout (not skill issue). |

## What this means
- **The content patch + P2 verifier fix are working**: data-accuracy 100%, REQ-025 100%, HTML 100%, narration 0%, recall 91.1%.
- **The remaining blocker is REQ-005 (Tech Score format)** — the agent fills the tech section but doesn't emit the specific `-?[0-9]/6` score pattern. This is a phase4a-prompt clarity issue, same class as the Phase-6 narration problem but in a different phase.
- **REQ-004 false positive did NOT recur** — it's content-dependent (only some agent outputs contain the Vietnamese word "oracle"). A P2 fix is still warranted for robustness but not blocking this cohort.

## Next steps (owner's call)
1. **REQ-005 patch** (phase4a-tech-active.md: demand explicit Tech Score format) → Cohort A‴ could reach the first PASS.
2. **Complete the cohort** (run 003-005) to get 5 genuine runs for statistical validity.
3. **REQ-004 P2 fix** (robustness, not urgent for this cohort).

The skill is now at **91.1% mean recall** — one phase-prompt clarity fix (Tech Score format) away from potentially the first autonomous successful completion.
