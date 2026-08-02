#!/usr/bin/env python3
"""VN100 V5 runner — chạy builder ZCode (build_report.py) cho list ticker + record tracker."""
import json, shutil, os, subprocess, sys, time

BATCH = sys.argv[1] if len(sys.argv) > 1 else '1'
tr = json.load(open('/tmp/vn100_tracker.json'))
rows = [(t['ticker'], t.get('industry','general')) for t in tr['tickers'] if t['status']=='needs_human']

if BATCH == '1': rows = rows[:24]
elif BATCH == '2': rows = rows[24:48]
elif BATCH == '3': rows = rows[48:]

BUILDER = os.path.expanduser('~/.zcode/skills/equity-research-vn/scripts/build_report.py')

for T, SEC in rows:
    print(f'===== {T} ({SEC}) =====', flush=True)
    r = subprocess.run(['python3', BUILDER, T, SEC], capture_output=True, text=True)
    out = r.stdout + r.stderr
    for line in out.split('\n'):
        if 'VERIFY' in line or 'ERROR' in line:
            print('  '+line.strip(), flush=True)
    # record
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
            row['notes'] = f"v5 builder ZCode: price {res.get('price',0)}, mcap {res.get('mcap',0)} tỷ, tech {res.get('tech_score',0)} {res.get('verdict','')}"
            break
    json.dump(tr, open('/tmp/vn100_tracker.json','w'), indent=2, ensure_ascii=False)
    if os.path.exists(f'/tmp/vn100_{T}/{T}_Complete_Report.html'):
        shutil.copy(f'/tmp/vn100_{T}/{T}_Complete_Report.html', '/tmp/vn100_reports/')
    shutil.rmtree(f'/tmp/vn100_{T}', ignore_errors=True)
    print(f'  → {T}: {res.get("recall",0)}/74, fails={len(fails)}', flush=True)
    time.sleep(60)

import collections
c = collections.Counter(t['status'] for t in tr['tickers'])
done = [t for t in tr['tickers'] if t['status']=='needs_human']
recalls = [t['recall'] for t in done if t.get('recall')]
print(f'\n=== BATCH {BATCH} DONE ===')
print(f'Status: {dict(c)}')
if recalls:
    print(f'Recall: min={min(recalls)}, max={max(recalls)}, avg={sum(recalls)/len(recalls):.1f}')
    print(f'≥72/74: {sum(1 for r in recalls if r>=72)} mã, ≥70: {sum(1 for r in recalls if r>=70)} mã')
