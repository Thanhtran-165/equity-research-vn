import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";
import { aggregatePostsToPeriod } from "@/lib/benchmark/periodAggregation";

export const dynamic = "force-dynamic";

/**
 * GET /api/public-benchmark/topics
 * Aggregate engagement by topicTag across all pages.
 */
export async function GET(req: Request) {
  return withFbErrors(async () => {
    const url = new URL(req.url);
    const periodDays = parseInt(url.searchParams.get("periodDays") ?? "30");

    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - periodDays);

    const posts = await prisma.benchmarkPost.findMany({
      where: {
        topicTag: { not: null },
        OR: [{ postedAt: null }, { postedAt: { gte: startDate, lte: endDate } }],
      },
      select: {
        topicTag: true,
        reactions: true,
        comments: true,
        shares: true,
        publicVideoViews: true,
        reactionsObserved: true,
        commentsObserved: true,
        sharesObserved: true,
        publicVideoViewsObserved: true,
        comparableEngagement: true,
        observedPublicEngagement: true,
        metricCoverageScore: true,
      },
    });

    const byTopic = new Map<string, typeof posts>();
    for (const p of posts) {
      const tag = p.topicTag?.trim();
      if (!tag) continue;
      if (!byTopic.has(tag)) byTopic.set(tag, []);
      byTopic.get(tag)!.push(p);
    }

    const topics = Array.from(byTopic.entries())
      .map(([topic, topicPosts]) => ({
        topic,
        ...aggregatePostsToPeriod(topicPosts),
      }))
      .sort((a, b) => {
        const av = a.medianComparableEngagementPerPost;
        const bv = b.medianComparableEngagementPerPost;
        if (av == null && bv == null) return 0;
        if (av == null) return 1;
        if (bv == null) return -1;
        return bv - av;
      });

    return ok({
      periodDays,
      topics,
      sampleWarning:
        topics.length === 0 || topics.every((t) => t.postsCaptured < 5)
          ? "Insufficient sample: all topics have fewer than 5 posts — conclusions are preliminary. Requires more collection periods."
          : topics.some((t) => t.postsCaptured < 5)
            ? "Some topics have fewer than 5 posts — treat those rankings as preliminary signal."
            : null,
    });
  });
}
