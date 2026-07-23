# Phase 6: Dashboard Build

Bạn là subagent Phase 6. Context tách biệt.

## Input
- `task-state.json` → TẤT CẢ phase results (phase0→5)
- Sub-skill: `vn-research-dashboard/SKILL.md` + `references/data_binding.md` + `chart_recipes.md`
- Template: `vn-research-dashboard/assets/dashboard_template.html` (22 sections canonical + 38 tokens)

## Nhiệm vụ — BẮT BUỘC theo thứ tự

### Bước 1: Copy template (KHÔNG tự chế HTML)
```bash
cp vn-research-dashboard/assets/dashboard_template.html [WORK_DIR]/[TICKER]_Complete_Report.html
```
Template đã có 22 sections chuẩn (sec-hero → sec-source). **KHÔNG tự chế section ids.**

### Bước 2: Đọc danh sách tokens chính xác
```bash
grep -oE '\{\{[A-Z_0-9]+\}\}' [TICKER]_Complete_Report.html | sort -u
```
38 tokens. **KHÔNG tự nghĩ tên token.**

### Bước 3: Fill tokens bằng str.replace
Fill từng `{{TOKEN}}` với data từ task-state.json phases. Đặc biệt:
- `{{SEC_XXX_HTML}}` — HTML content cho mỗi section (bao gồm canvas elements)
- Canvas ids bắt buộc: `chartHistRev, chartBSDt, chartHistCash, chartPeerScatter, chartProfileDD, chartProfileDist, chartReturns, chartSegMix, chartTechPrice, chartTechRSI, chartThesisCapex, chartThesisRPO, chartValPE`
- `{{CHART_DATA_JS}}` — JS object `const DATA = {...}` với ticker data

### Bước 3b: CONTENT DEPTH — BẮT BUỘC (học từ v2 test #1)

Mỗi section `{{SEC_XXX_HTML}}` phải có **content depth tối thiểu**. Verifier sẽ check.

| Section | Min chars | Phải chứa (gợi ý nội dung) |
|---------|-----------|---------------------------|
| `{{SEC_HERO_HTML}}` | 100 | KPI cards (giá, PE, PB, ROE, EPS, Tech Score) |
| `{{SEC_EXEC_HTML}}` | 500 | TL;DR: luận điểm chính + 4 highlight boxes (NPATMI, Q1 growth, P/E, FCF) |
| `{{SEC_BIZ_HTML}}** | **600** | **Mô tả business model: sản phẩm chính, khách hàng, kênh phân phối, nguồn thu. Tên thương hiệu cụ thể (Chinsu, Nam Ngư, WINMart...). Cấu trúc holding company. Canvas chartSegMix** |
| `{{SEC_INDUSTRY_HTML}}` | **500** | **Industry overview: quy mô thị trường FMCG/bán lẻ VN, tăng trưởng, cạnh tranh (tên đối thủ cụ thể), xu hướng. Không chỉ 1 câu chung chung** |
| `{{SEC_HISTORY_HTML}}` | **500** | **Timeline: thành lập, M&A, IPO, restructuring. Có năm cụ thể. Milestones quan trọng (VinMart acquisition 2020, MCH spin-off 2024)** |
| `{{SEC_SEGMENT_HTML}}` | **400** | **Bảng phân tích phân khúc: tên mảng, % stake, DT/LN từng mảng, mô tả. Bảng table + canvas chartSegMix** |
| `{{SEC_THESIS_HTML}}` | **600** | **Luận điểm đầu tư (bull case): 3 lý do cụ thể với số liệu. Catalyst roadmap. Canvas chartThesisCapex. "Điều gì sẽ thay đổi trong 2-3 năm tới?"** |
| `{{SEC_VALUATION_HTML}}` | **400** | **Bảng multiples (PE/PB/EV-EBITDA/P-S/Graham) + converge median + verdict. Canvas chartValPE. Nhận xét: đắt hay rẻ so với ngành + lịch sử** |
| `{{SEC_PEER_HTML}}` | **400** | **Peer comparison: MSN vs 2-3 peer cùng ngành (VNM, MWG...). So sánh PE/PB/growth/margin. Canvas chartPeerScatter** |
| `{{SEC_BS_HTML}}` | **300** | **Bảng cân đối: Total Assets, Equity, Debt, Net Debt, D/E. Canvas chartBSDt. Nhận xét đòn bẩy** |
| `{{SEC_RISK_HTML}}` | **500** | **Bear case: 3 rủi ro cụ thể với số liệu (nợ, FCF, cạnh tranh, governance). Mỗi rủi ro:触发 + impact. KHÔNG chỉ 1 câu** |
| `{{SEC_33K_HTML}}` | **300** | **Góc nhìn vốn: số vốn, số CP, tỷ trọng, DCA framework (4 đợt), stop-loss, take-profit** |
| `{{SEC_SCENARIO_HTML}}` | **300** | **3 kịch bản (bull/base/bear) với target price + xác suất. Bảng table** |
| `{{SEC_CHECKLIST_HTML}}` | **300** | **5-7 câu hỏi kiểm chứng trước đầu tư. Mỗi câu: ✅/⚠️/❌ + giải thích** |
| `{{SEC_INSIGHT_1_HTML}}` | **600** | **Insight 1: trigger (1 đoạn) + analysis với số liệu (2 đoạn) + HONEST CORRECTION (1 đoạn: "nhưng có thể sai vì...") + verdict + KPI watchlist table** |
| `{{SEC_INSIGHT_2_HTML}}` | **600** | **Insight 2: cùng cấu trúc. Chủ đề khác insight 1** |
| `{{SEC_INSIGHT_3_HTML}}` | **600** | **Insight 3: cùng cấu trúc. Có thể là bear case insight** |
| `{{SEC_TECH_HTML}}` | **400** | **Tech Score card + 6 signals grid + canvas chartTechPrice. Minh bạch dữ liệu (nguồn, kỳ)** |
| `{{SEC_TECH_PROFILE_HTML}}` | **400** | **Profile: archetype + HV + drawdown + VaR + VPCI + 4 điểm non-conclusion + interpretation_guardrail + canvas chartProfileDD/Dist** |
| `{{SEC_ANALYST_HTML}}` | **200** | **Analyst consensus: rating, target, date. Flag nếu stale** |
| `{{SEC_GLOSSARY_HTML}}` | **300** | **5-8 thuật ngữ ngành + giải thích (NPATMI, DuPont, FCF, archetype, BVPS...)** |
| `{{SEC_SOURCE_HTML}}` | **200** | **≥10 numbered citations (`id="ref-N"`) + mô tả nguồn** |

### Bước 3c: KEYWORD CHECK — BẮT BUỘC

Sau khi fill, report phải chứa các keyword sau (verifier check):

| Keyword | REQ | Phải có trong section nào |
|---------|-----|--------------------------|
| "split-adjusted" hoặc "Bẫy 5B" hoặc "cross-check" | REQ-003 | Bất kỳ đâu trong text |
| "sentiment" hoặc "tích cực" hoặc "tiêu cực" | REQ-008 | sec-news hoặc body text |
| "ước tính" hoặc "limitation" hoặc "honest" | REQ-017 | Bất kỳ đâu |

**Nếu thiếu keyword → thêm honest correction callout mentioning data limitation.**

### Bước 4: Verify structure
```bash
# Tokens replaced
grep -oE '\{\{[A-Z_0-9]+\}\}' [OUTPUT].html | wc -l  # phải = 0

# Section map
grep -oE 'id="sec-[a-z0-9-]+"' [OUTPUT].html | sort -u  # phải 22 canonical

# JS syntax
node --check extracted_js

# Div balance
```

## Requirements
- REQ-009: 22 canonical sections (≥15/22 match)
- REQ-010: 0 unreplaced tokens
- REQ-011: Canvas có height-wrapper
- REQ-012: Charts ≥10, Sections ≥20, Refs ≥10
- **REQ-013: Content depth ≥200 chars/section (mỗi section phải có nội dung thật, không rỗng)**
- **REQ-014: 3 insights riêng biệt (sec-insight-1/2/3), mỗi cái ≥500 chars**
- REQ-015: Bull + Bear cân bằng
- REQ-016: Valuation targets dương (no negative DCF)
- REQ-017: Flag honest về data limitation
- REQ-018: Sources ≥10 numbered citations
- REQ-019: JS syntax OK
- REQ-020: Div balance

## KHÔNG được (học từ LC-001, LC-002, v2 test #1)
- Tự viết HTML từ scratch — PHẢI copy template
- Tự chế section ids — dùng canonical
- Viết content quá ngắn (satisficing) — mỗi section phải đạt min_chars
- Bỏ canvas không có wrapper → giãn vô hạn
- Bỏ keyword check (split-adjusted, sentiment, honest)

## Bước 3d: DATA object — BẮT BUỘC đầy đủ keys (học từ PNJ v2 test #2)

Template JS reference các DATA keys. **Thiếu bất kỳ key nào → chart crash hoặc annotation sai.**
Sau khi inject `{{CHART_DATA_JS}}`, verify DATA object có đủ các key sau:

### Core financial keys (yếu tố fundamentals)
| Key | Loại | Ví dụ | Dùng cho |
|-----|------|-------|----------|
| `ticker` | string | "PNJ" | hero + title |
| `years` | array | [2021,2022,2023,2024,2025] | trục X mọi chart |
| `revenue` | array | [19547,33876,...] | chartHistRev |
| `netProfit` | array | [1029,1811,...] | chartHistRev (LƯU Ý: tên `netProfit` không phải `netIncome`) |
| `grossProfit` | array | | chartHistRev |
| `cfo` | array | | chartHistCash |
| `capex` | array | **số nguyên không comma** | chartThesisCapex (KHÔNG dùng fmt() — sẽ break JS array) |
| `inventory` | array | | chartProfileDD |
| `invGrowth` | array | **null thay vì None** | chartProfileDD |
| `eps` | array | [4197,5350,...] | chartHistRev (phải khớp `financials.json` eps_vnd) |
| `roe` | array | | chartHistRev |
| `bvps` | array | | chartBSDt |
| `equity` | array | | chartBSDt |
| `totalAssets` | array | | chartBSDt |
| `peHist` | array | [14.6,18.8,...] | chartValPE |
| `pbHist` | array | | chartBSDt |

### Valuation annotation keys
| Key | Loại | Ví dụ | Dùng cho |
|-----|------|-------|----------|
| `pe5med` | number | 12.9 | chartValPE annotation "5Y median" |
| `pe5avg` | number | 12.8 | chartValPE annotation "5Y avg" (auto-hide nếu \|-pe5med\| <0.5) |
| `pe` | number | 9.1 | chartValPE "Now" point + label |

### Peer scatter keys (sector-agnostic)
| Key | Loại | Ví dụ | Dùng cho |
|-----|------|-------|----------|
| `peers` | object | `{data: [{label,x,y,r,own},...]}` | chartPeerScatter (**cần `.data` sub-key**, mỗi point có field `own:true/false` và `r`) |
| `peerLabel` | string | "Peer bán lẻ VN (P/B vs CAGR NPAT, bubble=vốn hóa)" | dataset label — KHÔNG hardcode "BĐS VN" |
| `peerPBMin` | number | 1 | X-axis min (PNJ: 1, BĐS: 0.5) |
| `peerPBMax` | number | 5 | X-axis max (PNJ: 5, BĐS: 2) |
| `peerYLabel` | string | "CAGR NPAT 3Y (%)" | Y-axis title |
| `peerYMax` | number | 20 | Y-axis max |

### Technical annotation keys
| Key | Loại | Ví dụ | Dùng cho |
|-----|------|-------|----------|
| `tech52wLow` | number | 46500 | chartTechPrice support line + label |
| `techMA50val` | number | 64591 | chartTechPrice resistance line + label |
| `techRSI` | array | | chartTechRSI |
| `techWeeks`, `techPrice`, `techMA10/20/50` | arrays | | chartTechPrice datasets |

### Segment mix
| Key | Loại | Ví dụ | Dùng cho |
|-----|------|-------|----------|
| `segMix` | object | `{labels: [...], values: [...]}` | chartSegMix |

**Kiểm tra:** sau khi inject DATA, chạy `node --check` trên JS extract. Nếu crash → thiếu key hoặc sai format (None thay vì null, comma trong số).

## Cấu trúc insight (template)
Mỗi insight (sec-insight-1/2/3) phải có cấu trúc:
```html
<div class="insight-card">
  <h4>[Tiêu đề insight]</h4>
  <p>[Trigger: 1 đoạn mô tả event/fact]</p>
  <p>[Analysis: 2 đoạn với số liệu cụ thể]</p>
  <p class="honest-correction">Honest correction: [nhưng có thể sai vì...]</p>
  <table>[KPI watchlist]</table>
</div>
```
