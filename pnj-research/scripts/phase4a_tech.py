#!/usr/bin/env python3
"""
Phase 4a: Technical Analysis — Mode ACTIVE
Weekly 52 weeks, Tech Score -6→+6, Verdict STRONG SELL→STRONG BUY
Indicators: MA10/20/50, RSI(14), MACD, Bollinger, Beta
Pattern detection (only with evidence)
"""
import json, os, math

TICKER = "PNJ"
WORK_DIR = "/Users/bobo/ZCodeProject/pnj-research"
DATA_DIR = os.path.join(WORK_DIR, "data")

with open(os.path.join(DATA_DIR, "price_weekly.json")) as f:
    pw = json.load(f)
with open(os.path.join(DATA_DIR, "vnindex.json")) as f:
    vni = json.load(f)
with open(os.path.join(DATA_DIR, "vn30.json")) as f:
    vn30 = json.load(f)
with open(os.path.join(DATA_DIR, "overview.json")) as f:
    ov = json.load(f)

closes = pw["close"]
highs = pw["high"]
lows = pw["low"]
volumes = pw["volume"]
times = pw["time"]
n = len(closes)
current = closes[-1]

print("=" * 60)
print(f"  PHASE 4a: Technical ACTIVE — {TICKER}")
print("=" * 60)
print(f"  Bars: {n} weekly | Current: {current:,.0f} VND | Date: {times[-1]}")

# ============ MOVING AVERAGES ============
def sma(data, period):
    out = [None] * (period - 1)
    for i in range(period - 1, len(data)):
        out.append(sum(data[i - period + 1 : i + 1]) / period)
    return out

def ema(data, period):
    k = 2 / (period + 1)
    out = [data[0]]
    for i in range(1, len(data)):
        out.append(data[i] * k + out[-1] * (1 - k))
    return out

ma10 = sma(closes, 10)
ma20 = sma(closes, 20)
ma50 = sma(closes, 50)

ma10_last = ma10[-1]
ma20_last = ma20[-1]
ma50_last = ma50[-1] if ma50[-1] else (ma50[-2] if len(ma50) > 1 else None)

print(f"\n[1] Moving Averages:")
ma50_str = f"{ma50_last:,.0f}" if ma50_last else "NA"
print(f"  MA10: {ma10_last:,.0f} | MA20: {ma20_last:,.0f} | MA50: {ma50_str}")
print(f"  Price vs MA10: {'ABOVE' if current > ma10_last else 'BELOW'} ({(current/ma10_last-1)*100:+.1f}%)")
print(f"  Price vs MA20: {'ABOVE' if current > ma20_last else 'BELOW'} ({(current/ma20_last-1)*100:+.1f}%)")
print(f"  Price vs MA50: {'ABOVE' if current > ma50_last else 'BELOW'} ({(current/ma50_last-1)*100:+.1f}%)")

# ============ RSI(14) ============
def rsi_calc(data, period=14):
    out = [None] * len(data)
    if len(data) <= period:
        return out
    avg_gain = 0
    avg_loss = 0
    for i in range(1, period + 1):
        ch = data[i] - data[i - 1]
        if ch > 0:
            avg_gain += ch
        else:
            avg_loss += abs(ch)
    avg_gain /= period
    avg_loss /= period
    out[period] = 100 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)
    for i in range(period + 1, len(data)):
        ch = data[i] - data[i - 1]
        avg_gain = (avg_gain * (period - 1) + (ch if ch > 0 else 0)) / period
        avg_loss = (avg_loss * (period - 1) + (abs(ch) if ch < 0 else 0)) / period
        out[i] = 100 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)
    return out

rsi_arr = rsi_calc(closes, 14)
rsi14 = rsi_arr[-1]
print(f"\n[2] RSI(14): {rsi14:.1f}")
if rsi14 < 30:
    rsi_state = "OVERSOLD (quá bán)"
elif rsi14 > 70:
    rsi_state = "OVERBOUGHT (quá mua)"
else:
    rsi_state = "NEUTRAL"
print(f"  State: {rsi_state}")

# ============ MACD ============
ema12 = ema(closes, 12)
ema26 = ema(closes, 26)
macd_line = [ema12[i] - ema26[i] for i in range(n)]
signal_line = ema(macd_line, 9)
histogram = [macd_line[i] - signal_line[i] for i in range(n)]
macd_last = macd_line[-1]
signal_last = signal_line[-1]
hist_last = histogram[-1]
print(f"\n[3] MACD:")
print(f"  MACD line: {macd_last:,.0f} | Signal: {signal_last:,.0f} | Histogram: {hist_last:,.0f}")
print(f"  MACD vs Signal: {'ABOVE (bullish)' if macd_last > signal_last else 'BELOW (bearish)'}")
print(f"  Histogram trend: {'Rising' if hist_last > histogram[-2] else 'Falling'}")

# ============ BOLLINGER BANDS ============
def bollinger(data, period=20, mult=2):
    out = []
    for i in range(len(data)):
        if i < period - 1:
            out.append({"upper": None, "middle": None, "lower": None})
            continue
        sl = data[i - period + 1 : i + 1]
        mean = sum(sl) / period
        var = sum((x - mean) ** 2 for x in sl) / period
        sd = math.sqrt(var)
        out.append({"upper": mean + mult * sd, "middle": mean, "lower": mean - mult * sd})
    return out

bb = bollinger(closes, 20, 2)
bb_last = bb[-1]
bb_pos = (current - bb_last["lower"]) / (bb_last["upper"] - bb_last["lower"]) * 100
print(f"\n[4] Bollinger Bands (20,2):")
print(f"  Upper: {bb_last['upper']:,.0f} | Middle: {bb_last['middle']:,.0f} | Lower: {bb_last['lower']:,.0f}")
print(f"  Position: {bb_pos:.1f}% (<20% oversold, >80% overbought)")

# ============ BETA & CORRELATION ============
def weekly_returns(arr):
    return [(arr[i] / arr[i - 1] - 1) * 100 for i in range(1, len(arr))]

def beta(stock_ret, market_ret):
    ms = sum(stock_ret) / len(stock_ret)
    mm = sum(market_ret) / len(market_ret)
    cs = [x - ms for x in stock_ret]
    cm = [x - mm for x in market_ret]
    cov = sum(x * y for x, y in zip(cs, cm)) / len(stock_ret)
    var = sum(x * x for x in cm) / len(market_ret)
    return cov / var if var else 0

def correlation(a, b):
    ma_v = sum(a) / len(a)
    mb_v = sum(b) / len(b)
    ca = [x - ma_v for x in a]
    cb = [x - mb_v for x in b]
    num = sum(x * y for x, y in zip(ca, cb))
    den = (sum(x * x for x in ca) ** 0.5) * (sum(y * y for y in cb) ** 0.5)
    return num / den if den else 0

stock_ret = weekly_returns(closes)
vni_closes = vni["close"]
vni_ret = weekly_returns(vni_closes)
# Align lengths
min_len = min(len(stock_ret), len(vni_ret))
stock_ret_aligned = stock_ret[-min_len:]
vni_ret_aligned = vni_ret[-min_len:]

beta_val = beta(stock_ret_aligned, vni_ret_aligned)
corr_val = correlation(stock_ret_aligned, vni_ret_aligned)
stock_perf = (closes[-1] / closes[0] - 1) * 100
vni_perf = (vni_closes[-1] / vni_closes[0] - 1) * 100
alpha = stock_perf - beta_val * vni_perf
print(f"\n[5] Beta & Market correlation (52w):")
print(f"  PNJ perf 52w: {stock_perf:+.1f}% | VNINDEX perf 52w: {vni_perf:+.1f}%")
print(f"  Beta: {beta_val:.2f} | Correlation: {corr_val:.2f} | Alpha: {alpha:+.1f}%")

# ============ PERFORMANCE ============
period_high = max(highs)
period_low = min(lows)
pct_from_high = (current / period_high - 1) * 100
pct_from_low = (current / period_low - 1) * 100
print(f"\n[6] Performance:")
print(f"  52w High: {period_high:,.0f} | 52w Low: {period_low:,.0f}")
print(f"  From high: {pct_from_high:+.1f}% | From low: {pct_from_low:+.1f}%")

# ============ PATTERN DETECTION ============
print(f"\n[7] Pattern detection (evidence-based):")

# Swing points
def find_swings(arr, lookback=2):
    highs_pts = []
    lows_pts = []
    for i in range(lookback, len(arr) - lookback):
        is_h = all(arr[i] > arr[i - j] and arr[i] > arr[i + j] for j in range(1, lookback + 1))
        is_l = all(arr[i] < arr[i - j] and arr[i] < arr[i + j] for j in range(1, lookback + 1))
        if is_h:
            highs_pts.append({"idx": i, "price": arr[i]})
        if is_l:
            lows_pts.append({"idx": i, "price": arr[i]})
    return highs_pts, lows_pts

swing_highs, swing_lows = find_swings(closes, 2)
print(f"  Swing highs: {len(swing_highs)} | Swing lows: {len(swing_lows)}")

# Double bottom check
patterns_found = []
if len(swing_lows) >= 2:
    l1 = swing_lows[-2]
    l2 = swing_lows[-1]
    diff = abs(l1["price"] - l2["price"]) / min(l1["price"], l2["price"]) * 100
    weeks_apart = l2["idx"] - l1["idx"]
    if diff < 3 and weeks_apart >= 5:
        between = closes[l1["idx"] : l2["idx"] + 1]
        neckline = max(between)
        status = "confirmed" if current > neckline else "potential"
        patterns_found.append({
            "type": "double_bottom",
            "bottom1": l1["price"],
            "bottom2": l2["price"],
            "neckline": neckline,
            "diff_pct": round(diff, 2),
            "weeks_apart": weeks_apart,
            "status": status,
        })
        print(f"  ✅ Double Bottom: B1={l1['price']:,.0f} B2={l2['price']:,.0f} (diff {diff:.1f}%), neckline={neckline:,.0f}, status={status}")
    else:
        print(f"  ❌ No double bottom (last 2 lows diff={diff:.1f}%, apart={weeks_apart}w)")

# Channel detection
recent = closes[-20:] if len(closes) >= 20 else closes
recent_high = max(recent)
recent_low = min(recent)
first_third = recent[: len(recent) // 3]
last_third = recent[-(len(recent) // 3) :]
fh = max(first_third)
lh = max(last_third)
fl = min(first_third)
ll = min(last_third)
high_slope = lh - fh
low_slope = ll - fl
if high_slope < -100 and low_slope < -100:
    patterns_found.append({"type": "descending_channel", "trend": "bearish"})
    print(f"  ✅ Descending channel (bearish)")
elif high_slope > 100 and low_slope > 100:
    patterns_found.append({"type": "ascending_channel", "trend": "bullish"})
    print(f"  ✅ Ascending channel (bullish)")
else:
    print(f"  ℹ️  Trading range (high_slope={high_slope:.0f}, low_slope={low_slope:.0f})")

# Last candle analysis (weekly)
last_open = pw["open"][-1] if pw["open"] else closes[-2]
last_close = closes[-1]
last_high = highs[-1]
last_low = lows[-1]
body = abs(last_close - last_open)
upper_wick = last_high - max(last_close, last_open)
lower_wick = min(last_close, last_open) - last_low
rng = last_high - last_low
pct_body = body / rng * 100 if rng > 0 else 0
is_up = last_close >= last_open
if lower_wick > body * 2 and pct_body < 35:
    patterns_found.append({"type": "hammer", "signal": "bullish_reversal"})
    print(f"  ✅ Hammer (bullish reversal) — lower wick {lower_wick:,.0f} > body {body:,.0f}")
elif upper_wick > body * 2 and pct_body < 35:
    patterns_found.append({"type": "shooting_star", "signal": "bearish"})
    print(f"  ✅ Shooting Star (bearish)")
elif pct_body > 70:
    patterns_found.append({"type": "marubozu_bullish" if is_up else "marubozu_bearish", "signal": "bullish_momentum" if is_up else "bearish_momentum"})
    print(f"  ✅ Marubozu {'bullish' if is_up else 'bearish'}")
else:
    print(f"  ℹ️  Last candle: body={pct_body:.0f}% of range, {'green' if is_up else 'red'} — no specific candlestick pattern")

# ============ TECH SCORE (-6 → +6) ============
print(f"\n[8] TECH SCORE (signals):")
signals = []
score = 0

# 1. MA alignment
if current > ma10_last:
    score += 1
    signals.append(f"  +1 Price > MA10 ({(current/ma10_last-1)*100:+.1f}%)")
else:
    score -= 1
    signals.append(f"  -1 Price < MA10 ({(current/ma10_last-1)*100:+.1f}%)")

if current > ma20_last:
    score += 1
    signals.append(f"  +1 Price > MA20 ({(current/ma20_last-1)*100:+.1f}%)")
else:
    score -= 1
    signals.append(f"  -1 Price < MA20 ({(current/ma20_last-1)*100:+.1f}%)")

if ma50_last and current > ma50_last:
    score += 1
    signals.append(f"  +1 Price > MA50 ({(current/ma50_last-1)*100:+.1f}%)")
else:
    score -= 1
    signals.append(f"  -1 Price < MA50")

# 2. RSI
if rsi14 < 30:
    score += 1
    signals.append(f"  +1 RSI oversold ({rsi14:.1f})")
elif rsi14 > 70:
    score -= 1
    signals.append(f"  -1 RSI overbought ({rsi14:.1f})")
else:
    signals.append(f"   0 RSI neutral ({rsi14:.1f})")

# 3. MACD
if macd_last > signal_last:
    score += 1
    signals.append(f"  +1 MACD > Signal (bullish crossover)")
else:
    score -= 1
    signals.append(f"  -1 MACD < Signal (bearish)")

# 4. Pattern bonus
if any(p.get("type") == "double_bottom" and p.get("status") == "confirmed" for p in patterns_found):
    score += 1
    signals.append("  +1 Double bottom confirmed")
elif any(p.get("type") == "descending_channel" for p in patterns_found):
    score -= 1
    signals.append("  -1 Descending channel (bearish)")

for s in signals:
    print(s)
print(f"\n  >>> TECH SCORE: {score:+d}/6")

# Verdict
if score <= -5:
    verdict = "STRONG SELL"
elif score <= -3:
    verdict = "SELL"
elif score <= -1:
    verdict = "WEAK SELL"
elif score == 0:
    verdict = "NEUTRAL"
elif score <= 2:
    verdict = "WEAK BUY"
elif score <= 4:
    verdict = "BUY"
else:
    verdict = "STRONG BUY"
print(f"  >>> VERDICT: {verdict}")

# ============ TRADING STRATEGY (3 scenarios) ============
print(f"\n[9] Trading strategy (3 scenarios):")
# Support/resistance from swing points
resistances = sorted([s["price"] for s in swing_highs if s["price"] > current])[:3]
supports = sorted([s["price"] for s in swing_lows if s["price"] < current], reverse=True)[:3]
print(f"  Resistances: {[f'{r:,.0f}' for r in resistances]}")
print(f"  Supports: {[f'{s:,.0f}' for s in supports]}")

strategies = {
    "bullish": {
        "trigger": f"Break above {resistances[0]:,.0f}" if resistances else "Break above recent high",
        "target": f"{resistances[0]*1.1:,.0f}" if resistances else "N/A",
        "stop": f"{supports[0]:,.0f}" if supports else f"{current*0.93:,.0f}",
    },
    "base": {
        "trigger": f"Hold above MA20 ({ma20_last:,.0f})",
        "target": f"{ma20_last*1.05:,.0f}",
        "stop": f"{ma20_last*0.95:,.0f}",
    },
    "bearish": {
        "trigger": f"Break below {supports[0]:,.0f}" if supports else f"Break below {current*0.95:,.0f}",
        "target": f"{supports[1]:,.0f}" if len(supports) > 1 else "N/A",
        "stop": f"{current*1.03:,.0f}",
    },
}
for name, s in strategies.items():
    print(f"  {name}: entry={s['trigger']} | target={s['target']} | stop={s['stop']}")

# ============ SAVE ============
result = {
    "ticker": TICKER,
    "mode": "ACTIVE",
    "timeframe": "weekly 52 weeks",
    "bars": n,
    "current_price": current,
    "last_date": times[-1],
    "ma10": round(ma10_last, 0),
    "ma20": round(ma20_last, 0),
    "ma50": round(ma50_last, 0) if ma50_last else None,
    "rsi14": round(rsi14, 1),
    "rsi_state": rsi_state,
    "macd": round(macd_last, 0),
    "macd_signal": round(signal_last, 0),
    "macd_histogram": round(hist_last, 0),
    "macd_state": "bullish" if macd_last > signal_last else "bearish",
    "bollinger": {"upper": round(bb_last["upper"], 0), "middle": round(bb_last["middle"], 0), "lower": round(bb_last["lower"], 0), "position_pct": round(bb_pos, 1)},
    "beta": round(beta_val, 2),
    "correlation_vnindex": round(corr_val, 2),
    "alpha_52w": round(alpha, 1),
    "perf_52w": round(stock_perf, 1),
    "vnindex_perf_52w": round(vni_perf, 1),
    "period_high": round(period_high, 0),
    "period_low": round(period_low, 0),
    "pct_from_high": round(pct_from_high, 1),
    "pct_from_low": round(pct_from_low, 1),
    "patterns": patterns_found,
    "tech_score": score,
    "verdict": verdict,
    "signals": [s.strip() for s in signals],
    "resistances": [round(r, 0) for r in resistances],
    "supports": [round(s, 0) for s in supports],
    "strategies": strategies,
    # Chart data
    "chart_time": times,
    "chart_close": closes,
    "chart_ma10": [round(x, 0) if x else None for x in ma10],
    "chart_ma20": [round(x, 0) if x else None for x in ma20],
    "chart_ma50": [round(x, 0) if x else None for x in ma50],
    "chart_rsi": [round(x, 1) if x else None for x in rsi_arr],
    "chart_volume": volumes,
}

with open(os.path.join(DATA_DIR, "tech_active.json"), "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"\n✅ Phase 4a complete → data/tech_active.json")
print(f"   Tech Score: {score:+d}/6 → {verdict}")
