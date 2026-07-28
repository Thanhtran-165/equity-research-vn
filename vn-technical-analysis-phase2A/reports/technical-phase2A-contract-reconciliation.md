# Technical Phase 2A — Contract & Critical Oracle Reconciliation Report

**Phase:** 2A
**Date:** 2026-07-25
**Mode:** CONTRACT DESIGN ONLY (no production code)

---

## Executive Summary

```yaml
contracts_created: 10
requirements_created: 2 (requirement-registry + compatibility-matrix)
reconciliation_manifests: 5
total_deliverables: 18 (10 + 2 + 5 + 1 report)

formula_families:
  total: 22
  fully_reconciled: 7 (6 Sol decisions + F-DOUBLE-BOTTOM mode_parameterization)
  deferred_to_phase_3: 11 (thresholds + windows + F-INDUSTRY-PEER applicability)
  alias: 0 (F-VPT-CHANGE reclassified to DERIVED_OUTPUT in R3 — alias to OBV was self-contradictory)
  derived_output: 4 (F-ALPHA, F-TECH-SCORE, F-HV, F-VPT-CHANGE)
  duplicate_semantic: 0
  not_applicable: 0
  unclassified: 0
  previously_unaccounted: 4 (resolved)
  silently_excluded: 0

profile_blocks:
  total: 17
  reconciled: 17/17
  known_defects: 3 (B9, B12, B14 — all Phase 4 fix obligations)

setups:
  existing: 8
  coverage_status: BULLISH_ONLY (explicitly disclosed)
  bearish_policy: ADD_BEARISH_SETUP_REGISTRY (Sol decision §3, locked)
  mirror_by_sign_inversion: PROHIBITED
  complete_coverage_claim_allowed: false
  output_coverage_status_before_bearish_implementation: INCOMPLETE_BEARISH_COVERAGE

archetypes:
  total: 5
  precedence_complete: 5/5
  tie_break_complete: true (deterministic, unique precedence per archetype)

critical_ambiguities:
  total: 6
  resolved: 6/6 (all by Sol decisions §1-§6)

collector_gap:
  status: CONTRACT_DEFINED_EXTENSION_BLOCKED
  phase_6_blocked: true (until collector extension independently qualified)

code_changes: 0
protected_component_changes: 0
```

---

## 1. Contracts Created

| # | Contract | Purpose |
|---|---|---|
| 1 | technical-common-input.schema.json | Shared input for ACTIVE + PROFILE (market_data + research_context) |
| 2 | technical-active-output.schema.json | ACTIVE output with analysis_status + technical_state + confidence |
| 3 | technical-profile-output.schema.json | PROFILE output with 17 blocks + setups + archetype + coverage |
| 4 | market-data-packet-v1.schema.json | Collector → Technical OHLCV packet contract |
| 5 | parent-integration-contract.yaml | Handoff boundary (parent synthesis ONLY) |
| 6 | source-policy.yaml | Source hierarchy, integrated vs standalone, conflict resolution |
| 7 | price-basis-policy.yaml | 3 price bases: raw/adjusted/total-return with fail-closed |
| 8 | error-codes.yaml | 19 error codes with severity, mode, fail_closed |
| 9 | status-taxonomy.yaml | Separates validity/direction/confidence; bans BUY/SELL |
| 10 | REQ007-semantic-policy.yaml | 3-layer verification + forced translations + non-conclusion |

---

## 2. Critical Ambiguity Resolutions

All 6 resolved by Sol decisions:

| # | Ambiguity | Sol Decision | Contract |
|---|---|---|---|
| 1 | Verdict enum BUY/SELL | §1: Remove → status_taxonomy | status-taxonomy.yaml |
| 2 | Adjusted vs unadjusted | §2: 3 bases fail-closed | price-basis-policy.yaml |
| 3 | Channel slope 100 VND | §3: normalized_slope_pct | formula-oracle-reconciliation |
| 4 | events_1y bug | §4: Calendar window 365 days | VTA-REQ-013 |
| 5 | OBV/VPT bug | §5: Separate source series | VTA-REQ-014 |
| 6 | Collector OHLCV gap | §6: market-data-packet-v1 | market-data-packet-v1.schema.json |

---

## 3. Requirements

14 VTA-REQs (5 CRITICAL, 7 HIGH, 2 MEDIUM):
- REQ-005/006/007 compatibility resolved (REQ-007 = HIGHEST precedence)
- Price basis, formula integrity, mode separation, setup coverage, provenance, valuation boundary

---

## 4. Phase 2A Gate

```yaml
technical_phase_2A_gate:
  common_input_contract: PASS
  active_output_contract: PASS
  profile_output_contract: PASS
  market_data_packet_contract: PASS

  status_taxonomy:
    recommendation_enums_present: 0
    validity_and_direction_separated: true

  formulas:
    all_22_families_mapped: true
    unresolved_definitions_explicit: true (11 deferred to Phase 3)
    silently_resolved: 0
    unclassified: 0
    previously_unaccounted_reconciled: 4/4
    F_DOUBLE_BOTTOM: duplicate_semantic=false, mode_parameterization_recorded=true
    F_INDUSTRY_PEER: optional_not_equated_with_out_of_scope=true, runtime_applicability_defined=true
    F_VPT_CHANGE: alias_to_OBV=false, source_series=VPT, derived_from=F-VPT, independent_from_OBV=true

  profile_blocks:
    reconciled: 17/17

  setups:
    legacy_registry: 8/8
    bullish_only_disclosed: true
    bearish_policy_decision_recorded: true (ADD_BEARISH_SETUP_REGISTRY — locked decision)
    mirror_prohibited: true
    incomplete_coverage_claim_blocked: true

  coverage_status:
    dedicated_field: true
    analysis_status_unchanged: true
    INCOMPLETE_BEARISH_COVERAGE_in_analysis_status: false

  archetypes:
    reconciled: 5/5
    precedence_defined: true
    tie_break_defined: true

  critical_ambiguities:
    resolved: 6/6

  REQ_007:
    lexical_policy: complete
    semantic_implication_policy: complete
    imperative_policy: complete

  parent_boundary:
    valuation_modification_paths: 0
    direct_fetch_integrated_mode: prohibited

  protected_component_changes: 0
  code_changes: 0
```

---

## 5. Phase 2A Final Report

```yaml
technical_phase_2A:
  contracts_created: 10
  requirements_created: 2
  reconciliation_manifests: 5

  formula_families:
    total: 22
    fully_reconciled: 7
    deferred_to_phase_3: 11
    alias: 0
    derived_output: 4
    duplicate_semantic: 0
    not_applicable: 0
    unclassified: 0
    previously_unaccounted: 4
    previously_unaccounted_resolved: 4

  profile_blocks:
    total: 17
    reconciled: 17

  setups:
    existing: 8
    coverage_status: BULLISH_ONLY
    bearish_policy: ADD_BEARISH_SETUP_REGISTRY (locked)
    mirror_prohibited: true
    complete_coverage_claim_allowed: false

  archetypes:
    total: 5
    precedence_complete: true
    tie_break_complete: true

  critical_ambiguities:
    total: 6
    resolved: 6

  collector_gap:
    status: CONTRACT_DEFINED_EXTENSION_BLOCKED
    phase_6_blocked: true

  code_changes: 0
  protected_component_changes: 0
  final_gate: PASS (Phase 2A-R4 remediation complete)

R2_reporting_correction:
  affected: "Phase 2A-R2 summary header"
  problem: "RECONCILED reported as 8, actual record count 7. Arithmetic error in header, NOT a formula transition."
  no_additional_formula_moved: "No second formula transitioned RECONCILED→DERIVED_OUTPUT"

decision:
  owner_review_required: true
  phase_2B_authorized: false
  phase_3_authorized: false

decision:
  owner_review_required: true
  phase_2B_authorized: false
  phase_3_authorized: false
```

---

## Deliverables Index (18 total)

| # | File | Status |
|---|---|---|
| 1 | contracts/technical-common-input.schema.json | ✅ |
| 2 | contracts/technical-active-output.schema.json | ✅ |
| 3 | contracts/technical-profile-output.schema.json | ✅ |
| 4 | contracts/market-data-packet-v1.schema.json | ✅ |
| 5 | contracts/parent-integration-contract.yaml | ✅ |
| 6 | contracts/source-policy.yaml | ✅ |
| 7 | contracts/price-basis-policy.yaml | ✅ |
| 8 | contracts/error-codes.yaml | ✅ |
| 9 | contracts/status-taxonomy.yaml | ✅ |
| 10 | contracts/REQ007-semantic-policy.yaml | ✅ |
| 11 | requirements/requirement-registry.yaml | ✅ |
| 12 | requirements/REQ005-REQ006-REQ007-compatibility-matrix.yaml | ✅ |
| 13 | manifests/formula-oracle-reconciliation.yaml | ✅ |
| 14 | manifests/profile-block-reconciliation.yaml | ✅ |
| 15 | manifests/setup-coverage-reconciliation.yaml | ✅ |
| 16 | manifests/archetype-precedence-reconciliation.yaml | ✅ |
| 17 | manifests/critical-ambiguity-resolution.yaml | ✅ |
| 18 | reports/technical-phase2A-contract-reconciliation.md | ✅ (this file) |

All 18 deliverables complete.
