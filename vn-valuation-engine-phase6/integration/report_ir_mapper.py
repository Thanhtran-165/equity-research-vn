"""Report IR Mapper — embed adapter output zones into parent report-ir.schema.json structure.

Phase 6 P6B. Takes AdapterResult (zones populated by valuation_parent_adapter.adapt())
and embeds them into a parent report IR skeleton conforming to:
  /Users/bobo/.zcode/skills/equity-research-vn/architecture/report-ir.schema.json

Critical rule (Directive Phase 6 §3, §8.4): NEVER touch canonical_financial_DATA,
financial_period_labels, ticker_identity, news_event_clusters, chart_datasets.
Only inject adapter output into allowed zones (derived_metrics.valuation + audit_notes).
"""
from __future__ import annotations
import copy
from typing import Any, Dict, Optional

from integration_version import PARENT_REPORT_IR_VERSION, FORBIDDEN_TARGETS
from valuation_parent_adapter import AdapterResult


# ---------------------------------------------------------------------------
# Map adapter zones → parent IR paths (per report-ir-mapping.yaml)
# ---------------------------------------------------------------------------

# Parent IR target paths (per report-ir-mapping.yaml + report-ir.schema.json)
PARENT_IR_PATHS = {
    "valuation_inputs": "derived_metrics.valuation_inputs",  # NOT in schema yet — write to audit_notes
    "valuation_methods": "sections[valuation].structured_facts.deterministic_table",
    "valuation_results": "derived_metrics.valuation.range",
    "valuation_assumptions": "audit_notes.valuation_assumptions",
    "executive_summary_inputs": "sections[executive_summary].structured_facts.valuation_summary",
    "risks": "sections[risk].structured_facts.valuation_risks",
    "audit_notes": "sections[analyst_notes].structured_facts.valuation_audit",
    "citations": "metadata.source_snapshot_hashes.valuation_inputs",
}


def _get_section(sections, section_id):
    """Find section by id; return None if missing."""
    for s in sections:
        if s.get("section_id") == section_id:
            return s
    return None


def _ensure_section_structured_facts(section, key):
    """Ensure section.structured_facts[key] exists."""
    if "structured_facts" not in section or not isinstance(section["structured_facts"], dict):
        section["structured_facts"] = {}
    if key not in section["structured_facts"]:
        section["structured_facts"][key] = {}
    return section["structured_facts"][key]


def embed_into_parent_ir(
    parent_ir_skeleton: Dict[str, Any],
    adapter_result: AdapterResult,
) -> Dict[str, Any]:
    """Embed adapter zones into a parent IR skeleton.

    Args:
        parent_ir_skeleton: dict conforming to parent report-ir.schema.json.
            This function will NOT modify: financial_data, reporting_scope.annual_periods,
            metadata.ticker, charts (except adding to chart Valuation if missing).
        adapter_result: AdapterResult from valuation_parent_adapter.adapt()

    Returns:
        parent_ir: updated parent IR (deep copy of skeleton + adapter zones embedded).
    """
    parent_ir = copy.deepcopy(parent_ir_skeleton)

    # === NEVER touch forbidden targets ===
    # (We don't write to: financial_data, ticker_identity, charts, news_event_clusters)
    # (We only ADD to: derived_metrics.valuation, audit_notes, sections[valuation] etc.)

    # === derived_metrics.valuation (PE/PB/Graham extension per CONTR-009) ===
    parent_ir.setdefault("derived_metrics", {}).setdefault("valuation", {})

    # Find PE/PB/GRAHAM methods and inject into derived_metrics.valuation
    # These 3 are the ones parent verifier (REQ-025) currently checks.
    for method in adapter_result.valuation_methods:
        mid = method.get("method_id")
        status = method.get("status")
        if status == "VALID" and method.get("implied_price") is not None:
            if mid == "PE":
                parent_ir["derived_metrics"]["valuation"]["pe_implied"] = method.get("implied_price")
            elif mid == "PB":
                parent_ir["derived_metrics"]["valuation"]["pb_implied"] = method.get("implied_price")
            elif mid == "GRAHAM_NUMBER":
                parent_ir["derived_metrics"]["valuation"]["graham_implied"] = method.get("implied_price")

    # === valuation range ===
    parent_ir["derived_metrics"]["valuation"].update({
        "range": adapter_result.valuation_results,
        "median_target": adapter_result.valuation_results.get("median_implied_price"),
        "upside_pct": adapter_result.valuation_results.get("upside_pct_vs_current"),
    })

    # === Full method_results into audit_notes.valuation_methods (lossless preserve) ===
    parent_ir.setdefault("audit_notes", {}).setdefault("valuation", {})
    parent_ir["audit_notes"]["valuation"]["valuation_methods_full"] = adapter_result.valuation_methods
    parent_ir["audit_notes"]["valuation"]["valuation_warnings"] = adapter_result.audit_notes.get("valuation_warnings", [])
    parent_ir["audit_notes"]["valuation"]["valuation_errors"] = adapter_result.audit_notes.get("valuation_errors", [])
    parent_ir["audit_notes"]["valuation"]["peer_set"] = adapter_result.audit_notes.get("peer_set", [])
    parent_ir["audit_notes"]["valuation"]["assumptions_full"] = adapter_result.audit_notes.get("assumptions_full", {})
    parent_ir["audit_notes"]["valuation"]["adapter_mapping_metadata"] = adapter_result.adapter_metadata

    # === Section: valuation ===
    sections = parent_ir.get("sections") or []
    val_section = _get_section(sections, "valuation")
    if val_section is None:
        # Create section
        val_section = {
            "section_id": "valuation",
            "title": "Valuation",
            "applicability": "APPLICABLE",
            "structured_facts": {},
            "narrative": "",
            "warnings": [],
            "validation_status": "PENDING",
        }
        sections.append(val_section)
        parent_ir["sections"] = sections

    deterministic_table = _ensure_section_structured_facts(val_section, "deterministic_table")
    # Compact method summary for parent's deterministic valuation table
    deterministic_table["methods"] = [
        {
            "method_id": m.get("method_id"),
            "status": m.get("status"),
            "formula_id": m.get("formula_id"),
            "benchmark_type": m.get("benchmark_type"),
            "selected_multiple": m.get("selected_multiple"),
            "implied_price": m.get("implied_price"),
            "currency": m.get("currency"),
            "warnings_count": len(m.get("warnings") or []),
            "error_codes": m.get("error_codes") or [],
        }
        for m in adapter_result.valuation_methods
    ]

    # === Section: executive_summary ===
    exec_section = _get_section(sections, "executive_summary")
    if exec_section is not None:
        val_summary = _ensure_section_structured_facts(exec_section, "valuation_summary")
        val_summary.update(adapter_result.executive_summary_inputs)

    # === Section: risk ===
    risk_section = _get_section(sections, "risk")
    if risk_section is not None:
        val_risks = _ensure_section_structured_facts(risk_section, "valuation_risks")
        val_risks["items"] = adapter_result.risks

    # === Section: analyst_notes (audit_notes slot) ===
    audit_section = _get_section(sections, "analyst_notes")
    if audit_section is None:
        audit_section = {
            "section_id": "analyst_notes",
            "title": "Analyst Notes (Audit Trail)",
            "applicability": "APPLICABLE",
            "structured_facts": {},
            "narrative": "",
            "warnings": [],
            "validation_status": "PENDING",
        }
        sections.append(audit_section)
        parent_ir["sections"] = sections
    audit_valuation = _ensure_section_structured_facts(audit_section, "valuation_audit")
    audit_valuation["calculation_traces"] = {
        m.get("method_id"): m.get("calculation_trace")
        for m in adapter_result.valuation_methods
    }
    audit_valuation["equity_bridges"] = {
        m.get("method_id"): {
            "items": m.get("equity_bridge_items"),
            "balanced": m.get("bridge_balanced"),
        }
        for m in adapter_result.valuation_methods if m.get("equity_bridge_items")
    }
    audit_valuation["adapter_mapping_metadata"] = adapter_result.adapter_metadata

    # === Citations → metadata.source_snapshot_hashes.valuation_inputs ===
    metadata = parent_ir.setdefault("metadata", {})
    source_hashes = metadata.setdefault("source_snapshot_hashes", {})
    for c in adapter_result.citations:
        if c.get("content_hash"):
            source_hashes[f"valuation_input.{c.get('metric_id')}"] = c["content_hash"]

    # === Adapter result status → validation.deterministic_gate_results ===
    validation = parent_ir.setdefault("validation", {})
    deterministic_gates = validation.setdefault("deterministic_gate_results", {})
    deterministic_gates["valuation_integration"] = adapter_result.final_status
    if adapter_result.failures:
        deterministic_gates["valuation_integration_failures"] = [
            f.to_dict() for f in adapter_result.failures
        ]

    return parent_ir
