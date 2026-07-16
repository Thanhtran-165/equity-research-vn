import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";
import { buildMonthlyReport, formatMonthlyReportMarkdown } from "@/lib/reporting/monthlyReport";

export const dynamic = "force-dynamic";

/**
 * GET /api/reports/monthly?month=2026-06&format=md|json
 */
export async function GET(req: Request) {
  return withFbErrors(async () => {
    const url = new URL(req.url);
    const month = url.searchParams.get("month") ?? new Date().toISOString().slice(0, 7);
    const format = url.searchParams.get("format") ?? "json";

    // Validate month format YYYY-MM
    if (!/^\d{4}-\d{2}$/.test(month)) {
      return ok({ error: "Invalid month format. Use YYYY-MM." });
    }

    const startDate = `${month}-01`;
    const [year, mon] = month.split("-").map(Number);
    const lastDay = new Date(year, mon, 0).getDate();
    const endDate = `${month}-${String(lastDay).padStart(2, "0")}`;

    // Fetch posts created in this month
    const posts = await prisma.post.findMany({
      where: {
        createdTime: { gte: startDate, lte: endDate + "T23:59:59" },
      },
      select: {
        fbPostId: true,
        message: true,
        topic: true,
        postType: true,
        createdTime: true,
        permalinkUrl: true,
        reach: true,
        reactionsCount: true,
        commentsCount: true,
        sharesCount: true,
        clicks: true,
        metricSource: true,
        engagementRate: true,
      },
    });

    const postRows = posts.map((p) => ({
      ...p,
      reach: p.reach ?? null,
      clicks: p.clicks ?? null,
      engagementRate: p.engagementRate ?? null,
      metricSource: p.metricSource ?? null,
      message: p.message ?? null,
      permalinkUrl: p.permalinkUrl ?? null,
      createdTime: p.createdTime ?? null,
    }));

    // Fetch video daily metrics for this month
    const videoDaily = await prisma.videoDailyMetric.findMany({
      where: { date: { gte: startDate, lte: endDate } },
      include: { videoAsset: { select: { externalVideoId: true, title: true } } },
    });

    const report = buildMonthlyReport(month, postRows, videoDaily);

    if (format === "md") {
      const md = formatMonthlyReportMarkdown(report);
      return new Response(md, {
        headers: { "Content-Type": "text/markdown; charset=utf-8" },
      }) as any;
    }

    return ok(report);
  });
}
