// src/lib/shiller.mjs
// Robert Shiller online data (http://www.econ.yale.edu/~shiller/data/ie_data.xls)
// Primary source for CAPE, S&P 500 price/earnings, CPI, long-term rate since 1871.
// Returns the same shape as other providers.

import { execFileSync } from "node:child_process";
import { writeFileSync, readFileSync, existsSync } from "node:fs";

const URL = "http://www.econ.yale.edu/~shiller/data/ie_data.xls";

async function ensureDownloaded() {
  const tmp = "/tmp/shiller.xls";
  if (!existsSync(tmp)) {
    const r = await fetch(URL, { headers: { "User-Agent": "DejaVuResearch/1.0" } });
    if (!r.ok) throw new Error(`Shiller HTTP ${r.status}`);
    writeFileSync(tmp, Buffer.from(await r.arrayBuffer()));
  }
  return tmp;
}

export async function fetchShillerCAPE(opts = {}) {
  await ensureDownloaded();
  const out = execFileSync("python3", ["-c", `
import pandas as pd, json
df = pd.read_excel("/tmp/shiller.xls", sheet_name="Data", skiprows=7)
obs = []
for _, r in df.iterrows():
    d = r.get("Date")
    cape = r.get("CAPE") if "CAPE" in df.columns else r.get("CAPE.1")
    tr_cape = r.get("TR CAPE") if "TR CAPE" in df.columns else None
    if pd.isna(d) or pd.isna(cape): continue
    try:
        y = int(float(d))
        frac = float(d) - y
        m = int(round(frac * 12)) + 1
        if m > 12: y, m = y + 1, 1
        date = f"{y:04d}-{m:02d}-01"
    except: continue
    obs.append({"date": date, "value": float(cape), "tr_cape": float(tr_cape) if pd.notna(tr_cape) else None})
print(json.dumps(obs))
`]).toString();
  const observations = JSON.parse(out.trim().split("\n").pop());
  return {
    provider: "Shiller (Yale) Online Data",
    source: "Robert J. Shiller, Irrational Exuberance [Online Data] — CAPE",
    source_url: "http://www.econ.yale.edu/~shiller/data.htm",
    freq: "monthly",
    unit: "ratio (P / 10yr avg real earnings)",
    observations: observations.map((o) => ({ date: o.date, value: o.value, tr_cape: o.tr_cape })),
    updated: new Date().toISOString().slice(0, 10),
    note: "CAPE = real S&P 500 price divided by 10-year trailing average real earnings. Shiller, Yale.",
  };
}
