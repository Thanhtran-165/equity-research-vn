# Defect ERVN-ARTIFACT-QUALITY-002 — Unflagged External Claims (MWG-02)

| Field | Value |
|---|---|
| Defect ID | ERVN-ARTIFACT-QUALITY-002 |
| Severity | MAJOR |
| Status | OPEN — INVESTIGATION |
| Component | `no_source_claim_gate.py` + `bounded_retry` |
| Layer | `SKILL_MODEL_OR_ARTIFACT_ADMISSION` |
| Discovered | 2026-07-19 (RC1 TH-MWG-02) |
| Owner directive | 2026-07-19 §4-§5 |
| Target candidate | equity-research-vn-1.0.1-rc2 |

## 1. Failure symptoms (TH-MWG-02)

```yaml
ticker: MWG
run_id: TH-MWG-02
verdict: FAIL
failed_REQs:
  - REQ-027:  # Số liệu external phải flag
      evidence:
        external_claims_found: 4
        unflagged:
          - pattern: "\\d+\\s*điểm bán"
            match: "000 điểm bán"
            tier: B
            reason: "needs qualifier (~, khoảng, theo công bố, or ước tính)"
          - (3 more similar)
  - REQ-021:  # auto-fail blocker
```

The agent produced 4 external claims about MWG store count ("điểm bán") without required qualifiers (~, khoảng, theo công bố, ước tính).

## 2. Investigation questions (per owner §4)

5. **Why were external claims not flagged?**
   - The agent should have prefixed each external claim with a qualifier
   - Did the model produce unflagged text, or did a runner step strip qualifiers?
   - Is `no_source_claim_gate` configured to detect "điểm bán" pattern?

6. **Was bounded_retry triggered correctly?**
   - REQ-027 fail should trigger UNFLAGGED_EXTERNAL_CLAIM retry per §5

## 3. Required admission preflight

Same as ERVN-ARTIFACT-QUALITY-001 §3. Additionally, the no_source_claim_gate must:

```yaml
no_source_claim_gate:
  patterns_to_enforce:
    - regex: "\\d+\\s*điểm bán"
      required_qualifier: "[~khoảng theo công bố ước tính]"
      on_violation: TRIGGER_BOUNDED_RETRY
```

## 4. Investigation log

```
[X] Q5: Inspect MWG-02 raw model output for qualifier presence
    Finding: Model DID produce qualifiers, but used "Hơn" (more than) which
    semantically means ~ / khoảng. Four occurrences found:
      - "~3,000 điểm bán" (ĐMX) — qualifier "~" valid
      - "Hơn 5,000 điểm bán" — "Hơn" not in registered qualifier set
      - "Hơn 7,000 điểm bán" — same
      - "hơn 7,000 điểm bán" — same
    Verdict: SEMANTIC_GAP — model used a valid Vietnamese hedge ("Hơn" = more than)
    that the verifier's regex doesn't recognize.

[X] Q6: Trace no_source_claim_gate invocation
    Finding: Gate ran and detected all 4 matches. Only the "~3,000" one is properly
    qualified; the 3 "Hơn" ones are flagged as unflagged because the regex's character
    class [~khoảng theo công bố ước tính] doesn't include 'H' (start of "Hơn") nor
    recognize the multi-character word "Hơn".

[X] Bounded retry evaluation
    Finding: REQ-027 is medium severity (not in critical trigger list). The bounded
    retry was not triggered for REQ-027. Final verifier caught it, REQ-021 blocked.
```

## 4a. Confirmed root cause

The verifier's qualifier regex `[~khoảng theo công bố ước tính]` is **character-based** (matches single characters in the set), not word-based. The Vietnamese hedge **"Hơn"** (more than) is a valid qualifier semantically equivalent to "khoảng" but is not registered.

## 4b. Required RC2 changes

Two options (RC2 picks one):

### Option A — Extend qualifier word list
```yaml
no_source_claim_gate:
  accepted_qualifiers:
    single_char: [~]
    full_words: [khoảng, theo công bố, ước tính, hơn, trên, xấp xỉ]
  regex: "([~]|\\b(khoảng|theo công bố|ước tính|hơn|trên|xấp xỉ)\\b)"
```

### Option B — Treat as bounded_retry trigger
- Add REQ-027 (`UNFLAGGED_EXTERNAL_CLAIM`) to bounded_retry trigger list
- On trigger, model gets one retry with explicit feedback to add qualifier

**RC2 uses both**: extend qualifier list (Option A) AND add REQ-027 to retry triggers (Option B) for defense in depth.

## 5. Linked evidence

- `cohort-c/targeted-hotfix-v1.0.1/TH-MWG-02/run-result.json`
- `cohort-c/targeted-hotfix-v1.0.1/TH-MWG-02/.task-state/evidence/REQ-027.json`
- `cohort-c/targeted-hotfix-v1.0.1/TH-MWG-02/.phase6-attempt-*.txt`
