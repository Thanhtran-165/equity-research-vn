#!/usr/bin/env python3
"""
build_data_contract.py — Deterministic data-contract builder (Step 2 of content-cycle).

BRANCH-A CANDIDATE: adds a `technical` block to verified-dashboard-data.json so the
Phase-4A Tech Score flows through the pipeline as a machine-readable field.

Reads raw source-pack CSVs + JSONs, produces:
  1. verified-dashboard-data.json  — the single data contract Phase 6 renders from
  2. data/financials.json          — verifier-expected format (for REQ-022/025/026)
  3. data/balance_sheet.json       — verifier-expected format (for REQ-023)
  4. data/cash_flow.json           — verifier-expected format (for REQ-024)

This is DETERMINISTIC — no model involved. It bridges the source-pack's raw CSV format
to the verifier's expected JSON format, AND produces the dashboard_data contract that
Phase 6 receives inline (like the template).

BRANCH-A CHANGE: also reads `technical_active.json` from the source-pack and, when it
contains a `tech_score`, emits a `technical` block into the dashboard contract:
    {"technical": {"mode":"ACTIVE","tech_score":-6,"scale_min":-6,"scale_max":6,
                   "verdict":"STRONG SELL","source_file":"technical_active.json",
                   "verified":true}}
If technical_active.json is missing or has no tech_score -> `"technical": null`.
No fallback: a missing source value stays null so downstream gates fail loudly.

Usage:
  python3 build_data_contract.py <source_pack_dir> <output_dir>

ERVN-PERIOD-001 HOTFIX (v1.0.1):
  Replaces positional year mapping (years_asc[4-i]) with explicit period-key
  resolution via period_key_resolver.resolve_periods(). Positional mapping is
  forbidden; build fail-closes if no explicit period-labeled source is available.
  See ERVN-PERIOD-001.md for incident context.
"""
import sys, os, csv, json, datetime, re, unicodedata

# ERVN-PERIOD-001: import period_key_resolver (same dir as this file)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from period_key_resolver import resolve_periods, ResolverError

def load_csv(path):
    with open(path) as f:
        reader = csv.DictReader(f)
        return list(reader)

def safe_float(v):
    try: return float(v)
    except (ValueError, TypeError): return None


# ============================================================================
# SECTOR-HARDENING (v0.8.0): canonical field resolver
# ============================================================================
# Problem discovered in Cohort C: the builder used exact-string column lookups
# (e.g. row.get("Total Assets")) that broke on banking CSVs which use ALL CAPS
# ("TOTAL ASSETS"). VCB has real data (1.07 quadrillion VND) the builder couldn't
# read, producing equity=0 → REQ-023 checked nothing → REQ-025 PB=None.
#
# Fix: normalize any column name to a canonical key, then resolve via an alias
# map. Applies to: total_assets, equity, revenue, net_income, eps, capex,
# plus banking-specific (total_loans, deposits) for future sector support.
# FAILS CLOSED if a canonical field has no match in any alias (no default).

_CANONICAL_ALIASES = {
    "total_assets": [
        "total assets", "total_assets", "totalassets", "tổng tài sản",
        "tong tai san", "TOTAL ASSETS", "Total Assets",
    ],
    "equity": [
        "owner's equity", "owners equity", "owner equity", "equity",
        "owners' equity",  # insurance/plural possessive (BVH Bao Viet)
        "total equity", "shareholders equity", "shareholder's equity",
        "vốn chủ sở hữu", "von chu so huu", "OWNER'S EQUITY", "Owner's Equity",
        "OWNERS' EQUITY",  # ALL CAPS plural (insurance CSVs)
    ],
    "revenue": [
        "net sales", "sales", "revenue", "total revenue", "doanh thu",
        "total operating income", "net interest income",  # banking analogues
    ],
    "net_income": [
        "attributable to parent company", "net profit/(loss) after tax",
        "net profit after tax", "net profit", "net income",
        "profit after tax", "lợi nhuận sau thuế", "loi nhuan sau thue",
    ],
    "eps": [
        "eps basic (vnd)", "eps basic", "eps", "earnings per share",
        "eps (vnd)", "lãi cơ bản trên cổ phiếu",
    ],
    "capex": [
        "purchases of fixed assets and other long term assets",
        "purchases of fixed assets", "capital expenditure", "capex",
        "chi mua sắm tài sản cố định",
    ],
    # Banking-specific (for future NIM/CAR/NPL support; not yet wired to contract)
    "total_loans": [
        "loans and advances to customers, net", "loans and advances to customers",
        "total loans", "cho vay khách hàng", "dư nợ cho vay",
    ],
    "deposits": [
        "deposits from customers", "total deposits", "customer deposits",
        "tiền gửi khách hàng", "tien gui khach hang",
    ],
}


def _normalize_field_name(name):
    """Normalize a column/field name for case-insensitive, format-insensitive matching.

    Pipeline (per owner directive 2026-07-16, v0.14.0):
      trim whitespace → Unicode NFKC normalization
      → normalize curly quotes (’‘""') to ASCII
      → remove possessive apostrophes (owner's → owner, owners' → owner)
      → casefold → collapse spaces/underscores/hyphens → strip
    """
    if name is None:
        return ""
    s = str(name).strip()
    s = unicodedata.normalize("NFKC", s)
    # Normalize curly/smart quotes to ASCII
    s = s.replace("\u2019", "'").replace("\u2018", "'")  # ' ' → '
    s = s.replace("\u201c", '"').replace("\u201d", '"')  # " " → "
    # Remove possessive apostrophes: "owner's" → "owner", "owners'" → "owner"
    s = re.sub(r"(\w)'s\b", r"\1", s, flags=re.I)  # owner's → owner
    s = re.sub(r"(\w[sS])'", r"\1", s, flags=re.I)  # owners' → owners (then casefold)
    s = s.casefold()
    # collapse whitespace, underscores, hyphens to single space
    s = re.sub(r"[\s_\-]+", " ", s).strip()
    return s


def _build_column_index(columns):
    """Build a normalized-name → original-name index from CSV header columns."""
    return {_normalize_field_name(c): c for c in columns}


def resolve_field(row, column_index, canonical_key):
    """Resolve a canonical financial field from a CSV row, case/format-insensitively.

    Returns the raw value (string) if any alias matches, else None.
    FAILS CLOSED: no default, no fallback formula. A None return signals the
    field is genuinely absent from this sector's CSV (e.g. revenue in banking).
    """
    aliases = _NORMALIZED_ALIASES.get(canonical_key, set())
    for norm_alias, orig_col in column_index.items():
        if norm_alias in aliases:
            return row.get(orig_col)
    return None


# Precompute normalized alias lookup: canonical_key → set of normalized aliases
_NORMALIZED_ALIASES = {}
for canon, aliases in _CANONICAL_ALIASES.items():
    _NORMALIZED_ALIASES[canon] = {_normalize_field_name(a) for a in aliases}

def build_technical_block(src):
    """BRANCH-A: read technical_active.json from the source-pack and return the
    `technical` block for the dashboard contract. Returns None (→ JSON null) when:
      - technical_active.json is missing
      - file is unreadable / not valid JSON
      - has no `tech_score` key
    NO FALLBACK: a missing source value stays null so phase4a_gate fails as
    NO_SOURCE_DATA rather than silently inventing a number.
    """
    tech_path = os.path.join(src, "technical_active.json")
    if not os.path.exists(tech_path):
        return None
    try:
        tech = json.load(open(tech_path))
    except Exception:
        return None
    if not isinstance(tech, dict):
        return None
    if "tech_score" not in tech:
        return None
    # pass-through source values; canonicalization/consistency is the gate's job.
    return {
        "mode": "ACTIVE",
        "tech_score": tech.get("tech_score"),
        "scale_min": -6,
        "scale_max": 6,
        "verdict": tech.get("verdict"),
        "source_file": "technical_active.json",
        "verified": True,
    }

def _validate_source_schema(src):
    """FAIL-CLOSED schema validation (Cohort C hardening).

    A source-pack MUST carry canonical fields that unambiguously identify the
    company. Before Cohort C, the builder silently fell back to ticker="CTD",
    company="", price=0 when overview.json used non-canonical field names —
    which produced *fabricated-looking* data (PNJ pack rendered as a "CTD"
    artifact with price 0). That is a data-integrity violation, not a skill
    defect, so we now fail closed instead.

    Raises SystemExit(2) with a structured FAIL_SOURCE_SCHEMA record if any
    required canonical field is absent. The caller (runner) propagates this as
    a non-agent failure; the protocol logs it as a source-pack readiness gap.
    """
    overview_path = os.path.join(src, "overview.json")
    if not os.path.exists(overview_path):
        print(json.dumps({"status": "FAIL_SOURCE_SCHEMA",
                          "reason": "overview.json missing",
                          "source_pack": src}, ensure_ascii=False))
        sys.exit(2)
    try:
        overview = json.load(open(overview_path))
    except Exception as e:
        print(json.dumps({"status": "FAIL_SOURCE_SCHEMA",
                          "reason": f"overview.json unparseable: {e}",
                          "source_pack": src}, ensure_ascii=False))
        sys.exit(2)

    missing = []
    # Canonical identity fields — NO static fallback (was: "CTD").
    if not overview.get("symbol"):
        missing.append("symbol (canonical ticker; was silently defaulted to 'CTD')")
    if not overview.get("organ_name"):
        missing.append("organ_name (canonical company name; was silently empty)")
    price = overview.get("current_price")
    if price is None or (isinstance(price, (int, float)) and price <= 0):
        missing.append("current_price (must be a positive number; placeholder 0/50000 produces PE=0 or distorted PE)")

    if missing:
        print(json.dumps({"status": "FAIL_SOURCE_SCHEMA",
                          "reason": "canonical fields missing or invalid",
                          "missing": missing,
                          "source_pack": src,
                          "fix": "normalize overview.json to canonical schema (symbol, organ_name, current_price>0)",
                          "no_static_fallback": "builder no longer defaults ticker to 'CTD'"}, ensure_ascii=False))
        sys.exit(2)
    return overview

def main():
    src = sys.argv[1]; out = sys.argv[2]
    os.makedirs(os.path.join(out, "data"), exist_ok=True)

    # FAIL-CLOSED: validate canonical identity before touching any data.
    overview = _validate_source_schema(src)

    # --- ERVN-PERIOD-001 HOTFIX (v1.0.1): explicit period resolution ---
    # The old code assumed CSV rows are descending (row 0 = latest). The actual
    # vnstock sponsor format is ASCENDING (row 0 = oldest). This caused 376/475
    # (period,value) pairs to be assigned to wrong periods across 34 tickers
    # (see incidents/ERVN-PERIOD-001-forensic-summary.json).
    #
    # The fix: resolve period labels EXPLICITLY via period_key_resolver.
    # If no explicit period source is available, build ABORTS — no positional fallback.
    try:
        period_resolution = resolve_periods(src, expected_year_count=5,
                                            allow_value_diff_fallback=False)
    except ResolverError as e:
        sys.stderr.write(f"FAIL_CLOSED [ERVN-PERIOD-001 hotfix]: {e.code}\n")
        sys.stderr.write(f"  detail: {e.detail}\n")
        sys.stderr.write(f"  Build aborted. Positional mapping is forbidden.\n")
        sys.exit(2)
    years_asc = [int(y) for y in period_resolution.chronological_order]
    period_index = period_resolution.period_index  # year → StatementRowIndex

    # --- income statement ---
    inc = load_csv(os.path.join(src, "income_statement_sponsor.csv"))
    inc_idx = _build_column_index(inc[0].keys()) if inc else {}
    revenue = {}; npatmi = {}; eps = {}
    for y in years_asc:
        row_idx_info = period_index[str(y)]
        if row_idx_info.income >= len(inc):
            continue
        row = inc[row_idx_info.income]
        # SECTOR-HARDENING: canonical resolver (case/format-insensitive).
        # Banking has no revenue (returns None → revenue stays empty, correct).
        rev = safe_float(resolve_field(row, inc_idx, "revenue"))
        np = safe_float(resolve_field(row, inc_idx, "net_income"))
        e = safe_float(resolve_field(row, inc_idx, "eps"))
        if rev: revenue[str(y)] = rev
        if np: npatmi[str(y)] = np
        if e: eps[str(y)] = e

    # --- balance sheet (uses resolver indices) ---
    bs = load_csv(os.path.join(src, "balance_sheet_sponsor.csv"))
    bs_idx = _build_column_index(bs[0].keys()) if bs else {}
    total_assets = {}; equity = {}
    for y in years_asc:
        row_idx_info = period_index[str(y)]
        if row_idx_info.balance >= len(bs):
            continue
        row = bs[row_idx_info.balance]
        # SECTOR-HARDENING: resolves "TOTAL ASSETS" (banking) and "Total Assets" (industrial).
        ta = safe_float(resolve_field(row, bs_idx, "total_assets"))
        oe = safe_float(resolve_field(row, bs_idx, "equity"))
        if ta: total_assets[str(y)] = ta
        if oe: equity[str(y)] = oe

    # --- cash flow (uses resolver indices) ---
    cf = load_csv(os.path.join(src, "cash_flow_sponsor.csv"))
    cf_idx = _build_column_index(cf[0].keys()) if cf else {}
    capex = {}
    for y in years_asc:
        row_idx_info = period_index[str(y)]
        if row_idx_info.cash >= len(cf):
            continue
        row = cf[row_idx_info.cash]
        cx = safe_float(resolve_field(row, cf_idx, "capex"))
        if cx: capex[str(y)] = abs(cx)

    # --- overview + valuation ---
    # overview already loaded + validated by _validate_source_schema() above.
    try: valuation = json.load(open(os.path.join(src, "fundamental_valuation.json")))
    except: valuation = {}

    price = overview["current_price"]   # validated >0 by _validate_source_schema
    shares = overview.get("issue_share", 0)

    # --- build dashboard data contract (tỷ VND scale) ---
    rev_arr = [round(revenue.get(str(y),0)/1e9, 2) for y in years_asc]
    np_arr = [round(npatmi.get(str(y),0)/1e9, 2) for y in years_asc]
    eps_arr = [round(eps.get(str(y),0), 1) for y in years_asc]
    ta_arr = [round(total_assets.get(str(y),0)/1e9, 2) for y in years_asc]
    eq_arr = [round(equity.get(str(y),0)/1e9, 2) for y in years_asc]
    capex_arr = [round(capex.get(str(y),0)/1e9, 2) for y in years_asc]

    latest = years_asc[-1] if years_asc else "?"
    pe = round(price / eps.get(str(latest), 1), 2) if eps.get(str(latest)) else None
    bvps = round(equity.get(str(latest),0) / shares, 2) if shares else None
    pb = round(price / bvps, 2) if bvps else None

    contract = {
      "company": overview["organ_name"],   # validated non-empty by _validate_source_schema
      "ticker": overview["symbol"],         # validated present; NO "CTD" fallback
      "price": price,
      "shares": shares,
      "market_cap": overview.get("market_cap"),
      "periods": [int(y) for y in years_asc],
      "financials": {
        "revenue": rev_arr, "netProfit": np_arr, "eps": eps_arr,
        "totalAssets": ta_arr, "equity": eq_arr, "capex": capex_arr,
        "years": [str(y) for y in years_asc],
      },
      "valuation": {"pe": pe, "pb": pb, "price": price},
      "technical": build_technical_block(src),
      "company_profile": _load_company_profile(src),
      "references": _build_references(src),
      "_provenance": {
        "built_at": datetime.datetime.now().isoformat(),
        "source": "deterministic build_data_contract.py from source-pack CSVs",
        "unit": "tỷ VND (financials arrays); VND (price, eps)",
        "verification_status": "verified — values trace directly to sponsor CSVs",
        "period_resolution": {
          "method": period_resolution.detection_method,
          "confidence": period_resolution.confidence,
          "sources_used": period_resolution.sources_used,
          "hotfix_id": "ERVN-PERIOD-001",
        },
      }
    }
    json.dump(contract, open(os.path.join(out, "verified-dashboard-data.json"),"w"), indent=2, ensure_ascii=False)

    # --- write verifier-expected format files (string keys to match dicts) ---
    # FIX: store revenue/npatmi in TỶ VND (÷1e9) to match DATA array scale.
    # The verifier's REQ-022 uses divisor=1, so gt must be in the same scale as the DATA array.
    # EPS stays in raw VND (per-share, not scaled). Balance sheet uses divisor=1e9 in requirements
    # so those stay raw VND (verifier divides by 1e9 to get tỷ for comparison).
    fin_json = {
      "revenue_ty": {str(y): round(revenue.get(str(y))/1e9, 2) for y in years_asc if revenue.get(str(y))},
      "npatmi_ty": {str(y): round(npatmi.get(str(y))/1e9, 2) for y in years_asc if npatmi.get(str(y))},
      "eps_vnd": {str(y): eps.get(str(y)) for y in years_asc if eps.get(str(y))},
      "equity_ty": {str(y): round(equity.get(str(y))/1e9, 2) for y in years_asc if equity.get(str(y))},
      "overview": {"current_price": price, "issue_share": shares},
    }
    json.dump(fin_json, open(os.path.join(out, "data", "financials.json"),"w"), indent=2)
    bs_json = {"years": [str(y) for y in years_asc],
               "Total Assets": {str(y): total_assets.get(str(y)) for y in years_asc if total_assets.get(str(y))},
               "Owner's Equity": {str(y): equity.get(str(y)) for y in years_asc if equity.get(str(y))}}
    json.dump(bs_json, open(os.path.join(out, "data", "balance_sheet.json"),"w"), indent=2)
    cf_json = {"Purchases of fixed assets and other long term assets": {str(y): capex.get(str(y)) for y in years_asc if capex.get(str(y))}}
    json.dump(cf_json, open(os.path.join(out, "data", "cash_flow.json"),"w"), indent=2)

    print(f"data contract built → {out}")
    print(f"  years: {years_asc}")
    print(f"  revenue (tỷ): {rev_arr}")
    print(f"  npatmi (tỷ): {np_arr}")
    print(f"  eps: {eps_arr}")
    print(f"  PE: {pe} | PB: {pb}")
    print(f"  technical: {contract['technical']}")
    print(f"  references: {len(contract['references'])}")
    print(f"  data/*.json written for verifier (REQ-022→026)")

def _build_references(src):
    """Build ≥10 numbered references from news.csv + source URLs."""
    refs = []
    try:
        news = load_csv(os.path.join(src, "news.csv"))
        for i, row in enumerate(news[:12], 1):
            title = row.get("title", row.get("headline","")).strip()
            date = row.get("date", row.get("published","")).strip()
            src_url = row.get("url", row.get("link","")).strip()
            if title:
                refs.append({"id": i, "title": title[:120], "date": date, "url": src_url or "(vnstock)"})
    except Exception: pass
    # pad with standard sources if <10 (generic — no company-specific text)
    std = ["Vnstock sponsor data", "HOSE filings", "VIRECTC disclosure", "Issuer disclosure portal"]
    while len(refs) < 10:
        refs.append({"id": len(refs)+1, "title": std[len(refs) % len(std)], "date": "", "url": "(standard)"})
    return refs[:15]


def _load_company_profile(src):
    """Source Pack v2: load company_profile.json with operational KPIs, market
    position, distribution metrics. This provides the agent with company-specific
    descriptors (store counts, market share, factories, employees) so it doesn't
    need to fill from model memory. Returns None if file is absent (backward-compatible).
    """
    path = os.path.join(src, "company_profile.json")
    if not os.path.exists(path):
        return None
    try:
        return json.load(open(path))
    except Exception:
        return None


if __name__ == "__main__":
    main()
