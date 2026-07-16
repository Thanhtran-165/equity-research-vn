/**
 * CLI: Generate monthly report as Markdown file.
 * Usage: npm run report:monthly -- --month=2026-06
 */
import { PrismaClient } from "@prisma/client";
import { buildMonthlyReport, formatMonthlyReportMarkdown } from "../lib/reporting/monthlyReport";
import { writeFileSync, mkdirSync } from "fs";
import { join } from "path";

const prisma = new PrismaClient();

async function main() {
  const args = process.argv.slice(2);
  let month = "";
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--month" || args[i].startsWith("--month=")) {
      month = args[i].includes("=") ? args[i].split("=")[1] : args[++i] ?? "";
    }
  }

  if (!month) {
    const now = new Date();
    month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  }

  if (!/^\d{4}-\d{2}$/.test(month)) {
    console.error(`Invalid month: ${month}. Use YYYY-MM.`);
    process.exit(1);
  }

  console.log(`→ Generating monthly report for ${month}...`);

  const startDate = `${month}-01`;
  const [year, mon] = month.split("-").map(Number);
  const lastDay = new Date(year, mon, 0).getDate();
  const endDate = `${month}-${String(lastDay).padStart(2, "0")}`;

  const posts = await prisma.post.findMany({
    where: { createdTime: { gte: startDate, lte: endDate + "T23:59:59" } },
    select: {
      fbPostId: true, message: true, topic: true, postType: true,
      createdTime: true, permalinkUrl: true, reach: true,
      metricSource: true,
      reactionsCount: true, commentsCount: true, sharesCount: true,
      clicks: true, engagementRate: true,
    },
  });

  const postRows = posts.map((p) => ({
    ...p,
    reach: p.reach ?? null,
    clicks: p.clicks ?? null,
    engagementRate: p.engagementRate ?? null,
    message: p.message ?? null,
    permalinkUrl: p.permalinkUrl ?? null,
    createdTime: p.createdTime ?? null,
  }));

  const videoDaily = await prisma.videoDailyMetric.findMany({
    where: { date: { gte: startDate, lte: endDate } },
    include: { videoAsset: { select: { externalVideoId: true, title: true } } },
  });

  const report = buildMonthlyReport(month, postRows, videoDaily);
  const md = formatMonthlyReportMarkdown(report);

  const outputDir = join(process.cwd(), "reports");
  mkdirSync(outputDir, { recursive: true });
  const outputPath = join(outputDir, `${month}-chimcut-monthly-report.md`);
  writeFileSync(outputPath, md);

  console.log(`✓ Report saved: ${outputPath}`);
  console.log(`  Posts: ${report.page.totalPosts} | Reach: ${report.page.totalReach.toLocaleString("vi-VN")} | ER: ${report.page.avgER ? (report.page.avgER * 100).toFixed(2) + "%" : "—"}`);
  console.log(`  Videos: ${report.video.activeVideoCount} active | Views: ${report.video.totalViews3s.toLocaleString("vi-VN")} | Watch: ${report.video.watchTimeHours.toFixed(1)}h`);
  console.log(`  Post spikes: ${report.postSpikes.length} | Video spikes: ${report.videoSpikes.length}`);

  await prisma.$disconnect();
}

main().catch((e) => { console.error(e); process.exit(1); });
