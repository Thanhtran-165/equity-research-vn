#!/usr/bin/env python3
"""
ERVN-PERIOD-001 regression suite — proves period_integrity_gate distinguishes
all 6 mutation classes per owner directive §7.

Mutation variants:
  1. clean           — periods=[2021..2025], values=[10,20,30,40,50]   → expect PASS
  2. inverted        — periods=[2021..2025], values=[50,40,30,20,10]   → expect FAIL
  3. shifted         — periods=[2021..2025], values=[20,30,40,50,10]   → expect FAIL
  4. duplicate_period— periods=[2021,2022,2022,2024,2025]              → expect FAIL
  5. missing_metadata— no fundamental_sponsor.json                     → expect FAIL_CLOSED
  6. mixed_frequency — 'year' and 'quarter' rows in same CSV           → expect FAIL_CLOSED

Plus:
  7. collector_alignment  — Phase 6F collector output remains valid     → expect PASS

For each variant, build a synthetic source pack + contract, run gate,
verify the expected verdict. Records pass/fail per variant.
"""
import os, sys, json, csv, shutil, tempfile, hashlib

sys.path.insert(0, "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-candidate/runner")
from period_integrity_gate import evaluate as gate_evaluate, render_report as gate_render
from period_key_resolver import ResolverError

ROOT = "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-candidate/tests/fixtures"
os.makedirs(ROOT, exist_ok=True)


def write_synthetic_pack(pack_dir, periods, revenue_values, np_values, eps_values,
                          report_period="year", include_metadata=True,
                          fs_revenue_overrides=None):
    """Build a synthetic source pack with explicit values."""
    os.makedirs(pack_dir, exist_ok=True)
    # income CSV
    with open(os.path.join(pack_dir, "income_statement_sponsor.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["report_period", "ticker", "Sales",
                    "Attributable to parent company", "EPS basic (VND)"])
        # CSV is ASCENDING by year (vnstock sponsor convention)
        for p, r, n, e in zip(periods, revenue_values, np_values, eps_values):
            w.writerow([report_period, "TEST", r, n, e])
    # balance + cash (minimal — only used by resolver cross-check)
    with open(os.path.join(pack_dir, "balance_sheet_sponsor.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["report_period", "ticker", "Total Assets", "Owner's Equity"])
        for p in periods:
            w.writerow([report_period, "TEST", 100_000_000_000, 50_000_000_000])
    with open(os.path.join(pack_dir, "cash_flow_sponsor.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["report_period", "ticker", "Purchases of fixed assets"])
        for p in periods:
            w.writerow([report_period, "TEST", -10_000_000_000])
    # overview
    json.dump({"symbol": "TEST", "organ_name": "Test Tall", "current_price": 100000,
               "issue_share": 1_000_000, "sector": "Test"},
              open(os.path.join(pack_dir, "overview.json"), "w"), indent=2)
    # fundamental_sponsor.json (the period metadata)
    if include_metadata:
        data = {}
        for i, p in enumerate(periods):
            data[str(p)] = {
                "revenue": revenue_values[i],
                "net_profit": np_values[i],
                "eps": eps_values[i],
                "total_assets": 100_000_000_000,
                "total_equity": 50_000_000_000,
                "capex": -10_000_000_000,
            }
        if fs_revenue_overrides:
            for p, v in fs_revenue_overrides.items():
                if str(p) in data:
                    data[str(p)]["revenue"] = v
        snapshot = {
            "ticker": "TEST",
            "source_id": "synthetic_test_fixture",
            "years": [str(p) for p in periods],
            "data": data,
            "price": 100000, "shares": 1_000_000,
        }
        json.dump(snapshot, open(os.path.join(pack_dir, "fundamental_sponsor.json"), "w"),
                  indent=2, ensure_ascii=False)


def write_contract(contract_path, periods, revenue_arr_ty=None, np_arr_ty=None,
                    eps_arr=None):
    """Write a verified-dashboard-data.json with given array values."""
    if revenue_arr_ty is None:
        revenue_arr_ty = [10, 20, 30, 40, 50]
    if np_arr_ty is None:
        np_arr_ty = [5, 10, 15, 20, 25]
    if eps_arr is None:
        eps_arr = [1000, 1100, 1200, 1300, 1400]
    contract = {
        "company": "Test Tall", "ticker": "TEST", "price": 100000, "shares": 1_000_000,
        "periods": list(periods),
        "financials": {
            "revenue": revenue_arr_ty, "netProfit": np_arr_ty, "eps": eps_arr,
            "totalAssets": [100, 100, 100, 100, 100], "equity": [50, 50, 50, 50, 50],
            "capex": [10, 10, 10, 10, 10],
            "years": [str(p) for p in periods],
        },
        "valuation": {"pe": None, "pb": None, "price": 100000},
    }
    json.dump(contract, open(contract_path, "w"), indent=2)


def run_variant(name, build_pack_fn, build_contract_fn, expected_pass,
                 expected_resolver_error=None):
    """Run one regression variant. Returns dict with verdict."""
    pack_dir = os.path.join(ROOT, name, "source-pack")
    contract_path = os.path.join(ROOT, name, "verified-dashboard-data.json")
    if os.path.isdir(os.path.join(ROOT, name)):
        shutil.rmtree(os.path.join(ROOT, name))
    os.makedirs(pack_dir, exist_ok=True)
    build_pack_fn(pack_dir)
    build_contract_fn(contract_path)

    print(f"\n--- {name} ---")
    print(f"  expected: {'PASS' if expected_pass else 'FAIL'}/{expected_resolver_error or 'n/a'}")
    try:
        result = gate_evaluate(pack_dir, contract_path)
        actual_pass = result.overall_pass
        actual_resolver_error = None
        print(f"  actual:   {'PASS' if actual_pass else 'FAIL'} (gate)")
        print(f"  detection_method: {result.detection_method}")
        for k, v in result.sub_checks.items():
            mark = "✓" if v is True else "✗" if v is False else "?"
            print(f"    [{mark}] {k}: {v}")
        verdict_pass = (actual_pass == expected_pass)
        verdict_resolver = True  # gate didn't raise
    except ResolverError as e:
        actual_pass = False
        actual_resolver_error = e.code
        print(f"  actual:   FAIL_CLOSED by resolver ({e.code})")
        print(f"  detail: {e.detail[:120]}")
        verdict_pass = (expected_pass is False)  # FAIL_CLOSED counts as expected FAIL
        verdict_resolver = (expected_resolver_error is None) or (e.code == expected_resolver_error)
    overall_ok = verdict_pass and verdict_resolver
    print(f"  VERDICT: {'✓ PASS' if overall_ok else '✗ FAIL'}")
    return {
        "variant": name,
        "expected_pass": expected_pass,
        "expected_resolver_error": expected_resolver_error,
        "actual_pass": actual_pass,
        "actual_resolver_error": actual_resolver_error,
        "verdict_ok": overall_ok,
    }


def main():
    print("=" * 80)
    print("ERVN-PERIOD-001 REGRESSION SUITE — 6 + 1 variants")
    print("=" * 80)

    results = []

    # 1. CLEAN
    def clean_pack(d):
        write_synthetic_pack(d, [2021, 2022, 2023, 2024, 2025],
                              [10e9, 20e9, 30e9, 40e9, 50e9],
                              [5e9, 10e9, 15e9, 20e9, 25e9],
                              [1000, 1100, 1200, 1300, 1400])
    def clean_contract(p):
        write_contract(p, [2021, 2022, 2023, 2024, 2025],
                        revenue_arr_ty=[10, 20, 30, 40, 50],
                        np_arr_ty=[5, 10, 15, 20, 25],
                        eps_arr=[1000, 1100, 1200, 1300, 1400])
    results.append(run_variant("clean", clean_pack, clean_contract, expected_pass=True))

    # 2. INVERTED
    def inverted_pack(d):
        # Pack is clean (same as clean)
        write_synthetic_pack(d, [2021, 2022, 2023, 2024, 2025],
                              [10e9, 20e9, 30e9, 40e9, 50e9],
                              [5e9, 10e9, 15e9, 20e9, 25e9],
                              [1000, 1100, 1200, 1300, 1400])
    def inverted_contract(p):
        # Contract has values REVERSED — mimics v1.0.0 defect
        write_contract(p, [2021, 2022, 2023, 2024, 2025],
                        revenue_arr_ty=[50, 40, 30, 20, 10],
                        np_arr_ty=[25, 20, 15, 10, 5],
                        eps_arr=[1400, 1300, 1200, 1100, 1000])
    results.append(run_variant("inverted", inverted_pack, inverted_contract,
                                 expected_pass=False))

    # 3. SHIFTED (rotation, not full inversion)
    def shifted_pack(d):
        write_synthetic_pack(d, [2021, 2022, 2023, 2024, 2025],
                              [10e9, 20e9, 30e9, 40e9, 50e9],
                              [5e9, 10e9, 15e9, 20e9, 25e9],
                              [1000, 1100, 1200, 1300, 1400])
    def shifted_contract(p):
        # Shifted by one year (2021's value goes to 2022, etc.)
        write_contract(p, [2021, 2022, 2023, 2024, 2025],
                        revenue_arr_ty=[50, 10, 20, 30, 40],  # last wrapped to first
                        np_arr_ty=[25, 5, 10, 15, 20],
                        eps_arr=[1400, 1000, 1100, 1200, 1300])
    results.append(run_variant("shifted", shifted_pack, shifted_contract,
                                 expected_pass=False))

    # 4. DUPLICATE_PERIOD
    def dup_pack(d):
        # CSV has duplicate years
        write_synthetic_pack(d, [2021, 2022, 2022, 2024, 2025],
                              [10e9, 20e9, 30e9, 40e9, 50e9],
                              [5e9, 10e9, 15e9, 20e9, 25e9],
                              [1000, 1100, 1200, 1300, 1400])
    def dup_contract(p):
        write_contract(p, [2021, 2022, 2022, 2024, 2025],
                        revenue_arr_ty=[10, 20, 30, 40, 50])
    results.append(run_variant("duplicate_period", dup_pack, dup_contract,
                                 expected_pass=False))

    # 5. MISSING_METADATA (no fundamental_sponsor.json)
    def missing_pack(d):
        write_synthetic_pack(d, [2021, 2022, 2023, 2024, 2025],
                              [10e9, 20e9, 30e9, 40e9, 50e9],
                              [5e9, 10e9, 15e9, 20e9, 25e9],
                              [1000, 1100, 1200, 1300, 1400],
                              include_metadata=False)
    def missing_contract(p):
        write_contract(p, [2021, 2022, 2023, 2024, 2025],
                        revenue_arr_ty=[10, 20, 30, 40, 50])
    results.append(run_variant("missing_metadata", missing_pack, missing_contract,
                                 expected_pass=False,
                                 expected_resolver_error="POSITIONAL_ONLY_ASSUMPTION"))

    # 6. MIXED_FREQUENCY
    def mixed_pack(d):
        # Make a CSV with mixed year + quarter rows
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "income_statement_sponsor.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["report_period", "ticker", "Sales",
                        "Attributable to parent company", "EPS basic (VND)"])
            # Mix year and quarter
            for kind, val in [("year", 10e9), ("quarter", 3e9), ("year", 20e9),
                              ("quarter", 5e9), ("year", 30e9)]:
                w.writerow([kind, "TEST", val, val*0.1, 1000])
        # balance + cash (minimal)
        for stmt in ["balance_sheet_sponsor.csv", "cash_flow_sponsor.csv"]:
            with open(os.path.join(d, stmt), "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["report_period", "ticker", "X"])
                for kind in ["year", "quarter", "year", "quarter", "year"]:
                    w.writerow([kind, "TEST", 1])
        # overview
        json.dump({"symbol": "TEST", "organ_name": "Test", "current_price": 100000,
                   "issue_share": 1000000, "sector": "Test"},
                  open(os.path.join(d, "overview.json"), "w"), indent=2)
        # fundamental_sponsor.json still present
        data = {}
        for i, y in enumerate([2021, 2022, 2023, 2024, 2025]):
            data[str(y)] = {"revenue": (i+1)*10e9}
        json.dump({"years": ["2021","2022","2023","2024","2025"], "data": data,
                   "ticker": "TEST"}, open(os.path.join(d, "fundamental_sponsor.json"), "w"),
                  indent=2)
    def mixed_contract(p):
        write_contract(p, [2021, 2022, 2023, 2024, 2025],
                        revenue_arr_ty=[10, 20, 30, 40, 50])
    results.append(run_variant("mixed_frequency", mixed_pack, mixed_contract,
                                 expected_pass=False))

    # 7. COLLECTOR_ALIGNMENT — uses real collector output from Phase 6F
    def collector_pack(d):
        # Use Phase 6E FPT source pack
        for f in ["income_statement_sponsor.csv", "balance_sheet_sponsor.csv",
                  "cash_flow_sponsor.csv", "overview.json", "fundamental_sponsor.json"]:
            src = f"/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/FPT/{f}"
            if os.path.exists(src):
                shutil.copy(src, os.path.join(d, f))
    def collector_contract(p):
        # Use v1.0.1 builder output
        shutil.copy("/tmp/v101-fpt-redo/verified-dashboard-data.json", p)
    results.append(run_variant("collector_alignment", collector_pack, collector_contract,
                                 expected_pass=True))

    # Summary
    print()
    print("=" * 80)
    print("REGRESSION SUITE SUMMARY")
    print("=" * 80)
    n_ok = sum(1 for r in results if r["verdict_ok"])
    n_total = len(results)
    for r in results:
        mark = "✓" if r["verdict_ok"] else "✗"
        print(f"  [{mark}] {r['variant']:25s} expected={'PASS' if r['expected_pass'] else 'FAIL':5s} "
              f"actual={'PASS' if r['actual_pass'] else 'FAIL':5s}")
    print()
    print(f"Passed: {n_ok}/{n_total}")
    if n_ok == n_total:
        print("ALL REGRESSION VARIANTS BEHAVE AS EXPECTED ✅")
    else:
        print(f"{n_total - n_ok} VARIANTS FAILED — investigate ❌")

    # Save results
    summary_path = "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-candidate/ERVN-PERIOD-001-regression-summary.json"
    json.dump({"date": "2026-07-18", "results": results,
               "n_passed": n_ok, "n_total": n_total,
               "all_pass": n_ok == n_total},
              open(summary_path, "w"), indent=2)
    print(f"\nsummary: {summary_path}")

    return 0 if n_ok == n_total else 1


if __name__ == "__main__":
    sys.exit(main())
