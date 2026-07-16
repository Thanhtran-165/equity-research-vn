# test_phase6_preflight.py — Layer-2 gate tests (revised: FIX #2 + #3 + #4).
import os, sys, pytest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import phase6_preflight as P

def preflight(out, stop_reason=None):
    # unwrap 4-tuple for backward-compat assertions
    p, e, c, d = P.preflight_phase6(out, stop_reason=stop_reason)
    return p, e, c

def test_narration_caught():
    passed, errors, cls = preflight("I'll build the dashboard for CTD. Let me start by copying the template.\n## Step 1...")
    assert passed is False and cls == "NARRATION"

def test_vietnamese_narration_caught():
    passed, errors, cls = preflight("Tôi sẽ xây dashboard. Bước 1: copy template...")
    assert passed is False and cls == "NARRATION"

def test_markdown_fence_caught():
    passed, errors, cls = preflight("```html\n<!DOCTYPE html>\n<html>...</html>\n```")
    assert passed is False

def test_valid_html_passes():
    out = ('<!DOCTYPE html>\n<html><head></head><body>'
           '<section id="sec-hero">content</section>'
           '<canvas id="chartHistRev"></canvas>'
           '<script>const DATA = {ticker:"CTD",years:[2021]};</script>'
           '</body></html>')
    passed, errors, cls = preflight(out)
    assert passed is True and cls == "HTML"

# FIX #2: whitespace/attribute-order tolerant
def test_const_data_with_spaces_passes():
    out = '<!DOCTYPE html><html><body><section id="sec-x">y</section><canvas id="c"></canvas><script>const DATA = {\n  ticker: "CTD"\n}</script></body></html>'
    passed, _, _ = preflight(out)
    assert passed is True

def test_section_id_not_first_attribute_passes():
    out = '<!DOCTYPE html><html><body><section class="hero" data-x="1" id="sec-hero">content</section><canvas id="c"></canvas><script>const DATA={};</script></body></html>'
    passed, _, cls = preflight(out)
    assert passed is True and cls == "HTML"

# FIX #3: truncation detection
def test_html_starts_but_no_close_html_truncated():
    out = '<!DOCTYPE html><html><body><section id="sec-hero">content</section><canvas id="c"></canvas><script>const DATA={};</script>'
    passed, errors, cls = preflight(out)
    assert passed is False
    assert cls == "OUTPUT_TRUNCATED"

def test_max_tokens_stop_classified_truncated_not_malformed():
    out = '<!DOCTYPE html><html><body><section id="sec-hero">content'
    passed, errors, cls = preflight(out, stop_reason="max_tokens")
    assert cls == "OUTPUT_TRUNCATED"
    assert any("max_tokens" in e for e in errors)

def test_empty_caught():
    passed, errors, cls = preflight("")
    assert passed is False and cls == "EMPTY"

def test_malformed_html_no_sections():
    out = "<!DOCTYPE html><html><body><p>hello</p></body></html>"
    passed, errors, cls = preflight(out)
    assert passed is False

def test_no_false_positive_on_real_report():
    p = os.path.join(HERE,"..","..","skill-harness-evaluator-work","post-merge-0.1.1","fixtures","clean-control-flagged.html")
    if not os.path.exists(p): pytest.skip("fixture missing")
    out = open(p).read()
    passed, errors, cls = preflight(out)
    assert passed is True and cls == "HTML"

# FIX #4: alt-format valid still passes (whitespace tolerant DOCTYPE)
def test_alt_doctype_case_passes():
    out = '<!doctype html>\n<html><body><section id="sec-x">y</section><canvas id="c"></canvas><script>const DATA={};</script></body></html>'
    passed, _, cls = preflight(out)
    assert passed is True
