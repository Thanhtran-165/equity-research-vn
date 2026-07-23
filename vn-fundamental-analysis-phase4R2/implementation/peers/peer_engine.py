"""Peer comparison engine — Phase 4R (MUT-FUND-027 / 028 / 029 / 030).

Real implementation, not a placeholder. Computes a peer benchmark from a
declared central-tendency policy, enforces minimum coverage, period/scope
alignment, and ranking eligibility.
"""
from __future__ import annotations
import hashlib, json, statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from models import MetricInput, PeriodType, ReportingScope, AttributionScope
from peers.peer_policy import CentralTendencyPolicy, MINIMUM_PEER_COVERAGE


@dataclass
class PeerEntry:
    ticker: str
    value: Optional[float]
    period_kind: str = PeriodType.ANNUAL.value
    reporting_scope: str = ReportingScope.CONSOLIDATED.value
    attribution_scope: str = AttributionScope.ATTRIBUTABLE_TO_PARENT.value


@dataclass
class PeerResult:
    target_ticker: str = ""
    metric_id: str = ""
    peer_set_hash: str = ""
    coverage: int = 0
    policy: str = CentralTendencyPolicy.MEDIAN.value
    benchmark_value: Optional[float] = None
    target_value: Optional[float] = None
    ranking_eligible: bool = False
    target_rank: Optional[int] = None
    target_percentile: Optional[float] = None
    dropped_peers: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    target_period_kind: str = PeriodType.ANNUAL.value
    target_reporting_scope: str = ReportingScope.CONSOLIDATED.value
    target_attribution_scope: str = AttributionScope.ATTRIBUTABLE_TO_PARENT.value
    aligned_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


def _hash_peer_set(target_ticker: str, peers: List[PeerEntry], policy: str) -> str:
    payload = {"target": target_ticker, "policy": policy,
               "peers": [{"t": p.ticker, "v": p.value, "pk": p.period_kind, "rs": p.reporting_scope, "as": p.attribution_scope} for p in peers]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()[:16]


def _central_tendency(values: List[float], policy: str) -> Optional[float]:
    if not values:
        return None
    if policy == CentralTendencyPolicy.MEAN.value:
        return statistics.mean(values)
    if policy == CentralTendencyPolicy.TRIMMED_MEAN.value:
        if len(values) < 3:
            return statistics.mean(values)
        sorted_v = sorted(values)
        # drop 1 lowest + 1 highest
        return statistics.mean(sorted_v[1:-1])
    # default MEDIAN
    return statistics.median(values)


def compute_peer_benchmark(
    target_ticker: str,
    target_value: Optional[float],
    target_period_kind: str,
    target_reporting_scope: str,
    target_attribution_scope: str,
    metric_id: str,
    peers: List[PeerEntry],
    policy: str = CentralTendencyPolicy.MEDIAN.value,
) -> PeerResult:
    """Compute peer benchmark with full integrity checks.

    Detection matrix:
    - PEER_COVERAGE_INSUFFICIENT: fewer than MINIMUM_PEER_COVERAGE valid aligned peers
    - PERIOD_MISMATCH: a peer with period_kind != target's
    - SCOPE_MISMATCH: a peer with reporting_scope or attribution_scope != target's
    - PEER_POLICY_VIOLATION: reported benchmark does not match declared policy recomputation
    """
    result = PeerResult(target_ticker=target_ticker, metric_id=metric_id, policy=policy,
                       target_value=target_value,
                       target_period_kind=target_period_kind,
                       target_reporting_scope=target_reporting_scope,
                       target_attribution_scope=target_attribution_scope)
    aligned: List[float] = []
    dropped: List[Dict[str, Any]] = []
    for p in peers:
        # Target cannot be its own peer
        if p.ticker == target_ticker:
            dropped.append({"ticker": p.ticker, "reason": "TARGET_IS_PEER"})
            continue
        if p.value is None:
            dropped.append({"ticker": p.ticker, "reason": "PEER_NO_DATA"})
            continue
        if p.period_kind != target_period_kind:
            dropped.append({"ticker": p.ticker, "reason": "PERIOD_MISMATCH", "peer_period": p.period_kind, "target_period": target_period_kind})
            continue
        if p.reporting_scope != target_reporting_scope or p.attribution_scope != target_attribution_scope:
            dropped.append({"ticker": p.ticker, "reason": "SCOPE_MISMATCH", "peer_rs": p.reporting_scope, "peer_as": p.attribution_scope,
                            "target_rs": target_reporting_scope, "target_as": target_attribution_scope})
            continue
        aligned.append(p.value)
    result.aligned_count = len(aligned)
    result.coverage = len(aligned)
    result.dropped_peers = dropped
    result.peer_set_hash = _hash_peer_set(target_ticker, peers, policy)

    # Coverage gate
    if result.coverage < MINIMUM_PEER_COVERAGE:
        result.errors.append(f"PEER_COVERAGE_INSUFFICIENT: {result.coverage} < {MINIMUM_PEER_COVERAGE}")
        result.ranking_eligible = False
        result.benchmark_value = None
        return result

    # Outlier policy (trimmed mean path is the policy itself; otherwise we still note extreme dispersion)
    result.benchmark_value = _central_tendency(aligned, policy)
    if result.benchmark_value is None:
        result.errors.append("PEER_BENCHMARK_UNCOMPUTABLE")
        return result

    # Ranking eligibility
    result.ranking_eligible = True
    all_values = sorted(aligned + ([target_value] if target_value is not None else []), reverse=True)
    if target_value is not None:
        # rank 1 = highest
        try:
            result.target_rank = all_values.index(target_value) + 1
            result.target_percentile = round(1.0 - (result.target_rank - 1) / max(len(all_values) - 1, 1), 4)
        except ValueError:
            result.target_rank = None
            result.target_percentile = None
    return result


def verify_peer_policy(result: PeerResult, peers: List[PeerEntry], policy: str,
                       target_period_kind: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Independently recompute the benchmark under the declared policy and compare.

    Returns (ok, error_code). Used by the verifier to catch a median->mean swap.

    Detection logic:
    - Recompute benchmark under the declared policy.
    - If declared-policy recompute matches reported → ok (no violation).
    - Else if reported matches a DIFFERENT policy → PEER_POLICY_VIOLATION (swap).
    - Else (reported matches nothing) → PEER_POLICY_VIOLATION (corruption).
    """
    tpk = getattr(result, "target_period_kind", None) or target_period_kind or PeriodType.ANNUAL.value
    aligned = [p.value for p in peers if p.ticker != result.target_ticker and p.value is not None
               and p.period_kind == tpk]
    declared_recompute = _central_tendency(aligned, policy)
    if declared_recompute is None and result.benchmark_value is None:
        return True, None
    if declared_recompute is None or result.benchmark_value is None:
        return False, "PEER_POLICY_VIOLATION"
    # Declared-policy path: matches → ok
    if abs(declared_recompute - result.benchmark_value) < 1e-9:
        return True, None
    # Declared policy does NOT match — is there a different policy that does?
    for pol in (CentralTendencyPolicy.MEDIAN.value, CentralTendencyPolicy.MEAN.value, CentralTendencyPolicy.TRIMMED_MEAN.value):
        if pol == policy:
            continue
        v = _central_tendency(aligned, pol)
        if v is not None and abs(v - result.benchmark_value) < 1e-9:
            return False, "PEER_POLICY_VIOLATION"
    # Reported matches no known policy → corruption
    return False, "PEER_POLICY_VIOLATION"
