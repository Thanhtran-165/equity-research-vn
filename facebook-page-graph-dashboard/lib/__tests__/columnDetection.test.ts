import { describe, it, expect } from "vitest";
import { detectColumns, FIELD_ALIASES } from "../imports/columnDetection";

describe("detectColumns", () => {
  it("detects English column names", () => {
    const headers = ["Post ID", "Permalink", "Post message", "Reach", "Impressions", "Comments", "Shares"];
    const r = detectColumns(headers);
    expect(r.mapping.postId).toBe(0);
    expect(r.mapping.permalinkUrl).toBe(1);
    expect(r.mapping.messageSnippet).toBe(2);
    expect(r.mapping.reach).toBe(3);
    expect(r.mapping.impressions).toBe(4);
    expect(r.mapping.comments).toBe(5);
    expect(r.mapping.shares).toBe(6);
  });

  it("detects Vietnamese column names", () => {
    const headers = ["ID bài viết", "Liên kết", "Nội dung", "Lượt tiếp cận", "Lượt hiển thị", "Bình luận", "Chia sẻ"];
    const r = detectColumns(headers);
    expect(r.mapping.postId).toBe(0);
    expect(r.mapping.permalinkUrl).toBe(1);
    expect(r.mapping.messageSnippet).toBe(2);
    expect(r.mapping.reach).toBe(3);
    expect(r.mapping.impressions).toBe(4);
    expect(r.mapping.comments).toBe(5);
    expect(r.mapping.shares).toBe(6);
  });

  it("detects case-insensitively + with extra chars in header", () => {
    // Use longer aliases that pass the >= 8 char substring filter
    const headers = ["Content ID", "Accounts reached"];
    const r = detectColumns(headers);
    expect(r.mapping.postId).toBe(0);
    expect(r.mapping.reach).toBe(1);
  });

  it("warns when missing required post_id AND permalink", () => {
    const headers = ["Reach", "Impressions"];
    const r = detectColumns(headers);
    expect(r.mapping.postId).toBeNull();
    expect(r.mapping.permalinkUrl).toBeNull();
    expect(r.warnings.some((w) => w.includes("post_id hoặc permalink_url"))).toBe(true);
  });

  it("warns when missing reach column", () => {
    const headers = ["Post ID", "Permalink"];
    const r = detectColumns(headers);
    expect(r.mapping.reach).toBeNull();
    expect(r.warnings.some((w) => w.includes("THIẾU cột reach"))).toBe(true);
  });

  it("returns mapping = null for unrecognized fields", () => {
    const headers = ["Unknown column"];
    const r = detectColumns(headers);
    expect(r.mapping.reach).toBeNull();
    expect(r.mapping.postId).toBeNull();
  });

  it("handles ambiguous matches (2 cột cùng khớp 'reach')", () => {
    const headers = ["Reach", "Accounts reached"];
    const r = detectColumns(headers);
    expect(r.ambiguousFields).toContain("reach");
    expect(r.mapping.reach).toBe(0); // pick first
  });

  it("FIELD_ALIASES has all standard fields", () => {
    const requiredFields = [
      "postId", "permalinkUrl", "createdTime", "messageSnippet",
      "reach", "impressions", "clicks", "engagedUsers",
      "reactions", "comments", "shares", "videoViews", "watchTime",
    ];
    for (const f of requiredFields) {
      expect(FIELD_ALIASES).toHaveProperty(f);
      expect(FIELD_ALIASES[f as keyof typeof FIELD_ALIASES].length).toBeGreaterThan(0);
    }
  });
});
