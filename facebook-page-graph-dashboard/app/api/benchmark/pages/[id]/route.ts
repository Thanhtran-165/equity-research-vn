import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { ok, err, withFbErrors } from "@/lib/env";
import { normalizeCategory } from "@/lib/benchmark";

export const dynamic = "force-dynamic";

/**
 * PATCH /api/benchmark/pages/:id
 * Update competitor page (pageName, category, description, notes, isActive).
 */
export async function PATCH(req: Request, ctx: { params: { id: string } }) {
  return withFbErrors(async () => {
    const id = Number(ctx.params.id);
    if (!Number.isFinite(id)) return err("unknown_error", "id không hợp lệ", 400);

    let body: any;
    try {
      body = await req.json();
    } catch {
      return err("unknown_error", "Body không phải JSON hợp lệ", 400);
    }

    const existing = await prisma.competitorPage.findUnique({ where: { id } });
    if (!existing) return err("unknown_error", "Không tìm thấy page", 404);

    const data: any = {};
    if (body?.pageName != null) data.pageName = String(body.pageName).trim();
    if (body?.category != null) data.category = normalizeCategory(body.category);
    if (body?.description !== undefined) data.description = body.description ? String(body.description) : null;
    if (body?.notes !== undefined) data.notes = body.notes ? String(body.notes) : null;
    if (body?.isActive !== undefined) data.isActive = Boolean(body.isActive);
    // pageUrl thay đổi có thể vi phạm unique, chỉ cho phép nếu khác cũ và không trùng
    if (body?.pageUrl != null) {
      const newUrl = String(body.pageUrl).trim();
      if (newUrl && newUrl !== existing.pageUrl) {
        const dup = await prisma.competitorPage.findUnique({ where: { pageUrl: newUrl } });
        if (dup) return err("unknown_error", "pageUrl đã được dùng bởi page khác", 409);
        data.pageUrl = newUrl;
      }
    }

    const updated = await prisma.competitorPage.update({ where: { id }, data });
    return ok({ page: updated });
  });
}

/**
 * DELETE /api/benchmark/pages/:id
 * Soft delete (isActive=false). Nếu ?hard=true thì xoá thật (kèm snapshot).
 */
export async function DELETE(req: Request, ctx: { params: { id: string } }) {
  return withFbErrors(async () => {
    const id = Number(ctx.params.id);
    if (!Number.isFinite(id)) return err("unknown_error", "id không hợp lệ", 400);
    const url = new URL(req.url);
    const hard = url.searchParams.get("hard") === "true";

    const existing = await prisma.competitorPage.findUnique({ where: { id } });
    if (!existing) return err("unknown_error", "Không tìm thấy page", 404);

    if (hard) {
      await prisma.competitorPage.delete({ where: { id } });
      return ok({ deleted: true, hard: true });
    }
    const updated = await prisma.competitorPage.update({
      where: { id },
      data: { isActive: false },
    });
    return ok({ page: updated, softDeleted: true });
  });
}
