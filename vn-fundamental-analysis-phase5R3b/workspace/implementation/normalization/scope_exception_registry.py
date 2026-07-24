"""Scope exception registry — Phase 4R2 Blocker 3.

Replaces Phase 4R's silent `allow_attribution_mismatch=True` parameter with
explicit, versioned, registered scope-compatibility rules. Every formula-specific
scope exception must have a rule_id, rationale, and quality treatment.

A metric ID is unambiguous: ROA_GROUP (NPAT attributable / total group assets)
and ROA_ATTRIBUTABLE are distinct metric IDs, not the same `ROA` overloaded.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
from models import ReportingScope, AttributionScope


@dataclass
class ScopeCompatibilityRule:
    """A registered exception allowing numerator/denominator scope mismatch for a specific metric."""
    rule_id: str
    metric_id: str                   # unambiguous metric ID (ROA_GROUP, not ROA)
    numerator_reporting_scope: str
    denominator_reporting_scope: str
    numerator_attribution_scope: str
    denominator_attribution_scope: str
    allowed: bool
    rationale: str
    quality_treatment: str           # e.g. "WARNING: minority interest not stripped"


# === Registered scope-compatibility rules ===
# Default rule: numerator and denominator must share both scopes (strict).
# Exceptions are explicit per metric_id.

REGISTERED_RULES = [
    # Default strict rule for ROE: attributable NPAT / attributable equity (same scope)
    ScopeCompatibilityRule(
        rule_id="ROE_ATTRIBUTABLE_STRICT",
        metric_id="ROE",
        numerator_reporting_scope=ReportingScope.CONSOLIDATED.value,
        denominator_reporting_scope=ReportingScope.CONSOLIDATED.value,
        numerator_attribution_scope=AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
        denominator_attribution_scope=AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
        allowed=True,
        rationale="ROE = NPAT attributable to parent / common equity attributable to parent",
        quality_treatment="none",
    ),
    # ROA_GROUP: attributable NPAT / total group assets (registered exception)
    ScopeCompatibilityRule(
        rule_id="ROA_GROUP_ATTRIBUTABLE_OVER_GROUP_ASSETS",
        metric_id="ROA_GROUP",
        numerator_reporting_scope=ReportingScope.CONSOLIDATED.value,
        denominator_reporting_scope=ReportingScope.CONSOLIDATED.value,
        numerator_attribution_scope=AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
        denominator_attribution_scope=AttributionScope.TOTAL_GROUP.value,
        allowed=True,
        rationale="ROA conventionally uses NPAT attributable / total assets (group). "
                  "Total assets include 100% of subsidiaries' assets; NPAT attributable "
                  "excludes minority share. This is the standard DuPont ROA.",
        quality_treatment="WARNING: denominator includes minority assets; numerator excludes minority NI",
    ),
    # ROA_ATTRIBUTABLE: attributable NPAT / attributable assets (strict, both attributable)
    ScopeCompatibilityRule(
        rule_id="ROA_ATTRIBUTABLE_STRICT",
        metric_id="ROA_ATTRIBUTABLE",
        numerator_reporting_scope=ReportingScope.CONSOLIDATED.value,
        denominator_reporting_scope=ReportingScope.CONSOLIDATED.value,
        numerator_attribution_scope=AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
        denominator_attribution_scope=AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
        allowed=True,
        rationale="Strict ROA: both numerator and denominator attributable to parent.",
        quality_treatment="none",
    ),
    # NPM: attributable NPAT / total-group revenue (standard margin convention)
    ScopeCompatibilityRule(
        rule_id="NPM_ATTRIBUTABLE_OVER_GROUP_REVENUE",
        metric_id="NET_PROFIT_MARGIN",
        numerator_reporting_scope=ReportingScope.CONSOLIDATED.value,
        denominator_reporting_scope=ReportingScope.CONSOLIDATED.value,
        numerator_attribution_scope=AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
        denominator_attribution_scope=AttributionScope.TOTAL_GROUP.value,
        allowed=True,
        rationale="NPM = NPAT attributable to parent / total-group revenue. Revenue is "
                  "always total-group (consolidated); NPAT attributable excludes minority.",
        quality_treatment="WARNING: numerator excludes minority NI; denominator is total-group revenue",
    ),
    # DuPont AT uses total-group assets (same as ROA_GROUP)
    ScopeCompatibilityRule(
        rule_id="DUPONT_AT_GROUP_ASSETS",
        metric_id="DUPONT_AT",
        numerator_reporting_scope=ReportingScope.CONSOLIDATED.value,
        denominator_reporting_scope=ReportingScope.CONSOLIDATED.value,
        numerator_attribution_scope=AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
        denominator_attribution_scope=AttributionScope.TOTAL_GROUP.value,
        allowed=True,
        rationale="DuPont AT = Revenue / total assets (group). Standard DuPont decomposition.",
        quality_treatment="WARNING: denominator includes minority assets",
    ),
    # DuPont EM: total group assets / total group equity (both TOTAL_GROUP)
    ScopeCompatibilityRule(
        rule_id="DUPONT_EM_GROUP",
        metric_id="DUPONT_EM",
        numerator_reporting_scope=ReportingScope.CONSOLIDATED.value,
        denominator_reporting_scope=ReportingScope.CONSOLIDATED.value,
        numerator_attribution_scope=AttributionScope.TOTAL_GROUP.value,
        denominator_attribution_scope=AttributionScope.TOTAL_GROUP.value,
        allowed=True,
        rationale="DuPont EM = total assets / total equity (both group). Leverage ratio.",
        quality_treatment="none",
    ),
]


def get_rule_for_metric(metric_id: str) -> Optional[ScopeCompatibilityRule]:
    """Look up the registered scope-compatibility rule for a metric_id.

    Returns None if no rule registered (caller must treat unregistered metric
    as strict-scope-required and FAIL on any mismatch).
    """
    for rule in REGISTERED_RULES:
        if rule.metric_id == metric_id:
            return rule
    return None


def validate_scope_with_rule(metric_id: str,
                              numerator_reporting_scope: str,
                              denominator_reporting_scope: str,
                              numerator_attribution_scope: str,
                              denominator_attribution_scope: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate scope alignment against the registered rule for metric_id.

    Returns (ok, error_code, quality_warning).
    - If a registered rule exists and matches → ok, with quality_treatment as warning.
    - If no rule registered and scopes mismatch → SCOPE_MISMATCH (no silent exception).
    - If rule registered but scopes don't match the rule → SCOPE_MISMATCH.
    """
    rule = get_rule_for_metric(metric_id)
    if rule is None:
        # No registered exception → strict: all four scopes must match
        if numerator_reporting_scope != denominator_reporting_scope:
            return False, "SCOPE_MISMATCH", None
        if numerator_attribution_scope != denominator_attribution_scope:
            return False, "SCOPE_MISMATCH", None
        return True, None, None
    # Registered rule: check the actual scopes match the rule's allowance
    rs_ok = (numerator_reporting_scope == rule.numerator_reporting_scope and
             denominator_reporting_scope == rule.denominator_reporting_scope)
    as_ok = (numerator_attribution_scope == rule.numerator_attribution_scope and
             denominator_attribution_scope == rule.denominator_attribution_scope)
    if rs_ok and as_ok:
        warning = rule.quality_treatment if rule.quality_treatment != "none" else None
        return True, None, warning
    return False, "SCOPE_MISMATCH", None


def list_registered_rules() -> List[ScopeCompatibilityRule]:
    return list(REGISTERED_RULES)
