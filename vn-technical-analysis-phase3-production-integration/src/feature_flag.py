"""VTA Phase 3 Production Integration — feature_flag.py

Mandatory integration feature flag (directive section 11).

Contract:
  - name:             vta_phase_3_integration_enabled
  - default_state:    OFF
  - scope:            environment / tenant_or_consumer / invocation_path
  - runtime_disable:  supported (no restart required)

Design invariants:
  - The flag DISABLES integration routing only. It does NOT modify any frozen
    VTA implementation file. When OFF, the host's documented non-VTA fallback
    (or an explicit disabled status) is returned. The flag MUST NOT silently
    invoke a different technical-analysis implementation.
  - Fail-closed: an unknown / ambiguous flag state is treated as OFF.
  - Read-only side-effect policy: toggling the flag mutates only the in-process
    routing decision; it issues no external action and writes no market data.

Integration failure codes owned here (separate namespace, see
integration_failure_codes.py):
  - FEATURE_FLAG_AMBIGUOUS_STATE
  - FEATURE_FLAG_RESTART_REQUIRED_VIOLATION
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Tuple

from integration_failure_codes import (
    INTEGRATION_FLAG_AMBIGUOUS_STATE,
    INTEGRATION_FLAG_RESTART_REQUIRED_VIOLATION,
)


# ====================================================================
# Frozen flag identity
# ====================================================================

FLAG_NAME: str = "vta_phase_3_integration_enabled"
FLAG_DEFAULT_STATE: str = "OFF"

# Scope tuple (directive 11): the flag may be resolved per-environment,
# per-tenant/consumer, and per-invocation-path. The MOST SPECIFIC scope wins.
FLAG_SCOPE: Tuple[str, ...] = (
    "environment",
    "tenant_or_consumer",
    "invocation_path",
)

# Acceptable string states.
_STATE_ON = frozenset({"ON", "TRUE", "1", "YES", "ENABLED"})
_STATE_OFF = frozenset({"OFF", "FALSE", "0", "NO", "DISABLED"})


# ====================================================================
# Flag state
# ====================================================================

@dataclass(frozen=True)
class FeatureFlagDecision:
    """A resolved feature-flag decision.

    ``enabled`` is the authoritative boolean. ``raw_value`` is retained for
    observability only (never parsed as a machine contract beyond ON/OFF).
    """
    enabled: bool
    raw_value: str
    resolved_scope: str
    source: str                      # ENV / TENANT_REGISTRY / INVOCATION_OVERRIDE / DEFAULT
    fallback_reason: Optional[str]   # populated only when disabled via fallback

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "flag_name": FLAG_NAME,
            "enabled": self.enabled,
            "raw_value": self.raw_value,
            "resolved_scope": self.resolved_scope,
            "source": self.source,
            "fallback_reason": self.fallback_reason,
            "default_state": FLAG_DEFAULT_STATE,
        }


def _parse_state(raw: Any) -> Optional[bool]:
    """Parse a raw flag value into a strict bool. Ambiguous -> None (fail-closed)."""
    if raw is None:
        return None
    if isinstance(raw, bool):
        return raw
    s = str(raw).strip().upper()
    if s in _STATE_ON:
        return True
    if s in _STATE_OFF:
        return False
    # Ambiguous: fail-closed -> treat as OFF but flag the ambiguity.
    return None


class FeatureFlag:
    """Runtime-resolvable integration feature flag.

    Resolution precedence (highest first):
      1. invocation_path override (programmatic, runtime)
      2. tenant_or_consumer registry (provided at construction)
      3. environment variable
      4. DEFAULT (OFF)

    The flag supports runtime disable WITHOUT restart: ``disable()`` flips the
    in-process state atomically and returns immediately. If a caller declares
    ``restart_required_to_disable=True`` anywhere in the resolution chain, the
    flag raises INTEGRATION_FLAG_RESTART_REQUIRED_VIOLATION — the directive
    forbids restart-required disable.
    """

    def __init__(
        self,
        *,
        environment: Optional[Mapping[str, str]] = None,
        tenant_registry: Optional[Mapping[str, Mapping[str, str]]] = None,
        env_var_name: str = "VTA_PHASE_3_INTEGRATION_ENABLED",
        restart_required_to_disable: bool = False,
    ) -> None:
        if restart_required_to_disable:
            # Directive 11: restart_required_to_disable MUST be false. Refuse
            # construction rather than silently violating the contract.
            raise FeatureFlagConfigurationError(
                INTEGRATION_FLAG_RESTART_REQUIRED_VIOLATION,
                "restart_required_to_disable=true is prohibited by directive 11",
            )
        self._env = dict(environment) if environment else {}
        self._tenant_registry = {
            k: dict(v) for k, v in (tenant_registry or {}).items()
        }
        self._env_var_name = env_var_name
        self._invocation_overrides: dict[str, str] = {}
        # Runtime override switch (atomic). True = force OFF; False = force ON;
        # None = delegate to the environment/tenant/invocation chain.
        self._runtime_override: Optional[bool] = None
        self._lock = threading.RLock()
        # Seed environment from os.environ at construction time for the named var.
        if env_var_name and env_var_name not in self._env:
            os_val = os.environ.get(env_var_name)
            if os_val is not None:
                self._env[env_var_name] = os_val

    # ----------------------------------------------------------------
    # Runtime control (no restart required)
    # ----------------------------------------------------------------

    def disable(self) -> None:
        """Runtime disable. Atomically forces the flag OFF until cleared.

        Does NOT raise; never blocks. Honors directive 11's
        runtime_disable_supported=true, restart_required_to_disable=false.
        """
        with self._lock:
            self._runtime_override = True

    def enable(self) -> None:
        """Runtime enable. Atomically forces the flag ON until cleared.

        This is the programmatic counterpart to ``disable()``. Setting ON at
        runtime does NOT bypass the directive's default_state=OFF: when no
        runtime override is set, resolution falls through to the environment
        chain and ultimately the DEFAULT (OFF). An explicit ``enable()`` is the
        documented way the host turns integration routing ON.
        """
        with self._lock:
            self._runtime_override = False

    def clear_runtime_override(self) -> None:
        with self._lock:
            self._runtime_override = None

    def set_invocation_override(self, invocation_path: str, state: str) -> None:
        """Programmatic per-invocation-path override (scope: invocation_path)."""
        with self._lock:
            self._invocation_overrides[invocation_path] = str(state).upper()

    # ----------------------------------------------------------------
    # Resolution
    # ----------------------------------------------------------------

    def resolve(
        self,
        *,
        invocation_path: Optional[str] = None,
        tenant_or_consumer: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> FeatureFlagDecision:
        """Resolve the flag for a single invocation.

        Returns a FeatureFlagDecision. Never raises for ambiguous input — it
        returns a disabled decision with fallback_reason set so the host can
        emit INTEGRATION_FLAG_AMBIGUOUS_STATE via the observability layer.
        """
        with self._lock:
            runtime_override = self._runtime_override
            inv = dict(self._invocation_overrides)
            tenant_reg = {k: dict(v) for k, v in self._tenant_registry.items()}
            env = dict(self._env)
            env_var = self._env_var_name

        # 0. Runtime override is the highest-priority hard switch.
        #    True  -> force OFF (rollback / disable path).
        #    False -> force ON  (host programmatic enable).
        #    None  -> delegate to the environment/tenant/invocation chain.
        if runtime_override is True:
            return FeatureFlagDecision(
                enabled=False, raw_value="OFF",
                resolved_scope="runtime_override",
                source="RUNTIME_DISABLE",
                fallback_reason="runtime_disable_active",
            )
        if runtime_override is False:
            return FeatureFlagDecision(
                enabled=True, raw_value="ON",
                resolved_scope="runtime_override",
                source="RUNTIME_ENABLE",
                fallback_reason=None,
            )

        # 1. invocation_path override.
        if invocation_path and invocation_path in inv:
            parsed = _parse_state(inv[invocation_path])
            scope = "invocation_path"
            if parsed is None:
                return FeatureFlagDecision(
                    enabled=False, raw_value=inv[invocation_path],
                    resolved_scope=scope, source="INVOCATION_OVERRIDE",
                    fallback_reason=INTEGRATION_FLAG_AMBIGUOUS_STATE,
                )
            return FeatureFlagDecision(
                enabled=parsed, raw_value=inv[invocation_path],
                resolved_scope=scope, source="INVOCATION_OVERRIDE",
                fallback_reason=None,
            )

        # 2. tenant_or_consumer registry.
        if tenant_or_consumer and tenant_or_consumer in tenant_reg:
            entry = tenant_reg[tenant_or_consumer]
            raw = entry.get(env_var) or entry.get("state") or entry.get(FLAG_NAME)
            parsed = _parse_state(raw)
            scope = "tenant_or_consumer"
            if parsed is None:
                return FeatureFlagDecision(
                    enabled=False, raw_value=str(raw),
                    resolved_scope=scope, source="TENANT_REGISTRY",
                    fallback_reason=INTEGRATION_FLAG_AMBIGUOUS_STATE,
                )
            return FeatureFlagDecision(
                enabled=parsed, raw_value=str(raw),
                resolved_scope=scope, source="TENANT_REGISTRY",
                fallback_reason=None,
            )

        # 3. environment (explicit mapping, then os.environ var).
        raw = None
        source = "ENV"
        if env_var and env_var in env:
            raw = env[env_var]
        elif environment and environment in env:
            raw = env[environment]
        elif env_var:
            raw = os.environ.get(env_var)
        parsed = _parse_state(raw)
        if parsed is None:
            # 4. DEFAULT — OFF (directive 11). Ambiguous env also falls to OFF.
            return FeatureFlagDecision(
                enabled=False, raw_value=str(raw) if raw is not None else FLAG_DEFAULT_STATE,
                resolved_scope="environment",
                source="DEFAULT" if raw is None else "ENV",
                fallback_reason=INTEGRATION_FLAG_AMBIGUOUS_STATE if raw is not None else "default_off",
            )
        return FeatureFlagDecision(
            enabled=parsed, raw_value=str(raw),
            resolved_scope="environment", source=source,
            fallback_reason=None,
        )

    def is_enabled(
        self,
        *,
        invocation_path: Optional[str] = None,
        tenant_or_consumer: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> bool:
        return self.resolve(
            invocation_path=invocation_path,
            tenant_or_consumer=tenant_or_consumer,
            environment=environment,
        ).enabled


# ====================================================================
# Configuration errors (integration namespace only)
# ====================================================================

class FeatureFlagConfigurationError(RuntimeError):
    """Raised when the flag is constructed in a directive-forbidden configuration."""
    def __init__(self, code: str, msg: str):
        super().__init__(f"{code}: {msg}")
        self.code = code


__all__ = [
    "FLAG_NAME",
    "FLAG_DEFAULT_STATE",
    "FLAG_SCOPE",
    "FeatureFlag",
    "FeatureFlagDecision",
    "FeatureFlagConfigurationError",
]
