#!/usr/bin/env python3
"""
agent_runner.py — Instrumented genuine-agent runner for equity-research-vn (agent-eval §IV/V/VI).

BRANCH-A CANDIDATE: wires the Phase-4A Tech Score gate (phase4a_gate.py) into the
pipeline alongside the existing phase6 preflight, and injects the Tech Score into
the Phase-6 prompt so it flows as a machine-readable field.

Changes vs production runner (all additive):
  1. After phase4a_tech_active inference, run phase4a_gate on the phase output.
  2. If FAIL → retry phase4a (1 initial + max 2 recovery = 3 total, same as phase6).
  3. Record phase4a attempts in phase_events (like phase6_preflight).
  4. Inject the tech_score data into the phase6 prompt alongside the existing data
     contract injection: "You MUST include a tech-score-card div with data-metric=
     'tech-score' data-score='X' data-verdict='Y' using the exact values from the
     verified data contract."

Executes one full-pipeline agent run: 8 phases, each phase = a real model-inference call
(subagent-per-phase, per skill design). Records, per phase: phase_event, tool_calls,
duration, retries, model metadata. Runs the skill's per-phase verifier after each phase.
Writes a complete run-result.json matching the spec §V schema.

HONESTY CONTRACT:
  - If no model backend is available (no API key, no local runner), the model layer returns
    execution_type='NO_MODEL_BOUND' and the run is marked INVALID_FOR_AGENT_EVIDENCE.
    It is NEVER reported as a genuine_agent run. (spec §I forbids deterministic-workflow
    substitution; we honor that by refusing to fabricate.)
  - When a backend IS available, each phase calls it with the phase prompt + current
    task-state slice, captures the model's output, writes it to the workspace, and records
    genuine model metadata.

Usage:
  python3 agent_runner.py <run_id> <cohort> <workspace_dir> <source_pack_dir>
                          <ticker> [--perturbation <name>] [--scored <bool>]
                          [--model-backend <openai|zai|none>]
                          [--model-id <id>]
"""
import sys, os, json, time, shutil, hashlib, subprocess, argparse, datetime, platform, yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model_backends as MB

SKILL_DIR = os.path.expanduser("~/.zcode/skills/equity-research-vn")
VERIFIER = os.path.join(SKILL_DIR, "scripts/independent_verifier.py")
INIT_STATE = os.path.join(SKILL_DIR, "scripts/init_task_state.py")
PHASES = [
    ("phase0_sponsor", "phases/phase0-sponsor.md"),
    ("phase1_data", "phases/phase1-data.md"),
    ("phase2_fundamental", "phases/phase2-fundamental.md"),
    ("phase3_valuation", "phases/phase3-valuation.md"),
    ("phase4a_tech_active", "phases/phase4a-tech-active.md"),
    ("phase4b_tech_profile", "phases/phase4b-tech-profile.md"),
    ("phase5_news", "phases/phase5-news.md"),
    ("phase6_dashboard", "phases/phase6-dashboard.md"),
    ("phase7_deploy", "phases/phase7-deploy.md"),
]

def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None

def model_available(backend_name):
    """Delegate to adapter layer. Honest: refuse to claim genuine_agent if no backend."""
    b = MB.get_backend(backend_name)
    return b.is_available(), b.metadata()

def call_model(backend_name, model_id, phase_prompt, task_state_slice, phase_id):
    """Perform ONE genuine model inference via the adapter. Returns NO_MODEL_BOUND if unavailable."""
    b = MB.get_backend(backend_name, model_id)
    res = b.invoke(phase_prompt, task_state_slice)
    return {"output": res["output"], "model_meta": res["metadata"],
            "tool_calls": res.get("tool_calls", []), "error": res["error"],
            "inference_occurred": res["inference_occurred"]}

def load_technical_contract(workspace):
    """BRANCH-A: load the `technical` block from the verified data contract in workspace.
    Returns the block dict (may be None) — passed to phase4a_gate as the source contract."""
    contract_path = os.path.join(workspace, "verified-dashboard-data.json")
    if not os.path.exists(contract_path):
        return None
    try:
        return json.load(open(contract_path)).get("technical")
    except Exception:
        return None

def run_phase_verifier(workspace, ticker):
    """Run the skill's independent_verifier; return parsed per-REQ results.
    IMPORTANT: pass an ABSOLUTE artifact path. The verifier computes evidence_dir as
    os.path.join(os.path.dirname(REPORT), ".task-state", "evidence"); if REPORT is relative
    AND cwd==workspace, dirname(REPORT) gets joined under cwd → a nested doubled path.
    Absolute path keeps evidence_dir inside the workspace as intended."""
    workspace = os.path.abspath(workspace)
    # find the report artifact produced (phase6 writes HTML)
    artifact = None
    for f in os.listdir(workspace):
        if f.endswith("_Complete_Report.html"):
            artifact = os.path.join(workspace, f); break
    proc = subprocess.run([sys.executable, VERIFIER, ticker, artifact or "/dev/null"],
                          capture_output=True, text=True, cwd=workspace, timeout=300)
    ev_dir = os.path.join(workspace, ".task-state", "evidence")
    per_req = {}
    if os.path.isdir(ev_dir):
        for f in os.listdir(ev_dir):
            if f.startswith("REQ-") and f.endswith(".json"):
                try:
                    d = json.load(open(os.path.join(ev_dir, f)))
                    per_req[d.get("requirement_id", f[:-5])] = {"status": d.get("status"), "method": d.get("method")}
                except Exception: pass
    summary = {}
    sp = os.path.join(ev_dir, "_summary.json")
    if os.path.exists(sp): summary = json.load(open(sp))
    return {"exit_code": proc.returncode, "verdict": summary.get("verdict"),
            "recall_pct": summary.get("requirement_recall_pct"),
            "pass": summary.get("results", {}).get("pass"), "fail": summary.get("results", {}).get("fail"),
            "skip": summary.get("results", {}).get("skip"), "per_req": per_req}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id"); ap.add_argument("cohort"); ap.add_argument("workspace")
    ap.add_argument("source_pack"); ap.add_argument("ticker")
    ap.add_argument("--perturbation", default=None)
    ap.add_argument("--scored", default="true")
    ap.add_argument("--model-backend", default="zai", help="zai (GLM-native, default) | openai | ollama | zcode-native")
    ap.add_argument("--model-id", default=None)
    ap.add_argument("--protocol-sha256", default=None)
    args = ap.parse_args()

    os.makedirs(args.workspace, exist_ok=True)
    # fresh workspace: copy source pack, init task state
    for f in os.listdir(args.source_pack):
        src = os.path.join(args.source_pack, f)
        if os.path.isfile(src): shutil.copy2(src, os.path.join(args.workspace, f))
    subprocess.run([sys.executable, INIT_STATE, args.ticker, args.workspace], capture_output=True, text=True)
    # CONTENT PATCH (Step 2): build deterministic data contract from source-pack CSVs.
    # Produces data/{financials,balance_sheet,cash_flow}.json (verifier format) + verified-dashboard-data.json
    # (the contract Phase 6 renders from). This bridges the raw-CSV → verifier-JSON format gap.
    # BRANCH-A: verified-dashboard-data.json now also carries the `technical` block.
    import build_data_contract as BDC
    try:
        BDC.main.__wrapped__ if hasattr(BDC.main,'__wrapped__') else None
        # call with sys.argv override
        sys.argv = ["build_data_contract.py", args.source_pack, args.workspace]
        BDC.main()
    except Exception as e:
        phase_events = phase_events if 'phase_events' in dir() else []
        print(f"⚠️ data-contract build failed: {e}", file=sys.stderr)

    # BRANCH-A: the verified source contract for the phase4a gate (loaded once here so the
    # gate can be evaluated inside the per-phase loop without re-reading JSON each attempt).
    technical_contract = load_technical_contract(args.workspace)

    model_avail, model_detail = model_available(args.model_backend)
    run_start = datetime.datetime.now().isoformat()
    t_run0 = time.time()
    phase_events = []
    tool_calls_total = 0; retries_total = 0

    for phase_id, prompt_path in PHASES:
        t0 = time.time()
        prompt = open(os.path.join(SKILL_DIR, prompt_path)).read()
        prompt = prompt.replace("[TICKER]", args.ticker).replace("[WORK_DIR]", args.workspace)
        # LAYER 1 (PATCH): inline the dashboard template into phase6 prompt so the model can
        # fill tokens and return complete HTML in one response (it has no tool/bash channel).
        # The patched phase6 prompt contains a __TEMPLATE_INLINE_PLACEHOLDER__ marker.
        if phase_id == "phase6_dashboard" and "__TEMPLATE_INLINE_PLACEHOLDER__" in prompt:
            tmpl_path = os.path.join(SKILL_DIR, "vn-research-dashboard", "assets", "dashboard_template.html")
            if os.path.exists(tmpl_path):
                prompt = prompt.replace("__TEMPLATE_INLINE_PLACEHOLDER__", open(tmpl_path).read())
        # CONTENT PATCH (Step 3): inject the verified data contract into phase6 prompt.
        # The model renders from this JSON — it is FORBIDDEN from inventing numbers.
        # Also add an explicit ref-id demand for REQ-018.
        if phase_id == "phase6_dashboard":
            contract_path = os.path.join(args.workspace, "verified-dashboard-data.json")
            if os.path.exists(contract_path):
                contract = open(contract_path).read()
                prompt = prompt + f"\n\n## VERIFIED DATA CONTRACT (render from this ONLY — do NOT invent numbers)\n```json\n{contract}\n```\n"
            # BRANCH-A: inject the Tech Score as a machine-readable field into the phase6 prompt,
            # alongside the existing data contract injection. The model MUST render the exact
            # values from the verified `technical` block into a tech-score-card div.
            tech = technical_contract or {}
            tech_score = tech.get("tech_score")
            tech_verdict = tech.get("verdict")
            if tech_score is not None and tech_verdict is not None:
                prompt = prompt + (
                    "\n## TECH SCORE CARD — MANDATORY (machine-readable)\n"
                    "You MUST include a tech-score-card div with data-metric='tech-score' "
                    f"data-score='{tech_score}' data-verdict='{tech_verdict}' "
                    "using the exact values from the verified data contract. "
                    "Do NOT invent or alter the Tech Score or verdict — they are locked by the contract.")
            else:
                # No verified technical block → tell the model the field is unavailable rather
                # than letting it fabricate one. (NO_SOURCE_DATA propagates from the gate.)
                prompt = prompt + (
                    "\n## TECH SCORE CARD\nThe verified data contract has NO technical block "
                    "(technical_active.json was missing or had no tech_score). Do NOT fabricate "
                    "a Tech Score; omit the tech-score-card if you have no verified value.")
            # explicit reference-id demand for REQ-012/018
            prompt = prompt + ("\n## REFERENCES — MANDATORY\nThe sec-source section MUST contain ≥10 numbered references "
                                "using this exact markup: `<ol><li id=\"ref-1\">source 1</li><li id=\"ref-2\">...</li></ol>`. "
                                "Use the references array from the data contract. "
                                "REQ-018 verifier checks for `id=\"ref-N\"` patterns — plain text 'source' will FAIL.")
        # task-state slice for context isolation
        state_file = os.path.join(args.workspace, ".task-state", "task-state.json")
        state_slice = json.load(open(state_file)) if os.path.exists(state_file) else {}
        # PERTURBATION hooks (cohort B)
        perturbation_applied = None
        if args.perturbation == "source_order_shuffled" and phase_id == "phase1_data":
            perturbation_applied = "source files enumerated in shuffled order"
        # model inference
        model_result = call_model(args.model_backend, args.model_id, prompt, state_slice, phase_id)
        if not model_result["inference_occurred"]:
            # HONEST STOP: no model → cannot continue as genuine agent
            phase_events.append({"phase": phase_id, "duration_s": round(time.time()-t0,2),
                                 "inference_occurred": False, "error": model_result["error"],
                                 "perturbation_applied": perturbation_applied})
            break
        # LAYER 2 (PATCH, FIX #3/#4): phase-local preflight gate for phase6 + bounded retry.
        # Policy (FIX #4): 1 initial + max 2 recovery = 3 total attempts. Per-attempt artifacts preserved.
        # Truncation (FIX #3): OUTPUT_TRUNCATED classified distinctly; max_tokens stop → truncation.
        phase6_attempts = []
        if phase_id == "phase6_dashboard":
            import phase6_preflight as PF
            # attempt 1 = initial inference already done
            stop_reason = (model_result.get("model_meta") or {}).get("stop_reason")
            passed_pf, pf_errors, pf_cls, pf_detail = PF.preflight_phase6(model_result["output"], stop_reason=stop_reason)
            attempt_out = model_result["output"] or ""
            phase6_attempts.append({"attempt_number":1, "artifact_type":pf_cls, "preflight_failures":pf_errors,
                                    "output_sha256":hashlib.sha256(attempt_out.encode()).hexdigest()[:16] if attempt_out else None,
                                    "stop_reason":stop_reason, "duration_s":round(time.time()-t0,2)})
            # preserve attempt-1 artifact separately (never overwritten)
            if attempt_out:
                open(os.path.join(args.workspace, f".phase6-attempt-1.txt"),"w").write(attempt_out)
            recovery = 0
            while not passed_pf and recovery < 2:  # FIX #4: max 2 recovery → 3 total
                recovery += 1; retries_total += 1
                rt0 = time.time()
                feedback = (f"Your previous Phase-6 output was classified {pf_cls} and REJECTED.\n"
                            f"Errors: {'; '.join(pf_errors)}\n"
                            f"You MUST return ONLY complete HTML starting with <!DOCTYPE html> and ending with </html>. "
                            f"No narration, no markdown, no explanation. Fill the template and return it.")
                retry_result = call_model(args.model_backend, args.model_id,
                                          feedback + "\n\nOriginal phase prompt:\n" + prompt, state_slice, phase_id+"_retry")
                if retry_result["inference_occurred"] and retry_result["output"]:
                    r_stop = (retry_result.get("model_meta") or {}).get("stop_reason")
                    passed_pf, pf_errors, pf_cls, pf_detail = PF.preflight_phase6(retry_result["output"], stop_reason=r_stop)
                    r_out = retry_result["output"]
                    open(os.path.join(args.workspace, f".phase6-attempt-{1+recovery}.txt"),"w").write(r_out)
                    phase6_attempts.append({"attempt_number":1+recovery, "artifact_type":pf_cls, "preflight_failures":pf_errors,
                                            "output_sha256":hashlib.sha256(r_out.encode()).hexdigest()[:16],
                                            "stop_reason":r_stop, "duration_s":round(time.time()-rt0,2)})
                    if passed_pf:
                        model_result = retry_result
                        break
                else:
                    phase6_attempts.append({"attempt_number":1+recovery, "artifact_type":"NO_INFERENCE",
                                            "preflight_failures":["retry inference failed"],"stop_reason":None,
                                            "duration_s":round(time.time()-rt0,2)})
                    break
            phase6_final_cls = pf_cls
            phase6_recovered = (passed_pf and recovery>0)
        # === BRANCH-A: phase-local gate for phase4a (Tech Score) + bounded retry ===
        # Policy mirrors phase6: 1 initial + max 2 recovery = 3 total attempts. Per-attempt
        # artifacts preserved. Validated against the verified `technical` source contract.
        phase4a_attempts = []
        if phase_id == "phase4a_tech_active":
            import phase4a_gate as PG
            passed_4a, errs_4a, cls_4a = PG.gate_phase4a(model_result["output"], technical_contract)
            attempt_out = model_result["output"] or ""
            phase4a_attempts.append({"attempt_number":1, "classification":cls_4a, "errors":errs_4a,
                                     "output_sha256":hashlib.sha256(attempt_out.encode()).hexdigest()[:16] if attempt_out else None,
                                     "duration_s":round(time.time()-t0,2)})
            if attempt_out:
                open(os.path.join(args.workspace, ".phase4a-attempt-1.txt"),"w").write(attempt_out)
            recovery_4a = 0
            while not passed_4a and recovery_4a < 2:  # max 2 recovery → 3 total
                recovery_4a += 1; retries_total += 1
                rt0 = time.time()
                tech = technical_contract or {}
                feedback_4a = (f"Your previous Phase-4A Tech Score output was classified {cls_4a} and REJECTED.\n"
                               f"Errors: {'; '.join(errs_4a)}\n"
                               f"The verified source contract requires tech_score={tech.get('tech_score')} "
                               f"and verdict={tech.get('verdict')} (from {tech.get('source_file','technical_active.json')}). "
                               f"You MUST output a machine-readable tech-score-card with "
                               f"data-metric='tech-score' data-score='{tech.get('tech_score')}' "
                               f"data-verdict='{tech.get('verdict')}' using the EXACT verified values. "
                               f"Do not invent a different score.")
                retry_result = call_model(args.model_backend, args.model_id,
                                          feedback_4a + "\n\nOriginal phase prompt:\n" + prompt, state_slice, phase_id+"_retry")
                if retry_result["inference_occurred"] and retry_result["output"]:
                    r_out = retry_result["output"]
                    passed_4a, errs_4a, cls_4a = PG.gate_phase4a(r_out, technical_contract)
                    open(os.path.join(args.workspace, f".phase4a-attempt-{1+recovery_4a}.txt"),"w").write(r_out)
                    phase4a_attempts.append({"attempt_number":1+recovery_4a, "classification":cls_4a, "errors":errs_4a,
                                             "output_sha256":hashlib.sha256(r_out.encode()).hexdigest()[:16],
                                             "duration_s":round(time.time()-rt0,2)})
                    if passed_4a:
                        model_result = retry_result
                        break
                else:
                    phase4a_attempts.append({"attempt_number":1+recovery_4a, "classification":"NO_INFERENCE",
                                             "errors":["retry inference failed"],
                                             "duration_s":round(time.time()-rt0,2)})
                    break
            phase4a_recovered = (passed_4a and recovery_4a>0)
        # write FINAL phase output to workspace (phase6 produces the report); attempts preserved separately
        if phase_id == "phase6_dashboard" and model_result["output"]:
            open(os.path.join(args.workspace, f"{args.ticker}_Complete_Report.html"),"w").write(model_result["output"])
        tool_calls_total += len(model_result.get("tool_calls", []))
        phase_events.append({"phase": phase_id, "duration_s": round(time.time()-t0,2),
                             "inference_occurred": True, "model": model_result["model_meta"],
                             "perturbation_applied": perturbation_applied,
                             "phase4a_gate": ({"passed":passed_4a,"class":cls_4a,"errors":errs_4a,
                                               "attempts":phase4a_attempts, "total_attempts":len(phase4a_attempts),
                                               "recovered":phase4a_recovered if phase_id=="phase4a_tech_active" else None}
                                              if phase_id=="phase4a_tech_active" else None),
                             "phase6_preflight": ({"passed":passed_pf,"class":pf_cls,"errors":pf_errors,
                                                   "attempts":phase6_attempts, "total_attempts":len(phase6_attempts),
                                                   "recovered":phase6_recovered if phase_id=="phase6_dashboard" else None}
                                                  if phase_id=="phase6_dashboard" else None)})
    run_duration = time.time() - t_run0

    # final verifier
    verifier_result = run_phase_verifier(args.workspace, args.ticker)

    # determine execution_type honestly
    any_inference = any(e.get("inference_occurred") for e in phase_events)
    all_inference = len(phase_events) == len(PHASES) and any_inference
    execution_type = "genuine_agent" if all_inference else ("NO_MODEL_BOUND" if not any_inference else "PARTIAL_AGENT")

    run_result = {
        "run_id": args.run_id, "cohort": args.cohort, "scored": args.scored.lower()=="true",
        "execution_type": execution_type,
        "model": {"backend": args.model_backend, "model_id": args.model_id, "available": model_avail, "detail": model_detail},
        "protocol_sha256": args.protocol_sha256,
        "ticker": args.ticker,
        "source_pack_sha256": sha(os.path.join(args.source_pack,"benchmark-manifest.json")),
        "perturbation": args.perturbation,
        "start_time": run_start, "end_time": datetime.datetime.now().isoformat(),
        "duration_seconds": round(run_duration, 2),
        "phase_events": phase_events, "phases_completed": len([e for e in phase_events if e.get("inference_occurred")]),
        "tool_calls_total": tool_calls_total, "retries_total": retries_total,
        "validator_results": verifier_result,
        "requirements_passed": [r for r,v in verifier_result["per_req"].items() if v["status"]=="pass"],
        "requirements_failed": [r for r,v in verifier_result["per_req"].items() if v["status"]=="fail"],
        "requirements_skipped": [r for r,v in verifier_result["per_req"].items() if v["status"]=="skip"],
        "final_verdict": verifier_result["verdict"],
        "completion_claimed": None,  # filled by analysis
        "human_intervention": {"severity":"none","actions":[]},
        "artifacts": [f for f in os.listdir(args.workspace) if f.endswith(".html")],
        "artifact_sha256": sha(next((os.path.join(args.workspace,f) for f in os.listdir(args.workspace) if f.endswith(".html")), "")) or None,
        "environment_fingerprint": {"python": sys.version.split()[0], "platform": platform.platform()},
        "honesty_note": "execution_type=genuine_agent ONLY when all 8 phases had real model inference; NO_MODEL_BOUND runs are NEVER counted as agent evidence.",
    }
    out_path = os.path.join(args.workspace, "run-result.json")
    json.dump(run_result, open(out_path,"w"), indent=2, ensure_ascii=False)
    print(json.dumps({"run_id":args.run_id,"execution_type":execution_type,
                      "phases_completed":run_result["phases_completed"],
                      "final_verdict":verifier_result["verdict"],
                      "verifier_pass":verifier_result["pass"],"verifier_fail":verifier_result["fail"]}, indent=2))
    return 0 if execution_type=="genuine_agent" else 2  # rc 2 = no-model (not a failure, an honest signal)

if __name__ == "__main__":
    sys.exit(main() or 0)
