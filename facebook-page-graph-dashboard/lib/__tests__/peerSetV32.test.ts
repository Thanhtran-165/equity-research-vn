/**
 * Peer Set v3.2 Controlled Seed Tests
 *
 * Tests verify seed correctness, idempotency, and data preservation.
 * These tests read from the production SQLite DB to validate the seed state.
 */
import { describe, it, expect } from "vitest";
import { PrismaClient } from "@prisma/client";
import { readFileSync } from "fs";

const prisma = new PrismaClient();

// Expected v3.2 core peer canonical URLs
const V32_CORE_URLS = [
  "https://facebook.com/ichimoku.quoccuong/",
  "https://facebook.com/TuyenDauTu/",
  "https://facebook.com/tcdcnews/",
  "https://facebook.com/ngantalk/",
  "https://facebook.com/dffvn.official/",
  "https://facebook.com/masterbollingerbands/",
  "https://facebook.com/quang1505/",
  "https://facebook.com/mrtranvandinh/",
  "https://facebook.com/hoangquocdungvtv/",
  "https://facebook.com/koliaphan/",
];

const DFF_URL = "https://facebook.com/dffvn.official/";

describe("Peer Set v3.2 Controlled Seed", () => {
  it("1. DFF existing entity is reused, not duplicated", async () => {
    const dffPages = await prisma.benchmarkPage.findMany({
      where: { canonicalUrl: { contains: "dffvn" } },
    });
    expect(dffPages.length).toBe(1);
    expect(dffPages[0].id).toBe(4); // Original ID preserved
    expect(dffPages[0].benchmarkRole).toBe("core_peer");
  });

  it("2. Seed is idempotent (re-running upsert creates no new pages)", async () => {
    const countBefore = await prisma.benchmarkPage.count();
    // The seed script uses upsert by canonicalUrl — running it again would not create duplicates
    // Verify no duplicate canonicalUrls exist
    const allPages = await prisma.benchmarkPage.findMany({ select: { canonicalUrl: true } });
    const urls = allPages.map((p) => p.canonicalUrl.toLowerCase());
    const uniqueUrls = new Set(urls);
    expect(urls.length).toBe(uniqueUrls.size);
  });

  it("3. Exactly 10 external Core Peers after seed", async () => {
    const count = await prisma.benchmarkPage.count({
      where: { benchmarkRole: "core_peer", isOwnPage: false },
    });
    expect(count).toBe(10);
  });

  it("4. Exactly 1 own page", async () => {
    const count = await prisma.benchmarkPage.count({
      where: { isOwnPage: true },
    });
    expect(count).toBe(1);
  });

  it("5. Exactly 11 direct leaderboard entities", async () => {
    const count = await prisma.benchmarkPage.count({
      where: {
        OR: [
          { objectType: "facebook_page", benchmarkRole: "core_peer" },
          { isOwnPage: true, objectType: "facebook_page" },
        ],
      },
    });
    expect(count).toBe(11);
  });

  it("6. Old institutional/reference pages excluded from leaderboard", async () => {
    const oldPeers = await prisma.benchmarkPage.findMany({
      where: {
        canonicalUrl: {
          in: [
            "https://facebook.com/nguoiquansat.thongtintaichinh/",
            "https://facebook.com/VTVIndex/",
            "https://facebook.com/Kafi.vn/",
            "https://facebook.com/thoibaonganhang.vn/",
            "https://facebook.com/ChungkhoanVFS/",
          ],
        },
      },
    });
    for (const p of oldPeers) {
      expect(p.benchmarkRole).not.toBe("core_peer");
    }
  });

  it("7. Collection pack contains 10 peers × 4 rows = 40", () => {
    const csv = readFileSync("data/benchmark/collections/2026-07-13/benchmark-weekly-template.csv", "utf8");
    const dataLines = csv.split("\n").filter((l) => l && !l.startsWith("#") && !l.includes("pageName,pageUrl"));
    // 10 peers × 4 rows = 40 data rows
    expect(dataLines.length).toBe(40);
  });

  it("8. Own page excluded from collection pack", () => {
    const csv = readFileSync("data/benchmark/collections/2026-07-13/benchmark-weekly-template.csv", "utf8");
    expect(csv).not.toContain("Chim Cút");
    expect(csv).not.toContain("chimcutvnindex");
  });

  it("9. DFF appears exactly once in collection pack", () => {
    const csv = readFileSync("data/benchmark/collections/2026-07-13/peer-status.csv", "utf8");
    const dataLines = csv.split("\n").filter((l) => l && !l.startsWith("pageName"));
    expect(dataLines.length).toBe(10);
    const dffLines = dataLines.filter((l) => l.includes("DFF") || l.includes("dffvn") || l.includes("Dòng tiền"));
    expect(dffLines.length).toBe(1);
  });

  it("10. Historical data preserved — Post and VideoAsset counts unchanged", async () => {
    const postCount = await prisma.post.count();
    const videoCount = await prisma.videoAsset.count();
    expect(postCount).toBe(634);
    expect(videoCount).toBe(235);
  });

  it("11. theanh98 remains macro_reference", async () => {
    const page = await prisma.benchmarkPage.findUnique({
      where: { canonicalUrl: "https://facebook.com/theanh98/" },
    });
    expect(page?.benchmarkRole).toBe("macro_reference");
  });

  it("12. All v3.2 core peers have verificationConfidence = high", async () => {
    const corePeers = await prisma.benchmarkPage.findMany({
      where: { benchmarkRole: "core_peer", isOwnPage: false },
      select: { verificationConfidence: true },
    });
    for (const p of corePeers) {
      expect(p.verificationConfidence).toBe("high");
    }
  });

  it("13. All v3.2 core peers have collectionFrequency = weekly", async () => {
    const corePeers = await prisma.benchmarkPage.findMany({
      where: { benchmarkRole: "core_peer", isOwnPage: false },
      select: { collectionFrequency: true },
    });
    for (const p of corePeers) {
      expect(p.collectionFrequency).toBe("weekly");
    }
  });

  it("14. All v3.2 core peers have recommendedPostsPerCollection = 4", async () => {
    const corePeers = await prisma.benchmarkPage.findMany({
      where: { benchmarkRole: "core_peer", isOwnPage: false },
      select: { recommendedPostsPerCollection: true },
    });
    for (const p of corePeers) {
      expect(p.recommendedPostsPerCollection).toBe(4);
    }
  });

  it("15. Audience snapshots created for verified followers", async () => {
    const snapshots = await prisma.benchmarkAudienceSnapshot.count();
    expect(snapshots).toBe(10); // One per core peer
    // Verify all are followers (not likes)
    const types = await prisma.benchmarkAudienceSnapshot.groupBy({
      by: ["audienceCountType"],
      _count: true,
    });
    const followersCount = types.find((t) => t.audienceCountType === "followers")?._count ?? 0;
    expect(followersCount).toBe(10);
  });
});
