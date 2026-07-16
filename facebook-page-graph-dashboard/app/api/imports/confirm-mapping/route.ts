import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { ok, err } from "@/lib/env";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

/**
 * POST /api/imports/confirm-mapping
 * Body: { batchId, columnMapping }
 * Update columnMappingJson cho batch + status = "mapped".
 */
export async function POST(req: Request) {
  try {
    const body = await req.json();
    const batchId = Number(body?.batchId);
    const mapping = body?.columnMapping;

    if (!Number.isFinite(batchId)) {
      return err("unknown_error", "Thiếu batchId", 400);
    }
    if (!mapping || typeof mapping !== "object") {
      return err("unknown_error", "Thiếu columnMapping", 400);
    }

    const batch = await prisma.insightImportBatch.findUnique({ where: { id: batchId } });
    if (!batch) {
      return err("unknown_error", "Batch không tồn tại", 404);
    }

    const updated = await prisma.insightImportBatch.update({
      where: { id: batchId },
      data: {
        columnMappingJson: JSON.stringify(mapping),
        status: "mapped",
      },
    });

    return ok({ batch: updated });
  } catch (e: any) {
    return err("unknown_error", e?.message ?? String(e), 500);
  }
}
