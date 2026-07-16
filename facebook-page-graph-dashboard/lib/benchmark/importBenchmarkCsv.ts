/**
 * Benchmark CSV Import — parse public engagement CSV exports.
 *
 * Supports Vietnamese + English aliases for benchmark post columns.
 * Key principle: blank = null (NOT zero), "0" = observed zero.
 *
 * Dry-run mode returns a summary without writing to DB.
 */

import { parse } from "csv-parse/sync";
import { derivePostMetrics } from "./publicMetrics";

export interface BenchmarkCsvRow {
  pageUrl?: string;
  pageName?: string;
  postUrl: string;
  postedAt?: string | null;
  textSnippet?: string | null;
  contentType?: string | null;
  topicTag?: string | null;
  reactions: string | null;
  comments: string | null;
  shares: string | null;
  publicVideoViews: string | null;
}

export interface ParsedBenchmarkPost {
  pageUrl: string | null;
  pageName: string | null;
  postUrl: string;
  postedAt: string | null;
  textSnippet: string | null;
  contentType: string | null;
  topicTag: string | null;
  reactions: number | null;
  comments: number | null;
  shares: number | null;
  publicVideoViews: number | null;
  reactionsObserved: boolean;
  commentsObserved: boolean;
  sharesObserved: boolean;
  publicVideoViewsObserved: boolean;
  comparableEngagement: number | null;
  observedPublicEngagement: number | null;
  metricCoverageScore: number;
  warnings: string[];
}

export interface ImportResult {
  totalRows: number;
  parsed: ParsedBenchmarkPost[];
  skipped: { row: number; reason: string }[];
  warnings: string[];
}

// Column alias maps (lowercased, trimmed)
const COLUMN_ALIASES: Record<string, string[]> = {
  pageUrl: [
    "pageurl", "page url", "page_link", "page link",
    "url trang", "đường dẫn trang", "canonicalurl", "canonical url",
    "fb_url", "fb url",
  ],
  pageName: ["pagename", "page name", "trang", "tên trang", "fanpage"],
  postUrl: [
    "posturl", "post url", "permalink", "link", "bài đăng",
    "đường dẫn bài", "post_link", "post link", "url",
  ],
  postedAt: [
    "postedat", "posted at", "date", "ngày", "ngày đăng",
    "thời gian", "thời gian đăng", "created", "created_time",
    "createdtime", "publish", "published", "thời điểm",
  ],
  textSnippet: [
    "textsnippet", "text snippet", "text", "nội dung", "caption",
    "message", "content", "nội dung bài", "tiêu đề", "title",
  ],
  contentType: [
    "contenttype", "content type", "type", "loại", "định dạng",
    "format", "post type", "loại nội dung",
  ],
  topicTag: [
    "topictag", "topic tag", "topic", "chủ đề", "tag",
    "hashtag", "category", "danh mục",
  ],
  reactions: [
    "reactions", "reaction", "phản ứng", "lượt phản ứng",
    "likes", "thích", "cảm xúc",
  ],
  comments: [
    "comments", "comment", "bình luận", "lượt bình luận",
    "cmts", "bl",
  ],
  shares: [
    "shares", "share", "chia sẻ", "lượt chia sẻ",
    "lượt chia se", "cs",
  ],
  publicVideoViews: [
    "publicvideoviews", "public video views", "video views",
    "views", "lượt xem", "lượt xem video", "videoviews",
  ],
};

function normalizeHeader(h: string): string {
  return h.trim().toLowerCase().replace(/\s+/g, " ");
}

function buildHeaderMap(headers: string[]): Record<string, number> {
  const map: Record<string, number> = {};
  for (const [field, aliases] of Object.entries(COLUMN_ALIASES)) {
    // Exact match first
    for (let i = 0; i < headers.length; i++) {
      const norm = normalizeHeader(headers[i]);
      if (aliases.includes(norm)) {
        map[field] = i;
        break;
      }
    }
    if (map[field] != null) continue;
    // Substring match (≥8 chars to avoid false positives)
    for (let i = 0; i < headers.length; i++) {
      const norm = normalizeHeader(headers[i]);
      for (const alias of aliases) {
        if (alias.length >= 8 && norm.includes(alias)) {
          map[field] = i;
          break;
        }
      }
      if (map[field] != null) break;
    }
  }
  return map;
}

function getCell(row: string[], index: number | undefined): string {
  if (index == null || index < 0 || index >= row.length) return "";
  return row[index]?.trim() ?? "";
}

/**
 * Parse a benchmark CSV string into structured posts.
 */
export function parseBenchmarkCsv(csvText: string): ImportResult {
  let records: string[][] = [];
  try {
    records = parse(csvText, {
      skip_empty_lines: true,
      relax_column_count: true,
      trim: true,
    });
  } catch {
    return {
      totalRows: 0,
      parsed: [],
      skipped: [],
      warnings: ["CSV parse error: invalid format"],
    };
  }

  if (records.length < 2) {
    return {
      totalRows: 0,
      parsed: [],
      skipped: [],
      warnings: ["CSV is empty or has only headers"],
    };
  }

  const headers = records[0];
  const headerMap = buildHeaderMap(headers);

  if (headerMap.postUrl == null) {
    return {
      totalRows: 0,
      parsed: [],
      skipped: [],
      warnings: [
        "Missing required column: postUrl (need one of: postUrl, permalink, link, url, bài đăng, đường dẫn bài)",
      ],
    };
  }

  const parsed: ParsedBenchmarkPost[] = [];
  const skipped: { row: number; reason: string }[] = [];
  const warnings: string[] = [];

  for (let r = 1; r < records.length; r++) {
    const row = records[r];
    if (!row || row.every((c) => !c?.trim())) {
      skipped.push({ row: r + 1, reason: "empty row" });
      continue;
    }

    const postUrlRaw = getCell(row, headerMap.postUrl);
    if (!postUrlRaw) {
      skipped.push({ row: r + 1, reason: "missing postUrl" });
      continue;
    }

    const reactionsRaw = getCell(row, headerMap.reactions);
    const commentsRaw = getCell(row, headerMap.comments);
    const sharesRaw = getCell(row, headerMap.shares);
    const videoRaw = getCell(row, headerMap.publicVideoViews);
    const rowWarnings: string[] = [];

    const derived = derivePostMetrics({
      reactions: reactionsRaw || null,
      comments: commentsRaw || null,
      shares: sharesRaw || null,
      publicVideoViews: videoRaw || null,
    });

    if (!derived.reactionsObserved && !derived.commentsObserved) {
      rowWarnings.push("neither reactions nor comments observed");
    }

    parsed.push({
      pageUrl: getCell(row, headerMap.pageUrl) || null,
      pageName: getCell(row, headerMap.pageName) || null,
      postUrl: postUrlRaw,
      postedAt: getCell(row, headerMap.postedAt) || null,
      textSnippet: getCell(row, headerMap.textSnippet) || null,
      contentType: getCell(row, headerMap.contentType) || null,
      topicTag: getCell(row, headerMap.topicTag) || null,
      reactions: derived.reactions,
      comments: derived.comments,
      shares: derived.shares,
      publicVideoViews: derived.publicVideoViews,
      reactionsObserved: derived.reactionsObserved,
      commentsObserved: derived.commentsObserved,
      sharesObserved: derived.sharesObserved,
      publicVideoViewsObserved: derived.publicVideoViewsObserved,
      comparableEngagement: derived.comparableEngagement,
      observedPublicEngagement: derived.observedPublicEngagement,
      metricCoverageScore: derived.metricCoverageScore,
      warnings: rowWarnings,
    });
  }

  if (parsed.length === 0 && skipped.length > 0) {
    warnings.push(`All ${skipped.length} data rows skipped`);
  }

  return {
    totalRows: parsed.length,
    parsed,
    skipped,
    warnings,
  };
}

/**
 * Resolve a BenchmarkPage by pageUrl or pageName.
 * Returns pageId if found, null otherwise.
 */
export async function resolveBenchmarkPage(
  prisma: { benchmarkPage: { findFirst: Function; findUnique: Function } },
  pageUrl: string | null,
  pageName: string | null,
): Promise<number | null> {
  if (pageUrl) {
    const byUrl = await prisma.benchmarkPage.findUnique({ where: { canonicalUrl: pageUrl } });
    if (byUrl) return byUrl.id;
  }
  if (pageName) {
    const byName = await prisma.benchmarkPage.findFirst({
      where: { name: { equals: pageName } },
    });
    if (byName) return byName.id;
  }
  return null;
}
