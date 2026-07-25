# Architecture Decision Record — Option B Hybrid Deterministic Shell

**Date:** 2026-07-19
**Status:** APPROVED by owner
**Supersedes:** free-form full HTML generation (v1.0.0–v1.0.1-rc4)

## Context

After 4 release candidate cycles (48 genuine model runs), the period-inversion hotfix is validated (0 inversions) but the artifact generation architecture cannot reliably produce 12/12 PASS. Root cause: model has ~17% chance of omitting DATA/Chart.js code, triggering 5+ cascade failures per affected run. Post-generation repair gates have become a complex network with cross-layer conflicts.

## Decision

Adopt **Option B — Hybrid Deterministic Shell**:
- HTML skeleton, DATA block, charts, JavaScript = deterministic (renderer-generated)
- Section narrative text = model-generated (per-section, independently validated)
- Period hotfix preserved as data layer foundation

## Alternatives Considered

| Option | Reliability | Cost | Risk | Selected |
|--------|------------|------|------|----------|
| A: Keep current (RC5+) | ~67% pass rate | Low | High (growing complexity) | No |
| **B: Hybrid deterministic shell** | **~92% expected** | **Medium (3-5 sessions)** | **Medium** | **Yes** |
| C: Full structured IR (JSON-only model) | ~98% expected | High (5-8 sessions) | Low | No (deferred if B insufficient) |

## Rationale

1. Eliminates 83% of failures (DATA/charts become deterministic)
2. Lowest migration risk from current architecture
3. Preserves validated period hotfix
4. Model focuses on narrative (its strength)
5. Section-level retry isolates failures (1 section error → 1 REQ fail, not cascade)

## Consequences

- Model calls increase from 8 (phases) to ~20 (phases + 12 sections)
- Token usage similar or slightly lower (narrative-only vs full HTML)
- Renderer code is new (~1000 lines)
- Verifier requirements unchanged (same 29 REQs)
- Source packs, period resolver, data contract builder preserved unchanged
