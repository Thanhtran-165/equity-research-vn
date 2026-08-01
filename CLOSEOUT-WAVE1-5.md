# CLOSEOUT — Wave 1–5 equity-research-vn (ZCode)

**Ngày:** 2026-08-01 · **Phạm vi:** `/Users/bobo/.zcode/skills/equity-research-vn` + `hooks/predeploy-gate.sh`
**Không đụng:** bản Codex, không commit/push, không bật enforced production.

## 1. Trạng thái cuối

- **Registry:** 73 REQ · 9 phases · index tự sinh (`references/req_index.md`) · lint OK
- **Báo cáo chuẩn CTD:** 72/73 PASS (REQ-050 advisory duy nhất) · 14/14 charts · accessibility OK
- **Test suite:** 12/12 PASS (security, valuation units, sector applicability, mutation wave, gate matrix, negative 8/8, golden, fundamental/valuation depth, sentiment calibration, accessibility, registry lint)

## 2. Đã xử lý theo báo cáo bàn giao

| Wave | Nội dung |
|---|---|
| Wave 1 | P0-01 đơn vị, P0-02 FCFF/FCFE, P0-03 state machine, P0-04 no-shell, P0-05 gate fail-closed, P1-01 map+lint, P1-02 schema, P1-03 engine chung, P1-04 drift |
| Wave 2 | Data dictionary/PIT, average balances+accruals+normalized, sector registry, WACC protocol+applicability, claim taxonomy, citation registry |
| Wave 3 | Backtest walk-forward (chạy thật), sentiment calibration, forecast-error schema |
| Wave 4 | req_index tự sinh, accessibility (aria/reduced-motion), mutation corpus, 2 reviewer độc lập → 11 phát hiện đã xử lý |

## 3. Phát hiện từ 2 reviewer độc lập — đã vá

**Flash (black-box):**
- .verifier-hash không tồn tại → TAMPER check vô hiệu → **đã tạo hash + enforced fail-closed khi thiếu**
- REQ-062/035 vacuous pass → **đã sửa thành FAIL rõ ràng**
- Self-attestation split audit → **REQ-003 tự recompute CP độc lập**; phân biệt split (FAIL) vs dilution (advisory, task-state CTD đã ghi cause)
- P/E 13% (tranh luận: EPS 2025 trên CP bình quân 2025 là chuẩn — không sửa số liệu)

**Pro (white-box):**
- phase0-sponsor.md gán nhầm REQ-051 → **sửa thành REQ-067**
- WACC body legacy mâu thuẫn protocol → **thêm cảnh báo reference-only**
- REQ-068 chỉ check key → **check value rỗng** (null hợp lệ: investment_amount)
- CCC thiếu guard COGS≤0, SGR clip sai → **đã sửa**
- Gate fail-open khi JSON stdin hỏng → **enforced fail-closed**
- DDM BĐS mâu thuẫn registry → **đã đồng bộ ⚠️**
- Mutation m1 false-green → **mutate đúng nơi verifier đọc**
- FCFF/FCFE identity test band chặt ±2% → **đã thêm**

## 4. Còn chờ quyết định của chủ dự án (owner)

1. **Enforced mode deploy gate** — thiết kế fail-closed đã test xong (matrix 3 mode × 5 case), nhưng mặc định vẫn `advisory` (theo đúng Wave 5: shadow/advisory đo false positive trước). **Cần owner duyệt mới bật enforced.**
2. **Maturity label** — đã hạ xuống `QUALIFICATION_REQUIRED` (trung thực). Nâng lên chỉ sau qualification đa ngành + owner approval.
3. **Cold cohort 7 ngành** (Wave 5) — khung test đã có (mutation + multi-sector test), chưa chạy đủ 7 ngành thật (cần network + data từng mã).
4. **Review chéo 2 báo cáo** — Flash và Pro đã chạy độc lập; chưa có vòng tổng hợp toàn pipeline.

## 5. Residual risks (ghi nhận, chưa xử lý)

- Verifier vẫn heuristic (regex) — lỗi kiểu mới cần REQ mới
- Self-attestation còn ở REQ-066/067/068 (agent ghi task-state) — đã giảm bớt bằng recompute độc lập (REQ-003/059), chưa loại hết
- Backtest technical: 1 mẫu (CTD) — chưa đủ cohort để đổi nhãn Tech Score
- WACC body legacy vẫn chứa range cũ (cảnh báo, chưa xóa — giữ tham chiếu)

## 6. Supported / Prohibited uses

**Được:** bản nháp nghiên cứu nội bộ, hỗ trợ analyst, báo cáo tham khảo có người rà lại.
**Không được:** tự động khuyến nghị mua/bán, tự deploy vì verifier PASS, coi median là "fair value khoa học" khi chưa lọc applicability, gọi Tech/Sentiment score là alpha.
