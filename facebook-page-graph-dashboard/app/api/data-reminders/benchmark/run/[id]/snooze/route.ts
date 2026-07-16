import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

/**
 * POST /api/data-reminders/benchmark/run/[id]/snooze
 * Snoozes the run by 1 day.
 */
export async function POST(_req: Request, { params }: { params: { id: string } }) {
  return withFbErrors(async () => {
    const runId = parseInt(params.id);
    const run = await prisma.benchmarkCollectionRun.findUnique({ where: { id: runId } });
    if (!run) return ok({ error: "Run not found" }, 404);

    const snoozedUntil = new Date();
    snoozedUntil.setDate(snoozedUntil.getDate() + 1);
    snoozedUntil.setHours(18, 0, 0, 0);

    const updated = await prisma.benchmarkCollectionRun.update({
      where: { id: runId },
      data: { snoozedUntil },
    });

    return ok({ run: updated, message: `Snoozed until ${snoozedUntil.toISOString()}` });
  });
}
