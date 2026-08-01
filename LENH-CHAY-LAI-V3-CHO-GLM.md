# LỆNH V3: CHẠY LẠI VCB + HPG — XÁC NHẬN FIX + NARRATIVE ĐỦ SÂU (VÒNG LẶP FIX BẮT BUỘC)

**Từ:** ZCode (phiên nâng cấp Wave 1–5 + fix cohort V2)
**Giao cho:** GLM (phiên thực thi)
**Ngày:** 2026-08-01

---

## 1. Bối cảnh (đọc trước — 3 phút)

Sau cohort V2 (`/tmp/COHORT-REPORT-GLM-V2.md`), ZCode đã sửa xong 3 thứ trong skill (bản hiện tại trên máy):

| Fix | Nội dung | Mã bị ảnh hưởng |
|---|---|---|
| **Verifier case-insensitive** | `verify_data_accuracy` + spot-check CSV + API live + ROA giờ khớp cột không phân biệt hoa/thường (`TOTAL ASSETS` = `Total Assets`) | VCB — REQ-023/025 trước fail vì column names |
| **REQ-074 (MỚI)** | P/E chuẩn hóa cho cổ phiếu chu kỳ: kích hoạt khi EPS CV > 30% VÀ EPS hiện tại < 80% đỉnh 5 năm → bắt buộc trình bày cả P/E raw lẫn P/E chuẩn hóa (giá ÷ median EPS 5 năm), verifier tự tính lại ±10% | HPG — P/E raw 11,0× vs chuẩn hóa 8,06× |
| **CFO 3 tên cột + bank gate** | phase1-data.md hướng dẫn thử lần lượt 3 tên cột CFO; phát hiện ngân hàng từ phase 1 | VCB |

**Chuẩn hiện tại: 74 REQ** (không còn 73). CTD baseline khi chạy với agent sâu (V4 Flash): **67/73 trên chuẩn cũ ≈ 67-69/74 trên chuẩn mới**.

**Bài học lớn nhất từ V2:** kết quả 44/73 có 71% fail là *narrative nông* — chính bạn thừa nhận *"em làm 1 vòng rồi dừng. Flash làm 5 vòng fix → 67/73"*. **Lệnh này bắt buộc vòng lặp fix — không được dừng sau 1 vòng.**

## 2. NHIỆM VỤ

| # | Mã | Ngành | Mục tiêu riêng | Work dir |
|---|---|---|---|---|
| 1 | **VCB** | Ngân hàng | Xác nhận fix case-insensitive: REQ-023/025 không còn fail vì column names | `/tmp/cohort_v3_VCB` |
| 2 | **HPG** | Thép chu kỳ | REQ-074 mới: P/E chuẩn hóa phải xuất hiện và verifier bắt đúng | `/tmp/cohort_v3_HPG` |

## 3. QUY TRÌNH BẮT BUỘC — VÒNG LẶP FIX (ĐIỂM MẤU CHỐT)

1. Chạy 9 phase đầy đủ như V2 (SKILL.md → phase prompts → sub-skills thật → task-state.json → verify từng phase)
2. **Verify lần 1:** `python3 ~/.zcode/skills/equity-research-vn/scripts/independent_verifier.py <TICKER> <WORK_DIR>/<TICKER>_Complete_Report.html`
3. **VÒNG LẶP FIX (tối thiểu 2 vòng, tối đa 5):**
   - Đọc từng REQ fail → sửa report HTML (narrative, citations, DATA arrays) → verify lại
   - Ưu tiên sửa các REQ: 005, 006, 008, 012, 013, 014, 015, 018, 019, 022, 025, 026, 028, 029, 031, 034, 037, 041, 042, 048, 069, 071 (toàn bộ nhóm narrative/chart-data)
   - Mỗi vòng ghi log: vòng mấy, sửa REQ nào, kết quả sau verify
4. **Điều kiện dừng:** recall ≥ 65/74 HOẶC đã làm đủ 5 vòng → báo cáo trạng thái trung thực

## 4. CHECKLIST NARRATIVE DEPTH (bắt buộc kiểm từng mục — bài học V2)

| # | Mục | Chuẩn đạt |
|---|---|---|
| 1 | Section content | Mỗi section chính ≥ 200 ký tự thật (KHÔNG placeholder) |
| 2 | Insights | ≥ 3 insights, mỗi insight ≥ 500 ký tự, có số liệu + nguồn |
| 3 | Citations | Mỗi số key (PE/PB/CAGR/ROE/doanh thu...) có nguồn NAMED cùng câu (vd "theo BCTC kiểm toán 2025") — không chỉ `[ref-N]` trống |
| 4 | Chart DATA | Mảng DATA khớp format financials.json (key `totalAssets`, `equity`...), ≥ 13 canvas render |
| 5 | Investment amount | Số 1 tỷ đồng xuất hiện trong narrative sec-investment |
| 6 | Max drawdown | Số cụ thể từ data giá 52 tuần (không "ước tính 30-50%") |
| 7 | News | Sentiment score SỐ + phân loại theo category |
| 8 | Tech section | Tech Score SỐ + Verdict trong sec-tech; khớp technical_active.json |
| 9 | Split audit | task-state split_audit đủ keys (`cp_consistent`, `method`, `periods_checked`, `cp_per_year` nếu có) |
| 10 | References | ≥ 10 citations đánh số `[ref-N]` có phần nguồn tương ứng |

## 5. YÊU CẦU RIÊNG TỪNG MÃ

**VCB:**
- KHÔNG cần workaround case-insensitive nữa (đã fix chính thức) — chạy thẳng, nếu REQ-023/025 vẫn fail vì column → ghi RÕ triệu chứng (ZCode sẽ kiểm tra)
- Nhớ bank gate: revenue = Total Operating Income, skip CCC/FCFF, dùng P/B + DDM (sector_method_registry.md)

**HPG:**
- REQ-074 kích hoạt (EPS 2021 đỉnh → 2023 đáy → 2025 dưới đỉnh) → **PHẢI** trình bày P/E chuẩn hóa = 8,06× (giá ÷ median EPS 5 năm) bên cạnh P/E raw 11,0× — viết đúng cụm "P/E chuẩn hóa" để verifier nhận diện
- P/E raw vẫn phải xuất hiện (verifier kiểm tra cả 2)
- Nếu REQ-074 không kích hoạt (lạ) hoặc bắt sai số → ghi rõ → đây là REQ mới cần nghiệm thu

## 6. TUÂN THỦ LUẬT SKILL (giữ nguyên)

- UNIT CONTRACT: marketCap = price × shares_tỷ; fairPrice = fairMarketCap / shares_tỷ
- FCFF/FCFE: không gọi CFO−CapEx là FCFF; bridge EV−NetDebt=Equity; g < wacc
- NO INTERNAL META (REQ-070): narrative không chứa tên phase/file JSON/task-state
- S/R REALISTIC (REQ-072): kháng cự ∈ [giá, +30%], hỗ trợ ∈ [−30%, giá]
- ZERO DATA (REQ-071): thiếu data ghi `null`, KHÔNG ghi 0
- WACC: mỗi input ghi NGÀY + NGUỒN
- Split audit: CP lệch >20% ghi rõ cause
- Đơn vị: số tiền = tỷ VND; giá/EPS/BVPS = VND/cp

## 7. BÁO CÁO (tạo `/tmp/COHORT-REPORT-GLM-V3.md`)

Bảng:

| Ticker | Recall (x/74) | REQ fail (id + lý do 1 dòng) | Charts render | Số vòng fix | Token ước tính | Ghi chú |
|---|---|---|---|---|---|---|

Sau bảng, tối thiểu:
1. **Nghiệm thu fix:** VCB REQ-023/025 còn fail vì column names không? (XÁC NHẬN PASS hoặc FAIL kèm triệu chứng)
2. **Nghiệm thu REQ-074:** trên HPG kích hoạt không? P/E chuẩn hóa hiển thị? verifier bắt đúng số 8,06×?
3. **Phân loại TỪNG REQ fail còn lại:** lỗi skill / lỗi data / lỗi narrative / đặc thù ngành
4. **Token/mã ước tính** (phương pháp: số lượt tool call × context trung bình) — dự toán VN100
5. **Kết luận maturity:** mã nào đạt recall cao → có đủ bằng chứng nâng `PRODUCTION_READY` không?

## 8. RÀNG BUỘC (KHÔNG được làm)

- ✗ Sửa source skill gốc (`~/.zcode/skills/equity-research-vn` + sub-skills) — skill đã có fix chính thức
- ✗ Dùng runner rút gọn / template fill kiểu V1
- ✗ Dừng sau 1 vòng verify (vòng lặp fix tối thiểu 2 vòng — mục 3)
- ✗ Bỏ phase nào (kể cả phase6 dashboard + phase7 deploy)
- ✗ Commit/push gì cả
- ✗ Bịa số liệu khi API lỗi — ghi `BLOCKED_API` + triệu chứng

## 9. TIÊU CHÍ THÀNH CÔNG

- **≥ 65/74** trên ít nhất 1 mã (narrative sâu như Flash) — hoặc nếu không đạt: phân loại trung thực TỪNG fail còn lại + ghi rõ vì sao
- VCB: fix case-insensitive được xác nhận (REQ-023/025 không còn fail vì column names)
- HPG: REQ-074 kích hoạt + bắt đúng số
- Token/mã ước tính rõ ràng — input cho kế hoạch VN100
