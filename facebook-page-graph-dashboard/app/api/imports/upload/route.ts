import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { ok, err } from "@/lib/env";
import { detectColumns } from "@/lib/imports/columnDetection";
import { parseFileBuffer, hashFileBuffer } from "@/lib/imports/parseFile";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

/**
 * POST /api/imports/upload
 * Nhận FormData file (.csv/.xlsx/.xls), parse, detect columns, trả preview.
 * Tạo InsightImportBatch với status="pending" (chưa apply).
 */
export async function POST(req: Request) {
  try {
    const formData = await req.formData();
    const file = formData.get("file");
    if (!(file instanceof File)) {
      return err("unknown_error", "Thiếu field 'file' trong FormData", 400);
    }

    const filename = file.name;
    const buf = Buffer.from(await file.arrayBuffer());

    // Parse
    const parsed = parseFileBuffer(buf, filename);

    // Detect columns
    const detection = detectColumns(parsed.headers);

    // Hash để dedupe
    const fileHash = await hashFileBuffer(buf);

    // Check duplicate
    const existing = await prisma.insightImportBatch.findUnique({ where: { fileHash } });
    if (existing) {
      return ok({
        duplicate: true,
        existingBatchId: existing.id,
        filename: existing.filename,
        importedAt: existing.importedAt,
        status: existing.status,
      });
    }

    // Tạo batch mới
    const batch = await prisma.insightImportBatch.create({
      data: {
        filename,
        source: "meta_business_suite_csv",
        fileHash,
        rowCount: parsed.rows.length,
        status: "pending",
        rawColumnsJson: JSON.stringify(parsed.headers),
        columnMappingJson: JSON.stringify(detection.mapping),
        notes: detection.warnings.join("\n") || null,
      },
    });

    // Preview 20 dòng đầu
    const preview = parsed.rows.slice(0, 20).map((row, i) => {
      const obj: Record<string, string> = {};
      parsed.headers.forEach((h, idx) => {
        obj[h] = row[idx] ?? "";
      });
      return { _rowIndex: i + 1, ...obj };
    });

    // Detect if file might be Activity-filter (video-only) based on filename
    const lowerFilename = filename.toLowerCase();
    const isActivityFile = lowerFilename.includes("activity");
    const isPostsFile = lowerFilename.includes("posts") || lowerFilename.includes("post");
    const videoOnlyWarning =
      isActivityFile && isPostsFile
        ? "⚠️ File có 'activity' + 'posts' trong tên — Meta cảnh báo Activity filter chỉ trả về video posts. Dữ liệu này KHÔNG đại diện cho toàn bộ bài viết."
        : null;

    const allWarnings = [...detection.warnings];
    if (videoOnlyWarning) allWarnings.unshift(videoOnlyWarning);

    return ok({
      batchId: batch.id,
      filename,
      format: parsed.format,
      rowCount: parsed.rows.length,
      headers: parsed.headers,
      mapping: detection.mapping,
      warnings: allWarnings,
      ambiguousFields: detection.ambiguousFields,
      videoOnlyActivityFile: isActivityFile && isPostsFile,
      preview,
      meta: parsed.meta,
    });
  } catch (e: any) {
    return err("unknown_error", e?.message ?? String(e), 500);
  }
}
