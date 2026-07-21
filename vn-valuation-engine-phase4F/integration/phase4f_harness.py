"""F4F-D — Integration harness with hash binding + pre/post comparison.

Catches: MUT-INT-005 (drop_method), stale verifier result reuse.
"""
from __future__ import annotations
import hashlib, json, copy
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass, field


@dataclass
class HarnessResult:
    child_artifact_hash: str = ""
    child_verifier_artifact_hash: str = ""
    adapter_artifact_hash: str = ""
    pre_post_comparison_ok: bool = True
    pre_post_diffs: List[str] = field(default_factory=list)
    stale_verifier_detected: bool = False
    final_status: str = "PASS"


def _sha(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, default=str,
                   separators=(",",":"), ensure_ascii=False).encode()
    ).hexdigest()


def run_harness_with_binding(
    original_child_output: Dict[str, Any],
    post_adapter_output: Dict[str, Any],
    child_verifier_artifact_hash: str = None,
) -> HarnessResult:
    """Run harness with hash binding + pre/post comparison.

    Catches:
    - MUT-INT-005 (drop_method): method count drops between child and adapter
    - Stale verifier reuse: verifier bound to different artifact hash
    """
    result = HarnessResult(
        child_artifact_hash=_sha(original_child_output),
        child_verifier_artifact_hash=child_verifier_artifact_hash or _sha(original_child_output),
        adapter_artifact_hash=_sha(post_adapter_output),
    )

    # Pre/post comparison: entity, methods, formulas, etc.
    original_methods = original_child_output.get("method_results") or []
    post_methods = post_adapter_output.get("method_results") or post_adapter_output.get("valuation_methods") or []

    # Method count comparison
    orig_count = len(original_methods)
    post_count = len(post_methods) if isinstance(post_methods, list) else 0
    if orig_count != post_count:
        result.pre_post_diffs.append(f"method_count: pre={orig_count} post={post_count}")

    # Method ID comparison
    orig_ids = {m.get("method_id") for m in original_methods if isinstance(m, dict)}
    if isinstance(post_methods, list):
        post_ids = {m.get("method_id") for m in post_methods if isinstance(m, dict)}
    else:
        post_ids = set()
    if orig_ids != post_ids:
        missing = orig_ids - post_ids
        added = post_ids - orig_ids
        if missing: result.pre_post_diffs.append(f"missing_method_ids: {missing}")
        if added: result.pre_post_diffs.append(f"added_method_ids: {added}")

    # Entity comparison
    orig_entity = original_child_output.get("entity") or {}
    if "entity" in post_adapter_output:
        post_entity = post_adapter_output.get("entity") or {}
        for k in ("canonical_ticker", "canonical_company", "exchange", "sector"):
            if orig_entity.get(k) != post_entity.get(k):
                result.pre_post_diffs.append(f"entity.{k}: pre={orig_entity.get(k)} post={post_entity.get(k)}")

    result.pre_post_comparison_ok = len(result.pre_post_diffs) == 0
    if not result.pre_post_comparison_ok:
        result.final_status = "FAIL"

    # Stale verifier check: if provided hash doesn't match current artifact hash
    if child_verifier_artifact_hash and child_verifier_artifact_hash != result.child_artifact_hash:
        result.stale_verifier_detected = True
        result.final_status = "FAIL"
        result.pre_post_diffs.append(f"stale_verifier: bound_hash={child_verifier_artifact_hash[:12]} != current_hash={result.child_artifact_hash[:12]}")

    return result
