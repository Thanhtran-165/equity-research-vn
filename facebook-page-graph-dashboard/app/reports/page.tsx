"use client";

import { useCallback, useEffect, useState } from "react";
import { FileText, Download, Printer, Sparkles } from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import ErrorBox from "@/components/ErrorBox";
import EmptyState from "@/components/ui/EmptyState";
import Segmented from "@/components/ui/Segmented";
import TopicPerformanceTable, { type TopicPerformanceRow } from "@/components/TopicPerformanceTable";

interface WeeklyReportData {
  weekStart: string;
  weekEnd: string;
  reachTotal: number;
  engagementTotal: number;
  followerDelta: number;
  topReachPost?: any | null;
  topCommentPost?: any | null;
  topEngagementRatePost?: any | null;
  topTopic: string | null;
  topTopicLabel: string | null;
  topicComparison: TopicPerformanceRow[];
  moderationRiskSummary: { total: number; high: number; medium: number; low: number };
  commentSpikes: { fbPostId: string; commentsCount: number; median: number }[];
  summary: string;
  recommendation: string;
}

interface ApiError {
  code?: string;
  message: string;
  details?: any;
}

const num = (v: number | null | undefined) =>
  v == null ? "—" : v.toLocaleString("vi-VN");

export default function ReportsPage() {
  const [weeksAgo, setWeeksAgo] = useState<"0" | "1" | "2" | "3">("0");
  const [data, setData] = useState<WeeklyReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`/api/fb/reports/weekly?weeksAgo=${weeksAgo}`).then((x) => x.json());
      if (r.ok) setData(r.data);
      else setError(r.error);
    } catch (e: any) {
      setError({ message: e?.message ?? String(e) });
    } finally {
      setLoading(false);
    }
  }, [weeksAgo]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <>
      <div className="no-print">
        <PageHeader
          title="Báo cáo tuần"
          subtitle="Tổng hợp từ database — print-friendly (Ctrl+P để in/PDF)"
          icon={<FileText className="w-5 h-5" />}
          actions={
            <>
              <Segmented
                value={weeksAgo}
                onChange={(v) => setWeeksAgo(v as any)}
                size="sm"
                options={[
                  { value: "0", label: "Tuần này" },
                  { value: "1", label: "Tuần trước" },
                  { value: "2", label: "-2" },
                  { value: "3", label: "-3" },
                ]}
              />
              <button onClick={() => window.print()} className="btn-secondary">
                <Printer className="w-4 h-4" />
                <span className="hidden sm:inline">In / PDF</span>
              </button>
              <a href="/api/fb/export/posts" className="btn-secondary">
                <Download className="w-4 h-4" />
                <span className="hidden sm:inline">CSV</span>
              </a>
              <button onClick={load} className="btn-primary">
                ↻ <span className="hidden sm:inline">Tạo lại</span>
              </button>
            </>
          }
        />
      </div>

      {error && <div className="no-print mb-4"><ErrorBox title="Không tạo được báo cáo" error={error} onRetry={load} /></div>}

      {loading && (
        <div className="no-print space-y-3">
          <div className="skeleton h-24 w-full" />
          <div className="skeleton h-64 w-full" />
        </div>
      )}

      {!loading && !data && !error && (
        <EmptyState
          title="Chưa có báo cáo"
          description="Sync Facebook Data trước, sau đó bấm Tạo lại."
        />
      )}

      {!loading && data && (
        <article className="space-y-5">
          {/* Header cho print */}
          <header className="card p-6">
            <div className="flex items-start justify-between flex-wrap gap-3">
              <div>
                <div className="text-xs uppercase tracking-widest text-muted">BÁO CÁO HIỆU SUẤT TUẦN</div>
                <h1 className="text-2xl font-semibold mt-1">
                  {data.weekStart} → {data.weekEnd}
                </h1>
                {data.topTopicLabel && (
                  <div className="text-sm text-muted mt-1">
                    Chủ đề nổi bật: <span className="font-medium text-brand-600 dark:text-brand-400">{data.topTopicLabel}</span>
                  </div>
                )}
              </div>
              <div className="text-xs text-muted text-right">
                <div>Tạo lúc {new Date().toLocaleString("vi-VN")}</div>
                <div className="mt-0.5">facebook-page-graph-dashboard</div>
              </div>
            </div>
          </header>

          {/* Narrative summary — điểm nhấn */}
          <section className="card p-5 border-brand-200 dark:border-brand-500/30 bg-gradient-to-br from-brand-50/50 to-transparent dark:from-brand-500/5">
            <div className="flex items-start gap-3">
              <Sparkles className="w-5 h-5 text-brand-600 dark:text-brand-400 shrink-0 mt-0.5" />
              <div>
                <h2 className="font-semibold mb-1.5">Tóm tắt tuần</h2>
                <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed">
                  {data.summary}
                </p>
                {data.recommendation && (
                  <div className="mt-3 p-3 rounded-lg bg-white/60 dark:bg-slate-900/60 border border-brand-100 dark:border-brand-500/20">
                    <div className="text-xs uppercase tracking-wide text-brand-700 dark:text-brand-400 mb-0.5">
                      Khuyến nghị
                    </div>
                    <p className="text-sm text-slate-700 dark:text-slate-200">{data.recommendation}</p>
                  </div>
                )}
              </div>
            </div>
          </section>

          {/* KPI grid */}
          <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KpiBox label="Tổng reach" value={num(data.reachTotal)} />
            <KpiBox label="Tổng tương tác" value={num(data.engagementTotal)} />
            <KpiBox
              label="Follower delta"
              value={`${data.followerDelta > 0 ? "+" : ""}${num(data.followerDelta)}`}
              tone={data.followerDelta > 0 ? "success" : data.followerDelta < 0 ? "danger" : "neutral"}
            />
            <KpiBox
              label="Comment rủi ro cao"
              value={num(data.moderationRiskSummary.high)}
              tone={data.moderationRiskSummary.high > 0 ? "danger" : "neutral"}
              hint={`trên tổng ${data.moderationRiskSummary.total}`}
            />
          </section>

          {/* Top posts */}
          <section className="card p-5">
            <h2 className="font-semibold mb-3">Top bài viết</h2>
            <div className="space-y-3">
              <TopPostRow label="Reach cao nhất" post={data.topReachPost} metric="reach" />
              <TopPostRow label="Comment nhiều nhất" post={data.topCommentPost} metric="commentsCount" />
              <TopPostRow label="Engagement rate cao nhất" post={data.topEngagementRatePost} metric="engagementRate" />
            </div>
          </section>

          {/* Topic comparison */}
          <section>
            <h2 className="font-semibold mb-2">So sánh chủ đề</h2>
            <TopicPerformanceTable rows={data.topicComparison} />
          </section>

          {/* Spikes */}
          {data.commentSpikes.length > 0 && (
            <section className="card p-5 border-warning-200 dark:border-warning-500/30 bg-warning-50/50 dark:bg-warning-500/5">
              <h2 className="font-semibold text-warning-800 dark:text-warning-400 mb-2">
                ⚠️ Comment spike ({data.commentSpikes.length})
              </h2>
              <ul className="text-sm space-y-1">
                {data.commentSpikes.map((s) => (
                  <li key={s.fbPostId}>
                    <span className="font-mono text-xs">{s.fbPostId.slice(-12)}</span>:
                    <strong className="mx-1">{s.commentsCount}</strong> comments (median = {s.median})
                  </li>
                ))}
              </ul>
            </section>
          )}
        </article>
      )}
    </>
  );
}

function KpiBox({
  label,
  value,
  hint,
  tone = "neutral",
}: {
  label: string;
  value: React.ReactNode;
  hint?: string;
  tone?: "neutral" | "success" | "danger";
}) {
  const toneCls =
    tone === "success"
      ? "text-success-600 dark:text-success-500"
      : tone === "danger"
      ? "text-danger-600 dark:text-danger-500"
      : "";
  return (
    <div className="card p-4">
      <div className="text-xs text-muted uppercase tracking-wide">{label}</div>
      <div className={`text-2xl font-semibold tabular-nums ${toneCls}`}>{value}</div>
      {hint && <div className="text-xs text-muted">{hint}</div>}
    </div>
  );
}

function TopPostRow({ label, post, metric }: { label: string; post?: any | null; metric: string }) {
  if (!post) return null;
  const metricLabel: Record<string, string> = {
    reach: "reach",
    commentsCount: "comments",
    engagementRate: "ER",
  };
  const val =
    metric === "engagementRate"
      ? post.engagementRate == null
        ? "—"
        : `${(post.engagementRate * 100).toFixed(2)}%`
      : (post[metric] ?? 0).toLocaleString("vi-VN");
  return (
    <div className="flex items-start gap-3 text-sm border-b border-slate-100 dark:border-slate-800 pb-3 last:border-0 last:pb-0">
      <div className="w-32 shrink-0 text-muted text-xs uppercase tracking-wide pt-0.5">{label}</div>
      <div className="flex-1 min-w-0">
        <div className="text-slate-700 dark:text-slate-200 line-clamp-2">{post.message}</div>
        <div className="text-xs text-muted mt-0.5 tabular-nums">
          {metricLabel[metric]}: <strong>{val}</strong>
        </div>
      </div>
    </div>
  );
}
