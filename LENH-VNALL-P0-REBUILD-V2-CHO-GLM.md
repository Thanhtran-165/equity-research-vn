# LỆNH VNALL P0-REBUILD V2: TÁI SINH 1.000 MÃ (RUNNER MỚI + PREFLIGHT SECTOR)

**Từ:** ZCode
**Giao cho:** GLM
**Ngày:** 2026-08-08
**Lý do:** Sol checkpoint NO-GO lần 2 — đã vá P0-A..P0-F (commit `90883230b`). Bản vá
đã test: AAA/BMI/ACB/FPT 4/4 74/74, mutation ô bảng bị bắt (REQ-033, exit 1).

---

## 1. CẬP NHẬT (bắt buộc)

Từ repo `Thanhtran-165/equity-research-vn` (hoặc copy từ máy chủ):
- `scripts/build_report.py` (P0 checkpoint: CFO alias mở rộng, verdict_label, bank gate, bỏ segment % giả)
- `scripts/independent_verifier.py` (REQ-062 match-based + fail-closed 8 field, REQ-033 table-cell, REQ-059 CFO thật)
- `scripts/vnall_run_p0.py` (**RUNNER MỚI — dùng cái này, không dùng vnall_run.py cũ**)
- `references/sector_pack.md`, `vn-research-dashboard/assets/dashboard_template.html`

## 2. PILOT 8 MÃ (bắt buộc TRƯỚC khi chạy cả 1.000 — theo gate Sol)

Chạy bằng runner mới: `python3 scripts/vnall_run_p0.py <file 8 mã> --sleep 60`
8 mã: **AAA, ACB, BMI, FPT, AGG, SGR, 1 mã thiếu capex, 1 mã lỗ** (tự chọn 2 mã cuối
từ danh sách, note lý do chọn). Kiểm tra:
- Mỗi mã: `VERIFY: x/74` + status trong tracker (done/needs_human/NO_DATA) đúng với exit code;
- AGG phải vào pack BĐS (xem §4 preflight), BMI → insurance, SGR → đúng ngành thật;
- ACB (bank) KHÔNG còn FCF/WACC/Graham/segment % trong HTML.
Pilot sạch → mới chạy toàn bộ.

## 3. CHẠY TOÀN BỘ (tuần tự, ~30 giờ)

1. Tạo `/tmp/vnall_p0_batches/`: 5 file JSON, mỗi file ~200 mã
   `[{"ticker":"AAA","sector":"materials","batch":1}, ...]` — sector từ preflight §4.
2. Chạy từng batch: `python3 scripts/vnall_run_p0.py <batchN.json> --sleep 60`
   (runner tự: staging sạch, ghi tracker sau mỗi mã, done chỉ khi exit 0 + recall ≥70,
   crash giữa chừng → chạy lại lệnh, tracker nối tiếp — KHÔNG cần làm gì thêm).
3. Mã `NO_DATA`/`needs_human` → ghi đúng, KHÔNG dừng batch.

## 4. PREFLIGHT SECTOR (bắt buộc — P0-E)

Sector map cũ có lỗi đã biết (Sol xác nhận): AGG đang `finance` nhưng là BĐS An Gia;
BMI đang `finance` nhưng là bảo hiểm; SGR đang `banking` nhưng không phải ngân hàng.
Làm:
1. Script preflight: `Listing().all_symbols()` → ticker + tên công ty + ICB → map sang
   sector builder (đối chiếu bảng MAP trong `references/sector_pack.md`).
2. **Tên công ty phải khớp ngành**: với mỗi mã, tra tên (organ_name) — nếu tên chứa
   "ngân hàng"/"bank"/"chứng khoán"/"bảo hiểm"/"bất động sản"/"thép"... → kiểm tra
   sector map có khớp không; mâu thuẫn → ghi vào `/tmp/vnall_sector_fix.json`
   (danh sách mã cần sửa tay) và chuyển mã đó sang sector ĐÚNG.
3. Các mã không xác định được → `general` (pack 12) — KHÔNG tự đoán.
4. Lưu `/tmp/vnall_p0_sectors.json`: `{TICKER: sector}` cho 1.000 mã → dùng làm nguồn
   batch files.
5. Báo cáo trong `/tmp/VNALL-REPORT-P0.md`: số mã sector được hiệu chỉnh + danh sách.

## 5. BÁO CÁO `/tmp/VNALL-REPORT-P0.md`

1. Pilot 8 mã: bảng (ticker, sector, status, recall, exit) + xác nhận AGG/BMI/SGR đúng.
2. Toàn bộ: 1.000 mã → done/needs_human/NO_DATA, 74/74, avg recall.
3. So sánh với bản cũ (606 mã 74/74): bao nhiêu mã giữ/tụt + lý do (thiếu data thật).
4. Top-10 REQ fail + phân loại (lỗi data thật / lỗi builder cần ZCode).
5. Xác nhận mẫu: cfo/inventory trong `verified-dashboard-data.json` = thật hoặc null
   (5 mã: ngân hàng/industrial/materials/insurance/tech).
6. File tracker mới: `~/ZCodeProject/data/vnall/vnall_tracker_p0.json` (GHI ĐÈ sau
   khi audit bản cũ — giữ bản cũ nhãn `invalid` trước).

## 6. LƯU Ý

- **KHÔNG tự sửa builder/verifier/runner** — fail lạ → stack trace + ticker vào báo cáo.
- **KHÔNG dùng `--reuse`** và KHÔNG merge với `work/` cũ (runner P0 tự xử lý staging sạch).
- Mã `exit 1` là CHUẨN (fail-closed) — không phải lỗi runner.
- Xong → ZCode rà soát → mời GPT 5.6 Sol tái kiểm định chính thức.

**Ký:** ZCode — 2026-08-08
