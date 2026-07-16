#!/usr/bin/env python3
"""
CTD (Coteccons Construction, HOSE) — Technical Analysis
Implements BOTH modes of vn-technical-analysis skill:
  4a ACTIVE  -> technical_active.json  (score, verdict, indicators, patterns, strategy)
  4b PROFILE -> technical_profile.json (15 blocks + 8 setups + archetype, schema vn-technical-profile-v1)

Data (already fetched, in cwd):
  price_weekly_52w.csv, price_weekly_vnindex.csv, price_weekly_vn30.csv  (ACTIVE)
  price_daily_ctd.csv, price_daily_vnindex.csv, price_daily_vn30.csv      (PROFILE)
  overview.json

Price unit: vnstock prices are in THOUSANDS of VND. close=70.3 means 70,300 VND.
overview.json current_price=71700 is already in VND.
"""

import csv
import json
import math
import os
from datetime import datetime, timezone

DATA_DIR = "/Users/bobo/ZCodeProject/ctd_data"

# =============================================================================
# Helpers (ported from references/stock_profile_blocks.md + pattern_scoring.md)
# =============================================================================

def finite(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None

def round_(v, d=2):
    return None if not finite(v) else round(float(v), d)

def mean(values=[]):
    nums = [v for v in values if finite(v)]
    return sum(nums)/len(nums) if nums else None

def std_dev(values=[]):
    nums = [v for v in values if finite(v)]
    if len(nums) < 2:
        return None
    avg = mean(nums)
    return math.sqrt(sum((v-avg)**2 for v in nums) / (len(nums)-1))

def skewness(values=[]):
    nums = [v for v in values if finite(v)]
    if len(nums) < 3:
        return None
    avg, sd = mean(nums), std_dev(nums)
    if not sd:
        return None
    n = len(nums)
    return (n / ((n-1)*(n-2))) * sum(((v-avg)/sd)**3 for v in nums)

def excess_kurtosis(values=[]):
    nums = [v for v in values if finite(v)]
    if len(nums) < 4:
        return None
    avg, sd = mean(nums), std_dev(nums)
    if not sd:
        return None
    n = len(nums)
    z4 = sum(((v-avg)/sd)**4 for v in nums)
    return ((n*(n+1)) / ((n-1)*(n-2)*(n-3))) * z4 - (3*(n-1)**2)/((n-2)*(n-3))

def quantile(values, q):
    nums = sorted(v for v in values if finite(v))
    if not nums:
        return None
    if len(nums) == 1:
        return nums[0]
    pos = q * (len(nums) - 1)
    lo = math.floor(pos); hi = math.ceil(pos)
    if lo == hi:
        return nums[lo]
    return nums[lo] + (nums[hi] - nums[lo]) * (pos - lo)

def median(values=[]):
    return quantile(values, 0.5)

def percentile_of_value(values, value):
    nums = [v for v in values if finite(v)]
    if not nums or not finite(value):
        return None
    return round_(sum(1 for v in nums if v <= value) / len(nums) * 100)

def log_returns(rows=[]):
    out = []
    for i in range(1, len(rows)):
        p, c = rows[i-1].get("close"), rows[i].get("close")
        if p and c and p > 0 and c > 0:
            out.append(math.log(c/p))
    return out

def daily_returns_pct(rows=[]):
    out = []
    for i in range(1, len(rows)):
        p, c = rows[i-1].get("close"), rows[i].get("close")
        if p and c and p > 0 and c > 0:
            out.append((c/p - 1) * 100)
    return out

def drawdown_series(rows=[]):
    peak = None
    out = []
    for row in rows:
        c = finite(row.get("close"))
        if c is None:
            out.append(None); continue
        peak = c if peak is None else max(peak, c)
        out.append(c/peak - 1 if peak else None)
    return out

def realized_vol(rows, window):
    values = log_returns(rows)[-window:]
    if len(values) < max(5, window // 3):
        return None
    return round_(std_dev(values) * math.sqrt(252) * 100)

def realized_vol_history(rows, window):
    returns = log_returns(rows)
    min_count = max(5, window // 3)
    values = []
    for i in range(min_count, len(returns) + 1):
        sample = returns[max(0, i-window):i]
        v = round_(std_dev(sample) * math.sqrt(252) * 100) if len(sample) >= min_count else None
        if finite(v):
            values.append(v)
    return values

def pct_change(rows, window):
    if len(rows) <= window:
        return None
    start = rows[-1-window].get("close")
    end = rows[-1].get("close")
    if not (start and end and start > 0 and end > 0):
        return None
    return round_((end/start - 1) * 100)

def line_change_pct(points, window):
    if len(points) <= window:
        return None
    a = points[-1-window].get("value")
    b = points[-1].get("value")
    if not (finite(a) and finite(b)) or a == 0:
        return None
    return round_((b/a - 1) * 100)

def sma_at(rows, index, field, window):
    if index < window - 1:
        return None
    slice_ = rows[index-window+1:index+1]
    vals = [finite(r.get(field)) for r in slice_]
    vals = [v for v in vals if v is not None]
    return sum(vals)/len(vals) if len(vals) == window else None

def vwma_at(rows, index, field, window):
    if index < window - 1:
        return None
    slice_ = rows[index-window+1:index+1]
    num = 0.0; den = 0.0; ok = True
    for r in slice_:
        px = finite(r.get(field)); vol = finite(r.get("volume"))
        if px is None or vol is None:
            ok = False; break
        num += px * vol; den += vol
    return (num/den) if ok and den > 0 else None

def moving_average_before(rows, index, field, window):
    return sma_at(rows, index-1, field, window)

def average_value(rows, window):
    slice_ = rows[-window:]
    vals = [finite(r.get("value")) for r in slice_]
    vals = [v for v in vals if v is not None]
    return sum(vals)/len(vals) if vals else None

def drawdown_episodes(rows):
    peak = None; peak_date = None
    episodes = []
    in_dd = False; trough_idx = None; trough_close = None
    peak_at_start = None; peak_at_start_date = None
    for i, row in enumerate(rows):
        c = finite(row.get("close"))
        if c is None:
            continue
        if peak is None or c > peak:
            peak = c; peak_date = row.get("date")
            if in_dd:
                eps_depth = (trough_close/peak_at_start - 1)*100 if peak_at_start else None
                episodes.append({
                    "peak_date": peak_at_start_date, "trough_date": rows[trough_idx]["date"],
                    "depth_pct": round_(eps_depth), "recovery_days": i - trough_idx,
                })
                in_dd = False
        else:
            if not in_dd:
                in_dd = True; peak_at_start = peak; peak_at_start_date = peak_date
                trough_idx = i; trough_close = c
            elif c < trough_close:
                trough_idx = i; trough_close = c
    if in_dd:
        eps_depth = (trough_close/peak_at_start - 1)*100 if peak_at_start else None
        episodes.append({
            "peak_date": peak_at_start_date, "trough_date": rows[trough_idx]["date"],
            "depth_pct": round_(eps_depth), "recovery_days": None,
        })
    episodes.sort(key=lambda e: e["depth_pct"] or 0)
    return episodes

def rolling_return_series(rows, window):
    out = []
    for i in range(window, len(rows)):
        a = rows[i-window].get("close"); b = rows[i].get("close")
        if a and b and a > 0 and b > 0:
            out.append((b/a - 1) * 100)
    return out

def rolling_return_profile(rows, window):
    series = rolling_return_series(rows, window)
    values = [v for v in series if finite(v)]
    current = values[-1] if values else None
    return {
        "window": window,
        "current_return_pct": current,
        "percentile": percentile_of_value(values, current),
        "median_return_pct": round_(median(values)),
        "p10_return_pct": round_(quantile(values, 0.1)),
        "p90_return_pct": round_(quantile(values, 0.9)),
        "observations": len(values),
    }

def threshold_counts(values):
    nums = [v for v in values if finite(v)]
    return {
        "observations": len(nums),
        "up_5_pct": sum(1 for v in nums if v >= 5),
        "down_5_pct": sum(1 for v in nums if v <= -5),
        "up_10_pct": sum(1 for v in nums if v >= 10),
        "down_10_pct": sum(1 for v in nums if v <= -10),
    }

def typical_price(row):
    vals = [finite(row.get(f)) for f in ("high", "low", "close")]
    vals = [v for v in vals if v is not None]
    if len(vals) >= 3:
        return mean(vals)
    return finite(row.get("close"))

def forward_return(rows, index, window):
    if index + window >= len(rows):
        return None
    start = rows[index].get("close"); end = rows[index+window].get("close")
    if not (start and end and start > 0 and end > 0):
        return None
    return (end/start - 1) * 100

def forward_window_stats(events, key):
    matured = [e for e in events if finite(e.get(key))]
    vals = [e[key] for e in matured]
    return {
        "matured_events": len(matured),
        "median_pct": round_(median(vals), 4),
        "p25_pct": round_(quantile(vals, 0.25), 4),
        "p75_pct": round_(quantile(vals, 0.75), 4),
        "positive_rate_pct": round_(sum(1 for v in vals if v > 0)/len(vals)*100) if vals else None,
    }

def cmf_at(rows, index, window=20):
    sample = rows[max(0, index-window+1):index+1]
    sample = [r for r in sample if all(finite(r.get(f)) for f in ("high", "low", "close", "volume")) and r["volume"] > 0]
    if len(sample) < max(5, window // 2):
        return None
    vol_sum = sum(r["volume"] for r in sample)
    if not vol_sum:
        return None
    flow = 0
    for r in sample:
        rng = r["high"] - r["low"]
        if not rng:
            continue
        mult = ((r["close"] - r["low"]) - (r["high"] - r["close"])) / rng
        flow += mult * r["volume"]
    return flow / vol_sum

# pattern_scoring helpers
def pct(a, b):
    return (a/b - 1) * 100 if b else 0.0

def clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))

def slope(values):
    if len(values) < 2:
        return 0.0
    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    denom = sum((i - x_mean) ** 2 for i in range(n)) or 1
    return sum((i - x_mean) * (value - y_mean) for i, value in enumerate(values)) / denom

# =============================================================================
# CSV loading
# =============================================================================

def load_csv(path):
    """Load OHLCV csv. Prices in thousands of VND. Add value=close*volume*1000 (VND) + range_pct."""
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                o = float(r["open"]); h = float(r["high"]); lo = float(r["low"]); c = float(r["close"])
                v = float(r["volume"])
            except (ValueError, KeyError):
                continue
            if not (math.isfinite(c) and math.isfinite(v)):
                continue
            date = str(r.get("time", ""))[:10]
            rng = ((h - lo) / c * 100) if c > 0 else None
            rows.append({
                "date": date,
                "open": o, "high": h, "low": lo, "close": c,
                "volume": v,
                "value": c * v * 1000.0,  # VND
                "range_pct": rng,
            })
    return rows

def load_overview(path):
    with open(path) as f:
        return json.load(f)

# =============================================================================
# MODE 4a — ACTIVE indicators (weekly)
# Ported from references/indicators.md
# =============================================================================

def SMA(d, p):
    out = [None] * (p - 1)
    for i in range(p-1, len(d)):
        out.append(sum(d[i-p+1:i+1]) / p)
    return out

def EMA(d, p):
    if not d:
        return []
    k = 2 / (p + 1)
    o = [d[0]]
    for i in range(1, len(d)):
        o.append(d[i]*k + o[i-1]*(1-k))
    return o

def RSI(data, period=14):
    rs = [None] * len(data)
    if len(data) <= period:
        return rs
    avgGain = 0.0; avgLoss = 0.0
    for i in range(1, period + 1):
        ch = data[i] - data[i-1]
        if ch > 0: avgGain += ch
        else: avgLoss += abs(ch)
    avgGain /= period; avgLoss /= period
    rs[period] = 100 if avgLoss == 0 else 100 - 100/(1 + avgGain/avgLoss)
    for i in range(period + 1, len(data)):
        ch = data[i] - data[i-1]
        avgGain = (avgGain*(period-1) + (ch if ch > 0 else 0)) / period
        avgLoss = (avgLoss*(period-1) + (abs(ch) if ch < 0 else 0)) / period
        rs[i] = 100 if avgLoss == 0 else 100 - 100/(1 + avgGain/avgLoss)
    return rs

def Bollinger(data, period=20, mult=2):
    sma = SMA(data, period)
    out = []
    for i in range(len(data)):
        if i < period - 1:
            out.append({"upper": None, "middle": None, "lower": None})
            continue
        slice_ = data[i - period + 1: i + 1]
        m = sma[i]
        variance = sum((v - m)**2 for v in slice_) / period
        sd = math.sqrt(variance)
        out.append({"upper": m + mult * sd, "middle": m, "lower": m - mult * sd})
    return out

def findSwings(closes, lookback=2):
    highs = []; lows = []
    for i in range(lookback, len(closes) - lookback):
        isHigh = True; isLow = True
        for j in range(1, lookback + 1):
            if closes[i] <= closes[i-j] or closes[i] <= closes[i+j]: isHigh = False
            if closes[i] >= closes[i-j] or closes[i] >= closes[i+j]: isLow = False
        if isHigh: highs.append({"idx": i, "price": closes[i]})
        if isLow: lows.append({"idx": i, "price": closes[i]})
    return {"highs": highs, "lows": lows}

def detectDoubleBottom(closes, lows):
    patterns = []
    for i in range(len(lows) - 1):
        for j in range(i + 1, len(lows)):
            l1 = lows[i]; l2 = lows[j]
            diff = abs(l1["price"] - l2["price"]) / min(l1["price"], l2["price"]) * 100
            weeksApart = l2["idx"] - l1["idx"]
            if diff < 3 and weeksApart >= 5:
                between = closes[l1["idx"]:l2["idx"] + 1]
                neckline = max(between)
                patterns.append({
                    "type": "double_bottom",
                    "bottom1_idx": l1["idx"], "bottom1_price": l1["price"],
                    "bottom2_idx": l2["idx"], "bottom2_price": l2["price"],
                    "neckline": neckline,
                    "target": neckline + (neckline - min(l1["price"], l2["price"])),
                    "status": "potential",
                    "weeks_apart": weeksApart,
                    "price_diff_pct": round(diff, 2),
                })
    return patterns

def detectChannel(closes, lookback=20):
    recent = closes[-lookback:]
    third = max(1, lookback // 3)
    firstHigh = max(recent[:third])
    lastHigh = max(recent[-third:])
    firstLow = min(recent[:third])
    lastLow = min(recent[-third:])
    highSlope = lastHigh - firstHigh
    lowSlope = lastLow - firstLow
    if highSlope < -1.0 and lowSlope < -1.0:  # threshold in price (thousands VND); 1.0 = 1000 VND
        return {"type": "descending_channel", "trend": "bearish",
                "high_start": firstHigh, "high_end": lastHigh,
                "low_start": firstLow, "low_end": lastLow}
    if highSlope > 1.0 and lowSlope > 1.0:
        return {"type": "ascending_channel", "trend": "bullish",
                "high_start": firstHigh, "high_end": lastHigh,
                "low_start": firstLow, "low_end": lastLow}
    if abs(highSlope) < 1.0 and abs(lowSlope) < 1.0:
        return {"type": "trading_range", "trend": "neutral"}
    return None

def analyzeCandle(c):
    body = abs(c["close"] - c["open"])
    upperWick = c["high"] - max(c["close"], c["open"])
    lowerWick = min(c["close"], c["open"]) - c["low"]
    rng = c["high"] - c["low"]
    pctBody = (body / rng * 100) if rng > 0 else 0
    isUp = c["close"] >= c["open"]
    patterns = []
    if lowerWick > body * 2 and pctBody < 35 and not isUp:
        patterns.append({"name": "hammer", "signal": "bullish_reversal"})
    if lowerWick > body * 2 and pctBody < 35 and isUp:
        patterns.append({"name": "inverted_hammer", "signal": "bullish_reversal"})
    if upperWick > body * 2 and pctBody < 35:
        patterns.append({"name": "shooting_star", "signal": "bearish"})
    if pctBody > 70:
        patterns.append({"name": "marubozu_bullish" if isUp else "marubozu_bearish",
                         "signal": "bullish_momentum" if isUp else "bearish_momentum"})
    if pctBody < 10:
        patterns.append({"name": "doji", "signal": "indecision"})
    return patterns

def detectEngulfing(candles):
    patterns = []
    for i in range(1, len(candles)):
        prev = candles[i-1]; curr = candles[i]
        prevUp = prev["close"] >= prev["open"]
        currUp = curr["close"] >= curr["open"]
        if not prevUp and currUp and curr["close"] > prev["open"] and curr["open"] < prev["close"]:
            patterns.append({"idx": i, "date": curr.get("date"), "type": "bullish_engulfing", "signal": "bullish_strong"})
        if prevUp and not currUp and curr["close"] < prev["open"] and curr["open"] > prev["close"]:
            patterns.append({"idx": i, "date": curr.get("date"), "type": "bearish_engulfing", "signal": "bearish_strong"})
    return patterns

def detectThreeSoldiers(candles):
    if len(candles) < 3:
        return None
    last3 = candles[-3:]
    allGreen = all(c["close"] >= c["open"] for c in last3)
    allRed = all(c["close"] < c["open"] for c in last3)
    higherCloses = last3[0]["close"] < last3[1]["close"] < last3[2]["close"]
    lowerCloses = last3[0]["close"] > last3[1]["close"] > last3[2]["close"]
    if allGreen and higherCloses:
        return {"type": "three_white_soldiers", "signal": "bullish_reversal_strong"}
    if allRed and lowerCloses:
        return {"type": "three_black_crows", "signal": "bearish_reversal_strong"}
    return None

def checkDivergence(closes, rsi, swingLows, dates=None):
    # NOTE: RSI array is same length as closes (with None for first `period` entries),
    # so rsi[idx] corresponds directly to closes[idx]. No offset subtraction needed.
    # (The reference pattern_detection.md subtracts rsiOffset=14, but that assumes a
    # shorter RSI array — incorrect for the same-length RSI implementation here.)
    if len(swingLows) < 2:
        return {"has_divergence": False, "note": "Không đủ swing lows"}
    l1 = swingLows[-2]
    l2 = swingLows[-1]
    rsi1Idx = l1["idx"]
    rsi2Idx = l2["idx"]
    if rsi1Idx >= len(rsi) or rsi2Idx >= len(rsi):
        return {"has_divergence": False, "note": "Index ngoài range RSI"}
    if rsi[rsi1Idx] is None or rsi[rsi2Idx] is None:
        return {"has_divergence": False, "note": "RSI chưa tính tại swing low (trong 14 tuần đầu)"}
    priceChange = l1["price"] - l2["price"]  # dương = giá giảm l1->l2
    rsi1 = rsi[rsi1Idx]; rsi2 = rsi[rsi2Idx]
    rsiChange = rsi1 - rsi2  # dương = RSI giảm l1->l2
    d1 = dates[l1["idx"]] if dates and l1["idx"] < len(dates) else None
    d2 = dates[l2["idx"]] if dates and l2["idx"] < len(dates) else None
    p1vnd = round(l1["price"]*1000); p2vnd = round(l2["price"]*1000)
    # Bullish divergence: giá giảm (priceChange > 0) nhưng RSI tăng (rsiChange < 0)
    if priceChange > 0 and rsiChange < 0:
        return {
            "has_divergence": True,
            "type": "bullish",
            "swing_low_1": {"date": d1, "price_vnd": p1vnd, "rsi": round(rsi1, 2)},
            "swing_low_2": {"date": d2, "price_vnd": p2vnd, "rsi": round(rsi2, 2)},
            "note": f"Giá giảm {d1} ({p1vnd:,} VND) -> {d2} ({p2vnd:,} VND) nhưng RSI tăng {rsi1:.1f} -> {rsi2:.1f}"
        }
    if priceChange < 0 and rsiChange > 0:
        return {
            "has_divergence": True,
            "type": "bearish",
            "swing_low_1": {"date": d1, "price_vnd": p1vnd, "rsi": round(rsi1, 2)},
            "swing_low_2": {"date": d2, "price_vnd": p2vnd, "rsi": round(rsi2, 2)},
            "note": f"Giá tăng {d1} ({p1vnd:,} VND) -> {d2} ({p2vnd:,} VND) nhưng RSI giảm {rsi1:.1f} -> {rsi2:.1f}"
        }
    direction_price = "giảm" if priceChange > 0 else ("tăng" if priceChange < 0 else "đi ngang")
    direction_rsi = "giảm" if rsiChange > 0 else ("tăng" if rsiChange < 0 else "đi ngang")
    return {
        "has_divergence": False,
        "swing_low_1": {"date": d1, "price_vnd": p1vnd, "rsi": round(rsi1, 2)},
        "swing_low_2": {"date": d2, "price_vnd": p2vnd, "rsi": round(rsi2, 2)},
        "note": f"Giá và RSI cùng hướng ở 2 đáy gần nhất ({d1} -> {d2}): giá {direction_price} ({p1vnd:,} -> {p2vnd:,} VND), RSI {direction_rsi} ({rsi1:.1f} -> {rsi2:.1f}) — không có divergence"
    }

def weekly_returns(closes):
    return [(closes[i]/closes[i-1]-1)*100 for i in range(1, len(closes))]

def corr(a, b):
    if len(a) != len(b) or len(a) < 2:
        return None
    ma = sum(a)/len(a); mb = sum(b)/len(b)
    ca = [x-ma for x in a]; cb = [y-mb for y in b]
    num = sum(x*y for x, y in zip(ca, cb))
    den = (sum(x*x for x in ca)**0.5) * (sum(y*y for y in cb)**0.5)
    return num/den if den else 0

def beta(stock, market):
    if len(stock) != len(market) or len(stock) < 2:
        return None
    ms = sum(stock)/len(stock); mm = sum(market)/len(market)
    cs = [x-ms for x in stock]; cm = [x-mm for x in market]
    cov = sum(x*y for x, y in zip(cs, cm)) / len(stock)
    var = sum(x*x for x in cm) / len(market)
    return cov/var if var else 0

# =============================================================================
# MODE 4b — PROFILE 15 blocks (ported from stock_profile_blocks.md)
# =============================================================================

def price_behavior_profile(rows):
    latest = rows[-1] if rows else {}
    closes_252 = [r["close"] for r in rows[-252:] if finite(r.get("close"))]
    high_52w = max(closes_252) if closes_252 else None
    low_52w = min(closes_252) if closes_252 else None
    latest_close = latest.get("close")
    returns = daily_returns_pct(rows)
    rolling = [rolling_return_profile(rows, w) for w in (21, 63, 126, 252)]
    return {
        "latest_close": latest_close,
        "latest_date": latest.get("date"),
        "return_1m_pct": pct_change(rows, 21),
        "return_3m_pct": pct_change(rows, 63),
        "return_6m_pct": pct_change(rows, 126),
        "return_1y_pct": pct_change(rows, 252),
        "high_52w": high_52w,
        "low_52w": low_52w,
        "distance_from_52w_high_pct": round_((latest_close/high_52w - 1)*100)
            if finite(high_52w) and finite(latest_close) and high_52w > 0 else None,
        "distance_from_52w_low_pct": round_((latest_close/low_52w - 1)*100)
            if finite(low_52w) and finite(latest_close) and low_52w > 0 else None,
        "rolling_returns": rolling,
        "daily_return_distribution": {
            "observations": len(returns),
            "median_pct": round_(median(returns)),
            "p10_pct": round_(quantile(returns, 0.1)),
            "p90_pct": round_(quantile(returns, 0.9)),
            **threshold_counts(returns),
        },
        "interpretation_guardrail": "Hành vi giá là quan sát lịch sử; chỉ mô tả quá khứ, không phải dự phóng xu hướng tương lai.",
    }

def volatility_profile(rows):
    vol20_hist = realized_vol_history(rows, 20)
    vol60_hist = realized_vol_history(rows, 60)
    current_vol20 = realized_vol(rows, 20)
    current_vol60 = realized_vol(rows, 60)
    range_63 = [finite(r.get("range_pct")) for r in rows[-63:]]
    range_63 = [v for v in range_63 if v is not None]
    return {
        "hv20_pct": current_vol20,
        "hv60_pct": current_vol60,
        "hv120_pct": realized_vol(rows, 120),
        "hv252_pct": realized_vol(rows, 252),
        "hv20_percentile_1y": percentile_of_value(vol20_hist[-252:], current_vol20),
        "hv60_percentile_1y": percentile_of_value(vol60_hist[-252:], current_vol60),
        "range_pct_median_63d": round_(median(range_63)),
        "range_pct_p90_63d": round_(quantile(range_63, 0.9)),
        "interpretation_guardrail": "Biến động là độ phân tán lịch sử; chỉ mô tả quá khứ, không phải dải giá kỳ vọng hay dự phóng biến động tương lai.",
    }

def max_runup_profile(rows):
    if not rows:
        return None
    low_idx = 0
    best = {"value_pct": None, "low_date": rows[0].get("date"), "high_date": rows[0].get("date")}
    for i, row in enumerate(rows):
        if row.get("close") < rows[low_idx].get("close"):
            low_idx = i
        low = rows[low_idx].get("close")
        if low and low > 0:
            v = (row.get("close")/low - 1) * 100
            if not finite(best["value_pct"]) or v > best["value_pct"]:
                best = {"value_pct": round_(v), "low_date": rows[low_idx].get("date"), "high_date": row.get("date")}
    return best

def drawdown_profile(rows):
    dd_series = drawdown_series(rows)
    finite_dd = [v for v in dd_series if finite(v)]
    current = finite_dd[-1] if finite_dd else None
    max_depth = min(finite_dd) if finite_dd else None
    underwater = 0
    for v in reversed(dd_series):
        if finite(v) and v < 0:
            underwater += 1
        else:
            break
    episodes = drawdown_episodes(rows)
    recovery_days = [e.get("recovery_days") for e in episodes if finite(e.get("recovery_days"))]
    return {
        "current_drawdown_pct": round_(current*100) if finite(current) else None,
        "current_underwater_days": underwater,
        "max_drawdown_pct": round_(max_depth*100) if finite(max_depth) else None,
        "episode_count": len(episodes),
        "deep_drawdown_count_10_pct": sum(1 for e in episodes if (e.get("depth_pct") or 0) <= -10),
        "deep_drawdown_count_20_pct": sum(1 for e in episodes if (e.get("depth_pct") or 0) <= -20),
        "deep_drawdown_count_30_pct": sum(1 for e in episodes if (e.get("depth_pct") or 0) <= -30),
        "median_recovery_days": round_(median(recovery_days), 0) if recovery_days else None,
        "worst_episodes": episodes[:5],
        "max_runup": max_runup_profile(rows),
        "interpretation_guardrail": "Mức giảm từ đỉnh nhạy với cửa sổ và dữ liệu chưa điều chỉnh sự kiện vốn; chỉ mô tả quá khứ, không phải dự phóng đáy/đỉnh.",
    }

def liquidity_profile(rows):
    latest = rows[-1] if rows else {}
    values_252 = [finite(r.get("value")) for r in rows[-252:]]
    values_252 = [v for v in values_252 if v is not None]
    avg20 = average_value(rows, 20)
    avg60 = average_value(rows, 60)
    latest_value = finite(latest.get("value"))
    spike_days = 0
    for i in range(max(0, len(rows)-252), len(rows)):
        vol = finite(rows[i].get("volume"))
        avg20_at = sma_at(rows, i-1, "volume", 20)
        if vol and avg20_at and avg20_at > 0 and vol >= 2*avg20_at:
            spike_days += 1
    return {
        "latest_volume": latest.get("volume"),
        "latest_value": latest_value,
        "avg_value_20d": avg20,
        "avg_value_60d": avg60,
        "latest_value_percentile_1y": percentile_of_value(values_252, latest_value),
        "liquidity_stability": round_(std_dev(values_252)/mean(values_252) * 100)
            if values_252 and mean(values_252) else None,
        "volume_spike_days_1y": spike_days,
        "interpretation_guardrail": "Thanh khoản tính từ giá đóng cửa × khối lượng; không phản ánh block trade, sổ lệnh hay dữ liệu intraday.",
    }

def return_distribution_profile(rows):
    daily = daily_returns_pct(rows)
    one_year = daily[-252:]
    histogram_bins = [
        ("<= -10%", float("-inf"), -10), ("-10% đến -5%", -10, -5),
        ("-5% đến -2%", -5, -2), ("-2% đến 0%", -2, 0),
        ("0% đến 2%", 0, 2), ("2% đến 5%", 2, 5),
        ("5% đến 10%", 5, 10), ("> 10%", 10, float("inf")),
    ]
    def stats(sample):
        return {
            "observations": len(sample),
            "mean_pct": round_(mean(sample), 4),
            "median_pct": round_(median(sample), 4),
            "std_pct": round_(std_dev(sample), 4),
            "p01_pct": round_(quantile(sample, 0.01), 4),
            "p05_pct": round_(quantile(sample, 0.05), 4),
            "p25_pct": round_(quantile(sample, 0.25), 4),
            "p75_pct": round_(quantile(sample, 0.75), 4),
            "p95_pct": round_(quantile(sample, 0.95), 4),
            "p99_pct": round_(quantile(sample, 0.99), 4),
            "iqr_pct": round_(quantile(sample, 0.75) - quantile(sample, 0.25), 4),
            "skewness": round_(skewness(sample), 4),
            "excess_kurtosis": round_(excess_kurtosis(sample), 4),
            "positive_day_rate_pct": round_(sum(1 for v in sample if v > 0)/len(sample)*100) if sample else None,
        }
    return {
        "full_sample": stats(daily),
        "one_year": stats(one_year),
        "one_year_histogram": [
            {"label": lbl, "count": sum(1 for v in one_year if mn < v <= mx)}
            for lbl, mn, mx in histogram_bins
        ],
        "interpretation_guardrail": "Phân phối lợi suất là thống kê mô tả quá khứ; không giả định phân phối chuẩn; chỉ mô tả quá khứ, không dự phóng lợi suất tương lai.",
    }

def tail_risk_profile(rows):
    daily = daily_returns_pct(rows)
    tail = daily[-252:]
    q05 = quantile(tail, 0.05)
    q01 = quantile(tail, 0.01)
    es05 = mean([v for v in tail if v <= q05]) if finite(q05) else None
    es01 = mean([v for v in tail if v <= q01]) if finite(q01) else None
    rolling21 = [v for v in rolling_return_series(rows, 21) if finite(v)]
    rolling63 = [v for v in rolling_return_series(rows, 63) if finite(v)]
    return {
        "observations_1y": len(tail),
        "historical_var_95_1d_pct": round_(abs(q05), 4) if finite(q05) else None,
        "historical_var_99_1d_pct": round_(abs(q01), 4) if finite(q01) else None,
        "expected_shortfall_95_1d_pct": round_(abs(es05), 4) if finite(es05) else None,
        "expected_shortfall_99_1d_pct": round_(abs(es01), 4) if finite(es01) else None,
        "down_5pct_days_1y": sum(1 for v in tail if v <= -5),
        "down_10pct_days_1y": sum(1 for v in tail if v <= -10),
        "rolling_21d_p05_pct": round_(quantile(rolling21, 0.05)),
        "rolling_63d_p05_pct": round_(quantile(rolling63, 0.05)),
        "interpretation_guardrail": "Tail risk dùng lịch sử đã quan sát; VaR/ES ở đây là mô tả historical, không phải mô hình rủi ro giao dịch.",
    }

def liquidity_risk_profile(rows):
    tail = rows[-252:]
    values = [finite(r.get("value")) for r in tail]
    values = [v for v in values if v is not None and v >= 0]
    latest = rows[-1] if rows else {}
    avg20 = average_value(rows, 20)
    avg60 = average_value(rows, 60)
    med252 = median(values)
    drought_thr = med252 * 0.5 if finite(med252) else None
    severe_thr = med252 * 0.2 if finite(med252) else None
    capacity20 = avg20 * 0.1 if finite(avg20) else None
    capacity60 = avg60 * 0.1 if finite(avg60) else None
    def days_to_trade(notional):
        return {
            "notional": notional,
            "at_10pct_adv20_days": round_(notional/capacity20, 2) if capacity20 else None,
            "at_10pct_adv60_days": round_(notional/capacity60, 2) if capacity60 else None,
        }
    zero_vol = sum(1 for r in tail if (r.get("volume") or 0) <= 0)
    thin_days = sum(1 for r in tail if finite(r.get("value")) and r["value"] <= severe_thr) if severe_thr else 0
    drought_days = sum(1 for r in tail if finite(r.get("value")) and r["value"] <= drought_thr) if drought_thr else 0
    label = "trung bình"
    if zero_vol > 5 or thin_days >= 40 or (finite(avg20) and finite(med252) and avg20 < med252*0.4):
        label = "cao"
    if zero_vol == 0 and thin_days < 10 and finite(avg20) and finite(med252) and avg20 >= med252*0.8:
        label = "thấp"
    return {
        "observations_1y": len(tail),
        "latest_value": latest.get("value"),
        "median_value_1y": round_(med252, 0) if finite(med252) else None,
        "avg_value_20d": avg20,
        "avg_value_60d": avg60,
        "latest_value_percentile_1y": percentile_of_value(values, latest.get("value")),
        "zero_volume_days_1y": zero_vol,
        "value_drought_days_1y": drought_days,
        "severe_thin_value_days_1y": thin_days,
        "trade_capacity_scenarios": [days_to_trade(n) for n in (1_000_000_000, 5_000_000_000, 10_000_000_000)],
        "liquidity_risk_label": label,
        "interpretation_guardrail": "Rủi ro thanh khoản chỉ là stress test theo giá trị giao dịch lịch sử; không phản ánh sổ lệnh thời gian thực hoặc chi phí trượt giá thực tế.",
    }

def paired_rows(stock_rows, bench_rows):
    bench_by_date = {r.get("date"): r for r in bench_rows}
    out = []
    for r in stock_rows:
        b = bench_by_date.get(r.get("date"))
        if b and finite(r.get("close")) and finite(b.get("close")):
            out.append({"date": r.get("date"), "stock": r, "benchmark": b})
    return out

def benchmark_metrics(paired, window=252):
    pairs = paired[-(window+1):]
    if len(pairs) < max(5, window // 2):
        return None
    stock_rets, bench_rets = [], []
    for i in range(1, len(pairs)):
        sp, sc = pairs[i-1]["stock"]["close"], pairs[i]["stock"]["close"]
        bp, bc = pairs[i-1]["benchmark"]["close"], pairs[i]["benchmark"]["close"]
        if sp > 0 and bp > 0:
            stock_rets.append(sc/sp - 1); bench_rets.append(bc/bp - 1)
    if len(stock_rets) < max(5, window // 2):
        return None
    stock_cum = 1.0; bench_cum = 1.0
    for s, b in zip(stock_rets, bench_rets):
        stock_cum *= (1+s); bench_cum *= (1+b)
    stock_ret = stock_cum - 1; bench_ret = bench_cum - 1
    ms = sum(stock_rets)/len(stock_rets)
    mb = sum(bench_rets)/len(bench_rets)
    cs = [s-ms for s in stock_rets]; cb = [b-mb for b in bench_rets]
    cov = sum(x*y for x, y in zip(cs, cb)) / (len(stock_rets) - 1)
    var = sum(x*x for x in cb) / (len(bench_rets) - 1)
    beta_v = cov/var if var else None
    den_corr = (sum(x*x for x in cs)**0.5) * (sum(y*y for y in cb)**0.5)
    corr_v = sum(x*y for x, y in zip(cs, cb))/den_corr if den_corr else None
    r2 = corr_v*corr_v if finite(corr_v) else None
    hit_rate = sum(1 for s, b in zip(stock_rets, bench_rets) if s > b) / len(stock_rets) * 100
    stock_dd = drawdown_series([p["stock"] for p in pairs])
    bench_dd = drawdown_series([p["benchmark"] for p in pairs])
    dd_pairs = [(s, b) for s, b in zip(stock_dd, bench_dd) if finite(s) and finite(b)]
    if dd_pairs:
        ds = [x[0] for x in dd_pairs]; db = [x[1] for x in dd_pairs]
        ms2 = sum(ds)/len(ds); mb2 = sum(db)/len(db)
        cs2 = [x-ms2 for x in ds]; cb2 = [x-mb2 for x in db]
        den2 = (sum(x*x for x in cs2)**0.5) * (sum(y*y for y in cb2)**0.5)
        dd_sim = sum(x*y for x, y in zip(cs2, cb2))/den2 if den2 else None
    else:
        dd_sim = None
    return {
        "window": window,
        "observations": len(stock_rets),
        "stock_return_pct": round_(stock_ret*100),
        "benchmark_return_pct": round_(bench_ret*100),
        "relative_return_pct": round_((stock_ret - bench_ret)*100),
        "correlation": round_(corr_v, 4),
        "beta": round_(beta_v, 4),
        "r2": round_(r2, 4) if finite(r2) else None,
        "hit_rate_pct": round_(hit_rate),
        "stock_max_drawdown_pct": round_(min(ds for ds in stock_dd if finite(ds))*100) if any(finite(x) for x in stock_dd) else None,
        "benchmark_max_drawdown_pct": round_(min(db for db in bench_dd if finite(db))*100) if any(finite(x) for x in bench_dd) else None,
        "drawdown_similarity": round_(dd_sim, 4) if finite(dd_sim) else None,
    }

def relative_strength_profile(stock_rows, bench_rows, benchmarks):
    comparisons = []
    for bid, brows in benchmarks.items():
        paired = paired_rows(stock_rows, brows)
        metrics = {str(w): benchmark_metrics(paired, w) for w in (60, 120, 252)}
        comparisons.append({"benchmark": bid, "metrics": metrics})
    best_fit = None
    for c in comparisons:
        m252 = c["metrics"].get("252")
        r2_252 = m252.get("r2") if m252 else None
        if finite(r2_252) and (best_fit is None or r2_252 > best_fit["r2_252"]):
            best_fit = {"benchmark": c["benchmark"], "r2_252": r2_252}
    vnindex = next((c for c in comparisons if c["benchmark"] == "VNINDEX"), None)
    vni_252 = vnindex["metrics"]["252"] if vnindex and vnindex["metrics"].get("252") else {}
    vni_60 = vnindex["metrics"]["60"] if vnindex and vnindex["metrics"].get("60") else {}
    vni_120 = vnindex["metrics"]["120"] if vnindex and vnindex["metrics"].get("120") else {}
    return {
        "relative_strength_profile": {
            "best_fit_benchmark": best_fit,
            "comparisons": comparisons,
            "interpretation_guardrail": "So sánh benchmark là mô tả lịch sử theo dữ liệu hiện có, chỉ mô tả quá khứ, không phải cấu trúc dự phóng.",
        },
        "dynamic_beta_profile": {
            "primary_benchmark": "VNINDEX",
            "beta_60": vni_60.get("beta") if vni_60 else None,
            "beta_120": vni_120.get("beta") if vni_120 else None,
            "beta_252": vni_252.get("beta"),
        },
        "correlation_profile": {
            "primary_benchmark": "VNINDEX",
            "corr_60": vni_60.get("correlation") if vni_60 else None,
            "corr_252": vni_252.get("correlation"),
            "r2_252": vni_252.get("r2"),
            "drawdown_similarity_252": vni_252.get("drawdown_similarity"),
        },
    }

def classify_regime(r60, r120, drawdown, vol_rank):
    if not all(finite(x) for x in (r60, r120, drawdown)):
        return {"id": "unknown", "label": "chưa đủ dữ liệu"}
    if drawdown <= -0.18 or (r60 <= -0.12 and (vol_rank or 0) >= 75):
        rid = "stress"; label = "stress"
    elif r60 > 0.06 and r120 > 0.08 and drawdown > -0.08:
        rid = "uptrend"; label = "uptrend"
    elif r60 > 0.04 and r120 <= 0.08 and drawdown > -0.14:
        rid = "recovery"; label = "phục hồi"
    else:
        rid = "sideways"; label = "sideways"
    return {"id": rid, "label": label,
            "r60": round_(r60*100), "r120": round_(r120*100),
            "drawdown_pct": round_(drawdown*100), "vol_rank": vol_rank}

def regime_profile(stock_rows, vnindex_rows):
    rows = vnindex_rows
    regimes_by_date = {}
    for i, row in enumerate(rows):
        if i < 120:
            continue
        r60 = (row["close"]/rows[i-60]["close"] - 1) if rows[i-60].get("close") else None
        r120 = (row["close"]/rows[i-120]["close"] - 1) if rows[i-120].get("close") else None
        dd = drawdown_series(rows[:i+1])[-1]
        vol_hist = realized_vol_history(rows[:i+1], 20)
        vol_now = vol_hist[-1] if vol_hist else None
        vol_rank = percentile_of_value(vol_hist, vol_now) if finite(vol_now) else None
        regimes_by_date[row["date"]] = classify_regime(r60, r120, dd, vol_rank)
    current = regimes_by_date.get(rows[-1]["date"]) if rows else None
    paired = paired_rows(stock_rows, vnindex_rows)
    groups = {}
    for i in range(1, len(paired)):
        sp, sc = paired[i-1]["stock"]["close"], paired[i]["stock"]["close"]
        bp, bc = paired[i-1]["benchmark"]["close"], paired[i]["benchmark"]["close"]
        regime = regimes_by_date.get(paired[i]["date"])
        if not regime or regime["id"] == "unknown" or not (sp > 0 and bp > 0):
            continue
        rid = regime["id"]
        g = groups.setdefault(rid, {"regime_id": rid, "regime_label": regime["label"],
                                     "stock_returns": [], "bench_returns": []})
        g["stock_returns"].append(sc/sp - 1)
        g["bench_returns"].append(bc/bp - 1)
    behavior = []
    for g in groups.values():
        srs, brs = g["stock_returns"], g["bench_returns"]
        if not srs:
            continue
        behavior.append({
            "regime_id": g["regime_id"], "regime_label": g["regime_label"],
            "observations": len(srs),
            "stock_avg_daily_return_pct": round_(mean(srs)*100, 4),
            "benchmark_avg_daily_return_pct": round_(mean(brs)*100, 4),
            "relative_avg_daily_return_pct": round_((mean(srs) - mean(brs))*100, 4),
            "hit_rate_pct": round_(sum(1 for s, b in zip(srs, brs) if s > b)/len(srs)*100),
        })
    behavior.sort(key=lambda x: x["regime_id"])
    return {
        "primary_benchmark": "VNINDEX",
        "current_market_regime": current,
        "behavior_by_market_regime": behavior,
        "regime_guardrail": "Regime dùng trạng thái benchmark hiện có; không thay thế lịch sử thành phần point-in-time.",
    }

def volume_price_profile(rows):
    tail = rows[-252:]
    up_value = [finite(r.get("value")) for i, r in enumerate(tail) if i > 0 and finite(r.get("value"))
                and finite(tail[i-1].get("close")) and r.get("close") > tail[i-1].get("close")]
    down_value = [finite(r.get("value")) for i, r in enumerate(tail) if i > 0 and finite(r.get("value"))
                  and finite(tail[i-1].get("close")) and r.get("close") < tail[i-1].get("close")]
    up_value = [v for v in up_value if v is not None]
    down_value = [v for v in down_value if v is not None]
    avg_up = mean(up_value); avg_down = mean(down_value)
    pairs = []
    for i in range(1, len(tail)):
        ret = finite(tail[i].get("close")) and finite(tail[i-1].get("close"))
        if ret and tail[i-1]["close"] > 0 and finite(tail[i].get("value")):
            pairs.append((abs(tail[i]["close"]/tail[i-1]["close"] - 1), tail[i]["value"]))
    if len(pairs) >= 5:
        xs = [p[0] for p in pairs]; ys = [p[1] for p in pairs]
        mx, my = mean(xs), mean(ys)
        cx = [x-mx for x in xs]; cy = [y-my for y in ys]
        den = (sum(x*x for x in cx)**0.5) * (sum(y*y for y in cy)**0.5)
        ret_value_corr = round_(sum(x*y for x, y in zip(cx, cy))/den, 4) if den else None
    else:
        ret_value_corr = None
    return {
        "observations_1y": len(tail),
        "avg_value_up_days": round_(avg_up) if avg_up else None,
        "avg_value_down_days": round_(avg_down) if avg_down else None,
        "up_down_value_ratio_1y": round_(avg_up/avg_down, 4) if avg_up and avg_down else None,
        "abs_return_value_correlation_1y": ret_value_corr,
        "interpretation_guardrail": "Quan hệ giá-khối lượng là đồng biến hay nghịch biến trong quá khứ; không kết luận dòng tiền tương lai.",
    }

def confirmation_label(vpci_latest, vpci_change_20d, price_vs_sma_long, volume_ratio):
    known = [v for v in (vpci_latest, price_vs_sma_long, volume_ratio) if finite(v)]
    if len(known) < 2:
        return "chưa đủ dữ liệu"
    vc = vpci_change_20d or 0
    if finite(vpci_latest) and vpci_latest > 0 and vc >= 0 and (price_vs_sma_long or 0) >= 0 and (volume_ratio or 0) >= 0.8:
        return "giá-volume cùng xác nhận"
    if finite(vpci_latest) and vpci_latest < 0 and vc <= 0 and (price_vs_sma_long or 0) <= 0 and (volume_ratio or 0) >= 0.8:
        return "giá-volume cùng suy yếu"
    if (price_vs_sma_long or 0) >= 0 and (finite(vpci_latest) and vpci_latest <= 0):
        return "giá đi trước volume"
    if (price_vs_sma_long or 0) <= 0 and (finite(vpci_latest) and vpci_latest >= 0):
        return "volume không cùng chiều giá"
    return "hỗn hợp"

def vpci_profile(rows, short_window=20, long_window=100):
    series = []
    for i, row in enumerate(rows):
        sma_s = sma_at(rows, i, "close", short_window)
        sma_l = sma_at(rows, i, "close", long_window)
        vwma_s = vwma_at(rows, i, "close", short_window)
        vwma_l = vwma_at(rows, i, "close", long_window)
        avg_vol_s = sma_at(rows, i, "volume", short_window)
        avg_vol_l = sma_at(rows, i, "volume", long_window)
        vpc = (vwma_l - sma_l) if (finite(vwma_l) and finite(sma_l)) else None
        vpr = (vwma_s / sma_s) if (finite(vwma_s) and finite(sma_s) and sma_s) else None
        vm = (avg_vol_s / avg_vol_l) if (finite(avg_vol_s) and finite(avg_vol_l) and avg_vol_l > 0) else None
        vpci = (vpc * vpr * vm) if all(finite(x) for x in (vpc, vpr, vm)) else None
        series.append({"date": row.get("date"), "value": vpci,
                       "sma_short": sma_s, "sma_long": sma_l,
                       "volume_ratio_short_long": vm})
    valid = [s for s in series if finite(s.get("value"))]
    latest = series[-1] if series else {}
    latest_valid = valid[-1] if valid else {}
    latest_close = rows[-1].get("close") if rows else None
    price_vs_sma_long = (round_((latest_close/latest["sma_long"] - 1)*100)
                         if finite(latest_close) and finite(latest.get("sma_long")) and latest["sma_long"]
                         else None)
    vpci_change_20d = line_change_pct(valid, 20)
    label = confirmation_label(latest_valid.get("value"), vpci_change_20d,
                                price_vs_sma_long, latest.get("volume_ratio_short_long"))
    return {
        "methodology": "VPCI/VWMA/SMA daily OHLCV, fixed windows 20/100",
        "short_window": short_window, "long_window": long_window,
        "observations": len(rows), "valid_observations": len(valid),
        "sma_20": latest.get("sma_short"), "sma_100": latest.get("sma_long"),
        "price_vs_sma100_pct": price_vs_sma_long,
        "vpci_latest": latest_valid.get("value"),
        "vpci_20d_change_pct": vpci_change_20d,
        "vpci_percentile_1y": percentile_of_value([v["value"] for v in valid[-252:]], latest_valid.get("value")),
        "confirmation_label": label,
        "interpretation_guardrail": "VPCI/VWMA/SMA mô tả mức đồng thuận giữa giá và volume; chỉ mô tả quá khứ, không phải cấu trúc giao dịch hay dự phóng giá.",
    }

def money_flow_label(cmf20, cmf60, vpt_chg, obv_chg):
    vals = [v for v in (cmf20, cmf60, vpt_chg, obv_chg) if finite(v)]
    pos = sum(1 for v in vals if v > 0); neg = sum(1 for v in vals if v < 0)
    if pos + neg < 2:
        return "chưa đủ dữ liệu"
    if pos >= 3 and (cmf20 or 0) > 0.03 and (cmf60 or 0) >= 0:
        return "áp lực tiền dương"
    if neg >= 3 and (cmf20 or 0) < -0.03 and (cmf60 or 0) <= 0:
        return "áp lực tiền âm"
    if pos >= 3 and (not finite(cmf20) or cmf20 >= 0) and (not finite(cmf60) or cmf60 >= -0.03):
        return "nghiêng dương nhưng yếu"
    if neg >= 3 and (not finite(cmf20) or cmf20 <= 0) and (not finite(cmf60) or cmf60 <= 0.03):
        return "nghiêng âm nhưng yếu"
    return "hỗn hợp"

def money_flow_profile(rows):
    cum = []; obv = 0; vpt = 0
    for i in range(1, len(rows)):
        p, r = rows[i-1], rows[i]
        if not (p.get("close", 0) > 0 and r.get("close", 0) > 0) or not finite(r.get("volume")):
            continue
        ret = r["close"]/p["close"] - 1
        if r["close"] > p["close"]:
            obv += r["volume"]
        elif r["close"] < p["close"]:
            obv -= r["volume"]
        vpt += r["volume"] * ret
        cum.append({"date": r.get("date"), "obv": obv, "vpt": vpt,
                    "ret_pct": ret*100, "volume": r["volume"]})
    cmf20 = cmf_at(rows, len(rows)-1, 20)
    cmf60 = cmf_at(rows, len(rows)-1, 60)
    latest = cum[-1] if cum else {}
    vpt_chg = line_change_pct([{"value": c["vpt"]} for c in cum], 20)
    obv_chg = line_change_pct([{"value": c["obv"]} for c in cum], 20)
    label = money_flow_label(cmf20, cmf60, vpt_chg, obv_chg)
    tail = cum[-252:]
    return {
        "methodology": "OBV, VPT, CMF daily OHLCV, fixed windows 20/60",
        "observations": len(rows), "valid_observations": len(cum),
        "latest_date": latest.get("date"),
        "obv_latest": round_(latest.get("obv"), 0) if latest.get("obv") is not None else None,
        "vpt_latest": round_(latest.get("vpt"), 4) if latest.get("vpt") is not None else None,
        "obv_20d_change_pct": obv_chg,
        "vpt_20d_change_pct": vpt_chg,
        "cmf_20d": round_(cmf20, 4) if finite(cmf20) else None,
        "cmf_60d": round_(cmf60, 4) if finite(cmf60) else None,
        "positive_flow_days_1y": sum(1 for c in tail if c["ret_pct"] > 0 and c.get("volume", 0) > 0),
        "negative_flow_days_1y": sum(1 for c in tail if c["ret_pct"] < 0 and c.get("volume", 0) > 0),
        "money_flow_label": label,
        "interpretation_guardrail": "Money flow mô tả áp lực từ OHLCV ngày; không thay thế dữ liệu intraday, block trade, sổ lệnh hoặc lời gọi giao dịch.",
    }

def effort_result_label(low_cnt, high_cnt, he_cnt, latest_effort, latest_rpe, median_rpe):
    if not he_cnt:
        return "chưa đủ high-effort events"
    low_share = low_cnt / he_cnt; high_share = high_cnt / he_cnt
    if (finite(latest_effort) and latest_effort >= 2 and finite(latest_rpe) and finite(median_rpe)
            and latest_rpe <= median_rpe * 0.7):
        return "effort cao, result thấp"
    if low_share >= 0.45:
        return "thường có effort cao nhưng result thấp"
    if high_share >= 0.45:
        return "effort cao thường đi cùng result lớn"
    return "effort-result hỗn hợp"

def effort_result_profile(rows):
    obs = []
    for i in range(1, len(rows)):
        p, r = rows[i-1], rows[i]
        if not (p.get("close", 0) > 0 and r.get("close", 0) > 0):
            continue
        vol_avg20 = moving_average_before(rows, i, "volume", 20)
        val_avg20 = moving_average_before(rows, i, "value", 20)
        ret = (r["close"]/p["close"] - 1) * 100
        rng = r.get("range_pct") if finite(r.get("range_pct")) else None
        if rng is None and finite(r.get("high")) and finite(r.get("low")):
            rng = (r["high"]-r["low"])/p["close"]*100
        vol_ratio = (r["volume"]/vol_avg20) if (finite(r.get("volume")) and finite(vol_avg20) and vol_avg20 > 0) else None
        val_ratio = (r["value"]/val_avg20) if (finite(r.get("value")) and finite(val_avg20) and val_avg20 > 0) else None
        effort = mean([v for v in (vol_ratio, val_ratio) if finite(v)])
        result = max(abs(ret) if finite(ret) else 0, rng if finite(rng) else 0)
        obs.append({"date": r.get("date"), "ret_pct": ret, "abs_ret_pct": abs(ret),
                    "range_pct": rng, "effort_ratio": effort, "result_pct": result,
                    "result_per_effort": (result/effort) if (finite(effort) and effort > 0) else None})
    tail = obs[-252:]
    result_vals = [o["result_pct"] for o in tail if finite(o.get("result_pct"))]
    rpe_vals = [o["result_per_effort"] for o in tail if finite(o.get("result_per_effort"))]
    result_median = median(result_vals); result_p75 = quantile(result_vals, 0.75)
    rpe_median = median(rpe_vals)
    high_effort = [o for o in tail if finite(o.get("effort_ratio")) and o["effort_ratio"] >= 2]
    low_rhe = [o for o in high_effort if finite(o.get("result_pct")) and finite(result_median) and o["result_pct"] <= result_median]
    high_rhe = [o for o in high_effort if finite(o.get("result_pct")) and finite(result_p75) and o["result_pct"] >= result_p75]
    latest = obs[-1] if obs else {}
    label = effort_result_label(len(low_rhe), len(high_rhe), len(high_effort),
                                 latest.get("effort_ratio"), latest.get("result_per_effort"), rpe_median)
    return {
        "methodology": "Effort = avg(normalized volume 20D, normalized value 20D); Result = max(abs return, intraday range)",
        "observations_1y": len(tail),
        "high_effort_days_1y": len(high_effort),
        "low_result_high_effort_days_1y": len(low_rhe),
        "high_result_high_effort_days_1y": len(high_rhe),
        "low_result_high_effort_share_pct": round_(len(low_rhe)/len(high_effort)*100) if high_effort else None,
        "high_result_high_effort_share_pct": round_(len(high_rhe)/len(high_effort)*100) if high_effort else None,
        "median_result_pct_1y": round_(result_median, 4) if finite(result_median) else None,
        "median_result_per_effort_1y": round_(rpe_median, 4) if finite(rpe_median) else None,
        "latest_effort_ratio": latest.get("effort_ratio"),
        "latest_result_pct": latest.get("result_pct"),
        "effort_result_label": label,
        "interpretation_guardrail": "Effort-result đo từ dữ liệu ngày để nhận diện phiên nhiều giao dịch nhưng biến động tương ứng thấp/cao; không kết luận hấp thụ/cạn cung theo nghĩa cấu trúc giao dịch.",
    }

def high_volume_behavior_label(stats20, event_count):
    if event_count < 5 or stats20.get("matured_events", 0) < 5:
        return "chưa đủ high-volume events"
    if (stats20.get("positive_rate_pct") or 0) >= 60 and (stats20.get("median_pct") or 0) > 0:
        return "sau volume cao thường giữ giá tốt hơn"
    if (stats20.get("positive_rate_pct") or 100) <= 40 and (stats20.get("median_pct") or 0) < 0:
        return "sau volume cao thường suy yếu"
    return "hành vi sau volume cao hỗn hợp"

def high_volume_behavior_profile(rows, threshold=2):
    events = []
    for i in range(1, len(rows)):
        r, p = rows[i], rows[i-1]
        avg20 = moving_average_before(rows, i, "volume", 20)
        if not (finite(r.get("volume")) and finite(avg20) and avg20 > 0
                and p.get("close", 0) > 0 and r.get("close", 0) > 0):
            continue
        norm_vol = r["volume"] / avg20
        if norm_vol < threshold:
            continue
        events.append({
            "date": r.get("date"), "close": r["close"], "volume": r["volume"],
            "normalized_volume_20d": round_(norm_vol, 4),
            "same_day_return_pct": round_((r["close"]/p["close"] - 1)*100, 4),
            "forward_return_5d_pct": round_(forward_return(rows, i, 5), 4),
            "forward_return_20d_pct": round_(forward_return(rows, i, 20), 4),
            "forward_return_60d_pct": round_(forward_return(rows, i, 60), 4),
        })
    events_1y = events[-252:]
    stats20 = forward_window_stats(events, "forward_return_20d_pct")
    label = high_volume_behavior_label(stats20, len(events))
    return {
        "methodology": "High-volume event = volume >= 2x trailing 20D average; forward returns measured after event close",
        "threshold_normalized_volume_20d": threshold,
        "observations": len(rows),
        "event_count_full_sample": len(events),
        "event_count_1y": len(events_1y),
        "forward_5d": forward_window_stats(events, "forward_return_5d_pct"),
        "forward_20d": stats20,
        "forward_60d": forward_window_stats(events, "forward_return_60d_pct"),
        "post_high_volume_label": label,
        "latest_high_volume_event": events[-1] if events else None,
        "recent_high_volume_events": events[-12:],
        "interpretation_guardrail": "Event study mô tả điều đã xảy ra sau các phiên volume cao; chỉ mô tả quá khứ, không dùng để dự phóng phiên kế tiếp hoặc sinh cấu trúc mua bán.",
    }

def pvi_nvi_label(pvi_chg20, nvi_chg20, pvi_nvi_ratio):
    known = [v for v in (pvi_chg20, nvi_chg20, pvi_nvi_ratio) if finite(v)]
    if len(known) < 2:
        return "chưa đủ dữ liệu"
    if (pvi_chg20 or 0) > 0 and (nvi_chg20 or 0) <= 0:
        return "high-volume participation nổi bật hơn"
    if (nvi_chg20 or 0) > 0 and (pvi_chg20 or 0) <= 0:
        return "low-volume participation nổi bật hơn"
    if (pvi_chg20 or 0) > 0 and (nvi_chg20 or 0) > 0:
        return "participation cùng chiều"
    if (pvi_chg20 or 0) < 0 and (nvi_chg20 or 0) < 0:
        return "participation cùng suy yếu"
    return "participation hỗn hợp"

def pvi_nvi_profile(rows):
    series = []; pvi = 1000.0; nvi = 1000.0
    for i in range(1, len(rows)):
        p, r = rows[i-1], rows[i]
        if not (p.get("close", 0) > 0 and r.get("close", 0) > 0) or not finite(p.get("volume")) or not finite(r.get("volume")):
            continue
        ret = r["close"]/p["close"] - 1
        if r["volume"] > p["volume"]:
            pvi *= (1 + ret)
        if r["volume"] < p["volume"]:
            nvi *= (1 + ret)
        direction = "higher_volume" if r["volume"] > p["volume"] else ("lower_volume" if r["volume"] < p["volume"] else "same_volume")
        series.append({"date": r.get("date"), "volume": r["volume"], "ret_pct": round_(ret*100, 4),
                       "pvi": round_(pvi, 4), "nvi": round_(nvi, 4), "volume_direction": direction})
    latest = series[-1] if series else {}
    pvi_chg20 = line_change_pct([{"value": s["pvi"]} for s in series], 20)
    nvi_chg20 = line_change_pct([{"value": s["nvi"]} for s in series], 20)
    pvi_chg60 = line_change_pct([{"value": s["pvi"]} for s in series], 60)
    nvi_chg60 = line_change_pct([{"value": s["nvi"]} for s in series], 60)
    pvi_nvi_ratio = (latest["pvi"]/latest["nvi"]) if (finite(latest.get("pvi")) and finite(latest.get("nvi")) and latest.get("nvi")) else None
    tail = series[-252:]
    label = pvi_nvi_label(pvi_chg20, nvi_chg20, pvi_nvi_ratio)
    return {
        "methodology": "PVI updates on higher-volume days; NVI updates on lower-volume days; base=1000",
        "observations": len(series),
        "latest_date": latest.get("date"),
        "pvi_latest": latest.get("pvi"), "nvi_latest": latest.get("nvi"),
        "pvi_nvi_ratio": round_(pvi_nvi_ratio, 4) if finite(pvi_nvi_ratio) else None,
        "pvi_20d_change_pct": pvi_chg20, "nvi_20d_change_pct": nvi_chg20,
        "pvi_60d_change_pct": pvi_chg60, "nvi_60d_change_pct": nvi_chg60,
        "pvi_percentile_1y": percentile_of_value([s["pvi"] for s in tail], latest.get("pvi")),
        "nvi_percentile_1y": percentile_of_value([s["nvi"] for s in tail], latest.get("nvi")),
        "higher_volume_days_1y": sum(1 for s in tail if s["volume_direction"] == "higher_volume"),
        "lower_volume_days_1y": sum(1 for s in tail if s["volume_direction"] == "lower_volume"),
        "participation_regime_label": label,
        "interpretation_guardrail": "PVI/NVI mô tả price change xảy ra nhiều hơn ở phiên volume tăng hay giảm; không phải cấu trúc giao dịch.",
    }

def volume_at_price_profile(rows, window=252, bin_count=12):
    tail = []
    for r in rows[-window:]:
        tp = typical_price(r)
        if finite(tp) and finite(r.get("volume")) and r["volume"] >= 0:
            tail.append({**r, "typical_price": tp})
    prices = [t["typical_price"] for t in tail]
    if not prices:
        return {"acceptance_label": "chưa đủ dữ liệu"}
    min_p, max_p = min(prices), max(prices)
    span = max(max_p - min_p, 0); step = span/bin_count if span > 0 else None
    bins = [{"bin_index": i, "days": 0, "volume": 0.0, "value": 0.0} for i in range(bin_count)]
    for t in tail:
        if not step:
            continue
        idx = max(0, min(bin_count-1, int((t["typical_price"] - min_p)/step)))
        bins[idx]["days"] += 1
        bins[idx]["volume"] += t.get("volume") or 0
        bins[idx]["value"] += t.get("value") or 0
    total_vol = sum(b["volume"] for b in bins) or 0
    total_val = sum(b["value"] for b in bins) or 0
    for b in bins:
        b["volume_share_pct"] = round_(b["volume"]/total_vol*100, 2) if total_vol else None
        b["value_share_pct"] = round_(b["value"]/total_val*100, 2) if total_val else None
        b["price_low"] = round_(min_p + step*b["bin_index"], 4) if step else None
        b["price_high"] = round_(min_p + step*(b["bin_index"]+1), 4) if step else None
    poc = sorted(bins, key=lambda b: b["volume"], reverse=True)[0] if bins else None
    top3 = sorted(bins, key=lambda b: b["volume"], reverse=True)[:3]
    conc = sum(b.get("volume_share_pct") or 0 for b in top3)
    latest_close = rows[-1].get("close") if rows else None
    if latest_close and step:
        cur_bin = bins[max(0, min(bin_count-1, int((latest_close - min_p)/step)))]
    else:
        cur_bin = None
    label = "chưa đủ dữ liệu"
    if len(tail) >= 60 and poc:
        if cur_bin and cur_bin["bin_index"] == poc["bin_index"]:
            label = "giá hiện tại nằm trong vùng volume lớn nhất"
        elif latest_close and latest_close > min_p + step*poc["bin_index"]:
            label = "giá hiện tại nằm trên vùng volume lớn nhất"
        elif latest_close:
            label = "giá hiện tại nằm dưới vùng volume lớn nhất"
        else:
            label = "volume-at-price hỗn hợp"
    return {
        "methodology": "Daily volume-at-price approximation: assigns each day volume/value to typical-price bins over trailing 252 sessions",
        "window": window, "bin_count": bin_count, "observations": len(tail),
        "price_min": round_(min_p, 4), "price_max": round_(max_p, 4),
        "point_of_control_bin_index": poc["bin_index"] if poc else None,
        "point_of_control_price_range": [poc["price_low"], poc["price_high"]] if poc else None,
        "current_price_bin_index": cur_bin["bin_index"] if cur_bin else None,
        "volume_concentration_top3_pct": round_(conc, 2),
        "bins": bins,
        "acceptance_label": label,
        "interpretation_guardrail": "VAP là xấp xỉ từ dữ liệu ngày; không thay thế volume profile intraday, order book hoặc phân bổ khớp lệnh thực tế trong phiên.",
    }

# =============================================================================
# PROFILE setups + archetype (from pattern_scoring.md)
# =============================================================================

def status_from_score(score, distance_pct, noisy=False):
    if noisy:
        return "nhiễu"
    if score >= 78 and distance_pct is not None and distance_pct <= 3:
        return "gần xác nhận"
    if score >= 62:
        return "đang hình thành"
    return "chưa đủ sạch"

def reader_note(pattern_name, status, distance):
    if status == "gần xác nhận":
        return f"{pattern_name} đang ở gần vùng cần xác nhận; vẫn cần chờ giá đóng cửa vượt mốc quan sát."
    if status == "đang hình thành":
        return f"{pattern_name} có cấu trúc đáng quan sát nhưng chưa đủ điều kiện xác nhận."
    if status == "nhiễu":
        return f"{pattern_name} có vài nét giống mẫu nhưng đường giá còn nhiễu."
    suffix = f", còn cách vùng xác nhận khoảng {distance:.2f}%" if distance is not None else ""
    return f"{pattern_name} chưa đủ sạch để đọc mạnh{suffix}."

def setup(pattern_id, pattern_name, score, confirmation_price, watch_low, watch_high,
          current_close, caution, status=None):
    score = round(clamp(score), 2)
    if score < 55:
        return None
    distance = max(0.0, pct(confirmation_price, current_close)) if confirmation_price else None
    final_status = status or status_from_score(score, distance)
    return {
        "pattern_id": pattern_id,
        "pattern_name": pattern_name,
        "setup_status": final_status,
        "completion_score": score,
        "confirmation_price": round(confirmation_price, 4) if confirmation_price is not None else None,
        "watch_zone": {
            "low": round(watch_low, 4) if watch_low is not None else None,
            "high": round(watch_high, 4) if watch_high is not None else None,
        },
        "distance_to_confirmation_pct": round(distance, 2) if distance is not None else None,
        "caution_reason": caution,
        "reader_note": reader_note(pattern_name, final_status, distance),
    }

def detect_bull_flag(rows):
    current = rows[-1]["close"]
    recent = rows[-14:]
    pole = rows[-44:-14]
    if len(pole) < 20:
        return None
    pole_move = pct(max(r["close"] for r in pole[-5:]), min(r["close"] for r in pole[:15]))
    recent_high = max(r["high"] for r in recent)
    recent_low = min(r["low"] for r in recent)
    recent_range = pct(recent_high, recent_low)
    pullback = pct(recent_high, current)
    compact = max(0, 25 - recent_range) * 2.2
    score = 30 + min(pole_move, 35) + compact - max(0, pullback - 8) * 2
    if pole_move < 10 or recent_range > 16:
        score -= 20
    return setup("bull_flags", "Cờ tăng", score, recent_high, recent_low, recent_high, current,
                 "Cần có nhịp dẫn trước rõ và phần nghỉ không quá rộng.")

def detect_bull_pennant(rows):
    current = rows[-1]["close"]
    recent = rows[-12:]
    prior = rows[-42:-12]
    if len(prior) < 20:
        return None
    prior_move = pct(max(r["close"] for r in prior[-5:]), min(r["close"] for r in prior[:15]))
    first_range = max(r["high"] for r in recent[:6]) - min(r["low"] for r in recent[:6])
    last_range = max(r["high"] for r in recent[-6:]) - min(r["low"] for r in recent[-6:])
    compression = 1 - (last_range / first_range) if first_range > 0 else 0
    recent_high = max(r["high"] for r in recent)
    recent_low = min(r["low"] for r in recent)
    score = 35 + min(prior_move, 30) + clamp(compression * 55, 0, 35) - max(0, pct(recent_high, recent_low) - 14) * 2
    if prior_move < 10:
        score -= 18
    return setup("bull_pennants", "Cờ đuôi nheo tăng", score, recent_high, recent_low, recent_high, current,
                 "Cần thấy biên dao động co lại thay vì chỉ đi ngang rộng.")

def detect_ascending_triangle(rows):
    current = rows[-1]["close"]
    window = rows[-45:]
    highs = [r["high"] for r in window]
    lows = [r["low"] for r in window]
    resistance = sorted(highs)[int(len(highs) * 0.8)]
    high_spread = pct(max(highs[-25:]), min(highs[-25:]))
    low_rise = pct(min(lows[-10:]), min(lows[:15]))
    distance = max(0.0, pct(resistance, current))
    score = 45 + min(max(low_rise, 0), 18) * 1.8 + max(0, 8 - high_spread) * 3 - distance * 1.5
    return setup("triangles_ascending", "Tam giác tăng", score, resistance, min(lows[-20:]), resistance, current,
                 "Cần kháng cự đủ phẳng và đáy sau cao hơn đáy trước.")

def detect_falling_wedge(rows):
    current = rows[-1]["close"]
    window = rows[-40:]
    highs = [r["high"] for r in window]
    lows = [r["low"] for r in window]
    high_slope_v = slope(highs)
    low_slope_v = slope(lows)
    width_start = max(highs[:10]) - min(lows[:10])
    width_end = max(highs[-10:]) - min(lows[-10:])
    narrows = 1 - width_end / width_start if width_start > 0 else 0
    upper_now = highs[0] + high_slope_v * (len(highs) - 1)
    distance = max(0.0, pct(upper_now, current)) if upper_now > 0 else None
    score = 40 + clamp(narrows * 60, 0, 35) + (12 if high_slope_v < 0 and low_slope_v < 0 else -15) - (distance or 0) * 1.2
    return setup("wedges_falling", "Nêm giảm", score, upper_now, min(lows[-15:]), upper_now, current,
                 "Cần hai biên cùng dốc xuống và độ rộng thu hẹp.")

def detect_cup_with_handle(rows):
    if len(rows) < 75:
        return None
    current = rows[-1]["close"]
    window = rows[-90:]
    closes = [r["close"] for r in window]
    left_high = max(closes[:30])
    cup_low = min(closes[20:70])
    right_high = max(closes[55:])
    depth = pct(left_high, cup_low)
    recovery = pct(right_high, cup_low)
    handle = rows[-15:]
    handle_pullback = pct(max(r["high"] for r in handle), min(r["low"] for r in handle))
    confirmation = max(left_high, right_high)
    score = 35 + min(recovery, 35) + max(0, 35 - abs(depth - 25)) - max(0, handle_pullback - 16) * 2
    if depth < 12 or depth > 50:
        score -= 18
    return setup("cup_with_handle", "Cốc tay cầm", score, confirmation,
                 min(r["low"] for r in handle), confirmation, current,
                 "Mẫu dài, dễ nhiễu nếu tay cầm quá sâu hoặc hồi chưa đủ.")

def detect_rectangle_bottom(rows):
    current = rows[-1]["close"]
    window = rows[-35:]
    prior = rows[-75:-35]
    high = max(r["high"] for r in window)
    low = min(r["low"] for r in window)
    range_pct_v = pct(high, low)
    prior_drop = pct(prior[0]["close"], min(r["close"] for r in prior)) if prior else 0
    distance = max(0.0, pct(high, current))
    score = 42 + max(0, 18 - abs(range_pct_v - 12)) * 2 + min(max(prior_drop, 0), 18) - distance
    return setup("rectangle_bottoms", "Chữ nhật đáy", score, high, low, high, current,
                 "Cần vùng đi ngang đủ rõ sau một nhịp giảm hoặc tích lũy.")

def detect_double_bottom(rows):
    current = rows[-1]["close"]
    window = rows[-65:]
    lows = [r["low"] for r in window]
    first_i = min(range(0, 32), key=lambda idx: lows[idx])
    second_i = min(range(32, len(lows)), key=lambda idx: lows[idx])
    first_low = lows[first_i]
    second_low = lows[second_i]
    low_gap = abs(pct(second_low, first_low))
    neckline = max(r["high"] for r in window[first_i:second_i + 1])
    distance = max(0.0, pct(neckline, current))
    separation = second_i - first_i
    score = 48 + max(0, 8 - low_gap) * 4 + min(separation, 30) * 0.5 - distance * 1.5
    if separation < 12:
        score -= 15
    return setup("double_bottoms", "Hai đáy", score, neckline, min(first_low, second_low), neckline, current,
                 "Hai đáy cần tách nhau đủ xa và không lệch quá mạnh.")

def detect_measured_move_up(rows):
    current = rows[-1]["close"]
    first = rows[-70:-35]
    pullback = rows[-35:-12]
    recent = rows[-12:]
    if not first or not pullback:
        return None
    leg_low = min(r["low"] for r in first)
    leg_high = max(r["high"] for r in first)
    leg_move = pct(leg_high, leg_low)
    pull_low = min(r["low"] for r in pullback)
    retrace = (leg_high - pull_low) / (leg_high - leg_low) * 100 if leg_high > leg_low else 100
    confirmation = max(r["high"] for r in recent)
    score = 38 + min(leg_move, 30) + max(0, 30 - abs(retrace - 50)) - max(0, pct(confirmation, current)) * 1.2
    if leg_move < 12 or retrace < 25 or retrace > 75:
        score -= 18
    return setup("measured_move_up", "Measured Move tăng", score, confirmation, pull_low, confirmation, current,
                 "Cần nhịp đầu rõ, pha điều chỉnh vừa phải và chưa bị rơi vào vùng răng cưa.")

DETECTORS = [detect_bull_flag, detect_bull_pennant, detect_ascending_triangle,
             detect_falling_wedge, detect_cup_with_handle, detect_rectangle_bottom,
             detect_double_bottom, detect_measured_move_up]

def scan_setups(rows):
    candidates = [d(rows) for d in DETECTORS]
    candidates = [c for c in candidates if c]
    candidates.sort(key=lambda c: (-float(c["completion_score"]),
                                    float(c.get("distance_to_confirmation_pct") or 999),
                                    c["pattern_name"]))
    return candidates[:6]

CONTINUATION_PATTERNS = {
    "bull_flags", "bull_pennants", "high_tight_flags", "measured_move_up",
    "continuation_gaps", "rising_three_methods",
}
ACCUMULATION_PATTERNS = {
    "triangles_ascending", "triangles_symmetrical", "rectangle_bottoms",
    "cup_with_handle", "double_bottoms_adam_adam", "double_bottoms_adam_eve",
    "double_bottoms_eve_adam", "double_bottoms_eve_eve", "triple_bottoms",
    "pipe_bottoms", "rounding_bottoms",
}
DOWNSIDE_PATTERNS = {
    "bear_flags", "bear_pennants", "triangles_descending", "rectangle_tops",
    "head_and_shoulders_tops", "head_and_shoulders_tops_complex",
    "measured_move_down", "pipe_tops", "horn_tops", "diamond_tops",
    "three_falling_peaks", "triple_tops", "bump_and_run_reversal_tops",
    "falling_three_methods", "cup_with_handle_inverted",
}

def pattern_family(pattern_id):
    if pattern_id in CONTINUATION_PATTERNS:
        return "trend_following"
    if pattern_id in ACCUMULATION_PATTERNS:
        return "accumulation_breakout"
    if pattern_id in DOWNSIDE_PATTERNS:
        return "defensive_caution"
    if "bottom" in pattern_id or "valleys" in pattern_id:
        return "reversal_or_recovery"
    if "top" in pattern_id or "peaks" in pattern_id:
        return "defensive_caution"
    return "mixed"

def estimate_archetype(setups, high_volume_behavior):
    families = [pattern_family(s["pattern_id"]) for s in setups]
    hv_label = high_volume_behavior.get("post_high_volume_label", "") if high_volume_behavior else ""
    if not setups:
        return {"primary": "no_current_setup",
                "reader_note": "Không có setup chiều tăng rõ trong các mẫu heuristic; đọc theo từng phiên."}
    if "trend_following" in families:
        return {"primary": "trend_following",
                "reader_note": "Setup hiện tại nghiêng tiếp diễn; đọc ưu tiên theo sức giữ xu hướng."}
    if "accumulation_breakout" in families:
        return {"primary": "accumulation_breakout",
                "reader_note": "Setup hiện tại nghiêng tích lũy; đọc kỹ ở phiên xác nhận thoát nền."}
    if "suy yếu" in hv_label:
        return {"primary": "trap_prone",
                "reader_note": "Hành vi sau volume cao suy yếu; thận trọng với phá vỡ giả."}
    return {"primary": "mixed",
            "reader_note": "Setup hiện tại pha trộn; đọc theo từng cấu trúc cụ thể."}

# =============================================================================
# MAIN
# =============================================================================

def main():
    overview = load_overview(os.path.join(DATA_DIR, "overview.json"))

    # ---- ACTIVE mode: weekly ----
    weekly_ctd = load_csv(os.path.join(DATA_DIR, "price_weekly_52w.csv"))
    weekly_vni = load_csv(os.path.join(DATA_DIR, "price_weekly_vnindex.csv"))
    weekly_vn30 = load_csv(os.path.join(DATA_DIR, "price_weekly_vn30.csv"))

    closes = [r["close"] for r in weekly_ctd]
    last_row = weekly_ctd[-1]
    current_close_raw = last_row["close"]  # thousands VND
    current_close_vnd = current_close_raw * 1000.0
    first_close = weekly_ctd[0]["close"]
    perf_1y_pct = round_((current_close_raw/first_close - 1) * 100)

    # 52W high/low from overview.json (already VND); also compute from weekly closes
    high_52w_vnd = overview.get("highest_price1_year")  # VND
    low_52w_vnd = overview.get("lowest_price1_year")    # VND
    high_52w_raw = high_52w_vnd / 1000.0 if high_52w_vnd else None
    low_52w_raw = low_52w_vnd / 1000.0 if low_52w_vnd else None

    # Indicators (use raw thousands-VND closes; ratios unaffected by unit)
    ma10 = SMA(closes, 10); ma20 = SMA(closes, 20); ma50 = SMA(closes, 50)
    rsi = RSI(closes, 14)
    ema12 = EMA(closes, 12); ema26 = EMA(closes, 26)
    macd_line = [ema12[i] - ema26[i] for i in range(len(closes))]
    signal_line = EMA(macd_line, 9)
    bb = Bollinger(closes, 20, 2)
    last_idx = len(closes) - 1

    ma10_last = ma10[last_idx]; ma20_last = ma20[last_idx]; ma50_last = ma50[last_idx]
    rsi_last = rsi[last_idx]
    macd_last = macd_line[last_idx]; signal_last = signal_line[last_idx]
    bb_last = bb[last_idx]
    bb_pos = None
    if bb_last and bb_last["upper"] is not None and bb_last["lower"] is not None and bb_last["upper"] != bb_last["lower"]:
        bb_pos = (current_close_raw - bb_last["lower"]) / (bb_last["upper"] - bb_last["lower"]) * 100

    # Beta/Correlation vs VNINDEX + VN30 (weekly returns)
    vni_closes = [r["close"] for r in weekly_vni]
    vn30_closes = [r["close"] for r in weekly_vn30]
    # align lengths (they should all be 57)
    n = min(len(closes), len(vni_closes), len(vn30_closes))
    cs = closes[-n:]; vnis = vni_closes[-n:]; vn30s = vn30_closes[-n:]
    sr = weekly_returns(cs); vr = weekly_returns(vnis); v30r = weekly_returns(vn30s)
    beta_vni = beta(sr, vr)
    beta_vn30 = beta(sr, v30r)
    corr_vni = corr(sr, vr)
    corr_vn30 = corr(sr, v30r)
    stock_perf_1y = (cs[-1]/cs[0] - 1) * 100
    vni_perf_1y = (vnis[-1]/vnis[0] - 1) * 100
    alpha_1y = stock_perf_1y - (beta_vni or 0) * vni_perf_1y

    # Tech score (6 signals)
    sig_ma10 = 1 if current_close_raw > ma10_last else -1
    sig_ma20 = 1 if current_close_raw > ma20_last else -1
    sig_ma50 = 1 if current_close_raw > ma50_last else -1
    sig_rsi = 1 if (rsi_last or 0) > 55 else (-1 if (rsi_last or 0) < 45 else 0)
    sig_macd = 1 if macd_last > signal_last else -1
    sig_bb = 1 if (bb_pos or 0) > 50 else (-1 if (bb_pos or 0) < 50 else 0)
    tech_score = sig_ma10 + sig_ma20 + sig_ma50 + sig_rsi + sig_macd + sig_bb

    if tech_score >= 4:
        verdict = "STRONG BUY"
    elif tech_score >= 1:
        verdict = "BUY"
    elif tech_score <= -4:
        verdict = "STRONG SELL"
    elif tech_score <= -2:
        verdict = "SELL/REDUCE"
    else:
        verdict = "HOLD/NEUTRAL"

    # Patterns (evidence-only)
    swings = findSwings(closes, lookback=2)
    double_bottoms = detectDoubleBottom(closes, swings["lows"])
    channel = detectChannel(closes, lookback=20)

    # Candlestick patterns on last 8 weeks
    candle_patterns = []
    for r in weekly_ctd[-8:]:
        cps = analyzeCandle(r)
        for cp in cps:
            candle_patterns.append({"date": r["date"], "type": cp["name"], "signal": cp["signal"]})

    engulfing = detectEngulfing(weekly_ctd[-12:])
    three = detectThreeSoldiers(weekly_ctd[-3:])

    patterns_detected = []
    for db in double_bottoms:
        b1_date = weekly_ctd[db["bottom1_idx"]]["date"] if db["bottom1_idx"] < len(weekly_ctd) else None
        b2_date = weekly_ctd[db["bottom2_idx"]]["date"] if db["bottom2_idx"] < len(weekly_ctd) else None
        patterns_detected.append({
            "type": "double_bottom",
            "status": db["status"],
            "bottom1_date": b1_date, "bottom1_price_vnd": round(db["bottom1_price"]*1000),
            "bottom2_date": b2_date, "bottom2_price_vnd": round(db["bottom2_price"]*1000),
            "price_diff_pct": db["price_diff_pct"],
            "neckline_vnd": round(db["neckline"]*1000),
            "target_vnd": round(db["target"]*1000),
            "weeks_apart": db["weeks_apart"],
        })
    if channel:
        patterns_detected.append({
            "type": channel["type"],
            "status": "active",
            "trend": channel["trend"],
            "high_start_vnd": round(channel["high_start"]*1000),
            "high_end_vnd": round(channel["high_end"]*1000),
            "low_start_vnd": round(channel["low_start"]*1000),
            "low_end_vnd": round(channel["low_end"]*1000),
        })
    for cp in candle_patterns:
        patterns_detected.append({"type": cp["type"], "date": cp["date"], "signal": cp["signal"]})
    for eg in engulfing:
        patterns_detected.append({"type": eg["type"], "date": eg["date"], "signal": eg["signal"]})
    if three:
        patterns_detected.append({"type": three["type"], "signal": three["signal"]})

    # Divergence (honest)
    weekly_dates = [r["date"] for r in weekly_ctd]
    divergence = checkDivergence(closes, rsi, swings["lows"], dates=weekly_dates)

    # Support / Resistance
    support_resistance = {
        "resistance": [
            {"level": "R1", "price_vnd": round(high_52w_raw*1000) if high_52w_raw else None, "note": "52W high (overview.json)"},
            {"level": "R2", "price_vnd": round(ma50_last*1000) if ma50_last else None, "note": "MA50 weekly"},
        ],
        "support": [
            {"level": "S1", "price_vnd": round(ma10_last*1000) if ma10_last else None, "note": "MA10 weekly"},
            {"level": "S2", "price_vnd": round(low_52w_raw*1000) if low_52w_raw else None, "note": "52W low (overview.json)"},
        ],
    }

    # Trading strategy 3 scenarios
    strategy = {
        "scenario_bullish": {
            "trigger": f"Giá đóng cửa tuần vượt MA20 ({round(ma20_last*1000):,.0f} VND) với volume tăng, MACD cắt lên Signal",
            "action": "Tích lũy",
            "target": f"Vùng neckline / 52W high {round(high_52w_raw*1000):,.0f} VND" if high_52w_raw else "n/a",
            "stop_loss": f"Dưới MA10 {round(ma10_last*1000):,.0f} VND" if ma10_last else "n/a",
        },
        "scenario_neutral": {
            "trigger": f"Giá dao động quanh MA10/MA20 ({round(ma10_last*1000):,.0f}-{round(ma20_last*1000):,.0f} VND), RSI 45-55",
            "action": "Quan sát / giữ vị thế hiện có",
            "range": f"{round(low_52w_raw*1000):,.0f} - {round(high_52w_raw*1000):,.0f} VND" if high_52w_raw and low_52w_raw else "n/a",
        },
        "scenario_bearish": {
            "trigger": f"Giá mất MA50 ({round(ma50_last*1000):,.0f} VND), MACD nới rộng dưới Signal, volume bán tăng",
            "action": "Hạn chế / cắt lỗ",
            "support": f"52W low {round(low_52w_raw*1000):,.0f} VND" if low_52w_raw else "n/a",
        },
        "cyclical_note": "CTD là cổ phiếu ngành xây dựng (chu kỳ). Score bearish không tự động = bán; kết hợp fundamental (đơn hàng, biên lợi nhuận) trước khi quyết.",
    }

    active_json = {
        "schema": "vn-technical-active-v1",
        "ticker": "CTD",
        "company_name": overview.get("organ_short_name"),
        "sector": overview.get("sector"),
        "exchange": "HOSE",
        "data_source": "vnstock (VCI) — files provided",
        "data_period": f"{weekly_ctd[0]['date']} to {weekly_ctd[-1]['date']}",
        "weekly_observations": len(weekly_ctd),
        "price_current_vnd": round(current_close_vnd),
        "overview_current_price_vnd": overview.get("current_price"),
        "price_unit_note": "vnstock prices in thousands VND; *_vnd fields = raw * 1000",
        "performance_1y_pct": perf_1y_pct,
        "high_52w_vnd": round(high_52w_vnd) if high_52w_vnd else None,
        "low_52w_vnd": round(low_52w_vnd) if low_52w_vnd else None,
        "indicators": {
            "ma10_vnd": round(ma10_last*1000) if ma10_last else None,
            "ma20_vnd": round(ma20_last*1000) if ma20_last else None,
            "ma50_vnd": round(ma50_last*1000) if ma50_last else None,
            "rsi14": round_(rsi_last, 2),
            "macd": round_(macd_last, 4),
            "signal": round_(signal_last, 4),
            "macd_trend": "bullish" if macd_last > signal_last else "bearish",
            "macd_histogram": round_(macd_last - signal_last, 4),
            "bb_upper_vnd": round(bb_last["upper"]*1000) if bb_last and bb_last["upper"] else None,
            "bb_middle_vnd": round(bb_last["middle"]*1000) if bb_last and bb_last["middle"] else None,
            "bb_lower_vnd": round(bb_last["lower"]*1000) if bb_last and bb_last["lower"] else None,
            "bb_position_pct": round_(bb_pos, 2),
            "price_vs_ma10": "above" if current_close_raw > ma10_last else "below",
            "price_vs_ma20": "above" if current_close_raw > ma20_last else "below",
            "price_vs_ma50": "above" if current_close_raw > ma50_last else "below",
        },
        "correlation": {
            "beta_vnindex": round_(beta_vni, 4),
            "beta_vn30": round_(beta_vn30, 4),
            "corr_vnindex": round_(corr_vni, 4),
            "corr_vn30": round_(corr_vn30, 4),
            "alpha_1y_pct": round_(alpha_1y, 2),
            "stock_perf_1y_pct": round_(stock_perf_1y, 2),
            "vnindex_perf_1y_pct": round_(vni_perf_1y, 2),
            "outperform_market": stock_perf_1y > vni_perf_1y,
            "alignment_weeks": n,
        },
        "patterns_detected": patterns_detected,
        "divergence": divergence,
        "tech_score": tech_score,
        "tech_score_breakdown": {
            "price_vs_ma10": sig_ma10,
            "price_vs_ma20": sig_ma20,
            "price_vs_ma50": sig_ma50,
            "rsi_signal": sig_rsi,
            "macd_vs_signal": sig_macd,
            "bb_position": sig_bb,
        },
        "verdict": verdict,
        "support_resistance": support_resistance,
        "trading_strategy": strategy,
        "transparency": {
            "data_source": "vnstock (VCI) weekly OHLCV + overview.json",
            "patterns_evidence_only": "Chỉ flag patterns khi data show rõ; không tự tạo.",
            "known_limitations": "52W high/low lấy từ overview.json (snapshot). Tuần cuối có thể chưa kết thúc.",
        },
    }

    with open(os.path.join(DATA_DIR, "technical_active.json"), "w") as f:
        json.dump(active_json, f, ensure_ascii=False, indent=2)

    # ---- PROFILE mode: daily ----
    daily_ctd = load_csv(os.path.join(DATA_DIR, "price_daily_ctd.csv"))
    daily_vni = load_csv(os.path.join(DATA_DIR, "price_daily_vnindex.csv"))
    daily_vn30 = load_csv(os.path.join(DATA_DIR, "price_daily_vn30.csv"))

    benchmarks = {"VNINDEX": daily_vni, "VN30": daily_vn30}

    profile = {
        "schema": "vn-technical-profile-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "language_policy": "neutral_descriptive_non_advice",
        "symbol": "CTD",
        "stock_identity": {
            "symbol": "CTD",
            "company_name": overview.get("organ_short_name"),
            "sector": overview.get("sector"),
            "exchange": "HOSE",
            "sample_size": len(daily_ctd),
            "data_period": f"{daily_ctd[0]['date']} to {daily_ctd[-1]['date']}",
        },
        "price_behavior_profile": price_behavior_profile(daily_ctd),
        "volatility_profile": volatility_profile(daily_ctd),
        "drawdown_profile": drawdown_profile(daily_ctd),
        "liquidity_profile": liquidity_profile(daily_ctd),
        "return_distribution_profile": return_distribution_profile(daily_ctd),
        "tail_risk_profile": tail_risk_profile(daily_ctd),
        "liquidity_risk_profile": liquidity_risk_profile(daily_ctd),
        "volume_price_profile": volume_price_profile(daily_ctd),
        "volume_price_confirmation_profile": vpci_profile(daily_ctd),
        "money_flow_pressure_profile": money_flow_profile(daily_ctd),
        "effort_result_profile": effort_result_profile(daily_ctd),
        "high_volume_behavior_profile": high_volume_behavior_profile(daily_ctd),
        "pvi_nvi_participation_profile": pvi_nvi_profile(daily_ctd),
        "volume_at_price_profile": volume_at_price_profile(daily_ctd),
    }

    rs = relative_strength_profile(daily_ctd, daily_vni, benchmarks)
    profile.update(rs)
    profile["regime_profile"] = regime_profile(daily_ctd, daily_vni)

    # Setups + archetype
    setups = scan_setups(daily_ctd)
    profile["setups"] = setups
    profile["archetype"] = estimate_archetype(setups, profile["high_volume_behavior_profile"])

    # Non-conclusion (mandatory, points 1+2 always)
    profile["non_conclusion"] = [
        "Không kết luận đây là lời gọi giao dịch hoặc lời gọi mua bán.",
        "Tỷ lệ trong quá khứ không đảm bảo lặp lại trong tương lai.",
        "Các cửa sổ quan sát chồng lấp, không phải quan sát độc lập.",
        "Dữ liệu giá chưa điều chỉnh corporate actions được kiểm chứng đầy đủ.",
    ]

    profile["data_transparency"] = {
        "data_source": "vnstock (VCI) daily OHLCV",
        "price_unit": "thousands VND (close * 1000 = VND); value field = VND",
        "blocks_computed": 15,
        "setups_computed": 8,
        "industry_peer_profile": "skipped — no peer sector data provided",
    }

    with open(os.path.join(DATA_DIR, "technical_profile.json"), "w") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    # ---- Summary to stdout ----
    print("=" * 70)
    print("CTD TECHNICAL ANALYSIS — SUMMARY")
    print("=" * 70)
    print("\n[MODE 4a — ACTIVE]")
    print(f"  Data period      : {weekly_ctd[0]['date']} -> {weekly_ctd[-1]['date']} ({len(weekly_ctd)} weeks)")
    print(f"  Current price    : {current_close_vnd:,.0f} VND (weekly close)")
    print(f"  Overview price   : {overview.get('current_price'):,.0f} VND")
    print(f"  Perf 1Y          : {perf_1y_pct}%")
    print(f"  52W high/low     : {high_52w_vnd:,.0f} / {low_52w_vnd:,.0f} VND")
    print(f"  MA10/20/50       : {ma10_last*1000:,.0f} / {ma20_last*1000:,.0f} / {ma50_last*1000:,.0f} VND")
    print(f"  RSI(14)          : {round_(rsi_last,2)}")
    print(f"  MACD/Signal      : {round_(macd_last,4)} / {round_(signal_last,4)} ({'bullish' if macd_last>signal_last else 'bearish'})")
    print(f"  BB position      : {round_(bb_pos,2)}%")
    print(f"  Beta VNINDEX/VN30: {round_(beta_vni,4)} / {round_(beta_vn30,4)}")
    print(f"  Corr VNI/VN30    : {round_(corr_vni,4)} / {round_(corr_vn30,4)}")
    print(f"  Alpha 1Y         : {round_(alpha_1y,2)}% (stock {round_(stock_perf_1y,2)}% vs VNI {round_(vni_perf_1y,2)}%)")
    print(f"  Tech score       : {tech_score}  ->  {verdict}")
    print(f"  Score breakdown  : MA10={sig_ma10} MA20={sig_ma20} MA50={sig_ma50} RSI={sig_rsi} MACD={sig_macd} BB={sig_bb}")
    print(f"  Patterns detected: {len(patterns_detected)}")
    for p in patterns_detected:
        print(f"    - {p}")
    print(f"  Divergence       : {divergence['has_divergence']} ({divergence['note']})")

    print("\n[MODE 4b — PROFILE]")
    print(f"  Data period      : {daily_ctd[0]['date']} -> {daily_ctd[-1]['date']} ({len(daily_ctd)} days)")
    print(f"  Archetype        : {profile['archetype']['primary']}")
    print(f"    note           : {profile['archetype']['reader_note']}")
    print(f"  Setups (top)     : {len(setups)}")
    for s in setups:
        print(f"    - {s['pattern_name']} ({s['pattern_id']}): score={s['completion_score']}, status={s['setup_status']}, dist={s['distance_to_confirmation_pct']}%")
    # Key profile metrics
    pb = profile["price_behavior_profile"]
    vol = profile["volatility_profile"]
    dd = profile["drawdown_profile"]
    liq = profile["liquidity_profile"]
    vpci = profile["volume_price_confirmation_profile"]
    mf = profile["money_flow_pressure_profile"]
    er = profile["effort_result_profile"]
    hvb = profile["high_volume_behavior_profile"]
    pvi = profile["pvi_nvi_participation_profile"]
    vap = profile["volume_at_price_profile"]
    rs252 = profile["relative_strength_profile"]["comparisons"][0]["metrics"]["252"]
    reg = profile["regime_profile"]
    print(f"  Return 1M/3M/1Y  : {pb['return_1m_pct']}% / {pb['return_3m_pct']}% / {pb['return_1y_pct']}%")
    print(f"  HV20/60/120/252  : {vol['hv20_pct']}% / {vol['hv60_pct']}% / {vol['hv120_pct']}% / {vol['hv252_pct']}%")
    print(f"  Current drawdown : {dd['current_drawdown_pct']}% (max {dd['max_drawdown_pct']}%, underwater {dd['current_underwater_days']}d)")
    print(f"  Latest value     : {liq['latest_value']:,.0f} VND (pctile {liq['latest_value_percentile_1y']}% 1Y)")
    print(f"  VPCI latest      : {round_(vpci['vpci_latest'],6)} | {vpci['confirmation_label']}")
    print(f"  CMF 20/60        : {mf['cmf_20d']} / {mf['cmf_60d']} | {mf['money_flow_label']}")
    print(f"  Effort-result    : {er['effort_result_label']} (high-effort days 1Y: {er['high_effort_days_1y']})")
    print(f"  High-vol behavior: {hvb['post_high_volume_label']} (events 1Y: {hvb['event_count_1y']})")
    print(f"  PVI/NVI          : {pvi['participation_regime_label']} (ratio {pvi['pvi_nvi_ratio']})")
    print(f"  VAP acceptance   : {vap['acceptance_label']} (POC bin {vap['point_of_control_bin_index']})")
    if rs252:
        print(f"  vs VNINDEX 252d  : beta={rs252['beta']}, corr={rs252['correlation']}, R2={rs252['r2']}, relative={rs252['relative_return_pct']}%")
    print(f"  Market regime    : {reg['current_market_regime']}")
    print(f"  Non-conclusion   : {len(profile['non_conclusion'])} points")

    print("\n[FILES WRITTEN]")
    print(f"  {DATA_DIR}/technical_active.json")
    print(f"  {DATA_DIR}/technical_profile.json")

if __name__ == "__main__":
    main()
