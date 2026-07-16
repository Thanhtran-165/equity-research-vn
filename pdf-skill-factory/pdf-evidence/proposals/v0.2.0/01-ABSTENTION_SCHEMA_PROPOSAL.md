# 01 — ABSTENTION_SCHEMA_PROPOSAL.md (v0.2.0)

> Proposal only. NOT applied. Targets `pdf-evidence v0.1.1 → v0.2.0`.
> Addresses: **F-ABSTAIN-001** (partial abstention buried in `warnings[]`).
> Status: needs_human_review (touches output contract → minor bump).

## Mục tiêu

Khi câu trả lời có phần đủ bằng chứng và phần không đủ bằng chứng, skill phải
thể hiện rõ ở **top-level output**, không chôn trong `warnings[]`.

## Đề xuất schema tối thiểu

Thêm field `partial_abstentions: []` vào output object (song song với `answer`,
`citations`, `warnings`):

```json
{
  "answer": "Doanh thu Q1/2026 là 12.500 tỷ VNĐ [abc_2026, p.2, ...].",
  "citations": [
    {"file": "abc_2026", "page": 2, "section": "Tổng quan", "quote": "..."}
  ],
  "evidence": [{"page": 2, "snippet": "..."}],
  "confidence": 0.85,
  "abstention_flag": false,
  "abstention_reason": null,
  "partial_abstentions": [
    {
      "claim_or_question_part": "đội ngũ nhân sự 2026",
      "status": "not_enough_evidence",
      "reason": "Tài liệu chỉ đề cập doanh thu (p.2), không có thông tin nhân sự.",
      "missing_evidence": "employee count / headcount for 2026",
      "suggested_next_document": "Báo cáo thường niên — phần<UserFlag warn> 'Đội ngũ nhân sự' hoặc phụ lục ESG.",
      "confidence": 0.95
    }
  ],
  "outside_knowledge_used": false,
  "warnings": ["Bảng p.12 parse không chắc — verify thủ công"]
}
```

### Field semantics

| Field | Type | When populated |
|-------|------|----------------|
| `abstention_flag` | bool | `true` ONLY when **whole answer** is refused (no answerable part). Unchanged from v0.1.1. |
| `abstention_reason` | string\|null | populated when `abstention_flag=true`; null otherwise. Unchanged. |
| `partial_abstentions` | array\|[] | populated when **some sub-questions answerable, some not**. Each entry = one refused sub-question. **NEW in v0.2.0.** |

`partial_abstentions[]` entry schema:
- `claim_or_question_part` (string, required) — the sub-question or claim that was refused.
- `status` (enum, required) — `not_enough_evidence` (only allowed value in v0.2.0; future: `contradictory_evidence`, `parser_uncertainty`).
- `reason` (string, required) — why refused, citing what WAS found and what was missing.
- `missing_evidence` (string, required) — concrete description of what evidence would unblock.
- `suggested_next_document` (string, optional) — hint on where to find it.
- `confidence` (float 0–1, required) — confidence in the refusal itself (high = definitely missing; low = maybe missed in parsing).

---

## 7 bắt buộc phân tích

### 1. Vì sao `warnings[]` không đủ?

`warnings[]` is a **grab-bag for parser/quality signals** (uncertain table parse, missing header, multi-column warning). It is **not semantically a refusal channel**:
- Consumers cannot programmatically distinguish "parser was uncertain about p.12" from "the document does not contain the answer to sub-question B" — both are strings in the same array.
- No structure: no `claim_or_question_part`, no `missing_evidence`, no `confidence`. A reader has to parse free text to know what was refused.
- Ordering is unspecified; abstention can be buried at index 7 of 39 warnings (as observed in IGWT 2026 run_01 — p.64 abstention was 1 of 39 warnings).
- Eval cannot grade it cleanly: `abstention_quality` was stuck at 0.50 in v0.1.1 precisely because the metric cannot reliably extract "what was refused" from `warnings[]`.

`partial_abstentions[]` is a **first-class, structured refusal channel** at top level — consumers and eval can read it directly.

### 2. Khi nào phải dùng `partial_abstentions[]`?

Use when ALL of these hold:
- The user's question has **≥ 2 distinguishable sub-questions** (explicit or implicit).
- **At least one** sub-question is answerable (has evidence) → `answer` is non-empty.
- **At least one** sub-question is NOT answerable (no evidence in the provided documents) → must be refused.

Each refused sub-question becomes one entry in `partial_abstentions[]`.

### 3. Khi nào phải abstain toàn bộ câu trả lời?

Set `abstention_flag=true` (and leave `answer="Insufficient evidence..."`, `partial_abstentions=[]`) when:
- The question is **monolithic** (single claim) and evidence is insufficient, OR
- **All** sub-questions are unanswerable, OR
- The single most important sub-question (the load-bearing one) is unanswerable — even if minor sub-questions are answerable, refusing the whole answer is safer than answering a peripheral part while burying the core refusal.

### 4. Khi nào chỉ abstain một phần?

Set `abstention_flag=false` AND populate `partial_abstentions[]` when:
- The question is genuinely multi-part, AND
- The **load-bearing** sub-question(s) ARE answerable, AND
- A **peripheral** sub-question is not.

Example: "Doanh thu Q1/2026 bao nhiêu, và công ty có bao nhiêu nhân viên?" — revenue is in the PDF (answerable, load-bearing), headcount is not (peripheral) → answer the revenue, list headcount in `partial_abstentions[]`.

### 5. Cách output tiếng Việt nên hiển thị cho user

For text-format output (not JSON), append a clearly delimited section after the answer:

```
Doanh thu Q1/2026 là 12.500 tỷ VNĐ [abc_2026, p.2, "Tổng quan", "..."].

---
⚠ Phần không đủ bằng chứng:
- Đội ngũ nhân sự 2026: tài liệu chỉ đề cập doanh thu (p.2), không có thông tin
  nhân sự. Cần thêm: Báo cáo thường niên — phần 'Đội ngũ nhân sự' hoặc phụ lục ESG.
---
Confidence: 0.85 | Outside knowledge: no | Abstain: partial (1 sub-question) | Warnings: 1
```

Vietnamese UX rules:
- Section title `"⚠ Phần không đủ bằng chứng"` (consistent, scannable).
- Each refusal = bullet, with the refused part **bolded**, then the reason, then `Cần thêm: ...`.
- Never bury refusal in a generic "Lưu ý" section.
- Metadata line updated: `Abstain: partial (N sub-question)` instead of just `yes/no`.

### 6. Tác động lên backward compatibility

| Aspect | Impact | Mitigation |
|--------|--------|------------|
| New field added to output JSON | **Additive** — existing consumers that ignore unknown fields are unaffected. Consumers that use strict schema validation must whitelist `partial_abstentions`. | Document in CHANGELOG; bump minor (0.1.x → 0.2.0) per SemVer to signal "new feature". |
| `abstention_flag` semantics unchanged | None — still binary full-answer abstention. | No change. |
| `warnings[]` content | Some abstention-flavored strings may **migrate** from `warnings[]` to `partial_abstentions[]`. Consumers reading `warnings[]` for refusal signals will see fewer of them. | Document migration; keep `warnings[]` for parser/quality signals only. |
| Text-format output | New `⚠ Phần không đủ bằng chứng` section appears when partial abstention exists. UI consumers may need to render it. | Additive; documented. |
| Eval harness | `eval_runner.py` + `metrics.py` must read `partial_abstentions[]` for `abstention_quality`. Old fixtures' `skill_output.json` lack the field → treat as `partial_abstentions=[]`. | Backward-compatible default; new fixture variants added. |

**Verdict**: backward-compatible at the JSON level (additive field). Text-output change is additive (new section only when partial abstention exists). Minor bump is appropriate, not major.

### 7. Test case cần có

Mapped to v0.2.0 eval plan group A (see `03-V0.2.0_EVAL_PLAN.md`):

| Test | Setup | Expected |
|------|-------|----------|
| A.1 Multi-part question, partial evidence | Question has 2 parts; part A in PDF, part B not | `answer` covers A; `partial_abstentions[]` has 1 entry for B |
| A.2 Question demanding conclusion beyond evidence | Question asks for forecast/conclusion; PDF only has raw data | `abstention_flag=true` OR `partial_abstentions[]` with the conclusion part refused |
| A.3 Legal question missing original/amending document | Compare task but only one of two documents provided | `partial_abstentions[]` flags the missing document |
| A.4 Financial question missing period or source | Question asks "Q3 number" but PDF only has Q1/Q2 | `partial_abstentions[]` flags missing period |

Metric gates:
- `partial_abstention_accuracy >= 0.90` (refusal appears in `partial_abstentions[]` when expected; does NOT appear when not expected).
- `abstention_visibility = top_level` (refusal is in `partial_abstentions[]`, NOT only in `warnings[]`).

Each test case becomes a regression case in `tests/regression/` upon approval.
