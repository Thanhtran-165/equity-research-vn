# LỆNH V4: HPG CHẠY SÂU — 5 VÒNG FIX (MỤC TIÊU ≥ 65/74)

**Từ:** ZCode (phiên nâng cấp Wave 1–5 + fix cohort V2/V3)
**Giao cho:** GLM (phiên thực thi)
**Ngày:** 2026-08-01

---

## 1. Bối cảnh (đọc trước — 3 phút)

Chuỗi cohort đã xác lập:

| Đợt | Kết quả | Kết luận |
|---|---|---|
| V1 | 46-47/73 (runner rút gọn) | Không hợp lệ — lỗi cách chạy |
| V2 | VCB 44/73, HPG 44/73 (1 vòng) | 71% fail narrative — GLM dừng 1 vòng |
| V3 | VCB **51/74**, HPG **53/74** (3 vòng fix) | ~55% fail narrative — GLM 3 vòng < Flash 5 vòng (72/74) |

**REQ-074 (P/E chuẩn hóa) đã nghiệm thu PASS trên HPG** (pe_raw 11,0× + pe_norm 12,39×). Fix case-insensitive đã hoạt động. Bug regex Unicode đã được ZCode vá (strip dấu tiếng Việt).

**Mục tiêu lệnh này:** chứng minh recall ≥ 65/74 trên mã non-CTD khi agent làm ĐỦ SÂU (như Flash) — đây là điều kiện cuối để xét nâng maturity lên PRODUCTION_READY, và là mốc chuẩn cho kế hoạch VN100.

## 2. NHIỆM VỤ

**1 mã duy nhất: HPG** (thép chu kỳ) — ứng viên tốt nhất từ V3 (53/74, REQ-074 đã PASS, data đúng).

Work dir: **tái sử dụng `/tmp/cohort_v3_HPG`** nếu còn (data đã fetch + đã verify đúng — tiết kiệm API calls). Nếu không còn → tạo `/tmp/cohort_v4_HPG` mới và fetch lại theo quy tắc rate limit.

## 3. QUY TRÌNH BẮT BUỘC — VÒNG LẶP FIX SÂU

1. **Không chạy lại phase 0-4** nếu dùng lại work dir v3 (data + fundamental + valuation + technical đã có và đúng). Tập trung sửa **phase 5 (news), phase 6 (dashboard/narrative), phase 7 (deploy)**.
2. **Verify lần 0:** `python3 ~/.zcode/skills/equity-research-vn/scripts/independent_verifier.py HPG <WORK_DIR>/HPG_Complete_Report.html` — ghi lại danh sách fail xuất phát
3. **VÒNG LẶP FIX: tối thiểu 4 vòng, tối đa 6 vòng** (Flash đạt 72/74 sau 5 vòng — bạn phải theo kịp):
   - Mỗi vòng: đọc TỪNG REQ fail → sửa report (narrative, citations, DATA arrays, structure) → verify lại
   - Ghi log mỗi vòng: vòng số mấy, sửa REQ nào, kết quả
   - **KHÔNG được dừng ở vòng 1-2** dù mệt — đây chính là lý do 2 đợt trước chưa đạt
4. **Điều kiện dừng:** recall ≥ 68/74 (trên ngưỡng 65, dưới CTD 72) HOẶC hết 6 vòng → báo cáo trung thực

## 4. DANH SÁCH REQ FAIL CỦA HPG TỪ V3 (sửa ưu tiên theo thứ tự)

Từ báo cáo V3, HPG fail các REQ sau (đối chiếu với verify lần 0 — có thể đã đổi):

**Nhóm narrative (ưu tiên cao nhất — 60% fail):**
- REQ-003: split audit — task-state đủ keys + report mention đúng format
- REQ-005/006: sec-tech + sec-tech-profile — Tech Score SỐ + Verdict + 15 block profile
- REQ-008: sec-news — sentiment score SỐ + category breakdown
- REQ-013: section content ≥ 200 ký tự (mọi section chính)
- REQ-014: insights — đúng section id cấu trúc template
- REQ-015: sec-risk — content đầy đủ
- REQ-029: citation — mỗi số key có nguồn NAMED cùng câu
- REQ-031: drawdown — số cụ thể từ data 52 tuần, KHÔNG còn chữ "ước tính"
- REQ-034: temporal — claim theo năm khớp đúng năm data
- REQ-038: claim basis — "Top X" claim có số liệu gần
- REQ-041: news window — articles có date hợp lệ
- REQ-042: investment amount 1 tỷ trong đúng section
- REQ-047: macro citation — "giá thép" phải cite nguồn vĩ mô
- REQ-048: management claim — "CEO/CTO" cite nguồn
- REQ-063: valuation methods — thép chu kỳ PHẢI có EV/EBITDA + giải thích P/E normalized (REQ-074 đã pass — đừng phá)
- REQ-064: trend — "giảm/tăng" gán đúng context

**Nhóm data consistency (sửa ở cả data file LẪN DATA array trong HTML):**
- REQ-023: DATA array trong HTML PHẢI khớp balance_sheet.json (key + value — đây là lỗi bạn copy data sai, không phải verifier)
- REQ-024: capex khớp cash_flow.json
- REQ-036: CAGR recompute — kiểm tra số trong report đúng bằng công thức verifier
- REQ-037: technical_active.json — verifier đọc verified-dashboard-data.json — đồng bộ 2 file
- REQ-059: cash_flow.json CFO — dùng đúng 1 trong 3 tên cột, lưu raw_field_name

**Nhóm skill/regex (nếu vẫn fail → ghi RÕ để ZCode xử lý — ĐỪNG tự sửa skill):**
- REQ-011 (canvas height-wrapper), REQ-019 (JS syntax), REQ-025 (P/E extract pattern), REQ-062 (period integrity), REQ-069 (runtime render), REQ-071 (zero-data)

## 5. CHECKLIST NARRATIVE DEPTH (kiểm từng mục trước mỗi vòng verify)

| # | Mục | Chuẩn đạt |
|---|---|---|
| 1 | Section content | Mỗi section chính ≥ 200 ký tự thật |
| 2 | Insights | ≥ 3 insights, mỗi insight ≥ 500 ký tự, có số liệu + nguồn |
| 3 | Citations | Mỗi số key (PE/PB/CAGR/ROE/doanh thu/CFO...) có nguồn NAMED cùng câu |
| 4 | Chart DATA | Mảng DATA khớp financials.json/balance_sheet.json/cash_flow.json (key + value), ≥ 13 canvas render |
| 5 | Investment amount | Số 1 tỷ đồng trong narrative sec-investment |
| 6 | Max drawdown | Số cụ thể từ data 52 tuần |
| 7 | News | Sentiment SỐ + category breakdown |
| 8 | Tech | Tech Score SỐ + Verdict, khớp technical_active.json |
| 9 | Split audit | task-state đủ keys + report mention đúng |
| 10 | References | ≥ 10 citations `[ref-N]` có nguồn tương ứng |
| 11 | P/E chuẩn hóa | Giữ NGUYÊN phần REQ-074 đã pass: "P/E chuẩn hóa = 12,39×" bên cạnh "P/E 11,0×" |
| 12 | Macro | Giá thép/giá quặng sắt có nguồn + ngày |

## 6. TUÂN THỦ LUẬT SKILL (giữ nguyên)

- UNIT CONTRACT: marketCap = price × shares_tỷ; fairPrice = fairMarketCap / shares_tỷ
- FCFF/FCFE: không gọi CFO−CapEx là FCFF; bridge EV−NetDebt=Equity; g < wacc
- NO INTERNAL META (REQ-070): narrative không chứa tên phase/file JSON/task-state
- S/R REALISTIC (REQ-072): kháng cự ∈ [giá, +30%], hỗ trợ ∈ [−30%, giá]
- ZERO DATA (REQ-071): thiếu data ghi `null`, KHÔNG ghi 0
- WACC: mỗi input ghi NGÀY + NGUỒN
- Đơn vị: số tiền = tỷ VND; giá/EPS/BVPS = VND/cp

## 7. BÁO CÁO (tạo `/tmp/COHORT-REPORT-GLM-V4.md`)

| Hạng mục | Nội dung |
|---|---|
| Recall cuối | x/74 + biểu đồ tiến trình theo vòng (vòng 0: 53 → vòng 4: ...) |
| REQ fail cuối | id + lý do 1 dòng + phân loại (skill/data/narrative) |
| Vòng log | Bảng: vòng | REQ sửa | Recall sau vòng |
| Token | Token ước tính tổng (fetch/build/5-6 verify+fix) |
| Maturity | Có đủ bằng chứng nâng PRODUCTION_READY? (đạt ≥65/74 = CÓ, dưới = CHƯA + vì sao) |
| Nhóm skill còn fail | Liệt kê REQ nào nghi do verifier/skill (KHÔNG sửa — chỉ báo cáo) |

## 8. RÀNG BUỘC (KHÔNG được làm)

- ✗ Sửa source skill gốc (`~/.zcode/skills/equity-research-vn` + sub-skills) — nghi lỗi skill thì GHI RÕ trong báo cáo
- ✗ Dùng runner rút gọn / template fill
- ✗ Dừng trước vòng 4 (vòng lặp fix tối thiểu 4 vòng)
- ✗ Bỏ phase nào
- ✗ Commit/push gì cả
- ✗ Bịa số liệu khi API lỗi — ghi `BLOCKED_API` + triệu chứng

## 9. TIÊU CHÍ THÀNH CÔNG

- **HPG ≥ 68/74** (mục tiêu tham chiếu Flash 72/74) — hoặc nếu không đạt: log đầy đủ 4-6 vòng + phân loại TỪNG fail còn lại
- REQ-074 vẫn PASS (không bị vòng sửa sau phá)
- Báo cáo kết luận rõ: đủ/không đủ bằng chứng PRODUCTION_READY
