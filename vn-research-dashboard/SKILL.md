---
name: vn-research-dashboard
description: Xây dựng dashboard HTML equity research đẹp mắt cho cổ phiếu VN (Bloomberg/Fintech style) từ data đã thu thập và phân tích. Use khi user yêu cầu "dashboard", "báo cáo HTML", "trực quan hóa", "biểu đồ phân tích", hoặc khi cần trình bày kết quả phân tích cơ bản+định giá thành web page tương tác. Cốt lõi = template HTML có Chart.js + CSS gradient fintech, chỉ cần fill data.
---

# VN Research Dashboard

Báo cáo phân tích equity research dạng HTML dashboard — đẹp, tương tác, deploy được.

## Điều kiện tiên quyết

Cần output từ 4 skill trước:
- `vn-financial-data-collector` → data 5 năm
- `vn-fundamental-analysis` → ratios, DuPont, CAGR
- `vn-valuation-engine` → định giá, khuyến nghị
- `vn-technical-analysis` → indicators, patterns, beta (mảnh ghép kỹ thuật)
- `vn-news-digest` → bản tin 30 ngày (optional nhưng khuyến nghị)

## Workflow

### Bước 0: Design system (refactor 2026-06)

Template dùng **`_viz-shared/`** design system (`../_viz-shared/`):
- CSS/JS shared đã được `inject.py` inline sẵn vào `dashboard_template.html` (single-file, không phụ thuộc runtime)
- Template đã **tokenize** — thay hard-code HPG cũ bằng `{{UPPER_TOKEN}}`. Pattern fill = `str.replace` thuần
- Theme switching = thêm `data-theme="bloomberg"`/`"corporate"` lên `<html>` (xem `references/style_variants.md`)
- Chart rendering qua `viz.chart(id, {type,data,options})` registry (pattern "chart as plugin")

Khi cần sửa design chung (palette, component, chart helper): sửa `../_viz-shared/*.css|js` rồi chạy `python3 ../_viz-shared/inject.py`. KHÔNG sửa inline trong template.

### Bước 1: Copy template HTML

Đường dẫn template: `assets/dashboard_template.html`

Template có cấu trúc **10 section** (complete equity report, theo dashboard HPG đã build):
1. **Hero** — ticker, tên công ty, giá hiện tại, 6 KPI cards
2. **Executive Summary** — TL;DR + 4 highlight boxes
2. **Executive Summary** — TL;DR + 4 highlight boxes (tóm tắt nhanh)
3. **Kết quả kinh doanh** — 2 charts (Doanh thu/LNST, Biên LN) + bảng 5 năm
4. **Định giá PE/PB** — gauge + 5 kịch bản + 2 charts (PE/PB, Giá/BVPS)
5. **Multiples mở rộng** — 4 cards (PE, PB, P/S, P/CF)
6. **DCF & Graham** — 3 kịch bản DCF + Graham comparison
7. **DuPont** — chart stacked bar + diễn giải
8. **Special insights ngành** — 3 cards + dự phóng + đánh giá + khuyến nghị
9. **Technical Analysis** (data thật vnstock) — verdict + candlestick chart + indicators + correlation vs VNINDEX/VN30 + patterns + divergence check + trading strategy
10. **News Digest 30 ngày** — sentiment meter + news cards + timeline + key takeaways

⚠️ **Section 9 (Technical) yêu cầu data thật từ vnstock** — KHÔNG BAO GIỜ mô phỏng data giá. Nếu không fetch được → bỏ section hoặc ghi "data không khả thi".

### Bước 2: Fill data vào template

Tham khảo `references/data_binding.md` cho danh sách toàn bộ placeholder cần fill:

```javascript
// Cập nhật object data trong <script>:
const data = {
  ticker: "HPG",
  companyName: "HÒA PHÁT GROUP",
  priceCurrent: 23650,
  years: [2021, 2022, 2023, 2024, 2025],
  revenue: [...], netProfit: [...],
  eps: [...], bvps: [...], pe: [...], pb: [...],
  roe: [...], ros: [...],
  valuations: { pbMedian: 24026, peMedian: 26869, ... },
  recommendation: "ACCUMULATE",
  targetRange: "26,000 - 29,000"
};
```

### Bước 3: Kiểm tra syntax JavaScript (BẮT BUỘC)

**Lỗi phổ biến đã gặp:** Thiếu `}` đóng object, thiếu `new Chart(...)` wrapper, tooltip config lồng sai vào legend block.

**Verify:**
```bash
node -e "
const fs = require('fs');
const html = fs.readFileSync('dashboard.html','utf8');
const scripts = html.match(/<script>([\s\S]*?)<\/script>/g);
const last = scripts[scripts.length-1].replace(/<\/?script>/g,'');
fs.writeFileSync('/tmp/dash.js', last);
" && node --check /tmp/dash.js && echo '✅ Syntax OK'
```

Nếu lỗi, dump phần quanh dòng lỗi để debug. Đếm canvas vs `new Chart` để bắt thiếu:
```bash
node -e "
const fs = require('fs');
const html = fs.readFileSync('dashboard.html','utf8');
const scripts = html.match(/<script>([\s\S]*?)<\/script>/g);
const last = scripts[scripts.length-1].replace(/<\/?script>/g,'');
console.log('Canvas:', (html.match(/<canvas/g)||[]).length, '| new Chart:', (last.match(/new Chart/g)||[]).length);
"
```

### Bước 4: Mở local verify + Automated QA (BẮT BUỘC)

**4a. Syntax check** (như Bước 3) — đảm bảo JS hợp lệ.

**4b. Automated visual QA** — chạy script `scripts/qa_dashboard.js`:
```bash
# Cài playwright (1 lần)
npm install playwright --prefix /tmp/qa-runner
npx playwright install chromium

# Chạy QA
NODE_PATH=/tmp/qa-runner/node_modules node scripts/qa_dashboard.js \
  --url=file:///path/to/[TICKER]_Complete_Report.html \
  --output=/tmp/qa-[TICKER]
```

Script kiểm tra tự động:
- ✅ Tất cả `<canvas>` rendered (không blank)
- ✅ Không JS console errors
- ✅ Đủ sections (hero, exec summary, ≥7 section titles, footer, nav)
- ✅ Navigation links click được
- 📸 Screenshots: full-page + hero + middle

**Kết quả:**
- `✅ PASS` → tiếp tục Bước 5
- `⚠️ PASS WITH WARNINGS` → review warnings, fix nếu cần
- `❌ FAIL` → fix errors, rerun cho đến khi PASS

**4c. Mở local verify** (sau khi QA pass):
```bash
open dashboard.html
```

Kiểm tra mắt: tất cả charts hiển thị đúng, KPI cards có số đúng, không layout broken.

### Bước 4d: Cover image (OPTIONAL — chỉ khi user thêm `--with-cover`)

Nếu user yêu cầu cover image premium cho hero section:
- Đọc `references/cover_image.md` cho prompt template theo sector
- Dùng built-in `image_gen` tool (xem skill `imagegen`)
- Detect sector → chọn prompt → generate → embed vào hero background
- Mặc định KHÔNG generate (giữ dashboard lightweight)

### Bước 5: Deploy (optional)

Nếu user muốn deploy online, dùng skill `vercel-deploy`:
```bash
~/.local/bin/vercel deploy [folder] --prod --yes
```

## Style guide

Template dùng phong cách **Fintech hiện đại**:
- **Background:** Dark (#0a0a14) với radial gradient tím-hồng
- **Cards:** Glassmorphism (backdrop-filter blur, semi-transparent)
- **Charts:** Chart.js với gradient fill, dual y-axis, neon colors
- **Typography:** Inter (sans) + JetBrains Mono (numbers)
- **Color palette:**
  - Primary: #a855f7 (purple), #ec4899 (pink)
  - Accent: #06b6d4 (cyan), #10d98a (green), #fbbf24 (amber), #ff4d6d (red)
  - Text: #f0f0ff (main), #8b8ba7 (dim), #5a5a72 (faint)

User có thể yêu cầu đổi phong cách (Bloomberg Terminal tối, Corporate sáng). Xem `references/style_variants.md` cho biến thể CSS.

## Phân công

- **Thu thập data**: dùng skill `vn-financial-data-collector`
- **Phân tích cơ bản**: dùng skill `vn-fundamental-analysis`
- **Định giá**: dùng skill `vn-valuation-engine`
- **Deploy**: dùng skill `vercel-deploy`

## Tham khảo

- `assets/dashboard_template.html` — Template HTML hoàn chỉnh (Chart.js + CSS fintech)
- `scripts/qa_dashboard.js` — ⭐ Automated visual QA (Playwright): canvas check + JS errors + screenshots
- `references/data_binding.md` — Danh sách placeholder cần fill + schema data + market cap format
- `references/style_variants.md` — ⭐ Layout Router (sector/audience) + 3 biến thể CSS (Fintech/Bloomberg/Corporate)
- `references/chart_recipes.md` — Recipe cho 7 loại chart (bar+line combo, dual-axis, stacked DuPont, sensitivity table)
- `references/cover_image.md` — ⭐ Optional AI cover image generation (prompt template theo sector)
