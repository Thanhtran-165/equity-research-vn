import React from "react";
import TopicPerformanceTable, { type TopicPerformanceRow } from "./TopicPerformanceTable";

export interface WeeklyReportData {
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

interface Props {
  data: WeeklyReportData | null;
  loading?: boolean;
}

const num = (v: number | null | undefined) =>
  v == null ? "—" : v.toLocaleString("vi-VN");

function TopPostRow({ label, post }: { label: string; post?: any | null }) {
  if (!post) return null;
  return (
    <div className="flex items-start gap-2 text-sm">
      <span className="text-gray-500 min-w-[140px]">{label}</span>
      <div className="flex-1">
        <div className="text-gray-800 line-clamp-2">{post.message}</div>
        <div className="text-xs text-gray-500 mt-0.5">
          reach {num(post.reach)} · cmt {num(post.commentsCount)} · ER{" "}
          {post.engagementRate == null
            ? "—"
            : `${(post.engagementRate * 100).toFixed(2)}%`}
        </div>
      </div>
    </div>
  );
}

export default function WeeklyReportCard({ data, loading }: Props) {
  if (loading) {
    return (
      <div className="card p-6">
        <div className="h-6 bg-gray-100 animate-pulse rounded w-1/3 mb-3" />
        <div className="h-4 bg-gray-100 animate-pulse rounded w-2/3 mb-2" />
        <div className="h-4 bg-gray-100 animate-pulse rounded w-1/2" />
      </div>
    );
  }
  if (!data) {
    return (
      <div className="card p-6 text-center text-gray-500">
        Chưa có báo cáo tuần. Bấm “Tạo báo cáo tuần” để tạo.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <div className="flex items-baseline justify-between">
          <h2 className="text-lg font-semibold">
            Báo cáo tuần {data.weekStart} → {data.weekEnd}
          </h2>
          {data.topTopicLabel && (
            <span className="badge-info">Chủ đề nổi bật: {data.topTopicLabel}</span>
          )}
        </div>
        <p className="mt-2 text-gray-700">{data.summary}</p>
        {data.recommendation && (
          <div className="mt-3 p-3 rounded-lg bg-brand-50 border border-brand-100">
            <div className="text-xs uppercase tracking-wide text-brand-700">
              Khuyến nghị
            </div>
            <p className="text-sm text-gray-800 mt-1">{data.recommendation}</p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card p-4">
          <div className="text-xs text-gray-500">Tổng reach</div>
          <div className="text-xl font-semibold">{num(data.reachTotal)}</div>
        </div>
        <div className="card p-4">
          <div className="text-xs text-gray-500">Tổng tương tác</div>
          <div className="text-xl font-semibold">{num(data.engagementTotal)}</div>
        </div>
        <div className="card p-4">
          <div className="text-xs text-gray-500">Follower delta</div>
          <div
            className={`text-xl font-semibold ${
              data.followerDelta > 0
                ? "text-green-600"
                : data.followerDelta < 0
                ? "text-red-600"
                : ""
            }`}
          >
            {data.followerDelta > 0 ? "+" : ""}
            {num(data.followerDelta)}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-xs text-gray-500">Comment rủi ro cao</div>
          <div className="text-xl font-semibold text-red-600">
            {data.moderationRiskSummary.high}
          </div>
          <div className="text-xs text-gray-500">
            trên tổng {data.moderationRiskSummary.total}
          </div>
        </div>
      </div>

      <div className="card p-5 space-y-3">
        <h3 className="font-semibold">Top bài viết</h3>
        <TopPostRow label="Reach cao nhất" post={data.topReachPost} />
        <TopPostRow label="Comment nhiều nhất" post={data.topCommentPost} />
        <TopPostRow label="ER cao nhất" post={data.topEngagementRatePost} />
      </div>

      <div>
        <h3 className="font-semibold mb-2">So sánh chủ đề</h3>
        <TopicPerformanceTable rows={data.topicComparison} />
      </div>

      {data.commentSpikes.length > 0 && (
        <div className="card p-5 border-amber-200 bg-amber-50">
          <h3 className="font-semibold text-amber-800">
            ⚠️ Comment spike ({data.commentSpikes.length})
          </h3>
          <ul className="mt-2 space-y-1 text-sm">
            {data.commentSpikes.map((s) => (
              <li key={s.fbPostId} className="text-amber-800">
                Post <span className="font-mono">{s.fbPostId}</span>:{" "}
                <strong>{s.commentsCount}</strong> comments (median = {s.median})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
