"""Phase 4R peer engine tests (MUT-FUND-027 / 028 / 029 / 030).

16 tests covering peer set integrity, coverage gate, policy swap detection,
period misalignment, ranking eligibility, target-as-peer, no-data peer,
trimmed mean, hash stability, and verifier-side recompute.
"""
import sys, pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "implementation"))

from models import PeriodType, ReportingScope, AttributionScope
from peers.peer_engine import compute_peer_benchmark, PeerEntry, verify_peer_policy, PeerResult
from peers.peer_policy import CentralTendencyPolicy, MINIMUM_PEER_COVERAGE


def _peer(ticker, value, period_kind=PeriodType.ANNUAL.value, rs=ReportingScope.CONSOLIDATED.value, as_=AttributionScope.ATTRIBUTABLE_TO_PARENT.value):
    return PeerEntry(ticker=ticker, value=value, period_kind=period_kind, reporting_scope=rs, attribution_scope=as_)


def test_p4r_peer_001_peer_removed_coverage_drop():
    """P4R-TEST-PEER-001: removing peers drops coverage below minimum → PEER_COVERAGE_INSUFFICIENT."""
    peers = [_peer("CMG", 15.0), _peer("ELC", 16.0)]  # only 2 peers
    pr = compute_peer_benchmark("FPT", 14.0, PeriodType.ANNUAL.value,
                                ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                                "ROE", peers, CentralTendencyPolicy.MEDIAN.value)
    assert pr.coverage < MINIMUM_PEER_COVERAGE
    assert any("PEER_COVERAGE_INSUFFICIENT" in e for e in pr.errors)
    assert pr.ranking_eligible is False


def test_p4r_peer_001b_clean_three_peers_passes():
    """3 valid aligned peers → ok, ranking eligible."""
    peers = [_peer("CMG", 15.0), _peer("ELC", 16.0), _peer("ITD", 14.5)]
    pr = compute_peer_benchmark("FPT", 14.0, PeriodType.ANNUAL.value,
                                ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                                "ROE", peers, CentralTendencyPolicy.MEDIAN.value)
    assert pr.coverage == 3
    assert pr.ranking_eligible is True
    assert pr.benchmark_value == 15.0  # median of [14.5, 15.0, 16.0]


def test_p4r_peer_002_median_mean_policy_swap_detected():
    """P4R-TEST-PEER-002: declaring MEDIAN but reporting MEAN value → PEER_POLICY_VIOLATION."""
    peers = [_peer("CMG", 10.0), _peer("ELC", 20.0), _peer("ITD", 30.0)]
    # Median = 20.0, Mean = 20.0 -> degenerate (all equal). Use asymmetric values.
    peers = [_peer("CMG", 10.0), _peer("ELC", 15.0), _peer("ITD", 30.0)]
    # Median = 15.0, Mean = 18.33
    pr = compute_peer_benchmark("FPT", 12.0, PeriodType.ANNUAL.value,
                                ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                                "ROE", peers, CentralTendencyPolicy.MEDIAN.value)
    assert pr.benchmark_value == 15.0  # correct median
    # Now corrupt: report mean but declare median
    pr_corrupt = PeerResult(target_ticker="FPT", metric_id="ROE", policy=CentralTendencyPolicy.MEDIAN.value,
                           benchmark_value=18.33, coverage=3)  # mean masquerading as median
    ok, err = verify_peer_policy(pr_corrupt, peers, CentralTendencyPolicy.MEDIAN.value,
                                 target_period_kind=PeriodType.ANNUAL.value)
    assert ok is False
    assert err == "PEER_POLICY_VIOLATION"


def test_p4r_peer_003_peer_period_misalignment_dropped():
    """P4R-TEST-PEER-003: peer with different period_kind is dropped."""
    peers = [_peer("CMG", 15.0), _peer("ELC", 16.0, period_kind=PeriodType.QUARTERLY.value), _peer("ITD", 14.5)]
    pr = compute_peer_benchmark("FPT", 14.0, PeriodType.ANNUAL.value,
                                ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                                "ROE", peers, CentralTendencyPolicy.MEDIAN.value)
    # ELC dropped for period mismatch
    assert any(d["ticker"] == "ELC" and d["reason"] == "PERIOD_MISMATCH" for d in pr.dropped_peers)
    # Only 2 aligned -> coverage insufficient
    assert pr.coverage == 2
    assert any("PEER_COVERAGE_INSUFFICIENT" in e for e in pr.errors)


def test_p4r_peer_004_insufficient_coverage_still_ranked_blocked():
    """P4R-TEST-PEER-004: ranking blocked when coverage < 3."""
    peers = [_peer("CMG", 15.0)]  # only 1
    pr = compute_peer_benchmark("FPT", 14.0, PeriodType.ANNUAL.value,
                                ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                                "ROE", peers, CentralTendencyPolicy.MEDIAN.value)
    assert pr.ranking_eligible is False
    assert pr.target_rank is None


def test_p4r_peer_target_is_peer_dropped():
    """Target cannot be its own peer."""
    peers = [_peer("FPT", 14.0), _peer("CMG", 15.0), _peer("ELC", 16.0), _peer("ITD", 14.5)]
    pr = compute_peer_benchmark("FPT", 14.0, PeriodType.ANNUAL.value,
                                ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                                "ROE", peers, CentralTendencyPolicy.MEDIAN.value)
    assert any(d["ticker"] == "FPT" and d["reason"] == "TARGET_IS_PEER" for d in pr.dropped_peers)
    assert pr.coverage == 3  # 3 aligned after dropping FPT


def test_p4r_peer_no_data_peer_dropped():
    """Peer with None value is dropped."""
    peers = [_peer("CMG", None), _peer("ELC", 16.0), _peer("ITD", 14.5), _peer("KHG", 15.5)]
    pr = compute_peer_benchmark("FPT", 14.0, PeriodType.ANNUAL.value,
                                ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                                "ROE", peers, CentralTendencyPolicy.MEDIAN.value)
    assert any(d["ticker"] == "CMG" and d["reason"] == "PEER_NO_DATA" for d in pr.dropped_peers)
    assert pr.coverage == 3


def test_p4r_peer_scope_mismatch_dropped():
    """Peer with different scope is dropped."""
    peers = [_peer("CMG", 15.0, rs=ReportingScope.STANDALONE.value), _peer("ELC", 16.0), _peer("ITD", 14.5)]
    pr = compute_peer_benchmark("FPT", 14.0, PeriodType.ANNUAL.value,
                                ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                                "ROE", peers, CentralTendencyPolicy.MEDIAN.value)
    assert any(d["ticker"] == "CMG" and d["reason"] == "SCOPE_MISMATCH" for d in pr.dropped_peers)


def test_p4r_peer_mean_policy_computes_mean():
    peers = [_peer("CMG", 10.0), _peer("ELC", 20.0), _peer("ITD", 30.0)]
    pr = compute_peer_benchmark("FPT", 12.0, PeriodType.ANNUAL.value,
                                ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                                "ROE", peers, CentralTendencyPolicy.MEAN.value)
    assert pr.benchmark_value == 20.0  # mean


def test_p4r_peer_trimmed_mean_drops_outliers():
    """Trimmed mean drops 1 lowest + 1 highest."""
    peers = [_peer("CMG", 10.0), _peer("ELC", 15.0), _peer("ITD", 16.0), _peer("KHG", 17.0), _peer("MZD", 100.0)]
    pr = compute_peer_benchmark("FPT", 12.0, PeriodType.ANNUAL.value,
                                ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                                "ROE", peers, CentralTendencyPolicy.TRIMMED_MEAN.value)
    # Trimmed: drop 10.0 and 100.0; mean of [15,16,17] = 16.0
    assert pr.benchmark_value == 16.0


def test_p4r_peer_set_hash_stable():
    """Same peer set → same hash."""
    peers = [_peer("CMG", 15.0), _peer("ELC", 16.0), _peer("ITD", 14.5)]
    pr1 = compute_peer_benchmark("FPT", 14.0, PeriodType.ANNUAL.value,
                                 ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                                 "ROE", peers, CentralTendencyPolicy.MEDIAN.value)
    pr2 = compute_peer_benchmark("FPT", 14.0, PeriodType.ANNUAL.value,
                                 ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                                 "ROE", peers, CentralTendencyPolicy.MEDIAN.value)
    assert pr1.peer_set_hash == pr2.peer_set_hash


def test_p4r_peer_set_hash_changes_on_peer_removal():
    """Removing a peer → different hash."""
    full = [_peer("CMG", 15.0), _peer("ELC", 16.0), _peer("ITD", 14.5)]
    reduced = [_peer("CMG", 15.0), _peer("ELC", 16.0), _peer("KHG", 18.0)]
    pr1 = compute_peer_benchmark("FPT", 14.0, PeriodType.ANNUAL.value,
                                 ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                                 "ROE", full, CentralTendencyPolicy.MEDIAN.value)
    pr2 = compute_peer_benchmark("FPT", 14.0, PeriodType.ANNUAL.value,
                                 ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                                 "ROE", reduced, CentralTendencyPolicy.MEDIAN.value)
    assert pr1.peer_set_hash != pr2.peer_set_hash


def test_p4r_peer_target_rank_computed():
    peers = [_peer("CMG", 10.0), _peer("ELC", 12.0), _peer("ITD", 14.0)]
    pr = compute_peer_benchmark("FPT", 13.0, PeriodType.ANNUAL.value,
                                ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                                "ROE", peers, CentralTendencyPolicy.MEDIAN.value)
    assert pr.target_rank is not None
    # sorted desc: [14, 13, 12, 10]; FPT=13 -> rank 2
    assert pr.target_rank == 2


def test_p4r_peer_verify_policy_clean_pass():
    peers = [_peer("CMG", 10.0), _peer("ELC", 15.0), _peer("ITD", 30.0)]
    pr = compute_peer_benchmark("FPT", 12.0, PeriodType.ANNUAL.value,
                                ReportingScope.CONSOLIDATED.value, AttributionScope.ATTRIBUTABLE_TO_PARENT.value,
                                "ROE", peers, CentralTendencyPolicy.MEDIAN.value)
    ok, err = verify_peer_policy(pr, peers, CentralTendencyPolicy.MEDIAN.value)
    assert ok is True
    assert err is None


def test_p4r_peer_policy_swap_to_mean_detected():
    """Declaring MEDIAN but computing MEAN → violation."""
    peers = [_peer("CMG", 10.0), _peer("ELC", 15.0), _peer("ITD", 30.0)]
    # correct median = 15.0, mean = 18.33
    pr_wrong = PeerResult(target_ticker="FPT", metric_id="ROE",
                          policy=CentralTendencyPolicy.MEDIAN.value,
                          benchmark_value=18.333333, coverage=3)
    ok, err = verify_peer_policy(pr_wrong, peers, CentralTendencyPolicy.MEDIAN.value,
                                 target_period_kind=PeriodType.ANNUAL.value)
    assert ok is False
    assert err == "PEER_POLICY_VIOLATION"


def test_p4r_peer_runner_integration_end_to_end():
    """End-to-end: runner with peer_set produces a complete peer_comparison block."""
    from models import FundamentalRequest, MetricInput
    from runner import run_fundamental

    def _metric(mid, values, periods=None, **kw):
        n = len(values)
        if periods is None: periods = list(range(2025-n+1, 2026))
        defaults = dict(unit="BILLION_VND", periods=periods, scope="CONSOLIDATED", source_id="t")
        defaults.update(kw)
        return MetricInput(metric_id=mid, values=values, **defaults)

    req = FundamentalRequest(
        ticker="FPT", periods=[2023, 2024, 2025],
        metrics={
            "revenue": _metric("revenue", [35000, 40000, 45000]),
            "net_income": _metric("net_income", [5000, 5500, 6000]),
            "equity": _metric("equity", [30000, 33000, 36000]),
            "total_assets": _metric("total_assets", [60000, 66000, 72000]),
            "shares_outstanding": _metric("shares_outstanding", [1.5, 1.5, 1.5]),
        },
        peer_set=[
            {"ticker": "CMG", "value": 15.0},
            {"ticker": "ELC", "value": 16.0},
            {"ticker": "ITD", "value": 14.5},
        ],
        peer_policy="MEDIAN",
    )
    res = run_fundamental(req)
    pc = res.output.peer_comparison
    assert pc["coverage"] == 3
    assert pc["ranking_eligible"] is True
    assert pc["benchmark_value"] == 15.0  # median of [14.5, 15.0, 16.0]
    assert pc["policy"] == "MEDIAN"
    assert pc["target_period_kind"] is not None
