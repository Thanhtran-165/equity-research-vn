import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

/**
 * GET /api/public-benchmark/period-snapshots
 * List pre-computed period snapshots.
 * Query: ?pageId= & ?periodType=weekly|monthly & ?limit=50
 */
export async function GET(req: Request) {
  return withFbErrors(async () => {
    const url = new URL(req.url);
    const pageId = url.searchParams.get("pageId");
    const periodType = url.searchParams.get("periodType");
    const limit = Math.min(parseInt(url.searchParams.get("limit") ?? "50"), 200);

    const where: { [key: string]: unknown } = {};
    if (pageId) where.benchmarkPageId = parseInt(pageId);
    if (periodType) where.periodType = periodType;

    const snapshots = await prisma.benchmarkPeriodSnapshot.findMany({
      where,
      orderBy: [{ periodStart: "desc" }],
      take: limit,
      include: {
        page: {
          select: { name: true, canonicalUrl: true, isOwnPage: true, scaleBand: true },
        },
      },
    });

    return ok({ total: snapshots.length, snapshots });
  });
}
