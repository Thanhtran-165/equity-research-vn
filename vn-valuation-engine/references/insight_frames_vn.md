# Insight Frames VN — Thư viện frame + archetype router cho cổ phiếu Việt Nam

> ⭐ **MỚI v2.2.0** — học từ us-equity-research `references/insight_frames.md`, adapt cho đặc thù VN.
> Đọc BẮT BUỘC ở Phase "Section 8 Special Insights" của vn-research-dashboard.
> Thay thế "Section 8 Bull+Bear generic" bằng frame library động theo ngành.

## A. Archetype Router (ngành VN → default frames)

| Ngành (example tickers) | Default frames | KPI đặc thù |
|---|---|---|
| **Ngân hàng** (VCB, BID, CTG, TCB, MBB, ACB, VPB, HDB) | F1 NIM moat + F2 credit quality + F3 CASA funding | NIM, NPL %, CASA %, Tier-2, LnD |
| **Dầu khí / Lọc hóa dầu** (BSR, PVC, PVD, PLX, GAS) | F4 crack spread moat + F5 chu kỳ oil + F6 counterparty NOC | Crack spread, Brent vs WTI, capacity utilization |
| **Bất động sản** (VIC, VHM, NVL, MGR, KDH, DIG) | F7 NAV / land bank + F8 chu kỳ BĐS + F9 counterparty (off-plan) | NAV, land bank (ha), inventory turnover, pre-sales |
| **Thép** (HPG, HSG, NKG, TLH) | F5 chu kỳ giá HRC + F10 cost moat (quặng sắt) + F11 capacity | HRC price, capacity utilization, quặng sắt cost |
| **Bán lẻ / Tiêu dùng** (MWG, PNJ, FRT, DGW) | F12 same-store-sales + F13 ecosystem (thành viên) + F14 margin | SSSG, gross margin, store count, member program |
| **Công nghệ** (FPT, CMG, ELC) | F15 outsourcing moat + F16 government contracts + F17 chuyển đổi số | Revenue per employee, contract backlog, R&D % |
| **Chứng khoán** (SSI, VND, VCI, HCM, SHS) | F18 market-share broker + F19 margin lending + F20 self-trading risk | Market share, margin loan, self-trading P&L |
| **Bảo hiểm** (BVH, MIG, BIC) | F21 combined ratio + F22 investment yield + F23 bancassurance | Combined ratio, investment yield, bancassurance % |
| **Điện / Năng lượng** (POW, GEG, EVN, BII) | F24 EVN offtake + F25 capacity factor + F26 fuel cost | Capacity factor, tariff, fuel cost, EVN receivable |
| **Cảng / Logistics** (GMD, PHP, VSC, HAFF) | F27 throughput moat + F28 geographic advantage + F29 tariff | TEU, throughput, tariff/container |
| **Viễn thông** (VNM, FPT, Viettel-private) | F30 ARPU + F31 spectrum moat + F32 infrastructure sharing | ARPU, subscriber, market share |
| **Y tế** (HMH, IDC, DMC) | F33 bed capacity + F34 doctor retention + F35 insurance billing | Bed occupancy, doctor retention, insurance % |

**Edge cases:**
- **Conglomerate** (VIC, THD): hỏi user focus sub-business
- **Ngành mới/không match**: default F5 (chu kỳ) + F2 (margin) — 2 frame tổng quát nhất
- **Cổ phiếu chuyển mình** (vd từ real estate → công nghệ): dùng thesis keyword thay vì sector

---

## B. 35 Insight Frames (thư viện skeleton)

### Frame 1 — NIM moat (ngân hàng)
**Trigger**: ngân hàng có NIM cao/cao hơn peer.
**Câu hỏi**: NIM cao đến từ CASA hay risk pricing? Bền không?
**Honest correction**: NIM cao có thể do nhận nợ xấu (risk premium) → NPL tăng theo. CASA bền hơn risk pricing.

### Frame 2 — Credit quality (ngân hàng)
**Trigger**: NPL %, coverage ratio.
**Câu hỏi**: NPL thật bao nhiêu (bao gồm nợ nhớt ngoài BCTC)? Coverage đủ absorption không?
**Honest correction**: NPL VN có thể bị understate (restructure, evergreening). Check nợ M&A, nợ BĐS.

### Frame 3 — CASA funding (ngân hàng)
**Trigger**: tỷ lệ CASA (Current Account Savings Account).
**Câu hỏi**: CASA bền không? App/digital experience giữ được khách?
**Honest correction**: CASA dễ mất — khách chuyển sang ngân hàng khác khi app tốt hơn. Tech (MB, TCB) có lợi thế.

### Frame 4 — Crack spread moat (dầu khí lọc hóa dầu)
**Trigger**: BSR, PLX lọc dầu.
**Câu hỏi**: biên lọc (crack spread) bền không? Tỷ suất công suất refinary?
**Honest correction**: crack spread biến động mạnh — sinh lời chu kỳ, không phải moat cấu trúc. Capacity utilization quan trọng hơn.

### Frame 5 — Chu kỳ giá commodity (thép, dầu, than)
**Trigger**: cổ phiếu chu kỳ (HPG, BSR, BII).
**Câu hỏi**: "Đây là siêu chu kỳ hay bong bóng?" Historical analog (2007-2008, 2017-2018).
**Honest correction**: P/E thấp ở đỉnh chu kỳ = bẫy. Median 5N bị distort. Dùng P/B hoặc EV/EBITDA.

### Frame 6 — Counterparty NOC (dầu khí)
**Trigger**: khách hàng chính là NOC (Petrovietnam, EVN).
**Câu hỏi**: NOC trả nợ được không? Khoản phải thu aging?
**Honest correction**: NOC VN có rủi ro thanh khoản (EVN loss nhiều). Khoản phải thu lớn = risk thật.

### Frame 7 — NAV / land bank (BĐS)
**Trigger**: công ty BĐS lớn (VIC, VHM, NVL).
**Câu hỏi**: NAV thực bao nhiêu? Land bank ở đâu (prime vs non-prime)?
**Honest correction**: NAV có thể inflate — giá đất "kỳ vọng" không phải giá thật. Land bank non-prime khó monetize.

### Frame 8 — Chu kỳ BĐS
**Trigger**: cổ phiếu BĐS.
**Câu hỏi**: chu kỳ BĐS VN ở đâu? Hạ tầng/âm thanh khởi động hay đóng băng?
**Honest correction**: BĐS VN phụ thuộc chính sách (credit room, land law). Policy reversal risk cao.

### Frame 9 — Counterparty off-plan (BĐS)
**Trigger**: công ty BĐS bán off-plan.
**Câu hỏi**: buyer default rate? Deposits bảo vệ công ty thế nào?
**Honest correction**: off-plan VN có rủi ro buyer default + delivery delay. Legacy (NVL case) warning.

### Frame 10 — Cost moat quặng sắt (thép)
**Trigger**: HPG (tích hợp dọc quặng sắt).
**Câu hỏi**: cost quặng sắt của HPG so với peer nhập khẩu? Tích hợp dọc bền không?
**Honest correction**: HPG cost advantage thật NHƯNG bị chase bởi peer khi quặng sắt giảm giá. Moat phụ thuộc chu kỳ commodity.

### Frame 11 — Capacity utilization (thép, dầu khí)
**Trigger**: công ty công nghiệp heavy.
**Câu hỏi**: capacity utilization current? Lợi thế quy mô?
**Honest correction**: Capacity cao không tốt nếu demand yếu → fixed cost spread thin.

### Frame 12 — Same-store-sales growth (bán lẻ)
**Trigger**: MWG, PNJ, FRT.
**Câu hỏi**: SSSG dương hay âm? Traffic vs ticket?
**Honest correction**: SSSG VN khó tính (mở cửa hàng mới liên tục). Store count growth ≠ SSSG.

### Frame 13 — Ecosystem thành viên (bán lẻ)
**Trigger**: MWG (Annam Gao), PNJ (member).
**Câu hỏi**: member program retention? Repeat purchase rate?
**Honest correction**: Loyalty program VN chưa mature — retention thấp hơn Western benchmark.

### Frame 14 — Margin defensibility (bán lẻ)
**Trigger**: gross margin trend.
**Câu hỏi**: margin bền không? Private label gaining?
**Honest correction**: Gross margin VN bán lẻ thấp (~15-20%) — không có moat pricing power như Western retail.

### Frame 15 — Outsourcing moat (công nghệ FPT)
**Trigger**: FPT, CMG.
**Câu hỏi**: revenue per employee vs Indian peer (TCS, Infosys)? Contract backlog?
**Honest correction**: FPT outsourcing margin thấp hơn India — cost arbitrage đang thu hẹp.

### Frame 16 — Government contracts (công nghệ)
**Trigger**: FPT, Viettel.
**Câu hỏi**: % revenue từ government? Dependency?
**Honest correction**: Gov contract VN có rủi ro thanh khoản + thay đổi chính sách.

### Frame 17 — Chuyển đổi số tailwind (công nghệ)
**Trigger**: công ty công nghệ VN.
**Câu hỏi**: hưởng lợi trend chuyển đổi số VN hay quốc tế? Bền không?
**Honest correction**: Trend chuyển đổi số VN còn chậm vs quốc tế. Revenue growth có thể chậm hơn kỳ vọng.

### Frame 18 — Market share broker (chứng khoán)
**Trigger**: SSI, VND, VCI.
**Câu hỏi**: market share retail broker? Trend?
**Honest correction**: Market share VN chứng khoán biến động — khách dễ chuyển cho app tốt hơn (TCB, MBB).

### Frame 19 — Margin lending (chứng khoán)
**Trigger**: margin loan balance.
**Câu hỏi**: margin loan / equity? NPL margin?
**Honest correction**: Margin lending rủi ro chu kỳ thị trường — bull market phồng, bear market co.

### Frame 20 — Self-trading risk (chứng khoán)
**Trigger**: công ty CK tự trade.
**Câu hỏi**: % revenue từ self-trading? Volatility?
**Honest correction**: Self-trading revenue vol high — không bền. Check reporting transparency.

### Frame 21 — Combined ratio (bảo hiểm)
**Trigger**: BVH, MIG.
**Câu hỏi**: combined ratio < 100%? Bền không?
**Honest correction**: Bảo hiểm VN combined ratio cao (thường > 100%) — dựa vào đầu tư bù đắp.

### Frame 22 — Investment yield (bảo hiểm)
**Trigger**: công ty BH.
**Câu hỏi**: investment portfolio yield? Match liabilities?
**Honest correction**: Đầu tư BH VN tập trung trái phiếu chính phủ + gửi NH → yield thấp.

### Frame 23 — Bancassurance (bảo hiểm)
**Trigger**: MIG (MB Ageas), BIC.
**Câu hỏi**: bancassurance % revenue? Bank partner stable?
**Honest correction**: Bancassurance VN phụ thuộc ngân hàng đối tác — rủi ro mất deal.

### Frame 24 — EVN offtake (điện)
**Trigger**: POW, GEG.
**Câu hỏi**: EVN trả nợ được không? Khoản phải thu?
**Honest correction**: EVN VN lỗ nhiều — khoản phải thu từ EVN = risk thật (như Frame 6).

### Frame 25 — Capacity factor (điện)
**Trigger**: công ty điện.
**Câu hỏi**: capacity factor thực vs nameplate?
**Honest correction**: Capacity factor VN thấp do grid curtailment + demand yếu.

### Frame 26 — Fuel cost (điện nhiệt)
**Trigger**: BII, POW nhiệt than/dầu.
**Câu hỏi**: fuel cost % revenue? Tariff adjust kịp?
**Honest correction**: Tariff VN adjust chậm → cost inflation ăn mòn margin.

### Frame 27 — Throughput moat (cảng)
**Trigger**: GMD, PHP, VSC.
**Câu hỏi**: throughput growth? Cảng deep-water?
**Honest correction**: Cảng VN cạnh tranh gay gắt — tariff erode.

### Frame 28 — Geographic advantage (cảng)
**Trigger**: cảng gần Hải Phòng, Cái Mép.
**Câu hỏi**: location advantage bền không? Đường bộ kết nối?
**Honest correction**: Location bền NHƯNG infrastructure catch-up (cảng mới) erode advantage.

### Frame 29 — Tariff (cảng)
**Trigger**: giá container.
**Câu hỏi**: tariff trend? Volume vs value mix?
**Honest correction**: Tariff cảng VN thấp vs quốc tế — room tăng nhưng cạnh tranh.

### Frame 30 — ARPU (viễn thông)
**Trigger**: VNM (Viettel không listed).
**Câu hỏi**: ARPU trend? Data vs voice mix?
**Honest correction**: ARPU VN giảm dần — competition 3 nhà mạng.

### Frame 31 — Spectrum moat (viễn thông)
**Trigger**: VNM.
**Câu hỏi**: spectrum holdings? 5G rollout?
**Honest correction**: Spectrum VN assigned government — không phải moat company-driven.

### Frame 32 — Infrastructure sharing (viễn thông)
**Trigger**: VNM.
**Câu hỏi**: sharing towers? Cost saving?
**Honest correction**: Sharing VN chưa mature — regulate-driven.

### Frame 33 — Bed capacity (y tế)
**Trigger**: HMH, IDC.
**Câu hỏi**: bed capacity utilization? Expansion plan?
**Honest correction**: Y tế VN private còn nhỏ — scale advantage chưa rõ.

### Frame 34 — Doctor retention (y tế)
**Trigger**: HMH, IDC.
**Câu hỏi**: doctor retention rate? Compensation structure?
**Honest correction**: Bác sĩ VN có thể moonlight → retention khó.

### Frame 35 — Insurance billing (y tế)
**Trigger**: HMH, IDC.
**Câu hỏi**: % revenue từ BHYT? Tariff government?
**Honest correction**: BHYT tariff thấp → marginprivate patients mới là driver.

---

## C. Workflow dùng frames ở dashboard Section 8

Cho mỗi frame đã chọn (Phase 0 archetype routing):

1. **Read** template section (B ở trên)
2. **Fill** với data thật (vnstock + BCTC, citation footnote)
3. **Generate "honest correction"** — BẮT BUỘC. Tự hỏi: "Cách đọc nào ĐƠN GIẢN NHẤT mà bull case thường claim? Data có challenge nó không?"
4. **Verdict** + confidence (high/medium/low)
5. **KPI watchlist** 3-5 điểm cụ thể
6. **"Reframe cho nhà đầu tư"** closer — gắn insight với quyết định vốn đầu tư

**Output mỗi frame = 1 insight card** trong Section 8 Insights grid. **BẮT BUỘC** cân bằng: nếu có frame bull (vd F1 NIM moat) → phải có frame bear (vd F2 credit quality) đối ứng.

---

## D. Anti-patterns (KHÔNG được làm)

- ❌ **Cheerlead** — insight chỉ bullish, không challenge. Fix: honest correction BẮT BUỘC.
- ❌ **Generic** — insight dùng cho mọi công ty, không đặc thù. Fix: data thật + company-specific.
- ❌ **Bịa data** — invent số liệu. Fix: NOT FOUND nếu không có.
- ❌ **Copy 1 case** — clone HPG/BSR verbatim. Fix: frames là skeleton, content fill per ticker.
- ❌ **Skip honest correction** — vì "thật ra bull case đúng". Fix: correction là differentiator, BẮT BUỘC.

---

## E. Quality checklist per insight section (BẮT BUỘC verify)

- [ ] 1. Trigger question rõ — phrasing lại câu hỏi thesis
- [ ] 2. Data thật + citation — mỗi số có footnote source
- [ ] 3. Frame structure follow — 4-6 sub-block theo template
- [ ] 4. Honest correction callout — BẮT BUỘC 1 callout challenge
- [ ] 5. Verdict + confidence — rõ verdict + confidence level
- [ ] 6. KPI watchlist 3-5 points — cụ thể, measurable, quarterly
- [ ] 7. Reframe cho nhà đầu tư — closer gắn insight với vốn
- [ ] 8. KHÔNG cheerlead — nếu chỉ bull không challenge → fail
