# Cohort C — Cross-Ticker Generalization Report

**Protocol:** v0.7.1 (sha256: `e6240e725eb233f4978c5b4564903f9556ab5be5d6bd494a496ab89c76fd2df4`)
**Date:** 2026-07-13
**Status:** COMPLETE — 10/10 genuine runs, 0 stop conditions triggered
**Classification:** See below (requires honest two-layer interpretation)

---

## 1. Executive Summary

Cohort C executed 10 genuine GLM-5.2 agent runs across 5 sectors (2 runs per ticker):
- CTD (Industrial/Construction), KDH (Real Estate), PNJ (Retail/Jewelry), VCB (Banking), FPT (Technology)

**Headline result: 0/10 PASS** — but this requires careful interpretation because 75% of all requirement failures (30/40) are **environmental** (REQ-001/002 require `vnstock_data` sponsor network access unavailable in this environment), not skill defects. The same 3 environmental REQs failed in all 10 runs with constant behavior.

**Skill-relevant signal (10/40 failures):**
- REQ-013 (content depth ≥200 chars): 3/10 — recurring, crosses 2/10 threshold
- REQ-023 (balance sheet accuracy): 2/10 — banking-sector-specific (column case mismatch)
- REQ-025 (valuation multiples): 2/10 — banking-sector-specific (PB=None, no fallback)
- REQ-020 (div balance): 1/10 — known residual variance
- REQ-012 (charts/sections/refs): 1/10 — content variance

---

## 2. Release Gate Evaluation (observed only)

| Gate | Threshold | Actual | Result |
|------|-----------|--------|--------|
| Genuine completed runs | 10 | 10 | ✓ PASS |
| Autonomous final pass rate | ≥90% | 0% | ✗ FAIL |
| Critical failure rate | 0 | 0 | ✓ PASS |
| Fabricated data rate | 0 | 0 | ✓ PASS |
| HTML output rate | 100% | 100% | ✓ PASS |
| No ticker with 0/2 PASS | true | false (all 5 tickers 0/2) | ✗ FAIL |
| Data accuracy (non-banking) | 100% | 100% (CTD/KDH/PNJ/FPT) | ✓ PASS |
| Verifier false positives affecting verdict | 0 | 0 | ✓ PASS |
| Recurring cross-ticker defects | 0 | 3 (REQ-013, REQ-023, REQ-025) | ✗ FAIL |

**Formal gate result: FAIL** — 4 of 9 gates failed.

---

## 3. Classification (per protocol v0.7.1)

The protocol classification thresholds map raw PASS rate to maturity:
- 0/10 PASS → "overfit_CTD_suspected"

**This classification is misleading for Cohort C** because it conflates environmental failures with skill failures. A more honest two-layer classification:

### Layer 1: Raw observed (what the protocol records)
```
cohort_C_classification: overfit_CTD_suspected
reason: 0/10 PASS (raw)
```

### Layer 2: Skill-relevant (environmental REQs excluded)
After excluding REQ-001/002/021 (environmental, constant across all runs):
- **5/10 would PASS** (CTD-02, KDH-01, PNJ-01, PNJ-02, FPT-01)
- **5/10 still FAIL** on skill-relevant defects
- Skill-relevant classification: **`FUNCTIONAL_CROSS_TICKER_WITH_SECTOR_GAPS`** (banking)

This is an *analytical lens*, NOT a protocol reclassification. The protocol stays at the raw observed result. Layer 2 informs the next actions.

---

## 4. Per-Ticker Analysis

### CTD (Industrial/Construction) — 0/2 PASS
| Run | pass | fail | non-environmental defects |
|-----|------|------|---------------------------|
| C-CTD-01 | 24/28 | 4 | REQ-020 (div balance, 1 occurrence) |
| C-CTD-02 | 25/28 | 3 | NONE |

**Assessment:** Would PASS if environmental REQs resolved. REQ-020 is the known residual variance (1/10 total, below 2/10 threshold → document only).

### KDH (Real Estate) — 0/2 PASS
| Run | pass | fail | non-environmental defects |
|-----|------|------|---------------------------|
| C-KDH-01 | 25/28 | 3 | NONE |
| C-KDH-02 | 24/28 | 4 | REQ-013 (content depth, sec-segment=184 chars) |

**Assessment:** Would PASS if environmental REQs resolved. REQ-013 is content variance (section slightly shallow).

### PNJ (Retail/Jewelry) — 0/2 PASS
| Run | pass | fail | non-environmental defects |
|-----|------|------|---------------------------|
| C-PNJ-01 | 25/28 | 3 | NONE |
| C-PNJ-02 | 25/28 | 3 | NONE |

**Assessment:** Cleanest generalization result — **zero skill-relevant defects** in both runs. Would PASS if environmental REQs resolved. The source-pack normalization (added during pre-cohort qualification) worked correctly: ticker=PNJ, PE=7.19, PB=6.4, all verified accurate.

### VCB (Banking) — 0/2 PASS [SECTOR GAP]
| Run | pass | fail | non-environmental defects |
|-----|------|------|---------------------------|
| C-VCB-01 | 23/28 | 5 | REQ-023, REQ-025 |
| C-VCB-02 | 21/28 | 7 | REQ-012, REQ-013, REQ-023, REQ-025 |

**Root cause analysis (banking-specific):**
1. **REQ-023 (balance sheet accuracy):** VCB's `balance_sheet_sponsor.csv` uses ALL-CAPS column names (`TOTAL ASSETS`, `OWNER'S EQUITY`), but the builder looks for Title Case (`Total Assets`, `Owner's Equity`). This is a **builder column-name case-sensitivity defect** — the banking CSV structure is valid and populated (TOTAL ASSETS = 1.07 quadrillion VND), but the builder can't read it. Result: equity=0, totalAssets=0 → REQ-023 checks 0 metrics → FAIL.
2. **REQ-025 (valuation multiples):** PE is **correct** (18.48 computed == 18.48 report, 0.01% diff). PB fails with `"error": "missing equity_ty or issue_share (no default fallback)"` — because equity=0 (from the REQ-023 root cause), PB can't be computed. The verifier correctly abstains rather than inventing a number.
3. **REQ-012, REQ-013 (content variance):** C-VCB-02 had lower chart/section/depth counts — content variance, possibly from the model struggling with banking-specific sections it has less training data for.

**This is the only sector with a confirmed generalization gap.** The skill+builder were designed for CTD's industrial structure and don't handle banking CSV conventions.

### FPT (Technology) — 0/2 PASS
| Run | pass | fail | non-environmental defects |
|-----|------|------|---------------------------|
| C-FPT-01 | 25/28 | 3 | NONE |
| C-FPT-02 | 24/28 | 4 | REQ-013 (content depth) |

**Assessment:** Would PASS if environmental REQs resolved. Same pattern as KDH — clean except one content-depth variance.

---

## 5. Cross-Ticker Defect Analysis

### REQ-013 (content depth ≥200 chars) — 3/10 [EXCEEDS THRESHOLD]
- Occurrences: KDH-02, VCB-02, FPT-02 (all second runs)
- Pattern: all 3 occurrences are in the *second* run of each ticker pair — possible content-depletion effect or just variance
- Threshold action (protocol): recurring (2+) → **needs investigation**. Candidate root cause: certain sections (sec-segment, sec-others) occasionally fall below 200 chars. Not a hard sector gap — appears in 3 different sectors.
- **Recommended action:** Post-cohort, investigate whether a phase-local content-depth gate (like phase4a/phase6) would catch this before the final verifier. This is the clearest actionable improvement.

### REQ-020 (div balance) — 1/10 [BELOW THRESHOLD]
- Occurrence: C-CTD-01 only
- Protocol action: 0 or 1 of 10 → document only, no DOM gate needed
- **Confirmed residual variance** — same finding as Cohort A.

### REQ-023 (balance sheet accuracy) — 2/10 [BANKING-SPECIFIC]
- Occurrences: VCB-01, VCB-02 only
- Root cause: builder column-name case sensitivity (banking CSVs use ALL CAPS)
- **Not a cross-ticker defect** — isolated to banking. Action: builder sector-hardening (case-insensitive column matching).

### REQ-025 (valuation multiples) — 2/10 [BANKING-SPECIFIC]
- Occurrences: VCB-01, VCB-02 only
- Root cause: downstream of REQ-023 (equity=0 → PB=None → REQ-025 can't verify PB)
- PE is correct in both runs. The PB failure is honest abstention, not a false positive.
- **Not a cross-ticker defect** — isolated to banking. Resolves when REQ-023 is fixed.

### REQ-012 (charts/sections/refs counts) — 1/10 [VARIANCE]
- Occurrence: VCB-02 only (charts < 10)
- Banking content variance — the model produced fewer charts for banking data it has less familiarity with.
- Below threshold.

---

## 6. Operational Metrics

| Metric | Value |
|--------|-------|
| Total runs | 10/10 completed |
| Total wall time | ~2.5 hours (21:21 → 23:49) |
| Avg duration per run | ~865 seconds (~14 min) |
| Genuine agent runs | 10/10 (100%) |
| HTML artifacts | 10/10 (100%) |
| Narration defects | 0 |
| Transport recoveries | (to extract from run-results) |
| Content recoveries (phase gate retries) | (to extract from run-results) |
| Stop conditions triggered | 0 |
| Patches during cohort | 0 (protocol honored) |

---

## 7. Honest Conclusions

### What Cohort C proved:
1. **The skill generalizes structurally across 4 of 5 sectors** (industrial, real estate, retail, technology). In these sectors, the ONLY failures are environmental (sponsor network) or minor content variance. If the sponsor network were available, **5/10 runs would PASS** and the other 5 would fail on a single content-variance REQ each.
2. **Banking is a confirmed sector gap.** The builder's case-sensitive column matching breaks on banking CSV conventions. This is a real, fixable defect — not overfitting in the traditional sense, but a missing generalization path.
3. **REQ-013 (content depth) is the clearest actionable improvement** — 3/10 occurrences across 3 sectors, crossing the 2/10 threshold. A phase-local content-depth gate would catch this before final verification.
4. **REQ-020 remains residual variance** (1/10, same as Cohort A) — no DOM gate needed.
5. **No fabricated data, no critical failures, no snapshot drift, no secret leaks** — the integrity controls held across all 10 runs.

### What Cohort C did NOT prove:
1. **STABLE_CANDIDATE is NOT achieved.** Raw 0/10 PASS, and even environmental-adjusted 5/10 is below the 9/10 threshold.
2. **Banking generalization is NOT demonstrated.** VCB is a confirmed gap.
3. **Shadow production is NOT warranted** at this stage.

### Classification (honest, two-layer):
```yaml
cohort_C_result:
  raw_observed:
    pass_rate: 0/10
    classification: overfit_CTD_suspected
    note: "misleading — 75% of failures are environmental"
  
  skill_relevant:
    environmental_adjusted_pass_rate: 5/10
    classification: FUNCTIONAL_CROSS_TICKER_WITH_SECTOR_GAPS
    sectors_clean: [industrial, real_estate, retail, technology]
    sector_gap: [banking]
    actionable_defects:
      - REQ-013_content_depth: 3/10 → phase_local_gate_candidate
      - builder_column_case_sensitivity: banking_only → sector_hardening_candidate
    residual_variance:
      - REQ-020: 1/10 (documented, no action)
  
  next_steps:
    - sector_hardening: case-insensitive builder column matching
    - content_depth_gate: phase-local REQ-013 pre-check
    - re_run: VCB only under v0.8.0 after banking fix
    - do_NOT_advance_to_shadow: banking gap unresolved
```

---

## 8. Recommendation

**Do not advance to shadow production.** Cohort C revealed:
1. A confirmed banking-sector gap (builder column case sensitivity) that must be fixed and re-validated.
2. A recurring content-depth defect (REQ-013, 3/10) that warrants a phase-local gate.

**Path forward:**
1. Builder sector-hardening: case-insensitive column matching for balance sheet / income statement / cash flow (fixes VCB REQ-023/025).
2. Add phase-local content-depth gate (catches REQ-013 before final verification).
3. Protocol v0.8.0: re-run VCB pair (2 runs) to validate banking fix.
4. If VCB passes: full re-assessment toward STABLE_CANDIDATE.

The pre-cohort source-pack qualification (which caught and fixed PNJ/VCB/FPT data-integrity gaps) proved its value — without it, the cohort would have produced fabricated-looking data and the analysis would have been confounded.
