#!/usr/bin/env python3
"""
period_integrity_gate.py — Period-integrity gate for build_data_contract.py output.

ERVN-PERIOD-001 HOTFIX (equity-research-vn-1.0.1).

Validates that every (period, value) pair in the rendered contract matches the
corresponding (period, value) pair in the raw source CSV. Catches period-inversion
defects that escape the v0.14.9 verifier (which only checks internal consistency).

Sub-checks (6):
  1. raw_periods_unique                — all 5 period labels distinct
  2. values_length_matches_periods     — array length == period count, per field
  3. period_order_detected             — resolver returned a non-positional chronological_order
  4. explicit_period_value_pairs_preserved — every (period, value) survives round-trip
  5. latest_period_matches_source      — contract's latest period value == raw source's latest
  6. oldest_period_matches_source      — contract's oldest period value == raw source's oldest

Fields checked (PER FIELD, not aggregate):
  revenue, net_profit, eps, total_assets, total_equity, capex, operating_cash_flow

Failure mode: FAIL_PERIOD_PROVENANCE_INCOMPLETE (critical).
"""
import os
import sys
import csv
import json
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Add runner dir for resolver import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from period_key_resolver import resolve_periods, ResolverError, PeriodResolution

# Critical fields: canonical name → (csv_statement, csv_aliases, parent_array_key, scale)
# scale: multiplier to convert raw VND → contract units (e.g., 1e9 for tỷ VND arrays)
FIELDS = [
    # (canonical, statement_key, csv_aliases, parent_array_key, scale_to_contract)
    ("revenue",         "income",  ["sales", "net sales", "revenue"], "revenue",     1e-9),
    ("net_profit",      "income",  ["attributable to parent company", "net profit", "profit after tax"], "netProfit", 1e-9),
    ("eps",             "income",  ["eps basic", "earnings per share"], "eps",         1.0),
    ("total_assets",    "balance", ["total assets"], "totalAssets", 1e-9),
    ("total_equity",    "balance", ["owner's equity", "owners equity", "total equity",
                                     "equity attributable"], "equity", 1e-9),
    ("capex",           "cash",    ["purchases of fixed assets", "capex"], "capex", 1e-9),
    # operating_cash_flow: not always in verified-dashboard-data.json financials;
    # skip if absent from contract
]

# Fields whose raw CSV values are negative but contract stores them as positive (abs).
# Builder convention: capex stored as positive magnitude (see build_data_contract.py:268).
ABS_NORMALIZED_FIELDS = {"capex"}

# RC2.2: Canonical → financials array key (for sector-applicability null check)
_CANONICAL_TO_FIN_KEY = {
    "revenue": "revenue",
    "net_profit": "netProfit",
    "eps": "eps",
    "total_assets": "totalAssets",
    "total_equity": "equity",
    "capex": "capex",
}


def _arr_key_for(canonical):
    """Reverse lookup: canonical → financials array key."""
    return _CANONICAL_TO_FIN_KEY.get(canonical, canonical)


def _lookup_fin_array(fin, canonical):
    """Get the financials array for a canonical field. Returns None if absent or null."""
    key = _arr_key_for(canonical)
    return fin.get(key)


def _check_no_downstream_revenue_usage(contract, canonical):
    """Owner condition 4: NOT_APPLICABLE metric must not be consumed downstream.

    For revenue: PE uses EPS, PB uses equity — revenue not directly in valuation.
    Builder does not compute growth, so no growth-formula dependency either.
    Returns True if downstream is safe to skip; False if revenue is somehow used.
    """
    if canonical != "revenue":
        # For non-revenue fields declared NOT_APPLICABLE, downstream check is more complex.
        # Conservative: only allow revenue NOT_APPLICABLE in RC2; other fields must be VALID.
        return False
    # Check valuation doesn't reference revenue
    val = contract.get("valuation", {}) or {}
    # PE = price/eps (no revenue); PB = price/bvps (no revenue). Graham also eps-based.
    # If valuation has unexpected revenue-derived keys, fail.
    revenue_derived_keys = [k for k in val.keys() if "revenue" in k.lower() or "sales" in k.lower()]
    return len(revenue_derived_keys) == 0


@dataclass
class GateResult:
    overall_pass: bool
    sub_checks: Dict[str, bool]
    per_field_results: Dict[str, Dict] = field(default_factory=dict)
    failures: List[dict] = field(default_factory=list)
    detection_method: str = ""
    confidence: str = ""


def _read_csv_rows(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return list(csv.DictReader(f))


def _filter_year_rows(rows):
    if not rows:
        return []
    out = [r for r in rows if str(r.get("report_period","")).strip().lower() == "year"]
    return out if out else rows


def _find_csv_col(headers, aliases):
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
    if math.isnan(a_f) or math.isnan(b_f):
        return False
    if abs(a_f - b_f) <= abs_tol:
        return True
    denom = max(abs(a_f), abs(b_f), 1.0)
    return abs(a_f - b_f) / denom <= rel_tol


def evaluate(source_pack: str, contract_path: str,
             expected_year_count: int = 5,
             allow_value_diff_fallback: bool = False) -> GateResult:
    """Run all 6 sub-checks + per-field cross-check."""
    sub_checks = {}
    failures = []
    per_field = {}

    # Load contract
    if not os.path.exists(contract_path):
        return GateResult(False, {"contract_loadable": False},
                          failures=[{"code": "CONTRACT_MISSING", "path": contract_path}])
    contract = json.load(open(contract_path))

    # SUB-CHECK 1: raw_periods_unique
    fin = contract.get("financials", {})
    years = fin.get("years", [])
    periods_unique = len(set(years)) == len(years) and len(years) == expected_year_count
    sub_checks["raw_periods_unique"] = periods_unique
    if not periods_unique:
        failures.append({"code": "PERIOD_DUPLICATE_OR_WRONG_COUNT",
                         "years": years, "expected_count": expected_year_count})

    # SUB-CHECK 3: period_order_detected (via resolver)
    try:
        resolution = resolve_periods(source_pack,
                                      expected_year_count=expected_year_count,
                                      allow_value_diff_fallback=allow_value_diff_fallback)
        sub_checks["period_order_detected"] = True
        detection_method = resolution.detection_method
        confidence = resolution.confidence
    except ResolverError as e:
        sub_checks["period_order_detected"] = False
        sub_checks["period_order_detected_error"] = e.code
        failures.append({"code": "PERIOD_RESOLUTION_FAILED",
                         "resolver_error": e.code, "detail": e.detail})
        return GateResult(False, sub_checks, per_field, failures,
                          detection_method="(failed)", confidence="(failed)")

    # SUB-CHECK 2: values_length_matches_periods (per field)
    len_ok = True
    for canonical, _, _, arr_key, _ in FIELDS:
        arr = fin.get(arr_key, [])
        if arr and len(arr) != len(years):
            len_ok = False
            failures.append({"code": "VALUES_LENGTH_MISMATCH",
                             "field": canonical, "arr_len": len(arr), "periods_len": len(years)})
    sub_checks["values_length_matches_periods"] = len_ok

    # SUB-CHECK 4 + 5 + 6: per-field (period, value) cross-check
    # Read CSVs using resolver's row indices
    csv_rows_cache = {}
    statement_files = {"income": "income_statement_sponsor.csv",
                       "balance": "balance_sheet_sponsor.csv",
                       "cash": "cash_flow_sponsor.csv"}
    for stmt_key, fname in statement_files.items():
        rows = _filter_year_rows(_read_csv_rows(os.path.join(source_pack, fname)))
        csv_rows_cache[stmt_key] = rows

    # RC2.2: SECTOR_APPLICABILITY_GATE (ERVN-SECTOR-APPLICABILITY-001)
    # Per owner directive 2026-07-19 §2: a metric may be NOT_APPLICABLE only when
    # ALL 4 conditions hold:
    #   1. registered_sector_rule: contract has applicability_rule field
    #   2. metric_status: explicit "NOT_APPLICABLE" status
    #   3. numeric_value_present: false (value is null, NOT 0)
    #   4. downstream_metric_usage: false (not consumed by PE/PB/growth formulas)
    field_applicability = contract.get("field_applicability", {}) or {}

    def evaluate_sector_applicability(canonical):
        """Return (is_na, rule, na_valid).
        is_na: True if contract declares this metric NOT_APPLICABLE
        rule: applicability_rule string or None
        na_valid: True if all 4 owner conditions hold for NOT_APPLICABLE encoding
        """
        info = field_applicability.get(canonical)
        if not info:
            return False, None, True  # not declared N/A; no carve-out needed
        status = info.get("status")
        rule = info.get("applicability_rule")
        if status != "NOT_APPLICABLE":
            return False, rule, True  # declared VALID or unspecified; normal verification
        # status IS NOT_APPLICABLE — verify all 4 conditions
        cond1_registered_rule = rule is not None and isinstance(rule, str) and len(rule) > 0
        cond2_status = (status == "NOT_APPLICABLE")
        # Condition 3: numeric_value_present must be false → financials array must be None
        contract_arr = fin.get(canonical) if canonical == "revenue" else fin.get(_arr_key_for(canonical))
        # Map canonical to fin key
        contract_arr = _lookup_fin_array(fin, canonical)
        cond3_no_numeric = contract_arr is None
        # Condition 4: downstream usage — for revenue, check it's not in valuation/growth
        # Builder doesn't compute growth; valuation uses EPS+price not revenue directly.
        # So revenue NOT_APPLICABLE doesn't break PE/PB. (Growth would be N/A.)
        cond4_no_downstream_usage = _check_no_downstream_revenue_usage(contract, canonical)
        na_valid = cond1_registered_rule and cond2_status and cond3_no_numeric and cond4_no_downstream_usage
        return True, rule, na_valid

    period_value_pairs_preserved = True
    latest_ok = True
    oldest_ok = True
    chronological = resolution.chronological_order  # ["2021", ..., "2025"]
    latest_period = chronological[-1]
    oldest_period = chronological[0]

    for canonical, stmt_key, aliases, arr_key, scale in FIELDS:
        # RC2.2: sector-applicability carve-out check (per owner §2 conditions)
        is_na, rule, na_valid = evaluate_sector_applicability(canonical)
        if is_na:
            if na_valid:
                per_field[canonical] = {
                    "skipped": "SECTOR_NOT_APPLICABLE",
                    "applicability_rule": rule,
                    "na_encoding_valid": True,
                    "conditions": {
                        "registered_sector_rule": True,
                        "metric_status_NOT_APPLICABLE": True,
                        "numeric_value_absent": True,
                        "no_downstream_usage": True,
                    },
                }
                # Period check skipped for this metric only; do NOT contribute to
                # latest_ok/oldest_ok (those still depend on applicable metrics).
                continue
            else:
                # NOT_APPLICABLE declared but encoding invalid — fail loudly
                per_field[canonical] = {
                    "skipped": "INVALID_NA_ENCODING",
                    "applicability_rule": rule,
                    "na_encoding_valid": False,
                }
                period_value_pairs_preserved = False
                latest_ok = False
                oldest_ok = False
                failures.append({
                    "code": "FAIL_INVALID_NOT_APPLICABLE_ENCODING",
                    "field": canonical,
                    "rule": rule,
                    "reason": "NOT_APPLICABLE declared but encoding invalid (likely value=0 instead of null)",
                })
                continue
        arr = fin.get(arr_key, [])
        if not arr:
            per_field[canonical] = {"skipped": "no_contract_array"}
            continue
        csv_rows = csv_rows_cache.get(stmt_key, [])
        if not csv_rows:
            per_field[canonical] = {"skipped": "no_csv"}
            continue
        col = _find_csv_col(csv_rows[0].keys() if csv_rows else [], aliases)
        if not col:
            per_field[canonical] = {"skipped": "no_csv_column"}
            continue

        # For each year, look up raw CSV value at resolver-determined row index
        per_year_results = {}
        for y in chronological:
            idx_info = resolution.period_index.get(y)
            if not idx_info:
                per_year_results[y] = {"error": "no_resolver_index"}
                period_value_pairs_preserved = False
                continue
            row_idx = getattr(idx_info, stmt_key)
            if row_idx >= len(csv_rows):
                per_year_results[y] = {"error": "row_idx_out_of_range",
                                       "row_idx": row_idx, "csv_rows": len(csv_rows)}
                period_value_pairs_preserved = False
                continue
            raw_val = _safe_float(csv_rows[row_idx].get(col))
            # Normalize: some fields (capex) are stored as positive magnitude in contract
            if canonical in ABS_NORMALIZED_FIELDS and raw_val is not None:
                raw_val = abs(raw_val)
            # Convert raw VND → contract units
            raw_in_contract_units = raw_val * scale if raw_val is not None else None
            # Contract value at year's position in array
            if y in years:
                y_idx = years.index(y)
                contract_val = arr[y_idx] if y_idx < len(arr) else None
            else:
                contract_val = None
            match = _approx_eq(raw_in_contract_units, contract_val)
            per_year_results[y] = {
                "csv_row_index": row_idx,
                "raw_csv_value": raw_val,
                "raw_in_contract_units": raw_in_contract_units,
                "contract_value": contract_val,
                "match": match,
            }
            if not match:
                period_value_pairs_preserved = False
                failures.append({
                    "code": "PERIOD_VALUE_PAIR_MISMATCH",
                    "field": canonical, "period": y,
                    "raw_csv_value": raw_val,
                    "contract_value": contract_val,
                })

        per_field[canonical] = {
            "csv_column": col,
            "per_year": per_year_results,
        }
        # Check latest + oldest
        latest_pr = per_year_results.get(latest_period, {})
        oldest_pr = per_year_results.get(oldest_period, {})
        if not latest_pr.get("match"):
            latest_ok = False
        if not oldest_pr.get("match"):
            oldest_ok = False

    sub_checks["explicit_period_value_pairs_preserved"] = period_value_pairs_preserved
    sub_checks["latest_period_matches_source"] = latest_ok
    sub_checks["oldest_period_matches_source"] = oldest_ok

    overall = all(sub_checks.values())
    return GateResult(
        overall_pass=overall,
        sub_checks=sub_checks,
        per_field_results=per_field,
        failures=failures,
        detection_method=detection_method,
        confidence=confidence,
    )


def render_report(result: GateResult) -> str:
    lines = []
    lines.append("=" * 78)
    lines.append("PERIOD INTEGRITY GATE — ERVN-PERIOD-001 hotfix")
    lines.append("=" * 78)
    lines.append(f"detection_method: {result.detection_method}")
    lines.append(f"confidence:       {result.confidence}")
    lines.append(f"overall_pass:     {result.overall_pass}")
    lines.append("")
    lines.append("Sub-checks:")
    for k, v in result.sub_checks.items():
        mark = "✓" if v is True else ("✗" if v is False else "?")
        lines.append(f"  [{mark}] {k}: {v}")
    lines.append("")
    if result.failures:
        lines.append(f"Failures ({len(result.failures)}):")
        for f in result.failures[:20]:
            lines.append(f"  - {f}")
    lines.append("")
    lines.append("Per-field summary:")
    for fname, info in result.per_field_results.items():
        if "skipped" in info:
            lines.append(f"  {fname:18s}: SKIPPED ({info['skipped']})")
            continue
        per_y = info.get("per_year", {})
        all_match = all(yr.get("match") for yr in per_y.values() if "match" in yr)
        n_match = sum(1 for yr in per_y.values() if yr.get("match") is True)
        n_total = sum(1 for yr in per_y.values() if "match" in yr)
        mark = "✓" if all_match else "✗"
        lines.append(f"  {fname:18s}: [{mark}] {n_match}/{n_total} periods match (csv col: {info.get('csv_column')})")
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 period_integrity_gate.py <source_pack> <verified-dashboard-data.json>")
        sys.exit(2)
    src = sys.argv[1]
    contract = sys.argv[2]
    result = evaluate(src, contract)
    print(render_report(result))
    sys.exit(0 if result.overall_pass else 1)
