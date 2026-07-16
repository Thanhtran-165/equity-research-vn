import { prisma } from "@/lib/prisma";
import { ok, err, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

const VALID_STATUSES = [
  "pending", "meta_created", "downloaded", "renamed",
  "moved_to_incoming", "dry_run_ok", "applied_ok",
];

/**
 * POST /api/data-reminders/item/:id/check
 * Body: { status }
 */
export async function POST(req: Request, ctx: { params: { id: string } }) {
  return withFbErrors(async () => {
    const id = Number(ctx.params.id);
    if (!Number.isFinite(id)) return err("unknown_error", "id không hợp lệ", 400);

    const body = await req.json();
    const status = body?.status;
    if (!VALID_STATUSES.includes(status)) {
      return err("unknown_error", `Status không hợp lệ. Cho phép: ${VALID_STATUSES.join(", ")}`, 400);
    }

    const item = await prisma.dataReminderItem.findUnique({ where: { id } });
    if (!item) return err("unknown_error", "Item không tồn tại", 404);

    const now = new Date();
    const data: any = { status };
    if (status === "meta_created") data.metaCreatedAt = now;
    if (status === "downloaded") data.downloadedAt = now;
    if (status === "renamed") data.renamedAt = now;
    if (status === "moved_to_incoming") data.movedToIncomingAt = now;
    if (status === "dry_run_ok") data.dryRunAt = now;
    if (status === "applied_ok") data.appliedAt = now;

    const updated = await prisma.dataReminderItem.update({ where: { id }, data });

    // Check if run is completed
    const allItems = await prisma.dataReminderItem.findMany({ where: { runId: item.runId } });
    const requiredDone = allItems.filter((i) => i.required).every((i) => i.status === "applied_ok");
    if (requiredDone) {
      await prisma.dataReminderRun.update({
        where: { id: item.runId },
        data: { status: "completed", completedAt: now },
      });
    }

    return ok({ item: updated });
  });
}
