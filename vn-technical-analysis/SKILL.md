---
name: vn-technical-analysis
description: Phân tích kỹ thuật cổ phiếu VN từ data giá THẬT (vnstock API) — tính MA/RSI/MACD/Bollinger/Beta/Correlation, phát hiện candlestick & chart patterns thật, divergence check thành thật, và render biểu đồ nến + volume. Use khi user hỏi "phân tích kỹ thuật", "có nên mua/bán giờ", "khi nào vào lệnh", "beta/correlation", "mô hình nến/giá", hoặc khi cần mảnh ghép thứ 3 (timing) cho bộ phân tích equity research VN. Cốt lõi = data từ vnstock (VCI source), KHÔNG BAO GIỜ ngụy tạo/mô phỏng data giá.
---

# VN Technical Analysis

Phân tích kỹ thuật từ **data giá thực vnstock** — trả lời câu hỏi "khi nào mua/bán" (timing) mà fundamental và news không trả lời được.

## ⚠️ Nguyên tắc tối thượng: KHÔNG NGỤY TẠO DATA

**Tuyệt đối không** tự tạo chuỗi giá OHLC "mô phỏng" rồi trình bày như phân tích thật. Đây là lỗi nghiêm trọng đã từng xảy ra. Data giá PHẢI đến từ:

1. **vnstock (VCI source)** — nguồn chính, ưu tiên #1
2. **Yahoo Finance API** — backup (CORS issue khi gọi từ browser)
3. **TCBS API** — backup thứ cấp

Nếu không fetch được data → **nói thẳng "không có data"**, KHÔNG tự bổ sung bằng mô phỏng.

## Workflow 4 bước

### Bước 1: Fetch data giá thực từ vnstock

Tham khảo `references/vnstock_usage.md` + `vn-financial-data-collector/references/vnstock_api.md` cho code đầy đủ. Tóm tắt:

```python
from vnstock.api.quote import Quote
from vnstock.api.company import Company
from vnstock.api.financial import Finance

# Giá 52 tuần
q = Quote(symbol='HPG', source='VCI')
df = q.history(start='YYYY-MM-DD', end='YYYY-MM-DD', interval='1W')
# ⚠️ Giá = NGHÌN đồng (19.38 = 19,380 đ)
df = df.dropna(subset=['close'])

# Overview — vốn hóa, số CP, target_price analyst (cho context)
c = Company(symbol='HPG', source='VCI')
info = c.overview()
# info['market_cap'], info['issue_share'], info['target_price'],
# info['highest_price1_year'], info['lowest_price1_year']

# Ratios — PE/PB/EV-EBITDA tính sẵn (verify vs tự tính)
f = Finance(symbol='HPG', source='VCI')
ratios = f.ratio()
# ratios có: 'P/E','P/B','P/S','EV/EBITDA','ROE (%)','ROA (%)',
#            'Số CP lưu hành (triệu)','Vốn hóa'
```

**Lấy luôn VNINDEX + VN30** để tính tương quan:
```python
q_vni = Quote(symbol='VNINDEX', source='VCI')
df_vni = q_vni.history(start=..., end=..., interval='1W')
```

⚠️ **Bẫy đơn vị:** vnstock trả giá bằng nghìn đồng (19.38), KHÔNG phải đồng (19,380). Phải ×1000 khi tính toán.

### Bước 2: Tính indicators thực

Tham khảo `references/indicators.md` cho công thức + code Node.js/Python. Tóm tắt indicators bắt buộc:

| Indicator | Công thức | Khi nào quan trọng |
|---|---|---|
| **MA10/20/50** | Trung bình động 10/20/50 tuần | Xu hướng ngắn/trung hạn |
| **RSI(14)** | Relative Strength Index | < 30 quá bán, > 70 quá mua |
| **MACD** | EMA12 - EMA26, Signal = EMA9 | Bullish/bearish crossover |
| **Bollinger Bands** | MA20 ± 2σ | Overbought/oversold + breakout |
| **Beta** | Cov(stock,market)/Var(market) | Độ rủi ro vs thị trường |
| **Correlation** | Pearson(stock, index) | Mức độ liên quan thị trường |

### Bước 3: Phát hiện patterns — CHỈ KHI CÓ EVIDENCE

Tham khảo `references/pattern_detection.md` cho code phát hiện tự động. **Quy tắc thành thật:**

- ✅ Double Bottom: 2 đáy cách nhau ≥5 tuần, chênh <3% → flag là "TIỀM NĂNG", cần confirm
- ✅ Descending/Ascending Channel: fit trendline qua swing highs/lows → flag nếu slope rõ
- ✅ Candlestick: Hammer, Marubozu, Doji, Engulfing → flag từng nến với điều kiện body/wick
- ✅ Divergence: check 2 đáy giá + 2 đáy RSI → CHỈ flag nếu giá giảm + RSI tăng (bullish) hoặc ngược lại
- ❌ **KHÔNG** claim pattern nếu data không show — nói thẳng "không có"

### Bước 4: Render HTML

Copy template `assets/technical_template.html` (cùng phong cách dashboard). Cấu trúc:

1. **Tech Verdict Card** — score -6→+6, verdict pill (STRONG SELL → STRONG BUY)
2. **Candlestick + Volume chart** — custom canvas (Chart.js không native candlestick)
3. **4 Indicator cards** — giá hiện tại, perf 1Y, RSI, MACD
4. **Price + MA chart** + **RSI chart** + **MACD chart** (Chart.js)
5. **Correlation section** — chart 3 đường (stock vs VNINDEX vs VN30) + Beta/Alpha cards
6. **Support/Resistance zones** — swing highs/lows thực
7. **Patterns section** — chỉ patterns có evidence (Double Bottom, Channel, Candlesticks)
8. **Divergence check card** — kết quả thành thật (có hoặc KHÔNG có)
9. **Trading Strategy Insight** — 3 kịch bản (tích cực/trung tính/tiêu cực)
10. **Minh bạch dữ liệu card** — ghi rõ nguồn vnstock + patterns đã detect

## Output JSON

```json
{
  "ticker": "HPG",
  "data_source": "vnstock (VCI)",
  "data_period": "2025-06-22 to 2026-06-21",
  "price_current": 23600,
  "performance_1y_pct": 21.8,
  "high_52w": 27540,
  "low_52w": 19120,
  "indicators": {
    "ma10": 24218, "ma20": 24170, "ma50": 24153,
    "rsi14": 47.8,
    "macd": -19, "signal": 135, "macd_trend": "bearish",
    "price_vs_ma10": "below", "price_vs_ma20": "below", "price_vs_ma50": "below"
  },
  "correlation": {
    "beta_vnindex": 0.83, "beta_vn30": 0.85,
    "corr_vnindex": 0.61, "corr_vn30": 0.65,
    "alpha_1y": -9.2, "outperform_market": false
  },
  "patterns_detected": [
    {"type": "double_bottom", "status": "potential", "neckline": 25710, "target": 28300},
    {"type": "descending_channel", "status": "active", "trend": "bearish"},
    {"type": "hammer", "date": "2026-05-10", "signal": "bullish_reversal_potential"},
    {"type": "marubozu_bearish", "date": "2026-06-07", "signal": "strong_bearish_momentum"}
  ],
  "divergence": {
    "has_divergence": false,
    "note": "RSI và giá cùng hướng ở 2 đáy gần nhất — không có divergence"
  },
  "tech_score": -4,
  "verdict": "SELL/REDUCE",
  "support_resistance": {
    "resistance": [{"level": "R1", "price": 27540, "note": "52W high"}, {"level": "R2", "price": 24153, "note": "MA50"}],
    "support": [{"level": "S1", "price": 24218, "note": "MA10"}, {"level": "S2", "price": 19120, "note": "52W low"}]
  }
}
```

## Tech Score decision table

Tính score từ 6 signals (mỗi signal ±1):

| Signal | +1 (bullish) | -1 (bearish) |
|---|---|---|
| Giá vs MA10 | Trên | Dưới |
| Giá vs MA20 | Trên | Dưới |
| Giá vs MA50 | Trên | Dưới |
| RSI | > 55 | < 45 |
| MACD vs Signal | Trên (bullish) | Dưới (bearish) |
| BB Position | > 50% | < 50% |

| Score | Verdict | Khuyến nghị |
|---|---|---|
| +4 đến +6 | STRONG BUY | Tích lũy mạnh |
| +1 đến +3 | BUY | Tích lũy |
| -1 đến 0 | HOLD/NEUTRAL | Quan sát |
| -3 đến -2 | SELL/REDUCE | Hạn chế |
| -6 đến -4 | STRONG SELL | Tránh/Cắt lỗ |

⚠️ **Cổ phiếu chu kỳ:** Score bearish không phải lúc nào cũng = bán. Kết hợp với fundamental (skill `vn-valuation-engine`) để decide.

## Phối hợp với skills khác

- **Data fundamental**: `vn-financial-data-collector`
- **Định giá**: `vn-valuation-engine` (cơ bản vs kỹ thuật divergence)
- **Dashboard**: `vn-research-dashboard` (ghép technical vào report)
- **News**: `vn-news-digest`

## Tham khảo

- `references/vnstock_usage.md` — Code Python fetch giá + indicators (Quote, history, dropna, đơn vị nghìn đồng)
- `references/indicators.md` — Công thức + code Node.js/Python cho MA/RSI/MACD/Bollinger/Beta/Correlation
- `references/pattern_detection.md` — Code phát hiện Double Bottom, Channel, Candlestick, Divergence (với điều kiện evidence rõ)
- `assets/technical_template.html` — Template HTML (candlestick canvas + Chart.js + correlation)
