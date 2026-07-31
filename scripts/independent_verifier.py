#!/usr/bin/env python3
"""
independent_verifier.py — Independent Verifier (Lớp 3 + 4 anti-omission harness)

Lớp 3 (Evidence ledger): mỗi REQ gắn file evidence JSON với byproduct.
Lớp 4 (Independent verifier): đọc requirements.yaml (KHÔNG đọc SKILL.md prose),
tự chạy verification command, ghi evidence, output pass/fail.

KHÁC BIỆT VỚI enforce_spec.sh (cũ):
  - enforce_spec.sh = hardcode checks trong bash → agent có thể sửa
  - independent_verifier.py = đọc requirements.yaml (data-driven) → thêm/sửa REQ không cần code
  - Verifier KHÔNG tin agent claim → tự chạy command + kiểm artifact

Usage:
  python3 independent_verifier.py MSN /path/to/report.html
  → output: evidence/*.json + verdict (PASS/FAIL + requirement recall)

Exit code: 0 = all pass, 1 = any fail
"""
import json, sys, os, re, subprocess, yaml, datetime, hashlib

TICKER = sys.argv[1] if len(sys.argv) > 1 else "UNKNOWN"
REPORT = sys.argv[2] if len(sys.argv) > 2 else None
SKILL_DIR = os.path.expanduser("~/.zcode/skills/equity-research-vn")
REQ_FILE = os.path.join(SKILL_DIR, "requirements.yaml")

# Colors
RED = "\033[0;31m"; GREEN = "\033[0;32m"; YELLOW = "\033[1;33m"; NC = "\033[0m"

def read_report():
    if not REPORT or not os.path.exists(REPORT):
        return None
    with open(REPORT) as f:
        return f.read()

def extract_section_text(html, section_id):
    """Extract innerText of a section."""
    if not html:
        return ""
    # Find section block
    pattern = rf'<section[^>]*id="{section_id}"[^>]*>(.*?)</section>'
    m = re.search(pattern, html, re.DOTALL)
    if not m:
        return ""
    inner = m.group(1)
    # Strip tags
    text = re.sub(r"<[^>]+>", " ", inner)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_all_text(html):
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()

def _narrative_text(html):
    """Text thuần của narrative — strip <style>/<script> từ HTML GỐC trước khi
    extract tags (extract_all_text giữ nội dung script vì chỉ thay tags bằng space)."""
    if not html:
        return ""
    cleaned = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL)
    cleaned = re.sub(r"<script[^>]*>.*?</script>", " ", cleaned, flags=re.DOTALL)
    return extract_all_text(cleaned)

# ═══════════════════════════════════════════════════════════════
# VERIFICATION METHODS (data-driven from requirements.yaml)
# ═══════════════════════════════════════════════════════════════

def verify_non_advice_check(req, html):
    """REQ-007: Check tech-profile section for actionable investment advice.
    P4 FIX: negation-aware. Removes valid disclaimers before checking.
    P5 FIX (v0.1.5): entity-interruption-tolerant disclaimer matching.
      Problem: "không khuyến nghị mua/bán VCB" was flagged because the old
      pattern required "không phải khuyến nghị mua/bán" (exact "phải" + no entity
      after "bán"). Ticker/company names between disclaimer words broke matching.
      Fix: use grammar-level rules that allow entity tokens between negation
      and the advice keyword, while still FAILing real advice.
    STRONG BUY/STRONG SELL as Tech Score verdict is allowed (machine-readable, not advice)."""
    if not html:
        return False, {"error": "no html"}
    # Extract sec-tech-profile section text
    sec_text = extract_section_text(html, "sec-tech-profile")
    if not sec_text:
        return True, {"section_found": False, "note": "no sec-tech-profile section — vacuously PASS"}

    # Step 1: Remove valid disclaimer sentences (negation context)
    # P5: Entity-interruption-tolerant patterns.
    # Key insight: a disclaimer has the STRUCTURE "không [entity] khuyến nghị [entity] mua [entity] bán"
    # where [entity] can be ticker names, company names, or connective words.
    # We use .{0,40}? to allow up to 40 chars of interruption between key tokens.
    disclaimer_patterns = [
        # "không [phải] [entity] khuyến nghị mua [/entity] bán [entity]"
        # Handles: "không khuyến nghị mua/bán VCB", "không phải khuyến nghị mua/bán",
        #          "không phải là khuyến nghị mua bán VCB"
        r"không\s+(?:phải\s+(?:là\s+)?)?(?:[A-Z]{2,5}\s+)?khuyến\s+nghị\s+mua[/\s]*bán",
        # "không [entity] khuyến nghị mua" (standalone negation, no "bán" needed)
        r"không\s+(?:phải\s+(?:là\s+)?)?(?:[A-Z]{2,5}\s+)?khuyến\s+nghị\s+mua(?!\s*[/\s]*bán)",
        # "không [entity] khuyến nghị bán" (standalone negation)
        r"không\s+(?:phải\s+(?:là\s+)?)?(?:[A-Z]{2,5}\s+)?khuyến\s+nghị\s+bán",
        # "không cấu thành [entity] khuyến nghị đầu tư"
        r"không\s+cấu\s+thành\s+(?:[A-Z]{2,5}\s+)?(?:khuyến\s+nghị\s+đầu\s+tư|lời\s+khuyên\s+đầu\s+tư)",
        # "không [phải] [entity] lời khuyên tài chính"
        r"không\s+(?:phải\s+)?(?:[A-Z]{2,5}\s+)?lời\s+khuyên\s+tài\s+chính",
        # "không nên được hiểu/xem là [entity] khuyến nghị"
        r"không\s+nên\s+được\s+(?:hiểu|xem)\s+(?:là|như)\s+(?:[A-Z]{2,5}\s+)?khuyến\s+nghị",
        # "chỉ mang tính tham khảo [entity] không phải"
        r"chỉ\s+mang\s+tính\s+tham\s+khảo[^.]*?không\s+phải",
        # "không [entity] khuyến nghị mua/bán" — broader: negation anywhere before "khuyến nghị mua/bán"
        # within same sentence (handles "thông tin về VCB không phải là khuyến nghị mua/bán")
        r"(?:đây|nội\s+dung|thông\s+tin|đánh\s+giá|báo\s+cáo)[^.]{0,30}?không\s+(?:phải\s+(?:là\s+)?)?khuyến\s+nghị\s+mua[/\s]*bán",
        # English
        r"not\s+(?:investment\s+)?advice",
        r"for\s+educational\s+purposes\s+only",
    ]
    cleaned_text = sec_text
    disclaimers_removed = []
    for pat in disclaimer_patterns:
        matches = re.findall(pat, cleaned_text, re.I)
        if matches:
            disclaimers_removed.extend(matches)
            cleaned_text = re.sub(pat, "", cleaned_text, flags=re.I)

    # Step 1b: Also remove full sentences containing "không" + "khuyến nghị" within 60 chars
    # This catches cases like "VCB không phải khuyến nghị mua" where VCB precedes the negation.
    # CRITICAL: a sentence is ONLY removed as a disclaimer if it has NO actionable advice.
    # "không phải khuyến nghị chung, nhưng có thể mua VCB" = disclaimer + real advice → KEEP (FAIL).
    sentences = re.split(r'([.!?]\s+)', cleaned_text)
    rebuilt = []
    for i, s in enumerate(sentences):
        if i % 2 == 0:  # actual sentence (odd indices are delimiters)
            has_negation = bool(re.search(r"không\s|không$", s, re.I))
            has_advice_word = bool(re.search(r"khuyến\s+nghị|lời\s+khuyên|đầu\s+tư|advice", s, re.I))
            # Actionable = real advice signal that must FAIL even in a negation sentence
            has_actionable = bool(re.search(
                r"nên\s+mua|nên\s+bán|điểm\s+mua|điểm\s+bán|chốt\s+lời|cắt\s+lỗ|giải\s+ngân|"
                r"nhà\s+đầu\s+tư\s+nên|có\s+thể\s+mua|có\s+thể\s+bán|"
                r"khuyến\s+nghị\s+mua(?!\s*[/\s]*bán)|khuyến\s+nghị\s+bán",
                s, re.I))
            # Also check for "nhưng" (but) introducing actionable advice after a disclaimer
            has_but_clause = bool(re.search(r"nhưng[^.]{0,40}(?:mua|bán|nên|giải\s+ngân)", s, re.I))
            if has_negation and has_advice_word and not has_actionable and not has_but_clause:
                disclaimers_removed.append(s.strip()[:80])
                rebuilt.append("")  # remove this sentence
            else:
                rebuilt.append(s)
        else:
            rebuilt.append(s)
    cleaned_text = "".join(rebuilt)

    # Step 2: Allow STRONG BUY/STRONG SELL when used as Tech Score verdict (machine-readable)
    verdict_patterns = [
        r"(?:tech\s*score|verdict|kết\s+luận)\s*[:\s-]*\s*(?:STRONG\s+(?:BUY|SELL)|BUY|SELL|NEUTRAL)",
        r'data-verdict="(?:STRONG\s+(?:BUY|SELL)|BUY|SELL|NEUTRAL)"',
        r"(?:STRONG\s+(?:BUY|SELL)|BUY|SELL|NEUTRAL)\s*[×x]?\s*(?:/6|trên\s+6\s+tín\s+hiệu)",
    ]
    for pat in verdict_patterns:
        cleaned_text = re.sub(pat, "[VERDICT_LABEL]", cleaned_text, flags=re.I)

    # Step 3: Check remaining text for actionable advice signals
    # P5b: distinguish "nhà đầu tư nên mua" (actionable) from "nhà đầu tư nên tự đánh giá" (disclaimer)
    advice_signals = [
        r"nên\s+mua", r"nên\s+bán", r"khuyến\s+nghị\s+mua", r"khuyến\s+nghị\s+bán",
        r"nhà\s+đầu\s+tư\s+nên\s+(?!tự\s+đánh\s+giá|tham\s+vấn|cân\s+nhắc|hạn\s+chế)",  # NOT "nên tự đánh giá/tham vấn"
        r"điểm\s+mua", r"điểm\s+bán",
        r"chốt\s+lời", r"cắt\s+lỗ(?!\s+(?:cá\s+nhân|kỷ\s+luật|khẩu\s+vị))", r"giải\s+ngân",
        r"có\s+thể\s+mua", r"có\s+thể\s+bán",
        r"bullish.{0,30}(?:mua|buy|nên)", r"bearish.{0,30}(?:bán|sell|nên)",
    ]
    violations = []
    for pat in advice_signals:
        for m in re.finditer(pat, cleaned_text, re.I):
            ctx = cleaned_text[max(0,m.start()-30):m.end()+30]
            # v0.14.9: Clause-level negation guard — check up to 60 chars before
            pre_context = cleaned_text[max(0,m.start()-60):m.start()].lower()
            # Direct negation: "không nên mua"
            if re.search(r"không\s+(?:phải\s+)?$", pre_context):
                continue
            # v0.14.9: Clause-level negation patterns (must NOT contain 'nhưng' which overrides)
            # Clause boundaries: . ! ? ; — stop negation scope
            if "nhưng" not in pre_context:
                # "không khuyến nghị ... mua/bán"
                if re.search(r"không\s+khuyến\s+nghị[^.!?;]{0,50}$", pre_context):
                    continue
                # "không phải lúc nào (cũng) nên mua/bán"
                if re.search(r"không\s+phải\s+lúc\s+nào[^.!?;]{0,30}$", pre_context):
                    continue
                # "không đưa ra / không có / không phải ... (thời) điểm mua/bán"
                if re.search(r"không\s+(?:đưa\s+ra|có|phải)[^.!?;]{0,40}$", pre_context):
                    continue
            violations.append({"pattern": pat[:30], "context": ctx.strip()[:80]})

    passed = len(violations) == 0
    return passed, {
        "section_length": len(sec_text),
        "disclaimers_removed": len(disclaimers_removed),
        "advice_violations": violations[:3],
        "patch_note": "P5: entity-interruption-tolerant disclaimers + sentence-level negation removal + final negation guard",
    }

def verify_command(req, html):
    """Run shell command, check exit code / output."""
    cmd = req["verification"]["command"]
    # If JS check, extract JS from HTML first
    if "$JS_FILE" in cmd and html:
        js_file = "/tmp/_verify_check.js"
        scripts = re.findall(r"<script>(.*?)</script>", html, re.DOTALL)
        with open(js_file, "w") as f:
            f.write("\n".join(s for s in scripts if "cdn.jsdelivr" not in s))
        cmd = cmd.replace("$JS_FILE", js_file)
    else:
        cmd = cmd.replace("$JS_FILE", "/dev/null")
    cmd = cmd.replace("$TICKER", TICKER).replace("$REPORT", REPORT or "")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout.strip()
        exit_code = result.returncode

        if "expect_exit" in req["verification"]:
            passed = exit_code == req["verification"]["expect_exit"]
            return passed, {"output": output[:200], "exit_code": exit_code, "command": cmd[:100]}

        if "expect_min" in req["verification"]:
            try:
                val = int(output)
                passed = val >= req["verification"]["expect_min"]
            except:
                passed = False
                val = None
            return passed, {"output": output, "value": val, "min_expected": req["verification"]["expect_min"]}

        if "expect_max" in req["verification"]:
            try:
                val = int(output)
                passed = val <= req["verification"]["expect_max"]
            except:
                passed = False
                val = None
            return passed, {"output": output, "value": val, "max_expected": req["verification"]["expect_max"]}
    except Exception as e:
        return False, {"error": str(e)}
    return False, {"error": "unknown verification"}


def verify_artifact_check(req, html):
    """Check artifact content for patterns."""
    check = req["verification"].get("check", "")
    text = extract_all_text(html) if html else ""

    if "split-adjusted" in check.lower() or "bẫy 5b" in check.lower():
        passed = any(w in text.lower() for w in ["split-adjusted", "bẫy 5b", "cross-check eps", "audit split"])
        return passed, {"found": passed}

    if "placeholder" in check.lower() or "oracle" in check.lower():
        # Check for Oracle placeholder data in VISIBLE TEXT (not JS/CSS/comments)
        # "oracle" in JS comments is OK; in visible body text = bad
        # Strip script/style blocks first
        body_text = re.sub(r"<script.*?</script>", "", html or "", flags=re.DOTALL)
        body_text = re.sub(r"<style.*?</style>", "", body_text, flags=re.DOTALL)
        body_text = re.sub(r"<!--.*?-->", "", body_text, flags=re.DOTALL)
        body_text = re.sub(r"<[^>]+>", " ", body_text)
        body_text = re.sub(r"\s+", " ", body_text).strip().lower()
        # P3 FIX: context-scoped Oracle detection. Standalone "oracle" (including Vietnamese
        # business term meaning "chủ đầu tư then chốt") must NOT trigger. Require specific
        # Oracle Corporation signals: company name, ticker, product names, or USD financials.
        oracle_corp_signals = [
            r"oracle\s+corporation",
            r"\bORCL\b",
            r"NYSE:?\s*ORCL",
            r"oracle\s+oci",
            r"oracle\s+cloud",
            r"oracle\s+database",
            r"oracle[^a-z]{0,20}(?:revenue|capex|earnings|billion|usd)",
            r"\$\s*billions.*oracle",
            r"usd\s*billions.*oracle",
        ]
        has_oracle = any(re.search(pat, body_text, re.I) for pat in oracle_corp_signals)
        passed = not has_oracle
        return passed, {"no_placeholder": passed, "has_oracle": has_oracle,
                        "patch_note": "P3: context-scoped — standalone 'oracle' no longer triggers"}

    if "non_advice" in check.lower() or "neutral_descriptive" in check.lower():
        return verify_non_advice_check(req, html)

    if "tech score" in check.lower() or "verdict" in check.lower():
        sec = extract_section_text(html, "sec-tech")
        passed = bool(re.search(r"-?[0-9]\s*/\s*6|STRONG (SELL|BUY)|SELL|BUY|NEUTRAL", sec))
        return passed, {"has_tech_score": passed, "section_length": len(sec)}

    if "sec-tech-profile" in check.lower() or "non-advice" in check.lower():
        sec = extract_section_text(html, "sec-tech-profile")
        passed = len(sec) > 100
        return passed, {"section_length": len(sec)}

    if "sentiment" in check.lower():
        passed = bool(re.search(r"sentiment|tích cực|tiêu cực|trung tính", text.lower()))
        return passed, {"has_sentiment": passed}

    if "callout" in check.lower() or "limitation" in check.lower() or "honest" in check.lower():
        passed = any(w in text.lower() for w in ["ước tính", "limitation", "stale", "honest", "data limitation"])
        return passed, {"has_honest_flag": passed}

    if "risk" in check.lower():
        sec = extract_section_text(html, "sec-risk")
        passed = len(sec) > 100
        return passed, {"risk_section_length": len(sec)}

    if "dương" in check.lower() or "valuation" in check.lower():
        prices = re.findall(r'class="price[^"]*"[^>]*>\s*([-\d,]+)', html or "")
        negative = [p for p in prices if p.startswith("-")]
        passed = len(negative) == 0
        return passed, {"negative_prices": negative[:3], "total_prices": len(prices)}

    if "split-adjusted" in check.lower():
        passed = any(w in text.lower() for w in ["split-adjusted", "bẫy 5b", "cross-check"])
        return passed, {"found": passed}

    return False, {"error": f"unknown check: {check[:60]}"}


def verify_section_map(req, html):
    """Check section ids match canonical."""
    canonical = req["verification"]["canonical_sections"]
    min_match = req["verification"]["min_canonical_match"]
    # PATCH P0-2: high-signal sections must each be present (count proxy alone was gameable).
    required_signal = req["verification"].get("required_signal_sections", [])
    found = 0
    found_ids = []
    missing_ids = []
    for sec_id in canonical:
        if html and f'id="{sec_id}"' in html:
            found += 1
            found_ids.append(sec_id)
        else:
            missing_ids.append(sec_id)
    missing_signal = [s for s in required_signal if not (html and f'id="{s}"' in html)]
    # PATCH P0-2: PASS requires BOTH count threshold AND every signal section present.
    passed = found >= min_match and len(missing_signal) == 0
    return passed, {"found": found, "total": len(canonical), "min_required": min_match,
                    "missing": missing_ids[:10],
                    "missing_signal_sections": missing_signal,
                    "patch_note": "P0-2: tightened min 15→20 + required_signal_sections each-present"}


def verify_count_check(req, html):
    """Count charts, sections, refs."""
    mins = req["verification"]
    charts = len(re.findall(r"new Chart|viz\.chart", html or "")) if html else 0
    sections = len(re.findall(r"<section", html or "")) if html else 0
    refs = len(re.findall(r'id="ref-\d+"', html or "")) if html else 0
    passed = (charts >= mins.get("min_charts", 0) and
              sections >= mins.get("min_sections", 0) and
              refs >= mins.get("min_refs", 0))
    return passed, {"charts": charts, "sections": sections, "refs": refs,
                    "min_charts": mins.get("min_charts"), "min_sections": mins.get("min_sections"),
                    "min_refs": mins.get("min_refs")}


def verify_content_depth(req, html):
    """Check each section has enough content."""
    min_chars = req["verification"]["min_chars_per_section"]
    exempt = req["verification"].get("exempt_sections", [])
    all_secs = re.findall(r'<section[^>]*id="(sec-[^"]+)"', html or "")
    shallow = []
    for sec_id in all_secs:
        if sec_id in exempt:
            continue
        text = extract_section_text(html, sec_id)
        if len(text) < min_chars:
            shallow.append({"section": sec_id, "chars": len(text)})
    passed = len(shallow) == 0
    return passed, {"min_chars": min_chars, "shallow_sections": shallow[:5], "total_checked": len(all_secs)}


def verify_section_content(req, html):
    """Check specific sections have content."""
    secs = req["verification"]["sections"]
    min_chars = req["verification"]["min_chars_each"]
    results = {}
    passed = True
    for sec_id in secs:
        text = extract_section_text(html, sec_id)
        ok = len(text) >= min_chars
        results[sec_id] = {"chars": len(text), "ok": ok}
        if not ok:
            passed = False
    return passed, results


def verify_canvas_check(req, html):
    """Check canvas elements have height-wrapper."""
    if not html:
        return False, {"error": "no html"}
    canvases = list(re.finditer(r"<canvas\s", html))
    bare = 0
    bare_ids = []
    for m in canvases:
        before = html[max(0, m.start() - 80):m.start()]
        if not any(p in before for p in ["chart-wrap", "tech-chart-wrap", "height:", "height="]):
            bare += 1
            # Try to find canvas id
            id_match = re.search(r'id="([^"]*)"', html[m.start():m.start()+100])
            bare_ids.append(id_match.group(1) if id_match else "unknown")
    passed = bare == 0
    return passed, {"bare_canvas_count": bare, "bare_canvas_ids": bare_ids, "total_canvas": len(canvases)}


def verify_valuation_sanity(req, html):
    """Check val-card prices positive + DCF negative flag."""
    prices = re.findall(r'class="price[^"]*"[^>]*>\s*([-\d,]+)', html or "")
    negative = [p for p in prices if p.startswith("-")]
    # Check if negative prices have explanation note
    text = extract_all_text(html) if html else ""
    has_fcF_note = any(w in text.lower() for w in ["fcf", "fcf âm", "fcf<0", "không hợp lệ", "ev/ebitda"])
    passed = len(negative) == 0 or (len(negative) > 0 and has_fcF_note)
    return passed, {"negative_prices": negative[:3], "total_prices": len(prices), "has_fcf_note": has_fcF_note}


def _context_anchored_match(text, anchor_label, gt_val, tolerance_pct, fallback_key=None, window=400):
    """PATCH P1-1 (REQ-022): find gt_val within ±tolerance ONLY in a context window around
    an anchor. Prevents a corrupted value being masked by a sibling value matching globally.

    Anchors (in priority order):
      1. the YEAR label (for per-year table cells where year is adjacent)
      2. the field key (revenue_ty, npatmi_ty) — internal data label
      3. business synonyms for the field key (revenue↔Doanh thu, npatmi↔LNST/lợi nhuận)
    A value matches only if it appears within `window` chars of SOME anchor — not anywhere.
    Handles US/VN number formats."""
    def parse_num(s):
        try:
            c = s.strip()
            if "." in c and "," in c: c = c.replace(",", "")
            elif "." in c and "," not in c:
                parts = c.split(".")
                if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]): c = c.replace(".", "")
            return float(c)
        except Exception:
            return None
    def within_tol(n):
        return n is not None and abs(n - gt_val) / max(abs(gt_val), 0.001) * 100 <= tolerance_pct
    # build anchor synonym map keyed by the field key
    synonyms = {
        "revenue_ty": ["revenue_ty", "Doanh thu", "Revenue", "Tổng doanh thu"],
        "npatmi_ty": ["npatmi_ty", "LNST", "lợi nhuận sau thuế", "Net profit", "Net income", "Net Profit"],
        "eps_vnd": ["eps_vnd", "EPS", "EPS adj", " Thu nhập trên mỗi cổ phiếu"],
        "Total Assets": ["Total Assets", "Tổng tài sản"],
        "Owner's Equity": ["Owner's Equity", "Vốn chủ sở hữu"],
    }
    anchor_terms = synonyms.get(fallback_key, []) or ([fallback_key] if fallback_key else [])
    if anchor_label:
        anchor_terms = anchor_terms + [anchor_label]
    anchor_terms = [t for t in anchor_terms if t]
    positions = []
    for term in anchor_terms:
        positions.extend(m.start() for m in re.finditer(re.escape(term), text, re.I))
    if not positions:
        positions = [0]
    for a in positions:
        seg = text[max(0, a-window):a+window]
        for num_str in re.findall(r'([\d.,]+)', seg):
            if within_tol(parse_num(num_str)):
                return True
    return False

def _extract_data_js_arrays(html):
    """PATCH P1-1 (REQ-022): pull structured arrays from the report's `const DATA = {...}` JS
    object. Returns {years, revenue, netProfit, eps, ...} as lists of floats/strings. Used for
    unambiguous per-year verification (eliminates sibling-value substitution)."""
    if not html:
        return {}
    out = {}
    for name in ["years", "revenue", "netProfit", "net_profit", "eps", "capex", "totalAssets", "equity", "ownersEquity"]:
        m = re.search(rf'{name}\s*:\s*\[([^\]]+)\]', html)
        if m:
            vals = []
            for tok in m.group(1).split(","):
                tok = tok.strip().strip("'\"")
                if not tok:
                    continue
                try:
                    vals.append(float(tok))
                except ValueError:
                    vals.append(tok)
            out[name] = vals
    return out

def verify_data_accuracy(req, html):
    """Verify report numbers match data files (ground truth). Anti-fabrication."""
    import json as _json
    work_dir = os.path.dirname(REPORT) if REPORT else "."
    data_path = os.path.join(work_dir, req["verification"]["data_file"])

    if not os.path.exists(data_path):
        return False, {"error": f"data file not found: {data_path}"}

    with open(data_path) as f:
        ground_truth = _json.load(f)

    text = extract_all_text(html) if html else ""
    # PATCH P1-1 (REQ-022): parse the structured DATA JS object for unambiguous per-year
    # verification. This eliminates sibling-value substitution (a corrupted year being masked
    # by another year's value matching in a shared context window).
    data_arrays = _extract_data_js_arrays(html)  # {years:[...], revenue:[...], netProfit:[...], eps:[...]}
    mismatches = []
    checked = 0

    for field in req["verification"].get("fields", []):
        key = field["key"]
        tolerance = field.get("tolerance_pct", 5)

        # Get ground truth value
        gt_val = ground_truth.get(key)
        if gt_val is None:
            continue

        # Map field key → DATA array name
        data_arr_map = {"revenue_ty": "revenue", "npatmi_ty": "netProfit", "eps_vnd": "eps",
                        "Total Assets": "totalAssets", "Owner's Equity": "equity"}

        # If dict (per-year), check each year
        if isinstance(gt_val, dict):
            years = field.get("years", list(gt_val.keys()))
            divisor = field.get("divisor", 1)
            data_arr_name = data_arr_map.get(key)
            data_arr = data_arrays.get(data_arr_name, []) if data_arr_name else []
            data_years = data_arrays.get("years", [])
            for yr in years:
                yr_val = gt_val.get(str(yr)) or gt_val.get(yr)
                if yr_val is None:
                    continue
                yr_val = float(yr_val) / divisor
                checked += 1
                # PATH A (preferred): exact-index match via DATA JS array
                # normalize years to int-strings ("2025" not "2025.0")
                data_years_norm = [str(int(float(y))) if isinstance(y,(int,float)) else str(y) for y in data_years]
                if data_arr and str(yr) in data_years_norm:
                    try:
                        idx = data_years_norm.index(str(yr))
                        report_val = float(data_arr[idx]) if idx < len(data_arr) else None
                        # ground truth for revenue_ty is in tỷ (÷1e9 done); DATA revenue is in tỷ VND too
                        # eps_vnd is per-share VND (no divisor scaling needed vs DATA eps)
                        # normalize: compare magnitudes with tolerance
                        if report_val is not None:
                            denom = max(abs(yr_val), abs(report_val), 0.001)
                            diff_pct = abs(yr_val - report_val) / denom * 100
                            if diff_pct > tolerance:
                                mismatches.append(f"{key}[{yr}]: DATA array value {report_val} ≠ ground_truth {yr_val:,.1f} (diff {diff_pct:.1f}% > {tolerance}%)")
                                continue
                            else:
                                continue  # matched at exact index
                    except (ValueError, IndexError):
                        pass
                # PATH B (fallback): context-anchored match (for fields not in DATA, e.g. balance sheet)
                yr_str = str(yr)
                found_match = _context_anchored_match(text, yr_str, yr_val, tolerance, fallback_key=key)
                if not found_match:
                    mismatches.append(f"{key}[{yr}]: ground_truth={yr_val:,.1f} not found (DATA-array miss + context-anchored fallback miss, ±{tolerance}%)")
        else:
            # Single value — PATCH P1-1: context-anchored (around the field key)
            gt_val = float(gt_val)
            checked += 1
            found_match = _context_anchored_match(text, key, gt_val, tolerance, fallback_key=key)
            if not found_match:
                mismatches.append(f"{key}: ground_truth={gt_val:,.0f} not found near its label (±{tolerance}% context-anchored)")

    passed = len(mismatches) == 0 and checked > 0
    return passed, {"checked": checked, "mismatches": mismatches[:5], "ground_truth_file": req["verification"]["data_file"]}


def verify_capex_accuracy(req, html):
    """Verify capex chart data matches cash_flow.json. Anti-fabrication."""
    import json as _json
    work_dir = os.path.dirname(REPORT) if REPORT else "."
    data_path = os.path.join(work_dir, req["verification"]["data_file"])

    if not os.path.exists(data_path):
        return False, {"error": f"cash_flow.json not found"}

    with open(data_path) as f:
        cf = _json.load(f)

    capex_key = req["verification"].get("capex_key", "Purchases of fixed assets and other long term assets")

    # Get capex from ground truth (sponsor format: dict with per-period values)
    if isinstance(cf, dict):
        capex_data = cf.get(capex_key)
        if capex_data is None:
            return False, {"error": f"capex key '{capex_key}' not in cash_flow.json", "available_keys": list(cf.keys())[:10]}

        # Handle dict (per-period): extract annual values for 2021-2025
        if isinstance(capex_data, dict):
            years = ['2021','2022','2023','2024','2025']
            gt_capex = [abs(float(capex_data[y])) / 1e9 for y in years if y in capex_data and capex_data[y] is not None]
        elif isinstance(capex_data, (int, float)):
            gt_capex = [abs(float(capex_data)) / 1e9]
        elif isinstance(capex_data, list):
            gt_capex = [abs(float(v))/1e9 for v in capex_data if v]
        else:
            return False, {"error": f"unexpected capex data type: {type(capex_data)}"}
    else:
        return False, {"error": "unexpected cash_flow.json format"}

    # Get capex from report JS DATA object — v0.14.4: quoted-key + negative support
    # v0.14.6: add - to character class for negative values after commas (e.g. eps: [-250, -36])
    js_capex_match = re.search(r'["\']?capex["\']?\s*:\s*\[(-?[\d.,\s-]+)\]', html or "")
    if not js_capex_match:
        return False, {"error": "capex array not found in report JS DATA", "gt_capex_sample": gt_capex[:3]}

    report_capex = [float(x.strip()) for x in js_capex_match.group(1).split(",") if x.strip()]

    # Compare magnitudes (report capex should be in tỷ, similar order)
    if report_capex and gt_capex:
        gt_avg = sum(abs(v) for v in gt_capex) / len(gt_capex)
        report_avg = sum(abs(v) for v in report_capex) / len(report_capex)
        diff_pct = abs(report_avg - gt_avg) / max(gt_avg, 0.001) * 100
        tolerance = req["verification"].get("tolerance_pct", 10)
        passed = diff_pct <= tolerance
        return passed, {
            "gt_capex_avg": round(gt_avg, 1),
            "report_capex_avg": round(report_avg, 1),
            "diff_pct": round(diff_pct, 1),
            "tolerance_pct": tolerance,
            "note": "report capex matches ground truth" if passed else "CAPEX FABRICATED — does not match cash_flow.json"
        }

    return False, {"error": "could not compare capex"}


def _extract_primary_multiple(text, label_pattern, computed_val, tolerance_pct):
    """PATCH P2: extract a valuation multiple (P/E, P/B) from visible report text.
    Handles × (U+00D7) and ASCII x. Requires leading digit. Avoids Chart.js JS tokens.

    Strategy:
      1. Find all occurrences of `label <number>(×|x)` in the scoped text (sec-valuation or sec-hero).
      2. Normalize to floats.
      3. If all candidates are the same value → UNAMBIGUOUS, return it.
      4. If multiple distinct values:
         a. If a primary semantic marker (data-metric, TTM/hiện tại/current label, val-card) identifies one → return it.
         b. If no marker → FAIL_AMBIGUOUS (return None with ambiguity detail).
      5. NEVER select by computed-value match — that would be cherry-picking to PASS, not verifying.
      6. If no candidates at all → None (value not found)."""
    # match: label (P/E or P/B), optional descriptive text, then NUMBER, then × or x
    pat = re.compile(rf'{label_pattern}[^0-9\n]{{0,30}}([\d,]+\.?\d*)\s*[×x]', re.I)
    # v0.14.1: identify the OTHER multiple label to detect cross-contamination
    other_label = "p/e" if "p/?b" in label_pattern.lower() else "p/b"
    candidates = []  # list of (value, is_primary, is_projection)
    for m in pat.finditer(text):
        # v0.14.1: skip if the text between label and number contains the OTHER label
        # (prevents "P/B vs lịch sử P/E (TTM) 7.35×" from matching 7.35 as P/B)
        gap_text = text[m.start()+2:m.start()+len(m.group(0))].lower()  # text after "P/B"
        if other_label in gap_text:
            continue  # cross-contaminated match — the number belongs to the other multiple
        # v0.14.5: handle Vietnamese decimal notation (4,8 = 4.8, not 48)
        raw_orig = m.group(1)
        # If comma is followed by exactly 1-2 digits at the end → decimal separator
        if re.search(r',\d{1,2}$', raw_orig) and '.' not in raw_orig:
            raw = raw_orig.replace(',', '.')  # 4,8 → 4.8, 4,80 → 4.80
        else:
            raw = raw_orig.replace(',', '')  # 1,234.56 → 1234.56 (thousands)
        try:
            val = float(raw)
            if val > 1000: continue
            label_to_num = text[m.start():m.start()+len(m.group(0))].lower()
            has_primary = any(kw in label_to_num for kw in ["data-metric","ttm","hiện tại","current","val-card","mono","kpi-value"])
            has_projection = any(kw in label_to_num for kw in ["median","target","5y","projected","fcf","graham","ev/ebitda","p/cf","dcf","wacc"])
            is_primary = has_primary and not has_projection
            candidates.append((val, is_primary, has_projection))
        except ValueError:
            continue
    if not candidates:
        return None
    # Filter out projection candidates (median/5Y/target/DCF are NOT the current multiple)
    non_projection = [(v, ip) for v, ip, proj in candidates if not proj]
    if not non_projection:
        return None  # all candidates are projections — no current multiple found
    distinct = set(v for v, _ in non_projection)
    # Rule 3: all non-projection values same → unambiguous
    if len(distinct) == 1:
        return non_projection[0][0]
    # v0.14.8: majority vote — CONSTRAINED to valuation scope only
    # Only applies when: no canonical marker, candidates from valuation section,
    # projections removed, no P/E cross-contamination in candidate gaps
    from collections import Counter
    val_counts = Counter(v for v, _ in non_projection)
    most_common_val, most_common_count = val_counts.most_common(1)[0]
    if most_common_count >= 3 and most_common_count >= len(non_projection) * 0.6:
        return most_common_val
    # Rule 4a: multiple distinct non-projection → need primary marker
    marked = [(v, ip) for v, ip in non_projection if ip]
    if len(marked) >= 1:
        return marked[0][0]
    # Rule 4b: multiple distinct, no marker → AMBIGUOUS
    return None  # caller will report AMBIGUOUS_PRIMARY_MULTIPLE

def verify_valuation_recompute(req, html):
    """Recompute PE/PB/Graham from data, compare to report values.

    v0.14.7: PREFER canonical valuation contract over recompute from rounded financials.
    The verified-dashboard-data.json contains the authoritative PE/PB values computed
    by the builder from raw source data. The verifier now compares artifact values
    against these canonical values, falling back to recompute only when the contract
    is unavailable.

    v0.14.7: Handle PE=N/A when EPS=0 (legitimately non-computable). PB is still verified.
    """
    import json as _json, math as _math
    work_dir = os.path.dirname(REPORT) if REPORT else "."
    fin_path = os.path.join(work_dir, "data/financials.json")
    contract_path = os.path.join(work_dir, "verified-dashboard-data.json")

    if not os.path.exists(fin_path):
        return False, {"error": "financials.json not found"}

    with open(fin_path) as f:
        fin = _json.load(f)

    # v0.14.7: Load canonical valuation contract (authoritative PE/PB)
    contract = None
    if os.path.exists(contract_path):
        with open(contract_path) as f:
            contract = _json.load(f)

    price = fin.get("overview", {}).get("current_price")
    eps_2025 = fin.get("eps_vnd", {}).get("2025")

    full_text = extract_all_text(html) if html else ""
    val_text_parts = []
    for sec_id in ["sec-valuation", "sec-hero", "sec-exec"]:
        st = extract_section_text(html, sec_id) if html else ""
        if st:
            val_text_parts.append(st)
    val_text = "\n".join(val_text_parts) if val_text_parts else full_text

    results_check = {}
    all_pass = True

    for formula in req["verification"].get("formulas", []):
        name = formula["name"]
        tolerance = formula.get("tolerance_pct", 2)

        if name == "PE":
            # v0.14.8: Source-consistency check for EPS=0
            if eps_2025 == 0 or eps_2025 is None:
                # Check if EPS=0 is consistent with positive net profit
                np_2025 = fin.get("npatmi_ty", {}).get("2025")
                eps_status = "REPORTED_ZERO"
                if np_2025 and np_2025 > 0 and eps_2025 == 0:
                    eps_status = "SUSPECT_ZERO_OR_MISSING"
                contract_pe = contract.get("valuation", {}).get("pe") if contract else None
                if contract_pe is None:
                    if eps_status == "SUSPECT_ZERO_OR_MISSING":
                        results_check[name] = {"status": "NOT_AVAILABLE_DUE_TO_SOURCE_CONFLICT",
                                              "reason": f"EPS=0 but net profit={np_2025} tỷ > 0 → source data suspect",
                                              "eps_status": eps_status,
                                              "note": "PE skipped — PB still verified. Artifact should note EPS data quality concern."}
                    else:
                        results_check[name] = {"status": "NOT_COMPUTABLE", "reason": "EPS=0",
                                              "eps_status": eps_status,
                                              "note": "PE skipped — PB still verified"}
                    continue
                else:
                    results_check[name] = {"error": "EPS=0 but contract has PE — source data inconsistency"}
                    all_pass = False
                    continue

            # Use canonical contract PE if available (more precise than recompute)
            if contract and contract.get("valuation", {}).get("pe") is not None:
                computed = contract["valuation"]["pe"]
            else:
                computed = price / eps_2025 if eps_2025 else None
            report_val = _extract_primary_multiple(val_text, "P/?E", computed, tolerance)

        elif name == "PB":
            # v0.14.7: Use canonical contract PB if available
            if contract and contract.get("valuation", {}).get("pb") is not None:
                computed = contract["valuation"]["pb"]
                report_val = _extract_primary_multiple(val_text, "P/?B", computed, tolerance)
            else:
                equity = fin.get("equity_ty", {}).get("2025")
                shares = fin.get("overview", {}).get("issue_share")
                if equity is None or shares is None:
                    results_check[name] = {"error": "missing equity_ty or issue_share (no default fallback)"}
                    all_pass = False
                    continue
                bvps = equity * 1e9 / shares
                computed = price / bvps if bvps else None
                report_val = _extract_primary_multiple(val_text, "P/?B", computed, tolerance)
        else:
            continue

        if computed and report_val is not None:
            diff_pct = abs(computed - report_val) / computed * 100
            ok = diff_pct <= tolerance
            results_check[name] = {"computed": round(computed, 2), "report": report_val, "diff_pct": round(diff_pct, 2), "ok": ok}
            if not ok:
                all_pass = False
        else:
            results_check[name] = {"error": "could not extract or compute", "computed": computed, "report": report_val}
            all_pass = False

    return all_pass, results_check


def verify_chart_data_accuracy(req, html):
    """Verify DATA JS object arrays match financials.json."""
    import json as _json
    work_dir = os.path.dirname(REPORT) if REPORT else "."
    data_path = os.path.join(work_dir, req["verification"]["data_file"])

    if not os.path.exists(data_path):
        return False, {"error": "financials.json not found"}

    with open(data_path) as f:
        fin = _json.load(f)

    check_arrays = req["verification"].get("check_arrays", [])
    mismatches = []

    for arr_name in check_arrays:
        # Get ground truth
        if arr_name == "revenue":
            gt = list(fin.get("revenue_ty", {}).values())
        elif arr_name == "netProfit":
            gt = list(fin.get("npatmi_ty", {}).values())
        elif arr_name == "eps":
            gt = list(fin.get("eps_vnd", {}).values())
        else:
            continue

        # Get report JS value — v0.14.0: support negative numbers (airlines, cyclicals)
        # v0.14.1: support both quoted ("revenue") and unquoted (revenue) key formats
        # v0.14.6: add - to character class for negative values after commas
        js_match = re.search(rf'["\']?{arr_name}["\']?\s*:\s*\[(-?[\d.,\s-]+)\]', html or "")
        if not js_match:
            mismatches.append(f"{arr_name}: not found in JS DATA")
            continue

        report_vals = [float(x.strip()) for x in js_match.group(1).split(",") if x.strip()]

        # Compare arrays (allow length diff but values should match)
        min_len = min(len(gt), len(report_vals))
        for i in range(min_len):
            if gt[i] and abs(report_vals[i] - gt[i]) / max(abs(gt[i]), 0.001) * 100 > 5:
                mismatches.append(f"{arr_name}[{i}]: gt={gt[i]:.0f} vs report={report_vals[i]:.0f}")

    passed = len(mismatches) == 0
    return passed, {"checked_arrays": check_arrays, "mismatches": mismatches[:5]}


def verify_external_claim_flag(req, html):
    """Check that external claims are flagged appropriately.

    TWO-TIER PROVENANCE (v0.1.6, owner directive 2026-07-14):
      Tier A — Financial/Valuation claims (WCM, MCH, analyst targets):
        100% provenance required. Must have explicit flag (ước tính, estimate, source).
      Tier B — Widely-known company descriptors (store count, market share, factories):
        Memory allowed IF qualified as general background. Accepted qualifiers:
        "theo công bố" / "according to disclosures" / "ước tính" / "~" / "khoảng"
        This mirrors sell-side research: "Apple has 2B+ active devices" is background;
        "Revenue grew 18.6%" requires a source.

    A claim is UNFLAGGED only when it's a Tier A claim without provenance, OR a Tier B
    claim with NO qualifier whatsoever.
    """
    text = extract_all_text(html) if html else ""
    patterns = req["verification"].get("patterns", [])
    must_flag = req["verification"].get("must_flag", "ước tính|estimate")
    adjacent_window = req["verification"].get("adjacent_window", 200)

    # Tier B qualifiers — these make widely-known company descriptors acceptable
    # without requiring inline citation (like sell-side research).
    tier_b_qualifiers = [
        r"theo\s+(?:công\s+ bố|báo\s+cáo|disclosure|bctc|issuer|company)",
        r"according\s+to\s+(?:company|disclosure|report)",
        r"ước\s+tính", r"estimate", r"external", r"marketing",
        r"~",  # approximate marker (~38% thị phần)
        r"khoảng", r"xấp\s+xỉ", r"approximately", r"roughly",
        r"general\s+background", r"thông\s+tin\s+chung",
        r"nổi\s+tiếng", r"widely\s+known", r"phổ\s+biến",
        r"market\s+leader", r"thống\s+trị", r"dẫn\s+đầu",
    ]
    tier_b_qualifier_pattern = "|".join(tier_b_qualifiers)

    # Classify patterns into tiers
    # Tier A: financial/analyst claims (WCM, MCH — require strict provenance)
    tier_a_patterns = [p for p in patterns if "WCM" in p or "MCH" in p]
    # Tier B: company descriptors (store count, market share — allow qualifier)
    tier_b_patterns = [p for p in patterns if p not in tier_a_patterns]

    unflagged_claims = []
    total_claims = 0
    for pattern in patterns:
        is_tier_a = pattern in tier_a_patterns
        for m in re.finditer(pattern, text, re.I):
            total_claims += 1
            ctx = text[max(0, m.start()-adjacent_window):m.end()+adjacent_window]
            if is_tier_a:
                # Tier A: must have strict provenance flag
                if not re.search(must_flag, ctx, re.I):
                    unflagged_claims.append({"pattern": pattern, "match": m.group(0)[:40],
                                            "tier": "A", "reason": "strict provenance required"})
            else:
                # Tier B: accept either strict flag OR a tier-B qualifier
                if not re.search(must_flag, ctx, re.I) and not re.search(tier_b_qualifier_pattern, ctx, re.I):
                    unflagged_claims.append({"pattern": pattern, "match": m.group(0)[:40],
                                            "tier": "B", "reason": "needs qualifier (~, khoảng, theo công bố, or ước tính)"})
    passed = (total_claims == 0) or (len(unflagged_claims) == 0)
    return passed, {"external_claims_found": total_claims,
                    "unflagged": unflagged_claims[:5],
                    "adjacent_window": adjacent_window,
                    "tier_a_patterns": len(tier_a_patterns),
                    "tier_b_patterns": len(tier_b_patterns),
                    "patch_note": "v0.1.6: two-tier provenance — Tier A strict, Tier B qualifier-allowed"}


def verify_div_balance(req, html):
    """Check div open = div close."""
    if not html:
        return False, {"error": "no html"}
    opens = len(re.findall(r"<div[ >]", html))
    closes = len(re.findall(r"</div>", html))
    passed = opens == closes
    return passed, {"opens": opens, "closes": closes}


def verify_source_citation(req, html):
    """REQ-029: Source citation check — mọi số liệu trong narrative phải có nguồn.

    Quét narrative (text content, không CSS/JS) tìm số liệu định lượng
    không có source keyword gần đó. Key metrics phải cite ít nhất 1 lần.

    Lesson Learned #7-10: agent đưa %, multiples, drawdown không cite nguồn.
    """
    if not html:
        return False, {"error": "no html"}

    # Extract text content only (strip tags, CSS, JS)
    # Remove <style> and <script> blocks
    text_html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text_html = re.sub(r'<script[^>]*>.*?</script>', '', text_html, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text_html)
    text = re.sub(r'\s+', ' ', text).strip()

    source_keywords = ['bctc', 'theo', 'nguồn', 'source', 'ref-', 'vnstock', 'data',
                       'ước tính', 'giả định', 'khoảng', 'tiếp cận', 'estimate',
                       'tính từ', 'recompute', 'sponsor', 'kiểm toán', 'công bố']
    uncertainty_markers = ['ước tính', 'giả định', 'khoảng', 'có thể', 'xấp xỉ',
                           'tiếp cận', 'estimate', 'approximate']

    # Find all quantitative claims: numbers with units
    # Pattern: digits + (tỷ/nghìn/%/×/x/VND)
    number_pattern = re.compile(
        r'(\d[\d.,]*)\s*(tỷ\s*(?:vnd|đồng)?|nghìn\s*tỷ|ngàn\s*tỷ|%|phần\s*trăm|×|x\b|lần|vnd)',
        re.IGNORECASE
    )

    issues = []
    checked = 0
    unsourced = 0

    for m in number_pattern.finditer(text):
        val_str = m.group(1)
        unit = m.group(2).lower().strip()

        # Skip if value is 0 or clearly not a data point
        try:
            val = float(val_str.replace(',', '.'))
        except ValueError:
            continue
        if val == 0 or val == 100:
            continue

        checked += 1
        # Context window: 200 chars before and after
        start = max(0, m.start() - 200)
        end = min(len(text), m.end() + 200)
        context = text[start:end].lower()

        has_source = any(kw in context for kw in source_keywords)
        has_uncertainty = any(kw in context for kw in uncertainty_markers)

        if not has_source and not has_uncertainty:
            unsourced += 1
            snippet = text[max(0, m.start()-40):m.end()+40].strip()
            issues.append(f'"{val_str} {unit}" không có source gần — ...{snippet}...')

    # Key metrics must have at least 1 source citation
    key_metrics = ['P/E', 'P/B', 'CAGR', 'ROE', 'ROA', 'EPS']
    key_metric_issues = []
    for km in key_metrics:
        if km.lower() in text.lower():
            # Find first occurrence
            idx = text.lower().find(km.lower())
            context = text[max(0, idx-300):idx+300].lower()
            if not any(kw in context for kw in source_keywords):
                key_metric_issues.append(f'{km}: không có source cite trong context đầu tiên')

    passed = (unsourced <= 5) and (len(key_metric_issues) == 0)
    evidence = {
        "checked_numbers": checked,
        "unsourced_numbers": unsourced,
        "threshold": "≤5 unsourced (cho phép CSS artifacts lọt qua)",
        "unsourced_examples": issues[:5],
        "key_metrics_without_source": key_metric_issues,
    }
    return passed, evidence


def verify_price_source(req, html):
    """REQ-030: Price freshness check — giá phải fetch từ API, không tự điền.

    Check: price trong DATA object phải có source traceability.
    Nếu verified-dashboard-data.json có price nhưng không có price_fetched_at → suspect.

    Lesson Learned #6: price=62000 tự điền tay.
    """
    if not html:
        return False, {"error": "no html"}

    issues = []

    # Extract DATA object price
    data_match = re.search(r'price["\']?\s*[:=]\s*(\d+)', html)
    if not data_match:
        return True, {"note": "no price found in HTML (may be absent)"}

    price_val = int(data_match.group(1))
    if price_val == 0:
        issues.append("price = 0 in DATA")
        return False, {"price": 0, "issues": issues}

    # Check for price_fetched_at or price_source in DATA
    has_timestamp = bool(re.search(r'price_fetched_at|price_source|priceFetchedAt', html, re.IGNORECASE))
    has_api_source = bool(re.search(r'vnstock|sponsor|api.*price|fetch.*price', html, re.IGNORECASE))

    # Check for round numbers that suggest manual entry (60000, 50000, etc.)
    is_round = price_val % 1000 == 0

    if not has_timestamp and not has_api_source:
        if is_round:
            issues.append(f"price={price_val} là số tròn + không có price_fetched_at → NGHI NGOẠI tự điền tay")
        else:
            issues.append(f"price={price_val} không có price_fetched_at hoặc API source reference")

    passed = len(issues) == 0
    evidence = {
        "price_value": price_val,
        "has_price_fetched_at": has_timestamp,
        "has_api_source_reference": has_api_source,
        "is_round_number": is_round,
        "issues": issues,
    }
    return passed, evidence


def verify_drawdown_source(req, html):
    """REQ-031: Drawdown verification — claim drawdown phải có data thật.

    Nếu narrative nói "drawdown X%" → phải có max_drawdown trong DATA.
    Nếu KHÔNG có data → phải ghi "ước tính".

    Lesson Learned #9: "30-50% drawdown" không có data thật.
    """
    if not html:
        return False, {"error": "no html"}

    # Extract text content
    text_html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text_html = re.sub(r'<script[^>]*>.*?</script>', '', text_html, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text_html)
    text = re.sub(r'\s+', ' ', text).strip()

    issues = []

    # Find drawdown claims: "drawdown X%" or "giảm X%" or "mất X triệu"
    drawdown_patterns = [
        r'(?:drawdown|sụt giảm|giảm(?:\s+xuống)?)[^.]{0,30}?(\d+(?:[.,]\d+)?)\s*%',
        r'(?:mất|tổn\s*thất)[^.]{0,30}?(\d+(?:[.,]\d+)?)\s*(?:%|triệu|tỷ)',
        r'(?:có\s*thể\s*giảm|rủi\s*ro\s*giảm)[^.]{0,30}?(\d+(?:[.,]\d+)?)\s*[-–]\s*(\d+(?:[.,]\d+)?)\s*%',
    ]

    drawdown_claims = []
    for pat in drawdown_patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            val = m.group(1) if m.lastindex >= 1 else '?'
            context = text[max(0, m.start()-100):m.end()+100]
            drawdown_claims.append({
                'value': val,
                'context': context.strip()[:120],
            })

    # Check if DATA has max_drawdown
    has_drawdown_data = bool(re.search(r'max_drawdown|drawdownData|maxDrawdown', html, re.IGNORECASE))

    # Check if claims have uncertainty markers
    uncertainty_keywords = ['ước tính', 'giả định', 'có thể', 'khoảng', 'ngành', 'history',
                            'lịch sử', 'thường', 'trung bình', 'estimate']

    for claim in drawdown_claims:
        ctx_lower = claim['context'].lower()
        has_uncertainty = any(kw in ctx_lower for kw in uncertainty_keywords)
        if not has_drawdown_data and not has_uncertainty:
            issues.append(f"drawdown claim '{claim['value']}%' không có data thật và không có marker 'ước tính'")

    # If no drawdown claims at all → PASS (nothing to check)
    if not drawdown_claims:
        return True, {"note": "no drawdown claims found in narrative"}

    passed = len(issues) == 0
    evidence = {
        "drawdown_claims_found": len(drawdown_claims),
        "claims": [c['context'] for c in drawdown_claims[:5]],
        "has_max_drawdown_data": has_drawdown_data,
        "issues": issues,
    }
    return passed, evidence


def verify_chart_runtime_check(req, html):
    """REQ-028: Render-readiness proxy cho runtime chart render.

    Không có browser trong verifier, nhưng check 3 điều kiện cần cho chart render:
    1. Mỗi canvas ID referenced trong Chart(...) call phải có <canvas id="..."> element
    2. Mỗi Chart(...) call phải có data.datasets (không rỗng)
    3. Không có duplicate canvas ID (Chart.js strict mode fail)

    Học từ PNJ v2 test: 13 charts claimed render nhưng template có duplicate canvas
    sau </body> → Playwright strict mode violation.
    """
    if not html:
        return False, {"error": "no html"}

    issues = []

    # 1. Extract all canvas IDs from HTML
    canvas_ids = re.findall(r'<canvas[^>]*id=["\']([^"\']+)["\']', html)
    canvas_id_counts = {}
    for cid in canvas_ids:
        canvas_id_counts[cid] = canvas_id_counts.get(cid, 0) + 1

    # 2. Extract Chart(...) targets: $('chartId') or getElementById('chartId')
    # PATCH (P0-1): distinguish UNCONDITIONAL refs from CONDITIONAL/fallback refs.
    #   - conditional:  `if ($(id)) new Chart($(id)...)`        → canvas optional, not required
    #   - fallback:     `new Chart($(primary) || $(fallback))`  → only primary required
    # Previously ALL chart-like refs were treated as required → false positives on reports
    # that legitimately guard optional charts. (Audit 2026-07-12: REQ-028 FP on clean PNJ.)
    chart_targets = re.findall(r"""\$\(['"]([^'"]+)['"]\)|getElementById\(['"]([^'"]+)['"]\)""", html)
    referenced_ids = set()
    unconditional_required = set()   # ids that MUST have a canvas
    for t in chart_targets:
        cid = t[0] or t[1]
        if not (cid.startswith('chart') or cid.startswith('Chart')):
            continue
        referenced_ids.add(cid)
        # find the JS statement containing this ref to classify it
        for m in re.finditer(re.escape(cid), html):
            ctx = html[max(0, m.start()-90):m.end()+20]
            if re.search(r'\bif\s*\(\s*\$\(\s*[\'"]' + re.escape(cid), ctx) or \
               re.search(r'\bif\s*\(\s*document\.getElementById', ctx):
                break  # conditional — not required
            # fallback pattern: $(primary) || $(cid)  → cid is the fallback, primary required
            if re.search(r"\$\([^)]+\)\s*\|\|\s*\$\(\s*[\"']" + re.escape(cid), ctx):
                break  # this cid is a fallback, not required
            unconditional_required.add(cid)

    # 3. Check each UNCONDITIONAL referenced chart ID has canvas element
    # PATCH (P0-1): only missing *unconditional* canvases count. A handful of optional
    # charts absent is a WARN (defect), not a deploy-blocking FAIL.
    missing_canvas_required = [rid for rid in unconditional_required if rid not in canvas_id_counts]
    missing_canvas_optional = [rid for rid in (referenced_ids - unconditional_required) if rid not in canvas_id_counts]

    # 4. Check duplicate canvas IDs
    duplicates = {cid: count for cid, count in canvas_id_counts.items() if count > 1}

    # 5. Check DATA object exists (charts depend on it)
    has_data_obj = bool(re.search(r'const\s+DATA\s*=', html))

    # 6. Check Chart.js loaded
    has_chart_js = bool(re.search(r'new\s+Chart\s*\(', html))

    # PATCH (P0-1): split issues into critical (FAIL) vs advisory (WARN).
    #   FAIL: duplicate canvas IDs (strict-mode crash), no DATA, no Chart.js,
    #         canvas after </body>, OR many required canvases missing (>30%).
    #   WARN (not FAIL): a few optional/single required canvas absent.
    critical_issues = []
    advisory = []
    if duplicates:
        critical_issues.append(f"Duplicate canvas IDs (strict mode risk): {duplicates}")
    if not has_data_obj:
        critical_issues.append("No `const DATA =` object found — charts will crash")
    if not has_chart_js:
        critical_issues.append("No `new Chart(` calls found")
    if missing_canvas_required:
        pct_missing = len(missing_canvas_required) / max(len(unconditional_required), 1)
        msg = f"Required canvas missing: {missing_canvas_required} ({pct_missing:.0%} of {len(unconditional_required)} unconditional charts)"
        if pct_missing > 0.30:
            critical_issues.append(msg)
        else:
            advisory.append(msg)
    if missing_canvas_optional:
        advisory.append(f"Optional canvas absent (not deploy-blocking): {missing_canvas_optional}")
    issues = critical_issues + [f"WARN: {a}" for a in advisory]

    # Also check: canvas after </body> (template illustration leak — PNJ bug)
    body_close = html.rfind('</body>')
    html_close = html.rfind('</html>')
    if body_close >= 0 and html_close >= 0 and body_close < html_close:
        trailing = html[body_close:html_close]
        trailing_canvas = re.findall(r'<canvas[^>]*id=["\']([^"\']+)["\']', trailing)
        if trailing_canvas:
            critical_issues.append(f"Canvas elements after </body> (illustration leak): {trailing_canvas}")

    # PATCH (P0-1): PASS unless a CRITICAL issue. Advisory warnings don't block.
    passed = len(critical_issues) == 0
    return passed, {
        "canvas_ids_found": list(canvas_id_counts.keys()),
        "chart_ids_referenced": list(referenced_ids),
        "unconditional_required": list(unconditional_required),
        "missing_canvas_required": missing_canvas_required,
        "missing_canvas_optional": missing_canvas_optional,
        "duplicates": duplicates,
        "has_data_object": has_data_obj,
        "has_chart_js": has_chart_js,
        "critical_issues": critical_issues,
        "advisory": advisory,
        "issues": issues,
        "patch_note": "P0-1: conditional/fallback refs excluded from required; advisory split from critical",
    }


# ═══════════════════════════════════════════════════════════════
# V2 REVIEW-AGENT CHECKS (REQ-032..043)
# Chống 8 evasion patterns: keyword-stuffing, vacuous pass, bịa peer/segment/
# industry/tech data, trộn năm, cross-section mâu thuẫn, identity nhầm ticker.
# ═══════════════════════════════════════════════════════════════

_KNOWN_TICKERS = [
    # HOSE
    "ACB","BCM","BID","BVH","CTG","DIG","FPT","GAS","GEX","GMD","HDB","HPG","KDH",
    "MBB","MSN","MWG","NVL","OCB","PDR","PLX","PNJ","POW","REE","SAB","SSB","SSI",
    "STB","TCB","TPB","VCB","VHM","VIC","VJC","VNM","VPB","VRE","VSC","SBT",
    # HNX
    "CE1","IDC","MBS","NDN","NTP","PVS","SHB","SHS","TIG","VCS","VGS","VCG",
    # UpCOM
    "ACV","BAB","BVB","DPM","GVR","LPB","MCH","MSB","NAB","NKG","SMC","TCH","VGI",
    # NOTE: "VND" cố ý KHÔNG có trong danh sách — VND là đơn vị tiền tệ, xuất hiện
    # khắp report (giá 62,000 VND). VNDirect không nên được check như ticker lạ.
]

def _work_dir():
    return os.path.dirname(REPORT) if REPORT else "."

def _load_json_rel(path):
    """Load JSON relative to report work dir. Returns None on any failure."""
    full = os.path.join(_work_dir(), path)
    if not os.path.exists(full):
        return None
    try:
        with open(full) as f:
            return json.load(f)
    except Exception:
        return None

def _normalize_number(tok):
    """'12.345,6' / '12,345' / '9,078' / '12345' → float. VN thousands='.', decimal=','.
    Heuristic VN tiền tệ: 3 chữ số sau dấu phẩy = nghìn separator (9,078 = 9078);
    1-2 chữ số sau dấu phẩy = decimal (1,5 = 1.5). Dấu chấm luôn là nghìn separator
    khi có 3 chữ số sau (12.345 = 12345), nếu không (1.5) là decimal."""
    tok = tok.strip().replace(" ", "").replace("đ", "")
    if not tok:
        return None
    # Both separators → dot = thousands, comma = decimal
    if "." in tok and "," in tok:
        tok = tok.replace(".", "").replace(",", ".")
    elif "," in tok:
        after = tok.split(",")[1]
        if len(after) == 3:
            tok = tok.replace(",", "")
        else:
            tok = tok.replace(",", ".")
    elif "." in tok:
        after = tok.split(".")[1]
        if len(after) == 3:
            tok = tok.replace(".", "")
    try:
        return float(tok)
    except ValueError:
        return None

def _scale_to_tỷ(text_val, unit):
    """Convert a number+unit pair to tỷ VND."""
    unit = (unit or "").lower()
    if "nghìn tỷ" in unit or "ngan ty" in unit:
        return text_val * 1000
    if "triệu" in unit or "m" == unit.strip() or "tr" == unit.strip():
        return text_val / 1000
    if "tỷ" in unit or "tỉ" in unit or "b" == unit.strip():
        return text_val
    if "%" in unit:
        return text_val  # percent, no scaling
    return text_val

def _find_numeric_claims(text, keywords, window=120):
    """Find (keyword, value, context) claims: keyword then number within window."""
    claims = []
    for kw in keywords:
        pat = re.compile(re.escape(kw) + r"[^0-9%]{0," + str(window) + r"}?(\d[\d.,]*)\s*(nghìn tỷ|tỷ|tỉ|triệu|tr|m|%)?", re.I)
        for m in pat.finditer(text):
            val = _normalize_number(m.group(1))
            if val is None:
                continue
            claims.append({
                "keyword": kw,
                "value": val,
                "unit": m.group(2) or "",
                "context": text[max(0, m.start()-80):m.end()+80].strip()[:160],
            })
    return claims


def verify_peer_provenance(req, html):
    """REQ-032: Peer data phải có nguồn (peers.json / verified-dashboard-data.json).

    Chống bịa peer (Lesson Learned #4): nếu narrative có số liệu định lượng về peer
    (P/E, P/B, market cap của công ty khác) → phải có peer data file, value khớp ±10%.
    Chỉ mention tên peer không kèm số → không vi phạm.
    """
    if not html:
        return False, {"error": "no html"}
    peer_text = extract_section_text(html, "sec-peer")
    if not peer_text:
        return True, {"note": "no sec-peer section — nothing to check"}

    # Find quantitative peer claims (number near ticker/company or P/E P/B x-value)
    claims = []
    # pattern 1: ticker + number nearby (e.g. "HBC P/E 8x", "SSI vốn hóa 50.000 tỷ")
    for m in re.finditer(r"\b([A-Z]{3})\b[^.%0-9]{0,60}?(\d[\d.,]*)\s*(x|tỷ|tỉ|triệu|nghìn tỷ)?", peer_text):
        claims.append({"type": "ticker_value", "ticker": m.group(1), "value": m.group(2), "unit": m.group(3) or ""})
    # pattern 2: P/E or P/B multiple without ticker (e.g. "P/E 5x" — must come from data)
    for m in re.finditer(r"P/\s*[EB]\s*[^0-9]{0,10}?(\d[\d.,]*)\s*x?", peer_text, re.I):
        claims.append({"type": "multiple", "value": m.group(1)})

    # Check peer data source
    peers_data = None
    for cand in ("peers.json", "data/peers.json", "verified-dashboard-data.json"):
        d = _load_json_rel(cand)
        if d is not None:
            if cand.endswith("peers.json"):
                peers_data = d
            elif isinstance(d, dict) and ("peers" in d or "peer" in d):
                peers_data = d
        if peers_data is not None:
            break

    if not peers_data:
        # No peer data file → quantitative peer claims are unprovenanced
        if claims:
            return False, {
                "peer_claims_found": len(claims),
                "claims": [c for c in claims[:5]],
                "error": "quantitative peer claims without peers.json / verified-dashboard-data.json.peers",
                "hint": "phase1 phải fetch peers.json; nếu không fetch được → ghi 'chưa có data peer'",
            }
        return True, {"note": "peer names mentioned without quantitative claims — acceptable"}

    # Peer data exists → verify each claim value matches (contextual string match ±10%)
    peers_blob = json.dumps(peers_data, ensure_ascii=False)
    mismatches = []
    checked = 0
    for c in claims:
        v = _normalize_number(c.get("value"))
        if v is None:
            continue
        # find any number in peers blob within 10%
        for pv in re.findall(r"\d[\d.,]*", peers_blob):
            pv_f = _normalize_number(pv)
            if pv_f is None or pv_f == 0:
                continue
            if abs(v - pv_f) / max(abs(pv_f), 0.001) <= 0.10:
                checked += 1
                break
        else:
            mismatches.append(f"peer claim value {c.get('value')}{c.get('unit','')} not in peer data (±10%)")
    passed = len(mismatches) == 0
    return passed, {
        "peer_data_source": "peers.json" if peers_data else "verified-dashboard-data.json",
        "peer_claims_found": len(claims),
        "claims_verified": checked,
        "mismatches": mismatches[:5],
    }


def verify_cross_section_consistency(req, html):
    """REQ-033: Cùng 1 số liệu key ở nhiều section phải khớp (±5%).

    Trích (metric, year?, value) từ mọi section. Nếu 2 section cùng year-metric
    lệch >5% → FAIL. Nếu metric không gắn year → so chung nhóm.
    """
    if not html:
        return False, {"error": "no html"}

    metrics = {
        "revenue": [r"doanh thu", r"revenue"],
        "net_profit": [r"lợi nhuận ròng", r"lợi nhuận sau thuế", r"LNST", r"npatmi", r"net profit", r"NPAT"],
        "eps": [r"EPS"],
        "pe": [r"P\s*/\s*E", r"P/E"],
        "pb": [r"P\s*/\s*B", r"P/B"],
        "market_cap": [r"vốn hóa", r"market cap", r"marketcap"],
        "total_assets": [r"tổng tài sản", r"total assets"],
        "equity": [r"vốn chủ sở hữu", r"equity"],
    }
    # Metric không đo bằng % (revenue/profit/eps/assets/equity/market cap là số tuyệt đối)
    NO_PCT_UNIT = {"revenue", "net_profit", "eps", "market_cap", "total_assets", "equity"}

    # Collect per-section claims
    # Sections mang claim số liệu kinh doanh. Loại: source/glossary/analyst/checklist/
    # tech (ref numbers, định nghĩa, scale — gây false positive).
    CLAIM_SECTIONS = {
        "sec-hero", "sec-exec", "sec-biz", "sec-industry", "sec-history",
        "sec-segment", "sec-thesis", "sec-valuation", "sec-peer", "sec-bs",
        "sec-risk", "sec-scenario", "sec-insight-1", "sec-insight-2", "sec-insight-3",
    }
    section_ids = set(re.findall(r'<section[^>]*id="(sec-[a-z0-9-]+)"', html)) & CLAIM_SECTIONS
    per_metric = {}  # metric → [(year_or_None, value, section, context)]
    for sid in sorted(section_ids):
        sec_text = extract_section_text(html, sid)
        if not sec_text or len(sec_text) < 30:
            continue
        for metric, kws in metrics.items():
            for kw in kws:
                pat = re.compile(kw + r"[^0-9]{0,60}?(\d[\d.,]*)\s*(nghìn tỷ|tỷ|tỉ|triệu|tr|x|%)?", re.I)
                for m in pat.finditer(sec_text):
                    val = _normalize_number(m.group(1))
                    if val is None:
                        continue
                    unit = m.group(2) or ""
                    # "%" không phải đơn vị của metric số tuyệt đối (vd "Doanh thu CAGR 35%")
                    if unit == "%" and metric in NO_PCT_UNIT:
                        continue
                    # "CAGR" giữa keyword và số → đây là claim tăng trưởng, không phải giá trị metric
                    between = sec_text[m.start():m.start(1)]
                    if re.search(r"cagr|tăng trưởng|growth|biên|margin", between, re.I):
                        continue
                    scaled = _scale_to_tỷ(val, unit)
                    # Skip years-as-values (2021..2029, 4-digit, no unit)
                    if 2000 <= scaled <= 2099 and not unit:
                        continue
                    # Skip tiny unitless numbers (ref ids, points, index values)
                    if not unit and scaled < 20:
                        continue
                    # year near the claim? (trước HOẶC sau số — "…30,699 tỷ (FY2025)")
                    ctx = sec_text[max(0, m.start()-60):m.end()+60]
                    ym = re.search(r"20\d\d", ctx)
                    year = ym.group(0) if ym else None
                    # Claim không gắn year → không so sánh được (có thể là năm khác nhau)
                    if not year:
                        continue
                    per_metric.setdefault(metric, []).append({
                        "year": year, "value": scaled, "section": sid,
                        "context": ctx.strip()[:120],
                    })
                break  # first keyword hit per metric per section is enough

    issues = []
    checked_pairs = 0
    for metric, items in per_metric.items():
        if len(items) < 2:
            continue
        # group by year (None = "current" bucket)
        buckets = {}
        for it in items:
            buckets.setdefault(it["year"], []).append(it)
        for year, group in buckets.items():
            if len(group) < 2:
                continue
            vals = [g["value"] for g in group]
            vmin, vmax = min(vals), max(vals)
            if vmin == 0:
                continue
            diff_pct = (vmax - vmin) / vmin * 100
            checked_pairs += 1
            if diff_pct > 5:
                issues.append(
                    f"{metric}{'/'+year if year else ''}: {vmin:,.1f} vs {vmax:,.1f} (lệch {diff_pct:.1f}% > 5%) — "
                    + "; ".join(f"{g['section']}: {g['value']:,.1f}" for g in group)
                )

    passed = len(issues) == 0
    return passed, {
        "sections_scanned": len(section_ids),
        "metrics_with_multiple_claims": {m: len(v) for m, v in per_metric.items() if len(v) > 1},
        "pairs_compared": checked_pairs,
        "issues": issues[:5],
        "note": "sec-exec vs detail phải đồng nhất; 2 số khác năm không tính là mâu thuẫn",
    }


def verify_temporal_alignment(req, html):
    """REQ-034: Số liệu theo năm trong narrative phải khớp data file đúng năm.

    Chống trộn năm: 'doanh thu 2024 = 30.000' khi data 2024 = 22.905 → FAIL.
    Chart years phải khớp financials years.
    """
    if not html:
        return False, {"error": "no html"}
    fin = _load_json_rel(req["verification"].get("data_file", "data/financials.json"))
    if not fin:
        return False, {"error": f"financials.json not found: {req['verification'].get('data_file')}"}

    issues = []
    checked = 0

    # 1. Narrative claims with explicit year (năm có thể đứng TRƯỚC keyword
    #    "năm 2025 doanh thu..." HOẶC SAU số "...30,699 tỷ (FY2025)")
    text = _narrative_text(html)
    metric_kws = {
        "revenue_ty": [r"doanh thu", r"revenue"],
        "npatmi_ty": [r"lợi nhuận ròng", r"lợi nhuận sau thuế", r"LNST", r"npatmi"],
        "eps_vnd": [r"EPS"],
    }
    NO_PCT_UNIT = {"revenue_ty", "npatmi_ty", "eps_vnd"}
    for field, kws in metric_kws.items():
        gt = fin.get(field)
        if not isinstance(gt, dict):
            continue
        for kw in kws:
            pat = re.compile(kw + r"[^0-9]{0,80}?(\d[\d.,]*)\s*(nghìn tỷ|tỷ|tỉ|triệu|tr)?", re.I)
            for m in pat.finditer(text):
                claimed = _normalize_number(m.group(1))
                unit = m.group(2) or ""
                if claimed is None:
                    continue
                # Skip year-as-value / tiny unitless numbers
                if 2000 <= claimed <= 2099 and not unit:
                    continue
                if not unit and claimed < 20:
                    continue
                if unit == "%" and field in NO_PCT_UNIT:
                    continue
                scaled = _scale_to_tỷ(claimed, unit)
                # tìm năm trong ±60 chars quanh claim (trước hoặc sau số)
                ctx = text[max(0, m.start()-60):m.end()+60]
                ym = re.search(r"20\d\d", ctx)
                if not ym:
                    continue  # claim không gắn năm cụ thể — không verify được
                year = ym.group(0)
                if year not in gt:
                    continue
                truth = float(gt[year])
                if truth == 0:
                    continue
                checked += 1
                if abs(scaled - truth) / abs(truth) > 0.05:
                    issues.append(f"{field}[{year}]: narrative nói {scaled:,.0f}, data = {truth:,.1f} (>5%)")
            break  # one keyword per field

    # 2. Chart years vs financials years
    data_arrays = _extract_data_js_arrays(html)
    chart_years = data_arrays.get("years", [])
    gt_years = sorted(gt.keys())
    if chart_years:
        norm_chart = [str(int(float(y))) if isinstance(y, (int, float)) else str(y) for y in chart_years]
        if norm_chart and sorted(norm_chart) != [str(y) for y in gt_years]:
            issues.append(f"chart years {norm_chart} ≠ data years {gt_years}")

    passed = len(issues) == 0 and checked > 0
    return passed, {
        "checked": checked,
        "chart_years": chart_years,
        "data_years": gt_years,
        "issues": issues[:5],
        "note": "narrative claim theo năm phải khớp data đúng năm; CAGR baseline phải là năm đầu data",
    }


def verify_segment_check(req, html):
    """REQ-035: Segment breakdown phải có nguồn (segments.json/company_profile.json).

    Nếu sec-segment có % contribution hoặc revenue per segment → cần data source.
    Không có data → phải có marker 'ước tính'.
    """
    if not html:
        return False, {"error": "no html"}
    seg_text = extract_section_text(html, "sec-segment")
    if not seg_text:
        return True, {"note": "no sec-segment — nothing to check"}

    # Quantitative segment claims?
    has_numbers = bool(re.search(r"\d[\d.,]*\s*(?:%|tỷ|tỉ|triệu)", seg_text))
    if not has_numbers:
        return True, {"note": "sec-segment present but no quantitative breakdown"}

    # Source: segments.json / company_profile.json / financials.json segment keys
    segment_source = None
    for cand in ("segments.json", "data/segments.json", "company_profile.json"):
        d = _load_json_rel(cand)
        if d is not None:
            blob = json.dumps(d, ensure_ascii=False).lower()
            if any(k in blob for k in ("segment", "mảng", "cơ cấu", "contribution", "doanh thu theo")):
                segment_source = cand
                break
    # fallback: verified-dashboard-data.json may carry segments
    if not segment_source:
        d = _load_json_rel("verified-dashboard-data.json")
        if d and isinstance(d, dict) and any(k in json.dumps(d).lower() for k in ("segment", "contribution")):
            segment_source = "verified-dashboard-data.json"

    if not segment_source:
        # no data → numbers must be flagged as estimate
        has_estimate = bool(re.search(r"ước tính|giả định|estimate|theo công bố|khoảng", seg_text, re.I))
        if not has_estimate:
            return False, {
                "error": "segment numbers without segment data source AND without 'ước tính' marker",
                "segment_text": seg_text[:200],
                "hint": "phase1 phải tạo segments.json; nếu không có data → ghi 'ước tính'",
            }
        return True, {"note": "segment numbers flagged as estimate — acceptable"}

    return True, {"segment_source": segment_source, "note": "segment data source found"}


def verify_cagr_recompute(req, html):
    """REQ-036: CAGR claims phải recompute từ financials.json (±2%).

    Chống bịa CAGR: không chỉ keyword-check mà tính thật từ data.
    CAGR = (last/first)^(1/(n-1)) - 1. So với mọi claim 'CAGR X%'.
    """
    if not html:
        return False, {"error": "no html"}
    fin = _load_json_rel(req["verification"].get("data_file", "data/financials.json"))
    if not fin:
        return False, {"error": f"financials.json not found: {req['verification'].get('data_file')}"}

    text = _narrative_text(html)
    claims = _find_numeric_claims(text, ["CAGR", "tăng trưởng kép", "compound annual"], window=60)
    if not claims:
        # vacuous-pass guard: if "CAGR" mentioned without number → FAIL; absent → PASS note
        if re.search(r"CAGR|tăng trưởng kép", text, re.I):
            return False, {"error": "CAGR mentioned without numeric claim — cannot verify"}
        return True, {"note": "no CAGR claim in narrative"}

    def _claim_metric(ctx):
        """Xác định claim CAGR nói về metric nào từ ngữ cảnh."""
        c = ctx.lower()
        if any(k in c for k in ("doanh thu", "revenue")):
            return "revenue_ty"
        if any(k in c for k in ("lợi nhuận", "lnst", "npat", "profit")):
            return "npatmi_ty"
        return None  # không rõ → so với mọi field

    issues = []
    checked = 0
    for field in req["verification"].get("fields", ["revenue_ty", "npatmi_ty"]):
        gt = fin.get(field)
        if not isinstance(gt, dict) or len(gt) < 2:
            continue
        years = sorted(int(y) for y in gt.keys())
        first, last = str(years[0]), str(years[-1])
        v0, v1 = float(gt[first]), float(gt[last])
        if v0 <= 0:
            continue
        n = len(years)
        cagr = (v1 / v0) ** (1 / (n - 1)) - 1
        cagr_pct = cagr * 100
        tolerance = req["verification"].get("tolerance_pct", 2)
        for c in claims:
            claim_metric = _claim_metric(c["context"])
            if claim_metric is not None and claim_metric != field:
                continue  # claim này thuộc metric khác — không so với field này
            claim_pct = c["value"]
            diff = abs(claim_pct - cagr_pct)
            # relative tolerance, floor 1.0pp cho CAGR nhỏ
            tol_pp = max(tolerance, abs(cagr_pct) * tolerance / 100)
            checked += 1
            if diff > tol_pp:
                issues.append(
                    f"CAGR claim {claim_pct:.1f}% ≠ recomputed {cagr_pct:.1f}% for {field} ({first}-{last}, lệch {diff:.1f}pp > {tol_pp:.1f}pp)"
                )

    passed = len(issues) == 0 and checked > 0
    return passed, {
        "cagr_claims_found": len(claims),
        "claims": [c["context"] for c in claims[:5]],
        "checked": checked,
        "issues": issues[:5],
        "recompute_basis": "financials.json first→last year",
    }


def verify_tech_recompute(req, html):
    """REQ-037: Tech Score + Verdict phải khớp technical_active.json (±2).

    Chống bịa tech score: report score phải bằng data file score. Verdict phải
    tương ứng dấu score (≥+3 BUY side, ≤-3 SELL side, giữa NEUTRAL).
    """
    if not html:
        return False, {"error": "no html"}
    tech = _load_json_rel("technical_active.json")
    if not tech:
        vdd = _load_json_rel("verified-dashboard-data.json")
        tech = vdd.get("technical") if vdd and isinstance(vdd, dict) else None
    if not tech:
        return False, {"error": "technical_active.json / verified-dashboard-data.json.technical not found — thiếu nguồn"}

    data_score = tech.get("tech_score")
    data_verdict = (tech.get("verdict") or "").upper()
    scale_min = tech.get("scale_min", -6)
    scale_max = tech.get("scale_max", 6)
    if data_score is None:
        return False, {"error": "tech data file missing tech_score"}

    # Extract report tech score from sec-tech (formats: "2/6", "Tech Score 2", "Điểm kỹ thuật 2")
    tech_text = extract_section_text(html, "sec-tech")
    m = re.search(r"([-+]?\d+)\s*/\s*" + re.escape(str(scale_max)), tech_text) if tech_text else None
    if not m:
        m = re.search(r"(?:tech score|điểm kỹ thuật|score)[^\d-]{0,20}([-+]?\d+)", tech_text or "", re.I)
    if not m:
        return False, {"error": "no tech score number found in sec-tech"}

    report_score = int(m.group(1))
    issues = []
    if abs(report_score - data_score) > 2:
        issues.append(f"report Tech Score {report_score}/{scale_max} ≠ data {data_score}/{scale_max} (lệch >2)")

    # Verdict sign consistency
    report_verdict_m = re.search(r"(STRONG SELL|SELL|NEUTRAL|BUY|STRONG BUY)", tech_text or "", re.I)
    report_verdict = report_verdict_m.group(1).upper() if report_verdict_m else ""
    def verdict_side(v):
        v = v.upper()
        if "SELL" in v:
            return "sell"
        if "BUY" in v:
            return "buy"
        return "neutral"
    if report_verdict:
        rv_side = verdict_side(report_verdict)
        dv_side = verdict_side(data_verdict)
        if rv_side != dv_side:
            issues.append(f"report verdict '{report_verdict}' ≠ data verdict '{data_verdict}'")
        # scale consistency: score ≥ +3 → BUY; ≤ -3 → SELL; else NEUTRAL acceptable
        if report_score >= 3 and rv_side == "sell":
            issues.append(f"score +{report_score} nhưng verdict '{report_verdict}' (SELL side) — mâu thuẫn")
        if report_score <= -3 and rv_side == "buy":
            issues.append(f"score {report_score} nhưng verdict '{report_verdict}' (BUY side) — mâu thuẫn")

    passed = len(issues) == 0
    return passed, {
        "data_tech_score": data_score,
        "report_tech_score": report_score,
        "data_verdict": data_verdict,
        "report_verdict": report_verdict,
        "issues": issues,
    }


def verify_claim_basis(req, html):
    """REQ-038: Superlative/comparative claims phải có basis (số liệu/nguồn gần đó).

    Chống claim rỗng: 'dẫn đầu thị trường' không kèm số/nguồn → FAIL.
    """
    if not html:
        return False, {"error": "no html"}
    text = _narrative_text(html)

    superlatives = [
        r"dẫn đầu", r"lớn nhất", r"cao nhất", r"thấp nhất", r"nhanh nhất", r"tốt nhất",
        r"top\s*\d", r"số\s*1", r"duy nhất", r"vượt trội", r"đứng đầu", r"leading", r"dominant",
        r"chiếm\s*ưu thế", r"mạnh nhất",
    ]
    issues = []
    found = 0
    for pat in superlatives:
        for m in re.finditer(pat, text, re.I):
            found += 1
            ctx = text[max(0, m.start()-80):m.end()+200]
            has_basis = bool(re.search(r"\d[\d.,]*\s*(?:%|tỷ|tỉ|triệu|x)|ref-\d|BCTC|vnstock|data", ctx))
            if not has_basis:
                issues.append(f"claim '{m.group(0)}' không có số liệu/nguồn hỗ trợ trong ±200 chars: ...{ctx.strip()[:120]}...")

    # comparative claims vs peer: "cao hơn/thấp hơn X" needs a number
    for m in re.finditer(r"(?:cao|thấp|nhiều|ít)\s+hơn[^.%0-9]{0,40}?(\d[\d.,]*)\s*(?:%|x|tỷ|tỉ|triệu)", text, re.I):
        found += 1
        ctx = text[max(0, m.start()-80):m.end()+150]
        has_basis = bool(re.search(r"ref-\d|BCTC|vnstock|peers\.json|data|ước tính", ctx, re.I))
        if not has_basis:
            issues.append(f"so sánh '{m.group(1)}' không có nguồn gần đó: ...{ctx.strip()[:120]}...")

    passed = len(issues) == 0
    return passed, {
        "superlative_claims_found": found,
        "unbased_claims": issues[:5],
    }


def verify_industry_claim(req, html):
    """REQ-039: Claim về ngành (thị phần, quy mô thị trường, tăng trưởng ngành)
    phải cite nguồn. Chống bịa số ngành.
    """
    if not html:
        return False, {"error": "no html"}
    text = _narrative_text(html)

    industry_kws = [
        r"thị phần", r"quy mô thị trường", r"tăng trưởng ngành", r"toàn ngành",
        r"thị trường\s+(?:xây dựng|bán lẻ|ngân hàng|thép|bất động sản|chứng khoán|sữa|vàng|dược)",
        r"market share", r"industry growth", r"market size",
    ]
    source_kws = [
        r"báo cáo", r"công bố", r"ước tính", r"theo\s+", r"nghiên cứu", r"khảo sát",
        r"ref-\d", r"statista", r"fiinpro", r"world bank", r"imf", r"vietnam report",
        r"bộ xây dựng", r"gso", r"tổng cục thống kê", r"vneconomy", r"vir", r"cafef",
    ]
    issues = []
    found = 0
    for kw in industry_kws:
        for m in re.finditer(kw, text, re.I):
            ctx = text[max(0, m.start()-60):m.end()+200]
            has_number = bool(re.search(r"\d[\d.,]*\s*%?", ctx))
            if not has_number:
                continue  # mention without figure — not a claim
            found += 1
            if not re.search("|".join(source_kws), ctx, re.I):
                issues.append(f"industry claim '{m.group(0)}' không có nguồn: ...{ctx.strip()[:130]}...")

    passed = len(issues) == 0
    return passed, {
        "industry_claims_with_figures": found,
        "uncited_claims": issues[:5],
    }


def verify_identity(req, html):
    """REQ-040: Ticker + company name khớp target; không nhầm ticker khác.

    Ticker lạ trong narrative (ngoài sec-peer/sec-source) → FAIL.
    """
    if not html:
        return False, {"error": "no html"}
    profile = _load_json_rel("company_profile.json")
    company_name = None
    if profile and isinstance(profile, dict):
        company_name = profile.get("company_name") or profile.get("organ_name")

    issues = []
    text = extract_all_text(html)

    # 1. Target ticker present
    if TICKER != "UNKNOWN" and not re.search(rf"\b{TICKER}\b", text):
        issues.append(f"report không nhắc ticker {TICKER}")

    # 2. Company name present (fuzzy: first word of name)
    if company_name:
        name_words = [w for w in company_name.replace("JSC", "").replace("Corp", "").split() if len(w) > 3]
        if name_words and not any(w.lower() in text.lower() for w in name_words[:2]):
            issues.append(f"report không nhắc company name '{company_name}'")

    # 3. Foreign tickers outside allowed sections
    allowed_sections = {"sec-peer", "sec-source", "sec-glossary", "sec-analyst"}
    foreign = []
    for ticker in _KNOWN_TICKERS:
        if ticker == TICKER:
            continue
        for m in re.finditer(rf"\b{ticker}\b", html):
            # which section contains this occurrence?
            before = html[:m.start()]
            sec_open = list(re.finditer(r'<section[^>]*id="(sec-[a-z0-9-]+)"', before))
            sec = sec_open[-1].group(1) if sec_open else "pre-section"
            if sec not in allowed_sections:
                foreign.append((ticker, sec))
                break  # one hit per ticker is enough
    if foreign:
        issues.append(f"ticker khác xuất hiện ngoài peer/source: {foreign[:5]}")

    passed = len(issues) == 0
    return passed, {
        "ticker": TICKER,
        "company_name": company_name,
        "foreign_tickers": foreign[:5],
        "issues": issues,
    }


def verify_news_window(req, html):
    """REQ-041: News phải trong 30 ngày (news_digest.json hoặc date trong HTML).

    Article cũ >30 ngày hoặc thiếu date (khi không phải source standard) → FAIL.
    """
    if not html:
        return False, {"error": "no html"}
    nd = _load_json_rel("news_digest.json")
    today = datetime.date.today()

    # Try digest articles
    if nd and isinstance(nd, dict) and nd.get("articles"):
        articles = nd["articles"]
        issues = []
        checked = 0
        for a in articles:
            ds = a.get("date") or a.get("published_at") or a.get("time") or ""
            if not ds:
                issues.append(f"article thiếu date: {(a.get('title') or '')[:60]}")
                continue
            m = re.search(r"(\d{4})-(\d{2})-(\d{2})", str(ds)) or re.search(r"(\d{2})/(\d{2})/(\d{4})", str(ds))
            if not m:
                issues.append(f"article date không parse được: {ds}")
                continue
            if m.group(1) and len(m.group(1)) == 4:  # YYYY-MM-DD
                d = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            else:  # DD/MM/YYYY
                d = datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            checked += 1
            age = (today - d).days
            if age > 30:
                issues.append(f"article {d.isoformat()} cũ {age} ngày (>30): {(a.get('title') or '')[:50]}")
        passed = len(issues) == 0
        return passed, {"articles_checked": checked, "issues": issues[:5]}

    # Fallback: dates in HTML (e.g. "31/07/2026")
    text = re.sub(r'<[^>]+>', ' ', html)
    dates = re.findall(r"\b(\d{2})/(\d{2})/(\d{4})\b|\b(\d{4})-(\d{2})-(\d{2})\b", text)
    parsed = []
    for d1, m1, y1, y2, m2, d2 in dates:
        if y1:
            parsed.append(datetime.date(int(y1), int(m1), int(d1)))
        else:
            parsed.append(datetime.date(int(y2), int(m2), int(d2)))
    if not parsed:
        return False, {"error": "no news_digest.json articles AND no dates in HTML — không verify được news window"}

    latest = max(parsed)
    oldest_ok = today - datetime.timedelta(days=30)
    stale = [p.isoformat() for p in parsed if p < oldest_ok]
    passed = len(stale) == 0
    return passed, {
        "dates_found": [p.isoformat() for p in sorted(set(parsed))],
        "stale_dates": stale,
        "note": "news_digest.json rỗng — fallback check date trong HTML",
    }


def verify_investment_amount(req, html):
    """REQ-042: investment_amount từ task-state phải xuất hiện trong narrative.

    task-state không có amount → PASS note. Có amount → narrative phải nhắc ±10%.
    """
    if not html:
        return False, {"error": "no html"}
    ts = _load_json_rel(".task-state/task-state.json")
    amount = None
    if ts and isinstance(ts, dict):
        amount = ts.get("investment_amount")
        if amount is None:
            # nested? some runs store under state
            for k, v in ts.items():
                if isinstance(v, dict) and "investment_amount" in v:
                    amount = v["investment_amount"]
                    break
    if amount is None:
        return True, {"note": "task-state không có investment_amount — không có gì để check"}

    text = extract_all_text(html)
    # normalize amount to number: 100000000, 100tr, 100 triệu, 1 tỷ
    target = float(amount)
    found = False
    # numeric form with commas
    if re.search(rf"{int(target):,}".replace(",", "[.,]"), text):
        found = True
    # "100 triệu" / "100tr" / "1 tỷ" forms
    for m in re.finditer(r"(\d[\d.,]*)\s*(triệu|tr|tỷ|tỉ)\b", text, re.I):
        v = _scale_to_tỷ(_normalize_number(m.group(1)), m.group(2))
        if v and abs(v * 1e9 - target) / target <= 0.10:
            found = True
            break

    if not found:
        return False, {
            "error": f"investment_amount={amount:,} không xuất hiện trong narrative (sec-scenario/insight)",
            "hint": "phase0 thu amount từ user; phase6 phải dùng đúng amount trong kịch bản",
        }
    return True, {"investment_amount": amount, "found_in_narrative": True}


def verify_source_freshness(req, html):
    """REQ-043: References phải có date/năm (standard sources được miễn).

    Ref rỗng date và không phải standard → FAIL. Ref năm < report năm - 2 → FAIL.
    """
    if not html:
        return False, {"error": "no html"}
    text = extract_all_text(html)
    if "ref-" not in text:
        return True, {"note": "no refs found (REQ-018 sẽ check số lượng)"}

    standard_kws = ["standard", "bctc", "filings", "disclosure", "báo cáo tài chính", "công bố"]
    # collect ref blocks: id="ref-N" ... up to next ref or 200 chars
    refs = []
    for m in re.finditer(r'id="ref-\d+"[^>]*>(.{0,220}?)', html, re.DOTALL):
        block = re.sub(r'<[^>]+>', ' ', m.group(1))
        block = re.sub(r'\s+', ' ', block).strip()
        refs.append(block)

    issues = []
    checked = 0
    report_year = datetime.date.today().year
    for b in refs:
        if not b:
            continue
        checked += 1
        has_year = bool(re.search(r"20\d\d", b))
        is_standard = any(kw in b.lower() for kw in standard_kws)
        if not has_year and not is_standard:
            issues.append(f"ref không date và không phải standard: '{b[:80]}'")
        elif has_year:
            ym = re.search(r"(20\d\d)", b)
            yr = int(ym.group(1))
            if yr < report_year - 2 and not is_standard:
                issues.append(f"ref năm {yr} stale (>2 năm so với {report_year}): '{b[:80]}'")

    passed = len(issues) == 0
    return passed, {
        "refs_checked": checked,
        "refs_total": len(refs),
        "issues": issues[:5],
        "note": "standard sources (BCTC, filings, disclosure) được miễn date",
    }


# ═══════════════════════════════════════════════════════════════
# MAIN VERIFIER
# ═══════════════════════════════════════════════════════════════

def main():
    if not os.path.exists(REQ_FILE):
        print(f"{RED}❌ requirements.yaml not found: {REQ_FILE}{NC}")
        sys.exit(2)

    with open(REQ_FILE) as f:
        req_data = yaml.safe_load(f)

    html = read_report()
    if not html and REPORT:
        print(f"{YELLOW}⚠️ Report not found: {REPORT} — running pre-build checks only{NC}")
    elif not REPORT:
        print(f"{YELLOW}⚠️ No report path — running pre-build checks only{NC}")

    # Evidence dir
    evidence_dir = os.path.join(os.path.dirname(REPORT or "."), ".task-state", "evidence")
    os.makedirs(evidence_dir, exist_ok=True)

    results = {"total": 0, "pass": 0, "fail": 0, "skip": 0, "details": []}
    fail_details = []

    print(f"\n{'='*60}")
    print(f"  INDEPENDENT VERIFIER — {TICKER}")
    print(f"  Report: {REPORT or '(pre-build)'}")
    print(f"  Requirements: {req_data['total']}")
    print(f"{'='*60}\n")

    for req in req_data["requirements"]:
        rid = req["id"]
        method = req["verification"]["method"]
        priority = req.get("priority", "medium")

        # Skip artifact checks if no report
        if not html and method in ("artifact_check", "section_map_check", "count_check",
                                    "content_depth_check", "section_content_check",
                                    "canvas_check", "div_balance_check", "valuation_sanity_check",
                                    "data_accuracy_check", "capex_accuracy_check",
                                    "valuation_recompute_check", "chart_data_accuracy_check",
                                    "external_claim_flag_check",
                                    "source_citation_check",
                                    "price_source_check",
                                    "drawdown_source_check",
                                    "peer_provenance_check",
                                    "cross_section_consistency_check",
                                    "temporal_alignment_check",
                                    "segment_check",
                                    "cagr_recompute_check",
                                    "tech_recompute_check",
                                    "claim_basis_check",
                                    "industry_claim_check",
                                    "identity_check",
                                    "news_window_check",
                                    "investment_amount_check",
                                    "source_freshness_check"):
            results["skip"] += 1
            print(f"  ⏭️  {rid} [{priority:8}] SKIP (no artifact)")
            continue

        # Run verification
        detail = {"id": rid, "text": req["text"][:60], "priority": priority, "method": method}
        passed = False
        evidence = {}

        try:
            if method == "command":
                passed, evidence = verify_command(req, html)
            elif method == "artifact_check":
                passed, evidence = verify_artifact_check(req, html)
            elif method == "section_map_check":
                passed, evidence = verify_section_map(req, html)
            elif method == "count_check":
                passed, evidence = verify_count_check(req, html)
            elif method == "content_depth_check":
                passed, evidence = verify_content_depth(req, html)
            elif method == "section_content_check":
                passed, evidence = verify_section_content(req, html)
            elif method == "canvas_check":
                passed, evidence = verify_canvas_check(req, html)
            elif method == "div_balance_check":
                passed, evidence = verify_div_balance(req, html)
            elif method == "valuation_sanity_check":
                passed, evidence = verify_valuation_sanity(req, html)
            elif method == "data_accuracy_check":
                passed, evidence = verify_data_accuracy(req, html)
            elif method == "capex_accuracy_check":
                passed, evidence = verify_capex_accuracy(req, html)
            elif method == "valuation_recompute_check":
                passed, evidence = verify_valuation_recompute(req, html)
            elif method == "chart_data_accuracy_check":
                passed, evidence = verify_chart_data_accuracy(req, html)
            elif method == "external_claim_flag_check":
                passed, evidence = verify_external_claim_flag(req, html)
            elif method == "chart_runtime_check":
                passed, evidence = verify_chart_runtime_check(req, html)
            elif method == "source_citation_check":
                passed, evidence = verify_source_citation(req, html)
            elif method == "price_source_check":
                passed, evidence = verify_price_source(req, html)
            elif method == "drawdown_source_check":
                passed, evidence = verify_drawdown_source(req, html)
            elif method == "peer_provenance_check":
                passed, evidence = verify_peer_provenance(req, html)
            elif method == "cross_section_consistency_check":
                passed, evidence = verify_cross_section_consistency(req, html)
            elif method == "temporal_alignment_check":
                passed, evidence = verify_temporal_alignment(req, html)
            elif method == "segment_check":
                passed, evidence = verify_segment_check(req, html)
            elif method == "cagr_recompute_check":
                passed, evidence = verify_cagr_recompute(req, html)
            elif method == "tech_recompute_check":
                passed, evidence = verify_tech_recompute(req, html)
            elif method == "claim_basis_check":
                passed, evidence = verify_claim_basis(req, html)
            elif method == "industry_claim_check":
                passed, evidence = verify_industry_claim(req, html)
            elif method == "identity_check":
                passed, evidence = verify_identity(req, html)
            elif method == "news_window_check":
                passed, evidence = verify_news_window(req, html)
            elif method == "investment_amount_check":
                passed, evidence = verify_investment_amount(req, html)
            elif method == "source_freshness_check":
                passed, evidence = verify_source_freshness(req, html)
            elif method == "all_requirements_pass":
                # Special: checked at end
                results["skip"] += 1
                continue
            else:
                evidence = {"error": f"unknown method: {method}"}
        except Exception as e:
            evidence = {"error": str(e)}

        # Write evidence file
        evidence_file = os.path.join(evidence_dir, f"{rid}.json")
        evidence_data = {
            "requirement_id": rid,
            "text": req["text"],
            "priority": priority,
            "method": method,
            "status": "pass" if passed else "fail",
            "evidence": evidence,
            "verified_at": datetime.datetime.now().isoformat(),
            "artifact": REPORT,
        }
        with open(evidence_file, "w") as f:
            json.dump(evidence_data, f, indent=2, ensure_ascii=False)

        results["total"] += 1
        if passed:
            results["pass"] += 1
            status_color = GREEN + "✅ PASS" + NC
        else:
            results["fail"] += 1
            status_color = RED + "❌ FAIL" + NC
            fail_details.append((rid, req["text"][:80], evidence))

        print(f"  {status_color} {rid} [{priority:8}] {req['text'][:55]}")

    # REQ-021: all requirements pass
    all_pass = results["fail"] == 0
    results["total"] += 1
    # PATCH P0-4: write REQ-021 evidence with provenance binding (was MISSING → mutation
    # harness couldn't confirm detection; also a state-binding risk if deploy could use stale
    # or cross-run evidence). Bind to current run, artifact hash, post-validation timestamp.
    req021_evidence = {
        "requirement_id": "REQ-021",
        "text": "KHÔNG deploy nếu bất kỳ REQ nào FAIL. Hook PreToolUse chặn vercel deploy.",
        "priority": "critical",
        "method": "all_requirements_pass",
        "status": "pass" if all_pass else "fail",
        "evidence": {
            "source_run_id": os.environ.get("EVAL_RUN_ID", f"verifier-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"),
            "source_artifact": REPORT,
            "source_artifact_sha256": hashlib.sha256(open(REPORT, "rb").read()).hexdigest()[:16] if REPORT and os.path.exists(REPORT) else None,
            "evidence_generated_after_validation": True,
            "unresolved_required_failures": results["fail"],
            "all_requirements_pass": all_pass,
            "requirement_state_at_eval": {rid: st for rid, st in [(d.get("requirement_id") or d.get("id"), d.get("status")) for d in [json.load(open(os.path.join(evidence_dir, f))) for f in os.listdir(evidence_dir) if f.startswith("REQ-") and f.endswith(".json")]] if st},
        },
    }
    with open(os.path.join(evidence_dir, "REQ-021.json"), "w") as f:
        json.dump(req021_evidence, f, indent=2, ensure_ascii=False)
    if all_pass:
        results["pass"] += 1
        print(f"\n  {GREEN}✅ PASS{NC} REQ-021 [critical] All requirements pass — deploy allowed")
    else:
        results["fail"] += 1
        print(f"\n  {RED}❌ FAIL{NC} REQ-021 [critical] {results['fail']} requirement(s) failed — BLOCKED deploy")

    # Summary
    recall = results["pass"] / results["total"] * 100 if results["total"] else 0
    print(f"\n{'='*60}")
    print(f"  VERDICT: {'PASS' if all_pass else 'FAIL'}")
    print(f"  Requirements: {results['pass']}/{results['total']} pass ({recall:.0f}% recall)")
    print(f"  Evidence: {evidence_dir}/")
    if fail_details:
        print(f"\n  {RED}FAILED REQUIREMENTS:{NC}")
        for rid, text, ev in fail_details:
            print(f"    {rid}: {text}")
            if ev:
                key_info = {k: v for k, v in ev.items() if k != "error" and v}
                if key_info:
                    print(f"      → {json.dumps(key_info, ensure_ascii=False)[:120]}")
    print(f"{'='*60}\n")

    # Write summary evidence
    summary_file = os.path.join(evidence_dir, "_summary.json")
    with open(summary_file, "w") as f:
        json.dump({
            "verified_at": datetime.datetime.now().isoformat(),
            "ticker": TICKER,
            "artifact": REPORT,
            "results": results,
            "requirement_recall_pct": round(recall, 1),
            "verdict": "PASS" if all_pass else "FAIL",
        }, f, indent=2, ensure_ascii=False)

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
