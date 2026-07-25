#!/usr/bin/env python3
"""
ERVN-PERIOD-001 Forensic Audit — EXPANDED.

For every ticker+source-pack available (34 tickers, 21 sectors):
  1. Run current build_data_contract.py on the source pack
  2. Read raw CSV (income_statement_sponsor.csv) — ground truth
  3. Read parent's verified-dashboard-data.json
  4. For each (year, critical_field), trace:
     - raw_value_actual(year) = csv_rows[year - 2021]
     - parent_assigned(year)  = contract.financials.<field>[year_index]
     - raw_value_inverted(year) = csv_rows[4 - (year - 2021)]  # parent's assumption
     - verdict: ACTUAL_MATCH | INVERTED_MATCH | NEITHER
  5. Aggregate per-ticker + overall

Output: forensic-audit-results.jsonl + summary
"""
import os, sys, csv, json, subprocess, tempfile

BUILDER = "/Users/bobo/ZCodeProject/agent-eval/runner/build_data_contract.py"
PYTHON = sys.executable
OUT_DIR = "/Users/bobo/.zcode/skills/equity-research-vn/incidents/forensic-audit-runs"
RESULTS = "/Users/bobo/.zcode/skills/equity-research-vn/incidents/ERVN-PERIOD-001-forensic-audit.jsonl"
SUMMARY = "/Users/bobo/.zcode/skills/equity-research-vn/incidents/ERVN-PERIOD-001-forensic-summary.json"

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
FIELDS = [
    ("revenue",     ["sales", "net sales", "revenue", "doanh thu"]),
    ("net_profit",  ["attributable to parent company", "net profit", "profit after tax"]),
    ("eps",         ["eps basic", "earnings per share"]),
]

ALIASES_BY_CANON = {f[0]: f[1] for f in FIELDS}
PARENT_KEYS = {"revenue": "revenue", "net_profit": "netProfit", "eps": "eps"}
PARENT_SCALES = {"revenue": 1e9, "net_profit": 1e9, "eps": 1.0}

os.makedirs(OUT_DIR, exist_ok=True)
open(RESULTS, "w").close()


def find_csv_col(rows, canon):
    for h in rows[0].keys():
        hl = h.lower()
        for a in ALIASES_BY_CANON.get(canon, []):
            if a in hl:
                return h
    return None


def approx_eq(a, b):
    if a is None or b is None:
        return a is None and b is None
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    denom = max(abs(a), abs(b), 1.0)
    return abs(a - b) / denom < 0.001


def trace_ticker(t, sector, src):
    """Run parent builder on src, then trace (period, value) pairs for all FIELDS."""
    run_dir = os.path.join(OUT_DIR, t)
    if os.path.isdir(run_dir):
        import shutil; shutil.rmtree(run_dir)
    os.makedirs(run_dir, exist_ok=True)
    p = subprocess.run([PYTHON, BUILDER, src, run_dir],
                       capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        return {"ticker": t, "sector": sector, "error": "builder_failed",
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

    per_field = {}
    overall_actual = overall_inverted = overall_neither = 0
    for canon in [f[0] for f in FIELDS]:
        col = find_csv_col(rows, canon)
        if not col:
            per_field[canon] = {"skipped": "no_csv_column"}
            continue
        # Pull first 5 numeric values
        raw_first5 = []
        for r in rows[:5]:
            try:
                raw_first5.append(float(r[col]))
            except (ValueError, TypeError):
                raw_first5.append(None)
        # Parent's assigned array
        arr = fin.get(PARENT_KEYS[canon], [])
        scale = PARENT_SCALES[canon]
        per_year = {}
        f_actual = f_inverted = f_neither = 0
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
                verdict = "ACTUAL_MATCH"
                f_actual += 1; overall_actual += 1
            elif approx_eq(parent_val, raw_inverted):
                verdict = "INVERTED_MATCH"
                f_inverted += 1; overall_inverted += 1
            else:
                verdict = "NEITHER"
                f_neither += 1; overall_neither += 1
            per_year[str(y)] = {
                "raw_csv_actual": raw_actual,
                "raw_csv_inverted": raw_inverted,
                "parent_assigned": parent_val,
                "verdict": verdict,
            }
        per_field[canon] = {
            "csv_column": col,
            "n_actual_match": f_actual,
            "n_inverted_match": f_inverted,
            "n_neither": f_neither,
            "per_year": per_year,
        }
    return {
        "ticker": t, "sector": sector, "source_pack": src,
        "n_actual_match": overall_actual,
        "n_inverted_match": overall_inverted,
        "n_neither": overall_neither,
        "per_field": per_field,
    }


def main():
    print(f"=== ERVN-PERIOD-001 Forensic Audit (expanded) ===")
    print(f"tickers: {len(PACKS)}")
    print()

    grand_actual = grand_inverted = grand_neither = 0
    per_sector = {}
    per_ticker_summary = []
    fully_inverted_tickers = 0
    mixed_tickers = 0
    clean_tickers = 0
    failed = []

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
        total = rec["n_actual_match"] + rec["n_inverted_match"] + rec["n_neither"]
        sector_stats = per_sector.setdefault(sector, {"actual": 0, "inverted": 0, "neither": 0, "tickers": 0})
        sector_stats["actual"] += rec["n_actual_match"]
        sector_stats["inverted"] += rec["n_inverted_match"]
        sector_stats["neither"] += rec["n_neither"]
        sector_stats["tickers"] += 1
        per_ticker_summary.append({
            "ticker": t, "sector": sector,
            "actual": rec["n_actual_match"], "inverted": rec["n_inverted_match"],
            "neither": rec["n_neither"], "total": total,
        })
        if rec["n_inverted_match"] > 0 and rec["n_actual_match"] == 0:
            fully_inverted_tickers += 1
            v = "FULLY_INVERTED"
        elif rec["n_inverted_match"] > rec["n_actual_match"]:
            mixed_tickers += 1
            v = "MOSTLY_INVERTED"
        elif rec["n_actual_match"] > 0 and rec["n_inverted_match"] == 0:
            clean_tickers += 1
            v = "CLEAN"
        else:
            mixed_tickers += 1
            v = "MIXED"
        print(f"  [{v:15s}] {t:5s} ({sector:20s}): actual={rec['n_actual_match']:2d}  "
              f"inverted={rec['n_inverted_match']:2d}  neither={rec['n_neither']:2d}")

    total_pairs = grand_actual + grand_inverted + grand_neither
    print()
    print("=" * 90)
    print(f"FORENSIC AUDIT SUMMARY — ERVN-PERIOD-001 (Branch A classification)")
    print("=" * 90)
    print(f"tickers scanned:                 {len(PACKS)}")
    print(f"failed (no CSV / no column):     {len(failed)}")
    print(f"tickers with data:               {len(PACKS) - len(failed)}")
    print(f"distinct sectors:                {len(per_sector)}")
    print()
    print(f"FULLY_INVERTED tickers:          {fully_inverted_tickers}  (every checked pair inverted)")
    print(f"MOSTLY/MIXED tickers:            {mixed_tickers}")
    print(f"CLEAN tickers:                   {clean_tickers}")
    print()
    print(f"Total (period,value) pairs:      {total_pairs}")
    print(f"  correctly period-assigned:     {grand_actual} ({grand_actual/total_pairs*100:.1f}%)")
    print(f"  inverted (defect fired):       {grand_inverted} ({grand_inverted/total_pairs*100:.1f}%)")
    print(f"  neither:                       {grand_neither} ({grand_neither/total_pairs*100:.1f}%)")
    print()
    print(f"Per-sector breakdown:")
    for s, st in sorted(per_sector.items()):
        sect_total = st["actual"] + st["inverted"] + st["neither"]
        if sect_total == 0:
            continue
        pct = st["inverted"] / sect_total * 100
        print(f"  {s:20s} ({st['tickers']:2d} tickers): inverted={st['inverted']:3d}/{sect_total:3d} ({pct:5.1f}%)")

    summary = {
        "incident_id": "ERVN-PERIOD-001",
        "audit_date": "2026-07-18",
        "classification": "Branch A — LATENT_RELEASE_DEFECT",
        "classification_evidence": "Release-time CSVs are byte-identical to current CSVs; both ascending (or unsorted-but-row-0-is-oldest by vnstock sponsor convention). Period-inversion defect was present at v1.0.0 qualification.",
        "tickers_scanned": len(PACKS),
        "tickers_failed": len(failed),
        "tickers_with_data": len(PACKS) - len(failed),
        "distinct_sectors": len(per_sector),
        "fully_inverted_tickers": fully_inverted_tickers,
        "mixed_tickers": mixed_tickers,
        "clean_tickers": clean_tickers,
        "total_period_value_pairs": total_pairs,
        "correctly_period_assigned": grand_actual,
        "inverted_period_assigned": grand_inverted,
        "neither_match": grand_neither,
        "inversion_rate": round(grand_inverted / total_pairs, 4) if total_pairs else 0,
        "per_sector": dict(sorted(per_sector.items())),
        "per_ticker": per_ticker_summary,
        "failed": [{"ticker": t, "sector": s, "error": e} for t, s, e in failed],
    }
    json.dump(summary, open(SUMMARY, "w"), indent=2, ensure_ascii=False)
    print(f"\nsummary: {SUMMARY}")
    print(f"results: {RESULTS}")


if __name__ == "__main__":
    main()
