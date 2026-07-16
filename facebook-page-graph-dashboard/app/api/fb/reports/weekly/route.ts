import { prisma } from "@/lib/prisma";
import { aggregateByTopic, topicLabel } from "@/lib/metrics";
import { detectCommentSpike } from "@/lib/metrics";
import { ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

function viDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

/**
 * GET /api/fb/reports/weekly
 * Báo cáo tuần từ database. Query: ?weeksAgo=0 (mặc định = tuần hiện tại).
 */
export async function GET(req: Request) {
  return withFbErrors(async () => {
    const url = new URL(req.url);
    const weeksAgoRaw = Number(url.searchParams.get("weeksAgo") ?? "0");
    const weeksAgo = Number.isFinite(weeksAgoRaw) ? Math.max(0, weeksAgoRaw) : 0;

    const now = new Date();
    // Đầu tuần (thứ 2)
    const day = now.getDay(); // 0 = Sun
    const diffToMonday = (day === 0 ? -6 : 1 - day) - weeksAgo * 7;
    const weekStart = new Date(now);
    weekStart.setDate(now.getDate() + diffToMonday);
    weekStart.setHours(0, 0, 0, 0);
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 6);
    weekEnd.setHours(23, 59, 59, 999);

    const weekStartStr = viDate(weekStart);
    const weekEndStr = viDate(weekEnd);

    // Lấy post trong tuần (dựa createdTime)
    const posts = await prisma.post.findMany({
      where: {
        createdTime: { gte: weekStart.toISOString(), lte: weekEnd.toISOString() },
      },
      orderBy: { createdTime: "desc" },
    });

    const reachTotal = posts.reduce((s, p) => s + (p.reach ?? 0), 0);
    const engagementTotal = posts.reduce(
      (s, p) => s + p.reactionsCount + p.commentsCount + p.sharesCount + (p.clicks ?? 0),
      0,
    );

    // Follower delta trong tuần
    const snapshots = await prisma.pageSnapshot.findMany({
      where: { date: { gte: weekStartStr, lte: weekEndStr } },
      orderBy: { date: "asc" },
    });
    const followerDelta = snapshots.reduce((s, sn) => s + (sn.followersDelta ?? 0), 0);

    // Top post
    const topReachPost = [...posts].sort((a, b) => (b.reach ?? 0) - (a.reach ?? 0))[0] ?? null;
    const topCommentPost = [...posts].sort((a, b) => b.commentsCount - a.commentsCount)[0] ?? null;
    const topEngagementRatePost = [...posts]
      .filter((p) => p.engagementRate != null)
      .sort((a, b) => (b.engagementRate ?? 0) - (a.engagementRate ?? 0))[0] ?? null;

    // Topic comparison
    const topicComparison = aggregateByTopic(
      posts.map((p) => ({
        topic: p.topic,
        reach: p.reach,
        commentsCount: p.commentsCount,
        sharesCount: p.sharesCount,
        engagementRate: p.engagementRate,
        score: p.score,
      })),
    );
    const topTopic = topicComparison[0]?.topic ?? null;

    // Moderation risk summary
    const comments = await prisma.comment.findMany({
      where: { createdTime: { gte: weekStart.toISOString(), lte: weekEnd.toISOString() } },
    });
    const moderationRiskSummary = {
      total: comments.length,
      high: comments.filter((c) => c.riskLevel === "high").length,
      medium: comments.filter((c) => c.riskLevel === "medium").length,
      low: comments.filter((c) => c.riskLevel === "low").length,
    };

    const spikes = detectCommentSpike(
      posts.map((p) => ({
        fbPostId: p.fbPostId,
        commentsCount: p.commentsCount,
        message: p.message,
      })),
    );

    // Summary tiếng Việt
    const summary = buildViSummary({
      weekStart: weekStartStr,
      weekEnd: weekEndStr,
      postsCount: posts.length,
      reachTotal,
      engagementTotal,
      followerDelta,
      topTopic,
      moderationRiskSummary,
    });

    const recommendation = buildViRecommendation({
      topTopic,
      topicComparison,
      moderationRiskSummary,
      spikesCount: spikes.length,
    });

    // Lưu WeeklyReport (upsert theo weekStart)
    const report = await prisma.weeklyReport.upsert({
      where: { weekStart_weekEnd: { weekStart: weekStartStr, weekEnd: weekEndStr } },
      update: {
        reachTotal,
        engagementTotal,
        followerDelta,
        topPostId: topReachPost?.fbPostId ?? null,
        topTopic,
        summary,
        recommendation,
      },
      create: {
        weekStart: weekStartStr,
        weekEnd: weekEndStr,
        reachTotal,
        engagementTotal,
        followerDelta,
        topPostId: topReachPost?.fbPostId ?? null,
        topTopic,
        summary,
        recommendation,
      },
    });

    return ok({
      weekStart: weekStartStr,
      weekEnd: weekEndStr,
      reachTotal,
      engagementTotal,
      followerDelta,
      topReachPost: topReachPost && serializePost(topReachPost),
      topCommentPost: topCommentPost && serializePost(topCommentPost),
      topEngagementRatePost: topEngagementRatePost && serializePost(topEngagementRatePost),
      topTopic,
      topTopicLabel: topTopic ? topicLabel(topTopic) : null,
      topicComparison,
      moderationRiskSummary,
      commentSpikes: spikes,
      summary,
      recommendation,
      savedReportId: report.id,
    });
  });
}

function serializePost(p: any) {
  return {
    fbPostId: p.fbPostId,
    message: p.message,
    permalinkUrl: p.permalinkUrl,
    topic: p.topic,
    topicLabel: topicLabel(p.topic),
    createdTime: p.createdTime,
    reach: p.reach,
    impressions: p.impressions,
    reactionsCount: p.reactionsCount,
    commentsCount: p.commentsCount,
    sharesCount: p.sharesCount,
    clicks: p.clicks,
    engagementRate: p.engagementRate,
    score: p.score,
  };
}

function buildViSummary(x: {
  weekStart: string;
  weekEnd: string;
  postsCount: number;
  reachTotal: number;
  engagementTotal: number;
  followerDelta: number;
  topTopic: string | null;
  moderationRiskSummary: { total: number; high: number; medium: number; low: number };
}): string {
  const deltaStr =
    x.followerDelta > 0 ? `+${x.followerDelta}` : `${x.followerDelta}`;
  return (
    `Tuần ${x.weekStart} → ${x.weekEnd}: ` +
    `${x.postsCount} bài viết, ` +
    `tổng reach ${(x.reachTotal).toLocaleString("vi-VN")}, ` +
    `tổng tương tác ${x.engagementTotal.toLocaleString("vi-VN")}, ` +
    `follower ${deltaStr}. ` +
    (x.topTopic ? `Chủ đề nổi bật: ${topicLabel(x.topTopic)}. ` : "") +
    `Bình luận rủi ro cao: ${x.moderationRiskSummary.high}.`
  );
}

function buildViRecommendation(x: {
  topTopic: string | null;
  topicComparison: any[];
  moderationRiskSummary: { total: number; high: number; medium: number; low: number };
  spikesCount: number;
}): string {
  const parts: string[] = [];
  if (x.topTopic) {
    parts.push(
      `Tiếp tục đẩy mạnh nội dung nhóm "${topicLabel(x.topTopic)}" vì đang đạt reach cao nhất tuần.`,
    );
  }
  const weak = [...x.topicComparison].sort((a, b) => a.reachTotal - b.reachTotal)[0];
  if (weak && weak.postsCount > 0 && weak.topic !== x.topTopic) {
    parts.push(
      `Nhóm "${topicLabel(weak.topic)}" đang yếu → cân nhắc giảm tần suất hoặc đổi góc nội dung.`,
    );
  }
  if (x.moderationRiskSummary.high > 0) {
    parts.push(
      `Có ${x.moderationRiskSummary.high} comment rủi ro cao cần kiểm duyệt nhanh để tránh tổn thương thương hiệu.`,
    );
  }
  if (x.spikesCount > 0) {
    parts.push(
      `Phát hiện ${x.spikesCount} bài có lượng comment tăng bất thường → kiểm tra xem có sự kiện tiêu cực không.`,
    );
  }
  return parts.join(" ");
}
