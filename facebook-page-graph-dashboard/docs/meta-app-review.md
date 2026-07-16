# Meta App Review Preparation

Tài liệu chuẩn bị submit Meta App Review cho **Facebook Page Graph Dashboard**. Bao gồm:
- Thông tin App cơ bản cần setup.
- Use case cho từng permission.
- Script cho screencast quay cho reviewer.

---

## App Basic Information

| Trường | Giá trị đề xuất |
|---|---|
| **App name** | `Facebook Page Graph Dashboard` |
| **App category** | `Business` (ưu tiên) — fallback: `Productivity`, `Utilities` |
| **App icon** | PNG/JPG **1024 × 1024 px** (user tự upload trong Meta Dashboard) |
| **Privacy Policy URL** | `https://your-domain.com/privacy` |
| **Data Deletion URL** | `https://your-domain.com/data-deletion` |
| **Terms of Service URL** (optional) | `https://your-domain.com/terms` |
| **Contact email** | `stevetransg@gmail.com` |

> ⚠️ Meta **không chấp nhận** `localhost` cho Privacy Policy / Data Deletion URL. Phải là HTTPS public domain.

---

## Permissions Requested

### `pages_show_list` (required — Analytics phase)

**Use case:**
We use this permission to show the authenticated user the list of Facebook Pages they manage, so they can select which Page to connect to the dashboard. The app does not store the full Page list — it only persists the Page the user explicitly selects.

---

### `pages_read_engagement` (required — Analytics phase)

**Use case:**
We use this permission to read Page posts, post metadata, reactions count, comments count, shares count, and public engagement data from the selected Page. This is required to display organic post-level performance in the dashboard, compute engagement metrics, and identify top-performing content.

---

### `read_insights` (required — Analytics phase)

**Use case:**
We use this permission to retrieve Page and Post Insights for the selected Page, including reach (`post_impressions_unique`), impressions (`post_impressions`), engaged users (`post_engaged_users`), and clicks (`post_clicks`). These metrics are required for accurate analytics, engagement rate calculations, and weekly/monthly Page performance reports.

---

### `pages_read_user_content` (optional — Moderation phase)

**Use case:**
We use this permission to read user-generated comments on posts from the selected Page. This enables the moderation queue to detect spam, sensitive keywords, and comments requiring manual review. The app does not publish, edit, or delete comments without explicit admin action.

---

### `pages_manage_engagement` (optional — Moderation phase)

**Use case:**
We use this permission to allow Page admins to reply to or hide comments from the dashboard **after manual confirmation**. The app does not automatically delete comments without admin action. This permission is only used in the optional moderation module.

---

## Screencast Script For Reviewer

> Record a 2-3 minute screencast following these steps. Upload to a public URL (YouTube unlisted, Loom, etc.) and include in the App Review submission.

Steps:

1. **Open the app** at the public HTTPS URL.
2. **Go to Settings** page.
3. **Connect Facebook Page** — explain that the app uses Facebook Login or Page Access Token entered in `.env.local`.
4. **Complete Facebook Login** (if applicable) — show the OAuth flow.
5. **Show the list of managed Pages** returned by `/me/accounts`.
6. **Select a Page** to connect.
7. **Sync Page posts** — click the Sync button and explain it fetches recent posts.
8. **Open Dashboard** — show follower count, engagement metrics, and KPI cards.
9. **Show post performance metrics** — reactions, comments, shares, reach (if available).
10. **Open Posts page** — show sortable table with reach/impressions.
11. **Open Reports page** — generate a weekly report and show the summary.
12. **Explain** (voiceover or caption) that the app **only accesses Pages managed by the authenticated user**, does not sell data, does not share with third parties, and provides a `/data-deletion` flow for users.

---

## Data Handling Summary

- ✅ The app **does not sell** data.
- ✅ The app **does not share** data with third parties.
- ✅ The app **stores Page data only for analytics, reporting, and moderation** purposes.
- ✅ The app only accesses **Pages managed by the authenticated user**.
- ✅ Users can request deletion via `/data-deletion` — see [Data Deletion Instructions](../app/data-deletion/page.tsx).
- ✅ Privacy Policy is published at `/privacy` — see [Privacy Policy](../app/privacy/page.tsx).

---

## Checklist thao tác thủ công trong Meta Dashboard

1. ☐ Upload App Icon 1024×1024 PNG/JPG.
2. ☐ Set **App Category** = `Business` (hoặc `Productivity` / `Utilities & Tools`).
3. ☐ Set **Privacy Policy URL** = `https://your-domain.com/privacy`.
4. ☐ Set **Data Deletion URL** = `https://your-domain.com/data-deletion`.
5. ☐ (Optional) Set **Terms of Service URL** = `https://your-domain.com/terms`.
6. ☐ Save changes.
7. ☐ Mở **App Review → Permissions and Features**.
8. ☐ **Phase 1 — Analytics (submit trước)**: Request Advanced Access cho:
   - `pages_show_list`
   - `pages_read_engagement`
   - `read_insights`
9. ☐ **Phase 2 — Moderation (submit sau khi Phase 1 duyệt)**: Request Advanced Access cho:
   - `pages_read_user_content`
   - `pages_manage_engagement`
10. ☐ Upload **screencast** theo script ở trên.
11. ☐ Submit for review.

---

## Sau khi được duyệt

- Token Exchange flow sẽ tự động sinh long-lived Page token (đã có `scripts/refresh-token.sh`).
- Dashboard sẽ tự switch sang **Insights Mode** khi `metricSource = facebook_graph_api_insights` cho đa số post.
- `engagementRate` sẽ tính được chính xác (vì có `trueReach`).
