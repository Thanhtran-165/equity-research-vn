# Spec: Mở rộng bài phỏng vấn Lương Văn Phong thành tài liệu giáo dục AI

- **Ngày**: 2026-07-23
- **Trạng thái**: Đã duyệt thiết kế, chờ user duyệt spec
- **File gốc**: `/Users/bobo/Downloads/梁文锋-投资者交流会-越南语译本.md` (phỏng vấn DeepSeek đã dịch tiếng Việt, ~18.000 chữ, 9 sơ đồ Mermaid)
- **File output**: `/Users/bobo/Downloads/DeepSeek-Phong-van-Ban-mo-rong-cho-nguoi-moi-AI.md`

## 1. Mục tiêu

Biến bài phỏng vấn Lương Văn Phong (DeepSeek) thành tài liệu giáo dục AI cho:
- **Người mới hoàn toàn** chưa biết gì về AI
- **Người đầu tư/kinh doanh** muốn hiểu bức tranh kinh tế AI

Nguyên tắc: **chèn kiến thức nền vào bài phỏng vấn**, giữ nguyên dòng chảy câu chuyện. Người đọc vừa đọc phỏng vấn vừa học AI.

## 2. Yêu cầu từ user

| Yếu tố | Quyết định |
|---|---|
| Đối tượng | Người mới hoàn toàn + Người đầu tư/kinh doanh |
| Cấu trúc | Chèn bổ sung vào bài phỏng vấn (Cách A) |
| Phạm vi | 4 nhóm: AI cốt lõi + Lịch sử AI + Kinh tế AI + Phần cứng AI |
| Độ sâu | Vừa đủ (~500-800 chữ/box) |
| Jargon | Có — mỗi box liệt kê từ lóng ngành + cách người trong ngành nói chuyện |
| **Research** | **BẮT BUỘC WebSearch Mỹ** cho mọi thông tin về Mỹ (lịch sử, công ty, NVIDIA, thị trường, jargon) |

## 3. Danh sách 24 Context Box

### 📘 Nhóm 1: Khái niệm AI cốt lõi (10 box)
1. **AGI là gì?** — khác gì AI thường (Chương 1)
2. **LLM** — mô hình ngôn ngữ hoạt động thế nào (Chương 2)
3. **CoT** — chuỗi tư duy, kèm ví dụ toán (Chương 2)
4. **Agent** — khác chatbot thế nào (Chương 2)
5. **Học liên tục** — vì sao AI chưa thay người (Chương 2)
6. **Singularity** — điểm kỳ diệu có thật không (Chương 2)
7. **Embodied AI** — robot thông minh (Chương 2)
8. **Hallucination** — tại sao AI bịa (Chương 5)
9. **Scaling Law** — cứ to lên là giỏi? (Chương 6)
10. **Multimodal** — AI hiểu ảnh + âm thanh (Chương 8)

### 📗 Nhóm 2: Lịch sử AI + vì sao bùng nổ (4 box) — BẮT BUỘC WebSearch Mỹ
11. **Lịch sử AI rút gọn** (1950→2025) — đầu tài liệu
12. **Tại sao AI bùng nổ 2022** — ChatGPT moment — đầu tài liệu
13. **DeepSeek là ai** — lịch sử công ty — Chương 1
14. **Lương Văn Phong là ai** — tiểu sử — Chương 1

### 📕 Nhóm 3: Kinh tế AI + cuộc đua toàn cầu (5 box) — BẮT BUỘC WebSearch Mỹ
15. **API + định giá thế nào** — Chương 4
16. **Open source vs Closed source** — Chương 4
17. **Thị trường AI toàn cầu** — ai dẫn đầu — Chương 4
18. **Cuộc đua Mỹ-Trung về AI** — bối cảnh địa chính trị — Chương 8
19. **OpenAI vs Anthropic vs Google vs Meta** — Big 4 — Chương 8

### 📙 Nhóm 4: Phần cứng AI (5 box) — BẮT BUỘC WebSearch Mỹ
20. **GPU/Card AI là gì** — vì sao đắt — Chương 3
21. **NVIDIA vì sao độc quyền** — hào nước CUDA — Chương 5
22. **CUDA là gì** — phần mềm khó thay — Chương 5
23. **Chip Huawei vs NVIDIA** — so sánh — Chương 5
24. **TSMC & chuỗi cung ứng chip** — vì sao khó làm chip — Chương 5

**Tổng: 24 box × ~700-800 chữ = ~18.000 chữ thêm**

## 4. Cấu trúc mỗi Context Box (9 phần)

1. **Định nghĩa** (~30 chữ) — khái niệm bằng tiếng Việt đơn giản nhất
2. **Ví dụ đời thường** (~60 chữ) — không thuật ngữ, như giải thích cho trẻ
3. **Cách hoạt động** (~150 chữ) — đủ hiểu, không quá kỹ thuật
4. **Tại sao quan trọng** (~80 chữ) — giá trị, cho người đầu tư
5. **Nếu bỏ qua sẽ hiểu sai** (~80 chữ) — sai lầm phổ biến
6. **Mẹo nhớ** (~15 chữ) — câu vần/câu thần chú
7. **Jargon trong ngành** — từ lóng/từ viết tắt + dịch nghĩa
8. **Cách nói chuyện người trong ngành** — 1-2 câu ví dụ, kèm chú giải "thực ra có nghĩa là..."
9. **Liên kết bài phỏng vấn** — trích 1 câu thật của Lương Văn Phong

### Format box
- Bọc trong blockquote (nền vàng trong PDF)
- Tiêu đề: `📚 KIẾN THỨC NỀN #[số]: [Tên]`
- Box có thể bỏ qua nếu đã biết

## 5. Sơ đồ bổ sung (8 sơ đồ Mermaid mới)

| # | Thuộc box | Sơ đồ | Loại |
|---|---|---|---|
| 1 | Lịch sử AI | Timeline 1950→2025 (6 cột mốc) | Timeline |
| 2 | LLM | Pipeline: training data → weights → inference | Flowchart |
| 3 | CoT | So sánh "AI không CoT" vs "AI có CoT" | So sánh |
| 4 | Agent | Agentic loop (think → act → observe → loop) | Flowchart |
| 5 | Scaling Law | Biểu đồ "càng nhiều compute càng giỏi" | Chart |
| 6 | GPU/CUDA | Stack: Ứng dụng → CUDA → Driver → GPU | Stack |
| 7 | Thị trường AI | Bảng xếp hạng Big 4 + DeepSeek | Bảng |
| 8 | Cuộc đua Mỹ-Trung | So sánh năng lực + tài nguyên | So sánh |

→ Tổng tài liệu: **17 sơ đồ** (9 cũ + 8 mới). Tất cả resize về 643px width, render bằng WeasyPrint (đã fix layout).

## 6. Từ điển jargon (cuối tài liệu)

Bảng ~80-100 từ, 4 cột:

| Cột | Mô tả |
|---|---|
| Thuật ngữ | Từ lóng/tiếng Anh gốc |
| Nghĩa Việt | Dịch + giải thích 1 câu |
| Ngữ cảnh | Khi nào nghe thấy |
| Ví dụ câu | Câu người trong ngành nói, kèm dịch |

Ví dụ:
- "FLOPs" — Số phép tính AI thực hiện — Đọc paper — "Model này tốn 10²⁶ FLOPs để train" = "Mô hình này cần 10²⁶ phép tính để học"
- "context window" — Khả năng nhớ của AI — So sánh model — "Claude có context window 200k" = "Claude nhớ được 200.000 chữ"

## 7. Quy ước chất lượng BẮT BUỘC

| Quy ước | Cách verify |
|---|---|
| **Không bịa số liệu** | Mỗi con số phải có nguồn (phỏng vấn hoặc WebSearch) |
| **Không bịa trích dẫn** | "LIÊN KẾT BÀI PHỎNG VẤN" = câu thật trong transcript |
| **Jargon phải thật** | Mỗi từ lóng phải được WebSearch xác nhận người trong ngành Mỹ thật sự dùng |
| **Ví dụ phải đời thường** | Không dùng thuật ngữ trong "Ví dụ đời thường" |
| **Mỗi box độc lập** | Đọc riêng 1 box vẫn hiểu được |
| **WebSearch Mỹ BẮT BUỘC** | Mọi thông tin về Mỹ (lịch sử, công ty, NVIDIA, jargon) phải research |

### Phần "Nguồn" ở cuối mỗi box
- Danh sách URL/article mình đã WebSearch
- Chỉ dùng số liệu có năm (VD: "2024 revenue $X")

## 8. Quy trình 8 bước

```
1. TẠO 24 BOX — WebSearch Mỹ cho box cần thiết, verify jargon
2. CHÈN BOX VÀO TÀI LIỆU — sau đoạn phỏng vấn đầu tiên đề cập
3. TẠO 8 SƠ ĐỒ MERMAID MỚI
4. TẠO TỪ ĐIỂN JARGON (80-100 từ)
5. GHÉP FILE MARKDOWN CUỐI
6. XUẤT PDF — WeasyPrint (đã fix layout), verify sơ đồ 70%+ width
7. KIỂM TRA CHẤT LƯỢNG — số liệu, trích dẫn, tiếng Việt
8. BÁO CÁO + MỞ PDF
```

### Ước tính research
- ~12 box cần WebSearch Mỹ × 2-3 query = ~30 lượt search
- Verify jargon: ~10 lượt search
- **Tổng: ~40-50 WebSearch** trong toàn dự án

## 9. File output cuối

- `/Users/bobo/Downloads/DeepSeek-Phong-van-Ban-mo-rong-cho-nguoi-moi-AI.md` (Markdown)
- `/Users/bobo/Downloads/DeepSeek-Phong-van-Ban-mo-rong-cho-nguoi-moi-AI.pdf` (PDF)

**Thông số dự kiến**:
- ~40.000 chữ (gấp ~2.2 lần bản gốc)
- ~200 trang PDF
- 17 sơ đồ Mermaid
- 24 box kiến thức nền
- Từ điển jargon 80-100 từ

## 10. Rủi ro & cách xử lý

| Rủi ro | Cách xử lý |
|---|---|
| Tài liệu quá dài | Mỗi box có TL;DR 1 câu đầu → có thể skip |
| Box chồng chéo nội dung | Mỗi box focus 1 khái niệm |
| Jargon sai (bịa từ lóng) | WebSearch xác nhận + chỉ dùng jargon chắc chắn |
| Sơ đồ layout hẹp | Pipeline đã fix: resize 643px + WeasyPrint |
| Thông tin Mỹ sai/lỗi thời | WebSearch lại, ghi năm rõ ràng |
