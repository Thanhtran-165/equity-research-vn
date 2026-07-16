# Lệnh cho GLM: viết lại báo cáo HTML VN10Y theo kết quả đã nghiệm thu

Làm việc tại:

`/Users/bobo/ZCodeProject/vn10y-nghien-cuu`

File đầu ra duy nhất cần thay đổi:

`/Users/bobo/ZCodeProject/vn10y-nghien-cuu/index.html`

Đây là nhiệm vụ **biên tập và tái cấu trúc báo cáo**, không phải nhiệm vụ nghiên cứu mới. Không chạy lại mô hình, không sửa dữ liệu, không thay contract và không tự tạo thêm kết luận.

## 1. Mục tiêu nội dung

Viết lại báo cáo để trả lời rõ một kết luận trung tâm:

> Biến động lợi suất trái phiếu Việt Nam chưa đủ ổn định để dự báo thị trường cổ phiếu. Bond phù hợp hơn với vai trò tín hiệu bối cảnh hoặc “đèn vàng” quản trị rủi ro, và chỉ có ý nghĩa thực tế khi được đọc cùng độ rộng giá, khối lượng và trạng thái thị trường cổ phiếu.

Phải phân biệt ba khái niệm:

1. **Bối cảnh cảnh báo:** bond biến động mạnh khiến nhà đầu tư nên kiểm tra thêm trạng thái thị trường.
2. **Dự báo:** bond tự dự báo được hướng đi hoặc drawdown tương lai — nghiên cứu hiện không xác nhận điều này.
3. **Tín hiệu giao dịch:** điều kiện đủ để mua/bán — tuyệt đối không được tuyên bố.

Ngôn ngữ chính dành cho nhà đầu tư phổ thông. Phần thân bài giải thích bằng tiếng Việt tự nhiên; thuật ngữ thống kê chi tiết chuyển xuống phụ lục.

## 2. Nguồn sự thật duy nhất

Trước khi sửa HTML, đọc trực tiếp các artifact sau. Không lấy số từ trí nhớ, chat log hoặc HTML cũ.

### 2.1 Benchmark cấp index

- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/raw_yield_multidimensional_v2_2/outputs/multidimensional_decision_summary.json`
- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/raw_yield_multidimensional_v2_2/outputs/multidimensional_audit_manifest.json`
- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/raw_yield_multidimensional_v2_2/outputs/raw_yield_validation_results.csv`
- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/raw_yield_multidimensional_v2_2/outputs/stress_validation_results.csv`
- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/raw_yield_multidimensional_v2_2/outputs/oos_results.json`

Các headline được phép:

- Raw yield confirmatory: `0/90` Holm-significant.
- Stress composite supplementary: `0/42` Holm-significant.
- Stress index chỉ là nghiên cứu bổ sung; không được thay raw yield làm câu hỏi chính.
- Không có bằng chứng OOS ổn định để biến bond thành công cụ dự báo độc lập.

Không cần đưa structural-break cấp index vào headline. Nếu nhắc trong phụ lục, phải phân biệt joint-equation break với slope break; không gọi joint break là độ nhạy yield ổn định.

### 2.2 Daily market internals

- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/bond_inside_market_daily_completion_v1/outputs/18_review_bundle.json`
- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/bond_inside_market_daily_completion_v1/outputs/17_claim_evidence_map.json`
- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/bond_inside_market_daily_completion_v1/outputs/09_confirmatory_results.csv`
- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/bond_inside_market_daily_completion_v1/outputs/12_structural_breaks.json`
- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/bond_inside_market_daily_completion_v1/outputs/14_oos_results.json`
- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/bond_inside_market_daily_completion_v1/outputs/15_alert_results.json`

Headline được phép:

- Confirmatory `0/6`.
- Corrected slope break `0/6`, joint break `0/6`.
- OOS bond cải thiện `0/6` outcome.
- Alert độc lập có holdout counts `10, 3, 2, 12`; đây là sensitivity thăm dò, không phải xác suất dự báo đã xác nhận.
- Combined confirmation với price/volume còn mỏng; không operational.

### 2.3 Monthly market internals

- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/bond_inside_market_monthly_v1/outputs/18_review_bundle.json`
- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/bond_inside_market_monthly_v1/outputs/17_claim_evidence_map.json`
- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/bond_inside_market_monthly_v1/outputs/09_confirmatory_results.csv`
- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/bond_inside_market_monthly_v1/outputs/12_structural_breaks.json`
- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/bond_inside_market_monthly_v1/outputs/13_daily_monthly_comparison.json`
- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/bond_inside_market_monthly_v1/outputs/14_oos_results.json`
- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/bond_inside_market_monthly_v1/outputs/15_alert_results.json`
- `/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research/bond_inside_market_monthly_v1/outputs/01b_cache_provenance.json`

Headline được phép:

- 150 tháng dữ liệu, 120 tháng đạt coverage phân tích, 403 cổ phiếu current-active HOSE.
- Confirmatory `0/6`.
- Corrected slope break `0/6`, joint break `0/6`.
- OOS cải thiện `2/6`, không ổn định nên `NOT OPERATIONAL`.
- Independent monthly alert counts `1, 2, 1, 2`, quá mỏng để diễn giải xác suất.
- Monthly không “cứu” kết quả daily; cả hai đều không có bằng chứng confirmatory.

## 3. Việc bắt buộc làm trước khi sửa HTML

Tạo file:

`qa/claim_registry.json`

Mỗi claim public phải có:

```json
{
  "claim_id": "...",
  "public_sentence": "...",
  "source_file": "/absolute/path/to/artifact",
  "source_field_or_rows": "...",
  "status": "confirmatory|exploratory|limitation",
  "allowed_in_main_text": true,
  "caveat": "..."
}
```

Không sửa HTML cho tới khi registry có ít nhất các claim:

- Index raw yield `0/90`.
- Stress supplementary `0/42`.
- Daily internals `0/6`, OOS `0/6`.
- Monthly internals `0/6`, OOS `2/6 unstable`.
- Structural daily/monthly đều slope `0/6`, joint `0/6`.
- Universe current-active HOSE, không PIT.
- EW–VNINDEX là proxy.
- Daily và monthly dùng hai stock snapshots khác nhau; so sánh chỉ mang tính phương pháp.

## 4. Những nội dung cũ phải loại bỏ

Không dùng `index.html.bak`, `index.html.bak2` hoặc `index.html.v1_final_backup` làm nguồn nội dung.

Xóa khỏi public report nếu không map được về artifact mới:

- `β monthly = −6,92%/pp` và `R² = 10,7%`.
- Claim `5/23 chỉ báo monthly còn ý nghĩa`.
- Claim “ngành tài chính/ngân hàng nhạy nhất”.
- Bảng xếp hạng ngành.
- So sánh Việt Nam/Mỹ/Trung Quốc/Nhật Bản.
- Country chart và sector chart.
- Mọi câu nói monthly có `4/6 slope breaks`.
- Mọi lift, precision hoặc xác suất alert được suy từ mẫu quá mỏng.
- Mọi câu “yield tăng sẽ làm thị trường giảm”, “bond dự báo drawdown” hoặc tương đương.

Không được đổi những câu trên thành cách diễn đạt mềm hơn để giữ lại. Phải xóa nếu không còn bằng chứng.

## 5. Cấu trúc báo cáo mới

Giữ phong cách bài nghiên cứu HTML tối giản, tối màu và dễ đọc hiện tại; không biến thành dashboard vận hành. Mục tiêu khoảng 2.800–3.800 từ, 7 phần rõ ràng.

### Hero — câu trả lời trong 90 giây

Tiêu đề gợi ý:

`Lợi suất trái phiếu và cổ phiếu Việt Nam`

Phụ đề:

`Một tín hiệu bối cảnh rủi ro, không phải cỗ máy dự báo`

Ba thẻ tóm tắt:

1. **Điều tìm thấy:** có những liên hệ mô tả, nhưng không có quan hệ confirmatory ổn định.
2. **Điều không tìm thấy:** bond không cải thiện dự báo OOS một cách nhất quán.
3. **Cách dùng hợp lý:** xem bond như đèn vàng và kiểm tra thêm breadth/volume của thị trường cổ phiếu.

### Phần 1 — Câu hỏi thực sự là gì?

Giải thích sự khác nhau giữa tương quan, cảnh báo, dự báo và tín hiệu giao dịch. Nói rõ nghiên cứu được mở rộng từ bề mặt index sang cấu trúc bên trong thị trường.

### Phần 2 — Khi chỉ nhìn vào index

Trình bày benchmark raw yield và stress supplementary. Nói dễ hiểu rằng các dấu hiệu ban đầu có thể trông hợp lý nhưng không sống sót qua kiểm định chặt và OOS.

Không biến phần này thành danh sách 90 phép thử. Chỉ dùng một bảng bằng chứng ngắn.

### Phần 3 — Nhìn vào bên trong thị trường theo ngày

Giải thích các khái niệm bằng ngôn ngữ phổ thông:

- Bao nhiêu cổ phiếu cùng tăng/giảm.
- Bao nhiêu mã còn đứng trên các đường trung bình.
- Cổ phiếu bình quân so với VNINDEX.
- Khối lượng tăng/giảm và mức độ tham gia.

Kết luận: `0/6 confirmatory`, `0/6 OOS`; chưa đủ để biến bond thành cảnh báo tự động.

### Phần 4 — Khi kéo góc nhìn ra theo tháng

Giải thích vì sao monthly từng có vẻ hứa hẹn: giảm nhiễu ngắn hạn và gần với kênh discount-rate hơn. Sau đó nói thẳng rằng kiểm định mới vẫn cho `0/6`; OOS chỉ `2/6` và không ổn định.

Phải viết rõ: “monthly không cứu giả thuyết”, không nói “monthly yếu hơn” hay “mạnh hơn” chỉ dựa vào p-value.

### Phần 5 — Vì sao bond phù hợp làm đèn vàng hơn dự báo?

Giải thích:

- Bond phản ánh nhiều lực cùng lúc: lạm phát, thanh khoản, kỳ vọng chính sách, cung cầu TPCP.
- Một biến động bond có thể xuất hiện mà cổ phiếu chưa phản ứng cùng cách.
- Alert hiếm và mẫu holdout mỏng.
- Không có cải thiện OOS ổn định.

Kết luận: bond có thể khiến nhà đầu tư **kiểm tra thêm**, nhưng không đủ để quyết định thay họ.

### Phần 6 — Cách sử dụng thực tế

Đưa ra quy trình quan sát ba bước, không phải rule giao dịch:

1. Bond biến động bất thường → bật trạng thái theo dõi.
2. Kiểm tra breadth giá: tỷ lệ mã suy yếu, MA, EW–VNINDEX proxy, dispersion.
3. Kiểm tra volume: down-volume, participation, abnormal volume.

Chỉ khi nhiều lớp cùng xấu đi mới tăng mức thận trọng. Không đưa ngưỡng BUY/SELL và không hứa xác suất.

Thêm hộp “Không nên làm”:

- Không bán chỉ vì yield tăng.
- Không mua chỉ vì yield giảm.
- Không dùng bond để định thời điểm thị trường.

### Phần 7 — Giới hạn và cách đọc kết quả

Nội dung bắt buộc:

- Universe là current-active HOSE, có survivorship limitation.
- Không phải PIT/historical VNINDEX constituents.
- EW–VNINDEX gap là proxy.
- Daily và monthly khác stock snapshot; comparison là methodological.
- Alert depth mỏng.
- “Không tìm thấy bằng chứng xác nhận” không đồng nghĩa “không có quan hệ”.

Đưa HAC, dependent-wild bootstrap, Holm/BH và structural-break chi tiết vào `<details>` trong phụ lục. Không để phương pháp thống kê lấn át phần đọc chính.

## 6. Hình ảnh và biểu đồ

Xóa toàn bộ chart cũ không còn nguồn: `chartCurve`, `chartBreadth` cũ nếu chứa claim cũ, `chartSector`, `chartCountry`.

Tối đa ba visual mới:

1. **Ba lớp bằng chứng:** index benchmark / daily internals / monthly internals dưới dạng evidence matrix, ưu tiên HTML thay vì chart nếu toàn bộ confirmatory đều bằng 0.
2. **OOS:** daily `0/6`, monthly `2/6 nhưng không ổn định`; phải ghi chú rõ “không phải tỷ lệ thành công”.
3. **Độ sâu alert:** daily independent `10/3/2/12`, monthly `1/2/1/2`, kèm chú thích sample size chứ không diễn giải xác suất.

Không vẽ chart p-value để tạo cảm giác chính xác giả. Không dùng hiệu ứng 3D, gradient sặc sỡ hoặc quá nhiều KPI card.

Mọi canvas phải có đúng một `new Chart(...)`. Không được có Chart constructor trỏ tới ID không tồn tại.

## 7. Quy tắc văn phong

- Thuần tiếng Việt, câu ngắn, trực tiếp.
- Giải thích thuật ngữ ngay lần đầu xuất hiện.
- Ưu tiên “độ rộng thị trường” thay cho chỉ viết `breadth`.
- Ưu tiên “kiểm tra trên dữ liệu ngoài mẫu” thay cho chỉ viết `OOS`.
- Không dùng giọng quảng cáo hoặc giọng chắc chắn quá mức.
- Không viết như báo cáo log nội bộ.
- Không lặp các câu “nghiên cứu cho thấy” liên tục.
- Không biến phần giới hạn thành lời phủ nhận toàn bộ giá trị nghiên cứu.

## 8. Quy tắc claim cứng

Các câu sau bị cấm:

- `bond dự báo thị trường`
- `yield tăng khiến cổ phiếu giảm`
- `xác suất drawdown tăng ...` nếu lấy từ alert mỏng
- `tín hiệu mua`, `tín hiệu bán`
- `quan hệ nhân quả`
- `không có quan hệ`
- `monthly xác nhận`
- `ngành ... nhạy nhất`

Cách viết null đúng:

`Nghiên cứu chưa tìm thấy bằng chứng xác nhận đủ ổn định trong phạm vi dữ liệu hiện có.`

## 9. QA bắt buộc

Sau khi viết xong:

1. Kiểm tra chỉ có một `<html>`, `<head>`, `<body>`.
2. Tất cả `id` là duy nhất; mọi anchor hoạt động.
3. Số `<canvas>` bằng số `new Chart` và mọi ID khớp.
4. Không còn các claim cũ bị cấm ở Mục 4.
5. Không còn `4/6 slope breaks`.
6. Các số `0/90`, `0/42`, daily `0/6`, monthly `0/6`, OOS `0/6` và `2/6` phải map về registry.
7. Kiểm tra chính tả tiếng Việt và dấu câu.
8. Không horizontal overflow tại 390px, 768px và 1440px.
9. Chụp screenshot toàn trang ở mobile và desktop bằng Playwright nếu có.
10. Kiểm tra print layout cơ bản; không cắt bảng hoặc chart.

Tạo:

- `qa/claim_registry.json`
- `qa/rewrite_audit.json`
- `qa/screenshots/desktop.png`
- `qa/screenshots/mobile.png`

`rewrite_audit.json` phải ghi:

- Word count.
- Section count.
- Canvas count và Chart count.
- Danh sách claim bị xóa.
- Danh sách claim public và source artifact.
- Forbidden-phrase scan.
- Responsive QA status.
- Final status `PASS` hoặc `BLOCKED`.

## 10. Phạm vi file và an toàn

- Không sửa bất kỳ file nào trong `ResearchLab/research/**`.
- Không sửa các backup HTML.
- Tạo một backup mới `index.html.pre_risk_warning_rewrite` trước khi thay, nhưng không dùng backup làm nguồn.
- Không deploy Vercel trong nhiệm vụ này.
- Không gọi AI khác.
- Không tải dữ liệu ra Internet.

## 11. Phản hồi cuối tiết kiệm token

Chỉ trả về 8 dòng:

```text
1. STATUS: PASS/BLOCKED.
2. FILE: index.html path, word count, sections.
3. CLAIMS: registry count, unresolved claims.
4. REMOVED: số claim/chart cũ đã xóa.
5. EVIDENCE: index/daily/monthly headline counts.
6. VISUAL_QA: canvas/chart count, desktop/mobile status.
7. FORBIDDEN_SCAN: PASS/FAIL.
8. OPEN: file:// absolute path hoặc local preview URL; không deploy.
```

Nếu có bất kỳ unresolved claim hoặc forbidden claim nào, status phải là `BLOCKED`; không tự gọi bản HTML là final.

