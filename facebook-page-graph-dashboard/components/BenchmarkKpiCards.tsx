import React from "react";
import KpiCard from "./KpiCard";

interface Props {
  ownEngagementPer1k: number | null;
  peerMedian: number;
  ownRank: number;
  percentile: number;
  bestCompetitor: string;
  benchmarkScore: number | null;
  totalPeers: number;
  loading?: boolean;
}

const num = (v: number | null | undefined, digits = 2) =>
  v == null ? "—" : v.toLocaleString("vi-VN", { maximumFractionDigits: digits });

export default function BenchmarkKpiCards({
  ownEngagementPer1k,
  peerMedian,
  ownRank,
  percentile,
  bestCompetitor,
  benchmarkScore,
  totalPeers,
  loading,
}: Props) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      <KpiCard
        label="Engagement / 1k followers"
        value={num(ownEngagementPer1k)}
        hint={`peer median ${num(peerMedian)}`}
        loading={loading}
      />
      <KpiCard label="Peer median" value={num(peerMedian)} hint="cùng category/period" loading={loading} />
      <KpiCard
        label="Xếp hạng"
        value={ownRank > 0 ? `#${ownRank}/${totalPeers + 1}` : "—"}
        loading={loading}
      />
      <KpiCard
        label="Percentile"
        value={percentile != null ? `${percentile}%` : "—"}
        hint="càng cao càng tốt"
        loading={loading}
      />
      <KpiCard label="Best competitor" value={<span className="text-base">{bestCompetitor || "—"}</span>} loading={loading} />
      <KpiCard
        label="Benchmark score"
        value={benchmarkScore == null ? "—" : benchmarkScore.toFixed(1)}
        hint="0..100, percentile-weighted"
        loading={loading}
      />
    </div>
  );
}
