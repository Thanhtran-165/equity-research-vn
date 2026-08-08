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

## 3. CHẠY THEO LÔ NGÀNH (tuần tự — mỗi lô xong DỪNG chờ ZCode rà)

**KHÔNG chạy trộn 5 batch 200 mã.** Chia theo NHÓM NGÀNH — lỗi hệ thống thường lộ
theo đặc thù ngành (vd bảo hiểm nhiều cột doanh thu, ngân hàng không inventory, BĐS
ghi nhận theo dự án) → chạy hết 1 ngành, bắt lỗi + ZCode vá 1 lần → các mã còn lại
cùng ngành đều được lợi.

### 3a. Chia lô (theo sector từ preflight §4)

| Lô | Nhóm ngành (sector builder) | Khoảng số mã |
|---|---|---|
| 1 | banking + insurance | ~30 |
| 2 | realestate | ~80 |
| 3 | materials (thép/phân bón/xi măng/hóa chất) | ~120 |
| 4 | consumer + retail | ~240 |
| 5 | industrial (phần 1) | ~170 |
| 6 | industrial (phần 2) | ~170 |
| 7 | energy | ~90 |
| 8 | securities + pharma + tech + transport + nông + general | ~100 |

(Số mã thực tế theo `/tmp/vnall_p0_sectors.json` — chia lại cho khớp, mỗi lô ≤250 mã.)

### 3b. Quy trình mỗi lô

1. Tạo `/tmp/vnall_p0_batches/<LO>.json` (vd `batch_banking.json`) — chỉ mã thuộc lô đó.
2. Chạy: `python3 scripts/vnall_run_p0.py <file lô> --sleep 60`
   (runner tự: staging sạch, tracker sau mỗi mã, done chỉ khi exit 0 + recall ≥70,
   crash giữa chừng → chạy lại lệnh, tracker nối tiếp).
3. **XONG LÔ → DỪNG** → viết `/tmp/VNALL-LO-<TÊN LÔ>.md` (template §5b) → gửi ZCode rà.
4. **Chờ ZCode OK mới chạy lô kế.** Không tự ý nối tiếp dù lô sạch.

### 3c. Kỳ vọng theo ngành (để so sánh khi báo cáo)

- banking/insurance: ≥90% done (đặc thù đã test ACB/BMI)
- materials/energy/industrial: ≥85% done
- consumer/retail/realestate: ≥80% (data phức tạp hơn)
- Nếu lô nào tụt dưới 70% done → nghi lỗi ngành → CB-3 xem xét.

### 3d. Lưu ý

- Mã `NO_DATA`/`needs_human` → ghi đúng, KHÔNG dừng giữa lô (trừ CB-1/2/4/5).
- Lỗi phát hiện ở lô N → ZCode vá → **chỉ chạy lại lô N**, không đụng lô khác.

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

## 4b. CIRCUIT BREAKER — NGẮT MẠCH KHI PHÁT HIỆN VẤN ĐỀ KHÔNG TỰ VÁ ĐƯỢC (BẮT BUỘC)

**Nguyên tắc: BẠN KHÔNG ĐƯỢC TỰ SỬA builder/verifier/runner.** Gặp vấn đề hệ thống →
**DỪNG NGAY, báo ZCode** — đừng cố chạy tiếp, đừng "xử lý sáng tạo". Dưới đây là các
luật ngắt mạch bằng số — vi phạm luật nào là DỪNG + báo cáo ngay:

| # | Luật ngắt mạch | Hành động |
|---|---|---|
| **CB-1** | Builder/verifier/runner **crash code** (stack trace, lỗi regex, lỗi cột, TypeError...) — KHÔNG phải rate limit | DỪNG NGAY cả batch. Copy stack trace + ticker → báo ZCode. KHÔNG thử "sửa tạm" |
| **CB-2** | **5 mã liên tiếp** fail CÙNG 1 REQ không nằm trong danh sách đã biết (danh sách quen: REQ-002 data ngắn, REQ-024 thiếu capex, REQ-032 peer, REQ-071 zero, REQ-021 tổng hợp) | DỪNG — nghi lỗi hệ thống. Ghi 5 mã + REQ + trích dẫn vào báo cáo |
| **CB-3** | Trong 1 lô ngành: tỉ lệ `NO_DATA + needs_human` > **30%** (hoặc done < 70% kỳ vọng §3c) | DỪNG cuối lô — nghi lỗi đặc thù ngành. Báo ZCode trước khi chạy lô kế |
| **CB-4** | API lỗi **10 lần liên tiếp** (dù đã chờ + retry) | DỪNG — không chạy tiếp với dữ liệu hỏng. Báo ZCode |
| **CB-5** | Builder chạy nhưng **không ra dòng `VERIFY: x/74`** hoặc result.json thiếu key (`recall`/`fails`) | DỪNG — output format lạ = builder sai phiên bản. Báo ZCode |
| **CB-6** | **Mã lạ bất thường**: P/E vô lý (<0.1 hoặc >1000), mcap lệch 10× so với kỳ vọng vốn hóa, data trả toàn 0 dù API OK | Ghi `needs_human` + bằng chứng (KHÔNG dừng — xử lý theo luật mã lạ) |

**Khi ngắt mạch (CB-1→CB-5):**
1. Ghi trạng thái hiện tại vào tracker (không xóa gì).
2. Tạo `/tmp/VNALL-CIRCUIT-BREAK-<MÃ LỆNH>.md`: luật nào bị vi phạm + mã + bằng chứng
   (stack trace/trích dẫn) + số liệu tới điểm dừng.
3. **DỪNG HOÀN TOÀN** — không chạy lô khác, không tự vá, không thử lại sau 10 phút.
4. Báo ZCode (qua chủ đầu tư) kèm file báo cáo. Chờ lệnh tiếp.

**Ngoại lệ KHÔNG ngắt mạch (tự xử lý được):** rate limit lẻ tẻ (chờ 120s thử lại,
tối đa 2 lần/mã); mã thiếu dữ liệu thật → NO_DATA/needs_human theo đúng quy trình;
sector map lệch rõ ràng với tên công ty → sửa trong file sector (KHÔNG sửa code).

**Pilot 8 mã: sau mã cuối BẮT BUỘC dừng + báo cáo pilot** (dù sạch) — chờ ZCode/Sol
duyệt mới được chạy 1.000 mã. Áp dụng CB-1..CB-6 trong pilot luôn.

## 5. BÁO CÁO

### 5a. Báo cáo MỖI LÔ `/tmp/VNALL-LO-<TÊN>.md` (ngắn gọn — sau mỗi lô, §3b)

1. Bảng tóm tắt lô: số mã, done, needs_human, NO_DATA, 74/74, avg recall.
2. **Top-5 REQ fail CỦA LÔ** + phân loại: lỗi data thật / nghi lỗi hệ thống theo ngành
   (kèm 2-3 mã + trích dẫn).
3. Mã cần xem (needs_human): từng mã + lý do + bằng chứng.
4. **Nghi lỗi ngành?** (yes/no + lý do) — nếu nghi, dừng và ghi rõ.

### 5b. Báo cáo CUỐI `/tmp/VNALL-REPORT-P0.md` (sau lô cuối)

1. Pilot 8 mã: bảng (ticker, sector, status, recall, exit) + xác nhận AGG/BMI/SGR đúng.
2. Toàn bộ: 1.000 mã → done/needs_human/NO_DATA, 74/74, avg recall.
3. **Theo ngành** (bảng 8 lô): mỗi lô done/74/74/avg + REQ fail đặc trưng.
4. So sánh với bản cũ (606 mã 74/74): bao nhiêu mã giữ/tụt + lý do (thiếu data thật).
5. Top-10 REQ fail toàn cục + phân loại.
6. Xác nhận mẫu: cfo/inventory trong `verified-dashboard-data.json` = thật hoặc null
   (5 mã: ngân hàng/industrial/materials/insurance/tech).
7. File tracker mới: `~/ZCodeProject/data/vnall/vnall_tracker_p0.json` (GHI ĐÈ sau
   khi audit bản cũ — giữ bản cũ nhãn `invalid` trước).

## 6. LƯU Ý

- **KHÔNG tự sửa builder/verifier/runner** — fail lạ → stack trace + ticker vào báo cáo.
- **KHÔNG dùng `--reuse`** và KHÔNG merge với `work/` cũ (runner P0 tự xử lý staging sạch).
- Mã `exit 1` là CHUẨN (fail-closed) — không phải lỗi runner.
- Xong → ZCode rà soát → mời GPT 5.6 Sol tái kiểm định chính thức.

**Ký:** ZCode — 2026-08-08
