# Phase 5 Owner Review — vn-valuation-engine

**Date:** 2026-07-21
**Phase:** PHASE_5_GENUINE_BASELINE_COHORT
**Status:** **PASS** — standalone_maturity upgraded từ PROTOTYPE_OPERATIONAL → FUNCTIONAL

## Tóm tắt cho owner

```yaml
vn_valuation_engine:
  phase_1: PASS
  phase_2: PASS
  phase_3: PASS
  phase_4: PASS
  phase_5: PASS                              ← MỚI

  implementation_status: GENUINE_BASELINE_VALIDATED   ← nâng cấp
  standalone_maturity: FUNCTIONAL                     ← nâng cấp
  integration_maturity: NOT_YET_REQUALIFIED

parent:
  skill: equity-research-vn
  version: 1.1.0
  status: RELEASED_IMMUTABLE_LKG (unchanged byte-for-byte)

protected_children_unchanged:
  vn_financial_data_collector: true
  vn_news_digest: true
```

## Đã làm trong Phase 5

1. **P5A Cohort Freeze**: 5 tickers (VCB, BVH, HPG, MWG, FPT) covering 5 sector categories + special coverage cho MUT-F5 (minority interest) và MUT-F7 (shares range)
2. **P5B Live Preflight**: Identity + market + financial data resolved 5/5 qua vnstock API; raw snapshots preserved với SHA-256 hashes
3. **P5C Genuine Execution**: 10 runs (2 per ticker) qua 14-stage pipeline. **1 defect quan trọng bị bắt giữa chừng** (scale error × 1M trong source adapter) → safety stop → fix → re-run thành công
4. **P5D Verification + Paired Analysis**: Independent verifier PASS 10/10; deterministic replay 10/10 hash stable; paired methods_equal 5/5
5. **P5E Phase 5 Gate**: Tất cả gate conditions đáp ứng

## Kết quả chính

### 10 genuine runs

```yaml
ticker_runs:
  VCB-A: PASS (1 VALID: PE)              # banking — EV/EBITDA correctly NOT_APPLICABLE
  VCB-B: PASS (1 VALID)
  BVH-A: PASS (2 VALID: PE, P_CF)        # insurance — P_S NOT_APPLICABLE
  BVH-B: PASS (2 VALID)
  HPG-A: PASS (6 VALID: PE, PB, Graham, EV/EBITDA, P/CF, P/S)
  HPG-B: PASS (6 VALID)
  MWG-A: PASS (6 VALID)
  MWG-B: PASS (6 VALID)
  FPT-A: PASS (6 VALID)
  FPT-B: PASS (6 VALID)

total_methods_VALID: 42
total_methods_NA: 6
total_methods_INPUT_INCOMPLETE: 22 (mostly DCF FCFF missing forecast — fail-closed, not fabricated)
```

### Verdicts

```yaml
independent_verifier: 10/10 PASS
deterministic_replay: 10/10 semantically stable
paired_stability: 5/5 methods_equal
MUT_F5: PASS (3/5 tickers có minority, all included correctly)
MUT_F7: PASS (5/5 cross-check shares × price = market_cap chính xác 0.000%)

safety:
  fabricated_inputs: 0
  cross_ticker_contamination: 0
  unsupported_target_prices: 0
  unbalanced_bridge_false_pass: 0
  fatal_error_with_PASS: 0
  verifier_errors: 0
  secret_leaks: 0
```

## Defect caught giữa chừng (quan trọng)

Phase 5 không hoàn toàn clean — có 1 CRITICAL defect bị bắt:

```yaml
defect:
  id: SCALE_ERROR_FPT_EBITDA_x1M
  component: source-adapter/vnstock_adapter.py (Phase 5 NEW — không thuộc Phase 4 frozen)
  severity: CRITICAL (Directive §11 safety stop)
  trigger: scale_error_with_material_valuation_impact

root_cause: |
  Adapter set Scale.MILLION cho raw VND values từ vnstock.
  vnstock trả values ở VND UNIT (e.g., FPT EBITDA = 4.96e12 VND).
  Unit_currency_engine nhân × 1M → EBITDA = 4.96e18 (sai 1 triệu lần).
  Implied price EV/EBITDA = 25.8 tỷ VND/share (sai — phải là 25,843 VND).

discovery: |
  Independent verifier VVE-REQ-071 (EQUITY_BRIDGE_INVALID) bắt 6/10 runs FAIL.
  Đây là HPG, MWG, FPT (có EV/EBITDA method).
  VCB, BVH PASS vì không có EV-based method.

resolution: |
  Source adapter sửa Scale.MILLION → Scale.UNIT.
  Cohort re-ran với 8s delay giữa runs (rate-limit aware).
  Sau fix: 10/10 verifier PASS, FPT EV/EBITDA = 25,843 VND/share (hợp lý).

phase_4_impact: 0 |
  Phase 4 engines/runner/verifier KHÔNG bị patch.
  Hash verification confirmed: 15 implementation files unchanged.
  Phase 4 standalone_maturity PROTOTYPE_OPERATIONAL được preserve.
```

Đây là **bằng chứng hệ thống an toàn hoạt động đúng**: Phase 4 frozen verifier đã bắt được Phase 5 new component bug. Không có unsafe false PASS ở bất kỳ giai đoạn nào.

## 2 documented gaps đã được kiểm định trên dữ liệu thật

Cả 2 gaps được đưa từ Phase 4 (documented non-blocking) sang Phase 5 để kiểm định trên live data:

### MUT-F5 — Minority Interest Threshold

```yaml
exercised: true
tickers_with_minority: 3/5 (HPG, MWG, FPT)
result: PASS

cases:
  HPG: minority=127B VND (0.10% EV) — engine includes (conservative)
  MWG: minority=6.25B VND (0.01% EV) — engine includes
  FPT: minority=2.30T VND (4.64% EV) — engine includes; FPT là threshold boundary case (~5%)

unsafe_false_pass: 0
```

### MUT-F7 — Shares Range Sanity

```yaml
exercised: true
tickers_checked: 5/5
result: PASS

cross_check: shares × price = market_cap (exact match, 0.000% diff cho 5/5 tickers)
range_check: tất cả shares trong khoảng 10M-100B
unsafe_false_pass: 0
```

## So sánh maturity

```yaml
trước_phase_5:
  implementation_status: SYNTHETICALLY_VALIDATED
  standalone_maturity: PROTOTYPE_OPERATIONAL
  evidence_source: synthetic fixtures (Phase 4 P4D)

sau_phase_5:
  implementation_status: GENUINE_BASELINE_VALIDATED
  standalone_maturity: FUNCTIONAL
  evidence_source: 10 genuine live runs (Phase 5) + synthetic (Phase 4)

không_nâng:
  - STABLE_CANDIDATE (cần long-run evidence, Phase 8)
  - PRODUCTION_READY (cần agent runs + parent integration)
```

## Câu hỏi cho owner

1. **Chấp nhận FUNCTIONAL?** Phase 5 PASS với 10/10 acceptable runs, verifier 10/10 PASS, MUT-F5/F7 PASS, no safety violations.
2. **Phase 6 next?** Parent integration regression (8 PITs) cho vn-valuation-engine — sẽ yêu cầu directive mới.
3. **Skills khác?** vn-fundamental-analysis, vn-technical-analysis, vn-research-dashboard chưa harness.
4. **Apply P0-1 cho equity-research-vn?** Oracle spec gap còn sót lại từ re-audit.

## Trạng thái cuối

```yaml
phase_5_reported_result: PASS
phase_5_gate_passed: true
maturity_upgrade: PROTOTYPE_OPERATIONAL → FUNCTIONAL
parent_unchanged: true (505 files byte-for-byte)
phase_4_implementation_unchanged: true (15 files)
phase_6_authorized: false
parent_integration_authorized: false
owner_review_required: true
```

Phase 5 đã chứng minh vn-valuation-engine vận hành được trên dữ liệu thật với 10 acceptable runs, không có safety violation. Hệ thống deterministic shell + independent verifier đã làm đúng vai trò khi bắt được 1 defect trong source adapter mà không cho phép unsafe PASS.
