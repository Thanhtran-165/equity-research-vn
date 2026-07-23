"""Canonical models for vn-fundamental-analysis Phase 4."""
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


class Scope(str, Enum):
    CONSOLIDATED = "CONSOLIDATED"
    STANDALONE = "STANDALONE"
    ATTRIBUTABLE_TO_PARENT = "ATTRIBUTABLE_TO_PARENT"
    TOTAL_GROUP = "TOTAL_GROUP"


class ShareBasis(str, Enum):
    BASIC = "BASIC"
    DILUTED = "DILUTED"


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

    def get_value(self, year: int) -> Optional[float]:
        if year in self.periods:
            idx = self.periods.index(year)
            if idx < len(self.values):
                return self.values[idx]
        return None

    def latest_value(self) -> Optional[float]:
        if self.values:
            for v in reversed(self.values):
                if v is not None:
                    return v
        return None

    def is_missing(self) -> bool:
        return all(v is None for v in self.values)


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker, "company": self.company,
            "exchange": self.exchange, "sector": self.sector,
            "reporting_currency": self.reporting_currency, "periods": self.periods,
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
        }


@dataclass
class PipelineResult:
    output: FundamentalOutput
    errors: List[Dict[str, Any]]
    evidence_manifest: Dict[str, Any]
    execution_log: List[Dict[str, Any]]
    final_status: str  # PASS | PASS_WITH_WARNINGS | FAIL
