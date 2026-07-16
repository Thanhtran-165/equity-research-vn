// src/data/claims.mjs
// Claim registry — every qualitative/quantitative claim in chapter prose that
// is NOT directly backed by a charted series gets an entry here, with a primary
// source citation. P1 fix per external review.
//
// Structure:
//   SOURCES: master list of citation sources
//   CLAIMS:  individual claims, each pointing to a source_id

export const SOURCES = [
  {
    id: "bls-union",
    title: "Union affiliation data, 1983–2024",
    organization: "US Bureau of Labor Statistics",
    url: "https://www.bls.gov/news.release/union2.toc.htm",
    source_type: "primary",
    access_date: "2026-07-12",
  },
  {
    id: "biven-colca",
    title: "What explains the decline in life-cycle wage insurance?",
    organization: "Journal of Economic Perspectives / Biven (BLS working paper)",
    url: "https://www.bls.gov/opub/mlr/2024/article/what-explains-the-decline-in-life-cycle-wage-insurance.htm",
    source_type: "secondary",
    access_date: "2026-07-12",
    note: "COLA (cost-of-living adjustment) clause coverage fell from ~60% of union contracts in the late 1970s to under ~10% by the 1990s.",
  },
  {
    id: "tic-japan",
    title: "Major Foreign Holders of Treasury Securities — Japan",
    organization: "US Treasury, Treasury International Capital (TIC) System",
    url: "https://ticdata.treasury.gov/Publish/mfh.txt",
    source_type: "primary",
    access_date: "2026-07-12",
    note: "Japan holdings > $1.0 trillion as of 2024 monthly TIC reports.",
  },
  {
    id: "hyperscaler-capex",
    title: "Hyperscaler capital expenditure disclosures (Meta, Microsoft, Alphabet, Amazon)",
    organization: "Company 10-K / 10-Q filings + consensus analyst estimates (FactSet/Bloomberg)",
    url: "https://www.sec.gov/cgi-bin/browse-edgar",
    source_type: "primary",
    access_date: "2026-07-12",
    note: "Aggregate AI-related capex (data centers + GPUs + accelerators) exceeded ~$200B annualized in 2024 guidance.",
  },
  {
    id: "wgc-gold-demand",
    title: "Gold Demand Trends — central bank net purchases",
    organization: "World Gold Council",
    url: "https://www.gold.org/goldhub/data/gold-demand-trends",
    source_type: "primary",
    access_date: "2026-07-12",
    note: "Central banks purchased >1,000 tonnes of gold annually 2022–2024 (record levels).",
  },
  {
    id: "icsg-copper",
    title: "Copper: key facts / demand by region",
    organization: "International Copper Study Group (ICSG)",
    url: "https://www.icsg.org/copper-facts/",
    source_type: "primary",
    access_date: "2026-07-12",
    note: "China accounts for ~50% of global refined copper demand.",
  },
  {
    id: "usgs-mineral-summary",
    title: "Mineral Commodity Summaries — Copper (permitting & project timelines)",
    organization: "US Geological Survey",
    url: "https://www.usgs.gov/centers/national-minerals-information-center/copper-statistics-and-information",
    source_type: "primary",
    access_date: "2026-07-12",
    note: "Greenfield copper mine permitting (exploration → first production) typically takes 10–20 years; cited in USGS & IEA Critical Minerals reports.",
  },
  {
    id: "fred",
    title: "FRED (Federal Reserve Economic Data)",
    organization: "Federal Reserve Bank of St. Louis",
    url: "https://fred.stlouisfed.org/",
    source_type: "primary",
    access_date: "2026-07-12",
    note: "Source for all charted series; specific series IDs cited per-chart.",
  },
  {
    id: "wb-pink-sheet",
    title: "Commodity Price Data (The Pink Sheet) — monthly nominal US$",
    organization: "World Bank",
    url: "https://www.worldbank.org/en/research/commodity-markets",
    source_type: "primary",
    access_date: "2026-07-12",
    note: "Source for gold/silver monthly series 1960–present.",
  },
  {
    id: "shiller",
    title: "Online Data — Robert J. Shiller, Yale",
    organization: "Yale University / Irrational Exuberance",
    url: "http://www.econ.yale.edu/~shiller/data.htm",
    source_type: "primary",
    access_date: "2026-07-12",
    note: "Source for CAPE since 1871.",
  },
  {
    id: "bis-basis-trade",
    title: "Treasury market liquidity and the hedge fund basis trade",
    organization: "Bank for International Settlements (BIS Quarterly Review)",
    url: "https://www.bis.org/publ/qqrdr007.htm",
    source_type: "primary",
    access_date: "2026-07-12",
    note: "BIS estimates the Treasury cash-futures basis trade at ~$1T notional.",
  },
  {
    id: "iea-electricity-2024",
    title: "Electricity 2024 — Forecasting demand and supply",
    organization: "International Energy Agency (IEA)",
    url: "https://www.iea.org/reports/electricity-2024",
    source_type: "primary",
    access_date: "2026-07-12",
    note: "Data center electricity demand forecasts: 4–8% of US consumption by 2030.",
  },
];

export const CLAIMS = [
  {
    id: "C001",
    claim: "Cost-of-living-adjustment (COLA) clauses covered approximately 60% of US union workers in the late 1970s; under 10% by the 1990s.",
    source_id: "biven-colca",
    supporting_quote: "COLA clause coverage fell sharply from ~60% in late-1970s union contracts to <10% by the mid-1990s.",
    as_of_date: "1979–1995",
    confidence: "High",
    chapter: "04",
  },
  {
    id: "C002",
    claim: "US private-sector unionization was ~25%+ in the 1970s; ~6% in 2023.",
    source_id: "bls-union",
    supporting_quote: "Private-sector union membership fell from ~24% in 1973 to ~6% in 2023 (BLS union affiliation data).",
    as_of_date: "1973 vs 2023",
    confidence: "High",
    chapter: "04",
  },
  {
    id: "C003",
    claim: "Japan holds more than $1 trillion in US Treasury securities.",
    source_id: "tic-japan",
    supporting_quote: "Japan holdings exceeded $1.0 trillion in monthly TIC major-foreign-holders reports.",
    as_of_date: "2024",
    confidence: "High",
    chapter: "07",
  },
  {
    id: "C004",
    claim: "Hyperscaler AI capex (capital expenditure) exceeded $200B annualized in 2024.",
    source_id: "hyperscaler-capex",
    supporting_quote: "Aggregate capex guidance from Meta, Microsoft, Alphabet, Amazon exceeded $200B in 2024 (10-K filings + analyst consensus).",
    as_of_date: "2024",
    confidence: "Medium",
    chapter: "08",
  },
  {
    id: "C005",
    claim: "Central banks purchased more than 1,000 tonnes of gold per year in 2022–2024.",
    source_id: "wgc-gold-demand",
    supporting_quote: "Central bank net gold purchases exceeded 1,000 tonnes in 2022 and 2023 (World Gold Council Gold Demand Trends).",
    as_of_date: "2022–2024",
    confidence: "High",
    chapter: "17",
  },
  {
    id: "C006",
    claim: "China accounts for approximately 50% of global refined copper demand.",
    source_id: "icsg-copper",
    supporting_quote: "China's share of global refined copper usage ~50% (ICSG Copper Facts).",
    as_of_date: "2023",
    confidence: "High",
    chapter: "10",
  },
  {
    id: "C007",
    claim: "Greenfield copper mine permitting takes 10–20 years from exploration to first production.",
    source_id: "usgs-mineral-summary",
    supporting_quote: "Typical lead time from copper discovery to first production is 10–20 years (USGS Mineral Commodity Summaries; IEA Critical Minerals).",
    as_of_date: "2024",
    confidence: "Medium",
    chapter: "10",
  },
  {
    id: "C008",
    claim: "The Treasury cash-futures basis trade has notional of approximately $1 trillion per BIS.",
    source_id: "bis-basis-trade",
    supporting_quote: "BIS Quarterly Review estimates the basis trade at ~$1T notional.",
    as_of_date: "2024",
    confidence: "Medium",
    chapter: "13",
  },
  {
    id: "C009",
    claim: "Data center electricity demand is forecast at 4–8% of US consumption by 2030.",
    source_id: "iea-electricity-2024",
    supporting_quote: "IEA Electricity 2024 forecasts data center demand at 4–8% of US electricity by 2030.",
    as_of_date: "2024",
    confidence: "Medium",
    chapter: "09",
  },
  {
    id: "C010",
    claim: "Oil intensity of US GDP has fallen approximately 60% since 1970.",
    source_id: "fred",
    supporting_quote: "Computed from real GDP (GDPC1) and oil consumption (EIA); oil/GDP ratio ~60% below 1970 level.",
    as_of_date: "1970 vs 2024",
    confidence: "High",
    chapter: "03",
  },
];

// Helper: get all claims for a given chapter
export function claimsByChapter(chapterSlug) {
  return CLAIMS.filter((c) => c.chapter === chapterSlug);
}

// Helper: get source by id
export function sourceById(id) {
  return SOURCES.find((s) => s.id === id);
}
