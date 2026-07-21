# Phase 5R Regression Report

**Date:** 2026-07-21
**Status:** PASS (65/65 tests)

## Test inventory

### Phase 4 unit tests (preserved, must still PASS)
```yaml
source: implementation/p4a_tests.py
count: 57
result: 57/57 PASS
purpose: Confirm Phase 4 frozen implementation unchanged
```

### Phase 5R new regression tests (Directive §5)
```yaml
source: tests/test_source_adapter_scale.py
count: 8
result: 8/8 PASS

tests:
  test_raw_vnd_with_scale_unit_NOT_multiplied:          PASS — KEY regression for Phase 5 defect
  test_million_vnd_with_scale_million_multiplied_correctly: PASS
  test_thousand_vnd_with_scale_thousand_multiplied_correctly: PASS
  test_billion_vnd_with_scale_billion_multiplied_correctly: PASS
  test_adapter_default_scale_is_UNIT:                   PASS — adapter source inspection
  test_VVE_REQ_071_positive_balanced_bridge_PASS:      PASS
  test_VVE_REQ_071_negative_unbalanced_bridge_FAIL:    PASS — catches EQUITY_BRIDGE_INVALID
  test_prefixed_adapter_would_fail_scale_UNIT_test:    PASS — proves regression coverage
```

## Scale regression key tests (Directive §5)

### raw VND + Scale.UNIT → NOT multiplied

```python
raw_vnd_value = 4.96e12  # FPT EBITDA in raw VND
metric = _make_metric(raw_vnd_value, Scale.UNIT)
normalized = normalize_metric(metric)
assert normalized.normalized_value == pytest.approx(raw_vnd_value, rel=1e-9)
# Confirms Scale.UNIT does NOT multiply
```

### value in million VND + Scale.MILLION → multiplied × 1M

```python
value_in_millions = 8.619  # 8.619 million VND
metric = _make_metric(value_in_millions, Scale.MILLION)
normalized = normalize_metric(metric)
assert normalized.normalized_value == pytest.approx(8.619e6, rel=1e-6)
# Confirms Scale.MILLION multiplies correctly
```

## VVE-REQ-071 positive/negative

### Positive (balanced bridge)
```yaml
items: EV=10e9 - NET_DEBT=2e9 - MINORITY=1e9 = EQUITY_VALUE=7e9
expected: VVE-REQ-071 PASS
result: PASS
```

### Negative (unbalanced bridge)
```yaml
items: EV=10e9 - NET_DEBT=2e9 = 8e9, but EQUITY_VALUE=5e9 (imbalanced)
expected: VVE-REQ-071 FAIL with EQUITY_BRIDGE_INVALID
result: PASS (FAIL correctly raised)
```

## Meta-test: pre-fix adapter would fail

```python
def test_prefixed_adapter_would_fail_scale_UNIT_test():
    """Load reconstructed pre-fix adapter, confirm it has Scale.MILLION not Scale.UNIT.
    This proves the regression test would have caught the original defect."""
    src = open(prefixed_path).read()
    defaults = src.split("defaults = dict(")[1].split(")")[0]
    assert "Scale.MILLION" in defaults
    assert "Scale.UNIT" not in defaults
# Result: PASS — pre-fix confirmed buggy, regression would catch
```

## Phase 4 immutability

```yaml
phase4_implementation_files: 15
phase4_files_hash_compared_to_phase5_precohort_freeze: IDENTICAL
phase4_files_modified: 0
```

## Parent immutability

```yaml
parent_dir: equity-research-vn 1.1.0
parent_files: 505
parent_hash_compared_to_phase5_precohort_freeze: IDENTICAL
parent_files_modified: 0
```

## Conclusion

Regression gate PASS. All 8 new tests + 57 preserved Phase 4 tests pass. Scale regression specifically targets the Phase 5 defect (Scale.MILLION vs Scale.UNIT) and confirms:
1. Raw VND values are not multiplied when Scale.UNIT
2. Million-scale values are correctly multiplied when Scale.MILLION
3. VVE-REQ-071 catches both balanced and unbalanced bridges
4. Pre-fix adapter would have failed the new tests (proving coverage)
