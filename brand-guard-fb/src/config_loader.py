from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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
    "recent_years": [2025, 2026],
    # Note: risk band cutoffs (HIGH≥70, MID≥40) are hardcoded in ScoreResult.band
    # (models.py) and are not user-overridable via config.
}


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


def _parse_brand(raw: dict) -> Brand:
    required = ["id", "display_name", "aliases", "official_username",
                "official_page_url", "avatar_path", "cover_path"]
    for field_name in required:
        if field_name not in raw:
            raise ConfigError(f"Brand missing required field: {field_name}")
    tm_raw = raw.get("trademark", {}) or {}
    return Brand(
        id=raw["id"],
        display_name=raw["display_name"],
        aliases=list(raw["aliases"]),
        official_username=raw["official_username"],
        official_page_url=raw["official_page_url"],
        avatar_path=raw["avatar_path"],
        cover_path=raw["cover_path"],
        trademark=Trademark(
            vn_number=tm_raw.get("vn_number", ""),
            vn_class=tm_raw.get("vn_class", ""),
            meta_ip_rights_id=tm_raw.get("meta_ip_rights_id", ""),
        ),
        scoring_overrides=raw.get("scoring_overrides", {}) or {},
    )


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    scoring = _deep_merge(DEFAULT_SCORING, (data.get("defaults") or {}).get("scoring", {}))
    raw_brands = data.get("brands", []) or []
    if not raw_brands:
        raise ConfigError("Config must contain at least one brand under 'brands:'")
    brands = [_parse_brand(b) for b in raw_brands]
    return AppConfig(brands=brands, scoring=scoring)
