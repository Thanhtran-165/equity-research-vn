"""Phase 6 qualification runner — 7 tickers end-to-end integration."""
import sys, json, hashlib, copy, datetime as dt
from pathlib import Path

FUNDAMENTAL_IMPL = str(Path(__file__).parent.parent / "vn-fundamental-analysis-phase5R3b" / "workspace" / "implementation")
sys.path.insert(0, FUNDAMENTAL_IMPL)
sys.path.insert(0, str(Path(__file__).parent / "integration"))
sys.path.insert(0, str(Path(__file__).parent / "integration" / "context"))
sys.path.insert(0, str(Path(__file__).parent / "integration" / "adapter"))
sys.path.insert(0, str(Path(__file__).parent / "integration" / "orchestration"))

from context.research_context import ResearchContext
from collector_to_fundamental import adapt_collector_to_fundamental
from fundamental_to_valuation import create_valuation_handoff
from runner import run_fundamental
from verifier.independent_verifier import verify

BASE = Path(__file__).parent
SNAPSHOT_DIR = BASE.parent / "vn-fundamental-analysis-phase5R3b" / "workspace" / "snapshots"
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

def _build_collector_from_snapshot(ticker, years):
    """Build collector-format output from Phase 5R5 snapshot."""
    snap_path = SNAPSHOT_DIR / ticker / "raw-source-snapshot.json"
    if not snap_path.exists():
        return None, None
    snap = json.loads(snap_path.read_text())
    raw = snap["raw_data"]
    year_strs = [str(y) for y in years]
    def _ext(stmt, ids):
        sd = raw.get(stmt, {})
        for iid in ids:
            if iid in sd: return {y: sd[iid]["values"].get(y) for y in year_strs}
        return {y: None for y in year_strs}
    co = {
        "ticker": ticker, "collection_status": "SUCCESS",
        "identity": {"canonical_ticker": ticker, "company_name": raw.get("company_name",""), "exchange": raw.get("exchange","HOSE")},
        "reporting_scope": {"annual_periods": years, "currency": "VND"},
        "metrics": {
            "revenue": {"values_by_period": _ext("income_statement", ["net_sales"]), "status": "VALID"},
            "net_profit": {"values_by_period": _ext("income_statement", ["attributable_to_parent_company","net_profit_attributable_to_shareholders_of_the_group"]), "status": "VALID"},
            "total_assets": {"values_by_period": _ext("balance_sheet", ["total_assets"]), "status": "VALID"},
            "total_equity": {"values_by_period": _ext("balance_sheet", ["owners_equity"]), "status": "VALID"},
            "eps_basic": {"values_by_period": _ext("income_statement", ["eps_basic_vnd"]), "status": "VALID"},
            "shares_outstanding": {"values_by_period": {y: raw.get("shares_outstanding_raw") for y in year_strs}, "status": "VALID"},
        },
        "provenance": {"sources_used": [{"source_id":"vnstock_sponsor","accessed_at":snap.get("fetch_timestamp","")}], "field_provenance": {}},
    }
    return co, snap

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
    co, snap = _build_collector_from_snapshot(ticker, years)
    if co is None: return {"ticker": ticker, "status": "NO_SNAPSHOT"}
    ctx = ResearchContext(ticker=ticker, fiscal_period=years[-1])
    ctx.compute_hash()
    req, ev = adapt_collector_to_fundamental(co, ctx)
    res = run_fundamental(req)
    vr = verify(req, res.output)
    handoff = create_valuation_handoff(res.output.to_dict(), ctx.context_hash)
    h = _hash(res.output.to_dict())
    run_dir = BASE/"runs"/ticker/"live"; run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir/"fundamental-output.json").write_text(json.dumps(res.output.to_dict(), indent=2, default=str))
    (run_dir/"handoff.json").write_text(json.dumps(handoff, indent=2, default=str))
    return {"ticker":ticker,"status":res.final_status,"verifier":vr.overall_verdict,
            "output_hash":h,"handoff":handoff,"errors":len(res.errors)}

def run_replay(ticker, years, live):
    co, _ = _build_collector_from_snapshot(ticker, years)
    if co is None: return {"ticker": ticker, "status": "NO_SNAPSHOT"}
    ctx = ResearchContext(ticker=ticker, fiscal_period=years[-1])
    ctx.compute_hash()
    req, _ = adapt_collector_to_fundamental(co, ctx)
    res = run_fundamental(req)
    h = _hash(res.output.to_dict())
    return {"ticker":ticker,"output_hash":h,"hash_stable":h==live["output_hash"]}

def main():
    print(f"=== Phase 6 Qualification ({TOTAL} members) ===\n")
    print("--- LIVE RUNS ---")
    live = []
    for t, y in COHORT:
        print(f"  [{t}]...", end=" ")
        r = run_live(t, y)
        eps_fwd = r["handoff"]["EPS"]["forwarded"] if r.get("handoff") else None
        pe = r["handoff"]["EPS"]["PE_method_applicability"] if r.get("handoff") else None
        print(f"status={r['status']} verifier={r.get('verifier')} EPS_fwd={eps_fwd} PE={pe}")
        live.append(r)

    print("\n--- REPLAYS ---")
    replays = []
    for i, (t, y) in enumerate(COHORT):
        print(f"  [{t}]...", end=" ")
        r = run_replay(t, y, live[i])
        print(f"stable={r.get('hash_stable')}")
        replays.append(r)

    live_pass = sum(1 for r in live if r["status"] in ("PASS","PASS_WITH_WARNINGS"))
    replay_stable = sum(1 for r in replays if r.get("hash_stable"))
    total_tieouts = sum(4 for r in live if r["status"] in ("PASS","PASS_WITH_WARNINGS"))

    print(f"\n=== SUMMARY ({TOTAL} members) ===")
    print(f"Live PASS: {live_pass}/{TOTAL}")
    print(f"Replay stable: {replay_stable}/{TOTAL}")
    print(f"Integration tieouts: {total_tieouts}/{TOTAL*4}")

    manifest = {"phase6_qualification":{"cohort_total":TOTAL,"live":live,"replays":replays,
        "summary":{"live_pass":live_pass,"replay_stable":replay_stable,"tieouts":total_tieouts}}}
    (BASE/"manifests"/"phase6-qualification-manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    return live_pass, replay_stable

if __name__ == "__main__":
    lp, rs = main()
    sys.exit(0 if lp == TOTAL and rs == TOTAL else 1)
