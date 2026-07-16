from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from src.models import PageMeta


_YEAR_RE = re.compile(r"(?:Page created|Created on|Tham gia|Thành lập).*?(20\d{2})", re.IGNORECASE)
_RECENT_POST_RE = re.compile(r"data-utime=\"(\d{10,})\"")
_CACHE_DIR = Path(".cache/page_meta")
_CACHE_TTL_SECONDS = 7 * 24 * 3600  # 7 ngày — profiles clean không cần re-check mỗi ngày
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Upgrade-Insecure-Requests": "1",
}


def _cache_key(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def _slug_from_url(url: str) -> str:
    """Derive a UNIQUE filename slug from URL.

    BUGFIX (cache collision): Previously used urlparse path's first segment
    which collapses all /people/* URLs to slug 'people' and all /profile.php
    to 'profile.php' — causing every profile to overwrite the same avatar file.
    Now uses short SHA1 hash of full URL to guarantee uniqueness per profile.
    """
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def _cache_path(url: str) -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR / f"{_cache_key(url)}.json"


def _read_cache(url: str, ttl: int = _CACHE_TTL_SECONDS) -> PageMeta | None:
    p = _cache_path(url)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    fetched_ts = data.get("fetched_ts", 0)
    if time.time() - fetched_ts > ttl:
        return None
    meta = _meta_from_dict(url, data)
    # B.1 FIX: If avatar/cover was cleared (CDN URL expired), cache is stale —
    # invalidate so caller re-fetches fresh metadata with new CDN URLs.
    # C.2 FIX: But don't invalidate for profiles that genuinely have no avatar
    # (clean profiles without avatar, or FB-restricted profiles). Check a marker
    # field instead — if "avatar_checked" is True, profile was verified, keep cache.
    if not meta.avatar_url and not meta.cover_url and meta.title:
        if not data.get("avatar_checked", False):
            return None
    return meta


def _write_cache(url: str, meta: PageMeta, brand_id: str = "", source: str = "public") -> None:
    p = _cache_path(url)
    # B.1 FIX: Don't cache CDN URLs — they expire after ~6h (signature mismatch).
    # Only cache LOCAL file paths (stable). If avatar_url is a CDN URL, clear it
    # so next run re-fetches fresh metadata instead of using dead URL.
    avatar_to_cache = meta.avatar_url
    if avatar_to_cache and avatar_to_cache.startswith(("http://", "https://")):
        avatar_to_cache = ""  # CDN URL will be dead on cache hit → clear
    cover_to_cache = meta.cover_url
    if cover_to_cache and cover_to_cache.startswith(("http://", "https://")):
        cover_to_cache = ""
    payload = {
        "url": url,
        "title": meta.title,
        "description": meta.description,
        "avatar_url": avatar_to_cache,
        "cover_url": cover_to_cache,
        "is_verified": meta.is_verified,
        "created_year": meta.created_year,
        "recent_post_count_30d": meta.recent_post_count_30d,
        "fetched_at": meta.fetched_at,
        "fetched_ts": time.time(),
        # C.2: Mark that avatar was checked — prevents re-fetch of profiles
        # that genuinely have no avatar (clean profiles, FB-restricted accounts).
        "avatar_checked": True,
        # P3: Cache hardening — brand_id + source for namespace isolation
        "brand_id": brand_id,
        "source": source,
        "has_avatar": bool(avatar_to_cache and Path(avatar_to_cache).exists()),
        "has_cover": bool(cover_to_cache and Path(cover_to_cache).exists()),
    }
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _meta_from_dict(url: str, data: dict) -> PageMeta:
    return PageMeta(
        url=url,
        title=data.get("title", ""),
        description=data.get("description", ""),
        avatar_url=data.get("avatar_url", ""),
        cover_url=data.get("cover_url", ""),
        is_verified=data.get("is_verified", False),
        created_year=data.get("created_year"),
        recent_post_count_30d=data.get("recent_post_count_30d", 0),
        fetched_at=data.get("fetched_at", ""),
    )


def list_cached_urls(brand: "Brand | None" = None) -> list[str]:
    """List tất cả URL hợp lệ trong cache, optionally filter theo brand.

    Dùng cho --no-network mode: thay vì return empty khi không có URLs,
    đọc tất cả cache JSON files → lấy field "url" → filter official URLs.

    P3: Nếu cache entry có brand_id, chỉ trả URL match brand_id.
        Nếu cache entry không có brand_id (cache cũ), vẫn trả (backward-compatible).

    Args:
        brand: nếu truyền vào, loại trừ URL chính chủ của brand này + filter brand_id.

    Returns list of URLs.
    """
    urls: list[str] = []
    if not _CACHE_DIR.exists():
        return urls

    for f in _CACHE_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            url = data.get("url", "")
            if not url:
                continue
            # Skip stale entries (TTL check)
            fetched_ts = data.get("fetched_ts", 0)
            if time.time() - fetched_ts > _CACHE_TTL_SECONDS:
                continue
            # P3: brand_id filter — if entry has brand_id and it doesn't match, skip
            entry_brand_id = data.get("brand_id", "")
            if brand is not None and entry_brand_id and entry_brand_id != brand.id:
                continue
            # Filter official URLs
            if brand is not None:
                official_urls = {
                    brand.official_page_url.rstrip("/").lower(),
                    f"https://www.facebook.com/{brand.official_username}".rstrip("/").lower(),
                }
                if url.rstrip("/").lower() in official_urls:
                    continue
            urls.append(url)
        except (json.JSONDecodeError, OSError):
            continue
    return urls


def inspect_cache(brand_id: str | None = None) -> dict:
    """Inspect cache: count entries, stale count, by brand, by source.

    Returns dict with summary stats.
    """
    stats: dict = {
        "total": 0,
        "stale": 0,
        "valid": 0,
        "by_brand": {},
        "by_source": {},
        "with_avatar": 0,
        "with_cover": 0,
    }
    if not _CACHE_DIR.exists():
        return stats

    for f in _CACHE_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        stats["total"] += 1

        fetched_ts = data.get("fetched_ts", 0)
        is_stale = time.time() - fetched_ts > _CACHE_TTL_SECONDS
        if is_stale:
            stats["stale"] += 1
        else:
            stats["valid"] += 1

        bid = data.get("brand_id", "(legacy)")
        if brand_id and bid != brand_id and bid != "(legacy)":
            continue
        stats["by_brand"][bid] = stats["by_brand"].get(bid, 0) + 1

        source = data.get("source", "(unknown)")
        stats["by_source"][source] = stats["by_source"].get(source, 0) + 1

        if data.get("has_avatar"):
            stats["with_avatar"] += 1
        if data.get("has_cover"):
            stats["with_cover"] += 1

    return stats


def parse_page_meta(url: str, html: str) -> PageMeta:
    """Parse HTML Facebook page, trả về PageMeta."""
    soup = BeautifulSoup(html, "html.parser")

    def og(prop: str) -> str:
        tag = soup.find("meta", property=prop)
        return tag["content"].strip() if tag and tag.get("content") else ""

    title = og("og:title")
    avatar_url = og("og:image")
    description = og("og:description")
    if not description:
        desc_tag = soup.find("meta", attrs={"name": "description"})
        description = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else ""

    # Verified badge
    is_verified = bool(
        soup.find(attrs={"aria-label": re.compile(r"Verified", re.I)})
        or "Verified Page" in html
    )

    # Created year
    created_year: int | None = None
    m = _YEAR_RE.search(html)
    if m:
        try:
            created_year = int(m.group(1))
        except ValueError:
            pass

    # Recent posts (30d) — best-effort dựa vào data-utime
    cutoff = time.time() - 30 * 86400
    timestamps = [int(t) for t in _RECENT_POST_RE.findall(html)]
    recent_post_count_30d = sum(1 for ts in timestamps if ts >= cutoff)

    return PageMeta(
        url=url,
        title=title,
        description=description,
        avatar_url=avatar_url,
        cover_url="",  # cover thường trong meta og:image nếu chỉ có 1 image tag
        is_verified=is_verified,
        created_year=created_year,
        recent_post_count_30d=recent_post_count_30d,
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )


def _download_avatar_in_session(session: requests.Session, url: str, dest_path: Path) -> bool:
    """Download avatar/cover trong cùng session với page fetch để tránh 403 URL signature mismatch."""
    if not url:
        return False
    try:
        img_resp = session.get(url, timeout=15)
        if img_resp.status_code != 200:
            return False
        ct = img_resp.headers.get("Content-Type", "")
        if "image" not in ct:
            return False
        dest_path.write_bytes(img_resp.content)
        return True
    except Exception:
        return False


def _fetch_html_playwright(url: str, timeout_ms: int = 25000) -> tuple[str, requests.Session | None]:
    """Fetch HTML bằng Playwright (browser thật) cho profile FB block requests.
    Trả về (html, None) — session không cần vì avatar được download ngay trong browser context."""
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            context = browser.new_context(
                locale="vi-VN",
                viewport={"width": 1366, "height": 900},
            )
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            page = context.new_page()
            try:
                page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
            except PWTimeout:
                pass
            html = page.content()
            # Download avatar ngay trong context (session) để tránh URL signature expire
            return html, context
        finally:
            # Caller chịu trách nhiệm close context nếu cần
            pass


def fetch_page_meta_with_context(
    url: str,
    context,
    timeout_ms: int = 25000,
    download_avatar: bool = True,
) -> PageMeta:
    """Fetch metadata dùng Playwright context có sẵn (login hoặc ephemeral).

    Ưu điểm: dùng được session login → fetch đầy đủ, không bị login wall.
    Hỗ trợ download avatar + cover ngay trong context.
    """
    from playwright.sync_api import TimeoutError as PWTimeout
    import random
    import time

    cached = _read_cache(url)
    if cached is not None:
        return cached

    page = context.new_page()
    try:
        try:
            page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            page.wait_for_timeout(2500 + random.randint(500, 1500))
        except PWTimeout:
            pass

        html = page.content()
        if len(html) < 2000:
            # Có thể login wall hoặc redirect → thử lại
            page.wait_for_timeout(2000)
            html = page.content()

        meta = parse_page_meta(url, html)

        # B.3 FIX: Extract cover photo bằng DIMENSIONS (>800x250) thay vì alt text.
        # FB tiếng Việt không gán alt="Cover" → selector cũ miss.
        # Cover luôn lớn hơn avatar: avatar ~100-500px, cover ~800-1500px.
        try:
            cover_img = page.evaluate("""() => {
                const imgs = [...document.querySelectorAll('img')];
                // Ưu tiên: ảnh scontent, naturalWidth > 800, naturalHeight > 250,
                // KHÔNG phải avatar (path /t39.30808-1/ = avatar CDN pattern)
                for (const img of imgs) {
                    const src = img.src || '';
                    const w = img.naturalWidth || 0;
                    const h = img.naturalHeight || 0;
                    if (src.includes('scontent') && w > 800 && h > 250
                        && !src.includes('/t39.30808-1/')) {
                        return src;
                    }
                }
                return '';
            }""")
            if cover_img and not meta.cover_url:
                meta.cover_url = cover_img
        except Exception:
            pass

        # Download avatar + cover ngay trong context
        # Giữ CDN URL nếu download fail (sẽ retry pHash via download_to_temp)
        if download_avatar:
            slug = _slug_from_url(url)
            if meta.avatar_url:
                avatar_local = _CACHE_DIR / f"{slug}_avatar.jpg"
                if _download_avatar_via_page(page, meta.avatar_url, avatar_local):
                    meta.avatar_url = str(avatar_local)
            if meta.cover_url:
                cover_local = _CACHE_DIR / f"{slug}_cover.jpg"
                if _download_avatar_via_page(page, meta.cover_url, cover_local):
                    meta.cover_url = str(cover_local)

        _write_cache(url, meta)
        return meta
    finally:
        page.close()


def _download_avatar_via_page(page, url: str, dest_path: Path) -> bool:
    """Download avatar bằng cách fetch qua page context (giữ session + cookies)."""
    try:
        result = page.evaluate(
            """async (url) => {
                try {
                    const resp = await fetch(url, {credentials: 'include'});
                    if (!resp.ok) return '';
                    const blob = await resp.blob();
                    return await new Promise((resolve) => {
                        const reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result);
                        reader.readAsDataURL(blob);
                    });
                } catch (e) { return ''; }
            }""",
            url,
        )
        if not result or not result.startswith("data:"):
            return False
        # Parse data URL: data:image/jpeg;base64,<data>
        import base64
        header, b64 = result.split(",", 1)
        if "image" not in header:
            return False
        dest_path.write_bytes(base64.b64decode(b64))
        return True
    except Exception:
        return False


def fetch_page_meta(url: str, timeout: int = 15, use_playwright_fallback: bool = True) -> PageMeta:
    """Fetch HTML page (có cache), trả về PageMeta.
    Avatar/cover được download ngay trong cùng session để tránh FB CDN 403.

    FB có bot detection chặn requests module → trả HTML rỗng ~500 bytes.
    Fallback sang Playwright nếu requests trả về quá ít data."""
    cached = _read_cache(url)
    if cached is not None:
        return cached

    # Method 1: requests (nhanh, nhưng FB có thể block)
    session = requests.Session()
    session.headers.update(_HEADERS)
    html = ""
    try:
        resp = session.get(url, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        html = resp.text
    except Exception:
        pass

    # Nếu requests trả quá ít HTML (<2KB) → FB block → fallback Playwright
    if len(html) < 2000 and use_playwright_fallback:
        try:
            html_playwright, _ctx = _fetch_html_playwright(url)
            if len(html_playwright) > 2000:
                html = html_playwright
        except Exception as e:
            import sys
            print(f"[!] Playwright fallback failed for {url}: {e}", file=sys.stderr)

    if not html:
        return PageMeta(url=url, title="")

    meta = parse_page_meta(url, html)

    # Download avatar ngay trong session (FB CDN URL có signature thời hạn)
    # Quantitative: keep BOTH CDN URL (for fallback pHash via download_to_temp)
    # AND local path (preferred). Avatar local wins if download success.
    if meta.avatar_url:
        slug = _slug_from_url(url)
        avatar_local = _CACHE_DIR / f"{slug}_avatar.jpg"
        if _download_avatar_in_session(session, meta.avatar_url, avatar_local):
            meta.avatar_url = str(avatar_local)
        # else: giữ nguyên CDN URL — _phash_distance sẽ thử download lại
    if meta.cover_url:
        slug = _slug_from_url(url)
        cover_local = _CACHE_DIR / f"{slug}_cover.jpg"
        if _download_avatar_in_session(session, meta.cover_url, cover_local):
            meta.cover_url = str(cover_local)
    _write_cache(url, meta)
    return meta
