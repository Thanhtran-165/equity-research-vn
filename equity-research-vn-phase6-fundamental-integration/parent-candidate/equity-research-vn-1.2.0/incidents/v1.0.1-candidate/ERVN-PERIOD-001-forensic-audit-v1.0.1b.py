#!/usr/bin/env python3
"""
ERVN-PERIOD-001 — Forensic audit v2 (correct methodology).

v1 of this audit had a bug: it assumed CSV row 0 = year 2021 (the v1.0.0 bug).
The correct methodology is to use period_key_resolver to determine the actual
period→row mapping, then compare (period, value) pairs against the contract.

This v2 audit uses period_integrity_gate.evaluate() which already does this
correctly. Output: per-ticker PASS/FAIL across 6 sub-checks + 6 fields.
"""
import os, sys, json, subprocess

PYTHON = sys.executable
V101_BUILDER = "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-candidate/runner/build_data_contract.py"
GATE = "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-candidate/runner/period_integrity_gate.py"
sys.path.insert(0, os.path.dirname(GATE))
from period_integrity_gate import evaluate as gate_evaluate, render_report as gate_render

OUT_DIR = "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-candidate/forensic-audit-v1.0.1b-runs"
RESULTS = "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-candidate/ERVN-PERIOD-001-forensic-v1.0.1b.jsonl"
SUMMARY = "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-candidate/ERVN-PERIOD-001-forensic-v1.0.1b-summary.json"

PACKS = [
    ("FPT", "Technology",            "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/FPT"),
    ("KDH", "Real Estate",           "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/KDH"),
    ("PNJ", "Personal Goods",        "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/PNJ"),
    ("VCB", "Banking",               "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/VCB"),
    ("CTD", "Construction",          "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/CTD"),
    ("ACB", "Banking",               "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-fresh/ACB"),
    ("GEX", "Industrial",            "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-fresh/GEX"),
    ("PLX", "Energy",                "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-fresh/PLX"),
    ("SAB", "Beverage",              "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-fresh/SAB"),
    ("SSI", "Financial Services",    "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-fresh/SSI"),
    ("BID", "Banking",               "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs/BID"),
    ("GAS", "Energy",                "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs/GAS"),
    ("HPG", "Steel",                 "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs/HPG"),
    ("MWG", "Retail",                "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs/MWG"),
    ("VNM", "Food & Bev",            "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs/VNM"),
    ("BVH", "Insurance",             "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b1tp/BVH"),
    ("DGW", "Technology",            "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b1tp/DGW"),
    ("HDB", "Banking",               "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b1tp/HDB"),
    ("HDG", "Real Estate",           "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b1tp/HDG"),
    ("MSN", "Diversified",           "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b1tp/MSN"),
    ("DCM", "Chemicals",             "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b2/DCM"),
    ("DHG", "Pharma",                "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b2/DHG"),
    ("POW", "Utilities",             "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b2/POW"),
    ("VJC", "Airlines",              "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b2/VJC"),
    ("DXG", "Real Estate",           "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-soak/DXG"),
    ("GVR", "Agriculture",           "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-soak/GVR"),
    ("NAB", "Banking",               "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-soak/NAB"),
    ("REE", "Utilities",             "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-soak/REE"),
    ("TCB", "Banking",               "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-soak/TCB"),
    ("FRT", "Retail",                "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-req/FRT"),
    ("MBB", "Banking",               "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-req/MBB"),
    ("NLG", "Real Estate",           "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-req/NLG"),
    ("PVD", "Oil & Gas",             "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-req/PVD"),
    ("VHC", "Seafood",               "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-req/VHC"),
]

os.makedirs(OUT_DIR, exist_ok=True)
open(RESULTS, "w").close()


def run_one(t, sector, src):
    run_dir = os.path.join(OUT_DIR, t)
    if os.path.isdir(run_dir):
        import shutil; shutil.rmtree(run_dir)
    os.makedirs(run_dir, exist_ok=True)
    # Step 1: build with v1.0.1
    p = subprocess.run([PYTHON, V101_BUILDER, src, run_dir],
                       capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        return {"ticker": t, "sector": sector, "build_status": "FAIL_CLOSED",
                "stderr": p.stderr[:300]}

    # Step 2: run period_integrity_gate on the produced contract
    contract_path = os.path.join(run_dir, "verified-dashboard-data.json")
    if not os.path.exists(contract_path):
        return {"ticker": t, "sector": sector, "build_status": "NO_CONTRACT"}
    try:
        result = gate_evaluate(src, contract_path)
    except Exception as e:
        return {"ticker": t, "sector": sector, "build_status": "BUILT",
                "gate_status": "GATE_EXCEPTION", "error": str(e)[:200]}

    # Aggregate per-field match counts
    per_field_summary = {}
    total_pairs = 0
    matched_pairs = 0
    for fname, info in result.per_field_results.items():
        if "skipped" in info:
            per_field_summary[fname] = {"skipped": info["skipped"]}
            continue
        per_y = info.get("per_year", {})
        n_match = sum(1 for yr in per_y.values() if yr.get("match") is True)
        n_total = sum(1 for yr in per_y.values() if "match" in yr)
        per_field_summary[fname] = {"match": n_match, "total": n_total}
        total_pairs += n_total
        matched_pairs += n_match

    return {
        "ticker": t, "sector": sector,
        "build_status": "BUILT",
        "gate_overall_pass": result.overall_pass,
        "detection_method": result.detection_method,
        "confidence": result.confidence,
        "sub_checks": result.sub_checks,
        "per_field": per_field_summary,
        "total_pairs_checked": total_pairs,
        "matched_pairs": matched_pairs,
        "inverted_or_mismatched_pairs": total_pairs - matched_pairs,
        "failures": result.failures[:5],
    }


def main():
    print(f"=== ERVN-PERIOD-001 v1.0.1 Forensic Re-audit (methodology v2 — uses gate) ===")
    print(f"tickers: {len(PACKS)}")
    print()

    n_built = n_fail_closed = n_pass = n_field_mismatch = 0
    total_pairs = matched_pairs = 0
    per_sector = {}
    per_ticker = []

    for t, sector, src in PACKS:
        rec = run_one(t, sector, src)
        with open(RESULTS, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        if rec.get("build_status") == "FAIL_CLOSED":
            n_fail_closed += 1
            print(f"  [FAIL_CLOSED] {t:5s} ({sector:20s}): builder refused (no metadata)")
            per_ticker.append({"ticker": t, "sector": sector, "status": "FAIL_CLOSED"})
            continue
        if rec.get("build_status") != "BUILT":
            n_fail_closed += 1
            print(f"  [BUILD_FAIL]  {t:5s} ({sector:20s}): {rec.get('build_status')}")
            per_ticker.append({"ticker": t, "sector": sector, "status": rec.get("build_status")})
            continue
        n_built += 1
        total_pairs += rec["total_pairs_checked"]
        matched_pairs += rec["matched_pairs"]
        sect_stats = per_sector.setdefault(sector, {"built": 0, "pass": 0, "pairs_total": 0, "pairs_match": 0})
        sect_stats["built"] += 1
        sect_stats["pairs_total"] += rec["total_pairs_checked"]
        sect_stats["pairs_match"] += rec["matched_pairs"]
        if rec["gate_overall_pass"]:
            n_pass += 1
            sect_stats["pass"] += 1
            flag = "✓ PASS"
        else:
            n_field_mismatch += 1
            flag = "✗ FIELD_MISMATCH"
        tp = rec["total_pairs_checked"]
        mp = rec["matched_pairs"]
        print(f"  [{flag:16s}] {t:5s} ({sector:20s}): {mp}/{tp} pairs match, "
              f"method={rec['detection_method'][:30]}")

    print()
    print("=" * 90)
    print(f"V1.0.1 FORENSIC RE-AUDIT (v2) SUMMARY")
    print("=" * 90)
    print(f"tickers total:                  {len(PACKS)}")
    print(f"tickers BUILT by v1.0.1:        {n_built}")
    print(f"tickers FAIL_CLOSED:            {n_fail_closed}  (no fundamental_sponsor.json)")
    print(f"tickers GATE PASS:              {n_pass}")
    print(f"tickers FIELD_MISMATCH:         {n_field_mismatch}")
    print()
    print(f"Total (period,value) pairs checked: {total_pairs}")
    print(f"  correctly matched:                {matched_pairs} ({matched_pairs/total_pairs*100:.1f}%)" if total_pairs else "n/a")
    mismatched = total_pairs - matched_pairs
    print(f"  INVERTED or mismatched:           {mismatched} ({mismatched/total_pairs*100:.1f}%)" if total_pairs else "n/a")
    print()
    print(f"Defect elimination: {matched_pairs}/{total_pairs} = "
          f"{matched_pairs/total_pairs*100:.2f}% match rate" if total_pairs else "no data")
    print(f"v1.0.0 baseline: 94/475 = 19.79% match rate (376/475 inverted)")
    if mismatched == 0:
        print(f"\nPERFECT ELIMINATION: 0 inverted/mismatched pairs across {n_built} built tickers.")
    else:
        print(f"\nPARTIAL: {mismatched} mismatched pairs remain — investigate.")

    summary = {
        "audit": "ERVN-PERIOD-001 v1.0.1 re-audit v2",
        "audit_date": "2026-07-18",
        "tickers_total": len(PACKS),
        "tickers_built_v1_0_1": n_built,
        "tickers_fail_closed": n_fail_closed,
        "tickers_gate_pass": n_pass,
        "tickers_field_mismatch": n_field_mismatch,
        "total_pairs_checked": total_pairs,
        "matched_pairs": matched_pairs,
        "mismatched_or_inverted": mismatched,
        "match_rate": round(matched_pairs/total_pairs, 4) if total_pairs else 0,
        "v1_0_0_baseline": {"matched": 94, "total": 475, "match_rate": 0.1979},
        "improvement": f"{matched_pairs/total_pairs*100:.2f}% vs 19.79% baseline" if total_pairs else "n/a",
        "defect_eliminated": mismatched == 0,
        "per_sector": dict(sorted(per_sector.items())),
        "per_ticker": per_ticker,
    }
    json.dump(summary, open(SUMMARY, "w"), indent=2, ensure_ascii=False)
    print(f"\nsummary: {SUMMARY}")


if __name__ == "__main__":
    main()
