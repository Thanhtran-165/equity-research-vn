# THƯ MỜI KIỂM ĐỊNH ĐỘC LẬP — DỰ ÁN equity-research-vn

**Mời:** GPT 5.6 Sol
**Người mời:** Chủ đầu tư dự án (user) — qua ZCode
**Ngày:** 2026-08-08
**Đối tượng kiểm định:** Hệ thống `equity-research-vn` — bộ nghiên cứu cổ phiếu Việt Nam tự động (skill + verifier + builder + quy trình vận hành)

---

## 1. VÌ SAO MỜI BẠN

Bạn được chọn vì thế mạnh riêng: **logic chặt chẽ và tư duy học thuật**. Dự án này
đã qua nhiều vòng kiểm tra thực chiến (1.000 mã thật), nhưng chưa có một bên thứ ba
độc lập đứng từ góc độ **logic hệ thống + chuẩn mực học thuật tài chính** để chấm điểm
tổng thể. Đây chính là chỗ bạn mạnh nhất — và cũng là chỗ dễ bị bỏ sót nhất khi người
làm quen với hệ thống.

**Yêu cầu: review TOÀN BỘ hệ thống, nhưng trọng tâm chấm điểm đặt vào LOGIC và
HỌC THUẬT** (xem khung điểm §4 — hai mục này chiếm 50% tổng điểm).

## 2. BỐI CẢNH DỰ ÁN (đọc trước — 10 phút)

- **Skill** `equity-research-vn` (v3.2.0+): sinh báo cáo phân tích cổ phiếu VN từ dữ liệu
  vnstock (sponsor VCI) + BCTC kiểm toán. Định vị: **evidence pack khách quan — KHÔNG
  khuyến nghị mua/bán**.
- **Verifier độc lập** `independent_verifier.py` (~4.600 dòng): 74 REQ (requirements.yaml),
  recompute từng con số trong báo cáo từ dữ liệu gốc (data-driven), gate fail-closed,
  `.verifier-hash` chống sửa lén. Builder (`build_report.py`) tự động chạy verifier sau
  mỗi báo cáo.
- **Kết quả thực chiến**: 1.000 mã toàn thị trường (HOSE+HNX+UPCOM), **606 mã đạt 74/74
  tiêu chí**, 846 mã ≥70/74, trung bình 73.3/74; 0 mã bịa số liệu lọt qua (đã kiểm chứng
  bằng đối chiếu thủ công nhiều lượt). 4 lỗi hệ thống đã phát hiện qua chạy thật và vá:
  REQ-063 (contract thiếu key), REQ-064 (từ ngữ pack gây false positive), REQ-060 (EPS
  mâu thuẫn nội tại), nhóm ngành thiếu.
- **Mô hình vận hành**: skill được nhiều agent chạy (ZCode thiết kế/vá, GLM chạy batch
  lớn) — cần một bên kiểm định không tham gia phát triển.

## 3. NHIỆM VỤ KIỂM ĐỊNH

1. **Đọc hiểu hệ thống** (files §6) — đánh giá kiến trúc, thiết kế 74 REQ, logic verifier.
2. **Chấm điểm theo khung §4** — mỗi tiêu chí: điểm /100 + nhận xét 1-3 câu + bằng chứng.
3. **Thử nghiệm bịa số liệu (BẮT BUỘC, ≥1 lần)**: lấy 1 báo cáo đạt 74/74 bất kỳ,
   sửa 2-3 con số trong báo cáo HTML (tăng/giảm giá trị, đổi dấu, làm tròn sai), chạy
   verifier — ghi lại: lỗi nào bị bắt, lỗi nào LỌT QUA (nếu có). Đây là phép thử quan trọng
   nhất về logic phòng thủ.
4. **Soi lỗ hổng logic**: tìm kịch bản mà verifier có thể bị qua mặt (bịa số liệu mà
   không bị phát hiện) — ngay cả kịch bản khó xảy ra cũng đáng ghi.
5. **Kiểm tra chuẩn mực học thuật** (§5): công thức tài chính có sai chuẩn không.
6. **Kết luận**: điểm tổng /100 + đạt/không đạt từng tiêu chí + danh sách lỗ hổng xếp
   theo mức nghiêm trọng + đề xuất sửa cụ thể.

**GIỚI HẠN: KHÔNG sửa code, KHÔNG sửa file dự án.** Bạn chỉ đọc + chấm + báo cáo.
Mọi thay đổi do chủ đầu tư quyết định sau khi nhận báo cáo.

## 4. KHUNG CHẤM ĐIỂM (tổng 100 — trọng số theo thế mạnh model)

| # | Tiêu chí | Trọng số | Câu hỏi trọng tâm |
|---|----------|----------|--------------------|
| 1 | **Logic hệ thống & tính nhất quán** | **25%** | Verifier có tự mâu thuẫn không? REQ có chồng chéo/gap/điều kiện kích hoạt sai? Gate fail-closed có thật không? Có đường tắt (backdoor) để báo cáo xấu qua cổng? |
| 2 | **Tính học thuật (chuẩn tài chính)** | **25%** | Công thức và cách diễn giải có đúng chuẩn mực học thuật/ngành không (xem §5)? Có khái niệm dùng sai, công thức ngụy biện, hoặc định nghĩa không chặt? |
| 3 | **Phòng thủ chống bịa số liệu (mutation)** | **20%** | Thử nghiệm §3.3: tỉ lệ bắt được? Lỗ hổng nào lọt? Mức độ dễ khai thác? |
| 4 | **Thiết kế quy trình & khả năng tái lập** | **15%** | Tracker-first, chống bỏ cuộc, bằng chứng needs_human, tái lập giữa các lần chạy (606↔628/74), quy trình phân công đa agent có hợp lý? |
| 5 | **Giá trị & tính trung thực của đầu ra** | **15%** | Báo cáo có đúng định vị "evidence pack khách quan" không? Có chỗ nào vô tình ngụ ý khuyến nghị đầu tư? Disclaimer đủ chưa? |

## 5. TRỌNG TÂM HỌC THUẬT — các công thức cần soi kỹ

1. **Graham Number** = √(22,5 × EPS × BVPS) — verifier recompute ±5%. Đúng chuẩn? BVPS tính từ equity/shares đúng quy ước?
2. **P/E chuẩn hóa** (REQ-074): kích hoạt khi CV(EPS 5 năm) > 30% VÀ EPS cuối < 80% đỉnh 5 năm; giá trị = giá ÷ median EPS. Logic chuẩn hóa chu kỳ có hợp lý? Ngưỡng có phản khoa học?
3. **EV/EBITDA**: EV = vốn hóa + nợ ròng (tổng tài sản − VCSH). Định nghĩa nợ ròng thay cho nợ có lãi có chấp nhận được khi dữ liệu hạn chế? Có nên báo cáo rõ giới hạn?
4. **Accrual** = LNST − CFO (dương nhiều = lợi nhuận kém chất lượng). Đúng chuẩn học thuật (Sloan)? Có cảnh báo đơn vị/ngành không?
5. **CAGR** 5 năm + **YoY** recompute (REQ-036/061): so sánh đỉnh-đáy chu kỳ có được xử lý đúng (pack ngành hướng dẫn)? Temporal alignment (REQ-034) chống gán sai năm?
6. **Cross-footing** (REQ-060): EPS ≈ NPAT/shares ±15%, PE×EPS ≈ giá, vốn hóa ≈ giá×cổ phiếu. Ngưỡng 15% hợp lý? Có false positive với công ty tăng vốn giữa năm?
7. **Ngân hàng**: dùng P/B + DDM, KHÔNG áp dụng FCFF/CCC — gate đúng đặc thù? (pack ngành §1)
8. **BĐS**: "P/E thấp chưa chắc rẻ" — ghi nhận doanh thu theo dự án — pack có truyền tải đúng?

## 6. FILES CẦN ĐỌC (đường dẫn máy chủ)

| File | Vai trò |
|---|---|
| `~/.zcode/skills/equity-research-vn/SKILL.md` | Quy trình 9 phase, định vị dự án |
| `~/.zcode/skills/equity-research-vn/requirements.yaml` | 74 REQ — nguồn sự thật |
| `~/.zcode/skills/equity-research-vn/scripts/independent_verifier.py` | Verifier độc lập (~4.600 dòng) |
| `~/.zcode/skills/equity-research-vn/scripts/build_report.py` | Builder chuẩn (fetch + build + render + verify) |
| `~/.zcode/skills/equity-research-vn/references/sector_pack.md` | 13 nhóm ngành + cách đọc BCTC + bẫy số liệu |
| `~/ZCodeProject/data/vnall/vnall_tracker.json` | Kết quả 1.000 mã |
| `~/ZCodeProject/data/vnall/vnall_metrics.json` | 860 mã: P/E, P/B, ROE... |
| `~/ZCodeProject/data/vnall/reports/<TICKER>_Complete_Report.html` | Báo cáo mẫu (chọn 2-3 mã bất kỳ để mutation test) |
| `~/ZCodeProject/PHOI-HOP-ZCODE-GLM.md` | Mô hình vận hành 2 agent |
| `~/ZCodeProject/DISCLAIMER.md` | Định vị đầu ra |

## 7. ĐẦU RA MONG ĐỢI (báo cáo kiểm định)

`/tmp/BAO-CAO-KIEM-DINH-GPT56SOL.md` gồm:
1. TL;DR: điểm tổng + kết luận đạt/không đạt
2. Bảng điểm 5 tiêu chí (§4) kèm nhận xét + bằng chứng
3. Kết quả thử nghiệm bịa số liệu: từng lỗi bịa → bị bắt/không bị bắt + cách khai thác
4. Danh sách lỗ hổng logic (xếp theo mức nghiêm trọng, mỗi lỗ: mô tả + kịch bản khai thác + đề xuất sửa)
5. Nhận xét học thuật từng công thức (§5): đúng/sai/điều chỉnh đề xuất
6. Điểm tổng hợp + khuyến nghị nghiệm thu (đạt/điều kiện/không đạt)

## 8. NGUYÊN TẮC KIỂM ĐỊNH

- **Độc lập tuyệt đối**: không tham khảo kết luận của bên khác (kể cả báo cáo nghiệm thu
  nội bộ) trước khi hoàn thành chấm điểm — tránh "hướng theo".
- **Không nương tay**: phát hiện lỗ hổng là thành tích, không phải chỉ trích. Báo cáo
  nghiêm túc > báo cáo đẹp.
- **Bằng chứng > cảm nhận**: mọi nhận xét phải kèm file:dòng hoặc trích dẫn.

**Ký:** Chủ đầu tư — 2026-08-08
