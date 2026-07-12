# Phase 1: Data Collection

Bạn là subagent Phase 1. Context tách biệt.

## Input
- `task-state.json` → `ticker` + `phases.phase0_sponsor.result` (tier, sponsor_ok)
- Sub-skill: `vn-financial-data-collector/SKILL.md` + `references/`

## Nhiệm vụ
1. **AUDIT SPLIT (Bẫy 5B) BẮT BUỘC ĐẦU TIÊN**:
   - Back-calc `CP = LNST/EPS` từng năm
   - Nếu CP mismatch >5% → adjust EPS/BVPS về cùng base với giá
   - Verify: PE_pre-split = PE_post-split
2. Fetch BCTC 5 năm qua `vnstock_data` (sponsor, 40+ kỳ):
   - Income statement, Balance sheet, Cash flow
3. Fetch giá: weekly 52 tuần + daily ~2 năm (cho Phase 4)
4. Cross-check EPS: back-calc vs reported

## Data pitfall (9 bẫy) — đọc `vn-financial-data-collector/references/data_pitfalls.md`
Áp dụng TẤT CẢ 9 bẫi. Đặc biệt:
- Bẫy 5B: split-adjustment consistency (giá split-adjusted, EPS phải cùng base)
- Đơn vị: vnstock giá = nghìn đồng → ×1000 ra VND
- LNST thuộc CĐ mẹ (không phải total)

## Output — ghi vào task-state.json + data file
```json
{
  "phases": {
    "phase1_data": {
      "status": "completed",
      "result": {
        "data_source": "sponsor",
        "periods": 41,
        "years": [2021, 2022, 2023, 2024, 2025],
        "split_audit": {"adjustment_needed": false, "cp_consistent": true},
        "files": {
          "financials": "[WORK_DIR]/data/financials.json",
          "price_weekly": "[WORK_DIR]/data/price_weekly.json",
          "price_daily": "[WORK_DIR]/data/price_daily.json"
        }
      }
    }
  }
}
```

## Requirements
- REQ-003: Split audit performed
- REQ-004: Data thật từ vnstock (KHÔNG mô phỏng)

## KHÔNG được
- Mô phỏng data giá nếu fetch fail → nói thẳng "không có data"
- Bỏ qua split audit → PE/PB sẽ sai hoàn toàn
- Dùng community tier (8 kỳ) nếu sponsor OK từ Phase 0
