# training_sessions/

> Output of **TRAIN mode** sessions (v0.3.0+). Each session is a directory produced by running the TRAIN_SKILL_LOOP on one input file or one set of learning candidates.

## What this is

A *training session* is a structured loop that takes a candidate (or a user-provided file), runs the current skill, evaluates the output, identifies failures, proposes a minimal patch, applies it only if safe, re-runs, and decides whether to accept, reject, defer to human review, or mark inconclusive.

TRAIN mode is the **only** mode allowed to patch SKILL.md / policies.md / scripts / memory. RUN mode never patches; RELEASE mode only bumps version.

## Layout

One directory per session, named `YYYY-MM-DD_HHMMSS` or `YYYY-MM-DD_<label>`:

```
training_sessions/
├── README.md                                   # this file
├── 2026-07-06_110300/                          # IGWT 2026 session (v0.1.1 patch cycle)
├── 2026-07-06_v0.2.0_impl/                     # v0.2.0 implementation (P2.01–P2.07)
│   └── backup_v0.1.1/                          # rollback backups
└── 2026-07-06_v0.3.0_impl/                     # v0.3.0 implementation
    └── backup_v0.2.0/                           # rollback backups
```

## Required artifacts per TRAIN session

A session is considered complete only if these files exist (per TRAIN_SKILL_LOOP):

```
input_manifest.json
run_01_output.md
run_01_eval.json
failure_analysis.md
proposed_patch.md
applied_patch.diff      OR   rejected_patch.md
run_02_output.md         (if patch applied)
run_02_eval.json         (if patch applied)
regression_result.json   (if regression exists)
decision.md
```

## Decision values (decision.md)

- `accepted` — patch applied, primary failure fixed, KPI improved, regression green.
- `rejected` — patch unsafe or KPI regressed; runtime reverted.
- `needs_human_review` — patch non-minimal or schema/contract change; awaiting approval.
- `inconclusive` — insufficient data / file unreadable / cannot grade.
- `max_iterations_reached` — hit MAX_ITERATIONS without resolving.

## How sessions relate to learning candidates

A TRAIN session may consume one or more `learning_candidates/open/LC-*.json` files. The session's `input_manifest.json` lists which candidates it consumed. After the session, those candidates' `status` field transitions to `accepted`/`rejected`/`converted_to_regression`/`converted_to_training_session` (the candidate file stays on disk for audit).

## Backups

Before patching runtime, each session creates a `backup_vX.Y.Z/` subdir with copies of every file it intends to modify. This enables rollback if post-patch regression fails.

## Anti-patterns

- ❌ A RUN-mode task that wrote here (only TRAIN writes sessions).
- ❌ A session missing required artifacts (treat as `inconclusive`).
- ❌ A session that bumped `metadata.version` (only RELEASE bumps).
- ❌ A session that deleted a previous session's data.
