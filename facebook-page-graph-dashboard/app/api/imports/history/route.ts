import { prisma } from "@/lib/prisma";
import { ok } from "@/lib/env";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

/**
 * GET /api/imports/history
 * Danh sách tất cả batch.
 */
export async function GET() {
  const batches = await prisma.insightImportBatch.findMany({
    orderBy: { importedAt: "desc" },
    take: 100,
  });
  return ok({ batches });
}
