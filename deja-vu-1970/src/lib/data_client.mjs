// src/lib/data_client.mjs
// Client-safe data loader — uses fetch() to load JSON from committed static cache.
// Server version (data_loader.mjs) uses fs and is for build-time only.

const BASE = ""; // relative to site root

export async function getSeriesAsync(key) {
  try {
    const r = await fetch(`${BASE}/data/${key}.json`);
    if (!r.ok) return null;
    return await r.json();
  } catch { return null; }
}

export async function getManifestAsync() {
  try {
    const r = await fetch(`${BASE}/data/_manifest.json`);
    if (!r.ok) return null;
    return await r.json();
  } catch { return null; }
}
