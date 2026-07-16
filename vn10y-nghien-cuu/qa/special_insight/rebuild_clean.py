#!/usr/bin/env python3
"""Rebuild index.html cleanly from pre_editorial_expansion base.
Applies in one pass: rebalance framing + 3-tier SI section + chart JS + minimap link.
Avoids the corruption caused by incremental edits."""
import json, re
from pathlib import Path

BASE = Path("/Users/bobo/ZCodeProject/vn10y-nghien-cuu")
OUT = BASE / "index.html"
D = json.loads((BASE / "qa/special_insight/special_insight_chart_data.json").read_text())

html = (BASE / "index.html.pre_editorial_expansion").read_text()

# === 1. REBALANCE FRAMING (hotspots) ===
# 1a. Hero line
html = html.replace(
    "lợi suất trái phiếu phù hợp để <em>đọc bối cảnh tài chính cùng thời điểm</em>, không phải để <em>dự báo tương lai</em>.",
    "lợi suất trái phiếu <strong>có giá trị đọc bối cảnh tài chính cùng thời điểm</strong> — khi nó biến động mạnh, cổ phiếu thường yếu trong cùng cửa sổ — nhưng <strong>chưa cho thấy khả năng dự báo ổn định</strong>. Coi nó là vô ích hay coi nó là quả cầu pha lê đều sai cả hai."
)

# 1b. quickread "đi cùng" — fix "8 chỉ số" to "7 chỉ số headline"
html = html.replace(
    "Có, nhưng giới hạn. Chương 2 tìm thấy hai quan hệ đồng thời vượt hiệu chỉnh: biến động lợi suất 2 năm trong 5 phiên đi cùng 8 chỉ số cổ phiếu yếu hơn",
    "Có — đây là phát hiện tích cực quan trọng nhất của nghiên cứu. Chương 2 tìm thấy hai quan hệ đồng thời vượt hiệu chỉnh: biến động lợi suất 2 năm trong 5 phiên đi cùng 7 chỉ số cổ phiếu headline yếu hơn"
)

# === 2. INSERT 3-TIER SI SECTION before <section id="ch1"> ===
t = D["timeline"]; f = D["forest"]
md = D["multi_index_daily"]; mm = D["multi_index_monthly"]; br = D["breadth"]; ftl = br["f1_timeline"]

SECTION = '''
<section id="special-insight">
  <h2 class="section-title"><span class="num">★</span>Special Insight — Bond không đi trước, nhưng không vô ích</h2>

  <div class="callout good"><h4>Câu trả lời ngắn</h4><p>Bond không cho thấy khả năng đi trước thị trường, nhưng cũng không vô ích. Trong một số cửa sổ cùng kỳ, lợi suất tăng đi cùng return cổ phiếu thấp hơn — một liên hệ bối cảnh đã vượt gate trên nhiều chỉ số, chưa phải công cụ dự báo.</p></div>

  <h3>Nói dễ hiểu</h3>
  <p>Phần lớn báo cáo trả lời "không" cho câu hỏi dự báo. Nhưng giữa các kết quả âm tính có một phát hiện dương tính quan trọng: trong cùng cửa sổ thời gian, khi lợi suất trái phiếu tăng, return cổ phiếu thường thấp hơn. Quan trọng là phát hiện này <strong>không giới hạn ở VNINDEX</strong> — nó nhất quán trên 7 chỉ số daily; monthly có 2 chỉ số và một kết quả panel tổng hợp, và có cả một liên hệ với độ rộng thị trường (breadth). Section này đặt toàn bộ bằng chứng đó lên đúng trọng lượng, chia ba tầng rõ ràng: return chỉ số, độ rộng thị trường, và các nhánh không được hỗ trợ.</p>

  <h3>Tầng 1 — Return chỉ số cổ phiếu</h3>
  <p>Đây là tầng bằng chứng mạnh nhất. Hai cửa sổ thời gian đều cho thấy quan hệ cùng kỳ âm, vượt Holm trên nhiều chỉ số.</p>

  <h4>Daily: Δ2Y → return 5 phiên (7 chỉ số)</h4>
  <p>7 chỉ số có kết quả headline: VNINDEX, VN30, VNCOND, VNCONS, VNFIN, VNHEAL, VNIT. Tất cả đều âm, từ −0,17 đến −0,33 điểm % cho mỗi +10bps lợi suất 2Y trong cùng 5 phiên.</p>
  <div class="chart-box">
    <h4>β theo chỉ số (daily, điểm % return / +10bps 2Y)</h4>
    <div class="desc">7 chỉ số headline significant. Tất cả âm — quan hệ nhất quán, không cô lập ở VNINDEX. Lưu ý: thành phần chỉ số có thể chồng lấn, không độc lập.</div>
    <div class="chart-wrap"><canvas id="chartSiMultiDaily"></canvas></div>
  </div>

  <h4>Monthly: Δ10Y → return tháng (2 chỉ số + 1 panel)</h4>
  <p>2 chỉ số vượt Holm: VNINDEX, VNMAT. Ngoài ra <strong>PANEL_CORE</strong> — kết quả panel tổng hợp, không phải chỉ số — cũng vượt (p=0,015), nhưng <em>headline_allowed=False</em> vì là aggregate. Nhiều chỉ số khác cùng dấu âm nhưng không vượt ngưỡng. Biên độ lớn hơn daily: từ −0,71 đến −1,29 điểm % cho mỗi +10bps lợi suất 10Y trong cùng tháng.</p>
  <div class="chart-box">
    <h4>β theo chỉ số (monthly, điểm % return / +10bps 10Y)</h4>
    <div class="desc">2 chỉ số (xanh tím) + 1 kết quả panel tổng hợp (xám — không phải chỉ số, headline_allowed=False). β monthly lớn hơn daily nhưng n nhỏ hơn (144 tháng), khoảng tin cậy rộng hơn.</div>
    <div class="chart-wrap"><canvas id="chartSiMultiMonthly"></canvas></div>
  </div>

  <p><strong>VNINDEX làm ví dụ diễn giải chính</strong> (không phải toàn bộ bằng chứng): mỗi +10bps lợi suất 2Y trong 5 phiên đi cùng return VNINDEX thấp hơn khoảng −0,24 điểm % (CI 95% [−0,36; −0,13]); mỗi +10bps lợi suất 10Y trong 1 tháng đi cùng return thấp hơn khoảng −0,71 điểm % (CI [−1,18; −0,24]). Đây là CI của <em>liên hệ cùng kỳ</em>, không phải khoảng dự báo.</p>

  <div class="chart-box">
    <h4>Forest plot VNINDEX — quy mô hai effect với CI</h4>
    <div class="desc">Điểm + whisker CI 95% của liên hệ cùng kỳ. KHÔNG phải khoảng dự báo cho kỳ tiếp theo.</div>
    <div class="chart-wrap"><canvas id="chartSiForest"></canvas></div>
  </div>

  <h3>Tầng 2 — Độ rộng thị trường (breadth)</h3>
  <p>Tầng này dùng design/sample khác (net_advance_share, n=119 tháng), nên tách riêng. Chương 4 tìm thấy 2 liên hệ breadth monthly vượt Holm:</p>
  <div class="kpi-grid">
    <div class="kpi"><div class="val">F1</div><div class="lab">Δ2Y → net_advance_share, Holm p=0,0415, β≈−0,0007 cho 25bps</div></div>
    <div class="kpi"><div class="val">F5</div><div class="lab">Δ chênh lệch VN–US 2Y → net_advance_share, Holm p=0,0282, β≈−0,0007 cho 25bps</div></div>
  </div>
  <p>Hiệu ứng rất nhỏ: khoảng −0,07 điểm % breadth cho +25bps. Khi lợi suất 2Y tăng, tỷ lệ cổ phiếu tiến (net advance share) trong cùng tháng hơi thấp hơn. Đây là liên hệ <strong>cùng tháng</strong>, không dự báo.</p>
  <div class="chart-box">
    <h4>F1 song hành: Δ2Y vs net_advance_share theo tháng</h4>
    <div class="desc">Panel trên: Δ2Y monthly (bps). Panel dưới: net_advance_share (%) cùng tháng. Hai panel dùng trục riêng để bạn tự đối chiếu. <strong>120 tháng quan sát trên chart, 119 tháng trong regression F1</strong> (chênh 1 do complete-case controls). Breadth là design khác — không so sánh trực tiếp với tầng return.</div>
    <div class="chart-wrap" style="height:180px"><canvas id="chartSiBreadthD2Y"></canvas></div>
  </div>
  <div class="chart-box">
    <h4>net_advance_share (%) — panel dưới</h4>
    <div class="desc">Tỷ lệ cổ phiếu tiến ròng, cùng tháng với panel trên.</div>
    <div class="chart-wrap" style="height:180px"><canvas id="chartSiBreadthNAS"></canvas></div>
  </div>

  <h3>Tầng 3 — Các nhánh KHÔNG được hỗ trợ</h3>
  <p>Để tránh đọc quá rộng, đây là những gì <strong>không</strong> vượt gate:</p>
  <ul class="bul">
    <li><strong>Độ sâu/thanh khoản:</strong> không có liên hệ đáng tin sau khi kiểm soát các biến equity (VNINDEX return trễ, VNINDEX volatility 20 phiên trễ, regime MA200 trễ).</li>
    <li><strong>Cơ hội +10/−5:</strong> không có liên hệ đáng tin.</li>
    <li><strong>Khối lượng giao dịch (Ch3):</strong> đồng thời panel-parent 0/15, short-lag panel-parent 0/15, bond→volume Granger 0/150, OOS stable 0/15. (807 là tổng matrix bao gồm confirmatory + exploratory + sensitivity + blocked, không dùng làm mẫu số confirmatory.)</li>
  </ul>
  <p>Không suy diễn quan hệ breadth sang depth, liquidity hay opportunity — các nhánh đó null.</p>

  <h3>Evidence boundary — Granger và OOS</h3>
  <p>Để liên hệ cùng kỳ không bị đọc nhầm thành dự báo, đây là kết quả kiểm tra chiều thời gian và ngoài mẫu, nằm thẳng trong phần chính:</p>
  <div class="kpi-grid">
    <div class="kpi red"><div class="val">0/150</div><div class="lab">Granger bond→equity daily vượt Holm</div></div>
    <div class="kpi red"><div class="val">0/150</div><div class="lab">Granger bond→equity monthly vượt Holm</div></div>
    <div class="kpi red"><div class="val">0/140</div><div class="lab">OOS stable (trong 140 đánh giá được; 35 insufficient depth)</div></div>
  </div>
  <p>Chiều bond→equity: <strong>0/150 daily và 0/150 monthly</strong> vượt Holm — không có bằng chứng lợi suất trái phiếu đi trước cổ phiếu ở bất kỳ tần suất nào. <em>Chiều equity→bond chưa được kiểm định trong Chương 2</em> (scope gap, không kết luận null). OOS: 0/140 mô hình đủ depth đạt stable; 56 mixed (improved-fraction median ≈ 0,517, gần tung đồng xu — chỉ diagnostic, không phải kiểm định chính thức); 84 failed; 35 insufficient depth.</p>
  <p>Quan trọng: OOS null <strong>không</strong> là bằng chứng "không thể dự báo" — nó chỉ nói "chưa tìm thấy khả năng dự báo ổn định trong các thiết kế đã kiểm định". Không dùng OOS như bằng chứng H0 đúng.</p>

  <h3>Cách hiểu hợp lệ</h3>
  <p>Cách diễn giải đứng vững nhất: <strong>hai thị trường có thể cùng phản ánh những thay đổi vĩ mô hoặc tài chính chưa được nghiên cứu này cô lập</strong>. Khi có biến động lớn ở môi trường chung, cả trái phiếu và cổ phiếu (và độ rộng thị trường) cùng phản ứng trong cùng khoảng thời gian. Đây là cách đọc "common driver" — một yếu tố thứ ba có thể đẩy cả hai — nhưng yếu tố đó chưa được kiểm định trực tiếp.</p>
  <div class="callout warn"><h4>Phải ghi rõ những gì chưa chứng minh</h4>
  <p>Common driver chưa được kiểm định trực tiếp. Không chứng minh quan hệ nhân quả. Không chứng minh bond đi trước. Không chứng minh bond cải thiện quyết định đầu tư ngoài mẫu. Không suy diễn breadth sang depth/liquidity/opportunity.</p></div>

  <h3>Giả thuyết cần theo dõi trong tương lai</h3>
  <div class="callout warn"><h4>Câu hỏi mở, không phải kỳ vọng</h4><p>Liệu quan hệ đồng thời này có phát triển thành thông tin dẫn trước khi dữ liệu dài hơn hay không vẫn là một câu hỏi mở. Điều đó chỉ được chấp nhận nếu xuất hiện precedence, ổn định thời gian và cải thiện OOS trên dữ liệu tương lai.</p></div>
  <p>Điều kiện để xem xét nâng thành predictive research (tất cả phải đạt, không chỉ một):</p>
  <ol class="bul">
    <li>F1 vượt kiểm tra Monte Carlo sâu hơn (hiện cận ngưỡng).</li>
    <li>Beta ổn định qua interaction thời gian được đăng ký trước (không hậu nghiệm).</li>
    <li>Bond→equity precedence vượt hiệu chỉnh đa phép thử.</li>
    <li>OOS cải thiện vật chất và ổn định (không chỉ coin-flip).</li>
    <li>Kết quả lặp lại trên dữ liệu tương lai chưa dùng khi xây mô hình.</li>
  </ol>
  <p>Nhiều dữ liệu hơn chỉ tăng precision; không tự biến contemporaneous association thành prediction. Hiện tại, đây là liên hệ bối cảnh đã vượt gate — không hơn, không kém.</p>
</section>

'''
html = html.replace('<section id="ch1">', SECTION + '<section id="ch1">', 1)

# === 3. ADD MINIMAP LINK for special-insight ===
mm_old = '''      <li><a href="#open"><span class="dot"></span>1 — Tổng quan</a></li>
    </ul>'''
mm_new = '''      <li><a href="#open"><span class="dot"></span>1 — Tổng quan</a></li>
      <li><a href="#special-insight"><span class="dot" style="background:#22c55e"></span>★ Insight chính — Bond không đi trước, nhưng không vô ích</a></li>
    </ul>'''
if mm_old in html:
    html = html.replace(mm_old, mm_new, 1)
    html = html.replace('Mở đầu <span class="gcount">1</span>', 'Mở đầu <span class="gcount">2</span>', 1)
else:
    # Fallback: anchor-based insertion after the #open link line
    import re as _re
    html = _re.sub(
        r'(<li><a href="#open"[^<]*</a></li>)',
        r'\1\n      <li><a href="#special-insight"><span class="dot" style="background:#22c55e"></span>★ Insight chính — Bond không đi trước, nhưng không vô ích</a></li>',
        html, count=1)
    html = html.replace('Mở đầu <span class="gcount">1</span>', 'Mở đầu <span class="gcount">2</span>', 1)
# Hard assert: nav link MUST exist after this block
assert 'href="#special-insight"' in html, "NAV GATE FAILED: special-insight link missing after build"

# === 4. INSERT CHART JS before closing </script> of chart block ===
CHART_JS = '''
// Special Insight — Forest plot VNINDEX with CI whiskers
new Chart(document.getElementById('chartSiForest'),{type:'bar',
  data:{labels:['+10bps 2Y (5 phiên)\\n→ VNINDEX cùng 5 phiên','+10bps 10Y (1 tháng)\\n→ VNINDEX cùng tháng'],
  datasets:[{label:'point',data:[''' + str(f["daily"]["point_pct_per_10bps"]) + ''',''' + str(f["monthly"]["point_pct_per_10bps"]) + '''],
    backgroundColor:['rgba(245,158,11,.2)','rgba(139,92,246,.2)'],borderColor:['rgba(245,158,11,.35)','rgba(139,92,246,.35)'],borderWidth:1,barPercentage:0.3,categoryPercentage:0.6}]},
  options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
    plugins:{legend:{display:false}},
    scales:{x:{title:{display:true,text:'Điểm % return / +10bps (cùng kỳ)',color:TXT},grid:{color:GRID},ticks:{font:{size:9}},min:-1.3,max:0.1},
      y:{grid:{display:false},ticks:{font:{size:10}}}}},
  plugins:[{id:'siWhiskers',afterDatasetsDraw:function(chart){
    var ctx=chart.ctx,meta=chart.getDatasetMeta(0),xs=chart.scales.x;
    var data=[{lo:''' + str(f["daily"]["ci_low_pct_per_10bps"]) + ''',hi:''' + str(f["daily"]["ci_high_pct_per_10bps"]) + ''',pt:''' + str(f["daily"]["point_pct_per_10bps"]) + ''',c:'245,158,11'},{lo:''' + str(f["monthly"]["ci_low_pct_per_10bps"]) + ''',hi:''' + str(f["monthly"]["ci_high_pct_per_10bps"]) + ''',pt:''' + str(f["monthly"]["point_pct_per_10bps"]) + ''',c:'139,92,246'}];
    ctx.save();data.forEach(function(r,idx){var y=meta.data[idx].y,xLo=xs.getPixelForValue(r.lo),xHi=xs.getPixelForValue(r.hi),xPt=xs.getPixelForValue(r.pt);
      ctx.strokeStyle='rgba('+r.c+',.9)';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(xLo,y);ctx.lineTo(xHi,y);ctx.stroke();
      ctx.beginPath();ctx.moveTo(xLo,y-6);ctx.lineTo(xLo,y+6);ctx.moveTo(xHi,y-6);ctx.lineTo(xHi,y+6);ctx.stroke();
      ctx.fillStyle='rgba('+r.c+',1)';ctx.beginPath();ctx.arc(xPt,y,4,0,Math.PI*2);ctx.fill();});
    var x0=xs.getPixelForValue(0);ctx.strokeStyle='rgba(148,163,184,.4)';ctx.lineWidth=1;ctx.setLineDash([4,4]);
    ctx.beginPath();ctx.moveTo(x0,chart.chartArea.top);ctx.lineTo(x0,chart.chartArea.bottom);ctx.stroke();ctx.setLineDash([]);ctx.restore();}}]});

// Special Insight — Multi-index daily bar (7 indices)
new Chart(document.getElementById('chartSiMultiDaily'),{type:'bar',
  data:{labels:''' + json.dumps(md["indices"]) + ''',
  datasets:[{label:'β/10bps (%)',data:''' + json.dumps(md["beta_pct_per_10bps"]) + ''',
    backgroundColor:'rgba(245,158,11,.7)',borderRadius:4,maxBarThickness:50}]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},
    tooltip:{callbacks:{label:function(c){return c.parsed.y.toFixed(2)+' điểm % / +10bps (Holm p<0.05)';}}}},
    scales:{y:{title:{display:true,text:'β (điểm % return / +10bps 2Y)',color:TXT},grid:{color:GRID},ticks:{font:{size:9}}},
      x:{grid:{display:false},ticks:{font:{size:9}}}}}});

// Special Insight — Multi-index monthly bar (3 indices)
new Chart(document.getElementById('chartSiMultiMonthly'),{type:'bar',
  data:{labels:''' + json.dumps([i+' (panel)' if i=='PANEL_CORE' else i for i in mm["indices"]]) + ''',
  datasets:[{label:'β/10bps (%)',data:''' + json.dumps(mm["beta_pct_per_10bps"]) + ''',
    backgroundColor:''' + json.dumps(['rgba(148,163,184,.5)' if i=='PANEL_CORE' else 'rgba(139,92,246,.7)' for i in mm["indices"]]) + ''',borderRadius:4,maxBarThickness:50}]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},
    tooltip:{callbacks:{label:function(c){var lbl=c.label.includes('panel')?' (kết quả panel tổng hợp, không phải chỉ số, headline_allowed=False)':' (Holm p<0.05)';return c.parsed.y.toFixed(2)+' điểm % / +10bps'+lbl;}}}},
    scales:{y:{title:{display:true,text:'β (điểm % return / +10bps 10Y)',color:TXT},grid:{color:GRID},ticks:{font:{size:9}}},
      x:{grid:{display:false},ticks:{font:{size:9}}}}}});

// Special Insight — Breadth F1 timeline
var SI_B_LABELS=''' + json.dumps(ftl["labels"]) + ''';
var SI_B_D2Y=''' + json.dumps(ftl["d2y_bps"]) + ''';
var SI_B_NAS=''' + json.dumps(ftl["net_advance_share"]) + ''';
new Chart(document.getElementById('chartSiBreadthD2Y'),{type:'bar',
  data:{labels:SI_B_LABELS,
  datasets:[{label:'Δ2Y (bps)',data:SI_B_D2Y,
    backgroundColor:function(c){var v=c.parsed.y;return v>=0?'rgba(245,158,11,.7)':'rgba(59,130,246,.7)';},borderRadius:2,maxBarThickness:6}]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},
    tooltip:{callbacks:{title:function(c){return SI_B_LABELS[c[0].dataIndex];},label:function(c){var i=c.dataIndex;return 'Δ2Y='+c.parsed.y.toFixed(1)+'bps (breadth '+SI_B_NAS[i].toFixed(2)+'%)';}}}},
    scales:{y:{title:{display:true,text:'Δ2Y (bps)',color:TXT},grid:{color:GRID},ticks:{font:{size:9}}},x:{grid:{display:false},ticks:{font:{size:7},maxRotation:0,maxTicksLimit:10}}}}});

new Chart(document.getElementById('chartSiBreadthNAS'),{type:'bar',
  data:{labels:SI_B_LABELS,
  datasets:[{label:'net_advance_share (%)',data:SI_B_NAS,
    backgroundColor:function(c){var v=c.parsed.y;return v>=0?'rgba(34,197,94,.6)':'rgba(239,68,68,.6)';},borderRadius:2,maxBarThickness:6}]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},
    tooltip:{callbacks:{title:function(c){return SI_B_LABELS[c[0].dataIndex];},label:function(c){var i=c.dataIndex;return 'breadth='+c.parsed.y.toFixed(2)+'% (Δ2Y '+SI_B_D2Y[i].toFixed(1)+'bps)';}}}},
    scales:{y:{title:{display:true,text:'net_advance_share (%)',color:TXT},grid:{color:GRID},ticks:{font:{size:9}}},x:{grid:{display:false},ticks:{font:{size:7},maxRotation:0,maxTicksLimit:10}}}}});
'''
# Insert before the closing of chart script block
# Find the chart block's closing </script> — it's right before "<!-- SCRIPT: NAVIGATION -->"
nav_marker = "<!-- SCRIPT: NAVIGATION -->"
nav_idx = html.index(nav_marker)
# Find the </script> just before nav_marker
close_script = html.rindex("</script>", 0, nav_idx)
html = html[:close_script] + CHART_JS + "\n" + html[close_script:]

# === 5. PATCH legacy chartMonthlyBeta: annotate PANEL_CORE as panel (not an index) ===
html = html.replace(
    "data:{labels:['PANEL_CORE','VNMAT','VNINDEX'],\n  datasets:[{label:'β/10bps',data:[-0.884,-1.288,-0.707],\n    backgroundColor:'rgba(139,92,246,.6)'",
    "data:{labels:['PANEL_CORE (panel)','VNMAT','VNINDEX'],\n  datasets:[{label:'β/10bps',data:[-0.884,-1.288,-0.707],\n    backgroundColor:['rgba(148,163,184,.5)','rgba(139,92,246,.6)','rgba(139,92,246,.6)']"
)

OUT.write_text(html)
print(f"Rebuilt index.html cleanly: {len(html)} bytes")
print(f"canvases: {html.count('<canvas')} | SI canvases: {len(re.findall(r'canvas id=\"chartSi', html))}")
print(f"tiers: T1={html.count('Tầng 1')} T2={html.count('Tầng 2')} T3={html.count('Tầng 3')}")
print(f"nav elements: progressBar={html.count('id=\"progressBar\"')} minimap={html.count('id=\"minimap\"')} toTop={html.count('id=\"toTop\"')}")
