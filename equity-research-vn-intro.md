# Equity Research VN: Pipeline 7 bước phân tích cổ phiếu toàn diện — giờ có thêm Pro Stock Profile

> Hệ thống pipeline tự động hóa phân tích equity research cho cổ phiếu Việt Nam, từ dữ liệu tài chính đến dashboard HTML tương tác. Bài viết giới thiệu pipeline tổng quan và đặc biệt đi sâu vào nâng cấp mới: **Pro Stock Profile** — hồ sơ giá-khối lượng định lượng theo methodology phân tích thị trường nội bộ.

---

## Vì sao cần một pipeline tự động?

Phân tích một cổ phiếu Việt Nam cho đúng cần ít nhất 6 góc nhìn khác nhau: dữ liệu tài chính 5 năm, phân tích cơ bản (DuPont, CAGR), định giá đa phương pháp, phân tích kỹ thuật, tin tức thời sự, và tổng hợp thành báo cáo trực quan. Mỗi góc nhìn lại có những bẫy dữ liệu đặc thù thị trường VN (chia tách cổ phiếu, đơn vị tính, data stale từ API).

Thay vì làm thủ công và dễ mắc sai lầm, pipeline `equity-research-vn` tự động hóa toàn bộ quy trình này thành 7 bước tuần tự, với output là một dashboard HTML đẹp, tương tác, deploy được lên Vercel.

```
/equity-research-vn FPT    # Chạy đầy đủ pipeline cho FPT Corporation
/equity-research-vn HPG    # Cho Hòa Phát
/equity-research-vn VCB    # Cho Vietcombank
```

---

## Pipeline 7 bước — tổng quan

### Bước 1: Thu thập dữ liệu (vn-financial-data-collector)

Nguồn #1 là **vnstock API** — fetch trực tiếp BCTC, ratios, news, events qua Python. Web scraping (CafeF, Vietstock, trang QHCD doanh nghiệp) chỉ dùng khi vnstock thiếu.

**Audit split là việc đầu tiên bắt buộc.** Rất nhiều cổ phiếu VN phát hành cổ phiếu thưởng định kỳ (FPT tăng từ 0.9 → 1.7 tỷ cổ phiếu trong 5 năm, BSR chia tách 1.615x năm 2025). Nếu không điều chỉnh (adjust) EPS/BVPS về cùng cơ sở (base) với giá, PE/PB sẽ sai hoàn toàn.

Case BSR 2026 đã chứng minh: PE tính từ giá đã điều chỉnh chia tách (split-adjusted) trộn với EPS gốc BCTC cho ra PE = 6.10x, trong khi PE đúng phải là 9.85x — sai lệch 60%.

### Bước 2: Phân tích cơ bản (vn-fundamental-analysis)

5 chỉ số chính từng năm (EPS, BVPS, ROE, ROA, ROS) + DuPont decomposition (Biên LN × Vòng quay tài sản × Đòn bẩy) để hiểu **chất lượng** lợi nhuận, không chỉ con số cuối.

Ví dụ FPT thể hiện **Pattern phòng thủ chất lượng cao**: ROE ổn định 20-22% suốt 5 năm, cả 3 thành phần DuPont ít biến động, EPS tăng trưởng đều 16.7%/năm — không có yếu tố "ảo tưởng ROE" (tăng nhờ nợ).

### Bước 3: Định giá đa phương pháp (vn-valuation-engine)

11 phương pháp: PE/PB median 5N, EV/EBITDA, P/CF, P/S, PEG, DCF (3 kịch bản), DDM, Graham, Reverse DCF. Hội tụ bằng median + dải P25-P75.

Trọng tâm là **sự hội tụ** — không tin một phương pháp duy nhất. Reverse DCF cho biết thị trường đang ngụ ý tăng trưởng gì tại giá hiện tại, từ đó đánh giá định giá quá bi quan hay quá lạc quan.

### Bước 4: Phân tích kỹ thuật (vn-technical-analysis) — CẢ HAI MODE

Đây là phần đã được nâng cấp đáng kể. Skill `vn-technical-analysis` có **2 mode tách biệt**, cung cấp 2 góc nhìn khác nhau, không thay thế nhau:

#### Mode ACTIVE — timing và verdict mua/bán

Dùng dữ liệu giá weekly 52 tuần. Tính MA10/20/50, RSI(14), MACD, Bollinger, Beta. Phát hiện patterns (Double Bottom, Channel, Candlestick, Divergence) chỉ khi có bằng chứng. Output là **Tech Score từ -6 đến +6** và Verdict (STRONG SELL → STRONG BUY) cùng trading strategy 3 kịch bản.

Ngôn ngữ ở mode này sử dụng "bullish/bearish/tín hiệu/khuyến nghị" — phù hợp khi cần câu trả lời rõ ràng "có nên mua/bán giờ không".

#### Mode PROFILE — hồ sơ giá-khối lượng định lượng, NON-ADVICE

Đây là **nâng cấp trọng tâm**. Dùng dữ liệu giá daily ~2 năm (≥252 phiên) cho FPT + VNINDEX + VN30. Tính **15 block profile định lượng**:

| Block | Đo lường | Câu hỏi trả lời |
|-------|----------|-----------------|
| Price behavior | Rolling returns 1M/3M/6M/1Y + vị trí lịch sử | Vị trí hiện tại so với lịch sử của chính mã |
| Volatility | HV20/60/120/252 + percentile | Độ phân tán lợi suất annualized |
| Drawdown | Episodes, max DD, underwater days | Lịch sử các đợt giảm và thời gian phục hồi |
| Return distribution | Histogram 8 bins, skew, kurtosis | Hình dáng phân phối lợi suất ngày |
| Tail risk | Historical VaR/ES 95%, 99% | Rủi ro đuôi (mô tả historical, không mô hình) |
| Liquidity | GT giao dịch, volume spike days | Mức hoạt động giao dịch |
| VPCI | Xác nhận giá-volume (VWMA/SMA) | Mức đồng thuận giữa giá và volume |
| Money flow | OBV/VPT/CMF | Áp lực dòng tiền |
| Effort-result | Wyckoff: nỗ lực giao dịch vs kết quả giá | Phiên many giao dịch nhưng ít biến động |
| High-volume behavior | Event study forward returns sau volume ≥2x avg | Điều gì xảy ra sau phiên volume cao |
| PVI/NVI | Price index phiên volume tăng/giảm | Price change tập trung ở phiên nào |
| Volume-at-Price | Phân bổ volume theo mức giá (POC) | Volume tập trung ở vùng giá nào |

Cộng thêm **8 setup heuristic** (Cờ tăng, Cờ đuôi nheo, Tam giác tăng, Nêm giảm, Cốc tay cầm, Chữ nhật đáy, Hai đáy, Measured Move) và **archetype classification** (trend_following / accumulation_breakout / trap_prone / mixed).

**Ngôn ngữ ở mode PROFILE bắt buộc `neutral_descriptive_non_advice`**: KHÔNG dùng "bullish/bearish/tín hiệu/khuyến nghị/strong buy/sell". Mỗi block kèm `interpretation_guardrail` cảnh báo đây là quan sát lịch sử. Kết thúc bằng 4 điểm non-conclusion bắt buộc.

Sự phân biệt này quan trọng: mode PROFILE trả lời "cổ phiếu này hành xử thế nào", mode ACTIVE trả lời "có nên giao dịch giờ không".

### Bước 5: Bản tin 30 ngày (vn-news-digest)

Nguồn chính từ vnstock `Company.news()` + `Company.events()`, bổ sung WebSearch cho tin ngành/vĩ mô. Phân loại 5 nhóm (biz/sector/macro/disclosure/analyst), tính sentiment score (-100 → +100) với category breakdown.

Điểm giá trị nhất là **category divergence** — khi biz/disclosure tích cực nhưng macro tiêu cực (như FPT: khối ngoại bán ròng mạnh nhưng insider mua) → insight mà chỉ nhìn sentiment tổng hợp sẽ bỏ qua.

### Bước 6: Dashboard HTML (vn-research-dashboard)

Tổng hợp tất cả thành file `[TICKER]_Complete_Report.html` với **11-13 sections**:

1. Hero + 6 KPI cards
2. Executive Summary (TL;DR + 4 highlight boxes)
3. Kết quả kinh doanh 5 năm
4. Định giá PE/PB
5. Multiples mở rộng
6. DCF & Graham
7. DuPont
8. Special Insights (Bull + Bear Case cân bằng + Catalyst Roadmap)
9. **Technical Analysis mode ACTIVE** (Tech Score, Verdict, indicators, patterns)
9b. **🧬 Pro Stock Profile mode PROFILE** (15 block định lượng, archetype, non-advice)
9.5. Tương quan giá dầu (chỉ cho ngành lọc hóa dầu)
10. News Digest 30 ngày
11. Quan điểm độc lập

Phong cách fintech hiện đại: dark theme với gradient tím-hồng, glassmorphism, Chart.js cho charts tương tác, navigation bar sticky với scroll-spy, progress bar, back-to-top.

QA tự động qua Playwright verify canvas render + 0 JS errors trước khi hoàn tất.

### Bước 7: Deploy Vercel

Một lệnh `vercel deploy --prod` → URL công khai để chia sẻ.

---

## Case study: FPT Corporation (tháng 6/2026)

Chạy pipeline cho FPT tại giá 70,800đ cho thấy một tình huống kinh điển: **divergence giữa cơ bản và kỹ thuật**.

### Fundamental — KHỎE
- Doanh thu 70,113 tỷ, LNST 9,376 tỷ (+19.3% YoY), EPS CAGR 16.7%/năm
- ROE ổn định 21% suốt 5 năm, DuPont Pattern phòng thủ chất lượng cao
- Mảng chuyển đổi số +64.6% YoY, chiến lược AI-First với hợp đồng mới

### Valuation — STRONG BUY (+33%)
- Median FV: 94,255đ từ 11 phương pháp hội tụ
- Reverse DCF: thị trường ngụ ý g chỉ 11.2% — bằng NỬA EPS CAGR thực (21%) → định giá quá bi quan

### Technical mode ACTIVE — STRONG SELL (-4/6)
- Giảm -26% trong 1 năm, alpha -38% vs VNINDEX
- Giá dưới cả MA10/20/50, RSI 37.7 (gần quá bán)

### Technical mode PROFILE — insights mới

Đây là phần nâng cấp thực sự tạo ra giá trị. Mode PROFILE cho thấy những điều mà mode ACTIVE không thấy:

- **Archetype: ACCUMULATION_BREAKOUT** — setup nghiêng tích lũy, đọc kỹ phiên xác nhận thoát nền
- **3 setups chiều tăng**: Chữ nhật đáy (score 84.7 - đang hình thành), Hai đáy (72.2), Cốc tay cầm (60.4)
- **Mức giảm hiện tại -44.95%** (max -46.84%), underwater 345 ngày — lịch sử drawdown chi tiết
- **VPCI: "volume không cùng chiều giá"** + CMF âm → dòng tiền đang suy yếu, confirm áp lực kỹ thuật
- **Beta 252 chỉ ~0.33** (R² thấp) → FPT đi khá độc lập với thị trường, không phải bản sao VNINDEX

### News — BULLISH nhẹ (+38)
- Divergence: 8 lãnh đạo FPT + SCIC đăng ký MUA ~1.96 triệu cổ phiếu tại đáy 2 năm (insider buying signal mạnh)
- Category scores: biz=75, disclosure=86, analyst=100, nhưng macro=-100 (khối ngoại bán ròng)

### Tổng hợp

Dashboard cuối: 112.8 KB, 10 charts tương tác, 11 sections, QA pass 0 errors. Deploy tại Vercel URL công khai.

Điểm quan trọng nhất: **sự phân biệt 2 mode kỹ thuật** cho phép trình bày cả góc nhìn "timing giao dịch" (ACTIVE - STRONG SELL) lẫn "hồ sơ hành vi" (PROFILE - accumulation_breakout) mà không mâu thuẫn. Mode PROFILE bổ sung context phong phú cho quyết định cơ bản/định giá mà không đưa ra khuyến nghị giao dịch riêng.

---

## Kỹ thuật triển khai

### Stack

- **Python**: vnstock API (VCI source), pandas, statistics
- **JavaScript**: Chart.js 4.4 + chartjs-plugin-annotation
- **QA**: Playwright (verify canvas render + JS errors)
- **Deploy**: Vercel CLI

### Architecture đáng chú ý

**Profile engine portable**: Toàn bộ 15 block profile + 8 setup heuristic + archetype được port thành một module Python standalone (`profile_engine.py`), chỉ cần daily OHLCV từ vnstock. Có thể tái sử dụng cho bất kỳ mã cổ phiếu nào mà không phụ thuộc thư viện ngoài.

**Template + inject pattern**: Thay vì generate HTML bằng f-string Python (gây xung đột brace với JavaScript), dùng template HTML với placeholder `{{TOKEN}}` + string replacement đơn giản. Tránh hoàn toàn class bug khó debug.

**Ngôn ngữ tách bạch**: Verify tự động `grep` trong section PROFILE phải trả empty cho các từ "bullish/bearish/strong buy/khuyến nghị mua" — đảm bảo không trộn 2 mode ngôn ngữ.

---

## Nguyên tắc cốt lõi

Pipeline được xây trên 4 nguyên tắc:

1. **Data thật** từ nguồn chính thức (vnstock API, BCTC doanh nghiệp). Tuyệt đối không mô phỏng/ngụy tạo data giá.
2. **Cross-check** nhiều nguồn cho số liệu quan trọng (LNST, VCSH, EPS).
3. **Patterns chỉ claim khi có evidence** rõ. Nếu data không show → nói thẳng "không có".
4. **Thành thật về bất định**: mode PROFILE luôn kèm guardrail + 4 điểm non-conclusion cảnh báo đây là mô tả lịch sử, không phải dự báo.

---

## Bẫy dữ liệu đã xử lý

Pipeline áp dụng **9 bẫy dữ liệu** đặc thù thị trường VN (lessons learned từ case BSR 2026 và FPT 2026):

1. Split-adjustment consistency (Bẫy 5B) — audit split đầu tiên, adjust EPS/BVPS về cùng base
2. `Finance.ratio()` có thể stale — tự tính từ income_statement + balance_sheet
3. EPS vnstock ≠ EPS BCTC gốc — cross-check qua back-calc
4. Template HTML + Python inject — không f-string với JS
5. Section Insights cân bằng Bull/Bear
6. Section cuối = Independent view, không lặp báo cáo CTCK
7. Ngành đặc thù cần section riêng (lọc hóa dầu = crack spread, BĐS = NAV, ngân hàng = NIM)
8. Verify placeholders trước khi deploy
9. **Chạy cả 2 mode kỹ thuật** (ACTIVE + PROFILE) — không mặc định 1 mode

---

## Cách sử dụng

```
/equity-research-vn [TICKER]
```

Tùy chọn:

| Flag | Tác dụng |
|------|----------|
| `--fundamental-only` | Chỉ bước 1-3 + 6, bỏ cả 2 mode kỹ thuật + news |
| `--style bloomberg` | Phong cách Bloomberg Terminal tối |
| `--style corporate` | Phong cách corporate sáng |
| `--period 3y` | Kỳ phân tích 3 năm (mặc định 5 năm) |
| `--peers BID,CTG,TCB` | So sánh với peer ngành |
| `--no-deploy` | Chỉ tạo file local |

Pipeline mất 15-30 phút tùy mã (fetch data + tính toán + render + deploy).

---

## Kết luận

Equity research cho cổ phiếu Việt Nam có nhiều bẫy dữ liệu đặc thù mà các tool quốc tế không xử lý được. Pipeline `equity-research-vn` giải quyết bằng cách:

1. **Tự động hóa** 7 bước từ data đến deploy, giảm sai lầm thủ công
2. **Audit split** bắt buộc đầu tiên — xử lý bẫy lớn nhất thị trường VN
3. **Đa phương pháp định giá** hội tụ, không tin 1 PP duy nhất
4. **Cả 2 mode kỹ thuật** (ACTIVE + PROFILE) — vừa có verdict giao dịch, vừa có hồ sơ hành vi định lượng phong phú
5. **Ngôn ngữ tách bạch** — PROFILE non-advice với guardrail, ACTIVE với verdict rõ ràng
6. **Dashboard tương tác** đẹp, deploy được, QA tự động

Nâng cấp Pro Stock Profile (mode PROFILE) là bước tiến quan trọng nhất gần đây — biến phân tích kỹ thuật từ chỉ "Tech Score mua/bán" thành hồ sơ hành vi giá-khối lượng định lượng theo methodology chuyên nghiệp, đồng thời giữ được tính trung lập về mặt khuyến nghị.

---

*Pipeline được xây dưới dạng skill system, có thể tích hợp vào bất kỳ coding agent nào. Toàn bộ code Python (profile engine) 100% portable với vnstock, tái sử dụng được cho mọi mã cổ phiếu HOSE/HNX/UPCOM.*

*⚠️ Báo cáo do pipeline tạo là giáo dục/tham khảo, không phải lời khuyên đầu tư. Đầu tư cổ phiếu có rủi ro mất vốn.*
