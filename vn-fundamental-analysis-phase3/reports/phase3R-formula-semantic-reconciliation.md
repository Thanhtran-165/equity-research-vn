# Phase 3R Formula Semantic Reconciliation

**Date:** 2026-07-23

## Vấn đề

Phase 2 registry có 11 formulas. Trong đó `NET_PROFIT_MARGIN-v1.0.0` và `DUPONT-NPM-v1.0.0` có cùng:
- numerator: net_income_attributable_to_common
- denominator: revenue
- period relationship: annual / annual
- scope relationship: same scope

Khác nhau duy nhất: output unit (PERCENTAGE vs RATIO). Đây là **khác representation, không phải khác semantics**.

## Giải pháp: Phương án A

```yaml
canonical_formula:
  formula_id: NET_PROFIT_MARGIN-v1.0.0
  numerator: net_income_attributable_to_common
  denominator: revenue
  canonical_output: RATIO (0.12)
  display_output: PERCENTAGE (12.0%)
  
aliases:
  - alias_id: DUPONT_NPM_COMPONENT
    refers_to: NET_PROFIT_MARGIN-v1.0.0
    usage: "DuPont engine reads NET_PROFIT_MARGIN result as ratio form (no ×100)"
    does_not_recompute: true
```

DuPont engine tham chiếu kết quả `NET_PROFIT_MARGIN` thay vì tính lại.

## Formula registry cuối cùng

```yaml
canonical_formulas: 10
  1. EPS-BASIC-v1.0.0
  2. EPS-DILUTED-v1.0.0
  3. BVPS-v1.0.0
  4. ROE-v1.0.0
  5. ROA-v1.0.0
  6. NET_PROFIT_MARGIN-v1.0.0 (canonical ratio; DuPont uses this as component)
  7. DUPONT-AT-v1.0.0 (distinct: revenue / avg_total_assets)
  8. DUPONT-EM-v1.0.0 (distinct: avg_total_assets / avg_equity)
  9. DUPONT-ROE-CHECK-v1.0.0 (distinct: NPM × AT × EM)
  10. CAGR-v1.0.0

aliases: 1
  - DUPONT_NPM_COMPONENT → NET_PROFIT_MARGIN-v1.0.0 (no recompute)

duplicate_semantics: 0
omitted_phase1_formulas: 0
```

## Impact trên requirements

```yaml
changes:
  VFA-REQ-016 (was: DuPont NPM calculation):
    updated_to: "DuPont engine reads NET_PROFIT_MARGIN result (no separate recomputation)"
    formula_reference: NET_PROFIT_MARGIN-v1.0.0
    verifier_check: "verify DuPont NPM component == NET_PROFIT_MARGIN result (not recomputed)"
    
no_orphan_requirements: true
no_duplicate_verifier_recomputations: true
```

## Impact trên mutations

```yaml
mutation_reconciliation:
  removed: none
  updated:
    - MUT-FUND-015: "margin numerator changed to operating income" 
      → now targets NET_PROFIT_MARGIN (not a separate DUPONT-NPM)
      → expected_error: FORMULA_INPUT_DEFINITION_MISMATCH
  
  added_to_maintain_32:
    - MUT-FUND-032- replacement: "OPERATING_MARGIN vs NET_PROFIT_MARGIN confusion"
      severity: MAJOR
      expected_error: FORMULA_INPUT_DEFINITION_MISMATCH
      target: NET_PROFIT_MARGIN numerator (operating_income substituted for net_income)
  
  total_mutations: 32 (unchanged)
  formula_coverage: 10/10 canonical formulas
```

## Gate

```yaml
phase_3R_gate:
  canonical_formula_count: 10
  formula_IDs_unique: true
  duplicate_equations_with_same_semantics: 0
  omitted_phase1_formulas: 0
  aliases_documented: 1 (DUPONT_NPM_COMPONENT)
  
  requirements_mapped: "100% (33 requirements, VFA-REQ-016 updated)"
  verifier_formula_recomputations: "10 canonical + 0 aliases = 10 recomputations"
  formula_mutation_coverage: "10/10"
  
  mutations_designed: 32
  orphan_references: 0
  critical_design_ambiguities: 0
  
  implementation_changes: 0
  parent_changes: 0
  collector_changes: 0
  valuation_engine_changes: 0
  
  status: PASS
```
