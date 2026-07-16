"""Tests cho cache namespace, inspect_cache, multi-brand isolation."""
import json
import time
from pathlib import Path

from src.models import Brand, PageMeta
from src.page_meta import (
    list_cached_urls, inspect_cache, _write_cache, _cache_key,
)


def _brand(brand_id="brand_a"):
    return Brand(
        id=brand_id,
        display_name=f"Brand {brand_id}",
        aliases=[f"Brand {brand_id}"],
        official_username=brand_id,
        official_page_url=f"https://www.facebook.com/{brand_id}",
        avatar_path="/dev/null",
        cover_path="/dev/null",
    )


def _write_entry(cache_dir, url, brand_id="", source="public", title="Test"):
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = _cache_key(url)
    payload = {
        "url": url, "title": title, "avatar_url": "", "cover_url": "",
        "is_verified": False, "created_year": None, "recent_post_count_30d": 0,
        "fetched_at": "2026-01-01", "fetched_ts": time.time(),
        "avatar_checked": True, "brand_id": brand_id, "source": source,
        "has_avatar": False, "has_cover": False,
    }
    (cache_dir / f"{key}.json").write_text(json.dumps(payload))


def test_list_cached_urls_brand_id_filter(tmp_path, monkeypatch):
    """list_cached_urls chỉ trả URL match brand_id."""
    monkeypatch.setattr("src.page_meta._CACHE_DIR", tmp_path)
    _write_entry(tmp_path, "https://www.facebook.com/u1", brand_id="brand_a")
    _write_entry(tmp_path, "https://www.facebook.com/u2", brand_id="brand_b")

    urls_a = list_cached_urls(brand=_brand("brand_a"))
    urls_b = list_cached_urls(brand=_brand("brand_b"))

    assert len(urls_a) == 1
    assert "u1" in urls_a[0]
    assert len(urls_b) == 1
    assert "u2" in urls_b[0]


def test_list_cached_urls_legacy_entries_no_brand_id(tmp_path, monkeypatch):
    """Cache cũ không có brand_id → vẫn trả (backward-compatible)."""
    monkeypatch.setattr("src.page_meta._CACHE_DIR", tmp_path)
    _write_entry(tmp_path, "https://www.facebook.com/legacy1", brand_id="")

    urls = list_cached_urls(brand=_brand("brand_a"))
    assert len(urls) == 1  # legacy entry returned regardless of brand


def test_inspect_cache_stats(tmp_path, monkeypatch):
    """inspect_cache trả stats đúng."""
    monkeypatch.setattr("src.page_meta._CACHE_DIR", tmp_path)
    _write_entry(tmp_path, "https://www.facebook.com/u1", brand_id="brand_a", source="public")
    _write_entry(tmp_path, "https://www.facebook.com/u2", brand_id="brand_a", source="search_bar")
    _write_entry(tmp_path, "https://www.facebook.com/u3", brand_id="brand_b", source="manual")

    stats = inspect_cache()
    assert stats["total"] == 3
    assert stats["valid"] == 3
    assert stats["stale"] == 0
    assert stats["by_brand"]["brand_a"] == 2
    assert stats["by_brand"]["brand_b"] == 1
    assert stats["by_source"]["public"] == 1
    assert stats["by_source"]["search_bar"] == 1


def test_inspect_cache_stale_count(tmp_path, monkeypatch):
    """inspect_cache đếm stale entries đúng."""
    monkeypatch.setattr("src.page_meta._CACHE_DIR", tmp_path)
    # Write stale entry (8 days ago)
    key = _cache_key("https://www.facebook.com/stale1")
    payload = {
        "url": "https://www.facebook.com/stale1", "title": "Stale",
        "fetched_ts": time.time() - 8 * 24 * 3600,
        "brand_id": "brand_a", "source": "public",
        "avatar_checked": True, "has_avatar": False, "has_cover": False,
    }
    (tmp_path / f"{key}.json").write_text(json.dumps(payload))

    stats = inspect_cache()
    assert stats["total"] == 1
    assert stats["stale"] == 1
    assert stats["valid"] == 0


def test_multi_brand_cache_isolation(tmp_path, monkeypatch):
    """Cache brand_a không ảnh hưởng brand_b."""
    monkeypatch.setattr("src.page_meta._CACHE_DIR", tmp_path)
    _write_entry(tmp_path, "https://www.facebook.com/a1", brand_id="brand_a")
    _write_entry(tmp_path, "https://www.facebook.com/a2", brand_id="brand_a")
    _write_entry(tmp_path, "https://www.facebook.com/b1", brand_id="brand_b")
    _write_entry(tmp_path, "https://www.facebook.com/b2", brand_id="brand_b")

    urls_a = list_cached_urls(brand=_brand("brand_a"))
    urls_b = list_cached_urls(brand=_brand("brand_b"))

    assert len(urls_a) == 2
    assert len(urls_b) == 2
    # No overlap
    set_a = set(urls_a)
    set_b = set(urls_b)
    assert set_a.isdisjoint(set_b)
