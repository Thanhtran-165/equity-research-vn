# Protocol Comparison: v0.1.0 vs v0.2.0

**Date:** 2026-07-21

## What changed

| Aspect | v0.1.0 | v0.2.0 |
|---|---|---|
| MUT-VALUATION-001 oracle | "Corrupt one P/E value" (1-position) | MULTI_POSITION_SEMANTIC_CORRUPTION (≥3 positions; actual 9) |
| Materiality rule | implicit | explicit (>50% relative AND >1.0 absolute) |
| Majority-vote semantics | implicit verifier behavior | explicit oracle contract field |
| Mutation count | 5 | 6 (5 originals + MUT-VALUATION-002 positive control) |
| Clean control count | 1 | 1 (unchanged) |
| Hard gate definitions | 17 | 17 (unchanged) |
| Weights | PRS 0.25/0.35/0.40 | same |
| Maturity thresholds | unchanged | unchanged |
| Target skill | unchanged | unchanged (505 files byte-for-byte) |
| Target verifier | unchanged | unchanged |
| Backward pooling | n/a | NOT ALLOWED |

## Outcomes

| Metric | v0.1.0 | v0.2.0 | Delta |
|---|---|---|---|
| Mutations caught | 4/5 (1 oracle defect) | 6/6 (0 defects) | +2 caught, -1 oracle defect |
| correct_detection_rate | 0.8 | 1.0 | +0.2 |
| missed_critical_defects | 1 | 0 | -1 |
| Hard gates PASS | 15/17 | 17/17 | +2 |
| HG-011 | FAIL | PASS | resolved |
| HG-VALIDATOR-MISSED-CRITICAL | FAIL | PASS | resolved |
| SCS | 66.45 (MEDIUM) | 100.0 (HIGH) | +33.55 |
| target_verification_layer | FUNCTIONAL | ROBUST | upgraded |
| overall_target_skill | FUNCTIONAL | FUNCTIONAL | unchanged (capped by zero agent runs) |
| production_ready_supported | false | false | unchanged (needs agent evidence) |
| Phase 6 vn-valuation-engine | blocked (parent oracle gap) | UNBLOCKED | ready for owner directive |

## Why v0.2.0 was needed

Per protocol immutability (HG-PROTOCOL-IMMUTABLE), once v0.1.0 was frozen, the MUT-VALUATION-001 oracle could not be strengthened mid-audit. The correct procedure was:

1. Preserve v0.1.0 results as historical evidence (FAIL verdict immutable).
2. Create new protocol version v0.2.0 with strengthened oracle.
3. Re-freeze.
4. Re-audit cleanly.
5. Do NOT pool v0.1.0 and v0.2.0 results.

This procedure was followed. v0.2.0 is an independent audit with its own scorecard, manifests, and verdict.

## What v0.2.0 did NOT change

- Target skill: unchanged (505 files byte-for-byte)
- Target verifier: unchanged (independent_verifier.py byte-for-byte)
- Target requirements: unchanged
- Hard gate definitions: 17 gates unchanged
- Maturity thresholds: unchanged
- Weights: unchanged
- 4 of 5 original mutation oracles: unchanged (only MUT-VALUATION-001 strengthened)
- Specificity outcome: unchanged (1.0 in both versions)

## Conclusion

v0.2.0 successfully closes the v0.1.0 specification gap. The audit now supports:
- `target_verification_layer`: ROBUST (was FUNCTIONAL)
- Phase 6 vn-valuation-engine parent integration: UNBLOCKED (was blocked by parent oracle gap)
- `production_ready_supported`: still false (needs agent evidence — separate gap)
