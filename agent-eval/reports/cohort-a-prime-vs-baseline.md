# Cohort A′ vs Cohort A — Before/After Comparison (Phase-6 Patch)

Protocol v0.2.0 (`d10ea915`) vs baseline v0.1.0 (`bfb058d5`). Same benchmark (CTD), same source-pack (`5c5633d9`), same model (GLM-5.2), same scoring thresholds. Only change: phase6-dashboard.md patch + runner infrastructure (preflight/retry/streaming/max_tokens).

## Headline: Phase-6 output-type defect SOLVED

```yaml
phase6_patch_success:
  html_output_rate: 1.0     ✅  (was 0.0)
  narration_output_rate: 0.0 ✅  (was 1.0)
  invalid_output_blocked: true ✅ (preflight gate + retry working)
  critical_failures: 0      ✅
```

## Before/After comparison table

| KPI | Cohort A (baseline) | Cohort A′ (post-patch) | Change |
|---|---:|---:|---|
| **HTML output rate** | 0% | **100%** | ✅ fixed |
| **Narration rate** | 100% | **0%** | ✅ fixed |
| Phase-6 first-attempt success | N/A | 2/5 (40%) | new data |
| Phase-6 recovery rate | N/A | 3/5 (60%) | new data |
| Phase-6 unrecovered rate | N/A | 0/5 (0%) | new data |
| Final pass rate | 0% | 0% | unchanged (content quality, not output-type) |
| Mean recall | 39.3% | **66.4%** | **+27.1pp** ⬆️ |
| Minimum recall | 39.3% | 64.3% | +25.0pp |
| Maximum recall | 39.3% | 71.4% | +32.1pp |
| Recall σ | 0.0 | 2.85 | some variance introduced |
| Pipeline execution completion | 100% | 100% | unchanged |
| Autonomous successful completion | 0% | 0% | unchanged (still 0 PASS) |
| Premature completion claim rate | 0% | 0% | unchanged (honest) |
| HRS value | N/A (all-narration) | **88.18** | new |
| HRS evidence coverage | 83.3% | 83.3% | unchanged |

## Three separation axes (owner directive)

### 1. Output-type fix — ✅ SOLVED
```yaml
html_rate: 1.0      (was 0.0)
narration_rate: 0.0 (was 1.0)
```
The wrong-output-type defect is completely resolved. GLM-5.2 now emits structured HTML dashboards in 5/5 runs.

### 2. Content quality — improved but not complete
```yaml
verifier_recall: 66.4% (was 39.3%)  # +27.1pp
final_pass_rate: 0.0   (was 0.0)    # content REQs still fail
```
Recall nearly doubled but final verdict is still FAIL. **8 REQs still fail 5/5** — all content/data-accuracy: REQ-012 (charts/sections/refs counts), REQ-018 (≥10 refs), REQ-021 (deploy gate, correctly blocking), REQ-022-026 (data-accuracy: report values don't match ground-truth data files). These are **content-completeness** issues, not output-type.

### 3. Recovery behavior — working
```yaml
first_attempt_html_rate: 2/5 = 40%
recovered_after_retry_rate: 3/5 = 60%
unrecovered_rate: 0/5 = 0%
```
Phase-local preflight gate + bounded retry is functioning: 3 runs needed 1 retry (truncation → HTML), 2 runs succeeded first attempt, 0 runs failed after all attempts.

## REQ-level improvement (11 REQs improved, 8 still failing 5/5)

**Now passing 5/5 (were 0/5):** REQ-003 (split audit), REQ-006 (tech profile), REQ-008 (news), REQ-009 (canonical sections), REQ-014 (insights), REQ-015 (bull/bear), REQ-017 (honest flag), REQ-020 (div balance), REQ-028 (chart render-readiness) — these all required structured HTML, which the patch enabled.

**Still failing 5/5 (content/data):** REQ-012 (counts: charts/sections/refs below thresholds), REQ-018 (numbered refs <10), REQ-021 (deploy gate — correctly blocking), REQ-022-026 (data-accuracy: the agent fills sections but the numbers don't match the source-pack ground-truth data files).

## Phase-6 recovery detail (per run)

| Run | Attempts | Attempt classes | Recovered | Final |
|---|---:|---|---|---|
| A-001 | 2 | [OUTPUT_TRUNCATED, HTML] | ✅ | HTML |
| A-002 | 1 | [HTML] | — (first-try) | HTML |
| A-003 | 1 | [HTML] | — (first-try) | HTML |
| A-004 | 2 | [OUTPUT_TRUNCATED, HTML] | ✅ | HTML |
| A-005 | 2 | [OUTPUT_TRUNCATED, HTML] | ✅ | HTML |

Truncation on first attempt (3/5 runs) is the remaining output-budget edge — the model sometimes emits verbose CSS before reaching sections, hitting the streaming ceiling before completing. The preflight catches it and retry succeeds. This is a **known operational cost**, not a correctness issue.

## Operational metrics
```yaml
mean_duration: ~945s (vs baseline ~285s — 3.3× longer due to phase6 retries + streaming)
runs_needing_retry: 3/5
total_retries: 3
```

## Root-cause attribution (4-bucket)

| Bucket | Finding |
|---|---|
| Specification | **RESOLVED** — phase6 output contract now clear; inline template removes tool-channel dependency |
| Execution | improved (narration gone); remaining = content-filling quality (data-accuracy REQs) |
| Enforcement | **working perfectly** — preflight gate caught truncation 3/5, retry recovered all, deploy blocked 5/5 |
| Infrastructure | streaming + 32K budget works; truncation on verbose-CSS first-attempts is operational cost |

## Conclusion

The Phase-6 patch **successfully resolved the wrong-output-type defect**:
- html_output_rate: 0% → **100%**
- narration_rate: 100% → **0%**
- recall: 39.3% → **66.4%**
- preflight + recovery working (0 unrecovered)

Content quality (the remaining FAIL) is a **separate cycle**: the agent now emits structured HTML but doesn't fill data-accuracy REQs correctly (REQ-022-026: report numbers don't match source-pack ground truth). That's a content-filling/prompt-detail issue, not an output-type issue. Per owner directive: "nếu narration biến mất nhưng các REQ nội dung khác vẫn FAIL, nghĩa là bản vá đã giải quyết đúng output-type defect, và ta tiếp tục hardening chất lượng nội dung ở vòng kế tiếp."
