#!/usr/bin/env python3
"""VNALL DASHBOARD v2 — bản đồ toàn thị trường từ tracker + metrics (2026-08-06).
Đọc tracker + metrics từ thư mục ỔN ĐỊNH (repo: ZCodeProject/data/vnall/) — KHÔNG dùng
/tmp (bị dọn khi máy restart — bài học 2026-08-06: mất tracker 2 lần).
Sinh dashboard HTML tự đứng. Không gọi API — dữ liệu đã verify.
Usage: python3 vnall_dashboard.py [tracker.json] [output.html]
"""
import json, sys, collections, html, os, statistics

BASE = os.path.expanduser('~/ZCodeProject/data/vnall')
TRACKER = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, 'vnall_tracker.json')
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE, 'vnall_dashboard.html')
METRICS = os.path.join(os.path.dirname(TRACKER), 'vnall_metrics.json')

SECTOR_NAME = {
    'banking': 'Ngân hàng', 'realestate': 'BĐS', 'materials': 'Hàng hóa (thép/phân bón...)',
    'consumer': 'Tiêu dùng', 'retail': 'Bán lẻ', 'securities': 'Chứng khoán', 'finance': 'Tài chính',
    'insurance': 'Bảo hiểm', 'energy': 'Năng lượng & Điện', 'transport': 'Vận tải & Cảng',
    'pharma': 'Dược', 'tech': 'Công nghệ', 'industrial': 'Công nghiệp & SX',
    'general': 'Khác', '?': 'Khác',
}

def main():
    tr = json.load(open(TRACKER))
    tk = tr['tickers']
    met = {}
    if os.path.exists(METRICS):
        met = json.load(open(METRICS))
    HAS_MET = bool(met)
    done = [t for t in tk if t['status'] == 'done']
    n74 = sum(1 for t in done if t['recall'] == 74)
    avg = round(sum(t['recall'] for t in done) / len(done), 1) if done else 0
    nod = [t for t in tk if t['status'] == 'NO_DATA']
    nh = [t for t in tk if t['status'] == 'needs_human']

    def mget(t, k):
        v = met.get(t['ticker'], {})
        x = v.get(k)
        return x if isinstance(x, (int, float)) else None

    def fmt(x, d=1):
        return f'{x:,.{d}f}' if isinstance(x, (int, float)) else '—'

    # Phát hiện định giá bất thường (chỉ mã done + có metrics)
    odd = []
    if HAS_MET:
        for t in done:
            pe = mget(t, 'pe'); pb = mget(t, 'pb'); pe5 = mget(t, 'pe5med')
            tag = []
            if pe is not None and pe < 0: tag.append('P/E âm (lỗ)')
            if pe is not None and 0 < pe < 5: tag.append('P/E rất thấp')
            if pe is not None and pe5 and pe > 0 and pe < pe5 * 0.5: tag.append('P/E < 50% median 5 năm')
            if pb is not None and 0 < pb < 0.7: tag.append('P/B dưới tài sản ròng')
            if tag:
                odd.append((t['ticker'], SECTOR_NAME.get(t.get('sector','?'), t.get('sector','?')),
                            t.get('recall'), mget(t, 'pe'), mget(t, 'pb'), '; '.join(tag)))
        odd.sort(key=lambda r: (r[5], -(r[3] or 0)))

    by_sec = collections.defaultdict(list)
    for t in tk:
        by_sec[t.get('sector', '?')].append(t)
    sec_rows = []
    for sec, items in sorted(by_sec.items(), key=lambda kv: -len(kv[1])):
        d = [t for t in items if t['status'] == 'done']
        n74s = sum(1 for t in d if t['recall'] == 74)
        avgs = round(sum(t['recall'] for t in d) / len(d), 1) if d else 0
        mcap = sum(float(t.get('mcap_bn') or 0) for t in items)
        pes = [mget(t, 'pe') for t in d if isinstance(mget(t, 'pe'), (int, float)) and mget(t, 'pe') > 0]
        pbs = [mget(t, 'pb') for t in d if isinstance(mget(t, 'pb'), (int, float)) and mget(t, 'pb') > 0]
        pe_med = statistics.median(pes) if pes else None
        pb_med = statistics.median(pbs) if pbs else None
        sec_rows.append((SECTOR_NAME.get(sec, sec), len(items), len(d), n74s,
                         avgs, round(mcap), len([t for t in items if t['status'] == 'NO_DATA']),
                         pe_med, pb_med))

    top = sorted([t for t in done if t['recall'] == 74], key=lambda t: -(t.get('mcap_bn') or 0))[:20]
    nh_rows = sorted(nh, key=lambda t: (t.get('recall') or 0))

    def row(t):
        sec = SECTOR_NAME.get(t.get('sector', '?'), t.get('sector', '?'))
        mcap = t.get('mcap_bn')
        mcap_s = f'{mcap:,.0f}' if mcap else '—'
        fails = ', '.join((t.get('fails') or [])[:4]) or '—'
        pe_s = fmt(mget(t, 'pe'), 1) if HAS_MET else '—'
        pb_s = fmt(mget(t, 'pb'), 2) if HAS_MET else '—'
        roe_s = fmt(mget(t, 'roe'), 1) if HAS_MET else '—'
        return (f'<tr data-sec="{html.escape(t.get("sector","?"))}" data-r="{t.get("recall","")}" '
                f'data-pe="{pe_s if isinstance(mget(t,"pe"),(int,float)) else ""}">'
                f'<td class="mono">{t["ticker"]}</td><td>{sec}</td>'
                f'<td>{t["status"]}</td><td class="mono">{t.get("recall","—")}</td>'
                f'<td class="mono">{mcap_s}</td><td class="mono">{pe_s}</td>'
                f'<td class="mono">{pb_s}</td><td class="mono">{roe_s}</td>'
                f'<td class="mono small">{html.escape(fails)}</td></tr>')

    rows_all = ''.join(row(t) for t in sorted(tk, key=lambda x: x['ticker']))
    rows_sec = ''.join(
        f'<tr><td><b>{s}</b></td><td class="mono">{n}</td><td class="mono">{d}</td>'
        f'<td class="mono">{n74s}</td><td class="mono">{avgs}</td><td class="mono">{mc:,}</td>'
        f'<td class="mono">{nd}</td><td class="mono">{fmt(pe_med,1)}</td><td class="mono">{fmt(pb_med,2)}</td></tr>'
        for s, n, d, n74s, avgs, mc, nd, pe_med, pb_med in sec_rows)
    rows_top = ''.join(
        f'<tr><td class="mono">{i+1}</td><td class="mono"><b>{t["ticker"]}</b></td>'
        f'<td>{SECTOR_NAME.get(t.get("sector","?"), t.get("sector","?"))}</td>'
        f'<td class="mono">{t.get("mcap_bn"):,.0f}</td><td class="mono">{t.get("recall")}</td></tr>'
        for i, t in enumerate(top))
    rows_nh = ''.join(
        f'<tr><td class="mono">{t["ticker"]}</td><td>{SECTOR_NAME.get(t.get("sector","?"), t.get("sector","?"))}</td>'
        f'<td class="mono">{t.get("recall")}</td>'
        f'<td class="small">{html.escape(", ".join((t.get("fails") or [])[:5]))}</td></tr>'
        for t in nh_rows)

    rows_odd = ''.join(
        f'<tr><td class="mono"><b>{r[0]}</b></td><td>{r[1]}</td><td class="mono">{r[2]}</td>'
        f'<td class="mono">{fmt(r[3],1)}</td><td class="mono">{fmt(r[4],2)}</td><td class="small">{r[5]}</td></tr>'
        for r in odd[:30]) if HAS_MET else '<tr><td colspan="6" class="small">Cần /tmp/vnall_metrics.json (GLM gom xong)</td></tr>'

    sec_opts = ''.join(f'<option value="{html.escape(s)}">{html.escape(s)}</option>'
                       for s in sorted(set(t.get("sector","?") for t in tk)))

    met_note = 'có chỉ số định giá P/E · P/B · ROE' if HAS_MET else 'chưa có metrics (chờ GLM gửi /tmp/vnall_metrics.json)'

    doc = f'''<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VN-ALL Dashboard — Toàn thị trường (1.000 mã)</title>
<style>
body{{font-family:-apple-system,'Segoe UI',Roboto,sans-serif;background:#0f1420;color:#e6e8ee;margin:0;padding:24px}}
.wrap{{max-width:1300px;margin:0 auto}}
h1{{font-size:22px;margin:0 0 4px}} .sub{{color:#8b93a7;font-size:13px;margin-bottom:20px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:24px}}
.kpi{{background:#171e2e;border:1px solid #26304a;border-radius:10px;padding:14px 16px}}
.kpi .v{{font-size:22px;font-weight:700}} .kpi .l{{font-size:12px;color:#8b93a7}}
.kpi .g{{color:#4ade80}} .kpi .y{{color:#facc15}} .kpi .r{{color:#f87171}}
table{{width:100%;border-collapse:collapse;background:#171e2e;border-radius:10px;overflow:hidden;margin-bottom:24px}}
th{{background:#1e2740;text-align:left;padding:9px 12px;font-size:12px;color:#8b93a7;position:sticky;top:0}}
td{{padding:7px 12px;border-top:1px solid #222c46;font-size:13px}}
.mono{{font-family:ui-monospace,Menlo,monospace}} .small{{font-size:11px;color:#8b93a7}}
h2{{font-size:16px;margin:28px 0 10px;color:#c9d2e4}}
select,input{{background:#1e2740;color:#e6e8ee;border:1px solid #26304a;border-radius:6px;padding:4px 8px}}
.badge{{display:inline-block;padding:1px 8px;border-radius:20px;font-size:11px}}
</style></head><body><div class="wrap">
<h1>📊 VN-ALL Dashboard — Toàn thị trường Việt Nam</h1>
<div class="sub">Equity research evidence pack · 1.000 mã (HOSE+HNX+UPCOM) · verifier 74 REQ ·
dữ liệu vnstock sponsor (VCI) + BCTC kiểm toán · {met_note} · <b>không khuyến nghị mua/bán</b></div>
<div class="kpis">
<div class="kpi"><div class="v">{len(tk)}</div><div class="l">Tổng mã chạy</div></div>
<div class="kpi"><div class="v g">{len(done)}</div><div class="l">done (≥70/74)</div></div>
<div class="kpi"><div class="v g">{n74}</div><div class="l">74/74 PASS</div></div>
<div class="kpi"><div class="v">{avg}</div><div class="l">Recall trung bình</div></div>
<div class="kpi"><div class="v y">{len(nod)}</div><div class="l">NO_DATA (mã nhỏ)</div></div>
<div class="kpi"><div class="v r">{len(nh)}</div><div class="l">Cần xem tay</div></div>
</div>
<h2>Theo ngành (sector ICB)</h2>
<table><thead><tr><th>Ngành</th><th>Số mã</th><th>done</th><th>74/74</th><th>avg recall</th><th>Vốn hóa (tỷ)</th><th>NO_DATA</th><th>P/E median</th><th>P/B median</th></tr></thead>
<tbody>{rows_sec}</tbody></table>
<h2>Top vốn hóa 74/74 PASS (20 mã)</h2>
<table><thead><tr><th>#</th><th>Ticker</th><th>Ngành</th><th>Vốn hóa (tỷ)</th><th>Recall</th></tr></thead>
<tbody>{rows_top}</tbody></table>
<h2>Phát hiện định giá bất thường (mã done, {('30/{}') if HAS_MET else ''}{len(odd)} mã tìm thấy)</h2>
<table><thead><tr><th>Ticker</th><th>Ngành</th><th>Recall</th><th>P/E</th><th>P/B</th><th>Dấu hiệu</th></tr></thead>
<tbody>{rows_odd}</tbody></table>
<h2>Toàn thị trường — bộ lọc
<select id="sec" onchange="flt()" style="margin-left:10px">
<option value="">Tất cả ngành</option>{sec_opts}</select>
{'P/E tối đa: <input type="number" id="pemax" value="0" style="width:80px" oninput="flt()"> (0 = bỏ qua)' if HAS_MET else ''}
<label style="margin-left:10px"><input type="checkbox" id="only74" onchange="flt()"> Chỉ 74/74</label></h2>
<table id="all"><thead><tr><th>Ticker</th><th>Ngành</th><th>Status</th><th>Recall</th><th>Vốn hóa (tỷ)</th><th>P/E</th><th>P/B</th><th>ROE %</th><th>REQ fail</th></tr></thead>
<tbody>{rows_all}</tbody></table>
<script>
function flt(){{var v=document.getElementById('sec').value;
var pm=parseFloat(document.getElementById('pemax').value);
var o74=document.getElementById('only74').checked;
document.querySelectorAll('#all tbody tr').forEach(function(r){{
var ok=(v===''||r.dataset.sec===v)&&(!o74||r.dataset.r==='74');
if(ok&&pm>0){{var pe=parseFloat(r.dataset.pe);if(!isNaN(pe)&&pe>pm)ok=false;}}
r.style.display=ok?'':'none';}})}}
flt();
</script>
</div></body></html>'''
    open(OUT, 'w').write(doc)

    print(f'# VN-ALL TÓM TẮT — {len(tk)} mã (dashboard: {OUT})')
    print(f'- done {len(done)} ({len(done)*100//len(tk)}%) | 74/74: {n74} | avg {avg} | NO_DATA {len(nod)} | needs_human {len(nh)}')
    if HAS_MET:
        print(f'- Metrics: {len(met)} mã (P/E, P/B, ROE) — {len(odd)} mã định giá bất thường')
    print(f'- Theo ngành: ' + '; '.join(f'{s}: {n} mã ({n74s} PASS, avg {avgs})'
          for s, n, d, n74s, avgs, mc, nd, pe_med, pb_med in sec_rows[:8]))
    print(f'- Top vốn hóa 74/74: ' + ', '.join(t['ticker'] for t in top[:10]))

if __name__ == '__main__':
    main()
