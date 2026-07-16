/**
 * Report video metrics — top videos + daily trend.
 * Usage: npx tsx scripts/report-video-metrics.ts
 */
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  console.log("═══════════════════════════════════════════════════════════");
  console.log("  Video Metrics Report");
  console.log("═══════════════════════════════════════════════════════════\n");

  // VideoAsset summary
  const assetCount = await prisma.videoAsset.count();
  const linkedCount = await prisma.videoAsset.count({ where: { matchedPostId: { not: null } } });
  console.log(`VideoAssets: ${assetCount} total, ${linkedCount} linked to Post\n`);

  // VideoLifetimeMetric: top 20 by views
  const lifetimeMetrics = await prisma.videoLifetimeMetric.findMany({
    include: { videoAsset: true },
    orderBy: { videoViews3s: "desc" },
    take: 20,
    where: { videoViews3s: { gt: 0 } },
  });

  console.log("── Top 20 Video by Lifetime 3s Views ──");
  console.log("Views    | Reach   | Watch(s)  | Reactions | Comments | Shares | Title");
  console.log("-".repeat(100));
  for (const m of lifetimeMetrics) {
    const title = (m.videoAsset?.title ?? "(untitled)").slice(0, 40);
    console.log(
      `${String(m.videoViews3s ?? 0).padStart(8)} | ${String(m.reach ?? 0).padStart(7)} | ${String(Math.round(m.watchTimeSeconds ?? 0)).padStart(9)} | ${String(m.reactions ?? 0).padStart(9)} | ${String(m.comments ?? 0).padStart(8)} | ${String(m.shares ?? 0).padStart(6)} | ${title}`,
    );
  }

  // Top 20 by watch time
  console.log("\n── Top 20 Video by Lifetime Watch Time (seconds) ──");
  const watchMetrics = await prisma.videoLifetimeMetric.findMany({
    include: { videoAsset: true },
    orderBy: { watchTimeSeconds: "desc" },
    take: 20,
    where: { watchTimeSeconds: { gt: 0 } },
  });
  console.log("Watch(s)  | Views    | Title");
  console.log("-".repeat(70));
  for (const m of watchMetrics) {
    const title = (m.videoAsset?.title ?? "(untitled)").slice(0, 40);
    console.log(`${String(Math.round(m.watchTimeSeconds ?? 0)).padStart(9)} | ${String(m.videoViews3s ?? 0).padStart(8)} | ${title}`);
  }

  // Daily totals by month
  console.log("\n── Daily Video Views by Month (V02) ──");
  const dailyMetrics = await prisma.videoDailyMetric.findMany({
    select: { date: true, videoViews3s: true, watchTimeSeconds: true, reach: true },
  });

  const byMonth: Record<string, { views: number; watch: number; reach: number; rows: number }> = {};
  for (const d of dailyMetrics) {
    const month = d.date.slice(0, 7); // YYYY-MM
    if (!byMonth[month]) byMonth[month] = { views: 0, watch: 0, reach: 0, rows: 0 };
    byMonth[month].views += d.videoViews3s ?? 0;
    byMonth[month].watch += d.watchTimeSeconds ?? 0;
    byMonth[month].reach += d.reach ?? 0;
    byMonth[month].rows++;
  }

  console.log("Month    | Rows   | Total Views | Total Reach | Total Watch(hrs)");
  console.log("-".repeat(70));
  for (const [month, d] of Object.entries(byMonth).sort()) {
    console.log(
      `${month} | ${String(d.rows).padStart(6)} | ${String(d.views).padStart(11)} | ${String(d.reach).padStart(11)} | ${(d.watch / 3600).toFixed(1).padStart(15)}`,
    );
  }

  console.log(`\nTotal daily rows: ${dailyMetrics.length}`);

  await prisma.$disconnect();
}

main().catch(console.error);
