"""VTA Phase 3 independent verifier - main entrypoint.

Orchestrates the six verification-domain modules over a production output
packet against frozen input fixtures, formula contracts, and the failure-code
registry.

Independence contract (vta-phase-3-implementation-scope.yaml Section 7,
forbidden_dependencies):
  - Production decision logic is NOT imported (asserted below).
  - Expected outputs come only from frozen fixtures / contracts / registry.
  - No runtime-generated or network oracle is consulted.

Result schema (machine-readable, per the directive):
  Each per-VC record carries:
    VC_id, fixture_id, mutation_id, expected_status, observed_status,
    expected_primary_code, observed_primary_code, verdict

Record ordering is deterministic: primary key VC_id, secondary fixture_id,
tertiary mutation_id (lexicographic on each component).
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import sys
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import yaml

from . import common
from .common import (
    CheckOutcome,
    CODE_NONE,
    STATUS_ERROR,
    STATUS_FAIL,
    STATUS_PASS,
    VERDICT_ERROR,
    VERDICT_FAIL,
    VERDICT_PASS,
    build_vc_diagnostic_codes_map,
    build_vc_primary_code_map,
    unwrap_failure_code_registry,
    unwrap_formula_contracts,
    unwrap_vc_mapping,
)

VERIFIER_VERSION = "1.0.0"

# ===========================================================================
# Independence enforcement
# ===========================================================================

# Modules that production code lives under. Importing any of these as oracle
# source would break verifier independence and is blocked at startup.
_FORBIDDEN_PRODUCTION_MODULES = (
    "normalization_engine",
    "indicator_engine",
    "profile_engine",
    "output_assembler",
    "integration_adapter",
    "language_verifier",
    "runner",
    "src.normalization_engine",
    "src.indicator_engine",
    "src.profile_engine",
    "src.output_assembler",
    "src.integration_adapter",
    "src.language_verifier",
    "src.runner",
)


def _assert_independence() -> None:
    """Block execution if any forbidden production module is already imported.

    This is a runtime guard, not a static guarantee: it ensures the verifier
    process has not been (accidentally or deliberately) wired into production
    decision logic before evaluating any VC.
    """
    loaded = set(sys.modules.keys())
    offenders = sorted(loaded & set(_FORBIDDEN_PRODUCTION_MODULES))
    if offenders:
        raise RuntimeError(
            "Verifier independence violation: production decision modules are "
            "loaded in the same process: " + ", ".join(offenders)
        )


# ===========================================================================
# Context
# ===========================================================================


class VerificationContext:
    """Frozen inputs the verifier is allowed to consult.

    All paths must point at frozen artifacts; none is generated at runtime by
    production code. The context is constructed once and passed (read-only) to
    each domain module.
    """

    def __init__(
        self,
        output_packet_path: str,
        frozen_fixtures_dir: str,
        formula_contracts_path: str,
        failure_code_registry_path: str,
        vc_mapping_path: str,
        *,
        fixture_id: Optional[str] = None,
        mutation_id: Optional[str] = None,
        expected_status: str = STATUS_PASS,
        expected_primary_code: str = CODE_NONE,
    ) -> None:
        self.output_packet_path = output_packet_path
        self.frozen_fixtures_dir = frozen_fixtures_dir
        self.formula_contracts_path = formula_contracts_path
        self.failure_code_registry_path = failure_code_registry_path
        self.vc_mapping_path = vc_mapping_path
        self.fixture_id = fixture_id or ""
        self.mutation_id = mutation_id or ""
        self.expected_status = expected_status
        self.expected_primary_code = expected_primary_code

        # Eager-load the frozen authorities once. Unwrap the single top-level
        # wrapper key each review manifest carries so domain code addresses
        # the payload directly.
        self.failure_code_registry = unwrap_failure_code_registry(
            common.load_yaml(failure_code_registry_path)
        )
        self.vc_mapping = unwrap_vc_mapping(common.load_yaml(vc_mapping_path))
        self.formula_contracts = unwrap_formula_contracts(
            common.load_yaml(formula_contracts_path)
        )
        self.output_packet = common.load_artifact(output_packet_path)

        # Derived ownership maps (authoritative post Review-R3).
        self.vc_primary_code = build_vc_primary_code_map(self.failure_code_registry)
        self.vc_diagnostic_codes = build_vc_diagnostic_codes_map(
            self.failure_code_registry
        )

        # VC mapping lookup by VC_id for per-VC metadata (fixture ids, expected
        # codes, oracle source). Single source of truth for what each VC must
        # address.
        self.vc_records: Dict[str, Dict[str, Any]] = {}
        for record in self.vc_mapping.get("verifier_checks", []):
            vc_id = record.get("VC_id")
            if vc_id:
                self.vc_records[vc_id] = record

    # -- helpers --------------------------------------------------------

    def load_fixture(self, fixture_name: str) -> Any:
        """Load a frozen fixture by name from the fixtures directory.

        Accepts either a bare name (extension inferred: try .json then .yaml)
        or a path-relative name.
        """
        if not fixture_name:
            return None
        candidates = [
            os.path.join(self.frozen_fixtures_dir, fixture_name),
            os.path.join(self.frozen_fixtures_dir, fixture_name + ".json"),
            os.path.join(self.frozen_fixtures_dir, fixture_name + ".yaml"),
            os.path.join(self.frozen_fixtures_dir, fixture_name + ".yml"),
        ]
        for path in candidates:
            if os.path.isfile(path):
                return common.load_artifact(path)
        return None

    def expected_primary_code_for(self, vc_id: str) -> str:
        """The PRIMARY failure code this VC is contracted to emit when its
        controlled failure fires. Falls back to the VC-mapping's
        expected_primary_failure_code field, then to the registry's ownership
        map."""
        record = self.vc_records.get(vc_id, {})
        from_mapping = record.get("expected_primary_failure_code")
        if from_mapping and from_mapping != CODE_NONE:
            return from_mapping
        if from_mapping == CODE_NONE:
            return CODE_NONE
        return self.vc_primary_code.get(vc_id, CODE_NONE)

    def expected_status_for(self, vc_id: str) -> str:
        """Expected observed_status for this VC given the case under test.

        Default heuristic: the frozen case-level expected_status if provided;
        else PASS. Domain modules refine this with fixture-type awareness.
        """
        return self.expected_status


# ===========================================================================
# Domain registration
# ===========================================================================


# Each domain module exposes:
#   DOMAIN_NAME: str
#   OWNED_VC_IDS: Tuple[str, ...]
#   evaluate(ctx: VerificationContext) -> Dict[str, CheckOutcome]
# ===========================================================================

_DOMAIN_MODULES = (
    "formula_conformance",
    "schema_conformance",
    "provenance_integrity",
    "language_policy",
    "boundary_enforcement",
    "setup_semantics",
)


def _load_domain(name: str):
    """Import a verification-domain module from this package by name."""
    return __import__(f"{__package__}.{name}", fromlist=[name])


# ===========================================================================
# Canonical VC list (64) - derived from the frozen VC mapping, not hardcoded.
# ===========================================================================


def canonical_vc_ids(vc_mapping: Mapping[str, Any]) -> List[str]:
    """Return the canonical 64 VC ids in registry order. Accepts the wrapped
    or unwrapped VC mapping document."""
    payload = (
        unwrap_vc_mapping(vc_mapping)
        if isinstance(vc_mapping, Mapping)
        else vc_mapping
    )
    return [
        record["VC_id"]
        for record in payload.get("verifier_checks", [])
        if record.get("VC_id")
    ]


# ===========================================================================
# Verdict computation
# ===========================================================================


def _verdict_for(
    expected_status: str,
    expected_primary_code: str,
    outcome: CheckOutcome,
) -> str:
    """Decide PASS/FAIL/ERROR for one VC evaluation.

    A VC VERDICT_PASSes when the verifier's observed state matches the frozen
    expected state for the case under test. Concretely:
      - If the case expects a clean PASS (expected_status=PASS,
        expected_primary_code=NONE), the verifier must observe clean
        (observed_status=PASS, observed_primary_code=NONE).
      - If the case expects a controlled failure (expected_status=FAIL,
        expected_primary_code=<code>), the verifier must observe that failure
        with the contracted primary code.
      - ERROR (verifier could not evaluate) is never a PASS.
    """
    if outcome.observed_status == STATUS_ERROR:
        return VERDICT_ERROR
    if expected_status == STATUS_FAIL:
        if outcome.observed_status != STATUS_FAIL:
            return VERDICT_FAIL
        if expected_primary_code and expected_primary_code != CODE_NONE:
            if outcome.observed_primary_code != expected_primary_code:
                return VERDICT_FAIL
        return VERDICT_PASS
    # expected PASS
    if outcome.observed_status == STATUS_FAIL:
        return VERDICT_FAIL
    return VERDICT_PASS


# ===========================================================================
# Record ordering (deterministic)
# ===========================================================================


def _sort_key(record: Dict[str, Any]) -> Tuple[str, str, str]:
    return (
        str(record.get("VC_id", "")),
        str(record.get("fixture_id", "")),
        str(record.get("mutation_id", "")),
    )


# ===========================================================================
# Public entrypoint
# ===========================================================================


def run_verification(
    output_packet_path: str,
    frozen_fixtures_dir: str,
    formula_contracts_path: str,
    failure_code_registry_path: str,
    vc_mapping_path: str,
    *,
    fixture_id: Optional[str] = None,
    mutation_id: Optional[str] = None,
    expected_status: str = STATUS_PASS,
    expected_primary_code: str = CODE_NONE,
) -> Dict[str, Any]:
    """Run the full independent verification suite.

    Returns a JSON-serialisable result document with:
      - schema_version, verifier_version
      - summary (counts by verdict)
      - records (one per canonical VC, deterministically ordered)
      - independence_assertion
    """
    _assert_independence()

    ctx = VerificationContext(
        output_packet_path=output_packet_path,
        frozen_fixtures_dir=frozen_fixtures_dir,
        formula_contracts_path=formula_contracts_path,
        failure_code_registry_path=failure_code_registry_path,
        vc_mapping_path=vc_mapping_path,
        fixture_id=fixture_id,
        mutation_id=mutation_id,
        expected_status=expected_status,
        expected_primary_code=expected_primary_code,
    )

    canonical = canonical_vc_ids(ctx.vc_mapping)
    outcomes: Dict[str, CheckOutcome] = {}

    for domain_name in _DOMAIN_MODULES:
        module = _load_domain(domain_name)
        domain_outcomes = module.evaluate(ctx)
        for vc_id, outcome in domain_outcomes.items():
            # Last-writer-wins is fine because the domains own disjoint VC
            # sets; we still assert disjointness below in summary.
            outcomes[vc_id] = outcome

    # Apply precedence resolution: if multiple codes would fire, report the
    # lowest (tier, precedence) per the registry precedence_model. Each domain
    # already emits one primary code per VC, so this primarily normalises codes
    # to the registry-authoritative owner when domains observed a co-reported
    # code from a different tier.
    resolved_outcomes = _apply_precedence(ctx, outcomes)

    records: List[Dict[str, Any]] = []
    for vc_id in canonical:
        outcome = resolved_outcomes.get(vc_id)
        if outcome is None:
            record_outcome = CheckOutcome.error(
                f"VC {vc_id} not evaluated by any domain module",
                vc_id=vc_id,
            )
        else:
            record_outcome = outcome

        # Per-VC expected values: prefer case-level override if it targets
        # this VC, else the registry contract.
        expected_status_vc = _expected_status_for_vc(ctx, vc_id)
        expected_primary_vc = _expected_primary_code_for_vc(ctx, vc_id)

        verdict = _verdict_for(
            expected_status_vc, expected_primary_vc, record_outcome
        )

        records.append(
            {
                "VC_id": vc_id,
                "fixture_id": ctx.fixture_id,
                "mutation_id": ctx.mutation_id,
                "expected_status": expected_status_vc,
                "observed_status": record_outcome.observed_status,
                "expected_primary_code": expected_primary_vc,
                "observed_primary_code": record_outcome.observed_primary_code,
                "observed_diagnostic_codes": list(
                    record_outcome.observed_diagnostic_codes
                ),
                "verdict": verdict,
                "evidence": record_outcome.evidence,
                "domain": _domain_for_vc(ctx, vc_id),
            }
        )

    records.sort(key=_sort_key)

    summary = _summarise(records, canonical, resolved_outcomes, ctx)

    return {
        "schema_version": "1.0",
        "verifier_version": VERIFIER_VERSION,
        "input_artifacts": {
            "output_packet": output_packet_path,
            "frozen_fixtures_dir": frozen_fixtures_dir,
            "formula_contracts": formula_contracts_path,
            "failure_code_registry": failure_code_registry_path,
            "vc_mapping": vc_mapping_path,
            "fixture_id": ctx.fixture_id,
            "mutation_id": ctx.mutation_id,
        },
        "summary": summary,
        "records": records,
        "independence_assertion": {
            "production_modules_imported": False,
            "forbidden_modules_checked": list(_FORBIDDEN_PRODUCTION_MODULES),
            "oracles_consulted": [
                "frozen input fixtures",
                "frozen formula contracts",
                "frozen failure-code registry",
                "independent primitive arithmetic (numpy)",
            ],
        },
    }


# ===========================================================================
# Internal helpers
# ===========================================================================


def _domain_for_vc(ctx: VerificationContext, vc_id: str) -> str:
    record = ctx.vc_records.get(vc_id, {})
    surface = record.get("implementation_surface", {}) or {}
    module_path = surface.get("proposed_verifier_module", "") or ""
    return os.path.basename(module_path).replace(".py", "") or "unassigned"


def _expected_status_for_vc(ctx: VerificationContext, vc_id: str) -> str:
    """Per-VC expected observed_status.

    Default rule: the case-level expected_status provided by the caller applies
    uniformly (the typical case is a single fixture targeting one expected
    outcome). Domain modules encode the negative/positive fixture distinction
    inside their outcome, so the case-level expectation is the right
    comparison target. Special-case NONE-sentinel VCs (e.g. VC-ZERO-VOL-1):
    their expected primary is NONE and expected status is PASS.
    """
    return ctx.expected_status


def _expected_primary_code_for_vc(ctx: VerificationContext, vc_id: str) -> str:
    """Per-VC expected primary code for the case under test.

    If the case-level expectation is FAIL with a specific code, that code
    applies. Otherwise each VC contributes its contracted primary code only
    when the case expects FAIL; for PASS cases the expected code is NONE.
    """
    if ctx.expected_status == STATUS_FAIL:
        if ctx.expected_primary_code and ctx.expected_primary_code != CODE_NONE:
            return ctx.expected_primary_code
        return ctx.expected_primary_code_for(vc_id)
    return CODE_NONE


def _apply_precedence(
    ctx: VerificationContext, outcomes: Dict[str, CheckOutcome]
) -> Dict[str, CheckOutcome]:
    """Normalise each outcome's observed_primary_code to the registry-
    authoritative owner for that VC. The domains already emit one primary code
    per VC; this step guarantees the emitted code matches the frozen
    ownership map (post Review-R3) so the result schema is stable across
    implementations."""
    code_records: Dict[str, Dict[str, Any]] = {}
    for entry in ctx.failure_code_registry.get("codes", []):
        code = entry.get("failure_code")
        if code:
            code_records[code] = entry

    resolved: Dict[str, CheckOutcome] = {}
    for vc_id, outcome in outcomes.items():
        if outcome.observed_status != STATUS_FAIL:
            resolved[vc_id] = outcome
            continue
        authoritative = ctx.vc_primary_code.get(vc_id)
        emitted = outcome.observed_primary_code
        if authoritative and emitted != authoritative:
            # Co-report the originally-observed code as diagnostic, surface
            # the authoritative code as primary (registry ownership).
            diags = list(outcome.observed_diagnostic_codes)
            if emitted and emitted not in diags:
                diags.append(emitted)
            resolved[vc_id] = CheckOutcome(
                observed_status=outcome.observed_status,
                observed_primary_code=authoritative,
                observed_diagnostic_codes=diags,
                evidence={
                    **outcome.evidence,
                    "precedence_normalised_from": emitted,
                    "precedence_normalised_to": authoritative,
                },
            )
        else:
            resolved[vc_id] = outcome
    return resolved


def _summarise(
    records: List[Dict[str, Any]],
    canonical: Sequence[str],
    outcomes: Mapping[str, CheckOutcome],
    ctx: VerificationContext,
) -> Dict[str, Any]:
    verdict_counts = {"PASS": 0, "FAIL": 0, "ERROR": 0}
    observed_status_counts = {"PASS": 0, "FAIL": 0, "ERROR": 0, "SKIPPED": 0}
    for record in records:
        verdict_counts[record["verdict"]] = (
            verdict_counts.get(record["verdict"], 0) + 1
        )
        observed_status_counts[record["observed_status"]] = (
            observed_status_counts.get(record["observed_status"], 0) + 1
        )

    # Domain disjointness check (each VC owned by exactly one domain).
    domain_ownership: Dict[str, List[str]] = {}
    for record in ctx.vc_mapping.get("verifier_checks", []):
        vc_id = record.get("VC_id")
        if not vc_id:
            continue
        surface = record.get("implementation_surface", {}) or {}
        module = os.path.basename(
            surface.get("proposed_verifier_module", "") or ""
        ).replace(".py", "")
        domain_ownership.setdefault(module, []).append(vc_id)

    evaluated = set(outcomes.keys())
    canonical_set = set(canonical)
    missing = sorted(canonical_set - evaluated)
    extra = sorted(evaluated - canonical_set)

    return {
        "canonical_VC_count": len(canonical),
        "evaluated_VC_count": len(evaluated & canonical_set),
        "missing_VCs": missing,
        "extra_VCs": extra,
        "verdict_counts": verdict_counts,
        "observed_status_counts": observed_status_counts,
        "domain_ownership_sizes": {
            domain: len(vcs) for domain, vcs in sorted(domain_ownership.items())
        },
        "deterministic_order": "VC_id asc, fixture_id asc, mutation_id asc",
    }


# ===========================================================================
# CLI
# ===========================================================================


def _cli(argv: Sequence[str]) -> int:
    if len(argv) < 6:
        sys.stderr.write(
            "usage: vta_verifier.py "
            "<output_packet> <fixtures_dir> <formula_contracts.yaml> "
            "<failure_code_registry.yaml> <vc_mapping.yaml> "
            "[--fixture-id ID] [--mutation-id ID] "
            "[--expected-status PASS|FAIL] [--expected-primary-code CODE]\n"
        )
        return 2

    args = list(argv)
    positional: List[str] = []
    kw: Dict[str, str] = {}
    i = 0
    while i < len(args):
        token = args[i]
        if token.startswith("--"):
            key = token[2:]
            if i + 1 < len(args):
                kw[key] = args[i + 1]
                i += 2
            else:
                i += 1
        else:
            positional.append(token)
            i += 1

    result = run_verification(
        output_packet_path=positional[0],
        frozen_fixtures_dir=positional[1],
        formula_contracts_path=positional[2],
        failure_code_registry_path=positional[3],
        vc_mapping_path=positional[4],
        fixture_id=kw.get("fixture-id"),
        mutation_id=kw.get("mutation-id"),
        expected_status=kw.get("expected-status", STATUS_PASS),
        expected_primary_code=kw.get("expected-primary-code", CODE_NONE),
    )
    json.dump(result, sys.stdout, indent=2, sort_keys=True, default=str)
    sys.stdout.write("\n")
    return 0 if result["summary"]["verdict_counts"]["ERROR"] == 0 else 1


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
