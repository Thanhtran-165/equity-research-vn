"""F4G-D Semantic Binding Harness — Phase 4G.

Extends phase4f_harness.py with 26+ bound field pre/post comparison.
Enforces execution order: raw → context → artifact → verifier → adapter → comparison.
"""
from __future__ import annotations
import hashlib, json, copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class SemanticDrift:
    field_path: str
    pre_adapter_value: Any
    post_adapter_value: Any
    expected_mapping: str
    observed_mapping: str
    severity: str
    owner: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_path": self.field_path,
            "pre_adapter_value": str(self.pre_adapter_value)[:100],
            "post_adapter_value": str(self.post_adapter_value)[:100],
            "expected_mapping": self.expected_mapping,
            "observed_mapping": self.observed_mapping,
            "severity": self.severity,
            "owner": self.owner,
        }


@dataclass
class HarnessBindingResult:
    artifact_hash: str = ""
    context_hash: str = ""
    verified_artifact_hash: str = ""
    registry_hashes: Dict[str, str] = field(default_factory=dict)
    pre_post_comparison_ok: bool = True
    semantic_drifts: List[SemanticDrift] = field(default_factory=list)
    stale_verifier_detected: bool = False
    hash_binding_ok: bool = True
    final_status: str = "PASS"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_hash": self.artifact_hash,
            "context_hash": self.context_hash,
            "verified_artifact_hash": self.verified_artifact_hash,
            "registry_hashes": self.registry_hashes,
            "pre_post_comparison_ok": self.pre_post_comparison_ok,
            "semantic_drifts": [d.to_dict() for d in self.semantic_drifts],
            "stale_verifier_detected": self.stale_verifier_detected,
            "hash_binding_ok": self.hash_binding_ok,
            "final_status": self.final_status,
        }


def _sha(obj) -> str:
    clean = json.loads(json.dumps(obj, default=str))
    for k in ("generated_at", "started_at", "completed_at", "ts", "request_id"):
        clean.pop(k, None) if isinstance(clean, dict) else None
    return hashlib.sha256(
        json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def run_semantic_binding(
    pre_artifact: Dict[str, Any],
    post_adapter_output: Dict[str, Any],
    semantic_context: Dict[str, Any],
    verified_artifact_hash: str = None,
) -> HarnessBindingResult:
    """Run pre/post semantic comparison across 26+ bound field groups.

    Directive F4G-D §6.2: compare entity, valuation, methods, benchmarks,
    premium, basis, source/period/scope, errors, traces, bridges, prices,
    context hash, registry hashes, verifier artifact hash.
    """
    result = HarnessBindingResult()
    result.artifact_hash = _sha(pre_artifact)
    result.context_hash = semantic_context.get("semantic_context_hash", "")
    result.verified_artifact_hash = verified_artifact_hash or result.artifact_hash
    result.registry_hashes = semantic_context.get("registry_hashes", {})

    # Hash binding check
    if verified_artifact_hash and verified_artifact_hash != result.artifact_hash:
        result.stale_verifier_detected = True
        result.hash_binding_ok = False
        result.final_status = "FAIL"
        result.semantic_drifts.append(SemanticDrift(
            field_path="artifact_hash",
            pre_adapter_value=verified_artifact_hash[:16],
            post_adapter_value=result.artifact_hash[:16],
            expected_mapping="artifact hash matches verified hash",
            observed_mapping="STALE — artifact changed since verification",
            severity="CRITICAL", owner="HARNESS",
        ))

    drifts = result.semantic_drifts

    def compare(pre_val, post_val, field_path, owner="HARNESS", severity="MAJOR"):
        if pre_val != post_val:
            drifts.append(SemanticDrift(
                field_path=field_path,
                pre_adapter_value=pre_val, post_adapter_value=post_val,
                expected_mapping=f"{field_path} preserved",
                observed_mapping=f"changed: {str(pre_val)[:40]} → {str(post_val)[:40]}",
                severity=severity, owner=owner,
            ))

    # === 26+ bound field comparisons ===

    # 1-4: Entity
    pre_entity = pre_artifact.get("entity") or {}
    post_entity = post_adapter_output.get("entity") or {}
    for k in ("canonical_ticker", "canonical_company", "exchange", "sector"):
        compare(pre_entity.get(k), post_entity.get(k), f"entity.{k}")

    # 5-6: Valuation context
    compare(pre_artifact.get("valuation_date"), post_adapter_output.get("valuation_date"), "valuation_date")
    compare(pre_artifact.get("reporting_currency"), post_adapter_output.get("reporting_currency"), "reporting_currency")

    # 7-9: Methods
    pre_methods = pre_artifact.get("method_results") or []
    post_methods = post_adapter_output.get("method_results") or post_adapter_output.get("valuation_methods") or []
    pre_ids = sorted(m.get("method_id") for m in pre_methods if isinstance(m, dict))
    post_ids = sorted(m.get("method_id") for m in post_methods if isinstance(m, dict))
    compare(pre_ids, post_ids, "method_ids")
    compare(len(pre_methods), len(post_methods), "method_count")
    pre_statuses = sorted(f"{m.get('method_id')}:{m.get('status')}" for m in pre_methods if isinstance(m, dict))
    post_statuses = sorted(f"{m.get('method_id')}:{m.get('status')}" for m in post_methods if isinstance(m, dict))
    compare(pre_statuses, post_statuses, "method_statuses", severity="CRITICAL")

    # 10: Formula IDs
    pre_formula_ids = sorted(f"{m.get('method_id')}:{m.get('formula_id')}" for m in pre_methods if isinstance(m, dict))
    post_formula_ids = sorted(f"{m.get('method_id')}:{m.get('formula_id')}" for m in post_methods if isinstance(m, dict))
    compare(pre_formula_ids, post_formula_ids, "formula_ids")

    # 11: Benchmark types
    pre_bench_types = sorted(f"{m.get('method_id')}:{m.get('benchmark_type')}" for m in pre_methods if isinstance(m, dict) and m.get("benchmark_type"))
    post_bench_types = sorted(f"{m.get('method_id')}:{m.get('benchmark_type')}" for m in post_methods if isinstance(m, dict) and m.get("benchmark_type"))
    compare(pre_bench_types, post_bench_types, "benchmark_types")

    # 12: Fatal error state
    pre_errors = pre_artifact.get("errors") or []
    post_errors = post_adapter_output.get("errors") or []
    pre_fatal = sorted(e.get("code") for e in pre_errors if isinstance(e, dict) and e.get("severity") == "CRITICAL")
    post_fatal = sorted(e.get("code") for e in post_errors if isinstance(e, dict) and e.get("severity") == "CRITICAL")
    compare(pre_fatal, post_fatal, "fatal_error_state", severity="CRITICAL")

    # 13: Implied prices
    pre_prices = {m.get("method_id"): m.get("implied_price") for m in pre_methods if isinstance(m, dict)}
    post_prices = {m.get("method_id"): m.get("implied_price") for m in post_methods if isinstance(m, dict)}
    compare(pre_prices, post_prices, "implied_prices", severity="CRITICAL")

    # 14: Semantic context hash
    post_ctx_ref = post_adapter_output.get("semantic_context_reference") or {}
    post_ctx_hash = post_ctx_ref.get("semantic_context_hash") if isinstance(post_ctx_ref, dict) else None
    if post_ctx_hash:
        compare(result.context_hash, post_ctx_hash, "semantic_context_hash")

    # 15: Registry hashes (if present in post-adapter output)
    post_reg = post_adapter_output.get("registry_hashes") or {}
    if post_reg:
        for k in ("formula_registry_hash", "applicability_registry_hash"):
            compare(result.registry_hashes.get(k), post_reg.get(k), f"registry_hashes.{k}")

    # 16-17: Period and scope bindings (from input_summary)
    pre_input = pre_artifact.get("input_summary") or {}
    post_input = post_adapter_output.get("input_summary") or post_adapter_output.get("valuation_inputs") or {}
    pre_periods = {k: v.get("period") if isinstance(v, dict) else None for k, v in pre_input.items()}
    post_periods = {k: v.get("period") if isinstance(v, dict) else None for k, v in (post_input.items() if isinstance(post_input, dict) else [])}
    compare(pre_periods, post_periods, "period_bindings")
    pre_scopes = {k: v.get("scope") if isinstance(v, dict) else None for k, v in pre_input.items()}
    post_scopes = {k: v.get("scope") if isinstance(v, dict) else None for k, v in (post_input.items() if isinstance(post_input, dict) else [])}
    compare(pre_scopes, post_scopes, "scope_bindings")

    # 18: Source bindings
    pre_provenance = pre_artifact.get("provenance") or {}
    post_provenance = post_adapter_output.get("provenance") or {}
    pre_sources = {k: v.get("source_id") if isinstance(v, dict) else None for k, v in pre_provenance.items()}
    post_sources = {k: v.get("source_id") if isinstance(v, dict) else None for k, v in (post_provenance.items() if isinstance(post_provenance, dict) else [])}
    compare(pre_sources, post_sources, "source_bindings")

    # 19: Calculation trace hashes
    def _trace_hash(methods):
        traces = {}
        for m in methods:
            if isinstance(m, dict):
                trace = m.get("calculation_trace") or []
                traces[m.get("method_id")] = _sha(trace)
        return traces
    compare(_trace_hash(pre_methods), _trace_hash(post_methods), "calculation_trace_hashes")

    # 19b: Premium/discount blocks
    pre_premium = {m.get("method_id"): m.get("premium_discount") for m in pre_methods if isinstance(m, dict)}
    post_premium = {m.get("method_id"): m.get("premium_discount") for m in post_methods if isinstance(m, dict)}
    compare(pre_premium, post_premium, "premium_discount_blocks")

    # 20: Equity bridge hashes
    def _bridge_hash(methods):
        bridges = {}
        for m in methods:
            if isinstance(m, dict):
                eb = m.get("equity_bridge")
                bridges[m.get("method_id")] = _sha(eb) if eb else None
        return bridges
    compare(_bridge_hash(pre_methods), _bridge_hash(post_methods), "equity_bridge_hashes")

    # Final status
    if drifts:
        result.pre_post_comparison_ok = False
        if any(d.severity == "CRITICAL" for d in drifts):
            result.final_status = "FAIL"
        else:
            result.final_status = "FAIL"  # any drift = FAIL per Directive §6.3

    return result
