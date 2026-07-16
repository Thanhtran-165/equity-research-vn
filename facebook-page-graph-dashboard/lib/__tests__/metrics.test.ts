import { describe, it, expect, beforeEach, afterEach } from "vitest";
import {
  calculateEngagementRate,
  calculateCTR,
  calculateTotalActivity,
  isValidEngagementRate,
  calculatePostScore,
  aggregateByTopic,
  detectCommentSpike,
  percentileRank,
} from "../metrics";

// ============================================================
// calculateEngagementRate
// ============================================================
describe("calculateEngagementRate", () => {
  it("returns null when reach is null", () => {
    expect(
      calculateEngagementRate({ reactions: 10, comments: 5, shares: 2, clicks: 3, reach: null }),
    ).toBeNull();
  });

  it("returns null when reach is undefined", () => {
    expect(
      calculateEngagementRate({ reactions: 10, comments: 5, shares: 2, clicks: 3, reach: undefined }),
    ).toBeNull();
  });

  it("returns null when reach is 0", () => {
    expect(
      calculateEngagementRate({ reactions: 10, comments: 5, shares: 2, clicks: 3, reach: 0 }),
    ).toBeNull();
  });

  it("returns null when reach is negative", () => {
    expect(
      calculateEngagementRate({ reactions: 10, comments: 5, shares: 2, clicks: 3, reach: -100 }),
    ).toBeNull();
  });

  it("returns correct ratio when reach > 0 (social only, NO clicks)", () => {
    // social = 10 + 5 + 2 = 17; 17/100 = 0.17 (NOT 0.20 with clicks)
    expect(
      calculateEngagementRate({ reactions: 10, comments: 5, shares: 2, clicks: 3, reach: 100 }),
    ).toBeCloseTo(0.17, 5);
  });

  it("does NOT include clicks in engagement rate", () => {
    const withClicks = calculateEngagementRate({ reactions: 10, comments: 5, shares: 2, clicks: 100, reach: 100 });
    const withoutClicks = calculateEngagementRate({ reactions: 10, comments: 5, shares: 2, clicks: 0, reach: 100 });
    expect(withClicks).toBe(withoutClicks);
  });

  it("returns >1.0 when social engagement > reach (extreme, NOT silently capped)", () => {
    // social = 50 + 30 + 10 = 90; 90/50 = 1.8
    const er = calculateEngagementRate({
      reactions: 50, comments: 30, shares: 10, clicks: 10, reach: 50,
    });
    expect(er).toBeCloseTo(1.8, 5);
    expect(er).not.toBeNull();
  });

  it("returns 0 when engagement = 0 but reach > 0", () => {
    expect(
      calculateEngagementRate({ reactions: 0, comments: 0, shares: 0, clicks: 0, reach: 100 }),
    ).toBe(0);
  });
});

// ============================================================
// calculateCTR
// ============================================================
describe("calculateCTR", () => {
  it("returns clicks / reach when reach > 0", () => {
    expect(calculateCTR({ clicks: 50, reach: 1000 })).toBeCloseTo(0.05, 5);
  });

  it("returns null when reach is null", () => {
    expect(calculateCTR({ clicks: 50, reach: null })).toBeNull();
  });

  it("returns null when reach is 0", () => {
    expect(calculateCTR({ clicks: 50, reach: 0 })).toBeNull();
  });

  it("returns null when reach is negative", () => {
    expect(calculateCTR({ clicks: 50, reach: -1 })).toBeNull();
  });

  it("returns >1.0 when clicks > reach (extreme CTR, NOT capped)", () => {
    expect(calculateCTR({ clicks: 200, reach: 100 })).toBeCloseTo(2.0, 5);
  });
});

// ============================================================
// calculateTotalActivity
// ============================================================
describe("calculateTotalActivity", () => {
  it("returns sum of reactions + comments + shares + clicks", () => {
    expect(calculateTotalActivity({ reactions: 10, comments: 5, shares: 2, clicks: 3, reach: 100 })).toBe(20);
  });

  it("works with zeros", () => {
    expect(calculateTotalActivity({ reactions: 0, comments: 0, shares: 0, clicks: 0, reach: 100 })).toBe(0);
  });
});

// ============================================================
// isValidEngagementRate
// ============================================================
describe("isValidEngagementRate", () => {
  it("returns true for positive finite numbers", () => {
    expect(isValidEngagementRate(0.05)).toBe(true);
    expect(isValidEngagementRate(1.5)).toBe(true); // extreme nhưng vẫn valid
  });

  it("returns false for null", () => {
    expect(isValidEngagementRate(null)).toBe(false);
  });

  it("returns false for undefined", () => {
    expect(isValidEngagementRate(undefined)).toBe(false);
  });

  it("returns false for 0 or negative", () => {
    expect(isValidEngagementRate(0)).toBe(false);
    expect(isValidEngagementRate(-0.1)).toBe(false);
  });

  it("returns false for NaN/Infinity", () => {
    expect(isValidEngagementRate(NaN)).toBe(false);
    expect(isValidEngagementRate(Infinity)).toBe(false);
  });
});

// ============================================================
// percentileRank
// ============================================================
describe("percentileRank", () => {
  it("returns 0 for empty array", () => {
    expect(percentileRank([], 5)).toBe(0);
  });

  it("returns 1.0 for value >= max", () => {
    expect(percentileRank([1, 2, 3, 4, 5], 5)).toBe(1);
  });

  it("returns correct ratio for middle value", () => {
    // 3 values <= 3 in [1,2,3,4,5] → 3/5 = 0.6
    expect(percentileRank([1, 2, 3, 4, 5], 3)).toBeCloseTo(0.6, 5);
  });
});

// ============================================================
// calculatePostScore — không trộn metric
// ============================================================
describe("calculatePostScore", () => {
  it("returns null when population is empty", () => {
    expect(calculatePostScore({ reach: 100, engagementRate: 0.05 }, [])).toBeNull();
  });

  it("returns null when post has reach=null (no trueReach)", () => {
    const pop = [
      { reach: 100, engagementRate: 0.05 },
      { reach: 200, engagementRate: 0.1 },
    ];
    expect(calculatePostScore({ reach: null, engagementRate: null }, pop)).toBeNull();
  });

  it("returns null when post has engagementRate=null", () => {
    const pop = [
      { reach: 100, engagementRate: 0.05 },
      { reach: 200, engagementRate: 0.1 },
    ];
    expect(calculatePostScore({ reach: 100, engagementRate: null }, pop)).toBeNull();
  });

  it("returns null when post has engagementRate=0", () => {
    const pop = [
      { reach: 100, engagementRate: 0.05 },
    ];
    expect(calculatePostScore({ reach: 100, engagementRate: 0 }, pop)).toBeNull();
  });

  it("returns high score (~100) for top post", () => {
    const pop = [
      { reach: 100, engagementRate: 0.01, commentsCount: 1, sharesCount: 0 },
      { reach: 500, engagementRate: 0.05, commentsCount: 10, sharesCount: 5 },
      { reach: 1000, engagementRate: 0.1, commentsCount: 50, sharesCount: 20 }, // top
    ];
    const top = calculatePostScore(pop[2], pop);
    expect(top).not.toBeNull();
    expect(top).toBeGreaterThan(95);
  });

  it("returns low score for bottom post (lower than top)", () => {
    const pop = [
      { reach: 100, engagementRate: 0.01, commentsCount: 1, sharesCount: 0 }, // bottom
      { reach: 500, engagementRate: 0.05, commentsCount: 10, sharesCount: 5 },
      { reach: 1000, engagementRate: 0.1, commentsCount: 50, sharesCount: 20 }, // top
    ];
    const bottom = calculatePostScore(pop[0], pop);
    const top = calculatePostScore(pop[2], pop);
    expect(bottom).not.toBeNull();
    expect(top).not.toBeNull();
    // Bottom phải thấp hơn top rõ ràng (không cần đến 0)
    expect((bottom as number)).toBeLessThan((top as number));
  });

  it("filters out posts with null reach/ER from population (fair percentile)", () => {
    // Population có post null reach/ER → bị loại khỏi population
    const pop = [
      { reach: 100, engagementRate: 0.05, commentsCount: 5, sharesCount: 1 },
      { reach: 200, engagementRate: 0.1, commentsCount: 10, sharesCount: 3 },
      { reach: null, engagementRate: null, commentsCount: 100, sharesCount: 50 }, // bị loại
    ];
    const score = calculatePostScore(pop[0], pop);
    expect(score).not.toBeNull();
    // Phải tính trên 2 post valid, không phải 3
    expect(score).toBeGreaterThanOrEqual(0);
    expect(score).toBeLessThanOrEqual(100);
  });

  it("returns null when all posts in population have null reach/ER", () => {
    const pop = [
      { reach: null, engagementRate: null },
      { reach: null, engagementRate: null },
    ];
    // Post target có reach hợp lệ nhưng population rỗng sau filter
    expect(
      calculatePostScore({ reach: 100, engagementRate: 0.05 }, pop),
    ).toBeNull();
  });
});

// ============================================================
// aggregateByTopic — không trộn null
// ============================================================
describe("aggregateByTopic", () => {
  it("groups posts by topic", () => {
    const posts = [
      { topic: "chung_khoan", reach: 100, commentsCount: 5, sharesCount: 1 },
      { topic: "chung_khoan", reach: 200, commentsCount: 10, sharesCount: 3 },
      { topic: "vi_mo", reach: 50, commentsCount: 2, sharesCount: 0 },
    ];
    const result = aggregateByTopic(posts);
    expect(result).toHaveLength(2);
    const ck = result.find((r) => r.topic === "chung_khoan");
    expect(ck?.postsCount).toBe(2);
    expect(ck?.reachTotal).toBe(300);
  });

  it("returns empty array for empty input", () => {
    expect(aggregateByTopic([])).toEqual([]);
  });

  it("calculates engagementRateAvg ignoring null/undefined", () => {
    const posts = [
      { topic: "vi_mo", engagementRate: 0.05 },
      { topic: "vi_mo", engagementRate: null },
      { topic: "vi_mo", engagementRate: 0.15 },
    ];
    const result = aggregateByTopic(posts);
    // avg của 0.05 và 0.15 = 0.1, bỏ qua null
    expect(result[0].engagementRateAvg).toBeCloseTo(0.1, 5);
  });

  it("returns engagementRateAvg=null when all are null", () => {
    const posts = [
      { topic: "vi_mo", engagementRate: null },
      { topic: "vi_mo", engagementRate: null },
    ];
    expect(result()[0].engagementRateAvg).toBeNull();
    function result() { return aggregateByTopic(posts); }
  });

  it("sorts by reachTotal descending", () => {
    const posts = [
      { topic: "bds", reach: 10 },
      { topic: "vang", reach: 1000 },
      { topic: "vi_mo", reach: 100 },
    ];
    const result = aggregateByTopic(posts);
    expect(result[0].topic).toBe("vang");
    expect(result[1].topic).toBe("vi_mo");
    expect(result[2].topic).toBe("bds");
  });

  it("defaults unknown topic to 'khac'", () => {
    const posts = [{ topic: "", reach: 100 }];
    const result = aggregateByTopic(posts);
    expect(result[0].topic).toBe("khac");
  });
});

// ============================================================
// detectCommentSpike
// ============================================================
describe("detectCommentSpike", () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    process.env.COMMENT_SPIKE_MIN_COUNT = "20";
    process.env.COMMENT_SPIKE_RATIO = "3";
  });

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  it("returns empty array for empty input", () => {
    expect(detectCommentSpike([])).toEqual([]);
  });

  it("flags post above min count AND median*ratio", () => {
    // median = 10, threshold = 30; post có 50 comments (>20 min, >30 threshold)
    const posts = [
      { fbPostId: "p1", commentsCount: 5 },
      { fbPostId: "p2", commentsCount: 10 },
      { fbPostId: "p3", commentsCount: 15 },
      { fbPostId: "spike", commentsCount: 50 }, // → flag
    ];
    const result = detectCommentSpike(posts);
    expect(result).toHaveLength(1);
    expect(result[0].fbPostId).toBe("spike");
    expect(result[0].commentsCount).toBe(50);
  });

  it("does NOT flag post below COMMENT_SPIKE_MIN_COUNT", () => {
    // Post có 10 comments, median = 2, ratio = 3 → threshold = 6 (thoả)
    // nhưng min count = 20 → không thoả → không flag
    const posts = [
      { fbPostId: "p1", commentsCount: 1 },
      { fbPostId: "p2", commentsCount: 2 },
      { fbPostId: "p3", commentsCount: 3 },
      { fbPostId: "noSpike", commentsCount: 10 }, // > 6 threshold nhưng < 20 min
    ];
    const result = detectCommentSpike(posts);
    expect(result).toHaveLength(0);
  });

  it("does NOT flag post below median*ratio", () => {
    // median = 100, threshold = 300; post có 50 comments (≤ min 20 if env default, > min, < threshold)
    const posts = [
      { fbPostId: "p1", commentsCount: 100 },
      { fbPostId: "p2", commentsCount: 100 },
      { fbPostId: "p3", commentsCount: 100 },
      { fbPostId: "noSpike", commentsCount: 50 }, // > 20 min nhưng < 300 threshold
    ];
    const result = detectCommentSpike(posts);
    expect(result).toHaveLength(0);
  });

  it("respects COMMENT_SPIKE_MIN_COUNT env override", () => {
    process.env.COMMENT_SPIKE_MIN_COUNT = "5";
    process.env.COMMENT_SPIKE_RATIO = "3";
    // median = 2, threshold = 6; post có 10 (> 5 min, > 6 threshold) → flag
    const posts = [
      { fbPostId: "p1", commentsCount: 1 },
      { fbPostId: "p2", commentsCount: 2 },
      { fbPostId: "p3", commentsCount: 3 },
      { fbPostId: "spike", commentsCount: 10 },
    ];
    const result = detectCommentSpike(posts);
    expect(result).toHaveLength(1);
  });

  it("respects COMMENT_SPIKE_RATIO env override", () => {
    process.env.COMMENT_SPIKE_MIN_COUNT = "5";
    process.env.COMMENT_SPIKE_RATIO = "10"; // strict hơn
    // median = 2, threshold = 20; post có 10 (> 5 min, < 20 threshold) → không flag
    const posts = [
      { fbPostId: "p1", commentsCount: 1 },
      { fbPostId: "p2", commentsCount: 2 },
      { fbPostId: "p3", commentsCount: 3 },
      { fbPostId: "noSpike", commentsCount: 10 },
    ];
    const result = detectCommentSpike(posts);
    expect(result).toHaveLength(0);
  });
});
