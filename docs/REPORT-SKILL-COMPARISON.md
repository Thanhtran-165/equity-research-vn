# So sánh 6 Skill con của equity-research-vn

**Trích dẫn canonical:** Tag `skill-harness-evaluator-v0.1.0-final-r2`
**Ngày:** 2026-07-31

---

## Tổng quan pipeline

`equity-research-vn` là một pipeline 6 skill con, mỗi skill phụ trách một lớp phân tích. Dữ liệu chảy theo thứ tự xác định:

```
vn-financial-data-collector (thu thập data thô)
    ↓ JSON data 5 năm
vn-fundamental-analysis (phân tích cơ bản)
    ↓ ratios, DuPont, CAGR
vn-valuation-engine (định giá)    vn-technical-analysis (phân tích kỹ thuật)
    ↓ fair value, target price        ↓ indicators, patterns, Tech Score
    ↓                                 ↓
vn-news-digest (bản tin 30 ngày, optional)
    ↓ sentiment, events
vn-research-dashboard (tổng hợp HTML dashboard)
```

---

## Bảng so sánh 6 skill

| Skill | Vai trò | Input | Output | Mode | Nguồn data |
|---|---|---|---|---|---|
| **vn-financial-data-collector** | Thu thập + cross-check data tài chính | Ticker CP | JSON data 5 năm (revenue, profit, equity, assets...) | 1 mode | vnstock API + CafeF + QHCD |
| **vn-fundamental-analysis** | Phân tích cơ bản từ BCTC | JSON từ collector | Ratios (ROE/ROA/ROS), DuPont, CAGR, đánh giá chất lượng | 1 mode | JSON từ collector |
| **vn-valuation-engine** | Định giá đa phương pháp | JSON từ collector + ratios từ fundamental | Fair value, target price, khuyến nghị | 1 mode | JSON từ collector + fundamental |
| **vn-technical-analysis** | Phân tích kỹ thuật giá-khối lượng | Ticker CP | Indicators (MA/RSI/MACD/Bollinger), patterns, Tech Score, Verdict | **2 mode** (ACTIVE + PROFILE) | vnstock API (giá thực) |
| **vn-news-digest** | Bản tin 30 ngày | Ticker CP | HTML news digest, sentiment score, 4 nhóm tin | 1 mode | vnstock + CafeF + VietnamBiz... |
| **vn-research-dashboard** | Tổng hợp HTML dashboard | Output từ 5 skill kia | HTML dashboard hoàn chỉnh (Bloomberg/Fintech style) | 1 mode | Output từ 5 skill |

---

## Chi tiết từng skill

### 1. vn-financial-data-collector — Nền tảng data

```yaml
vai_tró: 'Thu thập + cross-check 3 nguồn (vnstock + CafeF + QHCD doanh nghiệp)'
đầu_vào: 'Ticker cổ phiếu (HPG, VCB, FPT...)'
đầu_ra: 'JSON data 5 năm: revenue, net_profit, equity, total_assets, EPS, BVPS, PE, PB'
đặc_thù: 'Quy tắc năm phân tích (≥tháng 4 → N-1, <tháng 4 → N-2). Cross-check bẫy dữ liệu VN.'
không_phải: 'Không phân tích, không đánh giá — chỉ thu thập và xác minh'
```

**Là nền tảng** cho toàn bộ pipeline. 5 skill phía sau đều dùng output JSON của skill này.

### 2. vn-fundamental-analysis — Sức khỏe tài chính

```yaml
vai_tró: 'Phân tích chất lượng lợi nhuận từ BCTC 5 năm'
đầu_vào: 'JSON từ collector'
đầu_ra: 'ROE/ROA/ROS, DuPont decomposition (3 thành phần), CAGR, xu hướng'
đặc_thù: 'Tập trung CHẤT LƯỢNG (không chỉ con số). Phân tách ROE = margin × turnover × leverage.'
không_phải: 'Không định giá, không kết luận mua/bán'
```

**Phụ thuộc collector.** Đọc JSON, tính toán ratios, đánh giá xu hướng.

### 3. vn-valuation-engine — Định giá

```yaml
vai_tró: 'Kết luận "rẻ hay đắt" từ hội tụ nhiều phương pháp'
đầu_vào: 'JSON từ collector + ratios từ fundamental'
đầu_ra: 'Fair value, target price, khuyến nghị (9 phương pháp: PE/PB/EV-EBITDA/DCF/Reverse DCF/DDM/Graham/DuPont)'
đặc_thù: 'Chọn phương pháp ưu tiên theo NGÀNH. Không tin 1 phương pháp duy nhất.'
không_phải: 'Không thu thập data, không phân tích kỹ thuật'
```

**Phụ thuộc collector + fundamental.** Trả lời câu hỏi "giá hợp lý bao nhiêu?"

### 4. vn-technical-analysis — Timing

```yaml
vai_tró: 'Trả lời "khi nào mua/bán" từ data giá-khối lượng'
đầu_vào: 'Ticker (lấy giá thực từ vnstock)'
đầu_ra_mode_ACTIVE: 'MA/RSI/MACD/Bollinger, candlestick patterns, Tech Score → Verdict BUY/SELL'
đầu_ra_mode_PROFILE: 'Hồ sơ giá-khối lượng định lượng (28 block: volatility, drawdown, VPCI/OBV/CMF, Wyckoff, archetype)'
đặc_thù: '2 MODE khác nhau. Mode ACTIVE = timing. Mode PROFILE = personality/behavioral profile.'
không_phải: 'Không phân tích cơ bản, không định giá'
```

**Độc lập nhất** trong pipeline — lấy data trực tiếp từ vnstock, không phụ thuộc skill khác. Đã được qualify sâu nhất qua Phase 3 (vta-phase-3-implementation, 410 fixtures).

### 5. vn-news-digest — Góc nhìn thời sự

```yaml
vai_tró: 'Bản tin 30 ngày, phân loại 4 nhóm + sentiment'
đầu_vào: 'Ticker'
đầu_ra: 'HTML news digest, sentiment score, events timeline'
đặc_thù: 'Bổ sung góc nhìn THỜI SỰ cho dashboard (dashboard fundamental chỉ có data BCTC)'
không_phải: 'Không phân tích tài chính, không định giá, không phân tích kỹ thuật'
```

**Optional nhưng khuyến nghị.** Đã được test qua phase7-pit (8 PIT, 64/64 PASS).

### 6. vn-research-dashboard — Mảnh ghép cuối

```yaml
vai_tró: 'Tổng hợp tất cả output thành HTML dashboard hoàn chỉnh'
đầu_vào: 'Output từ 5 skill kia (collector + fundamental + valuation + technical + news)'
đầu_ra: 'HTML dashboard Bloomberg/Fintech style, Chart.js, CSS gradient, deploy được'
đặc_thù: 'Template-driven — chỉ cần fill data vào tokens. Design system shared (_viz-shared).'
không_phải: 'Không thu thập/phân tích/định giá — chỉ trình bày'
```

**Skill cuối cùng** trong pipeline. Tích hợp mọi thứ.

---

## Dependency graph

```
collector ──→ fundamental ──→ valuation
    │                              │
    │              technical ←─────┤ (độc lập, lấy giá riêng)
    │                              │
    │              news-digest ←───┤ (optional)
    │                              │
    └─────────────────────────→ dashboard (tổng hợp tất cả)
```

```yaml
collector:      nền tảng, không phụ thuộc ai
fundamental:    phụ thuộc collector
valuation:      phụ thuộc collector + fundamental
technical:      gần độc lập (lấy giá trực tiếp từ vnstock)
news-digest:    gần độc lập (lấy tin trực tiếp)
dashboard:      phụ thuộc TẤT CẢ 5 skill kia
```

---

## Harness coverage

| Skill | Phase implementations | Verifier files | Test files | Harness status |
|---|---|---|---|---|
| vn-financial-data-collector | 0 | 0 | 0 | Test ngầm qua contracts downstream |
| vn-fundamental-analysis | 12 (phase1→5R3b) | 48 | 51 | ✅ HARNESS RẤT SÂU |
| vn-valuation-engine | 7 (phase4F→6R2) | 51 | 6 | ✅ HARNESS RẤT SÂU |
| vn-technical-analysis | Phase 3 qualify chain | 1 | 0 | ✅ HARNESS (Phase 3 đầy đủ) |
| vn-news-digest | 0 (test qua phase5/7) | — | — | ✅ Test integration (PIT 8/8) |
| vn-research-dashboard | 0 (test qua phase6/7) | — | — | ✅ Test integration (pipeline tổng) |

---

## Ba nhóm phân loại

```yaml
nhóm_thu_thập_phân_tích (2 skill):
  - vn-financial-data-collector: nền tảng data
  - vn-fundamental-analysis: phân tích cơ bản

nhóm_định_giá_kỹ_thuật (2 skill):
  - vn-valuation-engine: định giá (rẻ hay đắt)
  - vn-technical-analysis: timing (khi nào mua/bán)

nhóm_bổ_trợ_trình_bày (2 skill):
  - vn-news-digest: góc nhìn thời sự
  - vn-research-dashboard: tổng hợp HTML
```

---

## Điểm khác biệt quan trọng

### Mode duy nhất vs 2 mode

```yaml
1_mode: collector, fundamental, valuation, news-digest, dashboard
2_mode: technical-analysis (ACTIVE = timing, PROFILE = hồ sơ)
```

vn-technical-analysis là skill duy nhất có 2 mode riêng biệt, mỗi mode trả lời câu hỏi khác nhau.

### Phụ thuộc data thực vs tính toán

```yaml
lấy_data_thực_từ_api: collector, technical-analysis, news-digest
nhận_JSON_từ_skill_khác: fundamental, valuation, dashboard
```

3 skill đầu lấy data trực tiếp (vnstock API), 3 skill sau nhận input từ skill trước.

### Ngôn ngữ output

```yaml
JSON: collector, fundamental
HTML: news-digest, dashboard
kết_hợp: valuation (JSON + text), technical (HTML + JSON)
```
