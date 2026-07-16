# Evaluator Self-Test Report (dogfooding) — skill-harness-evaluator v0.1.0

Spec §XII requires 10 self-checks. Results below are **observed** (actually run, 2026-07-12).

| # | Self-check | Result | Evidence |
|---|---|---|---|
| 1 | Schema validation (all 5 schemas are valid Draft2020-12 + instances validate) | PASS | `Draft202012Validator.check_schema` on 5 schemas; skill-spec + score-report validated against schema |
| 2 | Unit test for scoring (SDS weighted sum, N/A denominator, PRS) | PASS | test_scoring.py (17 tests) |
| 3 | Hard-gate does NOT let mean score override critical FAIL | PASS | test_scoring::test_hard_gate_veto_high_score_still_fail |
| 4 | N/A requirement does not corrupt denominator | PASS | test_scoring::test_na_excluded_from_denominator_never_auto_pass + test_all_na_yields_recall_null |
| 5 | High-score-but-critical-failure → overall FAIL | PASS | test_report_generation::test_critical_mutation_missed_forces_hard_gate_fail |
| 6 | Repeated-run aggregation matches known-expected stats | PASS | test_report_generation::test_sealed_fixture_aggregates_to_known_mean_std (mean=90.0, σ=6.4498) |
| 7 | Intervention classification (minor/major/critical) | PASS | test_scoring::test_intervention_rate_and_classification |
| 8 | Report generation end-to-end + schema-valid | PASS | test_report_generation::test_full_report_generation_end_to_end |
| 9 | Smoke evaluation on fixture skill (sealed known-expected) | PASS | evaluator-smoke-fixture → scorecard with hard_gates PASS, HRS publishable, verification_layer ROBUST |
| 10 | Evaluator used to evaluate real target skill | PASS | reports/target-skill-scorecard.json (equity-research-vn audit, this session) |

Plus the additions:
- **Mutation correct-detection (N2)** — test_scoring::test_mutation_correct_detection_is_primary_not_raw ✅
- **Specificity (N3)** — test_scoring::test_specificity_false_positive_blocks_robust ✅
- **Protocol immutability (N4)** — test_hard_gates::test_protocol_lock_is_hash_consistent ✅
- **Snapshot drift** — test_hard_gates::test_snapshot_detects_modification ✅
- **Run isolation** — test_hard_gates::test_isolate_run_produces_fresh_task_state ✅

## Self-evaluation limitations (honest)
- Evaluator **không thể tự chứng minh hoàn toàn** tính đúng đắn của chính nó — sealed fixtures có expected results nên math được verify, nhưng "scoring philosophy đúng hay sai" là judgement của người dùng.
- Cần deterministic test (đã có) + sealed fixture có expected (đã có); **không** dùng self-score làm bằng chứng duy nhất.
- Maturity `evaluator_engine.final_level`: điền **FUNCTIONAL** (chưa ROBUST — chưa có repeated agent-run evidence trên chính evaluator; dogfood là single-pass).

## Conclusion
Evaluator v0.1.0 passes all 10 §XII self-checks + 5 addition checks. Anti-cheating invariants verified by test. Ready to score other skills, with the explicit limitation that it scores **deterministic + verification** layers well and **agent-execution** layers only provisionally (needs genuine agent runs).
