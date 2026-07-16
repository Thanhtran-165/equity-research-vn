import { prisma } from "@/lib/prisma";
import { toCsv, csvFilename } from "@/lib/csv";
import { topicLabel } from "@/lib/metrics";

export const dynamic = "force-dynamic";

/**
 * GET /api/fb/export/posts
 * Xuất bảng posts ra CSV.
 */
export async function GET() {
  const posts = await prisma.post.findMany({
    orderBy: { createdTime: "desc" },
    take: 500,
  });

  const rows = posts.map((p) => ({
    createdTime: p.createdTime ?? "",
    fbPostId: p.fbPostId,
    topic: topicLabel(p.topic),
    postType: p.postType,
    message: p.message ?? "",
    permalinkUrl: p.permalinkUrl ?? "",
    reach: p.reach ?? "",
    impressions: p.impressions ?? "",
    reactionsCount: p.reactionsCount,
    commentsCount: p.commentsCount,
    sharesCount: p.sharesCount,
    clicks: p.clicks ?? "",
    engagementRate: p.engagementRate ?? "",
    score: p.score ?? "",
  }));

  const headers = [
    "createdTime",
    "fbPostId",
    "topic",
    "postType",
    "message",
    "permalinkUrl",
    "reach",
    "impressions",
    "reactionsCount",
    "commentsCount",
    "sharesCount",
    "clicks",
    "engagementRate",
    "score",
  ];

  const csv = toCsv(rows, headers);
  const filename = csvFilename("posts");

  return new Response(csv, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="${filename}"`,
    },
  });
}
