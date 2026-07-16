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


def _is_placeholder(img: Image.Image) -> bool:
    """Phát hiện ảnh placeholder/default (khối màu gần đồng nhất).

    Placeholder xám của FB có entropy rất thấp — gần như đồng nhất.
    Ảnh thật (avatar brand, avatar giả mạo) luôn có chi tiết → entropy cao.

    Dùng std dev của pixel values: <5.0 = placeholder, >=5.0 = ảnh thật.
    """
    import numpy as np
    arr = np.array(img.convert("L"))
    return float(arr.std()) < 5.0


def _phash_distance(image_path_or_url: str) -> imagehash.ImageHash | None:
    """Compute pHash từ path hoặc URL. Trả về None nếu fail.

    B.2 FIX: khi download URL fail (FB CDN 403 signature mismatch), log warning
    ra stderr để caller biết — không silent fail.

    C.1 FIX (revised): Thay vì reject theo file-size cứng (<5KB) — vốn reject cả
    ảnh thật nhỏ và test fixtures — dùng _is_placeholder() kiểm tra entropy pixel.
    Placeholder xám đồng nhất (FB default avatar) có std-dev < 5.0 → skip.
    Ảnh thật dù nhỏ vẫn pass.
    """
    if not image_path_or_url:
        return None
    local_temp: str | None = None
    try:
        if image_path_or_url.startswith(("http://", "https://")):
            local_temp = _download_to_temp(image_path_or_url)
            if not local_temp:
                import sys
                print(
                    f"[!] pHash: avatar download fail (likely FB CDN signature expired): "
                    f"{image_path_or_url[:80]}...",
                    file=sys.stderr,
                )
                return None
            img = Image.open(local_temp)
        else:
            p = Path(image_path_or_url)
            if not p.exists():
                import sys
                print(f"[!] pHash: local file not found: {image_path_or_url}", file=sys.stderr)
                return None
            img = Image.open(p)
        if _is_placeholder(img):
            import sys
            print(f"[!] pHash: placeholder image detected (low entropy), skipping: {image_path_or_url[:80]}",
                  file=sys.stderr)
            return None
        return imagehash.phash(img)
    except Exception as e:
        import sys
        print(f"[!] pHash: error computing hash: {e}", file=sys.stderr)
        return None
    finally:
        if local_temp:
            try:
                import os
                os.remove(local_temp)
            except OSError:
                pass
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


def preflight_brand_assets(brand: Brand) -> list[str]:
    """Check brand avatar + cover files exist and are not placeholders.

    Returns list of error messages (empty = all OK).
    Called before scan to fail-closed: if brand assets are broken,
    scoring will silently produce all-zero avatar/cover scores.
    """
    errors: list[str] = []
    for label, path in [("avatar", brand.avatar_path), ("cover", brand.cover_path)]:
        p = Path(path)
        if not p.exists():
            errors.append(f"{label} file not found: {path}")
            continue
        try:
            img = Image.open(p)
            img.verify()  # Verify it's a valid image
            img = Image.open(p)  # Reopen after verify
            if _is_placeholder(img):
                errors.append(f"{label} appears to be a placeholder/solid-color image: {path}")
        except Exception as e:
            errors.append(f"{label} cannot be opened as image: {path} ({e})")
    return errors


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


def _score_avatar(page: PageMeta, brand: Brand, cfg: dict[str, Any]) -> tuple[int, bool]:
    """Returns (score, needs_semantic_check).
    A.3 FIX: flag semantic check khi distance > moderate (8) thay vì > weak (12).
    Avatar nhỏ (200x200) pHash variance cao — format khác có thể Hamming 8-12.
    Hạ ngưỡng để catch nhiều hơn, giảm miss."""
    if not page.avatar_url or not brand.avatar_path:
        return (0, False)
    h1 = _phash_distance(page.avatar_url)
    h2 = _phash_distance(brand.avatar_path)
    if h1 is None or h2 is None:
        return (0, False)
    distance = h1 - h2
    score = _bucket_score(distance, cfg, "avatar")
    # pHash partial miss (distance > moderate) → flag semantic check
    needs_check = score <= 15 and distance > cfg["avatar_distance_moderate"]
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
    needs_check = score <= 8 and distance > cfg["cover_distance_moderate"]
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
