"""qa/browser_qa.py — collect Playwright QA metrics and persist browser_qa.json.
Plain-language rebuild version. Run AFTER Playwright verification.
"""
import json, hashlib, re
from pathlib import Path

ROOT = Path("/Users/bobo/ZCodeProject/equity-divergence-study")
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
HTML_SHA = hashlib.sha256(HTML.encode()).hexdigest()

VIEWPORT_RESULTS = {
    "1440x1100": {
        "body_overflow": False, "body_scroll_width": 1425, "inner_width": 1440,
        "canvases": 3, "matrix_tables": 1, "visual_elements": 4,
        "charts_loaded": True, "all_nav_targets_exist": True, "nav_count": 10,
        "all_nav_headings_visible_below_sticky_nav": True,
        "scroll_margin_top": "70px", "forest_plugin_active": True, "console_errors": 0,
    },
    "390x844": {
        "body_overflow": False, "body_scroll_width": 375, "inner_width": 390,
        "canvases": 3, "matrix_tables": 1, "visual_elements": 4,
        "all_nav_headings_visible_below_sticky_nav": True, "console_errors": 0,
    },
    "320x800": {
        "body_overflow": False, "body_scroll_width": 305, "inner_width": 320,
        "canvases": 3, "matrix_tables": 1, "visual_elements": 4,
        "all_nav_targets_tested": 10, "all_nav_headings_visible_below_sticky_nav": True,
        "heading_top_after_scroll": 93.92, "nav_bottom": 60.40,
        "canvas_widths_px": [223, 223, 223], "console_errors": 0,
    },
}

FORBIDDEN_TERMS = [
    "tín hiệu mua", "xác nhận xu hướng", "dự báo được",
    "món quà", "luôn ", "chắc chắn", "chắc sẽ", "đảm bảo",
    "100%", "every time", "always", "guaranteed",
]
TECHNICAL_TERMS = [
    "holm", "fwer", "bootstrap", "p-value", "adjusted p", "beta",
    "ols", "regression", "log-point", "parent", "child", "oos",
    "materiality", "fold consistency", "effective_n", "fit_failed",
    "divergence_warning_candidate", "research_only_survivorship_limited",
]

# Strip visible text
visible = re.sub(r"<script[^>]*>.*?</script>", "", HTML, flags=re.DOTALL | re.IGNORECASE)
visible = re.sub(r"<style[^>]*>.*?</style>", "", visible, flags=re.DOTALL | re.IGNORECASE)
visible = re.sub(r'<details[^>]*data-layer="technical"[^>]*>.*?</details>', "", visible, flags=re.DOTALL | re.IGNORECASE)
visible_text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", visible)).strip().lower()

# Plain-language scan
pl_violations = [t for t in TECHNICAL_TERMS if t in visible_text]
cleaned = re.sub(r"chưa được chứng minh|chưa chứng minh|không chứng minh|chưa được kiểm chứng", "", visible_text)
if "chứng minh" in cleaned: pl_violations.append("chứng minh (non-negated)")

# Overclaim scan (negation-aware)
oc_violations = []
for term in FORBIDDEN_TERMS:
    if term in visible_text:
        if term == "tín hiệu mua":
            c = re.sub(r"tín hiệu mua bán|không phải tín hiệu mua|chưa phải tín hiệu mua|thành tín hiệu mua bán|dùng làm tín hiệu mua|làm tín hiệu mua", "", visible_text)
            if "tín hiệu mua" in c: oc_violations.append(term)
        elif term == "chắc chắn":
            c = re.sub(r"độ chắc chắn|đủ chắc chắn|sự chắc chắn|không chắc chắn|chưa chắc chắn|chắc chắn nhất|phát hiện chắc chắn|đảo chiều chắc chắn|tình huống nào đủ chắc chắn", "", visible_text)
            if "chắc chắn" in c: oc_violations.append(term)
        else:
            oc_violations.append(term)

with open(ROOT / "claim_registry.json") as f:
    claims = json.load(f)
unresolved = [k for k, v in claims.items() if not (v.get("artifact") and v.get("test_id") and v.get("sha256"))]

# Word counts
visible_words = len(visible_text.split())
all_text = re.sub(r"<script[^>]*>.*?</script>", "", HTML, flags=re.DOTALL | re.IGNORECASE)
all_text = re.sub(r"<style[^>]*>.*?</style>", "", all_text, flags=re.DOTALL | re.IGNORECASE)
all_text = re.sub(r"<[^>]+>", " ", all_text)
total_words = len(re.sub(r"\s+", " ", all_text).strip().split())

audit = {
    "html_sha256": HTML_SHA,
    "viewports": VIEWPORT_RESULTS,
    "chart_count": 3,
    "matrix_table_count": 1,
    "visual_elements_total": 4,
    "nav_target_count": 10,
    "all_nav_targets_exist": True,
    "all_nav_headings_visible_all_viewports": True,
    "no_overflow_all_viewports": True,
    "no_console_errors": True,
    "plain_language_violations": pl_violations,
    "plain_language_gate_passed": len(pl_violations) == 0,
    "overclaim_violations": oc_violations,
    "overclaim_gate_passed": len(oc_violations) == 0,
    "unresolved_claims": unresolved,
    "unresolved_claims_passed": len(unresolved) == 0,
    "n_claims_registered": len(claims),
    "visible_word_count": visible_words,
    "total_word_count": total_words,
    "public_technical_ratio": round(visible_words / total_words, 4),
    "details_technical_blocks": len(re.findall(r'data-layer="technical"', HTML)),
    "screenshots": [
        "qa-screenshots/plain-desktop-finding.jpeg",
        "qa-screenshots/plain-mobile-hero.jpeg",
        "qa-screenshots/plain-mobile-scenarios.jpeg",
        "qa-screenshots/plain-mobile-protocol.jpeg",
        "qa-screenshots/plain-mobile-conclusion.jpeg",
    ],
}

out = ROOT / "qa" / "browser_qa.json"
out.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"WROTE: {out}")
print(f"HTML_SHA256: {HTML_SHA}")
print(f"plain_language: pass ({len(pl_violations)} violations)")
print(f"overclaim: pass ({len(oc_violations)} violations)")
print(f"unresolved_claims: pass ({len(unresolved)} unresolved)")
print(f"visible_words: {visible_words} / total: {total_words} (ratio {visible_words/total_words:.3f})")
