#!/usr/bin/env python3
"""
run_tier1_validation.py — Tier 1 targeted validation (6 runs under protocol v0.8.0).

Validates the 3 fixes from Cohort C before committing to a full 10-run cohort:
  1. Banking builder fix (VCB ×2): REQ-023/025 should now PASS
  2. Content-depth gate (KDH ×1, FPT ×1): REQ-013 should be caught/recovered
  3. Clean controls (CTD ×1, PNJ ×1): no regression

Environment preflight MUST pass before this runs (vnstock_data + GLM backend).
Corrected PATH (/opt/homebrew/bin first) ensures verifier's python3 finds vnstock_data.
"""
import subprocess, sys, os, json, time, datetime, hashlib

AE = "/Users/bobo/ZCodeProject/agent-eval"
PROTO = "cad6e183d7a52135c872aa0b5f4b01a0f6252b3f05cc39229968a3f9710a3848"
PY = "/opt/homebrew/bin/python3"

# CRITICAL: prepend /opt/homebrew/bin so verifier's `python3` subprocess finds vnstock_data
os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")

RUNS = [
    ("T-VCB-01", "VCB", "banking builder fix"),
    ("T-VCB-02", "VCB", "banking builder fix (2nd)"),
    ("T-KDH-01", "KDH", "content-depth gate (had REQ-013)"),
    ("T-FPT-01", "FPT", "content-depth gate (had REQ-013)"),
    ("T-CTD-01", "CTD", "clean control"),
    ("T-PNJ-01", "PNJ", "clean control"),
]

TIER1_DIR = f"{AE}/cohort-c/tier1-validation"
MANIFEST_PATH = f"{AE}/cohort-c/tier1-manifest.json"


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
    """Run environment preflight. Returns True if qualified."""
    proc = subprocess.run([PY, f"{AE}/runner/environment_preflight.py"],
                          capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        print(f"\n🛑 ENVIRONMENT_NOT_QUALIFIED — cannot start Tier 1.\n", flush=True)
        print(proc.stdout, flush=True)
        return False
    print(f"\n✓ Environment preflight PASS — starting Tier 1.\n", flush=True)
    return True


def run_one(run_id, ticker, purpose, idx, total):
    ws = f"{TIER1_DIR}/{run_id}"
    if os.path.exists(ws):
        import shutil; shutil.rmtree(ws)
    os.makedirs(ws, exist_ok=True)
    src_pack = f"{AE}/cohort-c/source-packs/{ticker}"
    print(f"\n{'='*70}\n  TIER 1 run {idx}/{total} — {run_id} (ticker={ticker}, {purpose})\n{'='*70}", flush=True)
    t0 = time.time()
    try:
        proc = subprocess.run([PY, f"{AE}/runner/agent_runner.py",
            run_id, "tier1-validation", ws, src_pack, ticker,
            "--scored", "true", "--model-backend", "zai", "--model-id", "GLM-5.2",
            "--protocol-sha256", PROTO], capture_output=True, text=True, timeout=3000,
            env=os.environ)
    except subprocess.TimeoutExpired:
        print(f"  ❌ TIMEOUT (logical run {run_id})", flush=True)
        return {"run_id": run_id, "ticker": ticker, "status": "TIMEOUT"}
    dt = time.time()-t0
    rr_path = f"{ws}/run-result.json"
    if not os.path.exists(rr_path):
        print(f"  ❌ no run-result.json (rc={proc.returncode}); stderr: {proc.stderr[-300:]}", flush=True)
        return {"run_id": run_id, "ticker": ticker, "status": "NO_RESULT", "returncode": proc.returncode}
    rr = json.load(open(rr_path))
    rr["artifact_type"] = classify_artifact(ws)
    rr["wall_duration_s"] = round(dt, 1)
    rr["html_artifact_sha256"] = sha256_file(next((os.path.join(ws,f) for f in os.listdir(ws) if f.endswith(".html")), ""))
    json.dump(rr, open(rr_path,"w"), indent=2, ensure_ascii=False)
    # Extract content-depth gate result from phase events
    cdg = None
    for pe in rr.get("phase_events", []):
        pf = pe.get("phase6_preflight")
        if pf and pf.get("content_depth_gate"):
            cdg = pf["content_depth_gate"]
    print(f"  execution_type={rr.get('execution_type')} verdict={rr.get('final_verdict')} "
          f"pass={rr.get('validator_results',{}).get('pass')} fail={rr.get('validator_results',{}).get('fail')} "
          f"artifact={rr['artifact_type']} dt={dt:.0f}s", flush=True)
    if cdg:
        print(f"  content_depth_gate: passed={cdg.get('passed')} sections_failed={cdg.get('sections_failed')}", flush=True)
    return rr


def update_manifest(run_record):
    manifest = {"completed_runs": [], "protocol": "v0.8.0"}
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
    os.makedirs(TIER1_DIR, exist_ok=True)
    if not run_preflight():
        sys.exit(3)
    runs = []
    print(f"\n{'#'*70}\n#  TIER 1 — 6 targeted validation runs under protocol v0.8.0\n{'#'*70}\n", flush=True)
    for i, (run_id, ticker, purpose) in enumerate(RUNS, 1):
        rr = run_one(run_id, ticker, purpose, i, len(RUNS))
        runs.append(rr)
        update_manifest(rr)
    # Summary
    n = len(runs)
    n_pass = sum(1 for r in runs if r.get("final_verdict")=="PASS")
    print(f"\n{'='*70}\n  TIER 1 SUMMARY — {n}/{len(RUNS)} runs\n{'='*70}", flush=True)
    print(f"  PASS: {n_pass}/{n}", flush=True)
    for r in runs:
        print(f"  {r.get('run_id')} {r.get('ticker')}: {r.get('final_verdict')} "
              f"pass={r.get('validator_results',{}).get('pass')} fail={r.get('validator_results',{}).get('fail')} "
              f"| {r.get('requirements_failed')}", flush=True)
    # Tier 1 pass criteria
    vcb_runs = [r for r in runs if r.get("ticker")=="VCB"]
    vcb_023_025_pass = all("REQ-023" not in (r.get("requirements_failed") or []) and
                           "REQ-025" not in (r.get("requirements_failed") or [])
                           for r in vcb_runs) if vcb_runs else False
    req013_count = sum(1 for r in runs if "REQ-013" in (r.get("requirements_failed") or []))
    clean_controls = [r for r in runs if r.get("ticker") in ("CTD","PNJ")]
    clean_ok = all(r.get("final_verdict") in ("PASS",) or
                   set(r.get("requirements_failed") or []) <= {"REQ-021"}
                   for r in clean_controls) if clean_controls else False
    print(f"\n  TIER 1 CRITERIA:", flush=True)
    print(f"    VCB REQ-023/025 PASS 2/2: {vcb_023_025_pass}", flush=True)
    print(f"    REQ-013 occurrences: {req013_count}/6 (target: 0 or 1)", flush=True)
    print(f"    Clean controls (CTD/PNJ) no regression: {clean_ok}", flush=True)
    tier1_pass = vcb_023_025_pass and req013_count <= 1 and clean_ok
    print(f"\n  → TIER 1 {'PASS — proceed to Cohort C′' if tier1_pass else 'INCONCLUSIVE — review before C′'}", flush=True)
    json.dump({"runs": n, "pass": n_pass, "tier1_pass": tier1_pass,
               "vcb_023_025_pass": vcb_023_025_pass, "req013_count": req013_count,
               "protocol": "v0.8.0"}, open(f"{AE}/cohort-c/tier1-summary.json","w"), indent=2)


if __name__ == "__main__":
    main()
