import { describe, it, expect } from "vitest";
import { applyImportedInsights } from "../imports/applyImportedInsights";
import type { NormalizedRow } from "../imports/normalizeRows";
import type { MatchResult } from "../imports/matchPosts";

function makeRow(overrides: Partial<NormalizedRow> = {}): NormalizedRow {
  return {
    postId: "100_1",
    permalinkUrl: "https://facebook.com/post/1",
    externalContentId: null,
    createdTime: "2026-07-01T08:00:00Z",
    messageSnippet: "Test post",
    reach: 1000,
    impressions: 5000,
    engagedUsers: 100,
    clicks: 50,
    reactions: 80,
    comments: 15,
    shares: 5,
    videoViews: null,
    watchTime: null,
    rawRowJson: "{}",
    ...overrides,
  };
}

function makeMatch(overrides: Partial<MatchResult> = {}): MatchResult {
  return {
    status: "matched",
    matchedPostId: "100_1",
    confidence: 1.0,
    ...overrides,
  };
}

describe("applyImportedInsights", () => {
  it("applies insights + sets metricSource = meta_business_suite_csv", () => {
    const r = applyImportedInsights({
      row: makeRow(),
      match: makeMatch(),
      currentMetricSource: "facebook_public_metrics",
    });
    expect(r.shouldApply).toBe(true);
    expect(r.patch?.metricSource).toBe("meta_business_suite_csv");
    expect(r.patch?.reach).toBe(1000);
    expect(r.patch?.impressions).toBe(5000);
    expect(r.patch?.clicks).toBe(50);
    expect(r.patch?.engagedUsers).toBe(100);
  });

  it("calculates engagementRate when reach > 0 (social only, NO clicks)", () => {
    const r = applyImportedInsights({
      row: makeRow({ reach: 1000, reactions: 50, comments: 10, shares: 5, clicks: 20 }),
      match: makeMatch(),
      currentMetricSource: "facebook_public_metrics",
    });
    expect(r.shouldApply).toBe(true);
    expect(r.patch?.engagementRate).not.toBeNull();
    // social ER = (50 + 10 + 5) / 1000 = 0.065 (clicks excluded)
    expect(r.patch?.engagementRate).toBeCloseTo(0.065, 5);
  });

  it("does NOT apply when match.status is unmatched", () => {
    const r = applyImportedInsights({
      row: makeRow(),
      match: makeMatch({ status: "unmatched", matchedPostId: null }),
      currentMetricSource: "facebook_public_metrics",
    });
    expect(r.shouldApply).toBe(false);
    expect(r.patch).toBeNull();
  });

  it("does NOT overwrite facebook_graph_api_insights by default", () => {
    const r = applyImportedInsights({
      row: makeRow(),
      match: makeMatch(),
      currentMetricSource: "facebook_graph_api_insights",
    });
    expect(r.shouldApply).toBe(false);
    expect(r.reason).toContain("facebook_graph_api_insights");
  });

  it("DOES overwrite facebook_graph_api_insights when forceOverwrite=true", () => {
    const r = applyImportedInsights({
      row: makeRow(),
      match: makeMatch(),
      currentMetricSource: "facebook_graph_api_insights",
      forceOverwrite: true,
    });
    expect(r.shouldApply).toBe(true);
    expect(r.patch?.metricSource).toBe("meta_business_suite_csv");
  });

  it("overwrites video_views when allowVideoViewsOverwrite=true", () => {
    const r = applyImportedInsights({
      row: makeRow({ videoViews: 500 }),
      match: makeMatch(),
      currentMetricSource: "facebook_video_metric",
      allowVideoViewsOverwrite: true,
    });
    expect(r.shouldApply).toBe(true);
    expect(r.patch?.videoViews).toBe(500);
  });

  it("does NOT overwrite video_views when allowVideoViewsOverwrite=false and current is video_metric", () => {
    const r = applyImportedInsights({
      row: makeRow({ videoViews: 500 }),
      match: makeMatch(),
      currentMetricSource: "facebook_video_metric",
      allowVideoViewsOverwrite: false,
    });
    expect(r.shouldApply).toBe(true);
    expect(r.patch?.videoViews).toBeUndefined();
  });

  it("does NOT calculate ER when reach is null", () => {
    const r = applyImportedInsights({
      row: makeRow({ reach: null }),
      match: makeMatch(),
      currentMetricSource: "facebook_public_metrics",
    });
    expect(r.shouldApply).toBe(true);
    expect(r.patch?.engagementRate).toBeUndefined();
  });

  it("does NOT calculate ER when reach is 0", () => {
    const r = applyImportedInsights({
      row: makeRow({ reach: 0 }),
      match: makeMatch(),
      currentMetricSource: "facebook_public_metrics",
    });
    expect(r.shouldApply).toBe(true);
    expect(r.patch?.engagementRate).toBeUndefined();
  });

  it("overwrites current facebook_public_metrics (CSV ưu tiên hơn proxy)", () => {
    const r = applyImportedInsights({
      row: makeRow({ reach: 1000 }),
      match: makeMatch(),
      currentMetricSource: "facebook_public_metrics",
    });
    expect(r.shouldApply).toBe(true);
    expect(r.patch?.reach).toBe(1000);
  });

  it("overwrites legacy public_engagement_proxy (deprecated)", () => {
    const r = applyImportedInsights({
      row: makeRow({ reach: 1000 }),
      match: makeMatch(),
      currentMetricSource: "public_engagement_proxy",
    });
    expect(r.shouldApply).toBe(true);
    expect(r.patch?.reach).toBe(1000);
  });
});
