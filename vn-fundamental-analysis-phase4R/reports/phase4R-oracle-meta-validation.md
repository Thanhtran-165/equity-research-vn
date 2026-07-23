# Phase 4R — Oracle Meta-Validation (P4R-E)

**Status:** PASS — 32/32 oracles are valid, material, no-op=false, wrong-target=false.

---

## 1. Meta-validation methodology

Each of the 32 mutations was checked against 7 criteria before the fresh batch (P4R-F):

| Criterion | Check | Result |
|---|---|---|
| `target_exists` | The mutated field exists in the schema | 32/32 |
| `fixture_precondition_satisfied` | The clean fixture provides the precondition | 32/32 |
| `semantic_change_nonzero` | The mutation changes a material semantic property | 32/32 |
| `materiality_nonzero` | The mutation is non-trivial | 32/32 |
| `expected_error_reachable` | The expected error code is emitted by a reachable validator | 32/32 |
| `expected_primary_owner_defined` | The expected owner is a real component | 32/32 |
| `no_op` | Is the mutation a no-op? | false for all 32 |
| `wrong_target` | Does the mutation hit the wrong target? | false for all 32 |

---

## 2. Clean control + positive control + inversion

- **Clean control:** `_clean_request()` runs through runner + verifier → `PASS` (no errors, verifier verdict PASS).
- **Positive control:** Each mutation produces at least one error code in runner errors or verifier mismatches.
- **Inversion:** For 6 hardened areas (share basis, denominator, period, scope, peer, provenance) a dedicated inversion test exists in `tests/test_phase4r_verifier_inversion.py` — clean PASS, corrupted FAIL, restored PASS.
- **No-op detection:** All 32 mutations change at least one input value or binding; none is identity.
- **Wrong-target detection:** Each mutation's `expected_error` matches the validator that owns the corrupted field.
- **Mutation-ID hardcoding test:** The classifier in `run_mutation()` matches on error *codes*, not mutation *IDs*. No mutation ID appears in runner/verifier code.

---

## 3. Per-mutation summary (32/32 valid)

All 32 mutations are valid material oracles. Detailed results in
`manifests/phase4R-mutation-manifest.json` (fresh batch, 32/32 caught).

| Category | Count | All valid |
|---|---|---|
| Unit & scale | 5 | yes |
| Share & split | 5 | yes |
| Formula | 7 | yes |
| Applicability & missing data | 5 | yes |
| Period & scope | 4 | yes |
| Peer | 4 | yes |
| Provenance & export | 2 | yes |
| **Total** | **32** | **yes** |

---

## 4. P4R-E gate

```yaml
P4R_E_gate:
  mutations_reviewed: 32/32
  valid_material_oracles: 32/32
  invalid_oracles_in_final_suite: 0
  ambiguous_oracles: 0
  hardcoded_mutation_ID_logic: false
  verdict: PASS
```
