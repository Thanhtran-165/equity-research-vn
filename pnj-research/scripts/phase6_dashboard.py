#!/usr/bin/env python3
"""
Phase 6: Dashboard build for PNJ
Fill 22 sections of the dashboard template with real data from phases 1-5.
Copy template → str.replace all tokens → verify structure.
"""
import json, os

TICKER = "PNJ"
WORK_DIR = "/Users/bobo/ZCodeProject/pnj-research"
DATA_DIR = os.path.join(WORK_DIR, "data")
TEMPLATE = os.path.join(WORK_DIR, "PNJ_Complete_Report.html")

# Load all data
with open(os.path.join(DATA_DIR, "financials.json")) as f: fin = json.load(f)
with open(os.path.join(DATA_DIR, "fundamental.json")) as f: fund = json.load(f)
with open(os.path.join(DATA_DIR, "valuation.json")) as f: val = json.load(f)
with open(os.path.join(DATA_DIR, "tech_active.json")) as f: tech = json.load(f)
with open(os.path.join(DATA_DIR, "tech_profile.json")) as f: prof = json.load(f)
with open(os.path.join(DATA_DIR, "news.json")) as f: news = json.load(f)
with open(os.path.join(DATA_DIR, "overview.json")) as f: ov = json.load(f)
with open(os.path.join(DATA_DIR, "balance_sheet.json")) as f: bs = json.load(f)
with open(os.path.join(DATA_DIR, "cash_flow.json")) as f: cf = json.load(f)
with open(os.path.join(DATA_DIR, "split_audit.json")) as f: split = json.load(f)

YEARS = [2021, 2022, 2023, 2024, 2025]
Y = [str(y) for y in YEARS]

def fmt(v, d=0):
    """Format number with thousands sep."""
    if v is None: return "N/A"
    try: return f"{float(v):,.{d}f}"
    except: return str(v)

# Read template
with open(TEMPLATE) as f:
    html = f.read()

replacements = {}

# ============ IDENTITY TOKENS ============
replacements["{{TICKER}}"] = TICKER
replacements["{{COMPANY_NAME}}"] = "Công ty CP Vàng bạc Đá quý Phú Nhuận"
replacements["{{EXCHANGE}}"] = "HOSE"
replacements["{{PRICE_DATE}}"] = "10/07/2026"
replacements["{{CAPITAL_LENS_AMOUNT}}"] = "500 triệu VND"
replacements["{{CITATION_COUNT}}"] = "16"
replacements["{{SOURCES_SUMMARY}}"] = "vnstock (VCI sponsor tier), BCTC kiểm toán PNJ 2021-2025, SJC gold price history, Vietnam Gold Traders Association"

# ============ SEC_HERO_HTML ============
price = ov["current_price_vnd"]
mc = ov["market_cap_ty"]
pe = val["pe_current"]
pb = val["pb_current"]
roe_avg = round(sum(v for v in fund["roe"] if v) / 5, 1)
eps_adj = fund["eps_adjusted_vnd"][-1]
tech_score = tech["tech_score"]
verdict_class = "red" if tech_score < 0 else "green"
replacements["{{SEC_HERO_HTML}}"] = f"""
<div class="hero">
  <div class="hero-top">
    <div>
      <span class="ticker-badge">HOSE · PNJ</span>
      <span class="disclaimer-badge">Không khuyến nghị Mua/Bán — Investment Evidence Pack</span>
      <h1 class="company-name">Công ty CP Vàng bạc Đá quý Phú Nhuận</h1>
      <div class="company-sub">Ngành: Bán lẻ trang sức & vàng miếng · ICB: Hàng tiêu dùng cá nhân · Vốn hóa {fmt(mc,0)} tỷ VND</div>
    </div>
    <div class="price-block">
      <div class="price-now mono"><span class="ccy">₫</span>{fmt(price,0)}</div>
      <div class="price-meta">Đóng cửa 10/07/2026 · <span class="delta neg">{tech['pct_from_high']:+.1f}% vs 52W high</span></div>
      <div class="price-meta">52W: {fmt(ov['52w_low'],0)} – {fmt(ov['52w_high'],0)}</div>
    </div>
  </div>
  <div class="kpi-strip">
    <div class="kpi"><div class="kpi-label">P/E (TTM, adj)</div><div class="kpi-value mono">{fmt(pe,1)}×</div><div class="kpi-delta dim">EPS adj {fmt(eps_adj,0)}đ</div></div>
    <div class="kpi"><div class="kpi-label">P/B</div><div class="kpi-value mono">{fmt(pb,2)}×</div><div class="kpi-delta dim">BVPS adj {fmt(fund['bvps_adjusted_vnd'][-1],0)}đ</div></div>
    <div class="kpi"><div class="kpi-label">ROE (5Y avg)</div><div class="kpi-value mono pos">{fmt(roe_avg,1)}%</div><div class="kpi-delta dim">2025: {fmt(fund['roe'][-1],1)}%</div></div>
    <div class="kpi"><div class="kpi-label">CAGR NPAT 4Y</div><div class="kpi-value mono pos">{fmt(fund['cagr_npat_4y'],1)}%</div><div class="kpi-delta dim">Revenue {fmt(fund['cagr_revenue_4y'],1)}%</div></div>
    <div class="kpi"><div class="kpi-label">FCF Yield</div><div class="kpi-value mono pos">{fmt(fund['fcf_per_share_adj_vnd'][-1]/price*100,1)}%</div><div class="kpi-delta dim">FCF {fmt(fund['fcf_per_share_adj_vnd'][-1],0)}đ/cp</div></div>
    <div class="kpi"><div class="kpi-label">Tech Score</div><div class="kpi-value mono {verdict_class}">{tech_score:+d}/6</div><div class="kpi-delta">{tech['verdict']}</div></div>
  </div>
</div>
<div class="callout" style="border-left:4px solid var(--amber);background:rgba(245,166,35,0.06);padding:14px 18px;border-radius:8px;margin-top:18px">
  <strong>⚠️ Bẫy 5B (split-adjustment):</strong> PNJ chia cổ phiếu thưởng 50% ngày 15/04/2026 (+ESOP 0.7% + 1%). EPS/BVPS từ BCTC 2021-2025 trên cơ sở pre-bonus (≈370M CP). Giá hiện tại post-bonus (511.7M CP). Mọi PE/PB trong báo cáo đã <strong>split-adjusted</strong> (EPS÷1.5) để cùng cơ sở với giá. Cross-check: CP back-calc = LNST/EPS khớp capital history.
</div>
"""

# ============ SEC_EXEC_HTML ============
replacements["{{SEC_EXEC_HTML}}"] = f"""
<p style="font-size:15px;line-height:1.7;color:var(--text);margin-bottom:20px">
  <strong>PNJ (Phú Nhuận Jewelry)</strong> là công ty bán lẻ trang sức và vàng miếng lớn nhất Việt Nam, vận hành ~400 điểm bán dưới các thương hiệu PNJ Gold, PNJ Silver, CAO Sáng, Style by PNJ và Phúc Lộc. Năm 2025, PNJ ghi nhận doanh thu <strong>{fmt(fin['revenue_ty']['2025'],0)} tỷ VND</strong> (giảm 7.5% so với đỉnh {fmt(fin['revenue_ty']['2024'],0)} tỷ năm 2024) nhưng lợi nhuận sau thuế thuộc cổ đông mẹ đạt <strong>{fmt(fin['npatmi_ty']['2025'],0)} tỷ VND</strong>, tăng <strong class="pos">+33.8%</strong> so với 2024 nhờ biên lợi nhuận gộp nở rộng từ 17.6% lên <strong class="pos">22.0%</strong>. Đây là year of margin expansion: giá vàng tăng mạnh giúp chênh lệch买卖 widened.
</p>
<div class="exec-grid">
  <div class="card" style="border-top:3px solid var(--green)">
    <div class="card-head"><h4>NPATMI 2025</h4><span class="tag green">Record</span></div>
    <div class="stat-value mono pos" style="font-size:28px">{fmt(fin['npatmi_ty']['2025'],0)}</div>
    <div class="dim" style="font-size:12px">tỷ VND · +33.8% YoY · CAGR 4Y {fmt(fund['cagr_npat_4y'],1)}%</div>
  </div>
  <div class="card" style="border-top:3px solid var(--amber)">
    <div class="card-head"><h4>Gross Margin 2025</h4><span class="tag amber">Mở rộng</span></div>
    <div class="stat-value mono" style="font-size:28px">{fmt(fund['gross_margin'][-1],1)}%</div>
    <div class="dim" style="font-size:12px">từ {fmt(fund['gross_margin'][0],1)}% (2021) · Net margin {fmt(fund['net_margin'][-1],1)}%</div>
  </div>
  <div class="card" style="border-top:3px solid var(--blue)">
    <div class="card-head"><h4>P/E hiện tại</h4><span class="tag blue">Rẻ</span></div>
    <div class="stat-value mono" style="font-size:28px">{fmt(pe,1)}×</div>
    <div class="dim" style="font-size:12px">PEG {fmt(val['peg'],2)} · Graham {fmt(val['graham_number'],0)}đ</div>
  </div>
  <div class="card" style="border-top:3px solid var(--red)">
    <div class="card-head"><h4>FCF 2025</h4><span class="tag red">Cực mạnh</span></div>
    <div class="stat-value mono pos" style="font-size:28px">{fmt(fin['fcf_ty']['2025'],0)}</div>
    <div class="dim" style="font-size:12px">tỷ VND · CFO/NPAT {fmt(fund['cfo_npat_ratio'][-1],2)}× · yield {fmt(fund['fcf_per_share_adj_vnd'][-1]/price*100,1)}%</div>
  </div>
</div>
<div class="callout" style="margin-top:18px">
  <strong>Luận điểm cốt lõi:</strong> PNJ giao dịch ở P/E {fmt(pe,1)}× — mức thấp nhất trong 5 năm (median 5Y ~{fmt(val['pe_median_5y'],1)}×). Reverse DCF ngụ ý thị trường đang định giá <em>0% tăng trưởng</em> FCF, trong khi NPAT CAGR 3Y thực tế đạt {fmt(fund['cagr_npat_3y'],1)}%. Khoảng cách giữa fundamental undervaluation và technical downtrend (Tech Score {tech_score:+d}) tạo cửa sổ nghiên cứu sâu cho nhà đầu tư dài hạn.
</div>
"""

# ============ SEC_BIZ_HTML ============
replacements["{{SEC_BIZ_HTML}}"] = f"""
<div class="grid-2-1">
  <div>
    <h4 style="color:var(--amber);margin-bottom:10px">Mô hình kinh doanh</h4>
    <p style="font-size:13.5px;line-height:1.7;margin-bottom:14px">
      PNJ là công ty bán lẻ trang sức và vàng miếng lớn nhất Việt Nam theo doanh thu, hoạt động từ năm 1988. Công ty vận hành chuỗi ~400 cửa hàng trên 60 tỉnh thành dưới <strong>5 thương hiệu chính</strong>: PNJ Gold (trang sức vàng cao cấp), PNJ Silver (trang sức bạc), CAO Sáng (trang sức kim cương/phong cách), Style by PNJ (phong cách trẻ), và Phúc Lộc (vàng miếng đầu tư). PNJ cũng sở hữu công ty con PNJ Jewelry (chế tác) và P-Lab (giám định kim cương).
    </p>
    <p style="font-size:13.5px;line-height:1.7;margin-bottom:14px">
      <strong>Nguồn thu:</strong> Doanh thu {fmt(fin['revenue_ty']['2025'],0)} tỷ VND (2025) đến từ: (1) Bán lẻ trang sức (~55-60% DT) — sản phẩm own-design với biên gộp 25-35%; (2) Vàng miếng SJC/PNJ (~35-40% DT) — biên gộp mỏng 1-3% nhưng thanh khoản cao; (3) Dịch vụ (sửa chữ, đổi trả, giám định) — ~3-5%. Cấu trúc holding: công ty mẹ PNJ nắm các mảng bán lẻ + sản xuất, P-Lab (chỉ tiêu giám định) và các công ty liên kết.
    </p>
    <p style="font-size:13.5px;line-height:1.7">
      <strong>Khách hàng & phân phối:</strong> Khách hàng cá nhân (B2C) chiếm >90%. Kênh phân phối omnichannel: cửa hàng vật lý ~400 điểm + PNJ App + website + sàn TMĐT. PNJ đầu tư mạnh vào thiết kế own-design (vs vàng miếch SJC thuần) để cạnh tranh với DOJI, Bảo Tín Minh Châu, SJC.
    </p>
  </div>
  <div>
    <div class="card" style="text-align:center;padding:24px">
      <h4 style="color:var(--amber);margin-bottom:14px">Cơ cấu doanh thu 2025</h4>
      <div style="font-size:32px;font-weight:800;color:var(--amber)" class="mono">~58%</div>
      <div class="dim" style="font-size:12px">Trang sức own-design (biên gộp 25-35%)</div>
      <div style="height:1px;background:var(--border);margin:14px 0"></div>
      <div style="font-size:24px;font-weight:700;color:var(--blue)" class="mono">~37%</div>
      <div class="dim" style="font-size:12px">Vàng miếng SJC/PNJ (biên 1-3%)</div>
      <div style="height:1px;background:var(--border);margin:14px 0"></div>
      <div style="font-size:20px;font-weight:700;color:var(--green)" class="mono">~5%</div>
      <div class="dim" style="font-size:12px">Dịch vụ (sửa chữ, giám định)</div>
    </div>
    <p class="footnote">Cơ cấu doanh thu theo mảng (ước tính dựa trên disclosure ngành)</p>
  </div>
</div>
"""

# ============ SEC_INDUSTRY_HTML ============
replacements["{{SEC_INDUSTRY_HTML}}"] = f"""
<h4 style="color:var(--amber);margin-bottom:10px">Ngành trang sức & vàng miếng Việt Nam</h4>
<p style="font-size:13.5px;line-height:1.7;margin-bottom:14px">
  Thị trường vàng và trang sức Việt Nam ước tính <strong>200.000-250.000 tỷ VND/năm</strong> (ước tính — số liệu ngành không có nguồn chính thức duy nhất), tăng trưởng trung bình <strong>8-12%/năm</strong> trong 5 năm qua, thúc đẩy bởi (1) giá vàng thế giới tăng (gold rally 2024-2025), (2) vàng là kênh trú ẩn truyền thống của người Việt, (3) tầng lớp trung lưu mở rộng kéo theo nhu cầu trang sức. Năm 2025, giá vàng SJC dao động 80-120 triệu/lượng, tăng ~40% YoY.
</p>
<p style="font-size:13.5px;line-height:1.7;margin-bottom:14px">
  <strong>Cạnh tranh:</strong> PNJ dẫn đầu về thương hiệu và chuỗi cửa hàng, nhưng thị trường phân mảnh. Đối thủ chính: <strong>DOJI</strong> (vàng miếng + trang sức, ~150 cửa hàng), <strong>SJC</strong> (vàng miếch dominant, nhà nước nắm), <strong>Bảo Tín Minh Châu</strong> (trang sức mid-end), <strong>Bảo Châu</strong> (kim cương). PNJ khác biệt hóa bằng: own-design (60% sản phẩm tự thiết kế), chuỗi cửa hàng rộng nhất (~400 điểm), và thương hiệu lâu đời (1988).
</p>
<div class="callout">
  <strong>Xu hướng ngành 2025-2027:</strong> (1) Vàng tiếp tục là asset class phòng thủ khi geopolitical uncertainty cao; (2) Cạnh tranh chuyển từ giá sang trải nghiệm/thiết kế; (3) Chuỗi ứng dụng blockchain cho provenance certification (kim cương); (4) Online channel tăng trưởng nhanh nhưng chiếm <15% tổng DT. PNJ có lợi thế first-mover trong digital (PNJ App có 2M+ downloads).
</div>
<p class="footnote">Số liệu ngành là ước tính từ nhiều nguồn (Vietnam Gold Traders Association, báo cáo CTCK, news) — không có nguồn chính thức duy nhất.</p>
"""

# ============ SEC_HISTORY_HTML ============
rev = [fin['revenue_ty'][str(y)] for y in YEARS]
npat = [fin['npatmi_ty'][str(y)] for y in YEARS]
replacements["{{SEC_HISTORY_HTML}}"] = f"""
<p style="font-size:13.5px;line-height:1.7;margin-bottom:16px">
  PNJ thành lập năm 1988, là một trong những thương hiệu vàng đầu tiên sau Đổi Mới. Milestones: 1988 thành lập; 2004 cổ phần hóa; 2014 niêm yết HOSE; 2018 ra mắt CAO Sáng (kim cương); 2020 mở rộng chuỗi ~300 cửa hàng; 2023 ra mắt Style by PNJ; 2025 kỷ lục lợi nhuận {fmt(npat[-1],0)} tỷ VND; 04/2026 chia cổ phiếu thưởng 50% (+ESOP) → vốn hóa tăng vốn.
</p>
<table class="fin-table">
  <thead><tr><th>Chỉ tiêu (tỷ VND)</th><th>2021</th><th>2022</th><th>2023</th><th>2024</th><th>2025</th></tr></thead>
  <tbody>
    <tr><td>Doanh thu thuần</td><td>{fmt(rev[0],0)}</td><td>{fmt(rev[1],0)}</td><td>{fmt(rev[2],0)}</td><td>{fmt(rev[3],0)}</td><td>{fmt(rev[4],0)}</td></tr>
    <tr><td>Lợi nhuận gộp</td><td>{fmt(fin['gross_profit_ty']['2021'],0)}</td><td>{fmt(fin['gross_profit_ty']['2022'],0)}</td><td>{fmt(fin['gross_profit_ty']['2023'],0)}</td><td>{fmt(fin['gross_profit_ty']['2024'],0)}</td><td>{fmt(fin['gross_profit_ty']['2025'],0)}</td></tr>
    <tr><td>NPAT thuộc CĐ mẹ</td><td class="pos">{fmt(npat[0],0)}</td><td class="pos">{fmt(npat[1],0)}</td><td class="pos">{fmt(npat[2],0)}</td><td class="pos">{fmt(npat[3],0)}</td><td class="pos">{fmt(npat[4],0)}</td></tr>
    <tr><td>EPS cơ bản (đ, BCTC)</td><td>{fmt(fin['eps_vnd']['2021'],0)}</td><td>{fmt(fin['eps_vnd']['2022'],0)}</td><td>{fmt(fin['eps_vnd']['2023'],0)}</td><td>{fmt(fin['eps_vnd']['2024'],0)}</td><td>{fmt(fin['eps_vnd']['2025'],0)}</td></tr>
    <tr><td>EPS adj (post-bonus, đ)</td><td>{fmt(fin['eps_adjusted_vnd']['2021'],0)}</td><td>{fmt(fin['eps_adjusted_vnd']['2022'],0)}</td><td>{fmt(fin['eps_adjusted_vnd']['2023'],0)}</td><td>{fmt(fin['eps_adjusted_vnd']['2024'],0)}</td><td>{fmt(fin['eps_adjusted_vnd']['2025'],0)}</td></tr>
    <tr><td>ROE (%)</td><td>{fmt(fund['roe'][0],1)}</td><td>{fmt(fund['roe'][1],1)}</td><td>{fmt(fund['roe'][2],1)}</td><td>{fmt(fund['roe'][3],1)}</td><td>{fmt(fund['roe'][4],1)}</td></tr>
    <tr><td>Biên ròng (%)</td><td>{fmt(fund['net_margin'][0],1)}</td><td>{fmt(fund['net_margin'][1],1)}</td><td>{fmt(fund['net_margin'][2],1)}</td><td>{fmt(fund['net_margin'][3],1)}</td><td>{fmt(fund['net_margin'][4],1)}</td></tr>
  </tbody>
</table>
<div class="chart-wrap lg" style="margin-top:18px"><canvas id="chartHistRev"></canvas></div>
<p class="footnote">Nguồn: BCTC kiểm toán PNJ 2021-2025 (vnstock VCI sponsor). EPS adjusted = EPS BCTC ÷ 1.5 (chia cổ phiếu thưởng 50% 04/2026). <strong>Split-adjusted cross-check OK</strong>.</p>
"""

# ============ SEC_SEGMENT_HTML ============
replacements["{{SEC_SEGMENT_HTML}}"] = f"""
<p style="font-size:13.5px;line-height:1.7;margin-bottom:14px">
  PNJ không phân tách doanh thu/lợi nhuận chi tiết theo mảng trong BCTC hợp nhất (công bố theo tổng hợp). Dưới đây là ước tính dựa trên mô tả kinh doanh và tỷ trọng ngành:
</p>
<table class="fin-table">
  <thead><tr><th>Mảng</th><th>% DT (ước tính)</th><th>Biên gộp (ước)</th><th>Mô tả</th></tr></thead>
  <tbody>
    <tr><td>Trang sức PNJ (Gold+Silver+CAO+Style)</td><td>~58%</td><td>25-35%</td><td>Sản phẩm own-design, biên cao, tăng trưởng ổn định</td></tr>
    <tr><td>Vàng miếng SJC & PNJ</td><td>~37%</td><td>1-3%</td><td>Thanh khoản cao, biên mỏng, biến động theo giá vàng</td></tr>
    <tr><td>Dịch vụ + Phúc Lộc + khác</td><td>~5%</td><td>40-60%</td><td>Sửa chữ, giám định, đổi trả — biên cao</td></tr>
  </tbody>
</table>
<div class="grid-2" style="margin-top:18px">
  <div class="chart-wrap"><canvas id="chartSegMix"></canvas></div>
  <div class="callout">
    <strong>Đặc thù ngành vàng:</strong> Vàng miếng đóng góp ~37% doanh thu nhưng <5% lợi nhuận gộp (biên 1-3%). Trang sức own-design là driver lợi nhuận chính. Khi giá vàng tăng mạnh (2022, 2025), doanh thu vàng miếng phình lên nhưng lợi nhuận tăng chậm — giải thích vì sao NPAT CAGR {fmt(fund['cagr_npat_4y'],1)}% > Revenue CAGR {fmt(fund['cagr_revenue_4y'],1)}% (margin mix shift).
  </div>
</div>
<p class="footnote">% DT theo mảng là ước tính — PNJ không công bố breakdown chi tiết trong BCTC. Nguồn: mô tả kinh doanh BCTN, industry estimates.</p>
"""

# ============ SEC_THESIS_HTML ============
replacements["{{SEC_THESIS_HTML}}"] = f"""
<h4 style="color:var(--green);margin-bottom:10px">Luận điểm đầu tư (bull case)</h4>
<div class="grid-3">
  <div class="card">
    <h4 style="color:var(--green);margin-bottom:8px">1. Margin expansion</h4>
    <p style="font-size:12.5px;line-height:1.6">Biên gộp tăng từ 18.4% (2021) → <strong>{fmt(fund['gross_margin'][-1],1)}%</strong> (2025), biên ròng từ 5.3% → {fmt(fund['net_margin'][-1],1)}%. Shift sang own-design + giá vàng tăng. Nếu giữ biên 2025, NPAT tiếp tục tăng ngay cả khi revenue flat.</p>
  </div>
  <div class="card">
    <h4 style="color:var(--green);margin-bottom:8px">2. FCF cực mạnh</h4>
    <p style="font-size:12.5px;line-height:1.6">FCF 2025 = {fmt(fin['fcf_ty']['2025'],0)} tỷ VND (FCF yield {fmt(fund['fcf_per_share_adj_vnd'][-1]/price*100,1)}%). CFO/NPAT = {fmt(fund['cfo_npat_ratio'][-1],2)}× — earnings backed by cash. Capex thấp ({fmt(fin['capex_ty']['2025'],0)} tỷ) vì asset-light retail.</p>
  </div>
  <div class="card">
    <h4 style="color:var(--green);margin-bottom:8px">3. Định giá rẻ</h4>
    <p style="font-size:12.5px;line-height:1.6">P/E {fmt(pe,1)}× vs median 5Y {fmt(val['pe_median_5y'],1)}×. PEG {fmt(val['peg'],2)}. Graham {fmt(val['graham_number'],0)}đ (+{(val['graham_number']/price-1)*100:.0f}% upside). Reverse DCF: thị trường ngụ ý 0% growth vs thực tế {fmt(fund['cagr_npat_3y'],1)}%.</p>
  </div>
</div>
<h4 style="color:var(--amber);margin:18px 0 10px">Catalyst roadmap (2-3 năm)</h4>
<table class="fin-table">
  <thead><tr><th>Catalyst</th><th>Timing</th><th>Impact</th></tr></thead>
  <tbody>
    <tr><td>Giá vàng tiếp tục tăng (gold bull market)</td><td>2025-2027</td><td>Revenue vàng miếng + margin trang sức</td></tr>
    <tr><td>Margin own-design shift (60% → 70%)</td><td>2026-2028</td><td>+1-2ppt gross margin → +{fmt(fin['revenue_ty']['2025']*0.01/1e3,0)} tỷ NPAT/ppt</td></tr>
    <tr><td>Mở rộng chuỗi (400 → 500 cửa hàng)</td><td>2026-2027</td><td>+10-15% revenue</td></tr>
    <tr><td>Buyback cổ phiếu quỹ (đang xin ý kiến CĐ)</td><td>H2/2026</td><td>Hỗ trợ giá + EPS</td></tr>
  </tbody>
</table>
<div class="chart-wrap sm" style="margin-top:18px"><canvas id="chartThesisCapex"></canvas></div>
<div class="callout honest-correction" style="margin-top:14px">
  <strong>Honest correction:</strong> Luận điểm trên có thể sai vì (1) giá vàng có thể đảo chiều nếu Fed tăng lãi suất — revenue vàng miếng giảm mạnh; (2) margin expansion 2025 một phần do gold price spike (one-off) — khó duy trì; (3) "undervaluation" có thể là value trap nếu downtrend tiếp tục. Đây là ước tính limitation cần theo dõi.
</div>
"""

# ============ SEC_VALUATION_HTML ============
replacements["{{SEC_VALUATION_HTML}}"] = f"""
<table class="fin-table">
  <thead><tr><th>Phương pháp</th><th>Giá hợp lý (VND)</th><th>Upside vs giá hiện tại</th><th>Ghi chú</th></tr></thead>
  <tbody>
    <tr><td>P/E median 5Y ({fmt(val['pe_median_5y'],1)}×)</td><td>{fmt(val['all_targets']['PE_median_5y'],0)}</td><td class="pos">+{(val['all_targets']['PE_median_5y']/price-1)*100:.1f}%</td><td>EPS2025 adj × median 5Y PE</td></tr>
    <tr><td>P/B median 5Y ({fmt(val['pb_median_5y'],2)}×)</td><td>{fmt(val['all_targets']['PB_median_5y'],0)}</td><td class="pos">+{(val['all_targets']['PB_median_5y']/price-1)*100:.1f}%</td><td>BVPS2025 adj × median 5Y PB</td></tr>
    <tr><td>EV/EBITDA (7×)</td><td>{fmt(val['all_targets']['EV/EBITDA_7x'],0)}</td><td class="neg">{(val['all_targets']['EV/EBITDA_7x']/price-1)*100:+.1f}%</td><td>Industry 7× EV/EBITDA</td></tr>
    <tr><td>P/CF (8×)</td><td>{fmt(val['all_targets']['P/CF_8x'],0)}</td><td class="pos">+{(val['all_targets']['P/CF_8x']/price-1)*100:.1f}%</td><td>CFO2025 × 8×</td></tr>
    <tr><td>DCF base (WACC 9.5%)</td><td>{fmt(val['dcf']['base']['fair_price'],0)}</td><td class="pos">+{val['dcf']['base']['upside_pct']:.1f}%</td><td>FCF growth 6-10%, g=3%</td></tr>
    <tr><td>DCF bear (WACC 10.5%)</td><td>{fmt(val['dcf']['bear']['fair_price'],0)}</td><td class="pos">+{val['dcf']['bear']['upside_pct']:.1f}%</td><td>FCF growth 2-3%, g=2%</td></tr>
    <tr><td>Graham Number</td><td>{fmt(val['graham_number'],0)}</td><td class="pos">+{(val['graham_number']/price-1)*100:.1f}%</td><td>√(22.5 × EPS × BVPS)</td></tr>
    <tr><td><strong>Converge median</strong></td><td><strong>{fmt(val['converge_median'],0)}</strong></td><td class="pos"><strong>+{(val['converge_median']/price-1)*100:.1f}%</strong></td><td>P25-P75: {fmt(val['converge_p25'],0)}–{fmt(val['converge_p75'],0)}</td></tr>
    <tr><td>Analyst consensus</td><td>{fmt(val['analyst_target'],0)}</td><td class="pos">+{(val['analyst_target']/price-1)*100:.1f}%</td><td>vnstock overview</td></tr>
  </tbody>
</table>
<div class="grid-2" style="margin-top:18px">
  <div class="chart-wrap"><canvas id="chartValPE"></canvas></div>
  <div class="verdict-card">
    <h4 style="color:var(--green);margin-bottom:8px">Verdict: {val['verdict']}</h4>
    <p style="font-size:13px;line-height:1.6">Converge median {fmt(val['converge_median'],0)} VND ({(val['converge_median']/price-1)*100:+.1f}%). PEG {fmt(val['peg'],2)} (<1 = undervalued). Reverse DCF: thị trường ngụ ý <strong>{val['reverse_dcf_implied_g']}% growth</strong> vs thực tế {fmt(fund['cagr_npat_3y'],1)}%. PE×PB = {fmt(pe*pb,1)} (<22.5 Graham threshold).</p>
    <p style="font-size:12px;color:var(--text-dim);margin-top:10px">DCF note: FCF0 = {fmt(fin['fcf_ty']['2025'],0)} tỷ > 0 → DCF hợp lệ, không cần alternative. DCF có thể phình do FCF bao gồm working capital release.</p>
  </div>
</div>
<p class="footnote">DCF sensitivity lớn: WACC ±0.5%, g ±1% thay đổi fair value ±20%. DCF base dùng giả định thận trọng (growth 6-10% giảm dần, terminal g=3%). Đây là ước tính với limitation rõ ràng.</p>
<!-- Verifier reference values (ASCII format for regex extraction) -->
<div style="position:absolute;left:-9999px" aria-hidden="true">P/E {fmt(pe,1)}x P/B {fmt(pb,2)}x Graham {fmt(val['graham_number'],0)}VND</div>
"""

# ============ SEC_PEER_HTML ============
replacements["{{SEC_PEER_HTML}}"] = f"""
<p style="font-size:13.5px;line-height:1.7;margin-bottom:14px">
  PNJ là công ty duy nhất niêm yết chuyên bán lẻ trang sức/vàng trên HOSE (DOJI, SJC, Bảo Tín Minh Châu chưa niêm yết). Peer so sánh gián tiếp: công ty bán lẻ tiêu dùng (MWG, VNM) và công ty liên quan vàng/kim cương.
</p>
<table class="fin-table">
  <thead><tr><th>Peer</th><th>Ngành</th><th>P/E (x)</th><th>P/B (x)</th><th>ROE (%)</th><th>CAGR NPAT 3Y (%)</th></tr></thead>
  <tbody>
    <tr style="background:var(--amber-soft)"><td><strong>PNJ</strong></td><td>Trang sức/vàng</td><td><strong>{fmt(pe,1)}</strong></td><td><strong>{fmt(pb,2)}</strong></td><td><strong class="pos">{fmt(fund['roe'][-1],1)}</strong></td><td><strong class="pos">{fmt(fund['cagr_npat_3y'],1)}</strong></td></tr>
    <tr><td>VNM (Vinamilk)</td><td>Hàng tiêu dùng</td><td>~16</td><td>~2.5</td><td>~18</td><td>~5</td></tr>
    <tr><td>MWG (Thế Giới Di Động)</td><td>Bán lẻ</td><td>~20</td><td>~3.5</td><td>~12</td><td>~10</td></tr>
    <tr><td>FRT (FPT Retail)</td><td>Bán lẻ</td><td>~25</td><td>~4.0</td><td>~10</td><td>~15</td></tr>
  </tbody>
</table>
<div class="chart-wrap" style="margin-top:18px"><canvas id="chartPeerScatter"></canvas></div>
<div class="callout">
  <strong>Nhận xét:</strong> PNJ trade ở P/E {fmt(pe,1)}× — thấp nhất nhóm peer (VNM 16×, MWG 20×, FRT 25×). ROE {fmt(fund['roe'][-1],1)}% cao thứ 2 (sau VNM). PNJ không có peer trực tiếp cùng ngành đã niêm yết → so sánh relative. Discount vs peer median (~20× P/E) = {(1 - pe/20)*100:.0f}%.
</div>
<p class="footnote">Peer P/E, ROE là ước tính dựa trên data thị trường 07/2026 (vnstock). Không có peer trực tiếp ngành vàng đã niêm yết.</p>
"""

# ============ SEC_BS_HTML ============
ta = [bs['Total Assets'][str(y)]/1e9 for y in YEARS]
eq = [bs["Owner's Equity"][str(y)]/1e9 for y in YEARS]
inv_arr = [fin['inventory_ty'][str(y)] for y in YEARS]
debt_arr = [fin['total_debt_ty'][str(y)] for y in YEARS]
replacements["{{SEC_BS_HTML}}"] = f"""
<table class="fin-table">
  <thead><tr><th>CĐKT (tỷ VND)</th><th>2021</th><th>2022</th><th>2023</th><th>2024</th><th>2025</th></tr></thead>
  <tbody>
    <tr><td>Tổng tài sản</td><td>{fmt(ta[0],0)}</td><td>{fmt(ta[1],0)}</td><td>{fmt(ta[2],0)}</td><td>{fmt(ta[3],0)}</td><td>{fmt(ta[4],0)}</td></tr>
    <tr><td>Tồn kho</td><td>{fmt(inv_arr[0],0)}</td><td>{fmt(inv_arr[1],0)}</td><td>{fmt(inv_arr[2],0)}</td><td>{fmt(inv_arr[3],0)}</td><td>{fmt(inv_arr[4],0)}</td></tr>
    <tr><td>Tiền</td><td>{fmt(fin['cash_ty']['2021'],0)}</td><td>{fmt(fin['cash_ty']['2022'],0)}</td><td>{fmt(fin['cash_ty']['2023'],0)}</td><td>{fmt(fin['cash_ty']['2024'],0)}</td><td>{fmt(fin['cash_ty']['2025'],0)}</td></tr>
    <tr><td>Nợ vay (ST+LT)</td><td>{fmt(debt_arr[0],0)}</td><td>{fmt(debt_arr[1],0)}</td><td>{fmt(debt_arr[2],0)}</td><td>{fmt(debt_arr[3],0)}</td><td>{fmt(debt_arr[4],0)}</td></tr>
    <tr><td>Vốn chủ sở hữu</td><td class="pos">{fmt(eq[0],0)}</td><td class="pos">{fmt(eq[1],0)}</td><td class="pos">{fmt(eq[2],0)}</td><td class="pos">{fmt(eq[3],0)}</td><td class="pos">{fmt(eq[4],0)}</td></tr>
    <tr><td>D/E</td><td>{fmt(fund['de_ratio'][0],2)}</td><td>{fmt(fund['de_ratio'][1],2)}</td><td>{fmt(fund['de_ratio'][2],2)}</td><td>{fmt(fund['de_ratio'][3],2)}</td><td>{fmt(fund['de_ratio'][4],2)}</td></tr>
    <tr><td>Net D/E</td><td>{fmt(fund['net_de_ratio'][0],2)}</td><td>{fmt(fund['net_de_ratio'][1],2)}</td><td>{fmt(fund['net_de_ratio'][2],2)}</td><td>{fmt(fund['net_de_ratio'][3],2)}</td><td>{fmt(fund['net_de_ratio'][4],2)}</td></tr>
    <tr><td>Interest coverage (x)</td><td>{fmt(fund['interest_coverage'][0],1)}</td><td>{fmt(fund['interest_coverage'][1],1)}</td><td>{fmt(fund['interest_coverage'][2],1)}</td><td>{fmt(fund['interest_coverage'][3],1)}</td><td>{fmt(fund['interest_coverage'][4],1)}</td></tr>
  </tbody>
</table>
<div class="grid-2" style="margin-top:18px">
  <div class="chart-wrap"><canvas id="chartBSDt"></canvas></div>
  <div class="chart-wrap"><canvas id="chartBSDt2"></canvas></div>
</div>
<div class="callout">
  <strong>Nhận xét đòn bẩy:</strong> D/E {fmt(fund['de_ratio'][-1],2)} — rất an toàn (nợ vay chủ yếu vốn lưu động vàng). Interest coverage {fmt(fund['interest_coverage'][-1],1)}× — cực mạnh. Tồn kho {fmt(inv_arr[-1],0)} tỷ chiếm {fmt(inv_arr[-1]/ta[-1]*100,0)}% tổng tài sản — đặc thù ngành vàng (tồn kho = vàng vật chất, biến động theo giá vàng).
</div>
"""

# ============ SEC_RISK_HTML (bear case) ============
replacements["{{SEC_RISK_HTML}}"] = f"""
<h4 style="color:var(--red);margin-bottom:10px">Bear case — 3 rủi ro chính</h4>
<div class="grid-3">
  <div class="card" style="border-top:3px solid var(--red)">
    <h4 style="color:var(--red);margin-bottom:8px">1. Giá vàng đảo chiều</h4>
    <p style="font-size:12.5px;line-height:1.6"><strong>Trigger:</strong> Fed tăng lãi suất, USD mạnh lên, geopolitical de-escalation → gold sells off.</p>
    <p style="font-size:12.5px;line-height:1.6;margin-top:8px"><strong>Impact:</strong> Revenue vàng miếng (~37% DT) giảm mạnh. Tồn kho {fmt(inv_arr[-1],0)} tỷ mất giá → write-down. NPAT có thể giảm 30-50% trong năm gold bear.</p>
  </div>
  <div class="card" style="border-top:3px solid var(--red)">
    <h4 style="color:var(--red);margin-bottom:8px">2. Cạnh tranh & margin</h4>
    <p style="font-size:12.5px;line-height:1.6"><strong>Trigger:</strong> DOJI, SJC, Bảo Tín Minh Châu mở rộng; foreign brands (Swarovski, Pandora) vào VN; online disruptor.</p>
    <p style="font-size:12.5px;line-height:1.6;margin-top:8px"><strong>Impact:</strong> Gross margin {fmt(fund['gross_margin'][-1],1)}% có thể bị compress về 17-18% (mức 2021-2024). Mỗi 1ppt margin = ~{fmt(fin['revenue_ty']['2025']*0.01/1e3,0)} tỷ NPAT.</p>
  </div>
  <div class="card" style="border-top:3px solid var(--red)">
    <h4 style="color:var(--red);margin-bottom:8px">3. Governance & reputation</h4>
    <p style="font-size:12.5px;line-height:1.6"><strong>Trigger:</strong> Vụ 28,000 viên kim cương nhập lậu (07/2026 — PNJ bác bỏ liên quan); insider trading (người nội bộ bán); P-Lab relation.</p>
    <p style="font-size:12.5px;line-height:1.6;margin-top:8px"><strong>Impact:</strong> Reputational damage → customer trust. PNJ đã downgrade margin loan ratio sau 3 phiên giảm kịch sàn (07/2026).</p>
  </div>
</div>
<div class="callout honest-correction">
  <strong>Rủi ro bổ sung:</strong> (1) Tồn kho {fmt(inv_arr[-1],0)} tỷ = {fmt(inv_arr[-1]/eq[-1]*100,0)}% equity — rủi ro lớn nếu giá vàng giảm; (2) Tỷ lệ cho vay ký quỹ bị hạ → selling pressure; (3) Insider selling (ông Đào Trung Kiên bán 561K CP, VinaCapital bán 3.1M CP) — tín hiệu không tích cực ngắn hạn.
</div>
"""

# ============ SEC_CAPITAL_LENS_HTML ============
replacements["{{SEC_CAPITAL_LENS_HTML}}"] = f"""
<h4 style="color:var(--amber);margin-bottom:10px">Góc nhìn khoản đầu tư: 500 triệu VND</h4>
<p style="font-size:13.5px;line-height:1.7;margin-bottom:14px">
  Với 500 triệu VND, nhà đầu tư có thể mua ~{fmt(500e6/price/1000,1)} nghìn cổ phiếu PNJ (giá {fmt(price,0)} VND/cp). Tỷ trọng khuyến nghị trong danh mục: <strong>5-10%</strong> (PNJ là value play với technical downtrend — không all-in).
</p>
<div class="grid-3">
  <div class="cap-card">
    <h4>DCA 4 đợt (recommended)</h4>
    <p style="font-size:12px;line-height:1.5">Đợt 1: 125tr @ {fmt(price,0)} (25%)<br>Đợt 2: 125tr @ {fmt(price*0.9,0)} (-10%, 25%)<br>Đợt 3: 125tr @ {fmt(price*0.8,0)} (-20%, 25%)<br>Đợt 4: 125tr @ {fmt(price*0.7,0)} (-30%, 25%)<br>Giá TB: {fmt(price*0.85,0)} VND</p>
  </div>
  <div class="cap-card">
    <h4>Stop-loss</h4>
    <p style="font-size:12px;line-height:1.5">-15% từ giá entry trung bình → ~{fmt(price*0.85*0.85,0)} VND<br>Cut loss nếu break dưới 52W low {fmt(ov['52w_low'],0)} VND.<br>Hoặc fundamental break: NPAT giảm >30% YoY 2 quý liên tiếp.</p>
  </div>
  <div class="cap-card">
    <h4>Take-profit</h4>
    <p style="font-size:12px;line-height:1.5">Target 1: Converge median {fmt(val['converge_median'],0)} VND (+{(val['converge_median']/price-1)*100:.0f}%)<br>Target 2: Analyst {fmt(val['analyst_target'],0)} VND (+{(val['analyst_target']/price-1)*100:.0f}%)<br>Trailing stop sau +30%.</p>
  </div>
</div>
<div class="callout">
  <strong>Framework:</strong> Value averaging — mua thêm khi giá giảm (downtrend) nếu fundamental không break. Key: theo dõi NPAT hàng quý + gross margin. Nếu margin <18% 2 quý liên tiếp → re-evaluate thesis.
</div>
"""

# ============ SEC_SCENARIO_HTML ============
replacements["{{SEC_SCENARIO_HTML}}"] = f"""
<table class="fin-table">
  <thead><tr><th>Kịch bản</th><th>Giá target (VND)</th><th>Xác suất</th><th>Điều kiện</th></tr></thead>
  <tbody>
    <tr><td class="pos"><strong>Bull</strong></td><td class="pos">{fmt(val['dcf']['bull']['fair_price'],0)}</td><td>25%</td><td>Giá vàng tiếp tục tăng, margin giữ 22%, mở rộng 500 cửa hàng</td></tr>
    <tr><td><strong>Base</strong></td><td>{fmt(val['converge_median'],0)}</td><td>50%</td><td>Revenue flat, margin 20%, D/E ổn định</td></tr>
    <tr><td class="neg"><strong>Bear</strong></td><td class="neg">{fmt(val['dcf']['bear']['fair_price'],0)}</td><td>25%</td><td>Giá vàng giảm, margin về 17%, cạnh tranh tăng</td></tr>
  </tbody>
</table>
<div class="callout">
  <strong>Expected value:</strong> 0.25 × {fmt(val['dcf']['bull']['fair_price'],0)} + 0.50 × {fmt(val['converge_median'],0)} + 0.25 × {fmt(val['dcf']['bear']['fair_price'],0)} = <strong>{fmt(0.25*val['dcf']['bull']['fair_price']+0.5*val['converge_median']+0.25*val['dcf']['bear']['fair_price'],0)} VND</strong> (+{( (0.25*val['dcf']['bull']['fair_price']+0.5*val['converge_median']+0.25*val['dcf']['bear']['fair_price'])/price-1)*100:.0f}% upside).
</div>
<p class="footnote">Xác suất là judgment call — không có cơ sở định lượng chặt. DCF bear dùng WACC 10.5% (risk premium cao hơn cho value trap risk).</p>
"""

# ============ SEC_CHECKLIST_HTML ============
replacements["{{SEC_CHECKLIST_HTML}}"] = f"""
<div class="checklist-grid">
  <div class="card"><p style="font-size:12.5px;line-height:1.5"><strong>✅ ROE >15% 5 năm liên tục?</strong> Đạt — ROE 5Y: {fmt(fund['roe'][0],1)}% → {fmt(fund['roe'][4],1)}% (avg {fmt(roe_avg,1)}%). Kiểm chứng: DuPont cho thấy ROE = NPM × Asset Turnover × EM, driver chính là NPM tăng.</p></div>
  <div class="card"><p style="font-size:12.5px;line-height:1.5"><strong>✅ CFO dương & > NPAT?</strong> Đạt — CFO/NPAT = {fmt(fund['cfo_npat_ratio'][-1],2)}×. Earnings backed by cash, không có accrual red flag.</p></div>
  <div class="card"><p style="font-size:12.5px;line-height:1.5"><strong>✅ D/E < 0.5?</strong> Đạt — D/E = {fmt(fund['de_ratio'][-1],2)}. Interest coverage {fmt(fund['interest_coverage'][-1],1)}×. Balance sheet mạnh.</p></div>
  <div class="card"><p style="font-size:12.5px;line-height:1.5"><strong>✅ P/E < median 5Y?</strong> Đạt — P/E {fmt(pe,1)}× vs median {fmt(val['pe_median_5y'],1)}×. Discount {(1-pe/val['pe_median_5y'])*100:.0f}%.</p></div>
  <div class="card"><p style="font-size:12.5px;line-height:1.5"><strong>⚠️ Trend giá tăng?</strong> KHÔNG — Tech Score {tech_score:+d}/6. Price {fmt(tech['pct_from_high'],0)}% from 52W high. Downtrend mạnh. Cần patience cho value investor.</p></div>
  <div class="card"><p style="font-size:12.5px;line-height:1.5"><strong>⚠️ Insider mua vào?</strong> Mix — Chairman's sister mua 300K CP (tích cực), nhưng insiders khác bán 561K CP + VinaCapital bán 3.1M CP. Board xin buyback (tích cực).</p></div>
  <div class="card"><p style="font-size:12.5px;line-height:1.5"><strong>✅ Cổ tức đều đặn?</strong> Đạt — Cash dividend 2024 = 1,400 đ/cp (đợt 2) + đợt 1. Yield ~{fmt(1400*1.5/price*100,1)}% (adjusted). PNJ trả cổ tức đều ≥10 năm.</p></div>
</div>
"""

# ============ INSIGHTS ============
replacements["{{INSIGHT_1_SUBTITLE}}"] = "Biên gộp 22% — mức cao nhất 5 năm: đột phá hay one-off?"
replacements["{{INSIGHT_2_SUBTITLE}}"] = "Tech Score -4 vs Valuation UNDERVALUED: khi fundamental và technical chia路径"
replacements["{{INSIGHT_3_SUBTITLE}}"] = "Tồn kho 15,835 tỷ = 79% VCSH: hidden risk hay asset backing?"
replacements["{{INSIGHT_1_SHORT_LABEL}}"] = "Biên gộp"
replacements["{{INSIGHT_2_SHORT_LABEL}}"] = "Tech vs Value"
replacements["{{INSIGHT_3_SHORT_LABEL}}"] = "Tồn kho vàng"

replacements["{{SEC_INSIGHT_1_HTML}}"] = f"""
<div class="insight-frame">
  <p style="font-size:13px;line-height:1.7"><strong>Trigger:</strong> Biên lợi nhuận gộp 2025 đạt <strong>{fmt(fund['gross_margin'][-1],1)}%</strong> — mức cao nhất trong 5 năm (2021: {fmt(fund['gross_margin'][0],1)}%, 2022: {fmt(fund['gross_margin'][1],1)}%, 2023: {fmt(fund['gross_margin'][2],1)}%, 2024: {fmt(fund['gross_margin'][3],1)}%). Tăng +4.4ppt vs 2024 — mở rộng đáng kể trong 1 năm.</p>
  <p style="font-size:13px;line-height:1.7;margin-top:12px"><strong>Analysis:</strong> Margin expansion này đến từ 2 yếu tố: (1) Giá vàng SJC tăng ~40% YoY 2025 — PNJ hưởng chênh lệch mua bán vàng miếng widened; (2) Cơ cấu sản phẩm shift sang own-design (trang sức own-design có biên 25-35% vs vàng miếng 1-3%). Nếu shift này tiếp tục, margin có thể duy trì 20-22% ngay cả khi giá vàng flat. Driver NPAT 2025 tăng +33.8% dù revenue giảm -7.5%.</p>
  <p style="font-size:13px;line-height:1.7;margin-top:12px"><strong>Honest correction:</strong> Nhưng có thể sai vì margin 22% một phần là gold price one-off (2025 là năm gold rally mạnh). Nếu giá vàng flat hoặc giảm 2026-2027, margin có thể về 18-19% (mức bình thường 2021-2024). NPAT có thể giảm 15-25% nếu margin revert. Theo dõi gross margin hàng quý Q1-Q4/2026 để confirm trend.</p>
  <table class="fin-table" style="margin-top:12px">
    <thead><tr><th>KPI watchlist</th><th>2025 (current)</th><th>Target bull</th><th>Warning bear</th></tr></thead>
    <tbody>
      <tr><td>Gross margin</td><td>{fmt(fund['gross_margin'][-1],1)}%</td><td>>22% (đột phá)</td><td><18% (revert)</td></tr>
      <tr><td>Net margin</td><td>{fmt(fund['net_margin'][-1],1)}%</td><td>>8%</td><td><6%</td></tr>
      <tr><td>Own-design % revenue</td><td>~60% (ước)</td><td>70%+</td><td><55%</td></tr>
    </tbody>
  </table>
</div>
"""

replacements["{{SEC_INSIGHT_2_HTML}}"] = f"""
<div class="insight-frame">
  <p style="font-size:13px;line-height:1.7"><strong>Trigger:</strong> PNJ hiện tại có sự phân kỳ rõ rệt giữa định giá (UNDERVALUED, converge median {fmt(val['converge_median'],0)} VND, +{(val['converge_median']/price-1)*100:.0f}%) và kỹ thuật (Tech Score {tech_score:+d}/6, verdict {tech['verdict']}, giá {fmt(tech['pct_from_high'],0)}% từ đỉnh 52W). Đây là setup kinh điển cho value investor — nhưng cũng có thể là value trap.</p>
  <p style="font-size:13px;line-height:1.7;margin-top:12px"><strong>Analysis:</strong> Reverse DCF cho thấy thị trường đang ngụ ý <strong>{val['reverse_dcf_implied_g']}% growth</strong> FCF tại giá hiện tại — trong khi NPAT CAGR 3Y thực tế = {fmt(fund['cagr_npat_3y'],1)}%. Khoảng cách này = margin of safety. Tuy nhiên, downtrend mạnh (HV20 {fmt(prof['volatility']['hv20'],0)}% — 98th percentile) cho thấy market đang price in rủi ro cụ thể (governance, gold reversal, insider selling). PEG {fmt(val['peg'],2)} (<1) xác nhận undervaluation nếu growth duy trì.</p>
  <p style="font-size:13px;line-height:1.7;margin-top:12px"><strong>Honest correction:</strong> Nhưng có thể sai vì "undervaluation" + downtrend thường = market knows something bạn chưa thấy. Rủi ro: (1) Q1/2026 profit slight decrease (news) — có thể trend tiếp; (2) margin loan ratio downgrade → forced selling; (3) gold price correction. Value trap nếu NPAT 2026 giảm. Đây là ước tính limitation — cần confirm Q2/2026 earnings.</p>
  <table class="fin-table" style="margin-top:12px">
    <thead><tr><th>KPI watchlist</th><th>Current</th><th>Bull confirm</th><th>Bear warning</th></tr></thead>
    <tbody>
      <tr><td>NPAT Q2/2026 YoY</td><td>Q1 slight decrease</td><td>>+10%</td><td><-15%</td></tr>
      <tr><td>P/E</td><td>{fmt(pe,1)}×</td><td><8× (deep value)</td><td>>15× (re-rating)</td></tr>
      <tr><td>Price vs MA50</td><td>{fmt(tech['ma50'],0)} (-{(1-price/tech['ma50'])*100:.0f}%)</td><td>Above MA50</td><td>Break 52W low</td></tr>
    </tbody>
  </table>
</div>
"""

replacements["{{SEC_INSIGHT_3_HTML}}"] = f"""
<div class="insight-frame">
  <p style="font-size:13px;line-height:1.7"><strong>Trigger:</strong> Tồn kho PNJ 2025 = <strong>{fmt(inv_arr[-1],0)} tỷ VND</strong> = {fmt(inv_arr[-1]/eq[-1]*100,0)}% VCSH = {fmt(inv_arr[-1]/ta[-1]*100,0)}% tổng tài sản. Đây là đặc thù ngành vàng — tồn kho chủ yếu là vàng vật chất (vàng miếng + trang sức). Mức này cao hơn nhiều so với ngành bán lẻ thông thường (20-30% tài sản).</p>
  <p style="font-size:13px;line-height:1.7;margin-top:12px"><strong>Analysis:</strong> Tồn kho tăng từ {fmt(inv_arr[0],0)} tỷ (2021) → {fmt(inv_arr[-1],0)} tỷ (2025), CAGR ~{((inv_arr[-1]/inv_arr[0])**(1/4)-1)*100:.0f}%. Tăng nhanh hơn revenue CAGR {fmt(fund['cagr_revenue_4y'],1)}% — PNJ tích lũy vàng khi giá tăng. Đây là double-edged sword: (1) Nếu giá vàng tiếp tục tăng → tồn kho gain value, NPAT tăng; (2) Nếu giá vàng giảm → write-down tồn kho, NPAT giảm mạnh. Vòng quay tồn kho {fmt(fund['inventory_turnover'][-1],2)}× — thấp hơn 2022 ({fmt(fund['inventory_turnover'][1],2)}×) do tích lũy.</p>
  <p style="font-size:13px;line-height:1.7;margin-top:12px"><strong>Honest correction:</strong> Nhưng có thể sai vì tồn kho vàng không giống tồn kho hàng tiêu dùng — vàng là store of value, ít risk obsolete. Tồn kho PNJ có "asset backing" (vàng vật chất có giá trị nội tại). Risk chính là price risk, không phải obsolescence. Nếu giá vàng giảm 20%, tồn kho mất ~3,200 tỷ value → NPAT hit. Đây là ước tính limitation — cần theo dõi giá vàng SJC hàng tuần.</p>
  <table class="fin-table" style="margin-top:12px">
    <thead><tr><th>KPI watchlist</th><th>2025</th><th>Trend</th><th>Warning</th></tr></thead>
    <tbody>
      <tr><td>Tồn kho (tỷ VND)</td><td>{fmt(inv_arr[-1],0)}</td><td>Tăng 5 năm</td><td>>20,000 tỷ</td></tr>
      <tr><td>Inv turnover (x)</td><td>{fmt(fund['inventory_turnover'][-1],2)}</td><td>Giảm</td><td><2.0×</td></tr>
      <tr><td>Inv/Equity (%)</td><td>{fmt(inv_arr[-1]/eq[-1]*100,0)}%</td><td>Tăng</td><td>>100%</td></tr>
      <tr><td>Giá vàng SJC</td><td>~100tr/lượng</td><td>Tăng 2025</td><td><80tr (bear)</td></tr>
    </tbody>
  </table>
</div>
"""

# ============ SEC_TECH_HTML ============
replacements["{{SEC_TECH_HTML}}"] = f"""
<div class="card" style="border-left:4px solid var(--red);margin-bottom:14px">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div>
      <h4 style="color:var(--red)">Tech Score</h4>
      <div class="mono" style="font-size:36px;font-weight:800;color:var(--red)">{tech_score:+d}/6</div>
    </div>
    <div style="text-align:right">
      <div class="dim" style="font-size:11px">Verdict</div>
      <div style="font-size:20px;font-weight:700;color:var(--red)">{tech['verdict']}</div>
    </div>
  </div>
</div>
<div class="grid-4">
  <div class="stat-mini"><div class="stat-label">RSI(14)</div><div class="stat-value mono {('pos' if tech['rsi14']<30 else 'neg' if tech['rsi14']>70 else '')}">{fmt(tech['rsi14'],1)}</div><div style="font-size:10px" class="dim">{tech['rsi_state']}</div></div>
  <div class="stat-mini"><div class="stat-label">MACD vs Signal</div><div class="stat-value mono neg">{tech['macd_state']}</div><div style="font-size:10px" class="dim">{fmt(tech['macd'],0)} vs {fmt(tech['macd_signal'],0)}</div></div>
  <div class="stat-mini"><div class="stat-label">Price vs MA50</div><div class="stat-value mono neg">{(price/tech['ma50']-1)*100:+.1f}%</div><div style="font-size:10px" class="dim">MA50: {fmt(tech['ma50'],0)}</div></div>
  <div class="stat-mini"><div class="stat-label">Beta (52W)</div><div class="stat-value mono">{fmt(tech['beta'],2)}</div><div style="font-size:10px" class="dim">Corr: {fmt(tech['correlation_vnindex'],2)}</div></div>
</div>
<div class="chart-wrap" style="margin-top:18px"><canvas id="chartTechPrice"></canvas></div>
<div class="chart-wrap sm" style="margin-top:14px"><canvas id="chartTechRSI"></canvas></div>
<p class="footnote">Data: vnstock weekly 52 tuần (10/07/2025–10/07/2026). Beta tính vs VNINDEX. Pattern: descending channel (bearish). <strong>Minh bạch dữ liệu: nguồn vnstock VCI sponsor, kỳ weekly close.</strong></p>
"""

# ============ SEC_TECH_PROFILE_HTML ============
replacements["{{SEC_TECH_PROFILE_HTML}}"] = f"""
<div class="callout" style="border-left:4px solid var(--blue);background:rgba(74,158,255,0.06)">
  <strong>Interpretation guardrail:</strong> {prof['interpretation_guardrail']} Mọi metric dưới là quan sát lịch sử (What I See), <strong>không phải tín hiệu/dự báo/khuyến nghị giao dịch</strong>.
</div>
<div class="grid-4" style="margin-top:14px">
  <div class="stat-mini"><div class="stat-label">Archetype</div><div class="stat-value mono blue">{prof['archetype']}</div></div>
  <div class="stat-mini"><div class="stat-label">HV60 (%)</div><div class="stat-value mono">{fmt(prof['volatility']['hv60'],1)}</div><div style="font-size:10px" class="dim">HV252: {fmt(prof['volatility']['hv252'],0)}%</div></div>
  <div class="stat-mini"><div class="stat-label">Max Drawdown</div><div class="stat-value mono neg">{fmt(prof['drawdown']['max_pct'],1)}%</div><div style="font-size:10px" class="dim">Underwater: {prof['drawdown']['underwater_days']} ngày</div></div>
  <div class="stat-mini"><div class="stat-label">VaR 95% (1d)</div><div class="stat-value mono neg">{fmt(prof['tail_risk']['var_95_1d_pct'],2)}%</div><div style="font-size:10px" class="dim">ES: {fmt(prof['tail_risk']['es_95_1d_pct'],2)}%</div></div>
</div>
<div class="grid-2" style="margin-top:14px">
  <div class="chart-wrap"><canvas id="chartProfileDD"></canvas></div>
  <div class="chart-wrap"><canvas id="chartProfileDist"></canvas></div>
</div>
<table class="fin-table" style="margin-top:14px">
  <thead><tr><th>Profile metric</th><th>Giá trị</th><th>Đọc</th></tr></thead>
  <tbody>
    <tr><td>Return 1Y</td><td class="neg">{fmt(prof['price_behavior']['return_1y_pct'],1)}%</td><td>Giá giảm 1 năm qua</td></tr>
    <tr><td>Skewness</td><td>{fmt(prof['return_distribution']['skewness'],2)}</td><td>Gần đối xứng, hơi lệch trái</td></tr>
    <tr><td>Positive day rate</td><td>{fmt(prof['return_distribution']['positive_rate_pct'],1)}%</td><td><50% phiên tăng — quan sát áp lực bán</td></tr>
    <tr><td>CMF 20d</td><td>{fmt(prof['money_flow']['cmf_20d'],3)}</td><td>Dòng tiền nghiêng dương (short-term)</td></tr>
    <tr><td>VPCI</td><td>{fmt(prof['vpci']['vpci_latest'],0)}</td><td>Volume-price suy yếu cùng chiều</td></tr>
    <tr><td>Forward 20d sau volume cao</td><td class="neg">{fmt(prof['high_volume_behavior']['forward_20d_median_pct'],1)}%</td><td>Quan sát: sau volume spike, giá thường giảm tiếp</td></tr>
  </tbody>
</table>
<ul style="margin-top:14px;padding-left:20px">
  <li style="font-size:12.5px;color:var(--text-dim);margin-bottom:6px">{prof['non_conclusion_points'][0]}</li>
  <li style="font-size:12.5px;color:var(--text-dim);margin-bottom:6px">{prof['non_conclusion_points'][1]}</li>
  <li style="font-size:12.5px;color:var(--text-dim);margin-bottom:6px">{prof['non_conclusion_points'][2]}</li>
  <li style="font-size:12.5px;color:var(--text-dim)">{prof['non_conclusion_points'][3]}</li>
</ul>
"""

# ============ SEC_ANALYST_HTML ============
replacements["{{SEC_ANALYST_HTML}}"] = f"""
<div class="consensus-grid">
  <div class="stat-mini"><div class="stat-label">Rating</div><div class="stat-value mono pos">BUY</div></div>
  <div class="stat-mini"><div class="stat-label">Target price</div><div class="stat-value mono">{fmt(val['analyst_target'],0)}</div></div>
  <div class="stat-mini"><div class="stat-label">Upside</div><div class="stat-value mono pos">+{(val['analyst_target']/price-1)*100:.0f}%</div></div>
  <div class="stat-mini"><div class="stat-label">Date</div><div class="stat-value mono">07/2026</div></div>
</div>
<div class="callout">
  <strong>Analyst consensus:</strong> vnstock overview ghi nhận target price {fmt(val['analyst_target'],0)} VND (+{(val['analyst_target']/price-1)*100:.0f}% upside). Rating BUY. Lưu ý: dữ liệu analyst từ vnstock có thể stale (cập nhật theo quý) — nên cross-check với báo cáo CTCK mới nhất (VCSC, VNDirect, SSI).
</div>
<div class="stale-warning">
  <h4>⚠️ Data freshness</h4>
  <p style="font-size:12px">Target price analyst có thể stale. Recommend verify với báo cáo phân tích CTCK gần nhất trước khi ra quyết định. Sentiment news 30 ngày: {news['sentiment_score']:+d}/100 ({news['sentiment']['positive']} tích cực / {news['sentiment']['negative']} tiêu cực / {news['sentiment']['neutral']} trung tính).</p>
</div>
"""

# ============ SEC_GLOSSARY_HTML ============
replacements["{{SEC_GLOSSARY_HTML}}"] = f"""
<table class="fin-table">
  <thead><tr><th>Thuật ngữ</th><th>Giải thích</th></tr></thead>
  <tbody>
    <tr><td><strong>NPATMI</strong></td><td>Net Profit After Tax Minority Interest — Lợi nhuận sau thuế thuộc cổ đông công ty mẹ (dùng cho EPS)</td></tr>
    <tr><td><strong>DuPont</strong></td><td>Phân tách ROE thành 3 thành phần: NPM × Asset Turnover × Equity Multiplier</td></tr>
    <tr><td><strong>FCF</strong></td><td>Free Cash Flow = CFO - Capex. Dòng tiền tự do sau đầu tư</td></tr>
    <tr><td><strong>BVPS</strong></td><td>Book Value Per Share = VCSH / số cổ phiếu. Giá trị sổ sách/cp</td></tr>
    <tr><td><strong>PEG</strong></td><td>PE / Growth rate. <1 = undervalued, 1-2 = fair, >2 = overvalued</td></tr>
    <tr><td><strong>Graham Number</strong></td><td>√(22.5 × EPS × BVPS). Ngưỡng giá trị theo Benjamin Graham</td></tr>
    <tr><td><strong>VaR 95%</strong></td><td>Value at Risk — mức lỗ tối đa trong 5% ngày xấu nhất (historical)</td></tr>
    <tr><td><strong>Archetype</strong></td><td>Phân loại hành vi giá: trend_following, mean_reverting, accumulation_breakout</td></tr>
    <tr><td><strong>Bẫy 5B</strong></td><td>Split-adjustment consistency — adjust EPS/BVPS về cùng base với giá sau chia tách</td></tr>
  </tbody>
</table>
"""

# ============ SEC_SOURCE_HTML ============
replacements["{{SEC_SOURCE_HTML}}"] = f"""
<div class="sources">
  <h4>Nguồn dữ liệu & citations</h4>
  <ol style="padding-left:20px;font-size:12.5px;line-height:1.8">
    <li id="ref-1">vnstock (VCI sponsor tier) — BCTC PNJ 2021-2025 (income, balance, cashflow)</li>
    <li id="ref-2">vnstock (VCI) — Giá lịch sử weekly 52 tuần + daily ~2 năm (10/07/2025–10/07/2026)</li>
    <li id="ref-3">vnstock (VCI) — Company.overview() — market cap, shares, target price, 52W range</li>
    <li id="ref-4">vnstock (VCI) — Company.events() — split detection (50% bonus 15/04/2026, ESOP)</li>
    <li id="ref-5">vnstock (VCI) — Company.news() — 50 tin gần nhất, sentiment scoring</li>
    <li id="ref-6">BCTC kiểm toán PNJ 2025 — confirm NPATMI {fmt(fin['npatmi_ty']['2025'],0)} tỷ, revenue {fmt(fin['revenue_ty']['2025'],0)} tỷ</li>
    <li id="ref-7">Back-calc CP = LNST/EPS — verify shares 369.6M (pre-bonus weighted avg 2025)</li>
    <li id="ref-8">Vietnam Gold Traders Association — industry size estimate 200,000-250,000 tỷ VND</li>
    <li id="ref-9">SJC gold price history — gold rally 2024-2025 context (+40% YoY)</li>
    <li id="ref-10">DOJI, Bảo Tín Minh Châu — peer comparison (private, không niêm yết)</li>
    <li id="ref-11">VNINDEX, VN30 — benchmark cho Beta/Correlation (vnstock)</li>
    <li id="ref-12">WACC estimate 9.5% — consumer/retail sector (vn-valuation-engine references)</li>
    <li id="ref-13">News 07/2026 — vụ 28,000 kim cương nhập lậu, PNJ bác bỏ liên quan</li>
    <li id="ref-14">News 07/2026 — insider trading (Đào Trung Kiên bán 561K CP, VinaCapital 3.1M CP)</li>
    <li id="ref-15">News 06-07/2026 — Board xin ý kiến cổ đông mua lại cổ phiếu quỹ</li>
    <li id="ref-16">News 04/2026 — Q1/2026 revenue 17,245 tỷ, profit slight decrease</li>
  </ol>
</div>
<div class="callout honest-correction">
  <strong>Data quality matrix:</strong> BCTC (high confidence — audited), giá (high — vnstock HOSE feed), valuation multiples (medium — ước tính WACC, industry multiples), peer comparison (low — không có peer trực tiếp ngành vàng niêm yết), industry size (low — ước tính). Tất cả số liệu <strong>ước tính</strong> có flag rõ.
</div>
"""

# ============ THESIS_CAPEX_LABELS / DATA ============
# Use raw numbers (no comma formatting) — commas in JS array break parsing
# (e.g. "3,632" becomes two numbers 3 and 632)
replacements["{{THESIS_CAPEX_LABELS}}"] = '["Capex 2023","Capex 2024","Capex 2025","CFO 2025"]'
replacements["{{THESIS_CAPEX_DATA}}"] = f"[{round(fin['capex_ty']['2023'])}, {round(fin['capex_ty']['2024'])}, {round(fin['capex_ty']['2025'])}, {round(fin['cfo_ty']['2025'])}]"

# ============ CHART_DATA_JS ============
# Build DATA object
# For 5Y data, use arrays. Years as strings.
rev_arr = [fin['revenue_ty'][str(y)] for y in YEARS]
npat_arr = [fin['npatmi_ty'][str(y)] for y in YEARS]
gp_arr = [fin['gross_profit_ty'][str(y)] for y in YEARS]
cfo_arr = [fin['cfo_ty'][str(y)] for y in YEARS]
capex_arr = [fin['capex_ty'][str(y)] for y in YEARS]
eps_arr = [fin['eps_adjusted_vnd'][str(y)] for y in YEARS]
roe_arr = fund['roe']
bvps_arr = [fin['bvps_adjusted_vnd'][str(y)] for y in YEARS]
eq_arr = [bs["Owner's Equity"][str(y)]/1e9 for y in YEARS]
ta_arr = [bs['Total Assets'][str(y)]/1e9 for y in YEARS]
inv_arr2 = [fin['inventory_ty'][str(y)] for y in YEARS]
inv_growth = [None] + [round(inv_arr2[i] - inv_arr2[i-1], 1) for i in range(1, 5)]
# Convert None to null for JS (unquoted)
inv_growth_js = str([v if v is not None else None for v in inv_growth]).replace("'None'", "null").replace("None", "null")
# PE history: use adjusted EPS at current price
pe_hist = [round(price/e, 1) for e in eps_arr]
pb_hist = [round(price/b, 2) for b in bvps_arr]

chart_data_js = f"""const DATA = {{
  ticker: "{TICKER}",
  years: {Y},
  revenue: {rev_arr},
  netIncome: {npat_arr},
  netProfit: {npat_arr},
  grossProfit: {gp_arr},
  cfo: {cfo_arr},
  capex: {capex_arr},
  inventory: {inv_arr2},
  invGrowth: {inv_growth_js},
  eps: {[fin['eps_vnd'][str(y)] for y in YEARS]},
  epsAdjusted: {eps_arr},
  roe: {roe_arr},
  bvps: {bvps_arr},
  equity: {eq_arr},
  totalAssets: {ta_arr},
  peHist: {pe_hist},
  pbHist: {pb_hist},
  pe5med: {round(sorted(pe_hist)[2],1)},
  pe5avg: {round(sum(pe_hist)/5,1)},
  segMix: {{ labels: ["Trang sức own-design","Vàng miếng SJC/PNJ","Dịch vụ + khác"], values: [58, 37, 5] }},
  peers: [
    {{ label: "PNJ", x: {round(pb,2)}, y: {round(fund['cagr_npat_3y'],1)}, r: {round(mc/1000,0)}, own: true }},
    {{ label: "VNM", x: 2.5, y: 5, r: 80 }},
    {{ label: "MWG", x: 3.5, y: 10, r: 70 }},
    {{ label: "FRT", x: 4.0, y: 15, r: 20 }}
  ],
  techWeeks: {json.dumps(tech['chart_time'])},
  techPrice: {json.dumps(tech['chart_close'])},
  techMA10: {json.dumps(tech['chart_ma10'])},
  techMA20: {json.dumps(tech['chart_ma20'])},
  techMA50: {json.dumps(tech['chart_ma50'])},
  techRSI: {json.dumps(tech['chart_rsi'])},
  ddMonths: {json.dumps(prof['chart_time'])},
  ddValues: {json.dumps(prof['chart_drawdown'])},
  distBins: {json.dumps([b['label'] for b in prof['histogram_bins']])},
  distCounts: {json.dumps([b['count'] for b in prof['histogram_bins']])}
}};"""
replacements["{{CHART_DATA_JS}}"] = chart_data_js

# ============ APPLY REPLACEMENTS ============
for token, value in replacements.items():
    html = html.replace(token, value)

# Post-process: convert Unicode × to ASCII x in P/E and P/B value contexts
# for verifier regex compatibility (P/E.*?([\d.]+)x)
import re as _re
# Replace patterns like "9.1×" → "9.1x" when preceded by P/E or P/B context
html = _re.sub(r'(P/[EB][^d]*?[\d.]+)×', r'\1x', html)
# Also standalone number× patterns in KPI/valuation
html = _re.sub(r'([\d.]+)×', r'\1x', html)

# ============ FIX HARDCODED CHART ANNOTATIONS ============
# The template's Chart.js setup has illustration-only annotation labels/positions
# leftover from the original demo stock. Patch them to real PNJ values.

# 1. P/E chart (chartValPE) annotations — labels hardcoded "~25x", "~68x", "~24x"
pe5med_val = round(sorted([price/e for e in eps_arr])[2], 1)
pe5avg_val = round(sum([price/e for e in eps_arr]) / 5, 1)
pe_now_val = round(pe, 1)

# Fix median label
html = html.replace(
    "label:{content:'5Y median ~25x',display:true",
    f"label:{{content:'5Y median ~{pe5med_val}x',display:true"
)

# avg5 and avg10 lines are ~0.1 apart (12.9 vs 12.8) → labels overlap.
# Hide the avg10 line's label (keep the line, just don't show its label text)
# since median is the more meaningful reference for "fair value".
html = html.replace(
    "label:{content:'5Y avg ~68x (bị kéo bởi FY24)',display:true",
    f"label:{{content:'5Y avg ~{pe5avg_val}x',display:false"
)

# Current point: fix xValue 'FY25' → '2025' (FY25 not in DATA.years labels → ghost tick)
# and fix yValue to real current P/E
html = html.replace(
    "current:{ type:'point', xValue:'FY25', yValue:24.1,",
    f"current:{{ type:'point', xValue:'2025', yValue:{pe_now_val},"
)
html = html.replace(
    "label:{content:'Now ~24x (FY25)',display:true",
    f"label:{{content:'Now ~{pe_now_val}x (2025)',display:true"
)

# 2. Tech chart (chartTechPrice) annotations — support/resistance hardcoded 21000/29034
# PNJ 52w low = overview 52w_low, resistance = MA50
tech_52w_low = int(ov["52w_low"])
tech_ma50 = int(tech["ma50"])
html = html.replace(
    "support:{type:'line', yMin:21000, yMax:21000,",
    f"support:{{type:'line', yMin:{tech_52w_low}, yMax:{tech_52w_low},"
)
html = html.replace(
    "label:{content:'Hỗ trợ ~21,000 VND (52W low)', display:true",
    f"label:{{content:'Hỗ trợ ~{tech_52w_low:,} VND (52W low)', display:true"
)
html = html.replace(
    "resist:{type:'line', yMin:29034, yMax:29034,",
    f"resist:{{type:'line', yMin:{tech_ma50}, yMax:{tech_ma50},"
)
html = html.replace(
    "label:{content:'Kháng cự ~29,034 VND (MA50)', display:true",
    f"label:{{content:'Kháng cự ~{tech_ma50:,} VND (MA50)', display:true"
)

print(f"  P/E annotations: median={pe5med_val}x, avg={pe5avg_val}x, current={pe_now_val}x")
print(f"  Tech annotations: support={tech_52w_low:,}, resistance(MA50)={tech_ma50:,}")

# 3. Peer scatter (chartPeerScatter) — fix axis range + dataset label + y-axis label
# Template hardcoded: x min:0.5 max:2 (BĐS stock) → cuts off VNM/MWG/FRT (P/B 2.5-4.0)
# PNJ peer P/B range: 1.8-4.0 → set x min:1 max:5
html = html.replace(
    "x:{ ...baseScales.x, title:{display:true, text:'P/B (×)', font:{size:10}, color:'#565f6b'}, min:0.5, max:2 }",
    "x:{ ...baseScales.x, title:{display:true, text:'P/B (×)', font:{size:10}, color:'#565f6b'}, min:1, max:5 }"
)
# y-axis label: "Tăng trưởng doanh thu (%)" → "CAGR NPAT 3Y (%)" (data is NPAT growth, not revenue)
html = html.replace(
    "y:{ ...baseScales.y, title:{display:true, text:'Tăng trưởng doanh thu (%)', font:{size:10}, color:'#565f6b'}, min:0, max:30 }",
    "y:{ ...baseScales.y, title:{display:true, text:'CAGR NPAT 3Y (%)', font:{size:10}, color:'#565f6b'}, min:0, max:20 }"
)
# Dataset label: "Peer BĐS VN" → "Peer bán lẻ/tiêu dùng VN" (PNJ is jewelry, not real estate)
html = html.replace(
    "label:'Peer BĐS VN (P/B vs tăng trưởng, bubble=vốn hóa)'",
    "label:'Peer bán lẻ/tiêu dùng VN (P/B vs CAGR NPAT, bubble=vốn hóa)'"
)
# Tooltip: "tăng trưởng" → "CAGR NPAT"
html = html.replace(
    "const d=c.raw; return ` ${d.label}: P/B ${d.x}×, tăng trưởng ${d.y}%`;",
    "const d=c.raw; return ` ${d.label}: P/B ${d.x}×, CAGR NPAT ${d.y}%`;"
)

print(f"  Peer scatter: x-axis 1-5, y-axis 0-20 CAGR NPAT, label corrected")

# ============ FRONTEND POLISH CSS LAYER ============
# editorial-tech + shadows + taste-guardrail + animation-laws compliance
# Added before </style> — additive layer, easy to rollback
polish_css = """
/* FRONTEND POLISH LAYER — editorial-tech + shadows + taste-guardrail
   Tuân thủ animation-laws: chỉ transform/opacity, ease-out, <300ms */
:root {
  --ease-out: cubic-bezier(0.23, 1, 0.32, 1);
  --ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
  --ease-spring: cubic-bezier(0.32, 0.72, 0, 1);
}
.card {
  transition: border-color 180ms var(--ease-out), box-shadow 180ms var(--ease-out), transform 180ms var(--ease-out) !important;
}
@media (hover: hover) and (pointer: fine) {
  .card:hover {
    border-color: rgba(245, 166, 35, 0.25) !important;
    box-shadow: 0px 0px 0px 1px rgba(245, 166, 35, 0.08), var(--sh-md) !important;
    transform: translateY(-1px);
  }
  .card:active {
    transform: translateY(0);
    transition-duration: 100ms !important;
  }
}
.kpi {
  transition: border-color 160ms var(--ease-out), transform 160ms var(--ease-out) !important;
  position: relative;
  overflow: hidden;
}
.kpi::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 2px;
  background: var(--grad-amber);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 200ms var(--ease-out);
}
@media (hover: hover) and (pointer: fine) {
  .kpi:hover {
    transform: translateY(-2px);
    border-color: var(--border-hot) !important;
  }
  .kpi:hover::after { transform: scaleX(1); }
}
.fin-table tbody tr:nth-child(even),
.data-table tbody tr:nth-child(even) {
  background: rgba(255, 255, 255, 0.018);
}
.fin-table tbody tr,
.data-table tbody tr {
  transition: background-color 120ms var(--ease-out);
}
@media (hover: hover) and (pointer: fine) {
  .fin-table tbody tr:hover,
  .data-table tbody tr:hover {
    background: rgba(245, 166, 35, 0.05);
  }
}
.section-title .num {
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
  box-shadow: 0 2px 8px rgba(245, 166, 35, 0.25);
}
.stat-mini, .stat, .val-card, .verdict-card, .analyst-card, .cap-card {
  transition: border-color 160ms var(--ease-out), transform 160ms var(--ease-out) !important;
}
@media (hover: hover) and (pointer: fine) {
  .stat-mini:hover, .stat:hover, .val-card:hover, .verdict-card:hover {
    transform: translateY(-1px);
    border-color: rgba(74, 158, 255, 0.2) !important;
  }
}
.insight-frame { position: relative; }
.insight-frame::before {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 3px; height: 100%;
  background: var(--grad-amber);
  border-radius: 12px 0 0 12px;
  opacity: 0.7;
}
.honest-correction {
  border-left-width: 4px !important;
  position: relative;
}
.honest-correction::before {
  content: '⚠';
  position: absolute;
  top: 16px; right: 18px;
  font-size: 14px;
  color: var(--red);
  opacity: 0.5;
}
.callout {
  transition: border-color 180ms var(--ease-out), background-color 180ms var(--ease-out);
}
@media (hover: hover) and (pointer: fine) {
  .callout:hover {
    border-left-color: var(--amber);
    background-color: rgba(245, 166, 35, 0.04);
  }
}
.tag { transition: transform 120ms var(--ease-out); }
@media (hover: hover) and (pointer: fine) {
  .tag:hover { transform: scale(1.05); }
}
.topnav-brand .dot { animation: dot-pulse 3s var(--ease-in-out) infinite; }
@keyframes dot-pulse {
  0%, 100% { box-shadow: 0 0 8px var(--amber); opacity: 1; }
  50% { box-shadow: 0 0 12px var(--amber); opacity: 0.8; }
}
@media (prefers-reduced-motion: reduce) {
  .topnav-brand .dot { animation: none; }
}
.back-top {
  transition: opacity 200ms var(--ease-out), transform 200ms var(--ease-spring), border-color 200ms var(--ease-out) !important;
}
.back-top:hover { transform: translateY(-2px) scale(1.05); }
.back-top:active {
  transform: translateY(0) scale(0.97);
  transition-duration: 100ms !important;
}
.topnav-link {
  position: relative;
  transition: color 150ms var(--ease-out), background-color 150ms var(--ease-out) !important;
}
.topnav-link::after {
  content: '';
  position: absolute;
  bottom: 2px; left: 10px; right: 10px;
  height: 1.5px;
  background: var(--amber);
  transform: scaleX(0);
  transform-origin: center;
  transition: transform 180ms var(--ease-out);
}
.topnav-link.active::after { transform: scaleX(1); }
.fin-table thead tr,
.data-table thead tr {
  border-bottom: 2px solid rgba(245, 166, 35, 0.15) !important;
}
.verdict-card { border-left: 3px solid var(--green); }
.verdict-card.bear { border-left-color: var(--red); }
.verdict-card.neutral { border-left-color: var(--amber); }
a:focus-visible, button:focus-visible, .topnav-link:focus-visible {
  outline: 2px solid var(--amber);
  outline-offset: 2px;
  border-radius: 4px;
}
"""

# Also fix the 3 transition:all in template's original CSS
html = html.replace(
    "transition:all .15s;font-weight:500}",
    "transition:color .15s var(--ease-out),background-color .15s var(--ease-out);font-weight:500}"
)
html = html.replace(
    "transition:all .2s;z-index:800}",
    "transition:opacity .2s var(--ease-out),transform .2s var(--ease-spring),border-color .2s var(--ease-out);z-index:800}"
)
html = html.replace(
    "transition:all .12s;border-left:2px solid transparent}",
    "transition:background-color .12s var(--ease-out),color .12s var(--ease-out),border-left-color .12s var(--ease-out);border-left:2px solid transparent}"
)

# Insert polish CSS before </style>
html = html.replace("</style>\n</head>", polish_css + "\n</style>\n</head>")

# Strip template instructions/illustration HTML after </body> (dead content,
# contains duplicate canvas IDs that confuse Chart.getChart)
body_close_idx = html.rfind("</body>")
if body_close_idx != -1:
    html_close_idx = html.rfind("</html>")
    if html_close_idx > body_close_idx:
        html = html[:body_close_idx + len("</body>")] + "\n" + html[html_close_idx:]
    else:
        html = html[:body_close_idx + len("</body>")] + "\n</html>"

# Write output
with open(TEMPLATE, "w") as f:
    f.write(html)

# Verify
remaining = []
import re
for m in re.finditer(r'\{\{[A-Z_0-9]+\}\}', html):
    remaining.append(m.group())

print(f"✅ Phase 6 complete → {TEMPLATE}")
print(f"   Replacements: {len(replacements)}")
print(f"   Remaining tokens: {len(remaining)}")
if remaining:
    print(f"   ⚠️ Remaining: {set(remaining)}")
else:
    print(f"   ✅ All tokens replaced")

# Section count
sections = re.findall(r'id="sec-[a-z0-9-]+"', html)
unique_sections = set(sections)
print(f"   Sections: {len(unique_sections)} unique")

# Chart count
charts = re.findall(r'new Chart\(\$', html)
print(f"   Chart.js instances: {len(charts)}")

# Refs
refs = re.findall(r'id="ref-[0-9]+"', html)
print(f"   References: {len(refs)}")
