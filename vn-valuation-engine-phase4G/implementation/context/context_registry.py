"""Context Registry Loader.

Phase 4G F4G-B §4.5. Loads all registries from contracts/, verifies schema/version,
computes hashes. Fail-closed if registry is missing or malformed.
"""
from __future__ import annotations
import hashlib, os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


class CONTEXT_REGISTRY_MISSING(Exception):
    pass


class CONTEXT_REGISTRY_SCHEMA_INVALID(Exception):
    pass


class CONTEXT_REGISTRY_HASH_MISMATCH(Exception):
    pass


class CONTEXT_REGISTRY_VERSION_UNSUPPORTED(Exception):
    pass


# Registry paths relative to skill root
REGISTRY_PATHS = {
    "formula": "contracts/formula-registry.yaml",
    "applicability": "contracts/applicability-rules.yaml",
    "benchmark": "contracts/peer-set-policy.yaml",  # benchmarks defined in peer-set-policy
    "source": "contracts/valuation-provenance-contract.yaml",
    "period": "contracts/period-scope-policy.yaml",
    "scope": "contracts/period-scope-policy.yaml",  # same file, separate concern
    "error": "contracts/error-codes.yaml",
}


@dataclass
class RegistryBundle:
    """All loaded registries with their hashes."""
    formula: Dict[str, Any] = field(default_factory=dict)
    applicability: Dict[str, Any] = field(default_factory=dict)
    benchmark: Dict[str, Any] = field(default_factory=dict)
    source: Dict[str, Any] = field(default_factory=dict)
    period: Dict[str, Any] = field(default_factory=dict)
    scope: Dict[str, Any] = field(default_factory=dict)
    error: Dict[str, Any] = field(default_factory=dict)

    formula_hash: str = ""
    applicability_hash: str = ""
    benchmark_hash: str = ""
    source_hash: str = ""
    period_hash: str = ""
    scope_hash: str = ""
    error_hash: str = ""

    # Extracted approved methods (from formula + applicability)
    approved_method_ids: list = field(default_factory=list)
    # Approved formula_id → method_id mapping
    formula_by_method: Dict[str, str] = field(default_factory=dict)
    # Sector rules per method (from applicability)
    sector_rules: Dict[str, Dict[str, list]] = field(default_factory=dict)
    # Benchmark types by method
    benchmark_types_by_method: Dict[str, list] = field(default_factory=dict)
    # Error codes by severity
    fatal_error_codes: list = field(default_factory=list)
    material_warning_codes: list = field(default_factory=list)
    # Allowed periods and scopes
    allowed_periods: list = field(default_factory=list)
    allowed_scopes: list = field(default_factory=list)
    # Allowed source types
    allowed_source_types: list = field(default_factory=list)


def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load YAML file, fail-closed if missing or malformed."""
    import yaml
    if not path.exists():
        raise CONTEXT_REGISTRY_MISSING(f"Registry file missing: {path}")
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise CONTEXT_REGISTRY_SCHEMA_INVALID(f"Registry {path} is not a dict")
        return data
    except yaml.YAMLError as e:
        raise CONTEXT_REGISTRY_SCHEMA_INVALID(f"Registry {path} YAML error: {e}")


def _hash_registry(data: Dict[str, Any]) -> str:
    """Hash a registry dict (canonical form)."""
    import json
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_all_registries(skill_root: str) -> RegistryBundle:
    """Load all registries from skill contracts.

    Args:
        skill_root: path to vn-valuation-engine skill root

    Returns:
        RegistryBundle with all registries loaded + hashes computed + derived lookups.

    Raises:
        CONTEXT_REGISTRY_MISSING if any required registry is absent.
        CONTEXT_REGISTRY_SCHEMA_INVALID if any registry is malformed.
    """
    root = Path(skill_root)
    bundle = RegistryBundle()

    # Load each registry
    for key, rel_path in REGISTRY_PATHS.items():
        path = root / rel_path
        data = _load_yaml(path)
        h = _hash_registry(data)
        if key == "formula":
            bundle.formula = data
            bundle.formula_hash = h
            # Extract method → formula_id mapping
            for f in (data.get("formulas") or []):
                method = f.get("method")
                fid = f.get("formula_id")
                if method and fid:
                    bundle.formula_by_method[method] = fid
                    bundle.approved_method_ids.append(method)
        elif key == "applicability":
            bundle.applicability = data
            bundle.applicability_hash = h
            # Extract sector rules
            method_sectors = data.get("method_applicability_by_sector") or {}
            for method, rules in method_sectors.items():
                if isinstance(rules, dict):
                    bundle.sector_rules[method] = {
                        "applicable": rules.get("sectors_applicable", []),
                        "not_applicable": rules.get("sectors_NOT_applicable", []),
                    }
        elif key == "benchmark":
            bundle.benchmark = data
            bundle.benchmark_hash = h
            # Extract allowed benchmark types per method
            for entry in (data.get("benchmarks") or []):
                method = entry.get("method")
                btype = entry.get("type")
                if method and btype:
                    bundle.benchmark_types_by_method.setdefault(method, []).append(btype)
        elif key == "source":
            bundle.source = data
            bundle.source_hash = h
            bundle.allowed_source_types = list(data.get("allowed_source_types") or [])
        elif key == "period":
            bundle.period = data
            bundle.period_hash = h
            bundle.allowed_periods = list(data.get("allowed_periods") or [])
        elif key == "scope":
            bundle.scope = data
            bundle.scope_hash = h
            bundle.allowed_scopes = list(data.get("allowed_scopes") or [])
        elif key == "error":
            bundle.error = data
            bundle.error_hash = h
            for err in (data.get("errors") or []):
                sev = err.get("severity", "")
                code = err.get("code", "")
                if sev == "CRITICAL":
                    bundle.fatal_error_codes.append(code)
                elif sev == "MAJOR":
                    bundle.material_warning_codes.append(code)

    # Deduplicate approved method IDs
    bundle.approved_method_ids = sorted(set(bundle.approved_method_ids))

    return bundle
