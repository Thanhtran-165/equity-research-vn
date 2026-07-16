import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";
import {
  getCurrentWeekBounds,
  getPreviousWeekBounds,
  getWednesdayDueAt,
  isBenchmarkOverdue,
} from "@/lib/reminders/benchmarkReminderPlan";

export const dynamic = "force-dynamic";

/**
 * GET /api/data-reminders/benchmark/current
 *
 * Returns the current week's BenchmarkCollectionRun with catch-up logic:
 * - Creates run if Wednesday 18:00 has passed and none exists
 * - Populates items from 8 external core peers
 * - Updates collectedPosts from BenchmarkPost counts
 * - Marks completed if all items have ≥ target posts
 * - Marks overdue if past Sunday 18:00
 * - Includes previous incomplete runs
 */
export async function GET() {
  return withFbErrors(async () => {
    const now = new Date();
    const { weekStart, weekEnd } = getCurrentWeekBounds(now);
    const dueAt = getWednesdayDueAt(weekStart);

    // Get external core peers
    const corePeers = await prisma.benchmarkPage.findMany({
      where: { benchmarkRole: "core_peer", isOwnPage: false },
      orderBy: { name: "asc" },
    });

    // Find or create current week's run
    let run = await prisma.benchmarkCollectionRun.findUnique({
      where: { weekStart_weekEnd: { weekStart, weekEnd } },
      include: { items: { include: { page: true } } },
    });

    if (!run && now >= dueAt) {
      try {
        run = await prisma.benchmarkCollectionRun.create({
          data: {
            weekStart,
            weekEnd,
            dueAt,
            status: "pending",
          },
          include: { items: { include: { page: true } } },
        });
      } catch {
        // P2002 race — re-fetch
        run = await prisma.benchmarkCollectionRun.findUnique({
          where: { weekStart_weekEnd: { weekStart, weekEnd } },
          include: { items: { include: { page: true } } },
        });
      }
    }

    // Populate items if run exists but has none
    if (run && run.items.length === 0 && corePeers.length > 0) {
      await prisma.benchmarkCollectionItem.createMany({
        data: corePeers.map((p) => ({
          runId: run!.id,
          benchmarkPageId: p.id,
          targetPosts: 4,
        })),
      });
      run = await prisma.benchmarkCollectionRun.findUnique({
        where: { id: run.id },
        include: { items: { include: { page: true } } },
      });
    }

    // Update collectedPosts and item status
    if (run && run.items.length > 0) {
      for (const item of run.items) {
        const collected = await prisma.benchmarkPost.count({
          where: {
            benchmarkPageId: item.benchmarkPageId,
            capturedAt: { gte: weekStart, lte: weekEnd },
          },
        });
        const newStatus =
          collected >= item.targetPosts
            ? "complete"
            : collected > 0
              ? "collecting"
              : "not_started";
        if (collected !== item.collectedPosts || newStatus !== item.status) {
          await prisma.benchmarkCollectionItem.update({
            where: { id: item.id },
            data: { collectedPosts: collected, status: newStatus },
          });
        }
      }

      // Re-fetch with updated items
      run = await prisma.benchmarkCollectionRun.findUnique({
        where: { id: run.id },
        include: { items: { include: { page: true } } },
      });
    }

    // Auto-complete if all items complete
    if (run && run.status !== "completed" && run.status !== "skipped") {
      const allComplete = run.items.length > 0 && run.items.every((i) => i.status === "complete");
      if (allComplete) {
        await prisma.benchmarkCollectionRun.update({
          where: { id: run.id },
          data: { status: "completed", completedAt: now },
        });
        run = await prisma.benchmarkCollectionRun.findUnique({
          where: { id: run.id },
          include: { items: { include: { page: true } } },
        });
      } else if (isBenchmarkOverdue(weekEnd, run!.status, now)) {
        // Mark overdue
        await prisma.benchmarkCollectionRun.update({
          where: { id: run.id },
          data: { status: "overdue" },
        });
        run = await prisma.benchmarkCollectionRun.findUnique({
          where: { id: run.id },
          include: { items: { include: { page: true } } },
        });
      }
    }

    // Find previous incomplete runs
    const prevWeek = getPreviousWeekBounds(now);
    const incompleteRuns = await prisma.benchmarkCollectionRun.findMany({
      where: {
        weekEnd: { lt: weekStart },
        status: { in: ["pending", "in_progress", "overdue"] },
      },
      orderBy: { weekStart: "desc" },
      include: { items: { include: { page: true } } },
    });

    // Compute summary
    const items = run?.items ?? [];
    const collectedTotal = items.reduce((sum, i) => sum + i.collectedPosts, 0);
    const pagesCompleted = items.filter((i) => i.status === "complete").length;
    const pagesNotStarted = items.filter((i) => i.status === "not_started").length;

    // Shares coverage from benchmark posts this week
    const weekPosts = await prisma.benchmarkPost.count({
      where: {
        capturedAt: { gte: weekStart, lte: weekEnd },
        sharesObserved: true,
      },
    });
    const totalWeekPosts = await prisma.benchmarkPost.count({
      where: { capturedAt: { gte: weekStart, lte: weekEnd } },
    });
    const sharesCoverage = totalWeekPosts > 0 ? weekPosts / totalWeekPosts : 0;

    return ok({
      currentRun: run,
      incompleteRuns,
      summary: {
        externalCorePeers: corePeers.length,
        targetTotal: corePeers.length * 4,
        collectedTotal,
        pagesCompleted,
        pagesNotStarted,
        sharesCoverage,
        weekStart: weekStart.toISOString(),
        weekEnd: weekEnd.toISOString(),
        dueAt: dueAt.toISOString(),
        isOverdue: run ? isBenchmarkOverdue(weekEnd, run.status!, now) : false,
      },
    });
  });
}
