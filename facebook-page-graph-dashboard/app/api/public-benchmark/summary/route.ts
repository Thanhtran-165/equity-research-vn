import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

/**
 * GET /api/public-benchmark/summary
 * High-level summary of benchmark state.
 */
export async function GET() {
  return withFbErrors(async () => {
    const [
      totalPages,
      externalCorePeers,
      ownPage,
      totalPosts,
      postsWithReactions,
      postsWithComments,
      postsWithShares,
    ] = await Promise.all([
      prisma.benchmarkPage.count(),
      prisma.benchmarkPage.count({ where: { benchmarkRole: "core_peer", isOwnPage: false } }),
      prisma.benchmarkPage.findFirst({ where: { isOwnPage: true } }),
      prisma.benchmarkPost.count(),
      prisma.benchmarkPost.count({ where: { reactionsObserved: true } }),
      prisma.benchmarkPost.count({ where: { commentsObserved: true } }),
      prisma.benchmarkPost.count({ where: { sharesObserved: true } }),
    ]);

    const pagesByRole = await prisma.benchmarkPage.groupBy({
      by: ["benchmarkRole"],
      _count: true,
    });

    const pagesByScale = await prisma.benchmarkPage.groupBy({
      by: ["scaleBand"],
      _count: true,
    });

    const pagesWithPosts = await prisma.benchmarkPost.groupBy({
      by: ["benchmarkPageId"],
      _count: true,
    });

    const referenceSources =
      (pagesByRole.find((r) => r.benchmarkRole === "topic_reference")?._count ?? 0) +
      (pagesByRole.find((r) => r.benchmarkRole === "format_reference")?._count ?? 0) +
      (pagesByRole.find((r) => r.benchmarkRole === "creator_reference")?._count ?? 0) +
      (pagesByRole.find((r) => r.benchmarkRole === "group_reference")?._count ?? 0) +
      (pagesByRole.find((r) => r.benchmarkRole === "cross_platform_reference")?._count ?? 0);
    const watchlistSources = pagesByRole.find((r) => r.benchmarkRole === "watchlist")?._count ?? 0;

    return ok({
      totalPages,
      // Entity reconciliation: Chim Cút is NOT a peer
      externalCorePeers,
      ownPages: ownPage ? 1 : 0,
      directLeaderboardEntities: externalCorePeers + (ownPage ? 1 : 0),
      referenceSources,
      watchlistSources,
      totalExternalSources: totalPages - (ownPage ? 1 : 0),
      totalSourcesIncludingOwnPage: totalPages,
      // Legacy field kept for backward compat
      corePeers: externalCorePeers,
      ownPagePresent: !!ownPage,
      ownPageId: ownPage?.id ?? null,
      totalPosts,
      coverage: {
        reactions: totalPosts > 0 ? postsWithReactions / totalPosts : 0,
        comments: totalPosts > 0 ? postsWithComments / totalPosts : 0,
        shares: totalPosts > 0 ? postsWithShares / totalPosts : 0,
      },
      pagesByRole: pagesByRole.reduce(
        (acc, r) => ({ ...acc, [r.benchmarkRole]: r._count }),
        {} as Record<string, number>,
      ),
      pagesByScaleBand: pagesByScale.reduce(
        (acc, r) => ({ ...acc, [r.scaleBand ?? "unknown"]: r._count }),
        {} as Record<string, number>,
      ),
      pagesWithPostCount: pagesWithPosts.length,
      pagesWithoutPosts: totalPages - pagesWithPosts.length,
    });
  });
}
