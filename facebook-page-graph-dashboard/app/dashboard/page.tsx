"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Users,
  Eye,
  Heart,
  MessageSquare,
  TrendingUp,
  Flame,
  ArrowRight,
  Video,
  Upload,
  LayoutDashboard,
} from "lucide-react";
import KpiCard from "@/components/ui/KpiCard";
import ErrorBox from "@/components/ErrorBox";
import PageHeader from "@/components/layout/PageHeader";
import Sparkline from "@/components/charts/Sparkline";
import FollowerTrendChart from "@/components/charts/FollowerTrendChart";
import TopicPerformanceChart from "@/components/charts/TopicPerformanceChart";
import PostTypeDonut from "@/components/charts/PostTypeDonut";
import EmptyState from "@/components/ui/EmptyState";
import { useSync } from "@/components/layout/SyncContext";

interface DashboardData {
  page: { pageId: string; pageName: string };
  followers: number;
  followerDelta: number;
  totalTrueReach: number;
  totalVideoViews: number;
  totalPublicEngagement: number;
  metricSourceBreakdown: Record<string, number>;
  totalPosts: number;
  avgEngagementRate: number | null;
  avgEngagementRateNote: string;
  extremeEngagementRateCount?: number;
  extremeEngagementRateWarning?: string | null;
  totalComments: number;
  commentSpikeCount: number;
  commentSpikes: { fbPostId: string; commentsCount: number; median: number; message?: string | null }[];
  topPosts: any[];
  topicPerformance: any[];
  lastSnapshotDate: string | null;
  followerHistory: { date: string; followersCount: number; followersDelta?: number | null }[];
}

interface ApiError {
  code?: string;
  message: string;
  details?: any;
}

const num = (v: number | null | undefined) =>
  v == null ? "—" : v.toLocaleString("vi-VN");
const pct = (v: number | null | undefined) =>
  v == null ? "—" : `${(v * 100).toFixed(2)}%`;

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const { syncNonce, lastSyncResult } = useSync();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch("/api/fb/dashboard").then((x) => x.json());
      if (r.ok) setData(r.data);
      else setError(r.error);
    } catch (e: any) {
      setError({ message: e?.message ?? String(e) });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, syncNonce]);

  const breakdown = data?.metricSourceBreakdown;
  const mbsCount = breakdown?.meta_business_suite_csv ?? 0;
  const apiCount = breakdown?.facebook_graph_api_insights ?? 0;
  const videoCount = breakdown?.facebook_video_metric ?? 0;
  const showExtremeEr = (data?.extremeEngagementRateCount ?? 0) > 0;

  const followerSpark = (data?.followerHistory ?? [])
    .slice(-12)
    .map((s) => s.followersCount);

  const postTypeData = (data?.topPosts ?? []).reduce<Record<string, number>>((acc, p) => {
    const t = p.postType ?? "unknown";
    acc[t] = (acc[t] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <>
      <PageHeader
        title="Dashboard"
        subtitle={
          data?.page?.pageName
            ? `${data.page.pageName} · cập nhật ${data.lastSnapshotDate ?? "chưa sync"}`
            : "Tổng quan hiệu suất Page Facebook của bạn"
        }
        icon={<LayoutDashboard className="w-5 h-5" />}
        actions={
          <Link href="/imports" className="btn-primary">
            <Upload className="w-4 h-4" />
            <span className="hidden sm:inline">Import CSV</span>
          </Link>
        }
      />

      {/* Sync result banner */}
      {lastSyncResult?.ok && (
        <div className="glass-card p-3 mb-5 border-success-500/30 animate-fade-in">
          <div className="flex items-start gap-3 text-sm">
            <span className="text-neon-green mt-0.5">✓</span>
            <div className="flex-1 min-w-0">
              <div className="font-medium" style={{ color: "var(--text-main)" }}>
                Đồng bộ Graph API xong {lastSyncResult.data.syncedPosts} bài
              </div>
              <div className="text-xs text-muted mt-0.5">
                Dữ liệu chi tiết (reach, impressions) được cập nhật qua CSV import từ Meta Business Suite.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Data source indicator */}
      {(mbsCount > 0 || apiCount > 0) && (
        <div className="glass-card p-3 mb-5 animate-fade-in flex items-center gap-3 flex-wrap">
          <span className="text-xs text-muted">Nguồn dữ liệu:</span>
          {mbsCount > 0 && (
            <span className="badge-neon">
              📊 Meta Business Suite CSV ({mbsCount} posts)
            </span>
          )}
          {apiCount > 0 && (
            <span className="badge-cyan">
              🔌 Graph API Insights ({apiCount} posts)
            </span>
          )}
          {videoCount > 0 && (
            <span className="badge-neutral">
              🎥 Video Views ({videoCount} posts)
            </span>
          )}
        </div>
      )}

      {/* Extreme ER warning */}
      {showExtremeEr && (
        <div className="glass-card p-3 mb-5 border-warning-500/30 animate-fade-in">
          <div className="flex items-start gap-3 text-sm">
            <Flame className="w-4 h-4 text-neon-amber shrink-0 mt-0.5" />
            <div style={{ color: "var(--amber)" }}>
              <strong>ER cực đoan:</strong> {data?.extremeEngagementRateWarning}
              {" "}— một số bài có reach thấp + clicks cao (thường là bài chạy ads). Số không bị silently cap.
            </div>
          </div>
        </div>
      )}

      {error && <div className="mb-5"><ErrorBox title="Không tải được dashboard" error={error} onRetry={load} /></div>}

      {/* KPI grid — single mode, hiển thị tất cả metric có trong DB */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 mb-6">
        <KpiCard
          label="Followers"
          value={num(data?.followers)}
          delta={data?.followerDelta}
          icon={<Users className="w-4 h-4" />}
          spark={followerSpark.length >= 2 ? followerSpark : undefined}
          loading={loading}
        />
        <KpiCard
          label="Reach"
          value={num(data?.totalTrueReach)}
          icon={<Eye className="w-4 h-4" />}
          hint={`${mbsCount + apiCount}/${data?.totalPosts ?? 0} bài có reach thật`}
          loading={loading}
        />
        <KpiCard
          label="Video Views"
          value={num(data?.totalVideoViews)}
          icon={<Video className="w-4 h-4" />}
          hint={`${videoCount} bài video/reel`}
          loading={loading}
        />
        <KpiCard
          label="Avg Engagement Rate"
          value={pct(data?.avgEngagementRate)}
          icon={<Heart className="w-4 h-4" />}
          hint={data?.avgEngagementRateNote}
          loading={loading}
        />
        <KpiCard
          label="Comments"
          value={num(data?.totalComments)}
          icon={<MessageSquare className="w-4 h-4" />}
          loading={loading}
        />
      </div>

      {/* Spikes banner */}
      {data && data.commentSpikes.length > 0 && (
        <div className="glass-card p-4 mb-6 border-warning-500/30">
          <div className="flex items-center gap-2 mb-2">
            <Flame className="w-4 h-4 text-neon-amber" />
            <h3 className="font-medium text-sm" style={{ color: "var(--amber)" }}>
              Phát hiện {data.commentSpikes.length} bài comment tăng bất thường
            </h3>
          </div>
          <ul className="space-y-1 text-sm">
            {data.commentSpikes.map((s) => (
              <li key={s.fbPostId} style={{ color: "var(--text-dim)" }}>
                <span className="mono text-xs">{s.fbPostId.slice(-12)}</span>
                {" — "}
                <strong>{s.commentsCount}</strong> comments (median = {s.median})
                {s.message && <span className="ml-2 text-muted line-clamp-1">&ldquo;{s.message}&rdquo;</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <div className="glass-card p-4 lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium text-sm" style={{ color: "var(--text-main)" }}>Xu hướng Followers</h3>
            <span className="text-xs text-muted">{data?.followerHistory?.length ?? 0} snapshot</span>
          </div>
          {loading ? (
            <div className="skeleton h-[240px] w-full" />
          ) : (data?.followerHistory?.length ?? 0) >= 2 ? (
            <FollowerTrendChart
              data={(data!.followerHistory).map((s) => ({
                date: s.date,
                followers: s.followersCount,
              }))}
            />
          ) : (
            <div className="h-[240px] flex items-center justify-center text-sm text-muted">
              Cần ít nhất 2 snapshot (sync nhiều ngày liên tiếp) để xem xu hướng.
            </div>
          )}
        </div>

        <div className="glass-card p-4">
          <h3 className="font-medium text-sm mb-3" style={{ color: "var(--text-main)" }}>Cơ cấu loại bài</h3>
          {loading ? (
            <div className="skeleton h-[220px] w-full" />
          ) : Object.keys(postTypeData).length > 0 ? (
            <>
              <PostTypeDonut
                data={Object.entries(postTypeData).map(([name, value]) => ({ name, value }))}
              />
              <div className="flex flex-wrap gap-2 mt-2 justify-center text-xs">
                {Object.entries(postTypeData).map(([name, value], i) => (
                  <span key={name} className="text-muted">
                    <span
                      className="inline-block w-2 h-2 rounded-full mr-1"
                      style={{ backgroundColor: ["#a855f7", "#06b6d4", "#ec4899", "#10d98a", "#fbbf24"][i % 5] }}
                    />
                    {name}: {value}
                  </span>
                ))}
              </div>
            </>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-sm text-muted">
              Chưa có dữ liệu
            </div>
          )}
        </div>
      </div>

      {/* Topic performance + Top posts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <div className="glass-card p-4">
          <h3 className="font-medium text-sm mb-3" style={{ color: "var(--text-main)" }}>Hiệu suất theo chủ đề</h3>
          {loading ? (
            <div className="skeleton h-[260px] w-full" />
          ) : (data?.topicPerformance?.length ?? 0) > 0 ? (
            <>
              <TopicPerformanceChart data={data!.topicPerformance} metric="reach" />
              <div className="text-xs text-muted mt-2 text-center">Tổng reach theo chủ đề</div>
            </>
          ) : (
            <div className="h-[260px] flex items-center justify-center text-sm text-muted">Chưa có dữ liệu topic</div>
          )}
        </div>

        <div className="glass-card p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium text-sm" style={{ color: "var(--text-main)" }}>Top bài viết</h3>
            <Link href="/posts" className="text-xs text-neon-purple hover:underline flex items-center gap-0.5">
              Tất cả <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          {loading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => <div key={i} className="skeleton h-16 w-full" />)}
            </div>
          ) : (data?.topPosts?.length ?? 0) > 0 ? (
            <div className="space-y-2">
              {data!.topPosts.slice(0, 5).map((p, i) => {
                const metricVal = p.reach ?? p.videoViews ?? p.publicEngagement;
                const isMbs = p.metricSource === "meta_business_suite_csv";
                const isApi = p.metricSource === "facebook_graph_api_insights";
                const metricIcon = isMbs || isApi ? "👁" : p.videoViews != null ? "🎥" : "👥";
                return (
                  <a
                    key={p.fbPostId}
                    href={p.permalinkUrl ?? "#"}
                    target="_blank"
                    rel="noreferrer"
                    className="block p-3 rounded-xl hover:bg-white/5 transition-colors group"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-6 h-6 rounded-lg text-xs font-bold flex items-center justify-center shrink-0 text-white bg-grad-main">
                        {i + 1}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="text-sm line-clamp-2 group-hover:text-neon-purple" style={{ color: "var(--text-main)" }}>
                          {p.message || "(không có nội dung)"}
                        </div>
                        <div className="flex items-center gap-3 mt-1 text-xs text-muted flex-wrap">
                          <span className="badge-info">{p.topic}</span>
                          <span className="mono">
                            {metricIcon} {num(metricVal)}
                          </span>
                          <span className="mono">💬 {num(p.commentsCount)}</span>
                          <span className="mono">❤️ {num(p.reactionsCount)}</span>
                          {p.engagementRate != null && (
                            <span className="mono text-neon-green">ER {pct(p.engagementRate)}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </a>
                );
              })}
            </div>
          ) : (
            <EmptyState
              title="Chưa có bài viết"
              description="Bấm Sync ở góc trên phải để đồng bộ, hoặc import CSV từ Meta Business Suite."
            />
          )}
        </div>
      </div>
    </>
  );
}
