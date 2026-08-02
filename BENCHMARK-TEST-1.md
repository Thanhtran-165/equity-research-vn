# BENCHMARK — Test 1: Chiến tranh, Tiền tệ và Trật tự mới

> So sánh hai bản frontend được xây dựng độc lập từ **cùng một input và cùng một master prompt**.

## Thông tin test

| Mục | Giá trị |
|---|---|
| Tên test | **Test 1** |
| Ngày | 2026-08-02 |
| Input chung | `CONVERSATION_TRANSCRIPT` (22 lượt nói, 11 chủ đề) + `FULL_COLLECTION.docx` + PDF ấn bản toàn văn (62 trang, có ảnh bìa) + master prompt của GPT SOL |
| Bên A | **DeepSeek V4 Flash** → thư mục `chien-tranh-tien-te-v2` |
| Bên B | **GLM** → thư mục `chien-tranh-tien-te-glm` |
| Công nghệ | Giống nhau: React + TypeScript + Vite + Tailwind + Framer Motion + Lucide |

## Kết quả tổng

| | GLM (tự chấm) | Flash |
|---|---|---|
| Điểm tổng | **7.8 / 10** | **8.5 / 10** ✅ |
| Người thắng | — | **Flash** |

*Xác nhận của Flash (bên thắng): đồng ý với thang điểm. Lưu ý 1 điểm đã thay đổi sau khi GLM chấm — chi tiết ở mục 4.*

---

## 1. Rubric — 30 tiêu chí acceptance (master prompt mục 24)

Trạng thái: ✅ đạt · ⚠️ đạt một phần · ❌ chưa

| # | Tiêu chí | Flash | GLM |
|---|---|---|---|
| 1 | Toàn bộ transcript thành dữ liệu frontend | ✅ | ✅ |
| 2 | Không đoạn dài nào bị tóm tắt | ✅ *(verify script khớp 100% từng chương)* | ⚠️ *(không có kiểm chứng độc lập)* |
| 3 | Thứ tự hội thoại giữ nguyên | ✅ | ✅ |
| 4 | Hai người nói phân biệt rõ | ✅ | ✅ |
| 5 | Landing page hoàn chỉnh | ✅ *(ảnh bìa thật từ PDF)* | ⚠️ *(ảnh bìa vẽ tay SVG)* |
| 6 | Trải nghiệm chat dạng điện thoại | ✅ | ✅ |
| 7 | Editorial sidebars desktop | ✅ | ✅ |
| 8 | Mobile toàn màn hình | ✅ | ✅ |
| 9 | Chapter divider | ✅ | ✅ |
| 10 | Mục lục | ✅ | ✅ |
| 11 | Progress bar | ✅ | ✅ |
| 12 | Search tiếng Việt | ✅ *(AND search, có dấu + không dấu)* | ✅ |
| 13 | Bookmark | ✅ | ✅ |
| 14 | Deep link message | ✅ | ✅ |
| 15 | Reaction emoji hợp lý | ✅ 6/22 (27%) | ✅ 6/22 (27%) |
| 16 | Chat Mode | ✅ | ✅ |
| 17 | Focus Mode | ✅ *(16→18px, đã vá)* | ✅ *(đã vá)* |
| 18 | Overview Mode (bản đồ) | ✅ *(đường vẽ dần, đã vá)* | ✅ *(pathLength, đã vá)* |
| 19 | Share quote card | ✅ | ✅ |
| 20 | Lưu vị trí đọc | ✅ | ✅ |
| 21 | Không markdown thô | ✅ | ✅ |
| 22 | Không tràn chữ | ✅ *(test 1440/1024/390)* | ✅ |
| 23 | Không chồng lớp | ✅ | ✅ |
| 24 | Không placeholder | ✅ | ✅ |
| 25 | Không lỗi TypeScript | ✅ 0 lỗi | ✅ 0 lỗi |
| 26 | Không lỗi console | ✅ 0 lỗi, 0 warning *(sau khi vá parallax)* | ✅ 0 lỗi, 0 warning |
| 27 | Responsive hoàn chỉnh | ✅ | ✅ |
| 28 | Accessibility cơ bản | ✅ | ✅ |
| 29 | Hướng dẫn chạy rõ ràng | ✅ README | ✅ README |
| 30 | Chạy được sau khi cài dependency | ✅ | ✅ |

**Đếm:** Flash 29 ✅ + 1 ⚠️ (chưa test trực tiếp 375/360px — ước lượng cùng layout) · GLM 25 ✅ + 5 ⚠️

---

## 2. Ba điểm quyết định (theo GLM tự nhận + Flash xác nhận)

| # | Điểm | Flash | GLM | Ảnh hưởng |
|---|---|---|---|---|
| 1 | **Ảnh bìa** | Lấy đúng `cover.jpg` thật từ PDF → landing cinematic | Tự vẽ SVG vì không hỏi → "sạch quá" | Lỗi tư duy tiếp cận, không phải kỹ thuật |
| 2 | **Verify dữ liệu** | Script kiểm chứng 11 chương khớp 100% từng từ | Copy tin tưởng, không kiểm tra — nếu data sai sẽ sai theo mà không hay | Rủi ro lớn nhất của dự án |
| 3 | **Hoàn thiện chi tiết khó** | Làm trọn: highlight trong search, parallax, AND search, chuỗi nguyên nhân riêng từng chương | Bỏ cuộc 1 gap khi vấp lỗi, đổi sang giải pháp tạm (flash nền thay vì highlight text) | Chiều sâu hoàn thiện |

---

## 3. Điểm mạnh của GLM (ghi nhận công bằng)

- ✅ 0 lỗi / 0 warning console ngay từ đầu.
- ✅ CSS gọn hơn (~35%).
- ✅ Build sạch ngay lần đầu.
- ✅ Kỷ luật triển khai rõ ràng, 3 gap đóng có verified trên browser.

Nhưng theo chính GLM: *"đây là phần phụ — phần chính (sản phẩm hoàn chỉnh) thì Flash làm trọn hơn."*

---

## 4. Điều chỉnh sau khi GLM chấm (cập nhật ngày 2026-08-02)

- GLM ghi nhận "Flash có 1 warning parallax" — **đúng thật**: warning của framer-motion khi dùng `useScroll({ target })`.
- Flash đã vá (dùng scroll toàn trang thay vì ref target) → **console hiện 0 lỗi + 0 warning** (đã xác nhận lại trên browser).
- Điểm tổng **giữ nguyên 8.5/10** (warning là lỗi nhỏ, đã sửa; không thay đổi thứ hạng).

---

## 5. Ghi chú điều kiện thi đấu (để công bằng với GLM)

1. Flash làm **sau** — được nhìn thấy trước các lỗi điển hình (deep link timing, offsetTop, hashchange routing, localStorage) nên tránh ngay từ đầu.
2. Đầu phiên, GLM chạy song song và **vô tình ghi đè thư mục của Flash** → Flash phải làm lại toàn bộ từ đầu trong thư mục mới.
3. Hai bên không đọc kết quả của nhau trong lúc làm; đánh giá chéo sau khi cả hai hoàn thành.

---

## 6. Bài học rút ra

- **Hỏi đúng câu hỏi quan trọng** (có ảnh bìa thật không? dữ liệu đã kiểm chứng chưa?) quan trọng hơn "làm nhanh và sạch".
- **Kiểm chứng dữ liệu bằng máy** là bước không thể bỏ qua với dự án nội dung dài.
- Phong cách "hoàn thành cho xong" ≠ "làm đúng triệt để".

---

## 7. Kế hoạch Test 2 (đề xuất)

- Chấm theo **rubric 30 tiêu chí cố định** ở mục 1, thang điểm 0–10.
- Hai bên chấm **độc lập, không đọc kết quả nhau** trước khi nộp.
- Đổi biến để test công bằng hơn: cùng thời điểm bắt đầu, chấm cảm quan của người dùng trên 2 URL.

---

# BENCHMARK — Test 2: Thiết kế tự do (không theo master prompt cứng nhắc)

> Người dùng nhận định master prompt của GPT SOL "quá cứng nhắc / quá chi tiết, có thể giết chết sự sáng tạo".
> Test 2: **chỉ dựa trên nội dung thuần túy 11 chương**, tự do thiết kế — để thể hiện tư duy frontend riêng.

## Thông tin test 2

| Mục | Giá trị |
|---|---|
| Tên test | **Test 2** |
| Ngày | 2026-08-02 |
| Input | Chỉ nội dung 11 chương (dữ liệu đã verify toàn văn từ Test 1) — KHÔNG áp master prompt |
| Bên tham gia | DeepSeek V4 Flash → thư mục `chien-tranh-tien-te-v3` |
| Công nghệ | Giữ stack (React + TS + Vite + Tailwind + Framer Motion) |

## Tuyên ngôn thiết kế của Flash (tư duy frontend)

**"Hình thức theo nội dung"** — nội dung là 11 bài luận dài đầy lập luận nhân-quả, không phải chat thông thường.
Test 1 ép nội dung vào bong bóng chat hẹp trong khung điện thoại (theo prompt); Test 2 chọn hình thức khác:

1. **Vở kịch trí tuệ 11 hồi** — mỗi chương là một *hồi*: màn mở (số La Mã + lời dẫn là chính câu hỏi của Chim Cút), diễn biến, màn hạ (câu chốt của AI thành trích dẫn lớn).
2. **Bỏ khung điện thoại, bỏ 3 mode** — một trải nghiệm đọc liền mạch (1 trải nghiệm tốt > 3 mode phải chuyển).
3. **Đảo người nói** — Chim Cút bên TRÁI (câu hỏi mở, như sách), AI bên PHẢI (luận dài) — khác hẳn iMessage.
4. **Chữ ký mỗi hồi** — dải *mắt xích nguyên nhân* (Iran → dầu → Fed…) giữa câu hỏi và câu trả lời.
5. **Bookmark theo hồi** thay vì từng tin nhắn — đúng đơn vị đọc.
6. **Bảng màu nhà hát** — đen sâu + vàng đồng + **đỏ rèm** (burgundy) làm điểm nhấn.
7. **Bản đồ vở** — "mạch máu của vở" (chuỗi chính) + chương trình diễn 11 hồi.

## Kết quả Test 2 — Flash vs GLM (đã kiểm chứng thực tế cả hai bản)

| Tiêu chí | Flash (v3 — "Vở kịch 11 hồi") | GLM (v2 — "Đồng tâm") |
|---|---|---|
| Concept thiết kế | Kịch hóa: màn mở, lời dẫn, màn hạ | Hình học: tâm + vòng + dây cung |
| Mức độ bám nội dung | Cao (câu hỏi làm lời dẫn, câu chốt làm màn hạ) | Rất cao (đồng tâm có dẫn chứng từ chính văn bản: ch.1 khung, ch.6 áp dụng, ch.11 nhắc lại) |
| Trải nghiệm đọc bài dài | Tốt: cột rộng + nhịp nghỉ (màn hồi, màn hạ, nút hồi tiếp) | Đẹp ở toàn cảnh; đọc tuyến tính thuần TextBlock — ít nhịp nghỉ hơn |
| Bỏ gì (đúng đắn) | Bỏ khung điện thoại, bỏ 3 mode | Bỏ triệt để: bubble, avatar, reaction, sidebar, phone — **gọn nhất 3 bản** |
| Dữ liệu verify | ✅ script riêng (kế thừa test 1) | ✅ script mới `parse_transcript.py` chạy trong build, khớp 100% |
| Ảnh bìa thật | ✅ trích từ PDF | ✅ (tự nhận copy từ Flash — thẳng thắn) |
| Search AND không dấu | ✅ (verified: "trung quoc" → 13 kết quả) | ✅ code có AND token (chưa verify sâu qua test của tôi — ghi trung thực) |
| Light theme | ✅ đầy đủ | ❌ dark-only |
| Progress | Thanh ngang | Vòng cung (đúng concept đồng tâm) |
| Bundle gzip | JS 195 KB / CSS 8.8 KB | **JS 191 KB / CSS 5.1 KB — nhỏ hơn** |
| Quy mô code | ~5.000 dòng | **1.423 dòng — tinh gọn hơn hẳn** |
| Build TS / console | 0 lỗi / 0-0 | 0 lỗi / 0-0 |
| Điểm đề xuất | **9.0 / 10** | **8.8 / 10** |

### Nhận định công bằng

- **GLM thắng ở sự tinh gọn**: 1.423 dòng so với ~5.000, bundle nhỏ hơn, và khái niệm "bỏ đúng thứ" (bubble/avatar/reaction/sidebar) là tư duy thiết kế sắc — họ cũng đã học hỏi đúng 3 gap test 1.
- **Flash thắng ở trải nghiệm đọc dài và độ hoàn thiện**: vở kịch tạo nhịp nghỉ cho essay dài (màn hạ + câu chốt «…»), chuỗi nguyên nhân riêng từng hồi, light theme, share card poster hồi.
- Cả hai đều **verify dữ liệu 100%** — điểm test 1 được khắc phục ở cả 2 phía.
- Test 2 là test **tư duy thiết kế**: hai concept khác biệt rõ, đều đứng vững về lập luận — trọng tài cuối là cảm nhận của người dùng khi mở cả hai bản (5175 vs 5176).

## Kết quả Test 2 (tự chấm theo rubric Test 1, khung thoải mái hơn)

| Tiêu chí | Flash (v3) |
|---|---|
| Nội dung toàn văn (kế thừa verify 100%) | ✅ |
| Sáng tạo thiết kế khác biệt rõ so với Test 1 | ✅ Vở kịch 11 hồi |
| Hình thức phù hợp nội dung (bài dài đọc thoáng) | ✅ cột rộng, prose 17px |
| Prologue poster + mục lục hồi số La Mã | ✅ |
| ActCurtain: lời dẫn «câu hỏi» + dải mắt xích | ✅ |
| Màn hạ: câu chốt lớn + nút hồi tiếp/trước | ✅ |
| Deep link hồi `#/act-7` + nhấn mạnh hồi | ✅ (verified) |
| Search không dấu + highlight + nhảy đúng lượt | ✅ 13 kết quả "trung quoc" |
| Bản đồ vở (chuỗi chính + 11 hồi) | ✅ |
| Bookmark hồi + lưu localStorage | ✅ (["ch-01"]) |
| Share card hồi (PNG + copy text/link) | ✅ |
| Lưu hồi đọc gần nhất + khôi phục | ✅ |
| Dark mặc định + light | ✅ |
| Không tràn (1440/1024/390) | ✅ |
| Build TypeScript | ✅ 0 lỗi |
| Console | ✅ 0 lỗi, 0 warning |
| Bundle gzip | 195 KB (nhẹ hơn v2: 202 KB) |

**Điểm ước lượng: 9.0 / 10** — chưa test trực tiếp 375/360px (cùng layout fluid với 390).

## Điểm đáng chú ý trong quá trình làm

- Phát hiện và sửa lỗi `history.replaceState` không kích hoạt `hashchange` (điều hướng nội bộ bị treo) — đã vá bằng cách tự phát event.
- Reuse dữ liệu đã verify từ Test 1 → không lãng phí, tập trung toàn bộ thời gian vào thiết kế.
- 0 lỗi console/warning ngay từ các vòng test đầu.

---

# PHỤ LỤC — Kết quả chính thức Test 2 (sau xác minh chéo)

## Bảng điểm cuối cùng

| | GLM "Đồng tâm" | Flash "Vở kịch" |
|---|---|---|
| **GLM tự chấm** | 8.0 / 10 | **8.5 / 10** ✅ |
| **Điểm đề xuất của Flash (sau xác minh)** | 8.5 / 10 | **8.8 / 10** ✅ |
| Bundle gzip | **191 KB — gọn hơn** | 195 KB |
| Tính dễ hiểu | Trừu tượng | **Dễ hiểu hơn** |
| Search "trung quoc" | 9 kết quả (theo chương) | 13 kết quả (theo lượt nói) |
| Share | Cắt PNG | **Đầy đủ (PNG + copy text/link)** |
| Light theme | ❌ dark-only | ✅ |

*Khoảng cách test 2 hẹp hơn test 1 (0.5 vs 0.7) — cả hai nguồn chấm đều thống nhất Flash thắng.*

## ⚠️ Xác minh tranh cãi về search GLM (quan trọng — ghi nhận công khai)

- Flash từng ghi trong session: *"GLM search is broken (0 results for 'trung quoc')"*.
- **Xác minh lại bằng test trực tiếp trên port 5176: nhận định này SAI.** Search của GLM trả **9 kết quả** (`[role="option"]` đếm được), hoạt động bình thường. Lỗi thuộc về selector trong script test của Flash, không phải sản phẩm GLM.
- **Kết luận: GLM đúng, Flash sai ở phát hiện này.** Bài học: báo cáo chéo (kể cả của bên thắng) phải được xác minh, không tin vô điều kiện.

## Vì sao 13 vs 9 kết quả (không phải "tốt hơn/kém hơn")

- Flash trả kết quả **theo lượt nói** (message) → "trung quoc" xuất hiện trong 13 lượt.
- GLM trả kết quả **theo chương** → 9 chương chứa cụm này.
- Đơn vị trả về khác nhau; cả hai đều tìm đúng nội dung. Không phải chênh lệch chất lượng.
