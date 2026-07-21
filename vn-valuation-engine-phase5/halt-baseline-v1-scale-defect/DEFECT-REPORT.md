# P5C HALT — Scale Error Defect (Safety Stop)

**Timestamp:** 2026-07-21
**Trigger:** Directive §11 Safety Stop — `scale_error_with_material_valuation_impact`
**Severity:** CRITICAL
**Source component:** source-adapter/vnstock_adapter.py (Phase 5 NEW component)

## Observation

After P5C cohort ran 10 genuine runs, independent verification caught the defect:

```yaml
HPG-run-A: FAIL (EQUITY_BRIDGE_INVALID)
HPG-run-B: FAIL (EQUITY_BRIDGE_INVALID)
MWG-run-A: FAIL (EQUITY_BRIDGE_INVALID)
MWG-run-B: FAIL (EQUITY_BRIDGE_INVALID)
FPT-run-A: FAIL (EQUITY_BRIDGE_INVALID)
FPT-run-B: FAIL (EQUITY_BRIDGE_INVALID)
VCB-run-A: PASS (no EV-based method)
VCB-run-B: PASS (no EV-based method)
BVH-run-A: PASS (no EV-based method)
BVH-run-B: PASS (no EV-based method)
```

## Root cause

The `vnstock_adapter.py` set `scale=Scale.MILLION` for raw VND values from vnstock.
However, vnstock returns values already in raw VND (e.g., FPT EBITDA = 4.96e12 VND).
When the unit_currency_engine normalizes "MILLION scale" → UNIT, it multiplies by 1e6,
producing EBITDA = 4.96e18 (one million times the true value).

This caused:
- EV (EBITDA × 10x) = 4.96e19 (should be 4.96e13)
- equity_value = 4.43e19 (should be 4.43e13)
- implied_price = 25.84B VND per share (should be ~25,800 VND)

The bridge "balances" mathematically (sum is consistent) but the entire scale is wrong.
The verifier catches this via VVE-REQ-071 because bridge_balanced is None on reconstruction
(independent recompute rejects the corrupted scale).

## Classification

- **Bucket:** ENFORCEMENT (source adapter enforcement failure)
- **Sub-bucket (9-sub):** 3B — Verifier evidence-provenance (this is where the verifier proves its value)
- **Component owner:** SOURCE_ADAPTER (Phase 5 new component, not in Phase 4 freeze)
- **Engine/runner/verifier:** UNCHANGED (not patched — this is the source adapter, a separate layer)

## Why this is a SAFETY STOP (not just FAIL)

Per Directive §11:
```yaml
scale_error_with_material_valuation_impact: any
```

This is exactly that — scale error × 1M produced material impact (implied_price 25.8B VND vs reality 25.8K VND).

**However**, no actual `target_price` was emitted as production output (the engine FAILed the gate),
and the verifier caught it. So the system is fail-safe — this is recorded as DEFECT_FOUND_AND_CAUGHT.

## Why the engine is correct (not the defect)

The defect is in the source adapter (Phase 5 new component, not in Phase 4 frozen implementation).
The runner, engines, and verifier all worked as designed:
- unit_currency_engine.py: correctly multiplied by 1M when scale=MILLION
- equity_bridge_engine.py: correctly computed bridge from given inputs
- independent_verifier.py: correctly caught the imbalance via recompute

The adapter violates the implicit contract "raw vnstock values are in VND UNIT, not MILLION scale".

## Preserved artifacts

- artifacts/ — all 10 runs (raw + outputs + verification)
- manifests/ — all phase 5 manifests up to halt point
- source-snapshots/ — all raw vnstock payloads

## Remediation plan

1. Fix vnstock_adapter.py: change Scale.MILLION → Scale.UNIT for VND raw values
2. Re-run cohort from preserved raw snapshots (replay mode) to verify fix
3. Re-execute genuine retrieval for paired stability test (2 fresh runs per ticker)

## Phase 4 status

Phase 4 standalone_maturity: PROTOTYPE_OPERATIONAL — UNCHANGED.
The defect is in Phase 5 source adapter, not in Phase 4 frozen implementation.
