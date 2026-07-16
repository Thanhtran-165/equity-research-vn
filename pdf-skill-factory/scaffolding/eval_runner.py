#!/usr/bin/env python3
"""eval_runner.py — mini eval harness for pdf-evidence v0.1.

Reads fixtures from scaffolding/fixtures/*/case.json, expects a sibling
skill_output.json (the skill's actual output for that case), computes metrics
via metrics.py, writes a report.

Usage:
    python eval_runner.py                       # run all fixtures
    python eval_runner.py --fixture 01_text_qa  # run one fixture
    python eval_runner.py --report results/latest_report.json

NOTE on LLM-judge (PATCH 3 + PATCH 4):
faithfulness and hallucination_rate return -1.0 in v0.1 because the
groundedness_judge.md LLM call is not wired. The runner prints a warning.
DoD gates on these metrics only when they are >= 0 (i.e. judge is wired).
For v0.1, DoD v0.1 threshold table treats them as advisory.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = SCRIPT_DIR / "fixtures"
RESULTS_DIR = SCRIPT_DIR / "results"

sys.path.insert(0, str(SCRIPT_DIR))
from metrics import compute_all  # noqa: E402


# DoD v0.1 thresholds (mirror DEFINITION_OF_DONE.md)
DOD_V01 = {
    "citation_format_accuracy": 0.95,
    "citation_page_accuracy": 0.90,
    "abstention_accuracy": 0.90,
    "table_fidelity": 0.85,
    "coverage": 0.75,
    # LLM-judge metrics — only enforced when value >= 0 (judge wired)
    "hallucination_rate_max": 0.10,  # special: <= threshold
    "faithfulness": 0.85,
}

# DoD v0.2.0 thresholds (mirror proposals/v0.2.0/03-V0.2.0_EVAL_PLAN.md)
DOD_V02 = {
    "partial_abstention_accuracy": 0.90,
    "abstention_visibility": 1.0,     # = top_level (binary)
    "abstention_quality": 0.90,
    "table_handling": 0.90,
    "table_cell_accuracy": 0.90,      # N/A tolerated (None)
    "table_header_preservation": 0.90,
    "table_unit_preservation": 0.95,
    "table_uncertainty_disclosed": 1.0,
}


def load_case(case_dir: Path) -> dict:
    case_file = case_dir / "case.json"
    if not case_file.exists():
        raise FileNotFoundError(f"case.json missing in {case_dir}")
    return json.loads(case_file.read_text(encoding="utf-8"))


def load_skill_output(case_dir: Path) -> dict | None:
    out_file = case_dir / "skill_output.json"
    if not out_file.exists():
        return None
    return json.loads(out_file.read_text(encoding="utf-8"))


def evaluate_one(case_dir: Path) -> dict:
    case = load_case(case_dir)
    skill_out = load_skill_output(case_dir)

    fixture_id = case.get("id", case_dir.name)

    if skill_out is None:
        return {
            "id": fixture_id,
            "pass": False,
            "error": f"skill_output.json not found in {case_dir}; cannot evaluate. "
                     f"Run the skill on this fixture first and save output as skill_output.json.",
            "metrics": {},
        }

    expected = case.get("expected", {})
    evidence_pages = {e.get("page") for e in (skill_out.get("evidence") or []) if e.get("page") is not None}
    metrics = compute_all(skill_out, expected, evidence_pages)

    # When the skill correctly abstains, there are no claims and therefore no
    # citations to grade — citation metrics are vacuously satisfied.
    abstained = bool(skill_out.get("abstention_flag"))
    citations = skill_out.get("citations") or []

    pass_flags = []
    if not (abstained and not citations):
        if "citation_format_accuracy" in metrics and citations:
            pass_flags.append(metrics["citation_format_accuracy"] >= DOD_V01["citation_format_accuracy"])
        if "citation_page_accuracy" in metrics and expected.get("expected_citations"):
            pass_flags.append(metrics["citation_page_accuracy"] >= DOD_V01["citation_page_accuracy"])
    pass_flags.append(metrics["abstention_accuracy"] >= DOD_V01["abstention_accuracy"])
    if expected.get("expected_table") is not None and not abstained:
        pass_flags.append(metrics["table_fidelity"] >= DOD_V01["table_fidelity"])

    # LLM-judge metrics — only enforce if wired (>= 0)
    if metrics.get("faithfulness", -1.0) >= 0:
        pass_flags.append(metrics["faithfulness"] >= DOD_V01["faithfulness"])
    if metrics.get("hallucination_rate", -1.0) >= 0:
        pass_flags.append(metrics["hallucination_rate"] <= DOD_V01["hallucination_rate_max"])

    # v0.2.0 metrics — apply threshold when the fixture exercises the metric
    # partial abstention (group A)
    if expected.get("partial_abstention_expected") or skill_out.get("partial_abstentions"):
        pass_flags.append(metrics["partial_abstention_accuracy"] >= DOD_V02["partial_abstention_accuracy"])
        pass_flags.append(metrics["abstention_visibility"] >= DOD_V02["abstention_visibility"])
    # table wiring (group B) — when an expected_table is present
    if expected.get("expected_table") is not None and not abstained:
        pass_flags.append(metrics["table_handling"] >= DOD_V02["table_handling"])
        pass_flags.append(metrics["table_header_preservation"] >= DOD_V02["table_header_preservation"])
        pass_flags.append(metrics["table_unit_preservation"] >= DOD_V02["table_unit_preservation"])
        cell = metrics.get("table_cell_accuracy")
        if cell is not None:  # N/A tolerated when None
            pass_flags.append(cell >= DOD_V02["table_cell_accuracy"])
    # chart/table_id expected
    if expected.get("expected_table_id_prefix") or expected.get("expected_chart_id_prefix"):
        pass_flags.append(metrics["table_handling"] >= DOD_V02["table_handling"])
    # uncertainty disclosure (B.5)
    if expected.get("expected_table_uncertainty_disclosure"):
        pass_flags.append(metrics["table_uncertainty_disclosed"] >= DOD_V02["table_uncertainty_disclosed"])

    return {
        "id": fixture_id,
        "pass": all(pass_flags),
        "metrics": metrics,
    }


def main():
    ap = argparse.ArgumentParser(description="Eval harness for pdf-evidence.")
    ap.add_argument("--fixture", default=None, help="Run only this fixture (dir name)")
    ap.add_argument("--report", default=str(RESULTS_DIR / "latest_report.json"),
                    help="Path to write JSON report")
    args = ap.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if args.fixture:
        case_dirs = [FIXTURES_DIR / args.fixture]
        if not case_dirs[0].exists():
            print(f"ERROR: fixture not found: {case_dirs[0]}", file=sys.stderr)
            sys.exit(1)
    else:
        case_dirs = sorted(d for d in FIXTURES_DIR.iterdir() if d.is_dir() and (d / "case.json").exists())

    if not case_dirs:
        print("No fixtures found. Run scaffolding/fixtures/build_fixtures.py first.", file=sys.stderr)
        sys.exit(1)

    per_fixture = []
    for d in case_dirs:
        result = evaluate_one(d)
        per_fixture.append(result)
        status = "PASS" if result["pass"] else "FAIL"
        print(f"[{status}] {result['id']}")
        if result.get("error"):
            print(f"        {result['error']}")
        for k, v in (result.get("metrics") or {}).items():
            print(f"        {k}: {v:.3f}" if isinstance(v, float) else f"        {k}: {v}")

    overall_pass = all(r["pass"] for r in per_fixture)
    n_total = len(per_fixture)
    n_pass = sum(1 for r in per_fixture if r["pass"])

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version_tested": "0.1.0",
        "fixtures_evaluated": n_total,
        "fixtures_passed": n_pass,
        "regression_pass_rate": n_pass / n_total if n_total else 0.0,
        "dod_pass": overall_pass,
        "per_fixture": per_fixture,
        "note": "LLM-judge (faithfulness, hallucination_rate) returned -1.0 = not wired in v0.1. "
                "Use groundedness_judge.md to compute these for release decisions (PATCH 4). "
                "faithfulness_simple is a baseline heuristic only (PATCH 3).",
    }

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReport written: {report_path}")
    print(f"DoD pass: {overall_pass}  ({n_pass}/{n_total} fixtures passed)")

    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
