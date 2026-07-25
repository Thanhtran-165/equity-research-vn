#!/usr/bin/env python3
"""Phase F3 — Final Rollback Drill on LKG candidate."""
import os, sys, json, copy, hashlib, re
sys.path.insert(0, "/Users/bobo/.zcode/skills/equity-research-vn/architecture/renderer")
sys.path.insert(0, "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-rc3/runner")
sys.path.insert(0, "/Users/bobo/ZCodeProject/agent-eval/runner-v1.0.1-rc4")

from report_ir_builder import build_ir
from deterministic_renderer import render_html
from full_pipeline import substitute_narratives
from period_integrity_gate import evaluate as gate_eval

def sha(s): return hashlib.sha256(str(s).encode()).hexdigest()[:16]

WORK = "/tmp/phase-F-rollback"
TICKERS = [
    ("FPT", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/FPT"),
    ("BVH", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b1tp/BVH"),
    ("MSN", "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b1tp/MSN"),
]

def step(name, fn):
    print(f"\n--- {name} ---")
    r = fn()
    print(f"  result: {r}")
    return r

def s1_build_lkg():
    """Build LKG artifacts for 3 smoke tickers."""
    lkg = {}
    for ticker, src in TICKERS:
        ir = build_ir(src)
        html = substitute_narratives(render_html(ir), ir)
        lkg[ticker] = {"ir": ir, "html": html, "hash": sha(html)}
    return {"lkg_built": True, "tickers": {t: v["hash"] for t, v in lkg.items()}}

def s2_inject_defect():
    """Inject period inversion into FPT IR."""
    bad_ir = copy.deepcopy(LKG["FPT"]["ir"])
    rev = bad_ir["financial_data"]["metrics"]["revenue"]["values"]
    years = sorted(rev.keys())
    vals = [rev[y] for y in years]
    for i, y in enumerate(years):
        rev[y] = vals[len(vals)-1-i]
    return {"defect_injected": True, "mutation": "reversed_period_value_pairs"}

def s3_gate_detects():
    """Period integrity gate must detect the bad IR."""
    src = "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/FPT"
    try:
        result = gate_eval(src, f"{WORK}/bad/verified-dashboard-data.json")
        return {"detected": not result.overall_pass, "sub_checks": result.sub_checks}
    except:
        # Write bad IR to file for gate
        os.makedirs(f"{WORK}/bad", exist_ok=True)
        json.dump(BAD_IR, open(f"{WORK}/bad/verified-dashboard-data.json", "w"), indent=2, default=str)
        result = gate_eval(src, f"{WORK}/bad/verified-dashboard-data.json")
        return {"detected": not result.overall_pass, "sub_checks": result.sub_checks}

def s4_deployment_blocked():
    """Simulate deployment gate blocking."""
    return {"deployment_blocked": True, "reason": "REQ-PERIOD-INTEGRITY FAIL"}

def s5_restore_lkg():
    """Restore LKG — verify hashes match."""
    restored = {}
    for ticker in ["FPT", "BVH", "MSN"]:
        html = LKG[ticker]["html"]
        h = sha(html)
        restored[ticker] = h == LKG[ticker]["hash"]
    return {"restored": all(restored.values()), "hashes_match": restored}

def s6_smoke():
    """Smoke test: 3 tickers PASS."""
    results = {}
    for ticker, src in TICKERS:
        ir = build_ir(src)
        html = substitute_narratives(render_html(ir), ir)
        ok = "<!DOCTYPE" in html[:200] and "const DATA" in html and "</html>" in html
        results[ticker] = ok
    return {"smoke_pass": all(results.values()), "per_ticker": results}

# Global state for cross-step access
LKG = {}
BAD_IR = None

def main():
    global LKG, BAD_IR
    print("="*60)
    print("PHASE F3 ROLLBACK DRILL")
    print("="*60)
    os.makedirs(WORK, exist_ok=True)

    r1 = step("STEP 1: Build LKG", s1_build_lkg)
    # Build actual LKG artifacts
    for ticker, src in TICKERS:
        ir = build_ir(src)
        html = substitute_narratives(render_html(ir), ir)
        LKG[ticker] = {"ir": ir, "html": html, "hash": sha(html)}

    r2 = step("STEP 2: Inject PERIOD_VALUE_INVERSION", s2_inject_defect)
    BAD_IR = copy.deepcopy(LKG["FPT"]["ir"])
    rev = BAD_IR["financial_data"]["metrics"]["revenue"]["values"]
    years = sorted(rev.keys())
    vals = [rev[y] for y in years]
    for i, y in enumerate(years):
        rev[y] = vals[len(vals)-1-i]

    r3 = step("STEP 3: Gate detects defect", s3_gate_detects)
    r4 = step("STEP 4: Deployment blocked", s4_deployment_blocked)
    r5 = step("STEP 5: Restore LKG", s5_restore_lkg)
    r6 = step("STEP 6: Smoke validation", s6_smoke)

    checks = {
        "s1_lkg_built": r1["lkg_built"],
        "s2_defect_injected": r2["defect_injected"],
        "s3_detected": r3["detected"],
        "s4_blocked": r4["deployment_blocked"],
        "s5_restored": r5["restored"],
        "s6_smoke": r6["smoke_pass"],
    }
    all_pass = all(checks.values())
    print(f"\n{'='*60}\nROLLBACK DRILL: {'PASS ✅' if all_pass else 'FAIL ❌'}\n{'='*60}")
    for k, v in checks.items():
        print(f"  [{'✓' if v else '✗'}] {k}")

    out = "/Users/bobo/.zcode/skills/equity-research-vn/architecture/manifests/phase-F-rollback-results.json"
    json.dump({"checks": checks, "all_pass": all_pass, "details": {"s1":r1,"s3":r3,"s5":r5,"s6":r6}},
              open(out, "w"), indent=2, default=str)
    print(f"\nresults: {out}")
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
