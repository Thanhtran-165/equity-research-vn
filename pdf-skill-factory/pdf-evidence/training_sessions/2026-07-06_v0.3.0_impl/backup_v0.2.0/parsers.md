# parsers.md — pdf-evidence routing

> Decision tree chọn parser theo loại PDF. v0.1 chỉ cài pdfplumber + pypdf.
> Tool nâng cao (Camelot, PaddleOCR, Surya, Docling, DeepDoc, MinerU) chỉ **mô tả** — chưa cài.

## Decision tree

```
PDF input
    │
    ▼
[scripts/classify.py]
    │
    ├── digital_text ────────► pdfplumber.extract_text (fast path)
    │                            + pdfplumber.extract_tables nếu có bảng
    │
    ├── scanned ─────────────► v0.1: ABSTAIN + warning
    │                            "Scan PDF cần OCR — cài PaddleOCR/Surya (v0.5+) hoặc cung cấp text"
    │                            v0.5+: PaddleOCR (đa ngữ) hoặc Surya (layout + reading order)
    │
    ├── mixed ───────────────► per-page:
    │                            page có text → pdfplumber
    │                            page không text → warning (có thể scan)
    │
    ├── table_heavy ─────────► pdfplumber.extract_tables
    │                            + GIỮ headers/units/period
    │                            + warning nếu merged/rotated cell
    │                            v0.2+: Camelot (lattice → stream fallback)
    │                            v0.4+: DeepDoc TSR (auto-correct rotation)
    │
    ├── legal ───────────────► pdfplumber + detect "Điều/Khoản/Điểm/Nghị định/Thông tư"
    │                            GIỮ cấu trúc điều khoản
    │
    ├── financial ───────────► pdfplumber.extract_tables
    │                            GIỮ units/period/sign
    │                            phân biệt thực tế/dự báo/nhận định
    │
    ├── academic ────────────► pdfplumber
    │                            warning nếu multi-column (reading order có thể sai)
    │                            v0.5+: Surya (reading order)
    │
    ├── policy ──────────────► pdfplumber + structure detect
    │
    ├── slide_export ────────► pdfplumber
    │                            warning layout phi text
    │
    └── low_quality_ocr ─────► warning + verify thủ công
                                 không kết luận chắc
```

## Quy ước extract

Mọi extraction phải trả **page anchor** để citation có page:

```python
# scripts/extract.py output (v0.2.0)
{
  "schema_version": "0.2.0",
  "pages": [
    {
      "page": 1, "text": "...", "char_count": 1234,
      "tables": [
        {
          "table_id": "p1.t1",            # global, page-prefixed
          "page": 1,
          "headers": ["Chỉ tiêu", "Q1/2026 (tỷ VNĐ)"],
          "rows": [["Doanh thu", "12.500"]],
          "units": "tỷ VNĐ",              # inferred from headers (regex)
          "period": "Q1/2026",            # inferred from headers (regex)
          "parse_confidence": 1.0,        # 1.0 clean / 0.5 null headers / 0.3 merged-sparse
          "table_uncertainty_disclosure": false   # true when parse_confidence < 0.7
        }
      ],
      "charts": [
        {
          "chart_id": "p1.c1",            # global, page-prefixed
          "page": 1,
          "chart_type": "image_region",
          "title": null,
          "parse_confidence": 0.4,        # charts always lower than tables
          "table_uncertainty_disclosure": true
        }
      ]
    }
  ]
}
```

**Bắt buộc** (F-TABLE-001, TABLE-WIRING-001 — đã wire v0.2.0):
- `table_id` (pN.ti) / `chart_id` (pN.ci) global trong document.
- `units`, `period` được infer từ headers qua regex (fallback null + warning).
- `parse_confidence` + `table_uncertainty_disclosure` luôn emit.
- Khi claim bắt nguồn từ bảng/chart, citation PHẢI dùng `table_id`/`chart_id`
  (format `[file, page, table_id|chart_id, row/col, snippet]`) — extract.py emit id,
  ExtractEvidence → AnswerWithCitation propagate.
- KHÔNG bịa số liệu: cell null → abstain sub-question đó (→ `partial_abstentions[]`),
  không guess. Sign `(N)` → `-N` (sign convention); KHÔNG biến đổi khác.
- Bảng/chart parse không chắc → `note: "uncertain parse — verify"` + giảm `confidence`.

## Khi nào warning

| Tình huống | Warning |
|------------|---------|
| Page không có text layer | `"Page N có thể là scan — cần OCR"` |
| Bảng merged cell | `"Bảng p.N có merged cell — verify thủ công"` |
| Bảng rotated | `"Bảng p.N bị xoay — verify hoặc dùng DeepDoc (v0.4+)"` |
| Multi-column | `"PDF multi-column — reading order có thể sai"` |
| Parse confidence thấp | `"Parser uncertainty on p.N — verify"` |
| Đơn vị mất header | `"Bảng p.N mất header đơn vị — verify"` |

## Tool reference (chưa cài v0.1)

| Tool | Khi nào dùng | Lý do chưa cài |
|------|--------------|----------------|
| `pypdf` | fallback đọc PDF cơ bản | ✅ cài |
| `pdfplumber` | text + tables + char-level | ✅ cài |
| `PyMuPDF4LLM` | Markdown nhanh born-digital | v0.2+ |
| `Camelot` | bảng lattice/stream | v0.2+ |
| `DeepDoc` (RAGFlow) | layout + TSR + rotation fix | phức tạp, v0.4+ |
| `Docling` | structured output born-digital | v0.2+ |
| `Marker` | PDF→Markdown text-heavy | v0.3+ |
| `MinerU` | formula/table-heavy + OCR | v0.4+ |
| `PaddleOCR` | scan OCR đa ngữ (VN+80) | v0.5+ |
| `Surya` | layout + reading order + table 90+ ngôn ngữ | v0.5+ |
| `Unstructured` | unified pipeline | v0.6+ |

## Nguyên tắc cấm

- KHÔNG chạy text-only extraction trên page không có text layer (F15).
- KHÔNG tóm tắt bảng mà không đọc header (F04).
- KHÔNG cite bảng parse không chắc (F16).
- KHÔNG bỏ qua warning parser — phải forward tới user.
