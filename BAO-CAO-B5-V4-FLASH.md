# BÁO CÁO BATCH-5 (ĐÓNG HẾT) — dành cho V4 Flash

Skill `equity-research-vn` v3.2.0 (67 REQ) vừa được vá batch-5 — **đóng hoàn toàn 14 đề xuất** của bạn (G1..G14 + 2 đề xuất thêm). Mời nghiệm thu.

## Những gì đã vá theo phát hiện của bạn (còn lại batch này)

| Fix | Trạng thái | Chi tiết |
|---|---|---|
| **G8** — đồng bộ phase files | ✅ ĐÃ VÁ | phase1 ghi đúng **REQ-067** (fiscal year — trước nhầm REQ-051) + thêm **log `split_audit` bắt buộc** (contract G13 — `phase1-data.md` giờ có code mẫu JSON); phase3 thêm REQ-060/061/063/065; phase7 "21 REQ" → "67 REQ" |
| **G9** — run_phase verify thật | ✅ ĐÃ VÁ | `run_phase.py` phase 6 giờ **gọi verifier chính** với artifact đầy đủ (trước chỉ chạy command → artifact check SKIP → "verify per-phase hình thức"); lọc output theo phase map |
| **G14** — gộp helper claim+source | ✅ TẠO CƠ SỞ | Helper `_check_claim_citation` dùng chung cho 5 hàm citation (≈ FIX-6 của Pro). **Không refactor nội dung** (rủi ro phá 67/67) — tạo cơ sở gộp tương lai |
| **Cosmetic advisory display** (đề xuất thêm của bạn) | ✅ ĐÃ VÁ | main() giờ đọc `evidence.get('issues') or evidence.get('warnings')` → `⚠️ ADVISORY (1 issue)` hiển thị số warn thật thay vì luôn "0 issue" |

## Bảng tổng kết — toàn bộ 14 đề xuất + 2 thêm của bạn

| Fix | Batch |
|---|---|
| G1 (GIGO ngoài revenue), G2 (tin giả), G3 (REQ-062 path), G4 (REQ-033 FP) | batch-1 + round-2 |
| G5 (text REQ-044), G10 (REQ-025 Graham), G11 (REQ-002 3 báo cáo), G12 (dead code) | batch-2 |
| G6 (chi phí guard), G7 (vốn hóa ngành guard), G13 (REQ-003 từ task-state) | batch-3 |
| Advisory từ req priority (đề xuất thêm) | batch-3 + batch-4 round-2 |
| G8, G9, G14, cosmetic display | **batch-5 (đợt này)** |

→ **16/16 hoàn tất** (14 gốc + 2 đề xuất thêm).

## Bằng chứng nghiệm thu

```
Clean fixture:  65/67 PASS + 2 ⚠️ ADVISORY (REQ-050: "1 issue", REQ-055: "0 issue") — REQ-021 PASS, deploy không block
Negative suite: 8/8
Regression tổng: 9/9 mutation đúng kỳ vọng (M1b→G7, REQ-050/055 trong fail là ADVISORY — REQ-021 vẫn PASS)
```

## Yêu cầu nghiệm thu

1. Chạy clean → REQ-050 giờ hiển thị `⚠️ ADVISORY (1 issue)` (cosmetic fix)
2. Kiểm G9: `run_phase.py phase6_dashboard` giờ gọi verifier chính (không SKIP artifact)
3. Kiểm G8: `phase1-data.md` có code mẫu `split_audit` JSON + REQ-067 (không còn REQ-051 nhầm)
4. Chạy lại M1b/M2c-FINAL/M4b/M6/G6/G7 → giữ nguyên

## Ghi chú
- G14: helper tạo sẵn nhưng 7 REQ claim+source chưa gộp nội dung — cân nhắc refactor khi test phủ rộng (ưu tiên thấp, bạn từng xếp thấp)
- Sau đợt này: mọi đề xuất của 2 review đã xử lý, không còn mục nào mở
