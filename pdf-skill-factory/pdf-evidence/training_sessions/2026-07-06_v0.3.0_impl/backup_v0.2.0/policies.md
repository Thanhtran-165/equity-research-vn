# policies.md — pdf-evidence v0.1

> 8 policy chi tiết cho skill `pdf-evidence`. Đối chiếu `06-FAILURE_MODES.md` ở factory cho lỗi cụ thể.

## 1. Citation policy

**Format bắt buộc** cho mỗi claim quan trọng:
```
[file_name_or_alias, page_number, section_heading, quote_or_evidence_snippet]
```

Với bảng:
```
[file, page, table_id, row_or_column_reference]
```

**Khi nào dùng format bảng** (trigger — enforced by code path in v0.2.0):
- `extract.py` phát hiện bảng (`pN.ti`) hoặc chart (`pN.ci`) trên cited page VÀ
- Claim tham chiếu số liệu/range từ visual đó
→ PHẢI dùng format bảng/biểu đồ với `table_id` (hoặc `chart_id`).
- `table_id`/`chart_id` được extract.py emit; flow ExtractEvidence → AnswerWithCitation phải propagate.
- Nếu visual parse không chắc (`table_uncertainty_disclosure=true`) → vẫn dùng format bảng + `note: "uncertain parse — verify manually"` + giảm `confidence`.
- KHÔNG dùng format text-citation `[file, page, section, quote]` cho claim bắt nguồn từ bảng/chart.

Format citation bảng/biểu đồ đầy đủ (v0.2.0):
```
[file, page, table_id|chart_id, row/col reference, evidence snippet]
```
- Bảng: `[abc_2026, p.1, p1.t1, row 'Doanh thu' / col 'Q1/2026 (tỷ VNĐ)', '12.500']`
- Chart: `[igwt_2026, p.1, p1.c1, 'Gold Price 2045 Range', '~USD 6,900/oz lower bound']` (giá trị xấp xỉ, prefix `~`).

Quy ước:
- `file` = alias user cung cấp (vd `report_2026`) hoặc tên file ngắn.
- `page` = số trang (1-based). Nếu parser không xác định → `note: "Không xác định được trang từ parser hiện tại."`.
- `section` = heading gần nhất (vd `"Tổng quan tài chính"`).
- `quote` = snippet verbatim từ PDF (≤ 200 ký tự, không paraphrase).

Claim cần citation: số liệu, ngày, định nghĩa, điều khoản, so sánh, thay đổi, quote.
Claim không cần citation (ý procedural của skill): "Tài liệu không đề cập X".

**Lỗi liên quan**: F01 (thiếu page), F03 (nhầm page), F19 (trộn alias multi-PDF).

## 2. Evidence-first policy

- KHÔNG trả lời trước khi có evidence.
- Mỗi claim quan trọng phải có nguồn.
- Không thấy trong PDF → nói rõ "Tài liệu không đề cập ...".
- KHÔNG suy đoán thay tài liệu.
- KHÔNG bổ sung chi tiết từ trí nhớ để "đẹp" câu trả lời.
- Phân biệt main text vs. footnote → claim dựa chủ yếu footnote phải warn.

**Lỗi liên quan**: F02 (hallucination), F05 (trộn footnote).

## 3. Abstention / uncertainty policy (v0.2.0 — partial abstention là first-class)

Có 3 chế độ từ chối, KHÔNG bao giờ chôn refusal trong `warnings[]`:

### 3.1 Full abstain — `abstention_flag=true`

Khi:
- Câu hỏi **monolithic** (1 claim) và evidence thiếu, HOẶC
- **Tất cả** sub-question không answerable, HOẶC
- **Sub-question chính (load-bearing)** không answerable — kể cả khi peripheral answerable.

Output:
```json
{"abstention_flag": true, "answer": "Insufficient evidence in the provided documents.",
 "abstention_reason": "...", "partial_abstentions": []}
```

### 3.2 Partial abstain — `partial_abstentions[]` (mới v0.2.0)

Khi câu hỏi **multi-part**, sub-question **chính** answerable, một/vài sub-question **peripheral** không answerable.

Mỗi entry:
```json
{
  "claim_or_question_part": "số lượng nhân viên 2026",
  "status": "not_enough_evidence",
  "reason": "Tài liệu chỉ đề cập doanh thu (p.2), không có thông tin nhân sự.",
  "missing_evidence": "employee count / headcount for 2026",
  "suggested_next_document": "Báo cáo thường niên — phần 'Đội ngũ nhân sự'.",
  "confidence": 0.95
}
```

Bắt buộc: `status`="not_enough_evidence"; `missing_evidence` cụ thể (không "thiếu thông tin"); `confidence`≥0.7 cho chính refusal.

### 3.3 Low-confidence answer (không phải abstain)

Khi evidence có nhưng mờ/parse không chắc → trả lời + `confidence` thấp + `warnings[]` (warnings vẫn dùng cho parser/quality signals, KHÔNG dùng cho refusal).

### 3.4 Vì sao `warnings[]` không đủ cho refusal

`warnings[]` là grab-bag cho parser/quality signals (uncertain parse, missing header, multi-column). KHÔNG phải kênh từ chối có ngữ nghĩa:
- Consumer không phân biệt được "parser không chắc p.12" vs "tài liệu không chứa đáp án sub-question B".
- Không có structure: không `claim_or_question_part`, `missing_evidence`, `confidence`.
- Eval không grade được → `abstention_quality` stuck 0.50 ở v0.1.1.

`partial_abstentions[]` là first-class structured refusal channel → consumer + eval đọc trực tiếp.

### 3.5 Vietnamese text UX

Khi `partial_abstentions[]` non-empty, text output kèm section rõ ràng sau answer:
```
---
⚠ Phần không đủ bằng chứng:
- **<claim_or_question_part>**: <reason>. Cần thêm: <missing_evidence>.
---
Confidence: X | Outside knowledge: no | Abstain: partial(N) | Warnings: M
```

### Backward compatibility

- `partial_abstentions[]` là field **additive**. Consumer cũ ignore được (default `[]`).
- `abstention_flag` semantics KHÔNG đổi (vẫn binary full-answer abstain).
- `warnings[]` giữ nguyên cho parser signals; refusal strings di chuyển sang `partial_abstentions[]`.

**Lỗi liên quan**: F02 (hallucination), F05 (trộn footnote), **F-ABSTAIN-001** (partial abstention buried — đã fix v0.2.0).

**Lỗi liên quan**: F02 (hallucination thay vì abstain).

## 4. ⚠️ No-outside-knowledge policy (PATCH 6)

Mặc định `constraint.pdf_only=true`:

- KHÔNG trộn kiến thức ngoài (world knowledge, training data, thông tin thời sự) vào câu trả lời dựa trên PDF.
- Chỉ dùng kiến thức ngoài khi user **rõ ràng** cho phép (`pdf_only=false`).
- Khi dùng: phải tách section rõ ràng `"Ngoài tài liệu"` / `"Outside the documents"`, KHÔNG hòa lẫn với nội dung PDF.
- Set `outside_knowledge_used=true`.
- Reader phải biết phần nào từ PDF (verify được) vs. phần nào từ kiến thức ngoài (verify riêng).

Ví dụ sai:
```
Doanh thu 12.500 tỷ [PDF, p.7]. Công ty thuộc top 3 ngành bán lẻ [suy luận từ knowledge].
```
→ Nếu `pdf_only=true`: bỏ câu sau. Nếu `pdf_only=false`: tách section.

**Lỗi liên quan**: F02, F20.

## 5. Table policy

- KHÔNG tóm tắt bảng nếu chưa đọc header.
- GIỮ đơn vị (tỷ/triệu/nghìn VNĐ, %, USD), kỳ thời gian (Q1/2026, FY2025), cột/dòng.
- Số tài chính: kiểm dấu âm (`(N)` = `-N`), đơn vị, %.
- Nếu bảng parse không chắc → `warnings[]` + giảm confidence; không cite bảng như chắc chắn.
- Cell bị miss → nói rõ, không đoán.

**Lỗi liên quan**: F04 (bỏ bảng), F10 (nhầm dấu), F11 (nhầm đơn vị), F12 (bỏ kỳ), F16 (parse không chắc), F17 (xoay).

## 6. OCR policy

- **digital_text** → fast path: `pdfplumber`/`pypdf`.
- **scanned** (không text layer) → v0.1: **ABSTAIN** + warning `"Scan PDF cần OCR — chưa cài v0.1. Cài PaddleOCR/Surya hoặc cung cấp text OCR."`
- **mixed** → per-page: page không text layer → warning.
- **low_quality_ocr** → warning + verify thủ công.

Khi nào nghi scan:
- `classify.py` density char/page thấp (< 100 char).
- `pdfplumber` extract trả text rỗng/rất ít trên page có hình.

**Lỗi liên quan**: F15 (bỏ scan page).

## 7. Legal-document policy

- GIỮ đúng cấu trúc điều/khoản/điểm: `Điều X`, `Khoản Y`, `Điểm z`.
- KHÔNG diễn giải quá mức khi user hỏi nguyên văn → quote verbatim.
- "Thay đổi mới" / "sửa đổi" → phải xác định **văn bản gốc** + **văn bản sửa đổi**, so sánh (`CompareDocuments`).
- PHÂN BIỆT: hiệu lực / ngày ban hành / ngày áp dụng.
- Thiếu văn bản liên quan → nói thiếu, không bổ sung từ trí nhớ.
- Keyword pháp lý: "Điều", "Khoản", "Nghị định", "Thông tư", "Luật", "Quyết định".

**Lỗi liên quan**: F06 (không nhận sửa đổi), F07 (tóm tắt sai điều khoản), F08 (lẫn ngày), F09 (diễn giải quá mức).

## 8. Financial / macro report policy

- GIỮ đơn vị + kỳ báo cáo.
- PHÂN BIỆT:
  - **Dữ liệu thực tế** (đã ghi nhận).
  - **Dự báo** (tương lai, có giả định).
  - **Mục tiêu** (target — do tác giả đặt, có thời hạn).
  - **Khoảng xác suất** (probability range / scenario distribution).
  - **Nhận định** (ý kiến tác giả).
- KHÔNG biến nhận định tác giả thành sự thật khách quan.
- **MỖI số dự báo phải khai báo**: (a) loại `{actual | forecast | target | probability_range | scenario}`,
  (b) **time horizon** `{ngày/kỳ/năm áp dụng}`.
- Khi câu trả lời chứa ≥ 2 số dự báo với horizon khác nhau → gắn nhãn inline
  (vd "2030 decade target", "2045 model range", "12-month probability range")
  hoặc tóm tắt bảng horizon-type để reader không conflated.
- Số liệu → dẫn nguồn bảng/trang.
- Phân biệt bảng / biểu đồ / chú thích.

Keyword tài chính: "Doanh thu", "LNST", "BCTC", "VND", "%", "biên", "roe", "roa".

**Lỗi liên quan**: F10, F11, F12, F13 (nhận định thành sự thật), **F-FORECAST-001** (không khai báo horizon dự báo).

## 9. Multi-PDF policy

- So sánh 2+ văn bản → chạy `CompareDocuments`.
- Tìm: giống / khác / thay thế / xung đột.
- Mỗi difference có citation tới **cả** PDF.
- Conflict → nêu rõ + `warnings[]`, không pick im lặng.
- Citation bắt buộc có alias để phân biệt PDF nào.

**Lỗi liên quan**: F06, F18 (không phát hiện xung đột), F19 (trộn alias).

## 10. Vietnamese document policy

- GIỮ cấu trúc điều khoản tiếng Việt, không dịch gây mất nghĩa pháp lý.
- Phân biệt "nghìn/triệu/tỷ" (VN) vs. "thousand/million/billion" (EN).
- Tên riêng, cơ quan, ngày tháng giữ nguyên tiếng Việt khi cite (vd "Ngân hàng Nhà nước", "Ủy ban Chứng khoán Nhà nước").
- Output ngôn ngữ theo `constraint.language` (vi/en).
- Nếu PDF song ngữ → cite ngôn ngữ gốc của claim.

---

## Tóm tắt — checklist trước emit

- [ ] Mỗi claim có citation `[file, page, section, quote]`?
- [ ] Page ∈ evidence set?
- [ ] Quote verbatim?
- [ ] Không hallucinate?
- [ ] Không trộn kiến thức ngoài (`pdf_only=true`)?
- [ ] Bảng: header/đơn vị/kỳ/sign?
- [ ] Số tài chính: dấu/đơn vị/%?
- [ ] Đủ evidence hoặc abstain?
- [ ] Multi-PDF: alias phân biệt?
- [ ] Vietnamese: giữ điều khoản + đơn vị?
