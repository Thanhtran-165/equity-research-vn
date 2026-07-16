// src/lib/providers.mjs
// Pluggable data providers. FRED is primary (needs key). Fallbacks are no-key.
// Every provider returns: { series, source, provider, freq, unit, observations: [{date, value}], updated, note? }
// value is always a JS number or null (for missing/".").

// ---------------------------------------------------------------------------
// FRED  —  https://fred.stlouisfed.org/docs/api/fred/series_observations.html
// ---------------------------------------------------------------------------
export async function fetchFred(seriesId, opts = {}) {
  const key = process.env.FRED_API_KEY || (typeof Deno !== "undefined" ? Deno.env.get("FRED_API_KEY") : "");
  if (!key) throw new Error("NO_FRED_KEY");
  const params = new URLSearchParams({
    series_id: seriesId,
    api_key: key,
    file_type: "json",
    observation_start: opts.observation_start || "1960-01-01",
    observation_end: opts.observation_end || "",
  });
  const url = `https://api.stlouisfed.org/fred/series/observations?${params}`;
  const r = await fetch(url);
  if (!r.ok) {
    const body = await r.text();
    throw new Error(`FRED ${seriesId} HTTP ${r.status}: ${body.slice(0, 200)}`);
  }
  const j = await r.json();
  return {
    provider: "FRED",
    source: `FRED series ${seriesId}`,
    source_url: `https://fred.stlouisfed.org/series/${seriesId}`,
    freq: j.frequency || opts.freq || "?",
    unit: j.units || opts.unit || "?",
    observations: (j.observations || []).map((o) => ({
      date: o.date,
      value: o.value === "." ? null : Number(o.value),
    })),
    updated: new Date().toISOString().slice(0, 10),
  };
}

// ---------------------------------------------------------------------------
// Stooq (no key) — daily quotes for many series incl. gold, USD/JPY, S&P.
// Returns CSV. Endpoint: https://stooq.com/q/d/l/?s={SYMBOL}&i=d
// ---------------------------------------------------------------------------
export async function fetchStooq(symbol, opts = {}) {
  const url = `https://stooq.com/q/d/l/?s=${symbol}&i=d`;
  const r = await fetch(url, { headers: { "User-Agent": "DejaVuResearch/1.0" } });
  if (!r.ok) throw new Error(`Stooq ${symbol} HTTP ${r.status}`);
  const text = await r.text();
  const lines = text.trim().split("\n");
  if (lines.length < 2) throw new Error(`Stooq ${symbol}: no data`);
  const header = lines[0].split(",");
  const obs = [];
  for (const line of lines.slice(1)) {
    const cols = line.split(",");
    const date = cols[0];
    const close = Number(cols[4]);
    if (date && Number.isFinite(close)) obs.push({ date, value: close });
  }
  return {
    provider: "Stooq",
    source: `Stooq symbol ${symbol}`,
    source_url: `https://stooq.com/q/?s=${symbol}`,
    freq: "daily",
    unit: opts.unit || symbol.includes("/") ? "rate" : "price",
    observations: obs,
    updated: new Date().toISOString().slice(0, 10),
    note: "Stooq provides daily close. For series needing monthly/annual, caller should resample.",
  };
}

// ---------------------------------------------------------------------------
// World Bank (no key) — wide country coverage for CPI, GDP, debt, demographics.
// https://api.worldbank.org/v2/country/{CC}/indicator/{IND}?format=json&per_page=20000
// ---------------------------------------------------------------------------
export async function fetchWorldBank(indicator, country = "USA", opts = {}) {
  const url = `https://api.worldbank.org/v2/country/${country}/indicator/${indicator}?format=json&per_page=20000&date=1960:2025`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`WorldBank ${indicator} HTTP ${r.status}`);
  const j = await r.json();
  const data = Array.isArray(j) && j[1] ? j[1] : [];
  return {
    provider: "World Bank",
    source: `World Bank WDI ${indicator}`,
    source_url: `https://data.worldbank.org/indicator/${indicator}`,
    freq: "annual",
    unit: opts.unit || "?",
    observations: data
      .map((d) => ({ date: `${d.date}-01-01`, value: d.value == null ? null : Number(d.value) }))
      .sort((a, b) => a.date.localeCompare(b.date)),
    updated: new Date().toISOString().slice(0, 10),
  };
}

// ---------------------------------------------------------------------------
// IMF SDMX (no key) — broad macro & some commodities, quarterly/annual.
// https://api.imf.org/external/sdmx/2.1/data/{DB}/{KEY}?startPeriod=1960
// ---------------------------------------------------------------------------
export async function fetchIMF(database, key, opts = {}) {
  const start = opts.start || "1960";
  const url = `https://api.imf.org/external/sdmx/2.1/data/${database}/${key}?startPeriod=${start}&endPeriod=2025`;
  const r = await fetch(url, { headers: { Accept: "application/json" } });
  if (!r.ok) throw new Error(`IMF ${database}/${key} HTTP ${r.status}`);
  const text = await r.text();
  // IMF JSON is messy; try parse, else throw a soft signal.
  let j;
  try { j = JSON.parse(text); } catch { throw new Error(`IMF ${key}: non-JSON`); }
  // The structure varies; we leave it to the caller / registry to know its shape.
  return {
    provider: "IMF",
    source: `IMF SDMX ${database}/${key}`,
    source_url: `https://data.imf.org/`,
    freq: opts.freq || "?",
    unit: opts.unit || "?",
    observations: [], // parse-improvements land in the registry adapter
    updated: new Date().toISOString().slice(0, 10),
    note: "IMF SDMX response shape varies; adapter must parse.",
    _raw: j,
  };
}

// ---------------------------------------------------------------------------
// ECB Data Portal (no key) — EUR yields, exchange rates, gold reserves.
// https://data-api.ecb.europa.eu/service/data/{FLOW}/{KEY}
// ---------------------------------------------------------------------------
export async function fetchECB(flow, key, opts = {}) {
  const url = `https://data-api.ecb.europa.eu/service/data/${flow}/${key}?format=csvdata&startPeriod=1960`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`ECB ${flow}/${key} HTTP ${r.status}`);
  const text = await r.text();
  const lines = text.trim().split("\n");
  const header = lines[0].split(",");
  const dateIdx = header.findIndex((h) => h === "TIME_PERIOD");
  const valIdx = header.findIndex((h) => h === "OBS_VALUE");
  if (dateIdx < 0 || valIdx < 0) throw new Error(`ECB ${key}: no TIME_PERIOD/OBS_VALUE`);
  const obs = [];
  for (const line of lines.slice(1)) {
    const cols = line.split(",");
    const v = Number(cols[valIdx]);
    if (cols[dateIdx] && Number.isFinite(v)) obs.push({ date: cols[dateIdx], value: v });
  }
  return {
    provider: "ECB",
    source: `ECB Data Portal ${flow}/${key}`,
    source_url: `https://data.ecb.europa.eu/`,
    freq: opts.freq || "?",
    unit: opts.unit || "?",
    observations: obs,
    updated: new Date().toISOString().slice(0, 10),
  };
}

// ---------------------------------------------------------------------------
// BOJ Time-Series (no key) — JGB yields, BOJ policy, Japan CPI.
// https://www.stat-search.boj.or.jp/ssi/mtshtml/fm_tD.html — site is HTML.
// Programmatic CSV: https://www.stat-search.boj.or.jp/info/ssi/csv/fm_TD.html
// For simplicity we map a small set; many BOJ series are also on FRED.
// ---------------------------------------------------------------------------
// We rely on FRED mirror where possible (e.g. INTGSBJPM193N). Listed in registry.

// ---------------------------------------------------------------------------
// US Treasury Daily Treasury Par Yield Curve (no key) — for term premium proxies.
// https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/all?type=daily_field_rate&year=all
// ---------------------------------------------------------------------------
export async function fetchTreasury(year = "all") {
  const url = `https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/all?type=daily_field_rate&year=${year}`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`Treasury HTTP ${r.status}`);
  const text = await r.text();
  const lines = text.trim().split("\n");
  const header = lines[0].split(",");
  return {
    provider: "US Treasury",
    source: "US Treasury Daily Par Yield Curve",
    source_url: url,
    freq: "daily",
    unit: "percent",
    header,
    rows: lines.slice(1).map((l) => l.split(",")),
    updated: new Date().toISOString().slice(0, 10),
    note: "Multi-column; adapter picks the column.",
  };
}

// ---------------------------------------------------------------------------
// Resolve a series: try primary then fallbacks; return first success.
// Each candidate in the registry list: {provider, id, opts}.
// ---------------------------------------------------------------------------
export async function resolveSeries(candidates, meta = {}) {
  const errors = [];
  for (const c of candidates) {
    try {
      let out;
      if (c.provider === "FRED") out = await fetchFred(c.id, c.opts || {});
      else if (c.provider === "Stooq") out = await fetchStooq(c.id, c.opts || {});
      else if (c.provider === "WorldBank") out = await fetchWorldBank(c.id, c.country || "USA", c.opts || {});
      else if (c.provider === "IMF") out = await fetchIMF(c.id, c.key, c.opts || {});
      else if (c.provider === "ECB") out = await fetchECB(c.id, c.key, c.opts || {});
      else if (c.provider === "CMO") {
        const { fetchCMO } = await import("./wb_cmo.mjs");
        out = await fetchCMO(c.id, c.opts || {});
      } else throw new Error(`Unknown provider ${c.provider}`);
      return { ...out, ...meta, series_id: c.id, requested: c };
    } catch (e) {
      errors.push(`${c.provider}:${c.id} -> ${e.message}`);
    }
  }
  // All failed — return an honest empty record.
  return {
    provider: null,
    source: "NO_USABLE_SOURCE",
    source_url: null,
    freq: meta.freq || "?",
    unit: meta.unit || "?",
    observations: [],
    updated: new Date().toISOString().slice(0, 10),
    insufficient_primary_data: true,
    errors,
    ...meta,
  };
}
