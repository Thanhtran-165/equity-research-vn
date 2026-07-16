# File 6 — FAILURE_MODES.md

> 20 lỗi PDF thường gặp + cách skill tự sửa. Theo brief mục 3.4.
> Format: `Failure ID | Input | Expected | Actual | Root cause | Rule violated | Suggested fix | → regression test?`
> Phiên bản rút gọn chạy cùng skill ở `pdf-evidence/references/failure_modes.md`.

## Lỗi citation / evidence (F01–F05)

### F01 — Citation thiếu page
- **Input**: câu hỏi QA, evidence có snippet.
- **Expected**: citation `[file, p.7, "Tổng quan", "..."]`.
- **Actual**: citation `[file]` hoặc không có page.
- **Root cause**: parser trả text không kèm page; hoặc skill quên gắn page.
- **Rule violated**: `policies.md#citation`.
- **Suggested fix**: extract.py bắt buộc trả page; skill verify page ∈ evidence trước khi emit.
- **→ regression test?** yes — `fixtures/01_text_qa`.

### F02 — Hallucination (bịa nội dung)
- **Input**: câu hỏi về thông tin KHÔNG có trong PDF.
- **Expected**: `abstention_flag=true`.
- **Actual**: skill bịa câu trả lời.
- **Root cause**: dùng world knowledge thay vì PDF; không chạy `DetectMissingEvidence`.
- **Rule violated**: `policies.md#evidence`, `policies.md#abstention`, **PATCH 6 `policies.md#no-outside-knowledge`**.
- **Suggested fix**: enforce `pdf_only=true` default; mandatory `DetectMissingEvidence` trước answer.
- **→ regression test?** yes — `fixtures/02_no_answer_abstention`.

### F03 — Trích dẫn nhầm trang
- **Input**: snippet ở p.7, skill cite p.12.
- **Expected**: cite p.7.
- **Actual**: cite sai page.
- **Root cause**: parser gán page sai; hoặc skill lẫn evidence set.
- **Rule violated**: `policies.md#citation`.
- **Suggested fix**: extract.py verify page chính xác; skill check `page ∈ evidence` trước emit.
- **→ regression test?** yes — `fixtures/01_text_qa`.

### F04 — Bỏ qua bảng/phụ lục
- **Input**: PDF có bảng p.12.
- **Expected**: trả lời dùng bảng.
- **Actual**: skill chỉ dùng text, bỏ qua bảng.
- **Root cause**: parser không extract tables; hoặc skill không route table.
- **Rule violated**: `policies.md#table`.
- **Suggested fix**: route table_heavy → `ExtractTable`; warning nếu parse không chắc.
- **→ regression test?** yes — `fixtures/03_table`.

### F05 — Trộn footnote vào nội dung chính
- **Input**: PDF có footnote marker.
- **Expected**: tách biệt main vs footnote.
- **Actual**: skill lẫn footnote vào claim chính.
- **Root cause**: parser merge text không phân biệt.
- **Rule violated**: `policies.md#evidence`.
- **Suggested fix**: detect footnote pattern; warn nếu claim dựa chủ yếu footnote.
- **→ regression test?** yes (roadmap fixture).

## Lỗi pháp lý (F06–F09)

### F06 — Không nhận văn bản sửa đổi
- **Input**: 2 PDF (gốc + sửa đổi).
- **Expected**: phát hiện thay đổi.
- **Actual**: skill trả lời theo gốc, không compare.
- **Root cause**: skill không chạy `CompareDocuments`; hoặc classify nhầm.
- **Rule violated**: `policies.md#legal`, `policies.md#multi-pdf`.
- **Suggested fix**: task=detect_changes/compare → bắt buộc `CompareDocuments`.
- **→ regression test?** yes — `fixtures/05_multipdf_comparison`.

### F07 — Tóm tắt sai điều khoản pháp lý
- **Input**: văn bản có Điều 1, Khoản 2, Điểm a.
- **Expected**: giữ nguyên cấu trúc.
- **Actual**: skill paraphrase mất "Khoản 2".
- **Root cause**: skill optimize cho concision quá mức.
- **Rule violated**: `policies.md#legal`.
- **Suggested fix**: `legal_clause_preservation` metric; constraint giữ verbatim khi cite legal.
- **→ regression test?** yes — `fixtures/04_legal_mock`.

### F08 — Lẫn hiệu lực / ngày ban hành / ngày áp dụng
- **Input**: văn bản có "ban hành 01/01", "hiệu lực 15/01".
- **Expected**: phân biệt.
- **Actual**: skill gộp thành 1 ngày.
- **Root cause**: parser không tách; skill không verify.
- **Rule violated**: `policies.md#legal`.
- **Suggested fix**: detect keyword "ban hành" / "hiệu lực" / "áp dụng"; emit warning nếu mơ hồ.
- **→ regression test?** yes — `fixtures/04_legal_mock` (sub).

### F09 — Diễn giải quá mức
- **Input**: user hỏi nguyên văn.
- **Expected**: quote verbatim.
- **Actual**: skill diễn giải, thêm ý.
- **Rule violated**: `policies.md#legal`.
- **Suggested fix**: task=quote_verbatim → cấm paraphrase.
- **→ regression test?** yes — `fixtures/01_text_qa` (sub).

## Lỗi số liệu / bảng (F10–F13)

### F10 — Nhầm dấu âm số tài chính
- **Input**: bảng có "(12.500)" = -12.500.
- **Expected**: -12.500.
- **Actual**: 12.500.
- **Root cause**: parser không nhận dấu ngoặc = âm.
- **Rule violated**: `policies.md#financial`, `policies.md#table`.
- **Suggested fix**: normalize "(N)" → "-N"; warn nếu không chắc.
- **→ regression test?** yes — `fixtures/03_table` (negative variant).

### F11 — Nhầm đơn vị (tỷ/triệu/nghìn)
- **Input**: "12.500 tỷ".
- **Expected**: 12.500 tỷ VNĐ.
- **Actual**: 12.500 (thiếu đơn vị) hoặc 12.500 triệu.
- **Root cause**: skill bỏ header đơn vị; hoặc translate nhầm.
- **Rule violated**: `policies.md#financial`, `policies.md#table`, `policies.md#vietnamese`.
- **Suggested fix**: bắt buộc emit unit từ header; cảnh báo nếu thiếu.
- **→ regression test?** yes — `fixtures/03_table`.

### F12 — Bỏ qua kỳ thời gian
- **Input**: bảng Q1/2026 vs Q1/2025.
- **Expected**: phân biệt kỳ.
- **Actual**: skill gộp số liệu các kỳ.
- **Root cause**: parser mất header cột kỳ.
- **Rule violated**: `policies.md#financial`.
- **Suggested fix**: extract period từ header; warning nếu mất.
- **→ regression test?** yes — `fixtures/03_table`.

### F13 — Biến nhận định thành sự thật
- **Input**: báo cáo ghi "chúng tôi dự báo X".
- **Expected**: cite là dự báo.
- **Actual**: skill trình bày X như sự thật.
- **Rule violated**: `policies.md#financial`.
- **Suggested fix**: detect keyword "dự báo" / "kỳ vọng" / "nhận định"; prefix claim với loại.
- **→ regression test?** yes (roadmap financial fixture).

## Lỗi layout / parser (F14–F17)

### F14 — Đọc sai multi-column
- **Input**: PDF 2 cột.
- **Expected**: reading order đúng.
- **Actual**: skill merge chữ 2 cột.
- **Root cause**: parser không respect reading order.
- **Rule violated**: `parsers.md`.
- **Suggested fix**: detect multi-col; warning; (v0.5+ dùng Surya).
- **→ regression test?** yes (roadmap).

### F15 — Bỏ qua scan page
- **Input**: PDF mixed (text + 1 page scan).
- **Expected**: detect scan page, warning.
- **Actual**: skill trả lời thiếu nội dung scan.
- **Rule violated**: `policies.md#ocr`, `parsers.md`.
- **Suggested fix**: classify per-page; warning + abstain nếu scan page quan trọng.
- **→ regression test?** yes (roadmap v0.5).

### F16 — Bảng parse không chắc nhưng kết luận chắc
- **Input**: bảng phức tạp, parser confidence thấp.
- **Expected**: warning + verify.
- **Actual**: skill cite bảng như chắc chắn.
- **Rule violated**: `policies.md#table`.
- **Suggested fix**: warning + giảm confidence; không cite nếu parse confidence thấp.
- **→ regression test?** yes — `fixtures/03_table`.

### F17 — Bảng xoay 90/180 độ
- **Input**: bảng rotated.
- **Expected**: detect + warn.
- **Actual**: parser miss bảng.
- **Root cause**: không có rotation correction v0.1.
- **Rule violated**: `parsers.md`.
- **Suggested fix**: warning + abstain; (v0.4+ auto-correct DeepDoc).
- **→ regression test?** yes (roadmap v0.4).

## Lỗi multi-PDF (F18–F20)

### F18 — Không phát hiện xung đột giữa các PDF
- **Input**: 2 PDF mâu thuẫn số liệu.
- **Expected**: nêu conflict.
- **Actual**: skill pick 1 số liệu im lặng.
- **Rule violated**: `policies.md#multi-pdf`.
- **Suggested fix**: mandatory `CompareDocuments` khi multi-PDF; warning conflict.
- **→ regression test?** yes — `fixtures/05_multipdf_comparison`.

### F19 — Trộn citation giữa các PDF
- **Input**: 2 PDF alias `doc1`, `doc2`.
- **Expected**: citation ghi đúng alias.
- **Actual**: skill cite `[file]` mập mờ.
- **Rule violated**: `policies.md#citation`, `policies.md#multi-pdf`.
- **Suggested fix**: bắt buộc alias trong citation.
- **→ regression test?** yes — `fixtures/05_multipdf_comparison`.

### F20 — Trộn kiến thức ngoài (PATCH 6)
- **Input**: `pdf_only=true`.
- **Expected**: chỉ dùng PDF.
- **Actual**: skill bổ sung từ world knowledge.
- **Root cause**: skill không enforce `pdf_only`.
- **Rule violated**: **PATCH 6 `policies.md#no-outside-knowledge`**.
- **Suggested fix**: default `pdf_only=true`; check `outside_knowledge_used` flag; tách section "Ngoài tài liệu" nếu user cho phép.
- **→ regression test?** yes — test v0.1 check flag.

---

## Cách skill tự sửa (loop)

Mỗi failure → process theo `RUNBOOK.md`:
1. chạy eval → phát hiện F-NN;
2. map rule violated;
3. đề xuất instruction patch;
4. sửa SKILL.md/references;
5. re-run regression;
6. nếu pass DoD → bump version (human approval nếu minor/major);
7. append `skill_memory.json` + regression test permanent.
