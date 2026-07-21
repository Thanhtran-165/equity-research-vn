# ERVN-PERIOD-001 — Session Handoff Document
**Date:** 2026-07-19
**Status:** INCIDENT OPEN — paused at RC3 build phase
**Reason for pause:** Untracked file loss due to git branch switch

## 1. Incident summary

```yaml
ERVN_PERIOD_001:
  classification: LATENT_RELEASE_DEFECT (Branch A)
  severity: CRITICAL
  defect: PERIOD_INVERSION in build_data_contract.py v1.0.0
  v1_0_0_tag: IMMUTABLE (untouched, hash-verified)
  period_hotfix_architecture: VALIDATED (0 inversions across 24 genuine runs)
  incident_status: OPEN
```

## 2. What was accomplished

### Phase 1 — Discovery & forensic (COMPLETE)
- Incident ticket opened with full root cause analysis
- Forensic audit: 34 tickers, 21 sectors, 475 (period,value) pairs — **376/475 (79.2%) inverted**
- Classification: **Branch A — LATENT_RELEASE_DEFECT** (release-time CSVs byte-identical to current)
- Verifier gap proven: v0.14.9 returns PASS on FPT artifact with 12/15 inverted pairs
- Affected artifact registry: **147 historical artifacts cataloged as INVERTED**

### Phase 2 — Hotfix architecture (COMPLETE + VALIDATED)
- `period_key_resolver.py`: 3-strategy resolution, fail-closed, validated on CTD (15/15 pairs MATCH)
- `period_integrity_gate.py`: 6 sub-checks, PASS clean / FAIL inverted
- `build_data_contract.py` v1.0.1: produces correct ascending contract on CTD, fail-closed on packs without metadata
- All 3 components hash-locked and validated

### Phase 3 — Requalification attempts (RC1, RC2 attempted, RC3 designed)

**RC1 cohort (CLOSED — 8/12 PASS):**
- 12 genuine runs completed
- 0 period-inversion defects (architecture works)
- 2 BVH FAILs: sector-applicability defect (insurance revenue=0 encoding)
- 2 POW/MWG FAILs: agent artifact variance

**RC2 cohort (CLOSED — 7/12 PASS):**
- 12 genuine runs completed
- 0 period-inversion defects
- 2 BVH NO_RESULT: agent_runner `aig_result` UnboundLocalError (ERVN-RUNNER-STATE-001)
- 1 BVH FAIL: REQ-026 null downstream gap (ERVN-DOWNSTREAM-NA-001)
- 2 FPT/MSN FAILs: skeleton artifacts admitted (ERVN-ARTIFACT-QUALITY-001/002)

**RC3 (DESIGNED, NOT BUILT — patches lost):**
- 3 patches designed with full specifications:
  - Patch A (RUNNER-STATE-001): admission_rejected state safety
  - Patch B (DOWNSTREAM-NA-001): NOT_APPLICABLE encoding in DATA + REQ-026 carve-out
  - Patch C (ARTIFACT-QUALITY-001/002): 8-check artifact completeness admission
- Pre-cohort regression designed: 25 sub-checks across 4 sections
- Hash-lock manifest created: aggregate `0f92584c...` (13 components)
- **BUT: patches were untracked files, lost during git branch switch**

## 3. What was lost

### Lost permanently (untracked files in git working directory)
- `agent-eval/runner-v1.0.1/` (RC1 runner mirror)
- `agent-eval/runner-v1.0.1-rc2/` (RC2 runner mirror)
- RC3-patched `agent_runner.py` (42319 bytes, with admission_rejected guard)
- RC3-patched `artifact_admission_gate.py` (13040 bytes, with 8 completeness checks)
- RC3-patched `data_contract_enforcer.py` (14658 bytes, with NOT_APPLICABLE encoding)
- RC1 cohort artifacts (12 runs × multiple files)
- RC2 cohort artifacts (12 runs × multiple files)
- `run_targeted_hotfix_rc2.py` (RC2 cohort runner script)

### Cause
Patches were created as untracked files / uncommitted modifications in `/Users/bobo/ZCodeProject/agent-eval/runner-v1.0.1-*/`. When git branch switched from the working branch (likely `msvs-stage-r` or `ira-stage-r`) to `economic-life-atlas`, the untracked files in those mirror directories were lost.

**Note:** No branch (`msvs-stage-r`, `ira-stage-r`, `main`, `economic-life-atlas`) contains `artifact_admission_gate.py` in `agent-eval/runner/`. This file was never committed to any branch.

## 4. What is preserved (in `~/.zcode/skills/`, outside git)

### Incident documentation (complete)
- `ERVN-PERIOD-001.md` (incident ticket with forensic classification)
- `ERVN-PERIOD-001-production-policy.yaml`
- `ERVN-PERIOD-001-hotfix-design.md`
- `ERVN-PERIOD-001-OWNER-REVIEW.md`
- `ERVN-PERIOD-001-forensic-summary.json` (34-ticker audit data)
- `ERVN-PERIOD-001-affected-artifact-registry.json` (147 inverted artifacts)

### Defect tickets (complete, with root cause analysis)
- `ERVN-SECTOR-APPLICABILITY-001.md`
- `ERVN-RUNNER-STATE-001.md`
- `ERVN-DOWNSTREAM-NA-001.md`
- `ERVN-ARTIFACT-QUALITY-001.md` (POW-02: audit-split + bare canvas)
- `ERVN-ARTIFACT-QUALITY-002.md` (MWG-02: "Hơn" qualifier not in regex)

### RC3 candidate components (in skill dir, preserved)
- `v1.0.1-rc3/runner/build_data_contract.py` (contract semantics with NOT_APPLICABLE)
- `v1.0.1-rc3/runner/period_key_resolver.py` (explicit-key resolution)
- `v1.0.1-rc3/runner/period_integrity_gate.py` (6 sub-checks + sector applicability)
- `v1.0.1-rc3/scripts/independent_verifier_v0.14.10.py` (REQ-PERIOD-INTEGRITY + typed qualifiers + REQ-026 carve-out)
- `v1.0.1-rc3/scripts/requirements_v1.0.1.yaml` (with REQ-PERIOD-INTEGRITY)

### Hash-lock manifests (historical evidence)
- `v1.0.1-candidate/ERVN-PERIOD-001-v1.0.1-candidate-hash-lock.json` (RC1: `4a5071fc...`)
- `v1.0.1-rc2/ERVN-PERIOD-001-v1.0.1-rc2-hash-lock.json` (RC2: `04f3005f...`)
- `v1.0.1-rc3/ERVN-PERIOD-001-v1.0.1-rc3-hash-lock.json` (RC3: `0f92584c...`)

### Closure records
- `v1.0.1-rc1/RC1-CLOSURE-8OF12-FAIL.md`
- `v1.0.1-rc2/RC2-CLOSURE-7OF12-FAIL.md`

### Regression test scripts
- `v1.0.1-candidate/tests/ERVN-PERIOD-001-regression-suite.py` (7-variant)
- `v1.0.1-rc2/tests/rc2-pre-cohort-regression.py` (8-section, 25-check)
- `v1.0.1-rc3/tests/rc3-pre-cohort-regression.py` (4-section, 25-check)

## 5. RC3 patches to rebuild (from defect ticket specs)

### Patch A — agent_runner.py (ERVN-RUNNER-STATE-001)
**Problem:** Line 469 `phase6_integrity = {"passed": aig_result["passed"]}` outside `if admitted/else` block. When admission FAILs, `aig_result` unbound → `UnboundLocalError` → NO_RESULT.

**Fix spec (from ticket):**
1. Initialize `admission_rejected = False` at start of phase6 block
2. When admission FAILs: set `admission_rejected = True`, initialize all phase6_* variables to skipped-NA dicts
3. Guard all downstream enforcers (DATA, valuation, balance_sheet, no_source) with `if admission_rejected:`
4. Skip writing empty `.html` file when rejected
5. Return structured FAIL with `execution_type: ADMISSION_REJECTED`

**Challenge:** Baseline `agent_runner.py` (568 lines, production) **does not have admission gate at all**. The version I worked with before had admission gate logic (~640+ lines). Need to either:
- (a) Reconstruct admission gate from defect ticket + design doc, OR
- (b) Find the correct baseline agent_runner from git history (stash/diff)

### Patch B — data_contract_enforcer.py (ERVN-DOWNSTREAM-NA-001)
**Problem:** RC2 contract change (`revenue=null+NOT_APPLICABLE`) not propagated to JS DATA block. REQ-026 searches for revenue array → not found → FAIL.

**Fix spec (from ticket):**
1. When contract has `field_applicability.revenue.status=NOT_APPLICABLE`: inject `revenue: null, revenueStatus: "NOT_APPLICABLE", revenueApplicabilityRule: <rule>` into DATA
2. REQ-026: 5-condition carve-out (contract null + status + rule + artifact encodes same + no revenue-dependent chart)

**Status:** Already partially rebuilt (data_contract_enforcer.py patched with NOT_APPLICABLE encoding). REQ-026 carve-out already in `v1.0.1-rc3/scripts/independent_verifier_v0.14.10.py` (preserved).

### Patch C — artifact_admission_gate.py (ERVN-ARTIFACT-QUALITY-001/002)
**Problem:** Admission gate runs structural checks but does not verify full artifact completeness (FPT-01/MSN-02: 18KB skeleton with 0 sections admitted).

**Fix spec (from ticket):**
8 minimum checks:
1. `required_sections_present`: ≥20 of 22 canonical sections
2. `required_sections_populated`: content depth ≥200 chars per section
3. `required_charts_present`: ≥10 new Chart() calls
4. `bare_canvas_count`: 0 (every canvas in .chart-wrap)
5. `required_audit_split_present`: semantic check (REQ-003 marker + EPS context)
6. `DATA_contract_present`: `const DATA = {...}` block
7. `required_valuation_fields_present`: PE + PB referenced
8. `external_claim_flags_deferred_to_verifier`: marked as deferred

**Challenge:** File doesn't exist in any branch. Need to create from scratch based on defect ticket spec.

## 6. vn-financial-data-collector status (unchanged)

```yaml
vn_financial_data_collector:
  standalone_maturity: STABLE_CANDIDATE
  generalization_cohort: PASS_20_OF_20
  collector_raw_alignment: PASS_180_OF_180
  integration_status: BLOCKED_PENDING_PARENT_HOTFIX
  integration_blocker: equity_research_vn_period_inversion (ERVN-PERIOD-001)
```

## 7. Lessons learned (post-mortem)

### Process failure: untracked file loss
**Root cause:** All RC1/RC2/RC3 patches were created as untracked files in `/Users/bobo/ZCodeProject/agent-eval/runner-v1.0.1-*/`. These directories were:
- Not in `.gitignore` (so they appeared as untracked)
- Not committed to any branch
- Not in `~/.zcode/skills/` (which is outside git and would have been safe)

When git branch switched (likely via `git checkout` or worktree operation), the untracked files were either:
- Overwritten by the target branch's files in the same paths, OR
- Removed by `git clean` if that was run

**Prevention (for future sessions):**
1. **Commit working files frequently** — even WIP patches should be committed to a feature branch
2. **Place patches in `~/.zcode/skills/`** (outside git) rather than in `/Users/bobo/ZCodeProject/` (git-tracked)
3. **Use `git stash` before branch switch** — preserves untracked files
4. **Create a dedicated ERVN-PERIOD-001 branch** for all hotfix work
5. **Hash-lock BEFORE running cohorts** — so lost files can be detected immediately

### What went well
- Period hotfix architecture validated through 24 genuine runs (0 inversions)
- Forensic audit methodology sound (376/475 → 0/720 after fix)
- Defect tickets comprehensive (root cause + fix spec for each)
- All critical evidence in `~/.zcode/skills/` (outside git) → preserved

## 8. Recommended next steps (for fresh session)

```text
1. Create dedicated branch: git checkout -b ervn-period-001-hotfix
2. Rebuild RC3 patches from defect ticket specs:
   a. agent_runner.py: add admission gate from ERVN-RUNNER-STATE-001 spec
   b. artifact_admission_gate.py: create from ERVN-ARTIFACT-QUALITY-001 spec
   c. data_contract_enforcer.py: already partially rebuilt
3. Commit each patch immediately after creation
4. Run RC3 pre-cohort regression (25 sub-checks)
5. Hash-lock RC3 (new aggregate)
6. Smoke test (1 FPT run)
7. Launch 12-run cohort
8. If 12/12 PASS: rollback drill → Step 5 shadow → Step 6 soak → close incident
```

## 9. Official status

```yaml
ERVN_PERIOD_001:
  incident_status: OPEN
  paused_at: RC3_BUILD (patches lost, need rebuild)
  period_hotfix: VALIDATED (0 inversions in 24 runs)
  rc1: CLOSED_FAIL_8_OF_12 (artifacts lost, closure record preserved)
  rc2: CLOSED_FAIL_7_OF_12 (artifacts lost, closure record preserved)
  rc3: DESIGNED_NOT_BUILT (patches lost, specs preserved in defect tickets)

equity_research_vn:
  version: 1.0.0 (immutable tag, untouched)
  production_status: SUSPENDED_FOR_AFFECTED_SOURCE_PATH
  next_candidate: 1.0.1-rc3 (requires rebuild)

vn_financial_data_collector:
  standalone_maturity: STABLE_CANDIDATE
  integration_status: BLOCKED_PENDING_PARENT_HOTFIX
```
