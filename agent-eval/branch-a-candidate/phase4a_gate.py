#!/usr/bin/env python3
"""
phase4a_gate.py — Phase-local deterministic gate for Phase 4A (Technical ACTIVE).

BRANCH-A CANDIDATE. Mirrors the structure of phase6_preflight.py but for the Tech Score.

The agent's Phase-4A output may be HTML (a tech-score-card), markdown, JSON-ish, or
plain text. Tech Score / verdict are simple scalar values, so this gate:
  1. EXTRACTS tech_score + verdict from the phase output (tolerant of whitespace, HTML
     data-* attributes, JSON blocks, labelled text, uppercase/lowercase).
  2. VALIDATES: score exists, is integer, in [-6, 6]; verdict in canonical enum;
     score<->verdict consistent per the PREREGISTERED (locked) mapping.
  3. MATCHES against the verified source contract (the `technical` block produced by
     build_data_contract.py from technical_active.json). If the contract is null
     (no source data) the gate returns NO_SOURCE_DATA — no fallback.

PREREGISTERED score→verdict mapping (locked, do not change):
    [-6, -4] → STRONG SELL
    [-3, -2] → SELL
    [-1,  1] → NEUTRAL
    [ 2,  3] → BUY
    [ 4,  6] → STRONG BUY

classification ∈ VALID | MISSING_SCORE | OUT_OF_RANGE | INVALID_VERDICT | MISMATCH | NO_SOURCE_DATA

Return: (passed, errors, classification) where passed is bool, errors is list[str].
"""
import re, json

SCALE_MIN, SCALE_MAX = -6, 6

CANONICAL_VERDICTS = (
    "STRONG SELL", "SELL", "NEUTRAL", "BUY", "STRONG BUY",
)

# PREREGISTERED (locked) score→verdict mapping.
def verdict_for_score(score):
    """Map an integer score to its canonical verdict per the preregistered mapping.
    Returns None if score is outside [-6,6] (caller validates range first)."""
    if not isinstance(score, int):
        return None
    if -6 <= score <= -4: return "STRONG SELL"
    if -3 <= score <= -2: return "SELL"
    if -1 <= score <= 1:  return "NEUTRAL"
    if  2 <= score <= 3:  return "BUY"
    if  4 <= score <= 6:  return "STRONG BUY"
    return None

# ---------------------------------------------------------------------------
# Extraction (tolerant of HTML / JSON / whitespace / case).
# ---------------------------------------------------------------------------

_SCORE_PATTERNS = [
    # HTML data attributes (highest signal): data-score='-6', data-tech-score="-6"
    re.compile(r'data-(?:tech-)?score\s*=\s*["\']\s*(-?\d+)\s*["\']', re.I),
    # labelled text: "tech_score": -6   /   tech_score = -6   /   Tech Score: -6
    # (optional closing quote after the key handles JSON-style "tech_score": ...)
    # (single optional decimal to tolerate "-6.0")
    re.compile(r'tech[ _-]?score"?\s*[:=]\s*"?\s*(-?\d+(?:\.0)?)\s*"?', re.I),
]

_VERDICT_PATTERNS = [
    # HTML data attributes: data-verdict='STRONG SELL'
    re.compile(r'data-verdict\s*=\s*["\']\s*(STRONG\s*SELL|SELL|NEUTRAL|BUY|STRONG\s*BUY)\s*["\']', re.I),
    # labelled text: "verdict": "STRONG SELL"  /  verdict = STRONG SELL  /  Verdict: STRONG SELL
    re.compile(r'verdict"?\s*[:=]\s*["\']?\s*(STRONG\s*SELL|SELL|NEUTRAL|BUY|STRONG\s*BUY)\s*["\']?', re.I),
]

def _extract_score(text):
    """Return the first parseable integer score, or None."""
    if not text:
        return None
    for pat in _SCORE_PATTERNS:
        m = pat.search(text)
        if m:
            try:
                # float("‑6.0")/float("-6") then int() — collapses "-6.0" to -6
                return int(float(m.group(1)))
            except (ValueError, TypeError):
                continue
    return None

def _extract_verdict(text):
    """Return the first canonical verdict (normalized to "STRONG SELL" form), or None."""
    if not text:
        return None
    for pat in _VERDICT_PATTERNS:
        m = pat.search(text)
        if m:
            return _normalize_verdict(m.group(1))
    return None

def _normalize_verdict(v):
    """Normalize whitespace/case variants to the canonical enum form."""
    if not isinstance(v, str):
        return None
    collapsed = re.sub(r'\s+', ' ', v.strip().upper())
    for canon in CANONICAL_VERDICTS:
        if collapsed == canon:
            return canon
    return None

# ---------------------------------------------------------------------------
# Gate.
# ---------------------------------------------------------------------------

def gate_phase4a(phase_output, source_contract=None):
    """Validate Phase-4A Tech Score output.

    phase_output   : str  — the model's Phase-4A output (HTML/JSON/markdown/text).
    source_contract: dict — the `technical` block from verified-dashboard-data.json
                            (the verified source contract). May be None / missing
                            tech_score to represent NO_SOURCE_DATA.

    Returns (passed: bool, errors: list[str], classification: str).
    classification ∈ VALID | MISSING_SCORE | OUT_OF_RANGE | INVALID_VERDICT
                        | MISMATCH | NO_SOURCE_DATA
    """
    errors = []

    # --- source contract presence: no source data → no fallback, fail loud. ---
    if not source_contract or not isinstance(source_contract, dict):
        return False, ["no source data contract (technical block is null/missing — no fallback)"], "NO_SOURCE_DATA"
    contract_score = source_contract.get("tech_score")
    if contract_score is None:
        return False, ["source contract has no tech_score (no fallback)"], "NO_SOURCE_DATA"
    contract_verdict = _normalize_verdict(source_contract.get("verdict"))

    # --- extract from agent output ---
    score = _extract_score(phase_output)
    verdict = _extract_verdict(phase_output)

    # --- missing score (test #2): analysis present but no score. ---
    if score is None:
        errors.append("tech_score not found in phase output")
        return False, errors, "MISSING_SCORE"

    # --- out of range (test #3). ---
    if not isinstance(score, int) or score < SCALE_MIN or score > SCALE_MAX:
        errors.append(f"tech_score {score} outside [{SCALE_MIN},{SCALE_MAX}]")
        return False, errors, "OUT_OF_RANGE"

    # --- invalid verdict (test #4). ---
    if verdict is None:
        errors.append(f"verdict not found or not in canonical enum {CANONICAL_VERDICTS}")
        return False, errors, "INVALID_VERDICT"

    # --- score↔verdict consistency per preregistered mapping (test #5). ---
    expected_verdict = verdict_for_score(score)
    if expected_verdict is None or verdict != expected_verdict:
        errors.append(f"score↔verdict mismatch: score={score} implies verdict={expected_verdict}, got verdict={verdict}")
        return False, errors, "MISMATCH"

    # --- matches source contract (test #6): dashboard score must match verified source. ---
    try:
        contract_score_int = int(contract_score)
    except (ValueError, TypeError):
        contract_score_int = None
    if contract_score_int is None or score != contract_score_int:
        errors.append(f"tech_score {score} does not match verified source contract score {contract_score}")
        return False, errors, "MISMATCH"
    if contract_verdict is not None and verdict != contract_verdict:
        errors.append(f"verdict {verdict} does not match verified source contract verdict {contract_verdict}")
        return False, errors, "MISMATCH"

    return True, [], "VALID"

# Backwards-friendly alias matching phase6_preflight naming convention.
preflight_phase4a = gate_phase4a
