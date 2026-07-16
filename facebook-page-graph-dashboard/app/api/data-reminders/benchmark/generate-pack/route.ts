import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";
import { generateCollectionPack, type CollectionPeer } from "@/lib/benchmark/generateCollectionPack";
import { getCurrentWeekBounds } from "@/lib/reminders/benchmarkReminderPlan";

export const dynamic = "force-dynamic";

/**
 * POST /api/data-reminders/benchmark/generate-pack
 * Body: { weekStart?: "YYYY-MM-DD" }
 *
 * Generates the collection pack files on disk.
 */
export async function POST(req: Request) {
  return withFbErrors(async () => {
    const body = await req.json().catch(() => ({}));

    let weekStart: Date;
    if (body.weekStart) {
      const [y, m, d] = String(body.weekStart).split("-").map(Number);
      weekStart = new Date(y, m - 1, d);
    } else {
      weekStart = getCurrentWeekBounds(new Date()).weekStart;
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
      return ok({ error: "No external core peers found" }, 400);
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

    return ok({
      weekKey: result.weekKey,
      outputDir: result.outDir,
      files: result.files,
      peerCount: result.peerCount,
      targetRows: result.targetRows,
    });
  });
}
