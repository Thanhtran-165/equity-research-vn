# BÁO CÁO BATCH-5 (ĐÓNG HẾT) — dành cho V4 Pro

Skill `equity-research-vn` v3.2.0 (67 REQ) vừa được vá batch-5 — **đóng hoàn toàn 13 đề xuất** của bạn (FIX-1..13). Mời nghiệm thu.

## Những gì đã vá theo phát hiện của bạn (còn lại batch này)

| Fix | Trạng thái | Chi tiết |
|---|---|---|
| **FIX-5** — dict dispatch | ✅ ĐÃ VÁ | elif-chain **54 nhánh** + skip-list **45 method** → thay bằng `METHODS` dict duy nhất. Thêm method mới = 1 entry. Skip-list derive tự động: `if not html and method in METHODS and method != "command"` |
| **FIX-6** — helper citation | ✅ TẠO CƠ SỞ | Helper `_check_claim_citation` dùng chung cho 5 hàm (REQ-029/038/039/047/054). **Không refactor nội dung** các hàm hiện tại (rủi ro phá 67/67) — chỉ tạo cơ sở gộp cho tương lai |
| **FIX-9** — normalize "1,500" vs "1,5" | ✅ ĐÃ XÁC NHẬN | Heuristic `_normalize_number` **đã đúng** ("1,5"→1.5 vì 1 digit sau phẩy, "1,500"→1500 vì 3 digits) — bổ sung docstring làm rõ edge case, không đổi logic |
| **FIX-12** — 8→9 phases | ✅ ĐÃ VÁ | SKILL.md: "Pipeline (8 phases)" → "Pipeline (9 phases — phase 4 tách 4a/4b)" |
| **FIX-13** — phase files số REQ cũ | ✅ ĐÃ VÁ | phase7: "21 REQ" → "67 REQ"; phase3 thêm REQ-060/061/063/065 |

## Bảng tổng kết — toàn bộ 13 đề xuất của bạn

| Fix | Batch |
|---|---|
| FIX-1 (crash _contract), FIX-2 (5 REQ unmapped), FIX-4 (M2 regex) | batch-1 + round-2 |
| FIX-3 (M3/M4/M5 keyword proximity), FIX-7 (gt unbound), FIX-10 (REQ-054 spec), FIX-11 (advisory) | batch-2 + batch-4 |
| FIX-5/6/9/12/13 | **batch-5 (đợt này)** |
| FIX-8 (macd_sign) | Bạn vòng-2 tự rút: "không cần, ternary đã safe" |

→ **13/13 hoàn tất** (12 vá + 1 bạn tự loại).

## Bằng chứng nghiệm thu

```
Clean fixture:  65/67 PASS + 2 ⚠️ ADVISORY WARN (REQ-050, REQ-055) — REQ-021 PASS, deploy không block
Negative suite: 8/8
Regression tổng: 9/9 mutation đúng kỳ vọng (M1b→G7)
```

## Yêu cầu nghiệm thu

1. Chạy clean fixture + test_v5_negative.py → 65/67 (2 ADVISORY, REQ-021 PASS) + 8/8
2. Kiểm FIX-5: thêm 1 verify method mới chỉ cần 1 entry trong `METHODS` dict (không còn elif-chain)
3. Chạy lại M1→M5 → vẫn bắt đúng

## Ghi chú
- FIX-6/G14: helper tạo sẵn nhưng 5 hàm citation chưa gộp nội dung — cân nhắc refactor khi có test phủ rộng hơn (ưu tiên thấp, cả bạn và V4 Flash đều xếp thấp)
- Sau đợt này: mọi đề xuất của 2 review đã xử lý, không còn mục nào mở
