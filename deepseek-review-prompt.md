# PROMPT REVIEW ĐỘC LẬP — DÀNH CHO DEEPSEEK V4 PRO

## CÁCH DÙNG
1. Mở session mới trong ZCode, đổi model sang **DeepSeek V4 Pro**
2. Copy toàn bộ nội dung dưới đây (từ "BẮT ĐẦU" đến hết) dán vào session DeepSeek
3. DeepSeek sẽ đọc 6 báo cáo + research artifacts và trả kết quả review

---

# BẮT ĐẦU

Bạn là DeepSeek V4 Pro. Nhiệm vụ của bạn là **review độc lập** một bộ 6 báo cáo HTML nghiên cứu thị trường Việt Nam. Các báo cáo này do một model khác (GLM-5.2) tạo ra. Mục đích review là bắt lỗi — không phải khen.

## VAI TRÒ

Bạn là **người thẩm định độc lập**. Bạn không tạo báo cáo này. Bạn không có lợi ích gì trong việc bảo vệ chúng. Nhiệm vụ duy nhất của bạn là tìm ra nơi báo cáo sai, mơ hồ, quá mức, hoặc khó hiểu.

Quan trọng: nếu báo cáo đúng, nói đúng. Nếu báo cáo sai, nói sai. Không khen cho đẹp. Không chỉ trích cho có.

## PHẠM VI

### 6 báo cáo HTML cần review

Đọc từng file `index.html` và trích xuất visible text (bỏ CSS/JS/nội dung trong `<details data-layer="technical">`):

| # | Báo cáo | Đường dẫn file HTML | Nguồn nghiên cứu (read-only) |
|---|---|---|---|
| 0 | **Master** (tổng hợp) | `/Users/bobo/ZCodeProject/vn-market-research-master/site/index.html` | Tổng hợp 5 nghiên cứu dưới |
| 1 | **Bond & cổ phiếu** | `/Users/bobo/ZCodeProject/vn10y-nghien-cuu/index.html` | `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/bond_inside_vnindex_v1/` |
| 2 | **Giá, khối lượng, độ rộng** | `/Users/bobo/ZCodeProject/equity-volume-breadth/index.html` | `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/equity_price_volume_breadth_v1/` |
| 3 | **Dự báo đa biến** | `/Users/bobo/ZCodeProject/equity-multivariate-forecast/index.html` | `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/equity_multivariate_index_forecast_v1/` |
| 4 | **Phân kỳ cấp chỉ số** | `/Users/bobo/ZCodeProject/equity-divergence-study/index.html` | `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/equity_divergence_outcomes_v1/` |
| 5 | **Phân kỳ từng cổ phiếu** | `/Users/bobo/ZCodeProject/equity-stock-volume-divergence/index.html` | `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/equity_stock_volume_divergence_v1/` |

### Production URLs (để đối chiếu local vs production)

- Master: https://vn-market-research-master.vercel.app
- Bond: https://vn10y-nghien-cuu.vercel.app
- Breadth: https://equity-volume-breadth.vercel.app
- Multivariate: https://equity-multivariate-forecast.vercel.app
- Divergence chỉ số: https://equity-divergence-study.vercel.app
- Divergence cổ phiếu: https://equity-stock-volume-divergence.vercel.app

## BỐN LỚP KIỂM TRA

### Lớp 1 — CHÍNH XÁC SỐ LIỆU (quan trọng nhất)

Với mỗi báo cáo, đọc file HTML, trích xuất mọi số cụ thể, rồi mở thư mục research tương ứng để đối chiếu. **Mỗi con số trong HTML phải khớp artifact gốc.**

**Danh sách số liệu phải cross-check (bắt buộc):**

*Bản Master:*
- Không có số liệu riêng — tổng hợp từ 5 chuyên khảo. Kiểm tra các con số trích dẫn lại có khớp chuyên khảo gốc không.

*Bản Bond (vn10y):*
- Lợi suất 2 năm tăng 0,10 điểm % → VNINDEX thấp hơn 0,24 điểm % (cùng 5 phiên)
- Khoảng ước lượng: −0,36 đến −0,13 điểm %
- 7 chỉ số theo ngày: VNINDEX, VN30, VNCOND, VNCONS, VNFIN, VNHEAL, VNIT
- VNCOND nhạy nhất: −0,33 điểm %
- VNHEAL ít nhạy nhất: −0,17 điểm %
- 2 chỉ số theo tháng: VNINDEX, VNMAT
- Lợi suất 10 năm theo tháng: VNINDEX −0,71 điểm %, VNMAT −1,29 điểm %
- Độ lan tỏa: hiệu ứng −0,07 điểm % cho mỗi 0,25 điểm % lợi suất tăng
- 144 tháng dữ liệu (120 tháng cho độ lan tỏa)
- "Không tìm thấy lợi suất đi trước cổ phiếu ở bất kỳ tần suất nào"
- 300 cấu hình kiểm tra Granger

*Bản Breadth (giá-khối lượng-độ rộng):*
- 364 phép kiểm tra, 15 chỉ số, 403 mã HOSE
- Giá đi trước khối lượng: 13 kết quả daily + 1 monthly
- Khối lượng đi trước giá: 0 kết quả daily, 1 monthly
- Độ rộng đi trước khối lượng: 8 kết quả
- Độ rộng đi trước VNINDEX: 2 kết quả
- 120 lần kiểm tra ngoài mẫu, 0 lần ổn định
- Phân loại 120: 107 "lúc tốt lúc kém", 1 "kém hơn hẳn", 12 "không đủ dữ liệu", 0 "ổn định"

*Bản Multivariate:*
- Toàn mẫu: Brier improvement 0,035, Holm-adjusted p = 0,0006
- Verdict: PREDICTIVE_INCREMENTAL_UNSTABLE
- Calibration slope = −0,10 (lý tưởng 1,0)
- 98,5% cải thiện đến từ trước 2014
- Từ 2014: Brier improvement = −0,0004
- 2/6 giai đoạn tốt hơn
- Bảng giai đoạn: trước 2014 (+0,1068), 2014–2018 (−0,0015), 2019–2021 (+0,0032), 2022–2026 (−0,0018)
- VNREAL H20: adjusted p = 0,0396
- Breadth: 0 cell sống sót Holm
- Đây là phân tích hậu kỳ, chưa rerun pipeline từ 2014

*Bản Divergence chỉ số:*
- VNINDEX H60 DOWN: effect +4,75% (khoảng 0,046 log-point)
- Khoảng ước lượng: +1,97% đến +7,6%
- Holm-adjusted p ≈ 0,047
- Parent VNINDEX adjusted p ≈ 0,039
- OOS improvement ≈ −0,021
- Fold consistency: 3/6
- 0 DIVERGENCE_WARNING_CANDIDATE
- 4 parent families vượt Holm
- Binary power = 0,355
- 18 breadth OOS partial

*Bân Divergence cổ phiếu:*
- 3.032 trường hợp kiểm tra (KHÔNG PHẢI "3.000")
- 54 nhóm kiểm tra
- Verdict counts: NOT_SUPPORTED=2.995, FIT_FAILED=30, NOT_SUPPORTED_PARENT_GATE_FAIL=4, DESCRIPTIVE_ASSOCIATION_ONLY=3
- 7 cells vượt bước hiệu chỉnh: 3 giữ DESCRIPTIVE, 4 bị parent gate loại
- 30 cổ phiếu OOS, 26.854 predictions
- 13 OK (3 tốt hơn, 10 kém đi), 16 partial, 1 failed
- Primary pooled H60: beta ≈ 0,00694 log return ≈ 0,7%
- CI 95%: khoảng −0,44% đến +1,85%
- raw p = 0,375
- OOS pooled improvement ≈ −0,0003
- 2/6 folds tốt hơn
- Power ≈ 0,46 **← KIỂM TRA KỸ: báo cáo live ghi "0,44", artifact gốc có thể là 0,46**
- AR(1) rejection size ≈ 0,0155
- 110 cổ phiếu HOSE current-active
- Corporate actions: 140 sự kiện, độ nhảy trung vị 0,27108 → 0,26849
- 138 sự kiện đánh giá được: 67 tốt hơn/không đổi, 71 xấu hơn
- Master status: CLOSEOUT_INCONCLUSIVE_POWER_LIMITED

**Quy tắc cross-check:** Mở file `outputs/` trong research project, tìm artifact JSON/CSV tương ứng, đối chiếu từng số. Báo mỗi mismatch với: số trong HTML / số trong artifact / chênh lệch.

### Lớp 2 — VĂN PHONG BÌNH DÂN

Với mỗi báo cáo, trích xuất visible text (sau khi bỏ CSS/JS và nội dung trong `<details data-layer="technical">`). Quét xem các thuật ngữ sau có xuất hiện NGOÀI technical details không:

```
Holm, FWER, BH, bootstrap, dependent-wild, panel, parent omnibus,
child test, beta, log-point, p-value, raw_p, adjusted_p, OOS,
materiality, FIT_FAILED, survivorship-limited, Monte Carlo, AR(1),
confidence interval, null hypothesis, Granger, Brier, calibration slope,
R², regression, OLS, t-statistic, SE
```

Ngoài ra, kiểm tra các nhãn quy trình nội bộ có lộ ra hero/phần đọc chính không:
- "R6", "R4", "Session 2", "R2" — đây là nhãn vòng sửa nội bộ, không nên xuất hiện ngoài technical details

**Quy tắc:** Nếu thuật ngữ xuất hiện trong `<details data-layer="technical">`, đó là OK. Nếu xuất hiện ngoài, đó là violation. Báo mỗi violation với: thuật ngữ / vị trí (section nào) / câu chứa nó.

### Lớp 3 — LOGIC & OVERCLAIM

Với mỗi báo cáo, kiểm tra:

**Overclaim (nói quá):**
- Có chỗ nào biến "liên hệ trong mẫu" thành "dự báo" không?
- Có chỗ nào biến "phát hiện đáng chú ý" thành "tín hiệu giao dịch" không?
- Có chỗ nào nói "chứng minh", "chắc chắn", "luôn", "tín hiệu mua", "tín hiệu bán" không?
- Có chỗ nào gán nhân quả ("lợi suất tăng LÀM cổ phiếu giảm") không?
- Có chỗ nào gọi "current-active universe" là "đại diện toàn bộ lịch sử HOSE" không?

**Underclaim (nói thiếu):**
- Có chỗ nào kết quả âm bị giấu không?
- Có chỗ nào giới hạn power bị bỏ qua không?
- Có chỗ nào "FIT_FAILED" bị diễn giải thành "không có hiệu ứng" không?

**Minh bạch khái niệm (đặc biệt quan trọng):**
- Phân biệt "đi cùng" (cùng kỳ) vs "đi trước" (dự báo) có được giải thích ĐỦ không?
- Người đọc phổ thông có hiểu được vì sao "đi cùng" không giúp giao dịch không?
- Có chỗ nào lặp nhãn (vd: "CÙNG KỲ — KHÔNG PHẢI DỰ BÁO") mà không giải thích lý do không?
- Khái niệm "power hạn chế" / "khả năng bỏ sót hiệu ứng nhỏ" có được giải thích bình dân không?

### Lớp 4 — NHẤT QUÁN GIỮA 6 BÁO CÁO

- Các con số trích dẫn lại giữa master và chuyên khảo có khớp không?
- Cách dùng thuật ngữ có nhất quán không (vd: "vol" = khối lượng, không phải volatility)?
- Độ dài có quá chênh lệch không? (đặc biệt: stock-divergence chỉ ~4.300 ký tự visible — có quá mỏng không?)
- Thông điệp trung tâm có mâu thuẫn giữa master và chuyên khảo không?

## OUTPUT — ĐỊNH DẠNG BẮT BUỘC

Trả kết quả theo đúng cấu trúc sau. Không thêm phần thừa.

```
# REVIEW ĐỘC LẬP — DEEPSEEK V4 PRO

## TÓM TẮT
- Tổng số vấn đề nghiêm trọng: [số]
- Tổng số vấn đề nhẹ: [số]
- Khuyến nghị tổng thể: [PASS / PASS_CÓ_GHI_CHÚ / CẦN_SỬA / CẦN_SỬA_LỚN]
- 1 câu cảm nhận chung: [...]

## LỚP 1 — CHÍNH XÁC SỐ LIỆU

### Báo cáo Bond (vn10y)
[Mỗi dòng: claim trong HTML | giá trị trong artifact | MATCH / MISMATCH | chi tiết]
[...]

### Báo cáo Breadth
[...]

### Báo cáo Multivariate
[...]

### Báo cáo Divergence chỉ số
[...]

### Báo cáo Divergence cổ phiếu
[ĐẶC BIỆT kiểm tra power 0,44 vs 0,46]
[...]

### Cross-check Master vs chuyên khảo
[...]

## LỚP 2 — VĂN PHONG BÌNH DÂN

### Báo cáo [tên]
- Violations: [số]
- Chi tiết: [thuật ngữ / vị trí / câu]
[...]

## LỚP 3 — LOGIC & OVERCLAIM

### Overclaim tìm thấy
[Mỗi dòng: báo cáo / vị trí / câu / vì sao quá mức]

### Underclaim tìm thấy
[...]

### Minh bạch khái niệm
- "Đi cùng vs đi trước" được giải thích đủ không: [CÓ / KHÔNG / MỘT PHẦN] + lý do
- "Power hạn chế" được giải thích bình dân không: [CÓ / KHÔNG]
- Khái niệm nào khác người đọc phổ thông sẽ bối rối: [...]

## LỚP 4 — NHẤT QUÁN GIỮA 6 BÁO CÁO
[Mỗi dòng: loại không nhất quán / vị trí / chi tiết]

## 5 VẤN ĐỀ NGHIÊM TRỌNG NHẤT (xếp theo độ ưu tiên)
1. [...]
2. [...]
3. [...]
4. [...]
5. [...]

## ĐIỂM MẠNH ĐÁNG GIỮ (không phải khen, là nhận diện tài sản)
1. [...]
2. [...]
3. [...]

## KẾT LUẬN
[2–3 câu: bộ báo cáo này đáng tin đến đâu, cần sửa gì trước khi dùng]
```

## QUY TẮC

1. **Đọc thật trước khi đánh giá.** Không review dựa trên tiêu đề hay meta. Mở file, đọc visible text.
2. **Mở artifact thật.** Không đoán số liệu. Mở `outputs/*.json` trong research project để cross-check.
3. **Nói cụ thể.** Mỗi vấn đề phải có: báo cáo nào, vị trí nào, câu nào, vì sao sai.
4. **Phân biệt nghiêm trọng vs nhẹ.** Số liệu sai = nghiêm trọng. Lặp cảnh báo hơi nhiều = nhẹ.
5. **Không khen cho đẹp.** Nếu báo cáo tốt ở điểm nào, ghi vào "Điểm mạnh đáng giữ" — ngắn gọn.
6. **Không bị ảnh hưởng bởi nhận xét của model khác.** Đây là review của BẠN. Nếu bạn thấy báo cáo tốt, nói tốt. Nếu thấy sai, nói sai.

Bắt đầu review ngay. Đọc cả 6 file HTML + mở research artifacts. Không dừng giữa chừng để hỏi.
