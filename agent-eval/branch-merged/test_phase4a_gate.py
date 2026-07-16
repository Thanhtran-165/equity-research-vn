# test_phase4a_gate.py — BRANCH-A CANDIDATE: Phase-4A Tech Score gate tests.
#
# 11 tests covering the classification branches of phase4a_gate.gate_phase4a:
#   VALID | MISSING_SCORE | OUT_OF_RANGE | INVALID_VERDICT | MISMATCH | NO_SOURCE_DATA
#
# Mirrors the style of test_phase6_preflight.py (in-repo import via sys.path).
import os, sys, pytest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import phase4a_gate as G

# The verified source contract — the `technical` block emitted by build_data_contract.py
# for the CTD source-pack (technical_active.json: tech_score=-6, verdict=STRONG SELL).
SRC_CONTRACT = {
    "mode": "ACTIVE", "tech_score": -6, "scale_min": -6, "scale_max": 6,
    "verdict": "STRONG SELL", "source_file": "technical_active.json", "verified": True,
}

def gate(output, contract=SRC_CONTRACT):
    """Unwrap the 3-tuple for concise assertions."""
    return G.gate_phase4a(output, contract)


# --- Test 1: contract with valid score+verdict → PASS ---
def test_valid_score_and_verdict_passes():
    out = ('<div class="tech-score-card" data-metric="tech-score" '
           'data-score="-6" data-verdict="STRONG SELL"></div>')
    passed, errors, cls = gate(out)
    assert passed is True
    assert cls == "VALID"
    assert errors == []

# --- Test 2: analysis exists but no score → FAIL (MISSING_SCORE) ---
def test_analysis_present_but_no_score_fails():
    out = ("## Technical Analysis — CTD\nRSI: 42.8 (neutral-bearish). MACD below signal. "
           "Price trading below MA10/MA20/MA50. Descending channel active. "
           "No explicit score number appears anywhere in this output.")
    passed, errors, cls = gate(out)
    assert passed is False
    assert cls == "MISSING_SCORE"

# --- Test 3: score outside [-6,6] → FAIL (OUT_OF_RANGE) ---
def test_score_out_of_range_fails():
    out = 'tech_score: 12, verdict: STRONG BUY'
    passed, errors, cls = gate(out)
    assert passed is False
    assert cls == "OUT_OF_RANGE"
    assert any("outside" in e for e in errors)

# --- Test 4: verdict not in enum → FAIL (INVALID_VERDICT) ---
def test_invalid_verdict_fails():
    out = 'tech_score: -6, verdict: HOLD'
    passed, errors, cls = gate(out)
    assert passed is False
    assert cls == "INVALID_VERDICT"

# --- Test 5: score and verdict mismatch (score=5, verdict=SELL) → FAIL (MISMATCH) ---
def test_score_verdict_mismatch_fails():
    # Build a contract whose source ALSO says score=5/SELL so this isolates the
    # score↔verdict consistency check (test #5) from the contract-match check (test #6).
    contract = dict(SRC_CONTRACT, tech_score=5, verdict="SELL")
    out = 'tech_score: 5, verdict: SELL'
    passed, errors, cls = gate(out, contract)
    assert passed is False
    assert cls == "MISMATCH"
    assert any("mismatch" in e for e in errors)

# --- Test 6: dashboard score differs from contract → FAIL ---
def test_dashboard_score_differs_from_contract_fails():
    # The agent rendered -3/SELL (internally consistent), but the verified source
    # contract says -6/STRONG SELL → must fail (no silent substitution).
    out = 'tech_score: -3, verdict: SELL'
    passed, errors, cls = gate(out)  # SRC_CONTRACT = -6/STRONG SELL
    assert passed is False
    assert cls == "MISMATCH"
    assert any("does not match verified source" in e for e in errors)

# --- Test 7: missing source value → no fallback → FAIL (NO_SOURCE_DATA) ---
def test_missing_source_contract_no_fallback_fails():
    # No source data at all.
    passed, errors, cls = gate("tech_score: -6, verdict: STRONG SELL", None)
    assert passed is False
    assert cls == "NO_SOURCE_DATA"
    # Source present but no tech_score key → also NO_SOURCE_DATA (no fallback).
    contract_no_score = {"mode": "ACTIVE", "verdict": "BUY"}  # tech_score omitted
    passed2, errors2, cls2 = gate("tech_score: 4, verdict: BUY", contract_no_score)
    assert passed2 is False and cls2 == "NO_SOURCE_DATA"

# --- Test 8: whitespace / HTML formatting variations parse correctly ---
def test_whitespace_and_formatting_variations_parse():
    variants = [
        # multiline JSON with indented keys
        '{\n  "tech_score": -6,\n  "verdict": "STRONG SELL"\n}',
        # labelled text with pipes and spaces
        'Tech Score:    -6   |   Verdict:    STRONG SELL',
        # lower-case verdict, equals form
        'tech_score=-6 verdict=strong sell',
        # decimal tolerated
        'tech_score: -6.0, verdict: STRONG SELL',
        # data-tech-score attribute (hyphenated)
        '<div data-tech-score="-6" data-verdict="STRONG SELL"></div>',
    ]
    for v in variants:
        passed, errors, cls = gate(v)
        assert passed is True, f"variant should PASS: {v!r} → {cls} {errors}"
        assert cls == "VALID"

# --- Test 9: chart / script tokens don't create a false positive ---
def test_chart_and_script_tokens_no_false_positive():
    # Contains words that look numeric/chart-ish but NO tech_score/verdict pair.
    out = ('<canvas id="chart-score"></canvas>'
           '<script>const zscore=1.2; var composites={a:3,b:-1};</script>'
           '<div class="scorecard-wrap" data-metric="rsi">RSI 42.78</div>')
    passed, errors, cls = gate(out)
    assert passed is False
    # No tech_score token → MISSING_SCORE (NOT a spurious VALID).
    assert cls == "MISSING_SCORE"

# --- Test 10: retry produces valid score → autonomous content recovery recorded ---
def test_retry_recovery_succeeds_and_recorded():
    # Attempt 1: invalid (mismatch — score says BUY, verdict says SELL).
    bad_out = 'tech_score: 3, verdict: SELL'
    p1, _, cls1 = gate(bad_out)
    assert p1 is False  # first attempt rejected

    # Simulate the runner's bounded-retry loop (1 initial + max 2 recovery = 3 total),
    # mirroring agent_runner.py's phase6 retry policy. After the model corrects itself,
    # the retry output is VALID.
    attempts = [bad_out]
    max_recovery = 2
    final_pass, final_cls, recovered = False, None, False
    for recovery in range(1, max_recovery + 1):
        if recovery == 1:
            good_out = ('<div class="tech-score-card" data-metric="tech-score" '
                        'data-score="-6" data-verdict="STRONG SELL"></div>')
            attempts.append(good_out)
        p, _, c = gate(attempts[-1])
        if p:
            final_pass, final_cls, recovered = True, c, (recovery > 0)
            break
    assert final_pass is True
    assert final_cls == "VALID"
    # Recovery recorded: the loop took more than one attempt and succeeded after retry.
    assert recovered is True
    assert len(attempts) == 2  # initial rejected + 1 successful recovery

# --- Test 11: clean control (valid input) → PASS ---
def test_clean_control_valid_input_passes():
    out = ('<!DOCTYPE html><html><body>'
           '<section id="sec-tech"><div class="tech-score-card" '
           'data-metric="tech-score" data-score="-6" data-verdict="STRONG SELL">'
           'Tech Score: -6 / STRONG SELL</div></section>'
           '</body></html>')
    passed, errors, cls = gate(out)
    assert passed is True
    assert cls == "VALID"
    assert errors == []
