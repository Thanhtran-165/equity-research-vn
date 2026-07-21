# ERVN-PERIOD-001 — Hotfix Design Document
**Candidate:** `equity-research-vn-1.0.1`
**Status:** DRAFT 2026-07-18
**Author:** Hardening program (post-forensic-audit)

## 1. Goal

Eliminate the period-inversion defect in `build_data_contract.py` and add a
verifier-side gate that prevents any future recurrence. The defect must be
provably fixed — not just patched — because the v1.0.0 verifier was unable
to detect it.

## 2. Root cause

```python
# build_data_contract.py (v1.0.0, line 238-239, 253, 265)
for i, row in enumerate(inc[:5]):           # latest 5 rows (row 0 = 2025, row 1 = 2024, ...)
    yr = str(years_asc[4-i])
```

The comment claims CSV is descending (row 0 = latest). The actual vnstock sponsor
CSV format is **ascending** (row 0 = oldest). Result: oldest period's value gets
assigned to latest period label.

## 3. Why positional mapping is forbidden going forward

CSVs from vnstock sponsor endpoints do **not** have an explicit year column.
All year rows have `report_period = "year"`. The only way to know which row is
which year is:

(a) An external period-labeled source (ratios.csv column headers, fundamental_sponsor.json `years` key, or vnstock API call), OR
(b) A positional assumption about row ordering.

Option (b) is fragile because vnstock has changed CSV ordering in past releases
and may again. The hotfix must use (a).

## 4. Period-key resolver design

### 4.1 Input contract

```yaml
period_key_resolver:
  inputs:
    income_statement_sponsor_csv: required
    balance_sheet_sponsor_csv:    required
    cash_flow_sponsor_csv:        required
    ratios_csv:                   optional (community format with period-labeled columns)
    fundamental_sponsor_json:     optional (sponsor JSON with explicit 'years' key)

  output:
    period_index:                 # explicit, year-keyed
      "2021": {row_indices: {income: 0, balance: 0, cash: 0}}
      "2022": {row_indices: {income: 1, balance: 1, cash: 1}}
      ...
      "2025": {row_indices: {income: 4, balance: 4, cash: 4}}
    chronological_order:          # detected, not assumed
      - "2021"
      - "2022"
      ...
      - "2025"
    detection_method:             # which source was used
      one_of: [explicit_json_years, explicit_csv_column_headers, value_diff_consistency]
    confidence: high|medium|low
```

### 4.2 Resolution strategy (in priority order)

**Strategy 1 — EXPLICIT_JSON_YEARS (preferred):**
If `fundamental_sponsor.json` exists with `years` key, use those labels.
Cross-check: `fundamental_sponsor.json:years` count must equal count of year-rows
in CSV. If mismatch → fail.

```python
if os.path.exists(fundamental_sponsor_json):
    fs = json.load(fundamental_sponsor_json)
    explicit_years = fs.get("years", [])
    if len(explicit_years) == len(year_rows):
        # Use fs["data"][year] values directly — they're already period-labeled
        detection_method = "explicit_json_years"
```

**Strategy 2 — EXPLICIT_CSV_COLUMN_HEADERS:**
If `ratios.csv` exists with column headers like `2021`, `2022`, ... use those.
The CSV row with `item_en = "year"` gives the year numbers per column.

**Strategy 3 — VALUE_DIFF_CONSISTENCY (fallback):**
When no explicit period-labeled source is available, use this 3-source
cross-check:

```text
For both possible orderings (ascending vs descending) of CSV rows:
  1. Build the financials dict under that assumption
  2. Run a consistency check: does the latest year's EPS × shares
     approximately equal latest year's net profit? (accounting identity)
  3. Does equity[year] / shares ≈ BVPS reported by overview/market data?
  4. Does revenue trend match sector growth direction? (sector-aware sanity)

The ordering that produces internally consistent accounting identities wins.
If both orderings pass consistency (possible for monotonic companies), FAIL —
require explicit period labeling.
```

### 4.3 Fail-closed rules

```yaml
resolver_fail_closed:
  - duplicate_periods_detected:        FAIL_PERIOD_DUPLICATE
  - missing_period_label:              FAIL_PERIOD_LABEL_MISSING
  - unparseable_period:                FAIL_PERIOD_UNPARSEABLE
  - mixed_annual_quarterly_in_year_rows: FAIL_PERIOD_MIXED_FREQUENCY
  - both_orderings_pass_consistency:   FAIL_PERIOD_AMBIGUOUS_REQUIRES_EXPLICIT_SOURCE
  - inconsistent_across_statements:    FAIL_PERIOD_CROSS_STATEMENT_MISMATCH
                                       # if income says row 0 = 2021 but balance says row 0 = 2025
  - positional_only_assumption:        FAIL_PERIOD_POSITIONAL_FORBIDDEN
```

NO fallthrough to positional mapping. If period labels cannot be determined
explicitly, build aborts.

## 5. period_integrity_gate (new gate)

```yaml
period_integrity_gate:
  sub_checks:
    raw_periods_unique:                # all 5 period labels distinct
      required: true
    values_length_matches_periods:     # array length == period count
      required: true
    period_order_detected:             # resolver returned a chronological_order
      required: true
      forbidden_values: [null, "POSITIONAL"]
    explicit_period_value_pairs_preserved:   # every (period, value) survives the round-trip
      required: true
    latest_period_matches_source:      # contract's latest period value == raw source's latest period value
      required: true
      tolerance_pct: 0.1
    oldest_period_matches_source:      # same for oldest
      required: true
      tolerance_pct: 0.1

  fields_checked:                      # PER FIELD, not aggregate
    - revenue
    - net_profit
    - eps
    - total_assets
    - total_equity
    - capex
    - operating_cash_flow

  failure_mode: FAIL_PERIOD_PROVENANCE_INCOMPLETE
```

## 6. Verifier augmentation

Add a new REQ to `requirements.yaml`:

```yaml
- id: REQ-PERIOD-INTEGRITY
  severity: critical
  description: |
    Every (period, value) pair in the rendered artifact must match the
    corresponding (period, value) pair in the raw source CSV. Period-inversion
    defects (oldest value labeled as latest period) must FAIL.
  verification:
    method: period_value_pair_comparison
    sources:
      - raw CSV (income/balance/cash-flow sponsor)
      - verified-dashboard-data.json
      - data/financials.json
    rules:
      - for each (period, field) pair:
          raw_value = lookup via period_key_resolver
          contract_value = verified-dashboard-data.financials[field][period_index]
          artifact_value = parsed from rendered HTML DATA object
          all three must match within tolerance
      - set-equality (same numbers, different order) is NOT sufficient
  regression_fixture: ERVN-PERIOD-001-fixture-inverted-periods
```

### 6.1 Regression fixture

```yaml
fixture_name: ERVN-PERIOD-001-inverted-periods
description: |
  Synthetic artifact with periods=[2021..2025] but values assigned in reverse.
  Same number-set as a clean artifact; only ordering differs.
purpose: |
  Prove the verifier can distinguish (correct period → correct value) from
  (correct period → wrong value). v1.0.0 returned PASS on this fixture (real
  FPT qualification artifact, 12/15 inverted).
expected_verifier_result: FAIL_REQ-PERIOD-INTEGRITY
```

## 7. Hotfix file changes

### 7.1 Files to modify (under `equity-research-vn/scripts/` and `agent-eval/runner/`)

| File | Change |
|---|---|
| `agent-eval/runner/build_data_contract.py` | Replace `years_asc[4-i]` with call to `period_key_resolver.resolve(csv_path, fundamental_sponsor, ratios_csv)`. Drop positional mapping entirely. |
| `agent-eval/runner/period_key_resolver.py` | NEW — implements §4 |
| `agent-eval/runner/period_integrity_gate.py` | NEW — implements §5 |
| `agent-eval/runner/agent_runner.py` | Insert period_integrity_gate into pipeline between build_data_contract and existing gates |
| `equity-research-vn/scripts/independent_verifier.py` | Add REQ-PERIOD-INTEGRITY verification method (§6) |
| `equity-research-vn/requirements.yaml` | Add REQ-PERIOD-INTEGRITY entry |
| `equity-research-vn/scripts/test/fixtures/inverted_periods/` | NEW — regression fixture (clean + inverted variants) |
| `equity-research-vn/scripts/test/test_period_integrity.py` | NEW — TDD for resolver + gate + verifier check |

### 7.2 Files NOT to modify

- `agent-eval/cohort-c/production-release-v1.0.0/*` (immutable tag)
- `agent-eval/cohort-c/cohort-c-prime/*` (frozen qualification artifacts)
- `vn-financial-data-collector/*` (collector already correct; not the defect)

## 8. Requalification path (Branch A)

Per owner directive §XI:

```
1. Implement hotfix (§7)
2. Re-run forensic audit against v1.0.1 build → expect 0/475 inverted
3. Targeted validation: 12 runs across 6 sector archetypes
   - one bank (VCB)
   - one insurance (BVH)
   - one diversified conglomerate (MSN)
   - one negative-value company (POW or HSG)
   - one industrial (HPG)
   - one consumer (MWG or VNM)
4. Shadow requalification: 5+ tickers in fresh sectors, full agent_runner
5. Short operational soak (6-12 hours)
6. Rollback drill: deploy bad candidate → detect via period_integrity_gate → restore
7. Declare v1.0.1 PRODUCTION_READY
8. Close ERVN-PERIOD-001
```

If any step fails, return to step 1 with the failure mode documented.

## 9. Open questions for owner

- [ ] Confirm: when `fundamental_sponsor.json` is absent (current Phase 6E packs), should build abort, or fall through to Strategy 3 (value-diff consistency)? **Recommendation: abort, force source-pack completeness.**
- [ ] Confirm: should the verifier's new REQ-PERIOD-INTEGRITY be **critical** (blocks deploy) or **high** (warning)? **Recommendation: critical, given ERVN-PERIOD-001 severity.**
- [ ] Confirm: scope of historical artifact remediation. Owner directive §V.A.3 says "determine how many historical artifacts are affected". Do we attempt to retroactively correct qualification artifacts, or only document them as known-bad?

## 10. Acceptance criteria for v1.0.1

- [ ] Forensic audit re-run: 0/475 (period,value) pairs inverted
- [ ] Regression fixture: v0.14.10+ verifier returns FAIL on inverted-periods fixture
- [ ] 12/12 targeted hotfix runs PASS including REQ-PERIOD-INTEGRITY
- [ ] Shadow requalification ≥5 tickers, fresh sectors, all PASS
- [ ] Operational soak no failures attributable to period handling
- [ ] Rollback drill PASS (period_integrity_gate detects intentionally-bad candidate)
- [ ] `ERVN-PERIOD-001.md` status → CLOSED
- [ ] `vn-financial-data-collector/MATURITY.json` integration_maturity → PASS
