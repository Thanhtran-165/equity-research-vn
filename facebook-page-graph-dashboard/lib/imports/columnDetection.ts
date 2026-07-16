/**
 * Column detection — match header của file import với field chuẩn.
 *
 * Hỗ trợ alias tiếng Anh + tiếng Việt.
 * Trả về mapping + warnings (missing required fields, ambiguous matches).
 */

export type StandardField =
  | "postId"
  | "permalinkUrl"
  | "externalContentId"
  | "createdTime"
  | "messageSnippet"
  | "reach"
  | "impressions"
  | "engagedUsers"
  | "clicks"
  | "reactions"
  | "comments"
  | "shares"
  | "videoViews"
  | "watchTime";

export const FIELD_ALIASES: Record<StandardField, string[]> = {
  postId: [
    "post id", "content id", "facebook post id", "id", "post_id",
    "id bài viết", "id nội dung", "mã bài viết",
  ],
  permalinkUrl: [
    "permalink", "permalink url", "permalink_url", "post url", "post_url", "link", "content url", "content_url", "url",
    "liên kết", "url bài viết", "đường dẫn",
  ],
  externalContentId: [
    "external content id", "external_id", "external content",
    "id nội dung ngoài", "mã nội dung ngoài",
  ],
  createdTime: [
    "created time", "created_time", "published date", "published_date", "date published", "post date", "post_date", "date",
    "ngày đăng", "thời gian đăng", "ngày tạo", "ngày xuất bản",
  ],
  messageSnippet: [
    "post message", "post_message", "message", "content", "caption", "title", "description", "text",
    "nội dung", "tiêu đề", "chú thích", "mô tả",
  ],
  reach: [
    "reach", "post reach", "facebook reach", "accounts reached", "people reached",
    "lượt tiếp cận", "số người tiếp cận", "người tiếp cận", "tiếp cận",
  ],
  impressions: [
    "impressions", "post impressions", "total impressions", "total_impressions",
    "lượt hiển thị", "số lượt hiển thị", "hiển thị",
    // KHÔNG match "lượt hiển thị quảng cáo" (paid) — đó là paidImpressions, không phải organic.
  ],
  engagedUsers: [
    "engaged users", "engaged_users", "post engaged users", "engagements", "people engaged",
    "người tương tác", "lượt tương tác", "tương tác",
  ],
  clicks: [
    "clicks", "post clicks", "link clicks", "other clicks",
    "tổng lượt click", "tong luot click", "lượt click",
    "lượt nhấp", "số lượt nhấp", "nhấp",
  ],
  reactions: [
    "reactions", "likes and reactions", "likes",
    "cảm xúc", "lượt thích", "thích",
  ],
  comments: [
    "comments", "comment count", "comment_count",
    "bình luận", "số bình luận",
  ],
  shares: [
    "shares", "share count", "share_count", "lượt chia sẻ", "luot chia se",
    "chia sẻ", "số lượt chia sẻ",
  ],
  videoViews: [
    "video views", "video_views", "3-second video views", "3s views",
    "lượt xem video trong tối thiểu 3 giây", "lượt xem video", "lượt xem",
  ],
  watchTime: [
    "watch time", "watch_time", "average watch time",
    "số giây xem", "so giay xem", "giây xem",
    "thời gian xem", "thời lượng xem",
  ],
};

export interface ColumnMapping {
  /** Map từ standardField → index cột trong file (hoặc null nếu không match) */
  [field: string]: number | null;
}

export interface ColumnDetectionResult {
  mapping: ColumnMapping;
  warnings: string[];
  ambiguousFields: string[];
}

function normalize(s: string): string {
  return s
    .toLowerCase()
    .trim()
    .replace(/[\s_\-]+/g, " ")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

/**
 * Headers chứa các từ khóa paid/ad → KHÔNG match cho organic metrics (impressions, reach, clicks).
 */
function isPaidHeader(header: string): boolean {
  const h = normalize(header);
  return /quang cao|paid|ad | ads|advertising/.test(h);
}

/**
 * Detect mapping từ headers → standard fields.
 *
 * Chiến lược:
 * 1. Pass 1 — EXACT match (sau normalize). Ưu tiên cao nhất.
 * 2. Pass 2 — nếu Pass 1 không có match, thử substring với alias DÀI (>= 8 ký tự)
 *    để tránh false positive.
 */
export function detectColumns(headers: string[]): ColumnDetectionResult {
  const normalizedHeaders = headers.map(normalize);
  const mapping: ColumnMapping = {};
  const warnings: string[] = [];
  const ambiguousFields: string[] = [];

  for (const field of Object.keys(FIELD_ALIASES) as StandardField[]) {
    const aliases = FIELD_ALIASES[field].map(normalize);

    // Pass 1: EXACT match (skip paid/ad headers for organic metrics)
    const exactMatches: number[] = [];
    for (let i = 0; i < normalizedHeaders.length; i++) {
      const h = normalizedHeaders[i];
      if (!h) continue;
      // Skip paid/ad headers for organic metric fields
      if (isPaidHeader(headers[i]) && ["impressions", "reach", "clicks"].includes(field)) {
        continue;
      }
      if (aliases.includes(h)) {
        exactMatches.push(i);
      }
    }

    if (exactMatches.length === 1) {
      mapping[field] = exactMatches[0];
      continue;
    }
    if (exactMatches.length > 1) {
      mapping[field] = exactMatches[0];
      ambiguousFields.push(field);
      warnings.push(
        `Field "${field}" khớp nhiều cột (exact): ${exactMatches.map((m) => `"${headers[m]}"`).join(", ")} — đã chọn đầu.`,
      );
      continue;
    }

    // Pass 2: substring match với alias DÀI (>= 8 ký tự normalize)
    // Skip paid/ad headers for organic metric fields
    const substringMatches: number[] = [];
    for (let i = 0; i < normalizedHeaders.length; i++) {
      const h = normalizedHeaders[i];
      if (!h) continue;
      if (isPaidHeader(headers[i]) && ["impressions", "reach", "clicks"].includes(field)) {
        continue;
      }
      for (const alias of aliases) {
        if (alias.length >= 8 && h.includes(alias) && h.length <= alias.length + 30) {
          substringMatches.push(i);
          break;
        }
      }
    }

    if (substringMatches.length === 0) {
      mapping[field] = null;
    } else if (substringMatches.length === 1) {
      mapping[field] = substringMatches[0];
    } else {
      mapping[field] = substringMatches[0];
      ambiguousFields.push(field);
      warnings.push(
        `Field "${field}" khớp nhiều cột (substring): ${substringMatches.slice(0, 5).map((m) => `"${headers[m]}"`).join(", ")}${substringMatches.length > 5 ? ` (+${substringMatches.length - 5} khác)` : ""} — đã chọn đầu.`,
      );
    }
  }

  // Warnings cho missing required fields
  if (mapping.postId == null && mapping.permalinkUrl == null) {
    warnings.push("THIẾU post_id hoặc permalink_url — không thể match chính xác với post trong DB.");
  }
  if (mapping.reach == null) {
    warnings.push("THIẾU cột reach — đây là metric quan trọng nhất cho Insights Mode.");
  }
  if (mapping.impressions == null) {
    warnings.push("Thiếu cột impressions (không bắt buộc nhưng nên có).");
  }

  return { mapping, warnings, ambiguousFields };
}
