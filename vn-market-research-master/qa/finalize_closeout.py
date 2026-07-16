#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "qa"
SITE = ROOT / "site"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def tree_digest(root: Path) -> tuple[str, dict[str, str]]:
    members = {
        str(path.relative_to(root)): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".vercel" not in path.parts
    }
    canonical = json.dumps(members, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(canonical), members


def main() -> None:
    parser = argparse.ArgumentParser(description="Finalize the governed master research website closeout.")
    parser.add_argument("--production-url", required=True)
    parser.add_argument("--deployment-id", required=True)
    args = parser.parse_args()

    editorial = load(ROOT / "editorial/17_editorial_audit.json")
    editorial_resume = load(ROOT / "editorial/19_final_resume_packet.json")
    static = load(QA / "site_audit.json")
    local_browser = load(QA / "browser_qa.json")
    production_browser = load(QA / "browser_qa.production.json")
    legacy_local = load(QA / "legacy_reports_qa.local.json")
    legacy_production = load(QA / "legacy_reports_qa.production.json")
    deployments = load(QA / "deployments_r3.json")
    claims = load(SITE / "data/claim_registry.json")
    sources = load(SITE / "data/source_manifest.json")
    report_data = load(SITE / "data/report_data.json")

    local_html = (SITE / "index.html").read_bytes()
    site_digest, site_members = tree_digest(SITE)
    corrected = next(item for item in claims["claims"] if item["claim_id"] == "A-CONTEMPORANEOUS")
    corrected_ids = corrected["sources"][0]["test_id_or_key"].split(",")

    gates = {
        "editorial_pass": editorial_resume["status"] == "PASS_CODEX_LONGFORM_R3_CLOSEOUT",
        "master_depth_pass": editorial["checks"]["master_word_count_15000_18000"],
        "child_depth_pass": editorial["checks"]["children_word_count_4000_6000"],
        "no_numeric_pooling": editorial["checks"]["no_numeric_pooling"],
        "no_causal_chain": editorial["checks"]["no_causal_chain"],
        "no_operational_overclaim": editorial["checks"]["no_operational_overclaim"],
        "duplicate_sentence_ratio_below_005": editorial["duplicate_sentence_ratio"] < 0.05,
        "static_audit_pass": static["status"] == "PASS_MASTER_RESEARCH_SITE_STATIC_AUDIT",
        "local_browser_pass": local_browser["status"] == "PASS_MASTER_RESEARCH_SITE_BROWSER_QA",
        "production_browser_pass": production_browser["status"] == "PASS_MASTER_RESEARCH_SITE_BROWSER_QA",
        "local_browser_failures_empty": local_browser["failures"] == [],
        "production_browser_failures_empty": production_browser["failures"] == [],
        "production_http_all_200": all(item["httpStatus"] == 200 for item in production_browser["results"]),
        "production_longform_link_contract": all(
            (item["specialistCount"] == 5 if item["route"] == "master" else item["externalReportCount"] == 1)
            for item in production_browser["results"]
        ),
        "legacy_local_backlink_qa": legacy_local["status"] == "PASS_LEGACY_REPORT_BACKLINK_BROWSER_QA",
        "legacy_production_backlink_qa": legacy_production["status"] == "PASS_LEGACY_REPORT_BACKLINK_BROWSER_QA",
        "six_production_deployments_recorded": len(deployments["deployments"]) == 6,
        "claim_coverage_complete": static["claim_coverage_complete"],
        "unresolved_claims_empty": claims["unresolved_claims"] == [],
        "source_manifest_no_local_paths": "/Users/" not in json.dumps(sources),
        "statistics_not_rerun": sources["statistics_rerun"] is False,
        "corrected_bond_headline_set": len(corrected_ids) == 7 and len(set(corrected_ids)) == 7,
        "no_confirmed_trading_signal": (
            report_data["bond"]["granger_survivors"] == 0
            and report_data["pvb"]["oos_stable"] is False
            and report_data["forecast"]["folds_better"] < 4
            and report_data["divergence"]["warning_candidates"] == 0
            and report_data["stock"]["descriptive_count"] == 0
        ),
    }
    failures = [name for name, passed in gates.items() if not passed]
    status = "PASS_VN_MARKET_RESEARCH_LONGFORM_R3_END_TO_END_CLOSEOUT" if not failures else "FAIL_VN_MARKET_RESEARCH_LONGFORM_R3_END_TO_END_CLOSEOUT"

    output = {
        "status": status,
        "production_url": args.production_url,
        "deployment_id": args.deployment_id,
        "html_sha256": sha256_bytes(local_html),
        "site_tree_sha256": site_digest,
        "site_file_count": len(site_members),
        "page_count": static["page_count"],
        "visual_count": static["visual_count"],
        "claim_count": static["claim_count"],
        "browser_checks_local": local_browser["checkCount"],
        "browser_checks_production": production_browser["checkCount"],
        "viewport_count": production_browser["viewportCount"],
        "legacy_browser_checks_local": legacy_local["checkCount"],
        "legacy_browser_checks_production": legacy_production["checkCount"],
        "word_counts": editorial["word_counts"],
        "corrected_bond_headline_test_ids": corrected_ids,
        "statistics_rerun": False,
        "gates": gates,
        "failures": failures,
    }
    (QA / "final_closeout.json").write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    summary = f"""# {status}

- Production: {args.production_url}
- Deployment: `{args.deployment_id}`
- Pages: {output['page_count']} (1 master + 5 chapters)
- Visuals: {output['visual_count']}
- Governed claims: {output['claim_count']}; unresolved: 0
- Browser QA: {output['browser_checks_local']} local + {output['browser_checks_production']} production checks across {output['viewport_count']} viewports
- HTML SHA256: `{output['html_sha256']}` (canonical local build deployed by recorded production deployment)
- Site tree SHA256: `{output['site_tree_sha256']}`
- Backlink QA: {output['legacy_browser_checks_local']} local + {output['legacy_browser_checks_production']} production checks
- Statistics rerun: no
- Central boundary: context and disagreement are supported; no independent stable out-of-sample trading signal is confirmed.
"""
    (QA / "FINAL_CLOSEOUT.md").write_text(summary)
    print(status)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
