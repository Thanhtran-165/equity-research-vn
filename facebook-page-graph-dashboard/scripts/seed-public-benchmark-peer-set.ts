/**
 * Seed Peer Set v2 into BenchmarkPage table.
 * Usage: npm run benchmark:seed-peers
 */
import { PrismaClient } from "@prisma/client";
import { readFileSync } from "fs";
import { join } from "path";

const prisma = new PrismaClient();

function parseCsvSimple(text: string): string[][] {
  return text.trim().split("\n").map((line) => {
    const cells: string[] = [];
    let current = "";
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (inQuotes) {
        if (c === '"') { inQuotes = false; } else { current += c; }
      } else {
        if (c === '"') { inQuotes = true; }
        else if (c === ',') { cells.push(current.trim()); current = ""; }
        else { current += c; }
      }
    }
    cells.push(current.trim());
    return cells;
  });
}

async function main() {
  const csvPath = join(process.cwd(), "data/benchmark/public-benchmark-peer-set-v2.csv");
  const raw = readFileSync(csvPath, "utf-8");
  const rows = parseCsvSimple(raw);
  const headers = rows[0];
  const dataRows = rows.slice(1);

  console.log(`→ Seeding ${dataRows.length} peer set entries...`);

  let created = 0;
  let updated = 0;

  for (const row of dataRows) {
    const obj: Record<string, string> = {};
    headers.forEach((h, i) => { obj[h] = row[i] ?? ""; });
    if (!obj.name || !obj.canonicalUrl) continue;

    const existing = await prisma.benchmarkPage.findUnique({
      where: { canonicalUrl: obj.canonicalUrl },
    });

    if (!existing) {
      await prisma.benchmarkPage.create({
        data: {
          name: obj.name,
          canonicalUrl: obj.canonicalUrl,
          platform: "facebook",
          objectType: obj.objectType || "facebook_page",
          category: obj.category || null,
          benchmarkRole: obj.benchmarkRole || "watchlist",
          scaleBand: obj.scaleBand || null,
          collectionFrequency: obj.collectionFrequency || null,
          recommendedPostsPerCollection: obj.recommendedPostsPerCollection ? parseInt(obj.recommendedPostsPerCollection) : null,
          isOwnPage: false,
          activeStatus: "active",
          verificationConfidence: obj.verificationConfidence || null,
          notes: obj.notes || null,
        },
      });
      created++;
    } else {
      await prisma.benchmarkPage.update({
        where: { id: existing.id },
        data: {
          name: obj.name || undefined,
          objectType: obj.objectType || undefined,
          category: obj.category || undefined,
          benchmarkRole: obj.benchmarkRole || undefined,
          scaleBand: obj.scaleBand || undefined,
          collectionFrequency: obj.collectionFrequency || undefined,
          verificationConfidence: obj.verificationConfidence || undefined,
          notes: obj.notes || undefined,
        },
      });
      updated++;
    }
  }

  // Seed Chim Cút own page
  const ownPage = await prisma.benchmarkPage.findUnique({
    where: { canonicalUrl: "https://facebook.com/chimcutvnindex" },
  });
  if (!ownPage) {
    await prisma.benchmarkPage.create({
      data: {
        name: "Chim Cút",
        canonicalUrl: "https://facebook.com/chimcutvnindex",
        platform: "facebook",
        objectType: "facebook_page",
        category: "stock_market",
        benchmarkRole: "core_peer",
        scaleBand: "micro",
        isOwnPage: true,
        activeStatus: "active",
        verificationConfidence: "high",
        lastVerifiedAt: new Date(),
      },
    });
    created++;
    console.log("  ✓ Created Chim Cút own page");
  }

  console.log(`✓ Done: ${created} created, ${updated} updated`);
  const total = await prisma.benchmarkPage.count();
  const corePeers = await prisma.benchmarkPage.count({ where: { benchmarkRole: "core_peer" } });
  console.log(`  Total pages: ${total} | Core peers: ${corePeers}`);

  await prisma.$disconnect();
}

main().catch(console.error);
