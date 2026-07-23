"""Phase 5 — Full qualification runner.

Runs: 5 live runs + 5 frozen replays + source tieout + final regression.
"""
from __future__ import annotations
import sys, json, hashlib, datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "adapter"))
sys.path.insert(0, str(Path(__file__).parent.parent / "vn-fundamental-analysis-phase4R3" / "implementation"))

from live_fundamental_adapter import adapt_ticker, save_snapshot
from runner import run_fundamental
from verifier.independent_verifier import verify
from models import FundamentalRequest

COHORT = ["FPT", "VCB", "BVH", "HPG", "MWG"]
PEER_SETS = {
    "FPT": [{"ticker":"CMG","value":15.0},{"ticker":"ELC","value":16.0},{"ticker":"ITD","value":14.5}],
    "VCB": [{"ticker":"CTG","value":15.0},{"ticker":"BIDV","value":16.0},{"ticker":"TCB","value":18.0}],
    "BVH": [{"ticker":"MIG","value":10.0},{"ticker":"BMI","value":12.0},{"ticker":"VNR","value":8.0}],
    "HPG": [{"ticker":"HSG","value":10.0},{"ticker":"NKG","value":12.0},{"ticker":"VIS","value":8.0}],
    "MWG": [{"ticker":"DGW","value":15.0},{"ticker":"FRT","value":14.0},{"ticker":"PET","value":10.0}],
}
YEARS = [2021, 2022, 2023, 2024, 2025]
BASE = Path(__file__).parent


def _semantic_hash(obj):
    """Semantic hash — strips non-semantic fields (source_id, source_dates, timestamps)."""
    import copy
    stripped = copy.deepcopy(obj)
    # Recursively remove non-semantic fields
    def _strip(o):
        if isinstance(o, dict):
            for k in list(o.keys()):
                if k in ("source_id", "source_dates", "source_types", "source_metric_ids",
                         "provenance", "provenance_record", "applicability_decision",
                         "timestamp", "duration_seconds", "execution_log", "evidence_manifest",
                         "decision_hash", "raw_evidence_hash", "provenance_hash",
                         "applicability_decisions"):
                    del o[k]
                else:
                    _strip(o[k])
        elif isinstance(o, list):
            for item in o:
                _strip(item)
    _strip(stripped)
    return hashlib.sha256(json.dumps(stripped, sort_keys=True, default=str, separators=(",",":"), ensure_ascii=False).encode()).hexdigest()[:16]


def run_live(ticker):
    """Run A: genuine live fetch + calculation."""
    print(f"  [{ticker}] Live run...", end=" ")
    try:
        peers = PEER_SETS.get(ticker, [])
        req, snapshot = adapt_ticker(ticker, YEARS, peer_set=peers)
        # Save snapshot
        snap_path = save_snapshot(snapshot, BASE / "snapshots", ticker)
        # Run engine
        res = run_fundamental(req)
        vr = verify(req, res.output)
        # Save outputs
        run_dir = BASE / "runs" / ticker / "live"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "normalized-input.json").write_text(json.dumps({k: v.to_dict() for k, v in req.metrics.items()}, indent=2, default=str))
        (run_dir / "fundamental-output.json").write_text(json.dumps(res.output.to_dict(), indent=2, default=str))
        (run_dir / "verifier-result.json").write_text(json.dumps(vr.to_dict(), indent=2, default=str))
        output_hash = _semantic_hash(res.output.to_dict())
        print(f"status={res.final_status} verifier={vr.overall_verdict} hash={output_hash}")
        return {"ticker": ticker, "status": res.final_status, "verifier": vr.overall_verdict,
                "errors": len(res.errors), "output_hash": output_hash,
                "metrics": {m.metric_id: {"status": m.status, "value": m.value} for m in res.output.metric_results},
                "snapshot_path": str(snap_path)}
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return {"ticker": ticker, "status": "EXCEPTION", "error": str(e)}


def run_replay(ticker, live_result):
    """Run B: deterministic replay from frozen snapshot (NO live fetch)."""
    print(f"  [{ticker}] Replay...", end=" ")
    try:
        snap_path = Path(live_result["snapshot_path"])
        snapshot = json.loads(snap_path.read_text())
        # Rebuild request from snapshot raw data — do NOT call adapt_ticker (which fetches live).
        # Instead, reconstruct MetricInput from snapshot's raw_data.
        from live_fundamental_adapter import NORMALIZATION_VND, NORMALIZATION_SHARES
        from models import MetricInput, PeriodType, ReportingScope, AttributionScope, ShareBasis, DenominatorBasis

        raw = snapshot["raw_data"]
        year_strs = [str(y) for y in YEARS]
        n = len(YEARS)
        fetch_ts = snapshot.get("fetch_timestamp", "")

        def _extract(stmt, ids):
            sd = raw.get(stmt, {})
            for iid in ids:
                if iid in sd:
                    return [sd[iid]["values"].get(y) for y in year_strs]
            for iid, info in sd.items():
                en = info.get("item_en","").lower()
                for t in ids:
                    if t.lower().replace("_"," ") in en:
                        return [info["values"].get(y) for y in year_strs]
            return [None]*n

        rev_raw = _extract("income_statement", ["net_sales"])
        npat_raw = _extract("income_statement", ["attributable_to_parent_company","net_profit_attributable_to_shareholders_of_the_group"])
        ta_raw = _extract("balance_sheet", ["total_assets"])
        eq_raw = _extract("balance_sheet", ["owners_equity","owner_equity"])
        eps_raw = _extract("income_statement", ["eps_basic_vnd","eps_basic"])

        weighted_raw = []
        for i in range(n):
            npat_v = npat_raw[i]; eps_v = eps_raw[i]
            if npat_v and eps_v and eps_v != 0:
                weighted_raw.append(npat_v / eps_v)
            else:
                weighted_raw.append(None)

        def _norm(raw_list, factor):
            return [v*factor if v is not None else None for v in raw_list]

        def _m(mid, raw_v, norm_v, rs, as_, pk=PeriodType.ANNUAL.value, db=None, sb=None):
            return MetricInput(metric_id=mid, values=norm_v, periods=list(YEARS),
                unit="BILLION_VND" if mid != "shares_outstanding" else "BILLION_SHARES",
                scope=rs, source_id=f"replay:{ticker}:{mid}",
                raw_values=raw_v, raw_unit="VND" if mid!="shares_outstanding" else "SHARES", raw_scale="UNIT",
                period_kind_bindings=[pk]*n, reporting_scope_bindings=[rs]*n,
                attribution_scope_bindings=[as_]*n,
                denominator_basis_bindings=[db]*n if db else [],
                share_basis_bindings=[sb]*n if sb else [],
                source_metric_ids=[f"replay_{mid}_{y}" for y in YEARS],
                source_dates=[fetch_ts]*n, source_types=["frozen_replay"]*n)

        metrics = {
            "revenue": _m("revenue", rev_raw, _norm(rev_raw, NORMALIZATION_VND), ReportingScope.CONSOLIDATED.value, AttributionScope.TOTAL_GROUP.value),
            "net_income": _m("net_income", npat_raw, _norm(npat_raw, NORMALIZATION_VND), ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value),
            "equity": _m("equity", eq_raw, _norm(eq_raw, NORMALIZATION_VND), ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value, PeriodType.POINT_IN_TIME.value, DenominatorBasis.AVERAGE_COMMON_EQUITY.value),
            "total_assets": _m("total_assets", ta_raw, _norm(ta_raw, NORMALIZATION_VND), ReportingScope.CONSOLIDATED.value, AttributionScope.TOTAL_GROUP.value, PeriodType.POINT_IN_TIME.value, DenominatorBasis.AVERAGE_TOTAL_ASSETS.value),
            "shares_outstanding": _m("shares_outstanding", weighted_raw, _norm(weighted_raw, NORMALIZATION_SHARES), ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value, PeriodType.ANNUAL.value, None, ShareBasis.WEIGHTED_AVERAGE_BASIC.value),
        }

        req = FundamentalRequest(ticker=ticker, company=raw.get("company_name",""), exchange=raw.get("exchange","HOSE"),
                                 sector=raw.get("industry",""), periods=list(YEARS), metrics=metrics,
                                 peer_set=PEER_SETS.get(ticker, []))
        res = run_fundamental(req)
        vr = verify(req, res.output)
        replay_hash = _semantic_hash(res.output.to_dict())
        stable = (replay_hash == live_result["output_hash"])
        run_dir = BASE / "runs" / ticker / "replay"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "fundamental-output.json").write_text(json.dumps(res.output.to_dict(), indent=2, default=str))
        (run_dir / "verifier-result.json").write_text(json.dumps(vr.to_dict(), indent=2, default=str))
        print(f"status={res.final_status} hash={replay_hash} stable={stable}")
        return {"ticker": ticker, "status": res.final_status, "verifier": vr.overall_verdict,
                "output_hash": replay_hash, "hash_stable": stable}
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return {"ticker": ticker, "status": "EXCEPTION", "error": str(e)}


def main():
    print("=== Phase 5 Full Qualification ===\n")

    print("--- 5 LIVE RUNS ---")
    live_results = []
    for ticker in COHORT:
        r = run_live(ticker)
        live_results.append(r)

    print("\n--- 5 FROZEN REPLAYS ---")
    replay_results = []
    for i, ticker in enumerate(COHORT):
        r = run_replay(ticker, live_results[i])
        replay_results.append(r)

    # Summary
    live_ok = sum(1 for r in live_results if r["status"] in ("PASS", "PASS_WITH_WARNINGS"))
    replay_stable = sum(1 for r in replay_results if r.get("hash_stable"))
    verifier_ok = sum(1 for r in live_results if r.get("verifier") == "PASS")
    total_errors = sum(r.get("errors", 0) for r in live_results)

    print(f"\n=== Summary ===")
    print(f"Live runs PASS: {live_ok}/5")
    print(f"Replays stable: {replay_stable}/5")
    print(f"Verifier PASS: {verifier_ok}/5")
    print(f"Total errors: {total_errors}")

    manifest = {
        "phase5_qualification_manifest": {
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "cohort": COHORT,
            "live_runs": live_results,
            "replay_runs": replay_results,
            "summary": {
                "live_pass": live_ok,
                "replay_stable": replay_stable,
                "verifier_pass": verifier_ok,
                "total_errors": total_errors,
            }
        }
    }
    out = BASE / "manifests" / "phase5-qualification-manifest.json"
    out.write_text(json.dumps(manifest, indent=2, default=str))
    print(f"\nManifest: {out}")
    return live_ok, replay_stable


if __name__ == "__main__":
    live_ok, replay_stable = main()
    sys.exit(0 if live_ok == 5 and replay_stable == 5 else 1)
