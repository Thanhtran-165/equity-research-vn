import { describe, it, expect } from "vitest";
import { runQualityChecks } from "../benchmark/dataQuality";

describe("runQualityChecks", () => {
  it("returns FAIL when no pages seeded", () => {
    const report = runQualityChecks({
      totalPages: 0,
      corePeerCount: 0,
      ownPagePresent: false,
      totalPosts: 0,
      postsWithReactions: 0,
      postsWithComments: 0,
      postsWithShares: 0,
      postsWithComparableEngagement: 0,
      postsWithNeitherReactionsNorComments: 0,
      pagesWithPosts: 0,
      pagesWithoutPosts: 0,
      zeroMetricCount: 0,
      medianCoverageScore: null,
      oldestPostDays: null,
      newestPostDays: null,
      duplicatePostUrls: 0,
      nonPageInCorePeers: 0,
      watchlistWithPosts: 0,
      postsMissingPostedAt: 0,
    });
    expect(report.overall).toBe("fail");
    expect(report.checks.find((c) => c.id === "Q01")?.status).toBe("fail");
    expect(report.checks.find((c) => c.id === "Q02")?.status).toBe("fail");
  });

  it("returns PASS when all checks pass", () => {
    const report = runQualityChecks({
      totalPages: 20,
      corePeerCount: 9,
      ownPagePresent: true,
      totalPosts: 100,
      postsWithReactions: 95,
      postsWithComments: 90,
      postsWithShares: 60,
      postsWithComparableEngagement: 90,
      postsWithNeitherReactionsNorComments: 0,
      pagesWithPosts: 9,
      pagesWithoutPosts: 11,
      zeroMetricCount: 0,
      medianCoverageScore: 0.85,
      oldestPostDays: 30,
      newestPostDays: 2,
      duplicatePostUrls: 0,
      nonPageInCorePeers: 0,
      watchlistWithPosts: 0,
      postsMissingPostedAt: 5,
    });
    expect(report.overall).toBe("pass");
  });

  it("returns WARN for core peer count below 8", () => {
    const report = runQualityChecks({
      totalPages: 20,
      corePeerCount: 5,
      ownPagePresent: true,
      totalPosts: 100,
      postsWithReactions: 90,
      postsWithComments: 90,
      postsWithShares: 60,
      postsWithComparableEngagement: 90,
      postsWithNeitherReactionsNorComments: 0,
      pagesWithPosts: 9,
      pagesWithoutPosts: 11,
      zeroMetricCount: 0,
      medianCoverageScore: 0.8,
      oldestPostDays: 30,
      newestPostDays: 2,
      duplicatePostUrls: 0,
      nonPageInCorePeers: 0,
      watchlistWithPosts: 0,
      postsMissingPostedAt: 5,
    });
    const q03 = report.checks.find((c) => c.id === "Q03");
    expect(q03?.status).toBe("warn");
  });

  it("returns FAIL when non-facebook_page in core peers", () => {
    const report = runQualityChecks({
      totalPages: 20,
      corePeerCount: 9,
      ownPagePresent: true,
      totalPosts: 100,
      postsWithReactions: 90,
      postsWithComments: 90,
      postsWithShares: 60,
      postsWithComparableEngagement: 90,
      postsWithNeitherReactionsNorComments: 0,
      pagesWithPosts: 9,
      pagesWithoutPosts: 11,
      zeroMetricCount: 0,
      medianCoverageScore: 0.8,
      oldestPostDays: 30,
      newestPostDays: 2,
      duplicatePostUrls: 0,
      nonPageInCorePeers: 2,
      watchlistWithPosts: 0,
      postsMissingPostedAt: 5,
    });
    expect(report.checks.find((c) => c.id === "Q09")?.status).toBe("fail");
    expect(report.overall).toBe("fail");
  });

  it("returns WARN when posts have neither reactions nor comments", () => {
    const report = runQualityChecks({
      totalPages: 20,
      corePeerCount: 9,
      ownPagePresent: true,
      totalPosts: 100,
      postsWithReactions: 90,
      postsWithComments: 90,
      postsWithShares: 60,
      postsWithComparableEngagement: 90,
      postsWithNeitherReactionsNorComments: 5,
      pagesWithPosts: 9,
      pagesWithoutPosts: 11,
      zeroMetricCount: 0,
      medianCoverageScore: 0.8,
      oldestPostDays: 30,
      newestPostDays: 2,
      duplicatePostUrls: 0,
      nonPageInCorePeers: 0,
      watchlistWithPosts: 0,
      postsMissingPostedAt: 5,
    });
    const q07 = report.checks.find((c) => c.id === "Q07");
    expect(q07?.status).toBe("warn");
  });
});
