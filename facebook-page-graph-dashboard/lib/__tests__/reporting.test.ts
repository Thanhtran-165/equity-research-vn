import { describe, it, expect } from "vitest";
import {
  computePageSummary,
  topPostsByReach,
  topPostsByER,
  topPostsByCTR,
  detectPostSpikes,
  type PostReportRow,
} from "../reporting/pageReport";
import {
  computeVideoMonthlySummary,
  topVideosByViews,
  detectVideoSpikes,
} from "../reporting/videoReport";
import { buildMonthlyReport, formatMonthlyReportMarkdown } from "../reporting/monthlyReport";

function makePost(overrides: Partial<PostReportRow> = {}): PostReportRow {
  return {
    fbPostId: "p1",
    message: "Test post",
    topic: "chung_khoan",
    postType: "text",
    createdTime: "2026-06-15T10:00:00Z",
    permalinkUrl: null,
    reach: 1000,
    reactionsCount: 50,
    commentsCount: 10,
    sharesCount: 5,
    clicks: 20,
    engagementRate: null,
    metricSource: "meta_business_suite_csv",
    ...overrides,
  };
}

describe("computePageSummary", () => {
  it("computes totals correctly", () => {
    const posts = [makePost(), makePost({ reach: 2000, reactionsCount: 100 })];
    const s = computePageSummary(posts);
    expect(s.totalPosts).toBe(2);
    expect(s.totalReach).toBe(3000);
    expect(s.totalReactions).toBe(150);
    expect(s.totalClicks).toBe(40);
  });

  it("computes avg ER excluding clicks", () => {
    const posts = [makePost({ reach: 1000, reactionsCount: 50, commentsCount: 10, sharesCount: 5, clicks: 100 })];
    const s = computePageSummary(posts);
    // ER = (50+10+5)/1000 = 0.065, NOT 0.165 with clicks
    expect(s.avgER).toBeCloseTo(0.065, 5);
  });

  it("computes avg CTR including clicks", () => {
    const posts = [makePost({ reach: 1000, clicks: 50 })];
    const s = computePageSummary(posts);
    expect(s.avgCTR).toBeCloseTo(0.05, 5);
  });

  it("handles posts with no reach", () => {
    const posts = [makePost({ reach: null, clicks: null })];
    const s = computePageSummary(posts);
    expect(s.totalReach).toBe(0);
    expect(s.avgER).toBeNull();
    expect(s.avgCTR).toBeNull();
  });
});

describe("topPostsByReach", () => {
  it("sorts by reach descending", () => {
    const posts = [makePost({ fbPostId: "a", reach: 100 }), makePost({ fbPostId: "b", reach: 500 }), makePost({ fbPostId: "c", reach: 300 })];
    const top = topPostsByReach(posts, 2);
    expect(top[0].fbPostId).toBe("b");
    expect(top[1].fbPostId).toBe("c");
  });

  it("excludes posts with no reach", () => {
    const posts = [makePost({ reach: null })];
    expect(topPostsByReach(posts)).toHaveLength(0);
  });
});

describe("topPostsByER", () => {
  it("requires minReach threshold", () => {
    const posts = [makePost({ fbPostId: "small", reach: 100, reactionsCount: 50 }), makePost({ fbPostId: "big", reach: 1000, reactionsCount: 100 })];
    const top = topPostsByER(posts, 500, 10);
    expect(top.find((p) => p.fbPostId === "small")).toBeUndefined();
    expect(top.find((p) => p.fbPostId === "big")).toBeDefined();
  });
});

describe("topPostsByCTR", () => {
  it("sorts by CTR (clicks/reach)", () => {
    const posts = [
      makePost({ fbPostId: "a", reach: 1000, clicks: 10 }),
      makePost({ fbPostId: "b", reach: 1000, clicks: 100 }),
    ];
    const top = topPostsByCTR(posts, 500, 10);
    expect(top[0].fbPostId).toBe("b");
    expect(top[0].ctr).toBeCloseTo(0.1, 5);
  });
});

describe("detectPostSpikes", () => {
  it("detects days with reach > 3x median", () => {
    const posts = [
      makePost({ createdTime: "2026-06-01T00:00:00Z", reach: 100 }),
      makePost({ createdTime: "2026-06-02T00:00:00Z", reach: 100 }),
      makePost({ createdTime: "2026-06-03T00:00:00Z", reach: 100 }),
      makePost({ createdTime: "2026-06-04T00:00:00Z", reach: 100 }),
      makePost({ createdTime: "2026-06-05T00:00:00Z", reach: 10000 }), // spike
    ];
    const spikes = detectPostSpikes(posts);
    expect(spikes.length).toBeGreaterThanOrEqual(1);
    expect(spikes[0].date).toBe("2026-06-05");
  });

  it("returns empty for uniform data", () => {
    const posts = Array.from({ length: 5 }, (_, i) => makePost({ createdTime: `2026-06-0${i + 1}T00:00:00Z`, reach: 100 }));
    expect(detectPostSpikes(posts)).toHaveLength(0);
  });
});

describe("computeVideoMonthlySummary", () => {
  it("aggregates daily video metrics", () => {
    const rows = [
      { videoAssetId: 1, date: "2026-06-01", videoViews3s: 100, reach: 200, watchTimeSeconds: 500, reactions: 5, comments: 2, shares: 1 },
      { videoAssetId: 2, date: "2026-06-01", videoViews3s: 50, reach: 100, watchTimeSeconds: 250, reactions: 3, comments: 1, shares: 0 },
    ];
    const s = computeVideoMonthlySummary(rows);
    expect(s.totalViews3s).toBe(150);
    expect(s.summedReach).toBe(300);
    expect(s.watchTimeHours).toBeCloseTo(750 / 3600, 5);
    expect(s.activeVideoCount).toBe(2);
  });
});

describe("topVideosByViews", () => {
  it("sorts by views descending", () => {
    const rows = [
      { videoAssetId: 1, videoAsset: { externalVideoId: "v1", title: "A" }, date: "2026-06-01", videoViews3s: 100, reach: 0, watchTimeSeconds: 0, reactions: 0, comments: 0, shares: 0 },
      { videoAssetId: 2, videoAsset: { externalVideoId: "v2", title: "B" }, date: "2026-06-01", videoViews3s: 500, reach: 0, watchTimeSeconds: 0, reactions: 0, comments: 0, shares: 0 },
    ];
    const top = topVideosByViews(rows, 5);
    expect(top[0].externalVideoId).toBe("v2");
  });
});

describe("detectVideoSpikes", () => {
  it("detects daily view spikes", () => {
    const rows = Array.from({ length: 5 }, (_, i) => ({
      videoAssetId: 1, date: `2026-06-0${i + 1}`, videoViews3s: 100, reach: 50, watchTimeSeconds: 200, reactions: 0, comments: 0, shares: 0,
    }));
    rows.push({ videoAssetId: 1, date: "2026-06-06", videoViews3s: 5000, reach: 2000, watchTimeSeconds: 10000, reactions: 0, comments: 0, shares: 0 });
    const spikes = detectVideoSpikes(rows);
    expect(spikes.length).toBeGreaterThanOrEqual(1);
    expect(spikes[0].date).toBe("2026-06-06");
  });
});

describe("buildMonthlyReport", () => {
  it("includes all sections", () => {
    const posts = [makePost()];
    const videoDaily = [{ videoAssetId: 1, videoAsset: { externalVideoId: "v1", title: "Test" }, date: "2026-06-01", videoViews3s: 100, reach: 50, watchTimeSeconds: 200, reactions: 0, comments: 0, shares: 0 }];
    const report = buildMonthlyReport("2026-06", posts, videoDaily);
    expect(report.month).toBe("2026-06");
    expect(report.page.totalPosts).toBe(1);
    expect(report.video.totalViews3s).toBe(100);
    expect(report.dataQuality.length).toBeGreaterThan(0);
  });
});

describe("formatMonthlyReportMarkdown", () => {
  it("generates valid markdown with sections", () => {
    const posts = [makePost()];
    const report = buildMonthlyReport("2026-06", posts, []);
    const md = formatMonthlyReportMarkdown(report);
    expect(md).toContain("# Báo cáo tháng 2026-06");
    expect(md).toContain("## 1. Tổng quan");
    expect(md).toContain("## 2. Top Posts");
    expect(md).toContain("## 3. Video");
    expect(md).toContain("## 4. Spike Detection");
    expect(md).toContain("## 5. Data Quality");
  });

  it("includes data quality warnings", () => {
    const report = buildMonthlyReport("2026-06", [], []);
    const md = formatMonthlyReportMarkdown(report);
    expect(md).toContain("Summed reach is NOT unique Page reach");
    expect(md).toContain("Video assets not linked");
    expect(md).toContain("ER excludes clicks");
  });
});
