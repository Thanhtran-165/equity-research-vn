#!/usr/bin/env python3
"""
Phase F1 — Shadow Requalification (20 runs, 10 tickers, 7 fresh).
Uses same deterministic shell + section-generation pipeline as Phase E.
"""
import os, sys, json, time, hashlib, datetime, re
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")
sys.path.insert(0, "/Users/bobo/.zcode/skills/equity-research-vn/architecture/renderer")
sys.path.insert(0, "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-rc3/runner")
sys.path.insert(0, "/Users/bobo/ZCodeProject/agent-eval/runner-v1.0.1-rc4")

from report_ir_builder import build_ir
from deterministic_renderer import render_html
from section_generator import SECTION_PROMPTS, generate_section
from narrative_sanitizer import sanitize, validate_narrative
from full_pipeline import substitute_narratives
from phase_E_cohort import call_model_genuine

COHORT_DIR = "/Users/bobo/ZCodeProject/agent-eval/cohort-c/phase-F-shadow"
MAX_WORKERS = 4

# 3 controls + 7 fresh = 10 tickers, 10 sectors
SHADOW_TICKERS = [
    # Controls (Phase E regression)
    ("BVH", "Insurance",              "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b1tp/BVH"),
    ("MSN", "Diversified",            "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b1tp/MSN"),
    ("HPG", "Steel",                  "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs/HPG"),
    # Fresh tickers
    ("VCB", "Banking",                "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/VCB"),
    ("KDH", "Real Estate",            "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/KDH"),
    ("PNJ", "Consumer Goods",         "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/PNJ"),
    ("GAS", "Energy",                 "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs/GAS"),
    ("CTD", "Construction",           "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/CTD"),
    ("SAB", "Beverage",               "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-fresh/SAB"),
    ("GEX", "Industrial",             "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-fresh/GEX"),
]

def sha(s): return hashlib.sha256(str(s).encode()).hexdigest()[:16]

def run_one(run_id, ticker, sector, src_pack):
    ws = f"{COHORT_DIR}/{run_id}"
    if os.path.exists(ws):
        import shutil; shutil.rmtree(ws)
    os.makedirs(ws, exist_ok=True)
    t0 = time.time()
    evidence = {"logical_run_id": run_id, "ticker": ticker, "sector": sector,
                "section_results": [], "model_calls": 0,
                "sections_first_attempt_pass": 0, "sections_retried": 0,
                "sections_failed": 0, "failed_sections": []}

    ir = build_ir(src_pack)
    if "error" in ir:
        evidence["final_status"] = "FAIL"; evidence["error"] = ir["error"]
        evidence["duration_s"] = round(time.time()-t0, 1); return evidence

    data_hash = sha(json.dumps(ir["financial_data"], sort_keys=True, default=str))
    evidence["report_IR_hash"] = sha(json.dumps(ir, sort_keys=True, default=str))

    applicable = [s["section_id"] for s in ir["sections"]
                  if s["applicability"] == "APPLICABLE" and s["section_id"] in SECTION_PROMPTS]

    for sec_id in applicable:
        evidence["model_calls"] += 1
        result = generate_section(sec_id, ir, call_model_fn=call_model_genuine)
        evidence["section_results"].append({"section_id": sec_id, "status": result["status"],
                                            "attempts": result.get("attempts", 0),
                                            "char_count": result.get("char_count", 0)})
        for s in ir["sections"]:
            if s["section_id"] == sec_id:
                s["narrative"] = result.get("narrative_safe", ""); s["validation_status"] = result["status"]; break
        if result["status"] == "PASS":
            if result.get("attempts",0) == 1: evidence["sections_first_attempt_pass"] += 1
            else: evidence["sections_retried"] += 1
        else: evidence["sections_failed"] += 1; evidence["failed_sections"].append(sec_id)

    data_hash_after = sha(json.dumps(ir["financial_data"], sort_keys=True, default=str))
    evidence["data_hash_changed"] = data_hash != data_hash_after

    html = render_html(ir); html = substitute_narratives(html, ir)
    evidence["html_size"] = len(html); evidence["html_hash"] = sha(html)
    open(f"{ws}/{ticker}_Complete_Report.html", "w").write(html)
    json.dump(ir, open(f"{ws}/report_ir.json", "w"), indent=2, ensure_ascii=False, default=str)
    evidence["final_status"] = "FAIL" if (evidence["sections_failed"] > 0 or evidence["data_hash_changed"]) else "PASS"
    evidence["duration_s"] = round(time.time()-t0, 1)
    return evidence

def main():
    print(f"=== Phase F1: Shadow Requalification ===")
    print(f"tickers: {len(SHADOW_TICKERS)} × 2 = 20 runs ({sum(1 for _,_,_ in SHADOW_TICKERS[:3])} controls + 7 fresh)")
    print(f"concurrency: {MAX_WORKERS}\n")
    os.makedirs(COHORT_DIR, exist_ok=True)

    runs = []
    for ticker, sector, src in SHADOW_TICKERS:
        runs.append((f"SH-{ticker}-01", ticker, sector, src))
        runs.append((f"SH-{ticker}-02", ticker, sector, src))

    results = []; completed = 0; t_start = time.time()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(run_one, rid, tic, sec, src): rid for rid, tic, sec, src in runs}
        for future in as_completed(futures):
            rid = futures[future]
            try: ev = future.result()
            except Exception as e: ev = {"logical_run_id": rid, "final_status": "EXCEPTION", "error": str(e)[:200]}
            results.append(ev); completed += 1
            elapsed = time.time() - t_start
            print(f"  [{completed}/20] {rid}: {ev.get('final_status')} sections={ev.get('model_calls','?')} "
                  f"1st={ev.get('sections_first_attempt_pass',0)} fail={ev.get('sections_failed',0)} "
                  f"dt={ev.get('duration_s','?')}s elapsed={elapsed:.0f}s", flush=True)
            results.sort(key=lambda r: r.get("logical_run_id",""))
            json.dump({"completed": completed, "total_runs": 20, "results": results},
                      open(f"{COHORT_DIR}/manifest.json", "w"), indent=2, default=str)

    total_wall = time.time() - t_start; results.sort(key=lambda r: r.get("logical_run_id",""))
    n_pass = sum(1 for r in results if r.get("final_status") == "PASS")
    n_fail = sum(1 for r in results if "FAIL" in str(r.get("final_status","")))
    total_sections = sum(r.get("model_calls",0) for r in results)
    total_1st = sum(r.get("sections_first_attempt_pass",0) for r in results)
    total_retry = sum(r.get("sections_retried",0) for r in results)
    total_fail = sum(r.get("sections_failed",0) for r in results)
    total_data_changed = sum(1 for r in results if r.get("data_hash_changed"))

    # Per-ticker check: no ticker 0/2
    by_ticker = {}
    for r in results:
        by_ticker.setdefault(r["ticker"], []).append(r.get("final_status"))
    n_ticker_0 = sum(1 for t, ss in by_ticker.items() if all(s != "PASS" for s in ss))

    print(f"\n{'='*70}\nPHASE F1 SHADOW SUMMARY\n{'='*70}")
    for r in results:
        mark = "✓" if r.get("final_status") == "PASS" else "✗"
        print(f"  [{mark}] {r['logical_run_id']:14s} {r.get('final_status','?'):6s} "
              f"sections={r.get('model_calls','?')} 1st={r.get('sections_first_attempt_pass',0)} "
              f"retry={r.get('sections_retried',0)} fail={r.get('sections_failed',0)} dt={r.get('duration_s','?')}s")
    print(f"\nPASS: {n_pass}/20, FAIL: {n_fail}")
    print(f"Sections: {total_sections}, 1st pass: {total_1st} ({total_1st/max(total_sections,1)*100:.1f}%)")
    print(f"Retried: {total_retry}, Failed: {total_fail}")
    print(f"DATA changed: {total_data_changed}, Ticker 0/2: {n_ticker_0}")
    print(f"Wall: {total_wall:.0f}s ({total_wall/60:.1f} min)")
    print(f"\nGATE: completed={len(results)==20}, PASS≥19={n_pass>=19}, DATA=0={total_data_changed==0}, 0/2=0={n_ticker_0==0}")

    json.dump({"n_pass":n_pass,"n_fail":n_fail,"total_sections":total_sections,
               "first_attempt_pass":total_1st,"retried":total_retry,"section_failures":total_fail,
               "data_changed":total_data_changed,"ticker_zero":n_ticker_0,"wall_clock":round(total_wall,1),
               "gate_pass":n_pass>=19 and total_data_changed==0 and n_ticker_0==0,
               "results":results},
              open(f"{COHORT_DIR}/summary.json","w"), indent=2, default=str)
    print(f"\nsummary: {COHORT_DIR}/summary.json")

if __name__ == "__main__":
    main()
