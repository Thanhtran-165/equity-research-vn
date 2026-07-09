# 🇻🇳 equity-research-vn v2.2.7 — Bản giới thiệu cập nhật

> **Bộ skill ZCode nghiên cứu cổ phiếu Việt Nam — từ data thật đến dashboard HTML deploy Vercel**
>
 *Phiên bản này học từ 2 case thực tế: CTD (Coteccons, xây dựng) + KDH (Khang Điền, BĐS) — tích hợp 22 lessons learned, 3 vòng premortem, sponsor vnstock golden tier, và framework evidence pack matching benchmark ORCL.*

🔗 **Live demo KDH**: https://kdh-deploy.vercel.app
🔗 **Live demo CTD**: https://ctd-deploy.vercel.app

---

## 📋 Mục lục

1. [Skill là gì](#1-skill-là-gì)
2. [Có gì mới trong v2.2.7](#2-có-gì-mới-trong-v227)
3. [Pipeline 7 phase](#3-pipeline-7-phase)
4. [Ví dụ thực tế: KDH (Khang Điền)](#4-ví-dụ-thực-tế-kdh-khang-điền)
5. [Đặc thù ngành (lens riêng)](#5-đặc-thù-ngành-lens-riêng)
6. [Quality Gate — 10 checks trước deploy](#6-quality-gate--10-checks-trước-deploy)
7. [Cách dùng](#7-cách-dùng)
8. [Roadmap](#8-roadmap)

---

## 1. Skill là gì?

`equity-research-vn` là bộ **7 skill ZCode** chạy pipeline nghiên cứu cổ phiếu Việt Nam đầy đủ — từ thu thập data vnstock đến dashboard HTML đẹp mắt deploy Vercel. Dùng cho AI agent (ZCode, Claude Code, Codex).

```
/equity-research-vn KDH
→ 15-30 phút sau: dashboard 22 sections, 13 charts, 3 insights với honest corrections
→ Output: HTML single-file + Vercel URL
```

**Khác biệt cốt lõi** so với chat GPT thông thường:
- **Data thật** từ vnstock API (sponsor golden tier = 10+ năm BCTC)
- **22 sections evidence pack** (không phải tóm tắt 1 trang)
- **3 Special Insights** với "HONEST CORRECTION" bắt buộc (không cheerlead)
- **Quality Gate 10 checks** trước deploy (BLOCK nếu fail)
- **Đặc thù 12 ngành VN** (NAV BĐS, NIM ngân hàng, crack spread dầu khí...)

---

## 2. Có gì mới trong v2.2.7?

### 🔥 Sponsor vnstock detection (v2.2.1, verified KDH)

vnstock 4.0 có 2 tier:
| Tier | Import | Data | Số kỳ |
|---|---|---|---|
| Community (free) | `from vnstock import` | 8 kỳ (~2 năm) | Thiếu |
| **Sponsor golden** (trả phí) | `from vnstock_data import` | **40+ kỳ (10+ năm)** | Đầy đủ |

Skill tự detect sponsor qua `~/.vnstock/auth_state.json`. Nếu user có sponsor → dùng sponsor venv Python → fetch đầy đủ. Nếu không → fallback community (8 kỳ) + flag "history limited".

⚠️ **Sponsor key là quyền riêng của mỗi user** — skill KHÔNG hardcode key, KHÔNG share trong repo. Mỗi người tự auth.

**Ví dụ KDH**: Với sponsor → 8 năm full-year. Không sponsor → chỉ 2 năm → flag community edition.

### 🎯 Evidence Pack format (học từ us-equity-research)

Trước: Dashboard 11 sections ngắn (~86KB).
Giờ: **Investment Evidence Pack 22 sections** (~163KB), matching benchmark ORCL.

| Section | Nội dung |
|---|---|
| 1. Hero + 6 KPI | Giá, P/E, P/B, ROE, LNST YoY, metric đặc thù |
| 2. Executive Summary | 4 callouts (thesis/risk/valuation/capital lens) + "Nói cách khác" |
| 3. Business 101 | Mô hình kinh doanh, segments, khách hàng |
| 4. Industry Position | 3 tầng phân tích + peer table |
| 5. Financial History | Bảng 5 năm + 2 charts (Revenue/NP, CFO/Capex/FCF) |
| 6. Segment Analysis | Mix doanh thu + chart |
| 7. Investment Thesis | Điều kiện đúng/sai + KPI watchlist |
| 8. Valuation | 9 PP hội tụ + P/E/P/B history + NAV (BĐS) |
| 9. Peer Comparison | Scatter chart + table |
| 10. Balance Sheet + FCF | Honest assessment CFO/FCF |
| 11. Risk Matrix | 14 rủi ro × prob × impact |
| 12. Capital Lens | Lump-sum vs DCA + drawdown table |
| 13. Scenario Analysis | Bull/Base/Bear + expected value |
| 14. Checklist | 4 categories (Business/Financial/Valuation/Discipline) |
| ★15-17 | **3 Special Insights** (dynamic theo ngành) |
| 18. Technical ACTIVE | Tech Score -6→+6, Verdict, 6 signals, patterns |
| 19. Technical PROFILE | 15 blocks, archetype, NON-ADVICE |
| 20. Analyst Synthesis | Consensus + bull/bear + synthesis độc lập |
| 21. Glossary | Financial + domain terms |
| 22. Source Appendix | Numbered citations + Data Quality Matrix |

### 🛡️ 22 Lessons Learned (từ CTD + KDH)

Mỗi lỗi mắc trong build được ghi thành lesson trong SKILL.md:
- **Lớp 1 (Data)**: Sponsor detection, schema khác nhau, Company API KeyError
- **Lớp 2 (Template)**: 105 tokens skeleton, DATA JS Oracle residual, CSS thiếu
- **Lớp 3 (Layout)**: Grid nesting bugs
- **Lớp 4 (Content)**: Match benchmark depth, 3 insights (không 1)
- **Lớp 5 (Verification)**: Data integrity check, raw code leak
- **Lớp 6 (Process)**: Đọc spec trước build, pre-deploy 10-check

---

## 3. Pipeline 7 phase

```
Phase 0: Discovery (HỎI USER)
  ├─ Vốn giải ngân? Kỳ vọng? Risk tolerance?
  ├─ Sponsor detection (golden/community)
  └─ Archetype routing (insight_frames_vn.md)

Phase 1: Data research
  ├─ Sponsor venv: Finance (BCTC 5-10 năm)
  ├─ System python3: Company (overview/events/news), Quote (price)
  ├─ Audit split (Bẫy 5B)
  └─ 9 bẫy data pitfalls

Phase 2: Insight engine (ĐỘC ĐÁO)
  ├─ 3 frames từ archetype + insight_frames
  ├─ Mỗi frame: trigger + analysis + HONEST CORRECTION + verdict + KPI
  └─ Honest correction BẮT BUỘC (không cheerlead)

Phase 3: 19 generic sections
  ├─ Fundamental (EPS, ROE, DuPont, CAGR)
  ├─ Valuation (9 PP: PE/PB/EV-EBITDA/DCF/Graham...)
  └─ Content depth matching benchmark

Phase 4: Language layers
  ├─ Glossary (financial + domain)
  ├─ "💡 Nói cách khác" callouts (≥5)
  └─ Jargon kept (EPS, P/E...) + footnote

Phase 5: Dashboard render
  ├─ Copy skeleton (105 tokens)
  ├─ str.replace fill (KHÔNG f-string)
  ├─ Replace DATA Oracle → ticker VND
  ├─ Add CSS cho 35+ component classes
  └─ Build TOC sidebar

Phase 6: Quality gates + deploy
  ├─ 10-check pre-deploy (BLOCK nếu fail)
  ├─ Benchmark comparison (≥80% ORCL)
  └─ Vercel deploy (optional)
```

---

## 4. Ví dụ thực tế: KDH (Khang Điền)

> **Live**: https://kdh-deploy.vercel.app (163KB, 22 sections, 13 charts)

### Phase 0 brief
- **Ticker**: KDH (Nhà Khang Điền, HOSE — Real Estate)
- **Vốn**: 800 triệu VND
- **Horizon**: 1-3 năm
- **Risk tolerance**: -25%
- **Sponsor**: Golden tier → 8 năm data (2018-2025)

### Data snapshot (sponsor golden)

| Năm | Doanh thu (tỷ) | LNST (tỷ) | EPS (đ) | ROE | P/B | Tồn kho (tỷ) | CFO (tỷ) |
|---|---|---|---|---|---|---|---|
| FY21 | 3.738 | 1.202 | 1.790 | 11.8% | 2.31× | 7.733 | -2.010 |
| FY22 | 2.912 | 1.103 | 1.440 | 9.4% | 2.00× | 12.453 | -1.047 |
| FY23 | 2.088 | 716 | 840 | 4.6% | 1.52× | 18.787 | -1.543 |
| FY24 | 3.279 | 810 | 722* | 4.2% | 1.21× | 22.178 | -3.648 |
| FY25 | 4.651 | 1.045 | 870 | 4.9% | 1.11× | 23.260 | -2.024 |

*EPS FY24 adjusted (sponsor trả 80đ anomaly — back-calc shares mismatch 9×)

### 3 Special Insights (đặc thù BĐS)

**★ Insight 1 — Tồn kho 23.260 tỷ: tài sản chiến lược hay "đất kẹt"?**
- KDH nắm >500 ha "đất sạch" ở HCMC core (Thủ Đức, Q9, Mả Lặng D1)
- NAV estimate (markup 2.5×): ~39.461đ/cp → **P/NAV 0.53× (rẻ)**
- Broker cross-check: Yuanta NAV fair value 47.300đ, MBS TP 39.100đ
- ⚠️ HONEST CORRECTION: Markup 2.5× là ước tính. Nếu land bank non-prime nhiều → P/NAV 1.05× (fair). Cần breakdown prime vs non-prime.

**★ Insight 2 — CFO âm 5 năm: đặc thù BĐS hay distress signal?**
- CFO âm toàn bộ 5 năm (-1.000 đến -3.600 tỷ)
- Đặc thù BĐS: pre-sales + land accumulation = tạm ứng vốn
- ⚠️ HONEST CORRECTION: 5 năm âm liên tục dai dẳng hơn CTD (xây dựng, 3/5 năm). Nếu kéo dài + BĐS downcycle → rủi ro thanh khoản thật.

**★ Insight 3 — Mả Lặng 16.369 tỷ: game-changer hay concentrated bet?**
- Urban renewal District 1 (core HCMC) — approved by HCMC
- Site handover trước 31/12/2026, construction Q3/2026
- ⚠️ HONEST CORRECTION: 1 project = ~50% total assets. Concentration risk cao. Nếu trễ/thất bại → downside nặng.

### NAV analysis (BĐS-specific — thêm v2.2.7)

| Scenario markup | Inventory reval | NAV/cp | P/NAV | Verdict |
|---|---|---|---|---|
| Conservative (1.5×) | 34.890 tỷ | 18.730đ | 1.12× | fair |
| **Base (2.5×)** | **58.150 tỷ** | **39.461đ** | **0.53×** | **rẻ** |
| Bull (3.5×) | 81.410 tỷ | 60.192đ | 0.35× | rất rẻ |

### Dilution impact (cổ tức cổ phiếu 10% + ESOP 1%)

| Metric | FY25 (pre) | FY27 (flat) | FY27 (target 2.500 tỷ) |
|---|---|---|---|
| Shares | 1.122 tỷ | 1.245 tỷ (+11%) | 1.245 tỷ |
| EPS | 870đ | 784đ | **2.007đ** |
| P/E | 24.1× | 26.8× | **10.5×** |

### Technical
- **ACTIVE**: Tech Score **-6 / STRONG BEARISH** — giá dưới mọi MA, RSI 31.2, Alpha -54%
- **PROFILE**: archetype **accumulation_breakout** — cup-with-handle forming (30% from confirmation)

### Frontend polish (beautiful-shadows + animation-on-scroll)
- 134/134 cards có shadow tiered (sm/md/lg)
- 22 section scroll-reveal + IntersectionObserver
- prefers-reduced-motion guard

---

## 5. Đặc thù ngành (lens riêng)

Skill có **insight_frames_vn.md** với 35 frames + archetype router cho 12 ngành:

| Ngành | Lens riêng | KPI đặc thù |
|---|---|---|
| **BĐS** (KDH, VIC, VHM) | NAV, land bank, pre-sales | NAV/cp, markup factor, inventory turnover |
| **Ngân hàng** (VCB, TCB) | NIM, NPL, CASA | NIM, NPL %, CASA %, Tier-1 |
| **Xây dựng** (CTD, HBC) | Backlog, % hoàn thành, CFO vs LNST | Backlog/rev, convert rate |
| **Dầu khí** (BSR, PLX) | Crack spread, capacity | Crack spread, utilization |
| **Thép** (HPG, HSG) | HRC price, cost quặng sắt | HRC, capacity, by-product |
| **Bán lẻ** (MWG, PNJ) | SSSG, ecosystem | SSSG, gross margin, member % |
| **Công nghệ** (FPT) | Outsourcing, R&D | Rev/employee, contract backlog |

Mỗi ngành có **Section F** trong insight_frames: bảng đặc thù + bias dễ mắc + "đọc đúng cách".

---

## 6. Quality Gate — 10 checks trước deploy

```
1. ✅ JS syntax OK (node --check)
2. ✅ 0 unreplaced tokens (grep)
3. ✅ Data integrity (Chart values = ticker, KHÔNG Oracle)
4. ✅ Section content >500 chars mỗi section
5. ✅ TOC populated >10 items
6. ✅ Tables có CSS borders
7. ✅ No grid nesting
8. ✅ No raw code ({ref()} không lọt HTML)
9. ✅ PROFILE non-advice (0 từ cấm)
10. ✅ Benchmark comparison (≥80% ORCL: size/charts/sections/tables)
```

**KHÔNG deploy cho đến khi TẤT CẢ 10 pass.**

---

## 7. Cách dùng

```
# Cài đặt (1 lần)
git clone https://github.com/Thanhtran-165/equity-research-vn ~/.zcode/skills/equity-research-vn

# Chạy (mọi AI agent hỗ trợ skill)
/equity-research-vn KDH                    # Full pipeline + deploy
/equity-research-vn VCB --fundamental-only # Bỏ technical + news
/equity-research-vn FPT --no-deploy        # Chỉ local
/equity-research-vn HPG --period 3y        # Kỳ 3 năm

# Yêu cầu
- Python 3.11+ (sponsor venv cho golden tier)
- Node.js 18+ (Chart.js)
- vnstock sponsor package (golden tier, optional)
- Vercel CLI (cho deploy)
```

---

## 8. Roadmap

- [x] ~~Sponsor vnstock golden detection~~ ✅ v2.2.1
- [x] ~~Evidence pack 22 sections~~ ✅ v2.2.7
- [x] ~~3 Special Insights dynamic~~ ✅ v2.2.7
- [x] ~~Đặc thù 12 ngành VN~~ ✅ v2.2.3
- [x] ~~Quality Gate 10 checks~~ ✅ v2.2.5
- [x] ~~NAV estimate cho BĐS~~ ✅ v2.2.7 (KDH)
- [x] ~~Frontend polish (shadows + scroll reveal)~~ ✅
- [ ] Peer comparison data sponsor (fetch VIC/VHM/NLG)
- [ ] Elliott Wave + Fibonacci patterns
- [ ] Multi-language dashboard (EN/CN)
- [ ] Real-time data (WebSocket)
- [ ] Backtesting trading strategy

---

## 📊 So sánh benchmark

| Metric | Benchmark ORCL (US) | KDH (VN) | Đạt? |
|---|---|---|---|
| File size | 244KB | 163KB | ✅ (>120KB min) |
| Charts | 13 | 13 | ✅ |
| Sections | 22 | 22 | ✅ |
| Tables | 24 | 21 | ✅ |
| Citations | 16-69 | 17 | ✅ (≥10) |
| Honest corrections | 3+ | 4 | ✅ |
| "Nói cách khác" | 5+ | 7 | ✅ |
| 3 vòng premortem | — | ✅ 0 P0 | ✅ |

---

*equity-research-vn v2.2.7 · GitHub: Thanhtran-165/equity-research-vn · MIT License*
*Built with vnstock sponsor golden + ZCode AI agent · 2026-07-09*
