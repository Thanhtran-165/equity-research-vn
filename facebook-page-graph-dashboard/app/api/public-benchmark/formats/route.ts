import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";
import { aggregatePostsToPeriod } from "@/lib/benchmark/periodAggregation";

export const dynamic = "force-dynamic";

/**
 * GET /api/public-benchmark/formats
 * Aggregate engagement by contentType (format) across all pages.
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
        contentType: { not: null },
        OR: [{ postedAt: null }, { postedAt: { gte: startDate, lte: endDate } }],
      },
      select: {
        contentType: true,
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

    const byFormat = new Map<string, typeof posts>();
    for (const p of posts) {
      const fmt = p.contentType?.trim();
      if (!fmt) continue;
      if (!byFormat.has(fmt)) byFormat.set(fmt, []);
      byFormat.get(fmt)!.push(p);
    }

    const formats = Array.from(byFormat.entries())
      .map(([format, fmtPosts]) => ({
        format,
        ...aggregatePostsToPeriod(fmtPosts),
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
      formats,
      sampleWarning:
        formats.length === 0 || formats.every((f) => f.postsCaptured < 5)
          ? "Insufficient sample: all formats have fewer than 5 posts — conclusions are preliminary. Requires more collection periods."
          : formats.some((f) => f.postsCaptured < 5)
            ? "Some formats have fewer than 5 posts — treat those rankings as preliminary signal."
            : null,
      sharesNote:
        formats.some((f) => f.postsCaptured > 0)
          ? "Share ratio computed only on posts where shares were observed (observed subset)."
          : null,
    });
  });
}
