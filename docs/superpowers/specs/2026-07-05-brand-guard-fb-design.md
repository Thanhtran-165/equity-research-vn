# Spec: Brand Guard FB — ZCode skill tự dò fanpage Facebook giả mạo

- **Ngày:** 2026-07-05
- **Tác giả:** Thanhtran-165 (brainstormed with ZCode)
- **Trạng thái:** Chờ user duyệt
- **Loại:** ZCode skill (gọi theo yêu cầu, không chạy định kỳ)

## 1. Mục tiêu & phạm vi

### Vấn đề
Fanpage chính chủ của user liên tục bị kẻ gian lập trang giả mạo (cùng tên, cùng avatar, cùng ảnh bìa) để lừa đảo khách hàng, làm tổn hại uy tín thương hiệu.

### Mục tiêu
Xây dựng một **skill ZCode** khi được gọi sẽ tự:
1. Tìm các fanpage Facebook nghi ngờ giả mạo thương hiệu của user.
2. Chấm điểm rủi ro theo nhiều tín hiệu (tên, avatar, ảnh bìa, độ mới).
3. Trả về bảng markdown trong ZCode để user review.
4. Sinh mẫu đơn khiếu nại (Meta IP infringement + SHTT Việt Nam) cho các trang có rủi ro cao.

### Out of scope (YAGNI)
- Không scraping cần đăng nhập, không tương tác với trang nghi vấn.
- Không tự động takedown (chỉ sinh bằng chứng để user tự gửi).
- Không track lịch sử takedown (scope v1).
- Không giám sát đa nền tảng (Instagram, TikTok, web — để sau).
- Không chạy cron tự động — skill chỉ chạy khi user gọi.

### Tiêu chí thành công
- Skill gọi được qua `Skill` tool trong ZCode.
- Phát hiện ≥ 80% các trang có cùng tên + avatar chính chủ (so với dataset test 10 trang tự tạo).
- Output markdown có thể copy/forward ngay cho pháp chế hoặc đội marketing.
- Config tách biệt, user thay đổi thương hiệu mà không cần sửa code.

## 2. Kiến trúc tổng thể

```
brand-guard-fb/                       # root skill, đặt tại /Users/bobo/.zcode/skills/brand-guard-fb/
├── SKILL.md                          # ZCode skill manifest (YAML frontmatter + hướng dẫn dùng)
├── config/
│   ├── brands.yaml                   # user điền brand info
│   └── avatars/                      # avatar/cover chính chủ (gitignored)
│       ├── fptshop_avatar.png
│       └── fptshop_cover.png
├── src/
│   ├── __init__.py
│   ├── cli.py                        # entry point: parse args, orchestrate pipeline
│   ├── search.py                     # query DuckDuckGo/Bing HTML, parse link
│   ├── page_meta.py                  # fetch OG metadata + HTML heuristic
│   ├── scoring.py                    # fuzzy name + pHash + heuristics
│   ├── report.py                     # render markdown table
│   └── takedown_template.py          # render mẫu đơn khiếu nại
├── templates/
│   ├── meta_ip_report.md             # mẫu Meta IP infringement (EN)
│   └── shtt_complaint_vi.md          # mẫu đơn SHTT Việt Nam (Nghị định 65/2023)
├── .cache/                           # gitignored, TTL 24h
│   ├── page_meta/                    # cache HTML/OG metadata theo URL hash
│   └── complaints/                   # mẫu đơn đã sinh theo ngày
├── requirements.txt                  # rapidfuzz, imagehash, requests, beautifulsoup4, pyyaml, pillow
├── .gitignore                        # .cache/, config/avatars/, __pycache__/
└── tests/
    ├── test_scoring.py               # unit test fuzzy + pHash logic
    ├── test_search.py                # unit test regex parse search results
    └── fixtures/                     # HTML mẫu để test
```

### Pipeline (mỗi lần gọi skill)

1. **Load config** — đọc `config/brands.yaml`, lấy list brands cần giám sát.
2. **Search** — với mỗi brand, sinh 5-10 dork queries, gọi DuckDuckGo HTML endpoint (fallback Bing HTML), sleep 2-5s giữa queries.
3. **Filter URLs** — regex chỉ giữ URL dạng `facebook.com/<page-slug>`; loại `/profile.php`, `/groups/`, `/posts/`, `/photos/`, `/videos/`, `/reel/`.
4. **Fetch metadata** — với mỗi URL page: kiểm tra `.cache/page_meta/<urlhash>.json`, nếu stale (>24h) thì GET trang, parse OG metadata + heuristics HTML, lưu vào cache.
5. **Score** — áp dụng 5 tín hiệu (xem §3) để tính điểm 0-100.
6. **Render** — output markdown trong ZCode, group theo rủi ro (🔴/🟡/🟢).
7. **Takedown templates** — với top N trang rủi ro cao, sinh file đơn khiếu nại tại `.cache/complaints/YYYY-MM-DD-<brand_id>.md`, link tới file trong output.

### Lớp cách ly
- `search.py` — chỉ lo nguồn dữ liệu (đổi search engine không ảnh hưởng phần sau).
- `page_meta.py` — chỉ lo fetch + parse metadata (cache transparent với caller).
- `scoring.py` — chỉ lo logic chấm điểm (pure function, test độc lập).
- `report.py` + `takedown_template.py` — chỉ lo render (đổi format không động tới logic).

## 3. Chi tiết kỹ thuật

### 3.1. Search engine dorks (`src/search.py`)

**Endpoint chính:** `https://html.duckduckgo.com/html/?q=<query>` (HTML thuần, parse link bằng BeautifulSoup).
**Fallback:** Bing HTML (`https://www.bing.com/search?q=<query>`).
**Lý do chọn DDG:** không cần API key, không rate limit nặng như Google, không chặn UA thông thường.

**Dork patterns** (sinh tự động từ brand info):
```
site:facebook.com "<display_name>" -site:facebook.com/<official_username>
"<display_name>" site:facebook.com inurl:"<slug>"
"<alias_2>" site:facebook.com "liên hệ" OR "hotline"
"<display_name>" site:facebook.com "2025" OR "2026"
"<display_name>" site:facebook.com "chính sách" OR "khuyến mãi"
```

**Lọc kết quả** (regex):
```
^https?://(?:www\.)?facebook\.com/([\w.\-]+)/?(?:posts|photos|videos|reel)?/?$
```
Loại trừ: `/profile.php`, `/groups/`, `/people/`, `/pages/`, slug chính chủ, slug có chứ keyword `official` và verified.

**Rate limiting:**
- Sleep random 2-5s giữa các query.
- Max 10 query/brand/lần chạy.
- Xoay 5 User-Agent desktop khác nhau.
- HTTP timeout 15s, retry 2 lần với backoff.

### 3.2. Fetch metadata (`src/page_meta.py`)

Với mỗi URL page (đã qua cache check), GET HTML công khai (không đăng nhập), parse:
- `<meta property="og:title">` → tên hiển thị
- `<meta property="og:image">` → URL avatar/cover → download → pHash
- `<meta property="og:description">` → mô tả trang
- `<meta name="description">` → fallback
- Heuristics trên HTML:
  - `"Verified Page"` badge hoặc `aria-label="Verified"` → `is_verified=True`
  - Text `"Page created"` hoặc `"Created on"` → extract năm tạo
  - Count `data-utime` gần đây ( Posts timestamp ) → ước lượng hoạt động

**Cache:** Lưu JSON tại `.cache/page_meta/<sha1(url)>.json` với field `fetched_at`. TTL 24h — request lại nếu stale.

**Robots.txt:** Tôn trọng `robots.txt` của Facebook. Trang công khai được index bởi search engine → OK để fetch HEAD/GET 1 lần. **Không** giữ session, không follow links sâu.

### 3.3. Scoring (`src/scoring.py`)

Pure function `score_page(page_meta, brand_config) -> ScoreResult`:

| Tín hiệu | Trọng số | Logic |
|---|---|---|
| **Tên giống** | 35 | `max(rapidfuzz.token_set_ratio(page_title, alias) for alias in brand.aliases)`. ≥ 90 → 35đ, 80-89 → 22đ, < 80 → 0đ. **Trừ 35đ** nếu page_url == `official_page_url` hoặc page_title trùng alias CHÍNH CHỦ và page có verified badge (vì đó là chính chủ). |
| **Avatar pHash** | 25 | `imagehash.phash(download(og_image))` so với `imagehash.phash(brand.avatar_path)`. Hamming distance ≤ 4 → 25đ, 5-8 → 17đ, 9-12 → 4đ, > 12 → 0đ. |
| **Cover photo pHash** | 20 | Tương tự avatar, so với `brand.cover_path`. Cùng ngưỡng, trọng số thấp hơn (cover dễ change). |
| **Trang mới / hoạt động** | 12 | `+12` nếu `page_created_year` ∈ {2025, 2026}; `+3` nếu phát hiện ≥ 3 bài viết trong 30 ngày gần nhất. **Override về 0** nếu `is_verified=True` (verified = chính chủ gần như chắc chắn). |
| **Username/URL** | 8 | `rapidfuzz.token_set_ratio(slug, official_slug)`. ≥ 85 → 8đ, 70-84 → 5đ, < 70 → 0đ. |

**Tổng:** 0-100, có thể âm nếu verified override (clamp về 0).

**Phân loại:**
- 🔴 **Cao (≥ 70):** nhiều khả năng giả mạo → tự sinh mẫu đơn khiếu nại.
- 🟡 **Trung (40-69):** cần review tay.
- 🟢 **Thấp (< 40):** bỏ qua trong output rút gọn (flag `--verbose` để xem).

**Config overrides:** Mỗi brand có thể override ngưỡng qua `scoring_overrides.name_threshold`, `avatar_distance_thresholds`, …

### 3.4. Mẫu đơn khiếu nại (`templates/` + `src/takedown_template.py`)

**A. `meta_ip_report.md`** — Meta IP infringement form (EN, form chính thức của Facebook)
- Placeholders tự điền: `{brand.display_name}`, `{brand.trademark.vn_number}`, `{brand.official_page_url}`, list `{page.url}`, `{page.title}`, screenshot paths.
- Statement chuẩn: *"I have a good faith belief that use of the trademarks described above in the infringing materials is not authorized by the trademark owner, its agent, or the law."*
- Kèm link submit: `https://www.facebook.com/help/contact/638124867914415`
- Sworn statement clause đã có sẵn trong template.

**B. `shtt_complaint_vi.md`** — Đơn khiếu nại Cục SHTT Việt Nam (theo mẫu số 3 Nghị định 65/2023/NĐ-CP)
- Placeholders: tổ chức/cá nhân bị xâm phạm, tên nhãn hiệu + số đăng ký, mô tả hàng hóa/dịch vụ mang nhãn hiệu, hành vi xâm phạm (sử dụng nhãn hiệu không được phép trên Facebook page), bằng chứng (URL + screenshot + thời gian truy cập), chứng từ quyền sở hữu (Giấy chứng nhận đăng ký nhãn hiệu).
- Hướng dẫn nộp trực tuyến: `https://dms.noip.gov.vn`.
- Format 1 trang A4, có chỗ ký tên + đóng dấu.

**Render:** `takedown_template.py` đọc template, thay `{placeholders}` từ `brand_config` + `page_meta`, viết ra `.cache/complaints/YYYY-MM-DD-<brand_id>-<page_slug>.md`. Output markdown trong ZCode chỉ link tới file (không spam nội dung).

### 3.5. Cấu hình `config/brands.yaml`

```yaml
defaults:
  scoring:
    name_threshold_high: 90
    name_threshold_mid: 80
    avatar_distance_strong: 4
    avatar_distance_moderate: 8
    avatar_distance_weak: 12
    recent_years: [2025, 2026]
    risk_high: 70
    risk_mid: 40

brands:
  - id: fpt_shop
    display_name: "FPT Shop"
    aliases:                          # tất cả biến thể tên HỢP LỆ của brand
      - "FPT Shop"
      - "FPTShop"
      - "FPT Shop Việt Nam"
    official_username: "fptshop"
    official_page_url: "https://www.facebook.com/fptshop"
    avatar_path: "./config/avatars/fptshop_avatar.png"
    cover_path: "./config/avatars/fptshop_cover.png"
    trademark:
      vn_number: "12345-2020"         # số đăng ký nhãn hiệu VN (để điền đơn SHTT)
      vn_class: "9"                   # lớp Nice
      meta_ip_rights_id: ""           # Meta IP Rights ID (cấp sau đăng ký Brand Protection)
    scoring_overrides: {}             # optional, merge vào defaults
```

**Đa brand:** Skill lặp qua từng brand, output riêng section per brand.

### 3.6. Output markdown trong ZCode

```markdown
# 🔍 Brand Guard — Facebook Fake Page Scan
**Run at:** 2026-07-05 14:30 ICT  **Brands:** 1  **Pages scanned:** 18

## 🏷 FPT Shop

### 🔴 Cao rủi ro (3)
| # | Page | Tên hiển thị | Score | Tên (35) | Avatar (25) | Cover (20) | Mới (12) | URL (8) |
|---|------|--------------|-------|----------|-------------|------------|----------|---------|
| 1 | [fpt.shop.official](https://fb.com/fpt.shop.official) | FPT Shop Official | **92** | 35 | 25 | 20 | 12 | 0 |
| 2 | [fptshop2026](https://fb.com/fptshop2026) | FPT Shop | **85** | 35 | 17 | 17 | 12 | 4 |
| 3 | [fpt.shop.vn](https://fb.com/fpt.shop.vn) | FPT Shop VN | **71** | 35 | 4 | 0 | 12 | 8 |

👉 Đã sinh mẫu đơn khiếu nại: `.cache/complaints/2026-07-05-fpt_shop.md`

### 🟡 Trung (2) — cần review tay
| # | Page | Score | Lý do review |
|---|------|-------|--------------|
| 4 | [fptshop.support](...) | 58 | Tên giống, avatar khác, không có info mới |
| 5 | [fptshops.officiall](...) | 47 | ... |

### 🟢 Thấp (1) — bỏ qua
- `fpt-commerce` (score 22) — tên khác, không avatar trùng.

---
**Lưu ý pháp lý:** Kết quả chỉ là gợi ý dựa trên heuristic. Trước khi gửi khiếu nại, hãy review lại bằng chứng và xác nhận với pháp chế. Không tự liên hệ/xâm phạm trang nghi vấn.
```

## 4. SKILL.md manifest

```yaml
---
name: brand-guard-fb
description: Detect fake Facebook fanpages impersonating user's brand by name + avatar + cover photo + recency heuristics. Outputs a markdown report with risk scores and generates Meta IP / SHTT Vietnam takedown complaint templates. Use when user reports brand impersonation on Facebook or wants proactive brand protection monitoring.
---

# Brand Guard FB

Tự dò fanpage Facebook giả mạo thương hiệu, chấm điểm rủi ro, và sinh mẫu đơn khiếu nại.

## Khi nào dùng
- Bị lập fanpage giả mạo thương hiệu trên Facebook.
- Muốn giám sát định kỳ/three theo yêu cầu.
- Cần bằng chứng + mẫu đơn để gửi Meta Brand Protection hoặc Cục SHTT.

## Cách dùng
1. Đảm bảo `config/brands.yaml` đã điền brand info (xem `config/brands.example.yaml`).
2. Đặt avatar/cover chính chủ vào `config/avatars/`.
3. Gọi skill này. ZCode sẽ chạy script và trả về báo cáo markdown.

## Lưu ý
- Chỉ đọc trang công khai, không scraping cần đăng nhập, không vi phạm ToS Facebook một cách rõ ràng (chỉ search engine + HEAD/GET 1 lần).
- Kết quả là gợi ý heuristic — review tay trước khi hành động pháp lý.
```

## 5. Testing strategy

- **Unit tests (`tests/`):**
  - `test_scoring.py` — test fuzzy name (3 levels), pHash distance thresholds, verified override, total score, classification thresholds.
  - `test_search.py` — test regex lọc URL (accept page URL, reject profile/groups/posts).
  - Fixture HTML trong `tests/fixtures/` để test metadata parser mà không cần network.
- **Integration test:** chạy script với `--brand fpt_shop --no-network` để verify pipeline dùng cached data.
- **Manual smoke test:** chạy 1 lần thật với 1 brand demo (FPT Shop), verify output có format đúng và tìm được ít nhất 1 trang nghi vấn.

## 6. Rủi ro & giải pháp

| Rủi ro | Giải pháp |
|---|---|
| Search engine block (rate limit, captcha) | Sleep 2-5s giữa query, xoay UA, fallback DDG→Bing, cache 24h. Nếu bị block, in cảnh báo trong output. |
| Facebook HTML thay đổi structure | Parse chỉ dựa vào OG meta tags (ổn định hơn HTML structure). Heuristic HTML (verified badge, creation year) là best-effort — không fail pipeline nếu thiếu. |
| pHash false positive (ảnh common) | Yêu cầu **tên + avatar cùng trùng** mới vào 🔴. pHash alone không đủ. |
| Trang chính chủ bị false positive | `−35` override nếu URL == official_page_url hoặc verified badge. Whitelist official_username trong filter URL. |
| ToS Facebook | Không scraping đăng nhập, không follow link sâu, tôn trọng robots.txt. Chỉ dùng trang công khai đã được search engine index. |
| Pháp lý | Template chỉ là gợi ý, user tự review và ký trước khi gửi. |

## 7. Lộ trình tương lai (out of scope v1)

- **v2:** Track lịch sử takedown (state file `takedowns.yaml`, dashboard HTML).
- **v3:** Đa nền tảng (Instagram, TikTok, Zalo, website).
- **v4:** Tích hợp ZeroFox/Bolster API nếu budget có.
- **v5:** Auto-submit Meta IP report qua official form API (nếu Meta cấp).

## 8. Dependencies

```
# requirements.txt
rapidfuzz>=3.0.0
imagehash>=4.3.0
Pillow>=10.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
pyyaml>=6.0
```

Không cần Graph API access token, không cần Meta developer account.

## 9. Definition of Done

- [ ] Skill cài được qua `Skill` tool, không lỗi import.
- [ ] `config/brands.example.yaml` chạy được với brand demo.
- [ ] Unit tests pass ≥ 90% line coverage trên `scoring.py` và `search.py`.
- [ ] Smoke test với brand thực tế tìm được ít nhất 1 trang nghi vấn (hoặc output sạch nếu brand chưa bị giả).
- [ ] Mẫu đơn Meta + SHTT render đúng placeholders.
- [ ] README trong skill hướng dẫn setup đầy đủ.
