#!/usr/bin/env python3
"""
generate_fundamental_sponsor.py — Create fundamental_sponsor.json snapshots.

ERVN-PERIOD-001 HOTFIX step 1 (per owner directive §3 + §12).

For each ticker's source-pack, query vnstock_data sponsor API once, capture
explicit period-keyed data, and write a fundamental_sponsor.json alongside
the existing CSVs. The snapshot records BOTH normalized data AND raw source
evidence (column names, ordering, period labels) so period_key_resolver can
re-derive period mapping deterministically.

Snapshot schema (per owner §3):
  snapshot:
    ticker
    source_id                    (e.g., "vnstock_sponsor_vci")
    collection_timestamp
    statement_type               ("annual")
    statement_scope              ("consolidated")
    currency                     ("VND")
    unit                         ("raw")
    raw_period_labels            (["2018","2019","2020","2021","2022","2023","2024","2025"])
    source_order                 ("ascending_oldest_first" | "descending_latest_first" | "mixed")
    raw_field_names              (per statement: list of CSV column names)
    raw_values                   (per statement: {field: {period: value}})
    snapshot_hash                (sha256 of raw_values for content addressing)
    data                         (canonical 5-year window [2021..2025])
    price, shares, eps25, bvps25, pe, pb, graham   (overview-derived)
"""
import os
import sys
import json
import hashlib
import datetime
import warnings
import contextlib
import time
warnings.filterwarnings("ignore")


@contextlib.contextmanager
def _suppress_vnstock_banner():
    """Silence vnstock's promotional banner via fd-level stderr redirect."""
    saved_stderr_fd = os.dup(2)
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull_fd, 2)
        yield
    finally:
        os.dup2(saved_stderr_fd, 2)
        os.close(devnull_fd)
        os.close(saved_stderr_fd)

TICKERS = [
    # Phase 6E generalization cohort (10 tickers, 10 sectors)
    ("FPT", "Technology",            "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/FPT"),
    ("GAS", "Energy",                "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs/GAS"),
    ("MWG", "Retail",                "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs/MWG"),
    ("VNM", "Food & Beverage",       "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs/VNM"),
    ("DHG", "Pharma",                "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b2/DHG"),
    ("POW", "Utilities",             "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b2/POW"),
    ("VJC", "Airlines",              "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b2/VJC"),
    ("GVR", "Agriculture",           "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-soak/GVR"),
    ("NLG", "Real Estate",           "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-req/NLG"),
    ("DCM", "Chemicals",             "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b2/DCM"),
    # Requal tickers (targeted + shadow cohorts will use these)
    ("CTD", "Construction",          "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/CTD"),
    ("HPG", "Steel",                 "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs/HPG"),
    ("VCB", "Banking",               "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/VCB"),
    ("BVH", "Insurance",             "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b1tp/BVH"),
    ("MSN", "Diversified",           "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b1tp/MSN"),
    ("PVD", "Oil & Gas Services",    "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-req/PVD"),
    # Add remaining tickers that FAIL_CLOSED without metadata
    ("KDH", "Real Estate",           "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/KDH"),
    ("PNJ", "Personal Goods",        "/Users/bobo/ZCodeProject/agent-eval/cohort-c/source-packs/PNJ"),
    ("ACB", "Banking",               "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-fresh/ACB"),
    ("GEX", "Industrial",            "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-fresh/GEX"),
    ("PLX", "Energy",                "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-fresh/PLX"),
    ("SAB", "Beverage",              "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-fresh/SAB"),
    ("SSI", "Financial Services",    "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-fresh/SSI"),
    ("BID", "Banking",               "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs/BID"),
    ("DGW", "Technology",            "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b1tp/DGW"),
    ("HDB", "Banking",               "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b1tp/HDB"),
    ("HDG", "Real Estate",           "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-b1tp/HDG"),
    ("DXG", "Real Estate",           "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-soak/DXG"),
    ("NAB", "Banking",               "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-soak/NAB"),
    ("REE", "Utilities",             "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-soak/REE"),
    ("TCB", "Banking",               "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-soak/TCB"),
    ("FRT", "Retail",                "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-req/FRT"),
    ("MBB", "Banking",               "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-req/MBB"),
    ("VHC", "Seafood",               "/Users/bobo/ZCodeProject/agent-eval/cohort-c/shadow/source-packs-req/VHC"),
]

CANONICAL_FIELDS = {
    # canonical_name → list of CSV column aliases (case-insensitive substring match)
    "revenue":           ["Sales", "Net sales", "Revenue"],
    "net_profit":        ["Attributable to parent company", "Net profit", "Profit after tax"],
    "eps":               ["EPS basic"],
    "total_assets":      ["Total Assets"],
    "total_equity":      ["Owner's Equity", "Owners Equity", "Total Equity",
                           "Equity Attributable"],
    "capex":             ["Purchases of fixed assets"],
    "operating_cash_flow": ["Net cash from operating activities",
                             "Net cash generated from operating activities",
                             "Cash flow from operations"],
}

EXPECTED_5Y = [2021, 2022, 2023, 2024, 2025]


def _safe_float(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _find_col(columns, aliases):
    for col in columns:
        cl = col.lower()
        for a in aliases:
            if a.lower() in cl:
                return col
    return None


def fetch_statement(ticker, statement_kind, max_retries=3):
    """Fetch a statement via vnstock_data sponsor API. Returns DataFrame.
    Retries on rate limit (waits 60s between attempts).
    """
    from vnstock_data import Finance
    last_err = None
    for attempt in range(max_retries):
        try:
            with _suppress_vnstock_banner():
                f = Finance(symbol=ticker, source="VCI")
                if statement_kind == "income":
                    return f.income_statement()
                if statement_kind == "balance":
                    return f.balance_sheet()
                if statement_kind == "cash":
                    return f.cash_flow()
        except Exception as e:
            last_err = e
            msg = str(e).lower()
            if "rate" in msg or "giới hạn" in msg or "limit" in msg or "60" in msg:
                print(f"\n    [rate-limited, retry {attempt+1}/{max_retries}, waiting 60s]", end="", flush=True)
                time.sleep(60)
                continue
            raise
    raise last_err


def fetch_overview(ticker, max_retries=3):
    from vnstock_data import Company
    last_err = None
    for attempt in range(max_retries):
        try:
            with _suppress_vnstock_banner():
                c = Company(symbol=ticker, source="VCI")
                ov = c.overview()
            if hasattr(ov, "to_dict"):
                return ov.to_dict("records")[0] if len(ov) > 0 else {}
            return ov
        except Exception as e:
            last_err = e
            msg = str(e).lower()
            if "rate" in msg or "giới hạn" in msg or "limit" in msg or "60" in msg:
                print(f"\n    [rate-limited, retry {attempt+1}/{max_retries}, waiting 60s]", end="", flush=True)
                time.sleep(60)
                continue
            raise
    raise last_err


def detect_source_order(period_labels):
    """Determine chronological order of period labels (as ints)."""
    ints = []
    for p in period_labels:
        try:
            ints.append(int(str(p)[:4]))
        except (ValueError, TypeError):
            return "mixed"
    if ints == sorted(ints):
        return "ascending_oldest_first"
    if ints == sorted(ints, reverse=True):
        return "descending_latest_first"
    return "mixed"


def extract_statement_raw(df, statement_kind):
    """Return dict with raw_field_names + raw_values keyed by period."""
    if df is None or len(df) == 0:
        return {"raw_field_names": [], "raw_values": {}}
    # DataFrame index is the year string ("2018", "2019", ...)
    df_year = df[df["report_period"] == "year"] if "report_period" in df.columns else df
    period_labels = [str(idx) for idx in df_year.index.tolist()]
    columns = list(df.columns)
    raw_values = {}
    for canon, aliases in CANONICAL_FIELDS.items():
        col = _find_col(columns, aliases)
        if not col:
            continue
        per_period = {}
        for idx, period in zip(df_year.index, period_labels):
            try:
                val = float(df_year.loc[idx, col])
            except (ValueError, TypeError):
                continue
            per_period[str(period)] = val
        if per_period:
            raw_values[canon] = {"csv_column": col, "per_period": per_period}
    return {
        "raw_field_names": columns,
        "period_labels": period_labels,
        "raw_values": raw_values,
    }


def build_canonical_5y(raw_values_for_statement):
    """Pick the canonical [2021..2025] window from a statement's raw_values.

    Input format (per statement):
        {canon: {"csv_column": "...", "per_period": {period: value}}}
    OR (already flattened):
        {canon: {period: value}}
    """
    out = {}
    for canon, info in raw_values_for_statement.items():
        if isinstance(info, dict) and "per_period" in info:
            per_period = info["per_period"]
        elif isinstance(info, dict):
            per_period = info  # already flattened
        else:
            continue
        window = {}
        for y in EXPECTED_5Y:
            if str(y) in per_period:
                window[str(y)] = per_period[str(y)]
        if len(window) == len(EXPECTED_5Y):
            out[canon] = window
    return out


def compute_snapshot_hash(payload):
    """sha256 of sorted (canonical, period, value) triples — content-addressing."""
    triples = []
    for canon, info in (payload.get("raw_values_per_statement") or {}).items():
        for stmt, per_period in (info or {}).items():
            for p, v in (per_period or {}).items():
                triples.append((canon, stmt, str(p), str(v)))
    triples.sort()
    blob = "\n".join("|".join(t) for t in triples).encode()
    return hashlib.sha256(blob).hexdigest()


def generate_for_ticker(ticker, sector, source_pack, force_overwrite=False):
    """Generate fundamental_sponsor.json for one ticker.

    If force_overwrite=True, replaces existing snapshots that lack the
    full schema (raw_values_per_statement, source_order, snapshot_hash).
    """
    out_path = os.path.join(source_pack, "fundamental_sponsor.json")
    if os.path.exists(out_path) and not force_overwrite:
        # Check if existing snapshot has the full schema
        try:
            existing = json.load(open(out_path))
            if "raw_values_per_statement" in existing and "source_order" in existing:
                return {"ticker": ticker, "skipped": "already_full_schema", "path": out_path}
        except Exception:
            pass
        # Existing is minimal — proceed to overwrite
        if not force_overwrite:
            # Default: overwrite minimal schemas in-place
            pass

    print(f"  fetching {ticker} ({sector})...", end=" ", flush=True)
    try:
        inc_df = fetch_statement(ticker, "income")
        time.sleep(1.2)  # throttle to avoid 60 req/min rate limit
        bs_df = fetch_statement(ticker, "balance")
        time.sleep(1.2)
        cf_df = fetch_statement(ticker, "cash")
        time.sleep(1.2)
        overview = fetch_overview(ticker)
        time.sleep(1.2)
    except Exception as e:
        print(f"FAIL ({type(e).__name__}: {str(e)[:80]})")
        return {"ticker": ticker, "error": f"fetch_failed: {type(e).__name__}: {str(e)[:200]}"}

    inc_raw = extract_statement_raw(inc_df, "income")
    bs_raw = extract_statement_raw(bs_df, "balance")
    cf_raw = extract_statement_raw(cf_df, "cash")

    period_labels = inc_raw.get("period_labels", [])
    source_order = detect_source_order(period_labels)

    raw_values_per_statement = {
        "income":  {canon: info["per_period"] for canon, info in inc_raw.get("raw_values", {}).items()},
        "balance": {canon: info["per_period"] for canon, info in bs_raw.get("raw_values", {}).items()},
        "cash":    {canon: info["per_period"] for canon, info in cf_raw.get("raw_values", {}).items()},
    }

    canonical_5y = {
        "income":  build_canonical_5y(raw_values_per_statement["income"]),
        "balance": build_canonical_5y(raw_values_per_statement["balance"]),
        "cash":    build_canonical_5y(raw_values_per_statement["cash"]),
    }
    # Flatten: data["2025"]["revenue"] = ... (matches existing schema)
    data = {}
    for y in EXPECTED_5Y:
        data[str(y)] = {}
        for canon in CANONICAL_FIELDS:
            for stmt in ("income", "balance", "cash"):
                v = canonical_5y.get(stmt, {}).get(canon, {}).get(str(y))
                if v is not None and canon not in data[str(y)]:
                    data[str(y)][canon] = v

    # Overview-derived
    price = _safe_float(overview.get("current_price"))
    if price is not None and price < 1000:
        price = price * 1000  # vnstock returns thousands-of-VND
    shares = _safe_float(overview.get("issue_share") or overview.get("issue_share", 0))
    eps25 = data.get("2025", {}).get("eps")
    bvps25 = None
    pe = pb = None
    if shares:
        eq25 = data.get("2025", {}).get("total_equity")
        if eq25:
            bvps25 = eq25 / shares
    if eps25 and price:
        pe = round(price / eps25, 4)
    if bvps25 and price:
        pb = round(price / bvps25, 4)

    snapshot = {
        "ticker": ticker,
        "source_id": "vnstock_sponsor_vci",
        "collection_timestamp": datetime.datetime.now().isoformat(),
        "statement_type": "annual",
        "statement_scope": "consolidated",
        "currency": "VND",
        "unit": "raw",
        "raw_period_labels": period_labels,
        "source_order": source_order,
        "raw_field_names": {
            "income":  inc_raw.get("raw_field_names", []),
            "balance": bs_raw.get("raw_field_names", []),
            "cash":    cf_raw.get("raw_field_names", []),
        },
        "raw_values_per_statement": raw_values_per_statement,
        "snapshot_hash": "",
        "years": [str(y) for y in EXPECTED_5Y],
        "data": data,
        "price": price,
        "shares": shares,
        "eps25": eps25,
        "bvps25": bvps25,
        "pe": pe,
        "pb": pb,
    }
    snapshot["snapshot_hash"] = compute_snapshot_hash(snapshot)

    with open(out_path, "w") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False, default=str)

    print(f"OK (periods={len(period_labels)}, order={source_order}, hash={snapshot['snapshot_hash'][:12]})")
    return {
        "ticker": ticker,
        "path": out_path,
        "period_count": len(period_labels),
        "source_order": source_order,
        "snapshot_hash": snapshot["snapshot_hash"],
    }


def main():
    print(f"=== ERVN-PERIOD-001 §3 — Generating fundamental_sponsor.json snapshots ===")
    print(f"tickers: {len(TICKERS)}")
    print()
    results = []
    for ticker, sector, src in TICKERS:
        if not os.path.isdir(src):
            print(f"  [SKIP] {ticker}: source pack missing at {src}")
            results.append({"ticker": ticker, "error": "source_pack_missing"})
            continue
        results.append(generate_for_ticker(ticker, sector, src))

    # Summary
    print()
    print("=" * 80)
    n_ok = sum(1 for r in results if "snapshot_hash" in r)
    n_skip = sum(1 for r in results if r.get("skipped"))
    n_fail = sum(1 for r in results if "error" in r and "skipped" not in r)
    print(f"Generated: {n_ok}  Skipped (exists): {n_skip}  Failed: {n_fail}")
    orders = {}
    for r in results:
        if "source_order" in r:
            orders[r["source_order"]] = orders.get(r["source_order"], 0) + 1
    print(f"Source ordering detected:")
    for order, count in sorted(orders.items()):
        print(f"  {order}: {count} tickers")

    # Write manifest
    manifest_path = "/Users/bobo/.zcode/skills/equity-research-vn/incidents/v1.0.1-candidate/fundamental_sponsor_manifest.json"
    manifest = {
        "generated_at": datetime.datetime.now().isoformat(),
        "purpose": "ERVN-PERIOD-001 hotfix step 1 (owner directive §3)",
        "tickers_processed": len(results),
        "succeeded": n_ok,
        "skipped": n_skip,
        "failed": n_fail,
        "results": results,
    }
    json.dump(manifest, open(manifest_path, "w"), indent=2, ensure_ascii=False, default=str)
    print(f"\nmanifest: {manifest_path}")


if __name__ == "__main__":
    main()
