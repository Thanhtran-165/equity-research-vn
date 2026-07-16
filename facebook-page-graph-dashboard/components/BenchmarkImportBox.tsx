"use client";

import React, { useMemo, useState } from "react";
import { parseCsv } from "@/lib/csv";

const SAMPLE_CSV = `pageName,pageUrl,category,periodStart,periodEnd,followers,postsCount,reactionsCount,commentsCount,sharesCount,videoViews,topPostUrl,topPostEngagement,activeAds,dominantTopic,notes
CafeF,https://facebook.com/cafef,chứng khoán,2026-07-01,2026-07-31,1000000,120,50000,7000,3000,2000000,https://facebook.com/cafef/top,5000,true,chứng khoán,
Page Macro ABC,https://facebook.com/macroabc,vĩ mô,2026-07-01,2026-07-31,200000,40,12000,3500,800,300000,https://facebook.com/macroabc/top,1800,false,lãi suất,`;

const REQUIRED = ["pageName", "pageUrl", "periodStart", "periodEnd"];

function findHeaderIndex(headers: string[], name: string): number {
  const lower = headers.map((h) => h.trim().toLowerCase());
  return lower.indexOf(name.toLowerCase());
}

interface ParsedRow {
  raw: string[];
  record: Record<string, string> | null;
  error?: string;
}

export default function BenchmarkImportBox({
  onImported,
}: {
  onImported?: () => void;
}) {
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const parsedPreview = useMemo<{ headers: string[]; rows: ParsedRow[]; missing: string[] }>(() => {
    if (!text.trim()) return { headers: [], rows: [], missing: [] };
    const all = parseCsv(text);
    if (all.length === 0) return { headers: [], rows: [], missing: REQUIRED };
    const headers = all[0].map((h) => h.trim());
    const missing = REQUIRED.filter((h) => findHeaderIndex(headers, h) < 0);
    const rows: ParsedRow[] = [];
    for (let i = 1; i < all.length; i++) {
      const raw = all[i];
      if (raw.length === 1 && !raw[0].trim()) continue;
      const record: Record<string, string> = {};
      headers.forEach((h, idx) => {
        record[h] = (raw[idx] ?? "").trim();
      });
      let err: string | undefined;
      if (!record.pageName || !record.pageUrl || !record.periodStart || !record.periodEnd) {
        err = "Thiếu cột bắt buộc (pageName/pageUrl/periodStart/periodEnd).";
      } else if (
        Number.isNaN(new Date(record.periodStart).getTime()) ||
        Number.isNaN(new Date(record.periodEnd).getTime())
      ) {
        err = "periodStart/periodEnd không đúng định dạng ngày.";
      }
      rows.push({ raw, record: err ? null : record, error: err });
    }
    return { headers, rows, missing };
  }, [text]);

  const validRows = parsedPreview.rows.filter((r) => !r.error).length;
  const invalidRows = parsedPreview.rows.filter((r) => r.error).length;

  async function submit() {
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const r = await fetch("/api/benchmark/import-csv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ csv: text }),
      }).then((x) => x.json());
      if (r.ok) {
        setResult(r.data);
        onImported?.();
      } else {
        setError(r.error?.message ?? "Lỗi không rõ");
      }
    } catch (e: any) {
      setError(e?.message ?? String(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex gap-2">
          <button
            className="btn-secondary"
            onClick={() => setText(SAMPLE_CSV)}
            type="button"
          >
            Tải CSV mẫu
          </button>
          <button
            className="btn-secondary"
            onClick={() => setText("")}
            type="button"
          >
            Xoá
          </button>
        </div>
        <div className="text-xs text-gray-500">
          {parsedPreview.headers.length > 0 ? (
            <>
              {validRows} dòng hợp lệ · {invalidRows} lỗi
              {parsedPreview.missing.length > 0 && (
                <span className="text-red-600 ml-2">
                  thiếu cột: {parsedPreview.missing.join(", ")}
                </span>
              )}
            </>
          ) : (
            "chưa paste CSV"
          )}
        </div>
      </div>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste CSV vào đây. Hàng đầu phải là header theo mẫu."
        className="w-full h-56 px-3 py-2 font-mono text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
        spellCheck={false}
      />

      {parsedPreview.rows.length > 0 && (
        <div className="card p-3">
          <div className="text-xs uppercase tracking-wide text-gray-500 mb-2">
            Preview ({parsedPreview.rows.length} dòng)
          </div>
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th className="text-right">#</th>
                  <th>pageName</th>
                  <th>category</th>
                  <th>period</th>
                  <th className="text-right">followers</th>
                  <th className="text-right">posts</th>
                  <th className="text-right">reactions</th>
                  <th className="text-right">comments</th>
                  <th className="text-right">shares</th>
                  <th>Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {parsedPreview.rows.slice(0, 50).map((r, i) => (
                  <tr key={i}>
                    <td className="text-right text-gray-500">{i + 2}</td>
                    <td>{r.record?.pageName ?? r.raw[0]}</td>
                    <td>{r.record?.category ?? "—"}</td>
                    <td className="whitespace-nowrap text-xs">
                      {r.record?.periodStart ?? "—"} → {r.record?.periodEnd ?? "—"}
                    </td>
                    <td className="text-right">{r.record?.followers ?? "—"}</td>
                    <td className="text-right">{r.record?.postsCount ?? "—"}</td>
                    <td className="text-right">{r.record?.reactionsCount ?? "—"}</td>
                    <td className="text-right">{r.record?.commentsCount ?? "—"}</td>
                    <td className="text-right">{r.record?.sharesCount ?? "—"}</td>
                    <td>
                      {r.error ? (
                        <span className="badge-high">{r.error}</span>
                      ) : (
                        <span className="badge-low">OK</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="flex items-center gap-2">
        <button
          onClick={submit}
          disabled={submitting || validRows === 0}
          className="btn-primary"
          type="button"
        >
          {submitting ? "Đang import…" : `⬇ Import ${validRows} dòng`}
        </button>
        <span className="text-xs text-gray-500">
          Validate trước, chỉ import dòng hợp lệ.
        </span>
      </div>

      {error && (
        <div className="card p-3 border-red-200 bg-red-50 text-sm text-red-700">
          Lỗi: {error}
        </div>
      )}

      {result && (
        <div className="card p-4 border-green-200 bg-green-50">
          <div className="font-semibold text-green-800">
            Import xong: {result.importedRows} dòng thành công
          </div>
          {result.skippedRows > 0 && (
            <div className="text-sm text-amber-700 mt-1">
              Bỏ qua {result.skippedRows} dòng.
            </div>
          )}
          {result.warnings?.length > 0 && (
            <details className="mt-2 text-xs">
              <summary className="cursor-pointer text-gray-700">
                {result.warnings.length} warning(s)
              </summary>
              <ul className="mt-1 space-y-0.5">
                {result.warnings.slice(0, 30).map((w: any, i: number) => (
                  <li key={i} className="text-gray-700">
                    dòng {w.row}: {w.message}
                  </li>
                ))}
              </ul>
            </details>
          )}
          {result.errors?.length > 0 && (
            <details className="mt-2 text-xs">
              <summary className="cursor-pointer text-red-700">
                {result.errors.length} error(s)
              </summary>
              <ul className="mt-1 space-y-0.5">
                {result.errors.slice(0, 30).map((e: any, i: number) => (
                  <li key={i} className="text-red-700">
                    dòng {e.row}: {e.message}
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}

      <details className="card p-3">
        <summary className="cursor-pointer text-sm font-medium">
          Định dạng CSV mẫu (bấm để mở)
        </summary>
        <pre className="mt-2 text-xs bg-gray-50 p-3 rounded overflow-x-auto">
{SAMPLE_CSV}
        </pre>
        <p className="text-xs text-gray-600 mt-2">
          Cột bắt buộc: <code>pageName, pageUrl, periodStart, periodEnd</code>. Các cột
          khác để trống vẫn được (score dùng trọng số fallback nếu thiếu videoViews).
        </p>
      </details>
    </div>
  );
}
