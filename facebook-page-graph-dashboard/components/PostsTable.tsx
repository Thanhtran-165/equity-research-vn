"use client";

import React from "react";
import Link from "next/link";

export interface PostsTableRow {
  fbPostId: string;
  message: string | null;
  topic: string;
  topicLabel?: string;
  postType: string;
  createdTime: string | null;
  permalinkUrl: string | null;
  reach?: number | null;
  impressions?: number | null;
  reactionsCount: number;
  commentsCount: number;
  sharesCount: number;
  clicks?: number | null;
  engagementRate?: number | null;
  score?: number | null;
}

interface Props {
  rows: PostsTableRow[];
  loading?: boolean;
  showSort?: boolean;
  sort?: string;
  order?: "asc" | "desc";
  onSortChange?: (field: string) => void;
}

const num = (v: number | null | undefined) =>
  v == null ? "—" : v.toLocaleString("vi-VN");
const pct = (v: number | null | undefined) =>
  v == null ? "—" : `${(v * 100).toFixed(2)}%`;

function TypeBadge({ type }: { type: string }) {
  const map: Record<string, string> = {
    text: "badge-neutral",
    photo: "badge-info",
    video_or_reel: "badge-medium",
    link: "badge-low",
    unknown: "badge-neutral",
  };
  return <span className={map[type] ?? "badge-neutral"}>{type}</span>;
}

export default function PostsTable({
  rows,
  loading,
  showSort,
  sort,
  order,
  onSortChange,
}: Props) {
  const sortBtn = (field: string, label: string) => (
    <button
      type="button"
      className="inline-flex items-center gap-1 hover:text-gray-700"
      onClick={() => onSortChange?.(field)}
    >
      {label}
      {sort === field && (
        <span className="text-brand-600">{order === "asc" ? "▲" : "▼"}</span>
      )}
    </button>
  );

  return (
    <div className="table-wrap">
      <div className="overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              <th className="whitespace-nowrap">Ngày</th>
              <th>Chủ đề</th>
              <th>Loại</th>
              <th className="min-w-[280px]">Nội dung</th>
              {showSort ? sortBtn("reach", "Reach") : <th>Reach</th>}
              <th>Impressions</th>
              <th>Reactions</th>
              {showSort ? sortBtn("commentsCount", "Comments") : <th>Comments</th>}
              {showSort ? sortBtn("sharesCount", "Shares") : <th>Shares</th>}
              <th>Clicks</th>
              {showSort ? sortBtn("engagementRate", "ER") : <th>ER</th>}
              {showSort ? sortBtn("score", "Score") : <th>Score</th>}
              <th>Link</th>
            </tr>
          </thead>
          <tbody>
            {loading &&
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  <td colSpan={13}>
                    <div className="h-5 bg-gray-100 animate-pulse rounded" />
                  </td>
                </tr>
              ))}
            {!loading && rows.length === 0 && (
              <tr>
                <td colSpan={13} className="text-center text-gray-500 py-6">
                  Chưa có dữ liệu. Bấm “Sync Facebook Data” để đồng bộ.
                </td>
              </tr>
            )}
            {!loading &&
              rows.map((r) => (
                <tr key={r.fbPostId}>
                  <td className="whitespace-nowrap text-gray-600">
                    {r.createdTime?.slice(0, 10) ?? "—"}
                  </td>
                  <td>
                    <span className="badge-info">{r.topicLabel ?? r.topic}</span>
                  </td>
                  <td>
                    <TypeBadge type={r.postType} />
                  </td>
                  <td className="max-w-md">
                    <div className="line-clamp-2 text-gray-700">
                      {r.message ?? "(không có nội dung)"}
                    </div>
                  </td>
                  <td className="text-right tabular-nums">{num(r.reach)}</td>
                  <td className="text-right tabular-nums">{num(r.impressions)}</td>
                  <td className="text-right tabular-nums">{num(r.reactionsCount)}</td>
                  <td className="text-right tabular-nums">{num(r.commentsCount)}</td>
                  <td className="text-right tabular-nums">{num(r.sharesCount)}</td>
                  <td className="text-right tabular-nums">{num(r.clicks)}</td>
                  <td className="text-right tabular-nums">{pct(r.engagementRate)}</td>
                  <td className="text-right tabular-nums font-medium">
                    {r.score == null ? "—" : r.score.toFixed(1)}
                  </td>
                  <td>
                    {r.permalinkUrl ? (
                      <Link
                        href={r.permalinkUrl}
                        target="_blank"
                        className="text-brand-600 hover:underline text-xs"
                      >
                        Mở ↗
                      </Link>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
