/**
 * Page-level reporting helpers — aggregates Post data for monthly/weekly reports.
 */
import { calculateEngagementRate, calculateCTR } from "@/lib/metrics";
import { isTrueReachSource } from "@/lib/metricSource";

export interface PostReportRow {
  fbPostId: string;
  message: string | null;
  topic: string;
  postType: string;
  createdTime: string | null;
  permalinkUrl: string | null;
  reach: number | null;
  reactionsCount: number;
  commentsCount: number;
  sharesCount: number;
  clicks: number | null;
  engagementRate: number | null;
  metricSource?: string | null;
}

export interface PageSummary {
  totalPosts: number;
  totalReach: number;
  totalReactions: number;
  totalComments: number;
  totalShares: number;
  totalClicks: number;
  avgER: number | null;
  avgCTR: number | null;
}

export function computePageSummary(posts: PostReportRow[]): PageSummary {
  // Only compute ER/CTR from true-reach sources (facebook_graph_api_insights, meta_business_suite_csv)
  const trueReachPosts = posts.filter((p) => isTrueReachSource((p as any).metricSource) && p.reach != null && p.reach > 0);
  const withReach = posts.filter((p) => p.reach != null && p.reach > 0);
  const totalReach = withReach.reduce((s, p) => s + (p.reach ?? 0), 0);
  const totalReactions = posts.reduce((s, p) => s + p.reactionsCount, 0);
  const totalComments = posts.reduce((s, p) => s + p.commentsCount, 0);
  const totalShares = posts.reduce((s, p) => s + p.sharesCount, 0);
  const totalClicks = posts.reduce((s, p) => s + (p.clicks ?? 0), 0);

  const erValues = trueReachPosts.map((p) => calculateEngagementRate({
    reactions: p.reactionsCount, comments: p.commentsCount, shares: p.sharesCount, clicks: p.clicks ?? 0, reach: p.reach,
  })).filter((v): v is number => v != null);
  const ctrValues = trueReachPosts.map((p) => calculateCTR({ clicks: p.clicks ?? 0, reach: p.reach })).filter((v): v is number => v != null);

  return {
    totalPosts: posts.length,
    totalReach,
    totalReactions,
    totalComments,
    totalShares,
    totalClicks,
    avgER: erValues.length ? erValues.reduce((a, b) => a + b, 0) / erValues.length : null,
    avgCTR: ctrValues.length ? ctrValues.reduce((a, b) => a + b, 0) / ctrValues.length : null,
  };
}

export interface TopPost {
  fbPostId: string;
  message: string | null;
  permalinkUrl: string | null;
  topic: string;
  reach: number;
  reactions: number;
  comments: number;
  shares: number;
  clicks: number;
  er: number | null;
  ctr: number | null;
}

export function topPostsByReach(posts: PostReportRow[], limit = 20): TopPost[] {
  return posts
    .filter((p) => p.reach != null && p.reach > 0)
    .sort((a, b) => (b.reach ?? 0) - (a.reach ?? 0))
    .slice(0, limit)
    .map(toTopPost);
}

export function topPostsByER(posts: PostReportRow[], minReach = 500, limit = 20): TopPost[] {
  return posts
    .filter((p) => p.reach != null && p.reach >= minReach)
    .map((p) => {
      const er = calculateEngagementRate({
        reactions: p.reactionsCount, comments: p.commentsCount, shares: p.sharesCount, clicks: p.clicks ?? 0, reach: p.reach,
      });
      return { ...toTopPost(p), er };
    })
    .filter((p) => p.er != null)
    .sort((a, b) => (b.er ?? 0) - (a.er ?? 0))
    .slice(0, limit);
}

export function topPostsByCTR(posts: PostReportRow[], minReach = 500, limit = 20): TopPost[] {
  return posts
    .filter((p) => p.reach != null && p.reach >= minReach && p.clicks != null && p.clicks > 0)
    .map((p) => {
      const ctr = calculateCTR({ clicks: p.clicks ?? 0, reach: p.reach });
      return { ...toTopPost(p), ctr };
    })
    .filter((p) => p.ctr != null)
    .sort((a, b) => (b.ctr ?? 0) - (a.ctr ?? 0))
    .slice(0, limit);
}

export function topPostsByComments(posts: PostReportRow[], limit = 20): TopPost[] {
  return posts.sort((a, b) => b.commentsCount - a.commentsCount).slice(0, limit).map(toTopPost);
}

export function topPostsByShares(posts: PostReportRow[], limit = 20): TopPost[] {
  return posts.sort((a, b) => b.sharesCount - a.sharesCount).slice(0, limit).map(toTopPost);
}

function toTopPost(p: PostReportRow): TopPost {
  const er = calculateEngagementRate({
    reactions: p.reactionsCount, comments: p.commentsCount, shares: p.sharesCount, clicks: p.clicks ?? 0, reach: p.reach,
  });
  const ctr = calculateCTR({ clicks: p.clicks ?? 0, reach: p.reach });
  return {
    fbPostId: p.fbPostId,
    message: p.message,
    permalinkUrl: p.permalinkUrl,
    topic: p.topic,
    reach: p.reach ?? 0,
    reactions: p.reactionsCount,
    comments: p.commentsCount,
    shares: p.sharesCount,
    clicks: p.clicks ?? 0,
    er,
    ctr,
  };
}

export interface PostSpike {
  date: string;
  totalReach: number;
  totalComments: number;
  reason: string;
}

export function detectPostSpikes(posts: PostReportRow[]): PostSpike[] {
  // Group by date
  const byDate: Record<string, PostReportRow[]> = {};
  for (const p of posts) {
    if (!p.createdTime) continue;
    const d = p.createdTime.slice(0, 10);
    if (!byDate[d]) byDate[d] = [];
    byDate[d].push(p);
  }

  const daily = Object.entries(byDate).map(([date, arr]) => ({
    date,
    totalReach: arr.reduce((s, p) => s + (p.reach ?? 0), 0),
    totalComments: arr.reduce((s, p) => s + p.commentsCount, 0),
    posts: arr.length,
  }));

  if (daily.length < 3) return [];

  const reachValues = daily.map((d) => d.totalReach).sort((a, b) => a - b);
  const median = reachValues[Math.floor(reachValues.length / 2)] || 0;
  const threshold = median * 3;

  return daily
    .filter((d) => d.totalReach >= threshold && d.totalReach > 0)
    .map((d) => ({
      date: d.date,
      totalReach: d.totalReach,
      totalComments: d.totalComments,
      reason: `Reach ${d.totalReach.toLocaleString("vi-VN")} vs median ${median.toLocaleString("vi-VN")} (${d.posts} posts)`,
    }));
}
