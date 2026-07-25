#!/usr/bin/env python3
"""
full_pipeline.py — Complete deterministic shell + section generation pipeline.

Architecture Phase C integration.
Orchestrates: IR build → section generation → narrative substitution → final HTML.
"""
import sys, os, json, re, html as html_module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.expanduser("~/.zcode/skills/equity-research-vn/incidents/v1.0.1-rc3/runner"))

from report_ir_builder import build_ir
from deterministic_renderer import render_html
from section_generator import generate_all_sections, insert_narratives_into_ir


def substitute_narratives(html_text, ir):
    """Replace {{NARRATIVE:section_id}} placeholders with actual narrative text."""
    for section in ir["sections"]:
        placeholder = "{{NARRATIVE:" + section["section_id"] + "}}"
        narrative = section.get("narrative", "").strip()
        if narrative:
            # Narrative already sanitized by section_generator
            html_text = html_text.replace(placeholder, narrative)
        elif section.get("applicability") == "NOT_APPLICABLE":
            html_text = html_text.replace(placeholder,
                '<div class="not-applicable">Không áp dụng</div>')
        else:
            # Deterministic sections (sources, glossary, etc.) — render basic content
            html_text = html_text.replace(placeholder,
                f'<p>Nội dung cho section "{section["title"]}" sẽ được điền.</p>')
    return html_text


def run_pipeline(source_pack_dir, call_model_fn=None, parallel_sections=True):
    """Execute the complete pipeline: source → IR → sections → render → final HTML.

    Args:
        source_pack_dir: Path to source pack
        call_model_fn: callable(prompt, phase_id) → {"output": str, "inference_occurred": bool}
                       If None, uses stub narratives (for testing)
        parallel_sections: if True, generate sections in parallel

    Returns:
        {"ir": dict, "html": str, "sections": dict, "html_size": int}
    """
    # Step 1: Build IR
    ir = build_ir(source_pack_dir)
    if "error" in ir:
        return ir

    # Step 2: Generate section narratives
    results = generate_all_sections(ir, call_model_fn=call_model_fn, parallel=parallel_sections)

    # Step 3: Insert narratives into IR
    ir = insert_narratives_into_ir(ir, results)

    # Step 4: Render deterministic HTML shell
    html = render_html(ir)

    # Step 5: Substitute narrative placeholders
    html = substitute_narratives(html, ir)

    # Verify no remaining placeholders
    remaining = re.findall(r'\{\{NARRATIVE:\w+\}\}', html)
    if remaining:
        print(f"WARNING: {len(remaining)} placeholders unresolved: {remaining[:3]}")

    return {
        "ir": ir,
        "html": html,
        "html_size": len(html),
        "sections": results,
        "remaining_placeholders": len(remaining),
    }


if __name__ == "__main__":
    import sys
    ticker_pack = sys.argv[1] if len(sys.argv) > 1 else \
        "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/FPT"

    # Stub model for testing (no real API call)
    def stub_model(prompt, phase_id):
        if "insight" in phase_id:
            text = "Phân tích sâu sắc về cơ hội đầu tư và rủi ro. " * 25
        else:
            text = "Đây là phân tích chuyên sâu cho section. " * 10
        return {"output": text, "inference_occurred": True}

    result = run_pipeline(ticker_pack, call_model_fn=stub_model)
    print(f"\nHTML size: {result['html_size']} bytes")
    print(f"Sections: pass={result['sections']['n_pass']}, fail={result['sections']['n_fail']}")
    print(f"Remaining placeholders: {result['remaining_placeholders']}")

    # Div balance check
    div_open = len(re.findall(r'<div\b', result["html"], re.I))
    div_close = len(re.findall(r'</div>', result["html"], re.I))
    print(f"Div balance: {div_open}/{div_close}")

    # Chart count
    charts = len(re.findall(r'new\s+Chart', result["html"]))
    print(f"Chart() calls: {charts}")

    # DATA block
    has_data = "const DATA" in result["html"]
    print(f"DATA block: {has_data}")

    # Narrative content
    has_narrative = "phân tích" in result["html"].lower()
    print(f"Narrative inserted: {has_narrative}")
