# LỆNH VNALL: KHÁM PHÁ TOÀN BỘ THỊ TRƯỜNG VIỆT NAM (~1.000 MÃ, 5 ĐỢT × ~200)

**Từ:** ZCode
**Giao cho:** GLM
**Ngày:** 2026-08-02
**Skill:** equity-research-vn v3.2.0 (74 REQ) — builder chuẩn v3 + sector pack v3

---

## 1. BỐI CẢNH (đọc trước — 5 phút)

- Skill `equity-research-vn` đã **PRODUCTION_READY**: 73/73 mã VN100 hoàn tất (54 mã 74/74),
  builder chuẩn v3 (`scripts/build_report.py`) sinh báo cáo tự verify 74/74 trên 4 ngành đại diện
  (ACB ngân hàng, HPG thép chu kỳ, VIC BĐS, MWG bán lẻ).
- **BẠN KHÔNG ĐƯỢC TỰ VIẾT renderer/narrative generator** (Lesson #18 — cấm tuyệt đối).
  Dùng builder chuẩn v3 duy nhất — nó đã tự fetch + build + render + verify.
- Sector pack v3 (`references/sector_pack.md`, 12 nhóm ngành) — builder tự đọc và sinh
  section "Phân tích ngành". Bạn KHÔNG cần làm gì thêm.
- Token thực đo từ VN100: ~55-70K/mã → 1.000 mã ≈ **55-70 triệu token**.
  Chạy nhiều phiên, mỗi phiên 1 đợt (~200 mã ≈ 11-14 triệu token). Đừng cố làm 2 đợt 1 phiên.

## 2. FILE CHUẨN (chỉ dùng những file này — không sửa, không tạo bản khác)

| File | Vai trò |
|---|---|
| `~/.zcode/skills/equity-research-vn/scripts/build_report.py` | **Builder chuẩn v3 — BẮT BUỘC**, chạy `python3 <file> <TICKER> <SECTOR>` |
| `~/.zcode/skills/equity-research-vn/scripts/independent_verifier.py` | Verifier độc lập 74 REQ (builder gọi tự động; nếu cần xem fail chi tiết chạy riêng) |
| `~/.zcode/skills/equity-research-vn/references/sector_pack.md` | Sector pack v3 — builder tự đọc |
| `~/.zcode/skills/equity-research-vn/SKILL.md` | Quy trình 9 phase — đọc 1 lần để biết cấu trúc báo cáo |

## 3. MỤC TIÊU (goal) — ưu tiên cao nhất là HOÀN THÀNH, không phải điểm số

1. **100% mã chạy có status cuối rõ ràng** (done / needs_human / NO_DATA) — 0 mã bỏ lửng, 0 bỏ cuộc vì rate limit.
2. **≥70% số mã chạy đạt recall ≥70/74**. Mã <70/74 → ghi `needs_human` + lý do + bằng chứng cụ thể (recall, fail_reqs, trích đoạn).
3. **Tuyệt đối không bịa số liệu** — mọi con số phải từ builder (vnstock sponsor + BCTC). Không sửa data, không thêm "ước tính" của bạn.
4. **Cấm copy nội dung báo cáo mã khác** (Lesson #17) — mỗi mã số liệu riêng. Sau build, `grep` vài số đặc trưng mã cũ (VD sau build ACB không được còn số của CTD).
5. **Tracker cập nhật ngay sau mỗi mã** — crash giữa chừng không mất tiến độ, nối tiếp từ tracker.

## 4. DANH SÁCH MÃ (chạy script này MỘT LẦN đầu đợt 1)

```python
# /tmp/vnall_make_list.py — tạo danh sách toàn thị trường
from vnstock_data import Listing
import json
all_ = Listing().all_symbols()
# Lọc theo sàn:
#   HOSE + HNX: LẤY HẾT (~700 mã)
#   UPCOM: chỉ lấy mã có vốn hóa ≥500 tỷ HOẶC thanh khoản ≥1 tỷ/phiên (~300 mã)
#   (dùng Quote từng mã hoặc bảng tổng hợp để lọc — vốn hóa = price × shares)
# Bỏ: chứng chỉ quỹ ETF, mã mới niêm yết <6 tháng, mã bị cảnh báo kiểm soát (nếu xác định được)
json.dump({'hose_hxn': [...], 'upcom': [...]}, open('/tmp/vnall_list.json','w'), ensure_ascii=False)
print('TOTAL:', ...)
```

Sau đó chia thành **5 đợt liên tiếp, mỗi đợt ~200 mã** (gộp HOSE/HNX + UPCOM vào mỗi đợt,
đừng để UPCOM sót cuối). Lưu danh sách từng đợt: `/tmp/vnall_batch_1.json` … `_5.json`.

## 5. QUY TRÌNH TỪNG MÃ (lặp lại, không bỏ bước)

1. `python3 ~/.zcode/skills/equity-research-vn/scripts/build_report.py <TICKER> <SECTOR>`
   - `<SECTOR>`: truyền sector thật của mã (vd `banking`, `steel`, `realestate`, `retail`,
     `securities`, `insurance`, `energy`, `transport`, `pharma`, `tech`, `thủy sản`, …).
     Lấy từ Listing/metadata. Không chắc → `general`.
   - Builder tự: fetch sponsor 42 kỳ → tech score thật → build DATA 67 keys → render HTML →
     tự chạy verifier → in `VERIFY: x/74, fails=...` + ghi `/tmp/vn100_<TICKER>/result.json`.
2. Xem dòng `VERIFY` cuối:
   - **≥70/74** → `done`. Ghi tracker. Sang mã kế.
   - **<70/74** → chạy lại builder **1 lần** (thử lại API, có khi data lỗi thoáng qua).
     Vẫn <70 → `needs_human` + ghi đúng fail_reqs + trích dẫn bằng chứng vào `notes`.
   - Builder crash/API lỗi → thử lại 2 lần (sleep 60s giữa các lần). Vẫn fail →
     `NO_DATA` + lý do.
3. Ghi tracker NGAY (xem §6).
4. Rate limit: vnstock ~50 calls/10 phút. Builder ~9 calls/mã → **sleep 60s giữa mỗi mã**.
   Gặp lỗi rate limit → sleep 120s rồi thử lại. **KHÔNG ĐƯỢC chạy song song** (2 process =
   cùng chết rate limit).
5. Báo cáo mỗi đợt xong (xem §7), rồi mới bắt đầu đợt kế.

## 6. TRACKER MỞ RỘNG (bắt buộc — ghi sau MỖI mã)

File: `/tmp/vnall_tracker.json` — mỗi mã 1 object:
```json
{
  "ticker": "AAA", "sector": "nhựa", "batch": 1,
  "status": "done", "recall": 73, "fails": ["REQ-025"],
  "price": 12500, "mcap_bn": 1523,
  "token_est": 60000, "notes": "REQ-025: ... (trích dẫn)",
  "ts": "2026-08-02T10:00:00Z"
}
```
- `status ∈ {done, needs_human, NO_DATA}` — **status cuối phải rõ ràng, không có "in_progress" sót**.
- Nối tiếp từ tracker: đầu phiên đọc file, chạy tiếp các mã chưa có status cuối.
- Cuối phiên: rà soát lại toàn bộ tracker — **0 mã bỏ lửng** (không có status mà thiếu bằng chứng).

## 7. BÁO CÁO MỖI ĐỢT (file markdown, đúng template)

Tạo `/tmp/VNALL-REPORT-DOT-<n>.md` mỗi đợt gồm:
1. **TL;DR**: số mã done / needs_human / NO_DATA, recall trung bình, % ≥70/74.
2. **Bảng đầy đủ ~200 mã**: Ticker | Sector | Status | Recall | REQ fail (top 3) | Vốn hóa (tỷ).
3. **Top-20 REQ fail theo tần suất** (đợt này) — kèm 3 ví dụ mã + trích dẫn, phân loại
   (lỗi skill verifier / lỗi data API / lỗi builder / lỗi ngành).
4. **Mã cần con người xem** (needs_human): từng mã + lý do + bằng chứng.
5. **Mã lạ/đặc biệt**: công ty mới, ngành hiếm, data bất thường (vd P/E âm, EPS=0, chia tách) —
   mô tả khách quan.
6. **Bài học đợt này** (≤5 dòng).

Sau báo cáo đợt 1: **DỪNG lại, gửi báo cáo cho ZCode** (mình vá skill nếu có lỗi hệ thống),
nhận OK rồi mới chạy đợt 2. Các đợt 3-5 làm tương tự.

## 8. KHI GẶP BẤT THƯỜNG

- **Builder in lỗi không phải rate limit** (VD lỗi cột, lỗi regex): copy nguyên stack trace +
  mã ticker vào notes tracker + báo trong báo cáo đợt. **KHÔNG tự sửa builder, KHÔNG tự viết renderer
  thay thế** — gửi về ZCode vá.
- **Nghi mã bịa số liệu** (số không khớp data sponsor): kiểm tra builder output lần 2, nếu
  nghi vẫn còn → `needs_human` + bằng chứng. Không tự "sửa" báo cáo bằng tay.
- **Ngành hiếm không có trong sector pack** (12 nhóm): builder tự rơi về "12. NGÀNH KHÁC" —
  báo cáo mã đó bình thường, note tên ngành thật vào tracker (mình bổ sung pack sau).

## 9. DỰ TOÁN TOKEN (5 đợt)

| Đợt | Số mã | Token ước tính |
|---|---|---|
| 1 | ~200 | ~11-14M |
| 2 | ~200 | ~11-14M |
| 3 | ~200 | ~11-14M |
| 4 | ~200 | ~11-14M |
| 5 | ~200 | ~11-14M |
| **Tổng** | **~1.000** | **~55-70M** |

## 10. FILES ĐẦU RA (cuối toàn bộ)

| File | Nội dung |
|---|---|
| `/tmp/vnall_list.json` | Toàn bộ mã + sàn + lọc |
| `/tmp/vnall_batch_1..5.json` | 5 danh sách đợt |
| `/tmp/vnall_tracker.json` | Tracker ~1.000 mã (nguồn sự thật) |
| `/tmp/vnall_reports/<TICKER>_Complete_Report.html` | Báo cáo HTML từng mã |
| `/tmp/VNALL-REPORT-DOT-<1..5>.md` | 5 báo cáo đợt |
| `/tmp/VNALL-REPORT.md` | Báo cáo tổng cuối cùng (TL;DR + bảng thống kê + top REQ fail toàn cục + 10 mã cần chú ý + bài học) |

**Ký:** ZCode — 2026-08-02
