# Từ tuyên bố đến bằng chứng: Cách Skill Harness Evaluator thay đổi quy trình nghiệm thu AI Skill

**Trích dẫn canonical:** Tag `skill-harness-evaluator-v0.1.0-final-r2` (`252798ea6b1ee845eda63d1202db49289cf44978`)
**Ngày:** 2026-07-31
**Đối tượng:** `equity-research-vn` + `skill-harness-evaluator`

> Tag canonical `skill-harness-evaluator-v0.1.0-final-r2` có 12/12 accepted claims được hash-pin và resolve đầy đủ. Một số claim lịch sử không được chấp nhận vẫn giữ sentinel provenance vì chúng được phân loại `NOT_VERIFIED`; các claim này không tham gia final verdict và là cơ sở của maturity cap.

---

## Tóm tắt

> Trước harness, một dự án có thể hoàn thành về mặt kỹ thuật nhưng kết luận cuối vẫn phụ thuộc nhiều vào cách owner kể lại quá trình. Sau harness, mỗi kết luận quan trọng được gắn với protocol, run identity, authority chain, evidence hash và maturity gate. Kết quả không nhất thiết cao hơn, nhưng rõ ràng hơn: điều gì đã được chứng minh, điều gì chưa được chứng minh, giới hạn nằm ở đâu và một bên độc lập có thể kiểm tra lại bằng cách nào.

Harness không tự động làm skill tốt hơn. Nó tạo ra cơ chế để phát hiện lỗi, kiểm soát quy trình và biến các kết luận về skill thành những kết luận có bằng chứng, có giới hạn và có thể kiểm tra lại. Trong dự án này, harness thực tế đã góp phần làm chất lượng quy trình tốt hơn thông qua việc phát hiện retry-policy violation, bác bỏ kết luận PASS thiếu căn cứ, buộc phân biệt logical run, physical event và launcher attempt, tạo recovery protocol sạch, và áp maturity cap thay vì chấp nhận claim chưa xác minh.

---

## 1. Claim verification

### Trước harness

```yaml
phương_pháp: 'Owner khai báo PASS + agent tự báo kết quả'
evidence: 'Screenshot, log text, lời nói'
khả_năng_kiểm_chứng_độc_lập: KHÔNG
  - người review phải TIN owner
  - không có hash để đối chiếu
  - chạy lại có thể ra kết quả khác (uuid, timestamp)
```

Không có cách nào trả lời câu hỏi "Làm sao tôi biết skill thực sự PASS?"

### Sau harness

```yaml
phương_pháp: 'Hash-pin evidence + protocol freeze + authority chain'
evidence:
  - mỗi run có output_sha256 + run_result_sha256
  - mỗi protocol có protocol_sha256 + frozen_before_execution
  - mỗi artifact có source_sha256 (64 hex) resolve trên main hoặc archive
khả_năng_kiểm_chứng_độc_lập: CÓ
  - clone repo → đọc scorecard → đối chiếu hash
  - tải evidence archive → verify SHA-256
  - chạy lại verifier (đã hash-pin) → so sánh kết quả
```

Người kiểm tra không còn phải chỉ tin lời tuyên bố của owner. Họ có thể đối chiếu Git history, artifact hashes, protocol locks, archive manifests và scorecard digests từ một release tag cố định. Việc kiểm chứng vẫn phụ thuộc vào tính đúng của công cụ tạo hash, tính đầy đủ của archive, cách canonicalize dữ liệu, tính đúng của evaluator và verifier, và integrity của Git hosting. SHA-256 xác nhận bytes không đổi, không tự chứng minh nội dung đúng.

---

## 2. Protocol governance

### Trước harness

```yaml
scope_test: KHÔNG_RÕ
  - không biết test bao nhiêu ticker
  - không biết REQ nào kiểm tra
  - không biết role mỗi run
  - có thể đổi role sau khi thấy kết quả
thay_đổi_sau_khi_chạy: KHÔNG_QUẢN_TRỊ
```

### Sau harness

```yaml
scope_test: RÕ_RÀNG_VÀ_KHÓA
  - planned_runs: chính xác bao nhiêu run, ticker nào
  - requirement_matrix: 28 REQ/run, REQ-023 phải test trực tiếp
  - run_roles: frozen trước execution
  - applicability_matrix: APPLICABLE/NOT_APPLICABLE cho mỗi REQ × ticker
thay_đổi_sau_khi_chạy: BỊ_CẤM (protocol_sha256 khóa nội dung)
```

**Ví dụ — SAB role:** SAB được freeze là `CLEAN_POSITIVE_CONTROL`, `stress_case=false`, `REQ-023 APPLICABLE expect PASS`, `defect_injection=prohibited`. Không được đổi sau khi xem kết quả.

---

## 3. Attempt and retry accounting

### Trước harness

Trước khi có canonical protocol, retry chưa được quản trị nhất quán và chưa được hạch toán thành launcher attempt, physical event và logical run riêng biệt. Nếu run fail, có thể chạy lại cho đến khi PASS mà không ai biết đã thử bao nhiêu lần. Kết quả thuận lợi có thể được chọn lọc (cherry-picking), evidence của lần fail có thể bị xóa.

### Sau harness

Trong protocol completion và recovery của case study này, số launcher attempt được khóa trước. Retry ngoài protocol bị coi là vi phạm hoặc tạo ra evidence không có authority. Policy cụ thể: `maximum_launcher_attempts: 1`, `replacement_execution: prohibited`.

Nếu abort/interrupt → trạng thái `INCOMPLETE`, không chạy lại trong cùng protocol.

Mỗi launcher attempt có identity riêng. Phân loại: `PRE_EXECUTION_LAUNCHER_ABORT` / `INTERRUPTED_AGENT_EXECUTION` / `UNRESOLVED`. Evidence thất bại được bảo toàn, không xóa. Uncertainty không được giải quyết theo hướng PASS.

**Ví dụ thực tế:** TV13-CTD-01 chạy 3 lần. Hai lần đầu phân loại `UNRESOLVED` (không đủ evidence chứng minh pre-execution abort). Không hợp thức hóa ngược. Tạo recovery protocol v0.14 sạch, chạy đúng 1 lần TV14-CTD-01. Launcher safety contract sinh ra từ incident: NO pipe, NO dir reuse, capture PID/exit/signal.

---

## 4. Authority and supersession

### Trước harness

```yaml
authority: KHÔNG_RÕ
  - không biết version nào canonical
  - không có supersession chain
  - kết quả cũ và mới trộn lẫn (backward pooling)
```

### Sau harness

```yaml
authority: RÕ_RÀNG
  - mỗi protocol có source_file_sha256 + embedded_hash_verified
  - supersession chain: baseline_protocol_sha256 → predecessor
  - chain intact/broken được phân loại trung thực
  - kết quả KHÔNG trộn giữa protocol (no backward pooling)
```

**Ví dụ:** Chain v0.10→v0.12 phát hiện BROKEN (3 baselines match nothing located). v0.12 classified `UNRESOLVED`, không ép canonical. Tạo fresh authority (v0.13, v0.14) anchored vào accepted decisions.

---

## 5. Release versus maturity

### Trước harness

`PRODUCTION_READY` do owner quyết định, không có đánh giá độc lập về mức độ evidence.

### Sau harness

Harness không thay thế quyền quyết định phát hành của owner. Harness bổ sung một đánh giá độc lập về mức độ evidence và maturity.

```yaml
ba_trạng_thái_KHÔNG_đồng_nghĩa:
  owner_release_label:
    PRODUCTION_READY        # owner quyết định phát hành

  evaluator_maturity:
    FUNCTIONAL_WITH_GENERALIZATION_EVIDENCE  # evaluator đánh giá evidence

  evaluator_verdict:
    PASS_WITH_MATURITY_CAP  # có correctness, nhưng thiếu evidence maturity
```

Trong case này, evaluator chấp nhận functional correctness và generalization evidence, nhưng áp maturity cap vì năm nhóm metric chưa được xác minh dưới canonical authority: hard_gates, mutation, sensitivity, specificity, verification_layer_ROBUST.

---

## 6. Evidence preservation

### Trước harness

```yaml
preservation: KHÔNG_BỀN_VỮNG
  - artifact chỉ tồn tại trên 1 máy
  - máy hỏng = mất evidence
  - không có hash để verify integrity
```

### Sau harness

```yaml
preservation: BỀN_VỮNG
  - compact authority artifacts trên main repo (clean clone được)
  - raw evidence trong immutable GitHub release asset (hash-pinned)
  - mỗi artifact có SHA-256 để verify integrity

archive:
  name: skill-harness-evaluator-final-evidence.tar.zst
  sha256: 181bd7eb14a6e97ee978fb3c4ca7eb96ade6626c874cca0cc60313b073ce86d0
  members: 2.565 files
  storage: GitHub release asset (immutable)
```

---

## 7. Deterministic scorecard production

### Trước harness

Scorecard (nếu có) được viết tay, không deterministic. Chạy lại có thể ra kết quả khác.

### Sau harness

Scorecard được build deterministic từ evidence index. Hai lần build cho cùng digest (loại trừ timestamp). Không dùng model call để tính score.

```yaml
reproducibility:
  equity_research_vn: digests_match: true
  skill_harness_evaluator: digests_match: true
  nondeterministic_fields_excluded: [generated_at]
```

---

## 8. Bảng so sánh tổng hợp

| Khía cạnh | Trước harness | Sau harness |
|---|---|---|
| **Claim verification** | Tin owner, không verify được | Hash-pin, clone → verify, đối chiếu Git history + artifact hashes |
| **Protocol governance** | Không rõ, đổi sau khi chạy | Freeze trước, đổi = vi phạm |
| **Attempt and retry accounting** | Không quản trị, silent retry | Launcher attempt hạch toán, retry ngoài protocol = vi phạm |
| **Authority and supersession** | Version mới nhất = chính thức | Registry + supersession chain + lineage |
| **Release versus maturity** | Owner nói = chính thức | Owner release tách riêng evaluator maturity + cap |
| **Evidence preservation** | Local, máy hỏng = mất | Main + immutable archive + hash-pin |
| **Deterministic scorecard** | Viết tay, không deterministic | Build từ evidence index, digest match |

---

## 9. Kết quả định lượng từ case study

```yaml
canonical_case_results:
  registry_baseline:
    physical_events: 110
    logical_runs: 98

  final_inventory:
    physical_events: 115
    logical_runs: 103
    L1_explicit_genuine: 21
    L2_likely_genuine: 50
    L4_unknown: 32

  authoritative_completion:
    runs: 8/8_PASS
    requirements: 224/224

  critical_requirements:
    REQ_013: 8/8_PASS
    REQ_023: 8/8_DIRECT_PASS
    REQ_025: 8/8_PASS

  repository_publication:
    canonical_tag: skill-harness-evaluator-v0.1.0-final-r2
    commit: 252798ea6b1ee845eda63d1202db49289cf44978
    accepted_claims_with_valid_provenance: 12/12

historical_limitations:
  non_authoritative_completed_CTD_run: 1
  unresolved_launcher_incidents: 2
  canonical_metrics_NOT_VERIFIED: 5
```

---

## 10. Harness cũng có thể sai

Harness không phải một oracle bất khả sai. Giá trị của nó nằm ở chỗ sai sót được biểu diễn thành incident, evidence không bị xóa, uncertainty không được tự động giải quyết theo hướng PASS, và recovery chỉ được thực hiện sau khi authority mới đã được freeze.

Trong case study này, harness process từng đưa ra kết luận chưa đủ chặt:

- R1 phân loại CTD attempts là `PRE_EXECUTION_LAUNCHER_ABORT` dựa vào `phase=init`, nhưng sau phát hiện runner không update task-state phase → phân loại chuyển thành `UNRESOLVED`
- Báo cáo v0.1.0 ban đầu ghi `FAIL` dựa trên audit cũ, nhưng thực tế project đã tiến xa hơn nhiều
- Accountting model ban đầu trộn L3 (physical rescore) vào logical runs denominator

Mỗi lần sai được phát hiện, ghi nhận trung thực, và khắc phục qua remediation cycle. Đây là bài học mạnh nhất của toàn bộ dự án: **khả năng tự sửa lỗi có cấu trúc quan trọng hơn việc không bao giờ sai.**

---

## 11. Kết luận

Trước harness, một dự án có thể hoàn thành về mặt kỹ thuật nhưng kết luận cuối vẫn phụ thuộc nhiều vào cách owner kể lại quá trình. Sau harness, mỗi kết luận quan trọng được gắn với protocol, run identity, authority chain, evidence hash và maturity gate. Kết quả không nhất thiết cao hơn, nhưng rõ ràng hơn: điều gì đã được chứng minh, điều gì chưa được chứng minh, giới hạn nằm ở đâu và một bên độc lập có thể kiểm tra lại bằng cách nào.
