#!/usr/bin/env python3
"""CTD Dashboard — fill template tokenize đúng spec vn-research-dashboard.
Dùng str.replace thuần (KHÔNG f-string cho JS). Template 7 section fundamental + thêm 4 section technical/news/view."""
import json, re
from pathlib import Path

DATA = Path('/Users/bobo/ZCodeProject/ctd_data')
TPL = Path('/Users/bobo/.zcode/skills/vn-research-dashboard/assets/dashboard_template.html')
OUT = Path('/Users/bobo/ZCodeProject/CTD_Complete_Report.html')

fund = json.load(open(DATA/'fundamental_valuation.json'))
ta = json.load(open(DATA/'technical_active.json'))
tp = json.load(open(DATA/'technical_profile.json'))
news = json.load(open(DATA/'news_digest.json'))
ov = json.load(open(DATA/'overview.json'))

price = fund['price']; mcap = fund['market_cap']; shares = fund['shares']
ratios = fund['ratios']; val = fund['valuation']; fin = fund['financials']
fy25 = ratios['FY2025']; fy24 = ratios['FY2024']
ind = ta['indicators']; corr = ta['correlation']

# CTD chỉ có 2 năm full (BCTC community edition) — arrays 2 phần tử
years = [2024, 2025]
rev = [fin['FY2024']['revenue']/1e9, fin['FY2025']['revenue']/1e9]
np = [fin['FY2024']['net_profit']/1e9, fin['FY2025']['net_profit']/1e9]
eps = [fy24['EPS'], fy25['EPS']]
bvps = [fy24['BVPS'], fy25['BVPS']]
roe = [fy24['ROE'], fy25['ROE']]
ros = [fy24['ROS'], fy25['ROS']]
price_yr = [None, price/1000]  # chỉ có giá hiện tại, FY2024 year-end không có
pe = [fy24['PE'], fy25['PE']]
pb = [fy24['PB'], fy25['PB']]
# DuPont FY25
npm25 = fin['FY2025']['net_profit']/fin['FY2025']['revenue']*100
turn25 = fin['FY2025']['revenue']/fin['FY2025']['total_assets']
lev25 = fin['FY2025']['total_assets']/fin['FY2025']['equity']
npm24 = fin['FY2024']['net_profit']/fin['FY2024']['revenue']*100
turn24 = fin['FY2024']['revenue']/fin['FY2024']['total_assets']
lev24 = fin['FY2024']['total_assets']/fin['FY2024']['equity']

# ===== BUILD COMPOSITE HTML BLOCKS =====
# KPI strip (6 cards)
kpi_html = f'''<div class="kpi-strip">
<div class="kpi"><div class="kpi-label">P/E (FY25)</div><div class="kpi-value mono {'neg' if fy25['PE']>25 else 'pos'}">{fy25['PE']:.1f}<span>x</span></div><div class="kpi-delta neu">EPS {fy25['EPS']:,.0f}đ</div></div>
<div class="kpi"><div class="kpi-label">P/B (FY25)</div><div class="kpi-value mono pos">{fy25['PB']:.2f}<span>x</span></div><div class="kpi-delta pos">dưới sổ sách</div></div>
<div class="kpi"><div class="kpi-label">ROE (FY25)</div><div class="kpi-value mono neg">{fy25['ROE']:.2f}<span>%</span></div><div class="kpi-delta neu">sinh lời thấp</div></div>
<div class="kpi"><div class="kpi-label">BVPS (FY25)</div><div class="kpi-value mono">{fy25['BVPS']/1000:.1f}<span>K</span></div><div class="kpi-delta neu">nghìn đồng</div></div>
<div class="kpi"><div class="kpi-label">LNST YoY</div><div class="kpi-value mono pos">+117.8<span>%</span></div><div class="kpi-delta pos">228 tỷ đ</div></div>
<div class="kpi"><div class="kpi-label">Backlog</div><div class="kpi-value mono pos">65.5<span>K tỷ</span></div><div class="kpi-delta neu">~2x revenue</div></div>
</div>'''

# Financial table 5-year (CTD chỉ 2 năm — ghi chú rõ)
fin_table = '''<table class="fin-table"><thead><tr>
<th>Năm</th><th>Doanh thu (tỷ)</th><th>LNST (tỷ)</th><th>EPS (đ)</th><th>BVPS (đ)</th><th>ROE %</th><th>ROS %</th><th>P/E</th><th>P/B</th>
</tr></thead><tbody>'''
for i, y in enumerate(years):
    fin_table += f'''<tr>
<td class="mono"><strong>{y}</strong></td>
<td class="mono num">{rev[i]:,.0f}</td><td class="mono num">{np[i]:,.0f}</td>
<td class="mono num highlight">{eps[i]:,.0f}</td><td class="mono num">{bvps[i]:,.0f}</td>
<td class="mono num">{roe[i]:.2f}</td><td class="mono num">{ros[i]:.2f}</td>
<td class="mono num">{pe[i]:.1f}</td><td class="mono num">{pb[i]:.2f}</td>
</tr>'''
fin_table += '</tbody></table>'
fin_footnote = '<p class="footnote">⚠️ BCTC vnstock community edition giới hạn 8 kỳ (2024-Q2 → 2026-Q1). Chỉ có full-year FY2024 + FY2025. Ratios vnstock stale (2018) — tự tính từ BCTC. EPS dùng weighted-average shares từ BCTC.</p>'

# Valuation cards (5 scenarios) — CTD adapted
graham = val.get('Graham', 0) or 0
dcf_bear = val.get('DCF_per_share_bearish', 0) or 0
dcf_base = val.get('DCF_per_share_base', 0) or 0
dcf_bull = val.get('DCF_per_share_bullish', 0) or 0
pb_fair = fy25['BVPS'] * 1.0  # PB 1.0x floor
pe_fair = fy25['EPS'] * 15    # PE 15x moderate
scenarios = [
    ('PB 1.0x (floor)', pb_fair/1000, (pb_fair/price-1)*100, f"BVPS'25 × 1.0"),
    ('PE 15x', pe_fair/1000, (pe_fair/price-1)*100, f"EPS'25 × 15"),
    ('Graham √22.5', graham/1000, (graham/price-1)*100, '√(22.5·EPS·BVPS)'),
    ('DCF base (g=5%)', dcf_base/1000, (dcf_base/price-1)*100, 'WACC 12%, g 5%'),
    ('DCF bull (g=10%)', dcf_bull/1000, (dcf_bull/price-1)*100, 'WACC 12%, g 10%'),
]
max_val = max(s[1] for s in scenarios)
val_cards = ''
for name, v, upside, formula in scenarios:
    cls = 'pos' if v > price/1000 else 'neg' if v < price/1000*0.7 else 'neu'
    up_cls = 'pos' if upside > 0 else 'neg'
    width = min(v/max_val*100, 100)
    val_cards += f'''<div class="val-card"><div class="name">{name}</div><div class="price mono {cls}">{v:,.1f}K</div><div class="upside {up_cls}">{upside:+.0f}%</div><div class="bar-track"><div class="bar-fill" style="width:{width:.0f}%"></div></div><div class="formula">{formula}</div></div>'''

# Fair value = median of conservative scenarios
fair_vals = sorted([graham, dcf_bear, dcf_base, pb_fair, pe_fair])
fair_value = fair_vals[len(fair_vals)//2] / 1000  # K
diff_pct = (price/1000 - fair_value) / fair_value * 100
if diff_pct > 10: verdict, vcolor = '🔴 OVERVALUED', 'var(--red)'
elif diff_pct < -10: verdict, vcolor = '🟢 UNDERVALUED', 'var(--green)'
else: verdict, vcolor = '⚖️ FAIRLY VALUED', 'var(--amber)'

# Multiples grid
mult = f'''<div class="grid-4">
<div class="mult-card"><div class="m-label">P/E FY25</div><div class="m-val mono {'neg' if fy25['PE']>25 else ''}">{fy25['PE']:.1f}x</div><div class="m-note">cao (ROE thấp)</div></div>
<div class="mult-card"><div class="m-label">P/B FY25</div><div class="m-val mono pos">{fy25['PB']:.2f}x</div><div class="m-note">dưới sổ sách</div></div>
<div class="mult-card"><div class="m-label">P/CF</div><div class="m-val mono">{val.get('PCF',0):.1f}x</div><div class="m-note">CFO 816 tỷ</div></div>
<div class="mult-card"><div class="m-label">P/S</div><div class="m-val mono">{val.get('PS',0):.2f}x</div><div class="m-note">Rev 10K tỷ</div></div>
</div>'''

# DCF & Graham block
dcf_block = f'''<div class="grid-2">
<div class="card"><div class="card-head"><div><div class="card-title">DCF 3 kịch bản (FCFF proxy = NI)</div><div class="card-sub">Perpetuity growth, WACC 12%</div></div></div>
<table class="fin-table"><thead><tr><th>Kịch bản</th><th>g</th><th>Giá/cp</th><th>vs giá hiện</th></tr></thead><tbody>
<tr><td>Bearish</td><td class="mono">0%</td><td class="mono num">{dcf_bear:,.0f}đ</td><td class="mono num neg">{(dcf_bear/price-1)*100:+.0f}%</td></tr>
<tr><td>Base</td><td class="mono">5%</td><td class="mono num">{dcf_base:,.0f}đ</td><td class="mono num neg">{(dcf_base/price-1)*100:+.0f}%</td></tr>
<tr><td>Bullish</td><td class="mono">10%</td><td class="mono num">{dcf_bull:,.0f}đ</td><td class="mono num pos">{(dcf_bull/price-1)*100:+.0f}%</td></tr>
</tbody></table></div>
<div class="card"><div class="card-head"><div><div class="card-title">Graham Formula</div><div class="card-sub">V = √(22.5 · EPS · BVPS)</div></div></div>
<div class="gauge-wrap"><div class="gauge-num mono">₫{graham/1000:.1f}K</div><div class="gauge-label">Graham intrinsic value</div>
<div style="margin-top:12px;color:var(--text-dim)">Giá hiện <strong class="mono">{price/1000:.1f}K</strong> → {("đắt" if price>graham else "rẻ")} hơn {(abs(diff_pct)):.0f}% so Graham</div></div></div>
</div>'''

# DuPont interpretation
dupont_interp = f'''<div class="card"><div class="card-head"><div><div class="card-title">Diễn giải DuPont FY2025</div></div></div>
<div class="dupont-read">
<p><strong>ROE {fy25['ROE']:.2f}%</strong> = Biên LN {npm25:.2f}% × Vòng quay TS {turn25:.2f}x × Đòn bẩy {lev25:.2f}x</p>
<p>ROE thấp <strong>không phải vì đòn bẩy kém</strong> ({lev25:.2f}x hợp lý cho xây dựng) mà vì <strong>biên LN cực mỏng ({npm25:.2f}%)</strong> + <strong>vòng quay TS thấp ({turn25:.2f}x)</strong> — đặc thù ngành xây dựng: tài sản lớn (phải thu, hợp kếtodong dang) nhưng biên gộp mỏng (3.71%).</p>
<p style="color:var(--text-dim);font-size:13px">FY24 → FY25: biên phục hồi {npm24:.2f}% → {npm25:.2f}% (đòn bẩy hoạt động khi revenue +45%). Nếu biên tiếp tục expand, ROE có thể đạt 5-8% trong 2-3 năm tới.</p>
</div></div>'''

# Insights (Bull/Bear balance — skill yêu cầu)
insights = '''<div class="insights-grid">
<div class="insight-col bull"><div class="ic-head">🟢 Bull Case</div><ul>
<li><strong>Backlog kỷ lục ~65.5K tỷ</strong> — gấp 2x revenue năm, đảm bảo tầm nhìn đa năm</li>
<li><strong>LNST FY25 +117.8%</strong> — biên LN phục hồi 1.52% → 2.28%</li>
<li><strong>9M FY26: 48K tỷ đơn hàng mới</strong>, 94% khách quay lại</li>
<li><strong>Đường sắt Bắc-Nam 67 tỷ USD</strong> — nhà thầu lựa chọn Q2/2026</li>
</ul></div>
<div class="insight-col bear"><div class="ic-head">🔴 Bear Case</div><ul>
<li><strong>ROE chỉ 2.43%</strong> — sinh lời rất thấp dù revenue 10K tỷ</li>
<li><strong>Tech Score -6 / STRONG SELL</strong> — channel giảm, MACD bearish</li>
<li><strong>Biên gộp 3.71%</strong> — mỏng, dễ bị ăn mòn khi vật tư tăng</li>
<li><strong>CFO phạt thuế/giám đốc tài chính đổi người</strong> (05/2025)</li>
</ul></div>
</div>'''

# Rating block
rating = f'''<div class="card rating-card"><div class="card-head"><div><div class="card-title">Khuyến nghị tổng hợp</div></div></div>
<div class="rating-verdict neu">⚖️ HOLD / WATCH</div>
<div class="rating-detail">
<p><strong>9 PP hội tụ:</strong> Graham {graham/1000:.0f}K, DCF base {dcf_base/1000:.0f}K, PB 1.0x {pb_fair/1000:.0f}K → median <strong>{fair_value:.0f}K</strong></p>
<p>Giá hiện {price/1000:.1f}K → {"trên" if diff_pct>0 else "dưới"} median {abs(diff_pct):.0f}%</p>
<p style="color:var(--amber);font-size:13px">⚠️ Verdict kỹ thuật STRONG SELL mâu thuẫn với định giá dưới sổ sách → chờ tín hiệu kỹ thuật xác nhận (phá neckline 87-93K) trước khi hành động.</p>
</div></div>'''

# Forecast (CTD adapted — backlog → revenue projection)
forecast_block = f'''<div class="card-head"><div><div class="card-title">Dự phóng backlog → revenue</div><div class="card-sub">Backlog 65.5K tỷ, recognize ~50%/năm</div></div></div>
<div class="forecast-note">CTD là công ty xây dựng (KHÔNG có sản lượng thép). Dự phóng dựa trên backlog nhận diện + biên LN phục hồi. FY27E: nếu ROE đạt 5%, EPS ~4,600đ.</div>'''

# Disclaimer
disclaimer = '''<p><strong>⚠️ Miễn trừ trách nhiệm:</strong> Báo cáo này dành mục đích nghiên cứu, KHÔNG phải khuyến nghị đầu tư. Data từ vnstock API (VCI/TCBS) — BCTC community edition giới hạn 8 kỳ. Tech Score & Verdict dùng ngôn ngữ ACTIVE (timing); riêng Profile dùng <code>neutral_descriptive_non_advice</code>. Cổ phiếu chu kỳ — kết hợp fundamental trước khi quyết định.</p>'''

# Footer
footer = '<div>Nguồn: vnstock API (VCI/TCBS) · BCTC Coteccons · Tech/News analysis @2026-07-08</div>'

# Summary chart data (9 PP)
summary_methods = ['PB 1.0x', 'PE 15x', 'Graham', 'DCF bear', 'DCF base', 'DCF bull', 'P/B hiện', '52W low', '52W high']
summary_vals = [pb_fair/1000, pe_fair/1000, graham/1000, dcf_bear/1000, dcf_base/1000, dcf_bull/1000, pb[1], ta['low_52w_vnd']/1000, ta['high_52w_vnd']/1000]
summary_data = f'''{{labels: {json.dumps(summary_methods)}, datasets: [{{data: {json.dumps([round(v,1) for v in summary_vals])}, backgroundColor: (ctx) => {{ const v = ctx.parsed.y; const p = {price/1000:.1f}; if (v < p*0.8) return 'rgba(255,77,109,0.7)'; if (v > p*1.5) return 'rgba(16,217,138,0.7)'; return 'rgba(168,85,247,0.7)'; }}, borderRadius: 8}}]}}'''
summary_annotation = f'''{{priceLine: {{type: 'line', yMin: {price/1000:.1f}, yMax: {price/1000:.1f}, borderColor: '#fbbf24', borderWidth: 2, borderDash: [6,4], label: {{content: 'Giá {price/1000:.0f}K', display: true, position: 'end', backgroundColor: 'rgba(251,191,36,0.9)', color: '#000', font: {{weight:'700',size:10}}, borderRadius: 4}}}}}}'''

# ===== TECHNICAL + NEWS + VIEW SECTIONS (thêm vào trước disclaimer) =====
tech_section = f'''
<div class="section-title"><span class="tag pink">08</span><h2>Phân tích kỹ thuật · Mode ACTIVE</h2><div class="divider-line"></div></div>
<div class="card tech-card">
<div class="tech-header"><div class="tech-score neg">{ta['tech_score']}/+6</div><div class="tech-verdict verdict-sell">{ta['verdict']}</div></div>
<div class="ind-grid">
<div class="ind"><span class="ind-l">Giá (tuần)</span><span class="ind-v mono">{ta['price_current_vnd']/1000:.1f}K</span></div>
<div class="ind"><span class="ind-l">MA10/20/50</span><span class="ind-v mono">{ind['ma10_vnd']/1000:.0f}/{ind['ma20_vnd']/1000:.0f}/{ind['ma50_vnd']/1000:.0f}</span></div>
<div class="ind"><span class="ind-l">RSI(14)</span><span class="ind-v mono">{ind['rsi14']:.1f}</span></div>
<div class="ind"><span class="ind-l">MACD/Sig</span><span class="ind-v mono neg">{ind['macd']:.2f}/{ind['signal']:.2f}</span></div>
<div class="ind"><span class="ind-l">Bollinger</span><span class="ind-v mono">{ind['bb_lower_vnd']/1000:.0f}–{ind['bb_upper_vnd']/1000:.0f}K</span></div>
<div class="ind"><span class="ind-l">Beta VNINDEX/VN30</span><span class="ind-v mono">{corr['beta_vnindex']:.2f}/{corr['beta_vn30']:.2f}</span></div>
<div class="ind"><span class="ind-l">Alpha 1Y</span><span class="ind-v mono neg">{corr['alpha_1y_pct']:+.1f}%</span></div>
<div class="ind"><span class="ind-l">52W H/L</span><span class="ind-v mono">{ta['high_52w_vnd']/1000:.0f}/{ta['low_52w_vnd']/1000:.0f}K</span></div>
</div>
<div class="patterns-note"><strong>Patterns ({len(ta['patterns_detected'])}):</strong> Double Bottom ×7 (potential, neckline 87-93K), Descending Channel active, bearish candlesticks (marubozu, shooting star ×2, engulfing).</div>
<div class="divergence-note"><strong>Divergence: KHÔNG</strong> — 2 đáy gần nhất giá giảm cùng RSI giảm (76,190→70,800đ, RSI 50.3→43.0).</div>
<table class="fin-table strat-table"><thead><tr><th>Kịch bản</th><th>Trigger</th><th>Action</th></tr></thead><tbody>
<tr><td class="pos">Tích cực</td><td>Giá đóng cửa tuần vượt MA20 ({ind['ma20_vnd']:,}đ) + volume tăng + MACD cắt lên Signal</td><td>Tích lũy → neckline 92,783đ</td></tr>
<tr><td class="neu">Trung tính</td><td>Giá dao động MA10/MA20, RSI 45-55</td><td>Quan sát / giữ</td></tr>
<tr><td class="neg">Tiêu cực</td><td>Mất MA50 ({ind['ma50_vnd']:,}đ), MACD nới rộng</td><td>Hạn chế — support 65,979đ</td></tr>
</tbody></table>
<p class="cyclical-note">⚠️ CTD chu kỳ — score bearish không tự động = bán; kết hợp fundamental (backlog, biên) trước khi quyết.</p>
</div>

<div class="section-title"><span class="tag cyan">9b</span><h2>Pro Stock Profile · Mode PROFILE</h2><div class="divider-line"></div></div>
<div class="card profile-card">
<div class="archetype-badge">Archetype: <strong>{tp['archetype']['primary']}</strong></div>
<p class="profile-note">{tp['archetype'].get('reader_note','')}</p>
<div class="ind-grid">
<div class="ind"><span class="ind-l">Return 1M/3M/1Y</span><span class="ind-v mono">{tp['price_behavior_profile']['return_1m_pct']:+.1f}%/{tp['price_behavior_profile']['return_3m_pct']:+.1f}%/{tp['price_behavior_profile']['return_1y_pct']:+.1f}%</span></div>
<div class="ind"><span class="ind-l">HV60/HV252</span><span class="ind-v mono">{tp['volatility_profile']['hv60_pct']:.1f}%/{tp['volatility_profile']['hv252_pct']:.1f}%</span></div>
<div class="ind"><span class="ind-l">Drawdown hiện</span><span class="ind-v mono neg">{tp['drawdown_profile']['current_drawdown_pct']:.1f}%</span></div>
<div class="ind"><span class="ind-l">Max drawdown</span><span class="ind-v mono">{tp['drawdown_profile']['max_drawdown_pct']:.1f}%</span></div>
<div class="ind"><span class="ind-l">VaR 95% (1d)</span><span class="ind-v mono">{tp['tail_risk_profile']['historical_var_95_1d_pct']:.1f}%</span></div>
<div class="ind"><span class="ind-l">ES 95% (1d)</span><span class="ind-v mono">{tp['tail_risk_profile']['expected_shortfall_95_1d_pct']:.1f}%</span></div>
</div>
<div class="setups"><strong>Setups ({len(tp['setups'])}):</strong><ul>{''.join(f'<li><strong>{s.get("name","?")}</strong> — score {s.get("score",0)}, dist {s.get("distance_to_confirmation_pct","?")}, <em>{s.get("status","?")}</em></li>' for s in tp['setups'])}</ul></div>
<ol class="non-conclusion">{''.join(f'<li>{c}</li>' for c in tp['non_conclusion'])}</ol>
<p class="lang-policy">🔒 Ngôn ngữ <code>neutral_descriptive_non_advice</code> — MÔ TẢ hồ sơ, KHÔNG verdict mua/bán.</p>
</div>
'''

# News section
cat_bd = news.get('category_breakdown', {})
def fmt_chip(cat, d):
    if isinstance(d, dict):
        sc = d.get('score','?'); cnt = d.get('count','?')
        cls = 'chip-bull' if isinstance(sc,(int,float)) and sc>=20 else 'chip-bear' if isinstance(sc,(int,float)) and sc<=-20 else 'chip-neu'
        summ = d.get('items_summary',''); short = (summ[:90]+'…') if len(summ)>90 else summ
        return f'<span class="cat-chip {cls}"><strong>{cat}</strong> · {cnt} bài · score {sc}<span class="chip-summary">{short}</span></span>'
    return f'<span class="cat-chip">{cat}: {d}</span>'

news_section = f'''
<div class="section-title"><span class="tag purple">09</span><h2>Tin tức 30 ngày · News Digest</h2><div class="divider-line"></div></div>
<div class="card news-card">
<div class="sentiment-box bullish">Sentiment: <strong>{news['sentiment_score']}/100</strong> · {news['sentiment_label']}</div>
<p class="news-caveat">⚠️ {news.get('verdict_note','')}</p>
<div class="news-cats">{''.join(fmt_chip(k,v) for k,v in (cat_bd.items() if isinstance(cat_bd,dict) else []))}</div>
<h4 class="news-sub">Top stories:</h4>
<ul class="stories">{''.join(f'<li><strong>{s.get("title","?")}</strong> <span class="src">({s.get("source","")}, {s.get("date","")})</span><br><span class="story-impact">{s.get("impact","")}</span></li>' for s in news.get('material_stories',[])[:5] if isinstance(s,dict))}</ul>
</div>
'''

# Independent view
view_section = f'''
<div class="section-title"><span class="tag cyan">10</span><h2>🎯 Quan điểm độc lập</h2><div class="divider-line"></div></div>
<div class="card view-card">
<h4 class="view-h">Điều quan trọng nhất với Coteccons</h4>
<p>Đây là bài toán kinh điển: <strong>thị trường định giá dưới sổ sách (P/B 0.85)</strong> nhưng P/E 32x — vì <strong>ROE chỉ 2.43%</strong>. Tài sản 34.4K tỷ tạo ra LNST 228 tỷ. Câu hỏi cốt lõi: backlog kỷ lục 65.5K tỷ + biên LN đang phục hồi (1.52%→2.28%) có đẩy ROE lên mức xứng đáng (10%+) không?</p>
<h4 class="view-h">Hiểu nhầm thường mắc</h4>
<p>Nhiều người nhìn LNST +117% và kết luận "tăng trưởng đỉnh". Thực ra tăng trưởng từ base rất thấp (FY24 biên 1.52%) — phần lớn là <strong>đòn bẩy hoạt động</strong> khi revenue +45% mà chi phí cố định không tăng tương ứng. Cần theo dõi biên gộp (3.71%) xem có bền không.</p>
<h4 class="view-h">Quan điểm giá</h4>
<p>Tech Score -6 (STRONG SELL) mâu thuẫn với Profile archetype "accumulation_breakout". Điều này nói lên sự phân ly: <strong>ngắn hạn xấu (channel giảm + bearish candlesticks), nhưng cấu trúc dài hạn có dấu hiệu tích lũy</strong> (nhiều double bottom, drawdown -24%). Chờ phá vỡ neckline 87,200-92,783đ với volume xác nhận.</p>
</div>
'''

# Extra CSS for new sections (technical/news/view) — append before </style>
extra_css = '''
.tech-card .tech-header{display:flex;gap:16px;align-items:center;margin-bottom:16px}
.tech-score{font-size:36px;font-weight:800;font-family:var(--font-mono)}
.tech-score.neg{color:var(--red)}
.verdict-sell{background:rgba(255,77,109,0.15);color:var(--red);padding:6px 14px;border-radius:8px;font-weight:700}
.ind-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;margin:12px 0}
.ind{background:var(--bg-2);border:1px solid var(--border);border-radius:8px;padding:8px 12px;display:flex;justify-content:space-between;gap:8px;font-size:12px}
.ind-l{color:var(--text-dim)}.ind-v{font-weight:600}
.patterns-note,.divergence-note{margin:10px 0;padding:10px 14px;background:var(--bg-2);border-radius:8px;font-size:13px}
.cyclical-note{font-size:12px;color:var(--amber);padding:8px 12px;background:rgba(251,191,36,0.06);border-radius:6px;margin-top:8px}
.profile-card .archetype-badge{display:inline-block;background:var(--grad-main);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:18px;font-weight:700;margin-bottom:8px}
.setups ul{margin:6px 0 0 16px;font-size:13px}.non-conclusion{margin:10px 0 0 18px;font-size:13px}
.lang-policy{font-size:11px;color:var(--cyan);padding:6px 10px;background:rgba(6,182,212,0.06);border-left:2px solid var(--cyan);margin-top:10px}
.sentiment-box{display:inline-block;padding:8px 16px;border-radius:8px;font-weight:600;margin-bottom:8px}
.sentiment-box.bullish{background:rgba(16,217,138,0.15);color:var(--green)}
.news-caveat{font-size:12px;color:var(--amber);margin:6px 0}
.news-cats{display:flex;flex-direction:column;gap:6px;margin:10px 0}
.cat-chip{background:var(--bg-2);border:1px solid var(--border);padding:8px 12px;border-radius:8px;font-size:12px}
.cat-chip.chip-bull{border-left:3px solid var(--green)}.cat-chip.chip-bear{border-left:3px solid var(--red)}.cat-chip.chip-neu{border-left:3px solid var(--amber)}
.cat-chip .chip-summary{display:block;color:var(--text-dim);font-size:11px;margin-top:3px}
.stories{list-style:none;padding:0;margin:10px 0}.stories li{padding:10px 0;border-bottom:1px solid rgba(139,92,246,0.08);font-size:13px}
.stories .src{color:var(--text-faint);font-size:11px}.story-impact{color:var(--text-dim);font-size:12px}
.view-card .view-h{color:var(--purple);margin:16px 0 6px;font-size:14px}.view-card p{font-size:13px;line-height:1.6}
.strat-table th{background:var(--bg-2);font-size:11px;color:var(--text-dim)}.strat-table td{font-size:13px}
.mult-card{background:var(--bg-2);border:1px solid var(--border);border-radius:10px;padding:14px;text-align:center}
.mult-card .m-label{font-size:11px;color:var(--text-faint);text-transform:uppercase}.mult-card .m-val{font-size:22px;font-weight:700;margin:4px 0}
.mult-card .m-note{font-size:11px;color:var(--text-dim)}.grid-4{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:12px 0}
.insights-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:12px 0}
.insight-col{background:var(--bg-2);border:1px solid var(--border);border-radius:12px;padding:16px}
.insight-col.bull{border-left:3px solid var(--green)}.insight-col.bear{border-left:3px solid var(--red)}
.insight-col .ic-head{font-weight:700;margin-bottom:10px;font-size:14px}
.insight-col ul{list-style:none;padding:0}.insight-col li{padding:6px 0;border-bottom:1px solid rgba(139,92,246,0.06);font-size:13px}
.rating-verdict{font-size:24px;font-weight:800;text-align:center;margin:10px 0}
.dupont-read p{margin:8px 0;font-size:13px}
.forecast-note{font-size:12px;color:var(--text-dim);padding:10px;background:var(--bg-2);border-radius:8px}
'''

# ===== READ TEMPLATE + FILL =====
html = TPL.read_text(encoding='utf-8')

# Insert extra CSS before </style>
html = html.replace('</style>', extra_css + '\n</style>', 1)

# Define ALL tokens BEFORE replace loop (lesson learned)
tokens = {}
tokens['{{TICKER}}'] = 'CTD'
tokens['{{TICKER_BADGE}}'] = '⚡ HOSE · Construction & Materials'
tokens['{{COMPANY_NAME}}'] = 'COTECCONS CONSTRUCTION'
tokens['{{COMPANY_SUB}}'] = 'Coteccons Construction JSC · Ngành: Xây dựng & Vật liệu · FY kết 30/06'
tokens['{{PRICE_DISPLAY}}'] = f'{price:,.0f}'
tokens['{{PRICE_META}}'] = f'<strong class="mono pos">{mcap/1e12:.2f}K tỷ đ</strong> · {shares/1e6:.1f}M CP · Cập nhật 08/07/2026'
tokens['{{UPDATE_BADGE}}'] = '08/07/2026'
tokens['{{YEAR_RANGE}}'] = 'FY2024–FY2025'
tokens['{{LATEST_YEAR}}'] = 'FY2025'
tokens['{{SECTION01_NOTE}}'] = '⚠️ BCTC community edition: chỉ 8 kỳ gần nhất → full-year có 2 năm'
tokens['{{KPI_STRIP}}'] = kpi_html
tokens['{{FIN_TABLE_HTML}}'] = fin_table
tokens['{{FIN_TABLE_FOOTNOTE}}'] = fin_footnote
tokens['{{CHART_REVNP_SUB}}'] = 'Doanh thu (bar) + LNST (line), tỷ VNĐ'
tokens['{{CHART_MARGIN_SUB}}'] = 'Biên LN (ROS) + ROE dashed'
tokens['{{CHART_PEPB_SUB}}'] = 'P/E (trái) + P/B (phải), dual-axis'
tokens['{{CHART_PRICEBV_SUB}}'] = 'Giá (line) vs BVPS (bar)'
tokens['{{TABLE5Y_SUB}}'] = '2 năm full (BCTC giới hạn 8 kỳ)'
tokens['{{FAIR_VALUE}}'] = f'{fair_value:.1f}'
tokens['{{GAUGE_VERDICT}}'] = verdict
tokens['{{GAUGE_DIFF_NOTE}}'] = f'Giá hiện <strong class="mono">{price/1000:.1f}K</strong> → {"đắt" if diff_pct>0 else "rẻ"} hơn ~{abs(diff_pct):.0f}% so median'
tokens['{{VAL_CARDS_HTML}}'] = val_cards
tokens['{{MULTIPLES_GRID_HTML}}'] = mult
tokens['{{DCF_GRAHAM_HTML}}'] = dcf_block
tokens['{{DUPONT_INTERPRETATION_HTML}}'] = dupont_interp
tokens['{{SUMMARY_STATS_HTML}}'] = f'<p class="footnote">9 PP hội tụ. Median <strong>{fair_value:.0f}K</strong>. Phân kỳ lớn giữa Graham (bảo thủ) và DCF bull (lạc quan) — phản ánh rủi ro ROE thấp.</p>'
tokens['{{INSIGHTS_GRID_HTML}}'] = insights
tokens['{{INSIGHTS_TITLE}}'] = 'Xây dựng · Bull vs Bear'
tokens['{{FORECAST_YEARS}}'] = 'FY26E–FY28E'
tokens['{{FORECAST_SUB}}'] = 'Backlog → revenue recognition'
tokens['{{RATING_HTML}}'] = rating
tokens['{{DISCLAIMER_HTML}}'] = disclaimer
tokens['{{FOOTER_HTML}}'] = footer
tokens['{{YEARS}}'] = json.dumps(years)
tokens['{{CHART_DATA}}'] = json.dumps({
    'revenue': rev, 'netProfit': np, 'eps': eps, 'bvps': bvps,
    'price': [p or 0 for p in price_yr], 'pe': pe, 'pb': pb, 'roe': roe, 'ros': ros,
    'dupMargin': [npm24, npm25], 'dupTurn': [turn24*100, turn25*100], 'dupLev': [lev24*100, lev25*100],
    'forecastYears': ['FY24','FY25','FY26E','FY27E','FY28E'],
    'forecastVol': [6886, 10007, 12000, 13500, 15000],
    'forecastNP': [105, 228, 350, 480, 620],
}, ensure_ascii=False)
tokens['{{SUMMARY_CHART_DATA}}'] = summary_data
tokens['{{SUMMARY_ANNOTATION}}'] = summary_annotation
tokens['{{SUMMARY_CHART_SUB}}'] = f'Giá hiện {price/1000:.0f}K (đường vàng) vs 9 PP định giá'

# Replace all tokens
for k, v in tokens.items():
    html = html.replace(k, str(v))

# Inject technical + news + view sections BEFORE disclaimer div
inject_point = '<div class="disclaimer">'
extra_sections = tech_section + news_section + view_section + '\n  '
html = html.replace(inject_point, extra_sections + inject_point, 1)

# Fix forecast chart label (CTD không phải thép)
html = html.replace("Sản lượng thép (tr.tấn)", "Backlog recognize (tỷ)")
html = html.replace("Triệu tấn", "Tỷ VNĐ")

OUT.write_text(html, encoding='utf-8')
print(f"Wrote {OUT} ({len(html):,} bytes)")

# Verify
remaining = sorted(set(re.findall(r'\{\{[A-Z_0-9]+\}\}', html)))
print(f"Unreplaced tokens: {remaining if remaining else 'NONE ✓'}")
print(f"Sections: {html.count('section-title')}")
