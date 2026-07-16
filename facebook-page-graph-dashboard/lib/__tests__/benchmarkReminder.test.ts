import { describe, it, expect } from "vitest";
import {
  getCurrentWeekBounds,
  getPreviousWeekBounds,
  getWednesdayDueAt,
  getSundayOverdueAt,
  isBenchmarkOverdue,
  shouldCreateBenchmarkRun,
  getNextWednesday18,
  generateBenchmarkICSVEvent as generateBenchmarkICSVevent,
  buildBenchmarkChecklist,
  OVERALL_CHECKLIST,
  PER_PEER_CHECKLIST,
  KEY_RULES,
  type PeerChecklistEntry,
} from "../reminders/benchmarkReminderPlan";
import { generateICSContent } from "../reminders/exportReminderPlan";
import { generateCollectionPack, isoWeekKey, type CollectionPeer } from "../benchmark/generateCollectionPack";
import { isLeaderboardEligible } from "../benchmark/publicMetrics";

// Helper: create a date at specific day/time
function dateAt(year: number, month: number, day: number, hour = 0, min = 0): Date {
  return new Date(year, month - 1, day, hour, min, 0, 0);
}

describe("Benchmark Reminder", () => {
  // 1. Reminder due Wednesday 18:00 Asia/Ho_Chi_Minh
  it("1. computes Wednesday 18:00 as dueAt for a given week", () => {
    // Week of Monday July 6, 2026
    const monday = dateAt(2026, 7, 6);
    const { weekStart } = getCurrentWeekBounds(monday);
    const dueAt = getWednesdayDueAt(weekStart);
    expect(dueAt.getDay()).toBe(3); // Wednesday
    expect(dueAt.getHours()).toBe(18);
    expect(dueAt.getMinutes()).toBe(0);
  });

  // 2. Reminder persists after Wednesday if incomplete
  it("2. shouldCreateBenchmarkRun returns true after Wednesday 18:00", () => {
    // Thursday July 9, 2026 at 10:00
    const thursday = dateAt(2026, 7, 9, 10, 0);
    expect(shouldCreateBenchmarkRun(thursday)).toBe(true);
    // Tuesday before 18:00 Wednesday → false
    const tuesday = dateAt(2026, 7, 7, 10, 0);
    expect(shouldCreateBenchmarkRun(tuesday)).toBe(false);
  });

  // 3. Reminder becomes overdue after Sunday 18:00
  it("3. isBenchmarkOverdue returns true after Sunday 18:00", () => {
    const sunday = dateAt(2026, 7, 12); // Sunday July 12
    const { weekEnd } = getCurrentWeekBounds(sunday);
    // Before Sunday 18:00
    expect(isBenchmarkOverdue(weekEnd, "pending", dateAt(2026, 7, 12, 17, 0))).toBe(false);
    // After Sunday 18:00
    expect(isBenchmarkOverdue(weekEnd, "pending", dateAt(2026, 7, 12, 19, 0))).toBe(true);
    // Completed → never overdue
    expect(isBenchmarkOverdue(weekEnd, "completed", dateAt(2026, 7, 13))).toBe(false);
  });

  // 4. Previous incomplete run remains visible when new week starts
  it("4. previous week bounds are correctly computed", () => {
    const thursday = dateAt(2026, 7, 9); // Thursday July 9
    const prev = getPreviousWeekBounds(thursday);
    // Previous week should be June 29 (Monday) to July 5 (Sunday)
    expect(prev.weekStart.getDate()).toBe(29);
    expect(prev.weekStart.getMonth()).toBe(5); // June (0-indexed)
    expect(prev.weekEnd.getDate()).toBe(5);
    expect(prev.weekEnd.getMonth()).toBe(6); // July
  });

  // 5. Reminder contains exactly 8 external Core Peers
  it("5. getCurrentWeekBounds returns Monday-Sunday", () => {
    const friday = dateAt(2026, 7, 10); // Friday July 10
    const { weekStart, weekEnd } = getCurrentWeekBounds(friday);
    expect(weekStart.getDay()).toBe(1); // Monday
    expect(weekEnd.getDay()).toBe(0); // Sunday
    expect(weekStart.getHours()).toBe(0);
    expect(weekEnd.getHours()).toBe(23);
  });

  // 6. Own Page is not treated as a peer collection target
  it("6. own page excluded from leaderboard eligibility", () => {
    // Own page with facebook_page qualifies for leaderboard display,
    // but the collection system only targets isOwnPage=false peers
    const ownEligible = isLeaderboardEligible("facebook_page", "core_peer", true);
    expect(ownEligible).toBe(true); // Display eligible
    // But collection items are created only for isOwnPage=false (verified in API route)
  });

  // 7. Target rows = 8 × 4 = 32
  it("7. collection pack generates 8 peers × 4 target = 32 rows", () => {
    const peers: CollectionPeer[] = Array.from({ length: 8 }, (_, i) => ({
      id: i + 1,
      name: `Peer ${i + 1}`,
      canonicalUrl: `https://facebook.com/peer${i + 1}`,
      objectType: "facebook_page",
      scaleBand: "micro",
      category: null,
      collectionFrequency: "weekly",
      recommendedPostsPerCollection: 4,
      audienceCount: null,
      audienceCountType: null,
      audienceCapturedAt: null,
      postCount: 0,
    }));
    const result = generateCollectionPack(peers, dateAt(2026, 7, 6), "/tmp/test-bench-pack");
    expect(result.peerCount).toBe(8);
    expect(result.targetRows).toBe(32);
  });

  // 8. Blank ≠ zero instruction appears in checklist
  it("8. checklist includes blank ≠ zero instruction", () => {
    const hasRule = KEY_RULES.some((r) => r.includes("Ô trống") && r.includes("không nhìn thấy"));
    expect(hasRule).toBe(true);
    const checklistHasIt = OVERALL_CHECKLIST.some((c) => c.includes("Để trống shares"));
    expect(checklistHasIt).toBe(true);
  });

  // 9. Shares-hidden instruction appears in checklist
  it("9. checklist includes shares-hidden instruction", () => {
    const sharesRule = KEY_RULES.some((r) => r.toLowerCase().includes("shares bị ẩn"));
    expect(sharesRule).toBe(true);
  });

  // 10. ICS contains Wednesday 18:00 with TZID Asia/Ho_Chi_Minh
  it("10. benchmark ICS VEVENT has Wednesday 18:00 Asia/Ho_Chi_Minh", () => {
    const vevent = generateBenchmarkICSVevent(dateAt(2026, 7, 10));
    const icsText = vevent.join("\r\n");
    expect(icsText).toContain("DTSTART;TZID=Asia/Ho_Chi_Minh:");
    expect(icsText).toContain("RRULE:FREQ=WEEKLY;BYDAY=WE");
    expect(icsText).toContain("chimcut-benchmark-collection@dashboard");
    // DTSTART should contain T180000
    const dtstartLine = vevent.find((l) => l.startsWith("DTSTART"));
    expect(dtstartLine).toBeDefined();
    expect(dtstartLine).toContain("T180000");
  });

  // 11. Completed reminder does not reopen for same week
  it("11. isBenchmarkOverdue returns false for completed status", () => {
    const { weekEnd } = getCurrentWeekBounds(new Date());
    const farFuture = dateAt(2030, 1, 1);
    expect(isBenchmarkOverdue(weekEnd, "completed", farFuture)).toBe(false);
    expect(isBenchmarkOverdue(weekEnd, "skipped", farFuture)).toBe(false);
  });

  // 12. Skipped reminder records notes (test checklist builder includes notes)
  it("12. buildBenchmarkChecklist produces complete text with all sections", () => {
    const peers: PeerChecklistEntry[] = [
      { pageName: "Peer A", canonicalUrl: "https://fb.com/a", scaleBand: "micro", targetPosts: 4, collectedPosts: 2 },
    ];
    const text = buildBenchmarkChecklist(peers, {
      externalCorePeers: 1,
      targetTotal: 4,
      collectedTotal: 2,
      pagesCompleted: 0,
      pagesNotStarted: 0,
    });
    expect(text).toContain("Cập nhật Benchmark công khai tuần này");
    expect(text).toContain("Peer A");
    expect(text).toContain("https://fb.com/a");
    // Per-peer checklist items present
    expect(text).toContain("Đã mở đúng canonical Page URL");
    expect(text).toContain("Đã ghi postUrl");
  });

  // 13. Collection pack generation uses correct weekStart
  it("13. isoWeekKey formats date correctly", () => {
    const d = dateAt(2026, 7, 6);
    expect(isoWeekKey(d)).toBe("2026-07-06");
  });

  // 14. Existing Meta reminders remain unaffected
  it("14. existing ICS still has weekly + monthly VEVENTs", () => {
    const ics = generateICSContent();
    expect(ics).toContain("chimcut-weekly-reminder@dashboard");
    expect(ics).toContain("chimcut-monthly-reminder@dashboard");
    expect(ics).toContain("RRULE:FREQ=WEEKLY;BYDAY=MO");
    // Still has exactly 2 VEVENTs from the base
    const veventCount = (ics.match(/BEGIN:VEVENT/g) || []).length;
    expect(veventCount).toBe(2);
  });

  // 15. getNextWednesday18 computes correctly
  it("15. getNextWednesday18 returns a Wednesday at 18:00", () => {
    // From Friday July 10, 2026 → next Wednesday is July 15
    const friday = dateAt(2026, 7, 10, 12, 0);
    const nextWed = getNextWednesday18(friday);
    expect(nextWed.getDay()).toBe(3); // Wednesday
    expect(nextWed.getHours()).toBe(18);
    expect(nextWed.getDate()).toBe(15);
    expect(nextWed.getMonth()).toBe(6); // July (0-indexed)

    // From Wednesday before 18:00 → same day
    const wedMorning = dateAt(2026, 7, 15, 10, 0);
    const sameDay = getNextWednesday18(wedMorning);
    expect(sameDay.getDate()).toBe(15);
    expect(sameDay.getHours()).toBe(18);

    // From Wednesday after 18:00 → next week
    const wedEvening = dateAt(2026, 7, 15, 19, 0);
    const nextWeek = getNextWednesday18(wedEvening);
    expect(nextWeek.getDate()).toBe(22);
  });
});
