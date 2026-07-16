"""
phase6_preflight.py — Layer-2 enforcement: deterministic Phase-6 output gate (PATCH, revised).

FIX #2: whitespace/attribute-order tolerant regex (handles `const DATA =`, `<section class="x" id="sec-...">`).
FIX #3: truncation detection — `</html>` present, no mid-tag cutoff; OUTPUT_TRUNCATED distinct from MALFORMED.
classification ∈ HTML | NARRATION | MALFORMED_HTML | OUTPUT_TRUNCATED | EMPTY
"""
import re

def _has_data_object(text):
    return bool(re.search(r'\bconst\s+DATA\s*=', text)) or bool(re.search(r'\bDATA\s*=\s*\{', text))

def _has_canonical_section(text):
    return bool(re.search(r'<section\b[^>]*\bid\s*=\s*["\']sec-[^"\']+["\']', text, re.I))

def _has_canvas(text):
    return bool(re.search(r'<canvas\b', text, re.I)) or bool(re.search(r'chart-wrap', text, re.I))

def _starts_html(text):
    s = text.lstrip().lower()
    return s.startswith("<!doctype html") or s.startswith("<html")

def _has_doctype(text):
    return bool(re.search(r'<!doctype\s+html', text, re.I))

def _has_close_html(text):
    return bool(re.search(r'</html>\s*$', text.strip(), re.I))

def _narration_prefix(text):
    s = text.lstrip()
    return bool(re.match(r'^(I\'ll|I will|Tôi sẽ|Let me|Step \d|## |# |Bước )', s, re.I))

def _has_fence_near_start(text):
    return "```" in text[:200]

def preflight_phase6(output_text, stop_reason=None):
    """Return (passed, errors, classification, detail).
    stop_reason: from model response (e.g. 'end_turn', 'max_tokens') — used for truncation detection."""
    if not output_text or not output_text.strip():
        return False, ["empty output"], "EMPTY", {}
    detail = {"starts_html": _starts_html(output_text), "has_doctype": _has_doctype(output_text),
              "has_canonical_section": _has_canonical_section(output_text), "has_data_object": _has_data_object(output_text),
              "has_canvas": _has_canvas(output_text), "has_close_html": _has_close_html(output_text),
              "narration_prefix": _narration_prefix(output_text), "has_fence_at_start": _has_fence_near_start(output_text),
              "stop_reason": stop_reason}
    errors = []
    # TRUNCATION detection (FIX #3): started HTML but didn't close, or max_tokens stop
    if detail["starts_html"]:
        if stop_reason == "max_tokens":
            errors.append("OUTPUT_TRUNCATED: model stopped at max_tokens (output likely cut mid-generation)")
        elif not detail["has_close_html"]:
            # check for mid-tag/mid-script cutoff (last chars look incomplete)
            tail = output_text.strip()[-30:]
            if not re.search(r'</(html|body|script|section|div)>\s*$', tail, re.I) and "<" in tail and ">" not in tail.split("<")[-1]:
                errors.append("OUTPUT_TRUNCATED: ends mid-tag (no </html>, last chars incomplete)")
            else:
                errors.append("OUTPUT_TRUNCATED: no closing </html> after HTML start")
    if not detail["starts_html"]:
        errors.append("does not start with <!DOCTYPE html> or <html> (likely narration)")
    if not detail["has_canonical_section"]:
        errors.append("no canonical <section id=\"sec-...\"> elements")
    if not detail["has_data_object"]:
        errors.append("no `const DATA =` JS object")
    if not detail["has_canvas"]:
        errors.append("no chart container/canvas elements")
    if detail["narration_prefix"]:
        errors.append("narration prefix detected (I'll/Let me/Step/Bước/##)")
    if detail["has_fence_at_start"]:
        errors.append("markdown code fence at start (forbidden)")

    passed = len(errors) == 0
    if passed:
        classification = "HTML"
    elif any("OUTPUT_TRUNCATED" in e for e in errors):
        classification = "OUTPUT_TRUNCATED"
    elif detail["narration_prefix"] or _has_fence_near_start(output_text) or not detail["starts_html"]:
        classification = "NARRATION"
    else:
        classification = "MALFORMED_HTML"
    return passed, errors, classification, detail

def content_gate_phase6(output_text):
    """CONTENT GATE (Step 4): check content completeness beyond structure.
    Called AFTER preflight passes (structural). Checks refs count, section count."""
    import re
    errors = []
    ref_count = len(re.findall(r'id=["\']ref-\d+["\']', output_text, re.I))
    if ref_count < 10:
        errors.append(f"references <10: found {ref_count} id=ref-N patterns (REQ-018 requires ≥10)")
    section_count = len(re.findall(r'<section\b[^>]*\bid\s*=\s*["\']sec-[^"\']+["\']', output_text, re.I))
    if section_count < 20:
        errors.append(f"canonical sections <20: found {section_count} (REQ-012 requires ≥20)")
    return len(errors)==0, errors
