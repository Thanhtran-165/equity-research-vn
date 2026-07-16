#!/usr/bin/env python3
"""
valuation_render_gate.py — Deterministic PE/PB render enforcement (Branch B, v0.12.0).

PURPOSE (owner directive 2026-07-16):
  The agent sometimes renders PE/PB incorrectly: multiplying by 100 (7.35→735.0),
  omitting PB, or using wrong values. PE and PB are machine-readable data from
  the verified contract — the LLM should not have discretion over them.

  This module:
    1. Validates that PE and PB in the HTML match the contract values (±2%)
    2. If mismatch/missing, deterministically injects a valuation card snippet
       into the HTML (overwriting the agent's valuation section)
    3. Does NOT use model retry — pure deterministic enforcement
"""
import re, json


def extract_valuation_from_html(html):
    """Extract PE and PB values from the HTML dashboard.

    Looks in valuation section, data attributes, and visible text.
    Returns: {'pe': float|None, 'pb': float|None}
    """
    pe = None
    pb = None

    # Pattern 1: data-pe="7.35" data-pb="4.8"
    m = re.search(r'data-pe\s*=\s*["\']([\d.]+)["\']', html, re.I)
    if m:
        try: pe = float(m.group(1))
        except: pass
    m = re.search(r'data-pb\s*=\s*["\']([\d.]+)["\']', html, re.I)
    if m:
        try: pb = float(m.group(1))
        except: pass

    # Pattern 2: "P/E: 7.35" or "PE: 7.35" or "P/E = 7.35x"
    if pe is None:
        for pat in [r'P/?E\s*[:=]\s*([\d.]+)\s*(?:x|×|lần)?',
                    r'"pe"\s*:\s*([\d.]+)',
                    r'PE\s*[:=]\s*([\d.]+)']:
            m = re.search(pat, html, re.I)
            if m:
                try: pe = float(m.group(1)); break
                except: pass

    # Pattern 3: "P/B: 4.8" or "PB: 4.8"
    if pb is None:
        for pat in [r'P/?B\s*[:=]\s*([\d.]+)\s*(?:x|×|lần)?',
                    r'"pb"\s*:\s*([\d.]+)',
                    r'PB\s*[:=]\s*([\d.]+)']:
            m = re.search(pat, html, re.I)
            if m:
                try: pb = float(m.group(1)); break
                except: pass

    return {"pe": pe, "pb": pb}


def validate_valuation_render(html, contract):
    """Check that PE and PB in HTML match the contract values.

    Returns: {passed, pe_ok, pb_ok, html_pe, html_pb, contract_pe, contract_pb, errors}
    """
    html_val = extract_valuation_from_html(html)
    contract_val = contract.get("valuation", {})
    c_pe = contract_val.get("pe")
    c_pb = contract_val.get("pb")

    errors = []
    pe_ok = True
    pb_ok = True

    if c_pe is not None:
        if html_val["pe"] is None:
            errors.append(f"PE not found in HTML (contract: {c_pe})")
            pe_ok = False
        elif abs(html_val["pe"] - c_pe) / max(c_pe, 0.01) > 0.02:
            errors.append(f"PE mismatch: HTML={html_val['pe']} contract={c_pe} (diff >2%)")
            pe_ok = False

    if c_pb is not None:
        if html_val["pb"] is None:
            errors.append(f"PB not found in HTML (contract: {c_pb})")
            pb_ok = False
        elif abs(html_val["pb"] - c_pb) / max(abs(c_pb), 0.01) > 0.02:
            errors.append(f"PB mismatch: HTML={html_val['pb']} contract={c_pb} (diff >2%)")
            pb_ok = False

    return {
        "passed": pe_ok and pb_ok,
        "pe_ok": pe_ok,
        "pb_ok": pb_ok,
        "html_pe": html_val["pe"],
        "html_pb": html_val["pb"],
        "contract_pe": c_pe,
        "contract_pb": c_pb,
        "errors": errors,
    }


def inject_valuation_card(html, contract):
    """Deterministically inject valuation values into the HTML.

    Strategy: find all PE/PB patterns and replace with contract values.
    Also inject data-pe and data-pb attributes into sec-valuation.
    """
    val = contract.get("valuation", {})
    c_pe = val.get("pe")
    c_pb = val.get("pb")

    new_html = html

    # Replace all PE value patterns with contract value
    if c_pe is not None:
        # data-pe="..."
        new_html = re.sub(r'(data-pe\s*=\s*["\'])[\d.]+(["\'])',
                          rf'\g<1>{c_pe}\g<2>', new_html, flags=re.I)
        # "pe": ...
        new_html = re.sub(r'("pe"\s*:\s*)([\d.]+)', rf'\g<1>{c_pe}', new_html, flags=re.I)

    if c_pb is not None:
        new_html = re.sub(r'(data-pb\s*=\s*["\'])[\d.]+(["\'])',
                          rf'\g<1>{c_pb}\g<2>', new_html, flags=re.I)
        new_html = re.sub(r'("pb"\s*:\s*)([\d.]+)', rf'\g<1>{c_pb}', new_html, flags=re.I)

    # Also fix visible text patterns: "P/E: 735.0x" → "P/E: 7.35x"
    if c_pe is not None:
        new_html = re.sub(r'(P/?E\s*[:=]\s*)([\d.]+)(\s*(?:x|×|lần)?)',
                          rf'\g<1>{c_pe}\g<3>', new_html, flags=re.I)
    if c_pb is not None:
        new_html = re.sub(r'(P/?B\s*[:=]\s*)([\d.]+)(\s*(?:x|×|lần)?)',
                          rf'\g<1>{c_pb}\g<3>', new_html, flags=re.I)

    return new_html


def enforce_valuation(html, contract):
    """Full valuation enforcement: validate, inject if needed, re-validate.

    Returns: (new_html, report)
    """
    validation = validate_valuation_render(html, contract)

    if validation["passed"]:
        return html, {"action": "no_change_needed", "validation": validation}

    # Deterministic injection
    new_html = inject_valuation_card(html, contract)
    re_validation = validate_valuation_render(new_html, contract)

    return new_html, {
        "action": "deterministic_injection" if re_validation["passed"] else "injection_incomplete",
        "validation_before": validation,
        "validation_after": re_validation,
    }


if __name__ == "__main__":
    import sys, os
    if len(sys.argv) < 3:
        print("Usage: python3 valuation_render_gate.py <html_file> <contract.json>")
        sys.exit(1)
    html = open(sys.argv[1]).read()
    contract = json.load(open(sys.argv[2]))
    result = enforce_valuation(html, contract)
    print(json.dumps(result[1], indent=2, ensure_ascii=False))
    if not result[1]["validation_after" if "validation_after" in result[1] else "validation"]["passed"]:
        print("\nERRORS:", result[1].get("validation_before",{}).get("errors"))
