/**
 * Matching logic — match imported row với Post hiện có trong database.
 *
 * Confidence score:
 * - post_id:           1.00
 * - permalink:         0.95
 * - externalContentId: 0.90
 * - date + exact snippet: 0.80
 * - date + fuzzy snippet:  0.60-0.75
 * - below 0.60:        unmatched
 */
import type { NormalizedRow } from "./normalizeRows";

export interface CandidatePost {
  fbPostId: string;
  permalinkUrl: string | null;
  message: string | null;
  createdTime: string | null;
  pageId?: string;
}

export type MatchStatus = "matched" | "unmatched" | "ambiguous" | "skipped";

export interface MatchResult {
  status: MatchStatus;
  matchedPostId: string | null;
  confidence: number;
  matchedPost?: CandidatePost;
  ambiguousCandidates?: CandidatePost[];
}

/**
 * Levenshtein distance đơn giản (không optimize cho performance, chỉ dùng cho snippet <200 chars).
 */
function levenshtein(a: string, b: string): number {
  const m = a.length;
  const n = b.length;
  if (m === 0) return n;
  if (n === 0) return m;
  const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = 0; i <= m; i++) dp[i][0] = i;
  for (let j = 0; j <= n; j++) dp[0][j] = j;
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost);
    }
  }
  return dp[m][n];
}

/**
 * Similarity ratio 0..1 dựa trên Levenshtein.
 */
function similarity(a: string, b: string): number {
  const la = a.length;
  const lb = b.length;
  if (la === 0 && lb === 0) return 1;
  const maxLen = Math.max(la, lb);
  if (maxLen === 0) return 1;
  const dist = levenshtein(a.slice(0, 200), b.slice(0, 200));
  return 1 - dist / maxLen;
}

/**
 * Canonical URL so sánh — strip protocol + www + tracking.
 */
function canonicalUrl(u: string): string {
  try {
    const url = new URL(u);
    let path = url.pathname.replace(/\/+$/, "");
    return (url.host.replace(/^www\./, "") + path).toLowerCase();
  } catch {
    return u.toLowerCase().replace(/^https?:\/\//, "").replace(/\/+$/, "");
  }
}

const SIX_HOURS_MS = 6 * 60 * 60 * 1000;

/**
 * Match 1 row với danh sách posts trong DB.
 */
export function matchRow(row: NormalizedRow, posts: CandidatePost[]): MatchResult {
  if (!posts || posts.length === 0) {
    return { status: "unmatched", matchedPostId: null, confidence: 0 };
  }

  // 1. post_id exact match
  if (row.postId) {
    const exact = posts.find((p) => p.fbPostId === row.postId);
    if (exact) {
      return { status: "matched", matchedPostId: exact.fbPostId, confidence: 1.0, matchedPost: exact };
    }
  }

  // 2. permalink exact/canonical match
  if (row.permalinkUrl) {
    const canonical = canonicalUrl(row.permalinkUrl);
    const matches = posts.filter((p) => p.permalinkUrl && canonicalUrl(p.permalinkUrl) === canonical);
    if (matches.length === 1) {
      return { status: "matched", matchedPostId: matches[0].fbPostId, confidence: 0.95, matchedPost: matches[0] };
    }
    if (matches.length > 1) {
      return {
        status: "ambiguous",
        matchedPostId: null,
        confidence: 0.95,
        ambiguousCandidates: matches,
      };
    }
  }

  // 3. externalContentId exact match
  if (row.externalContentId) {
    const matches = posts.filter(
      (p) => p.fbPostId === row.externalContentId || p.fbPostId.endsWith("_" + row.externalContentId),
    );
    if (matches.length === 1) {
      return { status: "matched", matchedPostId: matches[0].fbPostId, confidence: 0.90, matchedPost: matches[0] };
    }
  }

  // 4. + 5. created_time + snippet similarity
  if (row.createdTime) {
    const rowDate = new Date(row.createdTime).getTime();
    if (Number.isFinite(rowDate)) {
      const candidates = posts
        .filter((p) => {
          if (!p.createdTime) return false;
          const t = new Date(p.createdTime).getTime();
          return Number.isFinite(t) && Math.abs(t - rowDate) <= SIX_HOURS_MS;
        })
        .map((p) => {
          let score = 0.5; // base cho date match trong 6h
          if (row.messageSnippet && p.message) {
            const sim = similarity(row.messageSnippet, p.message);
            if (sim >= 0.95) score = 0.80; // exact snippet
            else if (sim >= 0.7) score = 0.60 + sim * 0.15; // fuzzy 0.60-0.75
            else score = 0; // snippet quá khác → skip
          } else {
            // Không có snippet → chỉ date match với confidence thấp
            score = 0.55;
          }
          return { post: p, score };
        })
        .filter((c) => c.score >= 0.55)
        .sort((a, b) => b.score - a.score);

      if (candidates.length === 0) {
        // skip — không có match hợp lý
      } else if (candidates.length === 1) {
        return {
          status: candidates[0].score >= 0.6 ? "matched" : "unmatched",
          matchedPostId: candidates[0].score >= 0.6 ? candidates[0].post.fbPostId : null,
          confidence: candidates[0].score,
          matchedPost: candidates[0].score >= 0.6 ? candidates[0].post : undefined,
        };
      } else {
        // Nhiều candidate → chỉ ambiguous nếu top 2 có score gần nhau
        if (candidates.length >= 2 && candidates[0].score - candidates[1].score < 0.1) {
          return {
            status: "ambiguous",
            matchedPostId: null,
            confidence: candidates[0].score,
            ambiguousCandidates: candidates.slice(0, 3).map((c) => c.post),
          };
        }
        // Top candidate rõ ràng hơn
        if (candidates[0].score >= 0.6) {
          return {
            status: "matched",
            matchedPostId: candidates[0].post.fbPostId,
            confidence: candidates[0].score,
            matchedPost: candidates[0].post,
          };
        }
      }
    }
  }

  return { status: "unmatched", matchedPostId: null, confidence: 0 };
}

/**
 * Match nhiều rows cùng lúc.
 */
export function matchRows(rows: NormalizedRow[], posts: CandidatePost[]): MatchResult[] {
  return rows.map((r) => matchRow(r, posts));
}
