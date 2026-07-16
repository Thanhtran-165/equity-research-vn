# Baseline Run — IGWT 2026 Compact (pp.11-14, "Back to the Monetary Future")

Training case cho `vietnamese-document-translation-skill`. Section đại diện: trang 11-14 (Introduction: Back to the Monetary Future — Trust + Geopolitical Showdown + Transmission Sequence).

Source words: ~1.150 (prose,不包括 chart legends).

---

## 1. Intake result

- Document type: Báo cáo nghiên cứu tài chính/vàng (annual flagship)
- Source language: English
- Target language: Tiếng Việt
- Domain: macro + finance (vàng, tiền tệ, địa chính trị)
- Audience: specialist (analyst, investor) + retail (báo cáo phổ thông có tính giáo dục)
- Style mode: `financial_research_vi` (suy luận: báo cáo có số liệu + citation + lập luận tài chính → tone người kể chuyện số liệu; nhưng có văn phong journalistic với idiom → cần linh hoạt gloss)
- Layout sensitivity: HIGH (2-cột, pull-quote sidebar, chart, transmission-sequence infographic, 6-box grid)
- Risk level: HIGH (số liệu tài chính + citation tri thức + lập luận chính sách tiền tệ)

---

## 2. Extracted glossary (dynamic, 5 cột)

| source_term | vietnamese_term | type | confidence | note |
|---|---|---|---|---|
| In Gold We Trust | In Gold We Trust | do_not_translate | high | tên báo cáo — giữ nguyên |
| Back to the Monetary Future | Back to the Monetary Future | do_not_translate | high | tên theme — giữ + gloss lần đầu |
| Back to the Future | Back to the Future | do_not_translate | high | tên phim |
| Marty McFly | Marty McFly | do_not_translate | high | tên nhân vật phim |
| Tony Deden | Tony Deden | do_not_translate | high | tên người |
| Ludwig von Mises | Ludwig von Mises | do_not_translate | high | tên người |
| Hemingway | Hemingway | do_not_translate | high | tên người |
| Groucho Marx | Groucho Marx | do_not_translate | high | tên người |
| George Bernard Shaw | George Bernard Shaw | do_not_translate | high | tên người |
| John Tuld | John Tuld | do_not_translate | high | tên nhân vật phim Margin Call |
| Luke Gromen | Luke Gromen | do_not_translate | high | tên người |
| Donald Trump | Donald Trump | do_not_translate | high | tên người |
| Zohran Mamdani | Zohran Mamdani | do_not_translate | high | tên người |
| Iran | Iran | do_not_translate | high | tên quốc gia |
| Strait of Hormuz | Eo biển Hormuz | preferred_term | high | địa lý |
| Gulf region | vùng Vịnh | preferred_term | high | địa lý |
| QE / QQE / YCC / MMT | QE / QQE / YCC / MMT | do_not_translate | high | thuật ngữ — gloss lần đầu |
| margin call | lệnh ký quỹ (margin call) | locked_term | high | from termbase |
| safe haven | trú ẩn an toàn | locked_term | high | from termbase |
| store of value | kho lưu giá trị | locked_term | high | from termbase |
| velocity of money | tốc độ lưu thông tiền | locked_term | high | from termbase |
| financial repression | trấn áp tài chính | locked_term | high | from termbase |
| helicopter money | tiền trực thăng | locked_term | high | from termbase |
| gold standard | bản vị vàng | locked_term | high | from termbase |
| gold rally | nhịp tăng của vàng | preferred_term | medium | compound |
| bull market | thị trường bò | locked_term | high | from termbase |
| drawdown | sụt giảm từ đỉnh | locked_term | high | from termbase |
| safe-haven | trú ẩn an toàn | locked_term | high | from termbase |
| risk premium | phần bù rủi ro | preferred_term | high | |
| deleveraging | giảm đòn bẩy | preferred_term | high | |
| tangible assets | tài sản hữu hình | preferred_term | high | |
| transmission sequence | chuỗi truyền dẫn | preferred_term | medium | 2 cách: chuỗi truyền dẫn / trình tự truyền tác động |
| monetary system | hệ thống tiền tệ | preferred_term | high | |
| cinematic nod | cái gật đầu điện ảnh | preferred_term | medium | idiom — gloss |
| invisible lever | đòn bẩy vô hình | preferred_term | high | ẩn dụ Tony Deden |
| homeopathic doses | từng liều nhỏ (kiểu homeopathic) | preferred_term | high | idiom — KHÔNG "thuốc đồng cân" |
| Gradually, then suddenly | Dần dần, rồi đột ngột | do_not_translate | high | câu Hemingway — giữ + gloss |
| passed with flying colors | vượt qua xuất sắc | preferred_term | high | idiom |
| squandered | lãng phí / vứt bỏ | ambiguous_term | medium | 2 cách: lãng phí / đánh mất |
| Gilded Age | Thời đại Mạ Vàng (Gilded Age) | preferred_term | high | idiom lịch sử Mỹ — gloss |
| fire sale | bán tháo | preferred_term | high | tài chính |
| side quote / pull quote | trích dẫn nổi | preferred_term | medium | layout term |

---

## 3. Baseline Vietnamese translation

> Chạy theo `chunk_translator.md` + `editorial_rewriter_vi.md` mode `financial_research_vi`. Layout 2-cột: prose chính + pull-quote sidebar (italic „..."). Pull-quote giữ riêng, không trộn vào prose.

### Section 1 — Back to the Future of Trust: Trust as a Monetary Foundation

**Tóm tắt intro**

Chủ đề của kỳ ấn bản kỷ niệm 20 năm, "Back to the Monetary Future" (Trở lại Tương lai Tiền tệ), không chỉ là một *cinematic nod* (cái gật đầu điện ảnh) tới một bộ phim cuồng tông từ thời thơ ấu của chúng tôi: đó là một luận điểm. Cũng như Marty McFly trong *Back to the Future* phải nhận ra rằng muốn sửa chữa hiện tại thì phải hiểu quá khứ, lịch sử tiền tệ dạy ta rằng tương lai của tiền nằm ở quá khứ của chính nó.

**Trust as a Monetary Foundation (Niềm tin là nền tảng tiền tệ)**

Nằm ở trung tâm của quá trình chúng tôi theo dõi từ 2007 là tầm quan trọng cốt yếu của niềm tin. Đó là chất keo vô hình gắn kết các xã hội, cho phép hợp tác, và làm cho tương lai có vẻ đoán định được. Tony Deden, một trong những nhà tư tưởng sắc sảo nhất thời đại chúng ta, gọi đó là "đòn bẩy vô hình" – một dạng vốn quý hơn bất kỳ khoản mục nào trên bảng cân đối kế toán. Không có niềm tin, sẽ không có các mối quan hệ, không có tín dụng, không có nền kinh tế, không có tiền.

> *„Niềm tin không phải là một tài sản mềm. Nó là hệ điều hành cốt lõi của nền văn minh – kiến trúc thầm lặng làm cho thị trường vận hành, cộng đồng tồn tại, và lời hứa được giữ."*
> — Tony Deden

Do đó không phải ngẫu nhiên mà chúng tôi đã tường minh đưa từ "niềm tin" (trust) vào tựa đề báo cáo *In Gold We Trust* 2019, "Vàng trong Kỷ nguyên Niềm tin Bị bào mòn" (Gold in the Age of Eroding Trust). Điều đó chỉ phản ánh điều đã được in trên tiêu đề ngay từ báo cáo đầu tiên năm 2007: In Gold We Trust. Sự bào mòn niềm tin kể từ đó không hề chậm lại, mà trái lại còn tăng tốc.

Niềm tin có thể được xây dựng trong hàng thập kỷ – chỉ để rồi bị lãng phí trong vài giây. Tính bất đối xứng này mới là rủi ro thực sự. Niềm tin bào mòn một cách thầm lặng, *từng liều nhỏ (kiểu homeopathic)*, cho đến khi chạm một điểm tới hạn và đột ngột mất đi. "Gradually, then suddenly" (Dần dần, rồi đột ngột) – Hemingway khó có thể diễn tả động lực này chính xác hơn.

Sự phân cực chính trị tại Mỹ cho thấy sự đồng thuận xã hội đang bị bào mòn nhiều đến mức nào. Chiến thắng bầu cử của Donald Trump được theo sau, chỉ một năm sau, bởi một chiến thắng thị trưởng New York cũng quyết liệt tương đương của Zohran Mamdani, ứng viên từ cánh tả của Đảng Dân chủ. *Affordability* (khả năng chi trả) là vấn đề định hình trong cả hai trường hợp, nhưng các giải pháp chính trị mà những người chiến thắng tương ứng đề xuất lại khác xa nhau. Cuộc tranh giành phân phối không còn là một lý thuyết trừu tượng; nó là một vấn đề trung tâm trong chính trị đương đại. Những điểm tương đồng lịch sử với *Gilded Age* (Thời đại Mạ Vàng) cuối thế kỷ 19 rất đáng chú ý: những đỉnh cao bất bình đẳng như vậy thường đi trước các biến động chính trị lớn hoặc các đợt điều chỉnh thị trường sâu.

> *„Chính trị là nghệ thuật tìm kiếm rắc rối, phát hiện nó ở khắp nơi, chẩn đoán sai và áp dụng biện pháp sai."*
> — Groucho Marx

Nhưng niềm tin không chỉ là đồng tiền của chính trị mà còn là nền tảng của mọi hệ thống tiền tệ. Sự mất niềm tin hiện tại không chỉ là một quan sát xã hội. Như Ludwig von Mises đã nhận ra, niềm tin là hạ tầng vô hình của mọi hệ thống tiền tệ. Nếu người dân không còn coi lời hứa của nhà nước – kể cả sự ổn định của giá trị đồng tiền – là đáng tin cậy, thì *velocity of money* (tốc độ lưu thông tiền) tăng lên: người dân giữ tiền giấy trong thời gian ngắn hơn, chạy sang tài sản hữu hình, và đòi hỏi *risk premium* (phần bù rủi ro) cao hơn. Niềm tin, theo góc nhìn của chúng tôi, đang được định giá lại – và thị trường đang đưa ra phán quyết tính bằng ounce.

### Section 2 — The Geopolitical Showdown and Gold's Margin Call

Sau nhịp tăng giá vốn hành trình ngoạn mục của vàng trong các quý trước, một giai đoạn tích lũy không chỉ là khả dĩ mà, dưới góc kỹ thuật, là đã quá hạn. Động lực đến từ chính sự kiện mà, *by the textbook* (theo sách giáo khoa), lẽ ra phải có tác dụng ngược: khủng hoảng Iran.

Trong khi phần lớn người tham gia thị trường đầu cơ thêm một nhịp tăng giá, thị trường lại chuyển theo chiều ngược lại – cuộc chiến không trở thành chất xúc tác mà đúng hơn là *trigger* (chốt khởi động) cho một đợt điều chỉnh lành mạnh. Không có xu hướng tăng nào tuyến tính; ngay cả thị trường bò mang tính cấu trúc cũng cần các giai đoạn điều chỉnh, điều chỉnh vị thế, và tháo gỡ tâm lý. Kể từ khi báo cáo *In Gold We Trust* năm ngoái "The Big Long" phát hành, vàng đã giao dịch cao hơn gần 40% bất chấp đợt điều chỉnh này.

> *„Nếu anh là người đầu tiên chạy ra cửa, thì đó không gọi là hoảng loạn."*
> — John Tuld, *Margin Call* (phim)

Tháng 3/2026, giá vàng giảm 611 USD trong một tháng – mức giảm tuyệt đối hàng tháng lớn nhất từ trước đến nay. Tới cuối đợt điều chỉnh, vàng đã giảm 27% từ đỉnh mọi thời đại (ATH) tháng 1. Đúng như dự đoán, giới chính thống tuyên bố tài sản trú ẩn đã thất bại. Nhưng những ai hiểu cơ chế lại nhận ra một pattern quen thuộc: trong các giai đoạn căng thẳng tài chính cấp tính, vàng bị bán không phải mặc dù, mà chính vì tính thanh khoản cao của nó. Chúng tôi đã thấy đúng pattern tương tự vào tháng 10/2008, với mức giảm 29%, khi vụ phá sản Lehman kích hoạt *margin call* (lệnh ký quỹ) trên mọi hạng tài sản, và vào tháng 3/2020, khi một đợt thanh khoản quét qua thị trường trong giai đoạn đầu đại dịch Covid-19 và vàng giảm 12%.

Sự đồng thời của hai cơ chế làm cho đợt sụt giảm vừa qua trở nên độc nhất: thứ nhất, việc đóng cửa Eo biển Hormuz cắt đứt dòng tiền mặt tới các nhà sản xuất dầu tại vùng Vịnh – những bên trong nhiều năm đã tái chu kỳ thặng dư USD vào vàng. Thứ hai, việc leo thang buộc một đợt giảm đòn bẩy vì lợi suất tăng, kỳ vọng lãi suất tăng, và đồng USD mạnh hơn kích hoạt lệnh ký quỹ.

> *„Chính phủ Mỹ đang cố ngăn các thị trường tự do định giá chính xác chi phí của cuộc chiến Iran, tất cả trong khi vẫn duy trì ảo giác về thị trường tự do và hy vọng chiến tranh sẽ kết thúc trước khi thực tại tình hình trở nên rõ ràng với nhà đầu tư."*
> — Luke Gromen

Nhưng đây mới chính là mấu chốt: phản ứng của các ngân hàng trung ương (NHTW) với chính chuỗi sự kiện căng thẳng này mới là chất xúc tác thực sự cho vàng. Hai đợt sụt giảm từ đỉnh (drawdown) năm 2008 và 2020 không đánh dấu kết thúc nhịp tăng của vàng, mà đúng hơn là điểm khởi đầu cho nhịp tăng kế tiếp. Một điềm lành cho 2026?

Bởi điều theo sau căng thẳng trong hệ thống tài chính luôn luôn giống nhau: thêm thanh khoản. Các biện pháp trải dài từ *yield curve control* (kiểm soát đường cong lợi suất, YCC) đến tái khởi động QE hoặc QQE, *financial repression* (trấn áp tài chính), và thêm kích thích tài khóa, cho tới các đề xuất cực đoan hơn như MMT hay *helicopter money* (tiền trực thăng). Việc triển khai một hay nhiều công cụ này chỉ là vấn đề thời gian – đi kèm với sự hội tụ thêm giữa chính sách tiền tệ và chính sách tài khóa.

Cú sốc Lehman được theo sau bởi QE1 đến QE3 và giá vàng tăng gấp ba. Đợt sụp đổ Covid-19 được theo sau bởi sự mở rộng tài khóa và tiền tệ chưa từng có và giá vàng tăng hơn 70%. Trình tự truyền tác động – cú sốc năng lượng → cú sốc lạm phát → căng thẳng trái phiếu chính phủ → định giá lại tín dụng → thanh toán cưỡng bức → can thiệp NHTW – là một chu kỳ tự củng cố. Và vàng hưởng lợi ở mọi giai đoạn: như một công cụ phòng ngừa lạm phát, như một trú ẩn an toàn, và rốt cuộc như một kho lưu giá trị trung lập nằm ngoài vòng xoáy mất giá.

> *„Anh phải chọn giữa tin vào sự ổn định tự nhiên của vàng và sự ổn định tự nhiên của tính trung thực và trí thông minh của các thành viên chính phủ. Và, xin hết sức kính trọng các quý ngài đó, tôi khuyên anh, chừng nào hệ thống tư bản còn tồn tại, hãy bỏ phiếu cho vàng."*
> — George Bernard Shaw

Các đợt thoái lui do thanh khoản trong vàng không bác bỏ luận điểm; chúng là cơ hội mua được tạo ra bởi chính luận điểm đó. Tháng 3/2026 là một bài kiểm tra căng thẳng tiền tệ. Và vàng đã vượt qua xuất sắc (*passed with flying colors*).

---

## 4. Baseline MQM review

(Chi tiết error log ở file error_log.md. Tóm tắt ở đây.)

| Nhóm lỗi | Critical | Major | Minor |
|---|---|---|---|
| accuracy | 0 | 2 | 1 |
| terminology | 0 | 1 | 0 |
| fluency | 0 | 0 | 3 |
| style | 0 | 1 | 2 |
| number_unit | 0 | 1 | 0 |
| named_entity | 0 | 0 | 0 |
| formatting | 0 | 0 | 1 |
| omission | 0 | 1 | 0 |
| addition | 0 | 0 | 0 |
| hallucination | 0 | 0 | 0 |
| editorial_overreach | 0 | 0 | 1 |
| parsing_layout | 0 | 1 | 1 |
| **TOTAL** | **0** | **7** | **10** |

## 5. Baseline quality score

- Critical error: 0
- Major error: 7 → 7 × 5 = 35 điểm
- Minor error: 10 → 10 × 1 = 10 điểm
- **Tổng điểm lỗi: 45**
- Source words (prose): ~1.150
- **MQM Weighted Score = 45 / 1,15 = 39,1 / 1.000 words → FAIL (>10)**

KPI check:
- Critical = 0 ✓
- Hallucination = 0 ✓
- Number/unit/named entity error = 1 Major (chưa đạt 0)
- Locked terminology accuracy = 100% (các locked_term đều tuân thủ) ✓
- Protected tokens broken = 0 ✓
- MQM > 5 → CHƯA ĐẠT. Cần patch.

**Verdict**: 0 Critical + 0 hallucination là tín hiệu tốt, nhưng 7 Major (đặc biệt là 1 number_unit + 1 omission + 1 parsing_layout) đẩy score lên 39 — gấp 8 lần ngưỡng 5. Cần root cause + patch.
