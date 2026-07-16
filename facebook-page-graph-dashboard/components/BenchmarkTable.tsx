"use client";

import React from "react";

export interface BenchmarkRow {
  pageId?: string;
  pageName: string;
  pageUrl?: string;
  category?: string;
  isOwn: boolean;
  followers?: number;
  postsCount?: number;
  publicEngagement?: number | null;
  engagementPer1kFollowers?: number | null;
  avgCommentsPerPost?: number | null;
  avgSharesPerPost?: number | null;
  videoViewsPerFollower?: number | null;
  postingFrequencyPerDay?: number | null;
  benchmarkScore?: number | null;
  topPostUrl?: string | null;
  activeAds?: boolean | null;
}

interface Props {
  rows: BenchmarkRow[];
  loading?: boolean;
}

const num = (v: number | null | undefined, digits = 2) =>
  v == null ? "—" : v.toLocaleString("vi-VN", { maximumFractionDigits: digits });

export default function BenchmarkTable({ rows, loading }: Props) {
  return (
    <div className="table-wrap">
      <div className="overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              <th className="text-right">#</th>
              <th>Page</th>
              <th>Category</th>
              <th className="text-right">Followers</th>
              <th className="text-right">Posts</th>
              <th className="text-right">Public Engagement</th>
              <th className="text-right">Eng / 1k followers</th>
              <th className="text-right">Avg comments / post</th>
              <th className="text-right">Avg shares / post</th>
              <th className="text-right">Views / follower</th>
              <th className="text-right">Posting freq / day</th>
              <th className="text-right">Benchmark score</th>
              <th>Top post</th>
              <th>Active ads</th>
            </tr>
          </thead>
          <tbody>
            {loading &&
              Array.from({ length: 4 }).map((_, i) => (
                <tr key={i}>
                  <td colSpan={14}>
                    <div className="h-5 bg-gray-100 animate-pulse rounded" />
                  </td>
                </tr>
              ))}
            {!loading && rows.length === 0 && (
              <tr>
                <td colSpan={14} className="text-center text-gray-500 py-6">
                  Chưa có dữ liệu benchmark. Bấm “Import” để thêm competitor, hoặc chạy
                  <code className="mx-1">npm run seed</code> để có dữ liệu demo.
                </td>
              </tr>
            )}
            {!loading &&
              rows.map((r, i) => (
                <tr key={(r.pageId ?? r.pageName) + i} className={r.isOwn ? "bg-brand-50" : ""}>
                  <td className="text-right tabular-nums text-gray-500">{i + 1}</td>
                  <td>
                    <div className="font-medium">
                      {r.pageName}
                      {r.isOwn && (
                        <span className="ml-2 badge-info">Page bạn</span>
                      )}
                    </div>
                    {r.pageUrl && (
                      <a
                        href={r.pageUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-brand-600 hover:underline"
                      >
                        Mở ↗
                      </a>
                    )}
                  </td>
                  <td>
                    {r.category && <span className="badge-neutral">{r.category}</span>}
                  </td>
                  <td className="text-right tabular-nums">{num(r.followers, 0)}</td>
                  <td className="text-right tabular-nums">{num(r.postsCount, 0)}</td>
                  <td className="text-right tabular-nums">{num(r.publicEngagement, 0)}</td>
                  <td className="text-right tabular-nums">{num(r.engagementPer1kFollowers)}</td>
                  <td className="text-right tabular-nums">{num(r.avgCommentsPerPost)}</td>
                  <td className="text-right tabular-nums">{num(r.avgSharesPerPost)}</td>
                  <td className="text-right tabular-nums">{num(r.videoViewsPerFollower, 3)}</td>
                  <td className="text-right tabular-nums">{num(r.postingFrequencyPerDay)}</td>
                  <td className="text-right tabular-nums font-medium">
                    {r.benchmarkScore == null ? "—" : r.benchmarkScore.toFixed(1)}
                  </td>
                  <td>
                    {r.topPostUrl ? (
                      <a
                        href={r.topPostUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-brand-600 hover:underline"
                      >
                        Top ↗
                      </a>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>
                    {r.activeAds == null ? (
                      <span className="text-gray-400">—</span>
                    ) : r.activeAds ? (
                      <span className="badge-medium">Có</span>
                    ) : (
                      <span className="badge-low">Không</span>
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
