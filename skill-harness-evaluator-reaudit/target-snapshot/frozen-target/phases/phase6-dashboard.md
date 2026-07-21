# Phase 6: Dashboard Build (PATCHED — output-contract lock)

Bạn là subagent Phase 6. Context tách biệt.

## OUTPUT CONTRACT — KHÔNG THƯƠNG LƯỢNG (PATCH LAYER 1)

Đầu ra duy nhất được chấp nhận là **một tài liệu HTML hoàn chỉnh**. Cụ thể:

- Bắt đầu bằng `<!DOCTYPE html>` (không có ký tự nào trước nó — không leading space, không markdown fence, không lời dẫn).
- Kết thúc bằng `</html>`.
- **KHÔNG** viết Markdown (no `#`, no ```` ``` ````).
- **KHÔNG** viết lời dẫn, giải thích, narration (no "I'll build...", no "Tôi sẽ...", no "Step 1:").
- **KHÔNG** đặt HTML trong code fence.
- **KHÔNG** mô tả việc bạn sẽ làm gì — **LÀM nó** và trả về kết quả.

Nếu không thể tạo HTML hợp lệ, trả đúng chuỗi: `PHASE6_STRUCTURED_FAILURE: <lý do cụ thể>`. **Không thay bằng narration.**

## TẠI SAO PATCH NÀY

Bản prompt cũ yêu cầu `cp template` + `str.replace` — nhưng bạn (subagent) không có kênh tool/bash. Do đó các lần chạy trước đã **narrate** thay vì xuất artifact (5/5 FAIL, recall 39.3%). Patch này inline template + data để bạn fill trực tiếp và trả về HTML hoàn chỉnh trong một response.

## Input
- `task-state.json` → TẤT CẢ phase results (phase0→5)
- Template (INLINE bên dưới) — 22 sections canonical + 38 tokens
- Data từ task-state.json phases

## Nhiệm vụ

Đọc template inline bên dưới. Fill mỗi `{{TOKEN}}` với nội dung tương ứng từ task-state.json. Trả về **toàn bộ template đã fill** — từ `<!DOCTYPE html>` đến `</html>` — không thêm gì, không bớt gì.

### Template inline (FILL TỪNG TOKEN, giữ nguyên structure)

Dưới đây là template gốc. Thay mỗi `{{TOKEN}}` bằng nội dung thật. **Giữ nguyên tất cả phần HTML/JS/CSS không phải token.**

```
__TEMPLATE_INLINE_PLACEHOLDER__
```

(Separator trên là đánh dấu; runner sẽ inject template thực vào đây trước khi gửi prompt cho model.)

### Token fill rules
- `{{SEC_XXX_HTML}}` — HTML content cho section đó (≥ min chars per spec; bao gồm canvas elements)
- Canvas ids bắt buộc: `chartHistRev, chartBSDt, chartHistCash, chartPeerScatter, chartProfileDD, chartProfileDist, chartReturns, chartSegMix, chartTechPrice, chartTechRSI, chartThesisCapex, chartThesisRPO, chartValPE`
- `{{CHART_DATA_JS}}` — `const DATA = {...}` với ticker data (xem key list bên dưới)
- `{{TICKER}}`, `{{COMPANY_NAME}}` — từ overview

### Content depth (≥ min chars mỗi section)
| Section | Min |
|---|---|
| SEC_HERO | 100 | SEC_EXEC | 500 | SEC_BIZ | 600 | SEC_INDUSTRY | 500 |
| SEC_HISTORY | 500 | SEC_SEGMENT | 400 | SEC_THESIS | 600 | SEC_VALUATION | 400 |
| SEC_PEER | 400 | SEC_BS | 300 | SEC_RISK | 500 | SEC_33K | 300 |
| SEC_SCENARIO | 300 | SEC_CHECKLIST | 300 | SEC_INSIGHT_1/2/3 | 600 each |
| SEC_TECH | 400 | SEC_TECH_PROFILE | 400 | SEC_ANALYST | 200 | SEC_GLOSSARY | 300 | SEC_SOURCE | 200 |

### External claims & provenance (REQ-027)
- **Prefer values from the supplied DATA object and company_profile over internal knowledge.**
- **Financial/valuation numbers** (revenue, profit, EPS, PE, PB, capex): must come from the DATA object or source files — 100% provenance required.
- **Widely-known company descriptors** (market share, store count, factories, employees): acceptable as general background IF qualified with "~", "khoảng", "ước tính", or "theo công bố" — NOT presented as sourced fact.
- If a quantitative business fact is not in the source pack and you cannot qualify it, **omit it** rather than present it as confirmed.
- Example: `~38% thị phần (theo công bố ngành)` is acceptable; `38% thị phần` without qualifier is not.

### Keywords bắt buộc (verifier check)
- "split-adjusted" / "Bẫy 5B" / "cross-check" (REQ-003, anywhere)
- "sentiment" / "tích cực" / "tiêu cực" (REQ-008)
- "ước tính" / "limitation" / "honest" (REQ-017)

### DATA object keys (bắt buộc đầy đủ)
`ticker, years, revenue, netProfit, grossProfit, cfo, capex, inventory, invGrowth, eps, roe, bvps, equity, totalAssets, peHist, pbHist, pe5med, pe5avg, pe, peers{data:[{label,x,y,r,own}]}, peerLabel, peerPBMin, peerPBMax, peerYLabel, peerYMax, tech52wLow, techMA50val, techRSI, techWeeks, techPrice, techMA10/20/50, segMix{labels,values}`

## REMINDER LẦN CUỐI
Trả về HTML. Chỉ HTML. Từ `<!DOCTYPE html>` đến `</html>`. Không narration.

## Requirements (verifier sẽ check trên artifact)
- REQ-009: 22 canonical sections
- REQ-010: 0 unreplaced tokens
- REQ-011: Canvas có height-wrapper
- REQ-012: Charts ≥10, Sections ≥20, Refs ≥10
- REQ-013: Content depth ≥200 chars/section
- REQ-014: 3 insights (sec-insight-1/2/3), mỗi cái ≥500 chars
- REQ-015: Bull + Bear cân bằng
- REQ-016: Valuation targets dương
- REQ-017: Flag honest về data limitation
- REQ-018: Sources ≥10 numbered citations
- REQ-019: JS syntax OK
- REQ-020: Div balance
