# VTA Phase 3 Qualification Report (Remediation-R2)

## Final verdict: FAIL

Runtime qualification executed via two-stage pipeline:
- Stage A: Production runner → 184 observed outputs (0 errors)
- Stage B: Independent verifier → 103 PASS, 54 FAIL, 27 ERROR

## What works
- Determinism: PASS (3/3 byte-identical)
- Verifier independence: PASS
- Commit boundaries: clean (21 impl + 410 fixture)
- Content-derived identity: PASS
- Fixtures have actual OHLCV: 184/184
- Execution matrix: target_VC_ids only

## What fails
54 FAIL + 27 ERROR from remaining interface gaps:
- formula_conformance VCs need close series from OHLCV records
- Some VC handlers expect fields not present in production output
- Negative fixtures produce exceptions that bypass expected flow

## Root cause
3 separate agents independently wrote production code, verifier, and fixtures
without a shared JSON interface contract. The flattening fix improved results
(80→103 PASS) but didn't close all gaps.

## Recommendation
Full alignment requires iterating on each of the ~80 failing VC handlers
to accept production output format, OR building a shared serialization layer.
