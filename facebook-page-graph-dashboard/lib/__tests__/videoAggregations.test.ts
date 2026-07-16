import { describe, it, expect } from "vitest";
import {
  computeSocialER,
  computeAvgWatchPerView,
  aggregateDaily,
  aggregateMonthly,
  computeVideoSummary,
  detectVideoAnomalies,
} from "../videoAggregations";

describe("computeSocialER", () => {
  it("returns social engagement rate (excludes clicks)", () => {
    expect(computeSocialER(10, 5, 2, 1000)).toBeCloseTo(0.017, 5);
  });

  it("returns null when reach is 0", () => {
    expect(computeSocialER(10, 5, 2, 0)).toBeNull();
  });

  it("returns null when reach is negative", () => {
    expect(computeSocialER(10, 5, 2, -1)).toBeNull();
  });
});

describe("computeAvgWatchPerView", () => {
  it("returns watchTimeSeconds / videoViews3s", () => {
    expect(computeAvgWatchPerView(5000, 100)).toBe(50);
  });

  it("returns null when views is 0", () => {
    expect(computeAvgWatchPerView(5000, 0)).toBeNull();
  });

  it("returns null when views is negative", () => {
    expect(computeAvgWatchPerView(5000, -1)).toBeNull();
  });

  it("handles zero division safely", () => {
    expect(computeAvgWatchPerView(0, 0)).toBeNull();
  });
});

describe("aggregateDaily", () => {
  it("groups by date and sums metrics", () => {
    const rows = [
      { date: "2026-01-01", videoAssetId: 1, videoViews3s: 100, reach: 200, watchTimeSeconds: 500, reactions: 5, comments: 2, shares: 1 },
      { date: "2026-01-01", videoAssetId: 2, videoViews3s: 50, reach: 100, watchTimeSeconds: 250, reactions: 3, comments: 1, shares: 0 },
      { date: "2026-01-02", videoAssetId: 1, videoViews3s: 200, reach: 400, watchTimeSeconds: 1000, reactions: 10, comments: 5, shares: 2 },
    ];
    const daily = aggregateDaily(rows);
    expect(daily).toHaveLength(2);
    const jan1 = daily[0];
    expect(jan1.date).toBe("2026-01-01");
    expect(jan1.videoViews3s).toBe(150);
    expect(jan1.reach).toBe(300);
    expect(jan1.watchTimeSeconds).toBe(750);
    expect(jan1.reactions).toBe(8);
    expect(jan1.activeVideos).toBe(2);
  });

  it("computes watchTimeHours", () => {
    const rows = [
      { date: "2026-01-01", videoAssetId: 1, videoViews3s: 100, reach: 0, watchTimeSeconds: 3600, reactions: 0, comments: 0, shares: 0 },
    ];
    const daily = aggregateDaily(rows);
    expect(daily[0].watchTimeHours).toBe(1);
  });

  it("computes avgWatchTimePerView", () => {
    const rows = [
      { date: "2026-01-01", videoAssetId: 1, videoViews3s: 100, reach: 0, watchTimeSeconds: 500, reactions: 0, comments: 0, shares: 0 },
    ];
    const daily = aggregateDaily(rows);
    expect(daily[0].avgWatchTimePerView).toBe(5);
  });
});

describe("aggregateMonthly", () => {
  it("groups daily into months", () => {
    const daily = [
      { date: "2026-01-01", videoViews3s: 100, reach: 200, watchTimeSeconds: 500, watchTimeHours: 500/3600, avgWatchTimePerView: 5, socialEngagement: 8, socialEngagementRate: null, reactions: 5, comments: 2, shares: 1, activeVideos: 2 },
      { date: "2026-01-15", videoViews3s: 200, reach: 400, watchTimeSeconds: 1000, watchTimeHours: 1000/3600, avgWatchTimePerView: 5, socialEngagement: 17, socialEngagementRate: null, reactions: 10, comments: 5, shares: 2, activeVideos: 1 },
      { date: "2026-02-01", videoViews3s: 50, reach: 100, watchTimeSeconds: 250, watchTimeHours: 250/3600, avgWatchTimePerView: 5, socialEngagement: 4, socialEngagementRate: null, reactions: 3, comments: 1, shares: 0, activeVideos: 1 },
    ];
    const monthly = aggregateMonthly(daily);
    expect(monthly).toHaveLength(2);
    expect(monthly[0].month).toBe("2026-01");
    expect(monthly[0].videoViews3s).toBe(300);
    expect(monthly[1].month).toBe("2026-02");
  });
});

describe("computeVideoSummary", () => {
  it("aggregates lifetime metrics with asset breakdown", () => {
    const lifetime = [
      { videoAssetId: 1, externalVideoId: "v1", title: "A", reach: 1000, videoViews3s: 500, videoViews1min: 100, watchTimeSeconds: 5000, avgWatchTime: 10, reactions: 50, comments: 10, shares: 5, matchedPostId: null },
      { videoAssetId: 2, externalVideoId: "v2", title: "B", reach: 2000, videoViews3s: 1000, videoViews1min: 200, watchTimeSeconds: 10000, avgWatchTime: 10, reactions: 100, comments: 20, shares: 10, matchedPostId: null },
    ];
    const summary = computeVideoSummary(lifetime, 100, { min: "2026-01-01", max: "2026-07-08" }, 5, [1, 2, 3, 4, 5], [1, 2]);
    expect(summary.totalVideoAssets).toBe(5);
    expect(summary.lifetimeAssets).toBe(2);
    expect(summary.dailyActiveAssets).toBe(5);
    expect(summary.dailyOnlyAssets).toBe(3); // 3,4,5 are daily-only
    expect(summary.totalViews3s).toBe(1500);
    expect(summary.totalReach).toBe(3000);
    expect(summary.totalWatchTimeHours).toBeCloseTo(15000 / 3600, 5);
    expect(summary.unlinkedAssets).toBe(2);
  });

  it("counts daily-only assets correctly", () => {
    const lifetime = [
      { videoAssetId: 1, externalVideoId: "v1", title: "A", reach: 100, videoViews3s: 50, videoViews1min: null, watchTimeSeconds: 500, avgWatchTime: 10, reactions: 5, comments: 1, shares: 0, matchedPostId: null },
    ];
    const summary = computeVideoSummary(lifetime, 50, { min: "2026-01-01", max: "2026-06-30" }, 3, [1, 2, 3], [1]);
    expect(summary.totalVideoAssets).toBe(3);
    expect(summary.lifetimeAssets).toBe(1);
    expect(summary.dailyActiveAssets).toBe(3);
    expect(summary.dailyOnlyAssets).toBe(2);
  });
});

describe("detectVideoAnomalies", () => {
  it("flags avgWatchTimePerView > 600 seconds", () => {
    const lifetime = [
      { videoAssetId: 1, externalVideoId: "v1", title: "A", reach: 100, videoViews3s: 1, videoViews1min: null, watchTimeSeconds: 700, avgWatchTime: null, reactions: 0, comments: 0, shares: 0, matchedPostId: null },
    ];
    const anomalies = detectVideoAnomalies(lifetime);
    expect(anomalies.some((a) => a.type === "high_avg_watch")).toBe(true);
  });

  it("flags reach = 0 but views > 0", () => {
    const lifetime = [
      { videoAssetId: 1, externalVideoId: "v1", title: "A", reach: 0, videoViews3s: 100, videoViews1min: null, watchTimeSeconds: 0, avgWatchTime: null, reactions: 0, comments: 0, shares: 0, matchedPostId: null },
    ];
    const anomalies = detectVideoAnomalies(lifetime);
    expect(anomalies.some((a) => a.type === "zero_reach_with_views")).toBe(true);
  });

  it("flags views = 0 but watchTime > 0", () => {
    const lifetime = [
      { videoAssetId: 1, externalVideoId: "v1", title: "A", reach: 0, videoViews3s: 0, videoViews1min: null, watchTimeSeconds: 500, avgWatchTime: null, reactions: 0, comments: 0, shares: 0, matchedPostId: null },
    ];
    const anomalies = detectVideoAnomalies(lifetime);
    expect(anomalies.some((a) => a.type === "zero_views_with_watch")).toBe(true);
  });

  it("does not flag normal videos", () => {
    const lifetime = [
      { videoAssetId: 1, externalVideoId: "v1", title: "A", reach: 1000, videoViews3s: 500, videoViews1min: null, watchTimeSeconds: 5000, avgWatchTime: 10, reactions: 50, comments: 5, shares: 2, matchedPostId: null },
    ];
    const anomalies = detectVideoAnomalies(lifetime);
    expect(anomalies).toHaveLength(0);
  });
});
