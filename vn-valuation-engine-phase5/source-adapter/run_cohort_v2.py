"""Phase 5 cohort runner v2 — fixed adapter, rate-limit-aware."""
from __future__ import annotations
import hashlib, json, datetime as dt, sys, os, copy, time
from pathlib import Path
import warnings; warnings.filterwarnings('ignore')

SKILL = "/Users/bobo/.zcode/skills/vn-valuation-engine"
WORK = "/Users/bobo/ZCodeProject/vn-valuation-engine-phase5"
sys.path.insert(0, os.path.join(SKILL, "implementation"))
sys.path.insert(0, os.path.join(WORK, "source-adapter"))

from vnstock_adapter import fetch_live
from runner.valuation_runner import run_valuation
from models.canonical_models import ValuationOutput, MethodResult, CalculationStep
from verifier.independent_verifier import verify

ARTIFACTS = Path(WORK) / "artifacts" / "phase5-genuine-baseline"

def _sha_semantic(obj):
    clean = copy.deepcopy(obj)
    if isinstance(clean, dict):
        for k in ("request_id","started_at","completed_at","ts","generated_at"):
            if k in clean: clean[k] = "<redacted>"
        if "execution_log" in clean:
            clean["execution_log"] = [{"stage":e.get("stage"),"status":e.get("status")} for e in clean["execution_log"]]
        if "request" in clean and isinstance(clean["request"], dict):
            clean["request"]["request_id"] = "<redacted>"
    return hashlib.sha256(json.dumps(clean, default=str, sort_keys=True,
                                      separators=(",",":"), ensure_ascii=False).encode()).hexdigest()


def fetch_retry(ticker, d, n=6):
    for i in range(n):
        try: return fetch_live(ticker, d)
        except Exception as e:
            if "Rate" in str(e) or "rate" in str(e).lower():
                w = 50 + i*15
                print(f"  rate-limited, wait {w}s (attempt {i+1}/{n})")
                time.sleep(w); continue
            raise
    raise RuntimeError("rate limit persistent")


def run_one(ticker, label):
    run_dir = ARTIFACTS / f"{ticker}-{label}"
    run_dir.mkdir(parents=True, exist_ok=True)
    started = dt.datetime.now(dt.timezone.utc)
    print(f"\n[{ticker}-{label}] starting")

    fetched = fetch_retry(ticker, str(run_dir))
    req = fetched["request"]

    json.dump({"ticker":ticker,"run_label":label,
               "market_snapshot_sha256":fetched["market_sha"],
               "financials_snapshot_sha256":fetched["fin_sha"],
               "retrieval_timestamp":started.isoformat()},
              open(run_dir/"raw-source-manifest.json","w"), indent=2, ensure_ascii=False)
    json.dump(req.to_dict(), open(run_dir/"request.json","w"), indent=2, default=str, ensure_ascii=False)

    result = run_valuation(req)
    output = result.output.to_dict()
    errors = [e.to_dict() if hasattr(e,'to_dict') else str(e) for e in result.errors]
    final_status = result.final_status

    json.dump(output, open(run_dir/"valuation-output.json","w"), indent=2, default=str, ensure_ascii=False)
    json.dump(errors, open(run_dir/"errors.json","w"), indent=2, default=str, ensure_ascii=False)
    json.dump(result.evidence_manifest, open(run_dir/"evidence-manifest.json","w"), indent=2, default=str, ensure_ascii=False)
    json.dump(result.execution_log, open(run_dir/"execution-log.json","w"), indent=2, default=str, ensure_ascii=False)

    # Verification
    try:
        method_results = []
        for m in output.get("method_results",[]):
            trace = []
            for s in m.get("calculation_trace",[]):
                if isinstance(s, dict):
                    valid_keys = {f for f in CalculationStep.__dataclass_fields__}
                    trace.append(CalculationStep(**{k:v for k,v in s.items() if k in valid_keys}))
                else: trace.append(s)
            mr_kwargs = dict(
                method_id=m.get("method_id",""), status=m.get("status",""),
                formula_id=m.get("formula_id",""),
                input_metric_ids=m.get("input_metric_ids",[]),
                calculation_trace=trace,
                benchmark_type=m.get("benchmark_type"),
                selected_multiple=m.get("selected_multiple"),
                implied_enterprise_value=m.get("implied_enterprise_value"),
                implied_equity_value=m.get("implied_equity_value"),
                shares_outstanding=m.get("shares_outstanding"),
                implied_price=m.get("implied_price"),
                currency=m.get("currency","VND"),
                warnings=m.get("warnings",[]), error_codes=m.get("error_codes",[]),
            )
            eb = m.get("equity_bridge")
            if isinstance(eb, dict):
                mr_kwargs["equity_bridge_items"] = eb.get("items") or []
                mr_kwargs["bridge_balanced"] = eb.get("balanced") or eb.get("balances")
            elif isinstance(eb, list):
                mr_kwargs["equity_bridge_items"] = eb
            method_results.append(MethodResult(**mr_kwargs))

        output_obj = ValuationOutput(
            schema_version=output.get("schema_version",""),
            request=output.get("request",{}), entity=output.get("entity",{}),
            valuation_date=output.get("valuation_date",""),
            reporting_currency=output.get("reporting_currency","VND"),
            input_summary=output.get("input_summary",{}),
            method_results=method_results,
            peer_set=output.get("peer_set") or [],
            historical_benchmarks=output.get("historical_benchmarks") or [],
            valuation_range=output.get("valuation_range") or {},
            assumptions=output.get("assumptions") or {},
            warnings=output.get("warnings") or [],
            errors=output.get("errors") or [],
            provenance=output.get("provenance") or {},
            quality=output.get("quality") or {},
        )
        vr = verify(output_obj)
        ver_dict = vr.to_dict()
        ver_dict["summary"] = {
            "overall_verdict": vr.overall_verdict,
            "passed": vr.passed, "failed": vr.failed,
            "not_applicable": vr.not_applicable,
            "applicable_requirements": vr.applicable_requirements,
            "failure_codes": list({r.failure_code for r in vr.requirement_results if r.verdict=="FAIL" and r.failure_code}),
        }
    except Exception as e:
        import traceback
        ver_dict = {"error": f"{type(e).__name__}: {e}", "tb": traceback.format_exc()[-500:]}

    json.dump(ver_dict, open(run_dir/"verification-result.json","w"), indent=2, default=str, ensure_ascii=False)

    completed = dt.datetime.now(dt.timezone.utc)
    sem = _sha_semantic(output)
    quality = output.get("quality") or {}
    fs = quality.get("assessment") or quality.get("overall_status") or "UNKNOWN"
    
    summary = {
        "ticker": ticker, "run_label": label,
        "final_status": fs,
        "verification_verdict": ver_dict.get("summary",{}).get("overall_verdict") if isinstance(ver_dict.get("summary"),dict) else None,
        "verification_failed": ver_dict.get("summary",{}).get("failed") if isinstance(ver_dict.get("summary"),dict) else None,
        "verification_failure_codes": ver_dict.get("summary",{}).get("failure_codes") if isinstance(ver_dict.get("summary"),dict) else None,
        "semantic_output_hash": sem,
        "duration_seconds": (completed-started).total_seconds(),
        "started_at": started.isoformat(), "completed_at": completed.isoformat(),
        "methods_summary": [(m.get("method_id"), m.get("status"), m.get("implied_price")) for m in (output.get("method_results") or [])],
        "valuation_range": output.get("valuation_range"),
        "market_snapshot_sha256": fetched["market_sha"],
        "financials_snapshot_sha256": fetched["fin_sha"],
    }
    json.dump(summary, open(run_dir/"run-summary.json","w"), indent=2, default=str, ensure_ascii=False)
    methods_str = ",".join(f"{m[0]}={m[2]:,.0f}" if m[2] else f"{m[0]}:{m[1][:5]}" for m in summary["methods_summary"])
    print(f"  status={fs} ver={summary['verification_verdict']} hash={sem[:12]}... dur={summary['duration_seconds']:.1f}s")
    print(f"  methods: {methods_str}")
    return summary


TICKERS = ["VCB","BVH","HPG","MWG","FPT"]
all_runs = []
for ticker in TICKERS:
    for label in ["run-A","run-B"]:
        try:
            summary = run_one(ticker, label)
            all_runs.append(summary)
            # Sleep 8s between runs to avoid rate limit
            time.sleep(8)
        except Exception as e:
            print(f"FATAL {ticker}-{label}: {e}")
            all_runs.append({"ticker":ticker,"run_label":label,"final_status":"FATAL","error":str(e)})
            time.sleep(30)

out = Path(WORK) / "manifests" / "phase5-run-manifest.json"
json.dump({"phase_5C_runs": {
    "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    "total_runs": len(all_runs),
    "runs": all_runs,
    "adapter_version": "v2 (Scale.UNIT fixed)",
}}, open(out,'w'), indent=2, default=str, ensure_ascii=False)
print(f"\n=== COHORT v2 DONE: {len(all_runs)} runs ===")
print(f"WROTE {out}")
