# HUMAN APPROVAL REQUEST — pdf-evidence v0.2.0

```
Current version: 0.1.1 (RELEASED, regression GREEN, rollback NOT required)
Proposed version: 0.2.0
Approval required: YES (minor bump — changes output contract + table workflow)
Patch applied so far: NONE (proposal-only mode)
```

## Proposed changes

1. **Add top-level `partial_abstentions[]` output schema** (F-ABSTAIN-001)
   - New additive JSON field for partial-abstention cases (some sub-questions answerable, some not).
   - Refusal no longer buried in `warnings[]`; first-class structured field.
   - Text output gains a `⚠ Phần không đủ bằng chứng` section (Vietnamese UX).
   - See `01-ABSTENTION_SCHEMA_PROPOSAL.md`.

2. **Wire ExtractTable module** (TABLE-WIRING-001)
   - `extract.py` emits global `table_id` (`pN.ti`) + `chart_id` (`pN.ci`).
   - Infer `units` + `period` from headers via regex; populate fields (currently null).
   - Compute `parse_confidence` per table; `table_uncertainty_disclosure=true` when < 0.7.
   - Citation code-path enforces table/chart format when source is a visual.
   - See `02-TABLE_WIRING_PROPOSAL.md`.

## Why this is a minor version (not patch, not major)

- **Output contract changes** (additive field) → not a patch.
- **Document/table workflow changes** (code path, not just prompt) → not a patch.
- **Backward-compatible** (existing fixtures' `skill_output.json` default `partial_abstentions=[]`; no field removed/renamed) → not major.
- **May affect downstream consumers** that use strict schema validation → they must whitelist `partial_abstentions` (documented in CHANGELOG + SemVer signal).
- **Requires new regression tests** (8 new fixtures across groups A/B).

## Expected KPI improvement

| Metric | v0.1.1 | v0.2.0 target | Notes |
|--------|--------|---------------|-------|
| `partial_abstention_accuracy` | N/A (new) | ≥ 0.90 | F-ABSTAIN-001 |
| `abstention_visibility` | warnings-buried (0.50) | top_level | F-ABSTAIN-001 |
| `abstention_quality` | 0.50 | ≥ 0.90 | F-ABSTAIN-001 |
| `table_handling` | 0.85 (< threshold) | **≥ 0.90** | TABLE-WIRING-001 — closes the gap |
| `table_cell_accuracy` | N/A | ≥ 0.90 (when parseable) | TABLE-WIRING-001 |
| `table_header_preservation` | implicit | ≥ 0.90 | TABLE-WIRING-001 |
| `table_unit_preservation` | implicit | ≥ 0.95 | TABLE-WIRING-001 |
| `citation_accuracy` | 0.92 | maintain ≥ 0.90 | no regression |
| `hallucination_risk` | 0.02 | maintain ≤ 0.05 | anti-hallucination rules |
| `forecast_period_disclosure` | 0.95 | maintain ≥ 0.90 | no regression of F-FORECAST-001 |
| `regression_pass_rate` | 1.00 | maintain 1.00 | 13 fixtures (5 old + 8 new) |
| `critical_hallucination_count` | 0 | maintain 0 | |

## Key risks (see `04-RISK_ASSESSMENT.md` for full register)

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|------------|------------|
| R3 | False abstention (over-refusal) | high | medium | `missing_evidence` + `confidence≥0.7` gate; A.1 anti-pattern test |
| R4 | Under-abstention (still buried) | high | medium | `abstention_visibility=top_level` metric; A.2 test |
| R5 | Table parse uncertainty → fabricated cells | high | medium | `parse_confidence` + disclosure + abstain on null; B.5 test |
| R6 | Numeric hallucination (wrong column) | high | medium | row/col citation + round-trip + sign check; B.2/B.3 tests |
| R7 | v0.1.1 regression | high | low | full A+B+C regression before bump; tolerance-enforced |

All high-severity risks have explicit regression tests in `03-V0.2.0_EVAL_PLAN.md`.

## What is NOT in v0.2.0 (scope boundaries)

- ❌ No heavy dependencies (Camelot/Surya/paddleocr) — pdfplumber only.
- ❌ No LLM-judge wiring (`groundedness_judge.md`) — deferred.
- ❌ No OCR scan support — deferred to v0.5+.
- ❌ No major version bump — v0.2.0 is minor.

## Implementation cost estimate

- ~350 lines added/modified across runtime + scaffolding.
- SKILL.md stays well under 500 lines (~120 estimated).
- 8 new fixtures (reportlab-generated, no copyrighted content).
- Sequencing: P2.05 → P2.02 → P2.01 → P2.03 → P2.04 → regression gate → P2.07 → P2.06 (see `05-DRAFT_PATCH_PLAN.md`).

## Approval options

```
[ ] APPROVE v0.2.0 implementation  — proceed with full plan (P2.01-P2.07)
[ ] APPROVE only F-ABSTAIN-001     — implement partial_abstentions[] only; defer TABLE-WIRING-001
[ ] APPROVE only TABLE-WIRING-001  — implement ExtractTable wiring only; defer F-ABSTAIN-001
[ ] REJECT for now                 — keep v0.1.1; close proposal without implementation
[ ] REQUEST REVISION               — proposal needs changes; specify below
```

## Human decision (to be filled by reviewer)

```
Decision:   ________________________________________________
Reviewer:   ________________________________________________
Date:       ________________________________________________
Notes:      ________________________________________________
            ________________________________________________
            ________________________________________________
```

---

## Reminder

**Do not implement v0.2.0 until this request is signed APPROVED.** The runtime skill remains at v0.1.1; all v0.2.0 content lives in `pdf-evidence/proposals/v0.2.0/` only.
