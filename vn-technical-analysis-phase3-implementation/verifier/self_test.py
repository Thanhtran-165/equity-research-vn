"""Self-test harness for the VTA Phase 3 independent verifier.

This module asserts the verifier's structural contracts without consulting
any production code. It is intended to be run after any verifier change:

    python3 -m verifier.self_test

The harness exercises:

  1. Import cleanliness (no production decision module imported).
  2. Independence guard (the runtime guard rejects a forbidden module).
  3. 64-VC coverage and domain disjointness against the frozen VC mapping.
  4. Per-domain handler completeness.
  5. Deterministic record ordering across two runs.
  6. Result-schema completeness on every record.
  7. Verdict switching on controlled positive/negative synthetic fixtures
     (a representative sample across all six domains).

The harness constructs synthetic fixtures inline; it does NOT consume
production output. It is itself part of the verifier's independence boundary.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from typing import Any, Callable, Dict, List, Tuple

from . import (
    boundary_enforcement,
    formula_conformance,
    language_policy,
    provenance_integrity,
    schema_conformance,
    setup_semantics,
)
from . import vta_verifier
from .common import (
    STATUS_FAIL,
    STATUS_PASS,
    unwrap_vc_mapping,
    load_yaml,
)

# Default paths to the frozen authorities (review manifests).
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
_REVIEW = os.path.join(
    os.path.dirname(_REPO), "vn-technical-analysis-phase3-review", "manifests"
)
FORMULA_CONTRACTS = os.path.join(_REVIEW, "vta-formula-contract-registry.yaml")
FAILURE_REGISTRY = os.path.join(_REVIEW, "vta-failure-code-registry.yaml")
VC_MAPPING = os.path.join(_REVIEW, "vta-VC-to-verifier-mapping.yaml")


# ===========================================================================
# Assertion helpers
# ===========================================================================


class SelfTestFailure(Exception):
    pass


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestFailure(message)


# ===========================================================================
# Test 1: import cleanliness
# ===========================================================================


def test_import_cleanliness() -> None:
    forbidden = (
        "normalization_engine",
        "indicator_engine",
        "profile_engine",
        "output_assembler",
        "integration_adapter",
        "language_verifier",
        "runner",
    )
    loaded = set(sys.modules.keys())
    offenders = sorted(loaded & set(forbidden))
    _check(
        not offenders,
        f"production decision modules loaded in verifier process: {offenders}",
    )


# ===========================================================================
# Test 2: independence guard rejects a forbidden module
# ===========================================================================


def test_independence_guard() -> None:
    """Inject a forbidden module name into sys.modules and confirm the guard
    raises. Restore state afterwards."""
    import types

    stub = types.ModuleType("indicator_engine")
    sys.modules["indicator_engine"] = stub
    try:
        try:
            vta_verifier._assert_independence()
            raise SelfTestFailure(
                "independence guard did not raise on forbidden module"
            )
        except RuntimeError as exc:
            _check(
                "indicator_engine" in str(exc),
                f"guard raised but message lacks offender: {exc}",
            )
    finally:
        sys.modules.pop("indicator_engine", None)


# ===========================================================================
# Test 3: 64-VC coverage and domain disjointness
# ===========================================================================


def test_coverage_and_disjointness() -> None:
    mapping_doc = load_yaml(VC_MAPPING)
    mapping = unwrap_vc_mapping(mapping_doc)
    canonical = [
        rec["VC_id"]
        for rec in mapping.get("verifier_checks", [])
        if rec.get("VC_id")
    ]
    canonical_set = set(canonical)
    _check(len(canonical) == 64, f"expected 64 canonical VCs, got {len(canonical)}")
    _check(
        len(canonical_set) == 64,
        f"expected 64 unique canonical VCs, got {len(canonical_set)}",
    )

    domains = [
        formula_conformance,
        schema_conformance,
        provenance_integrity,
        language_policy,
        boundary_enforcement,
        setup_semantics,
    ]
    expected_counts = {
        "formula_conformance": 15,
        "schema_conformance": 23,
        "provenance_integrity": 6,
        "language_policy": 5,
        "boundary_enforcement": 3,
        "setup_semantics": 12,
    }
    owned: List[str] = []
    for domain in domains:
        owned_set = set(domain.OWNED_VC_IDS)
        _check(
            len(owned_set) == expected_counts[domain.DOMAIN_NAME],
            f"{domain.DOMAIN_NAME} owns {len(owned_set)} VCs, "
            f"expected {expected_counts[domain.DOMAIN_NAME]}",
        )
        _check(
            owned_set <= canonical_set,
            f"{domain.DOMAIN_NAME} owns VCs outside canonical set: "
            f"{sorted(owned_set - canonical_set)}",
        )
        _check(
            owned_set == set(domain._HANDLERS.keys()),
            f"{domain.DOMAIN_NAME} handler table does not match OWNED_VC_IDS",
        )
        owned.extend(domain.OWNED_VC_IDS)

    _check(
        len(owned) == len(set(owned)) == 64,
        f"domains are not disjoint or do not total 64: total={len(owned)}, "
        f"unique={len(set(owned))}",
    )


# ===========================================================================
# Test 4 + 5: end-to-end determinism + schema completeness
# ===========================================================================


def _synthetic_packet_and_fixture() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    import math

    closes = [100.0 + 2.0 * math.sin(i / 3.0) + i * 0.05 for i in range(60)]
    volumes = [1000 + 50 * i for i in range(60)]
    dates = [f"2025-01-{(i % 28) + 1:02d}" for i in range(60)]
    ohlcv = [
        {
            "date": d,
            "open": c - 0.1,
            "high": c + 0.5,
            "low": c - 0.5,
            "close": c,
            "volume": v,
            "adjustment_status": "ADJUSTED",
        }
        for d, c, v in zip(dates, closes, volumes)
    ]
    chain = [
        {"indicator_id": "RSI", "price_basis": "adjusted", "period": 14, "value": 55.0},
        {"indicator_id": "BB", "price_basis": "adjusted", "window": 20, "value": closes[-1]},
        {"indicator_id": "MA", "price_basis": "adjusted", "window": 21, "value": closes[-1]},
        {"indicator_id": "MACD", "price_basis": "adjusted", "value": 0.1},
        {
            "indicator_id": "Beta",
            "price_basis": "total_return_adjusted",
            "calculation": "beta",
            "value": 1.0,
        },
        {"indicator_id": "CMF", "price_basis": "adjusted", "value": 0.05},
    ]
    packet = {
        "mode": "ACTIVE",
        "as_of_date": "2025-03-31",
        "ticker": "TEST",
        "weekly_history": 52,
        "indicators": {
            "RSI": {"rsi_value": 55.0, "provenance": {"period": 14}},
            "BB": {
                "middle_value": closes[-1],
                "upper_value": closes[-1] + 1,
                "lower_value": closes[-1] - 1,
                "window": 20,
                "multiplier": 2.0,
                "std_convention": "POPULATION_DIV_N",
            },
            "MA": {"ma_values": {"21": closes[-1]}, "window": 21},
            "MACD": {"macd_line": 0.1, "signal_line": 0.05, "histogram": 0.05},
            "Beta": {"beta_value": 1.0, "benchmark_used": "VNINDEX", "window_weeks": 52},
            "CMF": {
                "cmf_value": 0.05,
                "obv_change": {"provenance": {"source_series": "OBV"}},
                "vpt_change": {"provenance": {"source_series": "VPT"}},
            },
        },
        "tech_score": 65,
        "binary_signals_6": {"signal_a": 1},
        "analysis_status": "VALID",
        "computation_chain": chain,
        "provenance": {
            "timestamp": "2025-03-31T00:00:00",
            "provider": "test_provider",
            "source_provider": "test_provider",
            "params": {"window": 20},
            "computation_chain": chain,
            "market_data_packet": {"id": "mp_1"},
            "input_provenance": [{"date": d, "source": "collector"} for d in dates],
        },
    }
    fixture = {"ohlcv": ohlcv, "weekly_close": closes, "mode": "ACTIVE"}
    return packet, fixture


def test_end_to_end_determinism() -> None:
    packet, fixture = _synthetic_packet_and_fixture()
    with tempfile.TemporaryDirectory() as tmp:
        fixtures_dir = os.path.join(tmp, "fixtures")
        os.makedirs(fixtures_dir, exist_ok=True)
        packet_path = os.path.join(tmp, "output_packet.json")
        fixture_path = os.path.join(fixtures_dir, "FX-TEST-1.json")
        with open(packet_path, "w") as f:
            json.dump(packet, f)
        with open(fixture_path, "w") as f:
            json.dump(fixture, f)

        kwargs = dict(
            output_packet_path=packet_path,
            frozen_fixtures_dir=fixtures_dir,
            formula_contracts_path=FORMULA_CONTRACTS,
            failure_code_registry_path=FAILURE_REGISTRY,
            vc_mapping_path=VC_MAPPING,
            fixture_id="FX-TEST-1",
            expected_status="PASS",
        )
        result1 = vta_verifier.run_verification(**kwargs)
        result2 = vta_verifier.run_verification(**kwargs)

        _check(
            result1["summary"]["canonical_VC_count"] == 64,
            f"canonical_VC_count != 64: {result1['summary']['canonical_VC_count']}",
        )
        _check(
            result1["summary"]["evaluated_VC_count"] == 64,
            f"evaluated_VC_count != 64: {result1['summary']['evaluated_VC_count']}",
        )
        _check(
            not result1["summary"]["missing_VCs"],
            f"missing VCs: {result1['summary']['missing_VCs']}",
        )
        _check(
            not result1["summary"]["extra_VCs"],
            f"extra VCs: {result1['summary']['extra_VCs']}",
        )

        vc_ids = [r["VC_id"] for r in result1["records"]]
        _check(
            vc_ids == sorted(vc_ids),
            "records are not sorted by VC_id",
        )
        required_keys = {
            "VC_id",
            "fixture_id",
            "mutation_id",
            "expected_status",
            "observed_status",
            "expected_primary_code",
            "observed_primary_code",
            "verdict",
        }
        _check(
            all(required_keys <= set(r.keys()) for r in result1["records"]),
            "at least one record is missing required schema keys",
        )
        _check(
            json.dumps(result1, sort_keys=True, default=str)
            == json.dumps(result2, sort_keys=True, default=str),
            "verifier output is not deterministic across runs",
        )


# ===========================================================================
# Test 7: verdict switching on controlled fixtures
# ===========================================================================


def test_verdict_switching() -> None:
    """Drive each domain with a controlled positive and negative fixture and
    confirm the verdict reflects the expected outcome."""
    cases: List[Tuple[str, Callable[[Any], Any], str, str, str]] = []

    # Language: clean text -> PASS; advice text -> FAIL.
    def clean_language(packet):
        return {
            "mode": "ACTIVE",
            "as_of_date": "2025-03-31",
            "ticker": "TEST",
            "indicators": {},
            "analysis_text": "The RSI value is 55.0 and the MA21 is 100.5.",
        }

    def advice_language(packet):
        return {
            "mode": "ACTIVE",
            "as_of_date": "2025-03-31",
            "ticker": "TEST",
            "indicators": {},
            "analysis_text": "Nên mua cổ phiếu này vì RSI đang quá bán.",
        }

    cases.append(("VC-REQ007-LEXICAL", clean_language, "PASS", "NONE", "lexical clean"))
    cases.append(("VC-ADV-LANG-1", advice_language, "FAIL", "ADVICE_LANGUAGE_DETECTED", "advice phrase injected"))

    # Boundary: clean adapter -> PASS; write to valuation -> FAIL.
    def clean_adapter(packet):
        return {"write_targets": ["technical_indicator", "tech_score"]}

    def valuation_write(packet):
        return {"write_targets": ["valuation_fair_value", "tech_score"]}

    cases.append(("VC-VAL-BOUND-1", clean_adapter, "PASS", "NONE", "clean adapter"))
    cases.append(("VC-VAL-BOUND-1", valuation_write, "FAIL", "VALUATION_OVERRIDE_ATTEMPT", "valuation write path"))

    # Input pre-flight: empty series -> FAIL with INSUFFICIENT_HISTORY.
    def empty_series_packet(packet):
        return {"mode": "ACTIVE", "error_code": "INSUFFICIENT_HISTORY"}

    def empty_series_fixture():
        return {"ohlcv": [], "mode": "ACTIVE"}

    # Schema drift: foreign key -> FAIL with SCHEMA_VALIDATION_FAILED.
    def drift_packet(packet):
        return {
            "mode": "ACTIVE",
            "as_of_date": "2025-03-31",
            "ticker": "TEST",
            "indicators": {},
            "foreign_injected_key": "should be rejected",
        }

    cases.append(("VC-SCHEMA-DRIFT-1", drift_packet, "FAIL", "SCHEMA_VALIDATION_FAILED", "foreign key injected"))

    with tempfile.TemporaryDirectory() as tmp:
        fixtures_dir = os.path.join(tmp, "fixtures")
        os.makedirs(fixtures_dir, exist_ok=True)
        for idx, (vc_id, packet_fn, expected_status, expected_code, label) in enumerate(cases):
            packet = packet_fn(None)
            packet_path = os.path.join(tmp, f"packet_{idx}.json")
            with open(packet_path, "w") as f:
                json.dump(packet, f)
            fixture_id = f"FX-CASE-{idx}"
            fixture_path = os.path.join(fixtures_dir, f"{fixture_id}.json")
            fixture = empty_series_fixture() if label == "" else {}
            with open(fixture_path, "w") as f:
                json.dump(fixture, f)

            result = vta_verifier.run_verification(
                output_packet_path=packet_path,
                frozen_fixtures_dir=fixtures_dir,
                formula_contracts_path=FORMULA_CONTRACTS,
                failure_code_registry_path=FAILURE_REGISTRY,
                vc_mapping_path=VC_MAPPING,
                fixture_id=fixture_id,
                expected_status=expected_status,
                expected_primary_code=expected_code,
            )
            record = next((r for r in result["records"] if r["VC_id"] == vc_id), None)
            _check(record is not None, f"{vc_id}: no record produced for case {label!r}")
            _check(
                record["verdict"] == "PASS",
                f"{vc_id} ({label}): expected verdict PASS (verifier agreed with "
                f"expected {expected_status}/{expected_code}), got "
                f"{record['verdict']} (observed {record['observed_status']}/"
                f"{record['observed_primary_code']})",
            )


# ===========================================================================
# Runner
# ===========================================================================


def run_all() -> int:
    tests: List[Tuple[str, Callable[[], None]]] = [
        ("import_cleanliness", test_import_cleanliness),
        ("independence_guard", test_independence_guard),
        ("coverage_and_disjointness", test_coverage_and_disjointness),
        ("end_to_end_determinism", test_end_to_end_determinism),
        ("verdict_switching", test_verdict_switching),
    ]
    failures = 0
    for name, test in tests:
        try:
            test()
            print(f"  PASS  {name}")
        except SelfTestFailure as exc:
            failures += 1
            print(f"  FAIL  {name}: {exc}")
        except Exception as exc:  # pragma: no cover - defensive
            failures += 1
            print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} self-test groups passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run_all())
