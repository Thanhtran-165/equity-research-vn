#!/usr/bin/env python3
"""
KDH Technical Analysis — BOTH modes (skill vn-technical-analysis).
Data source: vnstock (VCI) CSVs already fetched into /Users/bobo/ZCodeProject/kdh_data/.
Price unit: vnstock prices in THOUSANDS VND (close=21.0 = 21,000 VND).

Mode ACTIVE  -> technical_active.json  (weekly, MA/RSI/MACD/BB/Beta, Tech Score -6..+6, Verdict, patterns, strategy)
Mode PROFILE -> technical_profile.json (daily ~530d, 15 blocks, archetype, neutral_descriptive_non_advice)
"""
import csv, json, math, os, re
from datetime import datetime, timezone

DATA = "/Users/bobo/ZCodeProject/kdh_data"

# ----------------------------- IO helpers -----------------------------
def load_csv(path):
    """Return list of dict {date, open, high, low, close, volume} (floats, date str)."""
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            t = r.get("time") or r.get("date")
            if not t:
                continue
            try:
                rows.append({
                    "date": t[:10],
                    "open": float(r["open"]), "high": float(r["high"]),
                    "low": float(r["low"]),  "close": float(r["close"]),
                    "volume": float(r["volume"]),
                })
            except (ValueError, KeyError):
                continue
    rows.sort(key=lambda x: x["date"])
    return rows

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
    if len(nums) < 2: return None
    avg = mean(nums)
    return math.sqrt(sum((v-avg)**2 for v in nums) / (len(nums)-1))

def skewness(values=[]):
    nums = [v for v in values if finite(v)]
    if len(nums) < 3: return None
    avg, sd = mean(nums), std_dev(nums)
    if not sd: return None
    n = len(nums)
    return (n / ((n-1)*(n-2))) * sum(((v-avg)/sd)**3 for v in nums)

def excess_kurtosis(values=[]):
    nums = [v for v in values if finite(v)]
    if len(nums) < 4: return None
    avg, sd = mean(nums), std_dev(nums)
    if not sd: return None
    n = len(nums)
    z4 = sum(((v-avg)/sd)**4 for v in nums)
    return ((n*(n+1)) / ((n-1)*(n-2)*(n-3))) * z4 - (3*(n-1)**2)/((n-2)*(n-3))

def quantile(values, q):
    nums = sorted(v for v in values if finite(v))
    if not nums: return None
    if len(nums) == 1: return nums[0]
    pos = q * (len(nums) - 1)
    lo = math.floor(pos); hi = math.ceil(pos)
    if lo == hi: return nums[lo]
    return nums[lo] + (nums[hi] - nums[lo]) * (pos - lo)

def median(values=[]):
    return quantile(values, 0.5)

def percentile_of_value(values, value):
    nums = [v for v in values if finite(v)]
    if not nums or not finite(value): return None
    return round_(sum(1 for v in nums if v <= value) / len(nums) * 100)

# ----------------------------- indicator math (shared) -----------------------------
def SMA(d, p):
    out = [None]*(p-1)
    for i in range(p-1, len(d)):
        out.append(sum(d[i-p+1:i+1]) / p)
    return out

def EMA(d, p):
    if not d: return []
    k = 2 / (p + 1)
    o = [d[0]]
    for i in range(1, len(d)):
        o.append(d[i]*k + o[i-1]*(1-k))
    return o

def RSI(d, period=14):
    rs = [None]*len(d)
    if len(d) <= period: return rs
    ag = 0; al = 0
    for i in range(1, period+1):
        ch = d[i]-d[i-1]
        if ch > 0: ag += ch
        else: al += abs(ch)
    ag /= period; al /= period
    rs[period] = 100 if al == 0 else 100 - 100/(1 + ag/al)
    for i in range(period+1, len(d)):
        ch = d[i]-d[i-1]
        ag = (ag*(period-1) + (ch if ch > 0 else 0)) / period
        al = (al*(period-1) + (abs(ch) if ch < 0 else 0)) / period
        rs[i] = 100 if al == 0 else 100 - 100/(1 + ag/al)
    return rs

def bollinger(d, period=20, mult=2):
    sma = SMA(d, period)
    out = []
    for i in range(len(d)):
        if i < period-1:
            out.append({"upper": None, "middle": None, "lower": None})
            continue
        sl = d[i-period+1:i+1]
        m = sma[i]
        var = sum((v-m)**2 for v in sl)/period
        sd = math.sqrt(var)
        out.append({"upper": m + mult*sd, "middle": m, "lower": m - mult*sd})
    return out

def weekly_returns(closes):
    return [(closes[i]/closes[i-1]-1)*100 for i in range(1, len(closes))]

def corr(a, b):
    ma, mb = sum(a)/len(a), sum(b)/len(b)
    ca = [x-ma for x in a]; cb = [x-mb for x in b]
    den = (sum(x*x for x in ca)**0.5) * (sum(y*y for y in cb)**0.5)
    return sum(x*y for x, y in zip(ca, cb))/den if den else 0

def beta(stock, market):
    ms, mm = sum(stock)/len(stock), sum(market)/len(market)
    cs = [x-ms for x in stock]; cm = [x-mm for x in market]
    cov = sum(x*y for x, y in zip(cs, cm)) / len(stock)
    var = sum(x*x for x in cm) / len(market)
    return cov/var if var else 0

# ----------------------------- pattern detection (ACTIVE) -----------------------------
def find_swings(closes, lookback=2):
    highs, lows = [], []
    for i in range(lookback, len(closes)-lookback):
        isH = isL = True
        for j in range(1, lookback+1):
            if closes[i] <= closes[i-j] or closes[i] <= closes[i+j]: isH = False
            if closes[i] >= closes[i-j] or closes[i] >= closes[i+j]: isL = False
        if isH: highs.append({"idx": i, "price": closes[i]})
        if isL: lows.append({"idx": i, "price": closes[i]})
    return {"highs": highs, "lows": lows}

def detect_double_bottom_weekly(closes, lows):
    pats = []
    latest = closes[-1]
    for i in range(len(lows)-1):
        for j in range(i+1, len(lows)):
            l1, l2 = lows[i], lows[j]
            diff = abs(l1["price"]-l2["price"]) / min(l1["price"], l2["price"]) * 100
            weeks = l2["idx"] - l1["idx"]
            if diff < 3 and weeks >= 5:
                between = closes[l1["idx"]:l2["idx"]+1]
                neck = max(between)
                # Honest status per skill: potential only if price still above
                # bottom2 ( neckline breakout -> confirmed; break below bottom2 -> failed )
                floor = min(l1["price"], l2["price"])
                if latest < floor:
                    status = "failed"
                    note = f"Giá hiện tại {latest:.2f} đã break dưới đáy {floor:.2f} — pattern thất bại"
                elif latest > neck:
                    status = "confirmed"
                    note = f"Giá đã breakout trên neckline {neck:.2f}"
                else:
                    status = "potential"
                    note = "Chưa breakout neckline, chưa confirm"
                pats.append({
                    "type": "double_bottom",
                    "bottom1_week": l1["idx"], "bottom2_week": l2["idx"],
                    "bottom1_price": l1["price"], "bottom2_price": l2["price"],
                    "neckline": neck,
                    "target": neck + (neck - floor),
                    "status": status,
                    "status_note": note,
                    "weeks_apart": weeks,
                    "price_diff_pct": round_(diff, 2),
                    "current_price": latest,
                })
    # keep most recent / deepest
    if pats:
        pats.sort(key=lambda p: p["weeks_apart"], reverse=True)
        return pats[0]
    return None

def detect_channel(closes, lookback=20):
    recent = closes[-lookback:]
    third = math.floor(lookback/3)
    firstHigh = max(recent[:third]); lastHigh = max(recent[-third:])
    firstLow = min(recent[:third]); lastLow = min(recent[-third:])
    hs = lastHigh - firstHigh; ls = lastLow - firstLow
    # threshold ~3% of mid price
    mid = (firstHigh + lastHigh)/2 if (firstHigh+lastHigh) else 0
    thr = mid * 0.03 if mid else 0.5
    if hs < -thr and ls < -thr:
        return {"type": "descending_channel", "trend": "bearish",
                "high_start": firstHigh, "high_end": lastHigh,
                "low_start": firstLow, "low_end": lastLow}
    if hs > thr and ls > thr:
        return {"type": "ascending_channel", "trend": "bullish",
                "high_start": firstHigh, "high_end": lastHigh,
                "low_start": firstLow, "low_end": lastLow}
    if abs(hs) < thr and abs(ls) < thr:
        return {"type": "trading_range", "trend": "neutral"}
    return None

def analyze_candle(c):
    body = abs(c["close"]-c["open"])
    upper = c["high"] - max(c["close"], c["open"])
    lower = min(c["close"], c["open"]) - c["low"]
    rng = c["high"]-c["low"]
    pct_body = body/rng*100 if rng > 0 else 0
    isUp = c["close"] >= c["open"]
    pats = []
    if lower > body*2 and pct_body < 35 and not isUp:
        pats.append({"name": "hammer", "signal": "bullish_reversal"})
    if lower > body*2 and pct_body < 35 and isUp:
        pats.append({"name": "inverted_hammer", "signal": "bullish_reversal"})
    if upper > body*2 and pct_body < 35:
        pats.append({"name": "shooting_star", "signal": "bearish"})
    if pct_body > 70:
        pats.append({"name": "marubozu_bullish" if isUp else "marubozu_bearish",
                     "signal": "bullish_momentum" if isUp else "bearish_momentum"})
    if pct_body < 10:
        pats.append({"name": "doji", "signal": "indecision"})
    return pats

def detect_engulfing(candles):
    pats = []
    for i in range(1, len(candles)):
        p, c = candles[i-1], candles[i]
        pUp = p["close"] >= p["open"]; cUp = c["close"] >= c["open"]
        if not pUp and cUp and c["close"] > p["open"] and c["open"] < p["close"]:
            pats.append({"idx": i, "type": "bullish_engulfing", "signal": "bullish_strong"})
        if pUp and not cUp and c["close"] < p["open"] and c["open"] > p["close"]:
            pats.append({"idx": i, "type": "bearish_engulfing", "signal": "bearish_strong"})
    return pats

def check_divergence(closes, rsi, swing_lows, dates):
    if len(swing_lows) < 2:
        return {"has_divergence": False, "note": "Không đủ swing lows"}
    l1 = swing_lows[-2]; l2 = swing_lows[-1]
    # RSI array same length as closes (nulls for first 14)
    rsi1 = rsi[l1["idx"]]; rsi2 = rsi[l2["idx"]]
    if rsi1 is None or rsi2 is None:
        return {"has_divergence": False, "note": "RSI chưa xác định tại đáy"}
    price_change = l1["price"] - l2["price"]   # + = giá giảm
    rsi_change = rsi1 - rsi2                    # + = RSI giảm
    d1 = dates[l1["idx"]]; d2 = dates[l2["idx"]]
    if price_change > 0 and rsi_change < 0:
        return {"has_divergence": True, "type": "bullish",
                "note": f"Giá giảm {l1['price']:.2f} ({d1}) → {l2['price']:.2f} ({d2}) nhưng RSI tăng {rsi1:.1f} → {rsi2:.1f}"}
    if price_change < 0 and rsi_change > 0:
        return {"has_divergence": True, "type": "bearish",
                "note": f"Giá tăng {l1['price']:.2f} ({d1}) → {l2['price']:.2f} ({d2}) nhưng RSI giảm {rsi1:.1f} → {rsi2:.1f}"}
    pdir = "giảm" if price_change > 0 else ("tăng" if price_change < 0 else "đi ngang")
    rdir = "giảm" if rsi_change > 0 else ("tăng" if rsi_change < 0 else "đi ngang")
    return {"has_divergence": False,
            "note": f"Giá và RSI cùng hướng ở 2 đáy gần nhất (Δ giá: {pdir}, Δ RSI: {rdir}) — không có divergence"}

# =====================================================================
# MODE ACTIVE
# =====================================================================
def run_active():
    w = load_csv(f"{DATA}/price_weekly_52w.csv")
    wvni = load_csv(f"{DATA}/price_weekly_vnindex.csv")
    wvn30 = load_csv(f"{DATA}/price_weekly_vn30.csv")
    overview = json.load(open(f"{DATA}/overview.json"))

    closes = [r["close"] for r in w]
    dates = [r["date"] for r in w]
    n = len(closes)
    latest = closes[-1]
    latest_date = dates[-1]

    # MAs (weekly periods 10/20/50)
    ma10 = SMA(closes, 10); ma20 = SMA(closes, 20); ma50 = SMA(closes, 50)
    ma10_v = ma10[-1]; ma20_v = ma20[-1]; ma50_v = ma50[-1]

    rsi = RSI(closes, 14)
    rsi_v = rsi[-1]

    ema12 = EMA(closes, 12); ema26 = EMA(closes, 26)
    macd_line = [ema12[i]-ema26[i] for i in range(len(closes))]
    signal_line = EMA(macd_line, 9)
    macd_v = macd_line[-1]; signal_v = signal_line[-1]
    hist = macd_v - signal_v
    macd_trend = "bullish" if macd_v > signal_v else "bearish"

    bb = bollinger(closes, 20, 2)
    bb_last = bb[-1]
    bb_pos = (latest - bb_last["lower"])/(bb_last["upper"]-bb_last["lower"])*100 if (bb_last["upper"] and bb_last["upper"] != bb_last["lower"]) else None

    # 52w stats (full weekly sample = 57 weeks ~ covers 52w)
    high_52w = max(closes); low_52w = min(closes)
    perf_1y = (closes[-1]/closes[0]-1)*100
    # annualized vol from weekly returns
    rets = weekly_returns(closes)
    wk_vol = std_dev(rets)
    ann_vol = wk_vol * math.sqrt(52) if wk_vol else None

    # Beta / Correlation vs VNINDEX & VN30 (weekly returns, paired by date)
    def paired_ret(stock_rows, idx_rows):
        by = {r["date"]: r["close"] for r in idx_rows}
        sr, ir, pair_dates = [], [], []
        prev_s = None
        for r in stock_rows:
            d = r["date"]
            if d in by and prev_s is not None:
                sr.append(r["close"]/prev_s - 1)
                ir.append(by[d]/prev_idx - 1 if (prev_idx:=None) is not None else 0)
            # need previous index close too
        return sr, ir
    # simpler: build date->close maps for indices, iterate stock weeks
    def weekly_rets_paired(stock_rows, idx_rows):
        idx_by = {r["date"]: r["close"] for r in idx_rows}
        s_prev = None; i_prev = None
        sr, ir = [], []
        for r in stock_rows:
            d = r["date"]; ic = idx_by.get(d)
            if s_prev is not None and ic is not None and i_prev is not None:
                sr.append(r["close"]/s_prev - 1)
                ir.append(ic/i_prev - 1)
            s_prev = r["close"]
            if ic is not None: i_prev = ic
        return sr, ir
    sr_vni, ir_vni = weekly_rets_paired(w, wvni)
    sr_vn30, ir_vn30 = weekly_rets_paired(w, wvn30)
    beta_vni = beta(sr_vni, ir_vni) if len(sr_vni) > 5 else None
    beta_vn30 = beta(sr_vn30, ir_vn30) if len(sr_vn30) > 5 else None
    corr_vni = corr(sr_vni, ir_vni) if len(sr_vni) > 5 else None
    corr_vn30 = corr(sr_vn30, ir_vn30) if len(sr_vn30) > 5 else None
    # alpha 1y = stock perf - beta*market perf (use cumulative weekly)
    stock_cum = (closes[-1]/closes[0]-1)
    vni_by = {r["date"]: r["close"] for r in wvni}
    # find first & last paired index close
    vni_first = next((vni_by[r["date"]] for r in w if r["date"] in vni_by), None)
    vni_last = vni_by.get(latest_date) or next((vni_by[r["date"]] for r in reversed(w) if r["date"] in vni_by), None)
    vni_cum = (vni_last/vni_first - 1) if (vni_first and vni_last) else None
    alpha_1y = (stock_cum - beta_vni*vni_cum)*100 if (beta_vni is not None and vni_cum is not None) else None

    # ---- Patterns ----
    swings = find_swings(closes, 2)
    db = detect_double_bottom_weekly(closes, swings["lows"])
    ch = detect_channel(closes, 20)

    # candlesticks on last 8 weeks
    candle_pats = []
    for r in w[-8:]:
        for p in analyze_candle(r):
            candle_pats.append({"date": r["date"], **p,
                                "open": r["open"], "close": r["close"],
                                "high": r["high"], "low": r["low"]})
    # engulfing on last 8
    eng = detect_engulfing(w[-8:])
    eng_out = [{"week_index_from_end": len(w)-1-e["idx"]+ (n-8),
                "type": e["type"], "signal": e["signal"]} for e in eng]

    div = check_divergence(closes, rsi, swings["lows"], dates)

    patterns_detected = []
    if db:
        patterns_detected.append({
            "type": "double_bottom", "status": db["status"],
            "status_note": db.get("status_note"),
            "bottom1_price": db["bottom1_price"], "bottom2_price": db["bottom2_price"],
            "neckline": db["neckline"], "target": db["target"],
            "weeks_apart": db["weeks_apart"], "price_diff_pct": db["price_diff_pct"],
            "current_price": db.get("current_price"),
        })
    if ch:
        patterns_detected.append({"type": ch["type"], "status": "active", "trend": ch["trend"],
                                  "high_start": ch["high_start"], "high_end": ch["high_end"],
                                  "low_start": ch["low_start"], "low_end": ch["low_end"]})
    for cp in candle_pats[-4:]:
        patterns_detected.append({"type": cp["name"], "date": cp["date"], "signal": cp["signal"]})
    for e in eng_out[-2:]:
        patterns_detected.append({"type": e["type"], "signal": e["signal"]})

    # ---- Tech Score (-6..+6) ----
    # unit: prices in thousands VND; comparisons consistent
    s_ma10 = 1 if latest > ma10_v else -1
    s_ma20 = 1 if latest > ma20_v else -1
    s_ma50 = 1 if latest > ma50_v else -1 if ma50_v else 0
    s_rsi = 1 if rsi_v > 55 else (-1 if rsi_v < 45 else 0)
    s_macd = 1 if macd_v > signal_v else -1
    s_bb = 1 if (bb_pos is not None and bb_pos > 50) else -1
    score = s_ma10 + s_ma20 + s_ma50 + s_rsi + s_macd + s_bb
    if score >= 4: verdict = "TECHNICAL STRONG BULLISH"
    elif score >= 1: verdict = "TECHNICAL BULLISH"
    elif score <= -4: verdict = "TECHNICAL STRONG BEARISH"
    elif score <= -2: verdict = "TECHNICAL BEARISH"
    else: verdict = "TECHNICAL NEUTRAL"

    # Support/Resistance
    resistance = [
        {"level": "R1", "price": round_(high_52w*1000, 0), "note": "52W high"},
    ]
    if ma50_v: resistance.append({"level": "R2", "price": round_(ma50_v*1000, 0), "note": "MA50 (weekly)"})
    support = []
    if ma10_v: support.append({"level": "S1", "price": round_(ma10_v*1000, 0), "note": "MA10 (weekly)"})
    support.append({"level": "S2", "price": round_(low_52w*1000, 0), "note": "52W low"})

    # Strategy (3 scenarios) — ACTIVE language OK
    strategy = {
        "scenario_bullish": {
            "trigger": f"Giá đóng cửa tuần vượt và giữ trên MA20 ({ma20_v*1000:,.0f} VND) với volume tăng",
            "target": f"Vùng kháng cự {high_52w*1000:,.0f} VND (đỉnh 52 tuần)" + (f" → {db['target']*1000:,.0f} VND nếu double bottom confirm" if db else ""),
            "invalidation": f"Đóng cửa dưới đáy gần nhất {min(closes[-4:])*1000:,.0f} VND",
        },
        "scenario_neutral": {
            "range": f"{low_52w*1000:,.0f} – {high_52w*1000:,.0f} VND (biên 52 tuần)",
            "note": "Đi ngang trong channel/range; chờ breakout xác nhận với volume",
        },
        "scenario_bearish": {
            "trigger": f"Mất MA50 ({ma50_v*1000:,.0f} VND) hoặc RSI < 30",
            "target": f"Vùng hỗ trợ {low_52w*1000:,.0f} VND (đáy 52 tuần)",
            "invalidation": "Phục hồi trên MA10 với volume tăng",
        },
    }

    out = {
        "schema": "vn-technical-active-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ticker": "KDH",
        "company_name": overview.get("organ_name"),
        "exchange": "HOSE",
        "sector": overview.get("sector"),
        "data_source": "vnstock (VCI)",
        "data_period": f"{dates[0]} to {dates[-1]}",
        "timeframe": "weekly",
        "weeks_observed": n,
        "price_current_vnd": round_(latest*1000, 0),
        "price_current_k_vnd": latest,
        "latest_date": latest_date,
        "performance_1y_pct": round_(perf_1y, 2),
        "high_52w_vnd": round_(high_52w*1000, 0),
        "low_52w_vnd": round_(low_52w*1000, 0),
        "annualized_volatility_pct": round_(ann_vol, 2),
        "indicators": {
            "ma10": round_(ma10_v*1000, 0), "ma20": round_(ma20_v*1000, 0), "ma50": round_(ma50_v*1000, 0) if ma50_v else None,
            "ma10_k": round_(ma10_v, 2), "ma20_k": round_(ma20_v, 2), "ma50_k": round_(ma50_v, 2) if ma50_v else None,
            "rsi14": round_(rsi_v, 2),
            "macd": round_(macd_v, 4), "signal": round_(signal_v, 4), "histogram": round_(hist, 4),
            "macd_trend": macd_trend,
            "bollinger": {
                "upper": round_(bb_last["upper"], 2), "middle": round_(bb_last["middle"], 2),
                "lower": round_(bb_last["lower"], 2), "bb_position_pct": round_(bb_pos, 1),
            },
            "price_vs_ma10": "above" if latest > ma10_v else "below",
            "price_vs_ma20": "above" if latest > ma20_v else "below",
            "price_vs_ma50": ("above" if latest > ma50_v else "below") if ma50_v else "n/a",
        },
        "correlation": {
            "beta_vnindex": round_(beta_vni, 3), "beta_vn30": round_(beta_vn30, 3),
            "corr_vnindex": round_(corr_vni, 3), "corr_vn30": round_(corr_vn30, 3),
            "alpha_1y_pct": round_(alpha_1y, 2),
            "outperform_market": (alpha_1y > 0) if alpha_1y is not None else None,
            "paired_weeks_vnindex": len(sr_vni),
        },
        "patterns_detected": patterns_detected,
        "divergence": div,
        "swing_points": {
            "recent_highs": [{"date": dates[h["idx"]], "price": h["price"]} for h in swings["highs"][-3:]],
            "recent_lows": [{"date": dates[l["idx"]], "price": l["price"]} for l in swings["lows"][-3:]],
        },
        "tech_score": score,
        "tech_score_breakdown": {
            "price_vs_ma10": s_ma10, "price_vs_ma20": s_ma20, "price_vs_ma50": s_ma50,
            "rsi": s_rsi, "macd_vs_signal": s_macd, "bb_position": s_bb,
        },
        "verdict": verdict,
        "support_resistance": {"resistance": resistance, "support": support},
        "trading_strategy": strategy,
        "guardrail": "Verdict kỹ thuật chỉ là 1 input; cần kết hợp fundamental + valuation. Score bearish ở cổ phiếu chu kỳ có thể là vùng tích lũy cho value investor. KHÔNG phải lệnh giao dịch.",
        "data_transparency": {
            "price_unit": "VND (vnstock trả nghìn đồng, đã ×1000)",
            "indicators_period": "weekly bars (10/20/50 = tuần)",
            "patterns_claimed_only_with_evidence": True,
            "divergence_honest": not div["has_divergence"],
        },
    }
    return out

# =====================================================================
# MODE PROFILE  (15 blocks + setups + archetype)
# =====================================================================
def daily_returns_pct(rows):
    out = []
    for i in range(1, len(rows)):
        p, c = rows[i-1].get("close"), rows[i].get("close")
        if p and c and p > 0 and c > 0:
            out.append((c/p - 1) * 100)
    return out

def log_returns(rows):
    out = []
    for i in range(1, len(rows)):
        p, c = rows[i-1].get("close"), rows[i].get("close")
        if p and c and p > 0 and c > 0:
            out.append(math.log(c/p))
    return out

def drawdown_series(rows):
    peak = None; out = []
    for row in rows:
        c = finite(row.get("close"))
        if c is None: out.append(None); continue
        peak = c if peak is None else max(peak, c)
        out.append(c/peak - 1 if peak else None)
    return out

def realized_vol(rows, window):
    values = log_returns(rows)[-window:]
    if len(values) < max(5, window // 3): return None
    return round_(std_dev(values) * math.sqrt(252) * 100)

def realized_vol_history(rows, window):
    returns = log_returns(rows)
    min_count = max(5, window // 3)
    values = []
    for i in range(min_count, len(returns) + 1):
        sample = returns[max(0, i-window):i]
        v = round_(std_dev(sample) * math.sqrt(252) * 100) if len(sample) >= min_count else None
        if finite(v): values.append(v)
    return values

def pct_change(rows, window):
    if len(rows) <= window: return None
    start = rows[-1-window].get("close"); end = rows[-1].get("close")
    if not (start and end and start > 0 and end > 0): return None
    return round_((end/start - 1) * 100)

def line_change_pct(points, window):
    if len(points) <= window: return None
    a = points[-1-window].get("value"); b = points[-1].get("value")
    if not (finite(a) and finite(b)) or a == 0: return None
    return round_((b/a - 1) * 100)

def sma_at(rows, index, field, window):
    if index < window - 1: return None
    sl = rows[index-window+1:index+1]
    vals = [finite(r.get(field)) for r in sl]
    vals = [v for v in vals if v is not None]
    return sum(vals)/len(vals) if len(vals) == window else None

def vwma_at(rows, index, field, window):
    if index < window - 1: return None
    sl = rows[index-window+1:index+1]
    num = 0.0; den = 0.0; ok = True
    for r in sl:
        px = finite(r.get(field)); vol = finite(r.get("volume"))
        if px is None or vol is None: ok = False; break
        num += px*vol; den += vol
    return (num/den) if ok and den > 0 else None

def moving_average_before(rows, index, field, window):
    return sma_at(rows, index-1, field, window)

def average_value(rows, window):
    sl = rows[-window:]
    vals = [finite(r.get("value")) for r in sl]
    vals = [v for v in vals if v is not None]
    return sum(vals)/len(vals) if vals else None

def drawdown_episodes(rows):
    peak = None; peak_date = None
    episodes = []; in_dd = False; trough_idx = None; trough_close = None
    peak_at_start = None; peak_at_start_date = None
    for i, row in enumerate(rows):
        c = finite(row.get("close"))
        if c is None: continue
        if peak is None or c > peak:
            peak = c; peak_date = row.get("date")
            if in_dd:
                eps_depth = (trough_close/peak_at_start - 1)*100 if peak_at_start else None
                episodes.append({"peak_date": peak_at_start_date,
                                 "trough_date": rows[trough_idx]["date"],
                                 "depth_pct": round_(eps_depth),
                                 "recovery_days": i - trough_idx})
                in_dd = False
        else:
            if not in_dd:
                in_dd = True; peak_at_start = peak; peak_at_start_date = peak_date
                trough_idx = i; trough_close = c
            elif c < trough_close:
                trough_idx = i; trough_close = c
    if in_dd:
        eps_depth = (trough_close/peak_at_start - 1)*100 if peak_at_start else None
        episodes.append({"peak_date": peak_at_start_date,
                         "trough_date": rows[trough_idx]["date"],
                         "depth_pct": round_(eps_depth),
                         "recovery_days": None})
    episodes.sort(key=lambda e: e["depth_pct"] or 0)
    return episodes

def max_runup_profile(rows):
    if not rows: return None
    low_idx = 0
    best = {"value_pct": None, "low_date": rows[0].get("date"), "high_date": rows[0].get("date")}
    for i, row in enumerate(rows):
        if row.get("close") < rows[low_idx].get("close"): low_idx = i
        low = rows[low_idx].get("close")
        if low and low > 0:
            v = (row.get("close")/low - 1) * 100
            if not finite(best["value_pct"]) or v > best["value_pct"]:
                best = {"value_pct": round_(v), "low_date": rows[low_idx].get("date"), "high_date": row.get("date")}
    return best

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
    return {"window": window, "current_return_pct": current,
            "percentile": percentile_of_value(values, current),
            "median_return_pct": round_(median(values)),
            "p10_return_pct": round_(quantile(values, 0.1)),
            "p90_return_pct": round_(quantile(values, 0.9)),
            "observations": len(values)}

def threshold_counts(values):
    nums = [v for v in values if finite(v)]
    return {"observations": len(nums),
            "up_5_pct": sum(1 for v in nums if v >= 5),
            "down_5_pct": sum(1 for v in nums if v <= -5),
            "up_10_pct": sum(1 for v in nums if v >= 10),
            "down_10_pct": sum(1 for v in nums if v <= -10)}

# ---- B1 price_behavior ----
def price_behavior_profile(rows):
    latest = rows[-1] if rows else {}
    closes_252 = [r["close"] for r in rows[-252:] if finite(r.get("close"))]
    high_52w = max(closes_252) if closes_252 else None
    low_52w = min(closes_252) if closes_252 else None
    latest_close = latest.get("close")
    returns = daily_returns_pct(rows)
    rolling = [rolling_return_profile(rows, w) for w in (21, 63, 126, 252)]
    return {
        "latest_close": latest_close, "latest_date": latest.get("date"),
        "return_1m_pct": pct_change(rows, 21), "return_3m_pct": pct_change(rows, 63),
        "return_6m_pct": pct_change(rows, 126), "return_1y_pct": pct_change(rows, 252),
        "high_52w": high_52w, "low_52w": low_52w,
        "distance_from_52w_high_pct": round_((latest_close/high_52w - 1)*100) if high_52w and latest_close else None,
        "distance_from_52w_low_pct": round_((latest_close/low_52w - 1)*100) if low_52w and latest_close else None,
        "rolling_returns": rolling,
        "daily_return_distribution": {
            "observations": len(returns), "median_pct": round_(median(returns)),
            "p10_pct": round_(quantile(returns, 0.1)), "p90_pct": round_(quantile(returns, 0.9)),
            **threshold_counts(returns),
        },
        "interpretation_guardrail": "Hành vi giá là quan sát lịch sử; không phải dự báo xu hướng tương lai.",
    }

# ---- B2 volatility ----
def volatility_profile(rows):
    vol20_hist = realized_vol_history(rows, 20)
    vol60_hist = realized_vol_history(rows, 60)
    cv20 = realized_vol(rows, 20); cv60 = realized_vol(rows, 60)
    range_63 = [finite(r.get("range_pct")) for r in rows[-63:]]
    range_63 = [v for v in range_63 if v is not None]
    return {
        "hv20_pct": cv20, "hv60_pct": cv60,
        "hv120_pct": realized_vol(rows, 120), "hv252_pct": realized_vol(rows, 252),
        "hv20_percentile_1y": percentile_of_value(vol20_hist[-252:], cv20),
        "hv60_percentile_1y": percentile_of_value(vol60_hist[-252:], cv60),
        "range_pct_median_63d": round_(median(range_63)),
        "range_pct_p90_63d": round_(quantile(range_63, 0.9)),
        "interpretation_guardrail": "Biến động là độ phân tán lịch sử; không phải dải giá kỳ vọng hay dự báo biến động tương lai.",
    }

# ---- B3 drawdown ----
def drawdown_profile(rows):
    dd = drawdown_series(rows)
    fdd = [v for v in dd if finite(v)]
    current = fdd[-1] if fdd else None
    max_depth = min(fdd) if fdd else None
    underwater = 0
    for v in reversed(dd):
        if finite(v) and v < 0: underwater += 1
        else: break
    episodes = drawdown_episodes(rows)
    rec = [e.get("recovery_days") for e in episodes if finite(e.get("recovery_days"))]
    return {
        "current_drawdown_pct": round_(current*100) if finite(current) else None,
        "current_underwater_days": underwater,
        "max_drawdown_pct": round_(max_depth*100) if finite(max_depth) else None,
        "episode_count": len(episodes),
        "deep_drawdown_count_10_pct": sum(1 for e in episodes if (e.get("depth_pct") or 0) <= -10),
        "deep_drawdown_count_20_pct": sum(1 for e in episodes if (e.get("depth_pct") or 0) <= -20),
        "deep_drawdown_count_30_pct": sum(1 for e in episodes if (e.get("depth_pct") or 0) <= -30),
        "median_recovery_days": round_(median(rec), 0) if rec else None,
        "worst_episodes": episodes[:5],
        "max_runup": max_runup_profile(rows),
        "interpretation_guardrail": "Mức giảm từ đỉnh nhạy với cửa sổ và dữ liệu chưa điều chỉnh sự kiện vốn; không phải dự báo đáy/đỉnh.",
    }

# ---- B4 liquidity ----
def liquidity_profile(rows):
    latest = rows[-1] if rows else {}
    values_252 = [finite(r.get("value")) for r in rows[-252:]]
    values_252 = [v for v in values_252 if v is not None]
    avg20 = average_value(rows, 20); avg60 = average_value(rows, 60)
    latest_value = finite(latest.get("value"))
    spike = 0
    for i in range(max(0, len(rows)-252), len(rows)):
        vol = finite(rows[i].get("volume"))
        a20 = sma_at(rows, i-1, "volume", 20)
        if vol and a20 and a20 > 0 and vol >= 2*a20: spike += 1
    return {
        "latest_volume": latest.get("volume"), "latest_value": latest_value,
        "avg_value_20d": avg20, "avg_value_60d": avg60,
        "latest_value_percentile_1y": percentile_of_value(values_252, latest_value),
        "liquidity_stability": round_(std_dev(values_252)/mean(values_252)*100) if values_252 and mean(values_252) else None,
        "volume_spike_days_1y": spike,
        "interpretation_guardrail": "Thanh khoản tính từ giá đóng cửa × khối lượng; không phản ánh block trade, sổ lệnh hay dữ liệu intraday.",
    }

# ---- B5 return distribution ----
def return_distribution_profile(rows):
    daily = daily_returns_pct(rows)
    one_year = daily[-252:]
    bins = [("< = -10%", float("-inf"), -10), ("-10% to -5%", -10, -5),
            ("-5% to -2%", -5, -2), ("-2% to 0%", -2, 0),
            ("0% to 2%", 0, 2), ("2% to 5%", 2, 5),
            ("5% to 10%", 5, 10), ("> 10%", 10, float("inf"))]
    def stats(sample):
        return {
            "observations": len(sample),
            "mean_pct": round_(mean(sample), 4), "median_pct": round_(median(sample), 4),
            "std_pct": round_(std_dev(sample), 4),
            "p01_pct": round_(quantile(sample, 0.01), 4), "p05_pct": round_(quantile(sample, 0.05), 4),
            "p25_pct": round_(quantile(sample, 0.25), 4), "p75_pct": round_(quantile(sample, 0.75), 4),
            "p95_pct": round_(quantile(sample, 0.95), 4), "p99_pct": round_(quantile(sample, 0.99), 4),
            "iqr_pct": round_(quantile(sample, 0.75) - quantile(sample, 0.25), 4),
            "skewness": round_(skewness(sample), 4), "excess_kurtosis": round_(excess_kurtosis(sample), 4),
            "positive_day_rate_pct": round_(sum(1 for v in sample if v > 0)/len(sample)*100) if sample else None,
        }
    return {
        "full_sample": stats(daily), "one_year": stats(one_year),
        "one_year_histogram": [{"label": l, "count": sum(1 for v in one_year if mn < v <= mx)} for l, mn, mx in bins],
        "interpretation_guardrail": "Phân phối lợi suất là thống kê mô tả quá khứ; không giả định phân phối chuẩn và không dự báo lợi suất tương lai.",
    }

# ---- B6 tail risk ----
def tail_risk_profile(rows):
    daily = daily_returns_pct(rows); tail = daily[-252:]
    q05 = quantile(tail, 0.05); q01 = quantile(tail, 0.01)
    es05 = mean([v for v in tail if v <= q05]) if finite(q05) else None
    es01 = mean([v for v in tail if v <= q01]) if finite(q01) else None
    r21 = [v for v in rolling_return_series(rows, 21) if finite(v)]
    r63 = [v for v in rolling_return_series(rows, 63) if finite(v)]
    return {
        "observations_1y": len(tail),
        "historical_var_95_1d_pct": round_(abs(q05), 4) if finite(q05) else None,
        "historical_var_99_1d_pct": round_(abs(q01), 4) if finite(q01) else None,
        "expected_shortfall_95_1d_pct": round_(abs(es05), 4) if finite(es05) else None,
        "expected_shortfall_99_1d_pct": round_(abs(es01), 4) if finite(es01) else None,
        "down_5pct_days_1y": sum(1 for v in tail if v <= -5),
        "down_10pct_days_1y": sum(1 for v in tail if v <= -10),
        "rolling_21d_p05_pct": round_(quantile(r21, 0.05)),
        "rolling_63d_p05_pct": round_(quantile(r63, 0.05)),
        "interpretation_guardrail": "Tail risk dùng lịch sử đã quan sát; VaR/ES ở đây là mô tả historical, không phải mô hình rủi ro giao dịch.",
    }

# ---- B7 liquidity risk ----
def liquidity_risk_profile(rows):
    tail = rows[-252:]
    values = [finite(r.get("value")) for r in tail]
    values = [v for v in values if v is not None and v >= 0]
    latest = rows[-1] if rows else {}
    avg20 = average_value(rows, 20); avg60 = average_value(rows, 60)
    med252 = median(values)
    drought_thr = med252*0.5 if finite(med252) else None
    severe_thr = med252*0.2 if finite(med252) else None
    cap20 = avg20*0.1 if finite(avg20) else None
    cap60 = avg60*0.1 if finite(avg60) else None
    def dtt(notion):
        return {"notional": notion,
                "at_10pct_adv20_days": round_(notion/cap20, 2) if cap20 else None,
                "at_10pct_adv60_days": round_(notion/cap60, 2) if cap60 else None}
    zero_vol = sum(1 for r in tail if (r.get("volume") or 0) <= 0)
    thin_days = sum(1 for r in tail if finite(r.get("value")) and r["value"] <= severe_thr) if severe_thr else 0
    drought_days = sum(1 for r in tail if finite(r.get("value")) and r["value"] <= drought_thr) if drought_thr else 0
    label = "trung bình"
    if zero_vol > 5 or thin_days >= 40 or (finite(avg20) and finite(med252) and avg20 < med252*0.4): label = "cao"
    if zero_vol == 0 and thin_days < 10 and finite(avg20) and finite(med252) and avg20 >= med252*0.8: label = "thấp"
    return {
        "observations_1y": len(tail), "latest_value": latest.get("value"),
        "median_value_1y": round_(med252, 0) if finite(med252) else None,
        "avg_value_20d": avg20, "avg_value_60d": avg60,
        "latest_value_percentile_1y": percentile_of_value(values, latest.get("value")),
        "zero_volume_days_1y": zero_vol, "value_drought_days_1y": drought_days,
        "severe_thin_value_days_1y": thin_days,
        "trade_capacity_scenarios": [dtt(n) for n in (1_000_000_000, 5_000_000_000, 10_000_000_000)],
        "liquidity_risk_label": label,
        "interpretation_guardrail": "Rủi ro thanh khoản chỉ là stress test theo giá trị giao dịch lịch sử; không phản ánh sổ lệnh thời gian thực hoặc chi phí trượt giá thực tế.",
    }

# ---- B8 relative strength / dynamic beta / correlation ----
def paired_rows(stock_rows, bench_rows):
    bench_by = {r.get("date"): r for r in bench_rows}
    out = []
    for r in stock_rows:
        b = bench_by.get(r.get("date"))
        if b and finite(r.get("close")) and finite(b.get("close")):
            out.append({"date": r.get("date"), "stock": r, "benchmark": b})
    return out

def benchmark_metrics(paired, window=252):
    pairs = paired[-(window+1):]
    if len(pairs) < max(5, window // 2): return None
    sr, br = [], []
    for i in range(1, len(pairs)):
        sp, sc = pairs[i-1]["stock"]["close"], pairs[i]["stock"]["close"]
        bp, bc = pairs[i-1]["benchmark"]["close"], pairs[i]["benchmark"]["close"]
        if sp > 0 and bp > 0:
            sr.append(sc/sp - 1); br.append(bc/bp - 1)
    if len(sr) < max(5, window // 2): return None
    sc = 1.0; bc = 1.0
    for s, b in zip(sr, br): sc *= (1+s); bc *= (1+b)
    sret = sc - 1; bret = bc - 1
    ms = sum(sr)/len(sr); mb = sum(br)/len(br)
    cs = [s-ms for s in sr]; cb = [b-mb for b in br]
    cov = sum(x*y for x, y in zip(cs, cb)) / (len(sr) - 1)
    var = sum(x*x for x in cb) / (len(br) - 1)
    bt = cov/var if var else None
    den = (sum(x*x for x in cs)**0.5) * (sum(y*y for y in cb)**0.5)
    cc = sum(x*y for x, y in zip(cs, cb))/den if den else None
    r2 = cc*cc if finite(cc) else None
    hr = sum(1 for s, b in zip(sr, br) if s > b)/len(sr)*100
    sdd = drawdown_series([p["stock"] for p in pairs])
    bdd = drawdown_series([p["benchmark"] for p in pairs])
    dd_pairs = [(s, b) for s, b in zip(sdd, bdd) if finite(s) and finite(b)]
    if dd_pairs:
        ds = [x[0] for x in dd_pairs]; db = [x[1] for x in dd_pairs]
        ms2 = sum(ds)/len(ds); mb2 = sum(db)/len(db)
        cs2 = [x-ms2 for x in ds]; cb2 = [x-mb2 for x in db]
        den2 = (sum(x*x for x in cs2)**0.5) * (sum(y*y for y in cb2)**0.5)
        dds = sum(x*y for x, y in zip(cs2, cb2))/den2 if den2 else None
    else: dds = None
    return {
        "window": window, "observations": len(sr),
        "stock_return_pct": round_(sret*100), "benchmark_return_pct": round_(bret*100),
        "relative_return_pct": round_((sret - bret)*100),
        "correlation": round_(cc, 4), "beta": round_(bt, 4),
        "r2": round_(r2, 4) if finite(r2) else None,
        "hit_rate_pct": round_(hr),
        "stock_max_drawdown_pct": round_(min(d for d in sdd if finite(d))*100) if any(finite(x) for x in sdd) else None,
        "benchmark_max_drawdown_pct": round_(min(d for d in bdd if finite(d))*100) if any(finite(x) for x in bdd) else None,
        "drawdown_similarity": round_(dds, 4) if finite(dds) else None,
    }

def relative_strength_profile(stock_rows, bench_rows, benchmarks):
    comparisons = []
    for bid, brows in benchmarks.items():
        paired = paired_rows(stock_rows, brows)
        metrics = {str(w): benchmark_metrics(paired, w) for w in (60, 120, 252)}
        comparisons.append({"benchmark": bid, "metrics": metrics})
    best_fit = None
    for c in comparisons:
        r2_252 = c["metrics"].get("252", {}).get("r2") if c["metrics"].get("252") else None
        if finite(r2_252) and (best_fit is None or r2_252 > best_fit["r2_252"]):
            best_fit = {"benchmark": c["benchmark"], "r2_252": r2_252}
    vnindex = next((c for c in comparisons if c["benchmark"] == "VNINDEX"), None)
    vni_252 = vnindex["metrics"]["252"] if vnindex and vnindex["metrics"].get("252") else {}
    return {
        "relative_strength_profile": {
            "best_fit_benchmark": best_fit, "comparisons": comparisons,
            "interpretation_guardrail": "So sánh benchmark là mô tả lịch sử theo dữ liệu hiện có, không phải tín hiệu dự báo.",
        },
        "dynamic_beta_profile": {
            "primary_benchmark": "VNINDEX",
            "beta_60": vnindex["metrics"]["60"]["beta"] if vnindex and vnindex["metrics"].get("60") else None,
            "beta_120": vnindex["metrics"]["120"]["beta"] if vnindex and vnindex["metrics"].get("120") else None,
            "beta_252": vni_252.get("beta"),
        },
        "correlation_profile": {
            "primary_benchmark": "VNINDEX",
            "corr_60": vnindex["metrics"]["60"]["correlation"] if vnindex and vnindex["metrics"].get("60") else None,
            "corr_252": vni_252.get("correlation"), "r2_252": vni_252.get("r2"),
            "drawdown_similarity_252": vni_252.get("drawdown_similarity"),
        },
    }

# ---- B9 regime ----
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
    return {"id": rid, "label": label, "r60": round_(r60*100), "r120": round_(r120*100),
            "drawdown_pct": round_(drawdown*100), "vol_rank": vol_rank}

def regime_profile(stock_rows, vnindex_rows):
    rows = vnindex_rows
    regimes_by_date = {}
    for i, row in enumerate(rows):
        if i < 120: continue
        r60 = (row["close"]/rows[i-60]["close"] - 1) if rows[i-60].get("close") else None
        r120 = (row["close"]/rows[i-120]["close"] - 1) if rows[i-120].get("close") else None
        dd = drawdown_series(rows[:i+1])[-1]
        vh = realized_vol_history(rows[:i+1], 20)
        vn = vh[-1] if vh else None
        vr = percentile_of_value(vh, vn) if finite(vn) else None
        regimes_by_date[row["date"]] = classify_regime(r60, r120, dd, vr)
    current = regimes_by_date.get(rows[-1]["date"]) if rows else None
    paired = paired_rows(stock_rows, vnindex_rows)
    groups = {}
    for i in range(1, len(paired)):
        sp, sc = paired[i-1]["stock"]["close"], paired[i]["stock"]["close"]
        bp, bc = paired[i-1]["benchmark"]["close"], paired[i]["benchmark"]["close"]
        regime = regimes_by_date.get(paired[i]["date"])
        if not regime or regime["id"] == "unknown" or not (sp > 0 and bp > 0): continue
        rid = regime["id"]
        g = groups.setdefault(rid, {"regime_id": rid, "regime_label": regime["label"],
                                    "stock_returns": [], "bench_returns": []})
        g["stock_returns"].append(sc/sp - 1); g["bench_returns"].append(bc/bp - 1)
    behavior = []
    for g in groups.values():
        srs, brs = g["stock_returns"], g["bench_returns"]
        if not srs: continue
        behavior.append({"regime_id": g["regime_id"], "regime_label": g["regime_label"],
                         "observations": len(srs),
                         "stock_avg_daily_return_pct": round_(mean(srs)*100, 4),
                         "benchmark_avg_daily_return_pct": round_(mean(brs)*100, 4),
                         "relative_avg_daily_return_pct": round_((mean(srs)-mean(brs))*100, 4),
                         "hit_rate_pct": round_(sum(1 for s, b in zip(srs, brs) if s > b)/len(srs)*100)})
    behavior.sort(key=lambda x: x["regime_id"])
    return {"primary_benchmark": "VNINDEX", "current_market_regime": current,
            "behavior_by_market_regime": behavior,
            "regime_guardrail": "Regime dùng trạng thái benchmark hiện có; không thay thế lịch sử thành phần point-in-time."}

# ---- B10 volume_price_profile ----
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
        if finite(tail[i].get("close")) and finite(tail[i-1].get("close")) and tail[i-1]["close"] > 0 and finite(tail[i].get("value")):
            pairs.append((abs(tail[i]["close"]/tail[i-1]["close"] - 1), tail[i]["value"]))
    if len(pairs) >= 5:
        xs = [p[0] for p in pairs]; ys = [p[1] for p in pairs]
        mx, my = mean(xs), mean(ys)
        cx = [x-mx for x in xs]; cy = [y-my for y in ys]
        den = (sum(x*x for x in cx)**0.5) * (sum(y*y for y in cy)**0.5)
        rvc = round_(sum(x*y for x, y in zip(cx, cy))/den, 4) if den else None
    else: rvc = None
    return {
        "observations_1y": len(tail),
        "avg_value_up_days": round_(avg_up) if avg_up else None,
        "avg_value_down_days": round_(avg_down) if avg_down else None,
        "up_down_value_ratio_1y": round_(avg_up/avg_down, 4) if avg_up and avg_down else None,
        "abs_return_value_correlation_1y": rvc,
        "interpretation_guardrail": "Quan hệ giá-khối lượng là đồng biến hay nghịch biến trong quá khứ; không kết luận dòng tiền tương lai.",
    }

# ---- B11 VPCI ----
def confirmation_label(vpci_latest, vpci_change_20d, price_vs_sma_long, volume_ratio):
    known = [v for v in (vpci_latest, price_vs_sma_long, volume_ratio) if finite(v)]
    if len(known) < 2: return "chưa đủ dữ liệu"
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
                       "sma_short": sma_s, "sma_long": sma_l, "volume_ratio_short_long": vm})
    valid = [s for s in series if finite(s.get("value"))]
    latest = series[-1] if series else {}
    latest_valid = valid[-1] if valid else {}
    latest_close = rows[-1].get("close") if rows else None
    price_vs_sma_long = (round_((latest_close/latest["sma_long"] - 1)*100)
                         if finite(latest_close) and finite(latest.get("sma_long")) and latest["sma_long"] else None)
    vpci_change_20d = line_change_pct(valid, 20)
    label = confirmation_label(latest_valid.get("value"), vpci_change_20d, price_vs_sma_long, latest.get("volume_ratio_short_long"))
    return {
        "methodology": "VPCI/VWMA/SMA daily OHLCV, fixed windows 20/100",
        "short_window": short_window, "long_window": long_window,
        "observations": len(rows), "valid_observations": len(valid),
        "sma_20": latest.get("sma_short"), "sma_100": latest.get("sma_long"),
        "price_vs_sma100_pct": price_vs_sma_long,
        "vpci_latest": latest_valid.get("value"), "vpci_20d_change_pct": vpci_change_20d,
        "vpci_percentile_1y": percentile_of_value([v["value"] for v in valid[-252:]], latest_valid.get("value")),
        "confirmation_label": label,
        "interpretation_guardrail": "VPCI/VWMA/SMA mô tả mức đồng thuận giữa giá và volume; không phải tín hiệu giao dịch hay dự báo giá.",
    }

# ---- B12 money flow ----
def cmf_at(rows, index, window=20):
    sample = rows[max(0, index-window+1):index+1]
    sample = [r for r in sample if all(finite(r.get(f)) for f in ("high","low","close","volume")) and r["volume"] > 0]
    if len(sample) < max(5, window // 2): return None
    vol_sum = sum(r["volume"] for r in sample)
    if not vol_sum: return None
    flow = 0
    for r in sample:
        rng = r["high"]-r["low"]
        if not rng: continue
        mult = ((r["close"]-r["low"]) - (r["high"]-r["close"]))/rng
        flow += mult*r["volume"]
    return flow/vol_sum

def money_flow_label(cmf20, cmf60, vpt_chg, obv_chg):
    vals = [v for v in (cmf20, cmf60, vpt_chg, obv_chg) if finite(v)]
    pos = sum(1 for v in vals if v > 0); neg = sum(1 for v in vals if v < 0)
    if pos + neg < 2: return "chưa đủ dữ liệu"
    if pos >= 3 and (cmf20 or 0) > 0.03 and (cmf60 or 0) >= 0: return "áp lực tiền dương"
    if neg >= 3 and (cmf20 or 0) < -0.03 and (cmf60 or 0) <= 0: return "áp lực tiền âm"
    if pos >= 3 and (not finite(cmf20) or cmf20 >= 0) and (not finite(cmf60) or cmf60 >= -0.03): return "nghiêng dương nhưng yếu"
    if neg >= 3 and (not finite(cmf20) or cmf20 <= 0) and (not finite(cmf60) or cmf60 <= 0.03): return "nghiêng âm nhưng yếu"
    return "hỗn hợp"

def money_flow_profile(rows):
    cum = []; obv = 0; vpt = 0
    for i in range(1, len(rows)):
        p, r = rows[i-1], rows[i]
        if not (p.get("close", 0) > 0 and r.get("close", 0) > 0) or not finite(r.get("volume")): continue
        ret = r["close"]/p["close"] - 1
        if r["close"] > p["close"]: obv += r["volume"]
        elif r["close"] < p["close"]: obv -= r["volume"]
        vpt += r["volume"]*ret
        cum.append({"date": r.get("date"), "obv": obv, "vpt": vpt, "ret_pct": ret*100, "volume": r["volume"]})
    cmf20 = cmf_at(rows, len(rows)-1, 20); cmf60 = cmf_at(rows, len(rows)-1, 60)
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
        "obv_20d_change_pct": obv_chg, "vpt_20d_change_pct": vpt_chg,
        "cmf_20d": round_(cmf20, 4) if finite(cmf20) else None,
        "cmf_60d": round_(cmf60, 4) if finite(cmf60) else None,
        "positive_flow_days_1y": sum(1 for c in tail if c["ret_pct"] > 0 and c.get("volume", 0) > 0),
        "negative_flow_days_1y": sum(1 for c in tail if c["ret_pct"] < 0 and c.get("volume", 0) > 0),
        "money_flow_label": label,
        "interpretation_guardrail": "Money flow mô tả áp lực từ OHLCV ngày; không thay thế dữ liệu intraday, block trade, sổ lệnh hoặc khuyến nghị giao dịch.",
    }

# ---- B13 effort-result ----
def effort_result_label(low_cnt, high_cnt, he_cnt, latest_effort, latest_rpe, median_rpe):
    if not he_cnt: return "chưa đủ high-effort events"
    low_share = low_cnt/he_cnt; high_share = high_cnt/he_cnt
    if (finite(latest_effort) and latest_effort >= 2 and finite(latest_rpe) and finite(median_rpe)
            and latest_rpe <= median_rpe*0.7): return "effort cao, result thấp"
    if low_share >= 0.45: return "thường có effort cao nhưng result thấp"
    if high_share >= 0.45: return "effort cao thường đi cùng result lớn"
    return "effort-result hỗn hợp"

def effort_result_profile(rows):
    obs = []
    for i in range(1, len(rows)):
        p, r = rows[i-1], rows[i]
        if not (p.get("close", 0) > 0 and r.get("close", 0) > 0): continue
        vol_avg20 = moving_average_before(rows, i, "volume", 20)
        val_avg20 = moving_average_before(rows, i, "value", 20)
        ret = (r["close"]/p["close"] - 1)*100
        rng = (finite(r.get("range_pct")) and r["range_pct"]
               or (r["high"]-r["low"])/p["close"]*100 if (finite(r.get("high")) and finite(r.get("low"))) else None)
        vol_ratio = (r["volume"]/vol_avg20) if (finite(r.get("volume")) and finite(vol_avg20) and vol_avg20 > 0) else None
        val_ratio = (r["value"]/val_avg20) if (finite(r.get("value")) and finite(val_avg20) and val_avg20 > 0) else None
        effort = mean([v for v in (vol_ratio, val_ratio) if finite(v)])
        result = max(abs(ret) if finite(ret) else 0, rng if finite(rng) else 0)
        obs.append({"date": r.get("date"), "ret_pct": ret, "abs_ret_pct": abs(ret), "range_pct": rng,
                    "effort_ratio": effort, "result_pct": result,
                    "result_per_effort": (result/effort) if (finite(effort) and effort > 0) else None})
    tail = obs[-252:]
    rv = [o["result_pct"] for o in tail if finite(o.get("result_pct"))]
    rpe = [o["result_per_effort"] for o in tail if finite(o.get("result_per_effort"))]
    rm = median(rv); r75 = quantile(rv, 0.75); rpem = median(rpe)
    he = [o for o in tail if finite(o.get("effort_ratio")) and o["effort_ratio"] >= 2]
    low_rhe = [o for o in he if finite(o.get("result_pct")) and finite(rm) and o["result_pct"] <= rm]
    high_rhe = [o for o in he if finite(o.get("result_pct")) and finite(r75) and o["result_pct"] >= r75]
    latest = obs[-1] if obs else {}
    label = effort_result_label(len(low_rhe), len(high_rhe), len(he), latest.get("effort_ratio"), latest.get("result_per_effort"), rpem)
    return {
        "methodology": "Effort = avg(normalized volume 20D, normalized value 20D); Result = max(abs return, intraday range)",
        "observations_1y": len(tail), "high_effort_days_1y": len(he),
        "low_result_high_effort_days_1y": len(low_rhe), "high_result_high_effort_days_1y": len(high_rhe),
        "low_result_high_effort_share_pct": round_(len(low_rhe)/len(he)*100) if he else None,
        "high_result_high_effort_share_pct": round_(len(high_rhe)/len(he)*100) if he else None,
        "median_result_pct_1y": round_(rm, 4) if finite(rm) else None,
        "median_result_per_effort_1y": round_(rpem, 4) if finite(rpem) else None,
        "latest_effort_ratio": latest.get("effort_ratio"), "latest_result_pct": latest.get("result_pct"),
        "effort_result_label": label,
        "interpretation_guardrail": "Effort-result đo từ dữ liệu ngày để nhận diện phiên nhiều giao dịch nhưng biến động tương ứng thấp/cao; không kết luận hấp thụ/cạn cung theo nghĩa tín hiệu.",
    }

# ---- B14 high volume behavior ----
def forward_return(rows, index, window):
    if index + window >= len(rows): return None
    start = rows[index].get("close"); end = rows[index+window].get("close")
    if not (start and end and start > 0 and end > 0): return None
    return (end/start - 1)*100

def forward_window_stats(events, key):
    mat = [e for e in events if finite(e.get(key))]
    vals = [e[key] for e in mat]
    return {"matured_events": len(mat), "median_pct": round_(median(vals), 4),
            "p25_pct": round_(quantile(vals, 0.25), 4), "p75_pct": round_(quantile(vals, 0.75), 4),
            "positive_rate_pct": round_(sum(1 for v in vals if v > 0)/len(vals)*100) if vals else None}

def high_volume_behavior_label(stats20, event_count):
    if event_count < 5 or stats20.get("matured_events", 0) < 5: return "chưa đủ high-volume events"
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
                and p.get("close", 0) > 0 and r.get("close", 0) > 0): continue
        nv = r["volume"]/avg20
        if nv < threshold: continue
        events.append({"date": r.get("date"), "close": r["close"], "volume": r["volume"],
                       "normalized_volume_20d": round_(nv, 4),
                       "same_day_return_pct": round_((r["close"]/p["close"] - 1)*100, 4),
                       "forward_return_5d_pct": round_(forward_return(rows, i, 5), 4),
                       "forward_return_20d_pct": round_(forward_return(rows, i, 20), 4),
                       "forward_return_60d_pct": round_(forward_return(rows, i, 60), 4)})
    events_1y = events[-252:]
    s20 = forward_window_stats(events, "forward_return_20d_pct")
    label = high_volume_behavior_label(s20, len(events))
    return {
        "methodology": "High-volume event = volume >= 2x trailing 20D average; forward returns measured after event close",
        "threshold_normalized_volume_20d": threshold,
        "observations": len(rows), "event_count_full_sample": len(events), "event_count_1y": len(events_1y),
        "forward_5d": forward_window_stats(events, "forward_return_5d_pct"),
        "forward_20d": s20,
        "forward_60d": forward_window_stats(events, "forward_return_60d_pct"),
        "post_high_volume_label": label,
        "latest_high_volume_event": events[-1] if events else None,
        "recent_high_volume_events": events[-12:],
        "interpretation_guardrail": "Event study mô tả điều đã xảy ra sau các phiên volume cao; không dùng để dự báo phiên kế tiếp hoặc sinh tín hiệu mua bán.",
    }

# ---- B15 PVI/NVI ----
def pvi_nvi_label(pvi_chg20, nvi_chg20, pvi_nvi_ratio):
    known = [v for v in (pvi_chg20, nvi_chg20, pvi_nvi_ratio) if finite(v)]
    if len(known) < 2: return "chưa đủ dữ liệu"
    if (pvi_chg20 or 0) > 0 and (nvi_chg20 or 0) <= 0: return "high-volume participation nổi bật hơn"
    if (nvi_chg20 or 0) > 0 and (pvi_chg20 or 0) <= 0: return "low-volume participation nổi bật hơn"
    if (pvi_chg20 or 0) > 0 and (nvi_chg20 or 0) > 0: return "participation cùng chiều"
    if (pvi_chg20 or 0) < 0 and (nvi_chg20 or 0) < 0: return "participation cùng suy yếu"
    return "participation hỗn hợp"

def pvi_nvi_profile(rows):
    series = []; pvi = 1000.0; nvi = 1000.0
    for i in range(1, len(rows)):
        p, r = rows[i-1], rows[i]
        if not (p.get("close", 0) > 0 and r.get("close", 0) > 0) or not finite(p.get("volume")) or not finite(r.get("volume")): continue
        ret = r["close"]/p["close"] - 1
        if r["volume"] > p["volume"]: pvi *= (1+ret)
        if r["volume"] < p["volume"]: nvi *= (1+ret)
        direction = "higher_volume" if r["volume"] > p["volume"] else ("lower_volume" if r["volume"] < p["volume"] else "same_volume")
        series.append({"date": r.get("date"), "volume": r["volume"], "ret_pct": round_(ret*100, 4),
                       "pvi": round_(pvi, 4), "nvi": round_(nvi, 4), "volume_direction": direction})
    latest = series[-1] if series else {}
    pvi20 = line_change_pct([{"value": s["pvi"]} for s in series], 20)
    nvi20 = line_change_pct([{"value": s["nvi"]} for s in series], 20)
    pvi60 = line_change_pct([{"value": s["pvi"]} for s in series], 60)
    nvi60 = line_change_pct([{"value": s["nvi"]} for s in series], 60)
    ratio = (latest["pvi"]/latest["nvi"]) if (finite(latest.get("pvi")) and finite(latest.get("nvi")) and latest.get("nvi")) else None
    tail = series[-252:]
    label = pvi_nvi_label(pvi20, nvi20, ratio)
    return {
        "methodology": "PVI updates on higher-volume days; NVI updates on lower-volume days; base=1000",
        "observations": len(series), "latest_date": latest.get("date"),
        "pvi_latest": latest.get("pvi"), "nvi_latest": latest.get("nvi"),
        "pvi_nvi_ratio": round_(ratio, 4) if finite(ratio) else None,
        "pvi_20d_change_pct": pvi20, "nvi_20d_change_pct": nvi20,
        "pvi_60d_change_pct": pvi60, "nvi_60d_change_pct": nvi60,
        "pvi_percentile_1y": percentile_of_value([s["pvi"] for s in tail], latest.get("pvi")),
        "nvi_percentile_1y": percentile_of_value([s["nvi"] for s in tail], latest.get("nvi")),
        "higher_volume_days_1y": sum(1 for s in tail if s["volume_direction"] == "higher_volume"),
        "lower_volume_days_1y": sum(1 for s in tail if s["volume_direction"] == "lower_volume"),
        "participation_regime_label": label,
        "interpretation_guardrail": "PVI/NVI mô tả price change xảy ra nhiều hơn ở phiên volume tăng hay giảm; không phải tín hiệu giao dịch.",
    }

# ---- B16 volume-at-price ----
def typical_price(row):
    vals = [finite(row.get(f)) for f in ("high", "low", "close")]
    vals = [v for v in vals if v is not None]
    if len(vals) >= 3: return mean(vals)
    return finite(row.get("close"))

def volume_at_price_profile(rows, window=252, bin_count=12):
    tail = []
    for r in rows[-window:]:
        tp = typical_price(r)
        if finite(tp) and finite(r.get("volume")) and r["volume"] >= 0:
            tail.append({**r, "typical_price": tp})
    prices = [t["typical_price"] for t in tail]
    if not prices: return {"acceptance_label": "chưa đủ dữ liệu"}
    min_p, max_p = min(prices), max(prices)
    span = max(max_p - min_p, 0); step = span/bin_count if span > 0 else None
    bins = [{"bin_index": i, "days": 0, "volume": 0.0, "value": 0.0} for i in range(bin_count)]
    for t in tail:
        if not step: continue
        idx = max(0, min(bin_count-1, int((t["typical_price"] - min_p)/step)))
        bins[idx]["days"] += 1; bins[idx]["volume"] += t.get("volume") or 0; bins[idx]["value"] += t.get("value") or 0
    total_vol = sum(b["volume"] for b in bins) or 0
    total_val = sum(b["value"] for b in bins) or 0
    for b in bins:
        b["volume_share_pct"] = round_(b["volume"]/total_vol*100, 2) if total_vol else None
        b["value_share_pct"] = round_(b["value"]/total_val*100, 2) if total_val else None
    poc = sorted(bins, key=lambda b: b["volume"], reverse=True)[0] if bins else None
    top3 = sorted(bins, key=lambda b: b["volume"], reverse=True)[:3]
    conc = sum(b.get("volume_share_pct") or 0 for b in top3)
    latest_close = rows[-1].get("close") if rows else None
    cur_bin = bins[max(0, min(bin_count-1, int((latest_close - min_p)/step)))] if (latest_close and step) else None
    label = "chưa đủ dữ liệu"
    if len(tail) >= 60 and poc:
        if cur_bin and cur_bin["bin_index"] == poc["bin_index"]: label = "giá hiện tại nằm trong vùng volume lớn nhất"
        elif latest_close and latest_close > min_p + step*poc["bin_index"]: label = "giá hiện tại nằm trên vùng volume lớn nhất"
        elif latest_close: label = "giá hiện tại nằm dưới vùng volume lớn nhất"
        else: label = "volume-at-price hỗn hợp"
    return {
        "methodology": "Daily volume-at-price approximation: assigns each day volume/value to typical-price bins over trailing 252 sessions",
        "window": window, "bin_count": bin_count, "observations": len(tail),
        "price_min": round_(min_p, 4), "price_max": round_(max_p, 4),
        "point_of_control_bin_index": poc["bin_index"] if poc else None,
        "current_price_bin_index": cur_bin["bin_index"] if cur_bin else None,
        "volume_concentration_top3_pct": round_(conc, 2),
        "acceptance_label": label,
        "interpretation_guardrail": "VAP là xấp xỉ từ dữ liệu ngày; không thay thế volume profile intraday, order book hoặc phân bổ khớp lệnh thực tế trong phiên.",
    }

# ---- Pattern scoring (setups + archetype) ----
def pct(a, b): return (a/b - 1)*100 if b else 0.0
def clamp(v, lo=0.0, hi=100.0): return max(lo, min(hi, v))
def slope(values):
    if len(values) < 2: return 0.0
    n = len(values); xm = (n-1)/2; ym = sum(values)/n
    den = sum((i-xm)**2 for i in range(n)) or 1
    return sum((i-xm)*(v-ym) for i, v in enumerate(values))/den

def reader_note(name, status, distance):
    if status == "gần xác nhận": return f"{name} đang ở gần vùng cần xác nhận; vẫn cần chờ giá đóng cửa vượt mốc quan sát."
    if status == "đang hình thành": return f"{name} có cấu trúc đáng quan sát nhưng chưa đủ điều kiện xác nhận."
    if status == "nhiễu": return f"{name} có vài nét giống mẫu nhưng đường giá còn nhiễu."
    suffix = f", còn cách vùng xác nhận khoảng {distance:.2f}%" if distance is not None else ""
    return f"{name} chưa đủ sạch để đọc mạnh{suffix}."

def status_from_score(score, distance, noisy=False):
    if noisy: return "nhiễu"
    if score >= 78 and distance is not None and distance <= 3: return "gần xác nhận"
    if score >= 62: return "đang hình thành"
    return "chưa đủ sạch"

def setup(pid, pname, score, conf, wl, wh, cur, caution, status=None):
    score = round(clamp(score), 2)
    if score < 55: return None
    distance = max(0.0, pct(conf, cur)) if conf else None
    fs = status or status_from_score(score, distance)
    return {"pattern_id": pid, "pattern_name": pname, "setup_status": fs,
            "completion_score": score,
            "confirmation_price": round(conf, 4) if conf is not None else None,
            "watch_zone": {"low": round(wl, 4) if wl is not None else None,
                           "high": round(wh, 4) if wh is not None else None},
            "distance_to_confirmation_pct": round(distance, 2) if distance is not None else None,
            "caution_reason": caution,
            "reader_note": reader_note(pname, fs, distance)}

def detect_bull_flag(rows):
    cur = rows[-1]["close"]; recent = rows[-14:]; pole = rows[-44:-14]
    if len(pole) < 20: return None
    pole_move = pct(max(r["close"] for r in pole[-5:]), min(r["close"] for r in pole[:15]))
    rh = max(r["high"] for r in recent); rl = min(r["low"] for r in recent)
    rr = pct(rh, rl); pullback = pct(rh, cur)
    compact = max(0, 25 - rr)*2.2
    score = 30 + min(pole_move, 35) + compact - max(0, pullback-8)*2
    if pole_move < 10 or rr > 16: score -= 20
    return setup("bull_flags", "Cờ tăng", score, rh, rl, rh, cur, "Cần có nhịp dẫn trước rõ và phần nghỉ không quá rộng.")

def detect_bull_pennant(rows):
    cur = rows[-1]["close"]; recent = rows[-12:]; prior = rows[-42:-12]
    if len(prior) < 20: return None
    pm = pct(max(r["close"] for r in prior[-5:]), min(r["close"] for r in prior[:15]))
    fr = max(r["high"] for r in recent[:6]) - min(r["low"] for r in recent[:6])
    lr = max(r["high"] for r in recent[-6:]) - min(r["low"] for r in recent[-6:])
    comp = 1 - (lr/fr) if fr > 0 else 0
    rh = max(r["high"] for r in recent); rl = min(r["low"] for r in recent)
    score = 35 + min(pm, 30) + clamp(comp*55, 0, 35) - max(0, pct(rh, rl)-14)*2
    if pm < 10: score -= 18
    return setup("bull_pennants", "Cờ đuôi nheo tăng", score, rh, rl, rh, cur, "Cần thấy biên dao động co lại thay vì chỉ đi ngang rộng.")

def detect_ascending_triangle(rows):
    cur = rows[-1]["close"]; window = rows[-45:]
    highs = [r["high"] for r in window]; lows = [r["low"] for r in window]
    resistance = sorted(highs)[int(len(highs)*0.8)]
    hs = pct(max(highs[-25:]), min(highs[-25:]))
    lr = pct(min(lows[-10:]), min(lows[:15]))
    dist = max(0.0, pct(resistance, cur))
    score = 45 + min(max(lr, 0), 18)*1.8 + max(0, 8-hs)*3 - dist*1.5
    return setup("triangles_ascending", "Tam giác tăng", score, resistance, min(lows[-20:]), resistance, cur, "Cần kháng cự đủ phẳng và đáy sau cao hơn đáy trước.")

def detect_falling_wedge(rows):
    cur = rows[-1]["close"]; window = rows[-40:]
    highs = [r["high"] for r in window]; lows = [r["low"] for r in window]
    hsl = slope(highs); lsl = slope(lows)
    ws = max(highs[:10]) - min(lows[:10]); we = max(highs[-10:]) - min(lows[-10:])
    nar = 1 - we/ws if ws > 0 else 0
    upper_now = highs[0] + hsl*(len(highs)-1)
    dist = max(0.0, pct(upper_now, cur)) if upper_now > 0 else None
    score = 40 + clamp(nar*60, 0, 35) + (12 if hsl < 0 and lsl < 0 else -15) - (dist or 0)*1.2
    return setup("wedges_falling", "Nêm giảm", score, upper_now, min(lows[-15:]), upper_now, cur, "Cần hai biên cùng dốc xuống và độ rộng thu hẹp.")

def detect_cup_with_handle(rows):
    if len(rows) < 75: return None
    cur = rows[-1]["close"]; window = rows[-90:]
    closes = [r["close"] for r in window]
    lh = max(closes[:30]); cl = min(closes[20:70]); rh = max(closes[55:])
    depth = pct(lh, cl); recovery = pct(rh, cl)
    handle = rows[-15:]
    hp = pct(max(r["high"] for r in handle), min(r["low"] for r in handle))
    conf = max(lh, rh)
    score = 35 + min(recovery, 35) + max(0, 35 - abs(depth-25)) - max(0, hp-16)*2
    if depth < 12 or depth > 50: score -= 18
    return setup("cup_with_handle", "Cốc tay cầm", score, conf, min(r["low"] for r in handle), conf, cur, "Mẫu dài, dễ nhiễu nếu tay cầm quá sâu hoặc hồi chưa đủ.")

def detect_rectangle_bottom(rows):
    cur = rows[-1]["close"]; window = rows[-35:]; prior = rows[-75:-35]
    high = max(r["high"] for r in window); low = min(r["low"] for r in window)
    rp = pct(high, low); pd = pct(prior[0]["close"], min(r["close"] for r in prior)) if prior else 0
    dist = max(0.0, pct(high, cur))
    score = 42 + max(0, 18 - abs(rp-12))*2 + min(max(pd, 0), 18) - dist
    return setup("rectangle_bottoms", "Chữ nhật đáy", score, high, low, high, cur, "Cần vùng đi ngang đủ rõ sau một nhịp giảm hoặc tích lũy.")

def detect_double_bottom(rows):
    cur = rows[-1]["close"]; window = rows[-65:]
    lows = [r["low"] for r in window]
    fi = min(range(0, 32), key=lambda idx: lows[idx])
    si = min(range(32, len(lows)), key=lambda idx: lows[idx])
    fl = lows[fi]; sl = lows[si]; lg = abs(pct(sl, fl))
    neck = max(r["high"] for r in window[fi:si+1])
    dist = max(0.0, pct(neck, cur)); sep = si - fi
    score = 48 + max(0, 8-lg)*4 + min(sep, 30)*0.5 - dist*1.5
    if sep < 12: score -= 15
    return setup("double_bottoms", "Hai đáy", score, neck, min(fl, sl), neck, cur, "Hai đáy cần tách nhau đủ xa và không lệch quá mạnh.")

def detect_measured_move_up(rows):
    cur = rows[-1]["close"]; first = rows[-70:-35]; pullback = rows[-35:-12]; recent = rows[-12:]
    if not first or not pullback: return None
    ll = min(r["low"] for r in first); lh = max(r["high"] for r in first)
    lm = pct(lh, ll); pl = min(r["low"] for r in pullback)
    rt = (lh-pl)/(lh-ll)*100 if lh > ll else 100
    conf = max(r["high"] for r in recent)
    score = 38 + min(lm, 30) + max(0, 30 - abs(rt-50)) - max(0, pct(conf, cur))*1.2
    if lm < 12 or rt < 25 or rt > 75: score -= 18
    return setup("measured_move_up", "Measured Move tăng", score, conf, pl, conf, cur, "Cần nhịp đầu rõ, pha điều chỉnh vừa phải và chưa bị rơi vào vùng răng cưa.")

DETECTORS = [detect_bull_flag, detect_bull_pennant, detect_ascending_triangle,
             detect_falling_wedge, detect_cup_with_handle, detect_rectangle_bottom,
             detect_double_bottom, detect_measured_move_up]

def scan_setups(rows):
    cands = [d(rows) for d in DETECTORS]
    cands = [c for c in cands if c]
    cands.sort(key=lambda c: (-float(c["completion_score"]), float(c.get("distance_to_confirmation_pct") or 999), c["pattern_name"]))
    return cands[:6]

CONTINUATION_PATTERNS = {"bull_flags", "bull_pennants", "high_tight_flags", "measured_move_up", "continuation_gaps", "rising_three_methods"}
ACCUMULATION_PATTERNS = {"triangles_ascending", "triangles_symmetrical", "rectangle_bottoms", "cup_with_handle",
                         "double_bottoms_adam_adam", "double_bottoms_adam_eve", "double_bottoms_eve_adam",
                         "double_bottoms_eve_eve", "triple_bottoms", "pipe_bottoms", "rounding_bottoms"}

def pattern_family(pid):
    if pid in CONTINUATION_PATTERNS: return "trend_following"
    if pid in ACCUMULATION_PATTERNS: return "accumulation_breakout"
    if "bottom" in pid or "valleys" in pid: return "reversal_or_recovery"
    if "top" in pid or "peaks" in pid: return "defensive_caution"
    return "mixed"

def estimate_archetype(setups, hvb):
    families = [pattern_family(s["pattern_id"]) for s in setups]
    hv_label = hvb.get("post_high_volume_label", "") if hvb else ""
    if not setups:
        return {"primary": "no_current_setup", "reader_note": "Không có setup chiều tăng rõ trong các mẫu heuristic; đọc theo từng phiên."}
    if "trend_following" in families:
        return {"primary": "trend_following", "reader_note": "Setup hiện tại nghiêng tiếp diễn; đọc ưu tiên theo sức giữ xu hướng."}
    if "accumulation_breakout" in families:
        return {"primary": "accumulation_breakout", "reader_note": "Setup hiện tại nghiêng tích lũy; đọc kỹ ở phiên xác nhận thoát nền."}
    if "suy yếu" in hv_label:
        return {"primary": "trap_prone", "reader_note": "Hành vi sau volume cao suy yếu; thận trọng với phá vỡ giả."}
    return {"primary": "mixed", "reader_note": "Setup hiện tại pha trộn; đọc theo từng cấu trúc cụ thể."}

def run_profile():
    rows = load_csv(f"{DATA}/price_daily.csv")
    vni = load_csv(f"{DATA}/price_daily_vnindex.csv")
    vn30 = load_csv(f"{DATA}/price_daily_vn30.csv")
    overview = json.load(open(f"{DATA}/overview.json"))

    # add value (đồng) + range_pct to each row
    for r in rows:
        r["value"] = r["close"] * r["volume"] * 1000.0   # nghìn đồng → đồng
        r["range_pct"] = (r["high"]-r["low"])/r["close"]*100 if r["close"] else None
    for r in vni:
        r["value"] = r["close"]*r["volume"]  # index points × shares; keep as-is for index
        r["range_pct"] = (r["high"]-r["low"])/r["close"]*100 if r["close"] else None
    for r in vn30:
        r["value"] = r["close"]*r["volume"]
        r["range_pct"] = (r["high"]-r["low"])/r["close"]*100 if r["close"] else None

    if len(rows) < 60:
        return {"error": "Không đủ dữ liệu (cần ≥60 phiên)", "symbol": "KDH"}

    benchmarks = {"VNINDEX": vni, "VN30": vn30}

    profile = {
        "schema": "vn-technical-profile-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "language_policy": "neutral_descriptive_non_advice",
        "symbol": "KDH",
        "company_name": overview.get("organ_name"),
        "exchange": "HOSE",
        "sector": overview.get("sector"),
        "data_source": "vnstock (VCI)",
        "data_period": f"{rows[0]['date']} to {rows[-1]['date']}",
        "stock_identity": {"symbol": "KDH", "sample_size": len(rows)},
        "price_behavior_profile": price_behavior_profile(rows),
        "volatility_profile": volatility_profile(rows),
        "drawdown_profile": drawdown_profile(rows),
        "liquidity_profile": liquidity_profile(rows),
        "return_distribution_profile": return_distribution_profile(rows),
        "tail_risk_profile": tail_risk_profile(rows),
        "liquidity_risk_profile": liquidity_risk_profile(rows),
        "volume_price_profile": volume_price_profile(rows),
        "volume_price_confirmation_profile": vpci_profile(rows),
        "money_flow_pressure_profile": money_flow_profile(rows),
        "effort_result_profile": effort_result_profile(rows),
        "high_volume_behavior_profile": high_volume_behavior_profile(rows),
        "pvi_nvi_participation_profile": pvi_nvi_profile(rows),
        "volume_at_price_profile": volume_at_price_profile(rows),
    }
    rs = relative_strength_profile(rows, vni, benchmarks)
    profile.update(rs)
    profile["regime_profile"] = regime_profile(rows, vni)

    setups = scan_setups(rows)
    profile["setups"] = setups
    profile["archetype"] = estimate_archetype(setups, profile["high_volume_behavior_profile"])

    profile["non_conclusion"] = [
        "Không kết luận đây là khuyến nghị hoặc lời gọi giao dịch.",
        "Tỷ lệ trong quá khứ không đảm bảo lặp lại trong tương lai.",
        "Các cửa sổ quan sát chồng lấp, không phải quan sát độc lập.",
        "Dữ liệu giá chưa điều chỉnh corporate actions được kiểm chứng đầy đủ.",
    ]
    profile["data_transparency"] = {
        "price_unit": "VND (vnstock trả nghìn đồng, giá trị giao dịch = close × volume × 1000)",
        "timeframe": "daily bars",
        "sample_size_days": len(rows),
        "benchmarks": ["VNINDEX", "VN30"],
        "language_check": "neutral_descriptive_non_advice — ngôn ngữ mô tả trung tính, không đưa lời khuyên giao dịch",
    }
    return profile

# =====================================================================
if __name__ == "__main__":
    active = run_active()
    profile = run_profile()
    with open(f"{DATA}/technical_active.json", "w") as f:
        json.dump(active, f, ensure_ascii=False, indent=2)
    with open(f"{DATA}/technical_profile.json", "w") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    # summary to stdout
    print("=== ACTIVE ===")
    print(f"ticker={active['ticker']}  price={active['price_current_vnd']:,.0f} VND  ({active['latest_date']})")
    print(f"1y perf={active['performance_1y_pct']}%  high52w={active['high_52w_vnd']:,.0f}  low52w={active['low_52w_vnd']:,.0f}  annVol={active['annualized_volatility_pct']}%")
    ind = active["indicators"]
    print(f"MA10={ind['ma10_k']}  MA20={ind['ma20_k']}  MA50={ind['ma50_k']}  RSI={ind['rsi14']}  MACD={ind['macd']} signal={ind['signal']} ({ind['macd_trend']})  BBpos={ind['bollinger']['bb_position_pct']}%")
    c = active["correlation"]
    print(f"Beta VNI={c['beta_vnindex']}  Beta VN30={c['beta_vn30']}  Corr VNI={c['corr_vnindex']}  Alpha1y={c['alpha_1y_pct']}%  outperform={c['outperform_market']}")
    print(f"Patterns: {len(active['patterns_detected'])} detected")
    for p in active["patterns_detected"]:
        print(f"  - {p}")
    print(f"Divergence: has={active['divergence']['has_divergence']}  note={active['divergence']['note']}")
    print(f"Tech Score = {active['tech_score']}  ->  {active['verdict']}")
    print(f"  breakdown: {active['tech_score_breakdown']}")
    print()
    print("=== PROFILE ===")
    print(f"symbol={profile['symbol']}  sample={profile['stock_identity']['sample_size']} days")
    pb = profile["price_behavior_profile"]
    print(f"latest_close={pb['latest_close']}  return 1m/3m/6m/1y = {pb['return_1m_pct']}/{pb['return_3m_pct']}/{pb['return_6m_pct']}/{pb['return_1y_pct']}%")
    print(f"distance from 52w high = {pb['distance_from_52w_high_pct']}%  from low = {pb['distance_from_52w_low_pct']}%")
    v = profile["volatility_profile"]
    print(f"HV20={v['hv20_pct']}%(pct{v['hv20_percentile_1y']})  HV60={v['hv60_pct']}%(pct{v['hv60_percentile_1y']})  HV252={v['hv252_pct']}%")
    d = profile["drawdown_profile"]
    print(f"current DD={d['current_drawdown_pct']}%  maxDD={d['max_drawdown_pct']}%  underwater={d['current_underwater_days']}d  episodes={d['episode_count']}")
    print(f"VPCI label={profile['volume_price_confirmation_profile']['confirmation_label']}  latest={profile['volume_price_confirmation_profile']['vpci_latest']}")
    print(f"MoneyFlow label={profile['money_flow_pressure_profile']['money_flow_label']}  CMF20={profile['money_flow_pressure_profile']['cmf_20d']}  CMF60={profile['money_flow_pressure_profile']['cmf_60d']}")
    print(f"EffortResult label={profile['effort_result_profile']['effort_result_label']}")
    print(f"HVB label={profile['high_volume_behavior_profile']['post_high_volume_label']}  events_1y={profile['high_volume_behavior_profile']['event_count_1y']}")
    print(f"PVINVI label={profile['pvi_nvi_participation_profile']['participation_regime_label']}  PVI={profile['pvi_nvi_participation_profile']['pvi_latest']}  NVI={profile['pvi_nvi_participation_profile']['nvi_latest']}")
    print(f"VAP label={profile['volume_at_price_profile']['acceptance_label']}  POC bin={profile['volume_at_price_profile']['point_of_control_bin_index']}")
    db = profile["dynamic_beta_profile"]
    print(f"Beta VNI 60/120/252 = {db['beta_60']}/{db['beta_120']}/{db['beta_252']}")
    cp = profile["correlation_profile"]
    print(f"Corr VNI 252={cp['corr_252']}  R2={cp['r2_252']}  DDsim={cp['drawdown_similarity_252']}")
    print(f"Regime: {profile['regime_profile']['current_market_regime']}")
    print(f"Setups ({len(profile['setups'])}):")
    for s in profile["setups"]:
        print(f"  - {s['pattern_name']} ({s['pattern_id']}) score={s['completion_score']} status={s['setup_status']} dist={s['distance_to_confirmation_pct']}%")
    print(f"Archetype: {profile['archetype']['primary']}  -- {profile['archetype']['reader_note']}")
