"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Trophy,
  Users,
  TrendingUp,
  Flame,
  Tag,
  LayoutGrid,
  Activity,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
} from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import ErrorBox from "@/components/ErrorBox";
import EmptyState from "@/components/ui/EmptyState";
import Segmented from "@/components/ui/Segmented";
import { formatNumber } from "@/components/charts/chartTheme";
import AutoCollectionPanel from "./AutoCollectionPanel";
import AddPeerPanel from "./AddPeerPanel";
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

// ─── Types ──────────────────────────────────────────────

interface Summary {
  totalPages: number;
  externalCorePeers: number;
  ownPages: number;
  directLeaderboardEntities: number;
  referenceSources: number;
  watchlistSources: number;
  totalExternalSources: number;
  totalSourcesIncludingOwnPage: number;
  corePeers: number; // legacy alias for externalCorePeers
  ownPagePresent: boolean;
  ownPageId: number | null;
  totalPosts: number;
  coverage: { reactions: number; comments: number; shares: number };
  pagesByRole: Record<string, number>;
  pagesByScaleBand: Record<string, number>;
  pagesWithPostCount: number;
  pagesWithoutPosts: number;
}

interface LeaderboardRow {
  pageId: number;
  name: string;
  canonicalUrl: string;
  isOwnPage: boolean;
  scaleBand: string | null;
  category: string | null;
  audienceCount: number | null;
  postsCaptured: number;
  medianComparableEngagementPerPost: number | null;
  avgComparableEngagementPerPost: number | null;
  totalComparableEngagement: number | null;
  shareRatio: number | null;
  commentRatio: number | null;
  viralHitRate: number | null;
  metricCoverageScore: number | null;
  engagementPerFollower: number | null;
}

interface QualityCheck {
  id: string;
  label: string;
  status: "pass" | "warn" | "fail";
  detail: string;
  metric?: number;
}

interface QualityReport {
  overall: "pass" | "warn" | "fail";
  checks: QualityCheck[];
  summary: string;
}

interface OwnVsMedianData {
  ownPage: {
    id: number;
    name: string;
    audienceCount: number | null;
    postsCaptured: number;
    medianComparableEngagementPerPost: number | null;
    avgComparableEngagementPerPost: number | null;
    totalComparableEngagement: number | null;
    viralHitRate: number | null;
    shareRatio: number | null;
    commentRatio: number | null;
    metricCoverageScore: number | null;
    engagementPerFollower: number | null;
  };
  peerMedian: {
    medianComparableEngagementPerPost: number | null;
    avgReactionsPerPost: number | null;
    avgCommentsPerPost: number | null;
    viralHitRate: number | null;
    shareRatio: number | null;
    commentRatio: number | null;
    metricCoverageScore: number | null;
    peerCount: number;
  };
}

interface ViralPost {
  id: number;
  postUrl: string;
  postedAt: string | null;
  textSnippet: string | null;
  contentType: string | null;
  topicTag: string | null;
  reactions: number | null;
  comments: number | null;
  shares: number | null;
  comparableEngagement: number | null;
  shareRatio: number | null;
  page: { name: string; isOwnPage: boolean; scaleBand: string | null };
}

interface TopicAgg {
  topic: string;
  postsCaptured: number;
  medianComparableEngagementPerPost: number | null;
  avgComparableEngagementPerPost: number | null;
}

interface TopicsResponse {
  topics: TopicAgg[];
  sampleWarning?: string | null;
}

interface FormatAgg {
  format: string;
  postsCaptured: number;
  medianComparableEngagementPerPost: number | null;
  avgComparableEngagementPerPost: number | null;
}

interface FormatsResponse {
  formats: FormatAgg[];
  sampleWarning?: string | null;
  sharesNote?: string | null;
}

// ─── Helpers ────────────────────────────────────────────

function fmt(n: number | null | undefined, suffix = ""): string {
  if (n == null || !Number.isFinite(n)) return "—";
  return formatNumber(Math.round(n)) + suffix;
}

function pct(n: number | null | undefined): string {
  if (n == null || !Number.isFinite(n)) return "—";
  return `${(n * 100).toFixed(1)}%`;
}

function statusColor(status: "pass" | "warn" | "fail"): string {
  if (status === "pass") return "text-emerald-500";
  if (status === "warn") return "text-amber-500";
  return "text-rose-500";
}

function statusBg(status: "pass" | "warn" | "fail"): string {
  if (status === "pass") return "bg-emerald-500/10 border-emerald-500/30";
  if (status === "warn") return "bg-amber-500/10 border-amber-500/30";
  return "bg-rose-500/10 border-rose-500/30";
}

// ─── Page ───────────────────────────────────────────────

export default function PublicBenchmarkPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [quality, setQuality] = useState<QualityReport | null>(null);
  const [leaderboard, setLeaderboard] = useState<{ rows: LeaderboardRow[] } | null>(null);
  const [ownVsMedian, setOwnVsMedian] = useState<OwnVsMedianData | null>(null);
  const [viral, setViral] = useState<{ posts: ViralPost[] } | null>(null);
  const [topics, setTopics] = useState<TopicsResponse | null>(null);
  const [formats, setFormats] = useState<FormatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [leaderboardMode, setLeaderboardMode] = useState("direct");
  const [leaderboardScale, setLeaderboardScale] = useState("all");
  const [periodDays, setPeriodDays] = useState("30");

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, q] = await Promise.all([
        fetch("/api/public-benchmark/summary").then((r) => r.json()),
        fetch("/api/public-benchmark/data-quality").then((r) => r.json()),
      ]);
      setSummary(s);
      setQuality(q);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchLeaderboard = useCallback(async () => {
    const scaleParam = leaderboardScale !== "all" ? `&scaleBand=${leaderboardScale}` : "";
    const data = await fetch(
      `/api/public-benchmark/leaderboard?mode=${leaderboardMode}${scaleParam}&periodDays=${periodDays}`,
    ).then((r) => r.json());
    setLeaderboard(data);
  }, [leaderboardMode, leaderboardScale, periodDays]);

  useEffect(() => { fetchAll(); }, [fetchAll]);
  useEffect(() => { fetchLeaderboard(); }, [fetchLeaderboard]);

  useEffect(() => {
    fetch(`/api/public-benchmark/own-vs-median?periodDays=${periodDays}`).then((r) => r.json()).then(setOwnVsMedian).catch(() => {});
    fetch(`/api/public-benchmark/viral?limit=10&periodDays=${periodDays}`).then((r) => r.json()).then(setViral).catch(() => {});
    fetch(`/api/public-benchmark/topics?periodDays=${periodDays}`).then((r) => r.json()).then(setTopics).catch(() => {});
    fetch(`/api/public-benchmark/formats?periodDays=${periodDays}`).then((r) => r.json()).then(setFormats).catch(() => {});
  }, [periodDays]);

  if (loading && !summary) {
    return (
      <div className="p-6">
        <PageHeader title="Public Benchmark" subtitle="So sánh tương tác công khai với peer pages" icon={<Trophy className="w-5 h-5" />} />
        <div className="text-muted animate-pulse">Đang tải…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 space-y-4">
        <PageHeader title="Public Benchmark" subtitle="So sánh tương tác công khai" icon={<Trophy className="w-5 h-5" />} />
        <ErrorBox error={error} onRetry={fetchAll} />
      </div>
    );
  }

  if (!summary || summary.totalPages === 0) {
    return (
      <div className="p-6 space-y-4">
        <PageHeader title="Public Benchmark" subtitle="So sánh tương tác công khai" icon={<Trophy className="w-5 h-5" />} />
        <EmptyState
          title="Chưa seed Peer Set"
          description={<span>Chạy <code className="px-1 py-0.5 rounded bg-slate-200 dark:bg-slate-700">npm run benchmark:seed-peers</code> để nạp danh sách peer.</span>}
          action={<a href="/public-benchmark/import" className="btn-primary text-sm px-4 py-2 rounded-lg">Đi đến Import</a>}
        />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Public Benchmark"
        subtitle="So sánh tương tác công khai (reactions + comments) với peer pages"
        icon={<Trophy className="w-5 h-5" />}
        actions={
          <div className="flex items-center gap-2">
            <a href="/public-benchmark/import" className="text-sm text-cyan-400 hover:text-cyan-300 flex items-center gap-1">
              Nhập dữ liệu <ArrowRight className="w-3.5 h-3.5" />
            </a>
            <a href="/public-benchmark/collection" className="text-sm text-cyan-400 hover:text-cyan-300 flex items-center gap-1">
              Thu thập <ArrowRight className="w-3.5 h-3.5" />
            </a>
          </div>
        }
      />

      {/* ── Preliminary data warning ──────────────────────── */}
      {summary.totalPosts > 0 && summary.totalPosts < 80 && (
        <div className="card p-3 border-l-4 border-amber-500/50 flex items-center gap-2 text-sm">
          <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0" />
          <span className="text-muted">
            <strong className="text-amber-500">Pilot observation.</strong> Current data ({summary.totalPosts} posts) is insufficient for strong conclusions.
            All rankings show <em>preliminary signals</em> — requires more collection periods before peer-level insights are reliable.
          </span>
        </div>
      )}

      {/* ── Auto-Collection Panel ─────────────────────────── */}
      <AutoCollectionPanel />

      {/* ── Add Peer Panel ────────────────────────────────── */}
      <AddPeerPanel />

      {/* ── Section 1: Summary cards ─────────────────────── */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard icon={<Users className="w-4 h-4" />} label="Total sources" value={fmt(summary.totalSourcesIncludingOwnPage)} sub={`${summary.externalCorePeers} external peers + ${summary.ownPages} own page`} />
        <MetricCard icon={<Activity className="w-4 h-4" />} label="Posts collected" value={fmt(summary.totalPosts)} sub={`${summary.pagesWithPostCount}/${summary.totalPages} pages có data`} />
        <MetricCard
          icon={<TrendingUp className="w-4 h-4" />}
          label="Reactions coverage"
          value={pct(summary.coverage?.reactions)}
          sub={`Comments: ${pct(summary.coverage?.comments)}`}
        />
        <MetricCard
          icon={<ShieldCheck className="w-4 h-4" />}
          label="Data quality"
          value={quality?.overall ? quality.overall.toUpperCase() : "—"}
          valueClass={quality ? statusColor(quality.overall) : ""}
          sub={quality?.summary ?? ""}
        />
      </section>

      {/* ── Section 2: Quality checks ────────────────────── */}
      {quality && quality.checks && (
        <section>
          <h2 className="text-sm font-semibold text-muted uppercase tracking-wide mb-3">Data Quality</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {(quality?.checks ?? []).map((c) => (
              <div key={c.id} className={`card border p-3 flex items-start gap-3 ${statusBg(c.status)}`}>
                <div className={`mt-0.5 ${statusColor(c.status)}`}>
                  {c.status === "pass" ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-muted">{c.id} · {c.label}</div>
                  <div className="text-sm truncate">{c.detail}</div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── Section 3: Own vs Median ─────────────────────── */}
      {ownVsMedian && ownVsMedian.ownPage && ownVsMedian.peerMedian && (
        <section>
          <h2 className="text-sm font-semibold text-muted uppercase tracking-wide mb-3">Chim Cút vs Peer Median</h2>
          <div className="card p-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            <CompareMetric
              label="Median comparable engagement/post"
              own={ownVsMedian.ownPage.medianComparableEngagementPerPost}
              peer={ownVsMedian.peerMedian.medianComparableEngagementPerPost}
            />
            <CompareMetric
              label="Viral hit rate"
              own={ownVsMedian.ownPage.viralHitRate}
              peer={ownVsMedian.peerMedian.viralHitRate}
              isPct
            />
            <CompareMetric
              label="Share ratio"
              own={ownVsMedian.ownPage.shareRatio}
              peer={ownVsMedian.peerMedian.shareRatio}
              isPct
            />
            <CompareMetric
              label="Comment ratio"
              own={ownVsMedian.ownPage.commentRatio}
              peer={ownVsMedian.peerMedian.commentRatio}
              isPct
            />
          </div>
        </section>
      )}

      {/* ── Section 4: Leaderboard ───────────────────────── */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-muted uppercase tracking-wide flex items-center gap-2">
            <Trophy className="w-4 h-4" /> Leaderboard
          </h2>
          <div className="flex items-center gap-3">
            <Segmented
              value={leaderboardMode}
              onChange={setLeaderboardMode}
              options={[
                { label: "Direct", value: "direct" },
                { label: "All", value: "all" },
              ]}
            />
            <Segmented
              value={leaderboardScale}
              onChange={setLeaderboardScale}
              options={[
                { label: "All scale", value: "all" },
                { label: "micro", value: "micro" },
                { label: "small", value: "small" },
                { label: "medium", value: "medium" },
              ]}
            />
            <Segmented
              value={periodDays}
              onChange={setPeriodDays}
              options={[
                { label: "7d", value: "7" },
                { label: "30d", value: "30" },
                { label: "90d", value: "90" },
              ]}
            />
          </div>
        </div>
        <LeaderboardTable rows={leaderboard?.rows ?? []} />
      </section>

      {/* ── Section 5: Viral posts ───────────────────────── */}
      <section>
        <h2 className="text-sm font-semibold text-muted uppercase tracking-wide mb-3 flex items-center gap-2">
          <Flame className="w-4 h-4" /> Top viral posts
        </h2>
        {viral && viral.posts && viral.posts.length > 0 ? (
          <div className="card overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800/50 text-xs text-muted">
                <tr>
                  <th className="text-left p-2 font-medium">Page</th>
                  <th className="text-left p-2 font-medium">Post</th>
                  <th className="text-right p-2 font-medium">Reactions</th>
                  <th className="text-right p-2 font-medium">Comments</th>
                  <th className="text-right p-2 font-medium">Shares</th>
                  <th className="text-right p-2 font-medium">Comp. Eng.</th>
                </tr>
              </thead>
              <tbody>
                {(viral?.posts ?? []).map((p) => (
                  <tr key={p.id} className="border-t border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td className="p-2 whitespace-nowrap">
                      <span className={p.page.isOwnPage ? "text-cyan-400 font-medium" : ""}>{p.page.name}</span>
                    </td>
                    <td className="p-2 max-w-xs truncate">
                      <a href={p.postUrl} target="_blank" rel="noopener noreferrer" className="text-cyan-500 hover:underline truncate block">
                        {p.textSnippet || p.postUrl}
                      </a>
                    </td>
                    <td className="p-2 text-right tabular-nums">{fmt(p.reactions)}</td>
                    <td className="p-2 text-right tabular-nums">{fmt(p.comments)}</td>
                    <td className="p-2 text-right tabular-nums">{fmt(p.shares)}</td>
                    <td className="p-2 text-right tabular-nums font-semibold text-emerald-500">{fmt(p.comparableEngagement)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="card p-4 text-sm text-muted">Chưa có viral posts.</div>
        )}
      </section>

      {/* ── Section 6+7: Topics & Formats ─────────────────── */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div>
          <TopicFormatCard title="Topics" icon={<Tag className="w-4 h-4" />} data={(topics?.topics ?? []) as { topic: string; postsCaptured: number; medianComparableEngagementPerPost: number | null }[]} field="topic" />
          {topics?.sampleWarning && (
            <div className="text-xs text-amber-500 mt-1 px-1">{topics.sampleWarning}</div>
          )}
        </div>
        <div>
          <TopicFormatCard title="Formats" icon={<LayoutGrid className="w-4 h-4" />} data={(formats?.formats ?? []) as { format: string; postsCaptured: number; medianComparableEngagementPerPost: number | null }[]} field="format" />
          {formats?.sampleWarning && (
            <div className="text-xs text-amber-500 mt-1 px-1">{formats.sampleWarning}</div>
          )}
          {formats?.sharesNote && (
            <div className="text-xs text-muted mt-0.5 px-1">{formats.sharesNote}</div>
          )}
        </div>
      </section>
    </div>
  );
}

// ─── Components ─────────────────────────────────────────

function MetricCard({ icon, label, value, sub, valueClass = "" }: {
  icon: React.ReactNode; label: string; value: string; sub?: string; valueClass?: string;
}) {
  return (
    <div className="card p-4">
      <div className="flex items-center gap-2 text-xs text-muted mb-1">
        {icon} {label}
      </div>
      <div className={`text-2xl font-bold tabular-nums ${valueClass}`}>{value}</div>
      {sub && <div className="text-xs text-muted mt-1">{sub}</div>}
    </div>
  );
}

function CompareMetric({ label, own, peer, isPct = false }: {
  label: string; own: number | null; peer: number | null; isPct?: boolean;
}) {
  const ownVal = isPct ? pct(own) : fmt(own);
  const peerVal = isPct ? pct(peer) : fmt(peer);
  const diff = own != null && peer != null && peer > 0 ? ((own - peer) / peer) * 100 : null;
  return (
    <div>
      <div className="text-xs text-muted mb-1">{label}</div>
      <div className="flex items-baseline gap-2">
        <span className="text-lg font-bold text-cyan-400 tabular-nums">{ownVal}</span>
        {diff != null && (
          <span className={`text-xs font-medium ${diff >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
            {diff >= 0 ? "+" : ""}{diff.toFixed(0)}%
          </span>
        )}
      </div>
      <div className="text-xs text-muted">Peer median: {peerVal}</div>
    </div>
  );
}

function LeaderboardTable({ rows }: { rows: LeaderboardRow[] }) {
  if (rows.length === 0) {
    return <div className="card p-4 text-sm text-muted">Chưa có data leaderboard.</div>;
  }
  return (
    <div className="card overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 dark:bg-slate-800/50 text-xs text-muted">
          <tr>
            <th className="text-left p-2 font-medium">#</th>
            <th className="text-left p-2 font-medium">Page</th>
            <th className="text-left p-2 font-medium">Scale</th>
            <th className="text-right p-2 font-medium">Posts</th>
            <th className="text-right p-2 font-medium">Followers</th>
            <th className="text-right p-2 font-medium">Median Comp. Eng.</th>
            <th className="text-right p-2 font-medium">Avg Comp. Eng.</th>
            <th className="text-right p-2 font-medium">Share %</th>
            <th className="text-right p-2 font-medium">Viral %</th>
            <th className="text-right p-2 font-medium">Coverage</th>
          </tr>
        </thead>
        <tbody>
          {(rows ?? []).map((r, i) => (
            <tr key={r.pageId} className={`border-t border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/30 ${r.isOwnPage ? "bg-cyan-500/5" : ""}`}>
              <td className="p-2 text-muted tabular-nums">{i + 1}</td>
              <td className="p-2">
                <a href={r.canonicalUrl} target="_blank" rel="noopener noreferrer" className={`hover:underline ${r.isOwnPage ? "text-cyan-400 font-medium" : ""}`}>
                  {r.name}
                </a>
              </td>
              <td className="p-2 text-xs text-muted">{r.scaleBand ?? "—"}</td>
              <td className="p-2 text-right tabular-nums">{r.postsCaptured}</td>
              <td className="p-2 text-right tabular-nums">{fmt(r.audienceCount)}</td>
              <td className="p-2 text-right tabular-nums font-semibold">{fmt(r.medianComparableEngagementPerPost)}</td>
              <td className="p-2 text-right tabular-nums text-muted">{fmt(r.avgComparableEngagementPerPost)}</td>
              <td className="p-2 text-right tabular-nums">{pct(r.shareRatio)}</td>
              <td className="p-2 text-right tabular-nums">{pct(r.viralHitRate)}</td>
              <td className="p-2 text-right tabular-nums">{pct(r.metricCoverageScore)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TopicFormatCard({ title, icon, data, field }: {
  title: string; icon: React.ReactNode; data: { topic?: string; format?: string; postsCaptured: number; medianComparableEngagementPerPost: number | null }[]; field: string;
}) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-muted uppercase tracking-wide mb-3 flex items-center gap-2">{icon} {title}</h3>
      {data.length > 0 ? (
        <div className="card p-3 space-y-2">
          {data.slice(0, 8).map((d, i) => (
            <div key={i} className="flex items-center justify-between text-sm">
              <span className="truncate">{String(d[field as keyof typeof d] ?? "unknown")}</span>
              <div className="flex items-center gap-3">
                <span className="text-xs text-muted">{d.postsCaptured} posts</span>
                <span className="font-semibold tabular-nums text-cyan-400 w-16 text-right">
                  {fmt(d.medianComparableEngagementPerPost as number | null)}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card p-4 text-sm text-muted">Chưa có data.</div>
      )}
    </div>
  );
}
