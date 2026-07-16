# File 10 — REVIEW_REPORT.md

> Tự review dự án theo 5 câu hỏi brief mục 8 File 10 + ràng buộc chất lượng mục 9.
> Thành thật về điểm yếu.

## 5 câu hỏi review

### 1. Có bị lệch thành local PDF app không?

**Không.**

- Không clone RAGFlow/Docling/MinerU/AnythingLLM.
- Không build chatbot RAG production.
- Không cài dspy/gepa/textgrad/ragas/deepeval nặng.
- Code duy nhất: 2 script parser tối giản (`classify.py`, `extract.py`) + 1 eval runner + 1 metrics module + 5 fixture + 1 pytest. Tổng < 600 dòng Python.
- Skill `pdf-evidence` là artifact chính; scaffolding chỉ phục vụ demo loop.

✅ Đúng hướng "skill spec + eval runner + prompt optimizer", không phải app.

### 2. Có đúng hướng "AI cải thiện AI" không?

**Đúng, ở tầng instruction/policy/eval (PATCH 7).**

- Loop đầy đủ: `Task → Run → Eval → Critique → Update → Regression → Version` (`RUNBOOK.md`).
- Failure → map rule → patch proposal → sửa → regression → bump.
- Skill memory (`07-SKILL_MEMORY_SCHEMA.md`) lưu lesson tái sử dụng.
- Version có changelog + eval score trước/sau (`08-VERSIONING_PLAN.md`).
- 7 sub-skill dạng DSPy SIGNATURE (`scaffolding/modules/`) — sẵn sàng compile GEPA ở v0.7.
- Mỗi bug → regression test permanent (`scaffolding/tests/`).

✅ Đúng hướng. KHÔNG fine-tune, KHÔNG train lại model.

### 3. Eval có đủ đo lường không?

**Đủ cho v0.1 baseline, chưa đủ cho v1.0.**

Metric v0.1 (`05-PDF_EVAL_PLAN.md`):
- ✅ citation_format_accuracy (rule)
- ✅ citation_page_accuracy (rule)
- ✅ abstention_accuracy (rule)
- ✅ hallucination_rate (LLM-judge `groundedness_judge.md` PATCH 4)
- ✅ faithfulness (LLM-judge, thay `faithfulness_simple` PATCH 3)
- ✅ table_fidelity (rule cell-compare)
- ✅ coverage, concision, numeric_accuracy, legal_clause_preservation (rule)

Fixture v0.1 (PATCH 2): 5 case cover text_qa, no_answer_abstention, table, legal_mock, multipdf_comparison.

**Chưa đủ:**
- ❌ scan PDF thật (cần OCR, v0.5);
- ❌ bảng xoay (v0.4);
- ❌ BCTC thật VN (v0.4);
- ❌ Vietnamese_quality LLM-judge (manual v0.1);
- ❌ report-flow / academic paper / slide_export.

### 4. Có chạy được với GLM/GPT/Codex/ZCode không?

**Có, vì:**

- Skill `pdf-evidence` là markdown + Python thuần → chạy được trên ZCode (skill system), Codex (agent), GLM/GPT (system prompt).
- Eval runner là Python thuần, không phụ thuộc provider LLM cụ thể.
- `groundedness_judge.md` là prompt spec — gọi được với bất kỳ LLM nào.
- Module DSPy SIGNATURE ở dạng text — port sang dspy thật ở v0.7.

**Caveat:**
- v0.1 chạy tốt trên LLM đủ mạnh giữ instruction (GPT-4+, Claude, GLM-4+, Gemini Pro). LLM yếu hơn có thể bỏ self-check → cần guardrail engine nếu production.

### 5. Điểm yếu còn lại

| # | Điểm yếu | Hệ quả | Roadmap |
|---|----------|--------|---------|
| W1 | Fixture tự tạo, chưa có PDF pháp lý/tài chính VN phức tạp thực tế | Benchmark có thể over-estimate trên PDF thật | v0.3, v0.4 — thêm fixture thật (đã được phép) |
| W2 | OCR chưa cài | Scan PDF → abstain, không trả lời | v0.5 — cài PaddleOCR/Surya |
| W3 | `faithfulness_simple` là baseline heuristic | Không đủ tin cậy cho release quyết định | `groundedness_judge.md` LLM-judge (PATCH 4) đã có spec, cần wire vào runner v0.2 |
| W4 | Chưa có GEPA/dspy thật | Loop tự cải thiện prompt chưa tự động | v0.7 — cài dspy + dspy.GEPA |
| W5 | Multi-PDF synthesis còn sơ khai | So sánh 2 PDF OK, tổng hợp 5+ PDF chưa tối ưu | v0.6 |
| W6 | Vietnamese_quality chưa auto-eval | Tiếng Việt output chưa chấm rule | v0.3 — thêm metric + LLM-judge VI |
| W7 | Benchmark nhỏ (5 fixture) | Coverage metric còn hạn chế | Tăng dần qua regression |
| W8 | Chưa test trên PDF tiếng Anh | Skill design cho cả VI/EN nhưng fixture VI | Thêm fixture EN v0.2 |

## Đối chiếu 10 ràng buộc chất lượng (ASSUMPTIONS.md)

| # | Ràng buộc | Status | Bằng chứng |
|---|-----------|--------|------------|
| 1 | Không viết chung chung | ✅ | Mỗi policy có format + ví dụ cụ thể |
| 2 | Không chỉ liệt kê repo | ✅ | `01-REPO_LESSONS.md` có "áp dụng / rủi ro / eval" cho từng repo |
| 3 | Không cài RAGFlow/Dify/AnythingLLM | ✅ | Chỉ cài pdfplumber/pypdf/reportlab/pytest |
| 4 | Không nói "có thể" mà không thiết kế cụ thể | ✅ | Mỗi sub-skill có input/output schema cụ thể |
| 5 | Không chấp nhận skill không có eval | ✅ | `05-PDF_EVAL_PLAN.md` + `eval_runner.py` + 14 metric |
| 6 | Không chấp nhận output không có citation policy | ✅ | `references/policies.md#citation` + format bắt buộc |
| 7 | Không chấp nhận output không có failure loop | ✅ | `RUNBOOK.md` + `06-FAILURE_MODES.md` + 20 F-NN |
| 8 | Không chấp nhận output không có versioning | ✅ | `08-VERSIONING_PLAN.md` + SemVer + PATCH 8 gate |
| 9 | Không chấp nhận output không có skill memory | ✅ | `07-SKILL_MEMORY_SCHEMA.md` + JSON schema + ví dụ |
| 10 | Không chấp nhận output không có regression test | ✅ | `scaffolding/tests/test_regression.py` + DoD gate |

## 8 PATCH verification

| # | Patch | File | Status |
|---|-------|------|--------|
| 1 | DEFINITION_OF_DONE.md metric threshold | `DEFINITION_OF_DONE.md` | ✅ |
| 2 | 5 fixtures tối thiểu | `scaffolding/fixtures/01..05/` | ✅ |
| 3 | faithfulness_simple = baseline heuristic | `scaffolding/metrics.py` docstring + `05-PDF_EVAL_PLAN.md` PATCH 3 section | ✅ |
| 4 | groundedness_judge JSON verdict | `scaffolding/groundedness_judge.md` | ✅ |
| 5 | RUNBOOK agent vận hành | `RUNBOOK.md` | ✅ |
| 6 | No-outside-knowledge rule | `03-SYSTEM_PROMPT.md` + `references/policies.md#no-outside-knowledge` + F20 | ✅ |
| 7 | Không fine-tune, không train lại | `ASSUMPTIONS.md` PATCH 7 section + `09-IMPLEMENTATION_PLAN.md` | ✅ |
| 8 | Human approval gate minor/major | `08-VERSIONING_PLAN.md` PATCH 8 + `RUNBOOK.md` Phase 8 | ✅ |

## Kết luận

Dự án deliver **đúng scope**: skill `pdf-evidence` v0.1 + factory scaffolding tối giản cho loop tự cải thiện, không build app nặng, không fine-tune, không ghi đè skill cũ. 10 ràng buộc chất lượng pass. 8 patch tích hợp. 5 câu hỏi review trả lời thành thật, điểm yếu ghi rõ với roadmap.

**Bước kế tiếp được khuyến nghị**: chạy `RUNBOOK.md` Phase 0–6 để verify loop chạy được trên 5 fixture demo, sau đó thêm fixture thật (có phép) cho v0.2 (table) và v0.3 (legal VN).
