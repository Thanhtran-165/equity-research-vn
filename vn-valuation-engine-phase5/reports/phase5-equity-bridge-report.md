# Phase 5 Equity Bridge Report

**Date:** 2026-07-21
**Status:** PASS (6/6 bridges balanced per VVE-REQ-071)

## Equity bridge usage

6 EV/EBITDA methods emitted bridges (HPG, MWG, FPT — 2 runs each = 6 total). VCB and BVH không có EV-based method nên không có bridge.

## Bridge structure per equity-bridge-contract.yaml

Mỗi bridge có 6 items theo sign convention:
- EV (+)
- NET_DEBT (-)
- PREFERRED_EQUITY (-)
- MINORITY_INTEREST (-)
- NON_OPERATING_INVESTMENTS (+)
- EQUITY_VALUE (=)

## FPT example (representative)

```yaml
FPT EV/EBITDA bridge (run-A):
  EV:                          49,645,231,586,620 VND (+)
  NET_DEBT:                     3,039,934,965,907 VND (-)
  MINORITY_INTEREST:            2,301,851,329,197 VND (-)
  PREFERRED_EQUITY:                            0 VND (-)
  NON_OPERATING_INVESTMENTS:                   0 VND (+)
  EQUITY_VALUE:                44,303,445,291,516 VND (=)

balances: true
balance_check: PASS (sum of signed items = EQUITY_VALUE)
```

## MUT-F5 verification (rule_BR3)

```yaml
minority_interest_included: 3/3 tickers (HPG, MWG, FPT)
minority_above_5pct_EV_threshold: 0/3
  HPG: 0.10% EV
  MWG: 0.01% EV
  FPT: 4.64% EV (just under 5% — engine includes conservatively per rule_BR3.3 "optional but flag")

unsafe_omission: 0  # All non-zero minorities included
unsafe_false_pass: 0
```

## Bridge balance accuracy

```yaml
VVE-REQ-071 (bridge balances): 6/6 PASS
tolerance: 1 VND exact match
imbalance_cases: 0
```
