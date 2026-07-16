# File 4 — PDF_SKILL_WORKFLOW.md

> Workflow input → output theo pattern vn-* (N bước numbered).
> Skill `pdf-evidence` v0.1. Version rút gọn chạy được ở `pdf-evidence/SKILL.md`.

## Tổng quan

```
PDF(s) + question/task + constraint
        │
        ▼
[1] Intake & validate
        │
        ▼
[2] Classify each PDF
        │
        ▼
[3] Route parser theo loại
        │
        ▼
[4] Extract evidence (snippet + page + section)
        │
        ▼
[5] Sufficiency check ─── not enough ──► ABSTAIN
        │ enough
        ▼
[6] Answer with citation (draft)
        │
        ▼
[7] Self-check (DetectMissingEvidence + faithfulness + no-outside-knowledge)
        │
        ▼
[8] Format output (text/json/table/summary/research_note)
        │
        ▼
JSON schema + text answer
```

## Bước 1 — Intake & validate

**Input:** JSON theo `02-PDF_SKILL_SPEC.md` mục 4.
**Validate:**
- `documents[]` ≥ 1, mỗi path tồn tại.
- `question` hoặc `task` không rỗng.
- `output_format` hợp lệ.
- `constraint.pdf_only` (mặc định true).

**Nếu thiếu:** hỏi lại user, không tự đi tiếp.

## Bước 2 — Classify each PDF

Chạy `ClassifyPDF` (`pdf-evidence/scripts/classify.py` heuristic v0.1):
- Đếm ký tự/page → density thấp → nghi scan.
- Có text layer không?
- Có bảng không? (heuristic: nhiều dòng có ≥ 2 dấu cách/cột align).
- Keyword pháp lý ("Điều", "Khoản", "Nghị định", "Thông tư")?
- Keyword tài chính ("Doanh thu", "LNST", "BCTC", "VND", "%")?

Output `doc_type` ∈ {digital_text, scanned, mixed, table_heavy, legal, financial, academic, policy, slide_export, low_quality_ocr}.

## Bước 3 — Route parser

| doc_type | Parser v0.1 | Action |
|----------|-------------|--------|
| digital_text | pdfplumber | extract text + page |
| scanned | (no OCR v0.1) | **ABSTAIN** + cảnh báo "scan PDF cần OCR — chưa cài v0.1" |
| mixed | pdfplumber per-page | page không có text → cảnh báo |
| table_heavy | pdfplumber tables | extract + giữ header/units/period |
| legal | pdfplumber + structure detect | giữ điều/khoản/điểm |
| financial | pdfplumber + table | giữ units/period/sign |
| academic/policy/slide_export | pdfplumber | extract text, cảnh báo nếu layout phức tạp |
| low_quality_ocr | (abstain) | cảnh báo "low-quality — verify thủ công" |

## Bước 4 — Extract evidence

Chạy `ExtractEvidence`:
- Tìm snippet liên quan câu hỏi (keyword + section heading).
- Trích `{quote, page, section}` cho mỗi snippet.
- Với bảng → `ExtractTable` → `{headers, rows, units, period}`.
- Giữ **verbatim** quote (không paraphrase làm mất căn cứ cite).

## Bước 5 — Sufficiency check

Chạy `DetectMissingEvidence`:
- Evidence có trực tiếp trả lời câu hỏi không?
- Có cần thêm trang/section không?
- Có mâu thuẫn giữa các evidence không?

Nếu **không đủ**:
```json
{
  "abstention_flag": true,
  "abstention_reason": "Tài liệu chỉ nói doanh thu (p.7), không có nhân sự.",
  "answer": "Insufficient evidence in the provided documents."
}
```

## Bước 6 — Answer with citation (draft)

Chạy `AnswerWithCitation`:
- Viết câu trả lời từ evidence.
- **Mỗi claim quan trọng** gắn citation `[file, page, section, quote]`.
- Claim = số liệu, ngày, định nghĩa, điều khoản, so sánh, thay đổi.
- Claim = ý chung (vd "công ty tăng trưởng") → phải có số liệu support.

## Bước 7 — Self-check

| Check | Fail → |
|-------|--------|
| Mỗi claim có citation đầy đủ? | thêm citation hoặc bỏ claim |
| Page trong citation ∈ evidence set? | sửa page hoặc bỏ claim |
| Quote tồn tại verbatim trong PDF? | sửa quote hoặc bỏ claim |
| Có hallucination (claim không có support)? | bỏ claim hoặc abstain |
| Có trộn kiến thức ngoài (`pdf_only=true`)? | tách section "Ngoài tài liệu" hoặc bỏ |
| Bảng: header/units/period giữ? | sửa |
| Số tài chính: dấu/đơn vị/% đúng? | sửa |

Nếu > 30% claim fail self-check → `RefineAnswer` hoặc ABSTAIN.

## Bước 8 — Format output

Theo `output_format`:

- **text**: câu trả lời + inline citation `[file, p.X, section, "quote"]`.
- **json**: schema đầy đủ (`02-PDF_SKILL_SPEC.md` mục 5).
- **table**: markdown table + citation source line.
- **summary**: tóm tắt ngắn (≤ 200 từ) + citation đầu mỗi ý.
- **research_note**: research note format ( thesis + evidence bullets + citation + caveats).

## Multi-PDF variant (task=compare / detect_changes)

- Bước 1-5 cho mỗi PDF riêng.
- Bước 6': chạy `CompareDocuments`: list `differences[]`, `common[]`, `conflicts[]`.
- Mỗi difference có citation tới cả 2 PDF.
- Conflict → nêu rõ trong answer + `warnings[]`.

## Quy ước output cuối

Luôn kèm metadata line cuối (text format):
```
Confidence: 0.85 | Outside knowledge: no | Abstain: no | Warnings: 1 (table p.12 uncertain)
```

## Khi nào dừng và hỏi user

- PDF scan → hỏi "có OCR text sẵn không, hoặc cho phép dùng OCR tool ngoài?".
- Nhiều PDF mâu thuẫn → hỏi "ưu tiên PDF nào?".
- Câu hỏi mơ hồ → hỏi rõ.
- Constraint xung đột (pdf_only=false nhưng cũng "strict evidence") → hỏi rõ.
