# LỆNH V7: SỬA CSV SOURCE-PACK + VERIFY LẠI HPG (MỤC TIÊU ≥ 71/74)

**Từ:** ZCode
**Giao cho:** GLM
**Ngày:** 2026-08-01

---

## 1. Bối cảnh (đọc trước — 2 phút)

Sau V6, ZCode đã tự kiểm chứng và sửa trên `/tmp/cohort_v3_HPG`:

**ZCode đã sửa (KHÔNG cần đụng lại):**
- Verifier skill: 4 fix (REQ-036 dấu âm CAGR, REQ-025 skip "method", REQ-064 cắt glossary + window + YoY check) — bản skill hiện tại trên máy
- HTML HPG: dọn 7 residual (--18.2%, 34%, bảng peer C4G/FCN/VCG, P/B 0.74×→1.30×, "tăng 110%"→28.5%, tách đoạn 302 ký tự)

**Kết quả hiện tại: HPG 70/74** — fail còn: REQ-021 (hệ quả), REQ-050/051 (advisory), **REQ-062 (duy nhất là lỗi data CSV của bạn)**.

**Lỗi REQ-062 (ZCode đã xác định nguyên nhân):**
- `source-pack/income_statement_sponsor.csv` cột **"Sales"** ghi 2021 = **56,580 tỷ** — SAI
- Giá trị đúng: HPG 2021 doanh thu = **149,679 tỷ** (đã khớp: financials.json = verified-dashboard-data.json = 149,679)
- Verifier so CSV (raw) vs contract → bắt đúng mâu thuẫn → REQ-062 FAIL

## 2. NHIỆM VỤ (1 việc duy nhất)

1. **Đối chiếu toàn bộ 3 CSV** trong `/tmp/cohort_v3_HPG/source-pack/` (income, balance, cash_flow) với các file data đã đúng:
   - `income_statement_sponsor.csv` ↔ `data/financials.json` (revenue, npatmi, eps)
   - `balance_sheet_sponsor.csv` ↔ `data/balance_sheet.json` (total assets, equity)
   - `cash_flow_sponsor.csv` ↔ `data/cash_flow.json` (CFO, capex)
2. **Sửa CSV** cho khớp (mọi giá trị annual ±1%). Nghi ngờ cột nào (Sales vs Net sales, đơn vị, dòng năm) → fetch lại từ vnstock để lấy đúng
3. **Verify lại:** `python3 ~/.zcode/skills/equity-research-vn/scripts/independent_verifier.py HPG /tmp/cohort_v3_HPG/HPG_Complete_Report.html`

## 3. QUY TẮC BẮT BUỘC

- **KHÔNG đụng HTML** `/tmp/cohort_v3_HPG/HPG_Complete_Report.html` (bản hiện tại đang 70/74 — chỉ sửa CSV)
- **KHÔNG sửa source skill** — nghi lỗi verifier → ghi rõ bằng chứng, không tự sửa
- Nếu sau sửa CSV mà vẫn còn REQ fail khác phát sinh → verify lại và báo cáo (đừng sửa bừa)
- Không commit/push gì cả

## 4. BÁO CÁO (tạo `/tmp/COHORT-REPORT-GLM-V7.md` — NGẮN, 10 dòng)

| Hạng mục | Nội dung |
|---|---|
| Recall cuối | x/74 |
| CSV đã sửa | Cột nào, giá trị cũ → mới (nguồn đối chiếu) |
| REQ-062 | PASS/FAIL + lý do nếu fail |
| REQ-074 | PASS/FAIL (phải giữ PASS) |
| Kết luận | Đủ bằng chứng PRODUCTION_READY? (≥65/74 hard pass = CÓ) |

## 5. TIÊU CHÍ THÀNH CÔNG

- **HPG ≥ 71/74**, REQ-062 PASS, REQ-074 PASS → ZCode chốt PRODUCTION_READY + khởi động kế hoạch VN100
- Nếu CSV vẫn lệch sau khi đối chiếu → ghi rõ số liệu thật từ vnstock (không đoán)
