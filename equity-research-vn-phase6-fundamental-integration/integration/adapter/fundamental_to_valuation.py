"""Fundamental → Valuation handoff — Phase 6 integration.

Only VALID/VALID_NEGATIVE metrics forwarded. PE/PB applicability enforced.
"""
from __future__ import annotations
import json, hashlib
from typing import Any, Dict, Tuple


def create_valuation_handoff(fundamental_output: Dict[str, Any],
                              context_hash: str) -> Dict[str, Any]:
    """Create valuation handoff from fundamental output.

    Only VALID/VALID_NEGATIVE metrics forwarded.
    PE/PB applicability computed from EPS/BVPS values.
    """
    downstream = fundamental_output.get("downstream_export", {})
    eps_export = downstream.get("EPS_basic", {})
    bvps_export = downstream.get("BVPS", {})

    # Extract exported values
    eps_value = eps_export.get("value")
    eps_status = eps_export.get("status", "INPUT_INCOMPLETE")
    bvps_value = bvps_export.get("value")
    bvps_status = bvps_export.get("status", "INPUT_INCOMPLETE")

    # Determine PE applicability
    pe_applicability = "NOT_APPLICABLE"
    if eps_value is not None and eps_value > 0 and eps_status in ("VALID", "VALID_NEGATIVE"):
        pe_applicability = "APPLICABLE"
    elif eps_value is not None and eps_value <= 0:
        pe_applicability = "NOT_APPLICABLE"

    # Determine PB applicability
    pb_applicability = "NOT_APPLICABLE"
    if bvps_value is not None and bvps_value > 0 and bvps_status in ("VALID", "VALID_NEGATIVE"):
        pb_applicability = "APPLICABLE"
    elif bvps_value is not None and bvps_value < 0:
        pb_applicability = "NOT_APPLICABLE"

    # ROE-based methods
    metric_results = fundamental_output.get("metric_results", [])
    roe_result = next((m for m in metric_results if m.get("metric_id") == "ROE"), {})
    roe_status = roe_result.get("status", "INPUT_INCOMPLETE")
    roe_applicability = "NOT_APPLICABLE" if roe_status in ("MANUAL_REVIEW_REQUIRED", "ERROR", "INPUT_INCOMPLETE") else "APPLICABLE"

    handoff = {
        "context_hash": context_hash,
        "EPS": {
            "value": eps_value if eps_status in ("VALID", "VALID_NEGATIVE") else None,
            "status": eps_status,
            "PE_method_applicability": pe_applicability,
            "forwarded": eps_status in ("VALID", "VALID_NEGATIVE"),
        },
        "BVPS": {
            "value": bvps_value if bvps_status in ("VALID", "VALID_NEGATIVE") else None,
            "status": bvps_status,
            "PB_method_applicability": pb_applicability,
            "forwarded": bvps_status in ("VALID", "VALID_NEGATIVE"),
        },
        "ROE": {
            "status": roe_status,
            "ROE_method_applicability": roe_applicability,
            "forwarded": roe_status in ("VALID", "VALID_NEGATIVE"),
        },
        "growth_metrics": downstream.get("growth_metrics", {}),
        "peer_comparison": downstream.get("peer_comparison", {}),
        "blocked_metrics": [],
        "handoff_hash": "",
    }

    # Record blocked metrics
    for name, export in [("EPS", eps_export), ("BVPS", bvps_export)]:
        if export.get("status") not in ("VALID", "VALID_NEGATIVE"):
            handoff["blocked_metrics"].append({
                "metric": name,
                "status": export.get("status"),
                "reason": "non-valid status blocks downstream",
            })

    handoff["handoff_hash"] = hashlib.sha256(
        json.dumps({k: v for k, v in handoff.items() if k != "handoff_hash"},
                   sort_keys=True, default=str, separators=(",", ":")).encode()
    ).hexdigest()

    return handoff
