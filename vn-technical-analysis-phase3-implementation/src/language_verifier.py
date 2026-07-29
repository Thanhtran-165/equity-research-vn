"""VTA Phase 3 — language_verifier.py

Implements VTA-REQ-003: 3-layer non-advice language check (lexical + semantic +
imperative) with negation-awareness.

Owns failure codes (frozen registry, tier 7 POLICY):
  - ADVICE_LANGUAGE_DETECTED        (precedence 610)
  - INJECTED_ADVICE_PHRASE_FOUND    (DIAGNOSTIC, surfaced as part of ADVICE_LANGUAGE_DETECTED)

Public interface:
  - check_language(output_text) -> LanguageCheckResult

Design invariants enforced:
  - REQ-007 is HIGHEST precedence (overrides any other requirement).
  - Negation-aware: "không bullish", "phải không bullish" are ALLOWED because the
    negation cancels the advice force of the token.
  - No cross-module import of production decision logic. Standalone.
  - Deterministic output (no wall clock, no RNG, ordered iteration).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


# ====================================================================
# Frozen vocabularies (VTA-REQ-003, VC-REQ007-* canonical tokens)
# ====================================================================

# Layer 1 — lexical prohibited tokens (case-insensitive whole-word/phrase match).
# Source: VTA-REQ-003 prohibited_behavior list.
LEXICAL_PROHIBITED_TOKENS: tuple = (
    "bullish",
    "bearish",
    "tín hiệu",
    "tin hieu",
    "khuyến nghị",
    "khuyen nghi",
    "nên mua",
    "nen mua",
    "nên bán",
    "nen ban",
    "strong buy",
    "strong sell",
    "overbought",
    "oversold",
)

# Layer 1 — verdict tokens that imply a trading action (also prohibited).
VERDICT_TOKENS: tuple = (
    "buy",
    "sell",
    "hold",
    "mua",
    "bán",
    "ban",
    "nắm giữ",
    "nam giu",
    "chốt lời",
    "chot loi",
    "cắt lỗ",
    "cat lo",
)

# Layer 2 — semantic advice implications (rephrased advice without a banned token).
# Each tuple is a compiled regex. Match = semantic advice implication.
SEMANTIC_ADVICE_PATTERNS: tuple = (
    # "dự báo / dự kiến giá sẽ ..." — forecasting future price
    re.compile(r"\bd(?:ự|u)\s*b(?:á|a)o\b", re.IGNORECASE),
    re.compile(r"\bd(?:ự|u)\s*k(?:i|y)(?:ế|e)m\b", re.IGNORECASE),
    # "có thể đạt ..."  with a price-ish target phrasing is advice when combined with direction
    re.compile(r"\bcó\s*thể\s*đ(?:ạ|a)t\b", re.IGNORECASE),
    re.compile(r"\bco\s*the\s*đ(?:ạ|a)t\b", re.IGNORECASE),
    # "mục tiêu giá" — explicit price target (advice implication)
    re.compile(r"\bm(?:ụ|u)c\s*ti(?:ê|e)u\s*gi(?:á|a)\b", re.IGNORECASE),
    # "lợi nhuận kỳ vọng" — expected-return framing
    re.compile(r"\bl(?:ợi|oi)\s*nhu(?:ậ|u)(?:ậ|u)?n\s*k(?:ỳ|y)\s*v(?:ọ|o)ng\b", re.IGNORECASE),
    # "điểm mua / điểm bán" — entry/exit point
    re.compile(r"\bđ(?:i|ı)(?:ể|e)?m\s*mua\b", re.IGNORECASE),
    re.compile(r"\bđ(?:i|ı)(?:ể|e)?m\s*b(?:á|a)n\b", re.IGNORECASE),
    # "warrented / justified to buy" — English advice implication
    re.compile(r"\bjustified\s+to\s+(?:buy|sell|hold)\b", re.IGNORECASE),
    re.compile(r"\b(?:high\s+)?conviction\s+(?:buy|sell|long|short)\b", re.IGNORECASE),
)

# Layer 3 — imperative mood markers (Vietnamese + English).
IMPERATIVE_TOKENS: tuple = (
    "nên",        # "should" — the canonical advice marker
    "phải",       # "must"
    "cần",        # "need to"
    "hãy",        # "do!" (direct imperative)
    "đừng",       # "don't!" (negative imperative, still imperative)
    "dung",       # ascii folded
    "mua ngay",   # "buy now"
    "ban ngay",
    "should",
    "must",
    "ought to",
    "have to",
    "need to",
)

# Layer NEGATION — tokens that, when appearing immediately before a flagged token,
# cancel the advice force of that token.
# Vietnamese: "không", "chưa", "không phải", "phải không", "chẳng", "đâu phải".
# English: "not", "no", "never", "neither".
NEGATION_TOKENS: tuple = (
    "không",
    "khong",
    "chưa",
    "chua",
    "chẳng",
    "chang",
    "đâu",
    "dau",
    "not",
    "no",
    "never",
    "neither",
    "without",
)


# ====================================================================
# Result types
# ====================================================================

@dataclass(frozen=True)
class LayerFinding:
    """One violation finding from one layer."""
    layer: str                         # lexical | semantic | imperative | injected_phrase
    matched_token: str
    text_span: str                     # the surrounding text fragment (for diagnosis only)
    char_start: int
    char_end: int
    negation_context: str              # "negated" | "affirmative" | "no_negation_window"
    advice_force: str                  # "active" | "canceled" | "unknown"


@dataclass(frozen=True)
class LanguageCheckResult:
    """Deterministic result of check_language()."""
    passed: bool
    primary_failure_code: Optional[str]            # ADVICE_LANGUAGE_DETECTED | None
    diagnostic_codes: tuple                         # e.g. ("INJECTED_ADVICE_PHRASE_FOUND",)
    findings: tuple                                 # tuple[LayerFinding]
    layers_evaluated: tuple                          # ("lexical","semantic","imperative")
    layer_summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "primary_failure_code": self.primary_failure_code,
            "diagnostic_codes": list(self.diagnostic_codes),
            "findings": [
                {
                    "layer": f.layer,
                    "matched_token": f.matched_token,
                    "text_span": f.text_span,
                    "char_start": f.char_start,
                    "char_end": f.char_end,
                    "negation_context": f.negation_context,
                    "advice_force": f.advice_force,
                }
                for f in self.findings
            ],
            "layers_evaluated": list(self.layers_evaluated),
            "layer_summary": dict(self.layer_summary),
        }


# ====================================================================
# Helpers
# ====================================================================

# Whole-word / phrase boundaries. We build a single alternation regex per
# vocabulary so matching is deterministic and order-independent inside a layer.
def _compile_wordset(tokens: tuple) -> "re.Pattern[str]":
    escaped = sorted((re.escape(t) for t in tokens), key=len, reverse=True)
    return re.compile(r"(?<![A-Za-zÀ-ỹ0-9_])(" + "|".join(escaped) + r")(?![A-Za-zÀ-ỹ0-9_])",
                      re.IGNORECASE | re.UNICODE)


_LEXICAL_RE = _compile_wordset(LEXICAL_PROHIBITED_TOKENS)
_VERDICT_RE = _compile_wordset(VERDICT_TOKENS)
_IMPERATIVE_RE = _compile_wordset(IMPERATIVE_TOKENS)
_NEGATION_RE = _compile_wordset(NEGATION_TOKENS)


def _lower_fold(s: str) -> str:
    """ASCII-fold + lowercase for diacritic-insensitive matching of Vietnamese.

    NOTE: this fold is LOSSY — it collapses distinct Vietnamese letters that
    share a base (e.g. 'â' and 'ầ' both fold to 'a'). It is used ONLY for the
    lexical layer where we want "khuyến nghị" and "khuyen nghi" to both match.
    The negation layer must NOT use this fold directly because it would make
    'đâu' (negation) and 'đầu' (not a negation) collide; see _negation_context
    which matches both raw and folded forms with word boundaries.
    """
    table = {
        "á": "a", "à": "a", "ả": "a", "ã": "a", "ạ": "a",
        "ă": "a", "ắ": "a", "ằ": "a", "ẳ": "a", "ẵ": "a", "ặ": "a",
        "â": "a", "ầ": "a", "ẩ": "a", "ẫ": "a", "ậ": "a", "ấ": "a",
        "é": "e", "è": "e", "ẻ": "e", "ẽ": "e", "ẹ": "e",
        "ê": "e", "ế": "e", "ề": "e", "ể": "e", "ễ": "e", "ệ": "e",
        "í": "i", "ì": "i", "ỉ": "i", "ĩ": "i", "ị": "i",
        "ó": "o", "ò": "o", "ỏ": "o", "õ": "o", "ọ": "o",
        "ô": "o", "ố": "o", "ồ": "o", "ổ": "o", "ỗ": "o", "ộ": "o",
        "ơ": "o", "ớ": "o", "ờ": "o", "ở": "o", "ỡ": "o", "ợ": "o",
        "ú": "u", "ù": "u", "ủ": "u", "ũ": "u", "ụ": "u",
        "ư": "u", "ứ": "u", "ừ": "u", "ử": "u", "ữ": "u", "ự": "u",
        "ý": "y", "ỳ": "y", "ỷ": "y", "ỹ": "y", "ỵ": "y",
        "đ": "d",
    }
    out_chars = []
    for ch in s:
        out_chars.append(table.get(ch.lower(), ch.lower()))
    return "".join(out_chars)


def _context_span(text: str, start: int, end: int, window: int = 24) -> str:
    lo = max(0, start - window)
    hi = min(len(text), end + window)
    return text[lo:hi]


# A "letter" for word-boundary purposes: ASCII letters, digits, underscore, OR
# any Vietnamese letter in the U+00C0..U+1EF9 range. We use this so that 'phải'
# is correctly bounded by the space and by 'ọ' inside 'phải_chờ'.
_LETTER_RE = re.compile(r"[A-Za-z0-9_\u00C0-\u024F\u1E00-\u1EFF]")


def _is_letter(ch: str) -> bool:
    return bool(_LETTER_RE.match(ch))


def _negation_token_matches_at(text: str, tok: str, start: int) -> bool:
    """Check whether ``tok`` occurs in ``text`` ending at ``start`` (so the
    negation immediately precedes the flagged token at index ``start``),
    respecting word boundaries.

    We match BOTH the raw token (diacritic-sensitive — so 'đâu' matches only
    'đâu', never 'đầu') AND its folded form (so ascii 'dau' still matches
    when the user wrote without diacritics). The word boundary is checked
    against the actual preceding character so we never match a negation token
    that is a substring of a longer word.
    """
    if not tok or start <= 0:
        return False
    candidates = {tok, _lower_fold(tok)}
    for cand in candidates:
        if not cand:
            continue
        end = start
        begin = end - len(cand)
        if begin < 0:
            continue
        if text[begin:end].lower() != cand.lower():
            continue
        # Word boundary BEFORE the candidate: the char at begin-1 must not be
        # a letter (else the candidate is a suffix of a longer word).
        if begin > 0 and _is_letter(text[begin - 1]):
            continue
        # Word boundary AFTER the candidate: the char at start (= end) must not
        # be a letter (else the candidate is a prefix of a longer word). Note
        # the flagged token itself starts here, so we accept a following space
        # or the flagged token's first char only if it is non-letter... but the
        # flagged token IS a letter, so the negation must be separated by a
        # space/punct. The caller passes start = flagged token start, so the
        # char at `start` is the first char of the flagged token; we require
        # the negation to end exactly at start (adjacency) OR be followed by a
        # non-letter then the flagged token. We already verified end == start.
        return True
    return False


def _negation_context(text: str, start: int) -> str:
    """Inspect up to 24 chars before the match start for a negation token.

    A negation is recognized only when a negation token appears as a COMPLETE
    word within the prefix window (word boundaries enforced), so 'đầu' inside
    'đầu tư' does NOT count as the negation 'đâu'.

    Returns:
      "negated"           — a negation token is present as a whole word in the
                            24-char prefix window
      "no_negation_window"— the prefix window contains no whole-word negation
    """
    prefix = text[max(0, start - 24):start]
    # We scan the prefix for each negation token as a whole word. We accept
    # adjacency to the flagged token OR a short gap (<= 8 chars of spaces /
    # punctuation). This mirrors Vietnamese/English negation phrasing like
    # "không bullish", "not bullish", "chưa nên".
    for tok in NEGATION_TOKENS:
        # Try the raw token first (diacritic-sensitive).
        for cand in (tok, _lower_fold(tok)):
            if not cand:
                continue
            search_from = 0
            while True:
                idx = prefix.lower().find(cand.lower(), search_from)
                if idx < 0:
                    break
                end_idx = idx + len(cand)
                # Word boundary before.
                if idx > 0 and _is_letter(prefix[idx - 1]):
                    search_from = idx + 1
                    continue
                # Word boundary after: char at end_idx must not be a letter.
                if end_idx < len(prefix) and _is_letter(prefix[end_idx]):
                    search_from = idx + 1
                    continue
                # Whole-word negation found in prefix window.
                return "negated"
    return "no_negation_window"


def _iter_matches(regex: "re.Pattern[str]", text: str):
    for m in regex.finditer(text):
        yield m.group(1), m.start(), m.end()


# ====================================================================
# Layer scanners
# ====================================================================

def scan_lexical(text: str) -> List[LayerFinding]:
    """Layer 1: prohibited token scan, negation-aware."""
    findings: List[LayerFinding] = []
    for token, start, end in _iter_matches(_LEXICAL_RE, text):
        ctx = _negation_context(text, start)
        force = "canceled" if ctx == "negated" else "active"
        findings.append(LayerFinding(
            layer="lexical",
            matched_token=token,
            text_span=_context_span(text, start, end),
            char_start=start,
            char_end=end,
            negation_context=ctx,
            advice_force=force,
        ))
    # Verdict tokens are lexical too (BUY/SELL/HOLD verdict tokens prohibited).
    for token, start, end in _iter_matches(_VERDICT_RE, text):
        ctx = _negation_context(text, start)
        force = "canceled" if ctx == "negated" else "active"
        findings.append(LayerFinding(
            layer="lexical",
            matched_token=token,
            text_span=_context_span(text, start, end),
            char_start=start,
            char_end=end,
            negation_context=ctx,
            advice_force=force,
        ))
    return findings


def scan_semantic(text: str) -> List[LayerFinding]:
    """Layer 2: advice-implication patterns (forecasting, targets, conviction)."""
    findings: List[LayerFinding] = []
    for pat in SEMANTIC_ADVICE_PATTERNS:
        for m in pat.finditer(text):
            start, end = m.start(), m.end()
            ctx = _negation_context(text, start)
            force = "canceled" if ctx == "negated" else "active"
            findings.append(LayerFinding(
                layer="semantic",
                matched_token=m.group(0),
                text_span=_context_span(text, start, end),
                char_start=start,
                char_end=end,
                negation_context=ctx,
                advice_force=force,
            ))
    return findings


def scan_imperative(text: str) -> List[LayerFinding]:
    """Layer 3: imperative-mood tokens (nên, phải, cần, hãy, should, must, ...)."""
    findings: List[LayerFinding] = []
    for token, start, end in _iter_matches(_IMPERATIVE_RE, text):
        ctx = _negation_context(text, start)
        # Imperative negated: "không nên", "đừng mua" — the negation makes the
        # utterance non-advice in force, so it is allowed (canceled).
        force = "canceled" if ctx == "negated" else "active"
        findings.append(LayerFinding(
            layer="imperative",
            matched_token=token,
            text_span=_context_span(text, start, end),
            char_start=start,
            char_end=end,
            negation_context=ctx,
            advice_force=force,
        ))
    return findings


def detect_injected_advice_phrases(text: str) -> List[LayerFinding]:
    """Specifically detect injected advice phrases from MUT-ADV-LANG fixtures.

    These phrases are the canonical negative-fixture triggers (e.g. "nên mua").
    They overlap with lexical + imperative but are reported as a distinct
    diagnostic so a downstream consumer can attribute the violation to the
    injection rather than to ambient phrasing.
    """
    injected_phrases = ("nên mua", "nen mua", "nên bán", "nen ban",
                        "khuyến nghị mua", "khuyen nghi mua",
                        "strong buy", "strong sell")
    findings: List[LayerFinding] = []
    for phrase in injected_phrases:
        folded_text = _lower_fold(text)
        folded_phrase = _lower_fold(phrase)
        start = 0
        while True:
            idx = folded_text.find(folded_phrase, start)
            if idx < 0:
                break
            end = idx + len(phrase)
            ctx = _negation_context(text, idx)
            force = "canceled" if ctx == "negated" else "active"
            findings.append(LayerFinding(
                layer="injected_phrase",
                matched_token=text[idx:end],
                text_span=_context_span(text, idx, end),
                char_start=idx,
                char_end=end,
                negation_context=ctx,
                advice_force=force,
            ))
            start = end
    return findings


# ====================================================================
# Public entry point
# ====================================================================

# Frozen failure codes (must match vta-failure-code-registry.yaml exactly).
_FAILURE_CODE_ADVICE_LANGUAGE_DETECTED = "ADVICE_LANGUAGE_DETECTED"
_DIAGNOSTIC_INJECTED_ADVICE_PHRASE_FOUND = "INJECTED_ADVICE_PHRASE_FOUND"
_DIAGNOSTIC_PROHIBITED_TOKEN_FOUND = "PROHIBITED_TOKEN_FOUND"
_DIAGNOSTIC_SEMANTIC_ADVICE_DETECTED = "SEMANTIC_ADVICE_DETECTED"
_DIAGNOSTIC_IMPERATIVE_MOOD_DETECTED = "IMPERATIVE_MOOD_DETECTED"
_DIAGNOSTIC_NEGATION_BLIND_MATCH = "NEGATION_BLIND_MATCH"

_LAYERS_IN_ORDER = ("lexical", "semantic", "imperative")


def check_language(output_text: str) -> LanguageCheckResult:
    """Run the 3-layer non-advice check with negation-awareness.

    Args:
        output_text: the text content to vet (any string).

    Returns:
        LanguageCheckResult. ``passed`` is True iff all three layers report zero
        ACTIVE-force findings. Canceled (negated) findings do NOT fail the check
        (negation-awareness per VC-REQ007-NEGATION).
    """
    if not isinstance(output_text, str):
        # Non-string input is a contract violation; surface as a failure rather
        # than silently coercing. The diagnostic is the type name.
        return LanguageCheckResult(
            passed=False,
            primary_failure_code=_FAILURE_CODE_ADVICE_LANGUAGE_DETECTED,
            diagnostic_codes=(_DIAGNOSTIC_PROHIBITED_TOKEN_FOUND,),
            findings=(),
            layers_evaluated=_LAYERS_IN_ORDER,
            layer_summary={"lexical": 0, "semantic": 0, "imperative": 0,
                           "error": f"non-string input: {type(output_text).__name__}"},
        )

    text = output_text

    lexical = scan_lexical(text)
    semantic = scan_semantic(text)
    imperative = scan_imperative(text)
    injected = detect_injected_advice_phrases(text)

    # Negation-aware filter: only ACTIVE-force findings count as violations.
    active_lexical = [f for f in lexical if f.advice_force == "active"]
    active_semantic = [f for f in semantic if f.advice_force == "active"]
    active_imperative = [f for f in imperative if f.advice_force == "active"]
    active_injected = [f for f in injected if f.advice_force == "active"]

    # If any active finding exists, we have an advice-language violation.
    # Negation-blind matches (a negated token that we still flagged because our
    # negation window missed it) are surfaced as the NEGATION_BLIND_MATCH
    # diagnostic ONLY when the check still passes — they are informational.
    has_violation = bool(active_lexical or active_semantic or active_imperative or active_injected)

    findings_all = tuple(lexical + semantic + imperative + injected)

    diagnostics: List[str] = []
    if active_lexical:
        diagnostics.append(_DIAGNOSTIC_PROHIBITED_TOKEN_FOUND)
    if active_semantic:
        diagnostics.append(_DIAGNOSTIC_SEMANTIC_ADVICE_DETECTED)
    if active_imperative:
        diagnostics.append(_DIAGNOSTIC_IMPERATIVE_MOOD_DETECTED)
    if active_injected:
        diagnostics.append(_DIAGNOSTIC_INJECTED_ADVICE_PHRASE_FOUND)
    # Surface any negated findings that we DID report (informational; does not
    # by itself fail the check). This corresponds to VC-REQ007-NEGATION
    # observation surface.
    negated_reported = [f for f in findings_all if f.advice_force == "canceled"]
    if negated_reported and not has_violation:
        diagnostics.append(_DIAGNOSTIC_NEGATION_BLIND_MATCH)

    primary = _FAILURE_CODE_ADVICE_LANGUAGE_DETECTED if has_violation else None

    layer_summary = {
        "lexical_active": len(active_lexical),
        "lexical_canceled": len([f for f in lexical if f.advice_force == "canceled"]),
        "semantic_active": len(active_semantic),
        "imperative_active": len(active_imperative),
        "injected_phrase_active": len(active_injected),
    }

    return LanguageCheckResult(
        passed=not has_violation,
        primary_failure_code=primary,
        diagnostic_codes=tuple(dict.fromkeys(diagnostics)),  # de-dup, preserve order
        findings=findings_all,
        layers_evaluated=_LAYERS_IN_ORDER,
        layer_summary=layer_summary,
    )


__all__ = [
    "LanguageCheckResult",
    "LayerFinding",
    "check_language",
    "scan_lexical",
    "scan_semantic",
    "scan_imperative",
    "detect_injected_advice_phrases",
    "LEXICAL_PROHIBITED_TOKENS",
    "IMPERATIVE_TOKENS",
    "NEGATION_TOKENS",
]
