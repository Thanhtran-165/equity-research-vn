/**
 * Export Reminder Plan — date math + weekly/monthly checklist generator.
 */

export interface DateRange {
  start: string; // YYYY-MM-DD
  end: string;
}

export interface ReminderItem {
  code: string;
  title: string;
  priority: "P0" | "P1" | "P0-Monthly" | "P1-Monthly" | "P1-Backfill";
  required: boolean;
  platform: string;
  pageName: string;
  dateRange: DateRange;
  preset: string;
  dataView: string;
  contentLevel: string;
  filterMode: string;
  expectedFilename: string;
  purpose: string;
  note?: string;
  status: string;
}

export interface ReminderRun {
  type: "weekly" | "monthly";
  periodStart: string;
  periodEnd: string;
  dueAt: string;
  items: ReminderItem[];
}

const DAY = 24 * 60 * 60 * 1000;

function toISODate(d: Date): string {
  // Use local date components, NOT UTC (toISOString shifts timezone)
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/**
 * Lấy tuần trước (Monday → Sunday) tính từ ngày hiện tại.
 */
export function getPreviousFullWeek(now: Date = new Date()): DateRange {
  const day = now.getDay(); // 0=Sun, 1=Mon
  // Days since last Monday
  const daysSinceMonday = day === 0 ? 6 : day - 1;
  const thisMonday = new Date(now);
  thisMonday.setHours(0, 0, 0, 0);
  thisMonday.setDate(now.getDate() - daysSinceMonday);

  const lastMonday = new Date(thisMonday);
  lastMonday.setDate(thisMonday.getDate() - 7);
  const lastSunday = new Date(thisMonday);
  lastSunday.setDate(thisMonday.getDate() - 1);

  return { start: toISODate(lastMonday), end: toISODate(lastSunday) };
}

/**
 * Lấy Chủ Nhật cuối cùng trước ngày hiện tại.
 */
export function getLastSunday(now: Date = new Date()): string {
  const day = now.getDay();
  const daysSinceSunday = day === 0 ? 0 : day;
  const lastSunday = new Date(now);
  lastSunday.setHours(0, 0, 0, 0);
  lastSunday.setDate(now.getDate() - daysSinceSunday);
  if (day === 0) {
    // If today is Sunday, use previous Sunday
    lastSunday.setDate(lastSunday.getDate() - 7);
  }
  return toISODate(lastSunday);
}

/**
 * YTD range: Jan 1 → last Sunday.
 */
export function getYtdRange(now: Date = new Date()): DateRange {
  const year = now.getFullYear();
  return { start: `${year}-01-01`, end: getLastSunday(now) };
}

/**
 * Kiểm tra xem có phải Thứ Hai đầu tiên của tháng không.
 */
export function isFirstMondayOfMonth(now: Date = new Date()): boolean {
  if (now.getDay() !== 1) return false; // Not Monday
  return now.getDate() <= 7; // First week
}

/**
 * Filename generator.
 */
function buildFilename(
  code: string,
  dateRange: DateRange,
  isYtd: boolean = false,
): string {
  const slug = "chimcut_fb";
  if (isYtd) {
    const endParts = dateRange.end.split("-");
    return `${slug}_${code.toLowerCase()}_ytd_${dateRange.end}.csv`;
  }
  return `${slug}_${code.toLowerCase()}_${dateRange.start}_${dateRange.end}.csv`;
}

/**
 * Meta instruction steps for each item.
 */
export function buildMetaInstructionSteps(item: ReminderItem): string[] {
  return [
    "Mở Meta Business Suite → Thông tin chi tiết → Nội dung → Xuất dữ liệu",
    `Tab: ${item.platform}`,
    `Page: ${item.pageName}`,
    `Khoảng ngày: ${item.dateRange.start} → ${item.dateRange.end}`,
    `Số liệu đặt sẵn: ${item.preset}`,
    `Chế độ xem dữ liệu: ${item.dataView}`,
    `Cấp độ nội dung: ${item.contentLevel}`,
    `Bộ lọc: ${item.filterMode}`,
    "Bấm: Tạo",
    "Khi hoàn tất, bấm icon tải xuống",
    `Đổi tên file thành: ${item.expectedFilename}`,
  ];
}

/**
 * Generate weekly checklist (W01-W04).
 */
export function generateWeeklyReminderRun(now: Date = new Date()): ReminderRun {
  const week = getPreviousFullWeek(now);

  const items: ReminderItem[] = [
    {
      code: "W01",
      title: "Video Daily Activity Performance",
      priority: "P0",
      required: true,
      platform: "Facebook",
      pageName: "Chim Cút",
      dateRange: week,
      preset: "Hiệu quả",
      dataView: "Hằng ngày",
      contentLevel: "Video",
      filterMode: "Hoạt động",
      expectedFilename: `chimcut_fb_video_daily_activity_performance_${week.start}_${week.end}.csv`,
      purpose: "Cập nhật video/reels theo từng ngày. Dùng cho video dashboard, daily trend, spike detection.",
      note: "Nếu file này fail, thử tải lại. Nếu vẫn fail, chia nhỏ theo từng ngày hoặc 3 ngày.",
      status: "pending",
    },
    {
      code: "W02",
      title: "Posts Lifetime Created Performance",
      priority: "P0",
      required: true,
      platform: "Facebook",
      pageName: "Chim Cút",
      dateRange: week,
      preset: "Hiệu quả",
      dataView: "Trọn đời",
      contentLevel: "Bài viết",
      filterMode: "Ngày tạo",
      expectedFilename: `chimcut_fb_posts_lifetime_created_performance_${week.start}_${week.end}.csv`,
      purpose: "Cập nhật bài viết mới trong tuần. Dùng cho top posts, reach, ER, CTR.",
      note: "File này là dữ liệu lifetime của các bài được tạo trong tuần. Không phải dữ liệu từng ngày.",
      status: "pending",
    },
    {
      code: "W03",
      title: "Posts Lifetime Created Published",
      priority: "P0",
      required: true,
      platform: "Facebook",
      pageName: "Chim Cút",
      dateRange: week,
      preset: "Đã đăng",
      dataView: "Trọn đời",
      contentLevel: "Bài viết",
      filterMode: "Ngày tạo",
      expectedFilename: `chimcut_fb_posts_lifetime_created_published_${week.start}_${week.end}.csv`,
      purpose: "Cập nhật danh sách bài viết/master list. Giúp match bài viết, permalink, thời gian đăng.",
      status: "pending",
    },
    {
      code: "W04",
      title: "Video Lifetime Created Performance",
      priority: "P1",
      required: false,
      platform: "Facebook",
      pageName: "Chim Cút",
      dateRange: week,
      preset: "Hiệu quả",
      dataView: "Trọn đời",
      contentLevel: "Video",
      filterMode: "Ngày tạo",
      expectedFilename: `chimcut_fb_video_lifetime_created_performance_${week.start}_${week.end}.csv`,
      purpose: "Cập nhật lifetime ranking cho video/reels mới.",
      status: "pending",
    },
  ];

  const dueAt = new Date(now);
  dueAt.setHours(9, 0, 0, 0);
  // Due is today if Monday, else already overdue
  if (now.getDay() !== 1) {
    // Find this week's Monday
    const day = now.getDay();
    const daysSinceMonday = day === 0 ? 6 : day - 1;
    dueAt.setDate(now.getDate() - daysSinceMonday);
    dueAt.setHours(9, 0, 0, 0);
  }

  return {
    type: "weekly",
    periodStart: week.start,
    periodEnd: week.end,
    dueAt: dueAt.toISOString(),
    items,
  };
}

/**
 * Generate monthly refresh checklist (M01-M04) — only on first Monday of month.
 */
export function generateMonthlyRefreshItems(now: Date = new Date()): ReminderItem[] {
  if (!isFirstMondayOfMonth(now)) return [];

  const ytd = getYtdRange(now);
  const lastMonth = new Date(now);
  lastMonth.setMonth(lastMonth.getMonth() - 1, 0);
  const lastMonthStart = toISODate(new Date(lastMonth.getFullYear(), lastMonth.getMonth(), 1));
  const lastMonthEnd = toISODate(new Date(lastMonth.getFullYear(), lastMonth.getMonth() + 1, 0));

  return [
    {
      code: "M01",
      title: "Posts Lifetime Created Performance YTD",
      priority: "P0-Monthly",
      required: true,
      platform: "Facebook",
      pageName: "Chim Cút",
      dateRange: ytd,
      preset: "Hiệu quả",
      dataView: "Trọn đời",
      contentLevel: "Bài viết",
      filterMode: "Ngày tạo",
      expectedFilename: `chimcut_fb_posts_lifetime_created_performance_ytd_${ytd.end}.csv`,
      purpose: "Làm mới YTD lifetime metrics cho tất cả bài viết.",
      status: "pending",
    },
    {
      code: "M02",
      title: "Posts Lifetime Created Published YTD",
      priority: "P0-Monthly",
      required: true,
      platform: "Facebook",
      pageName: "Chim Cút",
      dateRange: ytd,
      preset: "Đã đăng",
      dataView: "Trọn đời",
      contentLevel: "Bài viết",
      filterMode: "Ngày tạo",
      expectedFilename: `chimcut_fb_posts_lifetime_created_published_ytd_${ytd.end}.csv`,
      purpose: "Master list YTD.",
      status: "pending",
    },
    {
      code: "M03",
      title: "Video Lifetime Created Performance YTD",
      priority: "P1-Monthly",
      required: false,
      platform: "Facebook",
      pageName: "Chim Cút",
      dateRange: ytd,
      preset: "Hiệu quả",
      dataView: "Trọn đời",
      contentLevel: "Video",
      filterMode: "Ngày tạo",
      expectedFilename: `chimcut_fb_video_lifetime_created_performance_ytd_${ytd.end}.csv`,
      purpose: "Video lifetime YTD refresh.",
      status: "pending",
    },
    {
      code: "M04",
      title: "Video Daily Activity Performance (previous month backfill)",
      priority: "P1-Backfill",
      required: false,
      platform: "Facebook",
      pageName: "Chim Cút",
      dateRange: { start: lastMonthStart, end: lastMonthEnd },
      preset: "Hiệu quả",
      dataView: "Hằng ngày",
      contentLevel: "Video",
      filterMode: "Hoạt động",
      expectedFilename: `chimcut_fb_video_daily_activity_performance_${lastMonthStart.slice(0, 7)}.csv`,
      purpose: "Backfill V02 cho tháng trước nếu thiếu.",
      status: "pending",
    },
  ];
}

/**
 * Generate ICS calendar file content — 2 VEVENTs (weekly + monthly).
 * Uses TZID=Asia/Ho_Chi_Minh for correct timezone.
 */
export function generateICSContent(): string {
  const now = new Date();
  const today = now.toISOString().replace(/[-:]/g, "").split(".")[0] + "Z";

  // Find next Monday for weekly DTSTART
  const nextMonday = new Date(now);
  const dayOfWeek = now.getDay();
  const daysUntilMonday = dayOfWeek === 1 ? (now.getHours() >= 9 ? 7 : 0) : (8 - dayOfWeek) % 7;
  nextMonday.setDate(now.getDate() + daysUntilMonday);
  nextMonday.setHours(9, 0, 0, 0);
  const weeklyDtStart = formatICSDate(nextMonday);

  // Find first Monday of next month for monthly DTSTART
  const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
  let firstMonNext = new Date(nextMonth);
  for (let d = 1; d <= 7; d++) {
    firstMonNext = new Date(nextMonth.getFullYear(), nextMonth.getMonth(), d, 9, 15, 0, 0);
    if (firstMonNext.getDay() === 1) break;
  }
  const monthlyDtStart = formatICSDate(firstMonNext);

  return [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Chim Cut Dashboard//Data Reminder//VI",
    "CALSCALE:GREGORIAN",
    "BEGIN:VTIMEZONE",
    "TZID:Asia/Ho_Chi_Minh",
    "BEGIN:STANDARD",
    "DTSTART:19700101T000000",
    "TZOFFSETFROM:+0700",
    "TZOFFSETTO:+0700",
    "END:STANDARD",
    "END:VTIMEZONE",
    // Weekly event
    "BEGIN:VEVENT",
    "UID:chimcut-weekly-reminder@dashboard",
    `DTSTAMP:${today}`,
    `DTSTART;TZID=Asia/Ho_Chi_Minh:${weeklyDtStart}`,
    "RRULE:FREQ=WEEKLY;BYDAY=MO",
    "SUMMARY:Cập nhật dữ liệu Meta cho Chim Cút (Hằng tuần)",
    "DESCRIPTION:Tải W01 (Video Daily Activity)\\nW02 (Posts Lifetime Performance)\\nW03 (Posts Lifetime Published)\\nW04 (Video Lifetime Performance nếu có video mới)",
    "BEGIN:VALARM",
    "TRIGGER:-PT0S",
    "ACTION:DISPLAY",
    "DESCRIPTION:Cập nhật dữ liệu Meta cho Chim Cút",
    "END:VALARM",
    "END:VEVENT",
    // Monthly event
    "BEGIN:VEVENT",
    "UID:chimcut-monthly-reminder@dashboard",
    `DTSTAMP:${today}`,
    `DTSTART;TZID=Asia/Ho_Chi_Minh:${monthlyDtStart}`,
    "RRULE:FREQ=MONTHLY;BYDAY=MO;BYSETPOS=1",
    "SUMMARY:Cập nhật dữ liệu Meta hằng tháng cho Chim Cút",
    "DESCRIPTION:Monthly refresh: M01 (Posts Lifetime Performance YTD)\\nM02 (Posts Lifetime Published YTD)\\nM03 (Video Lifetime YTD)\\nM04 (Video Daily backfill nếu thiếu)\\n\\nMonthly refresh sẽ tiếp tục hiện trong app nếu chưa completed.",
    "BEGIN:VALARM",
    "TRIGGER:-PT0S",
    "ACTION:DISPLAY",
    "DESCRIPTION:Cập nhật dữ liệu Meta hằng tháng",
    "END:VALARM",
    "END:VEVENT",
    "END:VCALENDAR",
  ].join("\r\n");
}

function formatICSDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const h = String(d.getHours()).padStart(2, "0");
  const min = String(d.getMinutes()).padStart(2, "0");
  return `${y}${m}${day}T${h}${min}00`;
}

/**
 * Check if a reminder is overdue.
 */
export function isOverdue(dueAt: string, now: Date = new Date()): boolean {
  return new Date(dueAt).getTime() < now.getTime();
}

/**
 * Check if run is completed (all required items Applied OK).
 */
export function isRunCompleted(items: ReminderItem[]): boolean {
  return items.filter((i) => i.required).every((i) => i.status === "applied_ok");
}
