# PDF Skill Factory

**AI-guided AI improvement for PDF understanding.**

Dự án này xây một **skill `pdf-evidence`** (evidence-first QA cho PDF) và một **factory** tối giản để skill đó tự cải thiện qua mỗi lần thất bại.

> ⚠️ Đây **không phải** app đọc PDF local, không phải RAG chatbot, không phải bản clone RAGFlow/Docling.
> Đây là **cơ chế để AI học cách xử lý PDF tốt hơn qua mỗi lần thất bại** — ở tầng instruction/policy/eval, không phải fine-tune model. Xem [`ASSUMPTIONS.md`](./ASSUMPTIONS.md).

## Sơ đồ đặt file

```
ZCodeProject/pdf-skill-factory/
│
├── ASSUMPTIONS.md                    # giả định + PATCH 7 (không fine-tune) — ĐỌC ĐẦU TIÊN
├── README.md                         # file này
├── DEFINITION_OF_DONE.md             # PATCH 1 — metric threshold cho mỗi version
├── RUNBOOK.md                        # PATCH 5 — quy trình agent vận hành loop
│
├── 01-REPO_LESSONS.md                # File 1 — bài học 20 repo
├── 02-PDF_SKILL_SPEC.md              # File 2 — đặc tả skill
├── 03-PDF_SKILL_SYSTEM_PROMPT.md     # File 3 — system prompt + PATCH 6 (no outside knowledge)
├── 04-PDF_SKILL_WORKFLOW.md          # File 4 — workflow input → output
├── 05-PDF_EVAL_PLAN.md               # File 5 — benchmark + metric
├── 06-FAILURE_MODES.md               # File 6 — 15+ lỗi + fix
├── 07-SKILL_MEMORY_SCHEMA.md         # File 7 — schema memory
├── 08-VERSIONING_PLAN.md             # File 8 — version roadmap + PATCH 8 (human approval gate)
├── 09-IMPLEMENTATION_PLAN.md         # File 9 — kế hoạch triển khai tối giản
├── 10-REVIEW_REPORT.md               # File 10 — tự review 5 câu hỏi
│
├── scaffolding/                      # code tối giản cho loop (KHÔNG phải app)
│   ├── eval_runner.py                # chạy eval trên fixture
│   ├── metrics.py                    # metric rule-based + LLM-judge (PATCH 3: faithfulness_simple = baseline)
│   ├── groundedness_judge.md         # PATCH 4 — JSON verdict supported/contradicted/not_enough_evidence
│   ├── modules/                      # 7 DSPy-style SIGNATURE (text spec, không cài dspy)
│   ├── memory/                       # skill_memory schema + ví dụ
│   ├── fixtures/                     # PATCH 2 — 5 case tối thiểu
│   │   ├── 01_text_qa/
│   │   ├── 02_no_answer_abstention/
│   │   ├── 03_table/
│   │   ├── 04_legal_mock/
│   │   └── 05_multipdf_comparison/
│   └── tests/
│       └── test_regression.py
│
└── pdf-evidence/                     # SKILL MỚI v0.1 (artifact chạy được)
    ├── SKILL.md                      # <500 dòng
    ├── CHANGELOG.md
    ├── references/
    │   ├── policies.md               # 8 policy + PATCH 6
    │   ├── failure_modes.md
    │   └── parsers.md
    ├── scripts/
    │   ├── classify.py
    │   └── extract.py
    └── agents/openai.yaml
```

## Cách dùng

### 1. Cài skill `pdf-evidence` vào ZCode

```bash
# Copy bản từ factory sang vị trí chạy của skill
cp -r ZCodeProject/pdf-skill-factory/pdf-evidence ~/.zcode/skills/pdf-evidence
```

Skill sẽ trigger khi user yêu cầu QA / trích / so sánh PDF với yêu cầu dẫn nguồn.

### 2. Chạy một vòng loop demo

Xem chi tiết từng bước ở [`RUNBOOK.md`](./RUNBOOK.md). Tóm tắt:

```bash
cd ZCodeProject/pdf-skill-factory

# Tạo PDF demo (chưa có sẵn)
python scaffolding/fixtures/build_fixtures.py

# Chạy eval trên 5 fixture
pytest scaffolding/tests/test_regression.py -v

# Hoặc chạy runner trực tiếp để xem báo cáo JSON
python scaffolding/eval_runner.py
```

### 3. Cải thiện skill khi có lỗi mới

Theo `RUNBOOK.md` mục "Vòng cải thiện":
1. chạy eval → đọc failure → map rule violated → đề xuất patch → sửa SKILL.md/references → re-run regression → nếu pass DoD → đề xuất bump version → **human approval gate** → bump.

## Khoảng cách với mục tiêu cuối

Dự án này deliver:
- ✅ v0.1 baseline (evidence + citation + abstention + table skeleton).
- ✅ Thiết kế đầy đủ cho v0.2–v1.0.
- ✅ Loop scaffolding chạy được trên 5 fixture demo.
- ⏳ v0.2+ (table, legal, financial, OCR thật, multi-PDF synthesis, GEPA) — roadmap.

## Tham khảo nhanh

| Muốn biết | Đọc |
|-----------|-----|
| Giả định & phạm vi | `ASSUMPTIONS.md` |
| Khi nào version đủ tốt để release | `DEFINITION_OF_DONE.md` |
| Agent vận hành loop thế nào | `RUNBOOK.md` |
| Skill làm gì, policy nào | `02-PDF_SKILL_SPEC.md` + `pdf-evidence/SKILL.md` |
| Bài học từ repo nào | `01-REPO_LESSONS.md` |
| Lỗi thường gặp | `06-FAILURE_MODES.md` + `pdf-evidence/references/failure_modes.md` |
