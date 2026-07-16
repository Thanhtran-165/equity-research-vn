"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  BarChart3,
  TrendingUp,
  Clock,
  Calendar,
  Layers,
  Upload,
  Trophy,
} from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import ErrorBox from "@/components/ErrorBox";
import EmptyState from "@/components/ui/EmptyState";
import { useChartTheme, formatNumber } from "@/components/charts/chartTheme";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface Benchmark {
  totalPosts: number;
  dateRange: { min: string | null; max: string | null };
  reach: { count: number; min: number; median: number; mean: number; p25: number; p75: number; p90: number; max: number } | null;
  reactions: { count: number; min: number; median: number; mean: number; p25: number; p75: number; p90: number; max: number };
  comments: { count: number; min: number; median: number; mean: number; p25: number; p75: number; p90: number; max: number };
  shares: { count: number; min: number; median: number; mean: number; p25: number; p75: number; p90: number; max: number };
  engagementRate: { count: number; min: number; median: number; mean: number; p25: number; p75: number; p90: number; max: number } | null;
  videoViews: { count: number; min: number; median: number; mean: number; p25: number; p75: number; p90: number; max: number } | null;
  byTopic: { topic: string; topicLabel: string; postCount: number; avgReach: number | null; avgReactions: number; avgComments: number; avgShares: number; avgER: number | null; totalReach: number }[];
  byType: { postType: string; postCount: number; avgReach: number | null; avgReactions: number; avgComments: number; avgER: number | null }[];
  byWeekday: { weekday: number; weekdayLabel: string; postCount: number; avgReach: number | null; avgER: number | null }[];
  byHour: { hourBucket: string; postCount: number; avgReach: number | null; avgER: number | null }[];
  correlations: { reachVsReactions: number | null; reachVsComments: number | null; reachVsShares: number | null; reactionsVsComments: number | null };
  topReachPosts: any[];
  topERPosts: any[];
  topCommentPosts: any[];
  insights: string[];
}

interface ApiError {
  code?: string;
  message: string;
  details?: any;
}

const num = (v: number | null | undefined) =>
  v == null ? "—" : v.toLocaleString("vi-VN", { maximumFractionDigits: 1 });
const pct = (v: number | null | undefined) =>
  v == null ? "—" : `${(v * 100).toFixed(2)}%`;

function StatCard({ label, stats, format = "num" }: { label: string; stats: any; format?: "num" | "pct" }) {
  if (!stats) return (
    <div className="glass-card p-4">
      <div className="text-xs text-muted uppercase tracking-wide mb-1">{label}</div>
      <div className="text-sm text-faint">Chưa có dữ liệu</div>
    </div>
  );
  const fmt = format === "pct" ? (v: number) => `${(v * 100).toFixed(2)}%` : (v: number) => v.toLocaleString("vi-VN");
  return (
    <div className="glass-card p-4">
      <div className="text-xs text-muted uppercase tracking-wide mb-2">{label}</div>
      <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
        <div className="text-faint">Median</div>
        <div className="mono text-right">{fmt(stats.median)}</div>
        <div className="text-faint">Mean</div>
        <div className="mono text-right">{fmt(stats.mean)}</div>
        <div className="text-faint">Top 25%</div>
        <div className="mono text-right text-neon-cyan">{fmt(stats.p75)}</div>
        <div className="text-faint">Top 10%</div>
        <div className="mono text-right text-neon-green">{fmt(stats.p90)}</div>
        <div className="text-faint">Best</div>
        <div className="mono text-right text-neon-purple">{fmt(stats.max)}</div>
        <div className="text-faint">Min</div>
        <div className="mono text-right text-faint">{fmt(stats.min)}</div>
      </div>
    </div>
  );
}

export default function InternalBenchmarkPage() {
  const [benchmark, setBenchmark] = useState<Benchmark | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const t = useChartTheme();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch("/api/benchmark/internal").then((x) => x.json());
      if (r.ok) setBenchmark(r.data.benchmark);
      else setError(r.error);
    } catch (e: any) {
      setError({ message: e?.message ?? String(e) });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Weekday chart data
  const weekdayData = (benchmark?.byWeekday ?? [])
    .filter((w) => w.avgReach != null)
    .map((w) => ({ name: w.weekdayLabel, reach: Math.round(w.avgReach!), posts: w.postCount }));

  // Hour chart data
  const hourData = (benchmark?.byHour ?? [])
    .filter((h) => h.avgReach != null)
    .map((h) => ({ name: h.hourBucket, reach: Math.round(h.avgReach!), posts: h.postCount }));

  return (
    <>
      <PageHeader
        title="Internal Benchmark"
        subtitle="Phân tích pattern từ chính bài viết của Page — baseline nội bộ"
        icon={<BarChart3 className="w-5 h-5" />}
        actions={
          <>
            <Link href="/imports" className="btn-secondary">
              <Upload className="w-4 h-4" /> Import thêm
            </Link>
            <button onClick={load} className="btn-primary">
              ↻ <span className="hidden sm:inline">Tính lại</span>
            </button>
          </>
        }
      />

      {loading && (
        <div className="space-y-3">
          <div className="skeleton h-24 w-full" />
          <div className="skeleton h-64 w-full" />
        </div>
      )}

      {error && <ErrorBox title="Không tải được benchmark" error={error} onRetry={load} />}

      {!loading && !benchmark && !error && (
        <EmptyState
          title="Chưa có đủ dữ liệu"
          description="Import CSV từ Meta Business Suite để có reach/impressions, sau đó tính lại."
          icon={<BarChart3 className="w-6 h-6" />}
          action={<Link href="/imports" className="btn-primary"><Upload className="w-4 h-4" /> Import CSV</Link>}
        />
      )}

      {benchmark && (
        <div className="space-y-6 animate-fade-in">
          {/* Summary KPI */}
          <div className="glass-card p-5">
            <div className="flex items-center gap-3 mb-4">
              <Trophy className="w-5 h-5 text-neon-amber" />
              <h2 className="font-semibold" style={{ color: "var(--text-main)" }}>Tổng quan Page</h2>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div>
                <div className="text-xs text-muted">Tổng bài viết</div>
                <div className="kpi-value text-2xl font-semibold text-neon-purple">{benchmark.totalPosts}</div>
              </div>
              <div>
                <div className="text-xs text-muted">Từ ngày</div>
                <div className="text-sm font-medium">{benchmark.dateRange.min?.slice(0, 10) ?? "—"}</div>
              </div>
              <div>
                <div className="text-xs text-muted">Đến ngày</div>
                <div className="text-sm font-medium">{benchmark.dateRange.max?.slice(0, 10) ?? "—"}</div>
              </div>
              <div>
                <div className="text-xs text-muted">Reach trung bình</div>
                <div className="kpi-value text-lg font-semibold text-neon-cyan">{num(benchmark.reach?.mean)}</div>
              </div>
              <div>
                <div className="text-xs text-muted">ER trung bình</div>
                <div className="kpi-value text-lg font-semibold text-neon-green">{pct(benchmark.engagementRate?.mean)}</div>
              </div>
            </div>
          </div>

          {/* Insights */}
          {benchmark.insights.length > 0 && (
            <div className="glass-card p-5">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="w-4 h-4 text-neon-purple" />
                <h3 className="font-medium text-sm" style={{ color: "var(--text-main)" }}>Insights</h3>
              </div>
              <ul className="space-y-1.5 text-sm">
                {benchmark.insights.map((ins, i) => (
                  <li key={i} className="flex gap-2" style={{ color: "var(--text-dim)" }}>
                    <span className="text-neon-purple">•</span>
                    <span>{ins}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Percentile stats */}
          <div>
            <div className="section-title">
              <span className="section-title-tag">Stats</span>
              <h3 className="font-medium text-sm" style={{ color: "var(--text-main)" }}>Phân phối metric</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <StatCard label="Reach" stats={benchmark.reach} />
              <StatCard label="Reactions" stats={benchmark.reactions} />
              <StatCard label="Comments" stats={benchmark.comments} />
              <StatCard label="Shares" stats={benchmark.shares} />
              <StatCard label="Engagement Rate" stats={benchmark.engagementRate} format="pct" />
              <StatCard label="Video Views" stats={benchmark.videoViews} />
            </div>
          </div>

          {/* By topic */}
          {benchmark.byTopic.length > 1 && (
            <div>
              <div className="section-title">
                <span className="section-title-tag">Topic</span>
                <h3 className="font-medium text-sm" style={{ color: "var(--text-main)" }}>Hiệu suất theo chủ đề</h3>
              </div>
              <div className="table-wrap overflow-x-auto scrollbar-thin">
                <table className="table">
                  <thead><tr>
                    <th>Chủ đề</th>
                    <th className="text-right">Bài</th>
                    <th className="text-right">Avg Reach</th>
                    <th className="text-right">Avg Reactions</th>
                    <th className="text-right">Avg Comments</th>
                    <th className="text-right">Avg ER</th>
                  </tr></thead>
                  <tbody>
                    {benchmark.byTopic.map((t) => (
                      <tr key={t.topic}>
                        <td><span className="badge-info">{t.topicLabel}</span></td>
                        <td className="text-right mono">{t.postCount}</td>
                        <td className="text-right mono">{num(t.avgReach)}</td>
                        <td className="text-right mono">{num(t.avgReactions)}</td>
                        <td className="text-right mono">{num(t.avgComments)}</td>
                        <td className="text-right mono text-neon-green">{pct(t.avgER)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* By post type */}
          {benchmark.byType.length > 1 && (
            <div>
              <div className="section-title">
                <span className="section-title-tag">Type</span>
                <h3 className="font-medium text-sm" style={{ color: "var(--text-main)" }}>Hiệu suất theo loại bài</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {benchmark.byType.map((tp) => (
                  <div key={tp.postType} className="glass-card p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="badge-neutral">{tp.postType}</span>
                      <span className="text-xs text-faint">{tp.postCount} bài</span>
                    </div>
                    <div className="space-y-1 text-xs">
                      <div className="flex justify-between"><span className="text-faint">Avg Reach</span><span className="mono">{num(tp.avgReach)}</span></div>
                      <div className="flex justify-between"><span className="text-faint">Avg Reactions</span><span className="mono">{num(tp.avgReactions)}</span></div>
                      <div className="flex justify-between"><span className="text-faint">Avg ER</span><span className="mono text-neon-green">{pct(tp.avgER)}</span></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Weekday + Hour charts */}
          {weekdayData.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="glass-card p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Calendar className="w-4 h-4 text-neon-cyan" />
                  <h3 className="font-medium text-sm" style={{ color: "var(--text-main)" }}>Avg Reach theo ngày trong tuần</h3>
                </div>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={weekdayData} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={t.grid} vertical={false} />
                    <XAxis dataKey="name" stroke={t.axis} fontSize={11} tickLine={false} axisLine={false} />
                    <YAxis stroke={t.axis} fontSize={11} tickLine={false} axisLine={false} width={48} tickFormatter={(v) => formatNumber(v)} />
                    <Tooltip contentStyle={{ background: t.tooltipBg, border: `1px solid ${t.tooltipBorder}`, borderRadius: 8, fontSize: 12 }} />
                    <Bar dataKey="reach" radius={[6, 6, 0, 0]} maxBarSize={40}>
                      {weekdayData.map((_, i) => <Cell key={i} fill={t.palette[i % t.palette.length]} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="glass-card p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Clock className="w-4 h-4 text-neon-pink" />
                  <h3 className="font-medium text-sm" style={{ color: "var(--text-main)" }}>Avg Reach theo khung giờ</h3>
                </div>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={hourData} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={t.grid} vertical={false} />
                    <XAxis dataKey="name" stroke={t.axis} fontSize={10} tickLine={false} axisLine={false} />
                    <YAxis stroke={t.axis} fontSize={11} tickLine={false} axisLine={false} width={48} tickFormatter={(v) => formatNumber(v)} />
                    <Tooltip contentStyle={{ background: t.tooltipBg, border: `1px solid ${t.tooltipBorder}`, borderRadius: 8, fontSize: 12 }} />
                    <Bar dataKey="reach" radius={[6, 6, 0, 0]} maxBarSize={50}>
                      {hourData.map((_, i) => <Cell key={i} fill={t.palette[(i + 2) % t.palette.length]} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Correlations */}
          {benchmark.correlations.reachVsShares != null && (
            <div className="glass-card p-4">
              <div className="flex items-center gap-2 mb-3">
                <Layers className="w-4 h-4 text-neon-amber" />
                <h3 className="font-medium text-sm" style={{ color: "var(--text-main)" }}>Tương quan giữa các metric (Pearson r)</h3>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                {[
                  ["Reach ↔ Reactions", benchmark.correlations.reachVsReactions],
                  ["Reach ↔ Comments", benchmark.correlations.reachVsComments],
                  ["Reach ↔ Shares", benchmark.correlations.reachVsShares],
                  ["Reactions ↔ Comments", benchmark.correlations.reactionsVsComments],
                ].map(([label, val]) => (
                  <div key={label as string} className="text-center p-2 rounded-lg" style={{ background: "rgba(168,85,247,0.05)" }}>
                    <div className="text-xs text-muted">{label}</div>
                    <div className={`kpi-value text-lg font-bold ${
                      typeof val === "number" && val > 0.7 ? "text-neon-green" :
                      typeof val === "number" && val > 0.4 ? "text-neon-amber" : "text-faint"
                    }`}>
                      {typeof val === "number" ? val.toFixed(2) : "—"}
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-xs text-faint mt-2">
                r &gt; 0.7 = tương quan mạnh · 0.4-0.7 = trung bình · &lt; 0.4 = yếu
              </p>
            </div>
          )}

          {/* Top posts by reach */}
          {benchmark.topReachPosts.length > 0 && (
            <div>
              <div className="section-title">
                <span className="section-title-tag">Top</span>
                <h3 className="font-medium text-sm" style={{ color: "var(--text-main)" }}>Top 10 bài theo Reach</h3>
              </div>
              <div className="space-y-1.5">
                {benchmark.topReachPosts.map((p, i) => (
                  <div key={p.fbPostId} className="glass-card p-3 flex items-start gap-3">
                    <div className="w-6 h-6 rounded-lg text-xs font-bold flex items-center justify-center shrink-0 text-white bg-grad-main">
                      {i + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm line-clamp-1" style={{ color: "var(--text-main)" }}>
                        {p.message || "(không có nội dung)"}
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-xs text-muted flex-wrap">
                        <span className="mono text-neon-purple">👁 {num(p.reach)}</span>
                        <span className="mono">❤️ {p.reactionsCount}</span>
                        <span className="mono">💬 {p.commentsCount}</span>
                        <span className="mono">🔁 {p.sharesCount}</span>
                        <span className="mono text-neon-green">ER {pct(p.engagementRate)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Ready for competitor comparison */}
          <div className="glass-card p-5" style={{ borderColor: "var(--border-hot)" }}>
            <div className="flex items-center gap-3 mb-2">
              <BarChart3 className="w-5 h-5 text-neon-pink" />
              <h3 className="font-semibold" style={{ color: "var(--text-main)" }}>Sẵn sàng cho so sánh đối thủ</h3>
            </div>
            <p className="text-sm text-muted">
              Khi bạn import CSV từ Meta Business Suite cho kỳ dài hơn (Jan-Jul 2026),
              internal benchmark sẽ tự cập nhật. Sau đó, bạn có thể vào{" "}
              <Link href="/benchmark" className="text-neon-purple hover:underline">/benchmark</Link>{" "}
              để so sánh pattern nội bộ với competitor (cần import competitor CSV).
            </p>
          </div>
        </div>
      )}
    </>
  );
}
