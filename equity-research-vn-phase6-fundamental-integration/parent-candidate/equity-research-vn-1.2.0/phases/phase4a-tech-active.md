# Phase 4a: Technical Analysis — Mode ACTIVE

Bạn là subagent Phase 4a. Context tách biệt.

## Input
- `task-state.json` → `phases.phase1_data.result.files` (price_weekly.json)
- Sub-skill: `vn-technical-analysis/SKILL.md` + `references/vnstock_usage.md` + `indicators.md` + `pattern_detection.md`

## Nhiệm vụ
1. Fetch giá **weekly** 52 tuần qua `Quote.history(interval='1W')`
2. Fetch VNINDEX + VN30 cho Beta/Correlation/Alpha
3. Market cap, số CP, 52W high/low từ `Company.overview()`
4. Tính: MA10/20/50, RSI(14), MACD, Bollinger, Beta
5. Phát hiện patterns (Double Bottom, Channel, Candlestick, Divergence) CHỈ KHI có evidence
6. Output: **Tech Score -6→+6, Verdict (STRONG SELL → STRONG BUY)**, trading strategy 3 kịch bản

## Output — ghi vào task-state.json
```json
{
  "phases": {
    "phase4a_tech_active": {
      "status": "completed",
      "result": {
        "last_close": ..., "ma10": ..., "ma20": ..., "ma50": ...,
        "rsi14": ..., "macd": ..., "beta": ...,
        "tech_score": -5, "verdict": "STRONG SELL",
        "signals": [...],
        "period_high": ..., "period_low": ..., "pct_from_high": ...
      }
    }
  }
}
```

## Requirements
- REQ-005: Technical mode ACTIVE (Tech Score + Verdict)
- **Mode PROFILE là Phase 4b RIÊNG BIỆT** — không làm ở đây

## KHÔNG được
- Mô phỏng data giá — data thật từ vnstock
- Collapse 2 mode thành 1 (Phase 4b sẽ check REQ-006)
- Claim pattern nếu data không show
