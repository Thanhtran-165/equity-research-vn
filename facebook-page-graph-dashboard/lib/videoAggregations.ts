/**
 * Video aggregation helpers — computed metrics from VideoLifetimeMetric + VideoDailyMetric.
 */

export interface VideoLifetimeRow {
  videoAssetId: number;
  externalVideoId: string;
  title: string | null;
  reach: number | null;
  videoViews3s: number | null;
  videoViews1min: number | null;
  watchTimeSeconds: number | null;
  avgWatchTime: number | null;
  reactions: number | null;
  comments: number | null;
  shares: number | null;
  matchedPostId: string | null;
}

export interface DailyAggregate {
  date: string;
  videoViews3s: number;
  reach: number;
  watchTimeSeconds: number;
  reactions: number;
  comments: number;
  shares: number;
  // Computed
  watchTimeHours: number;
  avgWatchTimePerView: number | null;
  socialEngagement: number;
  socialEngagementRate: number | null;
  activeVideos: number;
}

export interface MonthlyAggregate {
  month: string;
  rows: number;
  uniqueVideos: number;
  videoViews3s: number;
  reach: number;
  watchTimeSeconds: number;
  watchTimeHours: number;
  avgWatchTimePerView: number | null;
  reactions: number;
  comments: number;
  shares: number;
  socialEngagement: number;
  socialEngagementRate: number | null;
}

export interface TopActiveVideo {
  videoAssetId: number;
  externalVideoId: string;
  title: string | null;
  activeDays: number;
  videoViews3s: number;
  reach: number;
  watchTimeSeconds: number;
  watchTimeHours: number;
  avgWatchTimePerView: number | null;
  reactions: number;
  comments: number;
  shares: number;
  firstActiveDate: string;
  lastActiveDate: string;
}

export interface VideoSummary {
  totalVideoAssets: number;
  lifetimeAssets: number;
  dailyActiveAssets: number;
  dailyOnlyAssets: number;
  unlinkedAssets: number;
  totalViews3s: number;
  totalReach: number;
  totalWatchTimeSeconds: number;
  totalWatchTimeHours: number;
  avgWatchTimePerView: number | null;
  totalReactions: number;
  totalComments: number;
  totalShares: number;
  totalSocialEngagement: number;
  dateRange: { min: string | null; max: string | null };
  dailyRowCount: number;
}

export function computeVideoSummary(
  lifetime: VideoLifetimeRow[],
  dailyCount: number,
  dateRange: { min: string | null; max: string | null },
  totalAssets: number,
  dailyAssetIds: number[],
  lifetimeAssetIds: number[],
): VideoSummary {
  const totalViews3s = lifetime.reduce((s, v) => s + (v.videoViews3s ?? 0), 0);
  const totalReach = lifetime.reduce((s, v) => s + (v.reach ?? 0), 0);
  const totalWatch = lifetime.reduce((s, v) => s + (v.watchTimeSeconds ?? 0), 0);
  const totalReactions = lifetime.reduce((s, v) => s + (v.reactions ?? 0), 0);
  const totalComments = lifetime.reduce((s, v) => s + (v.comments ?? 0), 0);
  const totalShares = lifetime.reduce((s, v) => s + (v.shares ?? 0), 0);
  const dailyOnly = dailyAssetIds.filter((id) => !lifetimeAssetIds.includes(id)).length;

  return {
    totalVideoAssets: totalAssets,
    lifetimeAssets: lifetimeAssetIds.length,
    dailyActiveAssets: dailyAssetIds.length,
    dailyOnlyAssets: dailyOnly,
    unlinkedAssets: lifetime.filter((v) => !v.matchedPostId).length,
    totalViews3s,
    totalReach,
    totalWatchTimeSeconds: totalWatch,
    totalWatchTimeHours: totalWatch / 3600,
    avgWatchTimePerView: totalViews3s > 0 ? totalWatch / totalViews3s : null,
    totalReactions,
    totalComments,
    totalShares,
    totalSocialEngagement: totalReactions + totalComments + totalShares,
    dateRange,
    dailyRowCount: dailyCount,
  };
}

export function computeSocialER(reactions: number, comments: number, shares: number, reach: number): number | null {
  if (!reach || reach <= 0) return null;
  return (reactions + comments + shares) / reach;
}

export function computeAvgWatchPerView(watchTimeSeconds: number, views3s: number): number | null {
  if (!views3s || views3s <= 0) return null;
  return watchTimeSeconds / views3s;
}

export function aggregateDaily(rows: any[]): DailyAggregate[] {
  const byDate: Record<string, any[]> = {};
  for (const r of rows) {
    const d = r.date;
    if (!byDate[d]) byDate[d] = [];
    byDate[d].push(r);
  }

  return Object.entries(byDate)
    .map(([date, arr]) => {
      const views = arr.reduce((s, r) => s + (r.videoViews3s ?? 0), 0);
      const reach = arr.reduce((s, r) => s + (r.reach ?? 0), 0);
      const watch = arr.reduce((s, r) => s + (r.watchTimeSeconds ?? 0), 0);
      const reactions = arr.reduce((s, r) => s + (r.reactions ?? 0), 0);
      const comments = arr.reduce((s, r) => s + (r.comments ?? 0), 0);
      const shares = arr.reduce((s, r) => s + (r.shares ?? 0), 0);
      const social = reactions + comments + shares;
      return {
        date,
        videoViews3s: views,
        reach,
        watchTimeSeconds: watch,
        reactions,
        comments,
        shares,
        watchTimeHours: watch / 3600,
        avgWatchTimePerView: computeAvgWatchPerView(watch, views),
        socialEngagement: social,
        socialEngagementRate: computeSocialER(reactions, comments, shares, reach),
        activeVideos: arr.length,
      };
    })
    .sort((a, b) => a.date.localeCompare(b.date));
}

export function aggregateMonthly(daily: DailyAggregate[]): MonthlyAggregate[] {
  const byMonth: Record<string, DailyAggregate[]> = {};
  for (const d of daily) {
    const m = d.date.slice(0, 7);
    if (!byMonth[m]) byMonth[m] = [];
    byMonth[m].push(d);
  }

  return Object.entries(byMonth)
    .map(([month, arr]) => {
      const views = arr.reduce((s, d) => s + d.videoViews3s, 0);
      const reach = arr.reduce((s, d) => s + d.reach, 0);
      const watch = arr.reduce((s, d) => s + d.watchTimeSeconds, 0);
      const reactions = arr.reduce((s, d) => s + d.reactions, 0);
      const comments = arr.reduce((s, d) => s + d.comments, 0);
      const shares = arr.reduce((s, d) => s + d.shares, 0);
      const social = reactions + comments + shares;
      // uniqueVideos = sum of distinct activeVideos per day is NOT correct.
      // We need distinct videoAssetIds across the month. Since DailyAggregate
      // doesn't carry videoAssetId, we compute from raw rows instead.
      // This function is called from the API with DailyAggregate[] — the API
      // should pass uniqueVideoAssetIds separately. For now, use sum of activeVideos
      // as raw video-days, and the API will override with correct distinct count.
      const videoDays = arr.reduce((s, d) => s + d.activeVideos, 0);
      return {
        month,
        rows: arr.length,
        uniqueVideos: videoDays, // Will be overridden by API with actual distinct count
        videoViews3s: views,
        reach,
        watchTimeSeconds: watch,
        watchTimeHours: watch / 3600,
        avgWatchTimePerView: computeAvgWatchPerView(watch, views),
        reactions,
        comments,
        shares,
        socialEngagement: social,
        socialEngagementRate: computeSocialER(reactions, comments, shares, reach),
      };
    })
    .sort((a, b) => a.month.localeCompare(b.month));
}

export function topActiveVideos(rows: any[], limit = 20): TopActiveVideo[] {
  const byVideo: Record<number, any[]> = {};
  for (const r of rows) {
    const id = r.videoAssetId;
    if (!byVideo[id]) byVideo[id] = [];
    byVideo[id].push(r);
  }

  return Object.entries(byVideo)
    .map(([vidStr, arr]) => {
      const views = arr.reduce((s, r) => s + (r.videoViews3s ?? 0), 0);
      const reach = arr.reduce((s, r) => s + (r.reach ?? 0), 0);
      const watch = arr.reduce((s, r) => s + (r.watchTimeSeconds ?? 0), 0);
      const reactions = arr.reduce((s, r) => s + (r.reactions ?? 0), 0);
      const comments = arr.reduce((s, r) => s + (r.comments ?? 0), 0);
      const shares = arr.reduce((s, r) => s + (r.shares ?? 0), 0);
      const dates = arr.map((r) => r.date).sort();
      const asset = arr[0]?.videoAsset;
      return {
        videoAssetId: Number(vidStr),
        externalVideoId: asset?.externalVideoId ?? vidStr,
        title: asset?.title ?? null,
        activeDays: arr.length,
        videoViews3s: views,
        reach,
        watchTimeSeconds: watch,
        watchTimeHours: watch / 3600,
        avgWatchTimePerView: computeAvgWatchPerView(watch, views),
        reactions,
        comments,
        shares,
        firstActiveDate: dates[0],
        lastActiveDate: dates[dates.length - 1],
      };
    })
    .sort((a, b) => b.videoViews3s - a.videoViews3s)
    .slice(0, limit);
}

export interface VideoAnomaly {
  type: string;
  label: string;
  videoAssetId?: number;
  externalVideoId?: string;
  value?: number;
}

export function detectVideoAnomalies(lifetime: VideoLifetimeRow[]): VideoAnomaly[] {
  const anomalies: VideoAnomaly[] = [];

  for (const v of lifetime) {
    // avgWatchTimePerView > 600 seconds
    if (v.videoViews3s && v.videoViews3s > 0 && v.watchTimeSeconds) {
      const avg = v.watchTimeSeconds / v.videoViews3s;
      if (avg > 600) {
        anomalies.push({
          type: "high_avg_watch",
          label: "Possible watch time anomaly (>600s/view)",
          videoAssetId: v.videoAssetId,
          externalVideoId: v.externalVideoId,
          value: Math.round(avg),
        });
      }
    }
    // reach = 0 but views > 0
    if ((!v.reach || v.reach === 0) && v.videoViews3s && v.videoViews3s > 0) {
      anomalies.push({
        type: "zero_reach_with_views",
        label: "Reach = 0 but views > 0",
        videoAssetId: v.videoAssetId,
        externalVideoId: v.externalVideoId,
      });
    }
    // videoViews3s = 0 but watchTime > 0
    if ((!v.videoViews3s || v.videoViews3s === 0) && v.watchTimeSeconds && v.watchTimeSeconds > 0) {
      anomalies.push({
        type: "zero_views_with_watch",
        label: "Views = 0 but watch time > 0",
        videoAssetId: v.videoAssetId,
        externalVideoId: v.externalVideoId,
      });
    }
  }

  return anomalies;
}
