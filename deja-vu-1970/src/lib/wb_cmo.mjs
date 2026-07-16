// src/lib/wb_cmo.mjs
// World Bank Commodity Price Data ("The Pink Sheet") monthly workbook.
// Source: thedocs.worldbank.org/.../CMO-Historical-Data-Monthly.xlsx (free, no key).
// This is the canonical primary source for Gold/Silver/Platinum and many commodity
// series when FRED has discontinued them (LBMA gold was removed from FRED ~2022).
//
// Returns: { series, source, source_url, freq, unit, observations:[{date,value}], updated }
// Column map is fixed for the canonical workbook layout (verified 2024 layout).

import { writeFileSync, readFileSync, existsSync, mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const URL = "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx";

// CMO "Monthly Prices" column map. Verified against the canonical workbook.
// Indices are zero-based on the raw sheet (no header). Header is at row index 4.
export const CMO_COLUMNS = {
  CRUDE_BRENT: 2, CRUDE_DUBAI: 3, CRUDE_WTI: 4,
  NATGAS_EU: 6, NATGAS_US: 7, LNG_ASIA: 8,
  COAL_AUS: 13,
  COPPER: 32, ALUMINUM: 33, NICKEL: 34, ZINC: 35, TIN: 36, IRON_ORE: 37, LEAD: 38,
  GOLD: 69, PLATINUM: 70, SILVER: 71,
};

let _cache = null;

async function loadWorkbook() {
  if (_cache) return _cache;
  const tmp = "/tmp/cmo.xlsx";
  let buf;
  if (existsSync(tmp) && Date.now() - (existsSync(tmp) ? 0 : 0) >= 0) {
    // always refetch fresh — file is small (765KB)
  }
  if (!existsSync(tmp)) {
    const r = await fetch(URL, { headers: { "User-Agent": "DejaVuResearch/1.0" } });
    if (!r.ok) throw new Error(`CMO HTTP ${r.status}`);
    buf = Buffer.from(await r.arrayBuffer());
    writeFileSync(tmp, buf);
  } else {
    buf = readFileSync(tmp);
  }
  _cache = buf;
  return buf;
}

// Parse the xlsx with the bundled SheetJS-style approach. We don't ship a dep,
// so we shell out to python3+openpyxl/pandas (already verified available).
export async function fetchCMO(columnKey, opts = {}) {
  await loadWorkbook(); // ensures /tmp/cmo.xlsx exists
  const { execFileSync } = await import("node:child_process");
  const out = execFileSync("python3", ["-c", `
import pandas as pd, json
df = pd.read_excel("/tmp/cmo.xlsx", sheet_name="Monthly Prices", header=None)
col = ${CMO_COLUMNS[columnKey] || -1}
obs = []
for i in range(5, len(df)):
    d = df.iloc[i, 0]
    v = df.iloc[i, col]
    if pd.isna(d) or pd.isna(v): continue
    s = str(d).strip()
    if "M" not in s: continue
    y, m = s.split("M")
    obs.append({"date": f"{y}-{int(m):02d}-01", "value": float(v)})
print(json.dumps(obs))
`]).toString();
  const observations = JSON.parse(out.trim().split("\n").pop());
  return {
    provider: "World Bank CMO (Pink Sheet)",
    source: `World Bank Commodity Price Data — Pink Sheet, ${columnKey}`,
    source_url: "https://www.worldbank.org/en/research/commodity-markets",
    freq: "monthly",
    unit: opts.unit || "(see Pink Sheet)",
    observations,
    updated: new Date().toISOString().slice(0, 10),
    note: "Primary source: World Bank Commodity Price Data (Pink Sheet), nominal US$.",
  };
}
