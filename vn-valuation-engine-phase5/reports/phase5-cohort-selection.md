# Phase 5 Cohort Selection Report

**Date:** 2026-07-21

## 5 tickers chosen (frozen before any valuation run per Directive §6.3)

| Ticker | Sector category | Why | Method coverage |
|---|---|---|---|
| VCB | BANK_OR_FINANCIAL | Banking — PB preferred, EV/EBITDA NOT_APPLICABLE | PE, PB, Graham (input incomplete cho banking) |
| BVH | INSURANCE_OR_SECURITIES | Insurance — revenue structure khác, P_S NOT_APPLICABLE | PE, P_CF |
| HPG | INDUSTRIAL_OR_CYCLICAL | Steel/cyclical — EV-based preferred | All 6 (PE, PB, Graham, EV/EBITDA, P/CF, P/S) |
| MWG | CONSUMER_RETAIL_OR_CONGLOMERATE | Retail conglomerate — PEG, multi-segment consolidated | All 6 |
| FPT | TECHNOLOGY_OR_SERVICES | Tech — PE/PEG growth; minority interest 2.30T VND (MUT-F5 case) | All 6 |

## Sector coverage (Directive §6.3)

```yaml
sector_coverage:
  1_BANK_OR_FINANCIAL: VCB ✓
  2_INSURANCE_OR_SECURITIES: BVH ✓
  3_INDUSTRIAL_OR_CYCLICAL: HPG ✓
  4_CONSUMER_RETAIL_OR_CONGLOMERATE: MWG ✓
  5_TECHNOLOGY_OR_SERVICES: FPT ✓

coverage_complete: 5/5
```

## Special coverage (Directive §6.3)

```yaml
special_coverage:
  nonzero_or_material_minority_interest_case: "≥1 ticker → HPG, MWG, FPT (3 tickers ✓)"
  shares_outstanding_cross_checkable: "5/5 tickers ✓"
  positive_earnings_case: "≥3 tickers → 5/5 ✓"
  method_not_applicable_case: "≥1 ticker → VCB (EV/EBITDA), BVH (P_S) ✓"
  EV_based_method_case: "≥1 ticker → HPG, MWG, FPT ✓"
  peer_or_historical_benchmark_case: "≥2 tickers → all 5 have historical benchmark ✓"
```

## MUT-F5/F7 coverage targets

```yaml
MUT_F5_coverage_planned: true
  tickers: HPG, MWG, FPT (consolidated entities with minority interest on balance sheet)
  FPT đặc biệt quan trọng: minority = 2.30T VND = 4.64% EV (threshold boundary case)

MUT_F7_coverage_planned: true
  tickers: all 5 (shares × price = market_cap cross-check via vnstock)
```

## Selection constraints honored

```yaml
ticker_substitution_after_freeze: PROHIBITED (none done)
ticker_substitution_after_results_seen: PROHIBITED (none done)
patch_during_cohort: PROHIBITED (none done — adapter fix was pre-re-run, not patch to engines)
manual_value_injection: PROHIBITED (none done)
parent_runtime_fallback: PROHIBITED (none done)
```
