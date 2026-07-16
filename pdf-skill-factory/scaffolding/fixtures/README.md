# scaffolding/fixtures/

PATCH 2 — 5 fixture case tối thiểu cho pdf-evidence v0.1.

## Build

```bash
cd ZCodeProject/pdf-skill-factory
python scaffolding/fixtures/build_fixtures.py
```

Yêu cầu: `reportlab` (`pip install reportlab`). Script tạo PDF + case.json + skill_output.json (baseline) cho mỗi fixture.

## 5 fixture (PATCH 2)

| # | Tên | Loại test | Files |
|---|-----|-----------|-------|
| 01 | `01_text_qa` | text QA cơ bản (digital_text + financial) | source.pdf, case.json, skill_output.json |
| 02 | `02_no_answer_abstention` | không có đáp án → phải abstain | source.pdf, case.json, skill_output.json |
| 03 | `03_table` | bảng → extract + giữ header/units/period | source.pdf, case.json, skill_output.json |
| 04 | `04_legal_mock` | văn bản pháp lý → giữ điều/khoản/điểm + phân biệt hiệu lực | source.pdf, case.json, skill_output.json |
| 05 | `05_multipdf_comparison` | multi-PDF → so sánh gốc vs sửa đổi | source_a.pdf, source_b.pdf, case.json, skill_output.json |

## case.json schema

Xem `05-PDF_EVAL_PLAN.md`. Tóm tắt:

```json
{
  "id": "NN_name",
  "documents": [{"path": "source.pdf", "alias": "..."}],
  "question": "...",
  "task": "qa | extract_table | summarize | compare | detect_changes | quote_verbatim",
  "output_format": "text | json | table | summary | research_note",
  "constraint": {"pdf_only": true, "language": "vi"},
  "expected": {
    "answer_contains": ["..."],
    "answer_not_contains": ["..."],
    "abstention_expected": false,
    "expected_citations": [{"page": N, "section_keyword": "..."}],
    "expected_numbers": ["..."],
    "expected_clauses": ["..."],
    "expected_table": null | {"headers": [...], "rows": [...]},
    "required_points": 1,
    "answered_points": 1,
    "max_chars": null
  }
}
```

## skill_output.json — lưu ý quan trọng

`build_fixtures.py` sinh **baseline skill_output.json** đi kèm mỗi case để eval_runner có gì đánh giá. **Đây không phải output thật của skill pdf-evidence** — nó là mock realistic để demo loop.

Để chạy skill thật trên fixture:

1. Cài skill: `cp -r pdf-evidence ~/.zcode/skills/pdf-evidence`.
2. Mở ZCode session mới, gọi skill với input từ case.json.
3. Lưu output skill vào `skill_output.json` (thay file baseline).
4. Chạy `python scaffolding/eval_runner.py` để đánh giá.

## Thêm fixture mới

```
NN_<name>/
├── source.pdf       (hoặc source_a/b cho multi)
├── case.json
└── skill_output.json  (sinh bởi skill thật, hoặc baseline tạm)
```

Sau đó `eval_runner.py` tự nhận fixture mới (sort theo tên).

## Nguyên tắc fixture

- KHÔNG tải PDF bản quyền.
- Ưu tiên PDF text đơn giản (pdfplumber parse tin cậy).
- Phải có cả `abstention_expected=true` case (test refusal).
- Mỗi bug mới → thêm fixture kiểm chế độ đó.
