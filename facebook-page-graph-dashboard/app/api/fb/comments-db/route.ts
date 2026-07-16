import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

/**
 * GET /api/fb/comments-db
 * Đọc bảng Comment từ database (từ sync hoặc từ moderation queue).
 * Filter ở frontend, nhưng cũng hỗ trợ query: riskLevel, status, fbPostId.
 */
export async function GET(req: Request) {
  return withFbErrors(async () => {
    const url = new URL(req.url);
    const riskLevel = url.searchParams.get("riskLevel");
    const status = url.searchParams.get("status");
    const fbPostId = url.searchParams.get("fbPostId");
    const limitRaw = Number(url.searchParams.get("limit") ?? "300");
    const limit = Math.max(1, Math.min(1000, limitRaw));

    const where: any = {};
    if (riskLevel) where.riskLevel = riskLevel;
    if (status) where.status = status;
    if (fbPostId) where.fbPostId = fbPostId;

    const comments = await prisma.comment.findMany({
      where,
      orderBy: [{ createdTime: "desc" }],
      take: limit,
      include: { post: { select: { message: true, permalinkUrl: true } } },
    });

    return ok({ comments });
  });
}
