# Changelog

Tất cả thay đổi đáng chú ý của bộ skill `equity-research-vn`.

Format dựa trên [Keep a Changelog](https://keepachangelog.com/vi/1.1.0/), versioning theo [Semantic Versioning](https://semver.org/lang/vi/).

## [2.2.5] — 2026-07-07

### ⚠️ CHẤT LƯỢNG > TỐC ĐỘ — Quality Gate cứng

User insight: "vì sao gap vẫn xảy ra dù đã học hỏi?" → vì lessons đi vào reference files nhưng khi build KHÔNG đọc lại.

#### Added — 4 rules structural

- **Rule 1**: Đọc lại reference files TRƯỚC mỗi phase (table phase → reference BẮT BUỘC)
- **Rule 2**: Quality Gate 12 checks (grep verify) trước deploy — BLOCK nếu fail
  - Charts ≥10, Citations ≥10, Sections ≥20, Callouts ≥5, Honest corrections ≥3
  - DQ rows ≥10, Source refs ≥10, Tokens=0, PROFILE non-advice, Div balance, GAAP flag, FY flag
- **Rule 3**: Benchmark comparison — nếu <80% benchmark → BLOCK deploy
- **Rule 4**: KHÔNG "xong vội" — chất lượng > tốc độ, "hoàn thành" = pass ALL gates

#### Root cause fix

| Vấn đề | Khắc phục structural |
|---|---|
| Lessons vào reference nhưng không đọc khi build | Rule 1: ép mở reference trước mỗi phase |
| Build theo "nhớ" → thiếu charts/citations | Rule 2: grep verify 12 metrics |
| Không benchmark comparison | Rule 3: so sánh vs ORCL/NEM, <80% = BLOCK |
| Ưu tiên tốc độ | Rule 4: KHÔNG "xong vội" |

---
## [2.2.4] — 2026-07-07

### 🐛 Fix từ CTD test round 3 — báo cáo thiếu charts

User so sánh CTD vs ORCL: "số biểu đồ ít hơn, technical kém hơn hẳn".

#### Added
- **data_pitfalls.md Bẫy 9**: "Báo cáo thiếu biểu đồ — visual gap"
  - Dashboard report PHẢI có tối thiểu 10 charts
  - Verify `grep -c 'new Chart'` ≥ 10 trước deploy
  - Chart data phải thật, không simulate
- CTD report: thêm 11 charts (Revenue/LNST, CFO vs LNST, Backlog, P/E/P/B, Valuation, Debt/Equity, Peer scatter, Price+MA, RSI, Drawdown, Distribution)
- 8→9 bẫy pitfalls

#### Lesson
| Vấn đề | Khắc phục |
|---|---|
| CTD 0 charts vs ORCL 13 charts | Bẫy 9: minimum 10 charts requirement |
| Technical kém (chỉ tables) | Price+MA, RSI, Drawdown, Distribution charts thêm vào |

---

## [2.2.3] — 2026-07-07

### ✨ Added — Đặc thù ngành (bản chất ngành nghề)

User insight: "phải nhìn vào bản chất dn để phân tích các con số tài chính, nếu không sẽ bias".

#### Thêm vào insight_frames_vn.md

- **Section F: Đặc thù ngành — đọc số tài chính đúng cách** (BẮT BUỘC)
- 6 ngành có bảng đặc thù + bias dễ mắc:
  - **F.1 Xây dựng** (CTD, HBC, VCG): Doanh thu ≠ tiền, Backlog ≠ revenue, Working capital risk, Chu kỳ BĐS, D/E cao bình thường, Trích lập, Niên độ khác
  - **F.2 Ngân hàng** (VCB, TCB...): NIM, NPL ẩn, CASA, Provision coverage, Tier-1, LnD
  - **F.3 Dầu khí** (BSR, PLX): Crack spread, Capacity utilization, Counterparty NOC
  - **F.4 BĐS** (VIC, VHM): NAV, Land bank, Pre-sales, Chu kỳ chính sách
  - **F.5 Thép** (HPG, HSG): HRC price, Cost quặng sắt, By-product
  - **F.6 Ngành mới**: Handler hỏi user + WebSearch pitfalls + tạo bảng đặc thù

#### Thêm vào dashboard (CTD report)

- Section 4 giờ có 4.4 Lợi thế vượt trội + 4.5 Yếu sơn + 4.6 Đặc thù ngành xây dựng (8 dòng bảng)

#### 📚 Lesson

| User insight | Khắc phục |
|---|---|
| "phải nhìn bản chất dn để đọc số tài chính" | Section F — mỗi ngành có lens riêng, không template 1 size fits all |
| "không hiểu đặc thù = bias chắc chắn" | Rule: phân tích không hiểu đặc thù = số liệu đúng nhưng kết luận sai |

---

## [2.2.2] — 2026-07-07

### 🐛 Fix từ CTD test round 2 — subagent qualitative claims sai

Sau khi build CTD report đầy đủ, user phát hiện claim sai: "HBC thuộc hệ sinh thái Nguyễn Bá Dương". Thực tế ông Dương là **cựu** Chủ tịch CTD (rời 2020), HBC độc lập (ông Lê Viết Hải).

#### ✨ Added — Bẫy 8: Subagent qualitative claims sai

- **`vn-financial-data-collector/references/data_pitfalls.md`**: Thêm Bẫy 8 (7→8 bẫy) — "Subagent qualitative claims sai — tin blind"
  - Dấu hiệu: subagent trả narrative về sở hữu/governance, LLM đưa thẳng không verify
  - Cách phòng: verify ≥2 nguồn, flag VERIFY, cross-check BCTC "bên liên quan"
  - Rule cốt lõi: subagent = input KHÔNG phải truth

#### 📚 Lesson

| Sai lầm | Khắc phục |
|---|---|
| Tin subagent blind "HBC = hệ sinh thái NBD" | Verify ownership claims qua WebSearch trước khi đưa vào report |
| Insight 17 premise sai (related-party → thực ra là đối thủ cạnh tranh) | Cross-check với press (Dân Trí, ZNews) confirm "cựu Chủ tịch" |

#### 🧪 Trigger

Đây là silent failure kinh điển mà `skill-premortem` + `data_pitfalls.md` cảnh báo, nhưng vẫn mắc khi build nhanh. Lesson: **claims qualitative (narrative) khó detect hơn claims quantitative** — cần rule riêng.

---

## [2.2.1] — 2026-07-07

### 🐛 Fix từ CTD test — vnstock 4.0 sponsor detection

Sau khi test CTD (smoke test), phát hiện territory bác bỏ map: vnstock 4.0 có 2 gói khác nhau (community 8 kỳ vs sponsor 40+ kỳ) nhưng skill spec v2.2.0 chỉ mention `from vnstock import` (community).

#### ✨ Added — Sponsor detection

- **`equity-research-vn/SKILL.md` Step 0 (BẮT BUỘC)**: Detect sponsor qua `~/.vnstock/auth_state.json` (tier=golden). Nếu sponsor OK → dùng `from vnstock_data import` + sponsor venv Python. Nếu community → fallback `from vnstock import` + WebFetch bổ sung.
- **`vn-financial-data-collector/SKILL.md` Bước 2**: 2 cách import rõ ràng + cấu trúc data khác nhau (sponsor: cột tiếng Anh HOA + report_period; community: cột item/item_en + period columns).
- **`scripts/preflight.py`**: Auto-detect sponsor (try `from vnstock_data` first, fallback `from vnstock.api`). Thêm `vnstock_tier` vào output JSON. Nếu sponsor auth có nhưng import fail → gợi ý dùng sponsor venv Python.

#### 📚 Học từ đâu

| Cái | Nguồn |
|---|---|
| 2 cách import vnstock 4.0 | CTD test 7/2026 — fetch chỉ 8 kỳ vs sponsor 41 kỳ |
| Sponsor venv path | `~/.vnstock/auth_state.json` tier=golden + `/Users/bobo/dev/main-sonet-runtime/.venv-vnstock-sponsor311/` |
| Cấu trúc data khác nhau | CTD income_statement sponsor (cột HOA) vs community (cột item) |

#### 🧪 Verified

- `python3 preflight.py CTD` (community, system python) → flag COMMUNITY_TIER
- `/Users/bobo/.../venv-vnstock-sponsor311/bin/python preflight.py CTD` → sponsor_gold active, fetch 41 kỳ

---

## [2.2.0] — 2026-07-07

### 🛡️ Học từ `us-equity-research` + `skill-premortem`

Sau khi so sánh với `us-equity-research` (sau 4 vòng premortem) và chạy `skill-premortem` trên bộ equity-research-vn, áp dụng 5 cái hay + fix 4 bug.

#### ✨ Added — Scripts mới (chống silent failure)

- **`scripts/audit_split.py`** — Automate Bẫy 5B (split-adjustment consistency). Kiểm tra events + capital_history + back-calc CP=LNST/EPS. Silent failure thật đã xảy ra (BSR: PE sai 6.10× → đúng 9.85×, sai 60%).
- **`scripts/preflight.py`** — Port từ us-equity-research, adapt cho vnstock. 6 checks: split adjustment, LNST âm (PE vô nghĩa), IPO ngắn (< 5 năm), data stale, ticker mismatch (UPCOM/delisted).

#### 🔧 Changed — Workflow cải thiện

- **`vn-financial-data-collector/SKILL.md`**: Xóa `Finance.ratio()` khỏi workflow chính (Lesson #2 BSR stale). Tự tính EPS/BVPS/ROE/PE/PB từ `income_statement` + `balance_sheet`. `f.ratio()` chỉ cross-check, nếu chênh >5% → dùng số tự tính.
- **`vn-technical-analysis/SKILL.md`**: Tech Score verdict đổi từ "STRONG BUY/SELL" → "TECHNICAL STRONG BULLISH/BEARISH" + guardrail "technical = input, không phải verdict cuối". Học từ us-equity-research.

#### ✨ Added — Dashboard components (học từ us-equity-research)

- **Disclaimer block** — `{{DISCLAIMER_HTML}}` content template (3 kỷ luật + HIGHQ/MEDQ/LOWQ labels). Chống "ảo giác model" cho nhà đầu tư.
- **Sidebar TOC sticky** — Layout 2 cột (content trái + sidebar phải sticky). CSS thêm vào `_viz-shared/components.css` + `dashboard_template.html`. Responsive: ≥1100px = sidebar, <1100px = ẩn (dùng topnav).

#### ✨ Added — Insight frames library VN

- **`vn-valuation-engine/references/insight_frames_vn.md`** (MỚI) — 35 frames + archetype router cho 12 ngành VN (ngân hàng, dầu khí, BĐS, thép, bán lẻ, công nghệ, chứng khoán, bảo hiểm, điện, cảng, viễn thông, y tế). Học từ us-equity-research 12 frames + commodity extensions, adapt đặc thù VN (NIM/CASA, crack spread, NAV land bank, HRC price, SSSG...). Mỗi frame có "honest correction" BẮT BUỘC.

#### 📚 Học từ đâu

| Cái hay | Nguồn |
|---|---|
| Preflight script (7 checks) | us-equity-research/scripts/preflight.py |
| Disclaimer block (3 kỷ luật + HIGHQ/MEDQ/LOWQ) | us-equity-research/assets/dashboard_skeleton.html |
| Sidebar TOC sticky (layout 2 cột) | us-equity-research ORCL report |
| Technical guardrail (STRONG BUY → TECHNICAL STRONG BULLISH) | us-equity-research premortem vòng 3 |
| Insight frames library (12→35 frames) | us-equity-research/references/insight_frames.md |
| Audit Bẫy 5B auto | equity-research-vn Lesson #1 + skill-premortem VN |

#### 🐛 Fixed (từ skill-premortem VN)

- **B.3 Bẫy 5B audit manual** → automate `scripts/audit_split.py` (silent failure thật đã xảy ra)
- **B.1 IPO ngắn silent** → `preflight.py` flag HISTORY_TOO_SHORT
- **B.2 công ty lỗ PE vô nghĩa** → `preflight.py` flag NEGATIVE_EARNINGS + valuation path B
- **B.5 ratio() stale** → xóa khỏi workflow chính, chỉ cross-check

---

## [2.1.0] — 2026-06-29

### 🎨 `_viz-shared/` — Design system dùng chung (single source of truth)

Tách CSS/JS dùng chung của dashboard template thành **1 design system duy nhất**, loại bỏ trùng lặp + tokenize template. Đây là refactor kiến trúc lớn nhất kể từ v2.0.0 — không thay đổi tính năng người dùng cuối, nhưng giảm đáng kể duplicate và bug class.

#### Vấn đề trước

- Bảng màu (`:root`) lặp **4 lần** trong 4 template — đổi 1 màu phải sửa 4 nơi
- Code vẽ biểu đồ nến (~100 dòng) lặp **2 lần** (technical + profile)
- `dashboard_template` + `technical_template` **hard-code HPG** → mỗi lần chạy skill sửa tay → dễ sót → root cause của bug "placeholder không replace" (Lessons learned #4)
- 2 bug HTML: `technical_template.html:614` vỡ cú pháp (`class="signal-val buy"+21.8%`), nav lặp dòng "Mô hình nến"

#### ✨ Added — `_viz-shared/` (5 file mới)

- **`tokens.css`** — Design tokens `:root` + **3 theme variants** (Fintech mặc định / Bloomberg Terminal / Corporate sáng) qua `data-theme` attribute
- **`components.css`** — Tất cả UI classes dùng chung (hero, card, kpi, fin-table, news-card, timeline, exec-summary, callout, topnav...) — không hardcode color
- **`viz.js`** — **Chart registry** `viz.chart()` (pattern "chart as plugin", auto-merge legend/grid config) + `viz.renderCandlestick()` (trước đây ~100 dòng × 2) + `viz.setupNav()` (scrollspy + progress + back-top)
- **`inject.py`** — Design-time tool: inline `_viz-shared/*` vào template qua `{{VIZ_CSS}}`/`{{VIZ_JS}}`, không đụng data `{{TOKEN}}`
- **`README.md`** — Docs design system + pattern học được

#### 🔧 Changed

- **Tokenize** `dashboard_template.html` + `technical_template.html` (trước hard-code HPG → giờ `{{TICKER}}`/`{{COMPANY_NAME}}`/...)
- **Refactor dùng shared lib**: `profile_template.html` (CSS+JS), `news_template.html` (CSS only)
- **Theme switching**: từ rewrite `:root` (~30 dòng) → thêm `data-theme="..."` attribute (1 dòng)
- **Chart rendering**: từ `new Chart(...)` lặp config → `viz.chart(id, spec)` registry

#### 🐛 Fixed

- `technical_template.html:614` — HTML vỡ `class="signal-val buy"+21.8%` → composite token
- Nav duplicate "Mô hình nến" → mất
- Root cause "Lessons learned #4" (placeholder không replace) → giải quyết tại nguồn (template tokenize)

#### 🏛️ Patterns hiện thực hóa

Học từ BI tool production (Metabase) áp dụng vào stack Chart.js:

1. **Design tokens** — palette/radius/typography trong `:root`; theme = attribute override (không rewrite CSS)
2. **Chart as plugin** — registry với base-config merge, mỗi chart chỉ ghi phần riêng
3. **Build-time composition** — shared lib inline ra single-file template (Vercel-deployable, zero runtime deps)

#### 📊 Đã verify

- ✅ `node --check`: JS syntax sạch
- ✅ Playwright QA (`qa_dashboard.js`): 7/7 canvas render data thật, 0 JS errors, hero + 7 sections + footer
- ✅ Visual screenshot check: theme fintech, KPI cards, DuPont stacked chart render đúng
- ✅ 0 `{{VIZ_*}}` placeholder sót trong built templates
- ✅ Quét secret/path cá nhân trước push (repo public) — sạch

#### 📁 Files (14)

**Mới (5):** `_viz-shared/{tokens.css, components.css, viz.js, inject.py, README.md}`
**Tokenize (2):** `dashboard_template.html`, `technical_template.html`
**Refactor (2):** `profile_template.html`, `news_template.html`
**Docs (5):** `data_binding.md`, `style_variants.md`, SKILL.md × 3 (`vn-research-dashboard`, `vn-technical-analysis`, `equity-research-vn` — Lessons learned #10)

#### 🔁 Workflow mới

- **Design-time** (hiếm): sửa `_viz-shared/*` → chạy `python3 _viz-shared/inject.py` → tái sinh template self-contained
- **Report-time** (mỗi lần chạy skill): copy template → fill `{{TICKER}}` qua `str.replace` → single-file output → deploy Vercel

#### 📌 Lưu ý

- `longform-report` **không** thuộc pipeline này — chỉ đụng chart registry của nó (palette slate cố tình giữ vì là design system riêng có chủ đích, có `themes.md` riêng)
- Đây là **refactor nội bộ** — output dashboard giao diện giữ nguyên (đã verify bằng screenshot). Version bump 2.0.0 → 2.1.0 (MINOR theo SemVer: thêm khả năng mới = theme switching + chart registry, không break API)

---

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
