import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";
import {
  computeVideoSummary,
  aggregateDaily,
  aggregateMonthly,
  topActiveVideos,
  detectVideoAnomalies,
  computeSocialER,
  computeAvgWatchPerView,
} from "@/lib/videoAggregations";

export const dynamic = "force-dynamic";

/**
 * GET /api/video-dashboard
 * Query: ?startDate=&endDate=&sort=
 */
export async function GET(req: Request) {
  return withFbErrors(async () => {
    const url = new URL(req.url);
    const startDate = url.searchParams.get("startDate");
    const endDate = url.searchParams.get("endDate");
    const sort = url.searchParams.get("sort") ?? "videoViews3s";

    // Lifetime metrics (all — not date-filtered)
    const lifetimeRaw = await prisma.videoLifetimeMetric.findMany({
      include: { videoAsset: true },
    });

    // Get total assets and asset ID sets
    const totalAssets = await prisma.videoAsset.count();
    const dailyAssetIdsRaw = await prisma.videoDailyMetric.findMany({
      select: { videoAssetId: true },
      distinct: ["videoAssetId"],
    });
    const dailyAssetIds = dailyAssetIdsRaw.map((d) => d.videoAssetId);
    const lifetimeAssetIds = lifetimeRaw.map((m) => m.videoAssetId);

    const lifetime = lifetimeRaw.map((m) => ({
      videoAssetId: m.videoAssetId,
      externalVideoId: m.videoAsset.externalVideoId,
      title: m.videoAsset.title,
      reach: m.reach,
      videoViews3s: m.videoViews3s,
      videoViews1min: m.videoViews1min,
      watchTimeSeconds: m.watchTimeSeconds,
      avgWatchTime: m.avgWatchTime,
      reactions: m.reactions,
      comments: m.comments,
      shares: m.shares,
      matchedPostId: m.videoAsset.matchedPostId,
      socialER: computeSocialER(m.reactions ?? 0, m.comments ?? 0, m.shares ?? 0, m.reach ?? 0),
      avgWatchPerView: computeAvgWatchPerView(m.watchTimeSeconds ?? 0, m.videoViews3s ?? 0),
    }));

    // Sort lifetime
    const sortKey = sort as "videoViews3s" | "reach" | "watchTimeSeconds" | "socialER" | "avgWatchPerView";
    const validSort = ["videoViews3s", "reach", "watchTimeSeconds", "socialER", "avgWatchPerView"].includes(sort)
      ? sortKey
      : "videoViews3s";
    lifetime.sort((a: any, b: any) => (b[validSort] ?? 0) - (a[validSort] ?? 0));

    // Daily metrics (date-filtered)
    const dailyWhere: any = {};
    if (startDate) dailyWhere.date = { gte: startDate };
    if (endDate) dailyWhere.date = { ...(dailyWhere.date || {}), lte: endDate };

    const dailyRaw = await prisma.videoDailyMetric.findMany({
      where: dailyWhere,
      include: { videoAsset: { select: { externalVideoId: true, title: true } } },
      orderBy: { date: "asc" },
    });

    const daily = aggregateDaily(dailyRaw);
    const monthly = aggregateMonthly(daily);

    // Fix uniqueVideos: compute distinct videoAssetId per month from raw rows
    const monthlyVideoSets: Record<string, Set<number>> = {};
    for (const r of dailyRaw) {
      const m = r.date.slice(0, 7);
      if (!monthlyVideoSets[m]) monthlyVideoSets[m] = new Set();
      monthlyVideoSets[m].add(r.videoAssetId);
    }
    for (const m of monthly) {
      m.uniqueVideos = monthlyVideoSets[m.month]?.size ?? m.uniqueVideos;
    }

    const topActive = topActiveVideos(dailyRaw, 20);
    const summary = computeVideoSummary(
      lifetimeRaw.map((m) => ({
        videoAssetId: m.videoAssetId,
        externalVideoId: m.videoAsset.externalVideoId,
        title: m.videoAsset.title,
        reach: m.reach,
        videoViews3s: m.videoViews3s,
        videoViews1min: m.videoViews1min,
        watchTimeSeconds: m.watchTimeSeconds,
        avgWatchTime: m.avgWatchTime,
        reactions: m.reactions,
        comments: m.comments,
        shares: m.shares,
        matchedPostId: m.videoAsset.matchedPostId,
      })),
      dailyRaw.length,
      {
        min: dailyRaw[0]?.date ?? null,
        max: dailyRaw[dailyRaw.length - 1]?.date ?? null,
      },
      totalAssets,
      dailyAssetIds,
      lifetimeAssetIds,
    );

    const anomalies = detectVideoAnomalies(
      lifetimeRaw.map((m) => ({
        videoAssetId: m.videoAssetId,
        externalVideoId: m.videoAsset.externalVideoId,
        title: m.videoAsset.title,
        reach: m.reach,
        videoViews3s: m.videoViews3s,
        videoViews1min: m.videoViews1min,
        watchTimeSeconds: m.watchTimeSeconds,
        avgWatchTime: m.avgWatchTime,
        reactions: m.reactions,
        comments: m.comments,
        shares: m.shares,
        matchedPostId: m.videoAsset.matchedPostId,
      })),
    );

    return ok({
      summary,
      lifetime: lifetime.slice(0, 50),
      daily,
      monthly,
      topActive,
      anomalies,
      sort,
      dateRange: summary.dateRange,
    });
  });
}
