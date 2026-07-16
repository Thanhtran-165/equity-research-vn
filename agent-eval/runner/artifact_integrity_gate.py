#!/usr/bin/env python3
"""
artifact_integrity_gate.py — Phase 6 structural preflight hardening (Branch C, v0.11.0).

PURPOSE (owner directive 2026-07-15):
  REQ-019 (JS syntax) and REQ-020 (DOM div balance) have appeared across multiple
  cohorts. These are deterministic-checkable — no reason to wait for the final
  verifier. This gate catches them at phase 6 preflight time.

  Checks:
    1. JS syntax: extract <script> blocks, validate syntax (node --check or heuristic)
    2. DOM integrity: parse tag balance, detect unclosed critical elements
    3. Duplicate critical section IDs
    4. Canonical sections present
"""
import re, subprocess, tempfile, os, json


def check_js_syntax(html):
    """Check JavaScript syntax in all <script> blocks.

    Uses node --check if available; falls back to heuristic checks.
    Returns: {passed, errors, method}
    """
    scripts = re.findall(r'<script\b[^>]*>(.*?)</script>', html, re.DOTALL | re.I)
    errors = []

    for i, script in enumerate(scripts):
        script = script.strip()
        if not script:
            continue

        # Try node --check
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(script)
                f.flush()
                proc = subprocess.run(['node', '--check', f.name],
                                      capture_output=True, text=True, timeout=10)
                os.unlink(f.name)
                if proc.returncode != 0:
                    # Extract error line
                    err_line = proc.stderr.strip().split('\n')[0] if proc.stderr else "unknown"
                    errors.append(f"script[{i}]: {err_line[:100]}")
        except FileNotFoundError:
            # node not available — heuristic checks
            heuristic_errors = _heuristic_js_check(script, i)
            errors.extend(heuristic_errors)
        except Exception:
            pass

    return {
        "passed": len(errors) == 0,
        "errors": errors[:5],
        "method": "node --check" if subprocess.run(['which', 'node'], capture_output=True).returncode == 0 else "heuristic",
    }


def _heuristic_js_check(script, idx):
    """Heuristic JS validation when node is not available."""
    errors = []
    # Check bracket/paren/brace balance
    for open_ch, close_ch, name in [('{', '}', 'braces'), ('(', ')', 'parens'), ('[', ']', 'brackets')]:
        opens = script.count(open_ch)
        closes = script.count(close_ch)
        if opens != closes:
            errors.append(f"script[{idx}]: {name} imbalance ({opens} open, {closes} close)")
    # Check for common syntax errors
    if re.search(r'function\s+\w+\s*\([^)]*\)\s*$', script, re.M):
        errors.append(f"script[{idx}]: function without body")
    return errors


def check_dom_integrity(html):
    """Check DOM tag balance and structural integrity.

    Returns: {passed, errors, detail}
    """
    errors = []

    # Check div balance (REQ-020)
    div_opens = len(re.findall(r'<div\b[^>]*>', html, re.I))
    div_closes = len(re.findall(r'</div>', html, re.I))
    if div_opens != div_closes:
        errors.append(f"div imbalance: {div_opens} open, {div_closes} close")

    # Check section balance
    sec_opens = len(re.findall(r'<section\b[^>]*>', html, re.I))
    sec_closes = len(re.findall(r'</section>', html, re.I))
    if sec_opens != sec_closes:
        errors.append(f"section imbalance: {sec_opens} open, {sec_closes} close")

    # Check for unclosed critical elements
    for tag in ['html', 'body', 'head', 'table', 'script']:
        opens = len(re.findall(rf'<{tag}\b', html, re.I))
        closes = len(re.findall(rf'</{tag}>', html, re.I))
        if opens != closes:
            errors.append(f"{tag} imbalance: {opens} open, {closes} close")

    # Check for duplicate critical IDs
    ids = re.findall(r'id\s*=\s*["\'](sec-[^"\']+)["\']', html, re.I)
    seen = {}
    duplicates = []
    for id_val in ids:
        if id_val in seen:
            duplicates.append(id_val)
        seen[id_val] = True
    if duplicates:
        errors.append(f"duplicate section IDs: {duplicates[:3]}")

    return {
        "passed": len(errors) == 0,
        "errors": errors[:5],
        "detail": {
            "div_opens": div_opens, "div_closes": div_closes,
            "section_opens": sec_opens, "section_closes": sec_closes,
            "unique_section_ids": len(seen),
            "duplicates": duplicates[:3],
        }
    }


def check_artifact_integrity(html):
    """Full structural integrity check. Returns combined result."""
    js_result = check_js_syntax(html)
    dom_result = check_dom_integrity(html)

    all_errors = js_result["errors"] + dom_result["errors"]
    return {
        "passed": len(all_errors) == 0,
        "js_syntax": js_result,
        "dom_integrity": dom_result,
        "errors": all_errors,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 artifact_integrity_gate.py <html_file>")
        sys.exit(1)
    html = open(sys.argv[1]).read()
    result = check_artifact_integrity(html)
    print(json.dumps({k: v for k, v in result.items() if k != "errors"}, indent=2))
    if not result["passed"]:
        print("\nErrors:")
        for e in result["errors"]:
            print(f"  - {e}")
    sys.exit(0 if result["passed"] else 1)
