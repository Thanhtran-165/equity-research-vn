"""Tests cho scoring engine — weights mới (avatar 50, cover 30, name 15)
+ needs_semantic_check flag."""
from src.models import Brand, PageMeta, Trademark
from src.scoring import (
    score_page,
    _score_name,
    _score_avatar,
    _score_cover,
    _score_recency,
    _score_url,
)


def _brand(tmp_path=None):
    """Brand fixture với avatar/cover path có thể là file thật hoặc None."""
    avatar = str(tmp_path / "avatar.png") if tmp_path else "./tests/fixtures/fake_avatar.png"
    cover = str(tmp_path / "cover.png") if tmp_path else "./tests/fixtures/fake_cover.png"
    return Brand(
        id="fpt",
        display_name="FPT Shop",
        aliases=["FPT Shop", "FPTShop"],
        official_username="fptshop",
        official_page_url="https://www.facebook.com/fptshop",
        avatar_path=avatar,
        cover_path=cover,
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


# === NAME SCORING ===

def test_score_name_exact_match():
    page = PageMeta(url="https://www.facebook.com/fake", title="FPT Shop")
    assert _score_name(page, _brand(), _scoring_cfg()) == 15


def test_score_name_no_match():
    page = PageMeta(url="https://www.facebook.com/fake", title="Electronics Store")
    assert _score_name(page, _brand(), _scoring_cfg()) == 0


# === URL / WHITELIST ===

def test_score_url_exact_official_returns_zero():
    page = PageMeta(url="https://www.facebook.com/fptshop", title="FPT Shop")
    s = score_page(page, _brand(), _scoring_cfg())
    assert s.total == 0


def test_score_url_high_similarity():
    page = PageMeta(url="https://www.facebook.com/fptshop2026", title="FPT Shop")
    s = score_page(page, _brand(), _scoring_cfg())
    assert s.name == 15
    assert s.url in (0, 2)


# === RECENCY ===

def test_score_recency_high_for_2026():
    page = PageMeta(url="x", title="x", created_year=2026)
    assert _score_recency(page, _scoring_cfg()) == 3


def test_score_recency_zero_for_old():
    page = PageMeta(url="x", title="x", created_year=2018)
    assert _score_recency(page, _scoring_cfg()) == 0


def test_score_recency_override_when_verified():
    page = PageMeta(url="x", title="x", created_year=2026, is_verified=True)
    assert _score_recency(page, _scoring_cfg()) == 0


# === TOTAL / CLAMP ===

def test_total_clamped_at_zero():
    page = PageMeta(
        url="https://www.facebook.com/fptshop",
        title="FPT Shop",
        is_verified=True,
    )
    s = score_page(page, _brand(), _scoring_cfg())
    assert s.total == 0


# === AVATAR / COVER (pHash) ===

def _make_real_image(path, size=(32, 32)):
    """Tạo ảnh có entropy (không phải placeholder) cho test."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", size, color=(50, 50, 50))
    draw = ImageDraw.Draw(img)
    for x in range(0, size[0], 4):
        for y in range(0, size[1], 4):
            draw.rectangle([x, y, x + 2, y + 2], fill=(x * 8 % 256, y * 8 % 256, 100))
    img.save(path)
    return str(path)


def test_avatar_perfect_match(monkeypatch, tmp_path):
    from PIL import Image
    avatar = _make_real_image(tmp_path / "avatar.png")
    page_avatar_url = _make_real_image(tmp_path / "page.png")

    brand = Brand(
        id="x", display_name="X", aliases=["X"],
        official_username="x",
        official_page_url="https://www.facebook.com/x",
        avatar_path=avatar, cover_path=avatar,
    )
    page = PageMeta(
        url="https://www.facebook.com/y", title="X",
        avatar_url=page_avatar_url,
        cover_url=page_avatar_url,
    )

    import src.scoring as sc
    monkeypatch.setattr(sc, "_download_to_temp", lambda url: str(page_avatar_url))

    s = score_page(page, brand, _scoring_cfg())
    assert s.avatar == 50
    assert s.cover == 30


def test_avatar_no_match_returns_zero_no_flag():
    """Khi avatar_url rỗng → score 0, không flag semantic."""
    page = PageMeta(url="https://www.facebook.com/y", title="X")
    score, needs_check = _score_avatar(page, _brand(), _scoring_cfg())
    assert score == 0
    assert needs_check is False


def test_avatar_phash_miss_sets_semantic_flag(monkeypatch, tmp_path):
    """Khi pHash distance > weak (12) → score 0, needs_semantic_check=True."""
    from PIL import Image, ImageDraw
    import src.scoring as sc
    from src.models import Brand

    # Brand avatar: pattern có entropy (alternating colors)
    img_brand = Image.new("RGB", (64, 64), color=(10, 20, 30))
    draw_brand = ImageDraw.Draw(img_brand)
    for x in range(0, 64, 8):
        draw_brand.rectangle([x, 0, x + 4, 64], fill=(200, 100, 50))
    avatar = tmp_path / "brand.png"
    img_brand.save(avatar)

    # Page avatar: pattern khác hẳn → Hamming lớn
    img_page = Image.new("RGB", (64, 64), color=(255, 0, 0))
    draw = ImageDraw.Draw(img_page)
    for x in range(0, 64, 4):
        for y in range(0, 64, 4):
            draw.rectangle([x, y, x+2, y+2], fill=(0, 255, 0))
    page_avatar = tmp_path / "page.png"
    img_page.save(page_avatar)

    brand = Brand(
        id="x", display_name="X", aliases=["X"],
        official_username="x",
        official_page_url="https://www.facebook.com/x",
        avatar_path=str(avatar), cover_path=str(avatar),
    )
    page = PageMeta(
        url="https://www.facebook.com/y", title="X",
        avatar_url=str(page_avatar),
    )
    s = score_page(page, brand, _scoring_cfg())
    assert s.avatar == 0  # pHash miss (Hamming > 12)
    # name match + avatar miss → flag semantic check
    assert s.needs_semantic_check is True


def test_avatar_match_does_not_set_flag(monkeypatch, tmp_path):
    """Khi pHash match (Hamming ≤ 4) → không flag semantic."""
    import src.scoring as sc
    from src.models import Brand

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
    monkeypatch.setattr(sc, "_download_to_temp", lambda url: page_avatar)

    s = score_page(page, brand, _scoring_cfg())
    assert s.avatar == 50
    assert s.needs_semantic_check is False


def test_semantic_flag_off_when_name_doesnt_match(tmp_path):
    """Nếu tên KHÔNG match → không flag semantic (giảm false positive)."""
    from PIL import Image, ImageDraw
    from src.models import Brand

    # Brand avatar: pattern có entropy (alternating colors)
    img_brand = Image.new("RGB", (64, 64), color=(10, 20, 30))
    draw_brand = ImageDraw.Draw(img_brand)
    for x in range(0, 64, 8):
        draw_brand.rectangle([x, 0, x + 4, 64], fill=(200, 100, 50))
    avatar = tmp_path / "brand.png"
    img_brand.save(avatar)

    img_page = Image.new("RGB", (64, 64), color=(255, 0, 0))
    draw = ImageDraw.Draw(img_page)
    for x in range(0, 64, 4):
        for y in range(0, 64, 4):
            draw.rectangle([x, y, x+2, y+2], fill=(0, 255, 0))
    page_avatar = tmp_path / "page.png"
    img_page.save(page_avatar)

    brand = Brand(
        id="x", display_name="X", aliases=["X"],
        official_username="x",
        official_page_url="https://www.facebook.com/x",
        avatar_path=str(avatar), cover_path=str(avatar),
    )
    # title khác hoàn toàn brand
    page = PageMeta(
        url="https://www.facebook.com/y", title="Completely Different Name",
        avatar_url=str(page_avatar),
    )

    s = score_page(page, brand, _scoring_cfg())
    assert s.avatar == 0
    assert s.name == 0
    assert s.needs_semantic_check is False  # tên không match → không flag
