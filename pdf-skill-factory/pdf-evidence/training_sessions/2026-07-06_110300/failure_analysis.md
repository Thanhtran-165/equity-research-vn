# failure_analysis.md — IGWT 2026 training session

3 primary failures identified (run_01_eval.json). Each mapped to root cause, skill rule, and patch target.

---

## F-FORECAST-001 — Forecast-period not made explicit per claim

- **Observed output**: Answer presents USD 4,800 (2030 decade target), USD 6,900–20,800 (2045 model), USD 3,000–6,000 (12-month outlook). Only some bullets state the horizon.
- **Expected behavior**: Each forecast number must declare its **time horizon** + **type (forecast vs. target vs. probability range)** so reader cannot conflate them.
- **Root cause**: `references/policies.md#financial` says "phân biệt dữ liệu thực tế / dự báo / nhận định" but does NOT explicitly require stating the **time horizon** of each forecast. SKILL.md self-check list omits this dimension.
- **Skill rule violated**: `policies.md#financial` (incomplete — missing horizon-disclosure rule). Related to F13 in factory `06-FAILURE_MODES.md` ("biến nhận định thành sự thật").
- **Patch target**: `references/policies.md` (financial section) + `SKILL.md` self-check list.
- **Suggested fix**: Add rule "Each forecast number must declare: (a) type {actual | forecast | target | probability_range | scenario}, (b) time horizon {date or period}." Add self-check item "Forecast numbers: type + horizon declared?"
- **Should become regression test**: yes — covers F13 family with multi-horizon data.

---

## F-TABLE-001 — table_id never emitted for chart/table-page citations

- **Observed output**: Citations for p.11, p.20, p.28, p.47 cite `[file, page, section, quote]` (text-citation format) even though those pages contain charts/tables. The policy's table format `[file, page, table_id, row/col]` was never used. 42 tables in PDF → 0 `table_id`s emitted.
- **Expected behavior**: When a claim's evidence comes from a chart/table page, citation must include `table_id` (or chart_id) per `policies.md#citation` table format.
- **Root cause**: `policies.md#citation` DEFINES the table format but does not state a TRIGGER rule (when to switch from text format to table format). Workflow step 4 (`ExtractEvidence`) does not pass `table_id` from `extract.py` output to the citation.
- **Skill rule violated**: `policies.md#citation` (table branch) + `policies.md#table`.
- **Patch target**: `references/policies.md#citation` (add trigger rule) + `references/parsers.md` (force table_id propagation) + `SKILL.md` (workflow step 4 note).
- **Suggested fix**: Add to citation policy: "If the cited page has a detected table/chart AND the claim references a number/range from that visual, use the table format `[file, page, table_id, row/col]` or `[file, page, chart_id]`." Add to parsers.md: "extract.py MUST propagate `table_id` into the citation candidate."
- **Should become regression test**: yes — covers F04/F16 family (table handling).

---

## F-ABSTAIN-001 — Abstention not surfaced as first-class JSON field

- **Observed output**: Page 64 abstention appeared only as a `warnings[]` string ("Page 64 has no text layer..."). The output schema has `abstention_flag` and `abstention_reason` fields but they were not used for partial abstention (only for full-answer abstention).
- **Expected behavior**: Partial abstentions (some claims answerable, some not) must be reflected in `abstention_flag` semantics OR a new `partial_abstentions[]` field listing which sub-questions could not be answered.
- **Root cause**: `02-PDF_SKILL_SPEC.md` output schema defines `abstention_flag: bool` (binary) — insufficient for partial abstention. SKILL.md output schema inherits this limitation.
- **Skill rule violated**: `policies.md#abstention` (binary only).
- **Patch target**: `references/policies.md#abstention` + `SKILL.md` output schema note.
- **Suggested fix**: Extend abstention policy: "If some sub-questions are answerable but others are not, set `abstention_flag=false` for the answerable part AND populate `partial_abstentions: [{sub_question, reason}]`." This is a **schema extension** — flagged for human review (touches output contract).
- **Should become regression test**: yes (after schema extension approved).

---

## Secondary observations (not patch targets this session)

- **Spacing inconsistency in raw extraction** ("USD6,900" vs "USD 6,900"): cosmetic, not a rule violation. Skill picked canonical form. Defer.
- **Generic section headings** (p.28 "Executive Summaries"): correct per nearest-heading rule but unhelpful. Defer to a future "use chart title when available" rule — needs extract.py change, out of scope for minimal patch.

---

## Patch prioritization

| ID | Severity | Patch scope | Risk | Decision |
|----|----------|-------------|------|----------|
| F-FORECAST-001 | medium | policies.md + SKILL.md self-check (text only) | low | APPLY (minimal, text-only) |
| F-TABLE-001 | medium | policies.md + parsers.md + SKILL.md (text only) | low | APPLY (minimal, text-only) |
| F-ABSTAIN-001 | low-medium | policies.md + SKILL.md output schema (semantic extension) | medium — touches output contract | DEFER to needs_human_review (schema change) |

This session will apply F-FORECAST-001 and F-TABLE-001 (both minimal text-only patches, < 20% skill content). F-ABSTAIN-001 deferred to human review per TRAIN SKILL PROMPT §7.10 (touches output contract → not minimal).
