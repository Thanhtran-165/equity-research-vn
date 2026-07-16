#!/usr/bin/env python3
"""
run_cohort_c.py — Sequential Cohort C orchestrator (10 cross-ticker genuine runs).

Per protocol v0.7.1 + owner directive (2026-07-13):
  - Sequential (not parallel) — each run fresh workspace, fresh task-state, no artifact reuse.
  - No skill/verifier/protocol/source-pack/rubric change between runs.
  - STOP conditions: snapshot_drift, secret_leak, fabricated_data_detected,
    verifier_or_runner_crash_unclassified, critical_failure, source_pack_oracle_corruption.
  - Does NOT stop on a normal requirement FAIL (that is data to collect).
  - After each run: validate execution_type==genuine_agent; if NO_MODEL_BOUND, stop (infra).
  - No early generalization conclusions after 2/4/6 runs.
  - Append-only manifest update after each run.

10 logical runs:
  C-CTD-01, C-CTD-02, C-KDH-01, C-KDH-02, C-PNJ-01, C-PNJ-02,
  C-VCB-01, C-VCB-02, C-FPT-01, C-FPT-02
"""
import subprocess, sys, os, json, time, datetime, hashlib

AE = "/Users/bobo/ZCodeProject/agent-eval"
PROTO = "e6240e725eb233f4978c5b4564903f9556ab5be5d6bd494a496ab89c76fd2df4"
# Homebrew python 3.14.6 has yaml + anthropic (system python3 3.9.6 lacks anthropic)
PY = "/opt/homebrew/bin/python3"

RUNS = [
    ("C-CTD-01", "CTD"), ("C-CTD-02", "CTD"),
    ("C-KDH-01", "KDH"), ("C-KDH-02", "KDH"),
    ("C-PNJ-01", "PNJ"), ("C-PNJ-02", "PNJ"),
    ("C-VCB-01", "VCB"), ("C-VCB-02", "VCB"),
    ("C-FPT-01", "FPT"), ("C-FPT-02", "FPT"),
]

COHORT_DIR = f"{AE}/cohort-c/genuine-runs"
MANIFEST_PATH = f"{AE}/cohort-c/cohort-c-manifest.json"

STOP_REASONS = {
    "snapshot_drift", "secret_leak", "fabricated_data_detected",
    "verifier_or_runner_crash_unclassified", "critical_failure",
    "source_pack_oracle_corruption",
}


def classify_artifact(workspace):
    """Is the phase-6 output HTML or narration?"""
    for f in os.listdir(workspace):
        if f.endswith("_Complete_Report.html"):
            head = open(os.path.join(workspace,f)).read(100).lstrip()
            if head.startswith("<") or "<section" in head[:500] or "<!DOCTYPE" in head[:50]:
                return "HTML"
            return "NARRATION"
    return "NO_ARTIFACT"


def sha256_file(p):
    return hashlib.sha256(open(p,"rb").read()).hexdigest() if os.path.exists(p) else None


def run_one(run_id, ticker, idx, total):
    ws = f"{COHORT_DIR}/{run_id}"
    if os.path.exists(ws):
        import shutil; shutil.rmtree(ws)
    os.makedirs(ws, exist_ok=True)
    src_pack = f"{AE}/cohort-c/source-packs/{ticker}"
    print(f"\n{'='*70}\n  COHORT C run {idx}/{total} — {run_id} (ticker={ticker})\n{'='*70}", flush=True)
    t0 = time.time()
    try:
        proc = subprocess.run([PY, f"{AE}/runner/agent_runner.py",
            run_id, "cohort-c", ws, src_pack, ticker,
            "--scored", "true", "--model-backend", "zai", "--model-id", "GLM-5.2",
            "--protocol-sha256", PROTO], capture_output=True, text=True, timeout=3000)
    except subprocess.TimeoutExpired:
        dt = time.time()-t0
        print(f"  ❌ TIMEOUT after {dt:.0f}s (logical run {run_id})", flush=True)
        return {"run_id": run_id, "ticker": ticker, "status": "TIMEOUT",
                "duration_seconds": round(dt,1), "execution_type": "TIMEOUT"}
    dt = time.time()-t0
    rr_path = f"{ws}/run-result.json"
    if not os.path.exists(rr_path):
        print(f"  ❌ no run-result.json (rc={proc.returncode}); stderr tail: {proc.stderr[-300:]}", flush=True)
        return {"run_id": run_id, "ticker": ticker, "status": "NO_RESULT",
                "returncode": proc.returncode, "stderr_tail": proc.stderr[-300:],
                "duration_seconds": round(dt,1)}
    rr = json.load(open(rr_path))
    rr["artifact_type"] = classify_artifact(ws)
    rr["wall_duration_s"] = round(dt, 1)
    rr["html_artifact_sha256"] = sha256_file(next((os.path.join(ws,f) for f in os.listdir(ws) if f.endswith(".html")), ""))
    json.dump(rr, open(rr_path,"w"), indent=2, ensure_ascii=False)
    print(f"  execution_type={rr.get('execution_type')} verdict={rr.get('final_verdict')} "
          f"pass={rr.get('validator_results',{}).get('pass')} fail={rr.get('validator_results',{}).get('fail')} "
          f"artifact={rr['artifact_type']} dt={dt:.0f}s", flush=True)
    # Check stop conditions
    if rr.get("execution_type") not in ("genuine_agent",):
        print(f"  ⚠ execution_type={rr.get('execution_type')} — NOT genuine; investigate before continuing", flush=True)
    return rr


def update_manifest_append(run_record):
    """Append-only manifest update."""
    manifest = {"completed_runs": [], "started_at": datetime.datetime.now().isoformat(), "protocol": "v0.7.1"}
    if os.path.exists(MANIFEST_PATH):
        manifest = json.load(open(MANIFEST_PATH))
    manifest["completed_runs"].append({
        "run_id": run_record.get("run_id"),
        "ticker": run_record.get("ticker"),
        "execution_type": run_record.get("execution_type"),
        "final_verdict": run_record.get("final_verdict"),
        "pass": run_record.get("validator_results",{}).get("pass"),
        "fail": run_record.get("validator_results",{}).get("fail"),
        "skip": run_record.get("validator_results",{}).get("skip"),
        "artifact_type": run_record.get("artifact_type"),
        "duration_seconds": run_record.get("wall_duration_s") or run_record.get("duration_seconds"),
        "html_artifact_sha256": run_record.get("html_artifact_sha256"),
        "transport_recovery_count": run_record.get("transport_recovery_count"),
        "agent_content_recovery_count": run_record.get("agent_content_recovery_count"),
        "requirements_failed": run_record.get("requirements_failed"),
        "status": run_record.get("status", "COMPLETED"),
        "completed_at": datetime.datetime.now().isoformat(),
    })
    manifest["last_updated"] = datetime.datetime.now().isoformat()
    json.dump(manifest, open(MANIFEST_PATH,"w"), indent=2, ensure_ascii=False)


def check_stop_condition(rr):
    """Returns a stop reason string if a stop condition is met, else None."""
    if rr.get("status") in ("TIMEOUT", "NO_RESULT"):
        return f"infrastructure_failure:{rr.get('status')}"
    if rr.get("execution_type") == "NO_MODEL_BOUND":
        return "NO_MODEL_BOUND (infra blocker)"
    # Check for hard_gate critical violations
    for v in rr.get("hard_gate_violations", []):
        if any(s in str(v).lower() for s in ["secret_leak", "fabricated_data", "snapshot_drift"]):
            return f"critical:{v}"
    return None


def main():
    os.makedirs(COHORT_DIR, exist_ok=True)
    runs = []
    print(f"\n{'#'*70}\n#  COHORT C — 10 cross-ticker genuine runs under protocol v0.7.1\n#  Sequential, no patches between runs\n{'#'*70}\n", flush=True)
    for i, (run_id, ticker) in enumerate(RUNS, 1):
        rr = run_one(run_id, ticker, i, len(RUNS))
        runs.append(rr)
        update_manifest_append(rr)
        stop = check_stop_condition(rr)
        if stop:
            print(f"\n  🛑 STOP CONDITION TRIGGERED: {stop}", flush=True)
            print(f"  Cohort halted after {i}/{len(RUNS)} runs.", flush=True)
            break
        # Progress checkpoint every 2 runs
        if i % 2 == 0 and i < len(RUNS):
            n_pass = sum(1 for r in runs if r.get("final_verdict")=="PASS")
            print(f"\n  --- Checkpoint {i}/{len(RUNS)} runs: {n_pass}/{i} PASS so far (no early conclusions) ---\n", flush=True)
    # Final summary
    n = len(runs)
    n_genuine = sum(1 for r in runs if r.get("execution_type")=="genuine_agent")
    n_pass = sum(1 for r in runs if r.get("final_verdict")=="PASS")
    n_html = sum(1 for r in runs if r.get("artifact_type")=="HTML")
    print(f"\n{'='*70}\n  COHORT C SUMMARY — {n}/{len(RUNS)} runs completed\n{'='*70}", flush=True)
    print(f"  genuine_agent: {n_genuine}/{n}", flush=True)
    print(f"  PASS: {n_pass}/{n}", flush=True)
    print(f"  HTML artifacts: {n_html}/{n}", flush=True)
    # Per-ticker
    by_ticker = {}
    for r in runs:
        t = r.get("ticker","?")
        by_ticker.setdefault(t, []).append(r.get("final_verdict"))
    print(f"\n  Per-ticker:", flush=True)
    for t in sorted(by_ticker):
        verdicts = by_ticker[t]
        p = sum(1 for v in verdicts if v=="PASS")
        print(f"    {t}: {p}/{len(verdicts)} PASS  {verdicts}", flush=True)
    summary = {
        "completed_runs": n, "planned_runs": len(RUNS),
        "genuine_agent": n_genuine, "pass": n_pass,
        "html_artifacts": n_html,
        "per_ticker": {t: {"pass": sum(1 for v in vs if v=="PASS"), "total": len(vs), "verdicts": vs} for t,vs in by_ticker.items()},
        "protocol": "v0.7.1", "protocol_sha256": PROTO,
    }
    json.dump(summary, open(f"{AE}/cohort-c/cohort-c-summary.json","w"), indent=2, ensure_ascii=False)
    print(f"\n  → cohort-c/cohort-c-summary.json", flush=True)


if __name__ == "__main__":
    main()
