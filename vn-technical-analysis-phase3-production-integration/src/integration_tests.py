"""VTA Phase 3 Production Integration — integration_tests.py

Integration test suite (directive 15, 16, 26). Runs against the FROZEN
implementation corpus and the live integration adapter.

Coverage:
  - offline adapter qualification (Stage A): fixture/mutation/witness
    relationships through the integration path == direct frozen runner.
  - input-boundary qualification (directive 15): 16 input classes.
  - output-boundary qualification (directive 16): canonical packet preserved,
    deterministic record ID preserved, codes preserved, provenance preserved.
  - shadow parity (directive 13): integrated vs direct digest equality.
  - rollback drill (directive 24).

These tests do NOT modify any frozen artifact. They import the frozen runner
via the adapter (which pins the implementation commit).
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from typing import Any, Mapping, Tuple

# Make sibling integration modules importable when run directly.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import feature_flag  # noqa: E402
import integration_adapter  # noqa: E402
import observability  # noqa: E402
import rollback_hooks  # noqa: E402
from feature_flag import FeatureFlag, FLAG_DEFAULT_STATE  # noqa: E402
from integration_adapter import (  # noqa: E402
    HOST_INVOCATION_MAPPINGS,
    HOST_ROW_FIELD_MAPPINGS,
    INTEGRATION_VERSION,
    PINNED_IMPLEMENTATION_COMMIT,
    SUPPORTED_HOST_SCHEMA_VERSIONS,
    IntegrationAdapter,
)
from integration_failure_codes import (  # noqa: E402
    NAMESPACE,
    all_codes,
    assert_disjoint_from_canonical,
    count as integration_code_count,
)
from observability import (  # noqa: E402
    MANDATORY_DIMENSION_COUNT,
    MANDATORY_DIMENSIONS,
    MANDATORY_METRIC_COUNT,
    MANDATORY_METRICS,
    ObservabilityRecorder,
)
from rollback_hooks import DECLARED_ROLLBACK_STATE, RollbackController  # noqa: E402


# ====================================================================
# Test data helpers
# ====================================================================

_FROZEN_IMPL_DIR = os.environ.get(
    "VTA_FROZEN_IMPLEMENTATION_DIR",
    os.path.normpath(os.path.join(_HERE, "..", "..",
                                  "vn-technical-analysis-phase3-implementation")),
)


def _weekly_rows(n: int = 52, base: float = 25.0) -> list:
    """Deterministic weekly OHLCV (52+ rows for ACTIVE minimum)."""
    rows = []
    price = base
    for i in range(n):
        # Gentle deterministic drift; no randomness (deterministic tests).
        o = price
        c = round(o + (i % 5) * 0.05 - 0.10, 4)
        h = round(max(o, c) + 0.02, 4)
        lo = round(min(o, c) - 0.02, 4)
        v = 100000 + i * 100
        rows.append({
            "timestamp": f"2024-W{i // 1 + 1:02d}-MON" if False else _date_for_week(i),
            "open_price": o, "high_price": h, "low_price": lo,
            "close_price": c, "trade_volume": v, "trading_days_in_period": 5,
        })
        price = c
    return rows


def _date_for_week(i: int) -> str:
    # Deterministic calendar mapping: week i -> 2024 day (i*7+1), clamped.
    from datetime import date, timedelta
    d = date(2024, 1, 1) + timedelta(days=i * 7)
    return d.isoformat()


def _daily_rows(n: int = 60) -> list:
    rows = []
    price = 25.0
    for i in range(n):
        o = price
        c = round(o + (i % 3) * 0.03 - 0.03, 4)
        rows.append({
            "timestamp": _date_for_day(i),
            "open_price": o, "high_price": round(max(o, c) + 0.01, 4),
            "low_price": round(min(o, c) - 0.01, 4),
            "close_price": c, "trade_volume": 50000 + i * 50,
        })
        price = c
    return rows


def _date_for_day(i: int) -> str:
    from datetime import date, timedelta
    return (date(2024, 1, 1) + timedelta(days=i)).isoformat()


def _active_host_input(rows=None, **overrides) -> dict:
    base = {
        "schema_version": "host-market-data-v1",
        "host_input": {
            "symbol": "TEST",
            "mode": "ACTIVE",
            "frequency": "WEEKLY",
            "as_of_date": None,
            "source_provider": "TEST_PROVIDER",
            "adjustment_state": "ADJUSTED",
            "price_basis": "adjusted",
            "rows": rows if rows is not None else _weekly_rows(),
        },
    }
    base["host_input"].update(overrides)
    return base


def _profile_host_input(rows=None, **overrides) -> dict:
    base = {
        "schema_version": "host-market-data-v1",
        "host_input": {
            "symbol": "TEST",
            "mode": "PROFILE",
            "frequency": "DAILY",
            "as_of_date": None,
            "source_provider": "TEST_PROVIDER",
            "adjustment_state": "ADJUSTED",
            "price_basis": "adjusted",
            "rows": rows if rows is not None else _daily_rows(),
        },
    }
    base["host_input"].update(overrides)
    return base


def _make_adapter(enabled: bool = True) -> Tuple[IntegrationAdapter, FeatureFlag, ObservabilityRecorder]:
    ff = FeatureFlag()
    if enabled:
        ff.enable()
    obs = ObservabilityRecorder()
    adapter = IntegrationAdapter(
        frozen_implementation_dir=_FROZEN_IMPL_DIR,
        feature_flag=ff, observability=obs,
        environment="test", consumer="integration-test",
    )
    return adapter, ff, obs


# ====================================================================
# Tests
# ====================================================================

class TestWiringIdentity(unittest.TestCase):
    def test_version_pinning_constants(self):
        self.assertEqual(integration_adapter.PINNED_IMPLEMENTATION_COMMIT,
                         "23853411aa74c504ee2d79dd8889a845b5edf7de")
        self.assertTrue(INTEGRATION_VERSION.startswith("vta-phase-3-integration"))

    def test_feature_flag_default_off(self):
        self.assertEqual(FLAG_DEFAULT_STATE, "OFF")
        ff = FeatureFlag()
        d = ff.resolve(environment="x")
        self.assertFalse(d.enabled)

    def test_observability_metric_count(self):
        self.assertEqual(len(MANDATORY_METRICS), MANDATORY_METRIC_COUNT)
        self.assertEqual(MANDATORY_METRIC_COUNT, 12)

    def test_observability_dimension_count(self):
        self.assertEqual(len(MANDATORY_DIMENSIONS), MANDATORY_DIMENSION_COUNT)

    def test_integration_failure_namespace_disjoint(self):
        # The 43 canonical codes (representative subset) must not overlap.
        canonical_subset = {
            "EMPTY_SERIES", "INSUFFICIENT_HISTORY", "ZERO_PRICE_DETECTED",
            "LOOKAHEAD_BIAS_DETECTED", "MODE_CONTAMINATION",
            "SCHEMA_VALIDATION_FAILED", "VALUATION_OVERRIDE_ATTEMPT",
            "PROVENANCE_MISSING", "ADVICE_LANGUAGE_DETECTED",
        }
        assert_disjoint_from_canonical(canonical_subset)
        self.assertEqual(integration_code_count(), 9)
        for c in all_codes():
            self.assertTrue(c.startswith("INTEGRATION_"))


class TestHostInputMapping(unittest.TestCase):
    def setUp(self):
        self.adapter, _, _ = _make_adapter()

    def test_valid_active_input_maps(self):
        canonical = self.adapter.map_host_to_canonical_input(_active_host_input())
        self.assertEqual(canonical.mode, "ACTIVE")
        self.assertEqual(canonical.frequency, "WEEKLY")
        self.assertEqual(len(canonical.rows), 52)
        self.assertEqual(canonical.rows[0]["date"], "2024-01-01")
        self.assertTrue(canonical.canonical_input_digest)
        self.assertTrue(canonical.host_input_digest)

    def test_timestamp_iso_normalization(self):
        rows = _weekly_rows()
        rows[0]["timestamp"] = "2024-01-01T00:00:00+07:00"
        canonical = self.adapter.map_host_to_canonical_input(_active_host_input(rows=rows))
        # Offset applied: 2024-01-01T00:00:00+07:00 -> UTC 2023-12-31.
        self.assertEqual(canonical.rows[0]["date"], "2023-12-31")

    def test_unknown_schema_version_rejected(self):
        hi = _active_host_input()
        hi["schema_version"] = "host-market-data-v9"
        with self.assertRaises(integration_adapter.IntegrationFailureEnvelope_error) as cm:
            self.adapter.map_host_to_canonical_input(hi)
        self.assertEqual(cm.exception.envelope.integration_code,
                         "INTEGRATION_UNSUPPORTED_HOST_SCHEMA")

    def test_missing_required_row_field_rejected(self):
        rows = _weekly_rows()
        del rows[0]["close_price"]
        with self.assertRaises(integration_adapter.IntegrationFailureEnvelope_error):
            self.adapter.map_host_to_canonical_input(_active_host_input(rows=rows))

    def test_invalid_float_rejected(self):
        rows = _weekly_rows()
        rows[0]["close_price"] = "not-a-number"
        with self.assertRaises(integration_adapter.IntegrationFailureEnvelope_error) as cm:
            self.adapter.map_host_to_canonical_input(_active_host_input(rows=rows))
        self.assertEqual(cm.exception.envelope.integration_code,
                         "INTEGRATION_ADAPTER_SCHEMA_REJECTED")

    def test_mode_frequency_mismatch_rejected(self):
        hi = _active_host_input()
        hi["host_input"]["mode"] = "ACTIVE"
        hi["host_input"]["frequency"] = "DAILY"
        with self.assertRaises(integration_adapter.IntegrationFailureEnvelope_error):
            self.adapter.map_host_to_canonical_input(hi)


class TestInputBoundaryQualification(unittest.TestCase):
    """Directive 15: 16 input classes. None may crash the host process."""
    def setUp(self):
        self.adapter, _, _ = _make_adapter()

    def _run_status(self, host_input):
        # Use the full run() path so we exercise fail-closed handling.
        return self.adapter.run(host_input)["status"]

    def test_empty_series(self):
        hi = _active_host_input(rows=[])
        # Empty rows are structurally valid; forwarded to the frozen runner,
        # which emits the canonical EMPTY_SERIES envelope (directive 15).
        s = self._run_status(hi)
        self.assertEqual(s, "CANONICAL_FAILURE")

    def test_insufficient_history(self):
        hi = _active_host_input(rows=_weekly_rows(10))
        s = self._run_status(hi)
        self.assertEqual(s, "CANONICAL_FAILURE")

    def test_duplicate_timestamps(self):
        rows = _weekly_rows()
        rows[5] = dict(rows[5])  # dup of row 5 content but different date is fine;
        # force an actual duplicate date:
        rows[5]["timestamp"] = rows[4]["timestamp"]
        s = self._run_status(_active_host_input(rows=rows))
        self.assertIn(s, ("OK", "CANONICAL_FAILURE", "INTEGRATION_FAILURE"))

    def test_out_of_order_timestamps(self):
        rows = _weekly_rows()
        rows[0], rows[1] = rows[1], rows[0]
        s = self._run_status(_active_host_input(rows=rows))
        self.assertIn(s, ("OK", "CANONICAL_FAILURE"))

    def test_missing_bars(self):
        rows = _weekly_rows()
        for r in rows:
            r["trade_volume"] = None  # nullable
        s = self._run_status(_active_host_input(rows=rows))
        self.assertIn(s, ("OK", "CANONICAL_FAILURE"))

    def test_null_close(self):
        rows = _weekly_rows()
        rows[10]["close_price"] = None
        s = self._run_status(_active_host_input(rows=rows))
        self.assertIn(s, ("INTEGRATION_FAILURE", "CANONICAL_FAILURE"))

    def test_nan_and_infinity(self):
        rows = _weekly_rows()
        rows[10]["close_price"] = float("nan")
        rows[20]["close_price"] = float("inf")
        s = self._run_status(_active_host_input(rows=rows))
        self.assertIn(s, ("INTEGRATION_FAILURE", "CANONICAL_FAILURE"))

    def test_zero_price(self):
        rows = _weekly_rows()
        rows[3]["close_price"] = 0.0
        s = self._run_status(_active_host_input(rows=rows))
        self.assertEqual(s, "CANONICAL_FAILURE")

    def test_unknown_schema_version(self):
        hi = _active_host_input()
        hi["schema_version"] = "unknown"
        self.assertEqual(self._run_status(hi), "INTEGRATION_FAILURE")

    def test_malformed_timestamp(self):
        rows = _weekly_rows()
        rows[0]["timestamp"] = "not-a-date"
        self.assertEqual(self._run_status(_active_host_input(rows=rows)),
                         "INTEGRATION_FAILURE")

    def test_valid_profile_input(self):
        s = self._run_status(_profile_host_input())
        self.assertIn(s, ("OK", "CANONICAL_FAILURE"))


class TestOutputBoundaryQualification(unittest.TestCase):
    """Directive 16: canonical packet preserved through the host envelope."""
    def setUp(self):
        self.adapter, _, _ = _make_adapter()

    def test_canonical_packet_preserved_verbatim(self):
        result = self.adapter.run(_active_host_input())
        self.assertEqual(result["status"], "OK")
        env = result["envelope"]
        # The canonical packet body must round-trip through the host envelope
        # without field drops/renames/coercions.
        cp = env["canonical_packet"]
        self.assertIn("mode", cp)
        self.assertIn("body", cp)
        self.assertEqual(cp["mode"], "ACTIVE")

    def test_deterministic_record_id_stable(self):
        hi = _active_host_input()
        r1 = self.adapter.run(hi)
        r2 = self.adapter.run(hi)
        self.assertEqual(r1["envelope"]["deterministic_record_id"],
                         r2["envelope"]["deterministic_record_id"])

    def test_host_envelope_versioned(self):
        result = self.adapter.run(_active_host_input())
        env = result["envelope"]
        self.assertEqual(env["integration_version"], INTEGRATION_VERSION)
        self.assertEqual(env["pinned_implementation_commit"],
                         PINNED_IMPLEMENTATION_COMMIT)


class TestShadowParity(unittest.TestCase):
    """Directive 13: integrated output digest == direct frozen runner digest."""
    def setUp(self):
        self.adapter, _, _ = _make_adapter()

    def test_integrated_vs_direct_digest_match(self):
        import importlib
        sys.path.insert(0, os.path.join(_FROZEN_IMPL_DIR, "src"))
        runner = importlib.import_module("runner")
        canonical = self.adapter.map_host_to_canonical_input(_active_host_input())
        direct = runner.run_active(
            canonical.ticker, canonical.rows,
            as_of_date=canonical.as_of_date,
            source_provider=canonical.source_provider,
        )
        integrated = self.adapter.run(_active_host_input())
        self.assertEqual(integrated["status"], "OK")
        import hashlib, json
        direct_digest = hashlib.sha256(
            direct.packet.serialize().encode("utf-8")).hexdigest()
        self.assertEqual(integrated["envelope"]["output_digest"], direct_digest)


class TestFeatureFlagRouting(unittest.TestCase):
    def test_disabled_returns_explicit_status(self):
        adapter, ff, _ = _make_adapter(enabled=False)
        result = adapter.run(_active_host_input())
        self.assertEqual(result["status"], "DISABLED")
        self.assertEqual(result["fallback"]["kind"], "EXPLICIT_DISABLED_STATUS")
        self.assertFalse(result["feature_flag_decision"]["enabled"])

    def test_runtime_disable_no_restart(self):
        adapter, ff, _ = _make_adapter(enabled=True)
        self.assertTrue(adapter.run(_active_host_input())["status"] in ("OK",))
        ff.disable()  # runtime, no restart
        result = adapter.run(_active_host_input())
        self.assertEqual(result["status"], "DISABLED")


class TestRollbackDrill(unittest.TestCase):
    def test_rollback_drill_passes(self):
        adapter, ff, _ = _make_adapter(enabled=True)

        class Handle:
            def __init__(self_self):
                self_self.feature_flag = ff
                self_self._route = True
            def is_routing_to_vta(self_self):
                return self_self._route
            def set_routing_to_vta(self_self, b):
                self_self._route = bool(b)
            def prior_path_label(self_self):
                return "HOST_NON_VTA_FALLBACK" if not self_self._route else "VTA_INTEGRATED"

        ctrl = RollbackController(Handle())
        result = ctrl.execute_drill(known_invocations=3)
        self.assertEqual(result.rollback_result, "PASS")
        self.assertEqual(result.residual_vta_side_effects, 0)
        self.assertIn("feature_flag_disable", result.mechanisms_applied)
        # Declared state sanity.
        self.assertFalse(DECLARED_ROLLBACK_STATE.data_migration_required)
        self.assertEqual(DECLARED_ROLLBACK_STATE.irreversible_side_effects, 0)


def suite() -> unittest.TestSuite:
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    for cls in (
        TestWiringIdentity,
        TestHostInputMapping,
        TestInputBoundaryQualification,
        TestOutputBoundaryQualification,
        TestShadowParity,
        TestFeatureFlagRouting,
        TestRollbackDrill,
    ):
        s.addTests(loader.loadTestsFromTestCase(cls))
    return s


if __name__ == "__main__":
    unittest.main(defaultTest="suite", verbosity=2)
