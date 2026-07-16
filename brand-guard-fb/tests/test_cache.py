"""Tests cho cache system: _read_cache giữ avatar_checked, _slug_from_url không collision,
list_cached_urls đọc đúng cache, --no-network đọc cache."""
import json
import time
from pathlib import Path
from unittest.mock import patch

from src.models import Brand, PageMeta
from src.page_meta import (
    _read_cache,
    _write_cache,
    _slug_from_url,
    list_cached_urls,
    _cache_path,
    _cache_key,
)


def _brand():
    return Brand(
        id="test_brand",
        display_name="Test Brand",
        aliases=["Test Brand"],
        official_username="testbrand",
        official_page_url="https://www.facebook.com/testbrand",
        avatar_path="/dev/null",
        cover_path="/dev/null",
    )


def _make_meta(url, title="Test", avatar_url="", cover_url=""):
    return PageMeta(
        url=url,
        title=title,
        avatar_url=avatar_url,
        cover_url=cover_url,
    )


# === _slug_from_url không collision ===

def test_slug_unique_people_vs_profile_php():
    """Hai URL /people/* và /profile.php?id= phải có slug khác nhau."""
    url1 = "https://www.facebook.com/people/Chim-Cut/pfbid0ABC123"
    url2 = "https://www.facebook.com/profile.php?id=61587948592750"
    slug1 = _slug_from_url(url1)
    slug2 = _slug_from_url(url2)
    assert slug1 != slug2, f"Collision: {slug1} == {slug2}"


def test_slug_unique_different_pfbid():
    """Hai URL /people/ khác pfbid phải có slug khác nhau."""
    url1 = "https://www.facebook.com/people/Chim-Cut/pfbid0AAA"
    url2 = "https://www.facebook.com/people/Chim-Cut/pfbid0BBB"
    assert _slug_from_url(url1) != _slug_from_url(url2)


def test_slug_unique_username_vs_people():
    """URL /username và /people/Name/pfbid phải khác slug."""
    url1 = "https://www.facebook.com/fahmi.sham.604320"
    url2 = "https://www.facebook.com/people/Chim-Cut/pfbid0XYZ"
    assert _slug_from_url(url1) != _slug_from_url(url2)


# === _read_cache giữ cache avatar_checked=True ===

def test_read_cache_keeps_avatar_checked_entry(tmp_path, monkeypatch):
    """Cache entry có avatar_checked=True nhưng avatar_url rỗng → vẫn trả meta (không stale)."""
    monkeypatch.setattr("src.page_meta._CACHE_DIR", tmp_path)
    url = "https://www.facebook.com/test.profile"
    cache_file = tmp_path / f"{_cache_key(url)}.json"
    payload = {
        "url": url,
        "title": "Test Profile",
        "avatar_url": "",
        "cover_url": "",
        "fetched_ts": time.time(),
        "avatar_checked": True,
    }
    cache_file.write_text(json.dumps(payload))

    meta = _read_cache(url)
    assert meta is not None
    assert meta.title == "Test Profile"


def test_read_cache_invalidates_without_avatar_checked(tmp_path, monkeypatch):
    """Cache entry không có avatar_checked + avatar rỗng → stale → return None."""
    monkeypatch.setattr("src.page_meta._CACHE_DIR", tmp_path)
    url = "https://www.facebook.com/test.profile2"
    cache_file = tmp_path / f"{_cache_key(url)}.json"
    payload = {
        "url": url,
        "title": "Test Profile",
        "avatar_url": "",
        "cover_url": "",
        "fetched_ts": time.time(),
    }
    cache_file.write_text(json.dumps(payload))

    meta = _read_cache(url)
    assert meta is None  # stale → None


def test_read_cache_returns_none_for_expired(tmp_path, monkeypatch):
    """Cache entry quá TTL → return None."""
    monkeypatch.setattr("src.page_meta._CACHE_DIR", tmp_path)
    url = "https://www.facebook.com/test.profile3"
    cache_file = tmp_path / f"{_cache_key(url)}.json"
    payload = {
        "url": url,
        "title": "Old Profile",
        "avatar_url": "/some/local/path.jpg",
        "fetched_ts": time.time() - 8 * 24 * 3600,  # 8 ngày ago
        "avatar_checked": True,
    }
    cache_file.write_text(json.dumps(payload))

    meta = _read_cache(url)
    assert meta is None  # expired


# === list_cached_urls ===

def test_list_cached_urls_returns_all(tmp_path, monkeypatch):
    """list_cached_urls trả tất cả URL hợp lệ trong cache."""
    monkeypatch.setattr("src.page_meta._CACHE_DIR", tmp_path)
    urls = [
        "https://www.facebook.com/profile.php?id=61587948592750",
        "https://www.facebook.com/fahmi.sham.604320",
        "https://www.facebook.com/chim.cut.90",
    ]
    for url in urls:
        cache_file = tmp_path / f"{_cache_key(url)}.json"
        payload = {"url": url, "title": "Test", "fetched_ts": time.time(), "avatar_checked": True}
        cache_file.write_text(json.dumps(payload))

    result = list_cached_urls(brand=_brand())
    assert len(result) == 3
    for url in urls:
        assert url in result


def test_list_cached_urls_filters_official(tmp_path, monkeypatch):
    """list_cached_urls loại trừ URL chính chủ của brand."""
    monkeypatch.setattr("src.page_meta._CACHE_DIR", tmp_path)
    brand = _brand()
    urls = [
        "https://www.facebook.com/testbrand",
        "https://www.facebook.com/profile.php?id=1234567890",
    ]
    for url in urls:
        cache_file = tmp_path / f"{_cache_key(url)}.json"
        payload = {"url": url, "title": "Test", "fetched_ts": time.time(), "avatar_checked": True}
        cache_file.write_text(json.dumps(payload))

    result = list_cached_urls(brand=brand)
    assert len(result) == 1
    assert "profile.php?id=1234567890" in result[0]
    assert "testbrand" not in result[0]


def test_list_cached_urls_empty_when_no_cache(tmp_path, monkeypatch):
    """list_cached_urls trả empty list khi cache dir không tồn tại."""
    monkeypatch.setattr("src.page_meta._CACHE_DIR", tmp_path / "nonexistent")
    result = list_cached_urls()
    assert result == []
