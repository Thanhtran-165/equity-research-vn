"use client";

import React, { useMemo, useState } from "react";

export interface CommentRow {
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

interface Props {
  rows: CommentRow[];
  loading?: boolean;
}

const riskBadge: Record<string, string> = {
  low: "badge-low",
  medium: "badge-medium",
  high: "badge-high",
};

const sentimentBadge: Record<string, string> = {
  positive: "badge-low",
  negative: "badge-medium",
  neutral: "badge-neutral",
};

const actionLabelVi: Record<string, string> = {
  hide_or_review: "Ẩn / xem lại",
  manual_review: "Xem lại thủ công",
  suggest_reply: "Gợi ý trả lời",
  none: "Không cần",
};

const flagLabelVi: Record<string, string> = {
  spam: "Spam",
  attack: "Công kích",
  common_question: "Câu hỏi phổ biến",
  none: "—",
};

export default function CommentModerationTable({ rows, loading }: Props) {
  const [risk, setRisk] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const [q, setQ] = useState<string>("");

  const filtered = useMemo(() => {
    return rows.filter((r) => {
      if (risk && r.riskLevel !== risk) return false;
      if (status && r.status !== status) return false;
      if (q) {
        const text = (r.message ?? "").toLowerCase();
        if (!text.includes(q.toLowerCase())) return false;
      }
      return true;
    });
  }, [rows, risk, status, q]);

  return (
    <div className="space-y-3">
      <div className="card p-3 flex flex-wrap gap-2 items-center">
        <input
          type="text"
          placeholder="Tìm trong comment..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="flex-1 min-w-[200px] px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
        <select
          value={risk}
          onChange={(e) => setRisk(e.target.value)}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg bg-white"
        >
          <option value="">Mọi rủi ro</option>
          <option value="high">Cao</option>
          <option value="medium">Trung bình</option>
          <option value="low">Thấp</option>
        </select>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg bg-white"
        >
          <option value="">Mọi trạng thái</option>
          <option value="new">Mới</option>
          <option value="flagged">Đã cờ</option>
          <option value="reviewed">Đã xem</option>
          <option value="replied">Đã trả lời</option>
          <option value="hidden">Đã ẩn</option>
        </select>
        <span className="text-xs text-gray-500">
          {filtered.length}/{rows.length} comment
        </span>
      </div>

      <div className="table-wrap">
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>Ngày</th>
                <th className="min-w-[240px]">Comment</th>
                <th>Nguyên nhân</th>
                <th>Cảm xúc</th>
                <th>Rủi ro</th>
                <th>Hành động</th>
                <th className="min-w-[240px]">Gợi ý trả lời</th>
                <th>Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {loading &&
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    <td colSpan={8}>
                      <div className="h-5 bg-gray-100 animate-pulse rounded" />
                    </td>
                  </tr>
                ))}
              {!loading && filtered.length === 0 && (
                <tr>
                  <td colSpan={8} className="text-center text-gray-500 py-6">
                    Không có comment khớp bộ lọc.
                  </td>
                </tr>
              )}
              {!loading &&
                filtered.map((c) => (
                  <tr key={c.fbCommentId}>
                    <td className="whitespace-nowrap text-gray-600">
                      {c.createdTime?.slice(0, 10) ?? "—"}
                    </td>
                    <td>
                      <div className="text-gray-800 line-clamp-3">{c.message}</div>
                      {c.post?.permalinkUrl && (
                        <a
                          href={c.post.permalinkUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-brand-600 hover:underline"
                        >
                          Xem bài gốc ↗
                        </a>
                      )}
                    </td>
                    <td>{flagLabelVi[c.keywordFlag ?? "none"]}</td>
                    <td>
                      <span className={sentimentBadge[c.sentiment ?? "neutral"]}>
                        {c.sentiment ?? "neutral"}
                      </span>
                    </td>
                    <td>
                      <span className={riskBadge[c.riskLevel] ?? "badge-neutral"}>
                        {c.riskLevel}
                      </span>
                    </td>
                    <td className="text-xs">
                      {actionLabelVi[c.suggestedAction ?? "none"] ?? c.suggestedAction}
                    </td>
                    <td className="text-xs text-gray-700">
                      {c.suggestedReply ?? "—"}
                    </td>
                    <td>
                      <span className="badge-neutral">{c.status}</span>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
