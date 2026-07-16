import { prisma } from "@/lib/prisma";
import { err } from "@/lib/env";
import { toCsv } from "@/lib/csv";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

/**
 * GET /api/imports/:id/export-unmatched
 * Export unmatched/ambiguous rows ra CSV.
 */
export async function GET(_req: Request, ctx: { params: { id: string } }) {
  const id = Number(ctx.params.id);
  if (!Number.isFinite(id)) {
    return err("unknown_error", "id không hợp lệ", 400);
  }

  const batch = await prisma.insightImportBatch.findUnique({ where: { id } });
  if (!batch) {
    return err("unknown_error", "Batch không tồn tại", 404);
  }

  const rows = await prisma.importedPostInsight.findMany({
    where: {
      batchId: id,
      matchStatus: { in: ["unmatched", "ambiguous"] },
    },
    orderBy: { id: "asc" },
    take: 1000,
  });

  const csv = toCsv(
    rows.map((r) => ({
      matchStatus: r.matchStatus,
      postId: r.postId ?? "",
      permalinkUrl: r.permalinkUrl ?? "",
      createdTime: r.createdTime ?? "",
      messageSnippet: r.messageSnippet ?? "",
      reach: r.reach ?? "",
      impressions: r.impressions ?? "",
      engagedUsers: r.engagedUsers ?? "",
      clicks: r.clicks ?? "",
      reactions: r.reactions ?? "",
      comments: r.comments ?? "",
      shares: r.shares ?? "",
      videoViews: r.videoViews ?? "",
    })),
    [
      "matchStatus",
      "postId",
      "permalinkUrl",
      "createdTime",
      "messageSnippet",
      "reach",
      "impressions",
      "engagedUsers",
      "clicks",
      "reactions",
      "comments",
      "shares",
      "videoViews",
    ],
  );

  return new Response(csv, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="unmatched-batch-${id}.csv"`,
    },
  });
}
