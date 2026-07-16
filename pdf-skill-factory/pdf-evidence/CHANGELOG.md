# CHANGELOG — pdf-evidence skill

Theo format `08-VERSIONING_PLAN.md`. Mỗi entry: loại + approval + thay đổi + lý do + files + eval + limitations + next.

---

### 2026-07-06 — v0.3.0 — minor release (Train-on-Use mechanism)

**Loại**: minor (`0.2.0` → `0.3.0`) — workflow change: thêm cơ chế tự học trong quá trình làm việc.
**Approval**: APPROVED by user (NEXT COMMAND — Add Train-on-Use mechanism).
**Bump applied**: `metadata.version: "0.2.0"` → `"0.3.0"` trong SKILL.md.

**Why this version is minor (not patch)**: thay đổi workflow (3 modes mới), thêm schema mới (`learning_candidates/`), thêm policy domain (Train-on-Use), thêm tests mới. Backward-compatible (RUN mode behaves like v0.2.0 khi không có trigger fire).

**Source**: brief in `pasted-text-20260706-114827` (Train-on-Use / Continuous Skill Learning).

**Changes**:

1. **3 modes hoạt động (RUN/TRAIN/RELEASE)**:
   - **RUN** (mặc định): xử lý task + trả lời user + post-run self-evaluation + ghi `learning_candidate` khi trigger fire. **KHÔNG bao giờ tự sửa skill** (không patch SKILL.md/policies/scripts/memory/version).
   - **TRAIN** (khi user yêu cầu): chạy TRAIN_SKILL_LOOP đầy đủ (failure analysis → patch → regression → memory → before/after).
   - **RELEASE** (khi user yêu cầu): full regression → quality gates → CHANGELOG → bump version nếu được phép → rollback nếu post-bump fail.

2. **`learning_candidates/` schema + dir** (NEW):
   - `learning_candidates/schema.json` — JSON Schema 2020-12 cho `learning_candidate` (candidate_id LC-YYYY-NNN, trigger enum 12 giá trị, risk_level, suggested_action, status lifecycle, privacy rule evidence ≤300 chars).
   - `learning_candidates/README.md` — hướng dẫn + lifecycle + memory separation.
   - `learning_candidates/open/LC-2026-001.json` — ví dụ khởi tạo (multi-column academic layout → F14 novel_pattern).

3. **`learning_candidate` ≠ `skill_memory` separation**:
   - Candidate = tín hiệu thô từ RUN.
   - Memory = lesson đã xác nhận qua TRAIN (có before/after metric).
   - RUN chỉ ghi candidate; chỉ TRAIN mới ghi memory.

4. **12 learning triggers** (policies.md §11.3): new_document_type, citation_defect, table_defect, abstention_defect, numeric_defect, legal_structure_defect, forecast_horizon_defect, low_parse_confidence, ocr_required_unavailable, novel_pattern, user_reported_error, self_check_warning. Mỗi trigger có default `suggested_action`.

5. **Post-run self-evaluation** checklist (RUN chạy nội bộ sau mỗi task): 6 câu hỏi — claim thiếu evidence? citation thiếu page/table_id? phần nên abstain? bảng parse không chắc? loại tài liệu mới? pattern nên thành regression?

6. **`training_sessions/README.md`** (NEW): định nghĩa TRAIN mode artifacts, decision values, lifecycle.

7. **6 v0.3.0 tests** (pytest):
   - `test_v030_learning_candidate_schema_valid` — mọi candidate trong `open/` pass schema.
   - `test_v030_run_mode_does_not_self_patch` — RUN mode không sửa runtime.
   - `test_v030_candidate_created_for_new_doc_type` — candidate tạo khi gặp doc type ngoài enum.
   - `test_v030_candidate_created_for_citation_defect` — candidate tạo khi citation thiếu table_id.
   - `test_v030_memory_not_written_directly_from_run` — memory không bị RUN ghi trực tiếp.
   - `test_v030_release_mode_only_mode_that_bumps_version` — chỉ RELEASE mới bump.

**Before/After** (v0.2.0 → v0.3.0):

| Metric | v0.2.0 | v0.3.0 | Threshold | Status |
|--------|--------|--------|-----------|--------|
| learning_candidate_schema_valid | N/A | **1.00** | =1.00 | ✅ NEW pass |
| run_mode_no_self_patch | N/A | **true (1.00)** | =1.00 | ✅ NEW pass |
| candidate_created_for_new_doc_type | N/A | **true (1.00)** | =1.00 | ✅ NEW pass |
| candidate_created_for_failure | N/A | **true (1.00)** | =1.00 | ✅ NEW pass |
| memory_not_updated_without_train | N/A | **true (1.00)** | =1.00 | ✅ NEW pass |
| release_only_bumps_version | N/A | **true (1.00)** | =1.00 | ✅ NEW pass |
| partial_abstention_accuracy (v0.2.0) | 1.00 | maintained | ≥0.90 | ✅ stable |
| table_handling (v0.2.0) | 1.00 | maintained | ≥0.90 | ✅ stable |
| citation_accuracy (v0.1.1) | maintained | maintained | ≥0.90 | ✅ stable |
| forecast_period_disclosure (v0.1.1) | maintained | maintained | ≥0.95 | ✅ stable |
| regression_pass_rate | 1.00 | **1.00** (21/21 pytest, 13/13 DoD) | =1.00 | ✅ stable |

**Regression (re-run AFTER version bump)**:
- `scaffolding/tests/test_regression.py`: **21/21 PASS** (13 fixtures + 2 v0.1.1 meta + 6 v0.3.0)
- `scaffolding/eval_runner.py` DoD: **13/13 fixtures PASS**
- v0.1.1 + v0.2.0 behaviors unchanged — no regression.

**Files changed in v0.3.0** (vs v0.2.0):
- `pdf-evidence/SKILL.md` — version 0.3.0; new `## Train-on-Use` section + 3 modes + memory separation (137 → 152 lines, < 500 ✅)
- `pdf-evidence/references/policies.md` — new `## 11. Train-on-Use policy` (3 modes, triggers table, post-run self-eval, memory separation, privacy, no-auto-expand-policy); +2 self-check items
- `pdf-evidence/CHANGELOG.md` — this entry
- `pdf-evidence/learning_candidates/` — NEW: schema.json + README.md + open/LC-2026-001.json
- `pdf-evidence/training_sessions/README.md` — NEW (TRAIN mode artifacts/lifecycle)
- `pdf-evidence/training_sessions/2026-07-06_v0.3.0_impl/backup_v0.2.0/` — rollback backups of 10 v0.2.0 files
- `scaffolding/metrics.py` — +5 v0.3.0 metric functions (learning_candidate_schema_valid, learning_candidates_dir_valid, run_mode_no_self_patch, memory_not_updated_without_train, candidate_created_for_trigger)
- `scaffolding/tests/test_regression.py` — +6 v0.3.0 tests

**Diff size**: SKILL.md 137 → 152 lines (+15); policies.md 248 → 306 (+58); metrics.py ~370 → ~440 (+70); test_regression.py ~180 → ~250 (+70). Total ~210 lines added/modified across runtime + scaffolding.

**Backward compatibility**: ✅ ADDITIVE only.
- `learning_candidates/` is a new dir; consumers that don't read it are unaffected.
- RUN mode behaves identically to v0.2.0 when no trigger fires (just additionally writes a candidate file when one does).
- No output schema change (still v0.2.0 output contract).
- No new dependency.

**Known limitations carried into v0.3.0**:
1. OCR scan not installed (inherited; v0.5+).
2. `faithfulness`/`hallucination_rate` LLM-judge still -1.0 (inherited; v0.4+).
3. Train-on-Use là **cơ chế phát hiện** (detection) — không phải tự động sửa. Việc promote candidate → memory/regression/patch vẫn cần TRAIN session + human approval (nếu minor/major). Đây là design choice, không phải gap.
4. Trigger detection trong RUN mode hiện là **prompt-based** (skill tự đánh giá theo checklist) — chưa có code detector tự động cho mọi trigger. Code detector cho `low_parse_confidence` + `citation_defect` + `table_defect` đã có (extract.py emit parse_confidence; metrics có các hàm check); các trigger khác phụ tố self-evaluation của skill. Roadmap: wire detectors into RUN pipeline ở v0.4.

**Decision**: **RELEASED** — all gates pass (21/21 pytest, 13/13 DoD, 6 v0.3.0 KPI all = 1.00, no v0.1.1/v0.2.0 regression, backward compatible, no new dependency, SKILL.md < 500).

**Recommended next work** (not in v0.3.0):
- v0.4: wire trigger detectors vào RUN pipeline (code, không chỉ prompt); wire `groundedness_judge.md` LLM-judge.
- v0.5: PaddleOCR for scanned PDFs.
- Tích lũy learning candidates qua nhiều RUN tasks → batch TRAIN session.

---

### 2026-07-06 — v0.2.0 — minor release (partial abstention schema + ExtractTable wiring)

**Loại**: minor (`0.1.1` → `0.2.0`) — thay đổi output contract + table workflow.
**Approval**: APPROVED by user (HUMAN APPROVAL REQUEST signed `[x] APPROVE v0.2.0 implementation`).
**Bump applied**: `metadata.version: "0.1.1"` → `"0.2.0"` trong SKILL.md.

**Source**: proposal at `proposals/v0.2.0/` (6 files); implementation patches P2.01–P2.07.

**Changes**:

1. **F-ABSTAIN-001 — partial abstention schema (FIXED)**:
   - Added top-level `partial_abstentions[]` field with structured entries `{claim_or_question_part, status, reason, missing_evidence, suggested_next_document, confidence}`.
   - `abstention_flag` semantics unchanged (binary full-answer refusal).
   - Decision tree full vs partial abstain added to SKILL.md + policies.md §3.
   - Text output: `⚠ Phần không đủ bằng chứng` section when partial abstention exists.
   - Additive field → backward compatible (default `[]`).
   - `abstention_quality` 0.50 → **1.00**; `abstention_visibility` warnings-buried → **top_level**.

2. **TABLE-WIRING-001 — ExtractTable wiring (FIXED)**:
   - `extract.py` v0.2.0: global `table_id` (`pN.ti`) + `chart_id` (`pN.ci`); infers `units` + `period` from headers (ASCII-degraded tolerant regex); computes `parse_confidence` per table; `table_uncertainty_disclosure=true` when < 0.7.
   - Citation code-path enforces table/chart format when source is a visual.
   - Cells now flow into answer → `table_cell_accuracy` measurable.
   - `table_handling` 0.85 → **1.00**; `table_cell_accuracy` N/A → **1.00** (on 3 table fixtures).
   - **pdfplumber only — NO new heavy dependency** (Camelot/Surya deferred to v0.3+).

3. **F-FORECAST-001 / F-TABLE-001 (v0.1.1) — maintained, no regression**.

**Before/After** (v0.1.1 → v0.2.0, all 13 fixtures):

| Metric | v0.1.1 | v0.2.0 | Threshold | Status |
|--------|--------|--------|-----------|--------|
| partial_abstention_accuracy | N/A | **1.00** | ≥0.90 | ✅ NEW pass |
| abstention_visibility | warnings-buried (0.50) | **top_level (1.00)** | =1.0 | ✅ fixed |
| abstention_quality | 0.50 | **1.00** | ≥0.90 | ✅ fixed |
| table_handling | 0.85 | **1.00** | ≥0.90 | ✅ fixed (was below) |
| table_cell_accuracy | N/A | **1.00** (3 table fixtures) | ≥0.90 | ✅ NEW pass |
| table_header_preservation | implicit | **1.00** | ≥0.90 | ✅ NEW pass |
| table_unit_preservation | implicit | **1.00** | ≥0.95 | ✅ NEW pass |
| table_uncertainty_disclosed | N/A | **1.00** | =1.0 | ✅ NEW pass |
| citation_accuracy | 0.92 | maintained ≥0.90 | ≥0.90 | ✅ stable |
| page_accuracy | 1.00 | 1.00 | ≥0.90 | ✅ stable |
| hallucination_risk | 0.02 | maintained ≤0.05 | ≤0.05 | ✅ stable |
| critical_hallucination_count | 0 | 0 | =0 | ✅ stable |
| forecast_period_disclosure | 0.95 | maintained ≥0.95 | ≥0.90 | ✅ stable |
| regression_pass_rate | 1.00 | **1.00** (15/15 pytest, 13/13 DoD) | =1.00 | ✅ stable |

**Regression (re-run AFTER version bump)**:
- `scaffolding/tests/test_regression.py`: **15/15 PASS** (13 fixtures + 2 meta-tests)
- `scaffolding/eval_runner.py` DoD: **13/13 fixtures PASS**
- 8 new regression cases locked (group A: 06-09; group B: 10-13)
- v0.1.1 fixtures (01-05) unchanged and still pass — no backward-compat break.

**Files changed in v0.2.0** (vs v0.1.1):
- `pdf-evidence/SKILL.md` — version bump; output schema (+partial_abstentions, +table_id/chart_id fields); abstention decision-tree section; self-check items
- `pdf-evidence/references/policies.md` — §1 citation trigger (code-enforced note); §3 abstention extended (3 modes + UX + backward-compat)
- `pdf-evidence/references/parsers.md` — extract output spec v0.2.0 (global ids, units/period, parse_confidence, uncertainty)
- `pdf-evidence/scripts/extract.py` — rewritten v0.2.0 (global table_id/chart_id, units/period regex, parse_confidence, chart detection, uncertainty disclosure)
- `pdf-evidence/CHANGELOG.md` — this entry
- `scaffolding/metrics.py` — +7 new metric functions (partial_abstention_accuracy, abstention_visibility, table_header_preservation, table_unit_preservation, table_cell_accuracy, table_handling composite, table_uncertainty_disclosed)
- `scaffolding/eval_runner.py` — +DOD_V02 thresholds, v0.2.0 gate logic
- `scaffolding/tests/test_regression.py` — +DOD_V02, v0.2.0 assertions, fixture count ≥13
- `scaffolding/fixtures/build_fixtures.py` — +8 new fixture builders (06-13)
- `scaffolding/fixtures/06-13*/` — NEW: 8 fixture dirs (PDF + case.json + baseline skill_output.json)
- `scaffolding/memory/skill_memory.json` — version → 0.2.0; M-006 + M-007 status → resolved_in_v0.2.0 with measured after-values
- `pdf-evidence/proposals/v0.2.0/` — 6 proposal/design docs (approved, then implemented)
- `pdf-evidence/training_sessions/2026-07-06_v0.2.0_impl/backup_v0.1.1/` — rollback backups of all v0.1.1 runtime files

**Diff size**: SKILL.md 105 → ~125 lines (< 500 ✅); policies.md 162 → ~210; parsers.md 102 → ~135; extract.py ~85 → ~190; metrics.py ~260 → ~370; total ~400 lines added/modified.

**Backward compatibility**: ✅ ADDITIVE only.
- `partial_abstentions[]` is a new optional field (default `[]`); consumers that ignore unknown fields are unaffected.
- `abstention_flag` semantics unchanged.
- `citations[]` semantics unchanged (new optional sub-fields `table_id`, `chart_id`, `row`, `col`, `note` are additive).
- `warnings[]` retained for parser/quality signals.
- v0.1.1 fixtures' `skill_output.json` lack the new fields → treated as defaults → still pass.

**Known limitations carried into v0.2.0**:
1. OCR scan not installed (inherited; v0.5+). Scanned pages → abstain + warning.
2. `faithfulness` / `hallucination_rate` LLM-judge still returns -1.0 (`groundedness_judge.md` not wired — v0.3+).
3. Chart detection is heuristic-only (image regions without ruled grid); chart values are approximate, always flagged lower confidence. Real chart OCR (Surya) deferred to v0.3+.
4. Camelot (lattice/stream table extraction) deferred to v0.3+ — pdfplumber table extraction suffices for current fixtures but may miss complex merged/rotated tables in real-world PDFs.

**Memory closed**: M-006 (F-ABSTAIN-001) → resolved_in_v0.2.0; M-007 (TABLE-WIRING-001) → resolved_in_v0.2.0.

**Decision**: **RELEASED** — all gates pass (15/15 pytest, 13/13 DoD, all v0.2.0 KPI thresholds met, no v0.1.1 regression, backward compatible).

**Recommended next work** (not in v0.2.0):
- Wire `groundedness_judge.md` LLM-judge → enable DoD gating on `faithfulness`/`hallucination_rate`.
- v0.3: real chart OCR (Surya) + Camelot lattice/stream for complex tables.
- v0.5: PaddleOCR for scanned PDFs.

---

### 2026-07-06 — v0.1.1 — patch release (forecast-horizon disclosure + table_id citation trigger)

**Loại**: patch (`0.1.0` → `0.1.1`)
**Approval**: APPROVED by user (patch-level self-approve eligible per `08-VERSIONING_PLAN.md`); regression re-run green after bump.
**Bump applied**: `metadata.version: "0.1.0"` → `"0.1.1"` in SKILL.md.

**Source training session**: `training_sessions/2026-07-06_110300/` (input: In-Gold-We-Trust 2026 PDF, 64 pages).

**Failures addressed this release** (2 fixed, 1 deferred, 1 known-incomplete):

| ID | Status | Detail |
|----|--------|--------|
| **F-FORECAST-001** | ✅ **FIXED** | Forecast numbers now must declare type {actual\|forecast\|target\|probability_range\|scenario} + time horizon; multi-horizon answers must label inline or summarize in a horizon-type table. Metric `forecast_period_disclosure` 0.40 → **0.95**. |
| **F-TABLE-001** | 🟡 **PARTIALLY FIXED** | Citation trigger rule added: chart/table-page claims now use `[file, page, table_id/chart_id, ...]` format; `table_id` must be propagated from extract.py. `citation_accuracy` 0.80 → **0.92** (crosses 0.90 threshold). **BUT** `table_handling` only reached **0.85 — still BELOW the 0.90 threshold** because the `ExtractTable` module is not yet wired (no structured cell extraction). See TABLE-WIRING-001 below. |
| **F-ABSTAIN-001** | ⏸ **DEFERRED to human review** | Partial abstention currently surfaces only in `warnings[]`, not as a first-class JSON field. Requires output-schema extension (`partial_abstentions[]`). Touches output contract → not minimal → **needs_human_review**. Not addressed in v0.1.1. |
| **TABLE-WIRING-001** | ⏸ **KNOWN INCOMPLETE** (newly tracked) | `ExtractTable` module / `table_id` wiring is incomplete: policy + propagation rules added, but no structured table-cell extraction yet. `table_handling` 0.85 < 0.90 threshold. Tracked as outstanding work, not a v0.1.1 regression. |

**⚠️ Capability honesty**: Table capability is **NOT fully passed** in v0.1.1. Only the citation-format dimension of table handling improved (table_id now emitted). Structured cell extraction (the `table_cell_accuracy` metric) remains **N/A** — `ExtractTable` module wiring is a code change, out of scope for this text-only patch release. `table_handling` 0.85 < 0.90 DoD threshold is an **accepted known gap** for v0.1.1, explicitly carried forward to TABLE-WIRING-001.

**Before/After** (run_01 → run_02 on same PDF; re-verified post-bump):

| Metric | Before (v0.1.0) | After (v0.1.1) | Threshold | Status |
|--------|-----------------|----------------|-----------|--------|
| forecast_period_disclosure | 0.40 | **0.95** | – | ✅ F-FORECAST-001 fixed |
| citation_accuracy | 0.80 | **0.92** | ≥0.90 | ✅ now passes |
| table_handling | 0.40 | **0.85** | ≥0.90 | 🟡 improved but **below threshold** (TABLE-WIRING-001) |
| table_cell_accuracy | N/A | N/A | ≥0.90 | N/A — ExtractTable not wired |
| hallucination_risk | 0.05 | **0.02** | ≤0.05 | ✅ improved |
| critical_hallucination_count | 0 | **0** | 0 | ✅ stable |
| material_claim_evidence_coverage | 0.90 | **1.00** | ≥0.90 | ✅ improved |
| answer_correctness | 0.85 | **0.92** | – | ✅ improved (advisory) |
| abstention_accuracy | 1.00 | 1.00 | ≥0.90 | ✅ stable |
| abstention_quality | 0.50 | 0.50 | – | ⏸ unchanged (F-ABSTAIN-001 deferred) |
| page_accuracy | 1.00 | 1.00 | ≥0.90 | ✅ stable |
| numeric_accuracy | 0.95 | 0.97 | ≥0.95 | ✅ improved |
| unit_preservation_rate | 1.00 | 1.00 | ≥0.95 | ✅ stable |
| terminology_consistency | 4.5 | 4.7 | ≥4.0 | ✅ improved |
| regression_pass_rate | 1.00 | **1.00** | =1.00 | ✅ stable |

**Regression (re-run AFTER version bump)**:
- `scaffolding/tests/test_regression.py`: **7/7 PASS**
- `scaffolding/eval_runner.py` DoD: **5/5 fixtures PASS**
- 2 regression cases locked: `tests/regression/2026-07-06_F-FORECAST-001_failure_case.json`, `tests/regression/2026-07-06_F-TABLE-001_failure_case.json`

**Files changed in v0.1.1** (vs v0.1.0):
- `pdf-evidence/SKILL.md` — `metadata.version` 0.1.0 → 0.1.1; workflow step 4 (`+table_id`); self-check (+3 items)
- `pdf-evidence/references/policies.md` — §8 financial (forecast types + horizon rule); §1 citation (table-format trigger)
- `pdf-evidence/references/parsers.md` — table_id propagation rule
- `pdf-evidence/CHANGELOG.md` — this entry (replaces the prior "pending review" draft)
- `pdf-evidence/tests/regression/` — NEW: 2 cases
- `pdf-evidence/training_sessions/2026-07-06_110300/` — full session artifacts + backups
- `scaffolding/memory/skill_memory.json` — +M-004 (F-FORECAST-001), +M-005 (F-TABLE-001), +M-006 (F-ABSTAIN-001 deferred), +M-007 (TABLE-WIRING-001 known-incomplete)

**Known limitations carried into v0.1.1**:
1. `table_handling` 0.85 < 0.90 — table capability **NOT fully passed**; ExtractTable module not wired (TABLE-WIRING-001).
2. `abstention_quality` 0.50 — partial abstention not a first-class JSON field (F-ABSTAIN-001 deferred to human review).
3. OCR scan not installed (inherited from v0.1.0); scanned pages → abstain + warning.
4. `faithfulness` / `hallucination_rate` LLM-judge still returns -1.0 (groundedness_judge.md not wired — v0.2+).

**Recommended next work** (not in v0.1.1):
- TABLE-WIRING-001: wire `ExtractTable` module → raise `table_handling` above 0.90 (likely a **minor bump** → human approval required).
- F-ABSTAIN-001: decide output-schema extension (`partial_abstentions[]`) → **minor bump** → human approval required.
- Wire `groundedness_judge.md` LLM-judge → enable DoD gating on `faithfulness`/`hallucination_rate`.

---

### 2026-07-06 — v0.1.0 — baseline evidence/citation

**Loại**: major (initial release, baseline)
**Approval**: tự duyệt (initial baseline — theo `08-VERSIONING_PLAN.md` initial release không cần approval gate, đây là v0.1.0 baseline đầu tiên)

**Thay đổi**:
- Tạo skill `pdf-evidence` mới (KHÔNG ghi đè skill `pdf` cũ).
- 4 nguyên tắc tuyệt đối: evidence-first, citation bắt buộc `[file, page, section, quote]`, abstain khi insufficient, **no-outside-knowledge by default (PATCH 6)**.
- 8 policy: citation, evidence, abstention, no-outside-knowledge, table, OCR, legal, financial, multi-PDF, Vietnamese.
- Workflow 8 bước: Intake → Classify → Route → Extract Evidence → Sufficiency Check → Answer with Citation → Self-check → Format Output.
- 2 script: `classify.py` (heuristic digital/scan), `extract.py` (pdfplumber + page anchor).
- 3 reference: `policies.md`, `parsers.md`, `failure_modes.md` (20 lỗi F01–F20).
- Frontmatter `metadata.version: "0.1.0"`.

**Lý do**:
- Cần skill QA evidence-first riêng (skill `pdf` hiện có phục vụ tạo/render PDF).
- Khắc phục 20 failure mode phổ biến (F01 citation thiếu page, F02 hallucination, F04 bỏ bảng, F06 không nhận sửa đổi, F11 nhầm đơn vị, F20 trộn kiến thức ngoài).
- PATCH 6: tách bạch nội dung PDF vs. kiến thức ngoài.

**Files tạo**:
- `pdf-evidence/SKILL.md` (103 dòng, < 500 ✅)
- `pdf-evidence/CHANGELOG.md` (file này)
- `pdf-evidence/references/policies.md`
- `pdf-evidence/references/parsers.md`
- `pdf-evidence/references/failure_modes.md`
- `pdf-evidence/scripts/classify.py`
- `pdf-evidence/scripts/extract.py`
- `pdf-evidence/agents/openai.yaml`

**Eval score** (baseline mock outputs, regenerated khi chạy skill thật):
- citation_format_accuracy: 1.00 (threshold ≥ 0.95 ✅)
- citation_page_accuracy: 1.00 (threshold ≥ 0.90 ✅)
- abstention_accuracy: 1.00 (threshold ≥ 0.90 ✅)
- table_fidelity: 1.00 (threshold ≥ 0.85 ✅)
- faithfulness (LLM-judge): -1.00 (NOT WIRED v0.1 — cần `groundedness_judge.md` v0.2+)
- hallucination_rate (LLM-judge): -1.00 (NOT WIRED v0.1 — cần `groundedness_judge.md` v0.2+)
- faithfulness_simple (BASELINE heuristic PATCH 3): advisory only
- Regression: 7/7 pytest pass, 5/5 fixtures DoD pass.

**Known limitations**:
- OCR scan thật chưa cài (PDF scan → abstain + warning v0.1).
- Bảng xoay/phức tạp: pdfplumber có thể miss → warning.
- PDF pháp lý/tài chính VN phức tạp: chưa test wide → verify thủ công.
- `faithfulness_simple` là CI smoke; faithfulness thật (LLM-judge) chưa wire (PATCH 4 spec sẵn).
- Fixture tự tạo (reportlab), chưa có PDF pháp lý/tài chính thật VN — coverage metric còn over-estimate.
- Multi-column reading order: chưa handle (warning; v0.5+ Surya).

**Recommended next improvement (v0.2)**:
- Wire `groundedness_judge.md` vào LLM-judge call thật → enable faithfulness + hallucination_rate metric DoD.
- Thêm fixture `Camelot` cho bảng nâng cao (lattice/stream).
- Thêm 5 fixture thật (có phép) cho financial/legal VN.

---

## Hướng dẫn bump version sau

Theo `08-VERSIONING_PLAN.md`:
- Patch `0.1.Z` — fix bug nhỏ, reviewer tự duyệt.
- Minor `0.Y.0` — thêm policy/sub-skill → **HUMAN APPROVAL BẮT BUỘC (PATCH 8)**.
- Major `X.0.0` — breaking → **HUMAN APPROVAL + FULL RE-EVAL**.

Quy trình: chạy `eval_runner.py` → check DoD → đề xuất `APPROVAL_REQUEST.md` → đợi human ký → bump `metadata.version` trong SKILL.md → append entry này → copy sang `~/.zcode/skills/pdf-evidence/`.
