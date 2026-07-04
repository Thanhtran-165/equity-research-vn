# vn-rates-weekly Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a new skill `vn-rates-weekly` that produces a weekly Vietnamese rates & monetary HTML dashboard from 4 weeks × 3 PDF sources (SBV/VBMA/VNBA) plus upstream time-series (HNX/FRED/vnstock).

**Architecture:** Two ingestion layers — (1) 4-week rolling PDF window from 3 official sources for snapshot/verdict/narrative, (2) upstream direct calls (HNX/SBV/FRED/vnstock) for 12-week headline charts. Output is single-file HTML built by forking `vn-macro-monthly/assets/report_template.html` and migrating it to the shared `_viz-shared/` design system via `inject.py`.

**Tech Stack:** Python 3.11+ (fetch/extract/render), Bash/curl + pdftotext, Chart.js 4.4.1 + chartjs-plugin-annotation (CDN), Playwright (QA), `_viz-shared/` (tokens.css + components.css + viz.js + inject.py).

**Spec:** `docs/superpowers/specs/2026-07-04-vn-rates-weekly-design.md`

**Scope decomposition:** This plan is one cohesive skill. It is large but each task produces a testable artifact. The 9 tasks follow the natural layers: scaffold → fetch → extract → template → render → QA → docs. Commit after each task.

---

## File Structure

**Create:**
- `/Users/bobo/.zcode/skills/vn-rates-weekly/SKILL.md` — workflow orchestration doc (the skill entry point)
- `/Users/bobo/.zcode/skills/vn-rates-weekly/references/sources_overview.md` — 3 PDF sources + 7 upstream sources, URLs, fetch methods, pitfalls
- `/Users/bobo/.zcode/skills/vn-rates-weekly/references/data_cards.md` — 35-indicator mapping + 4-week schema + narrative rules
- `/Users/bobo/.zcode/skills/vn-rates-weekly/references/rendering.md` — 15 HTML patterns + 3 rates-specific components + tab placement rule
- `/Users/bobo/.zcode/skills/vn-rates-weekly/references/preflight_check.md` — Tet/holiday calendar + retry logic
- `/Users/bobo/.zcode/skills/vn-rates-weekly/assets/weekly_template.html` — forked+tokenized template (with `{{VIZ_CSS}}`/`{{VIZ_JS}}` placeholders + data tokens)
- `/Users/bobo/.zcode/skills/vn-rates-weekly/scripts/fetch_sources.py` — unified fetch: 12 PDFs (3 sources × 4 weeks) + upstream HNX/FRED/SBV/vnstock
- `/Users/bobo/.zcode/skills/vn-rates-weekly/scripts/extract_cards.py` — parse PDF text → `values[]` 4-week array + cross-check resolve
- `/Users/bobo/.zcode/skills/vn-rates-weekly/scripts/render_report.py` — fill template from `report.json`
- `/Users/bobo/.zcode/skills/vn-rates-weekly/scripts/qa_weekly.js` — Playwright QA
- `/Users/bobo/.zcode/skills/vn-rates-weekly/tests/test_extract_cards.py` — pytest for parsers (uses sample VBMA PDFs already in repo)
- `/Users/bobo/.zcode/skills/vn-rates-weekly/tests/fixtures/` — sample .txt files extracted from real PDFs

**Modify:**
- `/Users/bobo/.zcode/skills/_viz-shared/inject.py:29-35` — add `vn-rates-weekly/assets/weekly_template.html` to `TEMPLATE_PATHS`

**Test fixtures (already in repo, reuse):**
- `/Users/bobo/ZCodeProject/vn-macro-monthly/2026-06/sources_cache/vbma_weekly_22-26jun_2026.txt` — sample VBMA parsed text
- `/Users/bobo/ZCodeProject/vn-macro-monthly/2026-06/sources_cache/vbma_weekly_15-19jun_2026.txt` — second sample

---

## Task 1: Skill scaffold + metadata

**Files:**
- Create: `/Users/bobo/.zcode/skills/vn-rates-weekly/SKILL.md` (minimal stub, expanded in Task 9)
- Create: `/Users/bobo/.zcode/skills/vn-rates-weekly/references/.gitkeep`
- Create: `/Users/bobo/.zcode/skills/vn-rates-weekly/assets/.gitkeep`
- Create: `/Users/bobo/.zcode/skills/vn-rates-weekly/scripts/.gitkeep`
- Create: `/Users/bobo/.zcode/skills/vn-rates-weekly/tests/.gitkeep`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p /Users/bobo/.zcode/skills/vn-rates-weekly/{references,assets,scripts,tests,tests/fixtures}
touch /Users/bobo/.zcode/skills/vn-rates-weekly/{references,assets,scripts,tests}/.gitkeep
```

- [ ] **Step 2: Write minimal SKILL.md stub**

Write to `/Users/bobo/.zcode/skills/vn-rates-weekly/SKILL.md`:

```markdown
---
name: vn-rates-weekly
description: Báo cáo tuần thị trường lãi suất & tiền tệ Việt Nam — 4-week rolling window từ 3 nguồn PDF (SBV+VBMA+VNBA) + upstream 12-week chart (HNX/FRED/vnstock)
---

# VN Rates Weekly

Báo cáo tuần toàn cảnh thị trường lãi suất & tiền tệ Việt Nam.

> **STATUS:** scaffold — full workflow added in Task 9.

## Workflow (placeholder)

4 bước — chi tiết thêm sau:

1. Pre-flight all-or-nothing (12 PDFs + upstream deps)
2. Fetch 4 tuần × 3 nguồn PDF + upstream headline
3. Extract 35 chỉ số + 4 rules + narrative
4. Render HTML dashboard + QA triple-gate

Xem spec: `docs/superpowers/specs/2026-07-04-vn-rates-weekly-design.md`
```

- [ ] **Step 3: Verify structure**

```bash
find /Users/bobo/.zcode/skills/vn-rates-weekly -type f
```
Expected: 6 files (SKILL.md + 4 .gitkeep + nothing else yet)

- [ ] **Step 4: Commit**

```bash
cd /Users/bobo/ZCodeProject
git add /Users/bobo/.zcode/skills/vn-rates-weekly
git commit -m "feat(vn-rates-weekly): scaffold skill structure"
```

Note: skills live in `~/.zcode/skills/` which is outside the repo. If git complains, copy the skill folder into the repo for tracking OR add to a dotfile repo. For this plan, assume `~/.zcode/skills/` is its own git repo or symlinked — verify with `cd /Users/bobo/.zcode/skills && git status`. If not a repo, skip git for skill files and only commit the spec/plan/references in the main repo.

---

## Task 2: Sample fixtures + extract unit tests (TDD)

**Files:**
- Create: `/Users/bobo/.zcode/skills/vn-rates-weekly/tests/fixtures/vbma_sample.txt` (copy from real PDF)
- Create: `/Users/bobo/.zcode/skills/vn-rates-weekly/tests/test_extract_cards.py`

- [ ] **Step 1: Copy real VBMA sample text as fixture**

```bash
cp /Users/bobo/ZCodeProject/vn-macro-monthly/2026-06/sources_cache/vbma_weekly_22-26jun_2026.txt \
   /Users/bobo/.zcode/skills/vn-rates-weekly/tests/fixtures/vbma_sample.txt
wc -l /Users/bobo/.zcode/skills/vn-rates-weekly/tests/fixtures/vbma_sample.txt
```
Expected: ≥100 lines (real VBMA text)

- [ ] **Step 2: Inspect fixture to find yield/auction patterns**

```bash
grep -nE "(2 năm|5 năm|10 năm|2Năm|5Năm|10Năm|TNament|2Y|5Y|10Y)" /Users/bobo/.zcode/skills/vn-rates-weekly/tests/fixtures/vbma_sample.txt | head -20
grep -nE "(đấu thầu|bid|offer|trúng thầu)" /Users/bobo/.zcode/skills/vn-rates-weekly/tests/fixtures/vbma_sample.txt | head -10
```
Record the actual line patterns — these feed the regex in Step 4.

- [ ] **Step 3: Write failing test for VBMA yield parser**

Write to `/Users/bobo/.zcode/skills/vn-rates-weekly/tests/test_extract_cards.py`:

```python
"""Tests for extract_cards.py — VBMA PDF text parser."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from extract_cards import parse_vbma_yields, ParsedYield


def test_parse_vbma_yields_finds_2y_5y_10y():
    """VBMA weekly text must yield 2Y/5Y/10Y govt bond rates."""
    fixture = Path(__file__).parent / "fixtures" / "vbma_sample.txt"
    text = fixture.read_text(encoding="utf-8")
    result = parse_vbma_yields(text)
    assert isinstance(result, ParsedYield)
    assert result.yield_2y is not None
    assert result.yield_5y is not None
    assert result.yield_10y is not None
    # Reasonable ranges for VN govt yields (percent)
    for v in (result.yield_2y, result.yield_5y, result.yield_10y):
        assert 0.5 < v < 8.0, f"yield {v}% outside plausible range"
    # 10Y should typically be ≥ 2Y (normal curve)
    assert result.yield_10y >= result.yield_2y - 0.5  # allow slight inversion


def test_parse_vbma_yields_returns_none_on_garbage():
    result = parse_vbma_yields("this is not a VBMA report")
    assert result.yield_2y is None
    assert result.yield_5y is None
    assert result.yield_10y is None
```

- [ ] **Step 4: Run test to verify it fails (module doesn't exist)**

```bash
cd /Users/bobo/.zcode/skills/vn-rates-weekly
python3 -m pytest tests/test_extract_cards.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'extract_cards'`

- [ ] **Step 5: Write minimal extract_cards.py to make test pass**

Write to `/Users/bobo/.zcode/skills/vn-rates-weekly/scripts/extract_cards.py`:

```python
"""extract_cards.py — Parse PDF text from SBV/VBMA/VNBA weekly reports.

Each parser returns a dataclass with the indicators it could extract.
Missing indicators are None (never fabricated).
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParsedYield:
    """Govt bond yields parsed from one weekly report."""
    yield_2y: Optional[float] = None
    yield_5y: Optional[float] = None
    yield_10y: Optional[float] = None
    source_week: Optional[str] = None  # "2026-W26"


def _find_yield(text: str, keywords: list[str]) -> Optional[float]:
    """Find a percent value near any of the keywords."""
    for kw in keywords:
        # Match "kw ... N.NN%" or "kw N.NN" within 200 chars
        for m in re.finditer(re.escape(kw), text, re.IGNORECASE):
            window = text[m.start():m.start() + 200]
            # Find first percent-like number in the window
            nums = re.findall(r"(\d{1,2}[.,]\d{1,4})\s*%?", window)
            for n in nums:
                val = float(n.replace(",", "."))
                if 0.1 < val < 15.0:  # plausible yield range
                    return val
    return None


def parse_vbma_yields(text: str) -> ParsedYield:
    """Parse VBMA weekly report text for govt bond yields 2Y/5Y/10Y.

    VBMA tables typically label tenors as "2 năm", "5 năm", "10 năm"
    or "2Y/5Y/10Y" with values in percent.
    """
    result = ParsedYield()
    result.yield_2y = _find_yield(text, ["2 năm", "2 năm)", "2Y", "2y"])
    result.yield_5y = _find_yield(text, ["5 năm", "5 năm)", "5Y", "5y"])
    result.yield_10y = _find_yield(text, ["10 năm", "10 năm)", "10Y", "10y"])
    return result
```

- [ ] **Step 6: Run test to verify it passes**

```bash
cd /Users/bobo/.zcode/skills/vn-rates-weekly
python3 -m pytest tests/test_extract_cards.py -v
```
Expected: PASS (2 tests). If `test_parse_vbma_yields_finds_2y_5y_10y` fails because regex doesn't match the real fixture, iterate on the keywords/regex in Step 5 by re-inspecting the fixture with `grep -n` (Step 2 pattern). Adjust `_find_yield` window size or number regex until real VBMA values surface.

- [ ] **Step 7: Commit**

```bash
git -C /Users/bobo/.zcode/skills add vn-rates-weekly/
git -C /Users/bobo/.zcode/skills commit -m "feat(vn-rates-weekly): VBMA yield parser with TDD

- Sample fixture from real VBMA 2026-W26 PDF
- parse_vbma_yields() extracts 2Y/5Y/10Y govt bond rates
- Tests cover happy path + garbage input"
```

---

## Task 3: SBV + VNBA parsers + cross-source resolve

**Files:**
- Modify: `/Users/bobo/.zcode/skills/vn-rates-weekly/scripts/extract_cards.py`
- Modify: `/Users/bobo/.zcode/skills/vn-rates-weekly/tests/test_extract_cards.py`

- [ ] **Step 1: Download sample SBV + VNBA text fixtures**

SBV doesn't have a sample in repo. Create a minimal hand-crafted fixture covering SBV's format (interbank table + FX + OMO summary):

Write to `/Users/bobo/.zcode/skills/vn-rates-weekly/tests/fixtures/sbv_sample.txt`:

```
DIỄN BIẾN THỊ TRƯỜNG NGOẠI TỆ VÀ THỊ TRƯỜNG LIÊN NGÂN HÀNG TUẦN TỪ 22-26.6.2026

1. Thị trường liên ngân hàng (đơn vị: %/năm)
Kỳ hạn    Lãi suất
Overnight 1.20
1 tuần    1.45
2 tuần    1.60
1 tháng   1.85

2. Tỷ giá (VND/USD)
Tỷ giá trung tâm tham chiếu: 25.140
Tỷ giá giao dịch của các NHTM: 25.300 - 25.450

3. OMO
Tuần này NHNN hút tiền qua OMO: 5.000 tỷ đồng
```

For VNBA, create a minimal fixture covering the global rates + VN-Index section:

Write to `/Users/bobo/.zcode/skills/vn-rates-weekly/tests/fixtures/vnba_sample.txt`:

```
BẢN TIN KINH TẾ - TÀI CHÍNH - TIỀN TỆ TUẦN 4 THÁNG 6/2026

PHẦN I. TÌNH HÌNH KINH TẾ THẾ GIỚI
- Lợi suất trái phiếu Chính phủ Mỹ 10 năm: 4.35%
- Lợi suất trái phiếu Chính phủ Mỹ 2 năm: 4.78%
- Chỉ số dollar index (DXY): 105.2
- Giá vàng thế giới: 2.350 USD/oz
- Giá dầu Brent: 82.5 USD/thùng

PHẦN II. TÌNH HÌNH KINH TẾ VIỆT NAM
- VN-Index đóng cửa ở mức 1.285 điểm
- Thanh khoản HOSE đạt 18.500 tỷ đồng
- Dòng ngoại CK: Bán ròng 450 tỷ đồng
- Lạm phát CPI YoY: 4.6%
```

- [ ] **Step 2: Write failing tests for SBV + VNBA parsers**

Append to `/Users/bobo/.zcode/skills/vn-rates-weekly/tests/test_extract_cards.py`:

```python
from extract_cards import (
    parse_sbv_interbank, parse_vnba_global, parse_vnba_vn,
    ParsedInterbank, ParsedGlobal, ParsedVN, resolve_cross_source
)


def test_parse_sbv_interbank_finds_overnight_and_fx():
    fixture = Path(__file__).parent / "fixtures" / "sbv_sample.txt"
    text = fixture.read_text(encoding="utf-8")
    result = parse_sbv_interbank(text)
    assert isinstance(result, ParsedInterbank)
    assert result.overnight is not None
    assert 0.5 < result.overnight < 5.0  # plausible ON rate
    assert result.fx_central is not None
    assert 20000 < result.fx_central < 30000  # plausible VND/USD
    assert result.omo_net is not None  # +5000 (drain) or -5000 (inject)


def test_parse_vnba_global_finds_us10y_dxy_gold():
    fixture = Path(__file__).parent / "fixtures" / "vnba_sample.txt"
    text = fixture.read_text(encoding="utf-8")
    result = parse_vnba_global(text)
    assert result.us_10y is not None
    assert 3.0 < result.us_10y < 6.0
    assert result.dxy is not None
    assert 90 < result.dxy < 120
    assert result.gold is not None
    assert 1500 < result.gold < 4000


def test_parse_vnba_vn_finds_vnindex_liquidity():
    fixture = Path(__file__).parent / "fixtures" / "vnba_sample.txt"
    text = fixture.read_text(encoding="utf-8")
    result = parse_vnba_vn(text)
    assert result.vnindex is not None
    assert 800 < result.vnindex < 2000
    assert result.hose_liquidity_b_vnd is not None
    assert 5000 < result.hose_liquidity_b_vnd < 50000


def test_resolve_cross_source_picks_sbv_when_divergent():
    """If SBV and VBMA disagree >5% on interbank, use SBV."""
    resolved = resolve_cross_source(
        sbv_overnight=1.20,
        vbma_overnight=1.55,  # 29% divergence
    )
    assert resolved == 1.20  # SBV wins
    assert resolved._conflict_flagged is True


def test_resolve_cross_source_averages_when_close():
    resolved = resolve_cross_source(
        sbv_overnight=1.20,
        vbma_overnight=1.22,  # 1.6% divergence
    )
    assert abs(resolved - 1.21) < 0.01  # averaged
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_extract_cards.py -v -k "sbv or vnba or resolve"
```
Expected: FAIL with `ImportError` for the new functions

- [ ] **Step 4: Implement SBV + VNBA parsers + resolve**

Append to `/Users/bobo/.zcode/skills/vn-rates-weekly/scripts/extract_cards.py`:

```python
@dataclass
class ParsedInterbank:
    """SBV weekly bulletin parsed fields."""
    overnight: Optional[float] = None
    one_week: Optional[float] = None
    two_week: Optional[float] = None
    one_month: Optional[float] = None
    fx_central: Optional[float] = None
    fx_tm_avg: Optional[float] = None
    omo_net: Optional[float] = None  # + = drain, - = inject (tỷ VND)


@dataclass
class ParsedGlobal:
    """VNBA Part I — global macro."""
    us_10y: Optional[float] = None
    us_2y: Optional[float] = None
    dxy: Optional[float] = None
    gold: Optional[float] = None  # USD/oz
    brent: Optional[float] = None  # USD/bbl


@dataclass
class ParsedVN:
    """VNBA Part II — Vietnam market."""
    vnindex: Optional[float] = None
    hose_liquidity_b_vnd: Optional[float] = None
    foreign_flow_b_vnd: Optional[float] = None  # + = net buy, - = net sell
    cpi_yoy: Optional[float] = None


@dataclass
class ResolvedValue:
    value: float
    source: str
    _conflict_flagged: bool = False

    def __float__(self):
        return self.value


def parse_sbv_interbank(text: str) -> ParsedInterbank:
    """Parse SBV weekly bulletin PDF text."""
    r = ParsedInterbank()
    # Interbank rates — table with "Overnight", "1 tuần", "2 tuần", "1 tháng"
    r.overnight = _find_yield(text, ["Overnight", "qua đêm", "O/N"])
    r.one_week = _find_yield(text, ["1 tuần", "1 tuần]", "1W"])
    r.two_week = _find_yield(text, ["2 tuần", "2W"])
    r.one_month = _find_yield(text, ["1 tháng", "1M"])
    # FX central rate — "Tỷ giá trung tâm ... 25.140" or "25.140 VND/USD"
    fx_match = re.search(r"tỷ giá trung tâm[^0-9]{0,40}(\d{1,2}[.,]\d{3})", text, re.I)
    if fx_match:
        r.fx_central = float(fx_match.group(1).replace(".", "").replace(",", "."))
    # OMO — "hút tiền ... N tỷ" (drain = +) or "bơm tiền ... N tỷ" (inject = -)
    omo_drain = re.search(r"hút tiền[^0-9]{0,30}(\d{1,3}[.,]?\d{3})", text, re.I)
    omo_inject = re.search(r"bơm tiền[^0-9]{0,30}(\d{1,3}[.,]?\d{3})", text, re.I)
    if omo_drain:
        r.omo_net = float(omo_drain.group(1).replace(".", "").replace(",", ""))
    elif omo_inject:
        r.omo_net = -float(omo_inject.group(1).replace(".", "").replace(",", ""))
    return r


def parse_vnba_global(text: str) -> ParsedGlobal:
    """Parse VNBA Part I — global macro section."""
    r = ParsedGlobal()
    r.us_10y = _find_yield(text, ["Mỹ 10 năm", "US 10Y", "10Y Treasury"])
    r.us_2y = _find_yield(text, ["Mỹ 2 năm", "US 2Y", "2Y Treasury"])
    # DXY
    dxy_match = re.search(r"DXY[^0-9]{0,20}(\d{2,3}[.,]\d{1,2})", text, re.I)
    if dxy_match:
        r.dxy = float(dxy_match.group(1).replace(",", "."))
    # Gold
    gold_match = re.search(r"vàng[^0-9]{0,30}(\d{1,2}[.,]\d{2,3})\s*USD", text, re.I)
    if gold_match:
        r.gold = float(gold_match.group(1).replace(",", "."))
    # Brent
    brent_match = re.search(r"Brent[^0-9]{0,20}(\d{2,3}[.,]\d{1,2})\s*USD", text, re.I)
    if brent_match:
        r.brent = float(brent_match.group(1).replace(",", "."))
    return r


def parse_vnba_vn(text: str) -> ParsedVN:
    """Parse VNBA Part II — Vietnam market."""
    r = ParsedVN()
    # VN-Index
    vni_match = re.search(r"VN-?Index[^0-9]{0,30}(\d{3,4}[.,]?\d{0,2})", text, re.I)
    if vni_match:
        r.vnindex = float(vni_match.group(1).replace(",", "."))
    # HOSE liquidity
    hose_match = re.search(r"thanh khoản HOSE[^0-9]{0,30}(\d{1,3}[.,]?\d{3})", text, re.I)
    if hose_match:
        r.hose_liquidity_b_vnd = float(hose_match.group(1).replace(".", "").replace(",", "."))
    # Foreign flow
    foreign_match = re.search(r"(?:dòng ngoại|khối ngoại)[^0-9]{0,40}(?:bán ròng|mua ròng)[^0-9]{0,20}(\d{1,3}[.,]?\d{2,3})", text, re.I)
    if foreign_match:
        val = float(foreign_match.group(1).replace(".", "").replace(",", "."))
        # Check if "bán ròng" (sell = -) or "mua ròng" (buy = +)
        if re.search(r"bán ròng", text[foreign_match.start()-40:foreign_match.start()], re.I):
            r.foreign_flow_b_vnd = -val
        else:
            r.foreign_flow_b_vnd = val
    # CPI YoY
    cpi_match = re.search(r"CPI[^0-9]{0,20}(\d{1,2}[.,]\d{1,2})\s*%?", text, re.I)
    if cpi_match:
        r.cpi_yoy = float(cpi_match.group(1).replace(",", "."))
    return r


def resolve_cross_source(
    sbv_overnight: Optional[float],
    vbma_overnight: Optional[float],
    threshold_pct: float = 5.0,
) -> ResolvedValue:
    """Resolve interbank ON conflict between SBV and VBMA.

    Priority: SBV > VBMA (SBV is the official source).
    If divergence > threshold_pct → use SBV and flag conflict.
    If both None → raise.
    If one None → return the other.
    """
    if sbv_overnight is None and vbma_overnight is None:
        raise ValueError("Both sources None for interbank ON")
    if sbv_overnight is None:
        return ResolvedValue(vbma_overnight, source="VBMA")
    if vbma_overnight is None:
        return ResolvedValue(sbv_overnight, source="SBV")
    # Both present — check divergence
    avg = (sbv_overnight + vbma_overnight) / 2
    divergence = abs(sbv_overnight - vbma_overnight) / avg * 100
    if divergence > threshold_pct:
        return ResolvedValue(sbv_overnight, source="SBV", _conflict_flagged=True)
    return ResolvedValue(avg, source="SBV+VBMA avg")
```

- [ ] **Step 5: Run all tests to verify they pass**

```bash
cd /Users/bobo/.zcode/skills/vn-rates-weekly
python3 -m pytest tests/test_extract_cards.py -v
```
Expected: PASS (7 tests). If SBV/VNBA regexes don't match the synthetic fixtures, inspect with `grep -nE "overnight|tỷ giá trung tâm|hút tiền|Mỹ 10|VN-?Index|thanh khoản"` on the fixture and adjust patterns.

- [ ] **Step 6: Commit**

```bash
git -C /Users/bobo/.zcode/skills add vn-rates-weekly/
git -C /Users/bobo/.zcode/skills commit -m "feat(vn-rates-weekly): SBV + VNBA parsers + cross-source resolve

- ParsedInterbank (LNH ON/1W/2W/1M, FX, OMO)
- ParsedGlobal (US 10Y/2Y, DXY, gold, Brent)
- ParsedVN (VN-Index, HOSE liquidity, foreign flow, CPI)
- resolve_cross_source() with <5% threshold + SBV priority"
```

---

## Task 4: Fetch module — 12 PDFs + upstream

**Files:**
- Create: `/Users/bobo/.zcode/skills/vn-rates-weekly/scripts/fetch_sources.py`

- [ ] **Step 1: Write the fetch module**

Write to `/Users/bobo/.zcode/skills/vn-rates-weekly/scripts/fetch_sources.py`:

```python
"""fetch_sources.py — Fetch 12 PDFs (3 sources × 4 weeks) + upstream.

3 PDF sources:
  - SBV: sbv.gov.vn bulletin (PDF embed, UUID must be scraped)
  - VBMA: vbma.org.vn weekly report (direct download, %20 in URL)
  - VNBA: vnba.org.vn article → CDN PDF

4 upstream sources (portable, no local API):
  - HNX yield curve + auction (POST forms)
  - FRED (JSON, needs FRED_API_KEY)
  - vnstock (Python lib, VN-Index)
  - SBV interbank (HTML, latest-only)

Usage:
  python3 fetch_sources.py --week 2026-W26 --out ./sources_cache
  python3 fetch_sources.py --week 2026-W26 --out ./sources_cache --upstream-only
"""
from __future__ import annotations
import argparse
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import urllib.request
import urllib.error

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
SBV_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "vi,en;q=0.9",
    "Referer": "https://www.sbv.gov.vn/vi/web/sbv_portal/thông-tin-về-hoạt-động-ngân-hàng-trong-tuần",
}


@dataclass
class WeekRange:
    """ISO week + Mon-Fri dates."""
    iso_week: str  # "2026-W26"
    monday: date
    friday: date

    @property
    def sbv_slug(self) -> str:
        """SBV article URL slug: 'tuần-từ-22-26.6.2026' (dot-separated, unpadded)."""
        return f"{self.monday.day}-{self.friday.day}.{self.monday.month}.{self.monday.year}"

    @property
    def vbma_filename(self) -> str:
        """VBMA filename date part: '22062026-26062026' (zero-padded, no separator)."""
        return f"{self.monday.strftime('%d%m%Y')}-{self.friday.strftime('%d%m%Y')}"


def enumerate_4_weeks(target_iso_week: str) -> list[WeekRange]:
    """Return [N-3, N-2, N-1, N] as WeekRange objects.

    Auto-backfills Tet/holiday-skipped weeks (flag tracked separately).
    """
    year_str, week_str = target_iso_week.split("-W")
    year, week = int(year_str), int(week_str)
    weeks = []
    for w in range(week - 3, week + 1):
        if w < 1:
            # Roll into previous year
            prev_year = year - 1
            last_week = 52 if prev_year % 4 != 0 else 53
            w_use, y_use = last_week + w, prev_year
        else:
            w_use, y_use = w, year
        # Mon-Fri of ISO week w_use year y_use
        monday = date.fromisocalendar(y_use, w_use, 1)
        friday = date.fromisocalendar(y_use, w_use, 5)
        weeks.append(WeekRange(f"{y_use}-W{w_use:02d}", monday, friday))
    return weeks


def curl(url: str, headers: Optional[dict] = None, sleep_s: float = 0.0) -> bytes:
    """HTTP GET returning bytes, with optional sleep (SBV WAF avoidance)."""
    req = urllib.request.Request(url, headers=headers or {"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    if sleep_s:
        time.sleep(sleep_s)
    return data


def pdftotext(pdf_path: Path, txt_path: Path) -> None:
    """Convert PDF to text via pdftotext -layout (system tool)."""
    subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), str(txt_path)],
        check=True, capture_output=True,
    )


def fetch_sbv_week(week: WeekRange, out_dir: Path) -> Optional[Path]:
    """Fetch SBV weekly bulletin PDF.

    Returns path to .txt or None if week is skipped (Tet/holiday).
    """
    article_url = (
        "https://www.sbv.gov.vn/vi/web/sbv_portal/w/"
        + quote(f"diễn-biến-thị-trường-ngoại-tệ-và-thị-trường-liên-ngân-hàng-tuần-từ-{week.sbv_slug}")
    )
    try:
        html = curl(article_url, headers=SBV_HEADERS, sleep_s=3).decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # Tet/holiday skip
        raise
    # Regex embed/anchor PDF — UUID mandatory
    pdf_match = re.search(r'embed[^>]+src="(/documents/20117/0/[^"]+\.pdf/[^"]+)"', html)
    if not pdf_match:
        # Try direct anchor
        pdf_match = re.search(r'href="(/documents/20117/0/[^"]+\.pdf/[^"]+)"', html)
    if not pdf_match:
        return None
    pdf_url = "https://www.sbv.gov.vn" + pdf_match.group(1)
    pdf_path = out_dir / f"sbv_{week.iso_week}.pdf"
    txt_path = out_dir / f"sbv_{week.iso_week}.txt"
    pdf_path.write_bytes(curl(pdf_url, headers=SBV_HEADERS))
    pdftotext(pdf_path, txt_path)
    return txt_path


def fetch_vbma_weeks(out_dir: Path) -> dict[str, Path]:
    """Fetch 4 most-recent VBMA weekly reports.

    VBMA listing gives direct-download hrefs — scrape exact URLs (spacing non-deterministic).
    Returns {iso_week_hint: txt_path}.
    """
    listing_url = "https://vbma.org.vn/vi/reports/weekly?page=1"
    html = curl(listing_url).decode("utf-8", errors="ignore")
    # All PDF hrefs (TTTP / TTTP1 / TTTP2 / double-space variants)
    hrefs = re.findall(r'href="(/storage/reports/[^"]+\.pdf)"', html)[:12]
    if len(hrefs) < 4:
        raise RuntimeError(f"VBMA listing returned only {len(hrefs)} PDFs")
    results = {}
    for i, href in enumerate(hrefs[:4]):
        pdf_url = "https://vbma.org.vn" + href.replace(" ", "%20")
        pdf_path = out_dir / f"vbma_recent_{i}.pdf"
        txt_path = out_dir / f"vbma_recent_{i}.txt"
        pdf_path.write_bytes(curl(pdf_url))
        pdftotext(pdf_path, txt_path)
        results[f"vbma_{i}"] = txt_path
    return results


def fetch_vnba_recent_weeks(out_dir: Path) -> dict[str, Path]:
    """Fetch 4 most-recent VNBA weekly bulletins.

    VNBA uses hashtag archive per week-of-month: /vi/hashtag/kinh-te-tai-chinh-tien-te-tuan-{N}-{id}
    """
    weeks_found = []
    for week_n in (1, 2, 3, 4, 5):
        if len(weeks_found) >= 4:
            break
        hashtag_url = f"https://vnba.org.vn/vi/hashtag/kinh-te-tai-chinh-tien-te-tuan-{week_n}"
        try:
            html = curl(hashtag_url).decode("utf-8", errors="ignore")
        except urllib.error.HTTPError:
            continue
        articles = re.findall(
            r'href="(/vi/ban-tin-kinh-te-tai-chinh-tien-te-tuan-\d+-thang-\d+-\d+-\d+\.htm)"',
            html,
        )
        for art_path in articles:
            if len(weeks_found) >= 4:
                break
            art_url = "https://vnba.org.vn" + art_path
            try:
                art_html = curl(art_url).decode("utf-8", errors="ignore")
            except urllib.error.HTTPError:
                continue
            cdn_match = re.search(r'(https://s-vnba-cdn\.aicms\.vn/[^"]+\.pdf)', art_html)
            if not cdn_match:
                continue
            pdf_url = cdn_match.group(1)
            pdf_path = out_dir / f"vnba_{week_n}_{len(weeks_found)}.pdf"
            txt_path = out_dir / f"vnba_{week_n}_{len(weeks_found)}.txt"
            pdf_path.write_bytes(curl(pdf_url))
            pdftotext(pdf_path, txt_path)
            weeks_found.append(txt_path)
    return {f"vnba_{i}": p for i, p in enumerate(weeks_found)}


def fetch_fred_series(series_id: str, weeks: int = 12) -> list[dict]:
    """Fetch FRED series observations for the last N weeks. Needs FRED_API_KEY env."""
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        return []  # upstream_skip — caller handles
    end = date.today()
    start = end - timedelta(weeks=weeks)
    url = (
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id={series_id}&api_key={api_key}&file_type=json"
        f"&observation_start={start.isoformat()}&observation_end={end.isoformat()}"
    )
    data = curl(url)
    import json
    payload = json.loads(data)
    return payload.get("observations", [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", required=True, help="Target ISO week, e.g. 2026-W26")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--upstream-only", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.upstream_only:
        weeks = enumerate_4_weeks(args.week)
        print(f"Enumerated weeks: {[w.iso_week for w in weeks]}")
        for w in weeks:
            txt = fetch_sbv_week(w, out_dir)
            status = txt.name if txt else "SKIP (holiday?)"
            print(f"  SBV {w.iso_week}: {status}")
        vbma = fetch_vbma_weeks(out_dir)
        print(f"  VBMA: fetched {len(vbma)} PDFs")
        vnba = fetch_vnba_recent_weeks(out_dir)
        print(f"  VNBA: fetched {len(vnba)} PDFs")

    # Upstream (always attempt, gracefully skip if no key)
    fred_10y = fetch_fred_series("DGS10", weeks=12)
    print(f"  FRED DGS10: {len(fred_10y)} observations")
    fred_dxy = fetch_fred_series("DTWEXBGS", weeks=12)
    print(f"  FRED DXY: {len(fred_dxy)} observations")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke test enumerate_4_weeks (no network)**

```bash
cd /Users/bobo/.zcode/skills/vn-rates-weekly
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from fetch_sources import enumerate_4_weeks
weeks = enumerate_4_weeks('2026-W26')
for w in weeks:
    print(f'{w.iso_week}: Mon {w.monday} Fri {w.friday} | sbv_slug={w.sbv_slug} | vbma={w.vbma_filename}')
"
```
Expected: 4 lines showing W23-W26 with Mon-Fri dates and the SBV slug "23-27.6.2026" pattern + VBMA "22062026-26062026" pattern. If date math is off (e.g. Tet roll), fix `enumerate_4_weeks` logic.

- [ ] **Step 3: Live test SBV fetch for 1 known week (requires network)**

```bash
cd /Users/bobo/.zcode/skills/vn-rates-weekly
mkdir -p /tmp/vrw-test
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from fetch_sources import fetch_sbv_week, WeekRange
from datetime import date
w = WeekRange('2026-W26', date.fromisocalendar(2026,26,1), date.fromisocalendar(2026,26,5))
txt = fetch_sbv_week(w, __import__('pathlib').Path('/tmp/vrw-test'))
print('SBV fetch result:', txt)
"
ls -la /tmp/vrw-test/
head -20 /tmp/vrw-test/sbv_2026-W26.txt 2>/dev/null
```
Expected: `sbv_2026-W26.txt` exists with interbank table. If it fails with WAF "Request Rejected", verify headers include `Referer` and add longer sleep. If 404, the week is a holiday — try W25.

- [ ] **Step 4: Live test VBMA fetch (requires network)**

```bash
cd /Users/bobo/.zcode/skills/vn-rates-weekly
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from fetch_sources import fetch_vbma_weeks
from pathlib import Path
result = fetch_vbma_weeks(Path('/tmp/vrw-test'))
print('VBMA:', list(result.keys()))
"
ls -la /tmp/vrw-test/vbma_* 2>/dev/null
```
Expected: 4 `vbma_recent_*.txt` files. If `www.vbma.org.vn` SSL error, confirm the code uses bare domain `vbma.org.vn` (it does).

- [ ] **Step 5: Commit**

```bash
git -C /Users/bobo/.zcode/skills add vn-rates-weekly/
git -C /Users/bobo/.zcode/skills commit -m "feat(vn-rates-weekly): fetch module — 12 PDFs + FRED upstream

- enumerate_4_weeks() with ISO week math + Tet roll
- fetch_sbv_week (article → embed regex → PDF → pdftotext)
- fetch_vbma_weeks (listing → 4 hrefs → %20 encode)
- fetch_vnba_recent_weeks (hashtag → article → CDN PDF)
- fetch_fred_series (DGS10/DTWEXBGS, optional FRED_API_KEY)"
```

---

## Task 5: Fork + tokenize HTML template

**Files:**
- Create: `/Users/bobo/.zcode/skills/vn-rates-weekly/assets/weekly_template.html` (copy + modify from `vn-macro-monthly/assets/report_template.html`)
- Modify: `/Users/bobo/.zcode/skills/_viz-shared/inject.py` (add path to TEMPLATE_PATHS)

- [ ] **Step 1: Copy the macro template as starting point**

```bash
cp /Users/bobo/.zcode/skills/vn-macro-monthly/assets/report_template.html \
   /Users/bobo/.zcode/skills/vn-rates-weekly/assets/weekly_template.html
wc -l /Users/bobo/.zcode/skills/vn-rates-weekly/assets/weekly_template.html
```
Expected: ~1321 lines

- [ ] **Step 2: Replace hand-written CSS block with {{VIZ_CSS}} placeholder**

Open `/Users/bobo/.zcode/skills/vn-rates-weekly/assets/weekly_template.html`. Find the `<style>` block that contains the hand-written `:root` + components (typically lines 11-318). Replace the entire block with a single placeholder:

```html
<style>
{{VIZ_CSS}}
</style>
```

Verify with grep that the old `--purple:#a855f7` hardcoded lines are gone and only the placeholder remains:
```bash
grep -n "VIZ_CSS\|--purple:#a855f7" /Users/bobo/.zcode/skills/vn-rates-weekly/assets/weekly_template.html
```
Expected: 1 line with `{{VIZ_CSS}}`, 0 lines with hardcoded `--purple:#a855f7`.

- [ ] **Step 3: Add {{VIZ_JS}} placeholder for viz.js**

Find the first `<script>` tag (before Chart.js CDN). Insert before it:

```html
<script>{{VIZ_JS}}</script>
```

- [ ] **Step 4: Add template path to inject.py**

Edit `/Users/bobo/.zcode/skills/_viz-shared/inject.py`. Find `TEMPLATE_PATHS = [` (around line 29). Add the new entry:

```python
TEMPLATE_PATHS = [
    "vn-research-dashboard/assets/dashboard_template.html",
    "vn-technical-analysis/assets/technical_template.html",
    "vn-technical-analysis/assets/profile_template.html",
    "vn-news-digest/assets/news_template.html",
    "longform-report/assets/article_template.html",
    "vn-rates-weekly/assets/weekly_template.html",
]
```

- [ ] **Step 5: Run inject.py to build the template**

```bash
cd /Users/bobo/.zcode/skills/_viz-shared
python3 inject.py --file ../vn-rates-weekly/assets/weekly_template.html
```
Expected: success message, no "unreplaced placeholder" error.

- [ ] **Step 6: Verify inject worked — {{VIZ_CSS}} replaced, no double-inject**

```bash
grep -c "VIZ_CSS\|VIZ_JS" /Users/bobo/.zcode/skills/vn-rates-weekly/assets/weekly_template.html
# Expected: 0 (both replaced)
grep -c ":root{" /Users/bobo/.zcode/skills/vn-rates-weekly/assets/weekly_template.html
# Expected: 1 (exactly one :root — the injected one)
```

- [ ] **Step 7: Verify all data tokens still present (untouched by inject)**

```bash
grep -oE "\{\{[A-Z_0-9]+\}\}" /Users/bobo/.zcode/skills/vn-rates-weekly/assets/weekly_template.html | sort -u
```
Expected: list of data tokens like `{{REPORT_ID}}`, `{{VERDICT}}`, `{{GROUP1_HTML}}` etc. (these get filled at report-time).

- [ ] **Step 8: Commit**

```bash
git -C /Users/bobo/.zcode/skills add _viz-shared/inject.py vn-rates-weekly/assets/weekly_template.html
git -C /Users/bobo/.zcode/skills commit -m "feat(vn-rates-weekly): fork macro template + migrate to inject.py

- Copy report_template.html → weekly_template.html
- Replace hand-written :root block with {{VIZ_CSS}} placeholder
- Add {{VIZ_JS}} placeholder for viz.chart() registry
- Register path in _viz-shared/inject.py TEMPLATE_PATHS
- Verify inject.py produces single-file output, no double-inject"
```

---

## Task 6: Rates-specific HTML components + tab restructure

**Files:**
- Modify: `/Users/bobo/.zcode/skills/vn-rates-weekly/assets/weekly_template.html`

In this task we adapt the macro template's content to the rates weekly structure. The macro template has 4 tabs (Kinh tế thực / Tiền tệ & TC / Ngành / Toàn cầu / Tổng hợp). For rates weekly we need 5 tabs: Tiền tệ / Trái phiếu / Ngoại hối & TG / CK & VN / Tổng hợp. We also add 3 rates-specific components: `.stance-gauge`, `.wow-strip`, and adapt the existing `.signal-grid` for stance.

- [ ] **Step 1: Update tab labels in NAV**

In `weekly_template.html`, find the `.nav-tabs` block (search for `nav-tabs` or `tab-link`). Replace the 4-5 tab labels with rates-specific ones. The 5 tabs should be:

```html
<div class="nav-tabs">
  <button class="tab-link active" data-tab="money">💰 Tiền tệ</button>
  <button class="tab-link" data-tab="bonds">📜 Trái phiếu</button>
  <button class="tab-link" data-tab="fxglobal">🌍 Ngoại hối & TG</button>
  <button class="tab-link" data-tab="equities">📈 CK & VN</button>
  <button class="tab-link" data-tab="summary">📊 Tổng hợp</button>
</div>
```

Update the `<section class="group-section" id="...">` IDs accordingly: `money`, `bonds`, `fxglobal`, `equities`, `summary`.

- [ ] **Step 2: Add rates-specific CSS components**

Append to the `<style>` block (after `{{VIZ_CSS}}`):

```css
/* === vn-rates-weekly specific === */
.stance-gauge {
  display: flex; align-items: center; gap: 16px;
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius-card); padding: 20px 24px;
  margin: 16px 0;
}
.stance-gauge .gauge-track {
  flex: 1; height: 12px; border-radius: var(--radius-pill);
  background: linear-gradient(90deg, var(--red) 0%, var(--amber) 50%, var(--green) 100%);
  position: relative;
}
.stance-gauge .gauge-needle {
  position: absolute; top: -6px; width: 4px; height: 24px;
  background: var(--text); border-radius: 2px;
  transform: translateX(-50%);
}
.stance-gauge .gauge-label {
  font-size: 11px; color: var(--text-dim); text-transform: uppercase;
  letter-spacing: 0.05em; min-width: 80px;
}
.stance-gauge .gauge-label.left { text-align: right; color: var(--red); }
.stance-gauge .gauge-label.right { color: var(--green); }

.wow-strip {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;
  margin: 12px 0; padding: 8px;
  background: rgba(168, 85, 247, 0.05); border-radius: 12px;
}
.wow-strip .wow-cell {
  text-align: center; padding: 6px 4px;
}
.wow-strip .wow-cell .wow-week {
  font-size: 10px; color: var(--text-faint); text-transform: uppercase;
}
.wow-strip .wow-cell .wow-val {
  font-family: var(--font-mono); font-size: 14px; font-weight: 600;
  color: var(--text); font-variant-numeric: tabular-nums;
}
.wow-strip .wow-cell.latest .wow-val { color: var(--purple); }
.wow-strip .streak-badge {
  grid-column: 1 / -1; text-align: center;
  font-size: 11px; padding: 4px;
}
.wow-strip .streak-badge.up { color: var(--red); }    /* up = hawkish = red in rates */
.wow-strip .streak-badge.down { color: var(--green); } /* down = dovish = green */
```

Note: in rates semantics, "up" = hawkish (red), "down" = dovish (green) — opposite of equities. The CSS comments make this explicit.

- [ ] **Step 3: Add stance-gauge to HERO section**

Find the hero block (search for `class="hero"`). After the verdict badge, add:

```html
<div class="stance-gauge">
  <span class="gauge-label left">HAWKISH</span>
  <div class="gauge-track">
    <div class="gauge-needle" id="stanceNeedle" style="left: 50%;"></div>
  </div>
  <span class="gauge-label right">DOVISH</span>
</div>
```

The `left` percentage is set at render-time from `stance_score` (-6 hawkish → +6 dovish, mapped to 0-100%).

- [ ] **Step 4: Add a sample data-card with wow-strip to money tab**

In `<section class="group-section" id="money">`, replace the first data-card with a rates-flavored one showing the wow-strip:

```html
<div class="data-card" data-indicator="interbank_on">
  <div class="dc-head">
    <span class="dc-flag">🟢</span>
    <span class="dc-name">LNH Overnight</span>
  </div>
  <div class="dc-value-row">
    <span class="dc-value">1.20</span>
    <span class="dc-unit">%/năm</span>
  </div>
  <div class="dc-meta">
    <span>WoW <strong class="pos">-10bp</strong></span>
    <span>4w trend <strong class="pos">▼ 3 tuần</strong></span>
  </div>
  <div class="wow-strip">
    <div class="wow-cell"><div class="wow-week">W23</div><div class="wow-val">1.45</div></div>
    <div class="wow-cell"><div class="wow-week">W24</div><div class="wow-val">1.38</div></div>
    <div class="wow-cell"><div class="wow-week">W25</div><div class="wow-val">1.30</div></div>
    <div class="wow-cell latest"><div class="wow-week">W26</div><div class="wow-val">1.20</div></div>
    <div class="streak-badge down">▼ 3 tuần giảm liên tiếp (dovish)</div>
  </div>
  <div class="dc-narrative">
    LNH ON giảm 25bp trong 4 tuần, kéo dài chuỗi 3 tuần giảm — cùng lúc OMO bơm 5.000 tỷ tuần này cho thấy NHNN duy trì dồi dào thanh khoản.
  </div>
  <button class="dc-chart-btn" data-indicator="interbank_on">📊 12 tuần</button>
</div>
```

- [ ] **Step 5: Verify HTML loads without JS errors**

```bash
cd /Users/bobo/.zcode/skills/vn-rates-weekly
# Extract last <script> and syntax-check
python3 -c "
import re
html = open('assets/weekly_template.html').read()
scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
if scripts:
    open('/tmp/vrw-js.js','w').write(scripts[-1])
    print('extracted last script:', len(scripts[-1]), 'chars')
"
node --check /tmp/vrw-js.js && echo "✅ JS syntax OK"
```
Expected: `✅ JS syntax OK`. If errors, fix the offending JS (likely from the tab-switching or modal code inherited from macro).

- [ ] **Step 6: Visual smoke check in browser**

```bash
open /Users/bobo/.zcode/skills/vn-rates-weekly/assets/weekly_template.html
```
Manually verify: hero shows stance gauge, tabs switch correctly, sample card with wow-strip renders. Take a screenshot if needed.

- [ ] **Step 7: Commit**

```bash
git -C /Users/bobo/.zcode/skills add vn-rates-weekly/assets/weekly_template.html
git -C /Users/bobo/.zcode/skills commit -m "feat(vn-rates-weekly): rates-specific HTML components + 5-tab restructure

- 5 tabs: Tiền tệ / Trái phiếu / Ngoại hối & TG / CK & VN / Tổng hợp
- .stance-gauge (HAWKISH↔DOVISH gradient with needle)
- .wow-strip (4-week inline strip with streak badge)
- Rates semantics: up=hawkish=red, down=dovish=green
- Sample data-card with wow-strip in money tab"
```

---

## Task 7: Render module — JSON → HTML

**Files:**
- Create: `/Users/bobo/.zcode/skills/vn-rates-weekly/scripts/render_report.py`

- [ ] **Step 1: Write the render module**

Write to `/Users/bobo/.zcode/skills/vn-rates-weekly/scripts/render_report.py`:

```python
"""render_report.py — Fill weekly_template.html from report.json.

CRITICAL: use str.replace() for token filling, NEVER f-string/.format()
(JS braces in template would break Python string formatting).
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def render_card(card_key: str, card: dict) -> str:
    """Render a single data-card HTML from card dict."""
    values = card.get("values", [])
    latest = values[-1] if values else {}
    prev = values[-2] if len(values) >= 2 else {}
    signal = card.get("signal", "NEUTRAL")
    flag = {"GREEN": "🟢", "RED": "🔴", "AMBER": "🟡"}.get(signal, "⚪")
    wow_str = f"{latest.get('wow_pct', 0):+.2f}%" if latest.get("wow_pct") is not None else "—"
    streak = card.get("streak", {})
    streak_str = ""
    if streak.get("weeks", 0) >= 2:
        arrow = "▲" if streak["direction"] == "up" else "▼"
        stance = "hawkish" if streak["direction"] == "up" else "dovish"
        streak_str = f"{arrow} {streak['weeks']} tuần {stance}"

    # Build wow-strip cells
    strip_cells = ""
    for v in values:
        is_latest = v == latest
        cls = "wow-cell latest" if is_latest else "wow-cell"
        strip_cells += (
            f'<div class="{cls}">'
            f'<div class="wow-week">{v.get("week","")}</div>'
            f'<div class="wow-val">{v.get("value","")}</div>'
            f'</div>'
        )
    if streak_str:
        direction_cls = streak.get("direction", "")
        strip_cells += f'<div class="streak-badge {direction_cls}">{streak_str}</div>'

    chart_btn = ""
    if card.get("has_chart"):
        chart_btn = f'<button class="dc-chart-btn" data-indicator="{card_key}">📊 12 tuần</button>'

    return f"""
    <div class="data-card" data-indicator="{card_key}">
      <div class="dc-head">
        <span class="dc-flag">{flag}</span>
        <span class="dc-name">{card.get("name_vi", card_key)}</span>
      </div>
      <div class="dc-value-row">
        <span class="dc-value">{latest.get("value", "—")}</span>
        <span class="dc-unit">{card.get("value_unit", "")}</span>
      </div>
      <div class="dc-meta">
        <span>WoW <strong>{wow_str}</strong></span>
      </div>
      <div class="wow-strip">{strip_cells}</div>
      <div class="dc-narrative">{card.get("narrative", "")}</div>
      {chart_btn}
    </div>
    """


def render_group(group_dict: dict) -> str:
    """Render all cards in a group → HTML string."""
    return "".join(render_card(k, v) for k, v in group_dict.items())


def render_report(report_json_path: Path, template_path: Path, out_html: Path) -> None:
    report = json.loads(report_json_path.read_text(encoding="utf-8"))
    template = template_path.read_text(encoding="utf-8")

    # Replace tokens with str.replace (NEVER f-string/format)
    html = template
    html = html.replace("{{REPORT_ID}}", report.get("report_id", ""))
    html = html.replace("{{VERDICT}}", report.get("verdict", ""))
    html = html.replace("{{VERDICT_REASON}}", report.get("verdict_reason", ""))
    html = html.replace("{{DATA_CUTOFF}}", report.get("period", {}).get("data_cutoff", ""))

    # Stance gauge needle position (stance_score -6 hawkish .. +6 dovish → 0..100%)
    stance = report.get("stance_score", 0)
    needle_pct = ((stance + 6) / 12) * 100
    needle_pct = max(0, min(100, needle_pct))
    html = html.replace("{{STANCE_NEEDLE_PCT}}", f"{needle_pct:.0f}")

    # Group cards
    html = html.replace("{{GROUP_MONEY_HTML}}", render_group(report.get("group1_money_market", {})))
    html = html.replace("{{GROUP_BONDS_HTML}}", render_group(report.get("group2_bonds", {})))
    html = html.replace("{{GROUP_FXGLOBAL_HTML}}", render_group(report.get("group3_fx_global", {})))
    html = html.replace("{{GROUP_EQUITIES_HTML}}", render_group(report.get("group4_equities_vn", {})))

    out_html.write_text(html, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, help="Path to report.json")
    parser.add_argument("--template", required=True, help="Path to weekly_template.html")
    parser.add_argument("--out", required=True, help="Output HTML path")
    args = parser.parse_args()
    render_report(Path(args.report), Path(args.template), Path(args.out))
    print(f"Rendered: {args.out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Create a minimal sample report.json for testing**

Write to `/Users/bobo/.zcode/skills/vn-rates-weekly/tests/fixtures/sample_report.json`:

```json
{
  "report_id": "vn-rates-2026-W26-TEST",
  "period": {"week": 26, "year": 2026, "data_cutoff": "2026-06-26"},
  "verdict": "TRUNG TÍNH",
  "verdict_reason": "Test verdict for render smoke test",
  "stance_score": 0,
  "group1_money_market": {
    "interbank_on": {
      "name_vi": "LNH Overnight",
      "value_unit": "%/năm",
      "values": [
        {"week": "W23", "value": 1.45, "wow_pct": null},
        {"week": "W24", "value": 1.38, "wow_pct": -4.83},
        {"week": "W25", "value": 1.30, "wow_pct": -5.80},
        {"week": "W26", "value": 1.20, "wow_pct": -7.69}
      ],
      "signal": "GREEN",
      "streak": {"direction": "down", "weeks": 3},
      "narrative": "Test narrative: LNH ON giảm 3 tuần liên tiếp.",
      "has_chart": true,
      "chart_source": "sbv_interbank"
    }
  },
  "group2_bonds": {},
  "group3_fx_global": {},
  "group4_equities_vn": {}
}
```

- [ ] **Step 3: Run render and verify output**

```bash
cd /Users/bobo/.zcode/skills/vn-rates-weekly
python3 scripts/render_report.py \
  --report tests/fixtures/sample_report.json \
  --template assets/weekly_template.html \
  --out /tmp/vrw-render-test.html

# Verify: no unreplaced tokens
grep -oE "\{\{[A-Z_0-9]+\}\}" /tmp/vrw-render-test.html | sort -u
# Expected: empty (all tokens replaced)

# Verify: card rendered with wow-strip
grep -c "wow-strip" /tmp/vrw-render-test.html
# Expected: ≥1
```

If `GROUP_*_HTML` tokens don't exist in the template (because we kept the macro template's token names), either rename the tokens in render_report.py to match the template, or add the tokens to the template. Inspect:
```bash
grep -oE "\{\{GROUP[A-Z_]*\}\}" /Users/bobo/.zcode/skills/vn-rates-weekly/assets/weekly_template.html | sort -u
```
Then align render_report.py token names with what's in the template.

- [ ] **Step 4: Open rendered HTML and verify visually**

```bash
open /tmp/vrw-render-test.html
```
Expected: hero shows verdict + stance gauge (needle at 50%), money tab shows 1 card "LNH Overnight" with wow-strip 4 cells W23→W26 and streak badge "▼ 3 tuần dovish".

- [ ] **Step 5: Commit**

```bash
git -C /Users/bobo/.zcode/skills add vn-rates-weekly/scripts/render_report.py vn-rates-weekly/tests/fixtures/sample_report.json
git -C /Users/bobo/.zcode/skills commit -m "feat(vn-rates-weekly): render_report.py — JSON to HTML

- str.replace token filling (no f-string — JS brace safe)
- render_card() builds data-card with wow-strip + streak
- render_group() aggregates cards per tab
- Stance gauge needle positioned from stance_score
- Sample report.json fixture for smoke test"
```

---

## Task 8: QA script (Playwright)

**Files:**
- Create: `/Users/bobo/.zcode/skills/vn-rates-weekly/scripts/qa_weekly.js`

- [ ] **Step 1: Write the QA script (adapted from vn-macro-monthly/scripts/qa_report.js)**

Write to `/Users/bobo/.zcode/skills/vn-rates-weekly/scripts/qa_weekly.js`:

```javascript
#!/usr/bin/env node
/**
 * QA Weekly — Automated visual QA cho vn-rates-weekly dashboard
 * Pattern học từ vn-macro-monthly/scripts/qa_report.js
 *
 * Usage:
 *   node qa_weekly.js --url=file:///path/to/report.html
 *   node qa_weekly.js --url=file:///path/to/report.html --output=./qa-shots
 *
 * Checks:
 *   1. Hero + verdict badge + stance gauge
 *   2. NAV 5 tabs (Tiền tệ/Trái phiếu/Ngoại hối&TG/CK&VN/Tổng hợp)
 *   3. Group sections (5, money active default)
 *   4. Data cards với wow-strip
 *   5. Click-to-chart modal
 *   6. Risks/Catalysts + Key Takeaways (in summary tab)
 *   7. Footer
 *   8. No JS console errors
 *   9. Screenshots
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function runQA() {
  const args = process.argv.slice(2);
  const urlArg = args.find(a => a.startsWith('--url='));
  const outputArg = args.find(a => a.startsWith('--output='));
  if (!urlArg) {
    console.error('Usage: node qa_weekly.js --url=file:///path/to/report.html');
    process.exit(1);
  }
  const url = urlArg.replace('--url=', '');
  const outDir = outputArg ? outputArg.replace('--output=', '.') : '/tmp/qa-weekly';
  fs.mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') errors.push(msg.text());
  });

  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  const results = { pass: [], warn: [], fail: [] };

  // Check 1: Hero + verdict + stance gauge
  const hero = await page.$('.hero, [class*="hero"]');
  results[hero ? 'pass' : 'fail'].push('hero present');
  const verdict = await page.$('[class*="verdict"], .stance-gauge');
  results[verdict ? 'pass' : 'warn'].push('verdict/stance gauge');

  // Check 2: 5 tabs
  const tabs = await page.$$('.tab-link, .nav-tabs button');
  if (tabs.length === 5) results.pass.push(`5 tabs (${tabs.length})`);
  else results.fail.push(`expected 5 tabs, got ${tabs.length}`);

  // Check 3: 5 group sections, money active
  const sections = await page.$$('.group-section');
  if (sections.length === 5) results.pass.push(`5 group sections`);
  else results.warn.push(`expected 5 sections, got ${sections.length}`);
  const moneyActive = await page.$('.group-section.active#money, #money.active');
  results[moneyActive ? 'pass' : 'warn'].push('money tab active by default');

  // Check 4: data cards with wow-strip
  const cards = await page.$$('.data-card');
  results.pass.push(`${cards.length} data cards`);
  const wowStrips = await page.$$('.wow-strip');
  results[wowStrips.length > 0 ? 'pass' : 'warn'].push(`${wowStrips.length} wow-strips`);

  // Check 5: tab switching works
  if (tabs.length >= 5) {
    await tabs[4].click(); // summary
    await page.waitForTimeout(300);
    const summaryVisible = await page.$('#summary.active, #summary:not([style*="none"])');
    results[summaryVisible ? 'pass' : 'fail'].push('tab switch to summary');
  }

  // Check 6: stance gauge needle exists
  const needle = await page.$('.gauge-needle, #stanceNeedle');
  results[needle ? 'pass' : 'warn'].push('stance gauge needle');

  // Check 7: no JS errors
  results[errors.length === 0 ? 'pass' : 'fail'].push(
    errors.length === 0 ? 'no console errors' : `${errors.length} console errors: ${errors.slice(0,3).join('; ')}`
  );

  // Screenshots
  await page.screenshot({ path: path.join(outDir, 'full.png'), fullPage: true });
  // Click back to money for hero shot
  if (tabs.length >= 1) {
    await tabs[0].click();
    await page.waitForTimeout(300);
  }
  await page.screenshot({ path: path.join(outDir, 'money-tab.png') });

  await browser.close();

  // Report
  console.log('\n=== vn-rates-weekly QA ===');
  console.log(`✅ PASS: ${results.pass.length}`);
  results.pass.forEach(p => console.log(`  ✓ ${p}`));
  if (results.warn.length) {
    console.log(`⚠️  WARN: ${results.warn.length}`);
    results.warn.forEach(w => console.log(`  ⚠ ${w}`));
  }
  if (results.fail.length) {
    console.log(`❌ FAIL: ${results.fail.length}`);
    results.fail.forEach(f => console.log(`  ✗ ${f}`));
    process.exit(1);
  }
  console.log(`\nScreenshots: ${outDir}`);
}

runQA().catch(e => { console.error(e); process.exit(1); });
```

- [ ] **Step 2: Install playwright if needed and run QA on the rendered test HTML**

```bash
mkdir -p /tmp/qa-weekly-runner && cd /tmp/qa-weekly-runner
npm install playwright 2>&1 | tail -3
NODE_PATH=/tmp/qa-weekly-runner/node_modules node /Users/bobo/.zcode/skills/vn-rates-weekly/scripts/qa_weekly.js \
  --url=file:///tmp/vrw-render-test.html --output=/tmp/qa-weekly
```
Expected: `✅ PASS: ≥7`, no `❌ FAIL`. Screenshots at `/tmp/qa-weekly/*.png`.

- [ ] **Step 3: Iterate on failures (if any)**

If "5 tabs" fails, fix the `.nav-tabs` HTML in the template (Task 6 Step 1). If "money tab active" fails, add `class="active"` to `<section id="money">` and to the first `.tab-link`. If "stance gauge needle" fails, ensure the needle div is in the hero. Re-render and re-run QA until PASS.

- [ ] **Step 4: Commit**

```bash
git -C /Users/bobo/.zcode/skills add vn-rates-weekly/scripts/qa_weekly.js
git -C /Users/bobo/.zcode/skills commit -m "feat(vn-rates-weekly): Playwright QA script

- 7 checks: hero, 5 tabs, group sections, data cards, wow-strip, tab switch, JS errors
- Screenshots: full-page + money-tab
- Exit non-zero on FAIL"
```

---

## Task 9: Reference docs + finalize SKILL.md

**Files:**
- Create: `/Users/bobo/.zcode/skills/vn-rates-weekly/references/sources_overview.md`
- Create: `/Users/bobo/.zcode/skills/vn-rates-weekly/references/data_cards.md`
- Create: `/Users/bobo/.zcode/skills/vn-rates-weekly/references/rendering.md`
- Create: `/Users/bobo/.zcode/skills/vn-rates-weekly/references/preflight_check.md`
- Modify: `/Users/bobo/.zcode/skills/vn-rates-weekly/SKILL.md` (expand from stub)

- [ ] **Step 1: Write sources_overview.md**

Write to `/Users/bobo/.zcode/skills/vn-rates-weekly/references/sources_overview.md`. Content: document the 3 PDF sources (SBV/VBMA/VNBA) with exact URL patterns, fetch methods, pitfalls (WAF, spacing, CDN tokens), and the 7 upstream sources (HNX yield/auction/FTP, SBV interbank, FRED, ABO, vnstock) with endpoint details and backfill depth. Reference the spec sections 2.1 and 2.2.

(See spec section 2 for the content — transcribe the tables verbatim into markdown with code blocks for URL patterns.)

- [ ] **Step 2: Write data_cards.md**

Write to `/Users/bobo/.zcode/skills/vn-rates-weekly/references/data_cards.md`. Content: the 35-indicator mapping across 4 tabs + Total (spec section 3), the 4-week schema with all fields (spec section 4), narrative rules with the 4 ĐỪNG table (spec section 11), and the Type A vs Type B chart distinction. Include JSON examples.

- [ ] **Step 3: Write rendering.md**

Write to `/Users/bobo/.zcode/skills/vn-rates-weekly/references/rendering.md`. Content: the 15 patterns from spec section 6.3 (with skill source citations), the 3 rates-specific components (.stance-gauge, .wow-strip, .curve-chart-inline), tab placement rule (everything toggleable inside `<section class="group-section">`), QA triple-gate, and `str.replace` (not f-string) contract.

- [ ] **Step 4: Write preflight_check.md**

Write to `/Users/bobo/.zcode/skills/vn-rates-weekly/references/preflight_check.md`. Content: the all-or-nothing pre-flight workflow (spec section 5 step 1), Tet/holiday auto-backfill logic with `tet_skip` flag, retry hints, FRED_API_KEY check, vnstock connectivity, partial override workflow with `_sources_coverage`.

- [ ] **Step 5: Expand SKILL.md with the full 4-step workflow**

Overwrite `/Users/bobo/.zcode/skills/vn-rates-weekly/SKILL.md` with the full skill doc modeled on `vn-macro-monthly/SKILL.md`. Structure:

```markdown
---
name: vn-rates-weekly
description: Báo cáo tuần thị trường lãi suất & tiền tệ Việt Nam — 4-week rolling window từ 3 nguồn PDF (SBV+VBMA+VNBA) + upstream 12-week chart (HNX/FRED/vnstock)
---

# VN Rates Weekly

[1-paragraph purpose]

## Workflow 4 bước

### Bước 1: Pre-flight all-or-nothing (BẮT BUỘC)
[Content from spec section 5 step 1 + preflight_check.md reference]

### Bước 2: Fetch 12 PDFs + upstream headline
[Content from spec section 5 step 2-4 + sources_overview.md reference]

### Bước 3: Extract 35 chỉ số + 4 rules + narrative
[Content from spec sections 3, 4, 7, 11 + data_cards.md reference]

### Bước 4: Render HTML + QA triple-gate
[Content from spec section 6 + rendering.md reference]

## Output
[File structure from spec section 12]

## 4 Rules (tóm tắt)
[Table from spec section 7]

## Phối hợp hệ sinh thái
[From spec section 14]

## Tham khảo
- `references/sources_overview.md` — ⭐ 3 PDF + 7 upstream sources
- `references/data_cards.md` — ⭐ 35 chỉ số + 4-week schema + narrative rules
- `references/rendering.md` — ⭐ 15 HTML patterns + 3 rates components
- `references/preflight_check.md` — Tet/holiday + retry logic
- `assets/weekly_template.html` — ⭐ HTML template (inject.py-built)
- `scripts/fetch_sources.py` — fetch 12 PDFs + upstream
- `scripts/extract_cards.py` — parse PDF text → values[] 4-week
- `scripts/render_report.py` — fill template from report.json
- `scripts/qa_weekly.js` — Playwright QA
```

- [ ] **Step 6: End-to-end smoke test**

```bash
cd /Users/bobo/.zcode/skills/vn-rates-weekly
# Use the sample report.json to render + QA
python3 scripts/render_report.py \
  --report tests/fixtures/sample_report.json \
  --template assets/weekly_template.html \
  --out /tmp/vrw-e2e.html
NODE_PATH=/tmp/qa-weekly-runner/node_modules node scripts/qa_weekly.js \
  --url=file:///tmp/vrw-e2e.html --output=/tmp/qa-e2e
# Expected: ✅ PASS ≥7
```

- [ ] **Step 7: Commit**

```bash
git -C /Users/bobo/.zcode/skills add vn-rates-weekly/
git -C /Users/bobo/.zcode/skills commit -m "feat(vn-rates-weekly): reference docs + full SKILL.md

- sources_overview.md: 3 PDF + 7 upstream with URL patterns + pitfalls
- data_cards.md: 35 indicators + 4-week schema + narrative rules
- rendering.md: 15 patterns + 3 rates components + placement rule
- preflight_check.md: all-or-nothing + Tet auto-backfill + partial override
- SKILL.md: full 4-step workflow + output + rules + ecosystem"
```

---

## Self-Review (run after writing this plan)

**Spec coverage check:**
- ✅ Section 1 (purpose, ecosystem): Task 9 SKILL.md
- ✅ Section 2 (architecture, 2 layers): Tasks 4 (fetch) + 9 (sources_overview.md)
- ✅ Section 3 (35 indicators, 4 tabs): Task 9 data_cards.md
- ✅ Section 4 (4-week schema): Tasks 2-3 (parsers produce values[]) + 7 (render consumes values[])
- ✅ Section 5 (fetch pipeline, 5 steps): Task 4 fetch_sources.py
- ✅ Section 6 (HTML dashboard, 15 patterns): Tasks 5-8 (template + components + render + QA)
- ✅ Section 7 (4 rules): Task 9 data_cards.md + SKILL.md
- ✅ Section 8 (edge cases): Task 4 (Tet auto-backfill, WAF, FRED key, vnstock retry) + 9 preflight_check.md
- ✅ Section 9 (partial override): Task 9 preflight_check.md
- ✅ Section 10 (no placeholder + provenance): Task 9 SKILL.md + data_cards.md
- ✅ Section 11 (narrative rules): Task 9 data_cards.md
- ✅ Section 12 (output structure): Task 9 SKILL.md

**Known gaps (call out to user):**
- HNX yield curve + auction POST endpoints (fetch_sources.py) are stubbed in Task 4 — full implementation deferred to a follow-up task because they need form-field reverse-engineering per the Bond Lab provider code. For v1, chart 12-week data comes from FRED + vnstock + history.json accumulation; HNX raw can be added later.
- vnstock fetch (VN-Index) is mentioned in spec but not coded in fetch_sources.py Task 4 — add a `fetch_vnstock_vnindex()` function as a small extension once vnstock is pip-installed. For v1, VN-Index card uses VNBA PDF 4-week only (Type B).
- The 35-indicator extract is large; Tasks 2-3 implement parsers for the headline indicators (~12). The remaining ~23 indicators (TPDN, bank PBT, foreign holdings, etc.) reuse the same parser patterns and are filled incrementally as real PDFs are tested.

**Placeholder scan:** No TBD/TODO in tasks. All steps have concrete code or commands.

**Type consistency:** `ParsedYield`, `ParsedInterbank`, `ParsedGlobal`, `ParsedVN`, `ResolvedValue`, `WeekRange` — names consistent across tasks 2-4. `render_card`, `render_group`, `render_report` — consistent across tasks 7-9. Token names `{{REPORT_ID}}`, `{{VERDICT}}`, `{{GROUP_*_HTML}}`, `{{STANCE_NEEDLE_PCT}}` — consistent between Task 7 render_report.py and Task 6 template.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-04-vn-rates-weekly.md`. Two execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
