"""Verification domain: SETUP_SEMANTICS.

Owns 12 canonical VCs (per vta-VC-to-verifier-mapping.yaml
verifier_module_coverage = ARCHETYPE (9) + COV (2) + PROFILE coverage (1)):

  ARCHETYPE (9):
    VC-ARCH-AMBIG-1, VC-FALSE-BREAKOUT-1, VC-UNCONFIRMED-1, VC-LOOKAHEAD-1,
    VC-CONFLICT-SETUP-1, VC-BEARISH-DESIGN-1, VC-BEARISH-DESIGN-2,
    VC-BEARISH-DESIGN-3, VC-BEARISH-DESIGN-4
  SETUP_COVERAGE (2):
    VC-COV-1, VC-COV-2
  PROFILE coverage-status explicitness (1):
    VC-PROFILE-VALID-4

Independence: the verifier reasons over the output packet's setup/block/
coverage fields and the frozen input fixture. No production profile_engine /
setup detector is imported. The static-analysis checks (lookahead, sign-flip)
inspect a textual detector description supplied via the fixture, not the
production source.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence

from .common import CheckOutcome, CODE_NONE, STATUS_FAIL, STATUS_PASS

DOMAIN_NAME = "setup_semantics"

OWNED_VC_IDS = (
    # ARCHETYPE
    "VC-ARCH-AMBIG-1",
    "VC-FALSE-BREAKOUT-1",
    "VC-UNCONFIRMED-1",
    "VC-LOOKAHEAD-1",
    "VC-CONFLICT-SETUP-1",
    "VC-BEARISH-DESIGN-1",
    "VC-BEARISH-DESIGN-2",
    "VC-BEARISH-DESIGN-3",
    "VC-BEARISH-DESIGN-4",
    # SETUP_COVERAGE
    "VC-COV-1",
    "VC-COV-2",
    # PROFILE coverage-status explicitness
    "VC-PROFILE-VALID-4",
)

# Frozen score-band thresholds (from VC-UNCONFIRMED-1 precedence_rules).
_SCORE_NOT_PRESENT = 55  # < 55 NOT_PRESENT
_SCORE_EMERGING_LO = 55
_SCORE_EMERGING_HI = 61  # 55-61 emerging
_SCORE_INDEVELOPMENT_LO = 62
_SCORE_INDEVELOPMENT_HI = 77  # 62-77 INDEVELOPMENT
_SCORE_CONFIRMED = 78  # >= 78 CONFIRMED

# Volume confirmation threshold (VC-FALSE-BREAKOUT-1).
_BREAKOUT_VOLUME_RATIO = 1.5

# Bearish registry denominator (VC-BEARISH-DESIGN-4): 8 bullish + 5 bearish = 13.
# Per the VC's unresolved_dependency the denominator is proposed at 13.
_BULLISH_SETUP_COUNT = 8
_BEARISH_SETUP_COUNT_FROZEN = 5
_FROZEN_DENOMINATOR = _BULLISH_SETUP_COUNT + _BEARISH_SETUP_COUNT_FROZEN

# Canonical archetype set — the six archetype ids the profile_engine emits
# (frozen per the bearish setup registry archetype_feed / precedence). The
# verifier hardcodes this frozen set rather than importing the production
# module, preserving its independence boundary (the values are frozen data,
# not decision logic). VC-ARCH-AMBIG-1's deterministic fallback target is
# A-NO-CURRENT-SETUP.
_CANONICAL_ARCHETYPES = (
    "A-TREND-FOLLOWING",
    "A-ACCUMULATION-BREAKOUT",
    "A-DISTRIBUTION",
    "A-TRAP-PRONE",
    "A-MIXED",
    "A-NO-CURRENT-SETUP",
)
_CANONICAL_ARCHETYPE_SET = frozenset(_CANONICAL_ARCHETYPES)

# Canonical conflict-resolution options for VC-BEARISH-DESIGN-3.
_CONFLICT_BEHAVIOR_OPTIONS = ("OPTION_A", "OPTION_B", "OPTION_C")

# Allowed setup_coverage_status enum (VC-PROFILE-VALID-4).
_COVERAGE_STATUS_ENUM = (
    "BULLISH_ONLY",
    "INCOMPLETE_BEARISH_COVERAGE",
    "COMPLETE_DIRECTIONAL_COVERAGE",
)


def evaluate(ctx) -> Dict[str, CheckOutcome]:
    packet = ctx.output_packet
    fixture = _load_fixture(ctx)
    outcomes: Dict[str, CheckOutcome] = {}
    for vc_id in OWNED_VC_IDS:
        handler = _HANDLERS.get(vc_id)
        if handler is None:
            outcomes[vc_id] = CheckOutcome.error(
                f"No handler bound for {vc_id}", vc_id=vc_id
            )
            continue
        try:
            outcomes[vc_id] = handler(ctx, packet, fixture)
        except Exception as exc:  # pragma: no cover - defensive
            outcomes[vc_id] = CheckOutcome.error(
                f"Handler raised: {type(exc).__name__}: {exc}", vc_id=vc_id
            )
    return outcomes


# ===========================================================================
# Helpers
# ===========================================================================


def _load_fixture(ctx) -> Dict[str, Any]:
    if not ctx.fixture_id:
        return {}
    fixture = ctx.load_fixture(ctx.fixture_id)
    return fixture if isinstance(fixture, dict) else {"_root": fixture}


def _setups(packet: Dict[str, Any]) -> List[Dict[str, Any]]:
    setups = packet.get("setups") or packet.get("profile_blocks", {}).get("setups") if isinstance(packet.get("profile_blocks"), dict) else packet.get("setups")
    if isinstance(setups, list):
        return [s for s in setups if isinstance(s, dict)]
    return []


def _archetype(packet: Dict[str, Any]) -> Optional[str]:
    arch = packet.get("archetype")
    if isinstance(arch, dict):
        return arch.get("id") or arch.get("name")
    if isinstance(arch, str):
        return arch
    return None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _score_band(score: float) -> str:
    if score < _SCORE_NOT_PRESENT:
        return "NOT_PRESENT"
    if score <= _SCORE_EMERGING_HI:
        return "EMERGING"
    if score <= _SCORE_INDEVELOPMENT_HI:
        return "INDEVELOPMENT"
    return "CONFIRMED"


# ===========================================================================
# Per-VC handlers
# ===========================================================================


def _vc_arch_ambig_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-ARCH-AMBIG-1: ambiguous archetype assignment -> A-NO-CURRENT-SETUP
    fallback (deterministic)."""
    ambiguous_input = (
        fixture.get("ambiguous_input") is True
        or fixture.get("ambiguous_archetype") is True
        or _has_multiple_eligible_archetypes(packet)
    )
    archetype = _archetype(packet)
    if ambiguous_input:
        if archetype == "A-NO-CURRENT-SETUP":
            return CheckOutcome.fail(
                "ARCHETYPE_AMBIGUITY_FALLBACK",
                ["NONDETERMINISTIC_ARCHETYPE"],
                reason="ambiguous input correctly fell back to A-NO-CURRENT-SETUP",
            )
        # If multiple archetypes are reported as eligible without resolution,
        # the engine did not fall back deterministically.
        eligible = _eligible_archetypes(packet)
        if len(eligible) >= 2 and archetype not in _CANONICAL_ARCHETYPES:
            return CheckOutcome.fail(
                "ARCHETYPE_AMBIGUITY_FALLBACK",
                ["NONDETERMINISTIC_ARCHETYPE"],
                reason=(
                    "ambiguous input did not produce the deterministic "
                    "A-NO-CURRENT-SETUP fallback"
                ),
                eligible=eligible,
                observed_archetype=archetype,
            )
        return CheckOutcome.fail(
            "ARCHETYPE_AMBIGUITY_FALLBACK",
            ["NONDETERMINISTIC_ARCHETYPE"],
            reason="ambiguous input did not produce the deterministic fallback",
            observed_archetype=archetype,
        )
    # Non-ambiguous input: archetype must be in the canonical set and
    # deterministic.
    if archetype is not None and archetype not in _CANONICAL_ARCHETYPES:
        return CheckOutcome.fail(
            "ARCHETYPE_AMBIGUITY_FALLBACK",
            ["NONDETERMINISTIC_ARCHETYPE"],
            reason="reported archetype is not in the canonical set",
            observed_archetype=archetype,
            canonical=list(_CANONICAL_ARCHETYPES),
        )
    return CheckOutcome.pass_clean(
        ambiguous_input=False, observed_archetype=archetype
    )


def _has_multiple_eligible_archetypes(packet: Dict[str, Any]) -> bool:
    return len(_eligible_archetypes(packet)) >= 2


def _eligible_archetypes(packet: Dict[str, Any]) -> List[str]:
    arch = packet.get("archetype")
    if isinstance(arch, dict):
        eligible = arch.get("eligible") or arch.get("eligible_archetypes")
        if isinstance(eligible, list):
            return [str(a) for a in eligible]
    if isinstance(arch, list):
        return [str(a) for a in arch]
    return []


def _vc_false_breakout_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-FALSE-BREAKOUT-1: breakout without volume >= 1.5x avg20 -> not
    flagged (score < 55)."""
    setups = _setups(packet)
    if not setups:
        return CheckOutcome.pass_clean(setups_present=False)
    violations: List[Dict[str, Any]] = []
    for setup in setups:
        setup_type = str(setup.get("type") or setup.get("id") or "").lower()
        if "breakout" not in setup_type:
            continue
        breakout_volume = setup.get("breakout_volume") or setup.get("volume")
        avg20 = setup.get("avg20_volume") or setup.get("avg_volume_20")
        score = setup.get("score")
        if not _is_number(breakout_volume) or not _is_number(avg20) or avg20 == 0:
            continue
        ratio = float(breakout_volume) / float(avg20)
        below_threshold = ratio < _BREAKOUT_VOLUME_RATIO
        flagged = (
            (setup.get("status") not in (None, "NOT_PRESENT"))
            or (_is_number(score) and float(score) >= _SCORE_NOT_PRESENT)
        )
        if below_threshold and flagged:
            violations.append(
                {
                    "setup_id": setup.get("id"),
                    "ratio": ratio,
                    "score": score,
                    "status": setup.get("status"),
                }
            )
    if violations:
        return CheckOutcome.fail(
            "FALSE_BREAKOUT_WITHOUT_VOLUME",
            ["BREAKOUT_WITHOUT_VOLUME"],
            reason="breakout flagged without volume >= 1.5x avg20",
            violations=violations[:20],
            threshold=_BREAKOUT_VOLUME_RATIO,
        )
    return CheckOutcome.pass_clean(
        breakout_setups=len([s for s in setups if "breakout" in str(s.get("type", "")).lower()]),
        threshold=_BREAKOUT_VOLUME_RATIO,
    )


def _vc_unconfirmed_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-UNCONFIRMED-1: setup score 62-77 -> status=INDEVELOPMENT (not
    CONFIRMED)."""
    setups = _setups(packet)
    if not setups:
        return CheckOutcome.pass_clean(setups_present=False)
    violations: List[Dict[str, Any]] = []
    for setup in setups:
        score = setup.get("score")
        status = setup.get("status")
        if not _is_number(score):
            continue
        score_f = float(score)
        expected_band = _score_band(score_f)
        if _SCORE_INDEVELOPMENT_LO <= score_f <= _SCORE_INDEVELOPMENT_HI:
            if status != "INDEVELOPMENT":
                violations.append(
                    {
                        "setup_id": setup.get("id"),
                        "score": score_f,
                        "emitted_status": status,
                        "expected_status": "INDEVELOPMENT",
                    }
                )
        # Also flag boundary cases: score < 55 should be NOT_PRESENT, >= 78
        # CONFIRMED.
        elif score_f < _SCORE_NOT_PRESENT and status not in (None, "NOT_PRESENT"):
            violations.append(
                {
                    "setup_id": setup.get("id"),
                    "score": score_f,
                    "emitted_status": status,
                    "expected_status": "NOT_PRESENT",
                }
            )
        elif score_f >= _SCORE_CONFIRMED and status != "CONFIRMED":
            violations.append(
                {
                    "setup_id": setup.get("id"),
                    "score": score_f,
                    "emitted_status": status,
                    "expected_status": "CONFIRMED",
                }
            )
    if violations:
        return CheckOutcome.fail(
            "UNCONFIRMED_PATTERN_REPORTED_AS_CONFIRMED",
            ["UNCONFIRMED_MARKED_CONFIRMED"],
            reason="setup status disagrees with frozen score band",
            violations=violations[:20],
            bands={
                "NOT_PRESENT": f"< {_SCORE_NOT_PRESENT}",
                "EMERGING": f"{_SCORE_EMERGING_LO}-{_SCORE_EMERGING_HI}",
                "INDEVELOPMENT": f"{_SCORE_INDEVELOPMENT_LO}-{_SCORE_INDEVELOPMENT_HI}",
                "CONFIRMED": f">= {_SCORE_CONFIRMED}",
            },
        )
    return CheckOutcome.pass_clean(setups_evaluated=len(setups))


def _vc_lookahead_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-LOOKAHEAD-1: pattern at index i must not reference close[i+k] for
    k>0. The verifier performs static analysis on a detector description
    supplied via the fixture (detector_source / detector_pseudocode), since
    the verifier cannot import production pattern code. A reference to a
    future index (i+k, +k, close[i+...]) inside the detector body is the
    violation."""
    detector = (
        fixture.get("detector_source")
        or fixture.get("detector_pseudocode")
        or fixture.get("detector")
        or ""
    )
    if not isinstance(detector, str) or not detector.strip():
        # No detector text to analyse; assert the packet declares lookahead
        # safety explicitly.
        declared_safe = packet.get("lookahead_safe") is True or packet.get(
            "causal"
        ) is True
        if declared_safe:
            return CheckOutcome.pass_clean(detector_text=False, declared_safe=True)
        return CheckOutcome.error(
            "no detector source in fixture and packet does not declare lookahead safety"
        )
    future_refs = _find_future_references(detector)
    if future_refs:
        return CheckOutcome.fail(
            "LOOKAHEAD_BIAS_DETECTED",
            ["FUTURE_REFERENCE_DETECTED"],
            reason="detector body references future index close[i+k] for k>0",
            future_refs=future_refs[:20],
            detector_excerpt=detector[:200],
        )
    return CheckOutcome.pass_clean(
        detector_text=True, future_reference_count=0
    )


_FUTURE_INDEX_PATTERNS = (
    re.compile(r"\[[\s]*i\s*\+\s*[1-9][0-9]*[\s]*\]"),
    re.compile(r"\[[\s]*i\s*\+\s*k[\s]*\]"),
    re.compile(r"close\[i\s*\+"),
    re.compile(r"\bt\s*\+\s*[1-9][0-9]*\b"),
    re.compile(r"\+k\b(?!\s*[*=])"),
    re.compile(r"future", re.IGNORECASE),
    re.compile(r"lookahead", re.IGNORECASE),
)


def _find_future_references(detector_text: str) -> List[str]:
    out: List[str] = []
    for pattern in _FUTURE_INDEX_PATTERNS:
        for match in pattern.finditer(detector_text):
            out.append(match.group(0))
    return out


def _vc_conflict_setup_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-CONFLICT-SETUP-1: conflicting setups -> all reported, archetype
    assigned by precedence. No silent top-N truncation."""
    setups = _setups(packet)
    qualifying = [
        s for s in setups if _is_number(s.get("score")) and float(s.get("score")) >= _SCORE_NOT_PRESENT
    ]
    if not qualifying:
        return CheckOutcome.pass_clean(qualifying_setups=0)
    qualifying_count = len(qualifying)
    returned_count = len(setups)
    archetype = _archetype(packet)
    truncation_disclosed = packet.get("truncation_disclosed") is True or packet.get(
        "top_n_disclosed"
    ) is True
    if qualifying_count > returned_count and not truncation_disclosed:
        dropped_ids = [
            s.get("id")
            for s in qualifying[returned_count:]
        ]
        return CheckOutcome.fail(
            "SETUP_DROPPED_SILENTLY",
            ["SETUP_SILENTLY_DROPPED"],
            reason=(
                "qualifying setups silently truncated without disclosure "
                "(no top-N disclosure)"
            ),
            qualifying_count=qualifying_count,
            returned_count=returned_count,
            dropped_setup_ids=dropped_ids[:20],
        )
    # Sets must be sorted by score descending.
    scores = [float(s.get("score")) for s in setups if _is_number(s.get("score"))]
    sorted_desc = all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))
    if not sorted_desc and len(scores) > 1:
        return CheckOutcome.fail(
            "SETUP_DROPPED_SILENTLY",
            ["SETUP_SILENTLY_DROPPED"],
            reason="returned setups not sorted by score descending",
            observed_order=scores,
        )
    if archetype is not None and archetype not in _CANONICAL_ARCHETYPES:
        return CheckOutcome.fail(
            "SETUP_DROPPED_SILENTLY",
            ["SETUP_SILENTLY_DROPPED"],
            reason="archetype not resolved to canonical set for conflicting setups",
            observed_archetype=archetype,
            canonical=list(_CANONICAL_ARCHETYPES),
        )
    return CheckOutcome.pass_clean(
        qualifying_count=qualifying_count,
        returned_count=returned_count,
        archetype=archetype,
        sorted_desc=sorted_desc,
    )


# --- Bearish design gates -------------------------------------------------


def _vc_bearish_design_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-BEARISH-DESIGN-1: bearish setups have independent rules (NO sign
    inversion of bullish). Static analysis on the bearish detector source
    supplied via the fixture: detection_evidence or detector_source."""
    evidence = (
        fixture.get("detection_evidence")
        or fixture.get("bearish_detector_source")
        or fixture.get("detector_source")
        or ""
    )
    if not isinstance(evidence, str) or not evidence.strip():
        # Fall back to inspecting the output's bearish setups for a sign-flip
        # marker.
        for setup in _setups(packet):
            if str(setup.get("type", "")).lower().startswith("bearish"):
                if setup.get("sign_inverted") is True or setup.get(
                    "derived_from_bullish"
                ) is True:
                    return CheckOutcome.fail(
                        "BEARISH_SIGN_INVERSION",
                        ["SIGN_INVERSION_OF_BULLISH"],
                        reason="bearish setup derived from bullish with sign flip",
                        setup_id=setup.get("id"),
                    )
        return CheckOutcome.pass_clean(
            evidence_text=False, bearish_setups_independent=True
        )
    sign_flip_indicators = _detect_sign_inversion(evidence)
    if sign_flip_indicators:
        return CheckOutcome.fail(
            "BEARISH_SIGN_INVERSION",
            ["SIGN_INVERSION_OF_BULLISH"],
            reason="bearish detector source indicates sign inversion of bullish",
            indicators=sign_flip_indicators,
            evidence_excerpt=evidence[:200],
        )
    return CheckOutcome.pass_clean(
        evidence_text=True, sign_inversion_indicators=[]
    )


_SIGN_INVERSION_PATTERNS = (
    re.compile(r"sign[_\s]*flip", re.IGNORECASE),
    re.compile(r"-1\s*\*\s*bullish", re.IGNORECASE),
    re.compile(r"bullish\s*\*\s*-1", re.IGNORECASE),
    re.compile(r"import\s+bullish", re.IGNORECASE),
    re.compile(r"from\s+bullish", re.IGNORECASE),
    re.compile(r"invert\b", re.IGNORECASE),
    re.compile(r"negate\b", re.IGNORECASE),
)


def _detect_sign_inversion(evidence: str) -> List[str]:
    out: List[str] = []
    for pattern in _SIGN_INVERSION_PATTERNS:
        for match in pattern.finditer(evidence):
            out.append(match.group(0))
    return out


def _vc_bearish_design_2(ctx, packet, fixture) -> CheckOutcome:
    """VC-BEARISH-DESIGN-2: each bearish setup has confirmation + invalidation
    + min_history."""
    setups = _setups(packet)
    bearish = [
        s for s in setups if str(s.get("type") or s.get("direction") or "").lower().startswith("bearish")
    ]
    if not bearish:
        return CheckOutcome.pass_clean(bearish_setups=0)
    diagnostics: List[str] = []
    incomplete: List[Dict[str, Any]] = []
    for setup in bearish:
        missing: List[str] = []
        confirmation = setup.get("confirmation") or setup.get("confirmations")
        invalidation = setup.get("invalidation") or setup.get("invalidations")
        min_history = setup.get("min_history") or setup.get("minimum_history")
        if not confirmation:
            missing.append("confirmation")
            diagnostics.append("BEARISH_NO_CONFIRMATION")
        if not invalidation:
            missing.append("invalidation")
            diagnostics.append("BEARISH_NO_INVALIDATION")
        if not min_history:
            missing.append("min_history")
            diagnostics.append("BEARISH_NO_MIN_HISTORY")
        if missing:
            incomplete.append({"setup_id": setup.get("id"), "missing": missing})
    if incomplete:
        return CheckOutcome.fail(
            "BEARISH_SETUP_INCOMPLETE",
            sorted(set(diagnostics)),
            reason="bearish setups missing required completeness elements",
            incomplete=incomplete[:20],
        )
    return CheckOutcome.pass_clean(bearish_setups=len(bearish))


def _vc_bearish_design_3(ctx, packet, fixture) -> CheckOutcome:
    """VC-BEARISH-DESIGN-3: bullish+bearish simultaneous match behavior defined
    (frozen OPTION_A/B/C)."""
    conflict_behavior = packet.get("conflict_behavior") or packet.get(
        "bull_bear_conflict_resolution"
    )
    if isinstance(conflict_behavior, dict):
        option = conflict_behavior.get("option") or conflict_behavior.get("strategy")
    else:
        option = conflict_behavior
    if option in _CONFLICT_BEHAVIOR_OPTIONS:
        return CheckOutcome.pass_clean(conflict_behavior=option)
    # If simultaneous match evidence is present in the fixture but no
    # resolution option is declared, the behavior is undefined.
    simultaneous = (
        fixture.get("simultaneous_match") is True
        or fixture.get("bull_bear_simultaneous") is True
    )
    if simultaneous and option not in _CONFLICT_BEHAVIOR_OPTIONS:
        return CheckOutcome.fail(
            "SETUP_DROPPED_SILENTLY",
            ["BULL_BEAR_CONFLICT_UNDEFINED"],
            reason="bull+bear simultaneous match behavior not frozen to an option",
            observed_behavior=option,
            expected_options=list(_CONFLICT_BEHAVIOR_OPTIONS),
        )
    # No simultaneous evidence and no declared option: VC is silent.
    return CheckOutcome.pass_clean(conflict_behavior=option, simultaneous=False)


def _vc_bearish_design_4(ctx, packet, fixture) -> CheckOutcome:
    """VC-BEARISH-DESIGN-4: setup denominator frozen after Phase 3 review
    (8 bullish + 5 bearish = 13)."""
    applied = packet.get("setup_coverage_denominator") or packet.get("denominator")
    if not _is_number(applied):
        # Look inside setup_coverage block.
        coverage = packet.get("setup_coverage") or {}
        if isinstance(coverage, dict):
            applied = coverage.get("denominator") or coverage.get("total_setups")
    if not _is_number(applied):
        return CheckOutcome.fail(
            "DENOMINATOR_NOT_FROZEN",
            ["DENOMINATOR_PENDING_PHASE_3_REVIEW"],
            reason="setup_coverage denominator absent; cannot verify freeze",
            frozen=_FROZEN_DENOMINATOR,
        )
    if int(applied) != _FROZEN_DENOMINATOR:
        return CheckOutcome.fail(
            "DENOMINATOR_NOT_FROZEN",
            ["DENOMINATOR_PENDING_PHASE_3_REVIEW"],
            reason="applied denominator drifts from frozen registry value",
            applied=int(applied),
            frozen=_FROZEN_DENOMINATOR,
            abs_diff=abs(int(applied) - _FROZEN_DENOMINATOR),
        )
    return CheckOutcome.pass_clean(applied=int(applied), frozen=_FROZEN_DENOMINATOR)


# --- Setup coverage -------------------------------------------------------


def _vc_cov_1(ctx, packet, fixture) -> CheckOutcome:
    """VC-COV-1: setup_coverage_status MUST be INCOMPLETE_BEARISH_COVERAGE
    before Phase 4 bearish implementation. The verifier checks the bearish
    registry size; if < 5 designed, the status must NOT claim
    COMPLETE_DIRECTIONAL_COVERAGE."""
    coverage = packet.get("setup_coverage") or {}
    if not isinstance(coverage, dict):
        coverage = {}
    status = (
        coverage.get("status")
        or packet.get("setup_coverage_status")
        or packet.get("coverage_status")
    )
    designed_bearish = coverage.get("bearish_designed") or coverage.get(
        "bearish_setups_designed"
    )
    if _is_number(designed_bearish) and int(designed_bearish) >= _BEARISH_SETUP_COUNT_FROZEN:
        # Bearish registry complete; COMPLETE_DIRECTIONAL_COVERAGE allowed.
        if status == "COMPLETE_DIRECTIONAL_COVERAGE":
            return CheckOutcome.pass_clean(
                status=status, bearish_designed=int(designed_bearish)
            )
    # Bearish registry incomplete (or count absent): status must reflect that.
    if status == "COMPLETE_DIRECTIONAL_COVERAGE":
        return CheckOutcome.fail(
            "SETUP_COVERAGE_MISREPRESENTED",
            ["COVERAGE_PREMATURE_COMPLETENESS"],
            reason=(
                "setup_coverage_status claims COMPLETE_DIRECTIONAL_COVERAGE "
                "before bearish registry complete"
            ),
            observed_status=status,
            bearish_designed=designed_bearish,
            required_for_complete=_BEARISH_SETUP_COUNT_FROZEN,
        )
    if status not in _COVERAGE_STATUS_ENUM:
        return CheckOutcome.fail(
            "SETUP_COVERAGE_MISREPRESENTED",
            ["COVERAGE_NOT_EVALUATED_PROHIBITED"],
            reason="setup_coverage_status not in allowed enum",
            observed_status=status,
            allowed=list(_COVERAGE_STATUS_ENUM),
        )
    return CheckOutcome.pass_clean(status=status, allowed=list(_COVERAGE_STATUS_ENUM))


def _vc_cov_2(ctx, packet, fixture) -> CheckOutcome:
    """VC-COV-2: absence of bullish setup MUST NOT be reported as bearish
    evidence."""
    setups = _setups(packet)
    bullish_present = any(
        str(s.get("type") or s.get("direction") or "").lower().startswith("bullish")
        for s in setups
    )
    bearish_setups = [
        s
        for s in setups
        if str(s.get("type") or s.get("direction") or "").lower().startswith("bearish")
    ]
    # If the fixture is explicitly bullish-only and the engine still emitted a
    # bearish setup, that's the false positive.
    bullish_only_input = fixture.get("bullish_only_input") is True
    if bullish_only_input and bearish_setups:
        co_emit = packet.get("setup_coverage_status") in _COVERAGE_STATUS_ENUM
        return CheckOutcome.fail(
            "BEARISH_FALSE_POSITIVE",
            ["BEARISH_INFERRED_FROM_ABSENCE"] if not co_emit else [],
            reason="bearish detector fired on bullish-only input",
            bearish_setups=[s.get("id") for s in bearish_setups],
            co_emitted_coverage_misrepresented=not co_emit,
        )
    # Check that no bearish_setup is derived from an absence-of-bullish field.
    for setup in bearish_setups:
        rationale = str(setup.get("rationale") or setup.get("evidence") or "").lower()
        if "absence of bullish" in rationale or "bullish absence" in rationale or (
            "absence" in rationale and "bullish" in rationale
        ):
            return CheckOutcome.fail(
                "SETUP_COVERAGE_MISREPRESENTED",
                ["BEARISH_INFERRED_FROM_ABSENCE"],
                reason="bearish evidence cited from absence of bullish setup",
                setup_id=setup.get("id"),
                rationale=rationale,
            )
    return CheckOutcome.pass_clean(
        bullish_present=bullish_present,
        bearish_setups=len(bearish_setups),
    )


def _vc_profile_valid_4(ctx, packet, fixture) -> CheckOutcome:
    """VC-PROFILE-VALID-4: setup_coverage_status explicit; NOT_EVALUATED
    prohibited."""
    status = (
        packet.get("setup_coverage_status")
        or (packet.get("setup_coverage") or {}).get("status")
    )
    if status is None or status == "NOT_EVALUATED":
        return CheckOutcome.fail(
            "SETUP_COVERAGE_MISREPRESENTED",
            ["COVERAGE_NOT_EVALUATED_PROHIBITED"],
            reason="setup_coverage_status absent or NOT_EVALUATED",
            observed_status=status,
            allowed=list(_COVERAGE_STATUS_ENUM),
        )
    if status not in _COVERAGE_STATUS_ENUM:
        return CheckOutcome.fail(
            "SETUP_COVERAGE_MISREPRESENTED",
            ["COVERAGE_NOT_EVALUATED_PROHIBITED"],
            reason="setup_coverage_status not in allowed enum",
            observed_status=status,
            allowed=list(_COVERAGE_STATUS_ENUM),
        )
    return CheckOutcome.pass_clean(
        status=status, allowed=list(_COVERAGE_STATUS_ENUM)
    )


_HANDLERS = {
    "VC-ARCH-AMBIG-1": _vc_arch_ambig_1,
    "VC-FALSE-BREAKOUT-1": _vc_false_breakout_1,
    "VC-UNCONFIRMED-1": _vc_unconfirmed_1,
    "VC-LOOKAHEAD-1": _vc_lookahead_1,
    "VC-CONFLICT-SETUP-1": _vc_conflict_setup_1,
    "VC-BEARISH-DESIGN-1": _vc_bearish_design_1,
    "VC-BEARISH-DESIGN-2": _vc_bearish_design_2,
    "VC-BEARISH-DESIGN-3": _vc_bearish_design_3,
    "VC-BEARISH-DESIGN-4": _vc_bearish_design_4,
    "VC-COV-1": _vc_cov_1,
    "VC-COV-2": _vc_cov_2,
    "VC-PROFILE-VALID-4": _vc_profile_valid_4,
}
