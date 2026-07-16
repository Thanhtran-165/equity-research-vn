import { describe, it, expect } from "vitest";
import {
  getPreviousFullWeek,
  getLastSunday,
  getYtdRange,
  isFirstMondayOfMonth,
  generateWeeklyReminderRun,
  generateMonthlyRefreshItems,
  generateICSContent,
  isOverdue,
  isRunCompleted,
} from "../reminders/exportReminderPlan";

describe("getPreviousFullWeek", () => {
  it("returns previous Monday to Sunday when today is Monday", () => {
    // Monday July 13, 2026
    const monday = new Date("2026-07-13T10:00:00+07:00");
    const week = getPreviousFullWeek(monday);
    expect(week.start).toBe("2026-07-06");
    expect(week.end).toBe("2026-07-12");
  });

  it("returns previous Monday to Sunday when today is Wednesday", () => {
    // Wednesday July 15, 2026
    const wed = new Date("2026-07-15T10:00:00+07:00");
    const week = getPreviousFullWeek(wed);
    expect(week.start).toBe("2026-07-06");
    expect(week.end).toBe("2026-07-12");
  });

  it("returns previous Monday to Sunday when today is Sunday", () => {
    const sun = new Date("2026-07-19T10:00:00+07:00");
    const week = getPreviousFullWeek(sun);
    expect(week.start).toBe("2026-07-06");
    expect(week.end).toBe("2026-07-12");
  });
});

describe("getLastSunday", () => {
  it("returns last Sunday before today", () => {
    const wed = new Date("2026-07-15T10:00:00+07:00");
    const sun = getLastSunday(wed);
    expect(sun).toBe("2026-07-12");
  });

  it("returns previous Sunday if today is Sunday", () => {
    const sun = new Date("2026-07-19T10:00:00+07:00");
    expect(getLastSunday(sun)).toBe("2026-07-12");
  });
});

describe("getYtdRange", () => {
  it("returns Jan 1 to last Sunday", () => {
    const wed = new Date("2026-07-15T10:00:00+07:00");
    const ytd = getYtdRange(wed);
    expect(ytd.start).toBe("2026-01-01");
    expect(ytd.end).toBe("2026-07-12");
  });
});

describe("isFirstMondayOfMonth", () => {
  it("returns true for first Monday", () => {
    expect(isFirstMondayOfMonth(new Date("2026-07-06T10:00:00+07:00"))).toBe(true); // July 6 is Monday
  });

  it("returns false for second Monday", () => {
    expect(isFirstMondayOfMonth(new Date("2026-07-13T10:00:00+07:00"))).toBe(false);
  });

  it("returns false for non-Monday", () => {
    expect(isFirstMondayOfMonth(new Date("2026-07-01T10:00:00+07:00"))).toBe(false);
  });
});

describe("generateWeeklyReminderRun", () => {
  it("contains exactly W01-W04", () => {
    const run = generateWeeklyReminderRun(new Date("2026-07-13T10:00:00+07:00"));
    expect(run.type).toBe("weekly");
    expect(run.items).toHaveLength(4);
    expect(run.items.map((i) => i.code).sort()).toEqual(["W01", "W02", "W03", "W04"]);
  });

  it("W01 is Video/Daily/Activity/Performance", () => {
    const run = generateWeeklyReminderRun(new Date("2026-07-13T10:00:00+07:00"));
    const w01 = run.items.find((i) => i.code === "W01")!;
    expect(w01.contentLevel).toBe("Video");
    expect(w01.dataView).toBe("Hằng ngày");
    expect(w01.filterMode).toBe("Hoạt động");
    expect(w01.preset).toBe("Hiệu quả");
    expect(w01.priority).toBe("P0");
    expect(w01.required).toBe(true);
  });

  it("W02 is Posts/Lifetime/Created/Performance", () => {
    const run = generateWeeklyReminderRun(new Date("2026-07-13T10:00:00+07:00"));
    const w02 = run.items.find((i) => i.code === "W02")!;
    expect(w02.contentLevel).toBe("Bài viết");
    expect(w02.dataView).toBe("Trọn đời");
    expect(w02.preset).toBe("Hiệu quả");
  });

  it("does NOT include Posts/Daily/Activity", () => {
    const run = generateWeeklyReminderRun(new Date("2026-07-13T10:00:00+07:00"));
    const postsDaily = run.items.find(
      (i) => i.contentLevel === "Bài viết" && i.dataView === "Hằng ngày" && i.filterMode === "Hoạt động",
    );
    expect(postsDaily).toBeUndefined();
  });

  it("does NOT include Page/Daily/Performance", () => {
    const run = generateWeeklyReminderRun(new Date("2026-07-13T10:00:00+07:00"));
    const pageDaily = run.items.find(
      (i) => i.contentLevel === "Trang" && i.dataView === "Hằng ngày" && i.preset === "Hiệu quả",
    );
    expect(pageDaily).toBeUndefined();
  });

  it("expected filenames include correct period", () => {
    const run = generateWeeklyReminderRun(new Date("2026-07-13T10:00:00+07:00"));
    const w01 = run.items.find((i) => i.code === "W01")!;
    expect(w01.expectedFilename).toContain("2026-07-06");
    expect(w01.expectedFilename).toContain("2026-07-12");
    expect(w01.expectedFilename.endsWith(".csv")).toBe(true);
  });
});

describe("generateMonthlyRefreshItems", () => {
  it("returns empty on non-first-Monday", () => {
    expect(generateMonthlyRefreshItems(new Date("2026-07-13T10:00:00+07:00"))).toHaveLength(0);
  });

  it("returns M01-M04 on first Monday", () => {
    const items = generateMonthlyRefreshItems(new Date("2026-07-06T10:00:00+07:00"));
    expect(items.length).toBe(4);
    expect(items.map((i) => i.code).sort()).toEqual(["M01", "M02", "M03", "M04"]);
  });
});

describe("generateICSContent", () => {
  it("has weekly VEVENT with TZID=Asia/Ho_Chi_Minh", () => {
    const ics = generateICSContent();
    expect(ics).toContain("BEGIN:VCALENDAR");
    expect(ics).toContain("TZID:Asia/Ho_Chi_Minh");
    expect(ics).toContain("RRULE:FREQ=WEEKLY;BYDAY=MO");
    expect(ics).toContain("Cập nhật dữ liệu Meta cho Chim Cút (Hằng tuần)");
    // Must NOT use BYHOUR in RRULE (use DTSTART time instead)
    expect(ics).not.toContain("BYHOUR");
  });

  it("has monthly VEVENT with BYSETPOS=1", () => {
    const ics = generateICSContent();
    expect(ics).toContain("RRULE:FREQ=MONTHLY;BYDAY=MO;BYSETPOS=1");
    expect(ics).toContain("Cập nhật dữ liệu Meta hằng tháng cho Chim Cút");
  });

  it("contains 2 VEVENTs", () => {
    const ics = generateICSContent();
    const veventCount = (ics.match(/BEGIN:VEVENT/g) || []).length;
    expect(veventCount).toBe(2);
  });

  it("has VTIMEZONE block", () => {
    const ics = generateICSContent();
    expect(ics).toContain("BEGIN:VTIMEZONE");
    expect(ics).toContain("END:VTIMEZONE");
  });
});

describe("isOverdue", () => {
  it("returns true when past due", () => {
    const past = new Date(Date.now() - 86400000).toISOString();
    expect(isOverdue(past)).toBe(true);
  });

  it("returns false when future", () => {
    const future = new Date(Date.now() + 86400000).toISOString();
    expect(isOverdue(future)).toBe(false);
  });
});

describe("isRunCompleted", () => {
  it("returns true when all required items applied", () => {
    const items = [
      { code: "W01", required: true, status: "applied_ok", priority: "P0", title: "", platform: "", pageName: "", dateRange: { start: "", end: "" }, preset: "", dataView: "", contentLevel: "", filterMode: "", expectedFilename: "", purpose: null, note: null },
      { code: "W02", required: true, status: "applied_ok", priority: "P0", title: "", platform: "", pageName: "", dateRange: { start: "", end: "" }, preset: "", dataView: "", contentLevel: "", filterMode: "", expectedFilename: "", purpose: null, note: null },
      { code: "W04", required: false, status: "pending", priority: "P1", title: "", platform: "", pageName: "", dateRange: { start: "", end: "" }, preset: "", dataView: "", contentLevel: "", filterMode: "", expectedFilename: "", purpose: null, note: null },
    ] as any;
    expect(isRunCompleted(items)).toBe(true);
  });

  it("returns false when required item not done", () => {
    const items = [
      { code: "W01", required: true, status: "applied_ok", priority: "P0", title: "", platform: "", pageName: "", dateRange: { start: "", end: "" }, preset: "", dataView: "", contentLevel: "", filterMode: "", expectedFilename: "", purpose: null, note: null },
      { code: "W02", required: true, status: "pending", priority: "P0", title: "", platform: "", pageName: "", dateRange: { start: "", end: "" }, preset: "", dataView: "", contentLevel: "", filterMode: "", expectedFilename: "", purpose: null, note: null },
    ] as any;
    expect(isRunCompleted(items)).toBe(false);
  });
});
