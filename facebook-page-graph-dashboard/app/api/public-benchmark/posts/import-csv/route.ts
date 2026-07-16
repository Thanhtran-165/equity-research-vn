import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";
import { parseBenchmarkCsv, resolveBenchmarkPage } from "@/lib/benchmark/importBenchmarkCsv";
import { validatePilotImport, detectForbiddenColumns } from "@/lib/benchmark/pilotValidation";
import { parseDate } from "@/lib/imports/normalizeRows";

export const dynamic = "force-dynamic";

/**
 * POST /api/public-benchmark/posts/import-csv
 * Body: { csv: string, dryRun?: boolean, defaultPageId?: number }
 *
 * Parses CSV with Vietnamese aliases, resolves pages by URL or name,
 * and upserts BenchmarkPost records.
 *
 * Dry-run includes pilot validation quality gates.
 */
export async function POST(req: Request) {
  return withFbErrors(async () => {
    const body = await req.json();

    if (!body.csv || typeof body.csv !== "string") {
      return ok({ error: "csv field is required" }, 400);
    }

    const dryRun = body.dryRun !== false;
    const defaultPageId = body.defaultPageId ? parseInt(body.defaultPageId) : null;

    // Detect forbidden columns from raw headers
    const firstLine = body.csv.split("\n").find((l: string) => !l.startsWith("#") && l.trim());
    const csvHeaders = firstLine ? firstLine.split(",").map((h: string) => h.trim()) : [];
    const forbiddenColumns = detectForbiddenColumns(csvHeaders);

    const result = parseBenchmarkCsv(body.csv);
    if (result.parsed.length === 0) {
      return ok({
        error: "No valid rows parsed",
        warnings: result.warnings,
        skipped: result.skipped,
      }, 400);
    }

    // Get known core peers for validation
    const corePeers = await prisma.benchmarkPage.findMany({
      where: { benchmarkRole: "core_peer", isOwnPage: false },
      select: { id: true, name: true, canonicalUrl: true },
    });

    // If dry run, return preview with pilot validation
    if (dryRun) {
      const resolvedIds: (number | null)[] = [];
      const preview = await Promise.all(
        result.parsed.slice(0, 50).map(async (p) => {
          const pageId = await resolveBenchmarkPage(prisma, p.pageUrl, p.pageName);
          resolvedIds.push(pageId);
          return {
            postUrl: p.postUrl,
            pageResolved: pageId != null,
            pageName: p.pageName,
            reactions: p.reactions,
            comments: p.comments,
            shares: p.shares,
            comparableEngagement: p.comparableEngagement,
            warnings: p.warnings,
          };
        }),
      );

      // Resolve all remaining (beyond preview) for full validation
      for (const p of result.parsed.slice(50)) {
        const pageId = await resolveBenchmarkPage(prisma, p.pageUrl, p.pageName);
        resolvedIds.push(pageId);
      }

      const validation = validatePilotImport({
        parsed: result.parsed,
        skipped: result.skipped,
        forbiddenColumns,
        resolvedPageIds: resolvedIds,
        knownCorePeerNames: corePeers.map((p) => p.name),
        knownCorePeerUrls: corePeers.map((p) => p.canonicalUrl),
        knownCorePeerPageIds: corePeers.map((p) => p.id),
        isTestMode: body.testMode === true,
      });

      return ok({
        dryRun: true,
        totalRows: result.totalRows,
        skipped: result.skipped.length,
        previewRowCount: preview.length,
        preview,
        warnings: result.warnings,
        validation,
      });
    }

    // Apply: write to DB
    let imported = 0;
    let skipped = 0;
    const errors: string[] = [];
    const capturedAt = new Date();

    for (const p of result.parsed) {
      let pageId = await resolveBenchmarkPage(prisma, p.pageUrl, p.pageName);
      if (!pageId) pageId = defaultPageId;

      if (!pageId) {
        skipped++;
        continue;
      }

      try {
        await prisma.benchmarkPost.upsert({
          where: {
            benchmarkPageId_postUrl_capturedAt: {
              benchmarkPageId: pageId,
              postUrl: p.postUrl,
              capturedAt,
            },
          },
          create: {
            benchmarkPageId: pageId,
            postUrl: p.postUrl,
            postedAt: p.postedAt ? parseDate(p.postedAt) : null,
            textSnippet: p.textSnippet,
            contentType: p.contentType,
            topicTag: p.topicTag,
            reactions: p.reactions,
            comments: p.comments,
            shares: p.shares,
            publicVideoViews: p.publicVideoViews,
            reactionsObserved: p.reactionsObserved,
            commentsObserved: p.commentsObserved,
            sharesObserved: p.sharesObserved,
            publicVideoViewsObserved: p.publicVideoViewsObserved,
            comparableEngagement: p.comparableEngagement,
            observedPublicEngagement: p.observedPublicEngagement,
            metricCoverageScore: p.metricCoverageScore,
            source: "csv_import",
            capturedAt,
          },
          update: {
            postedAt: p.postedAt ? parseDate(p.postedAt) ?? undefined : undefined,
            reactions: p.reactions,
            comments: p.comments,
            shares: p.shares,
            publicVideoViews: p.publicVideoViews,
            reactionsObserved: p.reactionsObserved,
            commentsObserved: p.commentsObserved,
            sharesObserved: p.sharesObserved,
            publicVideoViewsObserved: p.publicVideoViewsObserved,
            comparableEngagement: p.comparableEngagement,
            observedPublicEngagement: p.observedPublicEngagement,
            metricCoverageScore: p.metricCoverageScore,
          },
        });
        imported++;
      } catch (err) {
        errors.push(`Failed to import ${p.postUrl}: ${err instanceof Error ? err.message : String(err)}`);
      }
    }

    return ok({ imported, skipped, errors, totalParsed: result.parsed.length });
  });
}
