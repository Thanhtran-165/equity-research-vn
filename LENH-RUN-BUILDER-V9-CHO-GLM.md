# LỆNH V9: CHẠY 73 MÃ VN100 BẰNG BUILDER CHUẨN (MỤC TIÊU: ≥70/73 MÃ ≥72/74)

**Từ:** ZCode · **Giao cho:** GLM · **Ngày:** 2026-08-02

---

## 1. BỐI CẢNH (đọc trước — 3 phút)

ZCode đã hoàn tất đợt vá (verify chéo trên máy ZCode):

| Hạng mục | Kết quả |
|---|---|
| **Verifier — 6 fix mới** | normalize EN/VN (số "33,797.9" parse đúng), REQ-022 số âm, REQ-033 cross-contamination + bull/bear + unit ×, REQ-031/048/055 (đợt trước) |
| **Builder chuẩn — đã đóng vào skill** | `~/.zcode/skills/equity-research-vn/scripts/build_report.py` (576 dòng, từ vn100_v2.py + 3 fix: REQ-003 mention, format) |
| **Kiểm chứng mẫu** | **VJC 74/74 PASS HOÀN TOÀN** (trước: 70/74), **BID 74/74**, golden CTD PASS, suite 12/12 |

**Đây là bản cuối — mọi mã chạy bằng builder này, KHÔNG tự sửa builder, KHÔNG tự viết renderer.**

## 2. NHIỆM VỤ

Chạy lại **71 mã needs_human** (2 reference CTD/HPG giữ nguyên) bằng:

```
python3 ~/.zcode/skills/equity-research-vn/scripts/build_report.py <TICKER> [SECTOR]
```

Builder tự làm mọi thứ: fetch data (42 kỳ sponsor), tech score thật, split audit, DATA 67 keys, narrative đầy đủ, verify. Agent CHỈ cần:
1. Chạy builder cho từng mã (tuần tự, sleep 60s giữa mã — rate limit)
2. Đọc kết quả verify in ra (`VERIFY: x/74, fails=[...]`)
3. Mã nào fail → đọc evidence (`/tmp/vn100_<TICKER>/.task-state/evidence/REQ-*.json`) → **sửa DATA trong data files** (financials.json/peers.json...) → **chạy LẠI builder** (builder đọc từ data files? — KHÔNG: builder tự fetch. Nếu cần sửa data → sửa source-pack CSV hoặc ghi chú → chạy lại) — tối đa 3 lần chạy lại/mã
4. Ghi kết quả vào `/tmp/vn100_tracker.json` (giữ format cũ) + copy report vào `/tmp/vn100_reports/`

**Lưu ý quan trọng:** builder chạy ở đâu cũng được (máy ZCode) — nhưng bạn chạy trong phiên của bạn, fetch trực tiếp qua vnstock (giống V4).

## 3. NGÀNH (đối số thứ 2)

| SECTOR truyền | Mã |
|---|---|
| `banking` | ACB, BID, CTG, HDB, MBB, STB, TCB, VPB, TPB, SHB, LPB, VCB, EIB, BVB, NVB, OCB, PGB, VIB, SSB, KLB, VAB (21 mã) |
| `insurance` | BVH, MIG, PVI (nếu trong danh sách) |
| `energy` | GAS, PLX, POW, PVS, PVD, BSR, PVB... (theo tracker) |
| Còn lại | tra theo tracker `sector` của từng mã (V4 đã có — dùng lại danh sách đó) |

→ Nếu không chắc: chạy không có sector (`general`) — builder vẫn hoạt động (chỉ khác narrative ngân hàng).

## 4. QUY TRÌNH & CHỐNG BỎ CUỘC (giữ nguyên luật lệnh VN100)

- Ghi tracker NGAY sau mỗi mã; gián đoạn → ghi progress → nối tiếp từ tracker
- Mã `BLOCKED_API` → thử lại sau 5 mã, lần 2 vẫn chết → ghi nhận
- Nghi lỗi builder/verifier → bằng chứng + `needs_human` → TIẾP TỤC mã khác (không sửa skill)

## 5. BÁO CÁO (tạo `/tmp/VN100-REPORT-V5.md`)

1. Bảng 73 mã: Ticker | Sector | Recall | REQ fail (id) | Số lần chạy lại
2. Thống kê: bao nhiêu mã ≥72/74; ≥70; avg recall; tổng token thực tế
3. Mọi mã fail còn lại — phân loại (builder/data/API) + evidence
4. Top-10 cơ hội (recall ≥72 + định giá) — output chính

## 6. RÀNG BUỘC

- ✗ Sửa builder / verifier / skill — bằng chứng + needs_human
- ✗ Copy HTML giữa mã; ✗ commit/push; ✗ chạy song song; ✗ bịa số
- Dừng sớm chỉ khi: phase fetch fail 3 lần (API) — ghi `BLOCKED_API`

## 7. TIÊU CHÍ THÀNH CÔNG

- **≥ 60/71 mã recall ≥ 72/74** (bản vá đã chứng minh VJC/BID 74/74 — mục tiêu thực tế cao hơn V4)
- 0 mã bỏ lửng; mọi fail còn lại có bằng chứng
- Báo cáo V5 đầy đủ → chốt VN100 dùng được + top-10 cơ hội cuối
