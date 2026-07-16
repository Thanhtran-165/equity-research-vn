#!/usr/bin/env python3
"""
test_req007_fixtures.py — REQ-007 entity-interruption-tolerant disclaimer tests.

Validates the v0.1.5 verifier patch for REQ-007:
  - Disclaimers with ticker/company names between words → PASS (was false positive)
  - Real advice with ticker names → FAIL
  - Disclaimer + real advice coexisting → FAIL
  - Clean control (no advice, no disclaimer) → PASS
  - Verdict labels (STRONG BUY/SELL) → PASS

These are the exact fixtures from the owner directive (2026-07-14).
"""
import sys, os, re, json
sys.path.insert(0, os.path.expanduser("~/.zcode/skills/equity-research-vn/scripts"))
from independent_verifier import verify_non_advice_check, extract_section_text

# Helper: wrap text in a minimal HTML with sec-tech-profile section
def make_html(sec_text):
    return f'''<!DOCTYPE html><html><body>
<section id="sec-tech-profile"><p>{sec_text}</p></section>
</body></html>'''

# Fixture set from owner directive + edge cases
FIXTURES = [
    # --- SHOULD PASS (valid disclaimers with entity interruption) ---
    {
        "id": "FX-001",
        "text": "Thông tin về VCB không phải là khuyến nghị mua/bán.",
        "expect": "PASS",
        "reason": "negation with ticker before disclaimer",
    },
    {
        "id": "FX-002",
        "text": "Đánh giá CTD này không cấu thành khuyến nghị đầu tư.",
        "expect": "PASS",
        "reason": "negation with company name before 'cấu thành'",
    },
    {
        "id": "FX-003",
        "text": "Nội dung trên đối với PNJ chỉ mang tính tham khảo, không phải lời khuyên tài chính.",
        "expect": "PASS",
        "reason": "negation with ticker in 'chỉ mang tính tham khảo' clause",
    },
    {
        "id": "FX-004",
        "text": "Đây mô tả đặc tính giá, không khuyến nghị mua/bán VCB có drawdown tối đa ước tính 25%.",
        "expect": "PASS",
        "reason": "T-VCB-01 exact case — ticker after 'bán'",
    },
    {
        "id": "FX-005",
        "text": "Báo cáo này không phải khuyến nghị mua/bán cho nhà đầu tư.",
        "expect": "PASS",
        "reason": "standard negation without 'phải là'",
    },
    # --- SHOULD FAIL (real advice with ticker) ---
    {
        "id": "FX-006",
        "text": "Khuyến nghị mua VCB ở mức giá hiện tại.",
        "expect": "FAIL",
        "reason": "direct buy recommendation with ticker",
    },
    {
        "id": "FX-007",
        "text": "Nhà đầu tư nên mua VCB để hưởng cổ tức.",
        "expect": "FAIL",
        "reason": "actionable advice with ticker",
    },
    {
        "id": "FX-008",
        "text": "Thông tin không phải khuyến nghị chung, nhưng có thể mua VCB ở vùng giá này.",
        "expect": "FAIL",
        "reason": "disclaimer + real advice in same text",
    },
    # --- SHOULD PASS (verdict labels, not advice) ---
    {
        "id": "FX-009",
        "text": "Tech Score: -4/6 — Verdict: SELL. Không phải khuyến nghị mua/bán.",
        "expect": "PASS",
        "reason": "verdict label + disclaimer",
    },
    {
        "id": "FX-010",
        "text": "Kết luận: STRONG SELL trên 6 tín hiệu kỹ thuật. Đây không phải lời khuyên tài chính.",
        "expect": "PASS",
        "reason": "STRONG SELL verdict + negation disclaimer",
    },
    # --- SHOULD PASS (clean, no advice, no disclaimer) ---
    {
        "id": "FX-011",
        "text": "Phân tích kỹ thuật dựa trên 6 tín hiệu: MACD âm, RSI dưới 30, volumes giảm. Drawdown tối đa 25% trong 52 tuần. Beta 1.2 so với VNINDEX.",
        "expect": "PASS",
        "reason": "clean technical analysis, no advice keywords",
    },
    # --- SHOULD FAIL (real advice, no ticker) ---
    {
        "id": "FX-012",
        "text": "Nhà đầu tư nên chốt lời ở mức giá này. Điểm mua phù hợp cho ngắn hạn.",
        "expect": "FAIL",
        "reason": "multiple actionable advice signals without ticker",
    },
    # --- Edge: "không nên mua" (negation + advice word) ---
    {
        "id": "FX-013",
        "text": "Không nên mua cổ phiếu này trong ngắn hạn do rủi ro biến động cao.",
        "expect": "PASS",
        "reason": "'không nên mua' = negated advice = disclaimer, not recommendation",
    },
]

def run_fixtures():
    results = []
    for fx in FIXTURES:
        html = make_html(fx["text"])
        req = {"verification": {"method": "non_advice_check"}}
        passed, evidence = verify_non_advice_check(req, html)
        actual = "PASS" if passed else "FAIL"
        expected = fx["expect"]
        ok = actual == expected
        results.append({
            "id": fx["id"],
            "expect": expected,
            "actual": actual,
            "ok": ok,
            "reason": fx["reason"],
            "evidence": evidence,
        })
        sym = "✓" if ok else "✗"
        print(f"  {sym} {fx['id']}: expect={expected} actual={actual} — {fx['reason']}")
        if not ok:
            print(f"    evidence: {json.dumps(evidence, ensure_ascii=False)[:200]}")
    return results

if __name__ == "__main__":
    print("="*70)
    print("REQ-007 FIXTURE TESTS (v0.1.5 entity-interruption-tolerant)")
    print("="*70)
    results = run_fixtures()
    passed = sum(1 for r in results if r["ok"])
    total = len(results)
    print(f"\n{'='*70}")
    print(f"  RESULTS: {passed}/{total} fixtures correct")
    print(f"{'='*70}")
    if passed < total:
        print("\n  FAILED fixtures:")
        for r in results:
            if not r["ok"]:
                print(f"    {r['id']}: expect={r['expect']} actual={r['actual']} — {r['reason']}")
    # Specificity: clean controls must PASS
    clean = [r for r in results if r["expect"] == "PASS"]
    clean_passed = sum(1 for r in clean if r["actual"] == "PASS")
    print(f"\n  Specificity (PASS-expected → actual PASS): {clean_passed}/{len(clean)}")
    # Sensitivity: FAIL-expected must FAIL
    fail_exp = [r for r in results if r["expect"] == "FAIL"]
    fail_caught = sum(1 for r in fail_exp if r["actual"] == "FAIL")
    print(f"  Sensitivity (FAIL-expected → actual FAIL): {fail_caught}/{len(fail_exp)}")
    sys.exit(0 if passed == total else 1)
