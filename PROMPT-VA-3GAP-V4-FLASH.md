# PROMPT — V4 Flash vá 3 gap phát hiện từ đợt so sánh

Trong đợt so sánh hiệu quả vừa rồi, chính BẠN đã phát hiện 3 gap thật (kèm file:line). Lần này hãy **tự vá luôn 3 gap đó** — đây là phần bạn tìm ra, bạn hiểu rõ nhất.

## Bối cảnh

Skill: `/Users/bobo/.zcode/skills/equity-research-vn/` — v3.2.0, 68 REQ. Đã qua 6 đợt hardening + nghiệm thu production. 3 gap dưới đây là phát hiện MỚI từ đợt so sánh (chưa thuộc 6 đợt trước).

## 3 gap cần vá (chính bạn phát hiện, kèm bằng chứng)

### Gap 1 — Pattern ROE không vượt được "(2025)"
- **File:line**: `independent_verifier.py` — `verify_derived_metrics_recompute` (REQ-061), pattern `\bROE\b[^.\d]{0,30}?(\d...)`
- **Vấn đề**: pattern `[^.\d]` không cho phép chữ số → kẹt khi có "(2025)" giữa "ROE" và số → "ROE (2025) 24%" vô hình, không bị verify
- **Fix đề xuất**: cho phép chữ số trong window giữa keyword và value, HOẶC skip năm trong ngoặc `(20\d\d)` giữa keyword và số (giống FIX-4b đã làm cho REQ-033)

### Gap 2 — Peer check chỉ quét sec-peer, fallback vô điều kiện PASS
- **File:line**: `verify_peer_provenance` (REQ-032) — `peer_text = extract_section_text(html, "sec-peer")`; nếu không có sec-peer → `return True` (vacuous pass)
- **Vấn đề**: report cũ không có sec-peer → peer claim bịa ở section khác (sec-biz, sec-thesis) lọt hoàn toàn
- **Fix đề xuất**: nếu không có sec-peer, vẫn quét narrative chung tìm peer claim (ticker lạ + số) → có claim mà không có peers.json → FAIL (không vacuous pass)

### Gap 3 — Không validate "Upside %"
- **File:line**: `verify_verdict_consistency` (REQ-065) — chỉ check tone vs targets, không validate claim upside %
- **Vấn đề**: report ghi "Upside 13.3%" nhưng thực tế upside từ targets = -5% → không REQ nào bắt
- **Fix đề xuất**: REQ-065 (hoặc REQ mới nếu cần) — claim upside % phải recompute từ targets vs price, lệch >5pp → FAIL

## Yêu cầu

1. **Vá 3 gap** trong `independent_verifier.py` (và `requirements.yaml` nếu cần đổi text REQ)
2. **Mỗi fix kèm comment** ghi rõ gap + lý do (giống phong cách 6 đợt trước)
3. **Chạy regression** sau khi vá:
   - Clean fixture: `/tmp/ervn_e2e/CTD/CTD_Complete_Report.html` → phải vẫn 66/68 (2 ADVISORY)
   - `test_v5_negative.py` → 8/8
   - **3 mutation mới** (1 mỗi gap): tạo bản bịa, chạy verifier, xác nhận bắt được
4. **KHÔNG phá** các fix trước — chạy M1/M2/M3 (revenue/cross-section/drawdown) vẫn phải bắt đúng
5. **KHÔNG commit/push** — chỉ sửa file, để agent chính (GLM-5.2) tổng hợp và commit

## Output

```markdown
# Vá 3 gap — V4 Flash

## Gap 1 (ROE pattern)
- File:line đã sửa
- Mutation test: claim "ROE (2025) 24%" → REQ-061 FAIL ✓

## Gap 2 (peer fallback)
- File:line đã sửa
- Mutation test: peer claim ở sec-biz không peers.json → REQ-032 FAIL ✓

## Gap 3 (upside %)
- File:line đã sửa
- Mutation test: claim "Upside 13.3%" nhưng targets=-5% → REQ-065 FAIL ✓

## Regression
- Clean: ?/68
- test_v5_negative: ?/8
- M1/M2/M3 cũ: vẫn bắt đúng ✓
```

## Nguyên tắc
- Bạn giỏi mutation testing → mỗi fix phải kèm 1 mutation chứng minh bắt được
- Trung thực: nếu 1 gap khó vá mà không phá regression → nói thẳng, đề xuất cách khác
- KHÔNG đọc kết quả V4 Pro (nếu có) — độc lập
