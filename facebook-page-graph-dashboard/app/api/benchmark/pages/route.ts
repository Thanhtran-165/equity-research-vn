import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { ok, err, withFbErrors } from "@/lib/env";
import { normalizeCategory } from "@/lib/benchmark";

export const dynamic = "force-dynamic";

/**
 * GET /api/benchmark/pages?category=&includeInactive=
 */
export async function GET(req: Request) {
  return withFbErrors(async () => {
    const url = new URL(req.url);
    const category = url.searchParams.get("category");
    const includeInactive = url.searchParams.get("includeInactive") === "true";

    const where: any = {};
    if (!includeInactive) where.isActive = true;
    if (category && category !== "all") where.category = normalizeCategory(category);

    const pages = await prisma.competitorPage.findMany({
      where,
      orderBy: [{ category: "asc" }, { pageName: "asc" }],
    });

    return ok({ pages });
  });
}

/**
 * POST /api/benchmark/pages
 * Body: { pageName, pageUrl, category, description?, notes? }
 */
export async function POST(req: Request) {
  return withFbErrors(async () => {
    let body: any;
    try {
      body = await req.json();
    } catch {
      return err("unknown_error", "Body không phải JSON hợp lệ", 400);
    }

    const pageName = (body?.pageName ?? "").toString().trim();
    const pageUrl = (body?.pageUrl ?? "").toString().trim();
    const category = normalizeCategory(body?.category);
    const description = body?.description ? String(body.description) : null;
    const notes = body?.notes ? String(body.notes) : null;

    if (!pageName) return err("unknown_error", "Thiếu pageName", 400);
    if (!pageUrl) return err("unknown_error", "Thiếu pageUrl", 400);

    const existing = await prisma.competitorPage.findUnique({ where: { pageUrl } });
    if (existing) {
      return err("unknown_error", `Page URL đã tồn tại (id=${existing.id})`, 409);
    }

    const page = await prisma.competitorPage.create({
      data: { pageName, pageUrl, category, description, notes },
    });
    return ok({ page });
  });
}
