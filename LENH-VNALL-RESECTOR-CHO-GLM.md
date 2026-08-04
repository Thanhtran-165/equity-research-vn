# LỆNH VNALL RESECTOR: GẮN NGÀNH THẬT CHO 1.000 MÃ (KHÔNG GỌI LẠI API)

**Từ:** ZCode
**Giao cho:** GLM
**Ngày:** 2026-08-04
**Lý do:** Batch 1.000 mã bị chạy thiếu tham số ngành → mọi báo cáo dùng "12. NGÀNH KHÁC".
Builder mới có chế độ `--reuse`: render lại với ngành thật, **0 call API tài chính** (chỉ 1 call news/mã).

---

## 1. CẬP NHẬT BUILDER (bắt buộc trước tiên)

```bash
cp /Users/bobo/ZCodeProject/scripts/build_report.py ~/.zcode/skills/equity-research-vn/scripts/build_report.py
# hoặc clone/pull repo Thanhtran-165/equity-research-vn → lấy scripts/build_report.py + references/sector_pack.md + vn-research-dashboard/assets/dashboard_template.html
```

Builder mới nhất: chế độ `--reuse` (đọc data đã lưu, đổi sector, render + verify — không gọi API tài chính).

## 2. KIỂM TRA ĐIỀU KIỆN (2 phút)

Với mỗi mã chạy được (`done` + `needs_human` trong `/tmp/vnall_tracker.json`, tổng 886):
- Cần còn: `/tmp/vn100_<TICKER>/verified-dashboard-data.json` + `/tmp/vn100_<TICKER>/data/financials.json`
- Mã nào THIẾU 2 file này → **KHÔNG re-render được** → liệt kê vào danh sách "mất data" trong báo cáo (không chạy lại fetch — quá đắt)

## 3. LẤY NGÀNH THẬT CHO TỪNG MÃ (1 lần, 1 script)

```python
# /tmp/vnall_sectors.py — lấy ngành thật từ Listing metadata
from vnstock_data import Listing
import json
syms = Listing().all_symbols()   # có cột industry/icb_code (hoặc industry_en)
out = {}
for _, r in syms.iterrows():
    t = str(r['ticker']).upper()
    ind = str(r.get('industry') or r.get('industry_en') or '').strip()
    if ind and ind.lower() != 'nan':
        out[t] = ind
json.dump(out, open('/tmp/vnall_sectors.json','w'), ensure_ascii=False)
print('sectors:', len(out), '/', len(syms))
```

Sau đó MAP ngành Listing → sector builder (đối chiếu bảng MAP trong
`references/sector_pack.md`): vd `banking/bank → banking`, `steel → steel`,
`realestate/property → realestate`, `retail → retail`, `insurance → insurance`,
`securities → securities`, `energy/oil&gas → energy`, `transport → transport`,
`pharma → pharma`, `technology → tech`, `consumer → consumer`...
Ngành nào không map được → `general`. Lưu `/tmp/vnall_sector_map.json`
dạng `{TICKER: sector}` cho cả 1.000 mã.

## 4. CHẠY RE-RENDER (tuần tự, ~886 mã)

```bash
python3 ~/.zcode/skills/equity-research-vn/scripts/build_report.py <TICKER> <SECTOR> --reuse
```

- Chỉ chạy mã có status `done`/`needs_human` (có data). Bỏ qua `NO_DATA` (114 mã).
- Mỗi mã: đọc data cũ + 1 call news → render → verify tự động → `VERIFY: x/74`.
- **Rate limit vẫn giữ**: news 1 call/mã — sleep 15-30s giữa các mã là đủ (tổng ~5-7 giờ).
- Ghi tracker NGAY sau mỗi mã (đúng format `/tmp/vnall_tracker.json` cũ), cập nhật:
  `sector` = sector thật mới, `recall`/`fails` = kết quả verify mới, `notes` thêm `resectored: true`.
- Mã mất data (kiểm tra §2) → giữ nguyên trong tracker, thêm `notes: "reuse_data_missing"`.

## 5. BÁO CÁO (file `/tmp/VNALL-REPORT-RESECTOR.md`)

1. **TL;DR**: số mã re-render thành công / mất data / bỏ qua NO_DATA.
2. **Bảng so sánh trước-sau**:
   - trước: 536 mã 74/74, avg 73.1 → sau: bao nhiêu 74/74, avg mới
   - mã nào ĐỔI điểm (tăng/giảm) — kèm REQ fail mới nếu có (đây là thông tin quan trọng cho ZCode)
3. **Phân bố sector thật**: top 15 ngành theo số mã + recall avg từng ngành (sau re-render).
4. **Danh sách mã mất data** (nếu có) + **16 needs_human** giữ nguyên (không phải do sector).
5. **Xác nhận section ngành**: trích 3-5 báo cáo mẫu (ngân hàng/thép/bán lẻ...) cho thấy
   `Phân tích ngành — <NHÓM ĐÚNG>`.

## 6. LƯU Ý

- **KHÔNG sửa builder, KHÔNG tự viết renderer** (Lesson #18). Nếu `--reuse` lỗi → copy stack
  trace + ticker vào báo cáo, gửi ZCode.
- **KHÔNG chạy lại fetch** cho mã mất data — báo cáo để ZCode quyết.
- Xong đợt này → báo cáo → ZCode sẽ giao việc dashboard tổng hợp toàn thị trường.

**Ký:** ZCode — 2026-08-04
