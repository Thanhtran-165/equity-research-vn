#!/usr/bin/env python3
"""classify.py — heuristic PDF type classification for pdf-evidence v0.1.

Lightweight, no OCR. Estimates per-page text density to flag scanned pages,
and uses keyword heuristics to suggest doc_type.

Usage:
    python classify.py path/to/file.pdf [--json]

Output JSON:
    {
      "pdf_path": "...",
      "pages": [{"page": 1, "type": "digital_text", "char_count": 1234, "has_text_layer": true}, ...],
      "doc_type_guess": "digital_text" | "scanned" | "mixed" | "table_heavy" | "legal" | "financial" | "academic" | "policy" | "slide_export" | "low_quality_ocr",
      "reasons": ["..."],
      "warnings": []
    }
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Run: pip install pdfplumber", file=sys.stderr)
    sys.exit(2)


LEGAL_KEYWORDS = ["Điều", "Khoản", "Điểm", "Nghị định", "Thông tư", "Luật", "Quyết định", "căn cứ"]
FINANCIAL_KEYWORDS = ["Doanh thu", "LNST", "BCTC", "lợi nhuận", "biên", "roe", "roa", "VND", "tỷ đồng"]


def classify_page(page) -> dict:
    text = page.extract_text() or ""
    char_count = len(text.strip())
    has_text_layer = char_count > 0
    if char_count == 0:
        ptype = "scanned"
    elif char_count < 100:
        ptype = "low_quality_ocr"
    else:
        ptype = "digital_text"
    tables = page.extract_tables() or []
    return {
        "page": page.page_number,
        "type": ptype,
        "char_count": char_count,
        "has_text_layer": has_text_layer,
        "table_count": len(tables),
    }


def guess_doc_type(pages: list[dict], full_text: str) -> tuple[str, list[str], list[str]]:
    reasons: list[str] = []
    warnings: list[str] = []

    digital = sum(1 for p in pages if p["type"] == "digital_text")
    scanned = sum(1 for p in pages if p["type"] == "scanned")
    low_q = sum(1 for p in pages if p["type"] == "low_quality_ocr")
    table_total = sum(p["table_count"] for p in pages)

    if scanned > 0 and digital == 0:
        doc_type = "scanned"
        reasons.append(f"{scanned} scanned pages, 0 digital")
        warnings.append("Scan PDF — OCR not installed in v0.1; will need to abstain.")
    elif scanned > 0 and digital > 0:
        doc_type = "mixed"
        reasons.append(f"{digital} digital, {scanned} scanned")
        warnings.append("Mixed PDF — some pages may need OCR.")
    elif low_q > 0 and digital == 0:
        doc_type = "low_quality_ocr"
        reasons.append(f"{low_q} low-quality pages")
        warnings.append("Low-quality text — verify manually.")
    else:
        # digital — narrow by content
        if any(kw in full_text for kw in LEGAL_KEYWORDS):
            doc_type = "legal"
            reasons.append("legal keywords detected")
        elif any(kw in full_text for kw in FINANCIAL_KEYWORDS):
            doc_type = "financial"
            reasons.append("financial keywords detected")
        elif table_total >= 3:
            doc_type = "table_heavy"
            reasons.append(f"{table_total} tables detected")
        else:
            doc_type = "digital_text"
            reasons.append(f"{digital} digital pages, {table_total} tables")

    return doc_type, reasons, warnings


def main():
    ap = argparse.ArgumentParser(description="Classify PDF type (heuristic, no OCR).")
    ap.add_argument("pdf_path", help="Path to PDF")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    args = ap.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"ERROR: file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    pages_info: list[dict] = []
    full_text_parts: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            info = classify_page(page)
            pages_info.append(info)
            full_text_parts.append(page.extract_text() or "")

    full_text = "\n".join(full_text_parts)
    doc_type, reasons, warnings = guess_doc_type(pages_info, full_text)

    result = {
        "pdf_path": str(pdf_path),
        "pages": pages_info,
        "doc_type_guess": doc_type,
        "reasons": reasons,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"PDF: {pdf_path}")
        print(f"doc_type_guess: {doc_type}")
        print(f"reasons: {reasons}")
        if warnings:
            print("warnings:")
            for w in warnings:
                print(f"  - {w}")
        print(f"pages: {len(pages_info)}")


if __name__ == "__main__":
    main()
