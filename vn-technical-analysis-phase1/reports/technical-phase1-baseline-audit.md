# Technical Phase 1 — Baseline Architecture & Failure Mode Audit

**Skill:** vn-technical-analysis
**Phase:** 1 (BASELINE_ARCHITECTURE_AND_FAILURE_MODE_AUDIT)
**Mode:** READ_ONLY
**Date:** 2026-07-25
**Audit agents:** 2

---

## Executive Summary

```yaml
sources_audited: 10
modes_found: 2 (ACTIVE weekly, PROFILE daily)
formulas_found: 22 (6 ACTIVE + 16 PROFILE families)
profile_blocks_found: 17 (claimed 15, actual 17)
setup_heuristics_found: 8 (bullish-only, bearish detectors missing)
archetypes_found: 5 (SKILL.md says 4, code has 5 incl no_current_setup)
ambiguities_total: 24
high_risk_ambiguities: 12
critical_failure_modes: 6
largest_integration_gaps:
  - "Collector does not provide price/OHLCV data — major blocker for Phase 6"
  - "No verifier exists — no independent recomputation"
  - "No provenance — output not traceable to source"
  - "Code embedded in markdown — not structured as runnable modules"
current_engineering_maturity: PROMPT_ONLY
phase_1_recommendation: "Proceed to Phase 2 (contracts) after Sol review. 6 CRITICAL ambiguities must be resolved in Phase 2-3 before implementation."
```

---

## 1. Sources Audited

10 sources: SKILL.md + 7 references + 2 parent phase files + requirements.yaml. See `manifests/technical-source-inventory.yaml`.

---

## 2. Modes

| Mode | Frequency | Parent Phase | Steps | Min History | Language Policy |
|---|---|---|---|---|---|
| ACTIVE | WEEKLY | phase4a | 4 | AMBIGUOUS | Weaker (BUY/SELL prohibited but "TECHNICAL STRONG BULLISH" allowed) |
| PROFILE | DAILY | phase4b | 5 | 60 sessions (hard), 252 (ideal) | Strict neutral_descriptive_non_advice |

Shared logic: OHLCV normalization, MA/RSI computation (but potentially different smoothing methods across modes — divergence risk).

Contamination risk: No guard prevents ACTIVE fields appearing in PROFILE output or vice versa.

---

## 3. Formulas

```yaml
formulas:
  claimed: 11 (SKILL.md indicator table)
  unique: 22 (6 ACTIVE families + 16 PROFILE families)
  duplicate_semantics: 0
  ambiguous: 17 (see oracle registry O-001..O-024)
```

Critical ambiguities:
- **RSI**: Wilder confirmed in indicators.md, but SKILL.md doesn't specify
- **Bollinger std**: Population (÷N) in ACTIVE, Sample (÷N-1) in PROFILE helpers — inconsistent
- **Beta window**: Implied 52 weeks but never stated
- **Adjusted vs unadjusted prices**: Never specified

---

## 4. Profile Blocks

```yaml
profile_blocks:
  claimed: 15 (SKILL.md) / 17 (reference header)
  confirmed: 17 (B1-B17 all have Python implementations)
  duplicate: 0
  undefined: 0
  ambiguous: 0 (blocks themselves are defined; count claim is ambiguous)
```

Known code bugs:
- B12: OBV change overwritten by VPT change (copy-paste)
- B14: events[-252:] cuts sporadic events not sessions
- B9: O(n²) from recomputing vol history in loop

---

## 5. Setup Heuristics

```yaml
setup_heuristics:
  claimed: 8
  confirmed: 8 (detector functions exist)
  duplicate: 0
  undefined: 0
  ambiguous: 1 (code says "top 6 returned" vs header says "8")
```

Critical gap: **Bearish setups exist in DOWNSIDE_PATTERNS dictionary but have NO detector functions.** Only bullish setups are detected. This means `trap_prone` archetype only triggers via high_volume_behavior, never via bearish pattern detection.

---

## 6. Archetypes

```yaml
archetypes:
  total: 5
  precedence_defined: true (trend_following > accumulation_breakout > trap_prone > mixed)
  tie_break_defined: false
  ambiguous: 1 (SKILL.md says 4, code has 5 incl no_current_setup)
```

---

## 7. Implicit Oracles

```yaml
implicit_oracles:
  total: 24
  critical: 6
  high: 6
  unresolved: 24 (none frozen in Phase 1)
```

Top 5 highest risk:
1. **O-007**: Adjusted vs unadjusted prices — split-unadjusted creates false patterns
2. **O-009**: Channel slope threshold 100 VND — not scale-free
3. **O-016**: Verdict enum contradiction (SKILL vs phase4a/REQ-005)
4. **O-013**: HVB events_1y cuts wrong dimension (events not sessions)
5. **O-024**: CMF B12 OBV/VPT bug — OBV metric silently wrong

---

## 8. Failure Modes

```yaml
failure_modes:
  total: 28
  critical: 6
  high: 10
  fail_closed_currently: 1 (only PROFILE <60 sessions)
  undetected_currently: 27
```

6 CRITICAL failure modes:
- FM-CORPORATE-ACTION-UNADJUSTED (price data may be unadjusted)
- FM-LOOKAHEAD-BIAS (pattern detection may reference future data)
- FM-MISSING-PROVENANCE (output not traceable)
- FM-FABRICATED-VALUE (no verifier to catch)
- FM-VALUATION-OVERRIDE (no guard against modifying fundamentals)
- FM-ZERO-PRICE (produces NaN cascade)

---

## 9. REQ-007

```yaml
REQ_007:
  samples_audited: ~30 language samples
  clearly_allowed: 9 patterns
  clearly_prohibited: 15 lexical + 3 semantic + 3 imperative
  ambiguous: 5 patterns
  lexical_only_insufficient: true
```

Key finding: **REQ-006 and REQ-007 check the same thing (non-advice) but with different regex and different negation awareness.** An implementation can PASS REQ-007 (negation-aware) but FAIL REQ-006 (negation-unaware) for the same text like "không phải tín hiệu."

Non-conclusion points: **2 conflicting versions** between metric_guardrails.md and stock_profile_blocks.md orchestrator. Point 3 differs completely.

---

## 10. Parent Boundary

```yaml
parent_boundary:
  collector_packet_sufficiency: "MAJOR GAP — collector does not provide OHLCV price data"
  direct_fetch_current_behavior: "YES — subagent fetches directly from vnstock"
  context_binding_current_state: "NONE"
  valuation_override_risk: "NONE currently (no path to modify valuation)"
  integration_blockers: 5 (IB-001..IB-005)
```

**Critical integration gap:** Collector provides fundamental data (revenue, NPAT, equity) but NOT market price data (daily/weekly OHLCV). Technical-analysis requires price series + benchmarks. This must be resolved before Phase 6.

---

## 11. Engineering Gap

```yaml
engineering_gap:
  current_maturity: PROMPT_ONLY
  largest_missing_layers:
    1: Verifier (no independent recomputation)
    2: Contracts (no formal schemas)
    3: Provenance (no source chain)
    4: Deterministic code (Python embedded in markdown)
    5: Mutation suite (no corruption testing)
```

12 dimensions assessed: 9 ABSENT, 1 PROMPT_ONLY, 1 INFORMAL, 0 DETERMINISTIC, 0 VERIFIED.

---

## 12. Ambiguity Summary (24 total)

| Category | Count | Severity Breakdown |
|---|---|---|
| FORMULA_DEFINITION | 7 | 3 CRITICAL, 4 HIGH |
| WINDOW_OR_SMOOTHING | 3 | 1 HIGH, 2 MEDIUM |
| DATA_FREQUENCY | 0 | — |
| ADJUSTMENT_POLICY | 1 | 1 CRITICAL |
| SOURCE_PRIORITY | 1 | 1 MEDIUM |
| PATTERN_THRESHOLD | 2 | 1 HIGH, 1 MEDIUM |
| SETUP_SCORING | 1 | 1 LOW |
| ARCHETYPE_PRECEDENCE | 1 | 1 MEDIUM |
| OUTPUT_SCHEMA | 1 | 1 HIGH |
| ERROR_BEHAVIOR | 2 | 1 HIGH, 1 MEDIUM |
| LANGUAGE_POLICY | 2 | 1 HIGH, 1 MEDIUM |
| PARENT_BOUNDARY | 3 | 1 CRITICAL, 2 HIGH |

---

## 13. Protocol

```yaml
protocol:
  code_changes: 0
  contract_changes: 0
  protected_component_changes: 0
```

---

## 14. Phase 1 Gate

```yaml
technical_phase_1_gate:
  mode_inventory_complete: true
  formula_inventory_complete: true
  pattern_inventory_complete: true
  profile_blocks_reconciled: true
  setup_heuristics_reconciled: true
  archetype_logic_mapped: true
  input_dependencies_complete: true
  implicit_oracles_catalogued: true
  failure_modes_catalogued: true
  REQ_007_baseline_complete: true
  parent_boundary_gap_complete: true
  engineering_gap_matrix_complete: true

  unresolved_ambiguities:
    listed: 24
    silently_resolved: 0

  code_changes: 0
  contract_changes: 0
  protected_component_changes: 0

  cross_manifest_consistency: PASS
```

---

## 15. Final Report Summary

```yaml
technical_phase_1:
  sources_audited: 10
  audit_agents_used: 2

  modes:
    ACTIVE: "Weekly, 4 steps, 6 indicator families, tech_score -6→+6"
    PROFILE: "Daily, 5 steps, 17 blocks, 8 setups bullish-only, 5 archetypes"

  formulas:
    claimed: 11
    unique: 22
    duplicate_semantics: 0
    ambiguous: 17

  profile_blocks:
    claimed: 15
    confirmed: 17
    duplicate: 0
    ambiguous: 0

  setup_heuristics:
    claimed: 8
    confirmed: 8
    duplicate: 0
    ambiguous: 1 (top 6 vs 8 returned)

  archetypes:
    total: 5
    precedence_defined: true
    tie_break_defined: false
    ambiguous: 1 (4 vs 5 count)

  implicit_oracles:
    total: 24
    critical: 6
    high: 6
    unresolved: 24

  ambiguities:
    total: 24
    critical: 6
    high: 6
    medium: 8
    low: 4

  failure_modes:
    total: 28
    critical: 6
    high: 10
    fail_closed_currently: 1
    undetected_currently: 27

  REQ_007:
    samples_audited: 30
    clearly_allowed: 9
    clearly_prohibited: 21
    ambiguous: 5
    lexical_only_insufficient: true

  parent_boundary:
    collector_packet_sufficiency: "MAJOR GAP — no price data from collector"
    direct_fetch_current_behavior: "YES (subagent fetches vnstock directly)"
    context_binding_current_state: "NONE"
    valuation_override_risk: "NONE currently"
    integration_blockers: 5

  engineering_gap:
    current_maturity: PROMPT_ONLY
    largest_missing_layers: [verifier, contracts, provenance, deterministic_code, mutations]

  protocol:
    code_changes: 0
    contract_changes: 0
    protected_component_changes: 0

  final_gate: PASS

decision:
  owner_review_required: true
  phase_2_authorized: false
```

---

## Deliverables Index

| # | File | Status |
|---|---|---|
| 1 | reports/technical-phase1-baseline-audit.md | ✅ (this file) |
| 2 | manifests/technical-source-inventory.yaml | ✅ |
| 3 | manifests/technical-mode-inventory.yaml | ✅ |
| 4 | manifests/technical-formula-inventory.yaml | ✅ |
| 5 | manifests/technical-pattern-heuristic-inventory.yaml | ✅ |
| 6 | manifests/technical-input-dependency-map.yaml | ✅ |
| 7 | manifests/technical-implicit-oracle-registry.yaml | ✅ |
| 8 | manifests/technical-failure-mode-registry.yaml | ✅ |
| 9 | manifests/technical-REQ007-language-baseline.yaml | ✅ |
| 10 | manifests/technical-parent-boundary-gap.yaml | ✅ |
| 11 | manifests/technical-engineering-gap-matrix.yaml | ✅ |
| 12 | manifests/technical-cross-manifest-gate.yaml | ✅ |

All 12 deliverables complete. Cross-manifest consistency gate: PASS.
