import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

/**
 * GET /api/public-benchmark/posts
 * Query: ?pageId= & ?limit=50 & ?offset=0 & ?sort=comparableEngagement|postedAt
 */
export async function GET(req: Request) {
  return withFbErrors(async () => {
    const url = new URL(req.url);
    const pageId = url.searchParams.get("pageId");
    const limit = Math.min(parseInt(url.searchParams.get("limit") ?? "50"), 500);
    const offset = parseInt(url.searchParams.get("offset") ?? "0");
    const sort = url.searchParams.get("sort") ?? "postedAt";

    const where: { [key: string]: unknown } = {};
    if (pageId) where.benchmarkPageId = parseInt(pageId);

    const orderBy: { [key: string]: "asc" | "desc" } =
      sort === "comparableEngagement"
        ? { comparableEngagement: "desc" }
        : sort === "reactions"
          ? { reactions: "desc" }
          : { postedAt: "desc" };

    const [posts, total] = await Promise.all([
      prisma.benchmarkPost.findMany({
        where,
        orderBy,
        take: limit,
        skip: offset,
        include: {
          page: {
            select: { name: true, canonicalUrl: true, isOwnPage: true },
          },
        },
      }),
      prisma.benchmarkPost.count({ where }),
    ]);

    return ok({ posts, total, limit, offset });
  });
}
