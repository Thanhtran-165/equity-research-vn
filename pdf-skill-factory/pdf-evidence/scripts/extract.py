#!/usr/bin/env python3
"""extract.py — pdfplumber wrapper for pdf-evidence v0.2.0.

v0.2.0 changes (TABLE-WIRING-001):
- Global table_id scheme: p{N}.t{i}  (page-prefixed, unique within document)
- Global chart_id scheme: p{N}.c{i}  (image-region pages without ruled grid)
- units inferred from headers via regex
- period inferred from headers via regex
- parse_confidence per table (1.0 clean / 0.5 null headers / 0.3 merged or sparse)
- table_uncertainty_disclosure=true when parse_confidence < 0.7

Usage:
    python extract.py path/to/file.pdf [--json] [--alias report_2026]

The page field is MANDATORY — skills MUST cite page when using this evidence.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Run: pip install pdfplumber", file=sys.stderr)
    sys.exit(2)


# Regexes for units + period inference from header text
UNIT_PATTERNS = [
    # Accept both proper Vietnamese and ASCII-degraded forms. pdfplumber on some
    # reportlab fonts strips diacritics: "tỷ VNĐ" → "tn VNn", "triệu" → "trieu".
    (r"(?:tn|t[ỷy])\s*(?:VN[nĐD]?|đồng)?", "tỷ VNĐ"),
    (r"(?:trieu|tri[ệe]u)\s*(?:VN[nĐD]?|đồng)?", "triệu VNĐ"),
    (r"(?:nghan|ngh[àa]n)\s*(?:VN[nĐD]?|đồng)?", "nghìn VNĐ"),
    (r"\bUSD\b", "USD"),
    (r"\bEUR\b", "EUR"),
    (r"\boz\b|ounce", "oz"),
    (r"\btonnes?\b", "tonnes"),
    (r"\bbn\b|billion", "bn"),
    (r"\btrn\b|trillion", "trn"),
    (r"%", "%"),
]
PERIOD_PATTERNS = [
    r"Q[1-4]/?\d{4}",
    r"FY\s*\d{4}",
    r"\b\d{4}\b",
    r"tháng\s*\d+",
    r"Q[1-4]\b",
]


def _infer_units(headers: list) -> str | None:
    """Infer the dominant unit from header text."""
    text = " ".join(str(h) for h in (headers or []) if h)
    if not text:
        return None
    for pat, unit in UNIT_PATTERNS:
        if re.search(pat, text, re.I):
            return unit
    return None


def _infer_period(headers: list) -> str | None:
    """Infer period(s) from header text, joined by '; '."""
    text = " ".join(str(h) for h in (headers or []) if h)
    if not text:
        return None
    found = []
    for pat in PERIOD_PATTERNS:
        m = re.findall(pat, text, re.I)
        # findall may return tuples for grouped patterns; coerce to str
        for g in m:
            s = g if isinstance(g, str) else " ".join(x for x in g if x)
            if s and s not in found:
                found.append(s)
    return "; ".join(found) if found else None


def _has_null_or_empty(headers: list) -> bool:
    return any(h is None or (isinstance(h, str) and h.strip() == "") for h in (headers or []))


def _is_sparse_or_merged(rows: list) -> bool:
    """Heuristic: row lengths inconsistent OR many empty cells → merged/sparse."""
    if not rows:
        return False
    widths = {len(r) for r in rows}
    if len(widths) > 1:
        return True
    total_cells = sum(len(r) for r in rows)
    empty = sum(1 for r in rows for c in (r or []) if c is None or (isinstance(c, str) and c.strip() == ""))
    return total_cells > 0 and (empty / total_cells) > 0.3


def _parse_confidence(headers: list, rows: list) -> float:
    """Heuristic parse confidence: 1.0 clean, 0.5 null headers, 0.3 merged/sparse."""
    if _has_null_or_empty(headers):
        return 0.5
    if _is_sparse_or_merged(rows):
        return 0.3
    return 1.0


def _detect_chart(page, page_num: int) -> list[dict]:
    """Heuristic chart detection: page has images but no/few ruled tables.

    v0.2.0 uses a simple heuristic — a 'chart' is an image-bearing page whose
    detected tables are empty or trivial. Returns chart_id list.
    """
    images = page.images or []
    if not images:
        return []
    # If page has real ruled tables, those take precedence (handled by caller).
    # Here we surface chart_id only when images exist; the caller decides whether
    # to also have table_ids.
    charts = []
    for i, _img in enumerate(images, start=1):
        charts.append({
            "chart_id": f"p{page_num}.c{i}",
            "page": page_num,
            "chart_type": "image_region",
            "title": None,  # could be inferred from nearest heading in a future version
            "parse_confidence": 0.4,  # charts: lower confidence than tables
            "table_uncertainty_disclosure": True,
        })
    return charts


def extract_page(page, page_num: int) -> dict:
    text = page.extract_text() or ""
    raw_tables = page.extract_tables() or []
    tables = []
    for i, t in enumerate(raw_tables, start=1):
        if not t:
            continue
        headers = list(t[0]) if t else []
        rows = [list(r) for r in t[1:]] if len(t) > 1 else []
        units = _infer_units(headers)
        period = _infer_period(headers)
        confidence = _parse_confidence(headers, rows)
        tables.append({
            "table_id": f"p{page_num}.t{i}",
            "page": page_num,
            "headers": headers,
            "rows": rows,
            "units": units,
            "period": period,
            "parse_confidence": confidence,
            "table_uncertainty_disclosure": confidence < 0.7,
        })
    charts = _detect_chart(page, page_num)
    return {
        "page": page_num,
        "text": text,
        "char_count": len(text.strip()),
        "tables": tables,
        "charts": charts,
    }


def main():
    ap = argparse.ArgumentParser(description="Extract text + tables with page anchors (v0.2.0).")
    ap.add_argument("pdf_path", help="Path to PDF")
    ap.add_argument("--alias", default=None, help="Document alias (for citations)")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    args = ap.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"ERROR: file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    pages_out: list[dict] = []
    warnings: list[str] = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            page_num = page.page_number
            info = extract_page(page, page_num)
            pages_out.append(info)
            if info["char_count"] == 0:
                warnings.append(f"Page {page_num} has no text layer — may be scanned (OCR not installed in v0.2.0).")
            for tbl in info["tables"]:
                tid = tbl["table_id"]
                if tbl["units"] is None:
                    warnings.append(f"Table {tid} on p.{page_num} could not infer units from headers — verify manually.")
                if tbl["period"] is None:
                    warnings.append(f"Table {tid} on p.{page_num} could not infer period from headers — verify manually.")
                if tbl["table_uncertainty_disclosure"]:
                    warnings.append(f"Table {tid} on p.{page_num} has uncertain parse (confidence={tbl['parse_confidence']}) — verify manually.")
            for ch in info["charts"]:
                warnings.append(f"Chart {ch['chart_id']} on p.{page_num} detected as image region — values are approximate; verify against source visual.")

    alias = args.alias or pdf_path.stem
    result = {
        "pdf_path": str(pdf_path),
        "alias": alias,
        "schema_version": "0.2.0",
        "pages": pages_out,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"PDF: {pdf_path} (alias: {alias})")
        print(f"pages: {len(pages_out)}")
        total_tables = sum(len(p["tables"]) for p in pages_out)
        total_charts = sum(len(p["charts"]) for p in pages_out)
        print(f"tables: {total_tables} | charts: {total_charts}")
        if warnings:
            print("warnings:")
            for w in warnings:
                print(f"  - {w}")


if __name__ == "__main__":
    main()
