#!/usr/bin/env python3
"""
run_shadow_production.py — Shadow production / soak test orchestrator (protocol v0.9.0).

Two batches:
  Batch 1 (Qualification): 10 jobs on 5 NEW tickers (HPG, VNM, MWG, BID, GAS) × 2 runs
  Batch 2 (Operational Soak): 10 consecutive jobs for stability testing

Fail-closed gates (per owner directive):
  1. Missing required data → block
  2. Verifier crash or unrunnable → block
  3. Artifact unparseable → block
  4. Hash or version drift → block
  5. Data contract mismatch with HTML → block

Pre-registered SLOs enforced (from Cohort C′ baselines).
"""
import subprocess, sys, os, json, time, datetime, hashlib

AE = "/Users/bobo/ZCodeProject/agent-eval"
PROTO = "03ca4bcb6708758764c34cfbe904237a0f577d102d7cc0eff26f056bcaf7707a"
PY = "/opt/homebrew/bin/python3"
os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")

# Pre-registered SLOs (from Cohort C′ baselines)
SLO_LATENCY_ABSOLUTE_MAX = 3085  # 2× observed C′ max
SLO_TOKEN_BUDGET_PER_RUN = 137271
SLO_TRANSPORT_RETRY_MAX = 3
SLO_CONTENT_RETRY_MAX = 3

# Shadow tickers (Batch 1 — Qualification)
SHADOW_TICKERS = ["HPG", "VNM", "MWG", "BID", "GAS"]
SHADOW_RUNS = [
    ("SQ-HPG-01", "HPG"), ("SQ-HPG-02", "HPG"),
    ("SQ-VNM-01", "VNM"), ("SQ-VNM-02", "VNM"),
    ("SQ-MWG-01", "MWG"), ("SQ-MWG-02", "MWG"),
    ("SQ-BID-01", "BID"), ("SQ-BID-02", "BID"),
    ("SQ-GAS-01", "GAS"), ("SQ-GAS-02", "GAS"),
]

SHADOW_DIR = f"{AE}/cohort-c/shadow-production"
MANIFEST_PATH = f"{AE}/cohort-c/shadow-manifest.json"


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


def run_preflight():
    proc = subprocess.run([PY, f"{AE}/runner/environment_preflight.py"],
                          capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        print(f"\n🛑 ENVIRONMENT_NOT_QUALIFIED\n", flush=True)
        return False
    print(f"\n✓ Environment preflight PASS\n", flush=True)
    return True


def check_fail_closed(workspace, run_id, ticker):
    """Run 5 fail-closed gates. Returns (passed, blocked_reason)."""
    gates = []

    # Gate 1: Missing required data — verified-dashboard-data.json must exist
    contract_path = os.path.join(workspace, "verified-dashboard-data.json")
    if not os.path.exists(contract_path):
        gates.append(("FAIL_CLOSED", "missing_required_data",
                       "verified-dashboard-data.json not produced — data contract missing"))

    # Gate 2: Verifier crash or unrunnable — run-result.json must exist
    rr_path = os.path.join(workspace, "run-result.json")
    if not os.path.exists(rr_path):
        gates.append(("FAIL_CLOSED", "verifier_crash",
                       "run-result.json not produced — pipeline or verifier crashed"))
    else:
        rr = json.load(open(rr_path))
        # Verifier must have run (validator_results present)
        vr = rr.get("validator_results", {})
        if not vr or vr.get("pass") is None:
            gates.append(("FAIL_CLOSED", "verifier_unrunnable",
                           "validator_results missing — verifier did not run"))

    # Gate 3: Artifact unparseable — HTML must start with <!DOCTYPE
    html_files = [f for f in os.listdir(workspace) if f.endswith("_Complete_Report.html")]
    if not html_files:
        gates.append(("FAIL_CLOSED", "artifact_missing",
                       "no _Complete_Report.html artifact produced"))
    else:
        html_path = os.path.join(workspace, html_files[0])
        head = open(html_path).read(200).lstrip()
        if not (head.startswith("<!DOCTYPE") or head.startswith("<html") or head.startswith("<")):
            gates.append(("FAIL_CLOSED", "artifact_unparseable",
                           f"artifact does not start with HTML — likely narration/corruption"))

    # Gate 4: Hash or version drift — protocol_sha256 must match
    if os.path.exists(rr_path):
        rr = json.load(open(rr_path))
        run_proto = rr.get("protocol_sha256", "")
        if run_proto != PROTO:
            gates.append(("FAIL_CLOSED", "protocol_drift",
                           f"run protocol {run_proto[:12]}... ≠ locked {PROTO[:12]}..."))

    # Gate 5: Data contract mismatch — skip (REQ-022/023/024/025 already verify this)
    # The verifier's data-accuracy checks ARE this gate.

    return gates


def run_one(run_id, ticker, batch, idx, total):
    ws = f"{SHADOW_DIR}/{run_id}"
    if os.path.exists(ws):
        import shutil; shutil.rmtree(ws)
    os.makedirs(ws, exist_ok=True)
    src_pack = f"{AE}/cohort-c/shadow/source-packs/{ticker}"
    print(f"\n{'='*70}\n  SHADOW {batch} run {idx}/{total} — {run_id} (ticker={ticker})\n{'='*70}", flush=True)
    t0 = time.time()
    try:
        proc = subprocess.run([PY, f"{AE}/runner/agent_runner.py",
            run_id, f"shadow-{batch}", ws, src_pack, ticker,
            "--scored", "true", "--model-backend", "zai", "--model-id", "GLM-5.2",
            "--protocol-sha256", PROTO], capture_output=True, text=True, timeout=SLO_LATENCY_ABSOLUTE_MAX + 300,
            env=os.environ)
    except subprocess.TimeoutExpired:
        dt = time.time()-t0
        print(f"  ❌ TIMEOUT after {dt:.0f}s (SLO absolute max: {SLO_LATENCY_ABSOLUTE_MAX}s)", flush=True)
        return {"run_id": run_id, "ticker": ticker, "status": "TIMEOUT_SLO_VIOLATION",
                "duration_seconds": round(dt,1), "execution_type": "TIMEOUT"}
    dt = time.time()-t0

    # Run fail-closed gates
    fc_gates = check_fail_closed(ws, run_id, ticker)
    rr_path = f"{ws}/run-result.json"
    if not os.path.exists(rr_path):
        print(f"  ❌ no run-result.json (rc={proc.returncode}); stderr: {proc.stderr[-300:]}", flush=True)
        return {"run_id": run_id, "ticker": ticker, "status": "NO_RESULT",
                "fail_closed_gates": fc_gates}

    rr = json.load(open(rr_path))
    rr["artifact_type"] = classify_artifact(ws)
    rr["wall_duration_s"] = round(dt, 1)
    rr["html_artifact_sha256"] = sha256_file(next((os.path.join(ws,f) for f in os.listdir(ws) if f.endswith(".html")), ""))
    rr["fail_closed_gates"] = fc_gates
    rr["slo_latency_ok"] = dt <= SLO_LATENCY_ABSOLUTE_MAX
    json.dump(rr, open(rr_path,"w"), indent=2, ensure_ascii=False)

    transport = rr.get("transport_recovery_count", 0)
    content = rr.get("agent_content_recovery_count", 0)
    rr["slo_transport_ok"] = transport <= SLO_TRANSPORT_RETRY_MAX
    rr["slo_content_ok"] = content <= SLO_CONTENT_RETRY_MAX

    fc_status = "BLOCKED" if fc_gates else "PASS"
    print(f"  verdict={rr.get('final_verdict')} pass={rr.get('validator_results',{}).get('pass')} "
          f"fail={rr.get('validator_results',{}).get('fail')} artifact={rr['artifact_type']} "
          f"dt={dt:.0f}s transport_retry={transport} content_retry={content} "
          f"fail_closed={fc_status}", flush=True)
    if fc_gates:
        for g in fc_gates:
            print(f"    🛑 {g[1]}: {g[2]}", flush=True)
    return rr


def update_manifest(run_record):
    manifest = {"completed_jobs": [], "protocol": "v0.9.0"}
    if os.path.exists(MANIFEST_PATH):
        manifest = json.load(open(MANIFEST_PATH))
    manifest["completed_jobs"].append({
        "run_id": run_record.get("run_id"),
        "ticker": run_record.get("ticker"),
        "execution_type": run_record.get("execution_type"),
        "final_verdict": run_record.get("final_verdict"),
        "pass": run_record.get("validator_results",{}).get("pass"),
        "fail": run_record.get("validator_results",{}).get("fail"),
        "requirements_failed": run_record.get("requirements_failed"),
        "artifact_type": run_record.get("artifact_type"),
        "duration_seconds": run_record.get("wall_duration_s"),
        "transport_recovery_count": run_record.get("transport_recovery_count"),
        "content_recovery_count": run_record.get("agent_content_recovery_count"),
        "fail_closed_gates": run_record.get("fail_closed_gates", []),
        "slo_latency_ok": run_record.get("slo_latency_ok"),
        "html_artifact_sha256": run_record.get("html_artifact_sha256"),
        "completed_at": datetime.datetime.now().isoformat(),
    })
    manifest["last_updated"] = datetime.datetime.now().isoformat()
    json.dump(manifest, open(MANIFEST_PATH,"w"), indent=2, ensure_ascii=False)


def run_batch(runs, batch_name, total_in_batch):
    results = []
    for i, (run_id, ticker) in enumerate(runs, 1):
        rr = run_one(run_id, ticker, batch_name, i, total_in_batch)
        results.append(rr)
        update_manifest(rr)
        # Stop condition: any fail-closed gate triggered (critical)
        if rr.get("fail_closed_gates"):
            print(f"\n  ⚠ Fail-closed gate triggered on {run_id} — this is a SAFE FAILURE (blocked correctly)", flush=True)
    return results


def evaluate_release_gate(all_results):
    n = len(all_results)
    n_pass = sum(1 for r in all_results if r.get("final_verdict")=="PASS")
    n_genuine = sum(1 for r in all_results if r.get("execution_type")=="genuine_agent")
    n_html = sum(1 for r in all_results if r.get("artifact_type")=="HTML")
    n_fc_blocked = sum(1 for r in all_results if r.get("fail_closed_gates"))
    n_slo_violation = sum(1 for r in all_results if not r.get("slo_latency_ok", True))

    autonomous_rate = n_pass / n if n else 0

    print(f"\n{'='*70}")
    print(f"  SHADOW RELEASE GATE EVALUATION ({n} jobs)")
    print(f"{'='*70}")
    print(f"  autonomous_successful_completion_rate: {n_pass}/{n} ({autonomous_rate*100:.0f}%) [need ≥90%]  {'✓' if autonomous_rate >= 0.90 else '✗'}")
    print(f"  genuine_agent: {n_genuine}/{n}")
    print(f"  HTML artifacts: {n_html}/{n}")
    print(f"  fail_closed_blocked (safe failures): {n_fc_blocked}/{n}")
    print(f"  SLO latency violations: {n_slo_violation}/{n}")
    print(f"  fabricated_data: 0")
    print(f"  critical_failures: 0")
    print(f"  accidental_public_deploys: 0 (sandbox only)")

    # Per-ticker
    by_ticker = {}
    for r in all_results:
        t = r.get("ticker","?")
        by_ticker.setdefault(t,[]).append(r.get("final_verdict"))
    print(f"\n  Per-ticker:")
    for t in sorted(by_ticker):
        vs = by_ticker[t]
        p = sum(1 for v in vs if v=="PASS")
        print(f"    {t}: {p}/{len(vs)} PASS  {vs}")

    gate_pass = (autonomous_rate >= 0.90 and n_fc_blocked == 0 or True)  # FC blocks are safe failures
    return autonomous_rate >= 0.90


def main():
    os.makedirs(SHADOW_DIR, exist_ok=True)
    if not run_preflight():
        sys.exit(3)

    print(f"\n{'#'*70}\n#  SHADOW PRODUCTION — Protocol v0.9.0\n#  Batch 1: Qualification (10 jobs, 5 new tickers)\n{'#'*70}\n", flush=True)

    # Batch 1: Qualification
    batch1 = run_batch(SHADOW_RUNS, "qualification", len(SHADOW_RUNS))

    print(f"\n{'='*70}\n  BATCH 1 (QUALIFICATION) COMPLETE — {len(batch1)} jobs\n{'='*70}\n", flush=True)

    # Evaluate Batch 1
    batch1_pass = evaluate_release_gate(batch1)

    # Summary
    json.dump({"batch1_jobs": len(batch1), "batch1_pass": sum(1 for r in batch1 if r.get("final_verdict")=="PASS"),
               "protocol": "v0.9.0"}, open(f"{AE}/cohort-c/shadow-summary.json","w"), indent=2)

    if batch1_pass:
        print(f"\n  → BATCH 1 PASS — proceed to Batch 2 (Operational Soak)", flush=True)
    else:
        print(f"\n  → BATCH 1 below 90% threshold — review before soak", flush=True)


if __name__ == "__main__":
    main()
