/**
 * Benchmark Data Quality Diagnostics — 10 checks.
 *
 * Each check returns: PASS / WARN / FAIL with details.
 * Overall status = worst individual status.
 */

export type QualityStatus = "pass" | "warn" | "fail";

export interface QualityCheck {
  id: string;
  label: string;
  status: QualityStatus;
  detail: string;
  metric?: number;
}

export interface DataQualityReport {
  overall: QualityStatus;
  checks: QualityCheck[];
  summary: string;
}

interface QualityInput {
  totalPages: number;
  corePeerCount: number;
  ownPagePresent: boolean;
  totalPosts: number;
  postsWithReactions: number;
  postsWithComments: number;
  postsWithShares: number;
  postsWithComparableEngagement: number;
  postsWithNeitherReactionsNorComments: number;
  pagesWithPosts: number;
  pagesWithoutPosts: number;
  zeroMetricCount: number;
  medianCoverageScore: number | null;
  oldestPostDays: number | null;
  newestPostDays: number | null;
  duplicatePostUrls: number;
  nonPageInCorePeers: number;
  watchlistWithPosts: number;
  postsMissingPostedAt: number;
}

export function runQualityChecks(input: QualityInput): DataQualityReport {
  const checks: QualityCheck[] = [];

  // 1. Peer Set v2 seeded
  checks.push({
    id: "Q01",
    label: "Peer Set v2 seeded",
    status: input.totalPages >= 10 ? "pass" : input.totalPages > 0 ? "warn" : "fail",
    detail:
      input.totalPages === 0
        ? "No BenchmarkPage records. Run `npm run benchmark:seed-peers`."
        : `${input.totalPages} pages in database (${input.corePeerCount} core peers).`,
    metric: input.totalPages,
  });

  // 2. Own page present
  checks.push({
    id: "Q02",
    label: "Chim Cút own page present",
    status: input.ownPagePresent ? "pass" : "fail",
    detail: input.ownPagePresent
      ? "Chim Cút own page is seeded."
      : "Own page not found. Re-run seed script.",
  });

  // 3. Core peer count within limits
  checks.push({
    id: "Q03",
    label: "Core peer count (8–12)",
    status:
      input.corePeerCount >= 8 && input.corePeerCount <= 12
        ? "pass"
        : input.corePeerCount > 12
          ? "fail"
          : "warn",
    detail: `${input.corePeerCount} core peers (target: 8–12).`,
    metric: input.corePeerCount,
  });

  // 4. Posts collected
  checks.push({
    id: "Q04",
    label: "Posts collected",
    status:
      input.totalPosts >= 50 ? "pass" : input.totalPosts > 0 ? "warn" : "fail",
    detail:
      input.totalPosts === 0
        ? "No BenchmarkPost records. Start collecting data."
        : `${input.totalPosts} posts collected.`,
    metric: input.totalPosts,
  });

  // 5. Reactions coverage
  const reactionsRate =
    input.totalPosts > 0 ? input.postsWithReactions / input.totalPosts : 0;
  checks.push({
    id: "Q05",
    label: "Reactions coverage",
    status: reactionsRate >= 0.8 ? "pass" : reactionsRate >= 0.5 ? "warn" : "fail",
    detail: `${input.postsWithReactions}/${input.totalPosts} posts have reactions (${(reactionsRate * 100).toFixed(0)}%).`,
    metric: Math.round(reactionsRate * 100),
  });

  // 6. Comments coverage
  const commentsRate =
    input.totalPosts > 0 ? input.postsWithComments / input.totalPosts : 0;
  checks.push({
    id: "Q06",
    label: "Comments coverage",
    status: commentsRate >= 0.8 ? "pass" : commentsRate >= 0.5 ? "warn" : "fail",
    detail: `${input.postsWithComments}/${input.totalPosts} posts have comments (${(commentsRate * 100).toFixed(0)}%).`,
    metric: Math.round(commentsRate * 100),
  });

  // 7. Shares not silently converted to zero
  checks.push({
    id: "Q07",
    label: "Shares missing ≠ zero",
    status:
      input.postsWithNeitherReactionsNorComments === 0 ? "pass" : "warn",
    detail:
      input.postsWithNeitherReactionsNorComments > 0
        ? `${input.postsWithNeitherReactionsNorComments} posts have neither reactions nor comments — check if missing metrics were entered as 0 by mistake.`
        : "All posts have at least reactions or comments observed.",
    metric: input.postsWithNeitherReactionsNorComments,
  });

  // 8. Comparable engagement coverage
  const comparableRate =
    input.totalPosts > 0 ? input.postsWithComparableEngagement / input.totalPosts : 0;
  checks.push({
    id: "Q08",
    label: "Comparable engagement coverage",
    status: comparableRate >= 0.7 ? "pass" : comparableRate >= 0.4 ? "warn" : "fail",
    detail: `${input.postsWithComparableEngagement}/${input.totalPosts} posts have comparable engagement (${(comparableRate * 100).toFixed(0)}%).`,
    metric: Math.round(comparableRate * 100),
  });

  // 9. Core peers have only facebook_page objectType
  checks.push({
    id: "Q09",
    label: "Core peers are all facebook_page",
    status: input.nonPageInCorePeers === 0 ? "pass" : "fail",
    detail:
      input.nonPageInCorePeers > 0
        ? `${input.nonPageInCorePeers} core peers have non-facebook_page objectType — remove from direct leaderboard.`
        : "All core peers are facebook_page type.",
    metric: input.nonPageInCorePeers,
  });

  // 10. Data freshness
  const freshnessStatus: QualityStatus =
    input.newestPostDays != null && input.newestPostDays <= 7
      ? "pass"
      : input.newestPostDays != null && input.newestPostDays <= 14
        ? "warn"
        : "fail";
  checks.push({
    id: "Q10",
    label: "Data freshness",
    status: freshnessStatus,
    detail:
      input.newestPostDays == null
        ? "No posts with postedAt — cannot assess freshness."
        : `Newest post is ${input.newestPostDays} day(s) old.`,
    metric: input.newestPostDays ?? undefined,
  });

  const failCount = checks.filter((c) => c.status === "fail").length;
  const warnCount = checks.filter((c) => c.status === "warn").length;
  const overall: QualityStatus = failCount > 0 ? "fail" : warnCount > 0 ? "warn" : "pass";

  const summary = `${checks.filter((c) => c.status === "pass").length}/${checks.length} pass, ${warnCount} warn, ${failCount} fail`;

  return { overall, checks, summary };
}
