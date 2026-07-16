# Thiết kế Báo cáo: Thanh khoản Tài sản — Khung đa tài sản cho Nhà đầu tư cá nhân

> **Ngày:** 2026-06-25
> **Trạng thái:** Đã duyệt thiết kế, chờ viết implementation plan
> **Loại:** Longform HTML (single-page, kể chuyện)
> **Định vị:** Framework đầu tư cá nhân — tiếng Việt, vừa đủ học thuật, có số minh họa.

---

## 1. Mục tiêu một câu

Giúp nhà đầu tư cá nhân hiểu vì sao **thanh khoản quyết định giá, biến động và rủi ro** của mọi loại tài sản — và dùng nó làm **thước đo risk/reward** khi phân bổ vốn giữa 6 loại tài sản: tiền mặt/CD, trái phiếu, cổ phiếu, vàng, bất động sản, crypto.

## 2. Quyết định phạm vi (đã chốt với người dùng)

| Quyết định | Lựa chọn |
|---|---|
| Định vị | Framework đầu tư cá nhân, tiếng Việt, vừa đủ học thuật |
| Phạm vi | 6 loại: tiền mặt/CD, trái phiếu, cổ phiếu, vàng, BĐS, crypto |
| Góc nhìn | Cả 4 (bản chất & chi phí thoát · premium · R/R · liquidity factor) |
| Định lượng | Công thức + số minh họa |
| Nguồn số | Paper kinh điển (Amihud, Pastor-Stambaugh, Hasbrouck, Kyle, Roll, Acharya-Pedersen, Corwin-Schultz, Brunnermeier-Pedersen, Sadka...) |
| Cấu trúc | Cách C — kể chuyện: trực giác → đo lường → đa tài sản → premium/R/R → liquidity factor → framework áp dụng |

## 3. Format & giọng văn

- **Format:** longform HTML một trang (theo mẫu `beyond-candlesticks`, `chart-patterns`, `trading-for-living`). Sticky TOC, charts/tables inline, citation ở cuối.
- **Độ dài dự kiến:** 12.000–16.000 chữ + ~10 bảng + ~8 charts minh họa.
- **Giọng văn:** như `beyond-candlesticks` — giải thích + số liệu + trực giác; có trích dẫn paper ở đúng chỗ nhưng không phô trương học thuật.
- **Thư mục lưu trữ:** `thanh-khoan-tai-san/` (mã nguồn HTML + tài liệu hỗ trợ).

## 4. Cấu trúc 6 phần

### Phần 1 — Trực giác: "Ra tiền trong bao lâu, mất bao nhiêu %?"

**Hook:** Bạn cầm 1 tỷ, 500 triệu cổ phiếu + 500 triệu căn hộ. Mai cần tiền gấp. Ra được bao nhiêu, trong bao lâu, mất bao nhiêu %?

**Nội dung:**
- Hai trục duy nhất: **thời gian thoát** (t→0∞) và **chi phí thoát** (c, %). Mọi thước đo phức tạp sau này đều quy về 2 trục này.
- 3 lớp thanh khoản (Brunnermeier & Pedersen 2009):
  - *Trading liquidity* — bid-ask spread, depth
  - *Funding liquidity* — margin, leverage của nhà tạo lập
  - *Market liquidity* — volume, breadth
- 2 bẫy trực giác:
  - "Cổ phiếu blue-chip luôn lỏng" — sai (Black Monday 1987, Flash Crash 2010).
  - "BĐS chậm vì giá trị lớn" — nửa đúng; chậm vì là *search market* chứ không phải *auction market*.
- Mini-table "dự đoán của bạn" tạo hook: BTC lỏng hơn hay trái phiếu chính phủ lỏng hơn? (câu trả lời bất ngờ cho Phần 3).

### Phần 2 — 4 thước đo kinh điển

**Hook:** Cổ phiếu A spread 0.05%, volume 100 tỷ/đ; cổ phiếu B spread 0.8%, volume 5 tỷ/đ. Cái nào thanh khoản hơn — và "hơn bao nhiêu"?

**4 thước đo:**

| Thước đo | Câu hỏi nó trả lời | Công thức | Paper |
|---|---|---|---|
| **Spread (Roll / Corwin-Schultz)** | Mỗi giao dịch mất bao nhiêu chi phí ẩn? | Roll: `s = 2√(−cov(r_t, r_{t−1}))`; CS từ high-low | Roll 1984, Corwin-Schultz 2012 |
| **Amihud ILLIQ** | Quy mô giao dịch đẩy giá chạy bao xa? | `ILLIQ = (1/D)·Σ|r_d| / DVOL_d` | Amihud 2002 |
| **Kyle λ (price impact)** | 1 đơn vị order flow đẩy giá bao nhiêu? | `Δp = λ·flow + ε`; λ = độ dốc | Kyle 1985 |
| **Pastor-Stambaugh γ** | Tài sản nhạy với *rủi ro thanh khoản hệ thống* ra sao? | hồi quy reversal on market return × flow innovation | Pastor-Stambaugh 2003 |

**Điểm cốt lõi:** 3 thước đầu đo **mức thanh khoản riêng**; thước thứ 4 (P-S) đo **rủi ro thanh khoản hệ thống**. Sự khác biệt này sẽ trở lại ở Phần 5.

**Mini-challenge:** Tính Amihud ILLIQ thủ công cho VN-Index (tận dụng dữ liệu volume đã có trong `bond_research`).

### Phần 3 — Profile thanh khoản của 6 loại tài sản

**Hook:** Xếp 6 loại tài sản theo ILLIQ từ thấp → cao — thứ tự có giống bạn nghĩ không?

**Bảng tổng hợp (số minh họa từ paper):**

| Tài sản | Spread ước lượng | Time-to-exit | Chi phí 1 giao dịch | Liquidity beta | Nguồn |
|---|---|---|---|---|---|
| Tiền mặt / CD | 0 | Tức thì / CD: phạt rút sớm | 0 / phạt ~3 tháng lãi | ~0 | — |
| TPCP (T-bill) | 0.005–0.02% | Tức thì | ~0.01–0.1% | thấp | Fleming 2003 |
| TPCP (T-bond) | 0.05–0.2% | Tức thì | ~0.05–0.2% | thấp | Fleming 2003 |
| Cổ phiếu large-cap | 0.01–0.1% | Tức thì | 0.05–0.2% + phí broker | trung bình | Hasbrouck 2009 |
| Cổ phiếu small-cap | 0.5–3% | Giới hạn theo volume | 0.5–3% + slippage | **cao** | Amihud 2002, Hasbrouck |
| Vàng (GLD/ETF) | 0.01–0.05% | Tức thì | ~0.1% | trung bình | — |
| Vàng (vật lý) | 2–5% | Vài giờ–vài ngày | 2–5% spread dealer | thấp | dealer data |
| Bất động sản | không có "spread" | **60–180 ngày** | **6–8%** (hoa hồng+thuế+hóa đơn) | trung bình–cao | Case & Shiller 2003 |
| Crypto (BTC/ETH) | 0.01–0.05% (CEX lớn) | Tức thì | ~0.1% + slippage | **rất cao** | Makarov-Schoar 2020 |
| Crypto (altcoin) | 0.5–5% | Phụ thuộc volume | lớn, dễ slippage | rất cao | — |

**Mỗi tài sản 1 thẻ (1–2 đoạn):** vì sao nó ở vị trí đó; đặc thù thanh khoản (BĐS = search market; crypto = 24/7 nhưng mỏng; trái phiếu VN = OTC không có sổ lệnh công khai).

**3 bất ngờ đáng chèn:**
1. Trái phiếu chính phủ Mỹ lỏng hơn cổ phiếu (spread < 0.01%).
2. Vàng vật lý gần như "không lỏng" so với GLD — cùng tài sản, 2 thanh khoản khác nhau.
3. Crypto "lỏng 24/7" nhưng liquidity beta cao nhất — lỏng lúc bình thường, cạn khi stress.

### Phần 4 — Phần bù thanh khoản có xứng không? (Premium + R/R)

**Hook:** Cổ phiếu small-cap và BĐS khó bán hơn → đáng lẽ phải sinh lời cao hơn. Nhưng cao hơn *bao nhiêu*, và *có thực sự đủ*?

**A. Lý thuyết premium:**
- Amihud & Mendelson (1986): quan hệ đơn điệu giữa spread và expected return — ~2–6 bps mỗi 1 bps spread.
- Acharya & Pedersen (2005, **LCAPM**): mở rộng CAPM với 4 dạng beta thanh khoản → `E[R_i] = Rf + β₁·(E[Rm]−Rf) + [beta thanh khoản]·liquidity premium`.

**B. Số thực chứng từ paper:**

| Tài sản | Premium ước lượng | Realized excess return | Có xứng? | Nguồn |
|---|---|---|---|---|
| Small-cap illiquid | ~2–4%/năm | ~1–2%/năm (sau 1980) | Không rõ — đã nén | Amihud 2002, Hou et al. 2020 |
| BĐS ở nhà | ~1.5–2%/năm | ~1–1.5%/năm | Biên hẹp | Flavin & Yamashita 2002 |
| Trái phiếu off-the-run | ~5–10 bps | ~5–10 bps | Có, ổn định | Krishnamurthy 2002 |
| Crypto (BTC) | không đo được | ±50%/năm | Không đo được | — |

**C. Liquidity-adjusted Sharpe (cốt lõi):**
- `L-Sharpe = (E[R] − Rf − c_liquidation) / σ`, với `c_liquidation = spread + slippage + time cost`.
- Quy đổi time-to-exit thành chi phí: bán gấp BĐS 30 ngày thay vì 150 ngày → mất thêm ~10–15% (fire-sale discount, Campbell-Giglio-Pathak 2011).
- **So-what cho cá nhân:** L-Sharpe cao nhất = tài sản đủ lỏng mà vẫn có premium (trái phiếu off-the-run, GLD, large-cap + một phần small-cap). BĐS và crypto trông premium cao nhưng L-Sharpe thấp.

**D. Quy tắc ngón tay cái:**
- Nếu `prem < chi phí thoát × 5` → premium không đủ bù.
- Quy tắc holding period: chỉ nắm tài sản ít lỏng nếu `horizon dự kiến > 5 × time-to-exit chuẩn`.

### Phần 5 — Khi thanh khoản biến mất: Liquidity Factor & Tail Risk

**Hook:** Tại sao *mọi thứ giảm cùng lúc* trong 2008, COVID 3/2020, bond tantrum 2013? Tương quan → 1.

**A. Liquidity spirals (Brunnermeier & Pedersen 2009):** vòng xoáy kép market liquidity ↓ → funding liquidity ↓ (margin calls) → market liquidity ↓ thêm. Khi leverage ép giải vốn, **thứ tự thoát: tài sản lỏng trước** → "liquidity goods selling first".

**B. Liquidity factor là nhân tố rủi ro:** Pastor & Stambaugh (2003) thêm nhân tố liquidity vào Fama-French → premium ~1.5–3%/năm cho tài sản có liquidity beta thấp. Sadka (2006): chỉ liquidity *vĩnh viễn* mới có premium.

**C. Liquidity tail risk (cho cá nhân):**
- Herfindahl của sổ lệnh: 1–2 market maker → rủi ro; nhiều → an toàn.
- "Dash for cash" (3/2020): ETF tiền thị trường rớt khi mọi người thoát USD cùng lúc.
- **Quy tắc cá nhân:** giả định trong khủng hoảng tương quan → 0.9. Vậy khoản "an toàn" thực sự = tiền mặt vật lý + T-bill trực tiếp (không qua fund).

**D. Số minh họa:**
- 3/2020: Treasury spread nới gấp 10× trong 2 tuần.
- Crypto 5/2022 (LUNA): spread BTC mở rộng 0.02% → 2–5%, slippage 10–20% trên size vừa.

### Phần 6 — Framework áp dụng cho nhà đầu tư cá nhân

**Hook:** Với 1 tỷ, chia thế nào — và dấu hiệu nào cho biết đang nắm *quá nhiều* tài sản thiếu thanh khoản?

**A. Khung Liquidity Tier:**

| Tier | Đặc điểm | Tỷ trọng gợi ý |
|---|---|---|
| **L0 — Khẩn cấp** | Ra tiền < 1 ngày, loss < 0.5% | 5–15% (tiền mặt, T-bill trực tiếp) |
| **L1 — Lỏng** | < 5 ngày, < 1% | 25–40% (large-cap, ETF, GLD) |
| **L2 — Lỏng vừa** | 5–30 ngày, 1–5% | 20–35% (small-cap, trái phiếu ít lỏng) |
| **L3 — Ít lỏng** | > 30 ngày, > 5% | < 15% (BĐS, PE, altcoin) |

**B. 3 câu hỏi tự kiểm trước khi mua:**
1. Nếu cần ra tiền trong 7 ngày, mất bao nhiêu %?
2. Tài sản này có liquidity beta cao không → premium có xứng không (L-Sharpe)?
3. Holding period của tôi có > 5 × time-to-exit không?

**C. Bẫy nhà đầu tư cá nhân VN hay gặp:**
- "Cổ phiếu thin" — vỏ large-cap nhưng thật ra một vài mã hiếm giao dịch.
- "BĐS tính thanh khoản = giá tăng" — sai; days-on-market mới là thước đo.
- "Crypto 24/7 = luôn bán được" — bán được ≠ bán được ở giá công bằng.
- "Trái phiếu ngân hàng = an toàn và lỏng" — gates/redemptions khi stress (bài học SCB 2022).

**D. Checklist 7 dòng:**
1. [ ] Tính ILLIQ (Amihud) cho từng vị thế định kỳ (1 lần/tháng).
2. [ ] Ước lượng chi phí thoát thực (c = spread + slippage ước lượng theo size của bạn).
3. [ ] Quy đổi holding period thành "ấn nút cài" → không mua L3 nếu horizon < 3 năm.
4. [ ] Đảm bảo L0 ≥ 5% mọi lúc (liquidity buffer).
5. [ ] Khi re-bal: bán L0/L1 trước, L2/L3 sau.
6. [ ] Stress-test: tương quan → 0.9, spread → ×3 → danh mục còn sống không?
7. [ ] Kiểm tra funding liquidity cá nhân (income vs debt) — không dùng đòn để mua L3.

## 5. Phụ lục

- **Phụ lục A:** Bảng công thức đầy đủ (Roll, CS, Amihud, Kyle, P-S, LCAPM) + mã Python ước lượng Amihud (tận dụng dữ liệu `bond_research`).
- **Phụ lục B:** Glossary ~30 thuật ngữ (liquidity, spread, depth, slippage, lambda, liquidity beta, fire-sale, gating, dash-for-cash...).
- **Phụ lục C:** Thư mục ~15 paper kinh điển, mỗi paper 1 câu annotation.
- **Disclaimer:** số minh họa từ paper kinh điển (chủ yếu thị trường Mỹ), cảnh báo rõ về áp dụng cho VN; đây là framework giáo dục, không phải lời khuyên đầu tư.

## 6. Thành phần kỹ thuật của HTML longform

- **Layout:** header + sticky TOC bên trái/trên, nội dung cuộn, citation tooltip hoặc section cuối.
- **Charts minh họa (planned, ~8):**
  1. Quan hệ 2 trục (time-to-exit × cost-to-exit), 6 tài sản là chấm.
  2. ILLIQ so sánh giữa tài sản (bar log-scale).
  3. Quan hệ spread ↔ expected return (Amihud-Mendelson).
  4. L-Sharpe so sánh.
  5. Liquidity spiral diagram (Brunnermeier-Pedersen).
  6. Tương quan → 1 trong stress (concept chart).
  7. Liquidity Tier wheel cho cá nhân.
  8. ~~Amihud ILLIQ time-series của VN-Index (từ `bond_research` data)~~ — **đã bỏ**; thay bằng chart ý niệm về ILLIQ (theo quyết định dữ liệu: dùng số quốc tế cho cả ví dụ lẫn data).
- **Tables:** ~10 (4 thước đo; profile 6 tài sản; premium thực chứng; Liquidity Tier; checklist; glossary tóm tắt...).
- **Tương tác (tùy chọn, nếu còn thời gian):** slider nhập "kích thước vị thế" → ước lượng slippage; calculator L-Sharpe đơn giản.

## 7. Rủi ro & cảnh báo về chất lượng

- **Rủi ro số liệu:** số minh họa chủ yếu thị trường Mỹ từ paper → cần ghi rõ caveat khi áp dụng cho VN; *không claim* đây là số đo chính thức cho VN.
- **Quyết định dữ liệu (đã chốt):** dùng **toàn bộ số từ paper quốc tế** cho cả ví dụ lẫn data — vì VN khuyết data nhiều tài sản (BĐS, crypto, trái phiếu OTC). Bỏ chart #8 (Amihud ILLIQ VN-Index thực chứng) → thay bằng chart ý niệm về ILLIQ. Không chạy số thực.
- **Rủi ro phổ quát hóa:** quy tắc ngón tay cái (prem < 5×cost; horizon > 5×exit) là heuristic, không phải luật — phải cảnh báo trong báo cáo.
- **Rủi ro quá dài:** 12–16k chữ là nhiều; cần TOC + section signpost tốt để người đọc nhảy tới phần cần.
- **Không phải lời khuyên đầu tư:** disclaimer rõ ở đầu + cuối.

## 8. Sửa lỗi từ fact-check (sau khi verify paper/number)

4 lỗi nghiêm trọng đã phát hiện qua Explore agents, **bắt buộc sửa** khi viết:

| # | Lỗi | Sửa thành |
|---|---|---|
| 1 | Pastor-Stambaugh premium "~1.5–3%/năm" | **~7.5%/năm** (high-minus-low decile spread, 1966–1999). Caveat: giảm sau 2000. |
| 2 | Campbell-Giglio-Pathak fire-sale "10–15%" | **~27–28%** foreclosure discount (AER 2011). Caveat: phản ánh chất lượng bỏ sót, không thuần illiquidity. |
| 3 | Case & Shiller 2003 — "search market" attribution | Search-market → gán cho **Wheaton (1977)** "A Search Model of the Housing Market". Case-Shiller chỉ nói về illiquidity + chi phí cao. |
| 4 | Makarov & Schoar 2020 journal | **Journal of Financial Economics** (không phải Review of Financial Studies). |

Plus các sửa title/precision:
- Sadka 2006 → "Momentum and Post-Earnings-Announcement Drift Anomalies: The Role of Liquidity Risk" (JFE).
- Hasbrouck 2009 → "Trading Costs and Returns for U.S. Equities: Estimating Effective Costs from Daily Data" (JF). Large-cap spread → "vài bp (~0.01–0.05%)" cho tên lỏng nhất.
- Case & Shiller 2003 → "Is There a Bubble in the Housing Market?", **Brookings Papers on Economic Activity**.
- Amihud-Mendelson "2–6 bps/bps" → trình bày là **xấp xỉ độ dốc** (slope), quan hệ **tăng, lõm** (increasing, concave) — không phải số trích.
- LUNA BTC spread "0.02→2–5%" → **không có nguồn chính thức**; trình bày là *minh họa xu hướng*.
- RE transaction cost 6–8% → ghi rõ **một bên (bán)**; round-trip ~8–12%.
- RE days-on-market 60–180 → ghi hiện tại median < 60 to-contract; 60–180 cho thị trường chậm.
- Vàng vật lý 2–5% → **một chân** (one-way dealer spread); round-trip ~5–9%.

## 9. Các bước tiếp theo

1. Spec này → user review (cổng hiện tại).
2. User duyệt → invoke `writing-plans` skill để chia implementation plan chi tiết (viết nội dung từng phần, dựng HTML, tạo charts, finalize).
3. Implement theo plan → dùng `longform` skill để dựng HTML theo style `beyond-candlesticks`.

## 9. Quyết định thực thi (đã chốt)

- **Nhịp trình bày:** viết **toàn bộ 6 phần + phụ lục** rồi mới trình bày bản HTML đầy đủ (không duyệt từng phần).
- **Dữ liệu:** dùng số quốc tế từ paper cho cả ví dụ lẫn data; không chạy số thực VN (vì VN khuyết data nhiều tài sản).
