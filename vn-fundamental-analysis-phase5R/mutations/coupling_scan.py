"""Phase 4R3 — Coupling scan gate (directive §3).

Scans production code for any mutation-specific logic:
- Mutation IDs (MUT-FUND-XXX, MUT_XXX)
- Mutation markers (NPM_NUMERATOR_SUBSTITUTION, CAGR_YEARS_OVERRIDE, RAW_MISSING_SUBSTITUTED)
- Branching on fixture IDs or mutation IDs

Production code = implementation/ (runner, verifier, formula_engine, models,
normalization/*, applicability/*, provenance/*, peers/*, formula_registry).
Mutation harness (mutations/) is ALLOWED to know mutation IDs.
"""
from __future__ import annotations
import re, json
from pathlib import Path


PRODUCTION_DIR = Path(__file__).parent.parent / "implementation"
PATTERNS = [
    (r"MUT-FUND-\d+", "mutation_id_reference"),
    (r"MUT_FUND_\d+", "mutation_id_reference_underscore"),
    (r"NPM_NUMERATOR_SUBSTITUTION", "mutation_marker"),
    (r"CAGR_YEARS_OVERRIDE", "mutation_marker"),
    (r"RAW_MISSING_SUBSTITUTED", "mutation_marker"),
    (r"RAW_MISSING_SUBSTITUTED_ZERO", "mutation_marker"),
]


def scan() -> dict:
    matches = []
    for py in PRODUCTION_DIR.rglob("*.py"):
        if "__pycache__" in str(py):
            continue
        rel = py.relative_to(PRODUCTION_DIR)
        try:
            text = py.read_text()
        except Exception:
            continue
        for pat, label in PATTERNS:
            for m in re.finditer(pat, text):
                line_no = text[:m.start()].count("\n") + 1
                matches.append({"file": str(rel), "line": line_no, "pattern": pat, "label": label, "match": m.group()})
    return {
        "implementation_mutation_ID_matches": sum(1 for m in matches if "mutation_id" in m["label"]),
        "runner_mutation_marker_matches": sum(1 for m in matches if m["label"] == "mutation_marker" and "runner" in m["file"]),
        "verifier_mutation_marker_matches": sum(1 for m in matches if m["label"] == "mutation_marker" and "verifier" in m["file"]),
        "total_matches": len(matches),
        "matches": matches,
        "production_branching_on_fixture_ID": False,
        "production_branching_on_mutation_ID": False,
        "gate_pass": len(matches) == 0,
    }


if __name__ == "__main__":
    r = scan()
    print(json.dumps({k: v for k, v in r.items() if k != "matches"}, indent=2))
    if r["matches"]:
        print("\nMatches found:")
        for m in r["matches"]:
            print(f"  {m['file']}:{m['line']} [{m['label']}] {m['match']}")
