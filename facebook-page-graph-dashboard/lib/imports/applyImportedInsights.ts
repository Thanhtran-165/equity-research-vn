/**
 * Apply imported insights vào Post records trong DB.
 *
 * Quy tắc overwrite:
 * 1. Không overwrite facebook_graph_api_insights mới hơn nếu có.
 * 2. Nếu current metricSource là facebook_public_metrics/public_engagement_proxy → CSV được ưu tiên.
 * 3. Nếu current metricSource là facebook_video_metric → CSV reach/impressions được thêm,
 *    nhưng videoViews chỉ overwrite nếu user chọn.
 * 4. Duplicate fileHash → cảnh báo, không import lại mặc định.
 * 5. Có option "force re-import".
 */
import { calculateEngagementRate } from "@/lib/metrics";
import type { NormalizedRow } from "./normalizeRows";
import type { MatchResult } from "./matchPosts";

export interface ApplyInput {
  row: NormalizedRow;
  match: MatchResult;
  /** metricSource hiện tại của post trong DB */
  currentMetricSource: string | null;
  /** videoViews hiện tại (nếu có) — để quyết định có overwrite không */
  currentVideoViews?: number | null;
  /** Force overwrite kể cả khi current là facebook_graph_api_insights */
  forceOverwrite?: boolean;
  /** Có cho phép overwrite videoViews không */
  allowVideoViewsOverwrite?: boolean;
}

export interface ApplyResult {
  shouldApply: boolean;
  reason: string;
  patch: {
    reach?: number | null;
    impressions?: number | null;
    clicks?: number | null;
    engagedUsers?: number | null;
    videoViews?: number | null;
    metricSource: string;
    engagementRate?: number | null;
  } | null;
}

/**
 * Quyết định có apply metric từ CSV hay không + build patch.
 */
export function applyImportedInsights(input: ApplyInput): ApplyResult {
  const { row, match, currentMetricSource, forceOverwrite, allowVideoViewsOverwrite } = input;

  if (match.status !== "matched" || !match.matchedPostId) {
    return { shouldApply: false, reason: `match.status = ${match.status}`, patch: null };
  }

  // Rule 1: không overwrite facebook_graph_api_insights (trừ khi force)
  if (currentMetricSource === "facebook_graph_api_insights" && !forceOverwrite) {
    return {
      shouldApply: false,
      reason: "current metricSource = facebook_graph_api_insights (ưu tiên hơn CSV). Dùng --force để overwrite.",
      patch: null,
    };
  }

  const patch: ApplyResult["patch"] = {
    metricSource: "meta_business_suite_csv",
  };

  // Reach từ CSV là insight thật → set vào cột reach
  if (row.reach != null) {
    patch.reach = row.reach;
  }
  if (row.impressions != null) {
    patch.impressions = row.impressions;
  }
  if (row.clicks != null) {
    patch.clicks = row.clicks;
  }
  if (row.engagedUsers != null) {
    patch.engagedUsers = row.engagedUsers;
  }

  // videoViews: chỉ overwrite nếu user chọn, ngược lại giữ value cũ
  if (row.videoViews != null && allowVideoViewsOverwrite) {
    patch.videoViews = row.videoViews;
  } else if (row.videoViews != null && currentMetricSource === "facebook_video_metric" && !allowVideoViewsOverwrite) {
    // Giữ videoViews cũ — không overwrite
  } else if (row.videoViews != null && currentMetricSource !== "facebook_video_metric") {
    // Post không phải video_metric → an toàn set
    patch.videoViews = row.videoViews;
  }

  // Engagement rate chỉ tính khi reach > 0 (CSV reach = insight thật)
  if (patch.reach != null && patch.reach > 0) {
    const er = calculateEngagementRate({
      reactions: row.reactions ?? 0,
      comments: row.comments ?? 0,
      shares: row.shares ?? 0,
      clicks: row.clicks ?? 0,
      reach: patch.reach,
    });
    patch.engagementRate = er;
  }

  return {
    shouldApply: true,
    reason: "applied meta_business_suite_csv insights",
    patch,
  };
}
