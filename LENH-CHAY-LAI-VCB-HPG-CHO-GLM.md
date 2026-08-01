# LỆNH V2: CHẠY LẠI ĐÚNG QUY TRÌNH — VCB + HPG (FULL 9 PHASES)

**Từ:** ZCode (phiên nâng cấp Wave 1–5)
**Giao cho:** GLM (phiên thực thi)
**Ngày:** 2026-08-01

---

## 1. Bối cảnh (đọc trước — 3 phút)

Cohort V1 (7 mã) của bạn đã chạy xong (`/tmp/COHORT-REPORT-GLM.md`) nhưng **kết quả verify 46–47/73 KHÔNG được dùng** để đánh giá skill, vì bạn chạy bằng runner rút gọn (script fill template) thay vì pipeline đầy đủ. Chính báo cáo của bạn kết luận: *"26 REQ fail đồng nhất = lỗi runner rút gọn, không phải lỗi ngành"*.

**Câu hỏi chưa được trả lời:** agent chạy ĐÚNG pipeline trên mã khác CTD đạt recall bao nhiêu? (CTD baseline: **72/73 PASS** khi chạy đủ 9 phase).

**Lệnh này yêu cầu chạy LẠI ĐÚNG CÁCH trên 2 mã đại diện khó nhất:** VCB (ngân hàng) + HPG (thép chu kỳ).

## 2. NHIỆM VỤ

| # | Mã | Ngành | Vì sao chọn | Work dir |
|---|---|---|---|---|
| 1 | **VCB** | Ngân hàng | Nhóm khó nhất: cấu trúc bảng cân đối khác, có bug column mapping đã biết | `/tmp/cohort_v2_VCB` |
| 2 | **HPG** | Thép chu kỳ | Cần P/E normalized, CAGR đỉnh-đáy, EV/EBITDA | `/tmp/cohort_v2_HPG` |

## 3. QUY TRÌNH BẮT BUỘC (KHÁC LỆNH CŨ — ĐIỂM MẤU CHỐT)

**🚫 TUYỆT ĐỐI CẤM dùng runner rút gọn / script fill template kiểu cohort V1.**

Chạy đúng như một agent nghiên cứu thật:

1. Đọc `~/.zcode/skills/equity-research-vn/SKILL.md` → thực hiện 9 phase theo đúng thứ tự
2. Mỗi phase: đọc prompt `phases/phaseN-*.md` → thu thập/phân tích data qua **sub-skills thật** (`vn-financial-data-collector`, `vn-fundamental-analysis`, `vn-technical-analysis`, `vn-valuation-engine`, `vn-news-digest`, `vn-research-dashboard`) → ghi kết quả vào task-state.json (đúng `task-state.schema.json`)
3. Verify sau mỗi phase: `python3 ~/.zcode/skills/equity-research-vn/scripts/run_phase.py <TICKER> <WORK_DIR> <phase_id>`
4. **Final:** `python3 ~/.zcode/skills/equity-research-vn/scripts/independent_verifier.py <TICKER> <WORK_DIR>/<TICKER>_Complete_Report.html`
5. **Narrative PHẢI đầy đủ như báo cáo thật**: ≥ 3 insights sâu, citations đủ, chart data thật từ financials.json — đây là phần runner V1 bỏ sót làm rớt 26 REQ

## 4. XỬ LÝ VCB — BUG ĐÃ BIẾT (quan trọng)

- Triệu chứng đã ghi nhận: API trả column names **UPPERCASE** (`'TOTAL ASSETS'`, `"OWNER'S EQUITY"`) còn script tìm Title Case → `equity_ty` rỗng → ROE/PB = 0
- **ZCode đang sửa song song ở skill gốc. BẠN KHÔNG ĐƯỢC sửa file skill gốc** (kể cả sub-skills)
- Nếu vẫn gặp lỗi: tự workaround **cục bộ trong phiên chạy của bạn** (ví dụ: chuẩn hóa tên cột về chữ thường khi đọc data) và **GHI RÕ vào báo cáo**: triệu chứng + cách bạn xử lý + có pass không → để ZCode đối chiếu với fix chính thức
- Nhớ đặc thù ngân hàng theo `sector_method_registry.md`: revenue = `Total Operating Income` (không có Net sales), **skip CCC/FCFF/WACC corporate**, dùng cost of equity + P/B + DDM

## 5. TUÂN THỦ LUẬT SKILL (giữ nguyên như lệnh cũ)

- **UNIT CONTRACT:** marketCap = price × shares_tỷ; fairPrice = fairMarketCap / shares_tỷ (`valuation_formulas.md`)
- **FCFF/FCFE:** không gọi CFO−CapEx là FCFF; bridge EV−NetDebt=Equity; g < wacc
- **NO INTERNAL META (REQ-070):** narrative không chứa tên phase/file JSON/task-state
- **S/R REALISTIC (REQ-072):** kháng cự ∈ [giá, +30%], hỗ trợ ∈ [−30%, giá]
- **ZERO DATA (REQ-071):** thiếu data ghi `null`, KHÔNG ghi 0
- **WACC:** mỗi input ghi NGÀY + NGUỒN (wacc_estimates.md)
- **Split audit:** CP lệch >20% ghi rõ cause (split → restate; dilution → ghi chú) — REQ-003 tự recompute
- **HPG đặc thù:** P/E phải NORMALIZED (loại năm đáy 2023); CAGR đỉnh-đỉnh giải thích chu kỳ
- Đơn vị: số tiền = tỷ VND; giá/EPS/BVPS = VND/cp

## 6. BÁO CÁO (tạo `/tmp/COHORT-REPORT-GLM-V2.md`)

Bảng theo mã:

| Ticker | Recall | REQ fail (id + lý do 1 dòng) | Charts render | Token ước tính | Ghi chú |
|---|---|---|---|---|---|

**Token ước tính:** ghi rõ phương pháp ước lượng (vd: số lượt gọi model × context trung bình theo ngưỡng window của bạn) — con số này dùng để dự toán mở rộng VN100, nên càng sát càng tốt.

Sau bảng, tối thiểu:
1. **So sánh với CTD baseline 72/73** — phần chênh là gì
2. **Phân loại TỪNG REQ fail**: lỗi skill (verifier sai/cứng) / lỗi data (API, mapping) / lỗi narrative (agent làm thiếu) / đặc thù ngành (cần rule riêng) — không gộp chung
3. **VCB column mapping:** sau workaround của bạn, lỗi còn hay hết? REQ nào bị ảnh hưởng?
4. **HPG P/E normalized:** verifier hiện chỉ check P/E raw — ghi rõ nếu thiếu check normalized (đề xuất REQ mới nếu cần)

## 7. RÀNG BUỘC (KHÔNG được làm)

- ✗ Sửa source skill gốc (`~/.zcode/skills/equity-research-vn` + sub-skills) — ZCode đang sửa song song
- ✗ Dùng runner rút gọn / template fill kiểu V1
- ✗ Bỏ phase nào (kể cả phase6 dashboard + phase7 deploy — cần đủ để verify charts)
- ✗ Commit/push gì cả
- ✗ Bịa số liệu khi API lỗi — ghi `BLOCKED_API` + triệu chứng

## 8. TIÊU CHÍ THÀNH CÔNG

- 2 mã chạy đủ 9 phase, evidence + verify đầy đủ (không ai bỏ phase)
- Recall báo cáo là con số THẬT của pipeline đầy đủ (không cần cao — cần thật và phân loại rõ)
- Mọi REQ fail được phân loại skill/data/narrative/ngành — đây là INPUT cho phiên sửa tiếp theo
