# PROMPT SO SÁNH HIỆU QUẢ — equity-research-vn (dành cho V4 Pro)

Bạn làm **so sánh độc lập hiệu quả** của verifier trước và sau 6 đợt hardening. KHÔNG sửa code — chỉ chạy, đo, báo cáo.

## Mục tiêu

Trả lời 1 câu hỏi duy nhất: **6 đợt hardening thực sự làm verifier mạnh hơn bao nhiêu, đo được bằng số?**

## Chuẩn bị (làm trước)

### 1. Lấy verifier CŨ (31 REQ, commit trước hardening)
```bash
cd /Users/bobo/ZCodeProject
git show 8ca86fe5f:scripts/independent_verifier.py > /tmp/verifier_old.py
git show 8ca86fe5f:requirements.yaml > /tmp/reqs_old.yaml
```

### 2. Lấy verifier MỚI (68 REQ, hiện tại)
- Verifier: `/Users/bobo/.zcode/skills/equity-research-vn/scripts/independent_verifier.py`
- Requirements: `/Users/bobo/.zcode/skills/equity-research-vn/requirements.yaml`

### 3. Report CTD cũ (bản deployed trước hardening)
- `/Users/bobo/ZCodeProject/ctd_deploy/index.html` (1254 dòng)

### 4. Report CTD mới (fixture E2E đã qua 6 đợt)
- `/tmp/ervn_e2e/CTD/CTD_Complete_Report.html`

## Thí nghiệm (góc BẠN — white-box / code diff)

Bạn giỏi **đọc code + đo lường cấu trúc**. Hãy làm 3 phép đo:

### Phép 1 — Phân tích diff verifier cũ vs mới
```bash
diff /tmp/verifier_old.py /Users/bobo/.zcode/skills/equity-research-vn/scripts/independent_verifier.py | head -200
wc -l /tmp/verifier_old.py /Users/bobo/.zcode/skills/equity-research-vn/scripts/independent_verifier.py
```

→ Trả lời:
- Thêm bao nhiêu dòng, bao nhiêu hàm verify_* mới?
- Cấu trúc dispatch thay đổi thế nào (elif-chain → dict)?
- Có regression tiềm ẩn không (code cũ bị xóa mất chức năng)?

### Phép 2 — Chạy 2 verifier trên report cũ + report mới
```bash
# 4 tổ hợp: {verifier cũ, mới} × {report cũ, mới}
# (verifier cũ cần requirements.yaml cũ trong SKILL_DIR hoặc cùng thư mục)
```

→ Bảng 2×2:
| | Report CŨ | Report MỚI |
|---|---|---|
| Verifier CŨ (31 REQ) | ? PASS / ? FAIL | ? PASS / ? FAIL |
| Verifier MỚI (68 REQ) | ? PASS / ? FAIL | ? PASS / ? FAIL |

Phân tích từng ô:
- Ô [cũ × cũ]: baseline
- Ô [mới × cũ]: verifier mới bắt được lỗi gì trong report cũ mà verifier cũ bỏ sót? (đây là "giá trị thêm")
- Ô [cũ × mới]: report mới có qua được verifier cũ không? (nếu qua → report mới tuân thủ cả chuẩn cũ)
- Ô [mới × mới]: trạng thái production hiện tại

### Phép 3 — Đo độ phủ chống-bịa
Liệt kê **8-10 lớp tấn công** (từ kinh nghiệm 5 đợt review của bạn: keyword proximity, GIGO, cross-section, drawdown, causal, citation, phase skip, price stale...).

Với mỗi lớp → đánh dấu: verifier cũ có chống không? verifier mới có chống không?
→ % lớp chống-biya: cũ ?% → mới ?%

## Output bắt buộc

```markdown
# So sánh hiệu quả verifier cũ (31 REQ) vs mới (68 REQ) — V4 Pro

## Phép 1: diff code
- Dòng: cũ ? → mới ?
- Hàm verify_*: cũ ? → mới ?
- Dispatch: ... → ...
- Regression tiềm ẩn: có/không (chi tiết)

## Phép 2: bảng 2×2
(bảng 4 ô + phân tích từng ô, liệt kê lỗi mới phát hiện trong [mới × cũ])

## Phép 3: độ phủ chống-bịa
| Lớp tấn công | Cũ | Mới |
| (8-10 lớp) | ✅/❌ | ✅/❌ |
% phủ: cũ ?% → mới ?%

## Kết luận
- 6 đợt hardening: giá trị đo được (số dòng, số REQ, % phủ, lỗi mới bắt được)
- Có regression không
- Trung thực: nếu giá trị nhỏ, nói thẳng
```

## Nguyên tắc
- **KHÔNG đọc kết quả của V4 Flash** — độc lập
- Mỗi con số phải có bằng chứng (paste output / file:line)
- Trung thực tuyệt đối: nếu diff chỉ là "thêm số lượng REQ mà không mạnh hơn thật", nói thẳng
- Bạn giỏi white-box → đo cấu trúc, đừng chỉ đếm REQ
