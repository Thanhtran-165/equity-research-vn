# Failure Taxonomy — equity-research-vn re-audit (2026-07-21)

4-bucket → 9-sub root-cause mapping (spec §IX). Each failure traced to a specific root cause.

## Summary

```yaml
total_failures_observed: 2  # both revolve around MUT-VALUATION-001
hard_gate_fail_count: 2
buckets:
  specification: 1
  execution: 0
  enforcement: 1
  infrastructure: 0
```

## Bucket 1: SPECIFICATION

### 1A. Test oracle under-specification

**Failure:** MUT-VALUATION-001 (one-shot P/E corruption 9.1→33.7 in KPI card only) was not detected by REQ-025 (valuation_recompute_check). The verifier correctly used majority-vote logic to identify primary P/E value as 9.1x (10/11 occurrences); the lone 33.7x was treated as outlier/projection.

**Root cause:** The mutation oracle contract specified "corrupt one P/E value" without constraining HOW MANY semantic positions the report uses for the same metric. A real report has 11+ P/E 9.1x positions (KPI card, sec-valuation, peer table, bottom crawlable div, etc.); corrupting only 1 leaves the majority intact.

**Evidence:**
- Original MUT-VALUATION-001: REQ-025 PASS (verifier picked 9.1x via majority vote)
- Stricter MUT-VALUATION-002 (all 11 P/E positions corrupted): REQ-025 FAIL ✓

**Severity:** Specification-level (oracle design), not verifier defect.

**Fix (P0):** Future mutation oracles for valuation must specify "corrupt the value in N semantic positions where N ≥ 3" or "corrupt ALL occurrences" to reflect real-world report structure. Alternatively, document in the oracle contract that the verifier's majority-vote semantics are part of the correctness contract.

## Bucket 2: EXECUTION

(none observed)

## Bucket 3: ENFORCEMENT

### 3A. Verifier evidence-provenance (residual from prior audit)

**Status:** Prior audit P0-3 flagged REQ-021 evidence not bound to current run state. Re-audit shows this is now caught when mutation forces REQ-018 FAIL (MUT-DEPLOY-001 → REQ-021 FAIL correctly). No new defect.

**Caveat:** Verifier logic for REQ-021 reads `unresolved_required_failures` count from current run, so provenance binding is implicit (per-run .task-state). Still no explicit `source_run_id`/`source_snapshot_hash` fields, but practically safe because evidence files live in run-scoped `.task-state/evidence/`.

**Severity:** LOW (residual). No longer blocking.

## Bucket 4: INFRASTRUCTURE

(none observed)

## Net statement

The only blocking failure (HG-VALIDATOR-MISSED-CRITICAL) is a **test oracle specification gap**, NOT a verifier implementation defect. Verifier correctly handles real-world P/E corruption (proven via MUT-VALUATION-002). The 1.1.0 target skill has materially improved vs prior audit (specificity 0.0→1.0; missed critical 3→1; correct detection 0.4→0.8).

**Hard gate remains FAIL** because the frozen oracle contract specified 5 oracles including the under-specified MUT-VALUATION-001, and we do not weaken the gate retroactively. The reclassification is documented for the owner but does not veto the FAIL.
