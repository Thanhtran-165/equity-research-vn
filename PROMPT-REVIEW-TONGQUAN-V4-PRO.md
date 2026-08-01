# PROMPT REVIEW TỔNG QUAN — equity-research-vn (dành cho V4 Pro)

Bạn là reviewer độc lập. Lần này **KHÔNG soi từng REQ** — 5 vòng trước đã làm kỹ. Lần này hãy nhìn **toàn bộ pipeline end-to-end** dưới góc **kiến trúc sư / người bảo trì codebase**. KHÔNG sửa code — chỉ phân tích, báo cáo.

## Bối cảnh

Skill: `/Users/bobo/.zcode/skills/equity-research-vn/` — pipeline 9 phase phân tích cổ phiếu Việt Nam, từ sponsor data đến dashboard deploy. Hiện **v3.2.0, 67 REQ** (đã qua 5 đợt hardening + 5 vòng nghiệm thu chéo — mọi lỗ hổng bịa đã đóng, 5/5 mutation bắt được, dict dispatch, helper citation).

## Góc review của BẠN (white-box, góc kiến trúc sư)

Bạn giỏi **đọc code + tư duy cấu trúc**. Lần trước bạn đã soi từng hàm verify_*. Lần này hãy **nhìn lên cao hơn** — cả codebase như 1 hệ thống. Tập trung 4 câu hỏi:

### 1. Kiến trúc tổng thể có lành mạnh không?
- Vẽ (bằng text) **sơ đồ kiến trúc**: input → 9 phase → output. Data chảy giữa các phase thế nào (task-state.json schema)?
- **Single point of failure** ở đâu? (1 file/hàm mà hỏng → cả pipeline chết)
- **Coupling** (ràng buộc chéo) giữa các phase: phase nào đọc output phase khác mà không qua interface rõ → khó refactor?
- `task-state.json` có trở thành **"god object"** (1 file chứa mọi thứ, ai cũng ghi vào) không? Schema có version control không?

### 2. Maintainability (khả năng bảo trì) sau 5 đợt hardening
- Verifier đã 4,091 dòng trong 1 file. **Đọc `independent_verifier.py` tổng thể** — có nên tách module không? Theo lớp nào (data-driven dispatch, narrative checks, data accuracy, tech/valuation)?
- 5 đợt vá để lại **tech debt** gì? (comment "V3 fix", "G13", "batch-2" rải rác — có cần dọn không?)
- Helper `_check_claim_citation` tạo rồi nhưng 5 hàm citation chưa gộp — **đánh giá**: gộp giờ đáng rủi ro hay nên để?
- Test suite: `test_v5_negative.py` (8 bài) + fixture builder — **đủ phủ không** cho production? Phase nào chưa có test?

### 3. Phân tán trách nhiệm (separation of concerns)
- Verifier hiện đảm nhận **cả 3 vai**: kiểm tra cấu trúc (section/canvas), kiểm tra dữ liệu (recompute/cross-footing), kiểm tra ngữ nghĩa (citation/causal/trend). 3 vai này có nên tách không?
- `run_phase.py` vừa chạy phase vừa verify — có nên tách "runner" và "verifier" ra 2 process không?
- Phase prompt (`phases/*.md`) vừa là **hướng dẫn cho agent** vừa chứa **yêu cầu kỹ thuật** — 2 mục đích này có xung đột không?

### 4. Định hướng tương lai (roadmap)
- Nếu phải **thêm 1 phase mới** (ví dụ phase ESG, phase so sánh đa ticker) — kiến trúc hiện cho phép không? Điểm cắm ở đâu?
- Nếu **thay engine verifier** (ví dụ từ Python regex sang LLM-as-judge) — interface nào ổn định, interface nào sẽ vỡ?
- **Maturity**: skill tự xưng "PRODUCTION_READY" trong VERSION — theo tiêu chí nào nên giữ/xóa nhãn này?

## Việc phải làm trước khi đánh giá

1. Đọc `independent_verifier.py` **toàn bộ** (không chỉ từng hàm — nhìn cấu trúc file)
2. Đọc `task-state.json` schema (từ 1 run thật: `/tmp/ervn_e2e/CTD/.task-state/task-state.json` hoặc fixture builder)
3. Đọc `run_phase.py` + `init_task_state.py` — luồng orchestration
4. Đếm: dòng code, số hàm, số REQ theo phase, độ trùng lặp (grep pattern lặp)
5. Vẽ sơ đồ kiến trúc bằng text (data flow)

## Output bắt buộc

```markdown
# Review tổng quan pipeline — góc kiến trúc sư (V4 Pro)

## Sơ đồ kiến trúc (text)
(input → 9 phase → output, data flow qua task-state.json)

## 4 câu hỏi (trả lời từng cái, có bằng chứng file:line / dòng code)

### 1. Kiến trúc tổng thể (single point of failure, coupling, god object)
### 2. Maintainability (tech debt, tách module, test phủ)
### 3. Separation of concerns (3 vai verifier, runner vs verifier, prompt 2 mục đích)
### 4. Roadmap (thêm phase, đổi engine, maturity label)

## Đề xuất (ưu tiên CRITICAL/HIGH/MEDIUM)
| ID | Mức | Vấn đề kiến trúc | Bằng chứng | Đề xuất |

## Khuyến nghị
- Làm ngay (≤3)
- Làm sau
- Không nên làm
```

## Nguyên tắc
- Trung thực: nếu kiến trúc **thực sự tốt**, nói thẳng — đừng bịa vấn đề cho có
- Mỗi đề xuất phải kèm **bằng chứng dòng/file** và **kịch bản cụ thể** (khi nào vấn đề phát sinh)
- KHÔNG sửa file — chỉ báo cáo
- **KHÔNG đọc review của V4 Flash** — giữ độc lập, tổng hợp sau
- Bạn giỏi white-box → đây là sân của bạn, hãy đào sâu
