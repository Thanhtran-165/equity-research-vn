# RUNBOOK — Agent vận hành PDF Skill Factory

> PATCH 5. Quy trình từng bước để agent vận hành loop tự cải thiện skill `pdf-evidence`.
> Agent đọc file này trước khi chạy bất kỳ vòng nào.

## Vòng đời tổng thể

```
Task → Run Skill → Evaluate → Critique → Update Skill → Regression Test → Version Release
        (pdf-evidence)   (eval_runner)  (map rule)   (sửa SKILL/references)  (pytest)   (DoD gate + human approval)
```

## Phase 0 — Chuẩn bị

```bash
cd /Users/bobo/ZCodeProject/pdf-skill-factory
cat ASSUMPTIONS.md           # xác nhận phạm vi, KHÔNG fine-tune
cat DEFINITION_OF_DONE.md    # xác nhận threshold version hiện tại
git status                   # xác nhận sạch, đang ở branch feat/pdf-skill-factory
```

Nếu chưa có fixture demo:
```bash
python scaffolding/fixtures/build_fixtures.py
ls scaffolding/fixtures/*/case.json   # phải thấy 5 case
```

## Phase 1 — Nhận task

Task có thể là:

- **(a) Fixture/bug mới** từ human (PDF + câu hỏi + ground-truth): tạo fixture mới ở `scaffolding/fixtures/NN_<name>/`.
- **(b) Lỗi phát hiện từ eval** hiện tại: vào Phase 3.
- **(c) Yêu cầu bump version**: vào Phase 8.

## Phase 2 — Chạy eval

```bash
python scaffolding/eval_runner.py
# hoặc
pytest scaffolding/tests/test_regression.py -v
```

Agent đọc báo cáo `scaffolding/results/latest_report.json` và stdout.

## Phase 3 — Phân tích failure

Cho mỗi test fail, agent điền vào format (theo `06-FAILURE_MODES.md`):

```text
Failure ID: F-NN
Input: <fixture id + câu hỏi>
Expected behavior: <ground-truth>
Actual behavior: <output skill>
Root cause: <classifier sai? extraction thiếu? citation format? hallucination? abstention không kích hoạt?>
Skill rule violated: <policy name trong references/policies.md>
Suggested fix: <patch cụ thể tới SKILL.md/references>
Should become regression test? yes
```

## Phase 4 — Đề xuất instruction patch

Trước khi sửa, agent phải:

1. Trích **rule bị vi phạm** từ `pdf-evidence/references/policies.md` (số mục + tên policy).
2. Viết **patch diff** (old text → new text) vào `scaffolding/results/patch_proposal.md`:
   ```text
   Version: 0.1.0 → 0.1.1 (patch)
   Problem: F-NN ...
   Old instruction: "..."
   New instruction: "..."
   Reason: ...
   Expected metric improvement: citation_page_accuracy 0.88 → 0.92
   Risk: có thể làm parser chậm hơn / tăng false-positive
   Test needed: fixture mới kiểm chế độ này
   ```
3. Không viết patch dài vô tổ chức — mỗi patch sửa 1 rule.

## Phase 5 — Áp dụng patch

Sửa file:

- `pdf-evidence/SKILL.md` nếu rule nằm trong body (giữ < 500 dòng).
- `pdf-evidence/references/policies.md` nếu rule detail nằm ở đây.
- `pdf-evidence/references/failure_modes.md` nếu thêm lỗi mới.
- Nếu cần sub-skill mới → thêm `scaffolding/modules/<Name>.md`.

Sau khi sửa:
```bash
wc -l pdf-evidence/SKILL.md   # phải ≤ 500
```

## Phase 6 — Re-run regression

```bash
pytest scaffolding/tests/test_regression.py -v
```

- Nếu xanh: sang Phase 7.
- Nếu vẫn fail: về Phase 3 (phân tích lại), không lặp cùng patch quá 2 lần — nếu vẫn fail, dừng và báo human.

## Phase 7 — Kiểm DoD

Đọc `DEFINITION_OF_DONE.md`. Đối chiếu `scaffolding/results/latest_report.json` với bảng threshold.

- Nếu **mọi** metric ≥ threshold v0.1 + regression 100% xanh: sang Phase 8.
- Nếu không: về Phase 3.

## Phase 8 — Đề xuất version bump (PATCH 8 — human approval gate)

Loại bump:

| Thay đổi | Loại | Approval |
|----------|------|----------|
| Sửa typo, sửa 1 rule nhỏ, fix regression | patch `x.y.Z` | reviewer tự duyệt |
| Thêm policy/sub-skill mới, sửa workflow | minor `x.Y.0` | **HUMAN APPROVAL BẮT BUỘC** |
| Định nghĩa lại skill, breaking change | major `X.0.0` | **HUMAN APPROVAL + FULL RE-EVAL** |

Quy trình yêu cầu approval (minor/major):

1. Agent sinh `scaffolding/results/APPROVAL_REQUEST.md`:
   ```markdown
   # Approval Request — pdf-evidence 0.1.0 → 0.2.0

   - Reason: thêm table extraction rules
   - Changes: ...
   - Eval before: {...}
   - Eval after:  {...}
   - Regression: 100% xanh
   - Risk: ...
   - Human cần duyệt: <tên>

   ## Approval
   - [ ] APPROVED: ____________ (name) — date: ______
   - [ ] REJECTED: lý do ____________________________
   ```
2. DỪNG. Đợi human điền `APPROVED: <name> <date>`.
3. Không có chữ ký → KHÔNG bump.

Patch bump có thể skip approval nếu reviewer tự ký.

## Phase 9 — Bump version

Sau khi có approval (nếu cần):

1. Cập nhật `pdf-evidence/SKILL.md` frontmatter `metadata.version`.
2. Append `pdf-evidence/CHANGELOG.md`:
   ```markdown
   ### 2026-MM-DD — vX.Y.Z — <title>
   **Thay đổi**: ...
   **Lý do**: ...
   **Files đã sửa**: ...
   **Eval score**: trước {…} / sau {…}
   **Known limitations**: ...
   **Lưu ý cho người sửa skill sau**: ...
   ```
3. Append `scaffolding/memory/skill_memory.json` với lesson (nếu có lỗi được sửa).
4. Copy `scaffolding/results/latest_report.json` → `scaffolding/results/vX.Y.Z_report.json`.
5. Nếu skill chạy ở `~/.zcode/skills/pdf-evidence/`, copy từ factory sang:
   ```bash
   cp -r pdf-evidence ~/.zcode/skills/pdf-evidence
   ```

## Phase 10 — Done

```bash
git add -A
git status    # phải thấy thay đổi có ý nghĩa
```

Báo cáo cho human: version trước → sau, metric trước → sau, fixture xanh, lesson mới.

## Lệnh cấm

- KHÔNG fine-tune, KHÔNG train lại model (PATCH 7).
- KHÔNG bump version nếu regression fail.
- KHÔNG tự ý minor/major bump mà không có human approval.
- KHÔNG ghi đè skill `pdf` cũ (~/.zcode/skills/pdf/).
- KHÔNG tải PDF bản quyền làm fixture.
- KHÔNG viết SKILL.md quá 500 dòng.
