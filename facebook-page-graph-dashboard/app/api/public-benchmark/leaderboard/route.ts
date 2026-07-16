import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";
import { isLeaderboardEligible } from "@/lib/benchmark/publicMetrics";
import { aggregatePostsToPeriod } from "@/lib/benchmark/periodAggregation";

export const dynamic = "force-dynamic";

/**
 * GET /api/public-benchmark/leaderboard
 * Query: ?mode=direct|comparable|all & ?scaleBand= & ?periodDays=7|30|90
 *
 * Direct leaderboard: only facebook_page core peers + own page.
 * Comparable leaderboard: defaults to reactions + comments (comparableEngagement).
 */
export async function GET(req: Request) {
  return withFbErrors(async () => {
    const url = new URL(req.url);
    const mode = (url.searchParams.get("mode") ?? "direct") as "direct" | "comparable" | "all";
    const scaleBand = url.searchParams.get("scaleBand");
    const periodDays = parseInt(url.searchParams.get("periodDays") ?? "30");

    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - periodDays);

    // Determine which pages qualify
    const where: { [key: string]: unknown } = {};
    if (mode === "direct") {
      where.OR = [
        { objectType: "facebook_page", benchmarkRole: "core_peer" },
        { isOwnPage: true, objectType: "facebook_page" },
      ];
    }
    if (scaleBand) {
      where.scaleBand = scaleBand;
    }

    const pages = await prisma.benchmarkPage.findMany({
      where,
      orderBy: [{ isOwnPage: "desc" }, { name: "asc" }],
    });

    // Filter to leaderboard-eligible only for direct mode
    const eligiblePages = pages.filter((p) =>
      isLeaderboardEligible(p.objectType, p.benchmarkRole, p.isOwnPage),
    );

    // Get latest audience snapshot per page
    const pageIds = eligiblePages.map((p) => p.id);

    const postsRaw = await prisma.benchmarkPost.findMany({
      where: {
        benchmarkPageId: { in: pageIds },
        OR: [
          { postedAt: null },
          { postedAt: { gte: startDate, lte: endDate } },
        ],
      },
    });

    // Get latest audience per page
    const audienceRaw = await prisma.benchmarkAudienceSnapshot.findMany({
      where: { benchmarkPageId: { in: pageIds } },
      orderBy: { capturedAt: "desc" },
    });
    const latestAudience = new Map<number, { count: number | null; type: string }>();
    for (const a of audienceRaw) {
      if (!latestAudience.has(a.benchmarkPageId)) {
        latestAudience.set(a.benchmarkPageId, { count: a.audienceCount, type: a.audienceCountType });
      }
    }

    const rows = eligiblePages.map((page) => {
      const posts = postsRaw
        .filter((p) => p.benchmarkPageId === page.id)
        .map((p) => ({
          reactions: p.reactions,
          comments: p.comments,
          shares: p.shares,
          publicVideoViews: p.publicVideoViews,
          reactionsObserved: p.reactionsObserved,
          commentsObserved: p.commentsObserved,
          sharesObserved: p.sharesObserved,
          publicVideoViewsObserved: p.publicVideoViewsObserved,
          comparableEngagement: p.comparableEngagement,
          observedPublicEngagement: p.observedPublicEngagement,
          metricCoverageScore: p.metricCoverageScore,
        }));

      const agg = aggregatePostsToPeriod(
        posts,
        latestAudience.get(page.id)?.count,
        latestAudience.get(page.id)?.type,
      );

      return {
        pageId: page.id,
        name: page.name,
        canonicalUrl: page.canonicalUrl,
        isOwnPage: page.isOwnPage,
        scaleBand: page.scaleBand,
        category: page.category,
        benchmarkRole: page.benchmarkRole,
        audienceCount: latestAudience.get(page.id)?.count ?? null,
        audienceCountType: latestAudience.get(page.id)?.type ?? null,
        ...agg,
      };
    });

    // Sort by median comparable engagement (descending)
    rows.sort((a, b) => {
      const av = a.medianComparableEngagementPerPost;
      const bv = b.medianComparableEngagementPerPost;
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      return bv - av;
    });

    return ok({
      mode,
      periodDays,
      scaleBand: scaleBand ?? null,
      pageCount: rows.length,
      rows,
    });
  });
}
