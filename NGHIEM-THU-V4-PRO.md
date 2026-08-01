# NGHIỆM THU — Bản vá batch-1 dành cho V4 Pro

## 🔄 VÒNG 2 — Phản hồi nghiệm thu 9.0/10 của bạn (FIX-4 = 6/10)

Bạn đã chỉ đúng root cause M2 gốc: regex `[^0-9]{0,60}?(\d...)` ăn "2025" (năm) làm số trước, rồi bị skip → số THẬT phía sau ("Doanh thu thuần năm 2025 đạt 50,000 tỷ") không bao giờ capture. Đã vá đúng đề xuất của bạn:

1. ✅ Pattern thêm **optional year prefix**: `kw + [^0-9]{0,60}? + (?:20\d\d[^0-9]{0,60}?)? + (\d...)` — năm không còn "nuốt" số thật
2. ✅ **Fallback dự phòng**: nếu vẫn bắt year-as-value → quét số kế tiếp trong 60 chars sau

### Bằng chứng vòng 2 — M2 gốc của bạn giờ bị bắt

```
✅ M2 gốc ("Doanh thu thuần năm 2025 đạt 50,000 tỷ đồng (số bịa)"):
   fail=[REQ-021, REQ-033]
   → REQ-033: revenue/2025: 30,699.0 vs 50,000.0 (lệch 62.9% > 5%)
```

Regression sau fix: clean **67/67**, `test_v5_negative.py` **8/8**, M1b + M2 (bản trước) vẫn bắt đúng.

**Mời bạn nghiệm thu vòng 2**: chạy lại M2 gốc → kỳ vọng `fail=[REQ-021, REQ-033]`. M3 (drawdown), M4 (key-metric source), M5 (causal chain) vẫn thuộc batch-2 (FIX-3 keyword proximity) — đúng như khuyến nghị ưu tiên 2 của bạn.

---

## VÒNG 1 — Kết quả gốc (trước khi bạn nghiệm thu)

Skill `equity-research-vn` v3.2.0 (67 REQ) tại `/Users/bobo/.zcode/skills/equity-research-vn/` vừa được vá theo **review của bạn** (FIX-1..13). Mời bạn nghiệm thu phần bạn phát hiện.

## Những gì đã vá theo phát hiện của bạn

| Fix của bạn | Trạng thái | Chi tiết |
|---|---|---|
| **FIX-1** — `_contract()` crash bug (`NameError`) | ✅ ĐÃ VÁ | `independent_verifier.py` (~dòng 1119): thay `_contract()` bằng `_load_json_rel("verified-dashboard-data.json")` — "bom nổ chậm" đã gỡ |
| **FIX-2** — 5 REQ unmapped (022/023/024/026/027) | ✅ ĐÃ VÁ | `requirements-phase-map.yaml`: thêm vào `phase6_dashboard` — không còn REQ critical bỏ sót |
| **FIX-4** — break-on-first-match + year-only bypass REQ-033 | ✅ ĐÃ VÁ | Bỏ `break` (chạy cả 2 keyword mỗi metric); year window nới ±100 và **chọn năm gần claim nhất** (trước hoặc sau) — trước đây claim không gắn year bị bỏ qua hoàn toàn |
| **FIX-7/8** — unbound vars (gt, macd_sign) | ⏳ ĐỢT SAU | Đã ghi nhận, xử lý cùng batch-2 |

## Bằng chứng nghiệm thu

Mutation **M2 của bạn** ("50,000 tỷ vs 30,699 tỷ trong cùng section") — từng LỌT — giờ bị bắt:

```
✅ M2: fail=[REQ-021, REQ-033, REQ-034]
  → REQ-033: revenue/2025: 30,699.0 vs 50,000.0 (lệch 62.9% > 5%) — sec-exec: 50,000.0; sec-exec: 30,699.0
```

Chạy lại đầy đủ:
- Clean fixture E2E: **67/67 PASS**
- `test_v5_negative.py`: **8/8 bắt đúng**

## Yêu cầu nghiệm thu (mời bạn tự kiểm chứng)

1. Chạy lại mutation M2 của bạn (hoặc M1 peer / M3 drawdown / M4 / M5 — nếu chưa vá thì ghi rõ "chưa vá" và xác nhận vẫn lọt như bạn đã báo)
2. Chạy: `python3 /Users/bobo/.zcode/skills/equity-research-vn/scripts/independent_verifier.py CTD /tmp/ervn_e2e/CTD/CTD_Complete_Report.html` → kỳ vọng 67/67
3. Xác nhận từng dòng trong bảng trên (ĐÃ VÁ / CHƯA ĐÚNG) và cho điểm nghiệm thu

## Ghi chú khác từ review bạn (chưa thuộc đợt này)

- FIX-3 (keyword proximity 9 REQ), FIX-5 (dict dispatch), FIX-6 (helper citation), FIX-9 (normalize "1,500" vs "1,5"), FIX-10 (REQ-054 spec/code), FIX-11..13 (WARN-only, 8/9 phases, số REQ cũ) → đang xếp batch-2
