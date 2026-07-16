/**
 * Monthly report generator — combines page + video + spikes + data quality.
 */
import {
  computePageSummary,
  topPostsByReach,
  topPostsByER,
  topPostsByCTR,
  topPostsByComments,
  topPostsByShares,
  detectPostSpikes,
  type PostReportRow,
  type PageSummary,
  type TopPost,
  type PostSpike,
} from "./pageReport";
import {
  computeVideoMonthlySummary,
  topVideosByViews,
  topVideosByWatchTime,
  detectVideoSpikes,
  type VideoMonthlySummary,
  type TopVideoInPeriod,
  type VideoSpike,
} from "./videoReport";

export interface MonthlyReportData {
  month: string;
  page: PageSummary;
  topReachPosts: TopPost[];
  topERPosts: TopPost[];
  topCTRPosts: TopPost[];
  topCommentPosts: TopPost[];
  topSharePosts: TopPost[];
  video: VideoMonthlySummary;
  topVideosViews: TopVideoInPeriod[];
  topVideosWatch: TopVideoInPeriod[];
  postSpikes: PostSpike[];
  videoSpikes: VideoSpike[];
  dataQuality: string[];
}

export function buildMonthlyReport(
  month: string,
  posts: PostReportRow[],
  videoDaily: any[],
): MonthlyReportData {
  return {
    month,
    page: computePageSummary(posts),
    topReachPosts: topPostsByReach(posts, 20),
    topERPosts: topPostsByER(posts, 500, 20),
    topCTRPosts: topPostsByCTR(posts, 500, 20),
    topCommentPosts: topPostsByComments(posts, 20),
    topSharePosts: topPostsByShares(posts, 20),
    video: computeVideoMonthlySummary(videoDaily),
    topVideosViews: topVideosByViews(videoDaily, 10),
    topVideosWatch: topVideosByWatchTime(videoDaily, 10),
    postSpikes: detectPostSpikes(posts),
    videoSpikes: detectVideoSpikes(videoDaily),
    dataQuality: [
      "Source: Meta Business Suite CSV (manual export)",
      "Summed reach is NOT unique Page reach — it's Σ reach across posts/videos/days",
      "Video assets not linked to Posts (different Meta ID systems)",
      "Paid impressions ignored — only organic metrics used",
      "ER excludes clicks (social engagement rate). CTR = clicks/reach separately.",
    ],
  };
}

export function formatMonthlyReportMarkdown(r: MonthlyReportData): string {
  const lines: string[] = [];
  const num = (v: number | null | undefined, d = 0) => v == null ? "—" : v.toLocaleString("vi-VN", { maximumFractionDigits: d });
  const pct = (v: number | null | undefined) => v == null ? "—" : `${(v * 100).toFixed(2)}%`;

  lines.push(`# Báo cáo tháng ${r.month} — Chim Cút`);
  lines.push("");
  lines.push(`> Nguồn: Meta Business Suite CSV · Tạo lúc ${new Date().toISOString()}`);
  lines.push("");

  // Summary
  lines.push("## 1. Tổng quan");
  lines.push("");
  lines.push("| Metric | Value |");
  lines.push("|---|---|");
  lines.push(`| Posts | ${r.page.totalPosts} |`);
  lines.push(`| Total reach | ${num(r.page.totalReach)} |`);
  lines.push(`| Reactions | ${num(r.page.totalReactions)} |`);
  lines.push(`| Comments | ${num(r.page.totalComments)} |`);
  lines.push(`| Shares | ${num(r.page.totalShares)} |`);
  lines.push(`| Clicks | ${num(r.page.totalClicks)} |`);
  lines.push(`| Avg ER (social) | ${pct(r.page.avgER)} |`);
  lines.push(`| Avg CTR | ${pct(r.page.avgCTR)} |`);
  lines.push("");

  // Top posts
  const formatTopPost = (label: string, posts: TopPost[], sortMetric: string) => {
    lines.push(`### ${label}`);
    lines.push("");
    lines.push(`| # | Message | Reach | ${sortMetric} | Reactions | Comments | Shares |`);
    lines.push(`|---|---|---|---|---|---|---|`);
    posts.slice(0, 10).forEach((p, i) => {
      const msg = (p.message ?? "(no text)").slice(0, 40).replace(/\|/g, "\\|");
      let sortVal = "";
      if (sortMetric === "ER") sortVal = pct(p.er);
      else if (sortMetric === "CTR") sortVal = pct(p.ctr);
      else if (sortMetric === "Reach") sortVal = num(p.reach);
      else if (sortMetric === "Comments") sortVal = num(p.comments);
      else if (sortMetric === "Shares") sortVal = num(p.shares);
      lines.push(`| ${i + 1} | ${msg} | ${num(p.reach)} | ${sortVal} | ${num(p.reactions)} | ${num(p.comments)} | ${num(p.shares)} |`);
    });
    lines.push("");
  };

  lines.push("## 2. Top Posts");
  lines.push("");
  formatTopPost("Top 10 by Reach", r.topReachPosts, "Reach");
  formatTopPost("Top 10 by ER (min reach 500)", r.topERPosts, "ER");
  formatTopPost("Top 10 by CTR (min reach 500)", r.topCTRPosts, "CTR");
  formatTopPost("Top 10 by Comments", r.topCommentPosts, "Comments");
  formatTopPost("Top 10 by Shares", r.topSharePosts, "Shares");

  // Video
  lines.push("## 3. Video");
  lines.push("");
  lines.push("| Metric | Value |");
  lines.push("|---|---|");
  lines.push(`| Active videos | ${r.video.activeVideoCount} |`);
  lines.push(`| Total 3s views | ${num(r.video.totalViews3s)} |`);
  lines.push(`| Summed reach | ${num(r.video.summedReach)} |`);
  lines.push(`| Watch time (hrs) | ${num(r.video.watchTimeHours, 1)} |`);
  lines.push(`| Avg sec/view | ${r.video.avgWatchPerView != null ? num(r.video.avgWatchPerView, 1) + "s" : "—"} |`);
  lines.push("");

  if (r.topVideosViews.length > 0) {
    lines.push("### Top 10 Video by Views");
    lines.push("");
    lines.push("| # | Title | Views | Reach | Watch (hrs) |");
    lines.push("|---|---|---|---|---|");
    r.topVideosViews.forEach((v, i) => {
      lines.push(`| ${i + 1} | ${(v.title ?? v.externalVideoId).slice(0, 30)} | ${num(v.videoViews3s)} | ${num(v.reach)} | ${num(v.watchTimeHours, 1)} |`);
    });
    lines.push("");
  }

  // Spikes
  lines.push("## 4. Spike Detection");
  lines.push("");
  if (r.postSpikes.length > 0) {
    lines.push("**Post spikes:**");
    for (const s of r.postSpikes) {
      lines.push(`- ${s.date}: ${s.reason}`);
    }
  } else {
    lines.push("No post spikes detected.");
  }
  lines.push("");
  if (r.videoSpikes.length > 0) {
    lines.push("**Video spikes:**");
    for (const s of r.videoSpikes) {
      lines.push(`- ${s.date}: ${s.reason}`);
    }
  } else {
    lines.push("No video spikes detected.");
  }
  lines.push("");

  // Data quality
  lines.push("## 5. Data Quality");
  lines.push("");
  for (const q of r.dataQuality) {
    lines.push(`- ${q}`);
  }

  return lines.join("\n");
}
