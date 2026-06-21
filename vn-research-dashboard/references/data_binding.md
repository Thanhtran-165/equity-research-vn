# Data Binding — Placeholder schema cho dashboard

Danh sách toàn bộ điểm cần fill trong template. Theo thứ tự xuất hiện trong HTML.

## Hero section

```html
<!-- Tên công ty -->
<div class="ticker-badge">⚡ HOSE:[EXCHANGE] · [SECTOR]</div>
<div class="company-name">[COMPANY_NAME]</div>
<div class="company-sub">[LEGAL_NAME] · Ngành: [SECTOR_VI] · [BIZ_MODEL]</div>

<!-- Giá hiện tại -->
<div class="price-now mono"><span class="ccy">₫</span>[PRICE_CURRENT]<span class="price-unit"> /cp</span></div>
<div class="price-meta">Capitalization ≈ <strong class="mono pos">[MARKET_CAP formatted]</strong> (~$[MARKET_CAP_USD]B USD) · Cập nhật [DATE]</div>
```

⚠️ **Market Cap format rule (BẮT BUỘC):**
- Fetch từ vnstock: `Company(symbol, source='VCI').overview()['market_cap']` → trả về VND tuyệt đối (1.99e14)
- Quy đổi: `/1e9` → tỷ VNĐ (199,254), `/25.5e3` → tỷ USD (~7.8)
- **Format chuẩn hiển thị:**
  - ✅ ĐÚNG: `₫199.3K tỷ` hoặc `199,254 tỷ VNĐ` hoặc `~$7.8B USD`
  - ❌ SAI: `₫136.5B tỷ` (trùng B + tỷ), `136.5B` (thiếu đơn vị), `136,500 tỷ` (sai số vì dùng CP cũ)
- **KHÔNG tự tính** `price × shares_cũ` — phải dùng số CP **hiện tại** (sau cổ tức CP gần nhất) hoặc fetch `market_cap` trực tiếp từ vnstock

## KPI cards (6 cards)

```html
<div class="kpi">
  <div class="kpi-label">[LABEL]</div>            <!-- VD: "P/E (2025)" -->
  <div class="kpi-value mono [pos/neu]">[VALUE]<span>x</span></div>
  <div class="kpi-delta [pos/neg/neu]">[DELTA_TEXT]</div>
</div>
```

6 cards gợi ý:
1. P/E (năm gần nhất)
2. P/B (năm gần nhất)
3. ROE (năm gần nhất)
4. BVPS (năm gần nhất)
5. LNST (năm gần nhất, YoY change)
6. Metric đặc thù ngành (sản lượng thép / SSSG bán lẻ / NAV BĐS...)

## Bảng tài chính 5 năm

Mỗi hàng là 1 chỉ số. **Cross-check số liệu trước khi fill** (xem skill `vn-financial-data-collector/references/data_pitfalls.md`).

Hàng bắt buộc:
- Doanh thu thuần, LNST, Vốn chủ sở hữu, Tổng tài sản, LCFD HĐKD (CFO)
- Số CP lưu hành (từng năm, **KHÔNG cố định**)
- EPS (đồng), BVPS (đồng) — dòng highlight
- ROE, ROA, Biên LNST (ROS)
- Giá cuối năm (đồng)

## Charts (Chart.js data array)

Tất cả array phải có **5 phần tử** (5 năm):

```javascript
const years = [2021, 2022, 2023, 2024, 2025];
const data = {
  revenue:   [150865, 142771, 118953, 140191, 158332],   // tỷ
  netProfit: [34521, 8444, 6835, 12021, 15515],          // tỷ
  eps:       [5937, 1319, 1068, 1878, 2019],             // đồng
  bvps:      [17713, 15313, 17031, 20313, 18867],        // đồng
  price:     [32.8, 19.5, 25.2, 25.0, 23.65],            // nghìn đồng (cho chart)
  pe:        [5.5, 14.8, 23.6, 13.3, 11.7],              // x
  pb:        [1.85, 1.27, 1.48, 1.23, 1.25],             // x
  roe:       [33.5, 8.6, 6.3, 9.2, 10.7],                // %
  ros:       [22.9, 5.9, 5.7, 8.6, 9.8],                 // %
  // DuPont: ÷100 cho asset turn và leverage để chart đẹp
  dupMargin: [22.9, 5.9, 5.7, 8.6, 9.8],                 // %
  dupTurn:   [91, 88, 67, 62, 66],                       // ×100
  dupLev:    [160, 165, 163, 173, 166],                  // ×100
};
```

⚠️ **Đơn vị `price` trong chart = nghìn đồng** (vì scale nhỏ hơn revenue). **Đơn vị `price_current` ở Hero = đồng** (23,650). **Phải consistent trong code.**

## Valuation scenarios (5 cards)

```html
<div class="val-card">
  <div class="name">[METHOD_NAME]</div>      <!-- "PB median 5N" -->
  <div class="price mono [pos/neu/neg]">[VALUE]K</div>
  <div class="upside [pos/neg]">[UPSIDE_PCT]%</div>
  <div class="bar-track"><div class="bar-fill" style="width:[PCT]%"></div></div>
  <div>[FORMULA_NOTE]</div>                   <!-- "BVPS'25 × PB 1.27x" -->
</div>
```

`bar-fill width`: scale theo `VALUE / MAX_VALUE × 100`, max = giá trị kịch bản cao nhất.

## Gauge (giá hợp lý trung tâm)

```html
<div class="gauge-num mono">₫[FAIR_VALUE]K</div>
<div class="gauge-verdict" style="background:[COLOR]">[VERDICT]</div>
<div>Giá hiện <strong>[PRICE_CURRENT]K</strong> → rẻ/đắt hơn ~[DIFF_PCT]%</div>
```

- `VERDICT`: "🟢 UNDERVALUED" (green) / "⚖️ FAIRLY VALUED" (amber) / "🔴 OVERVALUED" (red)

## Khuyến nghị cuối cùng

```html
<div class="kpi-label">Khuyến nghị (9 PP hội tụ)</div>
<div class="[neu/pos/neg]">[RECOMMENDATION]</div>      <!-- "⬆ ACCUMULATE" -->
<div>Dải mục tiêu: [TARGET_LOW] - [TARGET_HIGH] ([UPSIDE_RANGE])</div>
```

Recommendation mapping (từ `vn-valuation-engine`):
- STRONG BUY (>+30%), BUY/ACCUMULATE (+10% to +30%), HOLD (-10% to +10%), REDUCE (-30% to -10%), SELL (<-30%)

## Sources footer

```html
<div>Nguồn: <a href="[VIETSTOCK_URL]">Vietstock</a> ·
  <a href="[CAFEF_URL]">CafeF</a> ·
  <a href="[IR_URL]">BCTC [COMPANY]</a>
</div>
```

## Validation checklist trước khi "Done"

- [ ] Tất cả section có data — **grep raw placeholders** phải trả 0:
  ```bash
  grep -o "{{[A-Z_]*}}" BSR_Complete_Report.html | sort -u
  # Must return empty. If not → inject script bug
  ```
- [ ] Số liệu cross-check với ít nhất 2 nguồn
- [ ] **Market Cap đúng**: fetch từ vnstock `Company.overview()['market_cap']`, KHÔNG tự tính bằng CP cũ
- [ ] **Market Cap format đúng**: "₫199.3K tỷ" hoặc "199,254 tỷ VNĐ" — KHÔNG "₫XB tỷ" (trùng đơn vị)
- [ ] **Số CP nhất quán**: nếu có cổ tức CP gần → dùng số CP mới nhất cho market cap, nhưng dùng số CP **từng năm** cho EPS/BVPS
- [ ] **Split-adjustment check (BẮT BUỘC):** Nếu công ty có split/dividend-stock → verify PE/PB cross-year dùng cùng base (xem `data_pitfalls.md` Bẫy 5B). Back-calc `CP = LNST/EPS` từng năm → nếu CP mismatch > 5% → cần adjust
- [ ] Chart syntax OK (`node --check /tmp/dash.js` returns ✅)
- [ ] `Canvas count` = `new Chart count` (+ 1 nếu có custom canvas candlestick)
- [ ] Mở file local → tất cả charts hiển thị
- [ ] Disclaimer ở footer có cảnh báo "không phải lời khuyên đầu tư"
- [ ] **Rà soát toàn cục**: grep file cho các pattern sai phổ biến (`₫\d+\.?\d*[BMK]\s*tỷ` = trùng đơn vị, số CP cố định xuyên năm)

## ⚠️ Template + inject pattern (lessons learned case BSR 2026)

**Vấn đề:** Dùng f-string Python để generate HTML chứa JavaScript → xung đột brace `{{...}}` (Python f-string escape) với JS object literal `{...}` → JS syntax error khó debug.

**Pattern ĐÚNG (đã verify):**

1. **Tách template HTML tĩnh** (file `.html`) với placeholder `{{TOKEN_NAME}}`
2. **Python script inject** đọc template + replace placeholder bằng string replacement ĐƠN GIẢN (không f-string):
   ```python
   with open('dashboard_template.html') as f: tpl = f.read()
   html = tpl
   simple_tokens = {
       '{{PRICE_NOW}}': f"{price_now:,.0f}",
       '{{FINAL_REC}}': V['final_recommendation'],
       # ... tất cả tokens
   }
   for k, v in simple_tokens.items():
       html = html.replace(k, str(v))
   ```

3. **Token replacement order CRITICAL (bug đã mắc):** Vòng lặp `for k,v in simple_tokens.items()` phải chạy **SAU KHI tất cả token đã được add vào dict**. Nếu add token mới (VD oil correlation) sau vòng lặp → các token đó không được replace → raw `{{TOKEN}}` hiển thị trong dashboard.

   ```python
   # ✅ ĐÚNG: Define tất cả tokens TRƯỚC, replace SAU
   simple_tokens = {...}
   simple_tokens['{{NEW_TOKEN}}'] = value  # OK, thêm trước loop
   for k, v in simple_tokens.items():
       html = html.replace(k, str(v))

   # ❌ SAI: Replace trước, add token sau
   for k, v in simple_tokens.items():
       html = html.replace(k, str(v))
   simple_tokens['{{NEW_TOKEN}}'] = value  # BUG! Không bao giờ được replace
   ```

4. **JSON data injection** cho array/object lớn (chart data, news cards): Dùng pattern `/*TOKEN*/.../**/` trong template + regex replace:
   ```javascript
   // Trong template:
   const DATA_JSON = /*DATA*/{}/**/;
   // Trong Python:
   pattern = r'/\*DATA\*/.*?/\*\*/'
   repl = f'/*DATA*/{json.dumps(value)}/**/'
   html = re.sub(pattern, repl, html, count=1, flags=re.DOTALL)
   ```

5. **Verify cuối cùng (BẮT BUỘC):**
   ```python
   import re
   remaining = set(re.findall(r'{{[A-Z_]+}}', html))
   if remaining:
       print(f"⚠️ WARNING: {len(remaining)} placeholders unreplaced: {remaining}")
   else:
       print("✅ All placeholders replaced")
   ```

6. **JS chart syntax check** — Charts với nested options dễ thiếu/thừa `}`. Auto-fix script:
   ```bash
   node 22_fix_and_verify.js  # tự balance braces cho từng Chart block
   node --check /tmp/dash.js  # verify syntax
   ```

7. **Chart.js arrow function** trong tooltip/scales callback — dùng `function(v){return ...}` thay vì `v => ...` để tránh parser issue trong một số edge cases.
