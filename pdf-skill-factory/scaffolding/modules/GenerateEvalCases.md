# Module spec — GenerateEvalCases (roadmap v0.7)

> DSPy-style SIGNATURE. Auto-sinh eval case từ PDF để mở rộng benchmark.

## Signature

```
GenerateEvalCases(
  doc: PDFDocument
) -> cases: list[EvalCase]
```

`EvalCase = {question, expected_answer_contains, abstention_expected, expected_citations, task, output_format}`

## Mô tả

Từ 1 PDF, sinh nhiều câu hỏi test đa dạng:
- answerable (có đáp án) + expected citation;
- unanswerable (thông tin không có trong PDF) → expected abstain;
- table extraction;
- quote verbatim;
- compare (nếu multi-PDF).

Mỗi case phải có ground-truth để metric chạy được.

## Pattern học từ

- Voyager (automatic curriculum): đề xuất task mới dựa state.
- Reflexion: từ failure cũ → sinh case kiểm chế độ đó.

## Metric

- `case_diversity` — cover ≥ 5 loại (qa, abstain, table, quote, compare).
- `case_validity` — 80%+ case có ground-truth thực sự đúng (verify bởi human hoặc LLM-judge).

## Roadmap

v0.1: không cài. v0.7+: cài dạng DSPy module, compile bằng GEPA với metric `case_validity`.

## Lưu ý

- KHÔNG sinh case mà không có ground-truth (vô dụng cho eval).
- KHÔNG sinh case quá dễ (over-estimate skill).
- Phải có ≥ 30% case abstain (test refusal).

## v0.7+ compile hint

```
class GenerateEvalCases(dspy.Module):
    def __init__(self):
        self.prog = dspy.ChainOfThought("doc_context -> cases: list")
```
