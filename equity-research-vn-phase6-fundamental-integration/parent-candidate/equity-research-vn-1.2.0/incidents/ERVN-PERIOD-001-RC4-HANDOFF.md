# ERVN-PERIOD-001 — RC4 Handoff (from RC3 investigation)
**Date:** 2026-07-19
**Session:** RC3 closure + RC4 defect investigation

## RC3 closed

```yaml
rc3:
  runs: 12/12
  pass: 7
  fail_or_rejected: 5
  no_result: 0
  period_inversions: 0
  verdict: FAIL
  immutable: true
  closure_record: incidents/v1.0.1-rc3/RC3-CLOSURE-7OF12-FAIL.md
```

## 4 RC3 defects — investigation results

### Defect 1: ERVN-NA-ENFORCEMENT-002 (BVH-01/02) — ROOT CAUSE FOUND + FIXED

**Root cause (confirmed via 7-step trace):**
- Contract correct: `revenue=null, status=NOT_APPLICABLE, rule=INSURANCE_REVENUE_NOT_GENERIC_SALES`
- `serialize_data_block()` correct: produces `revenueStatus: "NOT_APPLICABLE"` ✓
- **BUT `inject_canonical_data()` skipped injection** because agent's DATA block had `revenue: [null,null,...]` which passed `validate_data_keys()` (revenue key present, no forbidden aliases)
- Agent DATA was missing `revenueStatus` + `revenueApplicabilityRule` but enforcer didn't check for these NA metadata keys

**Fix applied:** Added NA metadata check in `inject_canonical_data()`:
```python
# When contract has NOT_APPLICABLE fields, check if agent DATA has the required
# status/rule metadata keys. If missing, force injection even if validation passes.
for field, info in field_applicability.items():
    if info.get("status") == "NOT_APPLICABLE":
        status_key = f"{field}Status"
        if status_key not in agent_data:
            na_metadata_missing = True  # → force inject canonical DATA
```

**Verified:** After fix, enforcer now reports `action: replaced_agent_data_with_canonical`, `revenueStatus` + `NOT_APPLICABLE` present in output.

**File:** `/Users/bobo/ZCodeProject/agent-eval/runner-v1.0.1-rc3/data_contract_enforcer.py` (line ~215)

---

### Defect 2: ERVN-CONTENT-DEPTH-001 (POW-01) — ROOT CAUSE FOUND

**Root cause:**
- POW-01 artifact is 16KB skeleton (0 canonical sections, narration prefix)
- Admission gate **correctly rejects it** when tested standalone
- **BUT admission gate didn't run during cohort** — `phase_events.admission = None`
- Artifact was still written to disk and verifier ran on it

**Hypothesis:** The `if phase_id == "phase6_dashboard" and model_result["output"]:` guard at line 411 may not have triggered, OR the admission gate code path was bypassed by a different code branch (e.g., phase6 preflight loop overwriting model_result before admission gate runs).

**Fix needed:** Verify admission gate ALWAYS runs when phase6 produces output, regardless of which code path was taken. Add assertion: if HTML artifact exists in workspace, admission gate MUST have run.

**File:** `/Users/bobo/ZCodeProject/agent-eval/runner-v1.0.1-rc3/agent_runner.py` (phase6 block, ~line 411)

---

### Defect 3: ERVN-JS-VALIDITY-001 (MSN-02) — ROOT CAUSE KNOWN

**Root cause:**
- Agent produced HTML with JS syntax error (REQ-019 `node --check` returns exit 1)
- JS syntax is checked by artifact_integrity_gate (AIG), but only AFTER admission
- If AIG retry fails, artifact still proceeds to final verification

**Fix spec (from owner §4):**
- Add `node --check` (or equivalent JS parser) to **pre-admission** checks
- If JS invalid: bounded repair (1 attempt, fix script only)
- If repair fails: `FAIL_ARTIFACT_JS_INVALID`

**Regression fixtures needed:**
- missing bracket, unclosed string, trailing malformed expression, malformed DATA, clean multiline JS, JS with Vietnamese Unicode

---

### Defect 4: ERVN-ADMISSION-FALSE-POSITIVE-001 (MWG-02) — ROOT CAUSE KNOWN

**Root cause:**
- MWG-02 artifact is high-quality (106KB, 22 sections, 12 charts, all checks PASS)
- **Only failure: `required_audit_split_present = False`** — agent didn't use keyword "bẫy 5b" / "split-adjusted" / "cross-check EPS"
- For MWG (retail, no corporate action/split), audit-split requirement is NOT APPLICABLE

**Fix spec (from owner §6):**
- Replace keyword-based audit-split check with **applicability logic**:
  - If source metadata shows corporate action/split → audit-split APPLICABLE
  - If no evidence of split → audit-split NOT_APPLICABLE
- Don't remove requirement entirely; don't expand keyword list infinitely

**Implementation:** Check overview.json/events.csv for split/corporate action evidence. If none found, audit-split = NOT_APPLICABLE.

---

## RC4 scope (per owner §7)

```yaml
allowed_change_classes:
  - NA_enforcer_execution_and_final_artifact_encoding  # Defect 1 (FIXED)
  - admission_gate_always_runs                          # Defect 2 (root cause found)
  - JS_syntax_pre_admission                             # Defect 3
  - audit_split_applicability_logic                     # Defect 4
```

## RC4 pre-cohort regression (per owner §8)

Frozen fixtures from RC3 artifacts:
- `TH-BVH-01/BVH_Complete_Report.html` — NA enforcement fixture
- `TH-MSN-02/MSN_Complete_Report.html` — JS syntax fixture
- `TH-POW-01/POW_Complete_Report.html` — skeleton content depth fixture
- `TH-MWG-02/.phase6-rejected-raw.txt` — audit-split false positive fixture

## Files modified so far (RC4 work-in-progress)

- `data_contract_enforcer.py` — NA metadata check added (Defect 1 FIXED)
- `agent_runner.py` — needs investigation of admission gate bypass (Defect 2)
- `artifact_admission_gate.py` — needs JS check + audit-split applicability (Defects 3+4)

## Stop rule (per owner §10)

If RC4 also fails 12/12, do NOT open RC5. Evaluate architecture changes:
- deterministic_section_builder
- constrained_intermediate_representation
- section_level_generation
- removal_of_free_form_full_HTML_generation
