import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

/**
 * GET /api/public-benchmark/audience
 * Get latest audience snapshots for all pages.
 */
export async function GET() {
  return withFbErrors(async () => {
    const pages = await prisma.benchmarkPage.findMany({
      include: {
        audienceSnapshots: {
          orderBy: { capturedAt: "desc" },
          take: 1,
        },
      },
      orderBy: [{ isOwnPage: "desc" }, { name: "asc" }],
    });

    const rows = pages.map((p) => ({
      pageId: p.id,
      name: p.name,
      isOwnPage: p.isOwnPage,
      benchmarkRole: p.benchmarkRole,
      scaleBand: p.scaleBand,
      audienceCount: p.audienceSnapshots[0]?.audienceCount ?? null,
      audienceCountType: p.audienceSnapshots[0]?.audienceCountType ?? null,
      capturedAt: p.audienceSnapshots[0]?.capturedAt ?? null,
      source: p.audienceSnapshots[0]?.source ?? null,
    }));

    return ok({ total: rows.length, pages: rows });
  });
}

/**
 * POST /api/public-benchmark/audience
 * Add audience snapshot.
 * Body: { benchmarkPageId, audienceCount, audienceCountType?, source?, notes? }
 */
export async function POST(req: Request) {
  return withFbErrors(async () => {
    const body = await req.json();

    if (!body.benchmarkPageId || body.audienceCount == null) {
      return ok({ error: "benchmarkPageId and audienceCount required" }, 400);
    }

    const page = await prisma.benchmarkPage.findUnique({
      where: { id: parseInt(body.benchmarkPageId) },
    });
    if (!page) return ok({ error: "Page not found" }, 404);

    const snapshot = await prisma.benchmarkAudienceSnapshot.create({
      data: {
        benchmarkPageId: page.id,
        audienceCount: parseInt(body.audienceCount),
        audienceCountType: body.audienceCountType ?? "followers",
        source: body.source ?? "manual_public",
        verificationConfidence: body.verificationConfidence ?? "medium",
        notes: body.notes ?? null,
      },
    });

    return ok({ snapshot, message: "Audience snapshot saved" });
  });
}
