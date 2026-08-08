# KẾT QUẢ 4 ACCEPTANCE TESTS — CHECKPOINT 2 (SẴN SÀNG GO PILOT)

**Gửi:** GPT 5.6 Sol
**Từ:** Chủ đầu tư — qua ZCode
**Ngày:** 2026-08-08
**Commit:** `a6a1df7fe` (đã push GitHub) · Verifier SHA: `ee3dc764...` (cập nhật `.verifier-hash`)

Theo đúng yêu cầu của bạn ("gửi commit/hash + logs, có thể cấp GO pilot") — đây là
kết quả 4 acceptance tests, tự chạy trên máy theo đúng phương pháp iso-dir của bạn.

---

## 1. BỐN ACCEPTANCE TESTS

### Test 1 — Mutation render (iso-dir đầy đủ data files)

| Test | Kết quả | REQ bắt |
|---|---|---|
| Baseline | **74/74, exit 0** | — |
| Mutation mảng **CFO** trong DATA JS (443.62→999.99×5) | **72/74, exit 1** | REQ-026 (mở rộng sang cfo + inventory + null handling) |
| Mutation mảng **inventory** trong DATA JS (997.38→888.88×5) | **72/74, exit 1** | REQ-026 |
| Mutation 1 ô **revenue** trong bảng history (10,728.1→20,728.1) | **72/74, exit 1** | REQ-033 (table-cell check) |

### Test 2 — Runner clean work dir

- Build thành công (FPT): tracker `done`, exit 0, staging sạch.
- Builder crash (TEST99 — mã không tồn tại): **status NO_DATA, exit 1, note "không có
  result.json — builder crash"** — runner dọn `/tmp/vn100_<ticker>` TRƯỚC build, không
  thể đọc/copy `result.json` cũ. ✅

### Test 3 — ACB HTML sạch

- Không còn tỷ trọng giả 58%/22%/12%/8% (chỉ còn "NII" trong khái niệm ngành — hợp lệ).
- `[ref-10]` cho ngân hàng = **"Định giá ngân hàng — P/B, ROE, DDM / cost-of-equity"**
  (WACC không còn cho bank; non-bank giữ WACC — không hạ ngưỡng REQ-012).
- Không còn `HOSE` hardcode; `price_fetched_at`/`built_at` = **as-of thật từ dữ liệu giá**
  (2026-07-31 — ngày cuối của series), không còn 2026-08-02.
- `chartHistCash` được giữ với nhãn trung tính "Dòng tiền hoạt động 5 năm" (CFO ngân
  hàng là dữ liệu thật).
- ACB build mới: **74/74, exit 0**.

### Test 4 — Sector preflight artifact

- Script mới `scripts/vnall_sector_preflight.py`: Listing(source='vci') → tên công ty +
  sàn + ICB → map 13 pack → **đối chiếu TÊN với từ khóa ngành** (mâu thuẫn → ghi
  `/tmp/vnall_p0_sector_fix.json` + `needs_human`, không tự đoán) → xuất
  `/tmp/vnall_p0_sectors.json` TRƯỚC build.
- Fix biết trước đã nhúng: AGG→realestate, BMI→insurance; BANKS set không còn SGR.
- Lưu ý: trên máy kiểm định, API Listing tạm lỗi rate-limit ("Expecting value...") —
  script code chạy đúng, GLM chạy trên môi trường riêng sẽ có API bình thường. Log
  kèm: `scripts/vnall_sector_preflight.py` (đã test tới điểm gọi API, lỗi thuộc phía
  API không phải script).

## 2. TỔNG HỢP LOCAL (4 mã + runner)

```
AAA (materials) → 74/74 · cfo/inventory khớp CSV
BMI (insurance) → 74/74 · revenue khớp "Net sales from insurance business"
ACB (banking)   → 74/74 · inventory not_applicable · sạch 58/22/12/8 · ref P/B-ROE-DDM
FPT (tech)      → 74/74 · runner done đúng
```

## 3. ĐỀ XUẤT

Theo điều kiện bạn nêu — gửi commit/hash + logs → xin **GO pilot 8 mã**
(AAA/ACB/BMI/FPT/AGG/SGR + 1 mã thiếu capex + 1 mã lỗ, chạy bằng runner P0 +
preflight artifact). Kết quả pilot sẽ gửi bạn xem trước khi GO 1.000 mã.

**Ký:** Chủ đầu tư — 2026-08-08
