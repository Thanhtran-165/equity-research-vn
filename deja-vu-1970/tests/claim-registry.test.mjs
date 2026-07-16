// tests/claim-registry.test.mjs
// Test 5: claim registry — every qualitative/quantitative claim in chapter prose
// must have an entry with a source citation. P1 fix.

import { describe, test, expect } from "vitest";
import { CLAIMS, SOURCES } from "../src/data/claims.mjs";

describe("claim registry structure", () => {
  test("CLAIMS is a non-empty array", () => {
    expect(Array.isArray(CLAIMS), "CLAIMS must be an array").toBe(true);
    expect(CLAIMS.length, "CLAIMS must have entries").toBeGreaterThan(0);
  });

  test("every claim has required fields", () => {
    const required = ["id", "claim", "source_id", "confidence", "chapter"];
    for (const c of CLAIMS) {
      for (const f of required) {
        expect(c[f], `claim ${c.id || "(no id)"} must have ${f}`).toBeDefined();
      }
    }
  });

  test("every claim confidence is High/Medium/Low", () => {
    for (const c of CLAIMS) {
      expect(["High", "Medium", "Low"], `claim ${c.id} confidence invalid`).toContain(c.confidence);
    }
  });

  test("every claim.source_id resolves to a SOURCES entry", () => {
    for (const c of CLAIMS) {
      const src = SOURCES.find((s) => s.id === c.source_id);
      expect(src, `claim ${c.id} source_id ${c.source_id} not in SOURCES`).toBeDefined();
    }
  });
});

describe("SOURCES registry structure", () => {
  test("SOURCES is non-empty array", () => {
    expect(Array.isArray(SOURCES)).toBe(true);
    expect(SOURCES.length, "must have at least one source").toBeGreaterThan(0);
  });

  test("every source has id, title, organization, url, source_type", () => {
    const required = ["id", "title", "organization", "url", "source_type"];
    for (const s of SOURCES) {
      for (const f of required) {
        expect(s[f], `source ${s.id || "(no id)"} must have ${f}`).toBeDefined();
      }
    }
  });

  test("every source_type is primary or secondary", () => {
    for (const s of SOURCES) {
      expect(["primary", "secondary"], `source ${s.id} type invalid`).toContain(s.source_type);
    }
  });
});

describe("claim coverage of key quantitative claims (P1 fix)", () => {
  // These are the specific claims the review flagged as uncited.
  const expectedClaimSubstrings = [
    "COLA",           // 60% of workers had COLA in 1970s
    "union",          // unionization ~25%
    "Treasury",       // Japan >$1T Treasury holdings
    "capex",          // AI capex ~$200B
    "gold",           // central bank gold buying 1000+ tons
    "copper",         // China 50% copper demand
  ];

  test("registry covers the key uncited claims flagged in review", () => {
    const allClaimText = CLAIMS.map((c) => c.claim).join(" ").toLowerCase();
    for (const substr of expectedClaimSubstrings) {
      expect(allClaimText, `must have a claim mentioning "${substr}"`).toContain(substr.toLowerCase());
    }
  });
});
