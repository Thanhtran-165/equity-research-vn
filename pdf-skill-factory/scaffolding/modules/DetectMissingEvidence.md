# Module spec — DetectMissingEvidence

> DSPy-style SIGNATURE. Bắt buộc chạy trước `AnswerWithCitation`.

## Signature

```
DetectMissingEvidence(
  question: str,
  evidence: list[EvidenceSnippet],
  doc: PDFDocument
) -> report: {missing: list[str], severity: "low"|"medium"|"high", abstain_recommended: bool, reason: str}
```

## Mô tả

Kiểm tra evidence có đủ trả lời câu hỏi không. Nếu thiếu → đề xuất abstain. Đây là guardrail chống F02 (hallucination).

## Logic

- Tách câu hỏi thành các sub-question (số liệu? ngày? điều khoản? so sánh?).
- Mỗi sub-question → check evidence có snippet trả lời không.
- Nếu ≥ 1 sub-question không có evidence → `missing[]` populated.
- `severity = high` nếu (> 50% sub-question missing) → `abstain_recommended = true`.

## Policy áp dụng

- `policies.md#abstention`
- `policies.md#evidence`

## Metric

- `abstention_accuracy` (rule): abstain behavior matches expected.
- `hallucination_rate` (LLM-judge): module này giảm hallucination bằng cách bắt buộc abstain.

## Example

Input: question "đội ngũ nhân sự 2026?" + evidence chỉ có doanh thu (p.7).
Output:
```json
{
  "missing": ["nhân sự / employee count"],
  "severity": "high",
  "abstain_recommended": true,
  "reason": "Tài liệu chỉ đề cập doanh thu (p.7), không có thông tin nhân sự."
}
```

→ `AnswerWithCitation` skip, emit `abstention_flag=true`.

## Failure liên quan

F02 (hallucination thay vì abstain).

## v0.7+ compile hint

```
class DetectMissingEvidence(dspy.Module):
    def __init__(self):
        self.prog = dspy.ChainOfThought("question, evidence, doc_context -> report")
```
