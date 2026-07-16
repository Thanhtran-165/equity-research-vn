# Module spec — UpdateSkillInstruction (roadmap v0.7)

> DSPy-style SIGNATURE. Driver của "Update Skill → Regression → Version".

## Signature

```
UpdateSkillInstruction(
  failures: list[FailureAnalysis],
  current_instruction: SkillInstruction,
  eval_report: EvalReport
) -> patch: {old_text, new_text, reason, expected_metric_impact, risk, test_needed, version_target}
```

`FailureAnalysis = {failure_id, input, expected, actual, root_cause, rule_violated, suggested_fix}`

## Mô tả

Từ failure analysis + instruction hiện tại + eval report → đề xuất instruction patch cụ thể. Đây là module GEPA sẽ evolve instruction thật sự.

## Pattern học từ

- Reflexion (verbal feedback → memory).
- GEPA (reflective prompt evolution + Pareto + ASI).
- TextGrad (textual gradient → instruction rewrite).

## Output phải có

- `old_text` → `new_text` diff cụ thể (không "viết lại toàn bộ").
- `reason` dựa trên failure trace.
- `expected_metric_impact` (vd `citation_page_accuracy 0.88 → 0.92`).
- `risk` (vd "có thể làm parser chậm hơn").
- `test_needed` (regression test mới).
- `version_target` (patch/minor/major).

## Acceptance gate

- Patch phải pass regression suite trước khi commit.
- Minor/major → human approval (PATCH 8).
- Không accept patch nếu metric không improve.

## Roadmap

v0.1: spec only. v0.7+: cài DSPy + dspy.GEPA, chạy trên eval failure thật.

## v0.7+ compile hint

```
class UpdateSkillInstruction(dspy.Module):
    def __init__(self):
        self.prog = dspy.ChainOfThought("failures, current_instruction, eval_report -> patch")
```

Compile với metric `patch_acceptance_rate` (fraction patch được accept sau regression).
