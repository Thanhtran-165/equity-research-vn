"use client";

import { useState, useEffect } from "react";
import { Upload, FileSpreadsheet, Hand, Info, CheckCircle2, AlertTriangle, ArrowLeft } from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import ErrorBox from "@/components/ErrorBox";

interface PageOption {
  id: number;
  name: string;
  benchmarkRole: string;
  isOwnPage: boolean;
  canonicalUrl: string;
}

interface CsvPreviewRow {
  postUrl: string;
  pageResolved: boolean;
  pageName?: string | null;
  reactions: number | null;
  comments: number | null;
  shares: number | null;
  comparableEngagement: number | null;
  warnings: string[];
}

interface QualityGate {
  id: string;
  label: string;
  status: "pass" | "warn" | "fail";
  detail: string;
  metric?: number;
}

interface PilotValidation {
  totalRows: number;
  validRows: number;
  skippedRows: number;
  uniquePages: number;
  expectedCorePeersPresent: string[];
  postsPerPage: { name: string; count: number }[];
  reactionsCoverage: number;
  commentsCoverage: number;
  sharesCoverage: number;
  publicVideoViewsCoverage: number;
  audienceFollowerCoverage: number;
  blankMetricCount: number;
  observedZeroCount: number;
  duplicatePostUrlCount: number;
  ignoredForbiddenColumns: string[];
  staleCapturedAtCount: number;
  gates: QualityGate[];
  overallStatus: "pass" | "warn" | "fail";
}

export default function ImportPage() {
  const [pages, setPages] = useState<PageOption[]>([]);
  const [selectedPageId, setSelectedPageId] = useState("");
  const [csvText, setCsvText] = useState("");
  const [preview, setPreview] = useState<{ preview: CsvPreviewRow[]; totalRows: number; skipped: number; dryRun: boolean; warnings: string[]; validation?: PilotValidation } | null>(null);
  const [applyResult, setApplyResult] = useState<{ imported: number; skipped: number; errors: string[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showManual, setShowManual] = useState(false);

  // Manual form state
  const [manualForm, setManualForm] = useState({
    postUrl: "", postedAt: "", reactions: "", comments: "", shares: "", videoViews: "", textSnippet: "", contentType: "", topicTag: "",
  });

  useEffect(() => {
    fetch("/api/public-benchmark/pages")
      .then((r) => r.json())
      .then((d) => {
        setPages(d.pages || []);
      })
      .catch(() => {});
  }, []);

  const handlePreview = async () => {
    if (!csvText.trim()) return;
    setLoading(true);
    setError(null);
    setApplyResult(null);
    try {
      const res = await fetch("/api/public-benchmark/posts/import-csv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ csv: csvText, dryRun: true, defaultPageId: selectedPageId || null }),
      });
      const data = await res.json();
      if (data.error) {
        setError(data.error);
      } else {
        setPreview(data);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async () => {
    if (!csvText.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/public-benchmark/posts/import-csv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ csv: csvText, dryRun: false, defaultPageId: selectedPageId || null }),
      });
      const data = await res.json();
      if (data.error) {
        setError(data.error);
      } else {
        setApplyResult(data);
        setPreview(null);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  };

  const handleManualSubmit = async () => {
    if (!selectedPageId || !manualForm.postUrl) {
      setError("Cần chọn page và nhập post URL");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/public-benchmark/posts/manual", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          benchmarkPageId: selectedPageId,
          ...manualForm,
          reactions: manualForm.reactions || null,
          comments: manualForm.comments || null,
          shares: manualForm.shares || null,
          videoViews: manualForm.videoViews || null,
        }),
      });
      const data = await res.json();
      if (data.error) {
        setError(data.error);
      } else {
        setManualForm({ postUrl: "", postedAt: "", reactions: "", comments: "", shares: "", videoViews: "", textSnippet: "", contentType: "", topicTag: "" });
        setApplyResult({ imported: 1, skipped: 0, errors: [] });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSyncOwnPage = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/public-benchmark/sync-own-page", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      if (data.error) {
        setError(data.error);
      } else {
        setApplyResult({ imported: data.synced, skipped: data.skipped, errors: data.errors || [] });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <PageHeader
        title="Nhập dữ liệu Benchmark"
        subtitle="Nhập thủ công hoặc CSV cho public engagement metrics"
        icon={<Upload className="w-5 h-5" />}
        actions={<a href="/public-benchmark" className="text-sm text-cyan-400 hover:text-cyan-300 flex items-center gap-1"><ArrowLeft className="w-3.5 h-3.5" /> Quay lại</a>}
      />

      {error && <ErrorBox error={error} onRetry={() => setError(null)} />}

      {/* Info banner */}
      <div className="card p-4 border-l-4 border-cyan-500/50">
        <div className="flex gap-3">
          <Info className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm space-y-1">
            <p className="font-medium">Quy tắc nhập liệu</p>
            <ul className="list-disc list-inside space-y-0.5 text-muted">
              <li><strong>Ô trống</strong> = chưa quan sát (null), <strong>không</strong> phải zero</li>
              <li><strong>Nhập &ldquo;0&rdquo;</strong> = đã quan sát, giá trị bằng 0</li>
              <li>Comparable engagement = reactions + comments (metric luôn có cho mọi page)</li>
              <li>Shares có thể null — không tự động chuyển thành 0</li>
              <li><strong className="text-rose-400">Không dùng Meta Business Suite export cho page đối thủ</strong> — chỉ cho page mình sở hữu</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Sync own page */}
      <section>
        <h2 className="text-sm font-semibold text-muted uppercase tracking-wide mb-3">Đồng bộ Chim Cút</h2>
        <div className="card p-4 flex items-center justify-between">
          <div className="text-sm">
            <p className="font-medium">Sync từ Post table (MBS CSV) → BenchmarkPost</p>
            <p className="text-muted text-xs mt-0.5">Chỉ lấy reactions, comments, shares, videoViews — không lấy reach/clicks/watchTime</p>
          </div>
          <button
            onClick={handleSyncOwnPage}
            disabled={loading}
            className="btn-primary text-sm px-4 py-2 rounded-lg disabled:opacity-50"
          >
            Sync
          </button>
        </div>
      </section>

      {/* CSV Import */}
      <section>
        <h2 className="text-sm font-semibold text-muted uppercase tracking-wide mb-3 flex items-center gap-2">
          <FileSpreadsheet className="w-4 h-4" /> Nhập CSV
        </h2>
        <div className="card p-4 space-y-3">
          <div>
            <label className="text-xs text-muted block mb-1">Page mặc định (nếu CSV không có cột pageUrl/pageName)</label>
            <select
              value={selectedPageId}
              onChange={(e) => setSelectedPageId(e.target.value)}
              className="w-full bg-slate-100 dark:bg-slate-800 rounded-lg px-3 py-2 text-sm border border-slate-200 dark:border-slate-700"
            >
              <option value="">— Tự động nhận diện từ CSV —</option>
              {pages.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.benchmarkRole}){p.isOwnPage ? " ★" : ""}
                </option>
              ))}
            </select>
          </div>
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs text-muted">CSV nội dung (dán trực tiếp)</label>
              <a href="/api/public-benchmark/template.csv" className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1">
                <FileSpreadsheet className="w-3 h-3" /> Download template
              </a>
            </div>
            <textarea
              value={csvText}
              onChange={(e) => setCsvText(e.target.value)}
              placeholder={`postUrl,postedAt,reactions,comments,shares\nhttps://facebook.com/.../posts/123,2026-07-10,150,12,5\nhttps://facebook.com/.../posts/456,2026-07-09,,8,`}
              rows={6}
              className="w-full bg-slate-100 dark:bg-slate-800 rounded-lg px-3 py-2 text-sm font-mono border border-slate-200 dark:border-slate-700"
            />
          </div>
          <div className="flex gap-2">
            <button onClick={handlePreview} disabled={loading || !csvText.trim()} className="btn-secondary text-sm px-4 py-2 rounded-lg disabled:opacity-50">
              Dry run
            </button>
            <button onClick={handleApply} disabled={loading || !csvText.trim()} className="btn-primary text-sm px-4 py-2 rounded-lg disabled:opacity-50">
              Apply
            </button>
          </div>
        </div>
      </section>

      {/* CSV Preview */}
      {preview && (
        <section>
          <h3 className="text-sm font-semibold text-muted uppercase tracking-wide mb-3">Dry run preview</h3>
          <div className="card p-4 space-y-3">
            <div className="flex gap-4 text-sm flex-wrap">
              <span>Tổng rows: <strong>{preview.totalRows}</strong></span>
              <span>Skipped: <strong>{preview.skipped}</strong></span>
              {preview.validation && (
                <>
                  <span>Unique pages: <strong>{preview.validation.uniquePages}</strong></span>
                  <span>Blank metrics: <strong>{preview.validation.blankMetricCount}</strong></span>
                  <span>Observed zeros: <strong>{preview.validation.observedZeroCount}</strong></span>
                </>
              )}
            </div>

            {/* Pilot validation gates */}
            {preview.validation && (
              <div className="space-y-1">
                <div className={`text-xs font-medium flex items-center gap-1 ${
                  preview.validation.overallStatus === "pass" ? "text-emerald-500" :
                  preview.validation.overallStatus === "warn" ? "text-amber-500" : "text-rose-500"
                }`}>
                  {preview.validation.overallStatus === "pass" ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertTriangle className="w-3.5 h-3.5" />}
                  Pilot validation: {preview.validation.overallStatus.toUpperCase()}
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-1">
                  {preview.validation.gates.map((g) => (
                    <div key={g.id} className={`text-xs p-1.5 rounded border flex items-start gap-2 ${
                      g.status === "pass" ? "bg-emerald-500/5 border-emerald-500/20" :
                      g.status === "warn" ? "bg-amber-500/5 border-amber-500/20" : "bg-rose-500/5 border-rose-500/20"
                    }`}>
                      <span className={`mt-0.5 ${
                        g.status === "pass" ? "text-emerald-500" :
                        g.status === "warn" ? "text-amber-500" : "text-rose-500"
                      }`}>
                        {g.status === "pass" ? "✓" : g.status === "warn" ? "⚠" : "✗"}
                      </span>
                      <span className="text-muted">{g.label}: {g.detail}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {preview.warnings.length > 0 && (
              <div className="text-xs text-amber-500">{preview.warnings.join(", ")}</div>
            )}
            <table className="w-full text-xs">
              <thead className="text-muted">
                <tr>
                  <th className="text-left p-1">Page</th>
                  <th className="text-left p-1">Post URL</th>
                  <th className="text-center p-1">Resolved</th>
                  <th className="text-right p-1">Reactions</th>
                  <th className="text-right p-1">Comments</th>
                  <th className="text-right p-1">Shares</th>
                  <th className="text-right p-1">Comp. Eng.</th>
                </tr>
              </thead>
              <tbody>
                {preview.preview.map((r, i) => (
                  <tr key={i} className="border-t border-slate-100 dark:border-slate-800">
                    <td className="p-1 max-w-[100px] truncate text-muted">{r.pageName || "—"}</td>
                    <td className="p-1 max-w-xs truncate">{r.postUrl}</td>
                    <td className="p-1 text-center">{r.pageResolved ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 inline" /> : <AlertTriangle className="w-3.5 h-3.5 text-amber-500 inline" />}</td>
                    <td className="p-1 text-right tabular-nums">{r.reactions ?? "—"}</td>
                    <td className="p-1 text-right tabular-nums">{r.comments ?? "—"}</td>
                    <td className="p-1 text-right tabular-nums">{r.shares ?? "—"}</td>
                    <td className="p-1 text-right tabular-nums font-medium">{r.comparableEngagement ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Manual entry */}
      <section>
        <button
          onClick={() => setShowManual(!showManual)}
          className="text-sm font-semibold text-muted uppercase tracking-wide flex items-center gap-2 mb-3"
        >
          <Hand className="w-4 h-4" /> Nhập thủ công {showManual ? "−" : "+"}
        </button>
        {showManual && (
          <div className="card p-4 space-y-3">
            <div>
              <label className="text-xs text-muted block mb-1">Page *</label>
              <select
                value={selectedPageId}
                onChange={(e) => setSelectedPageId(e.target.value)}
                className="w-full bg-slate-100 dark:bg-slate-800 rounded-lg px-3 py-2 text-sm border border-slate-200 dark:border-slate-700"
              >
                <option value="">— Chọn page —</option>
                {pages.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}{p.isOwnPage ? " ★" : ""}</option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Input label="Post URL *" value={manualForm.postUrl} onChange={(v) => setManualForm({ ...manualForm, postUrl: v })} placeholder="https://facebook.com/..." />
              <Input label="Posted date" value={manualForm.postedAt} onChange={(v) => setManualForm({ ...manualForm, postedAt: v })} placeholder="2026-07-10" />
              <Input label="Reactions" value={manualForm.reactions} onChange={(v) => setManualForm({ ...manualForm, reactions: v })} placeholder="150 hoặc để trống" />
              <Input label="Comments" value={manualForm.comments} onChange={(v) => setManualForm({ ...manualForm, comments: v })} placeholder="12 hoặc để trống" />
              <Input label="Shares" value={manualForm.shares} onChange={(v) => setManualForm({ ...manualForm, shares: v })} placeholder="5 hoặc để trống" />
              <Input label="Video views" value={manualForm.videoViews} onChange={(v) => setManualForm({ ...manualForm, videoViews: v })} placeholder="1000 hoặc để trống" />
              <Input label="Content type" value={manualForm.contentType} onChange={(v) => setManualForm({ ...manualForm, contentType: v })} placeholder="reel/video/image/text" />
              <Input label="Topic tag" value={manualForm.topicTag} onChange={(v) => setManualForm({ ...manualForm, topicTag: v })} placeholder="macro/stocks/gold" />
            </div>
            <Input label="Text snippet" value={manualForm.textSnippet} onChange={(v) => setManualForm({ ...manualForm, textSnippet: v })} placeholder="Nội dung bài viết (tùy chọn)" />
            <button onClick={handleManualSubmit} disabled={loading} className="btn-primary text-sm px-4 py-2 rounded-lg disabled:opacity-50">
              Lưu bài
            </button>
          </div>
        )}
      </section>

      {/* Apply result */}
      {applyResult && (
        <div className="card p-4 border-l-4 border-emerald-500/50">
          <div className="flex items-center gap-2 text-sm">
            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
            <span className="font-medium">Imported: {applyResult.imported}</span>
            {applyResult.skipped > 0 && <span className="text-amber-500">Skipped: {applyResult.skipped}</span>}
            {applyResult.errors.length > 0 && (
              <span className="text-rose-500">Errors: {applyResult.errors.length}</span>
            )}
          </div>
          {applyResult.errors.length > 0 && (
            <ul className="mt-2 text-xs text-rose-400 list-disc list-inside">
              {applyResult.errors.slice(0, 5).map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

function Input({ label, value, onChange, placeholder }: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string;
}) {
  return (
    <div>
      <label className="text-xs text-muted block mb-1">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-slate-100 dark:bg-slate-800 rounded-lg px-3 py-2 text-sm border border-slate-200 dark:border-slate-700"
      />
    </div>
  );
}
