#!/usr/bin/env node
// scripts/fetch_data.mjs
// Fetches all series from the registry into static JSON under src/data/cache/.
// Reads FRED_API_KEY from .env.local if present (so `npm run fetch-data` works locally).
// For Vercel build: FRED_API_KEY must be set as a Vercel env var OR data must be
// pre-fetched & committed before deploy. We commit the cache for a static, reproducible build.

import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { REGISTRY } from "../src/data/registry.mjs";
import { resolveSeries } from "../src/lib/providers.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");

// --- Load .env.local manually (Node 22, no dotenv dep) ---
function loadEnv() {
  for (const f of [".env.local", ".env"]) {
    const p = resolve(ROOT, f);
    if (!existsSync(p)) continue;
    const txt = readFileSync(p, "utf8");
    for (const line of txt.split("\n")) {
      const m = line.match(/^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)\s*$/);
      if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
    }
  }
}
loadEnv();

const CACHE_DIR = resolve(ROOT, "src/data/cache");
mkdirSync(CACHE_DIR, { recursive: true });

// --- Main fetch loop ---
async function main() {
  const hasFredKey = !!process.env.FRED_API_KEY;
  console.log(`\n=== Déjà Vu data fetch ===`);
  console.log(`FRED_API_KEY: ${hasFredKey ? "SET" : "NOT SET (will try no-key fallbacks)"}`);
  console.log(`Series to fetch: ${REGISTRY.length}\n`);

  let ok = 0, partial = 0, failed = 0;
  const manifest = [];

  for (const entry of REGISTRY) {
    if (entry.derived && entry.key === "cape") {
      try {
        const { fetchShillerCAPE } = await import("../src/lib/shiller.mjs");
        const out = await fetchShillerCAPE();
        writeFileSync(resolve(CACHE_DIR, `${entry.key}.json`), JSON.stringify({ ...out, key: entry.key, label: entry.label, unit: entry.unit, freq: entry.freq }, null, 2));
        console.log(`  [OK     ] ${entry.key.padEnd(22)} Shiller      ${out.observations.length} obs`);
        manifest.push({ key: entry.key, label: entry.label, provider: "Shiller", n: out.observations.length, file: `${entry.key}.json`, source: out.source, source_url: out.source_url });
      } catch (e) {
        console.log(`  [INSUFF ] ${entry.key.padEnd(22)} ${e.message}`);
        manifest.push({ key: entry.key, label: entry.label, provider: null, n: 0, insufficient_primary_data: true, errors: [e.message] });
      }
      continue;
    }
    if (entry.derived) {
      console.log(`  [SKIP-DERIVED] ${entry.key.padEnd(22)} (computed at render time)`);
      manifest.push({ key: entry.key, derived: true, label: entry.label });
      continue;
    }
    const out = await resolveSeries(entry.series, {
      key: entry.key,
      label: entry.label,
      unit: entry.unit,
      freq: entry.freq,
    });
    const n = out.observations ? out.observations.length : 0;
    const insuff = !!out.insufficient_primary_data;
    if (n > 0) {
      ok++;
      const file = resolve(CACHE_DIR, `${entry.key}.json`);
      writeFileSync(file, JSON.stringify(out, null, 2));
      console.log(`  [OK     ] ${entry.key.padEnd(22)} ${out.provider.padEnd(12)} ${n} obs`);
      manifest.push({ key: entry.key, label: entry.label, provider: out.provider, n, file: `${entry.key}.json`, source: out.source, source_url: out.source_url });
    } else {
      failed++;
      const file = resolve(CACHE_DIR, `${entry.key}.json`);
      writeFileSync(file, JSON.stringify(out, null, 2)); // keep honest empty record too
      console.log(`  [INSUFF ] ${entry.key.padEnd(22)} ${out.errors ? out.errors.join(" | ") : ""}`);
      manifest.push({ key: entry.key, label: entry.label, provider: null, n: 0, file: `${entry.key}.json`, insufficient_primary_data: true, errors: out.errors });
    }
  }

  // Write manifest
  const fetchedAt = new Date().toISOString();
  writeFileSync(resolve(CACHE_DIR, "_manifest.json"), JSON.stringify({ fetched_at: fetchedAt, has_fred_key: hasFredKey, ok, failed, total: REGISTRY.length, series: manifest }, null, 2));

  console.log(`\n=== Summary ===`);
  console.log(`OK: ${ok}  |  Insufficient: ${failed}  |  Total: ${REGISTRY.length}`);
  console.log(`Manifest: src/data/cache/_manifest.json`);
  console.log(`Fetched at: ${fetchedAt}\n`);
}

main().catch((e) => { console.error("FATAL:", e); process.exit(1); });
