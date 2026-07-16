"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Bell,
  AlertTriangle,
  CheckCircle2,
  Download,
  Calendar,
  ExternalLink,
  Upload,
  Copy,
  Check,
} from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import ErrorBox from "@/components/ErrorBox";
import BenchmarkReminderSection from "./BenchmarkReminderSection";

interface ReminderItem {
  id: number;
  code: string;
  title: string;
  priority: string;
  required: boolean;
  platform: string;
  pageName: string;
  dateRangeStart: string;
  dateRangeEnd: string;
  preset: string;
  dataView: string;
  contentLevel: string;
  filterMode: string;
  expectedFilename: string;
  purpose: string | null;
  note: string | null;
  status: string;
}

interface ReminderRun {
  id: number;
  type: string;
  periodStart: string;
  periodEnd: string;
  dueAt: string;
  status: string;
  overdue: boolean;
  items: ReminderItem[];
}

interface HealthCheck {
  latestVideoDailyDate: string | null;
  latestImportDate: string | null;
  latestImportFile: string | null;
  previousWeekEnd: string;
  videoStale: boolean;
  importStale: boolean;
}

interface ApiError {
  code?: string;
  message: string;
}

const STATUS_LABELS: Record<string, string> = {
  pending: "Chưa làm",
  meta_created: "Đã tạo export",
  downloaded: "Đã tải file",
  renamed: "Đã đổi tên",
  moved_to_incoming: "Đã đưa vào incoming",
  dry_run_ok: "Dry-run OK",
  applied_ok: "Applied OK ✅",
};

export default function DataRemindersPage() {
  const [weeklyRun, setWeeklyRun] = useState<ReminderRun | null>(null);
  const [monthlyRun, setMonthlyRun] = useState<ReminderRun | null>(null);
  const [health, setHealth] = useState<HealthCheck | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch("/api/data-reminders/current").then((x) => x.json());
      if (r.ok) {
        setWeeklyRun(r.data.weeklyRun);
        setMonthlyRun(r.data.monthlyRun);
        setHealth(r.data.healthCheck);
      } else {
        setError(r.error);
      }
    } catch (e: any) {
      setError({ message: e?.message ?? String(e) });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function updateItemStatus(itemId: number, status: string) {
    try {
      await fetch(`/api/data-reminders/item/${itemId}/check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      load();
    } catch {}
  }

  function copyToClipboard(text: string, key: string) {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(key);
      setTimeout(() => setCopied(null), 1500);
    });
  }

  const weeklyOverdue = weeklyRun?.overdue;
  const monthlyOverdue = monthlyRun?.overdue;

  // Build "today" summary
  const todayItems: string[] = [];
  if (weeklyRun) {
    for (const item of weeklyRun.items) {
      if (item.status !== "applied_ok") {
        todayItems.push(`${item.code}: ${item.title}`);
      }
    }
  }
  if (monthlyRun) {
    for (const item of monthlyRun.items) {
      if (item.status !== "applied_ok") {
        todayItems.push(`${item.code}: ${item.title}`);
      }
    }
  }

  return (
    <>
      <PageHeader
        title="Nhắc cập nhật dữ liệu"
        subtitle="Hằng tuần Thứ Hai — tải file từ Meta Business Suite"
        icon={<Bell className="w-5 h-5" />}
        actions={
          <a href="/api/data-reminders/ics" className="btn-secondary" download>
            <Download className="w-4 h-4" />
            <span className="hidden sm:inline">Calendar (.ics)</span>
          </a>
        }
      />

      {/* Overdue banners */}
      {weeklyOverdue && (
        <div className="glass-card p-4 mb-5 border-red-500/40 bg-red-500/10">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
            <div className="text-sm text-red-300">
              <strong>Quá hạn tuần!</strong> Chưa cập nhật data tuần {weeklyRun?.periodStart} → {weeklyRun?.periodEnd}.
            </div>
          </div>
        </div>
      )}
      {monthlyOverdue && (
        <div className="glass-card p-4 mb-5 border-orange-500/40 bg-orange-500/10">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-orange-400 shrink-0" />
            <div className="text-sm text-orange-300">
              <strong>Monthly refresh quá hạn!</strong> Tháng này cần làm mới YTD data.
            </div>
          </div>
        </div>
      )}

      {/* Health warnings */}
      {health?.videoStale && (
        <div className="glass-card p-3 mb-5 border-amber-500/30">
          <div className="flex items-center gap-2 text-xs text-amber-400">
            <Calendar className="w-4 h-4" />
            Video daily data mới nhất: {health.latestVideoDailyDate ?? "—"} — chưa đến {health.previousWeekEnd}.
          </div>
        </div>
      )}
      {health?.importStale && (
        <div className="glass-card p-3 mb-5 border-amber-500/30">
          <div className="flex items-center gap-2 text-xs text-amber-400">
            <Calendar className="w-4 h-4" />
            Có thể data tuần trước chưa được apply. Import mới nhất: {health.latestImportFile?.slice(0, 30) ?? "—"}
          </div>
        </div>
      )}

      {/* Benchmark Weekly Collection section */}
      <BenchmarkReminderSection />

      {/* Today summary */}
      {todayItems.length > 0 && (
        <div className="glass-card p-4 mb-5">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-sm" style={{ color: "var(--text-main)" }}>📋 Hôm nay bạn cần làm gì?</h3>
            <div className="flex gap-1">
              <button
                onClick={() => copyToClipboard(todayItems.join("\n"), "checklist")}
                className="btn-icon"
                title="Copy checklist"
              >
                {copied === "checklist" ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <ul className="space-y-1 text-sm">
            {todayItems.map((item, i) => (
              <li key={i} className="flex gap-2 text-muted">
                <span className="text-neon-purple">☐</span> {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {error && <div className="mb-5"><ErrorBox error={error} onRetry={load} /></div>}

      {/* Don't-miss warnings */}
      <div className="glass-card p-4 mb-6 border-amber-500/20">
        <h3 className="font-medium text-sm mb-3 text-amber-400">⚠️ Đừng chọn nhầm</h3>
        <ul className="space-y-1.5 text-xs text-muted">
          <li><strong className="text-amber-400">Không:</strong> Bài viết / Hằng ngày / Hoạt động — Activity chỉ gồm video posts.</li>
          <li><strong className="text-amber-400">Không:</strong> Trang / Hằng ngày / Hiệu quả — chưa tìm thấy trong Content export.</li>
          <li><strong className="text-amber-400">Không:</strong> Map &ldquo;Lượt hiển thị quảng cáo&rdquo; vào organic impressions.</li>
          <li><strong className="text-amber-400">Không:</strong> Gọi video views là reach.</li>
          <li><strong className="text-amber-400">Không:</strong> Reach cộng gộp ≠ unique Page reach.</li>
        </ul>
      </div>

      {/* Weekly section */}
      {weeklyRun && (
        <div className="space-y-4 mb-6">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold" style={{ color: "var(--text-main)" }}>
              📅 Weekly Update: {weeklyRun.periodStart} → {weeklyRun.periodEnd}
            </h2>
            <span className={`badge ${weeklyOverdue ? "badge-high" : weeklyRun.status === "completed" ? "badge-low" : "badge-medium"}`}>
              {weeklyRun.status === "completed" ? "Hoàn thành" : weeklyOverdue ? "Quá hạn" : "Đang chờ"}
            </span>
          </div>
          {weeklyRun.items.map((item) => (
            <ReminderCard key={item.id} item={item} onStatusChange={updateItemStatus} onCopy={copyToClipboard} copied={copied} />
          ))}
        </div>
      )}

      {/* Monthly section */}
      {monthlyRun && (
        <div className="space-y-4 mb-6">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold" style={{ color: "var(--text-main)" }}>
              🔄 Monthly Refresh: YTD → {monthlyRun.periodEnd}
            </h2>
            <span className={`badge ${monthlyOverdue ? "badge-high" : monthlyRun.status === "completed" ? "badge-low" : "badge-medium"}`}>
              {monthlyRun.status === "completed" ? "Hoàn thành" : monthlyOverdue ? "Quá hạn" : "Đang chờ"}
            </span>
          </div>
          <p className="text-xs text-muted">
            Làm mới dữ liệu YTD để các bài/video cũ được cập nhật lifetime metrics. Monthly refresh sẽ tiếp tục hiện nếu chưa completed.
          </p>
          {monthlyRun.items.map((item) => (
            <ReminderCard key={item.id} item={item} onStatusChange={updateItemStatus} onCopy={copyToClipboard} copied={copied} />
          ))}
        </div>
      )}

      {/* Next steps */}
      {weeklyRun && (
        <div className="glass-card p-4">
          <h3 className="font-medium text-sm mb-2" style={{ color: "var(--text-main)" }}>Bước tiếp theo</h3>
          <p className="text-sm text-muted mb-3">
            Sau khi đã đưa file vào <code>imports/incoming/</code>:
          </p>
          <Link href="/imports" className="btn-primary">
            <Upload className="w-4 h-4" /> Mở trang Import
          </Link>
        </div>
      )}

      {loading && <div className="skeleton h-32 w-full" />}
    </>
  );
}

function ReminderCard({ item, onStatusChange, onCopy, copied }: {
  item: ReminderItem;
  onStatusChange: (id: number, status: string) => void;
  onCopy: (text: string, key: string) => void;
  copied: string | null;
}) {
  const priorityColor =
    item.priority.startsWith("P0") ? "text-red-400" :
    item.priority.startsWith("P1") ? "text-amber-400" : "text-muted";
  const done = item.status === "applied_ok";

  return (
    <div className={`glass-card p-4 ${done ? "border-green-500/30" : ""}`}>
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm font-bold" style={{ color: "var(--text-main)" }}>{item.code}</span>
            <span className="text-sm" style={{ color: "var(--text-main)" }}>{item.title}</span>
            {done && <CheckCircle2 className="w-4 h-4 text-green-400" />}
          </div>
          <div className="text-xs mt-1">
            <span className={priorityColor}>{item.priority}</span>
            {item.required ? " · Bắt buộc" : " · Nên có"}
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => onCopy(item.expectedFilename, `fn-${item.id}`)}
            className="btn-icon"
            title="Copy filename"
          >
            {copied === `fn-${item.id}` ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
          <select
            value={item.status}
            onChange={(e) => onStatusChange(item.id, e.target.value)}
            className="select w-auto !py-1 !text-xs"
          >
            {Object.entries(STATUS_LABELS).map(([val, label]) => (
              <option key={val} value={val}>{label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="text-xs space-y-1 text-muted mb-3">
        <div>📅 <strong>Khoảng ngày:</strong> {item.dateRangeStart} → {item.dateRangeEnd}</div>
        <div>⚙️ <strong>Preset:</strong> {item.preset} · <strong>Xem:</strong> {item.dataView} · <strong>Nội dung:</strong> {item.contentLevel} · <strong>Bộ lọc:</strong> {item.filterMode}</div>
        <div>📁 <strong>Filename:</strong> <code className="text-xs">{item.expectedFilename}</code></div>
        {item.purpose && <div>💡 {item.purpose}</div>}
        {item.note && <div className="text-amber-400">⚠️ {item.note}</div>}
      </div>

      <details className="text-xs">
        <summary className="cursor-pointer text-muted hover:text-slate-300">Hướng dẫn từng bước trong Meta →</summary>
        <ol className="mt-2 space-y-1 text-muted list-decimal list-inside">
          <li>Mở <a href="https://business.facebook.com/latest/" target="_blank" rel="noreferrer" className="text-neon-purple hover:underline inline-flex items-center gap-0.5">Meta Business Suite <ExternalLink className="w-3 h-3" /></a></li>
          <li>Thông tin chi tiết → Nội dung → Xuất dữ liệu</li>
          <li>Tab: {item.platform}</li>
          <li>Page: {item.pageName}</li>
          <li>Khoảng ngày: {item.dateRangeStart} → {item.dateRangeEnd}</li>
          <li>Số liệu đặt sẵn: {item.preset}</li>
          <li>Chế độ xem dữ liệu: {item.dataView}</li>
          <li>Cấp độ nội dung: {item.contentLevel}</li>
          <li>Bộ lọc: {item.filterMode}</li>
          <li>Bấm: Tạo</li>
          <li>Tải file xuống</li>
          <li>Đổi tên thành: <code>{item.expectedFilename}</code></li>
        </ol>
      </details>
    </div>
  );
}
