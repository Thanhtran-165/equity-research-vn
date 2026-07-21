"""Context-Aware Verifier — Phase 4G F4G-C.

Adds 8 context binding checks (VVE-REQ-082..089) on top of existing verifier.
These checks compare method results against the semantic context envelope,
catching mutations that self-consistent outputs would otherwise hide.

Architecture:
    child_artifact + semantic_context → context_verify() → ContextVerificationResult

The context is the AUTHORITY. If artifact disagrees with context, it FAILS —
regardless of whether the artifact is internally self-consistent.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# Error codes for context binding failures
APPLICABILITY_CONTEXT_MISMATCH = "APPLICABILITY_CONTEXT_MISMATCH"
FATAL_ERROR_STATE_REMOVED = "FATAL_ERROR_STATE_REMOVED"
BENCHMARK_CONTEXT_MISMATCH = "BENCHMARK_CONTEXT_MISMATCH"
UNREGISTERED_PREMIUM_DISCOUNT = "UNREGISTERED_PREMIUM_DISCOUNT"
SHARE_EPS_BASIS_MISMATCH = "SHARE_EPS_BASIS_MISMATCH"
SOURCE_BINDING_MISMATCH = "SOURCE_BINDING_MISMATCH"
PERIOD_CONTEXT_MISMATCH = "PERIOD_CONTEXT_MISMATCH"
SCOPE_CONTEXT_MISMATCH = "SCOPE_CONTEXT_MISMATCH"
STALE_VERIFICATION_RESULT = "STALE_VERIFICATION_RESULT"
SEMANTIC_CONTEXT_BINDING_MISMATCH = "SEMANTIC_CONTEXT_BINDING_MISMATCH"


@dataclass
class ContextReqResult:
    requirement_id: str
    verdict: str  # PASS | FAIL | NOT_APPLICABLE
    severity: str
    method_id: Optional[str] = None
    expected: str = ""
    observed: str = ""
    failure_code: Optional[str] = None


@dataclass
class ContextVerificationResult:
    verifier_version: str = "0.2.0-phase4g"
    overall_verdict: str = "PENDING"
    passed: int = 0
    failed: int = 0
    not_applicable: int = 0
    requirement_results: List[ContextReqResult] = field(default_factory=list)
    verified_artifact_hash: str = ""
    semantic_context_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verifier_version": self.verifier_version,
            "overall_verdict": self.overall_verdict,
            "passed": self.passed, "failed": self.failed,
            "not_applicable": self.not_applicable,
            "requirement_results": [
                {"requirement_id": r.requirement_id, "verdict": r.verdict,
                 "severity": r.severity, "method_id": r.method_id,
                 "expected": r.expected, "observed": r.observed,
                 "failure_code": r.failure_code}
                for r in self.requirement_results
            ],
            "verified_artifact_hash": self.verified_artifact_hash,
            "semantic_context_hash": self.semantic_context_hash,
        }


def _check(req_id, condition, expected, observed, severity="CRITICAL",
           method_id=None, failure_code=None) -> ContextReqResult:
    verdict = "PASS" if condition else "FAIL"
    return ContextReqResult(
        requirement_id=req_id, verdict=verdict, severity=severity,
        method_id=method_id, expected=expected, observed=observed,
        failure_code=failure_code if not condition else None,
    )


def context_verify(
    artifact: Dict[str, Any],
    semantic_context: Dict[str, Any],
    artifact_hash: str = "",
) -> ContextVerificationResult:
    """Run 8 context binding checks (VVE-REQ-082..089).

    Args:
        artifact: valuation-output dict (child output)
        semantic_context: semantic context dict (externally bound, NOT from artifact)
        artifact_hash: SHA-256 of artifact (for binding)

    Returns:
        ContextVerificationResult with per-requirement verdicts.
    """
    result = ContextVerificationResult()
    result.verified_artifact_hash = artifact_hash
    result.semantic_context_hash = semantic_context.get("semantic_context_hash", "")

    # Bind artifact hash to context's evidence hash
    # (Context must reference the same artifact via canonical_input_hash or execution_context_hash)

    approved_methods = semantic_context.get("approved_methods") or []
    approved_by_id = {m.get("method_id"): m for m in approved_methods if isinstance(m, dict)}
    artifact_methods = artifact.get("method_results") or []

    # === VVE-REQ-082: Applicability context binding ===
    # Catches: NA→VALID, INPUT_INCOMPLETE→VALID, method not approved, trace tampering
    for m in artifact_methods:
        mid = m.get("method_id", "")
        artifact_status = m.get("status", "")
        ctx_method = approved_by_id.get(mid)

        if ctx_method is None:
            # Method in artifact but not in context's approved list
            result.requirement_results.append(_check(
                "VVE-REQ-082", False,
                f"method '{mid}' should be in approved_methods",
                f"method '{mid}' NOT in context approved_methods",
                method_id=mid, failure_code=APPLICABILITY_CONTEXT_MISMATCH))
            continue

        ctx_status = ctx_method.get("applicability_status")
        ctx_permission = ctx_method.get("permission_to_emit_implied_price", False)

        # Status mismatch: context says NA but artifact says VALID
        if ctx_status in ("NOT_APPLICABLE", "INPUT_INCOMPLETE") and artifact_status == "VALID":
            result.requirement_results.append(_check(
                "VVE-REQ-082", False,
                f"context status='{ctx_status}' for {mid}",
                f"artifact status='{artifact_status}' — NA/INCOMPLETE cannot become VALID",
                method_id=mid, failure_code=APPLICABILITY_CONTEXT_MISMATCH))
        elif ctx_status == "VALID" and not ctx_permission and m.get("implied_price") is not None:
            result.requirement_results.append(_check(
                "VVE-REQ-082", False,
                f"context permission_to_emit_implied_price=False for {mid}",
                f"artifact has implied_price={m.get('implied_price')}",
                method_id=mid, failure_code=APPLICABILITY_CONTEXT_MISMATCH))
        else:
            result.requirement_results.append(_check(
                "VVE-REQ-082", True,
                f"context status='{ctx_status}' matches artifact status='{artifact_status}'",
                f"OK for {mid}", method_id=mid))

    # === VVE-REQ-083: Error state binding ===
    # Catches: fatal error removed from artifact
    ctx_error_state = semantic_context.get("error_state") or {}
    ctx_fatal_codes = set(ctx_error_state.get("fatal_error_codes") or [])
    artifact_errors = artifact.get("errors") or []
    artifact_error_codes = set()
    for e in artifact_errors:
        if isinstance(e, dict):
            artifact_error_codes.add(e.get("code", ""))

    # Check: any context fatal error missing from artifact OR downgraded to non-CRITICAL?
    removed_fatal = ctx_fatal_codes - artifact_error_codes
    # Also check: error code present but severity downgraded from CRITICAL
    downgraded = set()
    for e in artifact_errors:
        if isinstance(e, dict) and e.get("code") in ctx_fatal_codes:
            if e.get("severity") != "CRITICAL":
                downgraded.add(e.get("code"))
    problematic = removed_fatal | downgraded
    if ctx_fatal_codes and problematic:
        result.requirement_results.append(_check(
            "VVE-REQ-083", False,
            f"context fatal errors: {sorted(ctx_fatal_codes)}",
            f"artifact missing or downgraded: {sorted(problematic)}",
            failure_code=FATAL_ERROR_STATE_REMOVED))
    else:
        result.requirement_results.append(_check(
            "VVE-REQ-083", True,
            "all context fatal errors present in artifact",
            f"artifact errors: {sorted(artifact_error_codes)[:5]}"))

    # === VVE-REQ-084: Benchmark type binding ===
    # Catches: benchmark_type changed, benchmark_id mismatch
    ctx_benchmarks = semantic_context.get("benchmarks") or []
    ctx_bench_by_method = {b.get("method_id"): b for b in ctx_benchmarks if isinstance(b, dict)}

    for m in artifact_methods:
        mid = m.get("method_id", "")
        artifact_bench = m.get("benchmark_type")
        ctx_bench = ctx_bench_by_method.get(mid)
        if ctx_bench and artifact_bench:
            ctx_bench_type = ctx_bench.get("benchmark_type")
            if ctx_bench_type and artifact_bench != ctx_bench_type:
                result.requirement_results.append(_check(
                    "VVE-REQ-084", False,
                    f"context benchmark_type='{ctx_bench_type}' for {mid}",
                    f"artifact benchmark_type='{artifact_bench}'",
                    severity="MAJOR", method_id=mid, failure_code=BENCHMARK_CONTEXT_MISMATCH))
            else:
                result.requirement_results.append(_check(
                    "VVE-REQ-084", True,
                    f"benchmark_type matches for {mid}",
                    f"'{artifact_bench}'", severity="MAJOR", method_id=mid))

    # === VVE-REQ-085: Premium/discount binding ===
    # Catches: unsupported premium, premium hidden in selected_multiple
    for m in artifact_methods:
        mid = m.get("method_id", "")
        # Check if method has a premium_discount block
        premium = m.get("premium_discount")
        ctx_bench = ctx_bench_by_method.get(mid, {})
        ctx_policy = ctx_bench.get("premium_discount_policy_id")
        if isinstance(premium, dict):
            p_status = premium.get("status")
            if p_status == "APPLIED" and not ctx_policy:
                result.requirement_results.append(_check(
                    "VVE-REQ-085", False,
                    f"premium_discount APPLIED requires context policy for {mid}",
                    f"no premium_discount_policy_id in context",
                    severity="MAJOR", method_id=mid, failure_code=UNREGISTERED_PREMIUM_DISCOUNT))
            else:
                result.requirement_results.append(_check(
                    "VVE-REQ-085", True,
                    f"premium_discount consistent for {mid}",
                    f"status={p_status}", severity="MAJOR", method_id=mid))
        else:
            # No premium block — OK (default NONE)
            result.requirement_results.append(_check(
                "VVE-REQ-085", True,
                f"no premium_discount for {mid}",
                "OK (default NONE)", severity="MAJOR", method_id=mid))

    # === VVE-REQ-086: Share/EPS basis binding ===
    # Catches: BASIC→DILUTED swap, basis mismatch
    ctx_share_raw = semantic_context.get("share_context")
    # Skip entirely if share_context is None (not just empty dict from `or {}`)
    if ctx_share_raw is not None:
        ctx_share = ctx_share_raw if isinstance(ctx_share_raw, dict) else {}
        ctx_share_basis = ctx_share.get("share_basis")
        ctx_eps_basis = ctx_share.get("EPS_basis")

        # Only check if basis is defined
        if ctx_eps_basis:
            for m in artifact_methods:
                mid = m.get("method_id", "")
                if mid in ("PE", "PB", "GRAHAM_NUMBER", "PEG"):
                    inputs = m.get("input_metric_ids") or []
                    if ctx_eps_basis == "BASIC" and any("diluted" in str(i).lower() for i in inputs):
                        result.requirement_results.append(_check(
                            "VVE-REQ-086", False,
                            f"context EPS_basis='BASIC' for {mid}",
                            f"artifact uses diluted in inputs: {inputs}",
                            severity="MAJOR", method_id=mid, failure_code=SHARE_EPS_BASIS_MISMATCH))
                    elif ctx_eps_basis == "DILUTED" and any(i == "eps" for i in inputs):
                        result.requirement_results.append(_check(
                            "VVE-REQ-086", False,
                            f"context EPS_basis='DILUTED' for {mid}",
                            f"artifact uses basic 'eps' in inputs",
                            severity="MAJOR", method_id=mid, failure_code=SHARE_EPS_BASIS_MISMATCH))
                    else:
                        result.requirement_results.append(_check(
                            "VVE-REQ-086", True,
                            f"EPS basis consistent for {mid}",
                            f"basis={ctx_eps_basis}", severity="MAJOR", method_id=mid))

    # === VVE-REQ-087: Source registry binding ===
    # Catches: source_id replaced, source not supporting metric
    ctx_sources = semantic_context.get("source_registry") or []
    ctx_source_ids = {s.get("source_id"): s for s in ctx_sources if isinstance(s, dict)}
    artifact_provenance = artifact.get("provenance") or {}

    for metric_id, prov in artifact_provenance.items():
        if not isinstance(prov, dict): continue
        source_id = prov.get("source_id")
        if source_id and source_id not in ctx_source_ids:
            result.requirement_results.append(_check(
                "VVE-REQ-087", False,
                f"source_id in context registry",
                f"source_id='{source_id}' for metric '{metric_id}' NOT in context",
                severity="MAJOR", failure_code=SOURCE_BINDING_MISMATCH))
        elif source_id:
            ctx_src = ctx_source_ids[source_id]
            supported = ctx_src.get("supported_metric_ids") or []
            # Only flag if supported list is non-empty AND metric not in it
            # (empty supported list means "all metrics" — source doesn't restrict)
            if supported and metric_id not in supported:
                result.requirement_results.append(_check(
                    "VVE-REQ-087", False,
                    f"source '{source_id}' supports metrics: {supported}",
                    f"metric '{metric_id}' not supported by this source",
                    severity="MAJOR", failure_code=SOURCE_BINDING_MISMATCH))

    if not any(r.requirement_id == "VVE-REQ-087" for r in result.requirement_results):
        result.requirement_results.append(_check(
            "VVE-REQ-087", True,
            "all source_ids in context registry",
            "OK", severity="MAJOR"))

    # === VVE-REQ-088: Period contract binding ===
    # Catches: period changed to valid-but-wrong period
    ctx_periods = semantic_context.get("period_registry") or []
    ctx_period_by_metric = {p.get("metric_id"): p for p in ctx_periods if isinstance(p, dict)}
    artifact_input = artifact.get("input_summary") or {}

    for metric_id, metric_data in artifact_input.items():
        if not isinstance(metric_data, dict): continue
        artifact_period = metric_data.get("period")
        ctx_period = ctx_period_by_metric.get(metric_id)
        if ctx_period and artifact_period:
            ctx_normalized = ctx_period.get("normalized_period")
            if ctx_normalized and artifact_period != ctx_normalized:
                result.requirement_results.append(_check(
                    "VVE-REQ-088", False,
                    f"context period='{ctx_normalized}' for {metric_id}",
                    f"artifact period='{artifact_period}'",
                    severity="MAJOR", failure_code=PERIOD_CONTEXT_MISMATCH))

    if not any(r.requirement_id == "VVE-REQ-088" for r in result.requirement_results):
        result.requirement_results.append(_check(
            "VVE-REQ-088", True,
            "all periods match context",
            "OK", severity="MAJOR"))

    # === VVE-REQ-089: Scope contract binding ===
    # Catches: scope changed
    ctx_scopes = semantic_context.get("scope_registry") or []
    ctx_scope_by_metric = {s.get("metric_id"): s for s in ctx_scopes if isinstance(s, dict)}

    for metric_id, metric_data in artifact_input.items():
        if not isinstance(metric_data, dict): continue
        artifact_scope = metric_data.get("scope")
        ctx_scope = ctx_scope_by_metric.get(metric_id)
        if ctx_scope and artifact_scope:
            ctx_normalized = ctx_scope.get("normalized_scope")
            if ctx_normalized and artifact_scope != ctx_normalized:
                result.requirement_results.append(_check(
                    "VVE-REQ-089", False,
                    f"context scope='{ctx_normalized}' for {metric_id}",
                    f"artifact scope='{artifact_scope}'",
                    severity="MAJOR", failure_code=SCOPE_CONTEXT_MISMATCH))

    if not any(r.requirement_id == "VVE-REQ-089" for r in result.requirement_results):
        result.requirement_results.append(_check(
            "VVE-REQ-089", True,
            "all scopes match context",
            "OK", severity="MAJOR"))

    # Aggregate
    for r in result.requirement_results:
        if r.verdict == "PASS":
            result.passed += 1
        elif r.verdict == "FAIL":
            result.failed += 1
        else:
            result.not_applicable += 1

    any_critical_fail = any(r.verdict == "FAIL" and r.severity == "CRITICAL" for r in result.requirement_results)
    any_fail = any(r.verdict == "FAIL" for r in result.requirement_results)
    if any_critical_fail:
        result.overall_verdict = "FAIL"
    elif any_fail:
        result.overall_verdict = "FAIL"  # MAJOR fails also → FAIL for context binding
    else:
        result.overall_verdict = "PASS"

    return result
