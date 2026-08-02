#!/usr/bin/env python3
"""VN100 V6 runner — builder v2, 61 mã (loại top-10 + reference)."""
import json, shutil, os, subprocess, sys, time

BATCH = sys.argv[1] if len(sys.argv) > 1 else '1'
SKIP = {'CTD','HPG','TCB','BID','CTG','VPB','MBB','LPB','VIC','VHM','GAS','MSN'}
tr = json.load(open('/tmp/vn100_tracker.json'))
rows = [(t['ticker'], t.get('industry','general')) for t in tr['tickers'] if t['status']=='needs_human' and t['ticker'] not in SKIP]

if BATCH == '1': rows = rows[:20]
elif BATCH == '2': rows = rows[20:40]
elif BATCH == '3': rows = rows[40:]

BUILDER = os.path.expanduser('~/.zcode/skills/equity-research-vn/scripts/build_report.py')

for T, SEC in rows:
    print(f'===== {T} =====', flush=True)
    r = subprocess.run(['python3', BUILDER, T], capture_output=True, text=True)
    out = r.stdout + r.stderr
    for line in out.split('\n'):
        if 'VERIFY' in line or 'ERROR' in line:
            print('  '+line.strip(), flush=True)
    ev = f'/tmp/vn100_{T}/.task-state/evidence'
    fails = []
    if os.path.isdir(ev):
        for fn in os.listdir(ev):
            if fn.startswith('REQ-') and fn.endswith('.json'):
                try:
                    d = json.load(open(f'{ev}/{fn}'))
                    if d.get('status')=='fail': fails.append(d.get('requirement_id'))
                except: pass
    fails = list(dict.fromkeys(fails))
    res = json.load(open(f'/tmp/vn100_{T}/result.json')) if os.path.exists(f'/tmp/vn100_{T}/result.json') else {}
    for row in tr['tickers']:
        if row['ticker']==T:
            row['recall'] = res.get('recall',0)
            row['fail_reqs'] = fails
            row['notes'] = f"v6 builder v2: price {res.get('price',0)}, mcap {res.get('mcap',0)} tỷ"
            break
    json.dump(tr, open('/tmp/vn100_tracker.json','w'), indent=2, ensure_ascii=False)
    if os.path.exists(f'/tmp/vn100_{T}/{T}_Complete_Report.html'):
        shutil.copy(f'/tmp/vn100_{T}/{T}_Complete_Report.html', '/tmp/vn100_reports/')
    shutil.rmtree(f'/tmp/vn100_{T}', ignore_errors=True)
    print(f'  → {T}: {res.get("recall",0)}/74, fails={len(fails)}', flush=True)
    time.sleep(60)

done = [t for t in tr['tickers'] if t['status']=='needs_human' and 'v6 builder' in t.get('notes','')]
recalls = [t['recall'] for t in done if t.get('recall')]
print(f'\n=== BATCH {BATCH} DONE ===')
if recalls:
    print(f'Recall: min={min(recalls)}, max={max(recalls)}, avg={sum(recalls)/len(recalls):.1f}')
    print(f'74/74: {sum(1 for r in recalls if r==74)} mã, ≥72: {sum(1 for r in recalls if r>=72)} mã')
