import { describe, it, expect } from "vitest";
import {
  generateExportPlan,
  formatChecklistMarkdown,
  parsePeriod,
} from "../imports/exportPlan";

describe("parsePeriod", () => {
  it("parses monthly YYYY-MM", () => {
    const r = parsePeriod("2026-07");
    expect(r.start).toBe("2026-07-01");
    expect(r.end).toBe("2026-07-31");
    expect(r.label).toBe("2026-07");
  });

  it("parses quarterly YYYY-QX", () => {
    const r = parsePeriod("2026-Q2");
    expect(r.start).toBe("2026-04-01");
    expect(r.end).toBe("2026-06-30");
  });

  it("parses yearly YYYY", () => {
    const r = parsePeriod("2026");
    expect(r.start).toBe("2026-01-01");
    expect(r.end).toBe("2026-12-31");
  });

  it("handles February correctly (leap year)", () => {
    const r = parsePeriod("2024-02");
    expect(r.end).toBe("2024-02-29");
  });

  it("handles February (non-leap)", () => {
    const r = parsePeriod("2026-02");
    expect(r.end).toBe("2026-02-28");
  });
});

describe("generateExportPlan", () => {
  it("generates default plan with verified P0 tasks only (no G01)", () => {
    const tasks = generateExportPlan({ period: "monthly", startDate: "2026-07" });
    // P01, P02, V01 = P0 verified
    expect(tasks.some((t) => t.id === "P01")).toBe(true);
    expect(tasks.some((t) => t.id === "P02")).toBe(true);
    expect(tasks.some((t) => t.id === "V01")).toBe(true);
    // G01 NOT in default plan
    expect(tasks.some((t) => t.id === "G01")).toBe(false);
  });

  it("P0 tasks are P01 (Posts Lifetime Performance), P02 (Posts Lifetime Published), V01 (Video Lifetime Performance)", () => {
    const tasks = generateExportPlan({ period: "monthly", startDate: "2026-07" });
    const p0 = tasks.filter((t) => t.priority === "P0");
    expect(p0.length).toBe(3);
    expect(p0.map((t) => t.id).sort()).toEqual(["P01", "P02", "V01"]);
    // All P0 must be Lifetime
    expect(p0.every((t) => t.dataView === "Lifetime")).toBe(true);
  });

  it("G01 is NOT included by default", () => {
    const tasks = generateExportPlan({ period: "monthly", startDate: "2026-07" });
    expect(tasks.some((t) => t.id === "G01")).toBe(false);
  });

  it("G01 IS included when includeUnverifiedPagePerformance=true", () => {
    const tasks = generateExportPlan({ period: "monthly", startDate: "2026-07", includeUnverifiedPagePerformance: true });
    const g01 = tasks.find((t) => t.id === "G01");
    expect(g01).toBeDefined();
    expect(g01!.notes).toContain("UNVERIFIED");
  });

  it("V02 is P1 (Video Daily Activity)", () => {
    const tasks = generateExportPlan({ period: "monthly", startDate: "2026-07", includeVideo: true });
    const v02 = tasks.find((t) => t.id === "V02");
    expect(v02).toBeDefined();
    expect(v02!.priority).toBe("P1");
    expect(v02!.dataView).toBe("Daily");
    expect(v02!.filter).toBe("Activity");
  });

  it("V02 notes include video-only warning", () => {
    const tasks = generateExportPlan({ period: "monthly", startDate: "2026-07", includeVideo: true });
    const v02 = tasks.find((t) => t.id === "V02")!;
    expect(v02.notes).toContain("video");
  });

  it("excludes video when includeVideo=false", () => {
    const tasks = generateExportPlan({ period: "monthly", startDate: "2026-07", includeVideo: false });
    expect(tasks.some((t) => t.id === "V02")).toBe(false);
    expect(tasks.some((t) => t.id === "V03")).toBe(false);
  });

  it("G02 audience is P2 and labeled audience-only", () => {
    const tasks = generateExportPlan({ period: "monthly", startDate: "2026-07", includeAudience: true });
    const g02 = tasks.find((t) => t.id === "G02");
    expect(g02).toBeDefined();
    expect(g02!.priority).toBe("P2");
    expect(g02!.preset).toBe("Audience");
    expect(g02!.notes).toContain("KHÔNG thay thế");
  });

  it("excludes audience by default", () => {
    const tasks = generateExportPlan({ period: "monthly", startDate: "2026-07" });
    expect(tasks.some((t) => t.id === "G02")).toBe(false);
  });

  it("generates correct filename for P01", () => {
    const tasks = generateExportPlan({ period: "monthly", startDate: "2026-07" });
    const p01 = tasks.find((t) => t.id === "P01")!;
    expect(p01.filename).toContain("chimcut");
    expect(p01.filename).toContain("fb");
    expect(p01.filename).toContain("posts");
    expect(p01.filename).toContain("lifetime");
    expect(p01.filename).toContain("performance");
    expect(p01.filename.endsWith(".csv")).toBe(true);
  });

  it("includes UI path and website", () => {
    const tasks = generateExportPlan({ period: "monthly", startDate: "2026-07" });
    expect(tasks[0].uiPath).toContain("Insights");
    expect(tasks[0].website).toContain("business.facebook.com");
  });

  it("sets correct date range from period", () => {
    const tasks = generateExportPlan({ period: "quarterly", startDate: "2026-Q1" });
    expect(tasks[0].dateRange.start).toBe("2026-01-01");
    expect(tasks[0].dateRange.end).toBe("2026-03-31");
  });

  it("assigns correct priorities per final verified spec", () => {
    const tasks = generateExportPlan({
      period: "monthly",
      startDate: "2026-07",
      includeVideo: true,
      includeAudience: true,
      includeUnverifiedPagePerformance: true,
    });
    expect(tasks.find((t) => t.id === "P01")?.priority).toBe("P0"); // Posts Lifetime Performance
    expect(tasks.find((t) => t.id === "P02")?.priority).toBe("P0"); // Posts Lifetime Published
    expect(tasks.find((t) => t.id === "V01")?.priority).toBe("P0"); // Video Lifetime Performance
    expect(tasks.find((t) => t.id === "V02")?.priority).toBe("P1"); // Video Daily Activity
    expect(tasks.find((t) => t.id === "G02")?.priority).toBe("P2"); // Page Audience
    expect(tasks.find((t) => t.id === "V03")?.priority).toBe("P2"); // Video Retention
    expect(tasks.find((t) => t.id === "G01")?.priority).toBe("P2"); // Unverified Page Performance
  });

  it("does NOT have Posts/Daily/Activity in plan", () => {
    const tasks = generateExportPlan({ period: "monthly", startDate: "2026-07" });
    const postsDailyActivity = tasks.find(
      (t) => t.contentLevel === "Posts" && t.dataView === "Daily" && t.filter === "Activity",
    );
    expect(postsDailyActivity).toBeUndefined();
  });
});

describe("formatChecklistMarkdown", () => {
  it("produces valid markdown with all tasks", () => {
    const tasks = generateExportPlan({ period: "monthly", startDate: "2026-07" });
    const md = formatChecklistMarkdown(tasks, "2026-07");
    expect(md).toContain("# Export Checklist");
    expect(md).toContain("2026-07");
    expect(md).toContain("P01");
    expect(md).toContain("business.facebook.com");
    expect(md).toContain("[ ]");
  });

  it("groups by priority", () => {
    const tasks = generateExportPlan({ period: "monthly", startDate: "2026-07", includeVideo: true });
    const md = formatChecklistMarkdown(tasks, "2026-07");
    expect(md).toContain("## P0");
    expect(md).toContain("## P1");
  });
});
