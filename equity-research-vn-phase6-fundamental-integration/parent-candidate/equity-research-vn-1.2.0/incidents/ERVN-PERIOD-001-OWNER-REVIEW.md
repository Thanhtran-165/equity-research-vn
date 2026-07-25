# ERVN-PERIOD-001 — OWNER REVIEW PACKET
**Status:** Architecture proven; **PAUSED** awaiting owner design review before requal continuation
**Date:** 2026-07-18

This is the navigation document for the owner's design review. All artifacts
referenced are on local disk under `~/.zcode/skills/equity-research-vn/incidents/`.

---

## TL;DR

- **Defect confirmed:** `build_data_contract.py` v1.0.0 inverts period labels (oldest value → latest period).
- **Forensic scope:** 34 tickers, 21 sectors, 475 (period,value) pairs checked. **376/475 (79.2%) inverted.**
- **Classification:** Branch A — LATENT_RELEASE_DEFECT (release-time CSVs byte-identical to current).
- **Verifier gap proven:** v0.14.9 returns PASS on FPT qualification artifact with 12/15 pairs inverted.
- **Hotfix architecture:** resolver + gate + patched builder implemented and validated.
- **No production damage:** v1.0.0 tag untouched; sponsor_csv_path FAIL_CLOSED; artifacts suspended.

---

## Owner decisions confirmed this session

| Decision | Choice | Rationale |
|---|---|---|
| Collector `MATURITY.json` revision | integration_status=BLOCKED, parent_integration_regression=FAIL_PARENT_SIDE | Build success ≠ data correctness |
| ROBUST path for collector | DEFERRED until ERVN-PERIOD-001 closes | Active parent incident |
| Hotfix proceeding | Architecture completion only; **pause before requal runs** | Owner reviews design first |
| Source pack enrichment (next session) | Generate via vnstock (10 calls) | Authoritative period metadata |

---

## Recommended owner review sequence

### Step 1 — Read the incident ticket (10 min)
**File:** `ERVN-PERIOD-001.md`

Sections to focus on:
- §1 Defect (the `years_asc[4-i]` logic)
- §4b Forensic audit (Branch A classification evidence)
- §6 Required remediation (architectural fix contract)

### Step 2 — Skim the forensic summary (5 min)
**File:** `ERVN-PERIOD-001-forensic-summary.json`

Key numbers:
- `tickers_scanned: 34`
- `total_period_value_pairs: 475`
- `inverted_period_assigned: 376` (79.2%)
- `correctly_period_assigned: 94` (19.8%, false-positive matches)
- `per_sector`: every sector shows ~80% inversion rate

### Step 3 — Skim the hotfix design (10 min)
**File:** `ERVN-PERIOD-001-hotfix-design.md`

Key sections:
- §4 Period-key resolver design (3 strategies)
- §5 period_integrity_gate (6 sub-checks)
- §6 Verifier augmentation (REQ-PERIOD-INTEGRITY)
- §9 Open questions for owner (3 decisions)

### Step 4 — Inspect validation matrix (5 min)
**File:** this packet, §"Component validation matrix" below

Confirms: resolver PASS on CTD (15/15), gate PASS clean/FAIL inverted, builder produces correct ascending contract on CTD, fail-closed on Phase 6E packs.

### Step 5 — Decide on the 3 open questions

The design doc §9 lists 3 questions. Owner's vnstock answer covers question 1
(Strategy 1 will be primary; vnstock regenerates fundamental_sponsor.json).
Owner still needs to decide:

- **REQ-PERIOD-INTEGRITY severity:** critical (blocks deploy) or high (warning)?
  - **Recommendation: critical.** Matches incident severity.
- **Historical artifact remediation:** document as known-bad, re-build with v1.0.1, or side-by-side?
  - **Recommendation: document as known-bad.** Preserves evidence.

---

## Component validation matrix

| Component | File | Validation |
|---|---|---|
| `period_key_resolver.py` | `v1.0.1-candidate/runner/period_key_resolver.py` | Strategy 1 validated on CTD: 15/15 (period, value) pairs MATCH. Fail-closed on FPT pack (no metadata): POSITIONAL_ONLY_ASSUMPTION. |
| `period_integrity_gate.py` | `v1.0.1-candidate/runner/period_integrity_gate.py` | PASS on clean CTD contract: 6/6 sub-checks pass, 6/6 fields 5/5 periods match. FAIL on inverted v1.0.0 output: all 6 fields 0/5 match. Correctly handles abs-normalized capex. |
| `build_data_contract.py` v1.0.1 | `v1.0.1-candidate/runner/build_data_contract.py` | Produces CLEAN contract on CTD (5/6 fields ascending correctly). FAIL_CLOSED exit 2 on FPT Phase 6E pack. `_provenance.period_resolution` records method + confidence. |
| Verifier gap proof | `ERVN-PERIOD-001-verifier-gap-test.py` | Confirms v0.14.9 returns exit 0 on FPT qualification artifact (12/15 pairs inverted). Real-world proof, not synthetic. |

---

## Hash registry (integrity)

| Artifact | sha256 (first 32 hex) |
|---|---|
| `period_key_resolver.py` | `6cda6d50d46f076c4b01f18eb9a785ce` |
| `period_integrity_gate.py` | `6d328b7605eedb3fea88d52ca84954d2` |
| `build_data_contract.py v1.0.1` | `502d12c15901a03a888a7306b1c6d310` |
| `build_data_contract.py v1.0.0` (untouched) | `a322abc35884d2d542c6259303ae33e8` (matches release manifest) |
| `independent_verifier.py v0.14.9` (untouched) | `c155d5cb4c705adce9787fa6643c0101` (matches release manifest) |
| RELEASE-MANIFEST.json v1.0.0 | `9f308097de506645b990306feb570d5a` (untouched) |

---

## What this session did NOT touch

- `agent-eval/runner/build_data_contract.py` (the v1.0.0 file — untouched)
- `agent-eval/runner/agent_runner.py` (untouched)
- `equity-research-vn/scripts/independent_verifier.py` (untouched)
- `equity-research-vn/requirements.yaml` (untouched)
- `agent-eval/cohort-c/production-release-v1.0.0/*` (immutable release artifacts)
- `agent-eval/cohort-c/cohort-c-prime/*` (frozen qualification artifacts)
- `vn-financial-data-collector/*` (collector correct; not the defect)

All new code lives under `~/.zcode/skills/equity-research-vn/incidents/v1.0.1-candidate/`. No production path modified.

---

## Open items for next session (after owner approval)

1. Generate `fundamental_sponsor.json` for 10 Phase 6E source packs via vnstock API (10 calls).
2. Augment `independent_verifier.py` (or create `independent_verifier_v0.14.10.py`) with REQ-PERIOD-INTEGRITY that invokes `period_integrity_gate.evaluate()`.
3. Build regression fixtures: clean + inverted synthetic artifacts (proves gate distinguishes them as a unit test).
4. **Requal path** (per design §8):
   - Re-run forensic audit on v1.0.1 outputs → expect 0/475 inverted
   - 12 targeted hotfix runs (6 sector archetypes × 2 runs)
   - Shadow requalification (5+ tickers, fresh sectors, full agent_runner)
   - Short operational soak
   - Rollback drill (intentionally inject bad candidate; verify gate detects)
5. Close ERVN-PERIOD-001, restore collector integration_maturity, declare v1.0.1 PRODUCTION_READY.

Estimated next-session effort: 3-4 hours of focused work.

---

## Owner sign-off block

```
[ ] Design approved as written (proceed with §4-§8)
[ ] Design approved with modifications: ___________________________
[ ] REQ-PERIOD-INTEGRITY severity: critical / high (circle one)
[ ] Historical artifact handling: document-as-known-bad / rebuild / side-by-side (circle one)
[ ] Requal depth: full (12 targeted + shadow + soak + rollback) / abbreviated (targeted only)
[ ] Other notes: _________________________________________________
```
