# VTA Phase 3 — Production Integration Wiring Implementation Report

- **Phase:** VTA_PHASE_3_PRODUCTION_INTEGRATION
- **Commit role:** INTEGRATION_WIRING (commit 1 of 4)
- **Branch:** `vta-phase-3-production-integration`
- **Direct parent:** `e386c4ef3cbfabd6341de26461d62766c5885f47` (MATURITY / ROBUST_MACHINE)
- **Pinned implementation commit:** `23853411aa74c504ee2d79dd8889a845b5edf7de`
- **Frozen content modified:** 0

## 1. Objective

Integrate the frozen VTA Phase 3 implementation into a target production system
without changing any frozen artifact (production core, verifier, fixtures,
oracles, mutations, witnesses, qualification evidence, maturity artifacts,
specification/acceptance artifacts). This commit delivers the integration
**wiring only**: adapter, feature flag, observability, rollback hooks,
integration failure-code namespace, integration tests, and integration
metadata. No deployment, evidence, or decision artifacts are produced here.

## 2. Integration boundary

```
Host input
  -> IntegrationAdapter.map_host_to_canonical_input()   (validate + field map + tz normalize)
  -> frozen VTA runner (run_active / run_profile)        (loaded commit-pinned)
  -> frozen canonical OutputPacket                       (verbatim, never recomputed)
  -> IntegrationAdapter.map_canonical_to_host_envelope() (versioned transport envelope)
  -> Downstream READ-ONLY consumer
```

The adapter never recomputes indicators, reinterprets setups, creates canonical
failure codes, changes primary/diagnostic codes, drops provenance, alters the
deterministic record ID, changes tolerance/rounding, inserts default market
data, guesses missing fields, or uses message text as a machine contract.

## 3. Components delivered

All components live under
`vn-technical-analysis-phase3-production-integration/src/`:

| File | Role |
|------|------|
| `integration_adapter.py` | Host<->canonical boundary adapter; commit-pinned frozen-runner loader; explicit per-field mapping; deterministic record ID. |
| `feature_flag.py` | Mandatory integration flag: name `vta_phase_3_integration_enabled`, default **OFF**, runtime disable (no restart), scopes environment/tenant/invocation. Fail-closed on ambiguous state. |
| `observability.py` | **12 mandatory metrics**, **7 dimensions**, allowlisted structured logs (no secrets / raw dumps / local paths). |
| `rollback_hooks.py` | Rollback controller (3 mechanisms: feature_flag_disable, routing_reversion, deployment_version_reversion); declared state (prior identified, no data migration, 0 irreversible side effects). |
| `integration_failure_codes.py` | Separate namespace: **9 integration codes**, **0 overlap** with the 43 canonical VTA codes; precedence model; structural disjointness guard. |
| `integration_tests.py` | Integration test suite (**29 tests**): wiring identity, host input mapping, input-boundary (16 classes), output-boundary, shadow parity, feature-flag routing, rollback drill. |

## 4. Version pinning (directive 10)

The frozen `runner` is loaded by inserting its exact pinned `src/` directory at
the front of `sys.path`. The loaded module's declared commit is asserted equal
to `23853411aa74c504ee2d79dd8889a845b5edf7de`; a mismatch fails closed
(`INTEGRATION_CONFIGURATION_MISMATCH`). To avoid bare-name shadowing between
our `integration_adapter` and the frozen runner's sibling of the same name, the
loader isolates `sys.modules` during the frozen import and restores our module
afterwards. No frozen code is copied or modified.

Runtime log/metric dimensions expose the exact VTA version identifiers
(implementation commit, canonical schema, serialization, formula/setup/failure
registry versions).

## 5. Feature flag (directive 11)

- **name:** `vta_phase_3_integration_enabled`
- **default_state:** `OFF`
- **runtime_disable_supported:** `true` (atomic, no restart)
- **restart_required_to_disable:** `false` (enforced at construction;
  `restart_required_to_disable=True` raises
  `INTEGRATION_FLAG_RESTART_REQUIRED_VIOLATION`)
- OFF behavior: returns the host's explicit disabled status
  (`EXPLICIT_DISABLED_STATUS`). It does **not** silently invoke an alternative
  technical-analysis implementation.

Resolution precedence: runtime override > invocation_path > tenant_or_consumer >
environment > DEFAULT (OFF).

## 6. Failure separation (directive 17)

The canonical registry (43 codes) is frozen and unchanged. Integration
failures live in namespace `VTA_PHASE_3_INTEGRATION` and cover the directive's
permitted categories: adapter schema rejection, unavailable frozen package,
configuration mismatch, unsupported host schema, deployment-version mismatch,
integration timeout, host serialization failure, and feature-flag ambiguity.
`assert_disjoint_from_canonical` is a structural import-time guard. When a
canonical failure envelope is present, the canonical code is primary and no
integration code is substituted in its place.

## 7. Read-only boundary (directive 7)

VTA is integrated as an analytics capability only. The host envelope carries
the canonical packet verbatim; `integration_envelope` is a clearly-namespaced
host-only section. The adapter exposes no write primitive that could mutate
host state, market data, portfolio, account, or source data. Side-effect
policy is encoded in every emitted envelope.

## 8. Verification performed (wiring-level)

These checks were run during wiring to validate the boundary (full evidence is
produced in commit 3):

- **Integration test suite:** 29/29 PASS.
- **Canonical regression through integration path:** 184/184 fixtures with
  exact digest/code parity vs the direct frozen runner (178 OK + 6 canonical
  failure envelopes), **0 semantic divergences**, 0 adapter errors. Empty /
  insufficient-history inputs forward to the frozen runner and surface the
  canonical `EMPTY_SERIES` / `INSUFFICIENT_HISTORY` envelope (no adapter
  rejection of valid empty lists).
- **Feature flag:** ON -> OK envelope; OFF -> explicit disabled status;
  runtime `disable()` flips state with no restart.
- **Rollback drill:** PASS, 0 residual side effects, 0 data migration.

## 9. Immutability

After this commit, integration code is immutable. Subsequent commits add
deployment configuration, evidence, and decision artifacts only.
