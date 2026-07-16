/**
 * Generate weekly benchmark collection pack.
 *
 * Usage: npm run benchmark:collection-pack -- --week=2026-07-06
 *
 * Output: data/benchmark/collections/<week>/
 */
import { PrismaClient } from "@prisma/client";
import { generateCollectionPack, isoWeekKey, type CollectionPeer } from "../lib/benchmark/generateCollectionPack";

const prisma = new PrismaClient();

async function main() {
  const weekArg = process.argv
    .find((a) => a.startsWith("--week="))
    ?.split("=")[1];

  let weekStart: Date;
  if (weekArg) {
    const [y, m, d] = weekArg.split("-").map(Number);
    if (!y || !m || !d) {
      console.error(`Invalid --week format: ${weekArg} (expected YYYY-MM-DD)`);
      process.exit(1);
    }
    weekStart = new Date(y, m - 1, d);
  } else {
    const now = new Date();
    const day = now.getDay();
    const diff = day === 0 ? -6 : 1 - day;
    weekStart = new Date(now);
    weekStart.setDate(now.getDate() + diff);
    weekStart.setHours(0, 0, 0, 0);
  }

  const corePeers = await prisma.benchmarkPage.findMany({
    where: { benchmarkRole: "core_peer", isOwnPage: false },
    orderBy: { name: "asc" },
    include: {
      _count: { select: { posts: true } },
      audienceSnapshots: { orderBy: { capturedAt: "desc" }, take: 1 },
    },
  });

  if (corePeers.length === 0) {
    console.error("No external core peers found. Run `npm run benchmark:seed-peers` first.");
    process.exit(1);
  }

  const peers: CollectionPeer[] = corePeers.map((p) => ({
    id: p.id,
    name: p.name,
    canonicalUrl: p.canonicalUrl,
    objectType: p.objectType,
    scaleBand: p.scaleBand,
    category: p.category,
    collectionFrequency: p.collectionFrequency,
    recommendedPostsPerCollection: p.recommendedPostsPerCollection,
    audienceCount: p.audienceSnapshots[0]?.audienceCount ?? null,
    audienceCountType: p.audienceSnapshots[0]?.audienceCountType ?? null,
    audienceCapturedAt: p.audienceSnapshots[0]?.capturedAt ?? null,
    postCount: p._count.posts,
  }));

  const result = generateCollectionPack(peers, weekStart, process.cwd());

  console.log(`✓ Collection pack generated for week ${result.weekKey}`);
  console.log(`  ${result.outDir}/`);
  for (const f of result.files) {
    console.log(`    ├── ${f}`);
  }
  console.log(`  Peers: ${result.peerCount} | Target rows: ${result.targetRows}`);
  console.log(`\nNext step: User manually collects data, fills template, imports via /public-benchmark/import`);

  await prisma.$disconnect();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
