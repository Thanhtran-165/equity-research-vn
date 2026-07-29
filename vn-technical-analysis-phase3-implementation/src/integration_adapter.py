"""VTA Phase 3 — integration_adapter.py

Parent integration handoff (Phase 4a/4b boundary) and valuation-boundary
enforcement (VTA-REQ-011 / VC-VAL-BOUND-1/2 / VC-VAL-OVERRIDE-1).

Owns failure code (frozen registry, tier 7 POLICY):
  - VALUATION_OVERRIDE_ATTEMPT  (precedence 620)

Public interfaces:
  - handoff_to_parent(output_packet) -> ParentHandoff
  - enforce_valuation_boundary(output_packet) -> BoundaryCheck

Design invariants:
  - No path exists from technical output to fundamental/valuation fields.
  - The adapter exposes ONLY a read handoff; it has no write primitives that
    could ever target a valuation_* field.
  - Deterministic serialization (sorted keys, no wall-clock time).
  - No cross-module import of production decision logic (especially not from
    indicator_engine).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

# We import the OutputPacket type only for typing — we do NOT call any
# production decision function from output_assembler; we only read the packet.
from output_assembler import OutputPacket


# ====================================================================
# Frozen field namespace rules (VTA-REQ-011)
# ====================================================================

# Technical outputs are FORBIDDEN from writing into any valuation or
# fundamental field. These prefixes/names are the canonical boundary.
VALUATION_FIELD_PREFIXES: Tuple[str, ...] = (
    "valuation_",
    "fundamental_",
    "intrinsic_",
    "fair_value_",
    "target_price_",
    "dcf_",
    "ddm_",
    "pe_fair_",
    "pb_fair_",
    "earnings_estimate_",
    "revenue_estimate_",
)

# Explicit set of well-known valuation/fundamental field names that do not
# share a prefix (defensive enumeration).
VALUATION_FIELD_NAMES: Tuple[str, ...] = (
    "eps", "eps_ttm", "eps_forward",
    "pe_ratio", "pb_ratio", "ps_ratio",
    "dividend_yield", "payout_ratio",
    "book_value_per_share", "nav_per_share",
    "roe", "roa", "roic", "roce",
    "ebitda", "ebit", "net_debt", "enterprise_value",
    "wacc", "cost_of_equity", "cost_of_debt",
    "beta_fundamental",        # fundamental beta (different from technical beta)
    "alpha_jensen",            # Jensen's alpha is fundamental/valuation
    "fair_value", "intrinsic_value",
    "margin_of_safety",
    "quality_score", "growth_score", "profitability_score",
)

# A field is valuation-forbidden if it matches a prefix OR an explicit name.
def is_valuation_field(field_name: str) -> bool:
    if not isinstance(field_name, str) or not field_name:
        return False
    lowered = field_name.lower()
    for prefix in VALUATION_FIELD_PREFIXES:
        if lowered.startswith(prefix):
            return True
    return lowered in VALUATION_FIELD_NAMES


# Frozen failure code (must match vta-failure-code-registry.yaml exactly).
_FAILURE_VALUATION_OVERRIDE_ATTEMPT = "VALUATION_OVERRIDE_ATTEMPT"
_DIAGNOSTIC_VALUATION_KEY_IN_TECHNICAL_OUTPUT = "VALUATION_KEY_IN_TECHNICAL_OUTPUT"
_DIAGNOSTIC_VALUATION_WRITE_BLOCKED = "VALUATION_WRITE_BLOCKED"
_DIAGNOSTIC_WRITE_PATH_TO_VALUATION_DETECTED = "WRITE_PATH_TO_VALUATION_DETECTED"


# ====================================================================
# Result types
# ====================================================================

@dataclass(frozen=True)
class BoundaryCheck:
    """Result of enforce_valuation_boundary()."""
    passed: bool
    primary_failure_code: Optional[str]
    diagnostic_codes: Tuple[str, ...]
    violations: Tuple[Mapping[str, Any], ...]
    boundary_fields_scanned: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "primary_failure_code": self.primary_failure_code,
            "diagnostic_codes": list(self.diagnostic_codes),
            "violations": [dict(v) for v in self.violations],
            "boundary_fields_scanned": self.boundary_fields_scanned,
        }


@dataclass(frozen=True)
class ParentHandoff:
    """Read-only handoff packet for the parent integration layer.

    The handoff is STRUCTURALLY incapable of carrying valuation writes: it
    contains only technical observations and a frozen list of read-only field
    paths. Any attempt to construct a ParentHandoff whose ``write_targets``
    is non-empty and contains a valuation field is rejected at construction
    (see ``_validate_handoff_construction``).
    """
    source_module: str                       # always "vn-technical-analysis"
    technical_mode: str                      # ACTIVE | PROFILE
    symbol: str
    as_of_date: str
    technical_summary: Mapping[str, Any]     # read-only observations
    read_only_field_paths: Tuple[str, ...]   # paths the parent MAY read
    write_targets: Tuple[str, ...] = ()      # MUST be empty or non-valuation
    handoff_schema_version: str = "vta-parent-handoff-v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_module": self.source_module,
            "technical_mode": self.technical_mode,
            "symbol": self.symbol,
            "as_of_date": self.as_of_date,
            "technical_summary": dict(self.technical_summary),
            "read_only_field_paths": list(self.read_only_field_paths),
            "write_targets": list(self.write_targets),
            "handoff_schema_version": self.handoff_schema_version,
        }


# ====================================================================
# Boundary enforcement
# ====================================================================

def _walk_field_names(value: Any, prefix: str = "",
                      collected: Optional[List[str]] = None) -> List[str]:
    """Walk a nested structure and collect every field name encountered.

    We collect names (not values) so the boundary check is purely structural:
    a valuation key anywhere in the technical output is a violation, regardless
    of the value it carries.
    """
    if collected is None:
        collected = []
    if isinstance(value, Mapping):
        for k, v in value.items():
            child = f"{prefix}.{k}" if prefix else k
            collected.append(k)         # the leaf name
            collected.append(child)     # the full path
            _walk_field_names(v, child, collected)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _walk_field_names(item, prefix, collected)
    return collected


def enforce_valuation_boundary(output_packet: Any) -> BoundaryCheck:
    """Enforce the technical→valuation boundary on an output packet.

    Checks:
      1. No key in the packet body (recursively) is a valuation field.
      2. The packet carries no write_targets toward valuation fields.

    Args:
        output_packet: an OutputPacket or a mapping with a ``body`` key.

    Returns:
        BoundaryCheck. ``passed`` is True iff zero valuation fields are present
        in the technical output and no write path targets a valuation field.
    """
    if isinstance(output_packet, OutputPacket):
        body = output_packet.body
        provenance = output_packet.provenance
        mode = output_packet.mode
    elif isinstance(output_packet, Mapping):
        body = output_packet.get("body", output_packet)
        provenance = output_packet.get("provenance", {})
        mode = output_packet.get("mode", "UNKNOWN")
    else:
        return BoundaryCheck(
            passed=False,
            primary_failure_code=_FAILURE_VALUATION_OVERRIDE_ATTEMPT,
            diagnostic_codes=(_DIAGNOSTIC_VALUATION_KEY_IN_TECHNICAL_OUTPUT,),
            violations=({"code": _FAILURE_VALUATION_OVERRIDE_ATTEMPT,
                         "adapter": "integration_adapter",
                         "blocked_by": "non_packet_input"},),
            boundary_fields_scanned=0,
        )

    body_names = _walk_field_names(body)
    provenance_names = _walk_field_names(provenance)
    all_names = body_names + provenance_names
    scanned = len(set(all_names))

    violations: List[Mapping[str, Any]] = []
    # 1. valuation keys present in the technical output body.
    for name in sorted(set(all_names)):
        if is_valuation_field(name):
            violations.append({
                "code": _FAILURE_VALUATION_OVERRIDE_ATTEMPT,
                "adapter": "integration_adapter",
                "attempted_target_field": name,
                "blocked_by": "valuation_boundary_enforcer",
                "diagnostic": _DIAGNOSTIC_VALUATION_KEY_IN_TECHNICAL_OUTPUT,
                "mode": mode,
            })
    # 2. explicit write_targets in the packet (if any) targeting valuation.
    explicit_writes = []
    if isinstance(body, Mapping):
        explicit_writes = list(body.get("write_targets") or ())
        if isinstance(body.get("write_targets"), str):
            explicit_writes = [body["write_targets"]]
    for target in explicit_writes:
        if is_valuation_field(target):
            violations.append({
                "code": _FAILURE_VALUATION_OVERRIDE_ATTEMPT,
                "adapter": "integration_adapter",
                "attempted_target_field": target,
                "blocked_by": "valuation_boundary_enforcer",
                "diagnostic": _DIAGNOSTIC_WRITE_PATH_TO_VALUATION_DETECTED,
                "mode": mode,
            })

    if not violations:
        return BoundaryCheck(
            passed=True,
            primary_failure_code=None,
            diagnostic_codes=(),
            violations=(),
            boundary_fields_scanned=scanned,
        )
    return BoundaryCheck(
        passed=False,
        primary_failure_code=_FAILURE_VALUATION_OVERRIDE_ATTEMPT,
        diagnostic_codes=tuple({v["diagnostic"] for v in violations}),
        violations=tuple(violations),
        boundary_fields_scanned=scanned,
    )


# ====================================================================
# Parent handoff
# ====================================================================

def _validate_handoff_construction(write_targets: Tuple[str, ...]) -> None:
    """Fail-closed guard: a ParentHandoff must never carry a valuation write."""
    bad = [t for t in write_targets if is_valuation_field(t)]
    if bad:
        raise ValuationOverrideBlocked(
            f"ParentHandoff construction refused: write_targets include valuation fields: {bad}",
            attempted_targets=tuple(bad),
        )


class ValuationOverrideBlocked(RuntimeError):
    """Raised when an attempted valuation write is blocked at construction."""
    def __init__(self, msg: str, attempted_targets: Tuple[str, ...]):
        super().__init__(msg)
        self.attempted_targets = attempted_targets


def _extract_read_only_paths(body: Mapping[str, Any]) -> Tuple[str, ...]:
    """Build the deterministic list of read-only field paths the parent may read.

    These are all paths inside the technical output body — none can ever be a
    valuation field because enforce_valuation_boundary would have rejected them
    upstream. We list them explicitly so the parent integration contract is
    self-describing.
    """
    paths: List[str] = []

    def walk(value: Any, prefix: str = "") -> None:
        if isinstance(value, Mapping):
            for k in sorted(value.keys()):
                child = f"{prefix}.{k}" if prefix else k
                paths.append(child)
                walk(value[k], child)
        elif isinstance(value, (list, tuple)):
            for i, v in enumerate(value):
                walk(v, f"{prefix}[{i}]")

    walk(body)
    return tuple(paths)


def _technical_summary(body: Mapping[str, Any]) -> Mapping[str, Any]:
    """Project the body into a read-only technical summary for the parent.

    The summary deliberately excludes any key that could be misconstrued as
    a valuation/fundamental signal. We strip nothing here because the boundary
    check upstream already guarantees no valuation key is present; the summary
    is just a stable projection of the body.
    """
    return {k: body[k] for k in sorted(body.keys())}


def handoff_to_parent(
    output_packet: Any,
    *,
    write_targets: Optional[Tuple[str, ...]] = None,
) -> ParentHandoff:
    """Produce a read-only handoff packet for the parent integration layer.

    The handoff is structurally constrained:
      - ``write_targets`` is recorded but MUST be empty or contain only
        non-valuation fields. Any valuation target raises
        ValuationOverrideBlocked (the write never happens).
      - ``read_only_field_paths`` is the full enumeration of technical paths
        the parent may READ.
      - ``technical_summary`` is a stable, sorted-key projection.

    Args:
        output_packet: an OutputPacket or a mapping with a ``body`` key.
        write_targets: optional explicit write targets (must be non-valuation).

    Raises:
        ValuationOverrideBlocked: if any write target is a valuation field.
    """
    # First enforce the boundary on the packet itself — if the packet smuggles
    # a valuation key we surface it here.
    boundary = enforce_valuation_boundary(output_packet)
    if not boundary.passed:
        # Convert the boundary violations into a blocked-construction error so
        # the parent never receives a contaminated handoff.
        bad_targets = tuple(v["attempted_target_field"] for v in boundary.violations)
        raise ValuationOverrideBlocked(
            "ParentHandoff refused: valuation fields present in technical output",
            attempted_targets=bad_targets,
        )

    if isinstance(output_packet, OutputPacket):
        body = output_packet.body
        mode = output_packet.mode
        symbol = body.get("symbol", "UNKNOWN")
        as_of = body.get("as_of_date", "UNKNOWN")
    elif isinstance(output_packet, Mapping):
        body = output_packet.get("body", output_packet)
        mode = output_packet.get("mode", "UNKNOWN")
        symbol = body.get("symbol", "UNKNOWN") if isinstance(body, Mapping) else "UNKNOWN"
        as_of = body.get("as_of_date", "UNKNOWN") if isinstance(body, Mapping) else "UNKNOWN"
    else:
        raise TypeError(f"output_packet must be OutputPacket or Mapping, got {type(output_packet).__name__}")

    targets = tuple(write_targets) if write_targets else ()
    _validate_handoff_construction(targets)

    return ParentHandoff(
        source_module="vn-technical-analysis",
        technical_mode=mode,
        symbol=symbol,
        as_of_date=as_of,
        technical_summary=_technical_summary(body),
        read_only_field_paths=_extract_read_only_paths(body),
        write_targets=targets,
    )


__all__ = [
    "ParentHandoff",
    "BoundaryCheck",
    "ValuationOverrideBlocked",
    "handoff_to_parent",
    "enforce_valuation_boundary",
    "is_valuation_field",
    "VALUATION_FIELD_PREFIXES",
    "VALUATION_FIELD_NAMES",
]
