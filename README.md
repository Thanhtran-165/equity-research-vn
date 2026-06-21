# 📊 Equity Research VN — Pipeline Phân Tích Cổ Phiếu Việt Nam

Bộ 7 skills tạo pipeline phân tích equity research đầy đủ cho cổ phiếu Việt Nam — từ thu thập data đến dashboard HTML deploy được. Hoạt động với ZCode, Claude Code, Codex, hoặc bất kỳ AI agent nào hỗ trợ skills.

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![VN Stocks](https://img.shields.io/badge/Markets-HOSE%20%7C%20HNX%20%7C%20UPCoM-red.svg)

## 🎯 Tính năng

- **Pipeline 7 bước tự động**: Data → Cơ bản → Định giá → Kỹ thuật → Tin tức → Dashboard → Deploy
- **Data thật từ vnstock API** (open-source) — không mô phỏng
- **Dashboard HTML tương tác** 10-12 sections với Chart.js (candlestick, RSI, MACD, scatter correlation...)
- **7 bẫy dữ liệu đặc thù VN** — split-adjustment, số CP thay đổi, LNST thuộc CĐ mẹ, v.v.
- **Phong cách fintech hiện đại** — dark theme, gradient tím-hồng, glassmorphism
- **Tương quan giá dầu** đặc thù ngành lọc hóa dầu (case BSR)
- **Bear case cân bằng** — không chỉ bullish
- **Independent view** — tổng hợp quan điểm độc lập sau phân tích

## 📦 Cấu trúc

```
equity-research-vn/              # Orchestrator — chạy pipeline 7 bước
├── vn-financial-data-collector/ # Bước 1: Thu thập data (vnstock API)
├── vn-fundamental-analysis/    # Bước 2: EPS, ROE, DuPont decomposition
├── vn-valuation-engine/        # Bước 3: 9 PP định giá (DCF, PE/PB, Graham...)
├── vn-technical-analysis/      # Bước 4: MA, RSI, MACD, Beta, patterns
├── vn-news-digest/             # Bước 5: Bản tin 30 ngày + sentiment scoring
└── vn-research-dashboard/      # Bước 6: Dashboard HTML + QA + deploy
```

## 🚀 Cài đặt

### Yêu cầu

- Python 3.11+
- Node.js 18+ (cho dashboard QA)
- AI agent hỗ trợ skills (ZCode, Claude Code, Codex...)

### Cài đặt vnstock + yfinance

```bash
pip install vnstock --upgrade
pip install yfinance  # cho correlation giá dầu (BSR, GAS, PLX...)
```

### Cài đặt skills

Copy 7 thư mục skill vào thư mục skills của AI agent:

```bash
# ZCode
cp -r equity-research-vn vn-* ~/.zcode/skills/

# Claude Code
cp -r equity-research-vn vn-* ~/.claude/skills/

# Codex
cp -r equity-research-vn vn-* ~/.codex/skills/
```

### Deploy dashboard (tùy chọn)

```bash
npm i -g vercel
vercel login  # 1 lần duy nhất
```

## 📖 Cách dùng

### Lệnh chính

```
/equity-research-vn VCB        # Phân tích đầy đủ Vietcombank
/equity-research-vn FPT        # Phân tích đầy đủ FPT Corporation
/equity-research-vn HPG        # Phân tích đầy đủ Hòa Phát
/equity-research-vn BSR        # Phân tích đầy đủ Bình Sơn Refining
```

### Tùy chọn

```
/equity-research-vn VCB --fundamental-only    # Bỏ technical/news (7 sections)
/equity-research-vn FPT --style bloomberg     # Phong cách Bloomberg Terminal
/equity-research-vn MWG --period 3y           # Kỳ 3 năm (2023-2025)
/equity-research-vn VCB --peers BID,CTG,TCB   # So sánh với peer ngành
/equity-research-vn VNM --no-deploy           # Chỉ tạo file local
```

### Output

1. **`[TICKER]_Complete_Report.html`** — dashboard đầy đủ 10-12 sections (~100-130 KB)
2. **5 file JSON** structured data (data, fundamental, valuation, technical, news)
3. **URL Vercel** (nếu deploy)

## 🏗️ Pipeline 7 bước

| Bước | Skill | Output |
|---|---|---|
| 1 | `vn-financial-data-collector` | JSON data 5 năm + audit split |
| 2 | `vn-fundamental-analysis` | EPS, ROE, DuPont, CAGR |
| 3 | `vn-valuation-engine` | 9 PP định giá + khuyến nghị |
| 4 | `vn-technical-analysis` | MA, RSI, MACD, Beta, patterns |
| 5 | `vn-news-digest` | Sentiment score + 10 news cards |
| 6 | `vn-research-dashboard` | HTML dashboard + QA + deploy |
| 7 | (deploy) | URL Vercel |

## 🛡️ 7 Bẫy dữ liệu đặc thù VN

Pipeline áp dụng 7 bẫy để tránh sai sót tính toán:

1. **Số CP lưu hành thay đổi** — back-calc verify từng năm
2. **Đơn vị tính sai** — tỷ/tỷ = đồng, không ×1000
3. **LNST vs LN trước thuế** — dùng LNST thuộc CĐ mẹ
4. **Data cũ** — verify kỳ N-1 đã có BCTC
5. **Split-adjusted price** — adjust khi so sánh cross-year
6. **Vốn hóa sai format** — fetch từ vnstock, không tự tính
7. **🔴 Split-adjustment consistency** — adjust EPS/BVPS về cùng base với giá (Bẫy 5B, mới)

## 📊 Dashboard sections (10-12)

1. Hero + 6 KPI cards
2. Executive Summary (TL;DR + 4 highlight boxes)
3. Kết quả kinh doanh 5 năm
4. Định giá PE/PB
5. Multiples mở rộng (EV/EBITDA, P/CF, P/S)
6. DCF & Graham
7. DuPont decomposition
8. **Special Insights** — Bull Case + Bear Case + Catalyst Roadmap
9. Technical Analysis (data thật vnstock)
9.5. **🛢️ Tương quan giá dầu** (ngành lọc hóa dầu)
10. News Digest 30 ngày
11. **🎯 Quan điểm độc lập** — điều quan trọng nhất + hiểu nhầm + quan điểm giá

## 🎨 Phong cách

- **Dark theme** (`#0a0a14`) với radial gradient tím-hồng
- **Glassmorphism** cards (backdrop-filter blur)
- **Chart.js** với gradient fill, dual y-axis, neon colors
- **Inter** (sans) + **JetBrains Mono** (numbers)
- Color palette: purple `#a855f7`, pink `#ec4899`, cyan `#06b6d4`, green `#10d98a`, red `#ff4d6d`

## 📝 Lessons learned (từ case BSR 2026)

Pipeline đã được kiểm chứng với BSR (Bình Sơn Refining) — phát hiện và sửa nhiều lỗi:

1. **Split-adjustment consistency** — vnstock trả giá split-adjusted, BCTC dùng base CP gốc → mix chuẩn → PE/PB sai (đã add Bẫy 5B)
2. **vnstock ratio() có thể stale** — không tin ratio() tính sẵn
3. **EPS vnstock ≠ EPS BCTC** — cross-check qua back-calc
4. **Template HTML + Python inject** — tránh f-string xung đột brace
5. **Section 8 phải cân bằng Bull/Bear**
6. **Section cuối = Independent view**

Xem chi tiết: [CHANGELOG.md](CHANGELOG.md)

## 🤝 Đóng góp

Contributions welcome! Areas cần cải thiện:

- Thêm peer comparison (`--peers` option)
- Thêm ngành đặc thù mới (BĐS NAV, ngân hàng NIM/CASA)
- Cải thiện pattern detection (Elliott Wave, Fibonacci)
- Multi-language dashboard (EN/CN)

## ⚠️ Disclaimer

**Đây là công cụ giáo dục, KHÔNG phải lời khuyên đầu tư.** Xem [DISCLAIMER.md](DISCLAIMER.md) để hiểu rủi ro.

## 📜 License

MIT — xem [LICENSE](LICENSE)

## 🙏 Acknowledgments

- **vnstock** team (https://vnstocks.com) — open-source data library cho thị trường VN
- **Chart.js** — charting library
- **CafeF, Vietstock** — nguồn dữ liệu công khai
