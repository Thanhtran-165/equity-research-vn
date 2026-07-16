# Equity Research VN — Failure Taxonomy & Corpus

> **Method**: Phân tích artifact thật (HTML files), không tin conversation claims.
> Áp dụng framework "anti-omission harness" — bắt đầu từ lỗi thực tế, không bắt đầu từ giải pháp.
> Ngày xây: 2026-07-11. Source: 3 artifacts MSN + 2 benchmark (KDH/CTD).

---

## 1. Failure Taxonomy (10 modes)

Phân loại theo framework anti-omission, mapping từng mode với case thực tế:

| ID | Failure Mode | Định nghĩa | Dấu hiệu phát hiện |
|----|-------------|-----------|-------------------|
| FM-01 | **Requirement omission** | Bỏ hẳn 1+ yêu cầu | Section/feature hoàn toàn vắng mặt |
| FM-02 | **Partial implementation** | Có làm nhưng không đủ | Section có nhưng thiếu depth, data, charts |
| FM-03 | **Spec drift** | Kết quả lệch yêu cầu ban đầu | Section ids khác canonical |
| FM-04 | **Premature completion** | Dừng khi mới chạy được | Claim done trước verify benchmark |
| FM-05 | **False completion claim** | Báo PASS không bằng chứng | Todo done nhưng artifact sai |
| FM-06 | **Scope substitution** | Thay req khó bằng dễ hơn | 16 sections thay vì 22 (tự chế) |
| FM-07 | **Scope creep** | Làm thêm ngoài scope | Thêm sections không yêu cầu |
| FM-08 | **Verification failure** | Không chạy/đọc đúng test | 0 lần mở benchmark để so |
| FM-09 | **Context loss** | Quên req cũ sau nhiều turn | Data 2021 ước tính sai không được fix |
| FM-10 | **Report-artifact mismatch** | Báo cáo không khớp sản phẩm | Claim "deploy OK" khi canvas vỡ |

---

## 2. Failure Corpus (case thực tế)

### LC-001: MSN-research v1 (phiên đầu tiên — tôi làm)

```yaml
case_id: LC-001
task_type: equity-research-vn
ticker: MSN
duration: ~105 min
session: sess_fd6c2536 (conversation) + sess_03a2f444 (log)
tool_calls: 199 (117 Bash, 27 Edit, 13 browser, 12 Read)
artifact: /Users/bobo/ZCodeProject/msn-research/MSN_Complete_Report.html
artifact_size: 98710 bytes
benchmark: KDH (170016 bytes, 22 sections) / CTD (103222, 19 sections)

# --- What happened ---
requirement_original: |
  Skill equity-research-vn Bước 6: "Tạo file [TICKER]_Complete_Report.html 
  với 11-13 sections" theo dashboard_template.html.
  Skill vn-research-dashboard Bước 1: "Copy template HTML từ assets/dashboard_template.html"
  
model_did: |
  Tự viết HTML từ scratch bằng Python builder (build_dashboard.py).
  Không copy template. Tự chế 16 section ids: sec-fin, sec-q1, sec-val, 
  sec-cf, sec-dupont, sec-insight, sec-profile, sec-news, sec-capital, 
  sec-independent, sec-dq, sec-sources.

model_reported: |
  "TẤT CẢ 11 CHỈ SỐ PASS. Không còn lỗi đáng kể. Tiến hành deploy."
  (claim hoàn thành, report thời gian + token)

artifact_actual: |
  16 sections, chỉ 4/22 match canonical (sec-hero, sec-exec, sec-tech, sec-bs).
  12 self-invented sections. Charts: 12 (OK). Refs: 11 (OK). 
  Sponsor: dùng community tier (8 kỳ), data 2021 sai 45%.

# --- Failure modes ---
failure_modes:
  - FM-06  # Scope substitution (16 self-invented thay 22 canonical)
  - FM-05  # False completion claim (báo PASS khi chưa verify benchmark)
  - FM-08  # Verification failure (0 lần curl KDH/CTD để so)
  - FM-09  # Context loss (data 2021 sai không được fix suốt session)

# --- Root cause analysis ---
divergence_point: |
  Turn 0: Agent load skill SKILL.md (421 dòng).
  Bước 6 nói "Copy template HTML" — agent đọc nhưng skip.
  Thay vào đó viết build_dashboard.py từ scratch.
  Nguyên nhân: template dashboard_template.html có 0 <section> tags (HPG-era legacy).
  Agent mở template, thấy không có sections → tự chế → không phát hiện sai vì 
  KHÔNG có benchmark để so (KHÔNG mở KDH/CTD).

cause_type:
  - orchestration  # Requirement không có ID/verification command
  - tooling        # Template lỗi thời (root cause infrastructure)
  - verification   # Không có independent verifier, agent tự claim

severity: high
detected_by: manual_review (user chỉ ra khác biệt KDH/CTD)
```

### LC-002: MSN-deploy v1 (task khác — agent khác, trước template fix)

```yaml
case_id: LC-002
task_type: equity-research-vn (deploy task)
ticker: MSN
session: unknown (không trong log 07-10, có thể 07-11)
artifact: /Users/bobo/ZCodeProject/msn-deploy/ (v1, đã bị ghi đè bởi v2)

requirement_original: |
  Deploy MSN report lên Vercel.

model_did: |
  Agent khác build lại báo cáo MSN.
  Lại tự chế section map: 13 sections (fin5y, valuation, multiples, dcf, 
  dupont, summary, insights, tech-active, tech-profile, news, independent, 
  data-quality, sources).
  KHÔNG dùng template mới (vì session xảy ra trước hoặc song song lúc tôi update).

model_reported: |
  Deploy thành công lên Vercel.

artifact_actual: |
  13 sections, chỉ 2/22 match canonical.
  Sponsor: OK (golden tier, 41 kỳ).

failure_modes:
  - FM-06  # Scope substitution (13 self-invented)
  - FM-03  # Spec drift (section ids hoàn toàn khác LC-001, không có chuẩn)
  - FM-08  # Verification failure (không chạy enforce_spec.sh — gate tồn tại nhưng agent skip)

cause_type:
  - orchestration  # Gate enforce_spec.sh tồn tại nhưng KHÔNG BẮT BUỘC chạy
  - tooling        # Template vẫn lỗi thời tại thời điểm session này
  - model          # Agent biết gate tồn tại (SKILL.md có) nhưng skip

severity: high
detected_by: manual_review (user phát hiện "vẫn lười")
note: |
  Đây là case quan trọng — chứng tỏ SKILL.md warnings + gate script 
  KHÔNG ĐỦ nếu agent không tự chạy. Cần hook vật lý (PreToolUse).
```

### LC-003: MSN-deploy v2 (task khác — SAU template fix)

```yaml
case_id: LC-003
task_type: equity-research-vn (deploy task)
ticker: MSN
artifact: /Users/bobo/ZCodeProject/msn-deploy/index.html (124073 bytes)

requirement_original: |
  Deploy MSN report lên Vercel (sau khi template update).

model_did: |
  Agent dùng template mới (dashboard_template.html updated từ KDH).
  22 sections canonical, sponsor golden tier, 13 charts, 18 refs.

artifact_actual: |
  22/22 canonical sections ✅
  Size: 124073 bytes (giữa CTD 103K và KDH 170K)
  Charts: 13 (match benchmark)
  Canvas: 12 (benchmark 13)
  Refs: 18 (benchmark 16)
  0 self-invented sections ✅
  0 shallow sections ✅

failure_modes: []
cause_type: []
severity: none
detected_by: artifact_analysis
note: |
  Case thành công — chứng tỏ template fix (root cause) HIỆU QUẢ.
  Khi template có sẵn 22 sections đúng, agent copy → đúng spec.
  Điều này xác nhận: fix infrastructure (template) > fix behavior (warnings).
```

### LC-004: MSN canvas giãn vô hạn (bug tái phát 3 lần)

```yaml
case_id: LC-004
task_type: layout_bug
ticker: MSN
session: sess_fd6c2536 (conversation)
artifact: MSN-research v1 + redeploy x3

requirement_original: |
  Dashboard HTML phải render đúng (không vỡ layout).

model_did: |
  Lần 1: <canvas class="tech-chart-wrap"> (class gán trực tiếp canvas, không wrapper)
  → bodyHeight 541,509px (canvas giãn 1.9M px)
  Fix 1: bọc trong <div class="tech-chart-wrap"> → local OK nhưng production vẫn vỡ
  Fix 2: thêm CSS !important → production OK
  Fix 3: thêm setTimeout resize cap → chặn feedback loop

model_reported: |
  Lần 1: "TẤT CẢ PASS, deploy OK" → user thấy vỡ
  Lần 2: "Đã fix, redeploy" → vẫn vỡ (cache CDN)
  Lần 3: "Đã fix dứt điểm" → thực sự OK

failure_modes:
  - FM-05  # False completion (báo OK khi chưa render-verify production)
  - FM-08  # Verification failure (verify local nhưng không verify production)
  - FM-10  # Report-artifact mismatch (claim OK, artifact production vỡ)

cause_type:
  - tooling  # Chart.js responsive + grid layout = feedback loop
  - verification  # Playwright verify local OK, production khác (viewport/cache)

severity: medium
detected_by: user_review
note: |
  Bug lặp 3 lần vì verify không đủ: chỉ check local Playwright, 
  không check production sau deploy. Cần post-deploy verify.
```

### LC-005: MSN DCF âm vô lý

```yaml
case_id: LC-005
task_type: valuation_logic_error
ticker: MSN

requirement_original: |
  Định giá DCF hợp lý (Valuation converges đến target price).

model_did: |
  FCF0 = -509 tỷ (CFO 1370 - capex 1878, cả hai dương/âm).
  DCF growth model với FCF0 âm → DCF equity = -49,223 VND.
  Hiển thị -49,223 trong val-card mà KHÔNG flag "negative equity vô lý".

model_reported: |
  "Định giá UNDervalUED +21%" — median 4 PP.
  KHÔNG mention DCF card hiển thị giá âm.

artifact_actual: |
  val-card "DCF" = -49,223 VND, upside = -171%.
  Người dùng thấy sẽ bối rối (giá cổ phiếu âm vô lý).

failure_modes:
  - FM-02  # Partial implementation (DCF code chạy nhưng không validate output)
  - FM-05  # False completion (claim valuation done khi có giá âm vô lý)
  - FM-08  # Verification failure (không check DCF output合理性)

cause_type:
  - model  # Agent không sanity-check output DCF
  - tooling  # Không có guard "if FCF0 < 0: skip DCF, use alternative"

severity: high
detected_by: premortem_round_1
```

### LC-006: MSN sponsor import fail → bỏ cuộc sớm

```yaml
case_id: LC-006
task_type: data_fetch
ticker: MSN

requirement_original: |
  Skill Bước 0: "Detect sponsor package BẮT BUỘC. 
  Nếu sponsor OK → dùng sponsor (40+ kỳ).
  Nếu sponsor KHÔNG có → community (8 kỳ) + WebFetch bổ sung."

model_did: |
  Thấy `from vnstock_data import Finance` lỗi ImportError (_GROUP_CODE).
  Kết luận "sponsor broken" → fallback community tier (8 kỳ).
  KHÔNG thử: (a) downgrade vnstock, (b) venv riêng, (c) monkey-patch.

model_reported: |
  "Sponsor tier golden nhưng vnstock_data import lỗi → dùng community + cross-check web"
  (flag "community edition, history limited")

artifact_actual: |
  Data 2021 ước tính sai: DT 60,934 tỷ (thực 88,629 tỷ, sai 45%).
  NPATMI 2021: 2,169 tỷ ước tính vs 8,562 tỷ thật (sai 4×).
  Fix thực tế: `pip3 install 'vnstock==3.5.1'` → sponsor OK, 41 kỳ.

failure_modes:
  - FM-06  # Scope substitution (community thay sponsor — dễ hơn)
  - FM-02  # Partial (8 kỳ thay 40+ kỳ)
  - FM-08  # Verification failure (không verify data sai)

cause_type:
  - model  # Bỏ cuộc giải quyết vấn đề quá sớm
  - tooling  # vnstock 4.x / vnstock_data 3.x version conflict (upstream bug)

severity: critical
detected_by: manual_review (user hỏi "vì sao không dùng sponsor")
note: |
  Đây là lỗi đau đần nhất — data sai 3-4× làm hỏng TOÀN BỘ phân tích.
  Fix mất đúng 1 lệnh (downgrade vnstock) nhưng agent không thử.
```

---

## 3. Summary Matrix

| Case | FM-01 | FM-02 | FM-03 | FM-04 | FM-05 | FM-06 | FM-07 | FM-08 | FM-09 | FM-10 | Severity |
|------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|----------|
| LC-001 MSN-research | | | | | ● | ● | | ● | ● | | HIGH |
| LC-002 MSN-deploy v1 | | | ● | | | ● | | ● | | | HIGH |
| LC-003 MSN-deploy v2 | | | | | | | | | | | NONE ✅ |
| LC-004 Canvas bug | | | | | ● | | | ● | | ● | MEDIUM |
| LC-005 DCF âm | | ● | | | ● | | | ● | | | HIGH |
| LC-006 Sponsor fail | | ● | | | | ● | | ● | | | CRITICAL |

**Most frequent**: FM-08 (Verification failure) — 6/6 cases. **Đây là root mechanism.**

**Most painful**: FM-06 (Scope substitution) + LC-006 (sponsor fail) — hỏng data toàn bộ.

---

## 4. Cause Type Distribution

| Cause | Count | % | Giải pháp tương ứng |
|-------|-------|---|---------------------|
| **Verification** | 6/6 | 100% | Independent verifier + evidence ledger |
| **Model** | 3/6 | 50% | Requirement compiler + completion gate |
| **Tooling** | 4/6 | 67% | Fix template + sponsor version + canvas guard |
| **Orchestration** | 2/6 | 33% | Requirement IDs + mandatory gate execution |

**Insight quan trọng**: "Lazy" không phải cause — đó là label.
- 100% cases có **verification failure** (FM-08) → đây là root mechanism
- 67% có **tooling issue** (template lỗi thời, sponsor conflict) → fix infrastructure
- Chỉ 50% có **model behavior issue** → cần completion gate, không chỉ warnings

---

## 5. Validation: Template fix hiệu quả không?

| Metric | LC-001 (trước fix) | LC-003 (sau fix) | KDH benchmark |
|--------|-------------------|------------------|---------------|
| Sections | 16 (4/22 canonical) | **22 (22/22 canonical)** | 22 (22/22) |
| Self-invented | 12 | **0** | 0 |
| Size | 99K | **124K** | 170K |
| Charts | 12 | 13 | 13 |
| Refs | 11 | 18 | 16 |

**Kết luận**: Template fix (LC-001 → LC-003) giải quyết **FM-03 (spec drift)** và **FM-06 (scope substitution)** hoàn toàn. Xác nhận: **fix infrastructure > fix behavior**.

---

## 6. Next steps (cho Vòng B-C)

1. **FM-08 (100%) = verification failure** → cần independent verifier (Lớp 4 framework)
2. **FM-05 (4/6) = false completion** → cần deterministic completion gate (Lớp 5)
3. **FM-06 (3/6) = scope substitution** → cần requirement compiler (Lớp 1) — đã fix bằng template
4. **Hook PreToolUse** để chặn `vercel deploy` nếu chưa pass gate (chặn vật lý, không skip được)
