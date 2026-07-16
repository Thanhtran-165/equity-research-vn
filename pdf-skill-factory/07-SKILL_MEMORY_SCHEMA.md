# File 7 — SKILL_MEMORY_SCHEMA.md

> Schema lưu memory/lesson cho skill `pdf-evidence`. Theo brief mục 6.
> Schema chính thức: `scaffolding/memory/skill_memory.schema.json`.

## Triết lý

Memory **không lưu mọi thứ**. Chỉ lưu:

- lỗi lặp lại (≥ 2 lần cùng pattern);
- quy tắc cải thiện có giá trị tái sử dụng;
- chiến lược đọc PDF đã chứng minh hiệu quả (đo bằng metric);
- test case quan trọng;
- citation/table/legal/numeric failure đã sửa.

KHÔNG lưu:
- one-off output;
- raw trace;
- thông tin nhạy cảm từ PDF user;
- prompt mới chưa eval.

## Schema (JSON Schema 2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "pdf-evidence skill memory",
  "type": "object",
  "required": ["version", "items"],
  "properties": {
    "version": {"type": "string", "description": "skill version khi memory entry được thêm"},
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "skill_name", "version", "failure_pattern", "successful_strategy", "instruction_patch", "test_case", "metric_impact", "created_at"],
        "properties": {
          "id": {"type": "string", "pattern": "^M-\\d{3}$"},
          "skill_name": {"type": "string", "enum": ["ClassifyPDF", "OCRDecision", "ExtractEvidence", "ExtractTable", "AnswerWithCitation", "CompareDocuments", "DetectMissingEvidence", "RefineAnswer", "pdf-evidence"]},
          "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
          "doc_type": {"type": ["string", "null"], "description": "loại PDF áp dụng, null nếu通用"},
          "failure_pattern": {"type": "string", "description": "mô tả lỗi lặp lại, ngắn gọn"},
          "failure_ids": {"type": "array", "items": {"type": "string"}, "description": "F-NN trong 06-FAILURE_MODES.md"},
          "successful_strategy": {"type": "string", "description": "chiến lược đã chứng minh hiệu quả"},
          "instruction_patch": {"type": "string", "description": "diff ngắn: old → new instruction"},
          "test_case": {"type": "string", "description": "fixture id hoặc test function name"},
          "metric_impact": {
            "type": "object",
            "properties": {
              "metric": {"type": "string"},
              "before": {"type": "number"},
              "after": {"type": "number"}
            }
          },
          "confidence": {"type": "number", "minimum": 0, "maximum": 1, "description": "độ tin cậy chiến lược"},
          "created_at": {"type": "string", "format": "date-time"}
        }
      }
    }
  }
}
```

## Ví dụ (3 item khởi tạo — xem `scaffolding/memory/skill_memory.json`)

```json
{
  "version": "0.1.0",
  "items": [
    {
      "id": "M-001",
      "skill_name": "AnswerWithCitation",
      "version": "0.1.0",
      "doc_type": "digital_text",
      "failure_pattern": "Citation thiếu page number khi parser trả text không kèm page metadata",
      "failure_ids": ["F01"],
      "successful_strategy": "extract.py bắt buộc trả {text, page}; skill verify page ∈ evidence trước khi emit citation",
      "instruction_patch": "Old: 'emit citation with file and quote' → New: 'emit citation [file, page, section, quote]; if page missing → abstain'",
      "test_case": "fixtures/01_text_qa",
      "metric_impact": {"metric": "citation_page_accuracy", "before": 0.6, "after": 1.0},
      "confidence": 0.9,
      "created_at": "2026-07-06T10:00:00Z"
    },
    {
      "id": "M-002",
      "skill_name": "DetectMissingEvidence",
      "version": "0.1.0",
      "doc_type": null,
      "failure_pattern": "Skill bịa câu trả lời khi evidence thiếu",
      "failure_ids": ["F02"],
      "successful_strategy": "Mandatory DetectMissingEvidence pass trước khi AnswerWithCitation; pdf_only=true default",
      "instruction_patch": "Old: 'answer if you can' → New: 'always run DetectMissingEvidence; if missing → abstention_flag=true'",
      "test_case": "fixtures/02_no_answer_abstention",
      "metric_impact": {"metric": "hallucination_rate", "before": 0.4, "after": 0.0},
      "confidence": 0.95,
      "created_at": "2026-07-06T10:00:00Z"
    },
    {
      "id": "M-003",
      "skill_name": "ExtractTable",
      "version": "0.1.0",
      "doc_type": "table_heavy",
      "failure_pattern": "Bỏ qua đơn vị/ kỳ khi extract bảng",
      "failure_ids": ["F11", "F12"],
      "successful_strategy": "ExtractTable bắt buộc emit {headers, rows, units, period}; warning nếu mất",
      "instruction_patch": "Old: 'extract table rows' → New: 'emit headers+units+period; if any missing → warning + lower confidence'",
      "test_case": "fixtures/03_table",
      "metric_impact": {"metric": "table_fidelity", "before": 0.5, "after": 0.9},
      "confidence": 0.85,
      "created_at": "2026-07-06T10:00:00Z"
    }
  ]
}
```

## Quy ước

- `id` tăng dần `M-001`, `M-002`... không reuse.
- Mỗi item phải có ≥ 1 `failure_ids` trỏ tới `06-FAILURE_MODES.md`.
- `metric_impact` bắt buộc — không có "cải thiện" không đo được (ràng buộc chất lượng #5, brief).
- `confidence` phản ánh độ tin cậy; dưới 0.5 → cần thêm eval.
- Memory **không thay thế** regression test — test vẫn phải tồn tại ở `scaffolding/tests/`.

## Khi nào prune

- Item có `confidence < 0.3` sau 3 version → flag review.
- Item conflict item mới → resolve, giữ item có metric tốt hơn.
- Không xóa item đã có regression test (lưu ngữ cảnh lịch sử).
