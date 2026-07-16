# CSV Import — Technical Design

Tài liệu kỹ thuật cho module import CSV/XLSX từ Meta Business Suite.

---

## 1. Schema (Prisma)

### `InsightImportBatch`
Mỗi lần user upload 1 file = 1 batch.

| Field | Type | Mô tả |
|---|---|---|
| `id` | Int (PK) | Auto-increment |
| `filename` | String | Tên file gốc |
| `source` | String | `meta_business_suite_csv` |
| `importedAt` | DateTime | Timestamp |
| `importedBy` | String? | User identifier (future) |
| `fileHash` | String (unique) | SHA-256 hash để dedupe |
| `rowCount` | Int | Tổng số row data |
| `matchedCount` | Int | Rows match với post trong DB |
| `unmatchedCount` | Int | Rows không match (hoặc ambiguous) |
| `skippedCount` | Int | Rows skip do lỗi |
| `status` | String | `pending` → `mapped` → `imported` (hoặc `failed`) |
| `notes` | String? | Warnings accumulated |
| `rawColumnsJson` | String? | Header row gốc |
| `columnMappingJson` | String? | Mapping (user có thể sửa) |

### `ImportedPostInsight`
Mỗi row trong file = 1 record. Lưu raw + normalized.

| Field | Type | Mô tả |
|---|---|---|
| `id` | Int (PK) | |
| `batchId` | Int (FK) | → InsightImportBatch |
| `source` | String | `meta_business_suite_csv` |
| `postId` | String? | Post ID từ file (raw) |
| `permalinkUrl` | String? | Permalink từ file (normalized) |
| `externalContentId` | String? | Content ID nếu có |
| `createdTime` | String? | ISO datetime |
| `messageSnippet` | String? | Truncated 500 chars |
| `reach` / `impressions` / `engagedUsers` / `clicks` | Int? | Insight metrics |
| `reactions` / `comments` / `shares` | Int? | Engagement counts |
| `videoViews` / `watchTime` | Int? / Float? | Video metrics |
| `rawRowJson` | String | JSON của row gốc |
| `matchStatus` | String | `matched` / `unmatched` / `ambiguous` / `skipped` |
| `matchedPostId` | String? | Post ID trong DB nếu matched |
| `matchConfidence` | Float? | 0..1 |

### Cập nhật `Post` model

Không thay đổi schema của Post. Khi apply, update các field:
- `reach`, `impressions`, `engagedUsers`, `clicks`, `videoViews` (nếu có)
- `metricSource` = `meta_business_suite_csv`
- `engagementRate` (tính khi reach > 0)

---

## 2. Matching Logic

Thứ tự ưu tiên + confidence score:

| # | Method | Confidence | Điều kiện |
|---|---|---|---|
| 1 | `post_id` exact match | 1.00 | row.postId === post.fbPostId |
| 2 | `permalink_url` canonical | 0.95 | normalize URL cả 2 phía |
| 3 | `externalContentId` | 0.90 | post_id endsWith `_externalId` |
| 4 | date ± 6h + exact snippet | 0.80 | similarity(message) ≥ 0.95 |
| 5 | date ± 6h + fuzzy snippet | 0.60-0.75 | similarity 0.7-0.95 |
| <0.6 | unmatched | 0 | — |

### Ambiguous
- Nhiều candidate match với score top-2 chênh ≤ 0.10 → `ambiguous`.
- KHÔNG auto-apply. Phải user review.

---

## 3. Column Mapping

### Auto-detect

`columnDetection.ts` dùng alias map + normalize (lowercase + strip dấu tiếng Việt).

```ts
FIELD_ALIASES: Record<StandardField, string[]>
```

### Manual override

User có thể sửa mapping trong UI `/imports` (dropdown cho mỗi standard field).

---

## 4. Metric Priority (khi apply)

Quy tắc overwrite:

| `currentMetricSource` | Có ghi đè? | Lý do |
|---|---|---|
| `facebook_graph_api_insights` | ❌ Không (default) | API insight ưu tiên hơn CSV |
| `facebook_graph_api_insights` | ✅ Có (nếu `forceOverwrite=true`) | User yêu cầu |
| `facebook_video_metric` | ✅ cho reach/impressions; ❌ cho videoViews (default) | Giữ video views cũ |
| `facebook_public_metrics` | ✅ | CSV ưu tiên hơn proxy |
| `public_engagement_proxy` | ✅ | Legacy, CSV luôn ưu tiên |
| `unavailable` / null | ✅ | Không có gì để lose |

### Engagement Rate

Tính ER chỉ khi `reach > 0`. Công thức: `(reactions + comments + shares + clicks) / reach`.

Với `metricSource = meta_business_suite_csv`, ER được tính vì reach là insight thật.

---

## 5. Limitations

| Hạn chế | Mô tả |
|---|---|
| **No realtime** | Phải upload định kỳ. |
| **Format drift** | Meta có thể đổi header theo version → dashboard auto-detect nhưng có thể fail. |
| **Post matching** | Phụ thuộc chất lượng cột Post ID / Permalink. Nếu thiếu → fallback date+snippet (confidence thấp hơn). |
| **No file storage** | File không lưu trong DB, chỉ hash. Để re-apply, cần re-upload hoặc lưu trong `imports/incoming/`. |
| **Single Page** | Hiện module giả định tất cả rows cùng 1 Page. Multi-page cần batch thêm trường pageId. |

---

## 6. API Endpoints

| Method | Route | Mô tả |
|---|---|---|
| `POST` | `/api/imports/upload` | Upload FormData → parse → preview |
| `POST` | `/api/imports/confirm-mapping` | Update column mapping |
| `POST` | `/api/imports/apply` | Match + apply insights |
| `GET` | `/api/imports/history` | List batches |
| `GET` | `/api/imports/:id` | Batch detail + sample rows |
| `GET` | `/api/imports/:id/unmatched` | Unmatched/ambiguous rows |
| `GET` | `/api/imports/:id/export-unmatched` | Export CSV unmatched |
