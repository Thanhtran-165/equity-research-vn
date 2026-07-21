#!/usr/bin/env python3
"""
ERVN-PERIOD-001 §10 — Affected Artifact Registry.

Scans all artifact directories under agent-eval/ that contain a
verified-dashboard-data.json (the v1.0.0 builder output). For each, records:
  - artifact_id, ticker, generated_at
  - source_snapshot_hash (if discoverable)
  - inversion_detected (re-run period_integrity_gate logic on the contract)
  - affected_metrics, affected_sections
  - remediation_status

Per owner directive §10: don't delete artifacts, but tag them with the warning.
"""
import os, sys, json, csv, glob, hashlib, datetime
from collections import defaultdict

AGENT_EVAL = "/Users/bobo/ZCodeProject/agent-eval"
REGISTRY_PATH = "/Users/bobo/.zcode/skills/equity-research-vn/incidents/ERVN-PERIOD-001-affected-artifact-registry.json"
YEARS = [2021, 2022, 2023, 2024, 2025]


def find_csv_col(headers, aliases):
    for h in headers:
        hl = h.lower()
        for a in aliases:
            if a in hl:
                return h
    return None


def _safe_float(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _approx_eq(a, b, rel_tol=0.001, abs_tol=1.0):
    if a is None or b is None:
        return a is None and b is None
    try:
        a_f, b_f = float(a), float(b)
    except (ValueError, TypeError):
        return False
    if abs(a_f - b_f) <= abs_tol:
        return True
    denom = max(abs(a_f), abs(b_f), 1.0)
    return abs(a_f - b_f) / denom <= rel_tol


def assess_artifact(artifact_dir):
    """Check one artifact dir for period-inversion."""
    vdj_path = os.path.join(artifact_dir, "verified-dashboard-data.json")
    if not os.path.exists(vdj_path):
        return None
    try:
        vdj = json.load(open(vdj_path))
    except Exception:
        return None

    # Find CSV in same dir or parent source-pack
    csv_path = os.path.join(artifact_dir, "income_statement_sponsor.csv")
    if not os.path.exists(csv_path):
        # Try parent
        parent_csv = os.path.join(os.path.dirname(artifact_dir), "income_statement_sponsor.csv")
        if os.path.exists(parent_csv):
            csv_path = parent_csv
        else:
            return {
                "artifact_dir": artifact_dir,
                "vdj_present": True,
                "csv_present": False,
                "assessment": "no_csv_for_comparison",
            }

    try:
        rows = list(csv.DictReader(open(csv_path)))
    except Exception:
        return {"artifact_dir": artifact_dir, "vdj_present": True, "csv_present": True,
                "assessment": "csv_unparseable"}

    # Use v1.0.0 heuristic: was revenue[2025] in contract = row 0 or row 4?
    rev_col = find_csv_col(rows[0].keys(), ["sales", "net sales", "revenue"])
    if not rev_col:
        return {"artifact_dir": artifact_dir, "vdj_present": True, "csv_present": True,
                "assessment": "no_revenue_column"}
    csv_first5 = []
    year_rows = [r for r in rows if r.get("report_period") == "year"]
    if not year_rows:
        year_rows = rows[:5]
    for r in year_rows[:5]:
        csv_first5.append(_safe_float(r.get(rev_col)))
    fin = vdj.get("financials", {})
    years_arr = fin.get("years", [str(y) for y in YEARS])
    rev_arr = fin.get("revenue", [])
    if not rev_arr or len(rev_arr) != len(years_arr):
        return {"artifact_dir": artifact_dir, "vdj_present": True, "csv_present": True,
                "assessment": "length_mismatch"}

    # Compare latest period (years_arr last) value against csv_first5[0] (v1.0.0 inverted)
    # and csv_first5[-1] (correct)
    latest_year = years_arr[-1]
    latest_idx = years_arr.index(latest_year)
    latest_contract_val = rev_arr[latest_idx] * 1e9 if rev_arr[latest_idx] else None  # tỷ → VND
    csv_row0 = csv_first5[0]
    csv_row_last = csv_first5[-1] if len(csv_first5) >= 5 else None

    matches_row0 = _approx_eq(latest_contract_val, csv_row0)  # ascending CSV + v1.0.0 inversion
    matches_row_last = _approx_eq(latest_contract_val, csv_row_last)  # ascending CSV + correct
    # If neither matches, ambiguous
    if matches_row0 and not matches_row_last:
        assessment = "INVERTED"
    elif matches_row_last and not matches_row0:
        assessment = "CORRECT"
    elif matches_row0 and matches_row_last:
        assessment = "AMBIGUOUS_VALUES_EQUAL"
    else:
        assessment = "AMBIGUOUS_NO_MATCH"

    # Affected metrics: do same for netProfit, eps
    affected = []
    for field_key, csv_aliases in [("netProfit", ["attributable to parent company", "net profit", "profit after tax"]),
                                    ("eps", ["eps basic"])]:
        col = find_csv_col(rows[0].keys(), csv_aliases)
        if not col:
            continue
        arr = fin.get(field_key, [])
        if not arr or len(arr) != len(years_arr):
            continue
        scale = 1e9 if field_key == "netProfit" else 1.0
        latest_val = arr[latest_idx] * scale if arr[latest_idx] else None
        col_first5 = []
        for r in year_rows[:5]:
            col_first5.append(_safe_float(r.get(col)))
        col_row0 = col_first5[0]
        col_row_last = col_first5[-1] if len(col_first5) >= 5 else None
        if _approx_eq(latest_val, col_row0) and not _approx_eq(latest_val, col_row_last):
            affected.append(field_key)

    if assessment == "INVERTED":
        affected.insert(0, "revenue")

    return {
        "artifact_dir": artifact_dir,
        "vdj_present": True,
        "csv_present": True,
        "ticker": vdj.get("ticker"),
        "assessment": assessment,
        "latest_period": latest_year,
        "latest_period_revenue_in_contract": rev_arr[latest_idx] if rev_arr else None,
        "csv_row0_revenue": csv_row0,
        "csv_row_last_revenue": csv_row_last,
        "affected_metrics": list(set(affected)) if affected else [],
        "affected_sections": ["financials", "valuation", "trend_charts", "growth_calculations",
                              "narrative_conclusions"] if assessment == "INVERTED" else [],
    }


def main():
    print(f"=== ERVN-PERIOD-001 §10 — Affected Artifact Registry ===")
    # Find all verified-dashboard-data.json files
    candidates = glob.glob(f"{AGENT_EVAL}/**/verified-dashboard-data.json", recursive=True)
    print(f"found {len(candidates)} candidate artifacts")
    print()

    registry = []
    counts = defaultdict(int)
    for vdj in sorted(candidates):
        ad = os.path.dirname(vdj)
        info = assess_artifact(ad)
        if info is None:
            continue
        registry.append(info)
        counts[info.get("assessment", "unknown")] += 1

    # Mark known-bad artifacts
    n_inverted = counts.get("INVERTED", 0)
    n_correct = counts.get("CORRECT", 0)
    n_ambiguous = counts.get("AMBIGUOUS_VALUES_EQUAL", 0) + counts.get("AMBIGUOUS_NO_MATCH", 0)
    n_other = sum(v for k, v in counts.items()
                  if k not in ("INVERTED", "CORRECT", "AMBIGUOUS_VALUES_EQUAL", "AMBIGUOUS_NO_MATCH"))

    print(f"Assessment breakdown:")
    for status, n in sorted(counts.items()):
        print(f"  {status:30s}: {n}")
    print()

    payload = {
        "registry_date": datetime.datetime.now().isoformat(),
        "incident": "ERVN-PERIOD-001",
        "total_artifacts": len(registry),
        "summary": {
            "inverted": n_inverted,
            "correct": n_correct,
            "ambiguous": n_ambiguous,
            "other": n_other,
        },
        "warning_text": "DATA INTEGRITY WARNING — PERIOD MAPPING INCIDENT ERVN-PERIOD-001",
        "remediation_policy": "Historical artifacts preserved as evidence. Marked as "
                              "INVALID_FOR_PERIOD_SENSITIVE_CONCLUSIONS. Not deleted, not "
                              "regenerated. Owners of any shared artifacts should re-issue "
                              "from v1.0.1 once released.",
        "artifacts": registry,
    }
    json.dump(payload, open(REGISTRY_PATH, "w"), indent=2, ensure_ascii=False, default=str)
    print(f"registry: {REGISTRY_PATH}")
    print()
    print(f"=== Period-inversion affected artifacts: {n_inverted} ===")
    if n_inverted > 0:
        print(f"\nFirst 10 INVERTED artifacts:")
        for art in [a for a in registry if a.get("assessment") == "INVERTED"][:10]:
            print(f"  {art.get('artifact_dir')}")
            print(f"    ticker={art.get('ticker')}, affected={art.get('affected_metrics')}")


if __name__ == "__main__":
    main()
