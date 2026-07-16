"""Tests cho preflight brand asset check + CLI exit codes."""
import io
import contextlib
from pathlib import Path
from PIL import Image, ImageDraw

from src.models import Brand
from src.scoring import preflight_brand_assets, _is_placeholder
from src.cli import main


def _brand_with_paths(avatar, cover):
    return Brand(
        id="test", display_name="Test", aliases=["Test"],
        official_username="test",
        official_page_url="https://www.facebook.com/test",
        avatar_path=str(avatar), cover_path=str(cover),
    )


def _make_real_image(path, size=(32, 32)):
    img = Image.new("RGB", size, color=(50, 50, 50))
    draw = ImageDraw.Draw(img)
    for x in range(0, size[0], 4):
        for y in range(0, size[1], 4):
            draw.rectangle([x, y, x + 2, y + 2], fill=(x * 8 % 256, y * 8 % 256, 100))
    img.save(path)
    return str(path)


# === preflight ===

def test_preflight_ok(tmp_path):
    """Brand avatar + cover OK → no errors."""
    avatar = _make_real_image(tmp_path / "avatar.png")
    cover = _make_real_image(tmp_path / "cover.png")
    brand = _brand_with_paths(avatar, cover)
    errors = preflight_brand_assets(brand)
    assert errors == []


def test_preflight_missing_avatar(tmp_path):
    """Avatar không tồn tại → error."""
    cover = _make_real_image(tmp_path / "cover.png")
    brand = _brand_with_paths("/nonexistent/avatar.png", cover)
    errors = preflight_brand_assets(brand)
    assert len(errors) == 1
    assert "avatar" in errors[0].lower()


def test_preflight_placeholder_avatar(tmp_path):
    """Avatar là placeholder (solid color) → error."""
    img = Image.new("RGB", (240, 240), color=(128, 128, 128))
    avatar = tmp_path / "avatar.png"
    img.save(avatar)
    cover = _make_real_image(tmp_path / "cover.png")
    brand = _brand_with_paths(str(avatar), cover)
    errors = preflight_brand_assets(brand)
    assert len(errors) == 1
    assert "placeholder" in errors[0].lower()


# === CLI exit codes ===

def test_cli_exit_code_config_error(tmp_path):
    """Config file không tồn tại → exit 2."""
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = main(["--config", str(tmp_path / "nonexistent.yaml"), "--no-network"])
    assert rc == 2


def test_cli_no_network_exit_zero(tmp_path, monkeypatch):
    """--no-network với empty cache → exit 0 (not error)."""
    cache_dir = tmp_path / "page_meta"
    cache_dir.mkdir()
    monkeypatch.setattr("src.page_meta._CACHE_DIR", cache_dir)

    config = """
brands:
  - id: test
    display_name: "Test"
    aliases: ["Test"]
    official_username: testbrand
    official_page_url: https://www.facebook.com/testbrand
    avatar_path: /dev/null
    cover_path: /dev/null
"""
    config_path = tmp_path / "brands.yaml"
    config_path.write_text(config)

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = main(["--config", str(config_path), "--brand", "test", "--no-network"])
    assert rc == 0


def test_cli_inspect_cache_exit_zero(tmp_path, monkeypatch):
    """--inspect-cache → exit 0."""
    cache_dir = tmp_path / "page_meta"
    cache_dir.mkdir()
    monkeypatch.setattr("src.page_meta._CACHE_DIR", cache_dir)

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = main(["--inspect-cache"])
    assert rc == 0
