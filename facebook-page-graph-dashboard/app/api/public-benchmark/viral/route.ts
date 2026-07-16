import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

/**
 * GET /api/public-benchmark/viral
 * Get top viral posts across all pages (highest comparable engagement).
 * Query: ?limit=20 & ?periodDays=30 & ?multiplier=3
 */
export async function GET(req: Request) {
  return withFbErrors(async () => {
    const url = new URL(req.url);
    const limit = Math.min(parseInt(url.searchParams.get("limit") ?? "20"), 100);
    const periodDays = parseInt(url.searchParams.get("periodDays") ?? "30");

    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - periodDays);

    const posts = await prisma.benchmarkPost.findMany({
      where: {
        comparableEngagement: { not: null },
        OR: [{ postedAt: null }, { postedAt: { gte: startDate, lte: endDate } }],
      },
      orderBy: { comparableEngagement: "desc" },
      take: limit,
      include: {
        page: {
          select: { name: true, canonicalUrl: true, isOwnPage: true, scaleBand: true, benchmarkRole: true },
        },
      },
    });

    return ok({
      periodDays,
      total: posts.length,
      posts: posts.map((p) => ({
        id: p.id,
        postUrl: p.postUrl,
        postedAt: p.postedAt,
        textSnippet: p.textSnippet,
        contentType: p.contentType,
        topicTag: p.topicTag,
        reactions: p.reactions,
        comments: p.comments,
        shares: p.shares,
        publicVideoViews: p.publicVideoViews,
        comparableEngagement: p.comparableEngagement,
        observedPublicEngagement: p.observedPublicEngagement,
        shareRatio: p.shares != null && p.observedPublicEngagement != null && p.observedPublicEngagement > 0
          ? p.shares / p.observedPublicEngagement
          : null,
        page: p.page,
      })),
    });
  });
}
