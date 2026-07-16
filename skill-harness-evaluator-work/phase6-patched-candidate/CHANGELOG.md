# CHANGELOG — phase6-patched-candidate (Phase-6 output-contract patch)

**NOT the original skill.** Separate candidate copy with Phase-6 two-layer patch. Original skill (verification-layer 0.1.1) untouched. Baseline `PRE_PHASE6_PATCH_COHORT_A` preserved.

## Root cause (from Cohort A evidence — 5/5 narration, recall 39.3% σ=0)
The phase6 prompt told the agent to `cp template` + `str.replace` tokens — but the subagent has **no tool/bash channel** in the runner's `invoke()` (single-message exchange). So GLM-5.2 narrated the steps ("I'll build the dashboard... Let me start by copying the template") instead of emitting the artifact. **This is a harness/runner limitation expressed as a prompt gap, NOT "lazy model."** Confirmed: artifact head = "I'll build the dashboard for CTD...", 0 canonical sections, mentions `cp`/`str.replace`.

## Layer 1 — output-contract prompt (`phases/phase6-dashboard.md` rewritten)
- **Absolute output contract:** only complete HTML (`<!DOCTYPE html>`→`</html>`), no narration, no markdown, no fences, no leading explanation.
- **Inline template:** the runner injects `dashboard_template.html` (~17K tokens, well within 1M context) into the prompt at `__TEMPLATE_INLINE_PLACEHOLDER__`, so the model fills tokens and returns complete HTML in one response — no tool channel needed.
- **Structured failure path:** if HTML impossible, return `PHASE6_STRUCTURED_FAILURE: <reason>` — never narration.
- Token-fill rules, content-depth table, keyword list, DATA keys preserved from original.

## Layer 2 — phase-local preflight gate (`runner/phase6_preflight.py` + wired in `agent_runner.py`)
Deterministic gate runs immediately after phase6 inference. Checks: starts with DOCTYPE/html, has `<section id="sec-">`, has `const DATA=`, has canvas/chart-wrap, no narration prefix (`I'll`/`Tôi sẽ`/`Step`/`Bước`/`##`), no markdown fence.
- **FAIL → retry phase6 (up to 2×) with specific error feedback** (no manual artifact edit).
- **Classification:** HTML | NARRATION | MALFORMED_HTML | EMPTY.
- This is the "tự sửa đúng nghĩa" mechanism — doesn't depend on model adherence.

## Verification (candidate tests)
- `test_phase6_preflight.py`: **7/7 pass** — narration (EN+VI) caught, fence caught, valid HTML passes, no false-positive on real PNJ report, empty caught, malformed caught.
- `test_analyze_cohort.py`: **17/17 pass** (metric-split fix: pipeline_execution vs autonomous_successful; run_consistency from Cohort A).

## Not labeled
- **NOT STABLE.** Candidate prompt + gate are unverified on real agent runs (needs Cohort A′ after merge).
- Verifier 0.1.1 unchanged — no new verifier defect evidence.

## Files changed (candidate)
| File | change |
|---|---|
| `phases/phase6-dashboard.md` | rewritten (Layer 1: output contract + inline-template marker) |
| `runner/agent_runner.py` | Layer 1 template injection + Layer 2 preflight gate + retry wired in (now `facf49e3`) |
| `runner/phase6_preflight.py` | NEW — deterministic preflight gate |
| `runner/test_phase6_preflight.py` | NEW — 7 gate tests |
| `runner/analyze_cohort.py` | metric-split fix (autonomous_successful vs pipeline_execution) |
| `scripts/independent_verifier.py` | UNCHANGED (0.1.1) |
| `requirements.yaml` | UNCHANGED |

## Pending (post owner-review + merge)
- Cohort A′ (5 exact-repeat genuine runs) on merged skill → before/after comparison (html_output_rate, narration_rate, recall, autonomous_successful_completion_rate).
- Verifier mutation suite re-run on merged (should still be 16/16 — verifier unchanged).
