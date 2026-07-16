# 02 — TABLE_WIRING_PROPOSAL.md (v0.2.0)

> Proposal only. NOT applied. Targets `pdf-evidence v0.1.1 → v0.2.0`.
> Addresses: **TABLE-WIRING-001** (ExtractTable module not wired; `table_handling` 0.85 < 0.90).
> Goal: `table_handling: 0.85 → ≥ 0.90`.

## Mục tiêu

Wire module `ExtractTable` để:
- table_id/chart_id được tạo nhất quán khi parser detect visual.
- table_id truyền sang citation candidate → citation dùng đúng format bảng.
- structured cell data (headers, rows, units, period) chảy vào answer → `table_cell_accuracy` đo được.
- bảng parse không chắc → disclosure rõ, không bịa số liệu.

---

## 9 bắt buộc phân tích

### 1. ExtractTable hiện đang thiếu gì?

**Status in v0.1.1** (gap analysis):

| Capability | Present in v0.1.1? | Gap |
|------------|-------------------|-----|
| `extract.py` detects tables (pdfplumber `extract_tables()`) | ✅ | — |
| `extract.py` emits `table_id` (t1, t2...) per page | ✅ | — |
| `extract.py` emits `{headers, rows, units, period}` per table | 🟡 partial | `units`, `period` always `null` — no inference from header text |
| Citation trigger rule (when to use table format) | ✅ (added v0.1.1) | — |
| `table_id` propagated from extract.py → citation candidate | 🟡 policy says "must"; workflow does not enforce | no code path enforces it |
| Structured cell data flows into `answer` | ❌ | answer treats table-page citations as text quotes |
| `ExtractTable` as a named module with input/output contract | ❌ (only text spec in `scaffolding/modules/`) | not wired |
| Chart detection + `chart_id` | ❌ | charts (vs ruled tables) not distinguished |
| Uncertain-parse disclosure flag on table objects | ❌ | only generic `warnings[]` |
| `table_cell_accuracy` metric measurable | ❌ | N/A in eval_runner (no cells to compare) |

**Net gap**: policy + detection exist; **structured extraction + propagation + chart vs table distinction + uncertainty flag** are missing.

### 2. table_id được tạo ở đâu?

**In v0.1.1** (`scripts/extract.py`): `table_id` is generated per-page as `t{i}` where `i` is the 1-based index of the table on that page (e.g. page 7 with 2 tables → `t1`, `t2`, both with `page: 7`).

**Proposed v0.2.0**: keep the per-page `t{i}` scheme for tables. Add a parallel `c{i}` scheme for charts (see #4). Make `table_id`/`chart_id` **globally unique within a document** by prefixing with page: `p7.t1`, `p28.c1`. This avoids collision when aggregating across pages in multi-PDF comparisons.

Generation rule (proposed):
```
for each page p in doc:
    tables = detect_tables(p)        # pdfplumber
    charts = detect_charts(p)        # heuristic: image regions with no ruled grid (v0.2.0 heuristic; v0.3+ Surya)
    for i, t in enumerate(tables, 1):
        emit {table_id: f"p{p}.t{i}", page: p, headers, rows, units, period, parse_confidence}
    for i, c in enumerate(charts, 1):
        emit {chart_id: f"p{p}.c{i}", page: p, chart_type, title, parse_confidence}
```

### 3. table_id truyền sang citation như thế nào?

**Proposed propagation pipeline** (closes the v0.1.1 gap):

```
extract.py
   │ emits {tables: [{table_id, page, headers, rows, units, period, parse_confidence}], charts: [...]}
   ▼
ExtractEvidence module
   │ when a claim's evidence snippet is found on a page that has a table/chart:
   │   attach the relevant table_id/chart_id to the evidence record
   │   (evidence now carries {quote, page, section, table_id?, chart_id?})
   ▼
AnswerWithCitation module
   │ when building a citation:
   │   if evidence.table_id is set OR evidence.chart_id is set:
   │     use table/chart citation format [file, page, table_id|chart_id, row/col, evidence snippet]
   │   else:
   │     use text citation format [file, page, section, quote]
   │   if evidence.parse_confidence < 0.7:
   │     add note: "uncertain parse — verify"
   ▼
Output JSON citation
```

This makes the v0.1.1 policy rule ("when cited page has parser-detected table/chart AND claim references a number from that visual → use table format") **enforceable by code**, not just by prompt instruction.

### 4. Phân biệt table_id và chart_id ra sao?

| Visual type | Detection heuristic (v0.2.0) | id scheme | Why distinguish |
|-------------|------------------------------|-----------|-----------------|
| **Table** (ruled grid) | pdfplumber `extract_tables()` returns non-empty + cells form a regular grid | `p{N}.t{i}` | Cells can be extracted and cited by row/col |
| **Chart** (image-based visual: line, bar, pie, scatter) | Page has large image region AND no ruled grid covering it; optional v0.3+: Surya layout model classifies as "chart" | `p{N}.c{i}` | Cells cannot be reliably extracted; cite by chart title + approximate data point; always flag `parse_confidence` lower than table |

**Citation format difference**:
- Table: `[file, page, p7.t1, row 2 / col "Q1/2026", "12.500"]` — row/col reference is precise.
- Chart: `[file, page, p28.c1, "Gold Price 2045: Range", "~USD 6,900 lower bound"]` — value is approximate, prefixed with `~`, `parse_confidence` lower.

Charts always carry `table_uncertainty_disclosure = true` (see #5).

### 5. Khi nào dùng citation dạng text?

Use **text citation** `[file, page, section, quote]` when:
- The cited page has **no parser-detected table/chart**, OR
- The claim is a **prose statement** (not a number/range from a visual), even if the page happens to contain a table — e.g. "the report attributes the decline to central-bank selling" is a prose claim, cite it as text even if the same page has a table.

The trigger is **"claim sourced from the visual"**, not "page contains a visual".

### 6. Khi nào bắt buộc dùng citation dạng table/chart?

Use **table/chart citation** `[file, page, table_id|chart_id, row/col, snippet]` when:
- The cited page has a parser-detected table/chart, AND
- The claim references a **specific number/range/cell** that comes from that visual.

If unsure whether the number came from the visual or surrounding prose → default to table/chart format with `note: "uncertain source cell"` (safer; surfaces the ambiguity).

### 7. Cách xử lý bảng parse không chắc

When `parse_confidence < 0.7` (heuristic: pdfplumber returned a table but headers have nulls, or row count is implausible vs page char count, or Camelot stream-mode disagrees with lattice-mode):

- **MUST** set `table_uncertainty_disclosure = true` on the table object.
- **MUST** emit citation in table format BUT with `note: "uncertain parse — verify manually"`.
- **MUST NOT** present the table's numbers as certain in the answer — prefix with `~` or "approximately", or move the number to `warnings[]` + `partial_abstentions[]` if confidence is very low (< 0.4).
- **MUST** lower the answer's overall `confidence` field.

### 8. Cách giữ header, unit, period, row/column reference

| Element | How preserved | Fallback if missing |
|---------|---------------|---------------------|
| **Headers** | `extract.py` returns `t[0]` as headers; propagate verbatim | If header row has nulls → `parse_confidence` lowered; warning emitted |
| **Units** | Infer from header text via regex: `(tỷ|triệu|nghìn|VNĐ|USD|EUR|%|bn|trn|oz|tonnes|t)` → store in `units` field | If no unit in header → `units = null` + warning `"Bảng p.N mất header đơn vị — verify"` |
| **Period** | Infer from header text via regex: `(Q[1-4]/?\d{4}|FY\d{4}|\d{4}|tháng \d|Q[1-4])` → store in `period` field | If no period → `period = null` + warning |
| **Row/column reference** | Citation includes the row index + column header of the cited cell (e.g. `row 2 / col "Q1/2026"`) | If cell cannot be located precisely → use row label only + `note` |

This makes `unit_preservation_rate` and `table_header_preservation` measurable per-table, not just per-claim.

### 9. Cách tránh bịa số liệu từ bảng

Anti-hallucination rules when extracting from tables:
- **Never emit a number that is not in the extracted cells.** If the answer needs a number, it must come from a `rows[][]` cell, copied verbatim (including sign and decimal).
- **Normalize but do not transform**: `(12.500)` → `-12.500` is allowed (sign convention); `12.500` → `12500` is NOT (lost unit implication). Always pair with `units` field.
- **Never infer a cell** that pdfplumber returned as null. If a needed cell is null → abstain that sub-question (→ `partial_abstentions[]` per F-ABSTAIN-001 proposal), do NOT guess.
- **Round-trip check**: after building the answer, re-verify each numeric claim against the source cell. If mismatch → drop the claim or mark `note: "uncertain"`.
- **Sign check**: for financial tables, verify `(N)` ↔ `-N`, and verify the column the number came from (a common error: quoting the Q1/2025 column as Q1/2026).

---

## Citation format cho bảng/biểu đồ (proposed v0.2.0)

```
[file, page, table_id/chart_id, row/column reference, evidence snippet]
```

Examples:
- Table: `[igwt_2026, p.20, p20.t1, row "2025" / col "tonnes", "863"]`
- Chart: `[igwt_2026, p.28, p28.c1, "Gold Price 2045 Range", "~USD 6,900 lower bound"]`

## Nếu bảng không parse chắc

```
table_uncertainty_disclosure = true   # on the table object
note: "uncertain parse — verify manually"   # on the citation
```

If `parse_confidence < 0.4` → number moves to `partial_abstentions[]` (refused), not stated in answer.

---

## Expected metric improvement

| Metric | v0.1.1 | v0.2.0 target | Mechanism |
|--------|--------|---------------|-----------|
| `table_handling` | 0.85 | **≥ 0.90** | structured cells flow into answer; citation always carries table_id |
| `table_cell_accuracy` | N/A | **≥ 0.90** (when table parseable) | cells extracted verbatim; round-trip verified |
| `table_header_preservation` | implicit | **≥ 0.90** | headers propagated; warning if null |
| `table_unit_preservation` | implicit | **≥ 0.95** | units field inferred from header regex |
| `citation_accuracy` | 0.92 | **≥ 0.90** (maintained) | table/chart format enforced by code path |
| `hallucination_risk` | 0.02 | **≤ 0.05** (maintained) | anti-hallucination rules in #9 |

## Implementation note (NOT applied — for approval)

Wiring `ExtractTable` is a **code change** (new logic in `extract.py` or a new `scripts/extract_table.py`), not just a policy text change. It may use `pdfplumber` (already installed) for tables; chart detection in v0.2.0 is heuristic-only (no new dependency). `Camelot` is **not** required for v0.2.0 (deferred to v0.3+ if pdfplumber table extraction proves insufficient on real fixtures). **No heavy dependency added in v0.2.0.**
