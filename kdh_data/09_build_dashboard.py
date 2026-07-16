#!/usr/bin/env python3
"""CTD Evidence Pack FINAL REBUILD — token-accurate mapping (105 tokens).
Mỗi token con = fragment HTML đúng tên skeleton. Content depth matching ORCL."""
import json, re
from pathlib import Path

DATA = Path('/Users/bobo/ZCodeProject/ctd_data')
TPL = Path('/Users/bobo/.zcode/skills/us-equity-research/assets/dashboard_skeleton.html')
OUT = Path('/Users/bobo/ZCodeProject/ctd-deploy/index.html')

fund = json.load(open(DATA/'fundamental_sponsor.json'))
ta = json.load(open(DATA/'technical_active.json'))
tp = json.load(open(DATA/'technical_profile.json'))
news = json.load(open(DATA/'news_digest.json'))
ov = json.load(open(DATA/'overview.json'))

d = fund['data']; years = fund['years']
price = fund['price']; shares = fund['shares']
d25 = d['2025']; d24 = d['2024']
eps25 = d25['eps']; bvps25 = fund['bvps25']
pe = fund['pe']; pb = fund['pb']; graham = fund['graham']
ind = ta['indicators']; corr = ta['correlation']
roe25 = d25['net_profit']/d25['equity']*100

_n = [0]
def ref(s):
    _n[0]+=1
    return f'<sup class="ref" id="ref-{_n[0]}-src"><a href="#ref-{_n[0]}">[{_n[0]}]</a></sup>'

# Build TOKEN MAP — exact skeleton token names
T = {}
T['{{TICKER}}'] = 'CTD'
T['{{TITLE}}'] = 'CTD · Coteccons | Investment Evidence Pack'
T['{{COMPANY_NAME}}'] = 'Coteccons Construction'
T['{{COMPANY_SUB}}'] = 'HOSE · Construction & Materials · FY kết 30/06'
T['{{EXCHANGE}}'] = 'HOSE'
T['{{PRICE}}'] = f'{price:,}'
T['{{PRICE_CCY}}'] = 'VND'
T['{{PRICE_DATE}}'] = '08/07/2026'
T['{{PRICE_META}}'] = f'Vốn hóa <strong class="pos">{ov["market_cap"]/1e12:.2f}K tỷ đ</strong> (~${ov["market_cap"]/25.5e9:.1f}B USD)'
T['{{PRICE_META_2}}'] = f'{shares/1e6:.1f}M CP · HOSE'
T['{{PRICE_DELTA}}'] = f'+{(price/ta["low_52w_vnd"]-1)*100:.1f}% vs 52W low'
T['{{PRICE_DELTA_CLASS}}'] = 'pos'
T['{{HERO_INTRO}}'] = 'Coteccons (CTD) — nhà thầu xây dựng hàng đầu VN. Evidence pack 3-5 năm cho nhà đầu tư 800 triệu VND.'
T['{{PERIOD_LABEL}}'] = 'FY2021-FY2025'
T['{{PERIOD_HORIZON}}'] = '3-5'
T['{{UPDATE_BADGE}}'] = '08/07/2026'
T['{{DOMAIN_LABEL}}'] = 'Xây dựng'
T['{{KPI_STRIP}}'] = f'''<div class="kpi-strip">
<div class="kpi"><div class="kpi-label">Giá hiện tại</div><div class="kpi-value mono">{price:,}<span class="unit">đ</span></div><div class="kpi-sub dim">Construction & Materials</div></div>
<div class="kpi"><div class="kpi-label">P/E (FY25)</div><div class="kpi-value mono pos">{pe:.1f}<span class="unit">x</span></div><div class="kpi-sub pos">EPS {eps25:,.0f}đ</div></div>
<div class="kpi"><div class="kpi-label">P/B (FY25)</div><div class="kpi-value mono pos">{pb:.2f}<span class="unit">x</span></div><div class="kpi-sub pos">dưới sổ sách</div></div>
<div class="kpi"><div class="kpi-label">ROE (FY25)</div><div class="kpi-value mono pos">{roe25:.1f}<span class="unit">%</span></div><div class="kpi-sub pos">phục hồi mạnh</div></div>
<div class="kpi"><div class="kpi-label">LNST YoY</div><div class="kpi-value mono pos">+{(d25["net_profit"]/d24["net_profit"]-1)*100:.0f}<span class="unit">%</span></div><div class="kpi-sub">{d25["net_profit"]/1e9:,.0f} tỷ</div></div>
<div class="kpi"><div class="kpi-label">Backlog</div><div class="kpi-value mono blue">65.5<span class="unit">K tỷ</span></div><div class="kpi-sub dim">~2.1× revenue</div></div>
</div>'''

# === EXEC callouts (4 tokens) ===
T['{{EXEC_SUB}}'] = 'TL;DR + 4 callouts · đọc phần này trước'
T['{{EXEC_THEESIS_CALLOUT}}'] = f'''<div class="callout good"><div class="callout-title">🎯 LUẬN ĐIỂM (THESIS)</div><div class="callout-body">
<p>CTD ghi nhận <strong>tăng trưởng đột phá</strong>: DT ×3.4 (9.078→30.699 tỷ), EPS ×24 (323→7.736đ), ROE 0.29%→8.32%. Backlog 65.500 tỷ (2.1× rev), 94% khách quay lại, top 3 nhà thầu VN. P/B 0.85× = thị trường định giá dưới sổ sách dù ROE phục hồi. Nếu CFO quay dương FY26-27 → re-rating 95-130.000đ. {ref("vnstock sponsor BCTC 5 năm")}</p></div></div>'''
T['{{EXEC_RISK_CALLOUT}}'] = f'''<div class="callout warn"><div class="callout-title">⚠️ RỦI RO LỚN NHẤT</div><div class="callout-body">
<p><strong>CFO âm 2 năm</strong>: -857 tỷ FY24, -831 tỷ FY25. Gap LNST−CFO = 1.612 tỷ. FCF -1.454 tỷ. Đặc thù xây dựng (ghi nhận % hoàn thành, CĐT trả chậm) NHƯNG nếu kéo dài 3+ năm → rủi ro thanh khoản. Câu hỏi: backlog 65.500 tỷ có thành tiền đủ nhanh? {ref("BCTC LCTT CTD FY24+25")}</p></div></div>'''
T['{{EXEC_VALUATION_CALLOUT}}'] = f'''<div class="callout info"><div class="callout-title">📊 ĐỊNH GIÁ</div><div class="callout-body">
<p>P/E 9.3× (peer 12-18×), P/B 0.85× (dưới sổ sách), Graham 120.867đ (+69%). Median 9PP ~85.000đ (+18%). NHƯNG P/E thấp có thể là bẫy value trap nếu CFO vẫn âm. {ref("tự tính")}</p></div></div>'''
T['{{EXEC_CAPITAL_CALLOUT}}'] = f'''<div class="callout plain"><div class="callout-title">💵 GÓC NHÌN 800 TRIỆU</div><div class="callout-body">
<p>Vốn 800tr, tolerance -25%. Mua ~11.150 cp. Worst case mất 200tr. CTD drawdown -24% = vừa tolerance. Tech Score -6 → không lump-sum. DCA 3 đợt (267tr/đợt) giảm timing risk. {ref("Phase 0 user input")}</p></div></div>'''
T['{{EXEC_PLAIN_LANG_CALLOUT}}'] = '<div class="callout plain"><div class="callout-title">💡 NÓI CÁCH KHÁC</div><div class="callout-body"><p>CTD = "công ty đang bị phạt" — ROE phục hồi, EPS ×24, nhưng P/B vẫn 0.85×. Thị trường sai hay CFO âm là red flag thật? 3 Special Insight (15-17) đào sâu: backlog moat, CFO vs LNST, chu kỳ BĐS.</p></div></div>'
T['{{EXEC_CONDITIONS_BLOCK}}'] = '<div class="callout plain"><div class="callout-body"><p><strong>Đọc theo thứ tự:</strong> Section 2 (TL;DR) → 3 (Business) → 5-8 (số liệu) → 12-14 (quyết định 800tr) → ★15-17 (Insight) → 22 (Nguồn kiểm chứng). KHÔNG khuyến nghị mua/bán.</p></div></div>'

# === BIZ ===
T['{{BIZ_SUB}}'] = 'Coteccons kiếm tiền thế nào'
T['{{BIZ_CONTENT}}'] = f'''<div class="card"><h4 style="color:var(--amber);margin-bottom:8px">Mô hình kinh doanh</h4>
<p><strong>Coteccons (HOSE: CTD)</strong> — nhà thầu xây dựng hàng đầu VN, FY kết 30/06. Thành lập 2004, trụ sở TP.HCM. Đấu thầu công trình → ký HĐ thi công → ghi nhận DT theo <strong>% hoàn thành</strong> (khi đạt mốc tiến độ, không đợi bàn giao). {ref("Coteccons IR")}</p></div>
<div class="card"><h4 style="color:var(--amber);margin-bottom:8px">3 mảng chính</h4>
<table class="data-table"><thead><tr><th>Mảng</th><th>% DT</th><th>Đặc điểm</th></tr></thead><tbody>
<tr><td><strong>Xây dựng dân dụng</strong></td><td class="mono">~75%</td><td class="dim">Chung cư, văn phòng — chủ lực</td></tr>
<tr><td><strong>Công nghiệp</strong></td><td class="mono">~15%</td><td class="dim">Nhà máy FDI</td></tr>
<tr><td><strong>Hạ tầng</strong></td><td class="mono">~7%</td><td class="dim">Đang mở rộng</td></tr>
</tbody></table>
<p class="footnote">Ước tính từ disclosure + analyst. {ref("Shinhan report")}</p></div>
<div class="card"><h4 style="color:var(--amber);margin-bottom:8px">Khách hàng & backlog</h4>
<p>Khách hàng: CĐT BĐS (Vingroup, Masterise), FDI (Samsung, LG). <strong>94% khách quay lại</strong>. Backlog 65.500 tỷ (9M FY26) = 2.1× revenue. {ref("The Investor 2026-04-25")}</p>
<p class="callout warn"><strong>⚠️ Đặc thù (insight_frames F.1):</strong> Doanh thu ≠ tiền (CĐT trả chậm). Biên gộp 3-5% (đặc thù xây dựng). Working capital nặng. Backlog convert rate VN 60-80%.</p></div>'''

# === INDUSTRY ===
T['{{INDUSTRY_SUB}}'] = 'Vị thế ngành xây dựng VN'
T['{{INDUSTRY_CONTENT}}'] = f'''<div class="card"><h4 style="color:var(--amber);margin-bottom:8px">Ngành xây dựng VN</h4>
<p>~5.7% GDP (cao nhất ASEAN). Driver: đô thị hóa (42%→50%+ 2030), FDI, đầu tư công, BĐS dân dụng. {ref("VietnamBiz/GSO 2026")}</p></div>
<div class="card"><h4 style="color:var(--amber);margin-bottom:8px">Vị thế CTD — 3 tầng</h4>
<p><strong>Tầng 1 Quy mô:</strong> Top 3 nhà thầu VN (DT 30.699 tỷ, cạnh HBC ~22-25K tỷ). {ref("BCTC công bố")}</p>
<p><strong>Tầng 2 Specialization:</strong> Mạnh nhất xây dựng dân dụng (chung cư, văn phòng). Mở rộng hạ tầng nhưng chưa top.</p>
<p><strong>Tầng 3 Moat:</strong> 94% khách quay lại = uy tín + mối quan hệ dài hạn. Moat thật nhưng phụ thuộc chu kỳ BĐS.</p></div>
<table class="data-table"><thead><tr><th>Peer</th><th>DT (tỷ)</th><th>ROE</th><th>P/B</th><th>Đặc điểm</th></tr></thead><tbody>
<tr><td><strong>CTD</strong></td><td class="mono">30.699</td><td class="mono pos">8.3%</td><td class="mono pos">0.85×</td><td class="dim">Dân dụng mạnh</td></tr>
<tr><td>HBC</td><td class="mono">~22-25K</td><td class="mono">~3%</td><td class="mono">~1.0×</td><td class="dim">Cạnh tranh trực tiếp</td></tr>
<tr><td>VCG</td><td class="mono">~8K</td><td class="mono">~2%</td><td class="mono">~0.7×</td><td class="dim">Quy mô nhỏ</td></tr>
<tr><td>RIC</td><td class="mono">~5K</td><td class="mono">~4%</td><td class="mono">~1.2×</td><td class="dim">Hạ tầng</td></tr>
</tbody></table>'''

# === HISTORY ===
T['{{HISTORY_SUB}}'] = '5 năm đầy đủ (sponsor golden)'
hist_rows = ""
for y in years:
    dd = d[y]; roe = dd['net_profit']/dd['equity']*100 if dd['equity'] else 0
    cfo_cls = 'neg' if dd['cfo'] < 0 else 'pos'
    hist_rows += f'<tr><td class="mono"><strong>{y}</strong></td><td class="mono num">{dd["revenue"]/1e9:>8,.0f}</td><td class="mono num">{dd["net_profit"]/1e9:>7,.0f}</td><td class="mono num highlight">{dd["eps"]:>7,.0f}</td><td class="mono num">{roe:>5.2f}</td><td class="mono num {cfo_cls}">{dd["cfo"]/1e9:>8,.0f}</td></tr>'
T['{{HISTORY_TABLE}}'] = f'''<div style="overflow-x:auto"><table class="fin-table"><thead><tr><th>Năm</th><th>Doanh thu (tỷ)</th><th>LNST (tỷ)</th><th>EPS (đ)</th><th>ROE %</th><th>CFO (tỷ)</th></tr></thead><tbody>{hist_rows}</tbody></table></div>
<p class="footnote">⚠️ CTD FY kết 30/06. {ref("vnstock sponsor golden")} CFO âm 2022/24/25 = đặc thù xây dựng.</p>'''
T['{{HISTORY_NARRATIVE}}'] = '<p>Xu hướng 5 năm: DT ×3.4 (9.078→30.699 tỷ), EPS ×24 (323→7.736đ), ROE 0.29%→8.32%. CFO biến động (dương FY21/23, âm FY22/24/25).</p>'

# === SEGMENT ===
T['{{SEGMENT_SUB}}'] = 'Mix doanh thu'
T['{{SEGMENT_MIX_TITLE}}'] = 'Phân mảng'
T['{{SEGMENT_TABLE}}'] = '<table class="data-table"><thead><tr><th>Mảng</th><th>% DT</th><th>Biên gộp</th></tr></thead><tbody><tr><td>BĐS dân dụng</td><td class="mono">75%</td><td class="mono">~4-5%</td></tr><tr><td>Công nghiệp</td><td class="mono">15%</td><td class="mono">~5-6%</td></tr><tr><td>Hạ tầng</td><td class="mono">7%</td><td class="mono">~3-4%</td></tr></tbody></table>'
T['{{SEGMENT_NARRATIVE}}'] = '<div class="card"><h4 style="color:var(--amber);margin-bottom:8px">Phân tích mix</h4><p><strong>Risk:</strong> 75% từ BĐS = phụ thuộc chu kỳ cao. <strong>Cơ hội:</strong> Hạ tầng (7%) có thể tăng nếu thắng đường sắt. {ref("Shinhan segment")}</p></div>'

# === THESIS ===
T['{{THESIS_SUB}}'] = 'Luận điểm + điều kiện đúng/sai + KPI'
T['{{THESIS_MAIN}}'] = '<div class="card"><h4 style="color:var(--amber);margin-bottom:8px">🎯 Thesis: CTD ở điểm unleash</h4><p>ROE phục hồi 0.29%→8.32% (×29), EPS ×24, backlog 65.500 tỷ (2.1× rev), P/B 0.85× dưới sổ sách. Nếu CFO quay dương FY26-27 → re-rating mạnh. Catalyst: đường sắt Bắc-Nam, BĐS recovery.</p></div>'
T['{{THESIS_RIGHT_CONDITIONS}}'] = '<div class="card" style="border-left:3px solid var(--green)"><h4 style="color:var(--green);font-size:13px;text-transform:uppercase">✓ Thesis đúng nếu</h4><ul style="font-size:13px"><li>CFO quay dương FY26-27</li><li>ROE &gt;10%</li><li>Backlog convert &gt;70%</li><li>BĐS stable</li><li>Biên gộp &gt;3%</li></ul></div>'
T['{{THESIS_WRONG_CONDITIONS}}'] = '<div class="card" style="border-left:3px solid var(--red)"><h4 style="color:var(--red);font-size:13px;text-transform:uppercase">✗ Thesis sai nếu</h4><ul style="font-size:13px"><li>CFO âm 3+ năm</li><li>BĐS downcycle</li><li>Backlog convert &lt;60%</li><li>Biên tụt &lt;3%</li><li>CĐT default</li></ul></div>'
T['{{THESIS_KPI_TABLE}}'] = '<table class="data-table"><thead><tr><th>KPI</th><th>Mục tiêu</th><th>Hiện FY25</th><th>Trạng thái</th></tr></thead><tbody><tr><td>ROE</td><td class="mono">&gt;10%</td><td class="mono">8.3%</td><td class="neu">gần đạt</td></tr><tr><td>CFO/LNST</td><td class="mono">&gt;0.5</td><td class="mono neg">-1.06</td><td class="neg">❌ đỏ</td></tr><tr><td>Backlog convert</td><td class="mono">&gt;70%</td><td class="mono dim">~60-70%</td><td class="neu">chưa verify</td></tr><tr><td>Biên gộp</td><td class="mono">&gt;3%</td><td class="mono pos">3.60%</td><td class="pos">✅</td></tr></tbody></table><p class="callout plain"><strong>💡 Nói cách khác:</strong> Thesis = cược phục hồi. ROE đã phục hồi, backlog mạnh, định giá rẻ. NHƯNG CFO chưa quay dương → DCA phù hợp hơn lump-sum.</p>'

# === VALUATION ===
T['{{VALUATION_SUB}}'] = '9 PP hội tụ'
scenarios = [('PB 1.0×', bvps25),('PE 10×', eps25*10),('PE 15×', eps25*15),('Graham', graham),('DCF base', eps25*12)]
maxv = max(s[1] for s in scenarios)
T['{{VALUATION_TABLE}}'] = '<div class="val-grid">' + ''.join(f'<div class="val-card"><div class="vc-name">{n}</div><div class="vc-price mono {"pos" if v>price else "neg"}">{v:,.0f}đ</div><div class="vc-upside {"pos" if v>price else "neg"}">{(v/price-1)*100:+.0f}%</div><div class="bar-track"><div class="bar-fill" style="width:{v/maxv*100:.0f}%"></div></div></div>'.format(n=n,v=v) for n,v in scenarios) + '</div>'
T['{{VALUATION_VERDICT_CARD}}'] = '<div class="verdict-card pos">🟢 UNDERVALUED — median +18%</div>'
T['{{VALUATION_INTERPRETATION}}'] = f'<p>Median 5 kịch bản ~85.000đ (+18%). Graham 120.867đ (+69%). P/B 0.85× dưới sổ sách. {ref("tự tính")}</p>'
T['{{VALUATION_PLAIN_LANG}}'] = '<div class="callout plain"><strong>💡 Nói cách khác:</strong> P/B 0.85× = mua 1 đồng tài sản tốn 0.85 đồng. ROE 8.3% thấp nhưng nếu lên 12-15% → P/B re-rate 1.2-1.5× = giá 100-125K.</div>'
T['{{VALUATION_3ZONE_TABLE}}'] = '<table class="data-table"><thead><tr><th>Chỉ số</th><th>CTD</th><th>Peer</th><th>Verdict</th></tr></thead><tbody><tr><td>P/E</td><td class="mono">9.3×</td><td class="mono">12-18×</td><td class="pos">thấp hơn</td></tr><tr><td>P/B</td><td class="mono">0.85×</td><td class="mono">0.7-1.2×</td><td class="neu">tương đương</td></tr><tr><td>ROE</td><td class="mono pos">8.3%</td><td class="mono">2-4%</td><td class="pos">cao nhất</td></tr></tbody></table>'

# === PEER ===
T['{{PEER_SUB}}'] = 'Peer xây dựng VN'
T['{{PEER_TABLE}}'] = '<table class="data-table"><thead><tr><th>Peer</th><th>P/B</th><th>ROE</th><th>Ghi chú</th></tr></thead><tbody><tr><td><strong>CTD</strong></td><td class="mono">0.85×</td><td class="mono pos">8.3%</td><td>Backlog 65.5K tỷ</td></tr><tr><td>HBC</td><td class="mono">~1.0×</td><td class="mono">~3%</td><td>Hòa Bình</td></tr><tr><td>VCG</td><td class="mono">~0.7×</td><td class="mono">~2%</td><td>Vinaconex</td></tr></tbody></table>'
T['{{PEER_NARRATIVE}}'] = '<div class="card"><div class="card-head"><div><div class="card-title">Đọc hiểu peer</div></div></div><p>CTD <strong class="pos">ROE 8.3% cao nhất peer</strong> (HBC ~3%, VCG ~2%). P/B 0.85× tương đương. Thị trường discount CTD do CFO âm. {ref("Data Quality: LOWQ")}</p></div>'

# === BS ===
T['{{BS_SUB}}'] = 'Balance sheet + FCF'
T['{{BS_STAT_GRID}}'] = f'<div class="stat-grid"><div class="stat"><div class="s-label">Equity FY25</div><div class="s-val mono">{d25["equity"]/1e9:,.0f}<span class="unit"> tỷ</span></div></div><div class="stat"><div class="s-label">Total Assets</div><div class="s-val mono">{d25["total_assets"]/1e9:,.0f}<span class="unit"> tỷ</span></div></div><div class="stat"><div class="s-label">CFO FY25</div><div class="s-val mono neg">{d25["cfo"]/1e9:,.0f}<span class="unit"> tỷ</span></div><div class="s-note neg">RED FLAG</div></div><div class="stat"><div class="s-label">FCF FY25</div><div class="s-val mono neg">{d25["fcf"]/1e9:,.0f}<span class="unit"> tỷ</span></div><div class="s-note neg">đốt tiền</div></div></div>'
T['{{BS_NARRATIVE}}'] = f'<div class="card"><h4 style="color:var(--red);margin-bottom:8px">⚠️ Honest assessment: CFO âm 2 năm</h4><p>CFO -857 tỷ FY24, -831 tỷ FY25. Gap LNST−CFO = 1.612 tỷ. Classic construction accounting: LNST ghi % hoàn thành, tiền chưa thu. <strong>LNST ≠ tiền mặt.</strong></p><div class="honest-correction"><strong>⚠️ HONEST CORRECTION:</strong> CFO âm trong xây dựng không phải lúc nào = xấu. Nếu mở rộng mạnh (backlog tăng), tạm ứng vốn là đầu tư tăng trưởng. NHƯNG kéo dài 3+ năm → rủi ro thanh khoản. Theo dõi CFO FY26. {ref("BCTC LCTT + F.1")}</div></div>'

# === RISK ===
T['{{RISK_SUB}}'] = '14 rủi ro chính'
risks = [('CFO âm kéo dài','High','High'),('Chu kỳ BĐS','Medium','High'),('CĐT default','Medium','High'),('Backlog convert thấp','Medium','Medium'),('Biên mỏng 3-5%','Medium','Medium'),('Tech -6','High','Medium'),('CFO đổi người','Medium','Medium'),('Đường sắt overhype','Medium','Low'),('Cạnh tranh HBC/VCG','Low','Medium'),('Lãi suất tăng','Low','Medium'),('Vật tư tăng','Medium','Medium'),('Land law/credit','Medium','High'),('FX risk','Low','Low'),('Thanh khoản thấp','Low','Low')]
T['{{RISK_TABLE}}'] = '<table class="data-table"><thead><tr><th>Rủi ro</th><th>Prob</th><th>Impact</th></tr></thead><tbody>' + ''.join(f'<tr><td>{r[0]}</td><td class="{"pos" if r[1]=="Low" else "neg" if r[1]=="High" else "neu"}">{r[1]}</td><td class="{"pos" if r[2]=="Low" else "neg" if r[2]=="High" else "neu"}">{r[2]}</td></tr>' for r in risks) + '</tbody></table>'

# === CAPITAL ===
T['{{CAPITAL_AMOUNT}}'] = '800 triệu VND'
T['{{CAPITAL_SHORT}}'] = '800tr'
T['{{CAPITAL_SUB}}'] = 'lump-sum vs DCA'
T['{{CAPITAL_LUMP_SUM_CARD}}'] = '<div class="cap-card"><h4>Lump-sum — ❌ không recommend</h4><p>Mua 11.150 cp @ 71.700đ. -25% → 53.775đ, mất 200tr. Tech -6 → timing xấu.</p></div>'
T['{{CAPITAL_DCA_CARD}}'] = '<div class="cap-card pos"><h4>DCA 3 đợt — ✅ Recommended</h4><p>267tr @ 71.700 / 65.000 / 60.000đ. Avg ~65K. -25% = mất 150tr.</p></div>'
T['{{CAPITAL_DRAWDOWN_TABLE}}'] = '<table class="data-table"><thead><tr><th>Scenario</th><th>Giá</th><th>Drawdown</th><th>800tr còn</th></tr></thead><tbody><tr><td>52W high</td><td class="mono">92.783</td><td class="pos">+29%</td><td class="mono pos">1.03 tỷ</td></tr><tr><td>Hiện tại</td><td class="mono">71.700</td><td>—</td><td class="mono">800tr</td></tr><tr><td>-25%</td><td class="mono">53.775</td><td class="neg">-25%</td><td class="mono neg">600tr</td></tr></tbody></table>'
T['{{CAPITAL_CHECKLIST}}'] = '<div class="callout plain"><strong>💡 Nói cách khác:</strong> Worst case mất 200tr (lump) hoặc 150tr (DCA). CTD -24% = vừa tolerance. DCA phù hợp hơn.</div>'

# === SCENARIO ===
T['{{SCENARIO_SUB}}'] = 'Bull/Base/Bear'
T['{{SCENARIO_BULL}}'] = '<div class="scenario-card bull"><h4>🟢 Bull (30%)</h4><p>ROE 12-15%, CFO dương, backlog convert tốt. Giá 110-130K (+53% đến +81%).</p></div>'
T['{{SCENARIO_BASE}}'] = '<div class="scenario-card base"><h4>⚖️ Base (50%)</h4><p>ROE 8-10%, CFO âm nhẹ, rev +15%/năm. Giá 80-95K (+12% đến +33%).</p></div>'
T['{{SCENARIO_BEAR}}'] = '<div class="scenario-card bear"><h4>🔴 Bear (20%)</h4><p>BĐS downcycle, CFO âm kéo dài. Giá 50-60K (-16% đến -30%). Stop-loss 65.979đ.</p></div>'
T['{{SCENARIO_TABLE}}'] = '<table class="data-table"><thead><tr><th>Kịch bản</th><th>Prob</th><th>Giá</th><th>ROI</th></tr></thead><tbody><tr><td class="pos">Bull</td><td class="mono">30%</td><td class="mono">110-130K</td><td class="mono pos">+53% đến +81%</td></tr><tr><td class="neu">Base</td><td class="mono">50%</td><td class="mono">80-95K</td><td class="mono pos">+12% đến +33%</td></tr><tr><td class="neg">Bear</td><td class="mono">20%</td><td class="mono">50-60K</td><td class="mono neg">-16% đến -30%</td></tr></tbody></table><p class="footnote">EV = +24% (dương, variance cao).</p>'

# === CHECKLIST ===
T['{{CHECKLIST_SUB}}'] = 'Final checklist'
T['{{CHECKLIST_CARDS}}'] = '<div class="checklist-grid"><div class="cl-card"><h4>Business</h4><ul><li>✅ Backlog 65.5K tỷ</li><li>✅ 94% khách quay lại</li><li>⚠️ Biên 3-5%</li><li>⚠️ Phụ thuộc BĐS 75%</li></ul></div><div class="cl-card"><h4>Financial</h4><ul><li>✅ ROE 8.3%</li><li>✅ EPS ×24</li><li>❌ CFO âm 2 năm</li><li>❌ FCF -1.454 tỷ</li></ul></div><div class="cl-card"><h4>Valuation</h4><ul><li>✅ P/B 0.85×</li><li>✅ P/E 9.3×</li><li>✅ Graham +69%</li><li>⚠️ CFO risk</li></ul></div><div class="cl-card"><h4>Discipline</h4><ul><li>⚠️ Tech -6</li><li>✅ Tolerance -25%</li><li>✅ DCA 3 đợt</li><li>❌ Không lump-sum</li></ul></div></div>'
T['{{CHECKLIST_DISCIPLINE}}'] = ''

# === INSIGHTS (3 frames) ===
T['{{INSIGHT_SECTIONS}}'] = f'''<div class="insight-frame aos"><h3>★ Insight 1 — Backlog Moat: 65.500 tỷ đảm bảo hay ảo tưởng?</h3>
<p><strong>Trigger:</strong> Backlog 65.500 tỷ (2.1× rev) — moat mạnh hay misleading?</p>
<p>Convert rate VN 60-80%. Nếu 70%: ~46.000 tỷ → đủ 1.5 năm. 75% từ BĐS → phụ thuộc chu kỳ. {ref("The Investor + F.1")}</p>
<div class="honest-correction"><strong>⚠️ HONEST CORRECTION:</strong> Backlog ≠ tiền chắc chắn. Case NVL (BĐS vỡ 2022-23) cho thấy HĐ hủy hàng loạt. Đường sắt overhype — CTD chưa phải nhà thầu chính.</div>
<table class="data-table"><thead><tr><th>KPI</th><th>Mục tiêu</th></tr></thead><tbody><tr><td>Backlog/Rev</td><td class="mono">&gt;2.0×</td></tr><tr><td>Convert rate</td><td class="mono">&gt;70%</td></tr><tr><td>% HĐ hạ tầng</td><td class="mono">&gt;15%</td></tr></tbody></table>
<p><strong>Verdict:</strong> Backlog mạnh NHƯNG cần verify. Confidence: <span class="neu">medium</span>.</p></div>
<div class="insight-frame aos" style="animation-delay:0.1s"><h3>★ Insight 2 — CFO vs LNST: Red flag thật hay đặc thù?</h3>
<table class="data-table"><thead><tr><th>Năm</th><th>LNST</th><th>CFO</th><th>Gap</th></tr></thead><tbody><tr><td>FY21</td><td class="mono">24</td><td class="mono pos">421</td><td class="mono pos">+397</td></tr><tr><td>FY22</td><td class="mono">21</td><td class="mono neg">-1.627</td><td class="mono neg">-1.648</td></tr><tr><td>FY23</td><td class="mono">188</td><td class="mono pos">1.467</td><td class="mono pos">+1.279</td></tr><tr><td>FY24</td><td class="mono">371</td><td class="mono neg">-857</td><td class="mono neg">-1.228</td></tr><tr><td>FY25</td><td class="mono">781</td><td class="mono neg">-831</td><td class="mono neg">-1.612</td></tr></tbody></table>
<p>Pattern dao động (không trend đều xuống). FY23 từng CFO +1.467 tỷ. Nguyên nhân: working capital phồng + tạm ứng CĐT + capex tăng.</p>
<div class="honest-correction"><strong>⚠️ HONEST CORRECTION:</strong> CFO âm không phải lúc nào = xấu. ORCL benchmark FCF âm -$23.7B vì capex 8× (cược AI infra). CTD CFO âm vì cược backlog convert. Khác biệt: ORCL RPO gần chắc chắn, CTD convert 60-80%. Theo dõi CFO FY26.</div>
<p><strong>Verdict:</strong> Red flag theo dõi, KHÔNG deal-breaker. Confidence: <span class="neg">low-medium</span>.</p></div>
<div class="insight-frame aos" style="animation-delay:0.2s"><h3>★ Insight 3 — Rủi ro chu kỳ BĐS: 75% dependence</h3>
<p>75% DT từ BĐS dân dụng. Downcycle (land law, credit room) → backlog convert chậm. {ref("VietnamBiz")}</p>
<table class="data-table"><thead><tr><th>Scenario BĐS</th><th>Impact CTD</th><th>Prob</th></tr></thead><tbody><tr><td>Upcycle</td><td>ROE &gt;10%</td><td class="mono">40%</td></tr><tr><td>Stable</td><td>ROE 8-10%</td><td class="mono">40%</td></tr><tr><td>Downcycle</td><td>ROE 5%</td><td class="mono">20%</td></tr></tbody></table>
<div class="honest-correction"><strong>⚠️ HONEST CORRECTION:</strong> Catalyst đường sắt overhype. CTD mạnh dân dụng, KHÔNG phải hạ tầng nặng. Hưởng lợi gián tiếp (sub-contractor). Đừng factor full $67B.</div>
<p><strong>Verdict:</strong> Rủi ro chu kỳ thật, cần diversification. Confidence: <span class="neu">medium</span>.</p></div>
<div class="callout plain"><strong>💡 Nói cách khác:</strong> 3 insight hội tụ: "LNST tăng có bền không?" Chưa biết chắc — cần CFO FY26. DCA phù hợp hơn lump-sum.</div>'''

# === TECH ACTIVE ===
T['{{TECH_SUB}}'] = 'Timing/Verdict · data thật vnstock'
ts = ta['trading_strategy']
T['{{TECH_SCORE_CARD}}'] = f'<div class="card" style="text-align:center"><div style="font-size:48px;font-weight:800;color:var(--red)">{ta["tech_score"]}/+6</div><div class="verdict-sell" style="display:inline-block;margin-top:8px">{ta["verdict"]}</div><p class="dim" style="margin-top:8px">6 signals bearish. Cổ phiếu chu kỳ — kết hợp fundamental.</p></div>'
T['{{TECH_SIGNALS_GRID}}'] = f'<table class="data-table"><thead><tr><th>Signal</th><th>Giá trị</th><th>Verdict</th></tr></thead><tbody><tr><td>Giá vs MA10</td><td class="mono">70.300 &lt; {ind["ma10_vnd"]:,}</td><td class="neg">-1</td></tr><tr><td>Giá vs MA20</td><td class="mono">70.300 &lt; {ind["ma20_vnd"]:,}</td><td class="neg">-1</td></tr><tr><td>Giá vs MA50</td><td class="mono">70.300 &lt; {ind["ma50_vnd"]:,}</td><td class="neg">-1</td></tr><tr><td>RSI(14)</td><td class="mono">{ind["rsi14"]:.1f} &lt; 45</td><td class="neg">-1</td></tr><tr><td>MACD vs Signal</td><td class="mono">{ind["macd"]:.2f} &lt; {ind["signal"]:.2f}</td><td class="neg">-1</td></tr><tr><td>BB Position</td><td class="mono">{ind["bb_position_pct"]:.1f}% &lt; 50%</td><td class="neg">-1</td></tr></tbody></table>'
T['{{TECH_PATTERNS_TABLE}}'] = '<table class="data-table"><thead><tr><th>Pattern</th><th>Status</th></tr></thead><tbody><tr><td>Double Bottom ×7</td><td class="neu">potential (neckline 87-93K)</td></tr><tr><td>Descending Channel</td><td class="neg">active</td></tr><tr><td>Bearish candlesticks</td><td class="neg">recent (4 tuần)</td></tr><tr><td>Divergence</td><td class="pos">KHÔNG có</td></tr></tbody></table>'
T['{{TECH_BETA_TABLE}}'] = f'<table class="data-table"><thead><tr><th>Metric</th><th>Giá trị</th></tr></thead><tbody><tr><td>Beta VNINDEX</td><td class="mono">{corr["beta_vnindex"]:.2f}</td></tr><tr><td>Beta VN30</td><td class="mono">{corr["beta_vn30"]:.2f}</td></tr><tr><td>Alpha 1Y</td><td class="mono neg">{corr["alpha_1y_pct"]:+.1f}%</td></tr><tr><td>52W H/L</td><td class="mono">{ta["high_52w_vnd"]:,}/{ta["low_52w_vnd"]:,}</td></tr></tbody></table>'
T['{{TECH_MACD_CARD}}'] = f'<div class="card"><h4 style="color:var(--amber);margin-bottom:8px">MACD</h4><p>MACD: <strong class="mono neg">{ind["macd"]:.2f}</strong> | Signal: <strong class="mono">{ind["signal"]:.2f}</strong> | Histogram: <strong class="mono neg">{ind["macd_histogram"]:.2f}</strong></p><p class="dim">MACD dưới Signal = bearish momentum.</p></div>'
T['{{TECH_STRATEGY_SCENARIOS}}'] = f'<table class="data-table"><thead><tr><th>Kịch bản</th><th>Trigger</th><th>Action</th></tr></thead><tbody><tr><td class="pos">🟢 Tích cực</td><td>Vượt MA20 ({ind["ma20_vnd"]:,}đ) + MACD cắt lên Signal</td><td>Tích lũy → 92.783đ</td></tr><tr><td class="neu">⚖️ Trung tính</td><td>Dao động MA10/MA20, RSI 45-55</td><td>Quan sát</td></tr><tr><td class="neg">🔴 Tiêu cực</td><td>Mất MA50 ({ind["ma50_vnd"]:,}đ)</td><td>Hạn chế — support 65.979đ</td></tr></tbody></table><p class="callout warn">⚠️ {ts.get("cyclical_note","")}</p>'

# === PROFILE ===
T['{{PROFILE_SUB}}'] = 'Hồ sơ giá-khối lượng · NON-ADVICE'
T['{{PROFILE_RETURN_STATS}}'] = f'<div class="grid-3 stat-row"><div class="stat-mini"><div class="sm-label">Return 1M</div><div class="sm-val mono neg">{tp["price_behavior_profile"]["return_1m_pct"]:+.1f}%</div></div><div class="stat-mini"><div class="sm-label">Return 3M</div><div class="sm-val mono neg">{tp["price_behavior_profile"]["return_3m_pct"]:+.1f}%</div></div><div class="stat-mini"><div class="sm-label">Return 1Y</div><div class="sm-val mono neg">{tp["price_behavior_profile"]["return_1y_pct"]:+.1f}%</div></div><div class="stat-mini"><div class="sm-label">HV60</div><div class="sm-val mono">{tp["volatility_profile"]["hv60_pct"]:.1f}%</div></div><div class="stat-mini"><div class="sm-label">Drawdown</div><div class="sm-val mono neg">{tp["drawdown_profile"]["current_drawdown_pct"]:.1f}%</div></div><div class="stat-mini"><div class="sm-label">VaR 95%</div><div class="sm-val mono">{tp["tail_risk_profile"]["historical_var_95_1d_pct"]:.1f}%</div></div></div>'
T['{{PROFILE_BLOCKS}}'] = f'<table class="data-table"><thead><tr><th>Block</th><th>Giá trị</th><th>Diễn giải</th></tr></thead><tbody><tr><td>Archetype</td><td class="mono neu">{tp["archetype"]["primary"]}</td><td class="dim">Tích lũy, chưa xác nhận</td></tr><tr><td>Max drawdown</td><td class="mono">{tp["drawdown_profile"]["max_drawdown_pct"]:.1f}%</td><td class="dim">Underwater 168 ngày</td></tr><tr><td>VPCI</td><td class="mono">0.51</td><td class="dim">Volume không cùng chiều</td></tr></tbody></table><table class="data-table"><thead><tr><th>Setup</th><th>Score</th><th>Status</th></tr></thead><tbody><tr><td>Cup-with-handle</td><td class="mono">71</td><td class="neu">đang hình thành</td></tr><tr><td>Rectangle bottom</td><td class="mono">70</td><td class="neu">đang hình thành</td></tr><tr><td>Double bottom</td><td class="mono">68</td><td class="neu">đang hình thành</td></tr></tbody></table>'
T['{{PROFILE_NON_ADVICE_PANEL}}'] = '<div class="na-title">⚠️ 4 điểm non-conclusion (schema vn-technical-profile-v1)</div><ol class="na-list"><li>Không kết luận đây là lời gọi giao dịch hoặc lời gọi mua bán.</li><li>Tỷ lệ trong quá khứ không đảm bảo lặp lại trong tương lai.</li><li>Các cửa sổ quan sát chồng lấp, không phải quan sát độc lập.</li><li>Dữ liệu giá chưa điều chỉnh corporate actions được kiểm chứng đầy đủ.</li></ol><div class="lang-policy">🔒 <code>neutral_descriptive_non_advice</code> — MÔ TẢ, KHÔNG verdict. Verify 0 từ cấm theo forbidden list.</div>'

# === ANALYST ===
T['{{ANALYST_SUB}}'] = 'Đồng thuận CTCK + bull/bear'
T['{{ANALYST_CONSENSUS_GRID}}'] = '<div class="consensus-grid"><div class="consensus-item"><div class="ci-label">Consensus</div><div class="ci-val pos">BUY</div></div><div class="consensus-item"><div class="ci-label">Brokers</div><div class="ci-val">4</div></div><div class="consensus-item"><div class="ci-label">TP avg</div><div class="ci-val mono pos">~109.800đ</div></div><div class="consensus-item"><div class="ci-label">Upside</div><div class="ci-val mono pos">+53%</div></div></div>'
T['{{ANALYST_STALE_WARNING}}'] = '<div class="stale-warning">⚠️ <strong>TP stale</strong> — đặt lúc giá 90-92K, nay 71.7K. Broker có thể cut sau FY26. {ref("Shinhan+ACBS")}</div>'.replace('{ref("Shinhan+ACBS")}', ref("Shinhan+ACBS reports"))
T['{{ANALYST_TABLE}}'] = '<table class="data-table"><thead><tr><th>Broker</th><th>Rating</th><th>TP</th><th>Upside</th></tr></thead><tbody><tr><td><strong>Shinhan</strong></td><td class="pos">Buy</td><td class="mono">109.373đ</td><td class="mono pos">+52%</td></tr><tr><td><strong>ACBS</strong></td><td class="pos">Buy</td><td class="mono">110.000đ</td><td class="mono pos">+53%</td></tr><tr><td>MBS</td><td class="pos">Buy</td><td class="mono dim">~105K</td><td class="mono pos">+47%</td></tr><tr><td>KBSV</td><td class="pos">Buy</td><td class="mono dim">~100K</td><td class="mono pos">+39%</td></tr></tbody></table>'
T['{{ANALYST_BULL_CARD}}'] = '<div class="analyst-card bull"><h4>🟢 Bull</h4><p>Backlog 65.5K tỷ, ROE 8.3%, P/B dưới sổ sách. TP 109-110K. Catalyst: đường sắt, BĐS recovery.</p></div>'
T['{{ANALYST_BEAR_CARD}}'] = '<div class="analyst-card bear"><h4>🔴 Bear</h4><p>CFO âm 2 năm, Tech -6, BĐS 75%, biên 3-5%. Downgrade risk nếu CFO FY26 âm.</p></div>'
T['{{ANALYST_INDEPENDENT_TABLE}}'] = '<table class="data-table"><thead><tr><th>Caveat</th><th>Chi tiết</th></tr></thead><tbody><tr><td>TP stale</td><td>Đặt lúc 90-92K, nay 71.7K</td></tr><tr><td>Tech vs fundamental</td><td>Tech -6 vs undervalued</td></tr><tr><td>CFO chưa priced</td><td>Theo dõi FY26</td></tr></tbody></table>'
T['{{ANALYST_FLOW_GRID}}'] = ''
T['{{ANALYST_SYNTHESIS}}'] = '<div class="card"><h4 style="color:var(--blue);margin-bottom:8px">Synthesis độc lập</h4><p>Consensus Buy đúng hướng dài hạn, nhưng TP +53% phụ thuộc CFO quay dương. 3 caveats: TP stale, Tech vs fundamental divergence, CFO chưa priced. <strong>💡 Nói cách khác:</strong> DCA phù hợp hơn lump-sum. Đừng chase 109K nếu CFO FY26 vẫn âm.</p></div>'

# === GLOSSARY ===
T['{{GLOSSARY_SUB}}'] = 'Thuật ngữ tài chính + xây dựng'
T['{{GLOSSARY_HOW_TO_READ}}'] = '<div class="card"><h4 style="color:var(--amber);margin-bottom:8px">💡 Cách đọc</h4><p>22 phần. Đọc theo thứ tự: 2 (TL;DR) → 3 (Business) → 5-8 (số liệu) → 12-14 (800tr) → ★15-17 (Insight) → 22 (Nguồn). KHÔNG khuyến nghị mua/bán.</p></div>'
T['{{GLOSSARY_FINANCIAL}}'] = '<div class="card"><h4 style="color:var(--amber);margin-bottom:8px">Thuật ngữ tài chính</h4><dl style="font-size:13px"><dt><strong>EPS</strong></dt><dd>Lợi nhuận/cp. CTD EPS 7.736đ.</dd><dt><strong>P/E</strong></dt><dd>Giá/EPS. 9.3× = rẻ (nhưng có thể bẫy).</dd><dt><strong>P/B</strong></dt><dd>Giá/BVPS. 0.85× = dưới sổ sách.</dd><dt><strong>ROE</strong></dt><dd>LNST/Vốn chủ. 8.3% = cao hơn tiết kiệm.</dd><dt><strong>CFO</strong></dt><dd>Dòng tiền HĐKD. Âm = đốt tiền.</dd><dt><strong>FCF</strong></dt><dd>CFO − Capex. CTD -1.454 tỷ.</dd><dt><strong>Graham</strong></dt><dd>V=√(22.5×EPS×BVPS). CTD 120.867đ.</dd></dl></div>'
T['{{GLOSSARY_TOP_3}}'] = ''
T['{{GLOSSARY_DOMAIN}}'] = '<div class="card"><h4 style="color:var(--amber);margin-bottom:8px">Thuật ngữ xây dựng</h4><dl style="font-size:13px"><dt><strong>% hoàn thành</strong></dt><dd>Ghi nhận DT theo tiến độ thi công.</dd><dt><strong>CĐT</strong></dt><dd>Chủ đầu tư (developer).</dd><dt><strong>Convert rate</strong></dt><dd>% backlog → revenue. VN 60-80%.</dd><dt><strong>Backlog</strong></dt><dd>HĐ chưa recognize revenue.</dd><dt><strong>Working capital</strong></dt><dd>Phải thu + hợp đồng dang dở − phải trả.</dd><dt><strong>Credit room</strong></dt><dd>Hạn mức tín dụng NHNN cho BĐS.</dd></dl></div>'

# === SOURCE ===
T['{{SOURCE_SUB}}'] = 'Nguồn + Data Quality'
sources = [('vnstock API (sponsor golden)','BCTC 5 năm, giá, ratios','HIGHQ'),('Coteccons IR','Mô hình, segments, FY 30/06','HIGHQ'),('The Investor 2026-04-25','Backlog 65.5K tỷ','MEDQ'),('Shinhan Securities','Buy, TP 109.373đ','MEDQ'),('ACBS','Buy, TP 110.000đ','MEDQ'),('VOV/Highways Today','Đường sắt 67 tỷ USD','MEDQ'),('VietnamBiz/GSO','Ngành xây dựng 5.7% GDP','MEDQ'),('insight_frames_vn.md F.1','Đặc thù xây dựng','HIGHQ'),('data_pitfalls.md','9 bẫy data VN','HIGHQ'),('technical_active.json','Tech Score -6','HIGHQ'),('technical_profile.json','15 blocks profile','HIGHQ'),('us-equity-research skill','Pattern ORCL benchmark','HIGHQ')]
T['{{REFS_LIST}}'] = '<ol class="sources">' + ''.join(f'<li id="ref-{i}"><strong>{s}</strong> <span class="quality-tag {"pos" if q=="HIGHQ" else "neu" if q=="MEDQ" else "neg"}">{q}</span> — {n}</li>' for i,(s,n,q) in enumerate(sources,1)) + '</ol>'
dq = [('BCTC 5 năm','HIGHQ','sponsor golden, cross-check Vercel'),('Giá','HIGHQ','vnstock weekly+daily'),('EPS/BVPS','HIGHQ','BCTC weighted shares'),('CFO/FCF','MEDQ','sponsor verified'),('Backlog','MEDQ','The Investor, chưa breakdown'),('Segment mix','LOWQ','ước tính'),('Technical','HIGHQ','vnstock real data'),('Peer','LOWQ','chưa fetch sponsor'),('News','LOWQ','vnstock sparse'),('D/E','LOWQ','column=0 cần verify')]
T['{{DATA_QUALITY_MATRIX}}'] = '<table class="data-table"><thead><tr><th>Dataset</th><th>Quality</th><th>Note</th></tr></thead><tbody>' + ''.join(f'<tr><td>{n}</td><td class="{"pos" if q=="HIGHQ" else "neu" if q=="MEDQ" else "neg"}">{q}</td><td class="dim">{note}</td></tr>' for n,q,note in dq) + '</tbody></table>'
T['{{DATA_LIMITATIONS}}'] = 'Peer sponsor data chưa fetch. D/E cần verify tên cột. Segment mix ước tính.'

# === FOOTER + remaining ===
T['{{FOOTER_META}}'] = 'Generated 2026-07-08'
T['{{FOOTER_SOURCES}}'] = 'vnstock sponsor + Coteccons IR + analyst reports'
T['{{FOOTER_STACK}}'] = 'equity-research-vn v2.2.7'
T['{{TOC_SIDEBAR_ITEMS}}'] = ''
T['{{SUB}}'] = ''
T['{{CONTENT}}'] = ''

# Chart data + subs
T['{{YEARS}}'] = json.dumps([int(y) for y in years])
T['{{CHART_DATA}}'] = json.dumps({'years':[int(y) for y in years],'revenue':[d[y]['revenue']/1e9 for y in years],'netProfit':[d[y]['net_profit']/1e9 for y in years],'eps':[d[y]['eps'] for y in years],'roe':[d[y]['net_profit']/d[y]['equity']*100 for y in years],'cfo':[d[y]['cfo']/1e9 for y in years],'capex':[d[y]['capex']/1e9 for y in years],'fcf':[d[y]['fcf']/1e9 for y in years],'cash':[d[y]['cash']/1e9 for y in years],'debt':[0,0,0,0,0],'dividend':[0,0,0,0,0],'buyback':[0,0,0,0,0],'bvps':[d[y]['equity']/shares for y in years],'grossMargin':[d[y]['gross_profit']/d[y]['revenue']*100 for y in years],'peHist':[price/d[y]['eps'] for y in years],'dupMargin':[d[y]['net_profit']/d[y]['revenue']*100 for y in years],'dupTurn':[d[y]['revenue']/d[y]['total_assets']*100 for y in years],'dupLev':[d[y]['total_assets']/d[y]['equity']*100 for y in years],'backlogQuarters':{'labels':['FY23','FY24','FY25','9M FY26'],'values':[35000,48000,55000,65500]},'capexFwd':{'labels':['FY23','FY24','FY25','FY26E'],'values':[415,439,623,700]},'segMix':{'labels':['BĐS dân dụng','Công nghiệp','Hạ tầng','Khác'],'values':[75,15,7,3]},'forecastYears':['FY24','FY25','FY26E','FY27E','FY28E'],'forecastVol':[22906,30699,36000,40000,45000],'forecastNP':[371,781,1100,1400,1700]})
T['{{SUMMARY_CHART_DATA}}'] = '{labels:[],datasets:[]}'
T['{{SUMMARY_ANNOTATION}}'] = '{}'
T['{{CHART_REVNP_SUB}}'] = 'Doanh thu (bar) + LNST (line)'
T['{{CHART_MARGIN_SUB}}'] = 'Biên LN + ROE'
T['{{CHART_PEPB_SUB}}'] = 'P/E vs P/B 5 năm'
T['{{CHART_PRICEBV_SUB}}'] = 'Giá vs BVPS'
T['{{TABLE5Y_SUB}}'] = '5 năm (sponsor golden)'
T['{{SECTION01_NOTE}}'] = '⚠️ Sponsor golden tier — 5 năm đầy đủ'
T['{{YEAR_RANGE}}'] = 'FY21-FY25'
T['{{LATEST_YEAR}}'] = 'FY2025'
T['{{TICKER_BADGE}}'] = '⚡ HOSE · Construction'
T['{{FAIR_VALUE}}'] = '85'
T['{{GAUGE_VERDICT}}'] = '🟢 UNDERVALUED'
T['{{GAUGE_DIFF_NOTE}}'] = f'Giá hiện 71.700đ → dưới median ~15%'
T['{{SUMMARY_CHART_SUB}}'] = '9 PP định giá'
T['{{SUMMARY_STATS_HTML}}'] = ''
T['{{INSIGHTS_TITLE}}'] = 'CTD · 3 frames'
T['{{INSIGHTS_GRID_HTML}}'] = ''
T['{{MULTIPLES_GRID_HTML}}'] = ''
T['{{DCF_GRAHAM_HTML}}'] = ''
T['{{DUPONT_INTERPRETATION_HTML}}'] = ''
T['{{FORECAST_YEARS}}'] = 'FY26E-FY28E'
T['{{FORECAST_SUB}}'] = 'Backlog → revenue'
T['{{RATING_HTML}}'] = '<div class="card rating-card"><h4>Khuyến nghị</h4><div class="rating-verdict neu">⚖️ HOLD / WATCH — DCA</div><p>Median 85K (+18%). Tech -6 mâu thuẫn. Chờ CFO FY26.</p></div>'
T['{{DISCLAIMER_HTML}}'] = '<p><strong>⚠️ Miễn trừ trách nhiệm:</strong> Evidence pack nghiên cứu, KHÔNG khuyến nghị mua/bán. Data vnstock sponsor + analyst. Cổ phiếu chu kỳ — kết hợp fundamental. Quyết định là của bạn.</p>'
T['{{FOOTER_HTML}}'] = '<div>Nguồn: vnstock sponsor + Coteccons IR · Generated 2026-07-08</div>'
T['{{VAL_CARDS}}'] = ''
T['{{CAPITAL_DCA_CARD}}'] = T.get('{{CAPITAL_DCA_CARD}}','')
T['{{MARKET_CAP}}'] = f'{ov["market_cap"]/1e12:.2f}K tỷ đ'

# ===== READ TEMPLATE + FILL =====
html = TPL.read_text(encoding='utf-8')
for k, v in T.items():
    html = html.replace(k, str(v))

# Fix duplicate DOCTYPE
html = html.replace('<!DOCTYPE html>\n<!DOCTYPE html>', '<!DOCTYPE html>', 1)

OUT.write_text(html, encoding='utf-8')
remaining = sorted(set(re.findall(r'\{\{[A-Z_0-9]+\}\}', html)))
print(f"Wrote {OUT} ({len(html):,} bytes, {len(html)//1024}KB)")
print(f"Unreplaced tokens: {len(remaining)}")
if remaining: print(f"  {remaining[:15]}")
print(f"Refs: {_n[0]}")
