# Changelog

Tất cả thay đổi đáng chú ý của bộ skill `equity-research-vn`.

Format dựa trên [Keep a Changelog](https://keepachangelog.com/vi/1.1.0/), versioning theo [Semantic Versioning](https://semver.org/lang/vi/).

## [2.0.0] — 2026-06-24

### 🎉 vn-technical-analysis — Thêm mode PROFILE (stock profile methodology)

Nâng cấp `vn-technical-analysis` thêm lớp phân tích thứ 2 — **mode PROFILE** — hoạt động song song với mode ACTIVE (cũ). Methodology port từ dashboard `market_stats`: phân tích hồ sơ hành vi giá-khối lượng định lượng, ngôn ngữ phi-tư-vấn (`neutral_descriptive_non_advice`), KHÔNG verdict BUY/SELL.

### ✨ Added — mode PROFILE

- **17 block profile định lượng** (methodology từ dashboard phân tích thị trường nội bộ): price_behavior, volatility, drawdown, liquidity, return_distribution, tail_risk, liquidity_risk, VPCI, money_flow (OBV/VPT/CMF), effort-result (Wyckoff), high_volume_behavior, PVI/NVI, volume-at-price, relative_strength, dynamic_beta, correlation, regime
- **8 setup detection heuristic** chiều tăng: bull_flag, bull_pennant, ascending_triangle, falling_wedge, cup_with_handle, rectangle_bottom, double_bottom, measured_move_up — mỗi mẫu có score 0-100, status, watch_zone, reader_note
- **5 pattern family** classification + **4 stock archetype** (trend_following / accumulation_breakout / trap_prone / mixed)
- **13 metric dictionary** với guardrail Việt + CONSUMER_LABELS + scrubCopy rules + 4 điểm non-conclusion bắt buộc
- **Dashboard HTML single-page** (`profile_template.html`): dark theme + Chart.js + custom candlestick canvas + scrollspy. Pattern hấp thụ từ skill `longform` (component + chart recipe). Đồng nhất visual với `technical_template.html` (mode ACTIVE)
- **Biểu đồ nến + khối lượng** custom Canvas 2D (port từ mode ACTIVE) với MA20/MA50 + S/R = đỉnh/đáy 52 tuần
- **Ngôn ngữ đời thường**: đổi ~20 thuật ngữ khó (VaR/ES/underwater/Point of Control/percentile) sang tiếng Việt dễ hiểu, giữ thuật ngữ kỹ thuật trong ngoặc
- **100% portable với vnstock** — KHÔNG cần dependency ngoài. Loại bỏ phần local-only (scanner lịch sử) để chia sẻ an toàn

### 🔧 Changed

- `SKILL.md`: thêm bảng "Chọn mode (ACTIVE vs PROFILE)" + workflow mode PROFILE 5 bước (fetch → build 17 block → pattern scoring → narrative non-advice → render dashboard HTML)
- `agents/openai.yaml`: cập nhật description 2-mode

### 🛡️ Non-advice guardrail (methodology market_stats)

- `language_policy: neutral_descriptive_non_advice` — KHÔNG verdict BUY/SELL, KHÔNG "bullish/bearish/tín hiệu/khuyến nghị"
- Mỗi block có `interpretation_guardrail` cảnh báo đây là quan sát quá khứ
- 4 điểm non-conclusion bắt buộc cuối dashboard ("Không kết luận đây là khuyến nghị", "Tỷ lệ quá khứ không đảm bảo tương lai"...)
- QA checklist: grep token trống + canvas=new Chart + JS syntax + non-advice language

### 📊 Đã test end-to-end với HPG

- Fetch vnstock (585 phiên) → build 17 block + setup + archetype → render dashboard HTML (49KB)
- QA 5/5 PASS: token trống, canvas=5/Chart=4, JS syntax OK, non-advice pass, đủ 9 section
- Dashboard: biểu đồ nến 120 phiên + 4 chart phân tích (rolling percentile, distribution, VAP horizontal, benchmark base-100)

### 📚 Files

**Mới (5):**
- `vn-technical-analysis/references/stock_profile_blocks.md` — 17 block + code Python
- `vn-technical-analysis/references/pattern_scoring.md` — 8 setup + family + archetype (portable)
- `vn-technical-analysis/references/metric_guardrails.md` — 13 metric dict + non-advice rules + glossary
- `vn-technical-analysis/references/profile_render.md` — recipe map JSON→template + QA
- `vn-technical-analysis/assets/profile_template.html` — dashboard single-page + candlestick

**Sửa (2):**
- `vn-technical-analysis/SKILL.md` — 2-mode workflow
- `vn-technical-analysis/agents/openai.yaml` — description 2-mode

**Giữ nguyên (4):** indicators.md, pattern_detection.md, vnstock_usage.md, technical_template.html (mode ACTIVE)

### 🗺️ Roadmap cập nhật

- [x] ~~Stock profile methodology (mode PROFILE)~~ ✅ v2.0.0
- [ ] Peer comparison (`--peers BID,CTG,TCB`)
- [ ] Thêm ngành đặc thù (BĐS NAV, ngân hàng NIM/CASA)
- [ ] Elliott Wave + Fibonacci patterns
- [ ] Multi-language dashboard (EN/CN)

---

## [1.0.0] — 2026-06-21

### 🎉 Phiên bản đầu tiên — phát hành công khai

Pipeline 7 skills phân tích equity research cho cổ phiếu Việt Nam, kiểm chứng với case BSR (Bình Sơn Refining).

### ✨ Added (Tính năng mới)

- **Pipeline 7 bước tự động**: Data → Cơ bản → Định giá → Kỹ thuật → Tin tức → Dashboard → Deploy
- **7 skills** độc lập, có thể dùng riêng hoặc qua orchestrator `equity-research-vn`
- **Dashboard HTML** 10-12 sections với phong cách fintech hiện đại (dark theme, glassmorphism)
- **9 phương pháp định giá**: PE/PB median, EV/EBITDA, P/CF, P/S, DCF (3 scenarios), Graham, Reverse DCF, DDM
- **Technical analysis** với data thật vnstock: MA, RSI, MACD, Bollinger, Beta, Correlation, Pattern detection (evidence-based)
- **News digest** với sentiment scoring (-100 → +100) + category breakdown
- **7 bẫy dữ liệu** đặc thù VN (xem `data_pitfalls.md`)
- **Automated QA** với Playwright (verify canvas render + 0 JS errors)
- **Vercel deploy** tích hợp
- **Section "Tương quan giá dầu"** đặc thù ngành lọc hóa dầu (crack spread analysis)
- **Section "Independent view"** — điều quan trọng nhất + hiểu nhầm + quan điểm giá
- **Bear case section** — cân bằng với bull case, có catalyst triggers + case study warning

### 🛡️ 7 Bẫy dữ liệu đặc thù VN

1. Số CP lưu hành thay đổi — back-calc verify
2. Đơn vị tính sai (BVPS phình 1000x)
3. LNST vs LN trước thuế
4. Data cũ trong search results
5. Split-adjusted price
6. Vốn hóa sai format
7. **🔴 Split-adjustment consistency (Bẫy 5B, CRITICAL)** — adjust EPS/BVPS về cùng base với giá

### 📚 Lessons learned từ case BSR 2026

Pipeline đã được kiểm chứng thực tế với BSR (Bình Sơn Refining). Các lỗi đã mắc và cách phòng tránh:

1. **Split-adjustment consistency (Bẫy 5B)** — BSR chia tách 15/10/2025 (1.615x), vnstock trả giá split-adjusted nhưng BCTC dùng base CP gốc → PE/PB SAI hoàn toàn (PE sai 6.10x → đúng 9.85x). Đã add audit procedure đầu tiên.
2. **vnstock `Finance.ratio()` có thể stale** — chỉ trả 2018-2019 cho BSR dù request 2021-2025.
3. **EPS vnstock ≠ EPS BCTC** — BSR EPS 2021 vnstock = 2,073 đ, BCTC = 2,166 đ (MAS, PHS confirmed).
4. **Template HTML + Python inject** — f-string Python xung đột brace JS → syntax error khó debug. Đã chuyển sang placeholder `{{TOKEN}}` + string replace.
5. **Token replacement order matters** — vòng lặp replace phải chạy SAU khi tất cả token đã defined.
6. **Section 8 phải cân bằng Bull/Bear** — không chỉ bullish.
7. **Ngành đặc thù cần section riêng** — Refining (BSR) cần Section "Tương quan giá dầu" với crack spread analysis.

### 🎨 Phong cách dashboard

- Dark theme (#0a0a14) với radial gradient tím-hồng
- Glassmorphism cards (backdrop-filter blur)
- Chart.js với gradient fill, dual y-axis, neon colors
- Inter (sans) + JetBrains Mono (numbers)
- Sticky nav + scroll-spy + progress bar

### 📊 Output dashboard (case BSR)

- File size: 122.3 KB
- 11 canvas charts (Chart.js)
- 12 sections + 12 nav links
- QA PASS (9/9 checks: canvas render + 0 JS errors + sections + nav)
- Deploy: https://bsr-deploy.vercel.app

### 🔧 Tech stack

- **Python 3.11+**: vnstock, yfinance, pandas, numpy
- **Node.js 18+**: Chart.js, chartjs-plugin-annotation
- **Playwright**: automated QA
- **Vercel**: deploy
- **AI agent**: ZCode/Z.AI (GLM), Claude Code, Codex

### 📋 Supported tickers

Đã verify hoạt động: VCB, FPT, HPG, MWG, VNM, BSR, GAS, ACB, MBB, VIC, VHM, PLX, PVC, DPM, DGC...

### 🚧 Known limitations

- vnstock `Finance.ratio()` có thể stale cho một số mã (workaround: tự tính từ BCTC)
- Web search cho tin tức có thể index tin cũ (workaround: lọc theo ngày)
- DCF cực nhạy với giả định — luôn trình bày cả 3 scenarios
- Free float thấp (BSR 8%) làm giá biến động mạnh, khó phân tích kỹ thuật

### 🗺️ Roadmap 1.x

- [ ] Peer comparison (`--peers BID,CTG,TCB`)
- [ ] Thêm ngành đặc thù (BĐS NAV, ngân hàng NIM/CASA)
- [ ] Elliott Wave + Fibonacci patterns
- [ ] Multi-language dashboard (EN/CN)
- [ ] Real-time data (WebSocket) thay vì daily
- [ ] Backtesting trading strategy
