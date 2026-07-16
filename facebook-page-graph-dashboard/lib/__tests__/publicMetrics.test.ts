import { describe, it, expect } from "vitest";
import {
  calculateComparableEngagement,
  calculateObservedPublicEngagement,
  calculateMetricCoverageScore,
  calculateShareRatio,
  calculateCommentRatio,
  calculateViralHitRate,
  calculateEngagementPerFollower,
  derivePostMetrics,
  isLeaderboardEligible,
  median,
  type PublicPostMetrics,
} from "../benchmark/publicMetrics";

describe("calculateComparableEngagement", () => {
  it("returns reactions + comments when both observed", () => {
    const m: PublicPostMetrics = { reactions: 100, comments: 20, shares: 5, publicVideoViews: null, reactionsObserved: true, commentsObserved: true, sharesObserved: true, publicVideoViewsObserved: false };
    expect(calculateComparableEngagement(m)).toBe(120);
  });

  it("returns null when reactions not observed", () => {
    const m: PublicPostMetrics = { reactions: null, comments: 20, shares: 5, publicVideoViews: null, reactionsObserved: false, commentsObserved: true, sharesObserved: true, publicVideoViewsObserved: false };
    expect(calculateComparableEngagement(m)).toBeNull();
  });

  it("returns null when comments not observed", () => {
    const m: PublicPostMetrics = { reactions: 100, comments: null, shares: 5, publicVideoViews: null, reactionsObserved: true, commentsObserved: false, sharesObserved: true, publicVideoViewsObserved: false };
    expect(calculateComparableEngagement(m)).toBeNull();
  });

  it("includes observed zero values correctly", () => {
    const m: PublicPostMetrics = { reactions: 0, comments: 0, shares: null, publicVideoViews: null, reactionsObserved: true, commentsObserved: true, sharesObserved: false, publicVideoViewsObserved: false };
    expect(calculateComparableEngagement(m)).toBe(0);
  });
});

describe("calculateObservedPublicEngagement", () => {
  it("includes shares when observed", () => {
    const m: PublicPostMetrics = { reactions: 100, comments: 20, shares: 5, publicVideoViews: null, reactionsObserved: true, commentsObserved: true, sharesObserved: true, publicVideoViewsObserved: false };
    expect(calculateObservedPublicEngagement(m)).toBe(125);
  });

  it("excludes shares when not observed (null)", () => {
    const m: PublicPostMetrics = { reactions: 100, comments: 20, shares: null, publicVideoViews: null, reactionsObserved: true, commentsObserved: true, sharesObserved: false, publicVideoViewsObserved: false };
    expect(calculateObservedPublicEngagement(m)).toBe(120);
  });

  it("returns null when base comparable is null", () => {
    const m: PublicPostMetrics = { reactions: null, comments: null, shares: 5, publicVideoViews: null, reactionsObserved: false, commentsObserved: false, sharesObserved: true, publicVideoViewsObserved: false };
    expect(calculateObservedPublicEngagement(m)).toBeNull();
  });
});

describe("calculateMetricCoverageScore", () => {
  it("returns 1.0 when all metrics observed", () => {
    const m: PublicPostMetrics = { reactions: 1, comments: 1, shares: 1, publicVideoViews: 1, reactionsObserved: true, commentsObserved: true, sharesObserved: true, publicVideoViewsObserved: true };
    expect(calculateMetricCoverageScore(m)).toBeCloseTo(1.0);
  });

  it("returns 0.70 when only reactions + comments", () => {
    const m: PublicPostMetrics = { reactions: 1, comments: 1, shares: null, publicVideoViews: null, reactionsObserved: true, commentsObserved: true, sharesObserved: false, publicVideoViewsObserved: false };
    expect(calculateMetricCoverageScore(m)).toBeCloseTo(0.70);
  });

  it("returns 0 when nothing observed", () => {
    const m: PublicPostMetrics = { reactions: null, comments: null, shares: null, publicVideoViews: null, reactionsObserved: false, commentsObserved: false, sharesObserved: false, publicVideoViewsObserved: false };
    expect(calculateMetricCoverageScore(m)).toBe(0);
  });
});

describe("calculateShareRatio", () => {
  it("returns shares / observedEngagement when shares observed", () => {
    const m: PublicPostMetrics = { reactions: 100, comments: 20, shares: 30, publicVideoViews: null, reactionsObserved: true, commentsObserved: true, sharesObserved: true, publicVideoViewsObserved: false };
    // observed = 100 + 20 + 30 = 150
    expect(calculateShareRatio(m)).toBeCloseTo(30 / 150);
  });

  it("returns null when shares not observed", () => {
    const m: PublicPostMetrics = { reactions: 100, comments: 20, shares: null, publicVideoViews: null, reactionsObserved: true, commentsObserved: true, sharesObserved: false, publicVideoViewsObserved: false };
    expect(calculateShareRatio(m)).toBeNull();
  });
});

describe("calculateCommentRatio", () => {
  it("returns comments / comparableEngagement", () => {
    const m: PublicPostMetrics = { reactions: 100, comments: 30, shares: null, publicVideoViews: null, reactionsObserved: true, commentsObserved: true, sharesObserved: false, publicVideoViewsObserved: false };
    // comparable = 100 + 30 = 130
    expect(calculateCommentRatio(m)).toBeCloseTo(30 / 130);
  });

  it("returns null when comparableEngagement is 0", () => {
    const m: PublicPostMetrics = { reactions: 0, comments: 0, shares: null, publicVideoViews: null, reactionsObserved: true, commentsObserved: true, sharesObserved: false, publicVideoViewsObserved: false };
    expect(calculateCommentRatio(m)).toBeNull();
  });
});

describe("calculateViralHitRate", () => {
  it("returns fraction of posts >= 3x median", () => {
    // median of [10, 20, 30, 40, 100] = 30
    // 3x median = 90; only 100 qualifies
    const engs = [10, 20, 30, 40, 100].map((n) => n);
    expect(calculateViralHitRate(engs)).toBeCloseTo(1 / 5);
  });

  it("returns null when fewer than minSample posts", () => {
    expect(calculateViralHitRate([10, 20, 30])).toBeNull();
  });

  it("returns null when all engagements are 0", () => {
    expect(calculateViralHitRate([0, 0, 0, 0, 0])).toBeNull();
  });
});

describe("calculateEngagementPerFollower", () => {
  it("returns total / followers when type=followers", () => {
    expect(calculateEngagementPerFollower(500, 10000, "followers")).toBeCloseTo(0.05);
  });

  it("returns null when type is not followers", () => {
    expect(calculateEngagementPerFollower(500, 10000, "members")).toBeNull();
  });

  it("returns null when followers is 0", () => {
    expect(calculateEngagementPerFollower(500, 0, "followers")).toBeNull();
  });
});

describe("derivePostMetrics", () => {
  it("treats blank as null (NOT zero)", () => {
    const d = derivePostMetrics({ reactions: "", comments: "", shares: "", publicVideoViews: "" });
    expect(d.reactions).toBeNull();
    expect(d.reactionsObserved).toBe(false);
    expect(d.comparableEngagement).toBeNull();
  });

  it("treats '0' as observed zero", () => {
    const d = derivePostMetrics({ reactions: "0", comments: "0", shares: "", publicVideoViews: "" });
    expect(d.reactions).toBe(0);
    expect(d.reactionsObserved).toBe(true);
    expect(d.comparableEngagement).toBe(0);
  });

  it("parses numeric strings", () => {
    const d = derivePostMetrics({ reactions: "150", comments: "25", shares: "8", publicVideoViews: "1000" });
    expect(d.reactions).toBe(150);
    expect(d.comparableEngagement).toBe(175);
    expect(d.observedPublicEngagement).toBe(183);
  });
});

describe("isLeaderboardEligible", () => {
  it("returns true for facebook_page + core_peer", () => {
    expect(isLeaderboardEligible("facebook_page", "core_peer", false)).toBe(true);
  });

  it("returns true for own page with facebook_page type", () => {
    expect(isLeaderboardEligible("facebook_page", "core_peer", true)).toBe(true);
  });

  it("returns false for facebook_group even if core_peer", () => {
    expect(isLeaderboardEligible("facebook_group", "core_peer", false)).toBe(false);
  });

  it("returns false for topic_reference role", () => {
    expect(isLeaderboardEligible("facebook_page", "topic_reference", false)).toBe(false);
  });
});

describe("median", () => {
  it("handles odd count", () => {
    expect(median([1, 3, 5])).toBe(3);
  });

  it("handles even count", () => {
    expect(median([1, 2, 3, 4])).toBe(2.5);
  });

  it("handles nulls", () => {
    expect(median([1, null, 3, null, 5])).toBe(3);
  });

  it("returns null for empty array", () => {
    expect(median([])).toBeNull();
  });
});
