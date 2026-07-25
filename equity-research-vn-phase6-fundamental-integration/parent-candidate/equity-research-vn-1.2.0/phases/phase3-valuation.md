# Phase 3: Valuation

Bạn là subagent Phase 3. Context tách biệt.

## Input
- `task-state.json` → `phases.phase1_data.result` (financials) + `phases.phase2_fundamental.result` (EPS, BVPS, ROE)
- Sub-skill: `vn-valuation-engine/SKILL.md` + `references/valuation_formulas.md` + `wacc_estimates.md`

## Nhiệm vụ
1. Chọn PP định giá theo ngành (đọc `vn-financial-data-collector/references/sector_insights.md`)
2. Tính 9 PP:
   - PE/PB median 5 năm
   - EV/EBITDA
   - P/CF, P/S
   - DCF (3 kịch bản) — **SANITY CHECK: nếu FCF0 < 0 → flag + dùng EV/EBITDA-implied thay thế**
   - DDM (nếu trả cổ tức)
   - Graham Number
   - Reverse DCF
3. Target price analyst từ `Company.overview()` — tham khảo
4. Hội tụ → median + dải P25-P75 → khuyến nghị

## SANITY CHECK BẮT BUỘC (học từ LC-005)
```
nếu FCF0 < 0:
    DCF trực tiếp = equity âm vô lý → KHÔNG hiển thị giá âm
    dùng EV/EBITDA-implied equity value thay thế
    flag "FCF<0 → DCF alternative method"
nếu valuation target < 0:
    FAIL → không hiển thị, dùng alternative
```

## Output — ghi vào task-state.json
```json
{
  "phases": {
    "phase3_valuation": {
      "status": "completed",
      "result": {
        "pe": ..., "pb": ..., "ev_ebitda": ..., "ps": ..., "pcf": ...,
        "dcf_per_share": ...,
        "dcf_note": "FCF<0, dùng EV/EBITDA-implied" | null,
        "graham_number": ...,
        "converge_median": ...,
        "verdict": "UNDERVALUED|FAIR|OVERVALUED",
        "targets": {"pe_method": ..., "pb_method": ..., "analyst": ..., "dcf_alt": ...}
      }
    }
  }
}
```

## Requirements
- REQ-016: Valuation targets hợp lý (dương, không âm vô lý). DCF với FCF<0 phải flag.

## KHÔNG được
- Hiển thị DCF âm (LC-005 failure) — phải dùng alternative
- Skip sanity check output
