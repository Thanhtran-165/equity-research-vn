// src/lib/data_loader.mjs
// Client+server-safe data loader. Uses static JSON imports — no node: imports,
// no fs reads at runtime. Each series JSON is imported directly as an ES module.

import _manifest from "../data/cache/_manifest.json" with { type: "json" };

// Dynamically import all series JSON. Next.js bundles these as static assets.
import _aluminum from "../data/cache/aluminum.json";
import _boj_rate from "../data/cache/boj_rate.json";
import _broad_commodity from "../data/cache/broad_commodity.json";
import _cape from "../data/cache/cape.json";
import _coal from "../data/cache/coal.json";
import _coffee from "../data/cache/coffee.json";
import _cocoa from "../data/cache/cocoa.json";
import _core_cpi from "../data/cache/core_cpi.json";
import _core_pce from "../data/cache/core_pce.json";
import _copper from "../data/cache/copper.json";
import _corn from "../data/cache/corn.json";
import _cpi from "../data/cache/cpi.json";
import _corporate_debt from "../data/cache/corporate_debt.json";
import _deficit from "../data/cache/deficit.json";
import _debt_gdp from "../data/cache/debt_gdp.json";
import _dxy from "../data/cache/dxy.json";
import _federal_debt_total from "../data/cache/federal_debt_total.json";
import _fedfunds from "../data/cache/fedfunds.json";
import _fertilizer from "../data/cache/fertilizer.json";
import _gold from "../data/cache/gold.json";
import _household_debt from "../data/cache/household_debt.json";
import _inflation_expectation from "../data/cache/inflation_expectation.json";
import _interest_expense from "../data/cache/interest_expense.json";
import _japan_cpi from "../data/cache/japan_cpi.json";
import _jgb10y from "../data/cache/jgb10y.json";
import _m2 from "../data/cache/m2.json";
import _mortgage_30y from "../data/cache/mortgage_30y.json";
import _natgas_hh from "../data/cache/natgas_hh.json";
import _nickel from "../data/cache/nickel.json";
import _nominal_gdp from "../data/cache/nominal_gdp.json";
import _oil_brent from "../data/cache/oil_brent.json";
import _oil_wti from "../data/cache/oil_wti.json";
import _participation from "../data/cache/participation.json";
import _pce from "../data/cache/pce.json";
import _productivity from "../data/cache/productivity.json";
import _real_gdp from "../data/cache/real_gdp.json";
import _silver from "../data/cache/silver.json";
import _soybean from "../data/cache/soybean.json";
import _sp500 from "../data/cache/sp500.json";
import _sugar from "../data/cache/sugar.json";
import _term_premium from "../data/cache/term_premium.json";
import _tin from "../data/cache/tin.json";
import _ulc from "../data/cache/ulc.json";
import _unemployment from "../data/cache/unemployment.json";
import _uranium from "../data/cache/uranium.json";
import _usd_jpy from "../data/cache/usd_jpy.json";
import _wage_ahe from "../data/cache/wage_ahe.json";
import _wheat from "../data/cache/wheat.json";
import _y10y_treasury from "../data/cache/y10y_treasury.json";
import _y2y_treasury from "../data/cache/y2y_treasury.json";
import _y30y_treasury from "../data/cache/y30y_treasury.json";

const STORE = {
  aluminum: _aluminum, boj_rate: _boj_rate, broad_commodity: _broad_commodity,
  cape: _cape, coal: _coal, coffee: _coffee, cocoa: _cocoa, core_cpi: _core_cpi,
  core_pce: _core_pce, copper: _copper, corn: _corn, cpi: _cpi,
  corporate_debt: _corporate_debt, deficit: _deficit, debt_gdp: _debt_gdp,
  dxy: _dxy, federal_debt_total: _federal_debt_total, fedfunds: _fedfunds,
  fertilizer: _fertilizer, gold: _gold, household_debt: _household_debt,
  inflation_expectation: _inflation_expectation, interest_expense: _interest_expense,
  japan_cpi: _japan_cpi, jgb10y: _jgb10y, m2: _m2, mortgage_30y: _mortgage_30y,
  natgas_hh: _natgas_hh, nickel: _nickel, nominal_gdp: _nominal_gdp,
  oil_brent: _oil_brent, oil_wti: _oil_wti, participation: _participation,
  pce: _pce, productivity: _productivity, real_gdp: _real_gdp,
  silver: _silver, soybean: _soybean, sp500: _sp500, sugar: _sugar,
  term_premium: _term_premium, tin: _tin, ulc: _ulc, unemployment: _unemployment,
  uranium: _uranium, usd_jpy: _usd_jpy, wage_ahe: _wage_ahe, wheat: _wheat,
  y10y_treasury: _y10y_treasury, y2y_treasury: _y2y_treasury, y30y_treasury: _y30y_treasury,
};

export function getManifest() {
  return _manifest;
}

export function getSeries(key) {
  return STORE[key] || null;
}

export function allSeries() {
  return { ...STORE };
}

export function sourceStats() {
  const m = _manifest;
  const providers = {};
  for (const s of m.series) {
    if (s.derived) continue;
    const prov = s.provider || "None";
    providers[prov] = (providers[prov] || 0) + 1;
  }
  return {
    fetched_at: m.fetched_at,
    has_fred_key: m.has_fred_key,
    ok: m.ok,
    insufficient: m.failed,
    total_series: m.total,
    providers,
    series_list: m.series,
  };
}
