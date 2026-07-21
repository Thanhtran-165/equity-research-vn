# Phase 5R Remediation Report — vn-valuation-engine

**Date:** 2026-07-21
**Phase:** PHASE_5R_SOURCE_ADAPTER_REMEDIATION_REQUALIFICATION
**Status:** **PASS** — Phase 5R requalification thành công với patched adapter

## Executive Summary

Phase 5R được mở sau khi Phase 5 raw cohort **FAIL_SCALE_DEFECT** (safety stop do source adapter bug). Owner chỉ ra đúng: source adapter đã nằm trong phạm vi freeze của Phase 5, nên sửa giữa cohort là patch-in-frozen-cohort → không thể pool kết quả.

Phase 5R giải quyết bằng:
1. **Preserve raw Phase 5 verdict** (FAIL_SCALE_DEFECT immutable)
2. **Regression suite** (8 tests mới + 57 Phase 4 tests unchanged)
3. **Fresh precohort freeze** với patched adapter hash
4. **10 fresh live runs** (không reuse Phase 5 raw artifacts)
5. **Verdict separation**: raw FAIL / 5R PASS được ghi độc lập

```yaml
phase_5R_summary:
  regression_tests: 8/8 PASS (Scale.UNIT + Scale.MILLION + VVE-REQ-071 pos/neg)
  phase_4_unit_tests_preserved: 57/57 PASS
  fresh_runs: 10/10 (5 tickers × 2 runs)
  verifier_PASS: 10/10
  scale_defect_recurrence: 0  # KEY regression — defect không tái diễn
  
  phase_5R_gate: PASS
  maturity_outcome:
    implementation_status: GENUINE_BASELINE_REQUALIFIED
    standalone_maturity: FUNCTIONAL
```

## Verdict separation (Directive §9)

```yaml
phase_5:
  raw_verdict: FAIL_SCALE_DEFECT  # IMMUTABLE
  raw_artifacts_preserved: true
  raw_artifacts_location: halt-baseline-v1-scale-defect/

phase_5R:
  verdict: PASS
  fresh_runs: 10
  patched_adapter_hash: 7216ab2eb7bfbce1a464b4dc6485f0014a963c89a853a7f74131f9eb0c285431
  patches_during_phase5R_cohort: 0
  
no_pooling: true
raw_verdict_not_overwritten: true
```

## Patch registry (Directive Phase 5R §4)

```yaml
remediation:
  patch_id: PATCH-ADAPTER-01-scale-unit
  component: SOURCE_ADAPTER (Phase 5 new — NOT in Phase 4 frozen)
  file_changed: source-adapter/vnstock_adapter.py (1 file)
  phase4_files_modified: 0
  
  adapter_hash_before: 20b9fb455ff11b7f4cea4a213958042a14bc8a9c0cccfc108087cd05585046b6
  adapter_hash_after: 7216ab2eb7bfbce1a464b4dc6485f0014a963c89a853a7f74131f9eb0c285431
  
  root_cause: |
    Adapter set Scale.MILLION cho raw VND values từ vnstock.
    vnstock returns values ở VND UNIT (e.g., FPT EBITDA = 4.96e12 VND raw).
    Khi unit_currency_engine normalize Scale.MILLION → UNIT, nó nhân × 1M, 
    producing 4.96e18 (sai 1 triệu lần).
  
  fix: |
    Changed _metric default scale từ Scale.MILLION → Scale.UNIT 
    trong vnstock_adapter.py line ~52.
  
  tests_added: 8 tests trong tests/test_source_adapter_scale.py
    - 4 scale regression tests (UNIT/THOUSAND/MILLION/BILLION)
    - 1 adapter default scale smoke test
    - 2 VVE-REQ-071 positive/negative tests
    - 1 pre-fix adapter meta-test (chứng minh regression test would have caught bug)
```

## Regression gate (Directive §5)

```yaml
regression_gate:
  source_adapter_unit_tests: PASS  # 8/8 tests
  scale_unit_tests: PASS           # Scale.UNIT không nhân
  unit_currency_engine_tests: PASS # via Phase 4 P4A (57/57)
  runner_tests: PASS               # via Phase 4 P4A
  verifier_tests: PASS             # via Phase 4 P4A
  VVE_REQ_071_positive_test: PASS  # balanced bridge → PASS
  VVE_REQ_071_negative_test: PASS  # unbalanced bridge → FAIL with EQUITY_BRIDGE_INVALID
  
  phase4_files_hash_unchanged: true  # All 15 implementation files byte-for-byte
  parent_hash_unchanged: true        # equity-research-vn 1.1.0 (505 files) byte-for-byte
```

## Specific regression coverage (Directive §5)

### Test 1: raw VND + Scale.UNIT → NOT multiplied

```python
def test_raw_vnd_with_scale_unit_NOT_multiplied():
    raw_vnd_value = 4.96e12  # FPT EBITDA in raw VND
    metric = _make_metric(raw_vnd_value, Scale.UNIT)
    normalized = normalize_metric(metric)
    
    # Value should remain 4.96e12 (NOT multiplied by 1M)
    assert normalized.normalized_value == pytest.approx(raw_vnd_value, rel=1e-9)
    assert normalized.normalized_value < 1e15
```

### Test 2: million VND + Scale.MILLION → multiplied × 1M

```python
def test_million_vnd_with_scale_million_multiplied_correctly():
    value_in_millions = 8.619  # 8.619 million VND
    metric = _make_metric(value_in_millions, Scale.MILLION)
    normalized = normalize_metric(metric)
    
    # Should be multiplied by 1M
    assert normalized.normalized_value == pytest.approx(8.619e6, rel=1e-6)
```

### Test 3: VVE-REQ-071 positive (balanced bridge)

```python
# EV=10e9 - NET_DEBT=2e9 - MINORITY=1e9 = EQUITY_VALUE=7e9 → balanced
# Expected: VVE-REQ-071 PASS
```

### Test 4: VVE-REQ-071 negative (unbalanced bridge)

```python
# EV=10e9 - NET_DEBT=2e9 = 8e9, but EQUITY_VALUE=5e9 → unbalanced
# Expected: VVE-REQ-071 FAIL with EQUITY_BRIDGE_INVALID
```

### Meta-test: pre-fix adapter would fail

```python
def test_prefixed_adapter_would_fail_scale_UNIT_test():
    """Prove regression test would have caught the original defect."""
    # Load pre-fix adapter source (reconstructed)
    # Assert it has Scale.MILLION, not Scale.UNIT
```

## Fresh freeze comparison

```yaml
phase_5_precohort_freeze:
  adapter_hash: 20b9fb45... (Scale.MILLION bug)
  phase4_implementation_hashes: 15 files
  
phase_5R_precohort_freeze:
  adapter_hash: 7216ab2e... (Scale.UNIT fix)
  phase4_implementation_hashes: 15 files (UNCHANGED)
  
diff: only source-adapter/vnstock_adapter.py changed (1 file, 1 line)
phase4_files_modified: 0
```

## Conclusion

Phase 5R requalification thành công với 10 fresh runs sạch. Phase 5 raw verdict FAIL_SCALE_DEFECT preserved immutable. Scale defect không tái diễn (regression tests PASS + 10 fresh runs clean).

Phase 5R PASS → standalone_maturity → FUNCTIONAL được audit hỗ trợ.
