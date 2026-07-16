import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { ok, err } from "@/lib/env";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

/**
 * GET /api/imports/:id/unmatched
 * Danh sách unmatched/ambiguous rows của batch.
 */
export async function GET(_req: Request, ctx: { params: { id: string } }) {
  const id = Number(ctx.params.id);
  if (!Number.isFinite(id)) {
    return err("unknown_error", "id không hợp lệ", 400);
  }
  const rows = await prisma.importedPostInsight.findMany({
    where: {
      batchId: id,
      matchStatus: { in: ["unmatched", "ambiguous"] },
    },
    orderBy: { id: "asc" },
    take: 500,
  });

  return ok({
    rows: rows.map((r) => ({
      ...r,
      rawRow: r.rawRowJson ? JSON.parse(r.rawRowJson) : [],
    })),
  });
}
