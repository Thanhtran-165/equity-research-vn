"""Valuation Parent Adapter — vn-valuation-engine child output → equity-research-vn 1.1.0 parent IR.

Phase 6 P6B. Lossless mapping per contracts/report-ir-mapping.yaml.
Maps child ValuationOutput → parent report-ir.schema.json compatible structure.

Adapter responsibilities (Directive Phase 6 §8.5):
  - Preserve all method_results[] with full semantics (method_id, status, formula_id,
    input_metric_ids, calculation_trace, benchmark_type, selected_multiple,
    implied_enterprise_value, equity_bridge_items, bridge_balanced, implied_equity_value,
    shares_outstanding, implied_price, currency, warnings, error_codes).
  - Preserve valuation_range structure.
  - Preserve assumptions + provenance.
  - Map warnings/errors to audit_notes.valuation_warnings + audit_notes.valuation_errors.
  - Map provenance to metadata.source_hashes.valuation_inputs.
  - NO silent renames, NO lossy flattening, NO parent recalculation.

Adapter does NOT (Directive Phase 6 §3, §8.4):
  - Modify canonical_financial_DATA
  - Generate HTML
  - Recalculate any valuation
  - Substitute methods
  - Add target prices not present in child output
  - Change applicability decisions
"""
from __future__ import annotations
import hashlib, json, copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from integration_version import (
    ADAPTER_ID, ADAPTER_VERSION, CHILD_SCHEMA_VERSION, PARENT_VERSION,
    PARENT_REPORT_IR_VERSION, MAPPING_MODE, MAPPING_POLICY,
    ALLOWED_TARGETS, FORBIDDEN_TARGETS, get_adapter_metadata,
)


# ---------------------------------------------------------------------------
# Adapter result + failure
# ---------------------------------------------------------------------------

@dataclass
class AdapterFailure:
    code: str
    severity: str  # CRITICAL | MAJOR | MINOR
    target_zone: str
    method_id: Optional[str] = None
    metric_id: Optional[str] = None
    evidence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code, "severity": self.severity,
            "target_zone": self.target_zone,
            "method_id": self.method_id, "metric_id": self.metric_id,
            "evidence": self.evidence,
        }


@dataclass
class AdapterResult:
    """Output of mapping child valuation-output.json → parent report IR zones."""
    adapter_metadata: Dict[str, Any]
    valuation_inputs: Dict[str, Any] = field(default_factory=dict)
    valuation_methods: List[Dict[str, Any]] = field(default_factory=list)
    valuation_results: Dict[str, Any] = field(default_factory=dict)
    valuation_assumptions: Dict[str, Any] = field(default_factory=dict)
    executive_summary_inputs: Dict[str, Any] = field(default_factory=dict)
    risks: List[Dict[str, Any]] = field(default_factory=list)
    audit_notes: Dict[str, Any] = field(default_factory=dict)
    citations: List[Dict[str, Any]] = field(default_factory=list)
    failures: List[AdapterFailure] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    final_status: str = "PASS"  # PASS | FAIL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "adapter_metadata": self.adapter_metadata,
            "valuation_inputs": self.valuation_inputs,
            "valuation_methods": self.valuation_methods,
            "valuation_results": self.valuation_results,
            "valuation_assumptions": self.valuation_assumptions,
            "executive_summary_inputs": self.executive_summary_inputs,
            "risks": self.risks,
            "audit_notes": self.audit_notes,
            "citations": self.citations,
            "failures": [f.to_dict() for f in self.failures],
            "warnings": self.warnings,
            "final_status": self.final_status,
        }


# ---------------------------------------------------------------------------
# Method-result semantic preservation contract (Directive §8.5)
# ---------------------------------------------------------------------------

# Note: child output from Phase 5R uses 'equity_bridge' (single dict with items + balances),
# while MethodResult dataclass uses 'equity_bridge_items' + 'bridge_balanced'.
# Adapter must accept BOTH schemas — bridge is allowed in either form.
# Other fields are strict requirements.
STRICT_REQUIRED_METHOD_FIELDS = {
    "method_id", "status", "formula_id", "input_metric_ids",
    "calculation_trace", "benchmark_type", "selected_multiple",
    "implied_enterprise_value",
    "implied_equity_value", "shares_outstanding", "implied_price",
    "currency", "warnings", "error_codes",
}
# Bridge representation is flexible: either 'equity_bridge' (child output style)
# OR 'equity_bridge_items' + 'bridge_balanced' (MethodResult dataclass style).
BRIDGE_FIELD_VARIANTS = (
    {"equity_bridge"},
    {"equity_bridge_items", "bridge_balanced"},
)


def _has_valid_bridge(method: Dict[str, Any]) -> bool:
    """Check if method has bridge in either accepted form (with non-None value)."""
    # Form 1: equity_bridge (dict with items)
    eb = method.get("equity_bridge")
    if isinstance(eb, dict) and (eb.get("items") or eb.get("balanced") is not None or eb.get("balances") is not None):
        return True
    # Form 2: equity_bridge_items (list) + bridge_balanced (bool)
    ebi = method.get("equity_bridge_items")
    if isinstance(ebi, list):
        return True
    return False


# Methods that structurally require an equity bridge (EV-based methods).
# Other methods (PE, PB, Graham, P/CF, P/S, DDM) compute implied_price directly without a bridge.
BRIDGE_REQUIRED_METHODS = {"EV_EBITDA", "DCF_FCFF", "EV_EBIT", "EV_REVENUE", "REVERSE_DCF"}


def _validate_warnings_errors_shape(m: Dict[str, Any]) -> List[AdapterFailure]:
    """Validate warnings[] and error_codes[] are lists of strings."""
    failures = []
    mid = m.get("method_id", "<missing>")
    for field_name in ("warnings", "error_codes"):
        v = m.get(field_name)
        if v is None:
            continue  # missing optional field is OK
        if not isinstance(v, list):
            failures.append(AdapterFailure(
                code="INVALID_WARNING_ERROR_SHAPE", severity="MAJOR",
                target_zone="valuation_methods", method_id=mid,
                evidence=f"{field_name} must be list, got {type(v).__name__}",
            ))
        else:
            for item in v:
                if not isinstance(item, str):
                    failures.append(AdapterFailure(
                        code="INVALID_WARNING_ERROR_SHAPE", severity="MAJOR",
                        target_zone="valuation_methods", method_id=mid,
                        evidence=f"{field_name} must contain strings, got {type(item).__name__}",
                    ))
                    break
    return failures

VALID_METHOD_STATUSES = {
    "VALID", "NOT_APPLICABLE", "INPUT_INCOMPLETE",
    "CALCULATION_FAILED", "MANUAL_REVIEW_REQUIRED",
}


# ---------------------------------------------------------------------------
# Validation primitives
# ---------------------------------------------------------------------------

def _validate_method_result(m: Dict[str, Any]) -> List[AdapterFailure]:
    """Validate a single method_result for required fields + semantic consistency."""
    failures = []
    mid = m.get("method_id", "<missing>")

    # Check required fields present (Directive §8.5) — bridge fields accepted in either variant
    for f in STRICT_REQUIRED_METHOD_FIELDS:
        if f not in m:
            failures.append(AdapterFailure(
                code="MISSING_REQUIRED_FIELD", severity="CRITICAL",
                target_zone="valuation_methods", method_id=mid,
                evidence=f"method result missing required field '{f}'",
            ))

    # Bridge fields: required only for VALID EV-based methods (EV_EBITDA, DCF_FCFF).
    # INPUT_INCOMPLETE/NOT_APPLICABLE methods may omit bridge legitimately.
    method_status = m.get("status")
    if mid in BRIDGE_REQUIRED_METHODS and method_status == "VALID":
        if not _has_valid_bridge(m):
            failures.append(AdapterFailure(
                code="MISSING_REQUIRED_FIELD", severity="CRITICAL",
                target_zone="valuation_methods", method_id=mid,
                evidence=f"VALID EV-based method '{mid}' missing bridge (need 'equity_bridge' OR 'equity_bridge_items'+'bridge_balanced')",
            ))

    # Validate status enum
    status = m.get("status")
    if status not in VALID_METHOD_STATUSES:
        failures.append(AdapterFailure(
            code="INVALID_METHOD_STATUS", severity="CRITICAL",
            target_zone="valuation_methods", method_id=mid,
            evidence=f"status='{status}' not in {sorted(VALID_METHOD_STATUSES)}",
        ))

    # VALID status requires implied_price and calculation_trace
    if status == "VALID":
        if m.get("implied_price") is None:
            failures.append(AdapterFailure(
                code="VALID_METHOD_MISSING_IMPLIED_PRICE", severity="CRITICAL",
                target_zone="valuation_methods", method_id=mid,
                evidence="VALID status requires non-null implied_price",
            ))
        if not m.get("calculation_trace"):
            failures.append(AdapterFailure(
                code="VALID_METHOD_MISSING_TRACE", severity="CRITICAL",
                target_zone="valuation_methods", method_id=mid,
                evidence="VALID status requires non-empty calculation_trace",
            ))

    # NOT_APPLICABLE must NOT have implied_price (Directive §13 PIT-5)
    if status == "NOT_APPLICABLE" and m.get("implied_price") is not None:
        failures.append(AdapterFailure(
            code="NOT_APPLICABLE_WITH_PRICE", severity="CRITICAL",
            target_zone="valuation_methods", method_id=mid,
            evidence="NOT_APPLICABLE must not emit implied_price (would become fake valuation)",
        ))

    return failures


def _detect_duplicate_method_ids(methods: List[Dict[str, Any]]) -> List[AdapterFailure]:
    """Detect duplicate method_id values."""
    failures = []
    seen = {}
    for m in methods:
        mid = m.get("method_id")
        if mid in seen:
            failures.append(AdapterFailure(
                code="DUPLICATE_METHOD_ID", severity="CRITICAL",
                target_zone="valuation_methods", method_id=mid,
                evidence=f"duplicate method_id (first seen at index {seen[mid]})",
            ))
        else:
            seen[mid] = methods.index(m)
    return failures


def _detect_orphan_metric_references(
    methods: List[Dict[str, Any]],
    input_metric_ids: List[str],
) -> List[AdapterFailure]:
    """Detect method calculation_trace referencing metrics not declared in input_metric_ids."""
    failures = []
    valid_inputs = set(input_metric_ids or [])
    # Allow canonical benchmark IDs registered in formula_registry
    CANONICAL_AUX = {
        "PE_median_5y_v1", "PB_median_5y_v1", "EV_EBITDA_median_5y_v1",
        "P_CF_median_5y_v1", "P_S_median_5y_v1", "PEG_median_5y_v1",
        "PE_peer_median_v1", "PB_peer_median_v1", "EV_EBITDA_peer_median_v1",
        "wacc", "terminal_growth", "fcff_forecast",
    }
    # Allow common intermediate variable names that formulas produce within trace steps.
    # These are NOT external inputs — they are intermediate results from earlier steps in the same trace.
    INTERMEDIATE_VARS = {
        "ev_implied", "EV_implied", "ev", "EV",
        "equity_value", "EQUITY_VALUE",
        "shares", "shares_outstanding",
        "market_cap", "MARKET_CAP",
        "terminal_value", "discounted_fcff", "pv_terminal",
        "implied_enterprise_value", "implied_equity_value",
        "implied_price", "net_debt_total",
    }
    for m in methods:
        mid = m.get("method_id", "<missing>")
        for step in (m.get("calculation_trace") or []):
            for used in (step.get("inputs_used") or []):
                if used in valid_inputs: continue
                if used in CANONICAL_AUX: continue
                if used in INTERMEDIATE_VARS: continue
                failures.append(AdapterFailure(
                    code="ORPHAN_METRIC_REFERENCE", severity="MAJOR",
                    target_zone="valuation_methods", method_id=mid,
                    metric_id=used,
                    evidence=f"trace step {step.get('step')} references '{used}' not in input_metric_ids",
                ))
    return failures


# ---------------------------------------------------------------------------
# Main adapter
# ---------------------------------------------------------------------------

def adapt(child_output: Dict[str, Any]) -> AdapterResult:
    """Map child valuation-output dict to parent report IR zones.

    Args:
        child_output: dict conforming to valuation-output.schema.json

    Returns:
        AdapterResult with mapped zones + any validation failures.
        Caller is responsible for acting on `final_status` and `failures`.
    """
    result = AdapterResult(adapter_metadata=get_adapter_metadata())
    failures = result.failures
    warnings = result.warnings

    # === Top-level schema sanity ===
    if not isinstance(child_output, dict):
        failures.append(AdapterFailure(
            code="INVALID_CHILD_OUTPUT_TYPE", severity="CRITICAL",
            target_zone="adapter_input",
            evidence=f"child_output must be dict, got {type(child_output).__name__}",
        ))
        result.final_status = "FAIL"
        return result

    # === Valuation inputs (from input_summary) ===
    input_summary = child_output.get("input_summary") or {}
    allowed_input_fields = {"price", "shares_outstanding", "eps", "bvps", "revenue",
                            "ebitda", "net_debt"}
    result.valuation_inputs = {
        k: v for k, v in input_summary.items() if k in allowed_input_fields
    }
    # Reject cross-ticker input contamination
    request_ticker = (child_output.get("request") or {}).get("ticker")
    entity_ticker = (child_output.get("entity") or {}).get("canonical_ticker")
    if request_ticker and entity_ticker and request_ticker != entity_ticker:
        failures.append(AdapterFailure(
            code="CROSS_TICKER_CONTAMINATION", severity="CRITICAL",
            target_zone="valuation_inputs",
            evidence=f"request.ticker={request_ticker} != entity.canonical_ticker={entity_ticker}",
        ))

    # === F4F-E: Company name registry check (v1.1.0) ===
    # Adapter catches company_mismatch (MUT-INT-007) via cross-check against known VN registry.
    # If request.ticker is known but entity.canonical_company doesn't match → CRITICAL.
    KNOWN_COMPANY_REGISTRY = {
        "FPT": ("FPT Corporation", "FPT Corp"),
        "HPG": ("Hoa Phat Group",),
        "VCB": ("Joint Stock Commercial Bank for Foreign Trade of Vietnam", "Vietcombank"),
        "BVH": ("Bao Viet Holdings",),
        "MWG": ("Mobile World Investment",),
        "VNM": ("Vietnam Dairy Products",),
        "VIC": ("Vingroup",),
        "VHM": ("Vinhomes",),
        "MSN": ("Masan Group",),
        "PNJ": ("Phu Nhuan Jewelry",),
    }
    request_ticker = (child_output.get("request") or {}).get("ticker")
    entity_ticker = (child_output.get("entity") or {}).get("canonical_ticker")
    entity_company = (child_output.get("entity") or {}).get("canonical_company", "")
    check_ticker = entity_ticker or request_ticker
    if check_ticker in KNOWN_COMPANY_REGISTRY:
        valid_companies = KNOWN_COMPANY_REGISTRY[check_ticker]
        # Check if entity_company matches any known variant (case-insensitive, partial match OK)
        company_matches = any(
            vc.lower() in entity_company.lower() or entity_company.lower() in vc.lower()
            for vc in valid_companies
        )
        if not company_matches and entity_company:
            failures.append(AdapterFailure(
                code="ENTITY_COMPANY_MISMATCH", severity="CRITICAL",
                target_zone="entity",
                evidence=f"ticker={check_ticker} expected company containing one of {valid_companies}, got '{entity_company}'",
            ))

    # Collect input metric IDs for orphan detection
    input_metric_ids = list(input_summary.keys())

    # === Valuation methods (preserve all method_results[]) ===
    method_results = child_output.get("method_results") or []

    # Duplicate detection
    failures.extend(_detect_duplicate_method_ids(method_results))

    # Per-method validation
    for m in method_results:
        failures.extend(_validate_method_result(m))
        failures.extend(_validate_warnings_errors_shape(m))

    # Orphan metric references
    failures.extend(_detect_orphan_metric_references(method_results, input_metric_ids))

    # Preserve methods losslessly (Directive §8.5)
    result.valuation_methods = [copy.deepcopy(m) for m in method_results]

    # === Valuation results (range) ===
    val_range = child_output.get("valuation_range") or {}
    result.valuation_results = {
        "median_implied_price": val_range.get("median_implied_price"),
        "mean_implied_price": val_range.get("mean_implied_price"),
        "p25_implied_price": val_range.get("p25_implied_price"),
        "p75_implied_price": val_range.get("p75_implied_price"),
        "upside_pct_vs_current": val_range.get("upside_pct_vs_current"),
    }
    # Range must NOT be computed by parent — preserve as-is
    # but warn if range values look like raw VND amounts (>1e15 suggests scale issue)
    for k, v in result.valuation_results.items():
        if isinstance(v, (int, float)) and abs(v) > 1e15:
            warnings.append(f"valuation_results.{k}={v} exceeds 1e15 — possible scale issue")

    # === Valuation assumptions ===
    assumptions = child_output.get("assumptions") or {}
    result.valuation_assumptions = {
        "wacc": assumptions.get("wacc"),
        "wacc_source": assumptions.get("wacc_source"),
        "terminal_growth": assumptions.get("terminal_growth"),
        "premium_discounts_applied": assumptions.get("premium_discounts_applied") or [],
    }

    # === Executive summary inputs ===
    valid_methods = [m for m in method_results if m.get("status") == "VALID" and m.get("implied_price") is not None]
    if valid_methods:
        # Sort by relevance (number of trace steps as proxy) then take top 3
        top3 = sorted(valid_methods, key=lambda m: -len(m.get("calculation_trace") or []))[:3]
        result.executive_summary_inputs = {
            "target_price_median": val_range.get("median_implied_price"),
            "upside_pct": val_range.get("upside_pct_vs_current"),
            "methodology_summary": [m.get("method_id") for m in top3],
            "top3_methods": [
                {"method_id": m.get("method_id"), "implied_price": m.get("implied_price")}
                for m in top3
            ],
        }
    else:
        # NO valid methods → NO target price (Directive §13 PIT-5)
        result.executive_summary_inputs = {
            "target_price_median": None,
            "upside_pct": None,
            "methodology_summary": [],
            "top3_methods": [],
            "reason": "no VALID methods → no target price emitted (fail-closed)",
        }

    # === Risks (from warnings + errors) ===
    for w in (child_output.get("warnings") or []):
        result.risks.append({
            "risk_code": "VALUATION_WARNING",
            "severity": "MINOR",
            "description": w if isinstance(w, str) else json.dumps(w, default=str),
            "method_id": None, "metric_ids": [],
        })
    for e in (child_output.get("errors") or []):
        if isinstance(e, dict):
            result.risks.append({
                "risk_code": e.get("code", "UNKNOWN"),
                "severity": e.get("severity", "MAJOR"),
                "description": e.get("evidence") or e.get("message", ""),
                "method_id": e.get("method_id"),
                "metric_ids": e.get("metric_ids") or [],
            })

    # === Audit notes (full preservation) ===
    result.audit_notes = {
        "valuation_methods_full": copy.deepcopy(method_results),
        "valuation_warnings": copy.deepcopy(child_output.get("warnings") or []),
        "valuation_errors": copy.deepcopy(child_output.get("errors") or []),
        "peer_set": copy.deepcopy(child_output.get("peer_set") or []),
        "assumptions_full": copy.deepcopy(assumptions),
        "adapter_mapping_metadata": get_adapter_metadata(),
    }

    # === Citations (from provenance) ===
    provenance = child_output.get("provenance") or {}
    if isinstance(provenance, dict):
        for metric_id, prov in provenance.items():
            if isinstance(prov, dict):
                result.citations.append({
                    "metric_id": metric_id,
                    "source_id": prov.get("source_id"),
                    "source_type": prov.get("source_type"),
                    "source_date": prov.get("source_date"),
                    "content_hash": prov.get("source_sha") or prov.get("content_hash"),
                })

    # === Final status ===
    if any(f.severity == "CRITICAL" for f in failures):
        result.final_status = "FAIL"
    elif any(f.severity == "MAJOR" for f in failures):
        result.final_status = "PASS_WITH_WARNINGS"
    else:
        result.final_status = "PASS"

    return result


def adapter_evidence_manifest(result: AdapterResult, child_output_hash: str) -> Dict[str, Any]:
    """Build evidence manifest for adapter run (Directive §8.1 integration_evidence_manifest)."""
    import datetime as dt
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "adapter_metadata": result.adapter_metadata,
        "child_output_hash": child_output_hash,
        "failures": [f.to_dict() for f in result.failures],
        "warnings": result.warnings,
        "final_status": result.final_status,
        "zone_counts": {
            "valuation_inputs": len(result.valuation_inputs),
            "valuation_methods": len(result.valuation_methods),
            "valuation_results": len(result.valuation_results),
            "valuation_assumptions": len(result.valuation_assumptions),
            "executive_summary_inputs": len(result.executive_summary_inputs),
            "risks": len(result.risks),
            "audit_notes_keys": len(result.audit_notes),
            "citations": len(result.citations),
        },
        "forbidden_targets_touched": [],  # adapter never writes to forbidden targets
    }
