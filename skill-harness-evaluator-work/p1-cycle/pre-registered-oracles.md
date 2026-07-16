# P1 Patch Cycle — Pre-Registered Oracles (written BEFORE patch development)

Per owner requirement: expected detector + expected failure reason locked before running.
Holdouts are different in form from the dev mutations.

## REQ-022 (data_accuracy_check) oracles

| Mutation | Form | Expected detector | Expected failure reason | Forbidden |
|---|---|---|---|---|
| MUT-DATA-REV-001 (dev) | corrupt ONE revenue figure in a per-year table | REQ-022 data_accuracy_check FAIL | corrupted year's value not found in its year context (the other years' values no longer substitute) | parser_crash, unrelated FAIL |
| MUT-DATA-REV-002 (HOLDOUT) | shift ALL revenue figures by a constant factor (global rescale) so NO year matches ground truth | REQ-022 data_accuracy_check FAIL | no revenue value matches financials.json within tolerance in revenue context | REQ-021 alone, wrong reason |

## REQ-027 (external_claim_flag_check) oracles

| Mutation | Form | Expected detector | Expected failure reason | Forbidden |
|---|---|---|---|---|
| MUT-EXTCLAIM-001 (dev) | inject WCM/MCH/store-count claim with NO flag word adjacent | REQ-027 external_claim_flag_check FAIL | external claim present, no flag within context window | parser, wrong reason |
| MUT-EXTCLAIM-002 (HOLDOUT) | inject a claim with a flag word FAR away (>500 chars), not adjacent — flag-in-document-but-not-on-claim must still FAIL | REQ-027 external_claim_flag_check FAIL | flag exists globally but not adjacent to the claim | pass because flag found anywhere |

## Clean control
| Artifact | Expected |
|---|---|
| Frozen clean PNJ | REQ-022 PASS, REQ-027 PASS (no false positive) |

## Scope
Patches touch ONLY: REQ-022 logic in `verify_data_accuracy`, REQ-027 logic in `verify_external_claim_flag`. No other validator changed unless evidence (none expected).

## Unlock criteria (owner spec)
- false_positive_count = 0
- missed_critical_mutations = 0
- correct_detection_rate = 1.0 (all P0 + valid P1 + holdouts)
- wrong_reason_failure_rate = 0.0
- specificity_rate = 1.0
- no out-of-scope changes
- native tests PASS
