#!/usr/bin/env python3
"""Phase F2 — Operational Soak (20 consecutive jobs)."""
import os, sys, json, time, hashlib, datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")
sys.path.insert(0, "/Users/bobo/.zcode/skills/equity-research-vn/architecture/renderer")
sys.path.insert(0, "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-rc3/runner")
sys.path.insert(0, "/Users/bobo/ZCodeProject/agent-eval/runner-v1.0.1-rc4")

from report_ir_builder import build_ir
from deterministic_renderer import render_html
from section_generator import SECTION_PROMPTS, generate_section
from full_pipeline import substitute_narratives
from phase_E_cohort import call_model_genuine

COHORT_DIR = "/Users/bobo/ZCodeProject/agent-eval/cohort-c/phase-F-soak"
MAX_WORKERS = 4

# 20 jobs: 10 tickers × 2, include NOT_APPLICABLE (BVH), negative values (POW), sector-specific
SOAK_TICKERS = [
    ("FPT", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/FPT"),
    ("BVH", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b1tp/BVH"),
    ("MSN", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b1tp/MSN"),
    ("POW", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b2/POW"),
    ("HPG", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs/HPG"),
    ("MWG", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs/MWG"),
    ("VCB", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/VCB"),
    ("KDH", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/KDH"),
    ("GAS", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs/GAS"),
    ("CTD", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/CTD"),
]

def sha(s): return hashlib.sha256(str(s).encode()).hexdigest()[:16]

def run_one(run_id, ticker, src_pack):
    os.makedirs(f"{COHORT_DIR}/{run_id}", exist_ok=True)
    t0 = time.time()
    ir = build_ir(src_pack)
    if "error" in ir:
        return {"run_id": run_id, "ticker": ticker, "final_status": "FAIL", "error": ir["error"], "duration_s": round(time.time()-t0,1)}
    data_hash = sha(json.dumps(ir["financial_data"], sort_keys=True, default=str))
    applicable = [s["section_id"] for s in ir["sections"] if s["applicability"] == "APPLICABLE" and s["section_id"] in SECTION_PROMPTS]
    n_pass = n_fail = 0
    for sec_id in applicable:
        r = generate_section(sec_id, ir, call_model_fn=call_model_genuine)
        for s in ir["sections"]:
            if s["section_id"] == sec_id: s["narrative"] = r.get("narrative_safe",""); s["validation_status"] = r["status"]; break
        if r["status"] == "PASS": n_pass += 1
        else: n_fail += 1
    data_hash_after = sha(json.dumps(ir["financial_data"], sort_keys=True, default=str))
    html = substitute_narratives(render_html(ir), ir)
    open(f"{COHORT_DIR}/{run_id}/{ticker}_Complete_Report.html", "w").write(html)
    status = "FAIL" if n_fail > 0 or data_hash != data_hash_after else "PASS"
    return {"run_id": run_id, "ticker": ticker, "final_status": status,
            "sections": len(applicable), "pass": n_pass, "fail": n_fail,
            "data_changed": data_hash != data_hash_after, "duration_s": round(time.time()-t0,1)}

def main():
    print(f"=== Phase F2: Operational Soak (20 jobs) ===\n")
    os.makedirs(COHORT_DIR, exist_ok=True)
    jobs = [(f"SO-{t}-01", t, s) for t, s in SOAK_TICKERS] + [(f"SO-{t}-02", t, s) for t, s in SOAK_TICKERS]
    results = []; completed = 0; t_start = time.time()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(run_one, j[0], j[1], j[2]): j[0] for j in jobs}
        for future in as_completed(futures):
            r = future.result(); results.append(r); completed += 1
            print(f"  [{completed}/20] {r['run_id']}: {r['final_status']} dt={r.get('duration_s','?')}s", flush=True)
            json.dump({"completed": completed, "results": sorted(results, key=lambda x: x["run_id"])},
                      open(f"{COHORT_DIR}/manifest.json", "w"), indent=2, default=str)
    results.sort(key=lambda x: x["run_id"])
    n_pass = sum(1 for r in results if r["final_status"] == "PASS")
    n_data = sum(1 for r in results if r.get("data_changed"))
    wall = time.time() - t_start
    print(f"\n{'='*60}\nSOAK SUMMARY: PASS={n_pass}/20, DATA_changed={n_data}, Wall={wall/60:.1f}min\nGate: {'PASS ✅' if n_pass>=19 and n_data==0 else 'FAIL ❌'}\n{'='*60}")
    json.dump({"n_pass": n_pass, "data_changed": n_data, "wall_clock": round(wall,1),
               "gate_pass": n_pass>=19 and n_data==0, "results": results},
              open(f"{COHORT_DIR}/summary.json", "w"), indent=2, default=str)

if __name__ == "__main__":
    main()
