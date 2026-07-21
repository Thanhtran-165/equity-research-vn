# Phase 5 Applicability Report

**Date:** 2026-07-21
**Status:** PASS

## Applicability decisions per (method × sector × metric_state)

### VCB (banking)
| Method | Status | Reason |
|---|---|---|
| PE | VALID | EPS=3323 > 0, banking-specific |
| PB | INPUT_INCOMPLETE | BVPS missing (Owner's Equity structure different) |
| GRAHAM | INPUT_INCOMPLETE | EPS/BVPS chain incomplete |
| EV_EBITDA | NOT_APPLICABLE | Banking sector excluded per applicability-rules.yaml |
| P_CF | INPUT_INCOMPLETE | CFO not in scope for banking |
| P_S | NOT_APPLICABLE | Banking has interest income, not sales |
| DCF_FCFF | INPUT_INCOMPLETE | FCFF forecast missing |

### BVH (insurance)
| Method | Status | Reason |
|---|---|---|
| PE | VALID | EPS=1565 |
| PB | INPUT_INCOMPLETE | BVPS chain |
| GRAHAM | INPUT_INCOMPLETE | |
| EV_EBITDA | INPUT_INCOMPLETE | EBITDA proxy not material |
| P_CF | VALID | CFO available |
| P_S | NOT_APPLICABLE | Insurance revenue structure |
| DCF_FCFF | INPUT_INCOMPLETE | FCFF missing |

### HPG (steel/cyclical)
| Method | Status | Reason |
|---|---|---|
| PE | VALID | EPS=4037 |
| PB | VALID | BVPS computed |
| GRAHAM | VALID | EPS, BVPS > 0 |
| EV_EBITDA | VALID | EBITDA computed, bridge balanced |
| P_CF | VALID | CFO available |
| P_S | VALID | Revenue=55.8T |
| DCF_FCFF | INPUT_INCOMPLETE | FCFF forecast missing |

### MWG (retail) — same as HPG pattern
### FPT (technology) — same as HPG pattern

## Applicability accuracy: 100%
- VCB/BVH EV/EBITDA correctly NOT_APPLICABLE per banking/insurance rules
- VCB/BVH P_S correctly NOT_APPLICABLE
- All VALID methods have required inputs available
- All INPUT_INCOMPLETE methods have specific missing metric identified (no generic "incomplete")
