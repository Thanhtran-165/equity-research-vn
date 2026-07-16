// tests/scores.test.mjs
// Test 4: score direction & independence of the new 3-index / 4-subscore system.

import { describe, test, expect } from "vitest";
import {
  DEJAVU_DIMENSIONS, dejavuStats, verdict2D,
} from "../src/data/dejavu_scores.mjs";
import {
  COMMODITY_SCORECARD, commoditySubScores, commodityVerdict,
} from "../src/data/commodity_scores.mjs";

describe("Déjà Vu 3-index system", () => {
  test("every dimension has similarity, break, importance (not P/S/M/O)", () => {
    for (const d of DEJAVU_DIMENSIONS) {
      expect(d.similarity, `${d.id} must have similarity`).toBeDefined();
      expect(d.break, `${d.id} must have break`).toBeDefined();
      expect(d.importance, `${d.id} must have importance`).toBeDefined();
      // Old fields must be gone
      expect(d.P, `${d.id} must not have legacy P field`).toBeUndefined();
      expect(d.S, `${d.id} must not have legacy S field`).toBeUndefined();
      expect(d.M, `${d.id} must not have legacy M field`).toBeUndefined();
      expect(d.O, `${d.id} must not have legacy O field`).toBeUndefined();
    }
  });

  test("each index is in valid range 0-5", () => {
    for (const d of DEJAVU_DIMENSIONS) {
      for (const idx of ["similarity", "break", "importance"]) {
        expect(d[idx], `${d.id}.${idx} must be 0-5`).toBeGreaterThanOrEqual(0);
        expect(d[idx], `${d.id}.${idx} must be 0-5`).toBeLessThanOrEqual(5);
      }
    }
  });

  test("debt has LOW similarity (not high) — P0.1 logic fix", () => {
    const debt = DEJAVU_DIMENSIONS.find((d) => d.id === "debt");
    expect(debt, "debt dimension must exist").toBeDefined();
    // Debt today is very DIFFERENT from 1970s → low similarity
    expect(debt.similarity, "debt similarity must be low (periods differ)").toBeLessThanOrEqual(2);
    // But break severity is HIGH (biggest structural break)
    expect(debt.break, "debt break must be high (analogy fails)").toBeGreaterThanOrEqual(4);
    // And importance is HIGH
    expect(debt.importance, "debt importance must be high").toBeGreaterThanOrEqual(4);
  });

  test("verdict2D returns sensible label for low similarity + high break", () => {
    const fakeDim = { similarity: 1, break: 5, importance: 5 };
    const v = verdict2D(fakeDim);
    expect(v.cls, "should be divergent when break dominates").toBe("divergent");
  });

  test("verdict2D returns 'strong' for high similarity + low break", () => {
    const fakeDim = { similarity: 5, break: 1, importance: 3 };
    const v = verdict2D(fakeDim);
    expect(v.cls, "should be strong when similarity high, break low").toBe("strong");
  });

  test("dejavuStats returns three independent averages", () => {
    const s = dejavuStats();
    expect(s.similarity.avg, "similarity avg").toBeGreaterThanOrEqual(0);
    expect(s.break.avg, "break avg").toBeGreaterThanOrEqual(0);
    expect(s.importance.avg, "importance avg").toBeGreaterThanOrEqual(0);
    // The three should not be identical (proves they're measuring different things)
    const set = new Set([s.similarity.avg, s.break.avg, s.importance.avg]);
    expect(set.size, "three indices should differ").toBeGreaterThan(1);
  });

  test("every dimension has reasoning, counterargument, confidence", () => {
    for (const d of DEJAVU_DIMENSIONS) {
      expect(d.reasoning, `${d.id} must have reasoning`).toBeDefined();
      expect(d.counterargument, `${d.id} must have counterargument`).toBeDefined();
      expect(["High", "Medium", "Low"], `${d.id} confidence must be valid`).toContain(d.confidence);
    }
  });
});

describe("Commodity 4-subscore system", () => {
  test("commoditySubScores returns 5 fields, not a single average", () => {
    const c = COMMODITY_SCORECARD[0];
    const s = commoditySubScores(c);
    expect(s.historical_analogy, "must have historical_analogy").toBeDefined();
    expect(s.supply_tightness, "must have supply_tightness").toBeDefined();
    expect(s.structural_demand, "must have structural_demand").toBeDefined();
    expect(s.oversupply_risk, "must have oversupply_risk").toBeDefined();
    expect(s.net_bullish, "must have net_bullish").toBeDefined();
  });

  test("supply_tightness inverts elasticity (low elasticity → high tightness)", () => {
    // Pick a commodity with very low elasticity (e.g. gold = 1)
    const gold = COMMODITY_SCORECARD.find((c) => c.id === "gold");
    const s = commoditySubScores(gold);
    // Gold elasticity = 1, so tightFromElasticity = 6 - 1 = 5
    // tightness is average of [5, lead_time=5, concentration=3, geopol=4] = 4.25
    expect(s.supply_tightness, "gold tightness should reflect inelastic supply").toBeGreaterThanOrEqual(3.5);
  });

  test("net_bullish = tightness + demand - oversupply", () => {
    const c = COMMODITY_SCORECARD[0];
    const s = commoditySubScores(c);
    const expected = +(s.supply_tightness + s.structural_demand - s.oversupply_risk).toFixed(2);
    expect(s.net_bullish, "net_bullish formula").toBeCloseTo(expected, 1);
  });

  test("nickel has high oversupply_risk (>4) reflecting Indonesia glut", () => {
    const nickel = COMMODITY_SCORECARD.find((c) => c.id === "nickel");
    expect(nickel.oversupply_risk, "nickel oversupply must be high").toBeGreaterThanOrEqual(4);
  });

  test("uranium has high supply_tightness and structural_demand (AI/nuclear theme)", () => {
    const u = COMMODITY_SCORECARD.find((c) => c.id === "uranium");
    const s = commoditySubScores(u);
    expect(s.supply_tightness, "uranium tightness must be high").toBeGreaterThanOrEqual(3.5);
    expect(s.structural_demand, "uranium structural demand must be high").toBeGreaterThanOrEqual(3.5);
  });

  test("commodityVerdict returns one of 5 valid verdicts for every commodity", () => {
    const validCls = ["strong", "medium", "weak", "surface", "insufficient"];
    const validVi = ["Thiếu cung cấu trúc", "Thắt chặt chu kỳ", "Dư cung", "Phụ thuộc địa chính trị", "Narrative chưa đủ bằng chứng"];
    for (const c of COMMODITY_SCORECARD) {
      const v = commodityVerdict(c);
      expect(v, `${c.id} must have verdict`).toBeDefined();
      expect(v.cls, `${c.id} verdict cls must be valid`).toBeOneOf(validCls);
      expect(v.vi, `${c.id} verdict vi must be valid`).toBeOneOf(validVi);
      expect(v.en, `${c.id} verdict en must exist`).toBeTruthy();
    }
  });

  test("nickel verdict is 'Oversupply' (Dư cung)", () => {
    const nickel = COMMODITY_SCORECARD.find((c) => c.id === "nickel");
    const v = commodityVerdict(nickel);
    expect(v.cls, "nickel verdict should be weak (oversupply)").toBe("weak");
    expect(v.vi).toContain("Dư cung");
  });

  test("uranium verdict is 'Structurally scarce' (Thiếu cung cấu trúc)", () => {
    const u = COMMODITY_SCORECARD.find((c) => c.id === "uranium");
    const v = commodityVerdict(u);
    expect(v.cls, "uranium verdict should be strong (scarce)").toBe("strong");
    expect(v.vi).toContain("Thiếu cung");
  });
});
