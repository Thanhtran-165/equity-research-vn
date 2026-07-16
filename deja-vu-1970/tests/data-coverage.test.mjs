// tests/data-coverage.test.mjs
// Test 2: date coverage — confirms series actually span the claimed periods.
// Catches the P0.5 bug where oil_brent (POILBREUSDM) couldn't cover 1973 shock.

import { describe, test, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

function loadCache(key) {
  const p = resolve(process.cwd(), `src/data/cache/${key}.json`);
  try {
    return JSON.parse(readFileSync(p, "utf8"));
  } catch {
    return null;
  }
}

describe("series date coverage", () => {
  test("oil_wti_long covers both 1973 and 1979 shocks (P0.5 fix)", () => {
    const s = loadCache("oil_wti_long");
    expect(s, "oil_wti_long cache must exist").toBeDefined();
    const obs = s.observations.filter((o) => o.value != null);
    const first = obs[0]?.date;
    const last = obs[obs.length - 1]?.date;
    // Must start at or before 1973-10 (embargo) and extend to at least 2024
    expect(first <= "1973-10-01", `oil_wti_long first date ${first} must be ≤ 1973-10`).toBe(true);
    expect(last >= "2024-01-01", `oil_wti_long last date ${last} must be ≥ 2024-01`).toBe(true);
  });

  test("oil_wti_long has actual non-null values at 1973-10 embargo", () => {
    const s = loadCache("oil_wti_long");
    const embargoObs = s.observations.find((o) => o.date.startsWith("1973-10"));
    expect(embargoObs, "must have 1973-10 observation").toBeDefined();
    expect(embargoObs.value, "1973-10 value must be non-null").not.toBeNull();
    expect(embargoObs.value, "1973-10 value must be a number").toBeGreaterThan(0);
  });

  test("cpi covers 1965 to present", () => {
    const s = loadCache("cpi");
    const obs = s.observations.filter((o) => o.value != null);
    expect(obs[0].date <= "1965-01-01", "cpi first obs").toBe(true);
    expect(obs[obs.length - 1].date >= "2024-01-01", "cpi last obs").toBe(true);
  });

  test("gold/silver (CMO Pink Sheet) covers 1965–2024", () => {
    for (const key of ["gold", "silver"]) {
      const s = loadCache(key);
      const obs = s.observations.filter((o) => o.value != null);
      expect(obs[0].date <= "1965-01-01", `${key} first obs`).toBe(true);
      expect(obs[obs.length - 1].date >= "2024-01-01", `${key} last obs`).toBe(true);
    }
  });

  test("no series has negative prices for commodities", () => {
    for (const key of ["gold", "silver", "copper", "oil_brent", "oil_wti", "oil_wti_long", "uranium", "wheat"]) {
      const s = loadCache(key);
      if (!s) continue;
      const negatives = s.observations.filter((o) => o.value != null && o.value < 0);
      expect(negatives, `${key} must have no negative prices`).toHaveLength(0);
    }
  });
});
