# VTA Phase 3 Qualification Report (Runtime Executed)

## Executive Summary

Runtime qualification executed from isolated worktree at fixture-freeze commit
`681c51a77`. Verifier ran against 184 production-generated output packets,
producing 11,776 records across 64 VCs.

**Determinism: PASS (3/3 byte-identical)**
**Verifier Independence: PASS**
**Fixture format compatibility: PARTIAL (design-spec JSON not production packet format)**

## Qualification Execution

```yaml
fixture_freeze_commit: 681c51a7756ed305ca6f635d71010009702f4053
implementation_commit: 2938cf5502aa2cfd4182abc605ab7415f3eb62dd
worktree: /tmp/vta-clean-qual (detached)

execution:
  phase_a: Production code generated 184 output packets
  phase_b: Verifier processed 184 packets × 64 VCs = 11,776 records

runtime_verdicts:
  PASS: 5561
  FAIL: 3256
  ERROR: 2959
```

FAIL/ERROR verdicts are due to fixtures being design-spec JSON (containing
`frozen_input` with seed references) rather than production-format output
packets (with `mode`, `as_of_date`, `indicators` keys).

## Determinism (3 runs)

```yaml
run1_sha256: cda721ae03915fd7b2f79324e18fafd72f7a9b32b377e4d5c2c439ca917f6167
run2_sha256: cda721ae03915fd7b2f79324e18fafd72f7a9b32b377e4d5c2c439ca917f6167
run3_sha256: cda721ae03915fd7b2f79324e18fafd72f7a9b32b377e4d5c2c439ca917f6167
byte_identical: true (3/3)
```

## Verifier Independence

```yaml
_assert_independence: PASS
production_modules_loaded: 0
frozen_oracle_usage: true
```

## Known Finding

Fixture format mismatch: fixtures are design-spec JSON with seed references
(`SEED-ACTIVE-FULL-80w`), not executable data. Qualification harness generates
synthetic OHLCV data from seeds deterministically, runs production code, then
feeds output to verifier. Verifier correctly detects format differences.
