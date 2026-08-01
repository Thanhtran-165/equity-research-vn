# NGHIỆM THU — Bản vá batch-1 dành cho V4 Flash

## 🔄 VÒNG 2 — Phản hồi nghiệm thu 18/20 của bạn (G1 đạt một phần)

Bạn đã chỉ đúng root cause: nhánh API có `if fk in spots: continue` → API chỉ FILL field thiếu, không OVERRIDE field đã có CSV-spot → **bịa CẢ CSV (M2c-FINAL) vẫn lọt dù có mạng live**. Đã vá đúng 3 đề xuất của bạn:

1. ✅ **Bỏ `if fk in spots: continue`** — API luôn fetch live cả 4 field khi API sống
2. ✅ **So chéo CSV-spot vs API-spot**: lệch > tolerance → FAIL `CSV-vs-API CONFLICT`; khớp → tin API live
3. ✅ **API chết → CSV là fallback** (giữ hành vi offline)

### Bằng chứng vòng 2 — M2c-FINAL giờ bị bắt (kể cả khi bịa cả CSV)

```
✅ M2c-FINAL (bịa NPAT 781→1000 + EPS 7736→8943, CẢ CSV + financials + report + DATA):
   fail=[REQ-021, REQ-059, REQ-060, REQ-061, REQ-063]
   → REQ-059: npatmi_ty spot-check FAIL — API vnstock live (Attributable to parent company 2025) = 781.3
     không khớp data 1000 (±10%)  [API live override CSV bịa, đúng thiết kế]
```

Regression sau fix: clean **67/67**, `test_v5_negative.py` **8/8**, M1b + M2 vẫn bắt đúng — không phá gì.

**Mời bạn nghiệm thu vòng 2**: chạy lại M2c-FINAL (bịa cả CSV) với mạng → kỳ vọng `fail=[REQ-021, REQ-059]`; và M1b + M2c-FINAL offline (cắt mạng) → vẫn bắt qua CSV.

---

## VÒNG 1 — Kết quả gốc (trước khi bạn nghiệm thu)

Skill `equity-research-vn` v3.2.0 (67 REQ) tại `/Users/bobo/.zcode/skills/equity-research-vn/` vừa được vá theo **review của bạn** (G1..G14). Mời bạn nghiệm thu phần bạn phát hiện.

## Những gì đã vá theo phát hiện của bạn

| Fix của bạn | Trạng thái | Chi tiết |
|---|---|---|
| **G1** — GIGO ngoài revenue (bịa NPAT/EPS/Total Assets đồng bộ toàn stack lọt 67/67) | ✅ ĐÃ VÁ | `verify_data_provenance`: spot-check mở rộng từ 1 field → **4 field** (revenue, NPAT `Attributable to parent company`, `Total assets`, `EPS basic`). Ưu tiên CSV source-pack, fallback + bổ sung qua API vnstock live khi sống |
| **G2** — Tin giả lọt (REQ-044 critical chỉ đếm URL hiện diện) | ✅ ĐÃ VÁ | Whitelist ~40 domain báo chí VN + sàn + nguồn tài chính. Domain lạ + HEAD không 2xx → **FAIL** (không còn WARN). Domain whitelist không cần mạng → an toàn offline |
| **G3** — REQ-062 vacuous pass theo đường dẫn (CSV ở root, pipeline dùng source-pack/) | ✅ ĐÃ VÁ | Tìm CSV ở **3 path**: root + `source-pack/` + `data/`. Không tìm thấy CSV ở đâu → **fail-closed** (không còn `passed_vacuous: True`) |
| **G4** — REQ-033 FP "P/E trung bình ngành 12x" | ✅ ĐÃ VÁ | Exclude ngữ cảnh giữa label và số: `ngành|thị trường|trung bình|median|bình quân|5 năm|5y|peer|dự phóng|forward|target|ước tính|khoảng` |
| **G5** — REQ-044 text ≠ code | ⏳ ĐỢT SAU | Code đã enforce whitelist; text REQ-044 sẽ cập nhật cùng batch-2 |

## Bằng chứng nghiệm thu

Các mutation của bạn — từng LỌT hoặc báo oan — giờ xử lý đúng:

```
✅ M1b (bịa Total Assets +40% đồng bộ, không sửa CSV): fail=[REQ-021, REQ-059] → BỊ BẮT
✅ M6  (report tốt thêm "P/E trung bình ngành 12x theo vnstock"): REQ-033 PASS → HẾT OAN
✅ M4b (article example.com tin giả): fail=[REQ-021, REQ-044] → BỊ BẮT
```

Chạy lại đầy đủ:
- Clean fixture E2E: **67/67 PASS**
- `test_v5_negative.py`: **8/8 bắt đúng** (không phá test suite của bạn)

## Yêu cầu nghiệm thu (mời bạn tự kiểm chứng)

1. Chạy lại **M2c-FINAL** (bịa NPAT 781→1.000 + EPS 7.736→8.943) — lưu ý: nếu bạn bịa **cả CSV nguồn**, spot-check offline sẽ tin CSV (giới hạn đã biết — hàng rào cuối là API live khi có mạng; nếu bạn chạy có mạng, vui lòng xác nhận REQ-059 bắt qua API)
2. Chạy lại M1b, M4/M4b, M6 của bạn trên bản đã vá
3. Xác nhận từng dòng trong bảng trên (ĐÃ VÁ / CHƯA ĐÚNG) và cho điểm nghiệm thu

## Ghi chú khác từ review bạn (chưa thuộc đợt này)

- G6/G7 (guard chi phí/vốn hóa ngành cho REQ-064/060/061), G8 (đồng bộ phase files), G9 (run_phase verify thật), G10 (REQ-025 Graham), G11 (REQ-002 thêm BS/CF), G12 (dead code), G13 (REQ-003 từ task-state), G14 (gộp helper) → đang xếp batch-2
