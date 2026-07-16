/**
 * Video Asset Linking Script — match VideoAsset to Post via title + date.
 * Usage: npx tsx scripts/link-video-assets.ts
 *
 * Strategy:
 * 1. Permalink video ID match (confidence 1.0) — different ID spaces, 0 matches expected.
 * 2. Title substring match (confidence 0.8) — VideoAsset.title appears in Post.message.
 * 3. Title + same-day match (confidence 0.95) — title match AND createdTime same day.
 *
 * Only auto-link confidence >= 0.9. Others go to candidate review CSV.
 */
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  console.log("═══════════════════════════════════════════════════════════");
  console.log("  Video Asset Linking Report");
  console.log("═══════════════════════════════════════════════════════════\n");

  const assets = await prisma.videoAsset.findMany({
    where: { matchedPostId: null },
    select: { id: true, externalVideoId: true, title: true, createdTime: true },
  });
  console.log(`Unlinked assets: ${assets.length}`);

  const posts = await prisma.post.findMany({
    select: { fbPostId: true, message: true, createdTime: true, permalinkUrl: true },
  });

  let linked = 0;
  let candidates = 0;
  const candidateRows: any[] = [];

  for (const va of assets) {
    if (!va.title || va.title.length < 10) continue;
    const titleSnippet = va.title.slice(0, 20);

    // Find posts with matching title snippet
    const matches = posts.filter((p) => p.message && p.message.includes(titleSnippet));
    if (matches.length === 0) continue;

    if (matches.length === 1) {
      // Single match — check date proximity (±1 day to account for timezone)
      let confidence = 0.80;
      if (va.createdTime && matches[0].createdTime) {
        const vaDate = new Date(va.createdTime + "T00:00:00Z").getTime();
        const postDate = new Date(matches[0].createdTime).getTime();
        const dayDiff = Math.abs(vaDate - postDate) / (24 * 3600 * 1000);
        if (dayDiff <= 1.5) confidence = 0.95; // Same day or ±1 (timezone)
      }

      if (confidence >= 0.9) {
        await prisma.videoAsset.update({
          where: { id: va.id },
          data: { matchedPostId: matches[0].fbPostId },
        });
        linked++;
        console.log(`  ✓ Linked ${va.externalVideoId} → ${matches[0].fbPostId} (conf=${confidence})`);
      } else {
        candidateRows.push({
          videoAssetId: va.externalVideoId,
          title: va.title,
          candidatePostId: matches[0].fbPostId,
          confidence,
          reason: "title match, date mismatch",
        });
        candidates++;
      }
    } else {
      // Multiple matches — ambiguous, send to review
      for (const m of matches.slice(0, 3)) {
        candidateRows.push({
          videoAssetId: va.externalVideoId,
          title: va.title,
          candidatePostId: m.fbPostId,
          confidence: 0.60,
          reason: `ambiguous (${matches.length} matches)`,
        });
      }
      candidates++;
    }
  }

  console.log(`\n=== Summary ===`);
  console.log(`  Total unlinked: ${assets.length}`);
  console.log(`  Auto-linked (conf≥0.9): ${linked}`);
  console.log(`  Candidates (review needed): ${candidates}`);
  console.log(`  Still unlinked: ${assets.length - linked}`);

  if (candidateRows.length > 0) {
    console.log(`\n=== Top candidates ===`);
    for (const c of candidateRows.slice(0, 10)) {
      console.log(`  ${c.videoAssetId} → ${c.candidatePostId} (conf=${c.confidence}) ${c.reason}`);
    }
  }

  // Final count
  const totalLinked = await prisma.videoAsset.count({ where: { matchedPostId: { not: null } } });
  console.log(`\nTotal linked assets in DB: ${totalLinked}`);

  await prisma.$disconnect();
}

main().catch(console.error);
