# learning_candidates/

> Train-on-Use mechanism (v0.3.0). Raw signals captured during RUN mode for future TRAIN sessions.

## What this is

A **learning_candidate** is a raw signal that the skill detected something worth learning:
- a new document type not covered by current policy
- a citation/table/abstention/numeric defect
- low parse confidence on a table
- an OCR gap (scanned content the skill couldn't read)
- a novel pattern (multi-appendix, rotated table, chart-heavy, footnote-heavy, mixed-language, form-like)
- a user-reported error
- a self-check warning

Candidates are **NOT patches** and **NOT memory**:
- A *candidate* is a question / suspicion / "this looks worth investigating".
- A *skill_memory* entry is a confirmed lesson, validated through a TRAIN session with before/after metrics.

A candidate may be rejected. It only becomes memory (or a regression case, or a training session) after going through TRAIN.

## Schema

See `schema.json` (JSON Schema 2020-12). Each candidate has: `candidate_id` (LC-YYYY-NNN), `created_at`, `skill_version`, `source_session`, `input_file_type`, `document_type_detected`, `task_type`, `trigger`, `observed_issue`, `evidence` (≤300 chars, no sensitive content), `risk_level`, `suggested_action`, `related_failure_id`, `requires_human_review`, `status`.

## Directory layout

```
learning_candidates/
├── schema.json       # the JSON schema (source of truth)
├── README.md         # this file
└── open/             # candidates with status=open (pending TRAIN review)
    └── LC-2026-001.json   # one file per candidate
```

When a TRAIN session consumes a candidate, the file moves to status `accepted`/`rejected`/`converted_to_regression`/`converted_to_training_session` and stays in `open/` for audit (no deletion).

## How candidates are created (RUN mode)

RUN mode is the default user-facing mode. During a normal PDF task, the skill:

1. Performs the main task (answer/extract/compare).
2. Returns the answer to the user.
3. Runs an internal **post-run self-evaluation** against the checklist in `references/policies.md#train-on-use`.
4. For each fired trigger, writes a candidate file to `open/LC-YYYY-NNN.json`.
5. Does NOT modify SKILL.md, policies.md, scripts, memory, or version. RUN mode never self-patches.

## Triggers (summary — full list in policies.md#train-on-use)

| Trigger | Example | Default suggested_action |
|---------|---------|--------------------------|
| new_document_type | doc_type not in current policy enum | proposal_required |
| citation_defect | claim cites a page but no quote/table_id | create_regression |
| table_defect | table claim without table_id/chart_id | create_regression |
| abstention_defect | refusal buried in warnings[] | train_session |
| numeric_defect | sign/unit/period mismatch | train_session |
| legal_structure_defect | Điều/Khoản/Điểm lost | train_session |
| forecast_horizon_defect | horizon not labeled | create_regression |
| low_parse_confidence | table parse_confidence < 0.7 | train_session |
| ocr_required_unavailable | scanned page, no text layer | proposal_required |
| novel_pattern | multi-appendix / rotated table / chart-heavy / mixed-language | proposal_required |
| user_reported_error | user says answer is wrong | train_session |
| self_check_warning | any self-check item failed | train_session |

## Memory separation (critical)

```
learning_candidate  ≠  skill_memory
(raw signal)          (confirmed lesson)
```

- RUN mode creates candidates only.
- TRAIN mode reads candidates, runs the loop, and may promote a candidate to:
  - a regression case (`tests/regression/`),
  - a skill_memory entry (`scaffolding/memory/skill_memory.json`),
  - a policy patch (when approved).
- RELEASE mode bumps version after regression green.

A candidate MUST NOT be written directly to `skill_memory.json` without a TRAIN session and before/after metrics.

## Privacy

Candidates must NOT contain:
- full file content;
- personally identifiable information from the source PDF;
- proprietary text beyond a ≤300-char snippet needed to evidence the issue.

If the only way to evidence an issue is sensitive content → set `evidence: ""` and describe the issue generically in `observed_issue`.

## Lifecycle

```
RUN detects → writes LC-YYYY-NNN.json (status=open)
              ↓
TRAIN reviews → status ∈ {accepted, rejected, converted_to_regression, converted_to_training_session}
              ↓ (if accepted)
becomes: regression case | skill_memory entry | policy patch (via proposal)
```

Rejected candidates stay on disk for audit; they are not deleted.
