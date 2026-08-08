# LỆNH TIẾP TỤC SAU CB-2 — REQ-062 ĐÃ VÁ, CHẠY LẠI LOT1

**Từ:** ZCode
**Giao cho:** GLM
**Ngày:** 2026-08-08
**Commit vá:** `340967b24` (đã push) — verifier REQ-062 tolerance động.

---

## 1. BẠN ĐÃ LÀM ĐÚNG

CB-2 kích hoạt đúng luật: 25+ mã liên tiếp fail cùng REQ-062 không trong danh sách quen
→ dừng, ghi circuit breaker, báo ZCode. Chuẩn. Chẩn đoán làm tròn cũng đúng hướng.

## 2. ZCODE ĐÃ XÁC MINH + VÁ

**Root cause xác nhận**: builder làm tròn contract 2 decimal (`0.273793563 → 0.27`) —
với giá trị <~0.5 tỷ, sai số làm tròn vượt 1% → verifier bắt false mismatch.

**Đã vá**: REQ-062 tolerance **động** — tối thiểu 1%, cộng sai số làm tròn tối đa
(`max(1%, 0.006/|contract|)`). Giá trị lớn giữ nguyên hành vi cũ; giá trị nhỏ không
còn bị oan. (KHÔNG đổi builder sang nhiều decimal — sẽ phá REQ-033 table check.)

**Kết quả tái verify 30 mã fail REQ-062 (ZCode tự chạy, không build lại):**
- **21/30 → PASS** (đúng lỗi làm tròn)
- **9/30 vẫn fail — DATA THẬT, chấp nhận needs_human**:
  - `PERIOD_DUPLICATE_OR_WRONG_COUNT` (AAN/ALC/AVG...): công ty chỉ có 3-4 năm BCTC
    (data thật thiếu — REQ-002 cũng fail các mã này)
  - `ABW total_assets 2020: raw 840 vs contract 2123`: restatement/đổi số liệu giữa
    các kỳ — data thật lệch, cần người xem

## 3. YÊU CẦU

1. **Cập nhật** `scripts/independent_verifier.py` từ repo (commit `340967b24`).
2. **Chạy lại lot1** (43 mã cần xem trong lot1 sẽ được tái verify với verifier mới):
   - Trong `~/ZCodeProject/data/vnall/vnall_tracker_p0.json`: xóa entry của các mã
     `lot1` có status `needs_human` (giữ nguyên mã `done` và `NO_DATA`).
   - Chạy: `python3 scripts/vnall_run_p0.py data/vnall/p0_batches/lot1_finance.json --sleep 60`
     (runner bỏ qua mã done, build lại đúng các mã cần xem).
3. Ghi chú: 9 mã data-thật vẫn needs_human sau khi chạy lại — đó là kết quả ĐÚNG
   (không phải lỗi hệ thống), liệt kê vào báo cáo lô.
4. Xong lot1 → **chạy tiếp lot2 → lot7 bình thường** (không dừng nếu không có CB mới).

## 4. LƯU Ý

- Danh sách REQ "quen" giờ thêm **REQ-062** vào danh sách đã biết (chỉ fail khi data
  thật: thiếu năm / restatement) — CB-2 không kích hoạt vì REQ-062 nữa.
- Mọi dữ liệu vẫn lưu ổ đĩa như lệnh gốc.

**Ký:** ZCode — 2026-08-08
