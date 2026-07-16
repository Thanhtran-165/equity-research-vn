# Module spec — AnswerWithCitation

> DSPy-style SIGNATURE. Core module — đây là module mà GEPA sẽ optimize mạnh nhất.

## Signature

```
AnswerWithCitation(
  question: str,
  evidence: list[EvidenceSnippet],
  constraint: {pdf_only: bool, language: str}
) -> answer_obj: AnswerObject
```

`AnswerObject = {answer: str, citations: list[Citation], confidence: float, abstention_flag: bool, abstention_reason: str|null, outside_knowledge_used: bool, warnings: list[str]}`

`Citation = {file: str, page: int|null, section: str, quote: str, note: str|null}`

## Mô tả

Sinh câu trả lời từ evidence, mỗi claim quan trọng gắn citation đầy đủ format. Nếu không đủ evidence → `abstention_flag=true`.

## Policy áp dụng (tất cả)

- `policies.md#citation` — format bắt buộc.
- `policies.md#evidence` — evidence-first.
- `policies.md#abstention` — abstain khi thiếu.
- **`policies.md#no-outside-knowledge` (PATCH 6)** — `pdf_only=true` default.
- `policies.md#table`, `#legal`, `#financial`, `#multi-pdf`, `#vietnamese`.

## Metric (chính)

- `citation_format_accuracy` ≥ 0.95
- `citation_page_accuracy` ≥ 0.90
- `abstention_accuracy` ≥ 0.90
- `faithfulness` (LLM-judge) ≥ 0.85
- `hallucination_rate` (LLM-judge) ≤ 0.10

## Example

Input: question + 2 evidence snippet.
Output:
```json
{
  "answer": "Doanh thu Q1/2026 là 12.500 tỷ VNĐ [report_2026, p.7, 'Tổng quan tài chính', 'doanh thu hợp nhất Q1/2026 đạt 12.500 tỷ đồng'].",
  "citations": [{"file": "report_2026", "page": 7, "section": "Tổng quan tài chính", "quote": "...", "note": null}],
  "confidence": 0.9,
  "abstention_flag": false,
  "abstention_reason": null,
  "outside_knowledge_used": false,
  "warnings": []
}
```

## Failure liên quan

F01, F02, F03, F19, **F20 (PATCH 6)**.

## v0.7+ compile hint

```
class AnswerWithCitation(dspy.Module):
    def __init__(self):
        self.prog = dspy.ChainOfThought("question, evidence, constraint -> answer_obj")
    def forward(self, question, evidence, constraint):
        return self.prog(question=question, evidence=evidence, constraint=constraint)
```

GEPA sẽ tối ưu instruction của module này dựa trên failure trace (vd "miss citation page" → evolve instruction).
