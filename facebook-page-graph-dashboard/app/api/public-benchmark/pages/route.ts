import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

/**
 * GET /api/public-benchmark/pages
 * List all benchmark pages with filters.
 * Query: ?role= & ?objectType= & ?scaleBand= & ?active=true
 */
export async function GET(req: Request) {
  return withFbErrors(async () => {
    const url = new URL(req.url);
    const role = url.searchParams.get("role");
    const objectType = url.searchParams.get("objectType");
    const scaleBand = url.searchParams.get("scaleBand");
    const active = url.searchParams.get("active");

    const where: { [key: string]: unknown } = {};
    if (role) where.benchmarkRole = role;
    if (objectType) where.objectType = objectType;
    if (scaleBand) where.scaleBand = scaleBand;
    if (active === "true") where.activeStatus = "active";

    const pages = await prisma.benchmarkPage.findMany({
      where,
      orderBy: [{ isOwnPage: "desc" }, { benchmarkRole: "asc" }, { name: "asc" }],
      include: {
        _count: {
          select: {
            posts: true,
            audienceSnapshots: true,
          },
        },
      },
    });

    return ok({
      total: pages.length,
      pages,
    });
  });
}
