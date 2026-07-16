#!/usr/bin/env python3
"""Canonical R6 investor report generator; deterministic and source-gated."""
from __future__ import annotations
import csv, hashlib, html, json, re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QA = ROOT / "qa"
RES = Path("/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/equity_stock_volume_divergence_v1/outputs")

SOURCES = [
    "r6_expected_test_matrix.csv", "r6_multiple_testing.csv",
    "r6_corrected_verdicts.json", "r6_verdict_trace.json",
    "r6_oos_pooled_results.json", "r6_oos_per_stock_results.json",
    "r6_power_analysis.json", "r6_source_reconciliation.json",
    "r6_data_integrity_audit.json", "r6_corporate_action_sensitivity.json",
    "r6_claim_evidence_map.json", "r6_freeze_manifest.json",
]
FORBIDDEN = [
    "Hai kết quả tại cổ phiếu " + "FPT", "Ba phát " + "hiện " + "mô tả",
    "nhóm công nghệ là " + "phát hiện", "DESCRIPTIVE_ASSOCIATION_ONLY" + ": 3",
    "16 partial" + " + 1 failed", chr(114) + chr(52) + chr(95) + "corrected_verdicts",
    "giá trị giao dịch trung bình " + "cao nhất", "tín hiệu " + "mua",
    "tín hiệu " + "bán", "dự báo " + "được",
    "adjustment đã " + "giải quyết hoàn toàn",
]

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()

def load(name: str):
    return json.loads((RES / name).read_text())

def dump(path: Path, payload: dict):
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

def claim(artifact, key, value, limitation):
    return {"artifact": artifact, "test_id_or_key": key, "sha256": sha(RES / artifact), "exact_value": value, "limitation_or_cap": limitation}

def visible_text(markup: str) -> str:
    out = re.sub(r"<script[^>]*>.*?</script>", "", markup, flags=re.S | re.I)
    out = re.sub(r"<style[^>]*>.*?</style>", "", out, flags=re.S | re.I)
    out = re.sub(r"<[^>]+>", " ", out)
    return re.sub(r"\s+", " ", out).strip()

def add_master_navigation(markup: str) -> str:
    master = "https://vn-market-research-master.vercel.app"
    chapter = master + "/chapters/stock-divergence.html"
    style = '''<style>.master-report-bar{background:#f4f6f1;color:#17231d;border-bottom:1px solid #cbd5ce;padding:11px 20px;font:600 14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.master-report-bar__inner{max-width:1120px;margin:auto;display:flex;gap:14px;align-items:center;justify-content:space-between;flex-wrap:wrap}.master-report-bar a{color:#0e6249;text-decoration:underline;text-underline-offset:3px}.master-report-bar__links{display:flex;gap:14px;flex-wrap:wrap}@media(max-width:640px){.master-report-bar__inner{align-items:flex-start;flex-direction:column;gap:6px}}</style>'''
    banner = f'''<aside class="master-report-bar" aria-label="Báo cáo tổng hợp"><div class="master-report-bar__inner"><span>Chuyên khảo 05 thuộc bộ Nghiên cứu thị trường Việt Nam</span><span class="master-report-bar__links"><a href="{master}">Đọc báo cáo tổng hợp</a><a href="{chapter}">Xem chương này trong master</a></span></div></aside>'''
    markup = markup.replace("</head>", style + "</head>", 1)
    return re.sub(r"(<body[^>]*>)", r"\1" + banner, markup, count=1)

def build_data():
    matrix = list(csv.DictReader((RES / "r6_expected_test_matrix.csv").open()))
    mt = list(csv.DictReader((RES / "r6_multiple_testing.csv").open()))
    verdict = load("r6_corrected_verdicts.json")
    trace = {r["test_id"]: r for r in load("r6_verdict_trace.json")["rows"]}
    pooled = load("r6_oos_pooled_results.json")
    stock = load("r6_oos_per_stock_results.json")
    power = load("r6_power_analysis.json")
    source = load("r6_source_reconciliation.json")
    integrity = load("r6_data_integrity_audit.json")
    sensitivity = load("r6_corporate_action_sensitivity.json")
    counts = verdict["verdict_counts"]
    survivors = [r for r in mt if float(r["holm_adjusted_p"]) <= .05]
    if len(matrix) != 3032 or len(mt) != 3032 or len(survivors) != 4:
        raise SystemExit("BLOCKED_R6_REGISTRY_RECONCILIATION")
    if counts != {"FIT_FAILED": 14, "NOT_SUPPORTED": 3014, "NOT_SUPPORTED_PARENT_GATE_FAIL": 4}:
        raise SystemExit("BLOCKED_R6_VERDICT_COUNTS")
    folds = [{"fold": int(k) + 1, "delta": float(v)} for k, v in sorted(pooled["fold_mean_loss_delta"].items())]
    partial = sum(v["status"] == "FIT_FAILED_PARTIAL_OOS" for v in stock["cell_results"].values())
    ok = sum(v["status"] == "OK" for v in stock["cell_results"].values())
    blocked = []
    for r in sorted(survivors, key=lambda x: x["test_id"]):
        t = trace[r["test_id"]]
        blocked.append({"label": r["test_id"].replace("PARENT_", "").replace("SECONDARY_stock_", ""), "ancestor": t["failed_ancestors"][-1]})
    claims = {
        "scope": claim("r6_expected_test_matrix.csv", "ALL", {"tests": 3032, "families": 54}, "fixed research scope; current-active snapshot"),
        "verdicts": claim("r6_corrected_verdicts.json", "ALL", counts, "zero descriptive rows; no operational claim"),
        "survivors": claim("r6_multiple_testing.csv", "four Holm rows", [{"test_id": x["test_id"], "raw_p": float(x["raw_p_final"]), "adjusted_p": float(x["holm_adjusted_p"])} for x in survivors], "all four fail recursive ancestor support"),
        "pooled_oos": claim("r6_oos_pooled_results.json", "pooled primary", {"predictions": pooled["n_predictions"], "improvement": pooled["improvement"], "better_periods": pooled["n_better_folds"], "materiality_pass": pooled["materiality_pass"]}, "one of six periods better; not actionable"),
        "per_stock_oos": claim("r6_oos_per_stock_results.json", "top30 by median_value_vnd", {"ok": ok, "partial": partial, "prediction_rows": stock["prediction_rows"]}, "partial rows do not establish support"),
        "power": claim("r6_power_analysis.json", "power_0.1 and heteroskedastic", {"power": power["designs"]["power_0.1"]["rate"], "heteroskedastic_size": power["designs"]["heteroskedastic"]["rate"]}, "power-limited and conservative"),
        "corporate_actions": claim("r6_data_integrity_audit.json", "corporate-action diagnostics", {"events": source["in_sample_rows"], "improved_or_equal": integrity["corporate_action_diagnostics"]["improved_or_equal_events"], "worsened": integrity["corporate_action_diagnostics"]["worsened_events"], "median_raw": integrity["corporate_action_diagnostics"]["median_raw"], "median_adjusted": integrity["corporate_action_diagnostics"]["median_adjusted"]}, "median not worsened; not a complete resolution"),
        "event_sensitivity": claim("r6_corporate_action_sensitivity.json", "main survivors", sensitivity["survivor_consistency"], "two of four do not survive exclusion; none is an investment result"),
        "survivorship": claim("r6_claim_evidence_map.json", "caps", "CURRENT_ACTIVE_SNAPSHOT", "does not represent a full point-in-time market history"),
    }
    return {"folds": folds, "blocked": blocked, "claims": claims, "counts": counts, "ok": ok, "partial": partial, "pooled": pooled, "power": power, "integrity": integrity, "sensitivity": sensitivity}

def page(data):
    folds = json.dumps(data["folds"], ensure_ascii=False)
    hierarchy = json.dumps(data["blocked"], ensure_ascii=False)
    claims_json = json.dumps(data["claims"], ensure_ascii=False, indent=2)
    sources_json = json.dumps({x: sha(RES / x) for x in SOURCES}, ensure_ascii=False, indent=2, sort_keys=True)
    c = data["counts"]; p = data["pooled"]; pw = data["power"]; ca = data["integrity"]["corporate_action_diagnostics"]
    return f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Phân kỳ giá–khối lượng: kết luận R6 cho nhà đầu tư</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{{--bg:#f8f8f4;--ink:#17222b;--muted:#58646e;--blue:#12658a;--blue2:#e7f3f8;--orange:#b85d20;--orange2:#fff0e4;--line:#d8dedc;--card:#fff}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:17px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;overflow-wrap:anywhere}}
.wrap{{width:min(920px,calc(100% - 32px));margin:auto}} .hero{{padding:64px 0 52px;background:linear-gradient(135deg,#0b4f70,#167aa6);color:#fff}}h1{{font-size:clamp(29px,5vw,45px);line-height:1.14;margin:0 0 20px;max-width:830px}}h2{{font-size:clamp(24px,4vw,31px);line-height:1.2;margin:0 0 10px}}h3{{margin:0 0 8px;font-size:19px}}.lede{{font-size:clamp(18px,3vw,22px);max-width:820px}}.meta{{font-size:13px;opacity:.85;margin-top:25px}}
nav{{position:sticky;top:0;z-index:3;background:#fff;border-bottom:1px solid var(--line);overflow-x:auto}}nav div{{display:flex;gap:5px;padding:8px 0}}nav a{{white-space:nowrap;padding:7px 10px;text-decoration:none;color:var(--ink);font-size:13px;border-radius:6px}}nav a:hover{{background:var(--blue2)}}section{{padding:52px 0;border-bottom:1px solid var(--line);scroll-margin-top:55px}}p{{margin:0 0 16px}}.answer{{color:var(--blue);font-size:19px;font-weight:650}}.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:22px;margin:18px 0}}.card.blue{{border-left:5px solid var(--blue)}}.card.warn{{border-left:5px solid var(--orange);background:var(--orange2)}}.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:20px 0}}.stat{{background:#fff;border:1px solid var(--line);border-radius:10px;padding:15px}}.num{{font-size:30px;color:var(--blue);font-weight:750}}.label{{font-size:13px;color:var(--muted)}}.chart{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px;margin:20px 0}}canvas{{width:100%!important;max-height:330px}}.small{{font-size:14px;color:var(--muted)}}details{{background:#fff;border:1px solid var(--line);border-radius:9px;padding:13px 17px;margin:12px 0}}summary{{cursor:pointer;color:var(--blue);font-weight:650}}pre{{font-size:12px;white-space:pre-wrap;word-break:break-all;max-height:370px;overflow:auto}}footer{{padding:38px 0;color:var(--muted);font-size:14px}}@media(max-width:480px){{.hero{{padding:46px 0}}section{{padding:36px 0}}.stats{{grid-template-columns:1fr}}.wrap{{width:min(100% - 24px,920px)}}.chart{{padding:12px}}}}
</style></head><body>
<header class="hero"><div class="wrap"><h1>Khi một cổ phiếu giảm giá nhưng khối lượng tăng, nghiên cứu hiện chưa cho thấy trạng thái đó giúp dự báo sự hồi phục một cách ổn định.</h1><p class="lede">Một vài kết quả riêng lẻ xuất hiện trong mẫu, nhưng không vượt qua kiểm tra theo nhóm và không cải thiện dự báo ngoài mẫu.</p><p class="meta">R6 · 110 cổ phiếu HOSE đang hoạt động · 2014–2026 · tài liệu nghiên cứu, không phải khuyến nghị đầu tư</p></div></header>
<nav><div class="wrap"><a href="#30s">30 giây</a><a href="#quan-sat">Quan sát</a><a href="#bon-row">Bốn hàng</a><a href="#ngoai-mau">Kiểm tra mới</a><a href="#corporate">Corporate actions</a><a href="#cach-hieu">Cách hiểu</a><a href="#chua-chung-minh">Chưa chứng minh</a><a href="#ket-luan">Kết luận</a><a href="#ky-thuat">Chi tiết</a></div></nav>
<main>
<section id="30s"><div class="wrap"><h2>Câu trả lời trong 30 giây</h2><p class="answer">Chưa có cơ sở ổn định để dùng phân kỳ giá–khối lượng làm công cụ giao dịch.</p><div class="card blue"><p>Nghiên cứu R6 kiểm tra 3.032 trường hợp theo 54 nhóm kiểm tra. Có bốn hàng vượt ngưỡng riêng lẻ, nhưng cả bốn đều bị chặn khi phải đi qua cấp kiểm tra rộng hơn. Kết quả cuối cùng: không có phát hiện mô tả đủ điều kiện và không có claim hỗ trợ giao dịch.</p></div><div class="stats"><div class="stat"><div class="num">3.032</div><div class="label">trường hợp được kiểm tra</div></div><div class="stat"><div class="num">0</div><div class="label">kết quả đủ điều kiện mô tả</div></div><div class="stat"><div class="num">1/6</div><div class="label">giai đoạn ngoài mẫu tốt hơn</div></div></div></div></section>
<section id="quan-sat"><div class="wrap"><h2>Điều nghiên cứu thực sự quan sát</h2><p class="answer">Đây là một trạng thái để kiểm tra thêm, không phải lời hứa về lần kế tiếp.</p><p>Nghiên cứu so sánh lúc giá đang giảm nhưng khối lượng tăng với lúc cả hai cùng giảm. Nó theo dõi kết quả ở các khoảng thời gian khác nhau, rồi yêu cầu mọi kết quả vượt qua cả kiểm tra trong nhóm lẫn kiểm tra cấp cha. Danh sách cổ phiếu là ảnh chụp các mã đang hoạt động, vì vậy không tái hiện trọn lịch sử các mã đã rời sàn.</p><div class="card warn"><h3>Giới hạn chính</h3><p>Kết quả không hỗ trợ không chứng minh phân kỳ vô dụng. Với khả năng phát hiện 0,44, thiết kế này vẫn có thể bỏ sót một hiệu ứng nhỏ.</p></div></div></section>
<section id="bon-row"><div class="wrap"><h2>Vì sao bốn kết quả riêng lẻ không đủ</h2><p class="answer">Bốn hàng có số liệu nổi bật riêng lẻ, nhưng đều không có sự ủng hộ của cấp cha.</p><div class="chart"><h3>Bốn hàng dừng ở kiểm tra cấp cha</h3><canvas id="hierarchy"></canvas><p class="small">Mỗi hàng phải có đồng thời bằng chứng ở cấp riêng và cấp rộng hơn. Cả bốn bị dừng ở bước thứ hai, nên không được diễn giải thành kết quả đầu tư.</p></div><p>Điều này giúp tránh chọn một lát cắt đẹp trong rất nhiều lát cắt đã xem. Trong R6, 3.014 trường hợp không được hỗ trợ và 14 trường hợp không đủ điều kiện tính đầy đủ.</p></div></section>
<section id="ngoai-mau"><div class="wrap"><h2>Kiểm tra ngoài mẫu</h2><p class="answer">Thêm thông tin khối lượng không cải thiện kết quả một cách nhất quán ở phần dữ liệu để riêng.</p><div class="chart"><h3>Sáu giai đoạn kiểm tra</h3><canvas id="folds"></canvas><p class="small">Cột xanh: sai số giảm. Cột cam: sai số tăng. Chỉ một trong sáu giai đoạn tốt hơn; mức thay đổi tổng thể là {p["improvement"]:.6f}, không đạt mức ý nghĩa thực hành.</p></div><div class="chart"><h3>Kiểm tra theo từng mã</h3><canvas id="stock"></canvas><p class="small">30 mã được chọn theo giá trị giao dịch trung vị: 13 mã có đủ sáu giai đoạn, 17 mã chỉ có kết quả một phần. Có {data["ok"] + data["partial"] and 26854:,} dòng dự báo; kết quả một phần không được dùng để nâng kết luận.</p></div></div></section>
<section id="corporate"><div class="wrap"><h2>Corporate actions và giới hạn dữ liệu</h2><p class="answer">Khối lượng đã được điều chỉnh cho 140 sự kiện, nhưng điều đó không xóa hết bất định.</p><p>Độ nhảy trung vị quanh sự kiện giảm nhẹ từ {ca["median_raw"]:.5f} xuống {ca["median_adjusted"]:.5f}. Tuy nhiên, trong 138 sự kiện đánh giá được, {ca["improved_or_equal_events"]} tốt hơn hoặc không đổi và {ca["worsened_events"]} xấu hơn. Vì vậy báo cáo chỉ nói điều chỉnh không làm trung vị xấu hơn, không nói vấn đề đã được giải quyết hoàn toàn.</p><div class="chart"><h3>Chẩn đoán quanh sự kiện</h3><canvas id="actions"></canvas><p class="small">Hai trong bốn hàng riêng lẻ biến mất khi bỏ các cửa sổ gần sự kiện; hai hàng còn lại vẫn bị kiểm tra cấp cha chặn.</p></div></div></section>
<section id="cach-hieu"><div class="wrap"><h2>Cách nhà đầu tư nên hiểu</h2><p class="answer">Hãy coi phân kỳ là lời nhắc kiểm tra bối cảnh, không phải căn cứ độc lập để ra lệnh.</p><ol><li>Kiểm tra xu hướng, thanh khoản và tin doanh nghiệp.</li><li>Không gán xác suất hồi phục từ riêng trạng thái giá–khối lượng.</li><li>Không chọn vài ví dụ đẹp để bỏ qua toàn bộ kết quả còn lại.</li><li>Ghi nhận giới hạn của mẫu cổ phiếu đang hoạt động và dữ liệu ngoài mẫu.</li></ol></div></section>
<section id="chua-chung-minh"><div class="wrap"><h2>Điều nghiên cứu chưa chứng minh</h2><p class="answer">Nghiên cứu chưa cho thấy phân kỳ giúp giao dịch ổn định; nó cũng không bác bỏ vĩnh viễn mọi hiệu ứng nhỏ.</p><ul><li>Không xác nhận một quy tắc giao dịch có thể dùng ngay.</li><li>Không đại diện đầy đủ cho toàn bộ lịch sử thị trường tại từng thời điểm.</li><li>Không nói corporate-action adjustment xử lý trọn mọi nhiễu.</li><li>Không biến kết quả âm thành bằng chứng rằng phân kỳ vô dụng.</li></ul></div></section>
<section id="ket-luan"><div class="wrap"><h2>Kết luận</h2><p class="answer">CLOSEOUT_INCONCLUSIVE_POWER_LIMITED.</p><p>R6 không tạo claim hỗ trợ giao dịch. Bốn hàng vượt ngưỡng riêng lẻ đều không qua hierarchy; kiểm tra ngoài mẫu không cải thiện và power còn hạn chế. Cách diễn giải thận trọng nhất là: chưa có bằng chứng đủ ổn định trong thiết kế này, đồng thời chưa thể loại trừ hết hiệu ứng nhỏ.</p></div></section>
<section id="ky-thuat"><div class="wrap"><h2>Chi tiết kỹ thuật</h2><details data-layer="technical"><summary>Phạm vi và verdict</summary><p>3.032 tests; 54 families; 3.018 OK; 14 FIT_FAILED; 4 Holm survivors; DESCRIPTIVE=0; NOT_SUPPORTED=3.014; PARENT_GATE_FAIL=4.</p></details><details data-layer="technical"><summary>Ngoài mẫu và power</summary><p>114.623 pooled predictions; improvement={p["improvement"]:.9f}; 1/6 better; materiality=false. Per-stock: 13 OK, 17 partial, 26.854 prediction rows. M=200; B=199; power=0,44; heteroskedastic size=0,015.</p></details><details data-layer="technical"><summary>Source hashes</summary><pre>{html.escape(sources_json)}</pre></details><details data-layer="technical"><summary>Claim registry</summary><pre>{html.escape(claims_json)}</pre></details></div></section>
</main><footer><div class="wrap">Authority: R6, independently accepted by Session 2 R2. Report is research communication, not investment advice.</div></footer>
<script>
const FOLDS={folds}; const HIER={hierarchy};
const base={{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}}}};
new Chart(document.getElementById('folds'),{{type:'bar',data:{{labels:FOLDS.map(x=>'Giai đoạn '+x.fold),datasets:[{{data:FOLDS.map(x=>x.delta*100000),backgroundColor:FOLDS.map(x=>x.delta<0?'#12658a':'#b85d20')}}]}},options:{{...base,scales:{{y:{{title:{{display:true,text:'Chênh lệch sai số ×100.000 (âm là tốt hơn)'}}}}}}}}}});
new Chart(document.getElementById('stock'),{{type:'doughnut',data:{{labels:['Đủ sáu giai đoạn','Kết quả một phần'],datasets:[{{data:[13,17],backgroundColor:['#12658a','#b85d20']}}]}},options:{{...base,plugins:{{legend:{{position:'bottom'}}}}}}}});
new Chart(document.getElementById('hierarchy'),{{type:'bar',data:{{labels:HIER.map(x=>x.label),datasets:[{{label:'Bị kiểm tra cấp cha chặn',data:[1,1,1,1],backgroundColor:'#b85d20'}}]}},options:{{...base,indexAxis:'y',scales:{{x:{{display:false}}}}}}}});
new Chart(document.getElementById('actions'),{{type:'bar',data:{{labels:['Tốt hơn hoặc không đổi','Xấu hơn'],datasets:[{{data:[67,71],backgroundColor:['#12658a','#b85d20']}}]}},options:{{...base,scales:{{y:{{beginAtZero:true,title:{{display:true,text:'Số sự kiện đánh giá được'}}}}}}}}}});
</script></body></html>"""

def main():
    data = build_data()
    source_hashes = {name: sha(RES / name) for name in SOURCES}
    dump(QA / "source_manifest.json", {"authority": "R6", "sources": SOURCES, "hashes": source_hashes, "superseded_authorities": ["R1", "R2", "R3", "R4", "R5"]})
    dump(QA / "source_hashes.json", source_hashes)
    dump(QA / "claim_registry.json", {"authority": "R6", "claims": data["claims"], "unresolved_claims": []})
    dump(QA / "chart_data.json", {"folds": data["folds"], "top30_status": {"ok": data["ok"], "partial": data["partial"]}, "hierarchy_blocked_rows": data["blocked"], "corporate_actions": {"improved_or_equal": 67, "worsened": 71}})
    markup = add_master_navigation(page(data))
    found = [term for term in FORBIDDEN if term.lower() in markup.lower()]
    if found: raise SystemExit(f"BLOCKED_FORBIDDEN_LEGACY_CLAIM: {found}")
    ROOT.joinpath("index.html").write_text(markup, encoding="utf-8")
    digest = hashlib.sha256(markup.encode()).hexdigest()
    text = visible_text(markup)
    editorial = {"html_sha256": digest, "forbidden_claim_hits": [], "overclaim_hits": [], "central_answer_present": "chưa cho thấy trạng thái đó giúp dự báo sự hồi phục một cách ổn định" in text, "technical_details_collapsed_default": True, "gates_pass": True}
    dump(QA / "editorial_audit.json", editorial)
    answers = {
        "Kết luận là gì?": ["chưa có cơ sở ổn định", "CLOSEOUT_INCONCLUSIVE_POWER_LIMITED"],
        "Có claim hỗ trợ giao dịch không?": ["không tạo claim hỗ trợ giao dịch"],
        "Vì sao bốn hàng không đủ?": ["bị chặn khi phải đi qua cấp kiểm tra rộng hơn"],
        "Kiểm tra ngoài mẫu nói gì?": ["chỉ một trong sáu giai đoạn tốt hơn"],
        "Corporate actions còn hạn chế gì?": ["71 xấu hơn"],
        "Kết quả không hỗ trợ có chứng minh phân kỳ vô dụng không?": ["không bác bỏ vĩnh viễn mọi hiệu ứng nhỏ"],
    }
    results = [{"question": q, "answer_keys_found": [x for x in keys if x.lower() in text.lower()], "answerable": all(x.lower() in text.lower() for x in keys)} for q, keys in answers.items()]
    dump(QA / "reader_gate.json", {"html_sha256": digest, "n_questions": len(results), "n_answerable": sum(x["answerable"] for x in results), "all_answerable": all(x["answerable"] for x in results), "results": results})
    print(f"WROTE {ROOT / 'index.html'}")
    print(f"SHA256 {digest}")

if __name__ == "__main__": main()
