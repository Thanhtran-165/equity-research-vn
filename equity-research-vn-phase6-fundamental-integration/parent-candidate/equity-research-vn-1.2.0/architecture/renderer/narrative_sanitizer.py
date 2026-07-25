#!/usr/bin/env python3
"""
narrative_sanitizer.py — Narrative boundary enforcement.

Architecture Phase B component #5.
Ensures model-generated narrative text cannot inject HTML structure,
JavaScript, or modify deterministic facts.

Phase B uses frozen narrative fixtures, but sanitizer must still work
to prove the boundary is enforceable before Phase C (model generation).
"""
import html
import re

# Tags that model narrative is ALLOWED to contain (whitelist)
ALLOWED_TAGS = {
    "p", "br", "strong", "b", "em", "i", "u", "ul", "ol", "li",
    "blockquote", "span", "h4", "h5", "h6",
}

# Tags that are FORBIDDEN in narrative (injection vectors)
FORBIDDEN_TAGS = {
    "script", "style", "iframe", "canvas", "form", "input",
    "object", "embed", "link", "meta", "base",
    "section", "div", "table", "tr", "td", "th", "thead", "tbody",
}

# Patterns that indicate injection attempts
INJECTION_PATTERNS = [
    (r"const\s+DATA\s*=", "raw_DATA_assignment"),
    (r"new\s+Chart\s*\(", "chart_initialization"),
    (r"<script", "script_tag"),
    (r"on\w+\s*=", "event_handler"),
    (r"javascript:", "javascript_protocol"),
    (r"document\.", "dom_manipulation"),
    (r"window\.", "window_access"),
    (r"eval\s*\(", "eval_call"),
    (r"innerHTML", "inner_html"),
]


def sanitize(narrative_text):
    """Sanitize model narrative text for safe insertion into deterministic HTML.

    Strategy:
    1. Check for forbidden tags and injection patterns
    2. HTML-escape the entire text (no raw HTML allowed from model)
    3. Convert markdown-like syntax to safe HTML (bold, italic, lists)
    4. Return safe text + list of warnings

    Args:
        narrative_text: Raw model output string

    Returns:
        {
            "safe_text": str — sanitized, safe to insert into HTML
            "warnings": list of str — issues found
            "blocked": bool — True if narrative should be rejected entirely
        }
    """
    if not narrative_text:
        return {"safe_text": "", "warnings": [], "blocked": False}

    warnings = []
    text = str(narrative_text)

    # Step 1: Check for injection patterns
    for pattern, name in INJECTION_PATTERNS:
        if re.search(pattern, text, re.I):
            warnings.append(f"injection_attempt: {name}")
            # Block entirely if dangerous pattern found
            if name in ("raw_DATA_assignment", "chart_initialization", "script_tag",
                        "eval_call", "inner_html"):
                return {
                    "safe_text": "",
                    "warnings": warnings,
                    "blocked": True,
                    "reason": f"Blocked: {name} detected in narrative"
                }

    # Step 2: Check for forbidden HTML tags
    found_tags = set()
    for m in re.finditer(r'</?(\w+)', text, re.I):
        tag = m.group(1).lower()
        if tag in FORBIDDEN_TAGS:
            found_tags.add(tag)

    if found_tags:
        warnings.append(f"forbidden_tags_found: {found_tags}")
        # Strip forbidden tags but keep content
        for tag in found_tags:
            text = re.sub(rf'</?{tag}[^>]*>', '', text, flags=re.I)

    # Step 3: HTML-escape everything
    escaped = html.escape(text)

    # Step 4: Convert markdown-like syntax to safe HTML
    # Bold: **text** → <strong>text</strong>
    escaped = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escaped)
    # Italic: *text* → <em>text</em> (but not ** which is bold)
    escaped = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', escaped)
    # Line breaks: double newline → </p><p>
    escaped = f'<p>{escaped}</p>'
    escaped = escaped.replace('\n\n', '</p><p>')
    # Single newlines → <br>
    escaped = escaped.replace('\n', '<br>')

    return {
        "safe_text": escaped,
        "warnings": warnings,
        "blocked": False,
    }


def validate_narrative(narrative_text, section_id, min_chars=200):
    """Validate narrative meets section requirements.

    Returns: (passed: bool, evidence: dict)
    """
    if not narrative_text or not narrative_text.strip():
        return False, {"section_id": section_id, "error": "empty_narrative"}

    # Strip HTML for char counting
    text_only = re.sub(r'<[^>]+>', '', narrative_text)
    text_only = re.sub(r'\s+', ' ', text_only).strip()

    if len(text_only) < min_chars:
        return False, {
            "section_id": section_id,
            "error": "below_min_chars",
            "chars": len(text_only),
            "min_required": min_chars,
        }

    # Check for placeholder text
    placeholder_patterns = ["lorem ipsum", "placeholder", "TODO", "FIXME", "XXX"]
    for p in placeholder_patterns:
        if p.lower() in text_only.lower():
            return False, {"section_id": section_id, "error": f"placeholder_detected: {p}"}

    return True, {"section_id": section_id, "chars": len(text_only)}


if __name__ == "__main__":
    # Quick tests
    test1 = "This is a **bold** narrative about FPT revenue growth."
    r1 = sanitize(test1)
    print(f"Test 1 (safe): blocked={r1['blocked']}, warnings={r1['warnings']}")
    print(f"  output: {r1['safe_text'][:100]}")

    test2 = "<script>const DATA = {evil: true};</script>Narrative"
    r2 = sanitize(test2)
    print(f"\nTest 2 (injection): blocked={r2['blocked']}, warnings={r2['warnings']}")

    test3 = "<div class='section'><canvas id='bad'></canvas>Content</div>"
    r3 = sanitize(test3)
    print(f"\nTest 3 (forbidden tags): blocked={r3['blocked']}, warnings={r3['warnings']}")
    print(f"  output: {r3['safe_text'][:100]}")

    # Validation test
    v = validate_narrative("Short", "executive_summary", min_chars=200)
    print(f"\nValidation (short): passed={v[0]}, evidence={v[1]}")
