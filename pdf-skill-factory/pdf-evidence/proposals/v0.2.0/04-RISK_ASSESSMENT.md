# 04 — RISK_ASSESSMENT.md (v0.2.0)

> Risk analysis for the 2 proposed changes (F-ABSTAIN-001 schema, TABLE-WIRING-001 wiring).
> Each risk uses the 6-field format: Risk / Severity / Likelihood / Mitigation / Regression test / Human approval required.

## Risk register

### R1. Schema compatibility risk

```
Risk: Existing downstream consumers of pdf-evidence output JSON use strict schema validation; adding partial_abstentions[] causes them to reject the output.
Severity: medium
Likelihood: low
Mitigation: Field is ADDITIVE (no existing field removed/renamed). Treat unknown field as optional. Document in CHANGELOG. SemVer minor bump (0.1.x → 0.2.0) signals new feature.
Regression test: C.1 — 5 v0.1.1 fixtures must still pass (they have partial_abstentions=[] by default, backward compatible).
Human approval required: yes (part of v0.2.0 minor bump)
```

### R2. Output verbosity risk

```
Risk: partial_abstentions[] + the new "⚠ Phần không đủ bằng chứng" text section make every multi-part answer longer; some consumers may truncate.
Severity: low
Likelihood: medium
Mitigation: partial_abstentions[] only populated when partial abstention EXISTS (empty array otherwise). Text section only appears when partial_abstentions[] is non-empty. JSON consumers unaffected; text consumers see additive section.
Regression test: A.1 — verify answer length stays within reasonable bound; section only appears when expected.
Human approval required: yes (part of v0.2.0)
```

### R3. False abstention risk (over-refusal)

```
Risk: Skill becomes too eager to refuse, populating partial_abstentions[] for sub-questions that ARE answerable, hurting answer_correctness and coverage.
Severity: high
Likelihood: medium
Mitigation: partial_abstentions[] entry MUST include missing_evidence (concrete) + confidence ≥ 0.7 for the refusal itself. Eval gate partial_abstention_accuracy checks refusal appears ONLY when expected (not when answerable). Anti-pattern test: A.1's "revenue" part must NOT appear in partial_abstentions[].
Regression test: A.1, A.2, A.4 — refusal appears only for genuinely missing parts; coverage ≥ 0.80 on answerable parts.
Human approval required: yes
```

### R4. Under-abstention risk (under-refusal)

```
Risk: Skill keeps answering peripheral sub-questions while refusing only the core one, or buries refusal in warnings[] instead of partial_abstentions[] — repeating the original F-ABSTAIN-001 failure in a new form.
Severity: high
Likelihood: medium
Mitigation: abstention_visibility metric ENFORCES top-level placement. If load-bearing sub-question is unanswerable → abstention_flag=true (full refuse), not partial. Eval gate abstention_visibility=top_level.
Regression test: A.2 — conclusion-beyond-evidence must full-refuse OR clearly partial-refuse at top level, NOT in warnings[].
Human approval required: yes
```

### R5. Table parse uncertainty risk

```
Risk: New ExtractTable wiring surfaces more tables but pdfplumber mis-parses merged/rotated/borderless tables; skill cites fabricated or misaligned cells with false confidence.
Severity: high
Likelihood: medium
Mitigation: parse_confidence heuristic; table_uncertainty_disclosure=true when confidence < 0.7; cells with null → abstain (do NOT guess). Round-trip verify each numeric claim against source cell. Charts always flagged lower confidence.
Regression test: B.5 — uncertain table must disclose; B.3 — negative numbers normalized correctly.
Human approval required: yes
```

### R6. Numeric hallucination risk

```
Risk: Skill quotes a number from the wrong column/row (e.g. Q1/2025 quoted as Q1/2026), or invents a number not in extracted cells, especially in multi-period tables.
Severity: high
Likelihood: medium
Mitigation: Citation MUST include row/col reference; round-trip check; sign check ((N)↔-N); column provenance preserved. Anti-hallucination rules in 02-TABLE_WIRING_PROPOSAL.md #9.
Regression test: B.2 — multi-period table, no cross-period confusion; B.3 — sign preserved.
Human approval required: yes
```

### R7. Regression risk (v0.1.1 breaks)

```
Risk: Code change for ExtractTable + schema addition breaks one of the 5 v0.1.1 fixtures or causes F-FORECAST-001 / F-TABLE-001 to regress.
Severity: high
Likelihood: low
Mitigation: v0.1.1 fixtures' skill_output.json default partial_abstentions=[] (backward compat). Run full regression (C.1-C.4) BEFORE any version bump. If any v0.1.1 metric regresses > tolerance → block release, do not bump.
Regression test: C.1 (5 fixtures), C.2 (F-FORECAST-001), C.3 (F-TABLE-001), C.4 (no hallucination).
Human approval required: yes (release gate)
```

### R8. Skill bloat risk

```
Risk: Adding partial_abstentions policy + table-wiring details inflates SKILL.md past 500 lines or fragments policies.md beyond maintainability.
Severity: medium
Likelihood: medium
Mitigation: SKILL.md stays < 500 lines (currently 105; budget headroom ~395). Heavy detail goes to references/ (policies.md, parsers.md). New table-wiring code goes to scripts/, not SKILL.md. Word-count check before release.
Regression test: wc -l SKILL.md ≤ 500 as release gate.
Human approval required: no (self-enforced)
```

### R9. Dependency risk

```
Risk: TABLE-WIRING-001 tempts adding Camelot/Surya/paddleocr heavy deps in v0.2.0.
Severity: medium
Likelihood: low
Mitigation: v0.2.0 uses pdfplumber ONLY (already installed). Chart detection is heuristic (image regions). Camelot deferred to v0.3+ IF pdfplumber proves insufficient on real fixtures. No new pip dependency in v0.2.0.
Regression test: requirements check — no new import statements beyond pdfplumber/pypdf/reportlab/pytest.
Human approval required: no (self-enforced; if a heavy dep turns out to be needed → escalate to human review)
```

---

## Risk summary

| Severity\Likelihood | low | medium | high |
|---------------------|-----|--------|------|
| **high** | R7 | R3, R4, R5, R6 | — |
| **medium** | R9 | R1, R2, R8 | — |
| **low** | — | — | — |

**Highest concerns**: R3 (false abstention), R4 (under-abstention), R5 (table parse uncertainty), R6 (numeric hallucination) — all high-severity/medium-likelihood. All have explicit mitigation + regression test + require human approval.

**Net assessment**: v0.2.0 is a **moderate-risk minor bump**. Risks are bounded by additive schema, no new heavy dependency, and explicit eval gates. Approval recommended conditional on Group A/B/C tests passing in implementation phase.
