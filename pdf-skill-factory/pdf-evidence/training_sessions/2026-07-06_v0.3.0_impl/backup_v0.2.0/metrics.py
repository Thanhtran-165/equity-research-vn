"""metrics.py — eval metrics for pdf-evidence v0.1.

⚠️ PATCH 3 — READ THIS FIRST ⚠️

This module provides TWO tiers of metrics:

1. RULE-BASED / HEURISTIC (this file):
   - citation_format_accuracy
   - citation_page_accuracy
   - abstention_accuracy
   - table_fidelity
   - numeric_accuracy
   - legal_clause_preservation
   - coverage
   - concision
   - faithfulness_simple  ⚠️ BASELINE HEURISTIC ONLY — see below

2. LLM-JUDGE (spec in groundedness_judge.md):
   - faithfulness        (the DoD metric — replaces faithfulness_simple)
   - hallucination_rate  (the DoD metric)

`faithfulness_simple` is NOT the final faithfulness metric. It is a cheap
substring-match heuristic useful for CI smoke tests. It has known weaknesses:
- cannot detect paraphrased claims
- cannot detect contradictions
- cannot detect unsupported claims that happen to share words with evidence

For release decisions (DEFINITION_OF_DONE.md), use the LLM-judge
`groundedness_judge.md` to compute `faithfulness` and `hallucination_rate`.
The runner reports BOTH; DoD only gates on the LLM-judge versions.

A future version (v0.2+) will wire groundedness_judge.md into a live LLM call.
For v0.1, the LLM-judge is invoked manually or via a stub.
"""
from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Rule-based metrics
# ---------------------------------------------------------------------------

def citation_format_accuracy(citations: list[dict]) -> float:
    """Fraction of citations with all required fields: file, page, section, quote.

    A citation is well-formed if it has non-empty values for all four fields.
    Page may be null ONLY if accompanied by a note explaining why (then it counts
    as 0.5 to reflect partial credit).
    """
    if not citations:
        return 0.0
    score = 0.0
    for c in citations:
        has_file = bool(c.get("file"))
        has_section = bool(c.get("section"))
        has_quote = bool(c.get("quote"))
        page = c.get("page")
        if page is None:
            # only acceptable if a note explains missing page
            if c.get("note"):
                score += 0.5
            continue
        if has_file and has_section and has_quote and isinstance(page, int):
            score += 1.0
    return score / len(citations)


def citation_page_accuracy(citations: list[dict], evidence_pages: set[int]) -> float:
    """Fraction of citations whose page is in the evidence page set."""
    if not citations:
        return 0.0
    if not evidence_pages:
        # no evidence extracted — any citation is suspect
        return 0.0
    ok = sum(1 for c in citations if c.get("page") in evidence_pages)
    return ok / len(citations)


def abstention_accuracy(actual: dict, expected_abstain: bool) -> float:
    """1.0 if abstention behavior matches expectation, else 0.0."""
    actual_abstain = bool(actual.get("abstention_flag", False))
    return 1.0 if actual_abstain == expected_abstain else 0.0


def table_fidelity(actual_table: dict | None, expected_table: dict | None) -> float:
    """Cell-by-cell comparison of headers + rows. 1.0 = perfect match."""
    if expected_table is None:
        # No table expected — pass if skill didn't emit one either.
        return 1.0 if actual_table is None else 0.5
    if actual_table is None:
        return 0.0
    exp_headers = expected_table.get("headers") or []
    act_headers = actual_table.get("headers") or []
    header_score = _list_match(exp_headers, act_headers)
    exp_rows = expected_table.get("rows") or []
    act_rows = actual_table.get("rows") or []
    if not exp_rows:
        return header_score
    row_score = 0.0
    for er, ar in zip(exp_rows, act_rows):
        row_score += _list_match(er or [], ar or [])
    row_score /= len(exp_rows)
    return 0.5 * header_score + 0.5 * row_score


def _list_match(a: list, b: list) -> float:
    if not a:
        return 1.0 if not b else 0.0
    if len(a) != len(b):
        # length mismatch — score on overlap
        n = min(len(a), len(b))
        matches = sum(1 for i in range(n) if str(a[i]).strip() == str(b[i]).strip())
        return matches / len(a)
    matches = sum(1 for i in range(len(a)) if str(a[i]).strip() == str(b[i]).strip())
    return matches / len(a)


def numeric_accuracy(answer: str, expected_numbers: list[str]) -> float:
    """Fraction of expected number strings present in the answer."""
    if not expected_numbers:
        return 1.0
    found = sum(1 for n in expected_numbers if n in answer)
    return found / len(expected_numbers)


def legal_clause_preservation(answer: str, expected_clauses: list[str]) -> float:
    """Fraction of expected legal clauses (e.g. 'Điều 1', 'Khoản 2') preserved verbatim."""
    if not expected_clauses:
        return 1.0
    found = sum(1 for c in expected_clauses if c in answer)
    return found / len(expected_clauses)


def coverage(answered_points: int, required_points: int) -> float:
    """Fraction of required points the answer covered."""
    if required_points == 0:
        return 1.0
    return min(1.0, answered_points / required_points)


def concision(answer: str, max_chars: int | None) -> float:
    """1.0 if answer within max_chars, else proportional penalty."""
    if max_chars is None:
        return 1.0
    if len(answer) <= max_chars:
        return 1.0
    return max_chars / len(answer)


# ---------------------------------------------------------------------------
# ⚠️ BASELINE HEURISTIC — see PATCH 3 warning at top of file
# ---------------------------------------------------------------------------

def faithfulness_simple(claims: list[str], evidence_snippets: list[str]) -> float:
    """⚠️ BASELINE HEURISTIC — NOT the DoD faithfulness metric.

    Returns the fraction of `claims` that appear (as a substring, case-insensitive)
    in any evidence snippet. Useful only as a CI smoke signal.

    Known weaknesses:
    - Misses paraphrased claims (false negative).
    - Misses contradictions (claims present in evidence but spun wrongly).
    - Counts word-overlap as support (false positive).

    For release decisions, use `groundedness_judge.md` (LLM-judge) instead.
    That metric returns per-claim verdict: supported / contradicted / not_enough_evidence.
    """
    if not claims:
        return 1.0
    if not evidence_snippets:
        return 0.0
    haystack = " ".join(evidence_snippets).lower()
    supported = 0
    for claim in claims:
        # naive: try whole-claim substring; fallback to longest 4-word window
        if claim.lower() in haystack:
            supported += 1
            continue
        words = claim.split()
        if len(words) >= 4:
            window = " ".join(words[:4]).lower()
            if window in haystack:
                supported += 1
    return supported / len(claims)


# ---------------------------------------------------------------------------
# LLM-judge stubs (wire to groundedness_judge.md in v0.2+)
# ---------------------------------------------------------------------------

def faithfulness_llmjudge(claims: list[str], evidence_snippets: list[str], verdicts: list[dict] | None = None) -> float:
    """Faithfulness = (#supported) / (#claims), using groundedness_judge.md verdicts.

    `verdicts` is a list of {verdict: "supported"|"contradicted"|"not_enough_evidence", ...}
    produced by an LLM judge following groundedness_judge.md. If None, returns
    -1.0 to signal "LLM judge not run" (do not gate DoD on this in v0.1 unless
    you wire it up).
    """
    if verdicts is None:
        return -1.0
    if not claims:
        return 1.0
    supported = sum(1 for v in verdicts if v.get("verdict") == "supported")
    return supported / len(claims)


def hallucination_rate_llmjudge(claims: list[str], verdicts: list[dict] | None = None) -> float:
    """hallucination_rate = (#contradicted + #not_enough_evidence) / #claims.

    Uses groundedness_judge.md verdicts. Returns -1.0 if verdicts is None.
    """
    if verdicts is None:
        return -1.0
    if not claims:
        return 0.0
    bad = sum(1 for v in verdicts if v.get("verdict") in ("contradicted", "not_enough_evidence"))
    return bad / len(claims)


# ---------------------------------------------------------------------------
# v0.2.0 metrics (F-ABSTAIN-001 + TABLE-WIRING-001)
# ---------------------------------------------------------------------------

def partial_abstention_accuracy(actual: dict, expected: dict) -> float:
    """F-ABSTAIN-001. Refusal appears in partial_abstentions[] when expected,
    and does NOT appear when not expected.

    Expected gates (from fixture):
      expected["partial_abstention_expected"] = True/False
      expected["partial_abstention_topic"]    = keyword that should appear in some entry (optional)
    """
    expected_partial = bool(expected.get("partial_abstention_expected", False))
    actual_partial = actual.get("partial_abstentions") or []
    has_actual = len(actual_partial) > 0

    # Basic match: presence/absence
    if expected_partial != has_actual:
        return 0.0

    # If not expected, and not present → perfect.
    if not expected_partial:
        return 1.0

    # If expected AND present → check topic keyword is mentioned in some entry.
    topic = expected.get("partial_abstention_topic")
    if topic:
        joined = " ".join(
            (e.get("claim_or_question_part", "") + " " + e.get("reason", "") + " " + e.get("missing_evidence", ""))
            for e in actual_partial
        ).lower()
        if topic.lower() not in joined:
            return 0.3  # refusal present but on wrong topic
    # Confidence gate: each entry must have confidence >= 0.7 for the refusal
    if any((e.get("confidence") or 0) < 0.7 for e in actual_partial):
        return 0.6
    return 1.0


def abstention_visibility(actual: dict) -> float:
    """Returns 1.0 if abstention is at top level (abstention_flag OR partial_abstentions[]),
    0.0 if buried only in warnings[]. Discrete metric (reported as float for aggregation)."""
    has_flag = bool(actual.get("abstention_flag", False))
    has_partial = bool(actual.get("partial_abstentions"))
    if has_flag or has_partial:
        return 1.0
    # No top-level abstention — check if a refusal-flavored string slipped into warnings
    warnings = actual.get("warnings") or []
    refusal_markers = ("insufficient evidence", "not_enough_evidence", "abstain", "không đủ bằng chứng")
    buried = any(any(m in str(w).lower() for m in refusal_markers) for w in warnings)
    return 0.0 if buried else 1.0


def table_header_preservation(actual: dict, expected: dict) -> float:
    """TABLE-WIRING-001. For tables the skill claimed to extract, headers must be
    preserved vs the expected_table. 1.0 if all expected headers present (string
    contains, ASCII-degraded tolerant)."""
    expected_table = expected.get("expected_table")
    actual_table = actual.get("expected_table") or actual.get("table")
    if not expected_table:
        return 1.0  # no table expected → vacuously pass
    if not actual_table:
        return 0.0
    exp_headers = [str(h) for h in (expected_table.get("headers") or [])]
    act_headers = [str(h) for h in (actual_table.get("headers") or [])]
    if not exp_headers:
        return 1.0
    # ASCII-degrade both sides to tolerate mojibake
    def degrade(s: str) -> str:
        return s.encode("ascii", "ignore").decode().lower()
    act_degraded = [degrade(h) for h in act_headers]
    found = 0
    for eh in exp_headers:
        ed = degrade(eh)
        if any(ed in ad or ad in ed for ad in act_degraded):
            found += 1
    return found / len(exp_headers)


def table_unit_preservation(actual: dict, expected: dict) -> float:
    """TABLE-WIRING-001. units field on the extracted table must match expected.
    Tolerates ASCII degradation."""
    expected_unit = expected.get("expected_units")
    actual_table = actual.get("expected_table") or actual.get("table")
    if not expected_unit:
        return 1.0
    if not actual_table:
        return 0.0
    actual_unit = actual_table.get("units")
    if not actual_unit:
        return 0.0
    def degrade(s: str) -> str:
        return s.encode("ascii", "ignore").decode().lower().replace(" ", "")
    if degrade(str(expected_unit)) in degrade(str(actual_unit)) or degrade(str(actual_unit)) in degrade(str(expected_unit)):
        return 1.0
    return 0.0


def table_cell_accuracy(actual: dict, expected: dict) -> float | None:
    """TABLE-WIRING-001. Cell-by-cell match of expected_table rows vs actual.
    Returns None (N/A) when no expected_table present."""
    expected_table = expected.get("expected_table")
    actual_table = actual.get("expected_table") or actual.get("table")
    if not expected_table:
        return None
    if not actual_table:
        return 0.0
    exp_rows = expected_table.get("rows") or []
    act_rows = actual_table.get("rows") or []
    if not exp_rows:
        return 1.0
    # Compare by position; tolerate shorter actual rows (missing trailing cells)
    total = 0
    matched = 0
    for er, ar in zip(exp_rows, act_rows):
        for i, ev in enumerate(er):
            total += 1
            av = ar[i] if i < len(ar) else None
            if ev is not None and av is not None and str(ev).strip() == str(av).strip():
                matched += 1
            elif ev is None and (av is None or av == ""):
                matched += 1  # both empty
    return matched / total if total else 1.0


def table_handling(actual: dict, expected: dict) -> float:
    """Composite: avg of table_id presence + header preservation + cell accuracy.
    Only computed when expected_table present; else returns 1.0 (vacuous)."""
    expected_table = expected.get("expected_table")
    if not expected_table:
        return 1.0
    # sub-metric 1: citation has table_id/chart_id on table-page cases
    citations = actual.get("citations") or []
    expected_id_prefix = expected.get("expected_table_id_prefix") or expected.get("expected_chart_id_prefix")
    id_score = 1.0
    if expected_id_prefix and citations:
        id_score = sum(1 for c in citations if any(
            str(c.get(k) or "").startswith(expected_id_prefix) for k in ("table_id", "chart_id")
        )) / len(citations)
    header_score = table_header_preservation(actual, expected)
    cell = table_cell_accuracy(actual, expected)
    cell_score = 1.0 if cell is None else cell
    return (id_score + header_score + cell_score) / 3.0


def table_uncertainty_disclosed(actual: dict, expected: dict) -> float:
    """B.5 — if expected_table_uncertainty_disclosure=true, actual must disclose
    (either the table object carries table_uncertainty_disclosure=true OR a
    citation note contains 'uncertain'). Returns 1.0/0.0."""
    if not expected.get("expected_table_uncertainty_disclosure"):
        return 1.0  # not required
    # check table object
    tbl = actual.get("expected_table") or actual.get("table") or {}
    if tbl.get("table_uncertainty_disclosure"):
        return 1.0
    if actual.get("table_uncertainty_disclosure"):
        return 1.0
    # check citation notes
    for c in (actual.get("citations") or []):
        if "uncertain" in str(c.get("note") or "").lower():
            return 1.0
    return 0.0


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

def compute_all(actual: dict, expected: dict, evidence_pages: set[int]) -> dict[str, Any]:
    """Compute every metric for one fixture case.

    `actual` follows the skill output schema (02-PDF_SKILL_SPEC.md §5).
    `expected` follows the fixture `expected` block.
    Returns a dict of metric_name -> value. LLM-judge metrics return -1.0 when
    not run.
    """
    citations = actual.get("citations") or []
    evidence = actual.get("evidence") or []
    evidence_snippets = [e.get("snippet", "") for e in evidence]
    answer = actual.get("answer", "") or ""

    # naive claim extraction: split answer into sentences (heuristic only)
    claims = [s.strip() for s in re.split(r"[\.!\?]\s+", answer) if len(s.strip()) > 20]

    metrics = {
        "citation_format_accuracy": citation_format_accuracy(citations),
        "citation_page_accuracy": citation_page_accuracy(citations, evidence_pages),
        "abstention_accuracy": abstention_accuracy(actual, bool(expected.get("abstention_expected", False))),
        "table_fidelity": table_fidelity(actual.get("expected_table") or actual.get("table"), expected.get("expected_table")),
        "numeric_accuracy": numeric_accuracy(answer, expected.get("expected_numbers", [])),
        "legal_clause_preservation": legal_clause_preservation(answer, expected.get("expected_clauses", [])),
        "coverage": coverage(expected.get("answered_points", 1), expected.get("required_points", 1)),
        "concision": concision(answer, expected.get("max_chars")),
        # ⚠️ baseline heuristic, see PATCH 3
        "faithfulness_simple": faithfulness_simple(claims, evidence_snippets),
        # LLM-judge metrics — stubbed to -1.0 in v0.1
        "faithfulness": faithfulness_llmjudge(claims, evidence_snippets, None),
        "hallucination_rate": hallucination_rate_llmjudge(claims, None),
        # v0.2.0 metrics (F-ABSTAIN-001 + TABLE-WIRING-001)
        "partial_abstention_accuracy": partial_abstention_accuracy(actual, expected),
        "abstention_visibility": abstention_visibility(actual),
        "abstention_quality": partial_abstention_accuracy(actual, expected),  # alias: maps to partial_abstention_accuracy + visibility
        "table_handling": table_handling(actual, expected),
        "table_header_preservation": table_header_preservation(actual, expected),
        "table_unit_preservation": table_unit_preservation(actual, expected),
        "table_cell_accuracy": table_cell_accuracy(actual, expected),
        "table_uncertainty_disclosed": table_uncertainty_disclosed(actual, expected),
    }
    return metrics
