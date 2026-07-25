# ERVN-PERIOD-001 — INCIDENT CLOSED
**Closure Date:** 2026-07-20
**Owner Final Signoff:** APPROVED
**Release:** equity-research-vn v1.1.0

---

## Final State

```yaml
equity_research_vn:
  version: 1.1.0
  architecture: HYBRID_DETERMINISTIC_SHELL
  maturity: PRODUCTION_READY
  production_authorization: GRANTED

ERVN_PERIOD_001:
  status: CLOSED
  classification: LATENT_RELEASE_DEFECT
  original_severity: CRITICAL
  resolution:
    - period_mapping_fixed
    - period_integrity_gate_added
    - full_HTML_generation_retired
    - deterministic_renderer_adopted
    - section_level_generation_adopted

equity_research_vn_1_0_0:
  immutable: true
  production_use: PROHIBITED
  superseded_by: equity-research-vn-1.1.0

vn_financial_data_collector:
  standalone_maturity: STABLE_CANDIDATE
  integration_maturity: PRODUCTION_INTEGRATED_AFTER_DEPLOYMENT
```

## Qualification Summary (52 genuine runs, 376 sections, 100% PASS)

| Phase | Result | Key evidence |
|-------|--------|-------------|
| A — Design | PASS | Report IR schema, section registry, renderer contract |
| B — Renderer | PASS | 6/6 tickers, 12 mutations, 0 survived |
| C — Section pipeline | PASS | 8/8 synthetic cases |
| D — Integrated synthetic | PASS | 39/39 cases |
| E — Genuine targeted | PASS | 12/12, 142 sections, 100% first-attempt |
| F1 — Shadow | PASS | 20/20, 234 sections, 100% first-attempt |
| F2 — Operational soak | PASS | 20/20, 0 DATA changes |
| F3 — Rollback drill | PASS | 6/6, detect→block→restore→smoke |

## Historical artifacts

147 artifacts from v1.0.0 affected by period inversion. Registry preserved.
Policy: actively_used must be regenerated or carry warning; archived preserved with incident reference.

## Component inventory

**Preserved from hotfix (validated in 100 genuine runs):**
- `period_key_resolver.py`
- `period_integrity_gate.py`
- `build_data_contract.py` v1.0.1

**New architecture components:**
- `applicability_engine.py`
- `report_ir_builder.py`
- `deterministic_renderer.py`
- `narrative_sanitizer.py`
- `section_generator.py`
- `full_pipeline.py`

**Retired:**
- Free-form full HTML generation (RC1-RC4 path)
- Post-hoc artifact admission gate
- Post-hoc DATA contract enforcer
