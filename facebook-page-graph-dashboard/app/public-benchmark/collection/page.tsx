"use client";

import { useState, useEffect } from "react";
import { ClipboardList, ArrowLeft, CheckCircle2, Clock, Users } from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import ErrorBox from "@/components/ErrorBox";
import { formatNumber } from "@/components/charts/chartTheme";

interface PeerPage {
  id: number;
  name: string;
  canonicalUrl: string;
  benchmarkRole: string;
  scaleBand: string | null;
  category: string | null;
  collectionFrequency: string | null;
  recommendedPostsPerCollection: number | null;
  isOwnPage: boolean;
  _count?: { posts: number };
}

export default function CollectionPage() {
  const [peers, setPeers] = useState<PeerPage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/public-benchmark/peers")
      .then((r) => r.json())
      .then((d) => {
        setPeers(d.peers || []);
        setLoading(false);
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Failed");
        setLoading(false);
      });
  }, []);

  const corePeers = peers.filter((p) => p.benchmarkRole === "core_peer" || p.isOwnPage);
  const totalRecommended = corePeers.reduce(
    (sum, p) => sum + (p.recommendedPostsPerCollection ?? 0),
    0,
  );

  if (loading) {
    return (
      <div className="p-6">
        <PageHeader title="Thu thập tuần" subtitle="Weekly public engagement collection workflow" icon={<ClipboardList className="w-5 h-5" />} />
        <div className="text-muted animate-pulse">Đang tải…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 space-y-4">
        <PageHeader title="Thu thập tuần" icon={<ClipboardList className="w-5 h-5" />} />
        <ErrorBox error={error} />
      </div>
    );
  }

  // Get current ISO week
  const now = new Date();
  const weekStart = new Date(now);
  const day = now.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  weekStart.setDate(now.getDate() + diff);

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <PageHeader
        title="Thu thập tuần"
        subtitle={`Tuần ${weekStart.toLocaleDateString("vi-VN")} — ${formatNumber(totalRecommended)} posts mục tiêu`}
        icon={<ClipboardList className="w-5 h-5" />}
        actions={
          <div className="flex items-center gap-3">
            <a href="/api/public-benchmark/template.csv" className="text-sm text-cyan-400 hover:text-cyan-300">Download template</a>
            <a href="/public-benchmark" className="text-sm text-cyan-400 hover:text-cyan-300 flex items-center gap-1"><ArrowLeft className="w-3.5 h-3.5" /> Dashboard</a>
          </div>
        }
      />

      {/* Workload summary */}
      <section className="grid grid-cols-3 gap-3">
        <div className="card p-4">
          <div className="flex items-center gap-2 text-xs text-muted mb-1"><Users className="w-3.5 h-3.5" /> Core peers</div>
          <div className="text-2xl font-bold tabular-nums">{corePeers.length}</div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 text-xs text-muted mb-1"><ClipboardList className="w-3.5 h-3.5" /> Posts mục tiêu / tuần</div>
          <div className="text-2xl font-bold tabular-nums">{totalRecommended}</div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 text-xs text-muted mb-1"><Clock className="w-3.5 h-3.5" /> Dự kiến thời gian</div>
          <div className="text-2xl font-bold tabular-nums">~{Math.ceil(totalRecommended * 0.5)}m</div>
          <div className="text-xs text-muted">~30s/post</div>
        </div>
      </section>

      {/* Collection guide */}
      <section className="card p-4">
        <h2 className="text-sm font-semibold mb-2">Cách thu thập</h2>
        <ol className="list-decimal list-inside space-y-1 text-sm text-muted">
          <li>Vào từng page Facebook bên dưới</li>
          <li>Mở 3–5 bài gần nhất (nội dung gốc, không quảng cáo)</li>
          <li>Ghi reactions, comments, shares hiển thị công khai</li>
          <li>Nhập qua <a href="/public-benchmark/import" className="text-cyan-400 hover:underline">Import page</a> (CSV hoặc thủ công)</li>
          <li><strong className="text-rose-400">Không</strong> dùng Meta Business Suite export cho page đối thủ</li>
        </ol>
      </section>

      {/* Collection checklist */}
      <section>
        <h2 className="text-sm font-semibold text-muted uppercase tracking-wide mb-3">Danh sách thu thập</h2>
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-800/50 text-xs text-muted">
              <tr>
                <th className="text-left p-2 font-medium">Page</th>
                <th className="text-left p-2 font-medium">Scale</th>
                <th className="text-left p-2 font-medium">Tần suất</th>
                <th className="text-right p-2 font-medium">Mục tiêu</th>
                <th className="text-right p-2 font-medium">Đã có</th>
                <th className="text-center p-2 font-medium">Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {corePeers.map((p) => {
                const collected = p._count?.posts ?? 0;
                const target = p.recommendedPostsPerCollection ?? 0;
                const done = collected >= target && target > 0;
                return (
                  <tr key={p.id} className="border-t border-slate-100 dark:border-slate-800">
                    <td className="p-2">
                      <a href={p.canonicalUrl} target="_blank" rel="noopener noreferrer" className={`hover:underline ${p.isOwnPage ? "text-cyan-400 font-medium" : ""}`}>
                        {p.name} {p.isOwnPage && "★"}
                      </a>
                    </td>
                    <td className="p-2 text-xs text-muted">{p.scaleBand ?? "—"}</td>
                    <td className="p-2 text-xs text-muted">{p.collectionFrequency ?? "—"}</td>
                    <td className="p-2 text-right tabular-nums">{target}</td>
                    <td className="p-2 text-right tabular-nums">{collected}</td>
                    <td className="p-2 text-center">
                      {done ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 inline" />
                      ) : (
                        <span className="text-xs text-muted">{collected}/{target || "—"}</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
