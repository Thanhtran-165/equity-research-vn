"""Canonical Hashing for Semantic Context.

Phase 4G F4G-B §4.4. All hashes use SHA-256 over canonical JSON serialization.
Key order is sorted; timestamps and runtime fields are excluded.
"""
from __future__ import annotations
import hashlib, json
from typing import Any, Dict


def canonicalize_context(context_dict: Dict[str, Any]) -> str:
    """Canonical JSON serialization of a context dict.

    Rules (Directive §4.4):
      - key_order: sorted (recursively)
      - whitespace: normalized (compact separators)
      - timestamps_excluded: True (generated_at removed)
      - runtime_fields_excluded: True (request_id stays — it's semantic)
      - logical_run_id_excluded_if_nonsemantic: True

    The semantic_context_hash field is excluded (it's computed from the rest).
    """
    # Deep copy to avoid mutating input
    ctx = json.loads(json.dumps(context_dict, default=str))

    # Exclude non-semantic fields
    ctx.pop("generated_at", None)  # timestamp
    ctx.pop("semantic_context_hash", None)  # computed field (circular)

    # Recursive sort_keys via json.dumps
    return json.dumps(ctx, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_semantic_context_hash(context_dict: Dict[str, Any]) -> str:
    """Compute SHA-256 hash of canonical context representation."""
    canonical = canonicalize_context(context_dict)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_semantic_context_hash(context_dict: Dict[str, Any], expected_hash: str) -> bool:
    """Verify that context's semantic_context_hash matches computed hash."""
    actual = compute_semantic_context_hash(context_dict)
    return actual == expected_hash


def compute_registry_hash(registry_dict: Dict[str, Any]) -> str:
    """Compute SHA-256 hash of a registry dict (canonical form)."""
    canonical = json.dumps(registry_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_evidence_hash(evidence_dict: Dict[str, Any]) -> str:
    """Compute SHA-256 hash of an evidence dict (canonical form)."""
    canonical = json.dumps(evidence_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_method_result_hash(method_result: Dict[str, Any]) -> str:
    """Hash a method result for pre/post comparison (excludes runtime fields)."""
    mr = json.loads(json.dumps(method_result, default=str))
    # Exclude runtime/transient fields
    for k in ("started_at", "completed_at", "duration_ms"):
        mr.pop(k, None)
    canonical = json.dumps(mr, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_calculation_trace_hash(trace: list) -> str:
    """Hash a calculation trace for pre/post comparison."""
    canonical = json.dumps(trace, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
