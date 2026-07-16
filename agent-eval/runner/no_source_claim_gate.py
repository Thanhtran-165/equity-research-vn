#!/usr/bin/env python3
"""
no_source_claim_gate.py — Pre-phase6 no-source external claim prevention (Branch B).

PURPOSE (owner directive 2026-07-14):
  Shadow Batch 1 found that when source-packs lack news/events data, the agent
  fills gaps from model memory — writing factual claims ("200,000 điểm bán")
  without source citations. REQ-027 catches this at final verification, but the
  owner's directive is to fail EARLIER: prevent the claim from rendering as
  confirmed fact in the first place.

  This gate scans the phase 5 (news/qualitative) output BEFORE phase 6 renders
  the dashboard. If a claim has factual specificity (numbers + entity) but no
  provenance in the source-pack, the gate either:
    1. Requires the agent to add an "ước tính" / "external" flag, or
    2. Requires the agent to omit the claim (structured abstention)

  This is a phase-local gate (like content_depth_gate), with bounded retry.

Claim patterns that need provenance:
  - store/point-of-sale counts: "điểm bán", "cửa hàng", "điểm"
  - market share: "thị phần"
  - capacity: "công suất"
  - expansion plans: "kế hoạch mở rộng", "dự kiến"
  - M&A: "thương vụ", "mua lại"
  - recent events: "vừa qua", "gần đây", "mới đây"
"""
import re

# Factual claim patterns that require source provenance
CLAIM_PATTERNS = [
    (r"\d+[\.,]?\d*\s*(?:nghìn|triệu|tỷ|billion|million)?\s*điểm\s+bán", "point_of_sale_count"),
    (r"\d+[\.,]?\d*\s*(?:nghìn|triệu|tỷ)?\s*cửa\s+hàng", "store_count"),
    (r"\d+[\.,]?\d*\s*%\s*thị\s+phần", "market_share"),
    (r"thị\s+phần\s+\d+[\.,]?\d*\s*%", "market_share"),
    (r"công\s+xuất\s+\d+", "capacity"),
    (r"\d+[\.,]?\d*\s*(?:MW|GW|triệu tấn|nghìn tấn)", "capacity_numeric"),
    (r"kế\s+hoạch\s+mở\s+rộng[^.]{10,60}", "expansion_plan"),
    (r"dự\s+kiến\s+(?:mở|đạt|đạt được|tăng)", "expansion_projection"),
    (r"thương\s+vụ\s+(?:mua|mua lại|sáp nhập)", "ma_event"),
]

# Provenance flags that make a claim acceptable
PROVENANCE_FLAGS = [
    r"ước\s+tính", r"theo\s+(?:nguồn|báo cáo|CTC|BCTC|vcsc|vnds|vnstock)",
    r"\[?\(?(?:source|nguồn|trích dẫn)\]?\)?[:\s]",
    r"id=[\"']?ref-\d+", r"#ref-\d+", r"ref-\d+",
    r"theo\s+\w+", r"reported\s+by", r"according\s+to",
]


def scan_claims(text):
    """Scan text for factual claims without provenance.

    Returns list of {pattern, match, context, has_provenance} dicts.
    """
    findings = []
    for pattern, claim_type in CLAIM_PATTERNS:
        for m in re.finditer(pattern, text, re.I):
            # Check ±200 chars for provenance flag
            window_start = max(0, m.start() - 200)
            window_end = min(len(text), m.end() + 200)
            window = text[window_start:window_end]
            has_provenance = any(re.search(flag, window, re.I) for flag in PROVENANCE_FLAGS)
            ctx = text[max(0, m.start()-40):m.end()+40].strip()
            findings.append({
                "claim_type": claim_type,
                "match": m.group()[:60],
                "context": ctx[:120],
                "has_provenance": has_provenance,
            })
    return findings


def check_no_source_claims(html_text, source_pack_dir=None):
    """Check phase 5/6 output for unprovenanced external claims.

    Returns:
      passed: bool — True if no unprovenanced claims found
      findings: list of unprovenanced claims
      feedback: str — retry feedback if failed
    """
    # Extract text from HTML (strip tags for claim scanning)
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", html_text, flags=re.DOTALL | re.I)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    findings = scan_claims(text)
    unprovenanced = [f for f in findings if not f["has_provenance"]]

    passed = len(unprovenanced) == 0

    feedback = ""
    if not passed:
        lines = [
            f"NO_SOURCE_CLAIM_GATE: found {len(unprovenanced)} factual claim(s) without source provenance.",
            "Each external claim (store counts, market share, capacity, expansion plans, M&A) MUST either:",
            "  1. Have a provenance flag nearby (ước tính, [source], theo báo cáo, ref-N), OR",
            "  2. Be removed (structured abstention — do NOT include claims from model memory).",
            "",
            "Unprovenanced claims found:",
        ]
        for f in unprovenanced[:5]:
            lines.append(f"  [{f['claim_type']}] '{f['match']}' — context: ...{f['context']}...")
        lines.append("")
        lines.append("Fix: add provenance flag (e.g. 'ước tính 200,000 điểm bán (theo BCTC)') or remove the claim.")
        feedback = "\n".join(lines)

    return {
        "passed": passed,
        "total_claims": len(findings),
        "unprovenanced_count": len(unprovenanced),
        "unprovenanced_claims": unprovenanced[:5],
        "feedback": feedback,
    }


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 2:
        print("Usage: python3 no_source_claim_gate.py <html_file>")
        sys.exit(1)
    html = open(sys.argv[1]).read()
    result = check_no_source_claims(html)
    print(json.dumps({k: v for k, v in result.items() if k != "feedback"}, indent=2, ensure_ascii=False))
    if not result["passed"]:
        print("\n" + result["feedback"])
    sys.exit(0 if result["passed"] else 1)
