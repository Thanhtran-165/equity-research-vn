/**
 * Public Metrics — comparable engagement, observed engagement, coverage, ratios.
 *
 * Key principle: missing metric = null (NOT zero).
 * Only treat as zero when explicitly observed as zero.
 */

export interface PublicPostMetrics {
  reactions: number | null;
  comments: number | null;
  shares: number | null;
  publicVideoViews: number | null;
  reactionsObserved: boolean;
  commentsObserved: boolean;
  sharesObserved: boolean;
  publicVideoViewsObserved: boolean;
}

/**
 * comparableEngagement = reactions + comments
 * Only when both reactions and comments are observed (not null).
 */
export function calculateComparableEngagement(m: PublicPostMetrics): number | null {
  if (!m.reactionsObserved || !m.commentsObserved) return null;
  if (m.reactions == null || m.comments == null) return null;
  return m.reactions + m.comments;
}

/**
 * observedPublicEngagement = reactions + comments + shares (if observed)
 * Returns null if reactions or comments missing.
 * Includes shares only if sharesObserved=true.
 */
export function calculateObservedPublicEngagement(m: PublicPostMetrics): number | null {
  const base = calculateComparableEngagement(m);
  if (base == null) return null;
  if (m.sharesObserved && m.shares != null) return base + m.shares;
  return base;
}

/**
 * metricCoverageScore: how complete is the observation?
 * reactions: 0.35, comments: 0.35, shares: 0.20, video views: 0.10
 */
export function calculateMetricCoverageScore(m: PublicPostMetrics): number {
  let score = 0;
  if (m.reactionsObserved) score += 0.35;
  if (m.commentsObserved) score += 0.35;
  if (m.sharesObserved) score += 0.20;
  if (m.publicVideoViewsObserved) score += 0.10;
  return score;
}

/**
 * shareRatio = shares / observedPublicEngagement
 * Only if sharesObserved and denominator > 0.
 */
export function calculateShareRatio(m: PublicPostMetrics): number | null {
  if (!m.sharesObserved || m.shares == null) return null;
  const eng = calculateObservedPublicEngagement(m);
  if (eng == null || eng <= 0) return null;
  return m.shares / eng;
}

/**
 * commentRatio = comments / comparableEngagement
 * Only if comparableEngagement > 0.
 */
export function calculateCommentRatio(m: PublicPostMetrics): number | null {
  const comp = calculateComparableEngagement(m);
  if (comp == null || comp <= 0) return null;
  if (m.comments == null) return null;
  return m.comments / comp;
}

/**
 * Compute metrics for a post from raw input values.
 * Blank = null, "0" = observed zero.
 */
export function derivePostMetrics(input: {
  reactions?: string | number | null;
  comments?: string | number | null;
  shares?: string | number | null;
  publicVideoViews?: string | number | null;
}): PublicPostMetrics & {
  comparableEngagement: number | null;
  observedPublicEngagement: number | null;
  metricCoverageScore: number;
} {
  const parseMetric = (v: string | number | null | undefined): { value: number | null; observed: boolean } => {
    if (v == null || (typeof v === "string" && v.trim() === "")) return { value: null, observed: false };
    const n = typeof v === "number" ? v : parseFloat(v);
    if (!Number.isFinite(n)) return { value: null, observed: false };
    return { value: n, observed: true };
  };

  const r = parseMetric(input.reactions);
  const c = parseMetric(input.comments);
  const s = parseMetric(input.shares);
  const v = parseMetric(input.publicVideoViews);

  const metrics: PublicPostMetrics = {
    reactions: r.value,
    comments: c.value,
    shares: s.value,
    publicVideoViews: v.value,
    reactionsObserved: r.observed,
    commentsObserved: c.observed,
    sharesObserved: s.observed,
    publicVideoViewsObserved: v.observed,
  };

  return {
    ...metrics,
    comparableEngagement: calculateComparableEngagement(metrics),
    observedPublicEngagement: calculateObservedPublicEngagement(metrics),
    metricCoverageScore: calculateMetricCoverageScore(metrics),
  };
}

/**
 * Median of an array (null-safe).
 */
export function median(values: (number | null)[]): number | null {
  const valid = values.filter((v): v is number => v != null && Number.isFinite(v));
  if (valid.length === 0) return null;
  const sorted = [...valid].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

/**
 * viralHitRate: posts with comparableEngagement >= 3 * median / total valid posts.
 * Requires minimum 5 valid posts.
 */
export function calculateViralHitRate(engagements: (number | null)[], multiplier = 3, minSample = 5): number | null {
  const valid = engagements.filter((v): v is number => v != null && Number.isFinite(v));
  if (valid.length < minSample) return null;
  const med = median(valid);
  if (med == null || med <= 0) return null;
  const viralCount = valid.filter((v) => v >= med * multiplier).length;
  return viralCount / valid.length;
}

/**
 * engagementPerFollower = totalComparableEngagement / followers
 * Only when audienceCountType = "followers" and followers > 0.
 */
export function calculateEngagementPerFollower(
  totalComparableEngagement: number | null,
  audienceCount: number | null,
  audienceCountType: string | null,
): number | null {
  if (audienceCountType !== "followers") return null;
  if (!audienceCount || audienceCount <= 0) return null;
  if (totalComparableEngagement == null) return null;
  return totalComparableEngagement / audienceCount;
}

/**
 * Check if a BenchmarkPage qualifies for direct leaderboard.
 */
export function isLeaderboardEligible(objectType: string, benchmarkRole: string, isOwnPage: boolean): boolean {
  if (isOwnPage) return objectType === "facebook_page";
  return objectType === "facebook_page" && benchmarkRole === "core_peer";
}
