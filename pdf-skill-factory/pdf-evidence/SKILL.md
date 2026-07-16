---
name: pdf-evidence
description: Use when the user asks to read, answer questions about, extract tables from, summarize, quote, or compare PDF documents with verifiable source citations (page/section/quote). Triggers on phrases like "đọc PDF", "hỏi PDF", "trích bảng từ PDF", "so sánh PDF", "dẫn nguồn theo trang", "PDF QA with citations", "evidence from PDF", "quote from PDF". Refuses to fabricate; abstains when evidence is insufficient.
metadata:
  author: pdf-skill-factory
  version: "0.3.0"
  short-description: Evidence-first PDF QA with mandatory page citations.
---

# pdf-evidence — Evidence-first PDF QA

Skill giúp AI **đọc PDF và trả lời/dẫn/trích/so sánh dựa trên bằng chứng trong PDF**, dẫn nguồn chính xác `[file, page, section, quote]`, và **nói rõ khi không đủ bằng chứng** (abstain, không bịa).

> Đây là skill QA evidence-first, KHÔNG phải skill tạo/render PDF (đó là skill `pdf` riêng — không ghi đè).

## Nguyên tắc tuyệt đối

1. **EVIDENCE-FIRST.** Không trả lời trước khi có evidence.
2. **CITATION BẮT BUỘC.** Mỗi claim quan trọng có citation `[file_or_alias, page, section, quote]`. Bảng: `[file, page, table_id, row/col]`.
3. **ABSTAIN WHEN INSUFFICIENT.** Không thấy evidence → `"Insufficient evidence in the provided documents."` + `abstention_flag=true`. Abstain đúng là câu trả lời tốt.
4. **⚠️ NO OUTSIDE KNOWLEDGE BY DEFAULT.** Mặc định `pdf_only=true`: KHÔNG trộn kiến thức ngoài vào câu trả lời dựa trên PDF. Chỉ dùng kiến thức ngoài khi user **rõ ràng** cho phép → phải tách section "Ngoài tài liệu", set `outside_knowledge_used=true`.

## Input

JSON: `documents[]` (path + alias), `question` hoặc `task`, `output_format`, `constraint {pdf_only, language}`.

## Workflow (chi tiết `references/parsers.md` và spec `04-PDF_SKILL_WORKFLOW.md` ở factory)

1. **Intake** — validate documents/question/constraint.
2. **Classify** — mỗi PDF: digital_text | scanned | mixed | table_heavy | legal | financial | academic | policy | slide_export | low_quality_ocr. (script: `scripts/classify.py`)
3. **Route parser** — bảng routing ở `references/parsers.md`. Scan → **abstain + cảnh báo** v0.1 (OCR thật v0.5+).
4. **Extract evidence** — snippet + page + section + `table_id` (nếu claim từ bảng/chart). (script: `scripts/extract.py`)
5. **Sufficiency check** — đủ trả lời không? Không → abstain.
6. **Answer with citation** — mỗi claim kèm citation.
7. **Self-check** — `references/policies.md` các mục check + `references/failure_modes.md` 20 lỗi phải tránh.
8. **Format output** — text/json/table/summary/research_note.

## Output JSON schema

```json
{
  "answer": "...",
  "citations": [{"file": "...", "page": 7, "section": "...", "quote": "...", "table_id": null, "chart_id": null, "row": null, "col": null, "note": null}],
  "evidence": [{"page": 7, "snippet": "...", "table_id": null, "chart_id": null}],
  "confidence": 0.85,
  "abstention_flag": false,
  "abstention_reason": null,
  "partial_abstentions": [],
  "outside_knowledge_used": false,
  "warnings": []
}
```

`partial_abstentions[]` entry (when some sub-questions answerable, some not):
```json
{
  "claim_or_question_part": "...",
  "status": "not_enough_evidence",
  "reason": "...",
  "missing_evidence": "...",
  "suggested_next_document": "...",
  "confidence": 0.9
}
```

`abstention_flag=true` ONLY khi **toàn bộ** answer bị từ chối. `partial_abstentions[]` dùng khi **một phần** answer được, một phần không.

Cuối text answer kèm: `"Confidence: X | Outside knowledge: yes/no | Abstain: full/partial(N)/no | Warnings: N"`.

## Policies (chi tiết `references/policies.md`)

- **citation** — format bắt buộc `[file, page, section, quote]`; page không xác định → note rõ.
- **evidence** — mỗi claim quan trọng có nguồn; không suy đoán thay tài liệu.
- **abstention** — thiếu evidence → abstain; phân biệt confidence thấp vs. abstain.
- **⚠️ no-outside-knowledge (PATCH 6)** — mặc định `pdf_only=true`; tách section nếu user cho phép.
- **table** — đọc header trước; giữ đơn vị/kỳ/cột/dòng; cảnh báo nếu parse không chắc; kiểm dấu/đơn vị/% số tài chính.
- **ocr** — digital text → pdfplumber; scan → abstain + cảnh báo v0.1.
- **legal** — giữ điều/khoản/điểm; không diễn giải quá mức; phân biệt hiệu lực/ban hành/ap dụng; "thay đổi mới" → compare gốc vs sửa đổi.
- **financial** — giữ đơn vị/kỳ; phân biệt thực tế/dự báo/nhận định; không biến nhận định thành sự thật.
- **multi-pdf** — so sánh; tìm giống/khác; phát hiện sửa đổi; nêu xung đột.
- **vietnamese** — giữ cấu trúc điều khoản TV; phân biệt nghìn/triệu/tỷ; tên riêng giữ nguyên khi cite.

## Self-check trước emit

- Mỗi claim quan trọng có citation đầy đủ `[file, page, section, quote]`?
- Page trong citation ∈ evidence set?
- Quote tồn tại verbatim trong PDF?
- Có hallucination (claim không support)?
- Có trộn kiến thức ngoài (`pdf_only=true`)?
- Bảng: giữ header/đơn vị/kỳ? Claim từ bảng → dùng format `[file, page, table_id, row/col]`.
- Số tài chính: dấu/đơn vị/% đúng?
- Số dự báo: đã khai báo loại {actual/forecast/target/probability_range} + time horizon?
- Khi ≥ 2 forecast horizon trong 1 câu trả lời: đã gắn nhãn horizon từng số?
- Đủ evidence? Không → abstain.

> 30%+ claim fail self-check → `RefineAnswer` hoặc abstain.

## Giới hạn (nói rõ cho user)

- OCR scan thật chưa cài (v0.5+). PDF scan → cảnh báo + abstain nếu không có text layer.
- Bảng xoay/phức tạp: pdfplumber có thể miss → cảnh báo + `table_uncertainty_disclosure`.
- PDF pháp lý/tài chính VN phức tạp: verify thủ công.
- `faithfulness_simple` (heuristic trong `metrics.py`) chỉ là CI smoke; faithfulness thật dùng `groundedness_judge.md` (LLM-judge, chưa wire).

## Abstention — quyết định full vs partial (v0.2.0)

```
Câu hỏi có ≥ 2 sub-question không?
├── KHÔNG (monolithic)
│   └── evidence đủ?
│       ├── ĐỦ → answer + citation
│       └── THIẾU → abstention_flag=true (FULL abstain)
└── CÓ (multi-part)
    ├── sub-question CHÍNH (load-bearing) đủ evidence?
    │   ├── KHÔNG → abstention_flag=true (FULL abstain — không answer peripheral mà chôn core)
    │   └── CÓ → answer phần chính + mỗi peripheral thiếu → 1 entry partial_abstentions[]
    └── partial_abstentions[] MỖI entry phải có: claim_or_question_part, status="not_enough_evidence", reason, missing_evidence, confidence≥0.7
```

KHÔNG bao giờ chôn refusal trong `warnings[]`. Text output: section `⚠ Phần không đủ bằng chứng` sau answer.

## Tham chiếu

- `references/policies.md` ⭐ — 8 policy chi tiết.
- `references/parsers.md` — routing decision tree.
- `references/failure_modes.md` ⭐ — 20 lỗi thường gặp + fix.
- `scripts/classify.py` — heuristic classify.
- `scripts/extract.py` — pdfplumber wrapper.

## Train-on-Use (v0.3.0)

Skill có 3 chế độ (chi tiết `references/policies.md#train-on-use`):

- **RUN** (mặc định khi user yêu cầu xử lý file): xử lý task + trả lời user + self-check. Nếu phát hiện điểm đáng học (loại tài liệu mới, citation defect, bảng uncertain, OCR gap, novel pattern, user feedback), ghi `learning_candidates/open/LC-YYYY-NNN.json`. **RUN không bao giờ tự sửa skill** (không patch SKILL.md/policies/scripts/memory/version).
- **TRAIN** (khi user yêu cầu "train skill trên file này"): chạy TRAIN_SKILL_LOOP — failure analysis, patch proposal, apply nếu safe + KPI pass, regression, memory update, before/after.
- **RELEASE** (khi user yêu cầu release): full regression → quality gates → CHANGELOG → bump version nếu được phép → rollback nếu post-bump regression fail.

**Phân biệt quan trọng**: `learning_candidate` (tín hiệu thô từ RUN) ≠ `skill_memory` (lesson đã xác nhận qua TRAIN). RUN chỉ ghi candidate; chỉ TRAIN mới ghi memory.

Post-run self-evaluation checklist (RUN chạy nội bộ sau mỗi task):
- Có claim thiếu evidence? Có citation thiếu page/table_id/chart_id? Có phần nên abstain? Có bảng/số liệu parse không chắc? Có loại tài liệu mới? Có pattern nên thành regression?

Nếu tất cả ổn → không tạo candidate. Nếu có vấn đề → tạo candidate, KHÔNG sửa skill.

## Cải thiện skill

Loop tự cải thiện ở `ZCodeProject/pdf-skill-factory/`:
- `RUNBOOK.md` — quy trình agent vận hành.
- `06-FAILURE_MODES.md` — 20 lỗi + root cause + fix.
- `08-VERSIONING_PLAN.md` — version roadmap + human approval gate.

Khi gặp lỗi mới → RUN ghi learning_candidate → TRAIN chạy loop → RELEASE bump version (theo RUNBOOK).
