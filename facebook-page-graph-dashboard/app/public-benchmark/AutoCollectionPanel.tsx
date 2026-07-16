"use client";

import { useState, useEffect, useCallback } from "react";
import { RefreshCw, CheckCircle2, AlertTriangle, XCircle, Clock, Zap, AlertCircle } from "lucide-react";

interface CollectionLog {
  status: string;
  postsCollected: number;
  postsWithError: number;
  followerCount: number | null;
  collectedAt: string;
}

interface PeerStatus {
  id: number;
  name: string;
  canonicalUrl: string;
  lastCollectedAt: string | null;
  collectionStatus: string | null;
  collectionErrors: string | null;
  category: string | null;
  scaleBand: string | null;
  lastCollectionLog: CollectionLog | null;
  postsLast7Days: number;
}

interface StatusData {
  peers: PeerStatus[];
  needsReviewCount: number;
  summary: {
    totalPeers: number;
    successCount: number;
    partialCount: number;
    unavailableCount: number;
    neverCollected: number;
  };
}

export default function AutoCollectionPanel() {
  const [data, setData] = useState<StatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [collecting, setCollecting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch("/api/competitors/status").then((x) => x.json());
      if (r.ok) setData(r.data);
    } catch {
      // Silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleCollect() {
    setCollecting(true);
    try {
      await fetch("/api/competitors/collect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
    } catch {
      // ignore
    } finally {
      setCollecting(false);
    }
  }

  if (loading) {
    return (
      <div className="glass-card p-5">
        <div className="text-sm text-muted animate-pulse">Đang tải collection status…</div>
      </div>
    );
  }

  if (!data) return null;

  const { peers, summary, needsReviewCount } = data;

  return (
    <div className="glass-card p-5 mb-5 border-cyan-500/30">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-cyan-400" />
          <h2 className="text-lg font-semibold">Auto-Collection</h2>
          <span className="text-xs text-muted">Playwright session-based</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCollect}
            disabled={collecting}
            className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1 disabled:opacity-50"
          >
            <RefreshCw className={`w-3 h-3 ${collecting ? "animate-spin" : ""}`} />
            {collecting ? "Loading..." : "Collect Now"}
          </button>
          <button onClick={load} className="btn-secondary text-xs px-2 py-1.5">
            <RefreshCw className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-4">
        <SummaryCard label="Total Peers" value={String(summary?.totalPeers ?? 0)} />
        <SummaryCard label="✅ Success" value={String(summary?.successCount ?? 0)} color="text-emerald-400" />
        <SummaryCard label="⚠️ Partial" value={String(summary?.partialCount ?? 0)} color="text-amber-400" />
        <SummaryCard label="❌ Failed" value={String(summary?.unavailableCount ?? 0)} color="text-rose-400" />
        <SummaryCard label="Needs Review" value={String(needsReviewCount ?? 0)} color={needsReviewCount ? "text-amber-400" : ""} />
      </div>

      {/* Per-peer status table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 dark:bg-slate-800/50 text-xs text-muted">
            <tr>
              <th className="text-left p-2 font-medium">Peer</th>
              <th className="text-center p-2 font-medium">Status</th>
              <th className="text-right p-2 font-medium">Posts (7d)</th>
              <th className="text-right p-2 font-medium">Followers</th>
              <th className="text-left p-2 font-medium">Last Run</th>
              <th className="text-left p-2 font-medium">Errors</th>
            </tr>
          </thead>
          <tbody>
            {(peers ?? []).map((peer) => {
              const status = peer.collectionStatus || "never";
              const statusIcon =
                status === "success" ? <CheckCircle2 className="w-4 h-4 text-emerald-500 inline" /> :
                status === "partial" ? <AlertTriangle className="w-4 h-4 text-amber-500 inline" /> :
                status === "unavailable" || status === "blocked" ? <XCircle className="w-4 h-4 text-rose-500 inline" /> :
                <Clock className="w-4 h-4 text-slate-400 inline" />;

              const errors = peer.collectionErrors ? (() => {
                try { return JSON.parse(peer.collectionErrors); } catch { return []; }
              })() : [];

              return (
                <tr key={peer.id} className="border-t border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/30">
                  <td className="p-2">
                    <a href={peer.canonicalUrl} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline">
                      {peer.name}
                    </a>
                  </td>
                  <td className="p-2 text-center">{statusIcon}</td>
                  <td className="p-2 text-right tabular-nums">{peer.postsLast7Days}</td>
                  <td className="p-2 text-right tabular-nums">
                    {peer.lastCollectionLog?.followerCount
                      ? peer.lastCollectionLog.followerCount.toLocaleString("vi-VN")
                      : "—"}
                  </td>
                  <td className="p-2 text-xs text-muted">
                    {peer.lastCollectedAt
                      ? new Date(peer.lastCollectedAt).toLocaleDateString("vi-VN")
                      : "never"}
                  </td>
                  <td className="p-2 text-xs">
                    {errors.length > 0 ? (
                      <span className="text-amber-500 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" /> {errors.length} error(s)
                      </span>
                    ) : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Instructions */}
      <div className="mt-4 text-xs text-muted bg-slate-800/30 rounded p-3">
        <div className="font-medium text-cyan-400 mb-1">Cách chạy:</div>
        <div className="font-mono">npm run collect:competitors</div>
        <div className="mt-1">Hoặc pilot 3 peers: <code className="font-mono">npm run collect:competitors -- --pilot</code></div>
        <div className="mt-1 text-amber-400">⚠️ Browser sẽ mở. Đảm bảo bạn đã login Facebook. Tốc độ: 30s/page, max 5 posts/page.</div>
      </div>
    </div>
  );
}

function SummaryCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="bg-slate-800/30 rounded p-2 text-center">
      <div className="text-xs text-muted">{label}</div>
      <div className={`text-lg font-bold tabular-nums ${color || ""}`}>{value}</div>
    </div>
  );
}
