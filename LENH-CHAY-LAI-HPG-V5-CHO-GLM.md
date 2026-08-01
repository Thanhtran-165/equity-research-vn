# LỆNH V5: HPG CHẠY LẠI VỚI MẪU FORMAT CHUẨN TỪ CTD (MỤC TIÊU ≥ 68/74)

**Từ:** ZCode (phiên nâng cấp Wave 1–5 + fix cohort V2/V3/V4)
**Giao cho:** GLM (phiên thực thi)
**Ngày:** 2026-08-01

---

## 1. Bối cảnh (đọc trước — 5 phút)

Chuỗi cohort:

| Đợt | Kết quả | Bài học |
|---|---|---|
| V2 | 44/73 (1 vòng) | 71% fail narrative — dừng sớm |
| V3 | VCB 51/74, HPG 53/74 (3 vòng) | ~55% fail narrative |
| V4 | HPG peak 60/74 → final 54/74 (5 vòng) | **"Thêm narrative → tạo claims mới → verifier bắt thêm"** — bạn KHÔNG biết format chuẩn, nên thêm content sai format → mở diện tích lỗi |

**ZCode đã sửa 2 bug verifier thật từ V4** (bản hiện tại): REQ-069 chấp nhận JS keys không ngoặc kép; REQ-031 hết bắt nhầm "52 tuần" + so sánh dấu âm đúng. **Verifier giờ sạch** — nếu vẫn FAIL là do format HTML/narrative của bạn, không phải verifier.

**Điểm mấu chốt lệnh này:** ZCode trích **MẪU FORMAT CHUẨN từ CTD** (báo cáo đạt 72/74) — bạn KHÔNG còn phải đoán format. Đối chiếu từng phần của mình với mẫu TRƯỚC khi verify.

## 2. NHIỆM VỤ

**1 mã: HPG** — tái sử dụng `/tmp/cohort_v3_HPG` (data đã fetch, đã verify đúng). Mục tiêu: **≥ 68/74** sau tối đa 6 vòng fix (tối thiểu 4).

## 3. MẪU FORMAT CHUẨN (trích THẬT từ CTD_Complete_Report.html — báo cáo 72/74)

Đối chiếu format của bạn với từng mẫu dưới đây. **Mọi claim phải có `[ref-N]` + nguồn named cùng câu.**

### 3.1. DATA object — BẮT BUỘC đủ 67 keys (V4 bạn thiếu 23 keys → chart chết → REQ-069)

```js
const DATA = {
  "ticker": "...", "years": [...], "revenue": [...], "netProfit": [...],
  "grossProfit": [...], "cfo": [...], "capex": [...], "liabilities": [...],
  "eps": [...], "roe": [...], "bvps": [...], "equity": [...], "totalAssets": [...],
  "peHist": [...], "pbHist": [...], "pe5med": [...], "pe5avg": [...], "pe": ...,
  "peers": [...],
  "tech52wLow": ..., "techMA50val": ..., "techRSI": ..., "techWeeks": [...],
  "techPrice": [...], "ret1w": [...], "ret4w": [...],
  "techMA10": [...], "techMA20": [...], "techMA50": [...],
  "segMix": [...], "netIncome": [...],
  "ddMonths": [...], "ddValues": [...],
  "distBins": [...], "distCounts": [...]
}
```
→ **Mọi `DATA.<key>` chart JS tham chiếu PHẢI có trong object.** Copy danh sách keys từ CTD trước khi build.

> 📌 **MẪU ĐẦY ĐỦ:** nếu cần xem format cụ thể hơn, đọc trực tiếp
> `/Users/bobo/ZCodeProject/ctd-v4flash/CTD_Complete_Report.html` (báo cáo 72/74) —
> đối chiếu section nào fail thì mở section tương ứng trong file này.

### 3.2. Sec-valuation — bảng phương pháp + từng dòng có [ref-N] + lý do N/A

```
P/E (peer median 15x)  116,040 đ  15.0 × EPS 7,736 [ref-8]
EV/EBITDA 8x           32,235 đ   (883.8×8 − nợ ròng 3,396 tỷ) ÷ 114M cp [ref-3]
DCF N/A  FCF 2025 âm (−208 tỷ, CFO −831 tỷ) → dùng EV/EBITDA-implied thay thế [ref-6]
P/CF N/A  CFO âm — không tính được [ref-6]
DDM N/A  thiếu data cổ tức chi tiết từ API [ref-9]
```
→ HPG (thép chu kỳ): **PHẢI có EV/EBITDA + P/E chuẩn hóa** (REQ-074 đã pass — giữ nguyên "P/E chuẩn hóa = 12,39×").

### 3.3. Sec-tech — "SCORE: SỐ + VERDICT: TÊN (nguồn)" + bảng chỉ báo

```
ACTIVE TIMING/VERDICT Technical ACTIVE (weekly 52 tuần) [ref-4]
SCORE: -4  VERDICT: SELL (nguồn: score tính từ các chỉ báo)
MA10 / MA20 / MA50  67,980 / 73,736 / 74,379 đ  giá dưới cả 3 MA — xu hướng giảm
RSI(14) 37.8  vùng yếu, chưa quá bán (tính theo công thức Wilder) [ref-4]
```

### 3.4. Sec-risk — drawdown claim PHẢI khớp data (±15pp) + [ref-N]

```
Kỹ thuật ngắn hạn  Trung bình  Xu hướng giảm: giá dưới MA10/20/50, max drawdown 52 tuần -40.6% [ref-4]
```
→ V4 bạn fail vì claim "giảm 50%"/"giảm 30%" KHÔNG khớp max_drawdown HPG (-22,3%). **Chỉ viết đúng số từ data**, hoặc thêm "ước tính" nếu không phải data.

### 3.5. Insight — "★ Special Insight N — tiêu đề" + bullet + [ref-N] từng claim

```
★ Special Insight 1 — News digest 30 ngày + điểm sentiment TỐT
Coteccons công bố KQKD niên độ 2026: LNST 788 tỷ (+72,7%) — theo CafeF, 31/07 [ref-11]
★ Special Insight 2 — KLGD, GTGD và cấu trúc vốn
... 3 mức vốn mặc định (100tr/500tr/1 tỷ) mà không ảnh hưởng giá đáng kể (ước tính)
★ Special Insight 3 — Profile daily 2 năm — ngôn ngữ trung lập
Max drawdown 2 năm: -40.6% [ref-13] ... VaR(95%) -3.8%/ngày [ref-13]
```

### 3.6. Split audit mention (REQ-003) — đúng câu mẫu

```
mọi số liệu tài chính được cross-check theo bẫy 5B (back-calc CP = LNST/EPS, split-adjusted khi cần) [ref-2]
... (dilution, không phải split — cross-check bẫy 5B đã ghi nhận) [ref-2]
```
→ task-state split_audit vẫn phải đủ keys: `cp_consistent`, `method`, `periods_checked`, `cp_per_year`.

### 3.7. Citation — mỗi số có NGUỒN NAMED + [ref-N] cùng câu

ĐÚNG: `LNST 788 tỷ (+72,7%) — theo CafeF, 31/07 [ref-11]`
SAI: `LNST 788 tỷ [ref-11]` (không tên nguồn — REQ-029 sẽ FAIL)

### 3.8. News (REQ-008) — sentiment SỐ + category breakdown

News section phải có: tổng bài, điểm sentiment SỐ (vd 62/100 → BULLISH), breakdown theo category (KQKD X bài, cổ tức Y bài...), mỗi bài có ngày + nguồn (REQ-041).

### 3.9. Investment amount (REQ-042) — "1 tỷ" trong đúng section investment

Viết đúng cụm như mẫu: `3 mức vốn mặc định (100tr/500tr/1 tỷ) ... (ước tính)` — số "1 tỷ" PHẢI xuất hiện trong sec-investment hoặc section được chỉ định.

## 4. QUY TRÌNH BẮT BUỘC

1. Verify lần 0 (ghi baseline)
2. **Mỗi vòng fix:** đối chiếu TỪNG REQ fail với mẫu mục 3 → sửa → verify lại. Tối thiểu 4 vòng, tối đa 6
3. Ghi log mỗi vòng: vòng mấy, sửa REQ nào, recall sau vòng
4. Điều kiện dừng: **≥ 68/74** hoặc hết 6 vòng → báo cáo trung thực

## 5. RÀNG BUỘC (KHÔNG được làm)

- ✗ Sửa source skill gốc — nghi lỗi skill thì GHI RÕ trong báo cáo (kèm bằng chứng)
- ✗ Dùng runner rút gọn / template fill
- ✗ Dừng trước vòng 4
- ✗ Bỏ phase nào
- ✗ Commit/push gì cả
- ✗ Bịa số liệu khi API lỗi — ghi `BLOCKED_API`

## 6. BÁO CÁO (tạo `/tmp/COHORT-REPORT-GLM-V5.md`)

| Hạng mục | Nội dung |
|---|---|
| Recall cuối | x/74 + tiến trình theo vòng |
| REQ fail cuối | id + lý do 1 dòng + phân loại (skill/data/narrative) |
| Vòng log | Bảng: vòng \| REQ sửa \| recall |
| REQ-074 | PASS/FAIL (phải giữ PASS) |
| Nghi lỗi skill | REQ nào fail mà bạn tin là verifier sai — KÈM BẰNG CHỨNG (evidence + đoạn HTML) |
| Maturity | Đủ bằng chứng PRODUCTION_READY? (≥65/74 = CÓ) |
| Token | Tổng ước tính |

## 7. TIÊU CHÍ THÀNH CÔNG

- **HPG ≥ 68/74** sau ≤ 6 vòng (dùng mẫu mục 3 — không còn lý do đoán format)
- REQ-074 vẫn PASS
- Mọi fail còn lại phân loại rõ + bằng chứng cho phần nghi verifier
