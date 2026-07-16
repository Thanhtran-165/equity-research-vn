import { describe, it, expect } from "vitest";
import { aggregatePostsToPeriod, getPeriodBounds } from "../benchmark/periodAggregation";

describe("aggregatePostsToPeriod", () => {
  it("returns empty aggregation for no posts", () => {
    const agg = aggregatePostsToPeriod([]);
    expect(agg.postsCaptured).toBe(0);
    expect(agg.totalComparableEngagement).toBeNull();
    expect(agg.medianComparableEngagementPerPost).toBeNull();
  });

  it("computes totals and medians correctly", () => {
    const posts = [
      { reactions: 100, comments: 20, shares: 5, publicVideoViews: null, reactionsObserved: true, commentsObserved: true, sharesObserved: true, publicVideoViewsObserved: false, comparableEngagement: 120, observedPublicEngagement: 125, metricCoverageScore: 0.9 },
      { reactions: 200, comments: 50, shares: 10, publicVideoViews: null, reactionsObserved: true, commentsObserved: true, sharesObserved: true, publicVideoViewsObserved: false, comparableEngagement: 250, observedPublicEngagement: 260, metricCoverageScore: 0.9 },
      { reactions: 50, comments: 5, shares: null, publicVideoViews: null, reactionsObserved: true, commentsObserved: true, sharesObserved: false, publicVideoViewsObserved: false, comparableEngagement: 55, observedPublicEngagement: 55, metricCoverageScore: 0.7 },
    ];
    const agg = aggregatePostsToPeriod(posts);
    expect(agg.postsCaptured).toBe(3);
    expect(agg.totalReactions).toBe(350);
    expect(agg.totalComments).toBe(75);
    expect(agg.totalShares).toBe(15);
    expect(agg.totalComparableEngagement).toBe(425);
    // median of [55, 120, 250] = 120
    expect(agg.medianComparableEngagementPerPost).toBe(120);
    expect(agg.avgComparableEngagementPerPost).toBeCloseTo(425 / 3);
  });

  it("computes share ratio from totals", () => {
    const posts = [
      { reactions: 100, comments: 0, shares: 50, publicVideoViews: null, reactionsObserved: true, commentsObserved: true, sharesObserved: true, publicVideoViewsObserved: false, comparableEngagement: 100, observedPublicEngagement: 150, metricCoverageScore: 0.9 },
    ];
    const agg = aggregatePostsToPeriod(posts);
    // shareRatio = totalShares / totalObserved = 50 / 150
    expect(agg.shareRatio).toBeCloseTo(50 / 150);
  });

  it("computes engagement per follower when type=followers", () => {
    const posts = [
      { reactions: 100, comments: 50, shares: null, publicVideoViews: null, reactionsObserved: true, commentsObserved: true, sharesObserved: false, publicVideoViewsObserved: false, comparableEngagement: 150, observedPublicEngagement: 150, metricCoverageScore: 0.7 },
    ];
    const agg = aggregatePostsToPeriod(posts, 10000, "followers");
    // 150 / 10000
    expect(agg.engagementPerFollower).toBeCloseTo(150 / 10000);
  });

  it("returns null for engagement per follower when type != followers", () => {
    const posts = [
      { reactions: 100, comments: 50, shares: null, publicVideoViews: null, reactionsObserved: true, commentsObserved: true, sharesObserved: false, publicVideoViewsObserved: false, comparableEngagement: 150, observedPublicEngagement: 150, metricCoverageScore: 0.7 },
    ];
    const agg = aggregatePostsToPeriod(posts, 10000, "members");
    expect(agg.engagementPerFollower).toBeNull();
  });

  it("computes viral hit rate with minimum sample", () => {
    // 5 posts, median = 100, 3x = 300, one qualifies
    const posts = [50, 80, 100, 150, 500].map((ce) => ({
      reactions: ce, comments: 0, shares: null, publicVideoViews: null,
      reactionsObserved: true, commentsObserved: true, sharesObserved: false, publicVideoViewsObserved: false,
      comparableEngagement: ce, observedPublicEngagement: ce, metricCoverageScore: 0.7,
    }));
    const agg = aggregatePostsToPeriod(posts);
    expect(agg.viralHitRate).toBeCloseTo(1 / 5);
  });
});

describe("getPeriodBounds", () => {
  it("returns Monday-Sunday for weekly", () => {
    // 2026-07-10 is a Friday
    const date = new Date(2026, 6, 10); // July 10, 2026
    const { start, end } = getPeriodBounds(date, "weekly");
    expect(start.getDay()).toBe(1); // Monday
    expect(end.getDay()).toBe(0); // Sunday
  });

  it("returns month bounds for monthly", () => {
    const date = new Date(2026, 6, 15); // July 15
    const { start, end } = getPeriodBounds(date, "monthly");
    expect(start.getDate()).toBe(1);
    expect(start.getMonth()).toBe(6); // July
    expect(end.getMonth()).toBe(6);
    expect(end.getDate()).toBe(31); // July has 31 days
  });
});
