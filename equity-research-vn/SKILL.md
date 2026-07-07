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

## ⚠️ Phase 0 BẮT BUỘC — Hỏi user trước khi chạy

**KHÔNG mặc định bất kỳ tham số nào.** Trước khi fetch data, hỏi user:

1. **Số vốn dự kiến giải ngân** (VND hoặc USD) — ví dụ "200 triệu VND", "$5,000", "$33,000". **KHÔNG default $33,000.** Mỗi nhà đầu tư có vốn khác nhau.
2. **Kỳ vọng thời gian** — 1 năm? 3-5 năm? Dài hạn?
3. **Mục tiêu** — đầu tư giá trị? Tăng trưởng? Cổ tức?
4. **Risk tolerance** — chịu được drawdown bao nhiêu %?

Các tham số này ảnh hưởng trực tiếp:
- **Section "Góc nhìn vốn"** — số cổ phiếu, drawdown tolerance, DCA framework
- **Disclaimer** — "nếu là tiền của tôi" gắn với số vốn thật
- **Checklist** — câu hỏi tolerance phù hợp vốn thật

**Nếu user không trả lời**, dùng placeholder `[VỐN_CỦA_BẠN]` + flag "vui lòng cho biết số vốn để cá nhân hóa" — KHÔNG bịa số default.

## Pipeline 6 skill (chạy tuần tự)

### Bước 0: Detect sponsor package (BẮT BUỘC trước khi fetch — học từ CTD test 7/2026)

⚠️ **vnstock 4.0 có 2 cách dùng, khác biệt cực lớn:**

| Cách import | Tier | Số kỳ BCTC | Khi nào dùng |
|---|---|---|---|
| `from vnstock import ...` (community) | Free | **8 kỳ** (~2 năm) | Mặc định, không cần config |
| `from vnstock_data import ...` (sponsor) | Gold/Platinum | **40+ kỳ** (10+ năm) | Cần sponsor package + đã auth |

**Detect sponsor:**
```bash
# Check ~/.vnstock/auth_state.json — nếu "tier": "golden" → sponsor OK
cat ~/.vnstock/auth_state.json 2>/dev/null | grep tier

# Hoặc test import trong Python:
python3 -c "from vnstock_data import Finance; print('sponsor OK')" 2>/dev/null
# Nếu lỗi (vnstock 3.x / chưa cài sponsor package) → dùng `from vnstock import ...`
```

**Quy tắc:**
- Nếu sponsor OK → **dùng `from vnstock_data import Finance, Company, Quote`** + **dùng sponsor venv Python** (vd `/Users/bobo/dev/main-sonet-runtime/.venv-vnstock-sponsor311/bin/python`). Fetch 5 năm đầy đủ.
- Nếu sponsor KHÔNG có → dùng `from vnstock import ...` (community, 8 kỳ) + **WebFetch CafeF/Vietstock bổ sung 12 kỳ cũ**. Flag "community edition, history limited".

**⚠️ venv sponsor** thường nằm ở `/Users/bobo/dev/main-sonet-runtime/.venv-vnstock-sponsor311/`. Khi chạy script Python (preflight, audit_split, fetch), dùng path Python sponsor venv này thay vì `python3` system.

**Cấu trúc data khác nhau** giữa 2 gói:
- `vnstock` 4.0 (community): DataFrame có cột `item`, `item_en`, `item_id` + period columns
- `vnstock_data` 3.x (sponsor): DataFrame có cột tiếng Anh HOA (`Net sales`, `Attributable to parent company`, `EPS basic (VND)`, `Total Assets`, `Owner's Equity`...) + `report_period` = 'year'/'quarter'

→ **Code fetch phải handle cả 2 format.** Tham khảo `scripts/preflight.py` đã handle cả 2 (v2.2.1).

### Bước 1: Thu thập data → skill `vn-financial-data-collector`
- Kỳ phân tích 5 năm gần nhất: **2021-2025** (tháng hiện tại ≥ 4 → N-1 đã có BCTC)
- **NGUỒN #1: vnstock API** — fetch BCTC, ratios, info qua `Finance` + `Company` modules
- Web scraping (CafeF/Vietstock/QHCD DN) CHỈ khi vnstock thiếu (BCTC PDF, tin tức >50 bài)
- Áp dụng **8 bẫy dữ liệu** (số CP từng năm, đơn vị, LNST thuộc CĐ mẹ, data cũ, split-adjusted, vốn hóa, **split-adjustment consistency Bẫy 5B**)
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

### Bước 4: Phân tích kỹ thuật → skill `vn-technical-analysis` — **DATA THẬT vnstock + CHẠY CẢ 2 MODE**

⚠️ **QUAN TRỌNG: Phải chạy CẢ HAI mode** của skill `vn-technical-analysis`. Đây là 2 góc nhìn khác nhau, KHÔNG thay thế nhau:

#### Mode 4a — ACTIVE (timing, verdict mua/bán)
- Fetch giá **weekly** 52 tuần (22/06/2025 → 21/06/2026) qua `Quote.history(interval='1W')`
- Lấy VNINDEX + VN30 qua `Quote(symbol='VNINDEX')` để tính Beta/Correlation/Alpha
- Market cap, số CP, 52W high/low từ `Company.overview()`
- Tính: MA10/20/50, RSI(14), MACD, Bollinger, Beta
- Phát hiện patterns (Double Bottom, Channel, Candlestick, Divergence) CHỈ KHI có evidence
- Output: **Tech Score -6→+6, Verdict (STRONG SELL → STRONG BUY)**, trading strategy 3 kịch bản
- Đọc `vn-technical-analysis/references/vnstock_usage.md` + `indicators.md` + `pattern_detection.md`

#### Mode 4b — PROFILE (hồ sơ giá-khối lượng, mô tả, NON-ADVICE)
- Fetch giá **daily** ~2 năm (≥252 phiên, lý tưởng ~537 phiên) qua `Quote.history(interval='1D')` cho `[TICKER]` + VNINDEX + VN30
- ⚠️ `value = close × volume × 1000` (vnstock giá = nghìn đồng, ×1000 ra đồng)
- Tính **15 block profile** (port Python từ `references/stock_profile_blocks.md`, 100% portable với vnstock):
  - price_behavior, volatility (HV20/60/120/252), drawdown (episodes, underwater days)
  - liquidity, return_distribution, tail_risk (historical VaR/ES), liquidity_risk
  - volume_price, VPCI (xác nhận giá-volume), money_flow (OBV/VPT/CMF)
  - effort_result (Wyckoff), high_volume_behavior (event study), pvi_nvi, volume_at_price (VAP)
- Tính **8 setup heuristic** + **archetype** (trend_following / accumulation_breakout / trap_prone / mixed) từ `references/pattern_scoring.md`
- Output: **profile JSON schema `vn-technical-profile-v1`**, KHÔNG verdict mua/bán
- **NGÔN NGỮ BẮT BUỘC: `neutral_descriptive_non_advice`** — KHÔNG dùng "bullish/bearish/tín hiệu/khuyến nghị/strong buy/sell". Mỗi block kèm `interpretation_guardrail`. Kết thúc bằng 4 điểm non-conclusion
- Đọc `vn-technical-analysis/references/stock_profile_blocks.md` + `pattern_scoring.md` + `metric_guardrails.md`

#### Nguyên tắc chung cả 2 mode:
- **TUYỆT ĐỐI KHÔNG mô phỏng data** — data thật từ vnstock
- Nếu không fetch được → nói thẳng "không có data", KHÔNG tự bổ sung

### Bước 5: Bản tin 30 ngày → skill `vn-news-digest`
- Kỳ: 22/05/2026 → 21/06/2026
- **NGUỒN #1: vnstock** `Company.news()` (50 tin) + `Company.events()` (50 sự kiện công bố)
- **Nguồn #2: WebSearch** (chỉ bổ sung cho tin ngành/vĩ mô vnstock không có)
- Phân loại 5 nhóm (biz/sector/macro/disclosure/analyst)
- Sentiment score + category breakdown (BẮT BUỘC)
- Đọc `vn-news-digest/references/sentiment_scoring.md` + `news_sources.md`

### Bước 6: Dashboard HTML → skill `vn-research-dashboard`
- Tạo file `[TICKER]_Complete_Report.html` với **11-13 sections** (mở rộng tùy ngành):
  1. Hero + 6 KPI cards
  2. Executive Summary (TL;DR + 4 highlight boxes)
  3. Kết quả kinh doanh 5 năm
  4. Định giá PE/PB
  5. Multiples mở rộng
  6. DCF & Graham
  7. DuPont
  8. Special Insights ngành (Bull + Bear Case + Catalyst Roadmap) — **CÂN BẰNG**, không chỉ bullish
  9. Technical Analysis **mode ACTIVE** (data vnstock: candlestick + volume + indicators + correlation vs VNINDEX/VN30 + patterns + divergence check + trading strategy + Tech Score + Verdict + minh bạch dữ liệu)
  9b. **🧬 Pro Stock Profile mode PROFILE** (15 block định lượng + 8 setups + archetype + 4 điểm non-conclusion; ngôn ngữ non-advice; TÁCH BẠCH với section 9 — KHÔNG trộn ACTIVE/PROFILE)
  9.5. **🛢️ Tương quan giá dầu** (CHỈ cho ngành lọc hóa dầu/dầu khí — case BSR): crack spread analysis, BSR vs Brent scatter, annual + quarterly LNST correlation
  10. News Digest 30 ngày
  11. **🎯 Quan điểm độc lập** (luôn có): điều quan trọng nhất với doanh nghiệp này / hiểu nhầm thường mắc / quan điểm giá — tổng hợp sau toàn bộ phân tích, không lặp lại báo cáo CTCK
- **Section 8 (Insights) phải cân bằng**: 3 insight cards bullish + 3 insight cards bearish + catalyst timeline + case study warning (nếu có precedent giảm kế hoạch LNST)
- **⚠️ Section 9 vs 9b KHÔNG trộn ngôn ngữ**: Section 9 (ACTIVE) dùng Tech Score/Verdict/bullish-bearish. Section 9b (PROFILE) dùng mô tả + guardrail, KHÔNG verdict. Đọc `metric_guardrails.md` forbidden list
- Thêm navigation bar (sticky top nav + scroll-spy) + progress bar + back-to-top
- **Intent Router**: auto-detect sector từ `Company.overview()['sector']` → chọn sections ưu tiên (xem `vn-research-dashboard/references/style_variants.md` Layout Router). Ngành dầu khí → thêm Section 9.5 tương quan giá dầu
- Verify JS syntax (`node --check`) trước khi hoàn tất
- **Verify placeholders ĐÃ THAY THẾ**: `grep -o "{{[A-Z_]*}}" file.html | sort -u` phải trả empty (xem `data_binding.md` Template + inject pattern)
- **Verify ngôn ngữ non-advice ở section PROFILE**: `grep -iE "bullish|bearish|strong buy|strong sell|khuyến nghị mua|khuyến nghị bán|tín hiệu vào|tín hiệu ra"` trong nội dung section PROFILE phải trả empty
- **Automated QA**: chạy `scripts/qa_dashboard.js` (Playwright) → verify canvas render + 0 errors + screenshots
- Phong cách: fintech hiện đại (dark + gradient tím-hồng, glassmorphism) — trừ khi user chọn `--style bloomberg` hoặc `--style corporate`
- Đọc `vn-research-dashboard/references/data_binding.md` (ESPECIALLY phần Template + inject pattern) + `chart_recipes.md` + `style_variants.md`

### Bước 7: Deploy (hỏi user trước)
- Nếu user đồng ý: `~/.local/bin/vercel deploy [folder] --prod --yes`
- Trả về URL Vercel

## Tùy chọn (user có thể thêm vào sau ticker)

| Tùy chọn | Ví dụ | Action |
|---|---|---|
| Bỏ technical/news | `/equity-research-vn VCB --fundamental-only` | Chỉ bước 1-3 + 6 (7 sections) — bỏ cả 2 mode kỹ thuật (ACTIVE + PROFILE) + news |
| Đổi phong cách | `/equity-research-vn FPT --style bloomberg` | Phong cách Bloomberg Terminal tối |
| Đổi kỳ phân tích | `/equity-research-vn MWG --period 3y` | Kỳ 3 năm (2023-2025) |
| Thêm peer comparison | `/equity-research-vn VCB --peers BID,CTG,TCB` | So sánh với peer ngành |
| Không deploy | `/equity-research-vn VNM --no-deploy` | Chỉ tạo file local |

Nếu không có tùy chọn → chạy full pipeline mặc định.

## Output cuối cùng

1. **File `[TICKER]_Complete_Report.html`** (dashboard đầy đủ 11-13 sections, ~100-130 KB) — gồm cả Technical ACTIVE (section 9) + Pro Stock Profile (section 9b)
2. **Tóm tắt JSON** kết quả (data + indicators + valuation + tech verdict + sentiment + **profile JSON schema `vn-technical-profile-v1`**)
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
- ✅ Bước 4: Kỹ thuật — **báo CẢ 2 mode**: ACTIVE (score X/6, verdict Y, Z patterns) + PROFILE (archetype W, N setups, block highlights)
- ✅ Bước 5: News (sentiment X, Y tin)
- ✅ Bước 6: Dashboard (Z KB, X charts, N sections — verify đủ cả Technical ACTIVE + Pro Profile)
- ✅ Bước 7: Deploy (URL)

## Lưu ý thực thi

- Pipeline mất **15-30 phút** tùy mã (fetch data + tính toán + render + deploy)
- **vnstock cần Python 3.11+** — nếu lỗi import: `pip install vnstock --upgrade`
- **Data freshness**: BCTC kiểm toán công bố ~27/03 năm sau
- **Vercel deploy**: cần đã login (`vercel login`) — 1 lần duy nhất
- Nếu 1 bước fail → báo lỗi rõ, KHÔNG tự bỏ qua hoặc fake data

## ⚠️ Lessons learned (từ case BSR 2026 + FPT 2026)

Các lỗi đã mắc và cách phòng tránh:

1. **Split-adjustment consistency (Bẫy 5B)** — vnstock `Quote.history()` trả giá split-adjusted, BCTC dùng base CP gốc → mix chuẩn → PE/PB SAI hoàn toàn (BSR: PE sai 6.10x → đúng 9.85x). **Luôn audit split đầu tiên** và adjust EPS/BVPS về cùng base.

2. **vnstock `Finance.ratio()` có thể stale** — chỉ trả data 2018-2019 cho BSR dù request 2021-2025. **Không tin ratio() tính sẵn**, tự tính từ income_statement + balance_sheet.

3. **EPS vnstock ≠ EPS BCTC gốc** — BSR EPS 2021 vnstock = 2,073 đ, BCTC = 2,166 đ (MAS, PHS confirmed). **Cross-check EPS qua back-calc** `CP = LNST/EPS` và verify với báo cáo CTCK.

4. **Template HTML + Python inject** — KHÔNG dùng f-string Python với JS (xung đột brace). Dùng placeholder `{{TOKEN}}` + string replace. Token replacement loop phải chạy **SAU KHI tất cả token đã defined** (đã mắc bug placeholder không replace).

5. **Section 8 phải cân bằng Bull/Bear** — không chỉ bullish. Thêm Bear Case section với catalyst triggers + case study warning (BSR từng giảm 75% KH LNST 2024).

6. **Section cuối = Independent view** — tổng hợp sau toàn bộ phân tích, không lặp lại báo cáo CTCK. 3 phần: điều quan trọng nhất / hiểu nhầm thường mắc / quan điểm giá.

7. **Ngành đặc thù cần section riêng** — Refining (BSR) cần Section "Tương quan giá dầu" với crack spread analysis (không phải Brent trực tiếp). Ngành khác có thể cần section tương tự (BĐS = NAV, ngân hàng = NIM).

8. **Verify placeholders trước khi deploy** — `grep -o "{{[A-Z_]*}}" file.html | sort -u` phải trả empty. QA script chỉ check canvas/sections, không check placeholder chưa replace.

9. **⚠️ Chạy CẢ 2 mode kỹ thuật (ACTIVE + PROFILE)** — Case FPT 2026: đã mặc định mode ACTIVE (Tech Score/Verdict) mà bỏ sót mode PROFILE (15 block pro stock profile + archetype). Skill `vn-technical-analysis` có 2 mode TÁCH BIỆT, KHÔNG thay thế nhau:
   - **Mode ACTIVE** (section 9): timing mua/bán, Tech Score, verdict, dùng ngôn ngữ "bullish/bearish/tín hiệu"
   - **Mode PROFILE** (section 9b): hồ sơ giá-khối lượng, mô tả, **NON-ADVICE**, dùng ngôn ngữ "đang tăng/đang giảm/quan sát" + guardrail. Tính 15 block định lượng (HV, drawdown, VPCI, money flow, effort-result, VAP...) + 8 setup heuristic + archetype
   - **Cần 2 nguồn data khác nhau**: ACTIVE dùng weekly 52 tuần, PROFILE dùng **daily ~2 năm (≥252 phiên)** cho rolling/percentile có ý nghĩa
   - **KHÔNG trộn ngôn ngữ**: verify `grep -iE "bullish|bearish|strong buy|khuyến nghị mua"` trong section PROFILE phải trả empty
   - **Port Python** từ `references/stock_profile_blocks.md` + `pattern_scoring.md` — 100% portable với vnstock, tái dùng được cho mọi mã

10. **✅ Template đã tokenize + dùng `_viz-shared/` design system (refactor 2026-06)** — Giải quyết root cause của bug #4 (placeholder không replace). Trước đây `dashboard_template.html` + `technical_template.html` hard-code HPG → mỗi lần chạy phải edit tay → sót placeholder. Giờ:
    - Cả 2 template dùng `{{UPPER_TOKEN}}` (`{{TICKER}}`, `{{COMPANY_NAME}}`, `{{KPI_STRIP}}`, ...) — fill qua `str.replace`, KHÔNG bao giờ edit inline
    - CSS palette + components + chart helper + candlestick renderer gom vào `../_viz-shared/` (single source of truth, DRY)
    - Chart rendering qua `viz.chart(id, spec)` registry — base options (legend/grid) tự merge, KHÔNG lặp
    - Theme switch (Bloomberg/Corporate) = `data-theme="..."` attribute, KHÔNG rewrite `:root`
    - **Sửa design chung**: edit `_viz-shared/*.{css,js}` → chạy `python3 _viz-shared/inject.py` → tái sinh templates self-contained
    - Verify: `grep -oE "\{\{[A-Z_0-9]+\}\}" file.html` phải empty sau fill

## Báo cáo tiến độ
