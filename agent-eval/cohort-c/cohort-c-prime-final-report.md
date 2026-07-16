# Cohort C′ — Final Report: STABLE_CANDIDATE ACHIEVED

**Protocol:** v0.8.1 (sha256: `3695c58843c4281140f89265006dde5c1931e4242bd4f564dfa3211c1ee9a3ec`)
**Verifier:** 0.1.5 (sha256: `6cc2e40f`)
**Date:** 2026-07-14
**Status:** COMPLETE — **10/10 PASS, STABLE_CANDIDATE**

---

## Result

| Run | Ticker | Sector | verdict | pass | fail | duration |
|-----|--------|--------|---------|------|------|----------|
| Cp-CTD-01 | CTD | Industrial | **PASS** | 28 | 0 | 981s |
| Cp-CTD-02 | CTD | Industrial | **PASS** | 28 | 0 | 1021s |
| Cp-KDH-01 | KDH | Real estate | **PASS** | 28 | 0 | 881s |
| Cp-KDH-02 | KDH | Real estate | **PASS** | 28 | 0 | 744s |
| Cp-PNJ-01 | PNJ | Retail/Jewelry | **PASS** | 28 | 0 | 1004s |
| Cp-PNJ-02 | PNJ | Retail/Jewelry | **PASS** | 28 | 0 | 1543s |
| Cp-VCB-01 | VCB | Banking | **PASS** | 28 | 0 | 836s |
| Cp-VCB-02 | VCB | Banking | **PASS** | 28 | 0 | 1029s |
| Cp-FPT-01 | FPT | Technology | **PASS** | 28 | 0 | 1026s |
| Cp-FPT-02 | FPT | Technology | **PASS** | 28 | 0 | 911s |

**10/10 PASS. 0 requirement failures across all 10 runs. 0 fabricated data. 0 critical failures.**

---

## Release Gate Evaluation

| Gate | Threshold | Actual | Result |
|------|-----------|--------|--------|
| Genuine completed runs | 10 | 10 | ✓ |
| Final PASS rate | ≥9/10 | **10/10** | ✓ |
| REQ-013 occurrences | ≤1/10 | **0/10** | ✓ |
| REQ-020 occurrences | ≤1/10 | **0/10** | ✓ |
| REQ-025 occurrences | ≤1/10 | **0/10** | ✓ |
| Critical failures | 0 | 0 | ✓ |
| Fabricated data | 0 | 0 | ✓ |
| HTML output rate | 100% | 100% | ✓ |
| No ticker with 0/2 PASS | true | true (all 5 tickers 2/2) | ✓ |
| Verifier false positives | 0 | 0 | ✓ |
| Recurring cross-ticker defects | 0 | 0 | ✓ |

**ALL 11 GATES PASS.**

---

## Classification

```yaml
cohort_C_prime:
  pass_rate: 10/10 (100%)
  classification: STABLE_CANDIDATE
  per_ticker:
    CTD: 2/2 PASS
    KDH: 2/2 PASS
    PNJ: 2/2 PASS
    VCB: 2/2 PASS
    FPT: 2/2 PASS
  no_sector_gap: true
  shadow_production: ELIGIBLE
```

---

## Journey Summary (Cohort C → C′)

| Metric | Cohort C (v0.7.1) | Tier 1 (v0.8.0) | Cohort C′ (v0.8.1) |
|--------|-------------------|------------------|---------------------|
| PASS rate | 0/10 | 3/6 (rescored 4/6) | **10/10** |
| Avg recall | 24.3/28 | 27/28 | **28/28** |
| REQ-001/002 | FAIL 10/10 | PASS (PATH fix) | PASS 10/10 |
| VCB REQ-023/025 | FAIL 2/2 | PASS (builder fix) | PASS 2/2 |
| REQ-013 | 3/10 | 0/6 (content gate) | 0/10 |
| REQ-007 false positive | — | 1/6 | 0/10 (v0.1.5 fix) |
| REQ-020 | 1/10 | 1/6 | 0/10 |
| REQ-025 | 2/10 (banking) | 1/6 | 0/10 |

**Four hardening cycles** took the skill from 0/10 to 10/10:
1. Builder sector-hardening (banking CSV case-insensitivity)
2. Content-depth gate (semantic REQ-013 prevention)
3. Environment PATH fix (vnstock_data resolution)
4. REQ-007 entity-interruption-tolerant verifier

---

## Next Step: Shadow Production

Per the owner's roadmap:
```text
Cohort C′ (STABLE_CANDIDATE) ✓
→ Shadow production / soak test
→ Operational release gates
→ PRODUCTION_READY
```

Cohort C′ demonstrates the skill generalizes across 5 sectors (industrial, real estate, retail, banking, technology) with zero defects. The next gate is shadow production: running the pipeline in near-production conditions (≥10 consecutive jobs, sandbox deployment, monitoring).
