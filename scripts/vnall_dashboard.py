#!/usr/bin/env python3
"""VNALL DASHBOARD — bản đồ toàn thị trường từ tracker (2026-08-04).
Đọc /tmp/vnall_tracker.json → sinh /tmp/vnall_dashboard.html (tự đứng, mở trình duyệt)
+ in bản tóm tắt markdown ra stdout. Không gọi API — dữ liệu từ tracker đã verify.
Usage: python3 vnall_dashboard.py [tracker.json] [output.html]
"""
import json, sys, collections, html

TRACKER = sys.argv[1] if len(sys.argv) > 1 else '/tmp/vnall_tracker.json'
OUT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/vnall_dashboard.html'

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
    done = [t for t in tk if t['status'] == 'done']
    n74 = sum(1 for t in done if t['recall'] == 74)
    avg = round(sum(t['recall'] for t in done) / len(done), 1) if done else 0
    nod = [t for t in tk if t['status'] == 'NO_DATA']
    nh = [t for t in tk if t['status'] == 'needs_human']

    by_sec = collections.defaultdict(list)
    for t in tk:
        by_sec[t.get('sector', '?')].append(t)
    sec_rows = []
    for sec, items in sorted(by_sec.items(), key=lambda kv: -len(kv[1])):
        d = [t for t in items if t['status'] == 'done']
        n74s = sum(1 for t in d if t['recall'] == 74)
        avgs = round(sum(t['recall'] for t in d) / len(d), 1) if d else 0
        mcap = sum(float(t.get('mcap_bn') or 0) for t in items)
        sec_rows.append((SECTOR_NAME.get(sec, sec), len(items), len(d), n74s,
                         avgs, round(mcap), len([t for t in items if t['status'] == 'NO_DATA'])))

    top = sorted([t for t in done if t['recall'] == 74], key=lambda t: -(t.get('mcap_bn') or 0))[:20]
    nh_rows = sorted(nh, key=lambda t: (t.get('recall') or 0))

    def row(t):
        sec = SECTOR_NAME.get(t.get('sector', '?'), t.get('sector', '?'))
        mcap = t.get('mcap_bn')
        mcap_s = f'{mcap:,.0f}' if mcap else '—'
        fails = ', '.join((t.get('fails') or [])[:4]) or '—'
        return (f'<tr><td class="mono">{t["ticker"]}</td><td>{sec}</td>'
                f'<td>{t["status"]}</td><td class="mono">{t.get("recall","—")}</td>'
                f'<td class="mono">{mcap_s}</td><td class="mono small">{html.escape(fails)}</td></tr>')

    rows_all = ''.join(row(t) for t in sorted(tk, key=lambda x: x['ticker']))
    rows_sec = ''.join(
        f'<tr><td><b>{s}</b></td><td class="mono">{n}</td><td class="mono">{d}</td>'
        f'<td class="mono">{n74s}</td><td class="mono">{avgs}</td><td class="mono">{mc:,}</td>'
        f'<td class="mono">{nd}</td></tr>'
        for s, n, d, n74s, avgs, mc, nd in sec_rows)
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

    sec_opts = ''.join(f'<option value="{html.escape(s)}">{html.escape(s)}</option>'
                       for s in sorted(set(t.get("sector","?") for t in tk)))

    doc = f'''<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VN-ALL Dashboard — Toàn thị trường (1.000 mã)</title>
<style>
body{{font-family:-apple-system,'Segoe UI',Roboto,sans-serif;background:#0f1420;color:#e6e8ee;margin:0;padding:24px}}
.wrap{{max-width:1200px;margin:0 auto}}
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
.badge{{display:inline-block;padding:1px 8px;border-radius:20px;font-size:11px}}
.b-done{{background:#12261d;color:#4ade80}} .b-nod{{background:#241a12;color:#facc15}} .b-nh{{background:#2a1520;color:#f87171}}
</style></head><body><div class="wrap">
<h1>📊 VN-ALL Dashboard — Toàn thị trường Việt Nam</h1>
<div class="sub">Equity research evidence pack · 1.000 mã (HOSE+HNX+UPCOM) · verifier 74 REQ ·
dữ liệu vnstock sponsor (VCI) + BCTC kiểm toán · <b>không khuyến nghị mua/bán</b></div>
<div class="kpis">
<div class="kpi"><div class="v">{len(tk)}</div><div class="l">Tổng mã chạy</div></div>
<div class="kpi"><div class="v g">{len(done)}</div><div class="l">done (≥70/74)</div></div>
<div class="kpi"><div class="v g">{n74}</div><div class="l">74/74 PASS</div></div>
<div class="kpi"><div class="v">{avg}</div><div class="l">Recall trung bình</div></div>
<div class="kpi"><div class="v y">{len(nod)}</div><div class="l">NO_DATA (mã nhỏ)</div></div>
<div class="kpi"><div class="v r">{len(nh)}</div><div class="l">Cần xem tay</div></div>
</div>
<h2>Theo ngành (sector ICB)</h2>
<table><thead><tr><th>Ngành</th><th>Số mã</th><th>done</th><th>74/74</th><th>avg recall</th><th>Vốn hóa (tỷ)</th><th>NO_DATA</th></tr></thead>
<tbody>{rows_sec}</tbody></table>
<h2>Top vốn hóa 74/74 PASS (20 mã)</h2>
<table><thead><tr><th>#</th><th>Ticker</th><th>Ngành</th><th>Vốn hóa (tỷ)</th><th>Recall</th></tr></thead>
<tbody>{rows_top}</tbody></table>
<h2>Toàn thị trường — bộ lọc ngành
<select id="sec" style="margin-left:10px;background:#1e2740;color:#e6e8ee;border:1px solid #26304a;border-radius:6px;padding:4px 8px"
onchange="var v=this.value;document.querySelectorAll('#all tbody tr').forEach(function(r){{r.style.display=(v==='' || r.dataset.sec===v)?'':'none'}})">
<option value="">Tất cả ngành</option>{sec_opts}</select></h2>
<table id="all"><thead><tr><th>Ticker</th><th>Ngành</th><th>Status</th><th>Recall</th><th>Vốn hóa (tỷ)</th><th>REQ fail</th></tr></thead>
<tbody>{rows_all}</tbody></table>
</div></body></html>'''
    open(OUT, 'w').write(doc)

    print(f'# VN-ALL TÓM TẮT — {len(tk)} mã (dashboard: {OUT})')
    print(f'- done {len(done)} ({len(done)*100//len(tk)}%) | 74/74: {n74} | avg {avg} | NO_DATA {len(nod)} | needs_human {len(nh)}')
    print(f'- Theo ngành: ' + '; '.join(f'{s}: {n} mã ({n74s} PASS, avg {avgs})'
          for s, n, d, n74s, avgs, mc, nd in sec_rows[:8]))
    print(f'- Top vốn hóa 74/74: ' + ', '.join(t['ticker'] for t in top[:10]))

if __name__ == '__main__':
    main()
