#!/usr/bin/env python3
"""
section_generator.py — Section-level model generation pipeline.

Architecture Phase C.
Model writes narrative ONLY (no HTML, no DATA, no charts).
Pipeline: prepare deterministic facts → call model → sanitize → validate → insert into IR.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from narrative_sanitizer import sanitize, validate_narrative

# Section prompt templates — model receives structured facts + writes narrative only
SECTION_PROMPTS = {
    "executive_summary": {
        "task": "Viết tóm tắt điều hành 200-400 từ cho báo cáo phân tích cổ phiếu. Bao gồm: luận điểm đầu tư chính, rủi ro lớn nhất, catalyst gần nhất. KHÔNG lặp lại số liệu đã có trong bảng.",
        "min_chars": 200,
        "max_chars": 800,
    },
    "company_profile": {
        "task": "Mô tả hoạt động kinh doanh chính, sản phẩm/dịch vụ cốt lõi, vị thế thị trường. 200-400 từ.",
        "min_chars": 200,
        "max_chars": 600,
    },
    "industry_overview": {
        "task": "Phân tích bối cảnh ngành: quy mô, tốc độ tăng trưởng, cạnh tranh, xu hướng. 200-400 từ.",
        "min_chars": 200,
        "max_chars": 600,
    },
    "thesis": {
        "task": "Trình bày luận điểm Bull (3 điểm tích cực) và Bear (3 điểm tiêu cực). Phải cân bằng. 300-500 từ.",
        "min_chars": 300,
        "max_chars": 800,
        "must_have_both_sides": True,
    },
    "valuation": {
        "task": "Đánh giá PE/PB so với trung bình ngành và lịch sử. Nhận định đắt/rẻ/hợp lý. 150-300 từ.",
        "min_chars": 150,
        "max_chars": 500,
    },
    "balance_sheet": {
        "task": "Phân tích cấu trúc tài sản, đòn bẩy, chất lượng bảng cân đối. 150-300 từ.",
        "min_chars": 150,
        "max_chars": 500,
    },
    "risk": {
        "task": "Nêu 3-5 rủi ro chính (kinh doanh, tài chính, thị trường, pháp lý). Mỗi rủi ro 50-100 từ.",
        "min_chars": 300,
        "max_chars": 800,
    },
    "insight_1": {
        "task": "Cung cấp 1 insight đặc biệt về cổ phiếu này — điều mà nhà đầu tư bình thường có thể bỏ qua. ≥500 từ với phân tích sâu.",
        "min_chars": 500,
        "max_chars": 1200,
    },
    "insight_2": {
        "task": "Insight #2 — góc nhìn khác biệt về динамика kinh doanh hoặc tài chính. ≥500 từ.",
        "min_chars": 500,
        "max_chars": 1200,
    },
    "insight_3": {
        "task": "Insight #3 — phân tích kịch bản hoặc so sánh peer sâu sắc. ≥500 từ.",
        "min_chars": 500,
        "max_chars": 1200,
    },
    "analyst_notes": {
        "task": "Ghi chú phân tích bổ sung: điểm đáng chú ý, câu hỏi cho management, theo dõi gì trong quý tới. 200-400 từ.",
        "min_chars": 200,
        "max_chars": 600,
    },
    "tech_active": {
        "task": "Diễn giải Tech Score, xu hướng ngắn hạn, tín hiệu MA/RSI/MACD. 150-250 từ.",
        "min_chars": 150,
        "max_chars": 400,
    },
}


def build_section_prompt(section_id, ir):
    """Build the model prompt for one section.

    Returns: (prompt_string, config_dict)
    """
    spec = SECTION_PROMPTS.get(section_id, {"task": f"Viết nội dung cho section '{section_id}'.",
                                             "min_chars": 150, "max_chars": 500})
    ticker = ir["metadata"]["ticker"]
    company = ir["metadata"]["company_name"]
    sector = ir["metadata"]["sector"]
    metrics = ir["financial_data"]["metrics"]

    # Build deterministic facts string (read-only context for model)
    facts_lines = [f"Ticker: {ticker}", f"Company: {company}", f"Sector: {sector}"]
    for field in ["revenue", "net_profit", "eps", "total_assets", "total_equity", "capex"]:
        m = metrics.get(field, {})
        status = m.get("status", "VALID")
        if status == "NOT_APPLICABLE":
            facts_lines.append(f"{field}: NOT_APPLICABLE ({m.get('applicability_rule','')})")
        else:
            vals = m.get("values", {})
            latest = list(vals.values())[-1] if vals else None
            facts_lines.append(f"{field}: latest={latest}")

    valuation = ir.get("derived_metrics", {}).get("valuation", {})
    facts_lines.append(f"PE: {valuation.get('pe')}, PB: {valuation.get('pb')}")

    facts = "\n".join(facts_lines)

    prompt = f"""You are an equity research analyst writing in Vietnamese.

SECTION: {section_id}
COMPANY: {company} ({ticker})
SECTOR: {sector}

DETERMINISTIC FACTS (read-only, do not repeat these numbers verbatim — interpret them):
{facts}

TASK: {spec['task']}

RULES:
- Write ONLY narrative text (no HTML, no JavaScript, no tables)
- Write in Vietnamese
- Do NOT include any financial arrays, DATA blocks, or code
- Do NOT repeat numbers from the facts above — interpret trends and meaning
- Length: {spec['min_chars']}-{spec['max_chars']} characters
- Start directly with your analysis (no preamble like "I'll write..." or "Here is...")

Write your analysis:"""

    return prompt, spec


def generate_section(section_id, ir, model_backend="zai", model_id="GLM-5.2",
                     call_model_fn=None):
    """Generate one section's narrative via model.

    Args:
        section_id: which section to generate
        ir: report IR dict
        call_model_fn: callable(prompt, phase_id) → {"output": str, "inference_occurred": bool}

    Returns:
        {"section_id": str, "status": "PASS"|"FAIL"|"RETRY_EXHAUSTED"|"SKIPPED",
         "narrative": str, "narrative_safe": str, "warnings": list, "attempts": int}
    """
    # Check applicability
    section = next((s for s in ir["sections"] if s["section_id"] == section_id), None)
    if not section:
        return {"section_id": section_id, "status": "FAIL", "error": "section_not_in_ir"}

    if section["applicability"] == "NOT_APPLICABLE":
        return {"section_id": section_id, "status": "SKIPPED",
                "narrative": "", "narrative_safe": "", "warnings": ["NOT_APPLICABLE"]}

    if section_id not in SECTION_PROMPTS:
        # Sections without specific prompts (sources, glossary, etc.) — deterministic, skip model
        return {"section_id": section_id, "status": "SKIPPED",
                "narrative": "", "narrative_safe": "", "warnings": ["no_prompt_needed"]}

    prompt, spec = build_section_prompt(section_id, ir)
    min_chars = spec.get("min_chars", 200)

    max_attempts = 2  # 1 initial + 1 retry
    for attempt in range(1, max_attempts + 1):
        # Call model
        if call_model_fn:
            result = call_model_fn(prompt, f"section_{section_id}_attempt{attempt}")
        else:
            # Stub for Phase C testing without model
            result = {"output": f"[STUB] Phân tích {section_id} cho {ir['metadata']['ticker']}. "
                      "Đây là nội dung narrative thay thế cho test. " * 5, "inference_occurred": True}

        if not result.get("inference_occurred") or not result.get("output"):
            continue

        raw_narrative = result["output"].strip()

        # Sanitize
        san = sanitize(raw_narrative)
        if san["blocked"]:
            if attempt < max_attempts:
                prompt += f"\n\nLỖI: Nội dung trước đó bị chặn vì: {san['warnings']}. Hãy viết lại không sử dụng HTML/JavaScript."
                continue
            return {"section_id": section_id, "status": "RETRY_EXHAUSTED",
                    "narrative": raw_narrative, "narrative_safe": "",
                    "warnings": san["warnings"], "attempts": attempt}

        # Validate
        passed, evidence = validate_narrative(san["safe_text"], section_id, min_chars=min_chars)
        if passed:
            return {"section_id": section_id, "status": "PASS",
                    "narrative": raw_narrative, "narrative_safe": san["safe_text"],
                    "warnings": san["warnings"], "attempts": attempt,
                    "char_count": evidence.get("chars")}

        if attempt < max_attempts:
            prompt += f"\n\nNội dung trước đó quá ngắn ({evidence.get('chars',0)} ký tự, cần ≥{min_chars}). Hãy viết chi tiết hơn."
            continue

        return {"section_id": section_id, "status": "RETRY_EXHAUSTED",
                "narrative": raw_narrative, "narrative_safe": san["safe_text"],
                "warnings": [f"validation_fail: {evidence}"], "attempts": attempt}

    return {"section_id": section_id, "status": "FAIL",
            "narrative": "", "narrative_safe": "", "warnings": ["no_model_output"], "attempts": max_attempts}


def generate_all_sections(ir, model_backend="zai", model_id="GLM-5.2",
                          call_model_fn=None, parallel=False):
    """Generate narratives for all applicable sections.

    Args:
        ir: report IR dict
        call_model_fn: callable for model calls
        parallel: if True, use ThreadPoolExecutor for section generation

    Returns:
        {"results": [...], "n_pass": int, "n_fail": int, "n_skip": int}
    """
    applicable_sections = [s["section_id"] for s in ir["sections"]
                           if s["applicability"] == "APPLICABLE" and s["section_id"] in SECTION_PROMPTS]

    results = []
    if parallel:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(generate_section, sid, ir, model_backend, model_id, call_model_fn): sid
                       for sid in applicable_sections}
            for future in futures:
                sid = futures[future]
                try:
                    results.append(future.result())
                except Exception as e:
                    results.append({"section_id": sid, "status": "FAIL", "error": str(e)[:100]})
    else:
        for sid in applicable_sections:
            results.append(generate_section(sid, ir, model_backend, model_id, call_model_fn))

    n_pass = sum(1 for r in results if r["status"] == "PASS")
    n_fail = sum(1 for r in results if r["status"] in ("FAIL", "RETRY_EXHAUSTED"))
    n_skip = sum(1 for r in results if r["status"] == "SKIPPED")

    return {"results": results, "n_pass": n_pass, "n_fail": n_fail, "n_skip": n_skip,
            "total_applicable": len(applicable_sections)}


def insert_narratives_into_ir(ir, generation_results):
    """Insert generated narratives into IR sections (mutates ir in-place)."""
    for r in generation_results["results"]:
        for section in ir["sections"]:
            if section["section_id"] == r["section_id"]:
                section["narrative"] = r.get("narrative_safe", "")
                section["validation_status"] = r["status"]
                section["warnings"] = r.get("warnings", [])
                break
    return ir


if __name__ == "__main__":
    # Test with stub (no model call)
    sys.path.insert(0, "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-rc3/runner")
    from report_ir_builder import build_ir

    ir = build_ir("/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/FPT")
    results = generate_all_sections(ir, call_model_fn=None)  # stub mode
    print(f"Sections: pass={results['n_pass']}, fail={results['n_fail']}, skip={results['n_skip']}")
    for r in results["results"]:
        mark = "✓" if r["status"] == "PASS" else "✗" if r["status"] in ("FAIL","RETRY_EXHAUSTED") else "→"
        chars = r.get("char_count", "-")
        print(f"  [{mark}] {r['section_id']:20s} status={r['status']:16s} chars={chars}")
