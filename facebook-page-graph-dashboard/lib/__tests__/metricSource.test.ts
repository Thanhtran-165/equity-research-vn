import { describe, it, expect } from "vitest";
import {
  determineMetricSource,
  isPublicMetrics,
  normalizeMetricSource,
  isTrueReachSource,
} from "../metricSource";

// ============================================================
// determineMetricSource — 6 case bắt buộc theo spec user
// ============================================================
describe("determineMetricSource", () => {
  it("returns facebook_graph_api_insights when reach exists", () => {
    expect(determineMetricSource({ reach: 1000, videoViews: 100, publicEngagement: 50 }))
      .toBe("facebook_graph_api_insights");
  });

  it("returns facebook_graph_api_insights when reach = 0 (existence, not >0)", () => {
    // Spec user: "0 vẫn là facebook_public_metrics nếu API trả field hợp lệ"
    // → field reach trả về (kể cả 0) → insights, vì reach field tồn tại.
    expect(determineMetricSource({ reach: 0, videoViews: null, publicEngagement: 0 }))
      .toBe("facebook_graph_api_insights");
  });

  it("returns facebook_video_metric when videoViews exists but reach does NOT", () => {
    expect(determineMetricSource({ reach: null, videoViews: 100, publicEngagement: 50 }))
      .toBe("facebook_video_metric");
  });

  it("returns facebook_video_metric when videoViews = 0 (existence, not >0) — spec user", () => {
    // videoViews = 0 nhưng field có trả về → vẫn là video metric
    expect(determineMetricSource({ reach: null, videoViews: 0, publicEngagement: 0 }))
      .toBe("facebook_video_metric");
  });

  it("returns facebook_public_metrics when only publicEngagement exists (case spec user)", () => {
    // publicEngagement = 0 nhưng API trả field summary hợp lệ → vẫn là public_metrics
    expect(determineMetricSource({ reach: null, videoViews: null, publicEngagement: 0 }))
      .toBe("facebook_public_metrics");
  });

  it("returns facebook_public_metrics when publicEngagement > 0", () => {
    expect(determineMetricSource({ reach: null, videoViews: null, publicEngagement: 100 }))
      .toBe("facebook_public_metrics");
  });

  it("returns unavailable when ALL metrics are null", () => {
    expect(determineMetricSource({ reach: null, videoViews: null, publicEngagement: null }))
      .toBe("unavailable");
  });

  it("returns unavailable when all metrics are undefined", () => {
    expect(determineMetricSource({})).toBe("unavailable");
  });

  it("prioritizes insights > video_metric > public_metrics", () => {
    // Có cả 3 → phải là insights (ưu tiên cao nhất)
    expect(determineMetricSource({ reach: 100, videoViews: 200, publicEngagement: 50 }))
      .toBe("facebook_graph_api_insights");
  });

  it("prioritizes video_metric > public_metrics when no insights", () => {
    expect(determineMetricSource({ reach: null, videoViews: 200, publicEngagement: 50 }))
      .toBe("facebook_video_metric");
  });
});

// ============================================================
// isPublicMetrics — backward-compat
// ============================================================
describe("isPublicMetrics", () => {
  it("returns true for facebook_public_metrics", () => {
    expect(isPublicMetrics("facebook_public_metrics")).toBe(true);
  });

  it("returns true for legacy public_engagement_proxy", () => {
    expect(isPublicMetrics("public_engagement_proxy")).toBe(true);
  });

  it("returns false for facebook_graph_api_insights", () => {
    expect(isPublicMetrics("facebook_graph_api_insights")).toBe(false);
  });

  it("returns false for null", () => {
    expect(isPublicMetrics(null)).toBe(false);
  });

  it("returns false for undefined", () => {
    expect(isPublicMetrics(undefined)).toBe(false);
  });
});

// ============================================================
// normalizeMetricSource
// ============================================================
describe("normalizeMetricSource", () => {
  it("keeps facebook_graph_api_insights as-is", () => {
    expect(normalizeMetricSource("facebook_graph_api_insights"))
      .toBe("facebook_graph_api_insights");
  });

  it("converts legacy public_engagement_proxy → facebook_public_metrics", () => {
    // Spec user: "old metricSource public_engagement_proxy vẫn render được như facebook_public_metrics"
    expect(normalizeMetricSource("public_engagement_proxy"))
      .toBe("facebook_public_metrics");
  });

  it("keeps facebook_public_metrics as-is", () => {
    expect(normalizeMetricSource("facebook_public_metrics"))
      .toBe("facebook_public_metrics");
  });

  it("returns unavailable for null", () => {
    expect(normalizeMetricSource(null)).toBe("unavailable");
  });

  it("returns unavailable for unknown string", () => {
    expect(normalizeMetricSource("unknown_source")).toBe("unavailable");
  });
});

// ============================================================
// isTrueReachSource
// ============================================================
describe("isTrueReachSource", () => {
  it("returns true for facebook_graph_api_insights", () => {
    expect(isTrueReachSource("facebook_graph_api_insights")).toBe(true);
  });

  it("returns true for meta_business_suite_csv", () => {
    expect(isTrueReachSource("meta_business_suite_csv")).toBe(true);
  });

  it("returns false for facebook_video_metric", () => {
    expect(isTrueReachSource("facebook_video_metric")).toBe(false);
  });

  it("returns false for facebook_public_metrics", () => {
    expect(isTrueReachSource("facebook_public_metrics")).toBe(false);
  });

  it("returns false for public_engagement_proxy", () => {
    expect(isTrueReachSource("public_engagement_proxy")).toBe(false);
  });

  it("returns false for null/undefined", () => {
    expect(isTrueReachSource(null)).toBe(false);
    expect(isTrueReachSource(undefined)).toBe(false);
  });
});
