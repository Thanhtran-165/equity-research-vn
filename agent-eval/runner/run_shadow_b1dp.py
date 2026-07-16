#!/usr/bin/env python3
"""
run_shadow_b1dp.py — Shadow Batch 1″ (10 jobs on 5 fresh tickers, protocol v0.11.1).

Fresh tickers: ACB (banking), SAB (consumer/beverage), GEX (industrial),
               SSI (financial services), PLX (energy/logistics)
None of these have been used in any prior cohort, shadow batch, or patch building.
"""
import subprocess, sys, os, json, time, datetime, hashlib

AE = "/Users/bobo/ZCodeProject/agent-eval"
PROTO = "e4a8c3f95cda231ec7494627ecdbdac5472a03b05b5a8671486eaafe099a52b5"
PY = "/opt/homebrew/bin/python3"
os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")

RUNS = [
    ("SQ-ACB-01", "ACB"), ("SQ-ACB-02", "ACB"),
    ("SQ-SAB-01", "SAB"), ("SQ-SAB-02", "SAB"),
    ("SQ-GEX-01", "GEX"), ("SQ-GEX-02", "GEX"),
    ("SQ-SSI-01", "SSI"), ("SQ-SSI-02", "SSI"),
    ("SQ-PLX-01", "PLX"), ("SQ-PLX-02", "PLX"),
]

SHADOW_DIR = f"{AE}/cohort-c/shadow-production-b1dp"
MANIFEST_PATH = f"{AE}/cohort-c/shadow-b1dp-manifest.json"
SLO_LATENCY_ABSOLUTE_MAX = 3300


def sha256_file(p):
    return hashlib.sha256(open(p,"rb").read()).hexdigest() if os.path.exists(p) else None


def classify_artifact(workspace):
    for f in os.listdir(workspace):
        if f.endswith("_Complete_Report.html"):
            head = open(os.path.join(workspace,f)).read(100).lstrip()
            if head.startswith("<") or "<section" in head[:500] or "<!DOCTYPE" in head[:50]:
                return "HTML"
            return "NARRATION"
    return "NO_ARTIFACT"


def check_fail_closed(workspace, run_id, ticker):
    gates = []
    contract_path = os.path.join(workspace, "verified-dashboard-data.json")
    if not os.path.exists(contract_path):
        gates.append(("FAIL_CLOSED", "missing_required_data", "verified-dashboard-data.json not produced"))
    rr_path = os.path.join(workspace, "run-result.json")
    if not os.path.exists(rr_path):
        gates.append(("FAIL_CLOSED", "verifier_crash", "run-result.json not produced"))
    else:
        rr = json.load(open(rr_path))
        vr = rr.get("validator_results", {})
        if not vr or vr.get("pass") is None:
            gates.append(("FAIL_CLOSED", "verifier_unrunnable", "validator_results missing"))
    html_files = [f for f in os.listdir(workspace) if f.endswith("_Complete_Report.html")]
    if not html_files:
        gates.append(("FAIL_CLOSED", "artifact_missing", "no _Complete_Report.html"))
    else:
        html_path = os.path.join(workspace, html_files[0])
        head = open(html_path).read(200).lstrip()
        if not (head.startswith("<!DOCTYPE") or head.startswith("<html") or head.startswith("<")):
            gates.append(("FAIL_CLOSED", "artifact_unparseable", "artifact not HTML"))
    if os.path.exists(rr_path):
        rr = json.load(open(rr_path))
        if rr.get("protocol_sha256","") != PROTO:
            gates.append(("FAIL_CLOSED", "protocol_drift", "protocol hash mismatch"))
    return gates


def run_one(run_id, ticker, idx, total):
    ws = f"{SHADOW_DIR}/{run_id}"
    if os.path.exists(ws):
        import shutil; shutil.rmtree(ws)
    os.makedirs(ws, exist_ok=True)
    src_pack = f"{AE}/cohort-c/shadow/source-packs-fresh/{ticker}"
    print(f"\n{'='*70}\n  BATCH 1″ run {idx}/{total} — {run_id} (ticker={ticker})\n{'='*70}", flush=True)
    t0 = time.time()
    try:
        proc = subprocess.run([PY, f"{AE}/runner/agent_runner.py",
            run_id, "shadow-b1dp", ws, src_pack, ticker,
            "--scored", "true", "--model-backend", "zai", "--model-id", "GLM-5.2",
            "--protocol-sha256", PROTO], capture_output=True, text=True, timeout=SLO_LATENCY_ABSOLUTE_MAX,
            env=os.environ)
    except subprocess.TimeoutExpired:
        print(f"  ❌ TIMEOUT ({run_id})", flush=True)
        return {"run_id": run_id, "ticker": ticker, "status": "TIMEOUT"}
    dt = time.time()-t0
    fc_gates = check_fail_closed(ws, run_id, ticker)
    rr_path = f"{ws}/run-result.json"
    if not os.path.exists(rr_path):
        print(f"  ❌ no run-result.json; stderr: {proc.stderr[-300:]}", flush=True)
        return {"run_id": run_id, "ticker": ticker, "status": "NO_RESULT", "fail_closed_gates": fc_gates}
    rr = json.load(open(rr_path))
    rr["artifact_type"] = classify_artifact(ws)
    rr["wall_duration_s"] = round(dt, 1)
    rr["fail_closed_gates"] = fc_gates
    rr["slo_latency_ok"] = dt <= SLO_LATENCY_ABSOLUTE_MAX
    rr["html_artifact_sha256"] = sha256_file(next((os.path.join(ws,f) for f in os.listdir(ws) if f.endswith(".html")), ""))
    json.dump(rr, open(rr_path,"w"), indent=2, ensure_ascii=False)
    fc_status = "BLOCKED" if fc_gates else "PASS"
    print(f"  verdict={rr.get('final_verdict')} pass={rr.get('validator_results',{}).get('pass')} "
          f"fail={rr.get('validator_results',{}).get('fail')} artifact={rr['artifact_type']} "
          f"dt={dt:.0f}s fail_closed={fc_status}", flush=True)
    return rr


def update_manifest(run_record):
    manifest = {"completed_jobs": [], "protocol": "v0.11.1"}
    if os.path.exists(MANIFEST_PATH):
        manifest = json.load(open(MANIFEST_PATH))
    manifest["completed_jobs"].append({
        "run_id": run_record.get("run_id"), "ticker": run_record.get("ticker"),
        "execution_type": run_record.get("execution_type"),
        "final_verdict": run_record.get("final_verdict"),
        "pass": run_record.get("validator_results",{}).get("pass"),
        "fail": run_record.get("validator_results",{}).get("fail"),
        "requirements_failed": run_record.get("requirements_failed"),
        "artifact_type": run_record.get("artifact_type"),
        "duration_seconds": run_record.get("wall_duration_s"),
        "fail_closed_gates": run_record.get("fail_closed_gates", []),
        "slo_latency_ok": run_record.get("slo_latency_ok"),
        "completed_at": datetime.datetime.now().isoformat(),
    })
    manifest["last_updated"] = datetime.datetime.now().isoformat()
    json.dump(manifest, open(MANIFEST_PATH,"w"), indent=2, ensure_ascii=False)


def main():
    os.makedirs(SHADOW_DIR, exist_ok=True)
    # Preflight
    proc = subprocess.run([PY, f"{AE}/runner/environment_preflight.py"], capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        print("🛑 ENVIRONMENT_NOT_QUALIFIED", flush=True); sys.exit(3)
    print("✓ Environment preflight PASS\n", flush=True)

    print(f"\n{'#'*70}\n#  SHADOW BATCH 1″ — 10 fresh-ticker jobs under protocol v0.11.1\n{'#'*70}\n", flush=True)
    runs = []
    for i, (run_id, ticker) in enumerate(RUNS, 1):
        rr = run_one(run_id, ticker, i, len(RUNS))
        runs.append(rr)
        update_manifest(rr)

    # Summary
    n = len(runs)
    n_pass = sum(1 for r in runs if r.get("final_verdict")=="PASS")
    print(f"\n{'='*70}\n  BATCH 1″ SUMMARY — {n}/{len(RUNS)} jobs\n{'='*70}", flush=True)
    print(f"  PASS: {n_pass}/{n}", flush=True)
    by_ticker = {}
    for r in runs:
        t = r.get("ticker","?")
        by_ticker.setdefault(t,[]).append(r.get("final_verdict"))
    print(f"\n  Per-ticker:", flush=True)
    for t in sorted(by_ticker):
        vs = by_ticker[t]
        p = sum(1 for v in vs if v=="PASS")
        print(f"    {t}: {p}/{len(vs)} PASS  {vs}", flush=True)
    # REQ monitoring
    req025 = sum(1 for r in runs if "REQ-025" in (r.get("requirements_failed") or []))
    req019 = sum(1 for r in runs if "REQ-019" in (r.get("requirements_failed") or []))
    req020 = sum(1 for r in runs if "REQ-020" in (r.get("requirements_failed") or []))
    req027 = sum(1 for r in runs if "REQ-027" in (r.get("requirements_failed") or []))
    no_0_of_2 = all(sum(1 for v in vs if v=="PASS")>0 for vs in by_ticker.values())
    print(f"\n  RELEASE GATE:", flush=True)
    print(f"    final_PASS: {n_pass}/10 (need >=9)  {'✓' if n_pass>=9 else '✗'}", flush=True)
    print(f"    no_ticker_0_of_2: {no_0_of_2}  {'✓' if no_0_of_2 else '✗'}", flush=True)
    print(f"    REQ-025: {req025}/10 (0=stable, 1=variance, 2+=block)", flush=True)
    print(f"    REQ-019: {req019}/10  REQ-020: {req020}/10  REQ-027: {req027}/10", flush=True)
    json.dump({"jobs":n, "pass":n_pass, "per_ticker":{t:{"pass":sum(1 for v in vs if v=="PASS"),"total":len(vs)} for t,vs in by_ticker.items()},
               "req025":req025,"req019":req019,"req020":req020,"req027":req027,"protocol":"v0.11.1"},
              open(f"{AE}/cohort-c/shadow-b1dp-summary.json","w"), indent=2)


if __name__ == "__main__":
    main()
