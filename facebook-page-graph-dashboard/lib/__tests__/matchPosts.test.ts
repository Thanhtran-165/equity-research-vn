import { describe, it, expect } from "vitest";
import { matchRow, matchRows, type CandidatePost } from "../imports/matchPosts";
import type { NormalizedRow } from "../imports/normalizeRows";

const SAMPLE_POSTS: CandidatePost[] = [
  {
    fbPostId: "100063657162530_111",
    permalinkUrl: "https://www.facebook.com/chimcutvnindex/posts/111",
    message: "CPI tháng 7 tăng nhẹ",
    createdTime: "2026-07-01T08:00:00Z",
  },
  {
    fbPostId: "100063657162530_222",
    permalinkUrl: "https://www.facebook.com/chimcutvnindex/posts/222",
    message: "VN-Index tăng mạnh",
    createdTime: "2026-07-02T10:00:00Z",
  },
  {
    fbPostId: "100063657162530_333",
    permalinkUrl: "https://www.facebook.com/chimcutvnindex/posts/333",
    message: "Vàng SJC chạm đỉnh",
    createdTime: "2026-07-03T15:00:00Z",
  },
];

function makeRow(overrides: Partial<NormalizedRow> = {}): NormalizedRow {
  return {
    postId: null,
    permalinkUrl: null,
    externalContentId: null,
    createdTime: null,
    messageSnippet: null,
    reach: 1000,
    impressions: 5000,
    engagedUsers: null,
    clicks: null,
    reactions: 50,
    comments: 10,
    shares: 5,
    videoViews: null,
    watchTime: null,
    rawRowJson: "{}",
    ...overrides,
  };
}

describe("matchRow", () => {
  it("matches by post_id exact (confidence 1.0)", () => {
    const row = makeRow({ postId: "100063657162530_111" });
    const r = matchRow(row, SAMPLE_POSTS);
    expect(r.status).toBe("matched");
    expect(r.matchedPostId).toBe("100063657162530_111");
    expect(r.confidence).toBe(1.0);
  });

  it("matches by permalink exact (confidence 0.95)", () => {
    const row = makeRow({ permalinkUrl: "https://www.facebook.com/chimcutvnindex/posts/222" });
    const r = matchRow(row, SAMPLE_POSTS);
    expect(r.status).toBe("matched");
    expect(r.matchedPostId).toBe("100063657162530_222");
    expect(r.confidence).toBeCloseTo(0.95, 2);
  });

  it("matches by permalink canonical (strips query params)", () => {
    const row = makeRow({ permalinkUrl: "https://www.facebook.com/chimcutvnindex/posts/333?ref=foo" });
    const r = matchRow(row, SAMPLE_POSTS);
    expect(r.status).toBe("matched");
    expect(r.matchedPostId).toBe("100063657162530_333");
  });

  it("matches by date + exact snippet (confidence 0.80)", () => {
    const row = makeRow({
      createdTime: "2026-07-01T09:30:00Z", // trong 6h
      messageSnippet: "CPI tháng 7 tăng nhẹ", // exact
    });
    const r = matchRow(row, SAMPLE_POSTS);
    expect(r.status).toBe("matched");
    expect(r.confidence).toBeGreaterThanOrEqual(0.8);
  });

  it("matches by date + fuzzy snippet (confidence 0.60-0.75)", () => {
    // Snippet có typo nhẹ để similarity trong khoảng 0.7-0.95
    const row = makeRow({
      createdTime: "2026-07-02T11:00:00Z",
      messageSnippet: "VN-Inedx tăng mạnh", // typo "Inedx" → sim ~0.85
    });
    const r = matchRow(row, SAMPLE_POSTS);
    expect(r.status).toBe("matched");
    expect(r.confidence).toBeGreaterThanOrEqual(0.6);
  });

  it("returns unmatched when no identifiers", () => {
    const row = makeRow();
    const r = matchRow(row, SAMPLE_POSTS);
    expect(r.status).toBe("unmatched");
    expect(r.matchedPostId).toBeNull();
  });

  it("returns unmatched when date out of 6h window", () => {
    const row = makeRow({
      createdTime: "2026-08-01T09:00:00Z", // 1 tháng sau
      messageSnippet: "CPI tháng 7 tăng nhẹ",
    });
    const r = matchRow(row, SAMPLE_POSTS);
    expect(r.status).toBe("unmatched");
  });

  it("returns unmatched for empty posts array", () => {
    const r = matchRow(makeRow(), []);
    expect(r.status).toBe("unmatched");
  });

  it("handles ambiguous: 2 posts cùng snippet trong 6h", () => {
    const posts: CandidatePost[] = [
      {
        fbPostId: "p1",
        permalinkUrl: "https://facebook.com/p1",
        message: "Bài viết trùng nhau",
        createdTime: "2026-07-04T10:00:00Z",
      },
      {
        fbPostId: "p2",
        permalinkUrl: "https://facebook.com/p2",
        message: "Bài viết trùng nhau",
        createdTime: "2026-07-04T11:00:00Z",
      },
    ];
    const row = makeRow({
      createdTime: "2026-07-04T10:30:00Z",
      messageSnippet: "Bài viết trùng nhau",
    });
    const r = matchRow(row, posts);
    expect(r.status).toBe("ambiguous");
  });

  it("returns unmatched when snippet quá khác (sim < 0.7)", () => {
    const row = makeRow({
      createdTime: "2026-07-01T09:00:00Z",
      messageSnippet: "Bài viết hoàn toàn khác nội dung không liên quan",
    });
    const r = matchRow(row, SAMPLE_POSTS);
    expect(r.status).toBe("unmatched");
  });
});

describe("matchRows", () => {
  it("matches all rows in batch", () => {
    const rows = [
      makeRow({ postId: "100063657162530_111" }),
      makeRow({ postId: "100063657162530_222" }),
      makeRow({ postId: "999" }), // unmatched
    ];
    const results = matchRows(rows, SAMPLE_POSTS);
    expect(results).toHaveLength(3);
    expect(results[0].status).toBe("matched");
    expect(results[1].status).toBe("matched");
    expect(results[2].status).toBe("unmatched");
  });
});
