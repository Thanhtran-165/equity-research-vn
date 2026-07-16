#!/usr/bin/env python3
"""
run_cohort_c_prime.py — Cohort C′ full cross-ticker validation (10 runs, protocol v0.8.1).

The clean-verifier cohort: REQ-007 false positive fixed, banking builder hardened,
content-depth gate active, environment PATH corrected. This is the release-grade
cohort that determines STABLE_CANDIDATE.
"""
import subprocess, sys, os, json, time, datetime, hashlib

AE = "/Users/bobo/ZCodeProject/agent-eval"
PROTO = "3695c58843c4281140f89265006dde5c1931e4242bd4f564dfa3211c1ee9a3ec"
PY = "/opt/homebrew/bin/python3"
os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")

RUNS = [
    ("Cp-CTD-01", "CTD"), ("Cp-CTD-02", "CTD"),
    ("Cp-KDH-01", "KDH"), ("Cp-KDH-02", "KDH"),
    ("Cp-PNJ-01", "PNJ"), ("Cp-PNJ-02", "PNJ"),
    ("Cp-VCB-01", "VCB"), ("Cp-VCB-02", "VCB"),
    ("Cp-FPT-01", "FPT"), ("Cp-FPT-02", "FPT"),
]

COHORT_DIR = f"{AE}/cohort-c/cohort-c-prime"
MANIFEST_PATH = f"{AE}/cohort-c/cohort-c-prime-manifest.json"


def classify_artifact(workspace):
    for f in os.listdir(workspace):
        if f.endswith("_Complete_Report.html"):
            head = open(os.path.join(workspace,f)).read(100).lstrip()
            if head.startswith("<") or "<section" in head[:500] or "<!DOCTYPE" in head[:50]:
                return "HTML"
            return "NARRATION"
    return "NO_ARTIFACT"


def sha256_file(p):
    return hashlib.sha256(open(p,"rb").read()).hexdigest() if os.path.exists(p) else None


def run_preflight():
    proc = subprocess.run([PY, f"{AE}/runner/environment_preflight.py"],
                          capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        print(f"\n🛑 ENVIRONMENT_NOT_QUALIFIED — cannot start Cohort C′.\n", flush=True)
        return False
    print(f"\n✓ Environment preflight PASS — starting Cohort C′.\n", flush=True)
    return True


def run_one(run_id, ticker, idx, total):
    ws = f"{COHORT_DIR}/{run_id}"
    if os.path.exists(ws):
        import shutil; shutil.rmtree(ws)
    os.makedirs(ws, exist_ok=True)
    src_pack = f"{AE}/cohort-c/source-packs/{ticker}"
    print(f"\n{'='*70}\n  COHORT C′ run {idx}/{total} — {run_id} (ticker={ticker})\n{'='*70}", flush=True)
    t0 = time.time()
    try:
        proc = subprocess.run([PY, f"{AE}/runner/agent_runner.py",
            run_id, "cohort-c-prime", ws, src_pack, ticker,
            "--scored", "true", "--model-backend", "zai", "--model-id", "GLM-5.2",
            "--protocol-sha256", PROTO], capture_output=True, text=True, timeout=3000,
            env=os.environ)
    except subprocess.TimeoutExpired:
        print(f"  ❌ TIMEOUT ({run_id})", flush=True)
        return {"run_id": run_id, "ticker": ticker, "status": "TIMEOUT"}
    dt = time.time()-t0
    rr_path = f"{ws}/run-result.json"
    if not os.path.exists(rr_path):
        print(f"  ❌ no run-result.json (rc={proc.returncode}); stderr: {proc.stderr[-300:]}", flush=True)
        return {"run_id": run_id, "ticker": ticker, "status": "NO_RESULT"}
    rr = json.load(open(rr_path))
    rr["artifact_type"] = classify_artifact(ws)
    rr["wall_duration_s"] = round(dt, 1)
    rr["html_artifact_sha256"] = sha256_file(next((os.path.join(ws,f) for f in os.listdir(ws) if f.endswith(".html")), ""))
    json.dump(rr, open(rr_path,"w"), indent=2, ensure_ascii=False)
    print(f"  execution_type={rr.get('execution_type')} verdict={rr.get('final_verdict')} "
          f"pass={rr.get('validator_results',{}).get('pass')} fail={rr.get('validator_results',{}).get('fail')} "
          f"artifact={rr['artifact_type']} dt={dt:.0f}s", flush=True)
    return rr


def update_manifest(run_record):
    manifest = {"completed_runs": [], "protocol": "v0.8.1"}
    if os.path.exists(MANIFEST_PATH):
        manifest = json.load(open(MANIFEST_PATH))
    manifest["completed_runs"].append({
        "run_id": run_record.get("run_id"),
        "ticker": run_record.get("ticker"),
        "execution_type": run_record.get("execution_type"),
        "final_verdict": run_record.get("final_verdict"),
        "pass": run_record.get("validator_results",{}).get("pass"),
        "fail": run_record.get("validator_results",{}).get("fail"),
        "requirements_failed": run_record.get("requirements_failed"),
        "artifact_type": run_record.get("artifact_type"),
        "duration_seconds": run_record.get("wall_duration_s"),
        "completed_at": datetime.datetime.now().isoformat(),
    })
    manifest["last_updated"] = datetime.datetime.now().isoformat()
    json.dump(manifest, open(MANIFEST_PATH,"w"), indent=2, ensure_ascii=False)


def main():
    os.makedirs(COHORT_DIR, exist_ok=True)
    if not run_preflight():
        sys.exit(3)
    runs = []
    print(f"\n{'#'*70}\n#  COHORT C′ — 10 cross-ticker genuine runs under protocol v0.8.1\n#  Clean verifier (0.1.5), banking-hardened builder, content-depth gate\n{'#'*70}\n", flush=True)
    for i, (run_id, ticker) in enumerate(RUNS, 1):
        rr = run_one(run_id, ticker, i, len(RUNS))
        runs.append(rr)
        update_manifest(rr)
        if i % 2 == 0 and i < len(RUNS):
            n_pass = sum(1 for r in runs if r.get("final_verdict")=="PASS")
            print(f"\n  --- Checkpoint {i}/{len(RUNS)}: {n_pass}/{i} PASS (no early conclusions) ---\n", flush=True)
    # Final summary
    n = len(runs)
    n_pass = sum(1 for r in runs if r.get("final_verdict")=="PASS")
    print(f"\n{'='*70}\n  COHORT C′ SUMMARY — {n}/{len(RUNS)} runs\n{'='*70}", flush=True)
    print(f"  PASS: {n_pass}/{n}", flush=True)
    by_ticker = {}
    for r in runs:
        t = r.get("ticker","?")
        by_ticker.setdefault(t, []).append(r.get("final_verdict"))
    print(f"\n  Per-ticker:", flush=True)
    for t in sorted(by_ticker):
        vs = by_ticker[t]
        p = sum(1 for v in vs if v=="PASS")
        print(f"    {t}: {p}/{len(vs)} PASS  {vs}", flush=True)
    # Release gate
    req020 = sum(1 for r in runs if "REQ-020" in (r.get("requirements_failed") or []))
    req025 = sum(1 for r in runs if "REQ-025" in (r.get("requirements_failed") or []))
    req013 = sum(1 for r in runs if "REQ-013" in (r.get("requirements_failed") or []))
    any_0_of_2 = any(sum(1 for v in vs if v=="PASS")==0 for vs in by_ticker.values())
    print(f"\n  RELEASE GATE:", flush=True)
    print(f"    final_PASS: {n_pass}/10 (need ≥9)", flush=True)
    print(f"    REQ-013: {req013}/10 (need ≤1)", flush=True)
    print(f"    REQ-020: {req020}/10 (need ≤1)", flush=True)
    print(f"    REQ-025: {req025}/10 (need ≤1)", flush=True)
    print(f"    any ticker 0/2: {any_0_of_2} (need false)", flush=True)
    if n_pass >= 9 and req013 <= 1 and req020 <= 1 and req025 <= 1 and not any_0_of_2:
        print(f"\n  → STABLE_CANDIDATE ✓", flush=True)
    else:
        print(f"\n  → NOT YET STABLE_CANDIDATE — review defects", flush=True)
    json.dump({"completed_runs":n, "pass":n_pass, "per_ticker":{t:{"pass":sum(1 for v in vs if v=="PASS"),"total":len(vs)} for t,vs in by_ticker.items()},
               "req013":req013, "req020":req020, "req025":req025, "protocol":"v0.8.1"},
              open(f"{AE}/cohort-c/cohort-c-prime-summary.json","w"), indent=2)


if __name__ == "__main__":
    main()
