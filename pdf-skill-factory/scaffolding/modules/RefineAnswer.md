# Module spec — RefineAnswer

> DSPy-style SIGNATURE. In-task refine (Self-Refine + TextGrad style).

## Signature

```
RefineAnswer(
  answer_obj: AnswerObject,
  critique: list[CritiquePoint]
) -> refined: AnswerObject
```

`CritiquePoint = {dimension: "citation_present"|"page_correct"|"no_hallucination"|"table_complete"|"outside_knowledge_clean", issue: str, severity: "low"|"medium"|"high", suggested_fix: str}`

## Mô tả

Refine câu trả lời **trong cùng task** dựa trên critique đa chiều. Chỉ chạy khi `AnswerWithCitation` có issue cheap-fixable (vd thiếu citation format, table cells không khớp).

## Khi nào chạy

- Self-check fail ở 1-2 dimension → chạy RefineAnswer 1 lần.
- Self-check fail > 30% → không refine, abstain.
- Lặp tối đa 3 lần — nếu không improve, giữ answer + warning.

## Anti-vague critic (TextGrad pattern)

Critique PHẢI specific:
- ❌ "Câu trả lời chưa tốt."
- ✅ "Claim '12.500 tỷ' thiếu page — cite p.7."

## Policy áp dụng

- `policies.md#` tất cả (check lại).

## Metric

- `citation_format_accuracy` improvement sau refine.
- `faithfulness` improvement sau refine.

## Failure liên quan

F01, F03, F11 (cheap-fixable trong task).

## v0.7+ compile hint

```
class RefineAnswer(dspy.Module):
    def __init__(self):
        self.prog = dspy.ChainOfThought("answer_obj, critique -> refined")
```
