# Quy ước: Học từ chủ đề → Đóng gói skill

Vòng lặp rút kinh nghiệm sau mỗi chủ đề làm việc. Mục tiêu: bộ skill ngày càng đa dạng & chuẩn xác, nhưng **không bắt buộc dùng skill** trong mọi ngữ cảnh.

## Triết lý

- **Skill là công cụ, không là gông cùm.** Dùng khi hợp lý, bỏ qua khi linh hoạt hơn.
- **Học từ thực tế.** Mỗi chủ đề làm xong → rút pattern → quyết định đóng gói hay không.
- **1 chủ đề - 1 quyết định.** Tránh ôm đồm; tập trung 1 action mỗi lần rút kinh nghiệm.
- **Linh hoạt theo chủ đề.** Có chủ đề thấy pattern ngay (rút sau 1 lần), có chủ đề phải làm vài lần mới rõ (rút theo cụm).

## Quy ước làm việc

### Khi bắt đầu chủ đề mới

Tôi sẽ hỏi bạn **1 câu duy nhất** trước khi làm:

> "Chủ đề này dùng skill nào, hay làm tự do?"

- **Có skill phù hợp** → tôi invoke skill, làm theo workflow của skill đó.
- **Không có / không muốn** → làm tự do, không bị ràng buộc.

### Khi kết thúc chủ đề (bước rút kinh nghiệm cố định)

Sau khi chủ đề hoàn thành, tôi **luôn** thực hiện bước rút kinh nghiệm ngắn. Chỉ 1 output duy nhất, theo cấu trúc:

```
## Rút kinh nghiệm: [tên chủ đề]

**Pattern lặp / bài học đáng nhớ:**
[1-3 câu mô tả pattern hoặc bài học cụ thể]

**Quyết định (1 trong 3):**
[ ] TẠO SKILL MỚI — "[tên]" — vì [lý do: pattern rõ, tái sử dụng cao]
[ ] CẬP NHẬT SKILL CÓ SẴN — "[tên]" — thêm [component/reference/pitfall]
[ ] CHƯA ĐÁNG — ghi note thôi, vì [lý do: quá đặc thù / chỉ gặp 1 lần]

**Hành động:** [chỉ điền khi bạn duyệt 1 trong 2 ô đầu]
```

Bạn chỉ cần phản hồi "làm ô X" hoặc "chưa" — tôi sẽ thực hiện (hoặc bỏ qua).

### Nguyên tắc cho quyết định

| Tín hiệu | Quyết định |
|---|---|
| Pattern lặp ≥2 chủ đề, cấu trúc ổn định | → **TẠO SKILL MỚI** |
| Bổ sung 1 component/pitfall cho skill đã có | → **CẬP NHẬT SKILL** |
| Quá đặc thù 1 chủ đề, khó tái sử dụng | → **CHƯA ĐÁNG** (ghi note) |
| Chưa đủ data, cần làm thêm vài lần | → **CHƯA ĐÁNG** (đợi cụm) |

### Khi nào KHÔNG kích hoạt vòng lặp

- Chủ đề quá ngắn (< 5 phút, vd: sửa 1 typo, tra 1 số).
- Chủ đề rõ ràng không có pattern (vd: trả lời câu hỏi kiến thức chung).
- Bạn nói rõ "không cần rút kinh nghiệm".

Tôi sẽ dùng phán đoán — nếu thấy không đáng, tôi bỏ qua bước rút KN và chỉ kết thúc task bình thường.

## File note tích lũy

`/Users/bobo/ZCodeProject/SKILL-LEARNING-LOG.md` — nơi ghi các bài học được đánh dấu "CHƯA ĐÁNG" hoặc "chờ cụm". Khi tích lũy đủ → review và nâng lên thành skill.

(tự động tạo khi có entry đầu tiên)

## Tóm tắt cho tôi (AI) tự nhắc

1. **Bắt đầu:** hỏi "dùng skill hay tự do?"
2. **Làm:** theo lựa chọn của user.
3. **Kết thúc:** rút KN (1 output, 3 ô quyết định) — trừ khi quá ngắn/user nói bỏ qua.
4. **Thực thi:** chỉ khi user duyệt ô TẠO hoặc CẬP NHẬT.
