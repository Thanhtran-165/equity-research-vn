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
- `scripts/vnall_sector_preflight.py` (**PREFLIGHT V2 — 3 nguồn ICB+sàn, fail-closed**)
- `references/sector_pack.md`, `vn-research-dashboard/assets/dashboard_template.html`

## 2. PILOT 8 MÃ (bắt buộc TRƯỚC khi chạy cả 1.000 — theo gate Sol)

Chạy bằng runner mới: `python3 scripts/vnall_run_p0.py <file 8 mã> --sleep 60`
8 mã: **AAA, ACB, BMI, FPT, AGG, SGR, 1 mã thiếu capex, 1 mã lỗ** (tự chọn 2 mã cuối
từ danh sách, note lý do chọn). Kiểm tra:
- Mỗi mã: `VERIFY: x/74` + status trong tracker (done/needs_human/NO_DATA) đúng với exit code;
- AGG phải vào pack BĐS (xem §4 preflight), BMI → insurance, SGR → đúng ngành thật;
- ACB (bank) KHÔNG còn FCF/WACC/Graham/segment % trong HTML.
Pilot sạch → mới chạy toàn bộ.

## 3. CHẠY TUẦN TỰ 7 LÔ (ZCode ĐÃ PHÂN SẴN — không dừng giữa lô, chỉ dừng khi CIRCUIT BREAKER)

### 3a. 7 LÔ ĐÃ CHỐT (file trong repo: `data/vnall/p0_batches/`)

| Thứ tự | File | Nhóm | Số mã |
|---|---|---|---|
| 1 | `lot1_finance.json` | banking + insurance + finance | 143 |
| 2 | `lot2_materials.json` | materials | 119 |
| 3 | `lot3_consumer.json` | consumer + retail | 240 |
| 4 | `lot4_industrial_a.json` | industrial (A–L) | 171 |
| 5 | `lot5_industrial_b.json` | industrial (M–Z) | 172 |
| 6 | `lot6_energy.json` | energy | 87 |
| 7 | `lot7_pharma_tech.json` | pharma + tech + securities + còn lại | 68 |

Lưu ý: sector trong batch files là THAM CHIẾU từ tracker cũ (có thể sai — AGG/BMI-type).
**Sector THẬT dùng từ preflight**: sau §4, merge sector vào 7 file:
```python
import json, os
secs = json.load(open('/Users/bobo/ZCodeProject/data/vnall/preflight_p0_sectors.json'))
for fn in os.listdir('/Users/bobo/ZCodeProject/data/vnall/p0_batches'):
    p = f'/Users/bobo/ZCodeProject/data/vnall/p0_batches/{fn}'
    d = json.load(open(p))
    for it in d['tickers']:
        it['sector'] = secs.get(it['ticker'], 'general')
    json.dump(d, open(p, 'w'), ensure_ascii=False)
```
(Mã `needs_human` từ preflight — sector giữ nguyên gốc, ghi chú.)

### 3b. Chạy TUẦN TỰ liên tục (KHÔNG dừng giữa lô)

```bash
for f in lot1_finance lot2_materials lot3_consumer lot4_industrial_a lot5_industrial_b lot6_energy lot7_pharma_tech; do
  python3 scripts/vnall_run_p0.py data/vnall/p0_batches/$f.json --sleep 60
done
```
- Runner tự: staging sạch, tracker sau mỗi mã, done chỉ khi exit 0 + recall ≥70,
  **bỏ qua mã đã done** (chạy lại lô → nối tiếp đúng từ mã dở).
- **KHÔNG dừng sau mỗi lô** — trừ khi CIRCUIT BREAKER (CB-1/2/4/5) kích hoạt.
- Mỗi lô xong: viết `~/ZCodeProject/data/vnall/reports_p0/VNALL-LO-<TÊN>.md` (template §5a) — viết xong chạy lô kế
  ngay (báo cáo lô gửi kèm báo cáo cuối, không cần chờ).

### 3c. Khi CB dừng (không tự vá được)

1. Ghi trạng thái vào tracker + tạo `~/ZCodeProject/data/vnall/reports_p0/VNALL-CIRCUIT-BREAK-*.md` (luật + mã + bằng chứng).
2. DỪNG, báo ZCode. **ZCode sẽ vá builder/verifier rồi trả lệnh "tiếp tục từ lô N".**
3. Khi có lệnh tiếp: nếu ZCode yêu cầu chạy LẠI lô N (builder mới) → xóa entry done
   của lô N trong `vnall_tracker_p0.json` (chỉ lô N) → chạy lại file lô N → các lô
   sau chạy tiếp bình thường.

### 3d. Kỳ vọng theo lô (so sánh khi báo cáo)

- lot1 (tài chính) ≥90% done · lot2/6 (materials/energy) ≥85% · lot3 (consumer) ≥80%
- lot4/5 (industrial) ≥80% · lot7 (misc) ≥75%
- Lô nào done < 70% → nghi lỗi ngành (CB-3) → báo ZCode.

## 4. PREFLIGHT SECTOR (bắt buộc — P0-E)

Sector map cũ có lỗi đã biết (Sol xác nhận): AGG đang `finance` nhưng là BĐS An Gia;
BMI đang `finance` nhưng là bảo hiểm; SGR đang `banking` nhưng không phải ngân hàng.
Làm:
1. **Chạy script có sẵn** (KHÔNG tự viết lại):
   `python3 scripts/vnall_sector_preflight.py`
   Script join 3 nguồn vnstock: `all_symbols()` (tên) + `symbols_by_industries()`
   (ICB — lọc quỹ QU/FU/ET/CW, lấy cấp sâu nhất) + `symbols_by_exchange()` (sàn).
2. Script tự: đối chiếu tên công ty với từ khóa ngành (mâu thuẫn → `needs_human` +
   ghi `~/ZCodeProject/data/vnall/preflight_p0_sector_fix.json`); AGG→realestate, BMI→insurance đã nhúng sẵn.
3. **Fail-closed do script**: `general > 10%` hoặc mã pilot (AAA/ACB/BMI/FPT/AGG/SGR)
   còn `needs_human` → script `exit 1` — phải xử lý tay rồi chạy lại, KHÔNG tự đoán.
4. Artifact: `/tmp/vnall_p0_sectors.json` `{TICKER: sector}` → merge vào 7 batch files
   (đoạn mã §3a). Báo cáo số mã hiệu chỉnh trong báo cáo cuối.

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

### 5a. Báo cáo MỖI LÔ `~/ZCodeProject/data/vnall/reports_p0/VNALL-LO-<TÊN>.md` (ngắn gọn — sau mỗi lô, §3b)

1. Bảng tóm tắt lô: số mã, done, needs_human, NO_DATA, 74/74, avg recall.
2. **Top-5 REQ fail CỦA LÔ** + phân loại: lỗi data thật / nghi lỗi hệ thống theo ngành
   (kèm 2-3 mã + trích dẫn).
3. Mã cần xem (needs_human): từng mã + lý do + bằng chứng.
4. **Nghi lỗi ngành?** (yes/no + lý do) — nếu nghi, dừng và ghi rõ.

### 5b. Báo cáo CUỐI `~/ZCodeProject/data/vnall/reports_p0/VNALL-REPORT-P0.md` (sau lô cuối)

1. Pilot 8 mã: bảng (ticker, sector, status, recall, exit) + xác nhận AGG/BMI/SGR đúng.
2. Toàn bộ: 1.000 mã → done/needs_human/NO_DATA, 74/74, avg recall.
3. **Theo ngành** (bảng 8 lô): mỗi lô done/74/74/avg + REQ fail đặc trưng.
4. So sánh với bản cũ (606 mã 74/74): bao nhiêu mã giữ/tụt + lý do (thiếu data thật).
5. Top-10 REQ fail toàn cục + phân loại.
6. Xác nhận mẫu: cfo/inventory trong `verified-dashboard-data.json` = thật hoặc null
   (5 mã: ngân hàng/industrial/materials/insurance/tech).
7. File tracker mới: `~/ZCodeProject/data/vnall/vnall_tracker_p0.json` (GHI ĐÈ sau
   khi audit bản cũ — giữ bản cũ nhãn `invalid` trước).

## 5c. LƯU TRỮ — TẤT CẢ VÀO Ổ ĐĨA, CẤM /tmp CHO DỮ LIỆU QUAN TRỌNG (bắt buộc)

Bài học 2026-08-08: /tmp bị mất sạch 2 lần khi máy khởi động lại. Quy tắc:

| Dữ liệu | Nơi lưu (Ổ ĐĨA) |
|---|---|
| Tracker (nguồn sự thật) | `~/ZCodeProject/data/vnall/vnall_tracker_p0.json` (ghi sau MỖI mã) |
| Staging mỗi mã (data + report) | `~/ZCodeProject/data/vnall/work_p0/<TICKER>/` (copy sau mỗi mã xong) |
| Log mỗi mã | `~/ZCodeProject/data/vnall/logs_p0/<TICKER>.log` |
| Báo cáo lô / cuối / circuit-break | `~/ZCodeProject/data/vnall/reports_p0/` |
| Preflight artifact | `~/ZCodeProject/data/vnall/preflight_p0_*.json` |

- `/tmp` CHỈ là vùng trung gian tạm của builder (`/tmp/vn100_<TICKER>`) — mọi thứ quan
  trọng PHẢI được copy về ổ đĩa ngay sau mỗi mã (runner P0 đã tự làm).
- **Máy restart giữa chừng KHÔNG mất gì**: chạy lại lệnh runner cho lô đang dở →
  tracker nối tiếp (skip mã đã done), mã đang chạy dở sẽ build lại từ đầu.
- Cuối mỗi lô: kiểm tra file báo cáo lô tồn tại trên ổ đĩa TRƯỚC khi chạy lô kế.

## 6. LƯU Ý

- **KHÔNG tự sửa builder/verifier/runner** — fail lạ → stack trace + ticker vào báo cáo.
- **KHÔNG dùng `--reuse`** và KHÔNG merge với `work/` cũ (runner P0 tự xử lý staging sạch).
- Mã `exit 1` là CHUẨN (fail-closed) — không phải lỗi runner.
- Xong → ZCode rà soát → mời GPT 5.6 Sol tái kiểm định chính thức.

**Ký:** ZCode — 2026-08-08
