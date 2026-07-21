# ERVN-PERIOD-001 — Closure Report
**Date:** 2026-07-20
**Status:** READY FOR OWNER FINAL SIGNOFF

---

## 1. Incident timeline

| Date | Event |
|------|-------|
| 2026-07-18 | Phase 6E+6F collector validation discovered parent period inversion (376/475 pairs inverted) |
| 2026-07-18 | Incident ERVN-PERIOD-001 opened, forensic audit completed |
| 2026-07-18 | Period hotfix architecture built (resolver + gate + patched builder) |
| 2026-07-18 | RC1 cohort: 8/12 PASS — sector applicability + artifact quality defects |
| 2026-07-19 | RC2 cohort: 7/12 PASS — runner crash + null downstream + admission gaps |
| 2026-07-19 | RC3 cohort: 7/12 PASS — admission bypass + JS syntax + audit-split false positive |
| 2026-07-19 | RC4 cohort: 8/12 PASS — cascade from model DATA/chart omission |
| 2026-07-19 | Architecture review: Option B Hybrid Deterministic Shell approved |
| 2026-07-19 | Phase A (design) PASS — report IR schema, section registry, renderer contract |
| 2026-07-19 | Phase B (renderer prototype) PASS — 6/6 tickers, 12 mutation tests |
| 2026-07-19 | Phase C (section pipeline) PASS — 8/8 synthetic section cases |
| 2026-07-20 | Phase D (integrated synthetic) PASS — 39/39 cases |
| 2026-07-20 | Phase E (genuine cohort) PASS — **12/12, 142 sections, 100% first-attempt** |
| 2026-07-20 | Phase F1 (shadow) PASS — **20/20, 234 sections, 100% first-attempt** |
| 2026-07-20 | Phase F2 (soak) PASS — **20/20, 0 DATA changes** |
| 2026-07-20 | Phase F3 (rollback) PASS — **6/6, detect→block→restore→smoke** |

---

## 2. Final metrics

```yaml
total_genuine_runs_new_architecture: 52
total_sections_generated: 376
first_attempt_section_pass_rate: 100%
retries: 0
section_failures: 0
DATA_modifications_by_model: 0
period_inversions: 0
fabricated_sources: 0
cross_ticker_contamination: 0
sanitizer_bypasses: 0
```

---

## 3. Comparison: old architecture vs new

| Metric | RC1-RC4 (old) | Phase E-F (new) |
|--------|---------------|-----------------|
| Pass rate | 58-67% (7-8/12) | **100% (52/52)** |
| Section pass rate | ~83% (cascade failures) | **100% (376/376)** |
| DATA integrity violations | Multiple per cohort | **0** |
| Retries needed | 2-4 per run | **0** |
| Period inversions | 0 (hotfix worked) | **0** |

---

## 4. Closure gate

```yaml
incident_closure_gate:
  period_hotfix_validated: true (0 inversions in 52 new-arch runs + 48 RC1-RC4 runs)
  shadow_requalification: PASS (20/20)
  operational_soak: PASS (20/20)
  rollback_drill: PASS (6/6)
  collector_parent_integration: PENDING (standalone collector validated, integration ready)
  critical_open_defects: 0
  major_release_blockers: 0
```

---

## 5. Release recommendation

```yaml
release:
  version: equity-research-vn-1.1.0
  architecture: HYBRID_DETERMINISTIC_SHELL
  maturity: PRODUCTION_READY
  production_authorization: PENDING_OWNER_FINAL_SIGNOFF
```

**GLM không tự cấp final owner signoff.**

---

## 6. Collector integration

```yaml
vn_financial_data_collector:
  standalone_maturity: STABLE_CANDIDATE
  integration_maturity: PRODUCTION_INTEGRATED (pending parent release)
  role_in_new_architecture: DETERMINISTIC_DATA_FOUNDATION
```

---

## 7. Historical artifacts

147 artifacts from v1.0.0 affected by period inversion. Registry preserved at:
`incidents/ERVN-PERIOD-001-affected-artifact-registry.json`

These artifacts should not be used for period-sensitive conclusions. They may be regenerated with v1.1.0 architecture if needed.

---

## 8. Components validated and preserved

```yaml
preserved_from_hotfix:
  - period_key_resolver.py (0 inversions in 100 genuine runs)
  - period_integrity_gate.py
  - build_data_contract.py v1.0.1

new_components:
  - applicability_engine.py (shared decision_hash)
  - report_ir_builder.py (data contract → structured IR)
  - deterministic_renderer.py (IR → HTML + DATA + charts + JS)
  - narrative_sanitizer.py (escape + strip forbidden)
  - section_generator.py (model → section narrative)
  - full_pipeline.py (orchestrator)

retired:
  - free-form full HTML generation path (RC1-RC4)
  - artifact_admission_gate (no longer needed — renderer is deterministic)
  - data_contract_enforcer post-hoc injection (DATA now generated from IR)
```
