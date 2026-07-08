from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Optional


class RiskBand(IntEnum):
    LOW = 0
    MID = 1
    HIGH = 2


@dataclass
class Trademark:
    vn_number: str = ""
    vn_class: str = ""
    meta_ip_rights_id: str = ""


@dataclass
class Brand:
    id: str
    display_name: str
    aliases: list[str]
    official_username: str
    official_page_url: str
    avatar_path: str
    cover_path: str
    trademark: Trademark = field(default_factory=Trademark)
    scoring_overrides: dict = field(default_factory=dict)


@dataclass
class PageMeta:
    url: str
    title: str
    description: str = ""
    avatar_url: str = ""
    cover_url: str = ""
    is_verified: bool = False
    created_year: Optional[int] = None
    recent_post_count_30d: int = 0
    fetched_at: str = ""


@dataclass
class ScoreResult:
    total: int
    name: int
    avatar: int
    cover: int
    recency: int
    url: int
    # Flag: True khi pHash miss (avatar/cover khác nhiều) nhưng có khả năng edit nhẹ.
    # Agent thấy flag → gọi analyze_image MCP để check semantic.
    needs_semantic_check: bool = False

    @property
    def band(self) -> RiskBand:
        if self.total >= 70:
            return RiskBand.HIGH
        if self.total >= 40:
            return RiskBand.MID
        return RiskBand.LOW


@dataclass
class ScoredPage:
    page: PageMeta
    score: ScoreResult


@dataclass
class ScanReport:
    brand_id: str
    run_at: str
    pages: list[ScoredPage] = field(default_factory=list)

    def iter_by_band(self, band: Optional[RiskBand] = None):
        items = sorted(self.pages, key=lambda p: p.score.total, reverse=True)
        if band is None:
            return items
        return [p for p in items if p.score.band == band]
