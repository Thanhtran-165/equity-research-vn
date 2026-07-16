"""
content_depth_gate.py — Phase-local semantic content-depth gate (v0.8.0).

PURPOSE (owner directive 2026-07-14):
  REQ-013 appeared 3/10 in Cohort C across 3 sectors (KDH, VCB, FPT). Char-count
  alone is gameable — a section can exceed 200 chars with disclaimers, boilerplate,
  or pure data labels. This gate checks SEMANTIC depth:

    1. effective_chars ≥200 (after stripping HTML, scripts, citations, boilerplate)
    2. ≥1 analytical sentence (contains connective/insight language, not just data)
    3. not boilerplate-dominated (disclaimer/copyright/header text ratio < 60%)
    4. not pure data-labeling (number+label patterns alone don't count as analysis)

  If a section FAILS, the phase-local retry mechanism feeds back WHICH section
  lacks depth and WHY, so the model can fix it on retry (not just "too short").

  This gate runs AFTER phase6_preflight passes (structural) and BEFORE the final
  verifier. It's a Layer-2 deterministic check — no model inference.
"""
import re

# Minimum effective characters per canonical section (matches REQ-013 threshold)
MIN_EFFECTIVE_CHARS = 200

# Sections EXEMPT from depth check (structural/headers/references, not analytical).
# REQ-013 should only apply to sections expected to contain prose analysis.
# Exempt: hero (title banner), source (reference list), glossary (definitions),
#         checklist (yes/no grid), analyst (credentials line).
_STRUCTURAL_SECTIONS = frozenset({
    "sec-hero", "sec-source", "sec-glossary", "sec-checklist", "sec-analyst",
})

# Analytical/connective language signals (Vietnamese + English)
# A sentence with one of these is likely genuine analysis, not data labeling.
_ANALYSIS_SIGNALS = [
    # Vietnamese analytical connectors
    r"giải thích", r"cho thấy", r"cho thấy", r"phản ánh", r"nguyên nhân",
    r"do đó", r"bởi vì", r"điều này", r"hệ quả", r"ngụ ý", r"cụ thể",
    r"đáng chú ý", r"tương phản", r"so với", r"so với", r"so sánh",
    r"ngược lại", r"tương tự", r"hơn nữa", r"tuy nhiên", r"mặc dù",
    r"trong khi", r"đồng thời", r"nếu", r"trường hợp", r"kịch bản",
    r"xu hướng", r"động lực", r"rủi ro", r"cơ hội", r"triển vọng",
    r"điểm yếu", r"điểm mạnh", r"thách thức", r"lợi thế cạnh tranh",
    # English analytical connectors
    r"explains", r"indicates", r"suggests", r"reflects", r"because",
    r"therefore", r"however", r"although", r"while", r"compared",
    r"contrast", r"similarly", r"furthermore", r"moreover", r"consequently",
    r"trend", r"driver", r"risk", r"opportunity", r"outlook",
    r"weakness", r"strength", r"advantage", r"competitive",
]

# Boilerplate patterns (should not dominate a section)
_BOILERPLATE_PATTERNS = [
    r"không phải khuyến nghị", r"không cấu thành", r"mang tính tham khảo",
    r"not investment advice", r"for educational purposes",
    r"bản quyền", r"copyright", r"©", r"all rights reserved",
    r"source:?\s*vnstock", r"nguồn:?\s*vnstock",
]

# Data-labeling patterns (numbers + short labels, not analysis)
_DATA_LABEL_PATTERN = re.compile(
    r"[\d.,]+\s*[%‰]\s*[~]?\s*[\d.,]+\s*tỷ",  # "55% ~1,604 tỷ"
    re.IGNORECASE
)


def _strip_to_effective_text(section_html):
    """Extract effective prose text from a section's HTML.

    Removes: HTML tags, <script>/<style> blocks, citation-only elements,
    repeated whitespace. Keeps: visible text content.
    """
    # Remove script and style blocks entirely
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", section_html, flags=re.DOTALL | re.I)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.I)
    # Remove canvas/chart-container elements (visual only, no prose)
    text = re.sub(r"<canvas\b[^>]*/?>", " ", text, flags=re.I)
    # Strip all remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _split_sentences(text):
    """Split text into sentences (Vietnamese + English aware)."""
    # Split on . ! ? । followed by space or end
    raw = re.split(r"[.!?]\s+", text)
    # Filter: meaningful sentences (>15 chars, not just numbers)
    return [s.strip() for s in raw if len(s.strip()) > 15]


def _is_analytical(sentence):
    """Check if a sentence contains analytical/connective language (not pure data)."""
    lower = sentence.lower()
    for signal in _ANALYSIS_SIGNALS:
        if re.search(signal, lower):
            return True
    return False


def _boilerplate_ratio(text):
    """Fraction of text that matches boilerplate patterns (0.0 to 1.0)."""
    if not text:
        return 0.0
    boilerplate_chars = 0
    for pat in _BOILERPLATE_PATTERNS:
        for m in re.finditer(pat, text, re.I):
            boilerplate_chars += len(m.group(0))
    return min(boilerplate_chars / max(len(text), 1), 1.0)


def _data_label_ratio(text):
    """Fraction of text that is pure data-label patterns (0.0 to 1.0)."""
    if not text:
        return 0.0
    data_chars = sum(len(m.group(0)) for m in _DATA_LABEL_PATTERN.finditer(text))
    return min(data_chars / max(len(text), 1), 1.0)


def check_section_depth(section_html, section_id=None):
    """Check a single section's content depth semantically.

    Returns: {
        'passed': bool,
        'effective_chars': int,
        'min_required': int,
        'analysis_sentences': int,
        'has_analytical_insight': bool,
        'boilerplate_ratio': float,
        'data_label_ratio': float,
        'failures': [str],  # specific reasons, for retry feedback
    }
    """
    text = _strip_to_effective_text(section_html)
    effective_chars = len(text)
    sentences = _split_sentences(text)
    analysis_sentences = [s for s in sentences if _is_analytical(s)]
    bp_ratio = _boilerplate_ratio(text)
    dl_ratio = _data_label_ratio(text)

    failures = []
    # Layer 1: char-count check (matches REQ-013 exactly — catches the same defect)
    if effective_chars < MIN_EFFECTIVE_CHARS:
        failures.append(
            f"effective_chars={effective_chars} < {MIN_EFFECTIVE_CHARS} "
            f"(section too short after stripping HTML/scripts)"
        )
    # Layer 2: semantic check — only for borderline sections (200-250 chars).
    # Sections well above 250 chars are substantive (structured bullet analysis,
    # data tables). The semantic bar applies where depth is genuinely thin and
    # a section might game the char-count with padding.
    SEMANTIC_CHECK_THRESHOLD = 250
    if effective_chars < SEMANTIC_CHECK_THRESHOLD:
        if len(analysis_sentences) < 1:
            failures.append(
                f"section is short ({effective_chars} chars < {SEMANTIC_CHECK_THRESHOLD}) AND lacks "
                f"analytical sentence (need ≥1 with explanatory language like 'giải thích', "
                f"'phản ánh', 'tuy nhiên', 'so với', 'indicates', 'however'); "
                f"found {len(sentences)} sentences, none analytical"
            )
        if dl_ratio > 0.50 and len(analysis_sentences) == 0:
            failures.append(
                f"data_label_ratio={dl_ratio:.2f} > 0.50 in a short section with no analysis "
                f"(section is pure data labels like '55% ~1,604 tỷ', needs explanatory prose)"
            )
    # Layer 3: boilerplate dominance (any length) — catches padding with disclaimers
    if bp_ratio > 0.60:
        failures.append(
            f"boilerplate_ratio={bp_ratio:.2f} > 0.60 (section dominated by disclaimers/boilerplate, "
            f"not analysis)"
        )

    return {
        "passed": len(failures) == 0,
        "effective_chars": effective_chars,
        "min_required": MIN_EFFECTIVE_CHARS,
        "total_sentences": len(sentences),
        "analysis_sentences": len(analysis_sentences),
        "has_analytical_insight": len(analysis_sentences) >= 1,
        "boilerplate_ratio": round(bp_ratio, 3),
        "data_label_ratio": round(dl_ratio, 3),
        "failures": failures,
    }


def check_all_sections(html_text):
    """Check all canonical <section id="sec-..."> elements in the dashboard HTML.

    Returns: {
        'passed': bool (all sections pass),
        'sections_checked': int,
        'sections_passed': int,
        'sections_failed': int,
        'failures_by_section': {section_id: [failure_reasons]},
        'detail_by_section': {section_id: {check details}},
    }
    """
    # Find all canonical sections
    section_pattern = re.compile(
        r'(<section\b[^>]*\bid\s*=\s*["\'](sec-[^"\']+)["\'][^>]*>)(.*?)(</section>)',
        re.DOTALL | re.I
    )
    matches = section_pattern.findall(html_text)

    failures_by_section = {}
    detail_by_section = {}
    sections_passed = 0

    for open_tag, section_id, inner_html, close_tag in matches:
        # Skip structural sections (headers, references, glossary, etc.)
        if section_id in _STRUCTURAL_SECTIONS:
            continue
        full_section = open_tag + inner_html + close_tag
        result = check_section_depth(full_section, section_id)
        detail_by_section[section_id] = result
        if result["passed"]:
            sections_passed += 1
        else:
            failures_by_section[section_id] = result["failures"]

    total = len([m for m in matches if m[1] not in _STRUCTURAL_SECTIONS])
    return {
        "passed": len(failures_by_section) == 0,
        "sections_checked": total,
        "sections_passed": sections_passed,
        "sections_failed": total - sections_passed,
        "failures_by_section": failures_by_section,
        "detail_by_section": detail_by_section,
    }


def format_retry_feedback(gate_result):
    """Format gate failures as actionable feedback for phase-local retry.

    Returns a string the model can use to fix shallow sections on retry.
    """
    if gate_result["passed"]:
        return "All sections pass content-depth check."
    lines = [
        f"CONTENT_DEPTH_GATE FAILED on {gate_result['sections_failed']}/{gate_result['sections_checked']} sections.",
        "Each section needs: ≥200 effective chars AND ≥1 analytical sentence (not just data labels).",
        "Fix these sections by adding explanatory prose that connects data to insights:",
        ""
    ]
    for section_id, failures in gate_result["failures_by_section"].items():
        lines.append(f"  [{section_id}]")
        for f in failures:
            lines.append(f"    - {f}")
        lines.append("")
    lines.append("Do NOT pad with disclaimers or boilerplate. Add genuine analysis: why does the data look this way, what does it imply, how does it compare?")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 2:
        print("Usage: python3 content_depth_gate.py <dashboard.html>")
        sys.exit(1)
    html = open(sys.argv[1]).read()
    result = check_all_sections(html)
    print(json.dumps({
        "passed": result["passed"],
        "sections_checked": result["sections_checked"],
        "sections_passed": result["sections_passed"],
        "sections_failed": result["sections_failed"],
        "failed_sections": list(result["failures_by_section"].keys()),
    }, indent=2))
    if not result["passed"]:
        print("\n" + format_retry_feedback(result))
    sys.exit(0 if result["passed"] else 1)
