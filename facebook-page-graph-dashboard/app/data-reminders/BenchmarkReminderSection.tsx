"use client";

import { useState, useEffect, useCallback } from "react";
import { Trophy, AlertTriangle, CheckCircle2, Clock, Upload, ClipboardList, Copy, Check, FileSpreadsheet, Package } from "lucide-react";

interface BenchmarkItem {
  id: number;
  benchmarkPageId: number;
  targetPosts: number;
  collectedPosts: number;
  status: string;
  notes: string | null;
  page: {
    id: number;
    name: string;
    canonicalUrl: string;
    scaleBand: string | null;
    benchmarkRole: string;
    isOwnPage: boolean;
  };
}

interface BenchmarkRun {
  id: number;
  weekStart: string;
  weekEnd: string;
  dueAt: string;
  status: string;
  snoozedUntil: string | null;
  notes: string | null;
  completedAt: string | null;
  items: BenchmarkItem[];
}

interface BenchmarkSummary {
  externalCorePeers: number;
  targetTotal: number;
  collectedTotal: number;
  pagesCompleted: number;
  pagesNotStarted: number;
  sharesCoverage: number;
  weekStart: string;
  weekEnd: string;
  dueAt: string;
  isOverdue: boolean;
}

interface BenchmarkResponse {
  currentRun: BenchmarkRun | null;
  incompleteRuns: BenchmarkRun[];
  summary: BenchmarkSummary;
}

export default function BenchmarkReminderSection() {
  const [data, setData] = useState<BenchmarkResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch("/api/data-reminders/benchmark/current").then((x) => x.json());
      if (r.ok) setData(r.data);
    } catch {
      // Silent fail — section is optional
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  function copyToClipboard(text: string, key: string) {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(key);
      setTimeout(() => setCopied(null), 1500);
    });
  }

  async function handleGeneratePack() {
    setGenerating(true);
    try {
      const weekStart = data?.summary.weekStart.split("T")[0];
      await fetch("/api/data-reminders/benchmark/generate-pack", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ weekStart }),
      });
    } catch {
      // ignore
    } finally {
      setGenerating(false);
    }
  }

  async function handleRunStatus(runId: number, status: string, notes?: string) {
    await fetch(`/api/data-reminders/benchmark/run/${runId}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status, notes }),
    });
    load();
  }

  async function handleSnooze(runId: number) {
    await fetch(`/api/data-reminders/benchmark/run/${runId}/snooze`, { method: "POST" });
    load();
  }

  if (loading) {
    return (
      <div className="glass-card p-5">
        <div className="text-sm text-muted animate-pulse">Đang tải benchmark reminder…</div>
      </div>
    );
  }

  if (!data) return null;

  const { currentRun, incompleteRuns, summary } = data;

  // Build checklist text for copy
  const checklistText = currentRun
    ? currentRun.items.map((item) =>
        `[ ] ${item.page.name} — ${item.collectedPosts}/${item.targetPosts} posts (${item.status})\n    ${item.page.canonicalUrl}`
      ).join("\n")
    : "";

  const peerUrls = currentRun
    ? currentRun.items.map((i) => i.page.canonicalUrl).join("\n")
    : "";

  return (
    <div className="glass-card p-5 mb-5 border-purple-500/30">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Trophy className="w-5 h-5 text-purple-400" />
          <h2 className="text-lg font-semibold">Benchmark công khai</h2>
          {summary.isOverdue && currentRun && (
            <span className="text-xs px-2 py-0.5 rounded bg-red-500/20 text-red-400 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" /> Quá hạn
            </span>
          )}
          {currentRun?.status === "completed" && (
            <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" /> Hoàn thành
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleGeneratePack}
            disabled={generating}
            className="btn-secondary text-xs px-2 py-1 flex items-center gap-1 disabled:opacity-50"
          >
            <Package className="w-3 h-3" /> {generating ? "..." : "Collection pack"}
          </button>
          <a href="/api/public-benchmark/template.csv" className="btn-secondary text-xs px-2 py-1 flex items-center gap-1">
            <FileSpreadsheet className="w-3 h-3" /> Template
          </a>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-4">
        <SummaryCard label="Core Peers" value={String(summary.externalCorePeers)} />
        <SummaryCard label="Mục tiêu" value={String(summary.targetTotal)} />
        <SummaryCard label="Đã nhập" value={String(summary.collectedTotal)} accent={summary.collectedTotal > 0 ? "emerald" : undefined} />
        <SummaryCard label="Page xong" value={`${summary.pagesCompleted}/${summary.externalCorePeers}`} />
        <SummaryCard label="Chưa bắt đầu" value={String(summary.pagesNotStarted)} accent={summary.pagesNotStarted > 0 ? "amber" : undefined} />
      </div>

      {/* Due date info */}
      {currentRun && (
        <div className="text-xs text-muted mb-3 flex items-center gap-3 flex-wrap">
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Due: {new Date(summary.dueAt).toLocaleString("vi-VN")}
          </span>
          <span>Shares coverage: {(summary.sharesCoverage * 100).toFixed(0)}%</span>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex flex-wrap gap-2 mb-4">
        <a href="/public-benchmark/collection" className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1">
          <ClipboardList className="w-3 h-3" /> Mở Collection
        </a>
        <a href="/public-benchmark/import" className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1">
          <Upload className="w-3 h-3" /> Mở Import
        </a>
        <button onClick={() => copyToClipboard(checklistText, "checklist")} className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1">
          {copied === "checklist" ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />} Copy checklist
        </button>
        <button onClick={() => copyToClipboard(peerUrls, "urls")} className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1">
          {copied === "urls" ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />} Copy Peer URLs
        </button>
        {currentRun && currentRun.status !== "completed" && currentRun.status !== "skipped" && (
          <>
            <button onClick={() => handleSnooze(currentRun.id)} className="text-xs text-amber-400 hover:text-amber-300">
              Snooze 1 ngày
            </button>
            <button onClick={() => handleRunStatus(currentRun.id, "skipped", "Skipped by user")} className="text-xs text-muted hover:text-slate-400">
              Skip
            </button>
            <button onClick={() => handleRunStatus(currentRun.id, "completed")} className="text-xs text-emerald-400 hover:text-emerald-300">
              Mark complete
            </button>
          </>
        )}
      </div>

      {/* Key rules reminder */}
      <div className="text-xs text-muted bg-slate-800/30 rounded p-2 mb-4 space-y-0.5">
        <div>⚠️ Ô trống = không nhìn thấy. Số 0 = đã nhìn thấy và bằng 0.</div>
        <div>⚠️ Shares bị ẩn phải để trống. Likes không phải followers.</div>
        <div>⚠️ Không nhập reach, impressions, CTR, watch time.</div>
      </div>

      {/* Per-peer items */}
      {currentRun && currentRun.items.length > 0 ? (
        <div className="space-y-1">
          <div className="text-xs font-medium text-muted uppercase tracking-wide mb-2">Per-peer progress</div>
          {currentRun.items.map((item) => (
            <div key={item.id} className="flex items-center justify-between text-sm py-1.5 border-b border-slate-800/50">
              <div className="flex items-center gap-2 min-w-0">
                {item.status === "complete" ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                ) : item.status === "collecting" ? (
                  <Clock className="w-4 h-4 text-amber-500 flex-shrink-0" />
                ) : (
                  <div className="w-4 h-4 rounded-full border border-slate-600 flex-shrink-0" />
                )}
                <a href={item.page.canonicalUrl} target="_blank" rel="noopener noreferrer" className="text-purple-400 hover:underline truncate">
                  {item.page.name}
                </a>
                <span className="text-xs text-muted flex-shrink-0">{item.page.scaleBand}</span>
              </div>
              <div className="text-xs tabular-nums text-muted flex-shrink-0">
                {item.collectedPosts}/{item.targetPosts}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-sm text-muted">
          {currentRun ? "Chưa có items." : "Chưa đến lịch thu thập (Thứ Tư 18:00)."}
        </div>
      )}

      {/* Incomplete previous runs */}
      {incompleteRuns.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-800">
          <div className="text-xs font-medium text-amber-400 uppercase tracking-wide mb-2">⚠️ Chưa hoàn thành</div>
          {incompleteRuns.map((run) => (
            <div key={run.id} className="text-xs text-muted mb-1">
              Tuần {new Date(run.weekStart).toLocaleDateString("vi-VN")} — {run.items.filter((i) => i.status === "complete").length}/{run.items.length} pages
              {" "}
              <button onClick={() => handleRunStatus(run.id, "completed")} className="text-emerald-400 hover:underline">mark done</button>
              {" "}
              <button onClick={() => handleRunStatus(run.id, "skipped", "Old incomplete run")} className="text-muted hover:underline">skip</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SummaryCard({ label, value, accent }: { label: string; value: string; accent?: "emerald" | "amber" }) {
  const color = accent === "emerald" ? "text-emerald-400" : accent === "amber" ? "text-amber-400" : "";
  return (
    <div className="bg-slate-800/30 rounded p-2 text-center">
      <div className="text-xs text-muted">{label}</div>
      <div className={`text-lg font-bold tabular-nums ${color}`}>{value}</div>
    </div>
  );
}
