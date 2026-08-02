# GOAL SPEC — VN100 (kèm LENH-VN100-CHO-GLM.md)

> Mục tiêu cho GLM — đọc cùng lệnh VN100. Đây là "hợp đồng kết quả", không phải mô tả hoạt động.

## MỤC TIÊU (điều gì sẽ ĐÚNG khi xong)

100 mã VN100 mỗi mã có **kết quả cuối rõ ràng + bằng chứng**, chạy qua pipeline
equity-research-vn v3.2.0 (74 REQ), không có mã nào "bỏ lửng".

## BẰNG CHỨNG HOÀN THÀNH (cái gì chứng minh)

1. `/tmp/vn100_tracker.json` — đủ **100 dòng**, mỗi mã: ticker, industry, status
   ∈ {done, needs_human, NO_DATA, BLOCKED_API}, recall, fail_reqs, charts, token_est
2. `/tmp/vn100_reports/` — file HTML mọi mã có recall ≥ 60/74 (kèm evidence REQ)
3. `/tmp/VN100-REPORT.md` — bảng 100 mã + thống kê + top-10 REQ fail + 10 mã "cơ hội"
4. Không mã nào status rỗng / "đang chạy" ở cuối

## NGƯỠNG ĐỊNH LƯỢNG (thành công đo bằng số)

| Chỉ số | Ngưỡng |
|---|---|
| Mã có status cuối rõ ràng | **100/100** (0 bỏ lửng) |
| Mã đạt recall ≥ 60/74 | **≥ 60/100** |
| REQ-074 (P/E chuẩn hóa) trên mã chu kỳ | PASS khi kích hoạt |
| Tổng token thực tế | Ghi rõ (so dự toán 6-7M, ±30% chấp nhận) |
| Mã needs_human | ≤ 10, mỗi mã kèm bằng chứng (REQ id + evidence + đoạn HTML) |

## PHẠM VI

- TRONG: 100 mã VN100; tự sửa narrative/HTML/data trong work dir của mình; ghi tracker + progress sau mỗi mã
- NGOÀI: sửa source skill (cấm); commit/push (cấm); copy HTML giữa mã (cấm); chạy song song (cấm)

## ĐIỀU KIỆN DỪNG ĐỂ HỎI / BÁO (thay vì cày mù)

1. **Hết context / crash giữa đợt** → ghi `/tmp/vn100_progress_<đợt>.md` ("dừng tại mã X, lý do Y") → dừng an toàn. KHÔNG xin phép — đây là hành vi đúng.
2. **Nghi lỗi skill** → ghi `needs_human` + bằng chứng → TIẾP TỤC mã khác (ZCode vá skill song song, không chờ)
3. **API chết** → thử lại sau 5 mã; thử lần 2 vẫn chết → `BLOCKED_API` + triệu chứng
4. **Chỉ hỏi ZCode khi**: mâu thuẫn lệnh (không tự quyết được), hoặc cần quyết định ngoài phạm vi

## CẤM (hành vi bị coi là bỏ cuộc)

- Dừng mã vì "fail nhiều" (4 vòng fix là luật, không phải gợi ý)
- Chạy đợt 2-5 mà tracker đợt 1 chưa đầy đủ (nối tiếp phải dựa tracker)
- Nói "không làm được" mà không kèm bằng chứng + phương án (ghi needs_human + tiếp tục là phương án mặc định)
