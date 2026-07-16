// tests/series-mapping.test.mjs
// Test 1: series key ↔ FRED ID ↔ label consistency.
// Catches the P0.3 bug where debt_gdp pointed to a deficit series.

import { describe, test, expect } from "vitest";
import { REGISTRY, BY_KEY } from "../src/data/registry.mjs";

describe("series registry mapping", () => {
  test("every registry entry has a key, label, unit, freq, and series list", () => {
    for (const entry of REGISTRY) {
      expect(entry.key, `entry must have key`).toBeTruthy();
      expect(entry.label, `${entry.key} must have label`).toBeTruthy();
      expect(entry.unit, `${entry.key} must have unit`).toBeTruthy();
      expect(entry.freq, `${entry.key} must have freq`).toBeTruthy();
      // Either series list or derived flag
      expect(entry.series || entry.derived, `${entry.key} must have series or be derived`).toBeTruthy();
    }
  });

  test("BY_KEY lookup contains every registry entry", () => {
    for (const entry of REGISTRY) {
      expect(BY_KEY[entry.key], `BY_KEY must contain ${entry.key}`).toBeDefined();
    }
  });

  test("debt_gdp does NOT map to deficit series (P0.3 fix)", () => {
    const debt = BY_KEY["debt_gdp"];
    expect(debt, "debt_gdp must exist").toBeDefined();
    // FYFSGDA188S is Federal Surplus/Deficit, NOT debt/GDP. Must not appear here.
    const seriesIds = (debt.series || []).map((s) => s.id);
    expect(seriesIds, "debt_gdp must not use FYFSGDA188S").not.toContain("FYFSGDA188S");
    // Should map to a debt/GDP series
    expect(seriesIds.some((id) => /GDQ|GDP|DEBT/i.test(id)), "debt_gdp should point to a debt series").toBe(true);
  });

  test("deficit maps to FYFSGDA188S (deficit/surplus series)", () => {
    const deficit = BY_KEY["deficit"];
    expect(deficit, "deficit must exist").toBeDefined();
    const seriesIds = (deficit.series || []).map((s) => s.id);
    expect(seriesIds, "deficit should use FYFSGDA188S").toContain("FYFSGDA188S");
  });

  test("federal_debt_total label matches 'Total Public Debt' not 'Held by Public'", () => {
    const total = BY_KEY["federal_debt_total"];
    // GFDEGDQ188S is "Total Public Debt" — must not be labeled "held by public"
    expect(total.label.toLowerCase(), "label must not say 'held by public'").not.toContain("held by public");
  });

  test("oil_wti_long exists for historical coverage (P0.5 fix)", () => {
    expect(BY_KEY["oil_wti_long"], "must have oil_wti_long series").toBeDefined();
    const ids = (BY_KEY["oil_wti_long"].series || []).map((s) => s.id);
    expect(ids, "oil_wti_long should use WTISPLC").toContain("WTISPLC");
  });
});
