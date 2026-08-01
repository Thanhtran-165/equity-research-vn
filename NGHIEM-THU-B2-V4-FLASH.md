# NGHIỆM THU BATCH-2 — dành cho V4 Flash

Skill `equity-research-vn` v3.2.0 (67 REQ) tại `/Users/bobo/.zcode/skills/equity-research-vn/` vừa được vá batch-2. Mời nghiệm thu phần bạn phát hiện (G5→G14).

## Những gì đã vá theo phát hiện của bạn

| Fix | Trạng thái | Chi tiết |
|---|---|---|
| **G5** — text REQ-044 ≠ code | ✅ ĐÃ VÁ | Text đồng bộ với code whitelist: "URL phải thuộc whitelist báo chí VN/nguồn tài chính HOẶC truy cập được (HTTP <400). Domain lạ + unreachable → FAIL" |
| **G10** — REQ-025 text sai Graham | ✅ ĐÃ VÁ | Bỏ "Graham" khỏi text (REQ-063 verify Graham riêng) — text giờ đúng formulas PE/PB |
| **G11** — REQ-002 chỉ check income_statement | ✅ ĐÃ VÁ | Command check CẢ 3 báo cáo: `len(income_statement()), len(balance_sheet()), len(cash_flow())` — verifier lấy **MIN** (cả 3 ≥20 mới PASS); output "41 41 41" |
| **G12** — dead code split-adjusted | ✅ ĐÃ VÁ | Xóa nhánh `if "split-adjusted" in check.lower()` lặp lần 2 (dòng 314 cũ) — không bao giờ chạy vì nhánh chính (dòng 250) đã return; keyword "audit split" đã có sẵn |

Ngoài ra: FIX-3 (keyword proximity — 3 mutation còn lọt của review chéo cũng được vá: drawdown khớp dd_value thật, key metrics named source cùng câu, causal chain evidence định lượng) — bạn có thể kiểm tra chéo như thường lệ.

## Bằng chứng nghiệm thu

```
Clean fixture:   67/67 PASS
test_v5_negative: 8/8 bắt đúng (không phá test suite của bạn)
REQ-002:         PASS — output "41 41 41" (cả 3 báo cáo ≥20)
REQ-050/052/055: hiện priority=advisory (WARN-only)
Regression:      M1b ✅, M2c-FINAL ✅, M6 ✅, M4b ✅ (giữ nguyên từ batch-1)
```

## Yêu cầu nghiệm thu

1. Chạy lại clean fixture + test_v5_negative.py → 67/67 + 8/8
2. Kiểm tra REQ-002 command mới chạy được (3 số ≥20) — lưu ý verifier giờ lấy MIN
3. Kiểm tra G12: không còn nhánh dead code; REQ-003 vẫn PASS nhờ nhánh chính
4. Chạy lại M1b/M2c-FINAL/M4b/M6 của bạn → giữ nguyên kết quả batch-1

## Ghi chú batch-3 (liên quan phát hiện của bạn)

- G6/G7 (guard "chi phí tăng nhanh hơn doanh thu" + "vốn hóa toàn ngành" cho REQ-064/060/061)
- G8 (đồng bộ số REQ trong 9 phase files), G9 (run_phase gọi full verifier phase 6), G13 (REQ-003 từ task-state split_audit), G14 (gộp 7 REQ claim+source vào 1 helper)
