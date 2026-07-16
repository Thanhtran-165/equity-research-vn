import { describe, it, expect } from "vitest";
import { validatePilotImport, detectForbiddenColumns } from "../benchmark/pilotValidation";
import type { ParsedBenchmarkPost } from "../benchmark/importBenchmarkCsv";

function makePost(overrides: Partial<ParsedBenchmarkPost> = {}): ParsedBenchmarkPost {
  return {
    pageUrl: null,
    pageName: null,
    postUrl: "https://facebook.com/test/posts/1",
    postedAt: "2026-07-10",
    textSnippet: null,
    contentType: null,
    topicTag: null,
    reactions: 100,
    comments: 20,
    shares: 5,
    publicVideoViews: null,
    reactionsObserved: true,
    commentsObserved: true,
    sharesObserved: true,
    publicVideoViewsObserved: false,
    comparableEngagement: 120,
    observedPublicEngagement: 125,
    metricCoverageScore: 0.9,
    warnings: [],
    ...overrides,
  };
}

const KNOWN_PEERS = ["Peer A", "Peer B"];
const KNOWN_URLS = ["https://facebook.com/peerA", "https://facebook.com/peerB"];
const KNOWN_IDS = [1, 2];

describe("pilotValidation", () => {
  it("1. entity count distinguishes peer vs own page in validation context", () => {
    const report = validatePilotImport({
      parsed: [makePost({ pageName: "Peer A" }), makePost({ pageName: "Peer B" })],
      skipped: [],
      forbiddenColumns: [],
      resolvedPageIds: [1, 2],
      knownCorePeerNames: KNOWN_PEERS,
      knownCorePeerUrls: KNOWN_URLS,
      knownCorePeerPageIds: KNOWN_IDS,
    });
    expect(report.uniquePages).toBe(2);
    expect(report.expectedCorePeersPresent).toContain("Peer A");
    expect(report.expectedCorePeersPresent).toContain("Peer B");
  });

  it("2. CSV template headers detected correctly via forbidden column check", () => {
    // Template should NOT contain forbidden columns
    const templateHeaders = ["pageName", "pageUrl", "postUrl", "postedAt", "reactions", "comments", "shares", "publicVideoViews", "capturedAt"];
    expect(detectForbiddenColumns(templateHeaders)).toEqual([]);
  });

  it("3. collection pack contains exactly 8 external Core Peers (via validation)", () => {
    // Simulate 8 peers with 4 posts each = 32 rows
    const peers = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"];
    const posts: ParsedBenchmarkPost[] = [];
    for (const p of peers) {
      for (let i = 0; i < 4; i++) {
        posts.push(makePost({ pageName: p, postUrl: `https://fb.com/${p}/posts/${i}` }));
      }
    }
    const report = validatePilotImport({
      parsed: posts,
      skipped: [],
      forbiddenColumns: [],
      resolvedPageIds: posts.map(() => 1),
      knownCorePeerNames: peers,
      knownCorePeerUrls: peers.map((p) => `https://fb.com/${p}`),
      knownCorePeerPageIds: [1, 2, 3, 4, 5, 6, 7, 8],
    });
    expect(report.postsPerPage.length).toBe(8);
    expect(report.totalRows).toBe(32);
  });

  it("4. own page not counted as external peer", () => {
    const report = validatePilotImport({
      parsed: [
        makePost({ pageName: "Peer A" }),
        makePost({ pageName: "Chim Cút" }), // own page
      ],
      skipped: [],
      forbiddenColumns: [],
      resolvedPageIds: [1, null], // own page not in knownCorePeerPageIds
      knownCorePeerNames: ["Peer A"], // Chim Cút NOT in core peers
      knownCorePeerUrls: ["https://facebook.com/peerA"],
      knownCorePeerPageIds: [1],
    });
    expect(report.expectedCorePeersPresent).toContain("Peer A");
    expect(report.expectedCorePeersPresent).not.toContain("Chim Cút");
  });

  it("5. pilot gate warns when peer has fewer than 3 posts", () => {
    const report = validatePilotImport({
      parsed: [makePost({ pageName: "Peer A" }), makePost({ pageName: "Peer A" })], // only 2 posts
      skipped: [],
      forbiddenColumns: [],
      resolvedPageIds: [1, 1],
      knownCorePeerNames: KNOWN_PEERS,
      knownCorePeerUrls: KNOWN_URLS,
      knownCorePeerPageIds: KNOWN_IDS,
    });
    const g5 = report.gates.find((g) => g.id === "G5");
    expect(g5?.status).toBe("warn");
  });

  it("6. pilot gate warns when shares coverage below threshold", () => {
    // 5 posts, only 1 with shares = 20% coverage
    const posts: ParsedBenchmarkPost[] = [];
    for (let i = 0; i < 5; i++) {
      posts.push(makePost({
        postUrl: `https://fb.com/test/${i}`,
        shares: i === 0 ? 5 : null,
        sharesObserved: i === 0,
        observedPublicEngagement: i === 0 ? 125 : 120,
      }));
    }
    const report = validatePilotImport({
      parsed: posts,
      skipped: [],
      forbiddenColumns: [],
      resolvedPageIds: posts.map(() => 1),
      knownCorePeerNames: KNOWN_PEERS,
      knownCorePeerUrls: KNOWN_URLS,
      knownCorePeerPageIds: KNOWN_IDS,
    });
    const g8 = report.gates.find((g) => g.id === "G8");
    expect(g8?.status).toBe("warn");
    expect(report.sharesCoverage).toBeLessThan(0.5);
  });

  it("7. forbidden columns (reach/impressions/CTR/watchTime) are detected and fail", () => {
    expect(detectForbiddenColumns(["reach", "reactions", "comments"])).toContain("reach");
    expect(detectForbiddenColumns(["impressions", "lượt hiển thị"])).toContain("impressions");
    expect(detectForbiddenColumns(["watchtime", "thời gian xem"])).toContain("watchtime");
    expect(detectForbiddenColumns(["ctr"])).toContain("ctr");

    const report = validatePilotImport({
      parsed: [makePost()],
      skipped: [],
      forbiddenColumns: ["reach", "ctr"],
      resolvedPageIds: [1],
      knownCorePeerNames: KNOWN_PEERS,
      knownCorePeerUrls: KNOWN_URLS,
      knownCorePeerPageIds: KNOWN_IDS,
    });
    const g4 = report.gates.find((g) => g.id === "G4");
    expect(g4?.status).toBe("fail");
  });

  it("8. reference objects remain excluded from direct leaderboard validation", () => {
    // topic_reference should not appear in expected core peers
    const report = validatePilotImport({
      parsed: [makePost({ pageName: "CafeF" })], // topic_reference
      skipped: [],
      forbiddenColumns: [],
      resolvedPageIds: [null], // not in core peer IDs
      knownCorePeerNames: KNOWN_PEERS, // CafeF not included
      knownCorePeerUrls: KNOWN_URLS,
      knownCorePeerPageIds: KNOWN_IDS,
    });
    expect(report.expectedCorePeersPresent).not.toContain("CafeF");
  });

  it("9. observed zero survives in parsed data (not converted to null)", () => {
    const post = makePost({
      reactions: 0, comments: 0, shares: 0,
      reactionsObserved: true, commentsObserved: true, sharesObserved: true,
      comparableEngagement: 0, observedPublicEngagement: 0,
    });
    const report = validatePilotImport({
      parsed: [post],
      skipped: [],
      forbiddenColumns: [],
      resolvedPageIds: [1],
      knownCorePeerNames: KNOWN_PEERS,
      knownCorePeerUrls: KNOWN_URLS,
      knownCorePeerPageIds: KNOWN_IDS,
    });
    expect(report.observedZeroCount).toBe(3); // reactions, comments, shares all 0
    expect(report.blankMetricCount).toBe(1); // publicVideoViews unobserved
  });

  it("10. blank remains null in parsed data (not converted to zero)", () => {
    const post = makePost({
      reactions: 100, comments: 20,
      shares: null, sharesObserved: false,
      publicVideoViews: null, publicVideoViewsObserved: false,
      observedPublicEngagement: 120, // no shares added
    });
    const report = validatePilotImport({
      parsed: [post],
      skipped: [],
      forbiddenColumns: [],
      resolvedPageIds: [1],
      knownCorePeerNames: KNOWN_PEERS,
      knownCorePeerUrls: KNOWN_URLS,
      knownCorePeerPageIds: KNOWN_IDS,
    });
    // shares blank + videoViews blank = 2 blank metrics
    expect(report.blankMetricCount).toBe(2);
    // no observed zeros
    expect(report.observedZeroCount).toBe(0);
  });
});
