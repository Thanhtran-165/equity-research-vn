import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { ok, err } from "@/lib/env";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

/**
 * GET /api/imports/:id
 * Chi tiết batch + một số rows mẫu.
 */
export async function GET(_req: Request, ctx: { params: { id: string } }) {
  const id = Number(ctx.params.id);
  if (!Number.isFinite(id)) {
    return err("unknown_error", "id không hợp lệ", 400);
  }
  const batch = await prisma.insightImportBatch.findUnique({ where: { id } });
  if (!batch) {
    return err("unknown_error", "Batch không tồn tại", 404);
  }
  // 50 rows đầu để preview
  const sampleRows = await prisma.importedPostInsight.findMany({
    where: { batchId: id },
    take: 50,
    orderBy: { id: "asc" },
  });

  return ok({
    batch: {
      ...batch,
      rawColumns: batch.rawColumnsJson ? JSON.parse(batch.rawColumnsJson) : [],
      columnMapping: batch.columnMappingJson ? JSON.parse(batch.columnMappingJson) : null,
    },
    sampleRows: sampleRows.map((r) => ({
      ...r,
      rawRow: r.rawRowJson ? JSON.parse(r.rawRowJson) : [],
    })),
  });
}
