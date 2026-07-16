import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

/**
 * GET /api/public-benchmark/peers
 * Return core peers grouped by scale band.
 */
export async function GET() {
  return withFbErrors(async () => {
    const corePeers = await prisma.benchmarkPage.findMany({
      where: {
        OR: [
          { benchmarkRole: "core_peer" },
          { isOwnPage: true },
        ],
      },
      orderBy: [{ scaleBand: "asc" }, { name: "asc" }],
      include: {
        _count: { select: { posts: true } },
      },
    });

    const byScale = corePeers.reduce(
      (acc, p) => {
        const band = p.scaleBand ?? "unknown";
        if (!acc[band]) acc[band] = [];
        acc[band].push(p);
        return acc;
      },
      {} as Record<string, typeof corePeers>,
    );

    return ok({
      total: corePeers.length,
      byScaleBand: Object.fromEntries(
        Object.entries(byScale).map(([k, v]) => [k, v.length]),
      ),
      peers: corePeers,
    });
  });
}

/**
 * POST /api/public-benchmark/peers
 * Add or update a benchmark peer page.
 * Body: { name, canonicalUrl, category?, benchmarkRole?, scaleBand?, notes? }
 */
export async function POST(req: Request) {
  return withFbErrors(async () => {
    const body = await req.json();

    if (!body.name || !body.canonicalUrl) {
      return ok({ error: "name and canonicalUrl are required" }, 400);
    }

    // Normalize URL
    let url = String(body.canonicalUrl).trim();
    if (!url.startsWith("http")) {
      url = "https://" + url;
    }

    const validRoles = ["core_peer", "watchlist", "topic_reference", "format_reference", "extended_creator_peer"];
    const role = validRoles.includes(body.benchmarkRole) ? body.benchmarkRole : "watchlist";

    const page = await prisma.benchmarkPage.upsert({
      where: { canonicalUrl: url },
      create: {
        name: String(body.name).trim(),
        canonicalUrl: url,
        platform: "facebook",
        objectType: "facebook_page",
        category: body.category || null,
        benchmarkRole: role,
        scaleBand: body.scaleBand || null,
        isOwnPage: false,
        activeStatus: "active",
        verificationConfidence: "medium",
        lastVerifiedAt: new Date(),
        notes: body.notes || null,
      },
      update: {
        name: String(body.name).trim(),
        category: body.category || undefined,
        benchmarkRole: role,
        scaleBand: body.scaleBand || undefined,
        notes: body.notes ?? undefined,
        lastVerifiedAt: new Date(),
      },
    });

    return ok({ page, message: "Peer added" });
  });
}
