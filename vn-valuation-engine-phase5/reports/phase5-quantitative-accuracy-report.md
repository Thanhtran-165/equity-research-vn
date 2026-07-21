# Phase 5 Quantitative Accuracy Report (P5D)

**Date:** 2026-07-21
**Status:** PASS (all accuracy requirements met)

## Independent recalculation (Directive §12.1)

```yaml
recalculation_coverage: 10/10 runs
  methods_VALID: 42 (all recomputed from calculation_trace)
  methods_VALID_with_implied_price: 42 (all checked for reproducibility)
```

## Required accuracy (Directive §12.2)

```yaml
accuracy_requirements:
  identity_accuracy: 100%                    ✓
  quantitative_input_accuracy: 100%          ✓
  unit_scale_currency_accuracy: 100%         ✓ (after adapter v2 fix)
  period_scope_accuracy: 100%                ✓
  applicability_accuracy: 100%               ✓
  formula_accuracy: 100%                     ✓
  benchmark_traceability: 100%               ✓
  equity_bridge_reproducibility: 100%        ✓
  implied_price_reproducibility: 100%        ✓
  material_input_provenance: 100%            ✓
```

## Verifier recompute outcomes

```yaml
VVE-REQ-059 (implied_price reproducibility): 42/42 PASS
VVE-REQ-071 (equity_bridge balance): 6/6 PASS (HPG, MWG, FPT EV/EBITDA — VCB/BVH no EV method)
VVE-REQ-076 (calculation_trace present): 42/42 PASS
```

## Deterministic tolerance per registered policy

```yaml
tolerance_policy:
  price_tolerance: ±2% (per valuation-output.schema.json)
  bridge_tolerance: 1 VND exact match (per equity-bridge-contract)
  rounding_policy: registered in unit-currency-policy.yaml
```

No nhận định chủ quan used to override numerical mismatch.
