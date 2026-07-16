// src/lib/transforms.mjs
// Pure functions for time-series transformations. All operate on [{date,value}] arrays.
// No fake data: every function preserves provenance and only derives from real observations.

// --- Basic ---
export function byDate(rows) {
  return [...rows].filter((r) => r && r.value != null && Number.isFinite(r.value))
    .sort((a, b) => a.date.localeCompare(b.date));
}

export function filterRange(rows, startDate, endDate) {
  return byDate(rows).filter((r) => (!startDate || r.date >= startDate) && (!endDate || r.date <= endDate));
}

// Year-over-year percent change for index-level series (CPI, PCE, etc).
export function yoyPct(rows) {
  const d = byDate(rows);
  const out = [];
  for (const r of d) {
    const prev = sameMonthLastYear(d, r.date) || samePeriodLastYear(d, r.date);
    if (prev && prev.value) out.push({ date: r.date, value: ((r.value / prev.value) - 1) * 100 });
  }
  return out;
}

// Year-over-year ratio for index series: returns {date, value, prevDate}
export function yoyRatio(rows) {
  const d = byDate(rows);
  const out = [];
  for (const r of d) {
    const prev = sameMonthLastYear(d, r.date) || samePeriodLastYear(d, r.date);
    if (prev && prev.value) out.push({ date: r.date, value: r.value / prev.value, prevDate: prev.date });
  }
  return out;
}

// Find observation with date shifted exactly 12 months back (YYYY-MM-DD).
function sameMonthLastYear(rows, dateStr) {
  const m = dateStr.match(/^(\d{4})-(\d{2})/);
  if (!m) return null;
  const y = Number(m[1]) - 1, mo = m[2];
  return rows.find((r) => r.date === `${y}-${mo}-01`) || null;
}
// Fallback: take observation closest to 365 days before (for non-monthly).
function samePeriodLastYear(rows, dateStr) {
  const target = new Date(dateStr);
  target.setFullYear(target.getFullYear() - 1);
  const ts = target.getTime();
  let best = null, bestDiff = Infinity;
  for (const r of rows) {
    const diff = Math.abs(new Date(r.date).getTime() - ts);
    if (diff < bestDiff && diff < 40 * 86400000) { bestDiff = diff; best = r; }
  }
  return best;
}

// --- Real values: deflate a nominal series by CPI (both monthly, or resampled).
//   real_t = nominal_t / CPI_t * CPI_base
export function deflate(nominal, cpi, baseYear = 2024) {
  const c = byDate(cpi);
  const baseCpi = avgInYear(c, baseYear) || lastValue(c);
  if (!baseCpi) return [];
  return byDate(nominal).map((r) => {
    const cAt = c.find((x) => x.date === r.date) || nearestByMonth(c, r.date);
    if (!cAt || !cAt.value) return null;
    return { date: r.date, value: (r.value / cAt.value) * baseCpi };
  }).filter(Boolean);
}

function avgInYear(rows, year) {
  const yr = rows.filter((r) => r.date.startsWith(String(year)));
  if (!yr.length) return null;
  return yr.reduce((s, r) => s + r.value, 0) / yr.length;
}
function lastValue(rows) { return rows.length ? rows[rows.length - 1].value : null; }
function nearestByMonth(rows, dateStr) {
  const m = dateStr.match(/^(\d{4}-\d{2})/);
  if (!m) return null;
  return rows.find((r) => r.date.startsWith(m[1])) || null;
}

// --- Resample daily to monthly (last value of each month) ---
export function toMonthly(rows) {
  const seen = new Map();
  for (const r of byDate(rows)) {
    const k = r.date.slice(0, 7); // YYYY-MM
    seen.set(k, r.value); // last wins (rows sorted ascending)
  }
  return [...seen.entries()].map(([k, v]) => ({ date: `${k}-01`, value: v }));
}

// --- Resample daily to weekly (last value each Friday-ish) ---
export function toWeekly(rows) {
  const seen = new Map();
  for (const r of byDate(rows)) {
    const d = new Date(r.date);
    const day = d.getUTCDay();
    // shift to Friday
    const fri = new Date(d);
    fri.setUTCDate(d.getUTCDate() + ((5 - day + 7) % 7));
    const k = fri.toISOString().slice(0, 10);
    seen.set(k, r.value);
  }
  return [...seen.entries()].map(([k, v]) => ({ date: k, value: v })).sort((a, b) => a.date.localeCompare(b.date));
}

// --- Rolling mean over N observations ---
export function rollingMean(rows, window) {
  const d = byDate(rows);
  const out = [];
  for (let i = 0; i < d.length; i++) {
    if (i < window - 1) continue;
    let s = 0;
    for (let j = i - window + 1; j <= i; j++) s += d[j].value;
    out.push({ date: d[i].date, value: s / window });
  }
  return out;
}

// --- Equity–bond RETURN correlation (NOT yield-change correlation).
// Per P0 review: bond return ≠ yield change. Yield up → bond price DOWN.
// Approximation: bond_return ≈ -duration × Δy + carry (carry ≈ y/12 monthly).
// Uses 10Y Treasury as the duration proxy (D ≈ 8 years).
export function equityBondCorr(sp500Levels, yieldLevels, window = 36, duration = 8) {
  const a = byDate(sp500Levels), b = byDate(toMonthly(yieldLevels));
  const bm = new Map(b.map((r) => [r.date.slice(0, 7), r.value]));
  const joined = [];
  for (const r of a) {
    const bv = bm.get(r.date.slice(0, 7));
    if (bv != null) joined.push({ date: r.date, equity: r.value, yield: bv });
  }
  // Build monthly returns: equity = price return; bond = -D × Δy + carry
  const rets = [];
  for (let i = 1; i < joined.length; i++) {
    const prev = joined[i - 1], cur = joined[i];
    if (prev.equity && prev.yield != null && cur.equity && cur.yield != null) {
      const equityRet = cur.equity / prev.equity - 1;
      const dy = (cur.yield - prev.yield) / 100; // percentage point → decimal
      const carry = (prev.yield / 100) / 12;
      const bondRet = -duration * dy + carry;
      rets.push({ date: cur.date, equity: equityRet, bond: bondRet });
    }
  }
  return rollingCorrReturns(rets, window);
}
function rollingCorrReturns(rets, window) {
  const out = [];
  for (let i = window - 1; i < rets.length; i++) {
    const slice = rets.slice(i - window + 1, i + 1);
    const meanE = mean(slice.map((x) => x.equity));
    const meanB = mean(slice.map((x) => x.bond));
    let cov = 0, varE = 0, varB = 0;
    for (const x of slice) {
      cov += (x.equity - meanE) * (x.bond - meanB);
      varE += (x.equity - meanE) ** 2;
      varB += (x.bond - meanB) ** 2;
    }
    const denom = Math.sqrt(varE * varB);
    out.push({ date: rets[i].date, value: denom > 0 ? cov / denom : 0 });
  }
  return out;
}
// Legacy alias kept for any callers expecting old signature (now delegates to return-based).
export function rollingCorr(seriesA, seriesB, window) {
  return rollingCorrReturns(
    byDate(seriesA).map((r, i, arr) => {
      if (i === 0) return null;
      const prev = arr[i - 1];
      return { date: r.date, equity: r.value / prev.value - 1, bond: r.value / prev.value - 1 };
    }).filter(Boolean),
    window
  );
}
function mean(arr) { return arr.reduce((s, x) => s + x, 0) / arr.length; }

// --- Z-score vs full-sample (how many SD above/below mean) ---
export function zscore(rows) {
  const d = byDate(rows);
  if (!d.length) return [];
  const vals = d.map((r) => r.value);
  const m = mean(vals);
  const sd = Math.sqrt(mean(vals.map((v) => (v - m) ** 2))) || 1;
  return d.map((r) => ({ date: r.date, value: (r.value - m) / sd }));
}

// --- Percentile rank within sample ---
export function percentileRank(rows) {
  const d = byDate(rows);
  if (!d.length) return [];
  const vals = d.map((r) => r.value).sort((a, b) => a - b);
  return d.map((r) => {
    let below = 0;
    for (const v of vals) if (v < r.value) below++;
    return { date: r.date, value: (below / (vals.length - 1)) * 100 };
  });
}

// --- Rebase to 100 at a given date ---
export function rebase(rows, baseDate) {
  const d = byDate(rows);
  let base = d.find((r) => r.date === baseDate);
  if (!base) base = d[0];
  if (!base || !base.value) return [];
  const factor = 100 / base.value;
  return d.map((r) => ({ date: r.date, value: r.value * factor }));
}

// --- Maximum drawdown series ---
export function drawdown(rows) {
  const d = byDate(rows);
  let peak = -Infinity;
  return d.map((r) => {
    if (r.value > peak) peak = r.value;
    return { date: r.date, value: ((r.value / peak) - 1) * 100 };
  });
}

// --- Event-time alignment: rebase each series to T0=100 and index by month offset ---
export function eventTime(rows, eventDate, monthsBefore = 24, monthsAfter = 60) {
  const d = byDate(rows);
  const t0 = d.find((r) => r.date.startsWith(eventDate.slice(0, 7)));
  if (!t0) return [];
  const factor = 100 / t0.value;
  const out = [];
  const base = new Date(t0.date);
  for (const r of d) {
    const ms = (new Date(r.date).getTime() - base.getTime()) / (30.44 * 86400000);
    const m = Math.round(ms);
    if (m >= -monthsBefore && m <= monthsAfter) out.push({ t: m, value: r.value * factor });
  }
  return out;
}

// --- Stat helpers ---
export function statsAt(rows, year, month) {
  const m = `${year}-${String(month).padStart(2, "0")}`;
  const match = byDate(rows).filter((r) => r.date.startsWith(m));
  if (!match.length) return null;
  return { date: match[match.length - 1].date, value: match[match.length - 1].value, n: match.length };
}

export function valueAt(rows, dateStr) {
  const r = byDate(rows).find((x) => x.date.startsWith(dateStr.slice(0, 7)));
  return r ? r.value : null;
}
