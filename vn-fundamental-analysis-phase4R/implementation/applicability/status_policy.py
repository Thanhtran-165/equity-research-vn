"""Applicability / status policy — Phase 4R structural validation (MUT-FUND-019).

Builds an immutable ApplicabilityDecision per metric BEFORE formula execution.
A VALID decision requires every required_input non-None and non-MISSING.
Verifier independently re-derives the decision and compares to detect a status swap.
"""
from __future__ import annotations
import hashlib, json
from typing import Dict, List, Optional
from models import MetricInput, MetricStatus, ApplicabilityDecision


# metric_id -> required input metric IDs
REQUIRED_INPUTS = {
    "EPS_BASIC":   ["net_income", "shares_outstanding"],
    "EPS_DILUTED": ["net_income", "shares_outstanding"],
    "BVPS":        ["equity", "shares_outstanding"],
    "ROE":         ["net_income", "equity"],
    "ROA":         ["net_income", "total_assets"],
    "NET_PROFIT_MARGIN": ["net_income", "revenue"],
    "DUPONT_AT":   ["revenue", "total_assets"],
    "DUPONT_EM":   ["total_assets", "equity"],
}


def derive_decision(metric_id: str, metrics: Dict[str, MetricInput], year: int) -> ApplicabilityDecision:
    """Build the canonical applicability decision for a metric."""
    required = REQUIRED_INPUTS.get(metric_id, [])
    values: Dict[str, Optional[float]] = {}
    all_present = True
    for req_id in required:
        m = metrics.get(req_id)
        v = m.get_value(year) if m else None
        values[req_id] = v
        if v is None:
            all_present = False
    status = MetricStatus.VALID.value if all_present else MetricStatus.INPUT_INCOMPLETE.value
    # Decision hash binds metric_id + required inputs + their values + rule_id.
    payload = {"metric_id": metric_id, "required": required, "values": values, "rule_id": "EXPLICIT_COMPLETENESS_CHECK"}
    h = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()
    return ApplicabilityDecision(
        metric_id=metric_id, decided_status=status,
        required_inputs=list(required), required_input_values=values,
        decision_rule_id="EXPLICIT_COMPLETENESS_CHECK", decision_hash=h,
    )


def status_upgrade_is_valid(decision: ApplicabilityDecision, declared_status: str) -> bool:
    """A VALID output status requires the decision to also be VALID (cannot upgrade INCOMPLETE -> VALID)."""
    if declared_status == MetricStatus.VALID.value:
        return decision.decided_status == MetricStatus.VALID.value
    if declared_status == MetricStatus.VALID_NEGATIVE.value:
        return decision.decided_status == MetricStatus.VALID.value
    return True
