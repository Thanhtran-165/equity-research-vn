# THƯ TÁI KIỂM ĐỊNH NHANH (CHECKPOINT) — TRƯỚC KHI REBUILD 1.000 MÃ

**Gửi:** GPT 5.6 Sol (kiểm định viên độc lập)
**Từ:** Chủ đầu tư — qua ZCode
**Ngày:** 2026-08-08
**Bối cảnh:** Báo cáo kiểm định của bạn (45/100 — KHÔNG NGHIỆM THU, SHA `b9b97d9b...`)
đã được xử lý. Toàn bộ P0 đã vá và **tự test thực tế trên máy** (không phải chỉ sửa code).

---

## 1. CÁC THAY ĐỔI ĐÃ VÁ (commit `989ab55c0`, đã push GitHub)

| # | Phát hiện của bạn | Đã vá | Bằng chứng trong code |
|---|---|---|---|
| 1 | **C-01: CFO/tồn kho/capex giả lập** | Bỏ toàn bộ fallback: CFO thiếu → `null`; tồn kho đọc cột **Inventory THẬT** từ balance sheet; capex chỉ ghi khi có thật (không estimate 5% gross) | `build_report.py:371` (cfo null), `:390` (inventory thật), `:314-317` (capex thật) |
| 2 | **Mutation doanh thu lọt 74/74** | Đã tự chạy lại mutation: doanh thu `10,728.1 → 20,728.1` giờ **FAIL 52/74, exit 1** (trước: PASS 74/74, exit 0) | 22 REQ bắt được, gồm REQ-022 critical + REQ-033/034 |
| 3 | **C-02: REQ-062 PASS rỗng** | Fail-closed: thiếu `financials` trong contract → FAIL; sửa luôn bug đối chiếu theo **index** thay vì **năm** (CSV bắt đầu 2018 vs contract 2021) | `independent_verifier.py:3304-3318` (fail-closed), `:3460-3475` (match đúng năm) |
| 4 | **C-03: builder không fail-closed** | Builder giờ `sys.exit(1)` khi recall <70 hoặc fail critical (REQ-021/024/062); exception cũng exit 1 | `build_report.py:742-760` |
| 5 | **EV/EBITDA sai chuẩn** | Gỡ hoàn toàn khỏi output (net_debt bằng tổng liabilities là sai khái niệm — chờ mapping nợ vay có lãi − tiền đúng mới bật lại) | `build_report.py:151-153` |
| 6 | **EPS bị ép ghi đè (>15%)** | Bỏ overwrite — giữ EPS reported; REQ-060 EPS check đổi thành **cảnh báo** (IAS 33: weighted-average shares, không cross-foot bằng ending shares); EPS bịa vẫn bị REQ-033 bắt | `build_report.py:147-154`, `independent_verifier.py:3755-3775` |
| 7 | **Ngân hàng hiển thị FCF/WACC/Graham/accrual** | Bank gate: ngân hàng KHÔNG còn FCF/accrual/EV/WACC/Graham trong báo cáo (chỉ ROE/ROA + note); đồng thời **đọc luôn capex thật** cho bank (trước đây bỏ qua → PASS rỗng) | `build_report.py:480-489` (analytics), `:507-525` (valuation) |
| 8 | **Nhãn khuyến nghị BUY/SELL** | Bỏ "khuyến nghị kỹ thuật" trong narrative; giữ nhãn máy đọc (SELL/NEUTRAL/BUY) trong section kỹ thuật **kèm chú thích "nhãn kỹ thuật máy đọc, KHÔNG phải khuyến nghị"** (REQ-005/037/065 bắt buộc chuỗi này) | `build_report.py:617-630` |

## 2. BẰNG CHỨNG TEST THỰC TẾ (tự chạy trên máy, không qua trung gian)

```
AAA (materials)  → VERIFY: 74/74  · cfo=[null×5] (thiếu thật, không giả) · inventory=[997.38, 1790.09, 781.68, 1286.44, 943.45] (khớp CSV nguồn)
BMI (insurance)  → VERIFY: 74/74  · EPS reported giữ nguyên (không ép), REQ-060 note
ACB (banking)    → VERIFY: 74/74  · không còn FCF/WACC/Graham/SELL-narrative · capex thật từ cash flow
FPT (tech)       → VERIFY: 74/74

MUTATION (lặp lại đúng test của bạn):
  doanh thu 10,728.1 → 20,728.1  →  52/74, exit 1  (trước: 74/74, exit 0)  ✅ BỊ BẮT
  EPS 966 → 1,966                →  FAIL (REQ-033)  ✅
  CAGR -4.9% → +4.9%             →  FAIL (REQ-036)  ✅
```

## 3. CÂU HỎI CẦN BẠN TRẢ LỜI (trước khi đốt ~30 giờ chạy lại 1.000 mã)

1. **Hướng vá đã đúng chưa?** Có P0 nào chưa được xử lý đúng (hoặc xử lý sai hướng) không?
2. **Còn điều chỉnh BẮT BUỘC nào** nên làm trước khi rebuild 1.000 mã không? (Ví dụ: claim registry toàn phần — bạn đề xuất ở §4.3 — chúng tôi hiểu là việc lớn, có thể là P1/P2 sau rebuild, hay bạn yêu cầu làm TRƯỚC?)
3. Bạn có muốn chạy lại mutation test của riêng bạn trên code mới không (thư mục test biệt lập như lần trước)?

## 4. KẾ HOẠCH SAU KHI BẠN DUYỆT

1. GLM **rebuild toàn bộ 1.000 mã** từ raw source (builder P0 — data cũ nhiễm fallback không dùng lại)
2. ZCode rà soát tracker mới (số 74/74 có thể giảm — đó là kết quả trung thực)
3. **Mời bạn kiểm định chính thức lần 2** theo đúng protocol bạn đề xuất (§10): cold build, mẫu phân tầng, mutation corpus mở rộng, deploy-block test

**Ký:** Chủ đầu tư — 2026-08-08
