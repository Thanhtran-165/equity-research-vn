/**
 * Export Plan — sinh checklist export CSV/XLSX từ Meta Business Suite.
 *
 * Naming convention:
 *   chimcut_fb_<content_level>_<data_view>_<filter>_<preset>_<period>.csv
 *
 * Priority:
 *   P0 — Post-level master (bắt buộc)
 *   P1 — Page-level + Video (mở rộng)
 *   P2 — Audience/Earnings (tùy chọn)
 */

export type ExportPeriod = "monthly" | "quarterly" | "yearly";
export type ExportPriority = "P0" | "P1" | "P2";

export interface ExportTask {
  id: string;
  priority: ExportPriority;
  platform: string;
  page: string;
  contentLevel: string;
  dataView: string;
  filter: string;
  preset: string;
  dateRange: { start: string; end: string };
  period: ExportPeriod;
  filename: string;
  uiPath: string;
  website: string;
  notes: string;
}

export interface ExportPlanOptions {
  period: ExportPeriod;
  startDate: string; // YYYY-MM-DD or YYYY-MM or YYYY-QX or YYYY
  endDate?: string;
  page?: string; // default: "Chim Cút"
  includeVideo?: boolean;
  includeAudience?: boolean;
  includeUnverifiedPagePerformance?: boolean; // G01 — chưa verified trong Content Export
}

const WEBSITE = "https://business.facebook.com/latest/";
const UI_PATH = "Insights → Content → Export data";

function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

/**
 * Parse period input → date range.
 * - "2026-07" → { start: "2026-07-01", end: "2026-07-31" }
 * - "2026-Q2" → { start: "2026-04-01", end: "2026-06-30" }
 * - "2026" → { start: "2026-01-01", end: "2026-12-31" }
 */
export function parsePeriod(input: string): { start: string; end: string; label: string } {
  const m = input.match(/^(\d{4})-(\d{2})$/);
  if (m) {
    const [, y, mo] = m;
    const year = Number(y);
    const month = Number(mo);
    const start = `${y}-${mo}-01`;
    const lastDay = new Date(year, month, 0).getDate();
    const end = `${y}-${mo}-${pad2(lastDay)}`;
    return { start, end, label: input };
  }
  const q = input.match(/^(\d{4})-Q([1-4])$/i);
  if (q) {
    const [, y, qs] = q;
    const qi = Number(qs);
    const startMonth = (qi - 1) * 3 + 1;
    const endMonth = qi * 3;
    const start = `${y}-${pad2(startMonth)}-01`;
    const lastDay = new Date(Number(y), endMonth, 0).getDate();
    const end = `${y}-${pad2(endMonth)}-${pad2(lastDay)}`;
    return { start, end, label: input };
  }
  const y = input.match(/^(\d{4})$/);
  if (y) {
    return { start: `${input}-01-01`, end: `${input}-12-31`, label: input };
  }
  // Fallback: treat as date range
  return { start: input, end: input, label: input };
}

function makeFilename(
  page: string,
  contentLevel: string,
  dataView: string,
  filter: string,
  preset: string,
  periodLabel: string,
): string {
  const slug = page.toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, "");
  const parts = [
    slug,
    "fb",
    contentLevel.toLowerCase().replace(/\s+/g, "_"),
    dataView.toLowerCase().replace(/\s+/g, "_"),
    filter.toLowerCase().replace(/\s+/g, "_"),
    preset.toLowerCase().replace(/\s+/g, "_"),
    periodLabel.replace(/[^0-9Q]/g, "_").replace(/_+/g, "_").replace(/^_|_$/g, ""),
  ];
  return parts.join("_") + ".csv";
}

/**
 * Sinh danh sách export tasks theo options.
 */
export function generateExportPlan(opts: ExportPlanOptions): ExportTask[] {
  const page = opts.page ?? "Chim Cút";
  const { start, end, label } = parsePeriod(opts.startDate);
  const tasks: ExportTask[] = [];

  function task(
    id: string,
    priority: ExportPriority,
    contentLevel: string,
    dataView: string,
    filter: string,
    preset: string,
    notes = "",
  ): ExportTask {
    return {
      id,
      priority,
      platform: "Facebook",
      page,
      contentLevel,
      dataView,
      filter,
      preset,
      dateRange: { start, end },
      period: opts.period,
      filename: makeFilename(page, contentLevel, dataView, filter, preset, label),
      uiPath: UI_PATH,
      website: WEBSITE,
      notes,
    };
  }

  // P0 — Verified (tìm thấy và tải được từ Content Export)
  // P01: Posts / Lifetime / Created / Performance — ranking toàn bộ bài viết
  tasks.push(task("P01", "P0", "Posts", "Lifetime", "Created date", "Performance", "Ranking toàn bộ bài viết — top content. Bao gồm tất cả loại bài."));
  // P02: Posts / Lifetime / Created / Published — master list bài viết
  tasks.push(task("P02", "P0", "Posts", "Lifetime", "Created date", "Published", "Master list bài viết — danh sách đầy đủ."));
  // V01: Video / Lifetime / Created / Performance — top video ranking
  tasks.push(task("V01", "P0", "Video", "Lifetime", "Created date", "Performance", "Top video/reels ranking — milestone."));

  // P1 — Operational video (Activity filter chỉ gồm video)
  if (opts.includeVideo) {
    tasks.push(task("V02", "P1", "Video", "Daily", "Activity", "Performance", "Operational video daily trend. ⚠️ Chỉ gồm video posts — KHÔNG gồm photo/text/link."));
  }

  // P2 — Optional / Specialized
  if (opts.includeVideo) {
    tasks.push(task("V03", "P2", "Video", "Lifetime", "Created date", "Retention", "Chỉ tải nếu preset Tỷ lệ giữ chân có sẵn"));
  }

  // G02: Page / Daily / Audience — verified nhưng audience-only (KHÔNG phải performance)
  if (opts.includeAudience) {
    tasks.push(task("G02", "P2", "Page", "Daily", "—", "Audience", "Audience demographics only. KHÔNG có reach/impressions. KHÔNG thay thế performance."));
  }

  // G01: Page / Daily / Performance — ❌ CHƯA VERIFIED trong Content Export
  // Page preset "Hiệu quả" bị disable. Chỉ thêm nếu user explicitly opt-in.
  if (opts.includeUnverifiedPagePerformance) {
    tasks.push(task("G01", "P2", "Page", "Daily", "—", "Performance", "⚠️ UNVERIFIED — chưa tìm thấy trong Content Export. Page preset Performance bị disable. Thêm manually nếu tìm thấy ở Insights → Results/Overview."));
  }

  return tasks;
}

/**
 * Format checklist ra Markdown.
 */
export function formatChecklistMarkdown(tasks: ExportTask[], label: string): string {
  const lines: string[] = [];
  lines.push(`# Export Checklist — Chim Cút — ${label}`);
  lines.push("");
  lines.push(`> Website: ${WEBSITE}`);
  lines.push(`> UI Path: ${UI_PATH}`);
  lines.push(`> Date range: ${tasks[0]?.dateRange.start ?? "?"} → ${tasks[0]?.dateRange.end ?? "?"}`);
  lines.push("");

  const groups: Record<string, ExportTask[]> = {};
  for (const t of tasks) {
    if (!groups[t.priority]) groups[t.priority] = [];
    groups[t.priority].push(t);
  }

  let step = 1;
  for (const [priority, groupTasks] of Object.entries(groups)) {
    lines.push(`## ${priority} — ${priority === "P0" ? "Bắt buộc" : priority === "P1" ? "Mở rộng" : "Tùy chọn"}`);
    lines.push("");
    for (const t of groupTasks) {
      lines.push(`### ${step}. ${t.id}: ${t.contentLevel} / ${t.preset}`);
      lines.push("");
      lines.push(`- [ ] **Platform**: ${t.platform}`);
      lines.push(`- [ ] **Page**: ${t.page}`);
      lines.push(`- [ ] **Website**: ${t.website}`);
      lines.push(`- [ ] **UI path**: ${t.uiPath}`);
      lines.push(`- [ ] **Date range**: ${t.dateRange.start} → ${t.dateRange.end}`);
      lines.push(`- [ ] **Content level**: ${t.contentLevel}`);
      lines.push(`- [ ] **Data view**: ${t.dataView}`);
      lines.push(`- [ ] **Filter**: ${t.filter}`);
      lines.push(`- [ ] **Preset**: ${t.preset}`);
      lines.push(`- [ ] **Filename**: \`${t.filename}\``);
      lines.push(`- [ ] **Import priority**: ${t.priority}`);
      if (t.notes) lines.push(`- [ ] **Notes**: ${t.notes}`);
      lines.push("");
      step++;
    }
  }

  lines.push("---");
  lines.push("");
  lines.push("Sau khi tải xong tất cả file, copy vào thư mục `imports/incoming/` hoặc upload qua `/imports`.");
  lines.push("");

  return lines.join("\n");
}
