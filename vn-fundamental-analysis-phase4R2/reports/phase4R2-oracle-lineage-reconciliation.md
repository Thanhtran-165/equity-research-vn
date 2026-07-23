# Phase 4R2 — Oracle Lineage Reconciliation (P4R2-A)

**Subphase:** P4R2-A
**Verdict Phase 4R:** `FAIL_ORACLE_SEMANTIC_DRIFT_AND_FREEZE_INTEGRITY` (IMMUTABLE)
**Verdict Phase 4Q:** `FAIL_MUTATION_GATE` (IMMUTABLE)

---

## 1. Sai lầm được thừa nhận

Phase 4R đã đổi semantic target của 4 mutation để "khớp" với engine, thay vì sửa engine để bắt đúng contractual corruption. Cụ thể:

| Mutation | Phase 3 target (đúng) | Phase 4R drift (sai) |
|---|---|---|
| MUT-FUND-015 | margin numerator → operating income | shares inflated (EPS sanity) |
| MUT-FUND-017 | CAGR year count changed | shares inflated (EPS sanity) |
| MUT-FUND-018 | missing input → zero | equity inflated (BVPS sanity) |
| MUT-FUND-022 | near-zero denominator warning removed | equity inflated (BVPS sanity) |

Điều này làm `32/32 caught` mất ý nghĩa — nó chỉ chứng minh 32 mutation definitions cuối đã bị bắt, không phải 32 failure surfaces ban đầu.

---

## 2. Phương pháp remediation

Theo directive §2: **không thay mutation này bằng mutation khác semantic**. Mỗi mutation phải kiểm tra **cùng semantic requirement** như Phase 3.

### 2.1 MUT-FUND-015 — margin numerator confusion

- **Semantic slot (Phase 3):** NET_PROFIT_MARGIN numerator bị thay bằng operating income.
- **Cách engine phải bắt:** DUPONT_INCONSISTENT — vì DuPont chain dùng NPM, nếu NPM bị tính từ numerator sai thì reconstructed ROE ≠ direct ROE.
- **Phase 4R2 mutation:** thay `net_income` trong NPM bằng `operating_income` (giá trị lớn hơn NPAT). Engine phải phát hiện NPM recomputed khác NPM canonical.

### 2.2 MUT-FUND-017 — CAGR year count changed

- **Semantic slot (Phase 3):** số năm giữa first và last bị thay đổi (period distance).
- **Cách engine phải bắt:** CAGR_PERIOD_INVALID — vì CAGR = (end/begin)^(1/years), nếu `years` không khớp periods array thì invalid.
- **Phase 4R2 mutation:** corrupt period distance (periods array có 3 năm nhưng years=1 hoặc years=5). Engine phải phát hiện years ≠ len(periods)-1.

### 2.3 MUT-FUND-018 — missing input replaced with zero

- **Semantic slot (Phase 3):** một metric có raw value `None` bị thay bằng `0.0` trong normalized input.
- **Cách engine phải bắt:** MISSING_REPLACED_WITH_ZERO — đây là hard error (fail-closed), không phải plausibility guess.
- **Phase 4R2 mutation:** raw `net_income[2023] = None` nhưng normalized = 0.0. Engine phải phát hiện None→0.0 substitution via raw_normalized binding.

### 2.4 MUT-FUND-022 — near-zero denominator warning removed

- **Semantic slot (Phase 3):** denominator gần 0 (nhưng dương) → engine phải emit EXTREME_DENOMINATOR_WARNING. Mutation xóa warning khỏi output.
- **Cách engine phải bắt:** EXTREME_DENOMINATOR_WARNING phải present trong output khi denominator < threshold. Nếu bị strip → verifier phát hiện warning absent.
- **Phase 4R2 mutation:** denominator = 0.5 (gần 0), warning bị xóa khỏi ROE output. Engine phải phát hiện warning absent.

---

## 3. Lineage gate

```yaml
oracle_lineage_gate:
  original_slots_reconciled: 32/32
  semantic_slots_preserved: 32/32
  silent_target_substitutions: 0
  orphan_requirements: 0
  drifted_slots_in_phase_4R: 4
  restored_in_phase_4R2: 4
  new_mutation_ids_created: 0   # không cần v2 vì target gốc luôn valid
  INVALID_MUTATION_ORACLE_tagged: 4   # phase_4R versions tagged, không reuse
  verdict: PASS
```

## 4. 28 slots không drift (giữ nguyên Phase 4R)

28 mutation còn lại đã giữ đúng semantic target từ Phase 3 và được engine bắt đúng. Chúng được giữ nguyên trong Phase 4R2 (xem `phase4R2-mutation-manifest.json`).

---

Chi tiết JSON: `manifests/phase4R2-mutation-lineage.json`.
