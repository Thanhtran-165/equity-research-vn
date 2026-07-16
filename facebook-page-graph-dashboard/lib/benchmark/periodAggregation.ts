/**
 * Period Aggregation — compute BenchmarkPeriodSnapshot from BenchmarkPost records.
 *
 * Computes median/avg engagement, viral hit rate, ratios, coverage,
 * and engagement-per-follower for a given period.
 */

import {
  median,
  calculateViralHitRate,
} from "./publicMetrics";

export interface PostForAggregation {
  reactions: number | null;
  comments: number | null;
  shares: number | null;
  publicVideoViews: number | null;
  reactionsObserved: boolean;
  commentsObserved: boolean;
  sharesObserved: boolean;
  publicVideoViewsObserved: boolean;
  comparableEngagement: number | null;
  observedPublicEngagement: number | null;
  metricCoverageScore: number | null;
}

export interface AggregatedPeriod {
  postsCaptured: number;
  postsWithReactions: number;
  postsWithComments: number;
  postsWithShares: number;
  postsWithVideoViews: number;
  totalReactions: number | null;
  totalComments: number | null;
  totalShares: number | null;
  totalPublicVideoViews: number | null;
  totalComparableEngagement: number | null;
  totalObservedPublicEngagement: number | null;
  medianComparableEngagementPerPost: number | null;
  avgComparableEngagementPerPost: number | null;
  medianObservedEngagementPerPost: number | null;
  engagementPerFollower: number | null;
  viralHitRate: number | null;
  shareRatio: number | null;
  commentRatio: number | null;
  metricCoverageScore: number | null;
}

function sumOrNull(values: (number | null)[]): number | null {
  const valid = values.filter((v): v is number => v != null && Number.isFinite(v));
  if (valid.length === 0) return null;
  return valid.reduce((a, b) => a + b, 0);
}

function avgOrNull(values: (number | null)[]): number | null {
  const valid = values.filter((v): v is number => v != null && Number.isFinite(v));
  if (valid.length === 0) return null;
  return valid.reduce((a, b) => a + b, 0) / valid.length;
}

/**
 * Aggregate posts into a period snapshot.
 * @param posts Array of posts within the period
 * @param audienceCount Follower/member count for engagement-per-follower
 * @param audienceCountType "followers" | "members" | "unknown"
 */
export function aggregatePostsToPeriod(
  posts: PostForAggregation[],
  audienceCount?: number | null,
  audienceCountType?: string | null,
): AggregatedPeriod {
  if (posts.length === 0) {
    return {
      postsCaptured: 0,
      postsWithReactions: 0,
      postsWithComments: 0,
      postsWithShares: 0,
      postsWithVideoViews: 0,
      totalReactions: null,
      totalComments: null,
      totalShares: null,
      totalPublicVideoViews: null,
      totalComparableEngagement: null,
      totalObservedPublicEngagement: null,
      medianComparableEngagementPerPost: null,
      avgComparableEngagementPerPost: null,
      medianObservedEngagementPerPost: null,
      engagementPerFollower: null,
      viralHitRate: null,
      shareRatio: null,
      commentRatio: null,
      metricCoverageScore: null,
    };
  }

  const comparableEngagements = posts.map((p) => p.comparableEngagement);
  const observedEngagements = posts.map((p) => p.observedPublicEngagement);
  const reactions = posts.map((p) => p.reactions);
  const comments = posts.map((p) => p.comments);
  const shares = posts.map((p) => p.shares);
  const videoViews = posts.map((p) => p.publicVideoViews);
  const coverageScores = posts.map((p) => p.metricCoverageScore);

  const totalComp = sumOrNull(comparableEngagements);
  const totalObs = sumOrNull(observedEngagements);
  const totalShares = sumOrNull(shares);
  const totalComments = sumOrNull(comments);

  // Share ratio = total shares / total observed engagement
  const shareRatio =
    totalShares != null && totalObs != null && totalObs > 0
      ? totalShares / totalObs
      : null;

  // Comment ratio = total comments / total comparable engagement
  const commentRatio =
    totalComments != null && totalComp != null && totalComp > 0
      ? totalComments / totalComp
      : null;

  // Engagement per follower = total comparable / followers
  let engagementPerFollower: number | null = null;
  if (
    audienceCountType === "followers" &&
    audienceCount != null &&
    audienceCount > 0 &&
    totalComp != null
  ) {
    engagementPerFollower = totalComp / audienceCount;
  }

  return {
    postsCaptured: posts.length,
    postsWithReactions: posts.filter((p) => p.reactionsObserved).length,
    postsWithComments: posts.filter((p) => p.commentsObserved).length,
    postsWithShares: posts.filter((p) => p.sharesObserved).length,
    postsWithVideoViews: posts.filter((p) => p.publicVideoViewsObserved).length,
    totalReactions: sumOrNull(reactions),
    totalComments,
    totalShares,
    totalPublicVideoViews: sumOrNull(videoViews),
    totalComparableEngagement: totalComp,
    totalObservedPublicEngagement: totalObs,
    medianComparableEngagementPerPost: median(comparableEngagements),
    avgComparableEngagementPerPost: avgOrNull(comparableEngagements),
    medianObservedEngagementPerPost: median(observedEngagements),
    engagementPerFollower,
    viralHitRate: calculateViralHitRate(comparableEngagements),
    shareRatio,
    commentRatio,
    metricCoverageScore: avgOrNull(coverageScores),
  };
}

/**
 * Compute period boundaries.
 * weekly: ISO week (Monday 00:00 → Sunday 23:59)
 * monthly: calendar month
 */
export function getPeriodBounds(
  date: Date,
  periodType: "weekly" | "monthly",
): { start: Date; end: Date } {
  if (periodType === "weekly") {
    const day = date.getDay(); // 0=Sun, 1=Mon
    const diff = day === 0 ? -6 : 1 - day; // Monday start
    const start = new Date(date);
    start.setDate(date.getDate() + diff);
    start.setHours(0, 0, 0, 0);
    const end = new Date(start);
    end.setDate(start.getDate() + 6);
    end.setHours(23, 59, 59, 999);
    return { start, end };
  }

  // monthly
  const start = new Date(date.getFullYear(), date.getMonth(), 1, 0, 0, 0, 0);
  const end = new Date(date.getFullYear(), date.getMonth() + 1, 0, 23, 59, 59, 999);
  return { start, end };
}
