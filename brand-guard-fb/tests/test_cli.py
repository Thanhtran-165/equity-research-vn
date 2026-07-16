"""Tests cho CLI: --no-network đọc cache, multi-brand output."""
import json
import time
from pathlib import Path

from src.cli import main, _scan_brand, _add_report_counts
from src.config_loader import load_config
from src.models import Brand, PageMeta, ScanReport, ScoredPage, ScoreResult


def _write_cache_entry(cache_dir, url, title="Test Profile", avatar_url="", avatar_checked=True):
    """Helper: ghi 1 cache entry."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    import hashlib
    key = hashlib.sha1(url.encode("utf-8")).hexdigest()
    payload = {
        "url": url,
        "title": title,
        "description": "",
        "avatar_url": avatar_url,
        "cover_url": "",
        "is_verified": False,
        "created_year": None,
        "recent_post_count_30d": 0,
        "fetched_at": "2026-01-01T00:00:00",
        "fetched_ts": time.time(),
        "avatar_checked": avatar_checked,
    }
    (cache_dir / f"{key}.json").write_text(json.dumps(payload))


def _brand_fixture(brand_id="brand_a", official_username="branda"):
    return Brand(
        id=brand_id,
        display_name=f"Brand {brand_id[-1].upper()}",
        aliases=[f"Brand {brand_id[-1].upper()}"],
        official_username=official_username,
        official_page_url=f"https://www.facebook.com/{official_username}",
        avatar_path="/dev/null",
        cover_path="/dev/null",
    )


# === --no-network đọc cache ===

def test_no_network_reads_cache(tmp_path, monkeypatch):
    """--no-network với cache có entries → scan trả results, không empty."""
    cache_dir = tmp_path / "page_meta"
    monkeypatch.setattr("src.page_meta._CACHE_DIR", cache_dir)

    brand = _brand_fixture()
    fake_url = "https://www.facebook.com/profile.php?id=61587948592750"
    _write_cache_entry(cache_dir, fake_url, title="Brand A")

    scoring_cfg = {
        "name_threshold_high": 90,
        "name_threshold_mid": 80,
        "avatar_distance_strong": 4,
        "avatar_distance_moderate": 8,
        "avatar_distance_weak": 12,
        "cover_distance_strong": 4,
        "cover_distance_moderate": 8,
        "cover_distance_weak": 12,
        "recent_years": [2025, 2026],
    }

    report, stats = _scan_brand(brand, scoring_cfg, no_network=True)
    assert len(report.pages) >= 1
    assert any(p.page.url == fake_url for p in report.pages)


def test_no_network_empty_cache_returns_empty(tmp_path, monkeypatch):
    """--no-network với cache trống → return empty report (không crash)."""
    cache_dir = tmp_path / "page_meta"
    monkeypatch.setattr("src.page_meta._CACHE_DIR", cache_dir)

    brand = _brand_fixture()
    scoring_cfg = {"name_threshold_high": 90, "name_threshold_mid": 80,
                   "avatar_distance_strong": 4, "avatar_distance_moderate": 8,
                   "avatar_distance_weak": 12, "cover_distance_strong": 4,
                   "cover_distance_moderate": 8, "cover_distance_weak": 12,
                   "recent_years": [2025, 2026]}

    report, stats = _scan_brand(brand, scoring_cfg, no_network=True)
    assert len(report.pages) == 0


# === Multi-brand output ===

def test_multi_brand_output(tmp_path, monkeypatch):
    """Scan 2 brand → output chứa cả 2 brand reports."""
    cache_dir = tmp_path / "page_meta"
    monkeypatch.setattr("src.page_meta._CACHE_DIR", cache_dir)

    # Write cache entries cho 2 brand
    url_a = "https://www.facebook.com/profile.php?id=1111111111"
    url_b = "https://www.facebook.com/profile.php?id=2222222222"
    _write_cache_entry(cache_dir, url_a, title="Brand A")
    _write_cache_entry(cache_dir, url_b, title="Brand B")

    # Create config file with 2 brands
    config_content = """
defaults:
  scoring:
    name_threshold_high: 90
    name_threshold_mid: 80
    avatar_distance_strong: 4
    avatar_distance_moderate: 8
    avatar_distance_weak: 12
    cover_distance_strong: 4
    cover_distance_moderate: 8
    cover_distance_weak: 12
brands:
  - id: brand_a
    display_name: "Brand A"
    aliases: ["Brand A"]
    official_username: branda
    official_page_url: https://www.facebook.com/branda
    avatar_path: /dev/null
    cover_path: /dev/null
  - id: brand_b
    display_name: "Brand B"
    aliases: ["Brand B"]
    official_username: brandb
    official_page_url: https://www.facebook.com/brandb
    avatar_path: /dev/null
    cover_path: /dev/null
"""
    config_path = tmp_path / "brands.yaml"
    config_path.write_text(config_content)

    import io
    import contextlib
    stdout_buf = io.StringIO()
    with contextlib.redirect_stdout(stdout_buf):
        rc = main(["--config", str(config_path), "--no-network"])
    assert rc == 0

    output = stdout_buf.getvalue()
    # Cả 2 brand phải xuất hiện trong output
    assert "Brand A" in output
    assert "Brand B" in output


def test_summary_counts_risk_bands():
    """Summary stats must reflect actual report bands, not zero placeholders."""
    report = ScanReport(
        brand_id="brand_a",
        run_at="2026-01-01T00:00+0700",
        pages=[
            ScoredPage(
                page=PageMeta(url="https://www.facebook.com/high", title="High"),
                score=ScoreResult(total=80, name=15, avatar=50, cover=15, recency=0, url=0),
            ),
            ScoredPage(
                page=PageMeta(url="https://www.facebook.com/mid", title="Mid"),
                score=ScoreResult(total=50, name=15, avatar=35, cover=0, recency=0, url=0),
            ),
            ScoredPage(
                page=PageMeta(url="https://www.facebook.com/low", title="Low"),
                score=ScoreResult(
                    total=15, name=15, avatar=0, cover=0, recency=0, url=0,
                    needs_semantic_check=True,
                ),
            ),
        ],
    )
    stats = _add_report_counts({}, report)
    assert stats["high"] == 1
    assert stats["mid"] == 1
    assert stats["low"] == 1
    assert stats["semantic_check"] == 1
