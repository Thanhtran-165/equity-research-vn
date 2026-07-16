// src/data/registry.mjs
// Data registry: every mandated series from the brief (§10) mapped to
// [primary (FRED), fallbacks (no-key sources)] so the fetcher can resolve them.
// Each entry: { key, label, unit, freq, series: [{provider,id,...}] }
// FRED series IDs verified from FRED public catalog.
//
// When FRED_API_KEY is absent, the fetcher falls back to the no-key sources.
// If none yields data, the series is flagged `insufficient_primary_data` and
// shown honestly as "no primary data" — never fabricated.

export const REGISTRY = [
  // ---- US INFLATION & PRICES ----
  { key: "cpi", label: "US CPI (headline, YoY %)", unit: "% YoY", freq: "monthly", series: [
    { provider: "FRED", id: "CPIAUCSL", opts: { freq: "Monthly", unit: "Index" } }, // index; we transform to YoY later
    { provider: "WorldBank", id: "FP.CPI.TOTL.ZG", country: "USA", opts: { unit: "% YoY" } }, // already YoY
  ]},
  { key: "core_cpi", label: "US Core CPI (less food & energy, YoY %)", unit: "% YoY", freq: "monthly", series: [
    { provider: "FRED", id: "CPILFESL", opts: { freq: "Monthly", unit: "Index" } },
  ]},
  { key: "pce", label: "US PCE (headline, YoY %)", unit: "% YoY", freq: "monthly", series: [
    { provider: "FRED", id: "PCEPI", opts: { freq: "Monthly", unit: "Index" } },
  ]},
  { key: "core_pce", label: "US Core PCE (YoY %)", unit: "% YoY", freq: "monthly", series: [
    { provider: "FRED", id: "PCEPILFE", opts: { freq: "Monthly", unit: "Index" } },
  ]},
  { key: "inflation_expectation", label: "Univ. Michigan 1-yr inflation expectation (%)", unit: "%", freq: "monthly", series: [
    { provider: "FRED", id: "MICH", opts: { freq: "Monthly", unit: "%" } },
  ]},

  // ---- US GROWTH & LABOR ----
  { key: "real_gdp", label: "US Real GDP (% YoY)", unit: "% YoY", freq: "quarterly", series: [
    { provider: "FRED", id: "GDPC1", opts: { freq: "Quarterly", unit: "Bil. Chn. 2017 $" } },
    { provider: "WorldBank", id: "NY.GDP.MKTP.KD.ZG", country: "USA", opts: { unit: "% YoY" } },
  ]},
  { key: "nominal_gdp", label: "US Nominal GDP ($Bn)", unit: "$Bn", freq: "quarterly", series: [
    { provider: "FRED", id: "GDP", opts: { freq: "Quarterly", unit: "$Bn" } },
  ]},
  { key: "unemployment", label: "US Unemployment rate (U-3, %)", unit: "%", freq: "monthly", series: [
    { provider: "FRED", id: "UNRATE", opts: { freq: "Monthly", unit: "%" } },
    { provider: "WorldBank", id: "SL.UEM.TOTL.ZS", country: "USA" },
  ]},
  { key: "participation", label: "US Labor Force Participation (%)", unit: "%", freq: "monthly", series: [
    { provider: "FRED", id: "CIVPART", opts: { freq: "Monthly", unit: "%" } },
  ]},
  { key: "wage_ahe", label: "Avg Hourly Earnings, Total Private ($/hr)", unit: "$/hr", freq: "monthly", series: [
    { provider: "FRED", id: "CES0500000003", opts: { freq: "Monthly", unit: "$/hr" } },
  ]},
  { key: "productivity", label: "Nonfarm Business Productivity (YoY %)", unit: "% YoY", freq: "quarterly", series: [
    { provider: "FRED", id: "OPHNFB", opts: { freq: "Quarterly", unit: "Index" } },
  ]},
  { key: "ulc", label: "Unit Labor Cost (YoY %)", unit: "% YoY", freq: "quarterly", series: [
    { provider: "FRED", id: "ULCNFB", opts: { freq: "Quarterly", unit: "Index" } },
  ]},

  // ---- US MONETARY POLICY & RATES ----
  { key: "fedfunds", label: "Fed Funds Effective Rate (%)", unit: "%", freq: "monthly", series: [
    { provider: "FRED", id: "FEDFUNDS", opts: { freq: "Monthly", unit: "%" } },
  ]},
  { key: "y2y_treasury", label: "2-Year Treasury yield (%)", unit: "%", freq: "daily", series: [
    { provider: "FRED", id: "DGS2", opts: { freq: "Daily", unit: "%" } },
  ]},
  { key: "y10y_treasury", label: "10-Year Treasury yield (%)", unit: "%", freq: "daily", series: [
    { provider: "FRED", id: "DGS10", opts: { freq: "Daily", unit: "%" } },
  ]},
  { key: "y30y_treasury", label: "30-Year Treasury yield (%)", unit: "%", freq: "daily", series: [
    { provider: "FRED", id: "DGS30", opts: { freq: "Daily", unit: "%" } },
  ]},
  { key: "real_policy_rate", label: "Real Fed Funds (FFR - core CPI YoY, %)", unit: "%", freq: "monthly", derived: "fedfunds - core_cpi_yoy" },
  { key: "term_premium", label: "ACM Term Premium 10Y (%)", unit: "%", freq: "daily", series: [
    { provider: "FRED", id: "THREEFYTP10", opts: { freq: "Daily", unit: "%" } },
  ]},
  { key: "m2", label: "M2 Money Supply ($Bn)", unit: "$Bn", freq: "monthly", series: [
    { provider: "FRED", id: "M2SL", opts: { freq: "Monthly", unit: "$Bn" } },
  ]},

  // ---- US FISCAL & DEBT ----
  { key: "debt_gdp", label: "Federal Debt Held by Public / GDP (%)", unit: "%", freq: "quarterly", series: [
    { provider: "FRED", id: "FYGFGDQ188S", opts: { freq: "Quarterly", unit: "%" } }, // Federal Debt Held by Public / GDP (correct)
  ]},
  { key: "federal_debt_total", label: "Total Federal Debt / GDP (%)", unit: "%", freq: "quarterly", series: [
    { provider: "FRED", id: "GFDEGDQ188S", opts: { freq: "Quarterly", unit: "%" } }, // Total Public Debt / GDP (correct label)
  ]},
  { key: "deficit", label: "Federal Surplus/Deficit (% GDP)", unit: "% GDP", freq: "annual", series: [
    { provider: "FRED", id: "FYFSGDA188S", opts: { freq: "Annual", unit: "%" } }, // surplus/deficit (correct)
  ]},
  { key: "interest_expense", label: "Net Interest Expense on Public Debt ($Bn)", unit: "$Bn", freq: "annual", series: [
    { provider: "FRED", id: "A091RC1Q027SBEA", opts: { freq: "Quarterly", unit: "$Bn" } },
  ]},

  // ---- HOUSEHOLD / CORPORATE DEBT ----
  { key: "household_debt", label: "Household Debt / GDP (%)", unit: "%", freq: "quarterly", series: [
    { provider: "FRED", id: "HDTGPDUSQ163N", opts: { freq: "Quarterly", unit: "%" } },
  ]},
  { key: "corporate_debt", label: "Nonfinancial Corporate Debt / GDP (%)", unit: "%", freq: "quarterly", series: [
    { provider: "FRED", id: "BCNSDODNS", opts: {} },
  ]},
  { key: "mortgage_30y", label: "30-Year Fixed Mortgage Rate (%)", unit: "%", freq: "weekly", series: [
    { provider: "FRED", id: "MORTGAGE30US", opts: { freq: "Weekly", unit: "%" } },
  ]},

  // ---- FX ----
  { key: "dxy", label: "Trade-Weighted Dollar Index (Broad)", unit: "index", freq: "monthly", series: [
    { provider: "FRED", id: "DTWEXBGS", opts: { freq: "Daily", unit: "Index Jan 2006=100" } },
  ]},
  { key: "usd_jpy", label: "USD/JPY (¥ per $)", unit: "JPY", freq: "daily", series: [
    { provider: "FRED", id: "DEXJPUS", opts: { freq: "Daily", unit: "Yen/$" } },
    { provider: "Stooq", id: "usdjpy", opts: { unit: "JPY/$" } },
  ]},

  // ---- JAPAN ----
  { key: "boj_rate", label: "Japan Call/Interbank Rate (%)", unit: "%", freq: "monthly", series: [
    { provider: "FRED", id: "IRSTCI01JPM156N", opts: { freq: "Monthly", unit: "%" } },
  ]},
  { key: "jgb10y", label: "Japan 10Y JGB yield (%)", unit: "%", freq: "monthly", series: [
    { provider: "FRED", id: "IRLTLT01JPM156N", opts: { freq: "Monthly", unit: "%" } },
  ]},
  { key: "japan_cpi", label: "Japan CPI (YoY %)", unit: "% YoY", freq: "monthly", series: [
    { provider: "FRED", id: "JPNCPIALLMINMEI", opts: {} },
    { provider: "WorldBank", id: "FP.CPI.TOTL.ZG", country: "JPN" },
  ]},

  // ---- EQUITY & VALUATION ----
  { key: "sp500", label: "S&P 500 (close)", unit: "index", freq: "monthly", series: [
    { provider: "FRED", id: "SP500", opts: { freq: "Daily", unit: "Index" } },
    { provider: "Stooq", id: "^spx", opts: { unit: "index" } },
  ]},
  { key: "cape", label: "Shiller CAPE (Cyclically Adjusted P/E)", unit: "ratio", freq: "monthly", derived: "shiller_online_xls (Robert Shiller, Yale)" },
  { key: "market_concentration", label: "Top-4 S&P 500 weight proxy (CR4, %)", unit: "%", freq: "monthly", derived: "from separate concentration source" },

  // ---- STOCK-BOND CORRELATION ----
  { key: "stock_bond_corr", label: "S&P 500 / 10Y rolling 36M correlation", unit: "corr", freq: "monthly", derived: "rolling corr(spx_ret, 10y_chg)" },

  // ---- COMMODITIES — ENERGY ----
  { key: "oil_brent", label: "Crude oil, Brent-equivalent ($/bbl)", unit: "$/bbl", freq: "monthly", series: [
    { provider: "FRED", id: "POILBREUSDM", opts: { freq: "Monthly", unit: "$/bbl" } },
  ]},
  { key: "oil_wti", label: "WTI crude spot ($/bbl)", unit: "$/bbl", freq: "monthly", series: [
    { provider: "FRED", id: "POILWTIUSDM", opts: { freq: "Monthly", unit: "$/bbl" } },
  ]},
  // Long-history WTI spot (1946–present) — required to cover 1973 & 1979 shocks.
  // POILBREUSDM/POILWTIUSDM only have usable values from ~1990.
  { key: "oil_wti_long", label: "WTI spot crude — long history ($/bbl)", unit: "$/bbl", freq: "monthly", series: [
    { provider: "FRED", id: "WTISPLC", opts: { freq: "Monthly", unit: "$/bbl" } },
  ]},
  { key: "natgas_hh", label: "Henry Hub natural gas ($/MMBtu)", unit: "$/MMBtu", freq: "monthly", series: [
    { provider: "FRED", id: "PNGASUSUSDM", opts: { freq: "Monthly", unit: "$/MMBtu" } },
  ]},
  { key: "coal", label: "Coal (Australia, $/mt)", unit: "$/mt", freq: "monthly", series: [
    { provider: "FRED", id: "PCOALAUUSDM", opts: { freq: "Monthly", unit: "$/mt" } },
  ]},

  // ---- COMMODITIES — PRECIOUS ----
  { key: "gold", label: "Gold ($/troy oz)", unit: "$/oz", freq: "monthly", series: [
    { provider: "CMO", id: "GOLD", opts: { unit: "$/troy oz" } },
  ]},
  { key: "silver", label: "Silver ($/troy oz)", unit: "$/oz", freq: "monthly", series: [
    { provider: "CMO", id: "SILVER", opts: { unit: "$/troy oz" } },
  ]},

  // ---- COMMODITIES — BASE / INDUSTRIAL ----
  { key: "copper", label: "Copper ($/mt)", unit: "$/mt", freq: "monthly", series: [
    { provider: "FRED", id: "PCOPPUSDM", opts: { freq: "Monthly", unit: "$/mt" } },
  ]},
  { key: "aluminum", label: "Aluminum ($/mt)", unit: "$/mt", freq: "monthly", series: [
    { provider: "FRED", id: "PALUMUSDM", opts: { freq: "Monthly", unit: "$/mt" } },
  ]},
  { key: "nickel", label: "Nickel ($/mt)", unit: "$/mt", freq: "monthly", series: [
    { provider: "FRED", id: "PNICKUSDM", opts: { freq: "Monthly", unit: "$/mt" } },
  ]},
  { key: "tin", label: "Tin ($/mt)", unit: "$/mt", freq: "monthly", series: [
    { provider: "FRED", id: "PTINUSDM", opts: { freq: "Monthly", unit: "$/mt" } },
  ]},

  // ---- COMMODITIES — NUCLEAR ----
  { key: "uranium", label: "Uranium ($/lb U3O8)", unit: "$/lb", freq: "monthly", series: [
    { provider: "FRED", id: "PURANUSDM", opts: { freq: "Monthly", unit: "$/lb" } },
  ]},

  // ---- COMMODITIES — AGRICULTURE ----
  { key: "wheat", label: "Wheat ($/mt)", unit: "$/mt", freq: "monthly", series: [
    { provider: "FRED", id: "PWHEAMTUSDM", opts: { freq: "Monthly", unit: "$/mt" } },
  ]},
  { key: "corn", label: "Corn ($/mt)", unit: "$/mt", freq: "monthly", series: [
    { provider: "FRED", id: "PMAIZMTUSDM", opts: { freq: "Monthly", unit: "$/mt" } },
  ]},
  { key: "soybean", label: "Soybean ($/mt)", unit: "$/mt", freq: "monthly", series: [
    { provider: "FRED", id: "PSOYBUSDM", opts: { freq: "Monthly", unit: "$/mt" } },
  ]},
  { key: "sugar", label: "Sugar ($/kg)", unit: "$/kg", freq: "monthly", series: [
    { provider: "FRED", id: "PSUGAISAUSDM", opts: { freq: "Monthly", unit: "$/kg" } },
  ]},
  { key: "coffee", label: "Coffee (Other Mild Arabica, $/kg)", unit: "$/kg", freq: "monthly", series: [
    { provider: "FRED", id: "PCOFFOTMUSDM", opts: { freq: "Monthly", unit: "$/kg" } },
  ]},
  { key: "cocoa", label: "Cocoa ($/kg)", unit: "$/kg", freq: "monthly", series: [
    { provider: "FRED", id: "PCOCOUSDM", opts: { freq: "Monthly", unit: "$/kg" } },
  ]},
  { key: "fertilizer", label: "Fertilizer (Nitrogenous Mfg PPI, index)", unit: "index", freq: "monthly", series: [
    { provider: "FRED", id: "PCU325311325311", opts: { freq: "Monthly", unit: "Index" } },
  ]},

  // ---- BROAD COMMODITY INDEX ----
  { key: "broad_commodity", label: "Commodity Price Index ( IMF, 2016=100)", unit: "index", freq: "monthly", series: [
    { provider: "FRED", id: "PALLFNFINDEXM", opts: { freq: "Monthly", unit: "Index" } },
  ]},
];

// Quick lookup by key.
export const BY_KEY = Object.fromEntries(REGISTRY.map((r) => [r.key, r]));
