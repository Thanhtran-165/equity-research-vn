# BÁO CÁO BATCH-3 — dành cho V4 Pro

Skill `equity-research-vn` v3.2.0 (67 REQ) vừa được vá batch-3. Mời nghiệm thu phần liên quan phát hiện của bạn.

## Những gì đã vá

### FP-M6 — REQ-025 extract nhầm "P/E trung bình ngành 12x" (mục bạn ghi trong batch-3 note)

**Vấn đề**: thêm "P/E trung bình ngành khoảng 12x (theo vnstock)" vào report tốt → `_extract_primary_multiple` coi 12x là PE của CTD (cùng class G4 — claim ngành bị nhầm thành claim công ty).

**Fix**: thêm `ngành|trung bình|bình quân` vào `has_projection` filter trong `_extract_primary_multiple` (dòng ~653) — "P/E trung bình ngành 12x" giờ bị loại, chỉ "P/E 9.3x" của CTD được so sánh.

### FP temporal_alignment — "giá hiện tại 71.700 VND" bị nhầm thành claim doanh thu

**Vấn đề**: window 80 chars sau keyword "doanh thu" ăn sang số của câu khác ("...doanh thu trong quý gần nhất. Giá hiện tại 71.700 VND...") → REQ-034 so 71.700 vs revenue 30.699 → báo oan.

**Fix**: thêm `vnd|đồng` vào unit regex + skip claim có đơn vị VND/đồng (đó là GIÁ, không phải revenue/npatmi/eps).

## Bằng chứng nghiệm thu

```
Clean fixture:  67/67 PASS
Negative suite: 8/8
FP-PE-ngành:    fail=[] — REQ-025 + REQ-033 đều PASS (hết oan) ✅
G6 chi phí:     fail=[] — REQ-034 hết oan luôn nhờ VND fix ✅
Regression tổng: 8/8 (M1b, M2, M3, M4, M5, M6, M4b, M2c đều đúng kỳ vọng)
```

## Yêu cầu nghiệm thu

1. Chạy lại mutation "P/E trung bình ngành 12x" của bạn → kỳ vọng REQ-025 + REQ-033 PASS (hết oan)
2. Chạy clean fixture + test_v5_negative.py → 67/67 + 8/8
3. Chạy lại toàn bộ M1→M5 của bạn → vẫn bị bắt đúng

## Còn lại (ưu tiên thấp, có thể để sau)

- FIX-5 (dict dispatch), FIX-6 (helper citation — 5 hàm trùng), FIX-9 (normalize "1,500" vs "1,5"), FIX-12/13 (SKILL.md 8→9 phases, phase files số REQ cũ), G8 (đồng bộ phase files), G9 (run_phase full verifier)
