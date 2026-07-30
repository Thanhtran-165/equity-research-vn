# Báo cáo trình Sol — Dọn repo Git

**Ngày:** 2026-07-30
**Phạm vi:** Làm gọn repo `equity-research-vn` trên GitHub — bỏ project không liên quan + untrack artifacts trung gian

---

## 1. Vấn đề phát hiện

Repo `equity-research-vn` trên GitHub có **15.433 file**, gồm nhiều thư mục hoàn toàn không liên quan đến dự án (facebook-page-graph, sjc-gold-history, pdf-skill-factory...) + artifacts evaluation khổng lồ (agent-eval 5.943 file, skill-harness-evaluator-work 4.087 file). Repo công khai phình to, không chuyên nghiệp.

---

## 2. 3 đợt dọn đã thực hiện

### Đợt 1 — Xóa project không liên quan (commit `7f15e64ed`)

```yaml
phương_pháp: git rm (XÓA file vật lý + index)
số_file: 1.459
các_project_đã_xóa:
  - facebook-page-graph-dashboard (281)
  - sjc-gold-history (320)
  - pdf-skill-factory (123)
  - vn-market-research-master (114)
  - deja-vu-1970 (109)
  - vn10y-nghien-cuu (76)
  - pnj-research (75)
  - vn-rates-weekly (90)
  - brand-guard-fb (34)
  - vn-bond-transmission (54)
  - equity-divergence-study (30)
  - equity-volume-breadth (26)
  - equity-stock-volume-divergence (32)
  - equity-foreign-flow-relations (44)
  - equity-multivariate-forecast (10)
  - tradingview-pine (2 submodule)
  - + 10 file/thư mục nhỏ khác
```

### Đợt 2 — Untrack artifacts evaluation lớn (commit `ba16a2e7a`)

```yaml
phương_pháp: git rm --cached (KHÔNG xóa file vật lý, giữ local)
số_file: 12.419
các_thư_mục:
  - agent-eval (5.943) — qualify evidence equity-research-vn
  - skill-harness-evaluator-work (4.087) — audit work dir
  - skill-harness-evaluator-reaudit (1.474) — reaudit v0.1
  - skill-harness-evaluator-reaudit-v0.2.0 (915) — reaudit v0.2
local: GIỮ ĐẦY ĐỦ (truy ngược được khi cần)
```

### Đợt 3 — Untrack phase history intermediate (commit `1a4547c22`)

```yaml
phương_pháp: git rm --cached (KHÔNG xóa file vật lý, giữ local)
số_file: 1.452
các_thư_mục:
  - vn-fundamental-analysis-phase1→5R3b (11 dirs)
  - vn-valuation-engine-phase4F→6R2 (6 dirs)
  - equity-research-vn-phase6-fundamental-integration (555)
local: GIỮ ĐẦY ĐỦ
```

---

## 3. Kết quả

```yaml
trước: 15.433 file
sau:   103 file
giảm:  99.3% (15.330 file)
```

### Top-level còn lại trên repo (103 file)

```yaml
root_files:      .gitignore, README, SKILL.md, LICENSE, DISCLAIMER, RELEASE_NOTES
docs/scripts:    phases/, scripts/, docs/
6 skill con:     vn-financial-data-collector, vn-fundamental-analysis,
                 vn-news-digest, vn-research-dashboard, vn-technical-analysis,
                 vn-valuation-engine
authority:       skill-harness-evaluator-authority/ (5 file registry R1)
deployment:      vn-valuation-engine-deployment/
viz:             _viz-shared/
```

### Local vẫn còn đầy đủ

```yaml
agent-eval:                    vẫn trên đĩa (untracked)
skill-harness-evaluator-work:  vẫn trên đĩa (untracked)
phase history dirs:            vẫn trên đĩa (untracked)
.gitignore:                    chặn track lại tất cả
```

---

## 4. ⚠️ ĐIỂM CẦN SOL PHÊ DUYỆT — Final acceptance chưa merge vào main

Phát hiện khi verify: **final acceptance artifacts nằm trên branch riêng, CHƯA merge vào main.**

```yaml
trên_main_hiện_tại:
  skill-harness-evaluator-authority/:
    - authority-decision.yaml (R1)
    - authority-reconciliation-report.md (R1)
    - protocol-registry.yaml (R1)
    - run-overlap-and-rescore-map.yaml (R1)
    - run-registry.yaml (R1)
  # CHỈ có 5 file registry R1 — KHÔNG có final-acceptance/

trên_branch_riêng (skill-harness-evaluator-final-acceptance-remediation-R1):
  skill-harness-evaluator-authority/final-acceptance/:
    - canonical-evidence-index.yaml
    - consolidated-run-inventory.yaml
    - equity-research-vn-scorecard.yaml
    - skill-harness-evaluator-scorecard.yaml
    - final-acceptance-decision.yaml
    - final-acceptance-report.md
    - release-manifest.json
  # + completion-protocol-v0.13.0* (4 file)
  # + completion-execution-v0.13.0/ (directory)
  # + completion-recovery-protocol-v0.14.0* (4 file)
  # + completion-recovery-execution-v0.14.0/ (directory)
  # + protocol-authority-* (3 file)
```

**Tất cả authority work (freeze, execution, recovery, final acceptance) nằm trên chain branch riêng, chưa merge vào main.** Main chỉ có đến registry R1.

---

## 5. Đề xuất

```yaml
option_A (khuyến nghị):
  merge branch final-acceptance-remediation-R1 vào main
  → main sẽ có đầy đủ final authority artifacts (final-acceptance/ + completion + recovery)
  → repo vẫn gọn (chỉ +30 file artifacts, không phải artifacts trung gian)
  → main trở thành source of truth cuối

option_B:
  giữ branch riêng, không merge
  → main chỉ có registry R1
  → final acceptance tham chiếu qua branch
  → phù hợp nếu muốn tách "code repo" khỏi "authority repo"
```

---

## 6. Integrity checks

```yaml
local_files_preserved: true (git rm --cached không xóa vật lý)
unrelated_projects_removed: true (git rm xóa vật lý)
gitignore_updated: true (chặn track lại)
skill_harness_evaluator_code: không động vào (~/.zcode/skills/, không trong repo)
final_authority_branches: vẫn trên remote (8 branch)
```

---

## Tóm tắt cho Sol

```yaml
hoạt_động: làm gọn repo từ 15.433 → 103 file
phương_pháp: 3 commit (1 xóa + 2 untrack-giữ-local)
local: đầy đủ, không mất gì
repo: sạch, chỉ còn project-related
cần_phê_duyệt: final acceptance merge strategy (option A hay B)
```
