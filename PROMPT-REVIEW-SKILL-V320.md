# PROMPT REVIEW — equity-research-vn v3.2.0

Bạn là reviewer độc lập. Review toàn diện skill `equity-research-vn` (v3.2.0, 67 REQ) tại `/Users/bobo/.zcode/skills/equity-research-vn/`. KHÔNG sửa code — chỉ đọc, chạy, phân tích, báo cáo.

## Việc phải làm trước khi đánh giá

1. Đọc: `requirements.yaml`, `scripts/independent_verifier.py`, `phases/*.md`, `requirements-phase-map.yaml`
2. Chạy verifier trên fixture: `python3 .../independent_verifier.py CTD /tmp/ervn_e2e/CTD/CTD_Complete_Report.html` (kỳ vọng 67/67)
3. Chạy: `cd .../scripts/tests && python3 test_v5_negative.py` (kỳ vọng 8/8)
4. Tự làm ≥3 mutation test của riêng bạn (bịa số liệu, sửa verdict, xóa data file) — đừng tin kết quả 67/67 một cách mù quáng

## Đánh giá 4 khía cạnh

- **A. Lỗ hổng (coverage gaps)**: hành vi bịa/sai nào agent có thể làm mà 67 REQ không bắt được? REQ nào đang dạng "keyword-check" dễ lách (cần recompute/đối chiếu thật)? Phase nào trong 8 phase mỏng nhất về REQ?
- **B. Độ tin cậy (false positive/negative)**: chỗ nào báo oan report tốt? Chỗ nào bỏ sót lỗi thật? Chú ý: đơn vị (tỷ/triệu), số năm 20xx đọc nhầm thành giá trị, tiếng Việt, EPS diluted, RSI(14), tolerance quá rộng/hẹp.
- **C. Chất lượng code**: hàm trùng/chết, REQ trùng chức năng (nên gộp), priority critical/high/medium xếp sai chỗ nào?
- **D. Nhất quán spec**: mỗi REQ có được phản ánh đúng trong phase spec không? REQ nào agent không biết cách thỏa mãn?

## Output bắt buộc

```markdown
# Review equity-research-vn v3.2.0

## Đã làm
- Verifier trên fixture: X/67
- test_v5_negative.py: X/8
- Mutation riêng: N bài, bắt M, lọt K (liệt kê bài lọt)

## Đánh giá tổng thể (3-5 dòng)

## Đề xuất
| ID | Mức (CRITICAL/HIGH/MEDIUM) | Vấn đề | Bằng chứng (file:line/test) | Đề xuất cụ thể |

## Khuyến nghị
- Làm ngay (≤3)
- Làm sau (≤5)
- Không nên làm / cân nhắc kỹ
```

## Nguyên tắc

- Trung thực: nếu bịa vẫn PASS thì nói thẳng, kèm bằng chứng mutation
- Mỗi đề xuất phải kèm kịch bản lỗi cụ thể — không thêm REQ cho "đủ số"
- Không sửa file nào, chỉ báo cáo
