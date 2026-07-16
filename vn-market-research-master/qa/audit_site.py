#!/usr/bin/env python3
"""Fail-closed static audit for the generated research website."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
QA = ROOT / "qa"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    pages = [SITE / "index.html", *sorted((SITE / "chapters").glob("*.html"))]
    registry = json.loads((SITE / "data/claim_registry.json").read_text())
    source_manifest = json.loads((SITE / "data/source_manifest.json").read_text())
    claim_ids = {c["claim_id"] for c in registry["claims"]}
    failures: list[str] = []
    page_results = {}
    all_claim_refs = set()
    visual_count = 0

    if len(pages) != 6:
        failures.append(f"page_count={len(pages)}")
    if len(claim_ids) != len(registry["claims"]):
        failures.append("duplicate_claim_ids")
    if registry.get("unresolved_claims"):
        failures.append("unresolved_claims")

    for page in pages:
        raw = page.read_text()
        soup = BeautifulSoup(raw, "html.parser")
        ids = [tag.get("id") for tag in soup.find_all(attrs={"id": True})]
        toc_targets = [a.get("href", "")[1:] for a in soup.select(".page-toc a") if a.get("href", "").startswith("#")]
        refs = {a.get_text(strip=True) for a in soup.select("a.claim-ref")}
        all_claim_refs |= refs
        visuals = len(soup.select(".data-visual"))
        visual_count += visuals
        checks = {
            "one_h1": len(soup.find_all("h1")) == 1,
            "unique_ids": len(ids) == len(set(ids)),
            "toc_targets_exist": all(target in ids for target in toc_targets),
            "claim_refs_resolve": refs <= claim_ids,
            "technical_collapsed": all(not d.has_attr("open") for d in soup.select("details.technical")),
            "no_markdown_tokens": not bool(re.search(r"^#{1,4}\s|\*\*[^*]+\*\*", soup.get_text(), re.M)),
            "no_local_path": "/Users/bobo" not in raw and "file://" not in raw,
            "has_visual": visuals >= 1,
            "has_description": bool(soup.select_one('meta[name="description"]')),
            "report_link_contract": (
                len(soup.select(".specialist-card")) == 5
                if page.name == "index.html" and page.parent == SITE
                else len(soup.select(".external-report-link a")) == 1
            ),
        }
        if not all(checks.values()):
            failures.append(f"{page.name}:{[k for k,v in checks.items() if not v]}")
        page_results[str(page.relative_to(SITE))] = {"checks": checks, "toc_links": len(toc_targets), "claim_refs": sorted(refs), "visuals": visuals, "sha256": sha(page)}

    public_text = "\n".join(BeautifulSoup(p.read_text(), "html.parser").get_text(" ", strip=True) for p in pages)
    forbidden_assertions = [
        r"khối lượng dự báo (?:được )?giá",
        r"khối lượng xác nhận xu hướng",
        r"phân kỳ (?:là|tạo) tín hiệu (?:mua|bán)",
        r"bond (?:dẫn|dự báo) thị trường",
        r"chắc chắn không (?:có|tồn tại) hiệu ứng",
    ]
    overclaim_hits = []
    for pattern in forbidden_assertions:
        for match in re.finditer(pattern, public_text, re.I):
            prefix = public_text[max(0, match.start() - 140):match.start()].lower()
            if re.search(r"(?:không|chưa|không được|không thể)\b[^.!?]{0,125}$", prefix):
                continue
            overclaim_hits.append(pattern)
            break
    if overclaim_hits:
        failures.append(f"overclaim_hits={overclaim_hits}")

    source_path_leaks = []
    for item in source_manifest["sources"].values():
        if item.get("path") or str(item.get("artifact", "")).startswith("/"):
            source_path_leaks.append(item)
    if source_path_leaks:
        failures.append("source_manifest_path_leak")
    if source_manifest.get("statistics_rerun") is not False:
        failures.append("statistics_rerun_not_false")

    source_hash_lengths = all(len(item["sha256"]) == 64 for item in source_manifest["sources"].values())
    if not source_hash_lengths:
        failures.append("source_hash_length")
    if all_claim_refs != claim_ids:
        failures.append(f"claim_coverage_missing={sorted(claim_ids-all_claim_refs)}")

    css = (SITE / "assets/styles.css").read_text()
    js = (SITE / "assets/site.js").read_text()
    if "/Users/bobo" in css + js:
        failures.append("asset_local_path_leak")

    result = {
        "status": "PASS_MASTER_RESEARCH_SITE_STATIC_AUDIT" if not failures else "FAIL_MASTER_RESEARCH_SITE_STATIC_AUDIT",
        "failures": failures,
        "page_count": len(pages),
        "visual_count": visual_count,
        "claim_count": len(claim_ids),
        "claim_coverage_complete": all_claim_refs == claim_ids,
        "source_hash_lengths_64": source_hash_lengths,
        "overclaim_hits": overclaim_hits,
        "pages": page_results,
    }
    (QA / "site_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(result["status"])
    if failures:
        print("\n".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
