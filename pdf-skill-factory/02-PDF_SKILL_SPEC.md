# File 2 — PDF_SKILL_SPEC.md

> Đặc tả skill `pdf-evidence` v0.1. Đầy đủ 13 mục theo brief mục 3.2.
> File này là nguồn sự thật thiết kế. Implementation nằm ở `pdf-evidence/SKILL.md` + `references/`.

## 1. Mục tiêu skill

Skill `pdf-evidence` giúp AI **đọc PDF và trả lời/dẫn/trích/so sánh dựa trên bằng chứng trong PDF**, với:

- Mỗi claim quan trọng có nguồn cụ thể `[file, page, section, quote]`.
- Phát hiện và nói rõ khi không đủ bằng chứng (abstain, không bịa).
- Xử lý bảng, số liệu, văn bản pháp lý, báo cáo tài chính cẩn trọng.
- So sánh nhiều PDF, phát hiện thay đổi.
- Xuất theo nhiều định dạng (text, JSON, bảng, tóm tắt, research note).

## 2. Non-goals

- KHÔNG phục vụ tạo/render PDF (đó là skill `pdf` hiện có — không ghi đè).
- KHÔNG build RAG local hay chatbot production.
- KHÔNG fine-tune/train lại model (PATCH 7 — chỉ sửa instruction/policy/eval).
- KHÔNG chạy OCR thật v0.1 (chỉ policy routing, OCR thật ở v0.5+).
- KHÔNG tải PDF bản quyền làm benchmark.

## 3. Skill hierarchy (sub-skills)

| Sub-skill | Input | Output | Module spec |
|-----------|-------|--------|-------------|
| `ClassifyPDF` | doc (PDF path/list) | `doc_type` ∈ {digital_text, scanned, mixed, table_heavy, legal, financial, academic, policy, slide_export, low_quality_ocr} | `scaffolding/modules/ClassifyPDF.md` |
| `OCRDecision` | page | `needs_ocr: bool`, reason | mô tả trong `references/parsers.md` |
| `ExtractEvidence` | (question, doc) | `list[{quote, page, section}]` | `scaffolding/modules/ExtractEvidence.md` |
| `ExtractTable` | (page, table_id) | `{headers, rows, units, period}` | mô tả policy `references/policies.md#table` |
| `AnswerWithCitation` | (question, evidence) | `{answer, citations[], confidence}` | `scaffolding/modules/AnswerWithCitation.md` |
| `CompareDocuments` | (doc_a, doc_b, focus) | `{differences[], common[], conflicts[]}` | mô tả `references/policies.md#multi-pdf` |
| `DetectMissingEvidence` | (question, answer, doc) | `{missing, severity, abstain_recommended: bool}` | `scaffolding/modules/DetectMissingEvidence.md` |
| `RefineAnswer` | (answer, critique) | refined answer | `scaffolding/modules/RefineAnswer.md` |
| `GenerateEvalCases` | doc | eval examples | `scaffolding/modules/GenerateEvalCases.md` (roadmap) |
| `UpdateSkillInstruction` | (failures, current) | patch | `scaffolding/modules/UpdateSkillInstruction.md` (roadmap) |

## 4. Input schema

```json
{
  "documents": [{"path": "/abs/file.pdf", "alias": "report_2026"}],
  "question": "Doanh thu Q1/2026 bao nhiêu?",
  "task": "qa | extract_table | summarize | compare | detect_changes | quote_verbatim",
  "output_format": "text | json | table | summary | research_note",
  "constraint": {
    "pdf_only": true,
    "max_length": null,
    "language": "vi | en"
  }
}
```

Bắt buộc: `documents` ≥ 1, `question` hoặc `task`. `constraint.pdf_only=true` → không trộn kiến thức ngoài (PATCH 6).

## 5. Output schema

```json
{
  "answer": "Doanh thu Q1/2026 là 12.500 tỷ VNĐ.",
  "citations": [
    {"file": "report_2026", "page": 7, "section": "Tổng quan tài chính", "quote": "...12.500 tỷ đồng..."}
  ],
  "evidence": [
    {"page": 7, "snippet": "..."},
    {"page": 12, "snippet": "..."}
  ],
  "confidence": 0.85,
  "abstention_flag": false,
  "abstention_reason": null,
  "outside_knowledge_used": false,
  "warnings": ["Bảng p.12 parse không chắc — verify thủ công"]
}
```

- `abstention_flag=true` nếu không đủ evidence → `answer="Insufficient evidence in the provided documents."`.
- `outside_knowledge_used=true` chỉ khi user cho phép (PATCH 6) → phải tách section "Ngoài tài liệu".

## 6. Citation policy (xem `references/policies.md#citation`)

- Format: `[file_name_or_alias, page_number, section_heading, quote_or_evidence_snippet]`.
- Với bảng: `[file, page, table_id, row_or_col_reference]`.
- Nếu parser không trả page: `citation.note = "Không xác định được trang từ parser hiện tại."`.
- Mỗi claim quan trọng phải có ít nhất 1 citation.

## 7. Evidence-first policy (xem `references/policies.md#evidence`)

- Không trả lời trước khi có evidence.
- Mỗi claim quan trọng có nguồn.
- Không thấy trong PDF → nói rõ.
- Không suy đoán thay tài liệu.

## 8. Uncertainty / abstention policy (xem `references/policies.md#abstention`)

- Thiếu evidence → `abstention_flag=true`, `answer` = "Insufficient evidence".
- Phân biệt confidence thấp (có evidence mờ) vs. abstain (không có evidence).
- Abstain đúng được eval reward 1.0 (DEFINITION_OF_DONE.md).

## 9. ⚠️ PATCH 6 — No-outside-knowledge policy (xem `references/policies.md#no-outside-knowledge`)

- Mặc định `pdf_only=true`: KHÔNG trộn kiến thức ngoài vào câu trả lời dựa trên PDF.
- Chỉ dùng kiến thức ngoài khi user **rõ ràng** cho phép (`constraint.pdf_only=false`).
- Khi dùng: phải tách riêng section "Ngoài tài liệu" / "Outside the documents", KHÔNG hòa lẫn với nội dung PDF.
- `outside_knowledge_used` flag = true → reader biết phần nào cần verify.

## 10. Table policy (xem `references/policies.md#table`)

- Không tóm tắt bảng nếu chưa đọc header.
- Giữ đơn vị, kỳ thời gian, cột/dòng.
- Cảnh báo nếu bảng parse không chắc.
- Số tài chính: kiểm dấu âm/dương, nghìn/tỷ/triệu, %.

## 11. OCR policy (xem `references/policies.md#ocr`)

- Born-digital text → fast path (pdfplumber/pypdf).
- Scan/no-text-layer → phải route OCR (mô tả, chưa cài v0.1).
- Mixed → per-page decision.
- Low-quality OCR → cảnh báo, không kết luận chắc.

## 12. Legal-document policy (xem `references/policies.md#legal`)

- Giữ cấu trúc điều/khoản/điểm (Điều 1, Khoản 2, Điểm a).
- Không diễn giải quá mức khi user hỏi nguyên văn.
- "Thay đổi mới" → xác định gốc + văn bản sửa đổi, so sánh.
- Phân biệt hiệu lực / ngày ban hành / ngày áp dụng.
- Thiếu văn bản liên quan → nói thiếu.

## 13. Financial/Macro report policy (xem `references/policies.md#financial`)

- Giữ đơn vị, kỳ báo cáo.
- Phân biệt dữ liệu thực tế / dự báo / nhận định.
- Phân biệt bảng / biểu đồ / chú thích.
- Không biến nhận định tác giả thành sự thật khách quan.
- Số liệu → dẫn nguồn bảng/trang.

## 14. Multi-PDF policy (xem `references/policies.md#multi-pdf`)

- So sánh 2 văn bản, tìm giống/khác, phát hiện sửa đổi.
- Phát hiện điều khoản bị thay thế.
- Tổng hợp nhiều báo cáo, nêu xung đột.

## 15. Vietnamese document policy (xem `references/policies.md#vietnamese`)

- Giữ cấu trúc điều khoản tiếng Việt, không dịch gây mất nghĩa pháp lý.
- Số liệu tiếng Việt: phân biệt "nghìn/triệu/tỷ" vs "thousand/million/billion".
- Tên riêng, tên cơ quan, ngày tháng giữ nguyên tiếng Việt khi cite.
- Output ngôn ngữ theo `constraint.language`.

## 16. Failure policy

Khi skill fail (parse error, citation sai, hallucination):

- Không im lặng → emit `warnings[]`.
- Nếu lỗi nghiêm trọng → `abstention_flag=true`.
- Mỗi failure phải map được tới rule violated (`06-FAILURE_MODES.md`).
- Mỗi failure đã sửa → regression test permanent (`scaffolding/tests/`).

## 17. Tool contract (parser routing)

Xem `references/parsers.md`. Tóm tắt:

| Loại PDF | Parser (v0.1 cài) | Parser (mô tả, v0.5+) |
|----------|-------------------|----------------------|
| digital_text | pdfplumber, pypdf | PyMuPDF4LLM |
| scanned | (abstain + cảnh báo) | PaddleOCR, Surya |
| table_heavy | pdfplumber tables | Camelot, DeepDoc TSR |
| legal/financial | pdfplumber + giữ cấu trúc | Docling |

## 18. Quality gate

Skill v0.1 phải pass `DEFINITION_OF_DONE.md` threshold + regression 100% xanh + 8 ràng buộc chất lượng (ASSUMPTIONS.md mục "Ràng buộc chất lượng").
