# Phase 4Q Formula Inventory Reconciliation

**Date:** 2026-07-23

## 10 Canonical Formula IDs

```yaml
canonical_formulas:
  1. EPS-BASIC-v1.0.0
     numerator: net_income_attributable_to_common
     denominator: weighted_average_basic_shares
     output: VND_PER_SHARE
     basis: BASIC

  2. EPS-DILUTED-v1.0.0
     numerator: net_income_attributable_to_common
     denominator: weighted_average_diluted_shares
     output: VND_PER_SHARE
     basis: DILUTED
     note: "Different denominator from EPS-BASIC — different share count, different formula ID"

  3. BVPS-v1.0.0
     numerator: common_equity_attributable_to_ordinary
     denominator: period_end_ordinary_shares
     output: VND_PER_SHARE

  4. ROE-v1.0.0
     numerator: net_income_attributable
     denominator: average_common_equity
     output: PERCENTAGE

  5. ROA-v1.0.0
     numerator: net_income
     denominator: average_total_assets
     output: PERCENTAGE

  6. NET-PROFIT-MARGIN-v1.0.0
     numerator: net_income
     denominator: revenue
     output: RATIO (display as ×100 for percentage)

  7. DUPONT-AT-v1.0.0
     numerator: revenue
     denominator: average_total_assets
     output: RATIO
     note: "Different from ROA: ROA multiplies by 100, AT does not"

  8. DUPONT-EM-v1.0.0
     numerator: average_total_assets
     denominator: average_common_equity
     output: RATIO

  9. DUPONT-ROE-CHECK-v1.0.0
     equation: NPM × AT × EM (multiplicative identity check)
     inputs: [NET_PROFIT_MARGIN result, DUPONT-AT result, DUPONT-EM result]
     output: RATIO
     note: "Consistency check, not independent formula — reads other results"

  10. CAGR-v1.0.0
      equation: (ending/beginning)^(1/years) - 1
      output: RATIO

aliases:
  DUPONT_NPM_COMPONENT:
    refers_to: NET-PROFIT-MARGIN-v1.0.0
    recomputation: false
    usage: "DuPont engine reads NPM result; does NOT call a separate formula"

NOT_in_registry:
  OPERATING_MARGIN:
    status: "Not implemented in Phase 4 — would need operating_income input from collector"
    note: "If added in future, it would be formula #11 with different numerator (operating_income vs net_income)"
```

## Reconciliation answers

```yaml
Q: BASIC and DILUTED EPS — two formula IDs or two basis of one?
A: Two formula IDs (EPS-BASIC-v1.0.0 and EPS-DILUTED-v1.0.0).
   Different denominators (weighted_average_basic_shares vs weighted_average_diluted_shares).
   Different output values for same company. Legitimately distinct.

Q: Is OPERATING_MARGIN in the 10 canonical formulas?
A: No. OPERATING_MARGIN is not implemented. The 10 formulas are listed above.
   If added later, it would be #11 with numerator=operating_income (different from net_income).

Q: What are the "DuPont×4"?
A: DUPONT-AT (asset turnover), DUPONT-EM (equity multiplier),
   DUPONT-ROE-CHECK (reconstructed ROE), and the NPM alias reference.
   Note: NPM is NOT a DuPont formula — it's standalone. DuPont reads its result.

Q: Any duplicate semantics?
A: No. Each formula has distinct numerator/denominator/equation.
   NPM and DuPont-NPM are the SAME formula (alias), not duplicates.
```

## Gate

```yaml
P4Q_A_gate:
  candidate_commit_verified: true (7c6a465c5)
  canonical_formula_count: 10
  formula_IDs_unique: true
  duplicate_semantics: 0
  omitted_formulas: 0
  alias_recomputations: 0
  status: PASS
```
