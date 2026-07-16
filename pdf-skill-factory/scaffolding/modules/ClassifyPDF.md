# Module spec — ClassifyPDF

> DSPy-style SIGNATURE (text spec, không cài dspy v0.1). Sẽ compile bằng GEPA ở v0.7+.

## Signature

```
ClassifyPDF(doc: PDFDocument) -> doc_type: Literal[
  "digital_text", "scanned", "mixed", "table_heavy",
  "legal", "financial", "academic", "policy",
  "slide_export", "low_quality_ocr"
]
```

## Mô tả

Phân loại mỗi PDF theo loại để route parser + áp dụng policy tương ứng. v0.1 dùng heuristic (`scripts/classify.py`): density char/page + keyword pháp lý/tài chính + table count.

## Input fields

- `doc` — PDF document object: `{path, pages: [{page, text, char_count, tables}]}`.

## Output fields

- `doc_type` — một trong 10 loại trên.
- (optional) `confidence`, `reasons[]`.

## Metric

- `classification_accuracy` (rule): so với ground-truth doc_type trong fixture (nếu có).

## Example

Input: PDF có 10 trang, mỗi trang ≥ 1000 ký tự, có keyword "Doanh thu"/"LNST" → `doc_type = "financial"`, `confidence = 0.9`.

## Failure liên quan

F04 (bỏ qua bảng), F15 (bỏ qua scan) — nếu classify sai dẫn tới route sai parser.

## v0.7+ compile hint

```
class ClassifyPDF(dspy.Module):
    def __init__(self):
        self.prog = dspy.ChainOfThought("doc -> doc_type, confidence, reasons")
    def forward(self, doc):
        return self.prog(doc=doc)
```
Compile bằng `dspy.GEPA(metric=classification_accuracy, auto='medium')`.
