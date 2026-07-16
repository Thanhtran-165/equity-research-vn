# Content Diagnosis — Step 1: REQ-022→026 + REQ-012/018 Failure Classification

From 5 Cohort A′ artifacts. **All 5 runs fail identically** — σ=0 on the failure pattern. This is a **systematic data-contract defect**, not model variance.

## Finding 1: REQ-022→026 — `data file not found` (NOT wrong values)

```json
{"error": "data file not found: .../run-001/data/financials.json"}
```

The verifier's `data_accuracy_check` (REQ-022→026) reads ground-truth from:
- `data/financials.json` (revenue, npatmi, eps per-year)
- `data/balance_sheet.json` (Total Assets, Equity)
- `data/cash_flow.json` (capex)

These JSON files **do not exist** in the workspace. The source-pack provides raw CSVs (`income_statement_sponsor.csv`, `balance_sheet_sponsor.csv`, `cash_flow_sponsor.csv`) flat in the workspace root, NOT as the JSON format under `data/` that the verifier expects.

**Root cause:** Phases 1-2 are supposed to collect + structure data into these JSON files. But in the agent-eval pipeline, phases are inference-only (no file-write tool channel). The agent narrates "I'll collect data..." but can't actually write `data/financials.json`. Same capability-mismatch as the pre-patch Phase-6 narration, one layer earlier.

**Classification:** `cross_phase_data_binding_failure` — exactly your hypothesis. The data contract between phases is broken because no phase actually produces the JSON ground-truth files.

**Implication:** REQ-022→026 **cannot pass regardless of model quality** until the data pipeline produces the expected JSON format. This is a **fixture/contract gap**, not an agent-adherence issue.

## Finding 2: REQ-012/018 — `refs=0` (completion gap, not structural)

```yaml
charts: 13 (≥10 ✅)
sections: 22 (≥20 ✅)
refs: 0 (≥10 ❌)
```

The agent fills the template structure correctly (13 charts, 22 sections — both exceed thresholds) but produces **zero numbered references** (`id="ref-N"`). The template has `{{SEC_SOURCE_HTML}}` expecting `≥10 numbered citations`, but the agent fills it with unstructured "source" text instead of `<ol><li id="ref-1">...</li></ol>`.

**Classification:** `completion_contract_gap` — structure is there, mandatory content element is not filled. The prompt's source-section spec needs to demand `id="ref-N"` markup explicitly.

## Failure pattern consistency (5/5 identical)

| REQ | Run-001 | Run-002 | Run-003 | Run-004 | Run-005 | Pattern |
|---|---|---|---|---|---|---|
| REQ-022 | data file not found | same | same | same | same | **systematic** |
| REQ-023 | data file not found | same | same | same | same | **systematic** |
| REQ-024 | data file not found | same | same | same | same | **systematic** |
| REQ-025 | data file not found | same | same | same | same | **systematic** |
| REQ-026 | data file not found | same | same | same | same | **systematic** |
| REQ-012 | refs=0 | refs=0 | refs=0 | refs=0 | refs=0 | **systematic** |
| REQ-018 | refs=0 | refs=0 | refs=0 | refs=0 | refs=0 | **systematic** |

σ=0 across all 5 runs. This is a **design defect** (data contract + completion spec), not model variance.

## Architecture fix design (owner Steps 2-4)

### Step 2: machine-readable data contract
Build a `verified-dashboard-data.json` from the source-pack's raw CSVs (deterministic script, not model). This becomes the single verified data source:

```yaml
dashboard_data:
  company: "CTD (Coteccons Construction)"
  periods: [2021, 2022, 2023, 2024, 2025]
  financials:
    revenue: [...]      # from income_statement_sponsor.csv
    net_profit: [...]   # from income_statement_sponsor.csv
    eps: [...]          # computed
    total_assets: [...] # from balance_sheet_sponsor.csv
    equity: [...]
  valuation:
    pe: ...
    pb: ...
  capex: [...]          # from cash_flow_sponsor.csv
  references: [...]     # ≥10 numbered citations from news.csv + source URLs
provenance:
  source_file: ...
  unit: "tỷ VND"
  extraction_status: "verified"
```

Also write this in the verifier-expected format (`data/financials.json`, `data/balance_sheet.json`, `data/cash_flow.json`) so REQ-022→026 can actually run.

### Step 3: separate "compute data" from "render dashboard"
```
source-pack CSVs → deterministic build_data_contract.py → verified-dashboard-data.json + data/*.json
→ Phase 6 receives verified-dashboard-data.json INLINE (like template) → renders HTML from it
→ Phase 6 is forbidden from inventing numbers; it only renders the contract
```

### Step 4: phase-local content gate
After Phase-6 preflight (HTML structure), add content checks:
- DATA values match verified-dashboard-data.json
- refs count ≥10 (`id="ref-N"`)
- valuation recomputed matches
Specific feedback on mismatch → retry Phase 6 only.

## What this means for the next patch cycle
The fix is **not a prompt change** — it's a **pipeline architecture change**: add a deterministic data-contract builder between source-pack and Phase 6, inject the contract into the Phase-6 prompt (like the template), and add a content gate. This moves REQ-022→026 from "impossible" (data files don't exist) to "verifiable" (data files present, agent renders from contract).
