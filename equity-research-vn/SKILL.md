---
name: equity-research-vn
description: "Phân tích equity research đầy đủ cho cổ phiếu Việt Nam — pipeline 6 skill tự động (data → cơ bản → định giá → kỹ thuật → tin tức → dashboard). TRIGGER khi user gõ /equity-research-vn [TICKER] hoặc yêu cầu 'phân tích đầy đủ', 'complete equity research', 'báo cáo đầy đủ' cho mã CP VN cụ thể (HPG, VCB, FPT, MWG, VNM...). Cốt lõi = chạy pipeline 6 skill theo thứ tự, output = dashboard HTML 10 sections + deploy Vercel."
---

# /equity-research-vn [TICKER]

Slash command chạy pipeline 6 skill equity research cho cổ phiếu Việt Nam.

## Cách dùng

```
/equity-research-vn VCB        # Phân tích đầy đủ Vietcombank
/equity-research-vn FPT        # Phân tích đầy đủ FPT Corporation
/equity-research-vn HPG        # Phân tích đầy đủ Hòa Phát
```

`[TICKER]` = mã cổ phiếu HOSE/HNX/UPCOM (VCB, FPT, HPG, MWG, VNM, VIC, VHM, GAS, ACB, MBB...)

## Pipeline 6 skill (chạy tuần tự)

### Bước 1: Thu thập data → skill `vn-financial-data-collector`
- Kỳ phân tích 5 năm gần nhất: **2021-2025** (tháng hiện tại ≥ 4 → N-1 đã có BCTC)
- **NGUỒN #1: vnstock API** — fetch BCTC, ratios, info qua `Finance` + `Company` modules
- Web scraping (CafeF/Vietstock/QHCD DN) CHỈ khi vnstock thiếu (BCTC PDF, tin tức >50 bài)
- Áp dụng **7 bẫy dữ liệu** (số CP từng năm, đơn vị, LNST thuộc CĐ mẹ, data cũ, split-adjusted, vốn hóa, **split-adjustment consistency Bẫy 5B**)
- **⚠️ AUDIT BẮT BUỘC ĐẦU TIÊN (Bẫy 5B):** Chạy audit split trước khi tính EPS/PE/PB:
  1. Check `Company.events()` cho split/dividend-stock event
  2. Check `Company.capital_history()` (KBS) cho vốn điều lệ tăng đột biến
  3. Back-calc `CP = LNST/EPS` từng năm — nếu CP mismatch > 5% → adjust EPS/BVPS về cùng base với giá
  4. **Nếu split xảy ra trong kỳ phân tích**: adjust EPS/BVPS/shares cho TẤT CẢ năm về base post-split, và compute PE/PB trên cùng base. Verify: PE_pre-split = PE_post-split
- Đọc `vn-financial-data-collector/references/vnstock_api.md` (NGUỒN #1, chú ý phần **ratio() stale warning**) + `data_pitfalls.md` (đặc biệt Bẫy 5B + Audit procedure đầu tiên)

### Bước 2: Phân tích cơ bản → skill `vn-fundamental-analysis`
- EPS, BVPS, ROE, ROA, ROS từng năm (có sẵn trong `Finance.ratio()`)
- DuPont decomposition (Biên LN × Vòng quay TS × Đòn bẩy)
- CAGR full 5N + recovery (nếu cổ phiếu chu kỳ)
- Đọc `vn-fundamental-analysis/references/dupont_interpretation.md`

### Bước 3: Định giá → skill `vn-valuation-engine`
- Chọn PP theo ngành (đọc `vn-financial-data-collector/references/sector_insights.md`)
- PE/PB/EV-EBITDA/ROE có sẵn trong `Finance.ratio()` — verify vs tự tính
- 9 PP: PE/PB median 5N, EV/EBITDA, P/CF, P/S, DCF (3 kịch bản), DDM, Graham, Reverse DCF
- Target price analyst từ `Company.overview()['target_price']` — tham khảo
- Hội tụ → median + dải P25-P75 → khuyến nghị
- Đọc `vn-valuation-engine/references/valuation_formulas.md` + `wacc_estimates.md`

### Bước 4: Phân tích kỹ thuật → skill `vn-technical-analysis` — **DATA THẬT vnstock**
- Fetch giá thực từ vnstock `Quote.history()` (KHÔNG mô phỏng)
- Kỳ: 52 tuần (22/06/2025 → 21/06/2026)
- Lấy VNINDEX + VN30 qua `Quote(symbol='VNINDEX')` để tính Beta/Correlation/Alpha
- Market cap, số CP, 52W high/low từ `Company.overview()`
- Tính: MA10/20/50, RSI(14), MACD, Bollinger, Beta
- Phát hiện patterns CHỈ KHI có evidence
- **TUYỆT ĐỐI KHÔNG mô phỏng data**
- Đọc `vn-technical-analysis/references/vnstock_usage.md` + `indicators.md` + `pattern_detection.md`

### Bước 5: Bản tin 30 ngày → skill `vn-news-digest`
- Kỳ: 22/05/2026 → 21/06/2026
- **NGUỒN #1: vnstock** `Company.news()` (50 tin) + `Company.events()` (50 sự kiện công bố)
- **Nguồn #2: WebSearch** (chỉ bổ sung cho tin ngành/vĩ mô vnstock không có)
- Phân loại 5 nhóm (biz/sector/macro/disclosure/analyst)
- Sentiment score + category breakdown (BẮT BUỘC)
- Đọc `vn-news-digest/references/sentiment_scoring.md` + `news_sources.md`

### Bước 6: Dashboard HTML → skill `vn-research-dashboard`
- Tạo file `[TICKER]_Complete_Report.html` với **10-12 sections** (mở rộng tùy ngành):
  1. Hero + 6 KPI cards
  2. Executive Summary (TL;DR + 4 highlight boxes)
  3. Kết quả kinh doanh 5 năm
  4. Định giá PE/PB
  5. Multiples mở rộng
  6. DCF & Graham
  7. DuPont
  8. Special Insights ngành (Bull + Bear Case + Catalyst Roadmap) — **CÂN BẰNG**, không chỉ bullish
  9. Technical Analysis (data vnstock: candlestick + volume + indicators + correlation vs VNINDEX/VN30 + patterns + divergence check + trading strategy + minh bạch dữ liệu)
  9.5. **🛢️ Tương quan giá dầu** (CHỈ cho ngành lọc hóa dầu/dầu khí — case BSR): crack spread analysis, BSR vs Brent scatter, annual + quarterly LNST correlation
  10. News Digest 30 ngày
  11. **🎯 Quan điểm độc lập** (luôn có): điều quan trọng nhất với doanh nghiệp này / hiểu nhầm thường mắc / quan điểm giá — tổng hợp sau toàn bộ phân tích, không lặp lại báo cáo CTCK
- **Section 8 (Insights) phải cân bằng**: 3 insight cards bullish + 3 insight cards bearish + catalyst timeline + case study warning (nếu có precedent giảm kế hoạch LNST)
- Thêm navigation bar (sticky top nav + scroll-spy) + progress bar + back-to-top
- **Intent Router**: auto-detect sector từ `Company.overview()['sector']` → chọn sections ưu tiên (xem `vn-research-dashboard/references/style_variants.md` Layout Router). Ngành dầu khí → thêm Section 9.5 tương quan giá dầu
- Verify JS syntax (`node --check`) trước khi hoàn tất
- **Verify placeholders ĐÃ THAY THẾ**: `grep -o "{{[A-Z_]*}}" file.html | sort -u` phải trả empty (xem `data_binding.md` Template + inject pattern)
- **Automated QA**: chạy `scripts/qa_dashboard.js` (Playwright) → verify canvas render + 0 errors + screenshots
- Phong cách: fintech hiện đại (dark + gradient tím-hồng, glassmorphism) — trừ khi user chọn `--style bloomberg` hoặc `--style corporate`
- Đọc `vn-research-dashboard/references/data_binding.md` (ESPECIALLY phần Template + inject pattern) + `chart_recipes.md` + `style_variants.md`

### Bước 7: Deploy (hỏi user trước)
- Nếu user đồng ý: `~/.local/bin/vercel deploy [folder] --prod --yes`
- Trả về URL Vercel

## Tùy chọn (user có thể thêm vào sau ticker)

| Tùy chọn | Ví dụ | Action |
|---|---|---|
| Bỏ technical/news | `/equity-research-vn VCB --fundamental-only` | Chỉ bước 1-3 + 6 (7 sections) |
| Đổi phong cách | `/equity-research-vn FPT --style bloomberg` | Phong cách Bloomberg Terminal tối |
| Đổi kỳ phân tích | `/equity-research-vn MWG --period 3y` | Kỳ 3 năm (2023-2025) |
| Thêm peer comparison | `/equity-research-vn VCB --peers BID,CTG,TCB` | So sánh với peer ngành |
| Không deploy | `/equity-research-vn VNM --no-deploy` | Chỉ tạo file local |

Nếu không có tùy chọn → chạy full pipeline mặc định.

## Output cuối cùng

1. **File `[TICKER]_Complete_Report.html`** (dashboard đầy đủ 10 sections, ~100-130 KB)
2. **Tóm tắt JSON** kết quả (data + indicators + valuation + tech verdict + sentiment)
3. **URL Vercel** (nếu deploy)

## Nguyên tắc cốt lõi (áp dụng cho mọi bước)

- ✅ **Data THẬT** từ nguồn chính thức (Vietstock/CafeF/vnstock API/BCTC DN)
- ✅ **Cross-check** nhiều nguồn cho số liệu quan trọng (LNST, VCSH, EPS)
- ✅ **Patterns chỉ claim khi có evidence** rõ
- ✅ **Thành thật** về data: nếu không có → nói "không có"
- ❌ **KHÔNG mô phỏng/ngụy tạo** data giá
- ❌ **KHÔNG claim** divergence/pattern nếu data không show
- ❌ **KHÔNG dùng data cũ** (>1 năm) cho phân tích "gần nhất"

## Báo cáo tiến độ

Sau mỗi bước, báo cáo ngắn:
- ✅ Bước 1: Data thu thập (X nguồn, Y bẫy áp dụng)
- ✅ Bước 2: Cơ bản (ROE X%, DuPont pattern Y)
- ✅ Bước 3: Định giá (median X đ, khuyến nghị Y)
- ✅ Bước 4: Kỹ thuật (score X/6, verdict Y, Z patterns)
- ✅ Bước 5: News (sentiment X, Y tin)
- ✅ Bước 6: Dashboard (Z KB, X charts)
- ✅ Bước 7: Deploy (URL)

## Lưu ý thực thi

- Pipeline mất **15-30 phút** tùy mã (fetch data + tính toán + render + deploy)
- **vnstock cần Python 3.11+** — nếu lỗi import: `pip install vnstock --upgrade`
- **Data freshness**: BCTC kiểm toán công bố ~27/03 năm sau
- **Vercel deploy**: cần đã login (`vercel login`) — 1 lần duy nhất
- Nếu 1 bước fail → báo lỗi rõ, KHÔNG tự bỏ qua hoặc fake data

## ⚠️ Lessons learned (từ case BSR 2026)

Các lỗi đã mắc và cách phòng tránh:

1. **Split-adjustment consistency (Bẫy 5B)** — vnstock `Quote.history()` trả giá split-adjusted, BCTC dùng base CP gốc → mix chuẩn → PE/PB SAI hoàn toàn (BSR: PE sai 6.10x → đúng 9.85x). **Luôn audit split đầu tiên** và adjust EPS/BVPS về cùng base.

2. **vnstock `Finance.ratio()` có thể stale** — chỉ trả data 2018-2019 cho BSR dù request 2021-2025. **Không tin ratio() tính sẵn**, tự tính từ income_statement + balance_sheet.

3. **EPS vnstock ≠ EPS BCTC gốc** — BSR EPS 2021 vnstock = 2,073 đ, BCTC = 2,166 đ (MAS, PHS confirmed). **Cross-check EPS qua back-calc** `CP = LNST/EPS` và verify với báo cáo CTCK.

4. **Template HTML + Python inject** — KHÔNG dùng f-string Python với JS (xung đột brace). Dùng placeholder `{{TOKEN}}` + string replace. Token replacement loop phải chạy **SAU KHI tất cả token đã defined** (đã mắc bug placeholder không replace).

5. **Section 8 phải cân bằng Bull/Bear** — không chỉ bullish. Thêm Bear Case section với catalyst triggers + case study warning (BSR từng giảm 75% KH LNST 2024).

6. **Section cuối = Independent view** — tổng hợp sau toàn bộ phân tích, không lặp lại báo cáo CTCK. 3 phần: điều quan trọng nhất / hiểu nhầm thường mắc / quan điểm giá.

7. **Ngành đặc thù cần section riêng** — Refining (BSR) cần Section "Tương quan giá dầu" với crack spread analysis (không phải Brent trực tiếp). Ngành khác có thể cần section tương tự (BĐS = NAV, ngân hàng = NIM).

8. **Verify placeholders trước khi deploy** — `grep -o "{{[A-Z_]*}}" file.html | sort -u` phải trả empty. QA script chỉ check canvas/sections, không check placeholder chưa replace.

## Báo cáo tiến độ
