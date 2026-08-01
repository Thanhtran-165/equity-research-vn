# Prompt cho DeepSeek — Review gap patterns trong equity-research-vn

## Copy toàn bộ nội dung dưới đây gửi cho DeepSeek

---

Tôi đang xây dựng một hệ thống AI skill gọi là `equity-research-vn` — pipeline 8 phases phân tích cổ phiếu Việt Nam (thu thập data → phân tích cơ bản → định giá → phân tích kỹ thuật → bản tin → dashboard HTML). Hệ thống có một **independent verifier** (Python) kiểm tra 31 requirements sau khi agent tạo output.

Tôi vừa chạy thử pipeline trên ticker CTD (Coteccons Construction) và phát hiện **10 gap** — đây là các vấn đề mà verifier hiện tại KHÔNG BẮT ĐƯỢC, hoặc skill spec chưa quy định. Tôi muốn bạn review xem **còn loại vấn đề tương tự nào nữa không**.

### 10 gap đã phát hiện

**Nhóm A — Verifier scope hẹp (không check):**
1. **Peer data bịa**: Agent tự ghi P/B, CAGR, market_cap của công ty cùng ngành (HBC, DXG...) từ bộ nhớ, không fetch API. DXG đã hủy niêm yết → data sai. Verifier REQ-022 chỉ check data ticker chính, không check peer.
2. **Số liệu không cite source**: 81 số liệu định lượng (VND, %, multiples) trong narrative không có nguồn cite. Verifier không yêu cầu cite source cho mỗi số.
3. **Key metrics không cite**: PE 8x, CAGR 35% lặp nhiều lần nhưng không ghi "theo BCTC" hay "tính từ EPS".
4. **Drawdown bịa**: Agent ghi "CTD có thể giảm 30-50%" — không có data drawdown thật từ price history.
5. **Percentages trôi nổi**: 0.27%, 2.54%, 12.5% xuất hiện không có context/source.

**Nhóm B — Skill spec thiếu:**
6. **Investment amount hardcode**: Agent tự chọn 800 triệu VND cho section "góc nhìn khoản đầu tư" — không hỏi user quy mô vốn.
7. **API fallback thiếu**: Pipeline chỉ thử 1 nguồn data (VCI). Nếu VCI down → chết, không có fallback.
8. **Fiscal year giả định**: Skill giả định tất cả DN dùng dương lịch. Ngân hàng (VCB, BID) có thể khác.

**Nhóm C — Vận hành thủ công:**
9. **Price tự điền**: Khi tạo source pack thủ công, giá 62,000 được ghi tay thay vì fetch real-time.
10. **Source pack thiếu field**: fundamental_sponsor.json thiếu equity=0 → PB=null → REQ-025 FAIL.

### 3 REQ mới đã thêm (chưa implement verifier logic)
- REQ-029: source_citation_check — mọi số liệu phải cite nguồn
- REQ-030: price_source_check — giá phải fetch API
- REQ-031: drawdown_source_check — drawdown phải có data thật

### Cấu trúc pipeline
```
Phase 0: Sponsor detection (check API)
Phase 1: Data collection (fetch BCTC 5 năm + giá + peer)
Phase 2: Fundamental analysis (ROE, DuPont, CAGR)
Phase 3: Valuation (9 phương pháp: PE/PB/EV-EBITDA/P-CF/DCF/Reverse DCF/DDM/Graham/DuPont)
Phase 4a: Technical ACTIVE (MA/RSI/MACD/Bollinger, Tech Score)
Phase 4b: Technical PROFILE (28 blocks: volatility, VPCI/OBV/CMF, Wyckoff, archetype)
Phase 5: News digest (4 nhóm tin, sentiment)
Phase 6: Dashboard build (22 sections HTML, 13 charts)
Phase 7: Verify + deploy
```

### Verifier hiện tại (31 REQ)
- REQ-001/002: Sponsor import + data ≥20 kỳ
- REQ-003/004: Split audit + data thật
- REQ-005-008: Section content + news
- REQ-009-014: Structure (sections, charts, refs, tokens, depth)
- REQ-015-018: Data quality + references
- REQ-019-020: JS syntax + div balance
- REQ-021: No deploy if FAIL
- REQ-022-024: Data accuracy (revenue, balance sheet, capex)
- REQ-025-026: Valuation recompute + provenance
- REQ-027: External claim flagging
- REQ-028: Chart render readiness
- REQ-029-031: Source citation + price freshness + drawdown (MỚI)

### Yêu cầu

Dựa vào 10 gap trên và cấu trúc pipeline, hãy phân tích:

1. **Còn loại gap nào tương tự không?** — đặc biệt các pattern mà agent có thể "lách" verifier hiện tại
2. **Nhóm A (verifier scope):** Ngoài peer data, citation, drawdown — còn data nào agent có thể bịa mà verifier không check?
3. **Nhóm B (spec thiếu):** Ngoài investment amount, API fallback, fiscal year — còn input/config nào pipeline giả định mà không hỏi?
4. **Narrative quality:** Agent có thể tạo narrative "nghe có vẻ đúng" nhưng thực ra không có basis — làm sao bắt?
5. **Cross-section consistency:** Số liệu ở section 3 (valuation PE=8x) có khớp với section 9 (peer comparison) không? Có REQ nào check cross-section consistency không?
6. **Temporal consistency:** Số liệu "năm 2025" ở section 2 có khớp với "FY2025" ở section 3 không?
7. **Đề xuất REQ mới** nếu cần (format: REQ-032, text, method, priority)

Hãy liệt kê từng gap tìm được, kèm:
- Loại gap (verifier scope / spec thiếu / narrative quality / consistency)
- Mức nghiêm trọng (critical / high / medium)
- Đề xuất REQ hoặc method check
- Ví dụ cụ thể (nếu có)
