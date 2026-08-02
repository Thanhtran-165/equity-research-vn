# LỆNH VN100 (BẢN ĐẦY ĐỦ) — 100 MÃ VN100: QUY TRÌNH + GOAL + CHỐNG BỎ CUỘC

**Từ:** ZCode · **Giao cho:** GLM · **Ngày:** 2026-08-01
**File này là DUY NHẤT** — đọc hết trước khi bắt đầu, không cần file nào khác.

---

## 1. BỐI CẢNH (đọc trước — 5 phút)

Skill `equity-research-vn` v3.2.0 (74 REQ) đã **PRODUCTION_READY**: CTD 72/74, HPG 71/74 (0 critical/high fail, verify chéo bởi ZCode). Quy trình chuẩn đã chứng minh qua 7 đợt cohort: 9 phase đầy đủ + vòng fix + checklist narrative + **cấm copy báo cáo mã khác** (Lesson #17). Token/mã đo thật ~55-70K → 100 mã ≈ 6-7M token.

**Nhiệm vụ: chạy 100 mã VN100 theo quy trình chuẩn đó. KHÔNG chạy lại CTD/HPG (đã có — liệt kê trong tracker với status `done_reference`).**

## 2. DANH SÁCH MÃ

- Lấy danh sách VN100 **thật tại thời điểm chạy**: `Listing` VCI hoặc `Quote(symbol='VN100')` constituents; nếu không có → `Listing.all_symbols()` + lọc top ~100 theo vốn hóa, **GHI RÕ phương pháp** vào tracker
- Lưu danh sách vào `/tmp/vn100_tracker.json` trước khi chạy (mọi mã status `pending`)

## 3. PHÂN ĐỢT (chống mệt mỏi + mất chất lượng)

- **5 đợt × 20 mã.** Sau mỗi đợt: dừng, đọc lại checklist mục 6, ghi tiến độ `/tmp/vn100_progress_<đợt>.md`
- Mỗi mã: work dir riêng `/tmp/vn100_<TICKER>`; sau khi ghi tracker xong → **xóa work dir, CHỈ GIỮ** `/tmp/vn100_reports/<TICKER>_Complete_Report.html`
- **Rate limit (luật skill)**: chạy TUẦN TỰ, `sleep(60)` giữa các mã, `fetch_with_retry` 3 lần; hết vẫn fail → xử lý theo mục 5.3

## 4. QUY TRÌNH MỖI MÃ

1. `init_task_state.py <TICKER> /tmp/vn100_<TICKER>` → 9 phase theo SKILL.md (sub-skills thật)
2. **DỪNG SỚM**: phase 0-2 fail vì data (API chết, mã hủy niêm yết, data <3 năm) → xử lý theo mục 5.3, KHÔNG chạy tiếp (tiết kiệm token)
3. Build dashboard → verify `independent_verifier.py` → **tối thiểu 2 vòng fix, tối đa 4 vòng** (đọc fail → sửa → verify lại)
4. Ghi tracker + copy report vào `/tmp/vn100_reports/`

## 5. TỰ SỬA & NỐI LẠI — CHỐNG BỎ CUỘC (BẮT BUỘC, bài học 7 đợt cohort)

### 5.1. Tracker-first (nguồn sự thật duy nhất)
- **Ghi `/tmp/vn100_tracker.json` NGAY SAU mỗi mã** (không gom cuối đợt): ticker, industry, status, recall, fail_reqs, charts, token_est, notes
- Bị gián đoạn (crash, hết context, lỗi): **phiên mới mở tracker trước** → nối tiếp từ mã dang dở, **TUYỆT ĐỐI không chạy lại mã đã xong**
- Mã dang dở: đọc work dir cũ → verify lại → tiếp tục vòng fix, KHÔNG khởi tạo lại

### 5.2. FAIL không phải lý do dừng — là lý do sửa
- Fail lặp CÙNG REQ 2 vòng liên tiếp → KHÔNG bỏ: đổi chiến lược 1 lượt (a) mở mẫu `/Users/bobo/ZCodeProject/ctd-v4flash/CTD_Complete_Report.html` + `/tmp/cohort_v3_HPG/HPG_Complete_Report.html` xem format đúng, (b) đọc checklist mục 6, (c) sửa theo REQ evidence chi tiết → verify vòng 3
- Hết 4 vòng vẫn fail → ghi `needs_human` + bằng chứng (evidence + đoạn HTML) → sang mã khác, **PHẢI quay lại mã đó cuối đợt** verify lần cuối

### 5.3. NO_DATA / BLOCKED_API — thử lại trước khi bỏ
- Fail vì API (rate limit, connection) → **chuyển xuống cuối đợt, thử lại SAU khi chạy thêm 5 mã** — chỉ ghi nhận `BLOCKED_API` sau lần thử thứ 2
- Mã hủy niêm yết / data < 3 năm → `NO_DATA` + lý do cụ thể

### 5.4. Tự fix trong phạm vi được phép
- Được tự do sửa narrative/HTML/data trong work dir của mình
- Nghi lỗi skill → KHÔNG chờ, KHÔNG sửa skill: ghi `needs_human` + bằng chứng → **tiếp tục mã khác** (ZCode vá song song)
- Gián đoạn giữa đợt → ghi 1 dòng vào `/tmp/vn100_progress_<đợt>.md` ("dừng tại mã X, lý do Y") TRƯỚC khi dừng

## 6. CHECKLIST BẮT BUỘC (mỗi mã — bài học 7 đợt cohort)

- [ ] **CẤM copy HTML mã khác** — build từ `dashboard_template.html` TRẮNG + fill data đúng ticker; sau build **grep residual** (ticker khác + số đặc trưng các mã đã chạy — bài học V5/V6: PE 7.9, P/B 0.74, peer nhà thầu C4G/FCN/VCG sót vào HPG)
- [ ] Narrative: section ≥ 200 ký tự; ≥ 3 insights ≥ 500 ký tự; mỗi số key có nguồn NAMED cùng câu (vd "theo BCTC kiểm toán 2025")
- [ ] DATA object đủ keys (tham chiếu mẫu CTD 67 keys: revenue, netProfit, equity, totalAssets, peHist, pe5med, techMA10/20/50, ddValues, distBins...)
- [ ] REQ-070: không lộ meta nội bộ (tên phase/file JSON/task-state)
- [ ] REQ-072: S/R trong ±30% giá; REQ-071: thiếu data ghi `null` KHÔNG ghi 0
- [ ] REQ-074 (nếu EPS chu kỳ: CV > 30% VÀ EPS < 80% đỉnh 5 năm): trình bày P/E chuẩn hóa bên cạnh P/E raw
- [ ] Ngân hàng: revenue = Total Operating Income, skip CCC/FCFF, P/B + DDM (sector_method_registry.md)
- [ ] Split audit log đầy đủ (cp_consistent, method, periods_checked); WACC có ngày + nguồn; đơn vị tỷ VND
- [ ] Drawdown claim PHẢI khớp max_drawdown data (±15pp) hoặc có "ước tính"

## 7. GOAL — HỢP ĐỒNG KẾT QUẢ (điều gì ĐÚNG khi xong)

| # | Ngưỡng | Bằng chứng |
|---|---|---|
| 1 | **100/100 mã có status cuối rõ ràng** ∈ {done, needs_human, NO_DATA, BLOCKED_API} — 0 mã bỏ lửng | `/tmp/vn100_tracker.json` đủ 100 dòng |
| 2 | **≥ 60/100 mã recall ≥ 60/74** | tracker + reports HTML |
| 3 | **needs_human ≤ 10 mã**, mỗi mã kèm bằng chứng (REQ id + evidence + đoạn HTML) | tracker notes |
| 4 | REQ-074 PASS trên mọi mã kích hoạt (EPS chu kỳ) | evidence từng mã |
| 5 | Tổng token thực tế ghi rõ (so dự toán 6-7M, ±30% chấp nhận) | báo cáo cuối |
| 6 | `/tmp/VN100-REPORT.md` đầy đủ (mục 9) | file tồn tại |

## 8. RÀNG BUỘC (KHÔNG được làm)

- ✗ Sửa source skill gốc — nghi lỗi skill → ghi `needs_human` + bằng chứng (mục 5.4)
- ✗ Copy HTML giữa các mã (dù cùng ngành)
- ✗ Commit/push gì cả
- ✗ Bịa số liệu khi API lỗi — ghi `BLOCKED_API` + triệu chứng
- ✗ Chạy song song nhiều mã (rate limit)
- ✗ Bỏ phase nào (trừ dừng sớm mục 4.2)
- ✗ Dừng mã vì "fail nhiều" (4 vòng fix là luật)
- ✗ Nói "không làm được" mà không kèm bằng chứng + phương án (ghi needs_human + tiếp tục là phương án mặc định)

## 9. BÁO CÁO CUỐI (tạo `/tmp/VN100-REPORT.md` khi xong 100 mã — hoặc khi hết context, báo cáo phần đã xong vào progress file)

1. **Bảng 100 mã**: Ticker | Ngành | Status | Recall | REQ fail (id) | Charts | Token est
2. **Thống kê**: số mã ≥ 65/74; recall trung bình; tổng token thực tế
3. **Top-10 REQ fail theo tần suất** (input cho đợt vá skill)
4. **Phân loại lỗi**: skill (kèm bằng chứng + 3 ví dụ mã) / data (API, mapping) / đặc thù ngành
5. **10 mã "cơ hội"** (recall cao + định giá hấp dẫn) — đây là output chính người dùng dùng

## 10. FILE ĐẦU RA (tên file CỤ THỂ — ghi đúng tên này)

| File | Nội dung | Ghi khi nào |
|---|---|---|
| `/tmp/vn100_tracker.json` | 100 mã × (ticker, industry, status, recall, fail_reqs, charts, token_est, notes) | Sau mỗi mã |
| `/tmp/vn100_reports/<TICKER>_Complete_Report.html` | Báo cáo mọi mã done | Sau mỗi mã |
| `/tmp/vn100_progress_<đợt>.md` | Tiến độ từng đợt + điểm dừng khi gián đoạn | Cuối mỗi đợt / khi dừng |
| `/tmp/VN100-REPORT.md` | Báo cáo cuối (mục 9) | Khi xong 100 mã |

## 11. TIÊU CHÍ THÀNH CÔNG

- 100/100 mã có status cuối (0 bỏ lửng) — tracker là nguồn sự thật
- ≥ 60/100 mã recall ≥ 60/74; mọi fail phân loại rõ
- Báo cáo mục 9 đầy đủ — input cho phiên vá skill đợt VN100
- Tổng token ghi rõ → đối chiếu dự toán 6-7M
