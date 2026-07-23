# Phase 1 Baseline Audit — vn-fundamental-analysis

**Date:** 2026-07-23
**Skill:** vn-fundamental-analysis
**Status:** FULLY_PROMPT_DRIVEN (0 deterministic code)

## 1. File inventory

```yaml
files:
  total: 3
  structure:
    - SKILL.md (skill definition + workflow + formulas)
    - agents/openai.yaml (display interface)
    - references/dupont_interpretation.md (6 DuPont patterns + decision tree)
  
  deterministic_code: 0 .py files
  tests: 0
  contracts: 0
  schemas: 0
  registries: 0
```

## 2. Current behavior analysis

```yaml
architecture: FULLY_PROMPT_DRIVEN
  description: |
    Toàn bộ logic tính toán (EPS, BVPS, ROE, ROA, ROS, DuPont, CAGR)
    nằm trong SKILL.md prompt text. Model thực hiện calculation.
    Không có deterministic engine, không có verifier, không có schema.

behaviors:
  - id: BEH-001
    name: EPS calculation
    formula: "EPS = LNST[tỷ] / số CP[tỷ]"
    unit: "đồng/cổ phiếu"
    current_owner: MODEL
    risk: HIGH — sai đơn vị tỷ/tỷ, không split-adjust
    
  - id: BEH-002
    name: BVPS calculation
    formula: "BVPS = VCSH[tỷ] / số CP[tỷ]"
    unit: "đồng/cổ phiếu"
    current_owner: MODEL
    risk: HIGH — sai đơn vị, BVPS > 1,000,000 = red flag
    
  - id: BEH-003
    name: ROE calculation
    formula: "ROE = LNST / VCSH × 100"
    unit: "%"
    current_owner: MODEL
    risk: MEDIUM — straightforward but period mismatch possible
    
  - id: BEH-004
    name: ROA calculation
    formula: "ROA = LNST / Tổng TS × 100"
    unit: "%"
    current_owner: MODEL
    risk: MEDIUM
    
  - id: BEH-005
    name: ROS calculation
    formula: "ROS = LNST / Doanh thu × 100"
    unit: "%"
    current_owner: MODEL
    risk: MEDIUM
    
  - id: BEH-006
    name: DuPont decomposition (3 components)
    formula: "ROE = NPM × Asset Turnover × Equity Multiplier"
    components:
      - NPM = NPAT / Revenue
      - Asset Turnover = Revenue / Total Assets
      - Equity Multiplier = Total Assets / Equity
    current_owner: MODEL
    risk: HIGH — 3 multiplicative components, error compounds
    
  - id: BEH-007
    name: CAGR calculation
    formula: "CAGR = (end/start)^(1/n) - 1"
    current_owner: MODEL
    risk: HIGH — cyclical stock pitfall (năm đáy làm CAGR méo)
    
  - id: BEH-008
    name: Quality verdict
    values: ["TÀI CHÍNH KHỎE", "CẦN THEO DÕI", "NGUY HIỂM"]
    current_owner: MODEL
    risk: MEDIUM — subjective but structured
    
  - id: BEH-009
    name: Split adjustment check (Bẫy 5B)
    description: "Back-calc CP = LNST/EPS, kiểm tra split-adjusted"
    current_owner: MODEL
    risk: CRITICAL — sai split → EPS/BVPS sai → valuation sai
    
  - id: BEH-010
    name: Gross margin calculation
    formula: "Gross margin = (Revenue - COGS) / Revenue × 100"
    current_owner: MODEL
    risk: MEDIUM
    
  - id: BEH-011
    name: Net margin calculation
    formula: "Net margin = NPAT / Revenue × 100"
    current_owner: MODEL
    risk: LOW
```

## 3. Input contract

```yaml
inputs:
  source: vn-financial-data-collector (PRODUCTION_INTEGRATED)
  schema:
    data_years: [int] (e.g., [2021, 2022, 2023, 2024, 2025])
    shares_outstanding_b: [float] (tỷ cổ phiếu)
    income_statement:
      revenue_b_vnd: [float] (tỷ VND)
      net_profit_b_vnd: [float] (tỷ VND, attributable to parent)
    balance_sheet:
      equity_b_vnd: [float] (tỷ VND, owner's equity)
      total_assets_b_vnd: [float] (tỷ VND)
    cash_flow:
      cfo_b_vnd: [float] (tỷ VND, operating cash flow)
  
  unit_convention: "All values in tỷ VND (billions). Shares in tỷ (billions)."
  critical_note: "tỷ / tỷ = đơn vị cơ bản (đồng/cp for EPS/BVPS). KHÔNG nhân ×1000."
  
  missing_data_handling: "Currently MODEL decides — no fail-closed contract"
```

## 4. Output contract

```yaml
outputs:
  format: JSON + text narrative
  schema:
    ratios_by_year:
      - year: int
        eps: float (đồng/cp)
        bvps: float (đồng/cp)
        roe: float (%)
        roa: float (%)
        ros: float (%)
    dupont_2025:
      ni_margin: float (ratio, e.g., 0.098)
      asset_turn: float (ratio)
      leverage: float (ratio)
      roe: float (ratio)
      interpretation: string
    cagr:
      revenue_5y: float (ratio)
      net_profit_5y: float (ratio)
      note: string
    quality_verdict: string
  
  downstream_consumers:
    - vn-valuation-engine (PRODUCTION_INTEGRATED) — uses EPS, BVPS as valuation inputs
    - vn-research-dashboard (NOT YET HARDENED) — renders ratios in HTML
  
  output_validation: NONE (no schema, no verifier)
```

## 5. Formula inventory

```yaml
formulas:
  total: 10
  
  F-001 EPS:
    expression: "EPS = net_profit_b_vnd / shares_outstanding_b"
    inputs: [net_profit_b_vnd, shares_outstanding_b]
    output: đồng/cổ phiếu
    risk: unit confusion (tỷ/tỷ vs nghìn/nghìn)
    
  F-002 BVPS:
    expression: "BVPS = equity_b_vnd / shares_outstanding_b"
    inputs: [equity_b_vnd, shares_outstanding_b]
    output: đồng/cổ phiếu
    risk: unit confusion
    
  F-003 ROE:
    expression: "ROE = (net_profit_b_vnd / equity_b_vnd) × 100"
    inputs: [net_profit_b_vnd, equity_b_vnd]
    output: %
    risk: period mismatch (NPAT full year vs equity year-end)
    
  F-004 ROA:
    expression: "ROA = (net_profit_b_vnd / total_assets_b_vnd) × 100"
    inputs: [net_profit_b_vnd, total_assets_b_vnd]
    output: %
    
  F-005 ROS:
    expression: "ROS = (net_profit_b_vnd / revenue_b_vnd) × 100"
    inputs: [net_profit_b_vnd, revenue_b_vnd]
    output: %
    
  F-006 NPM (DuPont component 1):
    expression: "NPM = net_profit_b_vnd / revenue_b_vnd"
    output: ratio
    
  F-007 Asset Turnover (DuPont component 2):
    expression: "AT = revenue_b_vnd / total_assets_b_vnd"
    output: ratio
    
  F-008 Equity Multiplier (DuPont component 3):
    expression: "EM = total_assets_b_vnd / equity_b_vnd"
    output: ratio
    
  F-009 ROE check (DuPont):
    expression: "ROE_check = NPM × AT × EM"
    must_equal: F-003 ROE (within rounding tolerance)
    risk: multiplicative error compounding
    
  F-010 CAGR:
    expression: "CAGR = (end_value / start_value)^(1/n) - 1"
    inputs: [first_year_value, last_year_value, year_count]
    risk: cyclical distortion, negative start value
    
  F-011 Gross Margin:
    expression: "GM = (revenue - COGS) / revenue × 100"
    note: COGS not in current input schema — needs collector extension or derivation
    
  F-012 Net Margin:
    expression: "NM = NPAT / Revenue × 100"
    same as: F-005 ROS × 100 (identical formula)
```

## 6. Dependencies

```yaml
upstream:
  vn-financial-data-collector:
    status: PRODUCTION_INTEGRATED
    provides: [revenue, net_profit, equity, total_assets, shares_outstanding, cfo]
    risk: data quality (stale, missing periods, wrong units)
  
  equity-research-vn phase1-data:
    provides: financials.json with canonical fields
    risk: split adjustment not applied, period misalignment

downstream:
  vn-valuation-engine:
    status: PRODUCTION_INTEGRATED ACTIVE
    consumes: [EPS, BVPS] as valuation inputs
    risk: WRONG EPS/BVPS → WRONG implied price → WRONG target price
    criticality: HIGH — this is why fundamental must be hardened before valuation quality
    
  vn-research-dashboard:
    status: NOT YET HARDENED
    consumes: [ROE, ROA, ROS, DuPont, CAGR] for chart rendering

cross-formula_risks:
  - EPS uses shares_outstanding; BVPS uses same → if shares wrong, both wrong
  - DuPont ROE_check must equal direct ROE → discrepancy reveals calculation error
  - CAGR for cyclical stocks needs peak-to-peak or trough-to-trough, not end-to-end
  - Gross margin needs COGS which is NOT in current collector schema
```

## 7. Failure surface mapping

```yaml
failure_modes:
  FM-001: UNIT_CONFUSION
    description: "Model computes EPS as tỷ/tỷ but then multiplies ×1000"
    impact: EPS off by 1000×, BVPS off by 1000×
    downstream: valuation engine implied price off by 1000×
    severity: CRITICAL
    current_mitigation: SKILL.md warning text only
    
  FM-002: SPLIT_NOT_ADJUSTED
    description: "Shares outstanding post-split but financials pre-split (or vice versa)"
    impact: EPS/BVPS off by split ratio (e.g., 1.5× for 50% bonus)
    downstream: PE/PB/Graham all wrong
    severity: CRITICAL
    current_mitigation: SKILL.md mentions "Bẫy 5B" but no automated check
    
  FM-003: PERIOD_MISMATCH
    description: "NPAT is full-year but equity is mid-year or different fiscal year"
    impact: ROE/ROA slightly off
    severity: MEDIUM
    current_mitigation: none
    
  FM-004: DUPONT_DECOMPOSITION_ERROR
    description: "NPM × AT × EM ≠ ROE (rounding or calculation error)"
    impact: ROE quality verdict wrong
    severity: HIGH
    current_mitigation: none (no automated consistency check)
    
  FM-005: CYCLICAL_CAGR_DISTORTION
    description: "End-to-end CAGR misleading for cyclical stocks"
    impact: Growth assessment wrong → wrong valuation multiple
    severity: HIGH
    current_mitigation: SKILL.md text warning, no automated peak/trough detection
    
  FM-006: MISSING_DATA_SILENT_ZERO
    description: "Missing financial field silently replaced with 0"
    impact: Division by zero, or EPS=0 which blocks valuation
    severity: CRITICAL
    current_mitigation: none
    
  FM-007: NEGATIVE_EQUITY
    description: "Equity < 0 (insolvent company)"
    impact: BVPS negative, ROE meaningless, DuPont breaks
    severity: HIGH
    current_mitigation: none
    
  FM-008: ATTRIBUTABLE_VS_TOTAL_NPAT
    description: "Using total NPAT instead of NPAT attributable to parent"
    impact: EPS too high (includes minority interest)
    severity: HIGH
    current_mitigation: none
```

## 8. Parent integration analysis

```yaml
parent_requirements:
  REQ-003:
    text: "Audit split (Bẫy 5B) trước khi tính EPS/PE/PB"
    current_ownership: MODEL (prompt-driven)
    needs: deterministic split check from collector data
    
  REQ-013:
    text: "3 Special Insights riêng biệt, mỗi cái ≥500 chars"
    related: fundamental insights feed into special insights
    current_ownership: MODEL
    
  REQ-014:
    text: "Bull + Bear case cân bằng"
    method: section_content_check
    related: DuPont quality verdict informs bull/bear
    
  REQ-015:
    text: "Bull + Bear case cân bằng"
    method: artifact_check
    
  REQ-022:
    text: "Revenue/NPATMI/EPS trong report KHỚP data files (±5%)"
    criticality: HIGH — fundamental output must match collector data
    current_ownership: parent verifier checks AFTER model generates

parent_compensation:
  - parent verifier checks REQ-022 (data accuracy ±5%)
  - parent verifier checks REQ-003 (split adjustment mention)
  - BUT: parent verifier does NOT check DuPont consistency (NPM×AT×EM=ROE)
  - BUT: parent verifier does NOT check CAGR cyclical adjustment
  - BUT: parent verifier does NOT check unit sanity (BVPS range 5K-50K)
```

## 9. Release blockers (standalone)

```yaml
blockers:
  - id: BLK-001
    text: "No deterministic calculation engine — all formulas in prompt"
    severity: CRITICAL
    
  - id: BLK-002
    text: "No output schema validation"
    severity: CRITICAL
    
  - id: BLK-003
    text: "No split adjustment verification"
    severity: CRITICAL
    
  - id: BLK-004
    text: "No DuPont consistency check (NPM×AT×EM must equal ROE)"
    severity: HIGH
    
  - id: BLK-005
    text: "No unit sanity enforcement (BVPS range, EPS range)"
    severity: HIGH
    
  - id: BLK-006
    text: "No fail-closed for missing data"
    severity: HIGH
    
  - id: BLK-007
    text: "No CAGR cyclical adjustment logic"
    severity: MEDIUM
    
  - id: BLK-008
    text: "No negative equity handling"
    severity: MEDIUM
```

## 10. Risks to downstream (vn-valuation-engine)

```yaml
critical_risks_to_valuation:
  - "WRONG EPS → wrong PE implied price → wrong target price"
  - "WRONG BVPS → wrong PB implied price → wrong target price"
  - "MISSING EPS/BVPS → valuation engine INPUT_INCOMPLETE → DCF skipped"
  - "SPLIT NOT ADJUSTED → EPS/BVPS off by split ratio → ALL methods wrong"
  - "UNIT CONFUSION → EPS off by 1000× → implied price nonsensical"
  
mitigation_urgency: HIGH
  rationale: |
    vn-valuation-engine is PRODUCTION_INTEGRATED ACTIVE.
    It trusts EPS/BVPS from fundamental analysis.
    If fundamental is wrong, valuation produces wrong target prices
    that flow into equity-research-vn reports.
```

## 11. Comparison with vn-valuation-engine Phase 1

```yaml
similarity: HIGH
  - Both started FULLY_PROMPT_DRIVEN
  - Both have formulas in SKILL.md text
  - Both have 0 deterministic code
  - Both feed downstream consumers
  - Both have unit confusion risk (tỷ VND)
  
differences:
  - fundamental has FEWER formulas (10 vs 10 but simpler — ratios, not valuation methods)
  - fundamental has NO equity bridge complexity
  - fundamental has NO benchmark/peer selection
  - fundamental DuPont is multiplicative (3 components) vs valuation DCF (multi-step PV)
  - fundamental risk is MORE concentrated: EPS/BVPS errors propagate to ALL valuation methods
  
expected_hardening_effort: LOWER than valuation-engine
  - Fewer formulas
  - No bridge/applicability complexity
  - Input from collector is already PRODUCTION_INTEGRATED (clean data)
  - Can reuse patterns from valuation-engine (error codes, schema, verifier)
```

## 12. Recommended Phase 2-4 scope

```yaml
phase_2_contracts:
  - input schema (from collector)
  - output schema (ratios + DuPont + CAGR)
  - formula registry (10 formulas)
  - error codes (unit confusion, missing data, negative equity, split mismatch)
  - unit policy (tỷ VND convention, BVPS range 5K-50K, EPS range 100-50K)
  
phase_3_design:
  - deterministic engines: ratio_engine, dupont_engine, cagr_engine
  - unit sanity checker
  - split adjustment verifier
  - DuPont consistency checker
  - fail-closed missing data handler
  
phase_4_implementation:
  - ~800-1000 LOC (simpler than valuation-engine's ~2500)
  - 30-40 unit tests
  - synthetic fixtures (clean + mutations)
  - independent verifier
```

## Summary

```yaml
phase_1_audit_result:
  current_state: FULLY_PROMPT_DRIVEN
  deterministic_code: 0
  formulas: 10 (all in prompt text)
  release_blockers: 8 (3 CRITICAL)
  downstream_risk: HIGH (valuation engine depends on EPS/BVPS)
  
  recommended_next: Phase 2 (contract extraction)
  estimated_effort: 2-3 sessions (vs 5+ for valuation-engine)
  
  key_advantage: |
    vn-valuation-engine hardening journey created reusable patterns:
    - error codes structure
    - schema validation approach
    - context envelope architecture
    - mutation testing methodology
    These can be adapted for fundamental-analysis with less effort.
```
