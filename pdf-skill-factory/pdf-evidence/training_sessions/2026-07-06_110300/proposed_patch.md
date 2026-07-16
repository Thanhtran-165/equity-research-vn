# proposed_patch.md — IGWT 2026 training session

**Scope**: minimal, text-only, 2 patches (F-FORECAST-001 + F-TABLE-001).
**Files touched**: 3 (`references/policies.md`, `references/parsers.md`, `SKILL.md`).
**Estimated diff size**: < 5% of skill content. Well under the 20% needs-human-review threshold.
**F-ABSTAIN-001 deferred** (touches output contract → needs_human_review).

---

## Patch 1 — F-FORECAST-001 (forecast period disclosure)

### File: `pdf-evidence/references/policies.md` — section "8. Financial / macro report policy"

**OLD** (current, incomplete):
```
- PHÂN BIỆT:
  - **Dữ liệu thực tế** (đã ghi nhận).
  - **Dự báo** (tương lai, có giả định).
  - **Nhận định** (ý kiến tác giả).
- KHÔNG biến nhận định tác giả thành sự thật khách quan.
```

**NEW** (adds horizon + type disclosure):
```
- PHÂN BIỆT:
  - **Dữ liệu thực tế** (đã ghi nhận).
  - **Dự báo** (tương lai, có giả định).
  - **Mục tiêu** (target — do tác giả đặt, có thời hạn).
  - **Khoảng xác suất** (probability range / scenario distribution).
  - **Nhận định** (ý kiến tác giả).
- KHÔNG biến nhận định tác giả thành sự thật khách quan.
- **MỖI số dự báo phải khai báo**: (a) loại {actual | forecast | target | probability_range | scenario},
  (b) **time horizon** {ngày/kỳ/năm áp dụng}.
- Khi câu trả lời chứa ≥ 2 số dự báo với horizon khác nhau → tóm tắt bảng
  horizon-type hoặc gắn nhãn inline (vd "2030 decade target", "2045 model range",
  "12-month probability range") để reader không conflated.
```

**Reason**: run_01 answer mixed 2030/2045/12-month horizons without per-bullet labeling → reader-conflation risk (F13 family).

**Expected metric improvement**: `forecast_period_disclosure` 0.40 → 0.95 (custom metric); `hallucination_risk` stable or slightly down.

**Risk**: low. Pure text rule; no code change. Slight verbosity increase in answers.

**Test needed**: regression case with multi-horizon forecast data (F-FORECAST-001).

---

### File: `pdf-evidence/SKILL.md` — section "Self-check trước emit"

**OLD** (current self-check list):
```
- [ ] Bảng: giữ header/đơn vị/kỳ?
- [ ] Số tài chính: dấu/đơn vị/% đúng?
```

**NEW** (add 2 items):
```
- [ ] Bảng: giữ header/đơn vị/kỳ?
- [ ] Số tài chính: dấu/đơn vị/% đúng?
- [ ] Số dự báo: đã khai báo loại {actual/forecast/target/probability_range} + time horizon?
- [ ] Khi ≥ 2 forecast horizon trong 1 câu trả lời: đã gắn nhãn horizon từng số?
```

**Reason**: self-check list is the skill's last gate before emit; F-FORECAST-001 slipped through because no dimension checked horizon disclosure.

---

## Patch 2 — F-TABLE-001 (table_id trigger rule)

### File: `pdf-evidence/references/policies.md` — section "1. Citation policy"

**OLD** (current, defines table format but no trigger):
```
Với bảng:
\`\`\`
[file, page, table_id, row_or_column_reference]
\`\`\`
```

**NEW** (add trigger rule):
```
Với bảng:
\`\`\`
[file, page, table_id, row_or_column_reference]
\`\`\`

**Khi nào dùng format bảng** (trigger):
- Cited page có bảng/chart được parser detect VÀ
- Claim tham chiếu số liệu/range từ visual đó
→ PHẢI dùng format bảng với `table_id` (hoặc `chart_id` nếu là chart).
- Nếu visual parse không chắc → vẫn dùng format bảng + `note: "uncertain parse"`.
- KHÔNG dùng format text-citation cho claim bắt nguồn từ bảng/chart.
```

**Reason**: run_01 emitted 0 `table_id`s across 42 tables — policy defined the format but not WHEN to apply it.

**Expected metric improvement**: `table_handling` 0.40 → 0.80+; `citation_accuracy` (section-heading quality) 0.80 → 0.90+.

**Risk**: low. Pure policy text. May surface more `warnings[]` for uncertain parses (acceptable).

**Test needed**: regression case with chart/table-page citation (F-TABLE-001).

---

### File: `pdf-evidence/references/parsers.md` — section "Quy ước extract"

**OLD** (current, defines output but doesn't mention citation propagation):
```
Mọi extraction phải trả **page anchor** để citation có page:
[output JSON example]
```

**NEW** (add propagation rule):
```
Mọi extraction phải trả **page anchor** để citation có page:
[output JSON example unchanged]

**Bắt buộc**: khi extract.py detect bảng/chart trên page, `table_id` (t1, t2...)
phải được **truyền vào citation candidate** để AnswerWithCitation dùng format bảng.
extract.py không được "bỏ quên" table_id khi claim bắt nguồn từ bảng.
```

**Reason**: workflow gap — extract.py returns `table_id` in its output but the workflow does not propagate it into the citation; policy has no rule forcing propagation.

---

### File: `pdf-evidence/SKILL.md` — section "Workflow" step 4

**OLD** (current step 4):
```
4. **Extract evidence** — snippet + page + section. (script: `scripts/extract.py`)
```

**NEW** (add table_id propagation note):
```
4. **Extract evidence** — snippet + page + section + table_id (nếu claim từ bảng/chart).
   (script: `scripts/extract.py`)
```

---

## Patch summary

| # | Failure | File | Section | Lines added | Risk |
|---|---------|------|---------|-------------|------|
| 1a | F-FORECAST-001 | references/policies.md | §8 financial | +6 | low |
| 1b | F-FORECAST-001 | SKILL.md | self-check | +2 | low |
| 2a | F-TABLE-001 | references/policies.md | §1 citation | +6 | low |
| 2b | F-TABLE-001 | references/parsers.md | quy ước extract | +3 | low |
| 2c | F-TABLE-001 | SKILL.md | workflow step 4 | +1 (modify) | low |

Total: ~18 lines added/modified across 3 files. SKILL.md stays well under 500 lines.

**Traceability** (TRAIN SKILL PROMPT §7.10):
- failure_id: F-FORECAST-001, F-TABLE-001
- root_cause: policies incomplete (no horizon rule, no table-format trigger); workflow gap (table_id not propagated)
- file_changed: 3 files
- section_changed: 5 sections
- expected_metric_improvement: forecast_period_disclosure 0.40→0.95; table_handling 0.40→0.80; citation_accuracy 0.80→0.90
- risk: low (text-only, no code, no schema, no new dependency)
- test_or_regression_case: 2 new regression cases

**Decision**: APPLY (minimal, traceable, low-risk, no_scope_creep).
