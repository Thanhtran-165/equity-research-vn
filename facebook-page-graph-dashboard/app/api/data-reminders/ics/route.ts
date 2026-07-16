import { generateICSContent } from "@/lib/reminders/exportReminderPlan";
import {
  generateBenchmarkICSVEvent,
  generateFullICSContent,
} from "@/lib/reminders/benchmarkReminderPlan";

export const dynamic = "force-dynamic";

/**
 * GET /api/data-reminders/ics
 * Returns .ics calendar file with 3 VEVENTs:
 *   1. Weekly Meta data reminder (Monday 09:00)
 *   2. Monthly Meta data reminder (first Monday 09:15)
 *   3. Benchmark Weekly Collection (Wednesday 18:00)
 */
export async function GET() {
  const baseICS = generateICSContent();
  const benchmarkVEvent = generateBenchmarkICSVEvent();
  const fullICS = generateFullICSContent(baseICS, benchmarkVEvent);

  return new Response(fullICS, {
    headers: {
      "Content-Type": "text/calendar; charset=utf-8",
      "Content-Disposition": 'attachment; filename="chimcut-data-reminder.ics"',
    },
  });
}
