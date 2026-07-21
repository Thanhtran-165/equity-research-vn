# Phase 5 Source Preflight Report (P5B)

**Date:** 2026-07-21
**Status:** PASS (5/5 tickers preflighted)

## Required live data per Directive §7.1

### Identity
```yaml
identity_resolved: 5/5
  VCB: ticker + company + exchange + sector ✓ (banking)
  BVH: ticker + company + exchange + sector ✓ (insurance)
  HPG: ticker + company + exchange + sector ✓ (steel)
  MWG: ticker + company + exchange + sector ✓ (retail)
  FPT: ticker + company + exchange + sector ✓ (technology)
```

### Market data
```yaml
market_data_resolved: 5/5
  price: 5/5 (close from Trading.price_history)
  price_date: 5/5 (all 2026-07-20)
  currency: 5/5 (VND implicit)
```

### Financial data
```yaml
financial_data_resolved: 5/5
  reporting_period: 5/5 (year)
  revenue_or_operating_income: 3/5 (VCB, BVH = None — banking/insurance structure)
  net_profit_or_attributable_profit: 5/5 (Net profit after tax)
  equity: 5/5 (Owner's Equity)
  shares_outstanding: 5/5 (from Trading.total_shares)
```

### Conditional data
```yaml
conditional_data:
  EBITDA_or_required_EV_metric: 3/5 (HPG, MWG, FPT — computed from Operating profit + D&A)
  debt: 3/5 (Short-term + Long-term borrowings)
  cash: 5/5 (Cash and cash equivalents)
  minority_interest: 3/5 (HPG, MWG, FPT — consolidated entities)
  preferred_equity: 0/5 (none reported by these tickers)
  peer_or_historical_multiple_inputs: 5/5 (historical benchmark registered in formula_registry)
```

Conditional data unavailable không bắt buộc cho mọi ticker. Engine xử lý theo applicability contract (NOT_APPLICABLE status).

## Source evidence (Directive §7.2)

```yaml
source_snapshots_created: 5/5
  mỗi snapshot có:
    - source_name
    - retrieval_timestamp (UTC ISO)
    - ticker
    - endpoint_or_method
    - raw_payload_hash (SHA-256)
    - raw_payload_location
    - records_received
    - source_error (None)

secret_leaks: 0
cross_ticker_source_mix: 0
manual_value_injection: 0
```

## vnstock API notes

- Community tier: 60 requests/phút
- Rate limit encountered during initial cohort run → retry logic với backoff
- Re-run với 8s delay giữa runs avoided rate limit
- vnstock returns raw VND values (NOT millions) — critical for adapter design
