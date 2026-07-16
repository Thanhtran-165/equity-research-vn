"""Tests cho pHash: placeholder bị skip, ảnh thật (dù nhỏ) vẫn score đúng."""
from PIL import Image, ImageDraw
import numpy as np

from src.models import Brand, PageMeta
from src.scoring import (
    score_page,
    _phash_distance,
    _is_placeholder,
    _score_avatar,
    _score_cover,
)


def _scoring_cfg(**overrides):
    base = {
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
    base.update(overrides)
    return base


def _save_img(img, path):
    img.save(path)
    return str(path)


def _make_real_image(path, size=(32, 32)):
    """Tạo ảnh có entropy (không phải placeholder) cho test."""
    img = Image.new("RGB", size, color=(50, 50, 50))
    draw = ImageDraw.Draw(img)
    for x in range(0, size[0], 4):
        for y in range(0, size[1], 4):
            draw.rectangle([x, y, x + 2, y + 2], fill=(x * 8 % 256, y * 8 % 256, 100))
    img.save(path)
    return str(path)


# === _is_placeholder ===

def test_placeholder_solid_gray_detected():
    """Ảnh xám đồng nhất (FB placeholder) → _is_placeholder = True."""
    img = Image.new("RGB", (240, 240), color=(128, 128, 128))
    assert _is_placeholder(img) is True


def test_placeholder_solid_white_detected():
    """Ảnh trắng đồng nhất → _is_placeholder = True."""
    img = Image.new("RGB", (240, 240), color=(255, 255, 255))
    assert _is_placeholder(img) is True


def test_real_image_not_placeholder():
    """Ảnh có chi tiết (avatar thật) → _is_placeholder = False."""
    img = Image.new("RGB", (64, 64), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    for x in range(0, 64, 4):
        for y in range(0, 64, 4):
            draw.rectangle([x, y, x + 2, y + 2], fill=(0, 255, 0))
    assert _is_placeholder(img) is False


# === pHash match với ảnh thật nhỏ ===

def test_avatar_perfect_match_small_file(tmp_path):
    """Ảnh thật nhỏ (dưới 5KB cũ threshold) vẫn score 50 khi match."""
    avatar = _make_real_image(tmp_path / "avatar.png", size=(32, 32))
    page_avatar = _make_real_image(tmp_path / "page.png", size=(32, 32))

    brand = Brand(
        id="x", display_name="X", aliases=["X"],
        official_username="x",
        official_page_url="https://www.facebook.com/x",
        avatar_path=avatar, cover_path=avatar,
    )
    page = PageMeta(
        url="https://www.facebook.com/y", title="X",
        avatar_url=page_avatar,
        cover_url=page_avatar,
    )

    s = score_page(page, brand, _scoring_cfg())
    assert s.avatar == 50
    assert s.cover == 30


def test_avatar_match_does_not_set_flag(tmp_path):
    """pHash match → không flag semantic."""
    avatar = _make_real_image(tmp_path / "avatar.png")
    page_avatar = _make_real_image(tmp_path / "page.png")

    brand = Brand(
        id="x", display_name="X", aliases=["X"],
        official_username="x",
        official_page_url="https://www.facebook.com/x",
        avatar_path=avatar, cover_path=avatar,
    )
    page = PageMeta(
        url="https://www.facebook.com/y", title="X",
        avatar_url=page_avatar,
    )

    s = score_page(page, brand, _scoring_cfg())
    assert s.avatar == 50
    assert s.needs_semantic_check is False


# === pHash placeholder bị skip ===

def test_placeholder_avatar_returns_none_phash(tmp_path):
    """Placeholder xám → _phash_distance returns None."""
    img = Image.new("RGB", (240, 240), color=(128, 128, 128))
    placeholder = _save_img(img, tmp_path / "placeholder.jpg")

    result = _phash_distance(placeholder)
    assert result is None


def test_placeholder_does_not_false_positive(tmp_path):
    """Placeholder xám trên cả brand + page → avatar score = 0 (không match giả)."""
    img = Image.new("RGB", (240, 240), color=(128, 128, 128))
    placeholder = _save_img(img, tmp_path / "placeholder.jpg")

    brand = Brand(
        id="x", display_name="X", aliases=["X"],
        official_username="x",
        official_page_url="https://www.facebook.com/x",
        avatar_path=placeholder, cover_path=placeholder,
    )
    page = PageMeta(
        url="https://www.facebook.com/y", title="X",
        avatar_url=placeholder,
        cover_url=placeholder,
    )

    s = score_page(page, brand, _scoring_cfg())
    # Placeholder → _phash_distance returns None → score 0
    assert s.avatar == 0
    assert s.cover == 0


# === pHash miss → semantic flag ===

def test_avatar_phash_miss_sets_semantic_flag(tmp_path):
    """Khi pHash distance > weak → score 0, needs_semantic_check=True."""
    img_brand = Image.new("RGB", (64, 64), color=(10, 20, 30))
    draw_brand = ImageDraw.Draw(img_brand)
    for x in range(0, 64, 8):
        draw_brand.rectangle([x, 0, x + 4, 64], fill=(200, 100, 50))
    avatar = _save_img(img_brand, tmp_path / "brand.png")

    img_page = Image.new("RGB", (64, 64), color=(255, 0, 0))
    draw = ImageDraw.Draw(img_page)
    for x in range(0, 64, 4):
        for y in range(0, 64, 4):
            draw.rectangle([x, y, x + 2, y + 2], fill=(0, 255, 0))
    page_avatar = _save_img(img_page, tmp_path / "page.png")

    brand = Brand(
        id="x", display_name="X", aliases=["X"],
        official_username="x",
        official_page_url="https://www.facebook.com/x",
        avatar_path=avatar, cover_path=avatar,
    )
    page = PageMeta(
        url="https://www.facebook.com/y", title="X",
        avatar_url=page_avatar,
    )

    s = score_page(page, brand, _scoring_cfg())
    assert s.avatar == 0
    assert s.needs_semantic_check is True
