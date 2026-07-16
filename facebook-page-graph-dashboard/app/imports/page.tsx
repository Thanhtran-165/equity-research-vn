"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Upload,
  FileSpreadsheet,
  History,
  CheckCircle2,
  AlertCircle,
  Download,
  RefreshCw,
  Eye,
} from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import ErrorBox from "@/components/ErrorBox";
import EmptyState from "@/components/ui/EmptyState";

interface Batch {
  id: number;
  filename: string;
  source: string;
  importedAt: string;
  rowCount: number;
  matchedCount: number;
  unmatchedCount: number;
  skippedCount: number;
  status: string;
  notes: string | null;
}

interface UploadResult {
  batchId?: number;
  duplicate?: boolean;
  existingBatchId?: number;
  filename: string;
  format?: string;
  rowCount?: number;
  headers?: string[];
  mapping?: Record<string, number | null>;
  warnings?: string[];
  ambiguousFields?: string[];
  preview?: any[];
  meta?: any;
}

export default function ImportsPage() {
  const [batches, setBatches] = useState<Batch[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [applying, setApplying] = useState<number | null>(null);
  const [applyResult, setApplyResult] = useState<any | null>(null);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [editingMapping, setEditingMapping] = useState<Record<string, number | null> | null>(null);
  const [forceOverwrite, setForceOverwrite] = useState(false);
  const [allowVideoViewsOverwrite, setAllowVideoViewsOverwrite] = useState(false);

  const loadHistory = useCallback(async () => {
    setLoadingHistory(true);
    try {
      const r = await fetch("/api/imports/history").then((x) => x.json());
      if (r.ok) setBatches(r.data.batches);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  async function handleFile(file: File) {
    setUploading(true);
    setUploadError(null);
    setUploadResult(null);
    setApplyResult(null);
    setApplyError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await fetch("/api/imports/upload", {
        method: "POST",
        body: fd,
      }).then((x) => x.json());
      if (r.ok) {
        setUploadResult(r.data);
        if (r.data.mapping) setEditingMapping(r.data.mapping);
      } else {
        setUploadError(r.error?.message ?? "Upload failed");
      }
    } catch (e: any) {
      setUploadError(e?.message ?? String(e));
    } finally {
      setUploading(false);
    }
  }

  async function confirmMapping() {
    if (!uploadResult?.batchId || !editingMapping) return;
    setUploading(true);
    try {
      const r = await fetch("/api/imports/confirm-mapping", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          batchId: uploadResult.batchId,
          columnMapping: editingMapping,
        }),
      }).then((x) => x.json());
      if (!r.ok) {
        setUploadError(r.error?.message ?? "Confirm mapping failed");
      }
    } finally {
      setUploading(false);
    }
  }

  async function applyBatch(batchId: number, file: File | null) {
    setApplying(batchId);
    setApplyError(null);
    setApplyResult(null);
    try {
      let r;
      if (file) {
        const fd = new FormData();
        fd.append("file", file);
        fd.append("batchId", String(batchId));
        fd.append("forceOverwrite", String(forceOverwrite));
        fd.append("allowVideoViewsOverwrite", String(allowVideoViewsOverwrite));
        r = await fetch("/api/imports/apply", { method: "POST", body: fd }).then((x) => x.json());
      } else {
        r = await fetch("/api/imports/apply", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            batchId,
            forceOverwrite,
            allowVideoViewsOverwrite,
          }),
        }).then((x) => x.json());
      }
      if (r.ok) {
        setApplyResult(r.data);
        loadHistory();
      } else {
        setApplyError(r.error?.message ?? "Apply failed");
      }
    } catch (e: any) {
      setApplyError(e?.message ?? String(e));
    } finally {
      setApplying(null);
    }
  }

  return (
    <>
      <PageHeader
        title="Imports"
        subtitle="Nhập dữ liệu Meta Business Suite CSV/XLSX — nguồn insight chính thức do Page admin export thủ công"
        icon={<Upload className="w-5 h-5" />}
      />

      <div className="card p-4 mb-4 border-brand-200 dark:border-brand-500/30 bg-brand-50/50 dark:bg-brand-500/5">
        <p className="text-sm text-slate-700 dark:text-slate-200 m-0">
          <strong>Về nguồn dữ liệu:</strong> File CSV/XLSX từ Meta Business Suite là dữ liệu{" "}
          <strong>insight chính thức</strong> do bạn (Page admin) tự export. App coi đây là{" "}
          <code className="text-xs">meta_business_suite_csv</code> metricSource — được phép tính ER
          và đặt làm <strong>true reach</strong> (vì đây là insight thật từ Meta, không phải proxy).
        </p>
        <p className="text-xs text-muted mt-2 m-0">
          Workflow: Meta Business Suite → Insights → Content → Export CSV → upload vào đây.
        </p>
      </div>

      {/* Upload box */}
      <section className="mb-6">
        <h2 className="font-semibold mb-3 flex items-center gap-2">
          <FileSpreadsheet className="w-4 h-4" /> Upload CSV / XLSX
        </h2>
        <label
          className="card p-8 border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-brand-400 dark:hover:border-brand-500 cursor-pointer flex flex-col items-center justify-center gap-2 transition-colors"
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            const f = e.dataTransfer.files?.[0];
            if (f) handleFile(f);
          }}
        >
          <input
            type="file"
            accept=".csv,.xlsx,.xls"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
            }}
          />
          <Upload className="w-8 h-8 text-muted" />
          <div className="text-sm font-medium">
            {uploading ? "Đang upload…" : "Kéo thả file vào đây hoặc bấm để chọn"}
          </div>
          <div className="text-xs text-muted">Hỗ trợ: .csv, .xlsx, .xls</div>
        </label>
        {uploadError && <div className="mt-3"><ErrorBox error={uploadError} /></div>}
      </section>

      {/* Upload result — preview + mapping */}
      {uploadResult && (
        <section className="card p-5 mb-6 animate-fade-in">
          <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
            <h2 className="font-semibold m-0">Preview: {uploadResult.filename}</h2>
            {uploadResult.batchId && (
              <span className="badge-info">batch #{uploadResult.batchId}</span>
            )}
          </div>

          {uploadResult.duplicate && (
            <div className="p-3 mb-3 rounded-lg bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/30 text-sm text-amber-800 dark:text-amber-400">
              ⚠️ File này đã import trước đó (batch #{uploadResult.existingBatchId}). Tránh import
              lại trừ khi muốn overwrite.
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4 text-sm">
            <div>
              <div className="text-xs text-muted">Format</div>
              <div className="font-medium">{uploadResult.format ?? "—"}</div>
            </div>
            <div>
              <div className="text-xs text-muted">Rows</div>
              <div className="font-medium tabular-nums">{uploadResult.rowCount ?? 0}</div>
            </div>
            <div>
              <div className="text-xs text-muted">Columns detected</div>
              <div className="font-medium tabular-nums">{uploadResult.headers?.length ?? 0}</div>
            </div>
            <div>
              <div className="text-xs text-muted">Warnings</div>
              <div className="font-medium tabular-nums">{uploadResult.warnings?.length ?? 0}</div>
            </div>
          </div>

          {uploadResult.warnings && uploadResult.warnings.length > 0 && (
            <div className="mb-4 p-3 rounded-lg bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/30">
              <div className="text-xs uppercase tracking-wide text-amber-700 dark:text-amber-500 mb-1">
                Warnings
              </div>
              <ul className="text-xs text-amber-800 dark:text-amber-400 space-y-0.5 m-0 list-disc list-inside">
                {uploadResult.warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}

          {/* Column mapping editor */}
          {editingMapping && uploadResult.headers && (
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-sm m-0">Column mapping</h3>
                <button onClick={confirmMapping} className="btn-secondary !py-1 !px-2 text-xs">
                  <CheckCircle2 className="w-3 h-3" /> Confirm mapping
                </button>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {Object.entries(editingMapping).map(([field, idx]) => (
                  <label key={field} className="text-xs">
                    <span className="text-muted block">{field}</span>
                    <select
                      value={idx ?? -1}
                      onChange={(e) =>
                        setEditingMapping({
                          ...editingMapping,
                          [field]: e.target.value === "-1" ? null : Number(e.target.value),
                        })
                      }
                      className="select !py-1 !text-xs"
                    >
                      <option value={-1}>(không map)</option>
                      {uploadResult.headers!.map((h, i) => (
                        <option key={i} value={i}>{h}</option>
                      ))}
                    </select>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Preview table */}
          {uploadResult.preview && uploadResult.preview.length > 0 && (
            <div className="mb-4">
              <h3 className="font-medium text-sm mb-2">
                <Eye className="w-3 h-3 inline mr-1" /> Preview (20 dòng đầu)
              </h3>
              <div className="overflow-x-auto scrollbar-thin border border-slate-200 dark:border-slate-800 rounded-lg">
                <table className="table">
                  <thead>
                    <tr>
                      <th>#</th>
                      {uploadResult.headers?.map((h, i) => <th key={i}>{h}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {uploadResult.preview.map((row, i) => (
                      <tr key={i}>
                        <td className="text-muted">{row._rowIndex}</td>
                        {uploadResult.headers?.map((h, j) => (
                          <td key={j} className="text-xs max-w-[200px] truncate">
                            {row[h]}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Apply actions */}
          {uploadResult.batchId && !uploadResult.duplicate && (
            <div className="pt-4 border-t border-slate-200 dark:border-slate-800 space-y-3">
              <div className="flex items-center gap-4 text-xs flex-wrap">
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={forceOverwrite}
                    onChange={(e) => setForceOverwrite(e.target.checked)}
                  />
                  <span>Force overwrite (kể cả <code>facebook_graph_api_insights</code>)</span>
                </label>
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={allowVideoViewsOverwrite}
                    onChange={(e) => setAllowVideoViewsOverwrite(e.target.checked)}
                  />
                  <span>Overwrite video views</span>
                </label>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => applyBatch(uploadResult.batchId!, null)}
                  disabled={applying === uploadResult.batchId}
                  className="btn-primary"
                >
                  <RefreshCw className={`w-4 h-4 ${applying === uploadResult.batchId ? "animate-spin" : ""}`} />
                  Apply (match + import insights)
                </button>
                <span className="text-xs text-muted">
                  Cần file gốc trong <code>imports/incoming/</code>. Nếu lỗi, re-upload qua API apply.
                </span>
              </div>
            </div>
          )}
        </section>
      )}

      {/* Apply result */}
      {applyResult && (
        <section className="card p-5 mb-6 border-success-200 dark:border-success-500/30 bg-success-50/50 dark:bg-success-500/5 animate-fade-in">
          <h2 className="font-semibold mb-3 text-success-800 dark:text-success-400">
            ✓ Apply hoàn tất
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div>
              <div className="text-xs text-muted">Rows</div>
              <div className="font-medium tabular-nums">{applyResult.rowCount}</div>
            </div>
            <div>
              <div className="text-xs text-muted">Matched</div>
              <div className="font-medium tabular-nums text-success-600">{applyResult.matchedCount}</div>
            </div>
            <div>
              <div className="text-xs text-muted">Applied</div>
              <div className="font-medium tabular-nums">{applyResult.appliedCount}</div>
            </div>
            <div>
              <div className="text-xs text-muted">Unmatched</div>
              <div className="font-medium tabular-nums text-amber-600">{applyResult.unmatchedCount}</div>
            </div>
          </div>
          {applyResult.warnings?.length > 0 && (
            <details className="mt-3 text-xs">
              <summary className="cursor-pointer text-muted">{applyResult.warnings.length} warnings</summary>
              <ul className="mt-1 space-y-0.5 text-muted">
                {applyResult.warnings.slice(0, 10).map((w: string, i: number) => <li key={i}>{w}</li>)}
              </ul>
            </details>
          )}
        </section>
      )}

      {applyError && <div className="mb-4"><ErrorBox error={applyError} /></div>}

      {/* Import history */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold m-0 flex items-center gap-2">
            <History className="w-4 h-4" /> Import history
          </h2>
          <button onClick={loadHistory} className="btn-secondary !py-1 !px-2 text-xs">
            <RefreshCw className="w-3 h-3" /> Refresh
          </button>
        </div>

        {loadingHistory ? (
          <div className="card p-4">
            <div className="skeleton h-12 w-full" />
          </div>
        ) : batches.length === 0 ? (
          <EmptyState
            title="Chưa có import nào"
            description="Upload file CSV/XLSX từ Meta Business Suite để bắt đầu."
            icon={<AlertCircle className="w-6 h-6" />}
          />
        ) : (
          <div className="table-wrap">
            <div className="overflow-x-auto scrollbar-thin">
              <table className="table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Filename</th>
                    <th>Source</th>
                    <th className="text-right">Rows</th>
                    <th className="text-right">Matched</th>
                    <th className="text-right">Unmatched</th>
                    <th>Status</th>
                    <th>Imported at</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {batches.map((b) => (
                    <tr key={b.id}>
                      <td>{b.id}</td>
                      <td className="font-mono text-xs">{b.filename}</td>
                      <td><span className="badge-neutral">{b.source}</span></td>
                      <td className="text-right tabular-nums">{b.rowCount}</td>
                      <td className="text-right tabular-nums text-success-600">{b.matchedCount}</td>
                      <td className="text-right tabular-nums text-amber-600">{b.unmatchedCount}</td>
                      <td>
                        <StatusBadge status={b.status} />
                      </td>
                      <td className="text-xs text-muted">{new Date(b.importedAt).toLocaleString("vi-VN")}</td>
                      <td className="text-right">
                        {b.unmatchedCount > 0 && (
                          <a
                            href={`/api/imports/${b.id}/export-unmatched`}
                            className="btn-icon"
                            title="Export unmatched CSV"
                          >
                            <Download className="w-4 h-4" />
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>
    </>
  );
}

function StatusBadge({ status }: { status: string }) {
  const cls =
    status === "imported" ? "badge-low" :
    status === "failed" ? "badge-high" :
    status === "mapped" ? "badge-info" :
    "badge-neutral";
  return <span className={cls}>{status}</span>;
}
