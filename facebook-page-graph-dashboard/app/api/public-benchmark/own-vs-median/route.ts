import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";
import { aggregatePostsToPeriod } from "@/lib/benchmark/periodAggregation";
import { median } from "@/lib/benchmark/publicMetrics";

export const dynamic = "force-dynamic";

/**
 * GET /api/public-benchmark/own-vs-median
 * Compare Chim Cút (own page) against core peer median.
 * Query: ?periodDays=30
 */
export async function GET(req: Request) {
  return withFbErrors(async () => {
    const url = new URL(req.url);
    const periodDays = parseInt(url.searchParams.get("periodDays") ?? "30");

    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - periodDays);

    const ownPage = await prisma.benchmarkPage.findFirst({
      where: { isOwnPage: true },
    });
    if (!ownPage) {
      return ok({ error: "Own page not configured" }, 404);
    }

    const corePeers = await prisma.benchmarkPage.findMany({
      where: { benchmarkRole: "core_peer", isOwnPage: false },
    });

    const allPageIds = [ownPage.id, ...corePeers.map((p) => p.id)];

    const postsRaw = await prisma.benchmarkPost.findMany({
      where: {
        benchmarkPageId: { in: allPageIds },
        OR: [{ postedAt: null }, { postedAt: { gte: startDate, lte: endDate } }],
      },
    });

    // Latest audience per page
    const audienceRaw = await prisma.benchmarkAudienceSnapshot.findMany({
      where: { benchmarkPageId: { in: allPageIds } },
      orderBy: { capturedAt: "desc" },
    });
    const latestAudience = new Map<number, { count: number | null; type: string }>();
    for (const a of audienceRaw) {
      if (!latestAudience.has(a.benchmarkPageId)) {
        latestAudience.set(a.benchmarkPageId, { count: a.audienceCount, type: a.audienceCountType });
      }
    }

    // Aggregate own page
    const ownPosts = postsRaw
      .filter((p) => p.benchmarkPageId === ownPage.id)
      .map((p) => ({
        reactions: p.reactions, comments: p.comments, shares: p.shares,
        publicVideoViews: p.publicVideoViews,
        reactionsObserved: p.reactionsObserved, commentsObserved: p.commentsObserved,
        sharesObserved: p.sharesObserved, publicVideoViewsObserved: p.publicVideoViewsObserved,
        comparableEngagement: p.comparableEngagement,
        observedPublicEngagement: p.observedPublicEngagement,
        metricCoverageScore: p.metricCoverageScore,
      }));
    const ownAgg = aggregatePostsToPeriod(
      ownPosts,
      latestAudience.get(ownPage.id)?.count,
      latestAudience.get(ownPage.id)?.type,
    );

    // Aggregate per peer
    const peerAggs = corePeers.map((peer) => {
      const peerPosts = postsRaw
        .filter((p) => p.benchmarkPageId === peer.id)
        .map((p) => ({
          reactions: p.reactions, comments: p.comments, shares: p.shares,
          publicVideoViews: p.publicVideoViews,
          reactionsObserved: p.reactionsObserved, commentsObserved: p.commentsObserved,
          sharesObserved: p.sharesObserved, publicVideoViewsObserved: p.publicVideoViewsObserved,
          comparableEngagement: p.comparableEngagement,
          observedPublicEngagement: p.observedPublicEngagement,
          metricCoverageScore: p.metricCoverageScore,
        }));
      return {
        pageId: peer.id,
        name: peer.name,
        scaleBand: peer.scaleBand,
        ...aggregatePostsToPeriod(
          peerPosts,
          latestAudience.get(peer.id)?.count,
          latestAudience.get(peer.id)?.type,
        ),
      };
    });

    // Compute peer medians
    const peerMedianComparable = median(peerAggs.map((p) => p.medianComparableEngagementPerPost));
    const peerMedianReactions = median(
      peerAggs.map((p) => (p.totalReactions != null && p.postsCaptured > 0 ? p.totalReactions / p.postsCaptured : null)),
    );
    const peerMedianComments = median(
      peerAggs.map((p) => (p.totalComments != null && p.postsCaptured > 0 ? p.totalComments / p.postsCaptured : null)),
    );
    const peerMedianViral = median(peerAggs.map((p) => p.viralHitRate));
    const peerMedianShareRatio = median(peerAggs.map((p) => p.shareRatio));
    const peerMedianCommentRatio = median(peerAggs.map((p) => p.commentRatio));
    const peerMedianCoverage = median(peerAggs.map((p) => p.metricCoverageScore));

    return ok({
      periodDays,
      ownPage: {
        id: ownPage.id,
        name: ownPage.name,
        audienceCount: latestAudience.get(ownPage.id)?.count ?? null,
        ...ownAgg,
      },
      peerMedian: {
        medianComparableEngagementPerPost: peerMedianComparable,
        avgReactionsPerPost: peerMedianReactions,
        avgCommentsPerPost: peerMedianComments,
        viralHitRate: peerMedianViral,
        shareRatio: peerMedianShareRatio,
        commentRatio: peerMedianCommentRatio,
        metricCoverageScore: peerMedianCoverage,
        peerCount: peerAggs.length,
      },
      peers: peerAggs,
    });
  });
}
