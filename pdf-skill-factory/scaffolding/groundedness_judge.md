# groundedness_judge.md — PATCH 4

> Spec cho LLM-judge verdict. Thay thế `faithfulness_simple` (heuristic) cho metric DoD.
> Runner v0.1 trả `-1.0` cho `faithfulness` và `hallucination_rate` nếu judge chưa chạy;
> v0.2+ wire spec này vào LLM call thật.

## Mục đích

Kiểm tra mỗi claim trong câu trả lời của skill có **được support bởi evidence** không,
theo cách tinh vi hơn substring match.

Verdict 3 trạng thái:

| Verdict | Ý nghĩa | Đóng góp metric |
|---------|---------|-----------------|
| `supported` | Evidence chứa quote/data **hỗ trợ trực tiếp** claim (verbatim hoặc paraphrase rõ ràng) | `faithfulness += 1` |
| `contradicted` | Evidence **trái ngược** claim (vd claim "+10%" nhưng evidence "-10%") | `hallucination_rate += 1` |
| `not_enough_evidence` | Evidence không support cũng không contradict (claim không có căn cứ) | `hallucination_rate += 1` |

Metric:
- `faithfulness = (#supported) / (#claims)`
- `hallucination_rate = (#contradicted + #not_enough_evidence) / (#claims)`

## Input (judge prompt)

```
You are a strict groundedness judge for a PDF-QA system.

You will receive:
- CLAIM: a single factual claim extracted from the model's answer.
- EVIDENCE: the document snippets (with page numbers) that the model cited or
  that were retrieved for the question.

Decide whether the CLAIM is grounded in the EVIDENCE. Return a JSON verdict.

Rules:
- Be smart, logical, and very critical.
- DO NOT attempt to answer the original question yourself.
- DO NOT use outside knowledge. Only what is in EVIDENCE counts.
- "supported" requires the evidence to directly back the claim (verbatim OR clear
  paraphrase OR numerical equivalent).
- "contradicted" requires the evidence to directly conflict with the claim
  (e.g. opposite sign, different number, opposite conclusion).
- "not_enough_evidence" means the evidence neither supports nor contradicts the claim.
- Be super concise in your reasoning.

CLAIM: <<the claim text>>

EVIDENCE:
<<evidence snippets, each prefixed with [page N]>>

Respond with ONLY this JSON (no prose, no markdown fence):
{
  "verdict": "supported" | "contradicted" | "not_enough_evidence",
  "confidence": 0.0,
  "reason": "<= 30 words",
  "supporting_quote": "<verbatim quote from evidence, or null>"
}
```

## Output JSON schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "groundedness verdict",
  "type": "object",
  "required": ["verdict", "confidence", "reason"],
  "properties": {
    "verdict": {"type": "string", "enum": ["supported", "contradicted", "not_enough_evidence"]},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "reason": {"type": "string", "maxLength": 300},
    "supporting_quote": {"type": ["string", "null"]}
  }
}
```

## Ví dụ

**Claim**: "Doanh thu Q1/2026 là 12.500 tỷ VNĐ."
**Evidence**: `[page 7] "...doanh thu hợp nhất Q1/2026 đạt 12.500 tỷ đồng, tăng 11% so với cùng kỳ..."`
**Verdict**:
```json
{"verdict": "supported", "confidence": 0.98, "reason": "Page 7 states Q1/2026 revenue is 12.500 tỷ VND, matching the claim.", "supporting_quote": "doanh thu hợp nhất Q1/2026 đạt 12.500 tỷ đồng"}
```

**Claim**: "Công ty có 5.000 nhân viên."
**Evidence**: `[page 7] "...doanh thu 12.500 tỷ..."` (không có thông tin nhân sự)
**Verdict**:
```json
{"verdict": "not_enough_evidence", "confidence": 0.9, "reason": "Evidence does not mention employee count.", "supporting_quote": null}
```

**Claim**: "Lợi nhuận giảm 10%."
**Evidence**: `[page 7] "...lợi nhuận tăng 10%..."`
**Verdict**:
```json
{"verdict": "contradicted", "confidence": 0.95, "reason": "Evidence says profit increased 10%, not decreased.", "supporting_quote": "lợi nhuận tăng 10%"}
```

## Wire-up (roadmap v0.2+)

```python
# pseudo-code — wire this into eval_runner.py for v0.2+
def judge_claim(claim: str, evidence: list[dict], llm_client) -> dict:
    prompt = build_prompt(claim, evidence)  # per spec above
    raw = llm_client.complete(prompt, response_format="json")
    return parse_verdict(raw)  # validate against schema
```

Cho v0.1: runner trả `-1.0` và in cảnh báo `"LLM-judge not wired — faithfulness/hallucination metrics unavailable; using faithfulness_simple baseline only (PATCH 3)."`

## Lưu ý PATCH 3

`faithfulness_simple` (substring heuristic) vẫn chạy ở v0.1 như CI smoke, nhưng KHÔNG thay thế judge này. DoD gates trên `faithfulness` (LLM-judge) — không phải `faithfulness_simple`.
