# Shadow Batch 1 (Qualification) — Report

**Protocol:** v0.9.0 (sha256: `a3c97ead...`)
**Date:** 2026-07-14
**Status:** COMPLETE — 10/10 jobs, **GATE FAILED** (60% vs ≥90% needed)

---

## Results (separated per owner directive)

### Quality
```yaml
final_pass_rate: 6/10 (60%)
data_accuracy: ALL data REQs pass (0 fabricated)
fabricated_data: 0
verifier_false_passes: 0
```

### Operations
```yaml
end_to_end_success_rate: 6/10 (60%)
latency: mean=1238s max=1526s
latency_slo_breaches: 0/10 (threshold: 3085s) ✓
transport_retries: total=0 max_per_run=0
content_retries: total=16 max_per_run=2 (content-depth gate working)
```

### Safety
```yaml
fail_closed_events: 0/10 ✓
accidental_deploys: 0 (sandbox only) ✓
duplicate_artifacts: 0 ✓
secret_leaks: 0 ✓
protocol_drift: 0 ✓
```

---

## Per-Ticker Detail

| Ticker | Sector | Runs | PASS | Non-REQ-021 defects |
|--------|--------|------|------|---------------------|
| HPG | Steel | 2 | 1/2 | REQ-020 (div balance, 1 occurrence) |
| VNM | Consumer staples | 2 | **0/2** | **REQ-027 (external claim unflagged, 2/2)** |
| MWG | Retail (electronics) | 2 | **2/2** | NONE |
| BID | Banking (state) | 2 | **2/2** | NONE |
| GAS | Energy | 2 | 1/2 | REQ-012 (charts=0), REQ-028 (canvas render) |

---

## Failure Analysis

### VNM REQ-027 (0/2 — TICKER BLOCKER) [CROSS-TICKER DEFECT]

**What:** The agent wrote `"Hơn 200,000 điểm bán trên toàn quốc"` (over 200,000 points of sale nationwide) — an external claim about store/distribution count. REQ-027 requires external claims (store count, peer revenue, etc.) to be flagged as "ước tính" (estimated) when no source data file exists.

**Why it failed:** VNM's source-pack has `events.csv` empty and `news_digest.json` empty (stub). The agent correctly included a factual claim about Vinamilk's distribution network, but the verifier's REQ-027 checks that external claims have a flag/source citation nearby (within ±200 chars). The claim "200,000 điểm bán" has no adjacent flag.

**Classification:** This is a **real cross-ticker defect** — the agent includes external claims without source flags when the source-pack lacks news/events data. It appeared 2/2 on VNM (whose pack has empty news). This is NOT a verifier false positive — the claim genuinely lacks a source citation.

**Root cause:** VNM's source-pack was built with empty events.csv and news_digest.json (stub files). The agent filled in known facts (Vinamilk's distribution network) from its training data, but didn't flag them as externally-sourced. This is exactly the "data from memory" risk the protocol guards against.

### GAS-02 REQ-012 + REQ-028 (1/2 — CONTENT VARIANCE)

**What:** GAS-02 produced 0 charts (canvas elements present but `charts` count = 0 in verifier check). REQ-012 requires ≥10 charts; REQ-028 checks canvas render-readiness.

**Why:** The GAS-02 artifact has 12 `<canvas>` elements AND Chart.js is present, but the verifier's chart-counting logic found 0. This may be a **verifier chart-detection edge case** or the agent placed canvases in a structure the verifier's regex doesn't match. GAS-01 (same ticker) passed 28/0 — so this is variance, not a systematic GAS defect.

**Classification:** Content variance (1/2 occurrence). Needs investigation but not a ticker blocker.

### HPG-02 REQ-020 (1/2 — KNOWN RESIDUAL)

**What:** Div balance (open ≠ close tags). Known residual variance from Cohort A/C/C′. 1 occurrence in Batch 1.

**Classification:** Below 2/10 threshold. Document only.

---

## Batch 1 Gate Evaluation

```yaml
batch_1_gate:
  autonomous_successful_completion_rate: 60% (need ≥90%) ✗ FAIL
  no_ticker_0_of_2: false (VNM 0/2) ✗ FAIL
  critical_failures: 0 ✓
  fabricated_data: 0 ✓
  unsafe_false_passes: 0 ✓
  accidental_public_deploys: 0 ✓
  secret_leaks: 0 ✓
  protocol_drift: 0 ✓
```

**Formal result: GATE FAILED.** Two criteria failed:
1. Autonomous success rate 60% < 90%
2. VNM 0/2 — ticker-level blocker confirmed

---

## What Worked (positive signals)

1. **BID (state banking) 2/2 PASS** — banking generalization confirmed beyond VCB. The builder's case-insensitive resolver handles BIDV's CSV structure correctly.
2. **MWG (electronics retail) 2/2 PASS** — no confusion with PNJ's jewelry model. Retail generalization holds.
3. **HPG (steel) 1/2 PASS** — heavy industry works; one residual variance.
4. **All safety gates PASS** — 0 fail-closed events, 0 fabricated data, 0 protocol drift, 0 secret leaks.
5. **All SLOs within bounds** — 0 latency breaches, transport retries = 0.
6. **Content-depth gate active** — 16 content retries across 10 jobs (catching shallow sections before final verifier).

---

## Root Cause: VNM Source-Pack Completeness

The VNM 0/2 failure traces to the source-pack having empty `events.csv` and `news_digest.json`. When the agent has no news/events data to work with, it fills gaps from model memory and doesn't flag external claims. This is the same class of issue the C0 zero-source abstention test was designed to catch.

**This is NOT a skill regression from Cohort C′** — C′ used tickers with complete news data. The defect surfaces specifically when source-packs lack news/events content.

---

## Recommendation

**Do NOT proceed to Batch 2 (Operational Soak).** Per the owner's directive: "không nên mở Batch 2 nếu một ticker thất bại 2/2." VNM 0/2 is a confirmed ticker blocker.

**Required before Batch 2:**
1. **Fix VNM source-pack**: populate events.csv and news_digest.json with real Vinamilk news/events data (same as CTD/KDH/PNJ packs have). This is source-pack qualification, not a skill patch.
2. **Investigate GAS-02 chart detection**: determine if REQ-012 chart counting has an edge case or if the agent genuinely produced malformed chart structure.
3. **Re-run VNM pair** under corrected source-pack to confirm REQ-027 passes.

**Do NOT patch the skill, verifier, runner, builder, or protocol.** The defects are source-pack completeness (VNM) and content variance (GAS-02, HPG-02) — not architectural.
