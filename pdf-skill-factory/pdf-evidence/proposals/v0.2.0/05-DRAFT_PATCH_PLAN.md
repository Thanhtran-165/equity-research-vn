# 05 — DRAFT_PATCH_PLAN.md (v0.2.0)

> ⚠️ DRAFT ONLY. **NOT APPLIED.** No runtime file is modified by this plan.
> Implementation only after `06-HUMAN_APPROVAL_REQUEST.md` is signed APPROVED.
> All patches listed here will be applied together as the v0.2.0 release.

## Files dự kiến sửa (upon approval)

```
- pdf-evidence/SKILL.md                      (version bump + output schema note + self-check + workflow)
- pdf-evidence/references/policies.md        (abstention policy + table policy refinements)
- pdf-evidence/references/parsers.md         (ExtractTable wiring + chart detection)
- pdf-evidence/scripts/extract.py            (table_id/chart_id global scheme + units/period inference + parse_confidence)
- pdf-evidence/scripts/extract_table.py      (NEW — optional helper module, only if extract.py gets too large)
- pdf-evidence/tests/regression/             (NEW: 8 cases from eval plan groups A/B)
- scaffolding/memory/skill_memory.json       (close M-006 F-ABSTAIN-001, M-007 TABLE-WIRING-001)
- scaffolding/metrics.py                     (new metrics: partial_abstention_accuracy, abstention_visibility, table_header_preservation, table_unit_preservation, table_cell_accuracy)
- scaffolding/eval_runner.py                 (extend DoD table with v0.2.0 thresholds)
- scaffolding/tests/test_regression.py       (parametrize over 13 fixtures)
- scaffolding/fixtures/build_fixtures.py     (add 8 new fixture builders)
- pdf-evidence/CHANGELOG.md                  (v0.2.0 release entry, only upon release)
```

## Sections dự kiến sửa

```
- Output schema (add partial_abstentions[])
- Self-check (add 2 items: partial abstention visibility; table cell round-trip)
- Table citation policy (enforce code path, not just prompt)
- ExtractTable routing (units/period inference, chart vs table, parse_confidence)
- Abstention policy (partial vs full abstention decision tree)
```

---

## Patch entries (each: ID / failure / file / section / change / metric / risk / test / rollback)

### Patch P2.01 — Add `partial_abstentions[]` to output schema

```
Patch ID: P2.01
Failure addressed: F-ABSTAIN-001 (partial abstention buried in warnings[])
File: pdf-evidence/SKILL.md (output schema section) + pdf-evidence/references/policies.md (abstention section)
Section: Output JSON schema; §3 Abstention policy
Proposed change:
  - SKILL.md output schema: add "partial_abstentions": [] field with entry schema {claim_or_question_part, status, reason, missing_evidence, suggested_next_document, confidence}
  - policies.md §3: add decision tree "khi nào full abstain vs partial abstain" (see 01-ABSTENTION_SCHEMA_PROPOSAL.md #3, #4)
  - Clarify abstention_flag=true ONLY for whole-answer refusal
Expected metric improvement: abstention_quality 0.50 → ≥ 0.90 (new partial_abstention_accuracy metric); abstention_visibility = top_level
Risk: R1 (schema compat — additive, low), R3 (over-refusal — mitigated by missing_evidence + confidence gate), R4 (under-refusal — mitigated by abstention_visibility metric)
Test required: A.1, A.2, A.3, A.4 (group A in eval plan)
Rollback plan: revert SKILL.md + policies.md to v0.1.1 (backup in training_sessions/); partial_abstentions[] is additive so consumers ignore it after rollback
```

### Patch P2.02 — Wire ExtractTable module (table_id/chart_id + structured cells)

```
Patch ID: P2.02
Failure addressed: TABLE-WIRING-001 (ExtractTable not wired; table_handling 0.85 < 0.90)
File: pdf-evidence/scripts/extract.py + pdf-evidence/references/parsers.md + pdf-evidence/SKILL.md (workflow step 4)
Section: extract.py table output; parsers.md extract quy ước; SKILL.md workflow
Proposed change:
  - extract.py: change table_id scheme from per-page "t{i}" to global "p{N}.t{i}"; add chart detection (heuristic: image regions without ruled grid) emitting chart_id "p{N}.c{i}"
  - extract.py: infer units via regex from headers (tỷ|triệu|nghìn|VNĐ|USD|%|bn|trn|oz|tonnes|t); infer period via regex (Q[1-4]/?\d{4}|FY\d{4}|\d{4}); populate units + period fields (currently null)
  - extract.py: compute parse_confidence per table (heuristic: 1.0 if headers clean + row count plausible; 0.5 if null headers; 0.3 if merged cells detected)
  - extract.py: emit table_uncertainty_disclosure=true when parse_confidence < 0.7
  - parsers.md: document global table_id/chart_id scheme + units/period inference + parse_confidence rule
  - SKILL.md workflow step 4: note that evidence now carries table_id/chart_id + parse_confidence
Expected metric improvement: table_handling 0.85 → ≥ 0.90; table_cell_accuracy N/A → ≥ 0.90; table_header_preservation ≥ 0.90; table_unit_preservation ≥ 0.95
Risk: R5 (parse uncertainty — mitigated by disclosure + abstain on null cells), R6 (numeric hallucination — mitigated by row/col citation + round-trip check), R9 (dependency — pdfplumber only, no new dep)
Test required: B.1, B.2, B.3, B.4, B.5 (group B in eval plan)
Rollback plan: revert extract.py to v0.1.1 (backup in git/training_sessions); policies.md/parsers.md revert; no schema breakage
```

### Patch P2.03 — Citation enforcement (code path, not just prompt)

```
Patch ID: P2.03
Failure addressed: F-TABLE-001 (citation format enforcement was prompt-only in v0.1.1)
File: pdf-evidence/references/policies.md (§1 citation) + scaffolding/metrics.py
Section: citation policy trigger; metrics.citation_accuracy
Proposed change:
  - policies.md §1: keep v0.1.1 trigger rule, add note that extract.py now EMITS table_id/chart_id so the trigger is enforceable
  - metrics.py: citation_accuracy now checks table_id/chart_id presence when source page has a detected visual (rule-based, not LLM)
Expected metric improvement: citation_accuracy 0.92 → ≥ 0.95 on table-page citations
Risk: low (tightens existing rule)
Test required: B.1, B.4 (citation format on table/chart pages)
Rollback plan: revert policies.md + metrics.py to v0.1.1
```

### Patch P2.04 — Add v0.2.0 metrics to eval harness

```
Patch ID: P2.04
Failure addressed: enables measuring P2.01 + P2.02
File: scaffolding/metrics.py + scaffolding/eval_runner.py + scaffolding/tests/test_regression.py
Section: metrics module; DoD table; regression parametrization
Proposed change:
  - metrics.py: add functions partial_abstention_accuracy, abstention_visibility, table_header_preservation, table_unit_preservation, table_cell_accuracy
  - eval_runner.py: extend DOD table with v0.2.0 thresholds (partial_abstention_accuracy≥0.90, table_handling≥0.90, etc.); keep v0.1.1 thresholds as floor
  - test_regression.py: parametrize over 13 fixtures (5 existing + 8 new); add v0.2.0-specific assertions
Expected metric improvement: enables DoD gating on new metrics
Risk: R7 (regression — mitigated by full re-run before bump)
Test required: C.1, C.2, C.3, C.4 (regression group)
Rollback plan: revert metrics.py + eval_runner.py + test_regression.py to v0.1.1; existing fixtures still pass
```

### Patch P2.05 — Add 8 new fixtures

```
Patch ID: P2.05
Failure addressed: provides ground-truth for groups A/B
File: scaffolding/fixtures/build_fixtures.py + 8 new fixture dirs (06-13)
Section: build_fixtures.py — add 8 builders
Proposed change:
  - add build_06_partial_abstention_multi_part through build_13_uncertain_table (per 03-V0.2.0_EVAL_PLAN.md fixture plan)
  - each fixture: reportlab-generated PDF + case.json + baseline skill_output.json
Expected metric improvement: enables group A/B eval
Risk: low (synthetic fixtures; no copyrighted content)
Test required: each fixture has its own group A/B test
Rollback plan: delete the 8 new fixture dirs; revert build_fixtures.py to v0.1.1
```

### Patch P2.06 — Version bump + CHANGELOG (ONLY upon release)

```
Patch ID: P2.06
Failure addressed: release tagging
File: pdf-evidence/SKILL.md (metadata.version) + pdf-evidence/CHANGELOG.md
Section: frontmatter; release entry
Proposed change:
  - SKILL.md metadata.version: "0.1.1" → "0.2.0"
  - CHANGELOG.md: add "### 2026-07-XX — v0.2.0 — minor release" entry with before/after metrics, new capabilities, known limitations, deferred items
Expected metric improvement: N/A (tagging)
Risk: R7 (release gate — only applied after all P2.01-P2.05 tests green)
Test required: final full regression (groups A+B+C) must be 100% green
Rollback plan: revert metadata.version to "0.1.1"; mark CHANGELOG entry as "REVERTED"
```

### Patch P2.07 — Close memory items M-006, M-007

```
Patch ID: P2.07
Failure addressed: closes F-ABSTAIN-001 (M-006) and TABLE-WIRING-001 (M-007)
File: scaffolding/memory/skill_memory.json
Section: items M-006, M-007
Proposed change:
  - M-006: status_note "needs_human_review" → "resolved_in_v0.2.0"; metric_impact.after = measured value
  - M-007: status_note "accepted_known_gap" → "resolved_in_v0.2.0"; metric_impact.after = measured value
Expected metric improvement: N/A (memory hygiene)
Risk: low
Test required: P2.01 + P2.02 tests pass
Rollback plan: revert skill_memory.json to v0.1.1 (M-006/M-007 return to deferred/known-gap status)
```

---

## Sequencing (implementation phase, NOT now)

```
1. P2.05 (fixtures)      — provides ground-truth
2. P2.02 (extract.py)    — table/chart wiring
3. P2.01 (schema)        — partial_abstentions
4. P2.03 (citation)      — enforcement
5. P2.04 (metrics/eval)  — measuring
6. Run regression A+B+C  — gate
7. If green: P2.07 (memory close)
8. If green: P2.06 (version bump + CHANGELOG)
9. If any step fails: do NOT bump; revert that step; report
```

## Diff size estimate

- SKILL.md: +~15 lines (schema note + 2 self-check items + workflow note) → ~120 lines total (well under 500)
- policies.md: +~25 lines (abstention decision tree + table policy refinements) → ~190 lines
- parsers.md: +~15 lines (wiring details) → ~120 lines
- extract.py: +~60 lines (units/period inference, chart detection, parse_confidence, global id scheme) → ~180 lines
- metrics.py: +~50 lines (5 new metric functions)
- eval_runner.py: +~20 lines (DoD table extension)
- test_regression.py: +~10 lines (parametrize + new assertions)
- build_fixtures.py: +~150 lines (8 new builders)
- 8 new fixture dirs: ~8 × 3 files

Total: ~350 lines added/modified across runtime + scaffolding. SKILL.md stays well under 500.

## NOT in this plan (out of scope for v0.2.0)

- Camelot/Surya/paddleocr (heavy deps) — deferred to v0.3+
- LLM-judge wiring (`groundedness_judge.md`) — deferred to v0.2.x or v0.3
- New policy domains (OCR scan, multi-column reading order) — v0.5+
- Major version bump (v1.0) — not justified; v0.2.0 is minor

---

## Reminder

**This plan is NOT applied.** All changes are proposals pending human approval via `06-HUMAN_APPROVAL_REQUEST.md`. The runtime skill remains at v0.1.1.
