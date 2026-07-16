# Module spec — ExtractEvidence

> DSPy-style SIGNATURE. Skeleton for v0.7+ GEPA compile.

## Signature

```
ExtractEvidence(
  question: str,
  doc: PDFDocument
) -> evidence: list[EvidenceSnippet]
```

`EvidenceSnippet = {quote: str, page: int, section: str, snippet: str}`

## Mô tả

Tìm trong PDF các snippet **liên quan trực tiếp** tới câu hỏi, kèm page + section heading gần nhất. Quote giữ verbatim.

## Policy áp dụng

- `policies.md#evidence` — không trả lời trước evidence.
- `policies.md#citation` — page bắt buộc.
- `parsers.md#` — route theo doc_type.

## Metric

- `coverage` (rule): số điểm cần / số điểm extract được.
- `context_recall` (RAGAS-style): gold answer attributable to evidence.

## Example

Input: question "Doanh thu Q1/2026?" + PDF financial.
Output:
```json
[
  {"quote": "doanh thu hợp nhất Q1/2026 đạt 12.500 tỷ đồng", "page": 7, "section": "Tổng quan tài chính", "snippet": "..."},
  {"quote": "biên LN gộp 24% (vs 22% Q1/2025)", "page": 7, "section": "Tổng quan tài chính", "snippet": "..."}
]
```

## Failure liên quan

F01 (page thiếu), F03 (page sai), F04 (bỏ bảng), F14 (multi-col reading order).

## v0.7+ compile hint

```
class ExtractEvidence(dspy.Module):
    def __init__(self):
        self.prog = dspy.ChainOfThought("question, doc_context -> evidence: list")
    def forward(self, question, doc):
        return self.prog(question=question, doc_context=render(doc))
```
