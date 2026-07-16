# Open Questions — Đối chất thống kê với GPT

> Tài liệu nội bộ chuẩn bị cho buổi review ngày 02/07/2026.
> Mục đích: trình bày các lo ngại về over-correction và mất power,
> kèm số liệu thật từ artifact để GPT đánh giá độc lập.

---

## 1. Bối cảnh

Nghiên cứu 4 chương (2014–2026) về quan hệ lợi suất trái phiếu Chính phủ Việt Nam và cổ phiếu HOSE. Bốn chương dùng:

- Dependent-wild bootstrap (Shao 2011, shared innovation, block=5).
- Holm FWER 5% cho confirmatory families.
- BH FDR 10% cho exploratory.
- B=999 full matrix, B=9999 cho verdict candidates.
- Plus-one bootstrap p-values.
- True bivariate VAR(p) Granger với system BIC logdet.

Kết luận chính: **CONTEMPORANEOUS_ASSOCIATION_ONLY** — có quan hệ đồng thời giới hạn; chưa tìm thấy bằng chứng dự báo ổn định trong các thiết kế daily và monthly đã kiểm định. Riêng kết quả monthly bị giới hạn power do chuỗi tháng ngắn.

---

## 2. Lo ngại 1: Dữ liệu tháng quá ít + hiệu chỉnh chặt = mất power

### Số liệu

| Tần suất | n hiệu dụng | Min detectable Cohen d (80% power) |
|----------|-------------|-------------------------------------|
| Daily | 2.200–25.400 | 0,056–0,060 (rất nhỏ) |
| Monthly | 119 | 0,257 (small-medium) |
| Forward 3 tháng | 45 (chạy được) | 0,419 (medium) |

Với n=119 tháng, nghiên cứu chỉ phát hiện được hiệu ứng medium trở lên. Hiệu ứng nhỏ (Cohen d < 0,2) bị bỏ sót.

### Hiệu chỉnh thực tế

- F1 family: Holm nhân p × 5 (m=5 tests) → raw p=0,0083 thành Holm p=0,0415.
- F5 family: Holm nhân p × 3 → raw p=0,0094 thành Holm p=0,0282.
- Tổng cộng nghiên cứu có hơn 1.500 phép thử, nhưng con số này không trực tiếp nhân vào F1/F5. Holm được áp dụng trong từng family đã khóa với `m=3–5`; family chỉ nghiêm ngặt hơn nếu số phép thử bên trong chính family đó tăng.

### Câu hỏi cho GPT

> Với n=119 và Holm ×3–×5, có khả năng nghiên cứu đang **bỏ sót** quan hệ thật yếu không?
>
> Nếu thả Holm và dùng raw p < 0,01 cho monthly, có bao nhiêu test sẽ vượt? Điều đó nói gì về over-correction?

---

## 3. Lo ngại 2: F1 nằm trên ranh giới Bootstrap

### Số liệu

```
F1 raw p = 0,0083 (B=9999; artifact không lưu trực tiếp số exceedance)
95% CI cho p-value: [0,0065, 0,0101]
Holm threshold bước 1: 0,010
```

Cận trên CI (0,0101) **vượt qua** ngưỡng Holm (0,010). Nghĩa là: nếu chạy lại bootstrap với seed khác, F1 có thể **không vượt** Holm.

### Câu hỏi cho GPT

> F1 (Δ2Y → breadth, monthly) có nên được coi là **xác nhận** hay chỉ **cận ngưỡng**?
>
> Nếu GPT đồng ý F1 là cận ngưỡng, verdict có nên hạ từ CONTEMPORANEOUS_ASSOCIATION_ONLY xuống NOT_SUPPORTED?

---

## 4. Lo ngại 3: Nghiên cứu ban đầu tìm thấy tín hiệu rất mạnh — rồi biến mất

### Số liệu

Nghiên cứu sơ khai (`bond_inside_vnindex_v1`, stock-panel exploratory):

- Không có dòng nào có `p_raw=0`. Có 37/90 test có `p_raw<0,001`; p nhỏ nhất khoảng `2,2e-16`.
- Toàn bộ 90 dòng thiếu `effect_size`, nên hiện chưa thể phân biệt tín hiệu kinh tế với khác biệt do specification/inference.
- Mô hình dùng two-way clustering theo ngày và mã (`n_dates` khoảng 2.473; `n_symbols` khoảng 389). Vì vậy không được suy luận rằng 822.000 hàng tự động làm p-value giả.
- OOS cũ gồm 8 mô hình, chỉ 1 mô hình vượt base rate, margin tốt nhất khoảng `+0,032`. Điều này phù hợp với nghi ngờ overfit/inflation nhưng chưa chứng minh triệt để.

Nghiên cứu hiện tại (Chương 2, đã nghiệm thu):

- Quan hệ **đồng thời** (Layer A): p_raw=0,0001, Holm p=0,015 → **vượt**.
- Dòng Layer B được viện dẫn có `p_raw=0,6109`, nhưng đây là VNINDEX daily (`d_y2_5d_bps → fwd_ret_log_5d`) với `effective_n=2.907`, không phải monthly `n=119`. Kết quả này là không phát hiện được quan hệ dẫn trước trong thiết kế daily đó, không phải bằng chứng H0 đúng.

### Ba khả năng giải thích

| # | Giả thuyết | Bằng chứng ủng hộ | Bằng chứng chống |
|---|-----------|-------------------|------------------|
| A | Over-correction loại tín hiệu thật | F1 ranh giới; n=119 ít | Tỷ lệ dương tính 1,5% (vs 5% kỳ vọng); daily vẫn thấy tín hiệu |
| B | Tín hiệu cũ bị inflation hoặc khác biệt specification/inference | Thiếu effect size; outcome forward chồng lấn; OOS cũ chỉ 1/8 beat base rate | Two-way clustering đã được dùng; chưa có so sánh apples-to-apples |
| C | Tín hiệu đồng thời có thể tồn tại, dẫn trước chưa được xác nhận | Layer A vượt gate; Layer B và OOS không cho bằng chứng ổn định | Không bác bỏ H0 không đồng nghĩa H0 đúng |

### Câu hỏi cho GPT

> Giữa ba khả năng, GPT đánh giá khả năng nào khả dĩ nhất?
>
> Có cần chạy sensitivity (thả Holm, dùng raw p < 0,01) để phân biệt A vs B vs C không?

---

## 5. Lo ngại 4: Quan hệ có thay đổi theo từng cụm thời gian không?

### Bối cảnh

Thị trường Việt Nam đang trong quá trình tự hoàn thiện — từ thị trường mới nổi sang thị trường phát triển hơn. Cấu trúc, thanh khoản, chính sách và thành phần nhà đầu tư thay đổi đáng kể qua từng giai đoạn. Nếu quan hệ lợi suất trái phiếu ↔ cổ phiếu thay đổi theo từng sub-period, kết quả toàn mẫu có thể che khuất hoặc pha trộn các regime khác nhau.

### Số liệu: lợi suất 2 năm thay đổi cực mạnh qua 12 năm

| Giai đoạn | Avg y2 (%) | Std y2 (%) | Đặc trưng |
|-----------|-----------|-----------|-----------|
| 2014–2016 | 4,86–5,40 | 0,31–0,76 | Lãi suất cao, giảm dần |
| 2017–2018 | 3,39–4,19 | 0,27–0,74 | Hạ lãi suất |
| 2019–2021 | 0,65–3,02 | 0,08–0,54 | COVID, lãi suất cực thấp (y2 < 1% năm 2021) |
| 2022 | 2,67 | 1,45 | Tăng vọt, biến động kỷ lục |
| 2023–2026 | 1,94–3,55 | 0,21–0,91 | Bình thường hóa |

Đây không phải một thị trường ổn định. Năm 2021 lợi suất 2 năm ở mức 0,65% — gần zero. Năm 2022 std=1,45% — biến động gấp 18 lần năm 2021. Quan hệ thống kê có thể khác biệt căn bản giữa các giai đoạn này.

### Nghiên cứu đã test sự ổn định thời gian như thế nào?

**1. Structural break tests (Ch4):**
- Fixed break 2020-03 (COVID): joint p_boot=0,137, slope p_boot=0,443 — **không bác bỏ H0 không gãy**.
- Fixed break 2022-01 (tăng lãi suất): joint p_boot=0,407, slope p_boot=0,321 — **không bác bỏ H0 không gãy**.
- Unknown break sup-Wald: p_boot=0,580 — **không tìm thấy gãy**.

→ Kết luận được phép: chưa tìm thấy bằng chứng về điểm gãy trong các kiểm định đã chạy. Không được suy ra rằng quan hệ chắc chắn ổn định.

**2. Regime analysis (nghiên cứu sơ khai bond_inside_vnindex_v1):**
- Chia theo regime_bull (trên/dưới MA200) và vol_high (biến động cao/thấp).
- Kết quả: gần như null ở cả 4 regime.
- Một tín hiệu duy nhất: y2_realized_vol → breadth_deterioration, regime_bull=1, p_raw=0,015 (không vượt BH).

→ Không tìm thấy quan hệ thay đổi theo regime.

### Nhưng: nghiên cứu chưa kiểm tra đủ

| Kiểm tra | Đã làm? |
|----------|---------|
| Gãy cấu trúc ở 2 điểm cố định (2020-03, 2022-01) | ✓ (null) |
| Gãy cấu trúc unknown (sup-Wald scan) | ✓ (null) |
| Chia theo bull/bear regime | ✓ (null) |
| Chia theo vol cao/thấp | ✓ (null) |
| **Rolling window 2-3 năm** | ❌ chưa |
| **So sánh trước/sau 2018** | ❌ chưa |
| **So sánh trước/sau COVID** | ❌ chưa |
| **Sub-period beta stability** | ❌ chưa |

### Câu hỏi cho GPT

> Nghiên cứu test structural break và regime — cả hai đều null. Nhưng chưa test rolling window.
>
> Nếu chạy rolling 24 tháng, beta có dao động mạnh không? Nếu có, điều đó nghĩa là gì cho kết luận toàn mẫu?
>
> Thị trường Việt Nam thay đổi cấu trúc (thành viên, thanh khoản, chính sách) qua 12 năm. Liệu "không có gãy" là vì thực sự ổn định, hay vì test không đủ power để phát hiện gãy ở n=119?

---

### Quan điểm ZCode về lo ngại 4

Thị trường Việt Nam 2014–2026 không phải một thị trường. Nó là ít nhất ba thị trường khác nhau chồng lên nhau:

**2014–2017:** Lãi suất cao (y2 ~5%), thị trường nhỏ, thanh khoản mỏng, ít ngoại tham gia.

**2018–2021:** Hạ lãi suất cực mạnh, COVID, y2 chạm 0,65% — gần zero. Thanh khoản bùng nổ, dòng tiền cá nhân đổ vào. Cấu trúc thị trường thay đổi căn bản.

**2022–2026:** Bình thường hóa, y2 quay lại 2–3%, biến động 2022 std=1,45% — kỷ lục. Thị trường trưởng thành hơn, nhưng vẫn đang chuyển đổi.

Nghiên cứu lấy trung bình của ba giai đoạn này và chạy một bộ thống kê. Nếu quan hệ trái phiếu–cổ phiếu khác nhau giữa các giai đoạn — mạnh ở 2014, yếu ở 2021, ngược chiều ở 2022 — thì beta toàn mẫu sẽ pha loãng hoặc triệt tiêu. Kết quả: hiệu ứng rất nhỏ (−0,0007/25bps) không phải vì quan hệ thật nhỏ, mà vì nó bị trung bình hóa từ các mảnh trái dấu.

Về "không có gãy cấu trúc": tôi không tin hoàn toàn. Break test chạy trên n=119 tháng — cùng vấn đề power như mọi thứ khác. Sup-Wald scan chia 78 điểm, mỗi điểm chia mẫu thành hai nửa ~60 tháng — power phát hiện gãy trong mỗi nửa rất thấp. Nếu gãy tồn tại nhưng beta trước và sau cùng dấu (chỉ khác biên độ), break test sẽ khó bắt.

Tức là: "không có gãy" có thể đúng, nhưng cũng có thể là "không đủ dữ liệu để phát hiện gãy".

Nhưng đây là điểm xoay: nếu quan hệ thực sự thay đổi theo thời gian — mạnh năm này, yếu năm khác, thậm chí đảo chiều — thì điều đó củng cố cùng một kết luận: lợi suất trái phiếu không dự báo được cổ phiếu ổn định. Bởi vì "dự báo được" đòi hỏi quan hệ vững xuyên suốt, không phải chỉ trong một regime.

Nói cách khác:
- Nếu quan hệ ổn định yếu → kết luận "hiệu ứng nhỏ, không dự báo được" ✓
- Nếu quan hệ thay đổi theo regime → kết luận "không ổn định, không dự báo được" ✓

Cả hai đường đều về cùng một đích. Nhưng cái chúng ta không thể nói là: "trong giai đoạn X, lợi suất trái phiếu thực sự dự báo được cổ phiếu mạnh." Bởi vì chúng ta chưa tách giai đoạn để kiểm tra.

Về rolling window: nếu chạy rolling 24 tháng cho F1 monthly, mỗi cửa sổ chỉ có 24 điểm. Power phát hiện trong 24 điểm gần như bằng không. Beta sẽ dao động loạn — không phải vì quan hệ loạn, mà vì nhiễu thuần túy trong mẫu nhỏ. Kỳ vọng kết quả rolling sẽ không kết luận được gì — quá nhiễu. Nhưng nó có giá trị chẩn đoán: nếu beta dao động qua dấu (dương sang âm) một cách có hệ thống, đó là dấu hiệu regime change dù p-value không significant.

Tóm lại: lo ngại này không phải "có thể sai" — nó là hiện tượng thật mà nghiên cứu chưa xử lý đầy đủ. Thị trường Việt Nam đang chuyển đổi, và lấy trung bình 12 năm của một thị trường chuyển đổi sẽ che khuất cấu trúc bên trong. Nhưng tôi cũng không nghĩ nó thay đổi kết luận thực dụng. Dù tách regime hay không, không có regime nào cho dự báo ngoài mẫu ổn định — OOS 0/175 (Ch2) chạy trên toàn bộ giai đoạn. Nếu có một regime đặc biệt thuận lợi, OOS expanding-window sẽ bắt được ít nhất một phần. Nó không bắt được gì.

Điều tôi không biết và thành thật thừa nhận: nếu tách đúng regime — ví dụ chỉ 2018–2021 (lãi suất thấp, thanh khoản bùng nổ) — có thể có một cửa sổ hẹp nơi quan hệ mạnh hơn rõ rệt. Nhưng đó sẽ là overfitting theo thời gian — chọn giai đoạn thuận lợi sau khi nhìn kết quả. Và nghiên cứu đã ghi rõ: không được làm điều đó.

### Framing thay thế: quan hệ đang hình thành, không phải đã hoàn thiện

Người nghiên cứu đưa ra góc nhìn động (dynamic) thay vì tĩnh (static):

Thay vì hỏi "có quan hệ không?", nên hỏi **"quan hệ có đang hình thành và mạnh lên không?"**

Nếu beta toàn mẫu = −0,0007 (rất nhỏ), có ba cách diễn giải:

| Diễn giải | Beta theo thời gian | Ý nghĩa |
|-----------|---------------------|---------|
| Quan hệ yếu, ổn định | Beta ≈ −0,0007 xuyên suốt | Hiệu ứng thật nhỏ |
| Quan hệ mạnh nhưng bị pha loãng | Beta dao động qua regime | Trung bình hóa che khuất |
| **Quan hệ đang hình thành** | Beta gần 0 ở đầu mẫu, tăng dần về −0,002 ở cuối | Thị trường đang trưởng thành |

Ba kịch bản cho cùng beta toàn mẫu, nhưng ý nghĩa hoàn toàn khác. Kịch bản thứ ba nghĩa là: thị trường Việt Nam đang đi đúng hướng, quan hệ trái phiếu–cổ phiếu đang phát triển, và nghiên cứu hiện tại chỉ đang nhìn "trung bình của một quá trình tiến hóa."

Lý do kịch bản này khả dĩ:

- 2014: thị trường trái phiếu VN mỏng, ít giao dịch, thiếu chiều sâu.
- 2026: thị trường lớn hơn, thanh khoản tốt hơn, cơ cấu nhà đầu tư đa dạng hơn.
- Sự trưởng thành này có thể đang làm quan hệ trái phiếu–cổ phiếu mạnh lên dần — nhưng quá trình đó bị che khuất khi lấy trung bình 12 năm.

Điều này có thể kiểm tra bằng:
1. Rolling beta 36 tháng (cửa sổ đủ rộng hơn 24 tháng để giảm nhiễu).
2. So sánh beta nửa đầu (2014–2019) vs nửa sau (2020–2026).
3. Beta theo từng năm (chia 12 năm, mỗi năm ~12 tháng — quá ít cho p-value nhưng đủ xem trend).

Nếu beta thực sự tăng theo thời gian (|beta| cuối > đầu), điều đó sẽ:
- Không thay đổi kết luận "không dự báo được" (OOS vẫn null).
- Nhưng thay đổi cách nói về kết quả: từ "quan hệ yếu" thành "quan hệ đang phát triển."
- Mở hướng nghiên cứu tiếp theo: theo dõi xem trend có tiếp tục.

---

## 6. Lo ngại 5: Chưa kiểm tra đường cong lợi suất đầy đủ

### Số liệu

Các Chương 2–4 chỉ dùng **1 phép đo đường cong chính thức**: slope 10Y-2Y. Kết quả gần như null. Tuy nhiên curvature 2s5s10s đã xuất hiện ở tầng exploratory của `raw_yield_multidimensional_v2_2`, nên không được mô tả là hoàn toàn chưa nghiên cứu.

Nhưng cơ sở dữ liệu có **5 phép đo** chưa dùng:

| Phép đo | Có dữ liệu | Đã nghiên cứu |
|---------|-----------|---------------|
| Slope 10Y-2Y | ✓ | ✓ (null) |
| Slope 5Y-2Y | ✓ | ❌ |
| Slope 20Y-10Y | ✓ | ❌ |
| Curvature 2s5s10s | ✓ | ✓ exploratory: return null; volatility thấp hơn nhưng không vượt BH |
| Slope z-score 252 ngày | ✓ | ❌; đây là chuẩn hóa slope cũ, không phải chiều hình học độc lập |

Kết quả curvature exploratory cần trình bày đủ:

- `curvature → fwd_excess_ret_log_5d`: p_BH = `1,000 / 0,821 / 0,830` cho VNINDEX/VN30/VN100.
- `curvature → fwd_excess_ret_log_20d`: p_BH = `1,000 / 0,725 / 0,965`.
- `curvature → fwd_volatility_20d`: p_BH = `0,206 / 0,111 / 0,514`; cả ba đều `significant_bh=False`.

Ba giá trị trên mỗi dòng là ba index của cùng một outcome, không phải ba outcome độc lập.

### Câu hỏi cho GPT

> Việc chưa test curvature 2s5s10s có phải là khoảng trống nghiêm trọng không?
>
> Nếu curvature cho tín hiệu khi slope không cho, liệu đó có thay đổi kết luận chính không?

---

## 7. Dữ liệu tham chiếu nhanh cho GPT

### Kết quả chính (tất cả từ artifact đã hash)

| Chương | Câu hỏi | Kết quả | n |
|--------|---------|---------|---|
| 1 | Dự báo độc lập? | 0 phép thử vượt Holm | 90+42+6 |
| 2 | Đồng thời? | 2 quan hệ (Δ2Y daily × 8 chỉ số, Δ10Y monthly × 3 chỉ số) | 1.485 |
| 2 | Dẫn trước? | Granger 0/150 daily + 0/150 monthly (bond→equity); chiều equity→bond không được test trong Ch2 | 300 |
| 2 | OOS? | 0/140 mô hình đủ depth đạt stable; 35/175 insufficient (`n_folds=0`) | 140 đánh giá được / 175 đăng ký |
| 3 | Khối lượng? | 0/807 xác nhận | 807 |
| 4 | Breadth tháng? | F1 Holm p=0,0415, F5 Holm p=0,0282; effect -0,0007/25bps | 119 |
| 4 | Dẫn trước? | Granger 0/7 | 7 |
| 4 | OOS? | 0/3 stable (improvement 0,02-0,33% vs 2%) | 3 |

### Verdict

**CONTEMPORANEOUS_ASSOCIATION_ONLY** — có quan hệ đồng thời giới hạn, hiệu ứng nhỏ; chưa tìm thấy bằng chứng dự báo ổn định trong các thiết kế đã kiểm định. Trong 140 mô hình OOS đủ depth, không mô hình nào stable; 35 mô hình còn lại không đủ depth.

Chẩn đoán OOS bổ sung: 56 mô hình `OOS_MIXED` có improved-fraction median `0,517`, IQR `[0,508; 0,527]`; 84 mô hình `OOS_FAILED` có median `0,472`. Nhóm MIXED gần mức coin-flip, nhưng vì các fold phụ thuộc thời gian nên đây chỉ là diagnostic, không phải kiểm định Bernoulli chính thức.

### Quy trình thống kê

- Bootstrap: dependent-wild shared innovation (Shao 2011), block=5.
- P-value: plus-one two-sided, (#{exceed}+1)/(B+1).
- Hiệu chỉnh: Holm FWER 5% confirmatory, BH FDR 10% exploratory.
- Granger: true bivariate VAR(p), system BIC logdet, restricted-null bootstrap.
- Power validation: size 6,0% (target [1%,12%]); power 100% chỉ tại `beta_alt=0,3`. Kết quả này không chứng minh nghiên cứu có đủ power cho hiệu ứng thực tế nhỏ khoảng `−0,0007/25bps`.
- Mutation tests: 24 test bao phủ 20 spec defect classes.

---

## 8. Đề xuất action items cho buổi review

### Ưu tiên có thể thực hiện ngay

| Hạng | Action | Mục tiêu | Quy tắc diễn giải |
|------|--------|----------|-------------------|
| 1 | **Tăng bootstrap depth cho F1** (`B≥49.999` hoặc sequential Monte Carlo) | Quyết định F1 là xác nhận hay cận ngưỡng Monte Carlo | Không đổi seed nhiều lần rồi chọn kết quả thuận lợi |
| 2 | **Audit effect size nghiên cứu cũ** | Chuẩn hóa effect size và so sánh apples-to-apples cùng sample/outcome/timing/controls/inference | Giữ nhãn `unresolved / inflation suspected` cho đến khi hoàn tất |
| 3 | **Kiểm định chênh lệch beta giữa giai đoạn bằng interaction định trước** | Đánh giá beta stability mà không so p-value rời rạc của hai mẫu nhỏ | Dùng mốc thời gian khóa trước; rolling chart chỉ là diagnostic |

### Hạ ưu tiên hoặc không dùng làm decision rule

- **Raw-p sensitivity:** có thể mô tả, nhưng không được thay Holm. Trong Ch4, raw `p<0,01` ở monthly vẫn chỉ cho F1 và F5, không tạo thêm hit.
- **Rolling 24 tháng:** quá nhiễu; nếu cần minh họa nên dùng 36–48 tháng kèm CI và không dùng để chọn regime hậu nghiệm.
- **Curvature:** đã có exploratory null cho return. Chỉ mở module bổ sung được đăng ký trước cho 5Y–2Y, 20Y–10Y và curvature; chưa cần mở Chương 5.
- **Mở rộng lên 170+ tháng:** chuyển thành long-term monitoring vì cần hơn bốn năm dữ liệu, không khả thi trong report hiện tại.
- **Reverse Granger (scope gap):** Chương 2 chỉ kiểm định chiều bond→equity: 0/150 daily và 0/150 monthly vượt Holm. Chiều equity→bond chưa được đăng ký hoặc kiểm định trong Chương 2; vì vậy không được kết luận chiều ngược là null. Nếu nghiên cứu sau này cần đánh giá phản hồi hai chiều hoặc giả thuyết common driver, phải khóa một hypothesis family mới trước khi chạy. Đây là khoảng trống phạm vi (scope gap), không phải lỗi làm mất hiệu lực verdict bond→equity. Không dùng kết quả Ch4 0/7 hai chiều để thay thế coverage còn thiếu của Ch2.

### Claim bị rút lại hoặc thu hẹp sau review

- Rút lại: `37/90 test có p_raw=0,0000`; thay bằng `37/90 có p_raw<0,001`, không có p bằng 0.
- Rút lại: suy luận rằng số hàng stock-panel rất lớn tự động làm p-value giả; thay bằng `unresolved / inflation suspected`.
- Thu hẹp: `OOS 0/175 stable`; thay bằng `0/140 mô hình đủ depth stable, 35/175 insufficient`.
- Thu hẹp: Layer B không được quy toàn bộ về monthly `n=119`; nhánh daily có effective N hàng nghìn, còn monthly mới bị giới hạn power.
- Sửa: Granger Ch2 không test cả hai chiều. `24_granger_results.csv` có 300 rows, toàn bộ bond→equity; 150/150 là daily/monthly. Đổi `0/150 equity→bond` thành `chiều equity→bond không được test trong Ch2`. Lưu ý: Ch4 granger (0/7) mới mix 2 chiều (4 bond→equity + 3 equity→bond).

---

## 9. File artifact tham chiếu

| File | Vị trí |
|------|--------|
| Ch1 decision summary | `raw_yield_multidimensional_v2_2/outputs/multidimensional_decision_summary.json` |
| Ch2 child results | `bond_equity_chapter2_return_v1/outputs/23_index_child_results_full.csv` |
| Ch2 granger | `bond_equity_chapter2_return_v1/outputs/24_granger_results.csv` |
| Ch2 OOS | `bond_equity_chapter2_return_v1/outputs/28_oos_results.json` |
| Ch3 claim map | `bond_equity_chapter3_volume_v1/outputs/16_claim_evidence_map.json` |
| Ch4 confirmatory | `bond_equity_chapter4_inside_market_v1/outputs/13_confirmatory_results.csv` |
| Ch4 effect sizes | `bond_equity_chapter4_inside_market_v1/outputs/14d_effect_sizes.csv` |
| Ch4 OOS | `bond_equity_chapter4_inside_market_v1/outputs/20_oos_results.json` |
| Ch4 bootstrap validation | `bond_equity_chapter4_inside_market_v1/outputs/12_bootstrap_validation.json` |
| Old study exploratory | `bond_inside_vnindex_v1/outputs/12_stock_panel_exploratory_results.csv` |
| Claim registry | `vn10y-nghien-cuu/qa/claim_registry.json` |
| Source manifest (25 hash) | `vn10y-nghien-cuu/qa/final_synthesis/source_manifest.json` |
