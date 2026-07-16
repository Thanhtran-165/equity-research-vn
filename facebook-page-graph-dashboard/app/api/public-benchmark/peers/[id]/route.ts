import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

/**
 * DELETE /api/public-benchmark/peers/[id]
 * Remove a peer from benchmark. Cannot delete own page.
 */
export async function DELETE(_req: Request, { params }: { params: { id: string } }) {
  return withFbErrors(async () => {
    const pageId = parseInt(params.id);

    const page = await prisma.benchmarkPage.findUnique({ where: { id: pageId } });
    if (!page) {
      return ok({ error: "Page not found" }, 404);
    }

    // Guard: cannot delete own page
    if (page.isOwnPage) {
      return ok({ error: "Cannot delete own page" }, 400);
    }

    await prisma.benchmarkPage.delete({ where: { id: pageId } });

    return ok({ deleted: true, id: pageId, name: page.name });
  });
}

/**
 * PATCH /api/public-benchmark/peers/[id]
 * Update a peer's role or metadata.
 */
export async function PATCH(req: Request, { params }: { params: { id: string } }) {
  return withFbErrors(async () => {
    const pageId = parseInt(params.id);
    const body = await req.json();

    const page = await prisma.benchmarkPage.findUnique({ where: { id: pageId } });
    if (!page) {
      return ok({ error: "Page not found" }, 404);
    }

    const updateData: Record<string, unknown> = {};
    if (body.benchmarkRole) updateData.benchmarkRole = body.benchmarkRole;
    if (body.category !== undefined) updateData.category = body.category;
    if (body.scaleBand !== undefined) updateData.scaleBand = body.scaleBand;
    if (body.notes !== undefined) updateData.notes = body.notes;
    if (body.activeStatus) updateData.activeStatus = body.activeStatus;

    const updated = await prisma.benchmarkPage.update({
      where: { id: pageId },
      data: updateData,
    });

    return ok({ page: updated, message: "Updated" });
  });
}
