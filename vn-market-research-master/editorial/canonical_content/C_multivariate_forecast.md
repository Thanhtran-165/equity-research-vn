# Thử dự báo đa biến: một kết quả đẹp chưa đủ thành công cụ

## Câu trả lời ngắn

Nghiên cứu thử trả lời một câu hỏi thực tế: nếu mô hình đã biết diễn biến giá gần đây, việc thêm khối lượng có giúp dự báo hướng VNINDEX tốt hơn không? Ở khoảng năm phiên, kết quả tổng hợp cho thấy sai số giảm đáng kể. Nhưng lợi ích chỉ xuất hiện ở hai trong sáu giai đoạn kiểm tra, xác suất mô hình nói ra không khớp tốt với thực tế và phần lớn cải thiện tập trung ở dữ liệu cũ.

Kết luận vì vậy có hai vế. **Có một dấu vết lịch sử đáng nghiên cứu. Chưa có công cụ đủ ổn định để dùng hiện nay.** [C-70] [C-72]

> **Phát hiện:** Thêm khối lượng từng cải thiện kết quả tổng hợp ở khoảng năm phiên.
>
> **Ranh giới:** Kết quả không lặp đều qua thời gian, nên không được nâng thành tín hiệu giao dịch.

## Mô hình đã được hỏi điều gì?

Hãy hình dung hai người dự báo cùng một câu hỏi: VNINDEX sẽ tăng hay không trong khoảng năm phiên tới?

Người thứ nhất chỉ nhìn thông tin từ giá. Đây là mô hình tham chiếu. Người thứ hai nhìn cùng thông tin giá và được xem thêm dữ liệu khối lượng. Nếu người thứ hai liên tục dự báo tốt hơn trên phần dữ liệu chưa dùng để xây mô hình, ta mới có lý do nói khối lượng mang thêm giá trị.

So sánh này quan trọng hơn việc hỏi một mô hình có “đúng nhiều” hay không. Thị trường vốn có tỷ lệ phiên tăng và giảm không cân bằng hoàn toàn; một mô hình đơn giản đôi khi đã có kết quả khá. Câu hỏi đúng là phần thông tin mới có cải thiện được một chuẩn hợp lý hay không.

Nghiên cứu còn xem các khoảng ngắn, trung và dài hơn, ở dữ liệu ngày lẫn tháng. Kết quả đáng chú ý nhất nằm ở khoảng năm phiên của VNINDEX. Các khoảng còn lại không cho thấy giá trị bổ sung đủ mạnh trong thiết kế đã khóa.

## Vì sao kết quả năm phiên từng gây chú ý?

Khi gộp toàn bộ các dự báo ngoài mẫu, mô hình có thêm khối lượng giảm sai số xác suất đủ nhiều để vượt hai cổng ban đầu: mức cải thiện không quá nhỏ và khó giải thích bằng dao động ngẫu nhiên đơn giản. [C-70]

Nếu chỉ nhìn con số tổng hợp, người đọc dễ kết luận rằng khối lượng đã giúp dự báo. Nhưng một mô hình dùng trong thực tế cần hơn một trung bình đẹp. Nó phải giữ được lợi ích qua nhiều giai đoạn, đưa ra xác suất có ý nghĩa và không phụ thuộc gần như hoàn toàn vào một thời kỳ xa xưa.

Ba kiểm tra tiếp theo đều không đạt:

1. **Độ lặp lại:** Chỉ hai trong sáu giai đoạn cho kết quả tốt hơn mô hình chỉ dùng giá. [C-72]
2. **Độ tin cậy của xác suất:** Khi mô hình nói khả năng tăng cao hơn, kết quả thực tế không tăng tương ứng. Xác suất vì thế không thể được đọc theo nghĩa trực tiếp.
3. **Mức tập trung theo thời kỳ:** Phần lớn lợi ích tổng hợp đến từ giai đoạn trước 2014, khi cấu trúc thị trường Việt Nam khác đáng kể hiện nay.

Một kết quả có thể vượt kiểm tra thống kê ban đầu nhưng vẫn thất bại về khả năng sử dụng. Đây chính là trường hợp đó.

## “Hai trong sáu giai đoạn” nghĩa là gì?

Thay vì xây mô hình một lần trên toàn bộ lịch sử rồi chấm điểm trên chính dữ liệu đó, nghiên cứu mô phỏng cách sử dụng theo thời gian. Mô hình học từ quá khứ, dự báo phần tiếp theo, rồi cửa sổ huấn luyện được mở rộng. Quá trình tạo ra sáu giai đoạn đánh giá nối tiếp nhau.

Nếu khối lượng thực sự mang giá trị ổn định, ta kỳ vọng mô hình có thêm khối lượng tốt hơn ở phần lớn các giai đoạn. Kết quả chỉ hai giai đoạn tốt hơn cho thấy trung bình chung bị kéo bởi một số đoạn thuận lợi. Bốn giai đoạn còn lại không xác nhận lợi ích.

Điều này gần với trải nghiệm đầu tư hơn một con số duy nhất. Một chiến lược có lợi nhuận tốt nhờ một năm đặc biệt nhưng kém ở nhiều năm khác không thể được đánh giá như một công cụ ổn định. Mô hình dự báo cũng vậy.

## Vì sao xác suất mô hình không đáng tin?

Giả sử mô hình thường đưa ra các mức 60%, 70% hoặc 80% cho khả năng tăng. Một mô hình được căn chỉnh tốt phải có quan hệ hợp lý giữa mức xác suất và tần suất thực tế. Nhóm dự báo cao hơn cần tăng thường xuyên hơn nhóm dự báo thấp.

Trong kết quả hiện hành, quan hệ đó rất yếu và có dấu hiệu đảo chiều. Vì vậy, con số “80%” không thể được hiểu là cứ mười trường hợp thì khoảng tám trường hợp tăng. Đây là thất bại quan trọng đối với một công cụ ra quyết định, ngay cả khi điểm số tổng hợp từng tốt hơn.

Nhà đầu tư không chỉ cần mô hình xếp hạng đúng; họ còn cần biết mức tự tin có ý nghĩa gì. Nếu xác suất không đáng tin, việc dùng nó để tăng giảm tỷ trọng sẽ tạo cảm giác chính xác giả.

## Vai trò của giai đoạn trước 2014

Kết quả tổng hợp chủ yếu được tạo bởi dữ liệu trước 2014. Thị trường giai đoạn đó có quy mô, thành phần nhà đầu tư, thanh khoản và cơ chế vận hành khác hiện nay. Điều này không làm dữ liệu cũ “vô nghĩa”, nhưng làm giảm khả năng chuyển kết quả sang bối cảnh mới.

Phân tích sau đó chỉ nhìn các dự báo có ngày đánh giá từ 2014 trở đi cho thấy lợi ích không còn. Tuy nhiên, đây là phân tích hậu kỳ trên các dự báo đã được tạo từ quy trình toàn mẫu. Một số mô hình vẫn có thể học từ dữ liệu trước 2014. Vì vậy, nó chưa phải một nghiên cứu mới trong đó cả huấn luyện lẫn đánh giá đều bắt đầu từ năm 2014.

Cách kết luận đúng là: **kết quả hiện hành không cho thấy giá trị ứng dụng trong phần đánh giá hiện đại hơn**. Không được nói nghiên cứu đã chạy lại hoàn chỉnh trên thị trường sau 2014.

## Một tình huống sử dụng mô hình

Giả sử bảng điều khiển hiển thị xác suất VNINDEX tăng trong năm phiên tới là 72%, cao hơn mức thông thường. Người dùng có thể bị thúc đẩy tăng vị thế.

Trước khi hành động, cần hỏi:

- Mô hình này có tốt hơn chuẩn chỉ dùng giá trong giai đoạn gần đây không?
- Kết quả có lặp qua nhiều giai đoạn hay tập trung ở một đoạn cũ?
- Khi mô hình từng nói 70%, thị trường thực tế tăng với tần suất nào?
- Lợi ích có còn sau chi phí, độ trễ và thay đổi cấu trúc thị trường không?

Với nghiên cứu hiện hành, ba câu hỏi đầu chưa được trả lời theo hướng đủ tốt để vận hành. Vì vậy con số 72% không nên được hiển thị như một xác suất có thể tin trực tiếp. Tình huống này là minh họa cho quy trình đọc kết quả, không phải dự báo mới.

## Ví dụ giả định: vì sao một con số trung bình đẹp vẫn có thể gây thiệt hại

> **MINH HỌA GIẢ ĐỊNH — KHÔNG PHẢI KẾT QUẢ NGHIÊN CỨU**

Giả sử một mô hình được kiểm tra qua sáu giai đoạn. Trong hai giai đoạn đầu, nó tốt hơn chuẩn rất nhiều. Trong bốn giai đoạn sau, nó chỉ ngang hoặc kém hơn. Khi cộng toàn bộ dự báo lại, hai giai đoạn thuận lợi vẫn đủ kéo điểm trung bình lên mức đẹp.

Nếu nhà đầu tư chỉ nhìn điểm trung bình, họ có thể tưởng lợi thế xuất hiện đều đặn. Nhưng nếu bắt đầu sử dụng mô hình đúng vào một trong bốn giai đoạn kém, trải nghiệm thực tế sẽ hoàn toàn khác. Họ không nhận được “kết quả trung bình của toàn lịch sử”; họ chỉ sống qua đoạn thị trường đang diễn ra.

Ví dụ này cho thấy hai khái niệm phải được tách riêng:

- **Hiệu quả gộp:** kết quả khi cộng tất cả dự báo ở mọi giai đoạn.
- **Độ ổn định:** lợi ích có xuất hiện ở phần lớn các giai đoạn hay không.

Một công cụ vận hành cần cả hai. Hiệu quả gộp giúp phát hiện một dấu vết đáng nghiên cứu. Độ ổn định mới cho biết dấu vết đó có đủ đáng tin để đưa vào quyết định lặp lại hay không.

Trong nghiên cứu này, kết quả năm phiên đạt vế đầu nhưng thất bại ở vế thứ hai. Vì thế cách gọi phù hợp là “cải thiện tổng hợp nhưng không ổn định”, không phải “mô hình dự báo thành công”.

## Đọc mô hình như một cuộc thi có trọng tài

Một lỗi phổ biến là hỏi mô hình mới dự báo đúng bao nhiêu lần. Câu hỏi đó thiếu trọng tài. Nếu thị trường tăng trong 56% số trường hợp, một dự báo luôn nói “tăng” đã đúng 56% mà không cần hiểu bất kỳ điều gì.

Nghiên cứu vì vậy đặt hai mô hình lên cùng sân:

1. Mô hình tham chiếu đã biết lịch sử giá.
2. Mô hình mở rộng biết đúng phần giá đó và được xem thêm khối lượng.

Cả hai phải dự báo cùng ngày, cùng khoảng tương lai và được chấm bằng cùng thước đo. Chỉ khi mô hình mở rộng tốt hơn mô hình tham chiếu, ta mới nói phần khối lượng mang thêm thông tin. Nếu nó chỉ tốt hơn một dự báo ngây thơ nhưng không tốt hơn mô hình giá, đóng góp của khối lượng chưa được chứng minh.

Đây là nguyên tắc có thể áp dụng cho mọi dự án phân tích đang vận hành. Khi muốn thêm độ rộng, tin tức, dữ liệu phái sinh hoặc chỉ báo kỹ thuật, không nên hỏi biến mới có liên hệ với thị trường hay không. Hãy hỏi nó có cải thiện được chuẩn hiện hữu trên cùng tập dự báo hay không.

## Ba lớp câu hỏi mà một dashboard phải tách riêng

### Lớp 1: Mô hình đang nói gì?

Đây là đầu ra dễ thấy nhất: xác suất tăng, dự báo lợi suất hoặc nhãn xu hướng. Nó trả lời “mô hình hiện nghiêng về hướng nào?”.

### Lớp 2: Mô hình có đáng tin ở mức nào?

Lớp này hiển thị lịch sử so sánh với chuẩn, độ lặp lại theo thời gian và mức khớp giữa xác suất với tần suất thực tế. Nó trả lời “đầu ra vừa thấy có từng hoạt động nhất quán hay không?”.

### Lớp 3: Điều gì khiến kết quả không còn áp dụng?

Lớp cuối ghi rõ thời kỳ dữ liệu, thay đổi cấu trúc thị trường, mức thiếu dữ liệu và những điều nghiên cứu chưa kiểm tra. Nó trả lời “khi nào người dùng phải hạ mức tin cậy?”.

Một giao diện chỉ có lớp 1 tạo cảm giác chắc chắn giả. Một giao diện có đủ ba lớp biến mô hình từ máy phát tín hiệu thành công cụ hỗ trợ phán đoán. Với nghiên cứu hiện hành, lớp 1 có thể được giữ trong môi trường nghiên cứu, nhưng lớp 2 và lớp 3 phải luôn hiển thị vì chúng đang chứa các cảnh báo quyết định.

## Cách đọc bốn loại biểu đồ trong chương này

### Biểu đồ so sánh sai số

Thanh “có thêm khối lượng” thấp hơn thanh “chỉ dùng giá” nghĩa là sai số trung bình nhỏ hơn. Nó không nói mô hình đoán đúng mọi lần và không chuyển trực tiếp thành số điểm phần trăm lợi nhuận. Trước khi kết luận, cần xem mức chênh có vượt ngưỡng thực tế và có lặp theo thời gian không.

### Biểu đồ sáu giai đoạn

Mỗi cột đại diện cho một đoạn đánh giá nối tiếp. Cột tốt hơn cho biết mô hình mở rộng thắng chuẩn trong đoạn đó; cột kém hơn cho biết nó thua. Đây là biểu đồ quan trọng nhất đối với người dùng thực tế vì nó phơi bày sự không đều mà điểm trung bình có thể che khuất.

### Biểu đồ xác suất dự báo và tần suất thực tế

Nếu mô hình được căn chỉnh tốt, nhóm dự báo cao hơn phải đi cùng tần suất tăng cao hơn theo trật tự hợp lý. Khi đường thực tế phẳng hoặc đi ngược, con số xác suất không nên được đọc theo nghĩa trực tiếp. Nó có thể vẫn là một điểm số xếp hạng, nhưng không phải “xác suất thật” để đặt quy mô vị thế.

### Biểu đồ theo thời kỳ

Biểu đồ này không nhằm chứng minh nguyên nhân. Nó cho biết phần cải thiện đến từ giai đoạn nào. Nếu gần như toàn bộ lợi ích nằm ở dữ liệu cũ, người đọc phải đặt câu hỏi về khả năng chuyển sang thị trường hiện tại.

## Bốn tình huống người dùng dễ hiểu nhầm

### Tình huống 1: Xác suất tăng rất cao

Màn hình báo 78%. Phản ứng bản năng là tăng tỷ trọng. Cách đọc đúng là xem đây như mức nghiêng của mô hình, rồi kiểm tra lịch sử căn chỉnh và độ ổn định. Với nghiên cứu này, không được diễn giải 78% thành xác suất thực tế đáng tin.

### Tình huống 2: Mô hình thắng mạnh trong tháng gần nhất

Một đoạn thắng gần đây chưa đủ đảo ngược lịch sử thiếu ổn định. Nó là lý do tiếp tục theo dõi, không phải lý do nâng mô hình thành tín hiệu. Cần chờ nhiều giai đoạn độc lập và tiêu chuẩn phải được khóa trước.

### Tình huống 3: Mô hình thua trong vài tuần

Một đoạn thua cũng không chứng minh mô hình vĩnh viễn vô dụng. Câu hỏi là mức thua có nằm trong phạm vi dự kiến và có làm kết quả tích lũy mất ý nghĩa không. Dashboard cần hiển thị chuỗi thời gian, không chỉ trạng thái xanh hoặc đỏ.

### Tình huống 4: Thêm nhiều biến để cứu kết quả

Sau khi khối lượng không ổn định, người phát triển có thể muốn thêm độ rộng, lãi suất, ngoại hối và hàng chục chỉ báo. Nếu làm sau khi đã nhìn kết quả, nguy cơ chọn trúng nhiễu tăng mạnh. Mọi phiên bản mới phải được coi là nghiên cứu mới với danh sách biến, chuẩn so sánh và tiêu chuẩn đạt được khóa trước.

## Nếu đưa vào hệ thống đang vận hành, nên hiển thị thế nào?

### Trạng thái mặc định: nghiên cứu

Mô hình nên mang nhãn “thử nghiệm”, không nằm cạnh nút đặt lệnh và không phát thông báo mua bán. Người dùng phải nhìn thấy rằng chưa có ứng viên vận hành.

### Bảng theo dõi độ ổn định

Mỗi lần cập nhật nên lưu lại dự báo, kết quả thực tế, sai số của mô hình tham chiếu và sai số của mô hình mở rộng. Bảng theo dõi phải cho thấy hiệu quả lũy kế lẫn hiệu quả theo từng giai đoạn, tránh để một đoạn cũ tiếp tục che lấp hiện trạng.

### Cảnh báo về xác suất

Nếu mức căn chỉnh chưa đạt, giao diện không nên dùng câu “xác suất VNINDEX tăng là 72%”. Có thể dùng câu thận trọng hơn: “điểm mô hình đang nghiêng về tăng; xác suất chưa được xác nhận để đọc trực tiếp”.

### Điều kiện nâng cấp

Chỉ xem xét nâng mô hình khi một lần chạy mới, được khóa trước, cho thấy lợi ích trên dữ liệu hiện đại, lặp ở phần lớn giai đoạn, xác suất có ý nghĩa và kết quả không tập trung vào một chế độ duy nhất. Chi phí và quy tắc hành động phải được kiểm tra ở một nghiên cứu riêng.

## Điều gì có thể làm thay đổi kết luận?

Kết luận hiện tại không phải lời phán quyết vĩnh viễn. Nó có thể thay đổi nếu xuất hiện bằng chứng mới đáp ứng đồng thời các điều kiện sau:

- toàn bộ huấn luyện và đánh giá bắt đầu từ một mốc hiện đại được khóa trước;
- mô hình mở rộng thắng chuẩn giá ở phần lớn các giai đoạn, không chỉ ở trung bình;
- xác suất cao và thấp tương ứng với tần suất thực tế theo trật tự hợp lý;
- lợi ích xuất hiện ở nhiều trạng thái thị trường, không bị một thời kỳ chi phối;
- kết quả được tái lập trên một tập dữ liệu hoặc khoảng thời gian chưa dùng trong phát triển;
- nếu muốn giao dịch, hiệu quả vẫn còn sau chi phí, độ trễ và giới hạn thanh khoản.

Cho đến khi các điều kiện đó xuất hiện, kết quả năm phiên nên được giữ như một giả thuyết lịch sử đã qua kiểm tra nghiêm ngặt nhưng chưa đủ ổn định.

## Một bảng kết luận không gây hiểu nhầm

Nếu phải tóm tắt mô hình trong một bảng, nên dùng năm cột: “cải thiện trung bình”, “lặp qua thời gian”, “xác suất đáng tin”, “phân bố theo thời kỳ” và “quyền sử dụng”. Với khoảng năm phiên, chỉ cột đầu cho kết quả tích cực; ba cột ổn định không đạt và quyền sử dụng vẫn là nghiên cứu.

Cách trình bày này ngăn người đọc lấy một dấu đạt làm kết luận cho toàn mô hình. Nó cũng cho thấy đường nâng cấp cụ thể: mô hình không cần “thêm thông minh” theo nghĩa mơ hồ; nó cần vượt những cổng đang thất bại trên một lần chạy mới.

Các khoảng khác nên được ghi “chưa tìm thấy giá trị bổ sung trong thiết kế đã khóa”, không ghi “khối lượng vô dụng”. Câu đầu có phạm vi và có thể kiểm tra lại; câu sau là kết luận tuyệt đối mà dữ liệu không hỗ trợ.

## Kết luận dành cho người xây sản phẩm

Đừng biến đầu ra hiện tại thành thẻ xác suất lớn trên trang chủ. Hãy giữ nó ở khu vực nghiên cứu, cạnh chuẩn so sánh, lịch sử từng giai đoạn và cảnh báo về dữ liệu cũ. Mọi dự báo phải được lưu trước khi kết quả xảy ra để tránh viết lại lịch sử.

Nếu người dùng cần một câu ngắn, hãy dùng: “Khối lượng từng giúp điểm tổng hợp ở khoảng năm phiên, nhưng lợi ích chưa lặp đủ đều để dùng.” Câu này giữ cả phát hiện lẫn giới hạn và không đòi hỏi kiến thức thống kê.

## Nhà đầu tư nên giữ lại bài học nào?

### So sánh với chuẩn đơn giản

Một mô hình phức tạp không đáng dùng nếu không cải thiện đều so với mô hình đơn giản. “Có nhiều biến hơn” không phải bằng chứng “hiểu thị trường hơn”.

### Xem từng giai đoạn, không chỉ trung bình

Kết quả tổng hợp có thể che giấu bốn giai đoạn kém bằng hai giai đoạn rất tốt. Bảng điều khiển nên cho phép người dùng thấy độ lặp lại theo thời gian.

### Kiểm tra ý nghĩa của xác suất

Xác suất chỉ hữu ích khi mức cao và thấp tương ứng với tần suất thực tế khác nhau theo hướng hợp lý. Nếu không, nên trình bày mô hình như một thí nghiệm nghiên cứu, không như công cụ quyết định.

### Tách dữ liệu cũ khỏi thị trường hiện tại

Một phát hiện phụ thuộc vào giai đoạn sơ khai của thị trường cần được gắn nhãn rõ. Nếu muốn kiểm tra khả năng ứng dụng hiện nay, bước tiếp theo phải là khóa thiết kế mới rồi huấn luyện và đánh giá từ giai đoạn hiện đại, không cắt dữ liệu sau khi đã xem kết quả.

## Những điều nghiên cứu chưa chứng minh

Nghiên cứu chưa xác nhận khối lượng giúp dự báo hướng VNINDEX một cách ổn định. Nó chưa tạo mô hình giao dịch, chưa kiểm tra lợi nhuận sau chi phí và chưa cho phép dùng xác suất để xác định tỷ trọng. [C-72]

Kết quả năm phiên không được mở rộng sang mọi khoảng thời gian. Nó cũng không chứng minh cơ chế vì sao khối lượng từng giúp ở giai đoạn cũ. Các giả thuyết về cấu trúc nhà đầu tư hoặc thanh khoản chưa được nghiên cứu này cô lập.

Kết quả hậu kỳ từ 2014 trở đi không phải một lần chạy lại xác nhận. Một nghiên cứu tiếp theo phải khóa trước thời điểm bắt đầu, biến đầu vào, chuẩn so sánh và tiêu chuẩn đạt.

## Kết luận

Trước khi chấp nhận một mô hình mới, hãy hỏi: nó thắng chuẩn nào, thắng ở bao nhiêu giai đoạn, xác suất có khớp thực tế không, lợi ích tập trung ở thời kỳ nào và tiêu chuẩn đạt có được khóa trước không? Chỉ một con số trung bình không trả lời được năm câu đó.

Nếu mô hình không vượt qua, kết quả vẫn có ích: nó ngăn đội phát triển triển khai một đầu ra có vẻ thông minh nhưng chưa đáng tin. Một lần bác bỏ triển khai sai có thể giá trị hơn một mô hình mới.

Đội sản phẩm nên lưu cả phiên bản mô hình, ngày dự báo và dữ liệu đầu vào tại thời điểm đó. Nếu chỉ tính lại sau khi đã biết kết quả, lịch sử có thể vô tình dùng dữ liệu được sửa hoặc bổ sung. Một registry dự báo bất biến là điều kiện để vòng đánh giá tiếp theo đáng tin.

Trong thời gian theo dõi, không nên thay ngưỡng hoặc danh sách biến vì một vài tuần kém. Việc thay đổi tạo phiên bản mới và làm kết quả trước sau không còn so sánh trực tiếp. Kỷ luật phiên bản giúp phân biệt cải tiến thật với việc đuổi theo nhiễu.

Mỗi lần thay đổi phải bắt đầu một hồ sơ đánh giá mới.

Mô hình có thêm khối lượng từng tạo ra một kết quả tổng hợp đáng chú ý ở khoảng năm phiên. Nhưng lợi ích không lặp qua phần lớn các giai đoạn, xác suất không đáng tin và kết quả tập trung ở dữ liệu cũ. [C-70] [C-72]

Vì vậy, chương này không bàn giao một tín hiệu. Nó bàn giao một tiêu chuẩn đánh giá: **mô hình chỉ đáng dùng khi tốt hơn chuẩn đơn giản, lặp lại qua thời gian và nói ra mức tự tin có ý nghĩa**.

## Phụ lục kỹ thuật

Claim [C-70] map kết quả tổng hợp và mức điều chỉnh của ô VNINDEX ngày, khoảng năm phiên, mô hình giá cộng khối lượng so với mô hình chỉ dùng giá.

Claim [C-72] map số giai đoạn cải thiện: 2/6. Các cổng về độ tin cậy xác suất và mức tập trung theo thời kỳ không đạt, nên verdict hiện hành là cải thiện không ổn định, không phải ứng viên vận hành.

Nguồn R9 là chuỗi hiện hành. Phân tích phần đánh giá từ 2014 là dữ liệu bổ sung, không thay thế thiết kế xác nhận. Chi tiết nguồn và SHA256 nằm trong `14_claim_usage_matrix.json`.
