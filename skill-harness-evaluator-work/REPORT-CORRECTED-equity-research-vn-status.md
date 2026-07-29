# Báo cáo chính thức — Trạng thái `equity-research-vn`

**Ngày:** 2026-07-29
**Trạng thái:** `OFFICIAL_READY` — đã được Sol ACCEPT làm báo cáo chính thức
**Phạm vi:** Rà soát lại toàn bộ artifacts audit sau khi báo cáo v0.1.0 bị phát hiện đã lỗi thời
**Nguyên tắc:** Mỗi con số ghi rõ nguồn file. Phân biệt *owner-declared* vs *independently-verified*. Giới hạn scope mỗi kết luận. Không nhân đôi runs. Không gọi "mới nhất" khi chỉ mới nhất *trong tập đã khảo sát*.

---

## 1. Nhận lỗi về báo cáo trước

Báo cáo trước (`FAIL / EXPERIMENTAL / genuine_agent_runs: 0`) là kết quả **audit protocol v0.1.0** (12/7) ở thư mục cũ `skill-harness-evaluator-work/`. Trạng thái đó **đã lỗi thời**. Công việc đã tiếp tục qua nhiều protocol versions ở `/Users/bobo/ZCodeProject/agent-eval/`.

```yaml
historical_audit_v0_1_0:
  protocol: 0.1.0
  verdict: FAIL
  maturity: EXPERIMENTAL
  genuine_agent_runs_reported: 0   # ← SAI với hiện tại
  status: SUPERSEDED_HISTORICAL_RESULT
```

---

## 2. Trạng thái release (do owner công bố — KHÔNG phải do evaluator chứng minh)

```yaml
target_release:
  version: 1.1.0
  architecture: HYBRID_DETERMINISTIC_SHELL
  owner_release_label: PRODUCTION_READY
  owner_signoff: true
  release_date: 2026-07-20
  source_files:
    - equity-research-vn/VERSION
    - equity-research-vn/architecture/manifests/RELEASE-MANIFEST.json
  incident_closed: ERVN-PERIOD-001
```

**Lưu ý:** `PRODUCTION_READY` là **nhãn do owner đặt + signoff**. Đây KHÔNG phải kết quả do evaluator chứng minh độc lập.

```yaml
owner_declared_maturity: PRODUCTION_READY              # ĐÚNG, verify từ file
independently_verified_production_readiness: UNCONFIRMED   # chưa có canonical scorecard
```

---

## 3. Evaluator protocol — "mới nhất trong tập đã khảo sát", chưa chắc là canonical authority

Em tìm thấy chuỗi protocol versions trong `agent-eval/`, mỗi file đều có `frozen_before_execution: true` và SHA-256 hash khớp khi recomputed.

```yaml
audit_protocol:
  latest_locked_version_located: 0.12.0
  lock_hash_verified: true                       # 94a64b3a... recomputed = stored
  frozen_before_execution: true
  frozen_at: 2026-07-16T10:00:00
  verification_layer_version: 0.1.6
  all_located_protocols_hash_verified: true

  canonical_latest_protocol:
    status: UNCONFIRMED
    reason: no protocol registry or consolidated supersession manifest located
```

**Chỉnh sửa #3 của anh:** việc tìm thấy lock v0.12.0 chỉ chứng minh đây là protocol mới nhất **trong tập artifact em đã khảo sát**. Dự án có nhiều workstream Phase D/E/F và workspace thế hệ sau, nhưng chưa có registry nối chúng trực tiếp vào chuỗi `agent-eval v0.2.0 → v0.12.0`. Không backward-pool kết quả các workstream đó vào scorecard này.

---

## 4. Genuine agent runs — phân loại theo cấp độ evidence

Em đếm bằng `run_id` / `logical_run_id` để dedup, **rồi phân loại từng record theo bằng chứng agent invocation**. Không phải record nào cũng đủ evidence để gọi là "genuine execution".

**Quan trọng:** 12 records có `duration ≤ 30s` (0.1–3.3s) → đây là **re-score/verifier-only**, KHÔNG phải genuine agent run. Gồm `phase5-news-digest` (NND-*, 0.2–3.3s) và 2 `phase-F-shadow` PNJ (SH-PNJ-*, 0.1s).

```yaml
genuine_run_inventory:
  unique_run_ids_located: 74
  raw_artifact_run_mentions: 110
  records_without_deduplicable_ID: 24       # Cohort C/C-prime/targeted-v5

  # Phân loại theo evidence-of-genuine-invocation:
  evidence_classification:
    L1_explicit_label_genuine_agent:        # execution_type: genuine_agent + duration>30s
      count: 12                              # targeted-hotfix (logical runs, đã dedup)
      confidence: HIGH
    L2_duration_signature_no_label:         # duration>30s (agent signature) nhưng không label
      count: 50                              # phase-E/F-soak/F-shadow (trừ 2 PNJ)
      confidence: MEDIUM                     # có thể là deterministic re-run, chưa confirm
    L3_NOT_genuine_rescore_only:             # duration≤30s → re-score/verifier, KHÔNG genuine
      count: 12                              # phase5-news-digest (10) + 2 phase-F-shadow PNJ
      confidence: HIGH_that_NOT_genuine

  # Phép dedup L1 — cần ghi rõ để tránh hiểu lầm:
  deduplication_note:
    rc3_rc4_record_mentions_with_genuine_label: 24   # 12 rc3 + 12 rc4
    rc3_rc4_are_same_logical_runs_two_verifiers: true
    deduplicated_unique_genuine_agent_runs: 12
    note: "Hai con số 24 và 12 không mâu thuẫn — 24 là mentions, 12 là logical runs sau dedup"

  # Số genuine theo evidence — KHÔNG gọi 62 là "confirmed genuine":
  strictly_labeled_unique_minimum: 12        # chỉ L1
  likely_additional_unique_runs: 50          # L2, basis=runtime_signature, NOT_EXPLICITLY_LABELED
  genuine_or_likely_genuine_upper_observation: 62   # L1+L2, không phải "confirmed"
  theoretical_upper_bound_incl_unenumerable: 86     # 62 + 24 nếu đều genuine

  identified_duplicate_mentions:
    rc3_rc4_overlap: 12                      # cùng logical runs, 2 verifier versions

  confirmed_unique_minimum: 74               # = 12 + 50 + 12 (tổng unique IDs, mọi cấp)
  exact_unique_total: UNRESOLVED
  zero_genuine_runs_claim: REJECTED          # chắc chắn ≥12 genuine

  overlap_statement:
    only_detected_overlap_among_identifiable_ids: rc3_vs_rc4
    undiscovered_cross_scheme_overlap_possible: true

# Lưu ý về heuristic thời gian:
duration_heuristic:
  threshold_seconds: 30
  purpose: evidence_classification_only
  treated_as_proof_of_agent_execution: false   # không phải định nghĩa bản thể của genuine
rescore_exclusion:
  based_on:
    - extremely_short_duration                 # 0.1–3.3s
    - cohort_context
    - verifier_or_rescore_artifact_structure
```

**Overlap duy nhất phát hiện được trong các records có identifier đủ để đối chiếu là 12 runs giữa rc3 và rc4.** Không khẳng định không có overlap khác, vì 24 records thiếu run_id và các cohort dùng naming schemes khác nhau (SO-*, TH-*, NND-*, TV5-*, logical_run_id).

**Về phép dedup 24→12:** rc3 và rc4 ghi 12 records `genuine_agent` mỗi cohort (tổng 24 mentions), nhưng đây là **cùng 12 logical runs được đánh giá lại qua 2 verifier versions**. Sau dedup còn 12 unique. Hai con số không mâu thuẫn.

> **Cách diễn đạt an toàn:** Có **12 genuine-agent runs được xác nhận bằng label** (`execution_type: genuine_agent`); thêm **50 runs có dấu hiệu phù hợp với agent execution** (duration >30s) nhưng **chưa có explicit label**. Tổng unique IDs định vị được là 74; trong đó 12 là re-score-only (duration 0.1–3.3s, không genuine). Số genuine executions chính xác vẫn UNRESOLVED. **62 không phải "confirmed genuine runs"** — đó là upper observation gồm L1 + L2.

---

## 5. Kết quả mới nhất theo scope — không supersede lẫn nhau

### 5a. Targeted-v5 (protocol v0.12.0) — **CHỈNH SỬA QUAN TRỌNG NHẤT (#1)**

Protocol v0.12.0 dự kiến **8 runs**, manifest chỉ ghi **4 runs**. Không được gọi đây là "protocol v0.12.0 PASS toàn phần".

```yaml
targeted_validation_v5:
  protocol: 0.12.0
  planned_runs: 8                          # theo protocol lock
  located_runs: 4                          # theo manifest
  located_run_results:
    PASS: 4/4
    requirements: 28/28_per_run
    tickers: [ACB, GEX]

  executed_subset_verdict: PASS
  protocol_completion: 4/8
  full_protocol_verdict: INCOMPLETE        # ← không phải PASS toàn phần
```

Cách ghi đúng trong status tổng:
```yaml
v0_12_0:
  located_execution_subset: PASS
  full_execution_completion: UNCONFIRMED
```

### 5b. Cohort C cross-ticker (v0.7.1, trước đó)

```yaml
cross_ticker_cohort_c:
  protocol: 0.7.1
  date: 2026-07-13
  tickers: [CTD, KDH, PNJ, VCB, FPT]
  runs: 10
  raw_pass: 0/10
  environmental_failures_pct: 75           # vnstock_data không có network ở env
  skill_relevant_pass_excluding_env: 5/10
  recurring_skill_defects_found: [REQ-013, REQ-023, REQ-025]
  later_full_closure_proven: false
```

**Khoảng trống:** Cohort C phát hiện REQ-013/023/025 recurring. Targeted-v5 (sau đó) đóng REQ-013/025 cho ACB/GEX nhưng **không test REQ-023** và **không lặp trên 5 ticker gốc**. Chưa chứng minh defect đóng hoàn toàn cross-ticker.

### 5c. Targeted-hotfix-rc4 (v1.0.1 verifier, sau Cohort C)

```yaml
targeted_hotfix_rc4:
  date: 2026-07-19
  tickers: [BVH, FPT, HPG, MSN, MWG, POW]   # 6 ticker khác Cohort C
  runs: 12
  pass: 8, fail: 4
  failures: [BVH×2 insurance-specific, MSN×1, MWG×1]
  execution_type: genuine_agent
```

---

## 6. Những con số CHƯA có canonical evidence

Em đã tìm trong toàn bộ `agent-eval/` và **không tìm thấy 1 file scorecard tổng** ghi các con số này:

```yaml
canonical_consolidated_scorecard:
  located: false

hard_gates_17_of_17: UNVERIFIED             # không file nào ghi chính xác 17/17 PASS
mutation_suite_6_of_6: UNVERIFIED           # mutation suite chỉ ở thư mục cũ v0.1.0
validator_specificity_1_0: UNVERIFIED
verification_layer_ROBUST: UNVERIFIED
overall_evaluator_maturity: UNRESOLVED
evaluator_certified_production_readiness: UNCONFIRMED
```

Đây không phải kết luận "sai" — chỉ là em chưa tìm thấy file. Nếu file đó tồn tại ở đường dẫn em chưa quét, anh cho em đường dẫn, em sẽ đọc + verify hash.

---

## 7. Trạng thái tổng hợp có thể xác nhận an toàn

```yaml
verified_state_from_located_artifacts:

  historical_audit:
    protocol: 0.1.0
    verdict: FAIL
    maturity: EXPERIMENTAL
    status: SUPERSEDED

  target_release:
    version: 1.1.0
    architecture: HYBRID_DETERMINISTIC_SHELL
    owner_release_label: PRODUCTION_READY
    owner_signoff: true

  independent_evaluation:
    latest_locked_protocol_located: 0.12.0
    protocol_hash_verified: true

    targeted_v5:
      planned_runs: 8
      located_runs: 4
      located_runs_passed: 4/4
      full_protocol_completion: UNCONFIRMED     # chỉ 4/8 located

    genuine_agent_runs:
      unique_run_ids_located: 74
      raw_artifact_mentions: 110                # KHÔNG dùng làm số chính thức
      records_without_deduplicable_ID: 24
      strictly_labeled_unique_minimum: 12       # L1: execution_type=genuine_agent (deduped từ 24)
      likely_additional_unique_runs: 50         # L2: duration signature, NOT_EXPLICITLY_LABELED
      genuine_or_likely_genuine_upper_observation: 62  # L1+L2, không phải "confirmed"
      rescore_only_not_genuine: 12              # L3: duration 0.1–3.3s
      theoretical_upper_bound: 86
      exact_unique_total: UNRESOLVED
      zero_genuine_runs_claim: REJECTED

    cross_ticker_generalization:
      historical_cohort_raw_pass: 0/10
      environment_adjusted_skill_relevant_pass: 5/10
      REQ_013_later_targeted_result: PASS_AS_REPORTED   # ACB/GEX only
      REQ_025_later_targeted_result: PASS_AS_REPORTED   # ACB/GEX only
      REQ_023_full_closure: NOT_PROVEN
      original_five_ticker_requalification: NOT_PROVEN

    canonical_consolidated_scorecard:
      located: false

    hard_gates_17_of_17: UNVERIFIED
    mutation_suite_6_of_6: UNVERIFIED
    validator_specificity_1_0: UNVERIFIED
    verification_layer_ROBUST: UNVERIFIED
    evaluator_certified_production_readiness: UNCONFIRMED
```

---

## 8. Kết luận 1 câu (bảo vệ được nhất hiện nay)

> `equity-research-vn` v1.1.0 mang nhãn release `PRODUCTION_READY` do owner xác nhận, nhưng evaluator-certified production readiness vẫn chưa thể xác nhận vì chưa tìm thấy canonical consolidated scorecard. Trong 74 unique run identifiers đã định vị, 12 unique logical runs có explicit `genuine_agent` evidence, 50 runs khác có runtime signature phù hợp nhưng chưa có label xác nhận, và 12 runs được phân loại là verifier/re-score only. Targeted-v5 mới xác nhận subset 4/8 runs; full protocol completion vẫn chưa được chứng minh.

---

## Lịch sử đánh giá của Sol và lần lượt áp dụng

| Lần | Đánh giá | Đã sửa |
|---|---|---|
| Báo cáo gốc (v0.1.0) | REJECT_STALE | — |
| Đính chính 1 | ACCEPT_WITH_CORRECTIONS | staleness, owner vs independent, scope |
| Đính chính 2 | ACCEPT_WITH_CORRECTIONS | targeted-v5 subset, 110 không phải unique, latest=located, đổi tên state |
| **Bản này** | **áp dụng đủ 4 điểm** | — |
