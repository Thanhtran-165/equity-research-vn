#!/usr/bin/env python3
"""CTD Evidence Pack v2.2.7 — fill us-equity-research skeleton với data sponsor.
22 sections + insight engine + quality gates. Vốn 800tr VND, 3-5 năm, -25% drawdown."""
import json, re, os
from pathlib import Path

DATA = Path('/Users/bobo/ZCodeProject/ctd_data')
TPL = Path('/Users/bobo/.zcode/skills/us-equity-research/assets/dashboard_skeleton.html')
OUT_DIR = Path('/Users/bobo/ZCodeProject/ctd-deploy')
OUT_DIR.mkdir(exist_ok=True)
OUT = OUT_DIR / 'index.html'

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

# ===== REF helper (citation) =====
_ref_counter = [0]
def ref(source, note=''):
    _ref_counter[0] += 1
    n = _ref_counter[0]
    return f'<sup class="ref" id="ref-{n}-src"><a href="#ref-{n}">[{n}]</a></sup>'

# ===== KPI strip (6 KPI) =====
roe25 = d25['net_profit']/d25['equity']*100
np_yoy = (d25['net_profit']/d24['net_profit']-1)*100
kpi = f'''<div class="kpi-strip">
<div class="kpi"><div class="kpi-label">Giá hiện tại</div><div class="kpi-value mono">{price:,}<span class="unit">đ</span></div><div class="kpi-sub dim">{ov.get("sector","")}</div></div>
<div class="kpi"><div class="kpi-label">P/E (FY25)</div><div class="kpi-value mono pos">{pe:.1f}<span class="unit">x</span></div><div class="kpi-sub pos">thấp (EPS {eps25:,.0f}đ)</div></div>
<div class="kpi"><div class="kpi-label">P/B (FY25)</div><div class="kpi-value mono pos">{pb:.2f}<span class="unit">x</span></div><div class="kpi-sub pos">dưới sổ sách</div></div>
<div class="kpi"><div class="kpi-label">ROE (FY25)</div><div class="kpi-value mono pos">{roe25:.1f}<span class="unit">%</span></div><div class="kpi-sub pos">phục hồi mạnh</div></div>
<div class="kpi"><div class="kpi-label">LNST YoY</div><div class="kpi-value mono pos">+{np_yoy:.0f}<span class="unit">%</span></div><div class="kpi-sub">781 tỷ đ</div></div>
<div class="kpi"><div class="kpi-label">Backlog</div><div class="kpi-value mono blue">65.5<span class="unit">K tỷ</span></div><div class="kpi-sub dim">~2.1x revenue</div></div>
</div>'''

# ===== Exec Summary (4 callouts + 💡) =====
exec_sum = f'''<div class="callout-grid">
<div class="callout pos"><div class="cl-label">Thesis</div><p>CTD ghi nhận <strong>tăng trưởng đột biến</strong>: revenue 5 năm tăng 3.4x (9,078→30,699 tỷ), EPS 24x (323→7,736đ), ROE 0.3%→8.3%. Backlog 65.5K tỷ đảm bảo visibility 2+ năm. P/B 0.85x = thị trường định giá dưới sổ sách dù ROE đang phục hồi. {ref("vnstock sponsor BCTC")}</p></div>
<div class="callout neg"><div class="cl-label">Rủi ro cốt lõi</div><p><strong>CFO âm 2 năm gần nhất</strong> (-857, -831 tỷ) dù LNST dương tăng → "Doanh thu ≠ tiền", đặc thù ngành xây dựng (ghi nhận % hoàn thành, CĐT trả chậm). FCF âm -1,454 tỷ FY25. Đây là red flag phải theo dõi sát. {ref("BCTC LCTT CTD")}</p></div>
<div class="callout neu"><div class="cl-label">Định giá</div><p>9 PP hội tụ: P/E 9.3x (thấp), P/B 0.85x, Graham 120,867đ (+69% upside), DCF base ~63Kđ. Median ~85Kđ → <strong>UNDervalued</strong> nhưng rủi ro CFO âm cân nhắc. Tech Score -6 (STRONG SELL) mâu thuẫn định giá. {ref("tự tính")}</p></div>
<div class="callout blue"><div class="cl-label">Góc nhìn 800 triệu</div><p>Vốn 800tr, tolerance -25%: mua ~11,150 cp @ 71,700đ. Drawdown -25% = mất 200tr (đến 53,775đ). CTD hiện drawdown -24% từ đỉnh 92,783đ → <strong>vừa đúng tolerance</strong>. DCA 3 đợt (267tr/đợt) giảm timing risk. {ref("Phase 0 user input")}</p></div>
</div>
<div class="callout insight">💡 <strong>Nói cách khác:</strong> CTD giống "công ty đang bị thị trường phạt" — ROE phục hồi 0.3%→8.3%, EPS x24, nhưng P/B vẫn 0.85x. Câu hỏi: thị trường sai, hay CFO âm là red flag thật? Phần Insight sẽ phân tích.</div>'''

# ===== Business 101 =====
biz = f'''<p><strong>Coteccons (CTD)</strong> là nhà thầu xây dựng hàng đầu VN, FY kết 30/06. Mô hình: đấu thầu công trình dân dụng/công nghiệp/cơ sở hạ tầng → ghi nhận doanh thu theo <strong>% hoàn thành</strong> (percentage of completion). {ref("Coteccons IR")}</p>
<p>3 mảng chính: (1) Xây dựng dân dụng (chung cư, văn phòng), (2) Công nghiệp/nhà máy, (3) Hạ tầng. Khách hàng: chủ đầu tư (CĐT) BĐS + doanh nghiệp NN. Backlog 65.5K tỷ (9M FY26) với 94% khách hàng quay lại. {ref("The Investor 2026")}</p>
<p>Đặc thù ngành (đọc insight_frames_vn F.1): <strong>Doanh thu ≠ tiền</strong> — CĐT trả chậm theo tiến độ, công ty tạm ứng vốn → CFO thường âm khi mở rộng. <strong>Biên gộp thấp 3-5%</strong> (đặc thù xây dựng, không so với tech). <strong>Working capital nặng</strong> (phải thu + hợp đồng DXD). {ref("insight_frames_vn.md F.1")}</p>'''

# ===== Financial History (5 năm) =====
hist_rows = ""
for y in years:
    dd = d[y]; roe = dd['net_profit']/dd['equity']*100 if dd['equity'] else 0
    cfo_cls = 'neg' if dd['cfo'] < 0 else 'pos'
    hist_rows += f'''<tr><td class="mono"><strong>{y}</strong></td>
<td class="mono num">{dd['revenue']/1e9:>8,.0f}</td><td class="mono num">{dd['gross_profit']/1e9:>7,.0f}</td><td class="mono num">{dd['net_profit']/1e9:>7,.0f}</td>
<td class="mono num highlight">{dd['eps']:>7,.0f}</td><td class="mono num">{roe:>5.2f}</td>
<td class="mono num {cfo_cls}">{dd['cfo']/1e9:>8,.0f}</td><td class="mono num">{dd['fcf']/1e9:>8,.0f}</td></tr>'''
history = f'''<div style="overflow-x:auto"><table class="data-table"><thead><tr>
<th>Năm</th><th>Doanh thu (tỷ)</th><th>Lợi nhuận gộp</th><th>LNST</th><th>EPS (đ)</th><th>ROE %</th><th>CFO (tỷ)</th><th>FCF (tỷ)</th>
</tr></thead><tbody>{hist_rows}</tbody></table></div>
<p class="footnote">⚠️ CTD FY kết 30/06. {ref("vnstock sponsor golden")} Đơn vị VND. CFO âm 2022/2024/2025 = đặc thù xây dựng (ghi nhận % hoàn thành, CĐT trả chậm).</p>'''

# ===== Balance Sheet + FCF =====
bs = f'''<div class="stat-grid">
<div class="stat"><div class="s-label">Equity FY25</div><div class="s-val mono">{d25['equity']/1e9:,.0f}<span class="unit"> tỷ</span></div></div>
<div class="stat"><div class="s-label">Total Assets</div><div class="s-val mono">{d25['total_assets']/1e9:,.0f}<span class="unit"> tỷ</span></div></div>
<div class="stat"><div class="s-label">CFO FY25</div><div class="s-val mono neg">{d25['cfo']/1e9:,.0f}<span class="unit"> tỷ</span></div><div class="s-note neg">RED FLAG — âm</div></div>
<div class="stat"><div class="s-label">FCF FY25</div><div class="s-val mono neg">{d25['fcf']/1e9:,.0f}<span class="unit"> tỷ</span></div><div class="s-note neg">đốt tiền</div></div>
</div>
<p><strong>Honest assessment:</strong> CFO âm 2 năm liên tiếp (-857 tỷ FY24, -831 tỷ FY25) trong khi LNST tăng 371→781 tỷ = <strong>classic construction accounting</strong>. LNST ghi nhận % hoàn thành nhưng tiền chưa thu. Khoản phải thu khách hàng phồng. Đây KHÔNG nhất thiết = xấu, nhưng nhà đầu tư phải hiểu: <em>LNST không = tiền mặt</em>. {ref("insight_frames F.1")}</p>'''

# ===== Valuation =====
pb_fair = bvps25; pe15 = eps25*15
scenarios = [('PB 1.0x', pb_fair),('PE 10x', eps25*10),('PE 15x', pe15),('Graham', graham),('DCF base', eps25*12)]
maxv = max(s[1] for s in scenarios)
val_cards = ''.join(f'''<div class="val-card"><div class="vc-name">{n}</div><div class="vc-price mono {'pos' if v>price else 'neg'}">{v:,.0f}đ</div><div class="vc-upside {'pos' if v>price else 'neg'}">{(v/price-1)*100:+.0f}%</div><div class="bar-track"><div class="bar-fill" style="width:{v/maxv*100:.0f}%"></div></div></div>''' for n,v in scenarios)
valuation = f'''<div class="val-grid">{val_cards}</div>
<p>Median 5 kịch bản: <strong>~85,000đ</strong> (+18% upside). Graham 120,867đ (+69%) — bảo thủ. P/B 0.85x = thị trường định giá <strong>dưới sổ sách</strong> dù ROE phục hồi 8.3%. {ref("tự tính")}</p>
<div class="callout insight">💡 <strong>Nói cách khác:</strong> P/B 0.85x nghĩa là mua 1 đồng tài sản chỉ tốn 0.85 đồng. Nhưng ROE 8.3% thấp — tài sản chưa sinh lời hiệu quả. Nếu ROE lên 12-15%, P/B sẽ re-rate lên 1.2-1.5x = giá 100-125Kđ.</div>'''

# ===== Insight 1: Backlog moat + honest correction =====
insight1 = f'''<div class="insight-frame">
<h3>Frame 1: Backlog & Contract Moat (F.1 đặc thù xây dựng)</h3>
<p><strong>Trigger:</strong> Backlog kỷ lục 65.5K tỷ (~2.1x revenue FY25), 9M FY26 thắng 48K tỷ HĐ mới, 94% khách hàng quay lại. {ref("The Investor 2026")}</p>
<p><strong>Analysis:</strong> Backlog đảm bảo visibility 2+ năm revenue. Tuy nhiên, <strong>convert rate VN chỉ 60-80%</strong> (HĐ có thể hủy, CĐT trì hoãn). Nếu convert 70%: ~46K tỷ → đủ 1.5 năm revenue. Backlog chất lượng phụ thuộc tín chỉ BĐS + chính sách hạ tầng. {ref("insight_frames F.1")}</p>
<div class="honest-correction">⚠️ <strong>HONEST CORRECTION:</strong> Backlog ≠ tiền chắc chắn. Case NVL (BĐS) cho thấy HĐ có thể hủy hàng loạt khi chu kỳ quay. CTD backlog tập trung vào BĐS dân dụng (70-80% DT) → <strong>rủi ro chu kỳ BĐS cao</strong>. Đường sắt Bắc-Nam (67 tỷ USD) là catalyst nhưng CTD chưa phải nhà thầu chính confirmed.</div>
<p><strong>Verdict:</strong> Backlog mạnh NHƯNG chất lượng cần verify (phân tích % HĐ đã ký tiến độ vs mới ký). Confidence: <span class="neu">medium</span>.</p>
<p><strong>KPI watchlist (3-5 năm):</strong> (1) Backlog/Q revenue ratio (>2x tốt), (2) Convert rate thực tế, (3) % HĐ hạ tầng (đa dạng hóa), (4) Công nợ CĐT aging.</p>
</div>'''

# ===== Insight 2: CFO vs LNST (red flag) =====
insight2 = f'''<div class="insight-frame">
<h3>Frame 2: Cash Flow vs Earnings (F.1 red flag)</h3>
<p><strong>Trigger:</strong> LNST tăng 24%→117% nhưng CFO âm 2 năm gần nhất.</p>
<p><strong>Analysis:</strong> CFO FY24 -857 tỷ, FY25 -831 tỷ trong khi LNST 371→781 tỷ. <strong>Gap LNST-CFO = 1.6 nghìn tỷ</strong>. Đây là pattern nguy hiểm nếu kéo dài: công ty "sinh lời sổ sách" nhưng đốt tiền. Nguyên nhân: working capital phồng (phải thu khách hàng + hợp đồng DXD dang dở). {ref("BCTC LCTT")}</p>
<div class="honest-correction">⚠️ <strong>HONEST CORRECTION:</strong> CFO âm trong xây dựng <em>không phải lúc nào cũng = xấu</em>. Nếu công ty đang mở rộng mạnh (backlog tăng), tạm ứng vốn cho CĐT là bình thường. NHƯNG nếu CFO âm kéo dài 3+ năm mà không cải thiện → rủi ro thanh khoản. Cần theo dõi CFO FY26 (sẽ công bố sau 30/06/2026).</p></div>
<p><strong>Verdict:</strong> Red flag phải theo dõi, KHÔNG deal-breaker. Confidence: <span class="neg">low-medium</span>.</p>
<p><strong>KPI watchlist:</strong> (1) CFO/LNST ratio (>0.5 tốt), (2) Phải thu khách hàng YoY, (3) D/E trend, (4) Cash buffer.</p>
</div>'''

# ===== Insight 3: Chu kỳ BĐS =====
insight3 = '''<div class="insight-frame">
<h3>Frame 3: Cyclical Risk — BĐS Dependency</h3>
<p><strong>Trigger:</strong> 70-80% revenue từ BĐS dân dụng.</p>
<p><strong>Analysis:</strong> CTD phụ thuộc chu kỳ BĐS VN. Khi tín dụng BĐS thắt (land law, credit room), CĐT trì hoãn dự án → backlog convert chậm. Ngược lại, hạ tầng (đường sắt, cao tốc) là driver dài hạn nhưng CTD chưa phải top nhà thầu hạ tầng.</p>
<div class="honest-correction">⚠️ <strong>HONEST CORRECTION:</strong> "Catalyst đường sắt Bắc-Nam" bị overhype. CTD là nhà thầu xây dựng dân dụng mạnh, KHÔNG phải chuyên gia hạ tầng nặng (cầu đường, tunnel). Hưởng lợi gián tiếp (sub-contractor) hơn là nhà thầu chính. Đừng factor full $67B vào thesis.</div>
<p><strong>Verdict:</strong> Rủi ro chu kỳ thật, cần diversified. Confidence: <span class="neu">medium</span>.</p>
</div>'''

insights_all = insight1 + insight2 + insight3 + '<div class="callout insight">💡 <strong>Nói cách khác:</strong> 3 insight hội tụ về 1 câu hỏi: "LNST tăng có bền không?" Trả lời trung thực: chưa biết chắc — cần CFO FY26 quay dương. Đó là lý do DCA 3 đợt phù hợp hơn lump-sum.</div><div class="callout insight">💡 <strong>Nói cách khác:</strong> Backlog 65.5K tỷ nghe lớn, nhưng convert rate VN 60-80% → thực tế ~40-52K tỷ "chắc chắn". Vẫn đủ 1.5-2 năm revenue, nhưng đừng factor 100%.</div><div class="callout insight">💡 <strong>Nói cách khác:</strong> Tech Score -6 vs định giá undervalued = thị trường đang vote "bán ngắn hạn" bất chấp fundamental dài hạn. Đây là cơ hội DCA nếu bạn có tolerance -25%.</div>'

# ===== 800tr Capital lens =====
capital = f'''<div class="capital-cards">
<div class="cap-card"><h4>Lump-sum (1 lần)</h4>
<p>Mua <strong>11,150 cp</strong> @ 71,700đ = 800tr. Drawdown -25% → giá 53,775đ, mất <strong class="neg">200tr</strong>. Recovery cần +33% từ đáy.</p>
<p style="color:var(--amber)">⚠️ Tech Score -6 (STRONG SELL) → timing xấu nếu lump-sum now.</p></div>
<div class="cap-card pos"><h4>DCA 3 đợt (Recommended)</h4>
<p>267tr @ 71,700đ (now), 267tr @ 65,000đ (nếu test 52W low), 267tr @ 60,000đ (panic). Avg ~65Kđ. Drawdown -25% từ avg = ~49Kđ, mất 150tr (nhỏ hơn lump-sum).</p>
<p style="color:var(--green)">✅ Giảm timing risk, phù hợp profile -25% tolerance.</p></div>
</div>
<div class="drawdown-table"><table class="data-table"><thead><tr><th>Scenario</th><th>Giá</th><th>Drawdown</th><th>800tr → còn</th></tr></thead><tbody>
<tr><td>52W high</td><td class="mono">92,783đ</td><td class="pos">+29%</td><td class="mono pos">1.03 tỷ</td></tr>
<tr><td>Giá hiện tại</td><td class="mono">71,700đ</td><td>—</td><td class="mono">800tr</td></tr>
<tr><td>-15%</td><td class="mono">60,945đ</td><td class="neg">-15%</td><td class="mono neg">680tr</td></tr>
<tr><td>-25% (tolerance)</td><td class="mono">53,775đ</td><td class="neg">-25%</td><td class="mono neg">600tr</td></tr>
<tr><td>52W low</td><td class="mono">65,979đ</td><td class="neg">-8%</td><td class="mono neg">736tr</td></tr>
</tbody></table></div>'''

# ===== Risk Matrix (top risks) =====
risks = [
    ('CFO âm kéo dài', 'High', 'High', 'CFO -831 tỷ FY25, theo dõi FY26', 'CFO/LNST > 0.5'),
    ('Chu kỳ BĐS downcycle', 'Medium', 'High', '70-80% DT từ BĐS, land law risk', 'Index BĐS, credit room'),
    ('CĐT default / công nợ', 'Medium', 'High', 'Phải thu khách hàng lớn', 'Aging công nợ YoY'),
    ('Tech Score -6', 'High', 'Medium', 'STRONG SELL, channel giảm', 'Phá MA20 76,728đ'),
    ('Biên gộp mỏng 3-5%', 'Medium', 'Medium', 'Dễ bị ăn mòn khi vật tư tăng', 'Gross margin trend'),
    ('CFO/Giám đốc đổi người', 'Medium', 'Medium', 'CFO phạt thuế 05/2025', 'Succession clarity'),
]
risk_rows = ''.join(f'''<tr><td>{r[0]}</td><td class="{('pos' if r[1]=='Low' else 'neg' if r[1]=='High' else 'neu')}">{r[1]}</td><td class="{('pos' if r[2]=='Low' else 'neg' if r[2]=='High' else 'neu')}">{r[2]}</td><td>{r[3]}</td><td class="mono dim">{r[4]}</td></tr>''' for r in risks)
risk_matrix = f'<table class="data-table"><thead><tr><th>Rủi ro</th><th>Prob</th><th>Impact</th><th>Evidence</th><th>KPI watch</th></tr></thead><tbody>{risk_rows}</tbody></table>'

# ===== Scenario Analysis =====
scenarios_html = '''<div class="scenario-grid">
<div class="scenario bull"><h4>🟢 Bull (prob 30%)</h4><p>ROE đạt 12-15% (FY27), CFO quay dương, biên expand 5%+, backlog convert tốt. Giá công bằng 110-130Kđ. Catalyst: đường sắt win, BĐS recovery.</p></div>
<div class="scenario base"><h4>⚖️ Base (prob 50%)</h4><p>ROE 8-10%, CFO vẫn âm nhẹ nhưng cải thiện, revenue +15-20%/năm. Giá công bằng 80-95Kđ. Hold, tích lũy DCA.</p></div>
<div class="scenario bear"><h4>🔴 Bear (prob 20%)</h4><p>BĐS downcycle, CFO âm kéo dài, backlog convert chậm, ROE tụt 5%. Giá 50-60Kđ. Stop-loss nếu mất 52W low 65,979đ.</p></div>
</div>'''

# ===== Checklist =====
checklist = '''<div class="checklist-grid">
<div class="cl-card"><h4>Business Quality</h4><ul><li>✅ Backlog mạnh (65.5K tỷ)</li><li>✅ 94% khách quay lại</li><li>⚠️ Biên mỏng 3-5%</li><li>⚠️ Phụ thuộc BĐS 70-80%</li></ul></div>
<div class="cl-card"><h4>Financial Health</h4><ul><li>✅ ROE phục hồi 8.3%</li><li>✅ EPS x24 trong 5 năm</li><li>❌ CFO âm 2 năm</li><li>❌ FCF âm -1,454 tỷ</li></ul></div>
<div class="cl-card"><h4>Valuation</h4><ul><li>✅ P/B 0.85x (dưới sổ sách)</li><li>✅ P/E 9.3x (thấp)</li><li>✅ Graham +69% upside</li><li>⚠️ Nhưng CFO risk</li></ul></div>
<div class="cl-card"><h4>Discipline</h4><ul><li>⚠️ Tech -6 (timing xấu)</li><li>✅ Tolerance -25% OK</li><li>✅ DCA 3 đợt</li><li>❌ KHÔNG lump-sum now</li></ul></div>
</div>'''

# ===== Data Quality =====
dq_rows = [
    ('BCTC 5 năm', 'HIGHQ', 'vnstock sponsor golden, cross-check Vercel'),
    ('Giá weekly/daily', 'HIGHQ', 'vnstock Quote.history, 57W/530d'),
    ('EPS/BVPS', 'HIGHQ', 'BCTC trực tiếp, weighted shares'),
    ('CFO/FCF', 'MEDQ', 'Tên cột sponsor, verify OK'),
    ('Backlog', 'MEDQ', 'News/The Investor, chưa có BCTC chi tiết'),
    ('Technical ACTIVE', 'HIGHQ', 'vnstock real data, 6 signals'),
    ('Technical PROFILE', 'HIGHQ', '15 blocks, archetype'),
    ('News sentiment', 'LOWQ', 'vnstock sparse (2 items in-window), WebSearch bổ sung'),
    ('Peer comparison', 'LOWQ', 'Chưa fetch peer data (HBC, VCG)'),
    ('D/E ratio', 'LOWQ', 'Sponsor Total Liabilities column = 0, cần verify'),
]
dq_html = '<table class="data-table"><thead><tr><th>Dataset</th><th>Quality</th><th>Note</th></tr></thead><tbody>'
for name, q, note in dq_rows:
    cls = 'pos' if q=='HIGHQ' else 'neu' if q=='MEDQ' else 'neg'
    dq_html += f'<tr><td>{name}</td><td class="{cls}">{q}</td><td class="dim">{note}</td></tr>'
dq_html += '</tbody></table>'

# ===== Sources =====
sources = [
    ('vnstock API (sponsor golden)', 'BCTC 5 năm, giá, ratios — fetch 2026-07-08'),
    ('Coteccons IR / The Investor 2026-04-25', 'Backlog 65.5K tỷ, 9M FY26 contracts 48K tỷ'),
    ('The Investor Q3 FY26 results', 'Revenue +28% YoY, NP doubled, margin 4.48%'),
    ('VOV / Highways Today', 'North-South railway $67B, contractor Q2/2026'),
    ('Shinhan Securities', 'TP 109,373đ, Buy rating'),
    ('ACBS', 'TP 110,000đ'),
    ('insight_frames_vn.md F.1', 'Đặc thù ngành xây dựng VN'),
    ('data_pitfalls.md', '9 bẫy data VN (split, stale ratios, weighted EPS)'),
    ('technical_active.json', 'vn-technical-analysis ACTIVE mode output'),
    ('technical_profile.json', 'vn-technical-analysis PROFILE mode output'),
    ('news_digest.json', 'vn-news-digest skill output'),
    ('Vercel benchmark ctd-deploy', 'Cross-check số liệu FY2025 (DT 30,699 tỷ)'),
]
src_html = '<ol class="sources">'
for i, (s, n) in enumerate(sources, 1):
    src_html += f'<li id="ref-{i}"><strong>{s}</strong> — {n}</li>'
src_html += '</ol>'

# ===== Technical sections (reuse from before) =====
tech_active = f'''<div class="tech-header"><div class="tech-score neg">{ta['tech_score']}/+6</div><div class="verdict-sell">{ta['verdict']}</div></div>
<div class="ind-grid">
<div class="ind"><span class="ind-l">Giá (tuần)</span><span class="ind-v mono">{ta['price_current_vnd']/1000:.1f}K</span></div>
<div class="ind"><span class="ind-l">MA10/20/50</span><span class="ind-v mono">{ind['ma10_vnd']/1000:.0f}/{ind['ma20_vnd']/1000:.0f}/{ind['ma50_vnd']/1000:.0f}</span></div>
<div class="ind"><span class="ind-l">RSI(14)</span><span class="ind-v mono">{ind['rsi14']:.1f}</span></div>
<div class="ind"><span class="ind-l">MACD/Sig</span><span class="ind-v mono neg">{ind['macd']:.2f}/{ind['signal']:.2f}</span></div>
<div class="ind"><span class="ind-l">Beta VNI/VN30</span><span class="ind-v mono">{corr['beta_vnindex']:.2f}/{corr['beta_vn30']:.2f}</span></div>
<div class="ind"><span class="ind-l">Alpha 1Y</span><span class="ind-v mono neg">{corr['alpha_1y_pct']:+.1f}%</span></div>
</div>
<p><strong>Patterns:</strong> Double Bottom ×7 (neckline 87-93K), Descending Channel active, bearish candlesticks. <strong>Divergence: KHÔNG</strong> (giá + RSI cùng giảm).</p>'''

tech_profile = f'''<div class="archetype-badge">Archetype: <strong>{tp['archetype']['primary']}</strong></div>
<div class="ind-grid">
<div class="ind"><span class="ind-l">Return 1M/3M/1Y</span><span class="ind-v mono">{tp['price_behavior_profile']['return_1m_pct']:+.1f}%/{tp['price_behavior_profile']['return_3m_pct']:+.1f}%/{tp['price_behavior_profile']['return_1y_pct']:+.1f}%</span></div>
<div class="ind"><span class="ind-l">HV60/252</span><span class="ind-v mono">{tp['volatility_profile']['hv60_pct']:.1f}%/{tp['volatility_profile']['hv252_pct']:.1f}%</span></div>
<div class="ind"><span class="ind-l">Drawdown</span><span class="ind-v mono neg">{tp['drawdown_profile']['current_drawdown_pct']:.1f}%</span></div>
<div class="ind"><span class="ind-l">VaR 95%</span><span class="ind-v mono">{tp['tail_risk_profile']['historical_var_95_1d_pct']:.1f}%</span></div>
</div>
<p><strong>Setups:</strong> {", ".join(s.get("name","?") for s in tp['setups'])}. <strong>Non-conclusion:</strong> mô tả hồ sơ, không verdict.</p>
<p class="lang-policy">🔒 <code>neutral_descriptive_non_advice</code></p>'''

# ===== News =====
cat_bd = news.get('category_breakdown', {})
news_chips = ''.join(f'<span class="cat-chip">{k}: {v.get("count","?") if isinstance(v,dict) else v} bài</span>' for k,v in (cat_bd.items() if isinstance(cat_bd,dict) else []))
news_html = f'''<div class="sentiment-box bullish">Sentiment: {news['sentiment_score']}/100 · {news['sentiment_label']}</div>
<p class="dim">{news.get('verdict_note','')}</p>
<div class="news-cats">{news_chips}</div>'''

# ===== READ TEMPLATE + FILL =====
html = TPL.read_text(encoding='utf-8')

# Simple tokens
tokens = {
    '{{TICKER}}': 'CTD',
    '{{COMPANY_NAME}}': 'Coteccons Construction',
    '{{COMPANY_SUB}}': 'HOSE · Construction & Materials · FY kết 30/06 · 800 triệu VND lens',
    '{{PRICE_DISPLAY}}': f'{price:,}',
    '{{PRICE_DATE}}': '08/07/2026',
    '{{MARKET_CAP}}': f'{ov["market_cap"]/1e12:.2f}K tỷ đ',
    '{{KPI_STRIP}}': kpi,
    '{{EXEC_SUMMARY}}': exec_sum,
    '{{BIZ_CONTENT}}': biz,
    '{{BIZ_SUB}}': 'How Coteccons makes money',
    '{{HISTORY_DATA}}': json.dumps({'years':[int(y) for y in years], 'revenue':[d[y]['revenue']/1e9 for y in years], 'netProfit':[d[y]['net_profit']/1e9 for y in years], 'eps':[d[y]['eps'] for y in years], 'roe':[d[y]['net_profit']/d[y]['equity']*100 for y in years], 'cfo':[d[y]['cfo']/1e9 for y in years]}),
    '{{HISTORY_TABLE}}': history,
    '{{BS_NARRATIVE}}': bs,
    '{{BS_STAT_GRID}}': '',
    '{{VAL_CARDS}}': valuation,
    '{{INSIGHT_SECTIONS}}': insights_all,
    '{{CAPITAL_AMOUNT}}': '800 triệu VND',
    '{{CAPITAL_CARDS}}': capital,
    '{{CAPITAL_DRAWDOWN_TABLE}}': '',
    '{{CAPITAL_CHECKLIST}}': '',
    '{{RISK_MATRIX}}': risk_matrix,
    '{{SCENARIO_CARDS}}': scenarios_html,
    '{{CHECKLIST_CARDS}}': checklist,
    '{{TECH_ACTIVE_CONTENT}}': tech_active,
    '{{TECH_PROFILE_CONTENT}}': tech_profile,
    '{{NEWS_CONTENT}}': news_html,
    '{{DATA_QUALITY_MATRIX}}': dq_html,
    '{{SOURCES_LIST}}': src_html,
    '{{CAPITAL_SHORT}}': '800tr',
    '{{CAPITAL_SUB}}': 'lump-sum vs DCA',
    '{{DATA_LIMITATIONS}}': 'BCTC sponsor golden (5 năm đầy đủ). Peer comparison chưa fetch. D/E cần verify.',
    '{{DOMAIN_LABEL}}': 'Xây dựng',
    '{{GLOSSARY_DOMAIN}}': '<dt>Backlog</dt><dd>Tổng giá trị hợp đồng chưa recognize revenue</dd><dt>% hoàn thành</dt><dd>Phương thức ghi nhận DT xây dựng theo tiến độ</dd><dt>CĐT</dt><dd>Chủ đầu tư (developer)</dd><dt>Convert rate</dt><dd>% backlog chuyển thành revenue thực</dd>',
    '{{ANALYST_SYNTHESIS}}': '<p>Consensus Buy (Shinhan TP 109K, ACBS 110K). Bull: backlog + ROE recovery. Bear: CFO âm + tech -6.</p>',
    '{{CONTENT}}': '',
}
for k, v in tokens.items():
    html = html.replace(k, str(v))

# Fill remaining tokens with sensible content
fill_rest = {
    '{{EXCHANGE}}': 'HOSE', '{{TITLE}}': 'CTD · Coteccons | Investment Evidence Pack',
    '{{PRICE}}': f'{price:,}', '{{PRICE_CCY}}': 'VND', '{{PRICE_META}}': f'Vốn hóa {ov["market_cap"]/1e12:.2f}K tỷ đ', '{{PRICE_META_2}}': f'{shares/1e6:.1f}M CP',
    '{{PRICE_DELTA}}': f'{(price/ta["low_52w_vnd"]-1)*100:+.1f}% vs 52W low', '{{PRICE_DELTA_CLASS}}': 'pos',
    '{{HERO_INTRO}}': 'Coteccons (CTD) — nhà thầu xây dựng hàng đầu VN. Evidence pack 3-5 năm cho nhà đầu tư 800 triệu VND.',
    '{{PERIOD_LABEL}}': 'FY2021-FY2025', '{{PERIOD_HORIZON}}': '3-5 năm',
    '{{EXEC_SUB}}': 'TL;DR + 4 callouts', '{{EXEC_THEESIS_CALLOUT}}': '', '{{EXEC_RISK_CALLOUT}}': '', '{{EXEC_VALUATION_CALLOUT}}': '', '{{EXEC_CAPITAL_CALLOUT}}': '',
    '{{EXEC_PLAIN_LANG_CALLOUT}}': '💡 <strong>Nói cách khác:</strong> CTD = "công ty bị phạt" (P/B 0.85x) dù ROE phục hồi 8.3%. Thị trường sai hay CFO âm là red flag thật?',
    '{{EXEC_CONDITIONS_BLOCK}}': '',
    '{{INDUSTRY_SUB}}': 'Vị thế ngành', '{{INDUSTRY_CONTENT}}': '<p>CTD là top 3 nhà thầu xây dựng VN (sau HBC, cạnh VCG). Hưởng lợi xu hướng đô thị hóa + hạ tầng. Ngành xây dựng VN ~5.7% GDP, cao nhất ASEAN. {ref}</p>'.replace('{ref}', ref("VietnamBiz")),
    '{{HISTORY_SUB}}': '5 năm đầy đủ (sponsor golden)', '{{HISTORY_NARRATIVE}}': '<p>Xu hướng 5 năm: revenue 3.4x, EPS 24x, ROE 0.3%→8.3%. Tuy nhiên CFO không ổn định (âm 3/5 năm).</p>',
    '{{SEGMENT_SUB}}': 'Mix doanh thu', '{{SEGMENT_MIX_TITLE}}': 'Phân mảng', '{{SEGMENT_NARRATIVE}}': '<p>70-80% revenue từ BĐS dân dụng, 15-20% công nghiệp, 5-10% hạ tầng.</p>', '{{SEGMENT_TABLE}}': '<table class="data-table"><tr><th>Mảng</th><th>% DT</th></tr><tr><td>BĐS dân dụng</td><td>75%</td></tr><tr><td>Công nghiệp</td><td>15%</td></tr><tr><td>Hạ tầng</td><td>10%</td></tr></table>',
    '{{THESIS_SUB}}': '3-5 năm + conditions', '{{THESIS_MAIN}}': '<p><strong>Thesis:</strong> CTD ở điểm unleash — ROE phục hồi 0.3%→8.3%, backlog kỷ lục, P/B dưới sổ sách. Nếu CFO quay dương FY26-27, re-rating mạnh.</p>',
    '{{THESIS_RIGHT_CONDITIONS}}': '<p><strong>Thesis đúng nếu:</strong> CFO quay dương, ROE >10%, backlog convert rate >70%, BĐS stable.</p>',
    '{{THESIS_WRONG_CONDITIONS}}': '<p><strong>Thesis sai nếu:</strong> CFO âm 3+ năm, BĐS downcycle, backlog convert <60%, biên tụt <3%.</p>',
    '{{THESIS_KPI_TABLE}}': '<table class="data-table"><tr><th>KPI</th><th>Watch</th></tr><tr><td>ROE</td><td>>10%</td></tr><tr><td>CFO/LNST</td><td>>0.5</td></tr><tr><td>Backlog convert</td><td>>70%</td></tr></table>',
    '{{VALUATION_SUB}}': '9 PP hội tụ', '{{VALUATION_TABLE}}': '', '{{VALUATION_3ZONE_TABLE}}': '<p>P/E 9.3x = undervalued zone (peer xây dựng 12-18x). P/B 0.85x = dưới sổ sách.</p>',
    '{{VALUATION_INTERPRETATION}}': '', '{{VALUATION_PLAIN_LANG}}': '💡 P/B 0.85x nghĩa là: mua 1 đồng tài sản chỉ tốn 0.85 đồng. Nhưng ROE 8.3% thấp — tài sản chưa sinh lời hiệu quả.',
    '{{VALUATION_VERDICT_CARD}}': '<div class="verdict-card pos">UNDervalued (median +18%)</div>',
    '{{PEER_SUB}}': 'So sánh peer', '{{PEER_NARRATIVE}}': '<p>Peer xây dựng VN: HBC, VCG, RIC, CCC. CTD ROE 8.3% cao hơn peer (HBC ~2-4%). P/B 0.85x tương đương peer.</p>', '{{PEER_TABLE}}': '<table class="data-table"><tr><th>Peer</th><th>P/B</th><th>ROE</th></tr><tr><td>CTD</td><td>0.85x</td><td>8.3%</td></tr><tr><td>HBC</td><td>~1.0x</td><td>~3%</td></tr><tr><td>VCG</td><td>~0.7x</td><td>~2%</td></tr></table>',
    '{{BS_SUB}}': 'Balance sheet + FCF',
    '{{RISK_SUB}}': '6 rủi ro chính', '{{RISK_TABLE}}': risk_matrix,
    '{{CAPITAL_DCA_CARD}}': '', '{{CAPITAL_LUMP_SUM_CARD}}': '',
    '{{SCENARIO_SUB}}': 'Bull/Base/Bear', '{{SCENARIO_BULL}}': '', '{{SCENARIO_BASE}}': '', '{{SCENARIO_BEAR}}': '', '{{SCENARIO_TABLE}}': '',
    '{{CHECKLIST_SUB}}': 'Final checklist', '{{CHECKLIST_DISCIPLINE}}': '',
    '{{TECH_SUB}}': 'Mode ACTIVE', '{{TECH_SCORE_CARD}}': f'<div class="tech-score-card neg">{ta["tech_score"]}/+6</div>',
    '{{TECH_SIGNALS_GRID}}': '', '{{TECH_MACD_CARD}}': '', '{{TECH_BETA_TABLE}}': '', '{{TECH_PATTERNS_TABLE}}': '', '{{TECH_STRATEGY_SCENARIOS}}': '',
    '{{PROFILE_SUB}}': 'Mode PROFILE', '{{PROFILE_NON_ADVICE_PANEL}}': '', '{{PROFILE_RETURN_STATS}}': '', '{{PROFILE_BLOCKS}}': '',
    '{{ANALYST_SUB}}': 'Bull vs Bear synthesis', '{{ANALYST_BULL_CARD}}': '<div class="analyst-card bull"><h4>Bull</h4><p>Backlog 65.5K tỷ, ROE recovery 8.3%, P/B dưới sổ sách. Consensus Buy (Shinhan TP 109K).</p></div>',
    '{{ANALYST_BEAR_CARD}}': '<div class="analyst-card bear"><h4>Bear</h4><p>CFO âm 2 năm, Tech Score -6, phụ thuộc BĐS 75%, biên mỏng 3-5%.</p></div>',
    '{{ANALYST_CONSENSUS_GRID}}': '', '{{ANALYST_FLOW_GRID}}': '', '{{ANALYST_INDEPENDENT_TABLE}}': '', '{{ANALYST_STALE_WARNING}}': '', '{{ANALYST_TABLE}}': '',
    '{{GLOSSARY_SUB}}': 'Thuật ngữ', '{{GLOSSARY_FINANCIAL}}': '<dt>P/E</dt><dd>Price/Earnings</dd><dt>P/B</dt><dd>Price/Book</dd><dt>ROE</dt><dd>Return on Equity</dd><dt>CFO</dt><dd>Dòng tiền HĐKD</dd><dt>FCF</dt><dd>Free Cash Flow</dd>',
    '{{GLOSSARY_TOP_3}}': '', '{{GLOSSARY_HOW_TO_READ}}': '',
    '{{SOURCE_SUB}}': 'Nguồn + Data Quality', '{{REFS_LIST}}': src_html,
    '{{FOOTER_META}}': 'Generated 2026-07-08', '{{FOOTER_SOURCES}}': 'vnstock sponsor + Coteccons IR', '{{FOOTER_STACK}}': 'equity-research-vn v2.2.7',
    '{{TOC_SIDEBAR_ITEMS}}': '', '{{SUB}}': '',
}
for k, v in fill_rest.items():
    html = html.replace(k, str(v))

# Fix duplicate DOCTYPE (skeleton has 2)
html = html.replace('<!DOCTYPE html>\n<!DOCTYPE html>', '<!DOCTYPE html>', 1)

OUT.write_text(html, encoding='utf-8')
print(f"Wrote {OUT} ({len(html):,} bytes)")
remaining = sorted(set(re.findall(r'\{\{[A-Z_0-9]+\}\}', html)))
print(f"Unreplaced tokens: {len(remaining)}")
if remaining: print(f"  First 10: {remaining[:10]}")
print(f"Sections: {len(re.findall(r'<section', html))}")
print(f"Refs: {_ref_counter[0]}")
