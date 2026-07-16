# DEFINITION_OF_DONE — PDF Skill Factory

> PATCH 1. Một version `pdf-evidence` chỉ được release khi **tất cả** điều kiện dưới đây thoả.
> Nếu bất kỳ metric nào dưới ngưỡng, version KHÔNG được bump (xem `08-VERSIONING_PLAN.md`).

## Quy tắc chung

Definition of Done cho **mỗi version** `pdf-evidence vX.Y.Z`:

1. Tất cả metric ở bảng dưới ≥ threshold (không có metric nào dưới).
2. Toàn bộ regression suite (`scaffolding/tests/`) **100% xanh**.
3. Không có regression: các version trước pass, version này không pass thấp hơn version trước ở bất kỳ metric nào quá tolerance ±0.02.
4. CHANGELOG.md đã cập nhật với: thay đổi, lý do, files chạm, eval score trước/sau, limitations.
5. `skill_memory.json` đã append lesson mới (nếu có lỗi được sửa).
6. **PATCH 8**: Nếu là minor/major bump → phải có `APPROVAL_REQUEST.md` + chữ ký human `APPROVED: <name> <date>`.

## Threshold metric (v0.1 baseline)

| Metric | Ngưỡng v0.1 | Ngưỡng v1.0 (mục tiêu) | Loại | Ghi chú |
|--------|-------------|------------------------|------|---------|
| `citation_format_accuracy` | ≥ 0.95 | ≥ 0.98 | rule-based | mỗi citation có đủ `[file, page, section, quote]` |
| `citation_page_accuracy` | ≥ 0.90 | ≥ 0.95 | rule-based | page trong citation phải nằm trong evidence set |
| `abstention_accuracy` | ≥ 0.90 | ≥ 0.97 | rule-based | không có đáp án → phải nói "insufficient evidence" |
| `hallucination_rate` | ≤ 0.10 | ≤ 0.02 | LLM-judge (`groundedness_judge.md`) | claim không support / bịa |
| `table_fidelity` | ≥ 0.85 | ≥ 0.95 | rule-based cell-compare | header + đơn vị + cell đúng |
| `faithfulness` (LLM-judge) | ≥ 0.85 | ≥ 0.95 | `groundedness_judge.md` | thay thế `faithfulness_simple` baseline |
| `coverage` | ≥ 0.75 | ≥ 0.90 | rule-based | số điểm cần trả lời / số điểm trả lời được |
| `regression_suite_green` | 100% | 100% | pytest | không có test fail |

> **Lưu ý PATCH 3**: `faithfulness_simple` (substring heuristic trong `metrics.py`) **KHÔNG phải metric DoD**. Nó chỉ là CI smoke. Metric faithfulness DoD là `groundedness_judge.md` (LLM-judge).

## Threshold theo loại version

| Loại bump | Yêu cầu thêm |
|-----------|--------------|
| Patch `x.y.Z` | regression green + reviewer tự duyệt + DoD pass |
| Minor `x.Y.0` (PATCH 8) | + **human approval bắt buộc** + full eval trên benchmark hiện tại |
| Major `X.0.0` (PATCH 8) | + **human approval bắt buộc** + full re-eval trên **toàn bộ benchmark kể cả fixture cũ** + REVIEW_REPORT.md cập nhật |

## Checklist release (agent tự verify trước khi đề xuất bump)

```
[ ] wc -l pdf-evidence/SKILL.md ≤ 500
[ ] pytest scaffolding/tests/ 100% xanh
[ ] 5 fixtures tồn tại và pass threshold DoD
[ ] Mỗi metric ≥ threshold v0.1
[ ] CHANGELOG.md đã cập nhật entry cho version này
[ ] skill_memory.json đã append (nếu có lesson)
[ ] Nếu minor/major: APPROVAL_REQUEST.md đã có chữ ký APPROVED
[ ] 10 ràng buộc chất lượng (ASSUMPTIONS.md) vẫn pass
```

## Khi metric không pass

- KHÔNG bump version.
- Ghi lỗi vào `06-FAILURE_MODES.md` (mục mới).
- Tạo regression test case mới cho lỗi đó.
- Đề xuất instruction patch theo `RUNBOOK.md`.
- Lặp loop cho đến khi pass.

## Bằng chứng release

Mỗi version release phải kèm file `scaffolding/results/vX.Y.Z_report.json`:
```json
{
  "version": "0.1.0",
  "timestamp": "2026-07-06T...",
  "metrics": {"citation_format_accuracy": 0.97, "...": "..."},
  "regression_pass_rate": 1.0,
  "fixtures_evaluated": 5,
  "approval": {"required": false, "approved_by": null}
}
```
