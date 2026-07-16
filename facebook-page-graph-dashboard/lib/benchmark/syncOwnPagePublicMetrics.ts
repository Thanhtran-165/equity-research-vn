/**
 * Sync Chim Cút own-page public metrics from existing Post records.
 *
 * Chim Cút has true reach source (Meta Business Suite CSV), but for
 * PUBLIC BENCHMARK comparison we only use reactions + comments + shares
 * (the metrics that peers also have publicly visible).
 *
 * NO reach, clicks, or watchTime — those are NOT available for competitor pages,
 * so including them would create an unfair comparison.
 *
 * This function reads existing Post records (from MBS CSV import) and
 * creates/upserts BenchmarkPost entries for the Chim Cút own page.
 */

import { derivePostMetrics } from "./publicMetrics";

export interface OwnPagePostSource {
  postId: string;
  permalink: string;
  createdTime: string | Date | null;
  message: string | null;
  reactions: number | null;
  comments: number | null;
  shares: number | null;
  videoViews: number | null;
}

export interface SyncResult {
  synced: number;
  skipped: number;
  errors: string[];
}

/**
 * Transform a Post (from MBS CSV) into a BenchmarkPost-compatible input.
 * Strips reach/clicks/watchTime — only keeps public-engagement metrics.
 */
export function transformOwnPagePostForBenchmark(
  source: OwnPagePostSource,
): {
  postUrl: string;
  postedAt: string | null;
  textSnippet: string | null;
  contentType: string | null;
  topicTag: string | null;
  reactions: number | null;
  comments: number | null;
  shares: number | null;
  publicVideoViews: number | null;
  reactionsObserved: boolean;
  commentsObserved: boolean;
  sharesObserved: boolean;
  publicVideoViewsObserved: boolean;
  comparableEngagement: number | null;
  observedPublicEngagement: number | null;
  metricCoverageScore: number;
} {
  const metrics = derivePostMetrics({
    reactions: source.reactions,
    comments: source.comments,
    shares: source.shares,
    publicVideoViews: source.videoViews,
  });

  const snippet = source.message
    ? source.message.length > 200
      ? source.message.slice(0, 200) + "…"
      : source.message
    : null;

  return {
    postUrl: source.permalink || source.postId,
    postedAt:
      source.createdTime instanceof Date
        ? source.createdTime.toISOString()
        : source.createdTime,
    textSnippet: snippet,
    contentType: null, // Post model doesn't track content type
    topicTag: null,
    reactions: metrics.reactions,
    comments: metrics.comments,
    shares: metrics.shares,
    publicVideoViews: metrics.publicVideoViews,
    reactionsObserved: metrics.reactionsObserved,
    commentsObserved: metrics.commentsObserved,
    sharesObserved: metrics.sharesObserved,
    publicVideoViewsObserved: metrics.publicVideoViewsObserved,
    comparableEngagement: metrics.comparableEngagement,
    observedPublicEngagement: metrics.observedPublicEngagement,
    metricCoverageScore: metrics.metricCoverageScore,
  };
}

/**
 * Sync own-page posts into BenchmarkPost table.
 * Uses upsert keyed on [benchmarkPageId, postUrl, capturedAt].
 */
export async function syncOwnPagePostsToBenchmark(
  prisma: {
    benchmarkPage: { findFirst: Function };
    benchmarkPost: { upsert: Function; count: Function };
    post: { findMany: Function };
  },
  ownPageUrl: string,
  options?: { periodStart?: Date; periodEnd?: Date; limit?: number },
): Promise<SyncResult> {
  const ownPage = await prisma.benchmarkPage.findFirst({
    where: { canonicalUrl: ownPageUrl, isOwnPage: true },
  });

  if (!ownPage) {
    return {
      synced: 0,
      skipped: 0,
      errors: [`Own page not found: ${ownPageUrl}`],
    };
  }

  const where: { [key: string]: unknown } = {};
  if (options?.periodStart || options?.periodEnd) {
    where.createdTime = {};
    if (options?.periodStart) (where.createdTime as { gte?: Date }).gte = options.periodStart;
    if (options?.periodEnd) (where.createdTime as { lte?: Date }).lte = options.periodEnd;
  }

  const posts = await prisma.post.findMany({
    where,
    orderBy: { createdTime: "desc" },
    take: options?.limit ?? 500,
    select: {
      id: true,
      fbPostId: true,
      permalinkUrl: true,
      createdTime: true,
      message: true,
      reactionsCount: true,
      commentsCount: true,
      sharesCount: true,
      videoViews: true,
    },
  });

  let synced = 0;
  let skipped = 0;
  const errors: string[] = [];
  const capturedAt = new Date();

  for (const post of posts) {
    if (!post.permalinkUrl && !post.fbPostId) {
      skipped++;
      continue;
    }

    const transformed = transformOwnPagePostForBenchmark({
      postId: post.fbPostId,
      permalink: post.permalinkUrl,
      createdTime: post.createdTime,
      message: post.message,
      reactions: post.reactionsCount,
      comments: post.commentsCount,
      shares: post.sharesCount,
      videoViews: post.videoViews,
    });

    try {
      await prisma.benchmarkPost.upsert({
        where: {
          benchmarkPageId_postUrl_capturedAt: {
            benchmarkPageId: ownPage.id,
            postUrl: transformed.postUrl,
            capturedAt,
          },
        },
        create: {
          benchmarkPageId: ownPage.id,
          postUrl: transformed.postUrl,
          postedAt: transformed.postedAt,
          textSnippet: transformed.textSnippet,
          contentType: transformed.contentType,
          topicTag: transformed.topicTag,
          reactions: transformed.reactions,
          comments: transformed.comments,
          shares: transformed.shares,
          publicVideoViews: transformed.publicVideoViews,
          reactionsObserved: transformed.reactionsObserved,
          commentsObserved: transformed.commentsObserved,
          sharesObserved: transformed.sharesObserved,
          publicVideoViewsObserved: transformed.publicVideoViewsObserved,
          comparableEngagement: transformed.comparableEngagement,
          observedPublicEngagement: transformed.observedPublicEngagement,
          metricCoverageScore: transformed.metricCoverageScore,
          source: "own_page_sync",
          capturedAt,
        },
        update: {
          postedAt: transformed.postedAt,
          textSnippet: transformed.textSnippet,
          reactions: transformed.reactions,
          comments: transformed.comments,
          shares: transformed.shares,
          publicVideoViews: transformed.publicVideoViews,
          reactionsObserved: transformed.reactionsObserved,
          commentsObserved: transformed.commentsObserved,
          sharesObserved: transformed.sharesObserved,
          publicVideoViewsObserved: transformed.publicVideoViewsObserved,
          comparableEngagement: transformed.comparableEngagement,
          observedPublicEngagement: transformed.observedPublicEngagement,
          metricCoverageScore: transformed.metricCoverageScore,
        },
      });
      synced++;
    } catch (err) {
      errors.push(`Failed to sync post ${post.postId}: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  return { synced, skipped, errors };
}
