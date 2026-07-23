"""Phase 4R — Reproducibility harness (P4R-G).

Replays the 16 fixtures twice and confirms semantic hashes are stable.
Strips timestamps, durations, and runtime-only IDs from the comparison.
"""
from __future__ import annotations
import sys, json, hashlib, copy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "implementation"))
sys.path.insert(0, str(Path(__file__).parent))

from models import FundamentalRequest, MetricInput
from runner import run_fundamental
from verifier.independent_verifier import verify
from fixture_registry import FIXTURES_CLEAN, FIXTURES_FAILURE


def _semantic_hash(output_dict: dict) -> str:
    """Hash the semantically-meaningful subset of the output."""
    # Strip runtime-only fields
    stripped = copy.deepcopy(output_dict)
    # Remove timestamps, durations from evidence_manifest (not present in output_dict directly)
    # Keep metric_results, dupont, growth, peer_comparison, quality_summary, downstream_export, errors
    payload = {
        "metric_results": stripped.get("metric_results", []),
        "dupont": stripped.get("dupont"),
        "growth": stripped.get("growth", {}),
        "peer_comparison": {k: v for k, v in stripped.get("peer_comparison", {}).items()
                           if k not in ("peer_set_hash",)},
        "quality_summary": stripped.get("quality_summary", {}),
        "downstream_export": stripped.get("downstream_export", {}),
        "errors": stripped.get("errors", []),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()[:16]


def run_fixture_twice(name, factory):
    """Run a fixture twice; return (hash1, hash2, verdict1, verdict2)."""
    req1 = factory()
    res1 = run_fundamental(req1)
    vr1 = verify(req1, res1.output)

    req2 = factory()
    res2 = run_fundamental(req2)
    vr2 = verify(req2, res2.output)

    h1 = _semantic_hash(res1.output.to_dict())
    h2 = _semantic_hash(res2.output.to_dict())
    return {
        "fixture_id": name,
        "run1_hash": h1,
        "run2_hash": h2,
        "hash_stable": h1 == h2,
        "run1_verdict": vr1.overall_verdict,
        "run2_verdict": vr2.overall_verdict,
        "verdict_stable": vr1.overall_verdict == vr2.overall_verdict,
    }


def main():
    print("=== P4R-G Reproducibility (16 fixtures × 2 runs) ===\n")
    results = []
    all_fixtures = {**FIXTURES_CLEAN, **FIXTURES_FAILURE}
    for name, factory in all_fixtures.items():
        r = run_fixture_twice(name, factory)
        results.append(r)
        status = "STABLE" if r["hash_stable"] and r["verdict_stable"] else "DRIFT"
        print(f"  {name:35} -> {status}  hash1={r['run1_hash']} hash2={r['run2_hash']} verdict={r['run1_verdict']}")

    stable = sum(1 for r in results if r["hash_stable"] and r["verdict_stable"])
    print(f"\n=== Summary ===")
    print(f"Fixtures stable (hash + verdict): {stable}/16")

    manifest = {
        "phase4R_reproducibility_manifest": {
            "fixtures": 16,
            "repetitions": 2,
            "stable_count": stable,
            "results": results,
            "stripped_fields": ["timestamp", "duration_seconds", "execution_log"],
        }
    }
    Path(__file__).parent.parent / "manifests" / "phase4R-reproducibility-manifest.json"
    out = Path(__file__).parent.parent / "manifests" / "phase4R-reproducibility-manifest.json"
    out.write_text(json.dumps(manifest, indent=2, default=str))
    print(f"\nManifest: {out}")
    return stable


if __name__ == "__main__":
    stable = main()
    sys.exit(0 if stable == 16 else 1)
