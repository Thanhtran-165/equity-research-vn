/**
 * Logic gán metricSource — tách ra pure function để testable.
 *
 * Nguyên tắc (theo spec user phê duyệt):
 * - metricSource dựa trên SỰ TỒN TẠI của dữ liệu, không phải giá trị > 0.
 * - Một post có 0 reactions/cmt/shares nhưng API trả field hợp lệ
 *   vẫn là facebook_public_metrics.
 * - Ưu tiên: insights > video_metric > public_metrics > unavailable.
 */

export type MetricSource =
  | "facebook_graph_api_insights"
  | "facebook_video_metric"
  | "facebook_public_metrics"
  | "public_engagement_proxy" // deprecated alias (backward-compat only)
  | "meta_business_suite_csv" // manually imported from Meta Business Suite export
  | "unavailable";

export interface PostInsightsInput {
  /** True reach từ post_impressions_unique. NULL nếu API không trả. */
  reach?: number | null;
  /** Video views từ post_video_views. NULL nếu API không trả (không phải video post). */
  videoViews?: number | null;
  /** Reactions + comments + shares. NULL nếu không lấy được field summary. */
  publicEngagement?: number | null;
}

/**
 * Xác định metricSource cho 1 post dựa trên sự tồn tại của các metric.
 * KHÔNG dùng giá trị > 0 làm điều kiện.
 */
export function determineMetricSource(ins: PostInsightsInput): MetricSource {
  if (ins.reach != null) {
    return "facebook_graph_api_insights";
  }
  if (ins.videoViews != null) {
    return "facebook_video_metric";
  }
  if (ins.publicEngagement != null) {
    return "facebook_public_metrics";
  }
  return "unavailable";
}

/**
 * Helper backward-compat: gộp các giá trị cũ vào chuẩn mới.
 * - "public_engagement_proxy" → treat như "facebook_public_metrics"
 */
export function isPublicMetrics(source: string | null | undefined): boolean {
  return source === "facebook_public_metrics" || source === "public_engagement_proxy";
}

/**
 * Normalize bất kỳ metricSource nào (kể cả legacy) về chuẩn mới.
 */
export function normalizeMetricSource(source: string | null | undefined): MetricSource {
  if (source === "facebook_graph_api_insights") return "facebook_graph_api_insights";
  if (source === "facebook_video_metric") return "facebook_video_metric";
  if (source === "public_engagement_proxy") return "facebook_public_metrics"; // gộp
  if (source === "facebook_public_metrics") return "facebook_public_metrics";
  if (source === "meta_business_suite_csv") return "meta_business_suite_csv";
  return "unavailable";
}

/**
 * Returns true if the source provides true reach data (post_impressions_unique).
 * ER (engagement rate) is only valid for these sources.
 */
export function isTrueReachSource(source: string | null | undefined): boolean {
  return source === "facebook_graph_api_insights" || source === "meta_business_suite_csv";
}
