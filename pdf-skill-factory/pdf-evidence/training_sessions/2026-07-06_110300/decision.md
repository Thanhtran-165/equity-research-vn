# decision.md — IGWT 2026 training session

**Session**: `2026-07-06_110300`
**Skill**: pdf-evidence v0.1.0
**Input**: In-Gold-We-Trust-report-2026-Compact-Version-english.pdf
**Iterations used**: 2 of 3 (stopped early — primary failures fixed)

## Decision: `accepted` (with 1 deferred to human review)

### Rationale (against TRAIN SKILL PROMPT §15.1 stop-KPI)

All conditions for `decision = accepted` met:

| Condition | Status |
|-----------|--------|
| primary failure fixed | ✅ F-FORECAST-001 (0.40→0.95), F-TABLE-001 (0.80→0.92) |
| before/after metrics improved | ✅ see run_02_eval.json scorecard |
| no critical hallucination | ✅ count = 0 (before and after) |
| citation/evidence metrics pass threshold | ✅ citation_accuracy 0.92 ≥ 0.90; evidence_coverage 1.00 ≥ 0.90 |
| regression pass | ✅ 7/7 pytest + 5/5 DoD + 2 new regression cases |

### Final KPI Rule check (§16)

| KPI | Required | Actual |
|-----|----------|--------|
| session_completeness | 100% | ✅ all 10 mandatory session files present |
| critical_hallucination_count | 0 | ✅ 0 |
| citation_accuracy ≥ threshold | yes (or N/A w/ reason) | ✅ 0.92 ≥ 0.90 |
| primary_failure_metric improved | yes | ✅ forecast_period_disclosure +0.55, citation_accuracy +0.12 |
| regression_pass_rate = 100% (if exists) | yes | ✅ 100% |
| decision ∈ {accepted, needs_human_review} | yes | ✅ accepted (+1 deferred item) |

**Session status: PASS**

## Deferred item (separate from session decision)

**F-ABSTAIN-001**: partial abstention surfaced only as `warnings[]`, not as first-class JSON field. Requires output-schema extension (`partial_abstentions[]`). This touches the output contract → not minimal → **needs_human_review** (separately, not blocking this session).

## Version recommendation

**patch bump `0.1.0` → `0.1.1`** (reviewer self-approve per `08-VERSIONING_PLAN.md`):
- patch-level changes only (text rules + self-check items + workflow note)
- no new policy domain (financial policy EXTENDED, not added)
- no schema change, no code change, no dependency change
- regression green, DoD green

**Not yet applied to `metadata.version`** — bump is a separate explicit step per RUNBOOK Phase 9; this session produces the recommendation. Reviewer can apply by editing `SKILL.md` frontmatter `metadata.version: "0.1.1"` and re-running regression.

No minor/major bump requested. No human approval needed for patch bump.

## Stop early justification (§15.1 vs §15.2)

Stopped at iteration 2 (not 3) because §15.1 conditions met after first patch cycle. Running iteration 3 would risk over-fitting patches without new failure signal.

## Session artifacts

```
training_sessions/2026-07-06_110300/
├── input_manifest.json          ✅
├── run_01_output.md             ✅
├── run_01_eval.json             ✅
├── failure_analysis.md          ✅
├── proposed_patch.md            ✅
├── applied_patch.diff           ✅
├── run_02_output.md             ✅
├── run_02_eval.json             ✅
├── regression_result.json       ✅
├── decision.md                  ✅ (this file)
└── backup_pre_patch/            ✅ (SKILL.md, policies.md, parsers.md)
```

10/10 mandatory files present. session_completeness = 100%.
