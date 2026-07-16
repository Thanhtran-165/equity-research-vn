/**
 * Internal Benchmark — phân tích pattern từ chính bài viết của Page.
 *
 * Mục tiêu: biết "bài tốt" của Page này trông như thế nào — để:
 * 1. Đánh giá bài mới so với baseline nội bộ.
 * 2. Chuẩn bị cho so sánh với competitor.
 *
 * Metric phân tích:
 * - Median / top-25% / top-10% / best theo từng metric (reach, reactions, comments, shares, ER)
 * - Phân tích theo topic (nếu có)
 * - Phân tích theo post type (video, photo, text)
 * - Phân tích theo ngày trong tuần / giờ đăng
 * - Correlation giữa các metric
 */

export interface InternalPostData {
  fbPostId: string;
  message: string | null;
  topic: string;
  postType: string;
  createdTime: string | null;
  reach: number | null;
  impressions: number | null;
  reactionsCount: number;
  commentsCount: number;
  sharesCount: number;
  clicks: number | null;
  videoViews: number | null;
  engagementRate: number | null;
  metricSource: string | null;
}

export interface PercentileStats {
  count: number;
  min: number;
  median: number;
  mean: number;
  p25: number; // top 75%
  p75: number; // top 25%
  p90: number; // top 10%
  max: number;
}

export interface InternalBenchmark {
  totalPosts: number;
  dateRange: { min: string | null; max: string | null };
  // Stats toàn page
  reach: PercentileStats | null;
  reactions: PercentileStats | null;
  comments: PercentileStats | null;
  shares: PercentileStats | null;
  engagementRate: PercentileStats | null;
  videoViews: PercentileStats | null;
  // Phân tích theo topic
  byTopic: TopicBenchmark[];
  // Phân tích theo post type
  byType: TypeBenchmark[];
  // Phân tích theo ngày trong tuần
  byWeekday: WeekdayBenchmark[];
  // Phân tích theo giờ đăng
  byHour: HourBenchmark[];
  // Correlation
  correlations: {
    reachVsReactions: number | null;
    reachVsComments: number | null;
    reachVsShares: number | null;
    reactionsVsComments: number | null;
  };
  // Top posts mẫu
  topReachPosts: InternalPostData[];
  topERPosts: InternalPostData[];
  topCommentPosts: InternalPostData[];
  // Insights text (Vietnamese)
  insights: string[];
}

export interface TopicBenchmark {
  topic: string;
  topicLabel: string;
  postCount: number;
  avgReach: number | null;
  avgReactions: number;
  avgComments: number;
  avgShares: number;
  avgER: number | null;
  totalReach: number;
}

export interface TypeBenchmark {
  postType: string;
  postCount: number;
  avgReach: number | null;
  avgReactions: number;
  avgComments: number;
  avgER: number | null;
}

export interface WeekdayBenchmark {
  weekday: number; // 0=Sun, 1=Mon, ... 6=Sat
  weekdayLabel: string;
  postCount: number;
  avgReach: number | null;
  avgER: number | null;
}

export interface HourBenchmark {
  hourBucket: string; // "0-5", "6-11", "12-17", "18-23"
  postCount: number;
  avgReach: number | null;
  avgER: number | null;
}

const TOPIC_LABELS: Record<string, string> = {
  vi_mo: "Vĩ mô",
  chung_khoan: "Chứng khoán",
  lai_suat: "Lãi suất",
  bds: "BĐS",
  vang: "Vàng",
  khac: "Khác",
  influencer_tai_chinh: "Influencer",
};

const WEEKDAY_LABELS = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"];

function calcPercentiles(values: number[]): PercentileStats | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const n = sorted.length;
  const percentile = (p: number) => {
    const idx = Math.min(n - 1, Math.max(0, Math.ceil(p * n) - 1));
    return sorted[idx];
  };
  return {
    count: n,
    min: sorted[0],
    median: percentile(0.5),
    mean: sorted.reduce((a, b) => a + b, 0) / n,
    p25: percentile(0.25),
    p75: percentile(0.75),
    p90: percentile(0.9),
    max: sorted[n - 1],
  };
}

function pearsonCorrelation(xs: number[], ys: number[]): number | null {
  if (xs.length !== ys.length || xs.length < 3) return null;
  const n = xs.length;
  const mx = xs.reduce((a, b) => a + b, 0) / n;
  const my = ys.reduce((a, b) => a + b, 0) / n;
  let num = 0;
  let dx = 0;
  let dy = 0;
  for (let i = 0; i < n; i++) {
    num += (xs[i] - mx) * (ys[i] - my);
    dx += (xs[i] - mx) ** 2;
    dy += (ys[i] - my) ** 2;
  }
  const denom = Math.sqrt(dx * dy);
  if (denom === 0) return null;
  return num / denom;
}

export function computeInternalBenchmark(posts: InternalPostData[]): InternalBenchmark | null {
  if (!posts || posts.length === 0) return null;

  // Date range
  const dated = posts.filter((p) => p.createdTime);
  const dateRange = {
    min: dated.length ? dated.reduce((a, b) => (a.createdTime! < b.createdTime! ? a : b)).createdTime : null,
    max: dated.length ? dated.reduce((a, b) => (a.createdTime! > b.createdTime! ? a : b)).createdTime : null,
  };

  // Overall stats
  const reachStats = calcPercentiles(posts.filter((p) => p.reach != null).map((p) => p.reach!));
  const reactionStats = calcPercentiles(posts.map((p) => p.reactionsCount));
  const commentStats = calcPercentiles(posts.map((p) => p.commentsCount));
  const shareStats = calcPercentiles(posts.map((p) => p.sharesCount));
  const erStats = calcPercentiles(posts.filter((p) => p.engagementRate != null && p.engagementRate > 0 && p.engagementRate < 5).map((p) => p.engagementRate!));
  const videoStats = calcPercentiles(posts.filter((p) => p.videoViews != null).map((p) => p.videoViews!));

  // By topic
  const topicMap: Record<string, InternalPostData[]> = {};
  for (const p of posts) {
    const t = p.topic || "khac";
    if (!topicMap[t]) topicMap[t] = [];
    topicMap[t].push(p);
  }
  const byTopic: TopicBenchmark[] = Object.entries(topicMap).map(([topic, arr]) => {
    const reachArr = arr.filter((p) => p.reach != null).map((p) => p.reach!);
    const erArr = arr.filter((p) => p.engagementRate != null && p.engagementRate > 0 && p.engagementRate < 5).map((p) => p.engagementRate!);
    return {
      topic,
      topicLabel: TOPIC_LABELS[topic] ?? topic,
      postCount: arr.length,
      avgReach: reachArr.length ? reachArr.reduce((a, b) => a + b, 0) / reachArr.length : null,
      avgReactions: arr.reduce((a, b) => a + b.reactionsCount, 0) / arr.length,
      avgComments: arr.reduce((a, b) => a + b.commentsCount, 0) / arr.length,
      avgShares: arr.reduce((a, b) => a + b.sharesCount, 0) / arr.length,
      avgER: erArr.length ? erArr.reduce((a, b) => a + b, 0) / erArr.length : null,
      totalReach: reachArr.reduce((a, b) => a + b, 0),
    };
  }).sort((a, b) => (b.avgReach ?? 0) - (a.avgReach ?? 0));

  // By post type
  const typeMap: Record<string, InternalPostData[]> = {};
  for (const p of posts) {
    const t = p.postType || "unknown";
    if (!typeMap[t]) typeMap[t] = [];
    typeMap[t].push(p);
  }
  const byType: TypeBenchmark[] = Object.entries(typeMap).map(([type, arr]) => {
    const reachArr = arr.filter((p) => p.reach != null).map((p) => p.reach!);
    const erArr = arr.filter((p) => p.engagementRate != null && p.engagementRate > 0 && p.engagementRate < 5).map((p) => p.engagementRate!);
    return {
      postType: type,
      postCount: arr.length,
      avgReach: reachArr.length ? reachArr.reduce((a, b) => a + b, 0) / reachArr.length : null,
      avgReactions: arr.reduce((a, b) => a + b.reactionsCount, 0) / arr.length,
      avgComments: arr.reduce((a, b) => a + b.commentsCount, 0) / arr.length,
      avgER: erArr.length ? erArr.reduce((a, b) => a + b, 0) / erArr.length : null,
    };
  }).sort((a, b) => (b.avgReach ?? 0) - (a.avgReach ?? 0));

  // By weekday
  const weekdayMap: Record<number, InternalPostData[]> = {};
  for (const p of posts) {
    if (!p.createdTime) continue;
    const d = new Date(p.createdTime);
    if (isNaN(d.getTime())) continue;
    const wd = d.getDay();
    if (!weekdayMap[wd]) weekdayMap[wd] = [];
    weekdayMap[wd].push(p);
  }
  const byWeekday: WeekdayBenchmark[] = Array.from({ length: 7 }, (_, i) => {
    const arr = weekdayMap[i] ?? [];
    const reachArr = arr.filter((p) => p.reach != null).map((p) => p.reach!);
    const erArr = arr.filter((p) => p.engagementRate != null && p.engagementRate > 0 && p.engagementRate < 5).map((p) => p.engagementRate!);
    return {
      weekday: i,
      weekdayLabel: WEEKDAY_LABELS[i],
      postCount: arr.length,
      avgReach: reachArr.length ? reachArr.reduce((a, b) => a + b, 0) / reachArr.length : null,
      avgER: erArr.length ? erArr.reduce((a, b) => a + b, 0) / erArr.length : null,
    };
  });

  // By hour bucket
  const hourBuckets = ["0-5 (đêm)", "6-11 (sáng)", "12-17 (chiều)", "18-23 (tối)"];
  const hourMap: Record<string, InternalPostData[]> = {};
  for (const p of posts) {
    if (!p.createdTime) continue;
    const d = new Date(p.createdTime);
    if (isNaN(d.getTime())) continue;
    const h = d.getHours();
    const bucket = h < 6 ? hourBuckets[0] : h < 12 ? hourBuckets[1] : h < 18 ? hourBuckets[2] : hourBuckets[3];
    if (!hourMap[bucket]) hourMap[bucket] = [];
    hourMap[bucket].push(p);
  }
  const byHour: HourBenchmark[] = hourBuckets.map((bucket) => {
    const arr = hourMap[bucket] ?? [];
    const reachArr = arr.filter((p) => p.reach != null).map((p) => p.reach!);
    const erArr = arr.filter((p) => p.engagementRate != null && p.engagementRate > 0 && p.engagementRate < 5).map((p) => p.engagementRate!);
    return {
      hourBucket: bucket,
      postCount: arr.length,
      avgReach: reachArr.length ? reachArr.reduce((a, b) => a + b, 0) / reachArr.length : null,
      avgER: erArr.length ? erArr.reduce((a, b) => a + b, 0) / erArr.length : null,
    };
  });

  // Correlations
  const reachPairs = posts.filter((p) => p.reach != null && p.reach > 0);
  const correlations = {
    reachVsReactions: pearsonCorrelation(reachPairs.map((p) => p.reach!), reachPairs.map((p) => p.reactionsCount)),
    reachVsComments: pearsonCorrelation(reachPairs.map((p) => p.reach!), reachPairs.map((p) => p.commentsCount)),
    reachVsShares: pearsonCorrelation(reachPairs.map((p) => p.reach!), reachPairs.map((p) => p.sharesCount)),
    reactionsVsComments: pearsonCorrelation(posts.map((p) => p.reactionsCount), posts.map((p) => p.commentsCount)),
  };

  // Top posts
  const topReachPosts = [...posts]
    .filter((p) => p.reach != null)
    .sort((a, b) => b.reach! - a.reach!)
    .slice(0, 10);
  const topERPosts = [...posts]
    .filter((p) => p.engagementRate != null && p.engagementRate > 0 && p.engagementRate < 3)
    .sort((a, b) => b.engagementRate! - a.engagementRate!)
    .slice(0, 10);
  const topCommentPosts = [...posts]
    .sort((a, b) => b.commentsCount - a.commentsCount)
    .slice(0, 10);

  // Insights text
  const insights: string[] = [];
  if (reachStats) {
    insights.push(`Reach trung bình: ${Math.round(reachStats.mean).toLocaleString("vi-VN")} | Median: ${reachStats.median.toLocaleString("vi-VN")} | Top 10%: ${reachStats.p90.toLocaleString("vi-VN")} | Best: ${reachStats.max.toLocaleString("vi-VN")}.`);
  }
  if (byTopic.length > 1) {
    const best = byTopic[0];
    const worst = byTopic[byTopic.length - 1];
    insights.push(`Chủ đề reach cao nhất: ${best.topicLabel} (${Math.round(best.avgReach ?? 0).toLocaleString("vi-VN")}). Thấp nhất: ${worst.topicLabel} (${Math.round(worst.avgReach ?? 0).toLocaleString("vi-VN")}).`);
  }
  if (byType.length > 1) {
    const best = byType[0];
    insights.push(`Loại bài reach cao nhất: ${best.postType} (avg ${Math.round(best.avgReach ?? 0).toLocaleString("vi-VN")}).`);
  }
  // Best weekday
  const bestWeekday = [...byWeekday].filter((w) => w.avgReach != null).sort((a, b) => b.avgReach! - a.avgReach!);
  if (bestWeekday.length > 0 && bestWeekday[0].avgReach != null) {
    insights.push(`Ngày đăng reach cao nhất: ${bestWeekday[0].weekdayLabel} (avg ${Math.round(bestWeekday[0].avgReach!).toLocaleString("vi-VN")}).`);
  }
  // Best hour
  const bestHour = [...byHour].filter((h) => h.avgReach != null).sort((a, b) => b.avgReach! - a.avgReach!);
  if (bestHour.length > 0 && bestHour[0].avgReach != null) {
    insights.push(`Khung giờ đăng reach cao nhất: ${bestHour[0].hourBucket} (avg ${Math.round(bestHour[0].avgReach!).toLocaleString("vi-VN")}).`);
  }
  // Correlation insight
  if (correlations.reachVsShares != null) {
    if (correlations.reachVsShares > 0.7) {
      insights.push(`Tương quan mạnh giữa reach và shares (r=${correlations.reachVsShares.toFixed(2)}) — share là driver chính của reach.`);
    } else if (correlations.reachVsReactions != null && correlations.reachVsReactions > 0.7) {
      insights.push(`Tương quan mạnh giữa reach và reactions (r=${correlations.reachVsReactions.toFixed(2)}) — reaction là driver chính.`);
    }
  }

  return {
    totalPosts: posts.length,
    dateRange,
    reach: reachStats,
    reactions: reactionStats,
    comments: commentStats,
    shares: shareStats,
    engagementRate: erStats,
    videoViews: videoStats,
    byTopic,
    byType,
    byWeekday,
    byHour,
    correlations,
    topReachPosts,
    topERPosts,
    topCommentPosts,
    insights,
  };
}
