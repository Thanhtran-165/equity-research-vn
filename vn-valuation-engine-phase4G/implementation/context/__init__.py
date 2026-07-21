"""Context Envelope — Phase 4G F4G-B.

Versioned semantic context envelope for vn-valuation-engine.

Architecture (Directive Phase 4G §4.1):
    raw evidence → canonical inputs → registries → semantic context
    → valuation method results → verifier

The context is built BEFORE method results and binds them to:
    - approved methods + applicability decisions
    - benchmarks + premium/discount policies
    - share/EPS basis
    - source registry
    - period/scope alignment
    - error state

The valuation artifact may only REFERENCE the context (via hash), not self-author it.
"""
from .semantic_context import SemanticContext, build_context
from .context_hashing import (
    canonicalize_context, compute_registry_hash,
    compute_evidence_hash, compute_semantic_context_hash,
    verify_semantic_context_hash,
)
from .context_registry import (
    load_all_registries, RegistryBundle,
    CONTEXT_REGISTRY_MISSING, CONTEXT_REGISTRY_SCHEMA_INVALID,
)
from .context_validation import (
    validate_context, SELF_AUTHORED_CONTEXT_DETECTED,
    CONTEXT_CREATED_AFTER_RESULTS, ORPHAN_METHOD_CONTEXT,
)

__all__ = [
    "SemanticContext", "build_context",
    "canonicalize_context", "compute_registry_hash",
    "compute_evidence_hash", "compute_semantic_context_hash",
    "verify_semantic_context_hash",
    "load_all_registries", "RegistryBundle",
    "CONTEXT_REGISTRY_MISSING", "CONTEXT_REGISTRY_SCHEMA_INVALID",
    "validate_context", "SELF_AUTHORED_CONTEXT_DETECTED",
    "CONTEXT_CREATED_AFTER_RESULTS", "ORPHAN_METHOD_CONTEXT",
]
