"""Period & scope policy — Phase 4R structural validation (/ 024 / 025).

- Period alignment: ratio numerator and denominator must share period_kind
  (ANNUAL~ANNUAL, TTM~TTM, QUARTERLY~QUARTERLY same quarter). Mixed period
  kinds inside one ratio → PERIOD_MISMATCH.
- Scope alignment: ratio numerator and denominator must share reporting_scope
  AND attribution_scope. Cross-scope → SCOPE_MISMATCH.
"""
from __future__ import annotations
from typing import List, Optional, Tuple
from models import MetricInput, PeriodType, ReportingScope, AttributionScope


def normalize_period_kind_binding(metric: MetricInput, default: str = PeriodType.ANNUAL.value) -> Tuple[List[str], List[str]]:
    n = len(metric.values)
    bindings = list(metric.period_kind_bindings)
    warnings: List[str] = []
    while len(bindings) < n:
        bindings.append(default)
        warnings.append(f"STRUCTURAL_BINDING_DEFAULTED: period_kind defaulted to {default} (slot {len(bindings)-1})")
    return bindings[:n], warnings


def normalize_reporting_scope_binding(metric: MetricInput, default: str = ReportingScope.CONSOLIDATED.value) -> Tuple[List[str], List[str]]:
    n = len(metric.values)
    bindings = list(metric.reporting_scope_bindings)
    warnings: List[str] = []
    while len(bindings) < n:
        bindings.append(default)
        warnings.append(f"STRUCTURAL_BINDING_DEFAULTED: reporting_scope defaulted to {default} (slot {len(bindings)-1})")
    return bindings[:n], warnings


def normalize_attribution_scope_binding(metric: MetricInput, default: str = AttributionScope.ATTRIBUTABLE_TO_PARENT.value) -> Tuple[List[str], List[str]]:
    n = len(metric.values)
    bindings = list(metric.attribution_scope_bindings)
    warnings: List[str] = []
    while len(bindings) < n:
        bindings.append(default)
        warnings.append(f"STRUCTURAL_BINDING_DEFAULTED: attribution_scope defaulted to {default} (slot {len(bindings)-1})")
    return bindings[:n], warnings


def _binding_at(metric: MetricInput, binding_attr: str, normalize_default: str, year: int) -> Tuple[Optional[str], List[str]]:
    if year not in metric.periods:
        return None, []
    idx = metric.periods.index(year)
    raw = getattr(metric, binding_attr, [])
    if idx < len(raw) and raw[idx]:
        return raw[idx], []
    # Default
    n = len(metric.values)
    bindings = list(raw)
    warnings: List[str] = []
    while len(bindings) < n:
        bindings.append(normalize_default)
    if idx < len(bindings):
        return bindings[idx], [f"STRUCTURAL_BINDING_DEFAULTED: {binding_attr} defaulted to {normalize_default} (slot {idx})"]
    return normalize_default, [f"STRUCTURAL_BINDING_DEFAULTED: {binding_attr} defaulted to {normalize_default}"]


def validate_period_alignment(numerator: MetricInput, denominator: MetricInput, year: int) -> Tuple[bool, Optional[str], List[str]]:
    """Numerator and denominator must share period_kind at `year`."""
    n_kind, w1 = _binding_at(numerator, "period_kind_bindings", PeriodType.ANNUAL.value, year)
    d_kind, w2 = _binding_at(denominator, "period_kind_bindings", PeriodType.ANNUAL.value, year)
    warnings = w1 + w2
    if n_kind is None or d_kind is None:
        return False, "PERIOD_OUT_OF_RANGE", warnings
    # ANNUAL, TTM, YTD are full-year flow metrics. POINT_IN_TIME is a balance-sheet
    # stock metric. A flow/stock ratio (ROE = annual income / ending equity) is
    # standard accounting convention — ANNUAL and POINT_IN_TIME are compatible.
    annual_compatible = {PeriodType.ANNUAL.value, PeriodType.TTM.value, PeriodType.YTD.value, PeriodType.POINT_IN_TIME.value}
    if n_kind == d_kind:
        return True, None, warnings
    if n_kind in annual_compatible and d_kind in annual_compatible:
        return True, None, warnings
    return False, "PERIOD_MISMATCH", warnings


def validate_scope_alignment(numerator: MetricInput, denominator: MetricInput, year: int,
                             allow_attribution_mismatch: bool = False) -> Tuple[bool, Optional[str], List[str]]:
    """Numerator and denominator must share reporting_scope AND attribution_scope.

    `allow_attribution_mismatch=True` permits ATTRIBUTABLE_TO_PARENT numerator
    with TOTAL_GROUP denominator — this is standard for ROA (NPAT attributable
    / total assets) and DuPont AT/EM (the whole-group balance sheet is the
    correct denominator for an attributable numerator). Reporting_scope must
    still match (consolidated vs standalone).
    """
    n_rs, w1 = _binding_at(numerator, "reporting_scope_bindings", ReportingScope.CONSOLIDATED.value, year)
    d_rs, w2 = _binding_at(denominator, "reporting_scope_bindings", ReportingScope.CONSOLIDATED.value, year)
    n_as, w3 = _binding_at(numerator, "attribution_scope_bindings", AttributionScope.ATTRIBUTABLE_TO_PARENT.value, year)
    d_as, w4 = _binding_at(denominator, "attribution_scope_bindings", AttributionScope.ATTRIBUTABLE_TO_PARENT.value, year)
    warnings = w1 + w2 + w3 + w4
    if n_rs is None or d_rs is None or n_as is None or d_as is None:
        return False, "PERIOD_OUT_OF_RANGE", warnings
    if n_rs != d_rs:
        return False, "SCOPE_MISMATCH", warnings
    if not allow_attribution_mismatch and n_as != d_as:
        return False, "SCOPE_MISMATCH", warnings
    return True, None, warnings
