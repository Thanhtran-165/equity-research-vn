"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  MessageSquareWarning,
  Search,
  Copy,
  Check,
  ExternalLink,
  RefreshCw,
} from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import ErrorBox from "@/components/ErrorBox";
import EmptyState from "@/components/ui/EmptyState";

interface Comment {
  fbCommentId: string;
  fbPostId: string;
  message: string | null;
  createdTime: string | null;
  likeCount: number;
  commentCount: number;
  keywordFlag: string | null;
  sentiment: string | null;
  riskLevel: string;
  status: string;
  suggestedAction: string | null;
  suggestedReply: string | null;
  post?: { message: string | null; permalinkUrl: string | null } | null;
}

interface ApiError {
  code?: string;
  message: string;
  details?: any;
}

const RISK_OPTIONS = [
  { value: "all", label: "Mọi rủi ro" },
  { value: "high", label: "🔴 Cao" },
  { value: "medium", label: "🟡 Trung bình" },
  { value: "low", label: "🟢 Thấp" },
];

const STATUS_OPTIONS = [
  { value: "all", label: "Mọi trạng thái" },
  { value: "new", label: "Mới" },
  { value: "flagged", label: "Đã cờ" },
  { value: "reviewed", label: "Đã xem" },
  { value: "replied", label: "Đã trả lời" },
];

const FLAG_VI: Record<string, string> = {
  spam: "📢 Spam",
  attack: "⚔️ Công kích",
  common_question: "❓ Câu hỏi",
  none: "—",
};

const ACTION_VI: Record<string, string> = {
  hide_or_review: "Ẩn / xem lại",
  manual_review: "Xem lại thủ công",
  suggest_reply: "Gợi ý trả lời",
  none: "Không cần",
};

export default function CommentsPage() {
  const [rows, setRows] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [risk, setRisk] = useState("all");
  const [status, setStatus] = useState("all");
  const [q, setQ] = useState("");
  const [copied, setCopied] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch("/api/fb/comments-db?limit=500").then((x) => x.json());
      if (r.ok) setRows(r.data.comments);
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
    return rows.filter((c) => {
      if (risk !== "all" && c.riskLevel !== risk) return false;
      if (status !== "all" && c.status !== status) return false;
      if (q.trim() && !(c.message ?? "").toLowerCase().includes(q.trim().toLowerCase())) return false;
      return true;
    });
  }, [rows, risk, status, q]);

  // Stats
  const stats = useMemo(() => ({
    total: filtered.length,
    high: filtered.filter((c) => c.riskLevel === "high").length,
    medium: filtered.filter((c) => c.riskLevel === "medium").length,
    low: filtered.filter((c) => c.riskLevel === "low").length,
    needAction: filtered.filter((c) => c.suggestedAction && c.suggestedAction !== "none").length,
  }), [filtered]);

  function copyReply(id: string, text: string) {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(id);
      setTimeout(() => setCopied(null), 1500);
    });
  }

  return (
    <>
      <PageHeader
        title="Moderation"
        subtitle="Hàng đợi kiểm duyệt comment · MVP chỉ gợi ý action"
        icon={<MessageSquareWarning className="w-5 h-5" />}
        actions={
          <button onClick={load} className="btn-secondary">
            <RefreshCw className="w-4 h-4" />
            <span className="hidden sm:inline">Tải lại</span>
          </button>
        }
      />

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        <div className="card p-3">
          <div className="text-xs text-muted">Tổng comment</div>
          <div className="text-xl font-semibold tabular-nums">{stats.total}</div>
        </div>
        <div className="card p-3 border-danger-200 dark:border-danger-500/30">
          <div className="text-xs text-muted">Rủi ro cao</div>
          <div className="text-xl font-semibold tabular-nums text-danger-600 dark:text-danger-500">{stats.high}</div>
        </div>
        <div className="card p-3 border-warning-200 dark:border-warning-500/30">
          <div className="text-xs text-muted">Trung bình</div>
          <div className="text-xl font-semibold tabular-nums text-warning-600 dark:text-warning-500">{stats.medium}</div>
        </div>
        <div className="card p-3 border-brand-200 dark:border-brand-500/30">
          <div className="text-xs text-muted">Cần xử lý</div>
          <div className="text-xl font-semibold tabular-nums text-brand-600 dark:text-brand-400">{stats.needAction}</div>
        </div>
      </div>

      {/* Filter bar */}
      <div className="card p-3 mb-4 flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            type="text"
            placeholder="Tìm trong comment..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="input pl-9"
          />
        </div>
        <select value={risk} onChange={(e) => setRisk(e.target.value)} className="select w-auto">
          {RISK_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="select w-auto">
          {STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>

      {error && <div className="mb-4"><ErrorBox error={error} onRetry={load} /></div>}

      {/* List */}
      {!loading && filtered.length === 0 && !error ? (
        <EmptyState
          title="Không có comment khớp bộ lọc"
          description="Thay đổi filter hoặc sync lại để lấy comment mới."
        />
      ) : (
        <div className="space-y-2">
          {loading && Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card p-4"><div className="skeleton h-16 w-full" /></div>
          ))}
          {!loading && filtered.map((c) => (
            <div key={c.fbCommentId} className="card p-3">
              <div className="flex items-start gap-3">
                {/* Risk indicator */}
                <div className={`w-1 self-stretch rounded-full shrink-0 ${
                  c.riskLevel === "high" ? "bg-danger-500" : c.riskLevel === "medium" ? "bg-warning-500" : "bg-success-500"
                }`} />

                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap mb-1.5">
                    <span className={`badge-${c.riskLevel === "high" ? "high" : c.riskLevel === "medium" ? "medium" : "low"}`}>
                      {c.riskLevel}
                    </span>
                    {c.keywordFlag && c.keywordFlag !== "none" && (
                      <span className="badge-neutral">{FLAG_VI[c.keywordFlag] ?? c.keywordFlag}</span>
                    )}
                    {c.suggestedAction && c.suggestedAction !== "none" && (
                      <span className="badge-info">{ACTION_VI[c.suggestedAction] ?? c.suggestedAction}</span>
                    )}
                    <span className="text-xs text-muted ml-auto">
                      {c.createdTime?.slice(0, 10)}
                    </span>
                  </div>

                  <div className="text-sm text-slate-800 dark:text-slate-100 whitespace-pre-wrap mb-1.5">
                    {c.message || "(không có nội dung)"}
                  </div>

                  <div className="flex items-center gap-3 text-xs text-muted">
                    <span>❤️ {c.likeCount}</span>
                    <span>↩️ {c.commentCount}</span>
                    {c.post?.permalinkUrl && (
                      <a
                        href={c.post.permalinkUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="text-brand-600 dark:text-brand-400 hover:underline flex items-center gap-0.5"
                      >
                        Bài gốc <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>

                  {c.suggestedReply && (
                    <div className="mt-2 p-2 rounded-lg bg-brand-50 dark:bg-brand-500/10 border border-brand-100 dark:border-brand-500/20 flex items-start gap-2">
                      <div className="flex-1 min-w-0 text-xs text-brand-800 dark:text-brand-200">
                        <div className="text-[10px] uppercase tracking-wide text-brand-600 dark:text-brand-400 mb-0.5">
                          Gợi ý trả lời
                        </div>
                        {c.suggestedReply}
                      </div>
                      <button
                        onClick={() => copyReply(c.fbCommentId, c.suggestedReply!)}
                        className="btn-icon !w-7 !h-7 shrink-0"
                        title="Copy reply"
                      >
                        {copied === c.fbCommentId ? (
                          <Check className="w-3.5 h-3.5 text-success-600" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
