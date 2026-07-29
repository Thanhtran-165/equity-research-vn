"""VTA Phase 3 — canonical_packet.py

Neutral schema-only contract for the mode output packet.

This module defines the *canonical* top-level field set both production
(output_assembler) and the independent verifier agree on. It is intentionally
schema-only: it carries NO decision logic, NO formula recompute, and NO
production state. Both sides may import it without breaking the verifier
independence boundary, because importing a pure schema declaration is not
importing production *decision* logic.

Per R3 directive Sections 5-6, the assembled output packet MUST emit the full
canonical field set so that every independent verifier VC that reasons over a
top-level field (weekly_history, daily_history, setup_coverage_status,
setup_coverage_denominator, computation_chain, provenance, archetype, ...)
can find its evidence in the packet regardless of mode.

Design rules:
  - Every canonical field is ALWAYS emitted, even when its value is null
    (nullable fields use None / empty). This makes the schema a stable
    contract: the verifier never has to guess whether a field is "absent
    by design" vs "absent because production forgot to emit it".
  - Mode-specific fields (binary_signals_6 for ACTIVE; profile_blocks,
    bullish_setups, bearish_setups for PROFILE) are layered on top of the
    shared canonical set, never instead of it.
  - ``computation_chain`` is the flat list of per-computation provenance
    nodes the verifier's provenance domain (VC-PROV-1/2/MISS-1, VC-FAB-VAL-1)
    and formula domain (VC-PRICE-BASIS-1/2) reason over.
  - ``provenance`` is the top-level provenance block carrying timestamp /
    provider / params (VC-PROV-2 required components).
"""

from __future__ import annotations

from typing import Any, Dict, Optional


# ====================================================================
# Canonical output field contract
# ====================================================================

# Field name -> python type. This is documentation + a light validation aid;
# it is not enforced as a hard JSON-Schema (the verifier reimplements the
# structural checks independently per the independence contract).
CANONICAL_OUTPUT_FIELDS: Dict[str, Any] = {
    "schema_version": str,
    "mode": str,                            # ACTIVE or PROFILE
    "instrument_id": str,                   # canonical symbol/ticker id
    "evaluation_timestamp": str,            # as_of_date (ISO)
    "price_basis": str,                     # adjusted | total_return_adjusted
    "adjustment_state": str,                # ADJUSTED | TOTAL_RETURN_ADJUSTED | UNKNOWN
    "weekly_history": Optional[int],        # count of input weekly bars (ACTIVE)
    "daily_history": Optional[int],         # count of input daily bars (PROFILE)
    "indicators": dict,                     # nullable (PROFILE omits ACTIVE indicators)
    "profile_blocks": dict,                 # nullable (ACTIVE omits PROFILE blocks)
    "bullish_setups": list,
    "bearish_setups": list,
    "archetype": str,                       # canonical archetype id (both modes)
    "tech_score": Optional[int],            # ACTIVE-only aggregate; None for PROFILE
    "setup_coverage_status": str,           # BULLISH_ONLY | INCOMPLETE_BEARISH_COVERAGE | COMPLETE_DIRECTIONAL_COVERAGE
    "setup_coverage_denominator": int,      # frozen 13 (8 bullish + 5 bearish)
    "analysis_status": str,                 # VALID | VALID_WITH_WARNINGS | ERROR
    "primary_failure_code": Optional[str],  # None when clean
    "diagnostic_failure_codes": list,
    "provenance": dict,                     # top-level provenance block (VC-PROV-2)
    "computation_chain_id": str,            # stable id for the computation path
    "computation_chain": list,              # flat list of per-computation nodes
    "error_code": Optional[str],            # None when no error envelope
}

# The frozen setup-coverage denominator (8 bullish + 5 bearish = 13) per the
# bearish setup registry and VC-BEARISH-DESIGN-4.
FROZEN_SETUP_COVERAGE_DENOMINATOR = 13

# The canonical archetype set. The profile_engine emits these six archetype
# ids (frozen per the bearish setup registry archetype_feed and precedence).
# VC-ARCH-AMBIG-1's deterministic fallback target is A-NO-CURRENT-SETUP.
CANONICAL_ARCHETYPES = (
    "A-TREND-FOLLOWING",
    "A-ACCUMULATION-BREAKOUT",
    "A-DISTRIBUTION",
    "A-TRAP-PRONE",
    "A-MIXED",
    "A-NO-CURRENT-SETUP",
)

# Default deterministic fallback archetype when classification is ambiguous.
DEFAULT_ARCHETYPE = "A-NO-CURRENT-SETUP"

# Default setup_coverage_status before Phase 4Q bearish qualification.
DEFAULT_SETUP_COVERAGE_STATUS = "INCOMPLETE_BEARISH_COVERAGE"

# Allowed setup_coverage_status enum (VC-PROFILE-VALID-4 / VC-COV-1).
SETUP_COVERAGE_STATUS_ENUM = (
    "BULLISH_ONLY",
    "INCOMPLETE_BEARISH_COVERAGE",
    "COMPLETE_DIRECTIONAL_COVERAGE",
)

# Allowed top-level keys per mode. additionalProperties:false semantics: any
# top-level key NOT in the mode's allowed set is a foreign key (schema drift).
# These supersede the per-mode schemas in output_assembler so production and
# the verifier share ONE definition of "what keys may appear".
COMMON_CANONICAL_KEYS = frozenset(CANONICAL_OUTPUT_FIELDS.keys())

ALLOWED_ACTIVE_TOP_KEYS = COMMON_CANONICAL_KEYS | {
    "binary_signals_6",     # ACTIVE-only aggregate (6 binary signals)
    "as_of_date",           # legacy alias for evaluation_timestamp (kept for back-compat)
    "symbol",               # legacy alias for instrument_id (kept for back-compat)
    "ticker",               # legacy alias (envelope-level)
    "warnings",             # diagnostic warnings list
    "is_valid",             # envelope validity flag
    "validation",           # post-assembly validation result envelope
    "boundary_check",       # valuation-boundary check result
    "language_check",       # REQ-007 language check result
    "lookahead_safe",       # VC-LOOKAHEAD-1 declaration
    "causal",               # VC-LOOKAHEAD-1 declaration alias
}

ALLOWED_PROFILE_TOP_KEYS = COMMON_CANONICAL_KEYS | {
    "as_of_date",                   # legacy alias for evaluation_timestamp
    "symbol",                       # legacy alias for instrument_id
    "ticker",                       # legacy alias (envelope-level)
    "warnings",                     # diagnostic warnings list
    "is_valid",                     # envelope validity flag
    "validation",                   # post-assembly validation result envelope
    "boundary_check",               # valuation-boundary check result
    "language_check",               # REQ-007 language check result
    "lookahead_safe",               # VC-LOOKAHEAD-1 declaration
    "causal",                       # VC-LOOKAHEAD-1 declaration alias
    "setups",                       # legacy alias for combined setup listings
    "blocks",                       # legacy alias for profile_blocks
    "setup_coverage",               # nested coverage block (alternative shape)
    "conflict_behavior",            # VC-BEARISH-DESIGN-3 resolution option
    "bull_bear_conflict_resolution",  # VC-BEARISH-DESIGN-3 alias
}


def allowed_top_keys(mode: str) -> frozenset:
    """Return the allowed top-level key set for a mode.

    Raises ValueError for an unknown mode so callers fail closed.
    """
    if mode == "ACTIVE":
        return ALLOWED_ACTIVE_TOP_KEYS
    if mode == "PROFILE":
        return ALLOWED_PROFILE_TOP_KEYS
    raise ValueError(f"unknown mode: {mode!r}")


def is_canonical_field(name: str) -> bool:
    """True if ``name`` is one of the canonical shared output fields."""
    return name in CANONICAL_OUTPUT_FIELDS


__all__ = [
    "CANONICAL_OUTPUT_FIELDS",
    "FROZEN_SETUP_COVERAGE_DENOMINATOR",
    "CANONICAL_ARCHETYPES",
    "DEFAULT_ARCHETYPE",
    "DEFAULT_SETUP_COVERAGE_STATUS",
    "SETUP_COVERAGE_STATUS_ENUM",
    "COMMON_CANONICAL_KEYS",
    "ALLOWED_ACTIVE_TOP_KEYS",
    "ALLOWED_PROFILE_TOP_KEYS",
    "allowed_top_keys",
    "is_canonical_field",
]
