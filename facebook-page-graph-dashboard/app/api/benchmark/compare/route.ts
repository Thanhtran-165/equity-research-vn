import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { ok, err, withFbErrors } from "@/lib/env";
import {
  compareOwnPageToPeers,
  deriveSnapshot,
  normalizeCategory,
  type DerivedSnapshot,
  benchmarkCategoryLabel,
} from "@/lib/benchmark";
import { aggregateByTopic, topicLabel } from "@/lib/metrics";

export const dynamic = "force-dynamic";

/**
 * GET /api/benchmark/compare?category=&periodStart=&periodEnd=&weeks=4
 * Tạo/cập nhật OwnPagePublicComparableSnapshot từ internal Graph data đã sync,
 * rồi compare với competitor snapshots cùng filter.
 */
export async function GET(req: Request) {
  return withFbErrors(async () => {
    const url = new URL(req.url);
    const category = url.searchParams.get("category"); // 'all' hoặc key
    const weeksRaw = Number(url.searchParams.get("weeks") ?? "4");
    const weeks = Number.isFinite(weeksRaw) && weeksRaw > 0 ? Math.min(52, weeksRaw) : 4;

    // period từ query hoặc mặc định N tuần gần nhất
    const periodEnd = url.searchParams.get("periodEnd") ?? new Date().toISOString().slice(0, 10);
    const periodStart =
      url.searchParams.get("periodStart") ??
      new Date(Date.now() - (weeks * 7 - 1) * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);

    const pageId = process.env.FB_PAGE_ID ?? "";
    if (!pageId) {
      return err("unknown_error", "Thiếu FB_PAGE_ID trong .env.local", 500);
    }

    // ---- Build own comparable snapshot từ internal data ----
    const startIso = new Date(periodStart + "T00:00:00.000Z").toISOString();
    const endIso = new Date(periodEnd + "T23:59:59.999Z").toISOString();

    const [ownPosts, ownSnapshots, ownVideos] = await Promise.all([
      prisma.post.findMany({
        where: { pageId, createdTime: { gte: startIso, lte: endIso } },
      }),
      prisma.pageSnapshot.findMany({
        where: { pageId, date: { gte: periodStart, lte: periodEnd } },
        orderBy: { date: "asc" },
      }),
      prisma.videoMetric.findMany({
        where: { pageId, createdTime: { gte: startIso, lte: endIso } },
      }),
    ]);

    const ownFollowers = ownSnapshots.at(-1)?.followersCount ?? 0;
    const ownReactions = ownPosts.reduce((s, p) => s + p.reactionsCount, 0);
    const ownComments = ownPosts.reduce((s, p) => s + p.commentsCount, 0);
    const ownShares = ownPosts.reduce((s, p) => s + p.sharesCount, 0);
    const ownVideoViews =
      ownVideos.reduce((s, v) => s + (v.views ?? 0), 0) || null;
    const ownPostsCount = ownPosts.length;

    if (ownPostsCount === 0 && ownFollowers === 0) {
      return err(
        "unknown_error",
        "Chưa có dữ liệu internal (PageSnapshot/Post). Hãy sync Facebook Data và seed trước khi compare.",
        400,
      );
    }

    // Top post engagement (public proxy: reactions + comments + shares)
    const ownTopPost = [...ownPosts]
      .map((p) => ({
        fbPostId: p.fbPostId,
        message: p.message,
        permalinkUrl: p.permalinkUrl,
        eng: p.reactionsCount + p.commentsCount + p.sharesCount,
      }))
      .sort((a, b) => b.eng - a.eng)[0];

    const ownRaw = {
      followers: ownFollowers,
      postsCount: ownPostsCount,
      reactionsCount: ownReactions,
      commentsCount: ownComments,
      sharesCount: ownShares,
      videoViews: ownVideoViews,
      topPostEngagement: ownTopPost?.eng ?? null,
      periodStart,
      periodEnd,
    };
    const ownDerived = deriveSnapshot(ownRaw);

    // Lưu own comparable snapshot
    await prisma.ownPagePublicComparableSnapshot.upsert({
      where: { pageId_periodStart_periodEnd: { pageId, periodStart, periodEnd } },
      update: {
        followers: ownFollowers,
        postsCount: ownPostsCount,
        reactionsCount: ownReactions,
        commentsCount: ownComments,
        sharesCount: ownShares,
        videoViews: ownVideoViews,
        publicEngagement: ownDerived.publicEngagement,
        publicEngagementPerPost: ownDerived.publicEngagementPerPost,
        engagementPer1kFollowers: ownDerived.engagementPer1kFollowers,
        avgReactionsPerPost: ownDerived.avgReactionsPerPost,
        avgCommentsPerPost: ownDerived.avgCommentsPerPost,
        avgSharesPerPost: ownDerived.avgSharesPerPost,
        videoViewsPerFollower: ownDerived.videoViewsPerFollower,
        commentIntensity: ownDerived.commentIntensity,
        shareIntensity: ownDerived.shareIntensity,
        postingFrequencyPerDay: ownDerived.postingFrequencyPerDay,
      },
      create: {
        pageId,
        periodStart,
        periodEnd,
        followers: ownFollowers,
        postsCount: ownPostsCount,
        reactionsCount: ownReactions,
        commentsCount: ownComments,
        sharesCount: ownShares,
        videoViews: ownVideoViews,
        publicEngagement: ownDerived.publicEngagement,
        publicEngagementPerPost: ownDerived.publicEngagementPerPost,
        engagementPer1kFollowers: ownDerived.engagementPer1kFollowers,
        avgReactionsPerPost: ownDerived.avgReactionsPerPost,
        avgCommentsPerPost: ownDerived.avgCommentsPerPost,
        avgSharesPerPost: ownDerived.avgSharesPerPost,
        videoViewsPerFollower: ownDerived.videoViewsPerFollower,
        commentIntensity: ownDerived.commentIntensity,
        shareIntensity: ownDerived.shareIntensity,
        postingFrequencyPerDay: ownDerived.postingFrequencyPerDay,
      },
    });

    // ---- Lấy competitor snapshots (filter theo category/period) ----
    const catFilter =
      category && category !== "all" ? normalizeCategory(category) : null;

    const competitorSnapsRaw = await prisma.competitorMetricSnapshot.findMany({
      where: {
        periodStart,
        periodEnd,
        page: catFilter ? { category: catFilter, isActive: true } : { isActive: true },
      },
      include: { page: true },
    });

    const competitorDerived: DerivedSnapshot[] = competitorSnapsRaw.map((s) => ({
      followers: s.followers,
      postsCount: s.postsCount,
      reactionsCount: s.reactionsCount,
      commentsCount: s.commentsCount,
      sharesCount: s.sharesCount,
      videoViews: s.videoViews,
      topPostEngagement: s.topPostEngagement,
      periodStart: s.periodStart,
      periodEnd: s.periodEnd,
      publicEngagement: s.publicEngagement ?? 0,
      publicEngagementPerPost: s.publicEngagementPerPost,
      engagementPer1kFollowers: s.engagementPer1kFollowers,
      avgReactionsPerPost: s.avgReactionsPerPost,
      avgCommentsPerPost: s.avgCommentsPerPost,
      avgSharesPerPost: s.avgSharesPerPost,
      videoViewsPerFollower: s.videoViewsPerFollower,
      commentIntensity: s.commentIntensity,
      shareIntensity: s.shareIntensity,
      postingFrequencyPerDay: s.postingFrequencyPerDay,
      benchmarkScore: s.benchmarkScore,
      // gắn metadata cho ranked table
      ...({
        pageId: `cmp_${s.competitorPageId}`,
        pageName: s.page?.pageName ?? "—",
        pageUrl: s.page?.pageUrl,
      } as any),
    }));

    const ownPageName =
      process.env.BENCHMARK_OWN_PAGE_NAME ||
      ownSnapshots.at(-1)?.pageName ||
      "Page của bạn";

    const comparison = compareOwnPageToPeers({
      ownSnapshot: { ...ownDerived, ...({ pageId: "__own__", pageName: ownPageName } as any) },
      competitorSnapshots: competitorDerived,
      category: catFilter ?? undefined,
      ownPageName,
    });

    // Topic cluster so sánh trung bình engagementPer1k theo category
    const byCategory: Record<string, DerivedSnapshot[]> = {};
    for (const s of competitorDerived) {
      const cat = (s as any).category ?? "khac";
      // category không có trên snapshot, phải mượn từ page — lấy từ cmp row đã spread?
      // Fallback: dùng dominantTopic
      const key = (s as any).dominantTopic ?? "khac";
      if (!byCategory[key]) byCategory[key] = [];
      byCategory[key].push(s);
    }

    const topicCluster = Object.entries(byCategory).map(([topic, arr]) => {
      const eng = arr
        .map((s) => s.engagementPer1kFollowers)
        .filter((v): v is number => v != null && Number.isFinite(v));
      const engAvg = eng.length ? eng.reduce((a, b) => a + b, 0) / eng.length : null;
      return {
        topic,
        topicLabel: topicLabel(topic),
        pages: arr.length,
        engagementPer1kAvg: engAvg,
      };
    });

    // Best topic của own page (theo post count đã sync)
    const ownTopicAgg = aggregateByTopic(
      ownPosts.map((p) => ({
        topic: p.topic,
        reach: p.reach,
        commentsCount: p.commentsCount,
        sharesCount: p.sharesCount,
        engagementRate: p.engagementRate,
        score: p.score,
      })),
    );
    const bestTopicOwn =
      ownTopicAgg[0]?.topic ?? null;

    return ok({
      periodStart,
      periodEnd,
      category: catFilter,
      categoryLabel: benchmarkCategoryLabel(catFilter),
      ownSnapshot: {
        ...ownDerived,
        pageName: ownPageName,
        topPostUrl: ownTopPost?.permalinkUrl ?? null,
        topPostMessage: ownTopPost?.message ?? null,
      },
      competitorCount: competitorDerived.length,
      comparison,
      topicCluster,
      bestTopicOwn,
      bestTopicOwnLabel: bestTopicOwn ? topicLabel(bestTopicOwn) : null,
      notice:
        "Benchmark dựa trên chỉ số công khai (proxy) của competitor — không phải Facebook Insights private của đối thủ.",
    });
  });
}
