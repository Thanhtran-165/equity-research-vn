import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";
import { runQualityChecks } from "@/lib/benchmark/dataQuality";

export const dynamic = "force-dynamic";

/**
 * GET /api/public-benchmark/data-quality
 * Run 10 data quality diagnostic checks.
 */
export async function GET() {
  return withFbErrors(async () => {
    const [
      totalPages,
      corePeers,
      ownPage,
      totalPosts,
      postsWithReactions,
      postsWithComments,
      postsWithShares,
      postsWithComparable,
      postsMissingPostedAt,
    ] = await Promise.all([
      prisma.benchmarkPage.count(),
      prisma.benchmarkPage.count({ where: { benchmarkRole: "core_peer" } }),
      prisma.benchmarkPage.findFirst({ where: { isOwnPage: true } }),
      prisma.benchmarkPost.count(),
      prisma.benchmarkPost.count({ where: { reactionsObserved: true } }),
      prisma.benchmarkPost.count({ where: { commentsObserved: true } }),
      prisma.benchmarkPost.count({ where: { sharesObserved: true } }),
      prisma.benchmarkPost.count({ where: { comparableEngagement: { not: null } } }),
      prisma.benchmarkPost.count({ where: { postedAt: null } }),
    ]);

    // Pages with/without posts
    const pagesWithPostsRaw = await prisma.benchmarkPost.groupBy({
      by: ["benchmarkPageId"],
      _count: true,
    });
    const pagesWithPosts = new Set(pagesWithPostsRaw.map((p) => p.benchmarkPageId));

    // Posts with neither reactions nor comments
    const postsWithNeither = await prisma.benchmarkPost.count({
      where: {
        AND: [
          { reactionsObserved: false },
          { commentsObserved: false },
        ],
      },
    });

    // Non-facebook_page in core peers
    const nonPageInCorePeers = await prisma.benchmarkPage.count({
      where: {
        benchmarkRole: "core_peer",
        objectType: { not: "facebook_page" },
      },
    });

    // Duplicate postUrls
    const allPostUrls = await prisma.benchmarkPost.findMany({
      select: { postUrl: true },
    });
    const urlCounts = new Map<string, number>();
    for (const p of allPostUrls) {
      urlCounts.set(p.postUrl, (urlCounts.get(p.postUrl) ?? 0) + 1);
    }
    const duplicatePostUrls = Array.from(urlCounts.values()).filter((c) => c > 1).length;

    // Median coverage score
    const allCoverage = await prisma.benchmarkPost.findMany({
      where: { metricCoverageScore: { not: null } },
      select: { metricCoverageScore: true },
    });
    const coverageValues = allCoverage
      .map((p) => p.metricCoverageScore)
      .filter((v): v is number => v != null)
      .sort((a, b) => a - b);
    const medianCoverage =
      coverageValues.length === 0
        ? null
        : coverageValues.length % 2 !== 0
          ? coverageValues[Math.floor(coverageValues.length / 2)]
          : (coverageValues[coverageValues.length / 2 - 1] + coverageValues[coverageValues.length / 2]) / 2;

    // Freshness
    const newestPost = await prisma.benchmarkPost.findFirst({
      where: { postedAt: { not: null } },
      orderBy: { postedAt: "desc" },
      select: { postedAt: true },
    });
    const oldestPost = await prisma.benchmarkPost.findFirst({
      where: { postedAt: { not: null } },
      orderBy: { postedAt: "asc" },
      select: { postedAt: true },
    });
    const now = new Date();
    const daysSince = (d: Date | null): number | null => {
      if (!d) return null;
      return Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24));
    };

    const report = runQualityChecks({
      totalPages,
      corePeerCount: corePeers,
      ownPagePresent: !!ownPage,
      totalPosts,
      postsWithReactions,
      postsWithComments,
      postsWithShares,
      postsWithComparableEngagement: postsWithComparable,
      postsWithNeitherReactionsNorComments: postsWithNeither,
      pagesWithPosts: pagesWithPosts.size,
      pagesWithoutPosts: totalPages - pagesWithPosts.size,
      zeroMetricCount: 0, // Tracked elsewhere
      medianCoverageScore: medianCoverage,
      oldestPostDays: daysSince(oldestPost?.postedAt ?? null),
      newestPostDays: daysSince(newestPost?.postedAt ?? null),
      duplicatePostUrls,
      nonPageInCorePeers,
      watchlistWithPosts: 0,
      postsMissingPostedAt,
    });

    return ok(report);
  });
}
