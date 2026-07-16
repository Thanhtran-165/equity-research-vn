#!/usr/bin/env python3
"""Targeted Validation v5 (8 runs, protocol v0.12.0)."""
import subprocess, sys, os, json, time, datetime, hashlib, shutil
AE = "/Users/bobo/ZCodeProject/agent-eval"
PROTO = "94a64b3a57c1f95a7e388a35780532e5ba19e1abd555a061ab4a845227a624eb"
PY = "/opt/homebrew/bin/python3"
os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")
DIR = f"{AE}/cohort-c/targeted-v5"
MANIFEST = f"{AE}/cohort-c/targeted-v5-manifest.json"
RUNS = [
    ("TV5-ACB-01", "ACB", "shadow/source-packs-fresh"),
    ("TV5-ACB-02", "ACB", "shadow/source-packs-fresh"),
    ("TV5-GEX-01", "GEX", "shadow/source-packs-fresh"),
    ("TV5-GEX-02", "GEX", "shadow/source-packs-fresh"),
    ("TV5-GAS-01", "GAS", "shadow/source-packs"),
    ("TV5-CTD-01", "CTD", "source-packs"),
    ("TV5-SAB-01", "SAB", "shadow/source-packs-fresh"),
    ("TV5-SSI-01", "SSI", "shadow/source-packs-fresh"),
]

def sha(p): return hashlib.sha256(open(p,"rb").read()).hexdigest() if os.path.exists(p) else None
def classify(ws):
    for f in os.listdir(ws):
        if f.endswith("_Complete_Report.html"):
            h=open(os.path.join(ws,f)).read(100).lstrip()
            return "HTML" if h.startswith("<") else "NARRATION"
    return "NO_ARTIFACT"

def run_one(run_id, ticker, pack_subdir, idx, total):
    ws = f"{DIR}/{run_id}"
    if os.path.exists(ws): shutil.rmtree(ws)
    os.makedirs(ws, exist_ok=True)
    src = f"{AE}/cohort-c/{pack_subdir}/{ticker}"
    print(f"\n{'='*70}\n  TV5 run {idx}/{total} — {run_id} ({ticker})\n{'='*70}", flush=True)
    t0 = time.time()
    proc = subprocess.run([PY, f"{AE}/runner/agent_runner.py",
        run_id, "targeted-v5", ws, src, ticker,
        "--scored", "true", "--model-backend", "zai", "--model-id", "GLM-5.2",
        "--protocol-sha256", PROTO], capture_output=True, text=True, timeout=3300, env=os.environ)
    dt = time.time()-t0
    rr_path = f"{ws}/run-result.json"
    if not os.path.exists(rr_path):
        print(f"  ❌ no result; stderr: {proc.stderr[-200:]}", flush=True)
        return {"run_id": run_id, "ticker": ticker, "status": "NO_RESULT"}
    rr = json.load(open(rr_path))
    rr["wall_duration_s"] = round(dt,1)
    json.dump(rr, open(rr_path,"w"), indent=2, ensure_ascii=False)
    print(f"  verdict={rr.get('final_verdict')} pass={rr.get('validator_results',{}).get('pass')} "
          f"fail={rr.get('validator_results',{}).get('fail')} dt={dt:.0f}s | {rr.get('requirements_failed')}", flush=True)
    return rr

def update_manifest(r):
    m = {"completed_runs": [], "protocol": "v0.12.0"}
    if os.path.exists(MANIFEST): m = json.load(open(MANIFEST))
    m["completed_runs"].append({"run_id":r.get("run_id"),"ticker":r.get("ticker"),
        "final_verdict":r.get("final_verdict"),
        "pass":r.get("validator_results",{}).get("pass"),
        "fail":r.get("validator_results",{}).get("fail"),
        "requirements_failed":r.get("requirements_failed"),
        "duration_seconds":r.get("wall_duration_s"),
        "completed_at":datetime.datetime.now().isoformat()})
    m["last_updated"] = datetime.datetime.now().isoformat()
    json.dump(m, open(MANIFEST,"w"), indent=2, ensure_ascii=False)

def main():
    os.makedirs(DIR, exist_ok=True)
    proc = subprocess.run([PY, f"{AE}/runner/environment_preflight.py"], capture_output=True, text=True, timeout=60)
    if proc.returncode != 0: print("🛑 ENV NOT QUALIFIED"); sys.exit(3)
    print("✓ Environment preflight PASS\n", flush=True)
    print(f"\n{'#'*70}\n#  TARGETED VALIDATION v5 — Protocol v0.12.0\n{'#'*70}\n", flush=True)
    runs = []
    for i, (run_id, ticker, subdir) in enumerate(RUNS, 1):
        rr = run_one(run_id, ticker, subdir, i, len(RUNS))
        runs.append(rr); update_manifest(rr)
    n_pass = sum(1 for r in runs if r.get("final_verdict")=="PASS")
    print(f"\n{'='*70}\n  TV5 SUMMARY — {len(runs)} runs, PASS: {n_pass}/{len(runs)}\n{'='*70}")
    for r in runs:
        print(f"  {r.get('run_id')} {r.get('ticker')}: {r.get('final_verdict')} pass={r.get('pass')} | {r.get('requirements_failed')}")
    req013 = sum(1 for r in runs if "REQ-013" in (r.get("requirements_failed") or []))
    req025 = sum(1 for r in runs if "REQ-025" in (r.get("requirements_failed") or []))
    print(f"\n  REQ-013: {req013}/8  REQ-025: {req025}/8")

if __name__ == "__main__":
    main()
