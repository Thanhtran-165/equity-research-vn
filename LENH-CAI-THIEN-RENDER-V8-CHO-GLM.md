# LỆNH V8: CẢI THIỆN NARRATIVE GENERATOR + REBUILD 73 MÃ (MỤC TIÊU AVG ≥ 60/74)

**Từ:** ZCode · **Giao cho:** GLM · **Ngày:** 2026-08-02

---

## 1. BỐI CẢNH (đọc trước — 3 phút)

VN100 batch 1 đạt recall trung bình 53.2/74 (0 mã ≥ 60) — nguyên nhân hệ thống: `vn100_render2.py` (narrative generator tự sinh) không pass 10 REQ narrative; **2 REQ còn lại là bug verifier — ZCode ĐÃ VÁ XONG**:

| REQ | Trạng thái | Bằng chứng (ZCode verify trên ACB thật) |
|---|---|---|
| REQ-031 (drawdown "3 mức"/"50%") | ✅ ĐÃ VÁ (cắt disclaimer + chặn "(" + bỏ triệu/tỷ) | PASS trên ACB |
| REQ-048 ("CFO" bị bắt là claim quản lý) | ✅ ĐÃ VÁ (loại CFO khỏi keywords, thêm "Giám đốc tài chính") | PASS trên ACB |

→ **Còn 10 REQ narrative là việc của bạn** (render2): REQ-003, 005, 008, 013, 024, 029, 033/034/036 (format số), 037, 069.

**Data đã fetch và lưu** (`/tmp/vn100_reports/*.html` + tracker) — **KHÔNG fetch lại API**: chỉ cải thiện renderer + rebuild HTML từ data có sẵn.

## 2. NHIỆM VỤ

1. **Cải thiện `vn100_render2.py`** để pass 10 REQ còn lại (danh sách chi tiết mục 3)
2. **Rebuild 73 mã** (2 reference CTD/HPG không rebuild) — render lại HTML từ data đã lưu (nếu data files bị xóa, fetch LẠI data 73 mã theo quy tắc rate limit)
3. Verify từng mã → ghi tracker → **mục tiêu: recall trung bình ≥ 60/74, ≥ 60 mã recall ≥ 60/74** (đúng goal ban đầu)
4. Báo cáo `/tmp/VN100-REPORT-V2.md`

## 3. 10 REQ CẦN VÁ TRONG render2 (kèm cách fix từ báo cáo VN100 + kinh nghiệm cohort)

| REQ | Lỗi hiện tại | Fix trong renderer |
|---|---|---|
| **REQ-003** | Không output split_audit đúng format | Ghi task-state `phases.phase1_data.result.split_audit` đủ keys: `cp_consistent`, `method`, `periods_checked`, `cp_per_year` (back-calc CP=LNST/EPS từng năm) |
| **REQ-005/037** | tech_score=0/NEUTRAL cố định | Tính Tech Score THẬT từ price weekly 52 tuần: MA10/20/50 trend + RSI + MACD → score −6..+6 + verdict; ghi vào `technical_active.json` + narrative "SCORE: X VERDICT: Y (nguồn: ...)" |
| **REQ-008** | Không fetch news | Fetch news 30 ngày (vnstock Company.news, ≤50 bài) → sentiment score SỐ + category breakdown; nếu API chết → narrative ghi rõ "không fetch được news" (REQ-008 fail hợp lệ thì chấp nhận, đừng bịa) |
| **REQ-013** | Section <200 ký tự (sec-checklist) | Mọi section chính ≥ 200 ký tự thật |
| **REQ-024** | Thiếu capex array | DATA thêm `capex` từ `cash_flow.json['Purchases of fixed assets']` (đúng key) |
| **REQ-029** | Số thiếu cite cùng câu | Mỗi số key (PE/PB/ROE/CAGR/doanh thu) kèm nguồn NAMED cùng câu + [ref-N] |
| **REQ-033/034/036** | Format số bị parse sai ("1.190"→1190, revenue làm tròn "34") | Dùng format verifier-friendly: **comma nghìn** ("33,797.9"), P/B 2 số thập phân không số 0 thừa ("1.19"), không làm tròn revenue; gắn NĂM rõ cho mỗi claim |
| **REQ-069** | Canvas/DATA shape sai | Đủ 67 keys DATA (mẫu CTD), mọi `new Chart($('id'))` có canvas tương ứng, dataset data là ARRAY |

**Mẫu format chuẩn (đối chiếu trực tiếp):** `/Users/bobo/ZCodeProject/ctd-v4flash/CTD_Complete_Report.html` (72/74) + `/tmp/cohort_v3_HPG/HPG_Complete_Report.html` (71/74).

## 4. QUY TRÌNH

1. Sửa render2 → test trên **1 mã** (chọn mã recall thấp nhất hoặc ACB) → verify → lặp tới khi mã test ≥ 62/74
2. Mã test đạt → rebuild toàn bộ 73 mã (tuần tự; giữ `/tmp/vn100_reports/` cũ làm backup `/tmp/vn100_reports_v1/`)
3. Verify từng mã → cập nhật `/tmp/vn100_tracker.json` (giữ nguyên format — nguồn sự thật)
4. Báo cáo `/tmp/VN100-REPORT-V2.md` (bảng 73 mã + thống kê + còn REQ nào fail + top-10 cơ hội mới)

## 5. RÀNG BUỘC

- ✗ Sửa source skill — nghi verifier sai → bằng chứng + `needs_human`, không tự sửa
- ✗ Copy HTML giữa các mã (Lesson #17 — renderer sinh từ data từng mã là đúng)
- ✗ Bịa số khi thiếu data — `null`, không 0; news không fetch được thì ghi rõ
- ✗ Commit/push
- KHÔNG fetch lại data trừ khi data files đã bị xóa (kiểm tra `/tmp/vn100_reports/` + tracker trước)

## 6. TIÊU CHÍ THÀNH CÔNG

- **≥ 60/73 mã recall ≥ 60/74** (hoặc avg ≥ 60/74)
- REQ-031/048 không được tái phát (đã vá verifier — nếu còn fail là do narrative thật)
- Báo cáo V2 phân loại rõ phần còn fail — input đợt vá cuối
