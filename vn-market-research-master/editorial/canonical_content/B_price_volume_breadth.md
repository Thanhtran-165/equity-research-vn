# Giá, khối lượng và độ rộng: ba góc nhìn, không phải một chuỗi dự báo

## Câu trả lời ngắn

Giá cho biết thị trường đã đi đâu. Khối lượng cho biết có bao nhiêu giao dịch đi cùng chuyển động đó. Độ rộng cho biết chuyển động lan ra nhiều cổ phiếu hay chỉ tập trung ở một nhóm nhỏ. Ba lớp dữ liệu giúp nhà đầu tư mô tả chất lượng của trạng thái thị trường.

Nghiên cứu tìm thấy một số quan hệ trong mẫu, đáng chú ý nhất là giá từng xuất hiện trước thay đổi khối lượng ở dữ liệu ngày. Quan hệ này không lặp lại đủ ổn định trên dữ liệu chưa dùng để xây mô hình. Vì vậy, kết quả không cho phép nói khối lượng dự báo giá, xác nhận xu hướng hay tạo thành mắt xích cuối của một chuỗi chung. [B-67] [B-52]

> **Cách dùng phù hợp:** So sánh ba lớp để biết thị trường đang đồng thuận hay bất đồng.
>
> **Cách dùng không phù hợp:** Biến một trạng thái thành xác suất tăng giảm hoặc lệnh giao dịch.

## Ba đại lượng thực sự nói gì?

### Giá: kết quả đang hiển thị trên thị trường

Giá là đại lượng trực tiếp nhất. Chỉ số tăng cho biết giá trị tổng hợp của nhóm cổ phiếu đã tăng trong khoảng quan sát. Nó không nói đợt tăng có bao nhiêu cổ phiếu tham gia, bao nhiêu tiền được giao dịch hay xu hướng sẽ kéo dài bao lâu.

### Khối lượng: mức hoạt động giao dịch

Khối lượng cho biết số lượng cổ phiếu được trao tay. Khối lượng cao có thể đi cùng mua chủ động, bán chủ động, tái cân bằng hoặc một sự kiện riêng. Bản thân nó không chứa nhãn “tốt” hoặc “xấu”. Muốn hiểu khối lượng, nhà đầu tư phải đặt nó cạnh giá, lịch sử giao dịch và thông tin doanh nghiệp.

### Độ rộng: số cổ phiếu cùng tham gia

Độ rộng trả lời một câu hỏi khác: chuyển động của chỉ số có lan ra nhiều mã hay không. Chỉ số có thể tăng nhờ vài cổ phiếu vốn hóa lớn trong khi phần lớn thị trường đứng yên hoặc giảm. Ngược lại, chỉ số tăng vừa phải nhưng nhiều mã cùng cải thiện có thể cho thấy mức tham gia rộng hơn. Nghiên cứu hiện tại không chứng minh trạng thái nào bền hơn; độ rộng chỉ giúp mô tả cấu trúc bên dưới chỉ số.

## Nghiên cứu quan sát được gì?

Ở dữ liệu ngày, giá từng cho thấy quan hệ đi trước khối lượng trong mẫu. Nói đơn giản, một phần thay đổi khối lượng xuất hiện sau khi giá đã chuyển động. Đây là một phát hiện về thứ tự trong dữ liệu lịch sử, không phải bằng chứng rằng giá gây ra khối lượng hoặc có thể dự báo khối lượng một cách vận hành. [B-67]

Chiều mà nhiều nhà đầu tư kỹ thuật thường kỳ vọng lại không được xác nhận: nghiên cứu không tìm thấy bằng chứng ổn định rằng khối lượng đi trước giá. Điều đó không có nghĩa khối lượng vô dụng. Nó có nghĩa vai trò “tín hiệu báo trước” chưa được dữ liệu hiện hành hỗ trợ.

Khi đem các quan hệ sang phần dữ liệu chưa dùng để xây mô hình, không kết quả nào đạt tiêu chuẩn vận hành đã khóa. Vì thế, nghiên cứu không tạo ra một trình tự “giá rồi độ rộng rồi khối lượng”, cũng không tạo ra quy tắc “khối lượng xác nhận xu hướng”. [B-52]

## Vì sao ba lớp thường bị hiểu nhầm?

Giá là kết quả dễ nhìn nhất nên người dùng thường dùng khối lượng và độ rộng để kể thêm một câu chuyện về nguyên nhân hoặc độ bền. Vấn đề là cùng một trạng thái có thể được giải thích theo nhiều cách đối lập.

Giá tăng với khối lượng thấp có thể bị gọi là “thiếu cầu”, nhưng cũng có thể phản ánh nguồn cung ít. Giá giảm với khối lượng cao có thể bị gọi là “phân phối”, nhưng cũng có thể được kể là “hấp thụ nguồn cung”. Chỉ số tăng với độ rộng hẹp có thể là dấu hiệu tập trung, nhưng tập trung không cho biết khi nào nhóm dẫn dắt dừng tăng.

Khi một hình ảnh có thể hỗ trợ hai câu chuyện trái chiều, hình ảnh đó chưa đủ để quyết định. Nghiên cứu giúp chuyển trọng tâm từ tên gọi sang câu hỏi có thể kiểm tra: trạng thái xuất hiện trước kết quả nào, có lặp trên dữ liệu mới không và có tốt hơn chuẩn chỉ dùng giá không.

### Khối lượng không cho biết trực tiếp bên nào “thắng”

Mỗi giao dịch đều có người mua và người bán. Khối lượng cao nói rằng nhiều cổ phiếu được trao tay, không tự nói áp lực mua hay bán là nguyên nhân. Muốn hiểu hướng chủ động cần dữ liệu và định nghĩa khác, trong khi nghiên cứu hiện dùng khối lượng theo hợp đồng đã khóa.

Khối lượng cũng khác thanh khoản. Một mã có nhiều giao dịch nhưng chênh lệch mua bán rộng hoặc khả năng thực hiện lệnh lớn kém vẫn có thể khó giao dịch. Báo cáo không biến số lượng cổ phiếu trao tay thành kết luận về chi phí thực hiện.

### Độ rộng phụ thuộc vũ trụ được chọn

Tỷ lệ mã tăng giảm chỉ có nghĩa khi người đọc biết những mã nào được tính. Danh sách cổ phiếu đang hoạt động hiện nay có thể bỏ qua các mã đã rời sàn trong quá khứ. Một vũ trụ chỉ gồm mã thanh khoản cao có thể cho bức tranh khác toàn thị trường. Vì vậy mọi màn hình độ rộng cần hiển thị phạm vi và giới hạn dữ liệu.

Độ rộng cũng không phải trọng số vốn hóa. Một cổ phiếu nhỏ và một cổ phiếu lớn có thể đóng góp như nhau vào số mã tăng, trong khi ảnh hưởng đến VNINDEX rất khác. Chính sự khác biệt này làm độ rộng hữu ích để bổ sung cho chỉ số, nhưng cũng ngăn hai đại lượng thay thế nhau.

## Nghiên cứu đã tách ba loại câu hỏi như thế nào?

### Liên hệ cùng thời điểm

Câu hỏi đầu tiên là các lớp dữ liệu thay đổi cùng nhau ra sao trong cùng khoảng. Đây là phần mô tả trạng thái. Nó không đưa ra thứ tự và không cần được kể thành cơ chế.

### Thứ tự trong dữ liệu lịch sử

Câu hỏi tiếp theo là quá khứ của một biến có thêm thông tin cho biến kia hay không. Nghiên cứu xem từng chiều riêng. Điều này ngăn việc thấy giá đi trước khối lượng rồi tự động đảo câu thành khối lượng đi trước giá.

Kết quả đáng chú ý nhất nằm ở chiều giá sang khối lượng trong dữ liệu ngày. [B-67] Nó cho thấy giả thuyết “khối lượng luôn đi trước” không nên được coi là mặc định. Nhưng vì đây là kết quả trong mẫu, nó chỉ là nền tảng để đặt câu hỏi tiếp theo.

### Kiểm tra trên dữ liệu mới

Các mối quan hệ được đưa sang quy trình đánh giá theo thời gian. Không hướng nào đạt trạng thái ổn định đủ để vận hành. [B-52] Đây là bước quyết định quyền hạn: một quan hệ lịch sử có thể được kể trong phần khám phá nhưng không được biến thành công cụ.

### Vì sao không thể nối ba cặp thành một chuỗi?

Các cặp giá–khối lượng, giá–độ rộng và độ rộng–khối lượng không cùng nhau chứng minh một chuỗi chung. Muốn nói “giá thay đổi, độ rộng phản ứng rồi khối lượng theo sau”, cần một kiểm định đa biến được khóa riêng cho chính chuỗi đó. Ghép kết quả của các cặp là tạo claim mới.

Sơ đồ ba lớp trong báo cáo vì thế là công cụ giải thích. Các ô nằm cạnh nhau để người dùng nhớ xem cả ba, không phải sơ đồ dòng chảy đã đo được.

## Bốn tình huống minh họa

Các tình huống là ví dụ giả định, không phải tần suất thực nghiệm.

### Giá và độ rộng cùng tăng, khối lượng không đổi

Cách mô tả phù hợp là đợt tăng có mức tham gia rộng hơn nhưng hoạt động giao dịch chưa thay đổi rõ. Không nên gọi khối lượng “không xác nhận”. Người dùng kiểm tra xem thanh khoản thấp có phải đặc điểm chung của giai đoạn, liệu nhóm tăng có nền tảng lợi nhuận và danh mục có hưởng lợi hay không.

Nếu nhiều mã tăng nhẹ nhưng chỉ số được kéo bởi vài mã lớn, độ rộng và chỉ số vẫn có thể cùng tích cực theo những mức khác nhau. Hình không cho biết đợt tăng sẽ kéo dài.

### Giá tăng, độ rộng thu hẹp, khối lượng tăng

Đây là trạng thái tập trung với hoạt động cao hơn. Có thể giao dịch đang dồn vào nhóm dẫn dắt, cũng có thể một sự kiện ở vài mã lớn chi phối cả chỉ số và khối lượng.

Danh sách kiểm tra gồm đóng góp của từng mã, số ngành tham gia, giao dịch thỏa thuận, tái cân bằng và tin tức. Không được cộng “giá tăng” và “khối lượng tăng” thành điểm mua rồi coi “độ rộng hẹp” là một điểm trừ tùy ý. Chưa có trọng số nghiên cứu cho phép làm vậy.

### Giá giảm, độ rộng giảm, khối lượng cao

Ba lớp cùng mô tả một phiên suy yếu rộng và hoạt động cao. Điều đó làm câu mô tả hiện tại rõ hơn, nhưng vẫn không tạo xác suất phiên sau giảm. Nhà đầu tư có thể kiểm tra giới hạn rủi ro, thông tin mới và độ nhạy danh mục. Nếu quyết định giảm vị thế, lý do phải là rủi ro hoặc luận điểm bị phá vỡ, không phải vì ba “phiếu” độc lập cùng xuất hiện.

### Chỉ số đi ngang nhưng độ rộng cải thiện

Mức tham gia có thể đang dịch chuyển sang nhiều cổ phiếu trong khi nhóm vốn hóa lớn chưa tăng. Đây là thông tin hữu ích cho người nắm danh mục cân bằng hơn chỉ số. Nó chưa phải bằng chứng một nhịp tăng của VNINDEX sắp đến.

Người dùng có thể mở rộng danh sách theo dõi và kiểm tra ngành đang cải thiện. Muốn gọi đây là chỉ báo đi trước cần một nghiên cứu xác nhận riêng.

## Cách đọc ba biểu đồ mà không bị biểu đồ dẫn dắt

Biểu đồ giá cần ghi rõ lợi nhuận theo ngày, tuần hay tháng. Một đường tăng dài không nói độ rộng hoặc khối lượng nếu hai lớp kia không được hiển thị.

Biểu đồ khối lượng nên so với lịch sử của chính tài sản và giữ các phiên không giao dịch hoặc khối lượng bằng không như dữ liệu cần giải thích. Không nên thay số không bằng một giá trị rất nhỏ chỉ để công thức chạy, vì việc đó có thể tạo xu hướng giả.

Biểu đồ độ rộng phải nêu vũ trụ và số mã có dữ liệu. Nếu số lượng mã thay đổi mạnh qua thời gian, tỷ lệ cần đi kèm coverage. Không được vẽ đường độ rộng như thể nó có cùng đơn vị với VNINDEX trên một trục kép rồi suy ra hai đường “hội tụ” hay “phân kỳ”.

Sơ đồ đồng thuận trong master không chứa tần suất. Nó chỉ dạy cách đặt câu. Nếu người đọc muốn biết một trạng thái xảy ra bao nhiêu lần và kết quả sau đó thế nào, phải mở artifact của nghiên cứu tương ứng thay vì đoán từ kích thước ô hoặc màu.

## Đưa ba lớp vào dashboard

Một dashboard phù hợp nên có ba hàng độc lập. Hàng giá ghi hướng và khoảng thời gian. Hàng hoạt động ghi khối lượng so với lịch sử gần cùng cảnh báo sự kiện. Hàng độ rộng ghi số mã tăng giảm, coverage và ngành tham gia.

Phần diễn giải có thể tạo câu như “VNINDEX tăng trong khi mức tham gia hẹp; hoạt động giao dịch không thay đổi rõ”. Câu này tốt hơn nhãn “tích cực” vì nó giữ được bất đồng. Bên dưới là danh sách kiểm tra, không phải nút hành động.

Người dùng cần có khả năng mở định nghĩa từng trạng thái. Nếu thuật toán đổi khoảng nhìn lại hoặc vũ trụ, phiên bản phải được lưu. Nhật ký cũ không được tính lại bằng định nghĩa mới mà không ghi dấu, nếu không việc đánh giá quy trình về sau sẽ sai.

## Đồng thuận và bất đồng nên được hiểu thế nào?

“Đồng thuận” là cách gọi mô tả khi nhiều lớp dữ liệu cùng cho thấy một trạng thái tương thích. Ví dụ minh họa: chỉ số tăng, nhiều cổ phiếu cùng tăng và hoạt động giao dịch không co lại rõ rệt. “Bất đồng” là khi một lớp đi khác hai lớp còn lại, như chỉ số tăng nhưng số mã tham gia thu hẹp.

Các nhãn này không phải kết quả dự báo. Chúng giúp người đọc biết câu chuyện thị trường đang đơn giản hay cần kiểm tra thêm. Một bức tranh đồng thuận vẫn có thể đảo chiều. Một bức tranh bất đồng vẫn có thể kéo dài lâu. Nghiên cứu không gán xác suất cho hai trường hợp.

Điểm hữu ích là bất đồng buộc nhà đầu tư hạ độ chắc chắn. Nếu chỉ số tăng nhờ vài cổ phiếu lớn, luận điểm “toàn thị trường khỏe” cần được sửa. Nếu giá giảm nhưng khối lượng tăng, câu hỏi đúng là giao dịch đang tập trung ở đâu và có sự kiện nào xảy ra, không phải “đáy đã xuất hiện chưa”.

## Hai tình huống thường gặp

### Tình huống 1: Giá tăng nhưng khối lượng không tăng theo

Cách hiểu phổ biến là “đợt tăng thiếu xác nhận”. Nghiên cứu không xác nhận quy tắc đó. Khối lượng thấp có thể đến từ nguồn cung ít, mùa giao dịch trầm lắng hoặc đặc điểm riêng của mã. Bước hợp lý là kiểm tra mức thanh khoản so với lịch sử, độ rộng của thị trường và thông tin thúc đẩy giá.

Câu hỏi nên ghi vào nhật ký:

- Giá tăng ở toàn thị trường hay tập trung?
- Khối lượng thấp ở chính mã đang theo dõi hay ở cả thị trường?
- Có sự kiện doanh nghiệp, cơ cấu chỉ số hoặc thay đổi free-float không?
- Luận điểm đầu tư dựa trên yếu tố cơ bản nào ngoài chuyển động giá?

### Tình huống 2: Chỉ số tăng nhưng độ rộng hẹp

Đây là dấu hiệu chỉ số và phần còn lại của thị trường không kể cùng một câu chuyện. Nó không tự động là tín hiệu bán. Một số đợt tăng tập trung có thể tiếp tục nếu nhóm dẫn dắt còn động lực. Nhà đầu tư nên kiểm tra tỷ trọng nhóm dẫn dắt, số ngành tham gia, mức thanh khoản và diễn biến của danh mục mình đang nắm.

Nếu danh mục gồm nhiều cổ phiếu ngoài nhóm dẫn dắt, chỉ số tăng có thể không phản ánh trải nghiệm thực tế. Lúc này độ rộng giúp sửa cách mô tả danh mục, chứ chưa đưa ra thời điểm mua bán.

## Cách đưa ba lớp dữ liệu vào quy trình đầu tư

### Bước 1: Mô tả từng lớp riêng

Viết một câu về giá, một câu về khối lượng và một câu về độ rộng. Không nối chúng thành nguyên nhân trước khi có bằng chứng.

### Bước 2: Ghi điểm đồng thuận hoặc bất đồng

Chỉ ghi trạng thái. Ví dụ: “chỉ số tăng nhưng mức tham gia hẹp”. Tránh các từ như “sắp đảo chiều”, “xác nhận” hoặc “phân phối” nếu chưa có dữ liệu độc lập.

### Bước 3: Đối chiếu với danh mục

Kiểm tra cổ phiếu đang nắm có thuộc nhóm dẫn dắt không, thanh khoản có đủ cho quy mô vị thế không và biến động có đến từ sự kiện riêng không.

### Bước 4: Tìm bằng chứng ngoài ba biến

Kết quả kinh doanh, định giá, thông tin doanh nghiệp, dòng tiền ngành và điều kiện vĩ mô mới là các nguồn giúp kiểm tra luận điểm. Ba lớp dữ liệu nội tại chỉ cho biết nơi cần nhìn kỹ hơn.

### Bước 5: Đặt điều kiện vô hiệu hóa

Nếu luận điểm là “đợt tăng đang lan rộng”, hãy xác định điều gì làm luận điểm sai: số ngành tham gia giảm, danh mục không hưởng lợi hoặc nhóm dẫn dắt suy yếu. Điều kiện này hữu ích hơn một điểm số tổng hợp chưa được kiểm định.

## Những điều nghiên cứu chưa chứng minh

Nghiên cứu chưa xác lập chuỗi chung giữa giá, độ rộng và khối lượng. Nó chưa chứng minh khối lượng xác nhận xu hướng, chưa tạo xác suất đảo chiều và chưa xác nhận một mô hình có thể dùng như công cụ giao dịch. [B-52]

Quan hệ giá đi trước khối lượng chỉ là kết quả trong mẫu ở đúng phạm vi dữ liệu ngày. Nó không được mở rộng thành quan hệ nhân quả, không đại diện cho mọi cổ phiếu và không bảo đảm lặp lại ở giai đoạn mới. [B-67]

Độ rộng trong chương này được dùng để giải thích cách quan sát mức tham gia. Không kết luận hiện hành nào trong ma trận cho phép nói độ rộng đi trước khối lượng hoặc dự báo VNINDEX. Những kết luận rộng hơn phải dựa vào nguồn riêng, không được suy ra từ B-67.

## Một mẫu nhật ký ba lớp

Thay vì chấm điểm, nhà đầu tư có thể ghi ba hàng cố định sau mỗi phiên hoặc mỗi tuần:

- **Giá:** VNINDEX và danh mục đang tăng, giảm hay đi ngang trong khoảng đã chọn?
- **Hoạt động:** giá trị và khối lượng giao dịch cao hay thấp so với lịch sử của chính giai đoạn tương tự?
- **Mức tham gia:** bao nhiêu mã và bao nhiêu ngành cùng đi theo hướng chỉ số?

Sau ba hàng là hai câu bắt buộc: “Điểm nào đang đồng thuận?” và “Điểm nào đang bất đồng?”. Câu cuối cùng là “Dữ liệu độc lập nào cần kiểm tra trước khi đổi luận điểm?”.

Ví dụ giả định, nếu chỉ số tăng, độ rộng hẹp và khối lượng cao, nhật ký không kết luận tích cực hay tiêu cực. Nó ghi: “Đợt tăng tập trung với hoạt động cao; cần xem đóng góp nhóm dẫn dắt, thông tin doanh nghiệp và mức ảnh hưởng đến danh mục.” Câu này giữ được thông tin mà không giả vờ biết bước tiếp theo.

## Khi nào một trạng thái chỉ là nhiễu dữ liệu?

Khối lượng có thể tăng do tái cân bằng chỉ số, giao dịch thỏa thuận hoặc sự kiện doanh nghiệp. Độ rộng có thể thay đổi vì số mã có dữ liệu thay đổi. Chỉ số có thể nhảy do một cổ phiếu vốn hóa lớn. Vì vậy, trước khi diễn giải đồng thuận hay bất đồng, cần kiểm tra chất lượng dữ liệu và thành phần đóng góp.

Một dashboard tốt nên hiện coverage của độ rộng, tách giao dịch bất thường nếu có thể và cho phép mở danh sách cổ phiếu kéo chỉ số. Khi dữ liệu thiếu, trạng thái phải chuyển sang “chưa đủ thông tin” thay vì tự điền hoặc tiếp tục tính.

## Điều gì có thể nâng ba lớp thành công cụ mạnh hơn?

Muốn biến một trạng thái thành cảnh báo, nghiên cứu mới phải định nghĩa trước trạng thái, khoảng quan sát và kết quả tương lai. Nó phải so sánh với chuẩn hợp lý, đánh giá trên dữ liệu mới và kiểm tra mức lặp lại qua nhiều giai đoạn.

Muốn tạo điểm tổng hợp, cần khóa trước cách gán trọng số và chứng minh điểm đó tốt hơn từng lớp riêng. Không được chọn trọng số sau khi nhìn các giai đoạn đẹp. Nếu dùng độ rộng, vũ trụ cổ phiếu phải đúng tại từng thời điểm lịch sử để tránh giới hạn sống sót.

Muốn dùng cho giao dịch, còn cần chi phí, thanh khoản và nguyên tắc quản trị vị thế. Nghiên cứu hiện tại mới hỗ trợ lớp quan sát. Đây không phải thất bại: một bảng trạng thái trung thực thường hữu ích hơn một điểm số có vẻ chính xác nhưng chưa được kiểm chứng.

## Quy tắc biên tập cho mọi sản phẩm dùng ba biến

Mỗi câu phải tách điều quan sát khỏi điều suy luận. “Chỉ số tăng, 60% mã giảm” là quan sát nếu dữ liệu hỗ trợ. “Đợt tăng sắp kết thúc” là dự báo cần nghiên cứu riêng. “Dòng tiền thông minh đang thoát” là cơ chế chưa được xác nhận.

Màu sắc cũng phải giữ ranh giới đó. Xanh và đỏ dễ bị đọc như lệnh giao dịch; trạng thái mô tả nên dùng bảng màu trung tính và nhãn bằng câu. Tooltip cần nói rõ khoảng thời gian, vũ trụ và đơn vị. Không để người dùng phải biết tên biến thô mới hiểu biểu đồ.

Cuối cùng, mọi màn hình phải có đường dẫn tới định nghĩa và giới hạn. Nếu người dùng chỉ nhìn được một con số tổng hợp, hệ thống đang che mất chính phần quan trọng nhất của nghiên cứu.

## Kết luận

Một bài kiểm tra nhanh gồm năm câu: Tôi đã tách giá, khối lượng và độ rộng thành ba câu riêng chưa? Độ rộng dùng vũ trụ nào? Khối lượng có bị sự kiện đặc biệt chi phối không? Bất đồng hiện tại làm thay đổi mô tả hay đã bị biến thành dự báo? Có nguồn độc lập nào hỗ trợ luận điểm không?

Nếu câu trả lời dừng ở “ba biến cùng màu”, phân tích chưa đủ. Đồng thuận về dấu không phải ba phiếu độc lập và bất đồng không phải lời tiên tri. Giá trị của khung ba lớp nằm ở chất lượng câu hỏi nó mở ra.

Người dùng cũng cần tránh so sánh các khoảng không đồng nhất. Giá theo tuần, khối lượng theo ngày và độ rộng theo tháng không thể được đặt cạnh nhau rồi gọi là đồng thuận. Mỗi màn hình phải dùng khoảng thời gian rõ và mọi thay đổi khoảng đo phải được ghi nhận.

Khi ba lớp không đồng thuận, không cần chọn ngay lớp nào “đúng”. Chúng đang đo những khía cạnh khác nhau. Nhiệm vụ của nhà phân tích là xác định câu chuyện nào phù hợp với danh mục và bằng chứng nào có thể bác bỏ nó.

Giá, khối lượng và độ rộng là ba màn hình khác nhau. Chúng có thể giúp nhà đầu tư mô tả thị trường chính xác hơn và phát hiện khi câu chuyện của chỉ số không đại diện cho toàn bộ cổ phiếu. Nghiên cứu chưa xác nhận một chuỗi dự báo hoặc tín hiệu vận hành từ ba đại lượng này.

Cách dùng tốt nhất là **đọc mức tham gia, nhận diện bất đồng và mở kiểm tra tiếp theo**. Không dùng một trạng thái đơn lẻ để thay thế luận điểm đầu tư.

## Phụ lục kỹ thuật

Claim [B-67] chỉ hỗ trợ quan hệ `price→volume` ở dữ liệu ngày trong mẫu. Nó không hỗ trợ một claim riêng về `breadth→volume`.

Claim [B-52] cho biết không hướng nào trong nghiên cứu hiện hành đạt mức có thể vận hành. Kết quả này không có nghĩa ba biến vô dụng cho mô tả.

Nguồn, khóa truy xuất, SHA256 và giới hạn diễn giải nằm trong `14_claim_usage_matrix.json`.
