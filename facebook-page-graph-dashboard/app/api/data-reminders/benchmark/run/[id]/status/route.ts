import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

/**
 * POST /api/data-reminders/benchmark/run/[id]/status
 * Body: { status: "completed" | "skipped", notes?: string }
 */
export async function POST(req: Request, { params }: { params: { id: string } }) {
  return withFbErrors(async () => {
    const runId = parseInt(params.id);
    const body = await req.json();
    const { status, notes } = body;

    if (!["completed", "skipped", "pending", "in_progress"].includes(status)) {
      return ok({ error: "Invalid status. Use: completed, skipped, pending, or in_progress" }, 400);
    }

    const run = await prisma.benchmarkCollectionRun.findUnique({ where: { id: runId } });
    if (!run) return ok({ error: "Run not found" }, 404);

    const updateData: { status: string; notes?: string; completedAt?: Date } = { status };
    if (notes != null) updateData.notes = notes;
    if (status === "completed") updateData.completedAt = new Date();

    const updated = await prisma.benchmarkCollectionRun.update({
      where: { id: runId },
      data: updateData,
      include: { items: { include: { page: true } } },
    });

    return ok({ run: updated, message: `Run ${status}` });
  });
}
