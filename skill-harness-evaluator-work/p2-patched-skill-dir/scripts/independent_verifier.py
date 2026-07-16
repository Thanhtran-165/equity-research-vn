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
SKILL_DIR = "/Users/bobo/ZCodeProject/skill-harness-evaluator-work/p2-patched-skill-dir"
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

# ═══════════════════════════════════════════════════════════════
# VERIFICATION METHODS (data-driven from requirements.yaml)
# ═══════════════════════════════════════════════════════════════

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
        has_oracle = "oracle" in body_text or "$ billions" in body_text or "usd billions" in body_text
        passed = not has_oracle
        return passed, {"no_placeholder": passed, "has_oracle": has_oracle}

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

    # Get capex from report JS DATA object
    js_capex_match = re.search(r'capex:\s*\[([\d.,\s]+)\]', html or "")
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
    candidates = []  # list of (value, is_primary, is_projection)
    for m in pat.finditer(text):
        raw = m.group(1).replace(",", "")
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
    # Rule 4a: multiple distinct non-projection → need primary marker
    marked = [(v, ip) for v, ip in non_projection if ip]
    if len(marked) >= 1:
        return marked[0][0]
    # Rule 4b: multiple distinct, no marker → AMBIGUOUS
    return None  # caller will report AMBIGUOUS_PRIMARY_MULTIPLE

def verify_valuation_recompute(req, html):
    """Recompute PE/PB/Graham from data, compare to report values."""
    import json as _json, math as _math
    work_dir = os.path.dirname(REPORT) if REPORT else "."
    fin_path = os.path.join(work_dir, "data/financials.json")

    if not os.path.exists(fin_path):
        return False, {"error": "financials.json not found"}

    with open(fin_path) as f:
        fin = _json.load(f)

    # PATCH P2-hardened: NO company-specific defaults. Missing data → FAIL, not a fallback guess.
    price = fin.get("overview", {}).get("current_price")
    eps_2025 = fin.get("eps_vnd", {}).get("2025")
    if price is None or eps_2025 is None:
        return False, {"error": "missing price or eps_2025 in financials.json (no default fallback)"}
    full_text = extract_all_text(html) if html else ""
    # PATCH P2-hardened: SEMANTIC SCOPE — collect candidates from ALL primary-valuation sections.
    # The current P/E can appear in sec-hero (KPI card), sec-valuation, or sec-exec.
    # Combine all into one candidate pool; the ambiguity rule handles the rest.
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
            computed = price / eps_2025 if eps_2025 else None
            report_val = _extract_primary_multiple(val_text, "P/?E", computed, tolerance)
        elif name == "PB":
            # PATCH P2-hardened: NO default equity. Missing → FAIL.
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

        # Get report JS value
        js_match = re.search(rf'{arr_name}:\s*\[([\d.,\s]+)\]', html or "")
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
    """Check that external claims (WCM LN, MCH DT, store count) are flagged as estimates.
    PATCH P1-2 (REQ-027): INVERTED + ADJACENCY logic. The old code passed if ANY flag word
    existed ANYWHERE in the document — so a claim with a flag far away (or a flag for a
    different claim) masked an unflagged claim. Now: each matching claim MUST have a flag
    within an ADJACENT context window, else FAIL."""
    text = extract_all_text(html) if html else ""
    patterns = req["verification"].get("patterns", [])
    must_flag = req["verification"].get("must_flag", "ước tính|estimate")
    adjacent_window = req["verification"].get("adjacent_window", 200)  # chars each side

    unflagged_claims = []
    total_claims = 0
    for pattern in patterns:
        for m in re.finditer(pattern, text, re.I):
            total_claims += 1
            ctx = text[max(0, m.start()-adjacent_window):m.end()+adjacent_window]
            if not re.search(must_flag, ctx, re.I):
                unflagged_claims.append({"pattern": pattern, "match": m.group(0)[:40]})
    # No external claims → PASS (nothing to flag)
    # Claims present → PASS only if EVERY claim has an adjacent flag
    passed = (total_claims == 0) or (len(unflagged_claims) == 0)
    return passed, {"external_claims_found": total_claims,
                    "unflagged": unflagged_claims[:3],
                    "adjacent_window": adjacent_window,
                    "patch_note": "P1-2: inverted + adjacency — flag must be near each claim"}


def verify_div_balance(req, html):
    """Check div open = div close."""
    if not html:
        return False, {"error": "no html"}
    opens = len(re.findall(r"<div[ >]", html))
    closes = len(re.findall(r"</div>", html))
    passed = opens == closes
    return passed, {"opens": opens, "closes": closes}


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
                                    "external_claim_flag_check"):
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
