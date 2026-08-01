# NGHIỆM THU BATCH-2 — dành cho V4 Pro

Skill `equity-research-vn` v3.2.0 (67 REQ) tại `/Users/bobo/.zcode/skills/equity-research-vn/` vừa được vá batch-2 theo khuyến nghị của bạn (ưu tiên 1: FIX-3 keyword proximity). Mời nghiệm thu.

## Những gì đã vá theo phát hiện của bạn

### FIX-3 — 3 mutation còn lọt của bạn giờ đều bị bắt

| Mutation | Vòng 2 | Sau batch-2 | Cơ chế |
|---|---|---|---|
| **M3** drawdown ("có thể sụt giảm 60-70%" không data) | ❌ Lọt | ✅ **BẮT** (REQ-031) | Claim phải KHỚP max_drawdown thật (±15pp) — "có data trong report" không còn đủ; bỏ marker "có thể" (yếu — chỉ "ước tính/giả định/khoảng" mới đủ) |
| **M4** key-metric source ("P/E 9.3x (ước tính)" thay "(theo vnstock)") | ❌ Lọt | ✅ **BẮT** (REQ-029) | Key metrics cần **NAMED source trong CÙNG CÂU** (bctc/vnstock/ref-...); "data"/"theo" generic không tính; window 300 → câu chứa metric; dấu chấm trong "9.3" không phải hết câu |
| **M5** causal chain ("Lợi nhuận tăng 35% nhờ chiến lược marketing hiệu quả") | ❌ Lọt | ✅ **BẮT** (REQ-054) | Chỉ bắt causal claim định lượng (số trước/sau connector); evidence phải là số tỷ/triệu KHÁC hoặc named source trong cùng câu — số "%" của chính claim không tính; pre-window 40 chars (không ăn số câu trước) |

### FIX-7, FIX-11

| Fix | Chi tiết |
|---|---|
| **FIX-7** — `gt` unbound | `verify_temporal_alignment`: khởi tạo `gt` trước loop — hết UnboundLocalError |
| **FIX-11** — WARN-only | REQ-050/052/055 đổi priority medium → **advisory** (WARN-only, không block deploy) — đúng đề xuất của bạn |

## Bằng chứng nghiệm thu

```
Clean fixture:   67/67 PASS
test_v5_negative: 8/8 bắt đúng
M3-drawdown:     fail=[REQ-031] ✅ (trước: LỌT)
M4-citation:     fail=[REQ-029] ✅ (trước: LỌT)
M5-causal:       fail=[REQ-054] ✅ (trước: LỌT)
Regression cũ:   M1 ✅, M2 ✅, M2-gốc ✅, M6 (hết oan) ✅
```

## Yêu cầu nghiệm thu

1. Chạy lại **M3/M4/M5 của bạn** trên bản mới → kỳ vọng cả 3 bị bắt
2. Chạy lại clean fixture + test_v5_negative.py → 67/67 + 8/8
3. Xác nhận FIX-7 (gt khởi tạo trước loop) và FIX-11 (priority=advisory)

## Ghi chú batch-3 (liên quan phát hiện của bạn)

- **FP mới lộ ra khi test M6**: thêm "P/E trung bình ngành 12x" làm **REQ-025** (valuation recompute) extract nhầm 12x thành PE của CTD → cần exclude ngữ cảnh ngành cho REQ-025 (cùng class G4)
- FIX-5 (dict dispatch), FIX-6 (helper citation 5 hàm trùng), FIX-9 (normalize "1,500"), FIX-12/13 (8→9 phases, số REQ cũ)
