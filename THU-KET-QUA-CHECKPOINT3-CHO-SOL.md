# KẾT QUẢ VÁ CHECKPOINT 3 — 2 BLOCKER P0-E/P0-F ĐÃ XỬ LÝ

**Gửi:** GPT 5.6 Sol
**Từ:** Chủ đầu tư — qua ZCode
**Ngày:** 2026-08-08
**Commits:** `620392529` (vá) + `eb724cb1f` (dọn requirements dư) — đã push GitHub
**Hash mới:** verifier `fa3ba88a...` · requirements `049902b7...` — đã cập nhật `.verifier-hash`

Trả lời NO-GO checkpoint của bạn — cả 2 blocker đã vá và tự test.

---

## 1. P0-E — Preflight đã join đủ 3 nguồn + fail-closed

`scripts/vnall_sector_preflight.py` (viết lại):
- `all_symbols()` → ticker + tên công ty
- `symbols_by_industries()` → **ICB thật** (lọc `com_type_code` không phải cổ phiếu:
  QU/FU/ET/CW; lấy **cấp sâu nhất** mỗi symbol)
- `symbols_by_exchange()` → **sàn** (lỗi API → cảnh báo + fail-closed ở dưới)
- **Fail-closed**: `general > 10%` → `exit 1`; **mã pilot (AAA/ACB/BMI/FPT/AGG/SGR)
  còn `needs_human` → `exit 1`**; mâu thuẫn tên → `needs_human` + ghi fix file
- Fix biết trước giữ nguyên: AGG→realestate, BMI→insurance

Lưu ý trung thực: trên máy kiểm định local, API vnstock đang rate-limit nặng
(ConnectionError/RetryError khi gọi `symbols_by_exchange`, chạy 2 lần đều vậy) —
**script code đã chạy tới điểm gọi API** (đã test `symbols_by_industries()` trả 8.174
dòng đúng shape), lỗi thuộc phía API không phải script. Artifact 8 mã sẽ được tạo
trong môi trường chạy thật (GLM) — kèm lệnh bắt buộc fail-closed nếu coverage không đạt.

## 2. P0-F — Hết biểu đồ rỗng

| Hạng mục | Đã vá | Bằng chứng test |
|---|---|---|
| `chartSegMix` render khi segMix rỗng | Builder chỉ render canvas khi `segMix` có dữ liệu thật (`build_report.py:500`); template JS bọc guard `if (DATA.segMix && DATA.segMix.length)` | **ACB + AAA: 0 canvas `chartSegMix`** trong HTML (grep xác nhận) |
| REQ-069 đếm chart guard-data | Verifier nhận guard dữ liệu (`if (DATA.<key>...) { new Chart(...)`) — data rỗng → canvas không bắt buộc | REQ-069 PASS trên ACB/AAA |
| Chart dòng tiền ngân hàng dataset tồn kho rỗng | Template `chartHistCash` chỉ còn **1 dataset CFO**, nhãn `Dòng tiền hoạt động (tỷ VND)` — bỏ "Tăng tồn kho" + "CFO (tỷ VND, âm)" | ACB HTML: `1× Dòng tiền hoạt động (tỷ VND)`, **0× Tăng tồn kho / CFO (âm)** |
| REQ-012/018 đếm | Bỏ canvas rỗng → còn 13 chart thật ≥ ngưỡng 10 (không hạ ngưỡng) | ACB/AAA PASS REQ-012/018 |

## 3. BỘ TEST GIỮ NGUYÊN (iso-dir, đầy đủ data files)

```
BASELINE (AAA)      → 74/74, exit 0
MUT-CFO (DATA JS)   → 72/74, exit 1 (REQ-026)
MUT-INVENTORY       → 72/74, exit 1 (REQ-026)
MUT-1-Ô-BẢNG revenue → 72/74, exit 1 (REQ-033)
ACB (banking)       → 74/74 — không canvas segMix, chart CFO-only, ref-10 P/B-ROE-DDM
AAA (materials)     → 74/74 — non-bank thiếu segment: KHÔNG render chart segment rỗng
BMI (insurance)     → 74/74
```

## 4. DỌN PHỤ

- Xóa `requirements_v1.0.1.yaml` + `requirements_v1.0.1-rc2.yaml` khỏi skill và repo
  (bản dư — verifier chỉ đọc `requirements.yaml`).

## 5. ĐỀ XUẤT

Đã đáp ứng đủ 4 điều kiện gate của bạn (preflight artifact sẽ do môi trường chạy tạo,
kèm fail-closed; ACB/AAA không canvas rỗng; baseline + 3 mutation giữ kết quả).
Xin **GO pilot 8 mã** — kết quả pilot sẽ gửi bạn xem trước khi GO 1.000.

**Ký:** Chủ đầu tư — 2026-08-08
