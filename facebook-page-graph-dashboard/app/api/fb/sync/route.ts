import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import {
  FacebookApiError,
  getPageId,
  getPageInfo,
  getPostInsights,
  getRecentPosts,
  type FbPostRaw,
} from "@/lib/facebook";
import { determineMetricSource } from "@/lib/metricSource";
import { detectTopic, TOPIC_LABEL_VI } from "@/lib/topics";
import { calculateEngagementRate, calculatePostScore } from "@/lib/metrics";
import { ok, err, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

interface SyncWarning {
  fbPostId: string;
  message: string;
}

function detectPostType(raw: FbPostRaw): string {
  const attachments = raw.attachments?.data ?? [];
  if (attachments.length === 0) return raw.message ? "text" : "unknown";
  const first = attachments[0];
  const mediaType: string | undefined = first?.media_type;
  const type: string | undefined = first?.type;
  if (mediaType === "video" || type === "video_inline" || type === "video") return "video_or_reel";
  if (mediaType === "photo" || type === "photo") return "photo";
  if (type === "share" || type === "link") return "link";
  if (mediaType === "album") return "photo";
  return "unknown";
}

/**
 * POST /api/fb/sync
 * Sync dữ liệu Page + 25 bài gần nhất + insights vào SQLite.
 * Không fail toàn bộ nếu 1 post insight lỗi.
 */
export async function POST() {
  return withFbErrors(async () => {
    const pageId = getPageId();
    if (!pageId) {
      return err("missing_token", "Thiếu FB_PAGE_ID trong .env.local", 500);
    }

    // a. Page info + snapshot
    const info = await getPageInfo();
    const today = new Date().toISOString().slice(0, 10);

    const prevSnapshot = await prisma.pageSnapshot.findFirst({
      where: { pageId },
      orderBy: { date: "desc" },
    });
    const followersDelta = prevSnapshot
      ? info.followersCount - prevSnapshot.followersCount
      : 0;

    await prisma.pageSnapshot.upsert({
      where: { pageId_date: { pageId, date: today } },
      update: {
        pageName: info.name,
        followersCount: info.followersCount,
        fanCount: info.fanCount,
        followersDelta,
      },
      create: {
        date: today,
        pageId,
        pageName: info.name,
        followersCount: info.followersCount,
        fanCount: info.fanCount,
        followersDelta,
      },
    });

    // c. Lấy 25 bài gần nhất
    // Sync limit có thể override qua env hoặc query param. Default 25 (gần đây),
    // set cao hơn (vd 100, 250) khi cần import CSV với post cũ.
    const syncLimit = Number(process.env.SYNC_LIMIT ?? 100);
    const rawPosts = await getRecentPosts(syncLimit);

    // Bước 1: upsert tất cả post trước (insights có thể fail từng cái)
    type Draft = {
      fbPostId: string;
      pageId: string;
      message: string | null;
      permalinkUrl: string | null;
      createdTime: string | null;
      postType: string;
      topic: string;
      reactionsCount: number;
      commentsCount: number;
      sharesCount: number;
    };

    const drafts: Draft[] = rawPosts.map((r) => {
      const topic = detectTopic(r.message);
      return {
        fbPostId: r.id,
        pageId,
        message: r.message ?? null,
        permalinkUrl: r.permalink_url ?? null,
        createdTime: r.created_time ?? null,
        postType: detectPostType(r),
        topic,
        reactionsCount: r.reactions?.summary?.total_count ?? 0,
        commentsCount: r.comments?.summary?.total_count ?? 0,
        sharesCount: r.shares?.count ?? 0,
      };
    });

    // Upsert bản nháp để có row để tính score & insight append
    for (const d of drafts) {
      await prisma.post.upsert({
        where: { fbPostId: d.fbPostId },
        update: {
          message: d.message,
          permalinkUrl: d.permalinkUrl,
          createdTime: d.createdTime,
          postType: d.postType,
          topic: d.topic,
          reactionsCount: d.reactionsCount,
          commentsCount: d.commentsCount,
          sharesCount: d.sharesCount,
        },
        create: {
          ...d,
          rawJson: JSON.stringify({ source: "sync" }),
        },
      });
    }

    // d. Lấy insight từng post, không fail toàn bộ
    const warnings: SyncWarning[] = [];
    let failedInsights = 0;
    let trueReachCount = 0;
    let videoViewsCount = 0;
    let publicEngagementCount = 0;
    let unavailableCount = 0;

    for (const d of drafts) {
      try {
        const ins = await getPostInsights(d.fbPostId);
        for (const w of ins.warnings) warnings.push({ fbPostId: d.fbPostId, message: w });

        // metricSource dựa trên SỰ TỒN TẠI của dữ liệu (không phải > 0).
        // Logic tách ra helper `determineMetricSource` để testable.
        const metricSource = determineMetricSource({
          reach: ins.reach ?? null,
          videoViews: ins.videoViews ?? null,
          publicEngagement: ins.publicEngagement ?? null,
        });

        if (metricSource === "facebook_graph_api_insights") trueReachCount++;
        else if (metricSource === "facebook_video_metric") videoViewsCount++;
        else if (metricSource === "facebook_public_metrics") publicEngagementCount++;
        else unavailableCount++;

        await prisma.post.update({
          where: { fbPostId: d.fbPostId },
          data: {
            // KHÔNG ghi đè reach bằng proxy nữa — reach chỉ chứa trueReach
            reach: ins.reach ?? null,
            impressions: ins.impressions ?? null,
            engagedUsers: ins.engagedUsers ?? null,
            clicks: ins.clicks ?? null,
            videoViews: ins.videoViews ?? null,
            publicEngagement: ins.publicEngagement ?? null,
            metricSource,
          },
        });
      } catch (e: any) {
        if (e instanceof FacebookApiError && e.code === "missing_permission") throw e;
        failedInsights++;
        warnings.push({ fbPostId: d.fbPostId, message: e?.message ?? String(e) });
      }
    }

    // e. + f. Tính engagementRate và score cho population hiện tại
    const refreshed = await prisma.post.findMany({
      where: { pageId },
      orderBy: { createdTime: "desc" },
      take: 25,
    });

    for (const p of refreshed) {
      // Engagement rate CHỈ tính khi có trueReach (facebook_graph_api_insights).
      // Không tính khi reach = null hoặc reach = proxy (sẽ ra ER ~100% vô lý).
      if (p.metricSource === "facebook_graph_api_insights" && p.reach != null && p.reach > 0) {
        const eng = calculateEngagementRate({
          reactions: p.reactionsCount,
          comments: p.commentsCount,
          shares: p.sharesCount,
          clicks: p.clicks ?? 0,
          reach: p.reach,
        });
        await prisma.post.update({
          where: { id: p.id },
          data: { engagementRate: eng },
        });
      } else {
        await prisma.post.update({
          where: { id: p.id },
          data: { engagementRate: null },
        });
      }
    }

    // Tính score với population mới (sau khi có engagementRate)
    const population = await prisma.post.findMany({
      where: { pageId },
      orderBy: { createdTime: "desc" },
      take: 25,
    });
    for (const p of population) {
      const score = calculatePostScore(
        {
          reach: p.reach,
          engagementRate: p.engagementRate,
          commentsCount: p.commentsCount,
          sharesCount: p.sharesCount,
        },
        population.map((x) => ({
          reach: x.reach,
          engagementRate: x.engagementRate,
          commentsCount: x.commentsCount,
          sharesCount: x.sharesCount,
        })),
      );
      await prisma.post.update({
        where: { id: p.id },
        data: { score },
      });
    }

    return ok({
      syncedPosts: drafts.length,
      failedInsights,
      trueReachCount,
      videoViewsCount,
      publicEngagementCount,
      unavailableCount,
      metricSourceBreakdown: {
        facebook_graph_api_insights: trueReachCount,
        facebook_video_metric: videoViewsCount,
        public_engagement_proxy: publicEngagementCount,
        unavailable: unavailableCount,
      },
      warnings: warnings.slice(0, 50),
      page: {
        pageId: info.pageId,
        name: info.name,
        followersCount: info.followersCount,
        fanCount: info.fanCount,
        followersDelta,
      },
    });
  });
}
