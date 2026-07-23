# Phase 3 Formula Denominator Reconciliation

**Date:** 2026-07-23

## Formula count reconciliation

```yaml
phase_1_formula_count: 10
phase_2_formula_count: 11
difference: +1

reason: |
  Phase 1 listed "ROS" (Return on Sales) as a single formula with numerator=NPAT.
  Phase 2 recognized that "ROS" is ambiguous — it could mean either:
    - NET_PROFIT_MARGIN (NPAT / Revenue)
    - OPERATING_MARGIN (Operating Income / Revenue)

  Phase 2 resolved this by:
    1. Renaming the NPAT/Revenue formula canonically as NET_PROFIT_MARGIN-v1.0.0
       (formula_id: NET-PROFIT-MARGIN-v1.0.0)
    2. Adding DuPont-NPM-v1.0.0 as a SEPARATE formula (ratio form, not percentage)
       because DuPont uses ratio (0.098) while standalone margin uses percentage (9.8%)

  This is NOT a duplicate:
    - NET_PROFIT_MARGIN-v1.0.0 outputs PERCENTAGE (×100)
    - DUPONT-NPM-v1.0.0 outputs RATIO (no ×100)
    - Different output_unit, different downstream consumers
    - Different formula_ids

phase_1_formulas_omitted: 0
duplicate_equations_with_same_semantics: 0

mapping:
  Phase_1_F-005_ROS → Phase_2_NET-PROFIT-MARGIN-v1.0.0 (renamed, same equation ×100)
  Phase_1_F-006_NPM → Phase_2_DUPONT-NPM-v1.0.0 (kept as ratio form for DuPont)
```

## Conclusion

Formula count increase from 10→11 is justified by taxonomy clarification (percentage vs ratio form of same economic concept). No formulas omitted, no duplicates. All 11 formula IDs are unique.
