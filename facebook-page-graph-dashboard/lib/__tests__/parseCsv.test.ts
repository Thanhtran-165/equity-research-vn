import { describe, it, expect } from "vitest";
import { parseCsv } from "../imports/parseCsv";
import { parseNumber, parseDate, canonicalizeUrl, normalizeMessageSnippet } from "../imports/normalizeRows";

describe("parseCsv", () => {
  it("strips UTF-8 BOM", () => {
    const text = "\uFEFFname,reach\npost1,100\n";
    const r = parseCsv(text);
    expect(r.headers).toEqual(["name", "reach"]);
    expect(r.rows).toEqual([["post1", "100"]]);
  });

  it("parses comma delimiter", () => {
    const r = parseCsv("a,b,c\n1,2,3\n");
    expect(r.headers).toEqual(["a", "b", "c"]);
    expect(r.rows).toEqual([["1", "2", "3"]]);
    expect(r.delimiter).toBe(",");
  });

  it("detects semicolon delimiter", () => {
    const r = parseCsv("a;b;c\n1;2;3\n");
    expect(r.headers).toEqual(["a", "b", "c"]);
    expect(r.delimiter).toBe(";");
  });

  it("handles quoted fields with commas inside", () => {
    const r = parseCsv('a,b\n"hello, world",2\n');
    expect(r.rows).toEqual([["hello, world", "2"]]);
  });

  it("handles escaped quotes inside quoted field", () => {
    const r = parseCsv('a\n"she said ""hi"""\n');
    expect(r.rows).toEqual([['she said "hi"']]);
  });

  it("handles Vietnamese text", () => {
    const r = parseCsv("tiêu đề,lượt tiếp cận\nBài viết số 1,1234\n");
    expect(r.headers).toEqual(["tiêu đề", "lượt tiếp cận"]);
    expect(r.rows[0][0]).toBe("Bài viết số 1");
  });

  it("handles newline inside quoted field", () => {
    const r = parseCsv('a,b\n"line1\nline2",2\n');
    expect(r.rows).toEqual([["line1\nline2", "2"]]);
  });

  it("detects header row when first line is title", () => {
    // Meta có thể có dòng title trước header
    const r = parseCsv("Meta Business Suite Report\nPost ID,Reach,Impressions\n123,1000,5000\n");
    expect(r.headers).toEqual(["Post ID", "Reach", "Impressions"]);
    expect(r.headerRowIndex).toBe(1);
    expect(r.rows).toEqual([["123", "1000", "5000"]]);
  });

  it("returns warnings for empty file", () => {
    const r = parseCsv("");
    expect(r.warnings).toContain("empty-file");
  });
});

describe("parseNumber", () => {
  it("parses plain integer", () => {
    expect(parseNumber("1234")).toBe(1234);
  });

  it("parses with comma thousand separator (US)", () => {
    expect(parseNumber("1,234")).toBe(1234);
  });

  it("parses with dot thousand separator (EU/VI) when integer part <= 3 digits", () => {
    expect(parseNumber("1.234")).toBe(1234);
    expect(parseNumber("12.345")).toBe(12345);
  });

  it("parses decimal when integer part >= 4 digits (NOT thousand separator)", () => {
    expect(parseNumber("1234.567")).toBeCloseTo(1234.567, 3);
    expect(parseNumber("2246375.241")).toBeCloseTo(2246375.241, 3);
  });

  it("parses decimal with comma (EU)", () => {
    expect(parseNumber("1,5")).toBe(1.5);
  });

  it("parses US decimal 1,234.56", () => {
    expect(parseNumber("1,234.56")).toBeCloseTo(1234.56, 2);
  });

  it("parses EU decimal 1.234,56", () => {
    expect(parseNumber("1.234,56")).toBeCloseTo(1234.56, 2);
  });

  it("parses short decimal 1.5", () => {
    expect(parseNumber("1.5")).toBe(1.5);
  });

  it("parses short decimal 1.24", () => {
    expect(parseNumber("1.24")).toBe(1.24);
  });

  it("does NOT treat large decimal as thousand separator", () => {
    // CRITICAL: 2246375.241 should NOT become 2246375241
    expect(parseNumber("2246375.241")).toBeCloseTo(2246375.241, 3);
    expect(parseNumber("5384428.650")).toBeCloseTo(5384428.650, 3);
    expect(parseNumber("221382.625")).toBeCloseTo(221382.625, 3);
  });

  it("returns null for non-numeric", () => {
    expect(parseNumber("abc")).toBeNull();
  });

  it("returns null for empty", () => {
    expect(parseNumber("")).toBeNull();
    expect(parseNumber(null as any)).toBeNull();
  });
});

describe("parseDate", () => {
  it("parses ISO date", () => {
    expect(parseDate("2026-07-07")).toBe("2026-07-07");
  });

  it("parses ISO datetime", () => {
    expect(parseDate("2026-07-07T10:30:00Z")).toBe("2026-07-07");
  });

  it("parses MM/DD/YYYY WITHOUT timezone shift", () => {
    expect(parseDate("01/01/2026")).toBe("2026-01-01");
  });

  it("parses MM/DD/YYYY for July", () => {
    expect(parseDate("07/14/2026")).toBe("2026-07-14");
  });

  it("parses DD/MM/YYYY when day > 12", () => {
    expect(parseDate("14/7/2026")).toBe("2026-07-14");
  });

  it("parses Vietnamese date '7 tháng 7, 2026'", () => {
    expect(parseDate("7 tháng 7, 2026")).toBe("2026-07-07");
  });

  it("parses '01/15/2026 04:43' (datetime with time)", () => {
    expect(parseDate("01/15/2026 04:43")).toBe("2026-01-15");
  });

  it("returns null for invalid", () => {
    expect(parseDate("not a date")).toBeNull();
  });
});

describe("canonicalizeUrl", () => {
  it("adds https:// if missing", () => {
    expect(canonicalizeUrl("facebook.com/post/123")).toContain("https://facebook.com/post/123");
  });

  it("strips query params", () => {
    const u = canonicalizeUrl("https://www.facebook.com/post/123?ref=foo&utm_source=x");
    expect(u).toBe("https://www.facebook.com/post/123");
  });

  it("returns null for empty", () => {
    expect(canonicalizeUrl("")).toBeNull();
  });
});

describe("normalizeMessageSnippet", () => {
  it("trims and collapses whitespace", () => {
    expect(normalizeMessageSnippet("  hello\n\n  world  ")).toBe("hello world");
  });

  it("limits to 500 chars", () => {
    const long = "a".repeat(600);
    const r = normalizeMessageSnippet(long);
    expect(r!.length).toBe(500);
  });

  it("returns null for empty", () => {
    expect(normalizeMessageSnippet("")).toBeNull();
    expect(normalizeMessageSnippet("   ")).toBeNull();
  });
});
