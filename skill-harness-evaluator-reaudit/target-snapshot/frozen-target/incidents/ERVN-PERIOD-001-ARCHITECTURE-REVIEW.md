# ERVN-PERIOD-001 — Architecture Review
**Date:** 2026-07-19
**Status:** FINAL — RC chain HALTED, architecture review required
**Author:** Hardening program (after RC1–RC4 closure)

---

## 1. Executive Summary

After 4 release candidate cycles (RC1–RC4) with 48 genuine model runs across 6 tickers, the **period-inversion hotfix is validated** (0 inversions in 48 runs) but the **artifact generation architecture cannot reliably produce 12/12 PASS**. The dominant failure pattern is **cascade from model failing to render DATA block + Chart.js code** — a single representation defect triggers 5+ downstream REQ failures. This is not fixable by patching individual requirements; it requires restructuring how artifacts are generated.

**Recommendation: Option B — Hybrid deterministic shell** (HTML skeleton + DATA + charts deterministic; model writes section-level narrative only).

---

## 2. RC4 Closure

```yaml
rc4:
  runs: 12
  pass: 8
  fail: 4
  verdict: FAIL
  patches_during_cohort: 0
  period_inversion_defects: 0
  artifacts_preserved: true
  wall_clock: ~40 min (4-way parallel)
```

---

## 3. RC4 Failure Analysis

### BVH-01/02 (5 REQs each — 1 root cause chain)

| REQ | Failure | Root cause |
|-----|---------|------------|
| REQ-026 | revenue not found in JS DATA | Model didn't render DATA block with revenueStatus encoding |
| REQ-023 | Total Assets/Equity not found | DATA block malformed → balance sheet arrays missing |
| REQ-012 | charts=0 | Chart.js initialization code absent from artifact |
| REQ-028 | canvas_ids found but chart_ids_referenced=[] | Canvas HTML present but `new Chart()` calls missing |
| REQ-021 | auto-fail blocker | Consequence of above 4 |

**Chain:** Model produced HTML with canvas elements but no functional DATA/Chart code → 5 cascade failures from **1 representation defect**.

### MSN-02 (5 REQs — same cascade pattern)

Same chain as BVH: `charts=0` + DATA missing + 1 external claim without qualifier.

### MWG-02 (2 REQs — cross-layer inconsistency)

| REQ | Failure | Root cause |
|-----|---------|------------|
| REQ-003 | audit-split keyword not found | Admission gate defaults NOT_APPLICABLE, but **verifier still keyword-checks** — two layers use different applicability logic |
| REQ-021 | auto-fail blocker | Consequence of REQ-003 |

**Root:** Cross-layer semantic drift between admission gate (RC4 fix) and verifier (unfixed).

### Summary: 2 root causes, not 12

```yaml
root_cause_1:
  description: "Model fails to render DATA block + Chart.js code in ~17% of runs (2/12)"
  cascade: "5 REQ failures per affected run"
  affected_runs: BVH-01, BVH-02, MSN-02
  total_failures: 15 (of which 12 are cascade)

root_cause_2:
  description: "Admission gate and verifier use different audit-split applicability logic"
  cascade: "1 REQ failure + REQ-021 blocker"
  affected_runs: MWG-02
  total_failures: 2
```

---

## 4. RC1–RC4 History

| RC | PASS | FAIL | Dominant defect | Defects fixed | New defects |
|----|------|------|-----------------|---------------|-------------|
| RC1 | 8/12 | 4 | Sector applicability (revenue=0), agent variance | — | — |
| RC2 | 7/12 | 5 | Runner crash (aig_result), null downstream, skeleton admission | Sector gate | Crash exposed by admission gate |
| RC3 | 7/12 | 5 | Admission bypass, JS syntax lfohse, audit-split false positive | Runner crash, NO_RESULT | Admission gate too strict |
| RC4 | 8/12 | 4 | Cross-layer semantic drift, model DATA/chart rendering | POW bypass, MWG false positive | Verifier still keyword-checks audit-split |

### Pattern analysis

1. **Defects fully resolved:** 4 (period inversion, runner crash, POW admission bypass, MWG audit-split admission false positive)
2. **Defects reappearing in new form:** 2 (BVH NA encoding shifts from enforcer → DATA block → verifier cascade; model artifact quality varies run-to-run)
3. **Failures from free-form HTML generation:** ~83% (10/12 REQ failures in RC4 are from model not rendering DATA/charts)
4. **Failures from contract/enforcer/verifier mismatch:** ~17% (2/12 — MWG cross-layer audit-split)
5. **Overlapping gates with different semantics:** 2 layers (admission gate vs verifier) check audit-split with different logic

---

## 5. Current Harness Complexity

```yaml
current_harness:
  requirement_count: 29
  admission_checks: 15
  deterministic_enforcers: 3 (DATA, valuation, balance_sheet)
  retry_triggers: 4 (admission, integrity, content_depth, phase6_preflight)
  sector_exemptions: 1 (insurance revenue NOT_APPLICABLE)
  regex_or_keyword_rules: 8+
  post_generation_repairs: 4 layers
  verifier_requirements: 29
```

**Assessment:** The harness has become a **post-generation repair network**. Each cycle adds a new gate or exemption that interacts unpredictably with existing gates. The admission gate and verifier now use different applicability logic for the same requirement (audit-split). Deterministic enforcers modify the artifact AFTER admission, potentially invalidating what admission validated.

---

## 6. Dominant Failure Pattern

```text
Model generates HTML
→ Sometimes omits or malforms DATA block
→ Sometimes omits Chart.js initialization
→ Enforcer tries to fix DATA but may fail silently
→ Verifier checks DATA + charts → 5+ cascade failures
→ Each run has ~17% chance of this pattern (2/12 in RC4)
```

This is **not fixable by adding more gates**. The root cause is that the model is responsible for generating both narrative content AND technical infrastructure (DATA arrays, Chart.js code, DOM structure) in a single free-form HTML output.

---

## 7. Recommended Architecture: Option B — Hybrid Deterministic Shell

```yaml
recommended_architecture:
  option: B
  rationale: |
    Addresses 83% of failures (DATA/chart rendering) by making them deterministic.
    Lowest migration risk from current architecture.
    Preserves period hotfix as data layer foundation.
  migration_scope: |
    Phase A: Define report IR schema
    Phase B: Build deterministic renderer (HTML skeleton + DATA + charts)
    Phase C: Section-level prompts (model writes narrative JSON per section)
    Phase D: Migrate requirements to section-level validation
  expected_reliability_gain: |
    DATA/charts become deterministic → eliminates cascade failures.
    Model only writes narrative → fewer technical constraints → higher quality.
    Expected pass rate: 11-12/12 (vs current 7-8/12).
  expected_cost: 3-5 sessions
  expected_token_change: |
    Section-level generation uses ~20% fewer tokens (no HTML boilerplate).
    But more model calls (1 per section × 12 sections = 12 calls vs 1).
    Net: similar total tokens, better quality per call.
  expected_latency_change: |
    Section calls can run in parallel (4 workers).
    Expected: similar or slightly faster than current.
  backwards_compatibility: |
    Period hotfix (resolver + gate) preserved as-is.
    Verifier requirements unchanged (same REQ IDs).
    Source packs unchanged.
```

### Why not Option A (keep current)?
Continuing to patch gates leads to RC5, RC6... each adding complexity without addressing root cause. Technical debt grows. Probability of 12/12 remains ~67% per cohort (8/12 average).

### Why not Option C (full IR)?
Highest reliability but highest migration cost (5-8 sessions). Overkill for current problem — Option B achieves similar reliability with less disruption.

---

## 8. Structured Intermediate Representation (proposed schema)

```yaml
report_ir:
  metadata:
    ticker: FPT
    company: FPT Corporation
    sector: Technology
    periods: [2021, 2022, 2023, 2024, 2025]
    source_hashes: {...}

  data_contract:
    financial_metrics: {revenue: [...], netProfit: [...], ...}
    statuses: {revenue: VALID, ...}
    applicability_rules: {revenue: null, ...}
    provenance: {revenue: vnstock_sponsor, ...}

  sections:
    executive_summary: {content: "...", status: populated}
    company_profile: {content: "...", status: populated}
    financial_overview: {content: "...", status: populated}
    growth_analysis: {content: "...", status: populated}
    profitability: {content: "...", status: populated}
    balance_sheet: {content: "...", status: populated}
    cash_flow: {content: "...", status: populated}
    valuation: {content: "...", status: populated}
    risks: {content: "...", status: populated}
    catalysts: {content: "...", status: populated}
    audit_notes: {content: "...", status: populated}
    conclusion: {content: "...", status: populated}

  charts:
    - chart_id: chartHistRev
      chart_type: bar
      source_metrics: [revenue]
      period_value_pairs: {2021: 35671, ...}
      applicability: VALID
      title: Doanh thu 5 năm

  external_claims:
    - text: "~3,000 điểm bán"
      source: model_knowledge
      qualifier_type: APPROXIMATE
      confidence: medium

  validation:
    section_status: {all: populated}
    unresolved_items: []
```

---

## 9. Deterministic vs Model-Generated

### Deterministic (not model-controlled)
- Ticker identity, source provenance, period-value mapping
- DATA block, metric status, sector applicability
- Valuation calculations, chart datasets, chart wrappers
- Section containers, navigation, HTML skeleton
- JavaScript structure, audit metadata, null/NA rendering

### Model only generates
- Trend explanations, cause interpretation
- Qualitative comparison, risks, catalysts
- Executive summary, section-level narrative

### Model does NOT generate
- Raw financial arrays, period labels
- JavaScript chart code, full HTML
- Applicability status, source IDs, valuation numbers

---

## 10. Section-Level Generation Assessment

| Aspect | Current (full HTML) | Proposed (section-level) |
|--------|--------------------|-------------------------|
| Model calls per run | 8 phases × 1 call | 8 phases + 12 section calls = 20 |
| Token usage | ~100K tokens (full HTML) | ~80K tokens (narrative only) |
| Failure amplification | 1 error → 5+ cascade | 1 section error → 1 REQ fail |
| Retry granularity | Full artifact regeneration | Single section retry |
| Parallel execution | No (sequential phases) | Yes (sections in parallel) |
| Reusable sections | No (all-or-nothing) | Yes (good sections preserved) |

---

## 11. Components to Preserve

```yaml
preserved_from_hotfix:
  - period_key_resolver.py (VALIDATED — 0 inversions in 48 runs)
  - period_integrity_gate.py (VALIDATED)
  - build_data_contract.py v1.0.1 (data layer foundation)
  - fundamental_sponsor.json snapshots (period metadata)
  - independent_verifier.py (requirements unchanged)
  - requirement registry (29 REQs)
  - provenance logic
  - sector applicability registry
  - numeric/field normalizers
```

Period hotfix becomes the **deterministic data layer** for the new architecture.

---

## 12. Release & Production Policy

```yaml
equity_research_vn:
  production_authorization: BLOCKED
  v1_0_0_use: PROHIBITED (period inversion defect)
  v1_0_1_release: NOT_AUTHORIZED (artifact generation unreliable)

ERVN_PERIOD_001:
  status: OPEN
  period_layer: VALIDATED (0 inversions in 48 genuine runs)
  artifact_layer: NOT_REQUALIFIED

possible_split_release:
  deterministic_data_layer:
    status: POTENTIALLY_RELEASABLE_INTERNALLY
    (period resolver + data contract + source snapshots work reliably)
  full_research_artifact:
    status: BLOCKED (needs architecture migration)
```

---

## 13. Child-Skill Program Impact

```yaml
child_skill_program:
  vn_financial_data_collector:
    status: PRESERVE_STABLE_CANDIDATE
    (standalone maturity achieved; not dependent on artifact renderer)
  vn_news_digest:
    standalone_audit_allowed: true
    parent_integration_work: DEFERRED
  parent_artifact_dependent_skills:
    integration_hardening: DEFERRED_UNTIL_IR_DEFINED
```

---

## 14. Migration Plan

```text
Phase A — Define report IR and section schemas (1 session)
Phase B — Build deterministic renderer + chart builder (2 sessions)
Phase C — Section-level prompts + validators (1 session)
Phase D — Migrate current requirements to section validation (1 session)
Phase E — Synthetic fixtures + mutation tests (1 session)
Phase F — Targeted genuine cohort (1 session)
Phase G — Shadow + soak + rollback (1 session)
```

Each phase has deliverables, gate, and stop condition.

---

## 15. Final Assessment

```yaml
architecture_review:
  rc4_verdict: FAIL_8_OF_12
  dominant_failure_pattern: "Model fails to render DATA+charts → 5 cascade failures per affected run"
  current_architecture_assessment: "Post-generation repair network — too complex, gates conflict"
  recommended_option: "B — Hybrid deterministic shell"
  migration_required: true
  rc5_authorized: false

release:
  v1_0_1_production_ready: false
  period_data_layer_status: VALIDATED (reusable in new architecture)
  artifact_generation_status: NEEDS_REDESIGN

next_action:
  architecture_design_gate: "Owner approves Option B migration"
  owner_decision_required: true
```

---

## 16. Conclusion

The period-inversion hotfix succeeded — **0 inversions across 48 genuine runs** validates that period_key_resolver + period_integrity_gate + build_data_contract work correctly. This data layer should be preserved as the foundation for the new architecture.

The artifact generation layer (free-form HTML by LLM) cannot reach 12/12 reliability because:
1. Model has ~17% chance of omitting DATA/Chart code per run
2. Each omission cascades into 5+ requirement failures
3. Post-generation repair gates have become a complex network with cross-layer conflicts
4. Adding more gates increases complexity without addressing root cause

**Option B (hybrid deterministic shell)** is recommended because it:
- Eliminates 83% of failures (DATA/charts become deterministic)
- Preserves the validated period hotfix as data layer
- Has moderate migration cost (3-5 sessions)
- Allows model to focus on narrative quality (its strength)
