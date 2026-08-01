# PROMPT REVIEW TỔNG QUAN — equity-research-vn (dành cho V4 Flash)

Bạn là reviewer độc lập. Lần này **KHÔNG soi từng REQ** — 5 vòng trước đã làm kỹ. Lần này hãy nhìn **toàn bộ pipeline end-to-end** dưới góc **người dùng thật chạy skill**. KHÔNG sửa code — chỉ phân tích, báo cáo.

## Bối cảnh

Skill: `/Users/bobo/.zcode/skills/equity-research-vn/` — pipeline 9 phase phân tích cổ phiếu Việt Nam, từ sponsor data đến dashboard deploy. Hiện **v3.2.0, 67 REQ** (đã qua 5 đợt hardening + 5 vòng nghiệm thu chéo — mọi lỗ hổng bịa đã đóng, 5/5 mutation bắt được).

## Góc review của BẠN (black-box, góc người dùng)

Bạn giỏi **đánh đen** — đặt mình vào chỗ người dùng/kẻ gian, chạy pipeline thật, xem có chỗ nào **vẫn lọt** hoặc **gây khó chịu** mà soi từng REQ không thấy. Tập trung 4 câu hỏi:

### 1. Pipeline chạy thật có trơn không?
- Đọc `SKILL.md` + `phases/*.md` + `scripts/run_phase.py` + `init_task_state.py`
- Mô phỏng trong đầu 1 lần chạy đầy đủ: `user gõ /equity-research-vn CTD` → phase 0 → 1 → ... → 7 deploy
- **Chỗ nào user/agent có thể đi lạc?** Phase nào thiếu hướng dẫn rõ? Phase nào chồng chéo input/output? Có phase "cửa tử" (fail 1 bước là cả pipeline chết, không có lối thoát)?

### 2. Trải nghiệm người dùng non-code (quan trọng nhất)
Người dùng chính là **người không rành kỹ thuật**, dùng AI để chạy skill. Hãy đánh giá:
- Khi pipeline FAIL ở 1 REQ → thông báo lỗi có **đủ rõ để người non-code hiểu mình phải làm gì** không? Hay chỉ stack traceTechnical?
- Phase nào bắt user nhập tay (ví dụ investment amount) mà không có hướng dẫn đời thường?
- Output cuối (dashboard HTML) có thực sự **dùng được** cho người đầu tư, hay chỉ đẹp mà thiếu thông tin quyết định?

### 3. Kịch bản tấn công MỚI (vượt ra ngoài 67 REQ)
5 vòng trước test từng REQ. Lần này hãy nghĩ kịch bản **toàn pipeline** mà 67 REQ không bắt được:
- Agent gian lận ở NHIỀU phase cùng lúc (không chỉ 1 REQ)
- Agent bỏ qua 1 phase hoàn toàn mà vẫn PASS (pipeline có check phase missing không?)
- Data "thật" nhưng sai ngữ cảnh (ví dụ giá đúng ticker nhưng sai ngày — giá tuần trước đóng gói như giá hôm nay)
- Sự phối hợp giữa các phase tạo ra lỗ hổng (phase A chỉnh sửa data mà phase B không biết)

### 4. Tính khả thi khi scale
- Skill này chạy tốt cho CTD — nhưng nếu user chạy cho **5-10 ticker cùng lúc** thì sao? Có đụng rate limit vnstock không?
- Nếu ticker **rất nhỏ** (OTC, ít data) hoặc **mới IPO** (chưa đủ 5 năm BCTC) → pipeline xử lý thế nào? Có fail-closed hay vẫn cố chạy ra report rác?

## Việc phải làm trước khi đánh giá

1. Đọc `SKILL.md` (entry point), `requirements-phase-map.yaml` (sơ đồ REQ→phase), toàn bộ `phases/*.md`
2. Đọc `scripts/run_phase.py` + `init_task_state.py` để hiểu luồng chạy thật
3. Chạy thử mô phỏng: đọc `task-state.json` schema, xem 1 phase ghi gì cho phase sau
4. Tự nghĩ ra **≥3 kịch bản tấn công/lỗi pipeline mới** (không trùng 25+ mutation đã test ở vòng REQ)

## Output bắt buộc

```markdown
# Review tổng quan pipeline — góc người dùng (V4 Flash)

## Mô phỏng 1 lần chạy đầy đủ
(mô tả luồng user gõ lệnh → output cuối, chỗ nào mượt, chỗ nào kẹt)

## 4 câu hỏi (trả lời từng cái, có bằng chứng file:line)

### 1. Pipeline trơn không?
### 2. Người dùng non-code hiểu được không?
### 3. Kịch bản tấn công mới (≥3, kèm "REQ nào lẽ ra phải bắt")
### 4. Scale / edge case (OTC, IPO mới, đa ticker)

## Đề xuất (ưu tiên CRITICAL/HIGH/MEDIUM)
| ID | Mức | Vấn đề pipeline | Bằng chứng | Đề xuất |

## Khuyến nghị
- Làm ngay (≤3)
- Làm sau
- Không nên làm
```

## Nguyên tắc
- Trung thực: nếu pipeline **thực sự tốt**, nói thẳng "tốt, không có vấn đề" — đừng bịa vấn đề cho có
- Mỗi đề xuất phải kèm **kịch bản cụ thể** mà user/gian lận gặp phải — không lý thuyết suông
- KHÔNG sửa file — chỉ báo cáo
- **KHÔNG đọc review của V4 Pro** — giữ độc lập, tổng hợp sau
