# Phase 6 Owner Review — vn-valuation-engine

**Date:** 2026-07-21
**Phase:** PHASE_6_PARENT_INTEGRATION_REGRESSION
**Status:** **FAIL_ADAPTER_OR_MAPPING** — integration_maturity NOT_YET_REQUALIFIED

## Tóm tắt cho owner

```yaml
vn_valuation_engine:
  phase_6:
    fixtures_tested: 8 (5 tickers × coverage)
    adapter_tests: 40/40 PASS
    PITs_passed: 8/8
    mutations_executed: 28
    mutations_survived: 18 (10 CRITICAL + 8 MAJOR)
    reproducibility: 8/8 fixtures stable (×2 reps)
    gate_result: FAIL_ADAPTER_OR_MAPPING
    
  standalone_maturity: FUNCTIONAL (unchanged from Phase 5R)
  integration_maturity: NOT_YET_REQUALIFIED
  implementation_status: GENUINE_BASELINE_REQUALIFIED

parent_integrity:
  equity_research_vn: byte-for-byte unchanged (505 files)
  phase4_core: unchanged (15 files)
  collector: unchanged
  news_digest: unchanged
```

## Phát hiện chính

Phase 6 đã **thành công trong 3/4 subphases**:

```yaml
P6A_input_freeze: PASS
  - 8 fixtures selected with 13/13 coverage categories
  - Parent + child + protected components hash-locked
  - Parent re-audit v0.2.0 verified (17/17 hard gates, ROBUST verification layer)

P6B_adapter_candidate: PASS
  - 5 integration components built (versioned adapter v1.0.0)
  - 40/40 adapter unit tests PASS (8 clean + 12 negative + 4 reproducibility × parametrized)
  - 0 lossy mappings, 0 silent renames, 0 parent recalculations

P6C_eight_PITs: PASS (8/8)
  - PIT-1 Schema Compatibility: PASS (8 fixtures + 8 negatives)
  - PIT-2 Entity Alignment: PASS
  - PIT-3 Method Results Mapping: PASS
  - PIT-4 Calculation Trace + Provenance: PASS (with documented limitations)
  - PIT-5 Applicability + Failure Propagation: PASS
  - PIT-6 Financial DATA Integrity: PASS
  - PIT-7 Dual Verifier Agreement: PASS
  - PIT-8 End-to-End Parent Orchestration: PASS

P6D_mutation_requalification: FAIL
  - 28 mutations executed across 7 categories
  - 10 detected, 18 survived (10 CRITICAL + 8 MAJOR)
  - Reproducibility: 8/8 fixtures × 2 reps stable ✓
```

## Tại sao P6D FAIL

Phase 6 đã thiết kế adapter theo nguyên tắc **lossless mapping**: adapter chỉ preserve cấu trúc child output, không tính lại formulas. Điều này đúng về kiến trúc (adapter không có quyền tính lại — đó là job của child runner/verifier).

Tuy nhiên, khi test với 28 adversarial mutations, **adapter không phát hiện được các semantic vi phạm**:

```yaml
critical_mutations_not_caught_by_any_layer:
  - MUT-INT-005: drop_method (schema) — adapter preserves what's given
  - MUT-INT-007: company_mismatch (entity) — adapter không check company semantics
  - MUT-INT-010: selected_multiple_changed (formula) — adapter không recompute
  - MUT-INT-014: NOT_APPLICABLE→VALID (applicability) — adapter không validate sector rules
  - MUT-INT-016: fatal_error_removed (applicability) — adapter không require errors presence
  - MUT-INT-017: net_debt_sign_reversed (bridge) — adapter không sum-check bridge
  - MUT-INT-018: minority_interest_removed (bridge) — same
  - MUT-INT-019: cash_double_counted (bridge) — same
  - MUT-INT-020: shares_x1000 (bridge) — adapter không range-check (MUT-F7 known gap)

major_mutations_not_caught:
  - formula_id / benchmark / premium / scope / provenance — adapter không validate registry
```

## Root cause

```yaml
architecture_limitation:
  adapter_role: "Lossless mapping (correct by design)"
  adapter_does_not: "Recompute formulas, validate semantic correctness"
  
  child_verifier_limitation: |
    Phase 4 frozen verifier có các checks:
    - VVE-REQ-076: calculation_trace present for VALID methods
    - VVE-REQ-059: recompute implied_price matches
    - VVE-REQ-071: equity bridge balance
    
    Tuy nhiên:
    - VVE-REQ-071 chỉ check bridge_balanced flag, không recompute bridge items
    - Không có applicability consistency check (NA method with VALID price)
    - Không có shares range sanity (MUT-F7 known gap)
    - Không có provenance presence requirement
```

## Defense-in-depth analysis

Tôi đã chạy mỗi mutation qua 3 layers:
- **SCHEMA_ADAPTER**: bắt được 7 mutations
- **CHILD_VERIFIER**: bắt được 1 mutation (MUT-INT-013 implied_price changed)
- **INTEGRATION_VALIDATOR**: bắt được 0 thêm

Tổng: 10/28 detected. 18 survived.

## 3 hướng xử lý cho owner

### Option A — Chấp nhận FAIL với documented gaps (Recommended)

```yaml
option_A:
  description: |
    Accept Phase 6 FAIL. Adapter is correct by design (lossless mapping).
    18 survived mutations reveal gaps in child verifier (Phase 4 frozen)
    that require a separate remediation phase.
  
  rationale: |
    - PITs all PASS: integration boundary is structurally correct
    - Reproducibility PASS: pipeline deterministic
    - Survived mutations target SEMANTIC correctness, not STRUCTURAL
    - Adapter is correct — gap is in defense-in-depth
  
  outcome:
    phase_6: FAIL_ADAPTER_OR_MAPPING (documented)
    standalone_maturity: FUNCTIONAL (unchanged)
    integration_maturity: NOT_YET_REQUALIFIED
    next_phase: Phase 4F (child verifier remediation) — optional, separate directive
```

### Option B — Strengthen adapter v1.1.0 với defense-in-depth

```yaml
option_B:
  description: |
    Upgrade adapter from v1.0.0 (lossless only) to v1.1.0 (lossless + defense-in-depth).
    Add adapter-side checks:
    - Bridge sum balance check (catches MUT-INT-017/018/019)
    - Shares range check (catches MUT-INT-020)
    - Applicability consistency (catches MUT-INT-014/016)
    - Formula registry cross-check (catches MUT-INT-009/011)
  
  advantage: Catches most CRITICAL survived mutations without modifying Phase 4 frozen verifier.
  cost: New adapter version + re-run P6B/P6C/P6D (no parent/child changes).
  estimated: 1 phiên.
```

### Option C — Phase 4F child verifier remediation

```yaml
option_C:
  description: |
    Open Phase 4F to strengthen child verifier (Phase 4 frozen files modified).
    Add VVE-REQ-077 bridge recompute, VVE-REQ-078 applicability consistency,
    VVE-REQ-079 shares range, VVE-REQ-080 provenance presence.
  
  cost: Modifies Phase 4 frozen files → requires regression testing + maturity reassessment.
  estimated: 2 phiên.
```

## Cam kết đã giữ

✓ Không sửa equity-research-vn 1.1.0 (505 files byte-for-byte unchanged)
✓ Không sửa Phase 4 frozen implementation (15 files unchanged)
✓ Không sửa vn-financial-data-collector
✓ Không sửa vn-news-digest
✓ Không patch trong P6C/P6D frozen batch
✓ Không hạ gate mutation ( Directive §22 yêu cầu 0 critical survived)
✓ Không retry until PASS
✓ Không declare PRODUCTION_INTEGRATED
✓ Không deploy integration

## Trạng thái cuối

```yaml
phase_6_reported_result: FAIL_ADAPTER_OR_MAPPING
phase_6_gate_passed: false
mutations_survived: 18 (10 CRITICAL + 8 MAJOR)
parent_unchanged: true (byte-for-byte)
phase4_core_unchanged: true
protected_components_unchanged: true
production_integration_authorized: false
deployment_authorized: false
owner_review_required: true
recommended_next_action: Option A, B, or C (see above)
```

Phase 6 đã hoàn thành trung thực: 8/8 PITs PASS, reproducibility PASS, nhưng mutation gate FAIL với 18 survived mutations. Đây là bằng chứng cho thấy verification stack hiện tại có gaps ở defense-in-depth — adapter đúng về thiết kế (lossless mapping), nhưng không đủ để catch adversarial semantic mutations. Owner cần quyết định hướng xử lý.
