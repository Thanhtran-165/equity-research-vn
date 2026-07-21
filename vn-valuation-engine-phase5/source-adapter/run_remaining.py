"""Resume Phase 5 cohort — only run missing + save full manifest."""
from __future__ import annotations
import hashlib, json, datetime as dt, sys, os, copy, time
from pathlib import Path

import warnings
warnings.filterwarnings('ignore')

SKILL = "/Users/bobo/.zcode/skills/vn-valuation-engine"
WORK = "/Users/bobo/ZCodeProject/vn-valuation-engine-phase5"
sys.path.insert(0, os.path.join(SKILL, "implementation"))
sys.path.insert(0, os.path.join(WORK, "source-adapter"))

from vnstock_adapter import fetch_live
from runner.valuation_runner import run_valuation
from verifier.independent_verifier import verify

ARTIFACTS = Path(WORK) / "artifacts" / "phase5-genuine-baseline"

def _sha_semantic(obj):
    clean = copy.deepcopy(obj)
    for k in ("request_id","started_at","completed_at","ts","generated_at"):
        if isinstance(clean, dict) and k in clean:
            clean[k] = "<redacted>"
    if isinstance(clean, dict) and "execution_log" in clean:
        clean["execution_log"] = [{"stage":e.get("stage"),"status":e.get("status")} for e in clean["execution_log"]]
    return hashlib.sha256(
        json.dumps(clean, default=str, sort_keys=True,
                   separators=(",",":"), ensure_ascii=False).encode()
    ).hexdigest()


def fetch_with_retry(ticker, snapshot_dir, max_retries=5):
    """Retry with backoff for rate limit."""
    for attempt in range(max_retries):
        try:
            return fetch_live(ticker, snapshot_dir)
        except Exception as e:
            if "RateLimit" in str(e) or "Rate limit" in str(e) or "rate_limit" in str(e).lower():
                wait = 30 + attempt * 15
                print(f"  rate-limited, waiting {wait}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(f"Rate limit persisted through {max_retries} retries")


def run_one(ticker, run_label):
    run_dir = ARTIFACTS / f"{ticker}-{run_label}"
    run_dir.mkdir(parents=True, exist_ok=True)
    started = dt.datetime.now(dt.timezone.utc)
    print(f"\n[{ticker}-{run_label}] starting at {started.isoformat()}")

    fetched = fetch_with_retry(ticker, str(run_dir))
    request = fetched["request"]

    raw_manifest = {
        "ticker": ticker, "run_label": run_label,
        "market_snapshot_sha256": fetched["market_sha"],
        "financials_snapshot_sha256": fetched["fin_sha"],
        "retrieval_timestamp": started.isoformat(),
    }
    json.dump(raw_manifest, open(run_dir / "raw-source-manifest.json","w"),
              indent=2, ensure_ascii=False)
    json.dump(request.to_dict(), open(run_dir / "request.json","w"),
              indent=2, default=str, ensure_ascii=False)

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

    json.dump(output, open(run_dir / "valuation-output.json","w"),
              indent=2, default=str, ensure_ascii=False)
    json.dump(errors, open(run_dir / "errors.json","w"),
              indent=2, default=str, ensure_ascii=False)
    json.dump(evidence_manifest, open(run_dir / "evidence-manifest.json","w"),
              indent=2, default=str, ensure_ascii=False)
    json.dump(execution_log, open(run_dir / "execution-log.json","w"),
              indent=2, default=str, ensure_ascii=False)

    try:
        verification = verify(request, result.output)
        ver_dict = verification.to_dict() if hasattr(verification,'to_dict') else verification
    except Exception as e:
        ver_dict = {"error": f"{type(e).__name__}: {e}"}
    json.dump(ver_dict, open(run_dir / "verification-result.json","w"),
              indent=2, default=str, ensure_ascii=False)

    completed = dt.datetime.now(dt.timezone.utc)
    sem_hash = _sha_semantic(output)
    run_summary = {
        "ticker": ticker, "run_label": run_label,
        "final_status": final_status,
        "errors_count": len(errors) if isinstance(errors,list) else 1,
        "verification_verdict": ver_dict.get("verdict") if isinstance(ver_dict,dict) else None,
        "semantic_output_hash": sem_hash,
        "duration_seconds": (completed-started).total_seconds(),
        "started_at": started.isoformat(), "completed_at": completed.isoformat(),
        "output_methods": list(output.get("method_results",{}).keys()) if isinstance(output,dict) else [],
        "output_implied_price": output.get("implied_price") if isinstance(output,dict) else None,
    }
    json.dump(run_summary, open(run_dir / "run-summary.json","w"),
              indent=2, default=str, ensure_ascii=False)
    print(f"  status={final_status} duration={run_summary['duration_seconds']:.1f}s hash={sem_hash[:16]}...")
    return run_summary


# Check existing + run missing
TICKERS = ["VCB","BVH","HPG","MWG","FPT"]
all_runs = []
existing = {d.name for d in ARTIFACTS.iterdir() if d.is_dir()}
print(f"Existing: {sorted(existing)}")

for ticker in TICKERS:
    for label in ["run-A","run-B"]:
        run_name = f"{ticker}-{label}"
        run_dir = ARTIFACTS / run_name
        # Re-run if missing run-summary or has FATAL
        if (run_dir / "run-summary.json").exists():
            summary = json.load(open(run_dir / "run-summary.json"))
            if summary.get("final_status") not in ("FATAL",) and "error" not in summary:
                all_runs.append(summary)
                print(f"  {run_name}: cached, skipping")
                continue
        # Run new
        time.sleep(3)  # gentle rate-limit avoidance
        summary = run_one(ticker, label)
        all_runs.append(summary)

# Save full manifest
out = Path(WORK) / "manifests" / "phase5-run-manifest.json"
json.dump({"phase_5C_runs": {
    "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    "total_runs": len(all_runs),
    "runs": all_runs,
}}, open(out,'w'), indent=2, default=str, ensure_ascii=False)
print(f"\n=== COHORT DONE: {len(all_runs)} runs ===")
print(f"WROTE {out}")

print("\n=== SUMMARY ===")
for r in all_runs:
    print(f"  {r['ticker']}-{r['run_label']}: status={r.get('final_status')} hash={r.get('semantic_output_hash','ERR')[:12]}")
