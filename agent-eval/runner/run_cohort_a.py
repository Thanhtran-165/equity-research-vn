#!/usr/bin/env python3
"""
run_cohort_a.py — Sequential Cohort A orchestrator (5 cohort-a-triple-prime scored runs).

Per spec §V + §XV:
  - Sequential (not parallel) — each run fresh workspace, fresh task-state, no artifact reuse.
  - No skill/verifier/protocol/source-pack/rubric change between runs.
  - STOP condition: 2 critical failures of the SAME type → stop cohort, mark INVALIDATED/PARTIAL.
  - After each run: validate execution_type==genuine_agent; if NO_MODEL_BOUND, stop (infra).
  - Records each run's narration-vs-HTML classification (Phase 6 artifact type).
"""
import subprocess, sys, os, json, time, datetime

AE = "/Users/bobo/ZCodeProject/agent-eval"
PROTO = "707c84d9d4e16e207f17b96853aec6bda73f608c633d36475cf605da0dfc59ab"

def classify_artifact(workspace):
    """Is the phase-6 output HTML or narration? Key signal: starts with '<' (HTML) vs '#'/'Tôi' (narration)."""
    for f in os.listdir(workspace):
        if f.endswith("_Complete_Report.html"):
            head = open(os.path.join(workspace,f)).read(100).lstrip()
            if head.startswith("<") or "<section" in head[:500] or "<!DOCTYPE" in head[:50]:
                return "HTML"
            return "NARRATION"
    return "NO_ARTIFACT"

def run_one(run_id, idx, total):
    ws = f"{AE}/cohort-a-triple-prime/run-{idx:03d}"
    if os.path.exists(ws):
        import shutil; shutil.rmtree(ws)
    print(f"\n{'='*60}\n  COHORT A run {idx}/{total} — {run_id}\n{'='*60}", flush=True)
    t0 = time.time()
    proc = subprocess.run([sys.executable, f"{AE}/runner/agent_runner.py",
        run_id, "cohort-a-triple-prime", ws, f"{AE}/source-pack", "CTD",
        "--scored", "true", "--model-backend", "zai", "--model-id", "GLM-5.2",
        "--protocol-sha256", PROTO], capture_output=True, text=True, timeout=2400)
    dt = time.time()-t0
    rr_path = f"{ws}/run-result.json"
    if not os.path.exists(rr_path):
        print(f"  ❌ no run-result.json (rc={proc.returncode}); stderr tail: {proc.stderr[-200:]}", flush=True)
        return None
    rr = json.load(open(rr_path))
    rr["artifact_type"] = classify_artifact(ws)
    rr["wall_duration_s"] = round(dt, 1)
    json.dump(rr, open(rr_path,"w"), indent=2, ensure_ascii=False)
    print(f"  execution_type={rr['execution_type']} verdict={rr.get('final_verdict')} "
          f"recall={rr.get('validator_results',{}).get('recall_pct')} artifact={rr['artifact_type']} dt={dt:.0f}s", flush=True)
    return rr

def main():
    runs = []
    crit_types = {}  # critical-failure-type → count (stop if any reaches 2)
    for i in range(1, 6):
        rr = run_one(f"A-{i:03d}", i, 5)
        if rr is None:
            print("  STOP: run produced no result (infra failure)", flush=True); break
        runs.append(rr)
        if rr["execution_type"] != "genuine_agent":
            print(f"  STOP: execution_type={rr['execution_type']} (not genuine — infra blocker)", flush=True); break
        # stop condition: 2 critical hard-gate violations of same type
        for v in rr.get("hard_gate_violations", []):
            crit_types[v] = crit_types.get(v,0)+1
            if crit_types[v] >= 2:
                print(f"  STOP (spec §XV): 2 critical failures of same type '{v}'", flush=True)
                break
        if any(c>=2 for c in crit_types.values()): break
    # summary
    n = len(runs)
    print(f"\n{'='*60}\n  COHORT A SUMMARY — {n} runs\n{'='*60}", flush=True)
    print(f"  genuine: {sum(1 for r in runs if r['execution_type']=='genuine_agent')}/{n}", flush=True)
    print(f"  verdicts: {[(r.get('final_verdict'), r.get('artifact_type')) for r in runs]}", flush=True)
    narration = sum(1 for r in runs if r.get("artifact_type")=="NARRATION")
    html = sum(1 for r in runs if r.get("artifact_type")=="HTML")
    print(f"  narration-vs-HTML: {narration} narration / {html} HTML / {n-narration-html} other", flush=True)
    json.dump({"completed_runs":n, "runs":[{k:r.get(k) for k in ["run_id","execution_type","final_verdict","artifact_type","wall_duration_s"]} for r in runs],
               "narration_count":narration, "html_count":html, "stop_reason": ("completed" if n==5 else "stopped early")},
              open(f"{AE}/cohort-a-triple-prime/cohort-a-prime-summary.json","w"), indent=2)
    print(f"  → cohort-a-triple-prime/cohort-a-summary.json", flush=True)

if __name__ == "__main__":
    main()
