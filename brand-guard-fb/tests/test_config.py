"""Tests cho config validation fail-closed."""
import pytest
from pathlib import Path

from src.config_loader import load_config, ConfigError


def _write_config(tmp_path, content):
    p = tmp_path / "brands.yaml"
    p.write_text(content)
    return p


def test_config_missing_avatar_path(tmp_path):
    """avatar_path không tồn tại → ConfigError."""
    config = """
brands:
  - id: test
    display_name: "Test"
    aliases: ["Test"]
    official_username: testbrand
    official_page_url: https://www.facebook.com/testbrand
    avatar_path: /nonexistent/avatar.png
    cover_path: /nonexistent/cover.png
"""
    p = _write_config(tmp_path, config)
    with pytest.raises(ConfigError, match="avatar_path not found"):
        load_config(p)


def test_config_empty_aliases(tmp_path):
    """aliases rỗng → ConfigError."""
    config = """
brands:
  - id: test
    display_name: "Test"
    aliases: []
    official_username: testbrand
    official_page_url: https://www.facebook.com/testbrand
    avatar_path: /dev/null
    cover_path: /dev/null
"""
    p = _write_config(tmp_path, config)
    with pytest.raises(ConfigError, match="aliases must not be empty"):
        load_config(p)


def test_config_invalid_url(tmp_path):
    """official_page_url không phải facebook.com → ConfigError."""
    config = """
brands:
  - id: test
    display_name: "Test"
    aliases: ["Test"]
    official_username: testbrand
    official_page_url: https://twitter.com/testbrand
    avatar_path: /dev/null
    cover_path: /dev/null
"""
    p = _write_config(tmp_path, config)
    with pytest.raises(ConfigError, match="must point to facebook.com"):
        load_config(p)


def test_config_duplicate_brand_ids(tmp_path):
    """Duplicate brand IDs → ConfigError."""
    config = """
brands:
  - id: test
    display_name: "Test A"
    aliases: ["Test A"]
    official_username: testbranda
    official_page_url: https://www.facebook.com/testbranda
    avatar_path: /dev/null
    cover_path: /dev/null
  - id: test
    display_name: "Test B"
    aliases: ["Test B"]
    official_username: testbrandb
    official_page_url: https://www.facebook.com/testbrandb
    avatar_path: /dev/null
    cover_path: /dev/null
"""
    p = _write_config(tmp_path, config)
    with pytest.raises(ConfigError, match="Duplicate brand IDs"):
        load_config(p)


def test_config_validate_assets_false_skips_check(tmp_path):
    """validate_assets=False → skip avatar/cover existence check."""
    config = """
brands:
  - id: test
    display_name: "Test"
    aliases: ["Test"]
    official_username: testbrand
    official_page_url: https://www.facebook.com/testbrand
    avatar_path: /nonexistent/avatar.png
    cover_path: /nonexistent/cover.png
"""
    p = _write_config(tmp_path, config)
    cfg = load_config(p, validate_assets=False)
    assert len(cfg.brands) == 1
    assert cfg.brands[0].id == "test"


def test_config_scoring_threshold_order(tmp_path):
    """name_threshold_high < name_threshold_mid → ConfigError."""
    config = """
defaults:
  scoring:
    name_threshold_high: 70
    name_threshold_mid: 90
brands:
  - id: test
    display_name: "Test"
    aliases: ["Test"]
    official_username: testbrand
    official_page_url: https://www.facebook.com/testbrand
    avatar_path: /dev/null
    cover_path: /dev/null
"""
    p = _write_config(tmp_path, config)
    with pytest.raises(ConfigError, match="threshold_high.*<.*threshold_mid"):
        load_config(p)
