# Initial Risk Register — equity-research-vn audit

Recorded: 2026-07-12 (P0)

## R1. Fixture-data integrity (HIGH)
- **Risk:** The verifier's data-accuracy checks (REQ-022→026) read `data/{financials,balance_sheet,cash_flow}.json` *sibling to the report*. The CTD report is an **orphan** (no `data/` dir) → those REQs fail structurally, not because the report is wrong. Scoring that as a "correctness failure" would be a fixture error (spec §IX `fixture_error`), not a skill defect.
- **Mitigation:** Use **PNJ_Complete_Report.html** (complete deployed artifact, has sibling `data/`) as the primary frozen artifact for correctness + repeatability + mutation streams. Keep CTD as a secondary "hardship" artifact whose data-REQ N/A is explicitly recorded.

## R2. Self-verification loop (HIGH — addressed by N2/N3)
- **Risk:** Correctness evidence drawn only from the target's own verifier inherits the verifier's blind spots.
- **Mitigation:** Mutation/defect-injection suite (5 oracles) + clean-control specificity test. A verifier that PASSes a corrupted report = missed critical defect → hard gate.

## R3. Verifier-repeatability ≠ agent-stability (HIGH — addressed in plan)
- **Risk:** N=10 verifier reruns on a *frozen* artifact prove verifier determinism, NOT that the agent can produce the report 10× reliably.
- **Mitigation:** Separate KPI `verification_layer.*`; never feed into agent pass-rate / autonomous-completion. Maturity tiered.

## R4. REQ-028 fails on the very artifact it was learned from (MEDIUM — informative)
- **Risk/Observation:** REQ-028 (`chart_runtime_check`) was added specifically after the "PNJ v2: 27/27 PASS but charts crash" lesson. It FAILs on the actual PNJ_Complete_Report.html (chartBSDt2 looks like a duplicate). This is either a real residual defect in the artifact or a verifier false-positive — the audit must distinguish these (this is exactly what the specificity/clean-control test guards).
- **Mitigation:** Clean control (frozen PASS-expected artifact) + recompute checks.

## R5. `_summary.json.details` is empty (LOW — tooling)
- **Risk:** The verifier writes per-REQ evidence files but leaves the `details` array in `_summary.json` empty. The evaluator must read per-REQ evidence files, not rely on `details`.
- **Mitigation:** Evaluator reads `evidence/REQ-*.json` directly.

## R6. vnstock may require network (MEDIUM — honesty)
- **Risk:** Phase 0 REQ-002 period-count may hit vnstock's upstream. Reproducibility of that single REQ depends on network.
- **Mitigation:** Label import-check `local`, period-count `may_require_network`. Period-count evidence is integration-grade only, not deterministic.

## R7. Target immutability (MEDIUM — process)
- **Risk:** If `equity-research-vn` changes mid-audit, all hashes/scores are void.
- **Mitigation:** `target-skill-snapshot.json` recorded (directory_sha256, per-file sha256). Audit void on drift. Original skill never modified; any patched candidate is a separate copy.
