#!/usr/bin/env python3
"""
deterministic_renderer.py — Deterministic HTML renderer for equity research dashboard.

Architecture Phase B component #3 (renderer contract, see
architecture/migration-plan.yaml).

This renderer takes a validated report IR (JSON) and produces a complete HTML
dashboard WITHOUT any model involvement. The model only produces per-section
narrative text; this module emits:

  * the full HTML document (DOCTYPE, <head>, <body>, sidebar nav)
  * 20 section containers, each with a `{{NARRATIVE:section_id}}` placeholder
    (or a "Không áp dụng" notice when the section is NOT_APPLICABLE)
  * the `const DATA = {...}` block, derived from IR `financial_data`
    (null + `revenueStatus` + `revenueApplicabilityRule` handling for
    NOT_APPLICABLE fields such as INSURANCE_REVENUE_NOT_GENERIC_SALES)
  * Chart.js v4 chart JavaScript, one `new Chart(...)` per applicable chart,
    each canvas wrapped in `<div class="chart-wrap"><canvas id="..."></canvas></div>`
    (NOT_APPLICABLE charts are skipped)
  * Source footnotes built from `metadata`
  * Minimal CSS (`.chart-wrap { max-height: 250px }`, `.card` styling)

Design rules (per ADR / migration-plan.yaml):

  * NEVER depend on model output for HTML structure, DATA, charts, or JS.
  * Use string templates (str.format / % ) rather than f-strings for the large
    HTML/JS blocks, so dynamic content is inserted via narrow, named slots.
  * HTML-escape all narrative text (via html.escape).
  * Produce valid HTML: balanced divs, proper closing tags.
  * Numeric DATA values are serialized via json.dumps — only data is dynamic.

Public API:
  * render_html(ir: dict) -> str           — returns HTML string
  * render_to_file(ir: dict, output_path: str) -> str
                                            — writes HTML to disk, returns path
"""
from __future__ import annotations

import html
import json
import os
from typing import Any, Iterable, Mapping

__all__ = ["render_html", "render_to_file"]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CHART_JS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4"
SCHEMA_VERSION = "1.0.0-arch-b"

# Ordered list of section ids that should always be emitted in this order.
# This matches the IR `sections[].section_id` enum from report-ir.schema.json.
DEFAULT_SECTION_ORDER: tuple[str, ...] = (
    "executive_summary", "company_profile", "industry_overview",
    "history", "segment", "thesis", "valuation", "peers",
    "balance_sheet", "risk", "scenario", "checklist",
    "insight_1", "insight_2", "insight_3",
    "tech_active", "tech_profile", "analyst_notes",
    "glossary", "sources",
)

# Map canonical_field -> JavaScript DATA key (snake_case preserved).
# IR stores metrics keyed by canonical_field; the legacy template reads
# `DATA.revenue`, `DATA.netProfit`, etc. We keep both forms available so the
# generated DATA block is drop-in compatible with the existing template's
# Chart.js code.
_FIELD_TO_JS_KEY: dict[str, str] = {
    "revenue": "revenue",
    "net_profit": "netProfit",
    "total_revenue": "revenue",
    "eps": "eps",
    "total_assets": "totalAssets",
    "total_equity": "equity",
    "equity": "equity",
    "capex": "capex",
    "net_income": "netIncome",
    "gross_profit": "grossProfit",
    "operating_profit": "operatingProfit",
}

# Status values that should be emitted with `null` array + status flag.
_NOT_APPLICABLE_STATUSES = {"NOT_APPLICABLE"}
# Statuses that still emit an array of values (VALID, REPORTED_ZERO, etc.).
_VALID_LIKE_STATUSES = {
    "VALID", "REPORTED_ZERO", "SUSPECT_ZERO_OR_MISSING",
    "SOURCE_CONFLICT", "NOT_REPORTED",
}

# ---------------------------------------------------------------------------
# Document templates (string-based; only narrow named slots are dynamic)
# ---------------------------------------------------------------------------

# Minimal CSS for the deterministic shell. Inline so the produced HTML is
# self-contained; a real stylesheet can be linked via <link> later.
_CSS = """\
:root{--bg:#0f1419;--card:#161b22;--txt:#e6edf3;--muted:#8b949e;--accent:#4a9eff}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--txt);line-height:1.5}
.layout{display:flex;min-height:100vh}
nav.sidebar{width:230px;background:#0b0f14;border-right:1px solid #21262d;padding:14px 0;position:sticky;top:0;height:100vh;overflow:auto}
nav.sidebar a{display:block;color:var(--muted);text-decoration:none;padding:8px 18px;font-size:13px;border-left:3px solid transparent}
nav.sidebar a:hover{color:var(--txt);background:#161b22}
nav.sidebar a.active{color:var(--accent);border-left-color:var(--accent)}
main{flex:1;padding:20px 28px;max-width:1200px}
h1{font-size:22px;margin:0 0 4px}
.subtitle{color:var(--muted);font-size:12px;margin-bottom:18px}
.card{background:var(--card);border:1px solid #21262d;border-radius:8px;padding:16px 18px;margin-bottom:18px}
.card h2{font-size:15px;margin:0 0 10px;color:var(--accent)}
.narrative-slot{font-size:14px;color:var(--txt);min-height:1em}
.narrative-slot:empty::before{content:"{{NARRATIVE_PLACEHOLDER}}";color:var(--muted);font-style:italic}
.not-applicable{color:var(--muted);font-style:italic;background:#1d232b;border:1px dashed #30363d;border-radius:6px;padding:10px 12px}
.chart-wrap{max-height:250px;position:relative;margin-top:10px}
.chart-wrap canvas{max-height:250px}
.footnotes{margin-top:30px;border-top:1px solid #21262d;padding-top:14px;color:var(--muted);font-size:11px}
.footnotes h2{color:var(--txt);font-size:13px;margin:0 0 8px}
"""

# HTML head + open of body + sidebar shell. {title}, {css}, {chart_js_cdn},
# {ticker}, {company}, {nav_items}, {main_open}, {sections}, {footnotes},
# {main_close}, {data_block}, {chart_js} are filled in by render_html().
_HTML_DOC = """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
{css}
  </style>
  <script src="{chart_js_cdn}"></script>
</head>
<body>
  <div class="layout">
    <nav class="sidebar">
      <div style="padding:4px 18px 14px;border-bottom:1px solid #21262d;margin-bottom:8px">
        <strong>{ticker}</strong>
        <div class="subtitle" style="margin:0">{company}</div>
      </div>
{nav_items}
    </nav>
    <main>
      <h1>{company} <span style="color:var(--muted);font-weight:400;font-size:14px">({ticker})</span></h1>
      <div class="subtitle">Equity research dashboard &middot; schema {schema_version}</div>
{sections}
{footnotes}
    </main>
  </div>
  <script>
{data_block}
{chart_js}
  </script>
</body>
</html>
"""

# Template for each APPLICABLE section. NARRATIVE_TOKEN is replaced with the
# literal `{{NARRATIVE:<section_id>}}` placeholder AFTER str.format (because
# `.format()` would otherwise interpret `{{...}}` as escaped braces).
_SECTION_TEMPLATE = """      <section id="sec-{sec_id}" class="card" style="scroll-margin-top:60px">
        <h2>{title}</h2>
        <div class="narrative-slot">NARRATIVE_TOKEN</div>
        {chart_html}</section>
"""

# Template for NOT_APPLICABLE sections (no narrative placeholder).
_SECTION_NOT_APPLICABLE = """      <section id="sec-{sec_id}" class="card" style="scroll-margin-top:60px">
        <h2>{title}</h2>
        <div class="not-applicable">Không áp dụng</div>
      </section>
"""

# Single chart wrapper. The canvas id matches the chart_id from IR.
_CHART_WRAPPER = '<div class="chart-wrap"><canvas id="{chart_id}"></canvas></div>'

# Per-chart JS. Uses `if ($('chartId'))` guard like the legacy template so a
# missing canvas never throws. `chart_options` is JSON-serialized Chart.js
# options block (type/data/options). DATA refs are inserted as identifiers
# (not stringified) so they resolve at runtime from `const DATA`.
_CHART_JS = """if ($('{chart_id}')) new Chart($('{chart_id}'), {chart_options});"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_ir(ir_or_path: Any) -> dict:
    """Accept either an IR dict or a path to a JSON file containing one."""
    if isinstance(ir_or_path, Mapping):
        return dict(ir_or_path)
    if isinstance(ir_or_path, (str, os.PathLike)):
        with open(ir_or_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    raise TypeError(
        f"ir must be a dict or path-like, got {type(ir_or_path).__name__}"
    )


def _escape(text: Any) -> str:
    """HTML-escape arbitrary text, coercing non-strings to str first."""
    return html.escape(str(text) if text is not None else "", quote=True)


def _sections_by_id(ir: dict) -> dict[str, dict]:
    """Return {section_id: section_dict} from the IR."""
    out: dict[str, dict] = {}
    for sec in ir.get("sections", []) or []:
        sid = sec.get("section_id")
        if sid:
            out[sid] = sec
    return out


def _ordered_sections(ir: dict) -> list[dict]:
    """Return sections in canonical order; unknown section_ids appended last."""
    by_id = _sections_by_id(ir)
    ordered: list[dict] = []
    seen: set[str] = set()
    for sid in DEFAULT_SECTION_ORDER:
        sec = by_id.get(sid)
        if sec is not None:
            ordered.append(sec)
            seen.add(sid)
    # Append any IR-declared sections not in our canonical order.
    for sec in ir.get("sections", []) or []:
        sid = sec.get("section_id")
        if sid and sid not in seen:
            ordered.append(sec)
            seen.add(sid)
    return ordered


def _metric_status(metric: Mapping[str, Any]) -> str:
    """Return the canonical status of a metric (default VALID)."""
    status = metric.get("status")
    if isinstance(status, str) and status:
        return status
    return "VALID"


def _years(ir: dict) -> list[str]:
    """Return years as zero-padded 4-char strings, e.g. ['2021','2022',...]."""
    scope = ir.get("reporting_scope", {}) or {}
    years_raw = scope.get("annual_periods") or []
    if not years_raw:
        # Fallback: derive from financial_data metric values.
        metrics = (ir.get("financial_data", {}) or {}).get("metrics", {}) or {}
        any_metric = next(iter(metrics.values()), None) if metrics else None
        if any_metric:
            years_raw = sorted(any_metric.get("values", {}).keys())
    return [str(int(y)) if isinstance(y, (int, float)) else str(y) for y in years_raw]


def _series_for_metric(metric: Mapping[str, Any], years: list[str]) -> list[Any]:
    """Return a values list aligned to `years` for the given metric dict.

    For NOT_APPLICABLE metrics the IR may still carry a values dict; we return
    nulls in that case (caller emits status flag separately).
    """
    if _metric_status(metric) in _NOT_APPLICABLE_STATUSES:
        return [None] * len(years)
    values = metric.get("values", {}) or {}
    out: list[Any] = []
    for y in years:
        v = values.get(y)
        if v is None:
            v = values.get(int(y) if y.isdigit() else y)
        out.append(v)
    return out


def _js_identifier_for_field(canon_field: str) -> str:
    """Pick a JS DATA key for a canonical field."""
    if canon_field in _FIELD_TO_JS_KEY:
        return _FIELD_TO_JS_KEY[canon_field]
    # Fall back: camelCase of the canonical field.
    parts = canon_field.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


# ---------------------------------------------------------------------------
# DATA block generation
# ---------------------------------------------------------------------------

def _build_data_object(ir: dict) -> dict:
    """Build the DATA object (Python dict) that will be json.dump'd as JS.

    Layout (compatible with the legacy dashboard template):
        {
          "ticker": "FPT",
          "company": "FPT Corporation",
          "years": ["2021", ...],
          "revenue": [123, 456, ...],
          "revenueStatus": "VALID",
          "revenueApplicabilityRule": null,
          "netProfit": [...],
          "netProfitStatus": "VALID",
          ...
        }

    For NOT_APPLICABLE metrics (e.g. revenue for an insurer):
        "revenue": null,
        "revenueStatus": "NOT_APPLICABLE",
        "revenueApplicabilityRule": "INSURANCE_REVENUE_NOT_GENERIC_SALES"
    """
    years = _years(ir)
    data: dict[str, Any] = {
        "ticker": ir.get("metadata", {}).get("ticker", ""),
        "company": ir.get("metadata", {}).get("company_name", ""),
        "years": years,
    }

    metrics = (ir.get("financial_data", {}) or {}).get("metrics", {}) or {}
    for canon_field, metric in metrics.items():
        if not isinstance(metric, Mapping):
            continue
        js_key = _js_identifier_for_field(canon_field)
        status = _metric_status(metric)
        rule = metric.get("applicability_rule")

        if status in _NOT_APPLICABLE_STATUSES:
            data[js_key] = None
        else:
            data[js_key] = _series_for_metric(metric, years)
        # Always emit a status field (and rule when present) so the front-end
        # can branch without re-parsing.
        data[f"{js_key}Status"] = status
        data[f"{js_key}ApplicabilityRule"] = rule

    # Derived metrics: valuation + scores.
    derived = ir.get("derived_metrics", {}) or {}
    valuation = derived.get("valuation", {}) or {}
    if valuation:
        data["pe"] = valuation.get("pe")
        data["pb"] = valuation.get("pb")
        data["graham"] = valuation.get("graham")
        if "pe_hist" in valuation:
            data["peHist"] = valuation.get("pe_hist")
        if "pb_hist" in valuation:
            data["pbHist"] = valuation.get("pb_hist")

    scores = derived.get("scores", {}) or {}
    if scores:
        data["techScore"] = scores.get("tech_score")
        data["techVerdict"] = scores.get("tech_verdict")

    return data


def _render_data_block(data_obj: dict) -> str:
    """Render `const DATA = {...};` as JS, preserving `null`/numbers/etc.

    Uses json.dumps with indent=2 for readability; the result is valid JS
    because JSON is a strict subset of JavaScript for our value domain
    (strings, numbers, booleans, null, arrays, plain objects).
    """
    body = json.dumps(data_obj, indent=2, ensure_ascii=False, default=str)
    return "const DATA = {body};".format(body=body)


# ---------------------------------------------------------------------------
# Chart generation
# ---------------------------------------------------------------------------

def _js_string(s: Any) -> str:
    """Serialize `s` as a JS string literal (JSON-quoted)."""
    return json.dumps("" if s is None else str(s), ensure_ascii=False)


def _chart_options_payload(chart: Mapping[str, Any], data_obj: dict) -> str:
    """Build the {type,data,options} payload string for one Chart.js chart.

    The payload is hand-built (not via json.dumps round-trip) so that DATA
    references like ``data: DATA.revenue`` and ``labels: DATA.years`` are
    emitted as live JS identifiers rather than stringified JSON. Scalar
    values (title text, option booleans) are still JSON-escaped via
    ``_js_string`` so any unicode or quotes in them cannot break the JS.

    For charts backed by a single metric, dataset.data is the literal
    ``DATA.<jsKey>`` reference. For multi-metric charts, each dataset
    references its own DATA.<jsKey>.
    """
    chart_type = chart.get("chart_type", "bar")
    source_metrics = list(chart.get("source_metrics", []) or [])
    title = chart.get("title", "") or ""
    multi = len(source_metrics) > 1
    is_pie_like = chart_type in ("doughnut", "pie")

    # --- datasets ---
    ds_lines: list[str] = []
    for canon_field in source_metrics:
        js_key = _js_identifier_for_field(canon_field)
        ref = "DATA.{k}".format(k=js_key)
        label = _js_string(canon_field)
        if is_pie_like:
            ds_lines.append(
                "      {{ label: {label}, data: {ref} }}".format(label=label, ref=ref)
            )
        else:
            ds_lines.append(
                "      {{ label: {label}, data: {ref}, borderRadius: 4 }}".format(
                    label=label, ref=ref
                )
            )
    datasets_block = ",\n".join(ds_lines) if ds_lines else "      /* no datasets */"

    # --- options ---
    title_display = "true" if title else "false"
    legend_display = "true" if multi else "false"
    title_js = _js_string(title)
    if is_pie_like:
        scales_block = "      /* pie/doughnut: no cartesian scales */"
    else:
        scales_block = (
            "      x: {{}},\n"
            "      y: {{ beginAtZero: true }}"
        ).format()

    payload = (
        "{{\n"
        "  type: {chart_type},\n"
        "  data: {{\n"
        "    labels: DATA.years,\n"
        "    datasets: [\n"
        "{datasets}\n"
        "    ]\n"
        "  }},\n"
        "  options: {{\n"
        "    responsive: true,\n"
        "    maintainAspectRatio: false,\n"
        "    plugins: {{\n"
        "      legend: {{ display: {legend} }},\n"
        "      title: {{ display: {title_display}, text: {title_js} }}\n"
        "    }},\n"
        "    scales: {{\n"
        "{scales}\n"
        "    }}\n"
        "  }}\n"
        "}}".format(
            chart_type=_js_string(chart_type),
            datasets=datasets_block,
            legend=legend_display,
            title_display=title_display,
            title_js=title_js,
            scales=scales_block,
        )
    )
    return payload


def _render_chart_block(ir: dict, data_obj: dict) -> tuple[str, str]:
    """Return (chart_wrappers_html, chart_js_block) for all applicable charts.

    NOT_APPLICABLE charts (applicability != 'VALID') are skipped entirely.
    """
    charts = ir.get("charts", []) or []
    wrappers: list[str] = []
    js_lines: list[str] = []
    for chart in charts:
        if not isinstance(chart, Mapping):
            continue
        applicability = chart.get("applicability", "VALID")
        if applicability != "VALID":
            # Skip not-applicable charts (no canvas, no Chart() call).
            continue
        chart_id = chart.get("chart_id")
        if not chart_id:
            continue
        wrappers.append(_CHART_WRAPPER.format(chart_id=chart_id))
        options_payload = _chart_options_payload(chart, data_obj)
        js_lines.append(_CHART_JS.format(chart_id=chart_id, chart_options=options_payload))

    wrappers_html = "\n".join(wrappers)
    # Wrap chart JS in DOMContentLoaded + $ helper so canvas exists at run time.
    js_block = (
        "document.addEventListener('DOMContentLoaded', function(){\n"
        "  const $ = (id) => document.getElementById(id);\n"
        + ("\n".join(js_lines) if js_lines else "  /* no applicable charts */")
        + "\n});"
    )
    return wrappers_html, js_block


# ---------------------------------------------------------------------------
# Section HTML generation
# ---------------------------------------------------------------------------

def _render_section(section: Mapping[str, Any], chart_wrappers_html: str = "") -> str:
    """Render one <section> block. The narrative slot is a placeholder token
    `{{NARRATIVE:section_id}}` that downstream stages replace with model text.
    """
    sec_id = section.get("section_id", "")
    title = _escape(section.get("title", sec_id))
    applicability = section.get("applicability", "APPLICABLE")

    if applicability == "NOT_APPLICABLE":
        return _SECTION_NOT_APPLICABLE.format(sec_id=_escape(sec_id), title=title)

    # Build optional chart HTML snippet (caller decides which charts belong here).
    chart_html = chart_wrappers_html.strip()
    if chart_html:
        chart_html_block = chart_html + "\n      "
    else:
        chart_html_block = ""

    body = _SECTION_TEMPLATE.format(
        sec_id=_escape(sec_id),
        title=title,
        chart_html=chart_html_block,
    )
    # Replace the NARRATIVE_TOKEN sentinel with the literal
    # `{{NARRATIVE:<section_id>}}` placeholder (used by the downstream pipeline
    # to splice in model narrative). We can't put `{{...}}` directly in the
    # template because `.format()` would consume the doubled braces.
    narrative_token = "{{NARRATIVE:%s}}" % sec_id
    return body.replace("NARRATIVE_TOKEN", narrative_token)


def _build_nav_items(sections: Iterable[Mapping[str, Any]]) -> str:
    """Build sidebar <a> links for each section."""
    lines: list[str] = []
    for sec in sections:
        sid = sec.get("section_id", "")
        title = _escape(sec.get("title", sid))
        href = "#sec-" + _escape(sid)
        lines.append(
            '      <a href="{href}">{title}</a>'.format(href=href, title=title)
        )
    return "\n".join(lines)


def _build_footnotes(ir: dict) -> str:
    """Build source footnotes from metadata + source_snapshot_hashes."""
    md = ir.get("metadata", {}) or {}
    ticker = _escape(md.get("ticker", ""))
    company = _escape(md.get("company_name", ticker))
    sector = _escape(md.get("sector", ""))
    industry = _escape(md.get("industry", ""))
    exchange = _escape(md.get("exchange", ""))
    generated_at = _escape(md.get("generated_at", ""))
    schema = _escape(ir.get("schema_version", SCHEMA_VERSION))

    hashes = md.get("source_snapshot_hashes", {}) or {}
    hash_lines = "\n".join(
        "        {name}: {h}".format(name=_escape(k), h=_escape(v))
        for k, v in hashes.items()
    ) if hashes else "        (không có snapshot hash)"

    # Source list: prefer IR sections[sources].structured_facts if present.
    sources_section = None
    for sec in ir.get("sections", []) or []:
        if sec.get("section_id") == "sources":
            sources_section = sec
            break
    source_list_items: list[str] = []
    if sources_section:
        facts = sources_section.get("structured_facts", {}) or {}
        items = facts.get("source_list") or facts.get("sources") or []
        if isinstance(items, list):
            for it in items:
                source_list_items.append("        - " + _escape(it))

    sources_html = ""
    if source_list_items:
        sources_html = (
            '      <div class="card" id="sec-sources">\n'
            '        <h2>Nguồn tham khảo</h2>\n'
            '        <ul style="margin:0;padding-left:18px">\n'
            + "\n".join("<li>{}</li>".format(_escape(it)) for it in items) +
            "\n        </ul>\n"
            "      </div>\n"
        )

    footnotes = """<div class="footnotes">
      <h2>Footnotes</h2>
      <div>Mã: <strong>{ticker}</strong> &middot; {company} &middot; {sector} / {industry} &middot; {exchange}</div>
      <div>Generated: {generated_at} &middot; schema {schema}</div>
      <div style="margin-top:8px">Source snapshot hashes:</div>
<pre style="margin:4px 0 0;background:#0b0f14;padding:8px;border-radius:4px;overflow:auto">{hashes}</pre>
    </div>""".format(
        ticker=ticker, company=company, sector=sector, industry=industry,
        exchange=exchange, generated_at=generated_at, schema=schema,
        hashes=hash_lines,
    )
    return footnotes


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_html(ir: dict) -> str:
    """Render a complete, deterministic HTML dashboard from a report IR.

    Args:
        ir: Either a report IR dict, or a path to a JSON file containing one.

    Returns:
        A complete HTML document string. Section narratives are emitted as
        placeholders of the form ``{{NARRATIVE:<section_id>}}`` that a later
        stage replaces with model-generated text. NOT_APPLICABLE sections
        render a "Không áp dụng" notice instead of a placeholder.

    The returned HTML is fully self-contained (CSS inline, Chart.js loaded
    from CDN) and requires no further post-processing beyond placeholder
    substitution. It is valid HTML with balanced tags.
    """
    ir = _load_ir(ir)
    sections = _ordered_sections(ir)
    data_obj = _build_data_object(ir)
    data_block = _render_data_block(data_obj)
    chart_wrappers_html, chart_js_block = _render_chart_block(ir, data_obj)

    # Distribute chart wrappers: each VALID chart is attached to a section
    # that exists and is APPLICABLE. We prefer the chart's natural host
    # (based on chart_id prefix), but fall back to other APPLICABLE sections
    # if the natural host is NOT_APPLICABLE or absent — otherwise a VALID
    # chart would be silently dropped when its host section is NA.
    sections_by_id = _sections_by_id(ir)
    applicable_section_ids = [
        sid for sid, sec in sections_by_id.items()
        if sec.get("applicability", "APPLICABLE") != "NOT_APPLICABLE"
    ]
    section_to_charts: dict[str, str] = {}
    for chart in ir.get("charts", []) or []:
        if not isinstance(chart, Mapping):
            continue
        if chart.get("applicability") != "VALID":
            continue
        chart_id = chart.get("chart_id", "")
        wrapper = _CHART_WRAPPER.format(chart_id=chart_id)
        host_section = _host_section_for_chart(chart_id)
        # Fall back if the natural host is NA or absent.
        if host_section not in applicable_section_ids:
            host_section = _fallback_host_section(applicable_section_ids)
        if host_section:
            section_to_charts.setdefault(host_section, "")
            section_to_charts[host_section] += "\n          " + wrapper

    sections_html = "\n".join(
        _render_section(
            sec,
            chart_wrappers_html=section_to_charts.get(sec.get("section_id", ""), ""),
        )
        for sec in sections
    )

    nav_items = _build_nav_items(sections)
    footnotes = _build_footnotes(ir)
    md = ir.get("metadata", {}) or {}
    title = "{ticker} — Equity Research".format(
        ticker=_escape(md.get("ticker", "Dashboard"))
    )

    doc = _HTML_DOC.format(
        title=title,
        css=_CSS,
        chart_js_cdn=CHART_JS_CDN,
        ticker=_escape(md.get("ticker", "")),
        company=_escape(md.get("company_name", md.get("ticker", ""))),
        nav_items=nav_items,
        schema_version=SCHEMA_VERSION,
        sections=sections_html,
        footnotes=footnotes,
        data_block=data_block,
        chart_js=chart_js_block,
    )
    return doc


def render_to_file(ir: dict, output_path: str) -> str:
    """Render HTML from `ir` and write it to `output_path`.

    Args:
        ir: Report IR dict or path to a JSON file.
        output_path: Destination HTML file path. Parent directories are
            created if missing.

    Returns:
        The absolute `output_path` that was written.
    """
    html_str = render_html(ir)
    abs_path = os.path.abspath(str(output_path))
    parent = os.path.dirname(abs_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as fh:
        fh.write(html_str)
    return abs_path


# ---------------------------------------------------------------------------
# Internal: heuristic chart → section host mapping
# ---------------------------------------------------------------------------

def _host_section_for_chart(chart_id: str) -> str | None:
    """Map a chart_id to the section that should host its <canvas>.

    Heuristic but deterministic: uses well-known chart_id prefixes from the
    IR builder (`chartHistRev`, `chartHistNP`, `chartBSDt`, `chartValPE`, ...).
    Unknown chart_ids default to the financial overview section (`history`).
    """
    cid = (chart_id or "").lower()
    if cid.startswith("charthistrev"):
        return "history"
    if cid.startswith("charthistnp"):
        return "history"
    if cid.startswith("charthistcash") or cid.startswith("charthistcapex"):
        return "history"
    if cid.startswith("chartbs"):
        return "balance_sheet"
    if cid.startswith("chartval"):
        return "valuation"
    if cid.startswith("chartseg"):
        return "segment"
    if cid.startswith("chartthesis"):
        return "thesis"
    if cid.startswith("charttech"):
        return "tech_active"
    return "history"


def _fallback_host_section(applicable_ids: list[str]) -> str | None:
    """Return a sensible fallback section id for a chart whose natural host
    is NOT_APPLICABLE. Preference order: history → balance_sheet → valuation
    → first applicable section in canonical order → first applicable overall.
    """
    if not applicable_ids:
        return None
    preferred = ("history", "balance_sheet", "valuation",
                 "executive_summary", "analyst_notes", "sources")
    as_set = set(applicable_ids)
    for sid in preferred:
        if sid in as_set:
            return sid
    # Otherwise first applicable in canonical order.
    for sid in DEFAULT_SECTION_ORDER:
        if sid in as_set:
            return sid
    return applicable_ids[0]


# ---------------------------------------------------------------------------
# Smoke test / self-test
# ---------------------------------------------------------------------------

def _self_test() -> None:
    """Quick structural test on a synthetic FPT-like IR. Exits non-zero on fail."""
    ir = {
        "schema_version": SCHEMA_VERSION,
        "metadata": {
            "ticker": "FPT",
            "company_name": "FPT Corporation",
            "sector": "Technology",
            "industry": "IT Services",
            "exchange": "HOSE",
            "generated_at": "2026-07-19T00:00:00",
            "source_snapshot_hashes": {"income_statement": "abc123"},
        },
        "reporting_scope": {
            "statement_scope": "consolidated",
            "currency": "VND",
            "unit": "millions",
            "annual_periods": [2021, 2022, 2023, 2024, 2025],
        },
        "financial_data": {
            "metrics": {
                "revenue": {
                    "canonical_field": "revenue",
                    "values": {"2021": 100, "2022": 120, "2023": 140,
                               "2024": 160, "2025": 180},
                    "status": "VALID",
                    "applicability_rule": None,
                },
                "net_profit": {
                    "canonical_field": "net_profit",
                    "values": {"2021": 10, "2022": 12, "2023": 14,
                               "2024": 16, "2025": 18},
                    "status": "VALID",
                    "applicability_rule": None,
                },
                "eps": {
                    "canonical_field": "eps",
                    "values": {"2021": 1000, "2022": 1100, "2023": 1200,
                               "2024": 1300, "2025": 1400},
                    "status": "VALID",
                    "applicability_rule": None,
                },
                "total_assets": {
                    "canonical_field": "total_assets",
                    "values": {"2021": 500, "2022": 550, "2023": 600,
                               "2024": 650, "2025": 700},
                    "status": "VALID",
                    "applicability_rule": None,
                },
                "total_equity": {
                    "canonical_field": "total_equity",
                    "values": {"2021": 300, "2022": 320, "2023": 340,
                               "2024": 360, "2025": 380},
                    "status": "VALID",
                    "applicability_rule": None,
                },
                "capex": {
                    "canonical_field": "capex",
                    "values": {"2021": 20, "2022": 22, "2023": 24,
                               "2024": 26, "2025": 28},
                    "status": "VALID",
                    "applicability_rule": None,
                },
            }
        },
        "derived_metrics": {
            "valuation": {"pe": 18.5, "pb": 3.2, "graham": None},
            "scores": {"tech_score": 3, "tech_verdict": "BULLISH"},
        },
        "sections": [
            {"section_id": sid, "title": sid.replace("_", " ").title(),
             "applicability": "APPLICABLE", "validation_status": "PENDING"}
            for sid in DEFAULT_SECTION_ORDER
        ],
        "charts": [
            {"chart_id": "chartHistRev", "chart_type": "bar",
             "source_metrics": ["revenue"], "applicability": "VALID",
             "title": "Doanh thu"},
            {"chart_id": "chartHistNP", "chart_type": "bar",
             "source_metrics": ["net_profit"], "applicability": "VALID",
             "title": "Lợi nhuận"},
            {"chart_id": "chartHistCash", "chart_type": "bar",
             "source_metrics": ["capex"], "applicability": "VALID",
             "title": "CapEx"},
            {"chart_id": "chartBSDt", "chart_type": "bar",
             "source_metrics": ["total_assets", "total_equity"],
             "applicability": "VALID", "title": "Tài sản & VCSH"},
            {"chart_id": "chartValPE", "chart_type": "line",
             "source_metrics": ["eps"], "applicability": "VALID",
             "title": "EPS"},
            {"chart_id": "chartSkipped", "chart_type": "bar",
             "source_metrics": ["revenue"], "applicability": "NOT_APPLICABLE",
             "title": "Should be skipped"},
        ],
        "external_claims": [],
        "validation": {
            "section_results": {}, "deterministic_gate_results": {},
            "unresolved_items": [],
        },
    }

    html_str = render_html(ir)

    # --- Structural assertions ---
    assert "<!DOCTYPE html>" in html_str, "missing DOCTYPE"
    assert "</html>" in html_str, "missing </html>"
    assert html_str.count("<html") == html_str.count("</html>"), "unbalanced <html>"
    assert html_str.count("<body") == html_str.count("</body>"), "unbalanced <body>"
    assert html_str.count("<head>") == html_str.count("</head>"), "unbalanced <head>"
    assert html_str.count("<div") == html_str.count("</div>"), "unbalanced <div>"
    assert html_str.count("<section") == html_str.count("</section>"), "unbalanced <section>"

    # DATA block present and well-formed.
    assert "const DATA = {" in html_str, "missing DATA block"
    assert '"ticker": "FPT"' in html_str or '"ticker":"FPT"' in html_str, \
        "ticker not in DATA"
    assert '"revenue":' in html_str, "revenue not in DATA"
    assert '"revenueStatus": "VALID"' in html_str, "revenue status missing"

    # Chart.js CDN.
    assert CHART_JS_CDN in html_str, "Chart.js CDN missing"

    # Chart wrappers + new Chart() calls.
    chart_calls = html_str.count("new Chart(")
    assert chart_calls >= 5, "expected at least 5 Chart() calls, got %d" % chart_calls
    assert 'id="chartHistRev"' in html_str, "chartHistRev canvas missing"
    assert 'id="chartSkipped"' not in html_str, "NOT_APPLICABLE chart should be skipped"

    # Chart JS uses bare DATA identifiers (not stringified JSON).
    assert "labels: DATA.years" in html_str, "DATA.years labels ref missing"
    assert "data: DATA.revenue" in html_str, "DATA.revenue ref missing"
    assert "data: DATA.netProfit" in html_str, "DATA.netProfit ref missing"

    # Narrative placeholders.
    assert "{{NARRATIVE:executive_summary}}" in html_str, "exec_summary placeholder missing"

    print("SELF-TEST OK: %d chars, %d Chart() calls, %d sections" % (
        len(html_str), chart_calls, html_str.count("<section")
    ))


if __name__ == "__main__":
    _self_test()
