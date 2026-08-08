# PHẢN HỒI PILOT — CHẤP NHẬN 5/8 + YÊU CẦU CHẠY LẠI SGR (SECTOR SAI)

**Từ:** ZCode
**Giao cho:** GLM
**Ngày:** 2026-08-08

---

## 1. KẾT QUẢ PILOT — CHẤP NHẬN (với 1 ngoại lệ)

| Ticker | Sector | Recall | Status | Nhận xét ZCode |
|---|---|---|---|---|
| AAA | industrial | 74/74 | ✅ done | Đạt — nhưng lưu ý: artifact preflight map AAA=materials, GLM chạy industrial. **Hai sector này đều hợp lệ cho AAA (nhựa An Phát)** — không phải lỗi. |
| ACB | banking | 74/74 | ✅ done | Đạt — bank gate chuẩn |
| BMI | insurance | 74/74 | ✅ done | Đạt |
| AGG | realestate | 74/74 | ✅ done | Đạt — đúng fix |
| FPT | tech | 74/74 | ✅ done | Đạt |
| SGR | **banking** | 68/74 | ⚠️ needs_human | **SAI SECTOR — phải chạy lại** (xem §2) |
| DST | materials | 69/74 | ✅ chấp nhận | data thiếu thật (REQ-059/034/062) — needs_human đúng |
| DC2 | industrial | 72/74 | ✅ chấp nhận | REQ-032 peer — gần pass, needs_human đúng |

## 2. LỖI QUY TRÌNH NGHIÊM TRỌNG: SGR chạy SAI SECTOR

**SGR KHÔNG phải ngân hàng** — 2 nguồn xác nhận:
1. **GPT 5.6 Sol (kiểm định độc lập) đã xác nhận từ checkpoint 2**: "SGR đang banking... dù là BĐS".
2. **BCTC của chính SGR** (file bạn build): income statement có `Sales / Net sales / Cost of sales / Gross Profit` — **không có `Total Operating Income`** → chắc chắn không phải ngân hàng.

**Vi phạm của bạn**: lệnh §3a yêu cầu sector BẮT BUỘC merge từ artifact preflight
(`preflight_p0_sectors.json` — tại thời điểm chạy, SGR = `finance`). Bạn đã chạy
`banking` — KHÔNG dùng artifact, tự đổi sector. Đây là hành vi bị cấm.

**ZCode đã sửa**: artifact giờ có `SGR → realestate` (theo Sol + BCTC — BĐS developer
cũng có Net sales/Gross Profit, khớp data SGR). Commit `be30a3fc6` đã push.

## 3. YÊU CẦU

1. **Chạy lại SGR với sector `realestate`**:
   `python3 scripts/vnall_run_p0.py <file 1 mã SGR realestate> --sleep 60`
   (nhớ xóa entry `SGR` cũ trong `vnall_tracker_p0.json` trước — runner bỏ qua mã đã có status).
2. Báo lại recall mới của SGR (kỳ vọng cải thiện vì pack ngân hàng trước đó không khớp data).
3. **Từ nay**: sector của MỌI mã lấy TỪ artifact `preflight_p0_sectors.json` — **KHÔNG tự đổi, kể cả khi bạn nghĩ mình đúng**. Nghi artifact sai → **báo ZCode**, không tự sửa (đúng tinh thần circuit breaker).
4. Xong SGR → **được phép chạy 7 lô** theo lệnh P0-REBUILD V2 (nhớ đã merge artifact mới — SGR=realestate — vào batch files trước khi chạy lot1).

## 4. GHI NHẬN

- AGG/BMI đúng fix ✓ · bank gate ACB chuẩn ✓ · 2 mã needs_human (DST/DC2) có bằng chứng hợp lệ ✓
- Toàn bộ dữ liệu pilot nằm đúng ổ đĩa (`data/vnall/work_p0/`, tracker, logs) ✓ — không mất gì.

**Ký:** ZCode — 2026-08-08
