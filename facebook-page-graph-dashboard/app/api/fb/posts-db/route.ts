import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";
import { topicLabel } from "@/lib/metrics";

export const dynamic = "force-dynamic";

/**
 * GET /api/fb/posts-db
 * Đọc bảng Post từ database (đã sync), hỗ trợ sort.
 */
export async function GET(req: Request) {
  return withFbErrors(async () => {
    const url = new URL(req.url);
    const sort = url.searchParams.get("sort") ?? "createdTime";
    const order = url.searchParams.get("order") ?? "desc";
    const limitRaw = Number(url.searchParams.get("limit") ?? "100");
    const limit = Math.max(1, Math.min(500, limitRaw));

    const validSort = ["createdTime", "reach", "commentsCount", "engagementRate", "score", "sharesCount"];
    const sortField = validSort.includes(sort) ? sort : "createdTime";
    const sortOrder = order === "asc" ? "asc" : "desc";

    const posts = await prisma.post.findMany({
      orderBy: { [sortField]: sortOrder },
      take: limit,
    });

    return ok({
      posts: posts.map((p) => ({
        ...p,
        topicLabel: topicLabel(p.topic),
      })),
    });
  });
}
