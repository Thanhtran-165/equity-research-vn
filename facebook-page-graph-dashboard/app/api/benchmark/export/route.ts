import { prisma } from "@/lib/prisma";
import { toCsv, csvFilename } from "@/lib/csv";

export const dynamic = "force-dynamic";

/**
 * GET /api/benchmark/export
 * Xuất competitor pages + snapshots + own comparable snapshot ra CSV.
 */
export async function GET() {
  const snaps = await prisma.competitorMetricSnapshot.findMany({
    include: { page: true },
    orderBy: [{ periodStart: "desc" }, { periodEnd: "desc" }],
  });

  const headers = [
    "pageName",
    "pageUrl",
    "category",
    "periodStart",
    "periodEnd",
    "followers",
    "postsCount",
    "reactionsCount",
    "commentsCount",
    "sharesCount",
    "videoViews",
    "publicEngagement",
    "publicEngagementPerPost",
    "engagementPer1kFollowers",
    "avgReactionsPerPost",
    "avgCommentsPerPost",
    "avgSharesPerPost",
    "videoViewsPerFollower",
    "commentIntensity",
    "shareIntensity",
    "postingFrequencyPerDay",
    "benchmarkScore",
    "activeAds",
    "dominantTopic",
    "topPostUrl",
    "topPostEngagement",
  ];

  const rows = snaps.map((s) => ({
    pageName: s.page?.pageName ?? "",
    pageUrl: s.page?.pageUrl ?? "",
    category: s.page?.category ?? "",
    periodStart: s.periodStart,
    periodEnd: s.periodEnd,
    followers: s.followers,
    postsCount: s.postsCount,
    reactionsCount: s.reactionsCount,
    commentsCount: s.commentsCount,
    sharesCount: s.sharesCount,
    videoViews: s.videoViews ?? "",
    publicEngagement: s.publicEngagement ?? "",
    publicEngagementPerPost: s.publicEngagementPerPost ?? "",
    engagementPer1kFollowers: s.engagementPer1kFollowers ?? "",
    avgReactionsPerPost: s.avgReactionsPerPost ?? "",
    avgCommentsPerPost: s.avgCommentsPerPost ?? "",
    avgSharesPerPost: s.avgSharesPerPost ?? "",
    videoViewsPerFollower: s.videoViewsPerFollower ?? "",
    commentIntensity: s.commentIntensity ?? "",
    shareIntensity: s.shareIntensity ?? "",
    postingFrequencyPerDay: s.postingFrequencyPerDay ?? "",
    benchmarkScore: s.benchmarkScore ?? "",
    activeAds: s.activeAds == null ? "" : s.activeAds ? "true" : "false",
    dominantTopic: s.dominantTopic ?? "",
    topPostUrl: s.topPostUrl ?? "",
    topPostEngagement: s.topPostEngagement ?? "",
  }));

  const csv = toCsv(rows, headers);
  const filename = csvFilename("benchmark");
  return new Response(csv, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="${filename}"`,
    },
  });
}
