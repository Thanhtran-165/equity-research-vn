# PHỐI HỢP ZCODE ↔ GLM — Quy tắc phân công (2026-08-01)

> Quyết định của chủ dự án: **GLM có ngân sách sub rất lớn** — từ nay, mọi công việc
> "harness" (nặng, tốn token, chạy pipeline/cohort/test lớn) do **GLM thực thi**.
> **ZCode** giữ vai trò: phân tích, thiết kế, **soạn lệnh**, review kết quả, quyết định.

## Phân công chuẩn

| Loại việc | Ai làm |
|---|---|
| Soạn lệnh/đặc tả, phân tích lỗi, review, quyết định sửa | **ZCode** |
| Chạy pipeline nhiều mã, cohort đa ngành, test E2E lớn, backtest rộng, build nặng | **GLM** (nhận lệnh từ file) |
| Việc nhỏ trong 1 file, 1 lỗi cụ thể, kiểm chứng nhanh | ZCode (tự làm) |

## Cơ chế ra lệnh

1. ZCode soạn file lệnh: `LENH-<TÊN>-CHO-GLM.md` tại `/Users/bobo/ZCodeProject/`
   — gồm: bối cảnh ngắn · nhiệm vụ chi tiết · quy trình bắt buộc · tuân thủ luật skill ·
   định dạng báo cáo · ràng buộc cấm · tiêu chí thành công
2. Chủ dự án chuyển file cho GLM (hoặc trỏ GLM đọc file)
3. GLM tạo báo cáo kết quả theo định dạng đã quy định
4. ZCode đọc báo cáo → phân loại lỗi skill/data/ngành → soạn lệnh sửa tiếp

## Lệnh đã giao / đang chạy

- `LENH-COHORT-CHO-GLM.md` — cold cohort 7 ngành (VCB, SSI, HPG, MWG, VHM, CTD, mã IPO mới)
  → báo cáo kỳ vọng: `/tmp/COHORT-REPORT-GLM.md` — ✅ xong, nhưng runner rút gọn → KHÔNG hợp lệ để đánh giá skill
- `LENH-CHAY-LAI-VCB-HPG-CHO-GLM.md` — V2: chạy lại VCB+HPG full 9 phase
  → báo cáo: `/tmp/COHORT-REPORT-GLM-V2.md` — ✅ xong: 44/73 (71% fail narrative — GLM dừng 1 vòng) + phát hiện verifier Title Case
  → ZCode đã vá: verifier case-insensitive + REQ-074 (74 REQ) + CFO 3 tên cột + bank gate
- `LENH-CHAY-LAI-V3-CHO-GLM.md` — V3: chạy lại VCB+HPG với vòng lặp fix bắt buộc (tối thiểu 2 vòng), nghiệm thu 2 fix
  → báo cáo kỳ vọng: `/tmp/COHORT-REPORT-GLM-V3.md` — ✅ xong: VCB 51/74, HPG 53/74 (3 vòng fix); REQ-074 PASS; fix case-insensitive hoạt động; phát hiện bug regex Unicode → ZCode đã vá (strip dấu NFD) + test 6/6
- `LENH-CHAY-SAU-HPG-V4-CHO-GLM.md` — V4: HPG chạy SÂU — 4-6 vòng fix (mục tiêu ≥68/74), điều kiện xét PRODUCTION_READY + mốc chuẩn VN100
  → báo cáo kỳ vọng: `/tmp/COHORT-REPORT-GLM-V4.md` — ✅ xong: peak 60/74 (vòng 2) → final 54/74; REQ-074 PASS 5 vòng; bài học: GLM thiếu format chuẩn → ZCode đã vá 2 bug verifier (REQ-069 unquoted keys, REQ-031 pattern "52 tuần"/dấu âm)
- `LENH-CHAY-LAI-HPG-V5-CHO-GLM.md` — V5: HPG chạy lại với MẪU FORMAT CHUẨN trích từ CTD (9 mục: DATA 67 keys, valuation, tech, risk, insight, split audit, citation, news, investment) — hết lý do đoán format
  → báo cáo kỳ vọng: `/tmp/COHORT-REPORT-GLM-V5.md` — ✅ xong: 63/74 (tăng +9 nhờ mẫu), REQ-074 PASS; 89% fail còn lại = CTD residuals (copy HTML CTD để sót số liệu) → ZCode thêm quy tắc cấm copy (phase6 Lesson #17) + pitfalls mục 15
- `LENH-DON-RESIDUAL-HPG-V6-CHO-GLM.md` — V6: HPG dọn SẠCH residual CTD (danh sách 15 số + 8 từ khóa để grep) + verify lại, mục tiêu ≥68/74 → quyết định PRODUCTION_READY
  → báo cáo kỳ vọng: `/tmp/COHORT-REPORT-GLM-V6.md` — ✅ xong: 64/74, residual = 0; GLM báo 5 "lỗi skill" → kiểm chứng: 2 bug verifier thật (ZCode đã vá: dấu âm CAGR, glossary/window/YoY trend) + 3 lỗi GLM (34% sót, P/B 0.74× residual, peer C4G/FCN/VCG); ZCode tự sửa thêm 7 chỗ HTML → **HPG 70/74**; còn REQ-062 = CSV source-pack GLM ghi cột Sales sai (56,580 vs 149,679 tỷ)
- `LENH-SUA-CSV-V7-CHO-GLM.md` — V7: GLM đối chiếu 3 CSV source-pack với data files + verify lại → mục tiêu ≥71/74 → chốt PRODUCTION_READY
  → báo cáo kỳ vọng: `/tmp/COHORT-REPORT-GLM-V7.md` — ✅ xong: **HPG 71/74** (0 critical/high fail); ZCode verify chéo xác nhận 71/74 + fix verifier REQ-062 substring "Sales deductions" (giờ tự chọn "Net sales" đúng kể cả CSV cũ)

## KẾT LUẬN COHORT (7 đợt, 2026-08-01)

- **PRODUCTION_READY: ĐẠT** — HPG (non-CTD, thép chu kỳ) 71/74, 0 critical/high fail; CTD 72/74; verifier sạch sau 3 đợt vá bug (case-insensitive, dấu âm, glossary/window, method skip, substring column)
- Hành trình: V1 46/73 (runner rút gọn ✗) → V2 44/73 → V3 53/74 → V4 54/74 → V5 63/74 → V6 64/74 → V7 71/74
- Bài học đã đóng vào skill: cấm copy báo cáo mã khác (Lesson #17), pitfalls mục 15, CFO 3 tên cột, bank gate, rate limit, P/E chuẩn hóa (REQ-074)
- Token/mã đo thật: ~55-70K → **VN100 ≈ 6-7M token**

## Lệnh đang chạy

- `LENH-VN100-CHO-GLM.md` — bản đầy đủ quy trình + goal
- `LENH-RUN-BUILDER-V9-CHO-GLM.md` — **V9**: chạy 71 mã bằng BUILDER CHUẨN (scripts/build_report.py, đã vá 3 REQ còn lại → VJC 74/74 + BID 74/74) → mục tiêu ≥60/71 mã ≥72/74 → báo cáo `/tmp/VN100-REPORT-V5.md`

## KẾT QUẢ VN100 (cập nhật 2026-08-02)

- Batch 1 (renderer GLM v4): avg 71.1/74, 24 mã 73/74 — nhưng chỉ 46% mã pass 3 REQ nguy hiểm (022/033/003)
- **ZCode đã vá**: 6 fix verifier (normalize EN/VN, 022 số âm, 033 contamination/bull-bear/unit ×, 031, 048, 055) + renderer 3 REQ → **VJC 74/74, BID 74/74** (PASS hoàn toàn), golden + suite PASS
- **BUILDER CHUẨN đã đóng vào skill**: `scripts/build_report.py` + phase6 Lesson #18 (cấm tự viết renderer)
- Skill vẫn CHƯA commit (quyết định backup riêng đang chờ)

## KẾT QUẢ VN100 BATCH 1 (2026-08-01, GLM sess_3b54417a)

- 73/73 mã status rõ (0 bỏ lửng, 0 bịa, data thật); recall avg 53.2/74 (0 mã ≥60); token ~3.6M (−45%)
- 12 REQ fail 100%: **2 bug verifier đã vá bởi ZCode** (REQ-031 cắt disclaimer + chặn "(" + bỏ triệu/tỷ; REQ-048 loại CFO khỏi keywords quản lý — PASS trên ACB + golden + 12/12 suite), **10 lỗi narrative generator** → giao V8
- Skill nguyên vẹn (hash khớp); tracker đầy đủ 73 mã chi tiết
- Đã commit + push `da7856212` (docs/evidence/lệnh) — skill nằm ngoài git (cần quyết định backup riêng)

## Backlog tiềm năng giao GLM (khi cần)

- Chạy lại CTD theo pipeline đã nâng cấp (nằm trong cohort)
- Backtest technical mở rộng nhiều mã (walk-forward, nhiều cohort → đủ mẫu đổi nhãn Tech Score)
- Cold-run các mutation/negative corpus mở rộng theo ngành
- Shadow rollout đo false-positive của deploy gate trên nhiều lần deploy giả

## Nguyên tắc

- GLM không sửa source skill trừ khi lệnh ghi rõ; mặc định cohort = chạy + báo cáo
- Không commit/push trừ khi chủ dự án duyệt
- Báo cáo phải phân loại rõ: lỗi skill / lỗi data / đặc thù ngành — không gộp chung
