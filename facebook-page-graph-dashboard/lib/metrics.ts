/**
 * Tính toán metric: engagement rate, post score (percentile),
 * topic aggregation, comment spike detection.
 */

import type { Topic } from "./topics";

export interface EngagementInput {
  reactions: number;
  comments: number;
  shares: number;
  clicks: number;
  reach: number | null | undefined;
}

/**
 * socialEngagementRate = (reactions + comments + shares) / reach
 *
 * KHÔNG include clicks — clicks là CTR, không phải social engagement.
 * Nếu reach <= 0 hoặc null → trả null.
 *
 * KHÔNG silently cap — caller xử lý warning riêng.
 */
export function calculateEngagementRate(input: EngagementInput): number | null {
  const { reactions, comments, shares, reach } = input;
  if (reach == null || reach <= 0) return null;
  const num = reactions + comments + shares;
  return num / reach;
}

/**
 * clickThroughRate = clicks / reach
 * Riêng biệt với socialEngagementRate.
 */
export function calculateCTR(input: { clicks: number; reach: number | null | undefined }): number | null {
  const { clicks, reach } = input;
  if (reach == null || reach <= 0) return null;
  return clicks / reach;
}

/**
 * totalActivity = reactions + comments + shares + clicks
 * (chỉ để tham khảo, không dùng tính ER)
 */
export function calculateTotalActivity(input: EngagementInput): number {
  return input.reactions + input.comments + input.shares + input.clicks;
}

/**
 * Helper: ER hợp lệ để tính score/aggregate — KHÔNG bao gồm ER null.
 * Cũng KHÔNG cap silent — caller xử lý warning riêng.
 */
export function isValidEngagementRate(er: number | null | undefined): er is number {
  return er != null && Number.isFinite(er) && er > 0;
}

/**
 * Tính percentile rank cho 1 giá trị trong mảng giá trị số.
 * (percentile = % phần tử có giá trị <= x)
 */
export function percentileRank(values: number[], x: number): number {
  if (values.length === 0) return 0;
  let count = 0;
  for (const v of values) if (v <= x) count++;
  return count / values.length;
}

export interface PostForScore {
  reach?: number | null;
  engagementRate?: number | null;
  commentsCount?: number | null;
  sharesCount?: number | null;
}

/**
 * Score chuẩn hóa percentile:
 *  reachPercentile * 0.35
 *  + engagementRatePercentile * 0.30
 *  + commentsPercentile * 0.20
 *  + sharesPercentile * 0.15
 *
 * Trả điểm 0..100. Trả NULL nếu:
 *  - population rỗng
 *  - post không có reach (reach=null/undefined) — không trộn metric
 *  - post không có engagementRate hợp lệ — không trộn metric
 *
 * QUAN TRỌNG (theo phản biện): KHÔNG silently thay reach=null → 0 hoặc
 * engagementRate=null → 0 trong score. Nếu post không có trueReach/ER,
 * trả null thay vì fake score thấp.
 */
export function calculatePostScore(
  post: PostForScore,
  population: PostForScore[],
): number | null {
  if (!population || population.length === 0) return null;

  // Loại post khỏi score nếu thiếu trueReach hoặc engagementRate hợp lệ.
  // Tránh trộn metric (post reach=null không được tính score reach-percentile).
  if (post.reach == null || !isValidEngagementRate(post.engagementRate)) {
    return null;
  }

  // Population cũng chỉ gồm post có đủ reach + ER (để percentile fair).
  const validPop = population.filter(
    (p) => p.reach != null && isValidEngagementRate(p.engagementRate),
  );
  if (validPop.length === 0) return null;

  const reachArr = validPop.map((p) => p.reach as number);
  const engArr = validPop.map((p) => p.engagementRate as number);
  const commentsArr = validPop.map((p) => p.commentsCount ?? 0);
  const sharesArr = validPop.map((p) => p.sharesCount ?? 0);

  const reach = post.reach;
  const eng = post.engagementRate as number;
  const comments = post.commentsCount ?? 0;
  const shares = post.sharesCount ?? 0;

  const reachP = percentileRank(reachArr, reach);
  const engP = percentileRank(engArr, eng);
  const commentsP = percentileRank(commentsArr, comments);
  const sharesP = percentileRank(sharesArr, shares);

  const score =
    reachP * 0.35 + engP * 0.3 + commentsP * 0.2 + sharesP * 0.15;
  return Math.round(score * 1000) / 10; // 0..100, 1 số thập phân
}

// ---------- Topic aggregation ----------

export interface TopicAggregate {
  topic: Topic | string;
  topicLabel: string;
  postsCount: number;
  reachTotal: number;
  commentsTotal: number;
  sharesTotal: number;
  engagementRateAvg: number | null;
  scoreAvg: number | null;
}

const TOPIC_LABEL_FALLBACK: Record<string, string> = {
  vi_mo: "Vĩ mô",
  chung_khoan: "Chứng khoán",
  lai_suat: "Lãi suất",
  bds: "BĐS",
  vang: "Vàng",
  khac: "Khác",
};

export function topicLabel(topic: string): string {
  return TOPIC_LABEL_FALLBACK[topic] ?? topic;
}

export interface PostAggregate {
  topic: string;
  reach?: number | null;
  commentsCount?: number | null;
  sharesCount?: number | null;
  engagementRate?: number | null;
  score?: number | null;
}

export function aggregateByTopic(posts: PostAggregate[]): TopicAggregate[] {
  const buckets: Record<string, PostAggregate[]> = {};
  for (const p of posts) {
    const key = p.topic || "khac";
    if (!buckets[key]) buckets[key] = [];
    buckets[key].push(p);
  }
  const out: TopicAggregate[] = [];
  for (const [topic, arr] of Object.entries(buckets)) {
    const reachTotal = arr.reduce((s, p) => s + (p.reach ?? 0), 0);
    const commentsTotal = arr.reduce((s, p) => s + (p.commentsCount ?? 0), 0);
    const sharesTotal = arr.reduce((s, p) => s + (p.sharesCount ?? 0), 0);
    const engList = arr.map((p) => p.engagementRate).filter((v): v is number => v != null && Number.isFinite(v));
    const scoreList = arr.map((p) => p.score).filter((v): v is number => v != null && Number.isFinite(v));
    out.push({
      topic,
      topicLabel: topicLabel(topic),
      postsCount: arr.length,
      reachTotal,
      commentsTotal,
      sharesTotal,
      engagementRateAvg: engList.length ? engList.reduce((a, b) => a + b, 0) / engList.length : null,
      scoreAvg: scoreList.length ? scoreList.reduce((a, b) => a + b, 0) / scoreList.length : null,
    });
  }
  out.sort((a, b) => b.reachTotal - a.reachTotal);
  return out;
}

// ---------- Comment spike detection ----------

export interface PostForSpike {
  fbPostId?: string;
  commentsCount: number;
  message?: string | null;
}

export interface SpikeResult {
  fbPostId: string;
  commentsCount: number;
  median: number;
  message?: string | null;
}

function median(values: number[]): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

/**
 * MVP rule:
 *  commentsCount >= COMMENT_SPIKE_MIN_COUNT
 *  && commentsCount > median(comments) * COMMENT_SPIKE_RATIO
 */
export function detectCommentSpike(posts: PostForSpike[]): SpikeResult[] {
  const minCount = Number(process.env.COMMENT_SPIKE_MIN_COUNT ?? 20);
  const ratio = Number(process.env.COMMENT_SPIKE_RATIO ?? 3);
  if (!posts || posts.length === 0) return [];
  const med = median(posts.map((p) => p.commentsCount ?? 0));
  const threshold = med * ratio;
  return posts
    .filter((p) => (p.commentsCount ?? 0) >= minCount && (p.commentsCount ?? 0) > threshold)
    .map((p) => ({
      fbPostId: p.fbPostId ?? "",
      commentsCount: p.commentsCount ?? 0,
      median: med,
      message: p.message ?? null,
    }));
}
