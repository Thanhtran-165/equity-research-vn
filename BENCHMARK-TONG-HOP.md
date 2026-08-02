# BENCHMARK TỔNG HỢP — Chiến tranh, Tiền tệ và Trật tự mới

> Hai vòng test, cùng input (transcript + PDF + DOCX), hai model độc lập:
> **DeepSeek V4 Flash** (thư mục `chien-tranh-tien-te-v2` / `-v3`) vs **GLM** (`chien-tranh-tien-te-glm` / `-glm-v2`).
> Ngày: 2026-08-02. Chi tiết đầy đủ ở `BENCHMARK-TEST-1.md`.

---

## TEST 1 — Theo master prompt GPT SOL (chat điện thoại + sidebar)

| | GLM | Flash |
|---|---|---|
| Điểm (GLM tự chấm, Flash đồng ý) | 7.8 / 10 | **8.5 / 10** ✅ |
| Thắng ở | Kỷ luật: 0 warning, CSS gọn, build 1 lần pass | Ảnh bìa thật, **verify dữ liệu 100%**, hoàn thiện chi tiết khó |
| Thua vì | Không verify data, ảnh bìa vẽ tay, bỏ cuộc 1 gap | — |

## TEST 2 — Thiết kế tự do (không theo prompt cứng nhắc)

| | GLM "Đồng tâm" | Flash "Vở kịch 11 hồi" |
|---|---|---|
| Điểm (GLM tự chấm) | 8.0 / 10 | **8.5 / 10** ✅ |
| Điểm (Flash đề xuất sau xác minh) | 8.5 / 10 | **8.8 / 10** ✅ |
| Concept | Vòng tròn: tâm + 11 chương + dây cung | Màn mở, lời dẫn «câu hỏi», màn hạ «câu chốt» |
| Mạnh nhất | **Độ gọn**: 1.423 dòng, bundle 191 KB, "bỏ đúng thứ" | **Thực dụng + dễ hiểu**, nhịp đọc essay dài, light theme |
| Yếu nhất | Khái niệm trừu tượng, dark-only, đọc tuyến tính khô | Bundle to hơn, giữ nhiều component hơn |

## Kết quả chung qua 2 test

- **Flash thắng cả 2 test** — nhưng khoảng cách thu hẹp: Test 1 = 0.7 điểm, Test 2 = 0.5 điểm (theo GLM tự chấm).
- **Quy luật rút ra (lời GLM, được Flash đồng ý)**: GLM thiên về *tinh tế + kỷ luật*, Flash thiên về *thực dụng + đầy đủ* — trong sản phẩm thực tế, thực dụng thắng.
- **Điểm GLM cải thiện qua 2 test**: bù đúng 3 gap test 1 (verify data bằng script, ảnh bìa thật, search AND) — học hỏi nhanh.
- **Điểm Flash giữ vững**: verify dữ liệu bằng máy, hoàn thiện chi tiết, không bỏ cuộc khi gặp lỗi khó.

## Ghi chú quan trọng về tính trung thực (đã xác minh chéo)

1. **Flash từng báo sai về search của GLM** ("0 results") — xác minh lại: GLM trả **9 kết quả**, hoạt động tốt; lỗi thuộc script test của Flash. **GLM đúng, Flash sai ở phát hiện này** — đã ghi nhận công khai.
2. Số kết quả search khác nhau (13 vs 9) là do đơn vị trả về (theo lượt nói vs theo chương), không phải chênh lệch chất lượng.
3. Cả hai bản đều: build 0 lỗi TypeScript, console 0 lỗi/0 warning, dữ liệu toàn văn verified 100%, responsive, dark theme.

## Cách mở so sánh trực tiếp

| Bản | URL |
|---|---|
| Flash Test 1 (chat điện thoại) | http://localhost:5174/ |
| Flash Test 2 (vở kịch 11 hồi) | http://localhost:5175/ |
| GLM Test 2 (đồng tâm) | http://localhost:5176/ |
| GLM Test 1 | http://localhost:5173/ |
