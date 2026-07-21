"""Phase 5 cohort runner — 10 genuine runs (2 per ticker × 5 tickers).

Per Directive §8: each run executes the full 14-stage pipeline.
Per Directive §8.5: NO model calls — narrative disabled; core baseline
must complete with narrative model off.

Per Directive §3: NO patches during cohort. Engines/runner/verifier frozen.
"""
from __future__ import annotations
import hashlib, json, datetime as dt, sys, os, copy
from pathlib import Path

import warnings
warnings.filterwarnings('ignore')

# Setup paths
SKILL = "/Users/bobo/.zcode/skills/vn-valuation-engine"
WORK = "/Users/bobo/ZCodeProject/vn-valuation-engine-phase5"
sys.path.insert(0, os.path.join(SKILL, "implementation"))
sys.path.insert(0, os.path.join(WORK, "source-adapter"))

from vnstock_adapter import fetch_live
from runner.valuation_runner import run_valuation
from verifier.independent_verifier import verify

ARTIFACTS = Path(WORK) / "artifacts" / "phase5-genuine-baseline"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

TICKERS = ["VCB", "BVH", "HPG", "MWG", "FPT"]


def _sha_semantic(obj):
    """Hash of output excluding non-deterministic fields."""
    clean = copy.deepcopy(obj)
    for k in ("request_id","started_at","completed_at","ts","generated_at","execution_log"):
        if isinstance(clean, dict) and k in clean:
            if k == "execution_log":
                # keep log but strip timestamps
                clean[k] = [{"stage":e.get("stage"),"status":e.get("status")} for e in clean[k]]
            else:
                clean[k] = "<redacted>"
    return hashlib.sha256(
        json.dumps(clean, default=str, sort_keys=True,
                   separators=(",",":"), ensure_ascii=False).encode()
    ).hexdigest()


def run_one(ticker: str, run_label: str) -> dict:
    """Execute one genuine run."""
    run_dir = ARTIFACTS / f"{ticker}-{run_label}"
    run_dir.mkdir(parents=True, exist_ok=True)

    started = dt.datetime.now(dt.timezone.utc)
    print(f"\n{'='*60}\n[{ticker}-{run_label}] starting at {started.isoformat()}\n{'='*60}")

    # Stage 1: live retrieval → raw snapshot
    fetched = fetch_live(ticker, str(run_dir))
    request = fetched["request"]
    raw_manifest = {
        "ticker": ticker,
        "run_label": run_label,
        "market_snapshot_sha256": fetched["market_sha"],
        "financials_snapshot_sha256": fetched["fin_sha"],
        "raw_payload_paths": {
            "market": fetched["raw"]["market"]["path"],
            "financials": fetched["raw"]["financials"]["path"],
        },
        "retrieval_timestamp": started.isoformat(),
    }
    json.dump(raw_manifest, open(run_dir / "raw-source-manifest.json","w"),
              indent=2, ensure_ascii=False)

    # Save request.json (input)
    request_dict = request.to_dict()
    json.dump(request_dict, open(run_dir / "request.json","w"),
              indent=2, default=str, ensure_ascii=False)

    # Stage 2-15: run pipeline
    try:
        result = run_valuation(request)
        output = result.output.to_dict()
        errors = [e.to_dict() if hasattr(e,'to_dict') else str(e) for e in result.errors]
        final_status = result.final_status
        evidence_manifest = result.evidence_manifest
        execution_log = result.execution_log
    except Exception as e:
        import traceback
        output = {"error": f"{type(e).__name__}: {e}"}
        errors = [{"code":"PIPELINE_EXCEPTION","message":str(e),"traceback":traceback.format_exc()}]
        final_status = "FAIL"
        evidence_manifest = {}
        execution_log = [{"stage":"pipeline","status":"exception","error":str(e)}]

    # Save outputs
    json.dump(output, open(run_dir / "valuation-output.json","w"),
              indent=2, default=str, ensure_ascii=False)
    json.dump(errors, open(run_dir / "errors.json","w"),
              indent=2, default=str, ensure_ascii=False)
    json.dump(evidence_manifest, open(run_dir / "evidence-manifest.json","w"),
              indent=2, default=str, ensure_ascii=False)
    json.dump(execution_log, open(run_dir / "execution-log.json","w"),
              indent=2, default=str, ensure_ascii=False)

    # Stage: independent verification
    try:
        verification = verify(request, result.output)
        ver_dict = verification.to_dict() if hasattr(verification,'to_dict') else verification
    except Exception as e:
        ver_dict = {"error": f"{type(e).__name__}: {e}"}
    json.dump(ver_dict, open(run_dir / "verification-result.json","w"),
              indent=2, default=str, ensure_ascii=False)

    completed = dt.datetime.now(dt.timezone.utc)
    duration = (completed - started).total_seconds()

    # Semantic hash for paired stability
    sem_hash = _sha_semantic(output)

    run_summary = {
        "ticker": ticker,
        "run_label": run_label,
        "final_status": final_status,
        "errors_count": len(errors) if isinstance(errors,list) else 1,
        "verification_verdict": ver_dict.get("verdict") if isinstance(ver_dict,dict) else None,
        "semantic_output_hash": sem_hash,
        "duration_seconds": duration,
        "started_at": started.isoformat(),
        "completed_at": completed.isoformat(),
        "output_methods": list(output.get("method_results",{}).keys()) if isinstance(output,dict) else [],
        "output_implied_price": output.get("implied_price") if isinstance(output,dict) else None,
    }
    json.dump(run_summary, open(run_dir / "run-summary.json","w"),
              indent=2, default=str, ensure_ascii=False)

    print(f"\n[{ticker}-{run_label}] status={final_status} errors={len(errors)} duration={duration:.1f}s")
    print(f"  semantic_hash={sem_hash[:16]}...")
    if isinstance(output,dict):
        for m, r in (output.get("method_results") or {}).items():
            print(f"    {m}: {r.get('status') if isinstance(r,dict) else r}")

    return run_summary


# === Run cohort ===
all_runs = []
for ticker in TICKERS:
    for label in ["run-A", "run-B"]:
        # Sleep slightly between A and B of same ticker to get fresh retrieval
        import time
        if label == "run-B":
            time.sleep(2)
        try:
            summary = run_one(ticker, label)
            all_runs.append(summary)
        except Exception as e:
            print(f"FATAL on {ticker}-{label}: {e}")
            all_runs.append({"ticker":ticker,"run_label":label,"final_status":"FATAL","error":str(e)})

# Save full run manifest
out = Path(WORK) / "manifests" / "phase5-run-manifest.json"
json.dump({"phase_5C_runs": {
    "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    "total_runs": len(all_runs),
    "runs": all_runs,
}}, open(out,'w'), indent=2, default=str, ensure_ascii=False)
print(f"\n\n=== COHORT DONE: {len(all_runs)} runs ===")
print(f"WROTE {out}")

# Summary table
print("\n=== SUMMARY ===")
for r in all_runs:
    print(f"  {r['ticker']}-{r['run_label']}: status={r.get('final_status')} hash={r.get('semantic_output_hash','ERR')[:12]}")
