# File 8 — VERSIONING_PLAN.md

> Kế hoạch version hóa + PATCH 8: human approval gate cho minor/major bump.

## Roadmap version

```
v0.1 — baseline evidence/citation           ← scope dự án này (ĐÃ DELIVER)
v0.2 — table extraction rules
v0.3 — legal comparison rules
v0.4 — financial report rules
v0.5 — OCR/scan robustness
v0.6 — multi-PDF synthesis
v0.7 — auto-eval and self-refine (GEPA-style)
v1.0 — stable release
```

## SemVer áp dụng

| Loại | Khi nào | Approval |
|------|---------|----------|
| Patch `x.y.Z` | fix bug, sửa rule nhỏ, không thêm policy/sub-skill, không breaking | reviewer tự duyệt |
| Minor `x.Y.0` | thêm policy, thêm sub-skill, sửa workflow, thay đổi output schema (backward-compatible) | **HUMAN APPROVAL BẮT BUỘC (PATCH 8)** |
| Major `X.0.0` | breaking change (schema breaking, định nghĩa lại skill, change output contract) | **HUMAN APPROVAL + FULL RE-EVAL (PATCH 8)** |

## Mỗi version phải có (ràng buộc chất lượng #8)

- **Changelog** entry (`pdf-evidence/CHANGELOG.md`).
- **Added rules**: rule mới trong `references/policies.md`.
- **Removed rules**: rule bỏ (nếu có).
- **Known limitations**: giới hạn version này.
- **Eval score**: trước/sau (theo `scaffolding/results/vX.Y.Z_report.json`).
- **Regression result**: pass rate.
- **Recommended next improvement**: gợi ý version kế tiếp.

## PATCH 8 — Human approval gate

### Quy trình patch bump `x.y.Z`

1. Agent chạy eval → DoD pass.
2. Agent tự duyệt + commit + bump version trong SKILL.md `metadata.version`.
3. Append CHANGELOG.
4. Không cần file approval.

### Quy trình minor bump `x.Y.0`

1. Agent chạy eval → DoD pass + regression 100% xanh.
2. Agent sinh `scaffolding/results/APPROVAL_REQUEST.md`:
   ```markdown
   # Approval Request — pdf-evidence <old> → <new>

   - **Loại**: minor
   - **Reason**: <vd: thêm table extraction rules cho v0.2>
   - **Changes**:
     - thêm `references/policies.md#table-fidelity` rule;
     - thêm sub-skill `ExtractTable` module;
     - thay đổi output: thêm `expected_table` field (backward-compatible).
   - **Eval before**: {citation_format_accuracy: 0.97, ...}
   - **Eval after**:  {...}
   - **Regression**: 100% xanh (N tests)
   - **Risk**: <vd: parser chậm hơn 20%>
   - **Human cần duyệt**: <tên>

   ## Approval
   - [ ] APPROVED: ____________ (name) — date: ______
   - [ ] REJECTED: lý do ____________________________
   ```
3. **DỪNG**. Đợi human điền `APPROVED: <name> <date>`.
4. Không có chữ ký → **KHÔNG bump**.
5. Có chữ ký → bump version trong SKILL.md, append CHANGELOG, copy skill sang `~/.zcode/skills/`.

### Quy trình major bump `X.0.0`

Như minor, cộng thêm:

- **Full re-eval trên toàn bộ benchmark kể cả fixture cũ** (không chỉ benchmark hiện tại).
- **REVIEW_REPORT.md cập nhật** với breaking changes + migration guide.
- Human approval bắt buộc + 2 chữ ký nếu có thể (reviewer + maintainer).

## Template CHANGELOG entry

```markdown
### 2026-MM-DD — vX.Y.Z — <title>

**Loại**: patch | minor | major
**Approval**: tự duyệt | APPROVED: <name> <date> | (link APPROVAL_REQUEST.md)

**Thay đổi**:
- ...

**Lý do**:
- ...

**Files đã sửa**:
- pdf-evidence/SKILL.md
- pdf-evidence/references/policies.md
- ...

**Eval score**:
- Trước (vX.Y.Z-prev): {citation_format_accuracy: ..., hallucination_rate: ...}
- Sau  (vX.Y.Z):      {...}

**Regression**: N/N pass (100%)

**Known limitations**:
- ...

**Recommended next improvement**:
- vế sau (vd: v0.2 → table extraction rules, fix F11/F12)
```

## Anti-patterns (KHÔNG)

- Bump version mà regression fail.
- Bump version mà không có eval score trước/sau.
- Minor/major bump không có human approval.
- Bump version mà CHANGELOG không đầy đủ.
- Đổi version trong SKILL.md nhưng không copy sang `~/.zcode/skills/`.
- Patch bump che giấu breaking change.

## Version hiện tại

`pdf-evidence` v0.1.0 — baseline evidence/citation (deliverable dự án này).
