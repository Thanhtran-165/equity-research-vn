"""Verification domain: BOUNDARY_ENFORCEMENT.

Owns 3 canonical VCs (per vta-VC-to-verifier-mapping.yaml
verifier_module_coverage = BOUNDARY (3), PHASE_6 obligations):

    VC-VAL-BOUND-1, VC-VAL-BOUND-2, VC-VAL-OVERRIDE-1.

All three enforce the VTA-REQ-011 valuation boundary: the technical-analysis
integration adapter MUST NOT have a write path to fundamental / valuation_*
fields, and the technical output schemas MUST reject valuation_* keys.

Independence: boundary checks inspect the output packet's declared write
targets and schema keys only. No production integration_adapter is imported.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .common import CheckOutcome, CODE_NONE, STATUS_FAIL, STATUS_PASS

DOMAIN_NAME = "boundary_enforcement"

OWNED_VC_IDS = (
    "VC-VAL-BOUND-1",
    "VC-VAL-BOUND-2",
    "VC-VAL-OVERRIDE-1",
)

# Fields the valuation engine owns; the technical adapter must never write
# these. The valuation_* prefix is the contract's canonical marker; the small
# explicit list covers the named fundamental fields referenced in
# VC-VAL-BOUND-* fixtures.
_VALUATION_PREFIX = "valuation_"
_VALUATION_FIELDS = frozenset(
    {
        "valuation",
        "valuation_fair_value",
        "valuation_target_price",
        "valuation_upside_pct",
        "valuation_method",
        "valuation_currency",
        "valuation_as_of_date",
        "valuation_confidence",
        "intrinsic_value",
        "fair_value",
        "target_price",
        "fundamental_pe_ratio",
        "fundamental_pb_ratio",
        "fundamental_eps",
        "fundamental_roe",
    }
)


def evaluate(ctx) -> Dict[str, CheckOutcome]:
    packet = ctx.output_packet
    outcomes: Dict[str, CheckOutcome] = {}
    for vc_id in OWNED_VC_IDS:
        handler = _HANDLERS.get(vc_id)
        if handler is None:
            outcomes[vc_id] = CheckOutcome.error(
                f"No handler bound for {vc_id}", vc_id=vc_id
            )
            continue
        try:
            outcomes[vc_id] = handler(ctx, packet)
        except Exception as exc:  # pragma: no cover - defensive
            outcomes[vc_id] = CheckOutcome.error(
                f"Handler raised: {type(exc).__name__}: {exc}", vc_id=vc_id
            )
    return outcomes


# ===========================================================================
# Helpers
# ===========================================================================


def _write_targets(packet: Dict[str, Any]) -> List[str]:
    """Extract declared write targets from an integration-adapter packet.

    The adapter contract requires that any field it intends to write be
    declared in `write_targets` (a list). Undeclared writes are themselves a
    violation; here we inspect the declaration so the verifier can flag any
    valuation_* target."""
    targets = packet.get("write_targets") or packet.get("writes") or []
    if isinstance(targets, list):
        return [str(t) for t in targets if t is not None]
    return []


def _find_valuation_fields(names: Sequence[str]) -> List[str]:
    out: List[str] = []
    for name in names:
        if not isinstance(name, str):
            continue
        if name.startswith(_VALUATION_PREFIX) or name in _VALUATION_FIELDS:
            out.append(name)
    return out


def _all_field_keys(node: Any, prefix: str = "") -> List[str]:
    """Recursively collect all field names in the packet (for schema-level
    valuation-key rejection)."""
    out: List[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            path = f"{prefix}.{key}" if prefix else key
            out.append(path)
            out.extend(_all_field_keys(value, path))
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            path = f"{prefix}[{idx}]"
            out.extend(_all_field_keys(value, path))
    return out


# ===========================================================================
# Per-VC handlers
# ===========================================================================


def _vc_val_bound_1(ctx, packet) -> CheckOutcome:
    """VC-VAL-BOUND-1: integration adapter MUST NOT have a write path to
    fundamental/valuation fields."""
    targets = _write_targets(packet)
    offending = _find_valuation_fields(targets)
    if offending:
        return CheckOutcome.fail(
            "VALUATION_OVERRIDE_ATTEMPT",
            ["WRITE_PATH_TO_VALUATION_DETECTED"],
            reason="integration adapter declares write path to valuation fields",
            write_targets=targets,
            offending=offending,
        )
    return CheckOutcome.pass_clean(write_targets=targets, offending=[])


def _vc_val_bound_2(ctx, packet) -> CheckOutcome:
    """VC-VAL-BOUND-2: schema validation rejects valuation_* keys in
    technical output. The verifier independently scans the packet for any
    valuation_* field at any depth; presence means the schema did not reject
    the key."""
    all_keys = _all_field_keys(packet)
    # Consider both the leaf name and the full path for prefix matching.
    leaf_names = {key.rsplit(".", 1)[-1].split("[", 1)[0] for key in all_keys}
    offending_paths = [
        key
        for key in all_keys
        if (
            key.split(".")[-1].split("[", 1)[0].startswith(_VALUATION_PREFIX)
            or key.split(".")[-1].split("[", 1)[0] in _VALUATION_FIELDS
        )
    ]
    # Exclude provenance/warnings/errors envelopes from the schema check.
    offending_paths = [
        p
        for p in offending_paths
        if not p.startswith("provenance.")
        and not p.startswith("warnings.")
        and not p.startswith("errors.")
        and not p.startswith("computation_chain.")
    ]
    if offending_paths:
        return CheckOutcome.fail(
            "VALUATION_OVERRIDE_ATTEMPT",
            ["VALUATION_KEY_IN_TECHNICAL_OUTPUT"],
            reason="technical output contains valuation_* keys",
            offending_paths=offending_paths[:20],
            offending_count=len(offending_paths),
        )
    return CheckOutcome.pass_clean(
        scanned_keys=len(all_keys), offending_count=0
    )


def _vc_val_override_1(ctx, packet) -> CheckOutcome:
    """VC-VAL-OVERRIDE-1: integration adapter cannot modify valuation_*
    fields. The verifier checks both declared write targets and a diff
    envelope (if present) for valuation field modifications."""
    targets = _write_targets(packet)
    offending_targets = _find_valuation_fields(targets)
    # Diff envelope: packet may carry `modification_log` or `writes_applied`
    # describing attempted modifications.
    mods = packet.get("writes_applied") or packet.get("modification_log") or []
    mod_fields: List[str] = []
    if isinstance(mods, list):
        for entry in mods:
            if isinstance(entry, dict):
                field = entry.get("field") or entry.get("target")
                if isinstance(field, str):
                    mod_fields.append(field)
            elif isinstance(entry, str):
                mod_fields.append(entry)
    offending_mods = _find_valuation_fields(mod_fields)
    # The adapter must report a block when an attempt was made.
    blocked = packet.get("blocked") or packet.get("writes_blocked") or []
    blocked_fields = {
        (b.get("field") if isinstance(b, dict) else b) for b in (blocked or [])
    }
    unblocked_violations = [
        f for f in offending_mods if f not in blocked_fields
    ]
    if offending_targets or unblocked_violations:
        return CheckOutcome.fail(
            "VALUATION_OVERRIDE_ATTEMPT",
            ["VALUATION_WRITE_BLOCKED"],
            reason=(
                "integration adapter attempted to modify valuation_* fields "
                "without recording a block"
            ),
            offending_write_targets=offending_targets,
            offending_modifications=unblocked_violations,
            blocked_fields=sorted(str(f) for f in blocked_fields if f),
        )
    return CheckOutcome.pass_clean(
        offending_targets=offending_targets,
        offending_modifications=unblocked_violations,
        blocked_fields=sorted(str(f) for f in blocked_fields if f),
    )


_HANDLERS = {
    "VC-VAL-BOUND-1": _vc_val_bound_1,
    "VC-VAL-BOUND-2": _vc_val_bound_2,
    "VC-VAL-OVERRIDE-1": _vc_val_override_1,
}
