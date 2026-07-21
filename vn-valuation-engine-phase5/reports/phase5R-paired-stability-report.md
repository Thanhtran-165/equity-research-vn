# Phase 5R Paired Stability Report

**Date:** 2026-07-21
**Status:** PASS (5/5 ticker pairs methods_equal)

## Per-ticker pair analysis

| Ticker | methods_equal | market_snapshot | fin snapshot | verifier_verdict_equal | difference_class |
|---|---|---|---|---|---|
| VCB | ✓ | differ (ts) | differ (ts) | ✓ | SOURCE_DATA_CHANGED_BUT_OUTPUT_STABLE |
| BVH | ✓ | differ | differ | ✓ | SOURCE_DATA_CHANGED_BUT_OUTPUT_STABLE |
| HPG | ✓ | differ | differ | ✓ | SOURCE_DATA_CHANGED_BUT_OUTPUT_STABLE |
| MWG | ✓ | differ | differ | ✓ | SOURCE_DATA_CHANGED_BUT_OUTPUT_STABLE |
| FPT | ✓ | differ | differ | ✓ | SOURCE_DATA_CHANGED_BUT_OUTPUT_STABLE |

## Difference classification

```yaml
SOURCE_DATA_CHANGED_BUT_OUTPUT_STABLE: 5  # timestamps differ; financial values identical in 10s window
SOURCE_DATA_UNCHANGED_OUTPUT_STABLE: 0    # would require same snapshot
SOURCE_DATA_UNCHANGED_OUTPUT_DRIFT: 0     # defect case — not observed
SOURCE_SHAPE_CHANGED: 0
ENVIRONMENT_DRIFT: 0
```

## Required paired stability (Directive Phase 5R §8)

```yaml
required:
  canonical_inputs_semantically_equal: true (5/5)
  applicability_equal: true (5/5)
  formula_results_equal: true (5/5)
  verifier_verdict_equal: true (5/5)

unexplained_output_drift: 0
explained_or_stable: 5/5
```

## Deterministic replay

```yaml
snapshots_replayed: 10/10
semantic_output_hash_stable: 10/10
verifier_verdict_stable: 10/10

non_deterministic_fields_ignored:
  - execution timestamp
  - runtime duration
  - generated run ID
  - request_id
```

Replay proves engine is deterministic: same frozen request → identical output (semantic hash identical 10/10).

## Conclusion

Paired stability PASS. Deterministic replay PASS. Engine is deterministic across retrievals within a 10-second window — methods results identical 5/5, semantic hash stable 10/10.
