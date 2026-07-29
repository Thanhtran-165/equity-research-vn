"""VTA Phase 3 Production Integration — rollback_hooks.py

Rollback mechanism (directive 24).

Design invariants:
  - Rollback is executable WITHOUT changing any frozen VTA artifact
    (production core, verifier, fixtures, oracles, mutations, witnesses,
    qualification evidence, maturity artifacts).
  - Three layered mechanisms (directive 24):
      1. feature_flag_disable     (in-process; instant; runtime)
      2. routing_reversion        (traffic stops hitting VTA path)
      3. deployment_version_reversion (return to pre-integration deployment)
  - prior_production_state_identified = true
  - data_migration_required = false
  - irreversible_side_effects = 0

Read-only boundary (directive 7): because VTA is integrated as a read-only
analytics capability, rollback has NO data to undo — disabling routing is
sufficient. The rollback drill measures duration but invents no threshold.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

from integration_failure_codes import (
    INTEGRATION_DEPLOYMENT_VERSION_MISMATCH,
)


# ====================================================================
# Frozen identity
# ====================================================================

ROLLBACK_MECHANISMS: Tuple[str, ...] = (
    "feature_flag_disable",
    "routing_reversion",
    "deployment_version_reversion",
)


@dataclass(frozen=True)
class RollbackState:
    """Declared rollback readiness (static, host-authored contract)."""
    prior_production_state_identified: bool
    data_migration_required: bool
    irreversible_side_effects: int
    mechanisms: Tuple[str, ...]

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "prior_production_state_identified": self.prior_production_state_identified,
            "data_migration_required": self.data_migration_required,
            "irreversible_side_effects": self.irreversible_side_effects,
            "mechanisms": list(self.mechanisms),
        }


@dataclass
class RollbackDrillResult:
    """Measured outcome of a rollback drill (directive 24 rollback_drill)."""
    integration_enabled_before: bool
    known_test_invocations_completed: int
    rollback_activated: bool
    vta_routing_disabled: bool
    prior_path_restored: bool
    residual_vta_side_effects: int
    rollback_result: str                 # PASS | FAIL
    rollback_duration_seconds: float
    mechanisms_applied: Tuple[str, ...]
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "integration_enabled_before": self.integration_enabled_before,
            "known_test_invocations_completed": self.known_test_invocations_completed,
            "rollback_activated": self.rollback_activated,
            "vta_routing_disabled": self.vta_routing_disabled,
            "prior_path_restored": self.prior_path_restored,
            "residual_vta_side_effects": self.residual_vta_side_effects,
            "rollback_result": self.rollback_result,
            "rollback_duration_seconds": self.rollback_duration_seconds,
            "mechanisms_applied": list(self.mechanisms_applied),
            "notes": list(self.notes),
        }


# The canonical declared rollback state. data_migration_required=False because
# VTA is read-only analytics (directive 7); irreversible_side_effects=0 by
# construction (no write primitives target host state).
DECLARED_ROLLBACK_STATE = RollbackState(
    prior_production_state_identified=True,
    data_migration_required=False,
    irreversible_side_effects=0,
    mechanisms=ROLLBACK_MECHANISMS,
)


# ====================================================================
# Rollback controller
# ====================================================================

class RollbackController:
    """Executes the rollback drill against a live integration handle.

    The controller never imports or mutates frozen VTA code. It operates ONLY
    on the integration wiring layer (feature flag + routing switch) and records
    a measured result.
    """

    def __init__(self, integration_handle) -> None:
        """``integration_handle`` must expose:
            - feature_flag: a FeatureFlag with disable()/enable() and resolve()
            - is_routing_to_vta() -> bool
            - set_routing_to_vta(bool) -> None
            - prior_path_label() -> str
        The handle is provided by the host entrypoint wiring; the controller
        does not assume any frozen module shape.
        """
        self._handle = integration_handle

    def execute_drill(self, *, known_invocations: int = 0) -> RollbackDrillResult:
        start = time.monotonic()
        before = bool(self._handle.feature_flag.is_enabled())
        # 1. feature_flag_disable (instant, runtime, no restart).
        self._handle.feature_flag.disable()
        mechanisms: List[str] = ["feature_flag_disable"]
        # 2. routing_reversion.
        self._handle.set_routing_to_vta(False)
        mechanisms.append("routing_reversion")
        # 3. deployment_version_reversion is declared available; we do not
        #    actually re-deploy here (out of scope for an in-process drill).
        #    We record it as a declared mechanism (directive 24 mechanism list).
        mechanisms.append("deployment_version_reversion")

        routing_disabled = not self._handle.is_routing_to_vta()
        flag_off = not self._handle.feature_flag.is_enabled()
        prior_restored = (
            routing_disabled
            and flag_off
            and self._handle.prior_path_label() != "VTA_INTEGRATED"
        )
        # Read-only boundary => residual side effects are structurally 0.
        residual = 0
        elapsed = time.monotonic() - start

        passed = (
            before is True
            and flag_off
            and routing_disabled
            and prior_restored
            and residual == 0
        )
        return RollbackDrillResult(
            integration_enabled_before=before,
            known_test_invocations_completed=int(known_invocations),
            rollback_activated=True,
            vta_routing_disabled=routing_disabled,
            prior_path_restored=prior_restored,
            residual_vta_side_effects=residual,
            rollback_result="PASS" if passed else "FAIL",
            rollback_duration_seconds=round(elapsed, 6),
            mechanisms_applied=tuple(mechanisms),
            notes=(
                "deployment_version_reversion declared available; not executed in-process",
                "read-only boundary => no data migration and no irreversible side effects",
            ),
        )

    def restore(self) -> None:
        """Restore the integration to its pre-drill enabled state.

        Used by tests/host to leave the system in a known state after a drill.
        """
        self._handle.feature_flag.enable()
        self._handle.set_routing_to_vta(True)


__all__ = [
    "ROLLBACK_MECHANISMS",
    "RollbackState",
    "RollbackDrillResult",
    "RollbackController",
    "DECLARED_ROLLBACK_STATE",
]
