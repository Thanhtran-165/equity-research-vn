# THƯ TÁI KIỂM ĐỊNH CHECKPOINT 2 — P0-A..P0-F ĐÃ VÁ + PILOT LOCAL

**Gửi:** GPT 5.6 Sol (kiểm định viên độc lập)
**Từ:** Chủ đầu tư — qua ZCode
**Ngày:** 2026-08-08
**Commit vá:** `90883230b` (đã push GitHub)
**Trả lời checkpoint NO-GO của bạn (SHA `c331b573...`)** — toàn bộ P0-A..P0-F đã xử lý
và **tự test runtime trên máy** theo đúng phương pháp của bạn (iso-dir, đủ data files).

---

## 1. ĐỐI CHIẾU TỪNG BLOCKER → ĐÃ VÁ → BẰNG CHỨNG TEST

| Blocker của bạn | Đã vá | Bằng chứng test (tự chạy) |
|---|---|---|
| **P0-A: mutation 1 ô bảng lọt** | Verifier REQ-033 thêm `_verify_history_table`: parse bảng 5 năm, so TỪNG CELL (năm, cột) với financials.json ±2% | **Mutation ô 2025 revenue 10,728.1→20,728.1 (iso-dir đủ data): 72/74, exit 1 — REQ-033 bắt. Baseline iso: 74/74, exit 0** (không false positive) |
| **P0-B: CFO alias + oracle** | Builder nhận cả `Net cash inflows/(outflows) from operating activities` (exact-first) + `is not None` (giữ CFO=0 thật); cfo + inventory vào contract financials; REQ-062 field map có cfo/inventory; REQ-059 fail khi CFO null nhưng CSV có thật | **AAA: cfo=[443.62, 97.1, 2615.22, 958.91, 977.8] — khớp chính xác CSV nguồn** (trước: null×5 dù CSV có thật) |
| **P0-C: REQ-062 skip ngầm** | Fail-closed per-field: NO_CSV/NO_COLUMN/NO_CONTRACT_ARRAY/NO_YEAR_ROWS đều FAIL; chọn cột theo **độ khớp với contract** (match-based — sửa case bảo hiểm chọn nhầm "Net revenue of insurance premium" thay vì "Net sales from insurance business"); alias thêm total operating income + owners' equity; inventory ngân hàng = **not_applicable có rule rõ** (sector=banking) | ACB (bank): 74/74 — inventory not_applicable, revenue khớp Total Operating Income; BMI (bảo hiểm): 74/74 — revenue khớp cột đúng |
| **P0-D: runner** | `scripts/vnall_run_p0.py` mới: staging sạch mỗi mã, done CHỈ khi returncode==0 && recall≥70, xóa result.json cũ trước build, tracker nối tiếp, không merge work cũ | Test runner thật: FPT → tracker `done`, exit 0 |
| **P0-E: sector sai** | BANKS set bỏ SGR (không phải ngân hàng); lệnh GLM bắt buộc **preflight sector** (tên công ty đối chiếu ICB, mâu thuẫn → hiệu chỉnh/needs_human); pilot AGG/BMI/SGR trước toàn bộ | — (chạy tại GLM trong pilot) |
| **P0-F: remnants** | Bỏ segment % giả 22/12/8 cho bank; DATA fcf/accrual = None cho bank; verdict_label ở mọi narrative ngoài tech block (giữ nhãn máy + qualifier "không phải khuyến nghị"); identity hardcode (company_name/exchange/audit) → null; PEER1/PEER2 giả bỏ | ACB HTML: không còn "khuyến nghị kỹ thuật", không còn 22%/12%/8%; tech block giữ nhãn máy đọc + chú thích |

## 2. LƯU Ý 2 QUYẾT ĐỊNH CẦN BẠN XÁC NHẬN

1. **chartHistCash + ref-10 WACC giữ cho ngân hàng**: thử bỏ → vỡ REQ-018/012
   (ngưỡng ≥10 charts/refs). Giữ chart dòng tiền (bank có CFO thật) + ref nguồn WACC
   (chỉ định nghĩa nguồn, không phải khuyến nghị). Nếu bạn yêu cầu bỏ hẳn → phải hạ
   ngưỡng REQ-018/012 kèm rule — chờ bạn quyết.
2. **Claim registry toàn phần**: theo đúng đề xuất của bạn — để P1 (sau rebuild),
   vì P0-A/B/C đã phủ revenue bảng+prose, EPS, CFO, inventory, capex.

## 3. TEST TỔNG HỢP LOCAL (iso-dir, đủ data files)

```
AAA (materials) → 74/74 · cfo/inventory khớp CSV · REQ-062 8 field đối chiếu thật
BMI (insurance) → 74/74 · revenue khớp "Net sales from insurance business"
ACB (banking)   → 74/74 · inventory not_applicable · không segment % giả
FPT (tech)      → 74/74 · runner P0 ghi done đúng
Mutation ô bảng → 72/74 exit 1 (REQ-033) · Baseline → 74/74 exit 0
```

## 4. ĐỀ XUẤT GATE TIẾP THEO

1. Bạn xác nhận P0-A..P0-F (hoặc yêu cầu điều chỉnh) → GLM chạy **pilot 8 mã**
   (AAA/ACB/BMI/FPT/AGG/SGR + 1 mã thiếu capex + 1 mã lỗ) → gửi kết quả bạn xem →
2. Bạn GO → GLM rebuild 1.000 mã (runner mới, preflight sector) → báo cáo P0 →
3. Bạn kiểm định chính thức lần 2 theo protocol (§10 báo cáo gốc của bạn).

**Ký:** Chủ đầu tư — 2026-08-08
