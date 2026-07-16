import React from "react";

export interface TopicPerformanceRow {
  topic: string;
  topicLabel: string;
  postsCount: number;
  reachTotal: number;
  commentsTotal: number;
  sharesTotal: number;
  engagementRateAvg: number | null;
  scoreAvg: number | null;
}

interface Props {
  rows: TopicPerformanceRow[];
  loading?: boolean;
}

const num = (v: number | null | undefined) =>
  v == null ? "—" : v.toLocaleString("vi-VN");
const pct = (v: number | null | undefined) =>
  v == null ? "—" : `${(v * 100).toFixed(2)}%`;

export default function TopicPerformanceTable({ rows, loading }: Props) {
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Chủ đề</th>
            <th className="text-right">Số bài</th>
            <th className="text-right">Tổng reach</th>
            <th className="text-right">Tổng comment</th>
            <th className="text-right">Tổng share</th>
            <th className="text-right">ER trung bình</th>
            <th className="text-right">Score trung bình</th>
          </tr>
        </thead>
        <tbody>
          {loading &&
            Array.from({ length: 3 }).map((_, i) => (
              <tr key={i}>
                <td colSpan={7}>
                  <div className="h-5 bg-gray-100 animate-pulse rounded" />
                </td>
              </tr>
            ))}
          {!loading && rows.length === 0 && (
            <tr>
              <td colSpan={7} className="text-center text-gray-500 py-6">
                Chưa có dữ liệu.
              </td>
            </tr>
          )}
          {!loading &&
            rows.map((r) => (
              <tr key={r.topic}>
                <td>
                  <span className="badge-info">{r.topicLabel}</span>
                </td>
                <td className="text-right tabular-nums">{r.postsCount}</td>
                <td className="text-right tabular-nums">{num(r.reachTotal)}</td>
                <td className="text-right tabular-nums">{num(r.commentsTotal)}</td>
                <td className="text-right tabular-nums">{num(r.sharesTotal)}</td>
                <td className="text-right tabular-nums">{pct(r.engagementRateAvg)}</td>
                <td className="text-right tabular-nums">
                  {r.scoreAvg == null ? "—" : r.scoreAvg.toFixed(1)}
                </td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}
