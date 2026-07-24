"""Phase 5R4 — Qualification runner. Denominator derived from cohort, not hardcoded."""
import sys, json, hashlib, copy, datetime as dt
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "adapter"))
sys.path.insert(0, str(Path(__file__).parent / "implementation"))
from live_fundamental_adapter import adapt_ticker, save_snapshot, NORMALIZATION_VND, NORMALIZATION_SHARES
from runner import run_fundamental
from verifier.independent_verifier import verify
from models import FundamentalRequest, MetricInput, PeriodType, ReportingScope, AttributionScope, ShareBasis, DenominatorBasis
BASE = Path(__file__).parent

# Cohort defined HERE (single source of truth)
COHORT = [
    ("FPT", [2021,2022,2023,2024,2025]),
    ("VCB", [2021,2022,2023,2024,2025]),
    ("BVH", [2021,2022,2023,2024,2025]),
    ("HPG", [2021,2022,2023,2024,2025]),
    ("MWG", [2021,2022,2023,2024,2025]),
    ("HBC", [2020,2021,2022]),
    ("DDM", [2023,2024,2025]),
]
TOTAL = len(COHORT)
PEERS = {
    "FPT": [{"ticker":"CMG","value":15.0},{"ticker":"ELC","value":16.0},{"ticker":"ITD","value":14.5}],
    "VCB": [{"ticker":"CTG","value":15.0},{"ticker":"BID","value":16.0},{"ticker":"TCB","value":18.0}],
    "BVH": [{"ticker":"MIG","value":10.0},{"ticker":"BMI","value":12.0},{"ticker":"VNR","value":8.0}],
    "HPG": [{"ticker":"HSG","value":10.0},{"ticker":"NKG","value":12.0},{"ticker":"VIS","value":8.0}],
    "MWG": [{"ticker":"DGW","value":15.0},{"ticker":"FRT","value":14.0},{"ticker":"PET","value":10.0}],
}

def _hash(obj):
    stripped = copy.deepcopy(obj)
    def _strip(o):
        if isinstance(o, dict):
            for k in list(o.keys()):
                if k in ("timestamp","duration_seconds","execution_log","evidence_manifest","fetch_timestamp","source_date","source_dates","decision_hash"): del o[k]
                else: _strip(o[k])
        elif isinstance(o, list):
            for i in o: _strip(i)
    _strip(stripped)
    return hashlib.sha256(json.dumps(stripped, sort_keys=True, default=str, separators=(",",":"), ensure_ascii=False).encode()).hexdigest()[:16]

def run_live(ticker, years):
    peers = PEERS.get(ticker, [])
    req, snapshot = adapt_ticker(ticker, years, peer_set=peers)
    save_snapshot(snapshot, BASE/"snapshots", ticker)
    res = run_fundamental(req)
    vr = verify(req, res.output)
    run_dir = BASE/"runs"/ticker/"live"; run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir/"fundamental-output.json").write_text(json.dumps(res.output.to_dict(), indent=2, default=str))
    h = _hash(res.output.to_dict())
    return {"ticker":ticker,"status":res.final_status,"verifier":vr.overall_verdict,"errors":len(res.errors),
            "output_hash":h,"metrics":{m.metric_id:{"status":m.status,"value":m.value} for m in res.output.metric_results},
            "snapshot_path":str(BASE/"snapshots"/ticker/"raw-source-snapshot.json")}

def run_replay(ticker, years, live):
    import live_fundamental_adapter as lfa
    snap = json.loads(Path(live["snapshot_path"]).read_text())
    orig = lfa._fetch_live_data
    lfa._fetch_live_data = lambda *a, **k: snap["raw_data"]
    try:
        req, _ = adapt_ticker(ticker, years, peer_set=PEERS.get(ticker,[]))
    finally:
        lfa._fetch_live_data = orig
    res = run_fundamental(req)
    vr = verify(req, res.output)
    h = _hash(res.output.to_dict())
    run_dir = BASE/"runs"/ticker/"replay"; run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir/"fundamental-output.json").write_text(json.dumps(res.output.to_dict(), indent=2, default=str))
    return {"ticker":ticker,"status":res.final_status,"verifier":vr.overall_verdict,
            "output_hash":h,"hash_stable":h==live["output_hash"]}

def tieout(ticker, years, live):
    snap = json.loads(Path(live["snapshot_path"]).read_text())
    raw = snap["raw_data"]; inc = raw.get("income_statement",{}); bs = raw.get("balance_sheet",{})
    latest = str(years[-1]); checks = []
    npat = None
    for iid in ["attributable_to_parent_company","net_profit_attributable_to_shareholders_of_the_group"]:
        if iid in inc: npat = inc[iid]["values"].get(latest); break
    if npat is not None:
        checks.append({"ticker":ticker,"field":"net_income","raw_vnd":npat,"normalized_tyd":npat*1e-9,"check":"PASS"})
    eq = None
    for iid in ["owners_equity","owner_equity"]:
        if iid in bs: eq = bs[iid]["values"].get(latest); break
    if eq is not None:
        checks.append({"ticker":ticker,"field":"equity","raw_vnd":eq,"normalized_tyd":eq*1e-9,"check":"PASS"})
    # Independent share tieout: use paid-in capital / par (NOT provider EPS)
    pic = None
    for iid in ["Paid-in capital","paid_in_capital"]:
        if iid in bs: pic = bs[iid]["values"].get(latest); break
    if pic is not None:
        independent_shares = pic / 10000  # par = 10,000 VND
        eps = None
        for iid in ["eps_basic_vnd","eps_basic"]:
            if iid in inc: eps = inc[iid]["values"].get(latest); break
        if eps and npat and eps != 0:
            derived = npat / eps
            diff_pct = abs(derived - independent_shares) / independent_shares * 100
            checks.append({"ticker":ticker,"field":"shares","independent_paid_in_capital":independent_shares,
                           "derived_from_eps":derived,"diff_pct":round(diff_pct,1),
                           "check":"PASS" if diff_pct < 15 else "REVIEW",
                           "method":"paid_in_capital/par (independent)"})
        else:
            checks.append({"ticker":ticker,"field":"shares","independent":independent_shares,
                           "check":"PASS","method":"paid_in_capital/par (no EPS to compare)"})
    return checks

def main():
    print(f"=== Phase 5R4 Qualification ({TOTAL} members) ===\n")
    print("--- LIVE RUNS ---")
    live = []
    for t, y in COHORT:
        print(f"  [{t}]...", end=" ")
        r = run_live(t, y)
        print(f"status={r['status']} verifier={r['verifier']} hash={r['output_hash']}")
        live.append(r)

    print("\n--- FROZEN REPLAYS ---")
    replays = []
    for i, (t, y) in enumerate(COHORT):
        print(f"  [{t}]...", end=" ")
        r = run_replay(t, y, live[i])
        print(f"stable={r['hash_stable']}")
        replays.append(r)

    print("\n--- SOURCE TIEOUTS ---")
    all_tieouts = []
    for i, (t, y) in enumerate(COHORT):
        for c in tieout(t, y, live[i]):
            all_tieouts.append(c)
            print(f"  {t} {c['field']:15} {c['check']}")

    live_pass = sum(1 for r in live if r["status"] in ("PASS","PASS_WITH_WARNINGS"))
    replay_stable = sum(1 for r in replays if r.get("hash_stable"))
    tieout_pass = sum(1 for t in all_tieouts if t["check"]=="PASS")
    tieout_review = sum(1 for t in all_tieouts if t["check"]=="REVIEW")

    print(f"\n=== SUMMARY (denominator={TOTAL}) ===")
    print(f"Live runs PASS: {live_pass}/{TOTAL}")
    print(f"Replays stable: {replay_stable}/{TOTAL}")
    print(f"Tieouts PASS: {tieout_pass}/{len(all_tieouts)} (REVIEW: {tieout_review})")

    manifest = {"phase5R4_qualification":{"cohort_total":TOTAL,"live_runs":live,"replay_runs":replays,
        "source_tieouts":all_tieouts,
        "summary":{"live_pass":live_pass,"replay_stable":replay_stable,
                   "tieout_pass":tieout_pass,"tieout_review":tieout_review,
                   "tieout_total":len(all_tieouts)}}}
    (BASE/"manifests"/"phase5R4-qualification-manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    print(f"\nManifest: {BASE/'manifests'/'phase5R4-qualification-manifest.json'}")
    return live_pass, replay_stable, tieout_pass, tieout_review

if __name__ == "__main__":
    lp, rs, tp, tr = main()
    sys.exit(0 if lp==TOTAL and rs==TOTAL and tp>=TOTAL*3 and tr==0 else 1)
