"""Phase 4R structural validation tests — period & scope alignment.

10 tests covering period alignment (MUT-FUND-023), scope alignment
(MUT-FUND-024 / 025), and structural binding defaults.
"""
import sys, pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "implementation"))

from models import MetricInput, PeriodType, ReportingScope, AttributionScope
from normalization.period_scope_policy import (
    validate_period_alignment, validate_scope_alignment,
    normalize_period_kind_binding, normalize_reporting_scope_binding, normalize_attribution_scope_binding,
)


def _metric(mid, values, periods=None, **kw):
    n = len(values)
    if periods is None: periods = list(range(2025-n+1, 2026))
    defaults = dict(unit="BILLION_VND", periods=periods, scope="CONSOLIDATED", source_id="t")
    defaults.update(kw)
    return MetricInput(metric_id=mid, values=values, **defaults)


def test_p4r_struct_007_ttm_vs_quarter_period_mismatch_detected():
    """P4R-TEST-STRUCT-007: TTM numerator with quarterly denominator → PERIOD_MISMATCH."""
    npat = _metric("net_income", [5000], period_kind_bindings=[PeriodType.TTM.value])
    eq = _metric("equity", [33000], period_kind_bindings=[PeriodType.QUARTERLY.value])
    ok, err, _ = validate_period_alignment(npat, eq, 2025)
    assert ok is False
    assert err == "PERIOD_MISMATCH"


def test_p4r_struct_007b_annual_with_ttm_compatible():
    """ANNUAL and TTM are both full-year → compatible."""
    npat = _metric("net_income", [5000], period_kind_bindings=[PeriodType.ANNUAL.value])
    eq = _metric("equity", [33000], period_kind_bindings=[PeriodType.TTM.value])
    ok, err, _ = validate_period_alignment(npat, eq, 2025)
    assert ok is True
    assert err is None


def test_p4r_struct_period_alignment_clean_annual():
    """Both ANNUAL → ok."""
    npat = _metric("net_income", [5000], period_kind_bindings=[PeriodType.ANNUAL.value])
    eq = _metric("equity", [33000], period_kind_bindings=[PeriodType.ANNUAL.value])
    ok, err, _ = validate_period_alignment(npat, eq, 2025)
    assert ok is True


def test_p4r_scope_001_consol_standalone_scope_mismatch_detected():
    """P4R-TEST-SCOPE-001: consolidated numerator with standalone denominator → SCOPE_MISMATCH."""
    npat = _metric("net_income", [5000], reporting_scope_bindings=[ReportingScope.CONSOLIDATED.value])
    eq = _metric("equity", [33000], reporting_scope_bindings=[ReportingScope.STANDALONE.value])
    ok, err, _ = validate_scope_alignment(npat, eq, 2025)
    assert ok is False
    assert err == "SCOPE_MISMATCH"


def test_p4r_scope_002_attribution_total_mix_detected():
    """P4R-TEST-SCOPE-002: attributable NI with total-group equity → SCOPE_MISMATCH."""
    npat = _metric("net_income", [5000],
                   reporting_scope_bindings=[ReportingScope.CONSOLIDATED.value],
                   attribution_scope_bindings=[AttributionScope.ATTRIBUTABLE_TO_PARENT.value])
    eq = _metric("equity", [33000],
                 reporting_scope_bindings=[ReportingScope.CONSOLIDATED.value],  # same consolidation
                 attribution_scope_bindings=[AttributionScope.TOTAL_GROUP.value])  # different attribution
    ok, err, _ = validate_scope_alignment(npat, eq, 2025)
    assert ok is False
    assert err == "SCOPE_MISMATCH"


def test_p4r_struct_scope_alignment_clean_consolidated_attributable():
    """Both consolidated + attributable → ok."""
    npat = _metric("net_income", [5000],
                   reporting_scope_bindings=[ReportingScope.CONSOLIDATED.value],
                   attribution_scope_bindings=[AttributionScope.ATTRIBUTABLE_TO_PARENT.value])
    eq = _metric("equity", [33000],
                 reporting_scope_bindings=[ReportingScope.CONSOLIDATED.value],
                 attribution_scope_bindings=[AttributionScope.ATTRIBUTABLE_TO_PARENT.value])
    ok, err, _ = validate_scope_alignment(npat, eq, 2025)
    assert ok is True


def test_p4r_struct_period_kind_missing_pads_with_default():
    m = _metric("net_income", [5000, 5500])
    bindings, warns = normalize_period_kind_binding(m)
    assert bindings == [PeriodType.ANNUAL.value, PeriodType.ANNUAL.value]
    assert len(warns) == 2


def test_p4r_struct_reporting_scope_missing_pads_with_default():
    m = _metric("revenue", [100, 200])
    bindings, warns = normalize_reporting_scope_binding(m)
    assert bindings == [ReportingScope.CONSOLIDATED.value]*2
    assert len(warns) == 2


def test_p4r_struct_attribution_scope_missing_pads_with_default():
    m = _metric("equity", [100, 200])
    bindings, warns = normalize_attribution_scope_binding(m)
    assert bindings == [AttributionScope.ATTRIBUTABLE_TO_PARENT.value]*2
    assert len(warns) == 2


def test_p4r_struct_scope_alignment_both_standalone_ok():
    """Both standalone + attributable → ok (parent-only figures)."""
    npat = _metric("net_income", [5000],
                   reporting_scope_bindings=[ReportingScope.STANDALONE.value],
                   attribution_scope_bindings=[AttributionScope.ATTRIBUTABLE_TO_PARENT.value])
    eq = _metric("equity", [33000],
                 reporting_scope_bindings=[ReportingScope.STANDALONE.value],
                 attribution_scope_bindings=[AttributionScope.ATTRIBUTABLE_TO_PARENT.value])
    ok, err, _ = validate_scope_alignment(npat, eq, 2025)
    assert ok is True
