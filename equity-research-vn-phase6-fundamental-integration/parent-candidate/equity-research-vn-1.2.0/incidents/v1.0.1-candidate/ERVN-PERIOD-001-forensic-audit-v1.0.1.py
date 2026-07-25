#!/usr/bin/env python3
"""
ERVN-PERIOD-001 — Forensic audit re-run against v1.0.1 build_data_contract.py.

Repeats the original audit methodology but uses the v1.0.1 patched builder
(with period_key_resolver). Expected: 0/475 inverted (down from 376/475).

Failure mode: any ticker still showing inverted pairs means the resolver
didn't work for that pack.
"""
import os, sys, csv, json, subprocess, math

V101_BUILDER = "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-candidate/runner/build_data_contract.py"
PYTHON = sys.executable
OUT_DIR = "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-candidate/forensic-audit-runs-v1.0.1"
RESULTS = "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-candidate/ERVN-PERIOD-001-forensic-v1.0.1.jsonl"
SUMMARY = "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-candidate/ERVN-PERIOD-001-forensic-v1.0.1-summary.json"

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
YEARS = [2021, 2022, 2023, 2024, 2025]
FIELDS = [("revenue", ["sales", "net sales", "revenue"]),
          ("net_profit", ["attributable to parent company", "net profit", "profit after tax"]),
          ("eps", ["eps basic", "earnings per share"])]
PARENT_KEYS = {"revenue": "revenue", "net_profit": "netProfit", "eps": "eps"}
PARENT_SCALES = {"revenue": 1e9, "net_profit": 1e9, "eps": 1.0}

os.makedirs(OUT_DIR, exist_ok=True)
open(RESULTS, "w").close()


def find_csv_col(rows, canon):
    aliases = {f[0]: f[1] for f in FIELDS}
    for h in rows[0].keys():
        hl = h.lower()
        for a in aliases[canon]:
            if a in hl:
                return h
    return None


def approx_eq(a, b):
    if a is None or b is None:
        return a is None and b is None
    try:
        a_f, b_f = float(a), float(b)
    except (ValueError, TypeError):
        return False
    denom = max(abs(a_f), abs(b_f), 1.0)
    return abs(a_f - b_f) / denom < 0.001


def trace_ticker(t, sector, src):
    run_dir = os.path.join(OUT_DIR, t)
    if os.path.isdir(run_dir):
        import shutil; shutil.rmtree(run_dir)
    os.makedirs(run_dir, exist_ok=True)
    p = subprocess.run([PYTHON, V101_BUILDER, src, run_dir],
                       capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        return {"ticker": t, "sector": sector, "error": "builder_v1.0.1_failed",
                "stderr": p.stderr[:300]}

    vdj_path = os.path.join(run_dir, "verified-dashboard-data.json")
    if not os.path.exists(vdj_path):
        return {"ticker": t, "sector": sector, "error": "no_vdj"}
    vdj = json.load(open(vdj_path))
    fin = vdj.get("financials", {})
    years_arr = fin.get("years", [str(y) for y in YEARS])

    inc_path = os.path.join(src, "income_statement_sponsor.csv")
    if not os.path.exists(inc_path):
        return {"ticker": t, "sector": sector, "error": "no_csv"}
    rows = list(csv.DictReader(open(inc_path)))
    if not rows:
        return {"ticker": t, "sector": sector, "error": "empty_csv"}

    overall_actual = overall_inverted = overall_neither = 0
    for canon in [f[0] for f in FIELDS]:
        col = find_csv_col(rows, canon)
        if not col:
            continue
        raw_first5 = []
        for r in rows[:5]:
            try:
                raw_first5.append(float(r[col]))
            except (ValueError, TypeError):
                raw_first5.append(None)
        arr = fin.get(PARENT_KEYS[canon], [])
        scale = PARENT_SCALES[canon]
        for i, y in enumerate(YEARS):
            raw_actual = raw_first5[i] if i < len(raw_first5) else None
            raw_inverted = raw_first5[4 - i] if (4 - i) < len(raw_first5) else None
            if str(y) in years_arr:
                y_idx = years_arr.index(str(y))
                parent_val = arr[y_idx] * scale if y_idx < len(arr) else None
            else:
                parent_val = None
            if parent_val is None:
                continue
            if approx_eq(parent_val, raw_actual):
                overall_actual += 1
            elif approx_eq(parent_val, raw_inverted):
                overall_inverted += 1
            else:
                overall_neither += 1

    return {
        "ticker": t, "sector": sector, "source_pack": src,
        "n_actual_match": overall_actual,
        "n_inverted_match": overall_inverted,
        "n_neither": overall_neither,
    }


def main():
    print(f"=== ERVN-PERIOD-001 Forensic Re-audit — v1.0.1 builder ===")
    print(f"tickers: {len(PACKS)}")
    print(f"expected: 0 inverted (down from 376/475 in v1.0.0)")
    print()

    grand_actual = grand_inverted = grand_neither = 0
    per_sector = {}
    failed = []
    clean_count = 0
    still_inverted = 0

    for t, sector, src in PACKS:
        rec = trace_ticker(t, sector, src)
        with open(RESULTS, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        if "error" in rec:
            failed.append((t, sector, rec["error"]))
            print(f"  [FAIL] {t:5s} ({sector:20s}): {rec['error']}")
            continue

        grand_actual += rec["n_actual_match"]
        grand_inverted += rec["n_inverted_match"]
        grand_neither += rec["n_neither"]
        sect_stats = per_sector.setdefault(sector, {"actual": 0, "inverted": 0, "neither": 0, "tickers": 0})
        sect_stats["actual"] += rec["n_actual_match"]
        sect_stats["inverted"] += rec["n_inverted_match"]
        sect_stats["neither"] += rec["n_neither"]
        sect_stats["tickers"] += 1

        if rec["n_inverted_match"] == 0 and rec["n_actual_match"] > 0:
            clean_count += 1
            flag = "✓ CLEAN"
        elif rec["n_inverted_match"] > 0:
            still_inverted += 1
            flag = "✗ STILL_INVERTED"
        else:
            flag = "? NO_MATCHES"
        print(f"  [{flag:25s}] {t:5s} ({sector:20s}): actual={rec['n_actual_match']:2d}  "
              f"inverted={rec['n_inverted_match']:2d}  neither={rec['n_neither']:2d}")

    total_pairs = grand_actual + grand_inverted + grand_neither
    print()
    print("=" * 90)
    print(f"V1.0.1 FORENSIC RE-AUDIT SUMMARY")
    print("=" * 90)
    print(f"tickers scanned:        {len(PACKS)}")
    print(f"failed:                 {len(failed)}")
    print(f"CLEAN tickers:          {clean_count}")
    print(f"STILL_INVERTED tickers: {still_inverted}")
    print(f"distinct sectors:       {len(per_sector)}")
    print()
    print(f"Total (period,value) pairs:  {total_pairs}")
    print(f"  correctly assigned:        {grand_actual} ({grand_actual/total_pairs*100:.1f}%)")
    print(f"  INVERTED (defect):         {grand_inverted} ({grand_inverted/total_pairs*100:.1f}%)")
    print(f"  neither:                   {grand_neither} ({grand_neither/total_pairs*100:.1f}%)")
    print()

    improvement = ""
    if grand_inverted == 0 and still_inverted == 0:
        improvement = "PERFECT — defect eliminated"
    elif still_inverted > 0:
        improvement = f"PARTIAL — {still_inverted} tickers still inverted"
    print(f"Defect elimination status: {improvement}")
    print(f"v1.0.0 → v1.0.1: 376 inverted → {grand_inverted} inverted "
          f"({100*(376-grand_inverted)/376:.1f}% reduction)")

    summary = {
        "audit": "ERVN-PERIOD-001 v1.0.1 re-audit",
        "audit_date": "2026-07-18",
        "builder": V101_BUILDER,
        "tickers_scanned": len(PACKS),
        "tickers_failed": len(failed),
        "tickers_clean": clean_count,
        "tickers_still_inverted": still_inverted,
        "total_period_value_pairs": total_pairs,
        "correctly_period_assigned": grand_actual,
        "inverted_period_assigned": grand_inverted,
        "neither_match": grand_neither,
        "inversion_rate": round(grand_inverted / total_pairs, 4) if total_pairs else 0,
        "v1_0_0_baseline": {"inverted": 376, "total": 475, "rate": 0.7916},
        "improvement_pct": round(100 * (376 - grand_inverted) / 376, 2),
        "defect_eliminated": grand_inverted == 0 and still_inverted == 0,
        "per_sector": dict(sorted(per_sector.items())),
        "failed": [{"ticker": t, "sector": s, "error": e} for t, s, e in failed],
    }
    json.dump(summary, open(SUMMARY, "w"), indent=2, ensure_ascii=False)
    print(f"\nsummary: {SUMMARY}")
    print(f"results: {RESULTS}")


if __name__ == "__main__":
    main()
