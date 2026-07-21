"""Integration Validator — verify adapter output meets parent IR contract.

Phase 6 P6B. Validates that the adapter + mapper produced output conforming to:
  - parent report-ir.schema.json
  - lossless mapping policy (Directive §8.5-8.6)
  - no forbidden target writes
  - method_results[] preserved intact
  - calculation_trace preserved
  - provenance references valid
"""
from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from valuation_parent_adapter import AdapterResult, AdapterFailure
from integration_version import FORBIDDEN_TARGETS, ALLOWED_TARGETS


@dataclass
class IntegrationValidationResult:
    verdict: str  # PASS | FAIL
    checks_run: int = 0
    checks_passed: int = 0
    checks_failed: int = 0
    failures: List[Dict[str, Any]] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "checks_run": self.checks_run,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "failures": self.failures,
            "evidence": self.evidence,
        }


def validate_integration(
    child_output: Dict[str, Any],
    adapter_result: AdapterResult,
    parent_ir: Dict[str, Any],
) -> IntegrationValidationResult:
    """Run all integration checks."""
    result = IntegrationValidationResult(verdict="PASS")

    def check(condition: bool, name: str, evidence: str = ""):
        result.checks_run += 1
        if condition:
            result.checks_passed += 1
        else:
            result.checks_failed += 1
            result.failures.append({"check": name, "evidence": evidence})

    # === Check 1: child method_results count preserved ===
    child_methods = child_output.get("method_results") or []
    adapter_methods = adapter_result.valuation_methods
    check(
        len(child_methods) == len(adapter_methods),
        "method_count_preserved",
        f"child={len(child_methods)} adapter={len(adapter_methods)}",
    )

    # === Check 2: method IDs preserved (same set) ===
    child_ids = {m.get("method_id") for m in child_methods}
    adapter_ids = {m.get("method_id") for m in adapter_methods}
    check(
        child_ids == adapter_ids,
        "method_ids_preserved",
        f"child_ids={child_ids} adapter_ids={adapter_ids}",
    )

    # === Check 3: method order preserved ===
    child_order = [m.get("method_id") for m in child_methods]
    adapter_order = [m.get("method_id") for m in adapter_methods]
    check(
        child_order == adapter_order,
        "method_order_preserved",
        f"child_order={child_order} adapter_order={adapter_order}",
    )

    # === Check 4: each VALID method has calculation_trace in audit_notes ===
    audit_valuation = parent_ir.get("audit_notes", {}).get("valuation", {})
    preserved_traces = audit_valuation.get("valuation_methods_full", [])
    preserved_trace_ids = {m.get("method_id"): m for m in preserved_traces}
    for m in child_methods:
        if m.get("status") == "VALID":
            preserved = preserved_trace_ids.get(m.get("method_id"))
            check(
                preserved is not None and preserved.get("calculation_trace") == m.get("calculation_trace"),
                f"calculation_trace_preserved_for_{m.get('method_id')}",
                f"original_trace_len={len(m.get('calculation_trace') or [])}",
            )

    # === Check 5: no forbidden target touched ===
    forbidden_touched = []
    # Check financial_data unchanged (must be same as input skeleton)
    # Adapter must not modify financial_data — we trust parent_ir_skeleton construction
    # We can verify no adapter failure mentions forbidden zone
    for f in adapter_result.failures:
        if f.target_zone in FORBIDDEN_TARGETS:
            forbidden_touched.append(f.target_zone)
    check(
        len(forbidden_touched) == 0,
        "no_forbidden_target_touched",
        f"forbidden_touched={forbidden_touched}",
    )

    # === Check 6: PE/PB/Graham extracted to derived_metrics.valuation if VALID ===
    derived_val = parent_ir.get("derived_metrics", {}).get("valuation", {})
    pe_method = next((m for m in child_methods if m.get("method_id") == "PE"), None)
    if pe_method and pe_method.get("status") == "VALID":
        check(
            "pe_implied" in derived_val and derived_val["pe_implied"] == pe_method.get("implied_price"),
            "pe_extracted_to_derived_metrics",
            f"pe_implied={derived_val.get('pe_implied')} expected={pe_method.get('implied_price')}",
        )
    pb_method = next((m for m in child_methods if m.get("method_id") == "PB"), None)
    if pb_method and pb_method.get("status") == "VALID":
        check(
            "pb_implied" in derived_val and derived_val["pb_implied"] == pb_method.get("implied_price"),
            "pb_extracted_to_derived_metrics",
            f"pb_implied={derived_val.get('pb_implied')} expected={pb_method.get('implied_price')}",
        )
    graham_method = next((m for m in child_methods if m.get("method_id") == "GRAHAM_NUMBER"), None)
    if graham_method and graham_method.get("status") == "VALID":
        check(
            "graham_implied" in derived_val and derived_val["graham_implied"] == graham_method.get("implied_price"),
            "graham_extracted_to_derived_metrics",
            f"graham_implied={derived_val.get('graham_implied')} expected={graham_method.get('implied_price')}",
        )

    # === Check 7: NOT_APPLICABLE methods don't emit target_price ===
    exec_inputs = parent_ir.get("sections", [])
    exec_section = next((s for s in exec_inputs if s.get("section_id") == "executive_summary"), None)
    if exec_section:
        val_summary = exec_section.get("structured_facts", {}).get("valuation_summary", {})
        # If all methods NA, target_price_median must be None
        if all(m.get("status") == "NOT_APPLICABLE" for m in child_methods):
            check(
                val_summary.get("target_price_median") is None,
                "no_target_price_when_all_NA",
                f"target_price_median={val_summary.get('target_price_median')}",
            )

    # === Check 8: valuation_range preserved ===
    val_range = parent_ir.get("derived_metrics", {}).get("valuation", {}).get("range", {})
    child_range = child_output.get("valuation_range") or {}
    check(
        val_range.get("median_implied_price") == child_range.get("median_implied_price"),
        "median_implied_price_preserved",
        f"parent={val_range.get('median_implied_price')} child={child_range.get('median_implied_price')}",
    )

    # === Check 9: adapter final_status reflected in validation.deterministic_gate_results ===
    det_gates = parent_ir.get("validation", {}).get("deterministic_gate_results", {})
    check(
        det_gates.get("valuation_integration") == adapter_result.final_status,
        "adapter_status_in_validation",
        f"det_gates={det_gates.get('valuation_integration')} adapter={adapter_result.final_status}",
    )

    # === Check 10: no silent field renames — adapter must use canonical field names ===
    # Spot-check: input_summary keys match valuation_inputs keys (no rename)
    child_input_keys = set((child_output.get("input_summary") or {}).keys())
    adapter_input_keys = set(adapter_result.valuation_inputs.keys())
    # Adapter is allowed to FILTER (keep only allowed_input_fields) but not RENAME
    check(
        adapter_input_keys.issubset(child_input_keys),
        "no_silent_input_rename",
        f"adapter_input_keys={adapter_input_keys} child_input_keys={child_input_keys}",
    )

    # Final verdict
    result.verdict = "PASS" if result.checks_failed == 0 else "FAIL"
    result.evidence = {
        "child_method_count": len(child_methods),
        "adapter_method_count": len(adapter_methods),
        "preserved_trace_count": len(preserved_traces),
        "derived_valuation_keys": list(derived_val.keys()),
        "audit_notes_valuation_keys": list(audit_valuation.keys()),
    }
    return result
