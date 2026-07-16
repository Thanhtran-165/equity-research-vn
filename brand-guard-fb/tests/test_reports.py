"""Tests cho template rendering: alert post, complaints, no leftover placeholders."""
from src.models import Brand, ScoredPage, PageMeta, ScoreResult, RiskBand
from src.takedown_template import render_alert_post, render_meta_ip, render_shtt


def _brand():
    return Brand(
        id="test", display_name="Test Brand", aliases=["Test Brand"],
        official_username="testbrand",
        official_page_url="https://www.facebook.com/testbrand",
        avatar_path="/dev/null", cover_path="/dev/null",
    )


def _scored_page(url, title, total, avatar=0, cover=0, name=0):
    return ScoredPage(
        page=PageMeta(url=url, title=title),
        score=ScoreResult(total=total, name=name, avatar=avatar, cover=cover,
                          recency=0, url=0),
    )


def test_alert_post_high_says_xac_nhan():
    """HIGH band → 'XÁC NHẬN' trong alert post."""
    page = _scored_page("https://fb.com/fake1", "Fake Brand", 80, avatar=50, name=15)
    md = render_alert_post(brand=_brand(), pages=[page])
    assert "XÁC NHẬN" in md


def test_alert_post_mid_says_nghi_van():
    """MID band → 'NGHI VẤN' trong page list, không có '🔴 XÁC NHẬN' tag."""
    page = _scored_page("https://fb.com/fake2", "Fake Brand", 50, name=15)
    md = render_alert_post(brand=_brand(), pages=[page])
    assert "🟡 NGHI VẤN" in md
    # The HIGH tag should not appear for MID pages
    assert "🔴 XÁC NHẬN" not in md


def test_alert_post_no_leftover_placeholders():
    """Alert post render xong không còn {var} nào."""
    page = _scored_page("https://fb.com/fake3", "Fake", 75, avatar=50, name=15)
    md = render_alert_post(brand=_brand(), pages=[page])
    assert "{" not in md
    assert "}" not in md


def test_meta_ip_no_leftover_placeholders():
    """Meta IP template render xong không còn {var}."""
    page = _scored_page("https://fb.com/fake4", "Fake", 80, avatar=50)
    md = render_meta_ip(
        brand=_brand(), pages=[page],
        signatory_name="Test", signatory_title="Admin",
        signatory_email="test@test.com", today_date="2026-01-01",
    )
    assert "{" not in md
    assert "}" not in md


def test_shtt_no_leftover_placeholders():
    """SHTT template render xong không còn {var}."""
    page = _scored_page("https://fb.com/fake5", "Fake", 80, avatar=50)
    md = render_shtt(
        brand=_brand(), pages=[page],
        signatory_name="Test", signatory_title="Admin",
        signatory_email="test@test.com", today_date="2026-01-01",
    )
    assert "{" not in md
    assert "}" not in md


def test_meta_ip_has_evidence_checklist():
    """Meta IP template có evidence checklist."""
    page = _scored_page("https://fb.com/fake6", "Fake", 80)
    md = render_meta_ip(
        brand=_brand(), pages=[page],
        signatory_name="T", signatory_title="T", signatory_email="t@t.com",
        today_date="2026-01-01",
    )
    assert "Evidence Checklist" in md or "Checklist" in md


def test_alert_post_empty_pages():
    """Alert post với empty pages list không crash."""
    md = render_alert_post(brand=_brand(), pages=[])
    assert "CẢNH BÁO" in md


def test_alert_post_official_url_included():
    """Alert post chứa official page URL."""
    page = _scored_page("https://fb.com/fake7", "Fake", 75)
    md = render_alert_post(brand=_brand(), pages=[page])
    assert "https://www.facebook.com/testbrand" in md
