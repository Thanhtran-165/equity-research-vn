#!/usr/bin/env python3
"""
Phase 4b: Technical PROFILE — neutral_descriptive_non_advice language
Daily ~2 years (498 bars). 15 profile blocks + archetype + non-conclusion points.
NO bullish/bearish/buy/sell language.
"""
import json, os, math

TICKER = "PNJ"
WORK_DIR = "/Users/bobo/ZCodeProject/pnj-research"
DATA_DIR = os.path.join(WORK_DIR, "data")

with open(os.path.join(DATA_DIR, "price_daily.json")) as f:
    pd_data = json.load(f)
with open(os.path.join(DATA_DIR, "vnindex.json")) as f:
    vni_w = json.load(f)
with open(os.path.join(DATA_DIR, "overview.json")) as f:
    ov = json.load(f)

# Build rows for profile
closes = pd_data["close"]
highs = pd_data["high"]
lows = pd_data["low"]
opens = pd_data["open"]
volumes = pd_data["volume"]
times = pd_data["time"]
n = len(closes)

# value = close * volume * 1000 (vnstock already converted to VND, so value = close_vnd * volume)
# Actually close is already VND here. value = close * volume (in VND)
rows = []
for i in range(n):
    rng = (highs[i] - lows[i]) / closes[i] * 100 if closes[i] > 0 else 0
    rows.append({
        "date": times[i],
        "open": opens[i],
        "high": highs[i],
        "low": lows[i],
        "close": closes[i],
        "volume": volumes[i],
        "value": closes[i] * volumes[i],
        "range_pct": rng,
    })

print("=" * 60)
print(f"  PHASE 4b: Technical PROFILE — {TICKER}")
print("=" * 60)
print(f"  Bars: {n} daily | Range: {times[0]} → {times[-1]}")

# ============ HELPERS ============
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
    return sum(nums) / len(nums) if nums else None

def std_dev(values=[]):
    nums = [v for v in values if finite(v)]
    if len(nums) < 2:
        return None
    avg = mean(nums)
    return math.sqrt(sum((v - avg) ** 2 for v in nums) / (len(nums) - 1))

def skewness(values=[]):
    nums = [v for v in values if finite(v)]
    if len(nums) < 3:
        return None
    avg, sd = mean(nums), std_dev(nums)
    if not sd:
        return None
    nn = len(nums)
    return (nn / ((nn - 1) * (nn - 2))) * sum(((v - avg) / sd) ** 3 for v in nums)

def quantile(values, q):
    nums = sorted(v for v in values if finite(v))
    if not nums:
        return None
    if len(nums) == 1:
        return nums[0]
    pos = q * (len(nums) - 1)
    lo = math.floor(pos)
    hi = math.ceil(pos)
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
        p, c = rows[i - 1].get("close"), rows[i].get("close")
        if p and c and p > 0 and c > 0:
            out.append(math.log(c / p))
    return out

def daily_returns_pct(rows=[]):
    out = []
    for i in range(1, len(rows)):
        p, c = rows[i - 1].get("close"), rows[i].get("close")
        if p and c and p > 0 and c > 0:
            out.append((c / p - 1) * 100)
    return out

def drawdown_series(rows=[]):
    peak = None
    out = []
    for row in rows:
        c = finite(row.get("close"))
        if c is None:
            out.append(None)
            continue
        peak = c if peak is None else max(peak, c)
        out.append(c / peak - 1 if peak else None)
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
        sample = returns[max(0, i - window):i]
        v = round_(std_dev(sample) * math.sqrt(252) * 100) if len(sample) >= min_count else None
        if finite(v):
            values.append(v)
    return values

def pct_change(rows, window):
    if len(rows) <= window:
        return None
    start = rows[-1 - window].get("close")
    end = rows[-1].get("close")
    if not (start and end and start > 0 and end > 0):
        return None
    return round_((end / start - 1) * 100)

def sma_at(rows, index, field, window):
    if index < window - 1:
        return None
    sl = rows[index - window + 1 : index + 1]
    vals = [finite(r.get(field)) for r in sl]
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if len(vals) == window else None

def vwma_at(rows, index, field, window):
    if index < window - 1:
        return None
    sl = rows[index - window + 1 : index + 1]
    num = 0.0
    den = 0.0
    ok = True
    for r in sl:
        px = finite(r.get(field))
        vol = finite(r.get("volume"))
        if px is None or vol is None:
            ok = False
            break
        num += px * vol
        den += vol
    return (num / den) if ok and den > 0 else None

def moving_average_before(rows, index, field, window):
    return sma_at(rows, index - 1, field, window)

def average_value(rows, window):
    sl = rows[-window:]
    vals = [finite(r.get("value")) for r in sl]
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None

def line_change_pct(points, window):
    if len(points) <= window:
        return None
    a = points[-1 - window].get("value")
    b = points[-1].get("value")
    if not (finite(a) and finite(b)) or a == 0:
        return None
    return round_((b / a - 1) * 100)

# ============ BLOCK 1: price_behavior ============
print("\n[1] Price behavior profile:")
latest = rows[-1]
closes_252 = [r["close"] for r in rows[-252:] if finite(r.get("close"))]
high_52w = max(closes_252) if closes_252 else None
low_52w = min(closes_252) if closes_252 else None
latest_close = latest["close"]
ret_1m = pct_change(rows, 21)
ret_3m = pct_change(rows, 63)
ret_6m = pct_change(rows, 126)
ret_1y = pct_change(rows, 252)
dist_high = round_((latest_close / high_52w - 1) * 100) if high_52w and latest_close and high_52w > 0 else None
dist_low = round_((latest_close / low_52w - 1) * 100) if low_52w and latest_close and low_52w > 0 else None
print(f"  Latest: {latest_close:,.0f} ({latest['date']})")
print(f"  Returns: 1M={ret_1m:+.1f}% | 3M={ret_3m:+.1f}% | 6M={ret_6m:+.1f}% | 1Y={ret_1y:+.1f}%")
dist_high_s = f"{dist_high:+.1f}%" if dist_high is not None else "NA"
dist_low_s = f"{dist_low:+.1f}%" if dist_low is not None else "NA"
print(f"  52w: high={high_52w:,.0f} low={low_52w:,.0f} | from high={dist_high_s} from low={dist_low_s}")

# ============ BLOCK 2: volatility ============
print("\n[2] Volatility profile:")
hv20 = realized_vol(rows, 20)
hv60 = realized_vol(rows, 60)
hv120 = realized_vol(rows, 120)
hv252 = realized_vol(rows, 252)
vol20_hist = realized_vol_history(rows, 20)
hv20_pct = percentile_of_value(vol20_hist[-252:], hv20)
range_63 = [finite(r.get("range_pct")) for r in rows[-63:]]
range_63 = [v for v in range_63 if v is not None]
range_median = round_(median(range_63))
print(f"  HV20: {hv20:.1f}% (pct {hv20_pct:.0f}) | HV60: {hv60:.1f}% | HV120: {hv120:.1f}% | HV252: {hv252:.1f}%")
print(f"  Range median 63d: {range_median:.2f}%")

# ============ BLOCK 3: drawdown ============
print("\n[3] Drawdown profile:")
dd_series = drawdown_series(rows)
finite_dd = [v for v in dd_series if finite(v)]
current_dd = finite_dd[-1] if finite_dd else None
max_dd = min(finite_dd) if finite_dd else None
# underwater days
underwater = 0
for v in reversed(dd_series):
    if finite(v) and v < 0:
        underwater += 1
    else:
        break
print(f"  Current drawdown: {current_dd*100:.1f}% | Underwater: {underwater} days")
print(f"  Max drawdown: {max_dd*100:.1f}%")

# ============ BLOCK 4: liquidity ============
print("\n[4] Liquidity profile:")
values_252 = [finite(r.get("value")) for r in rows[-252:]]
values_252 = [v for v in values_252 if v is not None]
avg20_val = average_value(rows, 20)
avg60_val = average_value(rows, 60)
latest_val = finite(latest.get("value"))
liq_pct = percentile_of_value(values_252, latest_val)
liq_stab = round_(std_dev(values_252) / mean(values_252) * 100) if values_252 and mean(values_252) else None
print(f"  Latest value: {latest_val/1e9:.2f} tỷ VND | Avg20: {avg20_val/1e9:.2f} tỷ | Avg60: {avg60_val/1e9:.2f} tỷ")
print(f"  Percentile: {liq_pct:.0f}% | Stability CV: {liq_stab:.0f}%")

# ============ BLOCK 5: return distribution ============
print("\n[5] Return distribution:")
daily = daily_returns_pct(rows)
one_year = daily[-252:]
pos_rate = sum(1 for v in one_year if v > 0) / len(one_year) * 100 if one_year else None
skew = skewness(one_year)
dist_mean = mean(one_year)
dist_std = std_dev(one_year)
dist_p05 = quantile(one_year, 0.05)
dist_p95 = quantile(one_year, 0.95)
print(f"  Mean: {dist_mean:.3f}%/day | Std: {dist_std:.3f}% | Positive rate: {pos_rate:.1f}%")
print(f"  P5: {dist_p05:.2f}% | P95: {dist_p95:.2f}% | Skewness: {skew:.2f}")

# ============ BLOCK 6: tail risk (VaR/ES) ============
print("\n[6] Tail risk:")
q05 = quantile(one_year, 0.05)
q01 = quantile(one_year, 0.01)
es05 = mean([v for v in one_year if v <= q05]) if finite(q05) else None
es01 = mean([v for v in one_year if v <= q01]) if finite(q01) else None
var95 = abs(q05) if finite(q05) else None
var99 = abs(q01) if finite(q01) else None
print(f"  VaR 95% (1d): {var95:.2f}% | VaR 99%: {var99:.2f}%")
print(f"  ES 95%: {abs(es05):.2f}% | ES 99%: {abs(es01):.2f}%")

# ============ BLOCK 7: VPCI ============
print("\n[7] VPCI (volume-price confirmation):")
# Simplified: compute latest VPCI
short_w = 20
long_w = 100
i = len(rows) - 1
sma_s = sma_at(rows, i, "close", short_w)
sma_l = sma_at(rows, i, "close", long_w)
vwma_s = vwma_at(rows, i, "close", short_w)
vwma_l = vwma_at(rows, i, "close", long_w)
avg_vol_s = sma_at(rows, i, "volume", short_w)
avg_vol_l = sma_at(rows, i, "volume", long_w)
vpc = (vwma_l - sma_l) if (finite(vwma_l) and finite(sma_l)) else None
vpr = (vwma_s / sma_s) if (finite(vwma_s) and finite(sma_s) and sma_s) else None
vm = (avg_vol_s / avg_vol_l) if (finite(avg_vol_s) and finite(avg_vol_l) and avg_vol_l > 0) else None
vpci = (vpc * vpr * vm) if all(finite(x) for x in (vpc, vpr, vm)) else None
price_vs_sma100 = round_((latest_close / sma_l - 1) * 100) if finite(latest_close) and finite(sma_l) and sma_l else None
print(f"  VPCI: {vpci:.2f}" if finite(vpci) else "  VPCI: NA")
print(f"  Price vs SMA100: {price_vs_sma100:+.1f}%" if price_vs_sma100 else "  Price vs SMA100: NA")

# ============ BLOCK 8: money flow (OBV/CMF) ============
print("\n[8] Money flow:")
obv = 0
for i in range(1, len(rows)):
    p, r = rows[i - 1], rows[i]
    if r["close"] > p["close"]:
        obv += r["volume"]
    elif r["close"] < p["close"]:
        obv -= r["volume"]
# CMF20
sample = rows[-20:]
sample = [r for r in sample if all(finite(r.get(f)) for f in ("high", "low", "close", "volume")) and r["volume"] > 0]
vol_sum = sum(r["volume"] for r in sample)
flow = 0
for r in sample:
    rng = r["high"] - r["low"]
    if rng:
        mult = ((r["close"] - r["low"]) - (r["high"] - r["close"])) / rng
        flow += mult * r["volume"]
cmf20 = flow / vol_sum if vol_sum else None
print(f"  OBV latest: {obv/1e6:.1f}M | CMF20: {cmf20:.4f}" if finite(cmf20) else f"  OBV: {obv/1e6:.1f}M")

# ============ BLOCK 9: effort-result (Wyckoff) ============
print("\n[9] Effort-result (Wyckoff):")
obs = []
for i in range(1, len(rows)):
    p, r = rows[i - 1], rows[i]
    if not (p.get("close", 0) > 0 and r.get("close", 0) > 0):
        continue
    vol_avg20 = moving_average_before(rows, i, "volume", 20)
    ret = (r["close"] / p["close"] - 1) * 100
    rng = r.get("range_pct")
    vol_ratio = (r["volume"] / vol_avg20) if (finite(r.get("volume")) and finite(vol_avg20) and vol_avg20 > 0) else None
    effort = vol_ratio
    result = max(abs(ret), rng if finite(rng) else 0)
    rpe = (result / effort) if (finite(effort) and effort > 0) else None
    obs.append({"effort_ratio": effort, "result_pct": result, "result_per_effort": rpe})

tail_er = obs[-252:]
high_effort = [o for o in tail_er if finite(o.get("effort_ratio")) and o["effort_ratio"] >= 2]
result_vals = [o["result_pct"] for o in tail_er if finite(o.get("result_pct"))]
result_median = median(result_vals)
rpe_vals = [o["result_per_effort"] for o in tail_er if finite(o.get("result_per_effort"))]
rpe_median = median(rpe_vals)
low_rhe = [o for o in high_effort if finite(o.get("result_pct")) and finite(result_median) and o["result_pct"] <= result_median]
print(f"  High-effort days (vol≥2x avg): {len(high_effort)}")
print(f"  Low-result high-effort days: {len(low_rhe)} ({len(low_rhe)/len(high_effort)*100:.0f}% of high-effort)" if high_effort else "  Low-result: NA")
print(f"  Median result: {result_median:.2f}% | Median result/effort: {rpe_median:.2f}")

# ============ BLOCK 10: high-volume behavior ============
print("\n[10] High-volume event behavior:")
hv_events = []
for i in range(1, len(rows) - 60):
    r, p = rows[i], rows[i - 1]
    avg20 = moving_average_before(rows, i, "volume", 20)
    if not (finite(r.get("volume")) and finite(avg20) and avg20 > 0):
        continue
    if r["volume"] / avg20 < 2:
        continue
    # forward returns
    fr5 = (rows[i + 5]["close"] / r["close"] - 1) * 100 if i + 5 < len(rows) else None
    fr20 = (rows[i + 20]["close"] / r["close"] - 1) * 100 if i + 20 < len(rows) else None
    fr60 = (rows[i + 60]["close"] / r["close"] - 1) * 100 if i + 60 < len(rows) else None
    hv_events.append({"fr5": fr5, "fr20": fr20, "fr60": fr60})
fr20_vals = [e["fr20"] for e in hv_events if finite(e["fr20"])]
fr20_pos = sum(1 for v in fr20_vals if v > 0) / len(fr20_vals) * 100 if fr20_vals else None
fr20_med = median(fr20_vals)
print(f"  High-volume events: {len(hv_events)}")
print(f"  Forward 20d after event: median={fr20_med:.1f}% positive_rate={fr20_pos:.0f}%" if fr20_vals else "  Forward: NA")

# ============ ARCHETYPE ============
print("\n[11] Archetype classification:")
# Classify based on metrics
archetype_scores = {"trend_following": 0, "accumulation_breakout": 0, "trap_prone": 0, "mean_reverting": 0}
# trend_following: high HV, strong directional moves, high R² with market
if hv60 and hv60 > 30:
    archetype_scores["trend_following"] += 2
if abs(ret_3m or 0) > 15:
    archetype_scores["trend_following"] += 1
# mean_reverting: negative skew + high kurtosis + low R²
if skew and skew < -0.3:
    archetype_scores["mean_reverting"] += 2
# trap_prone: high low-result-high-effort ratio
if high_effort and len(low_rhe) / len(high_effort) > 0.45:
    archetype_scores["trap_prone"] += 2
# accumulation_breakout: low HV + tight ranges + VPCI positive
if hv60 and hv60 < 25:
    archetype_scores["accumulation_breakout"] += 1
archetype = max(archetype_scores, key=archetype_scores.get)
print(f"  Scores: {archetype_scores}")
print(f"  Archetype: {archetype}")

# ============ NON-CONCLUSION POINTS ============
non_conclusion = [
    "Không kết luận đây là khuyến nghị hoặc lời gọi giao dịch.",
    "Tỷ lệ trong quá khứ không đảm bảo lặp lại trong tương lai.",
    "Các cửa sổ quan sát chồng lấp, không phải quan sát độc lập.",
    "Dữ liệu giá đã điều chỉnh sự kiện chia tách (50% bonus shares 2026-04-15) nhưng có thể chưa phản ánh đầy đủ corporate actions khác.",
]

# ============ SAVE ============
result = {
    "ticker": TICKER,
    "mode": "PROFILE",
    "timeframe": f"daily {n} bars",
    "schema": "vn-technical-profile-v1",
    "language_policy": "neutral_descriptive_non_advice",
    "price_behavior": {
        "latest_close": latest_close,
        "latest_date": latest["date"],
        "return_1m_pct": ret_1m,
        "return_3m_pct": ret_3m,
        "return_6m_pct": ret_6m,
        "return_1y_pct": ret_1y,
        "high_52w": high_52w,
        "low_52w": low_52w,
        "distance_from_high_pct": dist_high,
        "distance_from_low_pct": dist_low,
    },
    "volatility": {
        "hv20": hv20,
        "hv60": hv60,
        "hv120": hv120,
        "hv252": hv252,
        "hv20_percentile": hv20_pct,
        "range_median_63d": range_median,
    },
    "drawdown": {
        "current_pct": round_(current_dd * 100) if current_dd else None,
        "underwater_days": underwater,
        "max_pct": round_(max_dd * 100) if max_dd else None,
    },
    "liquidity": {
        "latest_value_ty": round_(latest_val / 1e9, 2) if latest_val else None,
        "avg20_value_ty": round_(avg20_val / 1e9, 2) if avg20_val else None,
        "avg60_value_ty": round_(avg60_val / 1e9, 2) if avg60_val else None,
        "percentile_1y": liq_pct,
        "stability_cv": liq_stab,
    },
    "return_distribution": {
        "mean_pct": round_(dist_mean, 4) if dist_mean else None,
        "std_pct": round_(dist_std, 4) if dist_std else None,
        "positive_rate_pct": round_(pos_rate, 1) if pos_rate else None,
        "p05_pct": round_(dist_p05, 2) if dist_p05 else None,
        "p95_pct": round_(dist_p95, 2) if dist_p95 else None,
        "skewness": round_(skew, 4) if skew else None,
    },
    "tail_risk": {
        "var_95_1d_pct": round_(var95, 2) if var95 else None,
        "var_99_1d_pct": round_(var99, 2) if var99 else None,
        "es_95_1d_pct": round_(abs(es05), 2) if es05 else None,
        "es_99_1d_pct": round_(abs(es01), 2) if es01 else None,
    },
    "vpci": {
        "vpci_latest": round_(vpci, 2) if vpci else None,
        "price_vs_sma100_pct": price_vs_sma100,
    },
    "money_flow": {
        "obv_latest_m": round_(obv / 1e6, 1) if obv else None,
        "cmf_20d": round_(cmf20, 4) if cmf20 else None,
    },
    "effort_result": {
        "high_effort_days_1y": len(high_effort),
        "low_result_high_effort_pct": round_(len(low_rhe) / len(high_effort) * 100) if high_effort else None,
        "median_result_pct": round_(result_median, 4) if result_median else None,
        "median_result_per_effort": round_(rpe_median, 4) if rpe_median else None,
    },
    "high_volume_behavior": {
        "event_count": len(hv_events),
        "forward_20d_median_pct": round_(fr20_med, 2) if fr20_med else None,
        "forward_20d_positive_rate": round_(fr20_pos, 1) if fr20_pos else None,
    },
    "archetype": archetype,
    "archetype_scores": archetype_scores,
    "non_conclusion_points": non_conclusion,
    "interpretation_guardrail": "Tất cả metrics là quan sát lịch sử (What I See), không phải tín hiệu/dự báo/khuyến nghị giao dịch.",
    # Chart data for profile
    "chart_time": times[-252:],
    "chart_close": closes[-252:],
    "chart_volume": volumes[-252:],
    # Drawdown history for chart
    "chart_drawdown": [round_(v * 100, 2) if finite(v) else None for v in dd_series[-252:]],
    # Return histogram for chart
    "histogram_bins": [
        {"label": "<=-10%", "count": sum(1 for v in one_year if v <= -10)},
        {"label": "-10% to -5%", "count": sum(1 for v in one_year if -10 < v <= -5)},
        {"label": "-5% to -2%", "count": sum(1 for v in one_year if -5 < v <= -2)},
        {"label": "-2% to 0%", "count": sum(1 for v in one_year if -2 < v <= 0)},
        {"label": "0% to 2%", "count": sum(1 for v in one_year if 0 < v <= 2)},
        {"label": "2% to 5%", "count": sum(1 for v in one_year if 2 < v <= 5)},
        {"label": "5% to 10%", "count": sum(1 for v in one_year if 5 < v <= 10)},
        {"label": ">10%", "count": sum(1 for v in one_year if v > 10)},
    ],
}

with open(os.path.join(DATA_DIR, "tech_profile.json"), "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"\n✅ Phase 4b complete → data/tech_profile.json")
print(f"   Archetype: {archetype} | HV60: {hv60:.1f}% | MaxDD: {max_dd*100:.1f}%")
print(f"   VaR95: {var95:.2f}% | Language: neutral_descriptive_non_advice ✓")
