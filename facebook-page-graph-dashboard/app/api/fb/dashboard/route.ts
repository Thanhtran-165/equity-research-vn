import { prisma } from "@/lib/prisma";
import { aggregateByTopic, detectCommentSpike } from "@/lib/metrics";
import { ok, withFbErrors } from "@/lib/env";

// Local helper — auto-detect default dashboard view mode.
// (Tách ra pure function để testable, xem lib/__tests__/dashboardMode.test.ts)
function detectDefaultViewMode(args: {
  totalPosts: number;
  trueReachCount: number;
  publicOrVideoCount: number;
}): "insights" | "public" | "mixed" {
  const { totalPosts, trueReachCount, publicOrVideoCount } = args;
  if (totalPosts === 0) return "public";
  if (trueReachCount >= totalPosts / 2) return "insights";
  if (trueReachCount === 0) return "public";
  if (trueReachCount > 0 && publicOrVideoCount > 0) return "mixed";
  return "insights";
}

export const dynamic = "force-dynamic";

/**
 * GET /api/fb/dashboard
 * Trả 3 metric KHÔNG trộn theo nguyên tắc của phản biện:
 *  - totalTrueReach       : tổng reach thật (chỉ từ post_impressions_unique)
 *  - totalVideoViews      : tổng video views (metric riêng, không phải reach)
 *  - totalPublicEngagement: tổng reactions + comments + shares (proxy, không phải reach)
 *
 * engagementRate CHỈ tính cho post có trueReach.
 */
export async function GET() {
  return withFbErrors(async () => {
    const [latestSnapshot, prevSnapshot] = await prisma.pageSnapshot.findMany({
      orderBy: { date: "desc" },
      take: 2,
    });

    // Tăng take để bao gồm cả post cũ import từ CSV (MBS CSV có thể là post từ 2021-2025).
    const posts = await prisma.post.findMany({
      orderBy: { createdTime: "desc" },
      take: 500,
    });

    // 3 metric tách biệt — KHÔNG cộng chung
    const totalTrueReach = posts.reduce((s, p) => s + (p.reach ?? 0), 0);
    const totalVideoViews = posts.reduce((s, p) => s + (p.videoViews ?? 0), 0);
    const totalPublicEngagement = posts.reduce((s, p) => s + (p.publicEngagement ?? 0), 0);

    // Số post theo metricSource.
    // Backward-compat: gộp "public_engagement_proxy" cũ vào "facebook_public_metrics".
    const isPublicMetrics = (s: string | null | undefined) =>
      s === "facebook_public_metrics" || s === "public_engagement_proxy";
    // trueReach bao gồm: Graph API insights + Meta Business Suite CSV (cả 2 là insight thật).
    const isTrueReachSource = (s: string | null | undefined) =>
      s === "facebook_graph_api_insights" || s === "meta_business_suite_csv";
    const postsWithTrueReach = posts.filter((p) => isTrueReachSource(p.metricSource)).length;
    const postsWithMbsCsv = posts.filter((p) => p.metricSource === "meta_business_suite_csv").length;
    const postsWithVideoViews = posts.filter((p) => p.metricSource === "facebook_video_metric").length;
    const postsWithPublicEngagement = posts.filter((p) => isPublicMetrics(p.metricSource)).length;
    const postsUnavailable = posts.filter((p) => p.metricSource === "unavailable" || !p.metricSource).length;

    // Auto-detect dashboard mode mặc định:
    // - "insights": ĐA SỐ (>50%) bài có trueReach
    // - "public": KHÔNG có bài nào có trueReach, chỉ có public/video
    // - "mixed": có cả trueReach (it nhất 1) LẪN public/video
    const defaultViewMode: "insights" | "public" | "mixed" =
      posts.length === 0
        ? "public"
        : postsWithTrueReach >= posts.length / 2
        ? "insights"
        : postsWithTrueReach === 0
        ? "public"
        : "mixed";

    // Engagement rate chỉ tính cho post có trueReach (facebook_graph_api_insights hoặc meta_business_suite_csv).
    // KHÔNG silently cap ER — giữ số thật, kèm warning flag nếu ER cực đoan (>1.0).
    const engRatesRaw = posts
      .filter((p) => isTrueReachSource(p.metricSource))
      .map((p) => p.engagementRate)
      .filter((v): v is number => v != null && Number.isFinite(v) && v > 0);
    const avgEngagementRate = engRatesRaw.length
      ? engRatesRaw.reduce((a, b) => a + b, 0) / engRatesRaw.length
      : null;
    const extremeErCount = engRatesRaw.filter((v) => v > 1.0).length;

    const totalComments = posts.reduce((s, p) => s + p.commentsCount, 0);

    const spikes = detectCommentSpike(
      posts.slice(0, 25).map((p) => ({
        fbPostId: p.fbPostId,
        commentsCount: p.commentsCount,
        message: p.message,
      })),
    );

    // Top posts: rank theo trueReach trước, fallback theo videoViews, fallback theo publicEngagement
    const topPosts = [...posts]
      .sort((a, b) => {
        const aVal = a.reach ?? a.videoViews ?? a.publicEngagement ?? 0;
        const bVal = b.reach ?? b.videoViews ?? b.publicEngagement ?? 0;
        return bVal - aVal;
      })
      .slice(0, 10)
      .map((p) => ({
        fbPostId: p.fbPostId,
        message: p.message,
        topic: p.topic,
        postType: p.postType,
        createdTime: p.createdTime,
        permalinkUrl: p.permalinkUrl,
        reach: p.reach,
        videoViews: p.videoViews,
        publicEngagement: p.publicEngagement,
        metricSource: p.metricSource,
        impressions: p.impressions,
        reactionsCount: p.reactionsCount,
        commentsCount: p.commentsCount,
        sharesCount: p.sharesCount,
        clicks: p.clicks,
        engagementRate: p.engagementRate,
        score: p.score,
      }));

    const topicPerformance = aggregateByTopic(
      posts.map((p) => ({
        topic: p.topic,
        reach: p.reach,
        commentsCount: p.commentsCount,
        sharesCount: p.sharesCount,
        engagementRate: p.engagementRate,
        score: p.score,
      })),
    );

    const followersCount = latestSnapshot?.followersCount ?? 0;
    const followerDelta =
      latestSnapshot && prevSnapshot
        ? latestSnapshot.followersCount - prevSnapshot.followersCount
        : (latestSnapshot?.followersDelta ?? 0);

    const followerHistory = await prisma.pageSnapshot.findMany({
      where: { pageId: latestSnapshot?.pageId ?? process.env.FB_PAGE_ID ?? "" },
      orderBy: { date: "asc" },
      take: 30,
      select: { date: true, followersCount: true, followersDelta: true },
    });

    return ok({
      page: {
        pageId: latestSnapshot?.pageId ?? process.env.FB_PAGE_ID ?? "",
        pageName: latestSnapshot?.pageName ?? "",
      },
      followers: followersCount,
      followerDelta,
      // 3 metric tách biệt rõ ràng
      totalTrueReach,
      totalVideoViews,
      totalPublicEngagement,
      // Số post theo nguồn metric
      metricSourceBreakdown: {
        facebook_graph_api_insights: posts.filter((p) => p.metricSource === "facebook_graph_api_insights").length,
        meta_business_suite_csv: postsWithMbsCsv,
        facebook_video_metric: postsWithVideoViews,
        facebook_public_metrics: postsWithPublicEngagement, // gộp cả legacy public_engagement_proxy
        public_engagement_proxy: postsWithPublicEngagement, // backward-compat, deprecated
        unavailable: postsUnavailable,
      },
      defaultViewMode,
      totalPosts: posts.length,
      // ER chỉ hợp lệ khi có trueReach
      avgEngagementRate,
      avgEngagementRateNote:
        postsWithTrueReach > 0
          ? `Tính trên ${postsWithTrueReach}/${posts.length} post có trueReach`
          : "Không có post nào có trueReach — ER không khả dụng",
      extremeEngagementRateCount: extremeErCount,
      extremeEngagementRateWarning:
        extremeErCount > 0
          ? `${extremeErCount} post có ER > 100% — có thể do reach thật thấp hoặc metric bị nhiễu, không nên dùng làm benchmark.`
          : null,
      totalComments,
      commentSpikeCount: spikes.length,
      commentSpikes: spikes,
      topPosts,
      topicPerformance,
      lastSnapshotDate: latestSnapshot?.date ?? null,
      followerHistory,
    });
  });
}
