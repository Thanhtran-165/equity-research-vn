"""Canonical models for vn-fundamental-analysis Phase 4R.

Phase 4R extends Phase 4 models with structural identity bindings:
- Per-value bindings on MetricInput (share_basis / period_kind / reporting_scope /
  attribution_scope / denominator_basis / source_metric_ids / corporate-action trace).
- ApplicabilityDecision: immutable per-metric status decision with required_inputs.
- ProvenanceRecord: source chain binding for every material metric.

These additions are additive and backward-compatible with Phase 4 fixtures:
legacy MetricInput without explicit bindings defaults to canonical-conservative
values (weighted-average basic shares, annual period, consolidated scope,
attributable-to-parent attribution, average denominator) at normalization time
and the runner records STRUCTURAL_BINDING_DEFAULTED so the verifier can
distinguish an explicit binding from a defaulted one.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class MetricStatus(str, Enum):
    VALID = "VALID"
    VALID_NEGATIVE = "VALID_NEGATIVE"
    INPUT_INCOMPLETE = "INPUT_INCOMPLETE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    ERROR = "ERROR"


class PeriodType(str, Enum):
    ANNUAL = "ANNUAL"
    QUARTERLY = "QUARTERLY"
    TTM = "TTM"
    YTD = "YTD"
    POINT_IN_TIME = "POINT_IN_TIME"


# Alias used by policies; identical semantics to PeriodType.
PeriodKind = PeriodType


class Scope(str, Enum):
    CONSOLIDATED = "CONSOLIDATED"
    STANDALONE = "STANDALONE"
    ATTRIBUTABLE_TO_PARENT = "ATTRIBUTABLE_TO_PARENT"
    TOTAL_GROUP = "TOTAL_GROUP"


# P4R splits Scope into two orthogonal axes (/ ).
class ReportingScope(str, Enum):
    """Consolidation axis: whole group or just the parent entity."""
    CONSOLIDATED = "CONSOLIDATED"
    STANDALONE = "STANDALONE"


class AttributionScope(str, Enum):
    """Attribution axis: attributable to parent shareholders or to the total group."""
    ATTRIBUTABLE_TO_PARENT = "ATTRIBUTABLE_TO_PARENT"
    TOTAL_GROUP = "TOTAL_GROUP"


class ShareBasis(str, Enum):
    """Identity of a share count used as denominator for per-share metrics."""
    WEIGHTED_AVERAGE_BASIC = "WEIGHTED_AVERAGE_BASIC"
    WEIGHTED_AVERAGE_DILUTED = "WEIGHTED_AVERAGE_DILUTED"
    PERIOD_END_BASIC = "PERIOD_END_BASIC"
    PERIOD_END_DILUTED = "PERIOD_END_DILUTED"
    SPLIT_ADJUSTED_HISTORICAL = "SPLIT_ADJUSTED_HISTORICAL"


class DenominatorBasis(str, Enum):
    """Identity of a balance-sheet figure used as a ratio denominator."""
    AVERAGE_COMMON_EQUITY = "AVERAGE_COMMON_EQUITY"
    ENDING_COMMON_EQUITY = "ENDING_COMMON_EQUITY"
    AVERAGE_TOTAL_ASSETS = "AVERAGE_TOTAL_ASSETS"
    ENDING_TOTAL_ASSETS = "ENDING_TOTAL_ASSETS"
    AVERAGE_REVENUE = "AVERAGE_REVENUE"


@dataclass
class ProvenanceRecord:
    """Per-metric source chain binding.

    Resolves metric_result -> formula_inputs -> normalized_inputs ->
    collector_metric_id -> source_id -> raw_evidence.
    """
    source_id: str = ""
    source_date: str = ""
    source_type: str = ""
    collector_metric_id: str = ""
    normalized_input_ids: List[str] = field(default_factory=list)
    formula_input_ids: List[str] = field(default_factory=list)
    raw_evidence_hash: str = ""
    provenance_hash: str = ""  # hash of the record itself, for staleness detection

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_date": self.source_date,
            "source_type": self.source_type,
            "collector_metric_id": self.collector_metric_id,
            "normalized_input_ids": self.normalized_input_ids,
            "formula_input_ids": self.formula_input_ids,
            "raw_evidence_hash": self.raw_evidence_hash,
            "provenance_hash": self.provenance_hash,
        }


@dataclass
class ApplicabilityDecision:
    """Immutable per-metric status decision (P4R ).

    A VALID decision requires every required_input to be non-None and non-MISSING.
    The runner records this BEFORE formula execution; the verifier re-derives it
    independently and compares to detect a status swap.
    """
    metric_id: str
    decided_status: str  # MetricStatus value
    required_inputs: List[str] = field(default_factory=list)
    required_input_values: Dict[str, Optional[float]] = field(default_factory=dict)
    decision_rule_id: str = "EXPLICIT_COMPLETENESS_CHECK"
    decision_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "decided_status": self.decided_status,
            "required_inputs": self.required_inputs,
            "required_input_values": self.required_input_values,
            "decision_rule_id": self.decision_rule_id,
            "decision_hash": self.decision_hash,
        }


@dataclass
class MetricInput:
    metric_id: str
    values: List[Optional[float]]  # per-period values (None = missing)
    unit: str = "BILLION_VND"
    periods: List[int] = field(default_factory=list)
    scope: str = "CONSOLIDATED"
    source_id: str = ""
    quality_status: str = "VALID"
    basis: str = ""

    # === P4R structural identity bindings (additive) ===
    share_basis_bindings: List[str] = field(default_factory=list)
    period_kind_bindings: List[str] = field(default_factory=list)
    reporting_scope_bindings: List[str] = field(default_factory=list)
    attribution_scope_bindings: List[str] = field(default_factory=list)
    denominator_basis_bindings: List[str] = field(default_factory=list)
    source_metric_ids: List[str] = field(default_factory=list)
    source_dates: List[str] = field(default_factory=list)
    source_types: List[str] = field(default_factory=list)
    corporate_action_adjustment_ids: List[str] = field(default_factory=list)

    # === P4R2 raw channel (Blocker 2 — deterministic scale contract) ===
    # raw_values: collector-reported values BEFORE normalization.
    # If empty, defaults to `values` (identity: raw == normalized).
    # When a mutation injects a raw value different from normalized, the scale
    # contract validator detects raw × factor ≠ normalized → UNIT_SCALE_MISMATCH.
    raw_values: List[Optional[float]] = field(default_factory=list)
    raw_unit: str = ""        # e.g. "VND", "SHARES"
    raw_scale: str = ""       # e.g. "UNIT", "MILLION", "BILLION"

    def get_value(self, year: int) -> Optional[float]:
        if year in self.periods:
            idx = self.periods.index(year)
            if idx < len(self.values):
                return self.values[idx]
        return None

    def get_raw_value(self, year: int) -> Optional[float]:
        """Read the raw (pre-normalization) value for a year.

        If raw_values is empty or shorter than periods, falls back to `values`
        (identity contract: raw == normalized when collector already canonical).
        """
        if not self.raw_values:
            return self.get_value(year)
        if year in self.periods:
            idx = self.periods.index(year)
            if idx < len(self.raw_values):
                return self.raw_values[idx]
        return self.get_value(year)

    def latest_value(self) -> Optional[float]:
        if self.values:
            for v in reversed(self.values):
                if v is not None:
                    return v
        return None

    def is_missing(self) -> bool:
        return all(v is None for v in self.values)

    def get_binding(self, year: int, binding_attr: str) -> Optional[str]:
        """Read a per-period binding by name. Returns None if year out of range or binding absent."""
        if year not in self.periods:
            return None
        idx = self.periods.index(year)
        values = getattr(self, binding_attr, [])
        if idx < len(values):
            v = values[idx]
            return v if v else None
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_id": self.metric_id, "values": self.values, "unit": self.unit,
            "periods": self.periods, "scope": self.scope, "source_id": self.source_id,
            "quality_status": self.quality_status, "basis": self.basis,
        }


@dataclass
class CalculationStep:
    step: int
    expression: str
    inputs_used: List[str]
    result: Any
    rule_id: Optional[str] = None
    evidence: Optional[str] = None


@dataclass
class MetricResult:
    metric_id: str
    status: str  # MetricStatus value
    value: Optional[float]
    unit: str
    formula_id: str
    formula_version: str
    normalized_inputs: Dict[str, Any] = field(default_factory=dict)
    calculation_trace: List[CalculationStep] = field(default_factory=list)
    period: str = ""
    scope: str = ""
    basis: str = ""
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)
    note: str = ""

    # === P4R structural identity on the result ===
    share_basis: str = ""
    period_kind: str = ""
    reporting_scope: str = ""
    attribution_scope: str = ""
    denominator_basis: str = ""
    formula_input_metric_ids: Dict[str, str] = field(default_factory=dict)
    applicability_decision: Optional[ApplicabilityDecision] = None
    provenance_record: Optional[ProvenanceRecord] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_id": self.metric_id, "status": self.status, "value": self.value,
            "unit": self.unit, "formula_id": self.formula_id, "formula_version": self.formula_version,
            "normalized_inputs": self.normalized_inputs,
            "calculation_trace": [{"step": s.step, "expression": s.expression,
                                   "inputs_used": s.inputs_used, "result": s.result,
                                   "rule_id": s.rule_id, "evidence": s.evidence} for s in self.calculation_trace],
            "period": self.period, "scope": self.scope, "basis": self.basis,
            "warnings": self.warnings, "errors": self.errors, "provenance": self.provenance,
            "share_basis": self.share_basis, "period_kind": self.period_kind,
            "reporting_scope": self.reporting_scope, "attribution_scope": self.attribution_scope,
            "denominator_basis": self.denominator_basis,
            "formula_input_metric_ids": self.formula_input_metric_ids,
            "applicability_decision": self.applicability_decision.to_dict() if self.applicability_decision else None,
            "provenance_record": self.provenance_record.to_dict() if self.provenance_record else None,
        }


@dataclass
class DuPontResult:
    net_margin: Optional[float] = None
    asset_turnover: Optional[float] = None
    equity_multiplier: Optional[float] = None
    reconstructed_roe: Optional[float] = None
    direct_roe: Optional[float] = None
    consistency_difference: Optional[float] = None
    consistency_status: str = "NOT_COMPUTED"
    component_hashes: Dict[str, str] = field(default_factory=dict)
    component_basis_bindings: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class FundamentalRequest:
    ticker: str = ""
    company: str = ""
    exchange: str = "HOSE"
    sector: str = ""
    reporting_currency: str = "VND"
    periods: List[int] = field(default_factory=list)
    metrics: Dict[str, MetricInput] = field(default_factory=dict)
    corporate_actions: List[Dict[str, Any]] = field(default_factory=list)
    peer_set: List[Dict[str, Any]] = field(default_factory=list)
    peer_policy: str = "MEDIAN"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker, "company": self.company,
            "exchange": self.exchange, "sector": self.sector,
            "reporting_currency": self.reporting_currency, "periods": self.periods,
            "peer_policy": self.peer_policy,
            "peer_set_size": len(self.peer_set),
        }


@dataclass
class FundamentalOutput:
    entity: Dict[str, str] = field(default_factory=dict)
    metric_results: List[MetricResult] = field(default_factory=list)
    dupont: Optional[DuPontResult] = None
    growth: Dict[str, Any] = field(default_factory=dict)
    peer_comparison: Dict[str, Any] = field(default_factory=dict)
    quality_summary: Dict[str, Any] = field(default_factory=dict)
    downstream_export: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    applicability_decisions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity": self.entity,
            "metric_results": [m.to_dict() for m in self.metric_results],
            "dupont": self.dupont.to_dict() if self.dupont else None,
            "growth": self.growth,
            "peer_comparison": self.peer_comparison,
            "quality_summary": self.quality_summary,
            "downstream_export": self.downstream_export,
            "warnings": self.warnings,
            "errors": self.errors,
            "applicability_decisions": self.applicability_decisions,
        }


@dataclass
class PipelineResult:
    output: FundamentalOutput
    errors: List[Dict[str, Any]]
    evidence_manifest: Dict[str, Any]
    execution_log: List[Dict[str, Any]]
    final_status: str  # PASS | PASS_WITH_WARNINGS | FAIL
