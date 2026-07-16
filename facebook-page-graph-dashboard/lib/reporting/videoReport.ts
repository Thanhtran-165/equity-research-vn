/**
 * Video reporting helpers — aggregates VideoDailyMetric + VideoLifetimeMetric for monthly/weekly reports.
 */
import { aggregateDaily, aggregateMonthly } from "@/lib/videoAggregations";

export interface VideoMonthlySummary {
  totalViews3s: number;
  summedReach: number;
  watchTimeHours: number;
  avgWatchPerView: number | null;
  totalReactions: number;
  totalComments: number;
  totalShares: number;
  activeVideoCount: number;
  dailyRows: number;
}

export function computeVideoMonthlySummary(dailyRows: any[]): VideoMonthlySummary {
  const views = dailyRows.reduce((s, r) => s + (r.videoViews3s ?? 0), 0);
  const reach = dailyRows.reduce((s, r) => s + (r.reach ?? 0), 0);
  const watch = dailyRows.reduce((s, r) => s + (r.watchTimeSeconds ?? 0), 0);
  const reactions = dailyRows.reduce((s, r) => s + (r.reactions ?? 0), 0);
  const comments = dailyRows.reduce((s, r) => s + (r.comments ?? 0), 0);
  const shares = dailyRows.reduce((s, r) => s + (r.shares ?? 0), 0);
  const uniqueVideos = new Set(dailyRows.map((r) => r.videoAssetId)).size;

  return {
    totalViews3s: views,
    summedReach: reach,
    watchTimeHours: watch / 3600,
    avgWatchPerView: views > 0 ? watch / views : null,
    totalReactions: reactions,
    totalComments: comments,
    totalShares: shares,
    activeVideoCount: uniqueVideos,
    dailyRows: dailyRows.length,
  };
}

export interface TopVideoInPeriod {
  videoAssetId: number;
  externalVideoId: string;
  title: string | null;
  activeDays: number;
  videoViews3s: number;
  reach: number;
  watchTimeHours: number;
  avgWatchPerView: number | null;
  reactions: number;
  comments: number;
  shares: number;
}

export function topVideosByViews(dailyRows: any[], limit = 20): TopVideoInPeriod[] {
  return aggregateTopVideos(dailyRows, limit, "videoViews3s");
}

export function topVideosByWatchTime(dailyRows: any[], limit = 20): TopVideoInPeriod[] {
  return aggregateTopVideos(dailyRows, limit, "watchTimeSeconds");
}

function aggregateTopVideos(dailyRows: any[], limit: number, sortKey: string): TopVideoInPeriod[] {
  const byVideo: Record<number, any[]> = {};
  for (const r of dailyRows) {
    if (!byVideo[r.videoAssetId]) byVideo[r.videoAssetId] = [];
    byVideo[r.videoAssetId].push(r);
  }

  return Object.entries(byVideo)
    .map(([vid, arr]) => {
      const views = arr.reduce((s, r) => s + (r.videoViews3s ?? 0), 0);
      const reach = arr.reduce((s, r) => s + (r.reach ?? 0), 0);
      const watch = arr.reduce((s, r) => s + (r.watchTimeSeconds ?? 0), 0);
      const reactions = arr.reduce((s, r) => s + (r.reactions ?? 0), 0);
      const comments = arr.reduce((s, r) => s + (r.comments ?? 0), 0);
      const shares = arr.reduce((s, r) => s + (r.shares ?? 0), 0);
      const asset = arr[0]?.videoAsset;
      return {
        videoAssetId: Number(vid),
        externalVideoId: asset?.externalVideoId ?? vid,
        title: asset?.title ?? null,
        activeDays: arr.length,
        videoViews3s: views,
        reach,
        watchTimeHours: watch / 3600,
        avgWatchPerView: views > 0 ? watch / views : null,
        reactions,
        comments,
        shares,
      };
    })
    .sort((a: any, b: any) => (b[sortKey] ?? 0) - (a[sortKey] ?? 0))
    .slice(0, limit);
}

export interface VideoSpike {
  date: string;
  totalViews: number;
  totalReach: number;
  reason: string;
}

export function detectVideoSpikes(dailyRows: any[]): VideoSpike[] {
  const daily = aggregateDaily(dailyRows);
  if (daily.length < 3) return [];

  const viewsValues = daily.map((d) => d.videoViews3s).sort((a, b) => a - b);
  const median = viewsValues[Math.floor(viewsValues.length / 2)] || 0;
  const threshold = median * 3;

  return daily
    .filter((d) => d.videoViews3s >= threshold && d.videoViews3s > 0)
    .map((d) => ({
      date: d.date,
      totalViews: d.videoViews3s,
      totalReach: d.reach,
      reason: `Views ${d.videoViews3s.toLocaleString("vi-VN")} vs median ${median.toLocaleString("vi-VN")}`,
    }));
}
