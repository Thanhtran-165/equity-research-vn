import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";
import { syncOwnPagePostsToBenchmark } from "@/lib/benchmark/syncOwnPagePublicMetrics";

export const dynamic = "force-dynamic";

/**
 * POST /api/public-benchmark/sync-own-page
 * Sync Chim Cút's public metrics from Post table into BenchmarkPost.
 * Body: { periodStart?, periodEnd?, limit? }
 */
export async function POST(req: Request) {
  return withFbErrors(async () => {
    const body = await req.json().catch(() => ({}));
    const ownPageUrl = "https://facebook.com/chimcutvnindex";

    const result = await syncOwnPagePostsToBenchmark(prisma, ownPageUrl, {
      periodStart: body.periodStart ? new Date(body.periodStart) : undefined,
      periodEnd: body.periodEnd ? new Date(body.periodEnd) : undefined,
      limit: body.limit ?? 500,
    });

    return ok(result);
  });
}
