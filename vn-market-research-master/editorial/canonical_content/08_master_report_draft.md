# Đọc thị trường Việt Nam qua bond, giá, khối lượng và độ rộng

## Kết luận trong 90 giây

Năm nghiên cứu cùng dẫn đến một kết luận thực dụng: dữ liệu có thể giúp nhà đầu tư hiểu bối cảnh và nhận ra khi các lớp thị trường không đồng thuận, nhưng chưa tạo ra một tín hiệu độc lập đủ ổn định để giao dịch.

Lợi suất trái phiếu có liên hệ cùng thời điểm với một số chỉ số cổ phiếu. Giá từng xuất hiện trước thay đổi khối lượng trong mẫu. Một mô hình có thêm khối lượng từng cải thiện kết quả tổng hợp ở khoảng năm phiên. Một số dạng phân kỳ từng cho thấy liên hệ lịch sử. Nhưng khi yêu cầu các phát hiện phải lặp lại trên dữ liệu mới, giữ được qua nhiều giai đoạn và có ý nghĩa thực tế, không nghiên cứu nào bàn giao một công cụ vận hành.

Điều đó không làm bond, khối lượng, độ rộng hay phân kỳ vô dụng. Chúng phù hợp với ba việc:

1. Mô tả bối cảnh hiện tại chính xác hơn.
2. Nhận diện nơi một câu chuyện thị trường đang thiếu đồng thuận.
3. Chỉ ra dữ liệu nào cần kiểm tra tiếp trước khi tin vào luận điểm.

Chúng chưa phù hợp để gán xác suất tăng giảm, tạo điểm mua bán hoặc thay thế định giá và quản trị rủi ro.

### Ba cách đọc báo cáo

Người cần một câu trả lời nhanh có thể đọc phần 90 giây, bốn hình chính và kết luận lớn. Tuyến đọc này trả lời ba câu: dữ liệu có ích ở đâu, vì sao chưa có tín hiệu giao dịch và người dùng nên làm gì khi các màn hình bất đồng.

Người đang xây luận điểm đầu tư nên đọc năm chương nghiên cứu, phần bức tranh xuyên nghiên cứu và casebook. Tuyến này giải thích vì sao một quan hệ có thể đúng trong mẫu mà vẫn không dùng được, đồng thời đưa ra mẫu câu để chuyển quan sát thành việc kiểm tra doanh nghiệp, định giá và rủi ro.

Người kiểm chứng phương pháp có thể mở phụ lục và các chuyên khảo. Claim ID dẫn về artifact, khóa truy xuất và giới hạn. Tuyến kỹ thuật tồn tại để kiểm tra câu chữ công khai, không buộc mọi nhà đầu tư phải học công thức trước khi hiểu kết luận.

Dù chọn tuyến nào, người đọc nên giữ một quy tắc: **không đọc con số tách khỏi câu hỏi mà nó trả lời**. Một hệ số, xác suất hay số lần vượt ngưỡng không tự mang ý nghĩa đầu tư. Ý nghĩa đến từ thiết kế, chuẩn so sánh, độ lặp lại và ranh giới đã công bố.

Báo cáo cũng không đòi hỏi phải đọc liền một lần. Mỗi chương có câu trả lời ngắn, ví dụ, phần ứng dụng và giới hạn riêng. Người đọc có thể quay lại đúng lớp dữ liệu đang liên quan đến quyết định hiện tại, sau đó dùng liên kết chuyên khảo để kiểm tra sâu hơn mà không mất bối cảnh chung.

## 1. Chương trình nghiên cứu đã thực sự hỏi gì?

Nhà đầu tư thường nhìn nhiều màn hình cùng lúc. Chỉ số đang tăng hay giảm? Khối lượng có thay đổi không? Bao nhiêu cổ phiếu cùng tham gia? Lợi suất trái phiếu đang nói gì về bối cảnh tài chính? Khi hai màn hình bất đồng, đó có phải dấu hiệu đảo chiều?

Những câu hỏi này quen thuộc trong phân tích thị trường, nhưng chúng thường được trả lời bằng trực giác hoặc hình vẽ. Chương trình nghiên cứu đặt chúng vào một quy trình chặt hơn:

- Quan hệ có xuất hiện trong dữ liệu lịch sử không?
- Một biến có thực sự xuất hiện trước biến kia không?
- Thêm biến mới có giúp dự báo tốt hơn một chuẩn đơn giản không?
- Kết quả có lặp qua các giai đoạn chưa dùng để xây mô hình không?
- Nếu một trường hợp riêng lẻ đẹp, nhóm rộng hơn có hỗ trợ không?

Năm nghiên cứu không phải năm lần kiểm tra cùng một giả thuyết. Chúng dùng biến, tần suất, mẫu và kết quả tương lai khác nhau. Vì vậy báo cáo này so sánh bằng lời, không cộng số liệu để tạo một “bằng chứng tổng hợp”. Mỗi kết luận vẫn thuộc về nghiên cứu gốc và đi cùng giới hạn riêng.

Điểm chung nằm ở cách đánh giá. Quan hệ cùng thời điểm được tách khỏi dự báo. Kết quả trong mẫu được tách khỏi dữ liệu mới. Một con số tổng hợp được tách khỏi độ lặp lại theo giai đoạn. Trạng thái bất thường được tách khỏi lệnh giao dịch.

### Năm nghiên cứu tạo thành một chuỗi câu hỏi, không phải một chỉ báo

Nếu đặt cạnh nhau, năm nghiên cứu tạo thành một quá trình sàng lọc. Nghiên cứu bond hỏi hai thị trường có chuyển động liên quan hay không và liệu một bên có đi trước bên kia. Nghiên cứu giá, khối lượng và độ rộng hỏi thứ tự lịch sử giữa các lớp dữ liệu nội bộ thị trường. Nghiên cứu đa biến đi xa hơn: sau khi đã biết giá, việc thêm khối lượng có thực sự làm dự báo tốt hơn không. Hai nghiên cứu phân kỳ kiểm tra một trực giác phổ biến khác, trước hết ở cấp chỉ số rồi ở từng cổ phiếu.

Chuỗi đó không tạo ra công thức “bond cộng độ rộng cộng khối lượng bằng xu hướng”. Nó cho biết một ý tưởng phải trải qua những câu hỏi nào trước khi được dùng. Một quan hệ đẹp trên biểu đồ mới chỉ trả lời câu hỏi mô tả. Thứ tự xuất hiện trong dữ liệu lịch sử mới chỉ tạo giả thuyết về khả năng đi trước. Mô hình tốt hơn trên toàn mẫu mới chỉ cho thấy giá trị trung bình. Muốn đi vào quyết định, kết quả còn phải lặp lại ở nhiều giai đoạn, giữ được trên dữ liệu mới và tạo khác biệt đủ lớn so với một cách làm đơn giản.

Nhìn theo cách này, các kết quả âm không phải những ngõ cụt rời rạc. Chúng là thông tin về nơi một trực giác đã dừng lại. Bond dừng ở quan hệ cùng thời điểm. Giá đi trước khối lượng dừng ở dữ liệu trong mẫu. Cải thiện năm phiên dừng ở độ ổn định và độ tin cậy của xác suất. Phân kỳ dừng trước ngưỡng cảnh báo vận hành. Nghiên cứu từng cổ phiếu còn dừng sớm hơn vì giới hạn dữ liệu và khả năng phát hiện hiệu ứng nhỏ.

### Bốn tầng bằng chứng cần phân biệt

**Tầng 1 — quan sát trạng thái.** Đây là câu trả lời cho “đang xảy ra điều gì?”. Giá tăng hay giảm, khối lượng cao hay thấp, độ rộng mở rộng hay thu hẹp, lợi suất thay đổi theo hướng nào. Tầng này có thể hữu ích ngay vì nó giúp mô tả thị trường chính xác hơn. Nó không đòi hỏi một biến phải dự báo biến khác.

**Tầng 2 — liên hệ lịch sử.** Hai trạng thái từng xuất hiện cùng nhau hoặc một trạng thái thường xuất hiện trước trạng thái khác. Tầng này đáng nghiên cứu nhưng rất dễ bị kể thành cơ chế. Thứ tự thời gian không tự chứng minh nguyên nhân; hai biến có thể cùng phản ứng với thông tin khác, hoặc quan hệ có thể chỉ tồn tại trong một giai đoạn.

**Tầng 3 — giá trị bổ sung trên dữ liệu mới.** Một biến chỉ đáng gọi là hữu ích cho dự báo khi nó làm tốt hơn chuẩn đã có trên những thời điểm không dùng để xây mô hình. So sánh phải công bằng: cùng ngày đánh giá, cùng kết quả tương lai và cùng cách chia thời gian. Nếu mô hình phức tạp chỉ thắng một chuẩn quá yếu, chiến thắng đó không có nhiều ý nghĩa.

**Tầng 4 — công cụ vận hành.** Đây là ngưỡng cao nhất. Kết quả phải đủ lớn để quan tâm, lặp qua nhiều giai đoạn, đưa ra mức tự tin đáng tin và không phụ thuộc gần như hoàn toàn vào một thời kỳ đặc biệt. Một công cụ còn cần tính đến chi phí giao dịch, độ trễ dữ liệu, khả năng triển khai và quy tắc quản trị khi mô hình xuống cấp. Không nghiên cứu nào trong bộ hiện tại đạt tầng này.

Việc giữ bốn tầng riêng biệt là nền tảng của báo cáo. Nếu trộn chúng, người đọc có thể biến một tương quan thành dự báo hoặc biến một kết quả trung bình thành tín hiệu. Nếu chỉ chấp nhận tầng 4 rồi bỏ ba tầng trước, người đọc lại mất những dữ liệu có ích cho việc hiểu bối cảnh và chất lượng của luận điểm.

### Vì sao không thể cộng năm nghiên cứu thành một điểm số

Các nghiên cứu không dùng cùng một đơn vị quan sát. Bond được nghiên cứu theo thay đổi lợi suất và lợi nhuận chỉ số; độ rộng dùng cấu trúc số mã tăng giảm; mô hình đa biến dùng sai số xác suất; phân kỳ dùng trạng thái được định nghĩa theo khoảng nhìn lại; nghiên cứu cổ phiếu còn chịu ảnh hưởng của sự kiện doanh nghiệp và danh sách mã tồn tại. Cộng các kết quả này sẽ tạo một con số có vẻ chính xác nhưng không có ý nghĩa được kiểm định.

Ngay cả khi năm màn hình cùng chuyển sang màu xấu, báo cáo cũng không được gọi đó là “năm phiếu bán”. Chúng có thể phản ánh cùng một sự kiện và vì vậy không độc lập. Ngược lại, khi các màn hình bất đồng, báo cáo cũng không được mặc định thị trường sắp đảo chiều. Bất đồng chỉ cho biết câu chuyện hiện tại chưa bao quát hết dữ liệu.

Do đó, sản phẩm phù hợp không phải một đồng hồ tổng hợp. Nó là một hệ thống quan sát nhiều lớp, trong đó mỗi lớp giữ nguyên đơn vị, nguồn và giới hạn. Phần tổng hợp diễn ra trong quy trình suy nghĩ của người dùng: mô tả, đối chiếu, tìm nguyên nhân, đánh giá luận điểm và quản trị rủi ro.

## 2. Bond giúp đọc bối cảnh, không báo trước thị trường

Nghiên cứu về trái phiếu và cổ phiếu cho thấy thay đổi lợi suất có liên hệ cùng thời điểm với một số chỉ số. Đây là phát hiện tích cực: thị trường trái phiếu không đứng ngoài câu chuyện của cổ phiếu. Hai bên có thể cùng phản ánh thay đổi trong điều kiện tài chính hoặc thông tin mới. [A-CONTEMPORANEOUS]

Tuy nhiên, một ảnh chụp cùng thời điểm không cho biết thứ tự. Nghiên cứu kiểm tra cả hai chiều, theo ngày và theo tháng, với tổng cộng 300 cấu hình. Không trường hợp nào còn đủ mạnh sau khi tính đến số lượng phép thử. Cách nói dễ hiểu là chưa tìm thấy bằng chứng chắc rằng lợi suất báo trước cổ phiếu hoặc cổ phiếu báo trước lợi suất. [A-GRANGER-NULL]

### Ý nghĩa đối với nhà đầu tư

Bond nên được dùng như một màn hình bối cảnh. Khi lợi suất và cổ phiếu cùng thay đổi, nhà đầu tư có lý do kiểm tra:

- định giá có trở nên nhạy hơn với chi phí vốn không;
- nhóm ngành nào chịu ảnh hưởng nhiều hơn;
- thông tin chính sách, lạm phát hoặc tỷ giá nào đang được thị trường phản ánh;
- luận điểm đầu tư có phụ thuộc vào mặt bằng lãi suất hay không.

Những câu hỏi đó có thể cải thiện chất lượng phân tích mà không cần giả định lợi suất dự báo phiên tiếp theo.

### Ranh giới cần giữ

Không được biến câu “bond và cổ phiếu đi cùng trong một số giai đoạn” thành “bond dẫn thị trường”. Cũng không được kết luận bond vô dụng vì không dự báo được. Một dữ liệu có thể giúp đọc hiện tại dù không biết trước tương lai.

Trong thực tế, sự phân biệt này thay đổi cách viết nhận định. Thay vì viết “lợi suất tăng nên cổ phiếu sẽ giảm”, nhà phân tích nên viết “lợi suất tăng cùng lúc cổ phiếu suy yếu; cần đánh giá lại độ nhạy định giá, cấu trúc nợ và nhóm ngành chịu ảnh hưởng”. Câu thứ hai không yếu hơn. Nó chỉ tách rõ điều đã quan sát khỏi điều còn phải chứng minh.

Bond cũng có thể giúp phát hiện khi câu chuyện cổ phiếu thiếu một lớp bối cảnh. Một doanh nghiệp tăng trưởng tốt vẫn có thể bị định giá lại khi tỷ lệ chiết khấu thay đổi. Một ngân hàng có thể hưởng lợi hoặc chịu áp lực theo cấu trúc tài sản, nguồn vốn và chính sách chứ không chỉ theo hướng lợi suất. Một công ty bất động sản có thể nhạy với khả năng tái cấp vốn hơn với một thay đổi ngắn hạn của chỉ số. Nghiên cứu không xác nhận các cơ chế riêng này; nó chỉ cho thấy vì sao màn hình lợi suất đáng được đặt cạnh phân tích doanh nghiệp.

Vai trò dài hạn của chương bond vì thế là tạo kỷ luật về ngữ cảnh. Nó nhắc người dùng rằng cùng một chuyển động giá cổ phiếu có thể mang ý nghĩa khác nhau dưới các điều kiện tài chính khác nhau. Nhưng vì chưa có bằng chứng đi trước ổn định, màn hình này không được quyết định thời điểm giao dịch.

## 3. Giá, khối lượng và độ rộng cho biết mức tham gia

Ba đại lượng này trả lời ba câu hỏi khác nhau. Giá cho biết kết quả giao dịch. Khối lượng cho biết mức hoạt động. Độ rộng cho biết chuyển động lan ra nhiều cổ phiếu hay tập trung ở một nhóm.

Nghiên cứu tìm thấy giá từng xuất hiện trước thay đổi khối lượng ở dữ liệu ngày trong mẫu. Chiều ngược lại, khối lượng đi trước giá, không được xác nhận ổn định. Khi đem các quan hệ sang dữ liệu mới, không hướng nào đạt tiêu chuẩn vận hành. [B-67] [B-52]

Phát hiện này sửa một trực giác phổ biến. Khối lượng không tự mang nhãn “xác nhận xu hướng”. Một đợt tăng với khối lượng thấp không mặc nhiên yếu; một phiên giảm với khối lượng cao không mặc nhiên tạo đáy. Khối lượng cần được đọc cạnh giá, sự kiện và thanh khoản của chính tài sản.

### Độ rộng bổ sung điều gì?

Độ rộng giúp kiểm tra xem chỉ số có đại diện cho trải nghiệm của phần lớn cổ phiếu hay không. Nếu VNINDEX tăng nhờ vài mã vốn hóa lớn trong lúc nhiều cổ phiếu giảm, câu “thị trường tăng” vẫn đúng về điểm số nhưng thiếu thông tin về mức tham gia.

Đây là vai trò mô tả. Kết luận hiện hành không cho phép nói độ rộng báo trước khối lượng hoặc dự báo chỉ số. Việc dùng độ rộng trong báo cáo tổng hợp nhằm giúp nhà đầu tư đọc cấu trúc thị trường, không phục hồi một kết luận đã vượt quá bằng chứng.

### Đồng thuận không phải lời hứa

Khi giá, khối lượng và độ rộng cùng kể một câu chuyện, nhận định về trạng thái hiện tại rõ hơn. Nhưng trạng thái đồng thuận vẫn có thể đảo chiều. Khi chúng bất đồng, nhà đầu tư nên hạ mức chắc chắn và kiểm tra thêm. Bất đồng cũng có thể kéo dài.

Giá trị nằm ở việc mô tả đúng hơn, không phải đổi một trạng thái thành xác suất.

Một cách đọc hữu ích là xem ba đại lượng như ba câu mô tả độc lập. “Chỉ số tăng” nói về kết quả. “Khối lượng cao hơn lịch sử gần” nói về mức hoạt động. “Số mã tham gia ít” nói về phạm vi. Ghép thành câu “chỉ số tăng trong khi hoạt động cao nhưng phạm vi hẹp” giàu thông tin hơn từng nhãn riêng lẻ, nhưng vẫn chưa chứa dự báo.

Điều này đặc biệt quan trọng với VNINDEX, nơi một số cổ phiếu vốn hóa lớn có thể chi phối điểm số. Nhà đầu tư sở hữu danh mục rộng có thể trải nghiệm một thị trường rất khác với chỉ số. Độ rộng giúp giải thích khoảng cách đó. Khối lượng lại giúp phân biệt một chuyển động im ắng với một phiên có nhiều giao dịch, nhưng chưa cho biết bên mua hay bên bán sẽ thắng ở tương lai.

Nghiên cứu về thứ tự giá và khối lượng còn đưa ra một bài học về trực giác. Nếu giá thường xuất hiện trước thay đổi khối lượng trong mẫu, câu chuyện “dòng tiền đi trước rồi giá mới phản ứng” không thể được coi là mặc định. Có thể hoạt động giao dịch tăng sau khi giá đã thu hút chú ý. Đây mới là giả thuyết diễn giải, không phải cơ chế đã kiểm định. Giá trị của phát hiện là buộc người dùng kiểm tra thứ tự thay vì kể lại câu chuyện quen thuộc.

Trong sản phẩm, ba lớp nên hiển thị cạnh nhau nhưng không dùng chung thang điểm. Giá cần khoảng thời gian rõ ràng. Khối lượng cần so với lịch sử của chính tài sản và cần cảnh báo về phiên bất thường. Độ rộng cần nêu rõ vũ trụ cổ phiếu và cách xử lý mã thiếu dữ liệu. Khi ba lớp đồng thuận, hệ thống có thể nói “mức tham gia rộng hơn”; khi bất đồng, hệ thống chỉ nên nói “cần kiểm tra cấu trúc”.

## 4. Vì sao mô hình đa biến chưa trở thành công cụ?

Nghiên cứu đa biến đặt một câu hỏi trực tiếp hơn: nếu mô hình đã biết thông tin giá, thêm khối lượng có giúp dự báo hướng VNINDEX không?

Ở khoảng năm phiên, kết quả tổng hợp cho thấy mô hình có thêm khối lượng giảm sai số đủ lớn và vượt kiểm tra thống kê ban đầu. Đây là một phát hiện thật trong chuỗi hiện hành, không nên bị xóa khỏi câu chuyện. [C-70]

Nhưng một mô hình vận hành phải làm tốt hơn trung bình chung. Kết quả được chia thành sáu giai đoạn theo thời gian; chỉ hai giai đoạn tốt hơn mô hình chỉ dùng giá. Xác suất mô hình đưa ra không khớp tốt với tần suất thực tế. Phần lớn lợi ích còn tập trung ở dữ liệu trước 2014, khi thị trường Việt Nam khác hiện nay. [C-72]

### Bài học quan trọng

Một kết quả tổng hợp có thể đẹp mà công cụ vẫn không dùng được. Ba câu hỏi phải được hỏi cùng nhau:

1. **Có cải thiện trung bình không?** Ở năm phiên, câu trả lời từng là có.
2. **Có lặp qua thời gian không?** Chỉ hai trong sáu giai đoạn, nên chưa đạt.
3. **Mức tự tin có đáng tin không?** Xác suất không được căn chỉnh tốt, nên chưa đạt.

Nếu chỉ công bố câu đầu tiên, báo cáo sẽ tạo ấn tượng sai rằng đã có mô hình dự báo. Nếu chỉ công bố hai câu sau, báo cáo lại che mất một phát hiện lịch sử đáng nghiên cứu. Cách trình bày đúng phải giữ cả hai vế.

### Thị trường sau 2014

Khi chỉ nhìn các ngày đánh giá từ 2014 trở đi, lợi ích không còn. Tuy nhiên, đây là phân tích hậu kỳ trên dự báo của quy trình toàn mẫu; một số mô hình vẫn có thể học từ dữ liệu cũ. Nó chưa phải lần chạy lại trong đó cả huấn luyện và đánh giá đều bắt đầu từ thị trường hiện đại.

Bước nghiên cứu đúng trong tương lai là khóa thiết kế mới trước khi chạy. Không được gọi phân tích hậu kỳ hiện tại là bằng chứng xác nhận cho giai đoạn sau 2014.

Kết quả này minh họa vì sao đánh giá mô hình không thể dừng ở một con số trung bình. Nếu lợi ích đến gần như toàn bộ từ một thời kỳ cũ, mô hình có thể đang học cấu trúc thị trường đã thay đổi. Nếu chỉ hai trong sáu giai đoạn tốt hơn, người dùng không biết giai đoạn hiện tại thuộc nhóm nào trước khi kết quả xảy ra. Nếu xác suất cao không đi cùng tần suất thực tế cao, con số 70% hoặc 80% dễ tạo mức tự tin sai.

Một mô hình như vậy vẫn có giá trị nghiên cứu. Nó chỉ ra rằng khối lượng từng chứa thông tin bổ sung trong một cấu trúc dữ liệu cụ thể. Nhà nghiên cứu có thể dùng phát hiện đó để đặt giả thuyết về chế độ thị trường, cách chuẩn hóa thanh khoản hoặc sự thay đổi cơ chế giao dịch. Nhưng người vận hành không được dùng chính phát hiện này để đặt vị thế, vì chưa có quy tắc nhận biết trước khi nào lợi ích sẽ xuất hiện.

Chuẩn so sánh đơn giản cũng là một phần thiết yếu. Câu hỏi không phải mô hình có dự đoán đúng nhiều phiên hay không, mà là nó có tốt hơn cách chỉ dùng thông tin giá trên cùng các ngày hay không. Một mô hình có tỷ lệ đúng cao trong giai đoạn thị trường tăng phần lớn thời gian vẫn có thể không thêm giá trị. So với chuẩn buộc nghiên cứu trả lời đúng câu hỏi “thêm biến mới mang lại gì?”.

Nếu tiếp tục theo dõi, mô hình nên ở chế độ giám sát. Báo cáo hàng tháng cần cho thấy sai số so với chuẩn, kết quả từng giai đoạn cuốn chiếu, độ tin cậy của xác suất và mức phụ thuộc vào dữ liệu cũ. Không nên chỉ hiển thị xác suất của ngày hiện tại. Mục tiêu của giám sát là phát hiện khi bằng chứng đủ để mở lại nghiên cứu, không phải ngầm biến mô hình chưa đạt thành công cụ.

## 5. Phân kỳ có ích ở đâu?

Phân kỳ là tên gọi cho sự bất đồng giữa hai lớp dữ liệu. Ví dụ: giá giảm nhưng khối lượng tăng, hoặc chỉ số tăng trong lúc độ rộng thu hẹp. Trong thực hành, các trạng thái này thường được gắn ngay với câu chuyện đảo chiều.

Nghiên cứu cấp chỉ số kiểm tra trực tiếp liệu phân kỳ có báo trước đảo chiều, mức sinh lời hoặc rủi ro giảm sâu hay không. Một số liên hệ trong mẫu xuất hiện, nhưng không trạng thái nào vượt đầy đủ các cổng ngoài mẫu và mức cải thiện thực tế để thành cảnh báo vận hành. [D-102]

### Vai trò phù hợp: cảnh báo về nhận định

Phân kỳ không cảnh báo chắc rằng giá sắp đi hướng nào. Nó cảnh báo rằng nhận định hiện tại có thể quá đơn giản.

Nếu chỉ số tăng nhưng độ rộng hẹp, nhà đầu tư nên hỏi nhóm nào đang kéo chỉ số và danh mục của mình có thực sự hưởng lợi không. Nếu giá giảm với khối lượng tăng, cần kiểm tra tin tức, giao dịch bất thường và cấu trúc ngành trước khi gọi đó là tạo đáy.

Phân kỳ vì vậy có giá trị như một nút “mở điều tra”. Nó không phải nút “mua” hoặc “bán”.

Đây là vai trò gần với một cảnh báo chất lượng luận điểm hơn là cảnh báo thị trường. Khi giá và khối lượng bất đồng, điều bị cảnh báo trước tiên là cách giải thích của người dùng. Khi chỉ số và độ rộng bất đồng, điều bị cảnh báo là mức đại diện của chỉ số. Hệ thống chưa có căn cứ để cảnh báo rằng giá sẽ đảo chiều trong một số phiên cụ thể.

Phân kỳ cũng cần bối cảnh thời gian. Một trạng thái kéo dài ba phiên và một trạng thái kéo dài nhiều tuần không nhất thiết có cùng ý nghĩa. Một phiên khối lượng tăng do tái cơ cấu quỹ khác với hoạt động tăng dần trong quá trình hình thành xu hướng. Nghiên cứu đã khóa những định nghĩa cụ thể để tránh chọn lại sau khi thấy kết quả, nhưng một ứng dụng thực tế vẫn phải hiển thị đúng định nghĩa thay vì dùng từ “phân kỳ” như một nhãn chung.

Giá trị lớn nhất của phân kỳ nằm ở khả năng tổ chức hàng đợi phân tích. Thay vì yêu cầu người dùng rà toàn bộ thị trường, hệ thống có thể đưa ra danh sách nơi hai lớp dữ liệu đang kể chuyện khác nhau. Sau đó con người kiểm tra sự kiện, định giá, cấu trúc ngành và chất lượng dữ liệu. Nếu không có bằng chứng độc lập, mục được đóng lại mà không tạo hành động.

## 6. Tại sao kết quả từng cổ phiếu còn thận trọng hơn?

Ở cấp cổ phiếu, khối lượng bất thường có thể do sự kiện doanh nghiệp, giao dịch cổ đông lớn hoặc điều chỉnh giá. Mỗi mã có thanh khoản và lịch sử riêng. Danh sách dữ liệu hiện hành còn dựa trên những cổ phiếu đang hoạt động tại thời điểm lấy mẫu, nên có thể thiếu các mã đã rời thị trường.

Chuỗi nghiên cứu mới nhất đã sửa dữ liệu sự kiện doanh nghiệp, phần cuối chuỗi thiếu tương lai và cách chọn cổ phiếu theo thanh khoản. Sau sửa chữa, không còn phát hiện mô tả hoặc vận hành nào ở cấp cổ phiếu. Những kết quả riêng lẻ từng vượt một bước kiểm tra đều thất bại ở tầng nhóm rộng hơn. [E-66]

Kết luận này vẫn chưa phải bằng chứng “phân kỳ chắc chắn vô dụng”. Mô phỏng cho thấy thiết kế chỉ phát hiện được hiệu ứng khóa trong khoảng 44% trường hợp. Khả năng bỏ sót hiệu ứng nhỏ còn cao. [E-95]

### Cách dùng phù hợp ở cấp mã

Một hệ thống có thể đánh dấu cổ phiếu có giá và khối lượng khác thường để nhà phân tích kiểm tra:

- sự kiện doanh nghiệp và điều chỉnh giá;
- giao dịch thỏa thuận hoặc thay đổi sở hữu;
- tin tức mới;
- mức thanh khoản so với lịch sử;
- bối cảnh ngành và thị trường.

Nhãn nên là “cần xem thêm”. Nó chưa được phép trở thành xếp hạng cơ hội hoặc cảnh báo đảo chiều.

Kết quả cấp cổ phiếu giúp sửa một thiên lệch thường gặp: chọn vài ví dụ đẹp rồi tin rằng mô hình đúng trên toàn thị trường. Với hàng trăm mã và nhiều khoảng thời gian, luôn có thể tìm thấy những trường hợp phân kỳ đi trước một nhịp hồi mạnh. Câu hỏi nghiên cứu không phải “có ví dụ nào không”, mà là hiệu ứng có đủ rộng, vượt kiểm tra theo nhóm và lặp trên dữ liệu mới hay không.

Sau khi sửa dữ liệu sự kiện doanh nghiệp và cách xử lý phần cuối chuỗi, các trường hợp riêng lẻ không còn vượt được toàn bộ hệ thống phân cấp. Điều này cho thấy quản trị dữ liệu không phải phần phụ. Một hệ số điều chỉnh sai hoặc việc coi một kết quả tương lai chưa tồn tại là dữ liệu hợp lệ có thể biến nhiễu thành phát hiện.

Giới hạn sức mạnh phát hiện cần được giữ ở vị trí dễ thấy. Khả năng khoảng 44% nghĩa là thiết kế có thể bỏ qua một hiệu ứng nhỏ ngay cả khi hiệu ứng đó tồn tại ở mức được giả định. Vì vậy kết luận hợp lý là “chưa xác nhận được hiệu ứng đủ rõ và đủ rộng”, không phải “mọi hình thức phân kỳ ở mọi cổ phiếu đều vô dụng”. Điều này vừa ngăn quảng bá quá mức, vừa ngăn phủ định quá mức.

Nếu danh sách kiểm tra được đưa vào hệ thống, mỗi mục cần nêu mã, ngày, loại bất đồng, chất lượng dữ liệu, sự kiện doanh nghiệp gần nhất và lý do đóng hoặc chuyển cho phân tích viên. Không nên xếp hạng theo mức “mạnh” nếu mức đó chưa có liên hệ ổn định với kết quả tương lai.

## 7. Bức tranh xuyên năm nghiên cứu

Khi đọc riêng, mỗi chương có thể tạo cảm giác đây là một tập hợp kết quả âm. Khi đọc cùng nhau, bức tranh rõ hơn: phần lớn dữ liệu thị trường có khả năng mô tả trạng thái tốt hơn khả năng báo trước. Khoảng cách giữa hai vai trò này là kết luận trung tâm của toàn bộ chương trình.

### Điều gì thực sự lặp lại?

Không phải một hệ số hay một hướng dự báo lặp lại xuyên suốt. Điều lặp lại là cấu trúc của thất bại khi nâng cấp bằng chứng. Một liên hệ xuất hiện trong mẫu nhưng yếu đi khi chuyển sang dữ liệu mới. Một kết quả trung bình tồn tại nhưng tập trung ở ít giai đoạn. Một trường hợp riêng lẻ vượt kiểm tra nhưng nhóm rộng hơn không hỗ trợ. Một trạng thái có vẻ hợp lý về mặt kỹ thuật nhưng không cải thiện chuẩn đơn giản.

Sự lặp lại này không chứng minh thị trường Việt Nam hoàn toàn không thể dự báo. Nó cho thấy các quan hệ đơn giản giữa giá, khối lượng, độ rộng và bond chưa bền đủ để đứng một mình. Thị trường có thể thay đổi theo chính sách, cấu trúc nhà đầu tư, cơ chế giao dịch, chu kỳ tín dụng và chất lượng dữ liệu. Một quy tắc cố định dễ học được một giai đoạn rồi mất hiệu lực ở giai đoạn khác.

### Vì sao quan hệ cùng thời điểm vẫn có giá trị?

Một nhà đầu tư không chỉ cần biết tương lai. Họ còn cần hiểu điều gì đang diễn ra, danh mục có thực sự phản ánh chuyển động của chỉ số không và luận điểm có đang bỏ qua một lớp dữ liệu quan trọng không. Bond, khối lượng và độ rộng đóng góp vào những câu hỏi này.

Quan hệ cùng thời điểm có thể giúp kiểm tra tính nhất quán của câu chuyện. Nếu cổ phiếu suy yếu đồng thời lợi suất tăng, nhà đầu tư biết bối cảnh tài chính cần được đưa vào phân tích. Nếu chỉ số tăng nhưng độ rộng hẹp, họ biết điểm số không đại diện đầy đủ cho thị trường. Nếu giá giảm với hoạt động giao dịch cao, họ biết cần kiểm tra nguyên nhân trước khi gọi đó là cơ hội.

Giá trị này khó đo bằng lợi nhuận giao dịch trực tiếp, nhưng có thể đo bằng chất lượng quy trình: ít nhận định tuyệt đối hơn, nhiều điều kiện bác bỏ hơn, ít nhầm lẫn giữa chỉ số và danh mục hơn, và có nhật ký rõ ràng về lý do hành động.

### Những kết quả tưởng như mâu thuẫn thực ra nói gì?

Giá đi trước khối lượng trong mẫu nhưng thêm khối lượng từng cải thiện dự báo năm phiên không phải là mâu thuẫn. Kết quả thứ nhất nói về thứ tự giữa hai biến trong một thiết kế; kết quả thứ hai hỏi khối lượng có mang thông tin bổ sung khi mô hình đã biết giá hay không. Một biến có thể phản ứng sau ở nhiều trường hợp nhưng vẫn chứa thông tin trong một số chế độ. Vấn đề là lợi ích đó không lặp đủ đều để vận hành.

Phân kỳ cấp chỉ số từng có liên hệ lịch sử trong một số cấu hình, trong khi nghiên cứu cấp cổ phiếu không còn phát hiện mô tả sau sửa chữa. Hai cấp độ không dùng cùng đơn vị. Chỉ số là tổng hợp có trọng số; một chuyển động ở chỉ số có thể phản ánh sự tập trung của nhóm lớn mà không lặp ở từng mã. Vì vậy không được suy từ VNINDEX sang mọi cổ phiếu hoặc ngược lại.

Bond liên hệ cùng thời điểm với cổ phiếu nhưng không đi trước ổn định cũng không phải nghịch lý. Hai thị trường có thể phản ứng gần nhau với thông tin chung. Nghiên cứu hiện chưa cô lập nguyên nhân đó. Kết luận đúng là mối liên hệ bối cảnh tồn tại ở một số cấu hình, còn khả năng dùng thứ tự để dự báo chưa được xác nhận.

### Vai trò của giai đoạn trước và sau 2014

Kết quả mô hình đa biến cho thấy gần như toàn bộ lợi ích tổng hợp tập trung ở dữ liệu cũ. Điều này làm nổi bật một vấn đề rộng hơn: thị trường Việt Nam đã thay đổi đáng kể về thanh khoản, cơ cấu nhà đầu tư, sản phẩm, quy mô và quy định. Một quan hệ học từ giai đoạn sơ khai có thể không đại diện cho môi trường hiện tại.

Tuy nhiên, không nên tùy tiện cắt dữ liệu cũ sau khi thấy kết quả. Làm vậy sẽ thay đổi thiết kế dựa trên chính phát hiện cần kiểm tra. Cách đúng là mở một nghiên cứu mới, xác định trước mốc bắt đầu, xây lại đặc trưng và đánh giá hoàn toàn trong giai đoạn hiện đại. Cho đến khi có lần chạy đó, phần sau 2014 chỉ là một mô tả hậu kỳ có sức gợi ý, không phải kết luận xác nhận độc lập.

### Câu trả lời lớn về khả năng ứng dụng

Năm nghiên cứu cùng hỗ trợ một hệ thống **mô tả và kiểm tra**, chưa hỗ trợ một hệ thống **ra lệnh**. Sự khác biệt nằm ở đầu ra. Hệ thống mô tả trả lời: trạng thái nào đang xảy ra, lớp dữ liệu nào đồng thuận, lớp nào bất đồng và cần kiểm tra nguồn nào. Hệ thống ra lệnh phải trả lời thêm: nên mua hay bán, ở thời điểm nào, với xác suất và mức rủi ro nào. Bộ bằng chứng hiện chỉ đủ cho nhóm câu hỏi đầu.

Đây là một kết luận có giá trị lâu dài vì nó xác định đúng vị trí của dữ liệu trong quy trình đầu tư. Thay vì tiếp tục tìm cách biến mọi biến thành tín hiệu, dự án có thể xây một lớp quan sát đáng tin, có provenance và có ranh giới. Khi nghiên cứu mới đủ mạnh xuất hiện, một thành phần có thể được nâng vai trò mà không phải phá bỏ kiến trúc chung.

## 8. Cách đọc bằng chứng mà không cần biết thống kê

Một báo cáo nghiên cứu dễ gây sợ vì người đọc gặp nhiều con số trước khi biết chúng dùng để làm gì. Phần này đi theo hướng ngược lại: bắt đầu bằng câu hỏi đời thường, sau đó mới giải thích con số nào giúp trả lời câu hỏi đó. Người đọc không cần nhớ công thức. Họ chỉ cần giữ được ranh giới giữa điều đã thấy và điều đang suy ra.

### Câu hỏi thứ nhất: đây là quan sát hay dự báo?

Nếu báo cáo nói lợi suất tăng và cổ phiếu yếu hơn **trong cùng khoảng**, đó là quan sát cùng thời điểm. Nó giống việc thấy đường ướt và người đi đường cầm ô: hai hiện tượng xuất hiện cùng lúc. Ta chưa biết cái nào đến trước hoặc nguyên nhân nào đứng sau.

Nếu báo cáo nói một biến xuất hiện trước kết quả ở những ngày sau, đó mới là câu hỏi dự báo. Nhưng “xuất hiện trước” vẫn chưa đủ. Một chiếc đồng hồ hỏng cũng có thể đúng hai lần mỗi ngày. Quan hệ phải lặp lại trên những giai đoạn không dùng để tìm ra nó.

Khi đọc bất kỳ biểu đồ nào, hãy tìm nhãn thời gian. “Cùng kỳ” nghĩa là không được dùng để nói về phiên kế tiếp. “Năm phiên sau” nghĩa là có kết quả tương lai, nhưng vẫn cần biết quan hệ được tìm trong dữ liệu cũ hay kiểm tra trên dữ liệu mới.

### Câu hỏi thứ hai: kết quả có lớn đến mức đáng quan tâm không?

Một khác biệt có thể rất chắc về mặt tính toán nhưng quá nhỏ để thay đổi quyết định. Ngược lại, một khác biệt lớn trong mẫu nhỏ có thể rất không chắc chắn. Vì vậy người đọc cần nhìn cả độ lớn và khoảng bất định.

Hãy hình dung hai cửa hàng. Cửa hàng A bán trung bình hơn cửa hàng B một sản phẩm mỗi ngày, nhưng mỗi ngày doanh số dao động hàng trăm sản phẩm. Chênh lệch một sản phẩm khó có ý nghĩa vận hành. Nếu chênh lệch là năm mươi sản phẩm và lặp đều qua nhiều tháng, câu chuyện khác hẳn. Trong đầu tư cũng vậy: đừng để một dấu sao hoặc một giá trị nhỏ thay thế câu hỏi “khác biệt này có đủ để thay đổi hành động không?”.

Trong bộ nghiên cứu, ngưỡng về độ lớn được khóa trước ở nơi có mô hình dự báo. Điều đó ngăn việc thấy một cải thiện rất nhỏ rồi gọi nó là thành công. Với quan hệ mô tả, báo cáo dùng ngôn ngữ “đáng chú ý” hoặc “nhỏ” và không quy đổi thành lợi nhuận giao dịch nếu chưa có chiến lược được kiểm tra.

### Câu hỏi thứ ba: khoảng ước lượng nói gì?

Một ước lượng không phải sự thật chính xác đến nhiều chữ số. Nó là điểm giữa hợp lý nhất trong dữ liệu đã có. Khoảng đi cùng nó cho biết những giá trị nào còn phù hợp với độ nhiễu quan sát được.

Ví dụ minh họa: nếu một nghiên cứu ước tính trạng thái A đi cùng kết quả cao hơn 2%, nhưng khoảng hợp lý trải từ thấp hơn 1% đến cao hơn 5%, dữ liệu chưa loại trừ khả năng hiệu ứng bằng không hoặc ngược dấu. Không nên nói “A tạo thêm 2%”. Cách nói đúng là “ước lượng trung tâm cao hơn 2%, nhưng độ bất định còn bao gồm cả khả năng không cải thiện”.

Khoảng ước lượng trong biểu đồ bond cũng không phải khoảng dự báo. Nó mô tả sự không chắc chắn của quan hệ trung bình cùng kỳ, không cho biết VNINDEX phiên tới sẽ nằm trong vùng nào.

### Câu hỏi thứ tư: tại sao phải tính đến việc đã thử nhiều trường hợp?

Nếu tung một đồng xu đủ nhiều lần, sẽ có lúc xuất hiện một chuỗi mặt ngửa trông rất đặc biệt. Tương tự, khi nghiên cứu hàng trăm chỉ số, khoảng thời gian và kết quả, một vài hàng đẹp có thể xuất hiện chỉ vì số cơ hội quá lớn.

Việc điều chỉnh nhiều phép thử giống như nâng tiêu chuẩn cho một phát hiện sau khi biết đã mở rất nhiều cánh cửa. Nó không làm dữ liệu xấu đi; nó ngăn nhà nghiên cứu chọn đúng cánh cửa đẹp nhất rồi quên nói rằng hàng trăm cửa khác đã được mở.

Người đọc không cần nhớ tên phương pháp điều chỉnh. Chỉ cần hỏi: “Kết quả này còn đứng vững khi tính đến toàn bộ những trường hợp đã xem không?”. Trong báo cáo, các kết quả riêng lẻ ở nghiên cứu cổ phiếu từng nổi bật nhưng không qua cấp nhóm rộng hơn. Đó là lý do chúng không được đưa vào kết luận hỗ trợ.

### Câu hỏi thứ năm: “ngoài mẫu” có nghĩa gì?

Một học sinh đã xem đáp án có thể làm rất tốt đúng bộ đề đó. Để biết học sinh hiểu bài, cần một đề mới. Mô hình cũng vậy. Dữ liệu dùng để chọn biến và điều chỉnh tham số không thể đồng thời là bằng chứng cuối cùng rằng mô hình dự báo tốt.

Kiểm tra ngoài mẫu chia thời gian theo thứ tự. Mô hình chỉ học từ quá khứ rồi dự báo phần tiếp theo. Sau đó cửa sổ huấn luyện mở rộng và quá trình lặp lại. Cách làm này gần với vận hành hơn việc trộn ngẫu nhiên các ngày, vì thị trường tương lai không quay lại quá khứ để cung cấp dữ liệu.

Tuy vậy, “ngoài mẫu” không tự động nghĩa là dùng được. Mô hình có thể tốt hơn rất ít, chỉ tốt ở một vài giai đoạn hoặc đưa ra xác suất quá tự tin. Nghiên cứu đa biến là ví dụ rõ: kết quả tổng hợp năm phiên tốt hơn, nhưng chỉ hai trong sáu giai đoạn cải thiện và mức tự tin không khớp thực tế.

### Câu hỏi thứ sáu: kết quả có phụ thuộc một giai đoạn không?

Một chiến lược có thể thắng lớn trong một khủng hoảng và thua nhẹ trong mọi năm còn lại. Trung bình toàn bộ vẫn đẹp, nhưng người dùng không biết khủng hoảng tiếp theo bắt đầu khi nào. Nếu gần như toàn bộ lợi ích đến từ một thời kỳ, kết quả chưa đủ ổn định.

Trong báo cáo đa biến, phần lớn cải thiện tập trung trước 2014. Đây không phải chi tiết trang trí. Nó thay đổi cách hiểu: mô hình từng bắt được một cấu trúc lịch sử, nhưng bằng chứng hiện đại chưa đủ để coi cấu trúc đó còn hoạt động.

Khi xem biểu đồ theo giai đoạn, đừng chỉ đếm cột xanh và đỏ. Hãy hỏi giai đoạn tốt có điểm gì khác, sự khác biệt đó được xác định trước hay sau khi thấy kết quả, và liệu có quy tắc nhận biết từ dữ liệu có sẵn tại thời điểm quyết định hay không.

### Câu hỏi thứ bảy: xác suất có đáng tin không?

Nếu một mô hình nói “70% khả năng tăng” nhiều lần, khoảng bảy trong mười trường hợp tương tự nên tăng. Nếu thực tế chỉ khoảng năm trong mười, mô hình đang nói quá tự tin. Nó có thể vẫn sắp hạng một số trường hợp tốt hơn, nhưng con số 70% không được hiểu theo nghĩa thông thường.

Độ tin cậy xác suất quan trọng vì quyết định vị thế thường phụ thuộc mức tự tin, không chỉ hướng. Một mô hình nói đúng hướng nhưng xác suất méo có thể khiến người dùng đặt quy mô rủi ro sai. Do đó báo cáo không cho phép lấy xác suất hiện tại của mô hình đa biến làm căn cứ tăng tỷ trọng.

### Câu hỏi thứ tám: kết quả âm có nghĩa là gì?

“Chưa tìm thấy” không đồng nghĩa “đã chứng minh không tồn tại”. Nghiên cứu có thể thiếu dữ liệu, quan hệ có thể nhỏ, thay đổi theo thời kỳ hoặc phương pháp có thể thận trọng. Nghiên cứu cổ phiếu ghi rõ khả năng phát hiện hiệu ứng khóa chỉ khoảng 44%, nên nguy cơ bỏ sót còn đáng kể.

Nhưng giới hạn sức mạnh cũng không được dùng để cứu mọi giả thuyết. Khi một kết quả không được hỗ trợ, nó không thể trở thành tín hiệu chỉ vì “có thể nghiên cứu chưa đủ mạnh”. Trạng thái đúng là chưa kết luận; muốn nâng cấp phải có dữ liệu hoặc thiết kế mới được khóa trước.

### Một phiếu đọc nhanh cho mọi biểu đồ

Trước khi tin một hình, người đọc có thể trả lời bảy dòng:

1. Hình đang mô tả cùng thời điểm hay tương lai?
2. Đơn vị trên trục là gì?
3. Đây là dữ liệu thực nghiệm hay sơ đồ minh họa?
4. Kết quả thuộc toàn mẫu hay dữ liệu mới?
5. Độ lớn có đủ để quan tâm không?
6. Kết quả có lặp qua nhiều giai đoạn không?
7. Chú thích cấm suy diễn điều gì?

Nếu một biểu đồ không cho phép trả lời các câu đó, nó chưa đủ tốt để xuất hiện trong báo cáo dành cho nhà đầu tư.

### Cách đọc bốn hình chính của báo cáo

**Hình bond và cổ phiếu.** Mỗi chấm thể hiện ước lượng trung tâm về mức thay đổi cổ phiếu đi cùng một thay đổi lợi suất trong cùng khoảng. Đường ngang cho thấy vùng ước lượng còn hợp lý. Chấm nằm phía âm nói rằng trong dữ liệu nghiên cứu, lợi suất tăng thường đi cùng mức sinh lời cổ phiếu thấp hơn. Nó không nói một lần lợi suất tăng cụ thể sẽ làm chỉ số giảm đúng bằng con số đó. Các chỉ số còn chồng lấn cổ phiếu thành phần, nên bảy dòng không phải bảy cuộc thử nghiệm độc lập.

Khi nhìn hình này, người đọc nên hỏi hai câu: khoảng có nằm hoàn toàn một phía của không hay không, và tiêu đề có ghi rõ “cùng kỳ” hay không. Không cần ghi nhớ tên hệ số. Điều quan trọng là biết hình mô tả một quan hệ trung bình và ranh giới thời gian của nó.

**Sơ đồ giá, khối lượng và độ rộng.** Đây là sơ đồ khái niệm, không phải biểu đồ tần suất thực nghiệm. Ba ô được đặt cạnh nhau để nhắc rằng mỗi biến trả lời một câu hỏi khác nhau. Mũi tên quy trình, nếu có, chỉ hướng người dùng từ quan sát đến kiểm tra; nó không đại diện cho chuỗi nguyên nhân hoặc thứ tự đã được chứng minh.

Người đọc không nên đếm số trạng thái trong sơ đồ rồi suy ra xác suất. Ví dụ “giá tăng, độ rộng hẹp” chỉ là một trường hợp để học cách mô tả. Báo cáo chưa nói trạng thái này xảy ra bao nhiêu phần trăm hoặc sau đó thị trường giảm với tần suất nào.

**Hình sáu giai đoạn của mô hình đa biến.** Mỗi đoạn tương ứng một phần thời gian được để riêng để đánh giá. Màu “tốt hơn” nghĩa là mô hình có thêm biến giảm sai số so với chuẩn trong giai đoạn đó; màu “kém hơn” nghĩa là sai số tăng. Hai đoạn tốt không bị xóa, nhưng bốn đoạn còn lại cho thấy lợi ích không lặp đủ đều.

Không nên cộng chiều cao cột bằng mắt để kết luận hiệu quả. Kết quả tổng hợp đã được tính riêng và có cải thiện, nhưng công cụ bị từ chối vì độ lặp lại, chất lượng xác suất và sự tập trung theo thời kỳ. Hình này được thiết kế để ngăn một con số trung bình che mất cấu trúc theo thời gian.

**Thang bằng chứng của phân kỳ.** Các bậc đi từ quan sát trạng thái, qua liên hệ trong mẫu, kiểm tra trên dữ liệu mới đến công cụ vận hành. Một kết quả đứng ở bậc thấp không phải kết quả sai; nó chỉ chưa có quyền hạn của bậc cao hơn. Nghiên cứu phân kỳ hiện hỗ trợ việc mở điều tra, không hỗ trợ cảnh báo mua bán.

Thang này cũng giải thích vì sao một hàng riêng lẻ đẹp có thể bị chặn. Nếu cấp nhóm rộng hơn hoặc kiểm tra ngoài mẫu thất bại, hàng đó không được nhảy thẳng lên bậc vận hành. Không có đường tắt qua số lượng biểu đồ hoặc độ hấp dẫn của ví dụ.

### Biểu đồ tốt phải cho phép đọc mà không cần rê chuột

Con số cốt lõi, đơn vị và giới hạn phải nhìn thấy trực tiếp. Tooltip chỉ bổ sung chi tiết, không được giấu câu “không phải dự báo” hoặc “chỉ là minh họa”. Trên điện thoại, nhãn dài có thể xuống dòng nhưng không bị cắt; các hình nhiều chuỗi nên tách thành nhiều ô nhỏ thay vì ép vào hai trục.

Màu sắc không được mang toàn bộ ý nghĩa. Hình cần có nhãn chữ, ký hiệu hoặc mẫu đường để người đọc phân biệt khi in đen trắng hoặc khi có hạn chế về màu. Màu xanh không tự nghĩa là mua và màu đỏ không tự nghĩa là bán.

Một hình có thể chính xác về dữ liệu nhưng vẫn gây hiểu nhầm về thị giác. Trục bị cắt có thể phóng đại chênh lệch; hai trục tung có thể làm hai đường trông như đi cùng; sắp xếp chỉ các giai đoạn thuận lợi có thể che phần thất bại. Vì vậy QA biểu đồ phải kiểm tra cả số liệu, caption và cách hình dẫn mắt.

### Phân biệt ví dụ minh họa với bằng chứng

Báo cáo sử dụng ví dụ giả định để giúp người đọc hiểu cách suy nghĩ. Ví dụ luôn dùng những cụm như “giả sử” hoặc “tình huống minh họa” và không kèm tần suất được phát minh. Nó không được trích dẫn như bằng chứng rằng một trạng thái từng xảy ra trong lịch sử.

Ví dụ từ artifact thì khác. Nó phải gắn claim ID và chỉ được nói đúng giá trị, phạm vi cùng giới hạn đã khóa. Nếu một con số không có claim, nó không được đưa vào biểu đồ thực nghiệm. Sự phân biệt này giúp báo cáo phong phú hơn mà không tạo thêm phát hiện ngoài nghiên cứu.

## 9. Khung đọc thị trường sáu bước

Các nghiên cứu không tạo một chỉ báo tổng hợp. Chúng tạo ra một quy trình đặt câu hỏi. Quy trình sau có thể đưa vào nhật ký phân tích hoặc bảng điều khiển mà không biến dữ liệu thành lệnh giao dịch.

### Bước 1: Mô tả giá

Thị trường hoặc cổ phiếu đang tăng, giảm hay đi ngang trong khoảng quan sát? Mức thay đổi có bất thường so với lịch sử gần đây không? Chỉ ghi điều đã xảy ra.

### Bước 2: Kiểm tra mức tham gia

Khối lượng thay đổi thế nào? Chuyển động của chỉ số lan ra bao nhiêu cổ phiếu và ngành? Mục tiêu là biết điểm số chỉ số có đại diện cho thị trường rộng hay không.

### Bước 3: Đọc bối cảnh tài chính

Lợi suất có thay đổi cùng lúc không? Nếu có, điều kiện tài chính, định giá và nhóm ngành nhạy với chi phí vốn nào cần được xem lại? Không suy ra lợi suất dẫn thị trường.

### Bước 4: Nhận diện bất đồng

Có lớp dữ liệu nào đi ngược phần còn lại không? Ghi trạng thái bằng câu mô tả, không gắn nhãn mua bán. Bất đồng làm giảm mức chắc chắn của câu chuyện hiện tại.

### Bước 5: Đối chiếu nguồn độc lập

Kiểm tra kết quả kinh doanh, định giá, thông tin doanh nghiệp, chính sách, tỷ giá, thanh khoản và sự kiện vốn. Những nguồn này giúp phân biệt một trạng thái thị trường với một thay đổi có nguyên nhân cụ thể.

### Bước 6: Ghi quyết định và điều kiện làm nó sai

Nếu vẫn giữ luận điểm, ghi rõ dữ liệu nào sẽ bác bỏ nó. Quyết định cuối cùng dựa trên luận điểm, định giá và quản trị rủi ro; không dựa riêng vào bond, khối lượng, độ rộng hoặc phân kỳ.

## 10. Bốn tình huống ứng dụng

### Tình huống A: Chỉ số tăng nhưng danh mục không tăng

**Quan sát:** VNINDEX đi lên, nhưng độ rộng hẹp và danh mục ngoài nhóm vốn hóa lớn không hưởng lợi.

**Cách hiểu:** Câu “thị trường khỏe” cần được thu hẹp. Đợt tăng có thể đang tập trung.

**Kiểm tra tiếp:** Nhóm dẫn dắt, số ngành tham gia, thanh khoản và mức đóng góp của các mã lớn.

**Không được suy diễn:** Độ rộng hẹp chưa phải tín hiệu bán và chưa cho biết thời điểm đảo chiều.

### Tình huống B: Lợi suất tăng cùng lúc cổ phiếu giảm

**Quan sát:** Hai thị trường cùng phản ánh một bối cảnh kém thuận lợi hơn.

**Cách hiểu:** Định giá và chi phí vốn cần được xem lại, đặc biệt với nhóm nhạy lãi suất.

**Kiểm tra tiếp:** Chính sách, lạm phát, tỷ giá, cấu trúc nợ và lợi nhuận doanh nghiệp.

**Không được suy diễn:** Bond chưa được xác nhận là biến báo trước đợt giảm tiếp theo.

### Tình huống C: Giá giảm nhưng khối lượng tăng

**Quan sát:** Hoạt động giao dịch cao hơn trong lúc giá đi xuống.

**Cách hiểu:** Có trạng thái bất thường cần điều tra. Chưa biết đây là bán tháo, hấp thụ nguồn cung hay phản ứng sự kiện.

**Kiểm tra tiếp:** Tin tức, giao dịch lớn, sự kiện vốn, độ rộng và lịch sử thanh khoản.

**Không được suy diễn:** Không gọi đây là tạo đáy hoặc cơ hội mua chỉ từ hai biến.

### Tình huống D: Mô hình báo xác suất tăng cao

**Quan sát:** Một mô hình đa biến đưa ra mức tự tin cao hơn thông thường.

**Cách hiểu:** Trước hết phải kiểm tra mô hình có lặp lại ở giai đoạn gần đây và xác suất có khớp thực tế không.

**Kiểm tra tiếp:** Kết quả từng giai đoạn, chuẩn chỉ dùng giá, độ tin cậy xác suất và mức phụ thuộc vào dữ liệu cũ.

**Không được suy diễn:** Một điểm số tổng hợp đẹp không đủ để tăng tỷ trọng.

## 11. Những điều năm nghiên cứu cùng chưa chứng minh

### Chưa có tín hiệu độc lập ổn định

Không nghiên cứu nào hiện bàn giao một tín hiệu có thể đứng một mình để tạo lệnh giao dịch. Quan hệ cùng thời điểm, thứ tự trong mẫu và phân kỳ mô tả đều chưa vượt ranh giới này.

### Chưa có chuỗi nhân quả chung

Báo cáo không nói bond dẫn độ rộng, độ rộng dẫn giá rồi khối lượng xác nhận. Mỗi quan hệ được nghiên cứu riêng. Ghép chúng thành một câu chuyện chung sẽ tạo kết luận mới không có kiểm định chung.

Điều này cũng có nghĩa năm kết quả âm không thể được cộng lại để tuyên bố các đại lượng hoàn toàn không có giá trị. Mỗi nghiên cứu có độ nhạy và giới hạn khác nhau. Điều được phép nói là chưa có công cụ độc lập nào vượt các cổng hiện hành; điều không được phép nói là mọi quan hệ nhỏ đều đã bị loại trừ.

### “Chưa có tín hiệu” không đồng nghĩa “không có ứng dụng”

Một tín hiệu giao dịch phải đưa ra hướng hành động và chứng minh giá trị trên dữ liệu mới. Một lớp bối cảnh chỉ cần giúp người dùng mô tả trạng thái đúng hơn hoặc nhận ra khi luận điểm cần kiểm tra. Báo cáo này tìm thấy giá trị chủ yếu ở lớp thứ hai.

Sự phân biệt đó tránh hai cực đoan. Cực đoan thứ nhất là biến mọi quan hệ đẹp thành công cụ dự báo. Cực đoan thứ hai là bỏ toàn bộ dữ liệu chỉ vì nó không dự báo được. Quy trình đầu tư tốt cần cả dự báo có kiểm định lẫn quan sát bối cảnh có kỷ luật; hiện các nghiên cứu đóng góp cho phần quan sát.

### Kết quả âm không chứng minh hoàn toàn không tồn tại

Thiếu bằng chứng có thể đến từ quan hệ yếu, thay đổi theo thời kỳ, dữ liệu chưa đủ hoặc thiết kế có sức mạnh hạn chế. Đặc biệt ở cấp cổ phiếu, nguy cơ bỏ sót hiệu ứng nhỏ đã được ghi nhận.

### Không được cộng số liệu giữa các nghiên cứu

Mẫu, biến, khoảng thời gian và tiêu chuẩn đạt khác nhau. Việc nhiều chương cùng kết luận “chưa vận hành” không biến chúng thành năm phép thử độc lập cho cùng một null. Báo cáo chỉ tổng hợp cách hiểu, không thực hiện phân tích gộp.

## 12. Đưa kết quả vào dự án đang vận hành

### Bảng điều khiển thị trường

Có thể hiển thị riêng bốn lớp: giá, mức tham gia, độ rộng và bối cảnh lợi suất. Giao diện nên ưu tiên câu mô tả trạng thái. Không nên nén chúng thành một điểm “tăng giá/giảm giá” nếu điểm đó chưa có nghiên cứu riêng.

### Nhật ký luận điểm

Mỗi nhận định nên ghi: quan sát, điều chưa biết, dữ liệu cần kiểm tra, điều kiện vô hiệu hóa và quyết định cuối. Các lớp dữ liệu trong nghiên cứu phù hợp để điền ba ô đầu.

### Danh sách cần điều tra

Phân kỳ ở chỉ số hoặc cổ phiếu có thể tạo một hàng đợi kiểm tra. Mỗi mục cần đi kèm lý do, chất lượng dữ liệu và thông tin sự kiện. Danh sách này hỗ trợ phân tích viên, không tự gửi cảnh báo mua bán.

### Theo dõi mô hình nghiên cứu

Mô hình đa biến có thể tiếp tục chạy ở chế độ quan sát. Báo cáo định kỳ nên cho thấy kết quả theo giai đoạn, độ tin cậy xác suất và thay đổi so với chuẩn đơn giản. Chỉ mở lại đánh giá vận hành sau khi có thiết kế mới được khóa trước.

### Kiến trúc sản phẩm đề xuất

Một sản phẩm dài hạn nên có ba lớp thay vì một màn hình duy nhất.

**Lớp quan sát thị trường** hiển thị giá, khối lượng, độ rộng và lợi suất bằng đơn vị gốc. Mỗi ô cần cho biết khoảng thời gian, thời điểm cập nhật và nguồn. Người dùng có thể xem theo chỉ số, ngành hoặc cổ phiếu, nhưng không được thấy một điểm tổng hợp mua bán.

**Lớp diễn giải** chuyển dữ liệu thành câu trung tính. Ví dụ: “chỉ số tăng nhưng số mã tham gia giảm”, “giá giảm với hoạt động cao hơn lịch sử gần”, hoặc “lợi suất tăng cùng lúc nhóm nhạy chi phí vốn suy yếu”. Câu diễn giải phải nói rõ đây là quan sát, không phải dự báo. Khi dữ liệu thiếu hoặc chất lượng thấp, hệ thống nói “chưa đủ dữ liệu” thay vì điền bằng giá trị thay thế không được kiểm chứng.

**Lớp điều tra** chứa danh sách việc cần làm: kiểm tra sự kiện, báo cáo doanh nghiệp, thay đổi sở hữu, định giá, cấu trúc nợ hoặc thông tin chính sách. Mỗi mục có người phụ trách, ngày tạo, bằng chứng đã xem và lý do đóng. Lớp này biến một bất đồng thành công việc phân tích cụ thể mà không biến nó thành tín hiệu.

Ba lớp nên liên kết nhưng giữ quyền hạn riêng. Dữ liệu có thể tự động tạo câu mô tả. Câu mô tả có thể tự động mở một mục cần kiểm tra nếu đáp ứng quy tắc chất lượng. Nhưng chỉ con người hoặc một hệ thống quyết định đã được nghiên cứu riêng mới được thay đổi vị thế.

### Trạng thái và ngôn ngữ nên dùng

Sản phẩm nên ưu tiên các nhãn như “đồng thuận rộng”, “mức tham gia hẹp”, “bất đồng giá–khối lượng”, “bối cảnh lợi suất thay đổi” và “cần kiểm tra dữ liệu”. Tránh các nhãn “mạnh”, “yếu”, “tích cực”, “tiêu cực” nếu chúng dễ bị hiểu thành hành động mà chưa có chuẩn rõ ràng.

Mỗi nhãn phải có định nghĩa xem được ngay. “Mức tham gia hẹp” cần nói đang đo bao nhiêu mã và so với khoảng nào. “Khối lượng cao” cần nói cao hơn trung vị hay trung bình của bao nhiêu phiên. “Phân kỳ” cần nói chính xác hai hướng nào đang bất đồng. Sự minh bạch này quan trọng hơn màu sắc hoặc hiệu ứng giao diện.

Không nên dùng màu đỏ và xanh làm ngôn ngữ duy nhất. Ngoài vấn đề tiếp cận, người dùng có thể diễn giải đỏ là bán và xanh là mua. Biểu tượng, nhãn chữ và chú thích phải đủ để hiểu trạng thái. Màu chỉ hỗ trợ phân biệt dữ liệu.

### Kiểm soát chất lượng và lịch sử thay đổi

Mỗi quan sát cần gắn với phiên bản dữ liệu và định nghĩa. Nếu cách tính độ rộng, danh sách cổ phiếu hoặc điều chỉnh giá thay đổi, hệ thống phải ghi ngày và ảnh hưởng. Nghiên cứu cấp cổ phiếu đã cho thấy một sửa chữa dữ liệu có thể thay đổi kết luận; sản phẩm vận hành không thể coi provenance là phần phụ.

Các trạng thái từng hiển thị phải có khả năng tái tạo. Khi người dùng mở lại nhật ký ba tháng trước, họ cần thấy dữ liệu và định nghĩa tại thời điểm đó, không phải trạng thái được tính lại bằng vũ trụ hiện tại. Đây là điều kiện để đánh giá liệu quy trình có giúp ích hay chỉ tạo cảm giác hợp lý sau sự kiện.

Mỗi quý, nhóm vận hành nên xem lại ba thống kê quy trình: bao nhiêu mục “cần kiểm tra” được tạo, bao nhiêu mục dẫn đến thay đổi luận điểm, và bao nhiêu mục là do lỗi dữ liệu hoặc sự kiện đã biết. Đây không phải tỷ lệ thắng giao dịch. Nó đo chất lượng của lớp quan sát và chi phí mà nó tạo ra cho người dùng.

### Ranh giới quyền hạn

Không thành phần nào trong lớp nghiên cứu hiện hành được tự tăng tỷ trọng, giảm tỷ trọng hoặc gửi lệnh. Nếu sau này một mô hình đạt tiêu chuẩn vận hành, nó phải được triển khai thành mô-đun riêng với phiên bản, giới hạn rủi ro, cơ chế dừng và theo dõi suy giảm. Việc đặt nó cạnh dashboard bối cảnh không làm hai lớp có cùng thẩm quyền.

Ranh giới này giúp sản phẩm có ích ngay mà không chờ một mô hình hoàn hảo. Nó cũng ngăn việc một nhãn vô hại dần biến thành tín hiệu qua thói quen sử dụng mà không có lần phê duyệt nghiên cứu nào.

## 13. Một buổi đọc thị trường nên diễn ra thế nào?

Khung sáu bước chỉ có giá trị khi nó làm thay đổi cách người dùng làm việc. Một buổi đọc thị trường không nên bắt đầu bằng việc săn tín hiệu mạnh nhất. Nó nên bắt đầu bằng việc dựng một mô tả mà người khác có thể kiểm tra.

### Trước giờ giao dịch

Người phân tích ghi ba dòng ngắn: diễn biến giá gần nhất, mức tham gia của cổ phiếu và thay đổi đáng chú ý trong bối cảnh tài chính. Nếu có bất đồng, trạng thái được đánh dấu để theo dõi. Chưa có kết luận về hướng phiên mới.

Ví dụ: “VNINDEX tăng nhờ nhóm vốn hóa lớn; độ rộng không mở rộng tương ứng; lợi suất không có thay đổi nổi bật.” Câu này tốt hơn nhãn “tăng giá” vì nó nói rõ điều gì đang nâng chỉ số và điều gì chưa đồng thuận.

### Trong phiên

Mục tiêu là nhận biết dữ liệu mới có làm thay đổi mô tả ban đầu không. Độ rộng có mở rộng sang nhiều ngành? Khối lượng tăng ở toàn thị trường hay chỉ tại vài mã có sự kiện? Chuyển động của lợi suất có trùng thời điểm với thay đổi ở nhóm nhạy chi phí vốn không?

Người dùng không cần phản ứng với mọi thay đổi. Chỉ những quan sát làm sai luận điểm hoặc thay đổi mức rủi ro mới cần đi vào quyết định. Điều này giảm nguy cơ biến bảng điều khiển thành nguồn nhiễu liên tục.

### Sau phiên

Nhật ký cần tách bốn cột: điều đã quan sát, cách diễn giải, dữ liệu còn thiếu và quyết định. Nếu quyết định là giữ nguyên vị thế, lý do cũng phải được ghi. Sau một thời gian, nhật ký cho phép kiểm tra người dùng có thường xuyên biến bất đồng thành dự báo quá sớm hay không.

### Nguyên tắc thiết kế bảng điều khiển

Một sản phẩm phục vụ quy trình này nên giữ các lớp dữ liệu tách biệt. Giá, khối lượng, độ rộng và lợi suất có thể nằm trong cùng trang, nhưng không nên bị trộn thành một đồng hồ duy nhất. Người dùng cần thấy nguồn, thời điểm cập nhật và giới hạn của từng lớp.

Các trạng thái bất đồng nên dùng nhãn trung tính như “cần kiểm tra” hoặc “mức tham gia hẹp”. Màu đỏ và xanh dễ bị hiểu thành bán và mua; vì vậy màu chỉ nên biểu thị hướng dữ liệu, không biểu thị hành động. Tooltip cần trả lời “đang quan sát gì” thay vì “nên làm gì”.

Nếu hệ thống hiển thị kết quả mô hình, nó phải đặt cạnh chuẩn so sánh và lịch sử độ lặp lại. Một xác suất đơn lẻ không đủ. Người dùng cần biết mô hình có từng tốt hơn ở giai đoạn gần đây hay không và mức tự tin có khớp với kết quả thực tế không.

### Tiêu chuẩn để nâng vai trò trong tương lai

Một lớp dữ liệu chỉ nên được nâng từ “bối cảnh” lên “hỗ trợ quyết định” sau khi có nghiên cứu riêng chứng minh giá trị bổ sung trên dữ liệu mới. Muốn trở thành tín hiệu vận hành, nó còn phải lặp qua nhiều giai đoạn, có mức cải thiện đủ lớn, chịu được chi phí và không phụ thuộc một thời kỳ đặc biệt.

Cho đến khi đạt các điều kiện đó, sản phẩm nên tối ưu cho sự rõ ràng của quan sát. Đây không phải nhượng bộ. Một hệ thống giúp người dùng tránh kết luận quá sớm đã có giá trị thực tế, dù nó không dự báo giá ngày mai.

## 14. Casebook: tám tình huống để thực hành cách đọc

Các tình huống dưới đây là **minh họa giả định**, không phải phát hiện lịch sử mới và không dùng để chứng minh tần suất xảy ra. Mục tiêu là cho thấy cùng một dữ liệu có thể được chuyển thành quy trình kiểm tra như thế nào. Mỗi tình huống bắt đầu bằng điều quan sát được, chỉ ra kết luận vội vàng, rồi xây một cách đọc có ranh giới.

### Tình huống 1: VNINDEX tăng mạnh nhưng danh mục gần như đứng yên

**Quan sát.** Chỉ số tăng trong nhiều phiên, nhưng phần lớn cổ phiếu trong danh mục không tăng. Độ rộng cho thấy số mã tham gia thấp hơn ấn tượng do điểm số chỉ số tạo ra.

**Kết luận vội vàng.** “Danh mục của tôi chọn sai hoàn toàn” hoặc “độ rộng hẹp nên thị trường sắp giảm”. Cả hai câu đều đi xa hơn dữ liệu. Danh mục có thể khác chỉ số về ngành và vốn hóa; đợt tăng tập trung cũng có thể tiếp tục.

**Cách đọc có kỷ luật.** Tách hiệu ứng chỉ số khỏi hiệu ứng danh mục. Xác định các mã đóng góp lớn nhất cho VNINDEX, số ngành đang tham gia và mức sinh lời của nhóm vốn hóa tương ứng với danh mục. Sau đó kiểm tra luận điểm từng cổ phiếu: kết quả kinh doanh, định giá và chất xúc tác có thay đổi không.

**Quyết định.** Không bán danh mục chỉ vì độ rộng hẹp. Có thể điều chỉnh cách so chuẩn, rà lại mức tập trung hoặc giảm độ chắc chắn về câu “toàn thị trường đang khỏe”. Nhật ký cần ghi rõ chênh lệch đến từ cấu trúc chỉ số hay từ luận điểm doanh nghiệp bị sai.

### Tình huống 2: Lợi suất tăng nhanh trong lúc cổ phiếu giảm

**Quan sát.** Lợi suất và chỉ số cổ phiếu thay đổi theo hướng tạo cảm giác điều kiện tài chính kém thuận lợi hơn trong cùng khoảng.

**Kết luận vội vàng.** “Bond đã phát tín hiệu bán” hoặc “cổ phiếu chắc chắn còn giảm”. Nghiên cứu không xác nhận thứ tự báo trước ổn định giữa hai thị trường.

**Cách đọc có kỷ luật.** Xem lại định giá của các tài sản nhạy với tỷ lệ chiết khấu, cấu trúc nợ và thời điểm tái cấp vốn. Kiểm tra xem thay đổi lợi suất đi cùng thông tin chính sách, lạm phát, tỷ giá hay cung cầu trái phiếu. So sánh phản ứng giữa các ngành thay vì giả định toàn thị trường chịu tác động giống nhau.

**Quyết định.** Nếu luận điểm doanh nghiệp phụ thuộc mạnh vào chi phí vốn, người dùng có thể cập nhật kịch bản định giá. Việc thay đổi vị thế phải xuất phát từ định giá và rủi ro đã cập nhật, không từ hướng lợi suất đơn lẻ.

### Tình huống 3: Giá tăng nhưng khối lượng thấp hơn lịch sử gần

**Quan sát.** Một cổ phiếu tăng giá trong vài phiên với số lượng giao dịch thấp hơn mức thường thấy.

**Kết luận vội vàng.** “Đợt tăng không được xác nhận nên sẽ thất bại.” Nghiên cứu không trao cho khối lượng vai trò xác nhận xu hướng như một quy tắc chung.

**Cách đọc có kỷ luật.** Kiểm tra khối lượng thấp vì toàn thị trường trầm lắng hay chỉ riêng cổ phiếu. Xem độ rộng ngành, chênh lệch mua bán, free-float, lịch sự kiện và nguồn cung cổ phiếu. Giá có thể tăng trong thanh khoản thấp vì người bán không sẵn sàng bán, chứ không chỉ vì người mua yếu.

**Phản ví dụ.** Hai đợt tăng có cùng khối lượng thấp nhưng một đợt đi cùng cải thiện lợi nhuận doanh nghiệp, đợt kia chỉ dựa vào tin đồn. Trạng thái giá–khối lượng giống nhau không làm hai luận điểm có cùng chất lượng.

**Quyết định.** Không mua thêm hoặc bán ra chỉ vì nhãn “không xác nhận”. Dùng trạng thái này để đặt câu hỏi về thanh khoản và độ bền của luận điểm cơ bản.

### Tình huống 4: Giá giảm và khối lượng tăng mạnh

**Quan sát.** Cổ phiếu giảm trong phiên có hoạt động giao dịch cao bất thường.

**Kết luận vội vàng.** Có hai câu chuyện đối lập thường được kể: “bán tháo nên còn giảm” và “rũ bỏ nên sắp tạo đáy”. Cùng một hình ảnh không thể đồng thời chứng minh cả hai.

**Cách đọc có kỷ luật.** Kiểm tra thông tin doanh nghiệp, giao dịch thỏa thuận, thay đổi sở hữu, tái cân bằng chỉ số, ngày không hưởng quyền và diễn biến của ngành. So khối lượng với lịch sử của chính mã và xem hoạt động tập trung ở một phiên hay kéo dài. Nếu dữ liệu điều chỉnh sự kiện chưa đáng tin, trạng thái cần gắn cờ chất lượng.

**Phản ví dụ.** Một phiên giảm khối lượng cao do tin lợi nhuận suy yếu khác với phiên giảm do quỹ tái cơ cấu cuối kỳ. Biểu đồ giá và khối lượng có thể giống nhau nhưng nguyên nhân, định giá và phản ứng hợp lý hoàn toàn khác.

**Quyết định.** Đưa mã vào hàng đợi điều tra. Chỉ thay đổi vị thế sau khi nguồn độc lập làm thay đổi luận điểm hoặc giới hạn rủi ro bị vi phạm.

### Tình huống 5: Độ rộng cải thiện nhưng VNINDEX chưa tăng

**Quan sát.** Nhiều cổ phiếu hoặc ngành bắt đầu cải thiện trong khi điểm số chỉ số còn đi ngang vì nhóm vốn hóa lớn chưa tham gia.

**Kết luận vội vàng.** “Độ rộng đang báo trước một nhịp tăng chắc chắn.” Bộ nghiên cứu chưa xác nhận độ rộng tạo dự báo ổn định cho VNINDEX.

**Cách đọc có kỷ luật.** Mô tả rằng mức tham gia đang rộng hơn và kiểm tra liệu thay đổi có trải qua nhiều ngành, có đủ thanh khoản và có đi cùng cải thiện cơ bản hay không. Xác định phần khác biệt giữa chỉ số vốn hóa và trải nghiệm của danh mục cân bằng hơn.

**Quyết định.** Độ rộng có thể làm người dùng xem lại cách mô tả thị trường và danh sách theo dõi. Nó chưa đủ để tăng tỷ trọng chung. Nếu muốn kiểm tra khả năng báo trước, cần một nghiên cứu mới khóa định nghĩa, khoảng thời gian và chuẩn so sánh trước khi xem kết quả.

### Tình huống 6: Mô hình đưa ra xác suất tăng 80%

**Quan sát.** Màn hình mô hình hiển thị xác suất cao, trong khi các dữ liệu khác không có thay đổi rõ.

**Kết luận vội vàng.** “Mô hình rất tự tin nên cơ hội tốt.” Con số xác suất chỉ có nghĩa nếu được căn chỉnh: những trường hợp được gọi 80% phải xảy ra gần tám trong mười lần trên dữ liệu mới.

**Cách đọc có kỷ luật.** Xem kết quả mô hình so với chuẩn chỉ dùng giá, lịch sử theo sáu giai đoạn và chất lượng xác suất. Kiểm tra lợi ích có tập trung ở dữ liệu cũ hay không. Nếu mô hình chỉ tốt trong hai giai đoạn và xác suất nói quá tự tin, 80% không được hiểu theo nghĩa thông thường.

**Quyết định.** Không tăng vị thế từ điểm số này. Ghi dự báo vào chế độ giám sát để đánh giá về sau. Một mô hình chưa đạt có thể tạo dữ liệu nghiên cứu mới, nhưng không được dần trở thành tín hiệu chỉ vì người dùng quen nhìn nó.

### Tình huống 7: Nhiều màn hình cùng chuyển xấu

**Quan sát.** Chỉ số giảm, độ rộng thu hẹp, khối lượng tăng và lợi suất thay đổi trong cùng khoảng.

**Kết luận vội vàng.** “Bốn tín hiệu độc lập cùng xác nhận xu hướng giảm.” Các màn hình có thể cùng phản ứng với một sự kiện và không độc lập. Chương trình nghiên cứu cũng chưa kiểm định một chuỗi chung giữa bốn lớp.

**Cách đọc có kỷ luật.** Viết một câu mô tả tổng hợp nhưng giữ nguyên nguồn: giá đang giảm, phạm vi tham gia suy yếu, hoạt động tăng và bối cảnh lợi suất thay đổi. Sau đó tìm nguyên nhân độc lập: thông tin chính sách, lợi nhuận, tỷ giá, sự kiện ngành hoặc thay đổi dòng vốn. Đánh giá danh mục theo độ nhạy thực tế thay vì coi bốn màn hình là bốn phiếu.

**Quyết định.** Có thể giảm rủi ro nếu giới hạn danh mục hoặc luận điểm bị vi phạm, nhưng lý do phải là quản trị rủi ro và bằng chứng bổ sung. Báo cáo không cung cấp trọng số để cộng bốn trạng thái thành một mức bán.

### Tình huống 8: Các màn hình bất đồng hoàn toàn

**Quan sát.** Chỉ số tăng, độ rộng hẹp, khối lượng không đổi và lợi suất đi ngang. Không có câu chuyện duy nhất bao quát tất cả.

**Kết luận vội vàng.** “Phân kỳ càng lớn thì đảo chiều càng gần.” Bất đồng có thể kéo dài; không có đồng hồ đếm ngược nào được xác nhận.

**Cách đọc có kỷ luật.** Thu hẹp phạm vi của nhận định. Có thể chỉ một nhóm vốn hóa lớn đang tăng, trong khi phần còn lại chưa tham gia. Xem danh mục có tiếp xúc với nhóm đó không và nguyên nhân tăng có bền theo luận điểm doanh nghiệp hay không. Ghi rõ những lớp chưa đồng thuận thay vì cố ép chúng vào một nhãn.

**Quyết định.** Hạ mức chắc chắn, không nhất thiết hạ vị thế. Đặt điều kiện theo dõi: độ rộng mở rộng, nhóm dẫn dắt suy yếu, hoặc thông tin cơ bản thay đổi. Hành động chỉ xảy ra khi điều kiện gắn với luận điểm hoặc rủi ro được kích hoạt.

### Mẫu nhật ký dùng cho mọi tình huống

Một ghi chú tốt có thể chỉ dài một trang nhưng phải đủ bảy phần:

1. **Quan sát:** dữ liệu nào đã thay đổi, trong khoảng nào và đơn vị gì.
2. **Chất lượng dữ liệu:** nguồn, thời điểm cập nhật, thiếu dữ liệu hoặc sự kiện cần điều chỉnh.
3. **Diễn giải được phép:** câu mô tả hẹp nhất phù hợp với bằng chứng.
4. **Điều chưa biết:** hướng tương lai, nguyên nhân hoặc xác suất nào chưa được xác nhận.
5. **Nguồn kiểm tra độc lập:** doanh nghiệp, định giá, chính sách, ngành, sở hữu hoặc thanh khoản.
6. **Quyết định:** giữ, giảm, tăng hay chưa hành động, cùng lý do không dựa riêng vào trạng thái.
7. **Điều kiện làm sai:** dữ liệu nào sẽ buộc người dùng thay đổi luận điểm.

Sau một quý, nhóm đầu tư có thể xem lại nhật ký để tìm lỗi quy trình: có thường biến khối lượng thành xác nhận không, có gọi độ rộng hẹp là tín hiệu bán không, hay có dùng điểm mô hình mà không xem lịch sử độ tin cậy không. Đây là cách bộ nghiên cứu tạo giá trị vận hành mà không cần giả vờ đã có máy dự báo.

## 15. Chương trình nghiên cứu tiếp theo

Giai đoạn tiếp theo không cần thử vô hạn chỉ báo. Ba hướng có giá trị hơn:

1. **Cải thiện dữ liệu lịch sử:** danh sách cổ phiếu đúng tại từng thời điểm, sự kiện doanh nghiệp và chất lượng khối lượng.
2. **Khóa nghiên cứu hiện đại:** huấn luyện và đánh giá từ giai đoạn sau 2014 theo thiết kế định trước.
3. **Kiểm tra ứng dụng cụ thể:** thay vì hỏi “có dự báo thị trường không”, hỏi một trạng thái có giúp một quyết định xác định tốt hơn chuẩn hay không, với chi phí và rủi ro được ghi rõ.

Mỗi nghiên cứu mới cần giữ bộ khung quản trị đã hình thành: khóa giả thuyết, bảo toàn nguồn, đối chiếu toàn bộ ma trận, điều chỉnh nhiều phép thử, kiểm tra trên dữ liệu mới và gắn từng kết luận về đúng bằng chứng gốc.

### Những lần sửa sai đã thay đổi điều gì?

Giá trị dài hạn của chương trình không chỉ nằm ở kết quả cuối mà còn ở những lần kết quả phải thay đổi sau kiểm toán. Các lần sửa cho thấy một báo cáo thuyết phục về hình thức vẫn có thể sai ở dữ liệu, thứ tự kiểm tra hoặc cách nâng kết luận.

Trong nghiên cứu đa biến, một lỗi cách đọc kiểu dữ liệu từng làm thay đổi cách phân loại kết quả. Sau khi sửa, phát hiện năm phiên vẫn còn ở mức tổng hợp nhưng bị hạ đúng vì chỉ tốt ở hai trong sáu giai đoạn, xác suất không đáng tin và lợi ích tập trung ở thời kỳ cũ. Bài học là verdict phải được suy từ cổng đã khóa, không từ câu chuyện mà người viết muốn kể.

Trong nghiên cứu phân kỳ cấp chỉ số, việc chạy lại số lần mô phỏng đầy đủ và sửa phần tổng hợp theo nhóm làm xuất hiện một kết quả lịch sử mà bản trước đã bỏ sót. Nhưng kiểm tra ngoài mẫu vẫn không cho phép nâng thành cảnh báo. Bài học là một sửa chữa có thể khôi phục phát hiện mà không thay đổi ranh giới ứng dụng.

Trong nghiên cứu từng cổ phiếu, kiểm toán phát hiện điều chỉnh sự kiện doanh nghiệp chưa thực sự được áp dụng và phần cuối chuỗi thiếu dữ liệu tương lai bị mã hóa như kết quả hợp lệ. Sau khi xây lại, những phát hiện mô tả biến mất. Bài học là target và điều chỉnh dữ liệu có thể quyết định toàn bộ kết luận; không audit nào chỉ nhìn bảng cuối là đủ.

Ngoài ra, hệ thống phân cấp từng cho phép một kết quả cấp con được giữ dù cấp cha thất bại. Sửa recursive ancestor gate đã loại bỏ những phát hiện riêng lẻ đó. Đây chính là vấn đề chọn ví dụ đẹp trong nhiều lát cắt: một cổ phiếu hoặc một khoảng thời gian không được đại diện cho cả nhóm nếu tầng rộng hơn không hỗ trợ.

Những sửa chữa này không làm chương trình kém đáng tin. Ngược lại, lịch sử thay đổi được giữ lại cho thấy kết luận hiện hành đã chịu áp lực kiểm tra. Điều quan trọng là không xóa phiên bản sai, không âm thầm thay hash và không để báo cáo cũ tiếp tục được trình bày như authority hiện hành.

Đối với người đọc phổ thông, bài học đơn giản là: đừng chỉ hỏi “kết quả là gì?”, hãy hỏi thêm “kết quả này đã từng thay đổi sau kiểm tra nào?”. Một báo cáo trưởng thành phải kể được cả hai.

## 16. Kết luận lớn

Chương trình nghiên cứu không tìm thấy chiếc máy dự báo mà trực giác kỹ thuật thường hứa hẹn. Kết quả quan trọng hơn là biết chính xác từng lớp dữ liệu có thể làm gì.

Bond giúp đọc bối cảnh tài chính hiện tại. Giá, khối lượng và độ rộng giúp mô tả mức tham gia. Phân kỳ giúp nhận ra nơi một luận điểm cần được kiểm tra thêm. Mô hình đa biến cho thấy một kết quả trung bình đẹp vẫn có thể thất bại khi đòi hỏi độ lặp lại và xác suất đáng tin.

Nhà đầu tư có thể dùng các kết quả này ngay trong quy trình phân tích, nhưng ở vai trò khiêm tốn: đặt câu hỏi tốt hơn, giảm tự tin khi dữ liệu bất đồng và tìm bằng chứng độc lập trước khi hành động.

Kết luận cuối cùng là: **dữ liệu đã cải thiện cách đọc thị trường; nó chưa thay thế phán đoán đầu tư**.

## Từ điển đọc báo cáo bằng ngôn ngữ phổ thông

### Cùng thời điểm

Hai đại lượng thay đổi trong cùng khoảng quan sát. Điều này giúp mô tả bối cảnh nhưng không cho biết bên nào đến trước. Trong báo cáo bond, quan hệ cùng thời điểm không được dùng để dự báo phiên sau.

### Đi trước

Một thay đổi xuất hiện trước thay đổi khác theo thứ tự thời gian trong dữ liệu lịch sử. Đi trước không đồng nghĩa gây ra và cũng không bảo đảm dự báo được trên dữ liệu mới. Giá đi trước khối lượng trong mẫu là ví dụ.

### Trong mẫu

Phần dữ liệu được dùng để xây giả thuyết, chọn cấu hình hoặc ước tính mô hình. Kết quả trong mẫu hữu ích để khám phá nhưng thường đẹp hơn khả năng thực tế vì mô hình đã được điều chỉnh theo chính dữ liệu đó.

### Ngoài mẫu

Phần dữ liệu được giữ lại khỏi quá trình xây mô hình và dùng để kiểm tra sau đó. Trong chuỗi thời gian, việc chia phải theo thời gian để tương lai không lọt vào quá khứ. Ngoài mẫu là điều kiện cần cho dự báo, nhưng chưa đủ để thành công cụ.

### Chuẩn so sánh

Cách làm đơn giản mà mô hình mới phải vượt qua. Ví dụ, khi hỏi khối lượng có thêm giá trị không, chuẩn hợp lý là mô hình đã dùng thông tin giá. Nếu chuẩn quá yếu, mô hình phức tạp có thể thắng mà không tạo giá trị thật.

### Sai số dự báo

Khoảng cách giữa điều mô hình dự báo và điều thực tế xảy ra. Sai số thấp hơn là tốt hơn. Với xác suất, sai số còn phạt mô hình khi quá tự tin mà sai. Không nên quy đổi một thay đổi của sai số thành phần trăm lợi nhuận.

### Độ lặp lại theo giai đoạn

Mức độ kết quả xuất hiện ở nhiều đoạn thời gian khác nhau. Một cải thiện chỉ đến từ một giai đoạn có thể làm trung bình đẹp nhưng khó dùng, vì người dùng không biết trước khi nào giai đoạn đó quay lại.

### Độ tin cậy của xác suất

Mức khớp giữa xác suất mô hình nói và tần suất thực tế. Nếu nhóm dự báo 80% chỉ xảy ra khoảng một nửa số lần, xác suất không đáng tin theo nghĩa thông thường dù mô hình vẫn có thể sắp hạng được một phần.

### Khoảng ước lượng

Vùng giá trị còn hợp lý quanh ước lượng trung tâm, phản ánh độ nhiễu trong dữ liệu. Khoảng này không phải khoảng mà giá tương lai chắc chắn sẽ nằm trong đó. Nếu khoảng bao gồm không, dữ liệu chưa loại trừ khả năng không có khác biệt.

### Điều chỉnh nhiều phép thử

Cách nâng tiêu chuẩn khi nghiên cứu đã xem nhiều chỉ số, khoảng thời gian hoặc kết quả. Mục tiêu là giảm nguy cơ chọn nhầm một phát hiện ngẫu nhiên trong hàng trăm trường hợp. Người đọc chỉ cần nhớ rằng một hàng đẹp phải được đánh giá trong bối cảnh toàn bộ những hàng đã thử.

### Cấp cha và cấp con

Cấp con là trường hợp cụ thể, chẳng hạn một cổ phiếu ở một khoảng thời gian. Cấp cha là nhóm rộng hơn mà trường hợp đó thuộc về. Một kết quả riêng lẻ không được nâng nếu nhóm rộng hơn thất bại, vì nó có thể chỉ là lát cắt may mắn.

### Độ lớn có ý nghĩa thực tế

Mức cải thiện đủ lớn để đáng quan tâm, không chỉ khác không về mặt tính toán. Một mô hình tốt hơn rất ít có thể không bù được chi phí, độ trễ, sai số dữ liệu hoặc rủi ro triển khai.

### Sức mạnh phát hiện

Khả năng thiết kế nhận ra một hiệu ứng nếu hiệu ứng đó thực sự tồn tại ở mức giả định. Sức mạnh thấp làm tăng nguy cơ bỏ sót. Nó yêu cầu diễn giải kết quả âm thận trọng nhưng không cho phép gọi một kết quả thất bại là tín hiệu.

### Vũ trụ cổ phiếu đúng tại từng thời điểm

Danh sách mã thực sự tồn tại và đủ điều kiện ở mỗi ngày lịch sử. Nếu chỉ dùng các mã đang hoạt động hiện nay, nghiên cứu có thể bỏ qua doanh nghiệp đã hủy niêm yết hoặc rời sàn, làm bức tranh quá sạch so với thực tế.

### Sự kiện doanh nghiệp

Chia tách, cổ tức, phát hành và các thay đổi vốn có thể tạo bước nhảy ở giá hoặc khối lượng không phản ánh hành vi giao dịch thông thường. Dữ liệu cần điều chỉnh và kiểm tra; một điều chỉnh trung bình tốt hơn không có nghĩa mọi sự kiện đã được xử lý hoàn hảo.

### Phân kỳ

Trạng thái hai lớp dữ liệu đi khác hướng theo định nghĩa đã chọn. Phân kỳ là mô tả về bất đồng. Bộ nghiên cứu chưa xác nhận nó là cảnh báo đảo chiều hoặc tín hiệu mua bán ổn định.

### Độ rộng

Cách mô tả bao nhiêu cổ phiếu cùng tham gia chuyển động. Độ rộng giúp biết chỉ số tăng nhờ nhiều mã hay vài mã lớn. Nó không tự nói đợt tăng bền hay sắp đảo chiều.

### Bối cảnh

Thông tin giúp hiểu môi trường hiện tại nhưng chưa đưa ra hành động. Bond, khối lượng và độ rộng chủ yếu đóng vai trò này trong kết luận hiện hành.

### Tín hiệu vận hành

Một đầu ra đã chứng minh giá trị bổ sung trên dữ liệu mới, đủ lớn, lặp qua thời gian, có mức tự tin đáng tin và có quy tắc triển khai cùng quản trị rủi ro. Không thành phần nào trong năm nghiên cứu hiện đạt định nghĩa này.

### Claim và nguồn bằng chứng

Claim là một câu kết luận được phép sử dụng. Mỗi claim trong hệ thống phải trỏ tới artifact, khóa truy xuất, hash và giới hạn. Báo cáo HTML trình bày claim nhưng không trở thành nguồn thực nghiệm thay cho dữ liệu gốc.

## Phụ lục nguồn và giới hạn

- [A-CONTEMPORANEOUS]: quan hệ cùng thời điểm giữa thay đổi lợi suất và một số chỉ số; thành phần chỉ số chồng lấn, không phải dự báo.
- [A-GRANGER-NULL]: 300 kiểm tra hai chiều theo ngày và tháng không có survivor sau điều chỉnh; không chứng minh mọi hiệu ứng nhỏ vắng mặt.
- [B-67]: giá đi trước khối lượng ở dữ liệu ngày trong mẫu; không ổn định trên dữ liệu mới.
- [B-52]: không kết quả giá–khối lượng–độ rộng nào đạt mức vận hành.
- [C-70]: kết quả tổng hợp năm phiên có cải thiện và vượt kiểm tra ban đầu nhưng thất bại các cổng ổn định.
- [C-72]: chỉ 2/6 giai đoạn cải thiện.
- [D-102]: phân kỳ cấp chỉ số không tạo ứng viên cảnh báo vận hành.
- [E-66]: R6 không có verdict mô tả hoặc vận hành ở cấp cổ phiếu.
- [E-95]: nghiên cứu cổ phiếu có khả năng phát hiện hiệu ứng khóa khoảng 0,44, nên không loại trừ mọi hiệu ứng nhỏ.

Mỗi claim map tới artifact, khóa truy xuất, SHA256 và limitation trong `14_claim_usage_matrix.json`. HTML chỉ là sản phẩm trình bày, không phải nguồn bằng chứng.
