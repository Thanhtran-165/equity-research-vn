# failure_modes.md — pdf-evidence v0.1

> Rút gọn 20 lỗi thường gặp. Chi tiết + root cause + suggested fix ở factory `06-FAILURE_MODES.md`.
> Khi gặp lỗi → map F-NN → áp fix → thêm regression test.

## Citation / evidence

| ID | Lỗi | Fix nhanh |
|----|------|-----------|
| F01 | Citation thiếu page | extract.py bắt buộc trả page; verify page ∈ evidence trước emit |
| F02 | Hallucination (bịa) | `DetectMissingEvidence` bắt buộc; `pdf_only=true` default; abstain khi thiếu |
| F03 | Trích dẫn nhầm trang | verify page chính xác trong evidence set |
| F04 | Bỏ qua bảng/phụ lục | route `table_heavy` → `ExtractTable`; warning nếu parse không chắc |
| F05 | Trộn footnote vào main | detect footnote pattern; warn nếu claim dựa footnote |

## Pháp lý

| ID | Lỗi | Fix nhanh |
|----|------|-----------|
| F06 | Không nhận văn bản sửa đổi | task=`detect_changes/compare` → bắt buộc `CompareDocuments` |
| F07 | Tóm tắt sai điều khoản | giữ verbatim `Điều/Khoản/Điểm`; constraint no-paraphrase legal |
| F08 | Lẫn hiệu lực/ban hành/ap dụng | detect keyword; emit warning nếu mơ hồ |
| F09 | Diễn giải quá mức khi hỏi nguyên văn | task=`quote_verbatim` → cấm paraphrase |

## Số liệu / bảng

| ID | Lỗi | Fix nhanh |
|----|------|-----------|
| F10 | Nhầm dấu âm `(N)` | normalize `(N)` → `-N`; warn nếu không chắc |
| F11 | Nhầm đơn vị tỷ/triệu/nghìn | bắt buộc emit unit từ header; cảnh báo nếu thiếu |
| F12 | Bỏ kỳ thời gian | extract period từ header; warning nếu mất |
| F13 | Biến nhận định thành sự thật | detect "dự báo/kỳ vọng/nhận định"; prefix claim với loại |

## Layout / parser

| ID | Lỗi | Fix nhanh |
|----|------|-----------|
| F14 | Đọc sai multi-column | detect multi-col; warning; (v0.5+ Surya) |
| F15 | Bỏ qua scan page | classify per-page; warning + abstain nếu scan page quan trọng |
| F16 | Bảng parse không chắc nhưng kết luận chắc | warning + giảm confidence; không cite nếu confidence thấp |
| F17 | Bảng xoay | warning + abstain; (v0.4+ DeepDoc auto-correct) |

## Multi-PDF / PATCH 6

| ID | Lỗi | Fix nhanh |
|----|------|-----------|
| F18 | Không phát hiện xung đột PDF | mandatory `CompareDocuments` multi-PDF; warning conflict |
| F19 | Trộn citation alias | bắt buộc alias trong citation |
| F20 | Trộn kiến thức ngoài (`pdf_only=true`) | enforce default `pdf_only=true`; check `outside_knowledge_used`; tách section "Ngoài tài liệu" nếu user cho phép |

---

## Quy trình tự sửa

1. Phát hiện lỗi (qua eval runner hoặc user report).
2. Map F-NN → rule violated (`references/policies.md`).
3. Áp fix (sửa SKILL.md/references/scripts).
4. Thêm regression test (`scaffolding/tests/`).
5. Re-run regression cho đến khi xanh.
6. Nếu pass DoD → bump version theo `08-VERSIONING_PLAN.md` (human approval nếu minor/major).
7. Append `skill_memory.json` (lesson) + CHANGELOG.

Xem factory `06-FAILURE_MODES.md` cho format đầy đủ mỗi failure.
