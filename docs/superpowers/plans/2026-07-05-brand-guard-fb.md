# Brand Guard FB — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây dựng ZCode skill `brand-guard-fb` tự dò fanpage Facebook giả mạo theo tên + avatar + ảnh bìa + heuristic "trang mới", chấm điểm rủi ro, render markdown report trong ZCode, và sinh mẫu đơn khiếu nại Meta IP + SHTT Việt Nam.

**Architecture:** Pipeline 7 bước dạng CLI Python: load `brands.yaml` → query DuckDuckGo HTML (fallback Bing) → lọc URL page → fetch OG metadata (cache 24h tại `.cache/`) → chấm điểm 5 tín hiệu → render markdown → sinh mẫu đơn khiếu nại. Skill đặt tại `/Users/bobo/.zcode/skills/brand-guard-fb/`. Code ở `src/`, test ở `tests/`, template ở `templates/`. Mỗi layer (`search`, `page_meta`, `scoring`, `report`) có interface rõ ràng, test độc lập. Tuân thủ TDD: test viết trước, run fail, implement, run pass, commit.

**Tech Stack:** Python 3.11+, rapidfuzz (fuzzy string), imagehash + Pillow (perceptual hash), requests + beautifulsoup4 (HTTP + parse), pyyaml (config), pytest (test). Không cần Meta Graph API, không cần access token.

**Spec reference:** `docs/superpowers/specs/2026-07-05-brand-guard-fb-design.md`

---

## File Structure

**Skill root:** `/Users/bobo/.zcode/skills/brand-guard-fb/`

| File | Trách nhiệm |
|---|---|
| `SKILL.md` | ZCode manifest (YAML frontmatter + hướng dẫn dùng) |
| `requirements.txt` | Lock dependencies |
| `.gitignore` | Bỏ qua `.cache/`, `config/avatars/`, `__pycache__/` |
| `config/brands.example.yaml` | Sample config cho user copy |
| `src/__init__.py` | Package marker |
| `src/models.py` | Dataclass `Brand`, `PageMeta`, `ScoreResult`, `ScanReport` |
| `src/config_loader.py` | Load + validate `brands.yaml`, merge defaults |
| `src/search.py` | Sinh dorks, query DDG/Bing HTML, parse link, lọc URL |
| `src/page_meta.py` | Fetch OG metadata + heuristics HTML, cache 24h |
| `src/scoring.py` | Pure function chấm điểm 5 tín hiệu |
| `src/report.py` | Render markdown table + summary |
| `src/takedown_template.py` | Render mẫu đơn Meta + SHTT từ template |
| `src/cli.py` | Entry point argparse, orchestrate pipeline |
| `templates/meta_ip_report.md` | Mẫu Meta IP infringement (EN) |
| `templates/shtt_complaint_vi.md` | Mẫu đơn SHTT VN (Nghị định 65/2023) |
| `tests/__init__.py` | Package marker |
| `tests/test_scoring.py` | Unit test scoring |
| `tests/test_search.py` | Unit test dork generation + URL filter |
| `tests/test_config_loader.py` | Unit test config validation |
| `tests/test_report.py` | Unit test markdown render |
| `tests/test_page_meta.py` | Unit test OG parser với fixture HTML |
| `tests/fixtures/fake_page.html` | Sample FB page HTML để test parser |

**Working directory note:** Vì skill nằm ngoài git repo chính (`/Users/bobo/.zcode/skills/`), mình sẽ **code trong workspace `/Users/bobo/ZCodeProject/brand-guard-fb/`** (có git), test xong copy/symlink vào `/Users/bobo/.zcode/skills/brand-guard-fb/` ở task cuối. Cách này giữ code trong repo có version control.

---

## Task 1: Scaffold project + dependencies

**Files:**
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/requirements.txt`
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/.gitignore`
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/src/__init__.py`
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/tests/__init__.py`
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/config/brands.example.yaml`
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/.cache/.gitkeep`
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/config/avatars/.gitkeep`

- [ ] **Step 1: Tạo cấu trúc thư mục**

```bash
mkdir -p /Users/bobo/ZCodeProject/brand-guard-fb/{src,tests,config/avatars,templates,.cache}
touch /Users/bobo/ZCodeProject/brand-guard-fb/{src,tests}/__init__.py
touch /Users/bobo/ZCodeProject/brand-guard-fb/{.cache,config/avatars}/.gitkeep
```

- [ ] **Step 2: Viết `requirements.txt`**

```
rapidfuzz>=3.0.0
imagehash>=4.3.0
Pillow>=10.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
pyyaml>=6.0
pytest>=7.4.0
```

- [ ] **Step 3: Viết `.gitignore`**

```
__pycache__/
*.pyc
.cache/*
!.cache/.gitkeep
config/avatars/*
!config/avatars/.gitkeep
.venv/
.pytest_cache/
```

- [ ] **Step 4: Viết `config/brands.example.yaml`** (sample để user copy thành `brands.yaml`)

```yaml
defaults:
  scoring:
    name_threshold_high: 90
    name_threshold_mid: 80
    avatar_distance_strong: 4
    avatar_distance_moderate: 8
    avatar_distance_weak: 12
    cover_distance_strong: 4
    cover_distance_moderate: 8
    cover_distance_weak: 12
    recent_years: [2025, 2026]
    risk_high: 70
    risk_mid: 40

brands:
  - id: example_brand
    display_name: "Example Brand"
    aliases:
      - "Example Brand"
      - "ExampleBrand"
    official_username: "examplebrand"
    official_page_url: "https://www.facebook.com/examplebrand"
    avatar_path: "./config/avatars/example_avatar.png"
    cover_path: "./config/avatars/example_cover.png"
    trademark:
      vn_number: "00000-2020"
      vn_class: "9"
      meta_ip_rights_id: ""
    scoring_overrides: {}
```

- [ ] **Step 5: Cài dependencies trong venv**

```bash
cd /Users/bobo/ZCodeProject/brand-guard-fb
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 6: Verify pytest chạy được**

```bash
cd /Users/bobo/ZCodeProject/brand-guard-fb
source .venv/bin/activate
pytest --version
```
Expected: `pytest 7.x.x` (hoặc mới hơn).

- [ ] **Step 7: Commit**

```bash
cd /Users/bobo/ZCodeProject
git add brand-guard-fb/
git commit -m "feat(brand-guard-fb): scaffold project structure + dependencies"
```

---

## Task 2: Data models (`src/models.py`)

**Files:**
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/src/models.py`
- Test: `/Users/bobo/ZCodeProject/brand-guard-fb/tests/test_models.py`

- [ ] **Step 1: Viết failing test**

`tests/test_models.py`:
```python
from src.models import Brand, PageMeta, ScoreResult, ScanReport, RiskBand


def test_brand_minimum():
    b = Brand(
        id="x",
        display_name="X",
        aliases=["X"],
        official_username="x",
        official_page_url="https://www.facebook.com/x",
        avatar_path="./a.png",
        cover_path="./c.png",
    )
    assert b.id == "x"
    assert b.trademark.vn_number == ""


def test_pagemeta_defaults():
    p = PageMeta(url="https://www.facebook.com/foo", title="Foo")
    assert p.is_verified is False
    assert p.created_year is None
    assert p.recent_post_count_30d == 0


def test_scoreresult_classify_high():
    s = ScoreResult(total=92, name=35, avatar=25, cover=20, recency=12, url=0)
    assert s.band == RiskBand.HIGH


def test_scoreresult_classify_low():
    s = ScoreResult(total=22, name=22, avatar=0, cover=0, recency=0, url=0)
    assert s.band == RiskBand.LOW


def test_scanreport_iter():
    r = ScanReport(brand_id="x", run_at="2026-07-05T14:30+07:00", pages=[])
    assert list(r.iter_by_band()) == []
```

- [ ] **Step 2: Run test, expect ImportError**

Run: `pytest tests/test_models.py -v`
Expected: FAIL với `ModuleNotFoundError: No module named 'src.models'`

- [ ] **Step 3: Implement `src/models.py`**

```python
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
```

- [ ] **Step 4: Run test, expect PASS**

Run: `pytest tests/test_models.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add brand-guard-fb/src/models.py brand-guard-fb/tests/test_models.py
git commit -m "feat(brand-guard-fb): add data models — Brand, PageMeta, ScoreResult, ScanReport"
```

---

## Task 3: Config loader (`src/config_loader.py`)

**Files:**
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/src/config_loader.py`
- Test: `/Users/bobo/ZCodeProject/brand-guard-fb/tests/test_config_loader.py`

- [ ] **Step 1: Viết failing test**

`tests/test_config_loader.py`:
```python
from pathlib import Path

import pytest

from src.config_loader import load_config, ConfigError


@pytest.fixture
def tmp_config(tmp_path):
    cfg = tmp_path / "brands.yaml"
    cfg.write_text(
        """
defaults:
  scoring:
    name_threshold_high: 90
    name_threshold_mid: 80
    risk_high: 70
    risk_mid: 40
brands:
  - id: fpt
    display_name: "FPT Shop"
    aliases: ["FPT Shop", "FPTShop"]
    official_username: "fptshop"
    official_page_url: "https://www.facebook.com/fptshop"
    avatar_path: "./a.png"
    cover_path: "./c.png"
"""
    )
    return cfg


def test_load_ok(tmp_config):
    cfg = load_config(Path(tmp_config))
    assert len(cfg.brands) == 1
    b = cfg.brands[0]
    assert b.display_name == "FPT Shop"
    assert b.aliases == ["FPT Shop", "FPTShop"]
    assert cfg.scoring["name_threshold_high"] == 90


def test_missing_brand_field(tmp_path):
    bad = tmp_path / "brands.yaml"
    bad.write_text(
        """
defaults: {scoring: {risk_high: 70, risk_mid: 40}}
brands:
  - id: x
    display_name: "X"
"""
    )
    with pytest.raises(ConfigError, match="aliases"):
        load_config(Path(bad))


def test_default_scoring_when_missing(tmp_path):
    cfg_file = tmp_path / "brands.yaml"
    cfg_file.write_text(
        """
brands:
  - id: x
    display_name: "X"
    aliases: ["X"]
    official_username: "x"
    official_page_url: "https://www.facebook.com/x"
    avatar_path: "./a.png"
    cover_path: "./c.png"
"""
    )
    cfg = load_config(Path(cfg_file))
    assert cfg.scoring["risk_high"] == 70
    assert cfg.scoring["recent_years"] == [2025, 2026]
```

- [ ] **Step 2: Run test, expect ImportError**

Run: `pytest tests/test_config_loader.py -v`
Expected: FAIL với `ModuleNotFoundError`.

- [ ] **Step 3: Implement `src/config_loader.py`**

```python
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
    "risk_high": 70,
    "risk_mid": 40,
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
```

- [ ] **Step 4: Run test, expect PASS**

Run: `pytest tests/test_config_loader.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add brand-guard-fb/src/config_loader.py brand-guard-fb/tests/test_config_loader.py
git commit -m "feat(brand-guard-fb): config loader with validation + default scoring merge"
```

---

## Task 4: Search engine dorks + URL filter (`src/search.py`)

**Files:**
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/src/search.py`
- Test: `/Users/bobo/ZCodeProject/brand-guard-fb/tests/test_search.py`

- [ ] **Step 1: Viết failing test**

`tests/test_search.py`:
```python
from src.models import Brand, Trademark
from src.search import (
    build_dorks,
    extract_fb_page_urls,
    filter_eligible_urls,
)


def _brand():
    return Brand(
        id="fpt",
        display_name="FPT Shop",
        aliases=["FPT Shop", "FPTShop"],
        official_username="fptshop",
        official_page_url="https://www.facebook.com/fptshop",
        avatar_path="./a.png",
        cover_path="./c.png",
    )


def test_build_dorks_includes_display_name_and_alias():
    dorks = build_dorks(_brand())
    assert any("FPT Shop" in d for d in dorks)
    assert any("FPTShop" in d for d in dorks)
    assert any("-site:facebook.com/fptshop" in d for d in dorks)
    assert len(dorks) >= 5


def test_extract_fb_page_urls_from_html():
    html = """
    <a href="https://www.facebook.com/fpt.shop.official">x</a>
    <a href="https://www.facebook.com/fptshop2026/">y</a>
    <a href="https://www.facebook.com/profile.php?id=123">z</a>
    <a href="https://www.facebook.com/groups/fans">w</a>
    <a href="https://www.facebook.com/fptshop/posts/abc">deep</a>
    <a href="https://example.com/other">other</a>
    """
    urls = extract_fb_page_urls(html)
    assert "https://www.facebook.com/fpt.shop.official" in urls
    assert "https://www.facebook.com/fptshop2026" in urls
    assert all("profile.php" not in u for u in urls)
    assert all("/groups/" not in u for u in urls)
    assert all("/posts/" not in u for u in urls)


def test_filter_excludes_official():
    brand = _brand()
    urls = [
        "https://www.facebook.com/fptshop",
        "https://www.facebook.com/fpt.shop.official",
        "https://www.facebook.com/fptshop.official",
        "https://www.facebook.com/another",
    ]
    eligible = filter_eligible_urls(urls, brand)
    assert "https://www.facebook.com/fptshop" not in eligible
    assert "https://www.facebook.com/fpt.shop.official" in eligible
    # 'fptshop.official' contains 'official' keyword — usually a fake pattern, KEEP it
    assert "https://www.facebook.com/fptshop.official" in eligible
    assert "https://www.facebook.com/another" in eligible
```

- [ ] **Step 2: Run test, expect ImportError**

Run: `pytest tests/test_search.py -v`
Expected: FAIL với `ModuleNotFoundError`.

- [ ] **Step 3: Implement `src/search.py`**

```python
from __future__ import annotations

import re
import time
import random
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from src.models import Brand


# Regex: chỉ giữ URL page, loại profile/groups/posts/photos/videos/reel
_PAGE_URL_RE = re.compile(
    r"^https?://(?:www\.|m\.|web\.)?facebook\.com/"
    r"(?!profile\.php|groups/|people/|pages/|watch/|share/|sharer|sharer\.php|permalink\.php)"
    r"([\w.\-]+)"
    r"(?:/?(?:posts|photos|videos|reel|reels|events|shop|live)?/?.*)$",
    re.IGNORECASE,
)

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]


def build_dorks(brand: Brand) -> list[str]:
    """Sinh 5-10 dork queries từ brand info."""
    name = brand.display_name
    primary_alias = brand.aliases[0] if brand.aliases else name
    exclude_official = f"-site:facebook.com/{brand.official_username}"
    dorks = [
        f'site:facebook.com "{name}" {exclude_official}',
        f'"{name}" site:facebook.com inurl:"{brand.official_username}"',
        f'"{primary_alias}" site:facebook.com "liên hệ" OR "hotline"',
        f'"{name}" site:facebook.com "2025" OR "2026"',
        f'"{name}" site:facebook.com "chính sách" OR "khuyến mãi"',
        f'site:facebook.com "{name}" -"{brand.official_username}"',
    ]
    # Thêm dork cho mỗi alias phụ
    for alias in brand.aliases[1:3]:
        dorks.append(f'"{alias}" site:facebook.com {exclude_official}')
    # Dedup giữ thứ tự
    seen = set()
    out = []
    for d in dorks:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out[:10]


def extract_fb_page_urls(html: str) -> list[str]:
    """Parse HTML search results, trả về list URL Facebook page (đã normalize)."""
    soup = BeautifulSoup(html, "html.parser")
    raw_urls: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # DDG wrap URL trong /l/?uddg=
        if "uddg=" in href:
            from urllib.parse import parse_qs, unquote
            qs = parse_qs(urlparse(href).query)
            if "uddg" in qs:
                href = unquote(qs["uddg"][0])
        raw_urls.append(href)
    eligible: list[str] = []
    seen_slugs: set[str] = set()
    for url in raw_urls:
        m = _PAGE_URL_RE.match(url)
        if not m:
            continue
        slug = m.group(1)
        if slug.lower() in seen_slugs:
            continue
        seen_slugs.add(slug.lower())
        # Normalize URL (bỏ fragment, bỏ trailing slash)
        normalized = f"https://www.facebook.com/{slug}"
        eligible.append(normalized)
    return eligible


def filter_eligible_urls(urls: list[str], brand: Brand) -> list[str]:
    """Loại URL chính chủ, dedup."""
    official_urls = {
        brand.official_page_url.rstrip("/").lower(),
        f"https://www.facebook.com/{brand.official_username}".lower(),
    }
    out = []
    seen = set()
    for url in urls:
        u = url.rstrip("/").lower()
        if u in official_urls:
            continue
        if u in seen:
            continue
        seen.add(u)
        out.append(url.rstrip("/"))
    return out


def _query_ddg(query: str, timeout: int = 15) -> str:
    """Query DuckDuckGo HTML endpoint."""
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
    }
    resp = requests.post(url, data={"q": query}, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def _query_bing(query: str, timeout: int = 15) -> str:
    """Fallback Bing HTML."""
    url = f"https://www.bing.com/search?q={requests.utils.quote(query)}"
    headers = {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def search_pages(brand: Brand, max_queries: int = 10, sleep_range=(2, 5)) -> list[str]:
    """Query search engines, trả về list URL page nghi ngờ."""
    dorks = build_dorks(brand)[:max_queries]
    all_urls: list[str] = []
    for i, dork in enumerate(dorks):
        try:
            html = _query_ddg(dork)
        except requests.RequestException:
            try:
                time.sleep(random.uniform(*sleep_range))
                html = _query_bing(dork)
            except requests.RequestException:
                continue
        all_urls.extend(extract_fb_page_urls(html))
        if i < len(dorks) - 1:
            time.sleep(random.uniform(*sleep_range))
    return filter_eligible_urls(all_urls, brand)
```

- [ ] **Step 4: Run test, expect PASS**

Run: `pytest tests/test_search.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add brand-guard-fb/src/search.py brand-guard-fb/tests/test_search.py
git commit -m "feat(brand-guard-fb): dork generation + URL filter + DDG/Bing search"
```

---

## Task 5: Page metadata fetcher (`src/page_meta.py`)

**Files:**
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/src/page_meta.py`
- Test: `/Users/bobo/ZCodeProject/brand-guard-fb/tests/test_page_meta.py`
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/tests/fixtures/fake_page.html`

- [ ] **Step 1: Tạo fixture HTML**

`tests/fixtures/fake_page.html`:
```html
<!DOCTYPE html>
<html>
<head>
  <meta property="og:title" content="FPT Shop Official">
  <meta property="og:image" content="https://scontent.fsgn5-2.fna.fbcdn.net/v/avatar.png">
  <meta property="og:description" content="Cửa hàng điện máy chính hãng">
  <meta name="description" content="Cửa hàng điện máy chính hãng">
</head>
<body>
  <div aria-label="Verified">
    <span>Verified Page</span>
  </div>
  <div>Page created · 1 January 2026</div>
</body>
</html>
```

- [ ] **Step 2: Viết failing test**

`tests/test_page_meta.py`:
```python
from pathlib import Path

from src.page_meta import parse_page_meta


FIXTURE = Path(__file__).parent / "fixtures" / "fake_page.html"


def test_parse_og_title_and_image():
    html = FIXTURE.read_text(encoding="utf-8")
    meta = parse_page_meta("https://www.facebook.com/fakepage", html)
    assert meta.title == "FPT Shop Official"
    assert meta.avatar_url.endswith("avatar.png")
    assert meta.description == "Cửa hàng điện máy chính hãng"


def test_parse_verified_badge():
    html = FIXTURE.read_text(encoding="utf-8")
    meta = parse_page_meta("https://www.facebook.com/fakepage", html)
    assert meta.is_verified is True


def test_parse_created_year_2026():
    html = FIXTURE.read_text(encoding="utf-8")
    meta = parse_page_meta("https://www.facebook.com/fakepage", html)
    assert meta.created_year == 2026


def test_parse_no_meta_tags_returns_empty():
    meta = parse_page_meta("https://www.facebook.com/foo", "<html><body>nothing</body></html>")
    assert meta.title == ""
    assert meta.is_verified is False
    assert meta.created_year is None
```

- [ ] **Step 3: Run test, expect ImportError**

Run: `pytest tests/test_page_meta.py -v`
Expected: FAIL với `ModuleNotFoundError`.

- [ ] **Step 4: Implement `src/page_meta.py`**

```python
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


_YEAR_RE = re.compile(r"(?:Page created|Created on|Tham gia|Thành lập)[^0-9]*(20\d{2})", re.IGNORECASE)
_RECENT_POST_RE = re.compile(r"data-utime=\"(\d{10,})\"")
_CACHE_DIR = Path(".cache/page_meta")
_CACHE_TTL_SECONDS = 24 * 3600
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
}


def _cache_key(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


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
    return _meta_from_dict(url, data)


def _write_cache(url: str, meta: PageMeta) -> None:
    p = _cache_path(url)
    payload = {
        "title": meta.title,
        "description": meta.description,
        "avatar_url": meta.avatar_url,
        "cover_url": meta.cover_url,
        "is_verified": meta.is_verified,
        "created_year": meta.created_year,
        "recent_post_count_30d": meta.recent_post_count_30d,
        "fetched_at": meta.fetched_at,
        "fetched_ts": time.time(),
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


def fetch_page_meta(url: str, timeout: int = 15) -> PageMeta:
    """Fetch HTML page (có cache), trả về PageMeta."""
    cached = _read_cache(url)
    if cached is not None:
        return cached
    resp = requests.get(url, headers=_HEADERS, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()
    meta = parse_page_meta(url, resp.text)
    _write_cache(url, meta)
    return meta
```

- [ ] **Step 5: Run test, expect PASS**

Run: `pytest tests/test_page_meta.py -v`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add brand-guard-fb/src/page_meta.py brand-guard-fb/tests/test_page_meta.py brand-guard-fb/tests/fixtures/fake_page.html
git commit -m "feat(brand-guard-fb): page metadata fetcher with OG parser + 24h cache"
```

---

## Task 6: Scoring engine (`src/scoring.py`)

**Files:**
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/src/scoring.py`
- Test: `/Users/bobo/ZCodeProject/brand-guard-fb/tests/test_scoring.py`

- [ ] **Step 1: Viết failing test**

`tests/test_scoring.py`:
```python
from src.models import Brand, PageMeta, Trademark
from src.scoring import score_page, _score_name, _score_avatar, _score_recency, _score_url


def _brand():
    return Brand(
        id="fpt",
        display_name="FPT Shop",
        aliases=["FPT Shop", "FPTShop"],
        official_username="fptshop",
        official_page_url="https://www.facebook.com/fptshop",
        avatar_path="./tests/fixtures/fake_avatar.png",
        cover_path="./tests/fixtures/fake_cover.png",
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
        "risk_high": 70,
        "risk_mid": 40,
    }
    base.update(overrides)
    return base


def test_score_name_exact_match():
    page = PageMeta(url="https://www.facebook.com/fake", title="FPT Shop")
    assert _score_name(page, _brand(), _scoring_cfg()) == 35


def test_score_name_no_match():
    page = PageMeta(url="https://www.facebook.com/fake", title="Electronics Store")
    assert _score_name(page, _brand(), _scoring_cfg()) == 0


def test_score_url_exact_official_returns_zero():
    page = PageMeta(url="https://www.facebook.com/fptshop", title="FPT Shop")
    s = score_page(page, _brand(), _scoring_cfg())
    assert s.total == 0


def test_score_url_high_similarity():
    page = PageMeta(url="https://www.facebook.com/fptshop2026", title="FPT Shop")
    s = score_page(page, _brand(), _scoring_cfg())
    # name=35, url≥5, các khoản khác = 0 (no avatar file) → ≥ 40
    assert s.name == 35
    assert s.url >= 5


def test_score_recency_high_for_2026():
    page = PageMeta(url="x", title="x", created_year=2026)
    assert _score_recency(page, _scoring_cfg()) == 12


def test_score_recency_zero_for_old():
    page = PageMeta(url="x", title="x", created_year=2018)
    assert _score_recency(page, _scoring_cfg()) == 0


def test_score_recency_override_when_verified():
    page = PageMeta(url="x", title="x", created_year=2026, is_verified=True)
    assert _score_recency(page, _scoring_cfg()) == 0


def test_total_clamped_at_zero():
    page = PageMeta(
        url="https://www.facebook.com/fptshop",
        title="FPT Shop",
        is_verified=True,
    )
    s = score_page(page, _brand(), _scoring_cfg())
    assert s.total == 0


def test_avatar_perfect_match(monkeypatch, tmp_path):
    # Tạo 2 file ảnh giống hệt nhau
    from PIL import Image
    img = Image.new("RGB", (8, 8), color=(123, 45, 67))
    avatar = tmp_path / "avatar.png"
    img.save(avatar)
    page_avatar_url = tmp_path / "page.png"
    img.save(page_avatar_url)

    brand = Brand(
        id="x",
        display_name="X",
        aliases=["X"],
        official_username="x",
        official_page_url="https://www.facebook.com/x",
        avatar_path=str(avatar),
        cover_path=str(avatar),
    )

    page = PageMeta(url="https://www.facebook.com/y", title="X", avatar_url=str(page_avatar_url))

    # Mock download: dùng local path luôn
    import src.scoring as sc
    monkeypatch.setattr(sc, "_download_to_temp", lambda url: str(page_avatar_url))

    s = score_page(page, brand, _scoring_cfg())
    assert s.avatar == 25
```

- [ ] **Step 2: Run test, expect ImportError**

Run: `pytest tests/test_scoring.py -v`
Expected: FAIL với `ModuleNotFoundError`.

- [ ] **Step 3: Implement `src/scoring.py`**

```python
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
        return 35
    if best >= cfg["name_threshold_mid"]:
        return 22
    return 0


def _score_url(page: PageMeta, brand: Brand) -> int:
    slug = _slug(page.url).lower()
    official = brand.official_username.lower()
    if not slug or not official:
        return 0
    r = fuzz.token_set_ratio(slug, official)
    if r >= 85:
        return 8
    if r >= 70:
        return 5
    return 0


def _phash_distance(image_path_or_url: str) -> imagehash.ImageHash | None:
    """Compute pHash từ path hoặc URL. Trả về None nếu fail."""
    if not image_path_or_url:
        return None
    try:
        if image_path_or_url.startswith(("http://", "https://")):
            local = _download_to_temp(image_path_or_url)
            if not local:
                return None
            img = Image.open(local)
        else:
            p = Path(image_path_or_url)
            if not p.exists():
                return None
            img = Image.open(p)
        return imagehash.phash(img)
    except Exception:
        return None


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
    if distance <= cfg[f"{prefix}_distance_strong"]:
        return 25 if prefix == "avatar" else 20
    if distance <= cfg[f"{prefix}_distance_moderate"]:
        return 17 if prefix == "avatar" else 12
    if distance <= cfg[f"{prefix}_distance_weak"]:
        return 4 if prefix == "avatar" else 4
    return 0


def _score_avatar(page: PageMeta, brand: Brand, cfg: dict[str, Any]) -> int:
    if not page.avatar_url or not brand.avatar_path:
        return 0
    h1 = _phash_distance(page.avatar_url)
    h2 = _phash_distance(brand.avatar_path)
    if h1 is None or h2 is None:
        return 0
    return _bucket_score(h1 - h2, cfg, "avatar")


def _score_cover(page: PageMeta, brand: Brand, cfg: dict[str, Any]) -> int:
    if not page.cover_url or not brand.cover_path:
        return 0
    h1 = _phash_distance(page.cover_url)
    h2 = _phash_distance(brand.cover_path)
    if h1 is None or h2 is None:
        return 0
    return _bucket_score(h1 - h2, cfg, "cover")


def _score_recency(page: PageMeta, cfg: dict[str, Any]) -> int:
    # Verified override về 0
    if page.is_verified:
        return 0
    score = 0
    if page.created_year and page.created_year in cfg["recent_years"]:
        score += 12
    if page.recent_post_count_30d >= 3:
        score += 3
    return score


def score_page(page: PageMeta, brand: Brand, cfg: dict[str, Any]) -> ScoreResult:
    """Chấm điểm 1 page. Trả về 0 nếu là chính chủ."""
    # Whitelist chính chủ
    page_url_norm = page.url.rstrip("/").lower()
    official_urls = {
        brand.official_page_url.rstrip("/").lower(),
        f"https://www.facebook.com/{brand.official_username}".lower(),
    }
    if page_url_norm in official_urls:
        return ScoreResult(total=0, name=0, avatar=0, cover=0, recency=0, url=0)

    name = _score_name(page, brand, cfg)
    avatar = _score_avatar(page, brand, cfg)
    cover = _score_cover(page, brand, cfg)
    recency = _score_recency(page, cfg)
    url = _score_url(page, brand)

    # Nếu verified → tổng = 0 (chính chủ)
    if page.is_verified:
        return ScoreResult(total=0, name=name, avatar=avatar, cover=cover, recency=0, url=url)

    total = max(0, name + avatar + cover + recency + url)
    return ScoreResult(total=total, name=name, avatar=avatar, cover=cover, recency=recency, url=url)
```

- [ ] **Step 4: Run test, expect PASS**

Run: `pytest tests/test_scoring.py -v`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add brand-guard-fb/src/scoring.py brand-guard-fb/tests/test_scoring.py
git commit -m "feat(brand-guard-fb): scoring engine — name/avatar/cover/recency/url signals"
```

---

## Task 7: Report renderer (`src/report.py`)

**Files:**
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/src/report.py`
- Test: `/Users/bobo/ZCodeProject/brand-guard-fb/tests/test_report.py`

- [ ] **Step 1: Viết failing test**

`tests/test_report.py`:
```python
from src.models import Brand, PageMeta, ScoreResult, ScoredPage, ScanReport
from src.report import render_markdown


def _brand():
    return Brand(
        id="fpt",
        display_name="FPT Shop",
        aliases=["FPT Shop"],
        official_username="fptshop",
        official_page_url="https://www.facebook.com/fptshop",
        avatar_path="./a.png",
        cover_path="./c.png",
    )


def test_render_includes_brand_name_and_run_at():
    report = ScanReport(brand_id="fpt", run_at="2026-07-05T14:30+07:00")
    md = render_markdown(report, _brand())
    assert "FPT Shop" in md
    assert "2026-07-05T14:30+07:00" in md


def test_render_groups_by_band():
    pages = [
        ScoredPage(
            page=PageMeta(url="https://www.facebook.com/a", title="FPT Shop"),
            score=ScoreResult(total=92, name=35, avatar=25, cover=20, recency=12, url=0),
        ),
        ScoredPage(
            page=PageMeta(url="https://www.facebook.com/b", title="FPT"),
            score=ScoreResult(total=58, name=22, avatar=0, cover=0, recency=0, url=8),
        ),
        ScoredPage(
            page=PageMeta(url="https://www.facebook.com/c", title="Other"),
            score=ScoreResult(total=22, name=22, avatar=0, cover=0, recency=0, url=0),
        ),
    ]
    report = ScanReport(brand_id="fpt", run_at="2026-07-05T14:30+07:00", pages=pages)
    md = render_markdown(report, _brand())
    assert "Cao rủi ro" in md
    assert "Trung" in md
    assert "Thấp" in md
    assert "fpt-shop-a" not in md  # bảng không slugify
    assert "https://www.facebook.com/a" in md


def test_render_empty_pages():
    report = ScanReport(brand_id="fpt", run_at="2026-07-05T14:30+07:00", pages=[])
    md = render_markdown(report, _brand())
    assert "Không tìm thấy" in md or "0 trang" in md or "không có" in md.lower()
```

- [ ] **Step 2: Run test, expect ImportError**

Run: `pytest tests/test_report.py -v`
Expected: FAIL với `ModuleNotFoundError`.

- [ ] **Step 3: Implement `src/report.py`**

```python
from __future__ import annotations

from src.models import Brand, RiskBand, ScanReport

_BAND_VI = {RiskBand.HIGH: "🔴 Cao rủi ro", RiskBand.MID: "🟡 Trung", RiskBand.LOW: "🟢 Thấp"}


def _table_header() -> str:
    return (
        "| # | Page | Tên hiển thị | Score | Tên (35) | Avatar (25) | "
        "Cover (20) | Mới (12) | URL (8) |\n"
        "|---|------|--------------|-------|----------|-------------|"
        "------------|----------|---------|"
    )


def _row(idx: int, page_url: str, title: str, s) -> str:
    short_slug = page_url.replace("https://www.facebook.com/", "")
    return (
        f"| {idx} | [{short_slug}]({page_url}) | {title or '—'} | "
        f"**{s.total}** | {s.name} | {s.avatar} | {s.cover} | {s.recency} | {s.url} |"
    )


def render_markdown(report: ScanReport, brand: Brand) -> str:
    lines: list[str] = []
    lines.append("# 🔍 Brand Guard — Facebook Fake Page Scan")
    lines.append("")
    lines.append(f"**Run at:** {report.run_at}  **Brand:** {brand.display_name}  "
                 f"**Pages scanned:** {len(report.pages)}")
    lines.append("")

    if not report.pages:
        lines.append("✅ Không tìm thấy trang nghi vấn cho thương hiệu này.")
        return "\n".join(lines)

    for band in (RiskBand.HIGH, RiskBand.MID, RiskBand.LOW):
        items = report.iter_by_band(band=band)
        if not items:
            continue
        label = _BAND_VI[band]
        lines.append(f"## {label} ({len(items)})")
        lines.append("")
        lines.append(_table_header())
        for i, sp in enumerate(items, 1):
            lines.append(_row(i, sp.page.url, sp.page.title, sp.score))
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "**Lưu ý pháp lý:** Kết quả chỉ là gợi ý dựa trên heuristic. "
        "Trước khi gửi khiếu nại, hãy review lại bằng chứng và xác nhận với pháp chế. "
        "Không tự liên hệ/xâm phạm trang nghi vấn."
    )
    return "\n".join(lines)
```

- [ ] **Step 4: Run test, expect PASS**

Run: `pytest tests/test_report.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add brand-guard-fb/src/report.py brand-guard-fb/tests/test_report.py
git commit -m "feat(brand-guard-fb): markdown report renderer with risk band grouping"
```

---

## Task 8: Takedown templates

**Files:**
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/templates/meta_ip_report.md`
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/templates/shtt_complaint_vi.md`
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/src/takedown_template.py`
- Test: `/Users/bobo/ZCodeProject/brand-guard-fb/tests/test_takedown_template.py`

- [ ] **Step 1: Viết template Meta IP (EN)**

`templates/meta_ip_report.md`:
```markdown
# Meta IP Infringement Report

**Submit at:** https://www.facebook.com/help/contact/638124867914415

## Trademark Owner

- **Brand:** {brand.display_name}
- **Vietnam Trademark Reg. No.:** {brand.trademark.vn_number}
- **Nice Class:** {brand.trademark.vn_class}
- **Meta IP Rights ID:** {brand.trademark.meta_ip_rights_id}
- **Official Page:** {brand.official_page_url}

## Identified Infringing Pages

{infringing_pages_list}

## Statement of Good Faith Belief

I have a good faith belief that use of the trademarks described above in the
infringing materials is not authorized by the trademark owner, its agent, or
the law.

## Statement of Accuracy

I swear, under penalty of perjury, that the information in the notification
is accurate and that I am the trademark owner or am authorized to act on
behalf of the owner of an exclusive right that is allegedly infringed.

## Electronic Signature

**Name:** {signatory_name}
**Title:** {signatory_title}
**Date:** {today_date}
**Email:** {signatory_email}
```

- [ ] **Step 2: Viết template SHTT VN**

`templates/shtt_complaint_vi.md`:
```markdown
# ĐƠN YÊU CẦU XỬ LÝ VI PHẠM NHÃN HIỆU
*(Theo mẫu số 03 Nghị định 65/2023/NĐ-CP)*

Nộp trực tuyến tại: https://dms.noip.gov.vn

## 1. Thông tin tổ chức/cá nhân bị xâm phạm

- **Tên:** {brand.display_name}
- **Số đăng ký nhãn hiệu:** {brand.trademark.vn_number}
- **Lớp Nice:** {brand.trademark.vn_class}
- **Page chính chủ:** {brand.official_page_url}

## 2. Mô tả nhãn hiệu bị xâm phạm

Nhãn hiệu "{brand.display_name}" đã được cấp Giấy chứng nhận đăng ký nhãn hiệu
số {brand.trademark.vn_number} tại Cục Sở hữu trí tuệ Việt Nam, dùng cho hàng
hoá/dịch vụ thuộc lớp {brand.trademark.vn_class}.

## 3. Hành vi xâm phạm

Các cá nhân/tổ chức không được phép đã lập fanpage Facebook sử dụng nhãn hiệu
"{brand.display_name}" và hình ảnh trùng/tương tự với thương hiệu chính chủ
nhằm gây nhầm lẫn cho người tiêu dùng, vi phạm quyền sở hữu trí tuệ theo
Điều 4 Nghị định 65/2023/NĐ-CP.

## 4. Bằng chứng vi phạm

{infringing_pages_list_with_evidence}

## 5. Chứng từ quyền sở hữu

- Giấy chứng nhận đăng ký nhãn hiệu số {brand.trademark.vn_number}
- Ảnh chụp fanpage chính chủ: {brand.official_page_url}

## 6. Yêu cầu xử lý

Đề nghị Cục Sở hữu trí tuệ xem xét, xử lý theo quy định tại Nghị định
65/2023/NĐ-CP và thông tin cho cơ quan quản lý nền tảng Meta để gỡ bỏ
fanpage vi phạm.

## 7. Cam kết & Ký tên

Tôi cam kết những thông tin trên là đúng sự thật và hoàn toàn chịu trách
nội dung pháp lý về các thông tin đã khai.

**Đại diện:** {signatory_name}
**Chức danh:** {signatory_title}
**Ngày:** {today_date}
**Email liên hệ:** {signatory_email}
```

- [ ] **Step 3: Viết failing test**

`tests/test_takedown_template.py`:
```python
from pathlib import Path

from src.models import Brand, PageMeta, ScoreResult, ScoredPage
from src.takedown_template import render_meta_ip, render_shtt


def _brand():
    b = Brand(
        id="fpt",
        display_name="FPT Shop",
        aliases=["FPT Shop"],
        official_username="fptshop",
        official_page_url="https://www.facebook.com/fptshop",
        avatar_path="./a.png",
        cover_path="./c.png",
    )
    b.trademark.vn_number = "12345-2020"
    b.trademark.vn_class = "9"
    return b


def _pages():
    return [
        ScoredPage(
            page=PageMeta(url="https://www.facebook.com/fake1", title="FPT Shop"),
            score=ScoreResult(total=92, name=35, avatar=25, cover=20, recency=12, url=0),
        )
    ]


def test_render_meta_ip_fills_brand_and_pages():
    md = render_meta_ip(
        brand=_brand(),
        pages=_pages(),
        signatory_name="Nguyen A",
        signatory_title="Legal",
        signatory_email="legal@fpt.com",
        today_date="2026-07-05",
    )
    assert "FPT Shop" in md
    assert "12345-2020" in md
    assert "fake1" in md
    assert "Nguyen A" in md
    assert "legal@fpt.com" in md
    assert "good faith belief" in md.lower()


def test_render_shtt_fills_brand_and_pages():
    md = render_shtt(
        brand=_brand(),
        pages=_pages(),
        signatory_name="Nguyen A",
        signatory_title="Giám đốc",
        signatory_email="legal@fpt.com",
        today_date="2026-07-05",
    )
    assert "FPT Shop" in md
    assert "12345-2020" in md
    assert "fake1" in md
    assert "Nguyen A" in md
    assert "Nghị định 65/2023" in md
```

- [ ] **Step 4: Run test, expect ImportError**

Run: `pytest tests/test_takedown_template.py -v`
Expected: FAIL với `ModuleNotFoundError`.

- [ ] **Step 5: Implement `src/takedown_template.py`**

```python
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.models import Brand, ScoredPage


_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def _format_pages_list(pages: list[ScoredPage], with_evidence: bool = False) -> str:
    lines: list[str] = []
    for i, sp in enumerate(pages, 1):
        url = sp.page.url
        title = sp.page.title or "—"
        score = sp.score.total
        if with_evidence:
            lines.append(
                f"{i}. **URL:** {url}\n"
                f"   - Tên hiển thị: {title}\n"
                f"   - Điểm rủi ro: {score}/100\n"
                f"   -Screenshot: cần chụp thủ công vào lúc truy cập"
            )
        else:
            lines.append(f"{i}. {url} — {title} (score: {score})")
    return "\n".join(lines) if lines else "(không có)"


def render_meta_ip(
    brand: Brand,
    pages: list[ScoredPage],
    signatory_name: str,
    signatory_title: str,
    signatory_email: str,
    today_date: str | None = None,
) -> str:
    today_date = today_date or datetime.now().strftime("%Y-%m-%d")
    template = (_TEMPLATE_DIR / "meta_ip_report.md").read_text(encoding="utf-8")
    return template.format(
        brand=brand,
        infringing_pages_list=_format_pages_list(pages, with_evidence=False),
        signatory_name=signatory_name,
        signatory_title=signatory_title,
        signatory_email=signatory_email,
        today_date=today_date,
    )


def render_shtt(
    brand: Brand,
    pages: list[ScoredPage],
    signatory_name: str,
    signatory_title: str,
    signatory_email: str,
    today_date: str | None = None,
) -> str:
    today_date = today_date or datetime.now().strftime("%Y-%m-%d")
    template = (_TEMPLATE_DIR / "shtt_complaint_vi.md").read_text(encoding="utf-8")
    return template.format(
        brand=brand,
        infringing_pages_list_with_evidence=_format_pages_list(pages, with_evidence=True),
        signatory_name=signatory_name,
        signatory_title=signatory_title,
        signatory_email=signatory_email,
        today_date=today_date,
    )
```

- [ ] **Step 6: Run test, expect PASS**

Run: `pytest tests/test_takedown_template.py -v`
Expected: 2 passed.

- [ ] **Step 7: Commit**

```bash
git add brand-guard-fb/templates/ brand-guard-fb/src/takedown_template.py brand-guard-fb/tests/test_takedown_template.py
git commit -m "feat(brand-guard-fb): Meta IP + SHTT takedown templates with renderer"
```

---

## Task 9: CLI orchestration (`src/cli.py`)

**Files:**
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/src/cli.py`

- [ ] **Step 1: Implement `src/cli.py`** (no unit test — integration glue)

```python
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.config_loader import AppConfig, load_config
from src.models import RiskBand, ScoredPage, ScanReport
from src.page_meta import fetch_page_meta
from src.report import render_markdown
from src.scoring import score_page
from src.search import search_pages
from src.takedown_template import render_meta_ip, render_shtt


_IST = timezone(timedelta(hours=7))


def _scan_brand(brand, cfg: dict) -> ScanReport:
    run_at = datetime.now(_IST).strftime("%Y-%m-%dT%H:%M%z")
    report = ScanReport(brand_id=brand.id, run_at=run_at, pages=[])

    print(f"[*] Searching pages for brand: {brand.display_name}", file=sys.stderr)
    urls = search_pages(brand)
    print(f"[*] Found {len(urls)} candidate URLs", file=sys.stderr)

    scoring_cfg = {**cfg, **brand.scoring_overrides}

    for i, url in enumerate(urls, 1):
        print(f"[*] ({i}/{len(urls)}) Fetching {url}", file=sys.stderr)
        try:
            meta = fetch_page_meta(url)
        except Exception as e:
            print(f"[!] Failed to fetch {url}: {e}", file=sys.stderr)
            continue
        score = score_page(meta, brand, scoring_cfg)
        report.pages.append(ScoredPage(page=meta, score=score))

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="brand-guard-fb")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).parent.parent / "config" / "brands.yaml"),
        help="Path to brands.yaml",
    )
    parser.add_argument(
        "--brand",
        help="Brand ID to scan (default: scan all brands in config)",
    )
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="Skip network calls, only use cached page metadata",
    )
    parser.add_argument(
        "--generate-complaints",
        action="store_true",
        help="Generate takedown complaint templates for high-risk pages",
    )
    parser.add_argument(
        "--signatory-name", default="[YOUR NAME]",
    )
    parser.add_argument(
        "--signatory-title", default="[YOUR TITLE]",
    )
    parser.add_argument(
        "--signatory-email", default="[YOUR EMAIL]",
    )
    args = parser.parse_args(argv)

    config: AppConfig = load_config(Path(args.config))
    brands = [b for b in config.brands if not args.brand or b.id == args.brand]
    if not brands:
        print(f"[!] No brand matching '{args.brand}'", file=sys.stderr)
        return 2

    outputs: list[str] = []
    for brand in brands:
        report = _scan_brand(brand, config.scoring)
        outputs.append(render_markdown(report, brand))

        if args.generate_complaints:
            high_pages = report.iter_by_band(band=RiskBand.HIGH)
            if high_pages:
                out_dir = Path(".cache/complaints")
                out_dir.mkdir(parents=True, exist_ok=True)
                today = datetime.now(_IST).strftime("%Y-%m-%d")
                meta_md = render_meta_ip(
                    brand=brand,
                    pages=high_pages,
                    signatory_name=args.signatory_name,
                    signatory_title=args.signatory_title,
                    signatory_email=args.signatory_email,
                    today_date=today,
                )
                shtt_md = render_shtt(
                    brand=brand,
                    pages=high_pages,
                    signatory_name=args.signatory_name,
                    signatory_title=args.signatory_title,
                    signatory_email=args.signatory_email,
                    today_date=today,
                )
                meta_path = out_dir / f"{today}-{brand.id}-meta.md"
                shtt_path = out_dir / f"{today}-{brand.id}-shtt.md"
                meta_path.write_text(meta_md, encoding="utf-8")
                shtt_path.write_text(shtt_md, encoding="utf-8")
                outputs.append(
                    f"\n👉 Mẫu đơn khiếu nại: `{meta_path}` và `{shtt_path}`"
                )

    print("\n\n".join(outputs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Smoke test offline (no network)**

Tạo file `config/brands.yaml` mẫu dùng brand_example, chạy:
```bash
cd /Users/bobo/ZCodeProject/brand-guard-fb
source .venv/bin/activate
python -m src.cli --no-network
```
Expected: chạy không lỗi, output markdown (có thể rỗng vì cache trống).

- [ ] **Step 3: Commit**

```bash
git add brand-guard-fb/src/cli.py
git commit -m "feat(brand-guard-fb): CLI orchestration — pipeline search→fetch→score→render"
```

---

## Task 10: SKILL.md manifest + install symlink

**Files:**
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/SKILL.md`
- Create: `/Users/bobo/.zcode/skills/brand-guard-fb` (symlink → workspace)

- [ ] **Step 1: Viết `SKILL.md`**

`/Users/bobo/ZCodeProject/brand-guard-fb/SKILL.md`:
```markdown
---
name: brand-guard-fb
description: Detect fake Facebook fanpages impersonating user's brand by name + avatar + cover photo + recency heuristics. Outputs a markdown report with risk scores and generates Meta IP / SHTT Vietnam takedown complaint templates. Use when user reports brand impersonation on Facebook, wants proactive brand protection monitoring, says "fanpage bị giả mạo", "trang Facebook giả", or needs takedown templates for IP infringement.
---

# Brand Guard FB

Tự dò fanpage Facebook giả mạo thương hiệu, chấm điểm rủi ro, và sinh mẫu đơn khiếu nại Meta IP + SHTT Việt Nam.

## Khi nào dùng

- Bị lập fanpage giả mạo thương hiệu trên Facebook.
- Muốn giám sát theo yêu cầu (không chạy định kỳ).
- Cần bằng chứng + mẫu đơn để gửi Meta Brand Protection hoặc Cục SHTT.

## Cách dùng

### 1. Setup (chỉ 1 lần)

Đảm bảo `config/brands.yaml` đã điền brand info (copy từ `config/brands.example.yaml`). Các trường bắt buộc:
- `display_name`, `aliases[]` — tên chính + biến thể
- `official_username`, `official_page_url` — fanpage chính chủ
- `avatar_path`, `cover_path` — path tới ảnh avatar + cover chính chủ (đặt vào `config/avatars/`)
- `trademark.vn_number` — số đăng ký nhãn hiệu VN (có trong Giấy chứng nhận)

### 2. Chạy

Gọi skill từ ZCode. ZCode sẽ:

```bash
cd /Users/bobo/ZCodeProject/brand-guard-fb
source .venv/bin/activate
python -m src.cli --generate-complaints \
  --signatory-name "Tên bạn" \
  --signatory-title "Chức danh" \
  --signatory-email "email@brand.com"
```

Output: báo cáo markdown trong ZCode, kèm file mẫu đơn tại `.cache/complaints/YYYY-MM-DD-<brand>-meta.md` và `-shtt.md`.

### 3. Review & gửi

- Review báo cáo, đánh dấu trang thật sự giả mạo.
- Mở file mẫu đơn, điền chỗ `[YOUR ...]` còn thiếu, ký tên.
- Nộp:
  - Meta: https://www.facebook.com/help/contact/638124867914415
  - SHTT VN: https://dms.noip.gov.vn

## Lưu ý

- **Không** scraping cần đăng nhập, không vi phạm ToS Facebook rõ ràng.
- Kết quả là **gợi ý heuristic** — review tay trước khi hành động pháp lý.
- pHash chỉ so sánh ảnh chính chủ với ảnh trang nghi vấn; cần download ảnh trang nếu FB không expose og:image (thử lại sau).
- Nếu bị search engine block, thử lại sau vài giờ hoặc giảm số brand/queries.
```

- [ ] **Step 2: Symlink skill vào ZCode skill dir**

```bash
ln -s /Users/bobo/ZCodeProject/brand-guard-fb /Users/bobo/.zcode/skills/brand-guard-fb
ls -la /Users/bobo/.zcode/skills/brand-guard-fb
```
Expected: symlink hiện ra, không lỗi.

- [ ] **Step 3: Commit**

```bash
git add brand-guard-fb/SKILL.md
git commit -m "feat(brand-guard-fb): SKILL.md manifest + install symlink to ZCode skills dir"
```

---

## Task 11: Final integration test + README

**Files:**
- Create: `/Users/bobo/ZCodeProject/brand-guard-fb/README.md`

- [ ] **Step 1: Chạy full test suite**

```bash
cd /Users/bobo/ZCodeProject/brand-guard-fb
source .venv/bin/activate
pytest tests/ -v --tb=short
```
Expected: tất cả test PASS (khoảng 26 test cases).

- [ ] **Step 2: Smoke test với brand demo**

Tạo `config/brands.yaml` với 1 brand (vd "FPT Shop"), chạy thật:
```bash
python -m src.cli --brand fpt --generate-complaints
```
Expected: output markdown có ít nhất 1 trang nghi vấn, file `.cache/complaints/2026-07-05-fpt-*.md` được tạo.

- [ ] **Step 3: Viết `README.md`**

`/Users/bobo/ZCodeProject/brand-guard-fb/README.md`:
```markdown
# Brand Guard FB

ZCode skill — tự dò fanpage Facebook giả mạo, chấm điểm rủi ro, sinh mẫu đơn khiếu nại.

## Cài đặt

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config/brands.example.yaml config/brands.yaml
# Edit brands.yaml + đặt avatar/cover vào config/avatars/
```

## Sử dụng

```bash
python -m src.cli --generate-complaints \
  --signatory-name "Tên" --signatory-title "Chức danh" --signatory-email "email@brand.com"
```

## Test

```bash
pytest tests/ -v
```

## Cấu trúc

- `src/models.py` — dataclass
- `src/config_loader.py` — load brands.yaml
- `src/search.py` — DuckDuckGo/Bing dork search
- `src/page_meta.py` — fetch OG metadata + cache 24h
- `src/scoring.py` — 5 signals scoring (name/avatar/cover/recency/url)
- `src/report.py` — markdown renderer
- `src/takedown_template.py` — Meta IP + SHTT complaint templates
- `src/cli.py` — orchestration entry point

## Spec

See `docs/superpowers/specs/2026-07-05-brand-guard-fb-design.md` ở repo chính.
```

- [ ] **Step 4: Commit**

```bash
git add brand-guard-fb/README.md
git commit -m "docs(brand-guard-fb): README with install/use/test instructions"
```

---

## Self-Review checklist (sau khi code xong)

- [ ] Mọi test pass.
- [ ] `python -m src.cli --help` hoạt động, không lỗi.
- [ ] `config/brands.yaml` rỗng → báo lỗi ConfigError thân thiện.
- [ ] Skill symlink hoạt động (ZCode nhận skill).
- [ ] Smoke test với brand thực tế không crash, output có ý nghĩa.
- [ ] `templates/` render đúng placeholders (không còn `{brand.display_name}` lọt ra).
- [ ] `.cache/` không bị commit (check `git status`).
- [ ] README đề cập đủ: setup, dùng, test, cấu trúc, link spec.
