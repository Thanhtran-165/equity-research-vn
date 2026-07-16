/**
 * Controlled Seed Peer Set v3.2
 *
 * Dry-run identity reconciliation → transactional seed:
 *   - UPDATE DFF (existing ID=4): promote to v3.2 metadata
 *   - DOWNGRADE 6 old core peers (keep data, change role)
 *   - CREATE 9 new core peers
 *   - Verify final state: 10 external core + 1 own page = 11 leaderboard entities
 *
 * Usage: npx tsx scripts/seed-peer-set-v3-2.ts
 */
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();
const now = new Date();

interface ApprovedPeer {
  name: string;
  url: string;
  objectType: string;
  operatingModel: string;
  category: string;
  scaleBand: string;
  followers: number;
  vertical: string;
  ecosystem: string;
  videoShare: number;
  promoShare: number;
  notes: string;
}

const approvedPeers: ApprovedPeer[] = [
  { name: "Ichimoku Quốc Cường", url: "https://facebook.com/ichimoku.quoccuong/", objectType: "facebook_page", operatingModel: "stock_creator", category: "stock_market", scaleBand: "medium", followers: 188535, vertical: "stock", ecosystem: "ITP", videoShare: 80, promoShare: 15, notes: "ITP co-founder; daily VNIndex livestreams; ~189K followers; verified badge" },
  { name: "Chứng Khoán 5 Phút", url: "https://facebook.com/TuyenDauTu/", objectType: "facebook_page", operatingModel: "stock_creator", category: "stock_market", scaleBand: "small", followers: 23000, vertical: "stock", ecosystem: "CK5P", videoShare: 70, promoShare: 10, notes: "Multi-platform video; 23K followers; verified badge; TikTok+YouTube cross-platform" },
  { name: "TCDC News", url: "https://facebook.com/tcdcnews/", objectType: "facebook_page", operatingModel: "stock_creator", category: "stock_market", scaleBand: "small", followers: 29000, vertical: "stock", ecosystem: "TCDC", videoShare: 90, promoShare: 5, notes: "Daily market analysis videos; 29K followers; Reels tab active" },
  { name: "Ngân Talk", url: "https://facebook.com/ngantalk/", objectType: "facebook_page", operatingModel: "gold_creator", category: "gold_usd", scaleBand: "medium", followers: 217635, vertical: "gold", ecosystem: "NgânTalk", videoShare: 60, promoShare: 0, notes: "Pure gold/silver commentator; Monthly Gold Compass; 218K followers; no courses" },
  { name: "Trần Duy Phương (DFF)", url: "https://facebook.com/dffvn.official/", objectType: "facebook_page", operatingModel: "gold_creator", category: "gold_usd", scaleBand: "small", followers: 40296, vertical: "gold", ecosystem: "DFF", videoShare: 50, promoShare: 5, notes: "Gold analyst; SJC vs world; VTC News regular; 40K followers; DFF/Trần Duy Phương ecosystem" },
  { name: "Master Bollinger Bands (Nguyễn Phước Hải)", url: "https://facebook.com/masterbollingerbands/", objectType: "facebook_page", operatingModel: "gold_creator", category: "gold_usd", scaleBand: "small", followers: 14000, vertical: "gold", ecosystem: "MBB", videoShare: 80, promoShare: 5, notes: "Bollinger Bands gold/XAUUSD analysis; owner Nguyễn Phước Hải; 14K followers" },
  { name: "Trần Khánh Quang", url: "https://facebook.com/quang1505/", objectType: "facebook_page", operatingModel: "real_estate_creator", category: "real_estate", scaleBand: "small", followers: 18268, vertical: "real_estate", ecosystem: "ViệtAnHoa", videoShare: 40, promoShare: 15, notes: "CEO Việt An Hoa; RE investment philosophy; 18K followers; 'Real Estate Doctor'" },
  { name: "Trần Văn Định", url: "https://facebook.com/mrtranvandinh/", objectType: "facebook_page", operatingModel: "real_estate_creator", category: "real_estate", scaleBand: "small", followers: 137141, vertical: "real_estate", ecosystem: "TVD", videoShare: 70, promoShare: 15, notes: "RE investment expert; 137K followers; YouTube cross-platform; active May 2026" },
  { name: "Hoàng Quốc Dũng", url: "https://facebook.com/hoangquocdungvtv/", objectType: "facebook_page", operatingModel: "real_estate_creator", category: "real_estate", scaleBand: "small", followers: 28000, vertical: "real_estate", ecosystem: "HQD", videoShare: 60, promoShare: 15, notes: "Review BĐS group admin; project review videos; 28K followers; Vinhomes content" },
  { name: "Kolia Phan", url: "https://facebook.com/koliaphan/", objectType: "facebook_page", operatingModel: "macro_multi_asset_creator", category: "macro_economics", scaleBand: "small", followers: 43939, vertical: "macro", ecosystem: "Kolia", videoShare: 70, promoShare: 20, notes: "Forbes VN Top 6 Finance KOL 2024; multi-asset (stocks+gold+silver); 44K followers" },
];

// URLs to downgrade (6 old core peers, excluding DFF which stays)
const downgradeUrls = [
  { url: "https://facebook.com/nguoiquansat.thongtintaichinh/", role: "topic_reference", notes: "Media outlet 563K; 12.5x scale; editorial — audit downgrade v3.2" },
  { url: "https://facebook.com/VTVIndex/", role: "topic_reference", notes: "VTV institutional media — audit downgrade v3.2" },
  { url: "https://facebook.com/Kafi.vn/", role: "institutional_reference", notes: "Corporate securities brand — audit downgrade v3.2" },
  { url: "https://facebook.com/thoibaonganhang.vn/", role: "institutional_reference", notes: "Editorial/news outlet — audit downgrade v3.2" },
  { url: "https://facebook.com/ChungkhoanVFS/", role: "institutional_reference", notes: "Corporate securities company — audit downgrade v3.2" },
  { url: "https://facebook.com/thuanphaisinhvn/", role: "extended_creator_peer", notes: "Text-first; pending format verification — audit downgrade v3.2" },
];

async function main() {
  console.log("=== Controlled Seed Peer Set v3.2 ===\n");

  // Step 1: Dry-run reconciliation
  const allPages = await prisma.benchmarkPage.findMany();
  const actions: { name: string; url: string; action: string; existingId?: number }[] = [];

  for (const peer of approvedPeers) {
    const existing = allPages.find(
      (p) => p.canonicalUrl.toLowerCase() === peer.url.toLowerCase() ||
             (peer.url.includes("dffvn") && p.canonicalUrl.includes("dffvn")),
    );
    if (existing) {
      actions.push({ name: peer.name, url: peer.url, action: "UPDATE_EXISTING", existingId: existing.id });
    } else {
      actions.push({ name: peer.name, url: peer.url, action: "CREATE_NEW" });
    }
  }

  const createCount = actions.filter((a) => a.action === "CREATE_NEW").length;
  const updateCount = actions.filter((a) => a.action === "UPDATE_EXISTING").length;
  console.log(`Dry-run: ${updateCount} update existing, ${createCount} create new`);
  for (const a of actions) {
    console.log(`  ${a.action}: ${a.name}${a.existingId ? ` (ID=${a.existingId})` : ""}`);
  }

  // Step 2: Transactional seed
  console.log("\n=== Applying seed in transaction ===");
  await prisma.$transaction(async (tx) => {
    // 2a: Downgrade 6 old core peers
    for (const d of downgradeUrls) {
      await tx.benchmarkPage.updateMany({
        where: { canonicalUrl: d.url },
        data: { benchmarkRole: d.role, notes: d.notes },
      });
    }
    console.log(`  ✓ Downgraded ${downgradeUrls.length} old core peers`);

    // 2b: Upsert 10 approved peers
    for (const peer of approvedPeers) {
      await tx.benchmarkPage.upsert({
        where: { canonicalUrl: peer.url },
        create: {
          name: peer.name,
          canonicalUrl: peer.url,
          platform: "facebook",
          objectType: peer.objectType,
          category: peer.category,
          benchmarkRole: "core_peer",
          scaleBand: peer.scaleBand,
          collectionFrequency: "weekly",
          recommendedPostsPerCollection: 4,
          isOwnPage: false,
          activeStatus: "active",
          verificationConfidence: "high",
          lastVerifiedAt: now,
          notes: `[${peer.operatingModel}] ${peer.notes}`,
        },
        update: {
          name: peer.name,
          objectType: peer.objectType,
          category: peer.category,
          benchmarkRole: "core_peer",
          scaleBand: peer.scaleBand,
          collectionFrequency: "weekly",
          recommendedPostsPerCollection: 4,
          activeStatus: "active",
          verificationConfidence: "high",
          lastVerifiedAt: now,
          notes: `[${peer.operatingModel}] ${peer.notes}`,
        },
      });

      // Add audience snapshot if followers verified
      const page = await tx.benchmarkPage.findUnique({ where: { canonicalUrl: peer.url } });
      if (page && peer.followers) {
        // Check if snapshot already exists for this date
        const existingSnap = await tx.benchmarkAudienceSnapshot.findFirst({
          where: { benchmarkPageId: page.id, capturedAt: now, audienceCount: peer.followers },
        });
        if (!existingSnap) {
          await tx.benchmarkAudienceSnapshot.create({
            data: {
              benchmarkPageId: page.id,
              audienceCount: peer.followers,
              audienceCountType: "followers",
              source: "manual_browser_verified",
              verificationConfidence: "high",
              capturedAt: now,
            },
          });
        }
      }
    }
    console.log(`  ✓ Upserted ${approvedPeers.length} approved peers (with audience snapshots)`);
  });

  // Step 3: Verify final state
  const corePeers = await prisma.benchmarkPage.count({ where: { benchmarkRole: "core_peer", isOwnPage: false } });
  const ownPage = await prisma.benchmarkPage.count({ where: { isOwnPage: true } });
  const totalPages = await prisma.benchmarkPage.count();

  console.log("\n=== Final state verification ===");
  console.log(`  External Core Peers: ${corePeers} (expected 10)`);
  console.log(`  Own Pages: ${ownPage} (expected 1)`);
  console.log(`  Total BenchmarkPage: ${totalPages} (was 26, expected 35)`);
  console.log(`  Leaderboard entities: ${corePeers + ownPage} (expected 11)`);

  if (corePeers !== 10 || ownPage !== 1) {
    throw new Error(`VERIFICATION FAILED: expected 10 core + 1 own, got ${corePeers} + ${ownPage}`);
  }

  // Post-seed counts
  const [posts, videos, bp, bpost, ba, bps] = await Promise.all([
    prisma.post.count(),
    prisma.videoAsset.count(),
    prisma.benchmarkPage.count(),
    prisma.benchmarkPost.count(),
    prisma.benchmarkAudienceSnapshot.count(),
    prisma.benchmarkPeriodSnapshot.count(),
  ]);
  console.log(`\n  Data preservation: Post:${posts} Video:${videos} BPage:${bp} BPost:${bpost} BAud:${ba} BPer:${bps}`);

  console.log("\n✓ Seed applied successfully");
  await prisma.$disconnect();
}

main().catch((e) => {
  console.error("SEED FAILED — rolling back", e);
  process.exit(1);
});
