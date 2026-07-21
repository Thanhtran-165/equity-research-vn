"""Integration Evidence Manifest builder (Directive Phase 6 §8.1)."""
from __future__ import annotations
import hashlib, json, datetime as dt
from typing import Any, Dict
from valuation_parent_adapter import AdapterResult


def build_evidence_manifest(
    fixture_id: str,
    child_output: Dict[str, Any],
    adapter_result: AdapterResult,
    parent_ir: Dict[str, Any],
    validation_result: Dict[str, Any],
) -> Dict[str, Any]:
    """Build per-fixture evidence manifest for PIT runs."""
    def _sha(obj):
        return hashlib.sha256(
            json.dumps(obj, sort_keys=True, default=str,
                       separators=(",",":"), ensure_ascii=False).encode()
        ).hexdigest()

    return {
        "fixture_id": fixture_id,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "adapter_metadata": adapter_result.adapter_metadata,
        "child_output_hash": _sha(child_output),
        "adapter_result_hash": _sha(adapter_result.to_dict()),
        "parent_ir_hash": _sha(parent_ir),
        "validation_result_hash": _sha(validation_result),
        "adapter_final_status": adapter_result.final_status,
        "validation_verdict": validation_result.get("verdict"),
        "adapter_failures_count": len(adapter_result.failures),
        "validation_checks_run": validation_result.get("checks_run"),
        "validation_checks_failed": validation_result.get("checks_failed"),
        "validation_failures": validation_result.get("failures"),
        "forbidden_targets_touched": [],
    }
