import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";
import {
  generateWeeklyReminderRun,
  generateMonthlyRefreshItems,
  isFirstMondayOfMonth,
  isRunCompleted,
  getYtdRange,
} from "@/lib/reminders/exportReminderPlan";

export const dynamic = "force-dynamic";

/**
 * GET /api/data-reminders/current
 * Returns weeklyRun + optional monthlyRun (separate, with catch-up logic).
 */
export async function GET() {
  return withFbErrors(async () => {
    const now = new Date();

    // --- WEEKLY RUN ---
    const weeklyPlan = generateWeeklyReminderRun(now);
    let weeklyRun = await prisma.dataReminderRun.findUnique({
      where: {
        type_periodStart_periodEnd: {
          type: "weekly",
          periodStart: weeklyPlan.periodStart,
          periodEnd: weeklyPlan.periodEnd,
        },
      },
      include: { items: true },
    });

    if (!weeklyRun) {
      try {
        weeklyRun = await prisma.dataReminderRun.create({
          data: {
            type: "weekly",
            periodStart: weeklyPlan.periodStart,
            periodEnd: weeklyPlan.periodEnd,
            dueAt: new Date(weeklyPlan.dueAt),
            status: "pending",
          },
          include: { items: true },
        });
      } catch (e: any) {
        // Race condition: another request created it — re-fetch
        if (e?.code === "P2002") {
          weeklyRun = await prisma.dataReminderRun.findUnique({
            where: {
              type_periodStart_periodEnd: {
                type: "weekly",
                periodStart: weeklyPlan.periodStart,
                periodEnd: weeklyPlan.periodEnd,
              },
            },
            include: { items: true },
          });
        } else {
          throw e;
        }
      }
    }

    if (weeklyRun && weeklyRun.items.length === 0) {
      for (const item of weeklyPlan.items) {
        await prisma.dataReminderItem.create({
          data: {
            runId: weeklyRun.id,
            code: item.code, title: item.title, priority: item.priority,
            required: item.required, platform: item.platform, pageName: item.pageName,
            dateRangeStart: item.dateRange.start, dateRangeEnd: item.dateRange.end,
            preset: item.preset, dataView: item.dataView, contentLevel: item.contentLevel,
            filterMode: item.filterMode, expectedFilename: item.expectedFilename,
            purpose: item.purpose, note: item.note,
          },
        });
      }
      weeklyRun = await prisma.dataReminderRun.findUnique({
        where: { id: weeklyRun.id }, include: { items: true },
      })!;
    }

    // Weekly overdue: past Tuesday 12:00 and required items not done
    // BUT: auto-complete if data already covers the period
    const weeklyDataPresent = await checkWeeklyDataPresent(weeklyPlan.periodStart, weeklyPlan.periodEnd);
    if (weeklyDataPresent && weeklyRun!.status !== "completed") {
      await prisma.dataReminderRun.update({
        where: { id: weeklyRun!.id },
        data: { status: "completed", completedAt: now },
      });
      // Mark all required items as applied_ok
      await prisma.dataReminderItem.updateMany({
        where: { runId: weeklyRun!.id, required: true, status: { not: "applied_ok" } },
        data: { status: "applied_ok", appliedAt: now },
      });
      weeklyRun = { ...weeklyRun!, status: "completed" };
    }

    const weeklyOverdue = computeWeeklyOverdue(weeklyPlan, now) && weeklyRun!.status !== "completed";
    if (weeklyOverdue && weeklyRun!.status !== "overdue" && weeklyRun!.status !== "completed") {
      await prisma.dataReminderRun.update({
        where: { id: weeklyRun!.id },
        data: { status: "overdue" },
      });
      weeklyRun = { ...weeklyRun!, status: "overdue" };
    }

    // --- MONTHLY RUN (catch-up logic) ---
    // Use exact YTD range to find existing monthly run (not startsWith monthKey)
    const ytdRange = getYtdRange(now);
    let monthlyRun = await prisma.dataReminderRun.findFirst({
      where: { type: "monthly", periodStart: ytdRange.start, periodEnd: ytdRange.end },
      include: { items: true },
    });

    // Create monthly run if:
    // 1. We're past first Monday of month
    // 2. No monthly run exists for this YTD range yet
    const shouldCreateMonthly = isFirstMondayOfMonth(now) || isPastFirstMonday(now);
    if (!monthlyRun && shouldCreateMonthly) {
      const monthlyItems = generateMonthlyRefreshItems(getFirstMondayOfCurrentMonth(now) || now);
      if (monthlyItems.length > 0) {
        try {
          monthlyRun = await prisma.dataReminderRun.create({
            data: {
              type: "monthly",
              periodStart: ytdRange.start,
              periodEnd: ytdRange.end,
              dueAt: getMonthlyDueDate(now),
              status: "pending",
            },
            include: { items: true },
          });
        } catch (e: any) {
          if (e?.code === "P2002") {
            monthlyRun = await prisma.dataReminderRun.findFirst({
              where: { type: "monthly", periodStart: ytdRange.start, periodEnd: ytdRange.end },
              include: { items: true },
            });
          } else {
            throw e;
          }
        }
        // Only create items if run has zero items (prevents duplicates on repeated calls)
        if (monthlyRun && monthlyRun.items.length === 0) {
          for (const item of monthlyItems) {
            await prisma.dataReminderItem.create({
              data: {
                runId: monthlyRun.id,
                code: item.code, title: item.title, priority: item.priority,
                required: item.required, platform: item.platform, pageName: item.pageName,
                dateRangeStart: item.dateRange.start, dateRangeEnd: item.dateRange.end,
                preset: item.preset, dataView: item.dataView, contentLevel: item.contentLevel,
                filterMode: item.filterMode, expectedFilename: item.expectedFilename,
                purpose: item.purpose, note: item.note,
              },
            });
          }
          monthlyRun = await prisma.dataReminderRun.findFirst({
            where: { id: monthlyRun.id }, include: { items: true },
          });
        }
      }
    }

    // Monthly auto-complete: if YTD data already covers the period
    let monthlyOverdue = false;
    if (monthlyRun && monthlyRun.status !== "completed" && monthlyRun.status !== "skipped") {
      const monthlyDataPresent = await checkMonthlyDataPresent(monthlyRun.periodStart, monthlyRun.periodEnd);
      if (monthlyDataPresent) {
        // Data already covers YTD — auto-complete
        await prisma.dataReminderRun.update({
          where: { id: monthlyRun.id },
          data: { status: "completed", completedAt: now },
        });
        await prisma.dataReminderItem.updateMany({
          where: { runId: monthlyRun.id, required: true, status: { not: "applied_ok" } },
          data: { status: "applied_ok", appliedAt: now },
        });
        monthlyRun = { ...monthlyRun, status: "completed" };
      } else {
        monthlyOverdue = computeMonthlyOverdue(now);
        if (monthlyOverdue && monthlyRun.status !== "overdue") {
          await prisma.dataReminderRun.update({
            where: { id: monthlyRun.id },
            data: { status: "overdue" },
        });
        monthlyRun = { ...monthlyRun, status: "overdue" };
        }
      }
    }

    // --- HEALTH CHECK ---
    const latestVideoDate = await prisma.videoDailyMetric.findFirst({
      orderBy: { date: "desc" }, select: { date: true },
    });
    const latestBatch = await prisma.insightImportBatch.findFirst({
      orderBy: { importedAt: "desc" }, select: { importedAt: true, filename: true },
    });

    const videoStale = !latestVideoDate?.date || latestVideoDate.date < weeklyPlan.periodEnd;
    const importStale = !latestBatch?.importedAt ||
      latestBatch.importedAt < new Date(weeklyPlan.periodEnd + "T00:00:00Z");

    return ok({
      weeklyRun: weeklyRun ? { ...weeklyRun, overdue: weeklyOverdue } : null,
      monthlyRun: monthlyRun && monthlyRun.status !== "completed" && monthlyRun.status !== "skipped"
        ? { ...monthlyRun, overdue: monthlyOverdue }
        : null,
      healthCheck: {
        latestVideoDailyDate: latestVideoDate?.date ?? null,
        latestImportDate: latestBatch?.importedAt.toISOString() ?? null,
        latestImportFile: latestBatch?.filename ?? null,
        previousWeekEnd: weeklyPlan.periodEnd,
        videoStale,
        importStale,
      },
    });
  });
}

// --- Helpers ---

/**
 * Check if data already covers the weekly period:
 * - VideoDailyMetric has rows with date >= periodStart AND date <= periodEnd
 */
async function checkWeeklyDataPresent(periodStart: string, periodEnd: string): Promise<boolean> {
  const videoCount = await prisma.videoDailyMetric.count({
    where: { date: { gte: periodStart, lte: periodEnd } },
  });
  return videoCount > 0;
}

/**
 * Check if YTD data already covers the monthly refresh period:
 * - Posts with createdTime >= Jan 1 of current year exist
 * - VideoDailyMetric has rows within the last 7 days of periodEnd
 */
async function checkMonthlyDataPresent(periodStart: string, periodEnd: string): Promise<boolean> {
  // Check posts exist for this YTD range
  const postCount = await prisma.post.count({
    where: {
      createdTime: { gte: periodStart, lte: periodEnd + "T23:59:59" },
    },
  });
  // Check video daily data covers recent part of period (last 7 days before periodEnd)
  const recentStart = new Date(periodEnd);
  recentStart.setDate(recentStart.getDate() - 6);
  const recentStartStr = recentStart.toISOString().slice(0, 10);
  const videoCount = await prisma.videoDailyMetric.count({
    where: { date: { gte: recentStartStr, lte: periodEnd } },
  });
  return postCount > 0 && videoCount > 0;
}

function computeWeeklyOverdue(plan: { periodStart: string; dueAt: string }, now: Date): boolean {
  // Due = Monday 09:00. Overdue = past Tuesday 12:00.
  const due = new Date(plan.dueAt);
  const overdueThreshold = new Date(due);
  overdueThreshold.setDate(due.getDate() + 1); // Tuesday
  overdueThreshold.setHours(12, 0, 0, 0);
  return now.getTime() > overdueThreshold.getTime();
}

function computeMonthlyOverdue(now: Date): boolean {
  // Find first Monday of current month
  const firstMon = getFirstMondayOfCurrentMonth(now);
  if (!firstMon) return false;
  // Overdue = past Wednesday 12:00 after first Monday
  const threshold = new Date(firstMon);
  threshold.setDate(firstMon.getDate() + 2); // Wednesday
  threshold.setHours(12, 0, 0, 0);
  return now.getTime() > threshold.getTime();
}

function isPastFirstMonday(now: Date): boolean {
  const firstMon = getFirstMondayOfCurrentMonth(now);
  if (!firstMon) return false;
  return now.getTime() > firstMon.getTime();
}

function getFirstMondayOfCurrentMonth(now: Date): Date | null {
  const year = now.getFullYear();
  const month = now.getMonth();
  for (let day = 1; day <= 7; day++) {
    const d = new Date(year, month, day, 9, 0, 0, 0);
    if (d.getDay() === 1) return d;
  }
  return null;
}

function getMonthlyDueDate(now: Date): Date {
  const firstMon = getFirstMondayOfCurrentMonth(now);
  return firstMon ?? new Date(now.getFullYear(), now.getMonth(), 1, 9, 0, 0, 0);
}
