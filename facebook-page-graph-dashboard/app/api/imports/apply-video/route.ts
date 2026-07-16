import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { ok, err } from "@/lib/env";
import { parseFileBuffer } from "@/lib/imports/parseFile";
import { normalizeRows } from "@/lib/imports/normalizeRows";
import { detectColumns } from "@/lib/imports/columnDetection";
import { parseDate } from "@/lib/imports/normalizeRows";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

interface VideoApplyResult {
  batchId: number;
  videoAssetsCreated: number;
  videoAssetsUpdated: number;
  videoAssetsTotal: number;
  lifetimeMetricsApplied: number;
  dailyMetricsApplied: number;
  dailyMetricsUpdated: number;
  rowsSkipped: number;
  rowsMissingVideoId: number;
  rowsMissingDate: number;
  conflicts: string[];
  warnings: string[];
}

/**
 * POST /api/imports/apply-video
 * Body: { batchId }
 *
 * Applies video CSV files (V01 lifetime + V02 daily) into VideoAsset + VideoLifetimeMetric + VideoDailyMetric.
 * Does NOT touch Post model.
 */
export async function POST(req: Request) {
  let body: any;
  try {
    body = await req.json();
  } catch {
    return err("unknown_error", "Body không phải JSON hợp lệ", 400);
  }

  const batchId = Number(body?.batchId);
  if (!Number.isFinite(batchId) || batchId <= 0) {
    return err("unknown_error", "Thiếu batchId hợp lệ", 400);
  }

  const batch = await prisma.insightImportBatch.findUnique({ where: { id: batchId } });
  if (!batch) {
    return err("unknown_error", "Batch không tồn tại", 404);
  }

  // Load file
  const fs = await import("fs/promises");
  let fileBuffer: Buffer;
  try {
    fileBuffer = await fs.readFile(`${process.cwd()}/imports/incoming/${batch.filename}`);
  } catch {
    return err("unknown_error", `Không tìm thấy file "${batch.filename}"`, 400);
  }

  const parsed = parseFileBuffer(fileBuffer, batch.filename);

  // Detect if this is video file
  const isVideo = parsed.headers.some((h) =>
    h.toLowerCase().includes("id tài sản video") || h.toLowerCase().includes("video asset id")
  );
  if (!isVideo) {
    return err("unknown_error", "File không phải video export (thiếu 'ID tài sản video')", 400);
  }

  // Column mapping: use batch mapping or auto-detect
  const detection = detectColumns(parsed.headers);
  const mapping = batch.columnMappingJson
    ? JSON.parse(batch.columnMappingJson)
    : detection.mapping;

  // Find video asset ID column — "ID tài sản video"
  const videoIdCol = parsed.headers.findIndex((h) => {
    const hl = h.toLowerCase();
    return hl.includes("id tài sản video") || hl.includes("video asset id") || hl.includes("id video");
  });
  // Find shared video ID column
  const sharedVideoIdCol = parsed.headers.findIndex((h) =>
    h.toLowerCase().includes("id video chung") || h.toLowerCase().includes("shared video id")
  );
  // Find date column
  const dateCol = parsed.headers.findIndex((h) => h.toLowerCase().trim() === "ngày" || h.toLowerCase().trim() === "date");
  // Find title column
  const titleCol = parsed.headers.findIndex((h) =>
    h.toLowerCase().includes("tiêu đề") || h.toLowerCase().includes("title")
  );
  // Find createdTime column
  const createdTimeCol = parsed.headers.findIndex((h) =>
    h.toLowerCase().includes("thời gian đăng") || h.toLowerCase().includes("posted") || h.toLowerCase().includes("created")
  );
  // Find duration column
  const durationCol = parsed.headers.findIndex((h) =>
    h.toLowerCase().includes("thời lượng") || h.toLowerCase().includes("duration")
  );

  // Determine if this is daily (has "Ngày" column with different dates per row) or lifetime
  const sampleDates = parsed.rows.slice(0, 10).map((r) => dateCol >= 0 ? r[dateCol] : "");
  const hasVariedDates = sampleDates.filter(Boolean).length > 3 && new Set(sampleDates).size > 1;
  const isDaily = dateCol >= 0 && hasVariedDates;

  const result: VideoApplyResult = {
    batchId,
    videoAssetsCreated: 0,
    videoAssetsUpdated: 0,
    videoAssetsTotal: 0,
    lifetimeMetricsApplied: 0,
    dailyMetricsApplied: 0,
    dailyMetricsUpdated: 0,
    rowsSkipped: 0,
    rowsMissingVideoId: 0,
    rowsMissingDate: 0,
    conflicts: [],
    warnings: [...detection.warnings],
  };

  // Page ID from first row (column 2 typically)
  const pageIdCol = parsed.headers.findIndex((h) => h.toLowerCase().includes("id trang") || h.toLowerCase().includes("page id"));
  const pageId = pageIdCol >= 0 ? parsed.rows[0]?.[pageIdCol] : null;

  for (let i = 0; i < parsed.rows.length; i++) {
    const row = parsed.rows[i];
    const rawVideoId = videoIdCol >= 0 ? row[videoIdCol]?.trim() : "";
    const rawDate = dateCol >= 0 ? row[dateCol]?.trim() : "";
    const title = titleCol >= 0 ? row[titleCol]?.trim() : null;
    const createdTime = createdTimeCol >= 0 ? row[createdTimeCol]?.trim() : null;
    const duration = durationCol >= 0 ? parseInt(row[durationCol]) || null : null;
    const sharedVideoId = sharedVideoIdCol >= 0 ? row[sharedVideoIdCol]?.trim() || null : null;

    if (!rawVideoId) {
      result.rowsMissingVideoId++;
      result.rowsSkipped++;
      continue;
    }

    // Normalize row metrics using column detection
    const normalized = normalizeRows([row], mapping)[0];

    // Upsert VideoAsset
    let asset = await prisma.videoAsset.findUnique({
      where: { externalVideoId: rawVideoId },
    });

    if (!asset) {
      asset = await prisma.videoAsset.create({
        data: {
          externalVideoId: rawVideoId,
          sharedVideoId,
          pageId: pageId || null,
          title: title || null,
          createdTime: createdTime ? parseDate(createdTime) : null,
          durationSeconds: duration,
        },
      });
      result.videoAssetsCreated++;
    } else {
      // Update non-null fields only
      await prisma.videoAsset.update({
        where: { id: asset.id },
        data: {
          title: title || undefined,
          sharedVideoId: sharedVideoId || undefined,
          createdTime: createdTime ? parseDate(createdTime) ?? undefined : undefined,
          durationSeconds: duration ?? undefined,
        },
      });
      result.videoAssetsUpdated++;
    }
    result.videoAssetsTotal++;

    if (isDaily) {
      // V02: Daily metric
      const parsedDate = parseDate(rawDate);
      if (!parsedDate) {
        result.rowsMissingDate++;
        result.rowsSkipped++;
        continue;
      }
      const dateStr = parsedDate.slice(0, 10);

      const existing = await prisma.videoDailyMetric.findUnique({
        where: {
          videoAssetId_date_source: {
            videoAssetId: asset.id,
            date: dateStr,
            source: "meta_business_suite_csv",
          },
        },
      });

      const metricData = {
        reach: normalized.reach,
        videoViews3s: normalized.videoViews,
        watchTimeSeconds: normalized.watchTime,
        reactions: normalized.reactions,
        comments: normalized.comments,
        shares: normalized.shares,
        source: "meta_business_suite_csv",
        importBatchId: batchId,
        rawRowJson: JSON.stringify(row),
      };

      if (existing) {
        // Update non-null only
        await prisma.videoDailyMetric.update({
          where: { id: existing.id },
          data: {
            reach: metricData.reach ?? existing.reach ?? undefined,
            videoViews3s: metricData.videoViews3s ?? existing.videoViews3s ?? undefined,
            watchTimeSeconds: metricData.watchTimeSeconds ?? existing.watchTimeSeconds ?? undefined,
            reactions: metricData.reactions ?? existing.reactions ?? undefined,
            comments: metricData.comments ?? existing.comments ?? undefined,
            shares: metricData.shares ?? existing.shares ?? undefined,
          },
        });
        result.dailyMetricsUpdated++;
      } else {
        await prisma.videoDailyMetric.create({
          data: {
            videoAssetId: asset.id,
            date: dateStr,
            ...metricData,
          },
        });
        result.dailyMetricsApplied++;
      }
    } else {
      // V01: Lifetime metric
      const existing = await prisma.videoLifetimeMetric.findUnique({
        where: { videoAssetId: asset.id },
      });

      const metricData = {
        reach: normalized.reach,
        videoViews3s: normalized.videoViews,
        watchTimeSeconds: normalized.watchTime,
        reactions: normalized.reactions,
        comments: normalized.comments,
        shares: normalized.shares,
        source: "meta_business_suite_csv",
        importBatchId: batchId,
        rawRowJson: JSON.stringify(row),
      };

      if (existing) {
        // Update non-null only (don't overwrite non-null with null)
        await prisma.videoLifetimeMetric.update({
          where: { id: existing.id },
          data: {
            reach: metricData.reach ?? existing.reach ?? undefined,
            videoViews3s: metricData.videoViews3s ?? existing.videoViews3s ?? undefined,
            watchTimeSeconds: metricData.watchTimeSeconds ?? existing.watchTimeSeconds ?? undefined,
            reactions: metricData.reactions ?? existing.reactions ?? undefined,
            comments: metricData.comments ?? existing.comments ?? undefined,
            shares: metricData.shares ?? existing.shares ?? undefined,
          },
        });
        result.lifetimeMetricsApplied++;
      } else {
        await prisma.videoLifetimeMetric.create({
          data: { videoAssetId: asset.id, ...metricData },
        });
        result.lifetimeMetricsApplied++;
      }
    }
  }

  // Update batch status
  await prisma.insightImportBatch.update({
    where: { id: batchId },
    data: {
      status: "imported",
      rowCount: parsed.rows.length,
      matchedCount: result.videoAssetsTotal,
      notes: `Video ${isDaily ? "Daily" : "Lifetime"}: ${result.videoAssetsCreated} created, ${result.videoAssetsUpdated} updated, ${isDaily ? result.dailyMetricsApplied + result.dailyMetricsUpdated : result.lifetimeMetricsApplied} metrics. ${result.rowsSkipped} skipped.`,
    },
  });

  return ok({
    type: isDaily ? "V02-daily" : "V01-lifetime",
    ...result,
    totalRows: parsed.rows.length,
    headers: parsed.headers,
    mapping,
    warnings: result.warnings,
  });
}
