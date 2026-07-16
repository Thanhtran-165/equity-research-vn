"use client";

import { useState } from "react";
import { Download, AlertTriangle } from "lucide-react";

/**
 * MOCK Meta Business Suite Export — local only, NOT real Meta.
 * Dùng để test download flow + watched folder + import pipeline.
 */
const PLATFORMS = ["Facebook", "Instagram"];
const CONTENT_LEVELS = ["Bài viết / Posts", "Video", "Trang / Page"];
const DATA_VIEWS = ["Trọn đời / Lifetime", "Hằng ngày / Daily"];
const FILTERS = ["Ngày tạo / Created date", "Hoạt động / Activity", "—"];
const PRESETS = [
  "Đã đăng / Published",
  "Hiệu quả / Performance",
  "Đối tượng / Audience",
  "Tỷ lệ giữ chân / Retention",
  "Thu nhập / Earnings",
];

export default function MockMetaExportPage() {
  const [platform, setPlatform] = useState("Facebook");
  const [page, setPage] = useState("Chim Cút");
  const [contentLevel, setContentLevel] = useState("Bài viết / Posts");
  const [dataView, setDataView] = useState("Trọn đời / Lifetime");
  const [filter, setFilter] = useState("Ngày tạo / Created date");
  const [preset, setPreset] = useState("Đã đăng / Published");
  const [dateRange, setDateRange] = useState("2026-07-01 to 2026-07-31");
  const [generated, setGenerated] = useState(false);

  function handleExport() {
    // Generate mock CSV
    const slug = page.toLowerCase().replace(/\s+/g, "");
    const cl = contentLevel.split(" / ")[1]?.toLowerCase().replace(/\s+/g, "_") ?? "posts";
    const dv = dataView.split(" / ")[1]?.toLowerCase() ?? "lifetime";
    const fl = filter === "—" ? "none" : filter.split(" / ")[1]?.toLowerCase().replace(/\s+/g, "_") ?? "created";
    const ps = preset.split(" / ")[1]?.toLowerCase().replace(/\s+/g, "_") ?? "published";
    const filename = `${slug}_fb_${cl}_${dv}_${fl}_${ps}_mock.csv`;

    const headers = [
      "Post ID", "Page ID", "Page Name", "Title", "Description",
      "Duration (seconds)", "Posted", "Permalink", "Post type", "Language",
      "Date", "Views", "Reach", "Reactions, comments and shares",
      "Reactions", "Comments", "Shares", "Watch time (seconds)",
      "Average watch time", "Total clicks",
      "Organic views", "Paid views", "Organic reach", "Paid reach",
      "3-second video views", "1-minute video views",
    ];
    const rows: string[] = [];
    for (let i = 0; i < 10; i++) {
      const reach = Math.floor(Math.random() * 5000) + 50;
      const reactions = Math.floor(reach * 0.02);
      const comments = Math.floor(reach * 0.005);
      const shares = Math.floor(reach * 0.003);
      const views = Math.floor(reach * 2.5);
      rows.push([
        `mock_${Date.now()}_${i}`, "198980770851754", page,
        `Mock post ${i + 1}`, `This is a mock post description ${i + 1}`,
        String(Math.floor(Math.random() * 60) + 10),
        `2026-07-${String(i + 1).padStart(2, "0")}T10:00:00+0000`,
        `https://facebook.com/chimcutvnindex/posts/mock_${i}`,
        i % 3 === 0 ? "Video" : i % 3 === 1 ? "Photo" : "Text",
        "Vietnamese",
        `7/${i + 1}/2026`,
        String(views), String(reach), String(reactions + comments + shares),
        String(reactions), String(comments), String(shares),
        String(Math.floor(Math.random() * 100000)),
        String((Math.random() * 15).toFixed(3)),
        String(Math.floor(reach * 0.1)),
        String(views), "0", String(reach), "0",
        String(Math.floor(views * 0.7)), String(Math.floor(views * 0.1)),
      ].map((c) => `"${c}"`).join(","));
    }

    const csv = headers.map((h) => `"${h}"`).join(",") + "\n" + rows.join("\n");

    // Download
    const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    setGenerated(true);
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">MOCK Meta Business Suite Export</h1>
        <p className="text-sm text-muted">Local simulation — NOT real Meta. Dùng để test download + import pipeline.</p>
      </div>

      <div className="glass-card p-4 border-amber-500/30 bg-amber-500/5">
        <div className="flex items-start gap-2 text-sm text-amber-400">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>Đây là mock page giả lập UI export. KHÔNG kết nối tới Meta. File tạo ra là data giả để test pipeline.</span>
        </div>
      </div>

      <div className="glass-card p-5 space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <label className="text-sm">
            <span className="text-muted block mb-1">Platform</span>
            <select className="select" value={platform} onChange={(e) => setPlatform(e.target.value)}>
              {PLATFORMS.map((p) => <option key={p}>{p}</option>)}
            </select>
          </label>
          <label className="text-sm">
            <span className="text-muted block mb-1">Page</span>
            <input className="input" value={page} onChange={(e) => setPage(e.target.value)} />
          </label>
          <label className="text-sm">
            <span className="text-muted block mb-1">Content level</span>
            <select className="select" value={contentLevel} onChange={(e) => setContentLevel(e.target.value)}>
              {CONTENT_LEVELS.map((c) => <option key={c}>{c}</option>)}
            </select>
          </label>
          <label className="text-sm">
            <span className="text-muted block mb-1">Data view</span>
            <select className="select" value={dataView} onChange={(e) => setDataView(e.target.value)}>
              {DATA_VIEWS.map((d) => <option key={d}>{d}</option>)}
            </select>
          </label>
          <label className="text-sm">
            <span className="text-muted block mb-1">Filter</span>
            <select className="select" value={filter} onChange={(e) => setFilter(e.target.value)}>
              {FILTERS.map((f) => <option key={f}>{f}</option>)}
            </select>
          </label>
          <label className="text-sm">
            <span className="text-muted block mb-1">Preset</span>
            <select className="select" value={preset} onChange={(e) => setPreset(e.target.value)}>
              {PRESETS.map((p) => <option key={p}>{p}</option>)}
            </select>
          </label>
          <label className="text-sm col-span-2">
            <span className="text-muted block mb-1">Date range</span>
            <input className="input" value={dateRange} onChange={(e) => setDateRange(e.target.value)} />
          </label>
        </div>

        <button onClick={handleExport} className="btn-primary w-full">
          <Download className="w-4 h-4" /> Export mock CSV
        </button>

        {generated && (
          <div className="text-sm text-neon-green flex items-center gap-2">
            ✓ File CSV đã download (10 rows mock data). Kiểm tra thư mục Downloads.
          </div>
        )}
      </div>
    </div>
  );
}
