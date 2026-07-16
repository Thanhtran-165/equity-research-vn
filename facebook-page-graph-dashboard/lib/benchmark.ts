/**
 * Competitor Benchmark - Public Proxy Metrics.
 *
 * Lưu ý quan trọng:
 * - KHÔNG dùng token của người dùng để cố đọc private insights (reach, impressions,
 *   engaged_users, clicks) của Page khác. Đó là dữ liệu riêng tư của đối thủ.
 * - Benchmark dùng các chỉ số CÔNG KHAI: followers, reactions, comments, shares,
 *   video views, post frequency.
 * - Đây là "proxy" engagement, KHÔNG thể so sánh trực tiếp với internal
 *   reach-based engagement rate.
 */

import { percentileRank } from "./metrics";
import { topicLabel } from "./metrics";

// ---------- Types ----------

export interface RawSnapshotInput {
  followers: number;
  postsCount: number;
  reactionsCount: number;
  commentsCount: number;
  sharesCount: number;
  videoViews?: number | null;
  topPostEngagement?: number | null;
  periodStart: string; // YYYY-MM-DD
  periodEnd: string; // YYYY-MM-DD
}

export interface DerivedSnapshot extends RawSnapshotInput {
  publicEngagement: number;
  publicEngagementPerPost: number | null;
  engagementPer1kFollowers: number | null;
  avgReactionsPerPost: number | null;
  avgCommentsPerPost: number | null;
  avgSharesPerPost: number | null;
  videoViewsPerFollower: number | null;
  commentIntensity: number | null;
  shareIntensity: number | null;
  postingFrequencyPerDay: number | null;
  benchmarkScore: number | null;
}

// ---------- Period helpers ----------

export function numberOfDays(periodStart: string, periodEnd: string): number {
  const a = new Date(periodStart).getTime();
  const b = new Date(periodEnd).getTime();
  if (Number.isNaN(a) || Number.isNaN(b)) return 0;
  const diff = Math.max(0, b - a);
  return Math.max(1, Math.round(diff / (24 * 60 * 60 * 1000)) + 1);
}

// ---------- Formulas ----------

export function calculatePublicEngagement(input: RawSnapshotInput): number {
  return input.reactionsCount + input.commentsCount + input.sharesCount;
}

export function calculateEngagementPer1kFollowers(
  input: RawSnapshotInput,
  publicEngagement?: number,
): number | null {
  if (input.followers <= 0) return null;
  const pe = publicEngagement ?? calculatePublicEngagement(input);
  return pe / input.followers * 1000;
}

export function calculatePublicEngagementPerPost(
  input: RawSnapshotInput,
  publicEngagement?: number,
): number | null {
  if (input.postsCount <= 0) return null;
  const pe = publicEngagement ?? calculatePublicEngagement(input);
  return pe / input.postsCount;
}

export function calculateAverageMetrics(input: RawSnapshotInput) {
  const { postsCount, followers, videoViews } = input;
  const publicEngagement = calculatePublicEngagement(input);
  const days = numberOfDays(input.periodStart, input.periodEnd);

  return {
    avgReactionsPerPost: postsCount > 0 ? input.reactionsCount / postsCount : null,
    avgCommentsPerPost: postsCount > 0 ? input.commentsCount / postsCount : null,
    avgSharesPerPost: postsCount > 0 ? input.sharesCount / postsCount : null,
    videoViewsPerFollower:
      followers > 0 && videoViews != null ? videoViews / followers : null,
    commentIntensity:
      publicEngagement > 0 ? input.commentsCount / publicEngagement : null,
    shareIntensity:
      publicEngagement > 0 ? input.sharesCount / publicEngagement : null,
    postingFrequencyPerDay: days > 0 ? postsCount / days : null,
  };
}

/**
 * Compute toàn bộ derived metrics cho một raw snapshot.
 */
export function deriveSnapshot(input: RawSnapshotInput): DerivedSnapshot {
  const publicEngagement = calculatePublicEngagement(input);
  return {
    ...input,
    publicEngagement,
    publicEngagementPerPost: calculatePublicEngagementPerPost(input, publicEngagement),
    engagementPer1kFollowers: calculateEngagementPer1kFollowers(input, publicEngagement),
    ...calculateAverageMetrics(input),
    benchmarkScore: null, // tính riêng vì cần population
  };
}

// ---------- Benchmark score ----------

export interface PopulationRow {
  engagementPer1kFollowers: number | null;
  avgSharesPerPost: number | null;
  avgCommentsPerPost: number | null;
  videoViewsPerFollower: number | null;
  postingFrequencyPerDay: number | null;
  topPostEngagement?: number | null;
}

/**
 * Score chuẩn hóa percentile trong peer population.
 * Trọng số mặc định:
 *   engagementPer1kFollowers 0.35
 *   avgSharesPerPost 0.20
 *   avgCommentsPerPost 0.20
 *   videoViewsPerFollower 0.10
 *   postingFrequencyPerDay 0.10
 *   topPostEngagement 0.05
 *
 * Nếu thiếu videoViews → re-weight:
 *   engagementPer1kFollowers 0.40
 *   avgSharesPerPost 0.25
 *   avgCommentsPerPost 0.20
 *   postingFrequencyPerDay 0.10
 *   topPostEngagement 0.05
 *
 * Trả về 0..100 (1 số thập phân).
 */
export function calculateBenchmarkScore(
  snapshot: DerivedSnapshot,
  population: PopulationRow[],
): number | null {
  if (!population || population.length === 0) return null;

  const hasVideoViews =
    snapshot.videoViewsPerFollower != null &&
    population.some((p) => p.videoViewsPerFollower != null);

  const weights = hasVideoViews
    ? {
        engagementPer1kFollowers: 0.35,
        avgSharesPerPost: 0.2,
        avgCommentsPerPost: 0.2,
        videoViewsPerFollower: 0.1,
        postingFrequencyPerDay: 0.1,
        topPostEngagement: 0.05,
      }
    : {
        engagementPer1kFollowers: 0.4,
        avgSharesPerPost: 0.25,
        avgCommentsPerPost: 0.2,
        videoViewsPerFollower: 0,
        postingFrequencyPerDay: 0.1,
        topPostEngagement: 0.05,
      };

  const collect = (key: keyof PopulationRow): number[] =>
    population
      .map((p) => p[key])
      .filter((v): v is number => v != null && Number.isFinite(v));

  const arrEng = collect("engagementPer1kFollowers");
  const arrShares = collect("avgSharesPerPost");
  const arrComments = collect("avgCommentsPerPost");
  const arrVideo = collect("videoViewsPerFollower");
  const arrFreq = collect("postingFrequencyPerDay");
  const arrTop = collect("topPostEngagement");

  const safePct = (arr: number[], v: number | null | undefined): number => {
    if (v == null || arr.length === 0) return 0;
    return percentileRank(arr, v);
  };

  let score =
    safePct(arrEng, snapshot.engagementPer1kFollowers) * weights.engagementPer1kFollowers +
    safePct(arrShares, snapshot.avgSharesPerPost) * weights.avgSharesPerPost +
    safePct(arrComments, snapshot.avgCommentsPerPost) * weights.avgCommentsPerPost +
    safePct(arrVideo, snapshot.videoViewsPerFollower) * weights.videoViewsPerFollower +
    safePct(arrFreq, snapshot.postingFrequencyPerDay) * weights.postingFrequencyPerDay +
    safePct(arrTop, snapshot.topPostEngagement ?? null) * weights.topPostEngagement;

  return Math.round(score * 1000) / 10;
}

// ---------- Comparison ----------

export interface CompareInput {
  ownSnapshot: DerivedSnapshot;
  competitorSnapshots: DerivedSnapshot[];
  category?: string;
  ownPageName?: string;
}

export interface SnapshotForRank extends DerivedSnapshot {
  pageId?: string;
  pageName?: string;
  pageUrl?: string;
}

function median(values: number[]): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

function percentile(values: number[], p: number): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const idx = Math.min(sorted.length - 1, Math.max(0, Math.ceil(p * sorted.length) - 1));
  return sorted[idx];
}

export interface ComparisonResult {
  ownPageName: string;
  category: string | null;
  totalPeers: number;
  ownRank: number; // 1-based, rank 1 = cao nhất
  percentile: number; // 0..100, % peer có score <= own
  peerMedian: {
    engagementPer1kFollowers: number;
    avgCommentsPerPost: number;
    avgSharesPerPost: number;
    commentIntensity: number;
    shareIntensity: number;
    postingFrequencyPerDay: number;
    publicEngagementPerPost: number;
  };
  peerTop25: {
    engagementPer1kFollowers: number;
    avgCommentsPerPost: number;
    avgSharesPerPost: number;
    publicEngagementPerPost: number;
  };
  bestPage: {
    name?: string;
    score: number | null;
    engagementPer1kFollowers: number | null;
  } | null;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  ranked: Array<{
    pageId?: string;
    pageName?: string;
    pageUrl?: string;
    score: number | null;
    engagementPer1kFollowers: number | null;
    isOwn: boolean;
  }>;
}

/**
 * So sánh Page người dùng với peer competitor.
 */
export function compareOwnPageToPeers(input: CompareInput): ComparisonResult {
  const { ownSnapshot, competitorSnapshots, category, ownPageName } = input;
  const ownName = ownPageName ?? "Page của bạn";

  // Tập hợp tất cả snapshots (own + competitors) cho percentile population
  const all: SnapshotForRank[] = [
    { ...ownSnapshot, pageName: ownName, pageId: "__own__" },
    ...competitorSnapshots.map((s, i) => ({
      ...s,
      pageName: (s as any).pageName ?? `Competitor ${i + 1}`,
      pageUrl: (s as any).pageUrl,
    })),
  ];

  // Tính score cho mỗi row trong population
  const population = all.map((s) => ({
    engagementPer1kFollowers: s.engagementPer1kFollowers,
    avgSharesPerPost: s.avgSharesPerPost,
    avgCommentsPerPost: s.avgCommentsPerPost,
    videoViewsPerFollower: s.videoViewsPerFollower,
    postingFrequencyPerDay: s.postingFrequencyPerDay,
    topPostEngagement: s.topPostEngagement ?? null,
  }));

  const scored = all.map((s) => {
    const score = calculateBenchmarkScore(s as unknown as DerivedSnapshot, population);
    return { ...s, score };
  });

  // Rank theo score giảm dần
  const ranked = scored.sort((a, b) => (b.score ?? -1) - (a.score ?? -1));
  const ownRank = ranked.findIndex((r) => r.pageId === "__own__") + 1;
  const totalPeers = ranked.length;
  const ownPercentile =
    totalPeers > 0 ? Math.round(((totalPeers - ownRank) / (totalPeers - 1 || 1)) * 100) : 0;

  // Peer = competitorSnapshots (không tính own)
  const peers = competitorSnapshots;
  const med = (sel: (s: DerivedSnapshot) => number | null): number =>
    median(peers.map(sel).filter((v): v is number => v != null && Number.isFinite(v)));
  const top25 = (sel: (s: DerivedSnapshot) => number | null): number =>
    percentile(peers.map(sel).filter((v): v is number => v != null && Number.isFinite(v)), 0.75);

  const peerMedian = {
    engagementPer1kFollowers: med((s) => s.engagementPer1kFollowers),
    avgCommentsPerPost: med((s) => s.avgCommentsPerPost),
    avgSharesPerPost: med((s) => s.avgSharesPerPost),
    commentIntensity: med((s) => s.commentIntensity),
    shareIntensity: med((s) => s.shareIntensity),
    postingFrequencyPerDay: med((s) => s.postingFrequencyPerDay),
    publicEngagementPerPost: med((s) => s.publicEngagementPerPost),
  };
  const peerTop25 = {
    engagementPer1kFollowers: top25((s) => s.engagementPer1kFollowers),
    avgCommentsPerPost: top25((s) => s.avgCommentsPerPost),
    avgSharesPerPost: top25((s) => s.avgSharesPerPost),
    publicEngagementPerPost: top25((s) => s.publicEngagementPerPost),
  };

  const best = ranked[0];
  const bestPage = best && best.pageId !== "__own__"
    ? {
        name: best.pageName,
        score: best.score,
        engagementPer1kFollowers: best.engagementPer1kFollowers,
      }
    : {
        name: ranked[1]?.pageName ?? "—",
        score: ranked[1]?.score ?? null,
        engagementPer1kFollowers: ranked[1]?.engagementPer1kFollowers ?? null,
      };

  // Nhận xét tiếng Việt
  const strengths: string[] = [];
  const weaknesses: string[] = [];
  const recommendations: string[] = [];

  const ownEng = ownSnapshot.engagementPer1kFollowers;
  const ownComments = ownSnapshot.avgCommentsPerPost;
  const ownShares = ownSnapshot.avgSharesPerPost;
  const ownFreq = ownSnapshot.postingFrequencyPerDay;
  const ownPerPost = ownSnapshot.publicEngagementPerPost;
  const ownCommentIntensity = ownSnapshot.commentIntensity;
  const ownShareIntensity = ownSnapshot.shareIntensity;

  // Strengths
  if (ownEng != null && peerTop25.engagementPer1kFollowers > 0 && ownEng >= peerTop25.engagementPer1kFollowers) {
    strengths.push(
      "Page đang có hiệu suất tương tác công khai trên mỗi follower tốt hơn nhóm top 25%.",
    );
  } else if (ownEng != null && peerMedian.engagementPer1kFollowers > 0 && ownEng >= peerMedian.engagementPer1kFollowers) {
    strengths.push("Hiệu suất tương tác trên mỗi follower đang ngang bằng hoặc hơn median peer.");
  }
  if (ownShareIntensity != null && peerMedian.shareIntensity > 0 && ownShareIntensity >= peerMedian.shareIntensity) {
    strengths.push("Nội dung có tính lan truyền tốt (share intensity cao).");
  }
  if (ownPerPost != null && peerMedian.publicEngagementPerPost > 0 && ownPerPost >= peerMedian.publicEngagementPerPost) {
    strengths.push("Tương tác công khai trung bình mỗi bài cao hơn median peer.");
  }

  // Weaknesses
  if (ownEng != null && peerMedian.engagementPer1kFollowers > 0 && ownEng < peerMedian.engagementPer1kFollowers) {
    weaknesses.push(
      "Hiệu suất tương tác trên mỗi follower thấp hơn median peer — cần cải thiện chất lượng nội dung.",
    );
  }
  if (
    ownComments != null && ownShares != null &&
    peerMedian.avgCommentsPerPost > 0 && peerMedian.avgSharesPerPost > 0 &&
    ownComments >= peerMedian.avgCommentsPerPost &&
    ownShares < peerMedian.avgSharesPerPost
  ) {
    weaknesses.push(
      "Nội dung tạo tranh luận tốt nhưng khả năng lan truyền/share chưa tương xứng.",
    );
  }
  if (ownFreq != null && peerMedian.postingFrequencyPerDay > 0 && ownFreq < peerMedian.postingFrequencyPerDay * 0.5) {
    weaknesses.push("Tần suất đăng bài thấp hơn rõ rệt so với peer.");
  }

  // Recommendations
  if (ownFreq != null && ownPerPost != null &&
      peerMedian.postingFrequencyPerDay > 0 &&
      ownFreq < peerMedian.postingFrequencyPerDay &&
      ownPerPost >= peerMedian.publicEngagementPerPost) {
    recommendations.push(
      "Tần suất thấp nhưng chất lượng mỗi bài tốt; có thể thử tăng sản lượng có kiểm soát.",
    );
  }
  if (ownCommentIntensity != null && peerMedian.commentIntensity > 0 &&
      ownCommentIntensity >= peerMedian.commentIntensity * 1.3) {
    recommendations.push(
      "Nội dung tạo tranh luận mạnh; cần theo dõi rủi ro moderation.",
    );
  }
  if (ownShares != null && peerMedian.avgSharesPerPost > 0 &&
      ownShares < peerMedian.avgSharesPerPost * 0.7) {
    recommendations.push(
      "Share thấp: thử format dễ chia sẻ (carousel, infographic, tóm tắt số liệu) ở các chủ đề " +
      (category ? topicLabel(category) : "đang mạnh") + ".",
    );
  }
  if (ownEng != null && peerMedian.engagementPer1kFollowers > 0 &&
      ownEng < peerMedian.engagementPer1kFollowers) {
    recommendations.push(
      "Ưu tiên nội dung đã có tương tác cao trong quá khứ, CTA rõ hơn, thử A/B hook 3 dòng đầu.",
    );
  }
  if (recommendations.length === 0) {
    recommendations.push(
      "Hiệu suất khá cân bằng với peer — duy trì kế hoạch nội dung và theo dõi định kỳ qua /benchmark.",
    );
  }

  return {
    ownPageName: ownName,
    category: category ?? null,
    totalPeers: peers.length,
    ownRank,
    percentile: ownPercentile,
    peerMedian,
    peerTop25,
    bestPage,
    strengths,
    weaknesses,
    recommendations,
    ranked: ranked.map((r) => ({
      pageId: r.pageId,
      pageName: r.pageName,
      pageUrl: r.pageUrl,
      score: r.score,
      engagementPer1kFollowers: r.engagementPer1kFollowers,
      isOwn: r.pageId === "__own__",
    })),
  };
}

// ---------- Categories ----------

export const BENCHMARK_CATEGORIES = [
  "vi_mo",
  "chung_khoan",
  "lai_suat",
  "bds",
  "vang",
  "influencer_tai_chinh",
  "khac",
] as const;
export type BenchmarkCategory = (typeof BENCHMARK_CATEGORIES)[number];

export const BENCHMARK_CATEGORY_LABELS_VI: Record<string, string> = {
  vi_mo: "Vĩ mô",
  chung_khoan: "Chứng khoán",
  lai_suat: "Lãi suất",
  bds: "BĐS",
  vang: "Vàng",
  influencer_tai_chinh: "Influencer tài chính",
  khac: "Khác",
};

export function benchmarkCategoryLabel(cat: string | null | undefined): string {
  if (!cat) return "Tất cả";
  return BENCHMARK_CATEGORY_LABELS_VI[cat] ?? cat;
}

/**
 * Chuẩn hoá category nhập vào (chấp nhận cả label tiếng Việt hoặc key).
 */
export function normalizeCategory(input?: string | null): string {
  if (!input) return "khac";
  const trimmed = input.trim().toLowerCase();
  for (const [key, label] of Object.entries(BENCHMARK_CATEGORY_LABELS_VI)) {
    if (trimmed === key || trimmed === label.toLowerCase()) return key;
  }
  return trimmed;
}
