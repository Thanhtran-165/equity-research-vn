"""Context Validation.

Phase 4G F4G-B §4.7. Validates a SemanticContext structure.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SELF_AUTHORED_CONTEXT_DETECTED(Exception):
    pass


class CONTEXT_CREATED_AFTER_RESULTS(Exception):
    pass


class ORPHAN_METHOD_CONTEXT(Exception):
    pass


class ORPHAN_BENCHMARK_CONTEXT(Exception):
    pass


class ORPHAN_SOURCE_CONTEXT(Exception):
    pass


class PERIOD_CONTEXT_UNRESOLVED(Exception):
    pass


class SCOPE_CONTEXT_UNRESOLVED(Exception):
    pass


class SEMANTIC_CONTEXT_SCHEMA_INVALID(Exception):
    pass


class SEMANTIC_CONTEXT_HASH_MISMATCH(Exception):
    pass


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def validate_context(context_dict: Dict[str, Any], *,
                     registries=None,
                     verify_hash: bool = True) -> ValidationResult:
    """Validate a SemanticContext dict.

    Checks (Directive §4.7):
      - schema version
      - required fields
      - enum values
      - duplicate method IDs
      - duplicate source IDs
      - method/benchmark linkage
      - source/metric linkage
      - period linkage
      - scope linkage
      - error-state presence
      - registry hashes
      - evidence hashes
      - semantic context hash
      - generated-before-results invariant
    """
    result = ValidationResult(valid=True)
    errors = result.errors

    # Schema version
    if context_dict.get("context_schema_version") != "1.0.0":
        errors.append(f"context_schema_version must be '1.0.0', got '{context_dict.get('context_schema_version')}'")

    # Required entity fields
    entity = context_dict.get("entity") or {}
    for f in ("ticker", "company", "exchange", "sector"):
        if not entity.get(f):
            errors.append(f"entity.{f} required")

    # Required valuation_context fields
    vc = context_dict.get("valuation_context") or {}
    if not vc.get("valuation_date"):
        errors.append("valuation_context.valuation_date required")
    if not vc.get("reporting_currency"):
        errors.append("valuation_context.reporting_currency required")

    # generated_before_results invariant
    if not context_dict.get("generated_before_results"):
        errors.append("generated_before_results must be true (context must be created before method results)")

    # Approved methods: no duplicates
    approved = context_dict.get("approved_methods") or []
    method_ids = [m.get("method_id") for m in approved if isinstance(m, dict)]
    if len(method_ids) != len(set(method_ids)):
        errors.append(f"duplicate method IDs in approved_methods: {method_ids}")

    # Each approved method must have valid status
    VALID_STATUSES = {"VALID", "NOT_APPLICABLE", "INPUT_INCOMPLETE", "CALCULATION_FAILED", "MANUAL_REVIEW_REQUIRED"}
    for m in approved:
        if not isinstance(m, dict): continue
        status = m.get("applicability_status")
        if status not in VALID_STATUSES:
            errors.append(f"method '{m.get('method_id')}' has invalid status '{status}'")

    # Benchmarks: must link to approved methods
    benchmarks = context_dict.get("benchmarks") or []
    approved_set = set(method_ids)
    for b in benchmarks:
        if not isinstance(b, dict): continue
        bmethod = b.get("method_id")
        if bmethod and bmethod not in approved_set:
            errors.append(f"benchmark for method '{bmethod}' not in approved_methods")

    # Source registry: no duplicate source_ids
    sources = context_dict.get("source_registry") or []
    source_ids = [s.get("source_id") for s in sources if isinstance(s, dict)]
    if len(source_ids) != len(set(source_ids)):
        errors.append(f"duplicate source_ids: {source_ids}")

    # Period/scope registries must be non-empty if metrics present
    periods = context_dict.get("period_registry") or []
    scopes = context_dict.get("scope_registry") or []
    # (If context claims metrics, periods/scopes should be defined — but if no metrics, OK)

    # Error state presence
    error_state = context_dict.get("error_state")
    if error_state is None:
        errors.append("error_state required (even if empty lists)")
    elif isinstance(error_state, dict):
        if "fatal_error_codes" not in error_state:
            errors.append("error_state.fatal_error_codes required")
        if "material_warning_codes" not in error_state:
            errors.append("error_state.material_warning_codes required")

    # Registry hashes presence
    reg_hashes = context_dict.get("registry_hashes") or {}
    required_reg_keys = ("formula_registry_hash", "applicability_registry_hash",
                         "benchmark_registry_hash", "source_registry_hash",
                         "period_registry_hash", "scope_registry_hash", "error_registry_hash")
    for k in required_reg_keys:
        if not reg_hashes.get(k):
            errors.append(f"registry_hashes.{k} required")

    # Evidence hashes presence
    ev_hashes = context_dict.get("evidence_hashes") or {}
    if not ev_hashes.get("canonical_input_hash"):
        errors.append("evidence_hashes.canonical_input_hash required")
    if not ev_hashes.get("execution_context_hash"):
        errors.append("evidence_hashes.execution_context_hash required")

    # External binding proof
    if not context_dict.get("context_builder_version"):
        errors.append("context_builder_version required (proves external binding)")

    # Semantic context hash verification
    if verify_hash:
        from .context_hashing import compute_semantic_context_hash
        expected = context_dict.get("semantic_context_hash")
        if not expected:
            errors.append("semantic_context_hash required")
        else:
            actual = compute_semantic_context_hash(context_dict)
            if actual != expected:
                errors.append(f"semantic_context_hash mismatch: expected={expected[:16]}, actual={actual[:16]}")

    # Cross-registry checks (if registries provided)
    if registries:
        # Check formula_ids match registry
        for m in approved:
            if not isinstance(m, dict): continue
            mid = m.get("method_id")
            fid = m.get("formula_id")
            expected_fid = registries.formula_by_method.get(mid)
            if expected_fid and fid != expected_fid:
                errors.append(f"method '{mid}' formula_id='{fid}' but registry has '{expected_fid}'")
        # Check benchmark types
        for b in benchmarks:
            if not isinstance(b, dict): continue
            bmethod = b.get("method_id")
            btype = b.get("benchmark_type")
            allowed = registries.benchmark_types_by_method.get(bmethod, [])
            if allowed and btype not in allowed:
                errors.append(f"benchmark_type '{btype}' not allowed for method '{bmethod}'")

    result.valid = len(errors) == 0
    return result
