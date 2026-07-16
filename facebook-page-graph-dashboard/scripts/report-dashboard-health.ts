/**
 * Dashboard Health Report — PASS/WARN/FAIL with non-zero exit on FAIL.
 * Usage: npm run dashboard:health
 */
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

interface Check {
  level: "PASS" | "WARN" | "FAIL";
  message: string;
}

async function main() {
  const checks: Check[] = [];

  console.log("═══════════════════════════════════════════════════════════");
  console.log("  Dashboard Health Report");
  console.log("═══════════════════════════════════════════════════════════\n");

  // Posts
  const postCount = await prisma.post.count();
  const postBySource = await prisma.post.groupBy({ by: ["metricSource"], _count: true });
  const postsWithReach = await prisma.post.count({ where: { reach: { not: null, gt: 0 } } });
  const postsWithER = await prisma.post.count({ where: { engagementRate: { not: null } } });

  console.log("── Posts ──");
  console.log(`  Total: ${postCount}`);
  for (const s of postBySource) {
    console.log(`    ${s.metricSource}: ${s._count}`);
  }
  console.log(`  With reach > 0: ${postsWithReach}`);
  console.log(`  With ER: ${postsWithER}`);

  // Video
  const videoAssets = await prisma.videoAsset.count();
  const lifetimeMetrics = await prisma.videoLifetimeMetric.count();
  const dailyMetrics = await prisma.videoDailyMetric.count();
  const dailyRange = await prisma.videoDailyMetric.findFirst({ orderBy: { date: "asc" }, select: { date: true } });
  const dailyMax = await prisma.videoDailyMetric.findFirst({ orderBy: { date: "desc" }, select: { date: true } });
  const unlinkedAssets = await prisma.videoAsset.count({ where: { matchedPostId: null } });

  // Anomaly
  const anomalies = await prisma.videoLifetimeMetric.findMany({
    where: { videoViews3s: { gt: 0 } },
    include: { videoAsset: true },
  });
  let anomalyCount = 0;
  for (const a of anomalies) {
    if (a.videoViews3s && a.videoViews3s > 0 && a.watchTimeSeconds && a.watchTimeSeconds / a.videoViews3s > 600) {
      anomalyCount++;
    }
  }

  console.log("\n── Video ──");
  console.log(`  VideoAssets: ${videoAssets}`);
  console.log(`  Lifetime metrics: ${lifetimeMetrics}`);
  console.log(`  Daily rows: ${dailyMetrics}`);
  console.log(`  Daily date range: ${dailyRange?.date ?? "—"} → ${dailyMax?.date ?? "—"}`);
  console.log(`  Unlinked assets: ${unlinkedAssets}`);
  console.log(`  Anomalies: ${anomalyCount}`);

  // Imports
  const latestBatch = await prisma.insightImportBatch.findFirst({
    orderBy: { importedAt: "desc" },
    select: { id: true, filename: true, importedAt: true, status: true, rowCount: true },
  });
  const totalBatches = await prisma.insightImportBatch.count();
  console.log(`\n── Imports ──`);
  console.log(`  Total batches: ${totalBatches}`);
  if (latestBatch) {
    console.log(`  Latest: #${latestBatch.id} ${latestBatch.filename.slice(0, 40)}`);
    console.log(`    imported: ${latestBatch.importedAt.toISOString()}`);
    console.log(`    status: ${latestBatch.status} | rows: ${latestBatch.rowCount}`);
  }

  // Reminder — check duplicates manually
  const allItems = await prisma.dataReminderItem.findMany({
    select: { runId: true, code: true },
  });
  const seen = new Set<string>();
  const dupKeys: string[] = [];
  for (const item of allItems) {
    const key = `${item.runId}_${item.code}`;
    if (seen.has(key)) dupKeys.push(key);
    else seen.add(key);
  }
  const dupItems = dupKeys;

  console.log(`\n── Reminders ──`);
  console.log(`  Duplicate items: ${dupItems.length}`);

  // --- CHECKS ---
  console.log("\n── Health Checks ──");

  // FAIL: duplicate reminder items
  if (dupItems.length > 0) {
    checks.push({ level: "FAIL", message: `${dupItems.length} duplicate reminder items found` });
  } else {
    checks.push({ level: "PASS", message: "No duplicate reminder items" });
  }

  // FAIL: non-true-reach posts with ER
  const nonTrueReachWithER = await prisma.post.count({
    where: {
      engagementRate: { not: null },
      metricSource: { notIn: ["facebook_graph_api_insights", "meta_business_suite_csv"] },
    },
  });
  if (nonTrueReachWithER > 0) {
    checks.push({ level: "FAIL", message: `${nonTrueReachWithER} posts with ER but non-true-reach source` });
  } else {
    checks.push({ level: "PASS", message: "All ER rows are true-reach sources" });
  }

  // WARN: unlinked video assets
  if (unlinkedAssets > 0) {
    checks.push({ level: "WARN", message: `${unlinkedAssets} video assets unlinked (expected — Meta uses different ID systems)` });
  }

  // WARN: watch-time anomaly
  if (anomalyCount > 0) {
    checks.push({ level: "WARN", message: `${anomalyCount} video with avg watch time > 600s/view` });
  }

  // WARN: stale import (older than 14 days)
  if (latestBatch) {
    const daysSinceImport = (Date.now() - latestBatch.importedAt.getTime()) / (24 * 3600 * 1000);
    if (daysSinceImport > 14) {
      checks.push({ level: "WARN", message: `Latest import is ${Math.floor(daysSinceImport)} days old` });
    } else {
      checks.push({ level: "PASS", message: `Latest import is ${Math.floor(daysSinceImport)} days old` });
    }
  }

  // Print checks
  let hasFail = false;
  for (const c of checks) {
    const icon = c.level === "PASS" ? "✅" : c.level === "WARN" ? "⚠️ " : "❌";
    console.log(`  ${icon} [${c.level}] ${c.message}`);
    if (c.level === "FAIL") hasFail = true;
  }

  console.log("\n═══════════════════════════════════════════════════════════");
  console.log(`  Result: ${hasFail ? "FAIL ❌" : "PASS ✅ (with warnings)"}`);
  console.log("═══════════════════════════════════════════════════════════");

  await prisma.$disconnect();
  if (hasFail) process.exit(1);
}

main().catch((e) => {
  console.error("Health check FAILED:", e);
  process.exit(1);
});
