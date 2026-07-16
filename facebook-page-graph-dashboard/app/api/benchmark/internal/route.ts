import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";
import { computeInternalBenchmark } from "@/lib/internalBenchmark";

export const dynamic = "force-dynamic";

/**
 * GET /api/benchmark/internal
 * Tính internal benchmark từ tất cả Post trong DB (có reach hoặc engagement).
 */
export async function GET() {
  return withFbErrors(async () => {
    const posts = await prisma.post.findMany({
      where: {
        OR: [
          { reach: { not: null } },
          { reactionsCount: { gt: 0 } },
          { commentsCount: { gt: 0 } },
        ],
      },
      select: {
        fbPostId: true,
        message: true,
        topic: true,
        postType: true,
        createdTime: true,
        reach: true,
        impressions: true,
        reactionsCount: true,
        commentsCount: true,
        sharesCount: true,
        clicks: true,
        videoViews: true,
        engagementRate: true,
        metricSource: true,
      },
    });

    const benchmark = computeInternalBenchmark(
      posts.map((p) => ({
        ...p,
        createdTime: p.createdTime ?? null,
        reach: p.reach ?? null,
        impressions: p.impressions ?? null,
        clicks: p.clicks ?? null,
        videoViews: p.videoViews ?? null,
        engagementRate: p.engagementRate ?? null,
        metricSource: p.metricSource ?? null,
        message: p.message ?? null,
      })),
    );

    if (!benchmark) {
      return ok({ benchmark: null, message: "Chưa có đủ dữ liệu để tính benchmark." });
    }

    return ok({ benchmark });
  });
}
