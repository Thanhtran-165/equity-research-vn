import { describe, it, expect } from "vitest";
import { parseBenchmarkCsv } from "../benchmark/importBenchmarkCsv";

describe("parseBenchmarkCsv", () => {
  it("parses basic English headers", () => {
    const csv = `postUrl,postedAt,reactions,comments,shares
https://fb.com/p1,2026-07-10,100,20,5
https://fb.com/p2,2026-07-09,50,10,`;
    const result = parseBenchmarkCsv(csv);
    expect(result.totalRows).toBe(2);
    expect(result.parsed[0].reactions).toBe(100);
    expect(result.parsed[0].comparableEngagement).toBe(120);
  });

  it("parses Vietnamese column aliases", () => {
    const csv = `đường dẫn bài,ngày đăng,lượt phản ứng,bình luận,chia sẻ
https://fb.com/p1,2026-07-10,100,20,5`;
    const result = parseBenchmarkCsv(csv);
    expect(result.totalRows).toBe(1);
    expect(result.parsed[0].reactions).toBe(100);
    expect(result.parsed[0].comments).toBe(20);
    expect(result.parsed[0].shares).toBe(5);
  });

  it("treats blank shares as null, not zero", () => {
    const csv = `postUrl,reactions,comments,shares
https://fb.com/p1,100,20,`;
    const result = parseBenchmarkCsv(csv);
    expect(result.parsed[0].shares).toBeNull();
    expect(result.parsed[0].sharesObserved).toBe(false);
    // comparable engagement still computed from reactions + comments
    expect(result.parsed[0].comparableEngagement).toBe(120);
  });

  it("treats '0' as observed zero", () => {
    const csv = `postUrl,reactions,comments,shares
https://fb.com/p1,0,0,0`;
    const result = parseBenchmarkCsv(csv);
    expect(result.parsed[0].reactions).toBe(0);
    expect(result.parsed[0].reactionsObserved).toBe(true);
    expect(result.parsed[0].comparableEngagement).toBe(0);
  });

  it("skips rows without postUrl", () => {
    const csv = `postUrl,reactions,comments
,100,20
https://fb.com/p1,50,10`;
    const result = parseBenchmarkCsv(csv);
    expect(result.totalRows).toBe(1);
    expect(result.skipped.length).toBe(1);
  });

  it("returns error when postUrl column missing", () => {
    const csv = `reactions,comments
100,20`;
    const result = parseBenchmarkCsv(csv);
    expect(result.totalRows).toBe(0);
    expect(result.warnings.length).toBeGreaterThan(0);
  });

  it("handles quoted CSV fields", () => {
    const csv = `postUrl,textSnippet,reactions
"https://fb.com/p1","Hello, world",100`;
    const result = parseBenchmarkCsv(csv);
    expect(result.totalRows).toBe(1);
    expect(result.parsed[0].textSnippet).toBe("Hello, world");
    expect(result.parsed[0].reactions).toBe(100);
  });

  it("skips empty rows", () => {
    const csv = `postUrl,reactions,comments
https://fb.com/p1,100,20
,,
https://fb.com/p2,50,10`;
    const result = parseBenchmarkCsv(csv);
    expect(result.totalRows).toBe(2);
    expect(result.skipped.length).toBe(1);
  });

  it("handles videoViews Vietnamese alias", () => {
    const csv = `postUrl,reactions,comments,lượt xem video
https://fb.com/p1,100,20,5000`;
    const result = parseBenchmarkCsv(csv);
    expect(result.parsed[0].publicVideoViews).toBe(5000);
    expect(result.parsed[0].publicVideoViewsObserved).toBe(true);
  });

  it("parses pageUrl and pageName for page resolution", () => {
    const csv = `pageUrl,pageName,postUrl,reactions,comments
https://facebook.com/testpage,Test Page,https://fb.com/p1,100,20`;
    const result = parseBenchmarkCsv(csv);
    expect(result.parsed[0].pageUrl).toBe("https://facebook.com/testpage");
    expect(result.parsed[0].pageName).toBe("Test Page");
  });
});
