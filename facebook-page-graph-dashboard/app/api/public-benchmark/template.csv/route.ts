/**
 * GET /api/public-benchmark/template.csv
 * Download the benchmark weekly collection CSV template.
 *
 * Headers follow the import CSV spec. Blank = not observed. "0" = observed zero.
 */
export const dynamic = "force-static";

export async function GET() {
  const headers = [
    "pageName",
    "pageUrl",
    "objectType",
    "audienceCount",
    "audienceCountType",
    "postUrl",
    "postedAt",
    "textSnippet",
    "contentType",
    "topicTag",
    "reactions",
    "comments",
    "shares",
    "publicVideoViews",
    "capturedAt",
    "notes",
  ];

  // Example row (clearly marked) + instructions in comment lines
  const lines: string[] = [
    "# Benchmark Weekly Collection Template",
    "# QUY TẮC:",
    "#   - Ô trống = chưa quan sát được (null) — KHÔNG phải zero",
    "#   - Chỉ điền 0 nếu số công khai thực sự bằng 0",
    "#   - KHÔNG nhập reach, impressions, CTR, watch time — không dùng cho benchmark",
    "#   - likes KHÔNG phải followers — audienceCount = follower/member count thật",
    "#   - capturedAt bắt buộc (YYYY-MM-DD)",
    "#   - postUrl bắt buộc (permalink của bài viết)",
    "# Ví dụ (xóa dòng này trước khi import):",
    `# Chim Cút,https://facebook.com/chimcutvnindex,facebook_page,44880,followers,https://facebook.com/chimcutvnindex/posts/EXAMPLE,2026-07-10,"Snippet text",reel,macro,150,20,5,,2026-07-10,`,
    headers.join(","),
  ];

  const csv = lines.join("\n") + "\n";

  return new Response(csv, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": 'attachment; filename="benchmark-weekly-template.csv"',
    },
  });
}
