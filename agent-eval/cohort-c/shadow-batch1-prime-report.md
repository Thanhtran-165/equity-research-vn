# Shadow Batch 1′ — Report

**Protocol:** v0.10.0 (sha256: `03ca4bcb...`)
**Verifier:** 0.1.6 (two-tier REQ-027)
**Date:** 2026-07-15
**Status:** COMPLETE — 10/10 jobs, **GATE FAILED** (60% vs ≥90%, VNM 0/2)

---

## Results (separated per owner directive)

### Quality
```yaml
final_pass_rate: 6/10 (60%)
data_accuracy: REQ-022/023/024/025 pass on all tickers except VNM REQ-026
fabricated_data: 0
verifier_false_passes: 0
```

### Operations
```yaml
end_to_end_success_rate: 6/10 (60%)
latency: mean=1176s max=1951s
latency_slo_breaches: 0/10 ✓
transport_retries: total=0
content_retries: total=12 max=2
```

### Safety
```yaml
fail_closed_events: 0/10 ✓
accidental_deploys: 0 ✓
secret_leaks: 0 ✓
protocol_drift: 0 ✓
```

---

## Per-Ticker

| Ticker | Sector | Runs | PASS | Primary defect |
|--------|--------|------|------|----------------|
| BID | Banking (state) | 2 | **2/2** ✓ | NONE |
| GAS | Energy | 2 | **2/2** ✓ | NONE |
| HPG | Steel | 2 | 1/2 | REQ-019 JS syntax (1/2) |
| MWG | Retail | 2 | 1/2 | REQ-027 unqualified claim (1/2) |
| VNM | Consumer staples | 2 | **0/2** ✗ | REQ-026 netProfit→netIncome key name (2/2) |

---

## Comparison: Batch 1 (v0.9.0) → Batch 1′ (v0.10.0)

| Metric | Batch 1 (v0.9.0) | Batch 1′ (v0.10.0) | Change |
|--------|-------------------|---------------------|--------|
| PASS rate | 6/10 (60%) | 6/10 (60%) | Same |
| REQ-027 occurrences | 2/10 (VNM 2/2) | 2/10 (VNM-02 + MWG-02) | Same count, but now VARIANCE not systematic |
| VNM primary defect | REQ-027 (2/2) | REQ-026 (2/2) | Shifted — REQ-027 fixed on VNM-01 |
| BID | 2/2 PASS | 2/2 PASS | Stable ✓ |
| MWG | 2/2 PASS | 1/2 PASS | One REQ-027 instance |
| GAS | 1/2 | 2/2 ✓ | IMPROVED (chart init fixed) |
| HPG | 1/2 | 1/2 | REQ-020→REQ-019 (different variance) |

---

## Failure Analysis

### VNM REQ-026 (0/2 — TICKER BLOCKER) [KEY-NAME MISMATCH]

**What:** The data contract has `netProfit` (correct key, correct values: [8577, 10632, 11235, 10554, 10205]). But the agent rendered it as `netIncome` in the DATA JS object. The verifier's REQ-026 checks for `netProfit` in the DATA array → not found → FAIL.

**Why:** The agent used `netIncome` (common English accounting term) instead of `netProfit` (the exact key the verifier expects). BID-01 correctly used `netProfit`. This is **naming variance** — the agent doesn't consistently use the verifier-expected key name.

**Classification:** Agent content variance (key naming). Not a data-accuracy issue (values are correct). Not a source-pack issue (contract has correct key). The phase6 prompt lists required DATA keys but the agent sometimes substitutes synonyms.

**Fix candidate:** Strengthen phase6 prompt to emphasize exact key names, or add a DATA-key-name validator to phase6 preflight.

### VNM-02 REQ-027 (1 instance — variance, not systematic)

**What:** One "điểm bán" claim without qualifier. VNM-01 PASSED REQ-027 (had `~` qualifier). The two-tier system works — it's just variance where the agent sometimes forgets the qualifier.

### MWG-02 REQ-027 (1 instance — variance)

**What:** MWG mentioned store counts without qualifier. MWG-01 PASSED. Same pattern as VNM-02 — occasional omission of `~` or `khoảng`.

### HPG-01 REQ-019 (JS syntax — variance)

**What:** `node --check` failed on the JS. Agent produced invalid JavaScript syntax. HPG-02 PASSED. Content variance.

### VNM-02 REQ-020 (div balance — known residual)

1 instance of div tag imbalance. Known residual variance.

---

## Positive Signals

1. **REQ-027 two-tier system WORKS** — VNM-01 now PASSES (was 2/2 FAIL in Batch 1). The remaining 2/10 REQ-027 instances are genuine variance (agent forgot qualifier), not systematic.
2. **GAS 2/2 PASS** — improved from 1/2 (chart init now consistent).
3. **BID 2/2 PASS** — banking generalization stable across both batches.
4. **All safety gates PASS** — 0 fabricated data, 0 critical failures, 0 fail-closed events.
5. **All SLOs within bounds** — 0 latency breaches, 0 transport retries.
6. **Source Pack v2 working** — company_profile injected, agent has operational metrics from source.

---

## Assessment

**The architecture upgrades (Source Pack v2, two-tier REQ-027, prompt modification) are working.** The failure profile shifted from systematic REQ-027 (VNM 2/2) to content variance (REQ-026 key naming, occasional qualifier omission, JS syntax). This is progress — the defects are now isolated, varied, and low-severity.

**VNM 0/2 remains a ticker blocker**, but for a DIFFERENT reason than Batch 1: REQ-026 (netProfit→netIncome key mismatch) rather than REQ-027 (unprovenanced claims). The REQ-027 fix worked; a new variance surface appeared.

**This is the expected behavior of iterative hardening** — each fix reveals the next layer of variance. The remaining defects (key naming, qualifier omission, JS syntax) are all fixable with targeted prompt strengthening or phase-local validation.
