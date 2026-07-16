"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Newspaper,
  Search,
  ExternalLink,
  Eye,
  Heart,
  MessageSquare,
  Share2,
  Clock,
} from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import ErrorBox from "@/components/ErrorBox";
import EmptyState from "@/components/ui/EmptyState";
import Drawer from "@/components/ui/Drawer";

interface Post {
  id: number;
  fbPostId: string;
  pageId: string;
  message: string | null;
  permalinkUrl: string | null;
  createdTime: string | null;
  postType: string;
  topic: string;
  topicLabel?: string;
  reactionsCount: number;
  commentsCount: number;
  sharesCount: number;
  reach: number | null;
  impressions: number | null;
  engagedUsers: number | null;
  clicks: number | null;
  videoViews: number | null;
  publicEngagement: number | null;
  metricSource: string | null;
  engagementRate: number | null;
  score: number | null;
}

interface ApiError {
  code?: string;
  message: string;
  details?: any;
}

const TOPIC_OPTIONS = [
  { value: "all", label: "Tất cả chủ đề" },
  { value: "vi_mo", label: "Vĩ mô" },
  { value: "chung_khoan", label: "Chứng khoán" },
  { value: "lai_suat", label: "Lãi suất" },
  { value: "bds", label: "BĐS" },
  { value: "vang", label: "Vàng" },
  { value: "khac", label: "Khác" },
];

const SOURCE_OPTIONS = [
  { value: "all", label: "Mọi nguồn" },
  { value: "meta_business_suite_csv", label: "📊 MBS CSV (true reach)" },
  { value: "facebook_graph_api_insights", label: "🔌 Graph API (true reach)" },
  { value: "facebook_video_metric", label: "🎥 Video views" },
  { value: "facebook_public_metrics", label: "👥 Public engagement" },
];

const TYPE_OPTIONS = [
  { value: "all", label: "Mọi loại" },
  { value: "video_or_reel", label: "Video/Reel" },
  { value: "photo", label: "Photo" },
  { value: "text", label: "Text" },
  { value: "link", label: "Link" },
];

const num = (v: number | null | undefined) =>
  v == null ? "—" : v.toLocaleString("vi-VN");
const pct = (v: number | null | undefined) =>
  v == null ? "—" : `${(v * 100).toFixed(2)}%`;

function isTrueReach(source: string | null | undefined): boolean {
  return source === "facebook_graph_api_insights" || source === "meta_business_suite_csv";
}

function SourceBadge({ source }: { source: string | null }) {
  if (source === "meta_business_suite_csv")
    return <span className="badge bg-brand-500/15 text-brand-300 text-[10px] uppercase tracking-wide">📊 CSV</span>;
  if (source === "facebook_graph_api_insights")
    return <span className="badge bg-cyan-500/15 text-cyan-400 text-[10px] uppercase tracking-wide">🔌 API</span>;
  if (source === "facebook_video_metric")
    return <span className="badge bg-purple-500/15 text-purple-400 text-[10px] uppercase tracking-wide">🎥 Views</span>;
  if (source === "facebook_public_metrics" || source === "public_engagement_proxy")
    return <span className="badge bg-amber-500/15 text-amber-500 text-[10px] uppercase tracking-wide">👥 Proxy</span>;
  return <span className="badge bg-slate-700/40 text-slate-400 text-[10px] uppercase tracking-wide">N/A</span>;
}

export default function PostsPage() {
  const [allPosts, setAllPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const [topicFilter, setTopicFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [q, setQ] = useState("");

  const [selected, setSelected] = useState<Post | null>(null);
  const [comments, setComments] = useState<any[] | null>(null);
  const [commentsLoading, setCommentsLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`/api/fb/posts-db?sort=createdTime&order=desc&limit=500`).then((x) => x.json());
      if (r.ok) setAllPosts(r.data.posts);
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

  const filtered = useMemo(() => {
    let arr = [...allPosts];
    if (topicFilter !== "all") arr = arr.filter((p) => p.topic === topicFilter);
    if (typeFilter !== "all") arr = arr.filter((p) => p.postType === typeFilter);
    if (sourceFilter !== "all") {
      if (sourceFilter === "facebook_public_metrics") {
        arr = arr.filter((p) => p.metricSource === "facebook_public_metrics" || p.metricSource === "public_engagement_proxy");
      } else {
        arr = arr.filter((p) => p.metricSource === sourceFilter);
      }
    }
    if (q.trim()) {
      const lower = q.trim().toLowerCase();
      arr = arr.filter((p) => (p.message ?? "").toLowerCase().includes(lower));
    }
    return arr;
  }, [allPosts, topicFilter, typeFilter, q, sourceFilter]);

  async function openPost(post: Post) {
    setSelected(post);
    setComments(null);
    setCommentsLoading(true);
    try {
      const r = await fetch(`/api/fb/comments-db?fbPostId=${encodeURIComponent(post.fbPostId)}&limit=50`).then((x) => x.json());
      if (r.ok) setComments(r.data.comments);
    } catch {
      setComments([]);
    } finally {
      setCommentsLoading(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Bài viết"
        subtitle={`${filtered.length} bài · click row để xem chi tiết`}
        icon={<Newspaper className="w-5 h-5" />}
      />

      {/* Filter bar */}
      <div className="card p-3 mb-4 flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[180px]">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Tìm nội dung..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="input pl-9"
          />
        </div>
        <select value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)} className="select w-auto">
          {SOURCE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <select value={topicFilter} onChange={(e) => setTopicFilter(e.target.value)} className="select w-auto">
          {TOPIC_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} className="select w-auto">
          {TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <span className="text-xs text-slate-400 ml-auto">{filtered.length}/{allPosts.length}</span>
      </div>

      {error && <div className="mb-4"><ErrorBox error={error} onRetry={load} /></div>}

      {/* Compact triage table */}
      {!loading && filtered.length === 0 && !error ? (
        <EmptyState title="Không có bài viết khớp" description="Thử bỏ filter hoặc sync lại." />
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto scrollbar-thin">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50/50 dark:bg-slate-800/30 border-b border-slate-200 dark:border-slate-700">
                  <th className="text-left text-xs font-semibold text-slate-600 dark:text-slate-300 px-3 py-2 whitespace-nowrap">Ngày</th>
                  <th className="text-left text-xs font-semibold text-slate-600 dark:text-slate-300 px-2 py-2">Source</th>
                  <th className="text-left text-xs font-semibold text-slate-600 dark:text-slate-300 px-2 py-2">Loại</th>
                  <th className="text-left text-xs font-semibold text-slate-600 dark:text-slate-300 px-3 py-2 min-w-[200px]">Preview</th>
                  <th className="text-right text-xs font-semibold text-slate-600 dark:text-slate-300 px-2 py-2 whitespace-nowrap">Reach</th>
                  <th className="text-right text-xs font-semibold text-slate-600 dark:text-slate-300 px-2 py-2 whitespace-nowrap">❤️</th>
                  <th className="text-right text-xs font-semibold text-slate-600 dark:text-slate-300 px-2 py-2 whitespace-nowrap">💬</th>
                  <th className="text-right text-xs font-semibold text-slate-600 dark:text-slate-300 px-2 py-2 whitespace-nowrap">🔁</th>
                  <th className="text-right text-xs font-semibold text-slate-600 dark:text-slate-300 px-2 py-2 whitespace-nowrap">ER</th>
                </tr>
              </thead>
              <tbody>
                {loading && Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} className="border-b border-slate-100 dark:border-slate-800/50">
                    <td colSpan={9} className="px-3 py-2"><div className="h-5 bg-slate-200/50 dark:bg-slate-700/30 rounded animate-pulse" /></td>
                  </tr>
                ))}
                {!loading && filtered.map((p) => {
                  const trueReach = isTrueReach(p.metricSource);
                  return (
                    <tr
                      key={p.fbPostId}
                      onClick={() => openPost(p)}
                      className="border-b border-slate-100 dark:border-slate-800/50 cursor-pointer hover:bg-slate-50/70 dark:hover:bg-slate-800/30 transition-colors"
                    >
                      <td className="px-3 py-2 whitespace-nowrap text-xs text-slate-500 dark:text-slate-400">
                        {p.createdTime?.slice(0, 10) ?? "—"}
                      </td>
                      <td className="px-2 py-2"><SourceBadge source={p.metricSource} /></td>
                      <td className="px-2 py-2">
                        <span className="text-xs text-slate-500 dark:text-slate-400">{p.postType}</span>
                      </td>
                      <td className="px-3 py-2 max-w-[280px]">
                        <div className="text-sm text-slate-700 dark:text-slate-200 truncate" title={p.message ?? ""}>
                          {p.message ? p.message.slice(0, 150) : "(không có nội dung)"}
                        </div>
                        <span className="text-[10px] text-slate-400 dark:text-slate-500">{p.topicLabel ?? p.topic}</span>
                      </td>
                      <td className="px-2 py-2 text-right tabular-nums text-sm text-slate-600 dark:text-slate-300 whitespace-nowrap">
                        {num(p.reach)}
                      </td>
                      <td className="px-2 py-2 text-right tabular-nums text-sm text-slate-600 dark:text-slate-300">{num(p.reactionsCount)}</td>
                      <td className="px-2 py-2 text-right tabular-nums text-sm text-slate-600 dark:text-slate-300">{num(p.commentsCount)}</td>
                      <td className="px-2 py-2 text-right tabular-nums text-sm text-slate-600 dark:text-slate-300">{num(p.sharesCount)}</td>
                      <td className="px-2 py-2 text-right tabular-nums text-xs whitespace-nowrap">
                        {p.engagementRate != null && trueReach ? (
                          <span className="text-green-600 dark:text-green-400">{pct(p.engagementRate)}</span>
                        ) : p.engagementRate != null && !trueReach ? (
                          <span className="text-amber-500" title="Non-true-reach source">{pct(p.engagementRate)}*</span>
                        ) : (
                          <span className="text-slate-300 dark:text-slate-600">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Post detail drawer */}
      <Drawer
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected ? `${selected.createdTime?.slice(0, 10)}` : ""}
        width="max-w-lg"
      >
        {selected && (
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <SourceBadge source={selected.metricSource} />
              <span className="badge bg-slate-100 dark:bg-slate-700/40 text-slate-600 dark:text-slate-300 text-[10px]">{selected.postType}</span>
              <span className="badge bg-brand-500/10 text-brand-400 text-[10px]">{selected.topicLabel ?? selected.topic}</span>
              {isTrueReach(selected.metricSource) ? (
                <span className="badge bg-green-500/10 text-green-500 text-[10px]">✓ True reach</span>
              ) : (
                <span className="badge bg-amber-500/10 text-amber-500 text-[10px]">⚠ Non-true-reach</span>
              )}
            </div>

            <div className="card p-3 bg-slate-50 dark:bg-slate-800/40">
              <p className="text-sm text-slate-700 dark:text-slate-200 whitespace-pre-wrap leading-relaxed">
                {selected.message || "(không có nội dung)"}
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <MiniMetric icon={<Eye className="w-3 h-3" />} label="Reach" value={num(selected.reach)} />
              <MiniMetric icon={<Heart className="w-3 h-3" />} label="Reactions" value={num(selected.reactionsCount)} />
              <MiniMetric icon={<MessageSquare className="w-3 h-3" />} label="Comments" value={num(selected.commentsCount)} />
              <MiniMetric icon={<Share2 className="w-3 h-3" />} label="Shares" value={num(selected.sharesCount)} />
              <MiniMetric icon={<Clock className="w-3 h-3" />} label="Clicks" value={num(selected.clicks)} />
              <MiniMetric icon={<Eye className="w-3 h-3" />} label="Video views" value={num(selected.videoViews)} />
              <MiniMetric label="ER" value={isTrueReach(selected.metricSource) && selected.engagementRate != null ? pct(selected.engagementRate) : "—"} />
              <MiniMetric label="CTR" value={selected.clicks != null && selected.reach ? pct(selected.clicks / selected.reach) : "—"} />
            </div>

            {selected.permalinkUrl && (
              <a href={selected.permalinkUrl} target="_blank" rel="noreferrer" className="btn-secondary w-full">
                <ExternalLink className="w-4 h-4" /> Mở bài gốc
              </a>
            )}

            <div>
              <h4 className="font-medium text-sm mb-2 text-slate-700 dark:text-slate-200">Comments</h4>
              {commentsLoading ? (
                <div className="space-y-2">{[1, 2, 3].map((i) => <div key={i} className="h-10 bg-slate-200/40 dark:bg-slate-700/20 rounded animate-pulse" />)}</div>
              ) : comments && comments.length > 0 ? (
                <div className="space-y-1.5 max-h-60 overflow-y-auto scrollbar-thin">
                  {comments.map((c) => (
                    <div key={c.fbCommentId} className="p-2 rounded text-xs bg-slate-50 dark:bg-slate-800/40">
                      <div className="text-slate-700 dark:text-slate-200">{c.message}</div>
                      <div className="text-slate-400 mt-0.5">❤️ {c.likeCount} · ↩️ {c.commentCount}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400">Chưa có comment trong DB.</p>
              )}
            </div>
          </div>
        )}
      </Drawer>
    </>
  );
}

function MiniMetric({ icon, label, value }: { icon?: React.ReactNode; label: string; value: React.ReactNode }) {
  return (
    <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/40">
      <div className="text-[10px] text-slate-400 dark:text-slate-500 uppercase flex items-center gap-1">{icon}{label}</div>
      <div className="text-sm font-semibold tabular-nums text-slate-700 dark:text-slate-200">{value}</div>
    </div>
  );
}
