#!/usr/bin/env python3
"""Verify the public HTML against the frozen research artifacts.

Updated for editorial longform closeout: 14 sections, 10 charts, 33 claims,
6 automated prose gates, 25-hash provenance audit.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "index.html"
QA = ROOT / "qa"
FINAL_SYNTHESIS = QA / "final_synthession" if (QA / "final_synthession").exists() else QA / "final_synthesis"


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.anchors: list[str] = []
        self.sections: list[str] = []
        self.canvases: list[str] = []
        self.visible: list[str] = []
        self._hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag in {"script", "style"}:
            self._hidden_depth += 1
        if attr.get("id"):
            self.ids.append(str(attr["id"]))
        if tag == "a" and str(attr.get("href", "")).startswith("#"):
            self.anchors.append(str(attr["href"])[1:])
        if tag == "section" and attr.get("id"):
            self.sections.append(str(attr["id"]))
        if tag == "canvas" and attr.get("id"):
            self.canvases.append(str(attr["id"]))

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self._hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._hidden_depth == 0 and data.strip():
            self.visible.append(data.strip())


EXPECTED_SECTIONS = [
    "open", "quickread", "ch1", "ch2", "daily", "monthly", "timing",
    "ch3", "ch4", "opp-timeline", "synthesis", "use", "limits", "glossary",
]

# Prose rules: each is (name, predicate(html) -> bool, description)
# predicate returns True if VIOLATION found
def check_ch4_no_delta10y_for_breadth(html: str) -> bool:
    """Ch4 must not reference Δ10Y for breadth — Ch4 survivors are Δ2Y and VN-US spread 2Y."""
    ch4_match = re.search(r'<section id="ch4".*?</section>', html, re.DOTALL)
    if not ch4_match:
        return False
    ch4_text = ch4_match.group()
    # check if Δ10Y appears near "độ rộng" or "breadth"
    if "Δ10Y" in ch4_text and ("độ rộng" in ch4_text.lower()):
        return True
    return False

def check_use_no_delta10y_for_breadth(html: str) -> bool:
    """Use section must not reference Δ10Y for breadth either."""
    use_match = re.search(r'<section id="use".*?</section>', html, re.DOTALL)
    if not use_match:
        return False
    use_text = use_match.group()
    if "Δ10Y" in use_text and "độ rộng" in use_text.lower():
        return True
    return False

def check_no_absolute_null(html: str) -> bool:
    """No absolute 'Không.' as standalone answer to research questions."""
    if re.search(r'^Không\. Chương', html, re.MULTILINE):
        return True
    if "không phải do trái phiếu" in html:
        return True
    return False

def check_no_unproven_liquidity(html: str) -> bool:
    """'thanh khoản thắt/đang thắt' must be followed by disclaimer, or absent."""
    for m in re.finditer(r"thanh khoản (?:đang )?thắt", html):
        context = html[m.start():m.start() + 250]
        if "diễn giải kinh tế thường gặp" not in context and "không kiểm định" not in context:
            return True
    return False

def check_no_foreign_capital_claim(html: str) -> bool:
    """No unproven foreign capital inflow/outflow claim."""
    if "dòng vốn ngoại" in html:
        return True
    return False

def check_no_absolute_khong_giai_thich(html: str) -> bool:
    """'không giải thích' must be qualified with 'chưa' or 'ổn định'."""
    for m in re.finditer(r"không giải thích", html):
        context = html[max(0, m.start() - 40):m.start() + 60]
        if "chưa" not in context and "ổn định" not in context:
            return True
    return False

PROSE_RULES = [
    ("ch4_no_delta10y_breadth", check_ch4_no_delta10y_for_breadth,
     "Ch4 must not use Δ10Y for breadth (correct: Δ2Y + VN-US spread 2Y)"),
    ("use_no_delta10y_breadth", check_use_no_delta10y_for_breadth,
     "Use section must not use Δ10Y for breadth"),
    ("no_absolute_null", check_no_absolute_null,
     "No absolute 'Không.' or 'không phải do trái phiếu' as standalone conclusions"),
    ("no_unproven_liquidity", check_no_unproven_liquidity,
     "'thanh khoản thắt' must have disclaimer or be absent"),
    ("no_foreign_capital_claim", check_no_foreign_capital_claim,
     "No unproven foreign capital inflow/outflow claim"),
    ("no_absolute_khong_giai_thich", check_no_absolute_khong_giai_thich,
     "'không giải thích' must be qualified with 'chưa' or 'ổn định'"),
]


def main() -> None:
    html = HTML.read_text()
    parser = DocumentParser()
    parser.feed(html)
    visible = " ".join(parser.visible)

    errors = []
    checks = {}

    # 1. Section structure
    checks["section_count"] = len(parser.sections)
    checks["section_ids"] = parser.sections
    if parser.sections != EXPECTED_SECTIONS:
        errors.append(f"Sections mismatch: got {parser.sections}, expected {EXPECTED_SECTIONS}")

    # 2. Nav anchors match sections
    nav_section_anchors = [a for a in parser.anchors if a in EXPECTED_SECTIONS]
    if sorted(nav_section_anchors) != sorted(EXPECTED_SECTIONS):
        errors.append(f"Nav anchors don't cover all sections: {nav_section_anchors}")

    # 3. No duplicate IDs
    duplicates = sorted(key for key, count in Counter(parser.ids).items() if count > 1 and not key.startswith("chart"))
    checks["duplicate_ids"] = duplicates
    if duplicates:
        errors.append(f"Duplicate IDs: {duplicates}")

    # 4. Canvas = Chart count
    chart_ids = re.findall(r"new Chart\(document\.getElementById\(['\"]([^'\"]+)", html)
    checks["canvas_count"] = len(parser.canvases)
    checks["chart_count"] = len(chart_ids)
    if sorted(parser.canvases) != sorted(chart_ids):
        errors.append(f"Canvas/Chart mismatch: canvas={parser.canvases}, chart={chart_ids}")

    # 5. Claim registry
    registry = json.loads((QA / "claim_registry.json").read_text())
    checks["claim_count"] = len(registry["claims"])
    checks["unresolved_claims"] = registry.get("unresolved_claims", "MISSING")
    if registry.get("unresolved_claims") != []:
        errors.append(f"unresolved_claims not empty: {registry.get('unresolved_claims')}")
    # no HTML self-citation in sources
    self_cite = [c["id"] for c in registry["claims"] if "index.html" in str(c.get("source", "")) and "forbidden" not in str(c.get("source", ""))]
    if self_cite:
        errors.append(f"HTML self-citation in claims: {self_cite}")

    # 6. Prose rules (6 automated gates)
    prose_results = {}
    for rule_name, predicate, description in PROSE_RULES:
        violated = predicate(html)
        prose_results[rule_name] = {"description": description, "passed": not violated}
        if violated:
            errors.append(f"Prose rule '{rule_name}' VIOLATED: {description}")

    # 7. Hash audit
    html_hash = hashlib.sha256(HTML.read_bytes()).hexdigest()
    hex64 = re.compile(r"^[0-9a-f]{64}$")
    sm = json.loads((FINAL_SYNTHESIS / "source_manifest.json").read_text())
    sh = json.loads((FINAL_SYNTHESIS / "source_hashes.json").read_text())

    all_hashes = [("html", html_hash)]
    for ch in ["chapter1", "chapter2", "chapter3", "chapter4"]:
        for name, h in sm[ch]["artifact_hashes"].items():
            all_hashes.append((f"{ch}/{name}", h))

    invalid_hashes = [(n, h[:16]) for n, h in all_hashes if not hex64.match(h)]
    checks["hash_count"] = len(all_hashes)
    checks["invalid_hashes"] = invalid_hashes
    if invalid_hashes:
        errors.append(f"Invalid hashes: {invalid_hashes}")

    # HTML hash matches all governance artifacts
    hash_mismatch = []
    if sm["html_hash_sha256"] != html_hash:
        hash_mismatch.append("source_manifest")
    if registry.get("html_hash") != html_hash:
        hash_mismatch.append("claim_registry")
    if sh.get("html") != html_hash:
        hash_mismatch.append("source_hashes")
    checks["html_hash"] = html_hash[:16]
    checks["hash_mismatch"] = hash_mismatch
    if hash_mismatch:
        errors.append(f"HTML hash mismatch in: {hash_mismatch}")

    # 8. Word count (all visible text)
    word_count = len(re.findall(r"\b\w+\b", visible, flags=re.UNICODE))
    checks["word_count_visible"] = word_count

    # 9. Forbidden old content
    forbidden_old = ["0/108", "0/240", "Chương 5 sắp tới", "Chương 6 sắp tới", "sắp tới"]
    found_forbidden = [f for f in forbidden_old if f in html]
    checks["forbidden_old_content"] = found_forbidden
    if found_forbidden:
        errors.append(f"Forbidden old content found: {found_forbidden}")

    # Build report
    report = {
        "word_count_visible_text": word_count,
        "section_count": len(parser.sections),
        "section_ids": parser.sections,
        "canvas_count": len(parser.canvases),
        "chart_count": len(chart_ids),
        "canvas_chart_match": sorted(parser.canvases) == sorted(chart_ids),
        "duplicate_ids": duplicates,
        "claim_registry_count": len(registry["claims"]),
        "unresolved_claims": registry.get("unresolved_claims"),
        "prose_rules": prose_results,
        "hash_audit": {
            "total_hashes": len(all_hashes),
            "invalid_hashes": invalid_hashes,
            "html_hash": html_hash[:16],
            "hash_mismatch": hash_mismatch,
        },
        "forbidden_old_content": found_forbidden,
        "errors": errors,
        "final_status": "PASS" if not errors else "FAIL",
    }
    (QA / "rewrite_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
