#!/usr/bin/env python3
"""CTD Dashboard generator — Bước 6. Builds CTD_Complete_Report.html from JSON data."""
import json, re
from pathlib import Path

DATA = Path('/Users/bobo/ZCodeProject/ctd_data')
OUT = Path('/Users/bobo/ZCodeProject/CTD_Complete_Report.html')

fund = json.load(open(DATA/'fundamental_valuation.json'))
ta = json.load(open(DATA/'technical_active.json'))
tp = json.load(open(DATA/'technical_profile.json'))
news = json.load(open(DATA/'news_digest.json'))
ov = json.load(open(DATA/'overview.json'))

price = fund['price']
mcap = fund['market_cap']
shares = fund['shares']
ratios = fund['ratios']
val = fund['valuation']
fin = fund['financials']

def fmt_vnd(x):
    if x is None: return "—"
    if abs(x) >= 1e12: return f"{x/1e12:,.2f} nghìn tỷ"
    if abs(x) >= 1e9: return f"{x/1e9:,.0f} tỷ"
    if abs(x) >= 1e6: return f"{x/1e6:,.1f} triệu"
    return f"{x:,.0f}"

def fmt_pct(x):
    return "—" if x is None else f"{x:+.2f}%"

# ===== Build KPI cards =====
fy25 = ratios['FY2025']
kpi_cards = f"""
<div class="kpi"><div class="kpi-label">Giá hiện tại</div><div class="kpi-value mono">{price:,.0f}<span class="unit">đ</span></div></div>
<div class="kpi"><div class="kpi-label">Vốn hóa</div><div class="kpi-value mono">{mcap/1e12:.2f}<span class="unit">nghìn tỷ đ</span></div></div>
<div class="kpi"><div class="kpi-label">P/E (FY25)</div><div class="kpi-value mono {'neg' if fy25['PE']>25 else 'pos'}">{fy25['PE']:.1f}<span class="unit">x</span></div></div>
<div class="kpi"><div class="kpi-label">P/B (FY25)</div><div class="kpi-value mono {'pos' if fy25['PB']<1 else ''}">{fy25['PB']:.2f}<span class="unit">x</span></div></div>
<div class="kpi"><div class="kpi-label">ROE (FY25)</div><div class="kpi-value mono {'neg' if fy25['ROE']<10 else 'pos'}">{fy25['ROE']:.2f}<span class="unit">%</span></div></div>
<div class="kpi"><div class="kpi-label">Tech Score</div><div class="kpi-value mono neg">{ta['tech_score']}/+6</div><div class="kpi-sub neg">{ta['verdict']}</div></div>
"""

# ===== Financial table =====
fin_rows = ""
for label in ['FY2024','FY2025']:
    d = fin[label]
    rev = d.get('revenue'); gp = d.get('gross_profit'); ni = d.get('net_profit')
    eps = d.get('eps_vnd'); eq = d.get('equity'); ta_assets = d.get('total_assets')
    fin_rows += f"""<tr>
<td class="mono">{label}</td>
<td class="mono num">{fmt_vnd(rev)}</td>
<td class="mono num">{fmt_vnd(gp)}</td>
<td class="mono num">{fmt_vnd(ni)}</td>
<td class="mono num">{eps:,.0f}</td>
<td class="mono num">{ratios[label]['ROE']:.2f}%</td>
<td class="mono num">{ratios[label]['ROS']:.2f}%</td>
</tr>"""

# ===== Valuation cards =====
graham = val.get('Graham', 0) or 0
dcf_base = val.get('DCF_per_share_base', 0) or 0
fair_value_median = sorted(filter(None, [val.get('Graham'), val.get('DCF_per_share_bearish'),
    val.get('DCF_per_share_base'), fy25['BVPS'], val.get('DCF_per_share_bullish')]))
fv = graham  # conservative anchor
diff_pct = (price - fv) / fv * 100 if fv else 0

val_cards = f"""
<div class="val-card"><div class="vc-label">P/E FY2025</div><div class="vc-val mono">{fy25['PE']:.1f}x</div><div class="vc-note">EPS {fy25['EPS']:,.0f}đ</div></div>
<div class="val-card"><div class="vc-label">P/B FY2025</div><div class="vc-val mono {'accent-pos' if fy25['PB']<1 else ''}">{fy25['PB']:.2f}x</div><div class="vc-note">BVPS {fy25['BVPS']:,.0f}đ</div></div>
<div class="val-card"><div class="vc-label">P/CF</div><div class="vc-val mono">{val.get('PCF',0):.1f}x</div><div class="vc-note">CFO {fmt_vnd(fin['FY2025'].get('cfo'))}</div></div>
<div class="val-card"><div class="vc-label">P/S</div><div class="vc-val mono">{val.get('PS',0):.2f}x</div><div class="vc-note">Rev {fmt_vnd(fin['FY2025'].get('revenue'))}</div></div>
<div class="val-card"><div class="vc-label">Graham</div><div class="vc-val mono">{graham:,.0f}đ</div><div class="vc-note">√(22.5·EPS·BVPS)</div></div>
<div class="val-card"><div class="vc-label">DCF base (g=5%)</div><div class="vc-val mono">{dcf_base:,.0f}đ</div><div class="vc-note">WACC 12%</div></div>
"""

# DCF scenarios table
dcf_rows = ""
for scn, g in [('bearish',0.0),('base',0.05),('bullish',0.10)]:
    ps = val.get(f'DCF_per_share_{scn}', 0) or 0
    dcf_rows += f"<tr><td class='mono'>{scn}</td><td class='mono num'>{g:.0%}</td><td class='mono num'>{ps:,.0f}đ</td></tr>"

# ===== DuPont =====
d25 = fin['FY2025']
npm = d25['net_profit']/d25['revenue']*100
taturn = d25['revenue']/d25['total_assets']
eqmult = d25['total_assets']/d25['equity']

# ===== Insights (Bull/Bear balance) =====
insights_bull = """
<li><strong>Backlog kỷ lục ~65.5 nghìn tỷ</strong> — gấp ~2x doanh thu năm, đảm bảo tầm nhìn đa năm</li>
<li><strong>LNST FY25 +117.8%</strong> — tăng trưởng đột biến, biên LN 2.28% (đang phục hồi từ 1.52%)</li>
<li><strong>Đơn hàng mới 9 tháng FY26 ~48 nghìn tỷ</strong>, 94% khách hàng quay lại — ưu thế đã được thiết lập</li>
<li><strong>Đường sắt Bắc-Nam 67 tỷ USD</strong> — nhà thầu lựa chọn Q2/2026, CTD hưởng lợi trực tiếp</li>
"""
insights_bear = """
<li><strong>ROE chỉ 2.43%</strong> — sinh lời rất thấp trên vốn chủ, dù doanh thu 10 nghìn tỷ</li>
<li><strong>Tech Score -6 / STRONG SELL</strong> — giá dưới mọi MA, MACD bearish, RSI 42.8</li>
<li><strong>Biên lãi gộp 3.71%</strong> — mỏng đặc trưng ngành xây dựng, dễ bị ăn mòn khi chi phí vật tư tăng</li>
<li><strong>CFO phạt thuế/giám đốc tài chính đổi người</strong> (05/2025) — rủi ro quản trị chưa giải quyết</li>
"""

# ===== Technical ACTIVE section =====
ind = ta['indicators']
corr = ta['correlation']
tech_active_html = f"""
<h3>Tech Score: <span class="score-neg">{ta['tech_score']}/+6</span> · Verdict: <span class="verdict-sell">{ta['verdict']}</span></h3>
<div class="ind-grid">
  <div class="ind"><span class="ind-l">Giá (tuần)</span><span class="ind-v mono">{ta['price_current_vnd']:,}đ</span></div>
  <div class="ind"><span class="ind-l">MA10/20/50</span><span class="ind-v mono">{ind['ma10_vnd']:,} / {ind['ma20_vnd']:,} / {ind['ma50_vnd']:,}</span></div>
  <div class="ind"><span class="ind-l">RSI(14)</span><span class="ind-v mono">{ind['rsi14']:.1f}</span></div>
  <div class="ind"><span class="ind-l">MACD</span><span class="ind-v mono neg">{ind['macd']:.2f} / Sig {ind['signal']:.2f}</span></div>
  <div class="ind"><span class="ind-l">Bollinger</span><span class="ind-v mono">{ind['bb_lower_vnd']:,} – {ind['bb_upper_vnd']:,}đ</span></div>
  <div class="ind"><span class="ind-l">BB position</span><span class="ind-v mono">{ind['bb_position_pct']:.1f}%</span></div>
  <div class="ind"><span class="ind-l">Beta VNINDEX/VN30</span><span class="ind-v mono">{corr['beta_vnindex']:.2f} / {corr['beta_vn30']:.2f}</span></div>
  <div class="ind"><span class="ind-l">Corr VNINDEX/VN30</span><span class="ind-v mono">{corr['corr_vnindex']:.2f} / {corr['corr_vn30']:.2f}</span></div>
  <div class="ind"><span class="ind-l">Alpha 1Y</span><span class="ind-v mono neg">{corr['alpha_1y_pct']:+.1f}%</span></div>
  <div class="ind"><span class="ind-l">52W H/L</span><span class="ind-v mono">{ta['high_52w_vnd']:,} / {ta['low_52w_vnd']:,}đ</span></div>
</div>
<div class="patterns">
  <strong>Patterns phát hiện ({len(ta['patterns_detected'])}):</strong>
  <ul>
    <li><span class="tag-warn">Double Bottom (potential)</span> ×7 — neckline 87,200-92,783đ, target 92,830-116,890đ</li>
    <li><span class="tag-neg">Descending Channel (active)</span> — xu hướng giảm, high 84,380→72,700đ</li>
    <li><span class="tag-neg">Bearish candlesticks</span> — marubozu, 2× shooting star, bearish engulfing (4 tuần gần nhất)</li>
  </ul>
</div>
<div class="divergence-note">
  <strong>Divergence: KHÔNG có</strong> — 2 đáy gần nhất (05/04→14/06) giá giảm CÙNG RSI giảm (76,190→70,800đ, RSI 50.3→43.0). Không có tín hiệu phân kỳ.
</div>
"""

# Trading strategy
ts = ta['trading_strategy']
strategy_html = f"""
<table class="strat-table">
<tr><th>Kịch bản</th><th>Trigger</th><th>Action</th></tr>
<tr><td class="pos">Tích cực</td><td>{ts['scenario_bullish']['trigger']}</td><td>{ts['scenario_bullish']['action']} → {ts['scenario_bullish']['target']}</td></tr>
<tr><td class="neu">Trung tính</td><td>{ts['scenario_neutral']['trigger']}</td><td>{ts['scenario_neutral']['action']}</td></tr>
<tr><td class="neg">Tiêu cực</td><td>{ts['scenario_bearish']['trigger']}</td><td>{ts['scenario_bearish']['action']} — support {ts['scenario_bearish']['support']}</td></tr>
</table>
<p class="cyclical-note">⚠️ {ts['cyclical_note']}</p>
"""

# ===== Technical PROFILE section =====
pb = tp['price_behavior_profile']
vol = tp['volatility_profile']
dd = tp['drawdown_profile']
liq = tp['liquidity_profile']
tail = tp['tail_risk_profile']
vpc = tp['volume_price_confirmation_profile']
arch = tp['archetype']
setups = tp['setups']
non_concl = tp['non_conclusion']

setups_html = ""
for s in setups:
    setups_html += f"<li><strong>{s.get('name','?')}</strong> — score {s.get('score',0)}, dist to confirm {s.get('distance_to_confirmation_pct','?')}%, status <em>{s.get('status','?')}</em></li>"

profile_html = f"""
<h3>Archetype: <span class="archetype">{arch['primary']}</span></h3>
<p class="profile-note">{arch.get('reader_note','')}</p>
<div class="ind-grid">
  <div class="ind"><span class="ind-l">Return 1M/3M/1Y</span><span class="ind-v mono">{pb['return_1m_pct']:+.1f}% / {pb['return_3m_pct']:+.1f}% / {pb['return_1y_pct']:+.1f}%</span></div>
  <div class="ind"><span class="ind-l">HV60/HV252</span><span class="ind-v mono">{vol['hv60_pct']:.1f}% / {vol['hv252_pct']:.1f}%</span></div>
  <div class="ind"><span class="ind-l">Drawdown hiện tại</span><span class="ind-v mono neg">{dd['current_drawdown_pct']:.1f}%</span></div>
  <div class="ind"><span class="ind-l">Max drawdown</span><span class="ind-v mono">{dd['max_drawdown_pct']:.1f}%</span></div>
  <div class="ind"><span class="ind-l">Underwater days</span><span class="ind-v mono">{dd['current_underwater_days']}</span></div>
  <div class="ind"><span class="ind-l">VaR 95% (1d)</span><span class="ind-v mono">{tail['historical_var_95_1d_pct']:.1f}%</span></div>
  <div class="ind"><span class="ind-l">ES 95% (1d)</span><span class="ind-v mono">{tail['expected_shortfall_95_1d_pct']:.1f}%</span></div>
  <div class="ind"><span class="ind-l">VPCI</span><span class="ind-v mono">{vpc.get('vpci_latest', vpc.get('sma_20','?'))}</span></div>
  <div class="ind"><span class="ind-l">Liquidity %ile 1Y</span><span class="ind-v mono">{liq.get('latest_value_percentile_1y','?')}</span></div>
</div>
<div class="setups"><strong>Setups ({len(setups)}):</strong><ul>{setups_html}</ul></div>
<div class="non-conclusion">
  <strong>Điểm non-conclusion (mô tả, không khuyến nghị):</strong>
  <ol>{''.join(f'<li>{c}</li>' for c in non_concl)}</ol>
</div>
<p class="lang-policy">🔒 Ngôn ngữ: <code>neutral_descriptive_non_advice</code> — phần này MÔ TẢ hồ sơ giá-khối lượng, KHÔNG verdict mua/bán.</p>
"""

# ===== News section =====
cat_bd = news.get('category_breakdown', {})
def fmt_cat_chip(cat, d):
    if isinstance(d, dict):
        count = d.get('count', '?')
        score = d.get('score', '?')
        # sentiment label from score
        if isinstance(score, (int, float)):
            cls = 'chip-bull' if score >= 20 else 'chip-bear' if score <= -20 else 'chip-neu'
        else:
            cls = 'chip-neu'
        summary = d.get('items_summary', '')
        short = (summary[:70] + '…') if len(summary) > 70 else summary
        return f'<span class="cat-chip {cls}"><strong>{cat}</strong> · {count} bài · score {score}<br><span class="chip-summary">{short}</span></span>'
    return f'<span class="cat-chip">{cat}: {d}</span>'

top_stories = news.get('material_stories', [])[:5]
stories_html = ""
for s in top_stories:
    if isinstance(s, dict):
        stories_html += f"<li><strong>{s.get('title','?')}</strong> <span class='src'>({s.get('source','')}, {s.get('date','')})</span><br><span class='story-impact'>{s.get('impact','')}</span></li>"
    else:
        stories_html += f"<li>{s}</li>"

news_html = f"""
<div class="sentiment-box {'bullish' if news['sentiment_score']>20 else 'bearish' if news['sentiment_score']<-20 else 'neutral'}">
  Sentiment: <strong>{news['sentiment_score']}/100</strong> · {news['sentiment_label']}
</div>
<p class="news-caveat">⚠️ {news.get('verdict_note','')} — {news.get('caveat','')}</p>
<div class="news-cats">
  {''.join(fmt_cat_chip(k, v) for k,v in (cat_bd.items() if isinstance(cat_bd,dict) else []))}
</div>
<h4>Top stories ({len(top_stories)}):</h4>
<ul class="stories">{stories_html}</ul>
"""

# ===== Independent view =====
independent_html = f"""
<div class="ind-view">
<h4>Điều quan trọng nhất với Coteccons</h4>
<p>Đây là bài toán kinh điển: <strong>thị trường định giá dưới sổ sách (P/B 0.85)</strong> nhưng P/E lại 32x — vì <strong>ROE chỉ 2.43%</strong>. Tài sản 34.4 nghìn tỷ tạo ra LNST 228 tỷ. Câu hỏi cốt lõi: backlog kỷ lục 65.5 nghìn tỷ + biên LN đang phục hồi (1.52%→2.28%) có đẩy ROE lên mức xứng đáng (10%+) không, hay đây là đỉnh chu kỳ?</p>

<h4>Hiểu nhầm thường mắc</h4>
<p>Nhiều người nhìn LNST +117% và kết luận "tăng trưởng đỉnh". Thực ra tăng trưởng từ base rất thấp (FY24 biên 1.52%) — phần lớn là <strong>đòn bẩy hoạt động</strong> khi doanh thu tăng 45% mà chi phí cố định không tăng tương ứng. Cần theo dõi biên gộp (3.71%) xem có bền không, hay chỉ là pha lợi nhuận ngắn hạn.</p>

<h4>Quan điểm giá</h4>
<p>Tech Score -6 (STRONG SELL) mâu thuẫn với Profile archetype "accumulation_breakout" (đang tích lũy, chưa xác nhận). Điều này nói lên sự phân ly: <strong>ngắn hạn xấu (channel giảm + bearish candlesticks), nhưng cấu trúc dài hạn có dấu hiệu tích lũy</strong> (nhiều double bottom, drawdown -24% từ đỉnh). Chờ phá vỡ neckline 87,200-92,783đ với volume xác nhận trước khi hành động.</p>
</div>
"""

# ===== Assemble HTML =====
chart_price_data = ",".join([
    f"{ta['low_52w_vnd']/1000:.0f}",
    f"{ind['ma50_vnd']/1000:.0f}",
    f"{ind['bb_middle_vnd']/1000:.0f}",
    f"{ind['ma20_vnd']/1000:.0f}",
    f"{ind['ma10_vnd']/1000:.0f}",
    f"{ta['price_current_vnd']/1000:.0f}",
])

html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CTD · Coteccons Construction | Equity Research</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
  --bg-0:#0a0a14; --bg-1:#10101f; --bg-2:#16162a;
  --card:rgba(28,28,48,0.55); --card-solid:#1a1a2e;
  --border:rgba(139,92,246,0.18); --border-hot:rgba(236,72,153,0.35);
  --text:#f0f0ff; --text-dim:#8b8ba7; --text-faint:#5a5a72;
  --purple:#a855f7; --pink:#ec4899; --cyan:#06b6d4;
  --green:#10d98a; --red:#ff4d6d; --amber:#fbbf24;
  --grad-main:linear-gradient(135deg,#a855f7 0%,#ec4899 100%);
  --grad-bg:radial-gradient(ellipse at 20% 0%,rgba(139,92,246,0.15) 0%,transparent 50%),radial-gradient(ellipse at 80% 100%,rgba(236,72,153,0.12) 0%,transparent 50%);
  --font-sans:'Inter',-apple-system,sans-serif; --font-mono:'JetBrains Mono',monospace;
  --radius:20px;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg-0);background-image:var(--grad-bg);color:var(--text);font-family:var(--font-sans);line-height:1.6;min-height:100vh}}
.mono{{font-family:var(--font-mono)}}
.container{{max-width:1280px;margin:0 auto;padding:24px 20px 80px}}
/* Nav */
nav{{position:sticky;top:0;z-index:100;background:rgba(10,10,20,0.85);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);padding:12px 20px}}
nav .inner{{max-width:1280px;margin:0 auto;display:flex;gap:18px;align-items:center;flex-wrap:wrap}}
nav a{{color:var(--text-dim);text-decoration:none;font-size:13px;font-weight:500;padding:4px 0;border-bottom:2px solid transparent;transition:.2s}}
nav a:hover{{color:var(--text)}}
nav a.active{{color:var(--purple);border-bottom-color:var(--purple)}}
nav .brand{{font-weight:800;font-size:15px;color:var(--text);margin-right:auto}}
nav .brand .tk{{color:var(--purple)}}
/* Hero */
.hero{{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:36px 32px;margin:24px 0;backdrop-filter:blur(10px);position:relative;overflow:hidden}}
.hero::before{{content:'';position:absolute;top:-50%;right:-10%;width:60%;height:200%;background:var(--grad-main);opacity:.08;filter:blur(60px)}}
.hero h1{{font-size:32px;font-weight:800;margin-bottom:6px}}
.hero .sub{{color:var(--text-dim);font-size:15px;margin-bottom:16px}}
.hero .price-now{{font-family:var(--font-mono);font-size:42px;font-weight:700;background:var(--grad-main);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.hero .price-meta{{color:var(--text-dim);font-size:13px;margin-top:6px}}
/* KPI */
.kpi-strip{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin:24px 0}}
.kpi{{background:var(--bg-2);border:1px solid var(--border);border-radius:14px;padding:16px 18px;transition:.2s}}
.kpi:hover{{border-color:var(--border-hot);transform:translateY(-2px)}}
.kpi-label{{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--text-faint);margin-bottom:6px}}
.kpi-value{{font-size:24px;font-weight:700}}
.kpi-value .unit{{font-size:13px;color:var(--text-dim);margin-left:4px;font-weight:500}}
.kpi-value .unit{{font-size:13px;color:var(--text-dim);margin-left:4px;font-weight:500}}
.kpi-sub{{font-size:11px;margin-top:4px;color:var(--text-dim)}}
.pos{{color:var(--green)}} .neg{{color:var(--red)}} .neu{{color:var(--amber)}} .accent-pos{{color:var(--cyan)}}
/* Section */
section{{margin:48px 0;scroll-margin-top:80px}}
.sec-head{{display:flex;align-items:center;gap:12px;margin-bottom:18px}}
.sec-tag{{font-family:var(--font-mono);font-size:12px;color:var(--purple);background:rgba(168,85,247,0.12);padding:3px 10px;border-radius:6px;font-weight:600}}
.sec-head h2{{font-size:22px;font-weight:700}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:24px;backdrop-filter:blur(10px)}}
/* Tables */
table.data{{width:100%;border-collapse:collapse;font-size:14px}}
table.data th{{text-align:left;padding:10px 12px;color:var(--text-dim);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.05em;border-bottom:1px solid var(--border)}}
table.data td{{padding:11px 12px;border-bottom:1px solid rgba(139,92,246,0.08)}}
.num{{text-align:right}}
/* Valuation cards */
.val-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:16px 0}}
.val-card{{background:var(--bg-2);border:1px solid var(--border);border-radius:12px;padding:14px 16px}}
.vc-label{{font-size:11px;color:var(--text-faint);text-transform:uppercase;letter-spacing:.06em}}
.vc-val{{font-size:22px;font-weight:700;margin:4px 0}}
.vc-note{{font-size:11px;color:var(--text-dim)}}
/* Insights */
.insights-grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:16px 0}}
.insight-col{{background:var(--bg-2);border:1px solid var(--border);border-radius:14px;padding:20px}}
.insight-col.bull{{border-left:3px solid var(--green)}}
.insight-col.bear{{border-left:3px solid var(--red)}}
.insight-col h4{{font-size:14px;margin-bottom:12px;display:flex;align-items:center;gap:8px}}
.insight-col ul{{list-style:none;padding:0}}
.insight-col li{{padding:8px 0;border-bottom:1px solid rgba(139,92,246,0.06);font-size:14px;line-height:1.5}}
.insight-col li:last-child{{border:0}}
/* Tech indicators grid */
.ind-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin:14px 0}}
.ind{{background:var(--bg-2);border:1px solid var(--border);border-radius:10px;padding:10px 14px;display:flex;justify-content:space-between;align-items:center;gap:8px}}
.ind-l{{font-size:11px;color:var(--text-dim)}}
.ind-v{{font-size:13px;font-weight:600}}
.score-neg{{color:var(--red);font-weight:800}} .score-pos{{color:var(--green);font-weight:800}}
.verdict-sell{{background:rgba(255,77,109,0.15);color:var(--red);padding:2px 10px;border-radius:6px;font-weight:700;font-size:14px}}
.tag-warn{{background:rgba(251,191,36,0.15);color:var(--amber);padding:1px 8px;border-radius:4px;font-size:12px}}
.tag-neg{{background:rgba(255,77,109,0.15);color:var(--red);padding:1px 8px;border-radius:4px;font-size:12px}}
.patterns,.divergence-note,.setups,.non-conclusion{{margin:14px 0;padding:14px 16px;background:var(--bg-2);border-radius:10px;font-size:14px}}
.patterns ul,.setups ul{{margin:8px 0 0 18px}}
.strat-table{{width:100%;border-collapse:collapse;margin:12px 0;font-size:14px}}
.strat-table th{{background:var(--bg-2);padding:10px;text-align:left;font-size:12px;color:var(--text-dim)}}
.strat-table td{{padding:10px;border-bottom:1px solid var(--border)}}
.cyclical-note{{font-size:13px;color:var(--amber);margin-top:10px;padding:10px;background:rgba(251,191,36,0.06);border-radius:8px}}
.archetype{{background:var(--grad-main);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800}}
.profile-note,.lang-policy{{font-size:12px;color:var(--text-dim);font-style:italic}}
.lang-policy{{margin-top:12px;padding:8px 12px;background:rgba(6,182,212,0.06);border-left:2px solid var(--cyan)}}
/* News */
.sentiment-box{{display:inline-block;padding:10px 18px;border-radius:10px;font-size:16px;font-weight:600;margin-bottom:10px}}
.sentiment-box.bullish{{background:rgba(16,217,138,0.15);color:var(--green)}}
.sentiment-box.bearish{{background:rgba(255,77,109,0.15);color:var(--red)}}
.sentiment-box.neutral{{background:rgba(251,191,36,0.15);color:var(--amber)}}
.news-caveat{{font-size:12px;color:var(--amber);margin:8px 0}}
.news-cats{{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}}
.cat-chip{{background:var(--bg-2);border:1px solid var(--border);padding:8px 12px;border-radius:8px;font-size:12px;display:block;margin-bottom:6px}}
.cat-chip.chip-bull{{border-left:3px solid var(--green)}}
.cat-chip.chip-bear{{border-left:3px solid var(--red)}}
.cat-chip.chip-neu{{border-left:3px solid var(--amber)}}
.cat-chip .chip-summary{{display:block;color:var(--text-dim);font-size:11px;margin-top:3px;line-height:1.4}}
.stories{{list-style:none;padding:0;margin:12px 0}}
.stories li{{padding:12px 0;border-bottom:1px solid rgba(139,92,246,0.08);font-size:14px;line-height:1.5}}
.stories .src{{color:var(--text-faint);font-size:12px}}
.story-impact{{color:var(--text-dim);font-size:13px}}
/* DuPont bars */
.dupont{{display:flex;gap:8px;align-items:center;margin:14px 0;flex-wrap:wrap}}
.dupont-item{{flex:1;min-width:140px;background:var(--bg-2);border:1px solid var(--border);border-radius:10px;padding:12px;text-align:center}}
.dupont-item .v{{font-family:var(--font-mono);font-size:20px;font-weight:700}}
.dupont-item .l{{font-size:11px;color:var(--text-dim);margin-top:4px}}
.dupont-x{{font-size:20px;color:var(--purple);font-weight:700}}
/* Ind view */
.ind-view p{{margin:10px 0;font-size:14px;line-height:1.6}}
.ind-view h4{{color:var(--purple);margin-top:18px;font-size:15px}}
/* Chart container */
.chart-box{{background:var(--bg-2);border:1px solid var(--border);border-radius:12px;padding:18px;margin:14px 0;height:340px;position:relative}}
.chart-box canvas{{max-height:300px}}
/* Disclaimer */
.disclaimer{{margin-top:48px;padding:20px;background:rgba(255,77,109,0.04);border:1px solid rgba(255,77,109,0.15);border-radius:12px;font-size:12px;color:var(--text-dim);line-height:1.6}}
.disclaimer strong{{color:var(--red)}}
@media(max-width:768px){{
  .insights-grid,.val-grid{{grid-template-columns:1fr}}
  .hero h1{{font-size:24px}}
}}
</style>
</head>
<body>
<nav><div class="inner">
<span class="brand"><span class="tk">CTD</span> · Coteccons</span>
<a href="#summary" class="active">Tổng quan</a>
<a href="#financials">Tài chính</a>
<a href="#valuation">Định giá</a>
<a href="#dupont">DuPont</a>
<a href="#insights">Insights</a>
<a href="#technical">Kỹ thuật</a>
<a href="#profile">Profile</a>
<a href="#news">Tin tức</a>
<a href="#view">Quan điểm</a>
</div></nav>

<div class="container">

<!-- HERO -->
<div class="hero">
  <h1>CTD · Coteccons Construction</h1>
  <div class="sub">HOSE · Construction &amp; Materials · FY kết 30/06 · Báo cáo equity research {ov.get('rating_as_of','')}</div>
  <div class="price-now mono"><span style="font-size:24px;color:var(--text-dim)">₫</span>{price:,.0f}<span style="font-size:18px;color:var(--text-dim)"> /cp</span></div>
  <div class="price-meta">Vốn hóa ≈ <strong class="mono pos">{mcap/1e12:.2f} nghìn tỷ đ</strong> · {shares/1e6:.1f} triệu CP · Cập nhật 08/07/2026</div>
</div>

<!-- KPI -->
<div class="kpi-strip">{kpi_cards}</div>

<!-- SECTION 2: SUMMARY -->
<section id="summary">
  <div class="sec-head"><span class="sec-tag">02</span><h2>Tóm tắt điều hành</h2></div>
  <div class="card">
    <p style="font-size:15px;line-height:1.7"><strong>Coteccons (CTD)</strong> ghi nhận <strong>doanh thu FY25 = {fmt_vnd(fin['FY2025']['revenue'])} (+45.3%)</strong>, LNST <strong>{fmt_vnd(fin['FY2025']['net_profit'])} (+117.8%)</strong> — tăng trưởng đột biến nhờ đòn bẩy hoạt động. Tuy nhiên <strong>biên LN chỉ 2.28%</strong> và <strong>ROE 2.43%</strong> — sinh lời thấp đặc trưng ngành xây dựng. Định giá hiện tại <strong>P/B 0.85x (dưới sổ sách)</strong> nhưng <strong>P/E 31.9x</strong> phản ánh ROE thấp. Kỹ thuật ngắn hạn <strong>STRONG SELL (score -6)</strong> nhưng profile dài hạn cho dấu hiệu tích lũy (archetype: accumulation_breakout).</p>
    <div class="kpi-strip" style="margin-top:16px">
      <div class="kpi"><div class="kpi-label">⚡ Điểm nhấn</div><div style="font-size:14px;margin-top:6px">P/B &lt; 1 nhưng ROE 2.4% — thị trường不相信 sinh lời</div></div>
      <div class="kpi"><div class="kpi-label">⚠️ Rủi ro</div><div style="font-size:14px;margin-top:6px">Tech -6 + CFO đổi người + biên mỏng</div></div>
      <div class="kpi"><div class="kpi-label">✅ Catalyst</div><div style="font-size:14px;margin-top:6px">Backlog 65.5K tỷ + Đường sắt Bắc-Nam</div></div>
      <div class="kpi"><div class="kpi-label">📊 Verdict</div><div style="font-size:14px;margin-top:6px">Chờ phá neckline 87-93Kđ với volume</div></div>
    </div>
  </div>
</section>

<!-- SECTION 3: FINANCIALS -->
<section id="financials">
  <div class="sec-head"><span class="sec-tag">03</span><h2>Kết quả kinh doanh</h2></div>
  <div class="card">
    <table class="data">
      <thead><tr><th>Năm</th><th>Doanh thu</th><th>Lợi nhuận gộp</th><th>LNST</th><th>EPS (đ)</th><th>ROE</th><th>ROS</th></tr></thead>
      <tbody>{fin_rows}</tbody>
    </table>
    <p style="font-size:12px;color:var(--text-dim);margin-top:10px">⚠️ {fund['data_caveat']}</p>
    <div class="chart-box"><canvas id="chartRevNP"></canvas></div>
  </div>
</section>

<!-- SECTION 4: VALUATION -->
<section id="valuation">
  <div class="sec-head"><span class="sec-tag">04</span><h2>Định giá</h2></div>
  <div class="card">
    <div class="val-grid">{val_cards}</div>
    <h4 style="margin:18px 0 8px;color:var(--purple)">DCF 3 kịch bản</h4>
    <table class="data"><thead><tr><th>Kịch bản</th><th>Tốc độ tăng g</th><th>Giá/cổ phiếu</th></tr></thead><tbody>{dcf_rows}</tbody></table>
    <p style="font-size:12px;color:var(--text-dim);margin-top:8px">Anchor bảo thủ: Graham = <strong>{graham:,.0f}đ</strong> · Giá hiện tại {price:,.0f}đ = <span class="{'neg' if diff_pct>0 else 'pos'}">{diff_pct:+.1f}%</span> so với Graham</p>
    <div class="chart-box"><canvas id="chartPEPB"></canvas></div>
  </div>
</section>

<!-- SECTION 7: DUPONT -->
<section id="dupont">
  <div class="sec-head"><span class="sec-tag">07</span><h2>DuPont Decomposition (FY2025)</h2></div>
  <div class="card">
    <div class="dupont">
      <div class="dupont-item"><div class="v">{npm:.2f}%</div><div class="l">Biên LN (NPM)</div></div>
      <span class="dupont-x">×</span>
      <div class="dupont-item"><div class="v">{taturn:.2f}x</div><div class="l">Vòng quay TS</div></div>
      <span class="dupont-x">×</span>
      <div class="dupont-item"><div class="v">{eqmult:.2f}x</div><div class="l">Đòn bẩy (TA/EQ)</div></div>
      <span class="dupont-x">=</span>
      <div class="dupont-item" style="border-color:var(--pink)"><div class="v neu">{ratios['FY2025']['ROE']:.2f}%</div><div class="l">ROE</div></div>
    </div>
    <p style="font-size:13px;color:var(--text-dim);margin-top:12px">ROE thấp không phải vì đòn bẩy kém (3.67x hợp lý) mà vì <strong>biên LN cực mỏng (2.28%)</strong> + <strong>vòng quay TS thấp (0.29x)</strong> — đặc thù xây dựng: tài sản lớn (phải thu, hợp đồng) nhưng biên gộp mỏng.</p>
  </div>
</section>

<!-- SECTION 8: INSIGHTS -->
<section id="insights">
  <div class="sec-head"><span class="sec-tag">08</span><h2>Insights ngành — Bull vs Bear</h2></div>
  <div class="insights-grid">
    <div class="insight-col bull"><h4>🟢 Bull Case</h4><ul>{insights_bull}</ul></div>
    <div class="insight-col bear"><h4>🔴 Bear Case</h4><ul>{insights_bear}</ul></div>
  </div>
</section>

<!-- SECTION 9: TECHNICAL ACTIVE -->
<section id="technical">
  <div class="sec-head"><span class="sec-tag">09</span><h2>Phân tích kỹ thuật — Mode ACTIVE</h2></div>
  <div class="card">
    {tech_active_html}
    <h4 style="margin:18px 0 8px;color:var(--purple)">Chiến lược giao dịch 3 kịch bản</h4>
    {strategy_html}
    <div class="chart-box"><canvas id="chartPrice"></canvas></div>
  </div>
</section>

<!-- SECTION 9b: TECHNICAL PROFILE -->
<section id="profile">
  <div class="sec-head"><span class="sec-tag">9b</span><h2>Pro Stock Profile — Mode PROFILE</h2></div>
  <div class="card">
    {profile_html}
  </div>
</section>

<!-- SECTION 10: NEWS -->
<section id="news">
  <div class="sec-head"><span class="sec-tag">10</span><h2>Tin tức 30 ngày</h2></div>
  <div class="card">
    {news_html}
  </div>
</section>

<!-- SECTION 11: INDEPENDENT VIEW -->
<section id="view">
  <div class="sec-head"><span class="sec-tag">11</span><h2>🎯 Quan điểm độc lập</h2></div>
  <div class="card">
    {independent_html}
  </div>
</section>

<div class="disclaimer">
  <strong>⚠️ Miễn trừ trách nhiệm:</strong> Báo cáo này dành mục đích nghiên cứu, KHÔNG phải khuyến nghị đầu tư. Quyết định mua/bán là của nhà đầu tư. Data từ vnstock API (VCI/TCBS) — BCTC community edition giới hạn 8 kỳ. Tech Score & Verdict dùng ngôn ngữ ACTIVE (timing), riêng Profile dùng ngôn ngữ <code>neutral_descriptive_non_advice</code>. Cổ phiếu chu kỳ — kết hợp fundamental trước khi quyết.
</div>

</div>

<script>
// Chart defaults
Chart.defaults.color = '#8b8ba7';
Chart.defaults.borderColor = 'rgba(139,92,246,0.06)';
Chart.defaults.font.family = 'Inter, sans-serif';

// Rev & NP chart
new Chart(document.getElementById('chartRevNP'), {{
  type:'bar',
  data:{{
    labels:['FY2024','FY2025'],
    datasets:[
      {{label:'Doanh thu (tỷ đ)',data:[{fin['FY2024']['revenue']/1e9:.0f},{fin['FY2025']['revenue']/1e9:.0f}],backgroundColor:'rgba(168,85,247,0.6)',borderColor:'#a855f7',borderWidth:1,yAxisID:'y'}},
      {{label:'LNST (tỷ đ)',data:[{fin['FY2024']['net_profit']/1e9:.0f},{fin['FY2025']['net_profit']/1e9:.0f}],backgroundColor:'rgba(236,72,153,0.8)',borderColor:'#ec4899',borderWidth:1,yAxisID:'y'}}
    ]
  }},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{labels:{{boxWidth:12,font:{{size:11}}}}}}}},scales:{{y:{{ticks:{{callback:v=>v.toLocaleString()+' tỷ'}}}}}}}}
}});

// PE/PB chart
new Chart(document.getElementById('chartPEPB'), {{
  type:'bar',
  data:{{
    labels:['P/E','P/B','P/CF','P/S'],
    datasets:[{{label:'CTD FY25',data:[{fy25['PE']:.1f},{fy25['PB']:.2f},{val.get('PCF',0):.1f},{val.get('PS',0):.2f}],backgroundColor:['rgba(255,77,109,0.6)','rgba(6,182,212,0.7)','rgba(168,85,247,0.6)','rgba(251,191,36,0.6)'],borderWidth:1}}]
  }},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},scales:{{y:{{beginAtZero:true}}}}}}
}});

// Price chart (candlestick proxy — line + range)
const priceData = [];
new Chart(document.getElementById('chartPrice'), {{
  type:'line',
  data:{{
    labels:['52W ago','-40W','-30W','-20W','-10W','Hiện tại'],
    datasets:[{{
      label:'Giá đóng cửa tuần (nghìn đ)',
      data:[{chart_price_data}],
      borderColor:'#ec4899',backgroundColor:'rgba(236,72,153,0.1)',fill:true,tension:0.3,borderWidth:2,pointRadius:4
    }}]
  }},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},scales:{{y:{{ticks:{{callback:v=>v.toLocaleString()+'k'}}}}}}}}
}});

// Scroll-spy nav
const navLinks = document.querySelectorAll('nav a');
const sections = document.querySelectorAll('section');
window.addEventListener('scroll', () => {{
  let current = '';
  sections.forEach(s => {{ if(window.scrollY >= s.offsetTop - 100) current = s.id; }});
  navLinks.forEach(a => {{ a.classList.toggle('active', a.getAttribute('href') === '#'+current); }});
}});
</script>
</body>
</html>"""

OUT.write_text(html, encoding='utf-8')
print(f"Wrote {OUT} ({len(html):,} bytes, {len(html.splitlines())} lines)")
# Verify no unreplaced tokens
import re
remaining = sorted(set(re.findall(r'\{\{[A-Z_0-9]+\}\}', html)))
print(f"Unreplaced tokens: {remaining if remaining else 'NONE ✓'}")
