# File 5 — PDF_EVAL_PLAN.md

> Benchmark + metric plan cho skill `pdf-evidence`. Theo brief mục 3.3.
> Harness thực ở `scaffolding/eval_runner.py` + `scaffolding/metrics.py`.

## Benchmark — 15 loại test case (bắt buộc)

| # | Loại | Fixture v0.1 | Mô tả |
|---|------|--------------|-------|
| 1 | PDF text sạch | `fixtures/01_text_qa` ✅ | hỏi nội dung trực tiếp |
| 2 | PDF scan | (roadmap v0.5) | OCR routing — v0.1 phải abstain + cảnh báo |
| 3 | PDF có bảng | `fixtures/03_table` ✅ | extract + giữ header/units |
| 4 | Bảng bị xoay | (roadmap v0.4) | detect rotation |
| 5 | Báo cáo tài chính | (roadmap v0.4) | units/period/sign |
| 6 | Văn bản pháp lý | `fixtures/04_legal_mock` ✅ | giữ điều/khoản/điểm |
| 7 | Văn bản sửa đổi | `fixtures/05_multipdf_comparison` ✅ | so sánh gốc vs sửa đổi |
| 8 | Multi-PDF comparison | `fixtures/05_multipdf_comparison` ✅ | tìm khác biệt |
| 9 | Không có đáp án | `fixtures/02_no_answer_abstention` ✅ | phải abstain |
| 10 | Trích nguyên văn | `fixtures/01_text_qa` (sub) | quote verbatim |
| 11 | Tóm tắt | (sub-case) | summary ngắn |
| 12 | Số liệu | `fixtures/03_table` (sub) | numeric accuracy |
| 13 | Phát hiện thay đổi | `fixtures/05_multipdf_comparison` ✅ | detect_changes task |
| 14 | Chính vs phụ lục | (roadmap v0.3) | distinguish main vs appendix |
| 15 | Mức độ chắc chắn | (sub-case) | confidence calibration |

**PATCH 2**: 5 fixture v0.1 đủ cover loại 1, 3, 6, 7, 8, 9, 10, 12, 13. Loại còn lại ở roadmap.

## Fixture format

Mỗi fixture = thư mục `NN_<name>/`:
```
NN_<name>/
├── case.json     # input + ground-truth
├── source.pdf    # (hoặc source_a.pdf + source_b.pdf cho multi)
└── README.md     # mô tả case (optional)
```

`case.json` schema:
```json
{
  "id": "01_text_qa",
  "documents": [{"path": "source.pdf", "alias": "doc1"}],
  "question": "...",
  "task": "qa",
  "output_format": "json",
  "constraint": {"pdf_only": true, "language": "vi"},
  "expected": {
    "answer_contains": ["12.500 tỷ"],
    "answer_not_contains": [],
    "abstention_expected": false,
    "expected_citations": [{"page": 7, "section_keyword": "Tổng quan"}],
    "expected_table": null,
    "outside_knowledge_allowed": false
  },
  "metric_targets": {
    "citation_format_accuracy": 1.0,
    "citation_page_accuracy": 1.0,
    "abstention_accuracy": 1.0,
    "hallucination_rate": 0.0
  }
}
```

## Metric — 14 (theo brief mục 3.3)

| Metric | Loại | Định nghĩa | Implement v0.1 |
|--------|------|-----------|----------------|
| `citation_format_accuracy` | rule | mỗi citation có đủ `[file, page, section, quote]` | regex ✅ |
| `citation_page_accuracy` | rule | page trong citation ∈ evidence set | set membership ✅ |
| `abstention_accuracy` | rule | expected abstain → actual abstain; expected answer → actual answer | compare flag ✅ |
| `hallucination_rate` | LLM-judge | claim không support / total claims | `groundedness_judge.md` ✅ (PATCH 4) |
| `faithfulness` | LLM-judge | mỗi claim supported by cited page | `groundedness_judge.md` ✅ (thay `faithfulness_simple`) |
| `faithfulness_simple` | heuristic (BASELINE) | substring match claim↔evidence | `metrics.py` ⚠️ PATCH 3 — không phải metric cuối |
| `answer_correctness` | rule + LLM | answer chứa `expected.answer_contains`, không chứa `answer_not_contains` | rule ✅ + LLM (roadmap) |
| `page_accuracy` | rule | cited page đúng page thật chứa evidence | compare w/ fixture ✅ |
| `table_fidelity` | rule | cell-by-cell: header/units/rows đúng | cell compare ✅ |
| `numeric_accuracy` | rule | số trong answer khớp fixture | regex số ✅ |
| `legal_clause_preservation` | rule | "Điều X/Khoản Y/Điểm z" giữ nguyên | regex ✅ |
| `coverage` | rule | số điểm cần trả lời / trả lời được | count ✅ |
| `concision` | rule | answer length ≤ max_length | count ✅ |
| `vietnamese_quality` | LLM-judge (roadmap) | tiếng Việt tự nhiên, đúng thuật ngữ | manual v0.1 |

## PATCH 3 — faithfulness_simple là BASELINE, KHÔNG phải metric cuối

- `faithfulness_simple` trong `metrics.py`: substring heuristic — claim có xuất hiện verbatim trong evidence không?
- Hữu ích cho CI smoke, KHÔNG đủ cho release decision.
- **Metric faithfulness DoD** = `groundedness_judge.md` (LLM-judge verdict `supported/contradicted/not_enough_evidence`).
- Runner v0.1 chạy cả 2; báo cáo tách cột "heuristic" vs "llm-judge".

## PATCH 4 — groundedness_judge verdict

Xem `scaffolding/groundedness_judge.md`. Tóm tắt:
- Input: `{claim, evidence_context}`.
- Output JSON: `{verdict: "supported"|"contradicted"|"not_enough_evidence", confidence, reason, supporting_quote?}`.
- `faithfulness` = (count supported) / (total claims).
- `hallucination_rate` = (count contradicted + not_enough_evidence) / total.

## Score cited answer vs abstained answer

| Item type | Đúng | Sai |
|-----------|------|-----|
| Answerable (gold = answer) | answer đúng + citation đúng = 1.0 | sai số liệu/sai trang/thiếu citation = giảm |
| Unanswerable (gold = "no answer") | abstain (`abstention_flag=true`) = 1.0 | bịa (hallucinate) = 0.0 |
| Mixed (gold = "partial") | trả lời phần có evidence + nói rõ phần thiếu | bịa phần thiếu = 0.0 |

## Regression policy

- Mỗi bug đã fix → thêm pytest case permanent (`scaffolding/tests/test_regression.py`).
- Suite chỉ tăng, không xóa case cũ.
- Bump version bị block nếu regression không 100% xanh (`DEFINITION_OF_DONE.md`).

## Báo cáo eval

`scaffolding/results/latest_report.json`:
```json
{
  "timestamp": "...",
  "version_tested": "0.1.0",
  "fixtures_evaluated": 5,
  "metrics": {"citation_format_accuracy": 0.97, "...": "..."},
  "per_fixture": [{"id": "01_text_qa", "pass": true, "...": "..."}],
  "regression_pass_rate": 1.0,
  "dod_pass": true
}
```

Version bump yêu cầu `dod_pass=true`.
