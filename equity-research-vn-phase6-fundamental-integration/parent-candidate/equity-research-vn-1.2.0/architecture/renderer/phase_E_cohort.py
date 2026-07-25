#!/usr/bin/env python3
"""
Phase E — Genuine Section-Generation Cohort.

Pipeline per run:
  source pack → data contract → report IR → section-level model calls →
  sanitize → validate → deterministic render → final HTML

12 runs: 6 tickers × 2 runs each. 4-way parallel.
Model ONLY writes narrative text per section. Everything else is deterministic.
"""
import os, sys, json, time, subprocess, hashlib, datetime, re
from concurrent.futures import ThreadPoolExecutor, as_completed

PYTHON = "/opt/homebrew/bin/python3"
ARCH = "/Users/bobo/.zcode/skills/equity-research-vn/architecture"
RUNNER_MIRROR = "/Users/bobo/ZCodeProject/agent-eval/runner-v1.0.1-rc4"
SKILL_SCRIPTS = "/Users/bobo/.zcode/skills/equity-research-vn/scripts"
COHORT_DIR = "/Users/bobo/ZCodeProject/agent-eval/cohort-c/phase-E-section-generation"
PROTO = "ERVN-PERIOD-001-phase-E-section-generation"

os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")
sys.path.insert(0, f"{ARCH}/renderer")
sys.path.insert(0, "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-rc3/runner")
sys.path.insert(0, RUNNER_MIRROR)

from report_ir_builder import build_ir
from deterministic_renderer import render_html
from section_generator import SECTION_PROMPTS, build_section_prompt, generate_section
from narrative_sanitizer import sanitize, validate_narrative
from full_pipeline import substitute_narratives

TICKERS = [
    ("FPT", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/FPT"),
    ("BVH", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b1tp/BVH"),
    ("MSN", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b1tp/MSN"),
    ("POW", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b2/POW"),
    ("HPG", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs/HPG"),
    ("MWG", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs/MWG"),
]
MAX_WORKERS = 4


def call_model_genuine(prompt, phase_id):
    """Call GLM model via model_backends.py using invoke()."""
    sys.path.insert(0, RUNNER_MIRROR)
    try:
        import model_backends as MB
        b = MB.get_backend("zai", "GLM-5.2")
        res = b.invoke(prompt, {})
        return {"output": res["output"], "inference_occurred": res["inference_occurred"],
                "error": res.get("error","")}
    except Exception as e:
        return {"output": "", "inference_occurred": False, "error": str(e)[:200]}


def sha(s): return hashlib.sha256(str(s).encode()).hexdigest()[:16]


def run_one(run_id, ticker, src_pack):
    """Execute one genuine section-generation run."""
    ws = f"{COHORT_DIR}/{run_id}"
    if os.path.exists(ws):
        import shutil; shutil.rmtree(ws)
    os.makedirs(ws, exist_ok=True)
    t0 = time.time()

    evidence = {
        "logical_run_id": run_id, "ticker": ticker,
        "section_results": [], "model_calls": 0,
        "sections_first_attempt_pass": 0, "sections_retried": 0,
        "sections_failed": 0, "failed_sections": [],
    }

    # Step 1: Build IR
    ir = build_ir(src_pack)
    if "error" in ir:
        evidence["final_status"] = "FAIL"
        evidence["error"] = ir["error"]
        evidence["duration_s"] = round(time.time()-t0, 1)
        return evidence

    data_hash_before = sha(json.dumps(ir["financial_data"], sort_keys=True, default=str))
    evidence["report_IR_hash"] = sha(json.dumps(ir, sort_keys=True, default=str))
    evidence["data_contract_hash"] = data_hash_before

    # Step 2: Generate sections via genuine model
    applicable = [s["section_id"] for s in ir["sections"]
                  if s["applicability"] == "APPLICABLE" and s["section_id"] in SECTION_PROMPTS]

    for sec_id in applicable:
        evidence["model_calls"] += 1
        result = generate_section(sec_id, ir, call_model_fn=call_model_genuine)
        evidence["section_results"].append({
            "section_id": sec_id,
            "status": result["status"],
            "attempts": result.get("attempts", 0),
            "char_count": result.get("char_count", 0),
            "warnings": result.get("warnings", []),
        })
        # Insert into IR
        for s in ir["sections"]:
            if s["section_id"] == sec_id:
                s["narrative"] = result.get("narrative_safe", "")
                s["validation_status"] = result["status"]
                break

        if result["status"] == "PASS":
            if result.get("attempts", 0) == 1:
                evidence["sections_first_attempt_pass"] += 1
            else:
                evidence["sections_retried"] += 1
        elif result["status"] in ("FAIL", "RETRY_EXHAUSTED"):
            evidence["sections_failed"] += 1
            evidence["failed_sections"].append(sec_id)

    # Step 3: Verify DATA hash unchanged
    data_hash_after = sha(json.dumps(ir["financial_data"], sort_keys=True, default=str))
    evidence["data_hash_changed"] = data_hash_before != data_hash_after

    # Step 4: Render deterministic HTML
    html = render_html(ir)
    html = substitute_narratives(html, ir)
    evidence["html_size"] = len(html)
    evidence["html_hash"] = sha(html)

    # Write artifact
    open(f"{ws}/{ticker}_Complete_Report.html", "w").write(html)
    # Write IR
    json.dump(ir, open(f"{ws}/report_ir.json", "w"), indent=2, ensure_ascii=False, default=str)
    # Write evidence
    evidence["final_HTML_hash"] = sha(html)
    evidence["duration_s"] = round(time.time()-t0, 1)

    # Determine pass/fail
    required_failed = [s for s in evidence["failed_sections"]
                       if s in ["executive_summary", "company_profile", "thesis", "valuation",
                                "balance_sheet", "risk", "insight_1", "insight_2", "insight_3"]]
    evidence["final_status"] = "FAIL" if (evidence["sections_failed"] > 0 or evidence["data_hash_changed"]) else "PASS"
    evidence["required_sections_failed"] = required_failed

    return evidence


def main():
    print(f"=== Phase E: Genuine Section-Generation Cohort ===")
    print(f"tickers: {len(TICKERS)} × 2 = 12 runs")
    print(f"concurrency: {MAX_WORKERS}")
    print(f"model: GLM-5.2 (section-level narrative only)")
    print()

    os.makedirs(COHORT_DIR, exist_ok=True)

    runs = []
    for ticker, src in TICKERS:
        runs.append((f"PH-{ticker}-01", ticker, src))
        runs.append((f"PH-{ticker}-02", ticker, src))

    results = []
    completed = 0
    t_start = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(run_one, rid, tic, src): rid for rid, tic, src in runs}
        for future in as_completed(futures):
            rid = futures[future]
            try:
                ev = future.result()
            except Exception as e:
                ev = {"logical_run_id": rid, "final_status": "EXCEPTION", "error": str(e)[:200]}
            results.append(ev)
            completed += 1
            elapsed = time.time() - t_start
            n_pass = sum(1 for r in results if r.get("final_status") == "PASS")
            print(f"  [{completed}/12] {rid}: {ev.get('final_status')} "
                  f"sections={ev.get('model_calls','?')} pass={ev.get('sections_first_attempt_pass',0)} "
                  f"fail={ev.get('sections_failed',0)} dt={ev.get('duration_s','?')}s "
                  f"elapsed={elapsed:.0f}s", flush=True)

            # Save manifest
            results.sort(key=lambda r: r.get("logical_run_id", ""))
            json.dump({"date": datetime.datetime.now().isoformat(),
                       "phase": "E", "total_runs": 12, "completed": completed,
                       "results": results},
                      open(f"{COHORT_DIR}/manifest.json", "w"), indent=2, default=str)

    total_wall = time.time() - t_start
    results.sort(key=lambda r: r.get("logical_run_id", ""))

    # Summary
    print(f"\n{'='*70}")
    print("PHASE E GENUINE COHORT SUMMARY")
    print(f"{'='*70}")
    n_pass = sum(1 for r in results if r.get("final_status") == "PASS")
    n_fail = sum(1 for r in results if "FAIL" in str(r.get("final_status", "")))
    total_sections = sum(r.get("model_calls", 0) for r in results)
    total_first_pass = sum(r.get("sections_first_attempt_pass", 0) for r in results)
    total_retry = sum(r.get("sections_retried", 0) for r in results)
    total_section_fail = sum(r.get("sections_failed", 0) for r in results)
    total_data_changed = sum(1 for r in results if r.get("data_hash_changed"))

    for r in results:
        mark = "✓" if r.get("final_status") == "PASS" else "✗"
        print(f"  [{mark}] {r.get('logical_run_id','?'):14s} {str(r.get('final_status')):6s} "
              f"sections={r.get('model_calls','?')} 1st_pass={r.get('sections_first_attempt_pass',0)} "
              f"retry={r.get('sections_retried',0)} fail={r.get('sections_failed',0)} "
              f"dt={r.get('duration_s','?')}s")

    print(f"\ntotal runs: {len(results)}")
    print(f"PASS: {n_pass}, FAIL: {n_fail}")
    print(f"total sections: {total_sections}")
    print(f"first attempt pass: {total_first_pass} ({total_first_pass/max(total_sections,1)*100:.1f}%)")
    print(f"retried: {total_retry}")
    print(f"section failures: {total_section_fail}")
    print(f"DATA changed: {total_data_changed}")
    print(f"wall clock: {total_wall:.0f}s ({total_wall/60:.1f} min)")
    print()
    print("GATE:")
    print(f"  completed 12/12: {len(results) == 12}")
    print(f"  final PASS 12/12: {n_pass == 12}")
    print(f"  DATA modified: {total_data_changed}")

    summary = {
        "date": datetime.datetime.now().isoformat(), "phase": "E",
        "total_runs": len(results), "n_pass": n_pass, "n_fail": n_fail,
        "total_sections": total_sections, "first_attempt_pass": total_first_pass,
        "sections_retried": total_retry, "section_failures": total_section_fail,
        "data_changed": total_data_changed, "wall_clock": round(total_wall, 1),
        "gate_pass_12": n_pass == 12,
        "gate_data_unchanged": total_data_changed == 0,
        "results": results,
    }
    json.dump(summary, open(f"{COHORT_DIR}/summary.json", "w"), indent=2, default=str)
    print(f"\nsummary: {COHORT_DIR}/summary.json")


if __name__ == "__main__":
    main()
