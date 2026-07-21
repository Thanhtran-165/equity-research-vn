"""Semantic Context — versioned envelope binding valuation results to evidence.

Phase 4G F4G-B §4.3. Schema version 1.0.0.

The context is the AUTHORITY for what valuation results may claim. Method results
must conform to context decisions; context is never self-authored from output.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import datetime as dt


CONTEXT_SCHEMA_VERSION = "1.0.0"


@dataclass
class ApprovedMethod:
    method_id: str
    formula_id: str
    applicability_status: str  # VALID | NOT_APPLICABLE | INPUT_INCOMPLETE | CALCULATION_FAILED | MANUAL_REVIEW_REQUIRED
    applicability_rule_id: str
    permission_to_emit_implied_price: bool


@dataclass
class BenchmarkEntry:
    method_id: str
    benchmark_id: str
    benchmark_type: str  # e.g., PEER_MEDIAN, HISTORICAL_MEDIAN, PEER_MEAN
    selected_value: Optional[float]
    selection_rule_id: str
    premium_discount_policy_id: Optional[str] = None


@dataclass
class ShareContext:
    share_basis: str  # BASIC | DILUTED
    shares_metric_id: str
    EPS_basis: str  # BASIC | DILUTED
    EPS_metric_id: str
    split_adjustment_id: Optional[str] = None


@dataclass
class SourceEntry:
    source_id: str
    source_hash: str
    supported_metric_ids: List[str]
    source_periods: List[str]
    source_scopes: List[str]


@dataclass
class PeriodEntry:
    metric_id: str
    source_period: str
    normalized_period: str
    alignment_decision_id: str


@dataclass
class ScopeEntry:
    metric_id: str
    source_scope: str
    normalized_scope: str
    alignment_decision_id: str


@dataclass
class ErrorState:
    fatal_error_codes: List[str]
    material_warning_codes: List[str]
    error_state_hash: str = ""


@dataclass
class RegistryHashes:
    formula_registry_hash: str = ""
    applicability_registry_hash: str = ""
    benchmark_registry_hash: str = ""
    source_registry_hash: str = ""
    period_registry_hash: str = ""
    scope_registry_hash: str = ""
    error_registry_hash: str = ""


@dataclass
class EvidenceHashes:
    raw_source_hashes: Dict[str, str] = field(default_factory=dict)
    canonical_input_hash: str = ""
    execution_context_hash: str = ""


@dataclass
class SemanticContext:
    """Versioned envelope binding valuation results to evidence + registries.

    Built BEFORE method results. Cannot be self-authored from output.
    """
    context_schema_version: str = CONTEXT_SCHEMA_VERSION
    request_id: str = ""
    generated_at: str = ""
    generated_before_results: bool = True

    # Entity
    ticker: str = ""
    company: str = ""
    exchange: str = ""
    sector: str = ""

    # Valuation context
    valuation_date: str = ""
    reporting_currency: str = "VND"

    # Approved methods + applicability decisions
    approved_methods: List[ApprovedMethod] = field(default_factory=list)

    # Benchmark decisions per method
    benchmarks: List[BenchmarkEntry] = field(default_factory=list)

    # Share/EPS basis contract
    share_context: Optional[ShareContext] = None

    # Source registry
    source_registry: List[SourceEntry] = field(default_factory=list)

    # Period alignment
    period_registry: List[PeriodEntry] = field(default_factory=list)

    # Scope alignment
    scope_registry: List[ScopeEntry] = field(default_factory=list)

    # Error state snapshot from execution
    error_state: Optional[ErrorState] = None

    # Registry hashes (binding to frozen registries)
    registry_hashes: RegistryHashes = field(default_factory=RegistryHashes)

    # Evidence hashes (binding to raw evidence)
    evidence_hashes: EvidenceHashes = field(default_factory=EvidenceHashes)

    # Semantic context hash (computed via canonical serialization)
    semantic_context_hash: str = ""

    # External binding proof (context_builder_version from runner)
    context_builder_version: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Canonical dict representation (sorted, deterministic)."""
        return {
            "context_schema_version": self.context_schema_version,
            "request_id": self.request_id,
            "generated_before_results": self.generated_before_results,
            "entity": {
                "ticker": self.ticker, "company": self.company,
                "exchange": self.exchange, "sector": self.sector,
            },
            "valuation_context": {
                "valuation_date": self.valuation_date,
                "reporting_currency": self.reporting_currency,
            },
            "approved_methods": [
                {"method_id": m.method_id, "formula_id": m.formula_id,
                 "applicability_status": m.applicability_status,
                 "applicability_rule_id": m.applicability_rule_id,
                 "permission_to_emit_implied_price": m.permission_to_emit_implied_price}
                for m in self.approved_methods
            ],
            "benchmarks": [
                {"method_id": b.method_id, "benchmark_id": b.benchmark_id,
                 "benchmark_type": b.benchmark_type, "selected_value": b.selected_value,
                 "selection_rule_id": b.selection_rule_id,
                 "premium_discount_policy_id": b.premium_discount_policy_id}
                for b in self.benchmarks
            ],
            "share_context": (
                {"share_basis": self.share_context.share_basis,
                 "shares_metric_id": self.share_context.shares_metric_id,
                 "EPS_basis": self.share_context.EPS_basis,
                 "EPS_metric_id": self.share_context.EPS_metric_id,
                 "split_adjustment_id": self.share_context.split_adjustment_id}
                if self.share_context else None
            ),
            "source_registry": [
                {"source_id": s.source_id, "source_hash": s.source_hash,
                 "supported_metric_ids": list(s.supported_metric_ids),
                 "source_periods": list(s.source_periods),
                 "source_scopes": list(s.source_scopes)}
                for s in self.source_registry
            ],
            "period_registry": [
                {"metric_id": p.metric_id, "source_period": p.source_period,
                 "normalized_period": p.normalized_period,
                 "alignment_decision_id": p.alignment_decision_id}
                for p in self.period_registry
            ],
            "scope_registry": [
                {"metric_id": s.metric_id, "source_scope": s.source_scope,
                 "normalized_scope": s.normalized_scope,
                 "alignment_decision_id": s.alignment_decision_id}
                for s in self.scope_registry
            ],
            "error_state": (
                {"fatal_error_codes": list(self.error_state.fatal_error_codes),
                 "material_warning_codes": list(self.error_state.material_warning_codes),
                 "error_state_hash": self.error_state.error_state_hash}
                if self.error_state else None
            ),
            "registry_hashes": {
                "formula_registry_hash": self.registry_hashes.formula_registry_hash,
                "applicability_registry_hash": self.registry_hashes.applicability_registry_hash,
                "benchmark_registry_hash": self.registry_hashes.benchmark_registry_hash,
                "source_registry_hash": self.registry_hashes.source_registry_hash,
                "period_registry_hash": self.registry_hashes.period_registry_hash,
                "scope_registry_hash": self.registry_hashes.scope_registry_hash,
                "error_registry_hash": self.registry_hashes.error_registry_hash,
            },
            "evidence_hashes": {
                "raw_source_hashes": dict(self.evidence_hashes.raw_source_hashes),
                "canonical_input_hash": self.evidence_hashes.canonical_input_hash,
                "execution_context_hash": self.evidence_hashes.execution_context_hash,
            },
            "context_builder_version": self.context_builder_version,
            # NOTE: semantic_context_hash is computed AFTER serialization (excluded from its own hash)
        }


def build_context(
    *,
    request_id: str,
    entity: Dict[str, str],
    valuation_date: str,
    reporting_currency: str,
    approved_methods: List[ApprovedMethod],
    benchmarks: List[BenchmarkEntry],
    share_context: Optional[ShareContext],
    source_registry: List[SourceEntry],
    period_registry: List[PeriodEntry],
    scope_registry: List[ScopeEntry],
    error_state: ErrorState,
    registry_hashes: RegistryHashes,
    evidence_hashes: EvidenceHashes,
    context_builder_version: str,
) -> SemanticContext:
    """Build a semantic context (must be called BEFORE method results).

    Computes semantic_context_hash via canonical serialization.
    """
    import hashlib, json
    from .context_hashing import compute_semantic_context_hash

    ctx = SemanticContext(
        request_id=request_id,
        generated_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        generated_before_results=True,
        ticker=entity.get("ticker", ""),
        company=entity.get("company", ""),
        exchange=entity.get("exchange", "HOSE"),
        sector=entity.get("sector", ""),
        valuation_date=valuation_date,
        reporting_currency=reporting_currency,
        approved_methods=approved_methods,
        benchmarks=benchmarks,
        share_context=share_context,
        source_registry=source_registry,
        period_registry=period_registry,
        scope_registry=scope_registry,
        error_state=error_state,
        registry_hashes=registry_hashes,
        evidence_hashes=evidence_hashes,
        context_builder_version=context_builder_version,
    )
    # Compute the semantic_context_hash
    ctx.semantic_context_hash = compute_semantic_context_hash(ctx.to_dict())
    return ctx
