"""Phase 4R structural validation tests — share basis (MUT-FUND-008 / 009).

8 tests covering ShareBasis policy: clean pass, period-end→weighted swap,
basic→diluted swap, EPS_BASIS_MISMATCH detection, missing binding pad+warning,
BVPS basis rules, default propagation, and verifier-side detection.
"""
import sys, pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "implementation"))

from models import FundamentalRequest, MetricInput, MetricStatus, ShareBasis, PeriodType
from normalization.share_basis_policy import (
    validate_share_basis_for_metric, normalize_share_basis_binding, PER_SHARE_REQUIREMENTS,
)
from formula_engine import compute_eps, compute_bvps


def _metric(mid, values, periods=None, **kw):
    n = len(values)
    if periods is None: periods = list(range(2025-n+1, 2026))
    defaults = dict(unit="BILLION_VND", periods=periods, scope="CONSOLIDATED", source_id="t")
    defaults.update(kw)
    return MetricInput(metric_id=mid, values=values, **defaults)


def test_p4r_struct_001_share_basis_clean_weighted_average_basic_ok():
    """P4R-TEST-STRUCT-001 (positive control): WEIGHTED_AVERAGE_BASIC ok for EPS_BASIC."""
    sh = _metric("shares_outstanding", [1.5, 1.5, 1.5],
                 share_basis_bindings=[ShareBasis.WEIGHTED_AVERAGE_BASIC.value]*3)
    ok, err = validate_share_basis_for_metric("EPS_BASIC", sh, 2025)
    assert ok is True
    assert err is None


def test_p4r_struct_001b_period_end_disguised_as_weighted_detected():
    """P4R-TEST-STRUCT-001: period-end shares where weighted-average is required → SHARE_BASIS_MISMATCH.

    EPS spec requires WEIGHTED_AVERAGE_* shares. PERIOD_END_BASIC is a silent
    substitution that inflates EPS for issuers; the strict policy rejects it.
    """
    sh = _metric("shares_outstanding", [1.5, 1.5, 1.5],
                 share_basis_bindings=[ShareBasis.PERIOD_END_BASIC.value]*3)
    ok, err = validate_share_basis_for_metric("EPS_BASIC", sh, 2025)
    assert ok is False
    assert err == "SHARE_BASIS_MISMATCH"


def test_p4r_struct_002_basic_disguised_as_diluted_detected():
    """P4R-TEST-STRUCT-002: basic shares replaced with diluted → EPS_BASIS_MISMATCH."""
    sh = _metric("shares_outstanding", [1.5, 1.5, 1.5],
                 share_basis_bindings=[ShareBasis.WEIGHTED_AVERAGE_DILUTED.value]*3)
    ok, err = validate_share_basis_for_metric("EPS_BASIC", sh, 2025)
    assert ok is False
    assert err == "EPS_BASIS_MISMATCH"


def test_p4r_struct_002b_diluted_metric_accepts_diluted_basis():
    """EPS_DILUTED metric with DILUTED basis → ok."""
    sh = _metric("shares_outstanding", [1.6, 1.6, 1.6],
                 share_basis_bindings=[ShareBasis.WEIGHTED_AVERAGE_DILUTED.value]*3)
    ok, err = validate_share_basis_for_metric("EPS_DILUTED", sh, 2025)
    assert ok is True
    assert err is None


def test_p4r_struct_share_basis_missing_pads_with_warning():
    """Missing share_basis_bindings → padded with default + STRUCTURAL_BINDING_DEFAULTED warning."""
    sh = _metric("shares_outstanding", [1.5, 1.5, 1.5])  # no bindings
    bindings, warnings = normalize_share_basis_binding(sh)
    assert len(bindings) == 3
    assert bindings[0] == ShareBasis.WEIGHTED_AVERAGE_BASIC.value
    assert len(warnings) == 3
    assert "STRUCTURAL_BINDING_DEFAULTED" in warnings[0]


def test_p4r_struct_bvps_accepts_period_end():
    """BVPS uses period-end shares — any PERIOD_END_* basis is allowed."""
    sh = _metric("shares_outstanding", [1.5, 1.5, 1.5],
                 share_basis_bindings=[ShareBasis.PERIOD_END_BASIC.value]*3)
    ok, err = validate_share_basis_for_metric("BVPS", sh, 2025)
    assert ok is True


def test_p4r_struct_eps_carries_share_basis_identity():
    """compute_eps attaches share_basis to MetricResult."""
    eps = compute_eps(5000, 1.5, basis="WEIGHTED_AVERAGE_BASIC",
                     share_basis=ShareBasis.WEIGHTED_AVERAGE_BASIC.value)
    assert eps.share_basis == ShareBasis.WEIGHTED_AVERAGE_BASIC.value
    assert eps.metric_id == "EPS_BASIC"


def test_p4r_struct_eps_with_invalid_basis_still_numeric_but_flagged_by_validator():
    """Even with wrong basis, formula computes a number; validator catches the identity error."""
    sh = _metric("shares_outstanding", [1.5, 1.5, 1.5],
                 share_basis_bindings=[ShareBasis.PERIOD_END_DILUTED.value]*3)
    eps = compute_eps(5000, 1.5, basis="WEIGHTED_AVERAGE_BASIC",
                     share_basis=ShareBasis.PERIOD_END_DILUTED.value)
    # Numeric result still produced
    assert eps.value is not None
    # But validator flags it
    ok, err = validate_share_basis_for_metric("EPS_BASIC", sh, 2025)
    assert ok is False
    assert err == "EPS_BASIS_MISMATCH"
