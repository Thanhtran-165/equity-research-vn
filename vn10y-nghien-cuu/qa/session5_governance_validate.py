#!/usr/bin/env python3
"""Read-only validation for the Session 5 report-governance remediation."""
import csv,hashlib,json,re
from collections import defaultdict
from pathlib import Path
ROOT=Path('/Users/bobo/ZCodeProject/vn10y-nghien-cuu'); RES=Path('/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research')
G=RES/'bond_equity_chapter2_return_v1/outputs/24_granger_results.csv'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
rows=list(csv.DictReader(G.open())); groups=defaultdict(list)
for r in rows:groups[(r['frequency'],r['direction'])].append(r)
def minimum(v,k):return min(float(x[k]) for x in v if x.get(k) not in ('',None))
table={f'{a}|{b}':{'count':len(v),'adjusted_p_survivors':sum(float(x['p_adjusted'])<.05 for x in v if x.get('p_adjusted') not in ('',None)),'minimum_p_raw':minimum(v,'p_raw'),'minimum_p_bootstrap':minimum(v,'p_bootstrap'),'minimum_p_adjusted':minimum(v,'p_adjusted'),'test_id_set_sha256':hashlib.sha256('\n'.join(sorted(x['test_id'] for x in v)).encode()).hexdigest()} for (a,b),v in sorted(groups.items())}
audit={'artifact':'bond_equity_chapter2_return_v1/outputs/24_granger_results.csv','sha256':sha(G),'total':len(rows),'frequency_direction':table,'duplicate_test_ids':len(rows)-len({x['test_id'] for x in rows})}
(ROOT/'qa/session5_granger_direction_audit.json').write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n')
registry=json.loads((ROOT/'qa/claim_registry.json').read_text()); errors=[]
for c in registry['empirical_claims']:
 for s in c.get('sources',[]):
  p=RES/s['artifact']
  if not s.get('test_id_or_key') or not re.fullmatch('[0-9a-f]{64}',s.get('sha256','')) or not p.exists() or sha(p)!=s['sha256'] or 'index.html' in s['artifact']:errors.append(c['id'])
for phrase in ['0/150 daily + 0/150 monthly bond→equity','300 rows bond→equity','equity→bond chưa','scope gap','nếu chiều ngược','dữ liệu đủ để bắt']:
 if phrase.lower() in (ROOT/'index.html').read_text().lower() or phrase.lower() in (ROOT/'qa/claim_registry.json').read_text().lower():errors.append('forbidden:'+phrase)
if len(rows)!=300 or any(v['count']!=75 or v['adjusted_p_survivors']!=0 for v in table.values()) or audit['duplicate_test_ids'] or errors:raise SystemExit('GOVERNANCE_VALIDATION_FAIL '+str(errors))
print('PASS_SESSION5_GOVERNANCE')
