"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Video,
  Eye,
  Clock,
  Heart,
  MessageSquare,
  Share2,
  TrendingUp,
  AlertTriangle,
  Calendar,
} from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import ErrorBox from "@/components/ErrorBox";
import EmptyState from "@/components/ui/EmptyState";
import Segmented from "@/components/ui/Segmented";
import { useChartTheme, formatNumber } from "@/components/charts/chartTheme";
import {
  Line,
  LineChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface Summary {
  totalVideoAssets: number;
  lifetimeAssets: number;
  dailyActiveAssets: number;
  dailyOnlyAssets: number;
  unlinkedAssets: number;
  totalViews3s: number;
  totalReach: number;
  totalWatchTimeHours: number;
  avgWatchTimePerView: number | null;
  totalReactions: number;
  totalComments: number;
  totalShares: number;
  totalSocialEngagement: number;
  dateRange: { min: string | null; max: string | null };
  dailyRowCount: number;
}

interface LifetimeRow {
  videoAssetId: number;
  externalVideoId: string;
  title: string | null;
  reach: number | null;
  videoViews3s: number | null;
  watchTimeSeconds: number | null;
  avgWatchTime: number | null;
  reactions: number | null;
  comments: number | null;
  shares: number | null;
  socialER: number | null;
  avgWatchPerView: number | null;
}

interface DailyRow {
  date: string;
  videoViews3s: number;
  reach: number;
  watchTimeHours: number;
  socialEngagement: number;
  socialEngagementRate: number | null;
  avgWatchTimePerView: number | null;
  activeVideos: number;
}

interface MonthlyRow {
  month: string;
  rows: number;
  uniqueVideos: number;
  videoViews3s: number;
  reach: number;
  watchTimeHours: number;
  avgWatchTimePerView: number | null;
  reactions: number;
  comments: number;
  shares: number;
}

interface TopActiveRow {
  videoAssetId: number;
  externalVideoId: string;
  title: string | null;
  activeDays: number;
  videoViews3s: number;
  reach: number;
  watchTimeHours: number;
  avgWatchTimePerView: number | null;
  reactions: number;
  comments: number;
  shares: number;
  firstActiveDate: string;
  lastActiveDate: string;
}

interface Anomaly {
  type: string;
  label: string;
  externalVideoId?: string;
  value?: number;
}

interface VideoData {
  summary: Summary;
  lifetime: LifetimeRow[];
  daily: DailyRow[];
  monthly: MonthlyRow[];
  topActive: TopActiveRow[];
  anomalies: Anomaly[];
  sort: string;
  dateRange: { min: string | null; max: string | null };
}

interface ApiError {
  code?: string;
  message: string;
}

const num = (v: number | null | undefined, digits = 0) =>
  v == null ? "—" : v.toLocaleString("vi-VN", { maximumFractionDigits: digits });
const pct = (v: number | null | undefined) =>
  v == null ? "—" : `${(v * 100).toFixed(2)}%`;

export default function VideoDashboardPage() {
  const [data, setData] = useState<VideoData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [period, setPeriod] = useState<"all" | "28d" | "7d">("all");
  const [sort, setSort] = useState("videoViews3s");
  const t = useChartTheme();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let startDate: string | undefined;
      const now = new Date();
      if (period === "28d") {
        startDate = new Date(now.getTime() - 28 * 86400000).toISOString().slice(0, 10);
      } else if (period === "7d") {
        startDate = new Date(now.getTime() - 7 * 86400000).toISOString().slice(0, 10);
      }
      const params = new URLSearchParams({ sort });
      if (startDate) params.set("startDate", startDate);
      const r = await fetch(`/api/video-dashboard?${params}`).then((x) => x.json());
      if (r.ok) setData(r.data);
      else setError(r.error);
    } catch (e: any) {
      setError({ message: e?.message ?? String(e) });
    } finally {
      setLoading(false);
    }
  }, [period, sort]);

  useEffect(() => {
    load();
  }, [load]);

  const dailyChart = (data?.daily ?? []).map((d) => ({
    date: d.date.slice(5),
    views: d.videoViews3s,
    reach: d.reach,
  }));

  return (
    <>
      <PageHeader
        title="Video Dashboard"
        subtitle="Hiệu suất video/reels từ Meta Business Suite CSV"
        icon={<Video className="w-5 h-5" />}
        actions={
          <>
            <Segmented
              value={period}
              onChange={(v) => setPeriod(v as any)}
              options={[
                { value: "all", label: "YTD" },
                { value: "28d", label: "28 ngày" },
                { value: "7d", label: "7 ngày" },
              ]}
            />
            <button onClick={load} className="btn-primary">↻</button>
          </>
        }
      />

      {/* Data source badge */}
      <div className="glass-card p-3 mb-5 flex items-center gap-3 flex-wrap">
        <span className="badge-neon">📊 Meta Business Suite CSV</span>
        <span className="text-xs text-muted">
          {data?.dateRange.min ? `${data.dateRange.min} → ${data.dateRange.max}` : "Chưa có dữ liệu"}
        </span>
        <span className="text-xs text-muted">{data?.summary.dailyRowCount ?? 0} daily rows</span>
      </div>

      {/* Warnings */}
      {data?.anomalies && data.anomalies.length > 0 && (
        <div className="glass-card p-4 mb-5 border-amber-500/30">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span className="font-medium text-sm text-amber-400">{data.anomalies.length} cảnh báo</span>
          </div>
          <div className="space-y-2">
            {data.anomalies.map((a, i) => (
              <div key={i} className="text-xs p-2 rounded-lg" style={{ background: "rgba(251,191,36,0.05)" }}>
                <div className="flex items-center justify-between">
                  <span className="text-amber-400 font-medium">{a.label}</span>
                  <span className="mono text-muted">{a.externalVideoId}</span>
                </div>
                {a.value != null && (
                  <div className="mt-1 text-muted">
                    avg watch: <span className="mono text-amber-400">{a.value}s/view</span> ({(a.value / 60).toFixed(1)} min/view)
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {data && data.summary.unlinkedAssets > 0 && (
        <div className="glass-card p-3 mb-5 text-xs text-muted">
          ℹ️ {data.summary.unlinkedAssets} video assets chưa link với Post. Đây là điều bình thường vì Meta export dùng video asset IDs khác post IDs.
        </div>
      )}

      {error && <div className="mb-5"><ErrorBox error={error} onRetry={load} /></div>}

      {/* Summary KPIs */}
      {data && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
          <KpiBox icon={<Video className="w-4 h-4" />} label="Video assets" value={num(data.summary.totalVideoAssets)} hint={`${data.summary.lifetimeAssets} lifetime · ${data.summary.dailyOnlyAssets} daily-only`} />
          <KpiBox icon={<Eye className="w-4 h-4" />} label="Total 3s views" value={num(data.summary.totalViews3s)} />
          <KpiBox icon={<TrendingUp className="w-4 h-4" />} label="Summed reach" value={num(data.summary.totalReach)} hint="sum across videos/days, not unique" />
          <KpiBox icon={<Clock className="w-4 h-4" />} label="Watch time (hrs)" value={num(data.summary.totalWatchTimeHours, 1)} />
          <KpiBox icon={<Clock className="w-4 h-4" />} label="Avg watch/view" value={data.summary.avgWatchTimePerView != null ? `${num(data.summary.avgWatchTimePerView, 1)}s` : "—"} />
          <KpiBox icon={<Heart className="w-4 h-4" />} label="Social eng." value={num(data.summary.totalSocialEngagement)} />
        </div>
      )}

      {/* Daily trend chart */}
      <div className="glass-card p-4 mb-6">
        <h3 className="font-medium text-sm mb-3" style={{ color: "var(--text-main)" }}>Daily 3s Views + Reach</h3>
        {loading ? (
          <div className="skeleton h-[260px] w-full" />
        ) : dailyChart.length > 0 ? (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={dailyChart} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={t.grid} vertical={false} />
              <XAxis dataKey="date" stroke={t.axis} fontSize={10} tickLine={false} axisLine={false} minTickGap={20} />
              <YAxis stroke={t.axis} fontSize={11} tickLine={false} axisLine={false} width={48} tickFormatter={(v) => formatNumber(v)} />
              <Tooltip contentStyle={{ background: t.tooltipBg, border: `1px solid ${t.tooltipBorder}`, borderRadius: 8, fontSize: 12 }} />
              <Line type="monotone" dataKey="views" name="3s Views" stroke={t.colors.purple} strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="reach" name="Reach" stroke={t.colors.cyan} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-[260px] flex items-center justify-center text-sm text-muted">Chưa có dữ liệu daily</div>
        )}
      </div>

      {/* Monthly aggregation */}
      {data && data.monthly.length > 0 && (
        <div className="mb-6">
          <h3 className="font-medium text-sm mb-3" style={{ color: "var(--text-main)" }}>Monthly Video Performance</h3>
          <div className="table-wrap overflow-x-auto scrollbar-thin">
            <table className="table">
              <thead><tr>
                <th>Month</th>
                <th className="text-right">Rows</th>
                <th className="text-right">Videos</th>
                <th className="text-right">3s Views</th>
                <th className="text-right">Summed Reach</th>
                <th className="text-right">Watch (hrs)</th>
                <th className="text-right">Avg sec/view</th>
                <th className="text-right">Reactions</th>
                <th className="text-right">Comments</th>
                <th className="text-right">Shares</th>
              </tr></thead>
              <tbody>
                {data.monthly.map((m) => (
                  <tr key={m.month}>
                    <td className="mono">{m.month}</td>
                    <td className="text-right mono">{m.rows}</td>
                    <td className="text-right mono">{m.uniqueVideos}</td>
                    <td className="text-right mono">{num(m.videoViews3s)}</td>
                    <td className="text-right mono">{num(m.reach)}</td>
                    <td className="text-right mono">{num(m.watchTimeHours, 1)}</td>
                    <td className="text-right mono">{m.avgWatchTimePerView != null ? `${num(m.avgWatchTimePerView, 1)}s` : "—"}</td>
                    <td className="text-right mono">{num(m.reactions)}</td>
                    <td className="text-right mono">{num(m.comments)}</td>
                    <td className="text-right mono">{num(m.shares)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Lifetime ranking */}
      {data && data.lifetime.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium text-sm" style={{ color: "var(--text-main)" }}>Top Videos — Lifetime</h3>
            <select value={sort} onChange={(e) => setSort(e.target.value)} className="select w-auto !py-1 !text-xs">
              <option value="videoViews3s">Sort: 3s Views</option>
              <option value="reach">Sort: Reach</option>
              <option value="watchTimeSeconds">Sort: Watch Time</option>
              <option value="avgWatchPerView">Sort: Avg Watch/View</option>
              <option value="socialER">Sort: Social ER</option>
            </select>
          </div>
          <div className="table-wrap overflow-x-auto scrollbar-thin">
            <table className="table">
              <thead><tr>
                <th className="text-right">#</th>
                <th>Title</th>
                <th className="text-right">Reach</th>
                <th className="text-right">3s Views</th>
                <th className="text-right">Watch (hrs)</th>
                <th className="text-right">Avg sec/view</th>
                <th className="text-right">❤️</th>
                <th className="text-right">💬</th>
                <th className="text-right">🔁</th>
                <th className="text-right">Social ER</th>
              </tr></thead>
              <tbody>
                {data.lifetime.slice(0, 20).map((v, i) => {
                  const isAnomaly = v.avgWatchPerView != null && v.avgWatchPerView > 600;
                  return (
                  <tr key={v.videoAssetId} className={isAnomaly ? "bg-amber-500/5" : ""}>
                    <td className="text-right text-muted mono">{i + 1}</td>
                    <td className="max-w-[200px]">
                      <div className="line-clamp-1" style={{ color: "var(--text-main)" }}>
                        {v.title || v.externalVideoId}
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-xs text-faint mono">{v.externalVideoId.slice(0, 16)}</span>
                        {isAnomaly && <span className="badge bg-amber-500/20 text-amber-400 text-[9px] uppercase tracking-wide">⚠ anomaly</span>}
                      </div>
                    </td>
                    <td className="text-right mono">{num(v.reach)}</td>
                    <td className="text-right mono text-neon-purple">{num(v.videoViews3s)}</td>
                    <td className="text-right mono">{num((v.watchTimeSeconds ?? 0) / 3600, 1)}</td>
                    <td className={`text-right mono ${isAnomaly ? "text-amber-400 font-bold" : ""}`}>
                      {v.avgWatchPerView != null ? `${num(v.avgWatchPerView, 1)}s` : "—"}
                      {isAnomaly && <div className="text-[9px] text-amber-500/70">likely Meta data issue</div>}
                    </td>
                    <td className="text-right mono">{num(v.reactions)}</td>
                    <td className="text-right mono">{num(v.comments)}</td>
                    <td className="text-right mono">{num(v.shares)}</td>
                    <td className="text-right mono text-neon-green">{pct(v.socialER)}</td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Top active in period */}
      {data && data.topActive.length > 0 && (
        <div className="mb-6">
          <h3 className="font-medium text-sm mb-3" style={{ color: "var(--text-main)" }}>Top Active Videos in Period</h3>
          <div className="table-wrap overflow-x-auto scrollbar-thin">
            <table className="table">
              <thead><tr>
                <th>Video</th>
                <th className="text-right">Days</th>
                <th className="text-right">Views</th>
                <th className="text-right">Reach</th>
                <th className="text-right">Watch (hrs)</th>
                <th className="text-right">First active</th>
                <th className="text-right">Last active</th>
              </tr></thead>
              <tbody>
                {data.topActive.map((v) => (
                  <tr key={v.videoAssetId}>
                    <td className="max-w-[200px]">
                      <div className="line-clamp-1" style={{ color: "var(--text-main)" }}>
                        {v.title || v.externalVideoId}
                      </div>
                    </td>
                    <td className="text-right mono">{v.activeDays}</td>
                    <td className="text-right mono">{num(v.videoViews3s)}</td>
                    <td className="text-right mono">{num(v.reach)}</td>
                    <td className="text-right mono">{num(v.watchTimeHours, 1)}</td>
                    <td className="text-right mono text-xs">{v.firstActiveDate}</td>
                    <td className="text-right mono text-xs">{v.lastActiveDate}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {loading && <div className="skeleton h-32 w-full" />}
      {!loading && !data && !error && (
        <EmptyState title="Chưa có dữ liệu video" description="Import V01/V02 CSV từ Meta Business Suite." icon={<Video className="w-6 h-6" />} />
      )}
    </>
  );
}

function KpiBox({ icon, label, value, hint }: { icon: React.ReactNode; label: string; value: React.ReactNode; hint?: string }) {
  return (
    <div className="glass-card p-4">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-muted">{icon}</span>
        <span className="text-xs text-muted uppercase tracking-wide">{label}</span>
      </div>
      <div className="kpi-value text-xl font-semibold text-neon-purple">{value}</div>
      {hint && <div className="text-xs text-faint mt-1">{hint}</div>}
    </div>
  );
}
