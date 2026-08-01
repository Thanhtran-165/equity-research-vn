# PROMPT SO SÁNH HIỆU QUẢ — equity-research-vn (dành cho V4 Flash)

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

## Thí nghiệm (góc BẠN — black-box / mutation)

Bạn giỏi **bịa dữ liệu**. Hãy làm 2 lớp thí nghiệm:

### Lớp A — Chạy verifier cũ vs mới trên report CŨ
Mục đích: xem verifier mới có bắt được lỗi trong report cũ mà verifier cũ bỏ sót không.

```bash
# Verifier cũ + report cũ
cp /tmp/reqs_old.yaml /tmp/ctd_old_run/requirements.yaml  # setup
python3 /tmp/verifier_old.py CTD /Users/bobo/ZCodeProject/ctd_deploy/index.html

# Verifier mới + report cũ (copy data files nếu cần)
python3 /Users/bobo/.zcode/skills/equity-research-vn/scripts/independent_verifier.py CTD /Users/bobo/ZCodeProject/ctd_deploy/index.html
```

→ So sánh: **verifier cũ báo PASS cái gì mà verifier mới báo FAIL?** Đó là "lỗ hổng mới phát hiện trong report cũ".

### Lớp B — Mutation test trên report cũ (góc đen)
Lấy report CŨ, **bịa 5-10 lỗi** (theo đúng thế mạnh của bạn):
- Bịa revenue/npat/eps lệch data
- Bịa drawdown %, CAGR % không nguồn
- Thêm causal chain không evidence
- Giá cũ, tin giả
- Bỏ phase (nếu áp dụng được)

Chạy **cả 2 verifier** (cũ + mới) trên từng bản bịa → đếm:
- Verifier cũ bắt được mấy lỗi / tổng mấy lỗi?
- Verifier mới bắt được mấy lỗi / tổng mấy lỗi?
- **Sai lệch = độ mạnh thêm của 6 đợt hardening**

## Output bắt buộc

```markdown
# So sánh hiệu quả verifier cũ (31 REQ) vs mới (68 REQ) — V4 Flash

## Lớp A: report cũ qua 2 verifier
| Verifier | PASS | FAIL | REQ chạy | Lỗi mới phát hiện |
|----------|------|------|----------|-------------------|
| CŨ (31 REQ) | ? | ? | ? | (baseline) |
| MỚI (68 REQ) | ? | ? | ? | ? |

→ Liệt kê từng lỗi mới phát hiện (REQ nào, file:line, vì sao cũ bỏ sót)

## Lớp B: mutation test trên report cũ
| Mutation | Verifier cũ | Verifier mới | Chênh |
|----------|-------------|--------------|-------|
| (10 dòng) | BẮT/LỌT | BẮT/LỌT | +/- |

→ Tỉ lệ bắt: cũ ?/10 vs mới ?/10 = độ mạnh thêm ?%

## Kết luận
- 6 đợt hardening làm verifier mạnh thêm bao nhiêu (số liệu)
- Có lớp lỗi nào CŨ bắt được mà MỚI mất không (regression)
- Trung thực: nếu chênh nhỏ, nói thẳng
```

## Nguyên tắc
- **KHÔNG đọc kết quả của V4 Pro** — độc lập
- Mỗi con số phải có bằng chứng chạy thật (paste output)
- Trung thực tuyệt đối: nếu verifier mới không mạnh hơn nhiều, nói thẳng
- Mutation phải **assert áp được** (bài học từ batch-3) — kiểm tra file bị đổi trước khi kết luận
