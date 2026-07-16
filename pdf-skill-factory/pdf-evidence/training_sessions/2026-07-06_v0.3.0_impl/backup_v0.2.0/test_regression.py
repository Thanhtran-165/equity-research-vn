"""test_regression.py — pytest regression suite for pdf-evidence.

Runs the eval_runner over all fixtures and asserts that each one passes the
DoD v0.1 thresholds. If a fixture's skill_output.json is missing, the test is
SKIPPED (not failed) so that the suite can run in environments where only a
subset of fixtures have outputs.

Usage:
    pytest scaffolding/tests/test_regression.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCAFFOLDING_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = SCAFFOLDING_DIR / "fixtures"
sys.path.insert(0, str(SCAFFOLDING_DIR))

from metrics import compute_all  # noqa: E402

DOD_V01 = {
    "citation_format_accuracy": 0.95,
    "citation_page_accuracy": 0.90,
    "abstention_accuracy": 0.90,
    "table_fidelity": 0.85,
}

DOD_V02 = {
    "partial_abstention_accuracy": 0.90,
    "abstention_visibility": 1.0,
    "abstention_quality": 0.90,
    "table_handling": 0.90,
    "table_cell_accuracy": 0.90,
    "table_header_preservation": 0.90,
    "table_unit_preservation": 0.95,
    "table_uncertainty_disclosed": 1.0,
}


def _discover_fixtures() -> list[Path]:
    if not FIXTURES_DIR.exists():
        return []
    return sorted(
        d for d in FIXTURES_DIR.iterdir()
        if d.is_dir() and (d / "case.json").exists()
    )


FIXTURE_DIRS = _discover_fixtures()


def _load(fixture_dir: Path) -> tuple[dict, dict | None]:
    case = json.loads((fixture_dir / "case.json").read_text(encoding="utf-8"))
    out_file = fixture_dir / "skill_output.json"
    skill_out = json.loads(out_file.read_text(encoding="utf-8")) if out_file.exists() else None
    return case, skill_out


@pytest.mark.parametrize("fixture_dir", FIXTURE_DIRS, ids=lambda d: d.name)
def test_fixture_passes_dod(fixture_dir):
    case, skill_out = _load(fixture_dir)
    assert skill_out is not None, (
        f"skill_output.json missing in {fixture_dir}. "
        f"Run build_fixtures.py for baseline, or run the real skill and save its output."
    )

    expected = case.get("expected", {})
    evidence_pages = {
        e.get("page") for e in (skill_out.get("evidence") or []) if e.get("page") is not None
    }
    metrics = compute_all(skill_out, expected, evidence_pages)

    # Assert DoD v0.1 thresholds
    assert metrics["abstention_accuracy"] >= DOD_V01["abstention_accuracy"], (
        f"abstention_accuracy {metrics['abstention_accuracy']:.3f} < "
        f"{DOD_V01['abstention_accuracy']}"
    )

    abstained = bool(skill_out.get("abstention_flag"))
    citations = skill_out.get("citations") or []
    if citations and not abstained:
        assert metrics["citation_format_accuracy"] >= DOD_V01["citation_format_accuracy"], (
            f"citation_format_accuracy {metrics['citation_format_accuracy']:.3f} < "
            f"{DOD_V01['citation_format_accuracy']}"
        )

    if expected.get("expected_citations") and not abstained:
        assert metrics["citation_page_accuracy"] >= DOD_V01["citation_page_accuracy"], (
            f"citation_page_accuracy {metrics['citation_page_accuracy']:.3f} < "
            f"{DOD_V01['citation_page_accuracy']}"
        )

    if expected.get("expected_table") is not None and not abstained:
        assert metrics["table_fidelity"] >= DOD_V01["table_fidelity"], (
            f"table_fidelity {metrics['table_fidelity']:.3f} < "
            f"{DOD_V01['table_fidelity']}"
        )

    # v0.2.0 gates — partial abstention
    if expected.get("partial_abstention_expected") or skill_out.get("partial_abstentions"):
        assert metrics["partial_abstention_accuracy"] >= DOD_V02["partial_abstention_accuracy"], (
            f"partial_abstention_accuracy {metrics['partial_abstention_accuracy']:.3f} < "
            f"{DOD_V02['partial_abstention_accuracy']}"
        )
        assert metrics["abstention_visibility"] >= DOD_V02["abstention_visibility"], (
            f"abstention_visibility {metrics['abstention_visibility']:.3f} < top_level (1.0)"
        )

    # v0.2.0 gates — table wiring
    if expected.get("expected_table") is not None and not abstained:
        assert metrics["table_handling"] >= DOD_V02["table_handling"], (
            f"table_handling {metrics['table_handling']:.3f} < {DOD_V02['table_handling']}"
        )
        assert metrics["table_header_preservation"] >= DOD_V02["table_header_preservation"], (
            f"table_header_preservation {metrics['table_header_preservation']:.3f} < "
            f"{DOD_V02['table_header_preservation']}"
        )
        assert metrics["table_unit_preservation"] >= DOD_V02["table_unit_preservation"], (
            f"table_unit_preservation {metrics['table_unit_preservation']:.3f} < "
            f"{DOD_V02['table_unit_preservation']}"
        )
        cell = metrics.get("table_cell_accuracy")
        if cell is not None:
            assert cell >= DOD_V02["table_cell_accuracy"], (
                f"table_cell_accuracy {cell:.3f} < {DOD_V02['table_cell_accuracy']}"
            )

    # v0.2.0 gates — table_id / chart_id expected
    if (expected.get("expected_table_id_prefix") or expected.get("expected_chart_id_prefix")) and not abstained:
        assert metrics["table_handling"] >= DOD_V02["table_handling"], (
            f"table_handling (id branch) {metrics['table_handling']:.3f} < "
            f"{DOD_V02['table_handling']}"
        )

    # v0.2.0 gates — uncertainty disclosure
    if expected.get("expected_table_uncertainty_disclosure"):
        assert metrics["table_uncertainty_disclosed"] >= DOD_V02["table_uncertainty_disclosed"], (
            f"table_uncertainty_disclosed {metrics['table_uncertainty_disclosed']:.3f} < 1.0"
        )

    # If answer is expected, the answer_contains strings must appear
    if not expected.get("abstention_expected") and expected.get("answer_contains"):
        answer = skill_out.get("answer", "") or ""
        for needle in expected["answer_contains"]:
            assert needle in answer, (
                f"expected answer to contain '{needle}', got: {answer!r}"
            )

    # If abstention expected, no forbidden fabricated numbers
    if expected.get("abstention_expected"):
        answer = skill_out.get("answer", "") or ""
        for forbidden in expected.get("answer_not_contains", []):
            assert forbidden not in answer, (
                f"abstention case leaked '{forbidden}' into answer: {answer!r}"
            )


def test_at_least_5_fixtures_present():
    """PATCH 2 — minimum 5 fixtures (v0.1.1); v0.2.0 requires ≥ 13."""
    assert len(FIXTURE_DIRS) >= 13, (
        f"Expected >= 13 fixtures (v0.2.0), found {len(FIXTURE_DIRS)}. "
        f"Run: python scaffolding/fixtures/build_fixtures.py"
    )


def test_no_outside_knowledge_when_pdf_only():
    """PATCH 6 — when pdf_only=true, outside_knowledge_used must be False."""
    for fixture_dir in FIXTURE_DIRS:
        case, skill_out = _load(fixture_dir)
        if skill_out is None:
            continue
        constraint = case.get("constraint", {})
        if constraint.get("pdf_only", True):
            assert skill_out.get("outside_knowledge_used") is False, (
                f"{fixture_dir.name}: outside_knowledge_used must be False "
                f"when constraint.pdf_only=true (PATCH 6)"
            )
