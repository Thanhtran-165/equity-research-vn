# LỆNH VNALL P0-REBUILD: TÁI SINH 1.000 MÃ SAU VÁ KIỂM ĐỊNH

**Từ:** ZCode
**Giao cho:** GLM
**Ngày:** 2026-08-08
**Lý do:** Kiểm định độc lập (GPT 5.6 Sol) phát hiện dữ liệu cũ chứa SỐ GIẢ LẬP (CFO =
gross×0.3, tồn kho = gross, capex = gross×0.05 khi thiếu). Đã vá builder + verifier
(commit `989ab55c0`). **BÁO CÁO CŨ KHÔNG DÙNG ĐƯỢC NỮA — phải tái sinh từ đầu.**

---

## 1. CẬP NHẬT (bắt buộc trước tiên)

Lấy từ repo `Thanhtran-165/equity-research-vn` (hoặc copy từ máy chủ):
- `scripts/build_report.py` — bản P0 (cấm fallback, exit nonzero, bank gate, bỏ EV/EBITDA)
- `scripts/independent_verifier.py` — bản P0 (REQ-062 fail-closed + match đúng năm, REQ-060 EPS note)
- `references/sector_pack.md` — 13 nhóm ngành
- `vn-research-dashboard/assets/dashboard_template.html`

Xác nhận bản mới: chạy `python3 scripts/build_report.py AAA materials` trên 1 mã →
phải ra `VERIFY: 74/74` và **`cfo` trong `verified-dashboard-data.json` là số THẬT
hoặc `null` (không bao giờ là gross×0.3)**.

## 2. MỤC TIÊU

1. **Tái sinh 1.000 mã từ raw source** bằng builder P0 — fetch mới toàn bộ (data cũ
   nhiễm fallback, không tái sử dụng `--reuse`).
2. Mọi mã: `VERIFY: x/74` + gate exit đúng (mã <70/74 hoặc fail critical → exit 1 —
   **đây là chuẩn mới, không phải lỗi**).
3. Cập nhật `/tmp/vnall_tracker.json` + lưu bản mới vào `~/ZCodeProject/data/vnall/`
   (GHI ĐÈ bản cũ — bản cũ đã hết giá trị).
4. Báo cáo `/tmp/VNALL-REPORT-P0.md`.

## 3. QUY TRÌNH (giữ kỷ luật cũ)

- Tuần tự, sleep 60s giữa mã (rate limit vnstock).
- Sau mỗi mã: cập nhật tracker (status/recall/fails/sector).
- `exit 1` (mã không đạt) → ghi bình thường (needs_human/NO_DATA), KHÔNG dừng batch.
- Kỳ vọng chất lượng mới (CHẤP NHẬN THẤP HƠN bản cũ — trung thực hơn):
  - CFO/inventory/capex thiếu → `null` + "không có dữ liệu" (trước: số giả)
  - Mã thiếu capex thật → REQ-024 fail → needs_human (trước: fallback che)
  - Bank: báo cáo KHÔNG còn FCF/WACC/Graham (trước: sai chuẩn)
  - Ước tính: số mã 74/74 có thể GIẢM (mã thiếu dữ liệu thật sẽ xuống) — đó là kết quả
    ĐÚNG, không phải lỗi. Báo cáo trung thực con số mới.

## 4. BÁO CÁO `/tmp/VNALL-REPORT-P0.md`

1. Tổng: 1.000 mã, done/needs_human/NO_DATA, 74/74, avg recall.
2. **So sánh cũ → mới**: bao nhiêu mã tụt điểm (kèm lý do: thiếu CFO/capex/data), bao
   nhiêu mã giữ nguyên. Danh sách 30 mã tụt nhiều nhất + lý do.
3. Top-10 REQ fail mới + phân loại (lỗi data thật / lỗi builder cần ZCode vá).
4. Xác nhận mẫu 5 mã (ngân hàng/industrial/materials/insurance/tech): `cfo`/`inventory`
   trong verified-dashboard-data.json = thật hoặc null (trích dẫn JSON).
5. File tracker mới: `~/ZCodeProject/data/vnall/vnall_tracker.json` (bản P0).

## 5. LƯU Ý

- **KHÔNG tự sửa builder/verifier** — fail lạ → copy stack trace + ticker vào báo cáo.
- **KHÔNG dùng `--reuse`** cho đợt này (data cũ nhiễm fallback).
- Chạy xong → ZCode rà soát → mời GPT 5.6 Sol tái kiểm định lần 2.

**Ký:** ZCode — 2026-08-08
