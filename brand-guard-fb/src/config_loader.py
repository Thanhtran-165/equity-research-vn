from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from src.models import Brand, Trademark


DEFAULT_SCORING = {
    "name_threshold_high": 90,
    "name_threshold_mid": 80,
    "avatar_distance_strong": 4,
    "avatar_distance_moderate": 8,
    "avatar_distance_weak": 12,
    "cover_distance_strong": 4,
    "cover_distance_moderate": 8,
    "cover_distance_weak": 12,
    "recent_years": None,
}


def _resolve_defaults(scoring: dict) -> dict:
    if scoring.get("recent_years") is None:
        from datetime import datetime
        now = datetime.now().year
        scoring["recent_years"] = [now, now - 1]
    return scoring


class ConfigError(Exception):
    pass


@dataclass
class AppConfig:
    brands: list[Brand] = field(default_factory=list)
    scoring: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_SCORING))


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _validate_url(url: str, field_name: str, brand_id: str) -> None:
    """Validate URL is well-formed and points to facebook.com."""
    if not url:
        raise ConfigError(f"Brand '{brand_id}': {field_name} is empty")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ConfigError(f"Brand '{brand_id}': {field_name} must be http/https URL, got: {url}")
    if "facebook.com" not in (parsed.netloc or ""):
        raise ConfigError(f"Brand '{brand_id}': {field_name} must point to facebook.com, got: {parsed.netloc}")


def _validate_scoring(scoring: dict) -> None:
    """Validate scoring thresholds are sane."""
    for key in ("name_threshold_high", "name_threshold_mid"):
        v = scoring.get(key)
        if not isinstance(v, (int, float)) or not (0 <= v <= 100):
            raise ConfigError(f"scoring.{key} must be 0-100, got: {v}")
    if scoring["name_threshold_high"] < scoring["name_threshold_mid"]:
        raise ConfigError(
            f"name_threshold_high ({scoring['name_threshold_high']}) < "
            f"name_threshold_mid ({scoring['name_threshold_mid']})"
        )
    for prefix in ("avatar", "cover"):
        for suffix in ("strong", "moderate", "weak"):
            key = f"{prefix}_distance_{suffix}"
            v = scoring.get(key)
            if not isinstance(v, int) or v < 0 or v > 64:
                raise ConfigError(f"scoring.{key} must be 0-64, got: {v}")
        if scoring[f"{prefix}_distance_strong"] > scoring[f"{prefix}_distance_moderate"]:
            raise ConfigError(f"{prefix}: strong > moderate distance")
        if scoring[f"{prefix}_distance_moderate"] > scoring[f"{prefix}_distance_weak"]:
            raise ConfigError(f"{prefix}: moderate > weak distance")


def _parse_brand(raw: dict) -> Brand:
    required = ["id", "display_name", "aliases", "official_username",
                "official_page_url", "avatar_path", "cover_path"]
    for field_name in required:
        if field_name not in raw:
            raise ConfigError(f"Brand missing required field: {field_name}")

    brand_id = raw["id"]
    aliases = list(raw["aliases"])
    if not aliases:
        raise ConfigError(f"Brand '{brand_id}': aliases must not be empty")

    avatar_path = raw["avatar_path"]
    cover_path = raw["cover_path"]

    _validate_url(raw["official_page_url"], "official_page_url", brand_id)

    # Check avatar/cover exist (relative to cwd)
    if not Path(avatar_path).exists():
        raise ConfigError(
            f"Brand '{brand_id}': avatar_path not found: {avatar_path}. "
            f"Copy brand avatar to config/avatars/ before scanning."
        )
    if not Path(cover_path).exists():
        raise ConfigError(
            f"Brand '{brand_id}': cover_path not found: {cover_path}. "
            f"Copy brand cover to config/avatars/ before scanning."
        )

    tm_raw = raw.get("trademark", {}) or {}
    return Brand(
        id=brand_id,
        display_name=raw["display_name"],
        aliases=aliases,
        official_username=raw["official_username"],
        official_page_url=raw["official_page_url"],
        avatar_path=avatar_path,
        cover_path=cover_path,
        trademark=Trademark(
            vn_number=tm_raw.get("vn_number", ""),
            vn_class=tm_raw.get("vn_class", ""),
            meta_ip_rights_id=tm_raw.get("meta_ip_rights_id", ""),
        ),
        scoring_overrides=raw.get("scoring_overrides", {}) or {},
    )


def load_config(path: Path, validate_assets: bool = True) -> AppConfig:
    """Load and validate config.

    Args:
        path: Path to brands.yaml
        validate_assets: If True (default), check avatar/cover files exist.
                         Set False for tests where assets aren't real files.
    """
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    scoring = _deep_merge(DEFAULT_SCORING, (data.get("defaults") or {}).get("scoring", {}))
    scoring = _resolve_defaults(scoring)
    _validate_scoring(scoring)

    raw_brands = data.get("brands", []) or []
    if not raw_brands:
        raise ConfigError("Config must contain at least one brand under 'brands:'")

    brands = []
    for raw in raw_brands:
        if not validate_assets:
            # Temporarily skip asset existence check
            old_avatar = raw.get("avatar_path", "")
            old_cover = raw.get("cover_path", "")
            raw["avatar_path"] = "/dev/null"
            raw["cover_path"] = "/dev/null"
            brand = _parse_brand(raw)
            brand.avatar_path = old_avatar
            brand.cover_path = old_cover
            brands.append(brand)
        else:
            brands.append(_parse_brand(raw))

    # Check brand IDs unique
    ids = [b.id for b in brands]
    if len(ids) != len(set(ids)):
        raise ConfigError(f"Duplicate brand IDs: {ids}")

    return AppConfig(brands=brands, scoring=scoring)
