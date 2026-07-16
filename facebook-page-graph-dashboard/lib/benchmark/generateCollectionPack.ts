/**
 * Collection Pack Generator — core logic shared by CLI script and API route.
 *
 * Generates weekly benchmark collection pack:
 *   data/benchmark/collections/<week>/
 *     - collection-checklist.md
 *     - benchmark-weekly-template.csv
 *     - peer-status.csv
 */

import { mkdirSync, writeFileSync, existsSync } from "fs";
import { join } from "path";

export interface CollectionPeer {
  id: number;
  name: string;
  canonicalUrl: string;
  objectType: string;
  scaleBand: string | null;
  category: string | null;
  collectionFrequency: string | null;
  recommendedPostsPerCollection: number | null;
  audienceCount: number | null;
  audienceCountType: string | null;
  audienceCapturedAt: Date | null;
  postCount: number;
}

export interface CollectionPackResult {
  weekKey: string;
  outDir: string;
  files: string[];
  peerCount: number;
  targetRows: number;
}

function escapeCsv(val: string | null | undefined): string {
  if (val == null) return "";
  const s = String(val);
  if (s.includes(",") || s.includes('"') || s.includes("\n")) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

export function isoWeekKey(weekStart: Date): string {
  const y = weekStart.getFullYear();
  const m = String(weekStart.getMonth() + 1).padStart(2, "0");
  const d = String(weekStart.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export const TARGET_POSTS_PER_PEER = 4;

/**
 * Generate collection pack files from a list of peers.
 * Caller is responsible for fetching peers from DB.
 */
export function generateCollectionPack(
  peers: CollectionPeer[],
  weekStart: Date,
  baseDir: string,
): CollectionPackResult {
  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekStart.getDate() + 6);
  weekEnd.setHours(23, 59, 59, 999);

  const weekKey = isoWeekKey(weekStart);
  const outDir = join(baseDir, "data", "benchmark", "collections", weekKey);

  if (existsSync(outDir)) {
    // Overwrite
  }
  mkdirSync(outDir, { recursive: true });

  const targetPosts = TARGET_POSTS_PER_PEER;
  const files: string[] = [];

  // ── 1. collection-checklist.md ──────────────────────
  const checklistLines: string[] = [
    `# Benchmark Weekly Collection Checklist`,
    ``,
    `**Week:** ${weekKey} (${weekStart.toLocaleDateString("vi-VN")} → ${weekEnd.toLocaleDateString("vi-VN")})`,
    `**External Core Peers:** ${peers.length}`,
    `**Target posts/peer:** ${targetPosts}`,
    `**Total target rows:** ${peers.length * targetPosts}`,
    ``,
    `## Quy tắc thu thập`,
    ``,
    `- **Ô trống** = chưa quan sát được (null) — **KHÔNG** phải zero`,
    `- Chỉ điền **0** nếu số công khai thực sự bằng 0`,
    `- **Shares bị ẩn phải để trống** — không ghi thành 0`,
    `- **likes KHÔNG phải followers** — audienceCount = follower/member count thật`,
    `- **KHÔNG** nhập reach, impressions, CTR, watch time`,
    `- capturedAt bắt buộc (YYYY-MM-DD)`,
    `- postUrl bắt buộc (permalink của bài viết)`,
    `- **KHÔNG** dùng Meta Business Suite export cho page đối thủ`,
    ``,
    `## Danh sách thu thập`,
    ``,
  ];

  for (const peer of peers) {
    checklistLines.push(`### ${peer.name}`);
    checklistLines.push(`- **URL:** ${peer.canonicalUrl}`);
    checklistLines.push(`- **Scale band:** ${peer.scaleBand ?? "—"}`);
    checklistLines.push(`- **Category:** ${peer.category ?? "—"}`);
    checklistLines.push(`- **Target posts:** ${targetPosts}`);
    checklistLines.push(`- **Collection frequency:** weekly`);
    checklistLines.push(`- **Current followers:** ${peer.audienceCount ? peer.audienceCount.toLocaleString("vi-VN") : "chưa có — cần cập nhật"}`);
    checklistLines.push(`- **Posts đã có:** ${peer.postCount}`);
    checklistLines.push(`- **Metrics cần ghi:** reactions, comments, shares (nếu nhìn thấy), public video views (nếu nhìn thấy), postedAt, capturedAt, contentType, topicTag`);
    checklistLines.push(``);
  }

  const checklistPath = join(outDir, "collection-checklist.md");
  writeFileSync(checklistPath, checklistLines.join("\n"));
  files.push("collection-checklist.md");

  // ── 2. benchmark-weekly-template.csv ─────────────────
  const templateHeaders = [
    "pageName", "pageUrl", "objectType", "audienceCount", "audienceCountType",
    "postUrl", "postedAt", "textSnippet", "contentType", "topicTag",
    "reactions", "comments", "shares", "publicVideoViews", "capturedAt", "notes",
  ];
  const csvLines: string[] = [
    `# Benchmark Collection Template — Week ${weekKey}`,
    `# Ô trống = chưa quan sát (null) — KHÔNG phải zero`,
    `# Chỉ điền 0 nếu số công khai thực sự bằng 0`,
    `# Shares bị ẩn phải để trống`,
    `# KHÔNG nhập reach, impressions, CTR, watch time`,
    `# likes KHÔNG phải followers`,
    templateHeaders.join(","),
  ];

  for (const peer of peers) {
    for (let i = 0; i < targetPosts; i++) {
      csvLines.push([
        escapeCsv(peer.name),
        escapeCsv(peer.canonicalUrl),
        escapeCsv(peer.objectType),
        peer.audienceCount != null ? String(peer.audienceCount) : "",
        escapeCsv(peer.audienceCountType ?? "followers"),
        "", "", "", "", "", "", "", "", "",
        weekKey, "",
      ].join(","));
    }
  }

  const csvPath = join(outDir, "benchmark-weekly-template.csv");
  writeFileSync(csvPath, csvLines.join("\n") + "\n");
  files.push("benchmark-weekly-template.csv");

  // ── 3. peer-status.csv ────────────────────────────────
  const statusHeaders = [
    "pageName", "pageUrl", "targetPosts", "collectedPosts",
    "audienceSnapshotUpdated", "status", "notes",
  ];
  const statusLines: string[] = [statusHeaders.join(",")];

  for (const peer of peers) {
    const audienceUpdated =
      peer.audienceCapturedAt && (Date.now() - peer.audienceCapturedAt.getTime()) < 30 * 24 * 60 * 60 * 1000
        ? isoWeekKey(peer.audienceCapturedAt)
        : "";
    const status = peer.postCount >= targetPosts ? "complete" : peer.postCount > 0 ? "collecting" : "not_started";

    statusLines.push([
      escapeCsv(peer.name),
      escapeCsv(peer.canonicalUrl),
      String(targetPosts),
      String(peer.postCount),
      audienceUpdated,
      status,
      "",
    ].join(","));
  }

  const statusPath = join(outDir, "peer-status.csv");
  writeFileSync(statusPath, statusLines.join("\n") + "\n");
  files.push("peer-status.csv");

  return {
    weekKey,
    outDir,
    files,
    peerCount: peers.length,
    targetRows: peers.length * targetPosts,
  };
}
