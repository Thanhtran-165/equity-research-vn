import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { ok, err, withFbErrors } from "@/lib/env";
import {
  calculateBenchmarkScore,
  deriveSnapshot,
  normalizeCategory,
  type DerivedSnapshot,
} from "@/lib/benchmark";

export const dynamic = "force-dynamic";

/**
 * GET /api/benchmark/snapshots?category=&periodStart=&periodEnd=
 * Trả snapshots + page info + benchmarkScore (re-tính theo peer trong filter).
 */
export async function GET(req: Request) {
  return withFbErrors(async () => {
    const url = new URL(req.url);
    const category = url.searchParams.get("category");
    const periodStart = url.searchParams.get("periodStart");
    const periodEnd = url.searchParams.get("periodEnd");

    const pageWhere: any = { isActive: true };
    if (category && category !== "all") pageWhere.category = normalizeCategory(category);

    const snapWhere: any = {};
    if (periodStart) snapWhere.periodStart = { gte: periodStart };
    if (periodEnd) snapWhere.periodEnd = { lte: periodEnd };

    const snapshotsRaw = await prisma.competitorMetricSnapshot.findMany({
      where: {
        ...snapWhere,
        page: pageWhere,
      },
      include: { page: true },
      orderBy: [{ periodStart: "desc" }, { periodEnd: "desc" }],
    });

    // Re-tính benchmarkScore dựa trên peer population (cùng filter)
    const population = snapshotsRaw.map((s) => ({
      engagementPer1kFollowers: s.engagementPer1kFollowers,
      avgSharesPerPost: s.avgSharesPerPost,
      avgCommentsPerPost: s.avgCommentsPerPost,
      videoViewsPerFollower: s.videoViewsPerFollower,
      postingFrequencyPerDay: s.postingFrequencyPerDay,
      topPostEngagement: s.topPostEngagement,
    }));

    const snapshots = snapshotsRaw.map((s) => {
      const derived: DerivedSnapshot = {
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
        benchmarkScore: null,
      };
      const score = calculateBenchmarkScore(derived, population);
      return {
        id: s.id,
        competitorPageId: s.competitorPageId,
        periodStart: s.periodStart,
        periodEnd: s.periodEnd,
        followers: s.followers,
        postsCount: s.postsCount,
        reactionsCount: s.reactionsCount,
        commentsCount: s.commentsCount,
        sharesCount: s.sharesCount,
        videoViews: s.videoViews,
        topPostUrl: s.topPostUrl,
        topPostEngagement: s.topPostEngagement,
        activeAds: s.activeAds,
        dominantTopic: s.dominantTopic,
        publicEngagement: s.publicEngagement,
        publicEngagementPerPost: s.publicEngagementPerPost,
        engagementPer1kFollowers: s.engagementPer1kFollowers,
        avgReactionsPerPost: s.avgReactionsPerPost,
        avgCommentsPerPost: s.avgCommentsPerPost,
        avgSharesPerPost: s.avgSharesPerPost,
        videoViewsPerFollower: s.videoViewsPerFollower,
        commentIntensity: s.commentIntensity,
        shareIntensity: s.shareIntensity,
        postingFrequencyPerDay: s.postingFrequencyPerDay,
        benchmarkScore: score,
        page: s.page
          ? {
              id: s.page.id,
              pageName: s.page.pageName,
              pageUrl: s.page.pageUrl,
              category: s.page.category,
              description: s.page.description,
              notes: s.page.notes,
            }
          : null,
      };
    });

    return ok({ snapshots });
  });
}

/**
 * POST /api/benchmark/snapshots
 * Body: { competitorPageId | pageUrl, periodStart, periodEnd, followers, postsCount,
 *         reactionsCount, commentsCount, sharesCount, videoViews?, topPostUrl?,
 *         topPostEngagement?, activeAds?, dominantTopic? }
 * Tự tính derived metrics + benchmarkScore (re-tính cho tất cả peer cùng period).
 */
export async function POST(req: Request) {
  return withFbErrors(async () => {
    let body: any;
    try {
      body = await req.json();
    } catch {
      return err("unknown_error", "Body không phải JSON hợp lệ", 400);
    }

    const periodStart = (body?.periodStart ?? "").toString().trim();
    const periodEnd = (body?.periodEnd ?? "").toString().trim();
    if (!periodStart || !periodEnd) {
      return err("unknown_error", "Thiếu periodStart hoặc periodEnd", 400);
    }

    // resolve competitorPageId
    let competitorPageId: number | null = null;
    if (body?.competitorPageId != null) {
      competitorPageId = Number(body.competitorPageId);
    } else if (body?.pageUrl) {
      const found = await prisma.competitorPage.findUnique({
        where: { pageUrl: String(body.pageUrl) },
      });
      if (!found) return err("unknown_error", "pageUrl không tồn tại — tạo page trước", 404);
      competitorPageId = found.id;
    }
    if (!competitorPageId || !Number.isFinite(competitorPageId)) {
      return err("unknown_error", "Thiếu competitorPageId / pageUrl", 400);
    }

    const toNum = (v: any): number => {
      const n = Number(v);
      return Number.isFinite(n) ? n : 0;
    };
    const toNumNull = (v: any): number | null => {
      if (v === null || v === undefined || v === "") return null;
      const n = Number(v);
      return Number.isFinite(n) ? n : null;
    };
    const toBoolNull = (v: any): boolean | null => {
      if (v === null || v === undefined || v === "") return null;
      if (typeof v === "boolean") return v;
      const s = String(v).toLowerCase();
      if (s === "true" || s === "1" || s === "yes") return true;
      if (s === "false" || s === "0" || s === "no") return false;
      return null;
    };

    const raw = {
      followers: toNum(body?.followers),
      postsCount: toNum(body?.postsCount),
      reactionsCount: toNum(body?.reactionsCount),
      commentsCount: toNum(body?.commentsCount),
      sharesCount: toNum(body?.sharesCount),
      videoViews: toNumNull(body?.videoViews),
      topPostEngagement: toNumNull(body?.topPostEngagement),
      periodStart,
      periodEnd,
    };

    const warnings: string[] = [];
    if (raw.followers <= 0) warnings.push("followers <= 0 — engagementPer1kFollowers sẽ null.");
    if (raw.postsCount <= 0) warnings.push("postsCount <= 0 — các metric per post sẽ null.");
    if (raw.videoViews == null)
      warnings.push("videoViews bị thiếu — benchmarkScore sẽ dùng trọng số fallback.");

    const derived = deriveSnapshot(raw);

    // upsert theo (competitorPageId, periodStart, periodEnd)
    const data = {
      competitorPageId,
      periodStart,
      periodEnd,
      followers: raw.followers,
      postsCount: raw.postsCount,
      reactionsCount: raw.reactionsCount,
      commentsCount: raw.commentsCount,
      sharesCount: raw.sharesCount,
      videoViews: raw.videoViews,
      topPostUrl: body?.topPostUrl ? String(body.topPostUrl) : null,
      topPostEngagement: raw.topPostEngagement,
      activeAds: toBoolNull(body?.activeAds),
      dominantTopic: body?.dominantTopic ? String(body.dominantTopic) : null,
      publicEngagement: derived.publicEngagement,
      publicEngagementPerPost: derived.publicEngagementPerPost,
      engagementPer1kFollowers: derived.engagementPer1kFollowers,
      avgReactionsPerPost: derived.avgReactionsPerPost,
      avgCommentsPerPost: derived.avgCommentsPerPost,
      avgSharesPerPost: derived.avgSharesPerPost,
      videoViewsPerFollower: derived.videoViewsPerFollower,
      commentIntensity: derived.commentIntensity,
      shareIntensity: derived.shareIntensity,
      postingFrequencyPerDay: derived.postingFrequencyPerDay,
    };

    const existing = await prisma.competitorMetricSnapshot.findUnique({
      where: {
        competitorPageId_periodStart_periodEnd: {
          competitorPageId,
          periodStart,
          periodEnd,
        },
      },
    });

    let snapshot;
    if (existing) {
      snapshot = await prisma.competitorMetricSnapshot.update({
        where: { id: existing.id },
        data,
      });
    } else {
      snapshot = await prisma.competitorMetricSnapshot.create({ data });
    }

    // Update followersLatest trên page
    await prisma.competitorPage.update({
      where: { id: competitorPageId },
      data: { followersLatest: raw.followers },
    });

    // Re-tính benchmarkScore cho tất cả peer cùng period
    await recalcScoresForPeriod(periodStart, periodEnd);

    const refreshed = await prisma.competitorMetricSnapshot.findUnique({
      where: { id: snapshot.id },
    });

    return ok({ snapshot: refreshed, warnings });
  });
}

/**
 * Re-tính benchmarkScore cho tất cả snapshot cùng (periodStart, periodEnd).
 */
async function recalcScoresForPeriod(periodStart: string, periodEnd: string) {
  const all = await prisma.competitorMetricSnapshot.findMany({
    where: { periodStart, periodEnd },
  });
  if (all.length === 0) return;

  const population = all.map((s) => ({
    engagementPer1kFollowers: s.engagementPer1kFollowers,
    avgSharesPerPost: s.avgSharesPerPost,
    avgCommentsPerPost: s.avgCommentsPerPost,
    videoViewsPerFollower: s.videoViewsPerFollower,
    postingFrequencyPerDay: s.postingFrequencyPerDay,
    topPostEngagement: s.topPostEngagement,
  }));

  for (const s of all) {
    const derived: DerivedSnapshot = {
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
      benchmarkScore: null,
    };
    const score = calculateBenchmarkScore(derived, population);
    await prisma.competitorMetricSnapshot.update({
      where: { id: s.id },
      data: { benchmarkScore: score },
    });
  }
}
