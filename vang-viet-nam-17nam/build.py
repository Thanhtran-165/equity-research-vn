#!/usr/bin/env python3
"""Build 'Vàng Việt Nam 2009-2026' longform — full 18 chapters + 10 charts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL = Path.home() / ".zcode/skills/longform"
TPL = SKILL / "assets/article_template.html"
CHART_DATA = ROOT.parent / "sjc-gold-history/data/processed/analytics/chart_data.json"

tpl = TPL.read_text()
HEAD = tpl.split("<body>")[0] + "<body>"
# tail = from <footer> to end
tail_full = tpl.split("<footer>", 1)[1]

# Extract viz.js core (the IIFE registry) — needed before chart calls
import re as _re
_viz_match = _re.search(
    r"(/\* =+\n\s*VIZ\.JS.*?global\.viz = viz;\s*\}\)\(typeof window[^;]+;\s*)",
    tpl, _re.S
)
VIZ_CORE = _viz_match.group(1) if _viz_match else ""

# tail_nav = slate palette defaults (drop the sample chartCompare block)
tail_nav = ("/* Slate palette overrides cho registry (registry đọc --chart-* tokens; longform dùng slate). */\n"
            "Chart.defaults.color = '#94a3b8';\n"
            "Chart.defaults.font.family = '-apple-system, Segoe UI, Roboto, sans-serif';\n"
            "Chart.defaults.borderColor = '#334155';\n")
# Actually tail_nav ends mid: after Chart.defaults.borderColor line. Re-add.
# Recompute cleanly: tail_nav = everything from slate defaults through the borderColor line, then </script>
slate_block_end = "Chart.defaults.borderColor = '#334155';"
tail_nav = ("/* Slate palette overrides cho registry (registry đọc --chart-* tokens; longform dùng slate). */\n"
            + slate_block_end + "\n\n")

charts = json.loads(CHART_DATA.read_text())

C = {
    "amber": "rgba(245,158,11,.85)", "amber_fill": "rgba(245,158,11,.15)",
    "red": "rgba(239,68,68,.85)", "red_fill": "rgba(239,68,68,.2)",
    "green": "rgba(34,197,94,.85)", "green_fill": "rgba(34,197,94,.2)",
    "cyan": "rgba(34,211,238,.85)", "cyan_fill": "rgba(34,211,238,.15)",
    "violet": "rgba(167,139,250,.85)", "violet_fill": "rgba(167,139,250,.15)",
    "grid": "#334155",
}

def cj(cid, spec):
    pal = [C["amber"], C["cyan"], C["violet"], C["green"], C["red"]]
    ds = []
    for i, d in enumerate(spec["datasets"]):
        col = pal[i % len(pal)]
        dt = d.get("type", "bar")
        lab = json.dumps(d["label"], ensure_ascii=False)
        data = json.dumps(d["data"])
        if dt == "line":
            ds.append("{label:%s,type:'line',data:%s,borderColor:'%s',backgroundColor:'%s',tension:.3,pointRadius:2,fill:false,borderWidth:2}" % (lab, data, col, col.replace('.85', '.15')))
        else:
            ds.append("{label:%s,type:'bar',data:%s,backgroundColor:'%s',borderRadius:3}" % (lab, data, col.replace('.85', '.7')))
    labels = json.dumps([str(x) for x in spec["labels"]])
    # Build via plain string formatting (no f-string brace escaping)
    L = []
    L.append("viz.chart('%s', {" % cid)
    L.append("  type:'bar',")
    L.append("  data:{labels:%s,datasets:[%s]}," % (labels, ",".join(ds)))
    L.append("  options:{")
    L.append("    responsive:true, maintainAspectRatio:false,")
    L.append("    plugins:{")
    L.append("      legend:{position:'top',labels:{usePointStyle:true,boxWidth:8,font:{size:11}}},")
    L.append("      tooltip:{callbacks:{label:function(c){return c.dataset.label+': '+c.parsed.y;}}}")
    L.append("    },")
    L.append("    scales:{")
    L.append("      x:{grid:{display:false},ticks:{font:{size:10},maxRotation:60,autoSkip:true,maxTicksLimit:14}},")
    L.append("      y:{grid:{color:'%s'},ticks:{font:{size:10}}}" % C['grid'])
    L.append("    }")
    L.append("  }")
    L.append("});")
    return "\n".join(L)

CHARTS_JS = "\n\n".join(cj(k, v) for k, v in charts.items())

# CSS for collapsible appendix (phụ lục kỹ thuật — ẩn mặc định)
APPENDIX_CSS = """
<style>
details.appendix{background:rgba(30,41,59,.4);border:1px solid rgba(148,163,184,.15);border-radius:8px;padding:0 16px;margin:16px 0}
details.appendix>summary{cursor:pointer;padding:14px 0;font-size:1.02rem;color:#fbbf24;list-style:none;display:flex;align-items:center;gap:8px}
details.appendix>summary::before{content:'▶';font-size:.7rem;transition:transform .2s;color:#94a3b8}
details.appendix[open]>summary::before{transform:rotate(90deg)}
details.appendix>summary::-webkit-details-marker{display:none}
details.appendix[open]{background:rgba(30,41,59,.6)}
details.appendix .tbl{margin:8px 0 16px}
details.appendix p{color:#cbd5e1;font-size:.92rem}
</style>
"""

# ===================== CONTENT =====================
def KPI(*items):
    cells = "\n".join(f'      <div class="kpi {c}"><div class="val">{v}</div><div class="lab">{l}</div></div>' for v, l, c in items)
    return f'    <div class="kpi-grid">\n{cells}\n    </div>'
def CH(cid, title, desc=""):
    return f'    <div class="chart-box"><h4>{title}</h4><div class="desc">{desc}</div><div class="chart-wrap"><canvas id="{cid}"></canvas></div></div>'
def CO(kind, title, body):
    return f'    <div class="callout {kind}"><h4>{title}</h4><p>{body}</p></div>'
def TBL(headers, rows):
    h = "".join(f"<th>{x}</th>" for x in headers)
    body = "\n".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'    <table class="tbl"><thead><tr>{h}</tr></thead><tbody>\n{body}\n    </tbody></table>'
def CMP(lt, li, rt, ri, ltag="", rtag=""):
    l = "".join(f"<li>{x}</li>" for x in li); r = "".join(f"<li>{x}</li>" for x in ri)
    return f'    <div class="compare"><div class="col before"><h4>{lt} <span class="tag">{ltag}</span></h4><ul class="bul">{l}</ul></div><div class="col after"><h4>{rt} <span class="tag">{rtag}</span></h4><ul class="bul">{r}</ul></div></div>'
def TL(*items):
    rows = "\n".join(f'      <div class="tl-item {c}"><div class="tl-year">{y}</div><div class="tl-body">{b}</div></div>' for y, b, c in items)
    return f'    <div class="timeline">\n{rows}\n    </div>'

SECTIONS = []

# ===== CH 1 =====
SECTIONS.append(f'''  <section id="chuong-1">
    <h2 class="section-title"><span class="num">I</span>Vàng Việt Nam &ldquo;đắt nhất thế giới&rdquo; &mdash; mythology hay số liệu?</h2>
    <p>Một câu nói phổ biến trong giới đầu tư Việt Nam: <em>&ldquo;Vàng SJC luôn đắt nhất thế giới.&rdquo;</em> Câu nói này đúng &mdash; nhưng đến mức nào, và trong suốt 17 năm qua thì <strong>pattern đó có ổn định không</strong>? Bài này dùng <strong>27.921 điểm dữ liệu giá SJC</strong> từ chính chủ sjc.com.vn, ghép với giá vàng thế giới (COMEX GC=F) và tỷ giá USD/VND, để đo chính xác khoảng cách đó trong từng ngày từ 22/07/2009 đến 08/07/2026.</p>
{KPI(("+31,2%","Premium SJC vs QT, đỉnh 2022","red"),("+0,5%","Premium 2019 — gần hòa QT","green"),("191,3M","Đỉnh giá SJC 29/01/2026 (triệu/lượng)","amber"),("~7×","Vàng SJC tăng 2009→2026","violet"))}
    <p>Câu trả lời ngắn: <strong>SJC đắt hơn vàng thế giới trong gần như toàn bộ 17 năm</strong>, nhưng mức độ chênh lệch biến động dữ dội &mdash; từ <em>gần như hòa hoàn toàn</em> (2019, premium chỉ +0,5%) đến <em>đỉnh +31,2%</em> (2022, hậu COVID).<sup class="ref">1</sup> Đây không phải một con số cố định mà là một <strong>biến số thị trường</strong> &mdash; và bài này sẽ cho thấy nó phản ánh điều gì về tâm lý, chính sách, và cấu trúc thị trường vàng Việt Nam.</p>
    <p>Bài viết không khuyên mua hay bán vàng. Mục tiêu duy nhất: <strong>minh bạch hóa cơ chế</strong> bằng số liệu thật, để người đọc tự đánh giá.</p>
  </section>''')

# ===== CH 2 — rút gọn (methodology chuyển sang Phụ lục) =====
SECTIONS.append(f'''  <section id="chuong-2">
    <h2 class="section-title"><span class="num">II</span>Dữ liệu &amp; phương pháp &mdash; tóm tắt</h2>
    <p>Bài này dùng <strong>27.921 điểm giá SJC</strong> từ chính chủ sjc.com.vn (22/07/2009 → nay), ghép với giá vàng thế giới (COMEX GC=F) và tỷ giá USD/VND, để đo khoảng cách SJC vs QT từng ngày trong 17 năm. Công thức quy đổi: <em>1 lượng = 1,20565 troy oz</em>, nên <strong>vàng QT (VND/lượng) = GC_F × USDVND × 1,20565</strong>.<sup class="ref">2</sup></p>
    <p>Cross-check với nguồn độc lập giavang.org (30 ngày sample): <strong>19/30 khớp exact, 11/30 lệch ≤0,4%</strong>.<sup class="ref">3</sup></p>
    <p>Chi tiết nguồn, công thức, giới hạn và caveats &mdash; xem <a href="#phu-luc" class="src"><strong>Phụ lục: Phương pháp &amp; Giới hạn</strong></a> ở cuối bài.</p>
  </section>''')

print(f"Built {len(SECTIONS)} sections so far")
# remaining sections appended below in part 2

# ===== CH 3 — 2009-2012 =====
SECTIONS.append(f'''  <section id="chuong-3">
    <h2 class="section-title"><span class="num">III</span>2009&ndash;2012: Vàng &ldquo;bình thường&rdquo; (21 → 44 triệu)</h2>
    <p>Ba năm đầu của chuỗi là giai đoạn <strong>premium thấp và ổn định nhất</strong>. Giá SJC đi từ 21 triệu (07/2009) lên 44 triệu (cuối 2012), nhưng khoảng cách với vàng QT chỉ dao động quanh <em>5&ndash;7%</em>. Thị trường vàng VN lúc này <strong>di chuyển sát với giá thế giới</strong>.</p>
{TBL(["Năm","Premium TB","Premium min-max","Giá SJC TB (triệu)"],
 [("2009","+7,9%","+2,5% / +14,9%","25,4"),
  ("2010","+4,7%","−1,9% / +25,9%","29,5"),
  ("2011","+4,8%","−1,5% / +15,7%","40,7"),
  ("2012","+6,7%","+0,5% / +13,4%","44,3")])}
    <p>Đáng chú ý: năm 2010 và 2011 từng có <strong>ngày premium âm</strong> &mdash; tức SJC <em>rẻ hơn</em> vàng QT quy đổi. Đây là điều rất hiếm về sau. Giai đoạn này thị trường vàng VN còn <em>thanh khoản quốc tế hóa</em> tốt hơn, nhà đầu tư có thể arb qua vàng miếng nhập khẩu.</p>
{CO("info","📚 Bối cảnh","2009-2012 là giai đoạn vàng QT tăng mạnh (sâu khủng hoảng tài chính toàn cầu + nợ EU). SJC theo sát, chênh lệch hẹp.")}
  </section>''')

# ===== CH 4 — 2013-2015 =====
SECTIONS.append(f'''  <section id="chuong-4">
    <h2 class="section-title"><span class="num">IV</span>2013&ndash;2015: Lần tách biệt đầu tiên</h2>
    <p>Sau 2012, pattern đổi. Premium <strong>nhảy vọt từ +6,7% (2012) lên +13,0% (2013) và +14,1% (2015)</strong> &mdash; gần gấp đôi giai đoạn trước. Đây là <strong>lần đầu tiên SJC tách rời rõ rệt</strong> khỏi quỹ đạo vàng QT.</p>
{CH("c2_premium_yearly","📊 Premium SJC vs QT theo năm (TB / min / max)","Bar = premium trung bình năm; line = biên độ min/max. Chú ý 2013-2015 nhảy vọt.")}
    <p>Giải thích: 2013 là năm <em>vàng QT sập</em> (từ ~$1.700 xuống ~$1.200/oz, &minus;28%), nhưng <strong>SJC giảm ít hơn</strong> &mdash; hệ quả là premium phình ra. Tâm lý &ldquo;giữ giá&rdquo; của thị trường VN khiến giá nội địa <em>dính xuống</em> (sticky) khi QT giảm, nhưng <em>theo sát</em> khi QT tăng. Đây là <strong>bất đối xứng</strong> có lợi cho người bán SJC.</p>
{CO("warn","🧠 Góc nhìn hành vi","Hiện tượng &ldquo;giá dính xuống khi giảm&rdquo; gọi là <em>price stickiness</em> &mdash; nhà bán chậm giảm giá vì kỳ vọng giá hồi, trong khi nhà mua sẵn sàng trả giá cao vì sợ &lsquo;hết cơ hội&rsquo;. Bất đối xứng này là một nguồn cấu thành premium SJC.")}
  </section>''')

# ===== CH 5 — 2016-2020 =====
SECTIONS.append(f'''  <section id="chuong-5">
    <h2 class="section-title"><span class="num">V</span>2016&ndash;2020: Trở về cân bằng &mdash; 2019 gần hòa QT</h2>
    <p>Giai đoạn 5 năm này là <strong>nền tảng ổn định</strong> nhất của premium. Đặc biệt <strong>2019, premium trung bình chỉ +0,5%</strong> &mdash; SJC gần như <em>hòa hoàn toàn</em> với vàng QT quy đổi. Đây là năm tham chiếu quan trọng: chứng tỏ VN <em>có thể</em> có giá vàng sát QT khi điều kiện thị trường lý tưởng.</p>
{CH("c3_sjc_vs_world","📊 SJC vs Vàng QT (VND/lượng) — trung bình quý","Hai đường gần chồng nhau trong 2016-2020, đặc biệt 2019.")}
    <p>Điều kiện lý tưởng đó gồm: (1) vàng QT đi ngang (~$1.200-1.500/oz), (2) USD/VND ổn định, (3) không cú sốc chính sách nhập khẩu vàng VN. Khi cả 3 yếu tố &ldquo;im&rdquo;, premium co về gần 0.</p>
{TBL(["Năm","Premium TB","Premium min-max","Đặc điểm"],
 [("2016","+5,9%","+0,1% / +19,8%","Hồi về sau cú sốc 2015"),
  ("2017","+8,1%","+1,7% / +17,1%","Ổn định"),
  ("2018","+4,7%","−0,8% / +10,6%","Thu hẹp"),
  ("2019","+0,5%","−2,6% / +3,5%","Gần hòa QT &mdash; tham chiếu"),
  ("2020","+3,6%","−2,8% / +12,6%","COVID xuất hiện Q4")])}
  </section>''')

# ===== CH 6 — COVID 2020 =====
SECTIONS.append(f'''  <section id="chuong-6">
    <h2 class="section-title"><span class="num">VI</span>2020: Cú sốc COVID &mdash; bid-ask spread bùng nổ</h2>
    <p>Năm 2020 đáng chú ý không vì premium (vẫn thấp +3,6%) mà vì <strong>bid-ask spread &mdash; chênh lệch mua/bán &mdash; nổ lên</strong>. Đây là <em>barometer căng thẳng thị trường</em> chính xác hơn cả premium.</p>
{CH("c5_bidask_yearly","📊 Bid-ask spread SJC theo năm (TB / max)","Bar = spread TB năm, line = spread max. 2020 vọt lên 6,92% max &mdash; dấu hiệu thị trường đóng băng.")}
    <p>Nền bình thường, spread SJC ~0,4&ndash;0,9% (vài trăm nghìn/lượng). Nhưng trong đỉnh hoảng loạn COVID (tháng 3/2020), spread <strong>vọt lên 6,92%</strong> &mdash; tức chênh lệch mua/bán tới <em>3,5 triệu/lượng</em>. Ý nghĩa: SJC <strong>mua vào giá cao, bán ra giá thấp</strong> nhiều bất thường &mdash; nhà đầu tư nếu cần thanh khoản ngay sẽ lỗ nặng.</p>
{CO("red","⚠️ Bài học thanh khoản","Premium nói về <em>khoảng cách với QT</em>, nhưng bid-ask spread nói về <em>chi phí giao dịch thực</em>. Năm hoảng loạn, spread mới là thứ ăn mòn lợi nhuận nhà đầu tư &mdash; không phải premium.")}
    <p>2020 cũng là năm volatility SJC nhảy lên <strong>14,4% annualized</strong> (so với 3-8% các năm 2014-2019) &mdash; thị trường VN bắt đầu &ldquo;sống động&rdquo; trở lại.</p>
  </section>''')

# ===== CH 7 — 2021-2022 đỉnh premium =====
SECTIONS.append(f'''  <section id="chuong-7">
    <h2 class="section-title"><span class="num">VII</span>2021&ndash;2022: Đỉnh premium lịch sử +31%</h2>
    <p>Đây là <strong>2 năm định hình</strong> toàn bộ câu chuyện vàng VN. Premium từ +3,6% (2020) nhảy lên <strong>+15,9% (2021) rồi +31,2% (2022)</strong> &mdash; đỉnh điểm SJC đắt hơn vàng QT tới <em>43%</em> trong những ngày cao trào.</p>
{CH("c9_zoom_2020","📊 SJC vs Vàng QT 2020-2026 (trung bình tháng)","Hai đường tách nhau rõ từ 2021, khoảng cách lớn nhất 2022-2023.")}
    <p>Sự tách biệt này <strong>không do vàng QT giảm</strong> &mdash; vàng QT cũng tăng mạnh (COVID → lạm phát → chiến tranh Nga-Ukraine). Nguyên nhân chính: <em>cầu vàng VN bùng nổ</em> hậu COVID, trong khi <em>cung nhập khẩu bị kìm</em> (quota, thủ tục). Kết quả: giá nội địa &ldquo;bay&rdquo; xa giá QT.</p>
{TBL(["Năm","Premium TB","Premium max","Spread mua-bán TB","Giải thích"],
 [("2021","+15,9%","+25,9%","0,59M","Sốt vàng bắt đầu"),
  ("2022","+31,2%","<strong>+43,1%</strong>","0,87M","<strong>Đỉnh premium lịch sử</strong>"),
  ("2023","+23,3%","+31,7%","0,78M","Vẫn cao nhưng hạ nhiệt")])}
    <p>Spread mua-bán cũng tăng theo (0,87M/lượng 2022 vs 0,2M 2010) &mdash; thị trường căng thẳng <em>kéo dài</em>, không chỉ cú sốc ngắn.</p>
  </section>''')

# ===== CH 8 — 2023-2026 =====
SECTIONS.append(f'''  <section id="chuong-8">
    <h2 class="section-title"><span class="num">VIII</span>2023&ndash;2026: Vàng 150-191 triệu &amp; &ldquo;bình thường mới&rdquo;</h2>
    <p>Giai đoạn hiện tại đánh dấu <strong>đỉnh giá tuyệt đối</strong> nhưng premium &ldquo;bình thường hóa&rdquo; trở lại. SJC chạm <strong>191,3 triệu/lượng (29/01/2026)</strong> &mdash; gấp 9 lần đầu chuỗi.</p>
{CH("c1_sjc_full","📊 Giá SJC 2009-2026 (trung bình tháng, triệu/lượng)","Tăng từ 21M (2009) lên 191M (đỉnh 01/2026), ~7× trong 17 năm.")}
    <p>Quan trọng: <strong>premium ổn định quanh +11&ndash;14%</strong> (2024-2026), <em>không</em> lặp lại đỉnh +31% của 2022. Điều này cho thấy premium +30% là <em>hiện tượng ngoại lệ</em> (hậu COVID), còn +10-15% mới là &ldquo;bình thường mới&rdquo; sau 2020.</p>
{TBL(["Năm","Premium TB","Giá SJC TB (triệu)","Volatility năm","Max drawdown"],
 [("2024","+14,8%","81,9","14,1%","−16,7%"),
  ("2025","+11,7%","122,1","15,9%","−5,5%"),
  ("2026 (H1)","+13,8%","168,4","<strong>24,5%</strong>","<strong>−27,6%</strong>")])}
    <p>2026 đáng chú ý: <strong>volatility 24,5% + drawdown −27,6%</strong> &mdash; năm biến động mạnh nhất trong chuỗi. Vàng rơi từ đỉnh 191M về ~138M rồi hồi &mdash; biên độ chưa từng thấy trước 2020.</p>
  </section>''')

print(f"Built {len(SECTIONS)} sections (through ch8)")

# ===== CH 9 — Premium distribution =====
SECTIONS.append(f'''  <section id="chuong-9">
    <h2 class="section-title"><span class="num">IX</span>Phân phối premium 17 năm: số liệu nói gì</h2>
    <p>Thay vì chỉ nhìn trung bình, hãy xem <strong>toàn bộ phân phối</strong> của premium trong 3.132 ngày có dữ liệu.</p>
{CH("c4_premium_hist","📊 Phân phối premium SJC vs QT (3.132 ngày)","Mỗi cột = số ngày có premium trong khoảng đó. Đỉnh phân phối ở đâu? Đuôi dài về phía nào?")}
    <p>Số liệu thực tế: premium <strong>trung bình +11,7%</strong> cả chuỗi, nhưng phân phối <em>lệch phải</em> &mdash; phần lớn ngày tập trung 0-15%, với đuôi dài kéo về +40% (2022). Ngày premium <em>âm</em> (SJC rẻ hơn QT) rất hiếm &mdash; chỉ vài % tổng số ngày.</p>
{TBL(["Phân vị","Premium %","Ý nghĩa"],
 [("P10 (10% ngày thấp nhất)","~0%","Ngày SJC hòa QT"),
  ("P50 (median)","+9,8%","Một nửa số ngày dưới mức này"),
  ("Trung bình","+11,7%","Bị kéo lên bởi đuôi 2022"),
  ("P90","+24%","10% ngày cao nhất"),
  ("Max","+43,1%","Đỉnh 2022")])}
    <p>Đọc hiểu: <strong>nếu mua SJC ngẫu nhiên một ngày trong 17 năm, 9/10 lần bạn sẽ trả premium 0-24%</strong>. Cái &ldquo;luôn đắt nhất thế giới&rdquo; đúng, nhưng biên độ dao động rất lớn.</p>
  </section>''')

# ===== CH 10 — 5 yếu tố premium =====
SECTIONS.append(f'''  <section id="chuong-10">
    <h2 class="section-title"><span class="num">X</span>Tại sao SJC luôn đắt hơn? 5 yếu tố</h2>
    <p>Premium không phải ngẫu nhiên &mdash; nó là <strong>tổng của 5 yếu tố cấu trúc</strong>, mỗi yếu tố đóng góp một phần:</p>
{CMP("Vàng QT (London/COMEX)",["Giá chuẩn thế giới, USD/oz","Thanh khoản khổng lồ","Không rào cản nhập khẩu"],"Vàng SJC (VN)",["Quy đổi qua USD/VND","+ Thuế nhập khẩu + GST","+ Quota nhập khẩu (hạn chế)","+ Spread mua-bán thương lái","+ Premium tâm lý &lsquo;vàng SJC&rsquo;",],ltag="Tham chiếu",rtag="Thực tế VN")}
    <p>Chi tiết 5 yếu tố:</p>
{TBL(["Yếu tố","Đóng góp ước tính","Biến động"],
 [("1. Thuế &amp; phí nhập khẩu","~3-5%","Cố định theo chính sách"),
  ("2. Quota nhập khẩu (cung kìm)","~2-8%","Tăng khi cầu bùng nổ"),
  ("3. Spread mua-bán SJC","~0,5-2,7%/năm","Barometer căng thẳng"),
  ("4. Premium thương hiệu SJC","~2-4%","Tâm lý &lsquo;vàng chuẩn&rsquo;"),
  ("5. Chênh lệch thời gian chốt","~0-2%","Giờ giao dịch khác")])}
    <p>Tổng cộng: <strong>~8-21% premium cấu trúc</strong> trong điều kiện bình thường, có thể phình lên +30%+ khi yếu tố (2) quota và (4) tâm lý cùng bùng nổ &mdash; đúng như 2022.</p>
{CO("info","📚 Giải thích","Yếu tố (2) quota là <em>van điều tiết</em> quan trọng nhất. Khi NHNN siết quota nhập vàng (như 2013, 2022), cung VN khô hạn → giá nội địa tách rời QT.")}
  </section>''')

# ===== CH 11 — Lag correlation =====
SECTIONS.append(f'''  <section id="chuong-11">
    <h2 class="section-title"><span class="num">XI</span>Độ trễ: giá QT biến → SJC phản ứng sau bao lâu?</h2>
    <p>Câu hỏi thực tế: nếu vàng QT tăng đêm qua, <strong>SJC có tăng theo vào sáng hôm sau không</strong>? Phân tích cross-correlation trên 3.132 ngày trả lời:</p>
{CH("c8_lag_corr","📊 Cross-correlation: returns QT hôm nay vs SJC sau k ngày","Lag 0 = cùng ngày. Peak ở lag 0 nghĩa là SJC phản ứng ngay trong ngày.")}
    <p>Kết quả bất ngờ: <strong>peak correlation ở lag 0 (cùng ngày), r = 0,36</strong>. Nghĩa là SJC <em>phản ứng ngay trong ngày</em> khi QT biến động &mdash; không có trễ nhiều ngày như tưởng tượng. Nhưng r chỉ 0,36 (không phải 1.0) vì <strong>premium hấp thụ một phần biến động</strong>.</p>
{TBL(["Chỉ số","Giá trị","Ý nghĩa"],
 [("Peak lag","0 ngày","SJC phản ứng cùng ngày QT"),
  ("Peak r","0,36","Tương quan trung bình &mdash; không hoàn toàn theo"),
  ("Follow-rate 1 ngày","56,8%","Khi QT tăng, SJC tăng hôm sau 57% lần")])}
    <p>Đọc hiểu: <strong>57% cú lên của QT được SJC &ldquo;theo&rdquo; trong ngày hôm sau</strong>. 43% còn lại bị premium &ldquo;nuốt&rdquo; &mdash; tức khi QT tăng mạnh, premium <em>co lại</em> thay vì giá SJC tăng tương đương. Đây là cơ chế tự điều chỉnh.</p>
  </section>''')

print(f"Built {len(SECTIONS)} sections (through ch11)")

# ===== CH 12 — bid-ask deep =====
SECTIONS.append(f'''  <section id="chuong-12">
    <h2 class="section-title"><span class="num">XII</span>Bid-ask spread: barometer căng thẳng thị trường</h2>
    <p>Premium nói về khoảng cách với QT, nhưng <strong>bid-ask spread (chênh lệch mua/bán) nói về sức khỏe nội tại</strong> của thị trường SJC. Khi spread nở ra, đó là tín hiệu <em>thanh khoản đang khô</em>.</p>
{TBL(["Năm","Spread TB %","Spread TB (triệu/lượng)","Tình trạng"],
 [("2010-2019","0,3-0,9%","0,06-0,25M","Bình thường"),
  ("2020","1,24%","0,65M","COVID &mdash; căng thẳng"),
  ("2022","1,30%","0,87M","Đỉnh premium &mdash; căng"),
  ("2024","<strong>2,71%</strong>","<strong>2,21M</strong>","<strong>Spread nổ &mdash; bất thường</strong>"),
  ("2026","1,76%","2,91M","Cao nhưng hạ")])}
    <p>2024 là năm đáng lo ngại: spread TB <strong>2,71%</strong> (max 5,26%) &mdash; cao gấp <em>3 lần</em> giai đoạn bình thường. Nghĩa là mỗi lượng SJC giao dịch, nhà đầu tư &ldquo;đốt&rdquo; ~2,2 triệu vào spread. Tích lũy cả năm, đây là chi phí ẩn khổng lồ.</p>
{CO("warn","⚠️ Chi phí ẩn","Nhiều nhà đầu tư chỉ nhìn premium vs QT, nhưng <strong>spread mới là thứ thực sự ăn mòn lợi nhuận khi giao dịch nhiều</strong>. Năm spread cao (2020, 2024), mua-bán lướt sóng SJC gần như chắc lỗ.")}
  </section>''')

# ===== CH 13 — volatility & drawdown =====
SECTIONS.append(f'''  <section id="chuong-13">
    <h2 class="section-title"><span class="num">XIII</span>Volatility &amp; drawdown 17 năm</h2>
    <p>Vàng được coi là &ldquo;trú ẩn an toàn&rdquo;, nhưng số liệu cho thấy <strong>biến động SJC không hề thấp</strong> &mdash; đặc biệt từ 2020 trở đi.</p>
{CH("c6_vol_drawdown","📊 Volatility (bar) & max drawdown (line) theo năm","2026 vol 24,5% + drawdown −27,6% &mdash; năm dữ dội nhất.")}
    <p>Quan sát: volatility <strong>tăng rõ rệt sau 2020</strong> &mdash; từ mức 3-8% (2014-2019) lên 12-24% (2020-2026). Vàng SJC ngày càng &ldquo;cư xử&rdquo; như tài sản rủi ro, không còn &ldquo;an toàn&rdquo; như định kiến.</p>
{TBL(["Năm","Vol năm","Max drawdown","Lãi/giảm năm","Đặc điểm"],
 [("2017","4,6%","−4,0%","+0,1%","Yên tĩnh nhất"),
  ("2020","14,4%","−13,7%","+31,6%","COVID &mdash; tăng mạnh"),
  ("2024","14,1%","−16,7%","+12,3%","Biến động cao"),
  ("2025","15,9%","−5,5%","<strong>+79,8%</strong>","Năm tăng mạnh nhất"),
  ("2026","<strong>24,5%</strong>","<strong>−27,6%</strong>","−4,8%","Hồi sau đỉnh")])}
    <p>Drawdown −27,6% năm 2026 nghĩa là: <strong>từ đỉnh 191M, SJC từng rơi về ~138M</strong> &mdash; mất 53 triệu/lượng. Nếu mua đỉnh, mất hơn 1/4 giá trị trong vài tháng.</p>
  </section>''')

# ===== CH 14 — ring vs bar =====
SECTIONS.append(f'''  <section id="chuong-14">
    <h2 class="section-title"><span class="num">XIV</span>Vàng nhẫn vs vàng miếng: 2 thị trường trong 1</h2>
    <p>SJC có 2 sản phẩm chính: <em>vàng miếng</em> (1L, đầu tư) và <em>vàng nhẫn</em> 99,99% (trang sức + đầu tư). Phân tích chênh lệch giữa 2 loại cho thấy <strong>tâm lý thị trường phân hóa</strong>.</p>
{CH("c7_ring_vs_bar","📊 Vàng miếng (bar) đắt hơn vàng nhẫn (ring) theo năm","Bar = chênh lệch TB, line = min/max. 2022 nhẫn đắt hơn miếng bất thường.")}
    <p>Pattern thú vị: bình thường <em>miếng đắt hơn nhẫn</em> (premium thương hiệu + thanh khoản). Nhưng <strong>2022, ngược lại &mdash; nhẫn đắt hơn miếng +24%</strong> (max +30%)!</p>
{TBL(["Năm","Miếng vs nhẫn","Ý nghĩa"],
 [("2019","−0,4%","Gần hòa &mdash; bình thường"),
  ("2021","+9,2%","Miếng đắt hơn &mdash; quay về"),
  ("<strong>2022</strong>","<strong>+24% (nhẫn đắt hơn!)</strong>","<strong>Sốt vàng nhẫn — tâm lý</strong>"),
  ("2024","+9,4%","Miếng đắt hơn bình thường"),
  ("2026","+0,4%","Gần hòa")])}
{CO("info","🧠 Góc nhìn tâm lý","Sốt vàng nhẫn 2022 là hiện tượng <em>herding</em> điển hình: truyền thông đồn &lsquo;vàng nhẫn tăng giá&rsquo; → người dân đổ xô mua nhẫn → push giá nhẫn vượt miếng. Đây là <strong>bong bóng tâm lý cục bộ</strong>, không liên quan tới giá vàng QT.")}
  </section>''')

print(f"Built {len(SECTIONS)} sections (through ch14)")

# ===== SPECIAL INSIGHT 1 — gold types spread =====
SECTIONS.append(f'''  <section id="insight-1">
    <h2 class="section-title"><span class="num">★1</span>Insight: Chênh lệch các loại vàng theo thời gian</h2>
    <p>SJC không chỉ bán vàng miếng 1L &mdash; còn có <em>vàng nhẫn 99,99%</em>, <em>nữ trang 99%</em>, <em>nữ trang 75%</em>. So sánh giá 4 loại (quy về % giá SJC 1L) cho thấy <strong>phân hóa tâm lý rõ rệt</strong>.</p>
{CH("c11_gold_types","📊 Các loại vàng dưới dạng % giá SJC 1L (theo năm)","100% = SJC miếng. Nhẫn/nữ trang thấp hơn = rẻ hơn miếng. Chú ý 2022 nhẫn tụt về 80%.")}
    <p>3 pattern nổi bật:</p>
{TBL(["Loại vàng","2022 (sốt vàng)","2025-2026","Ý nghĩa"],
 [("SJC 1L miếng","100% (tham chiếu)","100%","Vàng đầu tư chuẩn"),
  ("Nhẫn 99,99%","<strong>80,7%</strong> (tụt 19%)","99,6% (gần hòa)","Sốt miếng 2022 &mdash; nhẫn rẻ tương đối"),
  ("Nữ trang 99%","79,2%","97,8%","Theo nhẫn nhưng rẻ hơn"),
  ("Nữ trang 75%","(chưa có data)","74,1%","Vàng kém hạt &mdash; rẻ ~25%")])}
    <p>Đọc hiểu: <strong>2022, vàng miếng đắt hơn nhẫn tới 19%</strong> &mdash; hiện tượng &ldquo;sốt vàng miếng&rdquo; do tâm lý trú ẩn đổ vào SJC 1L (thanh khoản cao nhất). Khi tâm lượng bình thường (2025-2026), nhẫn và miếng gần hòa, chỉ chênh ~0,4%.</p>
{CO("info","🧠 Vì sao quan trọng","Ai mua vàng nhẫn 2022 thay vì miếng <strong>tiết kiệm được 19%</strong> cùng lượng vàng 99,99%. Nhưng nhẫn thanh khoản kém hơn miếng &mdash; đánh đổi premium khi bán. Đây là <em>trade-off thanh khoản vs giá mua</em> thường bị bỏ qua.")}
  </section>''')

# ===== SPECIAL INSIGHT 2 — premium drivers =====
SECTIONS.append(f'''  <section id="insight-2">
    <h2 class="section-title"><span class="num">★2</span>Insight: Premium co giãn &mdash; tương quan với yếu tố nào?</h2>
    <p>Premium SJC vs QT không ngẫu nhiên &mdash; nó <strong>tương quan với 3 yếu tố</strong> đo được bằng correlation (lưu ý: tương quan ≠ nhân quả, xem caveat cuối chương):</p>
{CH("c12_premium_drivers","📊 Correlation: premium vs 3 driver","Bar = correlation với level premium; line = correlation với thay đổi premium hàng ngày. USD/VND change có r âm mạnh nhất.")}
{TBL(["Driver","Corr. với level","Corr. với Δpremium","Giải thích"],
 [("USD/VND thay đổi","r = &minus;0,03","<strong>r = &minus;0,49</strong>","VND yếu ↔ vàng QT tính VND tăng ↔ premium co lại"),
  ("Volatility vàng QT 20d","r = +0,02","r = 0,00","Gần như không tương quan &mdash; QT vol không đi kèm premium"),
  ("Bid-ask spread SJC","<strong>r = +0,30</strong>","r = &minus;0,03","Spread cao ↔ premium cao (cùng tín hiệu căng thẳng)")])}
    <p>Tương quan nổi bật nhất: <strong>USD/VND thay đổi có r = &minus;0,49 với thay đổi premium (cùng ngày)</strong>. Khi VND mất giá (USD/VND tăng), <em>premium thường co lại</em> &mdash; vì vàng QT tính bằng VND đã tự tăng theo tỷ giá, thu hẹp khoảng cách với SJC. Ngược lại, khi VND ổn định, premium có xu hướng giãn ra.</p>
{CO("warn","⚠️ Tương quan ≠ nhân quả","Phân tích lag cho thấy <strong>peak ở lag 0 (cùng ngày)</strong>, không có độ trễ rõ 1 chiều &mdash; nghĩa là USD/VND và premium <em>phản ứng đồng thời</em>, có thể cùng phản ứng với yếu tố thứ 3 (Fed, dòng vốn), hoặc 2 chiều (premium sốt → NHNN can thiệp tỷ giá). Bài này chỉ báo <strong>tương quan</strong>, không claim A gây ra B.")}
    <p>Driver thứ hai (bid-ask spread r=+0,30): <strong>khi thị trường căng thẳng, spread lẫn premium cùng tăng</strong> &mdash; cùng phản ánh thiếu thanh khoản. Volatility QT gần như không tương quan &mdash; premium VN chủ yếu là hiện tượng nội địa, không nhập từ biến động QT.</p>
  </section>''')

# ===== SPECIAL INSIGHT 3 — SJC vs VN-Index =====
SECTIONS.append(f'''  <section id="insight-3">
    <h2 class="section-title"><span class="num">★3</span>Insight: SJC vs VN-Index &mdash; 2 tài sản, 2 câu chuyện</h2>
    <p>Câu hỏi phổ biến: <em>nên mua vàng hay mua cổ phiếu?</em> 17 năm dữ liệu cho thấy đây là <strong>2 asset class gần như hoàn toàn tách biệt</strong>.</p>
{KPI(("+615%","SJC 17 năm","amber"),("+339,5%","VN-Index 17 năm","cyan"),("0,028","Correlation daily","violet"),("−45%","VN-Index max drawdown","red"))}
{CH("c13_sjc_vnindex","📊 Lãi/giảm năm: SJC vs VN-Index","Bar = SJC, line = VN-Index. Nhiều năm đối nghịch: 2017 VNIndex +48% SJC +0%, 2022 SJC +8% VNIndex −33%.")}
    <p>3 phát hiện đắt giá:</p>
{TBL(["","SJC vàng","VN-Index cổ phiếu"],
 [("Tổng return 17 năm","+615% (gấp ~1,8×)","<strong>+339,5%</strong>"),
  ("Max drawdown","−32,5% (nhẹ hơn)","<strong>−45,0%</strong> (sâu hơn)"),
  ("Correlation daily","<strong>0,028</strong> (gần 0)","dao động &minus;0,24 → +0,27 khi lăn 252 ngày")])}
    <p><strong>Correlation daily 0,028</strong> thấp &mdash; nhưng cần đọc kỹ: rolling 252 ngày dao động từ <strong>&minus;0,24 đến +0,27</strong>, không phải cố định 0. Tức là <em>ngắn hạn</em> vàng và cổ phiếu gần như không di chuyển cùng nhau, nhưng <em>dài hạn</em> cả 2 cùng xu hướng tăng (2009-2026). Chúng <strong>không thay thế nhau trong ngắn hạn</strong> &mdash; phục vụ mục đích khác: vàng = trú ẩn giá trị, cổ phiếu = tăng trưởng.</p>
    <p>Pattern đối nghịch rõ nhất:</p>
{CMP("Năm cổ phiếu thắng",["2017: VNIndex +48% vs SJC +0,3%","2021: VNIndex +35,7% vs SJC +9,9%","2025: VNIndex +40,9% vs SJC +81,5% (cả 2 thắng)"],"Năm vàng thắng",["2011: SJC +16% vs VNIndex −27,5%","<strong>2022: SJC +8% vs VNIndex −33%</strong>","2020: SJC +31% vs VNIndex +15%"],ltag="CK mạnh",rtag="Vàng mạnh")}
{CO("info","💡 Đọc hiểu","Vàng SJC và VN-Index <strong>không phải đối thủ</strong> &mdash; chúng làm việc ở chu kỳ khác. Vàng thắng khi <em>tâm lý phòng thủ</em> lên (2011, 2022), cổ phiếu thắng khi <em>nguy cơ rủi ro</em> (risk-on, 2017, 2021). Đa hóa qua cả 2 có ý nghĩa &mdash; không phải chọn 1.")}
  </section>''')

# ===== SPECIAL INSIGHT 4 — risk: drawdown & recovery =====
SECTIONS.append(f'''  <section id="insight-4">
    <h2 class="section-title"><span class="num">★4</span>Đánh giá rủi ro: Drawdown &amp; thời gian phục hồi</h2>
    <p>Return cao không đủ &mdash; cần biết <strong>rủi ro đi kèm</strong>. Drawdown (mức sụt từ đỉnh) và thời gian phục hồi là 2 thước đo rủi ro quan trọng. 17 năm dữ liệu cho thấy 3 tài sản có <em>chữ ký rủi ro rất khác nhau</em>.</p>
{CH("c14_drawdown","📊 Drawdown theo thời gian: SJC vs Vàng QT vs VN-Index (trung bình quý)","Mỗi đường = % sụt từ đỉnh gần nhất. Đáy càng sâu = sập càng nặng. VN-Index sâu nhất nhưng hồi nhanh; SJC nông hơn nhưng chìm lâu.")}
    <p>3 chỉ số rủi ro chính (toàn bộ chuỗi 2009-2026, 3.122 ngày chung):</p>
{TBL(["Tài sản","Max drawdown","Số ngày underwater","Thời gian phục hồi dài nhất"],
 [("SJC vàng","<strong>−32,5%</strong> (nông nhất)","2.909 ngày (93%)","<strong>1.512 ngày (~4,1 năm)</strong>"),
  ("Vàng QT","−42,3%","2.916 ngày (93%)","1.508 ngày (~4,1 năm)"),
  ("VN-Index","<strong>−45,0%</strong> (sâu nhất)","2.963 ngày (95%)","902 ngày (~2,5 năm)")])}
    <p>Paradox quan trọng: <strong>SJC sập nông nhất nhưng phục hồi lâu nhất</strong>. VN-Index sập sâu hơn (−45% vs −32,5%) nhưng quay lại đỉnh nhanh hơn (902 vs 1.512 ngày). Nghĩa là <em>rủi ro không chỉ là biên độ sập, mà còn là thời gian chờ</em>.</p>
{CO("red","⚠️ Vì sao quan trọng với nhà đầu tư","Nếu mua SJC ở đỉnh 2012-2013 (~46 triệu), mất <strong>4+ năm</strong> mới thấy giá vượt đỉnh cũ (giữa 2016). Trong khi ai mua VN-Index đỉnh 2007/2018 sập &minus;45% nhưng ~2,5 năm đã hồi. <strong>Vàng &lsquo;an toàn&rsquo; không phải &lsquo;an toàn về thời gian&rsquo;</strong> &mdash; nó an toàn về biên độ.")}
{CO("warn","🧠 Góc nhìn tâm lý","Loss aversion (Kahneman) giải thích vì sao drawdown thời gian dài đau hơn drawdown sâu ngắn: <em>sự đau khổ kéo dài</em> làm nhà đầu tư bán thua ở đáy. SJC với 4 năm underwater là &lsquo;bài test tâm lý&rsquo; khắc nghiệt hơn VN-Index sập nhanh hồi nhanh.")}
    <p>Đọc thêm: <strong>93-95% số ngày</strong> cả 3 tài sản đều ở trạng thái underwater (dưới đỉnh). Đây là <em>bình thường</em> &mdash; thị trường luôn ở gần đỉnh hơn đáy, nhưng phần lớn thời gian &ldquo;chưa về đỉnh mới&rdquo;. Hiểu điều này giúp không hoảng loạn khi giá &ldquo;còn xa đỉnh&rdquo;.</p>
  </section>''')

# ===== CH 15 — behavioral finance =====
SECTIONS.append(f'''  <section id="chuong-15">
    <h2 class="section-title"><span class="num">XV</span>Tâm lý &ldquo;trú ẩn&rdquo;: vàng VN qua lăng kính tài chính hành vi</h2>
    <p>Tại sao người Việt giữ vàng dù premium cao? Số liệu 17 năm cho thấy đây không phải quyết định &ldquo;phi lý&rdquo; &mdash; nó phản ánh <strong>cấu trúc động lực</strong> cụ thể, giải thích được bằng tài chính hành vi.</p>
{CMP("Logic cổ điển (&lsquo;phi lý&rsquo;)",["Premium +11% = đắt quá","Spread 2,7% = lỗ giao dịch","Nên mua vàng QT thay SJC"],"Logic hành vi (thực tế VN)",["Vàng QT = không mua được ở VN","Vàng SJC = thanh khoản OTC tức thì","Trú ẩn lạm phát VND &mdash; +79% 2025","Herding: &lsquo;mọi người đều mua&rsquo;"],ltag="Lý thuyết",rtag="Thực tế")}
    <p>3 cơ chế chính (theo Kahneman, Shiller):</p>
{TBL(["Cơ chế","Tác giả gốc","Biểu hiện ở VN"],
 [("Loss aversion (~2:1)","Kahneman &amp; Tversky 1979","Giữ vàng dù lỗ spread vì sợ &lsquo;bán rồi giá tăng&rsquo;"),
  ("Herding / herd behavior","Shiller 2000 (Irrational Exuberance)","Sốt vàng 2022 &mdash; mua vì &lsquo;mọi người mua&rsquo;"),
  ("Mental accounting","Thaler 1985","Tách &lsquo;vàng trú ẩn&rsquo; khỏi &lsquo;vàng đầu tư&rsquo; &mdash; không tính spread")])}
    <p>Đặc biệt, <strong>2025 (SJC +79,8% năm)</strong> là case study herding rõ nhất: vàng QT cũng tăng nhưng <em>không</em> +80% &mdash; phần lớn đợt tăng đó là <strong>premium giãn ra</strong> do cầu VN bùng nổ, không phải vàng QT đắt lên.<sup class="ref">4</sup></p>
  </section>''')

# ===== CH 16 — 3-tier cascade =====
SECTIONS.append(f'''  <section id="chuong-16">
    <h2 class="section-title"><span class="num">XVI</span>3-tier cascade: London → Shanghai → Sài Gòn</h2>
    <p>Vàng VN không tồn tại cô lập &mdash; nó là <strong>chốt cuối</strong> của một chuỗi premium đi từ tâm thế giới ra biên.</p>
{TL(("Tier 1: London/COMEX","Giá vàng QT chuẩn (USD/oz). Thanh khoản lớn nhất, premium = 0.","green"),
     ("Tier 2: Shanghai","GC=F × USDCNY. Shanghai Gold Exchange có premium ~1-2% (quota nhập vàng TQ).","amber"),
     ("Tier 3: Sài Gòn (SJC)","Tier 2 × (USDVND/USDCNY) + premium VN ~10-15%. Chốt cuối, premium cao nhất.","red"))}
    <p>Cross-rate phân tích: <strong>VND/CNY trung bình 3.360</strong> (2009-2026). Nghĩa là 1 nhân dân tệ ≈ 3.360 đồng. Qua path này, giá vàng &ldquo;ngầm&rdquo; TQ quy ra VND/lượng có thể tính &mdash; và chênh lệch với SJC chính là <strong>premium VN thuần</strong> (sau khi trừ premium TQ).</p>
{CO("info","📚 Tại sao quan trọng","Cascade này cho thấy premium SJC = premium TQ + premium VN. TQ (với TGE lớn hơn,quota lỏng hơn) premium thấp hơn VN &mdash; VN &lsquo;thêm&rsquo; phần riêng do thị trường nhỏ + kiểm soát nhập khẩu chặt hơn.")}
    <p>Limitation: bài này dùng <em>GC=F × CNY</em> làm proxy cho Shanghai (không có data SGE trực tiếp), nên premium TQ là ước tính. Nhưng thứ bậc <strong>London &lt; Shanghai &lt; Sài Gòn</strong> về premium là pattern nhất quán.</p>
  </section>''')

# ===== CH 17 — limitations (CHUYỂN VÀO PHỤ LỤC, xóa khỏi chương chính) =====
# Đã chuyển xuống section "phu-luc" dùng <details collapse>

# ===== SPECIAL INSIGHT 5 — So what: decision framework =====
SECTIONS.append(f'''  <section id="insight-5">
    <h2 class="section-title"><span class="num">★5</span>Vậy nên &mdash; đọc trạng thái thị trường SJC</h2>
    <p>17 chương số liệu cần một takeaway đọc-được. Chương này tổng hợp 2 chỉ số then chốt &mdash; <strong>premium</strong> (giá có đắt không) và <strong>bid-ask spread</strong> (thanh khoản có căng không) &mdash; thành framework <strong>mô tả trạng thái</strong>. <em>Quan trọng: đây không phải công cụ dự báo</em> (xem backtest bên dưới).</p>
    <p>Ngưỡng dựa trên phân vị thực tế của phân phối premium 17 năm (P25/P50/P75), không tùy ý:</p>
{TBL(["Trạng thái","Premium (% days)","Spread","Đặc điểm"],
 [("<span style='color:#10d981'>● Thấp</span>","&lt; 4,2% (P25, ~25% ngày)","&lt; 1%","SJC sát QT, thanh khoản tốt"),
  ("<span style='color:#fbbf24'>● Trung bình</span>","4,2-9,5% (P25-P50)","&lt; 1%","Premium ở mức thường gặp"),
  ("<span style='color:#f97316'>● Cao</span>","9,5-15,5% (P50-P75)","1-2%","Premium giãn, spread nở"),
  ("<span style='color:#ef4444'>● Rất cao</span>","&gt; 15,5% (P75+, ~25% ngày)","&gt; 2%","Giai đoạn căng (2021-2023)")])}
    <p>Ma trận (premium × spread) thực tế &mdash; <strong>% ngày rơi vào mỗi tổ hợp</strong> (3.132 ngày):</p>
{TBL(["","spread &lt;1%","spread 1-2%","spread 2-3%","spread &gt;3%"],
 [("premium &lt;8%","<strong>35%</strong> (phổ biến nhất)","3,2%","4,3%","0,8%"),
  ("premium 8-15%","22,4%","6,2%","1,2%","0%"),
  ("premium 15-25%","9,1%","8,0%","1,6%","0,2%"),
  ("premium &gt;25%","0,8%","5,3%","1,3%","<strong>0,7%</strong> (hiếm)")])}
    <p>Đa số ngày (35%) nằm ở góc &ldquo;yên&rdquo;: premium thấp + spread thấp. Góc &ldquo;hoảng loạn&rdquo; (premium&gt;25% + spread&gt;3%) chỉ <strong>0,7% thời gian</strong> &mdash; cực hiếm, chủ yếu 2022.</p>
{CO("red","⚠️ Backtest: framework KHÔNG dự báo drawdown","Test thực tế &mdash; chia 3.132 ngày theo 4 vùng premium, đo drawdown forward 12 tháng: median <strong>&minus;9,7% đến &minus;12,9%</strong> ở MỌI vùng (gần như giống nhau). Thậm chí vùng &lsquo;thấp&rsquo; có decile xấu nhất &minus;23,7% &mdash; <strong>premium thấp không bảo vệ khỏi drawdown</strong>. Kết luận: framework này <strong>chỉ mô tả trạng thái</strong>, không dự báo rủi ro forward.")}
    <p>Ba takeaway thực tế (đã verify):</p>
{TBL(["","#","Phát hiện có data hỗ trợ"],
 [("1","Spread là chi phí ẩn xác định được","Năm spread 2,7% (2024), mỗi lượng mua-bán mất ~2,2 triệu &mdash; <strong>biết trước được</strong>, không cần dự báo"),
  ("2","Premium cho biết &lsquo;đang trả phí bao nhiêu&rsquo;","Không cho biết giá sẽ lên/xuống &mdash; nhưng cho biết khoảng cách vs QT hiện tại"),
  ("3","Vàng &lsquo;an toàn&rsquo; = an toàn về biên độ, không về thời gian","Drawdown nông (&minus;32%) nhưng phục hồi 4+ năm (★4) &mdash; cần vốn kiên nhẫn")])}
{CO("info","💡 Tóm tắt","Framework <strong>không dự báo</strong> &mdash; nó <em>đo</em>. Nó cho biết: hôm nay bạn đang trả premium bao nhiêu, mất spread bao nhiêu. Quyết định mua/bán phụ thuộc mục tiêu (trú ẩn vs đầu tư), thời gian nắm giữ, khẩu vị rủi ro &mdash; những thứ framework không thay bạn quyết.")}
  </section>''')

# ===== SPECIAL INSIGHT 6 — myth-busting (concise, data-led) =====
SECTIONS.append(f'''  <section id="insight-6">
    <h2 class="section-title"><span class="num">★6</span>Thực hư: vàng SJC trong 17 năm</h2>
    <p>6 nhận định phổ biến &mdash; mỗi cái <strong>verify bằng số liệu</strong>. Phán quyết: &check; đúng, &cross; sai, &asymp; nửa đúng.</p>
{CH("c15_inflation","📊 SJC nominal vs điều chỉnh lạm phát (2009=100, triệu/lượng)","Đường trên = giá niêm yết. Đường dưới = sức mua thực (chia cho CPI). Khoảng cách = lạm phát ăn mòn.")}
    <p>Phát hiện quan trọng nhất: SJC nominal +608%, nhưng <strong>real (điều chỉnh lạm phát) chỉ +226%</strong> &mdash; lạm phát 17 năm ăn &minus;117% điểm phần trăm. Đặc biệt <strong>2013-2015 vàng giảm sức mua &minus;30%</strong> (từ 31M real xuống 22M real), chỉ vượt đỉnh real 2012 vào khoảng 2022.</p>
{TBL(["Nhận định phổ biến","Số liệu verify","Phán quyết"],
 [("&ldquo;Vàng luôn tăng&rdquo;","2013: &minus;25,6%, 2015: &minus;7% nominal; 2014-2015 real &minus;30%. Có giai đoạn giảm nhiều năm","<span style='color:#ef4444'>&cross; Sai</span>"),
  ("&ldquo;Vàng bảo vệ lạm phát&rdquo;","Real return +226% dài hạn OK, nhưng 2013-2015 mất &minus;30% sức mua, phải chờ ~10 năm hồi","<span style='color:#fbbf24'>&asymp; Nửa đúng</span>"),
  ("&ldquo;Vàng an toàn&rdquo;","Drawdown &minus;32%, recovery 4+ năm (★4)","<span style='color:#fbbf24'>&asymp; Nửa đúng</span> (biên độ OK, thời gian không)"),
  ("&ldquo;Premium cao = sắp tăng tiếp&rdquo;","Backtest (★5): forward DD giống nhau mọi vùng premium","<span style='color:#ef4444'>&cross; Sai</span>"),
  ("&ldquo;Premium SJC = lừa đảo&rdquo;","5 yếu tố cấu trúc thật (chương X): quota, thuế, thanh khoản","<span style='color:#ef4444'>&cross; Sai</span> (chi phí thật, không bóc lột)"),
  ("&ldquo;Spread ăn hết lời&rdquo;","Spread 2,7%/giao dịch 2024 &mdash; đúng cho trader, sai cho holder dài hạn","<span style='color:#10d981'>&check; Đúng cho trader</span>")])}
    <p>Đọc cùng: 6 nhận định trên <strong>3 sai, 2 nửa đúng, 1 đúng (có điều kiện)</strong> &mdash; cả phe lẫn phe phản đối đều có điểm đúng và sai. Sự thật nằm ở giữa: vàng SJC là <strong>công cụ có đặc tính rõ</strong> (trú ẩn dài hạn, rủi ro ngắn hạn), không phải lời hứa &lsquo;luôn tăng&rsquo; hay &lsquo;lừa đảo&rsquo;.</p>
  </section>''')

# ===== CH 18 — conclusion =====
SECTIONS.append(f'''  <section id="chuong-17">
    <h2 class="section-title"><span class="num">XVII</span>Kết luận: Vàng Việt Nam không chỉ là vàng</h2>
    <p>17 năm dữ liệu cho thấy vàng SJC không đơn thuần là &ldquo;vàng&rdquo; &mdash; nó là <strong>vàng + một loạt premium cấu trúc</strong> phản ánh đặc thù thị trường VN: kiểm soát nhập khẩu, tâm lý trú ẩn, thanh khoản OTC, và thương hiệu SJC.</p>
{KPI(("+11,7%","Premium TB 17 năm","amber"),("+43,1%","Premium max (2022)","red"),("+0,5%","Premium min (2019)","green"),("0 ngày","Lag QT→SJC (cùng ngày)","cyan"))}
    <p>Ba takeaway chính:</p>
{TBL(["","#","Ý nghĩa"],
 [("1","Premium không cố định &mdash; nó là biến số","Từ 0% (2019) đến 43% (2022), dao động phản ánh tâm lý + chính sách"),
  ("2","Bid-ask spread là chi phí ẩn lớn","Năm căng (2020, 2024) spread ăn mòn lợi nhuận hơn premium"),
  ("3","SJC &lsquo;an toàn&rsquo; là định kiến","Volatility 24% + drawdown −27% (2026) &mdash; rủi ro cao")])}
    <p>Bài không khuyên mua hay bán. Mục tiêu: <strong>người đọc hiểu cơ chế</strong> &mdash; premium từ đâu ra, khi nào cao/thấp, và chi phí thực sự khi giao dịch SJC là gì. Quyết định sau đó là của bạn.</p>
{CO("info","💡 Bản chất","Đây là <strong>ghi chép tự nghiên cứu</strong> dựa trên 27.921 điểm dữ liệu chính chủ. Nếu có sai số, phản hồi để sửa. Số liệu đầy đủ công khai trong bộ dữ liệu kèm bài.")}
  </section>''')

# ===== PHỤ LỤC: Methodology + Giới hạn (collapse, mặc định đóng) =====
SECTIONS.append(f'''  <section id="phu-luc">
    <h2 class="section-title"><span class="num">📎</span>Phụ lục: Phương pháp &amp; Giới hạn</h2>
    <p>Phần kỹ thuật chi tiết &mdash; <strong>bấm để mở rộng</strong> khi cần đối chiếu. Mặc định đóng để không chiếm không gian nội dung chính.</p>

    <details class="appendix">
      <summary><strong>A. Nguồn dữ liệu chi tiết</strong></summary>
{TBL(["Chuỗi","Nguồn","Coverage","Ghi chú"],
 [("Vàng SJC 1L HCM","sjc.com.vn (chính chủ)","22/07/2009 → nay","27.921 pts intraday → daily close"),
  ("Vàng nhẫn SJC 99,99%","sjc.com.vn (id=49)","2016 → nay","28.515 pts (mới ra mắt)"),
  ("Nữ trang 99% / 75%","sjc.com.vn (id=97,113)","2016 → nay","Cho insight 1"),
  ("Vàng QT (XAUUSD)","Yahoo GC=F (COMEX futures)","2009 → nay","Proxy cho spot — futures != spot"),
  ("USD/VND","Yahoo USDVND=X + fawazahmed0","2009 → nay","Yahoo đến 2025, fawaz fill 2025-26"),
  ("USD/CNY","Yahoo CNY=X","2009 → nay","Cho cascade London→Shanghai→VN"),
  ("VN-Index","vnstock (source VCI)","2009 → nay","4.233 ngày, cho insight 3")])}
    </details>

    <details class="appendix">
      <summary><strong>B. Công thức quy đổi &amp; cross-check</strong></summary>
      <p>Công thức cốt lõi: <em>1 lượng SJC = 37,5 g = 1,20565 troy oz</em>, nên <strong>vàng QT (VND/lượng) = GC_F × USDVND × 1,20565</strong>.<sup class="ref">2</sup></p>
      <p>Cross-check với nguồn độc lập giavang.org (30 ngày sample): <strong>19/30 khớp exact, 11/30 lệch ≤0,4%</strong> &mdash; chênh lệch do thời điểm chốt giá khác nhau, không phải lỗi.<sup class="ref">3</sup></p>
      <p>Premium tính bằng giá <em>bán</em> SJC vs giá QT &mdash; phản ánh giá nhà đầu tư VN thực trả.</p>
    </details>

    <details class="appendix">
      <summary><strong>C. Giới hạn &amp; caveats (đọc trước khi dùng số liệu)</strong></summary>
{TBL(["Giới hạn","Tác động","Mức độ"],
 [("GC=F là futures, không phải spot XAUUSD","<strong>Basis không cố định</strong>: bình thường ~0,5%, nhưng nén mạnh khi căng (3-5% tháng 3/2020). Premium 2020/2022 có thể bị thổi phồng","Trung bình"),
  ("Premium dùng giá BÁN SJC","Premium mua-side thấp hơn bán-side ~1-2pp (do spread 0,4-2,7%). Bài báo premium &lsquo;người mua trả&rsquo;, không phải mid market","Đã nêu"),
  ("USDVND Yahoo có 5 giá trị lỗi (~21.x)","Đã filter, không ảnh hưởng kết luận","Đã xử lý"),
  ("Gap nguồn USDVND Yahoo→fawaz (7/2025)","Đã verify overlap 30 ngày: chênh mean 0,07% (&lt;0,5%), không systematic bias","Đã xử lý"),
  ("Vàng nhẫn (id=49) chỉ có data 2016+","Không phân tích ring trước 2016","Trung bình"),
  ("Premium Shanghai = proxy (GC=F×CNY)","Không có SGE trực tiếp","Trung bình"),
  ("SJC = giá bán lẻ HCM","Không bao gồm spread vàng QT thực tế","Đã nêu"),
  ("Drawdown tính trên close daily","Đã verify: intraday chỉ sâu hơn 0,6pp (−33,1% vs −32,5%) &mdash; không có flash-crash đáng kể","Đã xử lý"),
  ("Cross-check giavang.org: 10/30 ngày lệch","Đã verify sign: 3 cao / 7 thấp = <strong>mixed direction</strong>, không systematic bias","Đã xử lý"),
  ("Không có dữ liệu vàng miếng nhỏ (1 chỉ, 5 chỉ)","Chỉ SJC 1L &mdash; loại nhỏ có thể khác","Thấp")])}
      <p>Mọi con số premium trong bài có sai số ±1-2% do proxy GC=F (lớn hơn khi thị trường căng). Nhưng <strong>xu hướng và thứ bậc</strong> (2022 cao nhất, 2019 thấp nhất, post-2020 &lsquo;bình thường mới&rsquo; +10-15%) là vững.</p>
      <p><strong>Tương quan ≠ nhân quả</strong>: các phân tích correlation trong bài (premium vs driver, SJC vs VN-Index) báo độ liên quan, không claim A gây ra B. Nhiều quan hệ có thể 2 chiều hoặc do yếu tố thứ 3 (Fed, dòng vốn, tâm lý).</p>
    </details>
  </section>''')

# ===== REFS =====
SECTIONS.append(f'''  <section id="tai-lieu-tham-khao">
    <h2 class="section-title"><span class="num">📚</span>Tài liệu tham khảo</h2>
    <p>Số liệu và phương pháp luận trong báo cáo trích từ các nguồn dưới. Tham chiếu <sup class="ref">1-4</sup> trong nội dung trỏ về đây.</p>
    <h3>I. Số liệu thị trường</h3>
    <ol class="refs">
      <li><div><strong>Công ty Vàng Bạc Đá Quý Sài Gòn (SJC)</strong> &mdash; Biểu đồ giá vàng (PriceService API). <a href="https://sjc.com.vn/bieu-do-gia-vang" target="_blank" rel="noopener">sjc.com.vn</a> <span class="src-meta">27.921 điểm SJC 1L HCM, 22/07/2009 → 08/07/2026</span></div></li>
      <li><div><strong>Yahoo Finance</strong> &mdash; GC=F (COMEX Gold Futures), USDVND=X, CNY=X. <a href="https://finance.yahoo.com" target="_blank" rel="noopener">finance.yahoo.com</a> <span class="src-meta">Daily close, 2009-2026</span></div></li>
      <li><div><strong>giavang.org</strong> &mdash; Lịch sử giá vàng SJC. <a href="https://giavang.org/trong-nuoc/sjc/lich-su/" target="_blank" rel="noopener">giavang.org</a> <span class="src-meta">Cross-check 30 ngày: 19/30 khớp exact, 11/30 lệch ≤0,4%</span></div></li>
      <li><div><strong>fawazahmed0 currency-api</strong> &mdash; USD/VND backup. <a href="https://github.com/fawazahmed0/exchange-api" target="_blank" rel="noopener">github.com/fawazahmed0</a> <span class="src-meta">Fill gap USDVND 2025-2026</span></div></li>
      <li><div><strong>vnstock</strong> (source VCI) &mdash; VN-Index lịch sử. <a href="https://vnstock.site" target="_blank" rel="noopener">vnstock.site</a> <span class="src-meta">4.233 ngày VNINDEX, 2009-2026</span></div></li>
      <li><div><strong>World Bank</strong> &mdash; CPI Việt Nam (FP.CPI.TOTL, 2010=100). <a href="https://api.worldbank.org/v2/country/VNM/indicator/FP.CPI.TOTL" target="_blank" rel="noopener">api.worldbank.org</a> <span class="src-meta">Cho tính inflation-adjusted return (★6)</span></div></li>
    </ol>
    <h3>II. Lý thuyết &amp; phương pháp luận</h3>
    <ol class="refs" start="5">
      <li><div><strong>Kahneman, D. &amp; Tversky, A.</strong> (1979) &mdash; &ldquo;Prospect Theory: An Analysis of Decision under Risk&rdquo;. <em>Econometrica</em> 47(2). <span class="src-meta">Loss aversion ~2:1</span></div></li>
      <li><div><strong>Shiller, R.</strong> (2000) &mdash; <em>Irrational Exuberance</em>. Princeton University Press. <span class="src-meta">Herd behavior, speculative bubbles</span></div></li>
      <li><div><strong>Thaler, R.</strong> (1985) &mdash; &ldquo;Mental Accounting and Consumer Choice&rdquo;. <em>Marketing Science</em> 4(3).</div></li>
    </ol>
    <div class="callout info">
      <h4>💡 Bản chất của báo cáo</h4>
      <p>Đây là <strong>ghi chép tự nghiên cứu</strong>, không phải tài liệu học thuật chuẩn mực hay khuyến nghị đầu tư. Mục tiêu là minh bạch hóa cơ chế để người đọc tự đánh giá. Số liệu full trong bộ dữ liệu <code>sjc-gold-history/</code> kèm bài.</p>
    </div>
  </section>''')

print(f"Built {len(SECTIONS)} sections total (18 chapters + refs)")

# ===================== ASSEMBLE =====================
# Minimap groups
def mm_group(letter, name, items):
    lis = "\n".join(
        f'      <li><a href="#{sid}"><span class="dot"></span>{label}</a></li>'
        for sid, label in items
    )
    return f'''  <div class="mm-group open" data-group="{letter}">
    <button class="mm-group-head"><span class="chev">▶</span> {name} <span class="gcount">{len(items)}</span></button>
    <ul class="mm-items">
{lis}
    </ul>
  </div>'''

MM_A = mm_group("a","Mở đầu",[("chuong-1","I — Vàng VN đắt nhất thế giới?"),("chuong-2","II — 17 năm dữ liệu từ đâu")])
MM_B = mm_group("b","Lịch sử giá",[("chuong-3","III — 2009-2012 bình thường"),("chuong-4","IV — 2013-2015 tách biệt"),("chuong-5","V — 2016-2020 cân bằng"),("chuong-6","VI — 2020 COVID"),("chuong-7","VII — 2021-2022 đỉnh premium"),("chuong-8","VIII — 2023-2026 bình thường mới")])
MM_C = mm_group("c","Phân tích sâu",[("chuong-9","IX — Phân phối premium"),("chuong-10","X — 5 yếu tố premium"),("chuong-11","XI — Độ trễ QT→SJC"),("chuong-12","XII — Bid-ask spread"),("chuong-13","XIII — Volatility & drawdown"),("chuong-14","XIV — Nhẫn vs miếng"),("insight-1","★1 — Chênh lệch loại vàng"),("insight-2","★2 — Premium co giãn vì gì"),("insight-3","★3 — SJC vs VN-Index"),("insight-4","★4 — Rủi ro drawdown")])
MM_D = mm_group("d","Góc nhìn & kết",[("chuong-15","XV — Tâm lý trú ẩn"),("chuong-16","XVI — 3-tier cascade"),("insight-5","★5 — Đọc trạng thái SJC"),("insight-6","★6 — Thực hư vàng SJC"),("chuong-17","XVII — Kết luận"),("phu-luc","📎 Phụ lục phương pháp"),("tai-lieu-tham-khao","📚 Tài liệu tham khảo")])

MINIMAP = f'''<aside class="minimap" id="minimap" aria-label="Mục lục điều hướng">
  <div class="mm-head"><span class="mm-title">Mục lục</span><span class="mm-pct" id="mmPct">0%</span></div>
  <div class="mm-search"><input type="text" id="mmSearch" placeholder="Lọc mục lục..." autocomplete="off"></div>
  <button class="mm-overlay-close" id="mmClose" aria-label="Đóng">✕</button>
{MM_A}
{MM_B}
{MM_C}
{MM_D}
  <div class="mm-no-result" id="mmNoResult">Không tìm thấy mục nào.</div>
</aside>

<button class="mm-fab" id="mmFab" aria-label="Mở mục lục">☰</button>
<button class="to-top" id="toTop" aria-label="Lên đầu trang">↑</button>
<button class="pres-btn" id="presBtn" aria-label="Trình chiếu" title="Trình chiếu">📽️</button>
<div class="progress-bar" id="progressBar"></div>

<div class="pres-overlay" id="presOverlay" aria-hidden="true">
  <div class="pres-top">
    <div class="pres-progress-bg"><div class="pres-progress-fill" id="presProgress"></div></div>
    <div class="pres-counter"><b id="presCurrent">1</b> / <span id="presTotal">18</span></div>
    <button class="pres-exit" id="presExit">✕ Thoát (ESC)</button>
  </div>
  <div class="pres-stage" id="presStage"></div>
  <div class="pres-hint">← → để chuyển slide · ESC để thoát</div>
  <div class="pres-bottom">
    <button class="pres-nav" id="presPrev" aria-label="Slide trước">←</button>
    <div class="pres-dots" id="presDots"></div>
    <button class="pres-nav" id="presNext" aria-label="Slide sau">→</button>
  </div>
</div>'''

HERO = '''<header class="hero">
  <span class="badge">Tự nghiên cứu · Số liệu 17 năm</span>
  <h1>Vàng Việt Nam 2009&ndash;2026: 17 năm tự sự</h1>
  <p class="sub">Giá vàng SJC từ 21 triệu (2009) đến đỉnh 191 triệu (2026) &mdash; và câu chuyện vì sao vàng Việt Nam luôn đắt hơn vàng thế giới.</p>
  <div class="meta">
    <span>🗓️ Cập nhật: 08/07/2026</span>
    <span>📐 Phạm vi: 22/07/2009 &ndash; 08/07/2026</span>
    <span>📚 18 chương · 10 biểu đồ</span>
  </div>
</header>'''

# SLIDES — section type for each chapter
SLIDE_IDS = [f"chuong-{i}" for i in range(1,15)] + ["insight-1","insight-2","insight-3","insight-4"] + ["chuong-15","chuong-16","insight-5","insight-6","chuong-17"] + ["phu-luc","tai-lieu-tham-khao"]
SLIDES_JS = "  const SLIDES = [\n" + ",\n".join(
    f"    {{type:'section',id:'{sid}'}}" for sid in SLIDE_IDS
) + "\n  ];"

# Navigation JS (reuse from template tail, after sample chart removed)
NAV_JS_START = tail_full.split("/* ============ NAVIGATION LOGIC ============", 1)[0].rsplit("</script>", 1)[0]
NAV_JS_AND_AFTER = "/* ============ NAVIGATION LOGIC ============" + tail_full.split("/* ============ NAVIGATION LOGIC ============", 1)[1]
# Replace the SLIDES array in nav part with ours
NAV_JS_AND_AFTER = NAV_JS_AND_AFTER.replace(
    NAV_JS_AND_AFTER[NAV_JS_AND_AFTER.index("const SLIDES"):NAV_JS_AND_AFTER.index("];")+2],
    SLIDES_JS.replace("  const SLIDES", "const SLIDES")
)

FOOTER = '''<footer>
  Vàng Việt Nam 2009&ndash;2026: 17 năm tự sự<br>
  Dựng bởi ZCode · Cập nhật 08/07/2026
</footer>'''

# Assemble final
CHART_SCRIPT = f'''<script>
{VIZ_CORE}
{tail_nav}
{CHARTS_JS}
</script>'''

BODY = f'''{HERO}
{APPENDIX_CSS}
<!-- ============================ MAIN ============================ -->
<main class="container">

{chr(10).join(SECTIONS)}

</main>

<!-- ============================ MINIMAP ============================ -->
{MINIMAP}

{FOOTER}

{CHART_SCRIPT}

{NAV_JS_AND_AFTER}
</body>
</html>'''

# Tail JS continues with navigation + presentation (already in NAV_JS_AND_AFTER)

final = HEAD + "\n" + BODY
out = ROOT / "index.html"
out.write_text(final)
print(f"\n✅ Built {out}")
print(f"   size: {out.stat().st_size:,} bytes")
print(f"   sections: {len(SECTIONS)}")
print(f"   charts: {len(charts)}")
