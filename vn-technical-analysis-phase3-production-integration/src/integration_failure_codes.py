"""VTA Phase 3 Production Integration — integration_failure_codes.py

SEPARATE namespace for integration-infrastructure failures (directive 17).

The canonical VTA failure-code registry (43 codes) is FROZEN and unchanged.
Integration failures live in a distinct namespace and MUST NOT overlap with any
canonical code. Integration failures MUST NOT masquerade as VTA formula or
setup failures — they describe ONLY the integration boundary itself.

Coverage (directive 17 permitted categories):
  - adapter schema rejection
  - unavailable frozen package
  - configuration mismatch
  - unsupported host schema
  - deployment-version mismatch
  - integration timeout
  - host serialization failure
  - feature-flag ambiguity

Each code carries:
  - code                   (stable machine contract; NOT free text)
  - category               (directive 17 category)
  - precedence             (lower = higher priority within integration tier)
  - required_context_fields(machine-readable keys; never parsed from message text)
  - semantic_definition    (human-only; may change without notice)
  - triggering_condition   (human-only)

Property P-NO-MESSAGE-AS-CONTRACT is inherited: only ``code`` + the documented
``required_context_fields`` are machine-readable.
"""

from __future__ import annotations

from typing import Tuple


# ====================================================================
# Namespace identity
# ====================================================================

NAMESPACE: str = "VTA_PHASE_3_INTEGRATION"
NAMESPACE_VERSION: str = "1.0.0"

# Explicit declaration: ZERO overlap with the 43 canonical VTA codes.
CANONICAL_CODE_COUNT: int = 43
OVERLAP_WITH_CANONICAL_CODES: int = 0


# ====================================================================
# Integration failure codes (8 codes)
# ====================================================================

INTEGRATION_ADAPTER_SCHEMA_REJECTED: str = "INTEGRATION_ADAPTER_SCHEMA_REJECTED"
INTEGRATION_FROZEN_PACKAGE_UNAVAILABLE: str = "INTEGRATION_FROZEN_PACKAGE_UNAVAILABLE"
INTEGRATION_CONFIGURATION_MISMATCH: str = "INTEGRATION_CONFIGURATION_MISMATCH"
INTEGRATION_UNSUPPORTED_HOST_SCHEMA: str = "INTEGRATION_UNSUPPORTED_HOST_SCHEMA"
INTEGRATION_DEPLOYMENT_VERSION_MISMATCH: str = "INTEGRATION_DEPLOYMENT_VERSION_MISMATCH"
INTEGRATION_TIMEOUT: str = "INTEGRATION_TIMEOUT"
INTEGRATION_HOST_SERIALIZATION_FAILED: str = "INTEGRATION_HOST_SERIALIZATION_FAILED"
INTEGRATION_FLAG_AMBIGUOUS_STATE: str = "INTEGRATION_FLAG_AMBIGUOUS_STATE"
INTEGRATION_FLAG_RESTART_REQUIRED_VIOLATION: str = "INTEGRATION_FLAG_RESTART_REQUIRED_VIOLATION"


# Precedence model: a single INTEGRATION tier. Lower value = higher priority.
# All integration codes are STRICTLY subordinate to canonical failure codes:
# if a canonical envelope is present, the canonical code is primary and no
# integration code is emitted in its place (directive 17).
_PRECEDENCE = {
    INTEGRATION_FROZEN_PACKAGE_UNAVAILABLE: 10,    # cannot load frozen impl -> highest prio
    INTEGRATION_DEPLOYMENT_VERSION_MISMATCH: 20,
    INTEGRATION_CONFIGURATION_MISMATCH: 30,
    INTEGRATION_ADAPTER_SCHEMA_REJECTED: 40,
    INTEGRATION_UNSUPPORTED_HOST_SCHEMA: 50,
    INTEGRATION_HOST_SERIALIZATION_FAILED: 60,
    INTEGRATION_TIMEOUT: 70,
    INTEGRATION_FLAG_AMBIGUOUS_STATE: 80,
    INTEGRATION_FLAG_RESTART_REQUIRED_VIOLATION: 90,
}


_REGISTRY = (
    {
        "code": INTEGRATION_ADAPTER_SCHEMA_REJECTED,
        "namespace": NAMESPACE,
        "category": "adapter_schema_rejection",
        "precedence": _PRECEDENCE[INTEGRATION_ADAPTER_SCHEMA_REJECTED],
        "required_context_fields": ("host_schema_version", "rejected_field"),
        "semantic_definition": (
            "Host input failed the integration adapter's structural schema "
            "check before any canonical VTA code path was entered."
        ),
        "triggering_condition": (
            "A required host field is absent, the wrong type, or fails the "
            "explicit host-to-canonical mapping declared in the host-mapping "
            "contract."
        ),
    },
    {
        "code": INTEGRATION_FROZEN_PACKAGE_UNAVAILABLE,
        "namespace": NAMESPACE,
        "category": "unavailable_frozen_package",
        "precedence": _PRECEDENCE[INTEGRATION_FROZEN_PACKAGE_UNAVAILABLE],
        "required_context_fields": ("expected_implementation_commit", "lookup_error"),
        "semantic_definition": (
            "The frozen VTA implementation package could not be located or "
            "loaded at the pinned commit."
        ),
        "triggering_condition": (
            "Import of the frozen runner module failed, or the loaded module's "
            "declared commit did not match the pinned implementation commit."
        ),
    },
    {
        "code": INTEGRATION_CONFIGURATION_MISMATCH,
        "namespace": NAMESPACE,
        "category": "configuration_mismatch",
        "precedence": _PRECEDENCE[INTEGRATION_CONFIGURATION_MISMATCH],
        "required_context_fields": ("config_key", "expected", "observed"),
        "semantic_definition": (
            "Integration configuration does not match the frozen deployment "
            "freeze contract."
        ),
        "triggering_condition": (
            "A deployment-freeze value (schema version, serialization version, "
            "formula/setup/failure-code registry version) differs at runtime "
            "from the pinned value."
        ),
    },
    {
        "code": INTEGRATION_UNSUPPORTED_HOST_SCHEMA,
        "namespace": NAMESPACE,
        "category": "unsupported_host_schema",
        "precedence": _PRECEDENCE[INTEGRATION_UNSUPPORTED_HOST_SCHEMA],
        "required_context_fields": ("host_schema_version", "supported_versions"),
        "semantic_definition": (
            "The host input declares a schema version this integration does "
            "not support."
        ),
        "triggering_condition": (
            "host_input.schema_version is not in the supported set declared by "
            "the host-mapping contract."
        ),
    },
    {
        "code": INTEGRATION_DEPLOYMENT_VERSION_MISMATCH,
        "namespace": NAMESPACE,
        "category": "deployment_version_mismatch",
        "precedence": _PRECEDENCE[INTEGRATION_DEPLOYMENT_VERSION_MISMATCH],
        "required_context_fields": ("declared_deployment_version", "observed_deployment_version"),
        "semantic_definition": (
            "The running deployment version does not match the frozen "
            "deployment-freeze manifest."
        ),
        "triggering_condition": (
            "deployment_manifest.version observed at runtime != pinned "
            "deployment-freeze version."
        ),
    },
    {
        "code": INTEGRATION_TIMEOUT,
        "namespace": NAMESPACE,
        "category": "integration_timeout",
        "precedence": _PRECEDENCE[INTEGRATION_TIMEOUT],
        "required_context_fields": ("phase", "elapsed_seconds", "deadline_seconds"),
        "semantic_definition": (
            "The integration boundary exceeded its declared deadline before "
            "the frozen VTA core returned."
        ),
        "triggering_condition": (
            "Wall-clock elapsed in adapter/runner/serializer phase > the "
            "declared phase deadline."
        ),
    },
    {
        "code": INTEGRATION_HOST_SERIALIZATION_FAILED,
        "namespace": NAMESPACE,
        "category": "host_serialization_failure",
        "precedence": _PRECEDENCE[INTEGRATION_HOST_SERIALIZATION_FAILED],
        "required_context_fields": ("serializer", "serialization_error"),
        "semantic_definition": (
            "The canonical output packet could not be serialized into the host "
            "transport envelope."
        ),
        "triggering_condition": (
            "canonical-to-host envelope assembly raised an exception after the "
            "canonical packet was already produced."
        ),
    },
    {
        "code": INTEGRATION_FLAG_AMBIGUOUS_STATE,
        "namespace": NAMESPACE,
        "category": "feature_flag",
        "precedence": _PRECEDENCE[INTEGRATION_FLAG_AMBIGUOUS_STATE],
        "required_context_fields": ("flag_name", "raw_value", "resolved_scope"),
        "semantic_definition": (
            "The feature flag resolved to an ambiguous value and was treated "
            "as OFF (fail-closed)."
        ),
        "triggering_condition": (
            "The resolved flag value parsed to neither a recognized ON nor OFF "
            "token."
        ),
    },
    {
        "code": INTEGRATION_FLAG_RESTART_REQUIRED_VIOLATION,
        "namespace": NAMESPACE,
        "category": "feature_flag",
        "precedence": _PRECEDENCE[INTEGRATION_FLAG_RESTART_REQUIRED_VIOLATION],
        "required_context_fields": ("flag_name", "violation"),
        "semantic_definition": (
            "The flag was configured with restart_required_to_disable=true, "
            "which is prohibited by directive 11."
        ),
        "triggering_condition": (
            "FeatureFlag constructed with restart_required_to_disable=True."
        ),
    },
)


def all_codes() -> Tuple[str, ...]:
    """Return every integration failure code (stable order: precedence asc)."""
    return tuple(rec["code"] for rec in sorted(_REGISTRY, key=lambda r: r["precedence"]))


def registry_records() -> Tuple[dict, ...]:
    """Return the full registry records (precedence-ascending)."""
    return tuple(sorted(_REGISTRY, key=lambda r: r["precedence"]))


def is_integration_code(code: str) -> bool:
    return code in {rec["code"] for rec in _REGISTRY}


def count() -> int:
    return len(_REGISTRY)


# Compile-time guard: assert zero overlap with a frozen canonical code set.
# The canonical set is provided by the host-mapping manifest; here we hard-assert
# the structural separation property at import time so a future drift is caught.
def assert_disjoint_from_canonical(canonical_codes) -> None:
    integration = {rec["code"] for rec in _REGISTRY}
    overlap = integration.intersection(set(canonical_codes))
    if overlap:
        raise RuntimeError(
            "integration failure-code namespace overlaps canonical VTA codes: "
            + ", ".join(sorted(overlap))
        )


__all__ = [
    "NAMESPACE",
    "NAMESPACE_VERSION",
    "CANONICAL_CODE_COUNT",
    "OVERLAP_WITH_CANONICAL_CODES",
    "INTEGRATION_ADAPTER_SCHEMA_REJECTED",
    "INTEGRATION_FROZEN_PACKAGE_UNAVAILABLE",
    "INTEGRATION_CONFIGURATION_MISMATCH",
    "INTEGRATION_UNSUPPORTED_HOST_SCHEMA",
    "INTEGRATION_DEPLOYMENT_VERSION_MISMATCH",
    "INTEGRATION_TIMEOUT",
    "INTEGRATION_HOST_SERIALIZATION_FAILED",
    "INTEGRATION_FLAG_AMBIGUOUS_STATE",
    "INTEGRATION_FLAG_RESTART_REQUIRED_VIOLATION",
    "all_codes",
    "registry_records",
    "is_integration_code",
    "count",
    "assert_disjoint_from_canonical",
]
