import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { ok, err } from "@/lib/env";
import { detectFormat, parseFileBuffer } from "@/lib/imports/parseFile";
import { normalizeRows } from "@/lib/imports/normalizeRows";
import { matchRows, type CandidatePost } from "@/lib/imports/matchPosts";
import { applyImportedInsights } from "@/lib/imports/applyImportedInsights";
import { detectTopic } from "@/lib/topics";
import type { ColumnMapping } from "@/lib/imports/columnDetection";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

/**
 * POST /api/imports/apply
 * Body: { batchId, forceOverwrite?, allowVideoViewsOverwrite? }
 *
 * Cần file gốc (không lưu file → user phải re-upload qua endpoint mới hoặc dùng cache).
 * Để đơn giản: route này nhận batchId, parse lại file từ /imports/incoming nếu có,
 * hoặc nhận file qua FormData cùng lúc.
 */
export async function POST(req: Request) {
  try {
    // Cho phép 2 mode:
    // 1. FormData với file + batchId (re-upload cùng file để apply)
    // 2. JSON body { batchId } — yêu cầu file đã có trong /imports/incoming
    const contentType = req.headers.get("content-type") ?? "";
    let batchId: number;
    let forceOverwrite = false;
    let allowVideoViewsOverwrite = false;
    let fileBuffer: Buffer | null = null;
    let filename = "";

    if (contentType.includes("multipart/form-data")) {
      const formData = await req.formData();
      const file = formData.get("file");
      if (file instanceof File) {
        fileBuffer = Buffer.from(await file.arrayBuffer());
        filename = file.name;
      }
      batchId = Number(formData.get("batchId") ?? 0);
      forceOverwrite = formData.get("forceOverwrite") === "true";
      allowVideoViewsOverwrite = formData.get("allowVideoViewsOverwrite") === "true";
    } else {
      const body = await req.json();
      batchId = Number(body?.batchId);
      forceOverwrite = Boolean(body?.forceOverwrite);
      allowVideoViewsOverwrite = Boolean(body?.allowVideoViewsOverwrite);
    }

    if (!Number.isFinite(batchId) || batchId <= 0) {
      return err("unknown_error", "Thiếu batchId hợp lệ", 400);
    }

    const batch = await prisma.insightImportBatch.findUnique({ where: { id: batchId } });
    if (!batch) {
      return err("unknown_error", "Batch không tồn tại", 404);
    }

    // Load file từ /imports/incoming nếu chưa có buffer
    if (!fileBuffer) {
      const incomingPath = `${process.cwd()}/imports/incoming/${batch.filename}`;
      try {
        const fs = await import("fs/promises");
        fileBuffer = await fs.readFile(incomingPath);
        filename = batch.filename;
      } catch {
        return err(
          "unknown_error",
          `Không tìm thấy file gốc "${batch.filename}". Hãy re-upload file qua FormData với field 'file'.`,
          400,
        );
      }
    }

    if (!detectFormat(filename)) {
      return err("unknown_error", "File không đúng định dạng (.csv/.xlsx/.xls)", 400);
    }

    // Parse lại
    const parsed = parseFileBuffer(fileBuffer, filename);

    // Lấy mapping từ batch (đã confirm), hoặc auto-detect nếu chưa confirm
    const mapping: ColumnMapping = batch.columnMappingJson
      ? JSON.parse(batch.columnMappingJson)
      : (await import("@/lib/imports/columnDetection")).detectColumns(parsed.headers).mapping;

    // Check if this is a Posts file (has postId column) — only apply Posts files to Post model
    const isPostsFile = mapping.postId != null || parsed.headers.some((h) =>
      h.toLowerCase().includes("id bài viết") || h.toLowerCase().includes("post id")
    );

    if (!isPostsFile) {
      // Skip Video/Page files — they need their own schema (VideoAsset, VideoDailyMetric, etc.)
      await prisma.insightImportBatch.update({
        where: { id: batchId },
        data: {
          status: "imported",
          notes: `SKIPPED — không phải Posts file (Video/Page). Cần schema riêng (VideoAsset/VideoDailyMetric).`,
        },
      });
      return ok({
        batchId,
        skipped: true,
        reason: "File không phải Posts (Video hoặc Page level) — không apply vào Post model. Sẽ xử lý qua schema VideoAsset/VideoDailyMetric ở phase sau.",
        rowCount: parsed.rows.length,
      });
    }

    // Normalize rows
    const normalized = normalizeRows(parsed.rows, mapping);
    const warnings: { fbPostId: string; message: string }[] = [];

    // Detect paid impressions column (if header contains "quảng cáo" / "ad" / "paid")
    const paidImpressionsCol = parsed.headers.findIndex((h) => {
      const hl = h.toLowerCase();
      return (hl.includes("hiển thị") || hl.includes("impressions")) &&
             (hl.includes("quảng cáo") || hl.includes("paid") || hl.includes("ad"));
    });
    if (paidImpressionsCol >= 0) {
      warnings.push({
        fbPostId: "(header)",
        message: `Paid impressions ignored for organic dashboard: cột "${parsed.headers[paidImpressionsCol]}" (col ${paidImpressionsCol}) là paid/ads metric, KHÔNG phải organic impressions.`,
      });
    }

    // Lấy tất cả post trong DB để match
    const dbPosts = await prisma.post.findMany({
      select: { fbPostId: true, permalinkUrl: true, message: true, createdTime: true, pageId: true },
    });
    const candidates: CandidatePost[] = dbPosts.map((p) => ({
      fbPostId: p.fbPostId,
      permalinkUrl: p.permalinkUrl,
      message: p.message,
      createdTime: p.createdTime,
      pageId: p.pageId,
    }));

    // Match
    const matchResults = matchRows(normalized, candidates);

    // Apply + create ImportedPostInsight records
    let matchedCount = 0;
    let unmatchedCount = 0;
    let ambiguousCount = 0;
    let skippedCount = 0;
    let appliedCount = 0;
    // warnings already declared above (SyncWarning[])

    // Xoá ImportedPostInsight cũ của batch (nếu re-apply)
    await prisma.importedPostInsight.deleteMany({ where: { batchId } });

    for (let i = 0; i < normalized.length; i++) {
      const row = normalized[i];
      const match = matchResults[i];

      let matchedPostId: string | null = null;
      if (match.status === "matched" && match.matchedPostId) {
        matchedPostId = match.matchedPostId;
        matchedCount++;
      } else if (match.status === "ambiguous") {
        ambiguousCount++;
      } else if (match.status === "unmatched") {
        unmatchedCount++;
        // Auto-import row vào Post collection với metricSource = meta_business_suite_csv
        // để dashboard hiển thị data CSV kể cả khi không match với post sync qua Graph API.
        // Dùng postId từ CSV làm fbPostId (nếu có); fallback permalink hash.
        if (row.postId || row.permalinkUrl) {
          const fallbackId = row.postId
            ? `csv_${row.postId}`
            : `csv_${require("crypto").createHash("md5").update(row.permalinkUrl ?? "").digest("hex").slice(0, 16)}`;
          try {
            await prisma.post.upsert({
              where: { fbPostId: fallbackId },
              create: {
                fbPostId: fallbackId,
                pageId: process.env.FB_PAGE_ID ?? "imported",
                message: row.messageSnippet,
                permalinkUrl: row.permalinkUrl,
                createdTime: row.createdTime,
                postType: "imported",
                topic: detectTopic(row.messageSnippet ?? undefined),
                reactionsCount: row.reactions ?? 0,
                commentsCount: row.comments ?? 0,
                sharesCount: row.shares ?? 0,
                reach: row.reach,
                impressions: row.impressions,
                engagedUsers: row.engagedUsers,
                clicks: row.clicks,
                videoViews: row.videoViews,
                metricSource: "meta_business_suite_csv",
                engagementRate:
                  row.reach != null && row.reach > 0
                    ? ((row.reactions ?? 0) + (row.comments ?? 0) + (row.shares ?? 0) + (row.clicks ?? 0)) / row.reach
                    : null,
                rawJson: JSON.stringify({ imported: true, batchId, source: "meta_business_suite_csv" }),
              },
              update: {
                message: row.messageSnippet ?? undefined,
                permalinkUrl: row.permalinkUrl ?? undefined,
                reach: row.reach ?? undefined,
                impressions: row.impressions ?? undefined,
                engagedUsers: row.engagedUsers ?? undefined,
                clicks: row.clicks ?? undefined,
                videoViews: row.videoViews ?? undefined,
                reactionsCount: row.reactions ?? undefined,
                commentsCount: row.comments ?? undefined,
                sharesCount: row.shares ?? undefined,
                metricSource: "meta_business_suite_csv",
                engagementRate:
                  row.reach != null && row.reach > 0
                    ? ((row.reactions ?? 0) + (row.comments ?? 0) + (row.shares ?? 0) + (row.clicks ?? 0)) / row.reach
                    : null,
              },
            });
            matchedPostId = fallbackId;
            // Đếm như "matched" vì đã import thành công vào Post collection
            appliedCount++;
          } catch (e: any) {
            warnings.push({ fbPostId: row.postId ?? "?", message: `Cannot auto-import row: ${e?.message ?? e}` });
          }
        }
      } else {
        skippedCount++;
      }

      // Insert ImportedPostInsight record
      await prisma.importedPostInsight.create({
        data: {
          batchId,
          source: "meta_business_suite_csv",
          postId: row.postId,
          permalinkUrl: row.permalinkUrl,
          externalContentId: row.externalContentId,
          createdTime: row.createdTime,
          messageSnippet: row.messageSnippet,
          reach: row.reach,
          impressions: row.impressions,
          engagedUsers: row.engagedUsers,
          clicks: row.clicks,
          reactions: row.reactions,
          comments: row.comments,
          shares: row.shares,
          videoViews: row.videoViews,
          watchTime: row.watchTime,
          rawRowJson: row.rawRowJson,
          matchStatus: match.status,
          matchedPostId,
          matchConfidence: match.confidence,
        },
      });

      // Apply metrics vào Post nếu matched
      if (match.status === "matched" && matchedPostId) {
        const currentPost = await prisma.post.findUnique({
          where: { fbPostId: matchedPostId },
          select: { metricSource: true, videoViews: true, reach: true },
        });
        if (!currentPost) continue;

        const result = applyImportedInsights({
          row,
          match,
          currentMetricSource: currentPost.metricSource,
          currentVideoViews: currentPost.videoViews,
          forceOverwrite,
          allowVideoViewsOverwrite,
        });

        if (result.shouldApply && result.patch) {
          await prisma.post.update({
            where: { fbPostId: matchedPostId },
            data: result.patch as any,
          });
          appliedCount++;
        } else {
          warnings.push({ fbPostId: matchedPostId, message: result.reason });
        }
      }
    }

    // Update batch status
    await prisma.insightImportBatch.update({
      where: { id: batchId },
      data: {
        status: "imported",
        matchedCount,
        unmatchedCount: unmatchedCount + ambiguousCount,
        skippedCount,
        notes: warnings.slice(0, 50).map((w) => `${w.fbPostId}: ${w.message}`).join("\n") || null,
      },
    });

    return ok({
      batchId,
      rowCount: normalized.length,
      matchedCount,
      unmatchedCount,
      ambiguousCount,
      skippedCount,
      appliedCount,
      warnings: warnings.slice(0, 20),
    });
  } catch (e: any) {
    return err("unknown_error", e?.message ?? String(e), 500);
  }
}
