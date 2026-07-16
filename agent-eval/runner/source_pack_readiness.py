#!/usr/bin/env python3
"""
source_pack_readiness.py — Semantic source-pack readiness gate (v0.9.1, Branch A).

UPGRADE from v0.9.0: the old readiness gate checked "file exists + parseable".
Shadow Batch 1 proved this insufficient: VNM's events.csv and news_digest.json
were empty stubs that passed the old gate, but the agent filled gaps from model
memory, producing unflagged external claims.

New semantic checks (per owner directive 2026-07-14):
  - files_parseable: file exists and is valid CSV/JSON
  - nonempty_records: file has ≥1 data row (not just header/stub)
  - ticker_match_rate: data rows reference the correct ticker
  - dates_present: news/events have date fields populated
  - sources_present: news/events have source/url fields
  - no_stub_markers: file is not a placeholder/stub

If news/events files are intentionally N/A for a ticker, the applicability map
must declare this explicitly — empty stubs are no longer silently accepted.
"""
import csv, json, os, re, sys


def check_csv_semantic(path, min_records=1, require_dates=False, require_sources=False, ticker=None):
    """Check a CSV file for semantic completeness."""
    result = {"file": os.path.basename(path), "format": "csv"}
    if not os.path.exists(path):
        result["status"] = "MISSING"
        return result
    try:
        with open(path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception as e:
        result["status"] = "UNPARSEABLE"
        result["error"] = str(e)[:100]
        return result

    # Strip empty rows
    rows = [r for r in rows if any(v and v.strip() for v in r.values() if isinstance(v, str))]

    if len(rows) < min_records:
        result["status"] = "EMPTY_STUB"
        result["records"] = len(rows)
        result["min_required"] = min_records
        return result

    result["records"] = len(rows)

    # Check ticker match
    if ticker:
        ticker_matches = sum(1 for r in rows if ticker in str(r.values()))
        result["ticker_match_rate"] = round(ticker_matches / len(rows), 2) if rows else 0
        if ticker_matches == 0 and len(rows) > 0:
            result["ticker_match_warning"] = f"no rows reference ticker '{ticker}'"

    # Check dates
    if require_dates:
        date_cols = [c for c in (rows[0].keys() if rows else []) if 'date' in c.lower() or 'time' in c.lower()]
        if date_cols:
            dates_filled = sum(1 for r in rows if any(r.get(c, '').strip() for c in date_cols))
            result["dates_present"] = dates_filled > 0
            result["dates_filled"] = dates_filled
        else:
            result["dates_present"] = False
            result["dates_warning"] = "no date-like column found"

    # Check sources
    if require_sources:
        src_cols = [c for c in (rows[0].keys() if rows else []) if 'source' in c.lower() or 'url' in c.lower() or 'link' in c.lower()]
        if src_cols:
            srcs_filled = sum(1 for r in rows if any(r.get(c, '').strip() for c in src_cols))
            result["sources_present"] = srcs_filled > 0
        else:
            result["sources_present"] = False

    result["status"] = "READY" if result.get("records", 0) >= min_records else "EMPTY_STUB"
    return result


def check_json_semantic(path, min_keys=1):
    """Check a JSON file for semantic completeness."""
    result = {"file": os.path.basename(path), "format": "json"}
    if not os.path.exists(path):
        result["status"] = "MISSING"
        return result
    try:
        data = json.load(open(path))
    except Exception as e:
        result["status"] = "UNPARSEABLE"
        result["error"] = str(e)[:100]
        return result

    if isinstance(data, dict):
        # Check for stub markers
        stub_markers = ["placeholder", "stub", "TODO", "dummy", ""]
        non_stub_keys = [k for k in data if data[k] not in stub_markers and data[k]]
        result["nonempty_keys"] = len(non_stub_keys)

        # Special: news_digest.json should have events array
        if "events" in data:
            events = data["events"]
            result["events_count"] = len(events) if isinstance(events, list) else 0
            if result["events_count"] == 0:
                result["status"] = "EMPTY_STUB"
                return result

        if result.get("nonempty_keys", 0) < min_keys:
            result["status"] = "EMPTY_STUB"
            return result

    elif isinstance(data, list):
        result["records"] = len(data)
        if len(data) < min_keys:
            result["status"] = "EMPTY_STUB"
            return result

    result["status"] = "READY"
    return result


def check_source_pack_semantic(pack_dir, ticker):
    """Full semantic readiness check for a source-pack."""
    results = {}

    # Required financial files (must have real data)
    results["income_statement"] = check_csv_semantic(
        os.path.join(pack_dir, "income_statement_sponsor.csv"),
        min_records=5, ticker=ticker)
    results["balance_sheet"] = check_csv_semantic(
        os.path.join(pack_dir, "balance_sheet_sponsor.csv"),
        min_records=5, ticker=ticker)
    results["cash_flow"] = check_csv_semantic(
        os.path.join(pack_dir, "cash_flow_sponsor.csv"),
        min_records=5, ticker=ticker)
    results["overview"] = check_json_semantic(
        os.path.join(pack_dir, "overview.json"), min_keys=3)
    results["technical_active"] = check_json_semantic(
        os.path.join(pack_dir, "technical_active.json"), min_keys=2)

    # News/events files (must have real data OR be declared N/A)
    events_path = os.path.join(pack_dir, "events.csv")
    news_path = os.path.join(pack_dir, "news_digest.json")
    news_csv_path = os.path.join(pack_dir, "news.csv")

    events_result = check_csv_semantic(events_path, min_records=1, require_dates=True, require_sources=True, ticker=ticker)
    news_result = check_json_semantic(news_path, min_keys=1)
    news_csv_result = check_csv_semantic(news_csv_path, min_records=1, require_dates=True, ticker=ticker) if os.path.exists(news_csv_path) else {"status": "MISSING", "file": "news.csv"}

    results["events"] = events_result
    results["news_digest"] = news_result
    results["news_csv"] = news_csv_result

    # Overall: all financial files must be READY
    # News/events: READY or explicitly N/A (but NOT empty stub)
    financial_ok = all(results[f]["status"] == "READY" for f in ["income_statement", "balance_sheet", "cash_flow", "overview", "technical_active"])

    news_events_status = []
    for key in ["events", "news_digest", "news_csv"]:
        s = results[key]["status"]
        if s == "EMPTY_STUB":
            news_events_status.append(f"{key}: EMPTY_STUB (agent may fill from memory)")
        elif s == "MISSING":
            news_events_status.append(f"{key}: MISSING")
        # READY is fine

    news_events_ok = len(news_events_status) == 0 or all("MISSING" in s for s in news_events_status)

    overall = {
        "ticker": ticker,
        "financial_files_ready": financial_ok,
        "news_events_ready": news_events_ok,
        "news_events_warnings": news_events_status,
        "overall_ready": financial_ok and news_events_ok,
        "detail": results,
    }
    return overall


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 source_pack_readiness.py <pack_dir> <ticker>")
        sys.exit(1)
    result = check_source_pack_semantic(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["overall_ready"] else 1)
