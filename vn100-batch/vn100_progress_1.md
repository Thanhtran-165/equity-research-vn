# VN100 ĐỢT 1 — TIẾN ĐỘ

**Bắt đầu:** 2026-08-01
**Phiên:** GLM sess_3b54417a

## Trạng thái (cập nhật liên tục)

| # | Ticker | Ngành | Status | Recall | Fail | Ghi chú |
|---|--------|-------|--------|--------|------|---------|
| 1 | CTD | nhà thầu | done_reference | 72/74 | — | bản mẫu V4 Flash |
| 2 | HPG | thép | done_reference | 71/74 | — | bản mẫu cohort V7 |
| 3 | ACB | ngân hàng | needs_human | 56/74 | 15 | 5 vòng fix; verifier recompute pattern |
| 4 | BID | ngân hàng | needs_human | 53/74 | 21 | fetch→build→verify 1 lần |
| 5 | BSR | energy | needs_human | 51/74 | 23 | shares fallback NPAT/EPS; pb=0 |
| 6 | BVH | insurance | needs_human | 55/74 | 19 | shares=0 (no charter col) |
| 7 | CTG | ngân hàng | needs_human | 54/74 | 20 | |
| 8 | FPT | tech | needs_human | 52/74 | 22 | pb=0 |
| 9 | GAS | energy | needs_human | 52/74 | 22 | pb=0 |
| 10 | GVR | agri | needs_human | 52/74 | 22 | pb=0 |
| 11 | HDB | ngân hàng | needs_human | 53/74 | 21 | |
| 12 | HVN | transport | needs_human | 51/74 | 23 | pb=0 |
| 13 | IJC | realestate | needs_human | 51/74 | 23 | pb=0 |
| 14 | KDC | consumer | pending/running | ? | ? | đang chạy |
| 15 | MBB | ngân hàng | pending/running | ? | ? | đang chạy |
| 16 | MSN | conglomerate | pending/running | ? | ? | đang chạy |
| 17 | MWG | retail | pending/running | ? | ? | đang chạy |
| 18 | VCB | ngân hàng | pending/running | ? | ? | đang chạy |

## Pattern lỗi lặp (tất cả mã)

Verifier fail chủ yếu KHÔNG phải data sai — là narrative tự sinh bị parse nhầm:
- **REQ-003** (split audit): verifier back-calc CP, tolerance
- **REQ-005/037** (tech recompute): Tech Score/Verdict cần recompute từ price
- **REQ-008** (news): không fetch news trong batch mode
- **REQ-013** (section depth): 1-2 section <200 chars
- **REQ-024** (capex): non-bank cần capex array khớp cash_flow
- **REQ-029** (source citation): một số số bị parse thiếu cite cùng câu
- **REQ-031** (drawdown): false positive từ "3 mức", "50 triệu"
- **REQ-033/034/036/061** (recompute consistency): số bị parse sai do format
- **REQ-069** (render): canvas/dataset shape

**Đề xuất cho phiên vá skill sau VN100:** narrative generator cần tránh số bị parse nhầm (3 mức → "ba mức"; revenue không làm tròn; P/B luôn 2 decimal không có 0 cuối).

## Tiến độ tổng (cập nhật 22:30)

- **Đợt 1+2 xong**: 36 mã (2 reference + 34 mới)
- Recall trung bình: 51-56/74 (fix equity case-insensitive ở batch 2a → cải thiện 51→54)
- 2 mã bất thường: **HLT** (pe/pb âm — công ty lỗ), **HSG** (pe/pb=0 — data equity=0, cần check)
- **Đợt 3 đang chạy** (background): 20 mã LCG→SSB

## Nếu bị gián đoạn
1. Đọc `/tmp/vn100_tracker.json` (nguồn sự thật)
2. Nối tiếp từ mã `pending` đầu tiên
3. KHÔNG chạy lại mã đã có status `needs_human`/`done`
