from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import imagehash
import requests
from PIL import Image
from rapidfuzz import fuzz

from src.models import Brand, PageMeta, ScoreResult


def _slug(url: str) -> str:
    path = urlparse(url).path.strip("/")
    return path.split("/")[0] if path else ""


def _score_name(page: PageMeta, brand: Brand, cfg: dict[str, Any]) -> int:
    if not page.title:
        return 0
    ratios = [fuzz.token_set_ratio(page.title, alias) for alias in brand.aliases]
    best = max(ratios) if ratios else 0
    if best >= cfg["name_threshold_high"]:
        return 15
    if best >= cfg["name_threshold_mid"]:
        return 8
    return 0


def _score_url(page: PageMeta, brand: Brand) -> int:
    slug = _slug(page.url).lower()
    official = brand.official_username.lower()
    if not slug or not official:
        return 0
    r = fuzz.token_set_ratio(slug, official)
    if r >= 85:
        return 2
    return 0


def _phash_distance(image_path_or_url: str) -> imagehash.ImageHash | None:
    """Compute pHash từ path hoặc URL. Trả về None nếu fail."""
    if not image_path_or_url:
        return None
    local_temp: str | None = None
    try:
        if image_path_or_url.startswith(("http://", "https://")):
            local_temp = _download_to_temp(image_path_or_url)
            if not local_temp:
                return None
            img = Image.open(local_temp)
        else:
            p = Path(image_path_or_url)
            if not p.exists():
                return None
            img = Image.open(p)
        return imagehash.phash(img)
    except Exception:
        return None
    finally:
        if local_temp:
            try:
                import os
                os.remove(local_temp)
            except OSError:
                pass


def _download_to_temp(url: str) -> str | None:
    try:
        resp = requests.get(url, timeout=15, stream=True)
        resp.raise_for_status()
        suffix = ".jpg"
        ct = resp.headers.get("Content-Type", "")
        if "png" in ct:
            suffix = ".png"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
            return f.name
    except Exception:
        return None


def _bucket_score(distance: int, cfg: dict[str, Any], prefix: str) -> int:
    """Avatar + Cover scoring theo weights mới (avatar 50, cover 30)."""
    if prefix == "avatar":
        if distance <= cfg["avatar_distance_strong"]:
            return 50
        if distance <= cfg["avatar_distance_moderate"]:
            return 35
        if distance <= cfg["avatar_distance_weak"]:
            return 15
    else:  # cover
        if distance <= cfg["cover_distance_strong"]:
            return 30
        if distance <= cfg["cover_distance_moderate"]:
            return 20
        if distance <= cfg["cover_distance_weak"]:
            return 8
    return 0
    return 0


def _score_avatar(page: PageMeta, brand: Brand, cfg: dict[str, Any]) -> tuple[int, bool]:
    """Returns (score, needs_semantic_check).
    needs_semantic_check=True khi pHash miss (distance > weak) NHƯNG avatar có
    → có thể bị edit nhẹ (filter/crop/recolor), agent nên dùng analyze_image."""
    if not page.avatar_url or not brand.avatar_path:
        return (0, False)
    h1 = _phash_distance(page.avatar_url)
    h2 = _phash_distance(brand.avatar_path)
    if h1 is None or h2 is None:
        return (0, False)
    distance = h1 - h2
    score = _bucket_score(distance, cfg, "avatar")
    # pHash miss (distance > weak) nhưng có avatar → flag semantic check
    needs_check = score == 0 and distance > cfg["avatar_distance_weak"]
    return (score, needs_check)


def _score_cover(page: PageMeta, brand: Brand, cfg: dict[str, Any]) -> tuple[int, bool]:
    """Returns (score, needs_semantic_check). See _score_avatar."""
    if not page.cover_url or not brand.cover_path:
        return (0, False)
    h1 = _phash_distance(page.cover_url)
    h2 = _phash_distance(brand.cover_path)
    if h1 is None or h2 is None:
        return (0, False)
    distance = h1 - h2
    score = _bucket_score(distance, cfg, "cover")
    needs_check = score == 0 and distance > cfg["cover_distance_weak"]
    return (score, needs_check)


def _score_recency(page: PageMeta, cfg: dict[str, Any]) -> int:
    """Recency signal — minor (3pts). Chỉ bonus nhẹ cho profile mới."""
    if page.is_verified:
        return 0
    score = 0
    if page.created_year and page.created_year in cfg["recent_years"]:
        score += 3
    return score


def score_page(page: PageMeta, brand: Brand, cfg: dict[str, Any]) -> ScoreResult:
    """Chấm điểm 1 page. Trả về total=0 nếu là chính chủ."""
    # Whitelist chính chủ
    page_url_norm = page.url.rstrip("/").lower()
    official_urls = {
        brand.official_page_url.rstrip("/").lower(),
        f"https://www.facebook.com/{brand.official_username}".lower(),
    }
    if page_url_norm in official_urls:
        return ScoreResult(total=0, name=0, avatar=0, cover=0, recency=0, url=0)

    name = _score_name(page, brand, cfg)
    avatar_score, avatar_needs_check = _score_avatar(page, brand, cfg)
    cover_score, cover_needs_check = _score_cover(page, brand, cfg)
    recency = _score_recency(page, cfg)
    url = _score_url(page, brand)

    # needs_semantic_check = True khi pHash miss NHƯNG có avatar/cover (có thể edit nhẹ)
    # Chỉ flag khi tên cũng match (giảm false positive)
    needs_check = (avatar_needs_check or cover_needs_check) and name > 0

    # Nếu verified → tổng = 0 (chính chủ)
    if page.is_verified:
        return ScoreResult(
            total=0, name=name, avatar=avatar_score, cover=cover_score,
            recency=0, url=url, needs_semantic_check=False,
        )

    total = max(0, name + avatar_score + cover_score + recency + url)
    return ScoreResult(
        total=total, name=name, avatar=avatar_score, cover=cover_score,
        recency=recency, url=url, needs_semantic_check=needs_check,
    )
