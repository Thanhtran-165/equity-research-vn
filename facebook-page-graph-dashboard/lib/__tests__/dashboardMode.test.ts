import { describe, it, expect } from "vitest";

/**
 * Logic auto-detect default dashboard mode — tách ra pure function để test.
 * Spec user phê duyệt:
 * - "insights": ĐA SỐ (>50%) bài có trueReach
 * - "public": KHÔNG có bài nào có trueReach, chỉ có public/video
 * - "mixed": có cả trueReach (it nhất 1) LẪN public/video
 */
export type DashboardViewMode = "insights" | "public" | "mixed";

export function detectDefaultViewMode(args: {
  totalPosts: number;
  trueReachCount: number;
  publicOrVideoCount: number;
}): DashboardViewMode {
  const { totalPosts, trueReachCount, publicOrVideoCount } = args;
  if (totalPosts === 0) return "public";
  // Đa số (>50%) bài có trueReach → insights
  if (trueReachCount >= totalPosts / 2) return "insights";
  // Không có bài nào có trueReach → public
  if (trueReachCount === 0) return "public";
  // Có cả trueReach (thiểu số) lẫn public/video → mixed
  if (trueReachCount > 0 && publicOrVideoCount > 0) return "mixed";
  // Fallback: chỉ có trueReach (không có public)
  return "insights";
}

describe("detectDefaultViewMode", () => {
  it("returns 'insights' when MAJORITY (>50%) posts have trueReach", () => {
    // 3/5 = 60% > 50%
    expect(
      detectDefaultViewMode({ totalPosts: 5, trueReachCount: 3, publicOrVideoCount: 2 }),
    ).toBe("insights");
  });

  it("returns 'insights' when ALL posts have trueReach", () => {
    expect(
      detectDefaultViewMode({ totalPosts: 10, trueReachCount: 10, publicOrVideoCount: 0 }),
    ).toBe("insights");
  });

  it("returns 'public' when NO post has trueReach (only public/video)", () => {
    expect(
      detectDefaultViewMode({ totalPosts: 10, trueReachCount: 0, publicOrVideoCount: 10 }),
    ).toBe("public");
  });

  it("returns 'mixed' when both trueReach (minority) and public/video exist", () => {
    // 1/10 = 10% trueReach, 9/10 public → mixed (không default insights chỉ vì 1 bài)
    expect(
      detectDefaultViewMode({ totalPosts: 10, trueReachCount: 1, publicOrVideoCount: 9 }),
    ).toBe("mixed");
  });

  it("does NOT default to insights only because 1 post has insights", () => {
    // Test cho case user nêu: nếu chỉ 1/25 bài có trueReach → mixed, không phải insights
    expect(
      detectDefaultViewMode({ totalPosts: 25, trueReachCount: 1, publicOrVideoCount: 24 }),
    ).toBe("mixed");
  });

  it("returns 'public' for empty dataset (no posts)", () => {
    expect(
      detectDefaultViewMode({ totalPosts: 0, trueReachCount: 0, publicOrVideoCount: 0 }),
    ).toBe("public");
  });

  it("returns 'insights' at exactly 50% threshold (boundary)", () => {
    // 5/10 = 50% → >= totalPosts/2 → insights
    expect(
      detectDefaultViewMode({ totalPosts: 10, trueReachCount: 5, publicOrVideoCount: 5 }),
    ).toBe("insights");
  });

  it("returns 'mixed' just below 50% threshold", () => {
    // 4/10 = 40% < 50% → mixed (vì vẫn có 4 bài trueReach + 6 bài public)
    expect(
      detectDefaultViewMode({ totalPosts: 10, trueReachCount: 4, publicOrVideoCount: 6 }),
    ).toBe("mixed");
  });

  it("handles real-world case: 20/25 posts have trueReach → insights", () => {
    // Page Chim Cút thực tế trước đây: 20/25 reach thật
    expect(
      detectDefaultViewMode({ totalPosts: 25, trueReachCount: 20, publicOrVideoCount: 5 }),
    ).toBe("insights");
  });

  it("handles real-world case: 0/25 posts have trueReach → public", () => {
    // Page Chim Cút thực tế hiện tại: 0/25 reach thật, 25 video/public
    expect(
      detectDefaultViewMode({ totalPosts: 25, trueReachCount: 0, publicOrVideoCount: 25 }),
    ).toBe("public");
  });
});
