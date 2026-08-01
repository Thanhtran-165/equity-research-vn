# LỆNH: CHẠY COLD COHORT ĐA NGÀNH CHO `equity-research-vn`

**Từ:** ZCode (phiên nâng cấp Wave 1–5)
**Giao cho:** GLM (phiên thực thi cohort)
**Ngày:** 2026-08-01

---

## 1. Bối cảnh (đọc trước — 2 phút)

Skill `equity-research-vn` trên ZCode đã qua nâng cấp Wave 1–5 (xem `CLOSEOUT-WAVE1-5.md`):
- **73 REQ** · 9 phases · registry lint OK · index tự sinh `references/req_index.md`
- Đã sửa: unit contract định giá (P0-01), FCFF/FCFE (P0-02), state machine (P0-03), bỏ shell=True (P0-04), deploy gate fail-closed (P0-05), no-internal-meta (REQ-070), zero-data (REQ-071), S/R realistic (REQ-072), text-structure (REQ-073)
- **12/12 test suite PASS** trong `scripts/tests/` — chạy trước khi bắt đầu: `cd ~/.zcode/skills/equity-research-vn/scripts/tests && for t in requirements-lint test_security_injection test_valuation_units test_predeploy_gate test_v5_negative test_fundamental_depth test_valuation_depth test_golden_e2e test_mutation_wave test_accessibility sentiment_calibration test_sector_applicability; do python3 $t.py; done`
- Maturity hiện tại: `QUALIFICATION_REQUIRED` (trung thực — chờ bằng chứng cohort)

## 2. NHIỆM VỤ (Wave 5 còn lại): cold cohort 7 ngành

Chạy pipeline đầy đủ cho **7 mã đại diện 7 nhóm** — mỗi mã trong **work dir riêng biệt** (KHÔNG dùng chung):

| # | Ngành | Ticker gợi ý | Lưu ý đặc thù |
|---|---|---|---|
| 1 | Ngân hàng | **VCB** | KHÔNG CCC/accrual CFO-based/FCFF/WACC corporate → dùng cost of equity, DDM/P/B (sector_method_registry.md) |
| 2 | Chứng khoán | **SSI** | Tài sản tài chính lớn — P/B chuẩn hóa; CCC null |
| 3 | Thép (chu kỳ) | **HPG** | P/E phải NORMALIZED (loại năm đáy); EV/EBITDA; CAGR đỉnh-đỉnh |
| 4 | Bán lẻ | **MWG** | CCC (DIO/DPO), SGR, PEG hợp lệ |
| 5 | BĐS | **VHM** | NAV/RNAV, DDM khi cổ tức ổn định; dở dang lớn |
| 6 | Nhà thầu | **CTD** (chạy lại bản mới) | CCC cao, vốn lưu động, CFO âm đặc trưng khi mở rộng; S/R realistic |
| 7 | Mã mới / ít lịch sử | 1 mã IPO gần đây (bạn chọn, ghi lý do) | Data ít → REQ "insufficient data" advisory hợp lệ; KHÔNG bịa số |

## 3. QUY TRÌNH BẮT BUỘC (mỗi mã)

1. **Khởi tạo:** `python3 ~/.zcode/skills/equity-research-vn/scripts/init_task_state.py <TICKER> <WORK_DIR>` (tạo thư mục mới mỗi mã: `/tmp/cohort_<TICKER>`)
2. **Chạy 9 phase theo `SKILL.md`** — mỗi phase: đọc prompt `phases/phaseN-*.md`, thu thập data qua `vn-financial-data-collector` (sponsor tier), phân tích qua sub-skills, **ghi result vào task-state.json** (tuân thủ `task-state.schema.json`)
3. **Verify từng phase** qua `scripts/run_phase.py <TICKER> <WORK_DIR> <phase_id>` — phase nào chỉ có REQ deferred → KHÔNG được tự ghi completed (P0-03)
4. **Final verify:** `python3 ~/.zcode/skills/equity-research-vn/scripts/independent_verifier.py <TICKER> <WORK_DIR>/<TICKER>_Complete_Report.html`
5. **Ghi kết quả** vào bảng báo cáo (mục 5)

## 4. TUÂN THỦ BẮT BUỘC (đã thành luật trong skill)

- **UNIT CONTRACT:** marketCap = price × shares_tỷ (KHÔNG /10); fairPrice = fairMarketCap / shares_tỷ — xem `valuation_formulas.md`
- **FCFF/FCFE:** KHÔNG gọi CFO−CapEx là FCFF; bridge EV−NetDebt=Equity; g < wacc
- **NO INTERNAL META (REQ-070):** narrative KHÔNG chứa tên phase/file JSON/task-state — nguồn dẫn = mô tả tiếng Việt + `{SRC('ref-N')}` (ẩn CSS)
- **S/R REALISTIC (REQ-072):** kháng cự ∈ [giá, +30%], hỗ trợ ∈ [−30%, giá]; mức xa → far_levels
- **ZERO DATA (REQ-071):** dataset toàn 0 → chart vẽ rỗng → FAIL — thiếu data ghi `null`, KHÔNG ghi 0
- **WACC:** mỗi input ghi NGÀY + NGUỒN (wacc_estimates.md protocol); beta từ phase 4a
- **Bẫy 5B:** split audit trong task-state; CP lệch >20% phải ghi rõ cause (split → restate, dilution → ghi chú) — REQ-003 tự recompute
- **Đơn vị:** số tiền = tỷ VND; giá/EPS/BVPS = VND/cp

## 5. BÁO CÁO (tạo `/tmp/COHORT-REPORT-GLM.md`)

Bảng theo mã:

| Ticker | Ngành | Recall | REQ fail (id + lý do 1 dòng) | Charts render | Ghi chú đặc thù ngành |
|---|---|---|---|---|---|

Sau bảng, tối thiểu:
1. **Lỗi hệ thống gặp phải** (nếu có): mô tả + tái hiện + đề xuất sửa — phân loại "lỗi skill" vs "lỗi data" vs "do ngành"
2. **Phát hiện theo ngành**: ngân hàng/chứng khoán có dùng đúng applicability không; thép P/E normalized không; CCC/SGR tính đúng không
3. **Đề xuất** cho phiên sửa tiếp theo (mỗi đề xuất gắn file + lý do)

## 6. RÀNG BUỘC (KHÔNG được làm)

- ✗ Sửa source skill (`~/.zcode/skills/equity-research-vn` + sub-skills) — cohort CHỈ chạy + báo cáo
- ✗ Sửa bản Codex / đồng bộ sang Codex
- ✗ Commit/push gì cả
- ✗ Bật enforced deploy gate
- ✗ Bịa số liệu khi API lỗi — ghi rõ "API fail" và dừng mã đó (đánh dấu `BLOCKED_API`)
- ✗ Dùng 1 work dir cho 2 mã (state đè nhau)

## 7. TIÊU CHÍ THÀNH CÔNG

- 7 mã chạy xong (hoặc ghi rõ mã nào BLOCKED_API/thiếu data — không giấu)
- Mỗi mã có evidence + verify đầy đủ
- Báo cáo phân loại rõ lỗi skill vs lỗi data — đây là INPUT cho phiên sửa tiếp theo
