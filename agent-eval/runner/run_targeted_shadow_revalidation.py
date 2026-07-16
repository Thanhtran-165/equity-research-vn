#!/usr/bin/env python3
"""
run_targeted_shadow_revalidation.py — 7-run targeted validation (protocol v0.9.1).

Validates the three hardening branches before committing to Shadow Batch 1′:
  VNM-complete ×2: source-pack fix + no-source gate (was 0/2 FAIL)
  VNM-zero-news ×1: negative control (empty news, verify gate prevents memory fill)
  GAS ×2: chart initialization consistency (was 1/2, GAS-02 had 0 charts)
  BID ×1: clean control (was 2/2 PASS)
  MWG ×1: clean control (was 2/2 PASS)

Pre-runs source-pack semantic readiness + environment preflight before any GLM run.
"""
import subprocess, sys, os, json, time, datetime, hashlib, shutil

AE = "/Users/bobo/ZCodeProject/agent-eval"
PROTO = "f1c7df7ef066439f5601c04085d5ec299e8666966b2c93f47df8fd75c1928496"
PY = "/opt/homebrew/bin/python3"
os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")

TARGETED_DIR = f"{AE}/cohort-c/targeted-revalidation"
MANIFEST_PATH = f"{AE}/cohort-c/targeted-manifest.json"

# Build VNM zero-news pack (copy complete pack but empty events/news)
VNM_ZERO_NEWS_PACK = f"{AE}/cohort-c/shadow/source-packs/VNM-zero-news"

RUNS = [
    ("TV-VNM-01", "VNM", "complete-pack", f"{AE}/cohort-c/shadow/source-packs/VNM"),
    ("TV-VNM-02", "VNM", "complete-pack", f"{AE}/cohort-c/shadow/source-packs/VNM"),
    ("TV-VNM-ZN", "VNM", "zero-news-control", VNM_ZERO_NEWS_PACK),
    ("TV-GAS-01", "GAS", "chart-consistency", f"{AE}/cohort-c/shadow/source-packs/GAS"),
    ("TV-GAS-02", "GAS", "chart-consistency", f"{AE}/cohort-c/shadow/source-packs/GAS"),
    ("TV-BID-01", "BID", "clean-control", f"{AE}/cohort-c/shadow/source-packs/BID"),
    ("TV-MWG-01", "MWG", "clean-control", f"{AE}/cohort-c/shadow/source-packs/MWG"),
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


def prepare_vnm_zero_news():
    """Create VNM zero-news pack: complete financials but empty events/news."""
    src = f"{AE}/cohort-c/shadow/source-packs/VNM"
    if os.path.exists(VNM_ZERO_NEWS_PACK):
        shutil.rmtree(VNM_ZERO_NEWS_PACK)
    shutil.copytree(src, VNM_ZERO_NEWS_PACK)
    # Empty the news/events files (but keep them parseable — header only)
    with open(os.path.join(VNM_ZERO_NEWS_PACK, "events.csv"), "w") as f:
        f.write("date,event,impact\n")
    json.dump({"events": []}, open(os.path.join(VNM_ZERO_NEWS_PACK, "news_digest.json"), "w"))
    with open(os.path.join(VNM_ZERO_NEWS_PACK, "news.csv"), "w") as f:
        f.write("date,title,source,url\n")
    print("  VNM zero-news pack prepared (financials complete, events/news empty)")


def run_one(run_id, ticker, purpose, src_pack, idx, total):
    ws = f"{TARGETED_DIR}/{run_id}"
    if os.path.exists(ws):
        shutil.rmtree(ws)
    os.makedirs(ws, exist_ok=True)
    print(f"\n{'='*70}\n  TARGETED run {idx}/{total} — {run_id} ({ticker}, {purpose})\n{'='*70}", flush=True)
    t0 = time.time()
    try:
        proc = subprocess.run([PY, f"{AE}/runner/agent_runner.py",
            run_id, "targeted-revalidation", ws, src_pack, ticker,
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
    rr["html_artifact_sha256"] = sha256_file(next((os.path.join(ws,f) for f in os.listdir(ws) if f.endswith(".html")), ""))
    json.dump(rr, open(rr_path,"w"), indent=2, ensure_ascii=False)
    # Extract gate results
    for pe in rr.get("phase_events", []):
        pf = pe.get("phase6_preflight", {})
        if pf:
            cdg = pf.get("content_depth_gate")
            nscg = pf.get("no_source_claim_gate")
            if cdg or nscg:
                print(f"  gates: content_depth={cdg} no_source={nscg}", flush=True)
    print(f"  verdict={rr.get('final_verdict')} pass={rr.get('validator_results',{}).get('pass')} "
          f"fail={rr.get('validator_results',{}).get('fail')} artifact={rr['artifact_type']} dt={dt:.0f}s", flush=True)
    return rr


def update_manifest(run_record):
    manifest = {"completed_runs": [], "protocol": "v0.9.1"}
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

    # Pre-flight checks
    print(f"\n{'#'*70}\n#  TARGETED REVALIDATION — Protocol v0.9.1\n{'#'*70}\n", flush=True)

    # Environment preflight
    proc = subprocess.run([PY, f"{AE}/runner/environment_preflight.py"], capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        print("🛑 ENVIRONMENT_NOT_QUALIFIED\n", flush=True); sys.exit(3)
    print("✓ Environment preflight PASS\n", flush=True)

    # Prepare VNM zero-news control
    print("Preparing VNM zero-news control pack...", flush=True)
    prepare_vnm_zero_news()

    # Source-pack semantic readiness for all packs used
    print("\nSource-pack semantic readiness:", flush=True)
    packs_to_check = [
        ("VNM", f"{AE}/cohort-c/shadow/source-packs/VNM"),
        ("VNM-zero-news", VNM_ZERO_NEWS_PACK),
        ("GAS", f"{AE}/cohort-c/shadow/source-packs/GAS"),
        ("BID", f"{AE}/cohort-c/shadow/source-packs/BID"),
        ("MWG", f"{AE}/cohort-c/shadow/source-packs/MWG"),
    ]
    # Note: VNM-zero-news is EXPECTED to fail news readiness (that's the point of the control)
    for ticker, pack in packs_to_check:
        proc = subprocess.run([PY, f"{AE}/runner/source_pack_readiness.py", pack, ticker.split("-")[0]],
                              capture_output=True, text=True, timeout=30)
        status = "READY" if proc.returncode == 0 else "NOT-READY"
        if "zero-news" in ticker:
            status = "EXPECTED-NOT-READY (control)"
        print(f"  {ticker}: {status}", flush=True)

    # Run 7 targeted validations
    print(f"\nStarting {len(RUNS)} targeted runs...\n", flush=True)
    runs = []
    for i, (run_id, ticker, purpose, src_pack) in enumerate(RUNS, 1):
        rr = run_one(run_id, ticker, purpose, src_pack, i, len(RUNS))
        runs.append(rr)
        update_manifest(rr)

    # Summary
    n_pass = sum(1 for r in runs if r.get("final_verdict") == "PASS")
    print(f"\n{'='*70}\n  TARGETED REVALIDATION SUMMARY — {len(runs)} runs\n{'='*70}", flush=True)
    print(f"  PASS: {n_pass}/{len(runs)}", flush=True)
    for r in runs:
        print(f"  {r.get('run_id')} {r.get('ticker')} ({r.get('purpose')}): {r.get('final_verdict')} "
              f"pass={r.get('validator_results',{}).get('pass')} fail={r.get('validator_results',{}).get('fail')} "
              f"| {r.get('requirements_failed')}", flush=True)

    # Criteria
    vnm_complete = [r for r in runs if r.get("purpose") == "complete-pack"]
    vnm_zn = [r for r in runs if r.get("purpose") == "zero-news-control"]
    gas_runs = [r for r in runs if r.get("purpose") == "chart-consistency"]
    controls = [r for r in runs if r.get("purpose") == "clean-control"]
    print(f"\n  CRITERIA:", flush=True)
    print(f"    VNM complete 2/2 PASS: {sum(1 for r in vnm_complete if r.get('final_verdict')=='PASS')}/2", flush=True)
    print(f"    VNM zero-news: {vnm_zn[0].get('final_verdict') if vnm_zn else '?'} (fabricated=0 required)", flush=True)
    print(f"    GAS 2/2 PASS: {sum(1 for r in gas_runs if r.get('final_verdict')=='PASS')}/2", flush=True)
    print(f"    Clean controls (BID+MWG) 2/2: {sum(1 for r in controls if r.get('final_verdict')=='PASS')}/2", flush=True)


if __name__ == "__main__":
    main()
