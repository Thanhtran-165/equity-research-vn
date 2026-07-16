#!/usr/bin/env python3
"""
run_targeted_v4.py — Targeted validation v4 (8 runs, protocol v0.11.0).

Validates the three artifact-integrity hardening branches:
  VNM ×2: DATA contract enforcer (REQ-026 netProfit key fix)
  MWG ×2: REQ-027 qualifier variance
  HPG ×1: JS syntax gate (REQ-019)
  GAS ×1: clean control
  BID ×1: clean control
  CTD ×1: regression control (benchmark ticker)
"""
import subprocess, sys, os, json, time, datetime, hashlib, shutil

AE = "/Users/bobo/ZCodeProject/agent-eval"
PROTO = ""
PY = "/opt/homebrew/bin/python3"
os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")

TARGETED_DIR = f"{AE}/cohort-c/targeted-v4"
MANIFEST_PATH = f"{AE}/cohort-c/targeted-v4-manifest.json"

RUNS = [
    ("TV4-VNM-01", "VNM", "data-enforcer", f"{AE}/cohort-c/shadow/source-packs/VNM"),
    ("TV4-VNM-02", "VNM", "data-enforcer", f"{AE}/cohort-c/shadow/source-packs/VNM"),
    ("TV4-MWG-01", "MWG", "req027-qualifier", f"{AE}/cohort-c/shadow/source-packs/MWG"),
    ("TV4-MWG-02", "MWG", "req027-qualifier", f"{AE}/cohort-c/shadow/source-packs/MWG"),
    ("TV4-HPG-01", "HPG", "js-syntax-gate", f"{AE}/cohort-c/shadow/source-packs/HPG"),
    ("TV4-GAS-01", "GAS", "clean-control", f"{AE}/cohort-c/shadow/source-packs/GAS"),
    ("TV4-BID-01", "BID", "clean-control", f"{AE}/cohort-c/shadow/source-packs/BID"),
    ("TV4-CTD-01", "CTD", "regression-control", f"{AE}/cohort-c/source-packs/CTD"),
]


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


def run_one(run_id, ticker, purpose, src_pack, idx, total):
    ws = f"{TARGETED_DIR}/{run_id}"
    if os.path.exists(ws):
        shutil.rmtree(ws)
    os.makedirs(ws, exist_ok=True)
    print(f"\n{'='*70}\n  TARGETED v4 run {idx}/{total} — {run_id} ({ticker}, {purpose})\n{'='*70}", flush=True)
    t0 = time.time()
    try:
        proc = subprocess.run([PY, f"{AE}/runner/agent_runner.py",
            run_id, "targeted-v4", ws, src_pack, ticker,
            "--scored", "true", "--model-backend", "zai", "--model-id", "GLM-5.2",
            "--protocol-sha256", PROTO], capture_output=True, text=True, timeout=3300,
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
    rr["purpose"] = purpose
    json.dump(rr, open(rr_path,"w"), indent=2, ensure_ascii=False)
    # Extract gate results
    for pe in rr.get("phase_events", []):
        pf = pe.get("phase6_preflight", {})
        if pf:
            for gate in ["content_depth_gate", "no_source_claim_gate",
                         "artifact_integrity_gate", "data_contract_enforcer"]:
                if pf.get(gate):
                    print(f"  {gate}: {pf[gate]}", flush=True)
    print(f"  verdict={rr.get('final_verdict')} pass={rr.get('validator_results',{}).get('pass')} "
          f"fail={rr.get('validator_results',{}).get('fail')} dt={dt:.0f}s | {rr.get('requirements_failed')}", flush=True)
    return rr


def update_manifest(run_record):
    manifest = {"completed_runs": [], "protocol": "v0.11.0"}
    if os.path.exists(MANIFEST_PATH):
        manifest = json.load(open(MANIFEST_PATH))
    manifest["completed_runs"].append({
        "run_id": run_record.get("run_id"),
        "ticker": run_record.get("ticker"),
        "purpose": run_record.get("purpose"),
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
    os.makedirs(TARGETED_DIR, exist_ok=True)
    print(f"\n{'#'*70}\n#  TARGETED VALIDATION v4 — Protocol v0.11.0\n#  DATA enforcer + integrity gate + two-tier REQ-027\n{'#'*70}\n", flush=True)

    # Environment preflight
    proc = subprocess.run([PY, f"{AE}/runner/environment_preflight.py"], capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        print("🛑 ENVIRONMENT_NOT_QUALIFIED\n", flush=True); sys.exit(3)
    print("✓ Environment preflight PASS\n", flush=True)

    runs = []
    for i, (run_id, ticker, purpose, src_pack) in enumerate(RUNS, 1):
        rr = run_one(run_id, ticker, purpose, src_pack, i, len(RUNS))
        runs.append(rr)
        update_manifest(rr)

    # Summary
    n_pass = sum(1 for r in runs if r.get("final_verdict") == "PASS")
    print(f"\n{'='*70}\n  TARGETED v4 SUMMARY — {len(runs)} runs\n{'='*70}", flush=True)
    print(f"  PASS: {n_pass}/{len(runs)}", flush=True)
    for r in runs:
        print(f"  {r.get('run_id')} {r.get('ticker')} ({r.get('purpose')}): {r.get('final_verdict')} "
              f"pass={r.get('validator_results',{}).get('pass')} fail={r.get('validator_results',{}).get('fail')} "
              f"| {r.get('requirements_failed')}", flush=True)

    # Criteria
    vnm = [r for r in runs if r.get("ticker")=="VNM"]
    mwg = [r for r in runs if r.get("ticker")=="MWG"]
    hpg = [r for r in runs if r.get("ticker")=="HPG"]
    controls = [r for r in runs if r.get("purpose") in ("clean-control","regression-control")]
    print(f"\n  CRITERIA:", flush=True)
    print(f"    VNM REQ-026 2/2 PASS: {sum(1 for r in vnm if 'REQ-026' not in (r.get('requirements_failed') or []) and r.get('final_verdict')=='PASS')}/2", flush=True)
    print(f"    VNM+MWG REQ-027 4/4 PASS: {sum(1 for r in vnm+mwg if 'REQ-027' not in (r.get('requirements_failed') or []) and r.get('final_verdict')=='PASS')}/4", flush=True)
    print(f"    HPG JS syntax: {'PASS' if all('REQ-019' not in (r.get('requirements_failed') or []) for r in hpg) else 'FAIL'}", flush=True)
    print(f"    Clean controls: {sum(1 for r in controls if r.get('final_verdict')=='PASS')}/{len(controls)}", flush=True)


if __name__ == "__main__":
    main()
