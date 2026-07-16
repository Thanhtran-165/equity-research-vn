# File 9 — IMPLEMENTATION_PLAN.md

> Kế hoạch triển khai tối giản. Theo brief mục 3.6 + mục 9.
> Nguyên tắc: không build app nặng, không clone hệ thống lớn, ưu tiên spec + eval runner + prompt optimizer, parser = module phụ trợ.

## Triết lý triển khai

| Việc | Làm | Không làm |
|------|-----|-----------|
| Skill spec | ✅ đầy đủ 10 file | ❌ không chạy production |
| Skill `pdf-evidence` | ✅ SKILL.md + references + 2 script | ❌ không cài 20 parser |
| Eval | ✅ `eval_runner.py` + `metrics.py` + 5 fixture | ❌ không cài RAGAS/DeepEval nặng |
| Loop self-improve | ✅ scaffolding demo 1 vòng | ❌ không cài dspy/gepa v0.1 |
| Memory | ✅ JSON schema + ví dụ | ❌ không build DB |
| Versioning | ✅ SemVer + human approval gate | ❌ không CI/CD phức tạp |
| Parser | ✅ pdfplumber + pypdf (có sẵn) | ❌ không clone Docling/MinerU |

## Đã deliver (v0.1)

```
✅ 10 spec files                — thiết kế đầy đủ v0.1 → v1.0
✅ pdf-evidence/SKILL.md        — skill <500 dòng
✅ references/policies.md       — 8 policy + PATCH 6
✅ references/failure_modes.md  — 20 lỗi
✅ references/parsers.md        — routing decision tree
✅ scripts/classify.py          — heuristic digital/scan
✅ scripts/extract.py           — pdfplumber wrapper
✅ scaffolding/eval_runner.py   — mini eval harness
✅ scaffolding/metrics.py       — rule + LLM-judge baseline (PATCH 3)
✅ scaffolding/groundedness_judge.md — LLM-judge spec (PATCH 4)
✅ scaffolding/modules/*.md     — 7 DSPy-style SIGNATURE
✅ scaffolding/memory/          — schema + ví dụ
✅ scaffolding/fixtures/        — 5 case (PATCH 2)
✅ scaffolding/tests/           — pytest regression
✅ DEFINITION_OF_DONE.md        — threshold (PATCH 1)
✅ RUNBOOK.md                   — agent vận hành (PATCH 5)
✅ ASSUMPTIONS.md               — không fine-tune (PATCH 7)
```

## Cách chạy 1 vòng loop demo

```bash
cd /Users/bobo/ZCodeProject/pdf-skill-factory

# Bước 1: tạo 5 PDF demo (chưa có sẵn)
python scaffolding/fixtures/build_fixtures.py

# Bước 2: chạy regression
pytest scaffolding/tests/test_regression.py -v

# Bước 3: chạy eval runner xem báo cáo JSON
python scaffolding/eval_runner.py > scaffolding/results/latest_report.json

# Bước 4: (giả lập skill output) xem metrics
python -c "import json; print(json.dumps(json.load(open('scaffolding/results/latest_report.json')), indent=2, ensure_ascii=False))"
```

## Cải thiện skill (loop)

Khi có lỗi mới:

1. **Thêm fixture** ở `scaffolding/fixtures/NN_<name>/` với PDF + `case.json`.
2. **Chạy eval** → đọc failure.
3. **Map rule violated** ở `references/policies.md`.
4. **Đề xuất patch** theo `RUNBOOK.md` Phase 4.
5. **Sửa** SKILL.md / references / scripts.
6. **Re-run regression** cho đến khi xanh.
7. **Kiểm DoD** (`DEFINITION_OF_DONE.md`).
8. **Bump version** theo `08-VERSIONING_PLAN.md` (human approval nếu minor/major).
9. **Append** `skill_memory.json` + CHANGELOG.

## Phụ thuộc

| Phụ thuộc | Mục đích | Cài |
|-----------|----------|-----|
| `pdfplumber` | extract text + tables | `pip install pdfplumber` |
| `pypdf` | fallback read PDF | `pip install pypdf` |
| `reportlab` | sinh fixture PDF | `pip install reportlab` |
| `pytest` | regression | `pip install pytest` |

Không cài: dspy, gepa, textgrad, ragas, deepeval, docling, marker, mineru, paddleocr, surya, camelot, unstructured, ragflow.

## Roadmap cài dần

| Version | Cài thêm | Lý do |
|---------|----------|-------|
| v0.2 | `camelot` | table extraction nâng cao |
| v0.3 | — | chỉ sửa policy legal |
| v0.4 | — | chỉ sửa policy financial |
| v0.5 | `paddleocr` hoặc `surya` | OCR scan |
| v0.6 | — | multi-PDF synthesis (prompt-level) |
| v0.7 | `dspy` + `dspy.GEPA` | auto prompt-opt |
| v1.0 | full regression on real PDF corpus | stable |

## Khi nào KHÔNG dùng skill này

- User muốn **tạo/render PDF** → dùng skill `pdf` hiện có (không ghi đè).
- User muốn **OCR offline production** → cài PaddleOCR/Surya riêng.
- User muốn **chatbot RAG production** → dùng RAGFlow/LangChain riêng.
- User muốn **fine-tune model** → ngoài phạm vi (PATCH 7).

## Đo lường thành công

Skill `pdf-evidence` v0.1 thành công khi (theo brief mục 10):

1. ✅ đọc và phân loại PDF;
2. ✅ trả lời dựa trên evidence;
3. ✅ dẫn nguồn theo trang/bảng;
4. ✅ phát hiện khi không đủ bằng chứng;
5. ✅ xử lý bảng và số liệu cẩn trọng (skeleton);
6. ✅ so sánh nhiều PDF (skeleton);
7. ⏳ tự tạo eval case (roadmap v0.7 — `GenerateEvalCases`);
8. ✅ tự phát hiện lỗi (eval_runner);
9. ✅ tự đề xuất sửa instruction (RUNBOOK + patch proposal);
10. ✅ lưu lesson vào skill memory;
11. ✅ nâng version có changelog và điểm số (SemVer + human approval).

9/11 đạt ở v0.1; 2/11 roadmap (auto-eval, multi-PDF synthesis nâng cao).
