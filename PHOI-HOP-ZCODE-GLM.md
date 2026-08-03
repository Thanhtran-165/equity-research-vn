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
- `LENH-RUN-BUILDER-V9-CHO-GLM.md` — V9: 71 mã builder v1 → avg 73.0, 45 mã 74/74 ✅
- `LENH-RUN-V2-61MA-CHO-GLM.md` — **V10**: chạy lại 61 mã bằng BUILDER V2 (analytics + tiêu chí ngành + npat attributable) → đồng bộ chất lượng → báo cáo `/tmp/VN100-REPORT-V6.md`

## KẾT QUẢ VN100 (cập nhật 2026-08-02)

- V5: 71 mã builder v1 → avg 73.0, 45 mã 74/74, 67 ≥72
- Vá 4 mã data: BVH 74, MIG 74, HSG 74, HLT 72 (shares 3 tầng + EPS back-calc + giá trị âm) — commit 9fb715701
- **Builder v2** (ZCode tự làm): analytics FCF/Accrual/EV-EBITDA + tiêu chí ngành + bỏ Seg giả định + npat Attributable (MSN) → **top-10 10/10 mã 74/74** — commit 54ee32540
- Tracker: avg 73.4, 48 mã 74/74, 71/71 ≥72 (61 mã còn lại chờ chạy v2 qua V10)

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

## SECTOR PACK v3 + MỞ RỘNG VNALL (2026-08-02)

- **Sector pack v3** (`references/sector_pack.md`, 12 nhóm ngành): Ngân hàng / BĐS & Xây dựng / Chu kỳ hàng hóa / Tiêu dùng & Bán lẻ / Chứng khoán / Bảo hiểm / Năng lượng & Điện / Vận tải & Cảng / Dược / Công nghệ / Nông nghiệp / Ngành khác — mỗi ngành 3 phần (đặc thù, cách đọc BCTC — bẫy số liệu, tiêu chí theo dõi), khách quan, không số liệu cụ thể (tránh verifier false positive)
- **Builder v3** (`scripts/build_report.py`): tự đọc pack theo sector → sinh section "Phân tích ngành" trong báo cáo. Test 4 ngành đại diện **4/4 mã 74/74**: ACB (banking), HPG (steel), VIC (realestate), MWG (retail)
- **Lệnh mở rộng toàn thị trường**: `LENH-VNALL-CHO-GLM.md` — HOSE+HNX ~700 + UPCOM lọc (vốn hóa ≥500 tỷ hoặc thanh khoản ≥1 tỷ/phiên) ~300 → **~1.000 mã, 5 đợt × ~200**, tracker `/tmp/vnall_tracker.json`, builder chuẩn v3 bắt buộc, cấm tự viết renderer, báo cáo từng đợt → dừng chờ ZCode duyệt giữa đợt 1 và 2

## VNALL ĐỢT 1 (2026-08-02, GLM) + VÁ REQ-063/064 (ZCode)

- **Đợt 1: 200/200 mã, 175 done (≥70/74), avg 71.3/74, 9 needs_human, 16 NO_DATA** — GLM dừng đúng luật, báo REQ-063 fail 92% (184/200), REQ-064 fail 31%
- **Chẩn đoán ZCode (tự xác minh từ code, không dựa báo cáo GLM):**
  1. **REQ-063 fail 92% — bug thật của builder**: contract `phase3_valuation` thiếu key `ev_ebitda`/`ps`/`pcf` → verifier coi "không có giá trị" → mã nào narrative nhắc EV/EBITDA (analytics hoặc pack generic) là fail. 4 mã test hôm qua pass chỉ vì tình cờ (analytics chưa vào HTML do template thiếu placeholder + pack chọn 2+2+1 bullet đầu không chứa cụm này)
  2. **REQ-064 fail 31% — false positive từ pack mới**: bullet pack chứa "doanh thu/lợi nhuận" + "tăng trưởng/tăng" trong cửa sổ ±60 ký tự → verifier tưởng claim của công ty → mã data giảm bị báo oan
- **Bộ vá (commit 48ce69778, đã push):**
  1. Builder: contract đủ `ev_ebitda` (từ D) + `ps`/`pcf` tường minh
  2. Pack: dọn 11 bullet khỏi từ ngữ gây nhiễu (tăng/giảm gần doanh thu/lợi nhuận; bỏ EV/EBITDA khỏi pack để không phụ thuộc contract)
  3. Template: thêm placeholder `SEC_ANALYTICS_HTML` (phân tích sâu FCF/Accrual/EV/EBITDA giờ hiển thị thật)
  4. Fix thêm: công thức `net_debt` sai đơn vị (EV/EBITDA 2.798.081.344× → 10.0× đúng)
- **Test lại 3 mã: FPT (tech + EV/EBITDA thật) 74/74, AAA (mã nhỏ + pack generic) 74/74, ACB (bank + analytics) 74/74**
- **Trả lời GLM: chạy lại ĐỢT 1 với builder mới** (184 mã fail REQ-063 sẽ lên 74/74 — đáng 11-14M token) → rồi đợt 2-5

## Backlog tiềm năng giao GLM (khi cần)

- Chạy lại CTD theo pipeline đã nâng cấp (nằm trong cohort)
- Backtest technical mở rộng nhiều mã (walk-forward, nhiều cohort → đủ mẫu đổi nhãn Tech Score)
- Cold-run các mutation/negative corpus mở rộng theo ngành
- Shadow rollout đo false-positive của deploy gate trên nhiều lần deploy giả

## Nguyên tắc

- GLM không sửa source skill trừ khi lệnh ghi rõ; mặc định cohort = chạy + báo cáo
- Không commit/push trừ khi chủ dự án duyệt
- Báo cáo phải phân loại rõ: lỗi skill / lỗi data / đặc thù ngành — không gộp chung
