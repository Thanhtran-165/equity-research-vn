# 🔍 Premortem: vn-bond-transmission (báo cáo longform trái phiếu VN)

**Phase**: mid-build (đã có data + outline + 3 chương Mở đầu, còn 15 chương)
**Input**: `vn-bond-transmission/` — 25 file (OUTLINE.md, COVERAGE.md, 5 script, 11 CSV raw, index.html)
**Map extracted**: Bài claim trái phiếu VN là "biến trung tâm" — phản ứng SBV mạnh (-0.5 đến -1.0% CUT, +1.3% HIKING), dẫn dắt tỷ giá (corr -0.66), KHÔNG phản ánh lạm phát (Fisher fail -0.10). 18 chương, research-driven + chronological.

**Context budget**: 25 file. Đọc hết OUTLINE.md + COVERAGE.md + master_monthly.csv + exploratory analysis. Scripts/CSV raw đọc sample. **Đủ coverage** cho blind spot logic.

---

## 🔴 Lens A — Assumption stress-test

### A.1 Tương quan Bond↔FX "mạnh -0.66" thực ra KHÔNG stable — đảo dấu theo period
- **Claim**: OUTLINE.md Ch9 + exploratory claim "bond↔FX tương quan âm mạnh -0.66, bond dẫn dắt FX 1-3 tháng"
- **Why weak**: Stress-test subsample cho thấy corr **đảo dấu hoàn toàn**:
  - 2014-2019: **-0.90** (âm mạnh)
  - 2020-2021 COVID: **+0.76** (dương mạnh!)
  - 2022-2023: +0.06 (gần 0)
  - 2024-2026: +0.84 (dương mạnh)
- **If false, what breaks**: Chương 9 claim "tương quan mạnh -0.66" = **spurious correlation từ việc gộp các regime khác nhau**. Sẽ bị reviewer bác: "đây là Simpson's paradox, không phải mối quan hệ thật". Toàn bộ luận điểm "bond dẫn dắt FX" sụp đổ.
- **Falsification test**: Chạy rolling 36-month correlation. Nếu corr đi ngang qua 0 liên tục → không có mối quan hệ stable → bài phải viết "regime-dependent", không "mạnh -0.66".

### A.2 "Fisher hypothesis fail cho VN" dựa trên 65 tháng, window bị truncate
- **Claim**: Ch11 — "bond↔CPI corr -0.10, Fisher fail"
- **Why weak**: CPI YoY monthly chỉ có 2019-11→2026 (65 tháng). Trong khi bond yields có 151 tháng. Window overlap **chỉ 65 tháng**, và 65 tháng này rơi vào giai đoạn bất thường (COVID + thắt chặt + phục hồi). Không thể kết luận "Fisher fail cho VN" từ 65 tháng bất thường.
- **If false, what breaks**: Chương 11 insight chính (Fisher fail) = **không đủ data để claim**. Có thể Fisher đúng cho VN ở dài hạn (1990-2018) nhưng data không đủ để thấy.
- **Falsification test**: Dùng FRED CPI VN annual (1990-2026, 42 điểm) + sjc CPI yearly (2009-2026, 18 điểm) chạy corr với proxy bond. Nếu corr dài hạn khác -0.10 → kết luận "fail" sai.

### A.3 SBV QĐ 2008-2019 "từ AMRO" — 17 entries chưa verify, có thể sai số QĐ
- **Claim**: COVERAGE.md — "10 verified, 17 pending verification (2008-2019)"
- **Why weak**: Verify vòng trước tìm **3 lỗi nghiêm trọng** (1123→1728, 1524→1606, 1124→1123). Nếu 3/5 QĐ gần đây đã sai, 17 QĐ cũ (từ AMRO summary, không phải QĐ gốc) **gần như chắc chắn có sai sót khác**.
- **If false, what breaks**: Event study Ch8 (12 SBV decisions) dùng timeline này. Nếu 2-3 events trong window 2014-2026 sai date/rate → kết quả Δ before/after bị sai → kết luận "HIKING tác động mạnh hơn CUT" có thể artifact.
- **Falsification test**: Verify QĐ 211/2019 (cắt 6.5→6.0%) — QĐ duy nhất pre-COVID trong window chính. Nếu sai → event study yếu.

---

## 🟡 Lens B — Silent-failure surface

### B.1 🔴 P0 — CPI YoY 54.93% tháng 12/2021 là LỖI PARSE, không phải số liệu thật
- **Input**: `data/raw/cpi/nso_cpi_monthly.csv` dòng 2021-12: cpi_yoy_pct=54.93
- **What skill does**: Script `03_fetch_cpi.py` regex bắt nhầm — "tăng 54,93%" có thể là số khác (VD: kim ngạch xuất khẩu, hoặc YoY của chỉ số giá vàng).
- **What goes wrong silently**: Master_monthly có CPI YoY 54.93% tháng 12/2021. Nếu bài claim "CPI đỉnh 54.93%" → **sai nghiêm trọng** (CPI VN thực tế 2021 ~1.84%). Hoặc nếu chart render → spike khổng lồ ruin chart. Hiện tại không có flag nào cảnh báo.
- **Why no flag**: Script parse regex mà không validate range (CPI YoY VN lịch sử 0-25%, >30% =可疑).
- **Fix hint**: Thêm range check trong `03_fetch_cpi.py`: nếu YoY > 25% → flag + re-parse bài gốc. Hoặc đơn giản: xóa dòng 2021-12 outlier + re-parse thủ công.

### B.2 🔴 P0 — "All 4 biến cùng lúc" chỉ có 34 tháng (2019-11 → 2023-12)
- **Input**: master_monthly.csv — overlap bond+FX+CPI+lending = 34 tháng
- **What skill does**: OUTLINE.md Ch17 "tổng hợp 4 mối quan hệ" + Ch9/11/13 dùng data này
- **What goes wrong silently**: Bài ngầm giả định "4 mối quan hệ cùng window" khi thực ra:
  - Bond+SBV: 151 tháng (2014-2026)
  - Bond+CPI: chỉ 65 tháng (2019-2026)
  - Bond+lending proxy: 116 tháng (2014-2023, **dừng 2023**)
  - All 4: **chỉ 34 tháng**
- Nếu so sánh "mối quan hệ nào mạnh nhất" dựa trên window khác nhau → so sánh táo → kết luận sai về ranking.
- **Why no flag**: COVERAGE.md ghi coverage từng biến nhưng KHÔNG flag "window không đồng nhất".
- **Fix hint**: Thêm bảng "window từng mối quan hệ" rõ trong Ch2 + caveat mỗi chương về window riêng.

### B.3 HNX par yield có thể KHÔNG phải "benchmark" mà là "đường cong fitting"
- **Input**: `01_fetch_hnx_yield.py` parse bảng HNX, dùng cột "Par yield"
- **What skill does**: Bài gọi "par yield benchmark" (Ch1, Ch2)
- **What goes wrong silently**: HNX publish 3 cột: Spot rate liên tục, Par yield, Spot rate theo năm. "Par yield" = computed yield sao cho bond price = par, **không phải giao dịch thật**. Nếu HNX thiếu giao dịch đủ → par yield là **nội suy phương pháp**, không thị trường thật.
- **Why no flag**: Script không kiểm tra method_note; bài không phân biệt "par yield computed" vs "giao dịch thật".
- **Fix hint**: Verify với HNX methodology doc; nếu par yield = nội suy → đổi label thành "par yield (computed)", không "benchmark thị trường".

---

## 🟢 Lens C — Right-problem check

**Bạn có đang giải đúng bài không?**

Outline hiện tại claim "trái phiếu là biến trung tâm" — nhưng exploratory analysis cho thấy **bond↔FX corr đảo dấu theo regime**, và **bond↔CPI gần không tương quan**. Nếu 2/4 mối quan hệ "trung tâm" thực ra không stable, thì thesis "biến trung tâm" yếu.

**Mục tiêu THẬT** của bạn (từ câu trả lời trước) = "đủ dùng cho vừa đầu tư vừa nghiên cứu từ số 0". Với data hiện tại, bài phù hợp nhất KHÔNG phải là "trái phiếu là biến trung tâm" (claim quá mạnh cho data không đủ), mà là **"trái phiếu VN phản ứng thế nào với chính sách SBV qua các regime"** — câu hỏi khiêm tốn hơn, data đủ trả lời, insight thực sự mới (regime-dependent correlation).

**Cách đơn giản hơn**: Thay vì 18 chương claim "biến trung tâm", bài 12 chương xoay quanh **1 insight thật**: "Mối quan hệ trái phiếu↔tỷ giá VN đảo dấu theo regime chính sách — đây là phát hiện mà không ai chỉ ra vì đa số nhìn full-period corr." Insight này đủ mới, đủ cụ thể, data vững.

---

## 📊 Bảng điểm

- **Lỗi P0**: 2 (B.1 CPI outlier, B.2 window không đồng nhất)
- **Lỗi P1**: 3 (A.1 corr đảo dấu, A.2 Fisher window, A.3 SBV QĐ)
- **Lỗi P2**: 1 (B.3 par yield label)
- **Tín hiệu dừng**: **TIẾP TỤC** — 2 P0 cần sửa trước khi viết thêm chương
- **Cross-skill patterns**: N/A (project độc lập, không phải skill)

---

## Kết luận trung thực

Đây là blind spot TÔI thấy. Có blind spot TÔI không thấy — premortem này cũng là 1 map (đặc biệt yếu ở phần verify SBV QĐ 2008-2019, tôi chưa verify từng cái).

**Đề xuất ưu tiên fix** (chi phí thấp nhất, giá trị cao nhất):
1. **B.1** (5 phút): Xóa/thừa sửa CPI YoY 54.93% → re-parse bài 2021-12
2. **A.1** (20 phút): Chạy rolling correlation + viết lại Ch9 thành "regime-dependent" thay vì "mạnh -0.66"
3. **B.2** (10 phút): Thêm bảng window từng mối quan hệ trong Ch2
4. **C** (quyết định của bạn): Có giảm scope thesis từ "biến trung tâm" → "regime-dependent" không? Đây là quyết định cấp độ tiền đề — ảnh hưởng toàn bộ 18 chương.

**Sau khi sửa, chạy lại `/skill-premortem` vòng 2** — blind spot mới sẽ xuất hiện vì map đã đổi (đặc biệt nếu thesis đổi sang regime-dependent).
