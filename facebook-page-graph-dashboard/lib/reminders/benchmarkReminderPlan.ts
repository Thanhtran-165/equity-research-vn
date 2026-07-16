/**
 * Benchmark Weekly Collection Reminder — date math, ICS, checklist text.
 *
 * Schedule: Wednesday 18:00 Asia/Ho_Chi_Minh, weekly.
 * Separate from Meta MBS data reminders (W01–W04, M01–M04).
 *
 * Persistence rules:
 * - If Wednesday 18:00 reached and no run for current week → create run.
 * - If run not completed/skipped → continue showing on subsequent days.
 * - If past Sunday 18:00 and not completed → overdue.
 * - If new week starts but previous run incomplete → keep old in "incomplete" section.
 */

export interface WeekBounds {
  weekStart: Date; // Monday 00:00 local
  weekEnd: Date;   // Sunday 23:59:59.999 local
}

/**
 * Get ISO week bounds (Monday 00:00 → Sunday 23:59) for the given date's week.
 */
export function getCurrentWeekBounds(now: Date): WeekBounds {
  const day = now.getDay(); // 0=Sun, 1=Mon
  const diff = day === 0 ? -6 : 1 - day;
  const weekStart = new Date(now);
  weekStart.setDate(now.getDate() + diff);
  weekStart.setHours(0, 0, 0, 0);
  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekStart.getDate() + 6);
  weekEnd.setHours(23, 59, 59, 999);
  return { weekStart, weekEnd };
}

/**
 * Get previous ISO week bounds.
 */
export function getPreviousWeekBounds(now: Date): WeekBounds {
  const current = getCurrentWeekBounds(now);
  const prevStart = new Date(current.weekStart);
  prevStart.setDate(current.weekStart.getDate() - 7);
  const prevEnd = new Date(current.weekEnd);
  prevEnd.setDate(current.weekEnd.getDate() - 7);
  return { weekStart: prevStart, weekEnd: prevEnd };
}

/**
 * Due at = Wednesday 18:00 local time of the current week.
 */
export function getWednesdayDueAt(weekStart: Date): Date {
  const due = new Date(weekStart);
  due.setDate(weekStart.getDate() + 2); // Monday + 2 = Wednesday
  due.setHours(18, 0, 0, 0);
  return due;
}

/**
 * Overdue at = Sunday 18:00 local time (end of collection window).
 */
export function getSundayOverdueAt(weekEnd: Date): Date {
  const overdue = new Date(weekEnd);
  overdue.setHours(18, 0, 0, 0);
  return overdue;
}

/**
 * Check if a run is overdue (past Sunday 18:00 and not completed/skipped).
 */
export function isBenchmarkOverdue(
  weekEnd: Date,
  status: string,
  now: Date = new Date(),
): boolean {
  if (status === "completed" || status === "skipped") return false;
  return now > getSundayOverdueAt(weekEnd);
}

/**
 * Check if a run should be created (Wednesday 18:00 or later in the current week).
 */
export function shouldCreateBenchmarkRun(now: Date = new Date()): boolean {
  const { weekStart } = getCurrentWeekBounds(now);
  const dueAt = getWednesdayDueAt(weekStart);
  return now >= dueAt;
}

// ─── Checklist text ─────────────────────────────────────

export const OVERALL_CHECKLIST: string[] = [
  "Mở trang /public-benchmark/collection",
  "Tải hoặc mở benchmark-weekly-template.csv",
  "Thu thập khoảng 4 bài cho mỗi Core Peer",
  "Cập nhật audience snapshot nếu thấy follower count",
  "Để trống shares nếu không nhìn thấy",
  "Chỉ ghi 0 nếu số công khai thực sự là 0",
  "Không nhập reach",
  "Không nhập impressions",
  "Không nhập CTR",
  "Không nhập watch time",
  "Chạy CSV dry-run",
  "Kiểm tra 9 quality gates",
  "Apply dữ liệu khi dry-run PASS",
  "Xác nhận leaderboard đã cập nhật",
];

export const PER_PEER_CHECKLIST: string[] = [
  "Đã mở đúng canonical Page URL",
  "Đã chọn 4 bài gần đây hoặc bài thuộc kỳ cần thu thập",
  "Đã ghi postUrl",
  "Đã ghi postedAt",
  "Đã chọn contentType",
  "Đã chọn topicTag",
  "Đã ghi reactions nếu nhìn thấy",
  "Đã ghi comments nếu nhìn thấy",
  "Đã ghi shares nếu nhìn thấy",
  "Đã ghi publicVideoViews nếu nhìn thấy",
  "Đã ghi capturedAt",
  "Đã cập nhật follower snapshot nếu có",
  "Hoàn thành Page này",
];

export const KEY_RULES: string[] = [
  "Ô trống = không nhìn thấy.",
  "Số 0 = đã nhìn thấy và giá trị thực bằng 0.",
  "Shares bị ẩn không được ghi thành 0.",
  "Likes không phải followers.",
  "Không dùng dữ liệu nội bộ của Chim Cút để tạo lợi thế so với peers.",
];

export interface PeerChecklistEntry {
  pageName: string;
  canonicalUrl: string;
  scaleBand: string | null;
  targetPosts: number;
  collectedPosts: number;
}

/**
 * Build the full benchmark reminder checklist text for display/copy.
 */
export function buildBenchmarkChecklist(
  peers: PeerChecklistEntry[],
  summary: {
    externalCorePeers: number;
    targetTotal: number;
    collectedTotal: number;
    pagesCompleted: number;
    pagesNotStarted: number;
  },
): string {
  const lines: string[] = [
    "Cập nhật Benchmark công khai tuần này",
    "",
    `External Core Peers: ${summary.externalCorePeers}`,
    `Target: 4 bài mỗi Page`,
    `Tổng mục tiêu: khoảng ${summary.targetTotal} bài`,
    `Đã nhập: ${summary.collectedTotal}`,
    `Page hoàn tất: ${summary.pagesCompleted}`,
    `Page chưa bắt đầu: ${summary.pagesNotStarted}`,
    "",
    "Checklist tổng:",
    ...OVERALL_CHECKLIST.map((item) => `[ ] ${item}`),
    "",
    "Quy tắc nổi bật:",
    ...KEY_RULES.map((r) => `- ${r}`),
    "",
    "Checklist theo từng Core Peer:",
    "",
  ];

  for (const peer of peers) {
    lines.push(`── ${peer.pageName} ──`);
    lines.push(`URL: ${peer.canonicalUrl}`);
    lines.push(`Scale: ${peer.scaleBand ?? "—"}`);
    lines.push(`Target: ${peer.targetPosts} | Collected: ${peer.collectedPosts}`);
    lines.push(...PER_PEER_CHECKLIST.map((item) => `[ ] ${item}`));
    lines.push("");
  }

  return lines.join("\n");
}

// ─── ICS ─────────────────────────────────────────────────

/**
 * Format a Date to ICS local date-time string (YYYYMMDDTHHMMSS).
 */
function formatICSDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const h = String(d.getHours()).padStart(2, "0");
  const min = String(d.getMinutes()).padStart(2, "0");
  return `${y}${m}${day}T${h}${min}00`;
}

/**
 * Find next Wednesday 18:00 from now.
 */
export function getNextWednesday18(now: Date = new Date()): Date {
  const day = now.getDay(); // 0=Sun, 3=Wed
  let daysUntilWed = (3 - day + 7) % 7;
  // If today is Wednesday but past 18:00, go to next week
  if (daysUntilWed === 0 && now.getHours() >= 18) {
    daysUntilWed = 7;
  }
  const next = new Date(now);
  next.setDate(now.getDate() + daysUntilWed);
  next.setHours(18, 0, 0, 0);
  return next;
}

/**
 * Generate the benchmark VEVENT block for ICS.
 * Returns lines to be inserted into a VCALENDAR.
 */
export function generateBenchmarkICSVEvent(now: Date = new Date()): string[] {
  const today = now.toISOString().replace(/[-:]/g, "").split(".")[0] + "Z";
  const nextWed = getNextWednesday18(now);
  const dtStart = formatICSDate(nextWed);

  const description = [
    "Cập nhật Benchmark công khai cho Chim Cút",
    "8 Core Peers × 4 bài/Page = khoảng 32 dòng",
    "",
    "Quy tắc:",
    "• Ô trống = không nhìn thấy (KHÔNG phải zero)",
    "• Shares bị ẩn phải để trống",
    "• Chỉ ghi 0 nếu số công khai thực sự bằng 0",
    "• Không nhập reach/impressions/CTR/watch time",
    "• Likes không phải followers",
    "",
    "Mở /public-benchmark/collection để bắt đầu",
  ].join("\\n");

  return [
    "BEGIN:VEVENT",
    "UID:chimcut-benchmark-collection@dashboard",
    `DTSTAMP:${today}`,
    `DTSTART;TZID=Asia/Ho_Chi_Minh:${dtStart}`,
    "RRULE:FREQ=WEEKLY;BYDAY=WE",
    "SUMMARY:Cập nhật Benchmark công khai cho Chim Cút",
    `DESCRIPTION:${description}`,
    "BEGIN:VALARM",
    "TRIGGER:-PT0S",
    "ACTION:DISPLAY",
    "DESCRIPTION:Cập nhật Benchmark công khai",
    "END:VALARM",
    "END:VEVENT",
  ];
}

/**
 * Generate the complete ICS content with all 3 events (weekly Meta + monthly Meta + benchmark).
 * This wraps the existing generateICSContent and adds the benchmark VEVENT.
 */
export function generateFullICSContent(
  existingICSContent: string,
  benchmarkVEvent: string[],
): string {
  // Insert benchmark VEVENT before END:VCALENDAR
  const lines = existingICSContent.split("\r\n");
  const endIdx = lines.indexOf("END:VCALENDAR");
  if (endIdx === -1) return existingICSContent;
  lines.splice(endIdx, 0, ...benchmarkVEvent);
  return lines.join("\r\n");
}
