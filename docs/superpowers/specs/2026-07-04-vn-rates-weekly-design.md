# Skill `vn-rates-weekly` — Báo cáo tuần Thị trường Lãi suất & Tiền tệ

- **Ngày thiết kế**: 2026-07-04
- **Trạng thái**: Approved (sau 5 vòng thảo luận)
- **Loại**: Skill mới (zhi code assistant)
- **Quan hệ**: Độc lập với `vn-macro-monthly` (cadence song song weekly vs monthly)

---

## 1. Mục đích & quan hệ hệ sinh thái

**Mục đích**: Báo cáo tuần (weekly) toàn cảnh thị trường lãi suất & tiền tệ Việt Nam — 4-week rolling window + 12-week headline chart, với verdict + narrative phong phú. Cover scope "rộng toàn cảnh tài chính tiền tệ": LNH, LSTP, TPCP/TPDN, FX, gold/oil/DXY, US rates, VN-Index, bank PBT.

**Quan hệ với skill khác**:
- **Độc lập** với `vn-macro-monthly` — hai cadence song song (weekly + monthly), không đụng chạm code. Có thể overlap nguồn (VBMA, VNBA) nhưng extract theo đúng granularity.
- Không thay thế phần monetary của monthly — monthly vẫn giữ CPI/PMI/IIP/FDI/XNK theo cadence hàng tháng.
- Weekly là mảnh ghép **nhịp tuần** (week-over-week trend, sự kiện NHNN, OMO, đấu thầu TPCP).

**Ràng buộc cốt lõi — Portable**: Skill **KHÔNG** gọi API local `:8001` của Bond Lab (vì đây là skill sẽ công bố). Gọi trực tiếp các upstream source (HNX/SBV/FRED/vnstock) + 3 PDF weekly chính thức.

---

## 2. Kiến trúc — 2 lớp ingestion song song

### Lớp 1 — Snapshot 4 tuần (12 PDFs từ 3 nguồn)

| Nguồn | Role | Scope | Fetch method |
|---|---|---|---|
| **SBV** bulletin ("Diễn biến TT ngoại tệ & LNH tuần") | Chính thức, hẹp | LNH (ON/1W/2W/1M), tỷ giá trung tâm + TM, OMO | `curl` article `sbv.gov.vn/vi/web/sbv_portal/w/...tuan-từ-{D1}-{D2}.{M}.{YYYY}` → regex `<embed src>` → `curl` PDF → `pdftotext -layout` |
| **VBMA** báo cáo tuần ("Bản tin TT trái phiếu tuần") | Chuyên sâu trái phiếu | LSTP (2Y/5Y/10Y), auction TPCP, secondary, TPDN phát hành, foreign holdings | `curl` listing `vbma.org.vn/vi/reports/weekly?page=1` → regex 4 hrefs gần nhất → `curl` PDF (URL-encode spaces) → `pdftotext` |
| **VNBA** bản tin tuần ("Bản tin KT-TC-TT tuần N tháng M") | Rộng nhất, bối cảnh | Global (Fed/ECB/BOJ/PBOC, gold/oil/DXY/US rates), VN macro + monetary + bonds + equities + bank PBT quý | `curl` article `vnba.org.vn/vi/ban-tin-kinh-te-tai-chinh-tien-te-tuan-{N}-thang-{M}-{YYYY}-{id}.htm` → regex CDN PDF `s-vnba-cdn.aicms.vn/...` → `curl` PDF → `pdftotext` |

**4-week rolling window**: mỗi lần chạy = fetch 4 tuần liên tiếp × 3 nguồn = 12 PDFs. Lợi ích:
- Mỗi card có **4 điểm dữ liệu** (4-week trend) + WoW comparison built-in (N vs N-1 trong cùng batch)
- **Chart 4-point có ngay lần đầu** — không đợi accumulate 6+ tuần
- **Narrative có trend** ("LNH ON tăng 3 tuần liên tiếp")
- **Cross-source check** cùng 1 tuần giữa 3 PDF

### Lớp 2 — Upstream headline (12 tuần cho ~12 card Type A)

Gọi trực tiếp upstream (portable, KHÔNG qua :8001):

| Nguồn upstream | Endpoint | Granularity | Backfill | Dùng cho chart |
|---|---|---|---|---|
| HNX yield curve | `POST hnx.vn/ModuleReportBonds/Bond_YieldCurve/SearchAndNextPageYieldCurveData` (form `pDate=dd/mm/YYYY`) | Daily | ✅ từ 2014-01-02 | LSTP 2Y/5Y/10Y 12 tuần |
| HNX auction | `POST hnx.vn/ModuleReportBonds/Bond_DauThau/Bond_KetQua_DauThau` (range search) | Weekly (auction day) | ✅ từ 2013-01-01 | Auction bid/offer 12 tuần |
| HNX FTP PDF | `GET owa.hnx.vn/ftp/THONGKEGIAODICH/{YYYYMMDD}/TP/{YYYYMMDD}_TP_Yield_change_statistics.pdf` | Daily | ✅ từ 2013-01-01 | Yield change 12 tuần |
| SBV interbank | `GET sbv.gov.vn/lãi-suất1` (HTML) | Daily (latest-only) | ❌ accumulate-only | LNH cross-check |
| FRED | `GET api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key=...` | Daily | ✅ decades | US 10Y/2Y, DXY 12 tuần (cần `FRED_API_KEY`) |
| ABO | `GET asianbondsonline.adb.org/vietnam/` (HTML) | Daily (latest-only) | ❌ | Cross-check LSTP |
| **vnstock** (source='VCI') | `Quote.history(symbol='VNINDEX', interval='1W', start, end)` | Weekly | ✅ | VN-Index + thanh khoản + dòng ngoại 12 tuần |

### Cross-check 3 lớp & conflict resolution
- PDF weekly ∩ upstream HNX/SBV ∩ ABO/FRED → resolve conflict
- **Priority monetary hẹp**: SBV > VBMA > VNBA
- **Priority bối cảnh rộng**: VNBA > VBMA
- **Priority LSTP**: HNX raw > VBMA tổng hợp
- Sai số <2%: chấp nhận; 2-5%: flag AMBER + note; >5%: dùng nguồn ưu tiên + signal AMBER

---

## 3. Data cards — 35 chỉ số, 4 nhóm + Tổng hợp

### Tab 1 — Thị trường tiền tệ (9 card)
1. LNH ON (overnight)
2. LNH 1W
3. LNH 1M
4. OMO (cung/rút tiền tuần)
5. LS chính sách (refinancing/discount/OMO rate)
6. LS huy động 12T (avg 4 NHTM)
7. LS cho vay 12T (avg 4 NHTM)
8. Tín dụng (%) YoY
9. M2 YoY

### Tab 2 — Thị trường trái phiếu (10 card)
10. LSTP 2Y
11. LSTP 5Y
12. LSTP 10Y
13. Slope 10Y−2Y (chênh LS)
14. TPCP đấu thầu — bid/offer ratio
15. TPCP secondary trading value
16. TPCP foreign holdings
17. TPDN phát hành (tỷ VND)
18. TPCP kỳ hạn phát hành mới (tenor mix)
19. Yield change tuần (10Y, bp)

### Tab 3 — Ngoại hối & toàn cầu (9 card)
20. Tỷ giá trung tâm USD/VND
21. Tỷ giá TM (BID/ASK avg)
22. Biến độ tỷ giá vs trung tâm (%)
23. DXY (chỉ số USD)
24. US 10Y yield
25. US 2Y yield
26. Gold spot ($/oz)
27. Brent crude ($/bbl)
28. Fed/ECB/BOJ action tuần

### Tab 4 — Thị trường chứng khoán & bối cảnh VN (7 card)
29. VN-Index (close)
30. Thanh khoản HOSE (tỷ VND)
31. Dòng ngoại CK (tỷ VND)
32. CPI YoY (monthly carryover — flag `frequency: "monthly_carryover"`)
33. IIP YoY (monthly carryover)
34. FDI realised YoY (monthly carryover)
35. Bank PBT quý gần nhất (top 4 NHTM)

### Tab 5 — Tổng hợp
- Verdict badge (THUẬN / LƯỢNG / THẮN CHẶT / TRUNG TÍNH)
- Stance gauge (HAWKISH ↔ DOVISH)
- 3-5 risks (color-coded)
- 3-5 catalysts
- 5 key takeaways (#1 ⭐)

### Card types
- **Type A (chart 12 tuần)**: LSTP 2Y/5Y/10Y, LNH ON/1W/1M, FX trung tâm, US 10Y/2Y, DXY, VN-Index — PDF 4-week + upstream 12-week → line chart
- **Type B (PDF-only 4-week)**: TPDN, bank PBT, foreign holdings, Fed/ECB/BOJ action — sparkline 4-week

---

## 4. Schema — 4-week array (mở rộng từ vn-macro-monthly 15-field Data Card)

```json
{
  "gov_10y_yield": {
    "name_vi": "Lợi suất trái phiếu CP 10 năm",
    "definition": "Yield TPCP 10Y benchmark, đóng cửa thứ 6 tuần N",
    "values": [
      {"week": "2026-W23", "value": 3.70, "wow_pct": null},
      {"week": "2026-W24", "value": 3.75, "wow_pct": 1.35},
      {"week": "2026-W25", "value": 3.83, "wow_pct": 2.13},
      {"week": "2026-W26", "value": 3.85, "wow_pct": 0.52}
    ],
    "value_unit": "%",
    "trend_4w": "+4.1%",
    "streak": {"direction": "up", "weeks": 4},
    "comparisons": {"prev_month": 3.55},
    "source_primary": "VBMA",
    "source_check": "HNX yield curve",
    "signal": "RED",
    "narrative": "LSTP 10Y +15bp trong 4 tuần, kéo dài chuỗi tăng — cùng lúc LNH ON giữ thấp cho thấy NHNN vẫn bơm tiền dồi dào trong khi giá tiền dài hạn đã đắt lên.",
    "has_chart": true,
    "chart_source": "hnx_yield_curve"
  }
}
```

**Trường mới cho weekly cadence**:
- `values[]` — mảng 4 điểm (thay `value` đơn của monthly)
- `trend_4w` — % biến động W-3 → W
- `streak` — chuỗi tăng/giảm bao nhiêu tuần
- `wow_pct` — % thay đổi tuần trước (thay `mom_pct` của monthly)
- `chart_source` — tên upstream cho modal chart (`hnx_yield_curve`, `fred_global`, `sbv_interbank`, `vnstock`, `null`)

**Signal semantics (rates-specific)**:
- `GREEN` = dovish/thuận (LNH↓, OMO bơm, LSTP↓)
- `RED` = hawkish/thắt chặt (LNH↑, OMO hút, LSTP↑)
- `AMBER` / `NEUTRAL` = không đổi / không rõ

**Verdict badge mapping**:
- THUẬN (dovish) — green tint
- LƯỢNG (mild dovish) — cyan tint
- TRUNG TÍNH — amber tint
- THẮN CHẶT (hawkish) — red tint

---

## 5. Fetch pipeline

### Bước 1 — Pre-flight all-or-nothing (4 tuần × 3 nguồn = 12 PDFs)
1. Detect tuần N (thứ 2 gần nhất đã kết thúc — tức thứ 6 tuần trước)
2. Enumerate 4 tuần: `[N-3, N-2, N-1, N]`
3. Tet/holiday skip check → **auto-backfill N-(x+1)** nếu tuần x là lễ, flag `tet_skip: true` trong `report.json`
4. HEAD check 12 PDFs (3 nguồn × 4 tuần) tồn tại
5. `FRED_API_KEY` check (nếu muốn chart Type A cho US rates/DXY)
6. vnstock connectivity check (cho VN-Index chart)
7. 12/12 + deps OK? → fetch | thiếu? → **DỪNG + đề xuất tuần thay thế** (máy sạch, không tạo thư mục)

### Bước 2 — Fetch 12 PDFs (song song 3 nguồn)

**SBV**:
```bash
for week in W-3 W-2 W-1 W:
    curl sbv.gov.vn/vi/web/sbv_portal/w/...tuan-từ-{D1}-{D2}.{M}.{YYYY}
    # → regex <embed src="/documents/20117/0/{D1}-{D2}.{M}.{YYYY}.pdf/{uuid}?t=...">
    # → curl PDF (UUID bắt buộc, không thể construct)
    # → pdftotext -layout
    # Header: Referer + Accept-Language: vi, sleep 3s tránh WAF
```

**VBMA**:
```bash
curl vbma.org.vn/vi/reports/weekly?page=1
# → regex /storage/reports/.*\.pdf (12 hrefs gần nhất)
# → chọn 4 hrefs cho tuần N-3..N
# Lưu ý: spacing non-deterministic ("TTTP" / "TTTP1" / "TTTP2" / double space)
#       → LUÔN scrape href chính xác, KHÔNG construct URL
# → curl PDF (URL-encode spaces %20)
# → pdftotext
```

**VNBA**:
```bash
# 4 bài viết tuần gần nhất qua hashtag archive
for n in 1 2 3 4 5:
    curl vnba.org.vn/vi/hashtag/kinh-te-tai-chinh-tien-te-tuan-{n}-{hashtagId}
# → regex ban-tin-kinh-te-tai-chinh-tien-te-tuan-{N}-thang-{M}-{YYYY}-{id}.htm
# → chọn 4 bài cho tuần N-3..N
# → curl article → regex s-vnba-cdn.aicms.vn/.*\.pdf
# → curl PDF (md5/expires token hiện không enforce nhưng re-fetch defensive)
# → pdftotext
```

Cache vào `sources_cache/{source}_{week}.pdf` + `.txt`.

### Bước 3 — Extract + populate `values[]` 4-week array
Mỗi nguồn PDF parse format riêng:
- **VBMA**: bảng yield 2Y/5Y/10Y, auction table, secondary table → regex số cuối tuần
- **VNBA**: 22 trang, parse theo tiêu đề section (Part I global / Part II VN monetary / Part III banks)
- **SBV**: bảng LNH ON/1W/2W/1M + bảng tỷ giá + OMO summary

Cross-source resolve: nếu VBMA và SBV cùng báo LNH ON cho tuần N mà lệch >0.05% → flag + dùng SBV (priority).

### Bước 4 — Fetch upstream headline (12 tuần cho ~12 card Type A)
```python
# HNX yield curve 12 thứ 6 gần nhất
for date in [12 closest Fridays]:
    POST hnx.vn/.../SearchAndNextPageYieldCurveData (pDate=date)

# HNX auction range
POST hnx.vn/.../Bond_KetQua_DauThau (range search 12 tuần)

# FRED US10Y/2Y/DXY 12 tuần
GET api.stlouisfed.org/fred/series/observations?series_id=DGS10&observation_start=...

# SBV interbank (accumulate-only)
# → nếu history.json đã có → dùng; nếu chưa → chỉ dùng PDF 4-week

# vnstock VN-Index 12 tuần
from vnstock.api.quote import Quote
q = Quote(symbol='VNINDEX', source='VCI')
q.history(start=..., end=..., interval='1W')
```

### Bước 5 — Append history.json + render HTML
Mỗi tuần chạy → append điểm mới vào `history.json`. Sau 3+ lần chạy = 7+ điểm → chart headline tự dài ra.

---

## 6. HTML dashboard — fork + học từ mọi skill

### 6.1. Base template
**Fork `vn-macro-monthly/assets/report_template.html`** + **migrate sang `inject.py`**:
- Thay CSS viết tay (dòng 11-318) bằng `{{VIZ_CSS}}`
- Thêm `{{VIZ_JS}}`, bọc Chart.js code vào `viz.chart()` registry nơi có thể
- Thêm path vào `/Users/bobo/.zcode/skills/_viz-shared/inject.py:29-35` (TEMPLATE_PATHS)

Đây là template base đúng nhất vì đã có sẵn: tabs (click-to-switch), `data-card` 15-field, `mini-table` yield curve, `highlight-box` pos/neg, `rc-grid` risks/catalysts, `kt-list`, modal chart với `MIN_POINTS_FOR_CHART` gate.

### 6.2. Design system `_viz-shared/` (chia sẻ với mọi VN skill)
Toàn bộ VN financial skill chia sẻ 1 design system tại `/Users/bobo/.zcode/skills/_viz-shared/`:
- `tokens.css` — design tokens + 3 theme (Fintech default / Bloomberg / Corporate)
- `components.css` (30KB) — tất cả component class
- `viz.js` — `viz.chart()` registry + scrollspy nav + candlestick renderer
- `inject.py` — chèn CSS/JS vào template → single-file output (no runtime deps)

**Design tokens (giữ cho cross-skill consistency)**:
- `--purple:#a855f7`, `--pink:#ec4899`, `--cyan:#06b6d4` — accent + chart
- `--green:#10d98a` = dovish/thuận, `--red:#ff4d6d` = hawkish/thắt chặt, `--amber:#fbbf24` = trung tính
- Font: Inter + JetBrains Mono (`font-variant-numeric: tabular-nums` cho số)
- `--radius-card:24px`, `--radius-pill:999px`
- Theme Corporate cho PDF export

### 6.3. 15 pattern áp dụng từ các skill

| # | Pattern (nguồn skill) | Áp dụng trong vn-rates-weekly |
|---|---|---|
| 1 | `inject.py` + `{{VIZ_CSS}}`/`{{VIZ_JS}}` (`_viz-shared`) | Kế thừa design system, tránh copy tay `:root` block (lỗi của vn-macro-monthly chưa migrate) |
| 2 | `.nav-tabs` click-to-switch + placement rule (`vn-macro-monthly`) | 5 tab; mọi component toggleable PHẢI nằm trong `<section class="group-section">`. Hero/nav/footer ngoài |
| 3 | `data-card` 15-field + `dc-meta` WoW/MoM/YoY (`vn-macro-monthly`) | Mỗi card có `values[]` 4-week + `wow_pct` + narrative "kể chuyện số liệu" |
| 4 | `mini-table` yield curve/tenor (`vn-macro-monthly`) | Bảng LSTP (1Y/3Y/5Y/10Y/30Y) + LNH (ON/1W/1M/3M/6M) — cột "Kỳ hạn \| W26 \| W25 \| WoW(đcb) \| MoM(đcb)" |
| 5 | `highlight-box` pos/neg (`vn-macro-monthly`) | 🔴 Tín hiệu thắt chặt (LNH↑, OMO hút) vs 🟢 Tín hiệu thuận (LNH↓, OMO bơm) ở đầu mỗi tab |
| 6 | `.kpi` strip + `.flag-dot` (`vn-macro-monthly`) | Hero 4 KPI: LSTP 10Y \| LNH ON \| Tỷ giá \| VN-Index — mỗi ô có dot màu signal |
| 7 | `.rc-grid` risks/catalysts + `.rc-level` (`vn-macro-monthly`) | Tab Tổng hợp: Rủi ro tuần tới (Fed, áp lực tỷ giá) vs Động lực (bơm tiền, tín dụng) |
| 8 | `.kt-list` numbered + ★ trên #1 (`vn-macro-monthly`) | 3-5 key takeaways tuần |
| 9 | `val-grid` 5-scenario (`vn-research-dashboard`) | "Kịch bản lãi suất" — 5 cột (Cắt giảm / Giữ nguyên / Tăng nhẹ / Tăng vừa / Tăng mạnh), 1 cột `.base` làm kịch bản trung tâm |
| 10 | `.signal-grid` 6-cell (`vn-technical-analysis`) | 6 tín hiệu stance hawkish/dovish: LNH / slope curve / real rate / credit growth / FX pressure / CSD balance |
| 11 | `.exec-summary` + 4 `exec-hl` boxes (`equity-research-vn`) | Above-the-fold: 1 câu headline + 4 ô pos/neg/neu |
| 12 | Sentiment meter + per-category bars (`vn-news-digest`) | "Stance meter" — điểm tổng hợp + thanh ngang mỗi kênh (LNH/trái phiếu/FX/tín dụng). Phát hiện divergence = insight giá trị nhất tuần |
| 13 | 5-part event card + "Vì sao quan trọng" (`vn-news-digest`) | Sự kiện tuần (quyết định NHNN, OMO, đấu thầu TPCP): category tag + ngày/nguồn + headline + metric box + hộp lý giải truyền động + stance pill |
| 14 | Vertical timeline `tl-item pos\|neg` (`vn-news-digest`) | Timeline Mon→Fri sự kiện tuần với chấm màu |
| 15 | Coverage-warn banner + `_sources_coverage` (`vn-macro-monthly`) | Partial run: 1 dòng vàng ở hero "X/3 nguồn", field JSON ghi rõ |

### 6.4. Component rates-specific (mới, chưa có template nào)
- `.stance-gauge` — gauge lớn gradient "HAWKISH ↔ DOVISH" ở hero (adapt từ `.gauge-wrap` của dashboard)
- `.curve-chart-inline` — yield curve chart luôn hiển thị (không modal), theo tenor (vn-macro-monthly đã có `#yieldCurve` canvas cố định)
- `.wow-strip` — thanh 4 ô (W-3, W-2, W-1, W) + trend arrow + streak badge (mới — cho 4-week window)

### 6.5. Cấu trúc dashboard cuối cùng
```
┌─────────────────────────────────────────────────────────────┐
│ HERO: "Thị trường Lãi suất & Tiền tệ — W26/2026"             │
│   verdict badge (THUẬN/LƯỢNG/THẮN CHẶT) + stance gauge       │
│   KPI strip: LSTP 10Y | LNH ON | Tỷ giá TM | VN-Index         │
│   [coverage-warn nếu partial]                                 │
├─────────────────────────────────────────────────────────────┤
│ EXEC-SUMMARY: 1 câu headline + 4 exec-hl boxes              │
├─────────────────────────────────────────────────────────────┤
│ NAV-TABS: [Tiền tệ] [Trái phiếu] [Ngoại hối&TG] [CK&VN] [📊 Tổng hợp] │
├─────────────────────────────────────────────────────────────┤
│ Tab active (vd Tiền tệ):                                     │
│   🔴 THẮN CHẶT highlights  |  🟢 THUẬN highlights            │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│   │ data-card    │ │ data-card    │ │ data-card    │         │
│   │ value+WoW    │ │ value+WoW    │ │ value+WoW    │         │
│   │ ▁▂▃▄ 4-wk    │ │ ▁▂▃▄ 4-wk    │ │ ▁▂▃▄ 4-wk    │         │
│   │ narrative    │ │ narrative    │ │ narrative    │         │
│   │ [📊 12w]     │ │ [📊 12w]     │ │              │         │
│   └──────────────┘ └──────────────┘ └──────────────┘         │
│   mini-table yield curve (always-visible)                    │
│   signal-grid 6-cell stance (tab Tiền tệ)                    │
├─────────────────────────────────────────────────────────────┤
│ Tab Tổng hợp: stance meter + rc-grid + kt-list + timeline    │
├─────────────────────────────────────────────────────────────┤
│ FOOTER: cutoff W26/2026 · 3 nguồn · _data_provenance         │
└─────────────────────────────────────────────────────────────┘
```

### 6.6. QA triple-gate (kế thừa từ mọi skill)
1. **JS syntax**: extract last `<script>` → `node --check`
2. **Token-grep**: `grep -oE "\{\{[A-Z_0-9]+\}\}"` phải rỗng
3. **Playwright**: `scripts/qa_weekly.js` — canvas rendered + console errors + tab switching + modal open + screenshots

---

## 7. 4 Rules (mở rộng từ vn-macro-monthly)

| Rule | Nội dung |
|---|---|
| **1. Time consistency** | `data_cutoff` = thứ 6 tuần N. PDF lấy tuần kết thúc ≤ cutoff. VNBA bỏ "tuần 1 tháng M+1" (lọc theo cutoff) |
| **2. Frequency** | Chỉ weekly (WoW). Card monthly (CPI/IIP/FDI) đánh dấu `frequency: "monthly_carryover"`, lấy từ tháng gần nhất, KHÔNG tạo điểm mới |
| **3. Conflict resolution** | Priority: SBV > VBMA > VNBA (monetary hẹp); VNBA > VBMA (bối cảnh rộng); HNX raw > VBMA tổng hợp (LSTP). Sai số <2% OK, 2-5% flag, >5% dùng priority |
| **4. Unit convention** | 8 suffix chuẩn (`_pct`, `_b_vnd`, `_vnd`, `_usd_b`, `_bps`, `_index`, `_ratio`, `_count`) + thêm `_wow_pct`, `_4w_trend_pct` |

---

## 8. Edge cases

| Trường hợp | Xử lý |
|---|---|
| **Tuần Tết / nghỉ lễ** (SBV skip tuần đó) | Auto-backfill N-(x+1), flag `tet_skip: true` trong `report.json`. Báo cáo luôn đủ 4 điểm |
| **VNBA monthly variant xen** (tuần 1 tháng M+1) | Lọc theo `data_cutoff`, chỉ giữ weekly |
| **VBMA space trong filename** (`TTTP` / `TTTP1` / `TTTP2` / double space) | LUÔN scrape href chính xác từ listing, KHÔNG construct URL |
| **SBV WAF "Request Rejected"** (F5 BIG-IP) | Add `Referer: sbv.gov.vn/vi/web/sbv_portal/thông-tin-về-hoạt-động-ngân-hàng-trong-tuần` + `Accept-Language: vi`, sleep 3s giữa requests |
| **FRED chưa set key** | Skip upstream US rates, chỉ dùng PDF 4-week + history. Flag `upstream_skip: "no_fred_key"` |
| **vnstock rate limit** | Đổi `source='VCI'` → `'KBS'` → `'DNSE'`, retry 3 lần |
| **Card chỉ primary, no check** | Flag `source_check: null`, warn trong footer |
| **Conflict >5% giữa các nguồn** | Signal `"AMBER"`, note giải thích conflict |
| **history.json chưa đủ điểm** (lần chạy đầu) | Chart Type A dùng PDF 4-week + upstream 12-week (không cần history). Modal chart gate `MIN_POINTS_FOR_CHART=8` cho history-only fallback |

---

## 9. Partial override (giống vn-macro-monthly)

User override ("dùng nguồn có sẵn" / "bỏ qua pre-flight") → chạy với nguồn có sẵn:
1. Tạo thư mục + cache NHƯNG chỉ với nguồn có sẵn
2. Áp dụng Nguyên tắc KHÔNG placeholder — KHÔNG tạo card cho chỉ số thiếu nguồn
3. Thêm 1 dòng `coverage-warn` ở hero ghi rõ "X/3 nguồn"
4. Bỏ qua news enrichment nếu partial < 2/3 nguồn
5. Trong `report.json`, thêm field `_sources_coverage` ghi nhận override

```json
"_sources_coverage": {
  "available": ["SBV", "VBMA"],
  "missing": ["VNBA"],
  "user_override": true,
  "retry_hint": "Thử lại sau <date> khi VNBA publish"
}
```

---

## 10. Nguyên tắc KHÔNG placeholder & Data Provenance (kế thừa vn-macro-monthly)

### Nguyên tắc KHÔNG placeholder
Chỉ đưa vào báo cáo những gì CÓ DỮ LIỆU THẬT. KHÔNG tạo khung/card/section "THIẾU" cho phần chưa có data. Khi nguồn bổ sung publish → chạy lại skill, card tự xuất hiện.

### Data Provenance (BẮT BUỘC)
Mọi số trong `report.json` phải trace được tới 1 file cụ thể trong `sources_cache/`. Thêm section `_data_provenance`:
```json
"_data_provenance": {
  "_rule": "Mọi số trong report.json phải trace được tới 1 file cụ thể trong sources_cache/",
  "sources_files": {
    "sbv_W26.txt": ["LNH ON/1W/1M", "tỷ giá trung tâm", "OMO"],
    "vbma_W26.txt": ["LSTP 2Y/5Y/10Y", "auction", "secondary", "TPDN"],
    "vnba_W26.txt": ["global macro", "VN-Index", "bank PBT", "gold/oil/DXY"]
  }
}
```

---

## 11. Narrative rules (kế thừa vn-macro-monthly)

Đóng vai "người kể chuyện số liệu, KHÔNG phải người cho ý kiến":
| ❌ Tránh | ✅ Làm |
|---|---|
| "NHNN sẽ phải siết tiền tệ" | "LNH ON tăng 50bp tuần này, kéo dài chuỗi 3 tuần tăng — cùng lúc OMO chuyển từ bơm sang hút 5 nghìn tỷ" |
| "Tôi dự báo tuần sau khó khăn" | "LSTP 10Y +15bp trong 4 tuần, trong khi LNH ON vẫn giữ thấp — hai số này cùng kể câu chuyện giá tiền dài hạn đắt lên" |

**4 ĐỪNG**:
1. ĐỪNG dùng "tôi nghĩ/có thể/dự báo" → dùng "số liệu cho thấy", "cùng lúc"
2. ĐỪNG khuyên mua/bán/khuyến nghị → chỉ kể diễn biến số
3. ĐỪNG dùng tính từ cảm tính ("đáng lo", "tốt") → dùng số so sánh ("+50bp", "3 tuần liên tiếp")
4. ĐỪNG kết luận định hướng → mở câu hỏi cho người đọc

---

## 12. Output structure

```
{project}/vn-rates-weekly/
├── history.json                    # append mỗi tuần, 6+ tuần → chart dài
├── 2026/
│   ├── W23/
│   │   ├── report.json             # data structured (nguồn dữ liệu chuẩn)
│   │   ├── report.html             # dashboard cuối
│   │   └── sources_cache/
│   │       ├── sbv_W23.pdf
│   │       ├── sbv_W23.txt
│   │       ├── vbma_W23.pdf
│   │       ├── vbma_W23.txt
│   │       ├── vnba_W23.pdf
│   │       └── vnba_W23.txt
│   ├── W24/ ... W25/ ... W26/
```

### `report.json` schema (tóm tắt)
```json
{
  "report_id": "vn-rates-2026-W26",
  "period": {"week": 26, "year": 2026, "data_cutoff": "2026-06-26", "weeks_covered": ["W23","W24","W25","W26"]},
  "verdict": "THẮN CHẶT NHẸ",
  "verdict_reason": "...",
  "stance_score": -2,
  "group1_money_market": { /* 9 cards */ },
  "group2_bonds": { /* 10 cards */ },
  "group3_fx_global": { /* 9 cards */ },
  "group4_equities_vn": { /* 7 cards */ },
  "stance_signals": [ /* 6 signals */ ],
  "weekly_events": [ /* timeline Mon-Fri */ ],
  "rate_scenarios": [ /* 5 scenarios val-grid */ ],
  "risks": [ /* 3-5 items */ ],
  "catalysts": [ /* 3-5 items */ ],
  "key_takeaways": [ /* 5 bullets, #1 ⭐ */ ],
  "_data_provenance": { /* file mapping */ },
  "_sources_coverage": { /* nếu partial */ }
}
```

### `history.json` schema
```json
{
  "series": {
    "gov_10y_yield": [{"week": "2026-W26", "value": 3.85}],
    "interbank_on": [{"week": "2026-W26", "value": 1.20}]
  }
}
```

**Rules history**:
- Mỗi lần skill chạy thành công → append entry
- **Re-run tuần cũ → ghi đè** (1 tuần = 1 giá trị)
- **Bắt đầu trống** (KHÔNG seed data cũ)

---

## 13. Plan triển khai

1. **Skill scaffold**: tạo `/Users/bobo/.zcode/skills/vn-rates-weekly/` với `SKILL.md` + `references/` + `assets/` + `scripts/`
2. **Fetch module**: viết `scripts/fetch_pdfs.py` (3 nguồn × 4 tuần) + `scripts/fetch_upstream.py` (HNX/FRED/SBV/vnstock)
3. **Extract module**: viết `scripts/extract_cards.py` parse PDF text → `values[]` 4-week + cross-check
4. **Template migration**: copy `vn-macro-monthly/assets/report_template.html` → `weekly_template.html`, inject `{{VIZ_CSS}}`/`{{VIZ_JS}}`, thêm path vào `inject.py:29-35`
5. **Component rates-specific**: thêm `.stance-gauge`, `.curve-chart-inline`, `.wow-strip`, `.signal-grid` stance variant
6. **Render module**: viết `scripts/render.py` fill template từ `report.json`
7. **QA**: viết `scripts/qa_weekly.js` (Playwright) + integrate `node --check` + token-grep
8. **SKILL.md workflow**: 4 bước (pre-flight → fetch 12 PDFs + upstream → extract + 4 rules → render + QA)
9. **References**: viết `sources_overview.md`, `data_cards.md` (35 chỉ số mapping + narrative rules), `rendering.md` (15 pattern + component mới), `preflight_check.md` (tet/holiday + retry logic)

### Các file sẽ tạo/sửa
- **Tạo**: `/Users/bobo/.zcode/skills/vn-rates-weekly/SKILL.md`
- **Tạo**: `/Users/bobo/.zcode/skills/vn-rates-weekly/references/{sources_overview,data_cards,rendering,preflight_check}.md`
- **Tạo**: `/Users/bobo/.zcode/skills/vn-rates-weekly/assets/weekly_template.html`
- **Tạo**: `/Users/bobo/.zcode/skills/vn-rates-weekly/scripts/{fetch_pdfs,fetch_upstream,extract_cards,render}.py`
- **Tạo**: `/Users/bobo/.zcode/skills/vn-rates-weekly/scripts/qa_weekly.js`
- **Sửa**: `/Users/bobo/.zcode/skills/_viz-shared/inject.py` (thêm path `weekly_template.html` vào TEMPLATE_PATHS dòng 29-35)

---

## 14. Phối hợp hệ sinh thái skill VN

```
vn-financial-data-collector  (DN cấp — equity data)
        ↓
vn-fundamental-analysis / vn-valuation-engine / vn-technical-analysis
vn-news-digest              (thời sự 30 ngày cho cổ phiếu)
vn-macro-monthly            (VĨ MÔ monthly — CPI/PMI/IIP/FDI/XNK)
⭐ vn-rates-weekly ⭐         (LÃI SUẤT & TIỀN TỆ weekly)  ← SKILL NÀY
        ↓
vn-research-dashboard       (render HTML equity research — share _viz-shared/)
```

`vn-rates-weekly` = mảnh ghép **nhịp tuần thị trường tiền tệ**. LNH/LSTP/OMO/FX là input cho mọi quyết định fixed-income và định hướng chính sách tiền tệ.

---

## Quyết định cuối (chốt)

- **Tên skill**: `vn-rates-weekly` (user đã dùng tên này xuyên suốt thảo luận, không đổi)
- **Themes**: giữ cả 3 (Fintech default / Bloomberg / Corporate) vì `_viz-shared/` đã có sẵn → không tốn công thêm, chỉ việc kế thừa. Corporate theme cho PDF export khi user muốn in báo cáo tuần.
