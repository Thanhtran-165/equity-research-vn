// tests/transforms.test.mjs
// Test 3: transform formulas — especially the P0.4 stock-bond correlation fix.

import { describe, test, expect } from "vitest";
import {
  yoyPct, deflate, toMonthly, rollingMean, equityBondCorr,
  byDate, filterRange, rebase, drawdown, zscore,
} from "../src/lib/transforms.mjs";

describe("transforms", () => {
  test("yoyPct computes correct year-over-year percent", () => {
    const input = [
      { date: "2020-01-01", value: 100 },
      { date: "2020-02-01", value: 101 },
      // ...
      { date: "2021-01-01", value: 110 }, // 10% YoY
      { date: "2021-02-01", value: 111.1 }, // 10% YoY
    ];
    const out = yoyPct(input);
    const jan21 = out.find((o) => o.date === "2021-01-01");
    expect(jan21.value).toBeCloseTo(10, 1);
  });

  test("yoyPct returns empty for single observation", () => {
    expect(yoyPct([{ date: "2020-01-01", value: 100 }])).toHaveLength(0);
  });

  test("deflate produces real values reindexed to base year", () => {
    const nominal = [{ date: "2024-01-01", value: 200 }];
    const cpi = [{ date: "2024-01-01", value: 100 }];
    const out = deflate(nominal, cpi, 2024);
    // real = nominal / cpi * cpi_base; base = 100; so real = 200/100*100 = 200
    expect(out[0].value).toBeCloseTo(200, 1);
  });

  test("toMonthly takes last value of each month from daily", () => {
    const daily = [
      { date: "2024-01-01", value: 1 },
      { date: "2024-01-15", value: 2 },
      { date: "2024-01-31", value: 3 },
      { date: "2024-02-01", value: 4 },
    ];
    const m = toMonthly(daily);
    expect(m).toHaveLength(2);
    expect(m[0].value).toBe(3); // last value of Jan
    expect(m[1].value).toBe(4); // only value of Feb
  });

  test("rollingMean averages over window", () => {
    const input = [{ date: "2024-01-01", value: 2 }, { date: "2024-02-01", value: 4 }, { date: "2024-03-01", value: 6 }];
    const out = rollingMean(input, 2);
    expect(out).toHaveLength(2);
    expect(out[0].value).toBe(3); // (2+4)/2
    expect(out[1].value).toBe(5); // (4+6)/2
  });

  test("equityBondCorr uses bond-return proxy not yield change (P0.4 fix)", () => {
    // Construct synthetic data where equity UP, yield DOWN (so bond return UP).
    // Yield-change correlation would be negative; bond-return correlation should be positive.
    const equity = [
      { date: "2024-01-01", value: 100 },
      { date: "2024-02-01", value: 101 }, // up 1%
      { date: "2024-03-01", value: 102 }, // up ~1%
      { date: "2024-04-01", value: 103 },
      { date: "2024-05-01", value: 104 },
    ];
    const yields = [
      { date: "2024-01-01", value: 4.0 },
      { date: "2024-02-01", value: 3.9 }, // yield down 10bp
      { date: "2024-03-01", value: 3.8 },
      { date: "2024-04-01", value: 3.7 },
      { date: "2024-05-01", value: 3.6 },
    ];
    const corr = equityBondCorr(equity, yields, 3, 8);
    expect(corr.length, "should produce correlation series").toBeGreaterThan(0);
    // Bond return = -D × Δy + carry. Yield fell → bond return positive. Equity rose → return positive.
    // So correlation should be POSITIVE (both up together).
    const avgCorr = corr.reduce((s, x) => s + x.value, 0) / corr.length;
    expect(avgCorr, "stock-bond RETURN correlation should be positive when both rise together").toBeGreaterThan(0);
  });

  test("rebase sets chosen date to 100", () => {
    const input = [{ date: "2020-01-01", value: 50 }, { date: "2021-01-01", value: 100 }];
    const out = rebase(input, "2020-01-01");
    expect(out[0].value).toBeCloseTo(100, 1);
    expect(out[1].value).toBeCloseTo(200, 1);
  });

  test("drawdown returns 0 at peak, negative otherwise", () => {
    const input = [{ date: "2024-01-01", value: 100 }, { date: "2024-02-01", value: 80 }];
    const out = drawdown(input);
    expect(out[0].value).toBe(0); // at peak
    expect(out[1].value).toBeCloseTo(-20, 0); // 20% drawdown
  });

  test("zscore centers around 0", () => {
    const input = [{ date: "2024-01-01", value: 1 }, { date: "2024-02-01", value: 2 }, { date: "2024-03-01", value: 3 }];
    const out = zscore(input);
    const mean = out.reduce((s, x) => s + x.value, 0) / out.length;
    expect(Math.abs(mean), "zscore mean ≈ 0").toBeLessThan(0.01);
  });

  test("filterRange respects bounds", () => {
    const input = [
      { date: "2020-01-01", value: 1 },
      { date: "2021-01-01", value: 2 },
      { date: "2022-01-01", value: 3 },
    ];
    const out = filterRange(input, "2021-01-01", "2022-06-01");
    expect(out).toHaveLength(2);
  });

  test("byDate filters nulls and sorts ascending", () => {
    const input = [
      { date: "2024-02-01", value: 2 },
      { date: "2024-01-01", value: 1 },
      { date: "2024-03-01", value: null }, // should be filtered
    ];
    const out = byDate(input);
    expect(out).toHaveLength(2);
    expect(out[0].date).toBe("2024-01-01");
  });
});
