import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";
import { derivePostMetrics } from "@/lib/benchmark/publicMetrics";
import { parseDate } from "@/lib/imports/normalizeRows";

export const dynamic = "force-dynamic";

/**
 * POST /api/public-benchmark/posts/manual
 * Body: { benchmarkPageId, postUrl, postedAt?, reactions?, comments?, shares?, videoViews?, textSnippet?, contentType?, topicTag? }
 *
 * Blank = null (NOT zero). "0" = observed zero.
 */
export async function POST(req: Request) {
  return withFbErrors(async () => {
    const body = await req.json();

    if (!body.benchmarkPageId || !body.postUrl) {
      return ok({ error: "benchmarkPageId and postUrl are required" }, 400);
    }

    const page = await prisma.benchmarkPage.findUnique({
      where: { id: parseInt(body.benchmarkPageId) },
    });
    if (!page) {
      return ok({ error: "BenchmarkPage not found" }, 404);
    }

    const metrics = derivePostMetrics({
      reactions: body.reactions ?? null,
      comments: body.comments ?? null,
      shares: body.shares ?? null,
      publicVideoViews: body.videoViews ?? null,
    });

    const postedAtStr = body.postedAt ? parseDate(String(body.postedAt)) : null;
    const capturedAt = new Date();

    const post = await prisma.benchmarkPost.upsert({
      where: {
        benchmarkPageId_postUrl_capturedAt: {
          benchmarkPageId: page.id,
          postUrl: body.postUrl,
          capturedAt,
        },
      },
      create: {
        benchmarkPageId: page.id,
        postUrl: body.postUrl,
        postedAt: postedAtStr,
        textSnippet: body.textSnippet ?? null,
        contentType: body.contentType ?? null,
        topicTag: body.topicTag ?? null,
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
        source: "manual_entry",
        capturedAt,
      },
      update: {
        postedAt: postedAtStr,
        textSnippet: body.textSnippet ?? undefined,
        contentType: body.contentType ?? undefined,
        topicTag: body.topicTag ?? undefined,
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
      },
    });

    return ok({ post, message: "Post saved" });
  });
}
