# Phase 4R — Survivor Root-Cause & Requirement Mapping

**Subphase:** P4R-A
**Workspace:** `/Users/bobo/ZCodeProject/vn-fundamental-analysis-phase4R/`
**Source:** `phase4Q-mutation-manifest.json` (verdict `FAIL_MUTATION_GATE`, **IMMUTABLE**)
**Protocol:** Phase 4R là batch độc lập, không pool với Phase 4Q, không rewrite verdict cũ.

---

## 1. Tóm tắt cho owner (đời thường)

Phase 4Q chạy 32 đột biến (giống như 32 "bài kiểm tra gian lận" — ta cố tình hỏng dữ liệu rồi xem engine có phát hiện không). Kết quả:

- **17/32 bị phát hiện đúng** ✅ — engine khỏe ở phần số học đơn giản (sai số tỷ, sai số cổ phiếu, thiếu số bị thay 0, v.v.).
- **15/32 lọt qua** ❌ — engine không phát hiện vì nó **chỉ nhìn con số, không nhìn "danh tính" của con số đó**.

Hình dung:today công ty phát hành thêm cổ phiếu, năm nay có 2 cách đếm cổ phiếu — **trung bình cả năm** và **cuối kỳ**. Nếu ai đó đánh tráo hai con số đó (chỉ khác nhau vài %), engine Phase 4 chỉ thấy "con số trông hợp lý" nên PASS. Nó không biết con số đó thuộc nhãn "trung bình" hay "cuối kỳ".

15 lỗ hổng này rơi thành 4 nhóm:

| Nhóm | Số lượng | Đặc điểm |
|---|---|---|
| Khoảng trống kiểm tra cấu trúc (structural validation gap) | 8 | Engine không gắn "nhãn" (basis/period/scope/status) vào từng con số |
| Peer engine chưa triển khai | 4 | Module đối chiếu công ty cùng ngành chưa tồn tại (thư mục rỗng) |
| Khoảng trống nhận thức scope | 2 | Không phân biệt consolidated vs standalone, attributable vs total |
| Khoảng trống thực thi nguồn gốc | 1 | Không hash-bind từng số với nguồn chứng cứ |

**0 CRITICAL survived** — engine đã vững ở những thứ nguy hiểm nhất. Còn lại 1 HIGH, 10 MAJOR, 4 MEDIUM.

---

## 2. Bảng ánh xạ 15 survivors

| # | Mutation | Severity | Target | Root cause class | REQ | Component sẽ sửa | Test regression |
|---|---|---|---|---|---|---|---|
| 1 | MUT-FUND-008 | MAJOR | period-end shares giả dạng weighted-avg | STRUCTURAL_VALIDATION_GAP | VFA-REQ-009 | normalization/share_basis_policy.py (NEW) + verifier | P4R-TEST-STRUCT-001 |
| 2 | MUT-FUND-009 | MAJOR | basic shares ↔ diluted | STRUCTURAL_VALIDATION_GAP | VFA-REQ-009 | normalization/share_basis_policy.py + verifier | P4R-TEST-STRUCT-002 |
| 3 | MUT-FUND-013 | MAJOR | ROE dùng ending equity âm thầm | STRUCTURAL_VALIDATION_GAP | VFA-REQ-006,013 | normalization/denominator_basis_policy.py (NEW) + verifier | P4R-TEST-STRUCT-003 |
| 4 | MUT-FUND-014 | MAJOR | ROA denominator đổi ra equity | STRUCTURAL_VALIDATION_GAP | VFA-REQ-014,016 | formula_engine.py + verifier | P4R-TEST-STRUCT-004 |
| 5 | MUT-FUND-016 | HIGH | DuPont EM dùng ending | STRUCTURAL_VALIDATION_GAP | VFA-REQ-018,024 | denominator_basis_policy.py + dupont + verifier | P4R-TEST-STRUCT-005 |
| 6 | MUT-FUND-019 | HIGH | INPUT_INCOMPLETE → VALID | STRUCTURAL_VALIDATION_GAP | VFA-REQ-021,022,029 | applicability/status_policy.py (NEW) + export + verifier | P4R-TEST-STRUCT-006 |
| 7 | MUT-FUND-023 | MAJOR | TTM numerator + quarter denominator | STRUCTURAL_VALIDATION_GAP (period) | VFA-REQ-006 | normalization/period_scope_policy.py (NEW) + verifier | P4R-TEST-STRUCT-007 |
| 8 | MUT-FUND-026 | MAJOR | avg → ending silently (general) | STRUCTURAL_VALIDATION_GAP | VFA-REQ-006 | denominator_basis_policy.py + verifier | P4R-TEST-STRUCT-008 |
| 9 | MUT-FUND-027 | MEDIUM | peer bị xóa | PEER_ENGINE_NOT_IMPLEMENTED | VFA-REQ-026 | peers/peer_engine.py (NEW) | P4R-TEST-PEER-001 |
| 10 | MUT-FUND-028 | MEDIUM | median ↔ mean | PEER_ENGINE_NOT_IMPLEMENTED | VFA-REQ-026 | peers/peer_engine.py + peer_policy.py | P4R-TEST-PEER-002 |
| 11 | MUT-FUND-029 | MEDIUM | peer sai period | PEER_ENGINE_NOT_IMPLEMENTED | VFA-REQ-026,006 | peers/peer_engine.py | P4R-TEST-PEER-003 |
| 12 | MUT-FUND-030 | MEDIUM | coverage <3 vẫn rank | PEER_ENGINE_NOT_IMPLEMENTED | VFA-REQ-026 | peers/peer_engine.py | P4R-TEST-PEER-004 |
| 13 | MUT-FUND-024 | MAJOR | consolidated ↔ standalone | SCOPE_AWARENESS_GAP | VFA-REQ-007 | normalization/scope_policy.py (NEW) + verifier | P4R-TEST-SCOPE-001 |
| 14 | MUT-FUND-025 | MAJOR | attributable NI + total equity | SCOPE_AWARENESS_GAP | VFA-REQ-007,011 | normalization/scope_policy.py + verifier | P4R-TEST-SCOPE-002 |
| 15 | MUT-FUND-031 | MAJOR | provenance bị xóa khỏi EPS | PROVENANCE_ENFORCEMENT_GAP | VFA-REQ-027,032 | provenance/provenance_engine.py (NEW) + verifier | P4R-TEST-PROV-001 |

---

## 3. Oracle integrity check

Theo directive §8, không được tự động gọi survivor là "oracle defect". Tôi đã kiểm chứng:

- **Target field exists:** cả 15 đột biến đều đánh vào field có thật trong schema (basis, period, scope, status, provenance).
- **Fixture precondition satisfiable:** cả 15 đều dựng được fixture hợp lệ (chỉ cần 2 năm số liệu + 1 peer set tối thiểu).
- **Material semantic change:** cả 15 đều tạo khác biệt ngữ nghĩa thật (không phải no-op).
- **Không wrong-target:** cả 15 đều đánh đúng canonical target (ví dụ EM đánh vào avg denominator, không phải vào trace).

Kết luận: **0 oracle defect**. 15 survivor là 15 implementation gap thật sự.

---

## 4. P4R-A gate

```yaml
P4R_A_gate:
  survivors_registered: 15/15
  requirements_mapped: 15/15
  component_owners_mapped: 15/15
  root_causes_assigned: 15/15
  remediation_designs_defined: 15/15
  regression_tests_planned: 15/15

  unresolved_root_causes: 0
  severity_reductions: 0
  auto_oracle_defect_count: 0

  verdict: PASS
```

Registry JSON chi tiết (mỗi survivor có: severity, expected_error, expected_primary_owner, observed_phase4Q_verdict, root_cause_class, root_cause_detail, affected_requirement_ids, affected_component, downstream_risk, remediation_design, regression_test_ids): `manifests/phase4R-survivor-registry.json`.

---

## 5. Bước tiếp theo

Chuyển sang **P4R-B: Structural validation hardening**. Patch theo thứ tự:

1. Mở rộng `models.py` thêm binding `share_basis`, `period_kind`, `denominator_basis`, `reporting_scope`, `attribution_scope`, `provenance` trên `MetricInput` / `MetricResult` / `CalculationStep`.
2. Tạo `normalization/share_basis_policy.py` (MUT-008/009).
3. Tạo `normalization/denominator_basis_policy.py` (MUT-013/016/026).
4. Mở rộng `formula_engine.py` thêm formula_input_identity binding (MUT-014).
5. Tạo `applicability/status_policy.py` + siết export gate (MUT-019).
6. Tạo `normalization/period_scope_policy.py` (MUT-023).

Sau khi structural xong, P4R-C triển khai peer engine + scope + provenance; rồi P4R-D fixtures, P4R-E oracle meta, P4R-F mutation requalification 32/32, P4R-G reproducibility + final gate.
