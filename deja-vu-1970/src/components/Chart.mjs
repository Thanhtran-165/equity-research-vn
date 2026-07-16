// src/components/Chart.mjs (server component)
// Pure-SVG time-series chart. No deps. Renders at build as inline SVG — crisp, themeable.
// Props:
//   series: [{name, color, data:[{date, value}], dashed?:bool}]
//   height: number (default 320)
//   yLabel: string
//   source: string (citation)
//   sourceUrl: string
//   updated: string (date)
//   note: string
//   logY: bool
//   eventMarkers: [{date, label, side?: 'top'|'bottom'}]
//   yFormat: 'pct' | 'usd' | 'num' | 'ratio'
//   zeroLine: bool
//   shading: [{from, to, label, color?}]  (period bands)

function fmt(v, kind) {
  if (v == null || !Number.isFinite(v)) return "";
  if (kind === "pct") return v.toFixed(1) + "%";
  if (kind === "usd") return "$" + (Math.abs(v) >= 1000 ? v.toFixed(0) : v.toFixed(2));
  if (kind === "ratio") return v.toFixed(1);
  if (Math.abs(v) >= 1000) return v.toLocaleString("en-US", { maximumFractionDigits: 0 });
  if (Math.abs(v) >= 10) return v.toFixed(1);
  return v.toFixed(2);
}

// Pick the right language string from a value that may be {vi, en} or plain string.
function pick(v, lang) {
  if (v == null) return "";
  if (typeof v === "string") return v;
  return v[lang] || v.vi || v.en || "";
}

export function Chart({
  title, subtitle,
  series = [],
  height = 320,
  yLabel = "",
  source = "", sourceUrl = "", updated = "", note = "",
  logY = false, yFormat = "num", zeroLine = false,
  eventMarkers = [], shading = [],
  lang = "vi",
}) {
  title = pick(title, lang);
  subtitle = pick(subtitle, lang);
  yLabel = pick(yLabel, lang);
  note = pick(note, lang);
  if (source && typeof source === "object") source = pick(source, lang);
  series = series.map((s) => ({ ...s, name: pick(s.name, lang) }));
  eventMarkers = eventMarkers.map((m) => ({ ...m, label: pick(m.label, lang) }));
  shading = shading.map((s) => ({ ...s, label: pick(s.label, lang) }));
  const W = 760, H = height;
  const M = { top: 16, right: 16, bottom: 28, left: 56 };
  const plotW = W - M.left - M.right;
  const plotH = H - M.top - M.bottom;

  // X scale: time across all data
  let allPts = [];
  for (const s of series) for (const p of s.data) if (p.value != null) allPts.push({ date: p.date, value: p.value });
  if (!allPts.length) {
    return `<div class="chart"><div class="chart-title">${title || ""}</div><div class="chart-subtitle">No data available — insufficient primary source.</div></div>`;
  }
  const xMin = allPts[0].date, xMax = allPts[allPts.length - 1].date;
  const xMinMs = new Date(xMin).getTime(), xMaxMs = new Date(xMax).getTime();
  const xScale = (d) => M.left + ((new Date(d).getTime() - xMinMs) / (xMaxMs - xMinMs || 1)) * plotW;

  // Y scale
  let vals = allPts.map((p) => p.value);
  let yMin = Math.min(...vals), yMax = Math.max(...vals);
  if (zeroLine) yMin = Math.min(yMin, 0);
  if (yMax === yMin) { yMax = yMin + 1; }
  const pad = (yMax - yMin) * 0.08;
  yMin -= pad; yMax += pad;
  if (logY) { yMin = Math.max(yMin, 1e-9); }
  const yScale = (v) => {
    if (logY) {
      const lo = Math.log10(yMin), hi = Math.log10(yMax);
      return M.top + plotH - ((Math.log10(Math.max(v, 1e-9)) - lo) / (hi - lo || 1)) * plotH;
    }
    return M.top + plotH - ((v - yMin) / (yMax - yMin || 1)) * plotH;
  };

  // Y ticks (5)
  const yTicks = [];
  for (let i = 0; i <= 5; i++) {
    let v;
    if (logY) { v = Math.pow(10, Math.log10(yMin) + (i / 5) * (Math.log10(yMax) - Math.log10(yMin))); }
    else { v = yMin + (i / 5) * (yMax - yMin); }
    yTicks.push({ v, y: yScale(v) });
  }

  // X ticks: pick ~6 year labels
  const xYearMin = new Date(xMin).getUTCFullYear(), xYearMax = new Date(xMax).getUTCFullYear();
  const span = xYearMax - xYearMin;
  const step = span <= 5 ? 1 : span <= 15 ? 2 : span <= 30 ? 5 : 10;
  const xTicks = [];
  for (let y = Math.ceil(xYearMin / step) * step; y <= xYearMax; y += step) {
    const d = `${y}-01-01`;
    xTicks.push({ d, x: xScale(d), label: String(y) });
  }

  // Build paths
  const paths = series.map((s, i) => {
    const colorVar = `var(--chart-line${series.length > 1 ? "-" + (i + 1) : ""})`;
    const pts = s.data.filter((p) => p.value != null)
      .map((p) => `${xScale(p.date).toFixed(1)},${yScale(p.value).toFixed(1)}`);
    const linePath = `M ${pts.join(" L ")}`;
    const areaPath = pts.length ? `M ${pts[0]} L ${pts.join(" L ")} L ${pts[pts.length - 1].split(",")[0]},${(M.top + plotH).toFixed(1)} L ${pts[0].split(",")[0]},${(M.top + plotH).toFixed(1)} Z` : "";
    return { linePath, areaPath, color: s.color || colorVar, name: s.name, dashed: s.dashed };
  });

  // Render
  const legend = series.length > 1
    ? `<div style="display:flex;gap:14px;flex-wrap:wrap;font-size:12px;margin-bottom:6px">${series.map((s, i) => `<span style="display:inline-flex;align-items:center;gap:5px"><svg width="14" height="10"><line x1="0" y1="5" x2="14" y2="5" stroke="var(--chart-line${i === 0 ? "" : "-" + (i + 1)})" stroke-width="2.5" ${s.dashed ? 'stroke-dasharray="3 2"' : ""}/></svg>${s.name}</span>`).join("")}</div>`
    : "";

  return `<div class="chart">
    ${title ? `<div class="chart-title">${title}</div>` : ""}
    ${subtitle ? `<div class="chart-subtitle">${subtitle}</div>` : ""}
    ${legend}
    <svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto;display:block" preserveAspectRatio="xMidYMid meet" role="img" aria-label="${title || "chart"}">
      <defs>
        ${paths.map((p, i) => `<linearGradient id="g${i}" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stop-color="${p.color}" stop-opacity="0.18"/><stop offset="100%" stop-color="${p.color}" stop-opacity="0"/></linearGradient>`).join("")}
      </defs>
      <!-- shading bands -->
      ${shading.map((sh) => {
        const x1 = xScale(sh.from), x2 = xScale(sh.to);
        return `<rect x="${x1.toFixed(1)}" y="${M.top}" width="${(x2 - x1).toFixed(1)}" height="${plotH}" fill="${sh.color || "var(--grid)"}" opacity="0.6"/><text x="${((x1 + x2) / 2).toFixed(1)}" y="${M.top + 12}" text-anchor="middle" font-size="10" fill="var(--fg-muted)">${sh.label || ""}</text>`;
      }).join("")}
      <!-- grid + y ticks -->
      ${yTicks.map((t) => `<line x1="${M.left}" y1="${t.y.toFixed(1)}" x2="${W - M.right}" y2="${t.y.toFixed(1)}" stroke="var(--grid)" stroke-width="1"/><text x="${M.left - 8}" y="${(t.y + 3).toFixed(1)}" text-anchor="end" font-size="11" fill="var(--fg-muted)">${fmt(t.v, yFormat)}</text>`).join("")}
      <!-- zero line -->
      ${zeroLine && yMin < 0 && yMax > 0 ? `<line x1="${M.left}" y1="${yScale(0).toFixed(1)}" x2="${W - M.right}" y2="${yScale(0).toFixed(1)}" stroke="var(--fg-muted)" stroke-width="1" stroke-dasharray="4 3"/>` : ""}
      <!-- x ticks -->
      ${xTicks.map((t) => `<line x1="${t.x.toFixed(1)}" y1="${M.top + plotH}" x2="${t.x.toFixed(1)}" y2="${M.top + plotH + 4}" stroke="var(--fg-muted)"/><text x="${t.x.toFixed(1)}" y="${(M.top + plotH + 18).toFixed(1)}" text-anchor="middle" font-size="11" fill="var(--fg-muted)">${t.label}</text>`).join("")}
      <!-- axis labels -->
      ${yLabel ? `<text x="${M.left - 44}" y="${M.top + plotH / 2}" text-anchor="middle" font-size="11" fill="var(--fg-muted)" transform="rotate(-90 ${M.left - 44} ${M.top + plotH / 2})">${yLabel}</text>` : ""}
      <!-- area fills -->
      ${paths.map((p, i) => p.areaPath && !p.dashed ? `<path d="${p.areaPath}" fill="url(#g${i})"/>` : "").join("")}
      <!-- lines -->
      ${paths.map((p) => `<path d="${p.linePath}" fill="none" stroke="${p.color}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round" ${p.dashed ? 'stroke-dasharray="4 3"' : ""}/>`).join("")}
      <!-- event markers -->
      ${eventMarkers.map((m) => {
        const x = xScale(m.date);
        if (x < M.left || x > W - M.right) return "";
        const y = m.side === "bottom" ? M.top + plotH - 8 : M.top + 8;
        return `<line x1="${x.toFixed(1)}" y1="${M.top}" x2="${x.toFixed(1)}" y2="${(M.top + plotH).toFixed(1)}" stroke="var(--chart-line-4)" stroke-width="1" stroke-dasharray="2 3" opacity="0.5"/><circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3" fill="var(--chart-line-4)"/><text x="${(x + 5).toFixed(1)}" y="${(y + 3).toFixed(1)}" font-size="10" fill="var(--fg-muted)">${m.label}</text>`;
      }).join("")}
    </svg>
    <div class="chart-caption">
      <span class="src">Source: ${sourceUrl ? `<a href="${sourceUrl}" target="_blank" rel="noopener">${source}</a>` : source || "—"}</span>
      ${updated ? `<span>Updated: ${updated}</span>` : ""}
    </div>
    ${note ? `<div class="chart-caption" style="font-style:italic">${note}</div>` : ""}
  </div>`;
}
