# BÁO CÁO RÚT KINH NGHIỆM — GLM vs Flash

**Dự án:** equity-research-vn (cohort → VN100 → VN-ALL 1.000 mã)
**Phiên phân tích:** GLM sess_3b54417a + Flash sess_89fd6e25
**Ngày:** 2026-08-08
**Mục đích:** Rút kinh nghiệm phối hợp 2 model cho dự án tương lai

---

## 1. Bối cảnh

Hai model cùng tham gia dự án equity-research-vn qua nhiều giai đoạn:
- **7 đợt cohort** (V1→V7): GLM chạy + Flash nghiệm thu chéo
- **VN100 (73 mã)**: GLM chạy 6 phiên (v1→v6), Flash build mẫu CTD 72/74
- **VN-ALL (1.000 mã)**: GLM chạy 5 đợt × 200 mã, Flash vá builder + dashboard

Mỗi model có thế mạnh chuyên môn khác nhau — bài học này ghi nhận để phối hợp hiệu quả hơn.

---

## 2. GLM mạnh về gì?

### 2.1 Chạy batch quy mô lớn, đúng kỷ luật
- **VN-ALL 1.000 mã**: 5 đợt × 200 mã, 0 mã bỏ lửng, tracker ghi sau mỗi mã
- **VN100 6 phiên** (v1→v6): kiên trì fix từ 53.2 → 73.5 avg recall (+20 điểm)
- **Chunk 50 mã/lần**: chia nhỏ batch tránh background task kill, tự nối tiếp từ tracker khi gián đoạn
- **Bằng chứng**: 846 done, 606 mã 74/74, avg 73.3

### 2.2 Phát hiện bug hệ thống có giá trị
- **Bug `_normalize_number` verifier**: `"33,797.9"` (format EN) bị parse thành 33.7979 thay vì 33797.9 → ảnh hưởng 4 REQ cùng lúc (034/033/036/064). Fix bằng raw number format → giải quyết hàng loạt.
- **REQ-063 fail 92%**: phát hiện đúng lúc, báo ZCode đúng luật (dừng giữa đợt chờ vá)
- **REQ-031/048 false positive**: "3 mức" bị bắt là drawdown, "CFO" bị bắt là claim quản lý — báo chính xác

### 2.3 Viết renderer tự sinh (từ đầu)
- `vn100_v2.py` (17 REQ fix tổng): tự viết fetch + tech score thật + news fetch + narrative generator
- Từ 0 mã 74/74 → 45 mã 74/74 (phiên V4) bằng renderer tự sinh
- Sau khi ZCode đóng builder chuẩn, GLM chuyển sang dùng builder → 606 mã 74/74

### 2.4 Trung thực báo cáo
- 14 mã needs_human có bằng chứng (recall + fail_reqs + lý do)
- 140 mã NO_DATA nêu rõ "API trả price=0"
- Không giấu số liệu xấu

---

## 3. Flash mạnh về gì?

### 3.1 Debug sâu, surgical (vá chính xác)
- **REQ-063/064**: GLM phát hiện fail 92%/31% nhưng không fix được root cause. Flash đọc evidence → tìm ra bug trong builder (narrative nhắc method valuation nhưng thiếu giá trị) + pack (từ ngữ gây nhiễu) → vá surgical, test 3 mã/fix → 0% fail.
- **REQ-060 (EPS mâu thuẫn)**: Flash thêm back-calc khi NPAT/shares lệch >15% → 3/3 mã test 74/74.
- **343 mã thiếu ngành "Industrial"**: Flash soi kỹ tracker, phát hiện 34% mã bị xếp "general" sai → thêm nhóm 13 vào sector_pack.

### 3.2 Xác minh chéo độc lập
- Không tin báo cáo GLM nguyên văn — mở tracker đếm lại trực tiếp
- Phát hiện GLM báo "1.192" sai (thật ra 1.214 — code của chính GLM tính ra 1.214)
- Phát hiện audit fail sau commit GLM (đổi nháy kép → backtick)

### 3.3 Tối ưu chi phí + viết tool giá trị
- **Chế độ `--reuse`**: đọc data cũ, đổi sector, render lại — tiết kiệm toàn bộ API cost (re-render 306 mã industrial chỉ tốn 1 call news/mã)
- **Dashboard HTML offline** (`vnall_dashboard.py`): hiển thị P/E, P/B, ROE, lọc ngành, phát hiện định giá bất thường — không gọi API

### 3.4 Kiến trúc tổng thể
- Build tay CTD fixture 72/74 làm chuẩn so sánh cho mọi phiên sau
- Thiết kế builder chuẩn (build_report.py) đóng vào skill — GLM chỉ chạy, không tự viết renderer

---

## 4. Điểm yếu từng model

### GLM — điểm yếu
| Yếu điểm | Bằng chứng | Tác động |
|----------|-----------|----------|
| **Báo số chưa verify** | Báo "1.192" trong khi code tính ra 1.214 (lần thứ 3) | Hiểu nhầm quy mô |
| **Dừng sớm đôi lúc** | V2 cohort định decline, user phải nói "a cần e thực hiện lệnh đó" | Chậm tiến độ |
| **Truyền sai parameter** | Truyền sector sai cho batch runner | Recall thấp hơn cần thiết |
| **Mất data 2 lần** | Lưu /tmp, reboot máy → mất hết | Phải chạy lại 1.000 mã |

### Flash — điểm yếu
| Yếu điểm | Bằng chứng | Tác động |
|----------|-----------|----------|
| **Không chạy batch lớn** | Phụ thuộc GLM sinh raw data | Không độc lập hoàn toàn |
| **Mất data 2 lần** | Cũng lưu /tmp trước khi học bài học | Trùng lặp công việc |
| **Chỉnh sửa Edit nhiều lần** | Dashboard v2 qua ~5 lần Edit nhỏ | Tốn thời gian |
| **Phụ thuộc git state** | Bị chặn push do merge conflict không liên quan | Chậm commit |

---

## 5. Bảng so sánh tổng hợp

| Khía cạnh | GLM | Flash | Model phù hợp |
|-----------|-----|-------|---------------|
| **Chạy batch lớn** | 1.000 mã, 0 bỏ lửng | Từng mã | **GLM** |
| **Debug sâu** | Phát hiện bug, không fix root cause | Vá surgical, test 3 mã/fix | **Flash** |
| **Kiểm chứng** | Trung thực nhưng đôi khi đếm sai | Xác minh chéo độc lập | **Flash** |
| **Viết tool** | Renderer tự sinh (từ đầu) | Dashboard + --reuse mode | **Cả hai** (khác vai trò) |
| **Kiên trì** | 6 phiên fix liên tục (+20 điểm) | Tập trung vá surgical | **GLM** |
| **Tối ưu cost** | Sleep 55s, chunk 50 | --reuse (0 API call) | **Flash** |
| **Báo cáo** | Đầy đủ, trung thực | Xác minh chéo + bắt lỗi số | **Flash** (verify) |

---

## 6. Bài học phối hợp cho tương lai

### 6.1 Phân vai tối ưu
- **GLM = vận hành**: chạy batch lớn, render, gom metrics, tracker, báo cáo định kỳ
- **Flash = kỹ thuật**: debug root cause, vá builder/verifier, viết tool tối ưu, xác minh chéo
- **Quy trình**: GLM chạy → Flash verify → Flash vá bug hệ thống → GLM chạy lại

### 6.2 Quy tắc phối hợp
1. **GLM chạy batch, Flash verify số liệu** (không tin second-hand)
2. **Flash vá bug, GLM chạy lại batch lớn** để kiểm chứng fix
3. **GLM phát hiện fail → dừng → báo Flash** (đúng luật, không tự vá source skill)
4. **Flash thiết kế builder, GLM chỉ chạy** (Lesson #18 — cấm tự viết renderer)
5. **Cả hai lưu data vào ổ cứng** (không /tmp — bài học mất data 2 lần)

### 6.3 Khi nào dùng từng model

| Tác vụ | Model | Lý do |
|--------|-------|-------|
| Chạy 1.000+ mã batch | GLM | Kiên trì, đúng kỷ luật, 0 bỏ lửng |
| Debug 1 REQ fail | Flash | Đọc evidence sâu, vá surgical |
| Xác minh báo cáo | Flash | Không tin second-hand, đếm lại |
| Viết dashboard/tool | Flash | Tối ưu cost, kiến trúc tổng thể |
| Viết renderer từ đầu | GLM | Kiên trì fix 6 phiên liên tục |
| Phát hiện bug hệ thống | Cả hai | GLM phát hiện đúng lúc, Flash tìm root cause |
| Cập nhật định kỳ hàng quý | GLM | Chạy batch quen, tracker kỷ luật |

---

## 7. Kết luận

**Không có model "giỏi mọi việc".** GLM mạnh vận hành (chạy batch lớn, kiên trì fix), Flash mạnh kỹ thuật (debug sâu, vá surgical, xác minh chéo). Phối hợp đúng vai → hiệu quả cao nhất.

**Bài học cốt lõi:** Đẳng cấp 2 model ngang nhau — khác biệt là **cách tiếp cận** (vận hành vs kỹ thuật), không phải giỏi-kém. Như bác sĩ phẫu thuật (Flash) và điều dưỡng (GLM): cả 2 đều cần thiết, vai trò khác nhau.

---

**Ký:** GLM sess_3b54417a — 2026-08-08
