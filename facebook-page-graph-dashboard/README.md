# Facebook Page Graph Dashboard

Dashboard theo dõi hiệu suất Fanpage Facebook bằng **Graph API** + công cụ moderation + báo cáo tuần.

> ⚠️ **Bảo mật**: Toàn bộ gọi Graph API đều **server-side**. Token chỉ lưu trong `.env.local`, không bao giờ expose ra browser, không log full token, không commit token lên git.

## 1. Mục tiêu dự án

- Dashboard bài viết: reach cao nhất, comment nhiều nhất, tỷ lệ tương tác, follower delta, video/reels kéo view.
- Moderation: lọc comment nhạy cảm (spam/công kích), gợi ý phản hồi mẫu, cảnh báo comment spike.
- Báo cáo: xuất CSV, chuẩn bị cấu trúc cho Google Sheet, so sánh chủ đề (vĩ mô, chứng khoán, lãi suất, BĐS, vàng).

## 2. Quyền Facebook cần có

Tạo Meta App tại <https://developers.facebook.com/apps/>, dùng Graph API Explorer để sinh token với các permission:

- `pages_show_list`
- `pages_read_engagement`
- `read_insights`
- `pages_read_user_content`
- `pages_manage_engagement`

`business_management` là **tùy chọn**, app không phụ thuộc vào quyền này.

## 3. Cách lấy Page Access Token

1. Vào [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer/).
2. Chọn Meta App.
3. Bấm **"User or Page"** → chọn **"Page Access Token"** (nếu muốn token Page trực tiếp) HOẶC giữ **"User Token"** rồi add permission bên dưới.
4. Add các permission ở mục 2.
5. Bấm **"Generate Access Token"**.
6. Nếu đang dùng User Token, gọi:
   ```text
   me/accounts?fields=id,name,access_token,tasks
   ```
   → trả về danh sách Page bạn quản lý, mỗi Page có `id`, `name`, `access_token` (Page Access Token).
7. Copy `id` và `access_token` của Page cần dùng.
8. Dán vào `.env.local`:
   ```bash
   FB_PAGE_ID=<id_cua_page>
   FB_PAGE_ACCESS_TOKEN=<page_access_token>
   FB_USER_ACCESS_TOKEN=<user_token_optional>
   ```
9. Khởi động lại `npm run dev`.

> Lưu ý: Page Access Token thường vô thời hạn nếu Page vẫn còn quyền và App ở chế độ Live (hoặc bạn dùng chính App của mình ở chế độ Development với role tester).

## 4. Biến môi trường

Copy `.env.example` → `.env.local` rồi điền:

```bash
FB_API_VERSION=v25.0
FB_PAGE_ID=
FB_PAGE_ACCESS_TOKEN=
FB_USER_ACCESS_TOKEN=
FB_APP_ID=
FB_APP_SECRET=
DATABASE_URL="file:./dev.db"
COMMENT_SPIKE_MIN_COUNT=20
COMMENT_SPIKE_RATIO=3
```

Giải thích:

- `FB_PAGE_ACCESS_TOKEN`: token chính để chạy dashboard.
- `FB_USER_ACCESS_TOKEN`: optional, chỉ dùng cho helper `/api/fb/accounts`.
- `FB_APP_ID` / `FB_APP_SECRET`: optional, để debug/exchange token sau này.
- `FB_API_VERSION`: lấy từ env, không hard-code (khi Meta bump version, code dùng giá trị này).

## 5. Cách chạy local

Yêu cầu: Node.js 18.17+ (khuyến nghị 20+).

```bash
npm install
cp .env.example .env.local   # rồi điền token như bước 3
npx prisma migrate dev --name init
npm run dev
```

Mở <http://localhost:3000>.

### Demo UI khi chưa có token

```bash
npm run seed   # tạo dữ liệu giả vào SQLite để xem dashboard
```

## 6. Cách test nhanh

1. Mở `/settings` → xem trạng thái env → bấm **Test Page Token**.
2. Vào `/dashboard` → bấm **Sync Facebook Data**.
3. Mở `/posts`, `/comments`, `/reports`.

## 7. Kiến trúc

```
/app
  /api
    /fb
      /page/route.ts            GET  -> info của Page
      /accounts/route.ts        GET  -> helper /me/accounts (cần user token)
      /posts/route.ts           GET  -> gọi thẳng Graph API lấy 25 bài gần nhất
      /post-insights/route.ts   GET  -> insights của 1 post
      /comments/route.ts        GET  -> comment của 1 post kèm moderation
      /sync/route.ts            POST -> sync Page + posts + insights về SQLite
      /moderation/route.ts      GET  -> moderation queue (DB)
      /reports/weekly/route.ts  GET  -> báo cáo tuần từ DB
      /export/posts/route.ts    GET  -> export CSV posts
      /dashboard/route.ts       GET  -> aggregate KPI dashboard
      /posts-db/route.ts        GET  -> danh sách post từ DB (có sort)
      /comments-db/route.ts     GET  -> danh sách comment từ DB
    /env/route.ts               GET  -> thông tin env (mask token)
  /dashboard /posts /comments /reports /settings
/components
  KpiCard, PostsTable, TopicPerformanceTable,
  CommentModerationTable, WeeklyReportCard, ErrorBox, Navbar
/lib
  facebook.ts   client Graph API + error mapping + token mask
  topics.ts     detectTopic (6 nhóm)
  moderation.ts keyword/sentiment/risk/suggestReply rule-based
  metrics.ts    engagementRate, percentile score, topic agg, comment spike
  csv.ts        CSV export
  prisma.ts     PrismaClient singleton
  env.ts        API helpers, publicEnvInfo
/prisma schema.prisma
/scripts seed.ts
```

## 8. Schema database

5 model: `PageSnapshot`, `Post`, `VideoMetric`, `Comment`, `WeeklyReport`. Chi tiết trong `prisma/schema.prisma`.

## 9. Logic nổi bật

- **Engagement rate** = (reactions + comments + shares + clicks) / reach (null nếu reach ≤ 0).
- **Post score** = 0.35·reachPercentile + 0.30·engagementRatePercentile + 0.20·commentsPercentile + 0.15·sharesPercentile.
- **Comment spike** (MVP): `commentsCount ≥ COMMENT_SPIKE_MIN_COUNT` và `commentsCount > median(25 bài gần nhất) × COMMENT_SPIKE_RATIO`.
- **Moderation**: rule-based. Nhóm spam → `hide_or_review`; công kích → `manual_review`; câu hỏi phổ biến → `suggest_reply` kèm mẫu tiếng Việt.
- **Topic detection**: keyword match, ưu tiên topic có nhiều match nhất.

## 9.4. Về chỉ số Reach / Video Views / Public Engagement

Dashboard **tách bạch 3 loại metric**, KHÔNG trộn lẫn thành "Total Reach":

| Metric | Bản chất | Source field | Ý nghĩa |
|---|---|---|---|
| **Reach thật** | Số người nhìn thấy bài | `post_impressions_unique` (Facebook Insights) | ✅ Chính thức, dùng cho ER |
| **Video Views** | Lượt xem video ≥3s | `post_video_views` (Facebook video metric) | ✅ Thật, nhưng CHỈ cho video/reel, không phải reach |
| **Public Engagement** | Tương tác công khai | `reactions + comments + shares` | ⚠️ **Proxy** — không phải reach, không dùng tính ER |

### 6 loại `metricSource` (gán theo sự tồn tại của dữ liệu, không phải > 0)

| metricSource | Ý nghĩa | Dùng tính ER? |
|---|---|---|
| `facebook_graph_api_insights` | Reach thật (`post_impressions_unique`). Cần App Review. | ✅ Có |
| `meta_business_suite_csv` | Reach/impressions imported từ Meta Business Suite CSV. Insight thật do Page admin export. | ✅ Có |
| `facebook_video_metric` | Video views (`post_video_views`). Metric thật cho video/reel. | ❌ Không |
| `facebook_public_metrics` | Reactions + comments + shares (field summary). Không phải reach. | ❌ Không |
| `public_engagement_proxy` | Alias cũ (deprecated, backward-compat). Sync mới không còn dùng. | ❌ Không |
| `unavailable` | Không có metric nào trả về. | ❌ Không |

**Quy tắc gán metricSource:**
- Một post có 0 reactions/cmt/shares nhưng API trả field summary hợp lệ vẫn là `facebook_public_metrics`.
- Một post có 0 video views nhưng `post_video_views` field có trả về vẫn là `facebook_video_metric`.
- Ưu tiên: `insights > video_metric > public_metrics > unavailable`.

### 3 chế độ xem Dashboard (auto-detect)

| Mode | Khi nào | Hiển thị |
|---|---|---|
| **Insights Mode** | Đa số (>50%) post có trueReach | Reach + ER, KPI Video/Engagement ẩn |
| **Public Engagement Mode** | Không có post nào có trueReach | Chỉ Public Engagement + Video Views, ER ẩn |
| **Mixed Mode** | Có cả trueReach lẫn public/video (thiểu số reach thật) | 3 cột riêng, không trộn |

### Nguyên tắc (theo phản biện)

1. ❌ KHÔNG cộng reach thật + video views + public engagement thành "Total Reach".
2. ❌ KHÔNG gán proxy/videoViews vào cột reach.
3. ❌ KHÔNG tính engagementRate nếu không có trueReach.
4. ❌ KHÔNG silently cap engagementRate (nếu ER cực đoan → flag warning, không sửa số).
5. ❌ KHÔNG dùng reach estimate mặc định (×25).
6. ✅ Mỗi post có đúng 1 `metricSource`.
7. ✅ Score chỉ tính cho post có đủ trueReach + engagementRate hợp lệ.
8. ✅ Nếu có `estimatedReach` → optional + calibration từ post thật của chính Page.

**Để có reach thật cho 100% post:** Cần App Review (Advanced Access cho `read_insights`) tại <https://developers.facebook.com/apps/{APP_ID}/review/>.

## 10. Lỗi thường gặp

| Hiệu ứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| `missing_token` | Thiếu `FB_PAGE_ACCESS_TOKEN` / `FB_PAGE_ID` trong `.env.local` | Điền lại + restart server |
| `invalid_token` (code 190) | Token hết hạn hoặc sai | Sinh lại Page Access Token ở Explorer |
| `missing_permission` (code 10/200/298) | Thiếu permission (vd. `read_insights`) | Cấp lại permission + sinh lại token |
| `/me/accounts` trả `data: []` | User không quản lý Page nào, hoặc thiếu `pages_show_list` | Cấp `pages_show_list` và đảm bảo user là admin Page |
| `unsupported_metric` | Metric không hỗ trợ ở version hiện tại | App tự fallback + warning (không crash). Có thể thay metric theo doc Graph API mới |
| Token hết hạn định kỳ | Page token có thể bị thu hồi khi đổi mật khẩu, gỡ quyền App | Sinh lại từ Explorer |

## 11. Bảo mật

- ❌ Không gọi Graph API từ browser.
- ❌ Không log / in full token (chỉ hiển thị mask `xxxxxx…yyyy`).
- ❌ Không lưu token vào DB.
- ❌ Không commit `.env.local` (đã trong `.gitignore`).
- ✅ Tất cả call Graph API nằm trong `app/api/*` hoặc `lib/*` (server-side).

## 12. Public Competitor Benchmark

Module `/benchmark` cho phép so sánh Page của bạn với các Page Facebook công khai cùng phân loại (vĩ mô, chứng khoán, lãi suất, BĐS, vàng, influencer tài chính). Module này **mở rộng** dự án, không phá vỡ module sync cũ.

### 12.1. Vì sao không lấy được reach/impressions của Page khác

Facebook/Meta **không cho phép** đọc các chỉ số private của Page khác:
- ❌ reach, impressions, engaged users, clicks, follower growth nội bộ.

Đó là dữ liệu riêng tư của đối thủ. Module benchmark KHÔNG cố đọc private insights bằng token của bạn.

### 12.2. Dữ liệu đối thủ dùng proxy công khai

| Chỉ số | Nguồn | Ghi chú |
|---|---|---|
| Followers / Likes | Trang công khai | Nếu Page ẩn, không có |
| Posts count trong kỳ | Đếm thủ công hoặc public API | MVP nhập CSV |
| Reactions công khai | Trang công khai | Tổng reactions |
| Comments công khai | Trang công khai | Tổng comments |
| Shares công khai | Trang công khai | Có thể bị ẩn |
| Video views công khai | Trang công khai | Có thể bị ẩn |
| Active ads | Meta Ad Library | Tích hợp tương lai |
| Dominant topic | Phân loại nội dung | Nhập tay |

> Không tự động scrape Facebook nếu chưa có phương thức hợp lệ (Meta Content Library / Ad Library API). MVP tập trung vào **manual / CSV import + analytics**.

### 12.3. Công thức

```text
Public Engagement          = reactions + comments + shares
Engagement / 1,000 followers = Public Engagement / followers × 1000
Public Engagement / Post   = Public Engagement / postsCount
Comment Intensity          = comments / publicEngagement
Share Intensity            = shares / publicEngagement
Posting Frequency / Day    = postsCount / numberOfDays(periodStart, periodEnd)
```

**Benchmark score** (percentile trong peer cùng category & period):

| Trọng số | Mặc định | Fallback (thiếu videoViews) |
|---|---|---|
| Engagement / 1k followers | 0.35 | 0.40 |
| Avg shares / post | 0.20 | 0.25 |
| Avg comments / post | 0.20 | 0.20 |
| Video views / follower | 0.10 | — |
| Posting frequency / day | 0.10 | 0.10 |
| Top post engagement | 0.05 | 0.05 |

> Follower tuyệt đối KHÔNG dùng làm chỉ số chính trong score — follower lớn không đồng nghĩa hiệu quả cao.

### 12.4. Cách chuẩn bị CSV

Header bắt buộc tối thiểu: `pageName, pageUrl, periodStart, periodEnd`. Các cột khác tùy chọn.

```csv
pageName,pageUrl,category,periodStart,periodEnd,followers,postsCount,reactionsCount,commentsCount,sharesCount,videoViews,topPostUrl,topPostEngagement,activeAds,dominantTopic,notes
CafeF,https://facebook.com/cafef,chứng khoán,2026-07-01,2026-07-31,1000000,120,50000,7000,3000,2000000,https://facebook.com/cafef/top,5000,true,chứng khoán,
Page Macro ABC,https://facebook.com/macroabc,vĩ mô,2026-07-01,2026-07-31,200000,40,12000,3500,800,300000,https://facebook.com/macroabc/top,1800,false,lãi suất,
```

Import: mở `/benchmark/import` → paste CSV → **Validate** → **Import**. Review các warning (followers ≤ 0, postsCount ≤ 0, thiếu videoViews).

### 12.5. Cách đọc kết quả

- **So với median peer**: Page bạn ngang bằng / trên / dưới mức trung bình peer trong cùng category.
- **So với top 25%**: nếu `engagementPer1kFollowers` ≥ peer top 25% → hiệu suất trên mỗi follower tốt.
- **So với best page**: khoảng cách tới Page dẫn đầu (theo score).

### 12.6. Cảnh báo khi dùng benchmark

- ❌ Không so sánh trực tiếp **public engagement** với **internal reach-based engagement rate** (hai thước đo khác nhau).
- ❌ Không dùng follower tuyệt đối làm kết luận hiệu quả.
- ⚠️ Page chạy ads mạnh có thể làm méo public engagement.
- ⚠️ Một số Page ẩn like/share hoặc giao diện Facebook không hiện đủ số liệu → validate kỹ khi import.

### 12.7. API endpoints

| Method | Route | Mô tả |
|---|---|---|
| GET | `/api/benchmark/pages` | List competitor pages (filter `?category=`) |
| POST | `/api/benchmark/pages` | Tạo competitor page |
| PATCH | `/api/benchmark/pages/:id` | Cập nhật page (pageName/category/notes/isActive...) |
| DELETE | `/api/benchmark/pages/:id` | Soft delete (`isActive=false`). `?hard=true` để xoá thật |
| GET | `/api/benchmark/snapshots` | List snapshots + benchmarkScore re-tính |
| POST | `/api/benchmark/snapshots` | Upsert snapshot, tự tính derived metrics + score |
| POST | `/api/benchmark/import-csv` | Parse → validate → upsert page + snapshot |
| GET | `/api/benchmark/compare` | So sánh own page với peer (rank, percentile, strengths, recommendations) |
| GET | `/api/benchmark/export` | Xuất CSV |

## 13. Roadmap

- [ ] Export Google Sheet (Service Account).
- [ ] Webhook realtime từ Facebook (cần app public + domain).
- [ ] Auto-hide comment sau khi user xác nhận (cần `pages_manage_engagement`).
- [ ] Telegram alert khi có spike / comment rủi ro cao.
- [ ] AI sentiment nâng cao (GPT/Claude/gemini) thay rule-based.
- [ ] Tích hợp Meta Content Library + Meta Ad Library API (cần quyền research).
- [ ] Auto-fetch public competitor metrics qua Facebook Graph API (với page đã được ủy quyền public).
- [ ] Multi-page dashboard.

---

## 13.1. Meta App Review basic setup

Để submit App Review (lấy `read_insights` Advanced Access cho true reach), cần setup trong Meta Developer Dashboard:

1. **Upload app icon 1024×1024** (PNG/JPG) trong Meta Developer Dashboard → App Settings.
2. **Set Privacy Policy URL**: `https://your-domain.com/privacy`
3. **Set Data Deletion URL**: `https://your-domain.com/data-deletion`
4. **(Optional) Set Terms of Service URL**: `https://your-domain.com/terms`
5. **Set Category**: `Business` (ưu tiên). Fallback: `Productivity` hoặc `Utilities & Tools`.
6. **Save changes**.
7. Quay lại **App Review → Permissions and Features** để submit.

> ⚠️ Meta yêu cầu **public HTTPS URL** cho Privacy Policy / Data Deletion — không chấp nhận `localhost`. Phải deploy app lên production (Vercel, Cloudflare, v.v.).

> 📧 **Contact email**: `stevetransg@gmail.com` (đã được dùng trong `/privacy`, `/data-deletion`, `/terms`).

Chi tiết permission use case + screencast script: xem [`docs/meta-app-review.md`](docs/meta-app-review.md).

## 13.2. Requested Permissions — Analytics Phase (SUBMIT TRƯỚC)

> ⚠️ **Quan trọng**: Submit 3 permission Analytics **trước**, đợi Meta duyệt xong rồi mới submit Moderation. Nếu submit cả đợt cùng lúc, Meta sẽ khó đánh giá use case và dễ reject.

| Permission | Mục đích |
|---|---|
| `pages_show_list` | Hiển thị danh sách Page mà user quản lý để chọn Page connect. |
| `pages_read_engagement` | Đọc Page posts, post metadata, reactions/comments/shares count, public engagement data. Cần để hiển thị organic post-level performance. |
| `read_insights` | Đọc Page/Post insights (reach, impressions, engaged users, clicks). Cần cho analytics chính xác, engagement rate, báo cáo tuần/tháng. |

**Use case screencast**: trong `docs/meta-app-review.md` (14 bước: open app → connect Page → sync → dashboard → reports).

## 13.3. Optional Permissions — Moderation Phase (SUBMIT SAU — Phase 2)

> ⚠️ Chỉ submit 2 permission này **SAU KHI** 3 permission Analytics (ở 13.2) đã được Meta duyệt. Đăng ký cùng lúc với Analytics sẽ làm reviewer khó đánh giá use case và dễ bị reject.

| Permission | Mục đích |
|---|---|
| `pages_read_user_content` | Đọc comment của user trên Page posts để build moderation queue (detect spam, sensitive keywords, comments cần manual review). |
| `pages_manage_engagement` | Cho phép Page admin reply/hide comment từ dashboard sau khi đã xác nhận thủ công. App KHÔNG tự động delete comment mà không có admin action. |

---

## 13.2. Tự khởi động + auto-sync (macOS LaunchAgent)

Dự án có **3 LaunchAgents** trên macOS để:
- **Server agent** (`com.bobo.fb-dashboard.server`): tự khởi động khi đăng nhập + tự restart nếu crash.
- **Sync agent** (`com.bobo.fb-dashboard.sync`): gọi `POST /api/fb/sync` mỗi 2 giờ.
- **Token refresh agent** (`com.bobo.fb-dashboard.token-refresh`): exchange USER → PAGE token mỗi 50 phút, tự update `.env.local`. Yêu cầu `FB_USER_ACCESS_TOKEN` + `FB_APP_ID` + `FB_APP_SECRET`.

### Cài đặt (chạy 1 lần)

```bash
# Build trước (cần .next production)
npm run build

# Load 2 agents
./scripts/agent-start.sh
```

### Vận hành

```bash
./scripts/agent-status.sh    # xem trạng thái + log gần đây
./scripts/agent-start.sh     # start/restart 2 agents
./scripts/agent-stop.sh      # dừng (vẫn tự chạy lại sau reboot)
```

### Lịch sync

Mỗi 2 giờ (theo giờ máy): `00:00, 02:00, 04:00, 06:00, 08:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00, 22:00`.

### Log

```bash
tail -f logs/server.out.log   # log server
tail -f logs/sync.out.log     # log sync (mỗi lần sync 1 dòng response)
```

### Bỏ cài đặt (gỡ hoàn toàn)

```bash
./scripts/agent-stop.sh
rm ~/Library/LaunchAgents/com.bobo.fb-dashboard.server.plist
rm ~/Library/LaunchAgents/com.bobo.fb-dashboard.sync.plist
rm ~/Library/LaunchAgents/com.bobo.fb-dashboard.token-refresh.plist
```

### Auto-refresh token (tùy chọn, khuyến nghị)

Page Access Token thường expire theo User token session (1-2 giờ). Để tự refresh:

**Bước 1: Lấy 3 thông tin từ Facebook**

1. **FB_APP_ID**: <https://developers.facebook.com/apps/> → chọn App → Settings → App ID. (vd `1022150267441192`)
2. **FB_APP_SECRET**: cùng trang → **App Secret** → Show → copy 32 ký tự hex.
3. **FB_USER_ACCESS_TOKEN**: vào <https://developers.facebook.com/tools/explorer/> → chọn App → add permission `pages_show_list, pages_read_engagement, read_insights, pages_read_user_content, pages_manage_engagement` → Generate Access Token (User Token, short-lived OK).

**Bước 2: Điền vào `.env.local`**

```bash
FB_APP_ID=<app_id>
FB_APP_SECRET=<app_secret>
FB_USER_ACCESS_TOKEN=<user_token_EAAB...>
```

**Bước 3: Restart agent**

```bash
./scripts/agent-start.sh
```

Script sẽ tự động detect `FB_USER_ACCESS_TOKEN` và load `com.bobo.fb-dashboard.token-refresh` agent (chạy mỗi 50 phút).

**Flow tự refresh:**

```
[mỗi 50 phút]
  refresh-token.sh
    → POST /api/fb/exchange-token { userToken, longLived: true }
      → lib/facebook.ts getLongLivedUserToken()  // short-lived → long-lived 60 ngày
      → lib/facebook.ts exchangeUserToPageToken() // user → page token
      → cập nhật .env.local + .env
    → ./scripts/agent-start.sh  // restart server với token mới
```

**Manual refresh (test ngay không đợi 50 phút):**

```bash
./scripts/refresh-token.sh
```

**Log refresh:**

```bash
tail -f logs/token-refresh.log
```

### Lưu ý

- Server chạy port **3123** (tránh xung đột port 3000).
- Token trong `.env.local` phải còn hạn — nếu hết hạn, sync sẽ fail, bạn cần sinh lại token và restart server.
- Sau khi `npm run build` lại (vd cập nhật code), chạy `./scripts/agent-start.sh` để server nhận code mới.

## 13.4. Meta Business Suite CSV Import

Vì `read_insights` Advanced Access bị chặn ở **Business Verification**, module CSV import cho phép user tự export insights từ Meta Business Suite và upload vào dashboard.

### Vì sao dùng CSV import

- App Review đang bị chặn vì user là cá nhân (chưa có pháp nhân xác minh).
- CSV export từ Meta Business Suite là dữ liệu **insight chính thức** do Meta cung cấp, được Page admin tự thao tác.
- Dashboard coi đây là nguồn "true insight data, manually imported" với `metricSource = meta_business_suite_csv`.
- **KHÔNG** gọi proxy engagement là reach. **KHÔNG** tự động login Meta. **KHÔNG** scrape UI.

### Cách export thủ công

1. Mở <https://business.facebook.com/latest/>
2. Chọn Page → **Insights** → **Content**
3. Chọn khoảng thời gian (7/28/90 ngày)
4. Bấm **Export** → chọn CSV hoặc XLSX
5. Tải file về máy
6. Upload vào dashboard `/imports`

Chi tiết: xem [`docs/csv-import-user-guide.md`](docs/csv-import-user-guide.md).

### Cách dùng watched folder (optional)

```bash
META_EXPORTS_WATCH_DIR=~/Downloads \
META_EXPORTS_AUTO_IMPORT=true \
npx tsx scripts/watch-meta-exports.ts
```

Script tự phát hiện file mới trong `~/Downloads` match pattern (`*.csv` + tên chứa "insights"/"facebook"/"meta") → copy vào `imports/incoming/` → upload qua API.

> ⚠️ Script chỉ xử lý file **user đã tự tải**. Không mở browser, không login, không scrape.

### Nguồn dữ liệu mới

| metricSource | Mô tả |
|---|---|
| `meta_business_suite_csv` | Manually imported từ Meta Business Suite export (CSV/XLSX) |

Được phép tính ER vì reach là insight thật từ Meta (do Page admin export, không phải proxy).

### Cảnh báo

- ⚠️ **Không realtime** — cần export định kỳ.
- ⚠️ **Format có thể thay đổi** — Meta có thể đổi header theo version UI.
- ⚠️ **Không scrape Meta** — không tự động tải file bằng browser automation.

Tài liệu kỹ thuật chi tiết: [`docs/csv-import-technical-design.md`](docs/csv-import-technical-design.md).

## Meta Business Suite Export Workflow

- **Target website**: https://business.facebook.com/latest/
- **Manual path**: Insights → Content → Export data
- **App KHÔNG tự động tải dữ liệu** từ Meta Business Suite.
- **Lý do**: account-safety risk, compliance risk, Meta khuyến nghị dùng official APIs cho programmatic access.

### Workflow triển khai

1. **Generate export checklist** — sinh danh sách file cần tải theo tháng/quý/năm:
   ```bash
   npm run export:checklist -- --month 2026-07
   # Output: docs/export-checklists/chimcut-2026-07.md
   ```

2. **User manually exports** files từ Meta Business Suite theo checklist.

3. **Watched folder detects** CSV/XLSX (optional semi-automation):
   ```bash
   npm run watch-exports
   # Theo dõi ~/Downloads, copy file hợp lệ vào imports/incoming/
   ```

4. **Dashboard imports** qua `/imports` — dry-run mapping + preview.

5. **User reviews and applies** metrics — confirm trước khi ghi vào DB.

### Export matrix

| ID | Priority | Verified? | Content | Data view | Preset | Use case |
|---|---|---|---|---|---|---|
| **P01** | **P0** | ✅ | Posts | Lifetime | Performance | Ranking toàn bộ bài viết |
| **P02** | **P0** | ✅ | Posts | Lifetime | Published | Master list bài viết |
| **V01** | **P0** | ✅ | Video | Lifetime | Performance | Top video ranking |
| V02 | P1 | ✅ | Video | Daily/Activity | Performance | Video daily trend (⚠️ chỉ video) |
| V03 | P2 | ✅ | Video | Lifetime | Retention | Video retention |
| G02 | P2 | ✅ | Page | Daily | Audience | Audience demo (KHÔNG phải performance) |
| ~~G01~~ | — | ❌ | Page | Daily | Performance | **Not yet found** trong Content Export |

> **⚠️ Meta limitation 1**: "Bộ lọc Hoạt động / Activity chỉ bao gồm bài viết có video."
>
> **⚠️ Meta limitation 2**: Page / preset "Hiệu quả / Performance" bị disable khi content level = Trang. G01 (Page / Daily / Performance) **chưa tìm thấy** trong Content Export. Nếu sau này tìm thấy ở Insights → Results/Overview, sẽ promote lên P0.
>
> **⚠️ Audience ≠ Performance**: Page / Daily / Audience (G02) chỉ có demographic data (tuổi, giới tính, quốc gia). **KHÔNG thay thế cho Page performance** — không có reach/impressions/engagement.

Chi tiết: [`docs/export-matrix-chimcut.md`](docs/export-matrix-chimcut.md)

### Mock automation lab

Test pipeline tại `http://localhost:3123/dev/mock-meta-export` — giả lập UI export Meta (KHÔNG kết nối Meta thật, chỉ tạo mock CSV để test import).

### Compliance

- ❌ KHÔNG browser automation trên Meta Business Suite thật.
- ❌ KHÔNG headless automation.
- ❌ KHÔNG cookie/session reuse.
- ❌ KHÔNG scheduled UI bot.
- ✅ Manual export + watched folder + import dry-run.
- ✅ Playwright chỉ dùng cho local mock page.

Chi tiết compliance: [`docs/meta-business-suite-export-compliance-research.md`](docs/meta-business-suite-export-compliance-research.md)

### Cleaning up downloaded export files

Script có thể đưa file export gốc trong Downloads vào **Trash/Archive** sau khi copy + import thành công.

**Mặc định TẮT** để an toàn:
```bash
META_EXPORTS_CLEANUP_MODE=none       # không cleanup
META_EXPORTS_CLEANUP_DRY_RUN=true    # dry-run ngay cả khi bật
```

**Recommended sau khi test 2-3 file thật:**
```bash
META_EXPORTS_CLEANUP_MODE=trash
META_EXPORTS_CLEANUP_DRY_RUN=false
META_EXPORTS_CLEANUP_AFTER=upload_dry_run
```

**Most conservative (archive thay vì trash):**
```bash
META_EXPORTS_CLEANUP_MODE=archive
META_EXPORTS_ARCHIVE_DIR=imports/archive
META_EXPORTS_CLEANUP_DRY_RUN=false
```

Cleanup modes:
| Mode | Hành động |
|---|---|
| `none` | Không làm gì (mặc định) |
| `trash` | Đưa file gốc vào Trash/Recycle Bin (khôi phục được) |
| `archive` | Move file gốc vào `imports/archive/` |

Cleanup triggers (`META_EXPORTS_CLEANUP_AFTER`):
| Stage | Khi nào cleanup |
|---|---|
| `copy` | Sau khi copy + hash verified |
| `upload_dry_run` | Sau khi API upload/dry-run thành công |
| `apply` | Sau khi user confirm apply metrics |

⚠️ **Không xóa vĩnh viễn** — luôn dùng Trash hoặc Archive. Nếu cleanup fail, file gốc được giữ nguyên. |


## 14. Scripts

```bash
npm run dev              # chạy dev
npm run build            # build production
npm run typecheck        # kiểm tra TypeScript
npm run prisma:migrate   # tạo migration mới
npm run prisma:generate  # regenerate client
npm run prisma:studio    # mở Prisma Studio để xem DB
npm run seed             # tạo dữ liệu demo
```
