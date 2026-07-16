import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { ok, err, withFbErrors } from "@/lib/env";
import { parseCsv } from "@/lib/csv";
import {
  calculateBenchmarkScore,
  deriveSnapshot,
  normalizeCategory,
  type DerivedSnapshot,
} from "@/lib/benchmark";

export const dynamic = "force-dynamic";

const EXPECTED_HEADERS = [
  "pageName",
  "pageUrl",
  "category",
  "periodStart",
  "periodEnd",
  "followers",
  "postsCount",
  "reactionsCount",
  "commentsCount",
  "sharesCount",
  "videoViews",
  "topPostUrl",
  "topPostEngagement",
  "activeAds",
  "dominantTopic",
  "notes",
];

function findHeaderIndex(headers: string[], name: string): number {
  const lower = headers.map((h) => h.trim().toLowerCase());
  return lower.indexOf(name.toLowerCase());
}

interface ParsedRow {
  pageName: string;
  pageUrl: string;
  category: string;
  periodStart: string;
  periodEnd: string;
  followers: number;
  postsCount: number;
  reactionsCount: number;
  commentsCount: number;
  sharesCount: number;
  videoViews: number | null;
  topPostUrl: string | null;
  topPostEngagement: number | null;
  activeAds: boolean | null;
  dominantTopic: string | null;
  notes: string | null;
}

function toNum(v: string | undefined): number {
  if (!v) return 0;
  const n = Number(String(v).trim().replace(/,/g, ""));
  return Number.isFinite(n) ? n : 0;
}
function toNumNull(v: string | undefined): number | null {
  if (!v || String(v).trim() === "") return null;
  const n = Number(String(v).trim().replace(/,/g, ""));
  return Number.isFinite(n) ? n : null;
}
function toBoolNull(v: string | undefined): boolean | null {
  if (!v || String(v).trim() === "") return null;
  const s = String(v).trim().toLowerCase();
  if (s === "true" || s === "1" || s === "yes") return true;
  if (s === "false" || s === "0" || s === "no") return false;
  return null;
}

/**
 * POST /api/benchmark/import-csv
 * Body: { csv: string }
 * Parse → validate → upsert CompetitorPage (theo pageUrl) → create snapshot.
 */
export async function POST(req: Request) {
  return withFbErrors(async () => {
    let body: any;
    try {
      body = await req.json();
    } catch {
      return err("unknown_error", "Body không phải JSON hợp lệ", 400);
    }
    const text: string = (body?.csv ?? "").toString();
    if (!text.trim()) return err("unknown_error", "Thiếu nội dung CSV", 400);

    const rows = parseCsv(text);
    if (rows.length < 2) {
      return err("unknown_error", "CSV cần có header + ít nhất 1 dòng dữ liệu", 400);
    }

    const header = rows[0].map((h) => h.trim());
    // kiểm tra header tối thiểu
    const missing = ["pageName", "pageUrl", "periodStart", "periodEnd"].filter(
      (h) => findHeaderIndex(header, h) < 0,
    );
    if (missing.length > 0) {
      return err("unknown_error", `Thiếu cột bắt buộc: ${missing.join(", ")}`, 400);
    }

    const idx: Record<string, number> = {};
    for (const h of EXPECTED_HEADERS) idx[h] = findHeaderIndex(header, h);

    const cell = (row: string[], key: string): string | undefined =>
      idx[key] >= 0 ? row[idx[key]] : undefined;

    const parsed: ParsedRow[] = [];
    const errors: { row: number; message: string }[] = [];
    const warnings: { row: number; message: string }[] = [];

    for (let r = 1; r < rows.length; r++) {
      const row = rows[r];
      const rowNum = r + 1;
      const pageName = (cell(row, "pageName") ?? "").trim();
      const pageUrl = (cell(row, "pageUrl") ?? "").trim();
      const periodStart = (cell(row, "periodStart") ?? "").trim();
      const periodEnd = (cell(row, "periodEnd") ?? "").trim();

      if (!pageName || !pageUrl || !periodStart || !periodEnd) {
        errors.push({
          row: rowNum,
          message: `Thiếu pageName/pageUrl/periodStart/periodEnd (dòng ${rowNum})`,
        });
        continue;
      }
      // validate date
      if (Number.isNaN(new Date(periodStart).getTime()) || Number.isNaN(new Date(periodEnd).getTime())) {
        errors.push({ row: rowNum, message: `Ngày không hợp lệ (dòng ${rowNum})` });
        continue;
      }

      const followers = toNum(cell(row, "followers"));
      const postsCount = toNum(cell(row, "postsCount"));
      const reactionsCount = toNum(cell(row, "reactionsCount"));
      const commentsCount = toNum(cell(row, "commentsCount"));
      const sharesCount = toNum(cell(row, "sharesCount"));
      const videoViews = toNumNull(cell(row, "videoViews"));
      const topPostEngagement = toNumNull(cell(row, "topPostEngagement"));

      if (followers <= 0) {
        warnings.push({ row: rowNum, message: `followers <= 0 (dòng ${rowNum})` });
      }
      if (postsCount <= 0) {
        warnings.push({ row: rowNum, message: `postsCount <= 0 (dòng ${rowNum})` });
      }
      if (videoViews == null) {
        warnings.push({ row: rowNum, message: `videoViews thiếu — score sẽ dùng trọng số fallback (dòng ${rowNum})` });
      }

      parsed.push({
        pageName,
        pageUrl,
        category: normalizeCategory(cell(row, "category")),
        periodStart,
        periodEnd,
        followers,
        postsCount,
        reactionsCount,
        commentsCount,
        sharesCount,
        videoViews,
        topPostUrl: cell(row, "topPostUrl") ? String(cell(row, "topPostUrl")) : null,
        topPostEngagement,
        activeAds: toBoolNull(cell(row, "activeAds")),
        dominantTopic: cell(row, "dominantTopic") ? String(cell(row, "dominantTopic")) : null,
        notes: cell(row, "notes") ? String(cell(row, "notes")) : null,
      });
    }

    if (parsed.length === 0) {
      return ok({
        importedRows: 0,
        skippedRows: rows.length - 1,
        errors,
        warnings,
      });
    }

    // Upsert page + snapshot
    let imported = 0;
    const skipped: string[] = [];
    for (const p of parsed) {
      try {
        const page = await prisma.competitorPage.upsert({
          where: { pageUrl: p.pageUrl },
          update: {
            pageName: p.pageName,
            category: p.category,
            followersLatest: p.followers,
            notes: p.notes ?? undefined,
          },
          create: {
            pageName: p.pageName,
            pageUrl: p.pageUrl,
            category: p.category,
            followersLatest: p.followers,
            notes: p.notes ?? null,
          },
        });

        const derived = deriveSnapshot({
          followers: p.followers,
          postsCount: p.postsCount,
          reactionsCount: p.reactionsCount,
          commentsCount: p.commentsCount,
          sharesCount: p.sharesCount,
          videoViews: p.videoViews,
          topPostEngagement: p.topPostEngagement,
          periodStart: p.periodStart,
          periodEnd: p.periodEnd,
        });

        const data = {
          competitorPageId: page.id,
          periodStart: p.periodStart,
          periodEnd: p.periodEnd,
          followers: p.followers,
          postsCount: p.postsCount,
          reactionsCount: p.reactionsCount,
          commentsCount: p.commentsCount,
          sharesCount: p.sharesCount,
          videoViews: p.videoViews,
          topPostUrl: p.topPostUrl,
          topPostEngagement: p.topPostEngagement,
          activeAds: p.activeAds,
          dominantTopic: p.dominantTopic,
          publicEngagement: derived.publicEngagement,
          publicEngagementPerPost: derived.publicEngagementPerPost,
          engagementPer1kFollowers: derived.engagementPer1kFollowers,
          avgReactionsPerPost: derived.avgReactionsPerPost,
          avgCommentsPerPost: derived.avgCommentsPerPost,
          avgSharesPerPost: derived.avgSharesPerPost,
          videoViewsPerFollower: derived.videoViewsPerFollower,
          commentIntensity: derived.commentIntensity,
          shareIntensity: derived.shareIntensity,
          postingFrequencyPerDay: derived.postingFrequencyPerDay,
          rawJson: JSON.stringify({ imported: true, source: "csv" }),
        };

        const existing = await prisma.competitorMetricSnapshot.findUnique({
          where: {
            competitorPageId_periodStart_periodEnd: {
              competitorPageId: page.id,
              periodStart: p.periodStart,
              periodEnd: p.periodEnd,
            },
          },
        });
        if (existing) {
          await prisma.competitorMetricSnapshot.update({ where: { id: existing.id }, data });
        } else {
          await prisma.competitorMetricSnapshot.create({ data });
        }
        imported++;
      } catch (e: any) {
        skipped.push(`${p.pageName}: ${e?.message ?? e}`);
      }
    }

    // Re-tính benchmarkScore cho mỗi (periodStart, periodEnd) xuất hiện
    const periods = new Set(parsed.map((p) => `${p.periodStart}|${p.periodEnd}`));
    for (const k of periods) {
      const [ps, pe] = k.split("|");
      await recalcScoresForPeriod(ps, pe);
    }

    return ok({
      importedRows: imported,
      skippedRows: skipped.length,
      errors,
      warnings,
      skippedDetails: skipped,
    });
  });
}

async function recalcScoresForPeriod(periodStart: string, periodEnd: string) {
  const all = await prisma.competitorMetricSnapshot.findMany({
    where: { periodStart, periodEnd },
  });
  if (all.length === 0) return;
  const population = all.map((s) => ({
    engagementPer1kFollowers: s.engagementPer1kFollowers,
    avgSharesPerPost: s.avgSharesPerPost,
    avgCommentsPerPost: s.avgCommentsPerPost,
    videoViewsPerFollower: s.videoViewsPerFollower,
    postingFrequencyPerDay: s.postingFrequencyPerDay,
    topPostEngagement: s.topPostEngagement,
  }));
  for (const s of all) {
    const derived: DerivedSnapshot = {
      followers: s.followers,
      postsCount: s.postsCount,
      reactionsCount: s.reactionsCount,
      commentsCount: s.commentsCount,
      sharesCount: s.sharesCount,
      videoViews: s.videoViews,
      topPostEngagement: s.topPostEngagement,
      periodStart: s.periodStart,
      periodEnd: s.periodEnd,
      publicEngagement: s.publicEngagement ?? 0,
      publicEngagementPerPost: s.publicEngagementPerPost,
      engagementPer1kFollowers: s.engagementPer1kFollowers,
      avgReactionsPerPost: s.avgReactionsPerPost,
      avgCommentsPerPost: s.avgCommentsPerPost,
      avgSharesPerPost: s.avgSharesPerPost,
      videoViewsPerFollower: s.videoViewsPerFollower,
      commentIntensity: s.commentIntensity,
      shareIntensity: s.shareIntensity,
      postingFrequencyPerDay: s.postingFrequencyPerDay,
      benchmarkScore: null,
    };
    const score = calculateBenchmarkScore(derived, population);
    await prisma.competitorMetricSnapshot.update({
      where: { id: s.id },
      data: { benchmarkScore: score },
    });
  }
}
