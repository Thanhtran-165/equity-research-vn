import { prisma } from "@/lib/prisma";
import { ok, err } from "@/lib/env";

export const dynamic = "force-dynamic";

/**
 * GET /api/fb/moderation
 * Query:
 *   ?riskLevel=high|medium|low
 *   ?status=new|flagged|reviewed|replied|hidden
 *   ?limit=...
 */
export async function GET(req: Request) {
  const url = new URL(req.url);
  const riskLevel = url.searchParams.get("riskLevel");
  const status = url.searchParams.get("status");
  const limitRaw = Number(url.searchParams.get("limit") ?? "200");
  const limit = Math.max(1, Math.min(500, limitRaw));

  // Lấy comment có status flagged hoặc new (hoặc theo filter)
  const where: any = {};
  if (riskLevel) where.riskLevel = riskLevel;
  if (status) {
    where.status = status;
  } else {
    where.status = { in: ["flagged", "new"] };
  }

  const comments = await prisma.comment.findMany({
    where,
    orderBy: [{ riskLevel: "desc" }, { createdTime: "desc" }],
    take: limit,
    include: { post: { select: { message: true, permalinkUrl: true } } },
  });

  return ok({ comments });
}
