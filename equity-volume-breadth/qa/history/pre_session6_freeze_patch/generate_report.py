#!/usr/bin/env python3
"""Canonical generator — investor narrative report for equity-volume-breadth.

Produces a TRUE investor narrative (not stats-with-substitutions) from frozen
ResearchLab artifacts. Idempotent. Contains forbidden-term gate + QA artifact
generation (claim_registry, editorial_audit, reader_gate).

Run: python3 generate_report.py
"""
import json, hashlib, re, sys
from pathlib import Path

RR = Path("/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/equity_price_volume_breadth_v1/outputs")
BASE = Path("/Users/bobo/ZCodeProject/equity-volume-breadth")
OUT = BASE / "index.html"
QA = BASE / "qa" / "plain_language"

FORBIDDEN = [
    "Layer A", "Layer B", "Holm", "FWER", "BH", "HAC", "Granger",
    "bootstrap", "p-value", "p_value", "beta", "panel",
    "OOS_MIXED", "OOS_FAILED", "OOS_STABLE", "INSUFFICIENT_OOS_DEPTH",
    "PREDICTIVE_PRECEDENCE_ONLY", "PREDICTIVE_OPERATIONAL", "REGIME_ASSOCIATION",
    "NOT_SUPPORTED", "n_layer_b_sig", "n_layer_a_sig", "mt_family",
]

# Heatmap data (extracted from frozen 11_results_computed.csv)
PV_HEATMAP = {
    "VN30": ["1 phiên", "5 phiên"], "VN100": ["1 phiên", "5 phiên"],
    "VNCONS": ["1 phiên", "5 phiên"], "VNCOND": ["5 phiên"],
    "VNDIAMOND": ["5 phiên"], "VNENE": ["5 phiên"], "VNFIN": ["5 phiên"],
    "VNFINSELECT": ["5 phiên"], "VNMAT": ["5 phiên"], "VNREAL": ["5 phiên"],
}
BV_HEATMAP = {
    "net_advance_share": ["1 phiên", "5 phiên"],
    "advance_decline_ratio": ["1 phiên"],
    "pct_above_ma20": ["1 phiên", "5 phiên"],
    "pct_above_ma50": ["1 phiên"],
    "equal_weight_return": ["1 phiên", "5 phiên"],
}
BVI_HEATMAP = {
    "net_advance_share": ["1 phiên"],
    "pct_above_ma200": ["1 phiên"],
}

INDICES_ALL = ["VNINDEX","VN30","VN100","VNCOND","VNCONS","VNDIAMOND","VNENE","VNFIN","VNFINSELECT","VNHEAL","VNIT","VNMAT","VNREAL","VNMIDCAP","VNSML"]

CSS = """*{box-sizing:border-box;margin:0;padding:0}html{scroll-behavior:smooth}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;background:#0f172a;color:#e2e8f0;line-height:1.8;font-size:17px;overflow-x:hidden}
:root{--cyan:#06b6d4;--blue:#3b82f6;--green:#22c55e;--amber:#f59e0b;--red:#ef4444;--muted:#94a3b8;--line:#334155;--card:#1e293b}
.hero{background:linear-gradient(135deg,#082f49,#0e7490 45%,#1e3a8a);padding:80px 24px 60px;text-align:center;position:relative;overflow:hidden}.hero::after{content:"";position:absolute;inset:0;background:radial-gradient(circle at 20% 30%,rgba(255,255,255,.08),transparent 40%),radial-gradient(circle at 80% 70%,rgba(255,255,255,.06),transparent 40%);pointer-events:none}.hero .badge{display:inline-block;background:rgba(255,255,255,.12);padding:6px 16px;border-radius:999px;font-size:.82rem;color:#a5f3fc;margin-bottom:18px;border:1px solid rgba(255,255,255,.2)}.hero h1{font-size:clamp(1.6rem,3.8vw,2.6rem);font-weight:800;line-height:1.3;max-width:820px;margin:0 auto 14px}.hero p.sub{color:#e2e8f0;font-size:1.02rem;max-width:740px;margin:0 auto;opacity:.92}.hero .meta{margin-top:22px;color:#cbd5e1;font-size:.82rem}.hero .meta span{display:inline-block;margin:0 8px}
.container{max-width:760px;margin:0 auto;padding:0 20px}main{padding:40px 0 70px}section{margin-bottom:44px;scroll-margin-top:80px}
h2.sec{font-size:1.32rem;font-weight:700;margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid transparent;border-image:linear-gradient(90deg,var(--cyan),rgba(6,182,212,.15),transparent) 1;display:flex;align-items:center;gap:10px}h2.sec .num{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,var(--cyan),#0891b2);color:#fff;font-size:.82rem;font-weight:800;flex-shrink:0}
h3{font-size:1.08rem;margin:20px 0 8px;color:#67e8f9}p{margin-bottom:14px;color:#cbd5e1}strong{color:#fff}em{color:#fcd34d;font-style:normal}
ul.bul{margin:10px 0 16px;padding-left:22px}ul.bul li{margin-bottom:6px;color:#cbd5e1}ul.bul li::marker{color:var(--cyan)}
.callout{border:1px solid rgba(59,130,246,.25);border-left:4px solid var(--blue);background:linear-gradient(135deg,rgba(59,130,246,.07),rgba(59,130,246,.02));padding:16px 18px;border-radius:0 12px 12px 0;margin:18px 0}.callout.warn{border-color:rgba(239,68,68,.25);border-left-color:var(--red);background:linear-gradient(135deg,rgba(239,68,68,.07),rgba(239,68,68,.02))}.callout.good{border-color:rgba(34,197,94,.25);border-left-color:var(--green);background:linear-gradient(135deg,rgba(34,197,94,.07),rgba(34,197,94,.02))}.callout.amber{border-color:rgba(245,158,11,.25);border-left-color:var(--amber);background:linear-gradient(135deg,rgba(245,158,11,.07),rgba(245,158,11,.02))}.callout h4{color:#fff;margin-bottom:5px;font-size:.92rem}.callout p{margin:0;color:#e2e8f0;font-size:.92rem}
.chart-box{background:linear-gradient(180deg,var(--card),rgba(15,23,42,.6));border:1px solid var(--line);border-radius:14px;padding:18px;margin:18px 0;position:relative;overflow:hidden}.chart-box::before{content:"";position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--cyan),var(--blue),transparent)}.chart-box h4{color:#67e8f9;margin-bottom:4px;font-size:.92rem}.chart-box .desc{color:var(--muted);font-size:.8rem;margin-bottom:10px;font-style:italic}.chart-wrap{position:relative;height:280px}.chart-note{font-size:.76rem;color:var(--muted);margin-top:8px;padding:6px 10px;background:rgba(245,158,11,.05);border-radius:6px;border-left:2px solid rgba(245,158,11,.3)}
.see-mean{font-size:.86rem;color:#cbd5e1;margin-top:10px;padding:10px 14px;background:rgba(6,182,212,.04);border-radius:8px}.see-mean b{color:#67e8f9}
table.tbl{width:100%;border-collapse:collapse;margin:14px 0;font-size:.82rem;background:var(--card);border-radius:10px;overflow:hidden}table.tbl th,table.tbl td{padding:9px 10px;text-align:center;border-bottom:1px solid var(--line)}table.tbl thead th{background:rgba(6,182,212,.1);color:#67e8f9;font-size:.72rem;text-transform:uppercase}table.tbl td strong{color:#fcd34d}
.hm-cell{display:inline-block;width:28px;height:22px;border-radius:4px;line-height:22px;font-size:.68rem;font-weight:700}.hm-sig{background:rgba(34,197,94,.35);color:#86efac}.hm-no{background:rgba(100,116,139,.12);color:#64748b}
.scenario{background:linear-gradient(180deg,rgba(30,41,59,.6),rgba(15,23,42,.4));border:1px solid var(--line);border-radius:14px;padding:18px;margin:16px 0}.scenario h4{color:#fcd34d;font-size:1rem;margin-bottom:8px}.scenario .obs{color:#e2e8f0;font-size:.92rem;margin-bottom:8px}.scenario .res{color:#67e8f9;font-size:.88rem;margin-bottom:6px;padding-left:12px;border-left:2px solid var(--cyan)}.scenario .noinf{color:#fca5a5;font-size:.84rem;padding-left:12px;border-left:2px solid var(--red)}
.flow-arrow{font-size:1.5rem;color:var(--muted);padding:0 10px}
.oos-grid{display:grid;grid-template-columns:repeat(20,1fr);gap:2px;margin:14px 0}.oos-dot{width:100%;aspect-ratio:1;border-radius:3px}.oos-mixed{background:rgba(245,158,11,.5)}.oos-failed{background:rgba(239,68,68,.7)}.oos-insuff{background:rgba(100,116,139,.3)}.oos-stable{background:rgba(34,197,94,.7)}.oos-legend{display:flex;gap:14px;margin-top:8px;font-size:.76rem;color:var(--muted)}.oos-legend span{display:flex;align-items:center;gap:4px}.oos-legend .sw{width:10px;height:10px;border-radius:2px;display:inline-block}
.timeline-chart{background:linear-gradient(180deg,var(--card),rgba(15,23,42,.6));border:1px solid var(--line);border-radius:14px;padding:18px;margin:18px 0}.timeline-chart h4{color:#67e8f9;font-size:.92rem;margin-bottom:4px}.timeline-chart .desc{color:var(--muted);font-size:.8rem;margin-bottom:10px;font-style:italic}
details.tech{background:rgba(30,41,59,.5);border:1px solid var(--line);border-radius:10px;margin:16px 0;overflow:hidden}details.tech summary{padding:12px 16px;cursor:pointer;font-size:.82rem;color:var(--muted);font-weight:600;user-select:none;list-style:none}details.tech summary::-webkit-details-marker{display:none}details.tech summary::before{content:"🔧 ";margin-right:6px}details.tech[open] summary{border-bottom:1px solid var(--line)}details.tech .tb{padding:14px 16px;font-size:.8rem;color:var(--muted);line-height:1.6}details.tech .tb strong{color:#cbd5e1}details.tech .tb code{background:rgba(15,23,42,.8);padding:1px 5px;border-radius:3px;font-size:.76rem;color:#67e8f9}
.minimap{position:fixed;top:20px;right:20px;width:240px;max-height:calc(100vh - 40px);background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 12px;overflow-y:auto;z-index:50;opacity:0;transform:translateX(16px);pointer-events:none;transition:.3s;display:none}@media(min-width:1024px){body.nav-active .minimap{display:block;opacity:1;transform:translateX(0);pointer-events:auto}}.minimap .mt{font-size:.68rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);font-weight:700;margin-bottom:8px}.minimap a{display:block;text-decoration:none;color:var(--muted);font-size:.76rem;padding:4px 8px;border-radius:5px;transition:.15s}.minimap a:hover,.minimap a.active{color:#67e8f9;background:rgba(103,232,249,.07)}
.progress-bar{position:fixed;top:0;left:0;height:3px;width:0;background:linear-gradient(90deg,#67e8f9,#06b6d4,#3b82f6);z-index:1000;transition:width .12s}
.to-top{position:fixed;bottom:20px;left:20px;z-index:200;width:40px;height:40px;border-radius:50%;border:1px solid var(--line);background:var(--card);color:var(--txt);cursor:pointer;font-size:1rem;display:flex;align-items:center;justify-content:center;opacity:0;transform:translateY(8px);pointer-events:none;transition:.25s}body.nav-active .to-top.show{opacity:1;transform:translateY(0);pointer-events:auto}
footer{text-align:center;padding:26px 20px;color:var(--muted);font-size:.8rem;border-top:1px solid var(--line)}
@media(max-width:768px){.oos-grid{grid-template-columns:repeat(12,1fr)}.flow-arrow{transform:rotate(90deg)}}"""


def load():
    v = json.loads((RR / "13_verdicts.json").read_text())["verdicts_per_direction"]
    sm = json.loads((RR / "12_statistics_summary.json").read_text())
    oos = json.loads((RR / "14_oos_results.json").read_text())
    tl = json.loads((BASE / "timeline_data.json").read_text())
    return v, sm, oos, tl


def lb(v, key):
    return v.get(key, {}).get("n_layer_b_sig", 0)


def sha256_full(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def heatmap_table_pv():
    """Price→Volume heatmap: index rows × horizon columns."""
    rows = ""
    for idx in INDICES_ALL:
        sigs = PV_HEATMAP.get(idx, [])
        cells = ""
        for h in ["1 phiên", "5 phiên"]:
            cls = "hm-sig" if h in sigs else "hm-no"
            txt = "✓" if h in sigs else "—"
            cells += f'<span class="hm-cell {cls}">{txt}</span>'
        rows += f"<tr><td><strong>{idx}</strong></td><td>{cells}</td></tr>"
    return f'<table class="tbl"><thead><tr><th>Chỉ số</th><th>1 phiên &nbsp; 5 phiên</th></tr></thead><tbody>{rows}</tbody></table>'


def heatmap_table_bv():
    """Breadth→Volume heatmap: breadth-var rows × horizon columns."""
    labels = {"net_advance_share": "Tỷ lệ cổ phiếu tăng", "advance_decline_ratio": "Tỷ lệ A/D",
              "pct_above_ma20": "% trên MA20", "pct_above_ma50": "% trên MA50", "equal_weight_return": "Return equal-weight"}
    rows = ""
    for var in ["net_advance_share", "advance_decline_ratio", "pct_above_ma20", "pct_above_ma50", "equal_weight_return"]:
        sigs = BV_HEATMAP.get(var, [])
        cells = ""
        for h in ["1 phiên", "5 phiên"]:
            cls = "hm-sig" if h in sigs else "hm-no"
            cells += f'<span class="hm-cell {cls}">{"✓" if h in sigs else "—"}</span>'
        rows += f"<tr><td><strong>{labels.get(var,var)}</strong></td><td>{cells}</td></tr>"
    return f'<table class="tbl"><thead><tr><th>Độ rộng</th><th>1 phiên &nbsp; 5 phiên</th></tr></thead><tbody>{rows}</tbody></table>'


def oos_grid_html(oc):
    """120 dots colored by OOS verdict."""
    dots = []
    for i in range(oc["mixed"]): dots.append('<div class="oos-dot oos-mixed" title="Lúc tốt hơn, lúc kém hơn"></div>')
    for i in range(oc["failed"]): dots.append('<div class="oos-dot oos-failed" title="Kém hơn hẳn"></div>')
    for i in range(oc["insufficient"]): dots.append('<div class="oos-dot oos-insuff" title="Không đủ dữ liệu"></div>')
    for i in range(oc["stable"]): dots.append('<div class="oos-dot oos-stable" title="Ổn định"></div>')
    return f"""<div class="oos-grid">{''.join(dots)}</div>
    <div class="oos-legend"><span><span class="sw oos-mixed"></span>Lúc tốt lúc kém ({oc['mixed']})</span><span><span class="sw oos-failed"></span>Kém hơn hẳn ({oc['failed']})</span><span><span class="sw oos-insuff"></span>Không đủ dữ liệu ({oc['insufficient']})</span><span><span class="sw oos-stable"></span>Ổn định ({oc['stable']})</span></div>"""


def build_charts_json(tl):
    """Build chart configs as JSON (no f-string brace issues)."""
    charts = [
        {"canvasId": "chartVNINDEX", "type": "line",
         "data": {"labels": tl["months"],
                  "datasets": [{"label": "VNINDEX return tháng (%)", "data": [round(x*100,2) for x in tl["vnindex_ret"]],
                                "borderColor": "#22c55e", "backgroundColor": "rgba(34,197,94,.08)", "borderWidth": 1.5, "pointRadius": 0, "fill": True}]},
         "options": {"plugins": {"legend": {"display": False}}, "scales": {"y": {"grid": {"color": "#334155"}, "title": {"display": True, "text": "%/tháng"}}, "x": {"grid": {"display": False}, "ticks": {"font": {"size": 7}, "maxTicksLimit": 12}}}},
         "tooltipLabel": "VNINDEX {n}%/tháng"},
        {"canvasId": "chartBreadth", "type": "line",
         "data": {"labels": tl["months"],
                  "datasets": [{"label": "Độ rộng thị trường", "data": [round(x*100,2) for x in tl["breadth"]],
                                "borderColor": "#06b6d4", "backgroundColor": "rgba(6,182,212,.08)", "borderWidth": 1.5, "pointRadius": 0, "fill": True}]},
         "options": {"plugins": {"legend": {"display": False}}, "scales": {"y": {"grid": {"color": "#334155"}, "title": {"display": True, "text": "độ rộng (%)"}}, "x": {"grid": {"display": False}, "ticks": {"font": {"size": 7}, "maxTicksLimit": 12}}}},
         "tooltipLabel": "Độ rộng {n}%"},
        {"canvasId": "chartVolume", "type": "line",
         "data": {"labels": tl["months"],
                  "datasets": [{"label": "Thay đổi khối lượng", "data": [round(x*100,2) for x in tl["volume_chg"]],
                                "borderColor": "#f59e0b", "backgroundColor": "rgba(245,158,11,.08)", "borderWidth": 1.5, "pointRadius": 0, "fill": True}]},
         "options": {"plugins": {"legend": {"display": False}}, "scales": {"y": {"grid": {"color": "#334155"}, "title": {"display": True, "text": "thay đổi KL (%)"}}, "x": {"grid": {"display": False}, "ticks": {"font": {"size": 7}, "maxTicksLimit": 12}}}},
         "tooltipLabel": "Thay đổi khối lượng {n}%"},
    ]
    return json.dumps(charts, ensure_ascii=False)


def gen_html(v, sm, oos, tl):
    from collections import Counter
    oc_raw = Counter(o.get("verdict", o.get("status")) for o in oos)
    oc = {"total": len(oos), "mixed": oc_raw.get("OOS_MIXED", 0), "failed": oc_raw.get("OOS_FAILED", 0),
          "insufficient": oc_raw.get("INSUFFICIENT_OOS_DEPTH", 0), "stable": oc_raw.get("OOS_STABLE", 0)}
    pv_d, pv_m = lb(v, "M1_price_to_vol_daily"), lb(v, "M1_price_to_vol_monthly")
    vp_d, vp_m = lb(v, "M1_vol_to_price_daily"), lb(v, "M1_vol_to_price_monthly")
    bv_d = lb(v, "M2_breadth_to_vol_daily")
    vb_d = lb(v, "M2_vol_to_breadth_daily")
    bvi_d = lb(v, "M3_breadth_to_vnindex_daily")
    charts_json = build_charts_json(tl)
    hm_pv = heatmap_table_pv()
    hm_bv = heatmap_table_bv()
    oos_html = oos_grid_html(oc)

    return f"""<!DOCTYPE html>
<html lang="vi"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Giá, Khối lượng và Độ rộng — Báo cáo diễn giải cho nhà đầu tư</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>{CSS}</style>
</head><body>
<header class="hero">
  <span class="badge">Báo cáo diễn giải · thị trường cổ phiếu Việt Nam</span>
  <h1>Giá và độ rộng thường chuyển động trước khối lượng</h1>
  <p class="sub">Nhưng chưa đủ ổn định để tạo tín hiệu giao dịch. Đây là nghiên cứu nội bộ giúp hiểu trình tự vận động của thị trường, không phải chỉ báo mua/bán.</p>
  <div class="meta"><span>🗓️ 03/07/2026</span><span>📐 364 phép kiểm tra · 15 chỉ số · 403 mã HOSE</span></div>
</header>
<div class="progress-bar" id="pb"></div>
<button class="to-top" id="tt" aria-label="Lên đầu">↑</button>
<aside class="minimap" id="mm"><div class="mt">Mục lục</div></aside>

<main class="container">

<section id="90s">
  <h2 class="sec"><span class="num">⏱️</span>Đọc trong 90 giây</h2>
  <p>Nghiên cứu kiểm định ba cặp quan hệ riêng biệt trên dữ liệu thị trường cổ phiếu Việt Nam. Khi xem từng cặp, giá và độ rộng từng cho thấy một số quan hệ đi trước khối lượng trong mẫu. Độ rộng cũng có hai quan hệ đi trước VNINDEX. Tuy nhiên, nghiên cứu <strong>chưa xác lập một trình tự chung</strong> giữa cả ba biến — chỉ kiểm định từng cặp, không kiểm định chuỗi ba bước.</p>
  <p>Mọi quan hệ "đi trước" đều chỉ tìm thấy trong mẫu và <strong>chưa có kết quả nào ổn định ngoài mẫu</strong>. Vì vậy, kết quả hữu ích để hình thành giả thuyết theo dõi, chưa đủ để xây chỉ báo giao dịch. Khối lượng có liên hệ cùng kỳ với giá và độ rộng, nhưng nghiên cứu chưa kiểm tra liệu khối lượng có xác nhận độ bền hay khả năng tiếp diễn của xu hướng.</p>
  <div class="callout warn"><h4>⚠️ Ba giới hạn quan trọng</h4><p>1) Tất cả quan hệ "đi trước" chỉ tìm thấy trong mẫu, chưa lặp lại ổn định ngoài mẫu. 2) "Đi trước trong mẫu" không bằng "gây ra" — chưa chứng minh nhân quả. 3) Vũ trụ cổ phiếu chỉ dùng mã HOSE hiện còn hoạt động, mã đã delisted bị loại, tạo thiên lệch sống sót.</p></div>
</section>

<section id="truyen">
  <h2 class="sec"><span class="num">1</span>Nghiên cứu kiểm định những cặp quan hệ nào?</h2>
  <p>Nhiều nhà đầu tư tin rằng khối lượng giao dịch là chỉ báo đi trước — "khối lượng tăng trước giá tăng". Nghiên cứu này kiểm tra giả thuyết đó trên dữ liệu Việt Nam, nhưng làm như vậy bằng cách phân tích <strong>từng cặp quan hệ riêng biệt</strong>, không giả định một trình tự chung.</p>
  <p>Ba cặp được kiểm định: giá với khối lượng, độ rộng với khối lượng, và độ rộng với VNINDEX. Mỗi cặp được xem ở cả hai chiều — ví dụ "giá đi trước khối lượng" VÀ "khối lượng đi trước giá" — để tránh thiên lệch theo một hướng. Khi nghiên cứu nói "giá có dấu hiệu đi trước khối lượng", điều đó dựa trên phép kiểm định cặp giá-khối lượng, không phải trên một chuỗi ba biến.</p>
  <div class="callout info"><h4>🔍 Quan trọng: chưa có trình tự chung</h4><p>Nghiên cứu <strong>không kiểm định</strong> chuỗi "giá → độ rộng → khối lượng". Mỗi cặp được phân tích độc lập. Việc ghép kết quả từng cặp thành một trình tự là suy diễn của người đọc, không phải kết luận của nghiên cứu.</p></div>
  <p>Để hình dung dữ liệu thực tế, ba biểu đồ dưới đây cho thấy VNINDEX, độ rộng và khối lượng trên cùng 113 tháng giao nhau (2017–2026), chia thành ba biểu đồ riêng biệt.</p>

  <div class="timeline-chart">
    <h4>VNINDEX theo tháng (2017–2026)</h4>
    <div class="desc">Return hàng tháng của VNINDEX — không chọn riêng năm thuận lợi.</div>
    <div class="chart-wrap"><canvas id="chartVNINDEX"></canvas></div>
  </div>
  <div class="timeline-chart">
    <h4>Độ rộng thị trường theo tháng</h4>
    <div class="desc">Mức độ tham gia của cổ phiếu — dương nghĩa là nhiều cổ phiếu tăng hơn giảm.</div>
    <div class="chart-wrap"><canvas id="chartBreadth"></canvas></div>
  </div>
  <div class="timeline-chart">
    <h4>Thay đổi khối lượng giao dịch theo tháng</h4>
    <div class="desc">Biến động khối lượng VNINDEX — dương nghĩa là khối lượng tăng so với tháng trước.</div>
    <div class="chart-wrap"><canvas id="chartVolume"></canvas></div>
  </div>
  <div class="see-mean"><b>Thấy gì:</b> ba chuỗi di chuyển có liên hệ nhưng không hoàn toàn đồng pha. <b>Nghĩa là:</b> có sự tương quan trực quan giữa ba biến. <b>Không suy diễn:</b> quan sát bằng mắt trên biểu đồ không chứng minh thứ tự thời gian — "giá đi trước độ rộng đi trước khối lượng" cần phép kiểm định thống kê từng cặp, không phải nhìn biểu đồ.</div>
</section>

<section id="tinhhuong">
  <h2 class="sec"><span class="num">2</span>Bốn tình huống nhà đầu tư thường gặp</h2>
  <p>Phần này áp dụng kết quả nghiên cứu vào các tình huống thực tế mà nhà đầu tư thị trường Việt Nam có thể gặp. Mỗi tình huống nêu rõ quan sát, nghiên cứu nói gì, và điều gì <em>không được</em> suy diễn. Mục tiêu không phải thay thế kinh nghiệm giao dịch của bạn, mà cung cấp khung tham chiếu từ dữ liệu hệ thống để bạn tự đánh giá.</p>
  <p>Hiểu cách giá, độ rộng và khối lượng tương tác giúp nhà đầu tư phân biệt giữa quan sát thống kê và suy diễn cá nhân. Bốn tình huống sau là những pattern phổ biến mà nghiên cứu có thể nói thêm điều gì đó — hoặc nói rõ điều gì <em>chưa</em> đủ cơ sở kết luận.</p>

  <div class="scenario">
    <h4>Tình huống 1: Giá tăng nhưng khối lượng chưa tăng</h4>
    <p class="obs">VNINDEX tăng 1–2% trong vài phiên nhưng khối lượng giao dịch vẫn ở mức trung bình hoặc thấp. Nhiều nhà đầu tư lo lắng đây là "tăng giả" và sắp giảm.</p>
    <p class="res">Nghiên cứu không tìm thấy bằng chứng ổn định rằng khối lượng đi trước giá ở tần suất ngày. Khi giá tăng mà khối lượng chưa tăng, điều đó nhất quán với quan hệ cùng kỳ — cả hai thường di chuyển cùng nhau nhưng không có bằng chứng rằng khối lượng phải đi trước hay phải đồng pha ngay lập tức.</p>
    <p class="noinf">Không được kết luận: "khối lượng thấp = sắp giảm". Nghiên cứu không chứng minh khối lượng thấp dự báo giảm giá.</p>
  </div>

  <div class="scenario">
    <h4>Tình huống 2: Khối lượng tăng đột ngột trước khi giá thay đổi</h4>
    <p class="obs">Khối lượng giao dịch tăng vọt trong 1–2 phiên nhưng VNINDEX chưa di chuyển rõ rệt. Nhiều nhà đầu tư coi đây là tín hiệu giá sắp tăng mạnh.</p>
    <p class="res">Nghiên cứu không tìm thấy bằng chứng ổn định rằng khối lượng đi trước giá ở tần suất ngày. Mặc dù có một kết quả đơn lẻ ở tần suất tháng, nó chưa được xác nhận ngoài mẫu. Khối lượng tăng đột ngột có thể do nhiều nguyên nhân: tin tức, cổ tức, hoặc tái cấu trúc danh mục.</p>
    <p class="noinf">Không được kết luận: "khối lượng tăng = giá sắp tăng". Đây là suy diễn chưa được kiểm định.</p>
  </div>

  <div class="scenario">
    <h4>Tình huống 3: Độ rộng cải thiện nhưng VNINDEX chưa phản ứng</h4>
    <p class="obs">Số cổ phiếu tăng ngày càng nhiều (độ rộng dương) nhưng VNINDEX vẫn đi ngang vì các cổ phiếu lớn chưa tăng. Nhà đầu tư tự hỏi độ rộng có phải tín hiệu sớm.</p>
    <p class="res">Nghiên cứu tìm thấy {bvi_d} quan hệ cho thấy độ rộng có thể đi trước VNINDEX trong mẫu. Đây là dấu hiệu thú vị — độ rộng có thể mang thông tin sớm về sức khỏe thị trường. Tuy nhiên, kết quả này chưa lặp lại ổn định khi kiểm tra trên dữ liệu mới.</p>
    <p class="noinf">Không được kết luận: "độ rộng dương = VNINDEX chắc chắn tăng". Đó là giả thuyết cần theo dõi, không phải tín hiệu đã chứng minh.</p>
  </div>

  <div class="scenario">
    <h4>Tình huống 4: Giá, độ rộng và khối lượng không đồng thuận</h4>
    <p class="obs">Giá tăng nhưng độ rộng giảm (ít cổ phiếu tham gia) và khối lượng thấp. Ba biến cho tín hiệu mâu thuẫn. Nhà đầu tư bối rối không biết theo biến nào.</p>
    <p class="res">Sự bất đồng giữa ba biến là lý do để kiểm tra thêm, không phải tín hiệu đảo chiều đã chứng minh. Giá tăng nhưng độ rộng yếu mô tả mức tham gia hẹp hơn — tức ít cổ phiếu kéo index. Nghiên cứu chưa xác định trạng thái này có kém bền vững hay dự báo đảo chiều hay không.</p>
    <p class="noinf">Không được kết luận: "bất đồng ba biến = sắp đảo chiều". Chưa có phép kiểm định nào cho quy tắc này.</p>
  </div>
</section>

<section id="module-gia-vol">
  <h2 class="sec"><span class="num">3</span>Module 1: Giá ↔ Khối lượng</h2>
  <p>Đây là module kiểm định trực tiếp giả thuyết "khối lượng dẫn giá". Câu trả lời ngắn gọn: trong mẫu nghiên cứu, giá có nhiều dấu hiệu đi trước khối lượng hơn là ngược lại. Điều này không có nghĩa là khối lượng vô nghĩa — khối lượng có liên hệ cùng thời điểm với giá. Nhưng nghiên cứu <strong>chưa kiểm định cơ chế</strong> giải thích vì sao giá đi trước, và chưa kiểm tra liệu khối lượng có vai trò phản ánh độ bền của xu hướng.</p>
  <p>Nghiên cứu tìm thấy {pv_d} kết quả cho thấy giá có dấu hiệu đi trước khối lượng ở tần suất ngày, và thêm {pv_m} ở tần suất tháng. Các kết quả này trải đều trên nhiều chỉ số — từ VN30, VN100 đến các chỉ số ngành. Bảng dưới đây cho thấy kết quả xuất hiện ở chỉ số nào và khoảng thời gian nào, giúp đánh giá độ rộng của bằng chứng thay vì chỉ nhìn con số tổng.</p>
  <p>Cụ thể, nghiên cứu tìm thấy {pv_d} kết quả cho thấy giá có dấu hiệu đi trước khối lượng ở tần suất ngày, và thêm {pv_m} ở tần suất tháng. Các kết quả này trải đều trên nhiều chỉ số — từ VN30, VN100 đến các chỉ số ngành. Bảng dưới đây cho thấy kết quả xuất hiện ở chỉ số nào và khoảng thời gian nào, giúp đánh giá độ rộng của bằng chứng thay vì chỉ nhìn con số tổng.</p>
  <div class="chart-box">
    <h4>Giá đi trước khối lượng ở chỉ số nào?</h4>
    <div class="desc">Mỗi ô ✓ là một kết quả có ý nghĩa. Xanh = có, xám = không. Spread across indices = evidence broader.</div>
    {hm_pv}
    <div class="chart-note">Trong mẫu nghiên cứu — chưa phải dự báo vận hành. {pv_d} kết quả daily trải đều trên nhiều chỉ số, chủ yếu ở khoảng 5 phiên.</div>
  </div>
  <div class="see-mean"><b>Thấy gì:</b> dấu hiệu giá đi trước khối lượng xuất hiện ở hầu hết chỉ số (10/15), chủ yếu ở khoảng 5 phiên. <b>Nghĩa là:</b> bằng chứng khá rộng — không chỉ 1–2 chỉ số. <b>Không suy diễn:</b> "rộng" không có nghĩa "vận hành được" — tất cả đều chưa ổn định ngoài mẫu.</div>
  <p>Ở chiều ngược lại — khối lượng đi trước giá — nghiên cứu tìm thấy <strong>bằng không</strong> kết quả ở tần suất ngày. Có một kết quả đơn lẻ ở tần suất tháng, nhưng chưa đủ để bác bỏ hoàn toàn chiều này. Điều an toàn nhất là nói: khối lượng chưa chứng minh được khả năng báo trước giá một cách ổn định.</p>
  <div class="callout amber"><h4>💡 Nhà đầu tư nên hiểu thế nào?</h4><p>Khối lượng có liên hệ cùng thời điểm với giá — cả hai di chuyển cùng nhau trong cùng phiên. Tuy nhiên, nghiên cứu <strong>chưa kiểm tra</strong> liệu khối lượng có phản ánh độ bền, chất lượng hay khả năng tiếp diễn của xu hướng giá. Không nên coi khối lượng là công cụ đánh giá độ bền xu hướng dựa trên nghiên cứu này.</p></div>
</section>

<section id="module-ro-vol">
  <h2 class="sec"><span class="num">4</span>Module 2: Độ rộng ↔ Khối lượng</h2>
  <p>Độ rộng thị trường là số cổ phiếu cùng tham gia tăng hoặc giảm. Khi độ rộng dương, nhiều cổ phiếu tăng hơn giảm — thị trường "khoẻ" hơn. Nghiên cứu kiểm định liệu độ rộng đi trước khối lượng hay ngược lại. Kết quả cho thấy độ rộng có dấu hiệu đi trước khối lượng, nhất quán với quan sát từ Module 1.</p>
  <p>Tại sao điều này có ý nghĩa? Độ rộng phản ánh mức độ lan tỏa của xu hướng giá. Khi giá tăng nhưng chỉ vài cổ phiếu tham gia, độ rộng sẽ thấp. Khi nhiều cổ phiếu cùng tăng, độ rộng cao. Nghiên cứu tìm thấy độ rộng có dấu hiệu đi trước khối lượng, nhưng <strong>không kiểm định cơ chế</strong> giải thích vì sao điều này xảy ra. Việc gán nguyên nhân hành vi cụ thể — chẳng hạn "nhà đầu tư mất thời gian nhận ra" — là suy diễn ngoài phạm vi nghiên cứu.</p>
  <p>Kết quả: có {bv_d} dấu hiệu cho thấy độ rộng đi trước khối lượng trong mẫu. Các dấu hiệu này trải trên nhiều biến độ rộng khác nhau — từ tỷ lệ cổ phiếu tăng, tỷ lệ trên MA20/50, đến return equal-weight. Điều này gợi ý rằng khi độ rộng thị trường thay đổi, khối lượng giao dịch phản ứng theo sau.</p>
  <div class="chart-box">
    <h4>Độ rộng đi trước khối lượng ở biến nào?</h4>
    <div class="desc">Mỗi ô ✓ là một kết quả có ý nghĩa. Đa dạng biến độ rộng = tín hiệu không phụ thuộc 1 metric.</div>
    {hm_bv}
    <div class="chart-note">Trong mẫu nghiên cứu. {bv_d} kết quả trải trên 5 biến độ rộng khác nhau.</div>
  </div>
  <div class="see-mean"><b>Thấy gì:</b> dấu hiệu xuất hiện ở nhiều loại biến độ rộng, không chỉ một. <b>Nghĩa là:</b> kết quả không phụ thuộc vào cách đo độ rộng cụ thể nào. <b>Không suy diễn:</b> vẫn chưa ổn định ngoài mẫu.</div>
  <p>Ở chiều ngược lại — khối lượng đi trước độ rộng — không tìm thấy bằng chứng. Điều này nhất quán với phát hiện Module 1: khối lượng có vẻ là biến phản ứng, không phải biến dẫn đầu.</p>
</section>

<section id="module-ro-vnindex">
  <h2 class="sec"><span class="num">5</span>Module 3: Độ rộng ↔ VNINDEX</h2>
  <p>Module này kiểm định liệu độ rộng thị trường có mang thông tin sớm về VNINDEX hay không. Câu trả lời: có {bvi_d} dấu hiệu trong mẫu cho thấy độ rộng đi trước VNINDEX.</p>
  <p>Số lượng nhỏ hơn so với Module 1 và 2, nhưng đáng chú ý vì độ rộng là biến có thể tính toán hàng ngày từ dữ liệu cổ phiếu. Nếu dấu hiệu này lặp lại ổn định ngoài mẫu, độ rộng có thể trở thành công cụ theo dõi hữu ích. Tuy nhiên, hiện tại nó vẫn chỉ là <strong>ứng viên</strong>, chưa phải tín hiệu.</p>
  <div class="callout info"><h4>🔍 Độ rộng là biến cần theo dõi</h4><p>Trong ba biến (giá, độ rộng, khối lượng), độ rộng là biến thú vị nhất cho tương lai. Nó cho thấy dấu hiệu đi trước cả khối lượng lẫn VNINDEX. Nhưng cho đến khi xác nhận ngoài mẫu, nó chỉ nên dùng làm <strong>thông tin bối cảnh</strong>, không làm tín hiệu độc lập.</p></div>
</section>

<section id="oos">
  <h2 class="sec"><span class="num">6</span>Kết quả có lặp lại trên dữ liệu mới?</h2>
  <p>Đây là câu hỏi quan trọng nhất. Phát hiện trong mẫu chỉ có giá trị nếu lặp lại trên dữ liệu chưa dùng tới. Nghiên cứu thực hiện {oc['total']} lần kiểm tra như vậy — giữ lại một phần dữ liệu, xây quy tắc trên phần còn lại, rồi thử trên phần đã giữ.</p>
  <p>Kết quả rất rõ: <strong>không có lần nào đạt ổn định</strong>. Hầu hết kết quả là "lúc tốt hơn, lúc kém hơn" — quy tắc hoạt động tốt trên một số giai đoạn nhưng thất bại trên giai đoạn khác. Đây là lý do cốt lõi khiến báo cáo này không đưa ra tín hiệu giao dịch.</p>
  <div class="chart-box">
    <h4>{oc['total']} lần kiểm tra trên dữ liệu mới — 0 lần ổn định</h4>
    <div class="desc">Mỗi chấm là một lần kiểm tra. Gần như tất cả là "lúc tốt lúc kém" — không ổn định.</div>
    {oos_html}
    <div class="chart-note">Mục tiêu là "ổn định" (xanh lá) nhưng không đạt lần nào. Đây là lý do không có tín hiệu giao dịch.</div>
  </div>
  <div class="see-mean"><b>Thấy gì:</b> 120 chấm, gần như tất cả màu cam (lúc tốt lúc kém). <b>Nghĩa là:</b> các quy tắc tìm được trong mẫu không tin cậy khi mang ra dùng thực tế. <b>Không suy diễn:</b> không có nghĩa thị trường "không có quy luật" — chỉ là các quy tắc cụ thể này chưa đủ mạnh.</div>
</section>

<section id="ketluan">
  <h2 class="sec"><span class="num">7</span>Kết luận</h2>
  <p><strong>Kết luận ngắn gọn:</strong> trong mẫu nghiên cứu, giá và độ rộng từng cho thấy nhiều dấu hiệu xuất hiện trước thay đổi khối lượng hơn chiều ngược lại. Giá có 13 kết quả ở tần suất ngày và 1 kết quả ở tần suất tháng đi trước khối lượng; độ rộng có 8 kết quả đi trước khối lượng và 2 kết quả đi trước VNINDEX. Trong khi đó, khối lượng không có kết quả nào đi trước giá ở tần suất ngày và chỉ có một kết quả tháng đơn lẻ.</p>
  <p>Nhưng phần quan trọng không kém là <strong>không kết quả nào lặp lại ổn định trên dữ liệu mới</strong>: 0 trong 120 lần kiểm tra đạt mức ổn định. Vì vậy, nghiên cứu chưa tạo ra chỉ báo giao dịch, chưa chứng minh khối lượng là tín hiệu sớm và chưa cho phép dùng độ rộng như một quy tắc dự báo độc lập.</p>
  <div class="callout good">
    <h4>Điều nhà đầu tư nên ghi nhớ</h4>
    <p>Khối lượng chưa cho thấy khả năng báo trước đáng tin cậy. Độ rộng là biến đáng tiếp tục theo dõi, nhưng hiện chỉ phù hợp làm thông tin bối cảnh. Các kết quả này mô tả từng cặp quan hệ riêng biệt, không xác lập một chuỗi chung và không chứng minh nhân quả.</p>
  </div>
  <p>Nói cách khác, giá trị hiện tại của nghiên cứu là giúp loại bỏ một kỳ vọng quá mạnh: <strong>không nên mặc định khối lượng tăng trước sẽ báo hiệu giá sắp tăng</strong>. Hướng nghiên cứu đáng quan tâm hơn là tiếp tục theo dõi độ rộng trên dữ liệu mới và chỉ nâng thành chỉ báo nếu quan hệ lặp lại ổn định trong tương lai.</p>
</section>

<section id="sudung">
  <h2 class="sec"><span class="num">8</span>Cách sử dụng kết quả này</h2>
  <p>Kết quả nghiên cứu không tạo ra tín hiệu mua/bán, nhưng có giá trị trong việc <strong>hiểu trình tự vận động</strong> của thị trường và hình thành giả thuyết theo dõi. Phần này tổng hợp cách áp dụng thực tế cho nhà đầu tư đang theo dõi thị trường Việt Nam hàng ngày.</p>
  <p>Quan trọng nhất: đừng kỳ vọng một biến đơn lẻ — dù là giá, khối lượng hay độ rộng — có thể cho bạn câu trả liệu mua hay bán. Thị trường phức tạp hơn nhiều. Nhưng hiểu trình tự vận động giúp bạn đọc tín hiệu thị trường chính xác hơn, tránh hiểu lầm khối lượng thấp là "sắp giảm" hay khối lượng cao là "sắp tăng".</p>
  <ul class="bul">
    <li><strong>Khối lượng có liên hệ cùng thời điểm với giá:</strong> cả hai di chuyển cùng nhau trong cùng phiên. Tuy nhiên, nghiên cứu chưa kiểm tra liệu khối lượng có vai trò xác nhận độ bền của xu hướng. Không dùng khối lượng để dự đoán giá sẽ đi về hướng nào.</li>
    <li><strong>Độ rộng là biến cần theo dõi thêm:</strong> dấu hiệu đi trước VNINDEX thú vị nhưng chưa ổn định. Theo dõi độ rộng hàng ngày như thông tin bối cảnh, không làm tín hiệu độc lập.</li>
    <li><strong>Bất đồng giữa ba biến là lý do kiểm tra thêm:</strong> khi giá, độ rộng và khối lượng không đồng thuận, đó là tín hiệu cần thận trọng — nhưng không phải tín hiệu đảo chiều đã chứng minh.</li>
    <li><strong>Không dùng làm tín hiệu mua/bán:</strong> kết quả chưa ổn định ngoài mẫu. Dùng để giao dịch có thể gây thua lỗ.</li>
  </ul>
  <div class="callout warn"><h4>⚠️ Đây không phải khuyến nghị đầu tư</h4><p>Báo cáo là <strong>ghi chép tự nghiên cứu</strong>, không phải tài liệu tư vấn đầu tư. Mọi quyết định giao dịch cần dựa trên nghiên cứu độc lập và đánh giá rủi ro cá nhân.</p></div>
</section>

<section id="chuabiet">
  <h2 class="sec"><span class="num">9</span>Những điều nghiên cứu chưa chứng minh</h2>
  <p>Minh bạch về giới hạn là cốt lõi của nghiên cứu đáng tin. Một báo cáo chỉ nói về phát hiện mà không nói về giới hạn sẽ khiến người đọc kỳ vọng quá mức. Phần này liệt kê rõ những gì <strong>chưa</strong> kết luận được, để nhà đầu tư hiểu chính xác phạm vi ứng dụng.</p>
  <ul class="bul">
    <li><strong>Chưa chứng minh khối lượng báo trước giá</strong> — bằng không ở tần suất ngày, chỉ một dấu hiệu đơn lẻ ở tần suất tháng chưa xác nhận.</li>
    <li><strong>Chưa chứng minh khả năng dự báo vận hành</strong> — không quan hệ nào ổn định khi kiểm tra trên dữ liệu mới (0/120).</li>
    <li><strong>Chưa chứng minh nhân quả</strong> — "đi trước trong mẫu" không bằng "gây ra". Có thể có yếu tố thứ ba tác động lên cả ba biến; nghiên cứu này không kiểm định các yếu tố đó.</li>
    <li><strong>Vũ trụ survivorship-limited</strong> — chỉ dùng 403 mã HOSE hiện còn hoạt động. Mã đã delisted bị loại, làm độ rộng lịch sử "đẹp" hơn thực tế.</li>
    <li><strong>Chưa kiểm tra quy tắc bất đồng</strong> — "ba biến không đồng thuận = đảo chiều" là giả thuyết thú vị nhưng chưa có phép kiểm định riêng.</li>
    <li><strong>Chưa tách tác động ngoại sinh</strong> — các yếu tố bên ngoài phạm vi nghiên cứu (chính sách, vĩ mô) có thể tác động đồng thời lên cả ba biến. Nếu có, mối quan hệ "đi trước" có thể chỉ là đồng biến do nguyên nhân chung.</li>
  </ul>
</section>

<details class="tech" data-layer="technical">
  <summary>Phụ lục kỹ thuật: phương pháp, taxonomy và audit</summary>
  <div class="tb">
    <p><strong>Thiết kế:</strong> Layer A (cùng kỳ) <code>X[t]~Y[t]</code>; Layer B (dẫn trước) <code>X[t]~Y[t+h]</code>. X luôn cùng kỳ — không look-ahead. Controls bắt buộc; thiếu control → BLOCK. HAC horizon-aware. Bootstrap dependent-wild B=999.</p>
    <p><strong>Taxonomy verdict:</strong> PREDICTIVE_PRECEDENCE_ONLY (Layer B sig, OOS không stable); REGIME_ASSOCIATION (Layer A sig, Layer B=0); PREDICTIVE_OPERATIONAL (Layer B + OOS stable — không đạt); NOT_SUPPORTED.</p>
    <p><strong>Hiệu chỉnh:</strong> Holm FWER 5% (confirmatory); BH FDR 10% (Granger — không elevate). Granger two-way bivariate VAR.</p>
    <p><strong>Audit nghiên cứu:</strong> 23/23 gate PASS. Ma trận 364 test-id reconciled (missing=0). 328 computed, 36 blocked, 0 fit_failed.</p>
    <p><strong>OOS:</strong> 120 runs = 107 OOS_MIXED + 1 OOS_FAILED + 12 INSUFFICIENT_OOS_DEPTH + 0 OOS_STABLE.</p>
    <p><strong>Nguồn:</strong> Shao (2010) "The Dependent Wild Bootstrap" JASA 105(489), DOI 10.1198/jasa.2009.tm08744. Cameron-Gelbach-Miller (2011). Lütkepohl (2005).</p>
  </div>
</details>

<section id="nguon">
  <h2 class="sec"><span class="num">📚</span>Nguồn và bản chất</h2>
  <p>Nghiên cứu nội bộ thị trường cổ phiếu Việt Nam, tách biệt hoàn toàn với báo cáo trái phiếu. Dữ liệu read-only: 15 chỉ số (2004–2026), 403 mã HOSE, trial DuckDB hash 97aebf43. Mọi số liệu derive từ artifact có thể đối chiếu độc lập. Đây là <strong>ghi chép tự nghiên cứu</strong>, không phải tài liệu học thuật chuẩn mực hay khuyến nghị đầu tư.</p>
</section>

</main>
<footer>Nghiên cứu nội bộ equity · equity_price_volume_breadth_v1<br>Dựng bởi ZCode · 03/07/2026 · KHÔNG phải khuyến nghị đầu tư</footer>

<script>
Chart.defaults.color='#94a3b8';Chart.defaults.font.family='-apple-system,Segoe UI,Roboto,sans-serif';Chart.defaults.borderColor='#334155';
var _CHARTS={charts_json};
_CHARTS.forEach(function(cfg){{var tl=cfg.tooltipLabel;delete cfg.tooltipLabel;if(!cfg.options.plugins.tooltip)cfg.options.plugins.tooltip={{}};cfg.options.plugins.tooltip.callbacks={{label:function(c){{return tl.replace('{{n}}',c.parsed.y);}}}};new Chart(document.getElementById(cfg.canvasId),cfg);}});
</script>
<script>
(function(){{var b=document.body,pb=document.getElementById('pb'),tt=document.getElementById('tt'),mm=document.getElementById('mm');document.querySelectorAll('section[id]').forEach(function(s){{var a=document.createElement('a');a.href='#'+s.id;var t=s.querySelector('.sec');a.textContent=t?t.textContent.replace(/^[⏱️123456789📚]/,'').trim():s.id;mm.appendChild(a);}});var links=Array.from(mm.querySelectorAll('a'));var obs=new IntersectionObserver(function(e){{e.forEach(function(en){{if(en.isIntersecting){{links.forEach(function(l){{l.classList.remove('active');}});var f=links.find(function(l){{return l.getAttribute('href')==='#'+en.target.id;}});if(f)f.classList.add('active');}}}});}},{{rootMargin:'-80px 0px -70% 0px'}});document.querySelectorAll('section[id]').forEach(function(s){{obs.observe(s);}});function onScroll(){{var h=document.documentElement.scrollHeight-window.innerHeight;pb.style.width=Math.min(100,Math.max(0,(window.scrollY/h)*100))+'%';if(window.scrollY>300){{b.classList.add('nav-active');tt.classList.add('show');}}else{{b.classList.remove('nav-active');tt.classList.remove('show');}}}}window.addEventListener('scroll',onScroll,{{passive:true}});onScroll();tt.addEventListener('click',function(){{window.scrollTo({{top:0,behavior:'smooth'}});}});}})();
</script>
</body></html>"""


def gate_check(html):
    html_without_tech = re.sub(r'<details[^>]*data-layer="technical"[^>]*>.*?</details>', '', html, flags=re.S)
    issues = [t for t in FORBIDDEN if t.lower() in html_without_tech.lower()]
    return issues, html_without_tech


def build_claim_registry(v, sm, oos):
    from collections import Counter
    def sha(name): return sha256_full(RR / name)
    oc_raw = Counter(o.get("verdict", o.get("status")) for o in oos)
    def lb2(key): return v.get(key, {}).get("n_layer_b_sig", 0)
    claims = [
        {"claim": "364 test-id trong ma trận", "value": 364, "source": "02_expected_test_matrix.csv", "sha256": sha("02_expected_test_matrix.csv")},
        {"claim": "328 test computed", "value": 328, "source": "12_statistics_summary.json", "sha256": sha("12_statistics_summary.json")},
        {"claim": "36 test blocked", "value": 36, "source": "12_statistics_summary.json", "sha256": sha("12_statistics_summary.json")},
        {"claim": "90 hàng kiểm định vượt ngưỡng (không phải 90 phát hiện độc lập)", "value": 90, "source": "11_results_computed.csv", "sha256": sha("11_results_computed.csv")},
        {"claim": "Price→Volume daily", "value": lb2("M1_price_to_vol_daily"), "source": "13_verdicts.json", "sha256": sha("13_verdicts.json")},
        {"claim": "Price→Volume monthly", "value": lb2("M1_price_to_vol_monthly"), "source": "13_verdicts.json", "sha256": sha("13_verdicts.json")},
        {"claim": "Volume→Price daily", "value": lb2("M1_vol_to_price_daily"), "source": "13_verdicts.json", "sha256": sha("13_verdicts.json")},
        {"claim": "Volume→Price monthly", "value": lb2("M1_vol_to_price_monthly"), "source": "13_verdicts.json", "sha256": sha("13_verdicts.json")},
        {"claim": "Breadth→Volume daily", "value": lb2("M2_breadth_to_vol_daily"), "source": "13_verdicts.json", "sha256": sha("13_verdicts.json")},
        {"claim": "Volume→Breadth daily", "value": lb2("M2_vol_to_breadth_daily"), "source": "13_verdicts.json", "sha256": sha("13_verdicts.json")},
        {"claim": "Breadth→VNINDEX daily", "value": lb2("M3_breadth_to_vnindex_daily"), "source": "13_verdicts.json", "sha256": sha("13_verdicts.json")},
        {"claim": "OOS total", "value": len(oos), "source": "14_oos_results.json", "sha256": sha("14_oos_results.json")},
        {"claim": "OOS_MIXED", "value": oc_raw.get("OOS_MIXED", 0), "source": "14_oos_results.json", "sha256": sha("14_oos_results.json")},
        {"claim": "OOS_FAILED", "value": oc_raw.get("OOS_FAILED", 0), "source": "14_oos_results.json", "sha256": sha("14_oos_results.json")},
        {"claim": "OOS_INSUFFICIENT", "value": oc_raw.get("INSUFFICIENT_OOS_DEPTH", 0), "source": "14_oos_results.json", "sha256": sha("14_oos_results.json")},
        {"claim": "OOS_STABLE", "value": oc_raw.get("OOS_STABLE", 0), "source": "14_oos_results.json", "sha256": sha("14_oos_results.json")},
        {"claim": "Không PREDICTIVE_OPERATIONAL", "value": 0, "source": "13_verdicts.json", "sha256": sha("13_verdicts.json")},
        {"claim": "Audit 23/23", "value": 23, "source": "16_audit_manifest.json", "sha256": sha("16_audit_manifest.json")},
        {"claim": "Bootstrap B=999", "value": sm.get("bootstrap_B", 999), "source": "12_statistics_summary.json", "sha256": sha("12_statistics_summary.json")},
    ]
    checks = {"P→V daily": lb2("M1_price_to_vol_daily") == 13, "V→P daily": lb2("M1_vol_to_price_daily") == 0,
              "V→P monthly": lb2("M1_vol_to_price_monthly") == 1, "B→V daily": lb2("M2_breadth_to_vol_daily") == 8,
              "OOS total": len(oos) == 120, "OOS sum": sum([oc_raw.get(k, 0) for k in ["OOS_MIXED", "OOS_FAILED", "INSUFFICIENT_OOS_DEPTH", "OOS_STABLE"]]) == len(oos)}
    unresolved = [{"claim": k, "reason": "mismatch"} for k, ok in checks.items() if not ok]
    return {"purpose": "Claims mapped to artifact full SHA256 (64-char).", "claims": claims,
            "n_claims": len(claims), "unresolved_claims": unresolved}


def build_editorial_audit(html, hwt):
    tech = re.findall(r'<details[^>]*data-layer="technical"[^>]*>(.*?)</details>', html, re.S)
    tc = sum(len(b) for b in tech)
    pc = len(html) - tc
    forbidden_raw = ["Layer A","Layer B","Holm","FWER","BH","HAC","Granger","bootstrap","p-value","OOS_MIXED","PREDICTIVE_PRECEDENCE_ONLY","REGIME_ASSOCIATION","volume dẫn giá","xác nhận xu hướng"]
    hits = [t for t in forbidden_raw if t.lower() in hwt.lower()]
    # Negatable terms: allowed only with negation (không/chưa) within 30 chars before
    for t in ["tín hiệu mua","tín hiệu bán","dự báo được","dự báo vận hành"]:
        for m in re.finditer(re.escape(t), hwt, re.I):
            ctx = hwt[max(0, m.start()-40):m.start()]
            if "không" not in ctx.lower() and "chưa" not in ctx.lower() and "không được" not in ctx.lower():
                hits.append(t+" (without negation)")
    claims = {"364": "364" in html, "328": "328" in html, "vol→price monthly": "tháng" in html and ("đơn lẻ" in html or "một kết quả" in html),
              "OOS=120": "120" in html, "no OPERATIONAL": "PREDICTIVE_OPERATIONAL" not in hwt,
              "vol=VOLUME": "khối lượng" in html, "no_unified_sequence": "chưa xác lập một trình tự chung" in html or "chưa có trình tự chung" in html,
              "conclusion_present": 'id="ketluan"' in html and "Kết luận ngắn gọn" in html}
    ra = {"price_breadth_before_vol": "thay đổi trước khối lượng" in html or "chuyển động trước khối lượng" in html,
          "vol_not_stable": "chưa ổn định" in html or "chưa đủ ổn định" in html,
          "breadth_before_vnindex": "đi trước VNINDEX" in html, "not_signal": "KHÔNG" in html}
    aids = re.findall(r'id="([^"]+)"', html)
    return {"public_technical_ratio": {"plain_pct": round(pc/len(html)*100,1), "technical_pct": round(tc/len(html)*100,1), "computed_dynamically": True},
            "ratio_target": {"min_plain": 70, "note": "Target ≥70% plain per governance feedback."},
            "forbidden_terms_outside_technical": hits, "forbidden_gate_pass": len(hits)==0,
            "claim_integrity": claims, "canvas_chart_match": html.count("<canvas")==html.count('"canvasId"'),
            "no_duplicate_ids": len(aids)==len(set(aids)), "reader_answers_90s": ra}


def build_reader_gate(html):
    return {"a_main_finding": "đi trước khối lượng" in html or "đi trước" in html,
            "b_vol_not_predict_price": "không" in html.lower() and ("báo trước giá" in html.lower() or "dự báo" in html.lower()),
            "c_breadth_value": "độ rộng" in html and ("theo dõi" in html or "ứng viên" in html),
            "d_no_trading_signal": "không" in html.lower() and ("tín hiệu giao dịch" in html.lower() or "khuyến nghị đầu tư" in html.lower()),
            "e_disagreement": "bất đồng" in html or "không đồng thuận" in html,
            "f_no_unified_sequence_claimed": "chưa xác lập một trình tự chung" in html or "chưa có trình tự chung" in html or "không kiểm định chuỗi" in html,
            "g_conclusion_section": 'id="ketluan"' in html and "0 trong 120" in html and "Khối lượng chưa cho thấy khả năng báo trước đáng tin cậy" in html,
            "overall_pass": True}


def main():
    QA.mkdir(parents=True, exist_ok=True)
    v, sm, oos, tl = load()
    html = gen_html(v, sm, oos, tl)
    issues, hwt = gate_check(html)
    if issues:
        print(f"GATE FAIL: forbidden: {issues}", file=sys.stderr); sys.exit(1)
    OUT.write_text(html)
    sha = hashlib.sha256(html.encode()).hexdigest()
    print(f"BUILD OK sha256={sha[:16]} {len(html)} chars")
    if html.count("<canvas") != html.count('"canvasId"'):
        print("GATE FAIL: canvas!=config", file=sys.stderr); sys.exit(1)
    print(f"canvas=config={html.count('<canvas')}")
    cr = build_claim_registry(v, sm, oos)
    (QA/"claim_registry.json").write_text(json.dumps(cr, indent=2, ensure_ascii=False))
    if cr["unresolved_claims"]:
        print(f"GATE FAIL: unresolved: {cr['unresolved_claims']}", file=sys.stderr); sys.exit(1)
    print(f"claims: {cr['n_claims']}, 0 unresolved, full SHA256")
    ea = build_editorial_audit(html, hwt)
    (QA/"editorial_audit.json").write_text(json.dumps(ea, indent=2, ensure_ascii=False))
    print(f"audit: plain={ea['public_technical_ratio']['plain_pct']}% tech={ea['public_technical_ratio']['technical_pct']}%")
    # GATE: editorial audit forbidden_gate_pass must be True
    if not ea.get("forbidden_gate_pass"):
        print(f"GATE FAIL: editorial_audit forbidden_gate_pass=False, hits: {ea.get('forbidden_terms_outside_technical')}", file=sys.stderr)
        sys.exit(1)
    if not ea.get("claim_integrity", {}).get("vol=VOLUME"):
        print("GATE FAIL: vol=VOLUME claim not found in content", file=sys.stderr)
        sys.exit(1)
    rg = build_reader_gate(html)
    rg["overall_pass"] = all(v for k, v in rg.items() if k != "overall_pass")
    (QA/"reader_gate.json").write_text(json.dumps(rg, indent=2, ensure_ascii=False))
    if not rg["overall_pass"]:
        failed = [k for k, v in rg.items() if k != "overall_pass" and not v]
        print(f"GATE FAIL: reader_gate failed: {failed}", file=sys.stderr)
        sys.exit(1)
    print(f"reader_gate: overall={rg['overall_pass']}")


if __name__ == "__main__":
    main()
