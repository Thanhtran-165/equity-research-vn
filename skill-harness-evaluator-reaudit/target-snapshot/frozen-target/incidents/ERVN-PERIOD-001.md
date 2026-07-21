# Incident ERVN-PERIOD-001 — Parent Period-Inversion Defect

| Field | Value |
|---|---|
| **Incident ID** | ERVN-PERIOD-001 |
| **Severity** | CRITICAL — data integrity |
| **Status** | OPEN — CLASSIFIED (Branch A: LATENT_RELEASE_DEFECT) |
| **Opened** | 2026-07-18 |
| **Component** | `build_data_contract.py` (equity-research-vn runner) |
| **Affected release** | `equity-research-vn-1.0.0` (immutable tag — not modified) |
| **Discovered by** | Phase 6F parent-integration regression of `vn-financial-data-collector` |
| **Next candidate** | `equity-research-vn-1.0.1` |

---

## 1. Defect

`build_data_contract.py` assigns CSV rows to year periods using **positional reverse mapping**:

```python
# build_data_contract.py:238-239 (and similar at 253, 265)
for i, row in enumerate(inc[:5]):  # latest 5 rows (row 0 = 2025, row 1 = 2024, ...)
    yr = str(years_asc[4-i])
```

The comment claims "row 0 = 2025, row 1 = 2024, ..." (i.e. CSV is descending by year). The actual vnstock sponsor CSV format is **ascending by year** (row 0 = 2021 = oldest, row 4 = 2025 = latest). Verified on 6 tickers (FPT, MWG, DHG, VJC, GVR, NLG) on 2026-07-18.

Consequence:
- `years_asc[4-i]` for i=0 → year 2025, but the row is actually 2021's data
- The OLDEST period's value is labeled as the LATEST period
- Every period label in `verified-dashboard-data.json` is reversed relative to its true value

## 2. Observed impact

| Ticker | Parent raw-CSV match | Collector raw-CSV match |
|---|---|---|
| FPT | 5/30 (17%) | 30/30 (100%) |
| MWG | 5/30 (17%) | 30/30 (100%) |
| DHG | 5/30 (17%) | 30/30 (100%) |
| VJC | 5/30 (17%) | 30/30 (100%) |
| GVR | 5/30 (17%) | 30/30 (100%) |
| NLG | 5/30 (17%) | 30/30 (100%) |
| **Total** | **30/180 (16.7%)** | **180/180 (100%)** |

Parent's 5/30 per ticker = only the latest-period values happen to be self-consistent within the inverted contract (because both `verified-dashboard-data.json` and `data/financials.json` were built by the same inverted logic).

## 3. Why the parent verifier did not catch this

`independent_verifier.py` (v0.14.9) performs:
- Internal consistency: `verified-dashboard-data.json` ↔ `data/financials.json` (both built by same builder → agree)
- PE/PB recompute: uses the contract's own (inverted) EPS → still internally consistent
- REQ-022/025/026: financial recompute using contract's own values → still internally consistent

**Missing check:** direct comparison of (period, value) pairs in the contract against (period, value) pairs in the raw source CSV. The verifier trusts the builder's period labels.

## 4. Classification — pending forensic audit

Two hypotheses (owner directive §V):

- **Branch A — LATENT_RELEASE_DEFECT:** The defect existed at v1.0.0 qualification time. If the release-qualification snapshots ALSO have ascending CSV order, the defect was always present.
- **Branch B — EXTERNAL_SOURCE_SCHEMA_DRIFT:** The vnstock sponsor CSV ordering changed after v1.0.0 release. If release snapshots show descending order, current snapshots show ascending, this is schema drift.

**Classification cannot be made until historical snapshots are compared (§VI forensic audit).**

## 4b. Forensic audit — COMPLETED 2026-07-18

### Branch-A vs Branch-B determination

All 5 Cohort C′ qualification tickers (CTD, FPT, KDH, PNJ, VCB) have source-pack CSVs that are **byte-identical (sha256 match)** between the qualification-time run dirs (`cohort-c-prime/Cp-<TICKER>-01/*.csv`, dated 2026-07-13) and the current source packs.

→ **Branch B (schema drift) RULED OUT.**

→ **Classification: Branch A — LATENT_RELEASE_DEFECT.** The period-inversion defect was present when `equity-research-vn-1.0.0` was qualified. The PRODUCTION_READY declaration was made on artifacts whose period labels were inverted relative to the source data.

### Period-trace scope (per owner directive §VI)

- **34 tickers scanned** (target was ≥20)
- **21 distinct sectors** (target was ≥10)
- **475 (period,value) pairs** traced across {revenue, net_profit, eps} × {2021..2025}

### Findings

| Metric | Value |
|---|---|
| Tickers fully period-inverted | **34 / 34** |
| Tickers clean | **0 / 34** |
| (period,value) pairs correctly period-assigned | **94 / 475 (19.8%)** |
| (period,value) pairs inverted (defect fired) | **376 / 475 (79.2%)** |
| (period,value) pairs neither | **5 / 475 (1.1%)** |
| Sectors affected | **21 / 21** |
| Per-sector inversion rate | ~80% consistent across every sector |

The 19.8% "correctly assigned" pairs are not actually correct — they are cases where the latest-period value in the source happens to coincide with what the inverted builder assigned to the latest period (because both indices map to position 4). E.g., for FPT revenue 2025 = 44023 tỷ, the builder's `years_asc[4-0]=2025` pulled row 0 (oldest), but the chart label "2025" was assigned array position 4 which also holds 44023 (since the dict lookup at line 245 of build_data_contract.py stored `revenue[2025] = row 4's value` correctly, but the array layout reversed it). The net effect: ~4/15 pairs per 3-field ticker look superficially correct.

### Implications

1. **v1.0.0 PRODUCTION_READY maturity is SUSPENDED_PENDING_REQUALIFICATION.** The qualification artifacts themselves are affected.
2. **All historical artifacts produced by v1.0.0 against sponsor-CSV source packs may have inverted period labels.** Scope: unknown — depends on which runs used sponsor CSVs.
3. **Hotfix path:** owner directive §XI Branch A — targeted hotfix → shadow requalification → short operational soak → rollback drill for v1.0.1.
4. **Verifier gap confirmed:** independent_verifier.py v0.14.9 cannot detect this because it consumes only the contract's own values (no raw-CSV cross-check). The fix in §IX (period-value pair comparison against raw source) is mandatory.

### Linked forensic evidence

- `incidents/ERVN-PERIOD-001-forensic-audit.py` — reproducible audit script
- `incidents/ERVN-PERIOD-001-forensic-audit.jsonl` — per-ticker, per-field, per-year traces
- `incidents/ERVN-PERIOD-001-forensic-summary.json` — aggregate summary
- `incidents/forensic-audit-runs/<TICKER>/verified-dashboard-data.json` — parent outputs (frozen for re-audit)

## 5. Production policy (interim, pending forensic classification)

```yaml
production_policy:
  sponsor_csv_path:
    status: FAIL_CLOSED
    reason: "Period-inversion confirmed on sponsor CSVs across 6 tickers; cannot trust period labels"
  unaffected_paths:
    status: PENDING_SCOPE_AUDIT
    reason: "Other ingestion paths (community vnstock, WebFetch) may not be affected; scope TBD"
  v1_0_0_tag:
    status: IMMUTABLE
    reason: "Owner directive §III: tag remains untouched; classification via forensic audit"
```

## 6. Required remediation (per owner directive §VII, §VIII)

### 6.1 period_key_resolver (architectural fix)

Replace positional mapping with explicit-period-key resolution:

```text
parse raw period labels (from `report_period` column or row metadata)
→ validate uniqueness (no duplicate periods)
→ determine chronological order (don't guess from array position)
→ map each value by explicit period key
→ reject positional guessing
```

```yaml
period_mapping:
  method: EXPLICIT_PERIOD_KEY
  positional_reverse_mapping: forbidden
  duplicate_periods: fail
  missing_period_label: fail
  unparseable_period: fail
  mixed_annual_quarterly: fail
```

### 6.2 period_integrity_gate (new gate)

```yaml
period_integrity_gate:
  raw_periods_unique: true
  values_length_matches_periods: true
  period_order_detected: true
  explicit_period_value_pairs_preserved: true
  latest_period_matches_source: true
  oldest_period_matches_source: true
```

Failure mode: `FAIL_PERIOD_PROVENANCE_INCOMPLETE`.

### 6.3 Verifier augmentation (per §IX)

Add fixture-based regression:

```yaml
raw:
  periods: [2021, 2022, 2023, 2024, 2025]
  values: [10, 20, 30, 40, 50]

bad_output:
  periods: [2021, 2022, 2023, 2024, 2025]
  values: [50, 40, 30, 20, 10]   # INVERTED

expected_verifier_result: FAIL_PERIOD_VALUE_MISMATCH
```

Verifier MUST compare raw (period, value) pairs against contract (period, value) pairs — not just set-equality or length.

## 7. Requalification scope (per §XI)

- **If Branch A (latent):** SUSPENDED_PENDING_REQUALIFICATION. Audit release evidence, count affected historical artifacts, hotfix + full requalification path (targeted hotfix → shadow → short soak → rollback drill for v1.0.1).
- **If Branch B (drift):** Keep v1.0.0 historical maturity, but block current production. Add deterministic order detection, release adapter as v1.0.1 after validation.

Either branch requires minimum:
- 12 targeted hotfix runs (6 sector archetypes × 2 runs)
- 20+ tickers raw alignment check across 10 sectors

## 8. Owner authorization required

- [ ] Owner approves SUSPENDED_FOR_AFFECTED_SOURCE_PATH status for v1.0.0 sponsor-CSV ingestion
- [ ] Owner authorizes hotfix candidate work on `equity-research-vn-1.0.1`
- [ ] Owner confirms v1.0.0 immutable tag is not to be modified
- [ ] Owner confirms `vn-financial-data-collector` ROBUST path remains DEFERRED until this incident closes

## 9. Linked evidence

- Discovery run: `/Users/bobo/.zcode/skills/vn-financial-data-collector/parent-integration-regression/`
- Discovery report: `/Users/bobo/.zcode/skills/vn-financial-data-collector/reports/phase6ef-stable-candidate-report.md`
- Collector maturity (unchanged): `/Users/bobo/.zcode/skills/vn-financial-data-collector/MATURITY.json`
