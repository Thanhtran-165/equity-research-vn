import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

/**
 * GET /api/competitors/status
 * Returns per-peer collection status for the dashboard.
 */
export async function GET() {
  return withFbErrors(async () => {
    const peers = await prisma.benchmarkPage.findMany({
      where: { benchmarkRole: "core_peer", isOwnPage: false },
      select: {
        id: true,
        name: true,
        canonicalUrl: true,
        lastCollectedAt: true,
        collectionStatus: true,
        collectionErrors: true,
        category: true,
        scaleBand: true,
      },
      orderBy: { name: "asc" },
    });

    // Get latest collection log per peer
    const logs = await prisma.collectionLog.findMany({
      where: { benchmarkPageId: { in: peers.map((p) => p.id) } },
      orderBy: { collectedAt: "desc" },
      take: peers.length * 3, // Recent few per peer
    });

    const latestLogByPeer = new Map<number, typeof logs[0]>();
    for (const log of logs) {
      if (!latestLogByPeer.has(log.benchmarkPageId)) {
        latestLogByPeer.set(log.benchmarkPageId, log);
      }
    }

    // Get post counts per peer from last 7 days
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    const postCounts = await prisma.benchmarkPost.groupBy({
      by: ["benchmarkPageId"],
      where: { capturedAt: { gte: sevenDaysAgo } },
      _count: true,
    });

    const postCountMap = new Map<number, number>();
    for (const pc of postCounts) {
      postCountMap.set(pc.benchmarkPageId, pc._count);
    }

    // Posts needing review (missing reactions or comments)
    const needsReview = await prisma.benchmarkPost.count({
      where: {
        capturedAt: { gte: sevenDaysAgo },
        OR: [{ reactionsObserved: false }, { commentsObserved: false }],
      },
    });

    return ok({
      peers: peers.map((p) => ({
        ...p,
        lastCollectionLog: latestLogByPeer.get(p.id) || null,
        postsLast7Days: postCountMap.get(p.id) || 0,
      })),
      needsReviewCount: needsReview,
      summary: {
        totalPeers: peers.length,
        successCount: peers.filter((p) => p.collectionStatus === "success").length,
        partialCount: peers.filter((p) => p.collectionStatus === "partial").length,
        unavailableCount: peers.filter((p) => p.collectionStatus === "unavailable" || p.collectionStatus === "blocked").length,
        neverCollected: peers.filter((p) => !p.collectionStatus || p.collectionStatus === "never").length,
      },
    });
  });
}
