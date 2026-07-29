"""Verification domain: LANGUAGE_POLICY.

Owns 5 canonical VCs (per vta-VC-to-verifier-mapping.yaml
verifier_module_coverage = LANGUAGE_POLICY (5)):

    VC-REQ007-LEXICAL, VC-REQ007-SEMANTIC, VC-REQ007-IMPERATIVE,
    VC-REQ007-NEGATION, VC-ADV-LANG-1.

REQ-007 mandates a 3-layer non-advice language policy:
  Layer 1 (lexical): regex scan for prohibited tokens.
  Layer 2 (semantic): advice-via-rephrasing detection.
  Layer 3 (imperative): imperative-mood (nên/phải/cần/hãy) detection.
A 4th cross-cutting VC (VC-REQ007-NEGATION) gates the layers with
negation context: 'NOT bullish' must NOT be flagged as a violation.

Independence: the prohibited token sets and negation rules are frozen inline
from the contract (contracts/REQ007-semantic-policy.yaml oracle). No
production language_verifier is imported.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .common import CheckOutcome, CODE_NONE, STATUS_FAIL, STATUS_PASS

DOMAIN_NAME = "language_policy"

OWNED_VC_IDS = (
    "VC-REQ007-LEXICAL",
    "VC-REQ007-SEMANTIC",
    "VC-REQ007-IMPERATIVE",
    "VC-REQ007-NEGATION",
    "VC-ADV-LANG-1",
)

# Frozen prohibited lexical tokens (lowercased). From
# VC-REQ007-LEXICAL canonical_obligation.
_LEXICAL_PROHIBITED = (
    # English advice / directional
    "bullish",
    "bearish",
    "overbought",
    "oversold",
    "strong buy",
    "strong sell",
    "buy",
    "sell",
    "hold",
    # Vietnamese advice
    "tín hiệu",
    "khuyến nghị",
    "nên mua",
    "nên bán",
    "mua",
    "bán",
    "giữ",
)

# Imperative-mood tokens (Layer 3). From VC-REQ007-IMPERATIVE
# canonical_obligation.
_IMPERATIVE_TOKENS = ("nên", "phải", "cần", "hãy")

# Semantic advice implications (Layer 2). Curated patterns capturing advice
# via rephrasing that lexical Layer 1 might miss. Each entry is (regex, label).
_SEMANTIC_PATTERNS: Tuple[Tuple[re.Pattern, str], ...] = (
    (re.compile(r"\b(should|shall|must|ought to)\b", re.IGNORECASE), "ENGLISH_MODAL_ADVICE"),
    (re.compile(r"\b(recommend[a-z]*)\b", re.IGNORECASE), "ENGLISH_RECOMMEND"),
    (re.compile(r"\b(suggest[a-z]*)\b", re.IGNORECASE), "ENGLISH_SUGGEST"),
    (re.compile(r"\b(advice|advise)\b", re.IGNORECASE), "ENGLISH_ADVICE"),
    (re.compile(r"(được\s+khuyến\s*nghị|khuyên)\b", re.IGNORECASE), "VI_RECOMMEND_REPHRASE"),
    (re.compile(r"(có\s+thể\s+(tăng|giảm|đi\s+lên|đi\s+xuống))\b", re.IGNORECASE), "VI_DIRECTIONAL_FORECAST"),
    (re.compile(r"(dự\s+kiến\s+(tăng|giảm))\b", re.IGNORECASE), "VI_FORECAST"),
    (re.compile(r"(triển\s+vọng\s+(tích\s*cực|tiêu\s*cực))\b", re.IGNORECASE), "VI_OUTLOOK"),
)

# Vietnamese negation tokens that gate lexical/semantic matches. When a
# prohibited token is preceded (within a small window) by a negation, the
# match is an affirmative non-advice statement (e.g. 'NOT bullish') and MUST
# NOT be flagged.
_VI_NEGATION_TOKENS = ("không", "chưa", "không phải", "không phải là")
_EN_NEGATION_TOKENS = ("not", "no", "never", "without", "non-")


def evaluate(ctx) -> Dict[str, CheckOutcome]:
    packet = ctx.output_packet
    outcomes: Dict[str, CheckOutcome] = {}
    text_spans = _collect_text(packet)
    for vc_id in OWNED_VC_IDS:
        handler = _HANDLERS.get(vc_id)
        if handler is None:
            outcomes[vc_id] = CheckOutcome.error(
                f"No handler bound for {vc_id}", vc_id=vc_id
            )
            continue
        try:
            outcomes[vc_id] = handler(ctx, packet, text_spans)
        except Exception as exc:  # pragma: no cover - defensive
            outcomes[vc_id] = CheckOutcome.error(
                f"Handler raised: {type(exc).__name__}: {exc}", vc_id=vc_id
            )
    return outcomes


# ===========================================================================
# Text extraction
# ===========================================================================


def _collect_text(packet: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Collect (path, text) spans from string-valued fields, skipping
    metadata/structural envelopes and identifiers.

    The canonical packet carries many non-narrative string fields (archetype,
    setup_coverage_status, provider ids, chain labels, fixture/config params)
    that may legitimately contain tokens like 'bearish' or imperative-shaped
    substrings without constituting advice language. Only narrative text
    fields (analysis_text, narrative, commentary, summary, text, message,
    description, note, reason, rationale) are scanned for the language policy;
    metadata envelopes are excluded entirely."""
    spans: List[Tuple[str, str]] = []
    skip = {
        "provenance", "warnings", "errors", "computation_chain",
        "validation", "boundary_check", "language_check",
        "diagnostic_failure_codes", "binary_signals_6",
        "indicators", "profile_blocks", "bullish_setups", "bearish_setups",
        "setup_coverage", "params",
    }
    _walk_text(packet, "", spans, skip)
    return spans


def _walk_text(
    node: Any,
    prefix: str,
    acc: List[Tuple[str, str]],
    skip: set,
) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in skip and prefix == "":
                continue
            _walk_text(value, f"{prefix}.{key}" if prefix else key, acc, skip)
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            _walk_text(value, f"{prefix}[{idx}]", acc, skip)
    elif isinstance(node, str):
        # Skip short structural identifiers (mode, ticker, schema names).
        if len(node) >= 4 and " " in node or _looks_like_phrase(node):
            acc.append((prefix, node))


# Structural identifier / enum shape: ALL-CAPS with optional underscores,
# hyphens, digits (e.g. VALID_WITH_WARNINGS, A-NO-CURRENT-SETUP,
# INCOMPLETE_BEARISH_COVERAGE, vn-technical-v1). These are not natural language
# and are excluded from the narrative-text scan.
_IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_\-]*$")


def _looks_like_phrase(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    # Pure structural identifiers / enum values are not narrative text.
    if _IDENTIFIER_RE.match(stripped) and stripped.upper() == stripped:
        return False
    # Short single-word tokens without spaces are not phrases.
    if " " not in stripped and len(stripped) < 4:
        return False
    return any(c.isalpha() for c in stripped)


# ===========================================================================
# Layered scanning
# ===========================================================================


def _scan_lexical(spans: Sequence[Tuple[str, str]]) -> List[Dict[str, Any]]:
    """Layer 1: prohibited token scan, negation-aware. Returns a list of
    violation dicts (path, token, span, negation_context)."""
    violations: List[Dict[str, Any]] = []
    for path, text in spans:
        lower = text.lower()
        for token in _LEXICAL_PROHIBITED:
            for match in re.finditer(re.escape(token), lower):
                start = match.start()
                window = lower[max(0, start - 24) : start]
                if _is_negated(window):
                    continue
                violations.append(
                    {
                        "layer": "LEXICAL",
                        "path": path,
                        "token": token,
                        "text_span": text[max(0, start - 8) : match.end() + 8],
                        "negation_context": False,
                    }
                )
    return violations


def _scan_semantic(spans: Sequence[Tuple[str, str]]) -> List[Dict[str, Any]]:
    """Layer 2: semantic advice implication scan, negation-aware."""
    violations: List[Dict[str, Any]] = []
    for path, text in spans:
        for pattern, label in _SEMANTIC_PATTERNS:
            for match in pattern.finditer(text):
                start = match.start()
                window = text[max(0, start - 24) : start].lower()
                if _is_negated(window):
                    continue
                violations.append(
                    {
                        "layer": "SEMANTIC",
                        "label": label,
                        "path": path,
                        "token": match.group(0),
                        "text_span": text[max(0, start - 8) : match.end() + 8],
                        "negation_context": False,
                    }
                )
    return violations


def _scan_imperative(spans: Sequence[Tuple[str, str]]) -> List[Dict[str, Any]]:
    """Layer 3: imperative-mood scan (nên/phải/cần/hãy), negation-aware."""
    violations: List[Dict[str, Any]] = []
    boundary = re.compile(r"\b")
    for path, text in spans:
        lower = text.lower()
        for token in _IMPERATIVE_TOKENS:
            for match in re.finditer(rf"\b{re.escape(token)}\b", lower):
                start = match.start()
                window = lower[max(0, start - 24) : start]
                if _is_negated(window):
                    continue
                violations.append(
                    {
                        "layer": "IMPERATIVE",
                        "path": path,
                        "token": token,
                        "text_span": text[max(0, start - 8) : match.end() + 8],
                        "negation_context": False,
                    }
                )
    return violations


def _is_negated(window_lower: str) -> bool:
    """Return True if the window immediately preceding a match contains a
    negation token (Vietnamese or English)."""
    for token in _VI_NEGATION_TOKENS:
        if token in window_lower:
            return True
    # English negations: word-boundary match.
    for token in _EN_NEGATION_TOKENS:
        if re.search(rf"\b{re.escape(token)}\b", window_lower):
            return True
    # 'non-' prefix directly attached: handled by the hyphen in the set above.
    return False


# ===========================================================================
# Per-VC handlers
# ===========================================================================


def _vc_req007_lexical(ctx, packet, spans) -> CheckOutcome:
    """VC-REQ007-LEXICAL: 0 prohibited tokens in output text (Layer 1)."""
    violations = _scan_lexical(spans)
    if violations:
        return CheckOutcome.fail(
            "ADVICE_LANGUAGE_DETECTED",
            ["PROHIBITED_TOKEN_FOUND"],
            reason="prohibited lexical token(s) found in output text",
            violations=violations[:20],
            violation_count=len(violations),
        )
    return CheckOutcome.pass_clean(layer="LEXICAL", violation_count=0)


def _vc_req007_semantic(ctx, packet, spans) -> CheckOutcome:
    """VC-REQ007-SEMANTIC: 0 advice implications via rephrased language
    (Layer 2)."""
    violations = _scan_semantic(spans)
    if violations:
        return CheckOutcome.fail(
            "ADVICE_LANGUAGE_DETECTED",
            ["SEMANTIC_ADVICE_DETECTED"],
            reason="semantic advice implication(s) found in output text",
            violations=violations[:20],
            violation_count=len(violations),
        )
    return CheckOutcome.pass_clean(layer="SEMANTIC", violation_count=0)


def _vc_req007_imperative(ctx, packet, spans) -> CheckOutcome:
    """VC-REQ007-IMPERATIVE: 0 imperative-mood constructions (Layer 3)."""
    violations = _scan_imperative(spans)
    if violations:
        return CheckOutcome.fail(
            "ADVICE_LANGUAGE_DETECTED",
            ["IMPERATIVE_MOOD_DETECTED"],
            reason="imperative-mood construction(s) found in output text",
            violations=violations[:20],
            violation_count=len(violations),
        )
    return CheckOutcome.pass_clean(layer="IMPERATIVE", violation_count=0)


def _vc_req007_negation(ctx, packet, spans) -> CheckOutcome:
    """VC-REQ007-NEGATION: 'NOT bullish' accepted (not flagged as violation).
    The verifier scans all spans for affirmative prohibited tokens that ARE
    negated and asserts the lexical/semantic layers did NOT flag them. A
    violation here means the negation gate failed (blind match)."""
    # Find negated occurrences of prohibited tokens.
    negated_occurrences: List[Dict[str, Any]] = []
    for path, text in spans:
        lower = text.lower()
        for token in _LEXICAL_PROHIBITED:
            for match in re.finditer(re.escape(token), lower):
                start = match.start()
                window = lower[max(0, start - 24) : start]
                if _is_negated(window):
                    negated_occurrences.append(
                        {
                            "path": path,
                            "token": token,
                            "text_span": text[max(0, start - 12) : match.end() + 12],
                        }
                    )
    if not negated_occurrences:
        # No negated prohibited tokens in this output -> the negation gate is
        # trivially satisfied for this case.
        return CheckOutcome.pass_clean(negated_occurrences=0)
    # If the lexical layer flagged any of these negated occurrences, the
    # negation gate failed (blind match). We detect this by comparing against
    # a non-negation-aware scan.
    blind = _scan_lexical_blind(spans)
    blind_paths_tokens = {(v["path"], v["token"]) for v in blind}
    negated_flagged = [
        occ
        for occ in negated_occurrences
        if (occ["path"], occ["token"]) in blind_paths_tokens
    ]
    if negated_flagged:
        return CheckOutcome.fail(
            "ADVICE_LANGUAGE_DETECTED",
            ["NEGATION_BLIND_MATCH"],
            reason=(
                "negation context was not evaluated before lexical token match "
                "(affirmative non-advice statement flagged as violation)"
            ),
            negated_occurrences=negated_occurrences[:10],
            blind_flagged=negated_flagged[:10],
        )
    return CheckOutcome.pass_clean(
        negated_occurrences=len(negated_occurrences),
        negation_gate_correct=True,
    )


def _scan_lexical_blind(spans: Sequence[Tuple[str, str]]) -> List[Dict[str, Any]]:
    """Non-negation-aware lexical scan (for VC-REQ007-NEGATION comparison)."""
    violations: List[Dict[str, Any]] = []
    for path, text in spans:
        lower = text.lower()
        for token in _LEXICAL_PROHIBITED:
            for match in re.finditer(re.escape(token), lower):
                violations.append({"path": path, "token": token})
    return violations


def _vc_adv_lang_1(ctx, packet, spans) -> CheckOutcome:
    """VC-ADV-LANG-1: injected 'n nên mua' -> ADVICE_LANGUAGE_DETECTED.
    Negative-fixture companion that combines lexical + imperative layers."""
    # 'nên mua' specifically: imperative 'nên' + lexical 'mua'.
    needle = re.compile(r"nên\s+mua", re.IGNORECASE)
    injected: List[Dict[str, Any]] = []
    for path, text in spans:
        for match in needle.finditer(text):
            injected.append(
                {
                    "path": path,
                    "token": match.group(0),
                    "text_span": text[
                        max(0, match.start() - 8) : match.end() + 8
                    ],
                }
            )
    # Also catch the broader injected-advice-phrase class (any lexical token
    # paired with an imperative within a small window).
    for path, text in spans:
        lower = text.lower()
        for imp in _IMPERATIVE_TOKENS:
            for imp_match in re.finditer(rf"\b{re.escape(imp)}\b", lower):
                window = lower[imp_match.start() : imp_match.end() + 12]
                for lex in _LEXICAL_PROHIBITED:
                    if lex in window and lex not in (imp,):
                        entry = {
                            "path": path,
                            "token": f"{imp} {lex}",
                            "text_span": text[
                                max(0, imp_match.start() - 4) : imp_match.end() + 16
                            ],
                        }
                        if entry not in injected:
                            injected.append(entry)
    if injected:
        return CheckOutcome.fail(
            "ADVICE_LANGUAGE_DETECTED",
            ["INJECTED_ADVICE_PHRASE_FOUND"],
            reason="injected advice phrase detected (imperative + lexical)",
            injected=injected[:20],
            injected_count=len(injected),
        )
    return CheckOutcome.pass_clean(injected_count=0)


_HANDLERS = {
    "VC-REQ007-LEXICAL": _vc_req007_lexical,
    "VC-REQ007-SEMANTIC": _vc_req007_semantic,
    "VC-REQ007-IMPERATIVE": _vc_req007_imperative,
    "VC-REQ007-NEGATION": _vc_req007_negation,
    "VC-ADV-LANG-1": _vc_adv_lang_1,
}
